# K7-F independent first review (DIESEL-1, Kisiwa freeze and evaluate)

Reviewer: Claude (fresh context, did not author K7-F). Date 2026-11-08.
Branch `task/DIESEL-K7F-kisiwa-freeze`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k7f`, head `c17567341`.

## Verdict: ACCEPT

There are no High or Medium findings, and three Low ones. None of them blocks the single K7-D + K7-F merge (§9o.4).

## Range reviewed

- K7-F's own code: `git diff 3cae5f46d..HEAD -- . ':!.agent'`, which is commits `cef9a7994` and `c17567341` (seven files). `3cae5f46d` is the main (K6b) merge. `f1f7dca2a` brings in only K7-D's review record (`git diff 3cae5f46d f1f7dca2a^2` shows nothing else of K7-D's), so `f1f7dca2a^2..HEAD` minus K6b's main merge is the same delta.
- Records: `aa429e0f4`, plus the packet `.agent/review-packet-K7F.md`.
- Specs judged against: §9o (R3n), the K7-F part of §9l.3, and §9m.5.
- K6b's own files (`actions/verification.py`, `fuel_verification.py`) came in through the main merge and were already reviewed. I read them only where K7-F calls them.

## Checks against the brief

1. **`freeze_and_evaluate`** (`tools/demo_combined_kisiwa.py:629-683`)
   - The calls match §9m.5. `build_fuel_verification_service(url, test_clock=...)` runs at `plan.freeze_at`, then at `evaluate_at`. The extra `SITE_CODE` argument to `fuel_summary` fits its optional `site_code` parameter.
   - The S-6 conditions are all present. They are: status 201; `effective_from` equals the resolved `complete_at`; `effective_from` is before night 6's window start (`night_opens`, 18:00 local); `candidates.from` is night 6's date; the baseline window is night 4's id. The builder added a sixth condition: plan `recorded_at == freeze_at`. That is stricter, and acceptable.
   - The verdict is recorded as computed. Only NOT_JUDGED, NO_PLAN or `stored` false stops the run. No verdict value is asserted, and the L0 test runs on VERIFIED, INEFFECTIVE and INCONCLUSIVE alike.
   - Nothing leaks past the cutoffs:
     - `evaluate_fuel_plan` → `_fuel_windows(..., known_at=now)` (`verification.py:426-433`) reads windows as known at `S−1d 13:00`.
     - In the kept `kisiwa.json`, night 8 (4 Nov) is recorded at 2026-11-05T12:30Z, before the 13:00Z evaluation. Night 9 is recorded at 2026-11-06T12:30Z, after it.
     - The stored verdict uses later nights 2, 3 and 4 Nov (nights 6–8) and never night 9 or 10. `effective_from` is 12:05Z, the plan is recorded at 12:30Z, and night 6 opens at 15:00Z.
   - Order: `record_action` → `freeze_and_evaluate` → `threads` (`build`, lines 791-796). A source-order test pins this.
2. **The default flip**
   - `Demo.prepare(sites=SITES)` and `--sites` default to `",".join(SITES)`. The new L0 test drives `main([... "prepare"])` and checks it receives four Sites.
   - The default cap is now 2×4830 = 9660 s, which is under 10800.
   - Callers I swept:
     - `tools/`, `backend/tests`, `host/tests`: only `test_demo_combined_postgres.py` relies on the default (see L3).
     - `test_demo_combined_mill.py` `THREE = tool.SITES` and `tools/dd1a2_addday_l2.py` predate K7-F (from K7-D), and both filter by `install_order`.
   - Deviation 2 (`test_demo_combined_finish_days.py` passes `CORE_SITES`): **confirmed**. The test is named for, and asserts, a three-Site prepare (`manifest["sites"] == ["kobo","cold","ev"]`, three objectives calls). Pinning it keeps its intent.
3. **KIS-3 printout and KIS-9 (e)**
   - KIS-3 (`demo_combined_rows.py:640-679`): `tolerance_l` is `"1/100000"`, and `max_diff_l` holds the five terms as exact `Fraction` text. The maximum is taken over the nights after the existing per-night tolerance assert, so a pass always has every value ≤ tolerance.
   - The L0 test checks both keys and ≤ tolerance, as §9o.3 asks. A further test plants differences inside the tolerance and checks the exact maxima.
   - A new fail case sits just beyond 1/100000.
   - KIS-9 (e) (`demo_combined_rows.py:753-756`, reads at `demo_combined_finish.py` `_kisiwa_action`) requires exactly one plan stamped `freeze_at` and exactly one outcome stamped `evaluate_at`. There are six fail bodies.
4. **KIS-10 `utc_aligned_window`** (`demo_combined_finish.py:59-66`, used at 1095)
   - It is correct. It floors `lo` to UTC midnight and ceils `hi`, so the window is 8 days, under `MAX_DAYS` 31.
   - It does not loosen KIS-10:
     - The estate summary is used only for the H2 negative ("no Portfolio value line names the fuel Action"). A wider window can only show more lines, so that check is equal or stricter.
     - The board read and every positive assertion still use the Site-local day.
   - The L0 test fails against the old window *in the sense that the real `check_window` refuses it*. It does not bind `kis_10` to the helper (see L1).
5. **Deviations**
   - **Deviation 1** (the R3k2 L2 carry on K6b's KIS-5 and KIS-10): **confirmed**. K6b brought two "not in this dataset (K7 adds it)" skip branches. Those are exactly what R3k2 L2 forbids, and K7-D's own carry test (`test_carry_r3k2_l2_no_kis_row_keeps_the_skip_branch`) would fail on the merged tree without the carry. It is a minimal edit (two `raise KisiwaMissing()`), and the count test went from 3 to 5.
   - **Deviation 3** (`story_links` falls back to `action.finding_id`): **confirmed**.
     - The kept `kisiwa.json` has no top-level `finding` key. It does have `action.finding_id`, written by `record_action` (line 623). So K7-D's "unexplained-fuel finding" link could never appear, and this is a real defect fix.
     - K7-F edits that same block for the verification link, so it is in scope.
     - Mutation M8 below shows the test catches it.
6. **Mutations.** I ran these on a scratch copy of `tools/`, `config/`, `backend/conversions`, the F0 probe result and the two test files, with the backend imported from the worktree. No repo file was edited. The baseline on the copy was 101 passed.

   | # | Mutation | Result |
   |---|---|---|
   | M1 | `kis_10` back to the old local-start window | **survives** (101 passed): L1 |
   | M2 | `effective_from` S-6 check removed | caught (`stop_s6[change0]`) |
   | M3 | `status == 201` S-6 check removed | **survives**: L2 |
   | M4 | KIS-9 (e) plan-stamp assert removed | caught (3 cases) |
   | M5 | KIS-3 `max_diff` never updated | caught |
   | M6 | freeze moved after `threads` | caught |
   | M7 | NOT_JUDGED accepted | caught |
   | M8 | `story_links` fallback removed | caught |
   | M9 | `utc_aligned_window` drops the ceiling on `hi` | caught |

7. **Process slips** (not blocking): the polling loop and one `head` use noted in the brief. The hand-copied `.demo3-combined-work` marker skipped the tool's ownership guard. In substance it was safe, because the database was K7-D's tool-made throwaway `*_test` DB. The coordinator accepted it, and it is recorded in the packet. A guard bypass should stay an explicit coordinator call each time and never become routine.

## Findings

### L1 (Low): the KIS-10 L0 test does not pin the call site
- **Where:** `backend/tests/test_k7f_kis10_window.py:20-31`, against `tools/demo_combined_finish.py:1095`.
- **What is wrong:** The tests check the helper and that the old window is refused by `check_window`. No test checks that `kis_10` actually calls the helper.
- **Failure scenario:** someone reverts line 1095 to `lo - timedelta(days=6), lo + timedelta(days=1)` (mutation M1). All L0 tests stay green. The regression then shows only in E3 or K9's rehearsal, where KIS-10 fails with 422 INVALID_WINDOW after a 2-hour four-Site prepare.
- **Fix:** add one L0 test that runs `kis_10` with a fake `Ctx` whose `get` calls `check_window` on the `from`/`to` it receives (or asserts they are UTC midnight), and that stubs `_kisiwa_fuel` and `demo_rows.kis10`. A source check that `kis_10` calls `utc_aligned_window(` would also do.
- **Why it is not blocking:** the packet's read-only re-run against the kept DB shows the current code passes KIS-10.

### L2 (Low): the spec-named `status == 201` stop is not exercised
- **Where:** `tools/demo_combined_kisiwa.py:661`, against `backend/tests/test_k7_kisiwa_story.py` `_fake_services` and `test_k7f_a_plan_off_the_card_is_stop_s6`.
- **What is wrong:** The fake freeze always answers 201, and none of the parametrized cases changes the status.
- **Failure scenario:** the `status` entry is dropped (mutation M3). Then a replayed freeze (`200, {"replayed": True, ...}`), for example a re-run on a database that already holds the plan, is accepted silently. The run reports a fresh story-time freeze that never happened.
- **Fix:** let the fake take a status, and add `200` (replay) to the stop-S-6 parametrization.

### L3 (Low): the slow L2 build test now prepares four Sites silently
- **Where:** `backend/tests/test_demo_combined_postgres.py:3` (docstring "all three Sites", "about 20-25 min") and `:56` (`d.prepare()`), and `backend/TESTING.md:327` ("one three-Site ... prepare").
- **What is wrong:** With the K7-F default, this slow test now builds Kisiwa too.
- **Failure scenario:** someone runs the slow tier before K8/K9. The run takes about 2.0–2.35 h instead of the documented figure, outside any cap the suite guide sets. Non-KIS rows awaiting K8's re-expectation (§9o.1, for example Protect `open_findings` +1) then fail and look like regressions. It would also be an unplanned four-Site run ahead of K9's rehearsal.
- **Why the fix is not to pin `CORE_SITES`:** a three-Site prepare now fails the KIS rows by design (R3k2 L2).
- **Fix:** update the docstring and TESTING.md to four Sites with the measured runtime. Optionally, mark the test as deferred until K8 lands. This is for the Architect or coordinator, not K7-F code. No full suite runs in the demo sprint, so it is not demo-blocking.

## Checks run (by me)

- **Focused tests** (no DB; plan2 venv python, absolute PYTHONPATH under the k7f worktree, run from `backend/tests`): `test_k7_kisiwa_story.py test_k7f_kis10_window.py test_demo_combined_finish_days.py test_demo_combined_links.py test_demo_combined_mill.py test_k6b_fuel_verification_rules.py test_dd1b2b_drain.py`.
  - Result: **170 passed, 4 skipped** in 11.9 s.
  - The 4 skips are DB-gated cases in the mill or K6b files, which are not K7-F's.
- **Probes:** `tools/probe_kisiwa_fuel.py --check` reported "probe result current". `tools/probe_kisiwa_nights.py --check` reported "probe result current (G6 pass)".
- **Mutations M1–M9:** see the table above.
- **Kept `var/demo3_kisiwa/kisiwa.json`** (file read, no SQL):
  - plan `status` 201, `recorded_at` 2026-11-02T12:30Z, `effective_from` 12:05Z, candidates from 2026-11-02;
  - verdict VERIFIED, `stored: true`, evaluated 2026-11-05T13:00Z;
  - night assessed-at stamps as quoted in check 1.

## Not verified

- **The scratch prepare itself** (exit 0, 4308 s, RAM samples): I have only the packet's record. Per the brief, I ran no prepare.
- **The KIS-10 re-check pass:** I did not re-run it. I ran no DB check, so I take it from the packet.
- **`tools/check-architecture.ps1` and `check-agent-workflow.ps1`:** not run, because the brief forbids passing `-ExecutionPolicy`. K7-F touches no frontend, so frontend tsc and the frontend suite do not apply.
- **The full backend suite:** not run, per the demo-sprint policy. The packet cites only focused runs (302 passed).

## Residual risk not named in the packet

- **The night-4 baseline query can stop the run wrongly.** The query behind the freeze's baseline check (`demo_combined_kisiwa.py:657`) takes night 4's *latest stored* revision, with no tank filter. The plan's baseline is the window the origin revision's claim cites (revision 1). If night 4 ever gains a later revision before the check runs, S-6 fires even though the plan is right. This fails closed and does not happen today.
- **No full self-check has run with KIS-5 and KIS-10 in it.** A Kisiwa-only prepare skips the self-check (`demo_combined.py:594`, which runs only when all core Sites are present). So the prepare's exit 0 says nothing about KIS rows. Their only evidence is the separate `demo_combined_kisiwa.py check` run. The first in-prepare KIS-5 and KIS-10 run will be K9's rehearsal.
