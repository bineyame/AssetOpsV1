"""W3-01 per-Site estate coverage and selected rows, inside the one estate REPEATABLE READ snapshot (pure).

`site_coverage(snapshot, tenant_id, site_id, domain, from_, to, known_at)` (Review closure 2, W5) reduces one
authorized Site's selected read for one domain to `{selection_id, match_state, job_state, source_freshness, state}`
plus the full selected-ID arrays of the `estate-selection/2` token and the selected rows. `snapshot` is the bound
read of `estate/adapters/postgres_estate_read.py`: every call it makes runs on the estate connection; nothing here
opens a connection, reads a page or writes.

Rulings applied: Run 6 Blocker 1 (cold/EV exact selected windows intersecting the estate day), Blocker 2 (mini-grid
money gates), readings 4-9 (historical, mini-grid currentness, unsettled rows, Action coverage and reduce) and
Run 7 q7-1 (the requested cutoff and the Site evidence cutoff are separate).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from assetops_backend.actions import lifecycle
from assetops_backend.evidence.provenance_read import source_gate
from assetops_backend.estate.scope import EstateSelectionInconsistent
from assetops_backend.evidence.public_provenance import estate_projection

MINI_GRID, COLD, EV, ACTIONS = "mini_grid", "cold_chain", "ev_charging", "actions"
DOMAIN_OF_SITE_TYPE = {"MINIGRID": MINI_GRID, "COLDCHAIN": COLD, "EV_CHARGING": EV}
CURRENT, PENDING, STALE, HISTORICAL, UNKNOWN, NOT_APPLICABLE = (
    "CURRENT", "PENDING_RECOMPUTE", "STALE_SOURCE", "HISTORICAL", "UNKNOWN", "NOT_APPLICABLE")
COVERED = (CURRENT, HISTORICAL)
_S3_CURRENT, _S3_PENDING, _S3_STALE, _S3_FAILED = "CURRENT", "PENDING", "STALE_PROJECTION", "FAILED"
VERIFIED_LOOKBACK = timedelta(days=30)


def _empty(state: str, **values: Any) -> dict[str, Any]:
    out = {"selection_id": None, "watermark": None, "match_state": "MISSING", "job_state": "NONE",
           "source_freshness": "UNKNOWN", "state": state, "rows": [],
           "selected_finding_revision_ids": [], "selected_action_event_ids": [],
           "selected_assessment_revision_ids": [], "selected_consequence_revision_ids": [],
           "selected_assumption_revision_ids": [], "cited_accepted_evidence_ids": []}
    out.update(values)
    return out


def site_coverage(snapshot: Any, tenant_id: Any, site_id: Any, domain: str, from_: datetime, to: datetime,
                  known_at: datetime) -> dict[str, Any]:
    """One Site's coverage for one estate domain at the requested cutoff `known_at`."""
    if domain == MINI_GRID:
        return _mini_grid(snapshot, tenant_id, site_id, from_, to, known_at)
    if domain in (COLD, EV):
        return _windowed(snapshot, tenant_id, site_id, domain, from_, to, known_at)
    if domain == ACTIONS:
        return _actions(snapshot, tenant_id, site_id, from_, to, known_at)
    raise ValueError(f"No estate coverage for domain {domain!r}.")


def _job_state(statuses: set[str], selected: bool) -> str:
    if "FAILED" in statuses:
        return "FAILED"
    if statuses & {"PENDING", "LEASED"}:
        return "PENDING"
    return "SETTLED" if selected else "NONE"


def _intersects(start: datetime | None, end: datetime | None, from_: datetime, to: datetime,
                known_at: datetime) -> bool:
    """The estate episode test `start < to AND end > from`; a null end is open through `known_at`."""
    if start is None:
        return False
    return start < to and (known_at if end is None else end) > from_


# --- mini-grid --------------------------------------------------------------------------------------------

def _mini_grid(snapshot: Any, t: Any, s: Any, from_: datetime, to: datetime, k: datetime) -> dict[str, Any]:
    historical = snapshot.historical
    watermark = snapshot.evidence_cutoff(t, s, k)
    days = snapshot.dispatch_days(t, s, from_, to, k)
    index = snapshot.finding_index(t, s, k)
    match_pass = index.get("match_pass")
    deferred = set(index.get("deferred_windows") or ())
    unknown = pending = stale = unmatched = False
    provable = True
    statuses: set[str] = set()
    selected_days = []
    for day in days:
        day_jobs = {j.get("status") for j in day.get("jobs") or ()}
        statuses |= day_jobs
        if day_jobs & {"PENDING", "LEASED", "FAILED"}:
            # q5 ruling 5 / spec "Selection rule": overlapping PENDING/LEASED/FAILED work is PENDING_RECOMPUTE,
            # ahead of the day's S3 STALE (late accepted evidence marks current coverage pending).
            pending = True
        selection = day.get("selection")
        if not day.get("available") or selection is None:
            unknown, provable = True, False
            continue
        selected_days.append(day)
        matched = (match_pass is not None and match_pass["matched_through_selection_seq"] >= int(selection["seq"])
                   and day.get("window_start") not in deferred)
        if not matched:
            unmatched, pending, provable = True, True, False
        if day.get("status") in (_S3_PENDING, _S3_FAILED):
            pending = True
        elif day.get("status") == _S3_STALE:
            stale = True
        elif day.get("status") != _S3_CURRENT:
            unknown = True
    match_state = "MISSING" if match_pass is None or not selected_days else "PENDING" if unmatched else "COMPLETE"
    freshness = "UNKNOWN" if unknown or not selected_days else "STALE" if stale else "RECENT"
    if historical:
        # Reading 4: a provable as-of selection is HISTORICAL; an outstanding marker stays in job_state only.
        state = HISTORICAL if provable and days else UNKNOWN
    else:
        state = UNKNOWN if unknown or not days else PENDING if pending else STALE if stale else CURRENT
    last = max(selected_days, key=lambda d: d["window_start"], default=None)
    out = _empty(state, watermark=watermark, match_state=match_state,
                 job_state=_job_state(statuses, bool(selected_days)), source_freshness=freshness,
                 selection_id=None if last is None else last.get("window_assessment_revision_id"))
    assessments = set()
    for day in selected_days:
        assessments |= {str(x) for x in day.get("assessment_revision_ids") or ()}
        if day.get("window_assessment_revision_id") is not None:
            assessments.add(str(day["window_assessment_revision_id"]))
    out["selected_assessment_revision_ids"] = sorted(assessments)
    if state not in COVERED:  # reading 6: mini-grid rows only from a CURRENT or provable HISTORICAL Site
        return out
    heads = [h for h in index.get("heads") or () if h.get("merged_into_finding_id") is None
             and _intersects(h.get("episode_start"), h.get("episode_end"), from_, to, k)]
    lineage = snapshot.finding_lineage(t, s, [h["finding_revision_id"] for h in heads], k) if heads else {}
    cited_by: dict[str, list[str]] = {}
    for row in lineage.get("evidence") or ():
        cited_by.setdefault(str(row["finding_revision_id"]), []).append(str(row["evidence_id"]))
    for row in lineage.get("assessments") or ():
        assessments.add(str(row["assessment_revision_id"]))
    cited, consequences, assumptions = set(), set(), set()
    rows = []
    for h in heads:
        frid = str(h["finding_revision_id"])
        cited |= set(cited_by.get(frid, ()))
        consequence = _mini_grid_money(snapshot, t, s, h, k, historical, cited_by.get(frid, []))
        if consequence.pop("_id", None) is not None:
            consequences.add(consequence["source_revision_id"])
        assumptions |= set(consequence.pop("_assumptions", ()))
        cited |= set(consequence.pop("_cited", ()))
        rows.append({"finding_id": str(h["finding_id"]), "finding_revision_id": frid,
                     "episode_start": h["episode_start"], "title": h.get("title"), "lifecycle": h.get("lifecycle"),
                     "consequence": consequence,
                     "source_provenance": snapshot.finding_provenance(t, s, frid, cited_by.get(frid, []))})
    out.update(rows=rows, selected_finding_revision_ids=sorted(r["finding_revision_id"] for r in rows),
               selected_assessment_revision_ids=sorted(assessments), cited_accepted_evidence_ids=sorted(cited),
               selected_consequence_revision_ids=sorted(consequences),
               selected_assumption_revision_ids=sorted(assumptions))
    return out


def _consequence(state: str, source_revision_id: Any = None, **extra: Any) -> dict[str, Any]:
    """Finding wire v2 (Run 8 ruling 3): `amount_low`/`amount_high` are the stored interval bounds for PRICED, both
    null otherwise; `amount` is the compatibility alias of `amount_low`; neither bound is a point estimate."""
    return {"state": state, "amount": None, "amount_low": None, "amount_high": None, "currency": None,
            "source_revision_id": None if source_revision_id is None else str(source_revision_id), **extra}


def _mini_grid_money(snapshot: Any, t: Any, s: Any, head: dict[str, Any], k: datetime, historical: bool,
                     finding_cited: list[str]) -> dict[str, Any]:
    """Run 6 Blocker 2: PRICED (and the COST flag) only for a CURRENT, ELIGIBLE, source-permitted exact selected
    consequence at the live cutoff; an unpriced stored row is UNPRICED; any other selected row is UNKNOWN with its
    revision ID; no stored row is UNPRICED with a null source (`No consequence recorded`)."""
    selected = snapshot.consequence(t, s, head["finding_revision_id"], k)
    cid = selected.get("consequence_revision_id")
    if cid is None:
        return _consequence("UNPRICED")
    cited = selected.get("cited") or {}
    extra = {"_id": cid, "_assumptions": [str(x) for x in cited.get("assumption_revision_ids") or ()],
             "_cited": [str(x) for x in cited.get("power_evidence_ids") or ()]}
    if selected.get("consequence_state") != "PRICED":
        return _consequence("UNPRICED", cid, **extra)
    if historical:  # a prior selected amount is never a current-money claim
        return _consequence("UNKNOWN", cid, **extra)
    block = snapshot.consequence_provenance(t, s, cid, head["finding_revision_id"],
                                            sorted({*finding_cited, *extra["_cited"]}))
    gate = source_gate(estate_projection(block))
    eligible = snapshot.eligibility(t, s, head["finding_id"], k).get("state") == "ELIGIBLE"
    low, high, currency = selected.get("amount_low"), selected.get("amount_high"), selected.get("currency")
    current = (selected.get("currentness") or {}).get("state") == "CURRENT"
    shaped = (low is not None and high is not None and isinstance(currency, str) and len(currency) == 3
              and currency.isupper() and _decimal(low) <= _decimal(high))
    if not (current and eligible and gate["permits_current_money"] and shaped):
        return _consequence("UNKNOWN", cid, **extra)
    out = _consequence("PRICED", cid, **extra)
    out.update(amount=str(low), amount_low=str(low), amount_high=str(high), currency=currency)
    return out


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value))


# --- cold and EV ------------------------------------------------------------------------------------------

def _windowed(snapshot: Any, t: Any, s: Any, domain: str, from_: datetime, to: datetime,
              k: datetime) -> dict[str, Any]:
    """Run 6 Blocker 1 and Run 7: the exact selected windows intersecting the estate day, pinned at the requested
    cutoff with the Site evidence cutoff as the W2 `known_at`; no window is UNKNOWN, never a zero."""
    evidence_cutoff = snapshot.evidence_cutoff(t, s, k)
    if evidence_cutoff is None:
        return _empty(UNKNOWN, source_freshness="NOT_APPLICABLE" if domain == EV else "UNKNOWN")
    windows = snapshot.selected_windows(t, s, domain, from_, to, evidence_cutoff, k)
    jobs = set() if snapshot.historical else set(snapshot.open_jobs(t, s, domain, from_, to, k))
    freshness = "NOT_APPLICABLE" if domain == EV else "UNKNOWN"
    if not windows:
        return _empty(UNKNOWN, watermark=evidence_cutoff, job_state=_job_state(jobs, False),
                      source_freshness=freshness)
    states = {w["state"] for w in windows}
    stale_probe = domain == COLD and any(w.get("probe_fresh") is False for w in windows)
    if domain == COLD:
        freshness = "STALE" if stale_probe else "UNKNOWN" if any(w.get("probe_fresh") is None for w in windows) \
            else "RECENT"
    if snapshot.historical:
        state = HISTORICAL
    elif jobs or PENDING in states:
        state = PENDING
    elif stale_probe or STALE in states:
        state = STALE
    elif UNKNOWN in states:
        state = UNKNOWN
    else:
        state = CURRENT
    latest = max(windows, key=lambda w: (w["selected_at"], w["seq"], w["selection_id"]))
    out = _empty(state, watermark=evidence_cutoff, match_state="NOT_APPLICABLE",
                 job_state=_job_state(jobs, True), source_freshness=freshness, selection_id=latest["selection_id"])
    by_finding: dict[str, dict[str, Any]] = {}
    assessments, cited, consequences = set(), set(), set()
    for w in windows:
        assessments |= set(w["assessment_revision_ids"])
        cited |= set(w["evidence_ids"])
        for row in w["findings"]:
            if not _intersects(row["episode_start"], row["episode_end"], from_, to, k):
                continue
            held = by_finding.get(row["finding_id"])
            if held is not None and held["finding_revision_id"] != row["finding_revision_id"]:
                raise EstateSelectionInconsistent(
                    f"Finding {row['finding_id']} has two selected revisions at one cutoff.")
            by_finding[row["finding_id"]] = row
    rows = []
    for row in by_finding.values():
        cited |= set(row["evidence_ids"])
        if row.get("consequence_revision_id") is not None:
            consequences.add(row["consequence_revision_id"])
        rows.append({"finding_id": row["finding_id"], "finding_revision_id": row["finding_revision_id"],
                     "episode_start": row["episode_start"], "title": row["title"], "lifecycle": row["lifecycle"],
                     "consequence": _consequence("UNPRICED", row.get("consequence_revision_id")),
                     "source_provenance": row["source_provenance"]})
    out.update(rows=rows, selected_finding_revision_ids=sorted(r["finding_revision_id"] for r in rows),
               selected_assessment_revision_ids=sorted(assessments), cited_accepted_evidence_ids=sorted(cited),
               selected_consequence_revision_ids=sorted(consequences))
    return out


# --- Actions ----------------------------------------------------------------------------------------------

def _actions(snapshot: Any, t: Any, s: Any, from_: datetime, to: datetime, k: datetime) -> dict[str, Any]:
    """Reading 8/9: a mini-grid Site's Actions created in `[from, to)` by `k`, each at its latest event by `k`,
    reduced over the complete ordered prefix. Coverage is CURRENT (HISTORICAL at an explicit earlier cutoff)."""
    window = snapshot.actions(t, s, from_, to, k)
    events_by: dict[str, list[dict[str, Any]]] = {}
    for event in window["events"]:
        events_by.setdefault(str(event["action_id"]), []).append(event)
    actions = [a for a in window["actions"] if events_by.get(str(a["id"]))]
    ids = [a["id"] for a in actions]
    basis = snapshot.action_basis(t, s, ids) if ids else {}
    verification = snapshot.verification(t, s, ids, k) if ids else {}
    rows, events, assessments, cited_all, origins = [], [], set(), set(), set()
    for a in actions:
        aid = str(a["id"])
        prefix = lifecycle.ordered(events_by[aid])
        selected = prefix[-1]
        reduced = lifecycle.reduce(prefix)
        resolution = reduced.get("resolution")
        b = basis.get(aid) or {}
        selected_ids = [aid, str(selected["id"]), str(a["origin_finding_revision_id"]), str(b.get("primary")),
                        str(b.get("foundation")), *[str(x) for x in b.get("assessments") or ()]]
        cited = sorted({str(x).lower() for x in (b.get("evidence") or [])} |
                       {str(x).lower() for x in (b.get("origin_evidence") or [])})
        provenance = snapshot.cited_provenance(t, s, cited, selected_ids)
        v = verification.get(aid) or {}
        resolved = resolution is not None and resolution["state"] == lifecycle.RESOLVED
        verified_at = None
        if resolved and resolution.get("outcome") == "VERIFIED":
            verified_at = (v.get("outcomes") or {}).get(resolution.get("outcome_id"))
        in_window = any(p["later_start"] <= k < p["later_end"] for p in v.get("plans") or ())
        events.append(str(selected["id"]))
        assessments |= {str(b.get("primary")), *[str(x) for x in b.get("assessments") or ()]}
        cited_all |= set(cited)
        origins.add(str(a["origin_finding_revision_id"]))
        rows.append({
            "action_id": aid, "action_code": a["action_code"], "created_at": a["created_at"],
            "selected_event_id": str(selected["id"]), "source_finding_id": str(a["origin_finding_id"]),
            "source_finding_revision_id": str(a["origin_finding_revision_id"]),
            "action_title": f"Action {a['action_code']}", "success_criterion": None, "owner": None, "due_at": None,
            "application_state": reduced["application"],
            "resolution_state": None if resolution is None else resolution["state"],
            "verification_outcome": resolution.get("outcome") if resolved else None,
            "source_provenance": provenance,
            "_open": reduced["application"] in ("PENDING", "APPLIED") and not resolved,
            "_verification_window": in_window and not resolved,
            "_verified_recent": verified_at is not None and k - VERIFIED_LOOKBACK <= verified_at <= k})
    state = HISTORICAL if snapshot.historical else CURRENT
    return {"selection_id": None, "watermark": None, "match_state": "NOT_APPLICABLE",
            "job_state": "NOT_APPLICABLE", "source_freshness": "NOT_APPLICABLE", "state": state, "rows": rows,
            "selected_finding_revision_ids": sorted(origins), "selected_action_event_ids": sorted(events),
            "selected_assessment_revision_ids": sorted(assessments), "selected_consequence_revision_ids": [],
            "selected_assumption_revision_ids": [], "cited_accepted_evidence_ids": sorted(cited_all)}


def not_applicable() -> dict[str, Any]:
    """A cold/EV Site's Action coverage: NOT_APPLICABLE (B4); it stays in the authorized scope."""
    return {**_empty(NOT_APPLICABLE), "match_state": "NOT_APPLICABLE", "job_state": "NOT_APPLICABLE",
            "source_freshness": "NOT_APPLICABLE"}
