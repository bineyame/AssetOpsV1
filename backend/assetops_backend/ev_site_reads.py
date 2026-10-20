"""W2-07 commit 3: the five selected EV Site reads (`.agent/W2-07-build-spec.md` "Five selected reads", "Commits 2-3",
concrete-artifact closure section 2, the post-W2-06 reconciliation and q1-q4).

A pure composition over injected collaborators: `reads` is W2-06's `EvReadService` (its own snapshot, currentness,
envelope, denominator, provenance, completeness and Finding IDs, called on one caller connection) and `money` is the
SELECT-only `EvMoneyReads` of the consequence adapter. Every route opens exactly one read-only repeatable-read
transaction; the public envelope is W2-06's, unchanged, with W2-07 fields alongside it.

q4: one current-revision selector for all five routes. UNKNOWN (no exact selection) -> no consequence; HISTORICAL
(explicit earlier cutoff) and PENDING_RECOMPUTE (overlapping job) -> no current amount, stored rows only as labelled
`Historical scenario` history; CURRENT -> derive the exact basis on this connection (commit-2 rules + pure
`ev_money.derive`) and select only the stored revision with that basis; a derived basis with no stored row is the
read guard `WITHHELD/STALE_BASIS` (never inserted).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable
from uuid import UUID

from assetops_backend.analytics.ev import SESSION_ANALYTIC, plain
from assetops_backend.analytics.ev_reads import EvPinnedLineageUnavailable
from assetops_backend.financials import ev_money as em

NO_MONEY = "No gross tariff scenario assessed."
HISTORY_LABEL = "Historical scenario"
NOT_INCLUDED = ["lost_sales", "collections", "margin", "repair", "warranty"]
#: q1 R5/R6 visible copy per (guard or stored) reason.
MONEY_COPY = {
    "HISTORICAL_CURRENT_CLAIM": HISTORY_LABEL,
    em.ERROR_PENDING: "New evidence is being assessed. The previous result may change.",
    em.SOURCE_GATE: "EV source or binding is unverified; session outcomes cannot be assessed.",
    em.CONTRADICTORY: "Accepted EV records conflict; no current gross tariff estimate.",
    "STALE_BASIS": "The gross tariff scenario is being refreshed.",
    em.INCOMPLETE: "Delivered energy is incomplete for pricing; partial metered energy is shown separately.",
    em.TARIFF_MISSING: "No published EV tariff covers the eligible delivery.",
    em.PRICE_GAP: "One tariff revision does not cover all eligible delivery intervals.",
    em.ELIGIBLE: "Gross tariff scenario; not cash collected.",
}
#: Public claim vocabulary role -> accepted binding role (`sites/binding_roles.EV_ROLES_1`).
ROLE_OF = {"session_event": "ev_session_event", "connector_meter_delta": "ev_connector_energy",
           "connector_status": "ev_connector_state", "fault_event": "ev_connector_fault",
           "site_import": "ev_site_import", "requested_power": "ev_requested_power",
           "allocated_limit": "ev_allocated_limit"}
PUBLIC_ROLE = {v: k for k, v in ROLE_OF.items()}
TARIFF_ROLE = em.TARIFF_KEY
#: (claim, required public roles, roles whose accepted IDs the row cites, limitation, highest state allowed).
CLAIMS = (
    ("SESSION_OUTCOME", ("session_event",), ("session_event",), None, "SUPPORTED"),
    ("SERVICE_STATE", ("connector_status",), ("connector_status",), "Availability is not assessed.", "LIMITED"),
    ("DELIVERED_ENERGY", ("session_event", "connector_meter_delta"), ("connector_meter_delta",), None, "SUPPORTED"),
    ("FAULT_ASSOCIATION", ("session_event", "fault_event"), ("fault_event",), "Cause is not established.",
     "LIMITED"),
    ("SITE_POWER_CONTEXT", ("site_import",), ("site_import",), None, "SUPPORTED"),
    ("POWER_CONSTRAINT", ("site_import", "requested_power", "allocated_limit"),
     ("site_import", "requested_power", "allocated_limit"), None, "LIMITED"),
    ("GROSS_TARIFF_SCENARIO", ("connector_meter_delta", TARIFF_ROLE), ("connector_meter_delta",),
     "Gross scenario only.", "SUPPORTED"),
)
NEXT_EVIDENCE = {
    "TERMINAL_GAP": ("Recover the missing session end report", "Needed before a session outcome is complete.",
                     "analysis"),
    "METER_GAP": ("Recover connector meter intervals", "Needed before delivered energy is complete.", "analysis"),
    "STATUS_GAP": ("Recover connector status history", "Needed before connector availability can be assessed.",
                   "analysis"),
    "INDEPENDENT_POWER_GAP": ("Record requested and allocated power",
                              "Independent requested and allocated readings are needed before a power constraint "
                              "can be assessed.", "analysis"),
    "SITE_IMPORT_GAP": ("Record Site import power", "Needed for Site power context.", "analysis"),
    "TARIFF_GAP": ("Publish an EV gross tariff", "Needed before a gross tariff scenario can be estimated.",
                   "financials"),
    "BILLING_GAP": ("Connect billing records", "Needed before any amount can be stated as collected.",
                    "financials"),
}
KIND_TEXT = {"EV_SESSION_START": "Session started", "EV_SESSION_END": "Session ended",
             "EV_SESSION_ABORT": "Session aborted", "EV_CONNECTOR_FAULT": "Connector fault",
             "EV_CONNECTOR_CLEAR": "Connector fault cleared"}
#: Review r1 M3: the plain suffix of the first Analysis cell, by accepted binding role (all eight `EV_ROLES_1`).
SOURCE_SUFFIX = {"ev_session_event": "session", "ev_connector_fault": "connector fault",
                 "ev_connector_state": "connector status", "ev_connector_energy": "energy",
                 "ev_connector_power": "connector power", "ev_site_import": "site import",
                 "ev_requested_power": "requested power", "ev_allocated_limit": "allocated power limit"}
UNKNOWN_SOURCE_SUFFIX = "EV reading"
#: W3-02 0c r1 H1: the pinned `STALE_BASIS` copy (the as-of tariff basis has no stored head by K), and the label of
#: an explicit earlier cutoff.
STALE_AS_OF_COPY = "Withheld · tariff basis has no stored consequence at this evidence cutoff"
HISTORICAL_AS_OF = "Historical as of {known_at}"
#: Review r1 M3: the plain word of each connector state (`sites/binding_roles.EV_CONNECTOR_STATES`).
STATE_TEXT = {"AVAILABLE": "Available", "UNPLUGGED": "Unplugged", "PLUGGED": "Plugged in",
              "AUTHORIZING": "Authorizing", "CHARGING": "Charging", "FAULTED": "Faulted", "DISABLED": "Disabled"}
UNRECOGNISED_STATE = "State not recognised"
SOURCE_UNVERIFIED_NOTE = "Source or binding unverified for this record."
#: q5 R3: the limitation of a claim whose interval-level numerator and denominator are not proved.
COVERAGE_UNKNOWN = "Coverage duration cannot be calculated from the selected records."
NULL_COVERAGE = {"known_seconds": None, "expected_seconds": None, "ratio": None, "unit": None}
WEEKDAYS = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY")


def _dec(value: Any) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def _union(spans) -> list[tuple[datetime, datetime]]:
    """Merge half-open spans; an overlap or a duplicate is counted once."""
    out: list[list[datetime]] = []
    for a, b in sorted(x for x in spans if x[1] > x[0]):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def _intersect(left, right) -> list[tuple[datetime, datetime]]:
    out, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        a, b = max(left[i][0], right[j][0]), min(left[i][1], right[j][1])
        if b > a:
            out.append((a, b))
        if left[i][1] < right[j][1]:
            i += 1
        else:
            j += 1
    return out


def _measure(spans) -> timedelta:
    return sum((b - a for a, b in spans), timedelta(0))


def _seconds(span: timedelta) -> int | float:
    value = span.total_seconds()
    return int(value) if value.is_integer() else value


def _coverage(known: timedelta, expected: timedelta, unit: str) -> dict[str, Any]:
    """q5 R3: exact measured coverage; `unit` states WINDOW_SECONDS or summed SESSION_SECONDS."""
    if expected <= timedelta(0):
        return dict(NULL_COVERAGE)
    us = lambda d: Decimal(d // timedelta(microseconds=1))  # noqa: E731
    return {"known_seconds": _seconds(known), "expected_seconds": _seconds(expected),
            "ratio": format((us(known) / us(expected)).normalize(), "f"), "unit": unit}


def _instant(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        at = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return at if at.tzinfo is not None else None


def enabled_connectors(foundation: dict[str, Any] | None) -> set[str]:
    """q6 R1: the effective Foundation's enabled connector component IDs (`ev-connector-enabled=ENABLED`), with or
    without a weekly schedule."""
    if foundation is None:
        return set()
    return {c["component_id"] for c in foundation["content"].get("components") or ()
            if c.get("component_type") == "EV_CONNECTOR"
            and {p["property_key"]: p["value"] for p in c.get("properties") or ()}.get("ev-connector-enabled")
            == "ENABLED"}


def service_windows(foundation: dict[str, Any] | None, assets: dict[str, str], lo: datetime | None,
                    hi: datetime | None) -> list[dict[str, Any]]:
    """q5 R1: every enabled connector's configured weekly occurrence intersecting `[lo,hi)`, resolved with its
    declared offset (W2-05a validated it unambiguous), unclipped, deduplicated across connectors, in start/end/ID
    order. Configuration only, never observed availability."""
    if foundation is None or lo is None or hi is None:
        return []
    found: dict[tuple[datetime, datetime], set[str]] = {}
    enabled = enabled_connectors(foundation)
    for schedule in foundation["content"].get("connector_enable_schedules") or ():
        weekly = schedule.get("weekly") or ()
        asset = assets.get(schedule.get("connector_asset_id"))
        if not weekly or asset is None or schedule.get("connector_asset_id") not in enabled:
            continue
        for w in weekly:
            if w.get("weekday") not in WEEKDAYS:
                continue
            try:
                h1, m1 = (int(x) for x in str(w["local_start"]).split(":"))
                h2, m2 = (int(x) for x in str(w["local_end"]).split(":"))
                offset = timedelta(minutes=int(w["utc_offset_minutes"]))
            except (KeyError, ValueError, TypeError):
                continue
            first = (lo + offset).date() - timedelta(days=1)
            day = first + timedelta(days=(WEEKDAYS.index(w["weekday"]) - first.weekday()) % 7)
            while day <= (hi + offset).date() + timedelta(days=1):
                base = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc) - offset
                start, end = base + timedelta(hours=h1, minutes=m1), base + timedelta(hours=h2, minutes=m2)
                if end > start and start < hi and end > lo:
                    found.setdefault((start, end), set()).add(asset)
                day += timedelta(days=7)
    return [{"from": plain(a), "to": plain(b),
             "connector_asset_ids": sorted(ids)} for (a, b), ids in sorted(found.items(),
                                                                           key=lambda x: (x[0], sorted(x[1])))]


def _utc_words(at: datetime) -> str:
    return at.strftime("%Y-%m-%d %H:%M")


def objective_windows(foundation: dict[str, Any] | None, assets: dict[str, str], lo: datetime | None,
                      hi: datetime | None) -> tuple[dict[str, str] | None, list[dict[str, Any]], bool]:
    """q5 R1/q6 R1: `(configured_service_window, configured_service_windows, service_schedule_declared)`. The single
    window is nonnull only when exactly one occurrence is common to every enabled connector of the Foundation;
    `declared` keeps a declared weekly schedule with no selected overlap distinct from missing configuration."""
    windows = service_windows(foundation, assets, lo, hi)
    schedules = [] if foundation is None else foundation["content"].get("connector_enable_schedules") or []
    on = enabled_connectors(foundation)
    declared = any(x.get("weekly") and x.get("connector_asset_id") in on for x in schedules)
    # q6 R1: common only when the one occurrence covers every enabled connector, scheduled or not.
    enabled = {assets.get(x) for x in on}
    common = ({"from": windows[0]["from"], "to": windows[0]["to"]}
              if len(windows) == 1 and enabled and set(windows[0]["connector_asset_ids"]) == enabled else None)
    return common, windows, declared


def _positive(seq: Any) -> bool:
    try:
        return int(seq) > 0
    except (TypeError, ValueError):
        return False


class EvSiteReads:
    def __init__(self, reads: Any, money: Any,
                 derive: Callable[[em.EvMoneyBasis], em.EvConsequence | None] = em.derive) -> None:
        self._reads, self._money, self._derive = reads, money, derive

    def dispose(self) -> None:
        self._reads.dispose()

    # --- the shared snapshot and money selector ----------------------------------------------------------------

    def _ctx(self, c, t: UUID, s: UUID, code: str, lo, hi, known_at) -> dict[str, Any]:
        snap, body = self._reads.open_on(c, t, s, code, lo, hi, known_at)
        ctx = {"c": c, "t": t, "s": s, "code": code, "snap": snap, "body": body}
        ctx["money"] = self._select(ctx)
        return ctx

    def _select(self, ctx: dict[str, Any], cutoff: datetime | None = None) -> dict[str, Any]:
        """q4: the one shared current-revision selector. Default (`cutoff` None) unchanged; a pinned estate
        `cutoff` is `_select_as_of`."""
        if cutoff is not None:
            return self._select_as_of(ctx, cutoff)
        c, t, s, snap = ctx["c"], ctx["t"], ctx["s"], ctx["snap"]
        lo, hi, state = snap["lo"], snap["hi"], snap["state"]
        history = [] if lo is None else self._money.history_on(c, t, s, lo, hi)
        current, guard, derived = None, None, None
        if state == "CURRENT":
            basis = self._money.basis_on(c, t, s, lo, hi, snap["selected"])
            derived = None if basis is None else self._derive(basis)
            if derived is not None:
                current = self._money.select_on(c, t, s, lo, hi, derived.basis_sha256)
                if current is None:
                    guard = "STALE_BASIS"
        elif state in ("HISTORICAL", "PENDING_RECOMPUTE") and history:
            guard = "HISTORICAL_CURRENT_CLAIM" if state == "HISTORICAL" else em.ERROR_PENDING
        return {"current": current, "guard": guard, "derived": derived,
                "history": [h for h in history if current is None or h["id"] != current["id"]]}

    def _select_as_of(self, ctx: dict[str, Any], cutoff: datetime) -> dict[str, Any]:
        """W3-02 0c r1 H1: the pinned selector as of the estate cutoff K. The basis is derived from the tariff
        assignments recorded at K and the head is the matching revision recorded by K (a later tariff or head is
        neither selected nor refused); history is the stored revisions recorded by K. A HISTORICAL pin still
        identifies its stored as-of head (guard `HISTORICAL_CURRENT_CLAIM`: labelled history, no current claim); no
        matching head by K is `STALE_BASIS`."""
        c, t, s, snap = ctx["c"], ctx["t"], ctx["s"], ctx["snap"]
        lo, hi, state = snap["lo"], snap["hi"], snap["state"]
        history = [h for h in self._money.history_on(c, t, s, lo, hi) if h["recorded_at"] <= cutoff]
        current, guard, derived = None, None, None
        if state in ("CURRENT", "HISTORICAL"):
            basis = self._money.basis_on(c, t, s, lo, hi, snap["selected"], known_at=cutoff)
            derived = None if basis is None else self._derive(basis)
            if derived is not None:
                current = self._money.select_on(c, t, s, lo, hi, derived.basis_sha256, known_at=cutoff)
                guard = "STALE_BASIS" if current is None else (
                    "HISTORICAL_CURRENT_CLAIM" if state == "HISTORICAL" else None)
            elif state == "HISTORICAL" and history:
                guard = "HISTORICAL_CURRENT_CLAIM"
        elif state == "PENDING_RECOMPUTE" and history:
            guard = em.ERROR_PENDING
        return {"current": current, "guard": guard, "derived": derived,
                "history": [h for h in history if current is None or h["id"] != current["id"]]}

    def _consequence(self, ctx: dict[str, Any]) -> dict[str, Any] | None:
        m = ctx["money"]
        row = m["current"]
        if row is None and m["guard"] is None:
            return None
        if row is not None and m["guard"] == "HISTORICAL_CURRENT_CLAIM":  # pinned as-of head: history, no claim
            return {**self._revision(row, HISTORY_LABEL), "label": HISTORY_LABEL}
        if row is None:  # a read guard: null current amount, never a stored row
            return {"revision_id": None, "revision_no": None, "state": "WITHHELD", "reason": m["guard"], "quantity_kwh": None,
                    "tariff_revision_id": None, "tariff_value": None, "currency": None, "amount": None,
                    "overlap_group": None, "recorded_at": None, "tariff_recorded_at": None, "source_gate": None,
                    "session_revision_ids": [], "evidence_ids": [], "limitation": MONEY_COPY[m["guard"]]}
        return self._revision(row, MONEY_COPY.get(row["reason"]))

    # --- pinned estate facades (W3-02 0c) -------------------------------------------------------------------------

    def _pinned_ctx(self, c, snap: dict[str, Any]) -> dict[str, Any]:
        """The context of one already pinned estate window (an `EvReadService.estate_snapshots_on` result), built
        without `_ctx`/`open_on`: its one exact session seq selected, its row-local `known` at or before both the
        selection cutoff and the committed watermark, and the money selected under that cutoff. Anything else is
        `EvPinnedLineageUnavailable` (the estate's inconsistent selection), never a re-read. 0c r1 L3: the one seq
        must be the `ev-session/1` analytic's, positive; the upstream pinned `_snapshot` proves its window."""
        cutoff, seqs = snap.get("selection_cutoff"), snap.get("selection_seqs")
        known, mark = snap.get("known"), snap.get("watermark")
        if (cutoff is None or not seqs or set(seqs) != {SESSION_ANALYTIC} or not _positive(seqs[SESSION_ANALYTIC])
                or snap.get("selected") is None or snap.get("lo") is None or snap.get("hi") is None
                or known is None or known > cutoff or (mark is not None and known > mark)):
            raise EvPinnedLineageUnavailable("The pinned EV window selection cannot be proved.")
        ctx = {"c": c, "t": snap["t"], "s": snap["s"], "code": snap["code"], "snap": snap, "cutoff": cutoff}
        ctx["money"] = self._select(ctx, cutoff)
        return ctx

    @staticmethod
    def _pinned_ids(snap: dict[str, Any]) -> dict[str, Any]:
        (analytic, seq), = snap["selection_seqs"].items()
        return {"window_start": plain(snap["lo"]), "window_end": plain(snap["hi"]), "known_at": plain(snap["known"]),
                "selection_seqs": {analytic: int(seq)},
                "assessment_revision_id": str(snap["selected"]["revision_id"]).lower(),
                "evidence_ids": list(snap["selected"]["evidence_ids"])}

    def capabilities_on(self, c, pinned_snap: dict[str, Any]) -> dict[str, Any]:
        """W3-02 0c: the W2 capability rows of one already pinned estate window on the caller's connection (no
        `_ctx`, `open_on`, `overview` or `evidence`), with that window's exact selected IDs. `unknown_meter`
        (W3-02 c1-q2) is whether any exact selected session has positive unknown meter seconds, from the same
        cached context (no second snapshot or transaction)."""
        ctx = self._pinned_ctx(c, pinned_snap)
        capabilities = self._capabilities(ctx)
        unknown_meter = any((session.get("unknown_meter_seconds") or 0) > 0 for session in self._sessions(ctx))
        return {**self._pinned_ids(pinned_snap), "capabilities": capabilities, "unknown_meter": unknown_meter}

    def money_on(self, c, pinned_snap: dict[str, Any]) -> dict[str, Any]:
        """W3-02 0c: the W2 consequence of one already pinned estate window (the stored head DTO, or the transient
        `revision_id: null` guard, never a stored row) and its stored history recorded by the cutoff, with full IDs
        (`financials` without `_ctx`, paging or provenance)."""
        ctx = self._pinned_ctx(c, pinned_snap)
        m = ctx["money"]
        consequence = self._consequence(ctx)
        if m["guard"] == "STALE_BASIS":
            consequence = {**consequence, "limitation": STALE_AS_OF_COPY}
        historical = HISTORICAL_AS_OF.format(known_at=plain(pinned_snap["known"]))             if pinned_snap["state"] == "HISTORICAL" else None
        return {**self._pinned_ids(pinned_snap), "state": pinned_snap["state"], "guard": m["guard"],
                "historical_label": historical, "consequence": consequence,
                "history": [{**self._revision(h, HISTORY_LABEL), "label": HISTORY_LABEL} for h in m["history"]]}

    @staticmethod
    def _revision(row: dict[str, Any], limitation: str | None) -> dict[str, Any]:
        return {"revision_id": plain(row["id"]), "revision_no": row["revision_no"], "state": row["state"], "reason": row["reason"],
                "quantity_kwh": plain(row["quantity_kwh"]), "tariff_revision_id": plain(row["tariff_revision_id"]),
                "tariff_value": plain(row["tariff_value"]), "currency": row["currency"],
                "amount": plain(row["amount"]), "overlap_group": row["overlap_group"],
                "recorded_at": plain(row["recorded_at"]), "tariff_recorded_at": plain(row["tariff_recorded_at"]),
                "source_gate": row["source_gate"], "session_revision_ids": list(row["session_revision_ids"]),
                "evidence_ids": list(row["evidence_ids"]), "limitation": limitation}

    # --- shared pieces -------------------------------------------------------------------------------------------

    def _links(self, ctx: dict[str, Any], own: str) -> dict[str, Any]:
        snap, base = ctx["snap"], f"/sites/{ctx['code']}/ev"
        q = "" if snap["lo"] is None or snap["known"] is None else (
            f"?from={plain(snap['lo'])}&to={plain(snap['hi'])}&known_at={plain(snap['known'])}")
        paths = {"self": base + own, "evidence": base + "/evidence", "analysis": base + "/evidence/analysis",
                 "financials": base + "/financials"}
        return {"self": paths["self"] + q, "evidence": paths["evidence"] + q, "analysis": paths["analysis"] + q,
                "finding": None, "financials": paths["financials"] + q}

    def _accepted(self, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        if "accepted" not in ctx:
            ctx["accepted"] = self._reads.accepted_on(ctx["c"], ctx["snap"])
        return ctx["accepted"]

    def _sessions(self, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        if "sessions" not in ctx:
            ctx["sessions"] = self._reads.sessions_on(ctx["c"], ctx["snap"])
        return ctx["sessions"]

    def _tariffs(self, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        if "tariffs" not in ctx:
            snap = ctx["snap"]
            if snap["lo"] is None:
                ctx["tariffs"] = []
            elif ctx.get("cutoff") is None:
                ctx["tariffs"] = self._money.tariff_on(ctx["c"], ctx["t"], ctx["s"], snap["lo"], snap["hi"])
            else:  # W3-02 0c r1: a pinned read discloses the tariff assignments recorded at K
                ctx["tariffs"] = self._money.tariff_on(ctx["c"], ctx["t"], ctx["s"], snap["lo"], snap["hi"],
                                                       known_at=ctx["cutoff"])
        return ctx["tariffs"]

    def _as_of(self, ctx: dict[str, Any]) -> str | None:
        sel = ctx["snap"]["selected"]
        return None if sel is None else plain(sel["created_at"])

    def _window(self, ctx: dict[str, Any]) -> timedelta:
        snap = ctx["snap"]
        return timedelta(0) if snap["lo"] is None else snap["hi"] - snap["lo"]

    def _intervals(self, ctx: dict[str, Any], role: str) -> list[tuple[datetime, datetime]]:
        """The union of accepted, selected (not EXCLUDED) `role` intervals clipped to the window."""
        lo, hi = ctx["snap"]["lo"], ctx["snap"]["hi"]
        return _union((max(r["interval_start"], lo), min(r["interval_end"], hi)) for r in self._accepted(ctx)
                      if r["role"] == role and r["use"] != "EXCLUDED"
                      and r["interval_start"] is not None and r["interval_end"] is not None)

    def _site_import(self, ctx: dict[str, Any]) -> tuple[list[tuple[datetime, datetime]], Decimal | None]:
        lo, hi = ctx["snap"]["lo"], ctx["snap"]["hi"]
        peak = None
        for r in self._accepted(ctx):
            if (r["role"] == ROLE_OF["site_import"] and r["use"] != "EXCLUDED" and r["interval_start"] is not None
                    and r["interval_end"] is not None and min(r["interval_end"], hi) > max(r["interval_start"], lo)):
                value = _dec(r["value"])
                peak = value if peak is None or (value is not None and value > peak) else peak
        return self._intervals(ctx, ROLE_OF["site_import"]), peak

    def _spans(self, ctx: dict[str, Any]) -> dict[str, tuple[datetime, datetime]] | None:
        """q5 R3: each selected session's proved active span `[START, END/ABORT)` by session ID; None when any
        selected session has no proved terminal span (INCOMPLETE or a missing end), or there is no session."""
        spans = {}
        for x in self._sessions(ctx):
            a, b = _instant(x["start_at"]), _instant(x["end_at"])
            if x["state"] == "INCOMPLETE" or a is None or b is None or b <= a:
                return None
            spans[x["session_id"]] = (a, b)
        return spans or None

    def _session_coverage(self, ctx: dict[str, Any], spans, evidence_ids: set[str] | None) -> dict[str, Any]:
        """Session-seconds: per session, the accepted SUPPORT connector-meter interval union clipped to its span
        (restricted to `evidence_ids` when given); duplicates within a session count once."""
        by_session: dict[str, list[tuple[datetime, datetime]]] = {}
        for r in self._accepted(ctx):
            if (r["role"] == ROLE_OF["connector_meter_delta"] and r["use"] == "SUPPORT" and r["session_id"] in spans
                    and r["interval_start"] is not None and r["interval_end"] is not None
                    and (evidence_ids is None or r["evidence_id"] in evidence_ids)):
                a, b = spans[r["session_id"]]
                by_session.setdefault(r["session_id"], []).append((max(r["interval_start"], a),
                                                                   min(r["interval_end"], b)))
        known = sum((_measure(_union(by_session.get(k, ()))) for k in spans), timedelta(0))
        return _coverage(known, sum((b - a for a, b in spans.values()), timedelta(0)), "SESSION_SECONDS")

    def _claim_coverage(self, ctx: dict[str, Any], claim: str, by_role: dict[str, list[str]]) -> dict[str, Any]:
        """q5 R3: exact interval unions, else null coverage (never presence of a role alone)."""
        window = self._window(ctx)
        if claim == "SITE_POWER_CONTEXT":
            imports = self._site_import(ctx)[0]
            return _coverage(_measure(imports), window, "WINDOW_SECONDS") if imports else dict(NULL_COVERAGE)
        if claim == "POWER_CONSTRAINT":
            sets = [self._intervals(ctx, ROLE_OF[r]) for r in ("site_import", "requested_power", "allocated_limit")]
            if not all(sets):
                return dict(NULL_COVERAGE)
            return _coverage(_measure(_intersect(_intersect(sets[0], sets[1]), sets[2])), window, "WINDOW_SECONDS")
        if claim in ("SESSION_OUTCOME", "DELIVERED_ENERGY", "GROSS_TARIFF_SCENARIO"):
            spans = self._spans(ctx)
            if spans is None:
                return dict(NULL_COVERAGE)
            if claim == "SESSION_OUTCOME":
                total = sum((b - a for a, b in spans.values()), timedelta(0))
                return _coverage(total, total, "SESSION_SECONDS")
            if claim == "DELIVERED_ENERGY":
                return (self._session_coverage(ctx, spans, None) if "connector_meter_delta" in by_role
                        else dict(NULL_COVERAGE))
            row = ctx["money"]["current"]
            if row is None or row["amount"] is None:
                return dict(NULL_COVERAGE)
            revisions = {str(x).lower() for x in row["session_revision_ids"]}
            priced = {x["session_id"]: spans[x["session_id"]] for x in self._sessions(ctx)
                      if str(x["revision_id"]).lower() in revisions}
            return (self._session_coverage(ctx, priced, {str(e).lower() for e in row["evidence_ids"]})
                    if priced else dict(NULL_COVERAGE))
        return dict(NULL_COVERAGE)  # SERVICE_STATE, FAULT_ASSOCIATION: no continuous duration claim

    def _capabilities(self, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        if "capabilities" in ctx:
            return ctx["capabilities"]
        snap, accepted, sessions = ctx["snap"], self._accepted(ctx), self._sessions(ctx)
        rows: list[dict[str, Any]] = []
        if snap["selected"] is not None or accepted:
            by_role: dict[str, list[str]] = {}
            for r in accepted:
                if r["role"] in PUBLIC_ROLE:
                    by_role.setdefault(PUBLIC_ROLE[r["role"]], []).append(r["evidence_id"])
            if self._tariffs(ctx):
                by_role[TARIFF_ROLE] = []
            incomplete = any(x["state"] == "INCOMPLETE" for x in sessions)
            contradictory = any(x["state"] == "CONTRADICTORY" for x in sessions)
            known_at = plain(snap["known"])
            for claim, required, cited, limitation, ceiling in CLAIMS:
                missing = [x for x in required if x not in by_role]
                if claim in ("SESSION_OUTCOME", "DELIVERED_ENERGY") and incomplete:
                    missing.append("session_terminal")
                state = ("UNAVAILABLE" if len(missing) >= len(required) and "session_terminal" not in missing
                         else "LIMITED" if missing else "SUPPORTED")
                if state == "SUPPORTED" and ceiling == "LIMITED":
                    state = "LIMITED"
                coverage = self._claim_coverage(ctx, claim, by_role)
                if state == "SUPPORTED" and coverage["ratio"] != "1":  # Full needs exact complete coverage
                    state = "LIMITED"
                if contradictory and claim in ("SESSION_OUTCOME", "DELIVERED_ENERGY"):
                    state = "CONTRADICTORY"
                if coverage["ratio"] is None:
                    limitation = COVERAGE_UNKNOWN if limitation is None else f"{limitation} {COVERAGE_UNKNOWN}"
                ids = sorted({e for role in cited for e in by_role.get(role, ())})
                rows.append({"claim": claim, "state": state, "required_roles": list(required),
                             "observed_roles": [x for x in required if x in by_role], "missing_roles": missing,
                             "coverage": coverage, "accepted_evidence_ids": ids, "as_of": known_at,
                             "limitation": limitation})
        ctx["capabilities"] = rows
        return rows

    # --- the five routes ---------------------------------------------------------------------------------------

    def overview(self, t: UUID, s: UUID, code: str, lo, hi, known_at) -> dict[str, Any]:
        def work(c):
            ctx = self._ctx(c, t, s, code, lo, hi, known_at)
            snap, body = ctx["snap"], ctx["body"]
            status, denominator = self._reads.status_on(snap)
            sessions = self._sessions(ctx)
            as_of = self._as_of(ctx)
            no_assessment = status["limitation"] if snap["selected"] is None else None
            foundation = self._reads.foundation_on(c, snap)
            limit_kw, feed_as_of = self._import_limit(foundation)
            common, windows, declared = objective_windows(foundation, self._assets(c, ctx), snap["lo"], snap["hi"])
            # energy (W2-06 selected session heads; contradictory support is null, no report is null)
            if not sessions:
                energy = {"supported_kwh": None, "complete_kwh": None, "partial_kwh": None, "unknown_seconds": None,
                          "as_of": as_of, "limitation": no_assessment or "No supported session energy."}
            else:
                contradictory = any(x["state"] == "CONTRADICTORY" for x in sessions)
                complete = [_dec(x["supported_kwh"]) for x in sessions if x["energy_complete"] is True]
                partial = [_dec(x["supported_kwh"]) or Decimal("0.000") for x in sessions
                           if x["energy_complete"] is False]
                supported = [_dec(x["supported_kwh"]) for x in sessions if x["supported_kwh"] is not None]
                energy = {
                    "supported_kwh": None if contradictory or not supported else plain(sum(supported, Decimal(0))),
                    "complete_kwh": plain(sum(complete, Decimal(0))) if complete else None,
                    "partial_kwh": plain(sum(partial, Decimal("0.000"))),
                    "unknown_seconds": sum(x["unknown_meter_seconds"] or 0 for x in sessions),
                    "as_of": as_of, "limitation": "Accepted EV records conflict." if contradictory else None}
            imports, peak = self._site_import(ctx)
            import_s = bool(imports)
            site_power = {
                "observed_peak_kw": plain(peak), "configured_limit_kw": limit_kw,
                "coverage": self._claim_coverage(ctx, "SITE_POWER_CONTEXT", {}),
                "claim_limit": "CONTEXT_ONLY" if import_s else "UNKNOWN",
                "as_of": plain(snap["known"]) if import_s else as_of,
                "limitation": None if import_s else (no_assessment
                                                     or "No accepted Site import intervals cover this window.")}
            findings = self._reads.findings_on(c, snap)
            money = self._consequence(ctx)
            summary = ({"state": None, "reason": None, "quantity_kwh": None, "amount": None, "currency": None,
                        "overlap_group": None, "as_of": None, "limitation": NO_MONEY} if money is None else
                       {"state": money["state"], "reason": money["reason"], "quantity_kwh": money["quantity_kwh"],
                        "amount": money["amount"], "currency": money["currency"],
                        "overlap_group": money["overlap_group"], "as_of": money["recorded_at"],
                        "limitation": money["limitation"]})
            links = self._links(ctx, "")
            return {**body,
                    "status": status,
                    "objective": {"text": "Let depot vehicles charge when scheduled, within the configured Site "
                                          "import limit.",
                                  "configured_service_window": common,
                                  "configured_service_windows": windows, "service_schedule_declared": declared,
                                  "site_import_limit_kw": limit_kw,
                                  "as_of": feed_as_of,
                                  "limitation": "Configuration is not a measured service result."
                                  if limit_kw is not None else "Site limit not declared"},
                    "denominator": denominator, "energy": energy, "site_power": site_power,
                    "findings": {"count": len(findings),
                                 "items": [{**{k: x[k] for k in ("finding_id", "revision_id", "session_id", "title",
                                                                 "claim_level", "as_of", "links")},
                                            **{k: x["claim"].get(k) for k in ("start_evidence_id",
                                                                              "fault_evidence_id",
                                                                              "abort_evidence_id")}}
                                           for x in findings],
                                 "as_of": as_of, "limitation": no_assessment},
                    "needs_attention": self._attention(ctx, sessions, findings, money, links),
                    "consequence_summary": summary, "links": links}
        return self._reads.within(work)

    @staticmethod
    def _import_limit(foundation: dict[str, Any] | None) -> tuple[str | None, str | None]:
        if foundation is None:
            return None, None
        for component in foundation["content"].get("components") or ():
            for prop in component.get("properties") or ():
                if prop.get("property_key") == "ev-site-import-limit" and prop.get("value") is not None:
                    return format(Decimal(str(prop["value"])).normalize(), "f"), plain(foundation["valid_from"])
        return None, plain(foundation["valid_from"])

    def _attention(self, ctx, sessions, findings, money, links) -> list[dict[str, Any]]:
        out = []
        if ctx["snap"]["state"] == "PENDING_RECOMPUTE":
            out.append({"code": "PENDING", "text": MONEY_COPY[em.ERROR_PENDING], "link": None})
        faults = [x for x in findings if x.get("claim_level")]
        if any(x["state"] == "OBSERVED_ABORT" and x["fault_evidence_id"] for x in sessions):
            out.append({"code": "FAULT_ABORT", "text": "A session ended with a connector fault.",
                        "link": faults[0]["links"]["self"] if len(faults) == 1 else None})
        if any(x["state"] == "INCOMPLETE" for x in sessions):
            out.append({"code": "INCOMPLETE_SESSION", "text": "A session has no accepted end report.",
                        "link": links["analysis"]})
        if ctx["snap"].get("unassessable") is not None or any((x["unknown_meter_seconds"] or 0) > 0 for x in sessions):
            out.append({"code": "METER_OR_SOURCE_GAP", "text": "Meter or source evidence is missing or unverified.",
                        "link": links["analysis"]})
        if money is not None and money["reason"] == em.TARIFF_MISSING:
            out.append({"code": "TARIFF_MISSING", "text": MONEY_COPY[em.TARIFF_MISSING], "link": links["financials"]})
        return out

    def evidence(self, t: UUID, s: UUID, code: str, lo, hi, known_at) -> dict[str, Any]:
        def work(c):
            ctx = self._ctx(c, t, s, code, lo, hi, known_at)
            snap = ctx["snap"]
            capabilities = self._capabilities(ctx)
            accepted = self._accepted(ctx)
            foundation = self._reads.foundation_on(c, snap)
            assets = self._assets(c, ctx)
            components = [] if foundation is None else list(foundation["content"].get("components") or ())
            connectors = sorted((x for x in components if x.get("component_type") == "EV_CONNECTOR"),
                                key=lambda x: x.get("component_id") or "")
            meters = [x for x in components if x.get("component_type") == "METER"]
            slots = [(f"CONNECTOR_{i + 1}", x, f"Connector {i + 1}") for i, x in enumerate(connectors[:2])]
            while len(slots) < 2:
                slots.append((f"CONNECTOR_{len(slots) + 1}", None, f"Connector {len(slots) + 1}"))
            slots.append(("SITE_METER", meters[0] if len(meters) == 1 else None, "Site meter"))
            sources = []
            checked = plain(snap["known"])
            contacts = self._contacts(c, ctx)
            for slot, component, fallback in slots:
                asset = None if component is None else assets.get(component.get("component_id"))
                facts = [r for r in accepted if asset is not None and r["asset_id"] == asset]
                if slot == "SITE_METER":
                    facts = [r for r in facts if r["role"] == ROLE_OF["site_import"]]
                good = all(r["quality"] == "GOOD" for r in facts)
                sources.append({
                    "slot": slot, "asset_id": asset,
                    "display_name": (component or {}).get("display_name") or fallback,
                    "contact": contacts(asset, ROLE_OF["site_import"] if slot == "SITE_METER" else None),
                    "quality": {"state": "NO_FACT" if not facts else "GOOD" if good else "DEGRADED",
                                "accepted_count": len(facts)},
                    "roles": sorted({PUBLIC_ROLE[r["role"]] for r in facts if r["role"] in PUBLIC_ROLE}),
                    "as_of": checked,
                    "limitation": None if facts else "No accepted report for this role."})
            for x in sources:
                if x["limitation"] is None and x["contact"]["state"] == "UNKNOWN":
                    x["limitation"] = "No source-specific contact diagnostic."
            sources.append({"slot": "BILLING", "asset_id": None, "display_name": "Billing system",
                            "contact": contacts(None, None),
                            "quality": {"state": "NO_FACT", "accepted_count": 0}, "roles": [], "as_of": checked,
                            "limitation": "No accepted payment feed."})
            return {**ctx["body"],
                    "capabilities": [{k: v for k, v in x.items() if k != "observed_roles"} for x in capabilities],
                    "sources": sources, "next_evidence": self._next(ctx, capabilities), "links": self._links(ctx, "/evidence")}
        return self._reads.within(work)

    def _contacts(self, c, ctx) -> Callable[[str | None, str | None], dict[str, Any]]:
        """q5 R2: a slot's source contact from its own bound sources' keys in the latest eligible diagnostic per
        bound registered gateway at `checked_at=min(to,known_at)`; never charger health, never inferred from
        silence."""
        snap = ctx["snap"]
        checked = None if snap["known"] is None else min(snap["hi"], snap["known"])
        bindings = [] if checked is None else self._reads.source_bindings_on(c, snap)
        diagnostics = {} if not bindings else self._reads.source_contacts_on(
            c, ctx["t"], ctx["s"], sorted({b[2] for b in bindings}, key=str), checked)

        def one(source: str, gateways: set) -> dict[str, Any]:
            seen = [(g, diagnostics[g]) for g in sorted(gateways, key=str) if g in diagnostics]
            if not seen or any(d["cadence_seconds"] is None for _, d in seen):
                return {"state": "UNKNOWN", "last_seen_at": None, "age_seconds": None, "diagnostic_id": None,
                        "diagnostic_received_at": None, "cadence_seconds": None}
            best = None
            for _, d in seen:
                keyed = {}
                for key, value in (d["contacts"] or {}).items():
                    try:
                        keyed[str(UUID(str(key))).lower()] = value
                    except ValueError:
                        continue
                at = _instant(keyed.get(source))
                if at is not None and (best is None or at > best[0]):
                    best = (at, d)
            if best is None:
                d = max((d for _, d in seen), key=lambda d: (d["received_at"], str(d["diagnostic_id"])))
                return {"state": "NEVER", "last_seen_at": None, "age_seconds": None,
                        "diagnostic_id": plain(d["diagnostic_id"]), "diagnostic_received_at": plain(d["received_at"]),
                        "cadence_seconds": d["cadence_seconds"]}
            at, d = best
            age = max(0, int((checked - at).total_seconds()))
            return {"state": "RECENT" if age <= 2 * d["cadence_seconds"] else "OLD", "last_seen_at": plain(at),
                    "age_seconds": age, "diagnostic_id": plain(d["diagnostic_id"]),
                    "diagnostic_received_at": plain(d["received_at"]), "cadence_seconds": d["cadence_seconds"]}

        def contact(asset: str | None, role: str | None) -> dict[str, Any]:
            gateways_of: dict[str, set] = {}
            for b_asset, source, gateway, b_role in bindings:
                if asset is not None and b_asset == asset and (role is None or b_role == role):
                    gateways_of.setdefault(source, set()).add(gateway)
            # q6 R2: one per-source object per bound source (sorted by source_id); a multi-source slot states
            # MIXED iff the per-source states differ and never lets one source's diagnostic stand for all.
            by_source = [{"source_id": plain(src), **one(src, gws)}
                         for src, gws in sorted(gateways_of.items(), key=lambda x: str(x[0]))]
            null = {"last_seen_at": None, "age_seconds": None, "diagnostic_id": None,
                    "diagnostic_received_at": None, "cadence_seconds": None}
            if not by_source:
                out = {"state": "UNKNOWN", **null}
            elif len(by_source) == 1:
                out = {k: v for k, v in by_source[0].items() if k != "source_id"}
            else:
                states = {x["state"] for x in by_source}
                out = {"state": states.pop() if len(states) == 1 else "MIXED", **null}
            return {"state": out["state"], "checked_at": plain(checked),
                    **{k: v for k, v in out.items() if k != "state"}, "by_source": by_source}
        return contact

    def _assets(self, c, ctx) -> dict[str, str]:
        return self._reads.assets_on(c, ctx["snap"])

    @staticmethod
    def _next_candidates(missing: set, power_missing: set, unknown_meter: bool) -> list[str]:
        """Review r1 L3: every candidate in the ruled rank, deduplicated; the caller takes the first three."""
        codes = []
        if "session_terminal" in missing:
            codes.append("TERMINAL_GAP")
        if "connector_meter_delta" in missing or unknown_meter:
            codes.append("METER_GAP")
        if "connector_status" in missing:
            codes.append("STATUS_GAP")
        if "requested_power" in power_missing or "allocated_limit" in power_missing:
            codes.append("INDEPENDENT_POWER_GAP")
        if "site_import" in missing:
            codes.append("SITE_IMPORT_GAP")
        if TARIFF_ROLE in missing:
            codes.append("TARIFF_GAP")
        codes.append("BILLING_GAP")
        return list(dict.fromkeys(codes))

    def _next(self, ctx, capabilities) -> list[dict[str, Any]]:
        if not capabilities:
            return []
        missing = {role for x in capabilities for role in x["missing_roles"]}
        power = {role for x in capabilities if x["claim"] == "POWER_CONSTRAINT" for role in x["missing_roles"]}
        sessions = self._sessions(ctx)
        codes = self._next_candidates(missing, power, any((x["unknown_meter_seconds"] or 0) > 0 for x in sessions))
        links = self._links(ctx, "/evidence")
        return [{"code": code, "text": NEXT_EVIDENCE[code][0], "why": NEXT_EVIDENCE[code][1],
                 "link": links[NEXT_EVIDENCE[code][2]]} for code in codes[:3]]

    @staticmethod
    def _row_words(label: str, role: str | None, family: str, kind: str | None, value: Any,
                   unit: str | None) -> tuple[str, Any, str | None]:
        """Review r1 M3: the plain first cell and value of an accepted record. Events and connector states show the
        ruled words (no unit); numeric readings keep their exact value and unit; no raw code is shown."""
        source_label = f"{label} · {SOURCE_SUFFIX.get(role, UNKNOWN_SOURCE_SUFFIX)}"
        if family == "EVENT":
            return source_label, KIND_TEXT.get(kind), None
        if role == "ev_connector_state":
            return source_label, None if value is None else STATE_TEXT.get(str(value), UNRECOGNISED_STATE), None
        return source_label, value, unit

    def analysis(self, t: UUID, s: UUID, code: str, lo, hi, known_at, cursor: str | None, limit: int) -> dict:
        def work(c):
            ctx = self._ctx(c, t, s, code, lo, hi, known_at)
            snap, body = ctx["snap"], ctx["body"]
            accepted = self._accepted(ctx)
            names = self._names(c, ctx)
            items = []
            for r in accepted:
                kind = r["record_kind"]
                label = names.get(r["asset_id"]) or "EV source"
                source_label, value_display, unit = self._row_words(
                    label, r["role"], r["family"], kind, r["value"], r["unit"])
                items.append({
                    "evidence_id": r["evidence_id"],
                    "source_label": source_label,
                    "role": PUBLIC_ROLE.get(r["role"], r["role"]), "record_kind": kind,
                    "value_display": value_display, "unit": unit,
                    "source_time": plain(r["source_time"]), "sent_at": plain(r["sent_at"]),
                    "received_at": plain(r["received_at"]), "quality": r["quality"], "use": r["use"],
                    "reason": r["reason"], "session_id": r["session_id"],
                    "interval_start": plain(r["interval_start"]), "interval_end": plain(r["interval_end"]),
                    "note": SOURCE_UNVERIFIED_NOTE if r["use"] == "EXCLUDED" and r["reason"] == "SOURCE_UNVERIFIED"
                    else None,
                    "record_target_state": "UNAVAILABLE",
                    "links": {"self": None, "evidence": None, "analysis": None, "finding": None, "financials": None},
                    "_sort": r["_sort"]})
            page, nxt = self._reads.page_on(items, snap, body, "analysis", cursor, limit)
            # W3-01 r1 M2: a claim rule reports the selected assessment's class; a pending alias never stands in.
            selected_block = body.get("selected_source_provenance")
            source_class = None if selected_block is None else selected_block["classification"]
            rules = [{"claim": x["claim"], "required_roles": x["required_roles"],
                      "observed_roles": x["observed_roles"], "missing_roles": x["missing_roles"],
                      "coverage": x["coverage"], "result": x["state"],
                      "accepted_evidence_ids": x["accepted_evidence_ids"], "source_class": source_class,
                      "known_at": plain(snap["known"]), "limitation": x["limitation"]}
                     for x in self._capabilities(ctx)]
            excluded = [] if snap["selected"] is None else list(
                snap["selected"]["result"].get("excluded_records") or ())
            return {**body, "items": page, "total_count": len(items), "excluded_records": excluded,
                    "claim_rules": rules, "next_cursor": nxt, "links": self._links(ctx, "/evidence/analysis")}
        return self._reads.within(work)

    def _names(self, c, ctx) -> dict[str, str]:
        foundation = self._reads.foundation_on(c, ctx["snap"])
        assets = self._assets(c, ctx)
        out = {}
        for x in [] if foundation is None else foundation["content"].get("components") or ():
            asset = assets.get(x.get("component_id"))
            if asset is not None and isinstance(x.get("display_name"), str):
                out[asset] = x["display_name"]
        return out

    def financials(self, t: UUID, s: UUID, code: str, lo, hi, known_at, cursor: str | None, limit: int) -> dict:
        def work(c):
            ctx = self._ctx(c, t, s, code, lo, hi, known_at)
            # W3-01 Run 4 q4 ruling 1: each stored row (current or history) carries its own window-level DTO;
            # a synthetic guard (`revision_id: null`) has none.
            row_dto = lambda r: self._reads.money_row_provenance_on(c, ctx["snap"], r)  # noqa: E731
            history = [{**self._revision(h, HISTORY_LABEL), "label": HISTORY_LABEL, "source_provenance": row_dto(h),
                        "_sort": (h["recorded_at"], h["id"])} for h in ctx["money"]["history"]]
            page, nxt = self._reads.page_on(history, ctx["snap"], ctx["body"], "financials", cursor, limit)
            consequence = self._consequence(ctx)
            if consequence is not None and consequence["revision_id"] is not None:
                consequence["source_provenance"] = row_dto(ctx["money"]["current"])
            return {**ctx["body"], "consequence": consequence, "history": page,
                    "not_included": list(NOT_INCLUDED), "next_cursor": nxt, "links": self._links(ctx, "/financials")}
        return self._reads.within(work)

    def assumptions(self, t: UUID, s: UUID, code: str, lo, hi, known_at) -> dict[str, Any]:
        def work(c):
            ctx = self._ctx(c, t, s, code, lo, hi, known_at)
            snap = ctx["snap"]
            tariffs = self._tariffs(ctx)
            tariff = None
            if tariffs:
                x = tariffs[0]
                tariff = {"revision_id": plain(x["revision_id"]), "value": plain(x["value"]),
                          "currency": x["currency"], "unit": x["unit"], "basis": x["basis"],
                          "valid_from": plain(x["valid_from"]), "valid_to": plain(x["valid_to"]),
                          "recorded_at": plain(x["recorded_at"])}
            note = None
            if tariffs and snap["known"] is not None and tariffs[0]["recorded_at"] > snap["known"]:
                note = (f"Tariff published {_utc_words(tariffs[0]['recorded_at'])} UTC; applied as a scenario to the "
                        f"selected delivery window. Evidence through {_utc_words(snap['known'])} UTC.")
            money = self._consequence(ctx)
            return {**ctx["body"], "tariff": tariff, "tariff_revision_count": len(tariffs),
                    "publication_note": note,
                    "consequence_tariff": None if money is None or money["tariff_revision_id"] is None else
                    {"revision_id": money["tariff_revision_id"], "value": money["tariff_value"],
                     "currency": money["currency"], "recorded_at": money["tariff_recorded_at"]},
                    "billing_state": "NO_RECORD", "missing_keys": [] if tariffs else [em.TARIFF_KEY],
                    "links": self._links(ctx, "/financial-assumptions")}
        return self._reads.within(work)
