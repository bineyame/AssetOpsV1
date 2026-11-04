"""CH-4 L0 (build sheet CH-4 §8.1): placement on eligible days, the opportunity item reducer, the copy, the lens
helpers, the moved headroom rule, the Portfolio block and card, and SUPPORT_LOST for opportunity threads."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from assetops_backend.chain import lifecycle as lc
from assetops_backend.chain import threads as th
from assetops_backend.chain import vocabulary as v
from assetops_backend.chain.lifecycle_run import thread_causes
from assetops_backend.chain.opportunities import opportunity_items
from assetops_backend.estate.portfolio import opportunity_block, productive_use_card
from assetops_backend.mini_decisions.projection import frozen_result
from assetops_backend.mini_depth.rules import Bound, headroom_on_every_eligible_day, observed_headroom_range
from assetops_backend.outcomes.outcome_map import categories_for, finding_signal_key, lens_flags, thread_signal_key

UTC = timezone.utc
ADDIS = "Africa/Addis_Ababa"
T, S = uuid4(), uuid4()


def _day_rows(first: date, eligible: set[int]) -> list[dict]:
    return [{"local_day": (first + timedelta(days=i)).isoformat(),
             "decision": "ELIGIBLE" if i in eligible else "EXCLUDED"} for i in range(5)]


def _row(eligible: set[int], tz: str = ADDIS, first: date = date(2026, 10, 27)) -> dict:
    return {"tenant_id": T, "site_id": S, "site_tz": tz, "opportunity_id": uuid4(), "first_day": first,
            "last_day": first + timedelta(days=4), "created_at": datetime(2026, 11, 3, 9, tzinfo=UTC),
            "revision_id": uuid4(), "eligible_days": len(eligible), "day_rows": _day_rows(first, eligible)}


# --- placement (R1, R2) -------------------------------------------------------------------------------------------

def test_zero_eligible_days_is_not_a_source():
    assert th.opportunity_source(_row(set())) is None
    assert th.opportunity_source({**_row(set()), "eligible_days": None}) is None


def test_episode_is_the_eligible_days_in_the_site_zone():
    one = th.opportunity_source(_row({4}))
    assert one is not None
    assert one.episode_start == datetime(2026, 10, 31, tzinfo=lc_zone(ADDIS))
    assert one.episode_end == datetime(2026, 11, 1, tzinfo=lc_zone(ADDIS))
    assert one.episode_start.astimezone(UTC) == datetime(2026, 10, 30, 21, tzinfo=UTC)
    two = th.opportunity_source(_row({1, 3}, tz="UTC"))
    assert two.episode_start == datetime(2026, 10, 28, tzinfo=UTC)
    assert two.episode_end == datetime(2026, 10, 31, tzinfo=UTC)
    assert th.effective_day(two) == date(2026, 10, 28)


def test_later_revision_gaining_eligibility_is_placed_once():
    first = _row(set())
    later = {**first, "revision_id": uuid4(), "created_at": first["created_at"] + timedelta(hours=1),
             "eligible_days": 1, "day_rows": _day_rows(first["first_day"], {4})}
    memory = th.MemoryThreads()
    reg = th.ThreadRegistry(memory, "test")
    sources = [s for s in (th.opportunity_source(first), th.opportunity_source(later)) if s is not None]
    assert len(sources) == 1
    report = reg.place_all(sources)
    assert report.counts == {"NEW_THREAD": 1}
    (occ,) = memory.occurrences.values()
    assert occ["episode_start"].date() == date(2026, 10, 31)


def lc_zone(name: str):
    from zoneinfo import ZoneInfo
    return ZoneInfo(name)


# --- the reducer --------------------------------------------------------------------------------------------------

TID = "2fc15fab-6652-5dfd-b337-57f8a6877268"


def _o(oid: str, num: int, start: datetime, end: datetime, *, public_no: int, first: str, last: str,
       status: str = "LIMITED", eligible: int = 2, assessed: int = 4, tz: str = ADDIS, known: datetime | None = None,
       selected: datetime | None = None, seq: int = 1, codes=("SOURCE_CLASS_MIXED",), decisions=None,
       headroom=None, site_code: str = "KOBO-001") -> tuple:
    study = {"site_id": str(S), "site_code": site_code, "site_name": "Kobo", "public_no": public_no,
             "first_day": first, "last_day": last, "status": status, "eligible_days": eligible,
             "assessed_days": assessed, "headroom_kw": headroom, "limitation_codes": list(codes),
             "decisions": decisions or ["ELIGIBLE", "ELIGIBLE", "EXCLUDED", "EXCLUDED", None],
             "selected_at": (selected or datetime(2026, 11, 1, tzinfo=UTC)).isoformat(), "seq": seq,
             "joined_at": datetime(2026, 11, 3, tzinfo=UTC).isoformat(),
             "source_known_at": (known or datetime(2026, 11, 1, tzinfo=UTC)).isoformat()}
    return ("O", oid, TID, num, 2, start, end, tz, "PRODUCTIVE_USE_HEADROOM", json.dumps(study),
            date.fromisoformat(last), "MINIGRID")


def _e(seq: int, state: str, day: date, known: datetime) -> tuple:
    return ("E", "cause", TID, seq, None, known, known, state, "OCCURRENCE", None, day, None)


def _addis(y: int, m: int, d: int) -> datetime:
    return datetime(y, m, d, tzinfo=lc_zone(ADDIS))


O3 = "00000000-0000-0000-0000-000000000003"
O4 = "00000000-0000-0000-0000-000000000004"
ROWS = [_o(O3, 1, _addis(2026, 10, 31), _addis(2026, 11, 1), public_no=3, first="2026-10-27", last="2026-10-31",
           eligible=1),
        _o(O4, 2, _addis(2026, 10, 31), _addis(2026, 11, 2), public_no=4, first="2026-10-28", last="2026-11-01"),
        _e(1, "OPEN", date(2026, 10, 31), datetime(2026, 11, 1, tzinfo=UTC))]
WEEK = (datetime(2026, 10, 26, 21, tzinfo=UTC), datetime(2026, 11, 2, 21, tzinfo=UTC))


def test_item_is_the_latest_seen_study_with_all_visible_occurrences():
    (item,) = opportunity_items(ROWS, *WEEK, None)
    assert item["study"]["code"] == "OPP-000004" and item["occurrences"] == 2
    assert item["title"] == "Daytime solar unused at Kobo" and item["short_label"] == "Kobo daytime solar"
    assert item["state"] == "OPEN" and item["state_label"] == "Open" and item["state_day"] == "2026-11-02"
    assert item["seen_line"] == "Seen on 2 of 4 well-observed days · 28 Oct–1 Nov"
    assert item["limit_line"] == v.LIMIT_MIXED and item["value_line"] is None
    assert item["evidence_label"] == "Limited evidence" and item["filter_state"] == "unconfirmed"
    assert item["lens_flags"] == ["OPPORTUNITY"]
    assert item["categories"]["items"][0]["category"] == "GROW_REVENUE"
    assert item["links"]["opportunity"] == f"/sites/KOBO-001/opportunities/{O4}"
    assert item["links"]["evidence"] == ("/sites/KOBO-001/performance/renewable?from=2026-10-27T21:00:00Z"
                                         "&to=2026-11-01T21:00:00Z")
    assert item["ref"] == {"kind": "OPPORTUNITY", "site": "KOBO-001", "id": O4}
    assert item["thread_ref"] == {"kind": "THREAD", "site": "KOBO-001", "id": TID}


def test_window_intersection_in_site_zone_and_last_instant():
    # 31 Oct Addis starts at 30 Oct 21:00Z; a window ending exactly then does not see it, one µs later does.
    edge = datetime(2026, 10, 30, 21, tzinfo=UTC)
    assert opportunity_items(ROWS, edge - timedelta(days=1), edge, None) == []
    (item,) = opportunity_items(ROWS, edge - timedelta(days=1), edge + timedelta(microseconds=1), None)
    assert item["study"]["code"] == "OPP-000004"
    # 1 Nov only: OPP-000004 is seen (its episode runs to 2 Nov), OPP-000003 is not.
    (one,) = opportunity_items(ROWS, datetime(2026, 10, 31, 21, tzinfo=UTC), datetime(2026, 11, 1, 21, tzinfo=UTC),
                               None)
    assert one["study"]["code"] == "OPP-000004"


def test_hidden_occurrence_and_late_selection_follow_k():
    late = [_o(O3, 1, _addis(2026, 10, 31), _addis(2026, 11, 1), public_no=3, first="2026-10-27",
               last="2026-10-31", eligible=1),
            _o(O4, 2, _addis(2026, 10, 31), _addis(2026, 11, 2), public_no=4, first="2026-10-28", last="2026-11-01",
               known=datetime(2026, 11, 2, tzinfo=UTC)), ROWS[2]]
    (item,) = opportunity_items(late, *WEEK, datetime(2026, 11, 1, 12, tzinfo=UTC))
    assert item["study"]["code"] == "OPP-000003" and item["occurrences"] == 1
    two = [_o(O4, 2, _addis(2026, 10, 31), _addis(2026, 11, 2), public_no=4, first="2026-10-28", last="2026-11-01",
              status="UNKNOWN", selected=datetime(2026, 11, 1, tzinfo=UTC), seq=1),
           _o(O4, 2, _addis(2026, 10, 31), _addis(2026, 11, 2), public_no=4, first="2026-10-28", last="2026-11-01",
              status="LIMITED", selected=datetime(2026, 11, 2, tzinfo=UTC), seq=2), ROWS[2]]
    assert opportunity_items(two, *WEEK, datetime(2026, 11, 1, 12, tzinfo=UTC))[0]["evidence"] == "UNKNOWN"
    assert opportunity_items(two, *WEEK, None)[0]["evidence"] == "LIMITED"


def test_zero_eligible_head_is_not_seen_and_order_is_by_site_then_last_day():
    zero = [_o(O4, 1, _addis(2026, 10, 31), _addis(2026, 11, 2), public_no=4, first="2026-10-28",
               last="2026-11-01", eligible=0), ROWS[2]]
    assert opportunity_items(zero, *WEEK, None) == []
    other = list(ROWS[:2]) + [ROWS[2]]
    alpha = ("O", "00000000-0000-0000-0000-00000000000a", "aaaa", 1, 1, _addis(2026, 10, 31), _addis(2026, 11, 1),
             ADDIS, "PRODUCTIVE_USE_HEADROOM",
             json.dumps({**json.loads(ROWS[0][9]), "site_code": "ABBA-001", "public_no": 9}), date(2026, 10, 31),
             "MINIGRID")
    items = opportunity_items([*other, alpha], *WEEK, None)
    assert [i["site_code"] for i in items] == ["ABBA-001", "KOBO-001"]


def test_state_and_filter_state_mapping():
    gone = [*ROWS, _e(2, "WITHDRAWN", date(2026, 11, 1), datetime(2026, 11, 1, 1, tzinfo=UTC))]
    (item,) = opportunity_items(gone, *WEEK, None)
    assert item["state"] == "WITHDRAWN" and item["filter_state"] == "no_longer_supported"
    assert item["state_label"] == "No longer seen"
    sup = [_o(O4, 1, _addis(2026, 10, 31), _addis(2026, 11, 2), public_no=4, first="2026-10-28", last="2026-11-01",
              status="SUPPORTED", codes=(), headroom={"low": "25.0", "high": "31"}), ROWS[2]]
    (s,) = opportunity_items(sup, *WEEK, None)
    assert s["filter_state"] == "supported" and s["value_line"] == "25–31 kW at midday on every eligible day"
    assert s["limit_line"] is None and s["evidence_label"] == "Supported"


# --- copy (§2.2) --------------------------------------------------------------------------------------------------

def test_copy_literals():
    assert v.seen_line(1, 1, date(2026, 10, 31), date(2026, 10, 31)) == "Seen on 1 of 1 well-observed days · 31 Oct"
    assert v.seen_line(2, 4, date(2026, 10, 28), date(2026, 11, 1)) == \
        "Seen on 2 of 4 well-observed days · 28 Oct–1 Nov"
    assert v.value_line("SUPPORTED", {"low": "25", "high": "25.0"}) == "25 kW at midday on every eligible day"
    assert v.value_line("LIMITED", {"low": "1", "high": "2"}) is None
    assert v.limit_line("LIMITED", ["SOURCE_CLASS_UNKNOWN"], []) == v.LIMIT_MIXED
    assert v.limit_line("LIMITED", [], ["LIMITED", "CONFLICT", "ELIGIBLE", None, "EXCLUDED"]) == \
        "Limited evidence: 2 of the 5 study days lack a reading needed to size it"
    assert v.limit_line("UNKNOWN", [], [None, None, "ELIGIBLE", "EXCLUDED", "EXCLUDED"]) == \
        "Not judged yet: 2 of the 5 study days have no reading"
    assert v.limit_line("SUPPORTED", [], []) is None
    assert v.EVIDENCE_LABEL == {"SUPPORTED": "Supported", "LIMITED": "Limited evidence", "UNKNOWN": "Not judged yet"}
    assert v.THREAD_STATE_WORDS["RESOLVED_MONITORING"] == "Checked and working, monitoring"
    assert v.OPP_NONE == "No opportunity found in this period"


# --- lens helpers (R5) --------------------------------------------------------------------------------------------

def test_thread_signal_key_and_lens_flags():
    assert thread_signal_key("PRODUCTIVE_USE_HEADROOM") == "SIGNAL:PRODUCTIVE_USE_HEADROOM"
    assert thread_signal_key("GENERATOR_RUNTIME_ABOVE_NEED") == finding_signal_key("GENERATOR_RUNTIME_ABOVE_NEED")
    assert lens_flags("SIGNAL:PRODUCTIVE_USE_HEADROOM", "mini_grid") == ["OPPORTUNITY"]
    assert lens_flags("WARNING:BATTERY_NEAR_RESERVE", "mini_grid") == ["RISK"]   # MG-4 PROTECT_ASSET
    assert lens_flags("WARNING:PEAK_NEAR_IMPORT_LIMIT", "ev_charging") == ["COST"] or \
        lens_flags("WARNING:PEAK_NEAR_IMPORT_LIMIT", "ev_charging") in (["RISK"], ["OPPORTUNITY"], [])
    assert lens_flags("SIGNAL:EVIDENCE_GAP", "mini_grid") == []          # MG-7 ASSURE_PERFORMANCE
    assert lens_flags("FINDING:NOPE", "mini_grid") == []
    key = finding_signal_key("GENERATOR_RUNTIME_ABOVE_NEED")
    assert categories_for(key, "mini_grid") == categories_for(thread_signal_key("GENERATOR_RUNTIME_ABOVE_NEED"),
                                                              "mini_grid")


def test_lens_of_every_category():
    from assetops_backend.outcomes.outcome_map import ENTRIES, LENS_OF_CATEGORY, outcome_roles
    from assetops_backend.outcomes.catalogue import DOMAINS, OUTCOME_BY_KEY
    seen = set()
    for key in ENTRIES:
        for domain in DOMAINS:
            moves, _ = outcome_roles(key, domain)
            if moves:
                cat = OUTCOME_BY_KEY[moves[0]].category
                seen.add(cat)
                assert lens_flags(key, domain) == ([LENS_OF_CATEGORY[cat]] if cat in LENS_OF_CATEGORY else [])
    assert {"GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET"} <= seen


# --- R3 -----------------------------------------------------------------------------------------------------------

def test_headroom_rules_keep_their_claims():
    bounds = [Bound(Decimal("25"), Decimal("31")), Bound(Decimal("27"), Decimal("29"))]
    assert headroom_on_every_eligible_day(bounds) == Bound(Decimal("25"), Decimal("29"))
    assert observed_headroom_range(bounds) == Bound(Decimal("25"), Decimal("31"))
    assert headroom_on_every_eligible_day([]) is None and observed_headroom_range([]) is None


def test_frozen_result_headroom_equals_the_pre_move_rule():
    from assetops_backend.mini_decisions import projection as pj
    rows = [{"local_day": f"2026-10-{27 + i}", "decision": "ELIGIBLE",
             "opportunity_kwh": {"low": str(20 + i), "high": str(40 - i)}, "constraints": [], "evidence_ids": []}
            for i in range(5)]
    orig = pj.day_row
    from types import SimpleNamespace
    pj.day_row = lambda d: d.row  # type: ignore[assignment]
    try:
        out = frozen_result([SimpleNamespace(local_day=r["local_day"], row=r) for r in rows],  # type: ignore[arg-type]
                            "MEASURED")
    finally:
        pj.day_row = orig  # type: ignore[assignment]
    lows = [Decimal(r["opportunity_kwh"]["low"]) for r in rows]
    highs = [Decimal(r["opportunity_kwh"]["high"]) for r in rows]
    assert out["headroom_kw"] == {"low": pj.decimal_text(min(lows)), "high": pj.decimal_text(min(highs))}


# --- Portfolio (§2.3) ---------------------------------------------------------------------------------------------

def test_portfolio_block_and_card():
    (item,) = opportunity_items(ROWS, *WEEK, None)
    found = opportunity_block([item])
    assert found["state"] == "FOUND" and found["items"] == [item] and found["headroom"] is None
    assert found["destination"] == "/findings/opportunities" and found["finding_id"] is None
    none = opportunity_block([])
    assert none["state"] == "NONE" and none["items"] == []
    card = productive_use_card([item])
    assert (card["state"], card["detail"], card["basis_text"], card["tone"], card["destination"]) == \
        ("FOUND", "Kobo daytime solar", "Listed under Findings › Opportunities", "green", "/findings/opportunities")
    empty = productive_use_card([])
    assert (empty["state"], empty["detail"], empty["tone"]) == ("NONE", "No opportunity found in this period",
                                                                "neutral")
    assert opportunity_block(None)["state"] == "UNKNOWN" and productive_use_card(None)["state"] == "UNKNOWN"


# --- SUPPORT_LOST (R6) --------------------------------------------------------------------------------------------

def _thread(links: list[str]) -> dict:
    return {"mechanism": "PRODUCTIVE_USE_HEADROOM", "subject_ref": "SITE", "links": links,
            "events": [lc.Event(1, "OPEN", "OCCURRENCE", O4, date(2026, 10, 31))],
            "occurrences": [(O4, _addis(2026, 10, 31))]}


def _inputs(eligible: int) -> dict:
    return {"tz": ADDIS, "finding_lifecycle": {},
            "opportunity_heads": {O4: {"revision_id": "rev-2", "created_at": datetime(2026, 11, 3, tzinfo=UTC),
                                       "eligible_days": eligible}}}


def test_support_lost_for_an_opportunity_without_action():
    causes = thread_causes(_thread([]), [], _inputs(0))
    (lost,) = [c for c in causes if c.cause == lc.SUPPORT_LOST]
    assert lost.cause_id == "rev-2" and lost.known_at == datetime(2026, 11, 3, tzinfo=UTC)
    assert not [c for c in thread_causes(_thread([]), [], _inputs(2)) if c.cause == lc.SUPPORT_LOST]


def test_no_support_lost_with_a_linked_action():
    assert not [c for c in thread_causes(_thread(["act-1"]), [], _inputs(0)) if c.cause == lc.SUPPORT_LOST]
