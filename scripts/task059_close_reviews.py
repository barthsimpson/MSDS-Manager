"""Controlled closure of B001-P012 and B001-P037 only."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
import json
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.application.dto import CorrectProductIdentityInput
from app.application.use_cases.correct_product_identity import CorrectProductIdentity
from app.infrastructure.config import load_settings
from app.infrastructure.db.models import (
    ManufacturerModel, ProductIdentityChangeModel, ProductModel, SdsDocumentModel,
)
from app.infrastructure.db.repositories.product import SqlAlchemyProductRepository
from app.infrastructure.db.session import create_engine_from_settings, create_session_factory
from app.infrastructure.db.transactions import TransactionExecutor


P012 = "ba2c9debc0c04ab3899ae1ce1f059e7f"
P037 = "833c0080c0a34bd1a40f5b2be18b82a6"
TARGET = "a11c4d78f64b41f89de6ec0196a9254b"
LEGACY = "a635199aa44944bbbf31cb63808f58d3"
CURRENT = "3da9cedfc58a47158694746b015bbaf2"
P012_SDS = "f7eb70cce36b49c7a83bfe12f8c0a8b7"


@dataclass(frozen=True)
class Source:
    manifest_id: str
    filename: str
    digest: str
    product_name: str
    issue_date: str
    revision: str


def _digest(path: Path) -> str:
    h = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_sources(batch: Path, source_root: Path) -> dict[str, Source]:
    manifest = json.loads((batch / "BATCH-001_MANIFEST.json").read_text(encoding="utf8"))
    entries = {row["id"]: row for row in manifest["files"]}
    result = {}
    for key in ("B001-P012", "B001-P037"):
        row = entries[key]
        document = json.loads((batch / "json" / row["json"]).read_text(encoding="utf8"))
        metadata = document["documents"][0]["document_metadata"]
        path = source_root / row["source_file"]
        if (document["source"]["original_filename"] != row["source_file"]
                or document["source"]["file_sha256"] != row["sha256"]
                or not path.is_file() or _digest(path) != row["sha256"]
                or path.open("rb").read(5) != b"%PDF-"):
            raise ValueError(f"BLOCKED_SOURCE: {key}")
        result[key] = Source(
            key, row["source_file"], row["sha256"],
            document["documents"][0]["product"]["product_name"]["value"],
            metadata["issue_date"]["value"], metadata["revision"]["value"],
        )
    return result


def validate_database(session: Session, sds_root: Path, sources: dict[str, Source]) -> str:
    p012 = session.get(ProductModel, P012)
    p037 = session.get(ProductModel, P037)
    target = session.get(ManufacturerModel, TARGET)
    legacy = session.get(ManufacturerModel, LEGACY)
    s012 = session.scalars(select(SdsDocumentModel).where(SdsDocumentModel.product_id == P012)).all()
    s037 = session.scalars(select(SdsDocumentModel).where(SdsDocumentModel.product_id == P037)).all()
    changes = session.scalars(select(ProductIdentityChangeModel).where(
        ProductIdentityChangeModel.product_id == P037)).all()
    a, b = sources["B001-P012"], sources["B001-P037"]
    if (p012 is None or p012.product_name != "Cleaner prof" or p012.manufacturer_id != TARGET
            or target is None or target.manufacturer_name != "CX80 Polska"
            or a.product_name != "CLEANER PROF" or a.product_name.casefold() != p012.product_name.casefold()
            or len(s012) != 1 or s012[0].sds_id != P012_SDS
            or s012[0].document_status.value != "CURRENT"
            or s012[0].issue_date != date.fromisoformat(a.issue_date)
            or s012[0].revision != a.revision
            or _digest(sds_root / s012[0].relative_path) != a.digest
            or session.scalar(select(ProductModel).where(ProductModel.product_name == a.product_name)) is not None):
        raise ValueError("BLOCKED_P012_IDENTITY_OR_PDF")
    if (p037 is None or p037.product_name != "XBRAKE CLEANER"
            or p037.manufacturer_product_code != "CX80 XBRAKE CLEANER"
            or b.product_name != "XBRAKE CLEANER" or b.issue_date != "2023-01-24"
            or b.revision != "3.0" or len(s037) != 3
            or {s.sds_id for s in s037} != {
                CURRENT, "3e8346e132bf4bb69016fc5524434472",
                "ecba2904093f40bf96e2762b6a9ebf09"}
            or len([s for s in s037 if s.document_status.value == "CURRENT"]) != 1
            or next(s for s in s037 if s.document_status.value == "CURRENT").sds_id != CURRENT
            or next(s for s in s037 if s.sds_id == CURRENT).issue_date != date(2026, 9, 1)
            or any(_digest(sds_root / s.relative_path) == b.digest for s in s037)):
        raise ValueError("BLOCKED_P037_IDENTITY_OR_LIFECYCLE")
    if p037.manufacturer_id == TARGET:
        valid = [c for c in changes if c.change_kind == "CORRECTION"
                 and c.old_manufacturer_id == LEGACY and c.new_manufacturer_id == TARGET
                 and c.old_product_name == c.new_product_name == p037.product_name
                 and c.old_manufacturer_product_code == c.new_manufacturer_product_code
                 == p037.manufacturer_product_code]
        if len(valid) != 1:
            raise ValueError("BLOCKED_P037_AUDIT_PROVENANCE")
        return valid[0].change_id
    if (p037.manufacturer_id != LEGACY or legacy is None
            or legacy.manufacturer_name != "Cx80" or changes):
        raise ValueError("BLOCKED_P037_MANUFACTURER")
    return "READY_CORRECTION"


def commit_correction(factory, sds_root: Path, sources: dict[str, Source]) -> str:
    def operation(session: Session) -> str:
        session.execute(text(
            "LOCK TABLE manufacturers, products, sds_documents IN SHARE ROW EXCLUSIVE MODE"))
        state = validate_database(session, sds_root, sources)
        if state != "READY_CORRECTION":
            return state
        CorrectProductIdentity(SqlAlchemyProductRepository(session)).execute(
            CorrectProductIdentityInput(P037, "XBRAKE CLEANER", "CX80 XBRAKE CLEANER", "CX80 Polska"))
        session.flush()
        return validate_database(session, sds_root, sources)

    return TransactionExecutor(factory).execute(operation)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--batch", type=Path, default=Path("docs/sds_bootstrap/BATCH-001_CX"))
    parser.add_argument("--commit", action="store_true")
    args = parser.parse_args()
    settings = load_settings()
    sources = load_sources(args.batch, args.source_root)
    engine = create_engine_from_settings(settings)
    factory = create_session_factory(engine)
    with factory() as session:
        session.execute(text("SET TRANSACTION READ ONLY"))
        state = validate_database(session, settings.sds_root_path, sources)
        session.rollback()
    print(json.dumps({"preflight": "PASS", "p012": "SKIP_EXACT_EXISTING",
                      "p037": state, "source_sha": {k: v.digest for k, v in sources.items()}}))
    if args.commit:
        change_id = commit_correction(factory, settings.sds_root_path, sources)
        print(json.dumps({"p037_change_id": change_id,
                          "p037": "ALREADY_CORRECT" if change_id == state else "CORRECTED"}))


if __name__ == "__main__":
    main()
