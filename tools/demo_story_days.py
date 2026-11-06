"""DEMO-SPARSE: the sparse story calendar (`backend/conversions/demo-story-days-v1.json`) resolved to a build order.

Build sheet `AssetOpsV1-plan2/.agent/build-sheet-DEMO-SPARSE.md` sections 2 and 3 U2. A day list names, per Site,
the story days that carry a registered Lab run (and the named `missing` days that carry none). Day offsets
`S[+-]Nd` are relative to the story day S; each kind's times `D[+-]Nd HH:MM` (UTC) are relative to the entry's day.
`resolve` returns every entry as a `DayRun`, ordered by `received_at` (the build order; a `missing` day has no
delivery and sorts at its day's end), with one `sequence_epoch` `day-<n>` per Site-day (DD1a1-R5), numbered by its
story run in that order and shared by the day's complement runs.

Nothing here reads the wall clock: the caller passes S, the DB clock and the install instants.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEFAULT_FILE = Path(__file__).resolve().parents[1] / "backend" / "conversions" / "demo-story-days-v1.json"
#: DD-1a1 (DD1a1-R Q7): full-day story days. Each Kobo / Cold kind lists its `complement`, so one entry expands into
#: its story run plus the steady runs (and named placeholders) that tile the Site's local day [00:00, 24:00).
#: `prepare --days` takes it; DD-1a2 builds the B-22 list on it and makes it the default.
V2_FILE = DEFAULT_FILE.with_name("demo-story-days-v2.json")
SITES = ("kobo", "cold", "ev")
SITE_CODE = {"kobo": "KOBO-001", "cold": "COLD-LAB-001", "ev": "EV-LAB-001"}
CODE_SITE = {v: k for k, v in SITE_CODE.items()}
BOARD_WINDOW_DAYS = 30
INSTALL_LEAD = timedelta(hours=1)
#: Q1 ruling: the re-timed demo configuration is known at install + 30 min; every run knows it.
KNOWLEDGE_AFTER_INSTALL = timedelta(minutes=30)
PAST_MARGIN = timedelta(minutes=5)
#: Kinds `add-day` may append (sheet U4); trial-*, failure and fault carry work rows and Actions (prepare only).
ADD_DAY_KINDS = {"kobo": ("normal", "overuse", "overcast", "late", "missing", "degraded"),
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

    @property
    def has_run(self) -> bool:
        return self.received_at is not None

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


def _entry(doc: dict, site: str, entry: dict, S: datetime) -> DayRun:
    kinds = doc["kinds"].get(site, {})
    kind = entry.get("kind")
    if kind not in kinds:
        raise StoryDaysError("UNKNOWN_KIND", f"{site} kind {kind!r} is not one of {sorted(kinds)}")
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


def _expand(doc: dict, site: str, entry: dict, S: datetime) -> list[DayRun]:
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
    if isinstance(comp, dict):
        c = kinds[comp["kind"]]
        for hour in comp["hours"]:
            start = at_day(hour, D)
            end = start + timedelta(minutes=c["interval_minutes"])
            out.append(DayRun(site, story.day, story.offset, comp["kind"], start, end, end + late, c.get("assess", "build"),
                              {"scenario_id": c["scenario_id"], "scenario_version": c["scenario_version"]}, None, None,
                              c.get("note", ""), story.known_at, start + timedelta(minutes=c["covers_minutes"]),
                              story.kind))
    else:
        for name in comp:
            c = kinds[name]
            out.append(DayRun(site, story.day, story.offset, name, at_day(c["start"], D), at_day(c["end"], D),
                              at_day(c["received_at"], D) + late, c.get("assess", "build"),
                              {"scenario_id": c["scenario_id"], "scenario_version": c["scenario_version"]}, None, None,
                              c.get("note", ""), story.known_at, None, story.kind))
    # DD1a1-R5 edge rule: the story run is sent unchanged; each complement is sent on [start, covers_end or end), so
    # where two complements meet the earlier ends exclusive and the shared 21:00Z day edge goes to the later day,
    # and it leaves out any instant the story run sends (a Cold complement starts after the story's emitted end).
    owned = ((iso(story.start), iso(story.end)),)
    out = [out[0]] + [replace(r, emit_until=r.covers_end or r.end, owned=owned) for r in out[1:]]
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
            installs: dict[str, datetime] | None = None) -> list[DayRun]:
    """Every day entry of every Site (with its complement runs), validated, in build order (by `received_at`)."""
    runs: list[DayRun] = []
    for site, entries in days_doc["sites"].items():
        if site not in SITES:
            raise StoryDaysError("UNKNOWN_KIND", f"site {site!r} is not one of {SITES}")
        seen: set[str] = set()
        for entry in entries:
            expanded = _expand(days_doc, site, entry, S)
            run = expanded[0]
            if run.day in seen:
                raise StoryDaysError("DUPLICATE_DAY", f"{site} has two entries on {run.day}")
            seen.add(run.day)
            runs.extend(expanded)
    validate(runs, S, db_now=db_now, installs=installs)
    order = sorted(runs, key=lambda r: (r.received_at or (_day_start(r) + timedelta(days=1)), SITES.index(r.site)))
    # DD1a1-R5: one sequence epoch per Site-day stream. The story runs are numbered `day-<n>` in build order (so a
    # v1 list, which has only story runs, keeps its epochs); each complement takes its Site-day's story epoch.
    epochs: dict[tuple[str, str], str] = {}
    for r in order:
        if r.has_run and not r.complement_of:
            epochs[(r.site, r.day)] = f"day-{len(epochs) + 1}"
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
    step = 7 if site in SITE_WEEKDAY else 1  # the next free ruled weekday
    offset = weekday_offset(site, S, day_offset(day) if day else (max(r.offset for r in mine) + step if mine else 0))
    D = S + timedelta(days=offset)
    date = D.date().isoformat()
    if date in delivered_days:
        raise StoryDaysError("DAY_HAS_EVIDENCE", f"{site} {date} already holds delivered evidence (append-only)")
    if any(r.day == date for r in mine):
        raise StoryDaysError("DUPLICATE_DAY", f"{site} already has a {next(r.kind for r in mine if r.day == date)} "
                                              f"entry on {date}")
    if offset < -BOARD_WINDOW_DAYS:
        raise StoryDaysError("OUTSIDE_BOARD_WINDOW", f"{site} {date} is earlier than S-{BOARD_WINDOW_DAYS}d")
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
