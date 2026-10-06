"""Validate TASK-043 migration and contracts on a disposable PostgreSQL cluster."""

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
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    work = Path(tempfile.mkdtemp(prefix="task043-", dir=repo / ".venv")).resolve()
    assert work.parent == (repo / ".venv").resolve()
    data = work / "postgres"
    env = os.environ.copy()
    env["PATH"] = str(pg_bin) + os.pathsep + env.get("PATH", "")
    env["PYTHONUTF8"] = "1"
    env["DATABASE_URL"] = f"postgresql+psycopg://task043@127.0.0.1:{port}/msds_manager"
    env["SDS_ROOT_PATH"] = str(work / "sds")
    env["BHP_EVIDENCE_ROOT_PATH"] = str(work / "evidence")
    (work / "sds").mkdir()
    (work / "evidence").mkdir()
    command_number = 0

    def run(*args: str) -> str:
        nonlocal command_number
        command_number += 1
        print("RUN:", " ".join(args[:4]) if "-c" not in args[:3]
              else f"{Path(args[0]).name} -c <inline validation>", flush=True)
        output_path = work / f"command-{command_number}.log"
        with output_path.open("wb") as output_file:
            result = subprocess.run(
                args, cwd=repo, env=env, stdout=output_file,
                stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=120,
            )
        output = output_path.read_text(encoding="utf-8", errors="replace")
        if result.returncode:
            raise RuntimeError(f"{' '.join(args[:4])} failed:\n{output}")
        return output

    try:
        run(str(pg_bin / "initdb.exe"), "-D", str(data), "-U", "task043",
            "--auth=trust", "--encoding=UTF8", "--locale=C")
        run(str(pg_bin / "pg_ctl.exe"), "-D", str(data), "-l", str(work / "postgres.log"),
            "-o", f"-p {port} -h 127.0.0.1", "-w", "start")
        run(str(pg_bin / "createdb.exe"), "-h", "127.0.0.1", "-p", str(port),
            "-U", "task043", "msds_manager")
        run(sys.executable, "-m", "alembic", "upgrade", "b379f54c12a0")
        run(sys.executable, "-c", """
from sqlalchemy import create_engine, text
from app.infrastructure.config import load_settings
engine = create_engine(load_settings().database_url)
with engine.begin() as connection:
    connection.execute(text("INSERT INTO usage_locations (location_id, location_name, status) "
                            "VALUES ('task043-pre-migration', 'Historical location', 'ACTIVE')"))
    connection.execute(text("INSERT INTO usage_location_history "
                            "(history_id, location_id, status, changed_at) "
                            "VALUES ('task043-pre-history', 'task043-pre-migration', "
                            "'ACTIVE', CURRENT_TIMESTAMP)"))
engine.dispose()
""")
        run(sys.executable, "-m", "alembic", "upgrade", "head")
        current = run(sys.executable, "-m", "alembic", "current")
        assert "c7e5a82d9043" in current, current
        print(run(sys.executable, "-m", "pytest", "-q", "--basetemp=" + str(work / "pytest"),
                  "tests/unit/test_application_contracts.py",
                  "tests/unit/test_domain_models.py",
                  "tests/unit/test_orm_metadata.py",
                  "tests/integration/test_task043_location_code.py",
                  "tests/integration/test_product_usage_repositories.py",
                  "tests/unit/test_task045_usage_location_code.py",
                  "tests/integration/test_task045_legacy_code_postgresql.py"), end="")
        print(run(sys.executable, "-m", "alembic", "check"), end="")
        print("TASK-043 isolated migration and focused validation: PASS")
    finally:
        if (data / "postmaster.pid").exists():
            run(str(pg_bin / "pg_ctl.exe"), "-D", str(data), "-m", "fast", "-w", "stop")
        assert work.resolve().parent == (repo / ".venv").resolve()
        shutil.rmtree(work)


if __name__ == "__main__":
    main()
