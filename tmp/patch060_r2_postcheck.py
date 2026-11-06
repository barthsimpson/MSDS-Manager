"""Read-only post-migration schema, data and SDS-history verification."""

import json
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.infrastructure.config import load_settings
from app.presentation.streamlit.composition import ShellComposition


preflight = json.loads(Path("tmp/patch060_r2_preflight.json").read_text(encoding="utf-8"))
settings = load_settings()
url = make_url(settings.database_url)
assert url.database == preflight["database"] == "msds_manager"
engine = create_engine(settings.database_url, connect_args={
    "options": "-c default_transaction_read_only=on"
})
factory = sessionmaker(bind=engine, expire_on_commit=False)
with engine.connect() as conn:
    conn.execute(text("SET TRANSACTION READ ONLY"))
    db_name = conn.scalar(text("SELECT current_database()"))
    revision = conn.scalar(text("SELECT version_num FROM alembic_version"))
    tables = inspect(conn).get_table_names(schema="public")
    counts = {name: conn.scalar(text(f'SELECT count(*) FROM "public"."{name}"'))
              for name in sorted(tables) if name != "alembic_version"}
    old_counts = {name: counts.get(name) for name in preflight["counts"]}
    missing_sds_product = conn.scalar(text(
        "SELECT count(*) FROM sds_documents s LEFT JOIN products p "
        "ON p.product_id=s.product_id WHERE p.product_id IS NULL"
    ))
    multi_current = conn.scalar(text(
        "SELECT count(*) FROM (SELECT product_id FROM sds_documents "
        "WHERE document_status='CURRENT' GROUP BY product_id HAVING count(*)>1) q"
    ))
    status_length = conn.scalar(text(
        "SELECT character_maximum_length FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name='sds_documents' "
        "AND column_name='document_status'"
    ))
    status_constraint = conn.scalar(text(
        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
        "WHERE conname='sds_document_status_values' "
        "AND conrelid='public.sds_documents'::regclass"
    ))
    current_index = conn.scalar(text(
        "SELECT indexdef FROM pg_indexes WHERE schemaname='public' "
        "AND tablename='sds_documents' "
        "AND indexname='uq_sds_documents_one_current_per_product'"
    ))
    unvalidated_constraints = conn.execute(text(
        "SELECT conrelid::regclass::text AS table_name, conname "
        "FROM pg_constraint WHERE connamespace='public'::regnamespace "
        "AND NOT convalidated ORDER BY 1,2"
    )).mappings().all()
    product = conn.execute(text(
        "SELECT p.product_id, p.product_name, m.manufacturer_name, "
        "s.sds_id, s.document_status, s.revision, s.relative_path "
        "FROM products p JOIN manufacturers m ON m.manufacturer_id=p.manufacturer_id "
        "LEFT JOIN sds_documents s ON s.product_id=p.product_id "
        "AND s.document_status='CURRENT' WHERE p.product_id=:id"
    ), {"id": preflight["product"]["product_id"]}).mappings().one()
    invalidated_sds_count = conn.scalar(text(
        "SELECT count(*) FROM sds_documents WHERE document_status='INVALIDATED'"
    ))
composition = ShellComposition(
    engine=engine, session_factory=factory, products=(),
    sds_root_path=settings.sds_root_path,
    bhp_evidence_root_path=settings.bhp_evidence_root_path,
    settings=settings,
)
history = composition.list_sds_history(preflight["product"]["product_id"])
current = next(item for item in history if item.document_status.value == "CURRENT")
pdf_path = (settings.sds_root_path / current.relative_path).resolve()
root = settings.sds_root_path.resolve()
pdf_within_root = pdf_path.is_relative_to(root)
pdf_exists = pdf_within_root and pdf_path.is_file()
pdf_size = pdf_path.stat().st_size if pdf_exists else None
engine.dispose()
result = {
    "database": db_name, "revision": revision,
    "sds_invalidation_present": "sds_invalidation" in tables,
    "sds_invalidation_count": counts.get("sds_invalidation"),
    "existing_counts_unchanged": old_counts == preflight["counts"],
    "existing_counts": old_counts,
    "missing_sds_product": missing_sds_product,
    "products_with_multiple_current_sds": multi_current,
    "status_column_length": status_length,
    "status_constraint_has_invalidated": "INVALIDATED" in status_constraint,
    "current_unique_index_unchanged":
        current_index == preflight["current_indexes"][0]["indexdef"],
    "unvalidated_constraints": [dict(row) for row in unvalidated_constraints],
    "target_product_unchanged": dict(product) == preflight["product"],
    "history_count": len(history),
    "history_statuses": [item.document_status.value for item in history],
    "current_sds_id": current.sds_id,
    "current_revision": current.revision,
    "pdf_within_configured_root": pdf_within_root,
    "pdf_exists": pdf_exists, "pdf_size_bytes": pdf_size,
    "invalidated_sds_count": invalidated_sds_count,
}
Path("tmp/patch060_r2_postcheck.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(result, ensure_ascii=False))
assert revision == "e4c6f21a9d80"
assert result["sds_invalidation_present"] and result["sds_invalidation_count"] == 0
assert result["existing_counts_unchanged"]
assert missing_sds_product == multi_current == 0
assert status_length == 11 and result["status_constraint_has_invalidated"]
assert result["current_unique_index_unchanged"]
assert not unvalidated_constraints
assert result["target_product_unchanged"]
assert current.sds_id == preflight["product"]["sds_id"]
assert current.revision == "5.0" and pdf_exists and pdf_size > 0
assert invalidated_sds_count == 0
