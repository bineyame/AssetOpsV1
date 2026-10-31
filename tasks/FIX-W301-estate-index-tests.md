# FIX-W301 Estate index test fixtures

Status: **in_review**. Test-fixture fix only; no product code changed. Packet: [.agent/FIX-W301-packet.md](../.agent/FIX-W301-packet.md).

## Scope

`test_historical_minigrid_outstanding_marker_page_two_keeps_basis` in `backend/tests/test_w301_estate_index_postgres.py`
failed because its `LATE` step used a fixed decision instant (2026-10-31T08:00Z) that the real clock passed on 2026-10-31.
Acceptance: the file passes alone, twice in a row, with no wall-clock dependence on a fixed date.
