"""CH-6b2 L0 (build sheet CH-6 §B2/§B3, CH6b2-R): the Portfolio card claims, `count.sites_disrupted`, the Protect
"Why?" lines, the Portfolio-body `card_notes`, the board's Grow headline and the copy preferences. Pure."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from assetops_backend.chain import claims as CL
from assetops_backend.chain import vocabulary as v
from assetops_backend.chain import why
from assetops_backend.estate.portfolio import card_notes
from assetops_backend.outcomes.credit import MONEY_NOT_CREDITED
from assetops_backend.site_outcomes.board import grow_headline
from assetops_backend.site_outcomes.read import portfolio_cards

LO, HI = datetime(2026, 10, 25, tzinfo=timezone.utc), datetime(2026, 11, 1, tzinfo=timezone.utc)
FULL = {"complete": 7, "partial": 0, "low": 0, "no_data": 0, "pending": 0, "expected": 7}
PART = {"complete": 5, "partial": 1, "low": 0, "no_data": 1, "pending": 0, "expected": 7}


class _Site:
    def __init__(self, code: str, name: str) -> None:
        self.site_code, self.site_name, self.domain, self.timezone = code, name, "cold_chain", "Etc/UTC"
        self.site_id = code


def _thread(tid: str, state: str, category: str | None) -> dict:
    items = [] if category is None else [{"category": category, "role": "MOVES"},
                                         {"category": "ASSURE_PERFORMANCE", "role": "CHECKED"}]
    return {"id": tid, "state": state, "state_label": v.THREAD_STATE_WORDS.get(state),
            "categories": {"items": items}, "occurrences": [{"finding_id": f"f-{tid}", "day": "2026-10-28"}]}


THREADS = {
    "A": [_thread("a1", "OPEN", "PROTECT_ASSET"), _thread("a2", "RECURRED", "PROTECT_ASSET")],   # one Site, once
    "B": [_thread("b1", "CHANGE_APPLIED", "PROTECT_ASSET"), _thread("b2", "OPEN", "OPTIMIZE_COST"),
          _thread("b3", "OPEN", None)],                                                          # none counts
    "C": [_thread("c1", "ACTION_IN_HAND", "PROTECT_ASSET"), _thread("c2", "CLOSED", "PROTECT_ASSET")],
}
SITES = [_Site("A", "GreenHarvest"), _Site("B", "Kobo"), _Site("C", "Depot")]


def _counts(monkeypatch, days=FULL, threads=THREADS, fail: str | None = None) -> CL.EstateCounts:
    def counted(req, site, lo, hi):
        if site.site_code == fail:
            raise LookupError("thread read failed")
        return threads[site.site_code]

    monkeypatch.setattr(CL, "claim_days", lambda req, site, lo, hi: days)
    monkeypatch.setattr(CL, "counted_threads", counted)
    # MB-1-R §2.2: these Sites have no opportunity-origin domain Action (the threads dict gains `verified_actions` 0).
    monkeypatch.setattr(CL, "verified_actions", lambda req, site, lo, hi, counted: [])
    return CL.estate_count_claims(object(), SITES, LO, HI, [], (LookupError,))


def test_sites_disrupted_counts_sites_with_a_primary_protect_thread_open_recurred_or_in_hand(monkeypatch) -> None:
    out = _counts(monkeypatch)
    c = out.claims[CL.SITES_DISRUPTED]
    assert (c.value, c.basis, c.text) == (2, "COMPLETE", "2 sites disrupted")
    assert [t["id"] for t in out.disrupted["A"]] == ["a1", "a2"] and out.disrupted["B"] == []
    assert [t["id"] for t in out.disrupted["C"]] == ["c1"]
    assert CL.SITES_DISRUPTED in out.claims_json()   # additive on `/estate/chain` `counts` and `summary.claims`


def test_sites_disrupted_basis_forms(monkeypatch) -> None:
    none = {k: [] for k in THREADS}
    assert _counts(monkeypatch, threads=none).claims[CL.SITES_DISRUPTED].text == "No sites disrupted"
    one = {**none, "C": THREADS["C"]}
    assert _counts(monkeypatch, threads=one).claims[CL.SITES_DISRUPTED].text == "1 site disrupted"
    # MD-CH6-4: the CHECKED_DAYS forms
    assert _counts(monkeypatch, PART).claims[CL.SITES_DISRUPTED].text == "2 found on days with complete readings"
    assert _counts(monkeypatch, PART, none).claims[CL.SITES_DISRUPTED].text == "None found on days with complete readings"
    failed = _counts(monkeypatch, fail="B")
    assert (failed.claims[CL.SITES_DISRUPTED].basis, failed.claims[CL.SITES_DISRUPTED].text) == ("NOT_KNOWN",
                                                                                                "Not known yet")
    assert failed.disrupted["B"] is None


def test_early_warnings_and_event_only_threads_never_count() -> None:
    """CH6b2-R Q2(a): only a thread with a Finding occurrence in the window is counted; an early warning is not a
    thread at all, and an event-only (no Finding) thread never enters."""
    rows = {"occurrences": [
        {"thread_id": "t-finding", "finding_id": "f1", "episode_start": LO, "episode_end": None},
        {"thread_id": "t-event", "finding_id": None, "episode_start": LO, "episode_end": None},
        {"thread_id": "t-before", "finding_id": "f2", "episode_start": datetime(2026, 10, 1, tzinfo=timezone.utc),
         "episode_end": datetime(2026, 10, 2, tzinfo=timezone.utc)}]}
    assert CL._finding_threads(rows, LO, HI) == {"t-finding"}


def test_count_card_value_splits_the_claim_text() -> None:
    claim = lambda value, basis, text: {"value": value, "basis": basis, "text": text}   # noqa: E731
    assert v.count_card_value(claim(2, "COMPLETE", "2 sites disrupted")) == {"text": "2", "small": "sites disrupted"}
    assert v.count_card_value(claim(0, "COMPLETE", "No sites disrupted")) == {"text": "No sites disrupted",
                                                                               "small": None}
    assert v.count_card_value(claim(0, "CHECKED_DAYS", "None found on days with complete readings")) == {
        "text": "None found", "small": "on days with complete readings"}
    assert v.count_card_value(claim(None, "NOT_KNOWN", "Not known yet")) == {"text": "Not known yet", "small": None}
    assert v.count_card_value(claim(0, "COMPLETE", "0 fixes confirmed"), "No verified result yet")["text"] \
        == "No verified result yet"


def _income(amount: str | None, days=FULL, basis="COMPLETE", cur="USD") -> dict:
    value = None if amount is None else {"amount": amount, "currency": cur}
    return {"key": "money.estimated_income", "value": value, "basis": basis, "days": days, "text": "x"}


def _site(code: str, name: str, earnings=None, nodes=None, short=None) -> dict:
    return {"site_code": code, "site_name": name, "earnings": earnings,
            "rows": [{"category": "GROW_REVENUE", "state": "OPPORTUNITY", "state_label": "Opportunity",
                      "short_value": short, "nodes": nodes}]}


def _cards(sites, counted=None, categories=(), objective_sites=None, unread=0):
    total = v.estate_income([(s["site_name"], s["earnings"]["estimated_income"]) for s in sites
                             if (s.get("earnings") or {}).get("estimated_income")])
    return portfolio_cards(sites, counted, total, list(categories), objective_sites, unread)


def test_grow_value_follows_money_total_form() -> None:
    complete = _cards([_site("K", "Kobo", {"estimated_income": _income("7.50")})])["GROW_REVENUE"]
    assert complete["value"] == {"text": "7.50 USD", "small": "estimated"} and complete["tone"] == "green"
    assert complete["parts"]["income"] == "Kobo: 7.50 USD over 7 of 7 days with complete readings"
    assert complete["parts"]["income_note"] == "Estimated income from days with complete readings: 7.50 USD · not billed or collected"
    assert complete["days_line"] == "Kobo: Complete readings on 7 of 7 days"
    assert complete["basis_text"] == "Declared price × measured kWh · not billed or collected"
    # CH6b2-R Q4: "At least" whenever the claim says so, including a named NOT_KNOWN Site (not only CHECKED_DAYS)
    named = _cards([_site("K", "Kobo", {"estimated_income": _income("7.50")}),
                    _site("D", "Depot", {"estimated_income": _income(None, None, "NOT_KNOWN")})])["GROW_REVENUE"]
    assert named["value"] == {"text": "At least 7.50 USD", "small": "estimated"}
    assert named["parts"]["income"] == "Kobo: 7.50 USD over 7 of 7 days with complete readings · Depot: not known yet"
    mixed = _cards([_site("K", "Kobo", {"estimated_income": _income("7.50")}),
                    _site("D", "Depot", {"estimated_income": _income("1.00", cur="EUR")})])["GROW_REVENUE"]
    assert mixed["value"] == {"text": "Not shown · amounts in more than one currency", "small": None}


def test_grow_without_income_keeps_the_gap_and_shows_the_potential_on_its_part() -> None:
    """CH6b2-R2 L3: the "possible" short-value fallback was dead code (`short_values` is never filled) and is removed
    (Known Deviation, BL-22): a Site with a potential and no income reads "Not known yet", the potential on its part."""
    potential = {"kpi": {"value": None, "text": "No target set yet"},
                 "potential": {"text": "18–20 kW of daytime solar unused\n1–2 USD per hour of use, at the declared price"},
                 "earnings": None}
    card = _cards([_site("K", "Kobo", nodes=potential, short="18–20 kW unused")])["GROW_REVENUE"]
    assert card["value"] == {"text": "Not known yet", "small": None} and card["missing"] is True
    assert card["parts"] == {"target": "No target set yet at any site",
                             "potential": "Kobo: 18–20 kW of daytime solar unused",
                             "income": "Not known yet", "income_note": None}
    assert card["basis_text"] == "Opportunities · revenue not measured yet"
    empty = _cards([_site("K", "Kobo")])["GROW_REVENUE"]
    assert empty["missing"] is True and empty["value"]["text"] == "Not known yet" and empty["tone"] == "neutral"
    assert empty["parts"]["potential"] == "No potential found yet"


def test_grow_target_lists_each_site_with_a_target_md_ch6_6() -> None:
    nodes = {"kpi": {"value": "ON_PACE", "text": "120 kWh so far this month"}, "potential": None, "earnings": None}
    card = _cards([_site("K", "Kobo", nodes=nodes), _site("D", "Depot")])["GROW_REVENUE"]
    assert card["parts"]["target"] == "Kobo: 120 kWh so far this month"


def test_protect_and_assure_cards_carry_the_count_claims(monkeypatch) -> None:
    counted = _counts(monkeypatch)
    sites = [{"site_code": s.site_code, "site_name": s.site_name, "rows": [], "earnings": None} for s in SITES]
    cats = [{"category": "PROTECT_ASSET", "warning_count": 1}]
    cards = portfolio_cards(sites, counted, v.estate_income([]), cats, 2, 1)
    protect, assure = cards["PROTECT_ASSET"], cards["ASSURE_PERFORMANCE"]
    assert protect["claim"] == counted.claims[CL.SITES_DISRUPTED].to_json()
    assert protect["value"] == {"text": "2", "small": "sites disrupted"} and protect["tone"] == "red"
    assert protect["detail"] == ("Service disruptions recorded as findings · 1 early warning, counted separately · "
                                 "loss not priced")
    # PF-C2: the shared coverage line carries every Site's days; Protect and Assure no longer repeat it.
    assert protect["days_line"] is None and assure["days_line"] is None
    assert assure["value"] == {"text": "1", "small": "fix confirmed"}   # Depot c2 CLOSED
    assert assure["claim"] == counted.claims[CL.VERIFIED_RESULTS].to_json()
    assert assure["detail"] == "targets declared at 2 sites, for any outcome, 1 site not judged yet"
    unknown = portfolio_cards(sites, None, v.estate_income([]), [], None, 3)
    assert unknown["PROTECT_ASSET"]["value"] == {"text": "Not known yet", "small": None}
    assert unknown["PROTECT_ASSET"]["detail"] == "Service disruptions recorded as findings · loss not priced"
    assert unknown["ASSURE_PERFORMANCE"]["detail"] is None and unknown["PROTECT_ASSET"]["days_line"] is None
    # CH5d1-R 2.1: Optimize joins the one builder, second in the order (its card: `test_ch5d1_optimize_card.py`)
    assert list(cards) == ["GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET", "ASSURE_PERFORMANCE"]


def test_protect_why_names_each_counted_site_and_thread() -> None:
    row = {"issues": [{"kind": "FINDING", "role": "MOVES", "text": "Chamber above 4°C for 25–35 minutes",
                       "ref": {"finding_id": "f-a1"}}]}
    lines = why.disrupted_lines([("GreenHarvest", THREADS["A"], row), ("Kobo", [], {}),
                                 ("Depot", THREADS["C"][:1], {})])
    assert lines == ["GreenHarvest: Chamber above 4°C for 25–35 minutes",
                     "GreenHarvest: Seen again, since 28 Oct",
                     "Depot: Action agreed, since 28 Oct",
                     "Early warnings are counted separately and not priced"]
    text = why.estate_text("PROTECT_ASSET", [], lines)
    assert text["comes_from"] == lines   # never cut to MAX_FROM


def test_card_notes_are_one_server_line_each() -> None:
    summary = {"count_basis": "CHECKED_DAYS", "evidence_gap_site_count": 1,
               "checked_days": [{"site_name": "Kobo", "checked": 5, "requested": 7, "withheld": True}]}
    notes = card_notes(summary, 3)
    # CH6b3-R3 M1: "days checked" means graded COMPLETE (the card's days line); the coverage clause is gone.
    # PV-1-R §2: the money clause moved to the Assure card's `value_note`; the body note is the gap clause alone.
    assert notes == {"PROTECT_ASSET": None, "ASSURE_PERFORMANCE": "evidence gap at 1 site"}
    assert all("days checked" not in (t or "") for t in notes.values())
    assert all(MONEY_NOT_CREDITED not in (t or "") for t in notes.values())
    complete = {"count_basis": "COMPLETE", "evidence_gap_site_count": 0, "checked_days": []}
    assert card_notes(complete, 3) == {"PROTECT_ASSET": None, "ASSURE_PERFORMANCE": "no evidence gaps"}


@pytest.mark.parametrize(("nodes", "expected"), [
    (None, None),
    ({"earnings": {"text": "7.50 USD over 3 of 3 days with complete readings", "basis": "COMPLETE"},
      "potential": {"text": "18–20 kW of daytime solar unused"}, "kpi": {"text": "No target set yet"}},
     "7.50 USD over 3 of 3 days with complete readings"),
    ({"earnings": {"text": "Not known yet", "basis": "NOT_KNOWN"},
      "potential": {"text": "18–20 kW of daytime solar unused\n1–2 USD per hour"}, "kpi": {"text": "No target"}},
     "18–20 kW of daytime solar unused"),
    ({"earnings": {"text": "Not known yet", "basis": "NOT_KNOWN"}, "potential": {"text": "No potential found yet"},
      "kpi": {"text": "No target set yet"}}, "No target set yet"),
])
def test_board_grow_headline_order(nodes, expected) -> None:
    assert grow_headline(nodes) == expected


def test_copy_preferences() -> None:
    one = {"complete": 1, "partial": 0, "low": 0, "no_data": 0, "pending": 0, "expected": 1}
    assert v.days_line(one) == "Complete readings on 1 of 1 day"                               # Q7a
    assert v.money_claim("estimated_income", {"amount": "2", "currency": "USD"}, one).text \
        == "2.00 USD over 1 of 1 day with complete readings · not billed or collected"
    assert v.days_line(FULL) == "Complete readings on 7 of 7 days"
    assert (v.headroom_unit(1), v.headroom_unit(6), v.headroom_unit(None)) == (   # Q7c
        "kW over 1 daylight hour", "kW over 6 daylight hours", "kW over daylight hours")


# ---- CH6b2-R2 M1: the moved card rules, goldens from the removed vitest cases ----------------------------------

@pytest.mark.parametrize(("gaps", "sites", "checked", "expected"), [
    (3, 3, False, "evidence gaps at all 3 sites"),
    (2, 4, False, "evidence gaps at 2 of 4 sites"),
    (1, 4, False, "evidence gap at 1 site"),
    (0, 4, False, "no evidence gaps"),
    (0, 4, True, "no evidence gaps on the days assessed"),
    (None, 4, False, "evidence gaps not assessed"),
    (6, 4, False, v.card_text("note.gap.many", gaps=6)),   # no vitest golden: the many branch, pinned to its template
])
def test_evidence_gap_text_branches(gaps, sites, checked, expected) -> None:
    assert v.evidence_gap_text(gaps, sites, checked) == expected
    if gaps == 6:
        assert "6" in expected


@pytest.mark.parametrize("checked", [False, True])
@pytest.mark.parametrize("gaps", [None, 0, 1, 2, 4, 6])
def test_evidence_gap_text_never_says_days_checked(gaps, checked) -> None:
    # CH6b3-R4 N1: "days checked" means graded COMPLETE; the gap clause follows coverage, so it says "assessed".
    assert "days checked" not in v.evidence_gap_text(gaps, 4, checked)


@pytest.mark.parametrize(("n", "unread", "expected"), [
    (3, 0, "targets declared at 3 sites, for any outcome"),
    (1, 0, "targets declared at 1 site, for any outcome"),
    (0, 0, "no targets declared"),                                  # only when every Site was read as None
    (2, 1, "targets declared at 2 sites, for any outcome, 1 site not judged yet"),
    (1, 2, "targets declared at 1 site, for any outcome, 2 sites not judged yet"),
    (0, 1, None),                                                   # n == 0 and unread > 0: no clause
    (None, 3, None),
])
def test_assure_target_branches(n, unread, expected) -> None:
    cards = portfolio_cards([], None, v.estate_income([]), [], n, unread)
    assert cards["ASSURE_PERFORMANCE"]["detail"] == expected


# ---- CH6b2-R2 H1: thread lifecycle is read at the request cutoff k for every domain -----------------------------

K = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
EVIDENCE = datetime(2026, 10, 31, 17, 5, tzinfo=timezone.utc)   # the cold/EV evidence cutoff (R7), before the Finding is known
KNOWN = datetime(2026, 11, 2, 9, tzinfo=timezone.utc)           # `cause_known_at` of the lifecycle events: after EVIDENCE


class _Req:
    """A request over one stored thread: the lifecycle events as `(state, cause_known_at)` after a Finding occurrence."""
    def __init__(self, domain: str, mechanism: str, events, k=K, effective=None) -> None:
        self.k = k
        eff = effective or datetime(2026, 10, 28).date()
        self.rows = {
            "occurrences": [{"thread_id": "t1", "finding_id": "f1", "opportunity_id": None, "mechanism": mechanism,
                             "episode_start": datetime(2026, 10, 28, 2, tzinfo=timezone.utc),
                             "episode_end": datetime(2026, 10, 28, 3, tzinfo=timezone.utc), "opportunity_no": None}],
            "events": [{"thread_id": "t1", "seq": n, "state": st, "cause_kind": "FINDING", "cause_id": "c",
                        "effective_day": (eff.get(st, datetime(2026, 10, 28).date()) if isinstance(eff, dict) else eff),
                        "recorded_at": at, "cause_known_at": at}
                       for n, (st, at) in enumerate(events, 1)],
            "actions": []}

    def threads(self, site_id):
        return self.rows

    def evidence_cutoff(self, site_id):
        return EVIDENCE


def _real_counts(monkeypatch, domain: str, mechanism: str, events, k=K, effective=None):
    site = _Site("A", "GreenHarvest")
    site.domain = domain
    req = _Req(domain, mechanism, events, k, effective)
    monkeypatch.setattr(CL, "claim_days", lambda r, s, lo, hi: FULL)
    return CL.estate_count_claims(req, [site], LO, HI, [], (LookupError,))


COLD = ("cold_chain", "COLD_START_FAILURE")
EV = ("ev_charging", "EV_INTERRUPTION")


@pytest.mark.parametrize(("domain", "mechanism"), [COLD, EV])
def test_open_known_after_evidence_cutoff_but_by_k_is_counted(monkeypatch, domain, mechanism) -> None:
    """H1 case 1 (cold) and its EV twin: OPEN's `cause_known_at` is after the evidence cutoff and no later than k."""
    out = _real_counts(monkeypatch, domain, mechanism, [("OPEN", KNOWN)])
    assert out.claims[CL.SITES_DISRUPTED].value == 1
    assert out.claims[CL.OPEN_THREADS].value == 1
    assert [t["id"] for t in out.disrupted["A"]] == ["t1"]


@pytest.mark.parametrize(("domain", "mechanism"), [COLD, EV])
def test_open_known_after_k_is_not_counted(monkeypatch, domain, mechanism) -> None:
    """H1 case 2: the as-known bound still holds."""
    out = _real_counts(monkeypatch, domain, mechanism, [("OPEN", datetime(2026, 11, 3, tzinfo=timezone.utc))])
    assert out.claims[CL.SITES_DISRUPTED].value == 0 and out.claims[CL.OPEN_THREADS].value == 0


def test_ev_action_in_hand_known_after_evidence_cutoff_is_counted(monkeypatch) -> None:
    """H1 case 3: an EV thread at ACTION_IN_HAND disrupts (in hand, not open)."""
    out = _real_counts(monkeypatch, *EV, [("OPEN", KNOWN), ("ACTION_IN_HAND", KNOWN)])
    assert out.claims[CL.SITES_DISRUPTED].value == 1
    assert out.claims[CL.OPEN_THREADS].value == 1   # open + in hand
    assert out.claims[CL.VERIFIED_RESULTS].value == 0


def test_only_a_verified_event_reaches_verified_results(monkeypatch) -> None:
    """H1 case 4: CHANGE_APPLIED later than the evidence cutoff is visible but not verified; RESOLVED_MONITORING is."""
    applied = _real_counts(monkeypatch, *COLD, [("OPEN", KNOWN), ("ACTION_IN_HAND", KNOWN), ("CHANGE_APPLIED", KNOWN)])
    assert applied.claims[CL.VERIFIED_RESULTS].value == 0 and applied.claims[CL.SITES_DISRUPTED].value == 0
    done = _real_counts(monkeypatch, *COLD, [("OPEN", KNOWN), ("ACTION_IN_HAND", KNOWN), ("CHANGE_APPLIED", KNOWN),
                                             ("RESOLVED_MONITORING", KNOWN)])
    assert done.claims[CL.VERIFIED_RESULTS].value == 1


LATER = datetime(2026, 11, 1).date()                 # after the window's last day (31 Oct)
_LIFE = [("OPEN", KNOWN), ("ACTION_IN_HAND", KNOWN), ("CHANGE_APPLIED", KNOWN), ("RESOLVED_MONITORING", KNOWN)]
_AFTER = {"CHANGE_APPLIED": LATER, "RESOLVED_MONITORING": LATER}


@pytest.mark.parametrize(("domain", "mechanism"), [COLD, EV])
def test_h1_a_fix_verified_after_the_window_counts_for_the_problem_found_in_it(monkeypatch, domain, mechanism) -> None:
    """CH6b3-R3 (a): VERIFIED effective after the window's last day and known by k -> verified, not open."""
    out = _real_counts(monkeypatch, domain, mechanism, _LIFE, effective=_AFTER)
    assert out.claims[CL.VERIFIED_RESULTS].value == 1 and out.claims[CL.OPEN_THREADS].value == 0
    assert out.claims[CL.SITES_DISRUPTED].value == 0


def test_h1_b_the_same_event_known_after_k_leaves_the_thread_in_hand(monkeypatch) -> None:
    """CH6b3-R3 (b): known after k, the verification is not visible: the thread is still ACTION_IN_HAND."""
    late = datetime(2026, 11, 3, tzinfo=timezone.utc)
    life = [("OPEN", KNOWN), ("ACTION_IN_HAND", KNOWN), ("CHANGE_APPLIED", late), ("RESOLVED_MONITORING", late)]
    out = _real_counts(monkeypatch, *COLD, life, effective=_AFTER)
    assert out.claims[CL.VERIFIED_RESULTS].value == 0 and out.claims[CL.OPEN_THREADS].value == 1


def test_h1_c_a_thread_without_a_finding_occurrence_in_the_window_is_not_counted(monkeypatch) -> None:
    """CH6b3-R3 (c): the window still selects WHICH problems count (no Finding occurrence -> not counted)."""
    site = _Site("A", "GreenHarvest")
    req = _Req(*COLD, _LIFE, K, _AFTER)
    req.rows["occurrences"][0]["finding_id"] = None
    monkeypatch.setattr(CL, "claim_days", lambda r, s, lo, hi: FULL)
    out = CL.estate_count_claims(req, [site], LO, HI, [], (LookupError,))
    assert out.claims[CL.VERIFIED_RESULTS].value == 0 and out.claims[CL.OPEN_THREADS].value == 0
    other = (datetime(2026, 11, 8, tzinfo=timezone.utc), datetime(2026, 11, 15, tzinfo=timezone.utc))
    out = _real_counts(monkeypatch, *COLD, _LIFE, effective=_AFTER)
    assert out.claims[CL.VERIFIED_RESULTS].value == 1                       # the control: with the occurrence it counts
    site2 = _Site("A", "GreenHarvest")
    out = CL.estate_count_claims(_Req(*COLD, _LIFE, K, _AFTER), [site2], *other, [], (LookupError,))
    assert out.claims[CL.VERIFIED_RESULTS].value == 0                       # an episode outside the window


def test_h1_d_a_later_recurrence_counts_as_open(monkeypatch) -> None:
    """CH6b3-R3 (d): a RECURRED event after the verification, known by k, reads the thread open."""
    life = _LIFE + [("RECURRED", KNOWN)]
    out = _real_counts(monkeypatch, *COLD, life, effective={**_AFTER, "RECURRED": LATER})
    assert out.claims[CL.VERIFIED_RESULTS].value == 0 and out.claims[CL.OPEN_THREADS].value == 1
    assert out.claims[CL.SITES_DISRUPTED].value == 1


@pytest.mark.parametrize(("domain", "mechanism", "site_ref"), [(*COLD, "COLD"), (*EV, "EV")])
def test_site_chain_thread_state_equals_the_claims_state(domain, mechanism, site_ref) -> None:
    """H1 case 5 (behavioural, L-R2-1): the served Site chain's thread state equals the claims' thread state for the
    same lifecycle (OPEN, ACTION_IN_HAND known after the evidence cutoff but by k), for cold and EV. CH6b3-R3: this
    holds only when no event is effective after the window's last day (the claim reads the latest known state, the
    chain reads `window_day`); the lifecycle here is effective inside the window."""
    import test_ch5a1_board_contract as BC
    import test_ch5a2_contract as C
    ref = getattr(BC, site_ref)
    tid = C.THREAD_IDS[ref.site_id]
    *_, lo, hi = C.LIFE[ref.site_id]
    r = C.client(C.LifecyclePort()).get(f"/api/sites/{ref.site_code}/chain", params={
        "from": lo.isoformat().replace("+00:00", "Z"), "to": hi.isoformat().replace("+00:00", "Z"),
        "known_at": "2026-11-03T12:00:00Z"})
    assert r.status_code == 200, r.text
    served = [t["state"] for t in r.json()["threads"] if t["id"] == tid]
    req = _Req(domain, mechanism, [("OPEN", KNOWN), ("ACTION_IN_HAND", KNOWN)])
    site = _Site("A", "GreenHarvest")
    site.domain = domain
    assert served == CL.site_thread_states(req, site, LO, HI) == ["ACTION_IN_HAND"]


def test_lifecycle_cutoff_is_the_request_cutoff_for_every_domain() -> None:
    from assetops_backend.chain.read import lifecycle_cutoff, site_cutoff
    k, ev = datetime(2026, 11, 2, tzinfo=timezone.utc), datetime(2026, 10, 31, 17, 5, tzinfo=timezone.utc)
    assert lifecycle_cutoff(k) == k and lifecycle_cutoff(None) is None
    assert site_cutoff("cold_chain", k, ev, k) == ev    # evidence reads stay on R7
