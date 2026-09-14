"""Complete SQLAlchemy persistence mapping for the Core domain."""

from .base import Base
from .catalog import (
    ManufacturerModel,
    ProductHistoryModel,
    ProductModel,
    ProductUsageLocationHistoryModel,
    ProductUsageLocationModel,
    UsageLocationHistoryModel,
    UsageLocationModel,
)
from .documents import BhpDecisionModel, DecisionEvidenceModel, SdsDocumentModel
from .safety import SafetyProfileModel, SdsComponentModel

__all__ = [
    "Base",
    "BhpDecisionModel",
    "DecisionEvidenceModel",
    "ManufacturerModel",
    "ProductHistoryModel",
    "ProductModel",
    "ProductUsageLocationHistoryModel",
    "ProductUsageLocationModel",
    "SafetyProfileModel",
    "SdsComponentModel",
    "SdsDocumentModel",
    "UsageLocationHistoryModel",
    "UsageLocationModel",
]
