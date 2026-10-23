"""Manifest, Evidence JSON and source PDF bind only by exact SHA-256."""

from hashlib import sha256
import json
from pathlib import Path

from app.infrastructure.filesystem.evidence_source_pdf import resolve_source_pdf


def test_isolated_batch_manifest_auto_binding_and_fallback(tmp_path):
    source_root = tmp_path / "batch-pdf"
    source_root.mkdir()
    filename = "ALUCYNK 23.01.2023 rew. 2.0.pdf"
    pdf = b"%PDF-1.4\n%%EOF\n"
    digest = sha256(pdf).hexdigest()
    (source_root / filename).write_bytes(pdf)
    payload = json.loads(Path(
        "docs/sds_bootstrap/BATCH-001_CX/json/B001-P001_DOC-001.json"
    ).read_text(encoding="utf8"))
    payload["source"]["file_sha256"] = digest
    manifest = tmp_path / "BATCH-001_MANIFEST.json"
    manifest.write_text(json.dumps({
        "batch": "BATCH-001_CX", "input_directory": str(source_root),
        "files": [{
            "json": "B001-P001_DOC-001.json", "source_file": filename,
            "sha256": digest,
        }],
    }), encoding="utf8")

    bound = resolve_source_pdf(manifest, "B001-P001_DOC-001.json", payload)
    assert bound.status == "AUTO_BOUND"
    assert bound.filename == filename
    assert bound.content == pdf

    (source_root / filename).write_bytes(b"%PDF-changed")
    assert resolve_source_pdf(manifest, "B001-P001_DOC-001.json", payload).status == "PDF_MISMATCH"

    (source_root / filename).unlink()
    assert resolve_source_pdf(manifest, "B001-P001_DOC-001.json", payload).status == "FALLBACK_REQUIRED"
    assert resolve_source_pdf(
        manifest, "B001-P001_DOC-001.json", payload, (filename, pdf)
    ).status == "MANUAL_BOUND"
    assert resolve_source_pdf(
        manifest, "B001-P001_DOC-001.json", payload, (filename, b"%PDF-wrong")
    ).status == "PDF_MISMATCH"


def test_manifest_and_json_disagreement_cannot_be_bypassed_by_fallback(tmp_path):
    pdf = b"%PDF-1.4\n%%EOF\n"
    payload = {"source": {"original_filename": "source.pdf", "file_sha256": sha256(pdf).hexdigest()}}
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "batch": "BATCH-001_CX", "input_directory": str(tmp_path),
        "files": [{
            "json": "source.json", "source_file": "source.pdf",
            "sha256": "0" * 64,
        }],
    }), encoding="utf8")
    assert resolve_source_pdf(
        manifest, "source.json", payload, ("source.pdf", pdf)
    ).status == "PDF_MISMATCH"
