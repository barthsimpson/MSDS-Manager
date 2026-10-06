"""Complete SQLAlchemy persistence mapping for the Core domain."""

from .base import Base
from .catalog import (
    ManufacturerModel,
    ProductHistoryModel,
    ProductModel,
    ProductUsageLocationHistoryModel,
    ProductUsageLocationModel,
    UnitOfMeasureModel,
    UsageLocationHistoryModel,
    UsageLocationModel,
)
from .documents import BhpDecisionModel, DecisionEvidenceModel, SdsDocumentModel
from .physical_review import PhysicalReviewItemModel, PhysicalReviewModel
from .safety import SafetyProfileModel, SdsComponentModel

__all__ = [
    "Base",
    "BhpDecisionModel",
    "DecisionEvidenceModel",
    "ManufacturerModel",
    "ProductHistoryModel",
    "ProductModel",
    "PhysicalReviewItemModel",
    "PhysicalReviewModel",
    "ProductUsageLocationHistoryModel",
    "ProductUsageLocationModel",
    "UnitOfMeasureModel",
    "SafetyProfileModel",
    "SdsComponentModel",
    "SdsDocumentModel",
    "UsageLocationHistoryModel",
    "UsageLocationModel",
]
