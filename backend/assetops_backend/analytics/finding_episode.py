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
  instant of the gap is covered by an observed coherent segment (Necessary, or
  Indeterminate only for a modelling reason, dispatch-3.1 `_NOT_EVIDENCE_GAPS`)
  or by an observed stop (last ON, then OFF reports on both sides, then first
  ON) that the selected runs' accepted generator reports confirm: both OFF
  endpoints present, and every report between the last and the first ON a
  GOOD, accepted, in-cohort OFF, in CURRENT non-Indeterminate windows with no
  generator series limit over the stop (Q17,
  `D-2026-10-12-s4-finding-phase-2-read-boundaries`). Missing or contrary
  proof leaves the stop unbridged. Window coverage or an empty segment list proves nothing; an
  INDETERMINATE or unobserved segment (contradiction, ambiguity, missing data)
  never bridges (`D-2026-10-12-s4-finding-phase-1-clarifications`).
- A cluster overlapping no episode opens a new Finding, linked by
  `recurs_after_finding_id` to the latest earlier episode of that generator
  only when the separation is assessed (CURRENT windows throughout) and
  observed OFF reports end the earlier run and precede the new one, each stop
  confirmed by the same report proof; otherwise it opens unlinked (recurrence
  relation unknown).
- One cluster over several episodes merges them: the earliest anchor (then
  UUID) stays canonical and the others record MERGED_INTO.
- One episode over several clusters splits: it keeps the cluster containing
  its immutable anchor (reserved before any other cluster is assigned); each
  other cluster opens a Finding `split_from` it.
- An episode with no cluster becomes UNCONFIRMED when the current basis over
  it is Indeterminate, and NO_LONGER_SUPPORTED when it is complete and has no
  Candidate (never "repaired" or "saved"). Candidate support over a
  NO_LONGER_SUPPORTED episode appends REOPENED under the same ID.
- The basis digest covers the selected window revisions and their input
  digests as well as the interval revisions; a revision whose supported facts
  (lifecycle, bounds, minutes, spans, limitations) are unchanged and whose
  provenance alone moved is BASIS_REFRESHED, never SUPPORT_CHANGED.
- Relation facts (continuity gaps, stop proofs, the recurrence record) are
  claim lineage (Q20): their normalized facts are in the support digest and
  their exact evidence IDs/digests in the basis digest, so a relation change
  always appends a revision. Version `finding-episode-2`; rows recorded under
  `finding-episode-1` are kept and re-evaluated by appending.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from fractions import Fraction
from typing import Any
from uuid import uuid4

from assetops_backend.analytics.assessment_inputs import iso, sha256_json
from assetops_backend.analytics.dispatch import CANDIDATE, INDETERMINATE, NECESSARY
from assetops_backend.analytics.dispatch_v3 import _NOT_EVIDENCE_GAPS, CONTINUITY_TOLERANCE, OFF_STATES

MATCHER_VERSION = "finding-episode-2"
GENERATOR_ROLES = ("generator_state", "generator_power")
DOMAIN = "mini_grid"
MECHANISM = "GENERATOR_SUPPORT_CANDIDATE"
CURRENT = "CURRENT"

SUPPORTED = "SUPPORTED"
UNCONFIRMED = "UNCONFIRMED"
NO_LONGER_SUPPORTED = "NO_LONGER_SUPPORTED"
MERGED = "MERGED"
BASIS_REFRESHED = "BASIS_REFRESHED"
REOPENED = "REOPENED"

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
    last_on: datetime | None = None

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
                             _at(interval.get("off_after")), segments, tuple(result.get("limitations") or ()),
                             _at(interval.get("last_on")))


@dataclass(frozen=True)
class StateReport:
    """One accepted public generator report of a selected AnalyticRun's input set (typed, normalized)."""
    evidence_id: str
    role: str
    asset: str
    at: datetime
    interval_start: datetime | None
    quality: str
    value: str | None
    member: tuple[str, str, str]
    disposition: str

    @property
    def clean(self) -> bool:
        return self.disposition == "ACCEPTED" and self.quality == "GOOD" and self.value is not None

    @property
    def off(self) -> bool:
        if not self.clean:
            return False
        if self.role == "generator_state":
            return self.value in OFF_STATES
        try:
            return Fraction(str(self.value)) == 0
        except (ValueError, ZeroDivisionError):
            return False

    def fact(self) -> list[Any]:
        return [self.evidence_id, iso(self.at), self.role, self.quality, self.value, list(self.member)]


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
    #: The selected run's accepted generator reports; None when they were not read (no stop proof possible).
    reports: tuple[StateReport, ...] | None = None
    members: frozenset[tuple[str, str, str]] = frozenset()
    generator_limits: tuple[tuple[datetime, datetime], ...] = ()


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
    support_sha256: str = ""
    #: The immutable recurrence record of the opening revision, carried into every later revision (Q20).
    recurrence: dict[str, Any] | None = None


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
    support_sha256: str = ""
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
        self.stop_cache: dict[str, list[dict[str, Any]]] = {}

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


def _stop_proof(site: _Site, asset: str, lo: datetime, hi: datetime, off_a: datetime,
                off_b: datetime) -> dict[str, Any]:
    """Q17: the selected runs' accepted generator reports confirm the stop (lo = last ON, hi = next first ON):
    both OFF endpoints are present, and every report strictly between lo and hi is an accepted GOOD in-cohort
    OFF, in CURRENT windows that are not Indeterminate and carry no generator series limit over the stop."""
    def refused(reason: str, ids: Any = ()) -> dict[str, Any]:
        return {"status": "REFUSED", "reason": reason, "evidence_ids": sorted(ids)}

    windows = [w for w in site.windows if w.start <= hi and lo < w.end]
    if not windows or not site.covered(lo, hi) or any(w not in site.usable for w in windows):
        return refused("STOP_NOT_ASSESSED")
    checked: list[StateReport] = []
    for w in windows:
        if w.reports is None:
            return refused("NO_TYPED_GENERATOR_REPORTS")
        if w.window_claim == INDETERMINATE:
            return refused("WINDOW_INDETERMINATE")
        if any(a <= hi and lo <= b for a, b in w.generator_limits):
            return refused("GENERATOR_SERIES_AMBIGUOUS")
        mine = [r for r in w.reports if r.asset == asset and w.start <= r.at < w.end and lo < r.at < hi]
        for reason, bad in (("UNACCEPTED_REPORT", [r for r in mine if r.disposition != "ACCEPTED"]),
                            ("NOT_GOOD_REPORT", [r for r in mine if not r.clean]),
                            ("WRONG_COHORT_REPORT", [r for r in mine if r.member not in w.members]),
                            ("CONTRARY_REPORT", [r for r in mine if not r.off])):
            if bad:
                return refused(reason, (r.evidence_id for r in bad))
        checked += mine
    first = [r.evidence_id for r in checked if off_a in (r.at, r.interval_start)]
    last = [r.evidence_id for r in checked if off_b in (r.at, r.interval_start)]
    if not first or not last:
        return refused("OFF_ENDPOINT_NOT_IN_SELECTED_RUN")
    return {"status": "CONFIRMED", "off_after_evidence_ids": sorted(first), "off_before_evidence_ids": sorted(last),
            "checked_evidence_ids": sorted(r.evidence_id for r in checked),
            "run_ids": sorted({str(w.run_id) for w in windows}),
            "window_revision_ids": sorted(str(w.window_revision_id) for w in windows),
            "reports_sha256": sha256_json(sorted(r.fact() for r in checked))}


def _stop_records(site: _Site, asset: str) -> list[dict[str, Any]]:
    """Stops between consecutive runs: last ON, the first OFF after it, the last OFF before the next run, then
    its first ON, in that order, each with its report proof (Q17). A contrary ON report between the OFFs is a
    run of its own; any other contrary, non-GOOD or out-of-cohort report refuses the proof."""
    if asset not in site.stop_cache:
        runs = sorted(site.intervals(asset), key=lambda i: i.first_on)
        site.stop_cache[asset] = [
            {"start": x.last_on, "end": y.first_on, "off_after": x.off_after, "off_before": y.off_before,
             "ended_assessment_revision_id": x.revision_id, "next_assessment_revision_id": y.revision_id,
             "proof": _stop_proof(site, asset, x.last_on, y.first_on, x.off_after, y.off_before)}
            for x, y in zip(runs, runs[1:])
            if x.last_on is not None and x.off_after is not None and y.off_before is not None
            and x.last_on <= x.off_after <= y.off_before <= y.first_on]
    return site.stop_cache[asset]


def _confirmed_stops(site: _Site, asset: str) -> list[dict[str, Any]]:
    return [r for r in _stop_records(site, asset) if r["proof"]["status"] == "CONFIRMED"]


def _stops(site: _Site, asset: str) -> list[tuple[datetime, datetime]]:
    return [(r["start"], r["end"]) for r in _confirmed_stops(site, asset)]


def _fully_covered(pieces: list[tuple[datetime, datetime]], lo: datetime, hi: datetime) -> bool:
    """Every instant of [lo, hi] lies in one of the pieces (no empty or vacuous span)."""
    t = lo
    for a, b in sorted(p for p in pieces if p[0] < p[1] and p[1] > lo):
        if a > t:
            return False
        t = max(t, b)
        if t >= hi:
            return True
    return t >= hi


def _bridges(site: _Site, asset: str, a: tuple[Seg, IntervalBasis], b: tuple[Seg, IntervalBasis]) -> bool:
    lo, hi = a[0].end, b[0].start
    if hi <= lo:
        return True
    if hi - lo > CONTINUITY_TOLERANCE or not site.covered(lo, hi):
        return False
    inside = [s for s, _ in _segments_in(site.intervals(asset), lo, hi)]
    if any(not s.coherent for s in inside if s.classification != CANDIDATE):
        return False
    if a[1].revision_id != b[1].revision_id and (a[1].off_after is None or b[1].off_before is None):
        return False
    # Window coverage is not observation: every instant of the gap needs an observed segment or stop.
    pieces = [(s.start, s.end) for s in inside if s.observed] + _stops(site, asset)
    return _fully_covered(pieces, lo, hi)


def _continuity(site: _Site, cluster: _Cluster) -> list[dict[str, Any]]:
    """Each gap the cluster bridged between Candidate spans (Q2/Q11 read): its bounds, the observed coherent
    segments and observed stops that cover it, and that it adds no Candidate minutes."""
    out: list[dict[str, Any]] = []
    spans = sorted(cluster.spans, key=lambda x: (x[0].start, x[0].end))
    reach = spans[0][0].end
    for s, _ in spans[1:]:
        lo, hi = reach, s.start
        reach = max(reach, s.end)
        if hi <= lo:
            continue
        inside = [(x, i) for x, i in _segments_in(site.intervals(cluster.asset), lo, hi)
                  if x.observed and x.classification != CANDIDATE]
        stops = [r for r in _confirmed_stops(site, cluster.asset) if r["start"] < hi and lo < r["end"]]
        out.append({
            "start": iso(lo), "end": iso(hi), "minutes": _num(_minutes(lo, hi)),
            "bridged_by": sorted({"OBSERVED_SEGMENTS"} if inside else set()) + (["OBSERVED_STOP"] if stops else []),
            "segments": [{"start": iso(max(x.start, lo)), "end": iso(min(x.end, hi)),
                          "classification": x.classification, "reasons": list(x.missing),
                          "assessment_revision_id": i.revision_id} for x, i in inside],
            "stops": [{"start": iso(r["start"]), "end": iso(r["end"]), "off_after": iso(r["off_after"]),
                       "off_before": iso(r["off_before"]),
                       "ended_assessment_revision_id": r["ended_assessment_revision_id"],
                       "next_assessment_revision_id": r["next_assessment_revision_id"],
                       "proof": r["proof"]} for r in stops],
            "candidate_minutes_added": "0",
        })
    return out


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
        "continuity": _continuity(site, cluster),
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
    # The supported facts, which SUPPORT_CHANGED means; provenance (revision IDs, inputs) is not in it.
    support = sha256_json({"lifecycle": lifecycle, "bounds": [iso(start), iso(end)],
                           "minutes": {k: _num(v) for k, v in minutes.items()}, "limitations": sorted(limits),
                           "spans": [[x["start"], x["end"], x["minutes"]] for x in claim.get("candidate_spans", [])],
                           "relations": _relation_facts(claim)})
    # The basis is the supported facts plus every selected interval and window revision, the window input
    # digests (controls, bindings, evidence) and the cited evidence: a changed selected window revision
    # appends a revision even with equal minutes (D-2026-10-12-s4-finding-phase-1-clarifications).
    basis = sha256_json({"matcher": MATCHER_VERSION, "model": site.model, "support": support,
                         "intervals": sorted(i.revision_id for i in intervals),
                         "windows": sorted(w.window_revision_id for w in windows if w.window_revision_id),
                         "inputs": inputs, "cited": cited,
                         # Q20: the full relation records (proof evidence IDs, report digests, assessment refs).
                         "relations": sha256_json({"continuity": claim.get("continuity") or [],
                                                   "recurrence": claim.get("recurrence")})})
    return Write(finding_id, transition, lifecycle, claim_level, site.model, primary_id, primary_run, window_rev,
                 start, end, minutes, claim, limits, assessments, cited, inputs, basis, support)


def _relation_facts(claim: dict[str, Any]) -> dict[str, Any]:
    """The supported relation facts (Q20): gap bounds, what bridged them, stop OFF bounds and proof status, and
    the recurrence status/prior/OFF times. Provenance IDs and digests are in the basis, not here."""
    rec = claim.get("recurrence") or {}
    return {
        "continuity": [[g["start"], g["end"], g["bridged_by"],
                        [[x["off_after"], x["off_before"], (x.get("proof") or {}).get("status")]
                         for x in g.get("stops") or ()]] for g in claim.get("continuity") or ()],
        "recurrence": None if not rec else [rec.get("status"), rec.get("reason"), rec.get("prior_finding_id"),
                                            (rec.get("off_after_prior") or {}).get("at"),
                                            (rec.get("off_before_new") or {}).get("at")],
    }


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
    w = _write(site, e.finding_id, lifecycle, lifecycle, INDETERMINATE if indeterminate else NECESSARY,
               primary, intervals, windows, e.episode_start, e.episode_end, minutes, claim, limits, cited)
    if e.lifecycle == lifecycle and e.support_sha256 == w.support_sha256:
        w.transition = BASIS_REFRESHED
    return w


def _recurrence(site: _Site, c: _Cluster, known: list[Episode]) -> tuple[Episode | None, dict[str, Any]]:
    """The earlier episode this cluster recurs after, only when an observed break is proven: the separation is
    assessed throughout, the earlier run ends with an observed OFF and the new run starts after one. The record
    names both OFF bounds and the covered windows, or why the relation is not established (Q3/Q13)."""
    earlier = [k for k in known if k.asset == c.asset and k.episode_end < c.start]
    prior = max(earlier, key=lambda k: (k.episode_end, k.finding_id), default=None)

    def unknown(reason: str) -> tuple[None, dict[str, Any]]:
        return None, {"status": "NOT_ESTABLISHED", "reason": reason,
                      "nearest_earlier_finding_id": None if prior is None else prior.finding_id}

    if prior is None:
        return unknown("NO_EARLIER_FINDING")
    if not site.covered(prior.episode_end, c.start):
        return unknown("SEPARATION_NOT_ASSESSED")
    ends = [i for i in site.intervals(c.asset)
            if i.first_on <= prior.episode_end <= (i.last_on or i.first_on)]
    if not ends or any(i.off_after is None or i.off_after > c.start for i in ends):
        return unknown("NO_OBSERVED_OFF_AFTER_EARLIER_RUN")
    new_run = c.spans[0][1]
    if new_run.off_before is None or new_run.off_before < prior.episode_end:
        return unknown("NO_OBSERVED_OFF_BEFORE_NEW_RUN")
    ended = min(ends, key=lambda i: i.off_after)
    # Q17: both stops around the separation (after the earlier run, before the new one) are proven by reports.
    records = _stop_records(site, c.asset)
    after = next((r for r in records if r["ended_assessment_revision_id"] == ended.revision_id), None)
    before = next((r for r in records if r["next_assessment_revision_id"] == new_run.revision_id), None)
    for stop in (after, before):
        if stop is None:
            return unknown("SEPARATION_STOP_NOT_OBSERVED")
        if stop["proof"]["status"] != "CONFIRMED":
            return unknown(f"SEPARATION_STOP_NOT_CONFIRMED: {stop['proof']['reason']}")
    return prior, {
        "status": "LINKED", "prior_finding_id": prior.finding_id, "prior_episode_end": iso(prior.episode_end),
        "separation_minutes": _num(_minutes(prior.episode_end, c.start)),
        "off_after_prior": {"at": iso(ended.off_after), "assessment_revision_id": ended.revision_id},
        "off_before_new": {"at": iso(new_run.off_before), "assessment_revision_id": new_run.revision_id},
        "stop_proofs": [after["proof"]] if after is before else [after["proof"], before["proof"]],
        "covered_window_revision_ids": sorted(w.window_revision_id for w in site.windows_over(prior.episode_end,
                                                                                              c.start)
                                              if w.window_revision_id)}


def _new(site: _Site, cluster: _Cluster, *, recurrence: tuple[Episode | None, dict[str, Any]],
         split_from: str | None) -> Write:
    finding_id = str(uuid4())
    recurs_after, relation = recurrence
    gap = None if recurs_after is None else _num(_minutes(recurs_after.episode_end, cluster.start))
    extra = {"recurs_after_finding_id": None if recurs_after is None else recurs_after.finding_id,
             "separation_minutes": gap, "split_from_finding_id": split_from, "recurrence": relation}
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
                w = _new(site, c, recurrence=_recurrence(site, c, known), split_from=None)
                writes.append(w)
                known.append(Episode(w.finding_id, c.asset, c.start, SUPPORTED, c.start, c.end, w.basis_sha256,
                                     model_version, w.support_sha256, w.claim["recurrence"]))
            continue
        # Ownership: an episode is reserved for the cluster containing its immutable anchor, so an earlier
        # cluster can never take it; each cluster goes to its earliest-anchor (then UUID) eligible episode.
        by_anchor = sorted(es, key=lambda e: (e.anchor_start, e.finding_id))
        home = {e.finding_id: next((i for i, c in enumerate(cs) if _overlaps(c, e)
                                    and c.start <= e.anchor_start <= c.end), None) for e in es}
        owners: dict[str, _Cluster] = {}
        owned_by: list[tuple[_Cluster, Episode | None, Episode]] = []
        for i, c in enumerate(cs):
            owner = next((e for e in by_anchor if _overlaps(c, e) and e.finding_id not in owners
                          and home[e.finding_id] in (None, i)), None)
            if owner is not None:
                owners[owner.finding_id] = c
            owned_by.append((c, owner, next(e for e in by_anchor if _overlaps(c, e))))
        split_parents = {first.finding_id for c, owner, first in owned_by if owner is None}
        absorbed: dict[str, list[Episode]] = {}
        for e in es:
            if e.finding_id not in owners:
                h = home[e.finding_id]
                c = cs[h] if h is not None else next(c for c in cs if _overlaps(c, e))
                canonical = next(o for o in es if owners.get(o.finding_id) is c)
                absorbed.setdefault(canonical.finding_id, []).append(e)
        for c, owner, first in owned_by:
            if owner is None:
                w = _new(site, c, recurrence=(None, {"status": "NOT_APPLICABLE", "reason": "SPLIT_PART"}),
                         split_from=first.finding_id)
                writes.append(w)
                continue
            merged = absorbed.get(owner.finding_id, [])
            if merged:
                transition = "MERGED"
            elif owner.finding_id in split_parents:
                transition = "SPLIT"
            elif owner.model_version != model_version:
                transition = "MODEL_REEVALUATED"
            elif owner.lifecycle == NO_LONGER_SUPPORTED:
                transition = REOPENED
            else:
                transition = "SUPPORT_CHANGED"
            extra = {"merged_finding_ids": sorted(m.finding_id for m in merged),
                     "split_into_count": sum(1 for _, o, f in owned_by if o is None and f is owner),
                     "recurrence": owner.recurrence}
            w = _support_write(site, owner.finding_id, c, transition, anchor=owner.anchor_start, extra=extra)
            if transition == "SUPPORT_CHANGED" and w.support_sha256 == owner.support_sha256:
                w.transition = BASIS_REFRESHED
            if w.basis_sha256 != owner.basis_sha256 or merged or owner.finding_id in split_parents:
                writes.append(w)
            for m in merged:
                mw = _support_write(site, m.finding_id, c, "MERGED_INTO", anchor=m.anchor_start,
                                    extra={"merged_into_finding_id": owner.finding_id, "recurrence": m.recurrence})
                mw.lifecycle, mw.merged_into = MERGED, owner.finding_id
                mw.basis_sha256 = sha256_json({"merged_into": owner.finding_id, "basis": mw.basis_sha256})
                writes.append(mw)
    return writes


def _when(value: Any) -> datetime | None:
    return value if value is None or isinstance(value, datetime) else _at(str(value))


def state_reports(evidence: list[dict[str, Any]] | None) -> tuple[StateReport, ...] | None:
    """The selected run's exact input evidence rows (`DispatchReadService.run`) as typed generator reports."""
    if evidence is None:
        return None
    return tuple(StateReport(str(e["evidence_id"]), e["role"], str(e["asset_id"]),
                             _when(e["interval_end"]) or _when(e["source_time"]), _when(e["interval_start"]),
                             str(e["quality"]), None if e["value"] is None else str(e["value"]),
                             (str(e["gateway_id"]), str(e["source_id"]), str(e["sequence_epoch"])),
                             str(e.get("disposition") or ""))
                 for e in evidence if e["role"] in GENERATOR_ROLES and e.get("asset_id") is not None)


def window_basis(read: dict[str, Any], run_evidence: list[dict[str, Any]] | None = None) -> WindowBasis:
    """Map a `DispatchReadService.window` read (and its selected run's input evidence) to the matcher's input."""
    selection = read.get("selection") or {}
    window_rev = read.get("window_assessment")
    cohort = selection.get("cohort") or {}
    members = frozenset((str(m["gateway_id"]), str(m["source_id"]), str(m["sequence_epoch"]))
                        for m in cohort.get("members") or ())
    limits = tuple((_at(x["start"]), _at(x["end"])) for x in cohort.get("limits") or ()
                   if x.get("role") in GENERATOR_ROLES)
    return WindowBasis(
        read["window"]["start"], read["window"]["end"], read["status"], selection.get("model_version"),
        None if not selection else str(selection["run_id"]), selection.get("input_sha256"),
        selection.get("cohort_sha256"), None if window_rev is None else str(window_rev["id"]),
        None if window_rev is None else window_rev["claim_level"],
        tuple(IntervalBasis.from_revision(r) for r in read.get("intervals") or ()),
        state_reports(run_evidence), members, limits)

