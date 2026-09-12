"""Gated Simulator Lab API surface (product side).

`create_app` includes this router only when `simulator_lab.enabled` is true.
When the flag is false the router is never mounted, so every
`/api/simulator-lab/*` path is genuinely unserved and returns 404 rather than
being served-but-empty or hidden behind UI navigation.

This module owns no simulated world, no private simulator truth, and no run
execution. It reports only that the Simulator Lab surface is served. Run
execution, truth overlays, staging and ingestion are owned by later slices and
must be added behind this same gate, under this prefix.
"""

from __future__ import annotations

from fastapi import APIRouter

SIMULATOR_LAB_API_PREFIX = "/api/simulator-lab"

simulator_lab_router = APIRouter(prefix=SIMULATOR_LAB_API_PREFIX, tags=["simulator-lab"])


@simulator_lab_router.get("/status")
def read_simulator_lab_status() -> dict[str, object]:
    """Report that the Simulator Lab surface is served in this build.

    This is a statement about the gate, not about any Site, device, source, or
    simulator run. No run exists, so none can be started, inspected, rerun, or
    compared against simulator truth.
    """
    return {
        "simulator_lab_enabled": True,
        "run_execution": "not_implemented",
        "truth_overlays": "not_implemented",
    }
