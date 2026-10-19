"""One locked PostgreSQL transaction for controlled Evidence JSON registration."""

from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.db.models import ProductModel
from app.infrastructure.db.repositories.evidence_identity_read import SqlAlchemyEvidenceIdentityRead
from app.infrastructure.db.repositories.sds_acceptance import SqlAlchemySdsAcceptanceRepository
from app.infrastructure.filesystem.sds_file_validator import SdsFileValidator


class SqlAlchemyControlledEvidenceRegistration:
    def __init__(self, session_factory: sessionmaker[Session], sds_root_path: Path) -> None:
        self._session_factory = session_factory
        self._validator = SdsFileValidator(sds_root_path)

    def verify_product(self, product_id: str) -> None:
        with self._session_factory() as session:
            if session.scalar(select(ProductModel.product_id).where(ProductModel.product_id == product_id)) is None:
                raise ValueError("Selected product does not exist.")

    def register(self, operation) -> str:
        with self._session_factory() as session:
            with session.begin():
                # Lock before revalidation. This serializes identity inserts even
                # from older workflows that do not participate in this importer.
                session.execute(text("LOCK TABLE manufacturers, products IN SHARE ROW EXCLUSIVE MODE"))
                return operation(
                    SqlAlchemyEvidenceIdentityRead(session),
                    SqlAlchemySdsAcceptanceRepository(session, allow_controlled=True),
                    self._validator,
                )
