"""Local configuration loading for infrastructure components."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"
REQUIRED_VARIABLES = (
    "DATABASE_URL",
    "SDS_ROOT_PATH",
    "BHP_EVIDENCE_ROOT_PATH",
)


class ConfigurationError(ValueError):
    """Raised when local infrastructure configuration is invalid."""


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str
    sds_root_path: Path
    bhp_evidence_root_path: Path

    def root_path_statuses(self) -> dict[str, bool]:
        """Report whether configured document roots are existing directories."""

        return {
            "SDS_ROOT_PATH": self.sds_root_path.is_dir(),
            "BHP_EVIDENCE_ROOT_PATH": self.bhp_evidence_root_path.is_dir(),
        }


def read_env_file(path: Path) -> dict[str, str]:
    """Read the minimal KEY=VALUE subset supported by the project."""

    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ConfigurationError(
                f"Invalid configuration line {line_number}: expected KEY=VALUE."
            )

        key, value = line.split("=", maxsplit=1)
        key = key.strip()
        if not key:
            raise ConfigurationError(
                f"Invalid configuration line {line_number}: key is empty."
            )
        values[key] = value.strip()

    return values


def load_settings(
    env_file: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> Settings:
    """Load required settings, with process variables overriding the .env file."""

    values = read_env_file(DEFAULT_ENV_FILE if env_file is None else env_file)
    process_environment = os.environ if environ is None else environ

    for key in REQUIRED_VARIABLES:
        if key in process_environment:
            values[key] = process_environment[key].strip()

    missing = [key for key in REQUIRED_VARIABLES if not values.get(key)]
    if missing:
        raise ConfigurationError(
            "Missing required configuration variables: " + ", ".join(missing)
        )

    return Settings(
        database_url=values["DATABASE_URL"],
        sds_root_path=Path(values["SDS_ROOT_PATH"]),
        bhp_evidence_root_path=Path(values["BHP_EVIDENCE_ROOT_PATH"]),
    )
