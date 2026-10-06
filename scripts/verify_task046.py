"""Validate TASK-046 hardening on a disposable PostgreSQL cluster."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile

from sqlalchemy import create_engine, inspect, text


OLD_REVISION = "c7e5a82d9043"
NEW_REVISION = "d8f3a21c6046"
CHECK_NAME = "ck_usage_locations_location_code_format"
UNIQUE_NAME = "uq_usage_locations_location_code"


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    pg_bin = Path(r"C:\Program Files\PostgreSQL\17\bin")
    if not (pg_bin / "initdb.exe").is_file():
        raise RuntimeError("PostgreSQL 17 binaries are required for isolated validation.")
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    work = Path(tempfile.mkdtemp(prefix="task046-", dir=repo / ".venv")).resolve()
    assert work.parent == (repo / ".venv").resolve()
    data = work / "postgres"
    env = os.environ.copy()
    env["PATH"] = str(pg_bin) + os.pathsep + env.get("PATH", "")
    env["PYTHONUTF8"] = "1"
    env["DATABASE_URL"] = f"postgresql+psycopg://task046@127.0.0.1:{port}/msds_manager"
    env["SDS_ROOT_PATH"] = str(work / "sds")
    env["BHP_EVIDENCE_ROOT_PATH"] = str(work / "evidence")
    (work / "sds").mkdir()
    (work / "evidence").mkdir()
    command_number = 0

    def run(*args: str, expected_failure: bool = False) -> str:
        nonlocal command_number
        command_number += 1
        print("RUN:", " ".join(args[:4]), flush=True)
        output_path = work / f"command-{command_number}.log"
        with output_path.open("wb") as output_file:
            result = subprocess.run(
                args, cwd=repo, env=env, stdout=output_file,
                stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=120,
            )
        output = output_path.read_text(encoding="utf-8", errors="replace")
        if expected_failure:
            if result.returncode == 0 or "NotNullViolation" not in output:
                raise RuntimeError(f"Expected NOT NULL rejection, got:\n{output}")
        elif result.returncode:
            raise RuntimeError(f"{' '.join(args[:4])} failed:\n{output}")
        return output

    def database_snapshot(engine) -> str:
        queries = {
            "locations": "SELECT * FROM usage_locations ORDER BY location_id",
            "history": "SELECT * FROM usage_location_history ORDER BY history_id",
            "assignments": "SELECT * FROM product_usage_locations ORDER BY product_id, location_id",
        }
        with engine.connect() as connection:
            rows = {
                name: [
                    [None if value is None else str(value) for value in row]
                    for row in connection.execute(text(query))
                ]
                for name, query in queries.items()
            }
        return hashlib.sha256(json.dumps(
            rows, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")).hexdigest()

    def verify_schema(engine, *, nullable: bool, expected_fingerprint: str) -> None:
        inspector = inspect(engine)
        column = next(c for c in inspector.get_columns("usage_locations")
                      if c["name"] == "location_code")
        assert column["type"].length == 32
        assert column["nullable"] is nullable
        assert CHECK_NAME in {c["name"] for c in inspector.get_check_constraints("usage_locations")}
        assert UNIQUE_NAME in {c["name"] for c in inspector.get_unique_constraints("usage_locations")}
        assert database_snapshot(engine) == expected_fingerprint

    engine = None
    try:
        run(str(pg_bin / "initdb.exe"), "-D", str(data), "-U", "task046",
            "--auth=trust", "--encoding=UTF8", "--locale=C")
        run(str(pg_bin / "pg_ctl.exe"), "-D", str(data), "-l", str(work / "postgres.log"),
            "-o", f"-p {port} -h 127.0.0.1", "-w", "start")
        run(str(pg_bin / "createdb.exe"), "-h", "127.0.0.1", "-p", str(port),
            "-U", "task046", "msds_manager")
        run(sys.executable, "-m", "alembic", "upgrade", OLD_REVISION)
        engine = create_engine(env["DATABASE_URL"])
        with engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO usage_locations (location_id, location_name, status) "
                "VALUES ('task046-legacy', 'Legacy', 'ACTIVE')"
            ))
        run(sys.executable, "-m", "alembic", "upgrade", NEW_REVISION,
            expected_failure=True)
        assert OLD_REVISION in run(sys.executable, "-m", "alembic", "current")
        with engine.connect() as connection:
            assert connection.scalar(text(
                "SELECT count(*) FROM usage_locations "
                "WHERE location_id = 'task046-legacy' AND location_code IS NULL"
            )) == 1
        assert next(c for c in inspect(engine).get_columns("usage_locations")
                    if c["name"] == "location_code")["nullable"] is True
        print("Isolated NULL rejection: PASS", flush=True)

        with engine.begin() as connection:
            connection.execute(text(
                "UPDATE usage_locations SET location_code = 'ISO' "
                "WHERE location_id = 'task046-legacy'"
            ))
            connection.execute(text(
                "INSERT INTO usage_locations "
                "(location_id, location_code, location_name, status) "
                "VALUES ('task046-other', 'OTH', 'Other', 'INACTIVE')"
            ))
            connection.execute(text(
                "INSERT INTO usage_location_history "
                "(history_id, location_id, status, changed_at) "
                "VALUES ('task046-history', 'task046-legacy', 'ACTIVE', CURRENT_TIMESTAMP)"
            ))
            connection.execute(text(
                "INSERT INTO manufacturers (manufacturer_id, manufacturer_name) "
                "VALUES ('task046-manufacturer', 'Test manufacturer')"
            ))
            connection.execute(text(
                "INSERT INTO products (product_id, product_name, manufacturer_product_code, "
                "manufacturer_id, use_description, use_restriction, usage_status) "
                "VALUES ('task046-product', 'Test product', 'T46', "
                "'task046-manufacturer', '', '', 'ACTIVE')"
            ))
            connection.execute(text(
                "INSERT INTO product_usage_locations "
                "(product_id, location_id, peak_quantity_value, peak_quantity_unit_id) "
                "SELECT 'task046-product', 'task046-legacy', 1, unit_id "
                "FROM unit_of_measure WHERE code = 'kg'"
            ))
        fingerprint = database_snapshot(engine)
        verify_schema(engine, nullable=True, expected_fingerprint=fingerprint)

        run(sys.executable, "-m", "alembic", "upgrade", NEW_REVISION)
        assert NEW_REVISION in run(sys.executable, "-m", "alembic", "current")
        verify_schema(engine, nullable=False, expected_fingerprint=fingerprint)
        print("Isolated upgrade and data preservation: PASS", flush=True)

        run(sys.executable, "-m", "alembic", "downgrade", OLD_REVISION)
        verify_schema(engine, nullable=True, expected_fingerprint=fingerprint)
        print("Isolated downgrade: PASS", flush=True)

        run(sys.executable, "-m", "alembic", "upgrade", NEW_REVISION)
        verify_schema(engine, nullable=False, expected_fingerprint=fingerprint)
        print("Isolated re-upgrade: PASS", flush=True)

        print(run(sys.executable, "-m", "alembic", "check"), end="")
        print(run(
            sys.executable, "-m", "pytest", "-q",
            "--basetemp=" + str(work / "pytest"),
            "tests/unit/test_application_contracts.py",
            "tests/unit/test_orm_metadata.py",
            "tests/unit/test_task045_usage_location_code.py",
            "tests/unit/test_task045_stanowiska_view.py",
            "tests/integration/test_product_usage_repositories.py",
        ), end="")
        print("TASK-046 isolated validation: PASS", flush=True)
    finally:
        if engine is not None:
            engine.dispose()
        if (data / "postmaster.pid").exists():
            run(str(pg_bin / "pg_ctl.exe"), "-D", str(data), "-m", "fast", "-w", "stop")
        assert work.resolve().parent == (repo / ".venv").resolve()
        shutil.rmtree(work)


if __name__ == "__main__":
    main()
