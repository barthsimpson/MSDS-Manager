from collections.abc import Iterator
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import Connection, Engine, insert
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from app.domain.enums import (
    BhpDecisionStatus,
    DecisionRecordStatus,
    EvidenceFileFormat,
    EvidenceType,
    FileAvailabilityStatus,
    ProductUsageStatus,
    SdsDocumentStatus,
)
from app.infrastructure.config import load_settings
from app.infrastructure.db.models import Base
from app.infrastructure.db.session import create_engine_from_settings


NOW = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def database_engine() -> Iterator[Engine]:
    settings = load_settings()
    assert make_url(settings.database_url).database == "msds_manager"
    engine = create_engine_from_settings(settings)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def connection(database_engine: Engine) -> Iterator[Connection]:
    with database_engine.connect() as database_connection:
        transaction = database_connection.begin()
        try:
            yield database_connection
        finally:
            if transaction.is_active:
                transaction.rollback()


def identifier(prefix: str) -> str:
    return f"task006-{prefix}-{uuid4().hex}"


def add_product(connection: Connection, label: str) -> str:
    manufacturer_id = identifier(f"manufacturer-{label}")
    product_id = identifier(f"product-{label}")
    connection.execute(
        insert(Base.metadata.tables["manufacturers"]),
        {
            "manufacturer_id": manufacturer_id,
            "manufacturer_name": f"TASK-006 Manufacturer {label}",
        },
    )
    connection.execute(
        insert(Base.metadata.tables["products"]),
        {
            "product_id": product_id,
            "product_name": f"TASK-006 Product {label}",
            "manufacturer_product_code": f"TASK006-{label}",
            "manufacturer_id": manufacturer_id,
            "use_description": "Integrity test",
            "use_restriction": "Test transaction only",
            "usage_status": ProductUsageStatus.ACTIVE,
        },
    )
    return product_id


def add_sds(
    connection: Connection,
    product_id: str,
    label: str,
    status: SdsDocumentStatus,
) -> str:
    sds_id = identifier(f"sds-{label}")
    connection.execute(
        insert(Base.metadata.tables["sds_documents"]),
        {
            "sds_id": sds_id,
            "product_id": product_id,
            "original_filename": f"{label}.pdf",
            "relative_path": f"task006/{label}.pdf",
            "issue_date": None,
            "revision": None,
            "document_status": status,
            "registered_at": NOW,
            "file_status": FileAvailabilityStatus.MISSING,
        },
    )
    return sds_id


def add_evidence(connection: Connection, label: str) -> str:
    evidence_id = identifier(f"evidence-{label}")
    connection.execute(
        insert(Base.metadata.tables["decision_evidence"]),
        {
            "evidence_id": evidence_id,
            "relative_path": f"task006/{label}.pdf",
            "evidence_type": EvidenceType.DOCUMENT,
            "file_format": EvidenceFileFormat.PDF,
            "file_status": FileAvailabilityStatus.MISSING,
        },
    )
    return evidence_id


def add_decision(
    connection: Connection,
    product_id: str,
    sds_id: str,
    label: str,
    record_status: DecisionRecordStatus,
) -> str:
    decision_id = identifier(f"decision-{label}")
    connection.execute(
        insert(Base.metadata.tables["bhp_decisions"]),
        {
            "decision_id": decision_id,
            "product_id": product_id,
            "sds_id": sds_id,
            "decision_status": BhpDecisionStatus.APPROVED,
            "notes": None,
            "registered_at": NOW,
            "record_status": record_status,
            "evidence_id": add_evidence(connection, label),
        },
    )
    return decision_id


def constraint_name(error: IntegrityError) -> str | None:
    return getattr(getattr(error.orig, "diag", None), "constraint_name", None)


def test_one_current_sds_per_product_and_archived_history(
    connection: Connection,
) -> None:
    product_a = add_product(connection, "sds-a")
    product_b = add_product(connection, "sds-b")

    add_sds(connection, product_a, "a-current", SdsDocumentStatus.CURRENT)
    add_sds(connection, product_a, "a-archived-1", SdsDocumentStatus.ARCHIVED)
    add_sds(connection, product_a, "a-archived-2", SdsDocumentStatus.ARCHIVED)
    add_sds(connection, product_b, "b-current", SdsDocumentStatus.CURRENT)

    with pytest.raises(IntegrityError) as error_info:
        with connection.begin_nested():
            add_sds(connection, product_a, "a-second-current", SdsDocumentStatus.CURRENT)

    assert (
        constraint_name(error_info.value)
        == "uq_sds_documents_one_current_per_product"
    )


def test_one_current_decision_per_sds_and_superseded_history(
    connection: Connection,
) -> None:
    product_id = add_product(connection, "decision")
    sds_a = add_sds(connection, product_id, "decision-a", SdsDocumentStatus.CURRENT)
    sds_b = add_sds(connection, product_id, "decision-b", SdsDocumentStatus.ARCHIVED)

    add_decision(connection, product_id, sds_a, "a-current", DecisionRecordStatus.CURRENT)
    add_decision(
        connection,
        product_id,
        sds_a,
        "a-superseded-1",
        DecisionRecordStatus.SUPERSEDED,
    )
    add_decision(
        connection,
        product_id,
        sds_a,
        "a-superseded-2",
        DecisionRecordStatus.SUPERSEDED,
    )
    add_decision(connection, product_id, sds_b, "b-current", DecisionRecordStatus.CURRENT)

    with pytest.raises(IntegrityError) as error_info:
        with connection.begin_nested():
            add_decision(
                connection,
                product_id,
                sds_a,
                "a-second-current",
                DecisionRecordStatus.CURRENT,
            )

    assert (
        constraint_name(error_info.value)
        == "uq_bhp_decisions_one_current_per_sds"
    )


def test_decision_product_must_match_the_sds_product(
    connection: Connection,
) -> None:
    product_a = add_product(connection, "matching-a")
    product_b = add_product(connection, "matching-b")
    sds_a = add_sds(connection, product_a, "matching-a", SdsDocumentStatus.CURRENT)

    with pytest.raises(IntegrityError) as error_info:
        with connection.begin_nested():
            add_decision(
                connection,
                product_b,
                sds_a,
                "mismatched",
                DecisionRecordStatus.CURRENT,
            )

    assert constraint_name(error_info.value) == "fk_bhp_decisions_sds_product"

    add_decision(
        connection,
        product_a,
        sds_a,
        "matching",
        DecisionRecordStatus.CURRENT,
    )
