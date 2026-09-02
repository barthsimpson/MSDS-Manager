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
        "app.presentation",
        "sqlalchemy",
        "psycopg",
        "alembic",
        "streamlit",
    )

    assert not any(
        module.startswith(forbidden_prefixes) for module in imports
    ), imports


def test_domain_does_not_import_outer_layers_or_database_libraries() -> None:
    imports = imported_modules(PROJECT_ROOT / "app" / "domain")
    forbidden_prefixes = (
        "app.application",
        "app.infrastructure",
        "app.presentation",
        "sqlalchemy",
        "psycopg",
        "alembic",
        "streamlit",
    )

    assert not any(
        module.startswith(forbidden_prefixes) for module in imports
    ), imports


def test_repositories_do_not_commit_or_expose_delete_operations() -> None:
    repositories_path = (
        PROJECT_ROOT / "app" / "infrastructure" / "db" / "repositories"
    )
    forbidden_calls: list[tuple[Path, str]] = []
    forbidden_methods: list[tuple[Path, str]] = []

    for source_path in repositories_path.glob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "commit"
            ):
                forbidden_calls.append((source_path, node.func.attr))
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name in {"delete", "remove"}
            ):
                forbidden_methods.append((source_path, node.name))

    assert forbidden_calls == []
    assert forbidden_methods == []
