"""Restore the backup to a new isolated database and compare read-only counts."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
from uuid import uuid4

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from app.infrastructure.config import load_settings


preflight = json.loads(Path("tmp/patch060_r2_preflight.json").read_text(encoding="utf-8"))
backup = json.loads(Path("tmp/patch060_r2_backup.json").read_text(encoding="utf-8"))
archive = Path(backup["backup_path"])
digest = hashlib.file_digest(archive.open("rb"), "sha256").hexdigest()
assert digest == backup["sha256"]
settings = load_settings()
url = make_url(settings.database_url)
assert url.database == backup["database"] == preflight["database"] == "msds_manager"
restore_db = f"msds_patch060_r2_restore_{uuid4().hex[:12]}"
assert restore_db != url.database
pg_bin = Path(r"C:\Program Files\PostgreSQL\17\bin")
env = os.environ.copy()
env["PGPASSWORD"] = url.password or ""
env["PGCONNECT_TIMEOUT"] = "10"
conn_args = ["--host", url.host or "localhost", "--port", str(url.port or 5432),
             "--username", url.username or ""]
created = subprocess.run(
    [str(pg_bin / "createdb.exe"), *conn_args, "--maintenance-db=postgres",
     "--template=template0", restore_db],
    env=env, text=True, capture_output=True,
)
if created.returncode:
    raise RuntimeError(f"createdb failed ({created.returncode}): {created.stderr.strip()}")
restored = subprocess.run(
    [str(pg_bin / "pg_restore.exe"), *conn_args, "--dbname", restore_db,
     "--exit-on-error", "--single-transaction", str(archive)],
    env=env, text=True, capture_output=True,
)
if restored.returncode:
    raise RuntimeError(f"pg_restore failed ({restored.returncode}) in {restore_db}: "
                       f"{restored.stderr.strip()}")
engine = create_engine(url.set(database=restore_db), connect_args={
    "options": "-c default_transaction_read_only=on"
})
with engine.connect() as conn:
    conn.execute(text("SET TRANSACTION READ ONLY"))
    tables = inspect(conn).get_table_names(schema="public")
    counts = {name: conn.scalar(text(f'SELECT count(*) FROM "public"."{name}"'))
              for name in sorted(tables) if name != "alembic_version"}
    revision = conn.scalar(text("SELECT version_num FROM alembic_version"))
    product = conn.execute(text(
        "SELECT p.product_id, s.sds_id, s.document_status, s.revision "
        "FROM products p JOIN sds_documents s ON s.product_id=p.product_id "
        "WHERE p.product_id=:id AND s.document_status='CURRENT'"
    ), {"id": preflight["product"]["product_id"]}).mappings().one()
engine.dispose()
assert counts == preflight["counts"]
assert revision == preflight["revision"]
assert product["sds_id"] == preflight["product"]["sds_id"]
result = {
    "restore_database": restore_db,
    "createdb_exit": created.returncode, "pg_restore_exit": restored.returncode,
    "archive_sha256_verified": True,
    "revision": revision,
    "table_count": len(tables),
    "all_existing_table_counts_match": counts == preflight["counts"],
    "product_count": counts["products"],
    "sds_count": counts["sds_documents"],
    "target_product_sds_matches": True,
    "test_database_retained": True,
}
Path("tmp/patch060_r2_restore_check.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(result, ensure_ascii=False))
