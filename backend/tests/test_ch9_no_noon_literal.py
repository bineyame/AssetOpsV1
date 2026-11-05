"""CH-9 (CH9-R2 Q4): exactly one function, `mini_depth.store.daylight_hours`, decides a day's renewable hours.

The five readers (worker `reconcile`, the page read's `hour_windows`, `read_selected_renewable_basis`, the study's
`day_heads` and the `daylight_headroom_kw` measure with its chain reader) must not name a noon or daylight hour of
their own: no `12` literal, no `local_noon`, no `NOON_HOURS`, no "noon"/"midday" text. Each reaches the rule
through `daylight_hours` (or, for `hour_windows`, the `daylight` callable its caller builds from it).
"""

from __future__ import annotations

import inspect
import re

import pytest

from assetops_backend.chain.adapters.postgres_chain_inputs import PostgresChainInputs
from assetops_backend.chain.measure_impls import RenewableHeadroom
from assetops_backend.mini_decisions import projection
from assetops_backend.mini_depth import read, store
from assetops_backend.mini_depth.worker import MiniDepthWorker

FORBIDDEN = re.compile(r"noon|midday|\b12\b|NOON_HOURS|MIDDAY", re.IGNORECASE)

READERS = {
    "reconcile": (MiniDepthWorker.reconcile, "daylight_hours("),
    "hour_windows": (read.hour_windows, "daylight("),
    "read_selected_renewable_basis": (read.MiniDepthRead.read_selected_renewable_basis, "daylight_hours("),
    "day_heads": (projection.day_heads, "daylight_hours("),
    "measure": (RenewableHeadroom, ".renewable_hours("),
    "measure_reader": (PostgresChainInputs.renewable_hours, "daylight_hours("),
    # Not a reader, but it checks each copied hour: its integrity messages name the study hour, never noon.
    "day_row": (projection.day_row, "def day_row"),
}


@pytest.mark.parametrize("name", sorted(READERS))
def test_reader_names_no_hour_of_its_own(name: str) -> None:
    fn, via = READERS[name]
    source = inspect.getsource(fn)
    assert via in source, f"{name} does not reach the rule through {via!r}"
    found = FORBIDDEN.findall(source)
    assert not found, f"{name} names its own noon/daylight hour: {found}"


def test_the_one_rule_owns_the_no_binding_hour() -> None:
    # The unmeasured (no PV binding) hours are declared once, in the store, beside `daylight_hours`.
    assert store.NO_PV_BINDING.hours == store.NOON_HOURS and not store.NO_PV_BINDING.measured
    assert "NO_PV_BINDING" in inspect.getsource(store.daylight_hours)


def test_guard_is_not_vacuous() -> None:
    # The pattern catches each spelling a reader could reintroduce.
    for bad in ("local_noon(day, tz)", "hours = (12,)", "NOON_HOURS", "the noon hour", "PERIOD_MIDDAY"):
        assert FORBIDDEN.search(bad), bad
    assert not FORBIDDEN.search("daylight_hours(c, t, s, d, k).study_hours")
