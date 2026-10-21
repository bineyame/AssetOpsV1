# W3-03 phase handoff

Branch `task/W3-03-portfolio-composition`. Spec: `.agent/W3-03-build-spec.md` closure 4 "Six builder runs" table,
plus closure 5 (S4/S7) on main `44307534`.

## Run 1 = seam run 0a (Lane A, existing estate files) â€” landed

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

## Run 2 = seam run 0b (Lane B) â€” landed, clean proof PARTIAL (stopped variant P-0b-1)
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
- RESOLVED (P-0b-1/r0b applied: `cold_case="excursion"`, `cold_drain=True`; cold line UNPRICED/null amount/pins selected cold Finding revision asserted; fixture + 0a tests 29 passed on `w303d_test`). Was: HELD cold `POTENTIAL_PRODUCT_EXPOSURE UNPRICED` â€” named cold `normal` makes no cold Finding/line (group
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

## Run 1a (Lane B) â€” landed: Portfolio scope/coverage/selection, token, cursor, refusal router (unmounted)
- `backend/assetops_backend/estate/portfolio.py`: `EstatePortfolioService(EstateEvidenceService).portfolio` runs the
  four 0a selectors once on one `scope` in one `PostgresEvidenceMoneyRead` snapshot; closure 5 S4 `reduce_units`,
  `settled`, `finding_unit`, `evidence_unit`, `money_units`; `portfolio_row` (wire `domain`/`episode_end`/
  `mechanism`, exact-pair Action join `_action_for`, quoted links); `token_site` (Finding-domain base + union of
  Finding/Action/Evidence/Financials arrays); `order_key`/`_marker` five-member Portfolio order. Body keys in 1a:
  envelope + `coverage{state,finding_state,evidence_state,money_state,sites}`, `lens`, `summary{finding_count}`,
  `order`, `total_count`, `rows`, `next_cursor`, `selection_token`. 1b adds cards/objectives/prompt/opportunity/
  progress/money and the remaining summary fields.
- `backend/assetops_backend/estate_portfolio_api.py::build_estate_portfolio_router` (not mounted; Lane A mounts after
  1b); `estate/composition.py::build_estate_portfolio_service`.
- Tests: `test_w303_portfolio_api.py` (2, fake selectors), `test_w303_portfolio_reduction.py` (41, S4 tables),
  `test_w303_portfolio_scope_snapshot_postgres.py` (2, on the 0b fixture).
- r0a L4 measured: one snapshot; `site_coverage` calls {mini_grid 3, cold_chain 3, ev_charging 6} = 12 for the
  three selectors, plus actions 1 (Action selector, KOBO only). No caching added.

### Run 1a readings (Architect may overturn)
1. "Settled" (S4 row 3) = `state in CURRENT|HISTORICAL`, `job_state` not `PENDING|FAILED|NONE`, freshness not
   `STALE`, match not `MISSING|PENDING`. Freshness `UNKNOWN` alone is not U (spec names only stale freshness).
2. F uses the same per-Site settled test on the Finding `site_coverage`; a Site type outside `DOMAIN_OF_SITE_TYPE`
   is U for F, E and M (unknown configuration, never N).
3. E: a Site with zero Evidence rows is U. A `HISTORICAL` row is G when it carries `selected_revision_ids` and is
   not `CONTRADICTORY` (the historical rule clears display readiness to UNKNOWN, so readiness is not re-read).
4. M: W3-02 `UNKNOWN_COVERAGE` is applied per Site/category through that Site's `_windows_covered` (its per-Site
   source), not category-wide, so a covered EV Site beside an uncovered one reduces to PARTIAL (r0a M1 intent).
5. Overall `coverage.state` = the same four-row reduction over all F, E and M units together.
6. `scope.covered_site_count` = Sites whose F, E and every M unit are not U. Status: EMPTY_SCOPE, then
   `snap.basis_historical` HISTORICAL, then PENDING if any Finding/Evidence/Financial Site coverage is
   `PENDING_RECOMPUTE` or job `PENDING`, then UNKNOWN if any of F/E/M is not COMPLETE, else CURRENT.
7. `total_count` is always the lens count (not nulled when incomplete; the UI appends `coverage incomplete`).
8. Rows: `action_state` = `application_state` (legacy projection); `next_move` null; links per S12 (quoted code;
   Finding route only for MINIGRID; Action link = W3-01 Action route) although S12 is outside 1a's reading list,
   because rows need links. `workflow_label` is 1b (closure 5 S7).
9. L4 "unchanged exact selected IDs and token versus the public roots": asserted as Portfolio rows == the public
   Findings rows filtered to SUPPORTED|UNCONFIRMED (field-by-field), `coverage.sites` == Findings root items, one
   window/cutoff across all roots, and a stable token across reads; the token digest itself has no public root
   counterpart to compare.
10. Foreign-tenant Site perturbation: a new tenant row plus a copied KOBO Site/import under it (test-scoped SQL).
11. Q-1a-1 (open, `.agent/W3-03-pending-rulings.md`): S9 tie key `recorded_at` is not in the Lane A Action rows.

### Run 1a checks
- Pure: `test_w303_portfolio_api.py`, `test_w303_portfolio_reduction.py`, `test_w303_estate_cursor.py`,
  `test_w302_estate_cursor.py`, `test_w301_estate_api.py`, `test_w302_evidence_api.py`, `test_w302_money_api.py`:
  134 passed.
- Postgres on private `w303f_test` (dropped after): `test_w303_portfolio_scope_snapshot_postgres.py` 2 passed, 230 s.
- `tools/check-all.ps1`: all 11 guards passed. No frontend touched.

## r1a fix round (done)
- M1: summary.finding_count null unless Finding coverage COMPLETE/EMPTY (portfolio.py); test asserts null on the partial variant. L2: partial rows compared with clean rows captured before add_empty_site. Reading 2: episode_end asserted vs public root.
- Passed on w303g_test: 75 tests (1a + fixture + selectors); check-all 11/11.
- Left for 1b: Q-1a-1 comparator (+coverage.py _selected_recorded_at), reading 3/8/11, L3 persisted EV M PARTIAL, L4 projections. Run 2: reading 6 (estateClient). Reading 9 already covered by existing inequality asserts. Not touched: readings 1/6 settledness, page_one_mode (r1a2).

## Next: r1a2 items, then run 1b


## Run 1b (Lane A + Lane B) - PARTIAL, stopped on pending rulings Q-1b-1..3
- Lane A `06acf1cf`: `estate/coverage.py::_actions` rows add private `_selected_recorded_at` (selected event
  `recorded_at`); `test_w303_selectors_postgres.py` asserts it equals the stored `action_event.recorded_at`.
  W3-01 golden (`test_w301_estate_golden_postgres.py`) + selectors: 8 passed, 215 s, bytes unchanged.
- Lane B `f3f04ef6` (`estate/portfolio.py`): `settled` (r1a2 1: HISTORICAL with selected head settled despite
  PENDING/FAILED job; `job_state=NONE` = no head = U); `money_pending` + status precedence (r1a2 2); `_action_for`
  `(-_selected_recorded_at, action_id)`, missing time raises `ActionSelectionError` (fallback removed);
  `workflow_label` + `rows[].workflow_label` (S7). Tests: `test_w303_portfolio_workflow_labels.py` (seven labels;
  tie test), `test_w303_portfolio_reduction.py` (historical job states, absent-head/current controls, UNKNOWN
  freshness, two pending U reductions), `test_w303_portfolio_api.py::test_builder_uses_one_connection_scoped_reader_and_refuses_missing_database` (r1a2 3).
- NOT built (resume here after rulings): r1a2 item 4 signed Portfolio cursor (Q-1b-1); all 1b projections
  (`selected_lines`, `money`, `scope_disclosure.sites`, five `value_cards`, `objectives`, `evidence_prompt`,
  `opportunity`, `progress`, `footer`, remaining `summary` keys) per r1a "Run 1b data source/wire fields"; the tie
  test's "both matching Actions remain in `progress.rows`" assertion; persisted tests
  `test_w303_portfolio_comparison_postgres.py` (November `[11-01,11-03)` chain / B4 proof, operating-cost, EV money),
  `test_w303_portfolio_scope_snapshot_postgres.py::test_page_size_does_not_change_cards_matrix_or_money` and
  `::test_late_revision_pending_historical_and_mixed_source` (variants incl. r1a2 1/2 persisted assertions).

### Run 1b readings (Architect may overturn)
1. r1a2 1 "selected head" under HISTORICAL = `job_state != "NONE"` (`coverage._job_state` returns NONE only when no
   day is selected); match/freshness rules unchanged.
2. r1a2 2 explicit pending guard = Site window uncovered AND a selected money line with eligibility `PENDING`
   (cold `withheld` / EV `ERROR_PENDING` reach lines as PENDING via `financials.decide`); no-line case is Q-1b-3.
3. "Outcome pending" = `_raw._verification_window` (already `in_window and not resolved`) and resolution != RESOLVED.
4. Q-1b-2: strict table order built; APPLIED + non-VERIFIED terminal reads `Applied` pending ruling.
5. Builder test uses the real builder against the migrated run-owned DB with an unknown tenant (EMPTY_SCOPE) and
   asserts the four selectors receive one `EvidenceMoneySnapshot` on one connection.

### Run 1b checks (private `w303h_test`, dropped after)
- Pure: workflow labels + reduction + portfolio API (incl. builder on DB) + cursor: 72 passed.
- Postgres: W3-02 money comparability + pinned facades (root bytes unchanged after the 1a composition edit) +
  W3-03 scope snapshot + selectors: 18 passed, 556 s. W3-01 golden + selectors after Lane A: 8 passed, 218 s.
- `tools/check-all.ps1`: all 11 guards passed. No frontend touched; no full backend suite (run 3).

## Run 1b resumed (after r1b) - PARTIAL: Lane A commit landed; stopped at context budget before Lane B
- Lane A (r1b Q-1b-1, Q-1b-3): `scope.py` `PORTFOLIO_CURSOR_KEY_ENV`, `portfolio_cursor_key()`,
  `encode_portfolio_cursor`, `_portfolio_envelope` (parser: base64/JSON, exact key set + lowercase 64-hex `mac`),
  `decode_portfolio_cursor` (compare_digest before `_shaped`); `decode_cursor("portfolio")` now always 422 (no
  unsigned path). `index.py::_scope` checks the key first for Portfolio (before any snapshot read, page one/empty
  scope too) and decodes signed; `_cursor` signs only Portfolio. `financials.py::windowed_lines` returns 4th
  `pending_guard`; `select_financial_scope` puts private `_pending_guard` on every per-Site cov (False for mini-grid
  and non-applicable). Tests: `test_w303_estate_cursor.py` (autouse key fixture; `::test_portfolio_signed_round_trip_and_tamper`,
  `::test_portfolio_signing_key_missing_or_malformed`, `::test_w301_w302_cursor_bytes_unchanged` sha256 of pre-seam
  bytes); `test_w303_selectors_postgres.py::test_financial_scope_pending_guard_without_line` (pure fake snap driving
  the real `windowed_lines`/`select_financial_scope`).
- Checks (private `w303i_test`, dropped after): W3-03 selectors + cursor, W3-02 cursor/money API/comparability/
  pinned facades/financials links, W3-01 golden + coverage: 102 passed, 1094 s (goldens unchanged).
  `tools/check-all.ps1`: all 11 guards passed.
- Known red until Lane B commit 2: `test_w303_portfolio_api.py::test_auth_before_parse_and_all_refusals` and
  `::test_cursor_lens_window_cutoff_and_v1_token` (no key set -> 503). Lane B adds the autouse key fixture there.
- Readings (Architect may overturn): R1 key check placed at the top of `_scope` (before `imported_sites`); admission
  is a filter with no refusal, so "admission precedes the key check" is unobservable. R2 parser does the envelope
  check only (no key), so a malformed envelope is 422 before a missing key 503; MAC/shape run in the snapshot.
  R3 the line-less guard test is pure (fake snap), not persisted; W3-02 public bytes proven by the W3-02 goldens.
- Resume (Lane B, commits 2 and 3 of the dispatch): commit 2 = autouse key fixture + extend
  `test_w303_portfolio_api.py::test_cursor_lens_window_cutoff_and_v1_token` (signed live/historical page two,
  valid-MAC changed grant/selection 409, missing-key 503 exact body), `portfolio.py::money_pending` ->
  `cov["_pending_guard"]` (PENDING line = consistency assertion only), `workflow_label` tests per r1b Q-1b-2 table
  (code already matches). Commit 3 = everything in the "NOT built" list of run 1b above except the cursor.

## Next: finish run 1b Lane B (commits 2-3 above), independent review of 1b, then run 2 (page)
