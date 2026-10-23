"""Operator gates for one Evidence JSON controlled import."""

import json
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

from streamlit.testing.v1 import AppTest

from app.application.use_cases.controlled_evidence_import import approve_import_plan
from app.application.use_cases.plan_evidence_json_import import PlanEvidenceJsonImport
from app.presentation.streamlit import evidence_import


PDF = b"%PDF-1.4\n%%EOF\n"
PAYLOAD = json.loads(Path(
    "docs/sds_bootstrap/BATCH-001_CX/json/B001-P001_DOC-001.json"
).read_text(encoding="utf8"))
PAYLOAD["source"]["file_sha256"] = sha256(PDF).hexdigest()
RAW = json.dumps(PAYLOAD, ensure_ascii=False).encode()


class Read:
    def manufacturers_named(self, name):
        return ()

    def similar_manufacturers(self, name):
        from app.application.dto.evidence_json import IdentityRecord
        return (IdentityRecord("similar-1", "CX80 Polska"),)

    def products_named(self, name):
        return ()

    def products_for_manufacturer(self, name, manufacturer_id, code):
        return ()


class ReadLink(Read):
    def manufacturers_named(self, name):
        from app.application.dto.evidence_json import IdentityRecord
        return (IdentityRecord("manufacturer-1", "CX80 POLSKA"),)

    def products_named(self, name):
        from app.application.dto.evidence_json import IdentityRecord
        return (IdentityRecord("product-1", "ALUCYNK", "KNOWN-CODE"),)

    def products_for_manufacturer(self, name, manufacturer_id, code):
        return self.products_named(name) if manufacturer_id == "manufacturer-1" else ()


class ReadApprovedEquivalent(Read):
    def manufacturers_named(self, name):
        from app.application.dto.evidence_json import IdentityRecord
        return (IdentityRecord("approved", "CX80 Polska"),) if name == "CX80 Polska" else ()

    def similar_manufacturers(self, name):
        from app.application.dto.evidence_json import IdentityRecord
        return (IdentityRecord("approved", "CX80 Polska"),
                IdentityRecord("unapproved", "CX80"))


class FakeComposition:
    def __init__(self, read=None, manifest_path=None):
        self.read = read or Read()
        self.manifest_path = manifest_path or Path("missing-batch-manifest.json")
        self.approved = []
        self.committed = []

    def resolve_evidence_pdf(self, json_filename, payload, fallback=None):
        from app.infrastructure.filesystem.evidence_source_pdf import resolve_source_pdf
        return resolve_source_pdf(self.manifest_path, json_filename, payload, fallback)

    def dry_run_evidence_json(self, payload):
        return PlanEvidenceJsonImport(self.read).execute(payload)

    def evidence_candidates(self, manufacturer_name, product_name, manufacturer_id, code):
        from app.application.manufacturer_identity import manufacturer_candidates
        exact, similar = manufacturer_candidates(self.read, manufacturer_name)
        return (exact, similar,
                self.read.products_for_manufacturer(product_name, manufacturer_id, code)
                if manufacturer_id else ())

    def approve_evidence_import(self, raw, key, manufacturer, product, description,
                                restriction, profile, filename, pdf, approval):
        plan = approve_import_plan(
            raw, key, self.read, manufacturer, product,
            use_description=description, use_restriction=restriction,
            safety_profile=profile, original_filename=filename,
            pdf_bytes=pdf, approval=approval,
        )
        self.approved.append(plan)
        return plan

    def commit_evidence_import(self, plan, raw, pdf):
        self.committed.append((plan, raw, pdf))
        return "sds-1"

    def evidence_import_result(self, sds_id):
        return "product-1", "CURRENT", "chosen.pdf"


def _app(monkeypatch, composition=None):
    composition = composition or FakeComposition()
    uploads = {
        "evidence-json-upload": SimpleNamespace(name="B001-P001_DOC-001.json", getvalue=lambda: RAW),
        "evidence-pdf-upload": SimpleNamespace(name="chosen.pdf", getvalue=lambda: PDF),
        "__calls": [],
    }
    def upload(*args, **kwargs):
        uploads["__calls"].append(kwargs["key"])
        return uploads.get(kwargs["key"])
    monkeypatch.setattr(evidence_import.st, "file_uploader", upload)
    def render(current_composition):
        from app.presentation.streamlit import evidence_import
        evidence_import.render_evidence_import(current_composition)
    app = AppTest.from_function(render, args=(composition,), default_timeout=10).run()
    return app, composition, uploads


def _dry_run(app):
    app.button(key="evidence-dry-run").click().run()
    app.selectbox(key="evidence-document").set_value("DOC-001").run()
    return app


def _complete_review(app):
    app.radio(key="evidence-manufacturer-action").set_value("CREATE")
    app.run()
    app.checkbox(key="evidence-similar-manufacturer-confirmed").set_value(True)
    app.radio(key="evidence-product-action").set_value("CREATE")
    app.text_area(key="evidence-use-description").set_value("Test use")
    app.text_area(key="evidence-use-restriction").set_value("Test restriction")
    app.text_input(key="evidence-reviewer").set_value("Test reviewer")
    app.checkbox(key="evidence-manual-confirmed").set_value(True)
    app.checkbox(key="evidence-pdf-confirmed").set_value(True)
    app.checkbox(key="evidence-document-confirmed").set_value(True)
    app.run()
    return app


def test_dry_run_review_approval_commit_and_rerun(monkeypatch):
    app, composition, _ = _app(monkeypatch)
    assert "evidence-commit" not in [button.key for button in app.button]
    _dry_run(app)
    assert "evidence-commit" not in [button.key for button in app.button]
    assert "Brak danych" in [item.value for item in app.markdown] or any(
        "Brak danych" in item.value for item in app.markdown)
    assert any("CX80 Polska" in item.value for item in app.markdown)
    assert app.button(key="evidence-approve").disabled
    _complete_review(app)
    assert not app.button(key="evidence-approve").disabled
    app.button(key="evidence-approve").click().run()
    assert len(composition.approved) == 1
    assert composition.approved[0].product_decision.manufacturer_product_code is None
    assert app.button(key="evidence-commit").disabled
    app.checkbox(key="evidence-final-confirmed").set_value(True).run()
    app.button(key="evidence-commit").click().run()
    assert len(composition.committed) == 1
    assert any("Import zakończony" in item.value for item in app.success)
    app.run()
    assert len(composition.committed) == 1
    assert "evidence-commit" not in [button.key for button in app.button]
    app.button(key="evidence-open-product").click().run()
    assert app.session_state["shell-navigation-target"] == "Produkty"
    assert app.session_state["product-card-id"] == "product-1"


def test_pdf_change_invalidates_approved_plan(monkeypatch):
    app, composition, uploads = _app(monkeypatch)
    _dry_run(app)
    _complete_review(app)
    app.button(key="evidence-approve").click().run()
    uploads["evidence-pdf-upload"] = SimpleNamespace(
        name="changed.pdf", getvalue=lambda: b"%PDF-changed")
    app.run()
    assert len(composition.committed) == 0
    assert evidence_import.WORK_KEY not in app.session_state
    assert any(evidence_import.STALE_MESSAGE in item.value for item in app.error)


def test_wrong_pdf_blocks_stage1_approval(monkeypatch):
    app, composition, uploads = _app(monkeypatch)
    _dry_run(app)
    assert app.button(key="evidence-approve").disabled
    _complete_review(app)
    uploads["evidence-pdf-upload"] = SimpleNamespace(
        name="wrong.pdf", getvalue=lambda: b"%PDF-wrong")
    app.run()
    assert app.button(key="evidence-dry-run").disabled
    assert any("PDF_MISMATCH" in item.value for item in app.error)
    assert composition.approved == []


def test_link_with_null_json_code_requires_separate_confirmation(monkeypatch):
    composition = FakeComposition(ReadLink())
    app, _, _ = _app(monkeypatch, composition)
    _dry_run(app)
    app.radio(key="evidence-manufacturer-action").set_value("LINK").run()
    app.selectbox(key="evidence-manufacturer-id").set_value("manufacturer-1").run()
    app.checkbox(key="evidence-manufacturer-link-confirmed").set_value(True).run()
    app.radio(key="evidence-product-action").set_value("LINK").run()
    app.selectbox(key="evidence-product-id").set_value("product-1")
    app.text_area(key="evidence-use-description").set_value("Test use")
    app.text_area(key="evidence-use-restriction").set_value("Test restriction")
    app.text_input(key="evidence-reviewer").set_value("Test reviewer")
    for key in ("evidence-manual-confirmed", "evidence-pdf-confirmed",
                "evidence-document-confirmed"):
        app.checkbox(key=key).set_value(True)
    app.run()
    assert app.button(key="evidence-approve").disabled
    app.checkbox(key="evidence-null-code-confirmed").set_value(True).run()
    assert not app.button(key="evidence-approve").disabled
    app.button(key="evidence-approve").click().run()
    assert composition.approved[0].product_decision.selected_id == "product-1"
    assert composition.approved[0].product_decision.null_code_link_confirmed


def test_similar_manufacturer_link_requires_checkbox(monkeypatch):
    composition = FakeComposition(ReadApprovedEquivalent())
    app, _, _ = _app(monkeypatch, composition)
    _dry_run(app)
    assert any("CX80 Polska" in item.value for item in app.markdown)
    app.radio(key="evidence-manufacturer-action").set_value("LINK").run()
    app.selectbox(key="evidence-manufacturer-id").set_value("approved").run()
    app.radio(key="evidence-product-action").set_value("CREATE")
    app.text_area(key="evidence-use-description").set_value("Test use")
    app.text_area(key="evidence-use-restriction").set_value("Test restriction")
    app.text_input(key="evidence-reviewer").set_value("Test reviewer")
    for key in ("evidence-manual-confirmed", "evidence-pdf-confirmed",
                "evidence-document-confirmed"):
        app.checkbox(key=key).set_value(True)
    app.run()
    assert app.button(key="evidence-approve").disabled
    app.checkbox(key="evidence-manufacturer-link-confirmed").set_value(True).run()
    assert not app.button(key="evidence-approve").disabled
    app.button(key="evidence-approve").click().run()
    assert composition.approved[0].manufacturer_decision.selected_id == "approved"
    assert composition.approved[0].manufacturer_decision.manufacturer_link_confirmed
    assert any("CX80 Polska" in item.value for item in app.markdown)


def test_stale_commit_consumes_old_plan(monkeypatch):
    class StaleComposition(FakeComposition):
        def commit_evidence_import(self, plan, raw, pdf):
            from app.application.use_cases.controlled_evidence_import import ImportPlanError
            raise ImportPlanError("STALE_RESOLUTION")

    app, composition, _ = _app(monkeypatch, StaleComposition())
    _dry_run(app)
    _complete_review(app)
    app.button(key="evidence-approve").click().run()
    app.checkbox(key="evidence-final-confirmed").set_value(True).run()
    app.button(key="evidence-commit").click().run()
    assert evidence_import.WORK_KEY not in app.session_state
    assert any(evidence_import.STALE_MESSAGE in item.value for item in app.error)


def _manifest(tmp_path, pdf_bytes=PDF, create_pdf=True):
    filename = PAYLOAD["source"]["original_filename"]
    if create_pdf:
        (tmp_path / filename).write_bytes(pdf_bytes)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "batch": "BATCH-001_CX", "input_directory": str(tmp_path),
        "files": [{
            "json": "B001-P001_DOC-001.json", "source_file": filename,
            "sha256": PAYLOAD["source"]["file_sha256"],
        }],
    }), encoding="utf8")
    return manifest


def test_available_manifest_pdf_is_auto_bound_without_second_upload(monkeypatch, tmp_path):
    app, _, uploads = _app(monkeypatch, FakeComposition(manifest_path=_manifest(tmp_path)))
    assert "evidence-pdf-upload" not in uploads["__calls"]
    assert not app.button(key="evidence-dry-run").disabled
    _dry_run(app)
    assert "evidence-pdf-upload" not in uploads["__calls"]
    assert app.button(key="evidence-approve").disabled


def test_manifest_same_filename_wrong_hash_blocks_dry_run(monkeypatch, tmp_path):
    app, _, uploads = _app(monkeypatch, FakeComposition(
        manifest_path=_manifest(tmp_path, pdf_bytes=b"%PDF-other")))
    assert app.button(key="evidence-dry-run").disabled
    assert "evidence-pdf-upload" not in uploads["__calls"]
    assert any("PDF_MISMATCH" in item.value for item in app.error)


def test_missing_manifest_pdf_shows_manual_fallback(monkeypatch, tmp_path):
    app, _, uploads = _app(monkeypatch, FakeComposition(
        manifest_path=_manifest(tmp_path, create_pdf=False)))
    assert "evidence-pdf-upload" in uploads["__calls"]
    assert not app.button(key="evidence-dry-run").disabled


def test_missing_pdf_fallback_blocks_dry_run_until_selected(monkeypatch, tmp_path):
    app, _, uploads = _app(monkeypatch, FakeComposition(
        manifest_path=_manifest(tmp_path, create_pdf=False)))
    uploads["evidence-pdf-upload"] = None
    app.run()
    assert "evidence-pdf-upload" in uploads["__calls"]
    assert app.button(key="evidence-dry-run").disabled


def test_json_change_invalidates_auto_bound_approved_plan(monkeypatch, tmp_path):
    composition = FakeComposition(manifest_path=_manifest(tmp_path))
    app, _, uploads = _app(monkeypatch, composition)
    _dry_run(app)
    _complete_review(app)
    app.button(key="evidence-approve").click().run()
    changed = dict(PAYLOAD)
    changed["documents"] = [dict(PAYLOAD["documents"][0], document_key="DOC-CHANGED")]
    uploads["evidence-json-upload"] = SimpleNamespace(
        name="B001-P001_DOC-001.json",
        getvalue=lambda: json.dumps(changed, ensure_ascii=False).encode(),
    )
    app.run()
    assert evidence_import.WORK_KEY not in app.session_state
    assert any(evidence_import.STALE_MESSAGE in item.value for item in app.error)
