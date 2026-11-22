"""6c (D-P6.41): the structure read as the evaluation sees it. The read's own failures (a database that cannot answer)
are `StoreUnavailable`; the evaluation maps that to `STRUCTURE_UNAVAILABLE` and nothing else, so a defect in the read
is a traceback and never reads as an outage. `decisions/composition.py` is the only importer."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from assetops_backend.decisions.records import StoreUnavailable

__all__ = ["GuardedStructureRead"]


class GuardedStructureRead:
    def __init__(self, read: Any) -> None:
        self._read = read

    def site_inputs(self, site: Any, month: str, known_at: datetime | None = None) -> Any:
        try:
            return self._read.site_inputs(site, month, known_at)
        except SQLAlchemyError as error:
            raise StoreUnavailable(str(error)) from error
