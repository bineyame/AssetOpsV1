"""DIESEL-K6b (build sheet DIESEL-1 §9m.4, ruling DIESEL-1-R3m): the `fuel-residual-within-band-1` family, pure.

The verification of a `FUEL_BALANCE` domain Action raised from an unexplained-fuel Finding. No I/O here: the night
choice, the verdict, the plan and outcome rows, and every client literal. `VerificationService.freeze_fuel_plan`,
`evaluate_fuel_plan` and `fuel_summary` (`verification.py`) do the reads and writes.

- The plan's effective time is the linked case's first COMPLETE `occurred_at` (`verification_plan.effective_from`).
- Later candidates: the 14 nights from the first night whose window (18:00 to 12:00 Site-local) starts at or after
  `effective_from`. A night counts (COMPLETE) when its stored fuel check is assessed and every generator slot is
  known; nights are chosen by data quality only, never by result.
- A night passes when `residual_low <= 0 <= residual_high` (exact; no tolerance) and the tank sensor reported all
  night (`gap_minutes == 0`). The first 3 COMPLETE nights decide: all pass, VERIFIED; any fails, INEFFECTIVE; fewer
  than 3 once the 14th night has ended, INCONCLUSIVE; otherwise not judged (nothing stored).
- H1: every state shows `FIXED_LINE`. H2: no money anywhere; `value` and `cost_check` are always null.

This module never imports `verification_families` (no cycle), `financials`, `fuel_cost*` or any price module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from fractions import Fraction
from typing import TYPE_CHECKING, Any, Mapping, Sequence
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from assetops_backend.actions import reserve_trial
from assetops_backend.actions import verification_rules as rules
from assetops_backend.actions.lifecycle import SYSTEM_DEMO
from assetops_backend.actions.ports import ActionRefused
from assetops_backend.chain import refs
from assetops_backend.fuel_balance import finding_text
from assetops_backend.fuel_balance.finding_text import litres1, short_day

if TYPE_CHECKING:  # types only
    from assetops_backend.fuel_balance.model import FuelBalanceWindow

UTC = timezone.utc

FUEL = "fuel-residual-within-band-1"
FUEL_PLAN_VERSION = "fuel-residual-verification-1"
FUEL_LEVER = "fuel-seal-dip-sensor-power@1"          # verification_plan.triggering_fixture (0057 pins it)
FREEZE_COMMAND = "FREEZE_FUEL_VERIFICATION_PLAN"
MIN_NIGHTS, LOOK_NIGHTS = 3, 14
METRIC_KEY = "fuel_residual_night"
EVALUATOR_JOB = "fuel-verification-evaluator"
#: §8.5, verbatim; frozen in the plan; never fitted.
TARGET = {"rule": "every later night: residual_low <= 0 <= residual_high and reporting_gap_minutes == 0",
          "over": "first 3 COMPLETE nights after the change",
          "basis": "owner-reviewed design, fuel-loss-feasibility Part A §3 Verify, chosen 2026-11-07"}
NIGHT_RULE = ("A night counts only when its stored fuel check is assessed (state is not NOT_ASSESSED) and every "
              "generator slot of the night is known (terms.unknown_slots == 0); nights are chosen by data quality "
              "only, never by value.")
BASIS_TEXT = ("SYSTEM_DEMONSTRATION: story-time freeze of a fuel Action's verification plan after its work case is "
              "COMPLETE and linked; no verified human principal exists, so no operator approval is recorded")
TARGET_MET, TARGET_MISS, LATER_SHORT = "TARGET_MET", rules.TARGET_MISS, "LATER_SHORT"
VERIFIED, INEFFECTIVE, INCONCLUSIVE = rules.VERIFIED, rules.INEFFECTIVE, rules.INCONCLUSIVE
NOT_JUDGED, NO_PLAN = "NOT_JUDGED", "NO_PLAN"
BAND, GAP = "BAND", "GAP"

# ---- client literals (all server-composed; the browser formats no number) -------------------------------------
HEADLINE = {"VERIFIED": "Fuel stayed accounted for", "INEFFECTIVE": "Target not met",
            "INCONCLUSIVE": "Could not conclude", "NOT_JUDGED": "Not judged yet",
            "NO_PLAN": "No verification plan yet"}
VERIFIED_TEXT = ("On {n} nights with complete readings after the change, the fuel in the tank matched the generator's "
                 "modelled use and the recorded deliveries within the stated margin, and the tank sensor sent "
                 "readings all night.")
FIXED_LINE = ("This check shows the fuel stayed accounted for after the change; it does not measure how much the "
              "change itself prevented.")                     # H1, §8.2 verbatim; shown in every state
MISS_BAND_TEXT = ("On the night of {date}, after the change, the fuel in the tank did not match the generator's "
                  "modelled use and the recorded deliveries within the stated margin.")
MISS_GAP_TEXT = "On the night of {date}, after the change, the tank sensor did not send readings all night."
LATER_TEXT = "Not judged yet: only {n} of 3 nights with complete readings after the change"
LATER_SHORT_TEXT = ("Only {n} of 3 nights with complete readings after the change in the 14 nights allowed, so no verdict "
                    "is given")
CRITERION_TEXT = ("3 nights with complete readings after the change within the stated margin, with the tank sensor sending "
                  "readings all night")
RULE_TEXT = ("Rule fixed before the check: the first 3 nights with complete readings after the change must each stay within "
             "the stated margin, with the tank sensor sending readings all night.")
ACTIVITY_NOTE = "Completed work is evidence of activity, not resolution."     # v69 :502, verbatim
NIGHT_TEXT = "{date} (6 pm to noon)"
RANGE_TEXT = "{lo} to {hi} L"
SENSOR_ALL = "Readings all night"
SENSOR_GAP = "No readings for {m} min"
RESULT_PASS, RESULT_BAND, RESULT_GAP = "Within the margin", "Outside the margin", "Sensor gap"
BASELINE_ROW = "The night of the finding"
BASELINE_RESULT = "Unexplained fuel found"
NOT_CHECKED = "Not judged yet"
CARDS = (("Nights with complete readings after the change", "{n} of 3", "Chosen by data quality, never by result"),
         ("Fuel accounted for", "{k} of {n} nights", "Within the stated margin"),
         ("Tank sensor", "Readings all night on {g} of {n} nights", "A gap is more than 60 minutes without a reading"),
         ("Final outcome", "{headline}", "Decided by the rule fixed before the check"))
LITERALS = (*HEADLINE.values(), VERIFIED_TEXT, FIXED_LINE, MISS_BAND_TEXT, MISS_GAP_TEXT, LATER_TEXT, LATER_SHORT_TEXT,
            CRITERION_TEXT, RULE_TEXT, ACTIVITY_NOTE, NIGHT_TEXT, RANGE_TEXT, SENSOR_ALL, SENSOR_GAP, RESULT_PASS,
            RESULT_BAND, RESULT_GAP, BASELINE_ROW, BASELINE_RESULT, NOT_CHECKED, *(s for card in CARDS for s in card))


@dataclass(frozen=True)
class FuelResidual:
    """`fuel-residual-within-band-1`: the plan of a `FUEL_BALANCE` domain Action from an unexplained-fuel Finding."""

    rule_id: str = FUEL
    plan_version: str = FUEL_PLAN_VERSION
    owner: str = "domain_action"


# ---- nights -----------------------------------------------------------------------------------------------------

def night_bounds(night: date, tz: str) -> tuple[datetime, datetime]:
    """Night `d` = `[local(d, 18:00), local(d + 1, 12:00))` in UTC (fold 0), K3's window."""
    z = ZoneInfo(tz)
    return (datetime.combine(night, time(18), z).astimezone(UTC),
            datetime.combine(night + timedelta(days=1), time(12), z).astimezone(UTC))


def later_nights(effective_from: datetime, tz: str) -> list[date]:
    """The 14 candidate nights: from the first whose window starts at or after `effective_from`."""
    d0 = effective_from.astimezone(ZoneInfo(tz)).date()
    if night_bounds(d0, tz)[0] < effective_from:
        d0 += timedelta(days=1)
    return [d0 + timedelta(days=i) for i in range(LOOK_NIGHTS)]


def complete(w: Any) -> bool:
    return w is not None and w.state != "NOT_ASSESSED" and int(w.terms["unknown_slots"]) == 0


def passes(w: Any) -> tuple[bool, str | None]:
    if not (w.residual_low <= 0 <= w.residual_high):
        return False, BAND
    if w.gap_minutes != 0:
        return False, GAP
    return True, None


def _candidates(plan: Mapping[str, Any]) -> list[date]:
    lo = date.fromisoformat(plan["later_selection_rule"]["candidates"]["from"])
    return [lo + timedelta(days=i) for i in range(LOOK_NIGHTS)]


def _miss_text(night: date, reason: str) -> str:
    return (MISS_BAND_TEXT if reason == BAND else MISS_GAP_TEXT).format(date=short_day(night))


def assess(plan: Mapping[str, Any], windows_by_date: Mapping[date, Any], now: datetime) -> dict[str, Any]:
    """The verdict over the latest revision per candidate night as known at `now` (pure)."""
    cands = _candidates(plan)
    tz = plan["basis"]["timezone"]
    chosen = [windows_by_date[d] for d in cands if complete(windows_by_date.get(d))][:MIN_NIGHTS]
    closed = night_bounds(cands[-1], tz)[1] <= now
    judged = [(w, *passes(w)) for w in chosen]
    first = next(((w, reason) for w, ok, reason in judged if not ok), None)
    out = {"candidates": cands, "chosen": chosen, "judged": judged, "look_ahead_closed": closed,
           "first_fail": None if first is None else first[0].night_date, "decided": False,
           "outcome": None, "reasons": [], "sentence": None, "not_judged_text": None}
    if len(chosen) == MIN_NIGHTS or closed:
        out["decided"] = True
        if first is not None:
            out.update(outcome=INEFFECTIVE, reasons=[TARGET_MISS], sentence=_miss_text(first[0].night_date, first[1]))
        elif len(chosen) == MIN_NIGHTS:
            out.update(outcome=VERIFIED, reasons=[TARGET_MET], sentence=VERIFIED_TEXT.format(n=MIN_NIGHTS))
        else:
            out.update(outcome=INCONCLUSIVE, reasons=[LATER_SHORT], sentence=LATER_SHORT_TEXT.format(n=len(chosen)))
    else:
        out["not_judged_text"] = LATER_TEXT.format(n=len(chosen))
    return out


def used_dates(plan: Mapping[str, Any], result: Mapping[str, Any]) -> list[str]:
    """WD-1m-R2: the baseline night and each chosen night, each with its next day (the window spans two dates)."""
    nights = [date.fromisoformat(plan["baseline_selection"]["night_date"])] + [w.night_date for w in result["chosen"]]
    return sorted({d.isoformat() for n in nights for d in (n, n + timedelta(days=1))})


# ---- plan ---------------------------------------------------------------------------------------------------------

def plan_row(domain_action_id: UUID, action: Mapping[str, Any], applied: Mapping[str, Any], baseline: Any,
             now: datetime) -> dict[str, Any]:
    """The plan row of a fuel Action (§9m.4 Freeze step 9). The caller has checked steps 1-8."""
    tz = action["timezone"]
    effective = applied["occurred_at"].astimezone(UTC)
    later = later_nights(effective, tz)
    later_start = night_bounds(later[0], tz)[0]
    selection = {"state": "COMPLETE", "night_date": baseline.night_date.isoformat(), "window_id": str(baseline.id),
                 "window_revision": baseline.revision, "input_sha256": baseline.input_sha256,
                 "state_found": baseline.state, "residual_low": rules.fmt(baseline.residual_low),
                 "residual_high": rules.fmt(baseline.residual_high), "gap_minutes": baseline.gap_minutes}
    content = {
        "plan_version": FUEL_PLAN_VERSION, "rule_id": FUEL, "domain_action_id": str(domain_action_id),
        "origin_finding_revision_id": str(action["origin_finding_revision_id"]),
        "applied_work_event_id": str(applied["id"]), "effective_from": effective.isoformat(),
        "baseline_start": baseline.window_start.isoformat(), "baseline_end": baseline.window_end.isoformat(),
        "later_start": later_start.isoformat(), "baseline_selection": selection, "baseline_evidence_ids": [],
        "basis": {"timezone": tz, "night_rule": NIGHT_RULE,
                  "applied": {"work_event_id": str(applied["id"]), "case_id": str(applied["case_id"]),
                              "occurred_at": effective.isoformat()},
                  "origin": {"finding_id": str(action["origin_finding_id"]),
                             "revision_id": str(action["origin_finding_revision_id"])},
                  "tank_asset_id": str(baseline.tank_asset_id), "windows_known_at": now.isoformat()},
        "target": TARGET, "guardrails": {}, "bands": {},
        "coverage": {"min_nights": MIN_NIGHTS, "look_ahead_nights": LOOK_NIGHTS},
        "later_selection_rule": {
            "rule": ("the first 3 COMPLETE nights whose window starts at or after effective_from, at most 14 nights "
                     "ahead, chosen by grade only at evaluation"),
            "min_nights": MIN_NIGHTS, "candidates": {"from": later[0].isoformat(), "to": later[-1].isoformat()}},
    }
    payload = {"command": FREEZE_COMMAND, "domain_action_id": str(domain_action_id)}
    return {**content, "id": uuid4(), "domain_action_id": domain_action_id, "origin_opportunity_revision_id": None,
            "origin_finding_revision_id": action["origin_finding_revision_id"], "applied_work_event_id": applied["id"],
            "effective_from": effective, "baseline_start": baseline.window_start, "baseline_end": baseline.window_end,
            "later_start": later_start, "later_end": later_start + timedelta(days=LOOK_NIGHTS),
            "plan_sha256": reserve_trial.sha(content), "actor_kind": SYSTEM_DEMO.actor_kind,
            "actor_id": SYSTEM_DEMO.actor_id, "source_channel": SYSTEM_DEMO.source_channel,
            "authorization_basis": BASIS_TEXT, "triggering_service": SYSTEM_DEMO.triggering_service,
            "triggering_fixture": FUEL_LEVER, "idempotency_key": f"fuel-plan-{domain_action_id}",
            "payload": payload, "payload_sha256": reserve_trial.sha(payload), "recorded_at": now}


def plan_wire(plan: Mapping[str, Any]) -> dict[str, Any]:
    def wire(v: Any) -> Any:
        if isinstance(v, datetime):
            return v.astimezone(UTC).isoformat()
        if isinstance(v, UUID):
            return str(v)
        return v
    out = {k: wire(v) for k, v in plan.items() if k not in ("tenant_id", "site_id")}
    out["plan_id"] = out.pop("id")
    return out


# ---- outcome ------------------------------------------------------------------------------------------------------

def _pin(w: Any) -> dict[str, Any]:
    return {"night_date": w.night_date.isoformat(), "window_id": str(w.id), "revision": w.revision,
            "input_sha256": w.input_sha256}


def _range(low: Fraction, high: Fraction) -> str:
    return RANGE_TEXT.format(lo=litres1(low), hi=litres1(high))


def outcome_rows(plan: Mapping[str, Any], result: Mapping[str, Any], now: datetime, source_class: str | None = None,
                 ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """The outcome row and its BASELINE / LATER / COMPARISON metric rows of a decided `assess` result. WD-1m-R2: the
    example-data class of the used nights is stored in `details.source` (never in `basis`)."""
    base = plan["baseline_selection"]
    chosen = [w.night_date.isoformat() for w in result["chosen"]]
    n = len(chosen)
    low, high = rules.parse_exact(base["residual_low"]), rules.parse_exact(base["residual_high"])
    comparison = {VERIFIED: "PASS", INEFFECTIVE: "FAIL"}.get(result["outcome"], "UNKNOWN")
    metrics = [rules._metric(METRIC_KEY, "BASELINE", "PASS", value=_range(low, high), unit="L",
                             reason=f"night {base['night_date']}: UNEXPLAINED"),
               rules._metric(METRIC_KEY, "LATER", "PASS" if n == MIN_NIGHTS else "UNKNOWN", value=f"{n} of 3",
                             unit="L", reason=", ".join(chosen)),
               rules._metric(METRIC_KEY, "COMPARISON", comparison, unit="L", reason=TARGET["rule"])]
    basis = {"plan_id": str(plan["id"]), "plan_sha256": plan["plan_sha256"], "rule_id": FUEL,
             "plan_version": FUEL_PLAN_VERSION, "target": TARGET, "windows_known_at": now.isoformat()}
    later = [{**_pin(w), "state": w.state, "residual_low": rules.fmt(w.residual_low),
              "residual_high": rules.fmt(w.residual_high), "gap_minutes": w.gap_minutes, "passes": ok,
              "fail_reason": reason} for w, ok, reason in result["judged"]]
    first = result["first_fail"]
    details = {"baseline": {"night_date": base["night_date"], "window_id": base["window_id"],
                            "revision": base["window_revision"], "input_sha256": base["input_sha256"]},
               "later": later, "first_fail": None if first is None else first.isoformat(),
               "sentence": result["sentence"], "source": {"source_class": source_class},
               "look_ahead_closed": result["look_ahead_closed"]}
    outcome = {"id": uuid4(), "domain_action_id": plan["domain_action_id"], "plan_id": plan["id"],
               "selection_binding_id": None, "evaluation_request_id": None, "supersedes_outcome_id": None,
               "outcome": result["outcome"], "reasons": list(result["reasons"]), "basis": basis,
               "basis_sha256": reserve_trial.sha(basis), "details": details, "actor_kind": "SYSTEM",
               "actor_id": "service:verification-evaluator", "triggering_job": EVALUATOR_JOB,
               "idempotency_key": f"fuel-outcome-{plan['id']}", "recorded_at": now}
    return outcome, metrics


# ---- the read wire ------------------------------------------------------------------------------------------------

def _sensor(gap: int) -> str:
    return SENSOR_ALL if gap == 0 else SENSOR_GAP.format(m=gap)


def _result_text(ok: bool, reason: str | None) -> str:
    return RESULT_PASS if ok else RESULT_BAND if reason == BAND else RESULT_GAP


def _later_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [{"role": "LATER", "label": NIGHT_TEXT.format(date=short_day(date.fromisoformat(r["night_date"]))),
             "range_text": _range(rules.parse_exact(r["residual_low"]), rules.parse_exact(r["residual_high"])),
             "sensor_text": _sensor(r["gap_minutes"]), "result_text": _result_text(r["passes"], r["fail_reason"]),
             "passes": r["passes"], "window_id": r["window_id"], "revision": r["revision"]} for r in rows]


def _live_rows(result: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [{**_pin(w), "residual_low": rules.fmt(w.residual_low), "residual_high": rules.fmt(w.residual_high),
             "gap_minutes": w.gap_minutes, "passes": ok, "fail_reason": reason} for w, ok, reason in result["judged"]]


def cards(state: str, rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    n = len(rows)
    k = sum(1 for r in rows if r["passes"])
    g = sum(1 for r in rows if r["gap_minutes"] == 0)
    values = (CARDS[0][1].format(n=n),
              NOT_CHECKED if n == 0 else CARDS[1][1].format(k=k, n=n),
              NOT_CHECKED if n == 0 else CARDS[2][1].format(g=g, n=n),
              CARDS[3][1].format(headline=HEADLINE[state]))
    return [{"label": label, "value": value, "note": note} for (label, _, note), value in zip(CARDS, values)]


def _local_text(at: datetime, tz: str) -> str:
    local = at.astimezone(ZoneInfo(tz))
    return f"{local.day} {local:%b} {local:%H:%M}"


def fuel_summary_wire(ctx: Mapping[str, Any], plan: Mapping[str, Any] | None,
                      outcomes: Sequence[Mapping[str, Any]], live: Mapping[str, Any] | None, origin: Any,
                      baseline: Any, site_code: str, site_visit: str | None = None) -> dict[str, Any]:
    """The fuel verdict read (§9m.4 Summary). A stored outcome is read back, never recomputed; with none, the live
    `assess` result gives the not-judged text. `origin` = the Action's origin pair, `baseline` = the night window the
    origin revision cites (None when unreadable). `value` and `cost_check` are always null (H2)."""
    action, applied = ctx["action"], ctx["applied"]
    tz = action["timezone"]
    fid, rev = str(origin["finding_id"]), str(origin["revision_id"])
    ref = refs.fuel_finding_ref(site_code, fid, rev)
    origin_wire = {"finding_id": fid, "revision_id": rev, "title": finding_text.TITLE,
                   "night_text": None if baseline is None else NIGHT_TEXT.format(date=short_day(baseline.night_date)),
                   "ref": ref, "href": refs.href_for(ref)}
    activity = None
    if applied is not None:
        case = refs.case_ref(site_code, str(applied["case_id"]))
        activity = {"case_code": applied.get("public_code"), "case_ref": case, "case_href": refs.href_for(case),
                    "completed_text": _local_text(applied["occurred_at"], tz), "site_visit_text": site_visit,
                    "note": ACTIVITY_NOTE}
    nights: list[dict[str, Any]] = []
    if baseline is not None:
        nights.append({"role": "BASELINE", "label": BASELINE_ROW, "range_text": _range(baseline.residual_low,
                                                                                      baseline.residual_high),
                       "sensor_text": _sensor(baseline.gap_minutes), "result_text": BASELINE_RESULT, "passes": None,
                       "window_id": str(baseline.id), "revision": baseline.revision})
    head = {"action_id": str(action["id"]), "action_code": action.get("action_code"), "title": action.get("title"),
            "owner_label": action.get("owner_label"), "rule_id": FUEL, "fixed_line": FIXED_LINE,
            "criterion_text": CRITERION_TEXT, "rule_text": RULE_TEXT, "origin": origin_wire, "activity": activity,
            "value": None, "cost_check": None}
    if plan is None:
        return {**head, "state": NO_PLAN, "headline": HEADLINE[NO_PLAN], "sentence": None, "not_judged_text": None,
                "cards": cards(NO_PLAN, []), "nights": nights, "effective_from": None, "plan": None, "outcome": None}
    plan_part = {"plan_id": str(plan["id"]), "later_candidates": dict(plan["later_selection_rule"]["candidates"])}
    effective = plan["effective_from"].astimezone(UTC).isoformat()
    if outcomes:
        o = outcomes[0]
        d = o["details"]
        recorded = o["recorded_at"]
        state = o["outcome"]
        return {**head, "state": state, "headline": HEADLINE[state], "sentence": d.get("sentence"),
                "not_judged_text": None, "cards": cards(state, d["later"]), "nights": nights + _later_rows(d["later"]),
                "effective_from": effective, "plan": plan_part,
                "outcome": {"outcome_id": str(o["id"]), "outcome": state, "reasons": list(o["reasons"]),
                            "recorded_at": recorded.astimezone(UTC).isoformat()
                            if isinstance(recorded, datetime) else recorded,
                            "source_class": (d.get("source") or {}).get("source_class")}}
    rows = _live_rows(live) if live else []
    return {**head, "state": NOT_JUDGED, "headline": HEADLINE[NOT_JUDGED], "sentence": None,
            "not_judged_text": None if not live else live.get("not_judged_text"), "cards": cards(NOT_JUDGED, rows),
            "nights": nights + _later_rows(rows), "effective_from": effective, "plan": plan_part, "outcome": None}


def refused_family() -> ActionRefused:
    return ActionRefused(409, "VERIFICATION_FAMILY_UNSUPPORTED",
                         "Only an Action raised from an unexplained-fuel Finding has a fuel verification plan.")
