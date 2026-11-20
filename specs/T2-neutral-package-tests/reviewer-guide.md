# T2 reviewer guide (rev 2: handshake round 1 folded in)

Standard review (W5). The checks below.

## Scope

The diff holds only these, plus the packet and the finish bookkeeping:
- `tools/checks/neutral_tests.py`;
- `tools/checks/test_select_tests_neutral.py`;
- `tools/check-all.ps1` (three guard lines and one comment);
- `tools/select-tests.py`;
- `backend/TESTING.md`.

## Child processes import this tree (D-T2.2)

1. Read the script: it must set `os.environ["PYTHONPATH"]` as well as `sys.path`.
2. Repeat proof 1 yourself (spec §3): a one-line break in the worktree's `world/history.py`, with main first on
   `PYTHONPATH`. The guard must go red, then green once the edit is reverted.

A guard that passes with the break still in place is a High.

## Anti-vacuity

- Run `--self-test` and read its four cases.
- In a scratch copy, delete `contracts/tests`: the guard must fail with `missing contracts/tests`.
- A floor set below today's counts is fine. A later diff that lowers a floor is a finding.

## No database or slot

`ASSETOPS_TEST_DATABASE_URL` is removed before pytest starts, and nothing waits on a slot.

## select-tests

- `test_select_tests_neutral.py` passes.
- `tools/world_history.py` still gives `mode: full`.
- A markdown file under `simulator/` gives `neutral: false`.

## The packet

It quotes:
- check-all's summary line before and after, showing three more guards;
- the red run that names the guard;
- the same counts for the combined run and the separate runs;
- the guard's timing.
