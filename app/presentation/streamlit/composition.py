"""Composition root for the minimal Streamlit shell."""

from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.application.dto import (
    AssignProductUsageLocationInput,
    CreateUsageLocationInput,
    ProductDetails,
    ProductListItem,
    UpdateProductAdministrativeDataInput,
    UpdateProductUsageLocationInput,
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
)
from app.infrastructure.config import ConfigurationError, Settings, load_settings
from app.infrastructure.db.repositories import SqlAlchemyProductRepository
from app.infrastructure.db.repositories import (
    SqlAlchemyProductUsageLocationRepository,
    SqlAlchemyUsageLocationRepository,
)
from app.infrastructure.db.session import (
    create_engine_from_settings,
    create_session_factory,
)
from app.infrastructure.db.transactions import PersistenceError, TransactionExecutor


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
                SqlAlchemyProductRepository(session)
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
                SqlAlchemyUsageLocationRepository(session)
            ).execute(location_id)
        )

    def assign_product_usage_location(
        self, data: AssignProductUsageLocationInput
    ) -> None:
        self._execute_write(
            lambda session: AssignProductUsageLocation(
                SqlAlchemyProductUsageLocationRepository(session),
                SqlAlchemyUsageLocationRepository(session),
            ).execute(data)
        )

    def update_product_usage_location(
        self, data: UpdateProductUsageLocationInput
    ) -> None:
        self._execute_write(
            lambda session: UpdateProductUsageLocation(
                SqlAlchemyProductUsageLocationRepository(session)
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
        )
    except (ConfigurationError, SQLAlchemyError, OSError, ImportError) as error:
        if engine is not None:
            engine.dispose()
        raise ShellInitializationError(INITIALIZATION_ERROR_MESSAGE) from error
