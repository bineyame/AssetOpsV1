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

No epoch name, manifest label or Lab run identifier is consulted.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from assetops_backend.analytics.assessment_inputs import (
    AcceptedReading,
    CohortLimit,
    CohortMember,
    CohortSelection,
    Window,
)


def _overlaps(a: tuple[datetime, datetime], b: tuple[datetime, datetime]) -> bool:
    return a[0] <= b[1] and b[0] <= a[1]


def select_cohort(readings: tuple[AcceptedReading, ...], window: Window,
                  explicit: tuple[CohortMember, ...] | None = None) -> CohortSelection:
    """`readings` cover the read range (window plus bracket). Only streams with a reading inside
    the window itself are candidates; a stream seen only in the bracket is not pulled in."""
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
                                   reason="the explicit cohort names overlapping epochs of one source")
        return CohortSelection("SELECTED_EXPLICIT", chosen, alternatives=others,
                               limits=series_limits(mine), reason=reason)
    if not present:
        return CohortSelection("EMPTY", (), reason="no accepted reading in the window")
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
                    + "); no coherent default cohort; select one explicitly"))
    successive = _multi_epoch(present)
    if successive:
        names = sorted(successive)
        return CohortSelection(
            "AMBIGUOUS", (), alternatives=tuple(names),
            reason=("a source reports in this window under more than one sequence epoch ("
                    + ", ".join(f"{m.source_id}@{m.sequence_epoch}" for m in names)
                    + "); central evidence does not attest that they are one physical stream, so the "
                      "default cohort does not blend them; select one explicitly"))
    return CohortSelection("SELECTED_UNIQUE", tuple(present), limits=series_limits(readings))


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


def series_limits(readings: tuple[AcceptedReading, ...]) -> tuple[CohortLimit, ...]:
    """Spans where a member's channel is not one public series (see module docstring)."""
    channels: dict[tuple, list[AcceptedReading]] = defaultdict(list)
    for r in readings:
        channels[(r.member, r.role, str(r.asset_id))].append(r)
    limits: list[CohortLimit] = []
    for (member, role, asset), rows in sorted(channels.items(), key=lambda kv: str(kv[0])):
        at_time: dict[datetime, list[AcceptedReading]] = defaultdict(list)
        for r in rows:
            at_time[r.placed_at].append(r)
        for when, same in sorted(at_time.items()):
            if len(same) > 1:
                limits.append(CohortLimit("REPORTS_OVERLAP", role, asset, member, when, when,
                                          tuple(sorted(str(x.evidence_id) for x in same))))
        ordered = sorted(rows, key=lambda r: r.sequence)
        latest: AcceptedReading | None = None
        for r in ordered:
            if latest is not None and r.placed_at < latest.placed_at:
                limits.append(CohortLimit("SEQUENCE_ORDER_INVERTED", role, asset, member, r.placed_at,
                                          latest.placed_at,
                                          tuple(sorted((str(r.evidence_id), str(latest.evidence_id))))))
            if latest is None or r.placed_at > latest.placed_at:
                latest = r
    return tuple(limits)
