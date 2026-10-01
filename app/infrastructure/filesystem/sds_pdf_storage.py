"""Create new SDS PDFs inside the configured root, without overwrite."""

from pathlib import Path, PureWindowsPath
from uuid import UUID, uuid4


class SdsPdfStorage:
    def __init__(self, root_path: Path, *, uuid_factory=uuid4, max_attempts: int = 5) -> None:
        self._root_path = root_path
        self._uuid_factory = uuid_factory
        self._max_attempts = max_attempts

    def _imported_directory(self) -> Path:
        root = self._root_path
        if not root.is_dir():
            raise OSError("SDS_ROOT_PATH nie istnieje lub nie jest katalogiem.")
        resolved_root = root.resolve()
        imported = root / "imported"
        imported.mkdir(exist_ok=True)
        resolved_imported = imported.resolve()
        if resolved_imported.parent != resolved_root:
            raise OSError("Katalog importu SDS wychodzi poza SDS_ROOT_PATH.")
        return resolved_imported

    def store_new_pdf(self, pdf_bytes: bytes) -> str:
        imported = self._imported_directory()
        for _ in range(self._max_attempts):
            storage_id = self._uuid_factory()
            if not isinstance(storage_id, UUID):
                raise ValueError("Niepoprawny identyfikator storage SDS.")
            target = imported / f"{storage_id}.pdf"
            if target.resolve().parent != imported:
                raise OSError("Docelowy plik SDS wychodzi poza SDS_ROOT_PATH.")
            try:
                with target.open("xb") as output:
                    try:
                        output.write(pdf_bytes)
                    except Exception:
                        output.close()
                        target.unlink()
                        raise
            except FileExistsError:
                continue
            return f"imported/{storage_id}.pdf"
        raise FileExistsError("Nie udało się wyznaczyć wolnej nazwy pliku SDS.")

    def _owned_path(self, relative_path: str) -> Path:
        parts = Path(relative_path).parts
        if len(parts) != 2 or parts[0] != "imported":
            raise ValueError("Niepoprawna ścieżka pliku importu SDS.")
        try:
            storage_id = UUID(Path(parts[1]).stem)
        except ValueError as error:
            raise ValueError("Niepoprawny identyfikator pliku importu SDS.") from error
        if parts[1] != f"{storage_id}.pdf":
            raise ValueError("Niepoprawna nazwa pliku importu SDS.")
        imported = self._imported_directory()
        target = imported / parts[1]
        if target.resolve().parent != imported:
            raise OSError("Plik importu SDS wychodzi poza SDS_ROOT_PATH.")
        return target

    def confirm_exists(self, relative_path: str) -> None:
        if not self._owned_path(relative_path).is_file():
            raise FileNotFoundError(f"Brak zapisanego pliku SDS: {relative_path}")

    def resolve_sds_path(self, relative_path: str) -> Path:
        if not isinstance(relative_path, str) or not relative_path or "\x00" in relative_path:
            raise ValueError("Niepoprawna ścieżka SDS.")
        windows_path = PureWindowsPath(relative_path)
        if windows_path.is_absolute() or windows_path.drive or windows_path.root:
            raise ValueError("Ścieżka SDS musi być względna.")
        normalized = relative_path.replace("\\", "/")
        reference = Path(normalized)
        if reference.is_absolute() or ".." in reference.parts:
            raise ValueError("Ścieżka SDS wychodzi poza SDS_ROOT_PATH.")
        root = self._root_path.resolve()
        target = (root / reference).resolve()
        if not target.is_relative_to(root):
            raise ValueError("Ścieżka SDS wychodzi poza SDS_ROOT_PATH.")
        return target

    def check_availability(self, relative_path: str) -> bool:
        return self.resolve_sds_path(relative_path).is_file()

    def read_sds(self, relative_path: str) -> bytes:
        target = self.resolve_sds_path(relative_path)
        if not target.is_file():
            raise FileNotFoundError("Plik SDS jest obecnie niedostępny.")
        return target.read_bytes()

    def remove_unregistered_file(self, relative_path: str) -> None:
        self._owned_path(relative_path).unlink()
