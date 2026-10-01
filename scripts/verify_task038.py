"""Validate TASK-038 on a disposable PostgreSQL cluster."""

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

    work = Path(tempfile.mkdtemp(prefix="task038-", dir=repo / ".venv")).resolve()
    assert work.parent == (repo / ".venv").resolve()
    data = work / "postgres"
    env["DATABASE_URL"] = f"postgresql+psycopg://task038@127.0.0.1:{port}/msds_manager"
    env["SDS_ROOT_PATH"] = str(work / "sds")
    env["BHP_EVIDENCE_ROOT_PATH"] = str(work / "evidence")
    (work / "sds").mkdir()
    (work / "evidence").mkdir()
    command_number = 0

    def run(*args: str) -> str:
        nonlocal command_number
        command_number += 1
        description = (f"{Path(args[0]).name} -c <inline validation>"
                       if "-c" in args[:3] else " ".join(args[:4]))
        print("RUN:", description, flush=True)
        output_path = work / f"command-{command_number}.log"
        with output_path.open("wb") as output_file:
            result = subprocess.run(
                args, cwd=repo, env=env, stdout=output_file,
                stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW,
            )
        output = output_path.read_text(encoding="utf-8", errors="replace")
        if result.returncode:
            raise RuntimeError(
                f"Command failed: {' '.join(args)}\n{output}"
            )
        return output

    try:
        run(str(pg_bin / "initdb.exe"), "-D", str(data), "-U", "task038",
            "--auth=trust", "--encoding=UTF8", "--locale=C")
        run(str(pg_bin / "pg_ctl.exe"), "-D", str(data), "-l", str(work / "postgres.log"),
            "-o", f"-p {port} -h 127.0.0.1", "-w", "start")
        run(str(pg_bin / "createdb.exe"), "-h", "127.0.0.1", "-p", str(port),
            "-U", "task038", "msds_manager")
        run(sys.executable, "-m", "alembic", "upgrade", "a97e2cb7f31d")
        run(sys.executable, "-c", """
from sqlalchemy import create_engine, text
from app.infrastructure.config import load_settings
engine = create_engine(load_settings().database_url)
with engine.begin() as connection:
    connection.execute(text('''INSERT INTO decision_evidence
        (evidence_id, relative_path, evidence_type, file_format, file_status)
        VALUES ('task038-historical', 'archive/old.pdf', 'DOCUMENT', 'PDF', 'AVAILABLE')'''))
engine.dispose()
""")
        run(sys.executable, "-m", "alembic", "upgrade", "head")
        run(sys.executable, "-c", """
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import Session
from app.infrastructure.config import load_settings
from app.infrastructure.db.models import DecisionEvidenceModel
from app.infrastructure.db.repositories.decision_evidence import from_model, to_model
from app.domain.models import DecisionEvidence
from app.domain.enums import EvidenceType, EvidenceFileFormat, FileAvailabilityStatus

engine = create_engine(load_settings().database_url)
assert 'original_filename' in {c['name'] for c in inspect(engine).get_columns('decision_evidence')}
with Session(engine) as session:
    old = session.get(DecisionEvidenceModel, 'task038-historical')
    assert old is not None and from_model(old).original_filename is None
    evidence = DecisionEvidence(
        evidence_id='task038-new', original_filename='Source Approval.PDF',
        relative_path='imported/technical-uuid.pdf', evidence_type=EvidenceType.DOCUMENT,
        file_format=EvidenceFileFormat.PDF, file_status=FileAvailabilityStatus.AVAILABLE,
    )
    session.add(to_model(evidence))
    session.commit()
with Session(engine) as session:
    assert from_model(session.get(DecisionEvidenceModel, 'task038-new')) == evidence
engine.dispose()
""")
        run(sys.executable, "-m", "alembic", "downgrade", "a97e2cb7f31d")
        run(sys.executable, "-c", """
from sqlalchemy import create_engine, inspect, text
from app.infrastructure.config import load_settings
engine = create_engine(load_settings().database_url)
assert 'original_filename' not in {c['name'] for c in inspect(engine).get_columns('decision_evidence')}
with engine.connect() as connection:
    assert connection.scalar(text('SELECT count(*) FROM decision_evidence')) == 2
engine.dispose()
""")
        run(sys.executable, "-m", "alembic", "upgrade", "head")
        run(sys.executable, "-c", """
from sqlalchemy import create_engine, text
from app.infrastructure.config import load_settings
engine = create_engine(load_settings().database_url)
with engine.begin() as connection:
    connection.execute(text("DELETE FROM decision_evidence WHERE evidence_id LIKE 'task038-%'"))
engine.dispose()
""")
        run(sys.executable, "-m", "pytest", "-q", "-W", "error::sqlalchemy.exc.SAWarning",
            "--basetemp=" + str(work / "pytest"),
            "tests/unit/test_decision_evidence_mapping.py",
            "tests/unit/test_domain_models.py",
            "tests/unit/test_orm_metadata.py",
            "tests/unit/test_register_bhp_decision.py",
            "tests/integration/test_task023_bhp_decision.py")
        current = run(sys.executable, "-m", "alembic", "current")
        assert "b379f54c12a0" in current, current
        run(sys.executable, "-m", "alembic", "check")
        print("TASK-038 isolated migration and focused validation: PASS")
    finally:
        if (data / "postmaster.pid").exists():
            run(str(pg_bin / "pg_ctl.exe"), "-D", str(data), "-m", "fast", "-w", "stop")
        assert work.resolve().parent == (repo / ".venv").resolve()
        shutil.rmtree(work)
        print("Disposable PostgreSQL cluster removed.")


if __name__ == "__main__":
    main()
