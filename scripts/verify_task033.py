"""Verify TASK-033 on a disposable PostgreSQL cluster, never the operator DB."""

import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    pg_bin = Path(r"C:\Program Files\PostgreSQL\17\bin")
    if not (pg_bin / "initdb.exe").is_file():
        raise RuntimeError("PostgreSQL 17 binaries are required for isolated validation.")
    env = os.environ.copy()
    env["PATH"] = str(pg_bin) + os.pathsep + env.get("PATH", "")
    env["PYTHONUTF8"] = "1"
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    work = Path(tempfile.mkdtemp(prefix="task033-", dir=repo / ".venv")).resolve()
    assert work.parent == (repo / ".venv").resolve()
    data = work / "postgres"
    command_number = 0

    def run(*args: str) -> str:
        nonlocal command_number
        command_number += 1
        print("RUN:", " ".join(args), flush=True)
        output_path = work / f"command-{command_number}.log"
        with output_path.open("wb") as output_file:
            result = subprocess.run(
                args, cwd=repo, env=env, stdout=output_file,
                stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW,
            )
        output = output_path.read_text(encoding="utf-8", errors="replace")
        print(output, end="", flush=True)
        result.check_returncode()
        return output

    try:
        for name in ("sds", "evidence"):
            (work / name).mkdir()
        env["DATABASE_URL"] = f"postgresql+psycopg://task033@127.0.0.1:{port}/msds_manager"
        env["SDS_ROOT_PATH"] = str(work / "sds")
        env["BHP_EVIDENCE_ROOT_PATH"] = str(work / "evidence")
        run(str(pg_bin / "initdb.exe"), "-D", str(data), "-U", "task033",
            "--auth=trust", "--encoding=UTF8", "--locale=C")
        run(str(pg_bin / "pg_ctl.exe"), "-D", str(data), "-l", str(work / "postgres.log"),
            "-o", f"-p {port} -h 127.0.0.1", "-w", "start")
        run(str(pg_bin / "createdb.exe"), "-h", "127.0.0.1", "-p", str(port),
            "-U", "task033", "msds_manager")
        run(sys.executable, "-m", "alembic", "upgrade", "head")
        run(sys.executable, "-c", '''
from app.infrastructure.config import load_settings
from sqlalchemy import create_engine, text
from uuid import NAMESPACE_URL, uuid5

engine = create_engine(load_settings().database_url)
unit_id = str(uuid5(NAMESPACE_URL, 'msds-manager/unit-of-measure/kg'))
with engine.begin() as connection:
    connection.execute(text("INSERT INTO manufacturers VALUES ('task033-roundtrip', 'Task 033')"))
    connection.execute(text("""INSERT INTO products (
        product_id, product_name, manufacturer_product_code, manufacturer_id,
        use_description, use_restriction, usage_status
    ) VALUES ('task033-roundtrip', 'Task 033', 'task033-roundtrip',
        'task033-roundtrip', '', '', 'ACTIVE')"""))
    connection.execute(text("INSERT INTO usage_locations VALUES ('task033-roundtrip', 'Task 033', 'ACTIVE')"))
    connection.execute(text("""INSERT INTO product_usage_locations (
        product_id, location_id, peak_quantity_value, peak_quantity_unit_id
    ) VALUES ('task033-roundtrip', 'task033-roundtrip', 0, :unit_id)"""), {'unit_id': unit_id})
    connection.execute(text("""INSERT INTO product_usage_location_history (
        history_id, product_id, location_id, peak_quantity_value,
        peak_quantity_unit_id, changed_at
    ) VALUES ('task033-roundtrip', 'task033-roundtrip', 'task033-roundtrip',
        0, :unit_id, now())"""), {'unit_id': unit_id})
engine.dispose()
''')
        run(sys.executable, "-m", "alembic", "downgrade", "e0dd7d6468bf")
        run(sys.executable, "-c", """
from app.infrastructure.config import load_settings
from sqlalchemy import create_engine, text

engine = create_engine(load_settings().database_url)
with engine.begin() as connection:
    for table in ('product_usage_locations', 'product_usage_location_history'):
        row = connection.execute(text(
            f"SELECT peak_quantity_unit, monthly_consumption_unit FROM {table} "
            "WHERE product_id = 'task033-roundtrip'"
        )).one()
        assert row == ('kg', None), (table, row)
    connection.execute(text("DELETE FROM product_usage_location_history WHERE product_id = 'task033-roundtrip'"))
    connection.execute(text("DELETE FROM product_usage_locations WHERE product_id = 'task033-roundtrip'"))
    connection.execute(text("DELETE FROM products WHERE product_id = 'task033-roundtrip'"))
    connection.execute(text("DELETE FROM usage_locations WHERE location_id = 'task033-roundtrip'"))
    connection.execute(text("DELETE FROM manufacturers WHERE manufacturer_id = 'task033-roundtrip'"))
engine.dispose()
""")
        run(sys.executable, "-m", "alembic", "upgrade", "head")
        run(sys.executable, "-m", "pytest", "-q", "-W", "error::sqlalchemy.exc.SAWarning",
            "--basetemp=" + str(work / "pytest"),
            "tests/unit/test_domain_quantity_rules.py",
            "tests/unit/test_domain_models.py",
            "tests/unit/test_orm_metadata.py",
            "tests/unit/test_application_contracts.py",
            "tests/unit/test_history_task015.py",
            "tests/integration/test_product_usage_repositories.py",
            "tests/integration/test_task033_unit_of_measure.py")
        run(sys.executable, "-m", "alembic", "current")
        run(sys.executable, "-m", "alembic", "check")
        print("TASK-033 isolated migration and focused validation: PASS", flush=True)
    finally:
        if (data / "postmaster.pid").exists():
            run(str(pg_bin / "pg_ctl.exe"), "-D", str(data), "-m", "fast", "-w", "stop")
        assert work.resolve().parent == (repo / ".venv").resolve()
        shutil.rmtree(work)
        print("Disposable PostgreSQL cluster removed.", flush=True)


if __name__ == "__main__":
    main()
