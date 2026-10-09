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
