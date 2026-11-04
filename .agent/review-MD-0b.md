# Review: MD-0b, mechanism dataset verification add-on (after fix round 1)

- Reviewer: fresh Claude (independent; not the author). Read-only on the branch.
- Branch `task/MD-0b-verification`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-md0b`, head `63e5c8f3b`, base main `ff499d54d`.
- Diff reviewed: `git diff ff499d54d...HEAD -- ':!.agent'` (13 files, +780/-126).
- Authority: build sheet MD-0 §14 Q3, §16-§19 (MD0b-R), plan rows MD0b-R and DS-R1, packet incl. "Fix round 1".

## Verdict: ACCEPT with one Medium fixed on the branch (M1 below, small); Lows optional

The slice does what §19 asks. ACT-K1 and ACT-K2 reach VERIFIED on real readings through the product's evaluator.
The close variant follows §2.6 e to the day. MD0b-R M1 holds, and the owned entries follow §19. One Medium: the new
wildcard is broader than its stated purpose, and it stays permissive after it is resolved. It is a 2-3 line fix,
plus one test.

## Checks run (by me, on `63e5c8f3b`)

| Check | Result |
|---|---|
| `git diff --stat ff499d54d...HEAD -- backend/assetops_backend` | empty: no product file changed |
| `tools/mechanism_dataset.py status` | exit 0: `assetops_mechanism_tpl_c3470a30_test` and `assetops_mechanism_tplc_c3470a30_test` usable (not rebuilt). A newer states template `tpl_7ed8e064` (19:47, another branch) also exists |
| L0/L1: `test_md0_fixture.py`, `test_md0b_ensure.py`, `tools/checks/test_chain_coherence.py` | **168 passed**, 5.5 s |
| L2m: `test_md0_mechanism_postgres.py` (`ASSETOPS_TEST_DATABASE_URL` = 127.0.0.1:55432/assetops_test, admin only; clones via pg_harness and `assetops_mechanism_c*_test`) | **7 passed, 0 skipped, 0 xfailed**, 440.5 s pytest / 442 s wall |
| Guard A `tools/check-architecture.ps1` (no `-ExecutionPolicy Bypass`) | passed |
| Guard W `tools/check-agent-workflow.ps1` | passed |
| `git merge-tree --write-tree HEAD task/CH-5a2-chain-endpoints` (`2f8b114d9`) | clean (tree `e66c8f5b5`), no textual conflict |

Values from my L2m record file:
- **Main.** ACT-K1 plan baseline `2026-10-29T05:30Z` (D11 08:30 local), later `2026-10-31T05:30Z` (D13 08:30), frozen
  `2026-10-30T21:42Z` (D13 00:42 local), baseline candidate 1,800 s. Outcome VERIFIED with
  `TARGET_AND_GUARDRAILS_PASS`; source classes baseline and later are both `AUTHORED_DEMONSTRATION`. Events ACCEPTED,
  APPLIED, RESOLVED. D-AW-3 record: `skipped 0`, state on D14 RECURRED.
- **Close.** VERIFIED. Thread OPEN and ACTION_IN_HAND 10-20 (D2), CHANGE_APPLIED and RESOLVED_MONITORING 10-21 (D3),
  CLOSED 10-28 (D10), RECURRED 10-31 (D13).
- **Undelivered D6-D9.** Every measure NO_DATA, none PENDING.

Not run, as briefed: the full suite, prepare, L3m `check --threads`, and the container runner `.sh`/`.ps1` path
(read only, below). I did not rerun the L3m "0 unexpected" claim, so it rests on the packet.

## Named items

- **No product change**: confirmed.
- **ACT-K1 VERIFIED on real readings, no monkeypatch**: confirmed. `verify_freeze` and `verify_evaluate`
  (`backend/tests/mechanism_dataset.py`) only call `POST .../verification/plans`, `.../later-selection` and
  `.../evaluations` on the `test_s6_verification_plan_postgres.verifying` harness. Nothing patches or replaces
  window evidence or source resolution. The test asserts both source classes and exactly one `verification_outcome` row.
- **Derived `generator_power`**: honest, labelled, and not tuned to pass.
  - In `verification_rules.py:371-536` the role only gates per-slot coverage, through `_SINGLE_POWER_ROLES`, and
    feeds `generator_kwh`. That total sits outside the verdict (`gen_total`, OUT-E E2). The cost check reads it
    afterwards (`verification.py:895`).
  - The verdict's target comes from dispatch `candidate_avoidable_seconds`, and comparability reads feeder, PV and
    SOC. So the 15 kW value cannot move the outcome; only its presence matters.
  - The rule, the value's source (`w4-mini-depth-cases-v1.json`) and the reason for using the status at the source
    time are all written in the fixture. `DERIVED_RULES` refuses any other rule text.
  - Choosing between the two rules: the status-at-source-time rule agrees with the generator status points. With
    the first rule, a positive mean sat after the last ON report. It is a modelling identity, not a threshold fit
    (see L3 for its one side effect).
- **Re-timed windows**: sound.
  - The baseline starts after the 30 min minimum runtime, on a 5-min UTC boundary, and inside the overrun.
  - The freeze comes after the baseline's UTC days are final (D11's UTC run reads to D12 06:00Z, and the freeze is
    D12 21:42Z). It also comes before any later-window reading.
  - The later window is the same UTC clock hour, two days on, on a non-overrun day. The sheet's original later
    window, D12, was also a non-overrun day, so the target is no easier than §2.2 intended.
  - Accepted by §19.
- **Close variant**: RESOLVED D3, CLOSED D10, RECURRED D13: confirmed (values above). See L1 on how tight the test is.
- **M1**:
  - The product mini worker drains the whole story (`drain_mini`, `MiniDepthWorker.run_pending` until a pass leaves
    none due; any FAILED raises).
  - D7 reads NONE (`readiness(...)` and the CH-5a1 `per_day[7] == NONE`).
  - Both MD-0 xfails and the CH-5a1 GAP-K7 xfail are now hard assertions. The FIX-MAIN-1 L1 owner strings are gone
    with them.
- **Owned entries**: correct.
  - COH-8 carries `MD0b-R:A1`, owner CH-5a2a, count 1 for each of week and month.
  - COH-6 ×4 carries `MD0b-R:A2`, owner CH-6a, exact subjects.
  - The §5 rule text gains the third kind, and `test_expected_mechanism_loads_and_only_names_declared_gaps` accepts
    `MD0b-R:`.
  - The spare-solar days are kept.
- **Close on demand (`ensure`)**: `auto|yes|no`, the path regex matches §19's list, `variants.close` is compared with
  the merge-base fixture, an unreadable diff builds, and a matching template is reused. The "close not selected"
  JSON line is printed. The `.sh` greps for it, adds `--deselect <real node>` and prints `CLOSE L2m NOT RUN`.
  It is never silent. Run directly with no template, the close test errors (`clone_template` raises); it does not
  skip. See L2 and L4 for the runner.
- **Drain in its own part**: `build` stops before `drain_mini` whenever a part already ran a step, and `_estimate`
  leaves the drain out of the ordinary-step estimate. The packet's part times are all under 540 s. `test_md0b_ensure`
  covers the estimate.

## Findings

### Medium

**M1. The `subject: "*"` wildcard covers any COH-8 finding at the window, and stays permissive once it is resolved.**
- **Where:** `tools/checks/chain_coherence.py:1095-1113`, `tools/checks/fixtures/chain_coherence/expected-mechanism.json`
  (the two COH-8 entries).
- **What is wrong:** `coh8_verified` (`chain_coherence.py:640-662`) puts three different problems into one finding:
  - the Portfolio row is not VERIFIED;
  - the progress row is missing;
  - `origin_revision_selected` is not True.

  The wildcard matches on (rule, site, window) only. So a regression on Kobo week or month, such as the progress row
  disappearing or the Portfolio row losing VERIFIED, is absorbed as long as it shows up as at most one COH-8 finding
  per window. In this dataset that is the only VERIFIED Action, which is exactly the one the entry covers.
- **Why it matters:**
  - After CH-5a2a merges, COH-8 reads `origin_selected` (`task/CH-5a2-chain-endpoints`, B6). The A1 finding then
    disappears and the entry becomes `resolved`.
  - A resolved wildcard does not fail `check` (`pass` is `not unexpected`). It keeps silently allowing one future
    COH-8 finding per window until someone deletes it.
  - An exact-subject entry that went stale would never match again, because Action ids change on each rebuild. The
    wildcard is strictly weaker.
  - CH-5a2a's branch does not touch `expected-mechanism.json`, so the "CH-5a2a deletes them" step is not guaranteed
    by either merge order.
- **Fix (small):**
  - Give a wildcard entry a required `detail` pattern, for example
    `"detail_match": "origin_revision_selected False$"` with nothing else in `problems`. Only match findings whose
    `detail` fits it.
  - Extend `test_wildcard_subject_expectation_is_bounded_by_count` so that a COH-8 finding with a different detail
    is unexpected.
  - Optional: make a resolved wildcard a failure, or at least a loud `STALE WILDCARD` line, so its deletion cannot
    be missed.
- This is an acceptance gap against "not hide a real regression", not a preference.

### Low

**L1. The close test accepts RESOLVED on D3 or D4 and CLOSED on whichever comes 7 days later.**
- **Where:** `backend/tests/test_md0_mechanism_postgres.py` (close test, the `md.day(...effective...) <= resolved <=
  md.day(...evaluate...)` and `resolved + timedelta(days=7)` lines).
- **What:** §2.6 e and DS-R1 fix the dates: VERIFIED is dated on the change's effective day (D3), so CLOSED is D10.
  The measured values are right, but a shift to RESOLVED D4 and CLOSED D11 would still pass.
- **Fix:** assert `resolved == md.day(SPEC, 3)` and `by_state["CLOSED"] == md.day(SPEC, 10)`.

**L2. The host runner's base fixture is likely mangled.**
- **Where:** `tools/run-backend-suite-in-container.ps1:85-86`.
- **What:** in Windows PowerShell 5.1, `git show ... | Set-Content -Encoding utf8` decodes git's UTF-8 through the
  console code page. Non-ASCII text in the fixture (`§`, already in the base's `late_fill.source`, and in
  `variants.close` after this merges) is mangled. `close_needed` then sees `variants.close` as changed whenever
  `mechanism-v1.json` is in the slice diff, and builds the close template (about 20 min).
- **Impact:** safe in direction (it over-builds and never skips), but it wastes time.
- **Fix:** have git write the file itself, for example `git -C $worktree show "${baseSha}:..." > $file` via
  `cmd /c`, or `git archive`. Alternatively set `[Console]::OutputEncoding = [Text.UTF8Encoding]::new()` around
  the two calls.

**L3. `generator_power` leads the other power channels by one interval.**
- **What:** the mean `[07:55, 08:00)` reads 15 kW while the 07:55 status point is STOPPED. `pv` and `dis` in the
  same interval take the interval-start values.
- **Impact:** it does not affect the verdict (coverage only), and the packet records why the status-at-source-time
  rule was chosen. It does add 1.25 kWh to the baseline `generator_kwh` that feeds the OUT-E cost check.
- **Fix:** note it in the fixture's `source` text for whoever reads trial fuel figures off MD-0. No code change needed.

**L4. "At E1/E4 and in the post-merge job" is only a comment.**
- **What:** `-Close yes` exists, but nothing in `backend/TESTING.md`, `.ai/ROLE_CONFIG.md` or any job invokes it.
- **Impact:** on `main` with `auto`, the diff is empty, so close is not selected unless a matching template
  already exists. The post-merge run would deselect the close test, loudly.
- **Fix:** add one line to `backend/TESTING.md`, or to the gate checklist the coordinator uses, saying E1/E4 and
  post-merge pass `-Close yes`.

**L5. The printed count can disagree with `pass`.**
- **Where:** `print_report` (`chain_coherence.py:1131-1135`).
- **What:** it counts every finding under a wildcard's (rule, site, window) as "expected", even past `count`.
  The NEW lines and `pass` are still correct (both come from `expected_unmatched`), but the per-rule summary line
  can say "0 new" while the run fails.
- **Fix:** derive `new` from `report["expected_unmatched"]`.

## Merge traps with CH-5a2a (`task/CH-5a2-chain-endpoints` at `2f8b114d9`)

- **Text.** `git merge-tree` is clean. CH-5a2a edits `chain_coherence.py` at `_board_findings`/COH-5, COH-7a
  (`window_day`), COH-8 (`origin_selected`) and COH-14. None of these overlaps MD-0b's `check`/`print_report`
  hunks. Its `test_chain_coherence.py` additions are disjoint from MD-0b's, and it does not edit
  `expected-mechanism.json`.
- **COH-8 entries.** After both merge, the two MD0b-R:A1 entries become `resolved` (see M1). Whoever merges second
  must delete them in that merge, and the coordinator should assign it.
- **COH-7a.** CH-5a2a changes COH-7a's card-day rule (`summary_day` becomes `window_day`). MD-0b's "L3m 0
  unexpected" was measured with the old rule, so rerun L3m `check --threads` on both variants after the second merge.
- **Template pruning.** `TEMPLATES_KEPT = 2` applies per kind across branches. A third states template, from a
  CH-5a2a or main build on this server, prunes the oldest. `tpl_7ed8e064` already exists next to `tpl_c3470a30`.
  This is existing behaviour, noted only because both lanes rebuild now.

## Residual risk not in the packet

- **D-AW-3 coverage.** It is no longer exercised on main, because A3 moved it to CH-6b R16. Until R16 lands, no
  data-level test covers the skipped-during-CHANGE_APPLIED path.
- **Runner path not executed.** Neither I nor the builder ran the `.sh`/`.ps1` runner. The logic reads correctly:
  the grep string matches the `json.dumps` output, and `set +e` covers the `[ -f ] &&` lines. The first container
  run should confirm `CLOSE L2m NOT RUN` appears when close is not selected.
- **Packet claim I could not verify.** The L3m "0 unexpected" was not rerun here.

## Re-review (fix round 2)

- Reviewer: fresh Claude (independent; not the author). Read-only on the branch; one plant made and reverted (`git status` clean after).
- Head `c6892d456`; fix diff `git diff 63e5c8f3b..c6892d456` (5 files, +58/-10).

### Verdict: ACCEPT

M1 is closed, L1 and L5 are fixed, and the close L2m passes with the L1 pin. Two new Lows below; neither blocks.

### Checks run (by me, on `c6892d456`)

| Check | Result |
|---|---|
| L0/L1 `test_md0_fixture.py`, `test_md0b_ensure.py`, `tools/checks/test_chain_coherence.py` | **169 passed**, 2.5 s |
| Plant: `check` wildcard condition `w.get("detail_contains") and w["detail_contains"] in f["detail"]` replaced by `True` | `test_wildcard_subject_expectation_is_bounded_by_count` **fails** (line 99, the different-detail case); 1 failed, 96 passed. Reverted |
| `tools/mechanism_dataset.py status` | both `c3470a30` templates (states `tpl_`, close `tplc_`) `usable: true`; not stale, not rebuilt |
| L2m `test_md0_mechanism_postgres.py` (`ASSETOPS_TEST_DATABASE_URL` 127.0.0.1:55432/assetops_test) | **7 passed**, 543.4 s pytest / 545 s wall (slower than the 440-457 s earlier runs; machine load, no stall) |
| Guard A `tools/check-architecture.ps1` (no Bypass) | first run exit 1: Rule 8 "no Python interpreter at '' or .venv" because this worktree has no `.venv` (environmental). Rerun with `ASSETOPS_GUARD_PYTHON` = the plan2 venv python: **passed** |
| Guard W `tools/check-agent-workflow.ps1` | passed |

Not run: L3m `check --threads` on either variant (not briefed as a rerun, and its derive writes the worktree's `var/` work folder). The packet's L3m numbers for this round rest on the packet.

### Named items

- **M1 closed.**
  - `check` (`chain_coherence.py:1109-1110`) absorbs a finding under a `"*"` entry only when the entry has a truthy `detail_contains` that is a substring of the finding's `detail`, and only while `used < count`. A wildcard without `detail_contains` matches nothing (tested: `pass is False`).
  - A different-detail finding stays unexpected and its entry is reported `resolved` (tested).
  - `count: 0` leaves the finding unexpected (tested). The count bound is per (rule, site, window).
  - `print_report` tags a resolved `"*"` entry `RESOLVED-WILDCARD (DELETE THIS ENTRY)` (tested via capsys).
  - Both A1 entries carry `"is VERIFIED, but its progress row has origin_revision_selected False"`, so a missing progress row or a Portfolio row that lost VERIFIED is no longer absorbed.
  - Non-vacuous: the plant above fails the test.
- **L1 fixed.** The close test asserts `resolved == md.day(SPEC, 3)`, `effective day == resolved`, and `CLOSED == md.day(SPEC, 10) == resolved + 7 days`. It passed in my L2m run.
- **L5 fixed.** Per-rule `new` now counts findings that are in `report["expected_unmatched"]` (by identity), so it agrees with `pass`. The new test pins `"<rule>: 1 finding(s), 0 expected, 1 new"` for the over-count case; the old logic would print `1 expected, 0 new` there and fail it.
- **COH-6 / variants.** There is one shared `expected-mechanism.json` and no variant field, so "COH-6 is close only" is enforced only by the note. On states the four COH-6 entries are reported `RESOLVED` and do not fail; that is what the builder described, and it is not a spurious unexpected entry. See N1 for the side effect.

### New findings (Low, neither blocks)

**N1 (Low). Close-only and main-only entries cross-apply because the file is not scoped by variant.**
- **Where:** `tools/checks/fixtures/chain_coherence/expected-mechanism.json` (the four COH-6 entries and the week COH-8 wildcard).
- **What:** the COH-6 subjects (`findings:opportunities`, `portfolio:opportunity`) are stable strings, not ids. A COH-6 regression on Kobo week or month with those subjects on the states/main variant would be absorbed silently. In the other direction, every close run prints `RESOLVED-WILDCARD (DELETE THIS ENTRY)` for the week COH-8 entry, which main still needs. That makes the new loud signal cry wolf on close, which weakens its value as the CH-5a2a deletion prompt.
- **Fix (optional):** add an optional `"variants": ["close"]` / `["states"]` field that `check` honours, or keep one expectations file per variant.

**N2 (Low, environmental). Guard A fails in a worktree without `.venv`.**
- **What:** Rule 8 needs `ASSETOPS_GUARD_PYTHON` in a worktree without `.venv`, or it reports a false failure. This is not caused by this slice. Builders and reviewers on sibling worktrees should set the variable.

### Residual risk

Unchanged from the first review and the packet: L2, L3 and L4 are open by choice. The CH-5a2a merge must delete both A1 entries and rerun L3m for COH-7a. L3m was not independently rerun in either review.

## Coordinator verification (merge prep, 9483db4e7) — ACCEPT
- Merge of main 27aa6a638 conflict-free; both MD0b-R:A1 COH-8 entries deleted (grep count 0).
- N1: `applicable(expect, variant)` filters entries with a `variants` list; ungated entries apply to all; the four MD0b-R:A2 COH-6 entries are `variants: ["close"]`. Double application in CLI + check() is idempotent. Test `test_variants_gate_expected_entries` covers the three cases.
- Builder evidence: templates rebuilt at c2615b00; L3m states 0 unexpected / COH-8 0, close 0 unexpected / COH-8 0 / COH-6 4 expected; no RESOLVED-WILDCARD; L0/L1 184 passed; L2m 7 passed; guards A, W pass.
