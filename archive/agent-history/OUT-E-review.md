# OUT-E slice review (cost check after the trial)

Reviewer: fresh Claude, 2026-10-31. Branch `task/OUT-E-cost-proof` at `462b5e6d`, reviewed against main `b94aee17`.
Contract: `AssetOpsV1-plan2/.agent/build-sheet-OUT-E.md` (sections 0, 2 E4/E5, 3, 4, 6, 8, 9). Architect ruling
2026-10-31 on E4 (option b, R595 open). E1 to E3 were unit-reviewed already. This review covers E4, E5, the E2/E3 fix
round and the whole slice.

## Verdict: ACCEPT

Nothing blocks. I found no High or Medium finding. There are four Low findings below. None of them needs to be fixed
before merge.

## Fix round (2862e0b2, 88c06602, dabcbe6a)
- **M1, the contract fixtures.** I diffed the JSON structure of the fixtures at `b94aee17` and at `HEAD`.
  `s6_verification_api_contract.json` only adds keys: `generator_kwh` (2 windows) and `cost_check` and `trial_hours`
  (one summary). No existing value changes and nothing is removed. `s6_action_api_contract.json` (462b5e6d) adds only
  `cost_check: null` and `trial_hours: null`, in its 7 verification summary bodies. This is clean.
- **`recorded_at` at the service clock.** `_cost_check` passes `now = self.clock()`. The evaluation's outcome row
  takes the same clock (`verification.py:771`). The SFC history and price selection read `known_at = now`, so the row
  is stamped at the time its inputs were known. Knowledge time is consistent. Append-only behaviour is unchanged: the
  writer only INSERTs, the 0037 trigger refuses UPDATE and DELETE, and supersession is ordered by `revision_no` under
  the advisory lock, not by timestamp. A fixed demo clock therefore cannot misorder revisions. One small remark is L3.
- **`_window_replay`.** The plan-freeze `_replay(plan, digest, site_code)` at `verification.py:346` is the only
  `_replay`. Its two callers (`:148`, `:306`) resolve to it, and the cost check uses `_window_replay` (`:870`, `:889`).
  The shadowing is gone.
- **L1.** The payload is `{outcome_id, intervention_cost}`, with no idempotency key (`verification.py:911`).
- **L2.** `finite_decimal` skips a malformed, boolean or non-finite SFC value, so the check reads SFC_MISSING.
- **L3.** `test_sfc_for_refuses_several_zero_and_ending_inside_the_window` (`test_out_e2_trial_comparison.py:147`)
  pins the three refusals.

## E4
- **Copy.** Every string in `board.py:51-75` and `mini.py:73-74` matches sheet section 4 exactly. That includes all
  11 reason words, the half-even rounding at 3 decimals (1/24 gives 0.042 and 11/240 gives 0.046) and a single
  figure when the bounds are equal. A test asserts that the reason-word keys equal `REASSESSMENT_REASONS`.
- **The label.** Every money line starts with `COST_PREFIX`, "Modelled change after the trial · not realised
  savings: ". The Assure line uses the sheet's exact form ("verified on test data · modelled change ...").
- **Intervention cost.** It is stored as amount 0 with its source text and is never subtracted (the E2 test).
  Following section 4 ("stored, not shown"), it does not appear on screen. See L2.
- **Not verified.** "Status changed; not attributed" appears when the result is not VERIFIED and the verdicts
  differ. When the verdicts are equal, the plain "Supply cost per kWh: X before and after the trial" appears instead.
  The before/after line appears only with a zero-target MG-2 objective and both trial hours known (R593).
- **Protect row.** No modelled cost claim can reach it. `cost_line` is gated on `cat == "OPTIMIZE_COST"`
  (`board.py:409`). `trial_line` needs an `avoidable_generator_minutes` objective in the row's own category, and MG-2
  is `OPTIMIZE_COST` (`catalogue.py:47`). The Postgres test asserts this on the real data: the Protect detail is
  null and "not realised savings" appears nowhere in the body. Per the packet, that test passed in the `-Tier all`
  run; I did not rerun it.
- **Fake-port tests.** `test_out_e4_readback.py` proves the Cost-row line in every state, the before/after line
  (attributed, not attributed, unchanged and absent) and the Assure line, both attributed and not attributed.
- **No recompute on read.** `_cost_check_read` returns the stored row and the stored outcome metrics as they are.

## E5 evidence
- **Full backend run.** Between `223baa5b` and `462b5e6d` only test files, a fixture and docs changed (`git diff
  --stat`). Under the tiered policy, the targeted rerun of the two fixed tests is enough, so a second `-Tier all` is
  not needed. The changed action fixture is also read by the frontend tests, and I reran those myself (see Checks).
  I did not verify the packet's 4518/2/0 counts or the "4 passed" rerun, because I ran no Postgres.
- **Captures.** Recording the API JSON is honest, adequate evidence for the text, and the packet records the shots
  as not rendered, with the reason, rather than as a pass. I decoded the five `board-*.json` files:
  - `verified` has exactly one modelled-change line, and it is the Assure line.
  - `target_miss`, `guardrail`, `withdrawn` and `inconclusive` have no modelled change, no "not realised savings" and
    no PRICE_MISSING text.
  - Every Earlier detail is null.
  The residual-risk check holds. The visual gap is not registered, which is L1.
- **Migrations.** `alembic heads` gives `0039_merge_objectives_cc (head)`. Against the CC-M branch `e7191a88`,
  0036 and 0037 differ in their docstrings only. 0039 is empty, with `down_revision = (0037, 0038)`.
- **Process.** Nothing under `var/` is tracked. The DB names are `assetops_out_e_trial_<case>_test`, `assetops_s602b_oute_audit*` and `assetops_out_e_board_test`.

## Findings (all Low, none blocking)
- **L1. The visual gap is not registered.** `.agent/mock-departure-register.md:589` (R595) records the missing
  Cost-row read-back on real data. It does not record that no Kobo Overview capture shows either OUT-E line: the
  s602b case DBs answer 409 "Awaiting evidence migration", and the `inconclusive` capture required by sheet E5 was
  never taken. This matters because "the mock is the layout spec": the longer Assure line and the `<small>` detail
  have never been seen at 1440 or 390. Fix: extend R595, or add a backlog line, so that the combined-dataset
  walkthrough captures both lines at 1440 and 390 against v70.
- **L2. R591 says more than the screen shows.** `mock-departure-register.md:585` says "the intervention cost is
  stated as zero", but sheet section 4 keeps it stored and not shown, and nothing on screen states it. Fix: reword
  R591 to "recorded as zero with its source, not shown, never subtracted", or have the Architect add it to the copy.
  This is wording only.
- **L3. History order with a fixed clock.** `postgres_trial_comparison_store.py` `history()` orders by
  `recorded_at, id`. With the service clock fixed, as in the demo and fixtures, two revisions can share a
  `recorded_at`, and `id` is a random uuid4, so the order is arbitrary. `history()` currently has no caller. Fix,
  when it gets one: order by `revision_no`.
- **L4. An untested case needs a ruling.** An INEFFECTIVE outcome can still reach MODELLED_IMPROVEMENT, because
  `FINAL_COMPARABLE` includes INEFFECTIVE. `cost_line` (`board.py:375-385`) would then show "Did not fix it" with
  "Modelled change after the trial · not realised savings: X USD less ..." in the Cost row. This follows the sheet,
  which does not gate the Cost line by verdict, and the line is labelled as modelled. But acceptance 4 says "no change
  is credited to the trial" on an outcome that was not verified, and no test pins this case either way. Fix: an
  Architect one-liner confirming the reading, plus a fake-port test pinning the resulting text. This is an ambiguity,
  not a defect.

## Checks run (worktree at 462b5e6d)
- **pytest, no Postgres URL.** `test_out_e2_trial_comparison`, `test_s6_verification_rules`, `test_out_e4_readback`,
  `test_out_e3_trial_comparison_postgres`, `test_out_e4_readback_postgres`, `test_out_b1_board`, `test_out_b2_mini`,
  `test_out_b3_cold_ev` and `test_out_d4_board`: **172 passed, 5 skipped** (the skips are the Postgres tests), 2.19 s.
- **`npx.cmd tsc --noEmit`:** clean (exit 0).
- **`npx.cmd vitest run src/sites/__tests__/outcomeBoard.test.tsx`:** 17 passed. The vitest config loaded under this
  session.
- **`npx.cmd vitest related --run <changed>`:** aborted with an unhandled "Failed to parse source ... .py" error from
  the related-graph walk. This is a tool issue, not this slice, so I ran the files directly.
- **Fixture consumers.** The seven frontend test files that read `s6_action_api_contract.json` (siteAction,
  siteActionVerification, siteFoundationChange and the four w1f4 files): 216 passed and 3 failed. The 3 failures
  are the known `w1f4VerificationStructure` ones.
- **`tools\check-all.ps1`** (with `ASSETOPS_GUARD_PYTHON` set to the plan2 venv): **All 11 guards passed** (estate
  guard self-tests: 7 passed).
- **`alembic heads`:** `0039_merge_objectives_cc (head)`.
- **Not run (by instruction):** Postgres tests, the full backend suite, full vitest, the browser and the captures.
  The `-Tier all` numbers, the E3 Postgres results and the targeted rerun are the implementer's and unverified by me.

## Residual risk (beyond the packet)
- `summary()` now does two more reads per verification summary (`store.outcomes` and `latest`) on every Action,
  Change and Recommendation read that embeds it. That costs runtime only. A cost-check store failure would fail
  those reads, but the store shares the action database, so the failure mode is not new.
