"""The assessment store port. Domain records only; no path or format here."""

from __future__ import annotations

from typing import Protocol

from assetops_backend.analytics.models import AssessmentHistory


class AssessmentStoreUnavailable(Exception):
    """The store cannot be read or written, or holds a document it cannot read."""


class AssessmentStore(Protocol):
    def load_history(self, site_id: str) -> AssessmentHistory:
        """A Site's assessment history; empty if none was ever written."""
        ...

    def save_history(self, history: AssessmentHistory) -> None:
        """Replace a Site's history in ONE atomic write."""
        ...
