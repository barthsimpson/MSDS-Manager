"""Read-only verification of the completed TASK-057 operator batch."""

from collections import Counter
from hashlib import sha256
from pathlib import Path
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.config import load_settings
from app.infrastructure.db.models import (
    BhpDecisionModel, ManufacturerModel, ProductHistoryModel, ProductModel,
    SafetyProfileModel, SdsComponentModel, SdsDocumentModel,
)
from app.infrastructure.db.session import create_engine_from_settings


report = Path("docs/sds_bootstrap/BATCH-001_CX/BATCH-001_STAGE1_IMPORT_REPORT.md")
lines = report.read_text(encoding="utf8").splitlines()
assert "Status: **BATCH COMMIT COMPLETE**" in lines
rows = []
for line in lines:
    if line.startswith("| B001-P"):
        values = [item.strip() for item in line.strip("|").split("|")]
        assert len(values) == 18, line
        rows.append(values)
assert len(rows) == 37
classification = Counter(row[13] for row in rows)
action = Counter(row[14] for row in rows)
assert classification == {
    "READY_CREATE": 22, "SKIP_EXACT_EXISTING": 1,
    "SKIP_DUPLICATE_SOURCE": 1, "REVIEW_IDENTITY": 11,
    "EXCLUDED_NON_SDS": 2,
}
assert action == {"COMMITTED": 22, "SKIPPED": 2,
                  "NOT_ATTEMPTED": 11, "EXCLUDED": 2}

settings = load_settings()
root = settings.sds_root_path
engine = create_engine_from_settings(settings)
try:
    with engine.connect().execution_options(postgresql_readonly=True) as connection:
        with Session(bind=connection) as session:
            manufacturers = session.scalars(select(ManufacturerModel)).all()
            products = session.scalars(select(ProductModel)).all()
            documents = session.scalars(select(SdsDocumentModel)).all()
            histories = session.scalars(select(ProductHistoryModel)).all()
            assert len(manufacturers) == 5
            assert {row.manufacturer_name for row in manufacturers} == {
                "CX80", "Cx80", "CX80 Polska", "Sherwin-Williams", "TEST",
            }
            assert len(products) == 27
            assert len(documents) == 29
            assert len(histories) == 33
            committed = [row for row in rows if row[14] == "COMMITTED"]
            committed_pids = set()
            committed_sids = set()
            for row in committed:
                manifest_id, expected_sha, product_id, sds_id = (
                    row[0], row[3], row[15], row[16],
                )
                product = session.get(ProductModel, product_id)
                document = session.get(SdsDocumentModel, sds_id)
                assert product is not None, manifest_id
                assert document is not None, manifest_id
                assert document.product_id == product_id, manifest_id
                assert product.product_name == row[5], manifest_id
                assert product.manufacturer_id == "a11c4d78f64b41f89de6ec0196a9254b"
                assert (product.use_description, product.use_restriction) == (None, None)
                assert document.document_status.value == "CURRENT"
                assert sha256((root / document.relative_path).read_bytes()).hexdigest() == expected_sha
                assert sum(history.product_id == product_id for history in histories) == 1
                committed_pids.add(product_id)
                committed_sids.add(sds_id)
            assert len(committed_pids) == len(committed_sids) == 22
            assert session.scalars(select(SafetyProfileModel).where(
                SafetyProfileModel.sds_id.in_(committed_sids)
            )).all() == []
            assert session.scalars(select(SdsComponentModel).where(
                SdsComponentModel.sds_id.in_(committed_sids)
            )).all() == []
            assert session.scalars(select(BhpDecisionModel).where(
                BhpDecisionModel.sds_id.in_(committed_sids)
            )).all() == []
            alucynk = session.get(ProductModel, "8691276f0dbd4bc6846ae14e02b79a60")
            assert alucynk.product_name == "ALUCYNK"
            assert session.get(SdsDocumentModel, "3c361a8019d64589b8fcf7ff9479654d").product_id == alucynk.product_id
            assert sum(row.product_name == "ALUCYNK" for row in products) == 1
            for name in ("CX80 Płyn Konserwująco Naprawczy", "XBRAKE CLEANER", "Cleaner prof"):
                assert sum(row.product_name == name for row in products) == 1
            print(json.dumps({
                "verified": True, "manifest_entries": len(rows),
                "classification": dict(classification), "action": dict(action),
                "manufacturer_rows": len(manufacturers), "product_rows": len(products),
                "sds_rows": len(documents), "history_rows": len(histories),
                "new_product_sds_history_each": len(committed), "new_pdfs_sha_verified": len(committed),
                "alucynk_unique": True, "review_unmodified": True,
                "committed_ids": [
                    {"manifest_id": row[0], "product_id": row[15], "sds_id": row[16]}
                    for row in committed
                ],
            }))
finally:
    engine.dispose()
