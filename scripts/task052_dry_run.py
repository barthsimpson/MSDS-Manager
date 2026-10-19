"""Developer-only Evidence JSON dry run; no DB or filesystem writes."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.application.use_cases.plan_evidence_json_import import PlanEvidenceJsonImport
from app.infrastructure.config import load_settings
from app.infrastructure.db.repositories.evidence_identity_read import SqlAlchemyEvidenceIdentityRead
from app.infrastructure.db.session import create_engine_from_settings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence_json", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.evidence_json.read_text(encoding="utf-8"))
    engine = create_engine_from_settings(load_settings())
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SET TRANSACTION READ ONLY")
            with Session(bind=connection) as session:
                plans = PlanEvidenceJsonImport(SqlAlchemyEvidenceIdentityRead(session)).execute(payload)
            connection.rollback()
        print(json.dumps([asdict(plan) for plan in plans], ensure_ascii=False, default=str, indent=2))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
