"""OUT-C U4: Depot (w504 positive) early warnings on real Postgres (build sheet OUT-C §2 U4, acceptance 4).

Board on the E window: no PEAK warning (60 of 80 kW, R563); CONNECTOR_OUT_OF_SERVICE exactly when an availability
connector has known unavailable time; whether CHARGER_FAULT fires is recorded (it cannot: no plan, R569)."""
from __future__ import annotations

import json
from dataclasses import replace

from test_out_b4_board_postgres import EV_BUILD, ROOT, _board, _case_db, _child, _client, _record, _serve
from test_out_c1_never_money import money_hits


def test_ev_w504_positive_warnings(monkeypatch, tmp_path) -> None:
    from assetops_backend.site_outcomes import ev

    seen: dict = {}
    with _case_db("ev", "c") as url:
        _child(url, ["-c", EV_BUILD, str(tmp_path), str(ROOT / "tools")])
        built = json.loads((tmp_path / "ev.json").read_text(encoding="utf-8"))
        assert built["status"] == "ready", built.get("status")
        window = {"from": built["evidence_window_E"]["from"], "to": built["evidence_window_E"]["to"]}
        _serve(monkeypatch, url, tmp_path)
        spied = ev.compose

        def compose(ports, **kw):
            def availability(lo, hi, _real=ports.availability):
                seen["availability"] = _real(lo, hi)
                return seen["availability"]

            def overview(lo, hi, _real=ports.overview):
                seen["overview"] = _real(lo, hi)
                return seen["overview"]
            return spied(replace(ports, availability=availability, overview=overview), **kw)

        monkeypatch.setattr(ev, "compose", compose)
        with _client() as c:
            body, _ = _board(c, "EV-LAB-001", "out_c_ev_board", **window)

    kinds = [w["kind"] for w in body["warnings"]]
    connectors = (((seen.get("availability") or {}).get("availability") or {}).get("connectors") or [])
    unavailable = [x.get("label") for x in connectors if (x.get("known_unavailable_seconds") or 0) > 0]
    power = (seen.get("overview") or {}).get("site_power") or {}
    _record("out_c_ev_warnings", {"kinds": kinds, "unavailable_connectors": unavailable, "site_power": power,
                                  "charger_fault_fires": "CHARGER_FAULT_OVERDUE_INSPECTION" in kinds,
                                  "seen": [(w["title"], w["seen"]) for w in body["warnings"]]})
    assert "PEAK_NEAR_IMPORT_LIMIT" not in kinds  # R563: 60 of 80 kW in this dataset
    out = [w for w in body["warnings"] if w["kind"] == "CONNECTOR_OUT_OF_SERVICE"]
    assert bool(out) == bool(unavailable), (out, unavailable)
    assert len(out) == len(unavailable)
    assert "CHARGER_FAULT_OVERDUE_INSPECTION" not in kinds  # R569: no plan in the EV data
    assert all("None" not in w["seen"] for w in body["warnings"])
    assert all(not w["title"].startswith("Connector Connector") for w in out)
    assert money_hits(body["warnings"]) == []
