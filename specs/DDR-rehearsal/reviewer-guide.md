# DDR reviewer guide

Architect (Claude), 2026-11-20, rev 1. Verification review for the checker and the tests; discovery for the store
read (D-DDR.6). Read `spec.md`, `rulings.md`, the runbook, then the diff. Done means every question in spec §7 answers
yes with evidence and every plant below fails its named test.

## What to check, and how

1. **Fixtures by hand (W2).** The board budget's rows, the profile and the expected records match spec §3 cell for
   cell; the expected records are not produced by running the reader; the checker's literals come from spec §3.4 and
   3A3's E2 to E5, not from a run.
2. **Independent gates (D-DDR.3).** Read each gate: it queries its own step's store; none reads another gate's result,
   a file in `$DIR`, or the test's state.
3. **Progress and skips.** Tests 2 to 4 cover every step that leaves a record; each skip names the expected gate.
4. **No code for the layout.** Test 5 and `git diff main...HEAD --stat`: only `rehearsal_check.py`, the store read
   (port, memory, Postgres), the fixtures, the tests, the runbook and the packet.
5. **The runbook.** Sections 7 to 11 exist with spec §6's content; every command in spec §1 appears in it exactly as
   the test runs it; "Erase" renumbered and the intro updated.
6. **Machine rules.** No database created or dropped by code or test outside the pooled `*_test` harness.

## Planted violations (each must fail the named test; the builder shows each failing once, in a scratch copy)

| # | Plant | Fails |
|---|---|---|
| P1 | G3 checks only that records exist (not uploads) | test 4 |
| P2 | G5 accepts any statement | test 3 (no S5) |
| P3 | G8 compares with the latest upload only, not the opening statement | test 3 (no S9) |
| P4 | G6 accepts the latest snapshot | test 3 (no S6) |
| P5 | the checker stops printing after the first failure | test 2 (every line present) |
| P6 | the Kisiwa contribution line written as −65.00 in the fixture | test 1 (the notice missing) |
| P7 | the emulated budget left in the folder | test 3 (G3) and S4's `EXPORT_PATHS_MIXED` |
| P8 | `portfolio_history` unordered | test 6 |
