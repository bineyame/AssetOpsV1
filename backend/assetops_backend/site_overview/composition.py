"""Composition for the S5-01 Site Overview read: one process seam, built once per app and disposed at shutdown.

Each dependency comes from its own domain's composition (no adapter is imported here). The consequence read is
the production `build_consequence_read_service`, which wires the persisted LR-01 money gate (Architect LR-01
deviations item 5); no ELIGIBLE stub is used outside isolated unit tests.
"""

from __future__ import annotations

from typing import Any


def build_site_overview_read(database_url: str | None, ledger: Any, thresholds: Any = None,
                             environment: str = "default"):
    from assetops_backend.analytics.composition import build_finding_store
    from assetops_backend.financials.composition import build_consequence_read_service
    from assetops_backend.scheduling.composition import build_upstream_currentness
    from assetops_backend.site_overview.read import SiteOverviewRead

    return SiteOverviewRead(build_upstream_currentness(database_url, thresholds), ledger,
                            build_consequence_read_service(database_url), build_finding_store(database_url),
                            environment=environment)
