"""Read-only control of the previously prepared TASK-060 acceptance database."""

import json
from pathlib import Path
from urllib.request import urlopen

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.infrastructure.config import load_settings
from app.presentation.streamlit.composition import ShellComposition


state = json.loads(Path("tmp/task060_acceptance_state.json").read_text(encoding="utf-8"))
settings = load_settings()
url = make_url(settings.database_url).set(database=state["database"])
engine = create_engine(url, connect_args={"options": "-c default_transaction_read_only=on"})
factory = sessionmaker(bind=engine, expire_on_commit=False)
with engine.connect() as connection:
    connection.execute(text("SET TRANSACTION READ ONLY"))
    revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
    audit_count = connection.scalar(text(
        "SELECT count(*) FROM sds_invalidation WHERE product_id=:product_id"
    ), {"product_id": state["product_id"]})
    product_exists = connection.scalar(text(
        "SELECT EXISTS(SELECT 1 FROM products WHERE product_id=:product_id)"
    ), {"product_id": state["product_id"]})
composition = ShellComposition(
    engine=engine, session_factory=factory, products=(),
    sds_root_path=Path(state["root"]) / "sds",
    bhp_evidence_root_path=Path(state["root"]) / "bhp",
    settings=settings,
)
history = composition.list_sds_history(state["product_id"])
sds_root = Path(state["root"]) / "sds"
files = {
    item.document_status.value: (sds_root / item.relative_path).is_file()
    for item in history
}
with urlopen(f"http://127.0.0.1:{state['port']}/_stcore/health", timeout=5) as response:
    health = response.status
engine.dispose()
print(json.dumps({
    "database": state["database"], "revision": revision,
    "product_exists": product_exists,
    "history_count": len(history),
    "statuses": sorted(item.document_status.value for item in history),
    "pdf_files_present": files,
    "audit_count": audit_count, "health_http": health,
}, ensure_ascii=False))
