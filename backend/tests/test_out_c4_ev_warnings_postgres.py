"""OUT-C U4: Depot (w504 positive) early warnings on real Postgres (build sheet OUT-C §2 U4, acceptance 4).

Board on the E window: no PEAK warning (60 of 80 kW, R563); CONNECTOR_OUT_OF_SERVICE exactly when an availability
connector has known unavailable time; whether CHARGER_FAULT fires is recorded (it cannot: no plan, R569). OUT-W: the
estate summary on 8 Oct (no event) judges Depot on the period with a plain link; on 6 Oct it refuses 409 (R577)."""
from __future__ import annotations

import json
import time
from dataclasses import replace
from datetime import datetime, timezone

from test_out_b4_board_postgres import EV_BUILD, ROOT, _board, _case_db, _child, _client, _record, _serve
from test_out_c1_never_money import money_hits


def _utc(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


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
            monkeypatch.setattr(ev, "compose", spied)  # the summary's boards must not overwrite the E reads above
            # OUT-W: the summary over 6 Oct (window E) and over 8 Oct (no event)
            start = time.perf_counter()
            r6 = c.get("/api/estate/outcome-summary", params={"from": "2026-10-06T00:00:00Z",
                                                             "to": "2026-10-07T00:00:00Z"})
            seconds = round(time.perf_counter() - start, 3)
            r8 = c.get("/api/estate/outcome-summary", params={"from": "2026-10-08T00:00:00Z",
                                                             "to": "2026-10-09T00:00:00Z"})
        # Architect ruling (a), 2026-10-31, R577: on 6 Oct the estate scope read refuses for this build (a Finding
        # in it has two selected revisions at one cutoff), so the summary honestly refuses 409 before composing a Site.
        # FIX-01 owns the duplicate selected revision; once it lands, this flips to 200 with Depot LATEST_EVENT on
        # window E: window == E, overview_href starting "/sites/EV-LAB-001/ev?from=", Protect equal to `body`'s.
        _record("out_w_ev_summary_day6", {"status": r6.status_code, "body": r6.json(), "seconds": seconds})
        assert r6.status_code == 409, r6.text
        assert r6.json()["detail"]["code"] == "ESTATE_SELECTION_INCONSISTENT", r6.text
        assert r8.status_code == 200, r8.text
        depot8 = next(x for x in r8.json()["sites"] if x["site_code"] == "EV-LAB-001")
        _record("out_w_ev_summary_day8", {k: depot8[k] for k in ("window", "window_basis", "overview_href")})
        assert depot8["window_basis"] == "PERIOD", depot8
        assert (_utc(depot8["window"]["from"]), _utc(depot8["window"]["to"])) == (
            _utc("2026-10-08T00:00:00Z"), _utc("2026-10-09T00:00:00Z")), depot8["window"]
        assert depot8["overview_href"] == "/sites/EV-LAB-001/ev", depot8["overview_href"]

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
