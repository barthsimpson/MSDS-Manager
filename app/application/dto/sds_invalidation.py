"""Input and read records for controlled SDS invalidation."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

from app.domain.enums import SdsDocumentStatus


InvalidationMode = Literal["ARCHIVED_ONLY", "NO_CURRENT", "RESTORE_ARCHIVED"]


@dataclass(frozen=True)
class InvalidateSdsInput:
    product_id: str
    invalidated_sds_id: str
    expected_status: SdsDocumentStatus
    expected_current_sds_id: str | None
    mode: InvalidationMode
    reason: str
    restored_sds_id: str | None = None


@dataclass(frozen=True)
class SdsHistoryItem:
    sds_id: str
    product_id: str
    original_filename: str
    relative_path: str
    issue_date: date | None
    revision: str | None
    document_status: SdsDocumentStatus
    registered_at: datetime
    invalidated_at: datetime | None
    invalidation_reason: str | None
    invalidated_from_status: str | None
    restored_sds_id: str | None
