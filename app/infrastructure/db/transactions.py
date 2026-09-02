"""Minimal transaction boundary for SQLAlchemy-backed application operations."""

from collections.abc import Callable
from typing import TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker


ResultT = TypeVar("ResultT")


class PersistenceError(RuntimeError):
    """Technology-neutral failure raised at the infrastructure boundary."""


class TransactionExecutor:
    """Run one application operation in one owned database transaction."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def execute(self, operation: Callable[[Session], ResultT]) -> ResultT:
        with self._session_factory() as session:
            try:
                result = operation(session)
                session.commit()
                return result
            except SQLAlchemyError as error:
                session.rollback()
                raise PersistenceError("Database operation failed.") from error
            except Exception:
                session.rollback()
                raise
