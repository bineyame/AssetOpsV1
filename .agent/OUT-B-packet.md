# OUT-B review packet: Site outcome board from existing reads

Task `tasks/OUT-B-site-outcome-board.md` (Status: in_review). Branch `task/OUT-B-site-outcome-board`, worktree `AssetOpsV1-outB`,
cut from OUT-A head 7b826e97 (no main merge yet). Contract: spec rev 3 `AssetOpsV1-plan2/.agent/build-spec-outcome-sprint-2026-10-29.md`
(pre-flight rulings B and addenda 1-8). Detail history: `.agent/OUT-B-phase-handoff.md` (readings 1-20, B4/B5/B6 notes).

## Outcome delivered
- Backend: `outcomes/status.py` (status roll-up), `site_outcomes/` (`board.py`, `mini.py`, `cold.py`, `ev.py`, `read.py`), `GET /api/sites/{site}/outcome-board`
  (`site-outcome-board-1`) for the mini, cold and EV Overviews, and `GET /api/estate/outcome-summary` (`estate-outcome-summary-1`). Every board value is
  composed from existing reads through bound ports; nothing new is stored.
- Frontend: `sites/OutcomeBoard.tsx` + `outcomeBoardClient.ts` replace the mini, cold and EV objective cards on the three Overviews (four outcome rows,
  closed by default, explainer dialog); Portfolio `OutcomeMatrix` ("Outcomes across the estate"), site dots on the category cards, Grow card short value.
- Addendum 8 wording applied: the Overview strip second sentence is "Each outcome row shows only what these reads support for the selected period." (d3554aca).

## Files materially changed
Backend `outcomes/status.py`, `site_outcomes/*`, `estate/scope.py` (`check_window`, `estate_request`), `estate/portfolio.py` (`site_work_rows`, `action_for`),
`estate/evidence_money.py` (`site_readiness`), `main.py` (route binding, hoists), `mini_depth/inputs.py`. Frontend `sites/OutcomeBoard.tsx`, `sites/outcomeBoardClient.ts`,
`sites/outcomes.css`, `sites/SiteWindowOverview.tsx`, cold/EV frames, `estate/PortfolioOutcomes.tsx`, `estate/EstatePortfolio.tsx`, `estate/estateClient.ts`,
`estate/portfolioWords.ts`, `test/panelStructure.ts`, `test/outcomeBoardFixture.ts`. Evidence `.agent/OUT-mock-measurements.md`, `.agent/OUT-B-captures/`.

## Acceptance criteria
Criterion-by-criterion status is in the task file and the handoff. Summary: board on the mini/cold/EV Overviews met (captures). Measured outcomes without a real
source read UNKNOWN/NOT_MEASURED honestly (met; asserted in `test_out_b4_board_postgres.py`). Portfolio matrix and dots met. Closed-board height caps met (below).
Per-read gates preserved (list below). Old card tests rewritten, none deleted for convenience (below). Combined-dataset checks carried (below).

## Deviations and readings
Ruled deviations: roll_up takes (outcome_key, state) pairs; `ActionFact` gains workflow_label/verification_href/is_domain; SignalFact extras; `headline_money` passthrough;
an absent `settled` key means UNKNOWN; Must-not-harm drops the NOT_MEASURED exclusion (constant `MUST_NOT_HARM_EXCLUDES_UNMEASURED=False`); the estate port is two methods
(one-Site `site_readiness` and `site_work_rows`) rather than one (handoff note 16). Readings 1-20: handoff "Packet notes" sections (Earlier ordering, headline fallback,
local-day depth windows, 31-day work window, settled bases, cold/EV chain and fault rules, EV wording).
Capture-tool deviation: the s5 overview producer refuses `_test` names, so its private DB was `assetops_s501_owner_outb` (dropped afterwards). `ready=False` on the
GreenHarvest overview capture is the generic capture heuristic; the page rendered fully (board, strip, panels).

## Per-read gate list (B4 review, handoff "B4 fix round" L4)
overview = `site_overview/route.py:137-158` (S2 source + performance gate + basis_reason); dispatch = `performance_gate`; Finding index = `basis_aware_gate`
(409 -> PortUnavailable); mini depth = no gate (`mini_depth_api.py:6`); Action detail, verification, Action index, assumption series = no gate flag on GET
(`action_api.py:212-221`); work lists, domain index, global work = `site_read_access` (= board `work_access`); cold/EV reads = access, window, Site type, disclosure
(`cold_site_api.py:60-102`, `ev_assessment_api.py:85-118`). Main binding proven by `test_out_b4_main_binding.py` (removing `work_access=` in `main.py` fails it).

## Changed tests (card assertions became board present + old cards absent; non-card assertions kept)
Cold: Run-7 chip x4 (overview half; Evidence strip assertions kept), five-cards test, null attention destination, w2f, r254 (rewritten). EV: unknown_pending,
all_five_routes, R254. Mini: W1-UX-02 stale day, W1-a Q2/R157/Q48, W1-a Q2 gray/none, W4-02 x5 card-value tests, W4-02 H3 x3. Card-value formatting tests lost their
subject (helpers deleted). estatePortfolio.test.tsx: 4 changed, 2 new. Panel guard admits `section.ob-board` on mini/cold/ev only (proven non-vacuous twice).
The s5SiteWindowOverview strip test is updated for addendum 8.

## Register changes
R521, R529 resolved; R437 closed (card removed); R535, R540-R552 added (R541, R535, R552 open; R552 carried to the combined dataset). R553-R554 free.

## Test results
- Vitest full at 6a706db2 (218.6 s): 3496 passed, 4 failed = the 3 known `w1f4VerificationStructure` plus one load flake, `coldWorkCases` "W5-02 K3b ... Incident What happened"
  (passed alone 36/36 and with its neighbours 166/166; flaked the same way in slice A). After addendum 8: s5SiteWindowOverview 59/59, `tsc` clean.
- check-all (direct, no override) at d3554aca: 11/11.
- Backend full, `tools\run-backend-suite-in-container.ps1 -Tier all`, d3554aca, started 15:12:01, wall 2460 s: 20 failed, 4257 passed, 8 errors; JUnit 4285 testcases, 0 skipped
  (`var/test-results/OPS-03/20261030-151209-b7030a/junit.xml`, git-ignored).

## Known failures (backend): 28 in the full run, none caused by OUT-B
Known: both w303 tests; both w301 estate-index tests (they fail in the full run too). The other 24 reproduce on main (plan2, 32adae2f): the 10 failing files rerun serially, each checkout
on its own `*_test` DB, gave 15 failed + 8 errors on BOTH (1594 s branch, 1608 s main) with identical sorted FAILED/ERROR lists (23 entries; diff empty). Five further full-run
failures passed on rerun: order/load flakes. The shared list covers w303 portfolio_comparison (3 setup errors), portfolio_fixture (1), scope_snapshot (setup errors, the 3 `late_revision` params),
selectors, w301 estate_index (2), provenance_dto, money_snapshot_helpers, s4_power_demo_case, TestRevisionSets/TestRealRows, cc_placement, w403_replay.
Trace: `ValueError: not enough values to unpack (expected 1, got 0)` at `backend/tests/test_s4_consequence_store_postgres.py:111`, `PowerSite.on(day)` unpacking
`[r for r in finding_revisions() if r["episode_start"].date() == day.date()]`, reached from `test_w303_portfolio_fixture_postgres.py:253` (`power.on(POWER_DAY)`, POWER_DAY 2026-10-06, line 49
of the store test). No finding episode exists on that day. OUT-B does not touch this path; likely clock/date dependence (slice A passed these at 08:31 the same day). The main breakage is under
separate investigation.

## Captures (`.agent/OUT-B-captures/`: README.txt, shots/, raw-evidence.json, logs/, capture-outb.mjs, targets-*.json)
v70 mock pair per capture at 1440 and 390, app at d3554aca. Overview closed and with one row open for Kobo (s5 producer, 2026-10-23), GreenHarvest COLD-LAB-001 (w502, 29 Oct 16:00-17:05Z),
Depot EV-LAB-001 (w504, 06 Oct 08:00-09:00Z). Portfolio (s602b estate case) with the matrix and site dots (4 dots, one per category card). Closed board, head to last summary bottom
(1440 / 390 px): Kobo 409 / 740, Depot 409 / 761, GreenHarvest 358 / 715; caps 450 / 800, all within. No page overflow at 390 (scrollWidth 390/390; 1440 shows 1425 = scrollbar);
board scrollWidth equals clientWidth everywhere. No JS console errors (favicon 404s only). Producer DBs dropped, servers and Vite stopped by PID, Chrome closed by the tool.
Kobo estate-case Overview is 409 AWAITING_EVIDENCE_MIGRATION (no board), so the s5 producer is the Kobo evidence.

## Carry-overs to the combined-dataset task (addendum 6)
R552; withdrawn assertions left as comments in `test_out_b4_board_postgres.py` (Kobo measured outcomes; cold B.7 #4 "Not yet verified" absent; EV Assure UNKNOWN because the fixture refuses the
covering day with ESTATE_SELECTION_INCONSISTENT); cold Portfolio cell NONE / readiness NONE; Kobo estate case lacking evidence migration.

## Residual risk and user-review focus
Open copy: none after addendum 8. Residual: 24 non-OUT-B backend failures on main (separate investigation); Kobo closed-board height at 390 is 740 of 800. Review per the task file; a fresh reviewer gates merge.

## Final-review fix round (review `.agent/OUT-B-review.md`; strings from build spec addendum 9)

- **H1:** `.ob-dialog` (`frontend/src/sites/outcomes.css`) is now the mock drawer: `margin:0 0 0 auto`, `height:100vh`, `width:min(550px,95vw)`, padding 28px, square corners, left border only. Still a native `<dialog>`; focus trap, Escape and focus return untouched. Not viewed in a browser.
- **M1:** `ev.py` Charging delivered = "{kwh} kWh with a complete meter record · {completed} of {started} {session|sessions} completed" (short form if `completed` or `started` is null; "Not available yet" only if `kwh` is null); Grow subline = "{kwh} kWh with a complete meter record" or null. Test `completed=0, complete_kwh=15` gives "15 kWh with a complete meter record · 0 of 1 session completed". R553 added to `.agent/mock-departure-register.md`. The null-denominator test now expects the short form for Grow (energy still stands).
- **M2:** `MINIGRID_OBJECTIVE` ends at "...protecting the battery reserve."; s5 test pins the constant, so it follows.
- **L1:** `cold.py` counts MISSING (m) and CONTRADICTORY (c) separately; texts per addendum 9; headline "fully" only when m=0 and c=0. Tests added.
- **L2/L3:** `ev.py` Assure subline never prints an unknown count; Connector status guards null span bounds ("Connector status missing for part of this window" plus the zone suffix). Tests added.
- **L4:** orphaned "Q10" comment removed from `portfolioWords.ts`.
- **M3 correction (28 full-run failures; JUnit `var/test-results/OPS-03/20261030-151209-b7030a/junit.xml`).** Lists saved: `.agent/OUT-B-evidence/rr-branch.txt` (branch serial rerun, 1594 s) and `rr-main.txt` (main 32adae2f, 1608 s). Their 15 FAILED + 8 ERROR lines are identical (the files differ only in venv path and timing lines).
  - **23 reproduced identically on main:** w303_portfolio_scope_snapshot (3 `late_revision` params failed; `three_domains_same_window...`, `foreign_tenant_missing_site...`, `page_size_does_not_change...`, `ev_footer_first_eligible...` errors); w303_selectors `portfolio_row_facts_and_verification_ids_match_stored_rows`; w301_estate_index `cost_risk_opportunity_eligibility_without_mock_seed`, `cost_lens_only_exact_eligible_current_rows`; w301_provenance_dto `w1_revision_selection_sets_and_estate_projection`, `w1_cold_ev_exact_cited_id_mapping[w1]`; w301_w1_money_snapshot_helpers `money_source_gate_exact_citations`, `money_source_gate_mixed_union_withholds`; s4_power_demo_case (3: `s405b_fresh_p01_publication...`, `source_state_compatibility_all_w1_consumers`, `s405b_an_ordinary_contextual_id...`); cc_placement `cold_ev_placement_risks_lens_and_paging`; w403_replay `positive_missing_late_replay_and_fresh_reload`; w303_portfolio_comparison (3 errors: `operating_cost_first_match_wins_across_partitions`, `ineligible_overlap_and_unknown_coverage_decline_total`, `ev_window_money_has_no_finding_attribution`); w303_portfolio_fixture `one_day_three_domain_fixture_public_roots` (error).
  - **5 passed on rerun (branch only; not rerun on main; `TestRevisionSets` in `test_s405_resolver_postgres.py`, `TestRealRows` in `test_s4_consequence_history_postgres.py`):** `TestRevisionSets::test_unbound_finding_and_consequence_are_unknown_from_their_exact_sets`, `TestRevisionSets::test_authored_finding_keeps_its_state_after_a_new_head_and_its_consequence_is_authored`, `TestRevisionSets::test_unknown_finding_makes_its_consequence_unknown_even_with_bound_power_inputs`, `TestRevisionSets::test_consequence_only_power_input_is_mixed_beside_its_finding`, `TestRealRows::test_cutoff_boundaries_and_the_real_clock_skew`. The earlier text listing `TestRevisionSets/TestRealRows` among the shared main-reproducing set was wrong; they are in the 5, not the 23.
  - Count: 23 + 5 = 28. Not rerun now; the full set is rerun on this branch after the main clock-fixture fix lands.
- **Checks this round:** focused backend b1-b4 non-Postgres (run with PYTHONPATH on the plan2 venv, as the host script is blocked by the execution policy): see results line below; vitest, tsc and check-all: see below.
- **Results:** backend b1-b4 non-Postgres 138 passed; `tsc --noEmit` clean; focused vitest (src/sites, src/estate, s5SiteWindowOverview) 1953 passed, 3 failed = the known `w1f4VerificationStructure` trio (a load flake in `siteFindingEvidence` passed alone, 46/46); `tools\check-all.ps1` direct, no override: All 11 guards passed. No Postgres, browser or full suite run.
