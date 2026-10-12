"""Candidate generator-support episode matcher (S4-01, `finding-episode-1`).

Pure: no I/O. `plan` takes the selected dispatch windows of one Site (with
their derived read status) and the persisted episodes, and returns the
Finding/FindingRevision writes that `D-2026-10-12-finding-episode-and-revisions`
requires. The caller persists them in one transaction; `plan` is a function of
its inputs, and every write carries a basis digest, so a retry over the same
selected basis plans nothing new.

Rules (decision "Identity and continuity" and "Revisions and lifecycle"):

- Only CURRENT windows selected under the current model count. A window that
  is STALE, FAILED, PENDING or unassessed never creates, extends or closes an
  episode; an episode or candidate cluster that reaches one is left unchanged.
- A support cluster is a run of CANDIDATE segments of one generator. Two spans
  join when they overlap, or when the gap is at most 20 minutes and every
  segment inside the gap is observed and Necessary, or Indeterminate only for
  a modelling reason (dispatch-3.1 `_NOT_EVIDENCE_GAPS`) (a stop between two intervals
  also needs observed OFF bounds on both sides). An INDETERMINATE or
  unobserved segment (contradiction, ambiguity, missing data) never bridges.
- A cluster overlapping no episode opens a new Finding, linked by
  `recurs_after_finding_id` to the latest earlier episode of that generator
  when an observed OFF report separates them (an unobserved gap links nothing).
- One cluster over several episodes merges them: the earliest anchor (then
  UUID) stays canonical and the others record MERGED_INTO.
- One episode over several clusters splits: it keeps the cluster containing
  its immutable anchor; each other cluster opens a Finding `split_from` it.
- An episode with no cluster becomes UNCONFIRMED when the current basis over
  it is Indeterminate, and NO_LONGER_SUPPORTED when it is complete and has no
  Candidate (never "repaired" or "saved").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from fractions import Fraction
from typing import Any
from uuid import uuid4

from assetops_backend.analytics.assessment_inputs import iso, sha256_json
from assetops_backend.analytics.dispatch import CANDIDATE, INDETERMINATE, NECESSARY
from assetops_backend.analytics.dispatch_v3 import _NOT_EVIDENCE_GAPS, CONTINUITY_TOLERANCE

MATCHER_VERSION = "finding-episode-1"
DOMAIN = "mini_grid"
MECHANISM = "GENERATOR_SUPPORT_CANDIDATE"
CURRENT = "CURRENT"

SUPPORTED = "SUPPORTED"
UNCONFIRMED = "UNCONFIRMED"
NO_LONGER_SUPPORTED = "NO_LONGER_SUPPORTED"
MERGED = "MERGED"

TITLES = {
    SUPPORTED: "Generator support merits review: bounded candidate avoidable running",
    UNCONFIRMED: "Generator support candidate unconfirmed by the current assessment",
    NO_LONGER_SUPPORTED: "Generator support candidate no longer supported (not a repair or a saving)",
    MERGED: "Generator support episode merged into an earlier episode",
}


def _at(text: str | None) -> datetime | None:
    return None if text is None else datetime.fromisoformat(text.replace("Z", "+00:00"))


def _minutes(a: datetime, b: datetime) -> Fraction:
    return Fraction(int((b - a).total_seconds()), 60)


def _num(x: Fraction) -> str:
    return format(float(x), ".4f")


@dataclass(frozen=True)
class Seg:
    start: datetime
    end: datetime
    observed: bool
    classification: str
    evidence_ids: tuple[str, ...]
    missing: tuple[str, ...] = ()

    @property
    def coherent(self) -> bool:
        """Observed, and Necessary or Indeterminate only for a modelling reason (transition, minimum
        runtime, headroom) - never for missing, poor-quality, contradictory or ambiguous evidence."""
        return self.observed and (self.classification == NECESSARY or (
            self.classification == INDETERMINATE and bool(self.missing)
            and all(m.startswith(_NOT_EVIDENCE_GAPS) for m in self.missing)))


@dataclass(frozen=True)
class IntervalBasis:
    revision_id: str
    run_id: str
    asset: str
    claim_level: str
    first_on: datetime
    off_before: datetime | None
    off_after: datetime | None
    segments: tuple[Seg, ...]
    limitations: tuple[str, ...]

    @staticmethod
    def from_revision(rev: dict[str, Any]) -> "IntervalBasis":
        result = rev["result"] or {}
        interval = result.get("interval") or {}
        segments = tuple(Seg(_at(s["start"]), _at(s["end"]), bool(s.get("observed")), s["classification"],
                             tuple(sorted(str(e) for e in s.get("evidence_ids") or ())),
                             tuple(s.get("missing") or ()))
                         for s in result.get("segments") or ())
        return IntervalBasis(str(rev["id"]), str(rev["analytic_run_id"]), str(result.get("generator_asset_id")),
                             rev["claim_level"], _at(interval.get("first_on")), _at(interval.get("off_before")),
                             _at(interval.get("off_after")), segments, tuple(result.get("limitations") or ()))


@dataclass(frozen=True)
class WindowBasis:
    start: datetime
    end: datetime
    status: str
    model_version: str | None
    run_id: str | None
    input_sha256: str | None
    cohort_sha256: str | None
    window_revision_id: str | None
    window_claim: str | None
    intervals: tuple[IntervalBasis, ...]


@dataclass(frozen=True)
class Episode:
    """A persisted Finding with its latest revision."""
    finding_id: str
    asset: str
    anchor_start: datetime
    lifecycle: str
    episode_start: datetime
    episode_end: datetime
    basis_sha256: str
    model_version: str


@dataclass
class Write:
    finding_id: str
    transition: str
    lifecycle: str
    claim_level: str
    model_version: str
    primary_revision_id: str
    primary_run_id: str
    window_revision_id: str | None
    episode_start: datetime
    episode_end: datetime
    minutes: dict[str, Fraction]
    claim: dict[str, Any]
    limitations: list[str]
    assessments: list[tuple[str, str, str, bool]]  # (assessment revision, run, scope, primary)
    cited_evidence_ids: list[str]
    input_sha256s: list[str]
    basis_sha256: str
    new_finding: dict[str, Any] | None = None
    merged_into: str | None = None
    asset: str = ""


@dataclass
class _Cluster:
    asset: str
    spans: list[tuple[Seg, IntervalBasis]] = field(default_factory=list)

    @property
    def start(self) -> datetime:
        return self.spans[0][0].start

    @property
    def end(self) -> datetime:
        return max(s.end for s, _ in self.spans)


class _Site:
    def __init__(self, windows: list[WindowBasis], model_version: str) -> None:
        self.windows = sorted(windows, key=lambda w: w.start)
        self.model = model_version
        self.usable = [w for w in self.windows if w.status == CURRENT and w.model_version == model_version]
        self.window_of: dict[str, WindowBasis] = {i.revision_id: w for w in self.usable for i in w.intervals}

    def intervals(self, asset: str) -> list[IntervalBasis]:
        return [i for w in self.usable for i in w.intervals if i.asset == asset]

    def covered(self, lo: datetime, hi: datetime) -> bool:
        """Every instant of [lo, hi] lies in a usable window."""
        t = lo
        while True:
            w = next((w for w in self.usable if w.start <= t < w.end), None)
            if w is None:
                return False
            if hi < w.end:
                return True
            t = w.end

    def margin_ok(self, lo: datetime, hi: datetime) -> bool:
        """No selected window touching [lo - 20 min, hi + 20 min] is unusable."""
        a, b = lo - CONTINUITY_TOLERANCE, hi + CONTINUITY_TOLERANCE
        return all(w in self.usable for w in self.windows if w.start <= b and a < w.end)

    def windows_over(self, lo: datetime, hi: datetime) -> list[WindowBasis]:
        return [w for w in self.usable if w.start <= hi and lo < w.end]


def _segments_in(intervals: list[IntervalBasis], lo: datetime, hi: datetime) -> list[tuple[Seg, IntervalBasis]]:
    return [(s, i) for i in intervals for s in i.segments if s.start < hi and lo < s.end]


def _bridges(site: _Site, asset: str, a: tuple[Seg, IntervalBasis], b: tuple[Seg, IntervalBasis]) -> bool:
    lo, hi = a[0].end, b[0].start
    if hi <= lo:
        return True
    if hi - lo > CONTINUITY_TOLERANCE or not site.covered(lo, hi):
        return False
    inside = _segments_in(site.intervals(asset), lo, hi)
    if any(not s.coherent for s, _ in inside if s.classification != CANDIDATE):
        return False
    if a[1].revision_id != b[1].revision_id and (a[1].off_after is None or b[1].off_before is None):
        return False
    return True


def _clusters(site: _Site) -> list[_Cluster]:
    out: list[_Cluster] = []
    for asset in sorted({i.asset for w in site.usable for i in w.intervals}):
        spans = sorted(((s, i) for i in site.intervals(asset) for s in i.segments if s.classification == CANDIDATE),
                       key=lambda x: (x[0].start, x[0].end))
        current: _Cluster | None = None
        for span in spans:
            if current is not None and _bridges(site, asset, max(current.spans, key=lambda x: x[0].end), span):
                current.spans.append(span)
                continue
            current = _Cluster(asset, [span])
            out.append(current)
    return out


def _overlaps(c: _Cluster, e: Episode) -> bool:
    return c.asset == e.asset and c.start <= e.episode_end and e.episode_start <= c.end


def _support_write(site: _Site, finding_id: str, cluster: _Cluster, transition: str, *,
                   anchor: datetime | None, extra: dict[str, Any]) -> Write:
    intervals = {i.revision_id: i for _, i in cluster.spans}
    start, end = cluster.start, cluster.end
    anchored = next((i for s, i in cluster.spans if anchor is not None and s.start <= anchor <= s.end), None)
    primary = anchored or cluster.spans[0][1]
    windows = {site.window_of[r].window_revision_id: site.window_of[r] for r in intervals}
    segs = _segments_in(list(intervals.values()), start, end) or [(s, i) for s, i in cluster.spans]
    minutes = {c: sum((_minutes(max(s.start, start), min(s.end, end)) for s, _ in segs if s.classification == c),
                      Fraction(0)) for c in (CANDIDATE, NECESSARY, INDETERMINATE)}
    minutes[CANDIDATE] = sum((_minutes(s.start, s.end) for s, _ in cluster.spans), Fraction(0))
    cited = sorted({e for s, _ in cluster.spans for e in s.evidence_ids})
    limits = sorted({x for i in intervals.values() for x in i.limitations})
    if anchor is not None and anchored is None:
        limits.append("ANCHOR_OUTSIDE_SUPPORT: the episode's anchor is no longer inside a Candidate segment")
    claim = {
        "schema_version": 1,
        "statement": "Bounded candidate avoidable generator running: only the Candidate segments are counted; "
                     "Necessary and Indeterminate portions stay separate and the whole interval is not avoidable.",
        "candidate_spans": [{"start": iso(s.start), "end": iso(s.end), "minutes": _num(_minutes(s.start, s.end)),
                             "assessment_revision_id": i.revision_id, "evidence_ids": list(s.evidence_ids)}
                            for s, i in cluster.spans],
        "other_portions": [{"start": iso(max(s.start, start)), "end": iso(min(s.end, end)),
                            "classification": s.classification, "observed": s.observed,
                            "assessment_revision_id": i.revision_id}
                           for s, i in segs if s.classification != CANDIDATE],
        **extra,
    }
    return _write(site, finding_id, transition, SUPPORTED, CANDIDATE, primary, list(intervals.values()),
                  list(windows.values()), start, end, minutes, claim, limits, cited)


def _write(site: _Site, finding_id: str, transition: str, lifecycle: str, claim_level: str,
           primary: IntervalBasis | WindowBasis, intervals: list[IntervalBasis], windows: list[WindowBasis],
           start: datetime, end: datetime, minutes: dict[str, Fraction], claim: dict[str, Any],
           limits: list[str], cited: list[str]) -> Write:
    if isinstance(primary, IntervalBasis):
        primary_id, primary_run = primary.revision_id, primary.run_id
        window_rev = site.window_of[primary.revision_id].window_revision_id
    else:
        primary_id, primary_run, window_rev = primary.window_revision_id, primary.run_id, primary.window_revision_id
    assessments = [(i.revision_id, i.run_id, "INTERVAL", i.revision_id == primary_id) for i in intervals]
    assessments += [(w.window_revision_id, w.run_id, "WINDOW", w.window_revision_id == primary_id)
                    for w in windows if w.window_revision_id]
    assessments = sorted(set(assessments))
    inputs = sorted({w.input_sha256 for w in windows if w.input_sha256})
    # The basis is the claim and its interval revisions. The selected window revision is cited, but a
    # reassessment elsewhere in the same UTC day that leaves this episode's intervals unchanged is not
    # a new Finding basis.
    basis = sha256_json({"matcher": MATCHER_VERSION, "model": site.model, "lifecycle": lifecycle,
                         "intervals": sorted(i.revision_id for i in intervals), "bounds": [iso(start), iso(end)],
                         "minutes": {k: _num(v) for k, v in minutes.items()}, "cited": cited})
    return Write(finding_id, transition, lifecycle, claim_level, site.model, primary_id, primary_run, window_rev,
                 start, end, minutes, claim, limits, assessments, cited, inputs, basis)


def _unsupported_write(site: _Site, e: Episode) -> Write | None:
    """UNCONFIRMED or NO_LONGER_SUPPORTED for an episode no current cluster covers; None when not decidable."""
    if not site.covered(e.episode_start, e.episode_end) or not site.margin_ok(e.episode_start, e.episode_end):
        return None
    intervals = [i for i in site.intervals(e.asset)
                 if any(s.start <= e.episode_end and e.episode_start <= s.end for s in i.segments)]
    windows = site.windows_over(e.episode_start, e.episode_end)
    segs = _segments_in(intervals, e.episode_start, e.episode_end)
    indeterminate = (any(s.classification == INDETERMINATE or not s.observed for s, _ in segs)
                     or any(i.claim_level == INDETERMINATE for i in intervals)
                     or any(w.window_claim == "INDETERMINATE" for w in windows))
    lifecycle = UNCONFIRMED if indeterminate else NO_LONGER_SUPPORTED
    if lifecycle == NO_LONGER_SUPPORTED and e.lifecycle == NO_LONGER_SUPPORTED:
        return None
    minutes = {c: sum((_minutes(max(s.start, e.episode_start), min(s.end, e.episode_end))
                       for s, _ in segs if s.classification == c), Fraction(0))
               for c in (CANDIDATE, NECESSARY, INDETERMINATE)}
    primary: IntervalBasis | WindowBasis = intervals[0] if intervals else windows[0]
    if isinstance(primary, WindowBasis) and primary.window_revision_id is None:
        return None
    claim = {
        "schema_version": 1,
        "statement": ("The current assessment cannot confirm the candidate support (Indeterminate); the earlier "
                      "revision stays inspectable." if indeterminate else
                      "A complete current assessment of this episode has no Candidate segment. This closes the "
                      "candidate claim only; it does not say the generator was repaired or that money was saved."),
        "candidate_spans": [],
        "other_portions": [{"start": iso(max(s.start, e.episode_start)), "end": iso(min(s.end, e.episode_end)),
                            "classification": s.classification, "observed": s.observed,
                            "assessment_revision_id": i.revision_id} for s, i in segs],
        "window_claims": sorted({w.window_claim for w in windows if w.window_claim}),
    }
    limits = sorted({x for i in intervals for x in i.limitations})
    if not intervals:
        limits.append("NO_INTERVAL: no current generator interval overlaps the episode bounds")
    cited = sorted({x for s, _ in segs for x in s.evidence_ids})
    return _write(site, e.finding_id, lifecycle, lifecycle, INDETERMINATE if indeterminate else NECESSARY,
                  primary, intervals, windows, e.episode_start, e.episode_end, minutes, claim, limits, cited)


def _new(site: _Site, cluster: _Cluster, *, recurs_after: Episode | None, split_from: str | None) -> Write:
    finding_id = str(uuid4())
    gap = None if recurs_after is None else _num(_minutes(recurs_after.episode_end, cluster.start))
    extra = {"recurs_after_finding_id": None if recurs_after is None else recurs_after.finding_id,
             "separation_minutes": gap, "split_from_finding_id": split_from}
    w = _support_write(site, finding_id, cluster, "OPENED", anchor=cluster.start, extra=extra)
    anchor_rev = cluster.spans[0][1]
    w.new_finding = {
        "finding_key": f"gen-support:{cluster.asset}:{cluster.start.strftime('%Y%m%dT%H%M%SZ')}:{finding_id[:8]}",
        "anchor_start": cluster.start, "anchor_assessment_revision_id": anchor_rev.revision_id,
        "cohort_sha256": site.window_of[anchor_rev.revision_id].cohort_sha256,
        "recurs_after_finding_id": None if recurs_after is None else recurs_after.finding_id,
        "split_from_finding_id": split_from,
    }
    w.asset = cluster.asset
    return w


def plan(windows: list[WindowBasis], episodes: list[Episode], model_version: str) -> list[Write]:
    site = _Site(windows, model_version)
    live = [e for e in episodes if e.lifecycle != MERGED]
    clusters = _clusters(site)
    writes: list[Write] = []
    # connected components of clusters and episodes by overlap
    parent: dict[int, int] = {}

    def find(x: int) -> int:
        while parent.setdefault(x, x) != x:
            x = parent[x]
        return x

    for ci, c in enumerate(clusters):
        find(ci)
        for ei, e in enumerate(live):
            if _overlaps(c, e):
                parent[find(ci)] = find(len(clusters) + ei)
    for ei in range(len(live)):
        find(len(clusters) + ei)
    groups: dict[int, tuple[list[_Cluster], list[Episode]]] = {}
    for ci, c in enumerate(clusters):
        groups.setdefault(find(ci), ([], []))[0].append(c)
    for ei, e in enumerate(live):
        groups.setdefault(find(len(clusters) + ei), ([], []))[1].append(e)

    known = list(live)  # for recurrence links, including findings opened in this pass
    for cs, es in sorted(groups.values(), key=lambda g: min([c.start for c in g[0]] + [e.episode_start for e in g[1]])):
        cs.sort(key=lambda c: c.start)
        if any(not site.covered(c.start, c.end) or not site.margin_ok(c.start, c.end) for c in cs) or any(
                not site.covered(e.episode_start, e.episode_end) for e in es if cs):
            continue
        if not cs:
            for e in es:
                w = _unsupported_write(site, e)
                if w is not None and w.basis_sha256 != e.basis_sha256:
                    writes.append(w)
            continue
        if not es:
            for c in cs:
                earlier = [k for k in known if k.asset == c.asset and k.episode_end < c.start]
                prior = max(earlier, key=lambda k: (k.episode_end, k.finding_id), default=None)
                off = c.spans[0][1].off_before
                if prior is not None and (off is None or off < prior.episode_end):
                    prior = None  # separation not evidenced by an observed OFF: no recurrence claim
                w = _new(site, c, recurs_after=prior, split_from=None)
                writes.append(w)
                known.append(Episode(w.finding_id, c.asset, c.start, SUPPORTED, c.start, c.end, w.basis_sha256,
                                     model_version))
            continue
        owners: dict[str, _Cluster] = {}
        owned_by: list[tuple[_Cluster, Episode | None, Episode]] = []
        for c in cs:
            over = sorted((e for e in es if _overlaps(c, e)),
                          key=lambda e: (not (c.start <= e.anchor_start <= c.end), e.anchor_start, e.finding_id))
            owner = next((e for e in over if e.finding_id not in owners), None)
            if owner is not None:
                owners[owner.finding_id] = c
            owned_by.append((c, owner, over[0]))
        split_parents = {first.finding_id for c, owner, first in owned_by if owner is None}
        absorbed: dict[str, list[Episode]] = {}
        for e in es:
            if e.finding_id not in owners:
                c = next(c for c in cs if _overlaps(c, e))
                canonical = next(o for o in es if owners.get(o.finding_id) is c)
                absorbed.setdefault(canonical.finding_id, []).append(e)
        for c, owner, first in owned_by:
            if owner is None:
                w = _new(site, c, recurs_after=None, split_from=first.finding_id)
                writes.append(w)
                continue
            merged = absorbed.get(owner.finding_id, [])
            if merged:
                transition = "MERGED"
            elif owner.finding_id in split_parents:
                transition = "SPLIT"
            elif owner.model_version != model_version:
                transition = "MODEL_REEVALUATED"
            else:
                transition = "SUPPORT_CHANGED"
            extra = {"merged_finding_ids": sorted(m.finding_id for m in merged),
                     "split_into_count": sum(1 for _, o, f in owned_by if o is None and f is owner)}
            w = _support_write(site, owner.finding_id, c, transition, anchor=owner.anchor_start, extra=extra)
            if w.basis_sha256 != owner.basis_sha256 or merged or owner.finding_id in split_parents:
                writes.append(w)
            for m in merged:
                mw = _support_write(site, m.finding_id, c, "MERGED_INTO", anchor=m.anchor_start,
                                    extra={"merged_into_finding_id": owner.finding_id})
                mw.lifecycle, mw.merged_into = MERGED, owner.finding_id
                mw.basis_sha256 = sha256_json({"merged_into": owner.finding_id, "basis": mw.basis_sha256})
                writes.append(mw)
    return writes


def window_basis(read: dict[str, Any]) -> WindowBasis:
    """Map a `DispatchReadService.window` read to the matcher's input."""
    selection = read.get("selection") or {}
    window_rev = read.get("window_assessment")
    return WindowBasis(
        read["window"]["start"], read["window"]["end"], read["status"], selection.get("model_version"),
        None if not selection else str(selection["run_id"]), selection.get("input_sha256"),
        selection.get("cohort_sha256"), None if window_rev is None else str(window_rev["id"]),
        None if window_rev is None else window_rev["claim_level"],
        tuple(IntervalBasis.from_revision(r) for r in read.get("intervals") or ()))

