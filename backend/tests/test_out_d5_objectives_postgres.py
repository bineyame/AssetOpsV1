"""OUT-D U5: declared objectives on the real producer data (build sheet OUT-D §3 U5).

Pattern `test_out_b4_board_postgres.py`: the Kobo `estate` build (board day 2026-10-21), the w502 `positive` cold
build and the w504 `positive` EV build, each in its own `assetops_out_d_<case>_test` database (dropped afterwards),
then the demo objectives file declared through `declare_objective fixture`. Per Site: the board's `objectives`
keys, a "Declared objective" contributor with a verdict chip for each declared measured outcome, no "No objective
declared" on an outcome that has one, and the estate summary's `objective_site_count`. Verdicts and row states are
recorded (printed), and asserted only where the data proves them. Kobo also proves reproducibility: the board at
`known_at = K1` keeps MG-2's text after a v2 declaration; the board now shows the v2 text.
"""
from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    import test_out_b4_board_postgres as b4

DEMO = Path(__file__).resolve().parents[1] / "conversions" / "demo-objectives.json"
LABEL = "Declared objective"
CHIPS = {"Met", "Missed", "Not judged yet"}


def _record(key: str, value: object) -> None:
    print(f"\nOUT-D5 record {key}:", json.dumps(value, default=str))


def _declare(url: str) -> list[dict]:
    """The demo file through the fixture command, against this case database."""
    import io
    from contextlib import redirect_stdout

    from assetops_backend import declare_objective
    from assetops_backend.objectives.composition import build_objective_store

    store = build_objective_store(url)
    out = io.StringIO()
    try:
        with redirect_stdout(out):
            assert declare_objective.main(["fixture", "--file", str(DEMO)], store=store) == 0
    finally:
        store.dispose()
    return [json.loads(line) for line in out.getvalue().splitlines() if line.strip().startswith("{")]


def _declared_lines(body: dict) -> dict[str, dict]:
    return {c["key"].split(":", 1)[1]: c for r in body["rows"] for c in r["contributors"] if c["label"] == LABEL}


def _outcomes(body: dict) -> dict[str, tuple[str, str]]:
    return {o["key"]: (o["state"], o["reason"]) for r in body["rows"] for o in r["outcomes"]}


def _check_site(body: dict, keys: set[str], lined: set[str], key: str) -> None:
    objectives = {o["outcome_key"]: o for o in body["objectives"]}
    lines = _declared_lines(body)
    outcomes = _outcomes(body)
    _record(key, {"read_state": body["read_state"], "states": b4._states(body),
                  "objectives": {k: o["verdict"] for k, o in objectives.items()},
                  "lines": {k: [c["text"], c["confidence"]["label"]] for k, c in lines.items()},
                  "outcomes": {k: outcomes[k] for k in objectives}})
    assert set(objectives) == keys, objectives
    assert set(lines) == lined, lines
    assert all(c["confidence"]["label"] in CHIPS for c in lines.values())
    assert all(outcomes[k][0] != "NO_OBJECTIVE" for k in objectives), outcomes
    assert body["policy_versions"]["objectives"] == "outcome-objectives/2"


def _summary(c, params: dict, key: str) -> dict:
    r = c.get("/api/estate/outcome-summary", params=params)
    assert r.status_code == 200, r.text
    body = r.json()
    _record(key, {"objective_site_count": body["objective_site_count"],
                  "objective_sites_unread": body["objective_sites_unread"],
                  "sites": [(s["site_code"], s["read_state"]) for s in body["sites"]]})
    unread = body["objective_sites_unread"]  # review M2: read Sites plus unread Sites are every Site
    assert isinstance(unread, int) and 0 <= unread <= len(body["sites"])
    assert (body["objective_site_count"] is None) == (unread == len(body["sites"]))
    return body


def test_kobo_estate_objectives_and_reproducibility(monkeypatch, tmp_path) -> None:
    from assetops_backend.site_outcomes import mini

    readings: list[dict] = []
    real = mini.mini_readings

    def spy(dispatch, **kw):  # CH-6a3: MG-1 now comes from the evaluator; only dispatch and `served` are passed
        out = real(dispatch, **kw)
        avoidable, unclear = mini._dispatch_minutes(dispatch)
        readings.append({"dispatch_loaded": dispatch is not None, "avoidable": avoidable, "unclear": unclear,
                         "unserved_kwh": (kw.get("served") or (None, None))[1] and kw["served"][1].get("unserved_kwh"),
                         "readings": {k: [v.value, v.complete, v.actual_text] for k, v in out.items()}})
        return out

    with b4._case_db("kobo", slice_="d") as url:
        spec, _ = b4._build_kobo(url, tmp_path, "estate")
        declared = _declare(url)
        _record("kobo_declared", declared)
        b4._serve(monkeypatch, url, tmp_path)
        b4._pin_kobo(monkeypatch, spec)
        monkeypatch.setattr(mini, "mini_readings", spy)
        with b4._client() as c:
            body, failed = b4._board(c, "KOBO-001", "kobo_d_2026_10_21", date="2026-10-21")
            _record("kobo_board_day_facts", readings[-1])
            _check_site(body, {"MG-1", "MG-2", "MG-5"}, {"MG-1", "MG-2", "MG-5"}, "kobo_d_objectives")
            plan = next(x for r in body["rows"] for x in r["contributors"] if x["key"] == "actual_against_plan")
            _record("kobo_assure_plan", plan["text"])
            assert plan["text"].endswith(" declared objectives met") or " declared objectives met · " in plan["text"]
            summary = _summary(c, {"from": "2026-10-21T00:00:00Z", "to": "2026-10-22T00:00:00Z"}, "kobo_d_summary")
            kobo_read = [s for s in summary["sites"] if s["site_code"] == "KOBO-001"]
            assert summary["objective_site_count"] == (1 if kobo_read and kobo_read[0]["read_state"] != "UNAVAILABLE"
                                                       else None)

            # Reproducibility on real data: K1 after v1; a v2 (target 30) declared later; the board at K1 keeps v1.
            from assetops_backend.objectives.composition import build_objective_store
            from assetops_backend.objectives.model import SYSTEM_DECLARER, Declaration

            store = build_objective_store(url)
            try:
                tenant = store.tenant_id("demo")
                site = store.site_id(tenant, "KOBO-001")
                v1 = {r["outcome_key"]: r for r in store.current(tenant, site, None)}["MG-2"]
                k1 = v1["recorded_at"] + timedelta(microseconds=1)
                at_k1 = {"date": "2026-10-21", "known_at": k1.isoformat().replace("+00:00", "Z")}
                before, _ = b4._board(c, "KOBO-001", "kobo_d_k1_before", **at_k1)
                store.declare(tenant, Declaration(
                    "KOBO-001", "MG-2", "avoidable_generator_minutes", Decimal("30"), None, "DECLARED",
                    "Declared for the demonstration; not a customer target", v1["id"], "out-d-kobo-001-mg-2-v2"),
                    SYSTEM_DECLARER, "SYSTEM_CLI")
            finally:
                store.dispose()
            after, _ = b4._board(c, "KOBO-001", "kobo_d_k1_after", **at_k1)
            now, _ = b4._board(c, "KOBO-001", "kobo_d_now", date="2026-10-21")
    assert _outcomes(after)["MG-2"] == _outcomes(before)["MG-2"]
    assert _declared_lines(after)["MG-2"] == _declared_lines(before)["MG-2"]
    assert _declared_lines(before)["MG-2"]["text"].startswith(
        "Supply cost per kWh: no generator time longer than needed")
    assert _declared_lines(now)["MG-2"]["text"].startswith(
        "Supply cost per kWh: at most 30 min a day with the generator on longer than needed")
    _record("kobo_d_reproducibility", {"k1": str(k1), "before": _declared_lines(before)["MG-2"],
                                       "now": _declared_lines(now)["MG-2"]})


def test_cold_w502_objectives(monkeypatch, tmp_path) -> None:
    import w502_cold_work_walkthrough as w502

    out = tmp_path / "positive"
    out.mkdir()
    with b4._case_db("cold", slice_="d") as url:
        b4._child(url, ["-c", w502.BUILD, "positive", str(out)])
        doc = json.loads((out / "positive.json").read_text(encoding="utf-8"))
        assert doc["blocked"] is None, doc["blocked"]
        _record("cold_declared", _declare(url))
        b4._serve(monkeypatch, url, tmp_path)
        window = dict(zip(("from", "to"), doc["w501"]["window"]))
        with b4._client() as c:
            body, _ = b4._board(c, "COLD-LAB-001", "cold_d_positive", **window)
            _check_site(body, {"CC-1", "CC-6"}, {"CC-1", "CC-6"}, "cold_d_objectives")
            assert {o["outcome_key"]: o["revision_id"] for o in body["objectives"]}["CC-1"] is None  # R584
            summary = _summary(c, b4._covering_day_params(window["from"], window["to"]), "cold_d_summary")
    assert summary["objective_site_count"] == 1


def test_ev_w504_objectives(monkeypatch, tmp_path) -> None:
    with b4._case_db("ev", slice_="d") as url:
        b4._child(url, ["-c", b4.EV_BUILD, str(tmp_path), str(b4.ROOT / "tools")])
        built = json.loads((tmp_path / "ev.json").read_text(encoding="utf-8"))
        assert built["status"] == "ready", built.get("status")
        _record("ev_declared", _declare(url))
        window = {"from": built["evidence_window_E"]["from"], "to": built["evidence_window_E"]["to"]}
        b4._serve(monkeypatch, url, tmp_path)
        with b4._client() as c:
            body, _ = b4._board(c, "EV-LAB-001", "ev_d_positive", **window)
            _check_site(body, {"EV-1", "EV-2"}, {"EV-1"}, "ev_d_objectives")  # EV-2: no board line (R583)
            assert _outcomes(body)["EV-2"][0] == "NOT_MEASURED"
            # R577 (FIX-01): the estate summary over Depot's 6 Oct day refuses 409 ESTATE_SELECTION_INCONSISTENT on
            # this build; recorded, and the count asserted only when the summary is served.
            r = c.get("/api/estate/outcome-summary", params=b4._covering_day_params(window["from"], window["to"]))
    _record("ev_d_summary", {"status": r.status_code, "body": r.json() if r.status_code != 200 else
                             {"objective_site_count": r.json()["objective_site_count"],
                              "objective_sites_unread": r.json()["objective_sites_unread"]}})
    if r.status_code == 200:
        assert r.json()["objective_site_count"] == 1
    else:
        assert (r.status_code, r.json()["detail"]["code"]) == (409, "ESTATE_SELECTION_INCONSISTENT")
