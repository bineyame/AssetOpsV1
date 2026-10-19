"""W2-05b commit 3: the pure `ev-publication/1`/`ev-observation/1` transform and the EV gateway mapping
(`D-2026-10-18-w2-05-buildspec` commit 3). The six shipped documents are exercised end to end in
`host/tests/test_ev_publication.py`; this file covers the transform's guards with private pack forcing."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from assetops_contracts.source_envelope_v4 import V4_EV_CHANNEL_MAPPINGS
from assetops_simulator.gateway.mappings import (
    COLD_V4_GATEWAY_MAPPINGS,
    EV_V4_GATEWAY_MAPPINGS,
    gateway_mapping_for,
)
from assetops_simulator.observation.transform import (
    EV_CONNECTOR_CHANNELS,
    EvChannel,
    ev_public_records,
)
from assetops_simulator.packs.ev_charger import DEFAULT_PARAMETERS, EvChargerPack, EvForcingRow, run_window

SHA = "a" * 64
T0 = datetime(2026, 10, 6, 8, 0, tzinfo=timezone.utc)
CHANNELS = {
    **{(c, name): EvChannel(f"{c}-{name}-device", name, c) for c in ("c1", "c2") for name in EV_CONNECTOR_CHANNELS},
    (None, "import"): EvChannel("site-meter", "import", None),
}


def _at(minutes: int) -> datetime:
    return T0 + timedelta(minutes=minutes)


def _run(rows, minutes: int = 60):
    forcing = tuple(EvForcingRow(_at(m), kind, connector, value) for m, kind, connector, value in rows)
    return run_window(EvChargerPack(DEFAULT_PARAMETERS, scenario_sha256=SHA), start=T0, end=_at(minutes),
                      forcing=forcing)


SESSION = [(0, "PLUG", "c1", "session-1"), (0, "AUTHORIZE", "c1", "ACCEPT"), (1, "REQUEST_KW", "c1", "60"),
           (31, "UNPLUG", "c1", "END")]


def _obs(minute, kind, action, release=None):
    return SimpleNamespace(time=_at(minute), kind=kind, connector="c1", action=action,
                           release_at=None if release is None else _at(release))


def test_ev_publication_has_its_own_closed_schema_4_mapping() -> None:
    assert gateway_mapping_for("ev-publication", 1) is EV_V4_GATEWAY_MAPPINGS
    assert gateway_mapping_for("cold-publication", 1) is COLD_V4_GATEWAY_MAPPINGS
    assert (EV_V4_GATEWAY_MAPPINGS.mapping_id, EV_V4_GATEWAY_MAPPINGS.mapping_version,
            EV_V4_GATEWAY_MAPPINGS.envelope_schema) == ("simulator-lab-gateway-ev", 1, 4)
    assert dict(EV_V4_GATEWAY_MAPPINGS.channels) == dict(V4_EV_CHANNEL_MAPPINGS)
    assert EV_V4_GATEWAY_MAPPINGS.entry("charger-controller", "session-event") is None
    with pytest.raises(LookupError):
        gateway_mapping_for("ev-publication", 2)


def test_series_order_and_ordinals() -> None:
    records = ev_public_records(_run(SESSION), channels=CHANNELS)
    keys = [(r.source_time, {"c1": 0, "c2": 1}.get(r.connector, 2)) for r in records]
    assert keys == sorted(keys)
    at_start = [(r.connector, r.channel) for r in records if r.source_time == _at(1)]
    assert at_start[:2] == [("c1", "state"), ("c1", "session-event")]
    for channel in {(r.connector, r.channel) for r in records}:
        ordinals = sorted(r.transition_ordinal for r in records if (r.connector, r.channel) == channel)
        assert ordinals == list(range(1, len(ordinals) + 1))


def test_a_paused_started_session_reports_zero_energy() -> None:
    # REQUEST_KW 0 at 08:10 pauses allocation; the started session still reports its zero deltas.
    rows = SESSION[:3] + [(10, "REQUEST_KW", "c1", "0"), (31, "UNPLUG", "c1", "END")]
    energy = [(r.interval_start, r.source_time, r.value) for r in ev_public_records(_run(rows), channels=CHANNELS)
              if r.channel == "energy"]
    assert (_at(10), _at(15), "0") in energy and (_at(30), _at(31), "0") in energy
    assert all(r[2] != "0" or r[0] >= _at(10) for r in energy)


def test_site_import_splits_at_any_connector_session_boundary() -> None:
    imports = [(r.interval_start, r.source_time, r.value) for r in ev_public_records(_run(SESSION), channels=CHANNELS)
               if r.channel == "import"]
    assert imports[:2] == [(_at(0), _at(1), "0"), (_at(1), _at(5), "60")]
    assert (_at(30), _at(31), "60") in imports and (_at(31), _at(35), "0") in imports


def test_observation_rows_that_match_nothing_refuse() -> None:
    run = _run(SESSION)
    with pytest.raises(ValueError, match="matches no public report"):
        ev_public_records(run, channels=CHANNELS, observations=(_obs(12, "ENERGY_REPORT", "DROP"),))
    with pytest.raises(ValueError, match="matches no public report"):
        ev_public_records(run, channels=CHANNELS, observations=(_obs(30, "EV_SESSION_END", "HOLD", 65),))
    with pytest.raises(ValueError, match="no active session"):
        ev_public_records(run, channels=CHANNELS, observations=(_obs(45, "EV_SESSION_END", "ADD"),))


def test_a_fault_without_a_scoped_session_is_not_published_pending_q16() -> None:
    run = _run([(0, "FAULT", "c1", "LATCH")])
    with pytest.raises(ValueError, match="no scoped session"):
        ev_public_records(run, channels=CHANNELS)


def test_an_unbound_channel_refuses() -> None:
    channels = dict(CHANNELS)
    del channels[("c2", "power")]
    with pytest.raises(ValueError, match="no bound channel"):
        ev_public_records(_run(SESSION), channels=channels)
