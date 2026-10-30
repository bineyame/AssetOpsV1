# OUT-C phase handoff (U1-U6 landed; closeout written; heavy jobs pending)

Sheet (wins): C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-sheet-OUT-C.md (§2 U5/U6, §3 copy, §4 wire,
§7 acceptance, §8 register). U1 review: AssetOpsV1-plan2\.agent\OUT-C1-review.md (ACCEPT, L1-L3 done).

## Landed (branch task/OUT-C-early-warnings)
- U1 67216448: outcomes/warnings.py (pure; KINDS sort; PEAK strict `>` - coordinator ruling on a sheet
  contradiction, 72/80 does not fire), catalogue/2 (MG-4, CC-3 measured).
- U2 5f9200e5: site_outcomes/visits.py, board.py warnings plumbing, read.py wire + summary warning_count,
  composers. U2 per-unit review requested from coordinator.
- U3 8928bcab: cold Cost row, w502 positive authored visits/plans (doc["out_c"], attest), Postgres
  test_out_c3_repeat_visits_postgres.py PASS, b4 cold updated (L1), FE fixtures catalogue/2.
- U4 (see git log; Postgres c4 + all 5 b4 board tests PASS, check-all 11/11): mini reserve_counts/_battery/Protect headline; ev extras + peak_facts (L3);
  tests test_out_c4_mini_ev.py, test_out_c4_ev_warnings_postgres.py.

## P-C1: NOT passed (recorded)
Estate summary over [2026-10-29, 2026-10-30) on w502 positive: 200, GreenHarvest Cost UNKNOWN, warnings only the 2
plan warnings (no REPEATED). So U5/U6 estate acceptance is vitest-only; no estate captures on this DB; carried
to the combined dataset. Board on the W5-01 window passes all acceptance-3 board checks.

## Resume: U5 then U6 (frontend), exactly per sheet §2 U5/U6
- Types: frontend/src/sites/outcomeBoardClient.ts:42-49 (OutcomeIssue.ref), :105 warnings; estate/estateClient.ts:488.
- ISSUE_KIND in frontend/src/sites/OutcomeBoard.tsx:46-52 (export it); dialog pattern in OutcomeBoard.tsx.
- Placements: estate/findingIndex.tsx:460; estate/EstatePortfolio.tsx PriorityPanel :208, pulse :618-632;
  estate/PortfolioOutcomes.tsx:64 PROTECT_DETAIL; sites/SiteFindingIndex.tsx:918; sites/ColdAssessmentViews.tsx:1255;
  sites/EvFindingIndex.tsx:21. CSS: port .oc-warn from frontend/mockups/v70/outcomes.css (mock outcomes.js:137-140).
- U6: work/GlobalMaintenance.tsx:253-259 card 4 replace; work/WorkRequestOverview.tsx:140 OverviewPanels notice.
- Fixture policy_versions.warnings in frontend/src/test/outcomeBoardFixture.ts:112 is still null; set
  "early-warnings/1" when typing.
- Heavy jobs need coordinator go: full vitest, full backend tier all, captures.
- Not yet run: full backend suite; Kobo b4 Postgres tests after the U4 mini change (MG-4 now needs dispatch).

## Packet notes to carry
- (b) connector with no unknown time: "{out} out {on|between ...}"; (d) b1_status rule-2 MG-4 -> MG-6.
- b1_board: cold Cost NO_OBJECTIVE + F-118 CHECKED safeguard issue; mini MG-4 NO_OBJECTIVE.
- b2_mini: PM-2 due-soon warning -> Protect WATCH, label "Due soon", UTC suffix asserted on warning seen.
- b3/b4_read fakes unchanged (same row from every window; dedupe); b4 board postgres `_case_db(slice_=)`.
- Battery contributor confidence: readiness chip whenever dispatch was read (incl. m = 0), literal sheet reading.
- EV window days are Site-local: a UTC-day window in Nairobi reads "between 20 Oct and 21 Oct".
- EV extras skip rows without asset_id (B fakes have none, so B3 EV boards show no EV warnings).
- Connector title: a label already starting with "Connector" is not prefixed again (w504 labels are
  "Connector c1"; first Postgres run showed "Connector Connector c1"). Small sheet deviation; record in packet.
- w504 E window: one CONNECTOR_OUT_OF_SERVICE ("44 min out and 16 min unknown on 6 Oct"), no PEAK (60/80),
  no CHARGER_FAULT (no plan, R569). EV board read_state PARTIAL from evidence_readiness ESTATE_SELECTION_INCONSISTENT
  (pre-existing B behaviour).

## U5/U6 landed (c7ca6ffe, 26448b3b, 5d57a6a3, 86fc3e59)
- U5 list/lenses/Site lists/Portfolio; U6 card + notice; register; U2-review L1 anchor tests (L2 already covered). Packet `.agent/OUT-C-packet.md`.
- Next (coordinator go): full vitest, backend `-Tier all`, captures 1440/390 vs v70 into `.agent/OUT-C-captures/` (no estate captures: P-C1).
