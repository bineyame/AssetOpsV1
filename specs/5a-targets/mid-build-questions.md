# 5a mid-build questions (RULES §4 item 7)

A question about something the spec did not fix stops only the affected part. Write it here (Q1, Q2 ...): the
unit, the section, what is stopped, what is built, and what you ask. The Architect rules in `rulings.md`. Record
the count in the packet; a count above zero is a spec-template defect to fix.

Count: **1** (reset at spec rev 2, after handshake round 1).

## Q1 (unit 1, spec §6 test 10): DS1b parity cannot live in `backend/tests`

- **Stopped:** test 10 only. **Built:** tests 1 and 2, `lines.py`, the fixture (its step 1 was produced from DS1b's
  `build_records` output for the October `plan` records and matches §5's values).
- **Why:** test 10 calls `build_records(view, generate_history(view))`. From `backend/tests/test_5a_targets.py` that
  is `from assetops_simulator...`, which `tools/checks/dependency-direction.ps1` (product-to-simulator) refuses for
  every file under `backend/`, tests included, with no allowlist. check-all failed on it at the first run. DS1b's
  golden (`simulator/tests/world/golden/records_v1.json`) holds digests only, so no file read can stand in.
- **Ask:** where the parity test lives. Builder's suggested default, not applied: a new
  `simulator/tests/world/test_5a_fixture_parity.py` that reads `backend/tests/fixtures/targets_lakeside.json` by path
  (a file read, no import across the seam) and compares step 1's parsed records with `build_records` for those IDs.
  This adds a file outside spec §7 question 8's list, so it needs the ruling.
