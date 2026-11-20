"""4d unit 3 (spec §4.3): the litre inputs over the fuel-balance store and the assessment store.

Both stores come from their own domains' compositions (the configuration-persistence guard); `dispose` releases both.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from assetops_backend.structure.litres.inputs import StoreLitreInputs


@dataclass(frozen=True)
class LitreInputsService:
    inputs: StoreLitreInputs
    dispose: Callable[[], None]


def build_litre_inputs(database_url: str | None) -> LitreInputsService:
    from assetops_backend.analytics.composition import build_postgres_assessment_store
    from assetops_backend.fuel_balance.composition import build_fuel_balance_store

    fuel = build_fuel_balance_store(database_url)
    try:
        assessments = build_postgres_assessment_store(database_url)
    except BaseException:
        fuel.dispose()  # L1
        raise

    def dispose() -> None:
        fuel.dispose()
        assessments.dispose()

    return LitreInputsService(StoreLitreInputs(fuel, assessments), dispose)


__all__ = ["LitreInputsService", "build_litre_inputs"]
