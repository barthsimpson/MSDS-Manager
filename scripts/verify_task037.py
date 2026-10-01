"""Run TASK-037 regression on a disposable PostgreSQL cluster."""

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
    work = Path(tempfile.mkdtemp(prefix="task037-", dir=repo / ".venv")).resolve()
    assert work.parent == (repo / ".venv").resolve()
    data = work / "postgres"
    (work / "sds").mkdir()
    (work / "evidence").mkdir()
    env["DATABASE_URL"] = f"postgresql+psycopg://task037@127.0.0.1:{port}/msds_manager"
    env["SDS_ROOT_PATH"] = str(work / "sds")
    env["BHP_EVIDENCE_ROOT_PATH"] = str(work / "evidence")
    command_number = 0

    def run(*args: str) -> str:
        nonlocal command_number
        command_number += 1
        print("RUN:", Path(args[0]).name, " ".join(args[1:3]), flush=True)
        log = work / f"command-{command_number}.log"
        with log.open("wb") as output:
            result = subprocess.run(
                args, cwd=repo, env=env, stdout=output, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        detail = log.read_text(encoding="utf-8", errors="replace")
        if result.returncode:
            raise RuntimeError(f"Validation command failed:\n{detail}")
        return detail

    try:
        run(str(pg_bin / "initdb.exe"), "-D", str(data), "-U", "task037",
            "--auth=trust", "--encoding=UTF8", "--locale=C")
        run(str(pg_bin / "pg_ctl.exe"), "-D", str(data), "-l", str(work / "postgres.log"),
            "-o", f"-p {port} -h 127.0.0.1", "-w", "start")
        run(str(pg_bin / "createdb.exe"), "-h", "127.0.0.1", "-p", str(port),
            "-U", "task037", "msds_manager")
        run(sys.executable, "-m", "alembic", "upgrade", "head")
        result = run(
            sys.executable, "-m", "pytest", "-q", "-W", "error::sqlalchemy.exc.SAWarning",
            "--basetemp=" + str(work / "pytest"),
            "tests/unit/test_bhp_evidence_storage.py",
            "tests/unit/test_import_bhp_evidence.py",
            "tests/unit/test_streamlit_bhp_decision.py",
            "tests/unit/test_register_bhp_decision.py",
            "tests/unit/test_bhp_evidence_validator.py",
            "tests/integration/test_task037_bhp_evidence.py",
            "tests/integration/test_task023_bhp_decision.py",
            "tests/integration/test_task025_sprint4_acceptance.py",
        )
        print(result.strip(), flush=True)
        current = run(sys.executable, "-m", "alembic", "current")
        assert "b379f54c12a0" in current, current
        run(sys.executable, "-m", "alembic", "check")
        print("TASK-037 isolated validation: PASS", flush=True)
    finally:
        if (data / "postmaster.pid").exists():
            run(str(pg_bin / "pg_ctl.exe"), "-D", str(data), "-m", "fast", "-w", "stop")
        assert work.resolve().parent == (repo / ".venv").resolve()
        shutil.rmtree(work)
        print("Disposable PostgreSQL cluster removed.", flush=True)


if __name__ == "__main__":
    main()
