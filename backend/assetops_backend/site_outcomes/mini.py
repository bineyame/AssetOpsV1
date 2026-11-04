"""OUT-B2: the mini-grid composer. It reads the injected mini ports and builds the board's `SiteFacts`.

Sources and rules: build spec §B.4 "Mini (Kobo)", rulings B-Q6/Q10-Q14/Q17/Q18/Q22/Q23 and addendum 2. Every port is
an existing service bound by B4 (`site_outcomes/read.py`); this module calls them through `MiniPorts` and never
imports an adapter or another package's composition. A refused or failed port never refuses the board: it is named
in `MiniComposition.failed`, its contributor reads "Not available yet · this record could not be loaded", and
`read_state` is PARTIAL (B-Q17). Only the overview, dispatch, depth, readiness and Finding index reads can leave an
outcome UNKNOWN (addendum 2 item 5, addendum 3 M1)."""
from __future__ import annotations

import calendar
import time
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any
from zoneinfo import ZoneInfo

from assetops_backend import perf, read_scope
from assetops_backend.analytics.dispatch_read import dispatch_minutes
from assetops_backend.analytics.finding_episode import MECHANISM as FINDING_MECHANISM
from assetops_backend.analytics.plain import ALTERNATIVE_LABELS
from assetops_backend.chain import refs
from assetops_backend.chain.vocabulary import provenance_suffix
from assetops_backend.chain.read import assessment_state, board_day, lead_finding, local_days
from assetops_backend.estate.placement import place
from assetops_backend.estate.portfolio import workflow_label
from assetops_backend.mini_depth.inputs import MiniInputsRefused, Window, local_day_of, local_hour, local_noon, zone
from assetops_backend.outcomes.catalogue import MINI
from assetops_backend.outcomes.display_code import display_code
from assetops_backend.outcomes.warnings import evaluate
from assetops_backend.site_outcomes.board import (
    DECLARED, MAINTENANCE_REQUEST, INCIDENT, PLAN_RECORD, ActionFact, CaseFact, Contributor, FindingFact, Option,
    PlanFact, SignalFact, SiteFacts, finding_moved_outcomes, objective_verdict, per_kwh_amount, readiness_confidence,
    unresolved_links)
from assetops_backend.outcomes.objectives import (
    BEHIND_PACE, MISSED, ON_PACE, TOO_EARLY, ObjectiveFact, Reading, judge_month)
from assetops_backend.site_outcomes import objective_facts
from assetops_backend.site_outcomes.productive_use import productive_energy
from assetops_backend.site_outcomes.visits import maintenance_cases, warning_facts

GROW, COST, PROTECT, ASSURE = "GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET", "ASSURE_PERFORMANCE"
WORK_WINDOW = timedelta(days=31)  # the Finding, Action, work and estate reads' maximum (B-Q22, addendum 2 item 4)
DEPTH_DOMAINS = ("renewable", "fuel", "service", "backup")
#: WALK1-5: the spare-solar read covers the 5 Site-local days ending on the board day (the recurrence rule's day
#: count, `mini_depth/rules.py` `summarize_renewable`; the read's `mini_depth/read.py` `MAX_DAYS`).
RENEWABLE_DAYS = 5
MAX_PAGES = 50

NOT_LOADED = "Not available yet · this record could not be loaded"
UTC_SUFFIX = " · UTC (Site time zone unavailable)"
GAP_GENERIC = "An evidence gap limits this conclusion"
NO_VERIFIED = "No verified result yet"
GROW_SUBLINE = "Sales to productive users are not metered, so revenue itself is not measured yet"
PROTECT_HEADLINE = "Battery and generator condition are not assessed"
#: Rulings C final review L2: the Protect headline when no warning moves MG-4 and m >= 1 periods were assessed.
PROTECT_CLEAR = "Battery stayed clear of its reserve in {m} assessed generator {periods}"
PROTECT_SUBLINE = ("Battery and generator condition is not assessed; these are early warnings only. Power was "
                   "delivered, but what customers needed is not measured")
COST_NO_MONEY = "No fuel cost estimated for this day"
COST_MONEY = "possible extra fuel cost on this day"
#: POLISH §1.1 (R626, owner Q1): a PRICED amount of zero; idle fuel is not modelled, so no amount is shown.
COST_ZERO = "No fuel cost estimated: the generator was on but delivered no measured power"
#: POLISH §1.7: MG-7 settled on a COMPLETE day with no generator use (readiness UNKNOWN only for lack of intervals).
#: The sheet's "No generator run to check ..." fails the product vocabulary guard ("run"), so the wording avoids it.
NO_RUN_READINGS = "Generator not used on this day, so nothing to check · readings complete"
FIXED = {
    "cash": "Not available yet · no billing or payment records",
    "earnings": "Not available yet · needs site income, operating cost and capital records",
    "plan_target": "Not available yet · no target declared for this site",
}
#: C (U4): the battery contributor from the dispatch body's binding constraints (no reserve %, R562).
RESERVE_CONSTRAINTS = ("BATTERY_AT_RESERVE", "BATTERY_NEAR_RESERVE")
NO_PERIOD_ASSESSED = "Not available yet · no generator period assessed on this day"
NO_FUEL_BALANCE = "No complete fuel balance yet"
PRICE_FALLBACK = "Declared price · see Assumptions"
NO_GEN_PLAN = "No preventive plan recorded"
SERVICE_MEASURED = "Delivered power measured; demand not measured"
NO_BACKUP_EVENT = "No backup event in this window"
SOLAR_NOT_READ = "Not available yet · spare solar not checked on the last 5 days"  # WALK1 Addendum 4
SOLAR_WELL_OBSERVED = "Spare solar on {e} of {a} well-observed {days}"
SOLAR_NOT_CHECKED = " · {n} of the last 5 days not checked"  # WALK1-5 (WN-2 on the Site row), R685
SERVICE_NOT_READ = "Not available yet · delivered power not read for this hour"
HEADROOM_ISSUE = "Productive-use headroom"
OPTION_WHAT_IF = "Productive-use what-if"
OPTION_TRIAL = "Trial a lower generator stop setting"
OPTION_CHANGE = "Proposed setting change"
OPTION_RESTORE = "Restore battery reporting"
VERIFICATION_TEXT = {"PENDING": "{code} not yet verified", "NO_PLAN": "{code} not yet verified",
                     "REASSESSMENT_PENDING": "{code} not yet verified", "VERIFIED": "{code} verified{suffix}",
                     "INEFFECTIVE": "{code} did not meet its target", "INCONCLUSIVE": "{code} result not determined"}
#: OUT-E E4: the Verified results line of a VERIFIED Action whose stored cost check shows a modelled improvement.
#: POLISH Addendum 6 Q6: the verdict and code prefix stay; the cost clause matches board.COST_CHANGE.
VERIFIED_WITH_COST = ("{code} verified{suffix}: estimated effect of the trial (not money saved): "
                      "{amount} {currency} less supply cost per kWh")
PENDING_STATES = ("PENDING", "NO_PLAN", "REASSESSMENT_PENDING")
PENDING_CHIP = {"label": "Pending", "tone": "neutral"}
HIGH_CHIP = {"label": "High", "tone": "green"}
UNKNOWN_CHIP = {"label": "Unknown", "tone": "gray"}
#: Addendum 2 item 3: `place(...).confidence` words (portfolioWords.ts:38) as board chips.
PLACEMENT_CHIP = {"SUPPORTED_SOURCE_COHERENT": HIGH_CHIP, "LIMITED": {"label": "Limited", "tone": "amber"},
                  "UNKNOWN": UNKNOWN_CHIP}
READINESS_WORD = {"FULL": "Full", "LIMITED": "Limited", "NONE": "None", "UNKNOWN": "Unknown"}
CLOSED_LABELS = ("Verified", "Resolution withdrawn")  # B-Q18
#: The Portfolio's source words (`estate/placement.py:54`, `:59`), copied as a local plain-text mapping so the
#: composer imports no private estate name (B2 review L1); test_out_b2_mini asserts equality.
SOURCE_TEXT = {"REGISTERED_SIMULATION": "Example data",
               "AUTHORED_DEMONSTRATION": "Prepared example data source", "MIXED": "Mixed sources"}
SOURCE_UNRESOLVED = "Source not resolved"
#: IDX-GAPS U2: the board's Finding window in days, and the gap line under the rows (`finding_gap_line`).
FINDING_WINDOW_DAYS = 31
GAPS_NO_READINGS = "{g} of the last {n} days {verb} no checked readings yet"
GAPS_NOT_ASSESSED = "Not available yet · {g} of {n} days {verb} not assessed yet"
#: IDX-GAPS Addendum 3: the board names a mini Finding by its lifecycle, in the plain titles of
#: `frontend/src/sites/findingWords.ts` `LIFECYCLE_WORDS` (copied verbatim); the stored title is never shown here.
FINDING_TITLE = {"SUPPORTED": "Generator may have been on longer than needed",
                 "UNCONFIRMED": "Extra generator time not confirmed by the latest check",
                 "NO_LONGER_SUPPORTED": "Extra generator time no longer supported by the latest check",
                 "MERGED": "Generator support review: joined into an earlier finding"}
FINDING_TITLE_FALLBACK = "Generator support review"
#: Addendum 3 L3, CH5a2b-R Q4: the diagnostics marker for an Action the Action index returned but `action_rows`
#: did not (never on the wire).
ACTION_ROW_MISSING = "ACTION_ROW_MISSING"

#: OUT-D U4: the objective actual texts that carry no number (the numbered ones are templates in `mini_readings`).
MG1_ACTUAL = "sales not recorded"
MG5_UNMEASURED = "critical demand not measured"
MG2_LONGER = "{m} min longer than needed on this day"
MG2_UNCLEAR = "{m} min not yet clear on this day"
MG5_UNSERVED = "{kwh} kWh not served"
#: OUT-D U4 (review M1): the Assure "Actual against plan" line when the objective store could not be read; it makes
#: no claim about whether a target exists.
PLAN_NOT_READ = "Not available yet · declared objectives could not be loaded"
#: WALK1-3 §4.4: estimated productive-use sales = measured use by declared productive users x the declared price per
#: kWh. Always an estimate at a declared price; never billed, collected or measured income.
SALES_NO_USERS = "Not available yet · no productive users identified for this site"
SALES_NO_READINGS = "Not available yet · no measured use by {names} on this day"
SALES_CONFLICT = "Not available yet · {names} {verb} conflicting readings on this day, so use is not estimated"
SALES_USED = "{kwh} kWh used by {names} in {h} measured {hours}"
SALES_NO_PRICE = SALES_USED + " · no price per kWh declared"
PRICE_DECLARED = "Declared at {p} {cur} per kWh"
PRICE_NOT_DECLARED = "Not available yet · no price per kWh declared"
SALES_HEADLINE = "estimated productive-use sales"
SALES_ZERO_HEADLINE = "No productive-use sales on this day: {names} not used"
SALES_SUBLINE = SALES_USED + ", at the declared price of {p} {cur} per kWh · not billed or collected"
#: WALK1-3b §A2.2/§A2.5: the MG-1 month-to-date reading (Site-local month through the board day). `{c}` checked days
#: have measured productive-use coverage; `{e}` days have elapsed; `{k}` is the objective's checked-day minimum.
MG1_SO_FAR = "{mtd} kWh so far this month, on {c} of {e} days checked"
MG1_PACE = MG1_SO_FAR + " · averages {avg} kWh a day; the target needs {need} kWh a day"
MG1_TOO_EARLY = "{mtd} kWh so far this month, on {c} checked {d}; too early to judge (needs {k} checked days)"
MG1_MISSED = "{mtd} kWh this month, all {m} days checked"

#: Every fixed viewer string, for the vocabulary scan (tests/test_out_b2_vocabulary.py).
COPY = (MG1_ACTUAL, MG5_UNMEASURED, MG2_LONGER.format(m="12"), MG2_UNCLEAR.format(m="5"), MG5_UNSERVED.format(kwh="3"),
        PLAN_NOT_READ, *objective_facts.COPY, NOT_LOADED, UTC_SUFFIX, GAP_GENERIC, NO_VERIFIED, GROW_SUBLINE,
        PROTECT_HEADLINE, PROTECT_SUBLINE,
        PROTECT_CLEAR.format(m=1, periods="period"), PROTECT_CLEAR.format(m=2, periods="periods"),
        COST_NO_MONEY, COST_MONEY, COST_ZERO, NO_RUN_READINGS, *FIXED.values(), NO_FUEL_BALANCE, PRICE_FALLBACK, NO_GEN_PLAN, SERVICE_MEASURED,
        NO_BACKUP_EVENT, SOLAR_NOT_READ, SOLAR_WELL_OBSERVED.format(e=1, a=1, days="day"),
        SOLAR_WELL_OBSERVED.format(e=0, a=2, days="days") + SOLAR_NOT_CHECKED.format(n=3), SERVICE_NOT_READ, HEADROOM_ISSUE, OPTION_WHAT_IF, OPTION_TRIAL,
        OPTION_CHANGE, OPTION_RESTORE, *ALTERNATIVE_LABELS.values(), *SOURCE_TEXT.values(),
        SOURCE_UNRESOLVED, *READINESS_WORD.values(),
        GAPS_NO_READINGS.format(g=1, n=31, verb="has"), GAPS_NO_READINGS.format(g=23, n=31, verb="have"),
        GAPS_NOT_ASSESSED.format(g=1, n=31, verb="is"), GAPS_NOT_ASSESSED.format(g=2, n=31, verb="are"),
        *FINDING_TITLE.values(), FINDING_TITLE_FALLBACK,
        SALES_NO_USERS, SALES_NO_READINGS.format(names="Grain mill"),
        SALES_CONFLICT.format(names="Grain mill", verb="has"), SALES_CONFLICT.format(names="A, B", verb="have"),
        SALES_USED.format(kwh="168.3", names="Grain mill", h="8", hours="hours"),
        SALES_USED.format(kwh="0", names="Grain mill", h="1", hours="hour"),
        SALES_NO_PRICE.format(kwh="168.3", names="Grain mill", h="8", hours="hours"),
        PRICE_DECLARED.format(p="0.25", cur="USD"), PRICE_NOT_DECLARED, SALES_HEADLINE,
        SALES_ZERO_HEADLINE.format(names="Grain mill"),
        SALES_SUBLINE.format(kwh="168.3", names="Grain mill", h="8", hours="hours", p="0.25", cur="USD"),
        MG1_SO_FAR.format(mtd="673.2", c=4, e=29), MG1_MISSED.format(mtd="250", m=30),
        MG1_PACE.format(mtd="200", c=4, e=12, avg="50", need="10"),
        MG1_TOO_EARLY.format(mtd="40", c=1, d="day", k=3), MG1_TOO_EARLY.format(mtd="80", c=2, d="days", k=5))


@dataclass(frozen=True)
class MiniPorts:
    """Existing services, bound by B4 to the request's tenant, Site, access basis, gate and pin. CH-5a1: the overview,
    the Finding index and the estate readiness are not read; their inputs come from the ChainReader (`chain/read.py`)."""
    source: Callable[[], tuple[bool, str]]                                       # R4: the overview's source gate
    depth: Callable[[str, datetime, datetime], dict[str, Any]]                   # mini_depth/read.py:338
    dispatch: Callable[[date], dict[str, Any]]                                   # analytics/dispatch_read.py:123
    assumption: Callable[[datetime], dict[str, Any]]                             # diesel_price_per_litre series
    #: CH-5a1 §A3: `ChainRequest.day` over (every day of the work window, the board day).
    chain_day: Callable[[tuple[date, ...], tuple[date, ...]], Any]
    chain_findings: Callable[[datetime, datetime], Any]                          # `ChainRequest.findings`
    findings_settled: Callable[[], bool]                                         # R8
    #: CH-5a2b R1: `ChainRequest.placement_facts(revision_ids)` and `ChainRequest.action_rows()` (the estate
    #: snapshot read they replace is gone from the board).
    placement_facts: Callable[[list[str]], Any]
    action_rows: Callable[[], Any]
    action_index: Callable[[datetime, datetime, str | None], dict[str, Any]]     # actions/site_index.py:160
    action_facts: Callable[[list[str]], Any]                                     # `ChainRequest.action_facts` (C6)
    #: `ChainRequest.money_head(finding_id, revision_id, is_latest, source_open, settled)` (CH5a1-R Q5).
    money: Callable[[str, str, bool, bool, bool], Any]
    work: Callable[[str, datetime, datetime, str | None], dict[str, Any]]        # work/site_index.py:309
    plans: Callable[[datetime, datetime], list[dict[str, Any]]]                  # preventive DRAFT, this Site
    objectives: Callable[[], list[dict[str, Any]]] = lambda: []                  # OUT-D objective store (current)
    pin: tuple[Any, Any] | None = None                                           # the route's pinned Finding
    #: WALK1-3 §4.3: the LOAD components declared `supply-use = PRODUCTIVE` in the Foundation in force at an instant
    #: ({"asset_code", "asset_id", "name"}), their accepted `feeder_demand` readings in `[lo, hi)`, and the
    #: `productive_use_price_per_kwh` series at an instant (the diesel `assumption` read with the productive key).
    productive_users: Callable[[datetime], list[dict[str, Any]]] = lambda at: []
    productive_readings: Callable[[list[Any], datetime, datetime], list[dict[str, Any]]] = lambda ids, lo, hi: []
    productive_price: Callable[[datetime], dict[str, Any]] = lambda at: {}


@dataclass(frozen=True)
class MiniComposition:
    facts: SiteFacts
    read_state: str                                # AVAILABLE | PARTIAL
    failed: tuple[str, ...]                        # port names that refused or failed
    diagnostics: tuple[tuple[str, str], ...]       # unresolved (holder id, Finding id) links and (Action id,
    #                                                ACTION_ROW_MISSING); never on the wire
    window: dict[str, datetime]                    # the overview day {from, to}
    timezone: str | None                           # the Site zone used for local dates, None = UTC fallback
    #: B-Q27: per category, the Portfolio card's short value ("{low}–{high} kW unused"); mini Grow only.
    short_values: dict[str, str] = field(default_factory=dict)


class Reads:
    """The shared producer-read seam of the mini, cold and EV composers.

    QW-1: every call adds `timings[name] = [calls, ms]` (and the same to the request recorder, `perf.py`), on
    success and on failure; the return value and the failure handling are unchanged."""

    def __init__(self, site: str | None = None) -> None:
        self.site = site  # CH5a1-R2: the Site code every ledger key starts with (one Reads per Site board)
        self.failed: list[str] = []
        self.statuses: dict[str, set[str]] = {}
        self.first: dict[str, dict[str, Any]] = {}  # IDX-GAPS U2: the first page body per paged read
        self.timings: dict[str, list[float]] = {}

    def call(self, name: str, fn: Callable[..., Any], *args: Any, memo: bool = False) -> Any:
        """CH5a1-R2 (ledger): the request-ledger key is `(site, *args)`, because the ports are per-Site
        closures (the summary's `objectives ()` read once per Site was 3 on one key). `memo` runs the read
        through the request memo (R1) on the same key, so a second call with the same arguments executes
        nothing and returns a mutable copy."""
        key = args if self.site is None else (self.site, *args)
        started = time.perf_counter()
        try:
            out = (read_scope.thaw(read_scope.memo(name, fn, *args, key=key)) if memo else fn(*args))
        except Exception:  # noqa: BLE001 - B.3: a refused or failed producer read never refuses the board
            if name not in self.failed:
                self.failed.append(name)
            return None
        finally:
            ms = (time.perf_counter() - started) * 1000
            entry = self.timings.setdefault(name, [0, 0.0])
            entry[0] += 1
            entry[1] += ms
            perf.record(f"read.{name}", ms)
            if not memo:  # a memoised read is counted by `read_scope.memo`, once per executed key
                read_scope.record(name, key, ms)
        return out

    def pages(self, name: str, fn: Callable[..., dict[str, Any]], *args: Any,
              key: str = "rows") -> list[dict[str, Any]] | None:
        rows: list[dict[str, Any]] = []
        cursor = None
        for _ in range(MAX_PAGES):
            body = self.call(name, fn, *args, cursor)
            if body is None:
                return None
            self.first.setdefault(name, body)
            rows += list(body.get(key) or ())
            if body.get("status") is not None:
                self.statuses.setdefault(name, set()).add(str(body["status"]))
            cursor = body.get("next_cursor")
            if not cursor:
                return rows
        self.failed.append(name)
        return None


# ---------------------------------------------------------------- Finding index (IDX-GAPS U2)

def finding_gap_line(day_facts: Any, requested: int) -> dict[str, Any] | None:
    """R8 / CH5a1-R Q9: the note under the board rows naming the requested days whose day grade is PENDING or
    NO_DATA (a missing row is NO_DATA), or None. "No checked readings" when no gap day holds a PENDING row.
    The index's PARTIAL-mode withholding is not reproduced (CH5a1-R Q4), so `withheld` is always False."""
    if day_facts is None or not day_facts.gaps:
        return None
    g = len(day_facts.gaps)
    pending = any("PENDING" in subjects.values() for d in day_facts.gaps
                  for subjects in (day_facts.grades.get(d) or {}).values())
    if not pending:
        text = GAPS_NO_READINGS.format(g=g, n=requested, verb="has" if g == 1 else "have")
    else:
        text = GAPS_NOT_ASSESSED.format(g=g, n=requested, verb="is" if g == 1 else "are")
    return {"text": text, "days": sorted(d.isoformat() for d in day_facts.gaps), "withheld": False}


# ---------------------------------------------------------------- formatting

def num(value: Any) -> str | None:
    """A decimal value as display text: integers plain, otherwise one decimal place."""
    if value is None:
        return None
    try:
        d = Decimal(str(value))
    except InvalidOperation:
        return None
    if d == d.to_integral_value():
        return str(int(d))
    return f"{d.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP).normalize():f}"


def utc(value: Any) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    text = str(value)
    parsed = datetime.fromisoformat(text[:-1] + "+00:00" if text.endswith("Z") else text)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def site_zone(name: str | None) -> ZoneInfo | None:
    """The Site zone through `mini_depth/inputs.py` `zone` (B2 review L2); missing or invalid gives None."""
    try:
        return zone(name)
    except MiniInputsRefused:
        return None


MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def day_month(d: Any) -> str:
    """A Site-local date as "d MMM" (guide §4)."""
    return f"{d.day} {MONTHS[d.month - 1]}"


def plural(n: Any, one: str, many: str) -> str:
    """Addendum 3 L7: the singular for n = 1 in every "{n} ..." template."""
    try:
        return one if n is not None and Decimal(str(n)) == 1 else many
    except InvalidOperation:
        return many


def price_text(value: Any) -> str | None:
    """B2 review L6: a declared price for display: two decimal places, more only when the stored value has them."""
    try:
        d = Decimal(str(value))
    except InvalidOperation:
        return None
    cents = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{cents:f}" if cents == d else f"{d.normalize():f}"


def limitation_text(limitation: str) -> str:
    """B-Q12: the plain label of the first known code (leading code, or a code named in the detail), else the
    generic sentence. A raw limitation string is never rendered."""
    lead = limitation.split(":", 1)[0].strip()
    if lead in ALTERNATIVE_LABELS:
        return ALTERNATIVE_LABELS[lead]
    for code, label in ALTERNATIVE_LABELS.items():
        if code in limitation:
            return label
    return GAP_GENERIC


def not_available(key: str, label: str, link_ref: dict[str, Any] | None = None) -> Contributor:
    return Contributor(key, label, NOT_LOADED, None, link_ref)


# ---------------------------------------------------------------- composer

def compose(ports: MiniPorts, *, site_code: str, day: date, site_timezone: str | None) -> MiniComposition:
    """`day` is the Site-local board day (R6: `selected_day` or `db_today()` read as the Site-local date; the window
    is `[local 00:00 D, local 00:00 D+1)` as UTC instants); `site_timezone` is the zone the route's Site lookup
    carries. Local dates use the depth body's own `site.timezone`; if depth is refused they are UTC with the suffix
    (addendum 2 item 6). CH-5a1: no overview, Finding index or estate readiness read (§A4)."""
    c = site_code
    reads = Reads(c)  # CH5a1-R2: the ledger keys every read by its Site
    start, end = board_day(day, site_timezone)
    work_lo = end - WORK_WINDOW

    gate = reads.call("source", ports.source)
    source_open = bool(gate and gate[0])
    depth = _depth(reads, ports, start, site_timezone)
    depth_ok = all(depth.get(d) is not None for d in DEPTH_DOMAINS)
    zone_name = next((b["site"].get("timezone") for b in depth.values()
                      if b is not None and (b.get("site") or {}).get("timezone")), None)
    tz = site_zone(zone_name) if depth_ok else None
    dispatch = reads.call("dispatch", ports.dispatch, day)
    # R5 / R8 / Q9: one snapshot read over every Site-local day of the work window; readiness on the board day.
    day_facts = reads.call("chain_day", ports.chain_day, local_days(work_lo, end, site_timezone), (day,))
    readiness = None if day_facts is None else day_facts.readiness
    heads = reads.call("chain_findings", ports.chain_findings, work_lo, end)
    settled_findings = reads.call("findings_settled", ports.findings_settled)
    findings_ok = heads is not None and bool(settled_findings)
    if not findings_ok and "chain_findings" not in reads.failed:
        reads.failed.append("chain_findings")  # unsettled Findings (R8): PARTIAL, so text and notice agree
    action_rows = reads.pages("action_index", ports.action_index, work_lo, end)
    price = reads.call("assumptions", ports.assumption, start)
    plans = reads.call("plans", ports.plans, work_lo, end)
    incidents = reads.pages("work_index", ports.work, "incidents", work_lo, end)
    visits = maintenance_cases(reads, ports.work, c, end)  # C: 60 days by occurrence (R571)
    cases: list[CaseFact] = [case_fact(r, INCIDENT, c) for r in incidents or ()] + list(visits or ())
    objective_rows = reads.call("objectives", ports.objectives)  # CH5a1-R2: keyed (site_code,) by `Reads`
    sales = _productive_sales(reads, ports, c, start, end)
    month = _productive_month(reads, ports, sales.get("users"), start, site_timezone)

    # CH-5a2b R1 (§B14 Q3): the chip's placement facts for the board-day heads only; the labels' Action rows.
    day_ids = [str(h.revision_id) for h in heads or () if _meets(h, start, end)]
    placements = reads.call("placement_facts", ports.placement_facts, day_ids) if day_ids else {}
    chain_actions = reads.call("action_rows", ports.action_rows) if action_rows else ()
    findings = _findings(heads or (), placements, c, start, end, work_lo)
    actions, has_change, missing_rows = _actions(reads, ports, action_rows or (), chain_actions, c, site_timezone)
    plan_facts = tuple(plan_fact(p, tz) for p in plans or ())

    # CH5a1-R Q2: `base` = the source gate, the settled board day and a dispatch read (CLOSED was the gate).
    read_ok = gate is not None and day_facts is not None   # the reads that replace the overview read
    settled_day = bool(day_facts is not None and day_facts.settled)
    base = source_open and settled_day and dispatch is not None
    assessment = {} if dispatch is None else {
        "state": assessment_state(dispatch.get("status")), "limitations": dispatch.get("limitations") or (),
        "claim_level": (dispatch.get("window_assessment") or {}).get("claim_level"),
        "dispatch_intervals": dispatch.get("intervals") or ()}
    lead_money = None if heads is None else lead_finding(heads, start, end, source_open=source_open,
                                                         pin=ports.pin, settled=settled_day)
    money_head = None if lead_money is None else reads.call(
        "money_head", ports.money, *lead_money, source_open, settled_day)
    body = {"money": {"source_provenance": None if money_head is None else money_head.source_provenance}}
    no_run = no_run_day(base, assessment, readiness)
    settled = {"MG-1": base and depth_ok, "MG-6": base, "MG-3": base, "MG-2": base and dispatch is not None,
               "MG-5": base and depth_ok, "MG-4": base and dispatch is not None,
               "MG-7": base and (readiness not in (None, "UNKNOWN") or no_run)}
    for key in finding_moved_outcomes(MINI):  # addendum 3 M1: the Finding source is a status producer
        settled[key] = settled.get(key, False) and findings_ok

    limitations = [str(x) for x in assessment.get("limitations") or ()]
    renewable = (depth.get("renewable") or {}).get("cards") or {}
    eligible, assessed = renewable.get("eligible_days"), renewable.get("assessed_days")
    lead = next((f for f in sorted(findings, key=lambda f: (f.title, f.finding_id)) if f.open and f.in_window), None)

    signals = (SignalFact("SIGNAL:PRODUCTIVE_USE_HEADROOM", eligible is not None and eligible >= 1, HEADROOM_ISSUE,
                          renewable_ref(c, start, site_timezone)),
               SignalFact("SIGNAL:EVIDENCE_GAP", bool(limitations),
                          (f"{limitation_text(limitations[0])} limits this conclusion"
                           if limitations and limitation_text(limitations[0]) != GAP_GENERIC else GAP_GENERIC)))

    rc = readiness_confidence(readiness)
    reserve = reserve_counts(dispatch)
    contributors = {
        GROW: _grow(c, depth, eligible, assessed, rc, sales["contributors"],
                     renewable_ref(c, start, site_timezone)),
        COST: _cost(c, dispatch, depth, price, lead, rc),
        PROTECT: _protect(c, depth, plan_facts, plans is None, reserve, rc),
        ASSURE: _assure(c, actions, body, read_ok, readiness, rc, limitations,
                        "action_facts" in reads.failed or action_rows is None, no_run),
    }
    options = {GROW: (Option(OPTION_WHAT_IF, refs.site_ref(c, "financial_scenarios")),),
               COST: tuple(o for o in (
                   Option(OPTION_TRIAL, refs.finding_ref(c, lead.finding_id, view="recommendation")) if lead else None,
                   Option(OPTION_CHANGE, refs.site_ref(c, "foundation_changes")) if has_change else None) if o),
               PROTECT: (),
               ASSURE: (Option(OPTION_RESTORE, refs.site_ref(c, "work")),) if limitations else ()}

    headroom = renewable.get("headroom_kw") or {}
    lo_kw, hi_kw = num(headroom.get("low")), num(headroom.get("high"))
    money = {} if money_head is None else {"amount_low": money_head.amount_low,
                                           "amount_high": money_head.amount_high, "currency": money_head.currency}
    priced = money_head is not None and money_head.priced
    zero = priced and _is_zero(money.get("amount_high"))  # §1.1: amount_low is pinned to 0 by the schema
    avoidable, _ = _dispatch_minutes(dispatch)
    verified = sum(1 for a in actions if a.verification_state == "VERIFIED")
    headline = {GROW: f"{lo_kw}–{hi_kw} kW of daytime solar unused" if lo_kw and hi_kw else None,
                COST: (COST_ZERO if zero else COST_MONEY if priced else COST_NO_MONEY)
                if read_ok else None,
                PROTECT: PROTECT_HEADLINE,
                ASSURE: f"{verified} {plural(verified, 'verified result', 'verified results')}"
                if verified else NO_VERIFIED}
    headline_money = {COST: {k: money.get(k) for k in ("amount_low", "amount_high", "currency")}
                      if priced and not zero else None}
    # WALK1-3 §4.4: a sales estimate leads; spare solar stays a contributor. L3: a zero-use day yields to a
    # spare-solar headline when one exists.
    if sales.get("headline") is not None and not (sales.get("zero") and headline[GROW] is not None):
        headline[GROW] = sales["headline"]
        headline_money[GROW] = sales.get("money")
    subline = {GROW: sales.get("subline"),
               COST: f"Generator stayed on {num(avoidable)} {plural(num(avoidable), 'minute', 'minutes')} longer "
                     "than needed"
               if avoidable is not None and avoidable > 0 else None,
               PROTECT: PROTECT_SUBLINE,
               ASSURE: limitation_text(limitations[0]) if limitations else None}

    # OUT-D U4: declared objectives, their readings, and the Assure "Actual against plan" count
    objectives = objective_facts.from_rows(objective_rows, num)
    readings = mini_readings(dispatch, depth, month, next((o for o in objectives if o.outcome_key == "MG-1"), None))
    if objective_rows is None:
        plan_line = Contributor("actual_against_plan", "Actual against plan", PLAN_NOT_READ)
        contributors[ASSURE] = tuple(plan_line if x.key == "actual_against_plan" else x
                                     for x in contributors[ASSURE])
    elif objectives:
        verdicts = [objective_verdict(o, readings, settled) for o in objectives]
        plan_line = Contributor("actual_against_plan", "Actual against plan", objective_facts.assure_text(verdicts))
        contributors[ASSURE] = tuple(plan_line if x.key == "actual_against_plan" else x
                                     for x in contributors[ASSURE])

    facts = SiteFacts(domain=MINI, site_code=c, findings=findings, actions=actions, cases=tuple(cases),
                      plans=plan_facts, readiness=readiness, contributors=contributors, options=options,
                      signals_extra=signals, headline=headline, headline_money=headline_money, subline=subline,
                      settled=settled, date_suffix="" if tz is not None else UTC_SUFFIX,
                      findings_settled=findings_ok, objectives=objectives,
                      finding_gaps=finding_gap_line(day_facts, FINDING_WINDOW_DAYS), readings=readings,
                      objectives_ok=objective_rows is not None,
                      objective_after={GROW: "productive_sales"},
                      work_window=(work_lo, end))  # WALK1-3b §A2.3: (a), then (b), then (c)
    suffix = "" if tz is not None else UTC_SUFFIX
    warnings = evaluate(warning_facts(facts, to=end, tz=tz, suffix=suffix, lo=start, reserve=reserve))
    w = sum(1 for x in warnings if any(o["key"] == "MG-4" for i in x.categories["items"] if i["role"] == "MOVES"
                                       for o in i["outcomes"]))
    facts = replace(facts, warnings=warnings, headline={
        **headline, PROTECT: f"{w} early {plural(w, 'warning', 'warnings')} on battery and generator" if w
        else protect_clear(reserve)})
    failed = tuple(reads.failed)
    diagnostics = unresolved_links(facts) + tuple((aid, ACTION_ROW_MISSING) for aid in missing_rows)
    return MiniComposition(facts, "PARTIAL" if failed else "AVAILABLE", failed, diagnostics,
                           {"from": start, "to": end}, zone_name if tz is not None else None,
                           {GROW: f"{lo_kw}–{hi_kw} kW unused"} if lo_kw and hi_kw else {})


def renewable_bounds(start: datetime, tz_name: str | None) -> tuple[datetime, datetime]:
    """The `RENEWABLE_DAYS` whole Site-local days ending on the board day, as UTC bounds (WALK1-5)."""
    name = tz_name or ""
    local_day = local_day_of(Window(start, start + timedelta(days=1)), name)
    return (local_hour(local_day - timedelta(days=RENEWABLE_DAYS - 1), 0, name).start,
            local_hour(local_day + timedelta(days=1), 0, name).start)


def renewable_ref(c: str, start: datetime, tz_name: str | None) -> dict[str, Any]:
    """The renewable page opened on the same 5 days the Productive use line describes (M2/L1); bare when refused."""
    try:
        lo, hi = renewable_bounds(start, tz_name)
    except MiniInputsRefused:
        return refs.evidence_ref(c, "renewable")
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    return refs.evidence_ref(c, "renewable", refs.window(lo.astimezone(timezone.utc).strftime(fmt),
                                                          hi.astimezone(timezone.utc).strftime(fmt)))


def renewable_href(c: str, start: datetime, tz_name: str | None) -> str:
    """`renewable_ref`'s screen path."""
    return refs.href_for(renewable_ref(c, start, tz_name))


def _depth(reads: Reads, ports: MiniPorts, start: datetime, tz_name: str | None) -> dict[str, dict | None]:
    """B-Q6: the Site-local day containing the overview `window.start`; the hourly domains read its local noon hour
    (reading recorded in the packet). WALK1-5: renewable reads the `RENEWABLE_DAYS` whole local days ending on it."""
    try:  # the mini_depth/inputs.py helpers (addendum 2 item 6, B2 review L2); a refusal leaves depth unread
        name = tz_name or ""
        local_day = local_day_of(Window(start, start + timedelta(days=1)), name)
        noon = local_noon(local_day, name)
        day_lo, day_hi = renewable_bounds(start, tz_name)
    except MiniInputsRefused:
        reads.failed.append("mini_depth")
        return {d: None for d in DEPTH_DOMAINS}
    windows = {"renewable": (day_lo, day_hi)}
    windows.update({d: (noon.start, noon.end) for d in ("fuel", "service", "backup")})
    return {d: reads.call("mini_depth", ports.depth, d, *windows[d]) for d in DEPTH_DOMAINS}


def mini_readings(dispatch: dict[str, Any] | None, depth: dict[str, dict | None],
                  month: dict[str, Any] | None = None, mg1: ObjectiveFact | None = None) -> dict[str, Reading]:
    """OUT-D U4 table: MG-2 avoidable generator minutes (complete when none is unclear), MG-1 the month-to-date
    measured use by declared productive users (WALK1-3b, `mg1_reading`) or no sales record, MG-5 the service depth's
    unserved critical kWh."""
    out: dict[str, Reading] = {}
    avoidable, unclear = _dispatch_minutes(dispatch)
    if avoidable is not None:
        text = (MG2_UNCLEAR.format(m=num(unclear)) if avoidable == 0 < unclear
                else MG2_LONGER.format(m=num(avoidable)))
        out["MG-2"] = Reading(avoidable, unclear == 0, text)
    out["MG-1"] = mg1_reading(month, mg1)
    unserved = (((depth.get("service") or {}).get("cards") or {}).get("unserved_kwh"))
    out["MG-5"] = (Reading(None, False, MG5_UNMEASURED) if unserved is None
                   else Reading(Decimal(str(unserved)), True, MG5_UNSERVED.format(kwh=num(unserved))))
    return out


def mg1_reading(month: dict[str, Any] | None, mg1: ObjectiveFact | None) -> Reading:
    """WALK1-3b §A2.2: the month-to-date reading; complete only when the month is over and every day was checked. Its
    text follows the verdict `judge_month` gives the declared MG-1 objective (the same pure rule the board applies);
    with no checked day, or no productive user, it is "sales not recorded"."""
    if month is None or month.get("kwh") is None:
        return Reading(None, False, MG1_ACTUAL)
    mtd, c, e, m = month["kwh"], month["checked"], month["elapsed"], month["month_days"]
    reading = Reading(mtd, e == m and c == m, None, c, e, m)
    words = {"mtd": num(mtd), "c": c, "e": e, "m": m}
    verdict = judge_month(mg1, reading) if mg1 is not None else None
    if verdict in (ON_PACE, BEHIND_PACE):
        text = MG1_PACE.format(**words, avg=num(mtd / c), need=num(Decimal(mg1.target) / m))
    elif verdict == TOO_EARLY:
        text = MG1_TOO_EARLY.format(**words, d=plural(c, "day", "days"), k=mg1.min_checked_days)
    elif verdict == MISSED:
        text = MG1_MISSED.format(**words)
    else:  # MET, or no MG-1 objective declared
        text = MG1_SO_FAR.format(**words)
    return replace(reading, actual_text=text)


def _productive_month(reads: Reads, ports: MiniPorts, users: list[dict[str, Any]] | None, start: datetime,
                      tz_name: str | None) -> dict[str, Any] | None:
    """WALK1-3b §A2.2: measured use by the declared productive users over the Site-local calendar month containing
    the board day, from its first local day through the end of the board day. A checked day is a local day with any
    GOOD coverage; a day whose readings conflict (Addendum 3 M1) is not checked and adds nothing. None when no user is
    declared, the readings could not be read, or the Site zone is refused."""
    if not users:
        return None
    try:
        name = tz_name or ""
        local_day = local_day_of(Window(start, start + timedelta(days=1)), name)
        first = local_day.replace(day=1)
        bounds = [local_hour(first + timedelta(days=k), 0, name).start for k in range(local_day.day + 1)]
    except MiniInputsRefused:
        return None
    raw = reads.call("productive_readings", ports.productive_readings, [u.get("asset_id") for u in users],
                     bounds[0], bounds[-1], memo=True)  # CH5a1-R2: on day 1 of a month = the day read
    if raw is None:
        return None
    names = {u.get("asset_id"): str(u.get("name")) for u in users}
    mtd, checked = Decimal(0), 0
    for lo, hi in zip(bounds, bounds[1:]):
        kwh = productive_energy(raw, lo, hi, names)["kwh"]
        if kwh is not None:
            mtd, checked = mtd + kwh, checked + 1
    return {"kwh": mtd if checked else None, "checked": checked, "elapsed": local_day.day,
            "month_days": calendar.monthrange(local_day.year, local_day.month)[1]}


# CH-1a section 5c Q3c: the rule moved unchanged to analytics.dispatch_read (one rule, two callers).
_dispatch_minutes = dispatch_minutes


def _meets(head: Any, start: datetime, end: datetime) -> bool:
    """`in_window`: the head's episode intersects the board day `[start, end)`."""
    lo, hi = utc(head.episode_start), utc(head.episode_end)
    return lo is not None and lo < end and (hi is None or hi > start)


def _findings(rows: Any, placements: Any, c: str, start: datetime,
              end: datetime, work_lo: datetime | None = None) -> tuple[FindingFact, ...]:
    """Every Finding head over the work window (`ChainRequest.findings`, the index's head rule), closed ones included
    (M1b). `in_window` = the episode intersects the board day. Confidence (CH-5a2b R1, §B14 Q1/Q3): `place(...)`
    over the revision's chain placement facts (source provenance state, lifecycle, `recurs_after`), for the board-day
    heads only; None when the facts are missing or their read failed. By F1 the chip reads only the source state
    and the lifecycle (pinned by `test_cc_placement`), so no consequence, Action or coverage is passed."""
    out = []
    for r in rows:
        lo, hi = utc(r.episode_start), utc(r.episode_end)
        in_window = _meets(r, start, end)
        confidence = None
        facts = (placements or {}).get(str(r.revision_id).lower()) if in_window else None
        if facts is not None:
            row = {"lifecycle": r.lifecycle, "source_provenance": {"state": facts.get("source_state")},
                   "_recurs_after": facts.get("recurs_after_finding_id"),
                   "_recurs_after_title": facts.get("recurs_after_title"), "_transition": r.transition,
                   "_episode_end": r.episode_end}
            try:
                confidence = place(row, None, {}, None).confidence
            except Exception:  # noqa: BLE001 - a malformed fact leaves the chip null, never the board
                confidence = None
        title = FINDING_TITLE.get(str(r.lifecycle), FINDING_TITLE_FALLBACK)
        out.append(FindingFact(str(r.finding_id), str(r.revision_id), title, FINDING_MECHANISM, r.lifecycle,
                               refs.finding_ref(c, str(r.finding_id), str(r.revision_id)),
                               confidence_label=confidence, in_window=in_window,
                               in_work_window=work_lo is not None and lo is not None and lo < end
                               and (hi is None or hi > work_lo)))
    return tuple(out)


def _actions(reads: Reads, ports: MiniPorts, rows: Any, chain_rows: Any,
             c: str, site_timezone: str | None = None) -> tuple[tuple[ActionFact, ...], bool, tuple[str, ...]]:
    """Action index rows; the workflow label from the chain Action row of the same id (`ChainRequest.action_rows`,
    CH-5a2b R1) fed to `workflow_label` unchanged (addendum 2 item 2); verification and the Foundation change from
    `action_facts` (CH-5a1 C6: one verification summary per Action, one change query for all). `chain_rows` None
    means the `action_rows` read failed."""
    by_id = {str(a["action_id"]).lower(): a for a in chain_rows or ()}
    out, has_change, missing = [], False, []
    rows = list(rows)
    facts = reads.call("action_facts", ports.action_facts, [str(r["action_id"]) for r in rows]) if rows else ()
    by_fact = {f.action_id.lower(): f for f in facts or ()}
    for r in rows:
        aid = str(r["action_id"])
        event_id = str((r.get("selected_event") or {}).get("id") or "")
        state = r.get("state") or {}
        resolution = state.get("resolution") or {}
        chain_action = by_id.get(aid.lower())
        label = NOT_LOADED if chain_rows is None or chain_action is None else workflow_label(chain_action)
        if chain_rows is not None and chain_action is None:  # addendum 3 L3: text and notice never disagree
            missing.append(aid)
            if "action_rows" not in reads.failed:
                reads.failed.append("action_rows")
        is_open = label not in CLOSED_LABELS if label != NOT_LOADED else resolution.get("state") not in (
            "RESOLVED", "RESOLUTION_WITHDRAWN")
        fact = by_fact.get(aid.lower())
        summary = None if fact is None else {"state": fact.verification_state, "cost_check": fact.cost_check,
                                             "trial_hours": read_scope.thaw(fact.trial_hours)}
        has_change = has_change or bool(fact and fact.has_change)
        origin = r.get("origin") or {}
        out.append(ActionFact(
            aid, r.get("action_code"), "", None if origin.get("finding_id") is None else str(origin["finding_id"]),
            None if origin.get("finding_revision_id") is None else str(origin["finding_revision_id"]),
            state.get("application") == "APPLIED", is_open, None if summary is None else summary.get("state"),
            refs.action_ref(c, aid, event_id=event_id or None),
            workflow_label=label,
            verification_ref=refs.action_ref(c, aid, view="verification", event_id=event_id or None),
            cost_check=None if summary is None else read_scope.thaw(summary.get("cost_check")),
            trial_hours=_trial_hours(summary, site_timezone),
            source_class=None if fact is None else fact.source_class))
    return tuple(out), has_change, tuple(missing)


def _trial_hours(summary: dict[str, Any] | None, site_timezone: str | None) -> dict[str, Any] | None:
    """The summary's trial hours, with the Site zone the I-11 scope line reads its later window in (CH-3 §5)."""
    hours = None if summary is None else summary.get("trial_hours")
    if hours is None:
        return None
    lo, hi = utc(hours.get("later_start")), utc(hours.get("later_end"))
    if lo is None or hi is None:
        return dict(hours)
    if site_timezone:
        from zoneinfo import ZoneInfo
        lo, hi = lo.astimezone(ZoneInfo(site_timezone)), hi.astimezone(ZoneInfo(site_timezone))
    return {**hours, "later_local": {"start": f"{lo:%H:%M}", "end": f"{hi:%H:%M}", "day": lo.date()}}


def case_fact(r: dict[str, Any], kind: str, c: str) -> CaseFact:
    cid = str(r["case_id"])
    link = refs.case_ref(c, cid) if kind == MAINTENANCE_REQUEST else refs.site_ref(c, "work_incidents")
    fids = tuple(str(x["finding_id"]) for x in r.get("finding_links") or () if x.get("finding_id"))
    return CaseFact(cid, r.get("code"), kind, r.get("title") or "", r.get("state") or "",
                    None if r.get("asset_id") is None else str(r["asset_id"]), r.get("asset_label"), fids,
                    utc(r.get("occurred_at")), link)


def plan_fact(p: dict[str, Any], tz: ZoneInfo | None) -> PlanFact:
    due = utc(p.get("next_due_at"))
    hours = p.get("next_due_hours")
    return PlanFact(str(p["canonical_plan_id"]), p.get("code"), p.get("title") or "", p.get("trigger_kind") or "",
                    None if due is None else due.astimezone(tz or timezone.utc).date(),
                    None if hours is None else float(Decimal(str(hours))), p.get("state") or "",
                    None if p.get("asset_id") is None else str(p["asset_id"]),
                    refs.estate_ref("maintenance_preventive"), due)


# ---------------------------------------------------------------- contributors (§B.4 mini table)

def _sales_line(text: str, chip: Any = None) -> Contributor:
    return Contributor("productive_sales", "Productive-use sales", text, chip)


def _productive_sales(reads: Reads, ports: MiniPorts, c: str, start: datetime, end: datetime) -> dict[str, Any]:
    """WALK1-3 §4.4 table: the Grow headline, money, subline, MG-1 kWh and the two contributors for the board's UTC
    day `[start, end)`. The measured hours are those the readings cover; nothing is scaled to the whole day. A failed
    port reads "Not available yet · this record could not be loaded" and makes the board PARTIAL (B-Q17)."""
    users = reads.call("productive_users", ports.productive_users, start)
    if users is None:
        return {"subline": None, "contributors": (_sales_line(NOT_LOADED),)}
    if not users:
        return {"subline": GROW_SUBLINE, "contributors": (_sales_line(SALES_NO_USERS),)}
    return {**_measured_sales(reads, ports, c, start, end, users), "users": list(users)}


def _measured_sales(reads: Reads, ports: MiniPorts, c: str, start: datetime, end: datetime,
                    users: list[dict[str, Any]]) -> dict[str, Any]:
    """The §4.4 table for declared productive users (the caller handled the failed and empty user reads)."""
    price_href = refs.site_ref(c, "financial_assumptions")
    names = ", ".join(str(u.get("name")) for u in users)
    raw = reads.call("productive_readings", ports.productive_readings, [u.get("asset_id") for u in users],
                     start, end, memo=True)  # CH5a1-R2: the month read shares it on day 1
    series = reads.call("productive_price", ports.productive_price, start)
    sel = (series or {}).get("selection") or {}
    p = sel.get("price") or {}
    shown = price_text(p.get("value")) if sel.get("state") == "PRICED" and p.get("value") is not None else None
    value, cur = (Decimal(str(p["value"])), str(p.get("currency"))) if shown is not None else (None, None)
    if series is None:
        price = Contributor("productive_price", "Price per kWh", NOT_LOADED, None, price_href)
    elif value is None:
        price = Contributor("productive_price", "Price per kWh", PRICE_NOT_DECLARED, None, price_href)
    else:
        price = Contributor("productive_price", "Price per kWh", PRICE_DECLARED.format(p=shown, cur=cur), DECLARED,
                            price_href)
    if raw is None:
        return {"subline": None, "contributors": (_sales_line(NOT_LOADED), price)}
    energy = productive_energy(raw, start, end, {u.get("asset_id"): str(u.get("name")) for u in users})
    kwh = energy["kwh"]
    if energy["conflict_assets"]:
        who = energy["conflict_assets"]
        text = SALES_CONFLICT.format(names=", ".join(who), verb="have" if len(who) > 1 else "has")
        return {"subline": None, "contributors": (_sales_line(text), price)}
    if kwh is None:
        return {"subline": None, "contributors": (_sales_line(SALES_NO_READINGS.format(names=names)), price)}
    h = num(Decimal(energy["measured_seconds"]) / Decimal(3600))
    words = {"kwh": num(kwh), "names": names, "h": h, "hours": plural(h, "hour", "hours")}
    if value is None:
        return {"kwh": kwh, "subline": None, "contributors": (_sales_line(SALES_NO_PRICE.format(**words)), price)}
    out = {"kwh": kwh, "subline": SALES_SUBLINE.format(**words, p=shown, cur=cur),
           "contributors": (_sales_line(SALES_USED.format(**words), DECLARED), price)}
    if kwh == 0:  # L3: the spare-solar headline leads on a zero-use day when one exists (see compose)
        return {**out, "headline": SALES_ZERO_HEADLINE.format(names=names), "money": None, "zero": True}
    amount = f"{(kwh * value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):f}"
    return {**out, "headline": SALES_HEADLINE, "money": {"amount_low": amount, "amount_high": amount, "currency": cur}}


def _grow(c: str, depth: dict, eligible: Any, assessed: Any, rc: Any,
          sales: tuple[Contributor, ...] = (), href: dict[str, Any] | None = None) -> tuple[Contributor, ...]:
    href = href or refs.evidence_ref(c, "renewable")
    if depth.get("renewable") is None:
        use = not_available("productive_use", "Productive use", href)
    elif eligible is None or assessed is None:
        use = Contributor("productive_use", "Productive use", SOLAR_NOT_READ, None, href)
    else:
        text = SOLAR_WELL_OBSERVED.format(e=eligible, a=assessed, days=plural(assessed, "day", "days"))
        # MOCK DEVIATION (R685): the mock's "of 5" is the days checked, and unchecked days are stated (R687: none).
        if assessed < RENEWABLE_DAYS:  # WALK1-5: assess the days read, state the rest
            text += SOLAR_NOT_CHECKED.format(n=RENEWABLE_DAYS - assessed)
        use = Contributor("productive_use", "Productive use", text, rc, href)
    # WALK1-3b §A2.3 order: Productive-use sales (a), [the "Declared objective" line (b), placed by the board after
    # "productive_sales"], Productive use spare solar (c), Price per kWh, Cash collected, Site earnings.
    return (*sales[:1], use, *sales[1:], Contributor("cash_collected", "Cash collected", FIXED["cash"]),
            Contributor("site_earnings", "Site earnings", FIXED["earnings"]))


def _cost(c: str, dispatch: Any, depth: dict, price: Any, lead: FindingFact | None,
          rc: Any) -> tuple[Contributor, ...]:
    a, u = _dispatch_minutes(dispatch)
    gen_href = refs.evidence_ref(c, "dispatch")
    if dispatch is None:
        gen = not_available("generator_use", "Generator use", gen_href)
    else:
        chip = PLACEMENT_CHIP.get(lead.confidence_label) if lead and lead.confidence_label else None
        gen = Contributor("generator_use", "Generator use", f"{num(a)} min avoidable, {num(u)} min unclear",
                          chip, gen_href)
    fuel_href = refs.evidence_ref(c, "fuel")
    if depth.get("fuel") is None:
        fuel = not_available("fuel", "Fuel", fuel_href)
    else:
        opening = (depth["fuel"].get("cards") or {}).get("opening_l")
        fuel = (Contributor("fuel", "Fuel", NO_FUEL_BALANCE, UNKNOWN_CHIP, fuel_href) if opening is None else
                Contributor("fuel", "Fuel", f"{num(opening)} L at the start of the window", rc, fuel_href))
    price_href = refs.site_ref(c, "financial_assumptions")
    if price is None:
        fuel_price = not_available("fuel_price", "Fuel price", price_href)
    else:
        sel = price.get("selection") or {}
        p = sel.get("price") or {}
        shown = price_text(p.get("value")) if p.get("value") is not None else None
        text = (f"Declared at {shown} {p.get('currency')} per litre"
                if sel.get("state") == "PRICED" and shown is not None else PRICE_FALLBACK)
        fuel_price = Contributor("fuel_price", "Fuel price", text, DECLARED, price_href)
    return gen, fuel, fuel_price


def protect_clear(reserve: tuple[int, int] | None) -> str:
    """L2: the no-warning Protect headline; `PROTECT_HEADLINE` unless m >= 1 periods were assessed."""
    if reserve is None or reserve[1] < 1:
        return PROTECT_HEADLINE
    m = reserve[1]
    return PROTECT_CLEAR.format(m=m, periods=plural(m, "period", "periods"))


def reserve_counts(dispatch: dict[str, Any] | None) -> tuple[int, int] | None:
    """(n, m): assessed generator periods whose result names a reserve constraint, of all assessed periods.
    Read from `binding_constraints` only, never from reason prose; None when the dispatch read failed."""
    if dispatch is None:
        return None
    intervals = list(dispatch.get("intervals") or ())
    n = sum(1 for x in intervals
            if set((x.get("result") or {}).get("binding_constraints") or ()) & set(RESERVE_CONSTRAINTS))
    return n, len(intervals)


def _battery(c: str, reserve: tuple[int, int] | None, rc: Any) -> Contributor:
    href = refs.site_ref(c, "health")
    if reserve is None:
        return not_available("battery", "Battery", href)
    n, m = reserve
    if n >= 1:
        text = f"At or near the reserve during {n} of {m} assessed generator {plural(m, 'period', 'periods')}"
    elif m > 0:
        text = f"No generator period at or near the reserve ({m} assessed)"
    else:
        text = NO_PERIOD_ASSESSED
    return Contributor("battery", "Battery", text, rc, href)


def _protect(c: str, depth: dict, plans: tuple[PlanFact, ...], plans_failed: bool,
             reserve: tuple[int, int] | None = None, rc: Any = None) -> tuple[Contributor, ...]:
    battery = _battery(c, reserve, rc)
    run_hours = [p for p in sorted(plans, key=lambda p: (p.code or "", p.plan_id)) if p.trigger_kind == "RUN_HOURS"]
    if plans_failed:
        generator = not_available("generator", "Generator", refs.estate_ref("maintenance_preventive"))
    elif not run_hours:
        generator = Contributor("generator", "Generator", NO_GEN_PLAN, PLAN_RECORD,
                                refs.estate_ref("maintenance_preventive"))
    else:
        due = run_hours[0].next_due_hours
        generator = Contributor("generator", "Generator",
                                f"Service due at {num(due)} operating {plural(num(due), 'hour', 'hours')} · hours "
                                "since service not recorded"
                                if due is not None else NO_GEN_PLAN, PLAN_RECORD,
                                refs.estate_ref("maintenance_preventive"))
    svc_href = refs.evidence_ref(c, "service")
    if depth.get("service") is None:
        service = not_available("service_delivery", "Service delivery", svc_href)
    elif (depth["service"].get("cards") or {}).get("delivered_load_kw") is None:
        service = Contributor("service_delivery", "Service delivery", SERVICE_NOT_READ, None, svc_href)
    else:
        service = Contributor("service_delivery", "Service delivery", SERVICE_MEASURED, UNKNOWN_CHIP, svc_href)
    bk_href = refs.evidence_ref(c, "backup")
    if depth.get("backup") is None:
        backup = not_available("backup_readiness", "Backup readiness", bk_href)
    else:
        cards = depth["backup"].get("cards") or {}
        outages, starts = cards.get("outage_count"), cards.get("start_success_count")
        text = (NO_BACKUP_EVENT if not outages and starts is None
                else f"{starts or 0} backup {plural(starts or 0, 'start', 'starts')} recorded")
        backup = Contributor("backup_readiness", "Backup readiness", text, UNKNOWN_CHIP, bk_href)
    return battery, generator, service, backup


def no_run_day(base: bool, assessment: dict, readiness: Any) -> bool:
    """POLISH §1.7 (P-12): a current day whose dispatch reading is COMPLETE with zero assessed intervals and whose
    readiness is exactly UNKNOWN had no generator run to check, so MG-7 is settled. Narrow to the mini board: the
    shared `claim_limit_read.reduce_day` still maps zero intervals to UNKNOWN for the Portfolio."""
    return (base and readiness == "UNKNOWN" and assessment.get("claim_level") == "COMPLETE"
            and not (assessment.get("dispatch_intervals") or ()))


def _is_zero(value: Any) -> bool:
    try:
        return value is not None and Decimal(str(value)) == 0
    except InvalidOperation:
        return False


def _assure(c: str, actions: tuple[ActionFact, ...], body: dict, overview_ok: bool, readiness: Any, rc: Any,
            limitations: list[str], actions_failed: bool, no_run: bool = False) -> tuple[Contributor, ...]:
    out: list[Contributor] = []
    mine = sorted((a for a in actions if not a.is_domain), key=lambda a: (a.code or "", a.action_id))
    if actions_failed and not mine:
        out.append(not_available("verified_results", "Verified results"))
    elif not mine:
        out.append(Contributor("verified_results", "Verified results", NO_VERIFIED))
    for a in mine:
        state = a.verification_state
        text = VERIFICATION_TEXT.get(state or "", None)
        cc = a.cost_check or {}
        if state == "VERIFIED" and cc.get("state") == "MODELLED_IMPROVEMENT":
            text = VERIFIED_WITH_COST.replace("{amount}", per_kwh_amount(cc)).replace(
                "{currency}", cc.get("currency") or "")
        out.append(Contributor("verified_results", "Verified results",
                               text.format(code=display_code(a.code), suffix=provenance_suffix(a.source_class))
                               if text else NOT_LOADED,
                               PENDING_CHIP if state in PENDING_STATES else None, a.verification_ref))
    out.append(Contributor("actual_against_plan", "Actual against plan", FIXED["plan_target"]))
    if not overview_ok:
        out.append(not_available("readings", "Readings", refs.evidence_ref(c)))
    elif no_run:
        # Addendum 4 item 3: the settled no-run day reads FULL on this line only; the shared readiness is unchanged
        out.append(Contributor("readings", "Readings", NO_RUN_READINGS, readiness_confidence("FULL"),
                               refs.evidence_ref(c)))
    else:
        src = ((body.get("money") or {}).get("source_provenance") or {}).get("state")
        word = READINESS_WORD.get(readiness or "UNKNOWN", "Unknown")
        out.append(Contributor("readings", "Readings",
                               f"{SOURCE_TEXT.get(src or 'UNKNOWN', SOURCE_UNRESOLVED)} · readiness {word}",
                               rc, refs.evidence_ref(c)))
    if limitations:
        out.append(Contributor("battery_reporting", "Battery reporting", limitation_text(limitations[0]),
                               HIGH_CHIP, refs.evidence_ref(c)))
    return tuple(out)
