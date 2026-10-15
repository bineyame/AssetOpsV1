"""Action event kinds, the reduced application state, exact-history selectors and the SYSTEM demo actor (S6-01a).

`D-2026-10-14-action-lifecycle-and-policy-application` with `D-2026-10-15-s601-action-store-and-ui`:

- An Action exists from acceptance, so it has no PROPOSED state. Events reduce in `(recorded_at, id)` order.
- ACCEPTED -> application PENDING. APPLIED -> APPLIED (only with a committed Foundation change). FAILED is an
  attempt: it records a failed application but leaves the application PENDING and never reverts APPLIED, even if
  it is recorded later. OBSERVED is state-neutral.
- No event infers verification or human approval: the outcome stays PENDING (S6-02 owns verification).
- `event_id` selects the exact event and its ordered prefix; `recorded_at` selects every event recorded through
  that server instant (ties included). Both together are a typed conflict. Neither is an `occurred_at` cutoff.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Sequence
from urllib.parse import quote
from uuid import UUID

ACCEPTED, APPLIED, FAILED, OBSERVED = "ACCEPTED", "APPLIED", "FAILED", "OBSERVED"
EVENT_KINDS = (ACCEPTED, APPLIED, FAILED, OBSERVED)
COMMANDS = ("ACCEPT", "APPLY", "OBSERVE")
OBSERVATION_CODE = "DEMO_REVIEW_NOTE"

# Reduced application states.
NONE_AT_CUTOFF = "NONE_AT_CUTOFF"
PENDING = "PENDING"

# The single transition table: (state, event kind) -> next state. A pair absent here leaves the state unchanged.
TRANSITIONS: dict[tuple[str, str], str] = {
    (NONE_AT_CUTOFF, ACCEPTED): PENDING,
    (PENDING, APPLIED): APPLIED,
}


@dataclass(frozen=True)
class SystemDemoActor:
    """The stable service principal of every SYSTEM demonstration command (never a human author)."""

    actor_kind: str = "SYSTEM"
    actor_id: str = "service:assetops-action-demonstration"
    source_channel: str = "SYSTEM_DEMONSTRATION_API"
    triggering_service: str = "assetops-backend/action-api"
    label: str = "SYSTEM demonstration"

    def basis(self, fixture_id: str, command: str) -> str:
        return (f"SYSTEM_DEMONSTRATION_CAPABILITY: server-issued grant for fixture {fixture_id}, command {command}; "
                "no verified human principal exists, so no operator approval is recorded")


SYSTEM_DEMO = SystemDemoActor()


def order_key(event: dict[str, Any]) -> tuple[datetime, str]:
    return (event["recorded_at"], str(event["id"]))


def ordered(events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(events, key=order_key)


def reduce(events: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """The application state after `events` (already a server-ordered prefix)."""
    state = NONE_AT_CUTOFF
    attempts = failed = 0
    last_failure = None
    accepted_at = applied_at = None
    for event in ordered(events):
        kind = event["kind"]
        state = TRANSITIONS.get((state, kind), state)
        if kind == ACCEPTED and accepted_at is None:
            accepted_at = event["recorded_at"]
        if kind == APPLIED and applied_at is None:
            applied_at = event["recorded_at"]
        if kind in (APPLIED, FAILED):
            attempts += 1
        if kind == FAILED:
            failed += 1
            last_failure = {"event_id": str(event["id"]), "failure_code": event["failure_code"],
                            "recorded_at": event["recorded_at"]}
    return {"application": state, "accepted_at": accepted_at, "applied_at": applied_at,
            "application_attempts": attempts, "failed_attempts": failed, "last_failure": last_failure,
            "outcome": {"state": "PENDING", "statement": "No verification exists yet; nothing is claimed about "
                                                          "an effect, a saving or approval."}}


class SelectorConflict(Exception):
    pass


class UnknownEvent(Exception):
    pass


@dataclass(frozen=True)
class Selector:
    kind: str  # "LATEST" | "EVENT_ID" | "RECORDED_AT"
    event_id: UUID | None = None
    recorded_at: datetime | None = None

    def query(self) -> str:
        if self.kind == "EVENT_ID":
            return f"?event_id={self.event_id}"
        if self.kind == "RECORDED_AT":
            return f"?recorded_at={quote(self.recorded_at.isoformat(), safe='')}"  # type: ignore[union-attr]
        return ""

    def wire(self) -> dict[str, Any]:
        return {"kind": self.kind, "event_id": None if self.event_id is None else str(self.event_id),
                "recorded_at": None if self.recorded_at is None else self.recorded_at.isoformat()}


def selector(event_id: UUID | None, recorded_at: datetime | None) -> Selector:
    if event_id is not None and recorded_at is not None:
        raise SelectorConflict("Choose either event_id or recorded_at, not both.")
    if event_id is not None:
        return Selector("EVENT_ID", event_id=event_id)
    if recorded_at is not None:
        if recorded_at.tzinfo is None:
            raise ValueError("recorded_at must carry a time zone offset.")
        return Selector("RECORDED_AT", recorded_at=recorded_at)
    return Selector("LATEST")


def select(events: Sequence[dict[str, Any]], chosen: Selector) -> list[dict[str, Any]]:
    """The `(recorded_at, id)`-ordered prefix the selector names."""
    rows = ordered(events)
    if chosen.kind == "EVENT_ID":
        for index, event in enumerate(rows):
            if str(event["id"]) == str(chosen.event_id):
                return rows[: index + 1]
        raise UnknownEvent(str(chosen.event_id))
    if chosen.kind == "RECORDED_AT":
        return [e for e in rows if e["recorded_at"] <= chosen.recorded_at]
    return rows
