"""DD-1a2 (DD1a2-R, L2, own `*_test` DB): the B-22 Kobo day shapes on the registered demo Kobo Site. Registered-Site
measurements are what bind (the pre-flight's template figures bind nothing).

- G0 `test_g0_...`: the 18:00 and 24:00 states of `kobo-steady-day` + `kobo-rest-mill` and of `kobo-steady-before-mill`
  + `kobo-rest-before-mill`, and the night after it, through the `_shifted` registered drafter. Fails on a stop.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from test_dd1a1_registered_kobo import _shifted, registered  # noqa: F401  (the module fixture)

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")
#: DD1a1-R15's bound at a cut that is not a story start.
SOC_BOUND, FUEL_BOUND = 0.5, 0.5


def _strip(d: dict) -> dict:
    return {k: v for k, v in d.items() if k not in ("probe_id", "interval")}


def test_g0_the_day_chains_on_the_registered_site(registered) -> None:  # noqa: F811
    import probe_kobo_nights as probe

    probes, handover = probe.day_chains(_shifted(registered))
    committed = json.loads(probe.derive.HANDOVER.read_text(encoding="utf-8"))
    print("\nDD1a2-R G0, registered KOBO-001 (local time):")
    for key in ("D-dusk", "D-dusk-run", "B-dusk", "B-dusk-run", "B-early"):
        v = probes[key]
        print(f"  {key:11} end {v['measured_end']} starts {v['generator_starts']} generator "
              f"{v['generator_intervals_local']} fuel used {v['fuel_used_l']} L min SoC {v['min_soc']}")
    for key in ("kobo-rest-before-mill", probe.derive.BEFORE_NIGHT):
        print(f"  start of {key}: {handover[key]['start']}")
    # STOPPED at 18:00 and 24:00 (`day_chains` refuses otherwise); 0 starts inside 06:00-20:00
    for key in ("D-dusk", "D-dusk-run", "B-dusk", "B-dusk-run"):
        assert probes[key]["measured_end"]["generator"] == "STOPPED", key
    for key in ("D-dusk", "B-dusk"):
        assert probes[key]["generator_starts"] == 0, key
    for key in ("D-dusk-run", "B-dusk-run"):
        assert all(a >= "20:00" for a, _ in probes[key]["generator_intervals_local"]), key
    # `steady`: the 24:00 within R15's bound of `kobo-night-early`'s declared start
    declared = committed["handover"]["kobo-night-early"]["start"]
    end = probes["D-dusk-run"]["measured_end"]
    assert abs(end["soc"] - declared["soc"]) <= SOC_BOUND and abs(end["fuel"] - declared["fuel"]) <= FUEL_BOUND, end
    # the committed handover file is this measurement
    assert {k: _strip(v) for k, v in probes.items()} == {k: _strip(committed["probes"][k]) for k in probes}
    assert {k: _strip(v) for k, v in handover.items()} == {k: _strip(committed["handover"][k]) for k in handover}
