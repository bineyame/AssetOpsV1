"""CH-2 / CH-3: the thread lookup shared by the read adapters (estate snapshot, board thread port).

One statement gives each listed Finding's occurrence (thread, number, count, story start), every event of the
threads involved, and each listed Action's link (thread, ACCEPTED time, origin occurrence start). `thread_lookup`
then computes, in pure code, each Finding's segment and its state on a day as of a `known_at` (CH-3 §3: events with
`recorded_at <= known_at`; segments by story time, ruling CH3-R) and each Action's segment. Nothing is stored.
Occurrences are still read as stored now (CH-2 residual risk R-2). Pure: no database driver here."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Iterable, Mapping, Sequence

from assetops_backend.chain import lifecycle as lc

#: One statement: F (Finding occurrence), E (event of an involved thread) and A (Action link) rows, same columns:
#: kind, ref, thread_id, num, cnt, at1, at2, txt1, txt2, txt3, day1.
LOOKUP = (
    "WITH fo AS (SELECT o.* FROM finding_thread_occurrence o WHERE o.tenant_id = :t "
    "AND CAST(o.finding_id AS text) = ANY(CAST(:f AS text[]))), "
    "al AS (SELECT l.* FROM chain_action_thread l WHERE l.tenant_id = :t "
    "AND CAST(l.action_id AS text) = ANY(CAST(:a AS text[]))), "
    "th AS (SELECT thread_id FROM fo UNION SELECT thread_id FROM al) "
    "SELECT 'F' AS kind, CAST(fo.finding_id AS text) AS ref, CAST(fo.thread_id AS text) AS thread_id, "
    "fo.occurrence_no AS num, (SELECT count(*) FROM finding_thread_occurrence x WHERE x.thread_id = fo.thread_id) "
    "AS cnt, fo.episode_start AS at1, CAST(NULL AS timestamptz) AS at2, s.timezone AS txt1, t.mechanism AS txt2, "
    "t.subject_ref AS txt3, CAST(NULL AS date) AS day1 FROM fo JOIN finding_thread t ON t.id = fo.thread_id "
    "JOIN site s ON s.tenant_id = fo.tenant_id AND s.id = fo.site_id "
    "UNION ALL SELECT 'E', e.cause_id, CAST(e.thread_id AS text), e.seq, NULL, e.recorded_at, NULL, e.state, "
    "e.cause_kind, NULL, e.effective_day FROM finding_thread_event e WHERE e.thread_id IN (SELECT thread_id FROM th) "
    "UNION ALL SELECT 'A', CAST(al.action_id AS text), CAST(al.thread_id AS text), NULL, NULL, "
    "CASE WHEN al.action_kind = 'MINI_TRIAL' THEN (SELECT min(x.recorded_at) FROM action_event x "
    "WHERE x.tenant_id = al.tenant_id AND x.action_id = al.action_id AND x.kind = 'ACCEPTED') "
    "ELSE (SELECT d.recorded_at FROM domain_action d WHERE d.tenant_id = al.tenant_id AND d.id = al.action_id) END, "
    "(SELECT o.episode_start FROM finding_thread_occurrence o WHERE o.finding_id = al.origin_finding_id), "
    "s.timezone, CAST(al.origin_finding_id AS text), NULL, NULL FROM al "
    "JOIN site s ON s.tenant_id = al.tenant_id AND s.id = al.site_id")

#: `state_day` (CH-3 packet deviation, additive): the Site-local day the state was read on, so COH-13 can compare a
#: board and a Portfolio read of one thread taken on different days.
PUBLIC_KEYS = ("id", "occurrence_no", "occurrences", "segment_no", "state", "state_effective_day", "state_day")


def _day(at: datetime | None, tz: str | None) -> date | None:
    return None if at is None or tz is None else lc.local_day(at, tz)


def thread_lookup(rows: Sequence[Any], *, day: date | None = None, known_at: datetime | None = None,
                  complete: Mapping[str, Iterable[date]] | None = None,
                  close_after: int = 7, day_at: datetime | None = None) -> dict[str, Any]:
    """`LOOKUP` rows -> {"findings": {finding_id: {id, occurrence_no, occurrences, segment_no, state,
    state_effective_day}}, "actions": {action_id: thread_id}, "action_segments": {action_id: n},
    "lifecycle": {finding_id: the board view (`lifecycle.thread_view`)}, "subjects": {finding_id: (mechanism,
    subject_ref)}}. `day` None reads the latest state; `complete` maps a Finding id to its fully checked days.
    `day_at` (an instant; CH3-R, AG-27) reads each Finding on its own Site's local day holding that instant, and
    overrides `day` for a Finding whose Site zone is known (the Portfolio's window across Sites)."""
    occ_rows: list[tuple[Any, ...]] = []
    act_rows: list[tuple[Any, ...]] = []
    events: dict[str, list[lc.Event]] = {}
    for kind, ref, thread_id, num, cnt, at1, at2, txt1, txt2, txt3, day1 in rows:
        if kind == "F":
            occ_rows.append((ref.lower(), thread_id, num, cnt, at1, txt1, txt2, txt3))
        elif kind == "E":
            events.setdefault(thread_id, []).append(lc.Event(int(num), txt1, txt2, ref, day1, at1))
        else:
            act_rows.append((ref.lower(), thread_id, at1, at2, txt1, (txt2 or "").lower()))
    findings: dict[str, Any] = {}
    views: dict[str, Any] = {}
    subjects: dict[str, Any] = {}
    for fid, thread_id, num, cnt, start, tz, mechanism, subject in occ_rows:
        evs = events.get(thread_id, [])
        on = _day(day_at, tz) if day_at is not None and tz is not None else day
        view = lc.thread_view(evs, lc.Occurrence(fid, _day(start, tz)), on, known_at,
                              (complete or {}).get(fid, ()), close_after)
        views[fid] = view
        subjects[fid] = (mechanism, subject)
        eff = view["state_effective_day"]
        findings[fid] = {"id": thread_id, "occurrence_no": int(num), "occurrences": int(cnt),
                         "segment_no": view["segment_no"], "state": view["state"],
                         "state_effective_day": None if eff is None else eff.isoformat(),
                         "state_day": None if on is None else on.isoformat()}
    actions: dict[str, Any] = {}
    segments: dict[str, int] = {}
    for aid, thread_id, accepted, origin_start, tz, origin in act_rows:
        actions[aid] = thread_id
        evs = lc.visible(events.get(thread_id, []), known_at)
        segments[aid] = lc.action_segment(evs, lc.Occurrence(origin, _day(origin_start, tz)), _day(accepted, tz))
    return {"findings": findings, "actions": actions, "action_segments": segments, "lifecycle": views,
            "subjects": subjects}


def public_thread(thread: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """The wire form of a Finding's thread (CH-2 §5.3 plus CH-3's state, effective day and segment)."""
    return None if thread is None else {k: thread.get(k) for k in PUBLIC_KEYS}
