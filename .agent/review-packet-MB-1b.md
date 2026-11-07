# Review packet MB-1b: the mill's thread line on the Kobo board's Grow row

- Task: FUEL-1 MB-1b, as ruled in `.agent/build-sheet-FUEL-1.md` "MB-1-R" §1 Q2/Q3/Q6 and §3 (the MB-1b card), amended by "MB-1a-R2" §1 (no policy -> no line; policy via `BoardServices.thread_policy`).
- Branch `task/FUEL-MB1b-mill-thread-line`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-mb1b`, from main `da51c7a8a`. Build commit `132e2f9c8`.
- **Status: built, ready for first review.** Size about 0.45 of the 0.55 card (stop S-j at 0.65 not reached). No stop fired (S-g, S-h, S-i, S-j).
- PV-1 had not merged when this was built. The card adds no `SiteFacts` field (the new fields are on `OpportunityActionFact`, defaulted, last), so the PV-1 "last `SiteFacts` field" rule does not apply. Both PV-1 and MB-1b edit `_row` near the thread-line loop; whichever merges second resolves there.

## Outcome delivered

- `mini.compose` builds the mill thread's `lifecycle.thread_view` per opportunity Action (`opportunity_thread`), with the lifecycle runner's own fully checked days over the board's `day_facts.rows`, its segment from `site_chain.actions_of`, the first MOVES category, and `count_known`.
- `board.opportunity_line_item` renders the Grow row's line in the three new literals; `_row` appends it after the Finding lines (text de-duplicated, subline joined as before).
- `thread_line_item`'s inner `item` is lifted to `_line_item` unchanged; every existing thread line is byte-equal.
- MILL-4 is written (runs at E3) with a pure `mill_thread_line` check and an L0 self-test; F-THREADS reports the S-8 Grow line's kind and text.

## Files materially changed

| File | Change |
|---|---|
| `backend/assetops_backend/site_outcomes/board.py` | `OPP_THREAD_MONITORING/CLOSED/SEEN_AGAIN` (verbatim §3.2); 4 defaulted `OpportunityActionFact` fields; `_line_item` (lift); `opportunity_line_item` (MOCK DEVIATION MD-FUEL-MB1-2 in its docstring); `_row` opp loop |
| `backend/assetops_backend/site_outcomes/mini.py` | imports (`chain.lifecycle`, `SITE_TYPE_OF_DOMAIN`, `categories_for`, `thread_signal_key`); `opportunity_thread` (§3.3 steps 1-7); the `opp` build passes its fields |
| `tools/demo_combined_finish.py` | `mill_thread_line` (pure), `_opp_line_text`, MILL-4 row (before MILL-5); F-THREADS `mill_line_s8` |
| `backend/tests/test_mb1_thread_line.py` (new, L0) | 33 tests: every kind, no-line cases, S-8/S+0/CLOSED compose shapes, parity, no policy, window guard, category, subline, rows byte-equal, MILL-4 pass/fail |
| `backend/tests/test_out_b2_vocabulary.py` | the three literals beside `THREAD_MONITORING` |

## Acceptance criteria (card §3)

| Item | Status | Evidence |
|---|---|---|
| 3.2 literals verbatim, in the vocabulary list | Met | `board.py` beside `THREAD_RECURRED`; `test_out_b2_vocabulary.py` passes (guards V/N accept, no S-g) |
| 3.2 BEFORE_CHANGE = bare `THREAD_BEFORE` | Met | `test_before_the_change_is_the_bare_before_line` |
| 3.3 four defaulted fields | Met | `OpportunityActionFact` |
| 3.3 steps 1-7 (occurrences `< end`, visible events, runner's measures/subject/starts, view, `count_known`, `actions_of` segment, category) | Met | `mini.opportunity_thread`; S-8, S+0, CLOSED, parity, window-guard, category tests |
| MB-1a-R2: policy None -> no view, no line | Met | `test_no_policy_gives_no_view_and_no_line` |
| `_line_item` lift, Finding lines byte-equal | Met | `test_ch3_rows.py` unchanged and passing |
| `opportunity_line_item` cases 1-5, thread ref | Met | kind tests + 8-case `test_no_line` |
| `_row` opp loop, sorted, category match, new text only | Met | compose tests; subline test |
| MOCK DEVIATION MD-FUEL-MB1-2 + packet row | Met | docstring + `_row` comment; row below |
| MILL-4 + L0 self-test (pass and fail) | Met (runs at E3) | `test_mill4_passes_each_kind` x3, `test_mill4_fails` x8 |
| F-THREADS S-8 line report | Met (runs at E3) | `f_threads` `mill_line_s8` |
| R4: Cold/EV unchanged; Optimize/Protect byte-equal | Met | `test_out_b3_cold_ev.py` unchanged and passing; `test_optimize_protect_and_assure_rows_are_byte_equal_with_and_without_the_line` |

## Mock deviation register row

| ID | Surface | v69 | Built | Why |
|---|---|---|---|---|
| MD-FUEL-MB1-2 | Kobo board, Grow row subline | no thread line on Grow | the mill's opportunity thread line ("Change checked and working ...", "... checked and closed ...", "Spare solar seen again ...") after the sales subline | MB-1-R Q2/Q3: the CH-3 thread line (already a deviation on Optimize) extended to an opportunity thread, in opportunity wording |

## Expected client view (computed at E3 by MILL-4; L0 shapes shown here)

| Story day | Grow row, the mill's line |
|---|---|
| S-11 | none (the Action is not listed before it is raised: MB-1a `opportunity_actions`) |
| S-8 | MONITORING: "Change checked and working (ACT-002) · {k} more fully checked days to close", k = 7 - fully checked days since the verified day (S-9) up to S-8 (L0 shape: `test_s8_shape_...`, the later occurrence excluded) |
| S-5, S-1, S+0 | RECURRED: "Spare solar seen again on 31 Oct after the change (ACT-002)" when the 10-31 recurrence is a visible started occurrence (L0 shape: `test_s0_shape_...`); else the S-8 kind |

`display_code("ACT-000002")` renders "ACT-002"; the card's table writes the stored code.

## Pre-flight interpretations (no redesign; flagged for the reviewer)

- P1. `effective_day` follows `thread_line_item`: change day for MONITORING/CLOSED/BEFORE_CHANGE, `recurred_day` for RECURRED. MILL-4 reformats RECURRED from `effective_day`.
- P2. Step 3 `starts`: every visible occurrence of the thread in `ct.rows` (not only those started by the board day), as `thread_clean_days` does. A later start lies after the board day, so `checked_days` (bounded by the day) is unaffected.
- P3. The line needs `facts.day`, which `read.py` board() sets after compose (only with a thread lookup port), exactly as for Finding lines. The compose tests set it the same way. No `read.py` change.
- P4. MILL-4's pure check lives in `demo_combined_finish.py` (card's file list); its self-test is in `test_mb1_thread_line.py`.

## Checks run

Python `AssetOpsV1-plan2\.venv`; PYTHONPATH absolute under the worktree; `assetops_backend` and `assetops_contracts` resolve into the worktree.

| Check | Revision | Result |
|---|---|---|
| `tests/test_mb1_thread_line.py` | `132e2f9c8` | 33 passed |
| Adjacent L0: `test_ch3_rows`, `test_out_b2_mini`, `test_out_b3_cold_ev` (unchanged), `test_out_b2_vocabulary`, `test_mb1_opportunity_board`, `test_demo_combined_finish_rows`, `test_demo_combined_finish_co1`, `test_out_b4_imports`, `test_ch9b1_origin_readers`, `test_ch5a1_board_contract`, `test_ch5a2_contract`, `tools/checks/test_chain_coherence.py` | `132e2f9c8` | 369 passed |
| Broader L0 (`test_out_*`, `test_ch*`, `test_mb1*`, `test_pv1*`, `test_estate_*`, `test_portfolio*`, `test_w303*`, `test_demo_combined_finish*`, non-Postgres) + `test_chain_coherence.py`, `-n 4` | `5220ad13a` (main + PV-1 merged) | 1438 passed, 1 skipped, **1 failed**: `test_ch1a_grading.py::test_period_bounds_addis_utc_tue_only_and_24h` (`ValueError: unknown period 'midday'`). Not this slice: the test, `chain/grading.py` and `chain/policy.py` are identical to main (CH-9 removed the midday period; stale test on main) |
| Postgres, DB `assetops_mb1b_test` (harness clones): `test_mb1_site_actions_postgres`, `test_ch9b1_opportunity_actions_postgres`, `test_ch9b3_mill_verdict_postgres`, `test_out_b4_board_postgres`, `test_ch5c2_real_composers_postgres` | `132e2f9c8` | 26 passed, 0 skipped, 856 s wall |
| `tools/check-all.ps1 -Python <venv>` (`ASSETOPS_GUARD_PYTHON` set) | `5220ad13a` | 15 of 17 PASS; the 2 missing-claim guards failed on `MODULE_NOT_FOUND` (no `frontend/node_modules`). After `npm ci`: `missing-claim-scan.mjs` passed, `test_missing_claim_scan.mjs` 26 pass / 0 fail |

Not run, per dispatch: prepare, baseline build, full suite, `test_demo_combined_postgres`. MILL-4 and F-THREADS run at E3.

## Known deviations

- None from the card. P1-P4 above are interpretations of unstated details.

## Residual risk

- The Postgres run was on the pre-merge build commit. The PV-1 merge auto-resolved with no conflict (PV-1 added a `SiteFacts` field and a `verdict_value` port; MB-1b adds none). The merged revision passed L0 only.
- The real `k` for S-8 and whether the 10-31 recurrence is a visible started occurrence on S-5..S+0 are only proven at E3 (MILL-4). S-i (a counted lifecycle day missing from `day_facts.rows`) can only appear on real rows. L0 parity shows both sides use one function over the same inputs.

## User-review focus

- The Grow subline wording on S-8 vs S+0 (MONITORING then "Spare solar seen again on 31 Oct ...") next to the Assure row's "verified" mill entry (MB-1-R Q4 accepted this reading).
- USER_REVIEW_REQUIRED: not on its own. It goes into the combined owner walkthrough.
