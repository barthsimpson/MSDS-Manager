"""Import SDS into isolated files and a rolled-back PostgreSQL transaction."""

from datetime import date
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.dto import AcceptSdsInput, AddSdsRevisionInput
from app.domain.enums import SdsDocumentStatus
from app.infrastructure.config import load_settings
from app.infrastructure.db.models import SdsDocumentModel
from app.presentation.streamlit.composition import ShellComposition


PDF = b"%PDF-1.4\nfixture\n"


def _composition(connection, root: Path) -> ShellComposition:
    factory = sessionmaker(
        bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
    )
    return ShellComposition(connection.engine, factory, (), root)


def test_first_sds_and_revision_import_preserve_metadata_and_lifecycle(tmp_path) -> None:
    engine = create_engine(load_settings().database_url)
    marker = uuid4().hex
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                composition = _composition(connection, tmp_path)
                first_id = composition.import_sds(
                    AcceptSdsInput(
                        source_relative_path="", product_name=f"TASK-036 {marker}",
                        manufacturer_product_code=marker,
                        manufacturer_name=f"Maker {marker}",
                        use_description="Use", use_restriction="Restriction",
                        issue_date=date(2025, 1, 1), revision="1",
                    ),
                    "Original SDS.PDF", PDF,
                )
                with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
                    first = session.get(SdsDocumentModel, first_id)
                    product_id = first.product_id
                    assert first.original_filename == "Original SDS.PDF"
                    assert first.relative_path.startswith("imported/")
                    assert UUID(Path(first.relative_path).stem)
                    assert first.relative_path != "Original SDS.PDF"
                    assert first.document_status is SdsDocumentStatus.CURRENT
                    assert (tmp_path / first.relative_path).read_bytes() == PDF

                second_id = composition.import_sds_revision(
                    AddSdsRevisionInput(
                        product_id=product_id, source_relative_path="",
                        issue_date=date(2026, 9, 30), revision=None,
                    ),
                    "Revision.pdf", PDF,
                )
                with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
                    old = session.get(SdsDocumentModel, first_id)
                    new = session.get(SdsDocumentModel, second_id)
                    assert old.document_status is SdsDocumentStatus.ARCHIVED
                    assert new.document_status is SdsDocumentStatus.CURRENT
                    assert new.revision is None
                    assert new.original_filename == "Revision.pdf"
                    assert new.relative_path != old.relative_path
                    assert (tmp_path / new.relative_path).read_bytes() == PDF
            finally:
                transaction.rollback()
    finally:
        engine.dispose()


def test_database_failure_after_file_write_rolls_back_and_removes_pdf(tmp_path, monkeypatch) -> None:
    engine = create_engine(load_settings().database_url)
    marker = uuid4().hex
    from app.infrastructure.db.repositories.sds_acceptance import SqlAlchemySdsAcceptanceRepository

    original = SqlAlchemySdsAcceptanceRepository.accept

    def fail_after_insert(self, data):
        original(self, data)
        raise RuntimeError("injected failure after insert")

    monkeypatch.setattr(SqlAlchemySdsAcceptanceRepository, "accept", fail_after_insert)
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                composition = _composition(connection, tmp_path)
                with pytest.raises(RuntimeError, match="injected failure"):
                    composition.import_sds(
                        AcceptSdsInput(
                            source_relative_path="", product_name=f"TASK-036 failure {marker}",
                            manufacturer_product_code=marker,
                            manufacturer_name=f"Maker {marker}",
                            use_description="Use", use_restriction="Restriction",
                        ),
                        "failure.pdf", PDF,
                    )
                assert list((tmp_path / "imported").iterdir()) == []
                with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
                    assert session.scalars(
                        select(SdsDocumentModel).where(SdsDocumentModel.original_filename == "failure.pdf")
                    ).all() == []
            finally:
                transaction.rollback()
    finally:
        engine.dispose()
