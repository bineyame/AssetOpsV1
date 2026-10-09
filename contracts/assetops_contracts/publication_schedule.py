"""The Lab-private publication schedule's neutral shape (S2-01c).

`D-2026-10-09-s2-simulated-publication-clock` and
`D-2026-10-09-s2-publication-clock-post-run-release`. The host persists this
schedule (`host/publication_schedule.py`); the gated Lab API reads it through
the execution port. Lab-private: nothing here enters a V3 envelope, a Batch V2
or a GatewayDiagnosticsV1. `scheduled_release_at` and `clock_instant` are on
the run's virtual publication clock; a released report's actual V3
`published_at` is the gateway's own stamp, read from the Stage.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone

INSTANT = "%Y-%m-%dT%H:%M:%SZ"
PENDING = "PENDING"
RELEASED = "RELEASED"

#: Ordinary (undelayed) publication of a RUN_VIRTUAL run, against the world
#: (`D-2026-10-09-s2-publication-gap-and-batch-boundary`).
ORDINARY_NOT_STARTED = "NOT_STARTED"  # no world boundary reached yet
ORDINARY_CONTIGUOUS = "CONTIGUOUS"  # admitted through the reached boundary; world running
ORDINARY_COMPLETE = "COMPLETE"  # admitted through the world's last boundary
ORDINARY_INCOMPLETE = "INCOMPLETE"  # a reached boundary is not yet admitted
ORDINARY_TERMINAL_GAP = "TERMINAL_GAP"  # the gateway clock passed an unadmitted boundary
ORDINARY_GAP_STATES = frozenset({ORDINARY_INCOMPLETE, ORDINARY_TERMINAL_GAP})


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
    #: The last reached world boundary whose undelayed reports the gateway
    #: admitted at that boundary's own instant (ordered publication). Later
    #: passes start after it; absent in a schedule written before it existed.
    admitted_through: str | None = None
    #: How many world boundaries the world had completed when the schedule was
    #: last written; None in a schedule written before it existed (then the
    #: gap check compares the two instants alone, failing closed).
    world_boundaries_completed: int | None = None
    #: The first ordinary boundary the gateway refused because its clock had
    #: already passed it (`PUBLICATION_INSTANT_PASSED`): a permanent gap for
    #: this run. Nothing later is admitted; recovery is a new run.
    ordinary_stopped_at: str | None = None

    def ordinary_publication(self) -> str:
        """Where ordinary publication stands against the world it observed."""
        if self.ordinary_stopped_at is not None:
            return ORDINARY_TERMINAL_GAP
        if self.world_reached_instant is None or self.world_boundaries_completed == 0:
            return ORDINARY_NOT_STARTED
        if self.admitted_through is None or self.admitted_through < self.world_reached_instant:
            return ORDINARY_INCOMPLETE
        return ORDINARY_COMPLETE if self.world_complete else ORDINARY_CONTIGUOUS

    def ordinary_gap(self) -> bool:
        """A reached boundary whose ordinary readings the gateway never admitted."""
        return self.ordinary_publication() in ORDINARY_GAP_STATES

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
