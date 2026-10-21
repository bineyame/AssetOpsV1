"""W4-02 unit 4 step 2 (pure): Site-local hour windows for the mini-depth inputs (closure 1 Q4, closure 4 S8)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from assetops_backend.mini_depth.inputs import INVALID_WINDOW, MiniInputsRefused, local_day_of, local_hour, local_noon


def test_local_noon_first_occurrence_and_refusals() -> None:
    w = local_noon(date(2026, 10, 6), "Africa/Nairobi")
    assert (w.start, w.end) == (datetime(2026, 10, 6, 9, tzinfo=timezone.utc),
                                datetime(2026, 10, 6, 10, tzinfo=timezone.utc))
    assert local_day_of(w, "Africa/Nairobi") == date(2026, 10, 6)
    # An ambiguous local hour takes the first offset occurrence (EDT, -04:00).
    amb = local_hour(date(2026, 11, 1), 1, "America/New_York")
    assert amb.start == datetime(2026, 11, 1, 5, tzinfo=timezone.utc) and amb.end - amb.start == timedelta(hours=1)
    # A nonexistent local hour and a missing/unknown zone refuse INVALID_WINDOW (never a UTC guess).
    for args in ((date(2026, 3, 8), 2, "America/New_York"), (date(2026, 10, 6), 12, ""),
                 (date(2026, 10, 6), 12, "Mars/Olympus")):
        with pytest.raises(MiniInputsRefused) as refused:
            local_hour(*args)
        assert refused.value.code == INVALID_WINDOW
