"""A non-persistent assessment store, for a composition that injects its own
evidence store and no assessment store (tests and isolated probes), so such a
build never writes assessment history into the shared `var/` root."""

from __future__ import annotations

from assetops_backend.analytics.models import AssessmentHistory


class MemoryAssessmentStore:
    def __init__(self) -> None:
        self._histories: dict[str, AssessmentHistory] = {}

    def load_history(self, site_id: str) -> AssessmentHistory:
        return self._histories.get(site_id, AssessmentHistory(site_id=site_id))

    def save_history(self, history: AssessmentHistory) -> None:
        self._histories[history.site_id] = history
