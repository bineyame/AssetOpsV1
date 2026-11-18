# Review packet: CH-5a2b (PC-1 count claims, COH-17, board off the estate snapshot, Q11 cutoff)

Branch `task/CH-5a2b-chain-counts`. Authority: `AssetOpsV1-plan2\.agent\build-sheet-CH-5a.md` §B13 as amended
by §B14, plus pre-flight `.agent/CH-5a2b-preflight.md`. Build record: `.agent/CH-5a2b-handoff.md`, which covers
phase 1 (`a8c748b7c`) and phase 2 (`c10d51658`..`0cdae5f9f`). This packet adds steps 0 and 5-8. `B` means
`backend/assetops_backend`.

## Outcome delivered
- **One count computation.** `chain/claims.estate_count_claims` produces the three PC-1 claims for
  `/estate/chain` `counts`, Portfolio `summary.claims` (3 keys) and Findings `summary.claims`
  (`count.opportunities`). Portfolio `summary.count_basis` is `count_basis(days)` (Q7, Q8, Q9).
- **COH-17.** The three bodies agree on value, basis and text in every estate and day window.
- **Board off the estate snapshot.** The mini board is read through `placement_facts` and `action_rows`. The
  `estate` port and `estate_bounds` are deleted. The diagnostic is renamed `ACTION_ROW_MISSING` (R1, Q1-Q5).
- **One cold/EV cutoff.** The board and the thread route share one cold/EV cutoff method (Q11).
- **Provenance wording.** The wording comes from the stored `source_class` (R2, Q6).

## Commits this session
- `5921ac43b` step 0: outcomes purity fix (deviation D1).
- `e595abc95` the w301 Postgres null-summary checks skip `summary.claims`, the same way the unit API test
  already does.
- `09957c0f6` merge of main (MD-0b, `692e4d57e`). The merge was clean: `chain_coherence.py` keeps both
  `variant=`/`applicable()` and COH-17.

## Acceptance (§B10/§B13/§B14 targets)
| Target | Status |
|---|---|
| One computation, three bodies (Q7) | Met. COH-17 = 0 on the clone, MD-0 states and MD-0 close |
| COH-17 non-vacuous | Met. The manifests are stamped `claims: true`. The windows S/week/month plus 11 (states), 14 (close) and 13 (clone) day windows were judged. The planted-change proof is from phase 2 (handoff) |
| A/B chips and labels only in Q3 classes | Met. The clone A/B (main `692e4d57e` against this slice, same clone) shows **0 board differences**. All 28 differing files differ only in `summary.claims` (added), `summary.count_basis` (1 window) and `known_at` (6 action_index bodies, the collection instant) |
| Every VERIFIED item carries its `source_class` wording | Met. 10/10 `result_label` read "Verified on example data", and all 5 `VERIFIED_WATCH_RETURN` reasons read "Change verified on example data; ...". A and B are identical |
| `count_basis` old -> new listed | See below |
| Claims at `known_at` against the legacy `opportunity_count` | Reported, no difference: equal in every window of all 3 datasets |
| "on the days checked" only in GAP-K7/C3/E2 windows | **Not met. Reported, not adapted** (D2) |
| Payload sizes | See below |
| Day A `failed` value (`test_out_b4_board_postgres`) | `[]` for Day A and Day B (before this slice: `["estate"]`). `port_errors` `[]` |

### `count_basis` old -> new (Portfolio `summary.count_basis`)
| Dataset | Window | A (main) | B (slice) | Screen text changed |
|---|---|---|---|---|
| polish clone | S 31 Oct | `null` | `CHECKED_DAYS` | **None.** Every input the client gates on that basis is null or empty: `evidence_gap_site_count` null (PulseCount and `evidenceGapText` show "Unknown" / "evidence gaps not assessed"), PROTECT `sites_with_primary_finding` null ("Not assessed"), `checked_days` `[]` (`checkedDaysClause` returns null) |
| polish clone | week, month | `CHECKED_DAYS` | `CHECKED_DAYS` | none |
| MD-0 states | S / week / month | `COMPLETE` / `CHECKED_DAYS` / `CHECKED_DAYS` | same | none |
| MD-0 close | all | not A/B'd (no A collect on the close DB) | `COMPLETE` / `COMPLETE` / `CHECKED_DAYS` | n/a |

### Claims against the legacy fields (info for CH-6b, Q7; no screen text changes)
- **polish clone S and week:**
  - `verified_resolution_count` 1, but `count.verified_results` 0.
  - `priority_site_count` 0, but `count.open_threads` 1.
- **polish clone month:** both pairs are equal (1/1 and 0/0).
- **MD-0 states:**
  - S: `priority_site_count` is `null`, but `count.open_threads` is 0.
  - week and month: equal.
- **MD-0 close:** equal in every window.
- **`opportunity_count`:** the legacy value, read at `scope.k`, equals `count.opportunities`, read at the
  request's `known_at`, in every window of all three datasets (Findings and Portfolio).

### Payload sizes (collected bundle files, bytes)
| Dataset | `/estate/chain` S / week / month | All chain bodies (estate, site and day) |
|---|---|---|
| polish clone | 6707 / 6718 / 6715 | 29 files, 1978-8329 |
| MD-0 states | 5084 / 5138 / 5152 | 25 files, 1921-6855 |
| MD-0 close | 1925 / 1925 / 1995 | 31 files, 1924-5209 |

## Checks run (this session; machine otherwise idle)
- **Unit tests (L0, localised):**
  - outcomes, warnings and board family (a1, c1, c2, c_rules, pa2a, pa2b, b1, b2, b3): 143 passed.
  - Adjacent (c3, c4, d4, b4 read/route/window/imports, b1 status, e4, cc_placement, ch5a2b_claims, b2
    vocabulary): 285 passed.
  - After the merge, `test_chain_coherence` + `test_md0b_ensure` + `test_out_a1_outcome_map`: 129 passed.
- **Postgres (L2, `assetops_ch5a2b_test`, created for this slice), 1-2 files per call:**
  - `test_ch5a2_chain_api_postgres` + `test_ch5a1_reader_postgres`: 13 passed, 44 s.
  - `test_w301_estate_index_postgres` + `test_w303_portfolio_fixture_postgres`: 19 passed and 3 failed, 501 s.
    The failures were `all(v is None ... if k != "opportunity_count")` tripping on the new `summary.claims`.
    They were fixed in `e595abc95`, and the 3 tests were rerun: 3 passed, 61 s.
  - `test_s6_action_store_postgres`: 12 passed, 103 s.
  - `test_out_b4_board_postgres`: 5 passed, 179 s. The Day A test was rerun with `-s` for the record.
- **MD-0:**
  - `status` gave `usable: false` for both variants.
  - `build --variant states --budget 540`: 3 parts (exit 3, 3, 0), seed 1162 s, template `tpl_b2120e5d`.
  - Without building, `ensure`'s auto rule was evaluated: it selects close, because the slice touches
    `B/chain/threads.py`.
  - `build --variant close --budget 540`: 3 parts, seed 1233 s, `tplc_b2120e5d`.
  - derive: 50 s (states) and 92 s (close).
- **L3m:**
  - `check --threads var/<work>/expected-threads.json --expect expected-mechanism.json --variant states`: all
    COH 0, 0 new, self-check 0/0.
  - The same check with `--variant close`: COH-6 4/4 expected (the close-only MD0b-R:A2 entries), every other
    rule 0, 0 new, self-check 4 pass.
  - As in MD-0b, no `settle` was run on the L3m DBs.
- **L3 polish clone `assetops_chainclone_ch5a2b_test`:**
  - Steps: create --migrate, backfill a-d (a 139 / b 9 / c 3 / d 6), settle (tick COMPLETED).
  - collect B: 85 x 200, `PGOPTIONS` read-only, `--work` the scratch `polish_work`.
  - check against `expected-today.json`: COH-2 2/2 and COH-7 8/8 expected, COH-17 0, every other rule 0,
    0 new, self-check 10 pass.
  - collect A: 56 x 200, from a temporary main worktree after its own read-only evidence and performance
    comparison.
  - Then the clone was dropped and the A worktree removed.
- **Guards (`tools/check-all.ps1 -Python <plan2 venv>`, after `npm ci` in `frontend`):** 14/14 PASS at `09957c0f6`, exit 0. Architecture seams, estate self-tests, navigation, agent workflow, dependency registry, delivery and mock-gap fixtures, missing-claim scan and fixtures, evidence width, mock deviation labels, screen ledger, chain coherence (103), event register (12).
- **Not run (owner testing rule):** the full suite, demo prepare, `test_demo_combined_postgres`, and the L2m
  `test_md0_mechanism_postgres`.

## Known deviations
- **D1 (step 0, pre-existing on main from CH-5a2a): outcomes purity.**
  - The problem: `outcomes/warnings.py` imported `chain.refs`, which broke `test_outcomes_package_is_pure`.
  - The fix keeps the allowlist unchanged, as CH-3 did. The test's rule allows stdlib typing plus `outcomes`
    only, and `chain.refs` also imports `urllib.parse`.
  - `WarningFacts.links` takes the `chain.refs` vocabulary (`estate_ref`, `evidence_ref`, `site_ref`,
    `href_for`), and `visits.warning_facts` passes `links=refs`. `Warning` carries `href`, set in `_make`.
    `_eref` and `_plan_ref` take `links`. `PLAN_LINK` becomes `PLAN_VIEW`. `PlanCue.link_ref` now defaults to
    None; the composer always passed the preventive Ref, `mini.plan_fact`.
  - A missing injection raises in `_links`.
  - Tests follow. They pass `links=R`, through a `partial` in c1/c2, and c_rules' `plan()` passes the Ref.
    Wire output is unchanged: no board A/B difference.
- **D2: "on the days checked" outside the GAP windows. Reported, not adapted.**
  - **MD-0 states.** The texts appear in week and month, both of which contain GAP-K7, and also in the day
    windows 2026-10-19 and 2026-10-28. Those two windows do not contain 10-25.
    - Cause: the estate day window spans two UTC days (`10-18..10-20` and `10-27..10-29`), and one of those
      days is outside the states day set (`no_data`). So the grade, and with it the text, is CHECKED_DAYS.
    - The GAP-K7 day window itself (`10-24..10-26`) reads NOT_KNOWN ("Not known yet"): all its days are
      no_data.
  - **MD-0 close.** The texts appear in month and in day 10-19, for the same reason.
  - **Polish clone.** Every window and every day window is CHECKED_DAYS. No day there grades `complete`; the
    grades are low, partial or no_data. Polish has no declared GAP days, so the target cannot hold there.
    Before this slice, week and month already read CHECKED_DAYS.
  - Owner of the question: the Architect. Either the target is restated (any `no_data` or below-complete day
    in the window, not only declared gaps), or the day-window span or the day set changes. No code was tuned.
- **D3.** `summary.claims` is new on Findings and Portfolio, so the w301 Postgres null-summary assertions now
  exclude it (`e595abc95`). This matches `test_w301_estate_api:134`.

## Residual risk
- The template prune policy keeps the two newest per variant. The states rebuild dropped the older
  `tpl_7ed8e064`, and the close rebuild dropped `tplc_c3470a30`. Main's `c2615b00` pair is kept.
- The close DB was not A/B'd for `count_basis`. The states A/B showed no change.
- `EstatePortfolioService.site_work_rows*` is unused by the board and kept (handoff).
- `frontend/node_modules` was installed in this worktree for the guards; it is untracked and gitignored.

## User-review focus
- D2: the "on the days checked" target needs an Architect ruling. It holds for no dataset as worded.
- The Q7 info list: on the clone, `verified_resolution_count` and `priority_site_count` differ from the claims
  in S and week. This is for CH-6b.
- D1: the injection shape (`WarningFacts.links`) against a relocated pure Ref module.

USER_REVIEW_REQUIRED: see the task file. The slice is backend only, with no frontend file touched; the merge
waits for review.
