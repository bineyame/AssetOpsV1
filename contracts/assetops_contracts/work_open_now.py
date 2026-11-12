"""The Work lists' "open now" counts (OPEN-NOW, `.agent/architect-sequence-client-scope-2026-11-11.md`).

A Work list shows the items in its date window. `open_now` answers a different question on the same response: how
many requests and incidents are open at the read's cutoff, whatever their dates. It obeys the cutoff (`known_at`)
and the Site scope of the list it rides on; it never obeys the window.

This module holds the shape and the one open rule; reading a store belongs to the backend.
"""

from __future__ import annotations

from dataclasses import dataclass

#: The reduced case states that count as open, for incidents and maintenance requests alike.
OPEN_STATES = frozenset({"OPEN", "IN_PROGRESS"})

#: The wire keys of `open_now`, in display order (incidents first, as the Work navigation orders them).
OPEN_NOW_KEYS = ("incidents", "requests", "line")


@dataclass(frozen=True)
class OpenNowCounts:
    """Open incidents and open maintenance requests at one cutoff, over one scope."""

    incidents: int
    requests: int

    def __post_init__(self) -> None:
        for name in ("incidents", "requests"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"open_now {name} must be a non-negative integer")

    def __add__(self, other: "OpenNowCounts") -> "OpenNowCounts":
        return OpenNowCounts(self.incidents + other.incidents, self.requests + other.requests)

    def wire(self, line: str) -> dict[str, int | str]:
        """The response object: the two counts and the server's own sentence for them."""
        return {"incidents": self.incidents, "requests": self.requests, "line": line}
