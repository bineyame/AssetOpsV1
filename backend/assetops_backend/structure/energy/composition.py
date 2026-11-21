"""4a unit 2 (spec §4.3): the energy inputs over the mini-depth reader and the commercial store.

The reader comes from `MiniDepthRead.from_url` with the evidence domain's link-rows reader; the commercial store is the
one `build_commercial_reads` already made (no second commercial engine). `dispose` disposes the reader only.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from assetops_backend.structure.energy.inputs import StoreEnergyInputs


@dataclass(frozen=True)
class EnergyInputsService:
    inputs: StoreEnergyInputs
    dispose: Callable[[], None]


def build_energy_inputs(database_url: str, store: Any) -> EnergyInputsService:
    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.mini_depth.read import MiniDepthRead

    mini = MiniDepthRead.from_url(database_url, build_link_rows_reader())
    return EnergyInputsService(StoreEnergyInputs(mini, store), mini.dispose)


__all__ = ["EnergyInputsService", "build_energy_inputs"]
