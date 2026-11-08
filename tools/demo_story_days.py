"""DEMO-SPARSE: the sparse story calendar (`backend/conversions/demo-story-days-v1.json`) resolved to a build order.

Build sheet `AssetOpsV1-plan2/.agent/build-sheet-DEMO-SPARSE.md` sections 2 and 3 U2. A day list names, per Site,
the story days that carry a registered Lab run (and the named `missing` days that carry none). Day offsets
`S[+-]Nd` are relative to the story day S; each kind's times `D[+-]Nd HH:MM` (UTC) are relative to the entry's day.
`resolve` returns every entry as a `DayRun`, ordered by `received_at` (the build order; a `missing` day has no
delivery and sorts at its day's end), with one `sequence_epoch` `day-<n>` per stream of consecutive built Site-days (DD1a1-R8), numbered by its
first story run in that order and shared by the stream's complement runs.

Nothing here reads the wall clock: the caller passes S, the DB clock and the install instants.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

#: DD1a2-R: the B-22 list. v1 and v2 are kept as history (`--days` takes them).
DEFAULT_FILE = Path(__file__).resolve().parents[1] / "backend" / "conversions" / "demo-story-days-v3.json"
V1_FILE = DEFAULT_FILE.with_name("demo-story-days-v1.json")
#: DD-1a1 (DD1a1-R Q7): full-day story days. Each Kobo / Cold kind lists its `complement`, so one entry expands into
#: its story run plus the steady runs (and named placeholders) that tile the Site's local day [00:00, 24:00).
V2_FILE = DEFAULT_FILE.with_name("demo-story-days-v2.json")
#: DD1a1-R16: a full day (a kind with a `complement` list) is built only where every join of its day is STOPPED on the
#: registered Site. `tools/probe_kobo_nights.py` records each measured join under `full_days` in this file.
JOINS_FILE = DEFAULT_FILE.with_name("kobo-night-handover-v1.json")
SITES = ("kobo", "cold", "ev")
SITE_CODE = {"kobo": "KOBO-001", "cold": "COLD-LAB-001", "ev": "EV-LAB-001"}
CODE_SITE = {v: k for k, v in SITE_CODE.items()}
BOARD_WINDOW_DAYS = 30
INSTALL_LEAD = timedelta(hours=1)
#: Q1 ruling: the re-timed demo configuration is known at install + 30 min; every run knows it.
KNOWLEDGE_AFTER_INSTALL = timedelta(minutes=30)
PAST_MARGIN = timedelta(minutes=5)
#: Kinds `add-day` may append (sheet U4); trial-*, failure and fault carry work rows and Actions (prepare only).
ADD_DAY_KINDS = {"kobo": ("normal", "overuse", "overcast", "late", "missing", "degraded", "steady", "steady-before-first"),
                 "cold": ("normal", "degraded", "late"), "ev": ("normal", "late")}
LATE_AS = ("normal", "overuse")
#: A Site whose registered model admits only one weekday: its story days fall back to that weekday on or before
#: the listed day (Monday = 0). ev-charger/1 is ruled TUESDAY 08:00-16:00 and refuses any other day
#: (`host/ev_publication.py` `ev_parameters`, "the run window ... is not within one TUESDAY").
SITE_WEEKDAY = {"ev": 1}


def weekday_offset(site: str, S: datetime, offset: int) -> int:
    """`offset` moved back to the Site's ruled weekday (unchanged for a Site without one)."""
    if site not in SITE_WEEKDAY:
        return offset
    return offset - ((S + timedelta(days=offset)).weekday() - SITE_WEEKDAY[site]) % 7


def date_offset(day: date, S: datetime) -> int:
    """OWN-G1 §4.2: a calendar date as its story offset (`S+Nd`). S is a UTC midnight and a day's date is
    `(S + offset).date()`, so the offset is the plain day difference."""
    return (day - S.date()).days


def offset_date(S: datetime, offset: int) -> date:
    return (S + timedelta(days=offset)).date()


def local_yesterday(db_now: datetime, zone: str) -> date:
    """OWN-G1 §4.2: the day before DB now in the Site's own timezone (read from the build's `site` row)."""
    from zoneinfo import ZoneInfo

    return db_now.astimezone(ZoneInfo(zone)).date() - timedelta(days=1)


DEFAULT_KNOWN_AT = "D-1d 12:00"
_DAY = re.compile(r"^S([+-]\d+)d$")
_TIME = re.compile(r"^D([+-]\d+)d (\d{2}):(\d{2})$")


class StoryDaysError(SystemExit):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.error_code = code


@dataclass(frozen=True)
class DayRun:
    site: str
    day: str  # YYYY-MM-DD
    offset: int  # days from S
    kind: str
    start: datetime | None
    end: datetime | None
    received_at: datetime | None
    assess: str  # build | tick | none
    scenario: dict | None  # {"scenario_id", "scenario_version"}
    epoch: str | None
    as_kind: str | None = None
    note: str = ""
    known_at: datetime | None = None  # the run's foundation_known_at
    #: DD-1a1 (v2 day lists): the end of the local hours this entry's scenario covers (a Cold run's scenario covers
    #: 60 min of its 65-min interval), and the story kind a complement belongs to ("" for the story entry itself).
    covers_end: datetime | None = None
    complement_of: str = ""
    #: DD1a1-R5 (one stream per Site-day): a complement sends only source times in [start, emit_until) that no story
    #: run of its Site-day sends (`owned`: each story run's closed [start, end], ISO pairs). A story run has neither
    #: and is sent unchanged.
    emit_until: datetime | None = None
    owned: tuple = ()
    #: DD1b2-R2 (seam rule): True on every run of a Site-day that has complements. In `payload()` only when True.
    seam: bool = False

    @property
    def has_run(self) -> bool:
        return self.received_at is not None

    def keep_observation(self):
        """DD1b2-R2 seam rule, for the Kobo host path: at a seam an interval reading comes from the run whose span ended
        there and a state reading from the run that starts there. None for a day with no complements (story-only days
        stay byte-equal). Takes a `DeviceObservation`."""
        if not self.seam:
            return None
        time_rule = self.keep()

        def keep(observation) -> bool:
            if observation.outcome == "NO_PRECEDING_INTERVAL":
                return False
            if time_rule is None:  # the story run
                return True
            if observation.reading_class == "INTERVAL_SIGNAL" and _parse(observation.source_sample_time) == self.emit_until:
                return True
            return time_rule(observation.source_sample_time)
        keep.takes_observation = True  # `_host` passes it as `keep_observation`, not `keep_source_time`
        return keep

    def keep(self):
        """The source-time predicate the producer passes to the host (`keep_source_time`); None for a story run."""
        if not self.complement_of:
            return None
        lo, hi = self.start, self.emit_until
        spans = [(_parse(a), _parse(b)) for a, b in self.owned]

        def keep(source_time: str) -> bool:
            t = _parse(source_time)
            return lo <= t < hi and not any(a <= t <= b for a, b in spans)
        return keep

    def payload(self) -> dict[str, Any]:
        out = asdict(self)
        if not out["seam"]:  # only a day with complements carries it, so a story-only day's payload is unchanged
            out.pop("seam")
        for key in ("start", "end", "received_at", "known_at", "covers_end", "emit_until"):
            out[key] = iso(out[key]) if out[key] is not None else None
        out["owned"] = [list(p) for p in self.owned]
        return out


def _parse(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def load(path: str | Path | None = None) -> dict:
    return json.loads(Path(path or DEFAULT_FILE).read_text(encoding="utf-8"))


def full_day_joins() -> dict:
    """The measured joins of every full-day story scenario (`full_days` of the handover file)."""
    return json.loads(JOINS_FILE.read_text(encoding="utf-8")).get("full_days", {})


def check_full_day(site: str, day: str, scenario_id: str, joins: dict | None = None) -> None:
    """DD1a1-R16 guard: a full day may only be built where every join is STOPPED (measured on the registered Site)."""
    entry = (full_day_joins() if joins is None else joins).get(scenario_id)
    if not entry or not entry.get("joins") or any(j.get("generator") != "STOPPED" for j in entry["joins"]):
        raise StoryDaysError("FULL_DAY_JOIN_NOT_STOPPED", f"{site} {day}: {scenario_id} has no measured full day whose "
                             "every join is STOPPED, so it stays story-only (partly checked) (DD1a1-R16)")


#: DD1a1-R15's bound at a cut that is not a story start.
JOIN_SOC_BOUND, JOIN_FUEL_BOUND = 0.5, 0.5
#: DD1a2-R Q8.1: the fresh declared start of a full day with no measured previous 24:00.
FRESH_NIGHT = "kobo-night-early"


def check_mill_side(doc: dict, site: str, kind: str, offset: int) -> None:
    """DD1a2-R: a `steady-before*` kind only before `mill_change_day`, a `steady` kind only after it."""
    change = doc.get("mill_change_day")
    if site != "kobo" or not change:
        return
    at_change = day_offset(change)
    if (kind.startswith("steady-before") and offset >= at_change) or (kind == "steady" and offset <= at_change):
        raise StoryDaysError("MILL_PROFILE_WRONG_SIDE", f"{site} S{offset:+d}d: kind {kind!r} is on the wrong side of the "
                                                        f"mill change {change} (DD1a2-R)")


def check_full_day_chains(doc: dict, site: str, entries: list[tuple[int, str]], handover: dict | None = None) -> None:
    """DD1a2-R, closing `review-DD-1a1.md:108-110`: each full kind's complement list is the chain measured in `full_days`,
    and each 00:00 start equals the previous built full day's recorded 24:00 within R15's bound. A full day with no such
    neighbour takes the fresh declared start (Q8.1), unbounded. `entries` is (offset, story kind)."""
    kinds = doc["kinds"].get(site, {})
    full = {off: kinds[kind] for off, kind in entries if isinstance(kinds[kind].get("complement"), list)}
    if not full:
        return
    data = json.loads(JOINS_FILE.read_text(encoding="utf-8")) if handover is None else handover
    joins = data.get("full_days", {})
    for off, spec in sorted(full.items()):
        sid, where = spec["scenario_id"], f"{site} S{off:+d}d"
        comp = [kinds[name] for name in spec["complement"]]
        night = next((c["scenario_id"] for c in comp if c["start"].startswith("D-1d")), None)
        rest = next((c["scenario_id"] for c in comp if not c["start"].startswith("D-1d")), None)
        entry = joins.get(sid) or {}
        if night not in entry.get("nights", ()) or rest != entry.get("rest"):
            raise StoryDaysError("FULL_DAY_CHAIN_UNMEASURED", f"{where}: {sid} runs {night} and {rest}, which is not the "
                                                              f"chain measured in full_days (DD1a2-R)")
        before = full.get(off - 1)
        if before is None:
            if night != FRESH_NIGHT:
                raise StoryDaysError("FULL_DAY_JOIN_UNMEASURED", f"{where}: {night} starts from a previous day's 24:00, "
                                                                 f"and no full day is built before it (DD1a2-R Q8.1)")
            continue
        start, end = data["handover"][night]["start"], joins[before["scenario_id"]]["end_24"]
        if (end["generator"] != "STOPPED" or abs(start["soc"] - end["soc"]) > JOIN_SOC_BOUND
                or abs(start["fuel"] - end["fuel"]) > JOIN_FUEL_BOUND):
            raise StoryDaysError("FULL_DAY_JOIN_BOUND", f"{where}: {night} starts {start}, the previous day ended {end}, "
                                                        f"outside {JOIN_SOC_BOUND} pp / {JOIN_FUEL_BOUND} L (DD1a1-R15)")


def day_offset(text: str) -> int:
    m = _DAY.match(text)
    if not m:
        raise StoryDaysError("UNKNOWN_KIND", f"day {text!r} is not S[+-]Nd")
    return int(m.group(1))


def at_day(text: str, D: datetime) -> datetime:
    m = _TIME.match(text)
    if not m:
        raise StoryDaysError("UNKNOWN_KIND", f"time {text!r} is not D[+-]Nd HH:MM")
    return D + timedelta(days=int(m.group(1)), hours=int(m.group(2)), minutes=int(m.group(3)))


#: DD1a1-R10, DD1a2-R Q8.4: a Kobo `degraded` day cuts its story run by gateway batch order (a random source-id order),
#: which no real outage looks like; the source-time cut is backlog BL-18. Until it lands no Kobo `degraded` day, with or
#: without complements, may enter a shown calendar, a demo script or a live `add-day`. Cold's `degraded` kind
#: (`cold-missing-probe`) is not an outage cut and stays allowed. Only the DD-1a1 degraded-day check sets this.
DEGRADED_PROBE = False


def _entry(doc: dict, site: str, entry: dict, S: datetime) -> DayRun:
    kinds = doc["kinds"].get(site, {})
    kind = entry.get("kind")
    if kind not in kinds:
        raise StoryDaysError("UNKNOWN_KIND", f"{site} kind {kind!r} is not one of {sorted(kinds)}")
    if site == "kobo" and kind == "degraded" and not DEGRADED_PROBE:
        raise StoryDaysError("DEGRADED_DAY_HELD", f"{site} {entry.get('day')}: a Kobo degraded day is held until BL-18 "
                                                  f"(source-time outage cut); the Architect rules (DD1a1-R10)")
    off = weekday_offset(site, S, day_offset(entry["day"]))
    D = S + timedelta(days=off)
    spec = dict(kinds[kind])
    as_kind = None
    if kind == "missing":
        return DayRun(site, D.date().isoformat(), off, kind, None, None, None, "none", None, None, None,
                      spec.get("note", ""))
    if kind == "late" and "scenario_id" not in spec:
        as_kind = entry.get("as")
        if as_kind not in LATE_AS or as_kind not in kinds:
            raise StoryDaysError("UNKNOWN_KIND", f"{site} late day {entry['day']} needs as: one of {LATE_AS}")
        spec = {**kinds[as_kind], **spec}
    scenario = {"scenario_id": spec["scenario_id"], "scenario_version": spec["scenario_version"]}
    if kind.startswith("trial-") and doc.get("trial", {}).get("scenario_id"):
        scenario = {"scenario_id": doc["trial"]["scenario_id"],
                    "scenario_version": doc["trial"].get("scenario_version", 1)}
    return DayRun(site, D.date().isoformat(), off, kind, at_day(spec["start"], D), at_day(spec["end"], D),
                  at_day(spec["received_at"], D), spec.get("assess", "build"), scenario, None, as_kind,
                  spec.get("note", ""), at_day(spec.get("foundation_known_at", DEFAULT_KNOWN_AT), D))


#: A Site's local day is UTC+3 (Kobo and Cold): the local day D is [D-1 21:00Z, D 21:00Z).
LOCAL_DAY_START = timedelta(hours=-3)


def _expand(doc: dict, site: str, entry: dict, S: datetime, boundaries: tuple = ()) -> list[DayRun]:
    """One day entry -> its story run plus its complement runs (DD1a1-R Q7). A kind's `complement` is either a list
    of kind names (Kobo: each carries its own relative times) or `{"kind": "steady", "hours": [...]}` (Cold: one
    plain replay per listed hour). A complement is received `received_at` as its kind says, plus the story's
    lateness (a `late` day), and inherits the story's Foundation knowledge. A `missing` day has no complement."""
    story = _entry(doc, site, entry, S)
    kinds = doc["kinds"].get(site, {})
    spec = kinds.get(story.as_kind or story.kind, {})
    comp = spec.get("complement")
    if not story.has_run or not comp:
        return [story]
    D = datetime.fromisoformat(story.day).replace(tzinfo=timezone.utc)
    late = story.received_at - at_day(spec["received_at"], D)
    out = [replace(story, covers_end=at_day(spec["covers_end"], D) if "covers_end" in spec else story.end)]
    if isinstance(comp, dict):  # DD1a1-R14 withdrew Cold complements; only a list of kind names is supported
        raise StoryDaysError("COMPLEMENT_FORM_UNSUPPORTED", f"{site} {story.day}: complement must be a list of kinds")
    else:
        check_full_day(site, story.day, spec["scenario_id"])
        for name in comp:
            c = kinds[name]
            start, end = at_day(c["start"], D), at_day(c["end"], D)
            cut = next((b for b in boundaries if start < b < end), None)
            if cut is not None:
                # DD1a1-R7: one run cannot cite one basis across a foundation revision change, so the complement is
                # split at that instant: part A [start, cut) runs the kind's `part_a` file (the same windows up to the cut), part B [cut, end) is the kind's derived
                # file, whose start state is measured from a probe of part A. Both take the story's one epoch.
                sp = c.get("split")
                if not sp or start + timedelta(minutes=sp["at_minutes"]) != cut:
                    raise StoryDaysError("SPLIT_UNSUPPORTED", f"{site} {story.day}: {name} crosses a Foundation "
                                                              f"revision at {iso(cut)} and has no split file there")
                b, a = kinds[sp["kind"]], kinds[sp["part_a"]]
                # DD1a1-R7b: a run may not end at the boundary instant, so part A runs `part_a_minutes` (one step
                # short of the cut) and covers/sends to the cut; the cut instant's reading belongs to part B.
                a_end = start + timedelta(minutes=sp.get("part_a_minutes", sp["at_minutes"]))
                out.append(DayRun(site, story.day, story.offset, name, start, a_end,
                                  at_day(sp["first_received_at"], D) + late, c.get("assess", "build"),
                                  {"scenario_id": a["scenario_id"], "scenario_version": a["scenario_version"]}, None,
                                  None, a.get("note", c.get("note", "")), story.known_at,
                                  cut if a_end != cut else None, story.kind))
                out.append(DayRun(site, story.day, story.offset, sp["kind"], cut, end,
                                  at_day(b["received_at"], D) + late, b.get("assess", "build"),
                                  {"scenario_id": b["scenario_id"], "scenario_version": b["scenario_version"]}, None,
                                  None, b.get("note", ""), story.known_at, None, story.kind))
                continue
            out.append(DayRun(site, story.day, story.offset, name, start, end,
                              at_day(c["received_at"], D) + late, c.get("assess", "build"),
                              {"scenario_id": c["scenario_id"], "scenario_version": c["scenario_version"]}, None, None,
                              c.get("note", ""), story.known_at, None, story.kind))
    # DD1a1-R5 edge rule: the story run is sent unchanged; each complement is sent on [start, covers_end or end), so
    # where two complements meet the earlier ends exclusive and the shared 21:00Z day edge goes to the later day,
    # and it leaves out any instant the story run sends (a Cold complement starts after the story's emitted end).
    owned = ((iso(story.start), iso(story.end)),)
    out = [replace(out[0], seam=len(out) > 1)] + [
        replace(r, emit_until=r.covers_end or r.end, owned=owned, seam=True) for r in out[1:]]
    _tiled(site, story.day, D, out)
    return out


def _tiled(site: str, day: str, D: datetime, runs: list[DayRun]) -> None:
    """L0: the runs of one full day tile the local day exactly, no gap and no overlap."""
    lo = D + LOCAL_DAY_START
    hi = lo + timedelta(hours=24)
    cursor = lo
    for r in sorted(runs, key=lambda r: r.start):
        if r.start != cursor:
            raise StoryDaysError("DAY_NOT_TILED", f"{site} {day}: {r.kind} starts {iso(r.start)}, expected {iso(cursor)}")
        cursor = r.covers_end or r.end
    if cursor != hi:
        raise StoryDaysError("DAY_NOT_TILED", f"{site} {day}: the runs end {iso(cursor)}, expected {iso(hi)}")


def resolve(days_doc: dict, S: datetime, *, db_now: datetime | None = None,
            installs: dict[str, datetime] | None = None, revision_boundaries: tuple = ()) -> list[DayRun]:
    """Every day entry of every Site (with its complement runs), validated, in build order (by `received_at`)."""
    runs: list[DayRun] = []
    for site, entries in days_doc["sites"].items():
        if site not in SITES:
            raise StoryDaysError("UNKNOWN_KIND", f"site {site!r} is not one of {SITES}")
        seen: set[str] = set()
        for entry in entries:
            expanded = _expand(days_doc, site, entry, S, tuple(revision_boundaries))
            run = expanded[0]
            if run.day in seen:
                raise StoryDaysError("DUPLICATE_DAY", f"{site} has two entries on {run.day}")
            seen.add(run.day)
            check_mill_side(days_doc, site, run.kind, run.offset)
            runs.extend(expanded)
        check_full_day_chains(days_doc, site, [(r.offset, r.as_kind or r.kind) for r in runs
                                               if r.site == site and r.has_run and not r.complement_of])
    validate(runs, S, db_now=db_now, installs=installs)
    order = sorted(runs, key=lambda r: (r.received_at or (_day_start(r) + timedelta(days=1)), SITES.index(r.site)))
    # DD1a1-R8: one sequence epoch per stream, a maximal run of consecutive built Site-days of one Site (a gateway does
    # not reset at local midnight). The story runs are numbered `day-<n>` in build order, so an isolated day keeps its
    # v1 epoch; a merged stream takes the number of its first story run in build order; each complement takes its
    # Site-day's epoch.
    story = [r for r in order if r.has_run and not r.complement_of]
    number = {(r.site, r.day): n for n, r in enumerate(story, 1)}
    epochs: dict[tuple[str, str], str] = {}
    for site in SITES:
        mine = sorted((r for r in story if r.site == site), key=lambda r: r.day)
        streams: list[list[DayRun]] = []
        for r in mine:
            if streams and _day_start(r) - _day_start(streams[-1][-1]) == timedelta(days=1):
                streams[-1].append(r)
            else:
                streams.append([r])
        for stream in streams:
            if len(stream) > 1:
                for i, r in enumerate(stream):
                    if r.kind == "late":
                        raise StoryDaysError("LATE_IN_STREAM", f"{site} {r.day}: a late day may not join a "
                                                               f"multi-day stream (DD1a1-R8)")
                    if r.kind == "degraded" and i < len(stream) - 1:
                        raise StoryDaysError("BUILT_DAY_AFTER_DEGRADED", f"{site} {r.day}: a degraded day may not "
                                                                         f"have a built day after it (DD1a1-R8)")
            first = min(stream, key=lambda r: number[(r.site, r.day)])
            for r in stream:
                epochs[(r.site, r.day)] = f"day-{number[(first.site, first.day)]}"
    return [replace(r, epoch=epochs[(r.site, r.day)]) if r.has_run else r for r in order]


def _day_start(run: DayRun) -> datetime:
    return datetime.fromisoformat(run.day).replace(tzinfo=timezone.utc)


def validate(runs: list[DayRun], S: datetime, *, db_now: datetime | None = None,
             installs: dict[str, datetime] | None = None, trial_pair: bool = True) -> None:
    kobo = [r for r in runs if r.site == "kobo"] if trial_pair else []
    before = [r for r in kobo if r.kind == "trial-before"]
    after = [r for r in kobo if r.kind == "trial-after"]
    if kobo and not (len(before) == 1 and len(after) == 1 and after[0].offset == before[0].offset + 1):
        raise StoryDaysError("TRIAL_PAIR_INVALID", "Kobo needs exactly one trial-before on D and one trial-after "
                                                   f"on D+1 (got {[r.day for r in before]} / {[r.day for r in after]})")
    shared: dict[datetime, DayRun] = {}
    for r in runs:
        if r.has_run and r.received_at in shared:
            # each run's acceptance is counted by its `received_at` (`_publish_and_accept`), so two runs may not share one
            raise StoryDaysError("DUPLICATE_RECEIVED_AT", f"{r.site} {r.day} and {shared[r.received_at].site} "
                                                          f"{shared[r.received_at].day} are both received "
                                                          f"{iso(r.received_at)}")
        if r.has_run:
            shared[r.received_at] = r
        if r.offset < -BOARD_WINDOW_DAYS:
            raise StoryDaysError("OUTSIDE_BOARD_WINDOW", f"{r.site} {r.day} is earlier than S-{BOARD_WINDOW_DAYS}d")
        if installs and r.site in installs and r.has_run and r.start < installs[r.site] + INSTALL_LEAD:
            raise StoryDaysError("DAY_BEFORE_INSTALL", f"{r.site} {r.day} starts {iso(r.start)}, less than "
                                                       f"{INSTALL_LEAD} after install {iso(installs[r.site])}")
        known_floor = installs[r.site] + KNOWLEDGE_AFTER_INSTALL if installs and r.site in installs else None
        if known_floor and r.has_run and r.known_at is not None and r.known_at < known_floor:
            raise StoryDaysError("DAY_BEFORE_INSTALL", f"{r.site} {r.day} knows its Foundation at "
                                                       f"{iso(r.known_at)}, before install + {KNOWLEDGE_AFTER_INSTALL}")
        if db_now is not None and r.has_run and r.received_at > db_now - PAST_MARGIN:
            raise StoryDaysError("DAY_NOT_IN_PAST", f"{r.site} {r.day} is received {iso(r.received_at)}, not "
                                                    f"before DB now - {PAST_MARGIN} ({iso(db_now)})")


#: DD1a2-R Q6: `prepare --baseline`. B-22 is the build; B-16 is the owner's fallback if the rehearsal measures the whole
#: prepare over 3 h (`owner-build-time-2026-11-06`). Story days before the baseline (S-28, S-21) stay in both.
BASELINE_FROM = {"b22": -20, "b16": -14}
BASELINE_TO = 1


def apply_baseline(days_doc: dict, S: datetime, baseline: str = "b22") -> dict:
    """The day list for `baseline`. B-16 drops every entry whose resolved offset (an EV Tuesday after
    `weekday_offset`) lies in [S-20, S-15]; B-22 is the list as it stands."""
    if baseline not in BASELINE_FROM:
        raise StoryDaysError("UNKNOWN_BASELINE", f"baseline {baseline!r} is not one of {sorted(BASELINE_FROM)}")
    lo, hi = BASELINE_FROM["b22"], BASELINE_FROM[baseline]
    return {**days_doc, "baseline": baseline,
            "sites": {site: [e for e in entries if not lo <= weekday_offset(site, S, day_offset(e["day"])) < hi]
                      for site, entries in days_doc["sites"].items()}}


def uncovered_weekdays(days_doc: dict, S: datetime, baseline: str = "b22") -> dict[str, list[str]]:
    """R1: the ruled weekdays of a one-weekday Site inside the baseline that no entry lands on. Reported, never moved."""
    out = {}
    for site, weekday in SITE_WEEKDAY.items():
        held = {weekday_offset(site, S, day_offset(e["day"])) for e in days_doc["sites"].get(site, [])}
        out[site] = [(S + timedelta(days=n)).date().isoformat()
                     for n in range(BASELINE_FROM[baseline], BASELINE_TO + 1)
                     if (S + timedelta(days=n)).weekday() == weekday and n not in held]
    return out


def from_payload(rows: list[dict]) -> list[DayRun]:
    def t(v):
        return None if v is None else datetime.fromisoformat(v.replace("Z", "+00:00"))

    return [DayRun(**{**r, "start": t(r["start"]), "end": t(r["end"]), "received_at": t(r["received_at"]),
                           "known_at": t(r.get("known_at")), "covers_end": t(r.get("covers_end")),
                           "emit_until": t(r.get("emit_until")),
                           "owned": tuple(tuple(p) for p in r.get("owned") or ())})
            for r in rows]


def plan_add_day(days_doc: dict, current: list[DayRun], site: str, kind: str, S: datetime, db_now: datetime, *,
                 day: str | None = None, as_kind: str | None = None, delivered_days: set[str] = frozenset(),
                 installs: dict[str, datetime] | None = None) -> DayRun:
    """The one entry `add-day` appends (sheet U4), live on real time: `received_at` and the Foundation knowledge
    are DB now; the run interval is the kind's on its day. Refuses with a `StoryDaysError` code; writes nothing."""
    if site not in SITES:
        raise StoryDaysError("UNKNOWN_KIND", f"site {site!r} is not one of {SITES}")
    kinds = days_doc["kinds"].get(site, {})
    if kind not in kinds:
        raise StoryDaysError("UNKNOWN_KIND", f"{site} kind {kind!r} is not one of {sorted(kinds)}")
    if kind not in ADD_DAY_KINDS[site]:
        raise StoryDaysError("PREPARE_ONLY_KIND", f"{site} kind {kind!r} carries work rows or Actions; add-day takes "
                                                  f"only {ADD_DAY_KINDS[site]}")
    mine = [r for r in current if r.site == site]
    # DD1a2-R (R4 FILL-1): a planned `missing` day holds no run and is fillable live
    held = [r for r in mine if r.has_run or kind == "missing"]
    step = 7 if site in SITE_WEEKDAY else 1  # the next free ruled weekday
    offset = weekday_offset(site, S, day_offset(day) if day else (max(r.offset for r in mine) + step if mine else 0))
    D = S + timedelta(days=offset)
    date = D.date().isoformat()
    if date in delivered_days:
        raise StoryDaysError("DAY_HAS_EVIDENCE", f"{site} {date} already holds delivered evidence (append-only)")
    if any(r.day == date for r in held):
        raise StoryDaysError("DUPLICATE_DAY", f"{site} already has a {next(r.kind for r in held if r.day == date)} "
                                              f"entry on {date}")
    if offset < -BOARD_WINDOW_DAYS:
        raise StoryDaysError("OUTSIDE_BOARD_WINDOW", f"{site} {date} is earlier than S-{BOARD_WINDOW_DAYS}d")
    check_mill_side(days_doc, site, kind, offset)
    if site == "kobo" and kinds[kind].get("complement"):
        after = next((r for r in mine if r.kind == "trial-after"), None)
        if after is not None and offset == after.offset + 1:
            raise StoryDaysError("FULL_DAY_AFTER_TRIAL", f"{site} {date}: a full day here starts its night inside the "
                                 f"trial's later day and takes the trial off Verified; use --kind normal (DD1a2-R3)")
    if site == "kobo" and any(r.kind == "late" and abs(r.offset - offset) == 1 for r in mine):
        # DD1a2-R Q4: `resolve` refuses this in a calendar (DD1a1-R8); add-day would skip it by minting its own epoch
        raise StoryDaysError("LATE_IN_STREAM", f"{site} {date} is next to a late day; a late day may not join a "
                                               f"multi-day stream (DD1a1-R8)")
    entry = {"day": f"S{offset:+d}d", "kind": kind}
    if kind == "late" and "scenario_id" not in kinds["late"]:
        entry["as"] = as_kind or "normal"
    planned = _entry(days_doc, site, entry, S)
    if D.date() > db_now.date() or (planned.end is not None and planned.end > db_now - PAST_MARGIN):
        raise StoryDaysError("DAY_NOT_IN_PAST", f"{site} {date} ends after DB now - {PAST_MARGIN} ({iso(db_now)})")
    if planned.has_run:
        epochs = [int(r.epoch.split("-")[1]) for r in current if r.epoch]
        planned = DayRun(**{**planned.__dict__, "received_at": db_now, "known_at": db_now,
                            "epoch": f"day-{max(epochs, default=0) + 1}",
                            "assess": "tick"})
    validate([planned], S, installs=installs, trial_pair=False)
    return planned


def plan_add_runs(days_doc: dict, current: list[DayRun], site: str, kind: str, S: datetime, db_now: datetime, *,
                  day: str | None = None, as_kind: str | None = None, delivered_days: set[str] = frozenset(),
                  installs: dict[str, datetime] | None = None) -> list[DayRun]:
    """DD1a2-R Q8.3: every run `add-day` delivers. `plan_add_day`'s refusals, then a full-day kind expands through
    `_expand` into its runs in source-time order, each received at DB now in that order (one second apart: a run's
    acceptance is counted by its `received_at`), with readings at story time. The day must have ended in real time."""
    planned = plan_add_day(days_doc, current, site, kind, S, db_now, day=day, as_kind=as_kind,
                           delivered_days=delivered_days, installs=installs)
    if not planned.has_run or not days_doc["kinds"][site][kind].get("complement"):
        return [planned]
    entry = {"day": f"S{planned.offset:+d}d", "kind": kind}
    runs = sorted(_expand(days_doc, site, entry, S), key=lambda r: r.start)
    last = max(r.covers_end or r.end for r in runs)
    if last > db_now - PAST_MARGIN:
        raise StoryDaysError("DAY_NOT_IN_PAST", f"{site} {planned.day} ends {iso(last)}, after DB now - {PAST_MARGIN} "
                                                f"({iso(db_now)})")
    return [replace(r, received_at=db_now + timedelta(seconds=n), known_at=db_now, epoch=planned.epoch, assess="tick")
            for n, r in enumerate(runs)]
