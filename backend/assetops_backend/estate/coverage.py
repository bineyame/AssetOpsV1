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

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable, Mapping
from zoneinfo import ZoneInfo

from assetops_backend import read_scope
from assetops_backend.actions import lifecycle
from assetops_backend.analytics.finding_index import DATA_GAP_REASONS, data_gap_reason, touched
from assetops_backend.evidence.provenance_read import source_gate
from assetops_backend.estate.scope import EstateSelectionInconsistent
from assetops_backend.outcomes.display_code import display_code
from assetops_backend.evidence.public_provenance import estate_projection

MINI_GRID, COLD, EV, ACTIONS = "mini_grid", "cold_chain", "ev_charging", "actions"
DOMAIN_OF_SITE_TYPE = {"MINIGRID": MINI_GRID, "COLDCHAIN": COLD, "EV_CHARGING": EV}
CURRENT, PENDING, STALE, HISTORICAL, UNKNOWN, NOT_APPLICABLE = (
    "CURRENT", "PENDING_RECOMPUTE", "STALE_SOURCE", "HISTORICAL", "UNKNOWN", "NOT_APPLICABLE")
COVERED = (CURRENT, HISTORICAL)
# COV-PARTIAL (D-2026-10-31-estate-coverage-v2): a live mini-grid period with unchecked days and clean checked days.
# Not in COVERED: no covered-Site count and no Current root. PARTIAL-MONEY (D-E5.45): its money is the lines of its
# analysed days only (`on_gap_day`; `financials.select_financial_scope`), never estimated for a gap day.
PARTIAL = "PARTIAL"
DAYS_POLICY = "estate-coverage/2"
DAYS_CHECKED = "{c} of {n} days assessed · {g} {unit} not available yet"
DAYS_WITHHELD = "; Findings next to those days are not shown yet"
_S3_CURRENT, _S3_PENDING, _S3_STALE, _S3_FAILED = "CURRENT", "PENDING", "STALE_PROJECTION", "FAILED"
VERIFIED_LOOKBACK = timedelta(days=30)


def _empty(state: str, **values: Any) -> dict[str, Any]:
    out = {"selection_id": None, "watermark": None, "match_state": "MISSING", "job_state": "NONE",
           "source_freshness": "UNKNOWN", "state": state, "rows": [],
           "selected_finding_revision_ids": [], "selected_action_event_ids": [],
           "selected_assessment_revision_ids": [], "selected_consequence_revision_ids": [],
           "selected_assumption_revision_ids": [], "cited_accepted_evidence_ids": [], "days": None}
    out.update(values)
    return out


# DATA-12 (D-E5.38): injected by `main.py` (`EstateClaims.day_grades`); None -> no `day_grades` keyword is passed and
# coverage keeps its UTC dispatch-day rule.
day_grades_provider: Callable[..., tuple[Mapping[date, str], str | None] | None] | None = None
_NO_DATA, _PENDING_GRADE, _NOT_EXPECTED = "NO_DATA", "PENDING", "NOT_EXPECTED"

# ANY-2 AR-3: injected by `main.py` (`chain.dispatch_day_rows.DispatchDayRows`): `(t, s, from_, to, k, explicit)` ->
# the stored `dispatch.day` rows as dispatch days, or None while the kind is not served (then today's compose).
dispatch_rows_provider: Callable[..., list[dict[str, Any]] | None] | None = None


def dispatch_days(snapshot: Any, t: Any, s: Any, from_: datetime, to: datetime, k: datetime) -> list[dict[str, Any]]:
    """The Site's S3 dispatch days of `[from_, to)` at `k`: stored rows when served, else the on-read compose. An
    explicit cutoff (a historical basis or a continuation page) reads the rows computed by `k`; a live page one
    reads the latest rows. (Other per-day readers of the same days, e.g. `evidence_money.mini_grid_rows`, can call
    this instead of `snapshot.dispatch_days` to read the same rows.)"""
    if dispatch_rows_provider is not None:
        explicit = bool(snapshot.basis_historical) or bool(getattr(snapshot, "continuation", False))
        days = dispatch_rows_provider(t, s, from_, to, k, explicit)
        if days is not None:
            return days
    return snapshot.dispatch_days(t, s, from_, to, k)


def local_day_grades_kw(site: Mapping[str, Any], req: Any, scope: Mapping[str, Any], tenant_id: Any) -> dict[str, Any]:
    """`{"day_grades": ..., "day_tz": ...}` for a mini-grid Site: its stored chain day grade per Site-local day of the
    request window (the frame the summary claims read) and the Site zone; `{}` for any other Site, with no provider,
    or when the read is unavailable (so `site_coverage` is called exactly as before). D-E5.43 L1: grades are read at
    `req.known_at` on page one (the claims' memo key, one `chain.day` read per Site) and at `k` on a cursor page."""
    if day_grades_provider is None or DOMAIN_OF_SITE_TYPE.get(site.get("site_type")) != MINI_GRID:
        return {}
    known_at = scope["k"] if scope.get("cursor") is not None else req.known_at
    read = day_grades_provider(tenant_id, site["site_code"], req.from_, req.to, known_at)
    return {} if read is None else {"day_grades": read[0], "day_tz": read[1]}


def site_coverage(snapshot: Any, tenant_id: Any, site_id: Any, domain: str, from_: datetime, to: datetime,
                  known_at: datetime, *, day_grades: Mapping[date, str] | None = None,
                  day_tz: str | None = None) -> dict[str, Any]:
    """One Site's coverage for one estate domain at the requested cutoff `known_at`. `day_grades` (mini-grid only)
    are the chain's Site-local day grades (D-E5.38/D-E5.42): they define the requested days, the gaps and PENDING;
    `day_tz` is the Site zone, for the Site-local day bounds of the gap-day Finding match (D-E5.43 L3)."""
    if domain == MINI_GRID:
        return _mini_grid(snapshot, tenant_id, site_id, from_, to, known_at, day_grades, day_tz)
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

def _mini_grid(snapshot: Any, t: Any, s: Any, from_: datetime, to: datetime, k: datetime,
               day_grades: Mapping[date, str] | None = None, day_tz: str | None = None) -> dict[str, Any]:
    """c2 r1 M1 and q12 ruling 1: gates, rows, arrays and the Site `state` come from page one's basis mode; a
    continuation's HISTORICAL label is the top-level response's only, never the Site coverage state."""
    return _mini_grid_basis(snapshot, t, s, from_, to, k, day_grades, day_tz)


def _mini_grid_basis(snapshot: Any, t: Any, s: Any, from_: datetime, to: datetime, k: datetime,
                     day_grades: Mapping[date, str] | None = None, day_tz: str | None = None) -> dict[str, Any]:
    historical = snapshot.basis_historical
    watermark = snapshot.evidence_cutoff(t, s, k)
    days = dispatch_days(snapshot, t, s, from_, to, k)  # AR-3: `dispatch.day` rows when served
    index = snapshot.finding_index(t, s, k)
    match_pass = index.get("match_pass")
    deferred = set(index.get("deferred_windows") or ())
    unknown = pending = stale = unmatched = gap = False
    provable = True
    statuses: set[str] = set()
    selected_days = []
    gap_days: list[date] = []
    for day in days:
        day_jobs = {j.get("status") for j in day.get("jobs") or ()}
        statuses |= day_jobs
        if day_jobs & {"PENDING", "LEASED", "FAILED"}:
            # q5 ruling 5 / spec "Selection rule": overlapping PENDING/LEASED/FAILED work is PENDING_RECOMPUTE,
            # ahead of the day's S3 STALE (late accepted evidence marks current coverage pending).
            pending = True
        selection = day.get("selection")
        if not day.get("available") or selection is None:
            # COV-PARTIAL §2.2: an unchecked day sets `gap`, not `unknown`; `provable` falls as before.
            provable = False
            if day_grades is None:
                gap = True
                gap_days.append(_day_of(day))
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
    gap_reasons: dict[date, str] | None = None
    if day_grades is not None:
        # D-E5.42: each requested Site-local day D decides on its stored grade first. NOT_EXPECTED is dropped from
        # requested and checked; NO_DATA is a NO_READINGS gap; PENDING makes the Site PENDING_RECOMPUTE; a day with
        # readings is checked only if the dispatch day with D's date has an available selection, else a NOT_ANALYSED
        # gap. Selection, match-pass and S3-status rules above are unchanged.
        analysed = {_day_of(d) for d in days if d.get("available") and d.get("selection") is not None}
        data_reasons = data_gap_days(days)
        gap_reasons = {}
        for d, g in day_grades.items():
            if g == _NOT_EXPECTED:
                continue
            if g == _NO_DATA:
                gap_reasons[d] = "NO_READINGS"
            elif g == _PENDING_GRADE:
                pending = True
            elif d not in analysed:
                gap_reasons[d] = "NOT_ANALYSED"
            elif d in data_reasons:  # D-E5.46: selected by the system, but the readings could not be analysed
                gap_reasons[d] = data_reasons[d]
        gap_days = sorted(gap_reasons)
        gap = bool(gap_days)
    match_state = "MISSING" if match_pass is None or not selected_days else "PENDING" if unmatched else "COMPLETE"
    aligned = day_grades is not None or len(days) == _requested_days(from_, to)
    if day_grades is not None:
        requested = sum(1 for g in day_grades.values() if g != _NOT_EXPECTED)
        checked = requested - len(gap_days)
    else:
        requested, checked = len(days), len(selected_days)
    # §2.3: PARTIAL only on a live, day-aligned read whose checked days are all clean. Any other gap is today's
    # rule byte for byte (C2, C4/R621, C5): the gap reads as `unknown`.
    partial = gap and aligned and not historical and bool(selected_days) and not (unknown or pending or stale)
    unknown = unknown or (gap and not partial)
    freshness = "UNKNOWN" if unknown or not selected_days else "STALE" if stale else "RECENT"
    if historical:
        # Reading 4: a provable as-of selection is HISTORICAL; an outstanding marker stays in job_state only.
        state = HISTORICAL if provable and days else UNKNOWN
    else:
        state = (UNKNOWN if unknown or not days else PENDING if pending else STALE if stale
                 else PARTIAL if partial else CURRENT)
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
    withheld = False
    if state not in COVERED and state != PARTIAL:  # reading 6: rows only from a CURRENT, PARTIAL or HISTORICAL Site
        out["days"] = _days_block(state, aligned, requested, checked, gap_days, withheld, reasons=gap_reasons)
        return out
    # POLISH Addendum 6 Q3: every head's stored title by Finding, before the window filter, so a recurrence can
    # name the earlier Finding it followed.
    head_titles = {str(h["finding_id"]): h.get("title") for h in index.get("heads") or ()}
    heads = [h for h in index.get("heads") or () if h.get("merged_into_finding_id") is None
             and _intersects(h.get("episode_start"), h.get("episode_end"), from_, to, k)]
    if state == PARTIAL:  # §2.5: drop every head that touches an unchecked day (open end read through `k`)
        # A data-fact gap (D-E5.46) holds no analysis to wait for, so it withholds nothing (as in the Finding index).
        waiting = [d for d in gap_days if gap_reasons is None or gap_reasons[d] not in DATA_GAP_REASONS]
        kept = [h for h in heads if not touched(
            {"episode_start": h["episode_start"], "episode_end": k if h.get("episode_end") is None
             else h["episode_end"]}, waiting, tz=day_tz if gap_reasons is not None else None)]
        withheld, heads = len(kept) != len(heads), kept
    out["days"] = _days_block(state, aligned, requested, checked, gap_days, withheld, reasons=gap_reasons)
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
        # PARTIAL-MONEY (D-E5.45): a PARTIAL Site's money is its analysed days' only; a head on a gap day (any
        # reason) shows no current amount and is never a money line. Nothing is estimated for the gap day.
        on_gap = state == PARTIAL and on_gap_day(h, gap_days, k, day_tz if gap_reasons is not None else None)
        consequence = _mini_grid_money(snapshot, t, s, h, k, historical, cited_by.get(frid, []), withhold=on_gap)
        if consequence.pop("_id", None) is not None:
            consequences.add(consequence["source_revision_id"])
        assumptions |= set(consequence.pop("_assumptions", ()))
        cited |= set(consequence.pop("_cited", ()))
        rows.append({"finding_id": str(h["finding_id"]), "finding_revision_id": frid,
                     "episode_start": h["episode_start"], "title": h.get("title"), "lifecycle": h.get("lifecycle"),
                     # W3-03 closure 4 B1/B2: the selected revision's stored end. CC-R2: the stored mechanism and
                     # the recurrence facts placement reads, all `.get` so fake snapshots need no new keys.
                     "episode_end": h.get("episode_end"), "mechanism": h.get("mechanism"),
                     "recurs_after_finding_id": h.get("recurs_after_finding_id"),
                     "recurs_after_title": (None if h.get("recurs_after_finding_id") is None
                                            else head_titles.get(str(h["recurs_after_finding_id"]))),
                     "revision_no": h.get("revision_no"), "transition": h.get("transition"),
                     "consequence": consequence, "_on_gap_day": on_gap,
                     "source_provenance": snapshot.finding_provenance(t, s, frid, cited_by.get(frid, []))})
    out.update(rows=rows, selected_finding_revision_ids=sorted(r["finding_revision_id"] for r in rows),
               selected_assessment_revision_ids=sorted(assessments), cited_accepted_evidence_ids=sorted(cited),
               selected_consequence_revision_ids=sorted(consequences),
               selected_assumption_revision_ids=sorted(assumptions))
    return out


def on_gap_day(head: Mapping[str, Any], gaps: list[date], k: datetime, tz: str | None) -> bool:
    """PARTIAL-MONEY: the episode `[start, end)` (open end read through `k`) overlaps a gap day's own bounds, the
    Site-local midnights when `tz` is given, else UTC. No continuity tolerance: a line wholly on an analysed day is
    that day's money; the waiting-gap tolerance (`touched`) has already dropped the heads next to NOT_ANALYSED days."""
    zone = ZoneInfo(tz) if tz else timezone.utc
    start, end = head["episode_start"], k if head.get("episode_end") is None else head["episode_end"]
    for d in gaps:
        lo = datetime.combine(d, time(0), tzinfo=zone).astimezone(timezone.utc)
        hi = datetime.combine(d + timedelta(days=1), time(0), tzinfo=zone).astimezone(timezone.utc)
        if start < hi and end > lo:
            return True
    return False


def _requested_days(from_: datetime, to: datetime) -> int:
    """C5: the number of UTC midnights in `[from_, to)`."""
    first = datetime.combine(from_.astimezone(timezone.utc).date(), datetime.min.time(), tzinfo=timezone.utc)
    if first < from_:
        first += timedelta(days=1)
    return 0 if first >= to else (to - first - timedelta(microseconds=1)) // timedelta(days=1) + 1


def data_gap_days(days: list[dict[str, Any]]) -> dict[date, str]:
    """D-E5.46 (GAP-REASONS): per dispatch day, READINGS_CONFLICT or NOT_ENOUGH_READINGS from the selected window's
    claim and limitation prefixes (`finding_index.data_gap_reason`, the one rule the Finding index uses). Only a
    selected CURRENT day with no open work: system work keeps its NOT_ANALYSED/PENDING precedence. HON-1: the chain
    counts take the same days out of "complete readings" (`EstateEvidenceService.site_data_gap_days_many`)."""
    out: dict[date, str] = {}
    for d in days:
        if not d.get("available") or d.get("selection") is None or d.get("status") != _S3_CURRENT:
            continue
        if {j.get("status") for j in d.get("jobs") or ()} & {"PENDING", "LEASED", "FAILED"}:
            continue
        why = data_gap_reason({"window_assessment": {"claim_level": d.get("window_claim_level")},
                               "selection": {"cohort_status": d.get("cohort_status")},
                               "limitations": d.get("window_limitations") or []})
        if why is not None:
            out[_day_of(d)] = why
    return out


def _day_of(day: dict[str, Any]) -> date:
    value = day.get("day")
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    return day["window_start"].astimezone(timezone.utc).date()


def _days_block(state: str, aligned: bool, requested: int, checked: int, gaps: list[date],
                withheld: bool, reasons: Mapping[date, str] | None = None) -> dict[str, Any] | None:
    """§2.6: the mini-grid `days` block (any state); `text` only when PARTIAL; `None` on a day-count mismatch (C5,
    Addendum 1 Q3: no day count is published from a mismatched read)."""
    if not aligned:
        return None
    gaps = sorted(gaps)
    text_value = None
    if state == PARTIAL:
        g = len(gaps)
        text_value = DAYS_CHECKED.format(c=checked, n=requested, g=g, unit="day" if g == 1 else "days")
        if withheld:
            text_value += DAYS_WITHHELD
    return {"policy": DAYS_POLICY, "requested": requested, "checked": checked,
            "gaps": [{"day": d.isoformat(), "state": "UNASSESSED",
                      "reason": "NO_ASSESSED_SELECTION" if reasons is None else reasons[d]} for d in gaps],
            "withheld": withheld, "text": text_value}


def _consequence(state: str, source_revision_id: Any = None, **extra: Any) -> dict[str, Any]:
    """Finding wire v2 (Run 8 ruling 3): `amount_low`/`amount_high` are the stored interval bounds for PRICED, both
    null otherwise; `amount` is the compatibility alias of `amount_low`; neither bound is a point estimate."""
    return {"state": state, "amount": None, "amount_low": None, "amount_high": None, "currency": None,
            "source_revision_id": None if source_revision_id is None else str(source_revision_id), **extra}


def _mini_grid_money(snapshot: Any, t: Any, s: Any, head: dict[str, Any], k: datetime, historical: bool,
                     finding_cited: list[str], withhold: bool = False) -> dict[str, Any]:
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
    if historical or withhold:  # a prior amount, or one on a gap day (C6, D-E5.45), is never current money
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
    # Run 8 ruling 6 suppresses today's job status for an explicit historical selection without a cursor. q10
    # ruling 3: a cursor continuation keeps page one's work-state fence, the same overlap/domain predicate with
    # `created_at <= cursor_known_at`, so an unchanged open job is not a selection change; the Site state and the
    # selected rows stay historical.
    fenced = not snapshot.basis_historical
    jobs = set(snapshot.open_jobs(t, s, domain, from_, to, k)) if fenced else set()
    freshness = "NOT_APPLICABLE" if domain == EV else "UNKNOWN"
    if not windows:
        return _empty(UNKNOWN, watermark=evidence_cutoff, job_state=_job_state(jobs, False),
                      source_freshness=freshness)
    states = {w["state"] for w in windows}
    stale_probe = domain == COLD and any(w.get("probe_fresh") is False for w in windows)
    if domain == COLD:
        freshness = "STALE" if stale_probe else "UNKNOWN" if any(w.get("probe_fresh") is None for w in windows) \
            else "RECENT"
    if snapshot.basis_historical:  # q12 ruling 1: Site state is page one's basis mode, not the response label
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
    by_finding: dict[str, tuple[dict[str, Any], tuple[Any, ...]]] = {}
    assessments, cited, consequences = set(), set(), set()
    for w in windows:
        assessments |= set(w["assessment_revision_ids"])
        cited |= set(w["evidence_ids"])
        order = (w["selected_at"], w["seq"], w["selection_id"])
        in_window: dict[str, str] = {}
        for row in w["findings"]:
            if not _intersects(row["episode_start"], row["episode_end"], from_, to, k):
                continue
            fid, frid = row["finding_id"], row["finding_revision_id"]
            if in_window.setdefault(fid, frid) != frid:  # one window never selects two revisions of one Finding
                raise EstateSelectionInconsistent(f"Finding {fid} has two revisions in one selected window.")
            held = by_finding.get(fid)
            if held is None:
                by_finding[fid] = (row, order)
            elif held[0]["finding_revision_id"] == frid:  # the same revision seen in two windows is no conflict
                if order > held[1]:
                    by_finding[fid] = (row, order)
            else:  # FIX-01: a Finding is revised per assessed window; the highest revision_no is the lineage head
                a, b = held[0].get("revision_no"), row.get("revision_no")
                if a is None or b is None or a == b:
                    raise EstateSelectionInconsistent(
                        f"Finding {fid} has two selected revisions at one cutoff.")
                if b > a:
                    by_finding[fid] = (row, order)
    rows = []
    for row, _ in by_finding.values():
        cited |= set(row["evidence_ids"])
        if row.get("consequence_revision_id") is not None:
            consequences.add(row["consequence_revision_id"])
        rows.append({"finding_id": row["finding_id"], "finding_revision_id": row["finding_revision_id"],
                     "episode_start": row["episode_start"], "title": row["title"], "lifecycle": row["lifecycle"],
                     "episode_end": row["episode_end"], "mechanism": row.get("mechanism"),  # CC-R2 (Q-C8)
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
        in_window = any(read_scope.within(p["later_start"], p["later_end"], k) for p in v.get("plans") or ())
        events.append(str(selected["id"]))
        assessments |= {str(b.get("primary")), *[str(x) for x in b.get("assessments") or ()]}
        cited_all |= set(cited)
        origins.add(str(a["origin_finding_revision_id"]))
        rows.append({
            "action_id": aid, "action_code": a["action_code"], "created_at": a["created_at"],
            "selected_event_id": str(selected["id"]), "source_finding_id": str(a["origin_finding_id"]),
            "source_finding_revision_id": str(a["origin_finding_revision_id"]),
            "action_title": f"Action {display_code(a['action_code'])}", "success_criterion": None, "owner": None, "due_at": None,
            "application_state": reduced["application"],
            "resolution_state": None if resolution is None else resolution["state"],
            "verification_outcome": resolution.get("outcome") if resolved else None,
            "source_provenance": provenance,
            # W3-03 closure 4 S8 / closure 5 S7: the selected plans (id, recorded_at, bounds) and outcomes at `k`.
            "_plans": list(v.get("plans") or ()), "_outcomes": dict(v.get("outcomes") or {}),
            "_outcome_id": None if resolution is None else resolution.get("outcome_id"),
            # CH5a2b-R Q6: the resolution outcome's stored source class (B7 wording; None when not stored).
            "_source_class": (v.get("source_classes") or {}).get(str(resolution.get("outcome_id")))
            if resolution is not None else None,
            # W3-03 r1a Q-1a-1: the selected Action event's own `recorded_at` (Portfolio tie key; never public).
            "_selected_recorded_at": selected["recorded_at"],
            "_open": reduced["application"] in ("PENDING", "APPLIED") and not resolved,
            "_verification_window": in_window and not resolved,
            "_verified_recent": verified_at is not None and read_scope.since(verified_at, VERIFIED_LOOKBACK, k)})
    state = HISTORICAL if snapshot.basis_historical else CURRENT  # q12 ruling 1: basis mode
    return {"selection_id": None, "watermark": None, "match_state": "NOT_APPLICABLE",
            "job_state": "NOT_APPLICABLE", "source_freshness": "NOT_APPLICABLE", "state": state, "rows": rows,
            "selected_finding_revision_ids": sorted(origins), "selected_action_event_ids": sorted(events),
            "selected_assessment_revision_ids": sorted(assessments), "selected_consequence_revision_ids": [],
            "selected_assumption_revision_ids": [], "cited_accepted_evidence_ids": sorted(cited_all)}


def not_applicable() -> dict[str, Any]:
    """A cold/EV Site's Action coverage: NOT_APPLICABLE (B4); it stays in the authorized scope."""
    return {**_empty(NOT_APPLICABLE), "match_state": "NOT_APPLICABLE", "job_state": "NOT_APPLICABLE",
            "source_freshness": "NOT_APPLICABLE"}
