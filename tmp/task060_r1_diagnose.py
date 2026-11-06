"""Read-only diagnostic of the operator-configured Product Card history query."""

import json
from pathlib import Path
import traceback

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.infrastructure.config import load_settings
from app.infrastructure.db.repositories.sds_invalidation import SqlAlchemySdsInvalidationRepository
from app.presentation.streamlit.composition import ShellComposition


settings = load_settings()
url = make_url(settings.database_url)
engine = create_engine(settings.database_url, connect_args={
    "options": "-c default_transaction_read_only=on"
})
factory = sessionmaker(bind=engine, expire_on_commit=False)
with engine.connect() as connection:
    connection.execute(text("SET TRANSACTION READ ONLY"))
    database = connection.scalar(text("SELECT current_database()"))
    revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
    audit_table = connection.scalar(text("SELECT to_regclass('public.sds_invalidation')::text"))
    product = connection.execute(text(
        "SELECT p.product_id, p.product_name, p.usage_status, "
        "s.sds_id, s.document_status, s.revision "
        "FROM products p JOIN manufacturers m ON m.manufacturer_id=p.manufacturer_id "
        "LEFT JOIN sds_documents s ON s.product_id=p.product_id AND s.document_status='CURRENT' "
        "WHERE p.product_name=:name AND m.manufacturer_name=:manufacturer"
    ), {
        "name": "SYLGARD 160 Silicone Elastomer-Part A",
        "manufacturer": "DOW POLSKA SP.Z O.O.",
    }).mappings().first()
assert database == url.database
result = {
    "database": database, "alembic_version": revision,
    "sds_invalidation_table": audit_table,
    "product_found": product is not None,
    "product_id": product["product_id"] if product else None,
    "current_sds_status": product["document_status"] if product else None,
    "revision": product["revision"] if product else None,
}
if product:
    composition = ShellComposition(
        engine=engine, session_factory=factory, products=(),
        sds_root_path=settings.sds_root_path,
        bhp_evidence_root_path=settings.bhp_evidence_root_path,
        settings=settings,
    )
    try:
        history = composition.list_sds_history(product["product_id"])
        result["history_count"] = len(history)
    except Exception:
        trace = traceback.format_exc()
        Path("tmp/task060_r1_traceback.txt").write_text(trace, encoding="utf-8")
        result["history_exception"] = trace.splitlines()[-1]
        result["traceback_file"] = "tmp/task060_r1_traceback.txt"
engine.dispose()
print(json.dumps(result, ensure_ascii=False))
