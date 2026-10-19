"""The composed application: the product, with a kernel wired behind the Lab.

This is the process entry point for a build that can EXECUTE. Run it from `host/`:

    ..\\.venv\\Scripts\\python.exe -m uvicorn lab_app:app --reload

`assetops_backend.main:app` still serves everything else and stays the entry point
for a build that does not execute. The difference is one argument and it is the
whole of the composition: `create_app` takes an execution port it cannot build,
and this module is the only place in the repository allowed to build one, because
it is the only place that may import a kernel and the product at once.

## Why the entry point moved rather than the import

The obvious alternative was for `assetops_backend.main` to import the leaf and
compose the port itself. That is exactly what `tools/checks/dependency-direction`
`.ps1` forbids and it forbids it for a reason worth restating: a product module
importing the leaf would let any later product module reach a kernel through it,
and the truth barrier would then be a naming convention. Moving the entry point
costs one line in a runbook and keeps the ban structural.

## The gate is read here too, and the port is built only when it is open

`load_feature_flags` decides. With the Lab disabled no router is mounted, so a
port would be unreachable anyway - and it is still not built, for the reason the
run store is not: a closed build must not create a directory, open a file or hold
a handle belonging to a capability it does not serve. A test asserts that with the
gate closed an exploding artifact store is never touched.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI

from assetops_backend.config import FeatureFlags, database_url, load_feature_flags
from assetops_backend.main import create_app
from assetops_backend.runs.registered_release import publisher_for
from assetops_backend.scenarios.composition import build_scenario_repository
from assetops_backend.sites.composition import build_foundation_store

from lab_execution import HostLabExecution
from cold_lab import StoreColdInputs
from ev_lab import StoreEvInputs
from gateway_publication import RegisteredGatewayPublisher
from assetops_gateway.ipc import GatewayLink

#: S2-01b: where the Lab host reaches its colocated gateway process. Both name
#: the gateway's own provisioning (`python -m assetops_gateway serve --config`):
#: the pipe/socket address and the protected local credential file it created.
#: Unset means no gateway, and registered runs then stage nothing - fail closed.
GATEWAY_ADDRESS_ENV = "ASSETOPS_GATEWAY_ADDRESS"
GATEWAY_CREDENTIAL_ENV = "ASSETOPS_GATEWAY_CREDENTIAL"


def gateway_from_environment() -> RegisteredGatewayPublisher | None:
    address = os.environ.get(GATEWAY_ADDRESS_ENV)
    credential = os.environ.get(GATEWAY_CREDENTIAL_ENV)
    if not address or not credential:
        return None
    return RegisteredGatewayPublisher(GatewayLink(address, Path(credential)))


def build_app(flags: FeatureFlags | None = None, **overrides: object) -> FastAPI:
    """The product application with an execution port behind the gated Lab.

    `overrides` are passed through to `create_app`, so a test composes fakes for
    the stores exactly as it does against the product entry point and gets the
    real kernel behind them.
    """
    resolved = load_feature_flags() if flags is None else flags
    execution = None
    if resolved.simulator_lab_enabled:
        # W2-02: the cold re-read port reads the same Foundation store and scenario repository
        # `create_app` is composed with - resolved here exactly as `create_app` resolves them, test
        # overrides included, and handed on so both sides hold the same objects.
        if overrides.get("foundation_store") is None and overrides.get("site_repository") is None:
            overrides["foundation_store"] = build_foundation_store(database_url())
        if overrides.get("scenario_repository") is None:
            overrides["scenario_repository"] = build_scenario_repository()
        execution = HostLabExecution(
            gateway=gateway_from_environment(),
            source_publisher=publisher_for(database_url()),
            cold_inputs=StoreColdInputs(overrides.get("foundation_store"), overrides["scenario_repository"]),
            # W2-05b q4 Q23: the EV re-read port over the same two objects.
            ev_inputs=StoreEvInputs(overrides.get("foundation_store"), overrides["scenario_repository"]),
        )
    return create_app(resolved, execution=execution, **overrides)


app = build_app()
