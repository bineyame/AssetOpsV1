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

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Mapping, Sequence
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from assetops_backend.actions import reserve_trial
from assetops_backend.actions import verification_rules as rules
from assetops_backend.actions.lifecycle import SYSTEM_DEMO
from assetops_backend.actions.ports import ActionRefused
from assetops_backend.chain.grading import COMPLETE, NO_DATA
from assetops_backend.chain.reader import _day_grade

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
SHORT_TEXT = "Not judged yet: only {n} of 3 fully checked days before the change"
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
