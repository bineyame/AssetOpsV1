# 3A7 review, commit 1 (discovery, W5)

Reviewer (Claude, fresh, not the author), 2026-11-21. Branch `task/3A7-month-reconciled` head `fc0364d7a` (base
`166942e7d`); diff `166942e7d...fc0364d7a`. Judged against `spec.md` rev 2, `rulings.md` (D-3A7.1 to .13, the
D-SC1.28 split) and D-3A7.14 to .15 (`61ca7a695`, not yet on the branch).

## Summary

- **Verdict: ACCEPT** for commit 1. No High or Medium. Three Lows (docs, a spec gap, state-index conflict), none blocking.
- Honesty holds. Money reads reconciled only when a current statement opens the gate (MATCHED on both headings, each
  against used lines, within the tolerance at `k`) and no covering statement is NOT_MATCHED or NOT_COMPARABLE. No used
  line is never 0. Exact `Decimal` under `EXACT`; no float.
- No served text: no `messages`/`i18n` change, `ReconRefused` carries codes and params only.
- D-3A7.14 is met (service at `structure/reconciliation.py`; `commercial/` imports no `structure`; 3A4 test_12 and 4b
  test_11a pass). D-3A7.15 is met by the constructor port. Commit 2's builder and command are listed below.
- Plants: my own run, 17 of 17 fail named tests. Architecture and workflow checks pass; the guard has no new block.
- Merge with `main` (3A6 merged): code merges cleanly; only `.ai/state/` conflicts. One `main` defect will hit
  commit 2's regression set (residual risk 1).

## Checks run (my output)

- `ASSETOPS_GUARD_PYTHON=<venv python> pwsh -NoProfile -File tools/check-architecture.ps1` (worktree, `fc0364d7a`):
  "Architecture check passed." `tools/check-agent-workflow.ps1`: "Agent workflow check passed."
- Focused tests, no database, `heavy-slot.sh --`, on a `git archive` copy of `fc0364d7a` (PYTHONPATH that copy's
  backend, contracts, simulator; `assetops_backend` resolved there): `test_3a7_reconciliation`, `test_3a4_commercial_months`,
  `test_4b_money_leaves`, `test_3c1a_person_work`, `test_3a1_commercial_service`: 269 passed, 2 failed. Both failures
  were in 4b and came from my copy, which was missing `Docs/demo-sprint/...`. After adding it, 3A7 plus 4b: 73 passed.
- Merge-risk run: `git merge-tree main fc0364d7a` (tree `7c49682f3`; conflicts only in `.ai/state/data.md` and
  `index-2.md`), same five files: **270 passed, 1 failed**,
  `test_3a1_commercial_service::test_no_log_call_in_the_commercial_package` on `commercial/envelope.py` (main's 3A6 r5
  file; see residual risk 1). R7 and R10 hold after main's 3B6 change maps `COLDCHAIN` to `COLD_CHAIN`, because the
  code compares to `MINI_GRID`.
- Plants (my own script, each applied to the scratch copy, the named test run, then reverted; the restore was checked):
  V1, V2 (local status tuple plus QUOTE in 4b's `COST_STATUSES`; R7 fails), V3, V4, V5, V6, V7, V8, V9, V10, V11, V13,
  V14, V16, V17, V18, V20: **each failed** its named test (V3/V4/V9 R3; V5/V6 R2+R9; V7 R2 T6+T10+R7; V8 T9+R4; V10
  T3+R9; V11 R4; V13 R2+T10; V14 R9; V16 R2/R4/R5/R8; V17 tolerance cases; V18 R8; V20 R5). V12, V15, V19 are word
  plants and belong to commit 2.
- I recomputed by hand: 501.50 × 0.01 = 5.015 < 5.02 (NOT_MATCHED); 510.05 − 505.00 = 5.05 ≤ 5.05; T1 fuel allowed
  5.05 on the accounts' base; T4 2.50 ≤ 5.10; T3 7.50 ≤ 10.10.

## Not verified

- **Postgres.** Commit 1 has no Postgres test (Q1 to Q3 are commit 2, D-SC1.28). I wrote a scratch smoke test (upgrade
  to 0068, adapter round-trip, FK on another tenant's Site, the three CHECK values, the triggers). The T1 tripwire
  refused it because a non-git scratch tree is not a pool slot. I did not work around the tripwire, and the brief rules
  out writing into the worktree. So the migration and adapter were checked by reading only: the 0065 refuse-downgrade
  form, the 0005 `ledger_append_only`, the composite FK as in 0043, 0044 and 0065, plain INSERT shapes, and `_values = vars(row)`.
- check-all was not rerun. The implementer's fast run at `cb862a7bf` failed 1 of 41 (decision index, D-SC1.* unknown on
  the 3A6 base). Merging main clears that.

## Findings

**L1 (Low; commit 2 must change).** Several texts contradict D-3A7.14 and D-3A7.15:
`structure/reconciliation.py:246-248` says "the composition builds it from the repository root".
`handoff.md` "Next" 3 says the builder "builds the `owner_file` port from the owner root", and "Next" 4 keeps the P4
digest residual, which D-3A7.14 voids.
`packet.md` "Known deviations" and `.ai/state/data.md` call Q1 and Q2 "await the Architect".
The build branch's `rulings.md:187` puts `commercial/reconciliation.py` in `ADOPTED`.
These matter because commit 2's implementer reads the handoff first. To fix: merge `61ca7a695`, which merges cleanly,
then fix the docstring, handoff, packet and state entry.

**L2 (Low; spec gap, for the Architect, not an acceptance gap).** `_cites` (line 191) follows §2.4 literally: a token
must not be preceded by a digit or `.` and must not be followed by a digit. So an owner file that names a longer slug
also cites the shorter one: "lakeside-power-north 2%" validates a tolerance for `lakeside-power`. Suggested fix: a slug
boundary that excludes `[a-z0-9-]` on both sides.

**L3 (Low; merge).** `.ai/state/index-2.md` line 169 is taken on `main` (main ends at 173), so 3A7's line becomes 174.
`.ai/state/data.md` conflicts on append. Resolve both when merging main in commit 2.

## What commit 2 must do (D-3A7.14, D-3A7.15)

- Add `structure/reconciliation_composition.py::build_commercial_reconciliation(database_url, *, owner_file=None)`,
  reached only through `commercial.composition.build_commercial_reads` (`months`, `store`). It imports no adapter and
  opens no file, and `commercial/composition.py` is untouched.
- In `reconcile_month.py`, build the `owner_file` reader from `owner_root` with pathlib and pass it in. `owner_root`
  None means the repository root.
- The SC-1 `ADOPTED` entry is `structure/reconciliation.py`.
- Drop the P4 residual.
- Name the finance lead with `--as` (3A3 person checks) and always pass `by_script=True`. The service already stores
  `recorded_by` and `recorded_role`, and it takes `by_script` as a parameter (Q1 default).

## Residual risk the packet does not name

1. **`main` fails its own 3A1 guard.** `test_no_log_call_in_the_commercial_package` fails on `main`, because 3A6 r5's
   `commercial/envelope.py` has `import logging` and `getLogger`. Commit 2's regression set (3A1, 3A3 and 3A6 files)
   will show this failure after main is merged. It is not 3A7's defect; it goes to the coordinator for 3A6's owner.
2. **Adapter and migration untested until commit 2.** If Q1 to Q3 find a defect, the fix lands in the same commit as
   the words.
3. **`this_month` on `NONE_MATCHED`.** It carries a covering zero-stated check (T10 asserts this), and spec §2.3 step 5
   says nothing about it. Commit 2's `none_matched` words must not read it.
