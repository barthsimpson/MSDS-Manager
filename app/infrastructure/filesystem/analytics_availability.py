"""Read-only overlay using the existing document storage path checks."""

from app.application.dto.analytics import AnalyticsFileAvailability as Availability
from app.infrastructure.filesystem.bhp_evidence_storage import BhpEvidenceStorage
from app.infrastructure.filesystem.sds_pdf_storage import SdsPdfStorage


class AnalyticsFileAvailabilityAdapter:
    def __init__(self, sds: SdsPdfStorage, evidence: BhpEvidenceStorage) -> None:
        self._sds = sds
        self._evidence = evidence

    def sds_availability(self, relative_path: str) -> Availability:
        try:
            if not self._sds._root_path.is_dir():
                return Availability.CHECK_FAILED
            return (Availability.AVAILABLE if self._sds.check_availability(relative_path)
                    else Availability.MISSING)
        except (OSError, ValueError, RuntimeError):
            return Availability.CHECK_FAILED

    def evidence_availability(self, relative_path: str) -> Availability:
        try:
            self._evidence.resolve_existing_evidence_path(relative_path)
            return Availability.AVAILABLE
        except FileNotFoundError:
            return Availability.MISSING
        except (OSError, ValueError, RuntimeError):
            return Availability.CHECK_FAILED
