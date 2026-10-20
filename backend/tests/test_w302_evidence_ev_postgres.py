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
    from test_w301_estate_index_ev_postgres import settled
    from test_w301_estate_index_postgres import ESTATE_KEYS, db_now, iso, watermark
    from test_w302_evidence_scope_snapshot_postgres import Evidence


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


def test_w302_evidence_ev_meter_gap_from_unknown_meter_seconds(chain) -> None:  # noqa: F811
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
