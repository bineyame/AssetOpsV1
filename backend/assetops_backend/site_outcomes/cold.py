"""OUT-B3: the cold-chain composer. It reads the injected cold ports and builds the board's `SiteFacts`.

Sources and rules: build spec §B.4 "Cold (GreenHarvest)", rulings B-Q7/Q17/Q18/Q21-Q24 and addenda 2-3. Every port is
an existing service bound by B4 (`site_outcomes/read.py`). A refused or failed port never refuses the board: it is
named in `Composition.failed` and `read_state` is PARTIAL (B-Q17). The overview read and the Finding source
(`cold_findings`, addendum 3 M1) can leave an outcome UNKNOWN; readiness can leave the evidence outcome UNKNOWN.
Dates use the route Site record's zone, else UTC with the suffix (addendum 3 b)."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from assetops_backend.outcomes.catalogue import COLD
from assetops_backend.outcomes.outcome_map import COLD_KIND_MECHANISM
from assetops_backend.site_outcomes.board import (
    INCIDENT, MAINTENANCE_REQUEST, PLAN_RECORD, ActionFact, CaseFact, Contributor, FindingFact, Option,
    PlanFact, SiteFacts, finding_moved_outcomes, readiness_confidence, unresolved_links)
from assetops_backend.site_outcomes.mini import (
    NOT_LOADED, UTC_SUFFIX, WORK_WINDOW, MiniComposition as Composition, Reads, case_fact, day_month, num, plan_fact,
    plural, site_zone, utc)

GROW, COST, PROTECT, ASSURE = "GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET", "ASSURE_PERFORMANCE"
EXCURSION, START_FAILURE = "COLD_EXCURSION", "COLD_START_FAILURE"
#: Reading 17 (packet): a pinned read (HISTORICAL) is settled as well as a CURRENT one.
SETTLED_CURRENTNESS = ("CURRENT", "HISTORICAL")

PEAK_NOT_READ = "Not available yet · peak temperature not read"
START_FAILED = "Automatic start failed; started by hand"
START_RECORDED = "Automatic start recorded"
NO_START = "Not available yet · no backup start in this window"
#: Addendum 3 (a), R551: honest cooling-recovery texts in place of the mock's "Restarted with power".
COOLING_TEXT = {
    "LIMITED": "Not available yet · no reading confirms that cooling restarted and the chamber returned to its limits",
    "UNAVAILABLE": "Not available yet · cooling recovery was not assessed in this window",
    "CONTRADICTORY": "Cooling records disagree, so recovery cannot be judged",
}
NO_PLAN_RECORDED = "No preventive plan recorded"
NO_VERIFIED = "No verified result yet"
STORAGE_LEVEL = "Not available yet · no storage contract recorded"
CHAIN_COMPLETE = "Every step recorded"
NO_CHAIN = "Not available yet · no power interruption in this window"  # reading 19: an empty causal strip
LOADING_RECORDS = "Not available yet"
PROTECT_SUBLINE_START = ("Backup did not start by itself; cooling stopped until it was started by hand. Compressor "
                         "and backup condition are not assessed")
PROTECT_SUBLINE = "Compressor and backup condition are not assessed"
ASSURE_FULL = "Event fully reconstructed · no verified result yet"
ASSURE_PART = "Event partly reconstructed · no verified result yet"
ASSURE_SUBLINE = "Loading and door records are not connected, so stock impact cannot be judged"
OPTION_START_TEST = "Witnessed automatic-start test"
OPTION_STOCK = "Stock value what-if"
OPTION_LOG = "Record stock and door log"
#: B-Q23: the asset-type part of a plan's `asset_label` ("{asset_code} · {asset_type}") for each Protect contributor.
PLAN_TYPE_TOKENS = {"backup_generator": ("GENERATOR",), "compressor": ("COMPRESSOR",)}
UNKNOWN_CHIP = {"label": "Unknown", "tone": "gray"}
PENDING_CHIP = {"label": "Pending", "tone": "neutral"}

#: Every fixed viewer string, for the vocabulary scan.
COPY = (PEAK_NOT_READ, START_FAILED, START_RECORDED, NO_START, *COOLING_TEXT.values(), NO_PLAN_RECORDED, NO_VERIFIED,
        STORAGE_LEVEL, CHAIN_COMPLETE, NO_CHAIN, LOADING_RECORDS, PROTECT_SUBLINE_START, PROTECT_SUBLINE,
        ASSURE_FULL, ASSURE_PART, ASSURE_SUBLINE, OPTION_START_TEST, OPTION_STOCK, OPTION_LOG)


@dataclass(frozen=True)
class ColdPorts:
    """Existing services, bound by B4 to the request's tenant, Site, access basis and cutoff."""
    overview: Callable[[datetime, datetime], dict[str, Any]]                       # cold_site_reads.py:314
    findings: Callable[[datetime, datetime, str | None], dict[str, Any]]           # assessment store :2361
    domain_actions: Callable[[datetime, datetime, str | None], dict[str, Any]]     # work/domain_action_index.py
    work: Callable[[str, datetime, datetime, str | None], dict[str, Any]]          # work/site_index.py:309
    plans: Callable[[datetime, datetime], list[dict[str, Any]]]                    # preventive DRAFT, this Site
    readiness: Callable[[datetime, datetime], str | None]                          # EstateEvidenceService (B4)


def compose(ports: ColdPorts, *, site_code: str, lo: datetime, hi: datetime,
            site_timezone: str | None) -> Composition:
    """`lo`/`hi` are the request window, passed unchanged (B-Q7). Findings are read over that window (the selected
    assessment, every lifecycle); work, domain Actions and plans over the 31-day work window ending at `hi`."""
    c = site_code
    reads = Reads()
    tz = site_zone(site_timezone)
    work_lo = hi - WORK_WINDOW

    overview = reads.call("cold_overview", ports.overview, lo, hi)
    finding_rows = reads.pages("cold_findings", ports.findings, lo, hi, key="items")
    findings_ok = finding_rows is not None
    action_rows = reads.pages("domain_action_index", ports.domain_actions, work_lo, hi)
    readiness = reads.call("evidence_readiness", ports.readiness, lo, hi)
    plans = reads.call("plans", ports.plans, work_lo, hi)
    cases: list[CaseFact] = []
    work_failed = False
    for kind, case_kind in (("incidents", INCIDENT), ("maintenance", MAINTENANCE_REQUEST)):
        rows = reads.pages("work_index", ports.work, kind, work_lo, hi)
        work_failed = work_failed or rows is None
        cases += [case_fact(r, case_kind, c) for r in rows or ()]

    findings = tuple(_finding(r, lo, hi) for r in finding_rows or ())
    actions = tuple(domain_action(r, c) for r in action_rows or () if r.get("title") is not None)  # B-Q21
    by_mech = {m: [f for f in sorted(findings, key=lambda f: (f.title, f.finding_id))
                   if f.mechanism == m and f.open and f.in_window] for m in (EXCURSION, START_FAILURE)}
    claims = {str(r["finding_id"]): r for r in finding_rows or ()}

    body = overview or {}
    base = overview is not None and (body.get("currentness") or {}).get("state") in SETTLED_CURRENTNESS
    settled = {o: base for o in ("CC-1", "CC-6", "CC-5")}
    settled["CC-7"] = base and readiness not in (None, "UNKNOWN")
    for key in finding_moved_outcomes(COLD):  # addendum 3 M1
        settled[key] = settled.get(key, False) and findings_ok

    rc = readiness_confidence(readiness)
    high = (body.get("objective") or {}).get("policy_high_deg_c")
    excursion = by_mech[EXCURSION][0] if by_mech[EXCURSION] else None
    start_failure = by_mech[START_FAILURE][0] if by_mech[START_FAILURE] else None
    strip = body.get("causal_strip") if overview is not None else None
    gaps = None if strip is None else (sum(1 for s in strip if s.get("state") == "MISSING"),
                                       sum(1 for s in strip if s.get("state") == "CONTRADICTORY"))
    suffix = "" if tz is not None else UTC_SUFFIX
    plan_facts = tuple(plan_fact(p, tz) for p in plans or ())
    labels = {str(p["canonical_plan_id"]): p.get("asset_label") for p in plans or ()}

    contributors = {
        GROW: (), COST: (),
        PROTECT: (_temperature(excursion, claims, high, rc), _backup(body, overview is not None, rc),
                  _cooling(body, overview is not None),
                  _plan("backup_generator", "Backup generator", plan_facts, labels, plans is None, suffix),
                  _plan("compressor", "Compressor", plan_facts, labels, plans is None, suffix)),
        ASSURE: (_verified(cases, work_failed), Contributor("storage_service_level", "Storage service level",
                                                            STORAGE_LEVEL),
                 _chain(strip, gaps, rc), Contributor("loading_door_records", "Loading and door records",
                                                      LOADING_RECORDS)),
    }
    start_action = next((a for a in sorted(actions, key=lambda a: (a.code or "", a.action_id))
                         if start_failure is not None and a.origin_finding_id == start_failure.finding_id), None)
    start_href = (start_action.href if start_action is not None else
                  f"/sites/{c}/findings/{start_failure.finding_id}/recommendation" if start_failure else None)
    options = {GROW: (), COST: (),
               PROTECT: tuple(o for o in (Option(OPTION_START_TEST, start_href) if start_href else None,
                                          Option(OPTION_STOCK, f"/sites/{c}/financials/scenarios")) if o),
               ASSURE: (Option(OPTION_LOG, f"/sites/{c}/work"),)}
    headline = {PROTECT: _excursion_headline(excursion, claims, high),
                ASSURE: (None if strip is None else NO_VERIFIED if not strip
                         else ASSURE_FULL if gaps == (0, 0) else ASSURE_PART)}
    subline = {PROTECT: PROTECT_SUBLINE_START if start_failure is not None else PROTECT_SUBLINE,
               ASSURE: ASSURE_SUBLINE}

    facts = SiteFacts(domain=COLD, site_code=c, findings=findings, actions=actions, cases=tuple(cases),
                      plans=plan_facts, readiness=readiness, contributors=contributors, options=options,
                      headline=headline, subline=subline, settled=settled, date_suffix=suffix,
                      findings_settled=findings_ok)
    failed = tuple(reads.failed)
    return Composition(facts, "PARTIAL" if failed else "AVAILABLE", failed, unresolved_links(facts),
                       {"from": lo, "to": hi}, site_timezone if tz is not None else None)


def domain_action(r: dict[str, Any], c: str) -> ActionFact:
    """A cold or EV domain Action row (`work/domain_action_index.py`): open, in hand only (B-Q18)."""
    aid = str(r["action_id"])
    origin = r.get("origin") or {}
    return ActionFact(aid, r.get("action_code"), r.get("title") or "",
                      None if origin.get("finding_id") is None else str(origin["finding_id"]),
                      None if origin.get("finding_revision_id") is None else str(origin["finding_revision_id"]),
                      False, True, None, (r.get("links") or {}).get("action") or f"/sites/{c}/actions/{aid}",
                      is_domain=True)


def _finding(r: dict[str, Any], lo: datetime, hi: datetime) -> FindingFact:
    bounds = r.get("episode_bounds") or {}
    start = utc((bounds.get("start") or {}).get("earliest"))
    end = utc((bounds.get("end") or {}).get("latest"))
    in_window = start is None or (start < hi and (end is None or end > lo))
    kind = r.get("kind")
    return FindingFact(str(r["finding_id"]), str(r["revision_id"]), r.get("title") or "",
                       COLD_KIND_MECHANISM.get(kind, kind), r.get("lifecycle") or "",
                       (r.get("links") or {}).get("finding"),
                       asset_id=None if r.get("subject_asset_id") is None else str(r["subject_asset_id"]),
                       in_window=in_window)


def _peak(f: FindingFact | None, claims: dict[str, dict[str, Any]]) -> str | None:
    if f is None:
        return None
    return num((claims.get(f.finding_id, {}).get("claim") or {}).get("peak_observed"))


def _temperature(f: FindingFact | None, claims: dict, high: Any, rc: Any) -> Contributor:
    peak = _peak(f, claims)
    if peak is None or num(high) is None:
        return Contributor("chamber_temperature", "Chamber temperature", PEAK_NOT_READ)
    return Contributor("chamber_temperature", "Chamber temperature",
                       f"Peak {peak}°C against a {num(high)}°C limit", rc)


def _excursion_headline(f: FindingFact | None, claims: dict, high: Any) -> str | None:
    """"Chamber above {high}°C for {lo}–{hi} min" from the episode bounds; None lets the board use the lead title."""
    if f is None or num(high) is None:
        return None
    b = claims.get(f.finding_id, {}).get("episode_bounds") or {}
    s_lo, s_hi = utc((b.get("start") or {}).get("earliest")), utc((b.get("start") or {}).get("latest"))
    e_lo, e_hi = utc((b.get("end") or {}).get("earliest")), utc((b.get("end") or {}).get("latest"))
    if None in (s_lo, s_hi, e_lo, e_hi):
        return None
    shortest = max(timedelta(0), e_lo - s_hi).total_seconds() / 60
    longest = (e_hi - s_lo).total_seconds() / 60
    span = (f"{num(shortest)}" if num(shortest) == num(longest) else f"{num(shortest)}–{num(longest)}")
    return f"Chamber above {num(high)}°C for {span} min"


def _backup(body: dict, ok: bool, rc: Any) -> Contributor:
    if not ok:
        return Contributor("backup_start", "Backup start", NOT_LOADED)
    codes = {str(n.get("code")) for n in body.get("needs_attention") or ()}
    if START_FAILURE in codes:
        return Contributor("backup_start", "Backup start", START_FAILED, rc)
    if ((body.get("backup_summary") or {}).get("observed_success") or 0) > 0:
        return Contributor("backup_start", "Backup start", START_RECORDED, rc)
    return Contributor("backup_start", "Backup start", NO_START)


def _cooling(body: dict, ok: bool) -> Contributor:
    if not ok:
        return Contributor("cooling_recovery", "Cooling recovery", NOT_LOADED)
    state = (body.get("cooling") or {}).get("state")
    text = COOLING_TEXT.get(state or "UNAVAILABLE", COOLING_TEXT["UNAVAILABLE"])
    return Contributor("cooling_recovery", "Cooling recovery", text,
                       UNKNOWN_CHIP if state == "CONTRADICTORY" else None)


def _plan(key: str, label: str, plans: tuple[PlanFact, ...], labels: dict[str, Any], failed: bool,
          suffix: str) -> Contributor:
    href = "/maintenance/preventive"
    if failed:
        return Contributor(key, label, NOT_LOADED, None, href)
    tokens = PLAN_TYPE_TOKENS[key]
    match = [p for p in sorted(plans, key=lambda p: (p.code or "", p.plan_id))
             if _asset_type(labels.get(p.plan_id)) in tokens]
    if not match:
        return Contributor(key, label, NO_PLAN_RECORDED, PLAN_RECORD, href)
    p = match[0]
    if p.next_due_at is not None:
        due = f"due {day_month(p.next_due_at)}{suffix}"
    elif p.next_due_hours is not None:
        due = f"due at {num(p.next_due_hours)} operating {plural(num(p.next_due_hours), 'hour', 'hours')}"
    else:
        due = "due date not recorded"
    return Contributor(key, label, f"{p.title} {due}", PLAN_RECORD, href)


def _asset_type(asset_label: Any) -> str | None:
    if not asset_label or " · " not in str(asset_label):
        return None
    return str(asset_label).rsplit(" · ", 1)[1].strip().upper()


def _verified(cases: list[CaseFact], failed: bool) -> Contributor:
    done = [x for x in cases if x.kind == MAINTENANCE_REQUEST and x.state == "COMPLETED"]
    if failed and not done:
        return Contributor("verified_results", "Verified results", NOT_LOADED)
    if not done:
        return Contributor("verified_results", "Verified results", NO_VERIFIED)
    latest = max(done, key=lambda x: (x.occurred_at is not None, x.occurred_at or datetime.min, x.case_id))
    return Contributor("verified_results", "Verified results", f"{latest.code} completed; not yet verified",
                       PENDING_CHIP, latest.href)


def _chain(strip: Any, gaps: tuple[int, int] | None, rc: Any) -> Contributor:
    label = "Power, backup and cooling chain"
    if strip is None:
        return Contributor("event_chain", label, NOT_LOADED)
    if not strip:
        return Contributor("event_chain", label, NO_CHAIN)
    m, c = gaps if gaps is not None else (0, 0)
    if m == 0 and c == 0:
        return Contributor("event_chain", label, CHAIN_COMPLETE, rc)
    parts = []
    if m:
        parts.append(f"{m} {plural(m, 'step', 'steps')} not recorded")
    if c:
        parts.append(f"{c} {plural(c, 'step has', 'steps have')} conflicting records")
    return Contributor("event_chain", label, " · ".join(parts), rc)

