from app.domain.enums import EvidenceFileFormat, EvidenceType, FileAvailabilityStatus
from app.domain.models import DecisionEvidence
from app.infrastructure.db.repositories.decision_evidence import from_model, to_model


def test_source_filename_is_preserved_independently_of_storage_path() -> None:
    evidence = DecisionEvidence(
        evidence_id="evidence-1",
        original_filename="Operator Approval.PDF",
        relative_path="imported/technical-uuid.pdf",
        evidence_type=EvidenceType.DOCUMENT,
        file_format=EvidenceFileFormat.PDF,
        file_status=FileAvailabilityStatus.AVAILABLE,
    )

    model = to_model(evidence)

    assert model.original_filename == "Operator Approval.PDF"
    assert model.relative_path == "imported/technical-uuid.pdf"
    assert from_model(model) == evidence


def test_historical_record_with_unknown_source_name_remains_readable() -> None:
    evidence = DecisionEvidence(
        evidence_id="historical-evidence",
        original_filename=None,
        relative_path="archive/old.msg",
        evidence_type=EvidenceType.EMAIL,
        file_format=EvidenceFileFormat.MSG,
        file_status=FileAvailabilityStatus.MISSING,
    )

    assert from_model(to_model(evidence)) == evidence
