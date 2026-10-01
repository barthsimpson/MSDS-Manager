"""Controlled filesystem access for BHP decision evidence."""

from pathlib import Path, PureWindowsPath
from uuid import UUID, uuid4


ALLOWED_SUFFIXES = {".msg", ".pdf", ".jpg", ".jpeg", ".png"}


class BhpEvidenceStorage:
    def __init__(self, root_path: Path, *, uuid_factory=uuid4, max_attempts: int = 5) -> None:
        self._root = root_path.resolve()
        self._uuid_factory = uuid_factory
        self._max_attempts = max_attempts

    def _require_root(self) -> Path:
        if not self._root.is_dir():
            raise OSError("BHP_EVIDENCE_ROOT_PATH nie istnieje lub nie jest katalogiem.")
        return self._root

    @staticmethod
    def _suffix(original_filename: str) -> str:
        if (
            not isinstance(original_filename, str)
            or not original_filename.strip()
            or original_filename in {".", ".."}
            or any(mark in original_filename for mark in ("/", "\\", ":", "\x00"))
        ):
            raise ValueError("Podaj nazwę dowodu bez ścieżki.")
        suffix = Path(original_filename).suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            raise ValueError("Nieobsługiwany format dowodu decyzji.")
        return suffix

    def validate_new_evidence(self, original_filename: str, content: bytes) -> str:
        suffix = self._suffix(original_filename)
        if not isinstance(content, bytes) or not content:
            raise ValueError("Plik dowodu jest pusty.")
        self._require_root()
        return suffix

    def _imported_directory(self) -> Path:
        root = self._require_root()
        imported = root / "imported"
        imported.mkdir(exist_ok=True)
        resolved = imported.resolve()
        if resolved.parent != root:
            raise OSError("Katalog importu dowodów wychodzi poza BHP_EVIDENCE_ROOT_PATH.")
        return resolved

    def store_new_evidence(self, original_filename: str, content: bytes) -> str:
        suffix = self.validate_new_evidence(original_filename, content)
        imported = self._imported_directory()
        for _ in range(self._max_attempts):
            storage_id = self._uuid_factory()
            if not isinstance(storage_id, UUID):
                raise ValueError("Niepoprawny identyfikator storage dowodu.")
            name = f"{storage_id}{suffix}"
            target = imported / name
            if target.resolve().parent != imported:
                raise OSError("Docelowy dowód wychodzi poza BHP_EVIDENCE_ROOT_PATH.")
            try:
                with target.open("xb") as output:
                    try:
                        output.write(content)
                    except Exception:
                        output.close()
                        target.unlink()
                        raise
            except FileExistsError:
                continue
            return f"imported/{name}"
        raise FileExistsError("Nie udało się wyznaczyć wolnej nazwy dowodu.")

    def _resolved_file(self, relative_path: str) -> tuple[Path, str]:
        self._require_root()
        if not isinstance(relative_path, str) or not relative_path:
            raise ValueError("Ścieżka dowodu jest wymagana.")
        if PureWindowsPath(relative_path).drive or PureWindowsPath(relative_path).root:
            raise ValueError("Ścieżka dowodu musi być względna.")
        normalized = relative_path.replace("\\", "/")
        parts = normalized.split("/")
        if any(part in {"", ".", ".."} or ":" in part for part in parts):
            raise ValueError("Niepoprawna ścieżka dowodu.")
        path = (self._root / Path(*parts)).resolve()
        if not path.is_relative_to(self._root):
            raise ValueError("Ścieżka dowodu wychodzi poza BHP_EVIDENCE_ROOT_PATH.")
        if path.suffix.lower() not in ALLOWED_SUFFIXES:
            raise ValueError("Nieobsługiwany format dowodu decyzji.")
        return path, "/".join(parts)

    def resolve_existing_evidence_path(self, relative_path: str) -> str:
        path, normalized = self._resolved_file(relative_path)
        if not path.is_file():
            raise FileNotFoundError(f"Brak pliku dowodu: {normalized}")
        if path.stat().st_size == 0:
            raise ValueError("Plik dowodu jest pusty.")
        return normalized

    def validate(self, relative_path: str) -> str:
        return self.resolve_existing_evidence_path(relative_path)

    def confirm_exists(self, relative_path: str) -> None:
        self.resolve_existing_evidence_path(relative_path)

    def check_availability(self, relative_path: str) -> bool:
        try:
            self.resolve_existing_evidence_path(relative_path)
            return True
        except (ValueError, OSError, RuntimeError):
            return False

    def read_existing_evidence(self, relative_path: str) -> bytes:
        self.resolve_existing_evidence_path(relative_path)
        path, _ = self._resolved_file(relative_path)
        return path.read_bytes()

    def list_existing_evidence(self) -> tuple[tuple[str, str], ...]:
        root = self._require_root()
        paths = []
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in ALLOWED_SUFFIXES:
                continue
            relative = path.relative_to(root).as_posix()
            if self.check_availability(relative):
                paths.append((relative, path.name))
        return tuple(sorted(paths))

    def remove_unregistered_evidence(self, relative_path: str) -> None:
        path, normalized = self._resolved_file(relative_path)
        parts = normalized.split("/")
        if len(parts) != 2 or parts[0] != "imported":
            raise ValueError("Można usunąć wyłącznie niezarejestrowany import dowodu.")
        try:
            storage_id = UUID(Path(parts[1]).stem)
        except ValueError as error:
            raise ValueError("Niepoprawny identyfikator importu dowodu.") from error
        if parts[1] != f"{storage_id}{path.suffix.lower()}":
            raise ValueError("Niepoprawna nazwa importu dowodu.")
        path.unlink()
