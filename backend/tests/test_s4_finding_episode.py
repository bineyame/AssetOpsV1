"""Pure (no database) tests of the S4-01 episode matcher `finding_episode.plan`.

Each scenario is built from selected dispatch windows and the episodes earlier
passes persisted (fed back from `plan`'s own writes), so the immutable choices
- which ID keeps which part, which earlier Finding a new one recurs after - are
checked without Postgres.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from itertools import count

from assetops_backend.analytics.dispatch import CANDIDATE, INDETERMINATE, NECESSARY
from assetops_backend.analytics.finding_episode import (
    Episode,
    IntervalBasis,
    Seg,
    StateReport,
    WindowBasis,
    Write,
    plan,
    plan_pass,
)

MODEL = "dispatch-3.1"
CONTRADICTION = ("REPORTS_OVERLAP: two PV reports at the same instants",)
_ids = count(1)


def at(hhmm: str, day: int = 6) -> datetime:
    h, m = map(int, hhmm.split(":"))
    return datetime(2026, 10, day, tzinfo=timezone.utc) + timedelta(hours=h, minutes=m)


def seg(a: datetime, b: datetime, cls: str = CANDIDATE, observed: bool = True, missing: tuple = ()) -> Seg:
    return Seg(a, b, observed, cls, (f"ev-{a:%d%H%M}",), missing)


def run(segments: list[Seg], off_before: datetime | None, off_after: datetime | None, asset: str = "G1",
        claim: str = CANDIDATE) -> IntervalBasis:
    n = next(_ids)
    return IntervalBasis(f"rev-{n}", f"run-{n}", asset, claim, segments[0].start, off_before, off_after,
                         tuple(segments), (), segments[-1].end)


MEMBER = ("gw", "src", "epoch-1")


def report(t: datetime, value: str = "STOPPED", *, quality: str = "GOOD", member: tuple = MEMBER,
           role: str = "generator_state", asset: str = "G1", eid: str | None = None) -> StateReport:
    return StateReport(eid or f"st-{t:%d%H%M}-{value}", role, asset, t, None, quality, value, member, "ACCEPTED")


def day(d: int, *intervals: IntervalBasis, status: str = "CURRENT", rev: str | None = None,
        extra: tuple = (), reports: tuple | None = (), limits: tuple = (), claim: str | None = None) -> WindowBasis:
    """A selected window; its run's accepted generator reports are the OFF bounds of its intervals (inside the
    window) plus `extra`, or None when `reports` is None (not read)."""
    start = datetime(2026, 10, d, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    offs = {t for i in intervals for t in (i.off_before, i.off_after) if t is not None and start <= t < end}
    typed = None if reports is None else tuple(report(t, asset=i.asset) for i in intervals
                                              for t in (i.off_before, i.off_after) if t in offs) + tuple(extra)
    return WindowBasis(start, end, status, MODEL, f"wrun-{d}", f"in-{d}", "cohort",
                       rev or f"win-{d}-{next(_ids)}", claim or (CANDIDATE if intervals else NECESSARY),
                       tuple(intervals), typed, frozenset({MEMBER}), limits)


def persisted(writes: list[Write], before: list[Episode] = ()) -> list[Episode]:
    """The episodes the store would return after applying `writes` (latest revision per Finding)."""
    out = {e.finding_id: e for e in before}
    for w in writes:
        prior = out.get(w.finding_id)
        anchor = prior.anchor_start if prior else w.new_finding["anchor_start"]
        out[w.finding_id] = Episode(w.finding_id, w.asset or prior.asset, anchor, w.lifecycle, w.episode_start,
                                    w.episode_end, w.basis_sha256, w.model_version, w.support_sha256,
                                    prior.recurrence if prior else w.claim.get("recurrence"))
    return list(out.values())


def opened(windows: list[WindowBasis]) -> tuple[list[Write], list[Episode]]:
    writes = plan(windows, [], MODEL)
    return writes, persisted(writes)


class TestSplitKeepsTheAnchor:
    def test_split_with_the_anchor_in_the_later_part_keeps_the_original_id(self) -> None:
        # opened at 08:30, then late earlier evidence moved the bounds to 08:00 (F04 shape)
        _, eps = opened([day(6, run([seg(at("08:30"), at("09:00"))], at("08:25"), at("09:05")))])
        [orig] = eps
        widened = plan([day(6, run([seg(at("08:00"), at("09:00"))], at("07:55"), at("09:05")))], eps, MODEL)
        eps = persisted(widened, eps)
        assert [(w.transition, w.episode_start) for w in widened] == [("SUPPORT_CHANGED", at("08:00"))]
        # a contradiction at 08:15-08:25 splits it; the anchor (08:30) lies in the later cluster
        writes = plan([day(6, run([seg(at("08:00"), at("08:15")),
                                   seg(at("08:15"), at("08:25"), INDETERMINATE, missing=CONTRADICTION),
                                   seg(at("08:25"), at("09:00"))], at("07:55"), at("09:05")))], eps, MODEL)
        kept = next(w for w in writes if w.finding_id == orig.finding_id)
        new = next(w for w in writes if w.finding_id != orig.finding_id)
        assert (kept.transition, kept.episode_start, kept.episode_end) == ("SPLIT", at("08:25"), at("09:00"))
        assert not any(x.startswith("ANCHOR_OUTSIDE_SUPPORT") for x in kept.limitations)
        assert (new.transition, new.episode_start) == ("OPENED", at("08:00"))
        assert new.new_finding["split_from_finding_id"] == orig.finding_id


class TestRecurrence:
    def _first(self) -> list[Episode]:
        return opened([day(6, run([seg(at("08:00"), at("08:30"))], at("07:55"), at("08:35")))])[1]

    def _later(self, *, off_before: datetime | None = at("07:55", 8)) -> WindowBasis:
        return day(8, run([seg(at("08:00", 8), at("08:30", 8))], off_before, at("08:35", 8)))

    def test_no_recurrence_link_across_an_unassessed_day(self) -> None:
        eps = self._first()
        windows = [day(6, run([seg(at("08:00"), at("08:30"))], at("07:55"), at("08:35"))), self._later()]
        [w] = [w for w in plan(windows, eps, MODEL) if w.new_finding]  # day 6 is re-read with new IDs
        assert w.transition == "OPENED" and w.new_finding["recurs_after_finding_id"] is None

    def test_linked_when_the_separation_is_assessed_and_off_is_observed(self) -> None:
        eps = self._first()
        windows = [day(6, run([seg(at("08:00"), at("08:30"))], at("07:55"), at("08:35"))), day(7), self._later()]
        [w] = [w for w in plan(windows, eps, MODEL) if w.new_finding]  # day 6 is re-read with new IDs
        assert w.new_finding["recurs_after_finding_id"] == eps[0].finding_id

    def test_no_link_when_the_earlier_run_has_no_observed_off(self) -> None:
        eps = self._first()
        windows = [day(6, run([seg(at("08:00"), at("08:30"))], at("07:55"), None)), day(7), self._later()]
        [w] = [w for w in plan(windows, eps, MODEL) if w.new_finding]  # day 6 is re-read with new IDs
        assert w.new_finding["recurs_after_finding_id"] is None

    def test_no_link_when_the_new_run_has_no_observed_off_before_it(self) -> None:
        eps = self._first()
        windows = [day(6, run([seg(at("08:00"), at("08:30"))], at("07:55"), at("08:35"))), day(7),
                   self._later(off_before=None)]
        [w] = [w for w in plan(windows, eps, MODEL) if w.new_finding]  # day 6 is re-read with new IDs
        assert w.new_finding["recurs_after_finding_id"] is None


class TestMergeAndSplit:
    def test_three_way_merge_keeps_the_earliest_anchor(self) -> None:
        stop = seg(at("08:10"), at("08:30"), INDETERMINATE, missing=CONTRADICTION)
        stop2 = seg(at("08:40"), at("09:00"), INDETERMINATE, missing=CONTRADICTION)
        _, eps = opened([day(6, run([seg(at("08:00"), at("08:10")), stop, seg(at("08:30"), at("08:40")), stop2,
                                     seg(at("09:00"), at("09:10"))], at("07:55"), at("09:15")))])
        assert len(eps) == 3
        writes = plan([day(6, run([seg(at("08:00"), at("09:10"))], at("07:55"), at("09:15")))], eps, MODEL)
        first = min(eps, key=lambda e: e.anchor_start)
        [canonical] = [w for w in writes if w.transition == "MERGED"]
        assert canonical.finding_id == first.finding_id and canonical.claim["merged_finding_ids"] == sorted(
            e.finding_id for e in eps if e is not first)
        assert sorted(w.merged_into for w in writes if w.transition == "MERGED_INTO") == [first.finding_id] * 2

    def test_mixed_split_and_merge_in_one_component(self) -> None:
        cut = seg(at("08:20"), at("08:30"), INDETERMINATE, missing=CONTRADICTION)
        _, eps = opened([day(6, run([seg(at("08:00"), at("08:20")), cut, seg(at("08:30"), at("08:50"))],
                                    at("07:55"), at("08:55")))])
        e1, e2 = sorted(eps, key=lambda e: e.anchor_start)
        # now 08:00-08:40 is one cluster (both anchors) and 08:45-08:50 is cut off by a contradiction
        writes = plan([day(6, run([seg(at("08:00"), at("08:40")),
                                   seg(at("08:40"), at("08:45"), INDETERMINATE, missing=CONTRADICTION),
                                   seg(at("08:45"), at("08:50"))], at("07:55"), at("08:55")))], eps, MODEL)
        by = {(w.finding_id, w.transition): w for w in writes}
        assert (e1.finding_id, "MERGED") in by and by[(e2.finding_id, "MERGED_INTO")].merged_into == e1.finding_id
        [part] = [w for w in writes if w.new_finding]
        assert part.new_finding["split_from_finding_id"] == e2.finding_id and part.episode_start == at("08:45")


class TestLifecycle:
    def test_candidate_over_a_closed_episode_reopens_it_under_the_same_id(self) -> None:
        candidate = run([seg(at("08:00"), at("08:30"))], at("07:55"), at("08:35"))
        _, eps = opened([day(6, candidate)])
        closed = plan([day(6, run([seg(at("08:00"), at("08:30"), NECESSARY)], at("07:55"), at("08:35"),
                                  claim=NECESSARY))], eps, MODEL)
        assert [w.transition for w in closed] == ["NO_LONGER_SUPPORTED"]
        eps = persisted(closed, eps)
        [w] = plan([day(6, run([seg(at("08:00"), at("08:30"))], at("07:55"), at("08:35")))], eps, MODEL)
        assert (w.finding_id, w.transition, w.lifecycle) == (eps[0].finding_id, "REOPENED", "SUPPORTED")

    def test_only_a_new_window_revision_appends_basis_refreshed(self) -> None:
        candidate = run([seg(at("08:00"), at("08:30"))], at("07:55"), at("08:35"))
        _, eps = opened([day(6, candidate, rev="win-a")])
        assert plan([day(6, candidate, rev="win-a")], eps, MODEL) == []  # same basis: idempotent
        [w] = plan([day(6, candidate, rev="win-b")], eps, MODEL)
        assert w.transition == "BASIS_REFRESHED" and w.window_revision_id == "win-b"
        assert w.basis_sha256 != eps[0].basis_sha256 and w.support_sha256 == eps[0].support_sha256

    def test_changed_minutes_are_support_changed_not_basis_refreshed(self) -> None:
        _, eps = opened([day(6, run([seg(at("08:00"), at("08:30"))], at("07:55"), at("08:35")))])
        [w] = plan([day(6, run([seg(at("08:00"), at("08:40"))], at("07:55"), at("08:45")))], eps, MODEL)
        assert w.transition == "SUPPORT_CHANGED"

    def test_a_stale_neighbouring_window_skips_the_episode(self) -> None:
        late = run([seg(at("23:30"), at("23:50"))], at("23:25"), None)
        assert plan([day(6, late), day(7, status="STALE_PROJECTION")], [], MODEL) == []
        assert [w.transition for w in plan([day(6, late)], [], MODEL)] == ["OPENED"]

    def test_the_pass_names_the_windows_it_deferred(self) -> None:
        """S4 deferred-match fix: a group skipped for its continuity margin names both the CURRENT window it lies
        in and the non-CURRENT neighbour, so neither reads as matched by this pass; a clear pass names none."""
        late = run([seg(at("23:30"), at("23:50"))], at("23:25"), None)
        early = run([seg(at("08:00", 5), at("08:30", 5))], at("07:55", 5), at("08:35", 5))
        writes, deferred = plan_pass([day(6, late), day(7, status="STALE_PROJECTION")], [], MODEL)
        assert writes == [] and deferred == {datetime(2026, 10, 6, tzinfo=timezone.utc),
                                             datetime(2026, 10, 7, tzinfo=timezone.utc)}
        writes, deferred = plan_pass([day(5, early), day(6, late), day(7, status="STALE_PROJECTION")], [], MODEL)
        assert [w.transition for w in writes] == ["OPENED"] and datetime(2026, 10, 5, tzinfo=timezone.utc)             not in deferred and len(deferred) == 2
        writes, deferred = plan_pass([day(6, late), day(7)], [], MODEL)
        assert [w.transition for w in writes] == ["OPENED"] and deferred == frozenset()
        # A stored episode whose window is no longer CURRENT cannot be closed or confirmed: deferred too.
        _, eps = opened([day(5, early)])
        writes, deferred = plan_pass([day(5, status="STALE_PROJECTION")], eps, MODEL)
        assert writes == [] and deferred == {datetime(2026, 10, 5, tzinfo=timezone.utc)}


class TestBridges:
    def _two_runs(self, *, off_after: datetime | None, off_before: datetime | None) -> list[WindowBasis]:
        a = run([seg(at("23:20", 8), at("23:50", 8))], at("23:15", 8), off_after)
        b = run([seg(at("00:05", 9), at("00:30", 9))], off_before, at("00:35", 9))
        return [day(8, a), day(9, b)]

    def test_cross_midnight_stop_with_observed_off_bridges(self) -> None:
        writes = plan(self._two_runs(off_after=at("23:55", 8), off_before=at("00:00", 9)), [], MODEL)
        assert [(w.episode_start, w.episode_end) for w in writes] == [(at("23:20", 8), at("00:30", 9))]

    def test_cross_midnight_stop_without_observed_off_opens_two_findings(self) -> None:
        writes = plan(self._two_runs(off_after=at("23:55", 8), off_before=None), [], MODEL)
        assert len(writes) == 2 and all(w.transition == "OPENED" for w in writes)
        assert writes[1].new_finding["recurs_after_finding_id"] is None

    def test_off_reports_out_of_order_prove_no_stop(self) -> None:
        writes = plan(self._two_runs(off_after=at("00:01", 9), off_before=at("00:00", 9)), [], MODEL)
        assert len(writes) == 2

    def test_an_empty_span_inside_the_gap_does_not_bridge(self) -> None:
        # a hole 08:10-08:15 with no segment: window coverage alone proves nothing
        holed = run([seg(at("08:00"), at("08:10")), seg(at("08:15"), at("08:30"))], at("07:55"), at("08:35"))
        assert len(plan([day(6, holed)], [], MODEL)) == 2

    def test_a_modelling_only_indeterminate_gap_bridges(self) -> None:
        model = seg(at("08:10"), at("08:20"), INDETERMINATE, missing=("transition inside the segment",))
        bridged = run([seg(at("08:00"), at("08:10")), model, seg(at("08:20"), at("08:30"))], at("07:55"),
                      at("08:35"))
        assert len(plan([day(6, bridged)], [], MODEL)) == 1


class TestRelationRecords:
    """Phase-2 read records (Q2/Q3/Q11/Q13): what bridged a gap and why a recurrence is or is not linked."""

    def test_a_bridged_stop_names_both_off_bounds_and_adds_no_candidate_minutes(self) -> None:
        writes = plan(TestBridges()._two_runs(off_after=at("23:55", 8), off_before=at("00:00", 9)), [], MODEL)
        [gap] = writes[0].claim["continuity"]
        assert (gap["start"], gap["end"], gap["bridged_by"]) == ("2026-10-08T23:50:00.000000Z", "2026-10-09T00:05:00.000000Z",
                                                                 ["OBSERVED_STOP"])
        [stop] = gap["stops"]
        assert (stop["off_after"], stop["off_before"]) == ("2026-10-08T23:55:00.000000Z", "2026-10-09T00:00:00.000000Z")
        assert gap["candidate_minutes_added"] == "0"

    def test_a_modelling_only_bridge_names_its_segments_and_reasons(self) -> None:
        model = seg(at("08:10"), at("08:20"), INDETERMINATE, missing=("transition inside the segment",))
        bridged = run([seg(at("08:00"), at("08:10")), model, seg(at("08:20"), at("08:30"))], at("07:55"),
                      at("08:35"))
        [w] = plan([day(6, bridged)], [], MODEL)
        [gap] = w.claim["continuity"]
        assert gap["bridged_by"] == ["OBSERVED_SEGMENTS"] and gap["stops"] == []
        assert gap["segments"][0]["reasons"] == ["transition inside the segment"]

    def test_an_intervening_on_report_is_its_own_run_not_one_stop(self) -> None:
        # A contrary ON between the two OFFs is a run of its own: no single stop spans it.
        a = run([seg(at("23:20", 8), at("23:50", 8))], at("23:15", 8), at("23:55", 8))
        on = run([seg(at("23:58", 8), at("23:58", 8), INDETERMINATE, missing=("generator state not observed",))],
                 at("23:55", 8), at("00:00", 9))
        b = run([seg(at("00:05", 9), at("00:30", 9))], at("00:00", 9), at("00:35", 9))
        writes = plan([day(8, a, on), day(9, b)], [], MODEL)
        assert len(writes) == 2  # the incoherent point at 23:58 refuses the bridge
        assert writes[0].claim["continuity"] == [] and writes[1].claim["continuity"] == []

    def test_linked_recurrence_names_both_offs_and_covered_windows(self) -> None:
        t = TestRecurrence()
        eps = t._first()
        windows = [day(6, run([seg(at("08:00"), at("08:30"))], at("07:55"), at("08:35"))), day(7), t._later()]
        [w] = [w for w in plan(windows, eps, MODEL) if w.new_finding]
        rec = w.claim["recurrence"]
        assert rec["status"] == "LINKED" and rec["prior_finding_id"] == eps[0].finding_id
        assert rec["off_after_prior"]["at"] == "2026-10-06T08:35:00.000000Z"
        assert rec["off_before_new"]["at"] == "2026-10-08T07:55:00.000000Z"
        assert len(rec["covered_window_revision_ids"]) == 3

    def test_unlinked_recurrence_states_the_reason(self) -> None:
        t = TestRecurrence()
        eps = t._first()
        windows = [day(6, run([seg(at("08:00"), at("08:30"))], at("07:55"), at("08:35"))), t._later()]
        [w] = [w for w in plan(windows, eps, MODEL) if w.new_finding]
        assert w.claim["recurrence"] == {"status": "NOT_ESTABLISHED", "reason": "SEPARATION_NOT_ASSESSED",
                                         "nearest_earlier_finding_id": eps[0].finding_id}


class TestStopProof:
    """Q17 (`D-2026-10-12-s4-finding-phase-2-read-boundaries`): a stop bridges only when the selected runs'
    accepted generator reports confirm it; anything contrary or unread leaves two Findings, not a silent bridge."""

    def _two(self, *, extra: tuple = (), reports: tuple | None = (), limits: tuple = (),
             claim: str | None = None, runs: tuple | None = None) -> list[WindowBasis]:
        a, b = runs or (run([seg(at("23:20", 8), at("23:50", 8))], at("23:15", 8), at("23:55", 8)),
                        run([seg(at("00:05", 9), at("00:30", 9))], at("00:00", 9), at("00:35", 9)))
        return [day(8, a, extra=extra, reports=reports, limits=limits, claim=claim, rev="win-8"),
                day(9, b, rev="win-9")]

    def _refused(self, windows: list[WindowBasis], reason: str) -> None:
        writes = plan(windows, [], MODEL)
        assert len(writes) == 2 and all(w.transition == "OPENED" for w in writes)
        assert all(w.claim["continuity"] == [] for w in writes)
        rec = writes[1].claim["recurrence"]
        assert rec["status"] == "NOT_ESTABLISHED" and rec["reason"] == f"SEPARATION_STOP_NOT_CONFIRMED: {reason}"
        assert writes[1].new_finding["recurs_after_finding_id"] is None

    def test_a_confirmed_stop_cites_its_checked_reports(self) -> None:
        mid = report(at("23:57", 8), eid="mid-off")
        [w] = plan(self._two(extra=(mid,)), [], MODEL)
        proof = w.claim["continuity"][0]["stops"][0]["proof"]
        assert proof["status"] == "CONFIRMED" and proof["off_after_evidence_ids"] == ["st-082355-STOPPED"]
        assert proof["off_before_evidence_ids"] == ["st-090000-STOPPED"]
        assert proof["checked_evidence_ids"] == ["mid-off", "st-082355-STOPPED", "st-090000-STOPPED"]
        assert proof["run_ids"] == ["wrun-8", "wrun-9"] and proof["reports_sha256"]

    def test_a_contradictory_state_between_two_valid_offs_refuses_the_bridge(self) -> None:
        self._refused(self._two(extra=(report(at("23:57", 8), "UNKNOWN_STATE", eid="contrary"),)),
                      "CONTRARY_REPORT")

    def test_a_non_good_report_between_the_offs_refuses_the_bridge(self) -> None:
        self._refused(self._two(extra=(report(at("23:57", 8), quality="SUSPECT"),)), "NOT_GOOD_REPORT")

    def test_a_report_from_outside_the_selected_cohort_refuses_the_bridge(self) -> None:
        self._refused(self._two(extra=(report(at("23:57", 8), member=("gw", "src", "epoch-0")),)),
                      "WRONG_COHORT_REPORT")

    def test_a_positive_power_report_between_the_offs_refuses_the_bridge(self) -> None:
        self._refused(self._two(extra=(report(at("23:57", 8), "4.2", role="generator_power"),)), "CONTRARY_REPORT")

    def test_unread_reports_never_bridge(self) -> None:
        self._refused(self._two(reports=None), "NO_TYPED_GENERATOR_REPORTS")

    def test_a_generator_series_limit_over_the_stop_refuses_the_bridge(self) -> None:
        self._refused(self._two(limits=((at("23:50", 8), at("23:59", 8)),)), "GENERATOR_SERIES_AMBIGUOUS")

    def test_an_indeterminate_window_refuses_the_bridge(self) -> None:
        writes = plan(self._two(claim=INDETERMINATE), [], MODEL)
        assert len(writes) == 2 and writes[1].claim["recurrence"]["reason"] == (
            "SEPARATION_STOP_NOT_CONFIRMED: WINDOW_INDETERMINATE")


class TestRelationsInTheBasis:
    """Q20: relation facts are claim lineage; a changed stop proof or recurrence appends a revision."""

    def test_a_changed_stop_proof_appends_a_revision_with_equal_minutes(self) -> None:
        t = TestStopProof()
        first = t._two()
        runs = (first[0].intervals[0], first[1].intervals[0])
        eps = persisted(plan(first, [], MODEL))
        assert plan(t._two(runs=runs), eps, MODEL) == []  # same basis and relations: idempotent
        # same windows and minutes, one more checked OFF report inside the stop: the proof digest moves
        windows = t._two(runs=runs, extra=(report(at("23:57", 8), eid="late-off"),))
        again = plan(windows, eps, MODEL)
        assert [w.transition for w in again] == ["BASIS_REFRESHED"]
        assert again[0].basis_sha256 != eps[0].basis_sha256 and again[0].support_sha256 == eps[0].support_sha256

    def test_a_refused_proof_is_support_not_provenance(self) -> None:
        bridged = plan(TestStopProof()._two(), [], MODEL)[0]
        assert bridged.claim["continuity"][0]["stops"][0]["proof"]["status"] == "CONFIRMED"
        refused = plan(TestStopProof()._two(extra=(report(at("23:57", 8), "X"),)), [], MODEL)[0]
        assert refused.support_sha256 != bridged.support_sha256

    def test_matcher_version_names_the_relation_proof(self) -> None:
        from assetops_backend.analytics.finding_episode import MATCHER_VERSION
        assert MATCHER_VERSION == "finding-episode-3"


class TestSeriesLimitEndReason:
    """LR-01 phase 2 (`finding-episode-3`, D-2026-10-15-lr01-source-time-cohort Q4): a material generator series
    refusal is carried into the revision with its lineage, and a cut tail ends the episode with SERIES_LIMIT."""

    OPEN_AFTER = "OPEN_BOUND: no OFF evidence after the interval in the read range"

    def _limit(self, a: datetime, b: datetime, asset: str = "G1", kind: str = "SEQUENCE_ORDER_INVERTED") -> dict:
        return {"kind": kind, "role": "generator_power", "asset_id": asset, "start": a.isoformat(),
                "end": b.isoformat(), "evidence_ids": ["ev-late", "ev-0800"], "clock": "NO_ATTESTATION",
                "attestation_refs": [], "window_start": "2026-10-06T00:00:00+00:00",
                "window_assessment_revision_id": "win-6-x", "analytic_run_id": "wrun-6"}

    def _window(self, interval: IntervalBasis, *limits: dict) -> WindowBasis:
        w = day(6, interval)
        return WindowBasis(w.start, w.end, w.status, w.model_version, w.run_id, w.input_sha256, w.cohort_sha256,
                           w.window_revision_id, INDETERMINATE if limits else w.window_claim, w.intervals,
                           w.reports, w.members, tuple((datetime.fromisoformat(x["start"]),
                                                        datetime.fromisoformat(x["end"])) for x in limits),
                           tuple(limits))

    def _cut(self, *limits: dict) -> IntervalBasis:
        i = run([seg(at("06:05"), at("07:00"))], at("06:00"), None)
        return IntervalBasis(i.revision_id, i.run_id, i.asset, i.claim_level, i.first_on, i.off_before, None,
                             i.segments, (self.OPEN_AFTER,), i.last_on)

    def test_run_one_tail_cut_is_series_limit_and_drops_the_dependent_open_bound(self) -> None:
        [w] = plan([self._window(self._cut(), self._limit(at("07:05"), at("08:00")))], [], MODEL)
        assert (w.lifecycle, w.episode_start, w.episode_end) == ("SUPPORTED", at("06:05"), at("07:00"))
        assert w.claim["end_reason"] == "SERIES_LIMIT"
        [s] = w.claim["series_limits"]
        assert (s["relation"], s["evidence_ids"], s["window_assessment_revision_id"], s["analytic_run_id"]) == (
            "CUTS_TAIL", ["ev-late", "ev-0800"], "win-6-x", "wrun-6")
        assert [x.split(":")[0] for x in w.limitations] == ["GENERATOR_SERIES_AMBIGUOUS"]
        assert not any(x.startswith("OPEN_BOUND") for x in w.limitations)
        # only the proven Candidate span is counted; the refused tail is not judged
        assert [c["start"][:16] for c in w.claim["candidate_spans"]] == ["2026-10-06T06:05"]

    def test_open_bound_without_a_refusal_stays_open_bound(self) -> None:
        [w] = plan([self._window(self._cut())], [], MODEL)
        assert w.claim["end_reason"] == "OPEN_BOUND" and w.claim["series_limits"] == []
        assert w.limitations == [self.OPEN_AFTER]

    def test_observed_off_and_candidate_end_are_typed(self) -> None:
        [w] = plan([day(6, run([seg(at("08:00"), at("08:30"))], at("07:55"), at("08:35")))], [], MODEL)
        assert w.claim["end_reason"] == "OFF_OBSERVED"
        [w] = plan([day(6, run([seg(at("08:00"), at("08:30")), seg(at("08:30"), at("09:00"), NECESSARY)],
                               at("07:55"), at("09:05")))], [], MODEL)
        assert w.claim["end_reason"] == "CANDIDATE_ENDED"

    def test_distant_or_other_asset_refusal_is_not_material(self) -> None:
        far = self._limit(at("08:00"), at("08:30"))
        other = self._limit(at("07:05"), at("08:00"), asset="G2")
        [w] = plan([self._window(self._cut(), far, other)], [], MODEL)
        assert w.claim["end_reason"] == "OPEN_BOUND" and w.claim["series_limits"] == []

    def test_refusal_inside_the_former_episode_revises_with_its_lineage(self) -> None:
        full = run([seg(at("06:05"), at("08:00"))], at("06:00"), at("08:05"))
        _, eps = opened([day(6, full)])
        writes = plan([self._window(self._cut(), self._limit(at("07:05"), at("08:00")))], eps, MODEL)
        [w] = writes
        assert (w.finding_id, w.transition, w.episode_end) == (eps[0].finding_id, "SUPPORT_CHANGED", at("07:00"))
        assert w.claim["end_reason"] == "SERIES_LIMIT"
        assert w.support_sha256 != eps[0].support_sha256
