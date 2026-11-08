"""DIESEL-K3: the one place fuel-balance storage is chosen (rule 1 of `tools/checks/configuration-persistence.ps1`).

The store receives the Action store (readings, SFC and no-load history) from `actions/composition.py` and K2's
caller-connection fuel records read from `work/composition.py`, by injection.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from assetops_backend.actions.composition import build_action_store
from assetops_backend.fuel_balance.adapters.postgres_fuel_balance_store import PostgresFuelBalanceStore
from assetops_backend.fuel_balance.service import FuelBalanceService


def build_fuel_balance_store(database_url: str | None, *, fuel_records: Callable[..., Any] | None = None,
                             test_db_clock_override: Callable[[], datetime] | None = None
                             ) -> PostgresFuelBalanceStore:
    if fuel_records is None:
        from assetops_backend.work.composition import build_fuel_records_reader

        fuel_records = build_fuel_records_reader()
    return PostgresFuelBalanceStore(database_url, actions=build_action_store(database_url),
                                    fuel_records=fuel_records, test_db_clock_override=test_db_clock_override)


def build_fuel_balance_service(store: PostgresFuelBalanceStore) -> FuelBalanceService:
    return FuelBalanceService(store)


def build_fuel_finding_service(database_url: str | None, *,
                               test_db_clock_override: Callable[[], datetime] | None = None):
    """DIESEL-K4a (§9j.6): the unexplained-fuel Finding service over the fuel-balance store (its clock, lock and
    window read), the assessment store (shared transaction, `fuel_balance_persist`), the Finding store
    (`fuel_apply`), the consequence store (`fuel_residual_append`) and the Trial comparison's diesel price selection.
    `test_db_clock_override` is test-only and constructor-only, as K3's."""
    from assetops_backend.analytics.composition import build_finding_store, build_postgres_assessment_store
    from assetops_backend.financials.composition import build_consequence_store, build_trial_comparison_ports
    from assetops_backend.fuel_balance.findings_service import FuelFindingService, FuelFindingStores

    return FuelFindingService(FuelFindingStores(
        fuel=build_fuel_balance_store(database_url, test_db_clock_override=test_db_clock_override),
        assessments=build_postgres_assessment_store(database_url), findings=build_finding_store(database_url),
        consequences=build_consequence_store(database_url),
        price_selection=build_trial_comparison_ports(database_url).price_selection))
