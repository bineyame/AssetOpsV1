"""The Lab-private publication schedule of a registered run (S2-01c phase 2).

`D-2026-10-09-s2-simulated-publication-clock`. A registered run whose frozen
publication profile declares `RUN_VIRTUAL` publishes through the gateway on a
virtual publication clock. This store is the Lab's half of it:

- the run's virtual publication clock as the Lab last advanced it, the world's
  reached instant and whether the world run has completed;
- every delayed public reading, recorded PENDING with its stable admission key,
  original source instant, scheduled release instant (the delay window's end)
  and the exact public report text, BEFORE anything is sent to the gateway;
- once released, the gateway's answer (message ID, sequence, outcome) and the
  Lab clock instant it was released at.

Everything here is Lab-private. The scheduled release instant and the delay
event that caused it never enter a report, a V3 envelope, a Batch V2 or a
GatewayDiagnosticsV1: the gateway receives only the unchanged public report
text, once it is due, and stamps `published_at` from its own persisted clock.

One JSON document per run under `var/publication-schedules`, replaced
atomically (partial file, then `os.replace`), like the file Stage beside it.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "assetops.lab-publication-schedule"
VERSION = 1
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCHEDULE_ROOT = REPOSITORY_ROOT / "var" / "publication-schedules"
INSTANT = "%Y-%m-%dT%H:%M:%SZ"
PENDING = "PENDING"
RELEASED = "RELEASED"


class ScheduleUnreadable(RuntimeError):
    def __init__(self, run_id: str, detail: str) -> None:
        self.run_id, self.detail = run_id, detail
        super().__init__(f"the publication schedule of {run_id} is unreadable: {detail}")


def parse_instant(text: str) -> datetime:
    """A strict `YYYY-MM-DDTHH:MM:SSZ` instant, or ValueError."""
    if not isinstance(text, str):
        raise ValueError(f"{text!r} is not a UTC instant")
    moment = datetime.strptime(text, INSTANT).replace(tzinfo=timezone.utc)
    if moment.strftime(INSTANT) != text:
        raise ValueError(f"{text!r} is not a canonical UTC instant")
    return moment


@dataclass(frozen=True)
class DelayedReport:
    report_key: str
    device_id: str
    signal_id: str
    source_time: str
    scheduled_release_at: str
    #: The scenario entry that held it: a private Lab cause, never sent.
    delay_event_id: str
    #: The exact public report text the gateway will receive once due.
    report_text: str
    state: str = PENDING
    #: The Lab's virtual publication instant when it was submitted. The V3
    #: `published_at` is the gateway's own stamp, read back from the Stage.
    released_at_clock: str | None = None
    message_id: str | None = None
    sequence: int | None = None
    outcome: str | None = None


@dataclass(frozen=True)
class PublicationSchedule:
    run_id: str
    snapshot_sha256: str
    clock_instant: str | None = None
    world_reached_instant: str | None = None
    world_complete: bool = False
    delayed: tuple[DelayedReport, ...] = field(default_factory=tuple)

    def pending(self) -> tuple[DelayedReport, ...]:
        return tuple(d for d in self.delayed if d.state == PENDING)

    def due(self, instant: str) -> tuple[DelayedReport, ...]:
        moment = parse_instant(instant)
        return tuple(d for d in self.pending() if parse_instant(d.scheduled_release_at) <= moment)

    def keys(self) -> frozenset[str]:
        return frozenset(d.report_key for d in self.delayed)

    def with_delayed(self, added: list[DelayedReport]) -> "PublicationSchedule":
        return replace(self, delayed=self.delayed + tuple(added))

    def released(self, answers: dict[str, dict], clock_instant: str) -> "PublicationSchedule":
        """Mark the reports the gateway answered for as RELEASED, by key."""
        delayed = []
        for item in self.delayed:
            answer = answers.get(item.report_key)
            # Submitted is released, whatever the gateway answered: a HELD
            # report is the gateway's hold to show, not a pending one to resend.
            if item.state == PENDING and answer is not None:
                item = replace(
                    item,
                    state=RELEASED,
                    released_at_clock=clock_instant,
                    message_id=answer.get("message_id"),
                    sequence=answer.get("sequence"),
                    outcome=answer["outcome"],
                )
            delayed.append(item)
        return replace(self, delayed=tuple(delayed))


def schedule_document(schedule: PublicationSchedule) -> dict:
    return {"schema": SCHEMA, "version": VERSION, **asdict(schedule), "delayed": [asdict(d) for d in schedule.delayed]}


def _from_document(run_id: str, document: object) -> PublicationSchedule:
    if not isinstance(document, dict) or document.get("schema") != SCHEMA or document.get("version") != VERSION:
        raise ScheduleUnreadable(run_id, "not a version-1 Lab publication schedule")
    try:
        body = {k: v for k, v in document.items() if k not in ("schema", "version", "delayed")}
        schedule = PublicationSchedule(**body, delayed=tuple(DelayedReport(**d) for d in document["delayed"]))
    except (TypeError, KeyError) as error:
        raise ScheduleUnreadable(run_id, str(error)) from error
    if schedule.run_id != run_id:
        raise ScheduleUnreadable(run_id, f"it names run {schedule.run_id}")
    return schedule


class JsonPublicationSchedules:
    def __init__(self, root: Path = SCHEDULE_ROOT) -> None:
        self._root = Path(root)

    def path(self, run_id: str) -> Path:
        return self._root / f"{run_id}.json"

    def read(self, run_id: str) -> PublicationSchedule | None:
        path = self.path(run_id)
        if not path.is_file():
            return None
        try:
            document = json.loads(path.read_bytes().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ScheduleUnreadable(run_id, str(error)) from error
        return _from_document(run_id, document)

    def write(self, schedule: PublicationSchedule) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        path = self.path(schedule.run_id)
        partial = path.with_name(path.name + ".partial")
        text = json.dumps(schedule_document(schedule), sort_keys=True, indent=1, ensure_ascii=False)
        partial.write_bytes(text.encode("utf-8"))
        os.replace(partial, path)
