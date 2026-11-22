"""DD4a (D-DD.85): a room receives produce in lots of at most 40 crates at 08:00 and 16:00 local, one IN per
receiving time; the named batches are received in lots from 27 Sep; a month that cannot be placed stops the build."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone

import pytest

from assetops_simulator.world import exports_cold

from .books_support import COLD, built, files_by_name

ZONE = timezone(timedelta(hours=3))


def _ledger():
    return list(files_by_name(built()[3])[f"{COLD}.profile.cold-storage-ledger.csv"].records)


def _ins():
    return [r for r in _ledger() if r["body"]["direction"] == "IN"]


def test_every_in_is_one_lot_at_a_free_receiving_time():
    ins = _ins()
    assert ins
    times = Counter((r["site_code"], r["clocks"]["occurred_at"]) for r in ins)
    assert max(times.values()) == 1, [k for k, n in times.items() if n > 1][:5]
    assert max(int(r["quantity"]["value"]) for r in ins) <= exports_cold.BATCH_CRATES
    assert {datetime.fromisoformat(r["clocks"]["occurred_at"]).timetz().isoformat() for r in ins} == {
        "08:00:00+03:00", "16:00:00+03:00"}


def test_named_batches_are_received_in_lots():
    lots = sorted((r["body"]["batch_ref"], r["clocks"]["occurred_at"][:16], int(r["quantity"]["value"]))
                  for r in _ins() if r["body"]["batch_ref"].startswith("B-"))
    assert lots == [
        ("B-1029", "2026-09-27T16:00", 20), ("B-1029", "2026-09-28T08:00", 40),
        ("B-1031", "2026-09-30T08:00", 40), ("B-1031", "2026-09-30T16:00", 40), ("B-1031", "2026-10-01T08:00", 40),
        ("B-1034", "2026-09-29T08:00", 40), ("B-1034", "2026-09-29T16:00", 40),
    ]
    ids = [r["source_record_id"] for r in _ins() if r["body"]["batch_ref"].startswith("B-")]
    assert len(ids) == len(set(ids)) == 7  # each lot its own Movement id


def test_a_month_that_cannot_be_placed_stops_the_build():
    # 30 dates x 2 receiving times x 40 crates x 7 days = 16,800 crate-days at most
    with pytest.raises(ValueError, match=r"^EMU_RECEIVING COLD-THIKA 2026-09$"):
        exports_cold._fill("COLD-THIKA", "2026-09", 20000, ZONE, [0], [])
