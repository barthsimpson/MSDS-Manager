"""Read-only schema, integrity and activity snapshot for PATCH-060-R2."""

import json
import os
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from app.infrastructure.config import load_settings
from app.infrastructure.config.settings import read_env_file, DEFAULT_ENV_FILE


settings = load_settings()
url = make_url(settings.database_url)
env_file_url = read_env_file(DEFAULT_ENV_FILE).get("DATABASE_URL")
source = "process environment" if os.environ.get("DATABASE_URL") else ".env"
engine = create_engine(settings.database_url, connect_args={
    "options": "-c default_transaction_read_only=on"
})
with engine.connect() as conn:
    conn.execute(text("SET TRANSACTION READ ONLY"))
    db_name = conn.scalar(text("SELECT current_database()"))
    revision = conn.scalar(text("SELECT version_num FROM alembic_version"))
    tables = inspect(conn).get_table_names(schema="public")
    counts = {name: conn.scalar(text(f'SELECT count(*) FROM "public"."{name}"'))
              for name in sorted(tables) if name != "alembic_version"}
    missing_sds_product = conn.scalar(text(
        "SELECT count(*) FROM sds_documents s LEFT JOIN products p "
        "ON p.product_id=s.product_id WHERE p.product_id IS NULL"
    ))
    multi_current = conn.scalar(text(
        "SELECT count(*) FROM (SELECT product_id FROM sds_documents "
        "WHERE document_status='CURRENT' GROUP BY product_id HAVING count(*)>1) q"
    ))
    status_column = conn.execute(text(
        "SELECT data_type, character_maximum_length FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name='sds_documents' "
        "AND column_name='document_status'"
    )).mappings().one()
    status_constraint = conn.scalar(text(
        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
        "WHERE conname='sds_document_status_values' "
        "AND conrelid='public.sds_documents'::regclass"
    ))
    current_indexes = conn.execute(text(
        "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname='public' "
        "AND tablename='sds_documents' AND indexdef ILIKE '%CURRENT%'"
    )).mappings().all()
    sessions = conn.execute(text(
        "SELECT pid, application_name, state, backend_type, "
        "xact_start IS NOT NULL AS in_transaction, "
        "EXTRACT(EPOCH FROM now()-COALESCE(xact_start,query_start,backend_start))::integer AS age_seconds "
        "FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid() "
        "ORDER BY pid"
    )).mappings().all()
    lock_count = conn.scalar(text(
        "SELECT count(*) FROM pg_locks l JOIN pg_stat_activity a ON a.pid=l.pid "
        "WHERE a.datname=current_database() AND l.locktype='advisory' "
        "AND l.pid<>pg_backend_pid()"
    ))
    role_can_create_database = conn.scalar(text(
        "SELECT rolcreatedb OR rolsuper FROM pg_roles WHERE rolname=current_user"
    ))
    database_size_bytes = conn.scalar(text("SELECT pg_database_size(current_database())"))
    product = conn.execute(text(
        "SELECT p.product_id, p.product_name, m.manufacturer_name, "
        "s.sds_id, s.document_status, s.revision, s.relative_path "
        "FROM products p JOIN manufacturers m ON m.manufacturer_id=p.manufacturer_id "
        "LEFT JOIN sds_documents s ON s.product_id=p.product_id "
        "AND s.document_status='CURRENT' "
        "WHERE p.product_id=:product_id"
    ), {"product_id": "8385e28101e6409c8110d33febbfdc86"}).mappings().first()
    result = {
        "config_source": source,
        "env_file_matches_effective_db": env_file_url == settings.database_url,
        "host": url.host, "port": url.port, "database": db_name,
        "database_matches_config": db_name == url.database,
        "revision": revision, "tables": sorted(tables), "counts": counts,
        "sds_invalidation_present": "sds_invalidation" in tables,
        "missing_sds_product": missing_sds_product,
        "products_with_multiple_current_sds": multi_current,
        "status_column": dict(status_column),
        "status_constraint": status_constraint,
        "current_indexes": [dict(row) for row in current_indexes],
        "other_sessions": [dict(row) for row in sessions],
        "other_advisory_locks": lock_count,
        "role_can_create_database": role_can_create_database,
        "database_size_bytes": database_size_bytes,
        "product": dict(product) if product else None,
        "configured_sds_root_exists": settings.sds_root_path.is_dir(),
    }
engine.dispose()
Path("tmp/patch060_r2_preflight.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
)
print(json.dumps(result, ensure_ascii=False, default=str))
