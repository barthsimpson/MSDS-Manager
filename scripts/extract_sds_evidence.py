"""Controlled local entry point for TASK-062-R3; no database imports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.infrastructure.filesystem.sds_evidence_pipeline import extract_evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="PDF SDS to Evidence JSON DRAFT")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--source-id", required=True)
    args = parser.parse_args()
    if not args.source_id.replace("-", "").isalnum():
        parser.error("source-id must be alphanumeric with hyphens")
    tmp_root = (Path(__file__).resolve().parents[1] / "tmp").resolve()
    output_dir = args.output_dir.resolve()
    if output_dir != tmp_root and tmp_root not in output_dir.parents:
        parser.error("output-dir must be inside the repository tmp/ directory")
    report_path = output_dir / f"{args.source_id}.validation.json"
    draft_path = output_dir / f"{args.source_id}.evidence.json"
    if report_path.exists() or draft_path.exists():
        parser.error("artifact already exists; use a fresh output directory")
    draft, gates = extract_evidence(args.pdf)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(gates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if any(gate["status"] == "FAIL" for gate in gates.values()):
        print(f"Validation failed; no draft written. Report: {report_path}")
        return 2
    draft_path.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Draft: {draft_path}; validation: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
