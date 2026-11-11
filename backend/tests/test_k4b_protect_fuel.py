"""DIESEL-K4b (`.agent/build-sheet-DIESEL-1.md` §9j.10-§9j.13, rulings DIESEL-1-R3j and R3j2): the Protect row's
unexplained-fuel placement (MG-8 "Fuel accounted for", the Finding issue and thread line, the node), the Portfolio
Protect lines (never summed), the SITES_DISRUPTED exclusion and the empty clean-day declaration. L0, fake ports."""
from __future__ import annotations

import json
from dataclasses import replace
from datetime import date, timedelta
from fractions import Fraction
from types import SimpleNamespace

import pytest

from assetops_backend.chain import claims, vocabulary as v
from assetops_backend.chain.lifecycle import ChainConfigError, parse_thread_lifecycle
from assetops_backend.chain.adapters.file_chain_config import load_thread_lifecycle
from assetops_backend.chain.composition import check_declared_chain_graph
from assetops_backend.site_outcomes import board, mini
from assetops_backend.site_outcomes.board import (
    ActionFact, FindingFact, SiteFacts, assemble, thread_line_item, with_threads)
from assetops_backend.site_outcomes.read import portfolio_cards

import test_out_b2_mini as B2

C, DAY, T = B2.C, B2.DAY, B2.T
PROTECT, COST, GROW, ASSURE = mini.PROTECT, mini.COST, mini.GROW, mini.ASSURE
NIGHT = DAY - timedelta(days=1)  # night D − 1: [19 Oct 18:00, 20 Oct 12:00) local = [T(19, 15), T(20, 9))
MG8_NA = {"key": "MG-8", "label": "Fuel accounted for", "state": "NOT_APPLICABLE",
          "reason": "CONFIGURATION_NOT_APPLICABLE"}


def window(state="UNEXPLAINED", night=NIGHT, low="61.24", high="98.36", reason=None, end=None):
    start = T(night.day, 15)
    return SimpleNamespace(night_date=night, window_start=start, window_end=end or start + timedelta(hours=18),
                           state=state, reason=reason, residual_low=Fraction(low), residual_high=Fraction(high),
                           tank_asset_id="tank")


PRICED = {"state": "PRICED", "amount_low": "76.55", "amount_high": "122.95", "currency": "USD"}


def finding(fid="fuel1", lifecycle="SUPPORTED", w=None, consequence=PRICED):
    w = w or window()
    return SimpleNamespace(finding_id=fid, revision_id=fid + "r", revision_no=1, lifecycle=lifecycle,
                           night_date=w.night_date, window=w, consequence=consequence, created_at=w.window_end)


def fuel_ports(fake, *, has=True, windows=(), findings=(), refuse=()):
    def go(name, value):
        fake.calls.append((name, ()))
        if name in refuse:
            raise RuntimeError(f"{name} refused")
        return value
    return replace(fake.ports(), fuel_has_windows=lambda: go("fuel_has_windows", has),
                   fuel_windows=lambda lo, hi: go("fuel_windows", tuple(windows)),
                   fuel_findings=lambda lo, hi: go("fuel_findings", tuple(findings)))


def compose(ports):
    comp = mini.compose(ports, site_code=C, day=DAY, site_timezone=B2.ZONE)
    return comp, {r["category"]: r for r in B2.checked(assemble(comp.facts))}


def outcome(row, key):
    return next(o for o in row["outcomes"] if o["key"] == key)


# ---- MG-8 applicability and state ---------------------------------------------------------------------------------

def test_no_window_site_gets_mg8_not_applicable_and_reads_nothing_else() -> None:
    fake = B2.Fake()
    comp, rows = compose(fuel_ports(fake, has=False))
    assert outcome(rows[PROTECT], "MG-8") == MG8_NA
    assert comp.read_state == B2.run()[0].read_state
    assert ("fuel_windows", ()) not in fake.calls and ("fuel_findings", ()) not in fake.calls
    assert "unexplained_fuel" not in (rows[PROTECT]["nodes"] or {})
    assert all(c["key"] != mini.FUEL_STOCK_KEY for c in rows[PROTECT]["contributors"])


def test_kobo_protect_row_equals_the_pre_k4b_row_except_the_mg8_entry(monkeypatch) -> None:
    """Must fail on any other Protect diff: the pre-K4b row is the same board with MG-8 out of the catalogue."""
    _, rows = compose(fuel_ports(B2.Fake(), has=False))
    monkeypatch.setattr(board, "SITE_OUTCOMES", tuple(o for o in board.SITE_OUTCOMES if o.key != "MG-8"))
    _, before = compose(fuel_ports(B2.Fake(), has=False))
    now = dict(rows[PROTECT])
    now["outcomes"] = [o for o in now["outcomes"] if o["key"] != "MG-8"]
    assert rows[PROTECT]["outcomes"][-1] == MG8_NA
    assert now == before[PROTECT]
    for cat in (GROW, COST, ASSURE):
        assert rows[cat] == before[cat]


def test_failed_applicability_read_is_partial_and_mg8_unknown_never_na() -> None:
    comp, rows = compose(fuel_ports(B2.Fake(), refuse=("fuel_has_windows",)))
    assert comp.read_state == "PARTIAL" and "fuel_has_windows" in comp.failed
    assert outcome(rows[PROTECT], "MG-8")["state"] == "UNKNOWN"


def test_failed_finding_read_is_partial_and_mg8_unknown() -> None:
    comp, rows = compose(fuel_ports(B2.Fake(), windows=[window("WITHIN_MARGIN")], refuse=("fuel_findings",)))
    assert comp.read_state == "PARTIAL" and "fuel_findings" in comp.failed
    assert outcome(rows[PROTECT], "MG-8")["state"] == "UNKNOWN"


@pytest.mark.parametrize("windows", [[], [window("NOT_ASSESSED", reason="MISSING_OPENING")],
                                     [window("WITHIN_MARGIN", night=NIGHT - timedelta(days=1))]])
def test_mg8_unknown_without_an_assessed_window_for_night_d_minus_1(windows) -> None:
    _, rows = compose(fuel_ports(B2.Fake(), windows=windows))
    assert outcome(rows[PROTECT], "MG-8")["state"] == "UNKNOWN"


def test_mg8_settled_without_a_finding_is_not_attention() -> None:
    _, rows = compose(fuel_ports(B2.Fake(), windows=[window("WITHIN_MARGIN")]))
    assert outcome(rows[PROTECT], "MG-8")["state"] not in ("UNKNOWN", "NEEDS_ATTENTION", "NOT_APPLICABLE")


def test_open_supported_fuel_finding_needs_attention_on_protect_only() -> None:
    _, rows = compose(fuel_ports(B2.Fake(), windows=[window()], findings=[finding()]))
    assert outcome(rows[PROTECT], "MG-8")["state"] == "NEEDS_ATTENTION"
    issue = next(i for i in rows[PROTECT]["issues"] if i["kind"] == "FINDING")
    assert issue["text"] == "Unexplained fuel overnight" and issue["role"] == "MOVES"
    assert issue["href"] == f"/sites/{C}/fuel-findings/fuel1"  # the FUEL_FINDING Ref (K5's page)
    for cat in (GROW, COST, ASSURE):
        assert all("Unexplained fuel" not in i["text"] for i in rows[cat]["issues"])


def test_applied_fuel_thread_is_watch() -> None:
    comp, _ = compose(fuel_ports(B2.Fake(), windows=[window()], findings=[finding()]))
    thread = {"id": "tf", "occurrence_no": 1, "occurrences": 1, "segment_no": 1, "state": "ACTION_IN_HAND",
              "applied": True, "verified": False}
    rows = {r["category"]: r for r in assemble(with_threads(comp.facts, {"findings": {"fuel1": thread}}))}
    assert outcome(rows[PROTECT], "MG-8")["state"] == "WATCH"


# ---- the "Fuel in the tank" contributor ------------------------------------------------------------------------------

UNKNOWN = {"label": "Unknown", "tone": "gray"}
CASES = [
    ([], "Not available yet · no fuel check for the night of 19 Oct", None),
    ([window("NOT_ASSESSED", reason="MISSING_OPENING")],
     "Not available yet · the night of 19 Oct could not be analysed: no tank reading at 6 pm", UNKNOWN),
    ([window("NOT_ASSESSED", reason="NO_LOAD_RATE_MISSING")],
     "Not available yet · the night of 19 Oct could not be analysed: no generator idle fuel rate declared", UNKNOWN),
    ([window("WITHIN_MARGIN")], "Accounted for within the margin on the night of 19 Oct",
     {"label": "High", "tone": "green"}),
    ([window("BELOW_MATERIALITY", low="12.04", high="30.46")],
     "About 12.0–30.5 L unexplained on the night of 19 Oct, below the 40 L the check flags", UNKNOWN),
    ([window()], "About 61.2–98.4 L unexplained on the night of 19 Oct", {"label": "Limited", "tone": "amber"}),
    ([window("EXCESS")], "More fuel in the tank than recorded on the night of 19 Oct; a delivery may be unrecorded",
     UNKNOWN),
]


@pytest.mark.parametrize("windows,text,chip", CASES)
def test_fuel_stock_contributor_cases_follow_backup_readiness(windows, text, chip) -> None:
    _, rows = compose(fuel_ports(B2.Fake(), windows=windows))
    keys = [c["key"] for c in rows[PROTECT]["contributors"]]
    assert keys[keys.index("backup_readiness") + 1] == "fuel_stock"
    c = B2.contributor(rows[PROTECT], "fuel_stock")
    assert (c["label"], c["text"], c["confidence"]) == ("Fuel in the tank", text, chip)
    assert "fuel" in c["href"]  # `refs.evidence_ref(c, "fuel")`
    for cat in (GROW, COST, ASSURE):
        assert all(x["key"] != "fuel_stock" for x in rows[cat]["contributors"])


def test_failed_window_read_reads_not_loaded() -> None:
    comp, rows = compose(fuel_ports(B2.Fake(), refuse=("fuel_windows",)))
    assert "fuel_windows" in comp.failed
    assert B2.contributor(rows[PROTECT], "fuel_stock")["text"] == mini.NOT_LOADED


# ---- the dispatch-only paths ---------------------------------------------------------------------------------------

def test_cost_lead_and_trial_option_ignore_the_fuel_finding() -> None:
    """Must fail if `lead` is chosen from all Findings: with no dispatch head, the fuel Finding would lead."""
    _, base = compose(fuel_ports(B2.Fake(chain_findings=()), windows=[window()]))
    _, with_fuel = compose(fuel_ports(B2.Fake(chain_findings=()), windows=[window()], findings=[finding()]))
    assert with_fuel[COST] == base[COST]
    assert all(o["text"] != mini.OPTION_TRIAL for o in with_fuel[COST]["options"])
    _, dispatch = compose(fuel_ports(B2.Fake(), windows=[window()], findings=[finding()]))
    assert dispatch[COST] == B2.run()[1][COST]


def test_fuel_thread_line_shows_on_protect_only() -> None:
    comp, _ = compose(fuel_ports(B2.Fake(), windows=[window()], findings=[finding()]))
    facts = replace(comp.facts, day=DAY)
    thread = {"id": "tf", "occurrence_no": 1, "occurrences": 1, "segment_no": 1, "state": "CHANGE_APPLIED",
              "applied": True, "verified": False}
    view = {"change_day": DAY + timedelta(days=2), "events": ()}
    rows = {r["category"]: r for r in assemble(with_threads(facts, {"findings": {"fuel1": thread},
                                                                     "lifecycle": {"fuel1": view}}))}
    assert [t["text"] for t in rows[PROTECT]["thread_lines"]][-1].startswith("Before the change on 22 Oct")
    for cat in (GROW, COST, ASSURE):
        assert all(t["thread_id"] != "tf" for t in rows[cat]["thread_lines"])


def _verified(view_extra):
    f = FindingFact("fuel1", "fuel1r", "Unexplained fuel overnight", "UNEXPLAINED_FUEL", "SUPPORTED", None,
                    thread={"id": "tf", "segment_no": 1, "state": "RESOLVED_MONITORING", "verified": True},
                    lifecycle_view={"change_day": DAY - timedelta(days=3), "close_after": 7, "checked_days": 2,
                                    **view_extra})
    a = ActionFact("a1", "ACT-000009", "Check the tank", "fuel1", "fuel1r", True, True, "VERIFIED", None,
                   thread_id="tf", segment_no=1)
    return thread_line_item(f, SiteFacts(domain="MINI", site_code=C, findings=(f,), actions=(a,), day=DAY))


def test_no_close_countdown_without_a_clean_day_measure() -> None:
    """R3j2 §9j2.4: must fail if the `close_measured` guard is removed (the same fact without it counts down)."""
    assert _verified({"close_measured": False}) is None
    assert _verified({})["kind"] == "MONITORING"


def test_all_three_fuel_reads_share_one_cutoff_when_no_known_at() -> None:
    """R3j3 L1: with `known_at=None` the applicability, window and Finding reads receive `night_context`'s instant.
    Must fail if `fuel_findings` reverts to the raw `known_at` (None)."""
    from datetime import datetime, timezone
    from uuid import uuid4

    from assetops_backend.site_outcomes.read import BoardServices, SiteOutcomeBoardService, SiteRef

    instant = datetime(2026, 10, 21, 5, 30, tzinfo=timezone.utc)
    seen: dict[str, object] = {}

    class Store:
        def night_context(self, t, s):
            return "Africa/Addis_Ababa", str(uuid4()), instant

        def has_windows(self, t, s, k):
            seen["has_windows"] = k
            return True

        def windows(self, t, s, tank, lo, hi, k):
            seen["windows"] = k
            return ()

        def fuel_findings(self, t, s, lo, hi, k):
            seen["fuel_findings"] = k
            return ()

    t, s = uuid4(), uuid4()
    ports = SiteOutcomeBoardService(BoardServices(fuel_balance=Store())).mini_ports(
        SiteRef(t, s, C, "Kobo", "MINIGRID", B2.ZONE), None)
    ports.fuel_has_windows()
    ports.fuel_windows(NIGHT, NIGHT)
    ports.fuel_findings(T(19, 15), T(20, 9))
    assert seen == {"has_windows": instant, "windows": instant, "fuel_findings": instant}


def test_fuel_finding_without_a_policy_never_counts_down() -> None:
    """R3j3 L2: an unknown lifecycle policy (`None`) marks the view `close_measured: False`. Must fail on the old
    `policy is not None and ...` form."""
    (fact,) = mini._fuel_findings([finding()], C, T(19, 15), T(20, 9), T(19, 15), None)
    assert fact.lifecycle_view == {"close_measured": False}


def test_composer_marks_the_fuel_view_and_with_threads_keeps_it() -> None:
    policy = load_thread_lifecycle()
    ff = mini._fuel_findings([finding()], C, B2.LO, B2.HI, B2.LO - timedelta(days=30), policy)
    assert ff[0].lifecycle_view == {"close_measured": False}
    facts = with_threads(SiteFacts(domain="MINI", site_code=C, findings=ff),
                         {"findings": {"fuel1": {"id": "tf"}}, "lifecycle": {"fuel1": {"change_day": None}}})
    assert facts.findings[0].lifecycle_view == {"change_day": None, "close_measured": False}
    dispatch = with_threads(SiteFacts(domain="MINI", site_code=C, findings=(replace(ff[0], lifecycle_view=None),)),
                            {"lifecycle": {"fuel1": {"change_day": None}}})
    assert dispatch.findings[0].lifecycle_view == {"change_day": None}


# ---- the node and the Portfolio Protect card ------------------------------------------------------------------------

def test_node_lists_supported_findings_by_night_priced_and_unpriced() -> None:
    older = finding("fuel0", w=window(night=NIGHT - timedelta(days=2), low="40.06", high="55.04"), consequence=None)
    gone = finding("fuel9", lifecycle="NO_LONGER_SUPPORTED", w=window(night=NIGHT - timedelta(days=1)))
    _, rows = compose(fuel_ports(B2.Fake(), windows=[window()], findings=[finding(), gone, older]))
    entries = rows[PROTECT]["nodes"]["unexplained_fuel"]
    assert [e["key"] for e in entries] == ["fuel0", "fuel1"]
    assert entries[1] == {
        "key": "fuel1", "night_date": "2026-10-19", "basis": "UNEXPLAINED_FUEL_AT_DECLARED_PRICE",
        "litres_low": "61.2", "litres_high": "98.4", "amount_low": "76.55", "amount_high": "122.95",
        "currency": "USD",
        "text": "Unexplained fuel on the night of 19 Oct: about 61.2–98.4 L, 76.55–122.95 USD at your declared price "
                "(a modelled range, shown on its own)"}
    assert entries[0]["text"] == "Unexplained fuel on the night of 17 Oct: about 40.1–55.0 L (no money estimate)"
    assert entries[0]["amount_low"] is None and entries[0]["currency"] is None
    for cat in (GROW, COST, ASSURE):
        assert "unexplained_fuel" not in (rows[cat]["nodes"] or {})


def test_node_excludes_a_window_ending_after_the_board() -> None:
    late = finding("late", w=window(night=DAY))  # ends 21 Oct 09:00 UTC, after the board's end
    _, rows = compose(fuel_ports(B2.Fake(), windows=[window()], findings=[late]))
    assert "unexplained_fuel" not in (rows[PROTECT]["nodes"] or {})


def _site(code, name, protect_nodes, assure_nodes=None, cost_claim=None):
    rows = [{"category": "PROTECT_ASSET", "state": "WATCH", "state_label": "Watch", "short_value": None,
             "nodes": protect_nodes},
            {"category": "ASSURE_PERFORMANCE", "state": "ON_TRACK", "state_label": "On track", "short_value": None,
             "nodes": assure_nodes}]
    return {"site_code": code, "site_name": name, "earnings": None, "rows": rows}


def _fuel_entry(key, amount_low, amount_high, text):
    return {"key": key, "night_date": "2026-10-19", "basis": "UNEXPLAINED_FUEL_AT_DECLARED_PRICE",
            "litres_low": "61.2", "litres_high": "98.4", "amount_low": amount_low, "amount_high": amount_high,
            "currency": "USD", "text": text}


def _cards(sites):
    return portfolio_cards(sites, None, v.estate_income([]), [], None, 0)


def test_protect_card_lists_each_line_and_the_clause_and_changes_nothing_else() -> None:
    a = _fuel_entry("f1", "76.55", "122.95", "night 19")
    b = _fuel_entry("f2", "10.00", "20.00", "night 17")
    value = {"verified_values": [{"key": "m", "action_code": "ACT-2", "basis": "B", "amount": "17.00",
                                  "currency": "USD", "text": "ACT-2: mill"}]}
    sites = [_site("KIS-001", "Kisiwa", {"unexplained_fuel": [a, b]}, value), _site("KOBO-001", "Kobo", None)]
    cards = _cards(sites)
    plain = _cards([_site("KIS-001", "Kisiwa", None, value), _site("KOBO-001", "Kobo", None)])
    assert cards[PROTECT]["fuel_lines"] == ["Kisiwa · night 19", "Kisiwa · night 17"]
    assert cards[PROTECT]["fuel_note"] == "Unexplained fuel is shown on its own and never added to any other money"
    assert {k: x for k, x in cards[PROTECT].items() if k not in ("fuel_lines", "fuel_note")} == {
        k: x for k, x in plain[PROTECT].items() if k not in ("fuel_lines", "fuel_note")}
    assert plain[PROTECT]["fuel_lines"] == [] and plain[PROTECT]["fuel_note"] is None
    for cat in (GROW, COST, ASSURE):
        assert cards[cat] == plain[cat]
    text = json.dumps(cards)
    for s in ("86.55", "142.95", "93.55", "139.95"):  # fuel+fuel and fuel+verified-value sums
        assert s not in text


# ---- SITES_DISRUPTED -------------------------------------------------------------------------------------------------

def _thread(mechanism):
    return {"id": "t", "state": "OPEN", "mechanism": mechanism,
            "categories": {"items": [{"category": "PROTECT_ASSET", "role": "MOVES"}]}}


def test_fuel_thread_is_not_a_service_disruption() -> None:
    """Must fail if the NOT_DISRUPTION_MECHANISMS predicate is removed."""
    assert claims.disrupting([_thread("UNEXPLAINED_FUEL")]) == []
    assert claims.disrupting([_thread("COLD_EXCURSION")]) == [_thread("COLD_EXCURSION")]


# ---- the empty clean-day declaration (R3j2 §9j2.3) ------------------------------------------------------------------

def _payload(measures):
    return {"schema": "thread-lifecycle", "version": 1, "policy_version": "thread-lifecycle/1", "close_after_clean_complete_days": {"default": 7},
            "inconclusive_expiry_days": 7, "clean_day_measures": measures}


def test_parse_accepts_an_empty_list_and_still_refuses_bad_lists() -> None:
    assert parse_thread_lifecycle(_payload({"X": []})).measures_for("X") == ()
    for bad in ({"X": "a"}, {"X": [""]}, {}):
        with pytest.raises(ChainConfigError):
            parse_thread_lifecycle(_payload(bad))


def test_unexplained_fuel_is_declared_with_no_clean_day_measure() -> None:
    policy = load_thread_lifecycle()
    assert "UNEXPLAINED_FUEL" in policy.clean_day_measures
    assert policy.measures_for("UNEXPLAINED_FUEL") == ()


def test_the_app_start_graph_check_passes() -> None:
    lines = check_declared_chain_graph()
    assert lines[0].startswith("chain graph OK: 7 measures, 6 lifecycle mechanisms, 16 outcome-map entries")
