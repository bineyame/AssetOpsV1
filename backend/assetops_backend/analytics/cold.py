"""Pure cold-chain assessment rules: `cold-excursion/1` and `cold-start-response/1` (W2-03).

Authority: `D-2026-10-17-w2-02-buildspec`, `.agent/W2-03-build-spec.md` ("Inputs, model and selection",
"Rules and exact outcomes") and `.agent/W2-technical-design-cold.md` section 5.

The rules read only accepted public evidence that the caller has already selected for one Site, one fixed
half-open window `[from_at, to_at)` and one knowledge cutoff `known_at`, together with the effective
configuration (room policy, return hysteresis, minimum excursion, start timeout, the bound probe/room/generator
assets) and the exact S4-05 source gate. A reading qualifies only when it is bound to the effective
`cold-roles-1` role and asset, GOOD and clock-attested; SUSPECT readings stay linked as CONTEXT, and unbound,
clock-unattested and contradictory records stay linked as EXCLUDED with their reason. Nothing here persists,
reads a clock, or consults private simulation state.

Claims stay bounded: an excursion is bounded by observed samples only (no interpolation across a gap of more
than ten minutes, no continuous curve), degree minutes are sums of observed rectangles, the peak is the maximum
observed sample. No spoilage, product-loss or failed-part claim is made.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Iterable, Mapping, Sequence
from uuid import UUID

from assetops_backend.analytics.assessment_inputs import iso
from assetops_contracts.source_envelope import canonical_json

EXCURSION_ANALYTIC = "cold-excursion"
START_RESPONSE_ANALYTIC = "cold-start-response"
MODEL_VERSION = "1"
DOMAIN = "cold_chain"

CLAIM_LEVELS = ("OBSERVED", "BOUNDED", "POSSIBLE", "UNKNOWN", "CONTRADICTORY")
EXCURSION_STATES = ("OBSERVED_EXCURSION", "NO_EXCURSION_OBSERVED", "UNKNOWN", "CONTRADICTORY")
START_RESULTS = ("OBSERVED_SUCCESS", "OBSERVED_FAILURE", "UNKNOWN", "CONTRADICTORY")
STEPS = ("GRID", "START_REQUEST", "START_RESULT", "GENERATOR", "TRANSFER", "BUS", "COMPRESSOR", "PROBE")
GAP_REASONS = ("MISSING_PROBE", "SUSPECT", "CLOCK_UNATTESTED", "CONTRADICTORY", "UNBOUND")
USES = ("SUPPORT", "CONTEXT", "EXCLUDED")

SLOT = timedelta(minutes=5)
MAX_BRIDGE = timedelta(minutes=10)
ORDER_TOLERANCE = timedelta(seconds=30)
COVERAGE_NEEDED = Decimal("0.8")

PROBE_ROLE = "chamber_temperature"
START_ROLE = "backup_start_event"
GRID_EVENT_ROLE = "grid_power_event"
GENERATOR_STATE_ROLE = "generator_state"
TRANSFER_ROLE = "transfer_result"
BUS_ROLE = "backup_bus_state"
COMPRESSOR_ROLE = "compressor_state"
DOOR_ROLE = "door_event"
#: Event kinds each event role carries, so an unbound event still links as EXCLUDED to the chain it names.
_ROLE_EVENT_KINDS = {
    START_ROLE: ("START_REQUEST", "START_RESULT"),
    GRID_EVENT_ROLE: ("POWER_LOSS", "POWER_RESTORED"),
    TRANSFER_ROLE: ("TRANSFER_RESULT",),
}
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


@dataclass(frozen=True)
class ColdEvidence:
    """One accepted public record as the selection read it. `role`/`asset_id` are the effective
    `cold-roles-1` binding at the record's source time (None when unbound); `value` is a Decimal for numeric
    readings, the state text for state readings, None for events."""

    evidence_id: UUID
    envelope_sha256: str
    family: str
    record_kind: str | None
    role: str | None
    asset_id: UUID | None
    source_time: datetime
    received_at: datetime
    decided_at: datetime
    quality: str
    value: Decimal | str | None
    unit: str | None
    event_id: str | None
    correlation_id: str | None
    outcome: str | None
    source_id: str
    clock_attested: bool


@dataclass(frozen=True)
class ColdWindow:
    """UTC half-open `[from_at, to_at)` and the knowledge cutoff on server receipt/decision time."""

    from_at: datetime
    to_at: datetime
    known_at: datetime

    def __post_init__(self) -> None:
        if not self.from_at < self.to_at:
            raise ValueError("a cold window needs from_at < to_at")

    def expected_instants(self) -> tuple[datetime, ...]:
        """Five-minute UTC-aligned instants `t` with `from_at <= t < to_at`."""
        offset = (self.from_at - _EPOCH) % SLOT
        first = self.from_at if offset == timedelta(0) else self.from_at + (SLOT - offset)
        out = []
        t = first
        while t < self.to_at:
            out.append(t)
            t += SLOT
        return tuple(out)


@dataclass(frozen=True)
class ColdPolicy:
    """Effective room configuration for `cold-excursion/1`."""

    room_asset_id: UUID
    probe_asset_id: UUID
    policy_low: Decimal
    policy_high: Decimal
    return_hysteresis: Decimal
    min_excursion_minutes: Decimal


@dataclass(frozen=True)
class ColdStartPolicy:
    """Effective generator configuration for `cold-start-response/1`; `transfer_bound` says the optional
    `transfer_result` role is bound, so a missing transfer is a missing step."""

    generator_asset_id: UUID
    start_timeout_minutes: Decimal
    transfer_bound: bool
    probe_asset_id: UUID | None = None


@dataclass(frozen=True)
class SourceGate:
    """The exact S4-05 source classification and source IDs, and whether it permits a Finding."""

    classification: str
    source_ids: tuple[str, ...]
    permitted: bool

    def basis(self) -> dict:
        return {"classification": self.classification, "source_ids": sorted(self.source_ids)}


@dataclass(frozen=True)
class ColdLink:
    evidence_id: UUID
    use: str
    reason: str | None = None


@dataclass(frozen=True)
class ColdGap:
    start: datetime
    end: datetime
    reason: str
    expected_points: int
    received_points: int


@dataclass(frozen=True)
class ColdExcursion:
    direction: str  # HIGH | LOW
    anchor_evidence_id: UUID
    anchor_time: datetime
    start_earliest: datetime | None
    start_latest: datetime
    end_earliest: datetime | None
    end_latest: datetime | None
    open: bool
    duration_low: Decimal
    duration_high: Decimal | None
    degree_minutes_low: Decimal
    degree_minutes_high: Decimal
    peak_observed: Decimal | None
    claim_level: str
    exposure_finding: bool
    links: tuple[ColdLink, ...]
    limitation: str | None


@dataclass(frozen=True)
class ColdStep:
    step: str
    state: str  # OBSERVED | MISSING | CONTRADICTORY
    at: datetime | None
    evidence_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True)
class ColdStartChain:
    correlation_id: str
    generator_asset_id: UUID
    anchor_evidence_id: UUID
    anchor_time: datetime
    steps: tuple[ColdStep, ...]
    missing_steps: tuple[str, ...]
    result: str
    claim_level: str
    start_timeout_min: Decimal
    failure_finding: bool
    links: tuple[ColdLink, ...]
    limitation: str | None


@dataclass(frozen=True)
class ColdAssessment:
    analytic_id: str
    model_version: str
    window: ColdWindow
    state: str
    claim_level: str
    known_points: int
    expected_points: int
    coverage: Decimal
    gaps: tuple[ColdGap, ...] = ()
    excursions: tuple[ColdExcursion, ...] = ()
    chains: tuple[ColdStartChain, ...] = ()
    links: tuple[ColdLink, ...] = ()
    limitations: tuple[str, ...] = field(default=())


# --- identity ------------------------------------------------------------------------------------------------


def episode_key_sha256(tenant_id: UUID, site_id: UUID, kind: str, subject_asset_id: UUID,
                       anchor_evidence_id: UUID) -> str:
    """SHA-256 of canonical JSON `[tenant_id,site_id,kind,subject_asset_id,anchor_evidence_id]`."""
    document = [str(tenant_id).lower(), str(site_id).lower(), kind, str(subject_asset_id).lower(),
                str(anchor_evidence_id).lower()]
    return hashlib.sha256(canonical_json(document).encode("utf-8")).hexdigest()


def basis_sha256(*, analytic_id: str, model_version: str, tenant_id: UUID, site_id: UUID, window: ColdWindow,
                 foundation_revision_ids: Iterable[UUID], binding_revision_ids: Iterable[UUID],
                 source_gate: SourceGate, records: Iterable[ColdEvidence]) -> str:
    """SHA-256 of the canonical basis document; records sorted by `(evidence_id, envelope_sha256)`."""
    rows = sorted({(str(r.evidence_id).lower(), r.envelope_sha256) for r in records})
    document = {
        "analytic_id": analytic_id,
        "model_version": model_version,
        "tenant_id": str(tenant_id).lower(),
        "site_id": str(site_id).lower(),
        "window": {"from": iso(window.from_at), "to": iso(window.to_at)},
        "known_at": iso(window.known_at),
        "foundation_revision_ids": sorted({str(i).lower() for i in foundation_revision_ids}),
        "binding_revision_ids": sorted({str(i).lower() for i in binding_revision_ids}),
        "source_gate": source_gate.basis(),
        "records": [{"evidence_id": e, "envelope_sha256": s} for e, s in rows],
    }
    return hashlib.sha256(canonical_json(document).encode("utf-8")).hexdigest()


# --- selection helpers ---------------------------------------------------------------------------------------


def _known(evidence: Iterable[ColdEvidence], window: ColdWindow) -> list[ColdEvidence]:
    rows = [e for e in evidence if window.from_at <= e.source_time < window.to_at
            and e.received_at <= window.known_at and e.decided_at <= window.known_at]
    return sorted(rows, key=lambda e: (e.source_time, e.received_at, str(e.evidence_id)))


def _exclusion(e: ColdEvidence, role: str, asset_id: UUID | None) -> str | None:
    """Why a record of `role` cannot support a claim, or None when it qualifies."""
    if e.role is None or (asset_id is not None and e.asset_id != asset_id):
        return "UNBOUND"
    if not e.clock_attested:
        return "CLOCK_UNATTESTED"
    if e.quality == "SUSPECT":
        return "SUSPECT"
    if e.quality != "GOOD":
        return e.quality
    return None


def _use(reason: str) -> str:
    return "CONTEXT" if reason == "SUSPECT" else "EXCLUDED"


def _minutes(delta: timedelta) -> Decimal:
    return Decimal(int(delta.total_seconds())) / Decimal(60)


def _is_probe_candidate(e: ColdEvidence, policy: ColdPolicy) -> bool:
    if e.family != "MEASUREMENT":
        return False
    if e.role == PROBE_ROLE:
        return True
    # An unbound temperature reading is still a probe-shaped record the gap must name.
    return e.role is None and e.unit == "degC"


# --- cold-excursion/1 ----------------------------------------------------------------------------------------


def _probe_points(rows: Sequence[ColdEvidence], policy: ColdPolicy) -> tuple[
        list[ColdEvidence], dict[UUID, str], dict[datetime, str]]:
    """(qualifying points ordered by source time, excluded/context reason by evidence ID, reason by instant)."""
    reasons: dict[UUID, str] = {}
    by_time: dict[datetime, list[ColdEvidence]] = {}
    instant_reason: dict[datetime, str] = {}
    for e in rows:
        if not _is_probe_candidate(e, policy):
            continue
        reason = _exclusion(e, PROBE_ROLE, policy.probe_asset_id)
        if reason is None and not isinstance(e.value, Decimal):
            reason = "UNAVAILABLE"
        if reason is not None:
            reasons[e.evidence_id] = reason
            instant_reason.setdefault(e.source_time, reason)
            continue
        by_time.setdefault(e.source_time, []).append(e)
    points: list[ColdEvidence] = []
    for t, group in sorted(by_time.items()):
        if len({g.value for g in group}) > 1:
            for g in group:
                reasons[g.evidence_id] = "CONTRADICTORY"
            instant_reason[t] = "CONTRADICTORY"
            continue
        points.append(group[0])
        for g in group[1:]:
            reasons[g.evidence_id] = "DUPLICATE"
    return points, reasons, instant_reason


def _gaps(window: ColdWindow, points: Sequence[ColdEvidence], instant_reason: Mapping[datetime, str]
          ) -> tuple[ColdGap, ...]:
    present = {p.source_time for p in points}
    gaps: list[ColdGap] = []
    run: list[datetime] = []
    reason_of = lambda t: instant_reason.get(t, "MISSING_PROBE") if instant_reason.get(t) in GAP_REASONS \
        else "MISSING_PROBE"

    def close(end: datetime) -> None:
        if run:
            gaps.append(ColdGap(run[0], end, reason_of(run[0]), len(run),
                                sum(1 for t in run if t in instant_reason)))
            run.clear()

    for t in window.expected_instants():
        if t in present:
            close(t)
            continue
        if run and reason_of(run[0]) != reason_of(t):
            close(t)
        run.append(t)
    close(window.to_at)
    return tuple(gaps)


def _band(value: Decimal, policy: ColdPolicy) -> str:
    if value > policy.policy_high:
        return "HIGH"
    if value < policy.policy_low:
        return "LOW"
    return "IN"


def _returned(value: Decimal, direction: str, policy: ColdPolicy) -> bool:
    if direction == "HIGH":
        return policy.policy_low <= value <= policy.policy_high - policy.return_hysteresis
    return policy.policy_low + policy.return_hysteresis <= value <= policy.policy_high


def _exceedance(value: Decimal, direction: str, policy: ColdPolicy) -> Decimal:
    over = value - policy.policy_high if direction == "HIGH" else policy.policy_low - value
    return over if over > 0 else Decimal(0)


def _episodes(points: Sequence[ColdEvidence], policy: ColdPolicy) -> list[dict]:
    """Confirmed excursions as index spans over `points`, plus whether any out-of-band sample stayed unconfirmed."""
    found: list[dict] = []
    i, n = 0, len(points)
    while i < n:
        direction = _band(points[i].value, policy)
        if direction == "IN":
            i += 1
            continue
        nxt = points[i + 1] if i + 1 < n else None
        confirmed = (nxt is not None and _band(nxt.value, policy) == direction
                     and SLOT <= nxt.source_time - points[i].source_time <= MAX_BRIDGE)
        if not confirmed:
            found.append({"start": i, "direction": direction, "confirmed": False})
            i += 1
            continue
        j = i + 1
        end_return = None
        while j < n:
            a = points[j]
            b = points[j + 1] if j + 1 < n else None
            if _returned(a.value, direction, policy) and b is not None and _returned(b.value, direction, policy):
                end_return = j
                break
            j += 1
        found.append({"start": i, "direction": direction, "confirmed": True, "return": end_return})
        if end_return is None:
            break
        i = end_return + 2
    return found


def _excursion(points: Sequence[ColdEvidence], span: dict, policy: ColdPolicy, window: ColdWindow,
               rows: Sequence[ColdEvidence], reasons: Mapping[UUID, str], claim_ceiling: str,
               gate: SourceGate) -> ColdExcursion:
    i, direction, r = span["start"], span["direction"], span["return"]
    first = points[i]
    before = points[i - 1] if i > 0 else None
    start_latest = first.source_time
    start_earliest = (before.source_time if before is not None and _band(before.value, policy) == "IN"
                      and first.source_time - before.source_time <= MAX_BRIDGE else None)
    last_out_index = (r - 1) if r is not None else len(points) - 1
    # Continuously observed run from the latest start: no step longer than ten minutes is bridged.
    k = i
    while k < last_out_index and points[k + 1].source_time - points[k].source_time <= MAX_BRIDGE:
        k += 1
    continuous_to = points[k].source_time
    if r is not None:
        end_earliest = points[r - 1].source_time
        stable = points[r]
        end_latest = stable.source_time if stable.source_time - end_earliest <= MAX_BRIDGE else None
        observed_end = end_earliest if k == last_out_index else continuous_to
        duration_low = max(Decimal(0), _minutes(observed_end - start_latest))
        duration_high = (_minutes(end_latest - start_earliest)
                         if end_latest is not None and start_earliest is not None else None)
        last_index = r
        is_open = False
    else:
        end_earliest = end_latest = None
        duration_low = max(Decimal(0), _minutes(continuous_to - start_latest))
        duration_high = None
        last_index = len(points) - 1
        is_open = True
    lo_index = i - 1 if start_earliest is not None else i
    dm_low = dm_high = Decimal(0)
    for a, b in zip(points[lo_index:last_index], points[lo_index + 1:last_index + 1]):
        step = b.source_time - a.source_time
        if step > MAX_BRIDGE:
            continue
        ea, eb = _exceedance(a.value, direction, policy), _exceedance(b.value, direction, policy)
        dm_low += min(ea, eb) * _minutes(step)
        dm_high += max(ea, eb) * _minutes(step)
    inside = points[i:last_out_index + 1]
    peak = (max(p.value for p in inside) if direction == "HIGH" else min(p.value for p in inside)) if inside \
        else None
    long_enough = duration_low >= policy.min_excursion_minutes
    if claim_ceiling in ("UNKNOWN", "CONTRADICTORY"):
        claim, exposure = claim_ceiling, False
    elif long_enough and gate.permitted:
        claim, exposure = "BOUNDED", True
    else:
        claim, exposure = "POSSIBLE", False
    span_from = start_earliest or start_latest
    span_to = end_latest or window.to_at
    used = {p.evidence_id for p in points[lo_index:last_index + 1]}
    links: list[ColdLink] = [ColdLink(e, "SUPPORT") for e in sorted(used, key=str)]
    for e in rows:
        if e.evidence_id in used or not (span_from <= e.source_time <= span_to):
            continue
        if e.evidence_id in reasons:
            links.append(ColdLink(e.evidence_id, _use(reasons[e.evidence_id]), reasons[e.evidence_id]))
        elif e.role == DOOR_ROLE:
            links.append(ColdLink(e.evidence_id, "CONTEXT", "DOOR_EVENT"))
    limitation = _excursion_limitation(start_earliest, is_open, long_enough, gate, claim_ceiling)
    return ColdExcursion(direction, first.evidence_id, start_latest, start_earliest, start_latest, end_earliest,
                         end_latest, is_open, duration_low, duration_high, dm_low, dm_high, peak, claim, exposure,
                         tuple(links), limitation)


def _excursion_limitation(start_earliest, is_open, long_enough, gate, ceiling) -> str | None:
    parts = []
    if ceiling == "UNKNOWN":
        parts.append("Probe coverage is below 80 percent of the expected readings, so the excursion is not assessed.")
    if ceiling == "CONTRADICTORY":
        parts.append("Contradictory probe readings block an excursion claim.")
    if start_earliest is None:
        parts.append("The earliest start is not known.")
    if is_open:
        parts.append("The excursion had not returned to the band by the end of the window.")
    if not long_enough and ceiling not in ("UNKNOWN", "CONTRADICTORY"):
        parts.append("The observed duration is shorter than the minimum excursion.")
    if not gate.permitted:
        parts.append("The source classification does not permit a Finding.")
    return " ".join(parts) or None


def assess_excursion(evidence: Iterable[ColdEvidence], window: ColdWindow, policy: ColdPolicy,
                     source_gate: SourceGate) -> ColdAssessment:
    """`cold-excursion/1` over the accepted records known at `window.known_at`."""
    rows = _known(evidence, window)
    points, reasons, instant_reason = _probe_points(rows, policy)
    expected = window.expected_instants()
    known = len({p.source_time for p in points} & set(expected))
    coverage = min(Decimal(1), Decimal(known) / Decimal(len(expected))) if expected else Decimal(0)
    contradictory = any(r == "CONTRADICTORY" for r in reasons.values())
    ceiling = "CONTRADICTORY" if contradictory else ("UNKNOWN" if coverage < COVERAGE_NEEDED else "BOUNDED")
    spans = _episodes(points, policy)
    excursions = tuple(_excursion(points, s, policy, window, rows, reasons, ceiling, source_gate)
                       for s in spans if s["confirmed"])
    unconfirmed = any(not s["confirmed"] for s in spans)
    if ceiling == "CONTRADICTORY":
        state, claim = "CONTRADICTORY", "CONTRADICTORY"
    elif ceiling == "UNKNOWN":
        state, claim = "UNKNOWN", "UNKNOWN"
    elif excursions:
        state = "OBSERVED_EXCURSION"
        claim = "BOUNDED" if any(x.claim_level == "BOUNDED" for x in excursions) else "POSSIBLE"
    elif unconfirmed:
        state, claim = "UNKNOWN", "POSSIBLE"
    else:
        state, claim = "NO_EXCURSION_OBSERVED", "BOUNDED"
    links = [ColdLink(p.evidence_id, "SUPPORT") for p in points]
    links += [ColdLink(e, _use(r), r) for e, r in reasons.items()]
    links += [ColdLink(e.evidence_id, "CONTEXT", "DOOR_EVENT") for e in rows if e.role == DOOR_ROLE]
    limitations = []
    if coverage < COVERAGE_NEEDED:
        limitations.append(f"{known} of {len(expected)} expected probe readings are usable.")
    if unconfirmed and not excursions:
        limitations.append("An out-of-band reading was not confirmed by a second reading.")
    return ColdAssessment(EXCURSION_ANALYTIC, MODEL_VERSION, window, state, claim, known, len(expected), coverage,
                          _gaps(window, points, instant_reason), excursions, (), tuple(links), tuple(limitations))


# --- cold-start-response/1 -----------------------------------------------------------------------------------


def _qualifying(rows: Sequence[ColdEvidence], role: str, asset_id: UUID | None) -> tuple[
        list[ColdEvidence], dict[UUID, str]]:
    good, reasons = [], {}
    for e in rows:
        if e.role != role and not (e.role is None and e.record_kind in _ROLE_EVENT_KINDS.get(role, ())):
            continue
        reason = _exclusion(e, role, asset_id)
        if reason is None:
            good.append(e)
        else:
            reasons[e.evidence_id] = reason
    return good, reasons


def _first_state(rows: Sequence[ColdEvidence], after: datetime | None, values: frozenset | None = None
                 ) -> ColdEvidence | None:
    if after is None:
        return None
    for e in rows:
        if e.source_time >= after - ORDER_TOLERANCE and (values is None or e.value in values):
            return e
    return None


def _chain(correlation: str, group: list[ColdEvidence], rows: Sequence[ColdEvidence], policy: ColdStartPolicy,
           window: ColdWindow, gate: SourceGate, probe_rows: Sequence[ColdEvidence]) -> ColdStartChain:
    reasons: dict[UUID, str] = {}
    starts, r = _qualifying(group, START_ROLE, policy.generator_asset_id)
    reasons.update(r)
    grid, r = _qualifying(group, GRID_EVENT_ROLE, None)
    reasons.update(r)
    transfers, r = _qualifying(group, TRANSFER_ROLE, None)
    reasons.update(r)
    requests = [e for e in starts if e.record_kind == "START_REQUEST"]
    request = requests[0] if requests else None
    results = [e for e in starts if e.record_kind == "START_RESULT"
               and (request is None or e.source_time >= request.source_time - ORDER_TOLERANCE)]
    succeeded = [e for e in results if e.outcome == "SUCCEEDED"]
    failed = [e for e in results if e.outcome == "FAILED"]
    losses = [e for e in grid if e.record_kind == "POWER_LOSS"]
    gen_states, r = _qualifying(rows, GENERATOR_STATE_ROLE, policy.generator_asset_id)
    reasons.update(r)
    bus_states, _ = _qualifying(rows, BUS_ROLE, None)
    comp_states, _ = _qualifying(rows, COMPRESSOR_ROLE, None)
    timeout = timedelta(seconds=int(policy.start_timeout_minutes * 60))

    steps: list[ColdStep] = []
    steps.append(ColdStep("GRID", "OBSERVED", losses[0].source_time, (losses[0].evidence_id,)) if losses
                 else ColdStep("GRID", "MISSING", None))
    steps.append(ColdStep("START_REQUEST", "OBSERVED", request.source_time, (request.evidence_id,)) if request
                 else ColdStep("START_REQUEST", "MISSING", None))
    contradictory = bool(succeeded and failed)
    inferred_timeout = False
    if contradictory:
        steps.append(ColdStep("START_RESULT", "CONTRADICTORY", None,
                              tuple(e.evidence_id for e in succeeded + failed)))
        for e in succeeded + failed:
            reasons[e.evidence_id] = "CONTRADICTORY"
        result_at = None
    elif results:
        steps.append(ColdStep("START_RESULT", "OBSERVED", results[0].source_time, (results[0].evidence_id,)))
        result_at = results[0].source_time
    else:
        steps.append(ColdStep("START_RESULT", "MISSING", None))
        result_at = None
        if request is not None and request.source_time + timeout < window.to_at:
            need = [t for t in window.expected_instants()
                    if request.source_time <= t <= request.source_time + timeout]
            seen = {e.source_time: e.value for e in gen_states}
            inferred_timeout = bool(need) and all(t in seen and seen[t] != "RUNNING" for t in need)
    gen_after = result_at if result_at is not None else (request.source_time + timeout if inferred_timeout else None)
    generator = _first_state(gen_states, gen_after, frozenset({"RUNNING", "FAILED"}))
    steps.append(ColdStep("GENERATOR", "OBSERVED", generator.source_time, (generator.evidence_id,)) if generator
                 else ColdStep("GENERATOR", "MISSING", None))
    # The outage window ends at the first restoration: a transfer back to the grid is not the start response.
    restored = [e.source_time for e in grid if e.record_kind == "POWER_RESTORED"]
    in_outage = [e for e in transfers if not restored or e.source_time < restored[0] - ORDER_TOLERANCE]
    transfer = in_outage[0] if in_outage else None
    if policy.transfer_bound:
        steps.append(ColdStep("TRANSFER", "OBSERVED", transfer.source_time, (transfer.evidence_id,)) if transfer
                     else ColdStep("TRANSFER", "MISSING", None))
    anchor_after = (transfer.source_time if transfer else
                    (generator.source_time if generator else result_at))
    bus = _first_state(bus_states, anchor_after)
    steps.append(ColdStep("BUS", "OBSERVED", bus.source_time, (bus.evidence_id,)) if bus
                 else ColdStep("BUS", "MISSING", None))
    compressor = _first_state(comp_states, bus.source_time if bus else None)
    steps.append(ColdStep("COMPRESSOR", "OBSERVED", compressor.source_time, (compressor.evidence_id,))
                 if compressor else ColdStep("COMPRESSOR", "MISSING", None))
    probe = _first_state(probe_rows, compressor.source_time if compressor else None)
    steps.append(ColdStep("PROBE", "OBSERVED", probe.source_time, (probe.evidence_id,)) if probe
                 else ColdStep("PROBE", "MISSING", None))
    missing = tuple(s.step for s in steps if s.state == "MISSING")

    if contradictory:
        result, claim = "CONTRADICTORY", "CONTRADICTORY"
    elif request is None:
        result, claim = "UNKNOWN", "UNKNOWN"
    elif failed:
        result, claim = "OBSERVED_FAILURE", "OBSERVED"
    elif succeeded:
        result, claim = "OBSERVED_SUCCESS", "OBSERVED"
    elif inferred_timeout:
        result, claim = "OBSERVED_FAILURE", "OBSERVED"
    else:
        result, claim = "UNKNOWN", "UNKNOWN"
    support = {i for s in steps if s.state == "OBSERVED" for i in s.evidence_ids}
    links = [ColdLink(i, "SUPPORT") for i in sorted(support, key=str)]
    links += [ColdLink(i, _use(reason), reason) for i, reason in reasons.items() if i not in support
              and any(e.evidence_id == i for e in group)]
    links += [ColdLink(e.evidence_id, "CONTEXT", e.record_kind) for e in group
              if e.evidence_id not in support and e.evidence_id not in reasons]
    anchor = request or min(group, key=lambda e: (e.source_time, str(e.evidence_id)))
    limitation_parts = []
    if missing:
        limitation_parts.append("Not observed: " + ", ".join(missing) + ".")
    if contradictory:
        limitation_parts.append("Contradictory start results block a start-response claim.")
    if result == "OBSERVED_FAILURE" and not gate.permitted:
        limitation_parts.append("The source classification does not permit a Finding.")
    return ColdStartChain(correlation, policy.generator_asset_id, anchor.evidence_id, anchor.source_time,
                          tuple(steps), missing, result, claim, policy.start_timeout_minutes,
                          result == "OBSERVED_FAILURE" and gate.permitted, tuple(links),
                          " ".join(limitation_parts) or None)


def assess_start_response(evidence: Iterable[ColdEvidence], window: ColdWindow, policy: ColdStartPolicy,
                          source_gate: SourceGate) -> ColdAssessment:
    """`cold-start-response/1`: one chain per accepted outage correlation that carries generator start events."""
    rows = _known(evidence, window)
    groups: dict[str, list[ColdEvidence]] = {}
    for e in rows:
        if e.family == "EVENT" and e.correlation_id is not None:
            groups.setdefault(e.correlation_id, []).append(e)
    probe_rows = [e for e in rows if e.role == PROBE_ROLE and e.family == "MEASUREMENT"
                  and _exclusion(e, PROBE_ROLE, policy.probe_asset_id) is None and isinstance(e.value, Decimal)]
    chains = tuple(
        _chain(c, g, rows, policy, window, source_gate, probe_rows)
        for c, g in sorted(groups.items(), key=lambda kv: (kv[1][0].source_time, kv[0]))
        if any(e.record_kind in ("START_REQUEST", "START_RESULT") for e in g)
    )
    if not chains:
        state, claim = "UNKNOWN", "UNKNOWN"
    elif any(c.result == "CONTRADICTORY" for c in chains):
        state, claim = "CONTRADICTORY", "CONTRADICTORY"
    else:
        state = chains[-1].result
        claim = chains[-1].claim_level
    links = tuple(link for c in chains for link in c.links)
    return ColdAssessment(START_RESPONSE_ANALYTIC, MODEL_VERSION, window, state, claim, 0, 0, Decimal(0), (), (),
                          chains, links, tuple(c.limitation for c in chains if c.limitation))


# --- selected inputs and the persisted result document (W2-03 commit 3) ------------------------------------


class ColdConfigurationRefused(Exception):
    """The effective cold configuration cannot be selected exactly (missing, duplicate or overlapping Foundation,
    `cold-roles-1` binding, policy or calibration); no claim is computed (fail closed)."""


@dataclass(frozen=True)
class ColdInputs:
    """One Site/window/cutoff selection: accepted records, effective policies, S4-05 gate and configuration IDs."""

    tenant_id: UUID
    site_id: UUID
    window: ColdWindow
    evidence: tuple[ColdEvidence, ...]
    policy: ColdPolicy
    start_policy: ColdStartPolicy
    gate: SourceGate
    foundation_revision_ids: tuple[UUID, ...]
    binding_revision_ids: tuple[UUID, ...]

    def basis(self, analytic_id: str) -> str:
        return basis_sha256(analytic_id=analytic_id, model_version=MODEL_VERSION, tenant_id=self.tenant_id,
                            site_id=self.site_id, window=self.window,
                            foundation_revision_ids=self.foundation_revision_ids,
                            binding_revision_ids=self.binding_revision_ids, source_gate=self.gate,
                            records=self.evidence)


def assess_all(inputs: ColdInputs) -> tuple[ColdAssessment, ColdAssessment]:
    """Both analytics over one selection: (`cold-excursion/1`, `cold-start-response/1`)."""
    return (assess_excursion(inputs.evidence, inputs.window, inputs.policy, inputs.gate),
            assess_start_response(inputs.evidence, inputs.window, inputs.start_policy, inputs.gate))


def plain(value):
    """JSON form of a result value: decimal strings, UTC instants, lowercase UUID text."""
    if isinstance(value, Decimal):
        text_value = format(value.normalize(), "f")
        return "0" if text_value in ("-0", "") else text_value
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


def assessment_document(assessment: ColdAssessment, *, policy: ColdPolicy | ColdStartPolicy,
                        gate: SourceGate) -> dict:
    """The persisted `assessment_revision.result`: the pure fields, its episodes/chains, policy and gate."""
    document = plain(assessment)
    document["policy"] = plain(policy)
    document["source_gate"] = {**gate.basis(), "permitted": gate.permitted}
    return document
