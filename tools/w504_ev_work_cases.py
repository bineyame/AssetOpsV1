"""W5-04a V1b: the non-test EV work fixture producer library (readiness rulings 20, 21, 29, 31, 34-38).

`.agent/W5-04-build-spec.md` "V1 selection, clock and schema" and "EV producer, UI and registry"; readiness rulings
34-38 supersede the earlier shifted-Site design (no generated Site, no shifted documents). Importable mode library in
the shape of `tools/w502_cold_work_cases.py`; the CLI is `tools/w504_ev_work_walkthrough.py`, whose walkthrough
CHILD alone imports the existing `backend/tests`/`host/tests` registered-replay helpers (ruling 36). Nothing here
imports a test module (AST-guarded), and `Chain.decision_clock()` is never a K0.

What is here, all pure or driven through caller-supplied HTTP callables:
- Two honest windows (ruling 35): the evidence window `E=[2026-10-06T08:00Z, 09:00Z)` of the registered, unmodified
  `ev-interrupted` replay at `EV-LAB-001` (evidence basis and K0 reads only), and the current Work window
  `W=[floorUTCday(R), +1 day)` (or a bounded explicit UTC window containing K1, the Incident `occurred_at` and the
  Maintenance `created_at`) for the three Work tabs and the Action detail URL.
- K0 (readiness 29/35): `read_k0` GETs `/ev/financials/scenarios?from&to` and `/ev/sessions?from&to` without
  `known_at`, then `/ev/findings?from&to&known_at=K0` for the same window; `cross_check_k0` / `select_positive`
  refuse preparation (raise `ProducerRefused`) on a null K0, unequal bounds, unequal clocks or a Finding/session not
  in that window. A clock is never invented.
- `clock_order`: `K0 < K1 <= K2 <= K3 <= K4` over returned `recorded_at` values, refused otherwise.
- The exact Action/intent/INC/WR/record/case-link payload literals (WR narrative per ruling 37).
- `evidence_clock_for`: a browser record clock maps to the last returned EV watermark no later than it (ruling 21).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterable, Mapping

#: Ruling 35/38: the registered EV Site (its stored display name and `Etc/UTC` zone are read back, never written).
SITE_CODE = "EV-LAB-001"
#: Ruling 38: the short name is a private manifest label only (the Site document/read has no short-name field).
SHORT_NAME = "Depot"
TIMEZONE = "Etc/UTC"
SITE_TYPE = "EV_CHARGING"
#: Ruling 34: the registered positive replay and the isolated unknown vector.
POSITIVE_SCENARIO = "ev-interrupted"
UNKNOWN_SCENARIO = "ev-missing-meter"
#: Ruling 35: the evidence window E of the registered replay (never shifted).
E_START = datetime(2026, 10, 6, 8, 0, tzinfo=timezone.utc)
E_END = datetime(2026, 10, 6, 9, 0, tzinfo=timezone.utc)
#: W4 limits (ruling 35): list windows of at most 31 days; occurrences at most 30 days back and 5 minutes ahead.
WORK_LIST_MAX = timedelta(days=31)
BACKDATE_LIMIT = timedelta(days=30)
FUTURE_SLACK = timedelta(minutes=5)
#: The DB-backed modes `prepare` emits (positive and mock-zero share one positive replay; submitted is `attest`).
MODES = ("positive", "mock-zero", "submitted")
#: Isolated selector-state vectors: captured only if the merged selector returns that state.
ISOLATED_STATES = {"pending": "PENDING_RECOMPUTE", "stale": "STALE_SOURCE", "unknown": "UNKNOWN"}
_FMT = "%Y-%m-%dT%H:%M:%SZ"

#: "EV producer, UI and registry": exact literals.
ACTION = {"title": "Investigate connector 2", "owner_label": "Charging operations", "due_at": None}
INCIDENT = {"title": "Charging session fault",
            "narrative": "Connector fault ended a charging session; outcome remains unverified"}
#: Ruling 37: the WR `narrative` is exactly the attested activity text.
WORK_REQUEST = {"title": "Connector diagnostic inspection",
                "narrative": "Inspect connector and witness a charging session",
                "activity": "Inspect connector and witness a charging session",
                "outcome_note": "Inspection recorded; recurrence and availability remain unverified"}
SERVICE_ACTOR = {"kind": "SERVICE", "id": "service:w401-fixture",
                 "attestation": "service=w401-fixture;job=w504-ev-work;rule=w504/1"}


class ProducerRefused(RuntimeError):
    """Fixture preparation refused: a returned public clock, window or selection disagreed (never invent one)."""


# ---- clocks -------------------------------------------------------------------------------------------------


def instant(value: str) -> datetime:
    """A UTC instant from ISO text (`Z` or offset); naive text is refused."""
    if not isinstance(value, str):
        raise ProducerRefused(f"expected an ISO instant, got {value!r}")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ProducerRefused(f"instant {value!r} has no UTC offset")
    return parsed.astimezone(timezone.utc)


def text_of(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime(_FMT)


def iso(value: datetime) -> str:
    """Microsecond-preserving UTC text for command bodies."""
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _aware(value: datetime, what: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ProducerRefused(f"{what} must be a timezone-aware instant")
    return value.astimezone(timezone.utc)


def floor_day(value: datetime) -> datetime:
    return _aware(value, "the instant").replace(hour=0, minute=0, second=0, microsecond=0)


def work_window(db_now: datetime) -> tuple[datetime, datetime]:
    """Ruling 35: `W = [floorUTCday(R), floorUTCday(R) + 1 day)`."""
    lo = floor_day(db_now)
    return lo, lo + timedelta(days=1)


def bounded_work_window(db_now: datetime, contained: Mapping[str, datetime]) -> dict[str, Any]:
    """Ruling 35: W from `R` if it contains every named instant (K1, Incident `occurred_at`, Maintenance
    `created_at`); otherwise the explicit UTC day-bounded window containing all of them, refused past W4's 31-day list
    limit or with an instant outside the 30-day backdate / 5-minute future bound around `R`."""
    if not contained:
        raise ProducerRefused("the Work window needs at least one returned instant")
    now = _aware(db_now, "R")
    values = {name: _aware(at, name) for name, at in contained.items()}
    for name, at in values.items():
        if at < now - BACKDATE_LIMIT or at > now + FUTURE_SLACK:
            raise ProducerRefused(f"{name} {iso(at)} is outside W4's occurrence bound around R {iso(now)}")
    lo, hi = work_window(now)
    recomputed = not all(lo <= at < hi for at in values.values())
    if recomputed:
        lo = floor_day(min(values.values()))
        hi = floor_day(max(values.values())) + timedelta(days=1)
        if hi - lo > WORK_LIST_MAX:
            raise ProducerRefused(f"no W4 list window of at most 31 days contains {sorted(values)}")
    return {"from": lo, "to": hi, "recomputed": recomputed, "contains": {k: iso(v) for k, v in values.items()}}


def clock_order(k0: datetime, k1: datetime, k2: datetime | None = None, k3: Iterable[datetime] = (),
                k4: Iterable[datetime] = ()) -> list[str]:
    """Ruling 35: `K0 < K1 <= K2 <= K3 <= K4` over returned clocks (every K3 at or before every K4). Returns the
    actual order for the manifest; refuses preparation otherwise."""
    k3, k4 = list(k3), list(k4)
    if (k3 or k4) and k2 is None:
        raise ProducerRefused("a submitted-case capture needs K2")
    if k4 and not k3:
        raise ProducerRefused("K4 (case links) needs K3 (the linked cases)")
    if not k0 < k1:
        raise ProducerRefused(f"K0 {iso(k0)} is not before K1 {iso(k1)}")
    stages = [("K1", [k1])] + ([("K2", [k2])] if k2 is not None else []) + ([("K3", k3)] if k3 else []) \
        + ([("K4", k4)] if k4 else [])
    for (a, before), (b, after) in zip(stages, stages[1:]):
        if max(before) > min(after):
            raise ProducerRefused(f"{a} {iso(max(before))} is after {b} {iso(min(after))}")
    return [f"K0={iso(k0)}"] + [f"{name}={iso(at)}" for name, values in stages for at in sorted(values)]


def evidence_clock_for(record_clock: datetime, watermarks: Iterable[datetime]) -> datetime:
    """Ruling 21: the last returned EV watermark no later than a browser record clock (never the record clock)."""
    earlier = [w for w in watermarks if w <= record_clock]
    if not earlier:
        raise ProducerRefused(f"no returned EV watermark at or before {iso(record_clock)}")
    return max(earlier)


# ---- K0 and the selected window (readiness 29) --------------------------------------------------------------


@dataclass(frozen=True)
class SelectedEv:
    k0: datetime
    lo: datetime
    hi: datetime
    scenarios_window: dict[str, Any]
    sessions_window: dict[str, Any]
    findings_window: dict[str, Any]
    finding_id: str
    finding_revision_id: str
    session_id: str
    session_revision_id: str
    connector_asset_id: str | None
    accepted_evidence_ids: list[str] = field(default_factory=list)

    def manifest(self) -> dict[str, Any]:
        return {"k0": iso(self.k0), "from": iso(self.lo), "to": iso(self.hi),
                "scenarios_window": self.scenarios_window, "sessions_window": self.sessions_window,
                "findings_window": self.findings_window, "finding_id": self.finding_id,
                "finding_revision_id": self.finding_revision_id, "session_id": self.session_id,
                "session_revision_id": self.session_revision_id, "connector_asset_id": self.connector_asset_id,
                "accepted_evidence_ids": list(self.accepted_evidence_ids)}


def _window(body: Any, name: str) -> dict[str, Any]:
    window = body.get("window") if isinstance(body, Mapping) else None
    if not isinstance(window, Mapping):
        raise ProducerRefused(f"the {name} response has no window")
    return dict(window)


def _same_instant(value: Any, wanted: datetime, what: str) -> None:
    if value is None or instant(value) != wanted:
        raise ProducerRefused(f"{what} {value!r} is not {iso(wanted)}")


def cross_check_k0(scenarios_body: Any, sessions_body: Any, lo: datetime, hi: datetime) -> datetime:
    """Readiness 29: K0 = scenarios `window.committed_watermark` (non-null); both windows have the requested bounds;
    `sessions.window.known_at == scenarios.window.known_at == K0` after UTC normalization. Otherwise refuse."""
    scenarios, sessions = _window(scenarios_body, "scenarios"), _window(sessions_body, "sessions")
    raw = scenarios.get("committed_watermark")
    if raw is None:
        raise ProducerRefused("the EV scenarios window has no committed_watermark (K0 is null)")
    k0 = instant(raw)
    for name, window in (("scenarios", scenarios), ("sessions", sessions)):
        _same_instant(window.get("from"), lo, f"{name} window.from")
        _same_instant(window.get("to"), hi, f"{name} window.to")
        _same_instant(window.get("known_at"), k0, f"{name} window.known_at")
    return k0


def _evidence_ids(block: Any) -> set[str]:
    if not isinstance(block, Mapping):
        return set()
    return {str(x).lower() for x in block.get("evidence_ids") or ()}


def select_positive(sessions_body: Mapping[str, Any], findings_body: Mapping[str, Any], k0: datetime,
                    lo: datetime, hi: datetime) -> dict[str, Any]:
    """The one SUPPORTED EV Finding whose session is a fault-ended (OBSERVED_ABORT with fault evidence) selected
    session of this same window at K0; declared evidence = the Finding's cited IDs that the selected head also
    cites (the server re-validates readiness-30 membership). Anything else refuses."""
    findings_window = _window(findings_body, "findings")
    _same_instant(findings_window.get("from"), lo, "findings window.from")
    _same_instant(findings_window.get("to"), hi, "findings window.to")
    _same_instant(findings_window.get("known_at"), k0, "findings window.known_at")
    sessions = {str(s["session_id"]).lower(): s for s in sessions_body.get("items") or ()}
    ended = {sid: s for sid, s in sessions.items()
             if s.get("state") == "OBSERVED_ABORT" and s.get("fault_evidence_id") is not None}
    supported = [f for f in findings_body.get("items") or ()
                 if f.get("lifecycle") == "SUPPORTED" and str(f.get("session_id") or "").lower() in ended]
    if len(supported) != 1:
        raise ProducerRefused(f"expected one SUPPORTED EV Finding on a fault-ended selected session, found "
                              f"{len(supported)} (sessions {sorted(ended)})")
    finding = supported[0]
    session = ended[str(finding["session_id"]).lower()]
    head = _evidence_ids(sessions_body.get("selected_source_provenance"))
    cited = _evidence_ids(finding.get("source_provenance"))
    declared = sorted(cited & head)
    if not declared:
        raise ProducerRefused("the selected Finding cites no evidence the selected head also cites")
    return {"finding": finding, "session": session, "accepted_evidence_ids": declared,
            "findings_window": findings_window}


Get = Callable[[str, Mapping[str, str]], tuple[int, Any]]


def read_k0(get: Get, code: str, lo: datetime, hi: datetime) -> SelectedEv:
    """The three public GETs and both checks; `get(path, params) -> (status, json)`."""
    base = f"/api/sites/{code}/ev"
    bounds = {"from": text_of(lo), "to": text_of(hi)}
    answers = {}
    for name, path, params in (("scenarios", "/financials/scenarios", bounds), ("sessions", "/sessions", bounds)):
        status, body = get(base + path, params)
        if status != 200:
            raise ProducerRefused(f"GET {base + path} answered {status}: {body!r}"[:400])
        answers[name] = body
    k0 = cross_check_k0(answers["scenarios"], answers["sessions"], lo, hi)
    # The same selected cutoff, as the server returned it (no reformatting of the clock).
    returned_k0 = str(answers["scenarios"]["window"]["committed_watermark"])
    status, findings = get(base + "/findings", {**bounds, "known_at": returned_k0})
    if status != 200:
        raise ProducerRefused(f"GET {base}/findings answered {status}: {findings!r}"[:400])
    chosen = select_positive(answers["sessions"], findings, k0, lo, hi)
    finding, session = chosen["finding"], chosen["session"]
    return SelectedEv(
        k0=k0, lo=lo, hi=hi, scenarios_window=_window(answers["scenarios"], "scenarios"),
        sessions_window=_window(answers["sessions"], "sessions"), findings_window=chosen["findings_window"],
        finding_id=str(finding["finding_id"]), finding_revision_id=str(finding["revision_id"]),
        session_id=str(session["session_id"]), session_revision_id=str(session["revision_id"]),
        connector_asset_id=None if session.get("connector_asset_id") is None else str(session["connector_asset_id"]),
        accepted_evidence_ids=chosen["accepted_evidence_ids"])


# ---- command bodies -----------------------------------------------------------------------------------------


def action_body(selected: SelectedEv, raised_at: datetime, key: str, actor: Mapping[str, Any] = SERVICE_ACTOR,
                db_now: datetime | None = None) -> dict[str, Any]:
    """Ruling 35: `raised_at` is current DB time (the domain service admits 30 days back to 5 minutes ahead of DB
    now) and after K0; never the 2026-10-06 evidence clock."""
    if raised_at <= selected.k0:
        raise ProducerRefused("the Action must be raised after K0 (it follows its evidence)")
    if db_now is not None and not (db_now - BACKDATE_LIMIT <= raised_at <= db_now + FUTURE_SLACK):
        raise ProducerRefused(f"raised_at {iso(raised_at)} is outside the DB-time window around {iso(db_now)}")
    return {"domain": SITE_TYPE, "origin_finding_id": selected.finding_id,
            "origin_finding_revision_id": selected.finding_revision_id, **ACTION, "raised_at": iso(raised_at),
            "actor": dict(actor), "idempotency_key": key}


def ev_criteria() -> list[dict[str, Any]]:
    from assetops_backend.work.domain_action import EV_CRITERIA

    return [{"key": k, "label": label, "required_evidence": req} for k, label, req in EV_CRITERIA]


def intent_body(selected: SelectedEv, finding_revision_id: str, declared_at: datetime, key: str,
                actor: Mapping[str, Any] = SERVICE_ACTOR, session_ids: Iterable[str] | None = None
                ) -> dict[str, Any]:
    """Positive intent: the returned Finding revision, sorted distinct selected session roots, sorted accepted
    evidence IDs, no case/record."""
    sessions = sorted({s.lower() for s in (session_ids or [selected.session_id])})
    if selected.session_id.lower() not in sessions:
        raise ProducerRefused("the intent must include the Finding's own session")
    return {"supersedes_id": None, "declared_at": iso(declared_at), "criteria": ev_criteria(),
            "basis": {"finding_revision_id": finding_revision_id, "work_case_id": None, "work_record_id": None,
                      "accepted_evidence_ids": sorted(selected.accepted_evidence_ids), "session_ids": sessions},
            "actor": dict(actor), "idempotency_key": key}


def incident_body(asset_id: str, occurred_at: datetime, key: str, actor: Mapping[str, Any] = SERVICE_ACTOR
                  ) -> dict[str, Any]:
    return {"kind": "INCIDENT", "occurred_at": iso(occurred_at), "asset_id": asset_id, "finding_links": [],
            "action_links": [], **INCIDENT, "cited_accepted_evidence_ids": [], "actor": dict(actor),
            "idempotency_key": key}


def request_body(asset_id: str, occurred_at: datetime, key: str, actor: Mapping[str, Any] = SERVICE_ACTOR
                 ) -> dict[str, Any]:
    return {"kind": "MAINTENANCE_REQUEST", "occurred_at": iso(occurred_at), "asset_id": asset_id,
            "finding_links": [], "action_links": [], "title": WORK_REQUEST["title"],
            "narrative": WORK_REQUEST["narrative"], "cited_accepted_evidence_ids": [], "actor": dict(actor),
            "idempotency_key": key}


def record_body(occurred_at: datetime, key: str, actor: Mapping[str, Any] = SERVICE_ACTOR) -> dict[str, Any]:
    return {"activity": WORK_REQUEST["activity"], "outcome_note": WORK_REQUEST["outcome_note"],
            "occurred_at": iso(occurred_at), "actor": dict(actor), "idempotency_key": key}


def case_link_body(case: Mapping[str, Any], event_id: str, key: str, actor: Mapping[str, Any] = SERVICE_ACTOR
                   ) -> dict[str, Any]:
    return {"case_id": case["id"], "case_revision_id": case["revision"]["id"], "case_event_id": event_id,
            "actor": dict(actor), "idempotency_key": key}


def submitted_case_times(db_now: datetime) -> dict[str, datetime]:
    """Ruling 35: INC/WR/record occurrences from current DB time (inside W4's 30-day backdate bound), never
    2026-10-06; the record follows its request."""
    now = _aware(db_now, "R")
    return {"incident": now - timedelta(minutes=3), "request": now - timedelta(minutes=2),
            "record": now - timedelta(minutes=1)}


def listed_ids(body: Mapping[str, Any], key: str) -> set[str]:
    """The IDs a W4/domain-work list response returns under `rows` (or `items`)."""
    rows = body.get("rows") or body.get("items") or ()
    return {str(r.get(key)).lower() for r in rows if isinstance(r, Mapping) and r.get(key) is not None}


def zero_reads_complete(incidents: Mapping[str, Any], maintenance: Mapping[str, Any]) -> bool:
    """Mock-zero: both W4 Site case reads return no rows (the complete-zero check the caller asserts)."""
    return not (incidents.get("items") or incidents.get("rows")) and not (
        maintenance.get("items") or maintenance.get("rows"))
