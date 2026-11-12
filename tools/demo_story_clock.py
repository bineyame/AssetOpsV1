"""DD1b1-R Q1, Q2: the story clocks of the Cold and EV children in a demo prepare. Add-day never uses them.

One rule per day, from the day's own `received_at`:

    worker       received_at + 5 min (assessment runs, selections, Findings)
    work store   received_at + 6 min, then + 1 s per command (cases, records, events, visits, plans)
    domain store received_at + 10 min, then + 1 s per command (Action `raised_at`, Action, links, intent)

Two command clocks, not one: a case completed before the Action was agreed is known before it, so the lifecycle
skips its APPLIED as illegal from OPEN and the thread reads "Action agreed", not "Change made" (DD1b1-R Q3).

The swaps are process-local and live here; production composition passes no clock.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta

from assetops_backend.prepare_clock import require_prepare_database

WORKER_AFTER = timedelta(minutes=5)
WORK_AFTER = timedelta(minutes=6)
ACTION_AFTER = timedelta(minutes=10)
STEP = timedelta(seconds=1)
#: DATA-13 (D-17N.4, C17): the Cold, EV and Kisiwa story Actions are due this long after they are raised. 14 days keeps
#: Kisiwa's (raised S-5d) in the future through a demo up to S+8d.
STORY_ACTION_DUE = timedelta(days=14)


def story_action_due(raised: datetime) -> datetime:
    """DATA-13: a story Action's `due_at` (within the domain service's 365-day due limit)."""
    return raised + STORY_ACTION_DUE


class StepClock:
    """Each read returns the next instant: `start`, then one step later, and so on."""

    def __init__(self, start: datetime) -> None:
        self.start = start
        self.last: datetime | None = None

    def __call__(self) -> datetime:
        self.last = self.start if self.last is None else self.last + STEP
        return self.last


def worker_instant(url: str, received_at: datetime) -> datetime:
    """The day's worker instant; switching a story clock on is refused outside a prepare or test database."""
    require_prepare_database(url)
    return received_at + WORKER_AFTER


@contextmanager
def story_commands(url: str, received_at: datetime) -> Iterator[tuple[StepClock, StepClock]]:
    """The work and domain stores built inside this block run on their story clocks; yields (work, domain). The caller
    points the Action's `raised_at` at the domain clock's first read. Stops if work-store time reaches the Action."""
    from assetops_backend.work import composition

    require_prepare_database(url)
    work, domain = StepClock(received_at + WORK_AFTER), StepClock(received_at + ACTION_AFTER)
    saved = composition.build_work_store, composition.build_domain_intent_store

    def clocked(build, clock):
        def built(database_url):
            store = build(database_url)
            store.test_db_clock_override = clock
            return store
        return built

    composition.build_work_store = clocked(saved[0], work)
    composition.build_domain_intent_store = clocked(saved[1], domain)
    try:
        yield work, domain
    finally:
        composition.build_work_store, composition.build_domain_intent_store = saved
    if work.last is not None and work.last >= domain.start:
        raise SystemExit(f"STORY_CLOCK_ORDER: the last work-store instant {work.last} is not before the Action "
                         f"instant {domain.start}.")
