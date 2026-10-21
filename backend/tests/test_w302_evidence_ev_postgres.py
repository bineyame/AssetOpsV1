"""W3-02 commit 1: estate Evidence EV window rows over the real W2-05b/W2-06 EV replay (`complete`).

Four display rows per selected stored EV window citing that window's selected assessment, the three supporting
claims in disclosure, typed EV gaps without BILLING_GAP, and the row-local Site link (closure 5 B5): the exact
window and the row's evidence cutoff, never the estate bounds. Needs ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlsplit

import pytest

from test_w205b_ev_replay_postgres import URL, chain  # noqa: F401 - the W2-05b replay fixture

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    import test_w205b_ev_replay_postgres as w205b
    from test_w206_ev_store_postgres import LATE_HI, LATE_LO, run_worker, select_exact
    from test_w301_estate_index_ev_postgres import day_of, settled
    from test_w301_estate_index_postgres import ESTATE_KEYS, db_now, iso, watermark
    from test_w302_evidence_scope_snapshot_postgres import Evidence
    from assetops_backend.estate import evidence_money
    from assetops_backend.estate.scope import decode_cursor


def at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_w302_evidence_ev_window_rows_links_and_gaps(chain) -> None:  # noqa: F811
    built, estate, day = settled(chain, "complete")
    evidence = Evidence(built.engine, built.tenant_id)
    window = {"from": iso(day), "to": iso(day + timedelta(days=1))}
    body = evidence.ok(**window, limit=100)
    windows = estate.windows(built.tenant_id, built.site_id, "ev_charging", day, day + timedelta(days=1),
                             db_now(built.engine))
    assert windows and body["status"] == "CURRENT" and body["coverage"]["state"] == "COMPLETE"
    assert body["total_count"] == 4 * len(windows) == len(body["rows"])
    mark = watermark(built.engine, built.site_id)
    for w in windows:
        mine = [r for r in body["rows"] if w["window_start"].strftime("%Y-%m-%dT%H:%M:%S.%fZ") in r["capability_key"]]
        assert sorted(r["capability_key"].split("@")[0] for r in mine) == ["availability", "cause", "energy",
                                                                           "sessions"]
        for r in mine:
            assert r["selected_revision_ids"] == [w["selection_id"]] and r["domain"] == "ev_charging"
            assert set(r["source_provenance"]) == ESTATE_KEYS
            assert set(r["source_provenance"]["evidence_ids"]) <= set(w["evidence_ids"])
            assert [c["claim"] for c in r["disclosure"]["supporting_claims"]] == [
                "SITE_POWER_CONTEXT", "POWER_CONSTRAINT", "GROSS_TARIFF_SCENARIO"]
            link = urlsplit(r["links"]["site_readiness"])
            q = {k: at(v[0]) for k, v in parse_qs(link.query).items()}
            assert link.path.endswith("/ev/evidence") and r["links"]["site_readiness_label"] is None
            assert (q["from"], q["to"]) == (w["window_start"], w["window_end"])  # never the estate day bounds
            assert q["known_at"] == mark <= at(body["window"]["known_at"]) + timedelta(seconds=1)
    assert all(g["domain"] == "ev_charging" and g["gap_code"] != "BILLING_GAP" and g["missing_role"] is None
               for g in body["gaps"])
    assert body["summary"]["capability_count"] == body["total_count"]
    assert body["summary"]["full_count"] is not None  # complete and current: truth counts are present


def test_w302_evidence_ev_meter_gap_from_unknown_meter_seconds(chain, monkeypatch) -> None:  # noqa: F811
    """c1-q2: a selected session with positive unknown meter seconds gives the estate METER_GAP group through the
    public `capabilities_on` `unknown_meter`, unlocking that window's energy row; the token carries the selected
    session revision IDs (c1-q3(5))."""
    built, estate, day = settled(chain, "missing-meter")
    evidence = Evidence(built.engine, built.tenant_id)
    body = evidence.ok(**{"from": iso(day), "to": iso(day + timedelta(days=1))}, limit=100)
    assert body["status"] == "CURRENT" and body["coverage"]["state"] == "COMPLETE"
    meter = [g for g in body["gaps"] if g["gap_code"] == "METER_GAP"]
    assert len(meter) == 1 and meter[0]["domain"] == "ev_charging" and meter[0]["missing_role"] is None
    assert meter[0]["site_ids"] == [str(built.site_id).lower()]
    assert meter[0]["unlocks"] and all(key.startswith("energy@") for key in meter[0]["unlocks"])
    rows = {r["capability_key"]: r for r in body["rows"]}
    assert all("METER_GAP" in rows[key]["gap_codes"] for key in meter[0]["unlocks"])
    # c1 r1 L5: the Site token input carries the selected session revision IDs beyond the assessment revision.
    captured = []
    real = evidence_money.selection_token
    monkeypatch.setattr(evidence_money, "selection_token", lambda *x: captured.append(x[-1]) or real(*x))
    evidence.ok(**{"from": iso(day), "to": iso(day + timedelta(days=1))}, limit=100)
    token_ids = set(captured[-1][0]["selected_assessment_revision_ids"])
    row_ids = {x for r in body["rows"] for x in r["selected_revision_ids"]}
    assert row_ids and row_ids < token_ids  # the session revision IDs are token input (their 409 fence is pure-tested)


LIVE_KEYS = ("capability_key", "raw_state", "readiness", "selected_revision_ids", "gap_codes", "current_ceiling")


def test_w302_evidence_live_cursor_later_disposition_preserves_rows_and_token(chain, monkeypatch) -> None:  # noqa: F811
    """c1 r1 M1: page one is live; a Site disposition decided after the cursor cutoff (the ordinary ingestion path,
    never backdated) moves only the W2 watermark. Page two, at the frozen cursor whose cutoff is earlier than its
    read time, keeps the page-one selection token and the rows' states, IDs and gaps: no row turns UNKNOWN."""
    built, _, _ = settled(chain, "late-record")
    select_exact(built, LATE_LO, LATE_HI)
    day = day_of(LATE_LO)
    evidence = Evidence(built.engine, built.tenant_id)
    params = {"from": iso(day), "to": iso(day + timedelta(days=1)), "limit": 4}
    whole = evidence.ok(**{**params, "limit": 100})
    first = evidence.ok(**params)
    assert first["next_cursor"] and first["status"] == "CURRENT" and len(whole["rows"]) > 4
    assert "UNKNOWN" not in {r["raw_state"] for r in whole["rows"]}
    cursor_k = at(decode_cursor("evidence", first["next_cursor"])["known_at"])
    late_at = db_now(built.engine)
    assert late_at > cursor_k
    monkeypatch.setattr(w205b, "LATE_DECISION", late_at)
    built.advance_late()
    run_worker(built)
    assert watermark(built.engine, built.site_id) > cursor_k  # a later disposition: the watermark moved
    second = evidence.ok(**params, cursor=first["next_cursor"])
    assert second["selection_token"] == first["selection_token"]
    assert [{k: r[k] for k in LIVE_KEYS} for r in second["rows"]] == [
        {k: r[k] for k in LIVE_KEYS} for r in whole["rows"][4:8]]
    assert "UNKNOWN" not in {r["raw_state"] for r in second["rows"]}
    assert second["gaps"] == whole["gaps"] and second["summary"]["full_count"] == whole["summary"]["full_count"]


def test_w302_evidence_live_cursor_changed_selected_id_is_409(chain) -> None:  # noqa: F811
    """Control for the M1 test: the late phase's backdated disposition re-heads a selected window, so the same live
    cursor is refused 409 `ESTATE_BASIS_CHANGED`."""
    built, _, _ = settled(chain, "late-record")
    select_exact(built, LATE_LO, LATE_HI)
    day = day_of(LATE_LO)
    evidence = Evidence(built.engine, built.tenant_id)
    params = {"from": iso(day), "to": iso(day + timedelta(days=1)), "limit": 4}
    first = evidence.ok(**params)
    assert first["next_cursor"]
    built.advance_late()
    run_worker(built)
    response = evidence.get(**params, cursor=first["next_cursor"])
    assert (response.status_code, response.json()["detail"]["code"]) == (409, "ESTATE_BASIS_CHANGED")
