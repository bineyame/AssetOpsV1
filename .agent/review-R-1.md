# Review R-1 (light), branch task/R-1-demo-fixes @ 6edb36976

Reviewer: fresh Claude (Opus), did not author the slice. Spec: `AssetOpsV1-plan2/.agent/architect-combined-pass-2026-11-08.md` A.1, A.2, A.5. Diff: `git diff main...task/R-1-demo-fixes`.

## Verdict: ACCEPT WITH NOTES

No High or Medium findings. The notes below are Low and do not block.

## Scope check
- 10 files changed: the review packet plus 9 files, all on the A.5 approved list. No product backend file changed (`backend/assetops_backend/**` untouched).
- T6: `backend/tests/fixtures/w3/w301-estate-golden.json` is not in the diff, and the worktree is clean (`git status` empty). Nothing T6-related is committed. The T6 outcome itself is left to the Architect ruling, as instructed.

## Item-by-item against the spec
- A1-a (`EstatePortfolio.tsx`): `fuelThread` is the exact predicate from the spec. When true, the cell renders one bold `<strong data-portfolio-workflow>` with the thread label ("Verified"), and the `workflow-text` span is suppressed. The `action_id === null` "Review finding" branch is unchanged. When false, the rendering is byte-identical to before. The MOCK DEVIATION MD-FUEL-K4-1 comment is verbatim. Tests: the R3p case has the three specified assertions, and the no-thread fallback case is added ("No action yetNo action agreed yet"). The `:182` non-fuel null-action case is unchanged and green.
- A1-b (`MiniPerformance.tsx`): `barLabel` is exported with the three branches as specified and is used only at the chart label. `feederName`, the load table and the critical card are unchanged. Kobo's "Clinic feeder delivered power · Critical load" stays byte-equal, and Kisiwa gives "Cold store (ice and fish) · Critical load". The MD-KIS-K1-1 comment is verbatim. The `barLabel` describe covers all three branches. R309 is unchanged and green.
- T1: replaced by the specified `pytest.raises(ValueError, match="unknown period 'midday'")`. The ruling says stale.
- T2: only the one call site passes `not_applicable=frozenset({"MG-8"})`, and the shared `kobo()` fixture is unchanged. The expected order matches the catalogue. The ruling says stale.
- T3: the vocabulary arm accepts a subset of the six names, with the FUEL-1 comment. Nothing else is loosened. The ruling says stale.
- T4: `SEAM_OWNERS` holds both stores, with the non-vacuous `KW in owner` assertion, and `objectives/composition.py` is added to the text check. The ruling says stale.
- T5: the change is test code only. The defaults are `None`, then `code = COLD if code is None else code`. The ruling says wrong (test code).
- T7: the patch target moved to `read_scope.clock`, imported inside the `if URL:` block. `read_scope.clock` exists (`read_scope.py:207`). `UTC` is defined in the test module (`:42`), and the `finding_service` and `recompute` patches are kept. The ruling says stale.

## Checks I ran (worktree C:\Users\assef\Bineyame\AssetOpsV1-r1)
- No-DB pytest, with `ASSETOPS_TEST_DATABASE_URL` unset: `test_ch1a_grading.py test_out_b1_board.py test_demo_a0_assumption_clock_seam.py test_w502_domain_intent_api.py` gave 56 passed, 8 skipped, 0 failed and 0 collection errors in 8.6 s. w502 now collects and skips.
- Scoped vitest: `src/estate/__tests__` plus `src/sites/__tests__/miniService*` and `miniPerformance*` gave 6 files and 134 tests, all passed. On this run vitest did execute; the sandbox did not block it.
- `npx.cmd tsc --noEmit` exited 0.

## Not verified by me
- T7 on Postgres (the packet reports 11 passed in 694 s on `assetops_r1_test`, including the DB-time asserts at `:310` and `:322`). I did not run it because Postgres runs were excluded for this review. The file cannot be collected without a DB URL, which is pre-existing.
- The A1-b height check (Coverage fully visible, `scrollHeight <= clientHeight` at 1440). By spec this belongs to the R-1c/K8c capture retake and is correctly marked not run.
- `tools/check-all.ps1`, which runs after the merge per spec. The full frontend suite and the build were not run (light review).

## Findings
- L1 (Low): the branch name `task/R-1-demo-fixes` differs from the spec's `task/R1-combined-lows`. This is cosmetic only, and the lineage is right (it branches from main afb0b9ccb).
- L2 (Low): the new A1-a fallback case asserts the text but not that exactly one `[data-portfolio-workflow]` exists on the no-thread row. The behaviour is unchanged from main, so this is test strength only, not an acceptance gap.

## Residual risk
- The T6 golden stays failing until the Architect rules. The packet's observation that `worker.run_pending` returns `[]` in the cold replay is a possible product or environment issue outside R-1's files.
- The demo-visible effect of A1-b still depends on the height check in the capture retake.
