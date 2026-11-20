> Moved verbatim from the former `.ai/CODE_STATE.md` on 2026-11-18 (declutter step 2), part 9 of 11; sections keep their original relative order; the original order of all sections is the numbering in `index-*.md`. Index: `INDEX.md` in this folder.

## CC-R1 - links, claim labels, beneficiary key, no-double-count check (built, in_review)

Lane C, branch `task/CC-R1-claim-links-beneficiary`. Spec: `specs/Lane-C/` sections 0.4 and CC-R1. Packet: `archive/agent-history/CC-R1-review-packet.md`.
- `estate/financials.py`: `BENEFICIARY_OF_CATEGORY` (owner Q9; five categories, including `PRODUCTIVE_USE_CONTRIBUTION_SCENARIO` for D1 and `RECORDED_REPAIR` -> `COOLING_PROVIDER`). `_line` emits a public `beneficiary` after `category`. `_beneficiary(line)` falls back to the category default, so hand-built test lines work. `_partition` has seven elements, and `compare()` unpacks seven.
- `estate/evidence_money.group_key_for_partition(..., *, beneficiary=None)` adds `beneficiary` to the hashed payload only when it differs from the category default. Default keys are byte-identical: a pinned value is asserted in `test_w303_portfolio_reduction.py`. The map is imported lazily because `financials` imports `evidence_money`.
- New `estate/money_invariants.double_count_violations(portfolio, financials=None)`. It is pure, takes parsed bodies, and uses `portfolio.selected_lines` as the member set. It emits violation texts prefixed `TOTAL_NOT_NULL`, `MEMBER_NOT_FOUND`, `MEMBERS_DISAGREE` or `MEMBERS_INTERSECT`. Tests and the scope-snapshot `Portfolio.ok()` helper call it. It is not called at runtime.
- Frontend:
  - `CommercialClaimLevel`, `Beneficiary`, `CLAIM_LABEL` and `BENEFICIARY_WORDS` live in `sites/actionPresentation.tsx`.
  - New `sites/ClaimLabel.tsx`, which renders "Evidence level and beneficiary not stated" for an unknown level or beneficiary (CC-R1-Q2).
  - The gross scenario label is in `MiniScenarios.tsx`.
  - The estate "Benefits:" line is in the Category cell of `EstateFinancials.tsx`. `FinancialRow.beneficiary` is optional.
  - `BridgeLinks` and `FinancialsLinks` gain an optional `recommendation`. Only the mini Financials frame wires it, producing "Open the recommendation →" with the view's `revision_id`.
- Register rows R500 (scenarios, verification) and R501 (financials).
- The verdict label (`VERIFIED_SIMULATED_TECHNICAL`, "Technical result verified on test data", CC-R1-Q1) shows under the Verification strip for a VERIFIED or INEFFECTIVE displayed outcome only. The vocabulary guard is unchanged.

## CC-R2 - Portfolio placement (D5) and the estate producer case (built, in_review)

Lane C, branch `task/CC-R2-placement`. Spec: `specs/Lane-C/rulings.md` "CC-R2". Packet: `archive/agent-history/CC-R2-review-packet.md`. Open: `archive/agent-history/CC-R2-questions.md`.
- New pure `estate/placement.py`:
  - `POLICY_VERSION` `estate-placement/1`, `GROUPS`, `GROUP_LABEL`, `REASON_TEXT` (20 codes; `VERIFIED_WATCH_RETURN` follows CC-R1-Q1) and `place(row, action, site_cov, line_group) -> Placement` with `.wire()`.
  - Rules run in order: 1, 2, Monitor, Compare, Unpriced, 6.
  - Confidence uses row facts; site coverage adds text only.
  - `workflow_label` is imported lazily from `portfolio` (cycle).
- Row facts:
  - `_index_snapshot` heads gain `f.mechanism`.
  - `postgres_estate_read._with_mechanism` runs one batched `finding.mechanism` SELECT per cold or EV window.
  - `coverage.py` mini rows carry `mechanism`, `recurs_after_finding_id`, `revision_no` and `transition` (all `.get`).
  - `index.select_finding_scope` adds the private `_recurs_after`, `_transition` and `_revision_no`, and a RISK flag for `index.RISK_MECHANISMS` (the Findings root `lens=risks` changes too).
- `portfolio.py`:
  - Rows carry `placement`, `confidence` and `confidence_reasons`; `priority` stays null.
  - `line_groups(lines, groups)` maps a Finding revision to its money group state, from the same `compare()`.
  - The marker is `(group_rank, at, site_code_key, site_id, finding_id, finding_revision_id)`, and `order_key` leads with `group_rank`.
  - `PORTFOLIO_ORDER` is given verbatim.
  - `summary.placement_counts` has five keys over `members`; it is null unless F is COMPLETE/EMPTY.
- `scope.py`:
  - `_MARKER_KINDS["portfolio"] = 6`.
  - The rank is an int from 1 to 5 and never a bool.
  - `cursor_after` and `cursor_marker` have a portfolio branch.
  - A five-part cursor fails with 422 INVALID_CURSOR.
- Producer: `tools/s602b_test_scoped_cases.py` case `estate` (`estate_findings`, `estate_assertions`, `pinned_app`, `_cursor_key`). The walkthrough `CASES` gains `estate`. **The `estate` case has not been run yet** (it needs an `assetops_s602b_audit_cc*` DB).
- Frontend:
  - `EstatePortfolio.tsx` has the Placement column, `placementRows` group headings (`tr.placement-group`, count from `placement_counts`), the confidence words and the `<details>` "How placement works".
  - The words are in `portfolioWords.ts`.
  - The types are `EstatePlacement` and `EstatePlacementGroup`.
  - Register R502.
- Rewritten by design:
  - five-part fixtures in `test_w303_estate_cursor.py`;
  - `test_w303_portfolio_api.py` (order, counts, marker length);
  - `test_w301_estate_index_postgres.py:199,204` (cold RISK). Lines 548-563 are mini-grid rows and needed no change.
- Ruled and applied (`4e986966`; CC-R2-Q1..Q4):
  - Q1, the confidence texts "claim" and "simulation";
  - Q2, there is no EV row in the W3-03 fixture;
  - Q3, the stale panel-bottom copy;
  - Q4, there is no Portfolio claim in the s602b capture script.

## OUT-A - outcome category labels and links (built, in_review)

Outcome sprint slice A, branch `task/OUT-A-category-labels` (main `cbc32703` merged in). Spec: `AssetOpsV1-plan2/.agent/build-spec-outcome-sprint-2026-10-29.md` Slice A + rulings A, addenda 1-2. Packet `archive/agent-history/OUT-A-packet.md`.
- Backend:
  - New pure `outcomes/catalogue.py`, which holds four categories and the site-level outcomes.
  - New pure `outcomes/outcome_map.py` (`outcome-map/1`: `categories_for(signal, domain)`, `finding_signal_key`, `outcome_roles`). NOT_MAPPED is used when the mechanism or the domain is unknown.
  - `categories` are on estate index rows (`estate/index.py`), Portfolio rows plus `summary.category_counts` (`estate/portfolio.py`), the mini Finding index and read (`analytics/finding_index.py`, `finding_read.py`), cold and EV Finding reads (`adapters/postgres_assessment_store.py`) and the mini Action read (`actions/service.py`).
- Fixtures: w301 golden and both S6 contracts were regenerated through write flags. Proof: `archive/agent-history/OUT-A-golden-equality.py`, which strips only `categories` and `selection_seq`.
- Frontend:
  - `sites/outcomeCategories.tsx` holds `CategoryTags` (solid = moves, outlined = touches), `AffectsLine` (prop `subject`, not `variant`; a guard bans `variant`) and `OutcomeIcon`/`OutcomeGlyph`. Styles are in `sites/outcomes.css`.
  - Pills are on the estate, Site, cold and EV Findings lists.
  - One Affects line appears on the mini Finding overview, evidence and history tabs, the cold and EV Finding overviews, and the ACT-048 pages.
- Portfolio: `estate/PortfolioOutcomes.tsx` renders four category cards in place of the five value cards. The cards not shown stay on the wire.
  - Grow "Not available yet" renders through gap `G-portfolio-grow-revenue` (registry `portfolio:3.grow-card-value`).
  - A missing OPERATING_COST gives `OPTIMIZE_COST_MISSING` ("Not assessed").
- `tools/measure-mock-panels.mjs --mock <dir>`; register R520-R528.
- Open:
  - Grow value until OUT-B6 (R524).
  - Two w303 backend tests fail on main, because they assert `_mechanism is None` after CC-R2. A separate round fixes them.
  - 3 w1f4 vitest failures are on main.
  - EV and cold vitest tests are load-flaky in the full suite.
  - No three-domain demo estate exists (R535).

## OUT-B - Site outcome board and Portfolio outcome matrix (built, in_review)
Branch `task/OUT-B-site-outcome-board` (head d3554aca before closeout commit; cut from OUT-A 7b826e97). Packet `archive/agent-history/OUT-B-packet.md`; history `archive/agent-history/OUT-B-phase-handoff.md`.
- Backend: `outcomes/status.py` (roll-up of outcome states); `site_outcomes/` (`board.py` facts -> four-outcome board, `mini.py`/`cold.py`/`ev.py` composers over bound `*Ports`,
  `read.py` binds the real reads incl. covering-day widening for cold/EV). Routes `GET /api/sites/{site}/outcome-board` (`site-outcome-board-1`) and `GET /api/estate/outcome-summary`
  (`estate-outcome-summary-1`). The board reads existing sources only; nothing stored. Read gates per source are listed in the packet and bound in `main.py` (`work_access=site_read_access`).
- Estate: `estate/scope.py` `check_window` (the one window rule) and `estate_request`; `site_readiness` and `site_work_rows` build requests through it (INVALID_WINDOW on misaligned or over-31-day).
- Frontend: `sites/OutcomeBoard.tsx` + `outcomeBoardClient.ts` replace the mini/cold/EV objective cards (closed rows by default, explainer dialog); `estate/PortfolioOutcomes.tsx`
  `OutcomeMatrix`, `SiteDots`, Grow short value; `getOutcomeSummary` optional on `EstateClient`. Panel guard admits `section.ob-board` on mini/cold/ev only.
- Settled: measured outcomes with no real source read UNKNOWN/NOT_MEASURED; Must-not-harm drops the NOT_MEASURED exclusion; closed-board height within 450 (1440) / 800 (390); register R521/R529 resolved,
  R437 closed, R535 and R540-R552 added.
- Left open: R541, R535, R552 (R552 to the combined dataset); combined-dataset assertions withdrawn as comments in `test_out_b4_board_postgres.py`; cold B.7 #4; EV Assure UNKNOWN on the fixture's
  ESTATE_SELECTION_INCONSISTENT; Kobo estate case lacks evidence migration (captures used the s5 producer).
- Results: vitest 3496 pass, 4 fail (3 known w1f4 + 1 load flake); backend full 20 failed/8 errors/0 skips, all but the 2 known w303 reproduce on main 32adae2f (identical 23-entry lists, `PowerSite.on` at
  `test_s4_consequence_store_postgres.py:111`; under separate investigation); check-all 11/11.

## OUT-C - early warnings, first set (built, in_review)
Branch `task/OUT-C-early-warnings` (cut from main e8cf8a36). Contract `AssetOpsV1-plan2/specs/OUT-C/spec.md`; packet `archive/agent-history/OUT-C-packet.md`; history `archive/agent-history/OUT-C-phase-handoff.md`.
- Backend: `outcomes/warnings.py` pure producer (`early-warnings/1`; seven rules; no money; `subject`/`visit_ids` never on the wire); catalogue/2 measures MG-4, CC-3.
  `site_outcomes/visits.py` reads maintenance over three recorded-time windows `[to-62,to-31) [to-31,to) [to,to+31)`, filtered by occurrence (60 days);
  board/summary carry `warnings[]`, summary `categories[].warning_count`; cold/mini/ev composers feed reserve counts, faults, connectors, peak, plans.
- Data: w502 `positive` authors repeat visits and plans (`doc["out_c"]`) so GreenHarvest Cost reads Needs attention on the w501 window.
- Frontend: `sites/EarlyWarnings.tsx` (`EarlyWarningList`, `SiteEarlyWarnings`, `miniBoardDay`); `OutcomeBoard.tsx` exports `ISSUE_KIND` and `ExplainerDialog`;
  `estate/useOutcomeSummary.ts`. Lists on estate Findings lenses, the three Site Findings lists, Portfolio (max 4); pulse warning count; Protect detail clause.
  Maintenance card 4 is `repeat_visits` (estate summary over covering UTC days); request page amber repeat-visit notice from the Site board.
- Settled: warnings render only backend text; empty list renders nothing; the frontend adds no "Not available yet" literal.
- Left open: P-C1 failed (the whole-day estate summary on w502 shows no REPEATED warning), so estate surfaces are vitest-only and carried to the combined
  dataset; R561, R562, R565, R566, R569 open; full vitest, full backend and captures await the coordinator's go.

## OUT-W - estate event windows for cold and EV Sites (built, in_review)
Branch `task/OUT-W-estate-event-windows` (cut from main 833e7c95). Contract `AssetOpsV1-plan2/specs/OUT-W/spec.md`; packet `archive/agent-history/OUT-W-packet.md`; history `archive/agent-history/OUT-W-phase-handoff.md`.
- Backend: `EstateEvidenceService.site_selected_windows` (`estate/evidence_money.py`, after `site_readiness`): the Evidence root's selected windows of one
  cold/EV Site on one snapshot (same `snap.selected_windows` arguments as `coverage._windowed`), deduplicated, ascending, forward and <= 31 days; [] for
  mini/unsupported/no cutoff, None outside the authorized set; window rule and `known_at` refusals as `site_readiness`. No new SQL, no new port.
- `site_outcomes/read.py`: `latest_window` (max end, then start), `_event_window` (any failure -> None; logs Site code and exception type only, silent for
  `PortUnavailable`), `summary()` composes cold/EV on the latest event (`LATEST_EVENT`) or the period (`PERIOD`), mini on its day (`DAY`); sites gain
  `window` and `window_basis` (None on a failed board); `overview_href` carries `?from=&to=[&known_at=]` only on `LATEST_EVENT`. Schema version unchanged.
- Frontend: `EstateOutcomeSummarySite` gains `window`/`window_basis` (never shown); fixtures and Portfolio vitest prove the cold cells use the query href.
  No component change: Portfolio cells and headers already use `overview_href`, and the Site page passes the URL window to its board (captured).
- Settled: P-C1 is asserted on real Postgres (w502 day and week: GreenHarvest LATEST_EVENT on the W5-01 window, Cost Needs attention, one repeat warning).
- Left open: R577 (Depot 6 Oct estate reads refuse 409 ESTATE_SELECTION_INCONSISTENT, a Finding with two selected revisions at one cutoff; FIX-01); the
  6 Oct EV assertion flips to LATEST_EVENT when FIX-01 lands. R576 standing (earlier events in a longer period do not affect cold/EV cells).
  Maintenance card 4 reads "Not assessed" while the summary is loading (pre-existing OUT-C behaviour, observed in capture).

## OUT-D - declared objectives and status (built, in_review)
Branch `task/OUT-D-declared-objectives` (from main 833e7c95, OUT-W merged in). Contract `AssetOpsV1-plan2/specs/OUT-D/spec.md`; packet
`archive/agent-history/OUT-D-packet.md`; history `archive/agent-history/OUT-D-phase-handoff.md`; U4 review `AssetOpsV1-plan2/.agent/OUT-D4-review.md` (REVISE, fixed f6be0782).
- Schema: migration `0038_out_objectives` (head; append-only objective revisions, named CHECKs, site FK, UPDATE/DELETE trigger). 20 head-literal
  test files name it; downgrade targets untouched. Writer guard `configuration-persistence.ps1` registers the store (anti-vacuity counter) and an
  `objectives` configuration domain.
- `outcomes/objectives.py` (pure: POLICY `outcome-objectives/1`, MEASURES, `judge` MET/MISSED/NOT_JUDGED, `ObjectiveFact` with `source_note` last);
  `outcomes/status.py` -> `outcome-status/2` (rules 4c/7/7b/7c; a failed objectives read is UNKNOWN / OBJECTIVES_NOT_READ, never NO_OBJECTIVE).
- `objectives/` package: `model.py` (validate -> 422 OBJECTIVE_INVALID), `adapters/postgres_objective_store.py` (`declare`, `current`),
  `composition.py`; `declare_objective.py` CLI (`fixture --file`, `declare`); demo file `backend/conversions/demo-objectives.json` (6 objectives).
- Board: `site_outcomes/objective_facts.py` (rows -> facts; CC-1 from the cold chamber range, never stored, R584); composers build `Reading`s;
  "Declared objective" contributor after domain contributors; wire `objectives[]` (verdict, source_note) and `objectives_read`. Mini Assure
  "Actual against plan": "{met} of {n} declared objectives met · {u} not checked yet"; failed read -> `mini.PLAN_NOT_READ`.
- Summary: `objective_site_count` counts Sites whose board and objectives were read (None when none was); `objective_sites_unread` the rest.
  Portfolio `assureDetailText` (PortfolioOutcomes.tsx): "targets declared at {n} sites[, {u} sites not checked]" / "no targets declared" only
  when all read / no clause otherwise. Explainer paragraph: a declared objective is not the customer's target.
- Left open: no On track on the demo data (R585; CC-1 On track proven on fakes only); `objective_site_count` is 1 per producer DB, never 3
  (no combined dataset, R535); Depot estate summary 409 (R577, FIX-01). Register R580-R586 + R542 note.

## OUT-E - cost check after the generator trial (built, in_review)
Branch `task/OUT-E-cost-proof` (from main b94aee17). Contract `AssetOpsV1-plan2/specs/OUT-E/spec.md`; packet `archive/agent-history/OUT-E-packet.md`;
history `archive/agent-history/OUT-E-phase-handoff.md`; E2/E3 review `AssetOpsV1-plan2/.agent/OUT-E2-3-review.md` (REVISE, fixed); E4 Architect ruling option b.
- Schema: CC-M merged (0036 productive-use kind, 0037 `trial_cost_comparison_revision`); empty merge `0039_merge_objectives_cc` (down 0037+0038) is
  the head; the 20 head-literal files and `mini_depth_probe` name it; 0036/0037 docstrings reworded only.
- `verification_rules.window_evidence` returns `generator_kwh` (outside `plan_sha256` and stored `details`; served on the evidence read).
- `financials/trial_fuel_comparison.py` (pure, Fraction): `compare()` per kWh of feeder demand, 11 reasons in 0037 order, `basis_sha256`.
- Writer `financials/adapters/postgres_trial_comparison_store.py` (INSERT-only, idempotent on basis and on key+payload; recorded at the service
  clock); `financials/composition.build_trial_comparison_ports`; `VerificationPorts.trial_comparison`; guard `$trialComparisonWriter` + probes
  in `tools/checks/test_estate_guard.py`.
- Hook (no route): `VerificationService.evaluate` -> `_after_new_outcome` on a non-replayed new VERIFIED/INEFFECTIVE/INCONCLUSIVE outcome;
  `_window_replay` + `_cost_check` (key `auto:{outcome_id}`, cost 0, SYSTEM demo actor); failures logged, never a rollback.
  `PostgresActionStore.sfc_history` (+ `finite_decimal`). Every evaluator test now appends one revision (PRICE_MISSING without a price).
- Read: `summary()` adds `cost_check`, `trial_hours`; board Earlier items carry `detail` (ACT in a MOVES row: Cost line on Optimize cost,
  before/after on a zero MG-2 target, attributed only on VERIFIED); mini Assure `VERIFIED_WITH_COST`; frontend renders `detail` as `<small>`.
- s602b case `verified` (40/28 kW generator, 60/63 kW loads, price v1); `complete_windows` gains 4 kW params and carries `trial_comparison`.
- Left open: R595 - on real s602b data the board day's Finding index is UNASSESSED, so the Action sits under Protect with no detail; the
  Cost-row line is proven on fakes only until the combined dataset. No re-run command (R592).

## COV-PARTIAL - estate coverage estate-coverage/2 (built, in_review)
Branch `task/COV-PARTIAL-estate-coverage` (from main 15eed62c8). Contract `AssetOpsV1-plan2/specs/COV-PARTIAL/spec.md`
plus Addendum 1. Packet `archive/agent-history/COV-PARTIAL-packet.md`. Decision `D-2026-10-31-estate-coverage-v2`.
- `estate/coverage.py` `_mini_grid_basis` adds `PARTIAL` (not in `COVERED`). An unchecked day sets `gap`. PARTIAL needs
  all four: a live read, `len(days) == _requested_days(from, to)`, at least one selected day, and every selected day
  clean. Any other gap folds into `unknown`, which is today's rule byte for byte.
- PARTIAL rows: every head `analytics.finding_index.touched` puts on a gap day is dropped (open end read as `k`). The
  rest go through `_mini_grid_money(..., withhold=True)`, so a PRICED row reads UNKNOWN with its revision and no amount.
- `days` sits on every mini-grid coverage and is None on a day-count mismatch, for cold, EV and Actions, and on
  `not_applicable()`. `text` comes from `DAYS_CHECKED`/`DAYS_WITHHELD` and is only set when PARTIAL.
- `estate/index.py` `_status`: PARTIAL ranks as UNKNOWN. `_coverage_site` projects `days`. Scope `covered_site_count`
  still counts only COVERED, so a PARTIAL Site is shown but not counted.
- `estate/portfolio.py`: `PARTIAL_STATUS`, placed after PENDING. It applies when some Site has F, E and M all PARTIAL and
  every other Site has no U unit.
- Frontend: `EstateSiteState` and `EstatePortfolioStatus` gain PARTIAL; `EstateCoverageSite.days?` is
  `EstateCoverageDays`. New: the `gapDayList` helper, the Portfolio context note `[data-portfolio-partial]` (R620),
  the drawer `[data-portfolio-scope-gaps]` and `partialConsequence`. On the Findings side: "Partly checked · ..." in
  `consequenceWords`, plus the `findingCauseCopy` panel and per-Site notice (R622).
- Tests: `test_cov_partial.py` (T1-T12), `test_cov_partial_portfolio.py` (S1-S6, X1, X2), `test_cov_partial_postgres.py`;
  vitest blocks in `estatePortfolio.test.tsx` and `estateRoots.test.tsx`.
- Golden `w301-estate-golden.json`: 39 added `days` keys, plus the KOBO-001 flips in scope-mixed and findings-mixed-week
  (Addendum 1 Q1).
- Open: CO-6 in `tools/demo_combined_finish.py` belongs to DEMO-A. Evidence and Financials show a PARTIAL Site through
  their existing "Some Sites are still being assessed" line; their rows carry day states, never PARTIAL. R621 means a
  historical gap stays Unknown.

## POLISH PA-1 - board truth (built, in_review)

- Contract: `specs/POLISH/` §1.1/§1.3/§1.6/§1.7/§6 D-2 and Addendum 2; packet `archive/agent-history/POLISH-PA-1-packet.md`.
- `site_outcomes/mini.py`: Cost copy "possible extra fuel cost on this day" / "No fuel cost estimated for this day";
  a PRICED `amount_high == 0` gives `COST_ZERO` and no headline money (R626 backend; idle fuel not modelled, owner Q1).
- `mini.no_run_day`: MG-7 settles when the overview day reading is `claim_level == "COMPLETE"` with no
  `dispatch_intervals` and readiness exactly `UNKNOWN`; the Readings line is `NO_RUN_READINGS`. Shared
  `claim_limit_read.reduce_day` is unchanged (Portfolio still reads zero intervals as UNKNOWN).
- `site_outcomes/board.py`: EV Optimize row uses `catalogue.ROW_NOT_MEASURED_EV_COST_UNPRICED` unless
  `headline_money["GROW_REVENUE"]` is set (R635). `cost_line` credits MODELLED_IMPROVEMENT only to VERIFIED, else
  `COST_NOT_CREDITED` (D-2, OUT-E L4).
- `ev.py` option "Investigate {connector_name(label)}". Trial comparison `history()` orders by
  `recorded_at, revision_no, id` (OUT-E L3).
- Open: EV-2 `missing_records` text still claims a tariff estimate but nothing renders it (Addendum 2 Q-C). Kobo
  Grow stays Unknown (R636: no sales records). Frontend fixtures still carry the old "exposure in this hour"
  headline (Lane B, PB-2). The S+1 Readings chip still shows readiness "Unknown" beside "readings complete".

