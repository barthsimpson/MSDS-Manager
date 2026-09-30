"""PATCH-009 metadata persistence and CURRENT-only read, with rollback."""

from dataclasses import replace
from datetime import date
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.application.dto import AcceptSdsInput, AddSdsRevisionInput
from app.application.use_cases import (
    AcceptSds, AddSdsRevision, GetProductDetails, ListSupervisoryProducts,
)
from app.domain.enums import SdsDocumentStatus
from app.infrastructure.config import load_settings
from app.infrastructure.db.models import SdsDocumentModel
from app.infrastructure.db.repositories import (
    SqlAlchemyProductRepository, SqlAlchemySdsAcceptanceRepository,
    SqlAlchemySupervisoryQuery,
)
from app.infrastructure.filesystem.sds_file_validator import SdsFileValidator
from app.presentation.streamlit.product_registry import _registry_row


def test_date_without_revision_persists_and_archived_revision_is_not_shown(tmp_path) -> None:
    settings = load_settings()
    marker = uuid4().hex
    (tmp_path / "old.pdf").write_bytes(b"%PDF-1.4\nold\n")
    (tmp_path / "new.pdf").write_bytes(b"%PDF-1.4\nnew\n")
    validator = SdsFileValidator(tmp_path)
    engine = create_engine(settings.database_url)
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                with Session(bind=connection) as session:
                    repository = SqlAlchemySdsAcceptanceRepository(session)
                    old_id = AcceptSds(repository, validator).execute(AcceptSdsInput(
                        source_relative_path="old.pdf",
                        product_name=f"PATCH-009 {marker}",
                        manufacturer_product_code=marker,
                        manufacturer_name=f"PATCH-009 {marker}",
                        use_description="Use",
                        use_restriction="Restriction",
                        issue_date=date(2025, 1, 1),
                        revision="old",
                        detected_language="PL",
                        language_valid=True,
                    ))
                    product_id = session.get(SdsDocumentModel, old_id).product_id
                    current_id = AddSdsRevision(repository, validator).execute(
                        AddSdsRevisionInput(
                            product_id=product_id,
                            source_relative_path="new.pdf",
                            issue_date=date(2026, 9, 30),
                            revision=None,
                        )
                    )
                    current = session.get(SdsDocumentModel, current_id)
                    archived = session.get(SdsDocumentModel, old_id)
                    assert current.issue_date == date(2026, 9, 30)
                    assert current.revision is None
                    assert current.document_status is SdsDocumentStatus.CURRENT
                    assert archived.revision == "old"
                    assert archived.document_status is SdsDocumentStatus.ARCHIVED

                    read_settings = replace(
                        settings, sds_root_path=tmp_path, bhp_evidence_root_path=tmp_path
                    )
                    row = next(
                        row for row in ListSupervisoryProducts(
                            SqlAlchemySupervisoryQuery(session, settings=read_settings)
                        ).execute()
                        if row.product_id == product_id
                    )
                    product = GetProductDetails(
                        SqlAlchemyProductRepository(session)
                    ).execute(product_id)
                    assert row.current_sds_id == current_id
                    assert row.current_sds_issue_date == date(2026, 9, 30)
                    assert row.current_sds_revision is None
                    assert _registry_row(product, row)["Rewizja SDS"] == "—"
            finally:
                transaction.rollback()
    finally:
        engine.dispose()
