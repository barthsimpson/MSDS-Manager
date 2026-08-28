"""Complete SQLAlchemy persistence mapping for the Core domain."""

from .base import Base
from .catalog import (
    ManufacturerModel,
    ProductModel,
    ProductUsageLocationModel,
    UsageLocationModel,
)
from .documents import BhpDecisionModel, DecisionEvidenceModel, SdsDocumentModel
from .safety import SafetyProfileModel, SdsComponentModel

__all__ = [
    "Base",
    "BhpDecisionModel",
    "DecisionEvidenceModel",
    "ManufacturerModel",
    "ProductModel",
    "ProductUsageLocationModel",
    "SafetyProfileModel",
    "SdsComponentModel",
    "SdsDocumentModel",
    "UsageLocationModel",
]
