"""Approved status and evidence enumerations for the Core domain."""

from enum import StrEnum


class ProductUsageStatus(StrEnum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"
    INACTIVE = "INACTIVE"


class UsageLocationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class SdsDocumentStatus(StrEnum):
    CURRENT = "CURRENT"
    ARCHIVED = "ARCHIVED"


class FileAvailabilityStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"


class BhpDecisionStatus(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DecisionRecordStatus(StrEnum):
    CURRENT = "CURRENT"
    SUPERSEDED = "SUPERSEDED"


class SafetyInformationStatus(StrEnum):
    YES = "YES"
    NO = "NO"
    NO_DATA = "NO_DATA"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class EvidenceType(StrEnum):
    EMAIL = "EMAIL"
    DOCUMENT = "DOCUMENT"
    PHOTO_SCAN = "PHOTO_SCAN"


class EvidenceFileFormat(StrEnum):
    MSG = "MSG"
    PDF = "PDF"
    JPG = "JPG"
    JPEG = "JPEG"
    PNG = "PNG"
