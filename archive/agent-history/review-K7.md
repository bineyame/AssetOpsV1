# Review: DIESEL-K7-D (Kisiwa story days, the build phase)

- Reviewer: Claude (Opus), the first independent review. Fresh context; not an author of the slice.
- Branch `task/DIESEL-K7-kisiwa-story`, HEAD `63f60f986`. Diff: `git diff main...HEAD` (11 files, +2121/−43).
- Judged against build sheet §9l.1, §9l.3 (K7-D), §9m.5 (R3m), §9n.3 (R3k2) and §9o (R3n, read on main in `AssetOpsV1-plan2`).

## Verdict: ACCEPT

The code matches the card. I found no High or Medium findings. The four Low findings below are test-strength gaps
and one self-attested check. They can be fixed on the branch, or carried to K7-F, which already edits
`tools/demo_combined_rows.py` and the L0 file. None blocks the merge. Under R3n §9o.4, K7-D merges only together
with K7-F.

## What I checked, and what I saw

1. **The three-Site `story.json` is byte-equal.**
   - Both pins in `backend/tests/k7_story_pins.py` pass against the merged tree (`test_1_*`, 2/2).
   - Every core loop in `resolve_story`, `objectives_instants`, `finish_build` and `finish` iterates `CORE_SITES`.
   - `installs` stays three Sites. Kisiwa is added only under `kisiwa=True`.
   - The default `--sites` and `Demo.prepare` are `CORE_SITES`. `add-day` still refuses KISIWA-001.
   - The `finish` drain condition `{"kobo","kisiwa"} & sites` leaves the three-Site behaviour unchanged.
   - Nothing under `backend/assetops_backend`, `contracts`, `simulator`, `host`, `frontend` or `config` is touched (empty diff stat), so S-10 holds.
2. **Calendar and derived log.**
   - `resolve` (`tools/demo_combined_kisiwa.py:234-265`) raises `STORY_SHIFT_NOT_WHOLE_DAYS` on a non-whole move. The test resolves to `delta_days` 27 at S = 2026-11-06.
   - The derived log is written to `<work>/operational-actions/kisiwa-001-story-{yyyymmdd}-v1.yaml` (`:339-344`). It has the four-line header, LF line endings, and only `at` and `sensor_disconnected.at` moved (L0 test 3 checks each of these).
   - The shipped v1 log is checked against `77777c82…b634` before deriving (S-3, `:326-329`). `config/` is unchanged in the diff.
   - The straddle check (`:360-372`) uses `[at, at]` for point actions and `[at, at+dur)` against `[start, end)` for the removal and the sensor span. It runs in `build` before any draft (`:667`) and again in KIS-9 (c).
3. **Fuel events.**
   - The delivery and the removal reach the runs only through K0. The derived log is frozen into every run by `draft(..., operational_actions=…)`.
   - `run_guards` (`:458-496`) checks the frozen history against both the expected list and F0's ids. It also checks the frozen log id, version and sha, the physics end state (exact `Fraction`), and each dip (rounded half-even, on the step grid).
   - `record_post` (`:386-405`) returns None for the removal, the seal and the sensor fix. The one SITE_VISIT is posted in `record_action`, after the case exists.
   - KIS-9 (a) asserts that no record lies in the removal span or names it.
   - Every record post sets the Work store's clock to its recorded instant, through a default-arg lambda (no late-binding bug).
4. **`raise_night`, `record_action`, `cli_raise_check`.**
   - The raise uses K4a's `worker.main(["raise", …], finding_service=build_fuel_finding_service(url, test_db_clock_override=lambda: instant))`. It wants OPENED for night 4 and NO_FINDING for the rest.
   - `record_action` posts `"domain": "FUEL_BALANCE"` (R3m) with the domain clock at `raised_at`, then:
     - the request on a StepClock from 13:10;
     - ASSIGN on its own clock at 13:20 (the deviation R3n ratified);
     - the record and COMPLETE on a second StepClock from `change_recorded_from`;
     - the SITE_VISIT at 12:15, guarded `changed.last < visit`;
     - the link at 12:20, guarded `visit < link`.
   - `order_chain` and `check_order` (`:268-285`) cover §9l.3's 14 instants in the card's order. `check_equalities` covers the `≤` side condition and the record = effective = run-6-start equality.
   - The packet's scratch figures agree with these stamps: Finding created at run end + 31 min, and night 4 OPENED at 95.657–144.343 L and 119.57–180.43 USD.
5. **The R3k2 carry.**
   - KIS-4 (`demo_combined_finish.py:976`), KIS-3 (`:1123`) and KIS-9 (`:1184`) raise `KisiwaMissing`. No "not in this dataset" text remains.
   - `run()` (`:1222`) and `demo_combined_kisiwa.check` (`:800`) use `failed_result`, which marks the row failed and carries the R3k2 body as `read`.
   - The packet reports, correctly, that the three-Site default prepare would now fail KIS-3, KIS-4 and KIS-9. R3n's single combined merge with K7-F resolves this.
6. **KIS-3 and KIS-9 rows** (`tools/demo_combined_rows.py:479-616`).
   - KIS-3 compares state, reason, gap and the four exact terms exactly, and the five toleranced terms within `1/100000`. It reproduces the band with `rules.balance`. It checks night 4's moved gap span and `REPORTING_GAP`, the other nights' WITHIN_MARGIN with gap 0, and `idle_seconds` 0.
   - KIS-9 (a)–(g) follow the card.
   - The consequence read `cons[0]` has no ORDER BY. This is sound, because 0056 writes one consequence row per Finding revision.
7. **Test strength.** I ran ten mutations on a scratch copy (`git archive HEAD` into the session scratchpad; the repository was never edited). The K7 L0 file was the oracle:

   | Mutation | Result |
   |---|---|
   | KIS-3 returns the missing body as a pass in place of raising | caught |
   | straddle check ignores the span end (`lo <= s < hi`) | caught |
   | KIS-9 (a) drops the removal-span test | caught |
   | KIS-9 (a) drops the dip recorded +15 min check | caught |
   | `run()` stops using `failed_result` (the R3k2 body is lost from `check.json`) | **survived** (L1) |
   | KIS-4 skip with other text, the string `raise KisiwaMissing()` left in a comment | **survived** (L1; contrived) |
   | `order_chain` drops `action.case_link_at` | **survived** (L2) |
   | `run_guards` dip comparison removed | **survived** (L3) |
   | `run_guards` history comparison removed | **survived** (L3) |
   | KIS-3 band-reproduction assert removed | **survived** (L4) |

   A literal revert of the original KIS-4 skip line is caught (`"not in this dataset" not in text`), and so is removing any one of the three raises (count == 3).
8. **Process.**
   - The builders disclosed read-only `sed -n`/`head` use and one empty heredoc append. Both are noted and not blocking.
   - The worktree was clean at review time.

## Findings

### L1 (Low): the R3k2 carry tests read source text and do not exercise the rows or the runner
- **Where:** `backend/tests/test_k7_kisiwa_story.py:520-536`. The code they cover is `tools/demo_combined_finish.py:1222` and `tools/demo_combined_kisiwa.py:800`.
- **What is wrong:** `test_carry_r3k2_l2_no_kis_row_keeps_the_skip_branch` greps the file for `"not in this dataset"` and counts `raise KisiwaMissing()` occurrences. `test_..._fails_every_kis_row` tests only `failed_result` on a hand-built exception. No test runs `kis_3`, `kis_4` or `kis_9` (or `run()`) against a dataset with no Kisiwa Site.
- **Failure scenario:**
  - A later edit reverts `run()` line 1222 to the pre-K7 `{"status": "fail", "error": ...}`. The rows still fail, but `check.json` loses the carry's required `read: {"kisiwa": "missing: …", "checked": 0}` body, and all 81 L0 tests still pass (mutation survived).
  - Likewise, a skip that returns a different body while a comment still contains the literal `raise KisiwaMissing()` passes the count.
- **Fix:** add one behavioural L0 test.
  - Monkeypatch `demo_combined_finish._kisiwa_read` to return None, and `psycopg.connect` to a fake whose `fetchone()` is None (for KIS-4).
  - Run each KIS row through the same try/except that `run()` uses, or call `run()` over a filtered `CHECKS`.
  - Assert `status == "fail"` and `read == KISIWA_MISSING_BODY` for KIS-3, KIS-4 and KIS-9.

### L2 (Low): the S-2 order test cannot see a dropped link in the chain
- **Where:** `backend/tests/test_k7_kisiwa_story.py:125-134`, which tests `tools/demo_combined_kisiwa.py:268-279`.
- **What is wrong:** the test swaps adjacent instants inside the chain that `order_chain` itself returns. If `order_chain` loses an entry, the test swaps the remaining pairs and still passes. `test_2_the_story_calendar_for_a_fixed_S` looks up only four keys by name.
- **Failure scenario:** someone removes `("action.case_link_at", …)` from the chain, or a later card adds an instant without adding it to the chain. Then `case_link_at` could move after `plan.freeze_at` with no S-2 stop, and K7-F's freeze would precede the case link. The mutation survived.
- **Fix:** assert that the chain's names equal §9l.3's 14-item list, in order. Better still, also swap adjacent **calendar** values in the story document and expect `STORY_CLOCK_ORDER` from `resolve`, as the card says ("`STORY_CLOCK_ORDER` for each adjacent pair swapped").

### L3 (Low): only the physics run guard has a negative test; the history, log and dip guards can be neutered silently
- **Where:** `tools/demo_combined_kisiwa.py:468` (history), `:473` (log) and `:491` (dip). Tests: `backend/tests/test_k7_kisiwa_story.py:228-251`.
- **What is wrong:** `test_run_guards_hold_for_every_story_run` is positive only. `test_run_guard_physics_fails_on_a_changed_start_state` covers physics only.
- **Failure scenario:** removing the dip comparison or the history comparison leaves all 81 L0 tests green (both mutations survived). A scratch prepare would also pass, because the guards fire only on a mismatch. A future handover edit, or a K0 change that drops an effect-bearing action from a run's frozen history, would then go unnoticed by the guard meant to be stop S-5.
- **Context:** the card's L0 list does not demand these negatives, so this is a test-strength gap, not an acceptance gap. KIS-9 (b) and (f) give partial backstops on the dips and the history, but from `kisiwa.json` (see L4).
- **Fix:** add two negatives, each expecting `SystemExit`:
  - a deep-copied handover with one `dip_l` changed by 1 L, matching `RUN_GUARD_DIP`;
  - a handover whose `intervention_history` for run 2 is empty, matching `RUN_GUARD_HISTORY`.

### L4 (Low): two KIS checks have no isolating fail body, and KIS-9 (f) is self-attested from `kisiwa.json`
- **KIS-3:**
  - Where: `tools/demo_combined_rows.py:579`. Tests: `backend/tests/test_k7_kisiwa_story.py:416-434`.
  - What is wrong: the card's L0 item 9 asks for "one fail body per item". The "reproduced band" item has none. The `residual_low` fail case trips the tolerance check first, so deleting the reproduction assert survives.
  - Failure scenario: if the stored terms and the stored band ever disagree within tolerance (for example a rules-version drift), KIS-3 would still pass once the assert is lost.
  - Fix: add a fail body that changes only `terms["no_load_l_per_h"]` or `terms["accuracy_l"]`, so that the re-computed band differs while the five toleranced terms still match.
- **KIS-9 (f):**
  - Where: `tools/demo_combined_rows.py:664-669`.
  - What is wrong: the check reads the history and log sha that the build wrote into `kisiwa.json` (the guard's own output), not the frozen identity stored with each run in the database. The card's (f) says "every Kisiwa run's frozen identity names the derived log".
  - Failure scenario: a run whose stored identity differs from what the build recorded (a re-publish, or a hand repair of the DB) would still pass.
  - Fix, optional and K7-F-sized: read each Kisiwa run's stored deterministic identity (operational-action log id, version, sha and `intervention_history`) by `run_id`, and compare it to the derived log.

## Checks run (by me, on `63f60f986`)
- K7 L0 and adjacent tests: `pytest backend/tests/test_k7_kisiwa_story.py test_out_b2_vocabulary.py test_demo_combined_finish_rows.py test_demo_combined_links.py test_demo_story_days.py -q` gave **211 passed** in 30.1 s.
- `pytest test_demo_combined_finish_days.py test_demo_combined_finish_co1.py test_k4a_fuel_finding_rules.py test_k6a_fuel_action_origin.py -q` gave **39 passed** in 4.4 s.
- `tools/probe_kisiwa_fuel.py --check` printed "probe result current", exit 0. `tools/probe_kisiwa_nights.py --check` printed "probe result current (G6 pass)", exit 0.
- Mutations: 10 on a scratch copy, through the K7 L0 file (table above). The repository was not edited.
- Python: `AssetOpsV1-plan2\.venv`, with PYTHONPATH set to the k7 worktree's `backend;contracts;tools;simulator;gateway;host;field;backend\tests;host\tests`.

## Not verified
- Anything Postgres-backed. Under the brief I did not query `assetops_demo3_kisiwa_test`. The scratch prepare's outcomes (KIS-3, KIS-4 and KIS-9 pass, OPENED night 4, stamps, 4199.5 s) are the packet's claims, read for consistency with the code but not re-observed.
- The prepare's exit code was not captured in K7-D. R3n moves that check to K7-F's packet.
- `tools/check-all.ps1`, `check-architecture.ps1` and `check-agent-workflow.ps1` were not run in this review. The card lists them as guards, and the packet does not report them either. **The coordinator should confirm a guard run on the merge head.**
- No layout evidence applies (no UI in K7-D).

## Residual risk not in the packet
- **The three-Site pins are frozen against main's day list and story file at `78a224393`.** Any later main edit to `demo-story-days-v3.json`, `demo-combined-story-v1.json` or the resolver would break `test_1_*` at the K7-F merge. That would be correct behaviour (S-9), but it would show up as a K7 failure. The K7-F merge should rerun `test_1_*` after `git merge main`.
- **The guard step is missing from the packet.** K7-F's packet should list `check-all`, `check-architecture` and `check-agent-workflow` results for the combined head.
