"""DD3d-a (D-DD.153): the tank's absolute tolerance floor, 2 x its declared level accuracy, in force over a month.

Read on the same Foundation read the litre inputs use (`FuelReadPort.read_at`). The margin factor, the accuracy values
and the rule for the one value in force are the night check's own (`fuel_balance`), imported by name.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, localcontext
from typing import Any
from uuid import UUID

from assetops_backend.fuel_balance.rules import ACCURACY_BASES, TANK_MARGIN_FACTOR, declared_for
from assetops_backend.fuel_balance.service import ACCURACY_BASIS_KEY, ACCURACY_KEY, accuracy_values
from assetops_backend.structure.litres.inputs import FuelReadPort
from assetops_backend.structure.observe.observe import Floor, _context


class StoreFloorRead:
    """`FloorReadPort` over the fuel-balance store."""

    def __init__(self, fuel: FuelReadPort) -> None:
        self._fuel = fuel

    def read(self, tenant_id: UUID, site_id: UUID, window: tuple[datetime, datetime],
             known_at: datetime) -> Floor | None:
        lo, hi = window

        def work(tx: Any) -> Floor | None:
            tanks = [a for a in tx.active_assets() if a.asset_type == "FUEL_TANK"]
            if len(tanks) != 1:
                return None
            revisions = tx.properties(tanks[0].asset_code, (ACCURACY_KEY, ACCURACY_BASIS_KEY), lo, hi)
            a = declared_for(accuracy_values(revisions), lo, hi, ACCURACY_BASES)
            if a is None:
                return None
            with localcontext(_context()):
                accuracy = Decimal(a.value.numerator) / Decimal(a.value.denominator)
                return Floor(TANK_MARGIN_FACTOR * accuracy, accuracy, a.basis, a.revision_id)

        return self._fuel.read_at(tenant_id, site_id, known_at, work)


__all__ = ["StoreFloorRead"]
