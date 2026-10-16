"""S6-02a: freeze a `reserve-trial-verification-1` plan, bind the later selection, and read plan and evidence.

`D-2026-10-16-s6-verification` and `D-2026-10-16-s602-questions` (`.agent/architect-A-S6-verification-answers.md`,
`.agent/architect-S6-02-answers.md`). A server-authorized SYSTEM demonstration command (capability command
`VERIFY`) may freeze a plan or append the later selection binding; it never supplies a metric, verdict or event.
Arithmetic lives in `verification_rules` (exact, pure); every row is written by the ninth writer
(`adapters/postgres_action_store.py`) under the battery-scoped trial lock.

Phase 1 reads report the verification *state* `PENDING` (no outcome exists yet; the evaluator is phase 2). Every
response labels the subject a simulated/authored policy trial: no causal or savings claim.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from fractions import Fraction
from typing import Any, Callable
from uuid import UUID, uuid4

from assetops_backend.actions import reserve_trial
from assetops_backend.actions import verification_rules as rules
from assetops_backend.actions.lifecycle import APPLIED, SYSTEM_DEMO
from assetops_backend.actions.ports import ActionRefused
from assetops_backend.analytics.assessment_inputs import BRACKET
from assetops_backend.sites.binding_roles import VERIFICATION_POINT_ROLES, VERIFICATION_POWER_ROLES

VERIFY = "VERIFY"
FREEZE_COMMAND = "FREEZE_VERIFICATION_PLAN"
BIND_COMMAND = "BIND_LATER_SELECTION"
DISPATCH_MODEL_PREFIX = "dispatch-3"
ROLES = tuple(VERIFICATION_POWER_ROLES) + tuple(VERIFICATION_POINT_ROLES)
CRITICAL_ROLES = ("critical_load_requested_power", "critical_load_delivered_power")
LABEL = ("Simulated or authored policy trial verification. It compares two observed windows under a frozen plan; "
         "it makes no causal or savings claim, and a later RESOLVED can be withdrawn.")
EPSILON = timedelta(microseconds=1)


def _wire(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Fraction):
        return rules.fmt(value)
    if isinstance(value, dict):
        return {str(k): _wire(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_wire(v) for v in value]
    if hasattr(value, "is_finite"):  # Decimal
        return reserve_trial.text_of(value)
    return value


def _day(instant: datetime) -> datetime:
    return datetime(instant.year, instant.month, instant.day, tzinfo=timezone.utc)


def required_days(start: datetime) -> list[datetime]:
    """The UTC days whose selected `dispatch-3` revisions can hold time inside `[start, start+60m)`: the window's
    day(s), plus the previous day when an interval starting then could reach the window (S3's 6 h read bracket:
    an interval belongs to the day of its first ON, and its segments may run up to the bracket past midnight)."""
    days = [datetime(d.year, d.month, d.day, tzinfo=timezone.utc) for d in rules.target_days(start)]
    if start - BRACKET >= _day(start):
        days = [d for d in days if d >= _day(start)]
    return days


def _intervals(selections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"assessment_revision_id": str(i["assessment_revision_id"]), "day": s["day"], "result": i["result"]}
            for s in selections if s.get("selected") for i in s["intervals"]]


def _selection_pin(selections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"day": s["day"], "selection_seq": s["selection_seq"], "run_id": str(s["run_id"]),
             "model_version": s["model_version"], "cohort_status": s["cohort_status"],
             "cohort_sha256": s["cohort_sha256"], "input_sha256": s["input_sha256"],
             "configuration_sha256": s["configuration_sha256"],
             "window_revision_ids": [str(i) for i in s["window_revision_ids"]],
             "interval_revision_ids": sorted(str(i["assessment_revision_id"]) for i in s["intervals"])}
            for s in selections]


def _bindings(rows: list[dict[str, Any]]) -> dict[str, Any]:
    loads = sorted({str(r["asset_id"]) for r in rows if r["role"] == "feeder_demand" and r["asset_id"]})
    critical = {role: sorted({str(r["asset_id"]) for r in rows if r["role"] == role and r["asset_id"]})
                for role in CRITICAL_ROLES}
    return {"role_sets": sorted({r["role_set"] for r in rows}),
            "binding_set_revision_ids": sorted({str(r["binding_set_revision_id"]) for r in rows}),
            "roles": sorted({r["role"] for r in rows}), "load_asset_ids": loads,
            "critical_load_asset_ids": critical}


def _critical_asset(bindings: dict[str, Any]) -> str | None:
    ids = {a for role in CRITICAL_ROLES for a in bindings["critical_load_asset_ids"].get(role, [])}
    return next(iter(ids)) if len(ids) == 1 and all(bindings["critical_load_asset_ids"].get(r) for r in CRITICAL_ROLES) \
        else None


class VerificationService:
    def __init__(self, actions: Any, clock: Callable[[], datetime] | None = None) -> None:
        self.actions = actions  # ActionService: its store, capability check and clock
        self.store = actions.store
        self.clock = clock or actions.clock

    # ---- freeze ------------------------------------------------------------------------------------------

    def freeze(self, tenant_id: UUID, site_id: UUID, site_code: str, action_id: UUID,
               command: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        granted, _ = self.actions.authorize_action(tenant_id, site_id, site_code, VERIFY, action_id)
        b0, l0 = command["baseline_start"], command["later_start"]
        supersedes = command.get("supersedes_plan_id")
        payload = {"command": FREEZE_COMMAND, "action_id": str(action_id), "baseline_start": b0.isoformat(),
                   "later_start": l0.isoformat(), "supersedes_plan_id": None if supersedes is None else str(supersedes),
                   "idempotency_key": command["idempotency_key"]}
        digest = reserve_trial.sha(payload)
        for plan in self.store.plans(tenant_id, site_id, action_id):
            if plan["idempotency_key"] == command["idempotency_key"]:
                return self._replay(plan, digest, site_code)
        now = self.clock()
        windows = {"baseline": (b0, b0 + rules.WINDOW), "later": (l0, l0 + rules.WINDOW)}
        for name, (lo, hi) in windows.items():
            problem = rules.window_problem(lo, hi)
            if problem:
                raise ActionRefused(422, "VERIFICATION_WINDOW_INVALID", f"The {name} window is invalid: {problem}",
                                    window=name)
        if (l0 - b0) % timedelta(days=1) != timedelta(0):
            raise ActionRefused(422, "VERIFICATION_WINDOW_CLOCK_MISMATCH",
                                "Both windows must cover the same UTC clock hour.")
        days = required_days(b0)
        ctx = self.store.verification_context(
            tenant_id, site_id, action_id, probes=[b0, b0 + rules.WINDOW - EPSILON, l0, l0 + rules.WINDOW - EPSILON],
            windows=windows, days=days, known_at=now)
        if ctx is None:
            raise ActionRefused(404, "ACTION_NOT_FOUND", "No such Action for this Site.")
        action, change = ctx["action"], ctx["change"]
        applied = [e for e in ctx["events"] if e["kind"] == APPLIED]
        if not applied or change is None:
            raise ActionRefused(409, "VERIFICATION_ACTION_NOT_APPLIED",
                                "A verification plan needs an APPLIED Action with a committed change artifact.")
        effective = change["effective_from"]
        if not (b0 + rules.WINDOW <= effective <= l0):
            raise ActionRefused(422, "VERIFICATION_WINDOW_STRADDLES_CHANGE",
                                "The baseline must end before the change's effective_from and the later window "
                                "must start at or after it.", effective_from=effective.isoformat())
        covering = {p.isoformat(): [str(i) for i in ids] for p, ids in ctx["covering"].items()}
        cov = list(ctx["covering"].values())
        old = cov[0][0] if len(cov[0]) == 1 and cov[0] == cov[1] else None
        new = cov[2][0] if len(cov[2]) == 1 and cov[2] == cov[3] else None
        if old is None or new is None or old == new or str(new) != str(change["new_foundation_revision_id"]):
            raise ActionRefused(409, "VERIFICATION_FOUNDATION_NOT_COMPARABLE",
                                "Each window must lie wholly under one covering FoundationRevision: the old one "
                                "for the baseline and the applied change's new one for the later window, with no "
                                "policy change inside either.", covering=covering,
                                new_foundation_revision_id=str(change["new_foundation_revision_id"]))
        unselected = [s["day"] for s in ctx["days"] if not s["selected"]]
        if unselected:
            raise ActionRefused(409, "VERIFICATION_BASELINE_NOT_SELECTED",
                                "Every UTC day covering the baseline needs a final S3 dispatch selection.",
                                days=unselected)
        models = {s["model_version"] for s in ctx["days"]}
        if len(models) != 1 or not next(iter(models)).startswith(DISPATCH_MODEL_PREFIX):
            raise ActionRefused(409, "VERIFICATION_MODEL_NOT_COMPARABLE",
                                "The baseline's selected days must share one dispatch-3 model version.",
                                model_versions=sorted(models))
        target = rules.target_window(b0, _intervals(ctx["days"]))
        if target["state"] != "KNOWN" or not target["candidate_seconds"]:
            raise ActionRefused(422, "VERIFICATION_BASELINE_UNSUPPORTED",
                                "The baseline needs positive supported Candidate seconds.", target=_wire(target))
        base_bindings, later_bindings = _bindings(ctx["bindings"]["baseline"]), _bindings(ctx["bindings"]["later"])
        readings = self.store.window_readings(tenant_id, site_id, b0, b0 + rules.WINDOW, list(ROLES), now)
        plan_id = uuid4()
        content = {
            "plan_version": rules.PLAN_VERSION, "action_id": str(action_id),
            "origin_finding_revision_id": str(action["origin_finding_revision_id"]),
            "applied_event_id": str(applied[0]["id"]), "change_id": str(change["id"]),
            "old_foundation_revision_id": str(old), "new_foundation_revision_id": str(new),
            "battery_asset_id": str(action["asset_id"]), "field": action["field"], "rule_id": action["rule_id"],
            "effective_from": effective.isoformat(), "baseline_start": b0.isoformat(), "later_start": l0.isoformat(),
            "baseline_candidate_seconds": target["candidate_seconds"],
            "baseline_selection": {"days": _selection_pin(ctx["days"]), "target": _wire(target)},
            "baseline_evidence_ids": sorted(str(r["id"]) for r in readings),
            "basis": {
                "analytic_id": "dispatch", "model_version": next(iter(models)),
                "cohort_rule": "S3 run cohort of each selected UTC day, matched exactly across windows",
                "baseline_cohort": [{"day": s["day"], "status": s["cohort_status"], "sha256": s["cohort_sha256"]}
                                    for s in ctx["days"]],
                "clock_basis": "UTC; accepted public evidence with S3 clock/cohort attestation",
                "baseline_bindings": base_bindings, "later_bindings_at_freeze": later_bindings,
                "load_asset_ids": base_bindings["load_asset_ids"],
                "critical_load_asset_id": _critical_asset(base_bindings),
                "source_rule": ("Resolve S4-05 source per window, never their union; a positive verdict needs one "
                                "coherent REGISTERED_SIMULATION or AUTHORED_DEMONSTRATION per window, the same class "
                                "and registered scenario/profile lineage, distinct run identity digests and intact "
                                "links."),
                "later_cutoff": {"accepted_evidence_in_later_window": ctx["accepted_in_window"]["later"],
                                 "rule": "No later-window report accepted and no later run begun at freeze."}},
            "target": {"metric": "candidate_avoidable_seconds", "classification": "CANDIDATE_AVOIDABLE",
                       "rule": "4 * later_seconds <= 3 * baseline_seconds", "ratio": [3, 4],
                       "inconclusive_when": ["INDETERMINATE time in window", "OPEN_BOUND interval time in window"]},
            "guardrails": {
                "unserved_critical_energy": {"rule": "later_kwh <= baseline_kwh", "unit": "kWh",
                                             "from": "requested minus delivered critical-load power"},
                "below_reserve_seconds": {"rule": "later == 0 and later <= baseline", "unit": "s",
                                          "basis": rules.GUARDRAIL_BASIS,
                                          "label": "Five-minute sampled guardrail, not continuous physical SOC proof",
                                          "seconds_per_breached_slot": 300},
                "terminal_soc": {"rule": "later_terminal_soc >= baseline_terminal_soc", "unit": "%",
                                 "after": "initial SOC comparability band"}},
            "bands": rules.bands_payload(),
            "coverage": {"slots_per_window": rules.SLOTS_PER_WINDOW, "slot_minutes": 5,
                         "power_roles": list(VERIFICATION_POWER_ROLES), "point_roles": list(VERIFICATION_POINT_ROLES),
                         "power_rule": ("one accepted INTERVAL_MEAN value covering the whole slot, or accepted "
                                        "non-overlapping subintervals exactly partitioning it; kWh = kW * covered "
                                        "seconds / 3600; point readings establish no energy"),
                         "soc_rule": "accepted sample at every slot start and at the window end; no carrying",
                         "reserve_rule": "reserve effective at each slot start; a change inside a slot is unassessable",
                         "missing": "any missing slot or role makes the result INCONCLUSIVE"},
            "later_selection_rule": {"rule": ("latest DEFAULT dispatch-3 selection of each required UTC day (the "
                                              "window's day, plus the previous day when the 6 h bracket reaches the "
                                              "window), appended as an immutable binding before evaluation"),
                                     "required_days": [d.date().isoformat() for d in required_days(l0)]},
        }
        plan = {**content, "id": plan_id, "supersedes_plan_id": supersedes, "effective_from": effective,
                "baseline_start": b0, "baseline_end": b0 + rules.WINDOW, "later_start": l0,
                "later_end": l0 + rules.WINDOW, "plan_sha256": reserve_trial.sha(content),
                "actor_kind": SYSTEM_DEMO.actor_kind, "actor_id": SYSTEM_DEMO.actor_id,
                "source_channel": SYSTEM_DEMO.source_channel,
                "authorization_basis": SYSTEM_DEMO.basis(granted.fixture_id or "", VERIFY),
                "triggering_service": SYSTEM_DEMO.triggering_service, "triggering_fixture": granted.fixture_id or "",
                "idempotency_key": command["idempotency_key"], "payload": payload, "payload_sha256": digest,
                "recorded_at": now}

        def check(c: Any, plans: list[dict[str, Any]]) -> None:
            superseded = {str(p["supersedes_plan_id"]) for p in plans if p["supersedes_plan_id"]}
            heads = [p for p in plans if str(p["id"]) not in superseded]
            if not plans and supersedes is not None:
                raise ActionRefused(409, "VERIFICATION_PLAN_NOT_HEAD", "There is no plan to replace.")
            if plans and (supersedes is None or str(supersedes) != str(heads[-1]["id"])):
                raise ActionRefused(409, "VERIFICATION_PLAN_NOT_HEAD",
                                    "A plan is already frozen; a replacement must name the current plan in "
                                    "supersedes_plan_id.", current_plan_id=str(heads[-1]["id"]))
            if plans and heads[-1]["id"] in ctx["outcome_plan_ids"]:
                raise ActionRefused(409, "VERIFICATION_PLAN_EVALUATED",
                                    "The current plan already has an outcome; it is no longer pending.")
            later = self.store.accepted_count(c, tenant_id, site_id, l0, l0 + rules.WINDOW, now)
            if later:
                raise ActionRefused(409, "VERIFICATION_LATER_WINDOW_STARTED",
                                    "A later-window report has already been accepted (or the later run has begun); "
                                    "freeze a new plan with a new later window.", accepted_evidence_count=later)

        row, replayed = self.store.freeze_plan(tenant_id, site_id, plan, check=check)
        if replayed:
            return self._replay(row, digest, site_code)
        return 201, {"label": LABEL, "replayed": False, "plan": self._plan_wire(row, site_code)}

    def _replay(self, plan: dict[str, Any], digest: str, site_code: str) -> tuple[int, dict[str, Any]]:
        if plan["payload_sha256"] != digest:
            raise ActionRefused(409, "VERIFICATION_IDEMPOTENCY_CONFLICT",
                                "This idempotency key already froze a different plan command.",
                                plan_id=str(plan["id"]))
        return 200, {"label": LABEL, "replayed": True, "plan": self._plan_wire(plan, site_code)}

    @staticmethod
    def _plan_wire(plan: dict[str, Any], site_code: str) -> dict[str, Any]:
        out = {k: _wire(v) for k, v in plan.items() if k not in ("tenant_id", "site_id")}
        out["plan_id"] = out.pop("id")
        out["actor"] = {"kind": out.pop("actor_kind"), "id": out.pop("actor_id"), "label": SYSTEM_DEMO.label,
                        "source_channel": out.pop("source_channel"),
                        "authorization_basis": out.pop("authorization_basis"),
                        "triggering": {"service": out.pop("triggering_service"), "job": None,
                                       "command": VERIFY, "fixture": out.pop("triggering_fixture")}}
        base = f"/api/sites/{site_code}/actions/{out['action_id']}/verification"
        out["links"] = {"plan": f"{base}/plan?plan_id={out['plan_id']}",
                        "evidence": f"{base}/evidence?plan_id={out['plan_id']}"}
        return out

    # ---- later selection binding ----------------------------------------------------------------------------

    def bind_later_selection(self, tenant_id: UUID, site_id: UUID, site_code: str, action_id: UUID, plan_id: UUID,
                             command: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        granted, _ = self.actions.authorize_action(tenant_id, site_id, site_code, VERIFY, action_id)
        plan = self._plan(tenant_id, site_id, action_id, plan_id)
        now = self.clock()
        selections = self.store.day_selections(tenant_id, site_id, required_days(plan["later_start"]), now)
        unselected = [s["day"] for s in selections if not s["selected"]]
        if unselected:
            raise ActionRefused(409, "VERIFICATION_LATER_NOT_SELECTED",
                                "Every UTC day covering the later window needs a final S3 dispatch selection.",
                                days=unselected)
        target = rules.target_window(plan["later_start"], _intervals(selections))
        selection = {"days": _selection_pin(selections), "target": _wire(target)}
        binding = {"id": uuid4(), "window_name": "LATER", "selection": selection,
                   "selection_sha256": reserve_trial.sha(selection), "actor_kind": SYSTEM_DEMO.actor_kind,
                   "actor_id": SYSTEM_DEMO.actor_id, "triggering_service": SYSTEM_DEMO.triggering_service,
                   "triggering_job": None, "triggering_fixture": granted.fixture_id or "", "recorded_at": now}
        row, replayed = self.store.append_selection_binding(tenant_id, site_id, plan, binding)
        return (200 if replayed else 201), {"label": LABEL, "replayed": replayed, "binding": _wire(
            {k: v for k, v in row.items() if k not in ("tenant_id", "site_id")})}

    # ---- reads ------------------------------------------------------------------------------------------------

    def _plan(self, tenant_id: UUID, site_id: UUID, action_id: UUID, plan_id: UUID) -> dict[str, Any]:
        for plan in self.store.plans(tenant_id, site_id, action_id):
            if plan["id"] == plan_id:
                return plan
        raise ActionRefused(404, "VERIFICATION_PLAN_NOT_FOUND", "No such verification plan for this Action.")

    def _select(self, tenant_id: UUID, site_id: UUID, action_id: UUID, plan_id: UUID | None,
                recorded_at: datetime | None) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        if self.store.action(tenant_id, site_id, action_id) is None:
            raise ActionRefused(404, "ACTION_NOT_FOUND", "No such Action for this Site.")
        if plan_id is not None and recorded_at is not None:
            raise ActionRefused(422, "VERIFICATION_SELECTOR_CONFLICT",
                                "Choose one selector: plan_id or recorded_at.")
        plans = self.store.plans(tenant_id, site_id, action_id)
        if plan_id is not None:
            chosen = next((p for p in plans if p["id"] == plan_id), None)
            if chosen is None:
                raise ActionRefused(404, "VERIFICATION_PLAN_NOT_FOUND", "No such verification plan for this Action.")
            return chosen, plans
        visible = [p for p in plans if recorded_at is None or p["recorded_at"] <= recorded_at]
        return (visible[-1] if visible else None), plans

    def plan(self, tenant_id: UUID, site_id: UUID, site_code: str, action_id: UUID, plan_id: UUID | None = None,
             recorded_at: datetime | None = None) -> dict[str, Any]:
        chosen, plans = self._select(tenant_id, site_id, action_id, plan_id, recorded_at)
        superseded_by = {str(p["supersedes_plan_id"]): str(p["id"]) for p in plans if p["supersedes_plan_id"]}
        current = plans[-1] if plans else None
        body: dict[str, Any] = {
            "label": LABEL, "action_id": str(action_id),
            "selector": {"plan_id": None if plan_id is None else str(plan_id),
                         "recorded_at": None if recorded_at is None else recorded_at.isoformat()},
            "verification_state": {"state": "PENDING" if plans else "NO_PLAN",
                                   "statement": "No verification outcome exists yet; PENDING is a read state."},
            "history": [{"plan_id": str(p["id"]), "recorded_at": p["recorded_at"].isoformat(),
                         "supersedes_plan_id": None if p["supersedes_plan_id"] is None else str(p["supersedes_plan_id"]),
                         "superseded_by_plan_id": superseded_by.get(str(p["id"]))} for p in plans],
            "plan": None, "selection_bindings": []}
        if chosen is not None:
            body["plan"] = self._plan_wire(chosen, site_code)
            body["is_current_plan"] = current is not None and chosen["id"] == current["id"]
            body["superseded_by_plan_id"] = superseded_by.get(str(chosen["id"]))
            body["selection_bindings"] = [_wire({k: v for k, v in b.items() if k not in ("tenant_id", "site_id")})
                                          for b in self.store.selection_bindings(tenant_id, site_id, chosen["id"])
                                          if recorded_at is None or b["recorded_at"] <= recorded_at]
        return body

    def evidence(self, tenant_id: UUID, site_id: UUID, site_code: str, action_id: UUID, plan_id: UUID | None = None,
                 recorded_at: datetime | None = None) -> dict[str, Any]:
        """Required and accepted evidence of the selected plan's two windows, as accepted by the cutoff (default:
        now): all twelve slots per window, interval kWh, SOC start/end samples, effective reserve, gaps and
        conflicts, sampled-breach seconds, exact comparability inputs against the frozen bands, and the target."""
        chosen, _ = self._select(tenant_id, site_id, action_id, plan_id, recorded_at)
        if chosen is None:
            raise ActionRefused(404, "VERIFICATION_PLAN_NOT_FOUND", "No verification plan for this Action.")
        known_at = recorded_at or self.clock()
        basis = chosen["basis"]
        windows = {}
        for name in ("baseline", "later"):
            lo, hi = chosen[f"{name}_start"], chosen[f"{name}_end"]
            readings = [rules.Reading(id=str(r["id"]), role=r["role"],
                                      asset_id=None if r["asset_id"] is None else str(r["asset_id"]),
                                      measurement=r["measurement"], source_time=r["source_time"],
                                      interval_start=r["interval_start"], interval_end=r["interval_end"],
                                      value_text=r["normalized_value_text"], unit=r["normalized_unit"],
                                      quality=r["quality"])
                        for r in self.store.window_readings(tenant_id, site_id, lo, hi, list(ROLES), known_at)]
            reserves = [rules.ReserveValue(value=Fraction(str(r["value"])), valid_from=r["valid_from"],
                                           valid_to=r["valid_to"], foundation_revision_id=str(r["foundation_revision_id"]))
                        for r in self.store.reserve_history(tenant_id, site_id, chosen["battery_asset_id"], lo, hi,
                                                            known_at)]
            windows[name] = rules.window_evidence(lo, readings, load_asset_ids=list(basis["load_asset_ids"]),
                                                  critical_load_asset_id=basis.get("critical_load_asset_id"),
                                                  reserves=reserves)
        bindings = [b for b in self.store.selection_bindings(tenant_id, site_id, chosen["id"])
                    if b["recorded_at"] <= known_at]
        later_target = bindings[-1]["selection"]["target"] if bindings else {
            "state": "NOT_BOUND", "statement": "The later window's selection binding has not been appended yet."}
        baseline_target = chosen["baseline_selection"]["target"]
        later_seconds = later_target.get("candidate_seconds") if later_target.get("state") == "KNOWN" else None
        return {
            "label": LABEL, "action_id": str(action_id), "plan_id": str(chosen["id"]),
            "knowledge_cutoff": known_at.isoformat(), "plan_version": chosen["plan_version"],
            "bands": chosen["bands"], "coverage": chosen["coverage"],
            "verification_state": {"state": "PENDING",
                                   "statement": "Evidence read only; no outcome is computed here (PENDING is a read "
                                                "state, not an outcome)."},
            "windows": _wire(windows),
            "comparability": _wire(rules.comparability(windows["baseline"], windows["later"])),
            "target": {"baseline": baseline_target, "later": later_target,
                       "later_selection_binding_id": str(bindings[-1]["id"]) if bindings else None,
                       "met": rules.target_met(chosen["baseline_candidate_seconds"], later_seconds),
                       "rule": chosen["target"]["rule"]},
        }
