# FIX-W401 packet: clock fixture

Task: clock audit rank 1 (FIX-W301-review-and-clock-audit.md). Test-only.

Fix: `backend/tests/test_w401_site_indexes_postgres.py` `test_pending_link_and_missing_source_keep_gap` read at fixed
POSITIVE_NOW+1min while the reselection was stamped with real `clock_timestamp()`; after 2026-11-01T01:01Z it became
invisible. It now reads at `max(POSITIVE_NOW, _db_now(runner)) + 1 min` (the idiom at :333/:400).

Diagnostic (not a fix): `test_w301_estate_index_postgres.py::test_cold_revision_waits_for_its_selected_assessment`
gains `assert set(moved) <= set(old)` before the loop, so the rare KeyError explains itself if it recurs.

Checks: w401 file 5 passed (154 s); w301 file 20 passed (580 s); check-all result in the report.
check-all: All 11 guards passed.
