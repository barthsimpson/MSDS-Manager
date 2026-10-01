"""Mapping between decision evidence domain records and persistence rows."""

from app.domain.models import DecisionEvidence
from app.infrastructure.db.models import DecisionEvidenceModel


def to_model(evidence: DecisionEvidence) -> DecisionEvidenceModel:
    return DecisionEvidenceModel(
        evidence_id=evidence.evidence_id,
        original_filename=evidence.original_filename,
        relative_path=evidence.relative_path,
        evidence_type=evidence.evidence_type,
        file_format=evidence.file_format,
        file_status=evidence.file_status,
    )


def from_model(model: DecisionEvidenceModel) -> DecisionEvidence:
    return DecisionEvidence(
        evidence_id=model.evidence_id,
        original_filename=model.original_filename,
        relative_path=model.relative_path,
        evidence_type=model.evidence_type,
        file_format=model.file_format,
        file_status=model.file_status,
    )
