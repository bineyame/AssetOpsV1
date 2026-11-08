"""DIESEL-K6b L0 (build sheet DIESEL-1 §9m.4, ruling DIESEL-1-R3m): `fuel-residual-within-band-1`, no database.

1. `later_nights`; 2. the choice by data quality; 3. the verdict table; 4. the literals (H1, guard V, H4, no money);
5. H2 static and the wire; 6. the outcome rows; 7. the board entry; 8. the Refs and the request link; 9. the KIS-5
and KIS-10 self-tests (one pass body, one fail body per item). Each "must fail" names the mutation it catches.
"""

from __future__ import annotations

import ast
import inspect
import re
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import pytest

from assetops_backend.actions import fuel_verification as fv
from assetops_backend.chain import refs, site_chain
from assetops_backend.site_outcomes import mini
from assetops_backend.site_outcomes.board import FuelVerdictFact

UTC = timezone.utc
TZ = "Africa/Dar_es_Salaam"            # UTC+3, no DST
SITE = "KISIWA-001"
NIGHT = date(2026, 10, 20)             # the night of the finding
H1 = ("This check shows the fuel stayed accounted for after the change; it does not measure how much the change "
      "itself prevented.")
H4 = re.compile(r"\b(theft|stolen|stole|siphon\w*|pilfer\w*)\b", re.IGNORECASE)
MONEY_KEY = re.compile(r"amount|price|currency|money", re.IGNORECASE)


@dataclass(frozen=True)
class W:
    """A FuelBalanceWindow stand-in (the attributes the family reads)."""
    night_date: date
    state: str = "WITHIN_MARGIN"
    residual_low: Fraction = Fraction(-5)
    residual_high: Fraction = Fraction(10)
    gap_minutes: int = 0
    terms: dict = field(default_factory=lambda: {"unknown_slots": "0"})
    revision: int = 1
    id: UUID = field(default_factory=uuid4)
    input_sha256: str = "a" * 64
    tank_asset_id: UUID = UUID(int=7)

    @property
    def window_start(self) -> datetime:
        return fv.night_bounds(self.night_date, TZ)[0]

    @property
    def window_end(self) -> datetime:
        return fv.night_bounds(self.night_date, TZ)[1]


def local(d: date, h: int, m: int = 0) -> datetime:
    return datetime(d.year, d.month, d.day, h, m, tzinfo=timezone(timedelta(hours=3))).astimezone(UTC)


BASELINE = W(NIGHT, "UNEXPLAINED", Fraction(45), Fraction(60))
EFFECTIVE = local(NIGHT + timedelta(days=1), 15, 5)    # 21 Oct 15:05 local: after the baseline window's end
ACTION = {"id": uuid4(), "action_code": "ACT-000003", "title": "Seal the tank cap", "owner_label": "Site lead",
          "domain": "FUEL_BALANCE", "origin_finding_id": uuid4(), "origin_finding_revision_id": uuid4(),
          "timezone": TZ}
APPLIED = {"id": uuid4(), "case_id": uuid4(), "occurred_at": EFFECTIVE, "public_code": "WR-000004"}


def plan(now: datetime | None = None) -> dict:
    return fv.plan_row(ACTION["id"], ACTION, APPLIED, BASELINE, now or EFFECTIVE + timedelta(minutes=30))


def first(p: dict) -> date:
    return date.fromisoformat(p["later_selection_rule"]["candidates"]["from"])


def nights(p: dict, *ws: W) -> dict:
    return {w.night_date: w for w in ws}


def at_close(p: dict) -> datetime:
    return fv.night_bounds(first(p) + timedelta(days=13), TZ)[1]


# --- 1. later_nights ---------------------------------------------------------------------------------------------

def test_1_later_nights_first_window_at_or_after_effective() -> None:
    """Must fail if `>=` becomes `>` (exactly 18:00 local would move to the next night)."""
    d = date(2026, 10, 21)
    assert fv.later_nights(datetime(2026, 10, 21, 12, 5, tzinfo=UTC), TZ)[0] == d       # 15:05 local
    assert fv.later_nights(local(d, 18, 30), TZ)[0] == d + timedelta(days=1)             # 18:30 local
    assert fv.later_nights(local(d, 18, 0), TZ)[0] == d                                  # exactly 18:00 local
    got = fv.later_nights(local(d, 18, 0), TZ)
    assert len(got) == 14 and got[-1] == d + timedelta(days=13)
    assert fv.night_bounds(d, TZ) == (datetime(2026, 10, 21, 15, tzinfo=UTC), datetime(2026, 10, 22, 9, tzinfo=UTC))


# --- 2. choice by data quality -----------------------------------------------------------------------------------

def test_2_choice_skips_unassessed_and_unknown_slots_and_keeps_a_failing_complete_night() -> None:
    """Must fail if the choice filters on `passes` (the failing night would be skipped and the verdict VERIFIED)."""
    p = plan()
    d = first(p)
    ws = [W(d, "NOT_ASSESSED", None, None, terms={}), W(d + timedelta(days=1), terms={"unknown_slots": "2"}),
          W(d + timedelta(days=2), "UNEXPLAINED", Fraction(20), Fraction(40)), W(d + timedelta(days=3)),
          W(d + timedelta(days=4)), W(d + timedelta(days=5))]
    r = fv.assess(p, nights(p, *ws), at_close(p) - timedelta(days=5))
    assert [w.night_date for w in r["chosen"]] == [d + timedelta(days=i) for i in (2, 3, 4)]
    assert r["outcome"] == fv.INEFFECTIVE and r["reasons"] == [fv.TARGET_MISS]
    assert not fv.complete(None) and not fv.complete(ws[0]) and not fv.complete(ws[1]) and fv.complete(ws[2])


# --- 3. the verdict table ----------------------------------------------------------------------------------------

def _judge(*specs, now=None) -> dict:
    p = plan()
    d = first(p)
    ws = [W(d + timedelta(days=i), **spec) for i, spec in enumerate(specs)]
    return fv.assess(p, nights(p, *ws), now or at_close(p) - timedelta(days=10))


def test_3_three_passes_verified() -> None:
    r = _judge({}, {}, {})
    assert (r["decided"], r["outcome"], r["reasons"]) == (True, fv.VERIFIED, [fv.TARGET_MET])
    assert r["sentence"] == fv.VERIFIED_TEXT.format(n=3) and r["sentence"].startswith("On 3 fully checked nights")


def test_3_band_and_gap_failures_name_the_first_failing_night() -> None:
    p = plan()
    d = first(p)
    band = _judge({}, {"residual_low": Fraction(5), "residual_high": Fraction(20)}, {"gap_minutes": 90})
    assert band["outcome"] == fv.INEFFECTIVE and band["first_fail"] == d + timedelta(days=1)
    assert band["sentence"] == fv.MISS_BAND_TEXT.format(date=f"{(d + timedelta(days=1)).day} Oct")
    gap = _judge({}, {"gap_minutes": 90}, {})
    assert gap["sentence"] == fv.MISS_GAP_TEXT.format(date=f"{(d + timedelta(days=1)).day} Oct")
    both = _judge({"residual_low": Fraction(1), "gap_minutes": 90}, {}, {})
    assert both["sentence"].startswith("On the night of") and "did not match" in both["sentence"]  # band first


@pytest.mark.parametrize(("low", "high", "ok"), [(Fraction(0), Fraction(5), True), (Fraction(-5), Fraction(0), True),
                                                 (Fraction(1, 10**6), Fraction(5), False),
                                                 (Fraction(-9), Fraction(-1, 10**6), False)])
def test_3_band_edges_are_exact(low, high, ok) -> None:
    """Must fail if any tolerance is added (1e-6 L above zero, and EXCESS below zero, both fail)."""
    assert fv.passes(W(NIGHT, residual_low=low, residual_high=high))[0] is ok


def test_3_short_open_short_closed_and_closed_failing() -> None:
    p = plan()
    open_ = _judge({}, {}, now=at_close(p) - timedelta(seconds=1))
    assert (open_["decided"], open_["not_judged_text"]) == (False, fv.LATER_TEXT.format(n=2))
    closed = _judge({}, {}, now=at_close(p))
    assert (closed["outcome"], closed["reasons"]) == (fv.INCONCLUSIVE, [fv.LATER_SHORT])
    assert closed["sentence"] == fv.LATER_SHORT_TEXT.format(n=2)
    failing = _judge({}, {"gap_minutes": 61}, now=at_close(p))
    assert failing["outcome"] == fv.INEFFECTIVE


# --- 4. literals -------------------------------------------------------------------------------------------------

def test_4_fixed_line_is_h1_byte_for_byte() -> None:
    assert fv.FIXED_LINE == H1


def test_4_every_literal_passes_guard_v_h4_and_names_no_money() -> None:
    import test_out_b2_vocabulary as b2

    patterns = b2._patterns()
    texts = list(fv.LITERALS) + [fv.VERIFIED_TEXT.format(n=3), fv.MISS_BAND_TEXT.format(date="4 Oct"),
                                 fv.LATER_TEXT.format(n=2), fv.SENSOR_GAP.format(m=90)]
    hits = sorted({(t, name) for t in texts for name, pat in patterns if pat.search(t)})
    assert hits == []
    assert not [t for t in texts if H4.search(t)]
    assert not [t for t in texts if re.search(r"\$|\bprice\b|\b(USD|TZS|KES|EUR)\b", t, re.IGNORECASE)]
    assert any(pat.search("The fuel draft is loaded") for _, pat in patterns)  # the scan is not vacuous


# --- 5. H2 static and the wire -----------------------------------------------------------------------------------

def test_5_module_imports_no_money_module() -> None:
    tree = ast.parse(Path(fv.__file__).read_text(encoding="utf-8"))
    names = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    names += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    assert not [n for n in names if re.search(r"financials|fuel_cost|price|verification_families", n)], names


def _money_keys(node: Any, path: str = "") -> list[str]:
    if isinstance(node, dict):
        return [p for k, v in node.items() for p in ([f"{path}.{k}"] if MONEY_KEY.search(str(k)) else [])
                + _money_keys(v, f"{path}.{k}")]
    if isinstance(node, list):
        return [p for i, v in enumerate(node) for p in _money_keys(v, f"{path}[{i}]")]
    return []


def _verified_wire() -> tuple[dict, dict, dict]:
    p = plan()
    d = first(p)
    result = fv.assess(p, nights(p, W(d), W(d + timedelta(days=1)), W(d + timedelta(days=2))), at_close(p))
    outcome, metrics = fv.outcome_rows(p, result, at_close(p), "REGISTERED_SIMULATION")
    ctx = {"action": ACTION, "applied": APPLIED}
    origin = {"finding_id": ACTION["origin_finding_id"], "revision_id": ACTION["origin_finding_revision_id"]}
    wire = fv.fuel_summary_wire(ctx, p, [{**outcome, "metrics": metrics}], None, origin, BASELINE, SITE,
                                site_visit="Visited the tank")
    return wire, outcome, p


def test_5_populated_wire_has_no_value_and_no_money_key() -> None:
    """Must fail if a value line is added (`value` not None) or a money key appears at any depth."""
    wire, _, _ = _verified_wire()
    assert wire["value"] is None and wire["cost_check"] is None
    assert _money_keys(wire) == []
    assert wire["state"] == "VERIFIED" and wire["headline"] == "Fuel stayed accounted for"
    assert wire["fixed_line"] == H1 and wire["sentence"] == fv.VERIFIED_TEXT.format(n=3)
    assert [c["value"] for c in wire["cards"]] == ["3 of 3", "3 of 3 nights", "Readings all night on 3 of 3 nights",
                                                   "Fuel stayed accounted for"]
    assert [n["role"] for n in wire["nights"]] == ["BASELINE", "LATER", "LATER", "LATER"]
    assert wire["nights"][0]["range_text"] == "45.0 to 60.0 L" and wire["nights"][0]["result_text"] == "Unexplained fuel found"
    assert wire["origin"]["href"] == (f"/sites/{SITE}/fuel-findings/{ACTION['origin_finding_id']}"
                                      f"?revision_id={ACTION['origin_finding_revision_id']}")
    assert wire["activity"]["case_href"] == f"/maintenance/requests/{APPLIED['case_id']}"
    assert wire["activity"]["completed_text"] == "21 Oct 15:05" and wire["activity"]["note"] == fv.ACTIVITY_NOTE
    assert wire["outcome"]["source_class"] == "REGISTERED_SIMULATION"


def test_5_no_plan_and_not_judged_wires() -> None:
    ctx = {"action": ACTION, "applied": None}
    origin = {"finding_id": ACTION["origin_finding_id"], "revision_id": ACTION["origin_finding_revision_id"]}
    none = fv.fuel_summary_wire(ctx, None, [], None, origin, BASELINE, SITE)
    assert none["state"] == "NO_PLAN" and none["fixed_line"] == H1 and none["activity"] is None
    assert [c["value"] for c in none["cards"]][1:3] == [fv.NOT_CHECKED, fv.NOT_CHECKED]
    p = plan()
    live = fv.assess(p, nights(p, W(first(p))), EFFECTIVE + timedelta(days=2))
    nj = fv.fuel_summary_wire({"action": ACTION, "applied": APPLIED}, p, [], live, origin, BASELINE, SITE)
    assert nj["state"] == "NOT_JUDGED" and nj["not_judged_text"] == fv.LATER_TEXT.format(n=1)
    assert nj["fixed_line"] == H1 and nj["value"] is None and nj["outcome"] is None


# --- 6. outcome rows ---------------------------------------------------------------------------------------------

def test_6_outcome_rows() -> None:
    p = plan()
    d = first(p)
    result = fv.assess(p, nights(p, W(d), W(d + timedelta(days=1), gap_minutes=70), W(d + timedelta(days=2))),
                       at_close(p))
    outcome, metrics = fv.outcome_rows(p, result, at_close(p), "AUTHORED_DEMONSTRATION")
    assert [(m["window_name"], m["state"], m["value_text"], m["unit"]) for m in metrics] == [
        ("BASELINE", "PASS", "45.0 to 60.0 L", "L"), ("LATER", "PASS", "3 of 3", "L"), ("COMPARISON", "FAIL", None, "L")]
    assert metrics[0]["reason"] == f"night {NIGHT.isoformat()}: UNEXPLAINED"
    assert metrics[1]["reason"] == ", ".join((d + timedelta(days=i)).isoformat() for i in range(3))
    assert metrics[2]["reason"] == fv.TARGET["rule"] and all(m["metric_key"] == fv.METRIC_KEY for m in metrics)
    assert outcome["idempotency_key"] == f"fuel-outcome-{p['id']}" and outcome["triggering_job"] == fv.EVALUATOR_JOB
    assert outcome["outcome"] == "INEFFECTIVE" and outcome["details"]["first_fail"] == (d + timedelta(days=1)).isoformat()
    assert outcome["details"]["source"] == {"source_class": "AUTHORED_DEMONSTRATION"}
    assert "source" not in outcome["basis"] and "source_class" not in str(outcome["basis"])
    assert outcome["details"]["baseline"] == {"night_date": NIGHT.isoformat(), "window_id": str(BASELINE.id),
                                              "revision": 1, "input_sha256": "a" * 64}
    assert [x["fail_reason"] for x in outcome["details"]["later"]] == [None, "GAP", None]
    assert fv.used_dates(p, result) == sorted({x.isoformat() for n in [NIGHT, d, d + timedelta(days=1),
                                                                        d + timedelta(days=2)]
                                               for x in (n, n + timedelta(days=1))})


def test_6_plan_row_columns() -> None:
    p = plan()
    assert p["rule_id"] == fv.FUEL and p["plan_version"] == fv.FUEL_PLAN_VERSION
    assert p["triggering_fixture"] == fv.FUEL_LEVER and p["effective_from"] == EFFECTIVE
    assert p["baseline_start"] == BASELINE.window_start and p["baseline_end"] == BASELINE.window_end
    assert p["later_start"] == fv.night_bounds(date(2026, 10, 21), TZ)[0]
    assert p["later_end"] - p["later_start"] == timedelta(days=14) and p["guardrails"] == {} and p["bands"] == {}
    assert p["baseline_selection"]["state_found"] == "UNEXPLAINED" and p["baseline_selection"]["residual_low"] == "45"
    assert p["idempotency_key"] == f"fuel-plan-{ACTION['id']}" and p["origin_opportunity_revision_id"] is None


# --- 7. the board entry ------------------------------------------------------------------------------------------

def _assure(fuel: tuple) -> list:
    return [c for c in mini._assure("KISIWA-001", (), {}, True, "FULL", None, [], False, False, (), fuel=fuel)
            if c.key == "verified_results"]


def test_7_board_entry_verified_and_pending_with_the_fuel_verdict_ref() -> None:
    ref = refs.fuel_verdict_ref(SITE, "a-1")
    (done,) = _assure((FuelVerdictFact("a-1", "ACT-000003", "t-1", "VERIFIED", ref, "REGISTERED_SIMULATION"),))
    code = mini.display_code("ACT-000003")
    assert done.text == f"{code} verified on example data" and done.link_ref == ref and done.confidence is None
    (pending,) = _assure((FuelVerdictFact("a-1", "ACT-000003", "t-1", None, ref),))
    assert pending.text == f"{code} not yet verified" and pending.confidence == mini.PENDING_CHIP
    assert pending.link_ref["kind"] == "FUEL_VERDICT"


def test_7_verified_values_signature_is_unchanged() -> None:
    """Must fail if `fuel` is passed into `_verified_values` (H2, structural)."""
    assert str(inspect.signature(mini._verified_values)) == (
        "(reads: 'Reads', ports: 'MiniPorts', actions: 'tuple[ActionFact, ...]', "
        "opp: 'tuple[OpportunityActionFact, ...]') -> 'tuple[dict[str, Any], ...]'")
    src = inspect.getsource(mini)
    assert re.search(r"_verified_values\(reads, ports, actions, opp\)", src)


def test_7_fuel_verdict_actions_filter() -> None:
    lo, hi = datetime(2026, 10, 20, tzinfo=UTC), datetime(2026, 11, 20, tzinfo=UTC)
    occ = {"thread_id": "t-1", "finding_id": "f-1", "opportunity_id": None, "episode_start": lo + timedelta(days=1),
           "episode_end": lo + timedelta(days=2), "mechanism": "UNEXPLAINED_FUEL", "subject_ref": "x", "occurrence_no": 1}
    fuel = {"action_id": "a-1", "action_code": "ACT-000003", "kind": "DOMAIN_INTENT", "thread_id": "t-1",
            "origin_finding_id": "f-1", "origin_opportunity_id": None, "accepted_at": lo + timedelta(days=3),
            "action_domain": "FUEL_BALANCE", "outcome": "VERIFIED", "outcome_recorded_at": lo + timedelta(days=9),
            "source_class": None}
    cold = {**fuel, "action_id": "a-2", "action_domain": "COLDCHAIN"}
    rows = {"occurrences": (occ,), "events": (), "actions": (fuel, cold)}
    got = site_chain.fuel_verdict_actions(rows, site=SITE, cutoff=None, lo=lo, hi=hi)
    assert [(g["action_id"], g["outcome"], g["ref"]["kind"]) for g in got] == [("a-1", "VERIFIED", "FUEL_VERDICT")]
    early = site_chain.fuel_verdict_actions(rows, site=SITE, cutoff=lo + timedelta(days=5), lo=lo, hi=hi)
    assert early[0]["outcome"] is None


# --- 8. Refs and the request link --------------------------------------------------------------------------------

def test_8_refs_and_action_wire_ref() -> None:
    aid = "7f1e0a52-4444-4a1e-9e7d-000000000007"
    assert refs.href_for(refs.fuel_verdict_ref(SITE, aid)) == f"/sites/{SITE}/domain-actions/{aid}/fuel-verification"
    base = {"action_id": aid, "kind": "DOMAIN_INTENT", "origin_opportunity_id": None}
    assert site_chain.action_wire_ref(SITE, {**base, "action_domain": "FUEL_BALANCE"})["kind"] == "FUEL_VERDICT"
    assert site_chain.action_wire_ref(SITE, {**base, "action_domain": "MINI", "origin_opportunity_id": "o"})["kind"] == \
        "DOMAIN_VERDICT"
    assert site_chain.action_wire_ref(SITE, {**base, "action_domain": "COLDCHAIN"})["kind"] == "ACTION"
    assert site_chain.action_wire_ref(SITE, {**base, "kind": "MINI_TRIAL"})["kind"] == "ACTION"


def test_8_request_link_opens_the_fuel_verdict_page() -> None:
    """R3m2 (K6b): must fail if the fuel branch is removed (the link would read `/actions/{id}/verification`)."""
    from assetops_backend.work import site_index as si
    from assetops_backend.work.link_coverage import DOMAIN_ACTION

    aid = str(uuid4())
    link = {"kind": DOMAIN_ACTION, "action_id": aid, "action_event_id": None, "finding_revision_id": str(uuid4()),
            "action_domain": "FUEL_BALANCE"}
    assert si._action_link(SITE, link, {"lineage": True})["href"] == f"/sites/{SITE}/domain-actions/{aid}/fuel-verification"
    assert si._action_link(SITE, link, {"lineage": False})["href"] is None


# --- 9. KIS-5 and KIS-10 self-tests ------------------------------------------------------------------------------

import demo_combined_rows as rows  # noqa: E402  (tools/ is on the path, as for test_demo_combined_finish_rows)


def _kis5_body() -> dict:
    wire, outcome, p = _verified_wire()
    p_nights = first(p)
    windows = {w.night_date: w for w in [W(p_nights), W(p_nights + timedelta(days=1)), W(p_nights + timedelta(days=2))]}
    # the stored outcome must pin the very windows the re-run sees
    result = fv.assess(p, windows, at_close(p))
    outcome, _ = fv.outcome_rows(p, result, at_close(p), None)
    read_back = {str(BASELINE.id): {"revision": 1, "input_sha256": "a" * 64}}
    read_back |= {str(w.id): {"revision": w.revision, "input_sha256": w.input_sha256} for w in windows.values()}
    return {"plan": p, "outcome": outcome, "read_back": read_back, "windows_by_date": windows, "summary": wire}


def test_9_kis5_pass_body() -> None:
    got = rows.kis5(**_kis5_body())
    assert got["outcome"] == "VERIFIED" and got["pins_checked"] == 4


@pytest.mark.parametrize("case", ["pin", "later", "verdict", "value", "money_key", "fixed_line"])
def test_9_kis5_fail_bodies(case: str) -> None:
    b = _kis5_body()
    if case == "pin":
        b["read_back"][str(BASELINE.id)] = {"revision": 2, "input_sha256": "a" * 64}
    elif case == "later":
        d = min(b["windows_by_date"])
        b["windows_by_date"][d - timedelta(days=0)] = W(d)          # a different window for the first night
    elif case == "verdict":
        b["outcome"] = {**b["outcome"], "outcome": "INCONCLUSIVE", "reasons": ["LATER_SHORT"]}
    elif case == "value":
        b["summary"] = {**b["summary"], "value": {"text": "x"}}
    elif case == "money_key":
        b["summary"] = {**b["summary"], "origin": {**b["summary"]["origin"], "amount_low": "1"}}
    else:
        b["summary"] = {**b["summary"], "fixed_line": "x"}
    with pytest.raises(AssertionError):
        rows.kis5(**b)


def _kis10_body() -> dict:
    p = plan()
    action = {"id": str(ACTION["id"]), "origin_finding_revision_id": ACTION["origin_finding_revision_id"]}
    entry = {"key": "verified_results", "text": f"{mini.display_code('ACT-000003')} verified on example data",
             "link_ref": refs.fuel_verdict_ref(SITE, str(ACTION["id"]))}
    board = {"rows": [{"category": "ASSURE_PERFORMANCE", "contributors": [entry], "nodes": {"verified_values": []}}]}
    return {"plan": p, "applied": APPLIED, "action": action, "claim_window_id": str(BASELINE.id),
            "action_thread": "t-1", "finding_thread": "t-1", "board": board, "code": "ACT-000003",
            "portfolio_lines": ["Kobo: ACT-002 about 17.00 USD a day"]}


def test_9_kis10_pass_body() -> None:
    assert rows.kis10(**_kis10_body())["thread"] == "t-1"


@pytest.mark.parametrize("case", ["late_freeze", "effective", "origin", "baseline", "thread", "entry_ref", "entry_missing",
                                  "value_entry", "portfolio_line"])
def test_9_kis10_fail_bodies(case: str) -> None:
    b = _kis10_body()
    if case == "late_freeze":
        b["plan"] = {**b["plan"], "recorded_at": b["plan"]["later_start"]}
    elif case == "effective":
        b["applied"] = {**APPLIED, "occurred_at": EFFECTIVE + timedelta(seconds=1)}
    elif case == "origin":
        b["action"] = {**b["action"], "origin_finding_revision_id": uuid4()}
    elif case == "baseline":
        b["claim_window_id"] = str(uuid4())
    elif case == "thread":
        b["finding_thread"] = "t-2"
    elif case == "entry_ref":
        b["board"]["rows"][0]["contributors"][0]["link_ref"] = refs.action_ref(SITE, str(ACTION["id"]))
    elif case == "entry_missing":
        b["board"]["rows"][0]["contributors"] = []
    elif case == "value_entry":
        b["board"]["rows"][0]["nodes"]["verified_values"] = [{"key": str(ACTION["id"]), "action_code": "ACT-000003"}]
    else:
        b["portfolio_lines"] = [f"Kisiwa: {mini.display_code('ACT-000003')} about 3.00 USD"]
    with pytest.raises(AssertionError):
        rows.kis10(**b)
