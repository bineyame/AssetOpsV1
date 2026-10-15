"""Public report cohort selection for one window (pure; S3-01 phase 2).

A cohort is a set of public report streams (gateway, registered source,
sequence epoch). The rule (dispatch-3 table, "Cohort"):

- A source whose readings in the window come from two or more sequence
  epochs has no coherent default choice: the result is AMBIGUOUS and names each
  epoch as an alternative. This holds whether the epochs' source-time spans
  overlap (two runs) or follow one another (a reprovisioned gateway, or a
  labelled fault fixture placed beside ordinary evidence): central evidence
  carries no attested marker that would tell these apart, so the default never
  blends epochs (phase-2 review F3, `D-2026-10-11-s3-phase-2-selection-and-read`).
  An explicit selection may still name one or more non-overlapping epochs.
- An explicit selection uses exactly the named members; readings of other
  members are excluded, never blended.
- Inside a selected member, each channel (role, asset) must be one series:
  a reading sequenced after another but placed earlier in source time
  (`SEQUENCE_ORDER_INVERTED`) or two readings at one channel-time
  (`REPORTS_OVERLAP`) mark that span unusable. Neither sequence ranges nor
  receipt order is used to split or pick between them.
- cohort-4 (LR-01, `D-2026-10-15-lr01-source-time-cohort`, Follow-up M1): where one
  effective clock attestation for the stream (source, epoch) covers both readings'
  measurement intervals, source time orders them and a later-sequenced reading
  placed earlier is a late arrival, not an inversion. Inside that attested series,
  placement-uncertainty intervals (`placed_at` +/- the attested UTC error) that
  overlap, or measurement intervals that genuinely overlap (touching ends do not),
  stay `REPORTS_OVERLAP`; no winner is chosen. A reading with no attestation, outside
  validity, straddling or claimed by two attestations, under simulated proof while not
  simulated, or a pair under two different attestations (an unproved clock step), keeps
  the sequence rule. Each refused span names its clock reason and attestation versions,
  and the selection pins the attestations it used (`clock_basis`). Epochs are never
  merged by source time.

No epoch name, manifest label or Lab run identifier is consulted.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from assetops_backend.analytics.assessment_inputs import (
    AcceptedReading,
    CohortLimit,
    CohortMember,
    CohortSelection,
    Window,
)
from assetops_backend.analytics.clock_attestation import MAX_UTC_ERROR, PROOF_SIMULATED, ClockAttestation


def _overlaps(a: tuple[datetime, datetime], b: tuple[datetime, datetime]) -> bool:
    return a[0] <= b[1] and b[0] <= a[1]


def select_cohort(readings: tuple[AcceptedReading, ...], window: Window,
                  explicit: tuple[CohortMember, ...] | None = None, attestations=()) -> CohortSelection:
    """`readings` cover the read range (window plus bracket). Only streams with a reading inside
    the window itself are candidates; a stream seen only in the bracket is not pulled in. `attestations`
    are the clock attestations effective at the knowledge cutoff (`clock_attestation.effective_as_of`)."""
    present = sorted({r.member for r in readings if window.contains(r.placed_at)})
    if explicit is not None:
        chosen = tuple(sorted(set(explicit)))
        unknown = [m for m in chosen if m not in present]
        reason = None if not unknown else (
            "explicit cohort names stream(s) with no accepted reading in the window: "
            + ", ".join(f"{m.source_id}@{m.sequence_epoch}" for m in unknown))
        mine = tuple(r for r in readings if r.member in set(chosen))
        others = tuple(m for m in present if m not in set(chosen))
        clash = _clashing(mine)
        if clash:
            return CohortSelection("AMBIGUOUS", (), alternatives=tuple(sorted(clash)),
                                   reason="the explicit cohort names overlapping epochs of one source", rules=RULES)
        return CohortSelection("SELECTED_EXPLICIT", chosen, alternatives=others,
                               limits=series_limits(mine, attestations), reason=reason, rules=RULES,
                               clock_basis=clock_basis(mine, attestations))
    if not present:
        return CohortSelection("EMPTY", (), reason="no accepted reading in the window", rules=RULES)
    # Streams seen only in the bracket are not candidates and are not named: naming them would
    # change this window's basis whenever a neighbour day receives evidence.
    readings = tuple(r for r in readings if r.member in set(present))
    clashing = _clashing(readings)
    if clashing:
        names = sorted(clashing)
        return CohortSelection(
            "AMBIGUOUS", (), alternatives=tuple(names),
            reason=("a source reports the same time span under more than one sequence epoch ("
                    + ", ".join(f"{m.source_id}@{m.sequence_epoch}" for m in names)
                    + "); no coherent default cohort; select one explicitly"), rules=RULES)
    successive = _multi_epoch(present)
    if successive:
        names = sorted(successive)
        return CohortSelection(
            "AMBIGUOUS", (), alternatives=tuple(names),
            reason=("a source reports in this window under more than one sequence epoch ("
                    + ", ".join(f"{m.source_id}@{m.sequence_epoch}" for m in names)
                    + "); central evidence does not attest that they are one physical stream, so the "
                      "default cohort does not blend them; select one explicitly"), rules=RULES)
    return CohortSelection("SELECTED_UNIQUE", tuple(present), limits=series_limits(readings, attestations),
                           rules=RULES, clock_basis=clock_basis(readings, attestations))


def _multi_epoch(members: list[CohortMember]) -> set[CohortMember]:
    """Members of a source (same gateway and source) present under two or more epochs."""
    by_source: dict[tuple, list[CohortMember]] = defaultdict(list)
    for m in members:
        by_source[(m.gateway_id, m.source_id)].append(m)
    return {m for group in by_source.values() if len(group) > 1 for m in group}


def _clashing(readings: tuple[AcceptedReading, ...]) -> set[CohortMember]:
    """Members of one source (same gateway and source) whose source-time spans overlap."""
    spans: dict[CohortMember, tuple[datetime, datetime]] = {}
    for r in readings:
        lo, hi = spans.get(r.member, (r.placed_at, r.placed_at))
        spans[r.member] = (min(lo, r.placed_at), max(hi, r.placed_at))
    by_source: dict[tuple, list[CohortMember]] = defaultdict(list)
    for m in sorted(spans):
        by_source[(m.gateway_id, m.source_id)].append(m)
    clashing: set[CohortMember] = set()
    for members in by_source.values():
        for i, a in enumerate(members):
            for b in members[i + 1:]:
                if _overlaps(spans[a], spans[b]):
                    clashing.update((a, b))
    return clashing


#: Cohort rule version persisted in every selection payload (LR-01, `D-2026-10-15-lr01-source-time-cohort`).
RULES = "cohort-4"
ATTESTED = "ATTESTED"
_UNCOVERED = "UNCOVERED"


@dataclass(frozen=True)
class _Clock:
    """A reading's clock basis: the one attestation that orders it, or why none does."""

    attestation: ClockAttestation | None
    reason: str  # ATTESTED | NO_ATTESTATION | OUTSIDE_VALIDITY | SPANS_ATTESTATIONS | CONFLICTING_ATTESTATIONS
    #             | SIMULATED_PROOF_FOR_LIVE_SOURCE | ERROR_ABOVE_CEILING
    refs: tuple[str, ...] = ()

    @property
    def key(self) -> str:
        return _UNCOVERED if self.attestation is None else str(self.attestation.attestation_id)


def _measured(r: AcceptedReading) -> tuple[datetime, datetime]:
    """The reading's measurement interval, or its instant."""
    return (r.interval_start or r.source_time, r.placed_at)


def _streams(attestations) -> dict[tuple[UUID, str], list[ClockAttestation]]:
    out: dict[tuple[UUID, str], list[ClockAttestation]] = defaultdict(list)
    for a in attestations:
        out[(a.source_id, a.sequence_epoch)].append(a)
    return out


def _clock(r: AcceptedReading, mine: list[ClockAttestation]) -> _Clock:
    if not mine:
        return _Clock(None, "NO_ATTESTATION")
    start, end = _measured(r)
    touching = [a for a in mine if a.touches(start, end)]
    covering = [a for a in touching if a.covers(start, end)]
    refs = tuple(sorted(a.ref for a in touching))
    if len(touching) > 1:
        # Two attestations claim this reading's time (overlapping proof) or it straddles their boundary.
        return _Clock(None, "CONFLICTING_ATTESTATIONS" if len(covering) > 1 else "SPANS_ATTESTATIONS", refs)
    if not covering:
        return _Clock(None, "SPANS_ATTESTATIONS" if touching else "OUTSIDE_VALIDITY", refs)
    a = covering[0]
    if a.proof_class == PROOF_SIMULATED and r.source_mode != "SIMULATED":
        return _Clock(None, "SIMULATED_PROOF_FOR_LIVE_SOURCE", refs)
    if a.max_utc_error > MAX_UTC_ERROR:
        return _Clock(None, "ERROR_ABOVE_CEILING", refs)
    return _Clock(a, ATTESTED, refs)


def _pair(clocks: list[_Clock]) -> tuple[str, tuple[str, ...]]:
    """The clock statement of a refused span: why source time could not settle it."""
    refs = tuple(sorted({x for c in clocks for x in c.refs}))
    if all(c.attestation is not None for c in clocks):
        keys = {c.key for c in clocks}
        return (ATTESTED if len(keys) == 1 else "CLOCK_STEP_UNPROVED"), refs
    return "+".join(sorted({c.reason for c in clocks if c.attestation is None})), refs


def clock_basis(readings: tuple[AcceptedReading, ...], attestations) -> tuple[ClockAttestation, ...]:
    """The effective attestations that touch at least one of these readings' measurement intervals."""
    by_stream = _streams(attestations)
    used = {a.event_id: a for r in readings for a in by_stream.get((r.source_id, r.sequence_epoch), ())
            if a.touches(*_measured(r))}
    return tuple(sorted(used.values(), key=lambda a: (str(a.attestation_id), a.version)))


def series_limits(readings: tuple[AcceptedReading, ...], attestations=()) -> tuple[CohortLimit, ...]:
    """Spans where a member's channel is not one public series (cohort-4, see module docstring)."""
    by_stream = _streams(attestations)
    channels: dict[tuple, list[AcceptedReading]] = defaultdict(list)
    for r in readings:
        channels[(r.member, r.role, str(r.asset_id))].append(r)
    limits: list[CohortLimit] = []
    seen: set[tuple] = set()

    def add(kind, role, asset, member, lo, hi, rows, clocks) -> None:
        ids = tuple(sorted({str(x.evidence_id) for x in rows}))
        if (kind, lo, hi, ids) in seen:
            return
        seen.add((kind, lo, hi, ids))
        clock, refs = _pair(clocks)
        limits.append(CohortLimit(kind, role, asset, member, lo, hi, ids, clock, refs))

    for (member, role, asset), rows in sorted(channels.items(), key=lambda kv: str(kv[0])):
        mine = by_stream.get((member.source_id, member.sequence_epoch), [])
        clock = {r.evidence_id: _clock(r, mine) for r in rows}
        # Two readings at one channel-time are never one series, attested or not.
        at_time: dict[datetime, list[AcceptedReading]] = defaultdict(list)
        for r in rows:
            at_time[r.placed_at].append(r)
        for when, same in sorted(at_time.items()):
            if len(same) > 1:
                add("REPORTS_OVERLAP", role, asset, member, when, when, same, [clock[x.evidence_id] for x in same])
        # Inside one attested series: overlapping placement-uncertainty intervals (placed_at +/- error) or a
        # genuine measurement-interval overlap stay ambiguous; intervals that only touch do not overlap.
        groups: dict[str, list[AcceptedReading]] = defaultdict(list)
        for r in rows:
            if clock[r.evidence_id].attestation is not None:
                groups[clock[r.evidence_id].key].append(r)
        for group in groups.values():
            error = clock[group[0].evidence_id].attestation.max_utc_error
            placed = sorted(group, key=lambda r: (r.placed_at, str(r.evidence_id)))
            for a, b in zip(placed, placed[1:]):
                if b.placed_at - a.placed_at <= 2 * error:
                    add("REPORTS_OVERLAP", role, asset, member, a.placed_at, b.placed_at, (a, b),
                        [clock[a.evidence_id], clock[b.evidence_id]])
            widest: AcceptedReading | None = None
            for r in sorted(group, key=lambda r: (_measured(r), str(r.evidence_id))):
                if widest is not None and _measured(r)[0] < _measured(widest)[1]:
                    add("REPORTS_OVERLAP", role, asset, member, _measured(r)[0],
                        min(_measured(r)[1], _measured(widest)[1]), (widest, r),
                        [clock[widest.evidence_id], clock[r.evidence_id]])
                if widest is None or _measured(r)[1] > _measured(widest)[1]:
                    widest = r
        # Sequence order against source-time order. A later-sequenced reading placed earlier is a late arrival,
        # not an inversion, only when one attestation orders both; any other pair keeps the inversion.
        latest: dict[str, AcceptedReading] = {}
        for r in sorted(rows, key=lambda r: r.sequence):
            mine_key = clock[r.evidence_id].key
            rivals = [q for k, q in latest.items() if mine_key == _UNCOVERED or k != mine_key]
            q = max(rivals, key=lambda q: q.placed_at, default=None)
            if q is not None and r.placed_at < q.placed_at:
                add("SEQUENCE_ORDER_INVERTED", role, asset, member, r.placed_at, q.placed_at, (r, q),
                    [clock[r.evidence_id], clock[q.evidence_id]])
            held = latest.get(mine_key)
            if held is None or r.placed_at > held.placed_at:
                latest[mine_key] = r
    return tuple(limits)
