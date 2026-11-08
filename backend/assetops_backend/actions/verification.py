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

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from fractions import Fraction
from typing import Any, Callable
from uuid import UUID, uuid4

from assetops_backend import read_scope
from assetops_backend.actions import reserve_trial
from assetops_backend.actions import verification_rules as rules
from assetops_backend.actions.lifecycle import APPLIED, RESOLUTION_WITHDRAWN, RESOLVED, SYSTEM_DEMO, latest_resolution
from assetops_backend.actions.ports import ActionRefused
from assetops_backend.analytics.assessment_inputs import BRACKET
from assetops_backend.chain.vocabulary import (  # FUEL-1 A3-R §3.6 (precedent `verification_families.py:41`)
    FUEL_VALUE_PAGE, NO_LOAD_BASIS_WORDS, money_text, price_text, trial_litres)
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
EVALUATE_COMMAND = "EVALUATE_VERIFICATION"
EVALUATOR_ID = "service:verification-evaluator"
EVALUATOR_SERVICE = "assetops-backend/verification-evaluator"
NON_DEMO_FIXTURE = "non-demo-evaluation"
CURRENT = "CURRENT"
PENDING_STATE, REASSESSMENT_PENDING, SETTLED = "PENDING", "REASSESSMENT_PENDING", "SETTLED"
FINAL = (rules.VERIFIED, rules.INEFFECTIVE)
#: OUT-E E3: a newly inserted outcome of these kinds gets one cost-check revision (INCONCLUSIVE: not calculated)
COST_CHECK_OUTCOMES = (rules.VERIFIED, rules.INEFFECTIVE, rules.INCONCLUSIVE)
COST_CHECK_COMMAND = "trial-cost-check/auto"
COST_CHECK_SOURCE = "Generator stop setting changed; no direct cost declared"
LOG = logging.getLogger(__name__)


@dataclass
class VerificationPorts:
    """What the verification service reads beside the Action store (wired by `actions.composition`).

    `day_status(tenant, site, day)` -> S3 `derive_status` of the UTC day's selection and S4 `match_state` of that
    day window; `provenance(tenant, site, evidence_ids)` -> the S4-05a source resolution of one exact ID set.
    A missing port fails closed: nothing is CURRENT and no source is coherent."""

    day_status: Callable[[UUID, UUID, date], dict[str, Any]] | None = None
    provenance: Callable[[UUID, UUID, list[str]], dict[str, Any]] | None = None
    #: OUT-E E3: `financials.composition.TrialComparisonPorts` (store + price_selection); None: no cost check
    trial_comparison: Any = None
    #: CH-9b2: the chain `SnapshotReader` (`latest`) the `midday-productive-shift-1` freeze reads; None: refused
    snapshots: Any = None
    #: DD1a1-R9: `run_assessments(tenant, site, run_id)` -> that S3 run's selected assessment revisions (each with
    #: its `scope`), or None when the run is unknown. None port: a re-selected baseline day fails closed as moved.
    run_assessments: Callable[[UUID, UUID, UUID], list[dict[str, Any]] | None] | None = None
    #: MV-1: the declared productive-use price over one span as known at a cutoff (`PriceSelection`); None: the mill
    #: value reads UNPRICED
    productive_price: Callable[[UUID, UUID, datetime, datetime, datetime], Any] | None = None


def _wire(value: Any) -> Any:
    if isinstance(value, datetime):  # F6 (fix round 1): UTC whatever the session TimeZone
        return (value.astimezone(timezone.utc) if value.tzinfo is not None else value).isoformat()
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


def _baseline_facts(revisions: list[dict[str, Any]] | None, lo: datetime, hi: datetime) -> list[Any] | None:
    """DD1a1-R9: the facts the verification reads from one S3 run over ``[lo, hi)``: each INTERVAL assessment whose
    interval or segments meet the window, as its key, claim level and full result (values, interval, segments,
    limitations). Run, revision and evidence identities are not facts. None when the run cannot be read."""
    if revisions is None:
        return None

    def meets(start: Any, end: Any) -> bool:
        s, e = rules._parse_time(start), rules._parse_time(end)
        if s is None:  # an unreadable time may sit in the window: it counts (fails closed, review Low 1)
            return True
        return (e is None or e > lo) and s < hi

    out = []
    for r in revisions:
        if r.get("scope") != "INTERVAL":
            continue
        result = r.get("result") or {}
        interval = result.get("interval") or {}
        if not (meets(interval.get("first_on"), interval.get("off_after") or interval.get("last_on"))
                or any(meets(g.get("start"), g.get("end")) for g in result.get("segments") or [])):
            continue
        out.append({"assessment_key": r["assessment_key"], "claim_level": r.get("claim_level"),
                    "result": _wire(result)})
    return sorted(out, key=lambda f: f["assessment_key"])


def _baseline_target(revisions: list[dict[str, Any]] | None, lo: datetime) -> tuple[Any, Any] | None:
    """DD1a1-R9 (review Low 2): the target the verification recomputes from one run's INTERVAL assessments, as its
    state and Candidate seconds (revision ids are not facts). A conflict anywhere in the run, even outside the
    window, makes the target INCONCLUSIVE, so a re-selection is facts-equal only when this is equal too."""
    if revisions is None:
        return None
    target = rules.target_window(lo, [{"assessment_revision_id": str(r.get("id")), "result": r.get("result") or {}}
                                      for r in revisions if r.get("scope") == "INTERVAL"])
    return target["state"], target["candidate_seconds"]


def _bindings(rows: list[dict[str, Any]]) -> dict[str, Any]:
    loads = sorted({str(r["asset_id"]) for r in rows if r["role"] == "feeder_demand" and r["asset_id"]})
    critical = {role: sorted({str(r["asset_id"]) for r in rows if r["role"] == role and r["asset_id"]})
                for role in CRITICAL_ROLES}
    return {"role_sets": sorted({r["role_set"] for r in rows}),
            "binding_set_revision_ids": sorted({str(r["binding_set_revision_id"]) for r in rows}),
            "roles": sorted({r["role"] for r in rows}), "load_asset_ids": loads,
            "critical_load_asset_ids": critical,
            "role_assets": {role: sorted({str(r["asset_id"]) for r in rows if r["role"] == role and r["asset_id"]})
                            for role in sorted({r["role"] for r in rows})}}


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
                                "must start at or after it.", effective_from=_wire(effective))
        covering = {_wire(p): [str(i) for i in ids] for p, ids in ctx["covering"].items()}
        cov = list(ctx["covering"].values())
        old = cov[0][0] if len(cov[0]) == 1 and cov[0] == cov[1] else None
        new = cov[2][0] if len(cov[2]) == 1 and cov[2] == cov[3] else None
        # F1: the baseline's covering revision must be the one the applied change moved *from* (its split prefix or
        # the superseded revision), never an unrelated earlier revision before an intervening publication.
        changed_from = {str(change[k]) for k in ("split_foundation_revision_id", "superseded_foundation_revision_id")
                        if change.get(k)}
        if old is None or new is None or old == new or str(new) != str(change["new_foundation_revision_id"]) \
                or str(old) not in changed_from:
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
        states = self._day_states(tenant_id, site_id, [{"day": s["day"], "run_id": s["run_id"]} for s in ctx["days"]],
                                  require_s4=False)
        stale = [s for s in states if not s["current"]]
        if stale:
            raise ActionRefused(409, "VERIFICATION_BASELINE_NOT_CURRENT",
                                "Every UTC day the baseline needs must have a CURRENT S3 dispatch selection "
                                "(D-2026-10-16-s602a-cutoff).", days=_wire(stale))
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
            "effective_from": _wire(effective), "baseline_start": _wire(b0), "later_start": _wire(l0),
            "baseline_candidate_seconds": target["candidate_seconds"],
            "baseline_selection": {"days": _selection_pin(ctx["days"]), "target": _wire(target),
                                   "currentness": [{"day": s["day"], "s3_status": s["status"]["s3_status"]}
                                                   for s in states]},
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
            if plans:
                prior = heads[-1]
                self._continuation_check(tenant_id, site_id, action, prior)
                # The observable later-run cutoff of the replaced plan (`D-2026-10-16-s602a-cutoff`): once its later
                # window has an accepted report, the new later window starts strictly after that window ends.
                started = self.store.accepted_count(c, tenant_id, site_id, prior["later_start"], prior["later_end"],
                                                    now)
                if started and l0 < prior["later_end"]:
                    raise ActionRefused(409, "VERIFICATION_LATER_WINDOW_STARTED",
                                        "The replaced plan's later window has started; the new later window must "
                                        "begin after it ends.", reason="NOT_AFTER_PRIOR_LATER_WINDOW",
                                        prior_later_end=_wire(prior["later_end"]))
            later = self.store.accepted_count(c, tenant_id, site_id, l0, l0 + rules.WINDOW, now)
            if later:
                raise ActionRefused(409, "VERIFICATION_LATER_WINDOW_STARTED",
                                    "A later-window report has already been accepted (or the later run has begun); "
                                    "freeze a new plan with a new later window.", accepted_evidence_count=later)

        row, replayed = self.store.freeze_plan(tenant_id, site_id, plan, check=check)
        if replayed:
            return self._replay(row, digest, site_code)
        return 201, {"label": LABEL, "replayed": False, "plan": self._plan_wire(row, site_code)}

    def freeze_domain_plan(self, tenant_id: UUID, site_id: UUID, domain_action_id: UUID) -> tuple[int, dict[str, Any]]:
        """CH-9b2 (CH9b2-R "Freeze trigger"): freeze the `midday-productive-shift-1` plan of a MINI domain Action,
        once, after its work case is COMPLETE and linked. A service method (story time and tests); no route."""
        from assetops_backend.actions.verification_families import MIDDAY, FAMILIES

        return FAMILIES[MIDDAY].freeze(self.store, self._ports().snapshots, tenant_id, site_id, domain_action_id,
                                       self.clock())

    def evaluate_domain_plan(self, tenant_id: UUID, site_id: UUID, domain_action_id: UUID,
                             today: date | None = None) -> dict[str, Any]:
        """CH-9b3 (CH9b3-R Q9): judge the mill plan once, storing the one decisive outcome or nothing. A service
        method: DD-1b calls it at story time, the `chain_snapshots` stage after its drain; no route."""
        from assetops_backend.actions.verification_families import MIDDAY, FAMILIES

        return FAMILIES[MIDDAY].evaluate(self.store, self._ports().snapshots, tenant_id, site_id, domain_action_id,
                                         self.clock(), today)

    def evaluate_site_domain_plans(self, tenant_id: UUID, site_id: UUID,
                                   today: date | None = None) -> list[dict[str, Any]]:
        """Every undecided mill plan of the Site, judged once each (the stage trigger)."""
        from assetops_backend.actions.verification_families import MIDDAY

        return [{"domain_action_id": str(a), **self.evaluate_domain_plan(tenant_id, site_id, a, today)}
                for a in self.store.undecided_domain_plans(tenant_id, site_id, MIDDAY)]

    def domain_summary(self, tenant_id: UUID, site_id: UUID, domain_action_id: UUID) -> dict[str, Any]:
        """CH9b3-R Q5: the read-only mill verdict of a MINI domain Action (one GET; the page's only read)."""
        from assetops_backend.actions import verification_families as vf

        ctx = self.store.domain_plan_context(tenant_id, site_id, domain_action_id)
        if ctx is None:
            raise ActionRefused(404, "ACTION_NOT_FOUND", "No such Action for this Site.")
        if ctx["action"]["domain"] != "MINI":  # a MINI Action's plan exists only from an opportunity (the freeze)
            raise ActionRefused(409, "VERIFICATION_FAMILY_UNSUPPORTED",
                                "Only a MINI Action raised from an opportunity has a midday verification.")
        plan = ctx["plan"]
        outcomes = [] if plan is None else self.store.domain_outcomes(tenant_id, site_id, domain_action_id)
        live = None
        if plan is not None and not outcomes:
            snapshots = self._ports().snapshots
            if snapshots is None:
                raise ActionRefused(503, "VERIFICATION_SNAPSHOTS_UNAVAILABLE", "The day snapshots cannot be read.")
            live = vf.assess_plan(plan, snapshots, tenant_id, site_id, self.clock())
        if outcomes and outcomes[0]["outcome"] == vf.VERIFIED:
            return vf.summary_wire(ctx, outcomes, live, price=self._mill_price(tenant_id, site_id, plan, outcomes[0]))
        return vf.summary_wire(ctx, outcomes, live)

    def _mill_price(self, tenant_id: UUID, site_id: UUID, plan: dict[str, Any], outcome: dict[str, Any]) -> Any:
        """MV-1 (FUEL-1 §2.2(c)): the declared productive-use price over the Site-local span from the first baseline
        day to the end of the last later day, as known when the verdict was recorded (a later publication never
        changes a shown verdict). None without the port: the value reads UNPRICED."""
        from assetops_backend.actions.verification_families import local_midnight

        port = self._ports().productive_price
        if port is None:
            return None
        tz = plan["basis"]["timezone"]
        details = outcome["details"]
        lo = local_midnight(min(date.fromisoformat(d) for d in details["baseline"]["days"]), tz)
        hi = local_midnight(max(date.fromisoformat(d) for d in details["later"]["days"]) + timedelta(days=1), tz)
        known_at = outcome["recorded_at"]
        if isinstance(known_at, str):
            known_at = datetime.fromisoformat(known_at)
        return port(tenant_id, site_id, lo, hi, known_at)

    def _continuation_check(self, tenant_id: UUID, site_id: UUID, action: dict[str, Any],
                            prior: dict[str, Any]) -> None:
        """F4 (`D-2026-10-16-s602a-holds`), under the trial lock: the head plan may be superseded while it has no
        outcome, or when the Action's latest settled outcome is that plan's INCONCLUSIVE and stays current. Never
        after a settled guardrail failure, a current VERIFIED / target-miss INEFFECTIVE (an outstanding RESOLVED),
        a withdrawal still awaiting its reassessment, or a permanent prior-trial overlap involving this Action."""
        from assetops_backend.actions.service import reassessment_overlaps

        action_id = action["id"]
        outcomes = self.store.outcomes(tenant_id, site_id, action_id)
        if not any(o["plan_id"] == prior["id"] for o in outcomes):
            return  # pending: no outcome yet for the current plan

        def refuse(reason: str, message: str) -> None:
            raise ActionRefused(409, "VERIFICATION_PLAN_EVALUATED", message, reason=reason,
                                current_plan_id=str(prior["id"]))

        latest = outcomes[-1]
        events = self.store.events(tenant_id, site_id, action_id)
        resolution = latest_resolution(events)
        if resolution is not None and resolution["state"] == RESOLVED:
            refuse("GUARDRAIL_FAILED" if resolution["guardrail_failed"] else "RESOLVED",
                   "The current plan is resolved; only an INCONCLUSIVE trial can continue with a new plan.")
        if resolution is not None:  # RESOLUTION_WITHDRAWN: settled only by an outcome of that run or a later one
            withdrawn = next(e for e in events if str(e["id"]) == resolution["event_id"])
            if not any(o["triggering_job"] == withdrawn.get("triggering_job") or o["recorded_at"] > withdrawn[
                    "recorded_at"] for o in outcomes):
                refuse("REASSESSMENT_PENDING", "A withdrawn resolution awaits its reassessment; complete it first.")
        if latest["plan_id"] != prior["id"] or latest["outcome"] != rules.INCONCLUSIVE:
            refuse("NOT_INCONCLUSIVE", "Only a plan whose latest settled outcome is INCONCLUSIVE can be continued.")
        state = self.current_state(tenant_id, site_id, action_id)
        if state["state"] != rules.INCONCLUSIVE:
            refuse("REASSESSMENT_PENDING", "The INCONCLUSIVE outcome is pending reassessment; evaluate it first.")
        scope = self.store.trial_actions(tenant_id, site_id, action["asset_id"], action["rule_id"])
        if any(str(action_id) in (o["action_id"], o["closure_action_id"]) for o in reassessment_overlaps(scope)):
            refuse("PRIOR_TRIAL_REASSESSMENT_OVERLAP", "A permanent prior-trial overlap involves this Action.")

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
        key = command["idempotency_key"]
        payload = {"command": BIND_COMMAND, "action_id": str(action_id), "plan_id": str(plan_id), "idempotency_key": key}
        digest = reserve_trial.sha(payload)
        for earlier in self.store.selection_bindings(tenant_id, site_id, plan_id):
            if earlier.get("idempotency_key") == key:
                return self._binding_replay(earlier, digest)
        now = self.clock()
        self._require_head(tenant_id, site_id, action_id, plan)
        if now < plan["later_end"]:
            raise ActionRefused(409, "VERIFICATION_LATER_WINDOW_OPEN",
                                "The later window has not closed yet; bind its selection after later_end.",
                                later_end=_wire(plan["later_end"]))
        selections = self.store.day_selections(tenant_id, site_id, required_days(plan["later_start"]), now)
        unselected = [s["day"] for s in selections if not s["selected"]]
        if unselected:
            raise ActionRefused(409, "VERIFICATION_LATER_NOT_SELECTED",
                                "Every UTC day covering the later window needs a final S3 dispatch selection.",
                                days=unselected)
        states = self._day_states(tenant_id, site_id, [{"day": s["day"], "run_id": s["run_id"]} for s in selections],
                                  require_s4=False)
        stale = [s for s in states if not s["current"]]
        if stale:
            raise ActionRefused(409, "VERIFICATION_LATER_NOT_CURRENT",
                                "Every UTC day the later window needs must have a CURRENT S3 dispatch selection "
                                "(D-2026-10-16-s602a-cutoff).", days=_wire(stale))
        target = rules.target_window(plan["later_start"], _intervals(selections))
        selection = {"days": _selection_pin(selections), "target": _wire(target),
                     "currentness": [{"day": s["day"], "s3_status": s["status"]["s3_status"]} for s in states]}
        binding = {"id": uuid4(), "window_name": "LATER", "selection": selection,
                   "selection_sha256": reserve_trial.sha({k: selection[k] for k in ("days", "target")}),
                   "actor_kind": SYSTEM_DEMO.actor_kind, "actor_id": SYSTEM_DEMO.actor_id,
                   "triggering_service": SYSTEM_DEMO.triggering_service, "triggering_job": None,
                   "triggering_fixture": granted.fixture_id or "", "idempotency_key": key, "payload_sha256": digest,
                   "recorded_at": now}

        def check(c: Any) -> None:
            if self.store.is_superseded(c, plan["id"]):
                raise ActionRefused(409, "VERIFICATION_PLAN_NOT_HEAD",
                                    "This plan has been replaced; bind the current plan's later selection.")

        row, replayed = self.store.append_selection_binding(tenant_id, site_id, plan, binding, check=check)
        if replayed and row.get("idempotency_key") == key:
            return self._binding_replay(row, digest)
        return (200 if replayed else 201), {"label": LABEL, "replayed": replayed, "binding": _wire(
            {k: v for k, v in row.items() if k not in ("tenant_id", "site_id")})}

    @staticmethod
    def _binding_replay(row: dict[str, Any], digest: str) -> tuple[int, dict[str, Any]]:
        if row["payload_sha256"] != digest:
            raise ActionRefused(409, "VERIFICATION_IDEMPOTENCY_CONFLICT",
                                "This idempotency key already bound a different selection command.",
                                binding_id=str(row["id"]))
        return 200, {"label": LABEL, "replayed": True, "binding": _wire(
            {k: v for k, v in row.items() if k not in ("tenant_id", "site_id")})}

    def _require_head(self, tenant_id: UUID, site_id: UUID, action_id: UUID, plan: dict[str, Any]) -> None:
        if any(p["supersedes_plan_id"] == plan["id"] for p in self.store.plans(tenant_id, site_id, action_id)):
            raise ActionRefused(409, "VERIFICATION_PLAN_NOT_HEAD",
                                "This plan has been replaced; use the current plan.", plan_id=str(plan["id"]))

    # ---- S3/S4 currentness ------------------------------------------------------------------------------------

    def _ports(self) -> VerificationPorts:
        return getattr(self.actions, "verification_ports", None) or VerificationPorts()

    def _day_states(self, tenant_id: UUID, site_id: UUID, pins: list[dict[str, Any]], *,
                    require_s4: bool, facts_window: tuple[datetime, datetime] | None = None) -> list[dict[str, Any]]:
        """Each pinned UTC day's S3 status (and, when required, S4 episode reassessment) against its pinned run.
        `pending` means S3/S4 work is not settled; `moved` means it settled on a different selection.

        DD1a1-R9: with `facts_window` (a baseline pin), a different selected run is `moved` only when the facts the
        verification reads over that window differ (`_baseline_facts`); equal facts are `reselected` (pinned run,
        current run, listed under `reselected` only when present) and do not block. A run that cannot be read fails
        closed as moved."""
        ports = self._ports()
        port = ports.day_status
        out = []
        for pin in pins:
            status = None if port is None else port(tenant_id, site_id, date.fromisoformat(str(pin["day"])))
            pending, moved, reselected = [], [], []
            if status is None:
                pending.append("S3/S4 currentness is not available")
            else:
                if status["s3_status"] != CURRENT:
                    pending.append(f"S3 {status['s3_status']}: {', '.join(status['s3_reasons']) or 'no reasons'}")
                if require_s4 and not status["s4_matched"]:
                    pending.append("S4 episode reassessment pending" +
                                   (" (deferred)" if status.get("s4_match_deferred") else ""))
                if status["s3_status"] == CURRENT and pin.get("run_id") is not None \
                        and status["run_id"] != str(pin["run_id"]):
                    facts = targets = None
                    if facts_window is not None and ports.run_assessments is not None:
                        lo, hi = facts_window
                        runs = [ports.run_assessments(tenant_id, site_id, UUID(str(run)))
                                for run in (pin["run_id"], status["run_id"])]
                        facts = [_baseline_facts(r, lo, hi) for r in runs]
                        targets = [_baseline_target(r, lo) for r in runs]
                    if facts is not None and facts[0] is not None and facts[0] == facts[1] \
                            and targets[0] is not None and targets[0] == targets[1]:
                        reselected.append({"pinned_run_id": str(pin["run_id"]), "current_run_id": status["run_id"],
                                           "facts": "equal", "assessments": len(facts[0])})
                    else:
                        moved.append(f"selection moved from run {pin['run_id']} to {status['run_id']}")
            state = {"day": str(pin["day"]), "pinned_run_id": None if pin.get("run_id") is None
                     else str(pin["run_id"]), "status": status, "pending": pending, "moved": moved,
                     "current": not pending and not moved}
            if reselected:  # listed only when it happened, so every earlier day-state body is unchanged
                state["reselected"] = reselected
            out.append(state)
        return out

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
            "verification_state": self.current_state(tenant_id, site_id, action_id, at=recorded_at),
            "history": [{"plan_id": str(p["id"]), "recorded_at": _wire(p["recorded_at"]),
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

    def _windows(self, tenant_id: UUID, site_id: UUID, plan: dict[str, Any], known_at: datetime,
                 reserves_known_at: datetime | None = None,
                 exclude: frozenset[str] = frozenset()) -> dict[str, dict[str, Any]]:
        """Both windows' evidence as accepted by `known_at`, filtered to the plan's battery and bound assets (F6).
        `reserves_known_at` holds the Foundation reserve history at another cutoff and `exclude` leaves out these
        accepted evidence IDs (F2 attribution replay)."""
        basis = plan["basis"]
        windows = {}
        for name in ("baseline", "later"):
            lo, hi = plan[f"{name}_start"], plan[f"{name}_end"]
            readings = [rules.Reading(id=str(r["id"]), role=r["role"],
                                      asset_id=None if r["asset_id"] is None else str(r["asset_id"]),
                                      measurement=r["measurement"], source_time=r["source_time"],
                                      interval_start=r["interval_start"], interval_end=r["interval_end"],
                                      value_text=r["normalized_value_text"], unit=r["normalized_unit"],
                                      quality=r["quality"])
                        for r in self.store.window_readings(tenant_id, site_id, lo, hi, list(ROLES), known_at)
                        if str(r["id"]) not in exclude]
            reserves = [rules.ReserveValue(value=Fraction(str(r["value"])), valid_from=r["valid_from"],
                                           valid_to=r["valid_to"], foundation_revision_id=str(r["foundation_revision_id"]))
                        for r in self.store.reserve_history(tenant_id, site_id, plan["battery_asset_id"], lo, hi,
                                                            reserves_known_at or known_at)]
            bound = basis["baseline_bindings"] if name == "baseline" else basis["later_bindings_at_freeze"]
            windows[name] = rules.window_evidence(lo, readings, load_asset_ids=list(basis["load_asset_ids"]),
                                                  critical_load_asset_id=basis.get("critical_load_asset_id"),
                                                  reserves=reserves, battery_asset_id=str(plan["battery_asset_id"]),
                                                  role_assets=bound.get("role_assets"))
        return windows

    def evidence(self, tenant_id: UUID, site_id: UUID, site_code: str, action_id: UUID, plan_id: UUID | None = None,
                 recorded_at: datetime | None = None) -> dict[str, Any]:
        """Required and accepted evidence of the selected plan's two windows, as accepted by the cutoff (default:
        now): all twelve slots per window, interval kWh, SOC start/end samples, effective reserve, gaps and
        conflicts, sampled-breach seconds, exact comparability inputs against the frozen bands, and the target."""
        chosen, _ = self._select(tenant_id, site_id, action_id, plan_id, recorded_at)
        if chosen is None:
            raise ActionRefused(404, "VERIFICATION_PLAN_NOT_FOUND", "No verification plan for this Action.")
        known_at = recorded_at or self.clock()
        windows = self._windows(tenant_id, site_id, chosen, known_at)
        bindings = [b for b in self.store.selection_bindings(tenant_id, site_id, chosen["id"])
                    if b["recorded_at"] <= known_at]
        later_target = bindings[-1]["selection"]["target"] if bindings else {
            "state": "NOT_BOUND", "statement": "The later window's selection binding has not been appended yet."}
        baseline_target = chosen["baseline_selection"]["target"]
        later_seconds = later_target.get("candidate_seconds") if later_target.get("state") == "KNOWN" else None
        provenance = self._ports().provenance
        sources = {name: None if provenance is None or not w["evidence_ids"] else _source_wire(
            provenance(tenant_id, site_id, list(w["evidence_ids"]))) for name, w in windows.items()}
        return {
            "label": LABEL, "action_id": str(action_id), "plan_id": str(chosen["id"]),
            "knowledge_cutoff": _wire(known_at), "plan_version": chosen["plan_version"],
            "bands": chosen["bands"], "coverage": chosen["coverage"],
            "verification_state": self.current_state(tenant_id, site_id, action_id, at=recorded_at),
            "windows": _wire(windows),
            "comparability": _wire(rules.comparability(windows["baseline"], windows["later"])),
            "source_resolution": {"baseline": sources["baseline"], "later": sources["later"],
                                  "pair": rules.source_pair(sources["baseline"], sources["later"]),
                                  "rule": chosen["basis"]["source_rule"]},
            "target": {"baseline": baseline_target, "later": later_target,
                       "later_selection_binding_id": str(bindings[-1]["id"]) if bindings else None,
                       "met": rules.target_met(chosen["baseline_candidate_seconds"], later_seconds),
                       "rule": chosen["target"]["rule"]},
        }

    # ---- evaluator job (D-2026-10-16-s6-verification) ----------------------------------------------------------

    def _head(self, tenant_id: UUID, site_id: UUID, action_id: UUID) -> dict[str, Any] | None:
        plans = self.store.plans(tenant_id, site_id, action_id)
        superseded = {p["supersedes_plan_id"] for p in plans if p["supersedes_plan_id"]}
        heads = [p for p in plans if p["id"] not in superseded]
        return heads[-1] if heads else None

    def _assess(self, tenant_id: UUID, site_id: UUID, plan: dict[str, Any], now: datetime) -> dict[str, Any]:
        """Read-only: is the pair settled, and if so the exact verdict, metrics, basis and details."""
        if now < plan["later_end"]:
            return {"state": PENDING_STATE, "reasons": ["LATER_WINDOW_OPEN"]}
        bindings = self.store.selection_bindings(tenant_id, site_id, plan["id"])
        if not bindings:
            return {"state": PENDING_STATE, "reasons": ["LATER_SELECTION_NOT_BOUND"]}
        binding = bindings[-1]
        base_days = self._day_states(tenant_id, site_id, plan["baseline_selection"]["days"], require_s4=True,
                                     facts_window=(plan["baseline_start"], plan["baseline_end"]))
        later_days = self._day_states(tenant_id, site_id, binding["selection"]["days"], require_s4=True)
        pending = [f"{w}:{d['day']}: {p}" for w, days in (("baseline", base_days), ("later", later_days))
                   for d in days for p in d["pending"]]
        pending += [f"later:{d['day']}: {m} (append a new later selection binding)" for d in later_days
                    for m in d["moved"]]
        if pending:
            return {"state": REASSESSMENT_PENDING, "reasons": pending, "days": {"baseline": base_days,
                                                                                "later": later_days}}
        blockers = [f"BASELINE_SELECTION_CHANGED:{d['day']}" for d in base_days if d["moved"]]
        probes = [plan["baseline_start"], plan["baseline_end"] - EPSILON, plan["later_start"],
                  plan["later_end"] - EPSILON]
        covering = self.store.covering_ids(tenant_id, site_id, probes, now)
        want = [[str(plan["old_foundation_revision_id"])]] * 2 + [[str(plan["new_foundation_revision_id"])]] * 2
        if covering != want:
            blockers.append("FOUNDATION_CHANGED")
        basis = plan["basis"]
        later_rows = _bindings(self.store.window_bindings(tenant_id, site_id, plan["later_start"], plan["later_end"],
                                                          now))
        if later_rows["role_assets"] != basis["baseline_bindings"].get("role_assets"):
            blockers.append("BINDINGS_NOT_COMPARABLE")
        windows = self._windows(tenant_id, site_id, plan, now)
        comparable = rules.comparability(windows["baseline"], windows["later"])
        provenance = self._ports().provenance
        sources = {name: None if provenance is None or not w["evidence_ids"] else _source_wire(
            provenance(tenant_id, site_id, list(w["evidence_ids"]))) for name, w in windows.items()}
        source = rules.source_pair(sources["baseline"], sources["later"])
        decision = rules.decide(baseline=windows["baseline"], later=windows["later"], comparable=comparable,
                                baseline_seconds=plan["baseline_candidate_seconds"],
                                later_target=binding["selection"]["target"], source=source, blockers=blockers)
        result = {"outcome": decision["outcome"], "reasons": decision["reasons"],
                  "guardrail_failed": decision["guardrail_failed"], "target_met": decision["target_met"]}
        outcome_basis = {
            "plan_id": str(plan["id"]), "plan_sha256": plan["plan_sha256"], "selection_binding_id": str(binding["id"]),
            "selection_sha256": binding["selection_sha256"],
            "origin_finding_revision_id": str(plan["origin_finding_revision_id"]),
            "applied_event_id": str(plan["applied_event_id"]), "change_id": str(plan["change_id"]),
            "baseline_days": [{"day": d["day"], "run_id": d["status"]["run_id"]} for d in base_days],
            "later_days": [{"day": d["day"], "run_id": d["status"]["run_id"]} for d in later_days],
            "covering_foundation_revision_ids": covering,
            "evidence_ids": {name: list(w["evidence_ids"]) for name, w in windows.items()},
            "source_resolutions": {name: None if s is None else {k: s.get(k) for k in (
                "state", "publication_ids", "source_classes", "fixtures", "runs")} for name, s in sources.items()},
            "later_bindings": later_rows["role_assets"], "result": result,
        }
        details = {
            "label": LABEL, "windows": {name: {k: w[k] for k in (
                "window_start", "window_end", "complete", "feeder_demand_kwh", "pv_available_kwh",
                "unserved_critical_kwh", "below_reserve_seconds", "initial_soc", "terminal_soc", "problems")}
                for name, w in _wire(windows).items()},
            "comparability": _wire(comparable), "source": source, "sources": sources,
            "target": {"baseline_seconds": plan["baseline_candidate_seconds"],
                       "later": binding["selection"]["target"], "met": decision["target_met"],
                       "rule": plan["target"]["rule"]},
            "days": _wire({"baseline": base_days, "later": later_days}), "blockers": blockers,
        }
        return {"state": SETTLED, "decision": decision, "basis": outcome_basis, "details": details,
                "binding": binding}

    def _attribution(self, tenant_id: UUID, site_id: UUID, action_id: UUID, resolution: dict[str, Any],
                     now: datetime) -> dict[str, Any]:
        """F2 (`D-2026-10-16-s602a-holds`): the accepted public readings that caused this RESOLVED closure to lose
        its pinned basis, persisted at withdrawal.

        Candidates were accepted after the RESOLVED event and by the withdrawal (`now`), touch a pinned window and
        match the plan's frozen role/bound asset for that window (the plan's battery for SOC); unbound assets and
        unbound roles are never candidates. Fix round 2 (re-review R1): each window whose computed result (coverage,
        energy, reserve seconds, SOC, problems) changed is replayed in acceptance order, with the Foundation reserve
        history held at the closure's cutoff. A candidate is causal only when its own arrival changes that window's
        result relative to the previous acceptance prefix, and it entered the window's used evidence. A reading that
        leaves the result unchanged (an exact duplicate, a later reading repeating an earlier change) is never causal,
        so it cannot move the overlap boundary. Readings accepted at the same instant are tested one by one (the
        others left out); they are recorded together as jointly causal only when the instant changes the result and
        no single one of them changes it on its own. `attribution` is CAUSAL (non-empty set), NONE
        (empty: Foundation, source, binding or worker-only cause, or readings that changed nothing) or INDETERMINATE
        (a bound candidate whose effect cannot be established, e.g. the window's S3 selection is still pending or
        moved while its evidence result is unchanged): INDETERMINATE keeps the ordinary hold and never overlaps."""
        closed_at = resolution["recorded_at"]
        plan = self._plan(tenant_id, site_id, action_id, UUID(resolution["plan_id"]))
        outcome = next((o for o in self.store.outcomes(tenant_id, site_id, action_id)
                        if str(o["id"]) == resolution["outcome_id"]), None)
        names = ("baseline", "later")
        spans = [(plan[f"{n}_start"], plan[f"{n}_end"]) for n in names]
        basis = plan["basis"]
        bound = {"baseline": basis["baseline_bindings"].get("role_assets") or {},
                 "later": basis["later_bindings_at_freeze"].get("role_assets") or {}}

        def is_bound(row: dict[str, Any], name: str) -> bool:
            asset = None if row["asset_id"] is None else str(row["asset_id"])
            if row["role"] == "battery_soc":
                return asset == str(plan["battery_asset_id"])
            return asset is not None and asset in bound[name].get(row["role"], [])

        late = self.store.late_evidence(tenant_id, site_id, spans, list(ROLES), closed_at, until=now)
        candidates = {n: [r for r in late if i in r["windows"] and is_bound(r, n)] for i, n in enumerate(names)}
        out: dict[str, Any] = {"attribution": "NONE", "invalidating_evidence": [], "basis_changes": [],
                               "candidate_evidence_ids": sorted({str(r["id"]) for rs in candidates.values()
                                                                 for r in rs})}
        if not out["candidate_evidence_ids"]:
            return out
        before = _wire(self._windows(tenant_id, site_id, plan, closed_at))
        after = _wire(self._windows(tenant_id, site_id, plan, now, reserves_known_at=closed_at))
        keys = ("complete", "feeder_demand_kwh", "pv_available_kwh", "unserved_critical_kwh", "below_reserve_seconds",
                "initial_soc", "terminal_soc", "problems")
        pinned = (outcome or {}).get("basis") or {}
        indeterminate = False

        def result(name: str, at: datetime, exclude: frozenset[str] = frozenset()) -> dict[str, Any]:
            window = _wire(self._windows(tenant_id, site_id, plan, at, reserves_known_at=closed_at,
                                         exclude=exclude))[name]
            return {k: window.get(k) for k in keys}

        def arrivals(name: str, was: dict[str, Any]) -> list[dict[str, Any]]:
            """R1: the candidates whose own arrival changed the window, replayed by acceptance prefix."""
            groups: dict[datetime, list[dict[str, Any]]] = {}
            for r in candidates[name]:  # `late_evidence` orders by acceptance
                groups.setdefault(r["decided_at"], []).append(r)
            prev, causal = was, []
            for at, group in groups.items():
                cur = result(name, at)
                if cur == prev:
                    continue  # nothing accepted at this instant changed the result
                ids = {str(r["id"]) for r in group}
                alone = group if len(group) == 1 else [
                    r for r in group if result(name, at, frozenset(ids - {str(r["id"])})) != prev]
                causal += alone or group  # jointly causal only when no single one changes it on its own
                prev = cur
            return causal

        for name in names:
            if not candidates[name]:
                continue
            was, now_ = ({k: w[name].get(k) for k in keys} for w in (before, after))
            entered = set(after[name]["evidence_ids"]) - set(before[name]["evidence_ids"])
            entered |= {i for p in after[name].get("problems") or [] for i in (p.get("evidence_ids") or [])}
            hit = [r for r in arrivals(name, was) if str(r["id"]) in entered] if was != now_ else []
            if was != now_ and hit:
                days = self._day_states(tenant_id, site_id, pinned.get(f"{name}_days", []), require_s4=True,
                                             facts_window=(plan["baseline_start"], plan["baseline_end"])
                                             if name == "baseline" else None)
                out["basis_changes"].append({
                    "window": name, "window_start": _wire(plan[f"{name}_start"]),
                    "window_end": _wire(plan[f"{name}_end"]), "closed": was, "reassessed": now_,
                    "pinned_s3_days": pinned.get(f"{name}_days", []),
                    "current_s3_days": [{"day": d["day"], "run_id": (d["status"] or {}).get("run_id"),
                                         "pending": d["pending"], "moved": d["moved"]} for d in _wire(days)]})
                out["invalidating_evidence"] += [{"id": str(r["id"]), "role": r["role"],
                                                  "asset_id": None if r["asset_id"] is None else str(r["asset_id"]),
                                                  "window": name, "accepted_at": _wire(r["decided_at"]),
                                                  "decided_at": _wire(r["decided_at"])} for r in hit]
            elif was != now_:
                indeterminate = True  # the result moved but no candidate can be named
            else:
                days = self._day_states(tenant_id, site_id, pinned.get(f"{name}_days", []), require_s4=True,
                                             facts_window=(plan["baseline_start"], plan["baseline_end"])
                                             if name == "baseline" else None)
                if any(d["pending"] or d["moved"] for d in days):
                    indeterminate = True  # the window's S3 selection may yet move on these readings
        if out["invalidating_evidence"]:
            out["attribution"] = "CAUSAL"
        elif indeterminate:
            out["attribution"] = "INDETERMINATE"
        return out

    def evaluate(self, tenant_id: UUID, site_id: UUID, site_code: str, action_id: UUID,
                 command: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        """A SYSTEM demonstration evaluation request. The evaluator job (never the caller) computes the verdict and
        appends outcome, metrics and RESOLVED / RESOLUTION_WITHDRAWN in one transaction under the trial lock."""
        granted, _ = self.actions.authorize_action(tenant_id, site_id, site_code, VERIFY, action_id)
        head = self._head(tenant_id, site_id, action_id)
        if head is None:
            raise ActionRefused(404, "VERIFICATION_PLAN_NOT_FOUND", "No verification plan for this Action.")
        if command.get("plan_id") is not None and command["plan_id"] != head["id"]:
            raise ActionRefused(409, "VERIFICATION_PLAN_NOT_HEAD", "Only the current plan can be evaluated.",
                                current_plan_id=str(head["id"]))
        key = command["idempotency_key"]
        payload = {"command": EVALUATE_COMMAND, "action_id": str(action_id), "plan_id": str(head["id"]),
                   "idempotency_key": key}
        digest = reserve_trial.sha(payload)
        fixture = granted.fixture_id or NON_DEMO_FIXTURE
        request = {"id": uuid4(), "action_id": action_id, "plan_id": head["id"],
                   "actor_kind": SYSTEM_DEMO.actor_kind, "actor_id": SYSTEM_DEMO.actor_id,
                   "source_channel": SYSTEM_DEMO.source_channel,
                   "authorization_basis": SYSTEM_DEMO.basis(fixture, VERIFY),
                   "triggering_service": SYSTEM_DEMO.triggering_service, "triggering_fixture": fixture,
                   "idempotency_key": key, "payload": payload, "payload_sha256": digest, "recorded_at": self.clock()}

        def compose(c: Any, req: dict[str, Any], latest: dict[str, Any] | None,
                    events: list[dict[str, Any]]) -> dict[str, Any]:
            # Fix round 1 F1: everything the writes depend on is read here, under the battery trial lock: the head,
            # the instant and the assessment. The instant never precedes a stored outcome or event, so a write is
            # always ordered after the state it was decided against (a concurrent evaluation that committed first
            # is then seen and either reused or superseded on a fresher basis).
            current = self._head(tenant_id, site_id, action_id)
            if current is None or current["id"] != head["id"]:
                raise ActionRefused(409, "VERIFICATION_PLAN_NOT_HEAD", "Only the current plan can be evaluated.",
                                    current_plan_id=None if current is None else str(current["id"]))
            stamps = [e["recorded_at"] for e in events] + ([latest["recorded_at"]] if latest is not None else [])
            now = self.clock()
            if stamps and max(stamps) >= now:
                now = max(stamps) + EPSILON
            assessed = self._assess(tenant_id, site_id, head, now)
            job = f"verification-evaluation:{req['id']}"
            resolution = latest_resolution(events)
            out_events: list[dict[str, Any]] = []

            def event(kind: str, plan_id: Any, outcome_id: Any, body: dict[str, Any], key_: str) -> None:
                out_events.append({"id": uuid4(), "kind": kind, "recorded_at": now + EPSILON * (len(out_events) + 1),
                                   "triggering_service": EVALUATOR_SERVICE, "triggering_job": job,
                                   "triggering_fixture": req["triggering_fixture"], "idempotency_key": key_,
                                   "verification_plan_id": plan_id, "verification_outcome_id": outcome_id,
                                   "payload": {"label": LABEL, **body}})

            resolved = resolution is not None and resolution["state"] == RESOLVED

            def withdraw(reason: str, reasons: list[str]) -> None:
                cause = self._attribution(tenant_id, site_id, action_id, resolution, now)
                event(RESOLUTION_WITHDRAWN, resolution["plan_id"], resolution["outcome_id"], {
                    "reason": reason, "reasons": reasons, "withdrawn_resolved_event_id": resolution["event_id"],
                    "withdrawn_outcome": resolution["outcome"], **cause,
                    "statement": "The earlier resolution no longer stands; the trial hold is restored."},
                    f"withdraw:{resolution['event_id']}")

            if assessed["state"] != SETTLED:
                if resolved and assessed["state"] == REASSESSMENT_PENDING:
                    withdraw(REASSESSMENT_PENDING, assessed["reasons"])
                return {"events": out_events, "result": {"state": assessed["state"], "reasons": assessed["reasons"],
                                                         "withdrawn": bool(out_events)}}
            basis_sha = reserve_trial.sha(assessed["basis"])
            decision = assessed["decision"]
            if latest is not None and latest["plan_id"] == head["id"] and latest["basis_sha256"] == basis_sha:
                outcome, insert = latest, False
                # F1: an outstanding RESOLVED stands only for this very outcome, and only while it is final.
                if resolved and (resolution["outcome_id"] != str(latest["id"]) or latest["outcome"] not in FINAL):
                    withdraw("RESOLUTION_NOT_CURRENT", [f"the current outcome is {latest['id']}"])
                    resolved = False
            else:
                outcome = {"id": uuid4(), "action_id": action_id, "plan_id": head["id"],
                           "selection_binding_id": assessed["binding"]["id"], "evaluation_request_id": req["id"],
                           "supersedes_outcome_id": None if latest is None else latest["id"],
                           "outcome": decision["outcome"], "reasons": decision["reasons"],
                           "basis": assessed["basis"], "basis_sha256": basis_sha, "details": assessed["details"],
                           "actor_kind": "SYSTEM", "actor_id": EVALUATOR_ID, "triggering_job": job,
                           "idempotency_key": req["idempotency_key"], "recorded_at": now}
                insert = True
                if resolved:
                    withdraw("BASIS_CHANGED", [f"superseded by outcome {outcome['id']}"])
                    resolved = False
            if outcome["outcome"] in FINAL and not (resolved and resolution["outcome_id"] == str(outcome["id"])):
                count = sum(1 for e in events if e["kind"] == RESOLVED
                            and str(e.get("verification_outcome_id")) == str(outcome["id"]))
                event(RESOLVED, head["id"], outcome["id"], {
                    "outcome": outcome["outcome"], "reasons": list(outcome["reasons"]),
                    "guardrail_failed": rules.GUARDRAIL_FAIL in outcome["reasons"],
                    "plan_id": str(head["id"]), "outcome_id": str(outcome["id"]),
                    "releases_hold": rules.GUARDRAIL_FAIL not in outcome["reasons"],
                    "statement": "Final current verification outcome; RESOLVED can later be withdrawn."},
                    f"resolve:{outcome['id']}:{count}")
            return {"outcome": outcome, "insert_outcome": insert, "metrics": decision["metrics"] if insert else [],
                    "events": out_events, "result": {"state": SETTLED, "new_outcome": insert,
                                                     "withdrawn": any(e["kind"] == RESOLUTION_WITHDRAWN
                                                                      for e in out_events),
                                                     "resolved": any(e["kind"] == RESOLVED for e in out_events)}}

        result = self.store.record_evaluation(tenant_id, site_id, head, request, compose)
        if result["replayed"]:
            if result["request"]["payload_sha256"] != digest:
                raise ActionRefused(409, "VERIFICATION_IDEMPOTENCY_CONFLICT",
                                    "This idempotency key already requested a different evaluation.")
            return 200, {"label": LABEL, "replayed": True, "request_id": str(result["request"]["id"]),
                         "state": SETTLED, "outcome": self._outcome_wire(result["outcome"], site_code)}
        body: dict[str, Any] = {"label": LABEL, "replayed": False, "request_id": str(result["request"]["id"]),
                                "state": result.get("state"), "reasons": result.get("reasons", []),
                                "withdrawn": result.get("withdrawn", False), "resolved": result.get("resolved", False),
                                "outcome": None}
        if result.get("outcome") is not None:
            if result.get("new_outcome") and result["outcome"]["outcome"] in COST_CHECK_OUTCOMES:
                self._after_new_outcome(tenant_id, site_id, head, result["outcome"], request)
            body["outcome"] = self._outcome_wire(result["outcome"], site_code)
            return (201 if result.get("new_outcome") else 200), body
        return 200, body

    # ---- OUT-E E3: the cost check after a final outcome (hook only; no route) ---------------------------------

    def _window_replay(self, tenant_id: UUID, site_id: UUID, plan: dict[str, Any],
                outcome: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        """The evaluator's own windows, comparability and source pair at `known_at = outcome.recorded_at`."""
        windows = self._windows(tenant_id, site_id, plan, outcome["recorded_at"])
        comparable = rules.comparability(windows["baseline"], windows["later"])
        provenance = self._ports().provenance
        sources = {name: None if provenance is None or not w["evidence_ids"] else _source_wire(
            provenance(tenant_id, site_id, list(w["evidence_ids"]))) for name, w in windows.items()}
        return windows, comparable, rules.source_pair(sources["baseline"], sources["later"])

    def _cost_check(self, tenant_id: UUID, site_id: UUID, plan: dict[str, Any], outcome: dict[str, Any],
                    request: dict[str, Any]) -> dict[str, Any] | None:
        """Compute and append the modelled cost check of one newly inserted final outcome, in its own transaction,
        with the evaluation's SYSTEM demo actor and key `auto:{outcome_id}`. Never touches the outcome."""
        ports = self._ports().trial_comparison
        if ports is None:
            return None
        from assetops_backend.financials import trial_fuel_comparison as tfc

        windows, comparable, source = self._window_replay(tenant_id, site_id, plan, outcome)
        basis = outcome["basis"]

        def facts(name: str) -> Any:
            w = windows[name]
            return tfc.WindowFacts(tuple(w["evidence_ids"]), bool(w["complete"]),
                                   rules.parse_exact(w.get("generator_kwh")),
                                   rules.parse_exact(w.get("feeder_demand_kwh")), plan[f"{name}_start"],
                                   plan[f"{name}_end"], w.get("generator_idle_seconds"))

        facts_out = tfc.OutcomeFacts(str(outcome["id"]), str(plan["id"]), str(basis["origin_finding_revision_id"]),
                                     outcome["outcome"], {n: tuple(basis["evidence_ids"].get(n) or ())
                                                          for n in tfc.WINDOWS},
                                     comparable["state"], source["state"])
        now = self.clock()
        generators = list((plan["basis"].get("baseline_bindings") or {}).get("role_assets", {})
                          .get("generator_power") or [])
        sfc = [] if len(generators) != 1 else self.store.sfc_history(
            tenant_id, site_id, generators[0], plan["baseline_start"], plan["later_end"], now)
        # FUEL-1 A2: the generator's declared no-load fuel rate history, read beside the SFC history
        no_load = [] if len(generators) != 1 else self.store.no_load_history(
            tenant_id, site_id, generators[0], plan["baseline_start"], plan["later_end"], now)
        prices = tuple(ports.price_selection(tenant_id, site_id, plan[f"{n}_start"], plan[f"{n}_end"], now)
                       for n in tfc.WINDOWS)
        cost = tfc.InterventionCost(Fraction(0), None, COST_CHECK_SOURCE)
        result = tfc.compare(facts("baseline"), facts("later"), facts_out, sfc, prices, cost, no_load)
        key = f"auto:{outcome['id']}"
        # CC-D2: the body without the idempotency key (the hook's body: outcome and intervention cost)
        payload = {"outcome_id": str(outcome["id"]), "intervention_cost": result["intervention_cost"]}
        row = {"tenant_id": tenant_id, "site_id": site_id, "action_id": outcome["action_id"],
               "verification_outcome_id": outcome["id"], "formula": result["formula"], "state": result["state"],
               "reason": result["reason"], "result": result, "intervention_cost": result["intervention_cost"],
               "price_revision_id": None if result["price"] is None else result["price"]["revision_id"],
               "basis_sha256": result["basis_sha256"], "actor_kind": request["actor_kind"],
               "actor_id": request["actor_id"], "source_channel": request["source_channel"],
               "authorization_basis": request["authorization_basis"],
               "triggering_service": request["triggering_service"],
               "triggering_fixture": request["triggering_fixture"], "idempotency_key": key,
               "payload_sha256": reserve_trial.sha(payload), "recorded_at": now}
        stored, _ = ports.store.append(row)
        return stored

    def _after_new_outcome(self, tenant_id: UUID, site_id: UUID, plan: dict[str, Any], outcome: dict[str, Any],
                           request: dict[str, Any]) -> None:
        """Any failure appends nothing and is logged; the recorded outcome is never rolled back."""
        try:
            self._cost_check(tenant_id, site_id, plan, outcome, request)
        except Exception:  # noqa: BLE001 - the cost check never undoes or fails the evaluation
            LOG.exception("Cost check after outcome %s was not recorded", outcome.get("id"))

    # ---- current state, outcome and history reads ---------------------------------------------------------------

    def _outcome_wire(self, outcome: dict[str, Any] | None, site_code: str) -> dict[str, Any] | None:
        if outcome is None:
            return None
        out = _wire({k: v for k, v in outcome.items() if k not in ("tenant_id", "site_id")})
        out["outcome_id"] = out.pop("id")
        base = f"/api/sites/{site_code}/actions/{out['action_id']}/verification"
        out["links"] = {"outcome": f"{base}/outcome?outcome_id={out['outcome_id']}",
                        "plan": f"{base}/plan?plan_id={out['plan_id']}"}
        return out

    def current_state(self, tenant_id: UUID, site_id: UUID, action_id: UUID,
                      at: datetime | None = None) -> dict[str, Any]:
        """The latest current verification read state: NO_PLAN, PENDING, REASSESSMENT_PENDING or the latest
        outcome. Late accepted evidence, a moved/non-current S3 or S4 basis or a changed covering Foundation makes a
        stored outcome REASSESSMENT_PENDING immediately (the outcome stays addressable). `at` reads history."""
        plans = [p for p in self.store.plans(tenant_id, site_id, action_id) if at is None or p["recorded_at"] <= at]
        if not plans:
            return {"state": "NO_PLAN", "reasons": [], "plan_id": None, "outcome_id": None,
                    "statement": "No verification plan is frozen for this Action."}
        superseded = {p["supersedes_plan_id"] for p in plans if p["supersedes_plan_id"]}
        head = [p for p in plans if p["id"] not in superseded][-1]
        outcomes = [o for o in self.store.outcomes(tenant_id, site_id, action_id)
                    if at is None or o["recorded_at"] <= at]
        latest = outcomes[-1] if outcomes else None
        base = {"plan_id": str(head["id"]), "outcome_id": None, "last_outcome": None}
        if latest is None or latest["plan_id"] != head["id"]:
            now = at or self.clock()
            reasons = ["LATER_WINDOW_OPEN"] if read_scope.within(None, head["later_end"], now) else ["NOT_EVALUATED"]
            return {**base, "state": PENDING_STATE, "reasons": reasons,
                    "statement": "No outcome for the current plan yet; PENDING is a read state, not an outcome."}
        base.update(outcome_id=str(latest["id"]), last_outcome=latest["outcome"])
        if at is not None:
            return {**base, "state": latest["outcome"], "reasons": list(latest["reasons"]), "historical": True,
                    "statement": "Historical: the outcome as recorded by the selected cutoff."}
        reasons = []
        windows = [(head["baseline_start"], head["baseline_end"]), (head["later_start"], head["later_end"])]
        late = self.store.late_evidence(tenant_id, site_id, windows, list(ROLES), latest["recorded_at"])
        reasons += [f"LATE_EVIDENCE:{e['id']}" for e in late]
        basis = latest["basis"]
        for name in ("baseline_days", "later_days"):
            for d in self._day_states(tenant_id, site_id, basis.get(name, []), require_s4=True, facts_window=(
                    head["baseline_start"], head["baseline_end"]) if name == "baseline_days" else None):
                reasons += [f"{name}:{d['day']}: {p}" for p in d["pending"] + d["moved"]]
        probes = [head["baseline_start"], head["baseline_end"] - EPSILON, head["later_start"],
                  head["later_end"] - EPSILON]
        if self.store.covering_ids(tenant_id, site_id, probes, self.clock()) != basis.get(
                "covering_foundation_revision_ids"):
            reasons.append("FOUNDATION_CHANGED")
        if reasons:
            return {**base, "state": REASSESSMENT_PENDING, "reasons": reasons,
                    "statement": ("Late evidence or a changed basis withdraws the current Verified/Resolved "
                                  "presentation until the evaluator appends a settled outcome; the earlier outcome "
                                  "stays addressable.")}
        return {**base, "state": latest["outcome"], "reasons": list(latest["reasons"]),
                "statement": "Current outcome of a simulated/authored policy trial; no causal or savings claim."}

    def outcome(self, tenant_id: UUID, site_id: UUID, site_code: str, action_id: UUID,
                outcome_id: UUID | None = None, recorded_at: datetime | None = None) -> dict[str, Any]:
        if self.store.action(tenant_id, site_id, action_id) is None:
            raise ActionRefused(404, "ACTION_NOT_FOUND", "No such Action for this Site.")
        if outcome_id is not None and recorded_at is not None:
            raise ActionRefused(422, "VERIFICATION_SELECTOR_CONFLICT", "Choose one selector: outcome_id or recorded_at.")
        outcomes = self.store.outcomes(tenant_id, site_id, action_id)
        if outcome_id is not None:
            chosen = next((o for o in outcomes if o["id"] == outcome_id), None)
            if chosen is None:
                raise ActionRefused(404, "VERIFICATION_OUTCOME_NOT_FOUND", "No such verification outcome.")
        else:
            visible = [o for o in outcomes if recorded_at is None or o["recorded_at"] <= recorded_at]
            chosen = visible[-1] if visible else None
        superseded_by = {str(o["supersedes_outcome_id"]): str(o["id"]) for o in outcomes if o["supersedes_outcome_id"]}
        body = {"label": LABEL, "action_id": str(action_id),
                "selector": {"outcome_id": None if outcome_id is None else str(outcome_id),
                             "recorded_at": None if recorded_at is None else recorded_at.isoformat()},
                "current_state": self.current_state(tenant_id, site_id, action_id),
                "outcome": None, "metrics": [], "is_latest_outcome": None}
        if chosen is not None:
            body["outcome"] = self._outcome_wire({k: v for k, v in chosen.items() if k != "metrics"}, site_code)
            body["metrics"] = _wire([{k: v for k, v in m.items() if k not in ("tenant_id", "site_id")}
                                     for m in chosen["metrics"]])
            body["is_latest_outcome"] = chosen["id"] == outcomes[-1]["id"]
            body["superseded_by_outcome_id"] = superseded_by.get(str(chosen["id"]))
            if not body["is_latest_outcome"] or outcome_id is not None or recorded_at is not None:
                body["historical_label"] = "Historical: an exact earlier outcome; the current state is separate."
            fuel_value = self._fuel_value(tenant_id, site_id, chosen)
            if fuel_value is not None:
                body["fuel_value"] = fuel_value
        return body

    def _fuel_value(self, tenant_id: UUID, site_id: UUID, chosen: dict[str, Any]) -> str | None:
        """FUEL-1 A3-R G3: the trial page's money line (MOCK DEVIATION MD-FUEL-A3-1) from the chosen outcome's own
        stored trial row; None unless that outcome is VERIFIED and the row has a priced total and a shown price."""
        ports = self._ports().trial_comparison
        if chosen.get("outcome") != "VERIFIED" or ports is None:
            return None
        row = ports.store.latest(tenant_id, site_id, UUID(str(chosen["id"])))
        result = (row or {}).get("result") or {}
        pt, p = result.get("priced_total"), price_text((result.get("price") or {}).get("value"))
        if not pt or p is None:
            return None
        return FUEL_VALUE_PAGE.format(
            l=trial_litres(pt["fuel_change_l"]), amount=money_text(pt["amount"], None, pt.get("currency")), p=p,
            cur=pt.get("currency") or "",
            basis=NO_LOAD_BASIS_WORDS.get((result.get("no_load") or {}).get("basis"), NO_LOAD_BASIS_WORDS[None]))

    def history(self, tenant_id: UUID, site_id: UUID, site_code: str, action_id: UUID) -> dict[str, Any]:
        if self.store.action(tenant_id, site_id, action_id) is None:
            raise ActionRefused(404, "ACTION_NOT_FOUND", "No such Action for this Site.")
        events = [e for e in self.store.events(tenant_id, site_id, action_id)
                  if e["kind"] in (RESOLVED, RESOLUTION_WITHDRAWN)]
        return {"label": LABEL, "action_id": str(action_id),
                "current_state": self.current_state(tenant_id, site_id, action_id),
                "plans": [{"plan_id": str(p["id"]), "supersedes_plan_id": _wire(p["supersedes_plan_id"]),
                           "recorded_at": _wire(p["recorded_at"])}
                          for p in self.store.plans(tenant_id, site_id, action_id)],
                "evaluation_requests": _wire([{k: r[k] for k in ("id", "plan_id", "idempotency_key", "recorded_at",
                                                                  "triggering_fixture")}
                                              for r in self.store.evaluation_requests(tenant_id, site_id, action_id)]),
                "outcomes": [{**{k: v for k, v in (self._outcome_wire(
                    {k: v for k, v in o.items() if k not in ("metrics", "basis", "details")}, site_code) or {}).items()}}
                    for o in self.store.outcomes(tenant_id, site_id, action_id)],
                "resolution_events": _wire([{k: e[k] for k in ("id", "kind", "recorded_at", "verification_plan_id",
                                                                "verification_outcome_id", "triggering_job",
                                                                "payload")} for e in events]),
                "statement": "RESOLVED is withdrawable, never permanent; every outcome stays addressable."}

    def summary(self, tenant_id: UUID, site_id: UUID, site_code: str, action_id: UUID) -> dict[str, Any]:
        """The verification state an Action/Recommendation/Change read exposes beside its pinned S6-01 history."""
        state = self.current_state(tenant_id, site_id, action_id)
        base = f"/api/sites/{site_code}/actions/{action_id}/verification"
        return {"label": LABEL, **state, "links": {"plan": f"{base}/plan", "outcome": f"{base}/outcome",
                                                   "history": f"{base}/history", "evidence": f"{base}/evidence"},
                **self._cost_check_read(tenant_id, site_id, action_id, state.get("outcome_id"))}

    def _cost_check_read(self, tenant_id: UUID, site_id: UUID, action_id: UUID,
                         outcome_id: str | None) -> dict[str, Any]:
        """OUT-E E4 (additive): the stored cost check and the two trial hours' stored avoidable-generator seconds of
        the outcome the current state names; both null when there is none. Never recomputed on read."""
        if outcome_id is None:
            return {"cost_check": None, "trial_hours": None, "source_class": None}
        ports = self._ports().trial_comparison
        row = None if ports is None else ports.store.latest(tenant_id, site_id, UUID(str(outcome_id)))
        cost = None
        if row is not None:
            change = (row["result"] or {}).get("change_per_demand_kwh") or {}
            price = (row["result"] or {}).get("price") or {}
            # FUEL-1 A2 (additive): the stored priced total of a `/2` MODELLED_IMPROVEMENT, else None
            cost = {"state": row["state"], "reason": row["reason"], "nominal": change.get("nominal"),
                    "upper": change.get("upper"), "currency": price.get("currency"),
                    "recorded_at": _wire(row["recorded_at"]),
                    "priced_total": (row["result"] or {}).get("priced_total")}
            if cost["priced_total"] is not None:  # FUEL-1 A3-R G2: the stored shared price, never amount / litres
                cost["price_per_litre"] = price.get("value")
        outcome = next((o for o in self.store.outcomes(tenant_id, site_id, action_id)
                        if str(o["id"]) == str(outcome_id)), None)
        seconds: dict[str, int | None] = {"BASELINE": None, "LATER": None}
        for m in (outcome or {}).get("metrics") or ():
            known = m["window_name"] in seconds and m["value_text"] is not None
            if m["metric_key"] == "candidate_avoidable_seconds" and known:
                seconds[m["window_name"]] = int(m["value_text"])
        # CH-3 §5 (I-11, additive): the later window the outcome's plan judged, so the board states its scope.
        plan = next((p for p in self.store.plans(tenant_id, site_id, action_id)
                     if outcome is not None and str(p["id"]) == str(outcome.get("plan_id"))), None)
        # CH5a2-R R2 (CH-5a2b, additive): the selected outcome's stored source class (`details.source.source_class`,
        # written on evaluate); never derived on read. None without an outcome or a stored class.
        source_class = (((outcome or {}).get("details") or {}).get("source") or {}).get("source_class")
        return {"cost_check": cost, "source_class": source_class,
                "trial_hours": {"before_seconds": seconds["BASELINE"], "after_seconds": seconds["LATER"],
                                "later_start": None if plan is None else _wire(plan["later_start"]),
                                "later_end": None if plan is None else _wire(plan["later_end"])}}


def _source_wire(resolution: dict[str, Any]) -> dict[str, Any]:
    return _wire({k: resolution.get(k) for k in ("state", "reasons", "publication_ids", "source_classes", "fixtures",
                                                  "runs", "problematic_accepted_evidence_ids")})
