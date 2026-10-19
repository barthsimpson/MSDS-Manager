import json
from dataclasses import replace
from pathlib import Path

import pytest

from app.application.dto.approved_import import HumanApproval, IdentityDecision
from app.application.dto.evidence_json import IdentityRecord
from app.application.dto.sds import SdsSafetyProfileDraft
from app.application.use_cases.controlled_evidence_import import (
    ControlledEvidenceImport, ImportPlanError, SAFETY_STATUS_FIELDS, approve_import_plan,
)
from app.application.use_cases.import_sds import ImportSds
from app.domain.enums import SafetyInformationStatus


RAW_JSON = Path("docs/sds_bootstrap/BATCH-001_CX/json/B001-P001_DOC-001.json").read_bytes()
PDF = b"%PDF-1.4\n%%EOF\n"
APPROVAL = HumanApproval("isolated-test-reviewer", True, True, True, True, True)


class Read:
    def __init__(self, manufacturers=(), products=()):
        self.manufacturers = manufacturers
        self.products = products

    def manufacturers_named(self, name):
        return tuple(row for row in self.manufacturers if row.name == name)

    def similar_manufacturers(self, name):
        return ()

    def products_named(self, name):
        return tuple(row for row in self.products if row.name == name)

    def products_for_manufacturer(self, name, manufacturer_id, code):
        return tuple(row for row in self.products if row.name == name and
                     (code is None or row.manufacturer_product_code == code))


def safety():
    return SdsSafetyProfileDraft(**{
        field: SafetyInformationStatus.NO_DATA for field in SAFETY_STATUS_FIELDS
    })


def approve(read=None, **changes):
    args = dict(
        raw_json=RAW_JSON, document_key="DOC-001", read=read or Read(),
        manufacturer=IdentityDecision("CREATE", "CX80 POLSKA"),
        product=IdentityDecision("CREATE", "ALUCYNK"),
        use_description="Isolated test use", use_restriction="Isolated test restriction",
        safety_profile=safety(), original_filename="chosen.pdf", pdf_bytes=PDF,
        approval=APPROVAL,
    )
    args.update(changes)
    return approve_import_plan(**args)


def test_approved_plan_binds_json_pdf_logical_sds_and_decisions():
    plan = approve()
    assert len(plan.source_json_fingerprint) == 64
    assert len(plan.pdf_fingerprint) == 64
    assert plan.document_key == "DOC-001"
    assert plan.product_decision.manufacturer_product_code is None
    assert plan.expected_manufacturer_candidates == ()
    assert plan.expected_product_candidates == ()


@pytest.mark.parametrize("change,expected", [
    ({"use_description": ""}, "PLAN_NOT_READY"),
    ({"use_restriction": ""}, "PLAN_NOT_READY"),
    ({"safety_profile": SdsSafetyProfileDraft()}, "INCOMPLETE_SAFETY_DATA"),
    ({"approval": replace(APPROVAL, safety_confirmed=False)}, "HUMAN_CONFIRMATION_REQUIRED"),
    ({"pdf_bytes": b"bad"}, "PDF_REQUIRED"),
])
def test_incomplete_approval_cannot_create_plan(change, expected):
    with pytest.raises(ImportPlanError, match=expected):
        approve(**change)


def test_null_code_link_requires_explicit_confirmation():
    read = Read(
        manufacturers=(IdentityRecord("m1", "CX80 POLSKA"),),
        products=(IdentityRecord("p1", "ALUCYNK", "KNOWN"),),
    )
    decisions = dict(
        manufacturer=IdentityDecision("LINK", "CX80 POLSKA", selected_id="m1"),
        product=IdentityDecision("LINK", "ALUCYNK", selected_id="p1"),
    )
    with pytest.raises(ImportPlanError, match="NULL_CODE_LINK_CONFIRMATION_REQUIRED"):
        approve(read, **decisions)
    decisions["product"] = replace(decisions["product"], null_code_link_confirmed=True)
    assert approve(read, **decisions).product_decision.selected_id == "p1"


def test_new_raw_manufacturer_requires_explicit_canonical_decision():
    payload = json.loads(RAW_JSON)
    payload["documents"][0]["parties"][0]["name"]["value"] += " NEW"
    plan = approve(raw_json=json.dumps(payload).encode())
    assert plan.manufacturer_decision.name == "CX80 POLSKA"


def test_generic_human_review_can_approve_another_manufacturer_and_product():
    payload = json.loads(RAW_JSON)
    document = payload["documents"][0]
    document["parties"][0]["name"]["value"] = "Example Raw Company"
    document["product"]["product_name"]["value"] = "Example Product"
    plan = approve(
        raw_json=json.dumps(payload).encode(),
        manufacturer=IdentityDecision("CREATE", "Example Canonical Company"),
        product=IdentityDecision("CREATE", "Example Product"),
    )
    assert plan.manufacturer_decision.name == "Example Canonical Company"
    assert plan.product_decision.name == "Example Product"


def test_pdf_or_approved_safety_change_stops_before_storage():
    plan = approve()

    class NoRegistration:
        def register(self, operation):
            raise AssertionError("registration must not run")

    class NoStorage:
        def store_new_pdf(self, pdf):
            raise AssertionError("storage must not run")

    committer = ControlledEvidenceImport(NoRegistration(), ImportSds(NoStorage()))
    with pytest.raises(ImportPlanError, match="PDF_CHANGED"):
        committer.execute(plan, RAW_JSON, b"%PDF-changed")
    plan.safety_profile.hazardous_classification_status = SafetyInformationStatus.YES
    with pytest.raises(ImportPlanError, match="SAFETY_PAYLOAD_CHANGED"):
        committer.execute(plan, RAW_JSON, PDF)


def test_filesystem_failure_never_reaches_database_registration():
    plan = approve()

    class NoRegistration:
        def register(self, operation):
            raise AssertionError("registration must not run")

    class FailingStorage:
        def store_new_pdf(self, pdf):
            raise OSError("injected filesystem failure")

    committer = ControlledEvidenceImport(NoRegistration(), ImportSds(FailingStorage()))
    with pytest.raises(OSError, match="injected filesystem failure"):
        committer.execute(plan, RAW_JSON, PDF)
