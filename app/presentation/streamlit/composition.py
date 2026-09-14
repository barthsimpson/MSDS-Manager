"""Composition root for the minimal Streamlit shell."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.application.dto import (
    AcceptSdsInput,
    AssignProductUsageLocationInput,
    CreateUsageLocationInput,
    ProductDetails,
    ProductListItem,
    UpdateProductAdministrativeDataInput,
    UpdateProductUsageLocationInput,
    BhpDecisionProduct,
    CurrentBhpDecision,
    RegisterBhpDecisionInput,
    RegisterBhpDecisionResult,
)
from app.application.exceptions import EntityNotFoundError
from app.application.use_cases import (
    AssignProductUsageLocation,
    CreateUsageLocation,
    DeactivateUsageLocation,
    GetProductDetails,
    ListProducts,
    ListUsageLocations,
    ReactivateUsageLocation,
    UpdateProductAdministrativeData,
    UpdateProductUsageLocation,
    AcceptSds,
    PrepareSdsDraft,
    RegisterBhpDecision,
)
from app.infrastructure.config import ConfigurationError, Settings, load_settings
from app.infrastructure.db.repositories import (
    SqlAlchemyProductHistoryRepository,
    SqlAlchemyProductRepository,
    SqlAlchemyProductUsageLocationHistoryRepository,
    SqlAlchemyProductUsageLocationRepository,
    SqlAlchemyUsageLocationHistoryRepository,
    SqlAlchemyUsageLocationRepository,
    SqlAlchemySdsAcceptanceRepository,
    SqlAlchemyBhpDecisionRepository,
    SqlAlchemyBhpDecisionQuery,
)
from app.infrastructure.db.session import (
    create_engine_from_settings,
    create_session_factory,
)
from app.infrastructure.db.transactions import PersistenceError, TransactionExecutor
from app.infrastructure.filesystem.pdf_sds_extractor import PdfSdsExtractor
from app.infrastructure.filesystem.sds_file_validator import SdsFileValidator
from app.infrastructure.filesystem.bhp_evidence_validator import BhpEvidenceValidator


INITIALIZATION_ERROR_MESSAGE = (
    "Nie udało się uruchomić aplikacji. Sprawdź konfigurację i połączenie z bazą."
)


class ShellInitializationError(RuntimeError):
    """Controlled, secret-free error exposed to the Streamlit view."""


@dataclass(slots=True)
class ShellComposition:
    """Ready read-only dependencies owned by the presentation layer."""

    engine: Engine
    session_factory: sessionmaker[Session]
    products: tuple[ProductListItem, ...]
    sds_root_path: Path
    bhp_evidence_root_path: Path = Path(".")

    def list_bhp_products(self) -> tuple[BhpDecisionProduct, ...]:
        with self.session_factory() as session:
            return SqlAlchemyBhpDecisionQuery(session).list_products()

    def get_current_bhp_decision(self, sds_id: str) -> CurrentBhpDecision | None:
        with self.session_factory() as session:
            return SqlAlchemyBhpDecisionQuery(session).get_current_decision(sds_id)

    def list_bhp_evidence_files(self) -> tuple[str, ...]:
        allowed = {".msg", ".pdf", ".jpg", ".jpeg", ".png"}
        return tuple(
            sorted(
                path.relative_to(self.bhp_evidence_root_path).as_posix()
                for path in self.bhp_evidence_root_path.rglob("*")
                if path.is_file() and path.suffix.lower() in allowed
            )
        )

    def register_bhp_decision(
        self, data: RegisterBhpDecisionInput
    ) -> RegisterBhpDecisionResult:
        return TransactionExecutor(self.session_factory).execute(
            lambda session: RegisterBhpDecision(
                BhpEvidenceValidator(self.bhp_evidence_root_path),
                SqlAlchemyBhpDecisionRepository(session),
            ).execute(data)
        )

    def list_sds_files(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                path.relative_to(self.sds_root_path).as_posix()
                for path in self.sds_root_path.rglob("*.pdf")
                if path.is_file()
            )
        )

    def prepare_sds_draft(self, relative_path: str):
        validator = SdsFileValidator(self.sds_root_path)
        return PrepareSdsDraft(PdfSdsExtractor(), validator).execute(
            validator.validate_relative(relative_path)
        )

    def accept_sds(self, data: AcceptSdsInput) -> str:
        validator = SdsFileValidator(self.sds_root_path)
        return TransactionExecutor(self.session_factory).execute(
            lambda session: AcceptSds(
                SqlAlchemySdsAcceptanceRepository(session), validator
            ).execute(data)
        )

    def get_product_details(self, product_id: str) -> ProductDetails:
        try:
            with self.session_factory() as session:
                return GetProductDetails(
                    SqlAlchemyProductRepository(session)
                ).execute(product_id)
        except (
            ConfigurationError,
            EntityNotFoundError,
            SQLAlchemyError,
            OSError,
            ImportError,
        ) as error:
            raise ShellInitializationError(INITIALIZATION_ERROR_MESSAGE) from error

    def list_usage_locations(self):
        try:
            with self.session_factory() as session:
                return ListUsageLocations(
                    SqlAlchemyUsageLocationRepository(session)
                ).execute()
        except (SQLAlchemyError, OSError, ImportError) as error:
            raise ShellInitializationError(INITIALIZATION_ERROR_MESSAGE) from error

    def update_product_administrative_data(
        self, data: UpdateProductAdministrativeDataInput
    ) -> None:
        self._execute_write(
            lambda session: UpdateProductAdministrativeData(
                SqlAlchemyProductRepository(session),
                SqlAlchemyProductHistoryRepository(session),
            ).execute(data)
        )

    def create_usage_location(self, data: CreateUsageLocationInput) -> None:
        self._execute_write(
            lambda session: CreateUsageLocation(
                SqlAlchemyUsageLocationRepository(session)
            ).execute(data)
        )

    def change_usage_location_status(self, location_id: str, active: bool) -> None:
        use_case = ReactivateUsageLocation if active else DeactivateUsageLocation
        self._execute_write(
            lambda session: use_case(
                SqlAlchemyUsageLocationRepository(session),
                SqlAlchemyUsageLocationHistoryRepository(session),
            ).execute(location_id)
        )

    def assign_product_usage_location(
        self, data: AssignProductUsageLocationInput
    ) -> None:
        self._execute_write(
            lambda session: AssignProductUsageLocation(
                SqlAlchemyProductUsageLocationRepository(session),
                SqlAlchemyUsageLocationRepository(session),
                SqlAlchemyProductUsageLocationHistoryRepository(session),
            ).execute(data)
        )

    def update_product_usage_location(
        self, data: UpdateProductUsageLocationInput
    ) -> None:
        self._execute_write(
            lambda session: UpdateProductUsageLocation(
                SqlAlchemyProductUsageLocationRepository(session),
                SqlAlchemyProductUsageLocationHistoryRepository(session),
            ).execute(data)
        )

    def _execute_write(self, operation) -> None:
        try:
            TransactionExecutor(self.session_factory).execute(operation)
        except (
            ConfigurationError,
            EntityNotFoundError,
            PersistenceError,
            SQLAlchemyError,
            OSError,
            ImportError,
            ValueError,
            TypeError,
        ) as error:
            raise ShellInitializationError(INITIALIZATION_ERROR_MESSAGE) from error

    def dispose(self) -> None:
        self.engine.dispose()


def build_shell_composition(
    settings_loader: Callable[[], Settings] = load_settings,
    engine_factory: Callable[[Settings], Engine] = create_engine_from_settings,
    session_factory_builder: Callable[
        [Engine], sessionmaker[Session]
    ] = create_session_factory,
) -> ShellComposition:
    """Build dependencies and verify a minimal read through Application."""

    engine: Engine | None = None
    try:
        settings = settings_loader()
        engine = engine_factory(settings)
        session_factory = session_factory_builder(engine)
        with session_factory() as session:
            products = ListProducts(SqlAlchemyProductRepository(session)).execute()
        return ShellComposition(
            engine=engine,
            session_factory=session_factory,
            products=tuple(products),
            sds_root_path=settings.sds_root_path,
            bhp_evidence_root_path=settings.bhp_evidence_root_path,
        )
    except (ConfigurationError, SQLAlchemyError, OSError, ImportError) as error:
        if engine is not None:
            engine.dispose()
        raise ShellInitializationError(INITIALIZATION_ERROR_MESSAGE) from error
