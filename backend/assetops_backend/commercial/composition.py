"""3A1 (spec §4): composes the commercial record service; the only importer of the Postgres adapter. `3A2` mounts
the HTTP intake on it."""
from __future__ import annotations

from datetime import datetime, timezone

from assetops_backend.commercial.adapters.postgres_commercial_store import PostgresCommercialStore
from assetops_backend.commercial.service import CommercialRecords


def _now() -> datetime:
    return datetime.now(timezone.utc)


def build_commercial_records(database_url: str) -> CommercialRecords:
    return CommercialRecords(PostgresCommercialStore(database_url), clock=_now)
