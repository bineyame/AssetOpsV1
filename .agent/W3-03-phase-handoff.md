# W3-03 phase handoff

Branch `task/W3-03-portfolio-composition`. Spec: `.agent/W3-03-build-spec.md` closure 4 "Six builder runs" table,
plus closure 5 (S4/S7) on main `44307534`.

## Run 1 = seam run 0a (Lane A, existing estate files) — landed

- `estate/index.py`: public `select_finding_scope(snap, tenant_id, req, scope) -> (per_site, rows)` and
  `select_action_scope(...) -> (per_site, rows)`; rows unfiltered/unsorted/unpaged, moved verbatim. `_findings`,
  `_actions` and `_finding_coverage` consume them. `_fence`/`_cursor` handle `portfolio` (kind + lens + null filter).
- `estate/evidence_money.py`: `select_evidence_scope(...) -> (per_site, rows)` (full canonical order);
  `estate/financials.py`: `select_financial_scope(...) -> (per_site, lines, applicable, groups, exclusions,
  diagnostics)` (full W3-02 order). Roots consume them.
- `estate/scope.py`: `KEYS["portfolio"]`, lens validation, `state` refused as unknown key; cursor keys = Finding keys
  + `kind`; five-part marker in `_marker_ok`/`cursor_after`/`cursor_marker`/`decode_cursor`.
- `estate/coverage.py`: Finding rows add `episode_end` (W1 selected revision; cold/EV selected heads) and
  `mechanism: None`; Action rows add private `_plans`, `_outcomes`, `_outcome_id` (`_verification_window` kept).
- `postgres_estate_read.py::verification`: plans gain `id`, `recorded_at`; both queries ordered `recorded_at, id`.
- Test: `backend/tests/test_w303_estate_cursor.py` (pure).

## Readings (Architect may overturn)

1. "Run 1" read as the first of the six runs, seam run 0a (closure 4 sequence: Lane A takes the branch for 0a first;
   1a needs reviewed 0a selectors). Closure 5 assigns 0a only "preserve `_verification_window` + exact verification
   IDs/times"; S4 and S7 `workflow_label` land in 1a/1b, so not built here.
2. Portfolio row facts exposed by the Finding selector as private keys `_domain` (stored uppercase `site_type`),
   `_episode_end`, `_mechanism`, so Findings root bytes stay identical; 1a maps them to wire `domain`,
   `episode_end`, `mechanism`.
3. Verification IDs reach the Action selector rows through private `_plans` (each `{id, recorded_at, later_start,
   later_end}`), `_outcomes` (`{outcome_id: recorded_at}`, the existing map) and `_outcome_id` (the surviving
   resolution's outcome), also via `_raw`.
4. A Portfolio cursor with nonnull `state_filter` or a `lens` outside the four lenses is a 422 shape error, not 409.
5. Cursor tests live in a new `test_w303_estate_cursor.py` (no file named in the spec for 0a).
6. The frontend `estateClient.ts` Portfolio status union (S1) is not a 0a deliverable; left for 1a/2.

## Next: run 2

Seam run 0b (Lane B): the single persisted 10-06 fixture and exact public root assertions (closure 4 B3/B4, closure 2
Q9 as amended, closure 3). Requires an independent 0a review first (unchanged W3-01/02 golden bytes).

## Run 1 checks

- Focused pure: `test_w303_estate_cursor.py`, `test_w302_estate_cursor.py`, W3-01/02 coverage/API tests: 101 passed.
- Postgres on private `w303a_test` (dropped after): W3-01 golden, index, index-EV, provenance DTO; W3-02 money
  comparability, financials/evidence links, evidence scope snapshot, evidence EV, pinned facades, plus both cursor
  files: 116 passed in 28m04s (golden response bytes unchanged).
- `tools/check-all.ps1`: all 11 guards passed. No full backend suite (run 3 owns the same-revision full suite).

## Run 0a fix round (review REVISE -> fixed)
- M1: `financials.py::select_financial_scope` per-Site cov now carries private `_windows_covered` (mini-grid: `state in COVERED`; cold/EV: windowed_lines flag). Pure test in `backend/tests/test_w303_selectors_postgres.py`.
- L1: Postgres value test (same file) asserts `_episode_end`, `_domain`, `_mechanism`, plan `id/recorded_at`, `_outcome_id`/`_outcomes` equal stored rows.
- L2 (confirm 422) and L4 (measure site_coverage calls, run 1a) need no 0a change. L3 (EstatePortfolioStatus in estateClient.ts) is left to run 2 per r0a.
- Checks: 0a tests + W3-02/W3-01 Postgres goldens 65 passed (w303b_test, dropped), golden bytes unchanged; check-all 11/11.
- Next: run 2 (0b) after re-review.

## Run 2 = seam run 0b (Lane B) — landed, clean proof PARTIAL (stopped variant P-0b-1)
- `backend/tests/test_w303_portfolio_fixture_postgres.py`: `build_portfolio_fixture(request, monkeypatch, capsys,
  cold_case="normal", cold_drain=False) -> PortfolioFixture` (one fresh DB; cold `normal` + EV `complete` per
  `mixed_replay`; EV-LAB-002 per `two_ev_sites` with tag 0x3022, golden KES tariffs + W2-07 money; P01 `PowerSite`,
  publish v1-v3, `Rig.run()`; all four Sites `imported_before` 10-05; frozen = max(runner.now+1min, db_now, latest
  cold/EV stored time+1us); `pin_snapshots` pins `EstateSnapshot`, `EvidenceMoneySnapshot`, assessment
  `_transaction_time`). `fx.estate()` (findings/actions) and `fx.money()` (evidence/financials) clients; `fx.window`.
- `::test_one_day_three_domain_fixture_public_roots`: all roots CURRENT, same window/known_at, 4 Sites; F/E/M roots
  COMPLETE; no Action in 10-06 (B4); W1 PRICED from stored consequence = ELIGIBLE operating-cost line; two EV lines
  match stored heads, disjoint technical/evidence IDs, one COMPARABLE group with exact `group_key_for_partition`;
  `estate_total` null; one-day dispatch selection present; every selected head/evidence in (09-30, frozen].
- RESOLVED (P-0b-1/r0b applied: `cold_case="excursion"`, `cold_drain=True`; cold line UNPRICED/null amount/pins selected cold Finding revision asserted; fixture + 0a tests 29 passed on `w303d_test`). Was: HELD cold `POTENTIAL_PRODUCT_EXPOSURE UNPRICED` — named cold `normal` makes no cold Finding/line (group
  UNKNOWN_COVERAGE). Probe: `excursion` + W2-04 `drain` makes it pass. See `.agent/W3-03-pending-rulings.md` P-0b-1.

### Run 2 readings (Architect may overturn)
1. 0b names no test file; used `test_w303_portfolio_fixture_postgres.py`, builder importable by 1a/1b.
2. Portfolio root does not exist yet: Portfolio-only facts (combined_value, card states, pulse note, F/E/M fields) are
   1a/1b; 0b asserts the equivalent root facts (`summary.estate_total` null, root coverage COMPLETE).
3. Price publication steps v1,v2,v3 as in `test_cost_lens_only_exact_eligible_current_rows` (power_estate P01 path).
4. Variants (a)-(e), empty Site and foreign tenant are 1b (N6); 0b only proves the (b) precondition (heads > 09-30).
5. B4 workflow-label Action-window test is 1b (closure 5 S7); 0b asserts no Action selected on 10-06.
6. L3 (`EstatePortfolioStatus` in `estateClient.ts`) belongs to seam run 2 (the page run after 1b) / Lane A per r0a/r0b; no frontend change in 0b.

### Run 2 checks
- `test_w303_portfolio_fixture_postgres.py` + `test_w303_estate_cursor.py` + `test_w303_selectors_postgres.py` on
  private `w303c_test` (dropped after): 29 passed, 85 s. `tools/check-all.ps1`: all 11 guards passed. No frontend touched.

## Next: run 3
Next: independent review of 0b, then run 1a.
