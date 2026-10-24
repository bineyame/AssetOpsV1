"""W5-04a V1b: the non-test EV work fixture producer library (readiness rulings 20, 29, 31; pre-flight 20-23).

`.agent/W5-04-build-spec.md` "V1 selection, clock and schema" (second paragraph) and "EV producer, UI and registry"
(first paragraph). Importable mode library in the shape of `tools/w502_cold_work_cases.py`; the CLI is
`tools/w504_ev_work_walkthrough.py`. Nothing here imports `backend/tests` (no `Chain`, no `decision_clock`).

What is here, all pure or driven through caller-supplied HTTP callables:
- Clocks: `R` is the private DB now, `D = floorUTCday(R) - 1 day`, and one delta moves the registered W2 EV
  scenario window `[2026-10-06T08:00Z, 09:00Z)` onto `[D+08:00, D+09:00)`; the same delta moves the scenario's
  `forcing[].time`, `observations[].time/release_at` and the Foundation `valid_from`/`valid_to`.
- The generated Site document: code `EV-W504-DEPOT-{suffix}`, display `Depot Charging Hub`, zone `Etc/UTC`, the
  registered EV Foundation components unchanged, no subtitle (readiness 20) and no money read (readiness 13).
- K0 (readiness 29): `read_k0` GETs `/ev/financials/scenarios?from&to` and `/ev/sessions?from&to` without
  `known_at`, then `/ev/findings?from&to&known_at=K0` for the same selected window, and `cross_check_k0` /
  `select_positive` refuse preparation (raise `ProducerRefused`) on a null K0, unequal bounds, unequal clocks or a
  Finding/session not in that window. A clock is never invented.
- The exact Action/intent/INC/WR/case-link payload literals and the mock-zero / submitted modes.
- `evidence_clock_for`: a browser record clock maps to the last returned EV watermark no later than it (ruling 21).

Not producible on merged code (see `.agent/W5-04a-questions.md` round 3, Q8-Q12): the registered EV parser pins
`site_code` and the window, `ev-fault` yields no Finding, and the registered gateway/central runner exists only in
test modules. `replay_shifted` therefore raises `ProducerBlocked` naming the blocking question instead of producing
a different fixture.
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCENARIO_DIR = ROOT / "config" / "scenarios"
SITE_PREFIX = "EV-W504-DEPOT-"
DISPLAY_NAME = "Depot Charging Hub"
#: Readiness/pre-flight 22: the short name. The Site document and Site read have no short-name field (Q12), so the
#: producer records it in the manifest only.
SHORT_NAME = "Depot"
TIMEZONE = "Etc/UTC"
SITE_TYPE = "EV_CHARGING"
#: Pre-flight 20 / readiness 31: the positive replay and the isolated unknown vector (see Q8 for `ev-fault`).
POSITIVE_SCENARIO = "ev-fault"
UNKNOWN_SCENARIO = "ev-missing-meter"
BASE_WINDOW_START = datetime(2026, 10, 6, 8, 0, tzinfo=timezone.utc)
BASE_WINDOW_END = datetime(2026, 10, 6, 9, 0, tzinfo=timezone.utc)
WINDOW_OFFSET = timedelta(hours=8)
WINDOW_LENGTH = timedelta(hours=1)
#: The DB-backed modes `prepare` emits (positive and mock-zero share one positive replay; submitted is `attest`).
MODES = ("positive", "mock-zero", "submitted")
#: Isolated selector-state vectors: captured only if the merged selector returns that state.
ISOLATED_STATES = {"pending": "PENDING_RECOMPUTE", "stale": "STALE_SOURCE", "unknown": "UNKNOWN"}
_SUFFIX = re.compile(r"[A-Z0-9]{1,12}")
_FMT = "%Y-%m-%dT%H:%M:%SZ"

#: "EV producer, UI and registry": exact literals.
ACTION = {"title": "Investigate connector 2", "owner_label": "Charging operations", "due_at": None}
INCIDENT = {"title": "Charging session fault",
            "narrative": "Connector fault ended a charging session; outcome remains unverified"}
WORK_REQUEST = {"title": "Connector diagnostic inspection",
                "activity": "Inspect connector and witness a charging session",
                "outcome_note": "Inspection recorded; recurrence and availability remain unverified"}
#: Q11: the spec gives the WR case no narrative, but W4 requires one (`work/service.py` CASE_CREATE_KEYS,
#: 1..4000 chars). Provisional value pending a ruling: the WR activity literal, flagged in the manifest.
WR_NARRATIVE_PENDING_RULING = WORK_REQUEST["activity"]
SERVICE_ACTOR = {"kind": "SERVICE", "id": "service:w401-fixture",
                 "attestation": "service=w401-fixture;job=w504-ev-work;rule=w504/1"}


class ProducerRefused(RuntimeError):
    """Fixture preparation refused: a returned public clock, window or selection disagreed (never invent one)."""


class ProducerBlocked(ProducerRefused):
    """The ruled input cannot be produced on merged code; the message names the open question."""


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


def day_d(db_now: datetime) -> datetime:
    """`D = floorUTCday(R) - 1 day`."""
    if db_now.tzinfo is None:
        raise ProducerRefused("R must be timezone-aware")
    r = db_now.astimezone(timezone.utc)
    return r.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)


def target_delta(db_now: datetime) -> timedelta:
    """The one delta that moves the registered window start onto `D + 08:00`."""
    return (day_d(db_now) + WINDOW_OFFSET) - BASE_WINDOW_START


def shifted_window(db_now: datetime) -> tuple[datetime, datetime]:
    """`[D+08:00, D+09:00)`."""
    lo = day_d(db_now) + WINDOW_OFFSET
    return lo, lo + WINDOW_LENGTH


def evidence_clock_for(record_clock: datetime, watermarks: Iterable[datetime]) -> datetime:
    """Ruling 21: the last returned EV watermark no later than a browser record clock (never the record clock)."""
    earlier = [w for w in watermarks if w <= record_clock]
    if not earlier:
        raise ProducerRefused(f"no returned EV watermark at or before {iso(record_clock)}")
    return max(earlier)


def site_code(suffix: str) -> str:
    if not isinstance(suffix, str) or not _SUFFIX.fullmatch(suffix):
        raise ValueError("the run suffix must be 1-12 upper-case letters/digits")
    return SITE_PREFIX + suffix


# ---- generated inputs ---------------------------------------------------------------------------------------


def _move(value: str | None, delta: timedelta) -> str | None:
    return None if value is None else text_of(instant(value) + delta)


def registered_scenario(scenario_id: str) -> dict[str, Any]:
    """The registered W2 EV scenario document (`config/scenarios/<id>.yaml`), read only."""
    path = SCENARIO_DIR / f"{scenario_id}.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or document.get("scenario_id") != scenario_id:
        raise ProducerRefused(f"{path} is not the registered {scenario_id} scenario")
    return document


def shifted_scenario_document(document: Mapping[str, Any], delta: timedelta) -> dict[str, Any]:
    """Every absolute instant of an `ev-scenario/1` document moved by `delta`; nothing else changes."""
    out = copy.deepcopy(dict(document))
    out["window"]["start"] = _move(out["window"]["start"], delta)
    out["window"]["end"] = _move(out["window"]["end"], delta)
    for row in out.get("forcing") or []:
        row["time"] = _move(row["time"], delta)
    for row in out.get("observations") or []:
        row["time"] = _move(row["time"], delta)
        if row.get("release_at") is not None:
            row["release_at"] = _move(row["release_at"], delta)
    return out


def registered_site_document() -> dict[str, Any]:
    """The registered EV Foundation document the product installer reads (`sites/ev_lab.FIXTURE_PATH`)."""
    from assetops_backend.sites.ev_lab import FIXTURE_PATH

    return yaml.safe_load(Path(FIXTURE_PATH).read_text(encoding="utf-8"))


def shifted_site_document(document: Mapping[str, Any], delta: timedelta, suffix: str) -> dict[str, Any]:
    """Readiness 20 / pre-flight 22: Site code/name/zone as ruled, Foundation effective interval moved by `delta`,
    components unchanged (their IDs stay the registered ones; stored UUIDs are returned on import). No subtitle."""
    out = copy.deepcopy(dict(document))
    if "subtitle" in out:
        raise ProducerRefused("the registered EV Site document carries a subtitle; the Site read has none")
    out["site_id"] = site_code(suffix)
    out["display_name"] = DISPLAY_NAME
    out["timezone"] = TIMEZONE
    foundation = out["foundation"]
    foundation["valid_from"] = _move(foundation["valid_from"], delta)
    if foundation.get("valid_to") is not None:
        foundation["valid_to"] = _move(foundation["valid_to"], delta)
    return out


def connector_components(site_document: Mapping[str, Any]) -> list[str]:
    """The Foundation connector component IDs (the WR/INC asset is the returned stored ID for one of them)."""
    return sorted(c["component_id"] for c in site_document["foundation"]["components"]
                  if c.get("component_type") == "EV_CONNECTOR")


def parse_shifted(document: Mapping[str, Any]):
    """The shifted document through the unchanged registered parser; its pins refuse it (Q9)."""
    from assetops_backend.scenarios.ev_parsing import parse_ev_scenario_document
    from assetops_backend.scenarios.ports import ScenarioConfigurationInvalid

    try:
        return parse_ev_scenario_document(copy.deepcopy(dict(document)))
    except ScenarioConfigurationInvalid as refused:
        raise ProducerBlocked(
            f"Q9: the registered EV scenario parser refuses the shifted document ({refused}); it pins site_code "
            "EV-LAB-001 and the 2026-10-06T08:00Z-09:00Z window, and no product change is authorized") from refused


def replay_shifted(scenario_id: str, db_now: datetime, suffix: str):
    """The private shifted replay of `scenario_id` for Site `EV-W504-DEPOT-{suffix}`.

    Blocked on merged code: the registered parser refuses the shifted document (Q9); were it admitted, the only
    registered gateway/central runner is test code (Q10), and `ev-fault` has no fault-aborted session (Q8)."""
    site_code(suffix)
    document = shifted_scenario_document(registered_scenario(scenario_id), target_delta(db_now))
    parse_shifted(document)
    raise ProducerBlocked("Q10: no non-test gateway/central runner for the registered EV publication path")


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
    status, findings = get(base + "/findings", {**bounds, "known_at": str(answers["scenarios"]["window"]["committed_watermark"])})
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


def action_body(selected: SelectedEv, raised_at: datetime, key: str, actor: Mapping[str, Any] = SERVICE_ACTOR
                ) -> dict[str, Any]:
    if raised_at <= selected.k0:
        raise ProducerRefused("the Action must be raised after K0 (it follows its evidence)")
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
            "narrative": WR_NARRATIVE_PENDING_RULING, "cited_accepted_evidence_ids": [], "actor": dict(actor),
            "idempotency_key": key}


def record_body(occurred_at: datetime, key: str, actor: Mapping[str, Any] = SERVICE_ACTOR) -> dict[str, Any]:
    return {"activity": WORK_REQUEST["activity"], "outcome_note": WORK_REQUEST["outcome_note"],
            "occurred_at": iso(occurred_at), "actor": dict(actor), "idempotency_key": key}


def case_link_body(case: Mapping[str, Any], event_id: str, key: str, actor: Mapping[str, Any] = SERVICE_ACTOR
                   ) -> dict[str, Any]:
    return {"case_id": case["id"], "case_revision_id": case["revision"]["id"], "case_event_id": event_id,
            "actor": dict(actor), "idempotency_key": key}


def submitted_case_times(lo: datetime) -> dict[str, datetime]:
    """W4 list-window semantics: both cases occur inside the generated `[D+08:00, D+09:00)` period."""
    return {"incident": lo + timedelta(minutes=20), "request": lo + timedelta(minutes=30),
            "record": lo + timedelta(minutes=40)}


def zero_reads_complete(incidents: Mapping[str, Any], maintenance: Mapping[str, Any]) -> bool:
    """Mock-zero: both W4 Site case reads return no rows (the complete-zero check the caller asserts)."""
    return not (incidents.get("items") or incidents.get("rows")) and not (
        maintenance.get("items") or maintenance.get("rows"))
