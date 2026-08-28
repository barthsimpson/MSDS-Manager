import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def imported_modules(package_path: Path) -> set[str]:
    modules: set[str] = set()
    for source_path in package_path.rglob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                modules.add(node.module)
    return modules


def test_application_does_not_import_infrastructure_or_database_libraries() -> None:
    imports = imported_modules(PROJECT_ROOT / "app" / "application")
    forbidden_prefixes = (
        "app.infrastructure",
        "sqlalchemy",
        "psycopg",
        "alembic",
    )

    assert not any(
        module.startswith(forbidden_prefixes) for module in imports
    ), imports


def test_domain_does_not_import_outer_layers_or_database_libraries() -> None:
    imports = imported_modules(PROJECT_ROOT / "app" / "domain")
    forbidden_prefixes = (
        "app.application",
        "app.infrastructure",
        "sqlalchemy",
        "psycopg",
        "alembic",
        "streamlit",
    )

    assert not any(
        module.startswith(forbidden_prefixes) for module in imports
    ), imports
