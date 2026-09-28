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

from fastapi import FastAPI

from assetops_backend.config import FeatureFlags, load_feature_flags
from assetops_backend.main import create_app

from lab_execution import HostLabExecution


def build_app(flags: FeatureFlags | None = None, **overrides: object) -> FastAPI:
    """The product application with an execution port behind the gated Lab.

    `overrides` are passed through to `create_app`, so a test composes fakes for
    the stores exactly as it does against the product entry point and gets the
    real kernel behind them.
    """
    resolved = load_feature_flags() if flags is None else flags
    execution = (
        HostLabExecution() if resolved.simulator_lab_enabled else None
    )
    return create_app(resolved, execution=execution, **overrides)


app = build_app()
