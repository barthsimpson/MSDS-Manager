"""Run TASK-026 checks on a disposable local PostgreSQL cluster (Windows).

Uses installed PostgreSQL binaries and existing migrations. The configured
operational database is never used. Run with .venv/Scripts/python.exe.
"""

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
    env = os.environ.copy()
    env["PATH"] = str(pg_bin) + os.pathsep + env.get("PATH", "")
    env["PYTHONUTF8"] = "1"
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    work = Path(tempfile.mkdtemp(prefix="task026-", dir=repo / ".venv")).resolve()
    assert work.parent == (repo / ".venv").resolve()
    data = work / "postgres"
    command_number = 0

    def run(*args: str, check: bool = True) -> str:
        nonlocal command_number
        command_number += 1
        print("RUN:", " ".join(args), flush=True)
        # pg_ctl's background server inherits pipe handles on Windows; use a
        # file so subprocess.run waits for pg_ctl, not for the server to exit.
        output_path = work / f"command-{command_number}.log"
        with output_path.open("wb") as output_file:
            result = subprocess.run(
                args, cwd=repo, env=env, stdout=output_file, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        output = output_path.read_text(encoding="utf-8", errors="replace")
        print(output, end="", flush=True)
        if check:
            result.check_returncode()
        return output

    try:
        for name in ("sds", "evidence"):
            (work / name).mkdir()
        env["DATABASE_URL"] = f"postgresql+psycopg://task026@127.0.0.1:{port}/msds_manager"
        env["SDS_ROOT_PATH"] = str(work / "sds")
        env["BHP_EVIDENCE_ROOT_PATH"] = str(work / "evidence")
        run(str(pg_bin / "initdb.exe"), "-D", str(data), "-U", "task026",
            "--auth=trust", "--encoding=UTF8", "--locale=C")
        run(str(pg_bin / "pg_ctl.exe"), "-D", str(data), "-l", str(work / "postgres.log"),
            "-o", f"-p {port} -h 127.0.0.1", "-w", "start")
        run(str(pg_bin / "createdb.exe"), "-h", "127.0.0.1", "-p", str(port),
            "-U", "task026", "msds_manager")
        run(sys.executable, "-m", "alembic", "upgrade", "head")
        if len(sys.argv) >= 3 and sys.argv[1] == "--diagnose":
            targets = sys.argv[2:]
            output = run(
                sys.executable, "-m", "pytest", *targets, "-vv", "-x",
                "--tb=long", "-W", "error::sqlalchemy.exc.SAWarning",
                "--basetemp=" + str(work / "diagnostic"), check=False,
            )
            expected = f"{len(targets)} passed"
            print("DIAGNOSTIC RESULT:", "PASS" if expected in output else "FAIL")
            return
        phases = (
            ("focused", "tests/unit/test_task026_supervisory.py"),
            ("integration", "tests/integration/test_task026_supervisory_read_model_postgresql.py"),
            ("regression", "tests"),
        )
        for phase, target in phases:
            run(sys.executable, "-m", "pytest", "-q", "-W", "error::sqlalchemy.exc.SAWarning",
                "--basetemp=" + str(work / phase), target)
        run(sys.executable, "-m", "alembic", "current")
        run(sys.executable, "-m", "alembic", "check")
        fixture_tables = (
            "manufacturers", "products", "usage_locations", "product_usage_locations",
            "product_history", "usage_location_history", "product_usage_location_history",
            "sds_documents", "safety_profiles", "sds_components",
            "bhp_decisions", "decision_evidence",
        )
        fixture_query = " UNION ALL ".join(
            f"SELECT '{table}', count(*) FROM {table}" for table in fixture_tables
        )
        remaining = run(
            str(pg_bin / "psql.exe"), "-h", "127.0.0.1", "-p", str(port),
            "-U", "task026", "-d", "msds_manager", "-At", "-F", "|",
            "-c", fixture_query,
        )
        counts = dict(line.split("|") for line in remaining.strip().splitlines())
        assert set(counts) == set(fixture_tables), "Fixture count query was incomplete"
        assert all(count == "0" for count in counts.values()), counts
        print("PostgreSQL fixture cleanup: PASS (12 empty business tables).", flush=True)
    finally:
        if (data / "postmaster.pid").exists():
            # Do not remove cluster files if PostgreSQL could not be stopped.
            run(str(pg_bin / "pg_ctl.exe"), "-D", str(data), "-m", "fast", "-w", "stop")
        assert work.resolve().parent == (repo / ".venv").resolve()
        shutil.rmtree(work)
        print("Temporary PostgreSQL cluster and fixtures removed.", flush=True)


if __name__ == "__main__":
    main()
