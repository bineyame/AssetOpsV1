"""Composition for the S5-01 Site Overview read: one process seam, built once per app and disposed at shutdown.

Each dependency comes from its own domain's composition (no adapter is imported here). The consequence read is
the production `build_consequence_read_service`, which wires the persisted LR-01 money gate (Architect LR-01
deviations item 5); no ELIGIBLE stub is used outside isolated unit tests.
"""

from __future__ import annotations

from typing import Any


def build_site_overview_read(database_url: str | None, ledger: Any, thresholds: Any = None,
                             environment: str = "default"):
    from assetops_backend.scheduling.composition import build_upstream_currentness
    from assetops_backend.site_overview.read import SiteOverviewRead

    # Review L4: one seam per process. The money read and Finding store are the seam's own (the production
    # `build_consequence_read_service` and Finding store), so `dispose` releases every engine this read owns.
    upstream = build_upstream_currentness(database_url, thresholds)
    return SiteOverviewRead(upstream, ledger, upstream.consequence_read, upstream.findings, environment=environment)
