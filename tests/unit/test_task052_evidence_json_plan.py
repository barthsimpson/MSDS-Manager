from copy import deepcopy
import json
from pathlib import Path

import pytest

from app.application.dto.evidence_json import IdentityRecord
from app.application.use_cases.plan_evidence_json_import import PlanEvidenceJsonImport


SAMPLE = Path("docs/sds_bootstrap/BATCH-001_CX/json/B001-P001_DOC-001.json")


class IdentityRead:
    def __init__(self, manufacturers=(), products=(), similar=()):
        self.manufacturers = manufacturers
        self.products = products
        self.similar = similar
        self.calls = []

    def manufacturers_named(self, name):
        self.calls.append(("manufacturer", name))
        return tuple(row for row in self.manufacturers if row.name == name)

    def similar_manufacturers(self, name):
        return tuple(row for row in self.similar if row.name != name)

    def products_named(self, name):
        self.calls.append(("product_name", name))
        return tuple(row for row in self.products if row.name == name)

    def products_for_manufacturer(self, name, manufacturer_id, code):
        self.calls.append(("product", name, manufacturer_id, code))
        return tuple(row for row in self.products if row.name == name and
                     (code is None or row.manufacturer_product_code == code))


@pytest.fixture
def sample():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def test_alucynk_reference_dry_run(sample):
    read = IdentityRead(similar=(IdentityRecord("m1", "CX80"), IdentityRecord("m2", "Cx80")))
    plan, = PlanEvidenceJsonImport(read).execute(sample)
    assert plan.validation_status == "VALID"
    assert plan.mapped_product_name == "ALUCYNK"
    assert plan.mapped_manufacturer_product_code is None
    assert str(plan.mapped_issue_date) == "2023-01-23"
    assert plan.mapped_revision == "2.0"
    assert plan.manufacturer_resolution.status == "CREATE_CANDIDATE"
    assert plan.manufacturer_resolution.canonical_name == "CX80 POLSKA"
    assert [row.name for row in plan.manufacturer_resolution.similar_records] == ["CX80", "Cx80"]
    assert plan.manufacturer_resolution.human_confirmation_required
    assert plan.product_resolution.status == "CREATE_CANDIDATE"
    assert plan.product_resolution.conditional_on_manufacturer
    assert plan.required_manual_inputs == ("use_description", "use_restriction")
    assert "INCOMPLETE_SAFETY_DATA" not in plan.blockers
    assert plan.commit_readiness == "NOT_READY"
    assert not any(call[0] == "product" for call in read.calls)


@pytest.mark.parametrize("count,status", [(0, "CREATE_CANDIDATE"), (1, "LINK_CANDIDATE"), (2, "HUMAN_REVIEW")])
def test_manufacturer_exact_cardinality(sample, count, status):
    manufacturers = tuple(IdentityRecord(f"m{i}", "CX80 POLSKA") for i in range(count))
    plan, = PlanEvidenceJsonImport(IdentityRead(manufacturers=manufacturers)).execute(sample)
    assert plan.manufacturer_resolution.status == status
    assert len(plan.manufacturer_resolution.candidate_ids) == count


@pytest.mark.parametrize("code,count,status", [
    (None, 0, "CREATE_CANDIDATE"), (None, 1, "LINK_CANDIDATE"),
    (None, 2, "HUMAN_REVIEW"), ("A-1", 0, "CREATE_CANDIDATE"),
    ("A-1", 1, "LINK_CANDIDATE"), ("A-1", 2, "HUMAN_REVIEW"),
])
def test_product_cardinality_with_and_without_code(sample, code, count, status):
    if code is not None:
        field = sample["documents"][0]["product"]["manufacturer_product_code"]
        field.update(value=code, state="FOUND", evidence=deepcopy(sample["documents"][0]["product"]["product_name"]["evidence"]))
    products = tuple(IdentityRecord(f"p{i}", "ALUCYNK", code) for i in range(count))
    read = IdentityRead(manufacturers=(IdentityRecord("m1", "CX80 POLSKA"),), products=products)
    plan, = PlanEvidenceJsonImport(read).execute(sample)
    assert plan.product_resolution.status == status
    assert len(plan.product_resolution.candidate_ids) == count
    assert ("product", "ALUCYNK", "m1", code) in read.calls
    if code is None and count == 1:
        assert plan.product_resolution.human_confirmation_required


def test_null_code_known_database_code_is_candidate_only(sample):
    read = IdentityRead(
        manufacturers=(IdentityRecord("m1", "CX80 POLSKA"),),
        products=(IdentityRecord("p1", "ALUCYNK", "KNOWN"),),
    )
    plan, = PlanEvidenceJsonImport(read).execute(sample)
    assert plan.product_resolution.status == "LINK_CANDIDATE"
    assert plan.product_resolution.human_confirmation_required
    assert plan.mapped_manufacturer_product_code is None


@pytest.mark.parametrize("state", ["AMBIGUOUS", "UNREADABLE"])
def test_non_importable_product_name_stays_unresolved(sample, state):
    field = sample["documents"][0]["product"]["product_name"]
    field.update(value=None, state=state, evidence=[])
    read = IdentityRead()
    plan, = PlanEvidenceJsonImport(read).execute(sample)
    assert plan.validation_status == "VALID"
    assert plan.mapped_product_name is None
    assert plan.product_resolution.status == "HUMAN_REVIEW"
    assert "PRODUCT_NAME_REQUIRES_HUMAN_REVIEW" in plan.blockers


@pytest.mark.parametrize("state", ["AMBIGUOUS", "UNREADABLE"])
def test_uncertain_code_never_becomes_null_code_link_candidate(sample, state):
    sample["documents"][0]["product"]["manufacturer_product_code"]["state"] = state
    read = IdentityRead(
        manufacturers=(IdentityRecord("m1", "CX80 POLSKA"),),
        products=(IdentityRecord("p1", "ALUCYNK", "KNOWN"),),
    )
    plan, = PlanEvidenceJsonImport(read).execute(sample)
    assert plan.validation_status == "VALID"
    assert plan.product_resolution.status == "HUMAN_REVIEW"
    assert "MANUFACTURER_PRODUCT_CODE_REQUIRES_HUMAN_REVIEW" in plan.blockers
    assert not any(call[0] == "product" for call in read.calls)


def test_invalid_field_stops_identity_reads_for_document(sample):
    sample["documents"][0]["product"]["product_name"]["evidence"] = []
    read = IdentityRead()
    plan, = PlanEvidenceJsonImport(read).execute(sample)
    assert plan.validation_status == "INVALID"
    assert plan.errors
    assert plan.manufacturer_resolution.status == "INVALID"
    assert plan.product_resolution.status == "INVALID"
    assert read.calls == []


@pytest.mark.parametrize("state,value", [
    ("NOT_FOUND", "NO"), ("AMBIGUOUS", "NO_DATA"),
    ("UNREADABLE", "NOT_APPLICABLE"), ("FOUND", None),
])
def test_extraction_state_cannot_invent_importable_value(sample, state, value):
    field = sample["documents"][0]["product"]["manufacturer_product_code"]
    field.update(state=state, value=value)
    plan, = PlanEvidenceJsonImport(IdentityRead()).execute(sample)
    assert plan.validation_status == "INVALID"


def test_invalid_document_does_not_stop_separate_logical_sds(sample):
    second = deepcopy(sample["documents"][0])
    second["document_key"] = "DOC-002"
    sample["documents"].append(second)
    sample["extraction_report"]["logical_sds_count"] = 2
    sample["documents"][0]["product"]["product_name"]["evidence"] = []
    read = IdentityRead()
    plans = PlanEvidenceJsonImport(read).execute(sample)
    assert [plan.validation_status for plan in plans] == ["INVALID", "VALID"]
    assert read.calls


def test_partial_safety_does_not_become_no_data(sample):
    safety = sample["documents"][0]["safety_profile"]
    safety["carcinogenicity"] = {"domain_value": None, "state": "NOT_FOUND", "evidence": []}
    plan, = PlanEvidenceJsonImport(IdentityRead()).execute(sample)
    assert plan.validation_status == "VALID"
    assert "INCOMPLETE_SAFETY_DATA" not in plan.blockers
    assert "SAFETY_DATA_DEFERRED_TO_STAGE_2" in plan.warnings
    assert plan.commit_readiness == "NOT_READY"


def test_new_manufacturer_raw_value_requires_review(sample):
    sample["documents"][0]["parties"][0]["name"]["value"] += " NOWA"
    plan, = PlanEvidenceJsonImport(IdentityRead()).execute(sample)
    assert plan.validation_status == "VALID"
    assert plan.manufacturer_resolution.status == "HUMAN_REVIEW"
    assert "UNAPPROVED_MANUFACTURER_RAW_VALUE" in plan.blockers


def test_each_logical_sds_has_separate_plan(sample):
    second = deepcopy(sample["documents"][0])
    second["document_key"] = "DOC-002"
    second["product"]["product_name"]["value"] = "INNY"
    sample["documents"].append(second)
    sample["extraction_report"]["logical_sds_count"] = 2
    plans = PlanEvidenceJsonImport(IdentityRead()).execute(sample)
    assert [plan.document_key for plan in plans] == ["DOC-001", "DOC-002"]
    assert [plan.mapped_product_name for plan in plans] == ["ALUCYNK", "INNY"]


@pytest.mark.parametrize("payload", [None, {}, {"documents": []}])
def test_invalid_envelope_has_explicit_result_without_reads(payload):
    read = IdentityRead()
    plan, = PlanEvidenceJsonImport(read).execute(payload)
    assert plan.validation_status == "INVALID"
    assert plan.errors
    assert plan.product_resolution.status == "INVALID"
    assert read.calls == []
