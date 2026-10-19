"""Pure EV charging-session correlation: `ev-session/1` (W2-06 commit 2).

Authority: `.agent/W2-06-build-spec.md` "Pre-build closure" (Canonical input, Total ordering and state table,
Coverage and JSON), "Run 1 rulings (q1)" R1-R12 and "Run 2 rulings (q2)" Q2-Q9, Q14 and Q15,
and "Run 3 rulings (q3)" P1-P5.

The rules read only accepted public records that the caller has already selected for one Site, one fixed
half-open window `[from_at, to_at)` and one knowledge cutoff `known_at` (records visible at the cutoff), together
with the effective configuration: one Foundation revision, one `ev-roles-1` binding-set revision, the published
mapping profile, the exact S4-05 source class and each bound connector's parent charger and ratings. A session is
materialized only from a qualifying accepted START inside the window; every linked record carries exactly one
use (SUPPORT, CONTEXT, EXCLUDED) and at most one reason chosen by the R4 precedence. Nothing here persists, reads
a clock, or consults private simulation state; the commit-3 writer persists what `assess` returns.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping, Sequence
from uuid import UUID

from assetops_backend.financials.fuel_cost import canonical_json, iso

SESSION_ANALYTIC = "ev-session/1"
MODEL_ID = "ev-session/1"
MODEL_VERSION = "1"
RULE_VERSION = "1"
DOMAIN = "ev_charging"
MECHANISM = "EV_INTERRUPTION"

STATES = ("COMPLETED", "OBSERVED_ABORT", "INCOMPLETE", "CONTRADICTORY")
USES = ("SUPPORT", "CONTEXT", "EXCLUDED")
#: R9: the fixed emission order of session reason codes. PENDING_RECOMPUTE is read currentness only.
REASON_ORDER = ("MISSING_START", "MISSING_TERMINAL", "CONFLICTING_TERMINAL", "CONFLICTING_START",
                "CONNECTOR_MISMATCH", "METER_GAP", "METER_OVERLAP", "METER_INVALID", "CLOCK_UNATTESTED",
                "SOURCE_UNVERIFIED", "PENDING_RECOMPUTE")

START = "EV_SESSION_START"
END = "EV_SESSION_END"
ABORT = "EV_SESSION_ABORT"
FAULT = "EV_CONNECTOR_FAULT"
CLEAR = "EV_CONNECTOR_CLEAR"
TERMINALS = (END, ABORT)
DELTA = "INTERVAL_DELTA"
MEAN = "INTERVAL_MEAN"
STATE_AT_INSTANT = "STATE_AT_INSTANT"
#: Same-instant semantic rank: START precedes context, FAULT precedes ABORT, END precedes ABORT (display only).
_KIND_RANK = {START: 0, FAULT: 1, END: 2, ABORT: 3, CLEAR: 4}
_CONTEXT_RANK = 5
_US_PER_HOUR = 3_600_000_000
_US_PER_SECOND = 1_000_000

FINDING_TITLE = "Observed EV charging interruption"
#: r8/r9 M1: the S4-05 whole-set classes on which `ev-session/1` may project (any other set state refuses).
ASSESSABLE_CLASSES = ("REGISTERED_SIMULATION", "AUTHORED_DEMONSTRATION")
#: r9 M1-a: the limitation of a MIXED/UNKNOWN accepted set (refused before `assess`; read-side only).
SOURCE_UNASSESSABLE = "EV source provenance is mixed or unverified; session outcomes cannot be assessed."
#: r9 M1-b: a coherent positive set whose every candidate START is excluded for its source/binding.
BINDING_UNVERIFIED = "EV source or binding is unverified; session outcomes cannot be assessed."


# --- inputs --------------------------------------------------------------------------------------------------


def _instant(value: Any) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def _uuid(value: Any) -> UUID | None:
    if value is None or isinstance(value, UUID):
        return value
    return UUID(str(value))


@dataclass(frozen=True)
class EvRecord:
    """One accepted public record as selected; fields match the `ev-w206-vectors/1` row keys (Q1). `asset_id` and
    `binding_revision_id` are the accepted row's bound asset and **member** binding ID (q3 P2; None when unbound);
    `value` is the accepted normalized decimal (or state) text. `clock_attested` (q3 P1) is true only when an
    effective clock attestation recorded by the knowledge cutoff covers this row's `source_id`, `sequence_epoch`
    and full measurement interval; this module only consumes the boolean."""

    report_key: str | None
    report_sha256: str | None
    batch_external_id: str | None
    ordinal: int | None
    accepted_evidence_id: UUID
    envelope_sha256: str
    source_time: datetime
    interval_start: datetime | None
    interval_end: datetime | None
    connector_id: str | None
    session_id: str | None
    family: str
    record_kind: str | None
    measurement: str | None
    quality: str
    value: str | None
    unit: str | None
    event_id: str | None
    outcome: str | None
    asset_id: UUID | None
    binding_revision_id: UUID | None
    source_id: str | None
    sequence_epoch: Any
    clock_attested: bool
    source_class: str | None
    #: q3 P2: the accepted row's `binding_set_revision_id` and channel identity, compared with its member binding.
    binding_set_revision_id: UUID | None = None
    role: str | None = None
    device_id: str | None = None
    signal_id: str | None = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "EvRecord":
        """Parse one vector/store row (ISO instants, UUID text) into a record."""
        return cls(
            report_key=row.get("report_key"), report_sha256=row.get("report_sha256"),
            batch_external_id=row.get("batch_external_id"), ordinal=row.get("ordinal"),
            accepted_evidence_id=_uuid(row["accepted_evidence_id"]), envelope_sha256=row["envelope_sha256"],
            source_time=_instant(row["source_time"]), interval_start=_instant(row.get("interval_start")),
            interval_end=_instant(row.get("interval_end")), connector_id=row.get("connector_id"),
            session_id=row.get("session_id"), family=row["family"], record_kind=row.get("record_kind"),
            measurement=row.get("measurement"), quality=row["quality"], value=row.get("value"),
            unit=row.get("unit"), event_id=row.get("event_id"), outcome=row.get("outcome"),
            asset_id=_uuid(row.get("asset_id")), binding_revision_id=_uuid(row.get("binding_revision_id")),
            source_id=row.get("source_id"), sequence_epoch=row.get("sequence_epoch"),
            clock_attested=bool(row["clock_attested"]), source_class=row.get("source_class"),
            binding_set_revision_id=_uuid(row.get("binding_set_revision_id")), role=row.get("role"),
            device_id=row.get("device_id"), signal_id=row.get("signal_id"),
        )

    @property
    def id(self) -> str:
        return str(self.accepted_evidence_id).lower()

    @property
    def kind(self) -> str | None:
        return self.record_kind if self.family == "EVENT" else None


@dataclass(frozen=True)
class EvWindow:
    """UTC half-open `[from_at, to_at)` and the knowledge cutoff."""

    from_at: datetime
    to_at: datetime
    known_at: datetime

    def __post_init__(self) -> None:
        if not self.from_at < self.to_at:
            raise ValueError("an EV window needs from_at < to_at")


@dataclass(frozen=True)
class EvConnector:
    """One bound EV_CONNECTOR: its single parent charger, public connector code and effective Foundation
    properties (`ev-connector-max-power` kW, `ev-meter-resolution`/`ev-meter-error-bound` kWh,
    `ev-clock-error-bound` s, cadences in minutes)."""

    asset_id: UUID
    charger_asset_id: UUID
    connector_id: str | None
    max_power_kw: Decimal
    meter_resolution_kwh: Decimal
    meter_error_bound_kwh: Decimal
    clock_error_bound_s: Decimal
    status_cadence_min: Decimal | None = None
    meter_cadence_min: Decimal | None = None
    #: q3 P4: `ev-charger-max-power` (kW) of the connector's actual parent charger.
    charger_max_power_kw: Decimal | None = None

    @property
    def tolerance(self) -> timedelta:
        return timedelta(microseconds=int(self.clock_error_bound_s * _US_PER_SECOND))

    @property
    def interval_error_kwh(self) -> Decimal:
        """R6: twice the per-boundary meter error bound."""
        return 2 * self.meter_error_bound_kwh


class EvConfigurationRefused(Exception):
    """The effective EV configuration cannot be selected exactly; no projection is computed (fail closed)."""


@dataclass(frozen=True)
class EvBindingMember:
    """q3 P2: one immutable member `signal_binding_revision` row of the selected `ev-roles-1` binding-set
    revision, as `ev_inputs` reads it on the writer's transaction."""

    binding_revision_id: UUID
    binding_set_revision_id: UUID
    role: str
    asset_id: UUID | None
    source_id: UUID
    device_id: str
    signal_id: str
    valid_from: datetime
    valid_to: datetime | None

    def valid_at(self, t: datetime) -> bool:
        return self.valid_from <= t and (self.valid_to is None or t < self.valid_to)


@dataclass(frozen=True)
class EvInputs:
    """One Site/window/cutoff selection: accepted records and the exact effective configuration."""

    tenant_id: UUID
    site_id: UUID
    window: EvWindow
    records: tuple[EvRecord, ...]
    connectors: tuple[EvConnector, ...]
    foundation_revision_id: UUID
    #: q3 P2: the selected binding-SET revision; each record's `binding_revision_id` names one of `binding_members`.
    binding_revision_id: UUID
    mapping_profile_id: str
    source_class: str
    binding_members: tuple[EvBindingMember, ...] = ()

    def member(self, binding_revision_id: UUID | None) -> EvBindingMember | None:
        """The effective member of the selected set with this ID (None when missing or foreign)."""
        found = [m for m in self.binding_members if m.binding_revision_id == binding_revision_id]
        if len(found) > 1:
            raise EvConfigurationRefused(f"binding member {binding_revision_id} is selected twice")
        if not found or found[0].binding_set_revision_id != self.binding_revision_id:
            return None
        return found[0]

    def configuration_row(self) -> list:
        """R8/Q14 outer configuration array of every basis/run digest."""
        return [str(self.foundation_revision_id).lower(), str(self.binding_revision_id).lower(),
                self.mapping_profile_id, MODEL_ID, RULE_VERSION, iso(self.window.from_at), iso(self.window.to_at),
                iso(self.window.known_at), self.source_class]


# --- outputs -------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class EvLink:
    evidence_id: UUID
    envelope_sha256: str
    use: str
    reason: str | None


@dataclass(frozen=True)
class EvInterval:
    evidence_id: UUID
    connector_asset_id: UUID
    start_at: datetime
    end_at: datetime
    kwh: Decimal
    error_bound_kwh: Decimal
    use: str
    reason: str | None


@dataclass(frozen=True)
class EvSession:
    external_session_id: str
    charger_asset_id: UUID
    connector_asset_id: UUID
    first_start_evidence_id: UUID
    anchor_time: datetime
    state: str
    start_at: datetime
    end_at: datetime | None
    start_bounds: tuple[datetime | None, datetime | None]
    end_bounds: tuple[datetime | None, datetime | None]
    supported_kwh: Decimal | None
    energy_complete: bool | None
    unknown_meter_seconds: int | None
    reason_codes: tuple[str, ...]
    fault_evidence_id: UUID | None
    finding_support: tuple[tuple[str, str], ...]
    links: tuple[EvLink, ...]
    intervals: tuple[EvInterval, ...]
    basis_sha256: str
    finding_key_sha256: str
    finding_support_sha256: str | None

    @property
    def qualified_fault_abort(self) -> bool:
        return self.state == "OBSERVED_ABORT" and self.fault_evidence_id is not None


@dataclass(frozen=True)
class EvAssessment:
    assessment_key: str
    sessions: tuple[EvSession, ...]
    orphan_terminal_ids: tuple[UUID, ...]
    denominator: dict
    status_state: str
    claim_level: str
    #: r9 M1-b: the stored status/denominator limitation (None for a computed result).
    limitation: str | None = None
    #: r9 M1-c: every accepted wrong-binding record of the input set, sorted by (source_time, evidence_id).
    excluded_records: tuple[dict, ...] = ()


# --- digests (Q14/Q15) ---------------------------------------------------------------------------------------


def _sha(document: Any) -> str:
    return hashlib.sha256(canonical_json(document).encode("utf-8")).hexdigest()


def assessment_key(window: EvWindow) -> str:
    return f"{SESSION_ANALYTIC}:{iso(window.from_at)}:{iso(window.to_at)}"


def evidence_rows(links: Iterable[EvLink]) -> list[list]:
    """Basis rows `[accepted_evidence_id, envelope_sha256, use, reason]`, deduplicated by ID, sorted by ID."""
    rows: dict[str, list] = {}
    for link in links:
        key = str(link.evidence_id).lower()
        row = [key, link.envelope_sha256, link.use, link.reason]
        if key in rows and rows[key] != row:
            raise ValueError(f"evidence {key} carries two different uses in one basis")
        rows[key] = row
    return [rows[k] for k in sorted(rows)]


def basis_sha256(links: Iterable[EvLink], inputs: EvInputs) -> str:
    """Canonical `[sorted evidence rows, configuration row]` SHA-256 (session basis: its linked rows only)."""
    return _sha([evidence_rows(links), inputs.configuration_row()])


def run_input_rows(inputs: EvInputs, assessment: "EvAssessment") -> list[list]:
    """q3 P3: one `[accepted_id, envelope_sha256, use, reason]` row per selected accepted record, sorted by ID.
    A record linked by the sessions with exactly one distinct use/reason keeps that pair; an unlinked record, or
    one linked with different pairs by two sessions, is the literal run-only `"CONTEXT", null` (never written into
    `ev_session_evidence`). One ID with two envelope digests is refused."""
    envelopes: dict[str, str] = {}
    for r in inputs.records:
        if envelopes.setdefault(r.id, r.envelope_sha256) != r.envelope_sha256:
            raise ValueError(f"evidence {r.id} carries two envelope digests")
    pairs: dict[str, set[tuple[str, str | None]]] = {}
    for session in assessment.sessions:
        for link in session.links:
            key = str(link.evidence_id).lower()
            if envelopes.get(key) != link.envelope_sha256:
                raise ValueError(f"evidence {key} carries two envelope digests")
            pairs.setdefault(key, set()).add((link.use, link.reason))
    rows = []
    for key in sorted(envelopes):
        found = pairs.get(key, set())
        use, reason = next(iter(found)) if len(found) == 1 else ("CONTEXT", None)
        rows.append([key, envelopes[key], use, reason])
    return rows


def run_input_sha256(inputs: EvInputs, assessment: "EvAssessment") -> str:
    """Q14 run `input_sha256` over the complete q3 P3 rows built from `inputs.records` and the session links."""
    return _sha([run_input_rows(inputs, assessment), inputs.configuration_row()])


#: q3 P4: the exact literal policy keys of one connector.
POLICY_KEYS = ("ev-charger-max-power", "ev-connector-max-power", "ev-meter-resolution", "ev-meter-error-bound",
               "ev-clock-error-bound", "ev-status-cadence", "ev-meter-cadence")


def policy_document(inputs: EvInputs) -> dict:
    """q3 P4: `{"connectors": {<lowercase connector asset UUID>: {seven literal keys}}}` from the selected
    configuration, every value exact decimal text `format(Decimal, "f")`; canonical key ordering supplies the
    order. All seven are required Foundation properties (`sites.ev_foundation` CHARGER_REQUIRED /
    CONNECTOR_REQUIRED), so a missing value refuses the configuration."""
    connectors: dict[str, dict] = {}
    for c in inputs.connectors:
        values = dict(zip(POLICY_KEYS, (c.charger_max_power_kw, c.max_power_kw, c.meter_resolution_kwh,
                                        c.meter_error_bound_kwh, c.clock_error_bound_s, c.status_cadence_min,
                                        c.meter_cadence_min)))
        missing = sorted(k for k, v in values.items() if v is None)
        if missing:
            raise EvConfigurationRefused(f"connector {c.asset_id} lacks required properties {missing}")
        key = str(c.asset_id).lower()
        if key in connectors:
            raise EvConfigurationRefused(f"connector {c.asset_id} is configured twice")
        connectors[key] = {k: format(Decimal(v), "f") for k, v in values.items()}
    return {"connectors": connectors}


def configuration_sha256(inputs: EvInputs) -> str:
    """Q14 `sha256(canonical_json([foundation, binding_set, mapping_profile, source_class, policy]))` with the
    q3 P4 policy document built from `inputs`."""
    return _sha([str(inputs.foundation_revision_id).lower(), str(inputs.binding_revision_id).lower(),
                 inputs.mapping_profile_id, inputs.source_class, policy_document(inputs)])


def cohort_sha256() -> str:
    return _sha([])


def finding_key_sha256(tenant_id: UUID, site_id: UUID, charger_asset_id: UUID, connector_asset_id: UUID,
                       external_session_id: str, first_start_evidence_id: UUID) -> str:
    return _sha([str(tenant_id).lower(), str(site_id).lower(), MECHANISM, str(charger_asset_id).lower(),
                 str(connector_asset_id).lower(), external_session_id, str(first_start_evidence_id).lower()])


def finding_support_sha256(support: Iterable[tuple[str, str]]) -> str:
    """Sorted `[[id, envelope_sha256], ...]` of START/FAULT/ABORT; `[]` on withdrawal."""
    return _sha(sorted([str(i).lower(), s] for i, s in support))


EMPTY_SUPPORT_SHA256 = _sha([])


def semantic_order_key(record: EvRecord, connector_asset_id: UUID | None = None,
                       external_session_id: str | None = None) -> tuple:
    """Total order `(source_time, connector_asset_id, external_session_id, kind_rank, accepted_evidence_id)`."""
    connector = connector_asset_id if connector_asset_id is not None else record.asset_id
    session = external_session_id if external_session_id is not None else record.session_id
    return (record.source_time, "" if connector is None else str(connector).lower(), session or "",
            _KIND_RANK.get(record.kind, _CONTEXT_RANK), record.id)


# --- classification ------------------------------------------------------------------------------------------


def _decimal(text: str | None) -> Decimal | None:
    if text is None:
        return None
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None


def _scale(resolution: Decimal) -> Decimal:
    exponent = resolution.normalize().as_tuple().exponent
    return Decimal(1).scaleb(min(int(exponent), 0))


def _source_reason(r: EvRecord, inputs: EvInputs) -> tuple[str, str] | None:
    """R4 step 1 (q3 P2): source gate, or the record's binding is not an effective member of the selected set with
    the exact role, asset, source/device/signal identity and validity at source time (EXCLUDED)."""
    member = inputs.member(r.binding_revision_id)
    if (r.asset_id is None or member is None or r.binding_set_revision_id != inputs.binding_revision_id
            or member.role != r.role or member.asset_id != r.asset_id
            or str(member.source_id).lower() != str(r.source_id).lower()
            or member.device_id != r.device_id or member.signal_id != r.signal_id
            or not member.valid_at(r.source_time) or r.source_class != inputs.source_class):
        return ("EXCLUDED", "SOURCE_UNVERIFIED")
    return None


def _event_gate(r: EvRecord, inputs: EvInputs) -> tuple[str, str] | None:
    """R4 steps 1-2 for events, states and means: source, non-GOOD quality, clock."""
    found = _source_reason(r, inputs)
    if found:
        return found
    if r.quality == "SUSPECT":
        return ("CONTEXT", "SOURCE_UNVERIFIED")
    if r.quality != "GOOD":
        return ("EXCLUDED", "SOURCE_UNVERIFIED")
    if not r.clock_attested:
        return ("EXCLUDED", "CLOCK_UNATTESTED")
    return None


def _connector_mismatch(r: EvRecord, connector: EvConnector) -> bool:
    return (r.asset_id != connector.asset_id
            or (r.connector_id is not None and connector.connector_id is not None
                and r.connector_id != connector.connector_id))


def _session_event_reason(r: EvRecord, inputs: EvInputs, connector: EvConnector,
                          start_at: datetime) -> tuple[str, str] | None:
    """Use/reason of a session-claiming event other than the anchor START, or None when it qualifies."""
    found = _event_gate(r, inputs)
    if found:
        return found
    if _connector_mismatch(r, connector):
        return ("EXCLUDED", "CONNECTOR_MISMATCH")
    if r.source_time < start_at - connector.tolerance:
        return ("CONTEXT", "CONNECTOR_MISMATCH")
    if r.source_time < start_at:
        return ("EXCLUDED", "CLOCK_UNATTESTED")
    return None


def _qualifies_start(r: EvRecord, inputs: EvInputs, connectors: Mapping[UUID, EvConnector]) -> bool:
    return (r.kind == START and r.session_id is not None and r.session_id.strip() != ""
            and r.asset_id in connectors and _event_gate(r, inputs) is None
            and not _connector_mismatch(r, connectors[r.asset_id])
            and inputs.window.from_at <= r.source_time < inputs.window.to_at)


def _meter_invalid(r: EvRecord, connector: EvConnector, start_at: datetime, limit: datetime,
                   window: EvWindow) -> bool:
    """R4 METER_INVALID: quality, interval, value, resolution multiple, power plausibility, containment in
    `[start_at, limit]` and in the selected window (never clipped)."""
    if r.quality != "GOOD" or r.interval_start is None or r.interval_end is None:
        return True
    if not r.interval_start < r.interval_end:
        return True
    value = _decimal(r.value)
    if value is None or not value.is_finite() or value < 0:
        return True
    if value % connector.meter_resolution_kwh != 0:
        return True
    micros = (r.interval_end - r.interval_start) // timedelta(microseconds=1)
    if value * _US_PER_HOUR > connector.max_power_kw * micros + connector.interval_error_kwh * _US_PER_HOUR:
        return True
    if r.interval_start < start_at or r.interval_end > limit:
        return True
    return r.interval_start < window.from_at or r.interval_end > window.to_at


def _overlapping(rows: Sequence[EvRecord]) -> set[str]:
    out: set[str] = set()
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            if a.interval_start < b.interval_end and b.interval_start < a.interval_end:
                out.update((a.id, b.id))
    return out


def _intersects(r: EvRecord, start_at: datetime, span_end: datetime) -> bool:
    """Q4-Q7: a point intersects when `START <= t < end`; a mean `[a,b)` when `a < end and START < b`."""
    if r.interval_start is not None and r.interval_end is not None:
        return r.interval_start < span_end and start_at < r.interval_end
    return start_at <= r.source_time < span_end


def _quantized(value: Decimal, connector: EvConnector) -> Decimal:
    if value % connector.meter_resolution_kwh == 0:
        return value.quantize(_scale(connector.meter_resolution_kwh))
    return value


def _session(start: EvRecord, inputs: EvInputs, connector: EvConnector) -> EvSession:
    window = inputs.window
    session_id = start.session_id
    start_at = start.source_time
    links: dict[str, EvLink] = {}

    def link(r: EvRecord, use: str, reason: str | None) -> None:
        links.setdefault(r.id, EvLink(r.accepted_evidence_id, r.envelope_sha256, use, reason))

    link(start, "SUPPORT", None)
    claiming = sorted((r for r in inputs.records if r.session_id == session_id and r.id != start.id),
                      key=semantic_order_key)

    # Competing STARTs and terminals.
    terminals: list[EvRecord] = []
    for r in claiming:
        if r.kind == START:
            found = _session_event_reason(r, inputs, connector, start_at)
            link(r, *(found or ("CONTEXT", "CONFLICTING_START")))
        elif r.kind in TERMINALS:
            found = _session_event_reason(r, inputs, connector, start_at)
            if found:
                link(r, *found)
            else:
                terminals.append(r)
    distinct_terminals = {r.id: r for r in terminals}
    if len(distinct_terminals) > 1:
        state = "CONTRADICTORY"
        for r in distinct_terminals.values():
            link(r, "CONTEXT", "CONFLICTING_TERMINAL")
    elif distinct_terminals:
        terminal = next(iter(distinct_terminals.values()))
        state = "COMPLETED" if terminal.kind == END else "OBSERVED_ABORT"
        link(terminal, "SUPPORT", None)
    else:
        state = "INCOMPLETE"
    terminal_times = sorted(r.source_time for r in distinct_terminals.values())

    # Same-session meter deltas.
    meters = [r for r in claiming if r.family == "MEASUREMENT" and r.measurement == DELTA]
    limit = terminal_times[-1] if state in ("COMPLETED", "OBSERVED_ABORT") else window.to_at
    reasons: dict[str, tuple[str, str]] = {}
    for r in meters:
        found = _source_reason(r, inputs)
        if found is None and not r.clock_attested:
            found = ("EXCLUDED", "CLOCK_UNATTESTED")
        if found is None and _connector_mismatch(r, connector):
            found = ("EXCLUDED", "CONNECTOR_MISMATCH")
        if found is None and state == "CONTRADICTORY":
            found = ("EXCLUDED", "CONFLICTING_TERMINAL")
        if found is None and _meter_invalid(r, connector, start_at, limit, window):
            found = ("EXCLUDED", "METER_INVALID")
        if found is not None:
            reasons[r.id] = found
    eligible = [r for r in meters if r.id not in reasons]
    for key in _overlapping(eligible):
        reasons[key] = ("EXCLUDED", "METER_OVERLAP")
    support = [r for r in eligible if r.id not in reasons]

    if state in ("COMPLETED", "OBSERVED_ABORT"):
        span_end = terminal_times[-1]
    elif state == "CONTRADICTORY":
        span_end = terminal_times[-1]
    else:
        span_end = max([r.interval_end for r in eligible], default=start_at)

    # Same-connector deltas of another (or no) session inside the span: EXCLUDED CONNECTOR_MISMATCH.
    foreign = [r for r in inputs.records
               if r.family == "MEASUREMENT" and r.measurement == DELTA and r.session_id != session_id
               and r.asset_id == connector.asset_id and _intersects(r, start_at, span_end)]
    for r in foreign:
        reasons[r.id] = _source_reason(r, inputs) or (
            ("EXCLUDED", "CLOCK_UNATTESTED") if not r.clock_attested else ("EXCLUDED", "CONNECTOR_MISMATCH"))
    meter_rows = sorted(meters + foreign, key=semantic_order_key)

    # FAULT/CLEAR, then connector state/means and Site import intersecting the observed span.
    fault_candidates: list[EvRecord] = []
    abort_at = terminal_times[0] if state == "OBSERVED_ABORT" else None
    for r in claiming:
        if r.kind in (FAULT, CLEAR):
            found = _session_event_reason(r, inputs, connector, start_at)
            if found:
                link(r, *found)
            elif (r.kind == FAULT and abort_at is not None
                  and abs(r.source_time - abort_at) <= connector.tolerance):
                fault_candidates.append(r)
            else:
                link(r, "CONTEXT", None)
    fault = fault_candidates[0] if len(fault_candidates) == 1 else None
    for r in fault_candidates:
        link(r, "SUPPORT" if r is fault else "CONTEXT", None)
    for r in meter_rows:
        use, reason = reasons.get(r.id, ("SUPPORT", None))
        link(r, use, reason)

    context = sorted((r for r in inputs.records if r.id not in links and _intersects(r, start_at, span_end)),
                     key=semantic_order_key)
    for r in context:
        on_connector = r.asset_id == connector.asset_id
        if r.kind in (FAULT, CLEAR) and r.session_id is None and on_connector:
            link(r, *(_event_gate(r, inputs) or ("CONTEXT", None)))
        elif r.family == "MEASUREMENT" and r.measurement in (STATE_AT_INSTANT, MEAN) and on_connector:
            found = _event_gate(r, inputs)
            if found is None and r.session_id is not None and r.session_id != session_id:
                found = ("EXCLUDED", "CONNECTOR_MISMATCH")
            link(r, *(found or ("CONTEXT", None)))
        elif (r.family == "MEASUREMENT" and r.measurement == MEAN and r.asset_id is not None
              and r.asset_id not in _connector_ids(inputs)):
            link(r, *(_event_gate(r, inputs) or ("CONTEXT", None)))

    # Coverage and quantity.
    intervals = []
    for r in meter_rows:
        value = _decimal(r.value)
        if (r.asset_id is None or r.interval_start is None or r.interval_end is None
                or not r.interval_start < r.interval_end or value is None or not value.is_finite() or value < 0):
            continue
        current = links[r.id]
        intervals.append(EvInterval(r.accepted_evidence_id, r.asset_id, r.interval_start, r.interval_end,
                                    _quantized(value, connector), connector.interval_error_kwh, current.use,
                                    current.reason))
    if state == "CONTRADICTORY":
        supported_kwh = None
        unknown_seconds = None
        energy_complete = None
        uncovered = 0
        end_at = None
        end_bounds = (terminal_times[0], terminal_times[-1])
    else:
        amounts = [_decimal(r.value) for r in support]
        supported_kwh = (sum(amounts, Decimal(0)).quantize(_scale(connector.meter_resolution_kwh))
                         if amounts else None)
        span_us = (span_end - start_at) // timedelta(microseconds=1)
        covered = sum((r.interval_end - r.interval_start) // timedelta(microseconds=1) for r in support)
        uncovered = max(span_us - covered, 0)
        unknown_seconds = -(-uncovered // _US_PER_SECOND)
        if state == "INCOMPLETE":
            energy_complete = False
            end_at = None
            end_bounds = (None, None)
        else:
            energy_complete = uncovered == 0 and supported_kwh is not None
            end_at = span_end
            end_bounds = (span_end, span_end)

    codes = set()
    if state == "INCOMPLETE":
        codes.add("MISSING_TERMINAL")
    if state == "CONTRADICTORY":
        codes.add("CONFLICTING_TERMINAL")
    if state != "CONTRADICTORY" and uncovered > 0:
        codes.add("METER_GAP")
    codes.update(link_.reason for link_ in links.values() if link_.reason is not None)
    reason_codes = tuple(code for code in REASON_ORDER if code in codes)

    finding_support: tuple[tuple[str, str], ...] = ()
    if fault is not None:
        abort = distinct_terminals[next(iter(distinct_terminals))]
        finding_support = tuple(sorted((r.id, r.envelope_sha256) for r in (start, fault, abort)))
    ordered_links = tuple(links[k] for k in sorted(links))
    return EvSession(
        external_session_id=session_id, charger_asset_id=connector.charger_asset_id,
        connector_asset_id=connector.asset_id, first_start_evidence_id=start.accepted_evidence_id,
        anchor_time=start_at, state=state, start_at=start_at, end_at=end_at, start_bounds=(start_at, start_at),
        end_bounds=end_bounds, supported_kwh=supported_kwh, energy_complete=energy_complete,
        unknown_meter_seconds=unknown_seconds, reason_codes=reason_codes,
        fault_evidence_id=None if fault is None else fault.accepted_evidence_id, finding_support=finding_support,
        links=ordered_links, intervals=tuple(sorted(intervals, key=lambda i: (i.start_at, str(i.evidence_id)))),
        basis_sha256=basis_sha256(ordered_links, inputs),
        finding_key_sha256=finding_key_sha256(inputs.tenant_id, inputs.site_id, connector.charger_asset_id,
                                              connector.asset_id, session_id, start.accepted_evidence_id),
        finding_support_sha256=finding_support_sha256(finding_support) if finding_support else None,
    )


def _connector_ids(inputs: EvInputs) -> set[UUID]:
    return {c.asset_id for c in inputs.connectors}


_DENOMINATOR_KEYS = ("started", "completed", "observed_abort", "incomplete", "contradictory", "orphan",
                     "confirmed_delivery", "fault_aborted")


def assess(inputs: EvInputs) -> EvAssessment:
    """`ev-session/1` over one selection: sessions, orphan terminals, whole-window denominator, claim level."""
    connectors: dict[UUID, EvConnector] = {}
    for c in inputs.connectors:
        if c.asset_id in connectors:
            raise EvConfigurationRefused(f"connector {c.asset_id} is configured twice")
        connectors[c.asset_id] = c
    starts: dict[tuple, EvRecord] = {}
    for r in sorted(inputs.records, key=semantic_order_key):
        if _qualifies_start(r, inputs, connectors):
            starts.setdefault((r.asset_id, r.session_id), r)
    sessions = tuple(_session(r, inputs, connectors[r.asset_id])
                     for r in sorted(starts.values(), key=semantic_order_key))

    # q3 P5: an orphan is a terminal without a qualifying START for its connector/session in the window.
    orphans = tuple(r.accepted_evidence_id for r in sorted(inputs.records, key=semantic_order_key)
                    if r.kind in TERMINALS and (r.asset_id, r.session_id) not in starts
                    and inputs.window.from_at <= r.source_time < inputs.window.to_at)
    # r9 M1-c: each accepted record excluded by its exact binding (source gate), once, full input set.
    unverified = sorted((r for r in inputs.records if _source_reason(r, inputs) is not None),
                        key=lambda r: (r.source_time, r.id))
    excluded = tuple({"evidence_id": r.id, "record_kind": r.record_kind, "reason": "SOURCE_UNVERIFIED"}
                     for r in unverified)
    # r9 M1-b: no qualifying session, and a candidate START in the window was excluded for its binding.
    if not sessions and any(r.kind == START and r.session_id is not None and r.session_id.strip() != ""
                            and inputs.window.from_at <= r.source_time < inputs.window.to_at
                            for r in unverified):
        return EvAssessment(assessment_key(inputs.window), (), orphans, dict.fromkeys(_DENOMINATOR_KEYS),
                            "UNKNOWN", "UNKNOWN", BINDING_UNVERIFIED, excluded)
    counts = {state: sum(1 for s in sessions if s.state == state) for state in STATES}
    denominator = {
        "started": len(sessions),
        "completed": counts["COMPLETED"],
        "observed_abort": counts["OBSERVED_ABORT"],
        "incomplete": counts["INCOMPLETE"],
        "contradictory": counts["CONTRADICTORY"],
        "orphan": len(orphans),
        "confirmed_delivery": sum(1 for s in sessions if s.state == "COMPLETED" and s.energy_complete is True),
        "fault_aborted": sum(1 for s in sessions if s.qualified_fault_abort),
    }
    if not sessions:
        claim_level = "UNKNOWN"
    elif counts["CONTRADICTORY"]:
        claim_level = "CONTRADICTORY"
    elif counts["INCOMPLETE"] or any("METER_GAP" in s.reason_codes for s in sessions):
        claim_level = "BOUNDED"
    else:
        claim_level = "OBSERVED"
    if counts["CONTRADICTORY"]:
        status_state = "CONTRADICTORY"
    elif sessions:
        status_state = "OBSERVED_SESSIONS"
    else:
        status_state = "NO_SESSIONS_OBSERVED"
    return EvAssessment(assessment_key(inputs.window), sessions, orphans, denominator, status_state, claim_level,
                        None, excluded)


def plain(value):
    """JSON form of a result value: decimal strings at their stored scale, UTC instants, lowercase UUID text."""
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return iso(value)
    if isinstance(value, UUID):
        return str(value).lower()
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if hasattr(value, "__dataclass_fields__"):
        return {k: plain(getattr(value, k)) for k in value.__dataclass_fields__}
    return value
