# POLISH PA-3 review packet: producers, links and rebuild

Task: `tasks/POLISH-PA-3-producers-rebuild.md`. Branch `task/POLISH-PA-3-producers-rebuild` from main `c4a39b1dc`.
Contract: `.agent/build-sheet-POLISH.md` §1.3, §3 (Lab names, narratives), §3.1 PA-3 rows, §4, §5 PA-3, §6, §7,
Addenda 3, 5 and 9. USER_REVIEW_REQUIRED: no (merge on review ACCEPT).

## Outcome delivered

| Item | Change |
|---|---|
| P-01/P-02 (§4, Addendum 9 Q3) | `tools/demo_combined.py` `story_links(story, days, kobo, web)` (pure) + `LINK_FORMS`; `links()`/`serve` print it. Cold/EV boards on the `days.json` event window; a day with null `start`/`end` links the whole calendar day, label "…, no event: whole day". No `/outcomes` or `/overview`. |
| Guards (Addendum 9 Q1) | `DB_RE` `^assetops_(demo3\|polish)_[a-z0-9]{1,20}_test$`; work `var/demo3*` or `var/polish*` (`WORK_PREFIXES`). Marker and drop guard unchanged. |
| P-08 slip (§1.3) | `demo_combined_ev.declare_and_work` records `action.action_code`, `intent.intent_id` and the Action's posted `raised_at` (the create response carries no `raised_at`; the posted body is the stored value). R645. |
| Narratives (§3, Addendum 9 Q2) | Kobo and EV requests pass `narrative=f"{title}."`. w502 BUILD `narrated(title)` adds it to the fixture WR and the earlier visits only when `demo_combined_cold` sets `ns["DEMO_NARRATIVES"]`; standalone w502 and the worst-case path are unchanged. |
| Lab names (§3, D-5) | `install_cold_lab`/`install_ev_lab` `display_name=None` overrides the record's name (`dataclasses.replace`; source bytes and sha256 unchanged, so later installs stay idempotent). `demo_combined_cold.DISPLAY_NAME` "GreenHarvest Cold Room" (first install); `demo_combined_ev._install` passes "Depot Charging Hub" to every EV day's chain. R646; R111 closed for the demo build. |
| CO-1 (DEMO-A L1/L2, Addenda 9 Q4 and 10) | Pure `cost_row_action_links(cost, action_id, action_code, verification_state)`: (1) the Action linked by href path `/sites/KOBO-001/actions/{id}`, in `earlier` when the verification state is final (VERIFIED/INEFFECTIVE/INCONCLUSIVE), else in `issues` + `in_hand`; text alone never passes; (2) the Must-not-harm href carries the Action id and verification event, and its text `display_code(action_code)`; (3) the L1 safeguards sentence. The state comes from the Action read's `verification.state` (`kobo.json` holds only the outcome id; the Kobo producer asserts VERIFIED). Coordinator correction to Addendum 10: CO-3's `earlier` line already carried the Action href before LINK-LINEAGE, so (1) alone may pass on the old board; (2), the Must-not-harm href, is the guard, pinned in `test_demo_combined_finish_co1.py`. |
| DEMO-A L3 | R535/R552 descriptions marked historical; `.ai/CODE_STATE.md` DEMO-A heading/main/addenda text current (`4f57261d3`, Addenda 1-4). |

## Files materially changed

- `tools/demo_combined.py`, `tools/demo_combined_ev.py`, `tools/demo_combined_kobo.py`, `tools/demo_combined_cold.py`,
  `tools/demo_combined_finish.py`, `tools/w502_cold_work_walkthrough.py` (passthrough only).
- `backend/assetops_backend/sites/cold_lab.py`, `backend/assetops_backend/sites/ev_lab.py`.
- Tests: new `backend/tests/test_demo_combined_links.py` (5 pure), new `test_demo_combined_finish_co1.py` (5 pure); 2 new tests each in
  `test_w202_cold_lab_bindings_postgres.py` and `test_w205a_ev_foundation_postgres.py`.
- Addendum 11/12: `backend/assetops_backend/ev_site_reads.py`, `site_outcomes/board.py`, `work/global_index.py`,
  `work/global_detail.py`, `work/adapters/postgres_global_read.py`; tests `test_polish_pa3_ev_tariff_copy.py` (new),
  `test_out_b1_board.py` (new Q1 test; `legacy()` strip in exact-item asserts, also in `test_out_b2_mini.py`,
  `test_out_b3_cold_ev.py`), `test_w601b_global_maintenance.py` (Q2), `test_w601c_request_detail.py` (Q3).
- Records: `.agent/mock-departure-register.md` (R645, R646, R111 note, R535/R552 L3, R655 TARIFF_GAP), `.ai/CODE_STATE.md`,
  `.ai/ACTIVE_CONTEXT.md`, task file.

## Acceptance criteria

1. `story_links` and test: **met** (pure test; serve printed the links, Runbook below).
2. Guards: **met** (pure test: polish accepted; `assetops_other_x_test` and `var/other_x` refused).
3. P-08 slip: **met** in the H1 build (`ev.json` fault day carries `action.code`, `action.raised_at`, `intent_id`).
4. Narratives: built; `wr-overview` shows the cold fixture WR.
5. Lab names: **met** (Postgres tests; `cold-board-failure` h1 "GreenHarvest Cold Room").
6. CO-1: **met** per Addendum 10 (pure test 5/5; finish check 17/17 on the H1 build).
7. Rebuild: **met**. Final build at `84ab3ca3d` (main `0ad27df7f` merged): self-check 17/17; slow build test 19/19,
   0 skipped (Final run below). `assetops_demo3_full_test` was never written.
8. Captures and screen check: **met**. Final strict capture: 15 hits per width, all PB-3 frontend; Kobo 0;
   server text awaiting lane A 0. Screen check: no PA-1/PA-2 misses.
9. Addendum 12 wire fields: **met** (one read-level test each; shapes in Final run).

## Heavy jobs (interim, on the pre-PB-2 build)

- **H1** `tools/demo_combined.py --db assetops_polish_full_test --work var/polish_full prepare` at `5e0c00970`:
  12:33:44-12:57:14 (about 1410 s; cap 3120 s). Kobo 1003.8 s (machine loaded, PB-2 in parallel), cold 58.2 s,
  EV 64.2 s. Self-check 16/17; CO-1 failed (Action only under `earlier`) and went to the Architect (Addendum 10).
- **Finish check re-run** (no rebuild): this worktree's `tools/demo_combined_finish.py` at `0021ec918`, run in the
  private tree's environment: **17 pass, 0 fail, 0 skipped** (13:11:11-13:12:08). The private tree's own copy is
  still `5e0c00970`; the post-PB-2 rebuild refreshes it.
- **H2** started 13:12 and was stopped by PID at the coordinator's hold (PB-2 merges first). Its database
  `assetops_demo3_t3344962b_test` and work folder were removed with the tool's `drop`. No result.
- **H3 (interim)**: serve (API 8990) and Vite (5490) from this worktree on the polish DB, CDP 9493,
  `DEMOB_STRICT=1 … capture var/polish_full .agent/POLISH-PA-3-captures`, 13:00:46-13:07:38: 28 captures, all
  settled, no overflow; strict gate 562 counted hits (281 per width). Stack stopped by PID; 8990, 5490, 9493 free.

### Capture counts per owner (per width; both widths identical)

| Capture | Hits | Owner |
|---|---|---|
| portfolio-week | 5 uuid ("Finding COLD-LAB-001 · <uuid>", `EstatePortfolio.tsx:142`); 2 "Scenario" (Addendum 8 Q4 What-if) | PB-3 (frontend) |
| kobo-board-S, kobo-board-S1 | 1 each, "critical load" (ROLE_WORDS, Addendum 8 Q2) | PB-2 (frontend) |
| kobo-board-S-open | 251 uuid, 3 raw timestamp, 2 enum code (Technical details, Addendum 8 Q5) | PB-2 (frontend) |
| kobo-verification | 1, `ACT-000001` (frontend `displayCode`) | PB-2 |
| cold-board-normal | 1, "Running" (`ColdAssessmentViews.tsx:734`) | PB-3 |
| ev-board-fault | 3 `REC <uuid>` (Addendum 5); 1 "Scenario details" (`EvSiteViews.tsx:760`) | PB-3 (frontend) |
| ev-board-fault | 1, "Needed before a gross tariff scenario can be estimated." | **server, `ev_site_reads.py:74` TARIFF_GAP; not in §3.1, no owner (reported, not fixed)** |
| maintenance-preventive | 5 `PM-0000nn` (frontend `displayCode`); "running hours"; "draft" x2 | PB-2 (codes); PB-3 (copy) |
| wr-overview | 1, `WR-000006` (frontend `displayCode`) | PB-2 |
| cold-board-failure, findings-all/cost/risks/opportunities | 0 | - |

Server text awaiting lane A (PA-1/PA-2 rows): **0**. A scan of the 11 reads behind the screens finds stored-form codes
only in `code`/`action_code`/`case_code` fields, so the remaining code hits are frontend renders. Awaiting PB-2
(coordinator): the Kobo Finding title "Generator support merits review" (`mini.FINDING_TITLE`).

### PA-1/PA-2 screen check

Method: the read behind each capture (fetched from the same serve) holds the exact server string; the cold rows are
also confirmed visually in `cold-board-failure-1440.png`.

| Slice / item | Shows in |
|---|---|
| PA-1 §1.1 "No fuel cost estimated: …" Cost headline | `kobo-board-S-*.png`, `kobo-board-S1-*.png` |
| PA-1 §1.6 "…needs odometer readings and a published charging tariff" | `ev-board-fault-*.png` |
| PA-1 §1.7 MG-7 "No objective declared" and "Generator not used on this day, so nothing to check · readings complete" | `kobo-board-S1-*.png` |
| PA-1 §1.3 "Investigate Connector …" | `ev-board-fault-*.png` |
| PA-1 D-2 COST_NOT_CREDITED | not on a capture screen (trial VERIFIED); PA-1 tests |
| PA-2a trial cost "Estimated effect of the trial (not money saved): …", "Goal before the trial: …" | `kobo-board-S-*.png` (Earlier), `kobo-board-S1-*.png` |
| PA-2a display codes in server sentences (ACT-001, WR-006/007/008, INC-005, PM-009/010) | `kobo-board-S*`, `cold-board-failure-*.png`, `cold-board-normal-*.png`, `ev-board-fault-*.png` |
| PA-2a Addendum 4 title "Generator may have been on longer than needed" | `portfolio-week-*.png`, `findings-all-*.png` |
| PA-2a no `Finding/Action <8 hex>` server labels | all board and list captures (0 in the reads) |
| PA-2a "No end time yet", "No action agreed yet", "Can't be compared across these sites yet" | `portfolio-week-*.png` |
| PA-2a "Backup generator did not start on its own"; "No record of switching to backup power." | `cold-board-failure-1440.png` (Needs attention, Next step) |
| PA-2a "Current view", RECURRED, UNCONFIRMED title | not on a capture screen, or not in this dataset's windows |
| PA-2b "Backup generator" asset word | `cold-board-failure-*.png`, `maintenance-preventive-*.png`, `wr-overview-*.png` |
| PA-2b preventive `summary` and `due_state`; cold board "Overdue"/"Due soon" chips | `maintenance-preventive` read; `cold-board-failure-1440.png` |
| PA-2b repeat warning with the plain asset word | `cold-board-failure` read |

Misses: none among the PA-1/PA-2 rows. One unowned server string (EV TARIFF_GAP "scenario", above).

## Runbook (final build `84ab3ca3d`, S = 2026-10-30; dates move on every rebuild, quote them from `links`)

`python tools/demo_combined.py --db assetops_polish_full_test --work var/polish_full serve`; from `frontend/`:
`$env:ASSETOPS_API_PORT="8990"; npm.cmd run dev -- --port 5490 --strictPort`. The first `performance:` line follows
the first tick (about 2-3 min on this machine). Links: portfolio/findings week
`?from=2026-10-24T00:00:00Z&to=2026-10-31T00:00:00Z`; preventive/maintenance month `?from=2026-10-02T00:00:00Z&to=2026-11-02T00:00:00Z`;
Kobo `/sites/KOBO-001?date=<day>` for each of 9 story days; GreenHarvest `/sites/COLD-LAB-001?from=<day>T16:00:00Z&to=<day>T17:05:00Z`
(S-7d, S-3d, S); Depot `/sites/EV-LAB-001/ev?from=<day>T08:00:00Z&to=<day>T09:00:00Z` (S-10d, S-3d); verification and Finding.
Depot: the follow-up Action is on Work › Actions; the fault-window board shows the warning and the plan (R645).

## Checks run

- `tools\run-host-tests.ps1 -- test_w202_cold_lab_bindings_postgres.py test_w205a_ev_foundation_postgres.py test_demo_combined_links.py`: 32 passed.
- Pure: `test_demo_combined_links.py`, `test_demo_combined_finish_co1.py`, `test_polish_pa3_ev_tariff_copy.py`; with the lab
  Postgres tests after the main merge: 38 passed. `test_w207_ev_site_reads_postgres.py` + tariff pin: 20 passed.
- Addendum 12 set (`-n 4 --dist loadfile`): w601b, w601c, out_b1/b2/b3/c2, out_c3 repeat-visits, out_e4 readback, w601a,
  out_w1, w301 estate api, cov_partial: 179 passed.
- `tools\check-all.ps1` on `84ab3ca3d`: 12/12 guards passed (13:53-14:11).

## Final run (post-PB-2, `84ab3ca3d`)

- **H1** prepare into `assetops_polish_full_test` / `var/polish_full`: 14:11:47-14:34:07, 1339.4 s (cap 3120 s);
  Kobo 955.0 s, cold 68.4 s, EV 78.3 s; self-check **17 pass, 0 fail, 0 skipped**.
- **H2** `toolsun-host-tests.ps1 -- backend/tests/test_demo_combined_postgres.py -m slow -q --junitxml=…` (60-min cap):
  14:34:28-15:05:50, **19 passed** in 1878.8 s; JUnit tests 19, failures 0, errors 0, skipped 0. Its own DB was
  dropped by the fixture (`var/` holds only `polish_full` and `sites`).
- **H3** serve + Vite from this worktree, CDP 9493, `DEMOB_STRICT=1`, 15:07:14-15:14:31: 28 captures, all settled,
  no overflow; **30 counted hits (15 per width), all PB-3 frontend**:
  portfolio-week 5 "Finding <site> · <uuid>" (`EstatePortfolio.tsx:142`) + 2 "Scenario"; cold-board-normal "Running";
  ev-board-fault 3 `REC <uuid>` + "Scenario details"; maintenance-preventive "running hours", "draft" x2.
  Kobo boards, verification and wr-overview 0 (PB-2 merged); EV TARIFF_GAP "scenario" gone (Addendum 11).
  Exempt hits: `kobo-board-S-open` 283 per width (was 24): PB-2's Technical details regions, recorded not counted.
  Stack stopped by PID; ports 8990, 5490, 9493 free.

### Addendum 12 wire shapes (for PB-3)

- Outcome board row items (`GET /api/sites/{code}/outcome-board`), case items in `in_hand` and `earlier` add
  `"kind": "INCIDENT" | "MAINTENANCE_REQUEST"` (as stored; not "WORK_REQUEST") and `"occurred_at": "2026-10-30T16:11:00Z" | null`.
  Plan items in `in_hand` add `"kind": "PLAN"` (no `occurred_at`). Action items are unchanged (no `kind`).
- `GET /api/work/preventive` rows add `"site_time_zone": "<IANA zone>" | null` (the Site's stored `timezone`).
- `GET /api/work/requests/{id}` `work_asset`: `{"code": "...", "type": "GENERATOR", "asset_label": "Backup generator"} | null`
  (PA-2b rule: code appended only when the Site has more than one non-retired asset of the type).

## Known deviations

- CO-1 reads the verification state from the Action read (`verification.state`); `kobo.json` stores only the outcome id.
- Board item `kind` is the stored `MAINTENANCE_REQUEST`, not the Addendum 12 wording "WORK_REQUEST" ("as stored").
- Existing exact-dict board item assertions now compare through `legacy()` (drops the two new keys); the new keys are
  pinned in `test_case_items_carry_their_stored_kind_and_occurred_at`.
- The aborted first H2 run (pre-hold) and the interim captures are superseded by the final run.

## Residual risk / review focus

- `var/polish_full/tree` is `84ab3ca3d`; PC serves it. Re-check after any later backend merge needs a rebuild.
- The screen check above was made on the interim build; the final build adds only PB-2 and Addenda 11-12.

