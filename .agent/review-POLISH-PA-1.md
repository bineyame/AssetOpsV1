# Review: POLISH PA-1 (board truth)

Reviewer: fresh Claude reviewer (did not author the slice). Date 2026-11-01.
Worktree `AssetOpsV1-polA`, branch `task/POLISH-PA-1-board-truth`, head `21816adf8`; base main `83918ac00`.
Diff reviewed: `git diff 83918ac00...21816adf8` (14 files; no `frontend/` or `tools/` files).
Spec: plan2 `.agent/build-sheet-POLISH.md` §1 (P-06, P-11, P-12), §1.1, §1.6, §1.7, §3.1, §5 PA-1, §6, §7, Addenda 2-4.
Addendum 4 is present in the plan2 working tree but is **not committed** there yet (`git status`: `M .agent/build-sheet-POLISH.md`).

## Verdict: REVISE

The code that was built is correct and narrow. Every point I was asked to check holds, except one: Addendum 4 item 3
says the S+1 readiness chip changes "in a PA-1 fix round before merge", and that change is not in the branch. This is
the only blocking finding. The fix is small.

## Findings

### H-1: the Addendum 4 item 3 readiness chip is not implemented (acceptance gap, blocks merge)
- `backend/assetops_backend/site_outcomes/mini.py:730-731`: in the settled case the Readings contributor is built as
  `Contributor("readings", "Readings", NO_RUN_READINGS, rc, ...)`, where `rc = readiness_confidence(readiness)`
  (`mini.py:368`). Readiness is exactly `UNKNOWN` here by construction, so the chip reads "Unknown" next to
  "readings complete". The packet's Residual risk and `.ai/CODE_STATE.md` both say so.
- Addendum 4 item 3 requires the following, in the MG-7 settled case only:
  - the chip is the one `mini.py` gives FULL readiness;
  - no "Unknown" word appears on the line;
  - the shared readiness value and `reduce_day` stay unchanged.
- `backend/tests/test_polish_pa1_board_truth.py:69-74` asserts the outcome, the row label and the text, but not the chip.
- Why it matters: this is a ruled pre-merge item, and it is the "says Unknown and complete at once" contradiction
  this slice exists to remove.
- Fix:
  - in the `elif no_run:` branch, pass `readiness_confidence("FULL")` instead of `rc`. Leave `rc` for every other
    contributor alone.
  - in the settled-case test, assert that the readings chip is not `mini.UNKNOWN_CHIP`, that it equals
    `board.readiness_confidence("FULL")`, and that no contributor text in the Assure row contains "Unknown".
  - optionally, assert in `test_no_run_rule_is_narrow` that the non-settled cases keep `rc`.

### L-1: `COST_NOT_CREDITED` is not in any scanned vocabulary tuple (test gap; preference-adjacent)
- `backend/assetops_backend/site_outcomes/board.py:58` defines a new client string. The `test_out_b2_vocabulary.py`
  `_constants()` list does not include it, and no `_boards()` fixture renders a non-VERIFIED MODELLED_IMPROVEMENT.
- I checked it by hand against `productVocabulary.json` (the same patterns as the test) and it passes. Today nothing
  pins it, though. The existing `COST_CHANGE`/`COST_NO_CHANGE` are not scanned either, so this is a gap from before
  the slice that this slice extends.
- Fix: add `board.COST_NOT_CREDITED` to `_constants()`. The other `COST_*` strings can be added in the same line.
  This can be folded into the H-1 round.

### L-2: R636 overlaps R627 without a cross-reference (register hygiene)
- `.agent/mock-departure-register.md:635` (R636) records Kobo Grow "Unknown" on S and S+1 because there are no sales
  records. R627 (`:626`) already records "Day S: Grow 'Unknown' with no line" for the same reason (it cites R582).
- R636 is not a duplicate: it adds S+1 and the MG-1 OBJECTIVE_NOT_JUDGED cause the Architect asked for. It should
  still cite R627 and R582 so the two are not read as two separate departures.
- Fix: add "(see R627, R582)" to R636's reason cell.

### L-3: the `COST_NOT_CREDITED` wording on states that cannot be reached (residual, not a defect)
- `board.py:386-387` also returns "The trial did not fix the problem" for INCONCLUSIVE, PENDING and `None`. That wording
  would be untrue for those states.
- They cannot be reached today: `financials/trial_fuel_comparison.py:32,82-83` produces a comparison only for
  `FINAL_COMPARABLE = ("VERIFIED", "INEFFECTIVE")`, and every other outcome gives the reason OUTCOME_INCONCLUSIVE
  (UNAVAILABLE).
- The sheet (§5) states this rule as written, and the packet names the risk. No change is needed. If a later slice
  adds a MODELLED_IMPROVEMENT for any other state, this line must be revisited.

## Point-by-point checks

| Check | Result |
|---|---|
| No number or story data tuned | Holds. The diff has no `tools/`, fixture, migration or producer changes. The only data in the diff is test fixtures. |
| Zero headline only when the priced top is 0 | Holds. `mini.py:388`: `zero = priced and _is_zero(amount_high)`, where `priced` already requires PRICED + ELIGIBLE. `headline_money` is `None` only `if priced and not zero` fails (`:389-390`). `amount_low` is not tested. 0.01 keeps money (test `:38`). |
| MG-7 settled rule is the three conditions, narrow | Holds. `no_run_day` (`mini.py:698-703`) = `base` (the standing precondition already on every settled key) ∧ `readiness == "UNKNOWN"` ∧ `claim_level == "COMPLETE"` ∧ no `dispatch_intervals`. The fields match `site_overview/read.py:360-370` and the Overview "Day reading" line (`SiteWindowOverview.tsx:496`). `test_no_run_rule_is_narrow` covers one interval, LIMITED, stale and `None` readiness, and FULL keeps the old line. |
| Shared `reduce_day` unchanged | Holds. `analytics/claim_limit_read.py` is not in the diff. |
| EV tariff sentence depends on a real priced tariff | Holds. `board.py:567` checks `headline_money["GROW_REVENUE"]`, which `ev.py:185,207-208` sets only when `consequence_summary.state == "PRICED"` with an amount. Both branches are tested (test `:57`). EV-2 `missing_records` is unchanged (Addendum 2 Q-C). |
| `cost_line` credits only VERIFIED | Holds. `board.py:385-388`. Tested for VERIFIED, INEFFECTIVE, INCONCLUSIVE, PENDING and `None` (see L-3). |
| `history()` ordering | Holds. `ORDER BY recorded_at, revision_no, id` (`postgres_trial_comparison_store.py:85`). The test fails under the old order: the T1 pair has ids `ffffffff-...` (revision 1) and `00000000-...-0001` (revision 2). Postgres uuid comparison is bytewise, so the old `recorded_at, id` order puts (o1,2) before (o1,1) and the first assertion fails. Two outcomes interleave across T0/T1/T2, as Q-A asks. I also ran it on a run-owned `*_test` DB and it passed. |
| New strings scanned, pass the guard | `COST_ZERO` and `NO_RUN_READINGS` are in `mini.COPY` (`:149`), and `ROW_NOT_MEASURED_EV_COST_UNPRICED` is in the a1 catalogue scan. All of these, plus `COST_MONEY`, `COST_NO_MONEY`, `COST_NOT_CREDITED` and "Investigate Connector C2", produce zero pattern hits in my manual run of `_patterns()`. Gap: L-1. |
| Readings wording deviation | Addendum 4 item 1 accepts "Generator not used on this day, so nothing to check · readings complete". It is closed, but committing Addendum 4 in plan2 is still pending. |
| Register R626/R635/R636 | R635 is accurate (it cites R628, R263, the `_row` site and the constant). R626's update is accurate (honest zero, Q1, closes with PB-2). R636 is accurate on cause (`mini.py:466` `Reading(None, False, MG1_ACTUAL)` → `status.py:88` OBJECTIVE_NOT_JUDGED), but see L-2. The ids are inside PA-1's reserved R635-R639. |
| No frontend files changed | Holds. The frontend fixtures still carry "exposure in this hour", which Lane B (PB-2) owns, as the packet notes. |
| Connector wording | `ev.py:220` uses `connector_name`, so there is no double prefix. The b3 test pins "Investigate Connector C2". |
| Captures | Deferred to PA-3 under Addendum 3. The packet records them as not run, not as a pass. The compose-level exact-output tests are present for each changed string. |

## Checks I ran (head `21816adf8`)

- `tools\run-host-tests.ps1 -- test_polish_pa1_board_truth.py test_out_b2_mini.py test_out_b3_cold_ev.py test_out_a1_outcome_map.py test_out_b2_vocabulary.py test_out_b1_board.py test_out_e4_readback.py`: **118 passed**, 2.8 s.
- `tools\run-host-tests.ps1 --` all non-Postgres `test_out_*.py` + `test_polish_pa1_board_truth.py`: **344 passed**, 9.6 s.
- `tools\run-host-tests.ps1 -- test_polish_pa1_trial_history_postgres.py` (run-owned DB cloned from `assetops_test`): **1 passed**, 9.7 s.
- `tools\check-architecture.ps1`: it failed at first because no guard interpreter was set (rule 8 "no Python interpreter"). That is an environment issue, not the slice. With `ASSETOPS_GUARD_PYTHON` set to the plan2 venv it **passed**.
- `tools\check-agent-workflow.ps1`: **passed**.
- I did not run any of the following:
  - the packet's directory-wide `-k` run: the host wrapper refuses a directory, and a direct run hit unrelated import errors from the PYTHONPATH environment, so I replaced it with the file list above;
  - the other four Postgres files in the packet's 30-pass run;
  - `-Tier all`, serve, browsers or frontend.
- Cited, not rerun: the implementer's check-all 11/11 at `ddf5b7537`, and the Postgres scoped run of 30 passed in 810.9 s. That code revision is `68823980a`. The commits after it change only a test assertion (`adc731a41`) and records, which I verified with `git diff --stat 68823980a 21816adf8`.

## Residual risk not named in the packet

- Addendum 4 is uncommitted in plan2. Until it is committed, the ruling that H-1 and the wording acceptance rest on
  exists only in a working tree.
