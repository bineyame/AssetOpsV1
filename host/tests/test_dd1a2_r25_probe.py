"""DD1a2-R Q8.3 gate (R25): the `steady` add-day kind on the Foundation after the Action's 25 % reserve. The three runs of
a live ST-7 day (`kobo-night-early`, `kobo-steady-day`, `kobo-rest-mill`) are probed on the registered KOBO-001 with the
reserve at 25 %. Pass: STOPPED at 18:00 and 24:00, 0 starts 06:00-20:00. Fail: the kind runs 06:00-18:00 only and reads
partly checked (no Architect return)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

import pytest

from test_dd1a1_registered_kobo import KNOWN_AT, _shifted, registered  # noqa: F401  (the module fixture)

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")


def _publish_reserve(store, value: float) -> None:
    import test_s1_bindings_postgres as pgb
    from assetops_backend.sites.foundation_service import FoundationService

    known = datetime.fromisoformat(KNOWN_AT.replace("Z", "+00:00")) - timedelta(hours=1)
    service = FoundationService(store, "demo", pgb.Clock(known))
    tenant = service.tenant()
    service.publish_battery_reserve(tenant, service.site(tenant, "KOBO-001"), asset_code="battery", value=value,
                                    effective_from=known, note="DD1a2 R25 probe: the Action's reserve")


def test_r25_the_steady_add_day_kind_on_the_25_percent_reserve(registered) -> None:  # noqa: F811
    import probe_kobo_nights as probe

    draft = _shifted(registered)
    before_probes, _ = probe.day_chains(draft)  # the 30 % reserve (G0's measurement)
    _publish_reserve(registered, 25.0)
    probes, handover = probe.day_chains(draft)  # raises SystemExit if STOPPED fails at 18:00 or 24:00
    committed = json.loads(probe.derive.HANDOVER.read_text(encoding="utf-8"))
    start = committed["handover"]["kobo-night-early"]["start"]
    night_doc, _ = probe.derive.night_document("kobo-night-early", start)
    night = probe.measure("R25-night-early", night_doc, f"{probe.DAY}T21:00:00Z", f"{probe.NEXT}T03:00:00Z", draft)
    print("\nDD1a2-R25, registered KOBO-001, battery reserve 25 % (local time):")
    for key in ("D-dusk", "D-dusk-run"):
        v = probes[key]
        print(f"  {key:10} end {v['measured_end']} starts {v['generator_starts']} generator "
              f"{v['generator_intervals_local']} min SoC {v['min_soc']}")
    print(f"  night-early (steady kind): end {night['measured_end']} generator {night['generator_intervals_local']} "
          f"min SoC {night['min_soc']}")
    for key in ("D-dusk", "D-dusk-run"):
        b, a = before_probes[key], probes[key]
        print(f"  {key:10} min SoC at 30 %: {b['min_soc']}; at 25 %: {a['min_soc']}")
    for key in ("D-dusk", "D-dusk-run"):
        assert probes[key]["measured_end"]["generator"] == "STOPPED", key
    assert probes["D-dusk"]["generator_starts"] == 0
    assert all(a >= "20:00" for a, _ in probes["D-dusk-run"]["generator_intervals_local"])
    # non-vacuity: the reserve reached the model, so the night's generator pattern differs from the 30 % case
    assert probes["B-early"]["generator_intervals_local"] != before_probes["B-early"]["generator_intervals_local"] \
        or probes["B-early"]["fuel_used_l"] != before_probes["B-early"]["fuel_used_l"], "the 25 % reserve changed nothing"
