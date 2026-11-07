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
