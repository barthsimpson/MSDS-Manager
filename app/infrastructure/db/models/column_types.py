"""Shared SQLAlchemy column type factories."""

from enum import StrEnum

from sqlalchemy import Enum as SqlEnum


def enum_column_type(enum_class: type[StrEnum], name: str) -> SqlEnum:
    """Map an approved domain enum to reversible VARCHAR plus CHECK metadata."""

    return SqlEnum(
        enum_class,
        name=name,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        values_callable=lambda members: [member.value for member in members],
    )
