# POLISH PA-2a review packet: server copy, codes and titles

Task: `tasks/POLISH-PA-2a-server-copy.md`. Branch `task/POLISH-PA-2a-server-copy` from main `4681ba7d8`.
Contract: `.agent/build-sheet-POLISH.md` §3 and §3.1 BE rows, §5 PA-2, Addendum 3 (captures), Addendum 4 (titles),
Addendum 6 (split; Q1, Q3, Q5, Q6, Q8, Q9, Q10). USER_REVIEW_REQUIRED: no (merge on review ACCEPT).
Captures: deferred to PA-3 (Addendum 3). The exact-output tests below are the screen proof until then.

## Outcome delivered

| Item | Change |
|---|---|
| Display codes (§3, Q8) | New `outcomes/display_code.py` `display_code()`: prefix + number padded to at least 3 (`ACT-000001` → `ACT-001`, `ACT-001234` → `ACT-1234`; other text unchanged; written without `re` because `test_out_a1` keeps `outcomes/` pure). Applied in `warnings.py` refs (work case, plan), `board._item_text`/`_action_name`, `mini.py` verification lines, `cold.py:313,354`, and the work labels built from codes: `global_index` linked request and detail labels, `global_detail` "Incident {code}", `domain_action_index` "Maintenance request {code}", `operational_index` labels. Stored and wire `code`/`action_code`/`public_code` fields are unchanged. |
| Finding labels (§3 ids, Q3) | `finding_label(title)`: the stored title, else "Finding". `estate/index.py` `finding_label` from the row title. `_ReadTx.finding_titles()` (new SQL `_FINDING_TITLES`) feeds `_finding_link` in `site_index`, `global_index` and `global_detail`. `title` added to `_IndexTx.finding_revisions`; domain Action detail (cold, EV), domain rows and W1 rows use it (`_title_label`). |
| RECURRED (Q3) | `estate/coverage.py` maps every head's title by Finding before the window filter and carries `recurs_after_title`; `index.py` passes `_recurs_after_title`; `placement._reason` gives "Happened again after an earlier occurrence ({title})" or, without a title, "Happened again after an earlier occurrence" (`RECURRED_TITLED` is a separate constant so `REASON_TEXT` keys are unchanged). |
| Action labels (Q9) | `site_index.action_label()`: the display code, else "Action". The W4 site index reads codes through the new `_ReadTx.action_codes()` (the `_ACTION_CODES` SQL moved from `postgres_global_read.py` to `postgres_work_read.py`; global imports it). `global_index.coded_actions` uses the same helper; basis pairs keep stored codes. |
| Finding titles (Addendum 4, Q1) | `finding_episode.TITLES` SUPPORTED/UNCONFIRMED/NO_LONGER_SUPPORTED per Addendum 4; MERGED unchanged. Golden manifest edited directly (see deviations). |
| §3.1 BE strings | `evidence_money.CURRENT_VIEW` "Current view"; `placement` EPISODE_OPEN "No end time yet"; `portfolio.workflow_label(None)` "No action agreed yet", with `placement._ACTION_REASON` and `board.WORKFLOW_IN_HAND` keyed to it; `DISPLAYED_VALUE["WITHHELD"]` "Can't be compared across these sites yet"; `cold_site_reads.ATTENTION["COLD_START_FAILURE"]` "Backup generator did not start on its own". |
| Q5 TRANSFER | `COLD_OBSERVATION_WORDS`, `UNREADABLE_OBSERVATIONS` and `plain_limitation` moved into `analytics/cold_site_reads.py` (estate re-exports them; an analytics → estate import would invert the package direction). TRANSFER reads "No record of switching to backup power."; `ColdSiteReadService._limits` applies `plain_limitation`, so the backup summary no longer shows "Not observed: TRANSFER.". Stored analytics unchanged. |
| Q6 trial cost | `board.COST_PREFIX` "Estimated effect of the trial (not money saved): ", `COST_CHANGE` "…{amount} {currency} less supply cost per kWh.", `COST_NO_CHANGE` "…no lower supply cost per kWh.", `TRIAL_ATTRIBUTED` "Goal before the trial: {before}; after: {after}.". `mini.VERIFIED_WITH_COST` "{code} verified on test data: estimated effect of the trial (not money saved): {amount} {currency} less supply cost per kWh". `trial_fuel_comparison.LABEL` unchanged (stored). |
| Q7 | `UTC_SUFFIX` unchanged. |
| "critical load" | Confirmed frontend-owned (PB-2): the server labels in `binding_roles.py:115,119` are already "Critical load requested/delivered power". |

## Files materially changed

- Backend: `outcomes/display_code.py` (new), `outcomes/warnings.py`, `site_outcomes/{board,mini,cold}.py`,
  `analytics/{cold_site_reads,finding_episode}.py`, `estate/{coverage,index,placement,portfolio,evidence_money}.py`,
  `work/{site_index,global_index,global_detail,domain_action_index,operational_index}.py`,
  `work/adapters/postgres_{work_read,global_read,domain_action_index}.py`.
- Tools: `tools/w601_seed.py` (finds the linked Finding by href, not by the old label),
  `tools/s602b_test_scoped_cases.py` (expected workflow label).
- Tests: new `backend/tests/test_polish_pa2a_server_copy.py` (14 pure tests). Mechanical updates in
  `test_cc_placement{,_postgres}`, `test_idx_gaps_board`, `test_out_b1_board`, `test_out_b2_mini`,
  `test_out_b3_cold_ev`, `test_out_c3_cold_cost` (fake record codes padded, e.g. `MR-5` → `MR-005`, so the inputs read
  like stored codes), `test_out_e4_readback{,_postgres}`, `test_polish_pa1_board_truth`, `test_w204_cold_reads`,
  `test_w302_*` (5 files), `test_w303_portfolio_{api,workflow_labels}`, `test_w301_estate_index_postgres`,
  `test_w401_site_indexes_postgres`, `test_w502_domain_{action_index,intent,work_links}_postgres`,
  `test_w504_ev_intent_api`, `test_w601{a,b,c}_*`, and `fixtures/w3/w301-estate-golden.json`.
- Records: task file, `.agent/mock-departure-register.md` R640, `.ai/CODE_STATE.md` "POLISH PA-2a".

## Acceptance criteria

1. Display codes in server labels and sentences; stored and wire fields unchanged: **met**
   (`test_display_code_*`, `test_board_item_text_*`, `test_warning_ref_labels_*`, `test_mini_verified_results_*`;
   Postgres: w601a/b/c and w502 now assert `display_code(stored)` labels).
2. Finding labels are titles, else "Finding"; RECURRED text: **met** (`test_finding_links_read_the_revision_title`,
   `test_placement_reason_texts`; Postgres: w401, w502, w504, w601, w301 index assert the stored titles).
3. Action labels are the display code, else "Action": **met** (`test_action_links_*`, w601c `coded_actions` test,
   w401 asserts `ACT-[0-9]{3,}`, w502 work links assert `display_code(stored code)`).
4. Titles per Addendum 4; golden edited: **met** (golden replay 6 passed after the 2 mixed-branch labels were fixed).
5. §3.1 BE strings, Q5, Q6, Q7: **met** (`test_placement_reason_texts`, `test_no_action_agreed_yet_*`,
   `test_portfolio_and_estate_labels`, `test_cold_read_copy_and_transfer_observation`, `test_trial_cost_*`).
6. Pure pins plus mechanical updates: **met**.
7. Captures deferred to PA-3; R640; guards: **met**.

## Old → new (server strings)

- "Finding {id8}" → stored title / "Finding"; "Action {id8}" → "ACT-001" / "Action".
- "Returned after an earlier episode (Finding {id8})" → "Happened again after an earlier occurrence ({title})".
- "No end is recorded for this episode" → "No end time yet". "Recommendation not accepted" → "No action agreed yet".
- "Not comparable for this selection" → "Can't be compared across these sites yet". "Opens current Site view" → "Current view".
- "Automatic generator start failed in the accepted record" → "Backup generator did not start on its own".
- Cold observation codes (review L2). The cold Site read now applies the whole estate map, so each stored
  `Not observed: CODE[, CODE].` fragment becomes one plain sentence per code (estate already did this):
  - GRID: "Not observed: GRID." → "No record of a grid power loss."
  - START_REQUEST → "No record of a generator start request."
  - START_RESULT → "No record of a generator start result."
  - GENERATOR → "No record of the generator running or failing."
  - TRANSFER → "No record of switching to backup power." (estate was "No record of power transferring to the generator.")
  - BUS → "No record of the electrical bus state."
  - COMPRESSOR → "No record of the compressor state."
  - PROBE → "No record of a room temperature reading."
  - A malformed or unknown fragment → "Some required observations have no readable description."
  - Only TRANSFER's words changed; the other seven are new only on the cold Site read. GENERATOR's "running" is
    existing estate copy, unchanged and not ruled here.
- "Action ACT-000001" (estate/Portfolio `action_title`, review M1) → "Action ACT-001".
- Earlier detail join (review L1): "…per kWh. · Goal before the trial: …" → "…per kWh. Goal before the trial: …"
  (a part that ends a sentence is followed by one space; otherwise " · " stays, e.g. "Not calculated yet · Goal …").
- "Modelled change after the trial · not realised savings: … per kWh of feeder demand" → "Estimated effect of the trial (not money saved): … supply cost per kWh."
- "{label} before the trial: {b} · after: {a}" → "Goal before the trial: {b}; after: {a}."
- Banned-word swaps: none were needed beyond Addendum 4's titles.

## Checks run (revision `987761898` unless noted)

- New pure tests: `test_polish_pa2a_server_copy.py` 14 passed.
- Unit files without a DB (affected set): 1112 passed, 585 skipped (Postgres modules). Three `_postgres` modules
  failed only because no URL was set (`ArgumentError … got None`), and 61 collection NameErrors come from
  Postgres-only modules run without a DB. Both are environment artifacts; the same modules pass in the Postgres runs below.
- Focused Postgres (9 files: w401 site indexes, w502 ×3, w504 EV intent API, w601a/b/c, w301 estate index): 103 passed
  after the fixes (`81873eba4`; the first pass found 20 label pins, all updated).
- Sheet-scoped regression, host wrapper, `-n 4 --dist loadfile`, `-k "(estate or portfolio or work or warning or
  outcome or finding_episode or vocabulary or polish or placement or board) and not w301_estate_golden"` over its 113
  collected files at `81873eba4`: 41.0 min wall; JUnit tests=813, failures=3, errors=0, skipped=0.
  - `test_out_b4_board_postgres` and `test_out_d5_objectives_postgres`: the `s602b` producer pinned "Recommendation not
    accepted". Fixed in `987761898`; both files rerun: 8 passed.
  - `test_w401_work_service_postgres::test_foreign_asset_and_evidence_refuse`: `WORK_OCCURRED_AT_FUTURE` instead of
    `WORK_LINK_SCOPE_INVALID`. It also fails on main `4681ba7d8` (run from plan2), so it is pre-existing and
    date-dependent, not caused by this slice.
- Golden replay (coordinator go-ahead), `tools
un-host-tests.ps1 -- backend/tests/test_w301_estate_golden_postgres.py -q`
  at `53b02604c`: 3.4 min wall; 4 passed (mini_grid, cold, ev branches), **2 failed** (`[mixed]` manifest replay and
  clock+30 days): `findings-mixed-week $.rows[0].finding_label: actual 'Generator may have been on longer than needed'
  != expected 'Finding 00000001'`. The mixed branch holds 2 literal `"finding_label": "Finding 00000001"` values
  (deterministic ids, not `$derive` markers) that the direct edit missed. Reported to the coordinator before any fix.
  - Fix (coordinator OK): those 2 strings now read "Generator may have been on longer than needed"; rerun at the fix
    commit: **6 passed**, 0 failed, 3.9 min wall.
- Not run: the full suites.
- `tools\check-all.ps1 -Python …plan2\.venv\Scripts\python.exe`: All 11 guards passed.

## Known deviations

- **Golden titles.** Addendum 6 said 12 strings. The manifest also held 2 NO_LONGER_SUPPORTED titles, which changed
  with `TITLES` and were edited too.
- **Golden labels.** The 12 `finding_label` markers (`{"$derive": "finding_label"}`, which built `Finding {id8}`) are
  now each row's literal title. The `finding_label` derive rule (`test_w301_estate_golden_postgres.py:430-431`)
  is now unused and is kept, with no code change (review L3).
- **Board title words.** `mini.FINDING_TITLE` (the board names a mini Finding by its lifecycle) is unchanged.
  `test_idx_gaps_board::test_board_finding_titles_are_the_frontend_plain_titles` pins it equal to frontend
  `findingWords.ts` `LIFECYCLE_WORDS`, which PB-2 owns. Changing both together belongs to PB-2 (or a small fix after PB-2).
- **Unruled cost wording.** `board.COST_NOT_CALCULATED` ("Modelled change not calculated: …") was not ruled and is unchanged.
- **Extra files.** `tools/w601_seed.py` and `tools/s602b_test_scoped_cases.py` were touched; both pinned the old
  label or wording.
- **API and shared code.** The wire shapes are unchanged: the same keys, with label values changed. Codes in code
  fields are unchanged. The shared code changes are the `plain_limitation` move (estate re-exports it, so callers are
  unchanged) and `_ACTION_CODES` moving to the work read adapter.
- **Codes not padded in tests.** Test fakes that used short codes (`MR-5`) now use 3-digit codes. `display_code` pads
  any `PREFIX-n` text, so an outcome key such as `MG-7` would be padded if it were ever passed in. Only record-code
  fields are passed.

## Residual risk

- One extra read per row on the work indexes (`finding_titles`, `action_codes`) and one per domain Action detail.
- The titles show only after the PA-3 rebuild, because they are stored per revision.
- The `exempt_hits` and PA-x hits are re-checked in PA-3 captures.

## Review focus

The display-code coverage list (Q8), the RECURRED title path through `coverage.py`, the `plain_limitation` move, and
the board title-words pairing left to PB-2.

## Fix round 1 (review `.agent/review-POLISH-PA-2a.md`, REVISE)

- M1: `estate/coverage.py` `action_title` uses `display_code` ("Action ACT-001"); pin in `test_w301_estate_api.py`
  updated. `test_w303_portfolio_workflow_labels.py` builds its own fake `action_title` (`Action {aid}`), no 6-digit pin.
- M2: `tools/demo_combined_finish.py` CO-3 marker is the new `COST_PREFIX` text "Estimated effect of the trial (not
  money saved): ". The check is unchanged: some Kobo Optimize-cost Earlier detail must contain the marker.
- L1: `board.action_detail` joins after a sentence-ending part with one space; pins in `test_out_e4_readback.py`
  and `test_out_e4_readback_postgres.py` updated.
- L2, L3: packet only (above).
- More 6-digit pins found while running the touched tests: `test_out_e4_readback_postgres.py` (Cost item text and the
  Protect safeguards sentence now read `ACT-001`), `test_link_lineage.py` (safeguards sentence) and
  `test_out_c_rules.py` (fake codes padded `WR-1` → `WR-001`, as in the other OUT tests).
- Merged main `ab248b4c3` (CODE_STATE append conflict: both entries kept, PB-0 then PA-2a).
- Checks after the merge, with PYTHONPATH set to this worktree (`assetops_backend` and `assetops_contracts` import from `AssetOpsV1-polA2`):
  - pure and unit tests: PA-2a, e4 readback, PA-1, w303 workflow labels, OUT-B2 vocabulary, OUT-A1: 54 passed;
  - every backend test file without a DB: 3551 passed. The only failures and errors are Postgres modules run with no URL;
  - host wrapper, Postgres: `test_w301_estate_api`, `test_w303_portfolio_api`, `test_w303_portfolio_workflow_labels`,
    `test_w303_selectors_postgres`, `test_out_e4_readback{,_postgres}`, `test_polish_pa2a_server_copy`,
    `test_link_lineage`, `test_out_c_rules`: 89 passed (1.1 min);
  - `tools\check-all.ps1 -Python …plan2\.venv\Scripts\python.exe`: All 12 guards passed.
