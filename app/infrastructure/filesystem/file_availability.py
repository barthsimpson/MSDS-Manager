"""Read-only availability checks for references inside configured document roots."""

from pathlib import Path


def source_file_available(root: Path, relative_path: str | None) -> bool:
    if not relative_path:
        return False
    try:
        reference = Path(relative_path)
        if reference.is_absolute() or reference.drive or reference.root:
            return False
        resolved_root = root.resolve()
        candidate = (resolved_root / reference).resolve()
        return candidate.is_relative_to(resolved_root) and candidate.is_file()
    except (OSError, ValueError, RuntimeError):
        return False
