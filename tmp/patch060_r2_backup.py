"""Create and inspect a full custom-format backup outside the repository."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.engine import make_url

from app.infrastructure.config import load_settings


repo = Path.cwd().resolve()
preflight = json.loads(Path("tmp/patch060_r2_preflight.json").read_text(encoding="utf-8"))
settings = load_settings()
url = make_url(settings.database_url)
assert preflight["database"] == url.database == "msds_manager"
assert preflight["revision"] == "b7d4a1f03962"
assert not preflight["other_sessions"] and preflight["other_advisory_locks"] == 0

backup_root = repo.parent / "MSDS-Manager-backups"
assert backup_root != repo and repo not in backup_root.parents
free = shutil.disk_usage(backup_root.parent).free
assert free > 2 * preflight["database_size_bytes"]
backup_root.mkdir(exist_ok=True)
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
archive = backup_root / f"msds_manager_patch060_r2_{stamp}_{uuid4().hex[:8]}.dump"
pg_bin = Path(r"C:\Program Files\PostgreSQL\17\bin")
env = os.environ.copy()
env["PGPASSWORD"] = url.password or ""
env["PGCONNECT_TIMEOUT"] = "10"
base = ["--host", url.host or "localhost", "--port", str(url.port or 5432),
        "--username", url.username or "", "--dbname", url.database]
dump = subprocess.run(
    [str(pg_bin / "pg_dump.exe"), *base, "--format=custom", "--file", str(archive)],
    env=env, text=True, capture_output=True,
)
if dump.returncode:
    raise RuntimeError(f"pg_dump failed ({dump.returncode}): {dump.stderr.strip()}")
size = archive.stat().st_size
assert size > 0
listing = subprocess.run(
    [str(pg_bin / "pg_restore.exe"), "--list", str(archive)],
    env=env, text=True, capture_output=True,
)
if listing.returncode:
    raise RuntimeError(f"pg_restore --list failed ({listing.returncode}): {listing.stderr.strip()}")
for name in ("products", "sds_documents", "bhp_decisions", "decision_evidence"):
    assert f"TABLE public {name} " in listing.stdout, name
digest = hashlib.sha256()
with archive.open("rb") as stream:
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(chunk)
result = {
    "database": url.database, "backup_path": str(archive),
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "size_bytes": size, "sha256": digest.hexdigest(),
    "pg_dump_exit": dump.returncode,
    "pg_restore_list_exit": listing.returncode,
    "pg_restore_list_entries": sum(";" in line for line in listing.stdout.splitlines()
                                   if line and line[0].isdigit()),
    "required_tables_in_archive": True,
}
Path("tmp/patch060_r2_backup.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(result, ensure_ascii=False))
