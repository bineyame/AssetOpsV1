"""CH-9b R1-R2 (CH9b2-R): the verification family registry and the `midday-productive-shift-1` plan freeze.

A verification plan's family is its `rule_id`. `FAMILIES` maps each family to its code path:

- `reserve-trial-1`: the S6-02a path in `verification.VerificationService` (`freeze`, `bind_later_selection`,
  `evaluate`, the plan/outcome/history reads), unchanged. Its plans belong to a W1 `action` (Finding origin).
- `midday-productive-shift-1`: `MiddayShift`, the plan of the MINI `domain_action` "run the mill at midday", raised
  from an opportunity (0051). It is frozen once, at story time, after the work case is COMPLETE and linked
  (CH9b1-R2: record, complete, link, then freeze) through `VerificationService.freeze_domain_plan`; no HTTP route.

The mill plan (R2, CH9b2-R Q2-Q7, Q9):

- The effective day is the Site-local day of the case's COMPLETE `occurred_at`. It is in **neither** window: a day
  with both pre- and post-change hours is neither "before" nor "after".
- Baseline: the last `MIN_DAYS` (3) COMPLETE days before the effective day, looking back at most `LOOK_DAYS` (14).
  Later window: the first 3 COMPLETE days after it, looking ahead at most 14; the plan stores that candidate range
  only, and CH-9b3 chooses the days at evaluation with the same `choose_days`.
- A day counts only when every `productive_kwh` row of the Site that day is COMPLETE (the SnapshotReader weakest-row
  day rule). Days are chosen by grade only; no value is read at freeze.
- Fewer than 3 COMPLETE baseline days: the plan still freezes, with the days found and `baseline_selection.state =
  "SHORT"`; CH-9b3 then shows "Not judged yet: only {n} of 3 fully checked days before the change".
- Target: the owner's declared rule (CH9b1-R P1), verbatim; `guardrails = {}` (BL-09, SCOPE-1).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_UP, Decimal, InvalidOperation
from typing import Any, Mapping, Sequence
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from assetops_backend.actions import reserve_trial
from assetops_backend.actions import verification_rules as rules
from assetops_backend.actions.lifecycle import SYSTEM_DEMO
from assetops_backend.actions.ports import ActionRefused
from assetops_backend.chain.grading import COMPLETE, NO_DATA
from assetops_backend.chain.reader import _day_grade
from assetops_backend.chain.vocabulary import money2

LOG = logging.getLogger(__name__)

RESERVE = "reserve-trial-1"
MIDDAY = "midday-productive-shift-1"
MIDDAY_PLAN_VERSION = "midday-productive-shift-verification-1"
MIDDAY_FIXTURE = "productive-load-midday@1"
MEASURE = "productive_kwh"
MIN_DAYS = 3
LOOK_DAYS = 14
SHORT, FULL = "SHORT", "COMPLETE"
FREEZE_COMMAND = "FREEZE_DOMAIN_VERIFICATION_PLAN"
#: CH9b1-R P1 (owner 2026-11-05, `.agent/owner-mill-pass-margin-2026-11-05.md`), verbatim; never fitted.
TARGET = {"rule": "10*mean(later) >= 11*mean(baseline) productive_kwh[midday]",
          "over": "COMPLETE days of each window", "ratio": [11, 10], "declared_by": "owner 2026-11-05"}
SHORT_TEXT = "Not judged yet: only {n} of 3 days with complete readings before the change"
DAY_RULE = ("A day counts only when every productive_kwh row of the Site that day is COMPLETE (the SnapshotReader "
            "weakest-row day rule); days are chosen by grade only, never by value.")
BASIS_TEXT = ("SYSTEM_DEMONSTRATION: story-time freeze of a domain Action's verification plan after its work case "
              "is COMPLETE and linked; no verified human principal exists, so no operator approval is recorded")


# ---- pure day choice (L0) -----------------------------------------------------------------------------------

def day_grades(rows: Sequence[Any], days: Sequence[date], measure: str = MEASURE) -> dict[date, str]:
    """Each requested day's grade from its `measure` rows (weakest row decides); a day with no row is NO_DATA."""
    by_day: dict[date, list[str]] = {}
    for r in rows:
        if r.measure == measure:
            by_day.setdefault(r.local_day, []).append(r.grade)
    return {d: _day_grade(by_day[d]) if d in by_day else NO_DATA for d in days}


def baseline_candidates(effective_day: date) -> list[date]:
    """The look-back range, nearest day first: effective_day-1 .. effective_day-14 (the effective day excluded)."""
    return [effective_day - timedelta(days=i) for i in range(1, LOOK_DAYS + 1)]


def later_candidates(effective_day: date) -> list[date]:
    """The look-ahead range, nearest day first: effective_day+1 .. effective_day+14 (the effective day excluded)."""
    return [effective_day + timedelta(days=i) for i in range(1, LOOK_DAYS + 1)]


def choose_days(grades: Mapping[date, str], candidates: Sequence[date], n: int = MIN_DAYS) -> list[date]:
    """The first `n` COMPLETE days of `candidates` in their order (nearest the change first), returned ascending.
    Only the grade is read; a day missing from `grades` does not count."""
    picked = [d for d in candidates if grades.get(d) == COMPLETE][:n]
    return sorted(picked)


def baseline_selection(grades: Mapping[date, str], effective_day: date) -> dict[str, Any]:
    candidates = baseline_candidates(effective_day)
    days = choose_days(grades, candidates)
    return {"state": FULL if len(days) == MIN_DAYS else SHORT, "found": len(days), "min_days": MIN_DAYS,
            "days": [d.isoformat() for d in days],
            "candidates": {"from": candidates[-1].isoformat(), "to": candidates[0].isoformat()},
            "grades": {d.isoformat(): grades.get(d, NO_DATA) for d in sorted(candidates)}}


def short_text(selection: Mapping[str, Any]) -> str | None:
    """CH9b2-R Q4 (MOCK DEVIATION, CH-9b3 renders it): the not-judged line of a SHORT baseline, else None."""
    return SHORT_TEXT.format(n=selection["found"]) if selection["state"] == SHORT else None


def local_midnight(day: date, tz: str) -> datetime:
    return datetime.combine(day, time(0), tzinfo=ZoneInfo(tz)).astimezone(timezone.utc)


# ---- the families --------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class ReserveTrial:
    """`reserve-trial-1`: `VerificationService.freeze` / `evaluate` and its reads, unchanged (R1)."""

    rule_id: str = RESERVE
    plan_version: str = rules.PLAN_VERSION
    owner: str = "action"


@dataclass(frozen=True)
class MiddayShift:
    """`midday-productive-shift-1`: the plan of a MINI domain Action from an opportunity."""

    rule_id: str = MIDDAY
    plan_version: str = MIDDAY_PLAN_VERSION
    owner: str = "domain_action"

    def freeze(self, store: Any, snapshots: Any, tenant_id: UUID, site_id: UUID, domain_action_id: UUID,
               now: datetime) -> tuple[int, dict[str, Any]]:
        ctx = store.domain_plan_context(tenant_id, site_id, domain_action_id)
        if ctx is None:
            raise ActionRefused(404, "ACTION_NOT_FOUND", "No such Action for this Site.")
        if ctx["plan"] is not None:
            return 200, {"replayed": True, "plan": plan_wire(ctx["plan"])}
        action, applied = ctx["action"], ctx["applied"]
        if action["domain"] != "MINI" or action["origin_opportunity_revision_id"] is None:
            raise ActionRefused(409, "VERIFICATION_FAMILY_UNSUPPORTED",
                                "Only a MINI Action raised from an opportunity has a midday verification plan.")
        if applied is None:
            raise ActionRefused(409, "VERIFICATION_ACTION_NOT_APPLIED",
                                "A verification plan needs the Action's linked work case to be COMPLETE.")
        if snapshots is None:
            raise ActionRefused(503, "VERIFICATION_SNAPSHOTS_UNAVAILABLE", "The day snapshots cannot be read.")
        tz = action["timezone"]
        effective = applied["occurred_at"].astimezone(timezone.utc)
        effective_day = effective.astimezone(ZoneInfo(tz)).date()
        candidates = baseline_candidates(effective_day)
        rows = snapshots.latest(tenant_id, site_id, candidates[-1], candidates[0], [MEASURE], known_at=now)
        grades = day_grades(rows, candidates)
        selection = baseline_selection(grades, effective_day)
        chosen = set(selection["days"])
        selection["pins"] = sorted(
            ({"day": r.local_day.isoformat(), "subject_ref": r.subject_ref, "revision": r.revision,
              "input_fp": r.input_fp} for r in rows if r.measure == MEASURE and r.local_day.isoformat() in chosen),
            key=lambda p: (p["day"], p["subject_ref"]))
        baseline_end = local_midnight(effective_day, tz)
        later_start = baseline_end + timedelta(days=1)
        later = later_candidates(effective_day)
        content = {
            "plan_version": MIDDAY_PLAN_VERSION, "rule_id": MIDDAY, "domain_action_id": str(domain_action_id),
            "origin_opportunity_revision_id": str(action["origin_opportunity_revision_id"]),
            "applied_work_event_id": str(applied["id"]), "effective_from": effective.isoformat(),
            "baseline_start": (baseline_end - timedelta(days=LOOK_DAYS)).isoformat(),
            "later_start": later_start.isoformat(),
            "baseline_selection": selection, "baseline_evidence_ids": [],
            "basis": {"measure": MEASURE, "period": "operating_hours", "timezone": tz, "day_rule": DAY_RULE,
                      "effective_day": effective_day.isoformat(),
                      "effective_day_rule": "The effective day is in neither window (CH9b2-R Q2).",
                      "applied": {"work_event_id": str(applied["id"]), "case_id": str(applied["case_id"]),
                                  "occurred_at": effective.isoformat()},
                      "snapshots_known_at": now.isoformat()},
            "target": TARGET, "guardrails": {}, "bands": {},
            "coverage": {"min_days": MIN_DAYS, "look_back_days": LOOK_DAYS, "look_ahead_days": LOOK_DAYS},
            "later_selection_rule": {
                "rule": ("the first 3 COMPLETE days after the effective day, at most 14 days ahead, chosen by grade "
                         "only at evaluation (choose_days)"),
                "min_days": MIN_DAYS, "candidates": {"from": later[0].isoformat(), "to": later[-1].isoformat()}},
        }
        payload = {"command": FREEZE_COMMAND, "domain_action_id": str(domain_action_id)}
        plan = {**content, "id": uuid4(), "domain_action_id": domain_action_id,
                "origin_opportunity_revision_id": action["origin_opportunity_revision_id"],
                "applied_work_event_id": applied["id"], "effective_from": effective,
                "baseline_start": baseline_end - timedelta(days=LOOK_DAYS), "baseline_end": baseline_end,
                "later_start": later_start, "later_end": later_start + timedelta(days=LOOK_DAYS),
                "plan_sha256": reserve_trial.sha(content), "actor_kind": SYSTEM_DEMO.actor_kind,
                "actor_id": SYSTEM_DEMO.actor_id, "source_channel": SYSTEM_DEMO.source_channel,
                "authorization_basis": BASIS_TEXT, "triggering_service": SYSTEM_DEMO.triggering_service,
                "triggering_fixture": MIDDAY_FIXTURE, "idempotency_key": f"midday-plan-{domain_action_id}",
                "payload": payload, "payload_sha256": reserve_trial.sha(payload), "recorded_at": now}
        row, replayed = store.freeze_domain_plan(tenant_id, site_id, plan)
        return (200 if replayed else 201), {"replayed": replayed, "plan": plan_wire(row)}


    # ---- CH-9b3: the verdict (CH9b3-R Q1-Q4, Q9) ------------------------------------------------------------

    def evaluate(self, store: Any, snapshots: Any, tenant_id: UUID, site_id: UUID, domain_action_id: UUID,
                 now: datetime, today: date | None = None) -> dict[str, Any]:
        """Judge the plan once: store the one decisive outcome when `assess` decides, else store nothing.
        Callable at story time (DD-1b) and by the `chain_snapshots` stage after its drain (Q9)."""
        ctx = store.domain_plan_context(tenant_id, site_id, domain_action_id)
        if ctx is None:
            raise ActionRefused(404, "ACTION_NOT_FOUND", "No such Action for this Site.")
        plan = ctx["plan"]
        if plan is None or plan["rule_id"] != MIDDAY:
            return {"state": "NO_PLAN", "stored": False}
        prior = store.domain_outcomes(tenant_id, site_id, domain_action_id)
        if prior:
            return {"state": prior[0]["outcome"], "stored": False, "replayed": True, "outcome_id": str(prior[0]["id"])}
        if snapshots is None:
            raise ActionRefused(503, "VERIFICATION_SNAPSHOTS_UNAVAILABLE", "The day snapshots cannot be read.")
        result = assess_plan(plan, snapshots, tenant_id, site_id, now, today)
        if not result["decided"]:
            return {"state": NOT_JUDGED, "stored": False, "not_judged_text": result["not_judged_text"]}
        used = [d.isoformat() for d in result["baseline_days"] + result["later_days"]]
        source_class = store.example_source_class(tenant_id, site_id, used, plan["basis"]["timezone"], now)  # WD-1m-R2
        outcome, metrics = outcome_rows(plan, result, now, source_class)
        row, replayed = store.record_domain_outcome(tenant_id, site_id, outcome, metrics)
        return {"state": row["outcome"], "stored": not replayed, "replayed": replayed, "outcome_id": str(row["id"])}


# ---- CH-9b3: the pure verdict (L0) ------------------------------------------------------------------------------

NOT_JUDGED = "NOT_JUDGED"
VERIFIED, INEFFECTIVE, INCONCLUSIVE = rules.VERIFIED, rules.INEFFECTIVE, rules.INCONCLUSIVE
TARGET_MET, LATER_SHORT, BASELINE_ZERO = "TARGET_MET", "LATER_SHORT", "BASELINE_ZERO"
METRIC_KEY = "midday_productive_kwh"
EVALUATOR_JOB = "midday-verification-evaluator"
#: CH9b3-R Q2 (MOCK DEVIATION, mirrors `SHORT_TEXT`): the later window is still open with fewer than 3 days.
LATER_TEXT = "Not judged yet: only {n} of 3 days with complete readings after the change"
#: CH9b3-R Q2: the look-ahead closed with fewer than 3 days (INCONCLUSIVE LATER_SHORT; MOCK DEVIATION).
LATER_SHORT_TEXT = "Only {n} of 3 days with complete readings after the change in the 14 days allowed, so no verdict is given"
#: CH9b3-R Q3 verbatim (MOCK DEVIATION).
BASELINE_ZERO_TEXT = "No midday use was measured before the change, so a 10% rise cannot be measured"
#: SCOPE-1 / CH9b3-R Q7 verbatim: the VERIFIED sentence.
VERIFIED_TEXT = "Midday use rose by at least the declared 10% on days with complete readings"
#: R7 (CH9b3-R Q7): the before/after line of a judged outcome.
R7_TEXT = "Midday use before and after the change: {b} → {a} kWh a day on {n} days with complete readings each"
CENT = Decimal("0.01")
#: MV-1 (FUEL-1 §2): the mill value line of a VERIFIED outcome. The arithmetic uses the SHOWN means and the shown
#: price, so the line reproduces by hand.
VALUE_BASIS = "ESTIMATED_SALES_AT_DECLARED_PRICE"
VALUE_TEXT = ("About {d} {cur} a day more in estimated sales to productive users: ({a} − {b}) kWh a day × your "
              "declared {p} {cur} per kWh, on {n} days with complete readings before and after the change")
VALUE_COST_TEXT = "No cost is recorded for this change"
VALUE_UNPRICED_TEXT = "No sales estimate: {why}"
VALUE_UNPRICED_WHY = {
    "NO_PRICE": "no price per kWh is declared for productive users",
    "PRICE_SPANS_WINDOW": "the declared price per kWh changed between the two periods",
}
VALUE_UNPRICED_OTHER = "the declared price per kWh could not be read"


def day_kwh(rows: Sequence[Any], days: Sequence[date]) -> dict[date, Decimal | None]:
    """Each day's Σ `value.kwh` over its `productive_kwh` rows (Decimal, exact); None when any row has no kWh."""
    out: dict[date, Decimal | None] = {}
    for d in days:
        total: Decimal | None = Decimal(0)
        for r in rows:
            if r.measure != MEASURE or r.local_day != d:
                continue
            kwh = (r.value or {}).get("kwh")
            if kwh is None or total is None:
                total = None
                continue
            total += Decimal(str(kwh))
        out[d] = total
    return out


def judged_grades(rows: Sequence[Any], days: Sequence[date]) -> dict[date, str]:
    """`day_grades`, with a COMPLETE day lacking a kWh value counted as NO_DATA (it is not fully checked)."""
    grades = day_grades(rows, days)
    values = day_kwh(rows, days)
    return {d: (NO_DATA if g == COMPLETE and values[d] is None else g) for d, g in grades.items()}


def mean_text(total: Decimal, n: int) -> str:
    return format((total / n).quantize(CENT, rounding=ROUND_HALF_EVEN), "f")


def miss_texts(l_sum: Decimal, nl: int, b_sum: Decimal, nb: int) -> tuple[str, str]:
    """CH-9b3 fix L2: (after, needed) texts of a MISS, compared exactly. Cents when they already read after < needed;
    otherwise more places (after rounded down, needed rounded up) until the shown figures agree with the verdict."""
    after, needed = l_sum / nl, b_sum * TARGET["ratio"][0] / TARGET["ratio"][1] / nb
    for places in range(2, 13):
        q = Decimal(1).scaleb(-places)
        a_txt = format(after.quantize(q, rounding=ROUND_HALF_EVEN if places == 2 else ROUND_DOWN), "f")
        n_txt = format(needed.quantize(q, rounding=ROUND_HALF_EVEN if places == 2 else ROUND_UP), "f")
        if Decimal(a_txt) < Decimal(n_txt):
            break
    return a_txt, n_txt


def assess(plan: Mapping[str, Any], rows: Sequence[Any], today: date) -> dict[str, Any]:
    """The verdict of a frozen plan over snapshot rows read now (pure; Decimal and integers only, never floats).

    - SHORT baseline (frozen), or a frozen baseline day no longer COMPLETE: not judged, nothing stored (Q2, Q4).
    - Later window: the first 3 COMPLETE days after the effective day, ended before `today` (Site-local), at most 14
      ahead. Fewer than 3 while the look-ahead is open: not judged; once it closed: INCONCLUSIVE LATER_SHORT (Q2).
    - Baseline mean 0: INCONCLUSIVE BASELINE_ZERO (Q3). Else `10*mean(later) >= 11*mean(baseline)`: VERIFIED
      TARGET_MET, otherwise INEFFECTIVE TARGET_MISS (Q1)."""
    selection = plan["baseline_selection"]
    effective_day = date.fromisoformat(plan["basis"]["effective_day"])
    base_days = [date.fromisoformat(d) for d in selection["days"]]
    later_all = later_candidates(effective_day)
    later_open = [d for d in later_all if d < today]
    closed = later_all[-1] < today
    out: dict[str, Any] = {"decided": False, "outcome": None, "reasons": [], "baseline_days": base_days,
                           "later_days": [], "not_judged_text": None, "line": None, "sentence": None,
                           "look_ahead_closed": closed}
    if selection["state"] == SHORT:
        out["not_judged_text"] = short_text(selection)
        return out
    grades = judged_grades(rows, base_days + later_open)
    still = [d for d in base_days if grades[d] == COMPLETE]
    if len(still) < MIN_DAYS:
        out["not_judged_text"] = SHORT_TEXT.format(n=len(still))
        out["days_before_now"] = len(still)  # L3: the table's count is the line's count
        return out
    later = choose_days(grades, later_open)
    out["later_days"] = later
    values = day_kwh(rows, base_days + later)
    b_sum = sum((values[d] for d in base_days), Decimal(0))
    nb, nl = len(base_days), len(later)
    out.update(baseline_kwh=b_sum, baseline_mean=mean_text(b_sum, nb),
               threshold=mean_text(b_sum * TARGET["ratio"][0] / TARGET["ratio"][1], nb))
    if nl < MIN_DAYS:
        if not closed:
            out["not_judged_text"] = LATER_TEXT.format(n=nl)
            return out
        out.update(decided=True, outcome=INCONCLUSIVE, reasons=[LATER_SHORT], line=LATER_SHORT_TEXT.format(n=nl))
        return out
    l_sum = sum((values[d] for d in later), Decimal(0))
    out.update(decided=True, later_kwh=l_sum, later_mean=mean_text(l_sum, nl))
    out["line"] = R7_TEXT.format(b=out["baseline_mean"], a=out["later_mean"], n=nl)
    if b_sum == 0:
        out.update(outcome=INCONCLUSIVE, reasons=[BASELINE_ZERO], sentence=BASELINE_ZERO_TEXT, threshold=None)  # L1
    elif TARGET["ratio"][1] * l_sum * nb >= TARGET["ratio"][0] * b_sum * nl:
        out.update(outcome=VERIFIED, reasons=[TARGET_MET], sentence=VERIFIED_TEXT)
    else:
        out.update(outcome=INEFFECTIVE, reasons=[rules.TARGET_MISS])
        out["later_mean"], out["threshold"] = miss_texts(l_sum, nl, b_sum, nb)  # L2
        out["line"] = R7_TEXT.format(b=out["baseline_mean"], a=out["later_mean"], n=nl)
    return out


def assess_plan(plan: Mapping[str, Any], snapshots: Any, tenant_id: UUID, site_id: UUID, now: datetime,
                today: date | None = None) -> dict[str, Any]:
    """`assess` over the rows `SnapshotReader.latest` returns as known at `now` (baseline start .. look-ahead end)."""
    tz = plan["basis"]["timezone"]
    today = today or now.astimezone(ZoneInfo(tz)).date()
    effective_day = date.fromisoformat(plan["basis"]["effective_day"])
    first = min([date.fromisoformat(d) for d in plan["baseline_selection"]["days"]] or [effective_day])
    rows = [r for r in snapshots.latest(tenant_id, site_id, first, later_candidates(effective_day)[-1], [MEASURE],
                                        known_at=now) if r.measure == MEASURE]
    result = assess(plan, rows, today)
    used = {d.isoformat() for d in result["baseline_days"] + result["later_days"]}
    result["pins"] = sorted(({"day": r.local_day.isoformat(), "subject_ref": r.subject_ref, "revision": r.revision,
                              "input_fp": r.input_fp} for r in rows if r.local_day.isoformat() in used),
                            key=lambda p: (p["day"], p["subject_ref"]))
    result["today"], result["known_at"] = today, now
    return result


def outcome_rows(plan: Mapping[str, Any], result: Mapping[str, Any], now: datetime, source_class: str | None = None,
                 ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """The outcome row and its BASELINE / LATER / COMPARISON metric rows of a decided `assess` result. WD-1m-R2: the
    example-data class of the used days is stored in `details.source` (never in `basis`, so replay identity holds)."""
    base = [d.isoformat() for d in result["baseline_days"]]
    later = [d.isoformat() for d in result["later_days"]]
    unit = "kWh/day"

    def window(name: str, days: list[str], mean: str | None) -> dict[str, Any]:
        return rules._metric(METRIC_KEY, name, "PASS" if len(days) == MIN_DAYS else "UNKNOWN", value=mean,
                             unit=unit, reason=f"{len(days)} of {MIN_DAYS} days with complete readings:{', '.join(days)}")

    comparison = {VERIFIED: "PASS", INEFFECTIVE: "FAIL"}.get(result["outcome"], "UNKNOWN")
    metrics = [window("BASELINE", base, result.get("baseline_mean")),
               window("LATER", later, result.get("later_mean")),
               rules._metric(METRIC_KEY, "COMPARISON", comparison, value=result.get("later_mean"),
                             threshold=result.get("threshold"), unit=unit, reason=TARGET["rule"])]
    basis = {"plan_id": str(plan["id"]), "plan_sha256": plan["plan_sha256"], "rule_id": MIDDAY,
             "plan_version": MIDDAY_PLAN_VERSION, "target": TARGET, "snapshots_known_at": now.isoformat()}
    details = {"baseline": {"days": base, "sum_kwh": format(result["baseline_kwh"], "f"),
                            "mean_kwh_per_day": result["baseline_mean"]},
               "later": {"days": later, **({"sum_kwh": format(result["later_kwh"], "f"),
                                           "mean_kwh_per_day": result["later_mean"]} if "later_kwh" in result else {})},
               "threshold_kwh_per_day": result.get("threshold"), "line": result["line"],
               "sentence": result["sentence"], "pins": result["pins"],
               "pinned_baseline": plan["baseline_selection"].get("pins", []),
               "source": {"source_class": source_class},
               "site_today": result["today"].isoformat(), "look_ahead_closed": result["look_ahead_closed"],
               "recurrence": "not recorded (BL-07); the declared rule alone decides"}
    outcome = {"id": uuid4(), "domain_action_id": plan["domain_action_id"], "plan_id": plan["id"],
               "selection_binding_id": None, "evaluation_request_id": None, "supersedes_outcome_id": None,
               "outcome": result["outcome"], "reasons": list(result["reasons"]), "basis": basis,
               "basis_sha256": reserve_trial.sha(basis), "details": details, "actor_kind": "SYSTEM",
               "actor_id": "service:verification-evaluator", "triggering_job": EVALUATOR_JOB,
               "idempotency_key": f"midday-outcome-{plan['id']}", "recorded_at": now}
    return outcome, metrics


def _price_text(value: Any) -> str | None:
    """MV-1: a private copy of `site_outcomes.mini.price_text` (`actions` never imports `site_outcomes`; a parity
    test pins the two): two decimal places, more only when the stored value has them."""
    try:
        d = Decimal(str(value))
    except InvalidOperation:
        return None
    cents = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{cents:f}" if cents == d else f"{d.normalize():f}"


def mill_value(details: Mapping[str, Any], outcome: str, price: Any) -> dict[str, Any] | None:
    """MV-1 (FUEL-1 §2.2(e)): the estimated-sales value line of a VERIFIED outcome, from the stored shown means and
    the declared productive-use price (`PriceSelection`); None for any other outcome. Pure."""
    if outcome != VERIFIED:
        return None
    b, a = details["baseline"].get("mean_kwh_per_day"), details["later"].get("mean_kwh_per_day")
    nb, nl = len(details["baseline"]["days"]), len(details["later"]["days"])
    if a is None or b is None or Decimal(a) <= Decimal(b) or nb != MIN_DAYS or nl != MIN_DAYS:
        LOG.warning("mill value withheld: VERIFIED outcome with means %s -> %s on %s/%s days", b, a, nb, nl)
        return None
    if price is None or price.state != "PRICED" or price.value is None:
        reason = None if price is None else price.reason
        why = VALUE_UNPRICED_WHY.get(reason, VALUE_UNPRICED_OTHER)
        return {"state": "UNPRICED", "reason": reason or "PRICE_UNREADABLE", "basis": VALUE_BASIS, "per_day": None,
                "before_per_day": None, "after_per_day": None, "currency": None, "price": None,
                "text": VALUE_UNPRICED_TEXT.format(why=why), "cost_text": VALUE_COST_TEXT}
    p = Decimal(str(price.value))
    p_txt = _price_text(price.value)
    per_day = money2((Decimal(a) - Decimal(b)) * p)
    before, after = money2(Decimal(b) * p), money2(Decimal(a) * p)
    return {"state": "PRICED", "reason": None, "basis": VALUE_BASIS, "per_day": per_day, "before_per_day": before,
            "after_per_day": after, "currency": price.currency,
            "price": {"revision_id": price.revision_id, "value": p_txt, "currency": price.currency},
            "text": VALUE_TEXT.format(d=per_day, cur=price.currency, a=a, b=b, p=p_txt, n=nl),
            "cost_text": VALUE_COST_TEXT}


def summary_wire(ctx: Mapping[str, Any], outcomes: Sequence[Mapping[str, Any]],
                 live: Mapping[str, Any] | None, price: Any = None) -> dict[str, Any]:
    """CH9b3-R Q5-Q7: the mill verdict read. A stored outcome is read back, never recomputed; with none, the live
    `assess` result (`live`) gives the not-judged text. Never a cost check or trial hours (null). MV-1: `value` is
    the estimated-sales line of a VERIFIED outcome at `price` (`mill_value`), else null."""
    action, plan = ctx["action"], ctx["plan"]
    head = {"action_id": str(action["id"]), "action_code": action.get("action_code"), "title": action.get("title"),
            "rule_id": MIDDAY, "target": TARGET, "cost_check": None, "trial_hours": None, "value": None}
    if plan is None:
        return {**head, "state": "NO_PLAN", "outcome": None, "reasons": [], "sentence": None, "line": None,
                "not_judged_text": None, "plan": None, "metrics": []}
    plan_part = {"plan_id": str(plan["id"]), "effective_day": plan["basis"]["effective_day"],
                 "baseline_days": list(plan["baseline_selection"]["days"]),
                 "later_candidates": plan["later_selection_rule"]["candidates"]}
    row = {"metric_key": METRIC_KEY, "label": "Midday use", "unit": "kWh a day", "rule": TARGET["rule"]}
    if outcomes:
        o = outcomes[0]
        d = o["details"]
        cmp = next((m for m in o["metrics"] if m["window_name"] == "COMPARISON"), {})
        row.update(before=d["baseline"].get("mean_kwh_per_day"), after=d["later"].get("mean_kwh_per_day"),
                   threshold=d.get("threshold_kwh_per_day"), days_before=len(d["baseline"]["days"]),
                   days_after=len(d["later"]["days"]), state=cmp.get("state", "UNKNOWN"))
        recorded = o["recorded_at"]
        head["value"] = mill_value(d, o["outcome"], price)
        return {**head, "state": o["outcome"], "reasons": list(o["reasons"]), "sentence": d.get("sentence"),
                "line": d.get("line"), "not_judged_text": None,
                "outcome": {"outcome_id": str(o["id"]), "outcome": o["outcome"], "reasons": list(o["reasons"]),
                            "recorded_at": recorded.astimezone(timezone.utc).isoformat()
                            if isinstance(recorded, datetime) else recorded,
                            "source_class": (d.get("source") or {}).get("source_class")},  # WD-1m-R2: wire only
                "plan": {**plan_part, "later_days": list(d["later"]["days"])}, "metrics": [row]}
    live = live or {}
    later_days = [d.isoformat() for d in live.get("later_days", [])]
    row.update(before=live.get("baseline_mean"), after=None, threshold=live.get("threshold"),
               days_before=live.get("days_before_now", len(plan["baseline_selection"]["days"])),
               days_after=len(later_days), state="UNKNOWN")
    return {**head, "state": NOT_JUDGED, "outcome": None, "reasons": [], "sentence": None, "line": None,
            "not_judged_text": live.get("not_judged_text"), "plan": {**plan_part, "later_days": later_days},
            "metrics": [row]}


def plan_wire(plan: Mapping[str, Any]) -> dict[str, Any]:
    def wire(v: Any) -> Any:
        if isinstance(v, datetime):
            return v.astimezone(timezone.utc).isoformat()
        if isinstance(v, UUID):
            return str(v)
        return v
    out = {k: wire(v) for k, v in plan.items() if k not in ("tenant_id", "site_id")}
    out["plan_id"] = out.pop("id")
    out["not_judged_text"] = short_text(out["baseline_selection"])
    return out


FAMILIES: dict[str, Any] = {RESERVE: ReserveTrial(), MIDDAY: MiddayShift()}


def family_of(plan: Mapping[str, Any]) -> Any:
    """The family of a stored plan (its `rule_id`); an unknown family fails closed."""
    try:
        return FAMILIES[plan["rule_id"]]
    except KeyError:
        raise ActionRefused(409, "VERIFICATION_FAMILY_UNSUPPORTED", "Unknown verification family.") from None


# DIESEL-K6b (DIESEL-1-R3m): the fuel family, registered last (`fuel_verification` never imports this module).
from assetops_backend.actions.fuel_verification import FUEL, FuelResidual  # noqa: E402

FAMILIES[FUEL] = FuelResidual()
