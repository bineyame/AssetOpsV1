"""CH-3 §4: `run_lifecycle` reads a Site's lifecycle causes and appends the planned thread events through the CH-2
thread store (insert-only, the sole writer). Backfill step (d) and the tick's `chain_threads` stage both call it;
the time-based causes (INCONCLUSIVE_EXPIRED, CLEAN_DAYS) are evaluated on every run.

Causes (build sheet §4), each keyed for idempotency on `(cause_kind, cause_id)`:
- ACTION_EVENT: a mini Action's ACCEPTED / APPLIED / RESOLUTION_WITHDRAWN `action_event` (id), or a domain Action
  raised (the `domain_action` id; ACCEPTED);
- VERIFICATION_OUTCOME: VERIFIED / INEFFECTIVE (outcome id), and INCONCLUSIVE_EXPIRED for a latest INCONCLUSIVE outcome
  whose plan `later_end + inconclusive_expiry_days` is before the database time;
- DOMAIN_CASE: a COMPLETE `work_event` on a case linked to a domain Action (APPLIED);
- OCCURRENCE: an occurrence placed with no event (backfill order), so a story-time recurrence still reads RECURRED;
- SUPPORT_LOST: every occurrence's latest Finding revision is NO_LONGER_SUPPORTED;
- CLEAN_DAYS: planned by `plan_lifecycle` from the COMPLETE snapshot days.

Each cause carries its fact's own recorded time as `known_at`, written as the event's `cause_known_at` (CH3-R D-b,
0045); a CLEAN_DAYS close has no single fact and keeps the event's own `recorded_at`.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Sequence
from uuid import UUID

from assetops_backend.chain import lifecycle as lc
from assetops_backend.chain.threads import OPP_MECHANISM


def _day(at: datetime | None, tz: str) -> date | None:
    return None if at is None else lc.local_day(at, tz)


def causes_for_site(inputs: dict[str, Any], policy: lc.LifecyclePolicy) -> list[lc.Cause]:
    """Every cause the Site's stored rows give, before the per-thread link and segment filters."""
    tz, now = inputs["tz"], inputs["now"]
    out: list[lc.Cause] = []
    for e in inputs["action_events"]:
        kind = e["kind"]
        cause = {"ACCEPTED": lc.ACTION_ACCEPTED, "APPLIED": lc.ACTION_APPLIED,
                 "RESOLUTION_WITHDRAWN": lc.RESOLUTION_WITHDRAWN}[kind]
        at = e["effective_from"] if kind == "APPLIED" and e.get("effective_from") is not None else e["recorded_at"]
        out.append(lc.Cause(cause, "ACTION_EVENT", str(e["id"]), lc.local_day(at, tz), e["recorded_at"],
                            str(e["action_id"]), e["recorded_at"]))
    latest: dict[str, dict[str, Any]] = {}
    for o in inputs["outcomes"]:
        if not o["superseded"]:
            prior = latest.get(str(o["action_id"]))
            if prior is None or (o["recorded_at"], str(o["id"])) > (prior["recorded_at"], str(prior["id"])):
                latest[str(o["action_id"])] = o
        if o["outcome"] in ("VERIFIED", "INEFFECTIVE") and not o["superseded"]:
            # CH3-R M1: a superseded outcome (another outcome's `supersedes_outcome_id`) gives no cause.
            at = o["effective_from"] if o["outcome"] == "VERIFIED" and o.get("effective_from") else o["recorded_at"]
            out.append(lc.Cause(lc.VERIFIED if o["outcome"] == "VERIFIED" else lc.INEFFECTIVE, "VERIFICATION_OUTCOME",
                                str(o["id"]), lc.local_day(at, tz), o["recorded_at"], str(o["action_id"]),
                                o["recorded_at"]))
    for aid, o in latest.items():
        if o["outcome"] == "INCONCLUSIVE" and o.get("later_end") is not None:
            expiry = o["later_end"] + timedelta(days=policy.inconclusive_expiry_days)
            if expiry < now:
                # Known once both the outcome is recorded and its expiry has passed (CH3-R D-b).
                out.append(lc.Cause(lc.INCONCLUSIVE_EXPIRED, "VERIFICATION_OUTCOME", str(o["id"]),
                                    lc.local_day(expiry, tz), o["recorded_at"], aid, max(o["recorded_at"], expiry)))
    for d in inputs["domain_actions"]:
        out.append(lc.Cause(lc.ACTION_ACCEPTED, "ACTION_EVENT", str(d["id"]), lc.local_day(d["recorded_at"], tz),
                            d["recorded_at"], str(d["id"]), d["recorded_at"]))
    for w in inputs["case_completions"]:
        out.append(lc.Cause(lc.ACTION_APPLIED, "DOMAIN_CASE", str(w["id"]), lc.local_day(w["occurred_at"], tz),
                            w["recorded_at"], str(w["action_id"]), w["recorded_at"]))
    return out


def thread_causes(thread: dict[str, Any], site_causes: Sequence[lc.Cause], inputs: dict[str, Any]) -> list[lc.Cause]:
    """The causes of one thread: its linked Actions' causes, its occurrences with no event, and SUPPORT_LOST."""
    tz = inputs["tz"]
    linked = thread["links"]
    out = [c for c in site_causes if c.action_id in linked]
    with_event = {e.cause_id for e in thread["events"] if e.cause_kind == "OCCURRENCE"}
    known = thread.get("occurrence_known", {})  # source id -> the revision's created_at (0045 `source_known_at`)
    for source_id, start in thread["occurrences"]:
        if source_id not in with_event and start is not None:
            out.append(lc.Cause(lc.OCCURRENCE, "OCCURRENCE", source_id, lc.local_day(start, tz), start,
                                known_at=known.get(source_id)))
    revs = [inputs["finding_lifecycle"].get(source_id) for source_id, _ in thread["occurrences"]]
    if revs and all(r is not None and r["lifecycle"] == "NO_LONGER_SUPPORTED" for r in revs):
        last = max(revs, key=lambda r: (r["created_at"], str(r["revision_id"])))  # type: ignore[union-attr]
        out.append(lc.Cause(lc.SUPPORT_LOST, "SUPPORT_LOST", str(last["revision_id"]),  # type: ignore[index]
                            lc.local_day(last["created_at"], tz), last["created_at"],  # type: ignore[index]
                            known_at=last["created_at"]))  # type: ignore[index]
    # CH4-R R6: an opportunity thread whose every occurrence's selected head revision now has 0 eligible days,
    # with no linked Action, has lost its support (cause id = the latest such revision, known at its created_at).
    heads = inputs.get("opportunity_heads") or {}
    opp = [heads.get(source_id) for source_id, _ in thread["occurrences"]]
    if (thread.get("mechanism") == OPP_MECHANISM and opp and not linked
            and all(h is not None and int(h["eligible_days"] or 0) == 0 for h in opp)):
        last = max(opp, key=lambda h: (h["created_at"], str(h["revision_id"])))  # type: ignore[union-attr]
        out.append(lc.Cause(lc.SUPPORT_LOST, "SUPPORT_LOST", str(last["revision_id"]),  # type: ignore[index]
                            lc.local_day(last["created_at"], tz), last["created_at"],  # type: ignore[index]
                            known_at=last["created_at"]))  # type: ignore[index]
    return out


def thread_clean_days(thread: dict[str, Any], inputs: dict[str, Any], policy: lc.LifecyclePolicy) -> set[date]:
    tz = inputs["tz"]
    measures = policy.measures_for(thread["mechanism"])
    started = [lc.local_day(start, tz) for _, start in thread["occurrences"] if start is not None]
    return lc.fully_checked_days(inputs["snapshots"], thread["subject_ref"], measures, started)


def run_lifecycle(reader: Any, store: Any, tenant_id: UUID, site_id: UUID | None,
                  policy: lc.LifecyclePolicy | None = None) -> dict[str, Any]:
    """Step (d) for one Site, or every Site of the tenant when `site_id` is None. Returns the step report."""
    if policy is None:
        from assetops_backend.chain.composition import thread_lifecycle_policy
        policy = thread_lifecycle_policy()
    sites = [sid for sid, _ in reader.site_ids(tenant_id)] if site_id is None else [site_id]
    counts: dict[str, int] = {}
    skipped: list[dict[str, Any]] = []
    states: list[dict[str, Any]] = []
    for sid in sites:
        threads = store.site_threads(tenant_id, sid)
        if not threads:
            continue
        inputs = reader.lifecycle_inputs(tenant_id, sid)
        site_causes = causes_for_site(inputs, policy)
        close_after = policy.close_after(inputs.get("site_type"))  # L2: the per-Site-type override
        for t in threads:
            causes = thread_causes(t, site_causes, inputs)
            clean = thread_clean_days(t, inputs, policy)

            def planner(existing: Sequence[lc.Event], t: dict[str, Any] = t) -> lc.LifecyclePlan:
                occs = [lc.Occurrence(s, _day(st, inputs["tz"])) for s, st in t["occurrences"]]
                return lc.plan_lifecycle(str(t["id"]), existing, occs, t["links"], causes,
                                         close_after=close_after, clean_days=clean)

            plan = store.append_events(tenant_id, sid, t, planner, policy.policy_version)
            for e in plan.events:
                counts[e.state] = counts.get(e.state, 0) + 1
            skipped += plan.skipped
            final = store.thread_head(t["id"])
            states.append({"site_id": str(sid), "thread_id": str(t["id"]), "mechanism": t["mechanism"],
                           "state": final[0], "effective_day": None if final[1] is None else final[1].isoformat()})
    return {"step": "d", "counts": dict(sorted(counts.items())), "written": sum(counts.values()),
            "skipped": len(skipped), "skipped_causes": skipped, "threads": states}
