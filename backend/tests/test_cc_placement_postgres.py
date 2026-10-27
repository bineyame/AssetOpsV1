"""CC-R2 (D5) producer assertions on the W3-03 `build_portfolio_fixture` (cold `excursion`, EV `complete`, KOBO-001
W1; one `demo` tenant; a `*_test` DB). Needs ASSETOPS_TEST_DATABASE_URL.

CC-00 facts pinned from this fixture (recorded in `.agent/CC-R2-review-packet.md`): both selected cold Findings
(`COLD_EXCURSION` and `COLD_START_FAILURE`) have a null stored `episode_end`, so each is ACT_NOW with
`EPISODE_OPEN` + `NO_ACTION_RECORDED`; the EV `complete` producer selects no EV Finding, so no EV row exists here
(the EV placement assertion is open question CC-R2-Q2); KOBO-001's W1 row is PRICED in a SINGLE_LINE group with a
closed episode, so it is COMPARE_VALUE / `PRICED_SINGLE`.
"""

from __future__ import annotations

import pytest

from test_w301_estate_index_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_s1_bindings_postgres import engine, store  # noqa: F401 - the S4 mini-grid fixtures
    from test_w301_estate_golden_postgres import cold_chain, ev_chain  # noqa: F401 - the replay factories
    from test_w303_portfolio_fixture_postgres import build_portfolio_fixture
    from test_w303_portfolio_scope_snapshot_postgres import Portfolio

    from assetops_backend.estate.money_invariants import double_count_violations

ACT_NOW_OPEN = {"policy_version": "estate-placement/1", "group": "ACT_NOW", "group_rank": 2, "reasons": [
    {"code": "EPISODE_OPEN", "text": "The episode is still open"},
    {"code": "NO_ACTION_RECORDED", "text": "No accepted Action; open the recommendation"}]}
PRICED_SINGLE = {"policy_version": "estate-placement/1", "group": "COMPARE_VALUE", "group_rank": 3, "reasons": [
    {"code": "PRICED_SINGLE", "text": "Priced cost exposure; no like line to compare with"}]}
GROUPS = ("NEEDS_INVESTIGATION", "ACT_NOW", "COMPARE_VALUE", "UNPRICED_RISK", "MONITOR")


@pytest.fixture(autouse=True)
def _cursor_key(monkeypatch):
    """r1b Q-1b-1: every Portfolio request needs the deployment key; a test-only value, never a default."""
    from assetops_backend.estate.scope import PORTFOLIO_CURSOR_KEY_ENV
    monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, "4d" * 32)


def test_cold_ev_placement_risks_lens_and_paging(request, monkeypatch, capsys) -> None:
    fx = build_portfolio_fixture(request, monkeypatch, capsys)
    view = Portfolio(fx.engine, fx.tenant_id)
    body = view.ok(**fx.window, limit=100)
    assert double_count_violations(body) == []
    assert body["order"] == ("group_rank asc, episode_start desc nulls last, site_code_key asc, site_id asc, "
                             "finding_id asc, finding_revision_id asc")
    rows = body["rows"]
    assert all(r["priority"] is None for r in rows)  # no numeric priority, ever
    assert all(r["placement"]["policy_version"] == "estate-placement/1" and r["confidence"] for r in rows)

    cold = [r for r in rows if r["domain"] == "COLDCHAIN"]
    ev = [r for r in rows if r["domain"] == "EV_CHARGING"]
    (kobo,) = [r for r in rows if r["site_code"] == "KOBO-001"]
    # CC-00: the two cold Findings, each with a null stored episode end, and no EV Finding in this fixture.
    assert sorted(r["mechanism"] for r in cold) == ["COLD_EXCURSION", "COLD_START_FAILURE"]
    assert ev == [] and len(rows) == 3
    for r in cold:
        assert r["episode_end"] is None and r["workflow_label"] == "Recommendation not accepted"
        assert r["placement"] == ACT_NOW_OPEN and r["lens_flags"] == ["RISK"]
        assert (r["confidence"], r["confidence_reasons"]) == (
            "SUPPORTED_SOURCE_COHERENT", ["Supported claim", "Registered simulation source"])
    assert kobo["placement"] == PRICED_SINGLE and kobo["lens_flags"] == ["COST"]
    assert kobo["episode_end"] is not None and kobo["consequence"]["state"] == "PRICED"
    assert body["summary"]["placement_counts"] == {"NEEDS_INVESTIGATION": 0, "ACT_NOW": 2, "COMPARE_VALUE": 1,
                                                   "UNPRICED_RISK": 0, "MONITOR": 0}
    ranks = [r["placement"]["group_rank"] for r in rows]
    assert ranks == sorted(ranks)

    # lens=risks returns exactly the cold and EV rows (here: the two cold rows), on both roots.
    risks = view.ok(**fx.window, lens="risks", limit=100)
    assert [(r["finding_id"], r["finding_revision_id"]) for r in risks["rows"]] == [
        (r["finding_id"], r["finding_revision_id"]) for r in rows if r["domain"] in ("COLDCHAIN", "EV_CHARGING")]
    assert risks["summary"]["placement_counts"] == body["summary"]["placement_counts"]  # over all lenses
    findings = fx.estate().ok("findings", **fx.window, lens="risks", limit=100)
    assert {r["finding_id"] for r in findings["rows"]} == {r["finding_id"] for r in cold}
    assert all(r["confidence"] is None for r in findings["rows"])  # Findings-index rows keep null

    # limit=2 paging returns every row exactly once, in group order, with six-part cursors.
    paged, cursor = [], None
    while True:
        page = view.ok(**fx.window, limit=2, **({} if cursor is None else {"cursor": cursor}))
        paged += page["rows"]
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert [(r["finding_id"], r["finding_revision_id"]) for r in paged] == [
        (r["finding_id"], r["finding_revision_id"]) for r in rows]
    assert [GROUPS.index(r["placement"]["group"]) for r in paged] == sorted(
        GROUPS.index(r["placement"]["group"]) for r in paged)
