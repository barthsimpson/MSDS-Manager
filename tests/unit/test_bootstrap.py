from importlib import import_module
from pathlib import Path


def test_app_package_and_base_structure_are_available() -> None:
    app = import_module("app")
    project_root = Path(__file__).resolve().parents[2]

    assert app.__name__ == "app"
    assert (project_root / "app" / "domain").is_dir()
    assert (project_root / "app" / "application").is_dir()
    assert (project_root / "app" / "infrastructure").is_dir()
    assert (project_root / "app" / "presentation").is_dir()
