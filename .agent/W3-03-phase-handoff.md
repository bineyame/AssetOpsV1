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

## Run 1a (Lane B) — landed: Portfolio scope/coverage/selection, token, cursor, refusal router (unmounted)
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

## Run 1b Lane B (resumed 2) - PARTIAL: commits 2 and 3a landed; stopped at context budget before 3b
- Commit 2 `3a0d96bc`: `test_w303_portfolio_api.py` autouse test-only key + `signed()`; signed live/historical page two,
  unsigned/wrong-MAC/tampered 422, valid-MAC changed selection/grant 409, missing/malformed key 503 exact body (page
  one, page two, empty scope). `portfolio.money_pending` uses `_pending_guard`. Label table (r1b Q-1b-2) and line-less
  guard cases in `test_money_table`.
- Commit 3a `6c4e0449` (`portfolio.py` "run 1b: full-scope projections" block + `_portfolio` body): `selected_lines`,
  `money`, `scope_disclosure`, `value_cards` (`operating_cost_card` N2), `objectives` (`objective`, N5 reasons),
  `evidence_prompt`, `opportunity`, `progress` (nine fields, `_plan_id`), `footer`, full `summary`. Tests:
  `test_w303_portfolio_api.py::test_full_scope_projections_ignore_page_size_and_empty_scope`,
  `::test_evidence_prompt_null_steps_and_coverage_precedence_pure`; persisted
  `test_w303_portfolio_scope_snapshot_postgres.py::test_page_size_does_not_change_cards_matrix_or_money`; tie test
  now asserts both Actions (plus another-revision Action) in `progress.rows`. Autouse key fixture added to the
  persisted scope-snapshot file (its 1a tests would otherwise 503 after Lane A).
- Checks: pure W3-03 (api, labels, reduction, cursor) 84 passed; scope snapshot postgres 3 passed, 334 s (private
  `w303j_test`, dropped after); `tools/check-all.ps1` all 11 guards passed (before 3a's last test edit; rerun next).
- NOT built (resume 3b here): `test_w303_portfolio_comparison_postgres.py` (new file) with
  `::test_selected_action_window_workflow_and_withdrawal` (B4 `[11-01,11-03)` successive cutoffs per r1b "Progress and
  B4"), `::test_operating_cost_first_match_wins_across_partitions`, `::test_ineligible_overlap_and_unknown_coverage_decline_total`,
  `::test_ev_window_money_has_no_finding_attribution`; scope-snapshot `::test_late_revision_pending_historical_and_mixed_source`
  (variants a/b/c1/c2/d/empty-Site incl. r1a2 1/2 and r1b Q-1b-3 line-less guard), `::test_evidence_prompt_null_steps_and_coverage_precedence`
  (fake snapshot; a pure version exists in the API file), `::test_ev_footer_first_eligible_and_coverage_warning`.
- Readings (Architect may overturn):
  R4 `money_pending` = `_pending_guard` OR (uncovered window AND a selected PENDING line): the line stays sufficient,
  not required ("consistency assertion" read as sufficiency, since mini-grid PENDING_REASSESSMENT and Site PENDING
  lines carry no guard).
  R5 Card `detail` is null for COMPARABLE_GROUP/SITE_OWNED (page formats category/window per S10); UNPRICED detail is
  server-filled `{site_name} · consequence recorded without a price`; `display_value` null for the two money states,
  literal otherwise; `basis` null always; VERIFIED_RECOVERY destination `/financials` (wire example).
  R6 Risk card is always UNKNOWN (no reviewed RISK producer, closure 4 N4); no COUNT path built.
  R7 All objective `destination`s null (no reviewed Site Evidence/Financials route named); matrix item adds
  `site_name` and stored `site_type` as `domain`. Unknown configuration gives UNKNOWN cost/evidence cells.
  R8 Evidence cell: FULL if all rows FULL, else NONE if any NONE, else LIMITED; UNKNOWN when historical, `evidence_unit`
  is U (incl. CONTRADICTORY/no rows).
  R9 `evidence_prompt` also carries `site_code`; text is server-built from the three literals.
  R10 `progress.verification_plan_id` = plan active at the cutoff, else latest recorded selected plan; outcome id =
  `_raw._outcome_id`. Counts use W3-01 `_coverage_state` over Action coverage (as the Actions root) and its
  `_verification_window` / `_verified_recent` flags. No per-row "origin revision not selected" field (nine exact
  fields); the page must derive that disclosure - flag for run 2.
  R11 `scope_disclosure.sites[].source_provenance` = `snap.cited_provenance(site, union cited ids, selected_revision_ids)`
  (one extra same-connection query per Site with selected IDs), null when the Site has no selected ID.
  R12 Footer requires `quantity.low == high`, `amount.low == high`, ELIGIBLE, and a non-current-view EV `links.evidence`
  route; the "other Sites may lack coverage" sentence is left to the page from `coverage.sites` + domains.
  R13 `evidence_gap_site_count` counts Sites in every typed gap (null-step gaps included).

## Run 1b Lane B (resumed 3) - commit 3b, main merge, r1b2 applied
- Commit 3b `0f29d4cb`: new `test_w303_portfolio_comparison_postgres.py` (`::test_selected_action_window_workflow_and_withdrawal`
  B4 `[11-01,11-03)` cutoffs Outcome pending -> Verified -> Resolution withdrawn, IDs/times vs Action root + stored rows;
  `::test_operating_cost_first_match_wins_across_partitions`, `::test_ineligible_overlap_and_unknown_coverage_decline_total`,
  `::test_ev_window_money_has_no_finding_attribution`); scope snapshot `::test_late_revision_pending_historical_and_mixed_source`
  [a_lineless_cold, b_historical, c1_unbound, c2_mixed, mg_historical_marker], `::test_evidence_prompt_null_steps_and_coverage_precedence`
  (fake World snapshot), `::test_ev_footer_first_eligible_and_coverage_warning`; fixture `w1_source` (P01/MIXED/UNBOUND).
  No code defect found. Notes: wire `recorded_at`/`known_at` are whole seconds, so tests compare via `wire_time`
  against the exact cutoff; at the 09-30 cutoff `accepted_action_count=0` (Action coverage complete), not null.
- Merge of main `12673d16` (r1b2 `cdc43856`); handoff and pending-rulings files kept.
- r1b2 commit: R1 `estate_portfolio_api.py` checks `portfolio_cursor_key()` after parse, before `store.read`
  (snapshot check kept); R10 `progress(..., selected_pairs)` adds `origin_revision_selected` (tenth field, full
  selected Finding pairs before lifecycle/lens/page); R11 `postgres_evidence_ledger.link_rows_many_on` (one query,
  `_links_sql` shared, single-Site SQL text byte-identical), `evidence/composition.build_link_rows_many_reader`,
  `PostgresEstateRead(link_rows_many=)` + `EstateSnapshot.cited_provenance_many` (`_Prefetched` reads; per-Site
  fallback when unset), `portfolio.py` scope disclosure batched, key passed in both compositions and W3-02 test
  `evidence_read`; R12 footer requires nonnull `links.evidence`. Tests: R1/R2 zero-read + refusal order
  (`test_cursor_lens_window_cutoff_and_v1_token`), R5 both priced states, R7 null destinations + unknown config,
  R8 evidence-cell vectors, R10 tie test + B4, R11 constant batched count (1 per request at limits 1/100) + per-Site
  truth, R12 null-route skip, R13 null-step-only count. R1/R2 touch the Lane A cursor seam boundary (coordinator
  instructed "apply every r1b2 change").
- Pending rulings added (no decision taken): P-1b-1 variant (a) not produced by `advance_late`; P-1b-2 mini-grid
  marker producer is STALE (positive r1a2-1 proof missing); P-1b-3 (d) overlap no producer; P-1b-4 single W1 Site /
  no persisted EV ERROR_PENDING; P-1b-5 R4 false-guard + PENDING line no producer; P-1b-6 R10 persisted `true`.
- Run 2 items from r1b2: type/render ten progress-row fields and `Origin Finding revision not selected` only when
  `origin_revision_selected=false` (page size 1, nonmatching lens) in `rendersChangeDisclosureWithoutRecoveredMoney`;
  R12 warning predicate (`Other Sites may lack comparable full-window coverage.` only from another applicable EV
  Site with UNKNOWN/PENDING/STALE coverage, else `Categories and windows remain separate.`) in
  `rendersEvFooterAndMissingEnergyBasis`; preserve R2 refusal order; R5 formatted value + UNPRICED copy and R6
  `Not assessed` (empty Risks lens) in `rendersContextFiveCardsPulseAndSelectedRows`; R7 `Site detail unavailable`
  and R8 labels in `rendersFiveObjectiveRowsForEveryAuthorizedSite`; R9 `site_code` typed in
  `rendersTypedEvidencePromptAndExactDestinations`; never infer origin selection from the paged Finding table.
- Checks (private `w303k_test`, dropped after): pure W3-03 (api, labels, reduction, cursor, fake prompt) 85
  passed; W3-03 persisted (comparison, scope snapshot, fixture, selectors) 19 passed, 23 min (two then fixed and
  rerun green: B4, page-size); W3-02 comparability + money API + W3-01 golden 24 passed, 7 min (bytes unchanged);
  `tools/check-all.ps1` all 11 guards passed. No frontend touched; no full backend suite.

## r1b3 + 1b review Lows (Lane B) — landed
- P-1b-1..6 resolved by r1b3 (pending-rulings file): test comments now cite the ruled pure/fake-snapshot proofs and
  claim no persisted late-cold, covered mini-grid marker, overlap, EV pending head or origin-true case.
  `test_money_table` adds the explicit false-guard + PENDING-line case (P-1b-5); the labels test adds Action-order
  independence for `origin_revision_selected` (P-1b-6).
- L2: the R11 test spies `_Prefetched` and fails on any per-Site `link_rows` fallback. L4: run-1b prints removed.
  L5: comparison comment cites P-1b-6. L6: this file is UTF-8 without BOM, dashes restored.
- Open: L1 (file ownership) and L3 (prompt Site order sentence) are with the Architect as r1b4.

## Next: r1b4, then run 2 (page)

## Run 2 (Lane A + Lane B, page) - landed; one open ruling P-2-1
Commits on `task/W3-03-portfolio-composition` after merging main:
- `2845897c` Lane A: `main.py` mounts `build_estate_portfolio_router` (reviewed 1b); `estateClient.ts` adds
  `PORTFOLIO_SCHEMA`, `EstatePortfolioStatus` (5), F/E/M `EstatePortfolioCoverage`, row/card/objective/prompt types,
  ten-field `EstateProgressRow`, `EstatePortfolioBody` (`Omit<EstateEnvelope,"status"|"coverage">`),
  `EstatePortfolioQuery` (lens, no state) and `EstateClient.portfolio()`; existing root types unchanged.
- `a0631e80`, `d3fb632b`, `5cef129c` Lane B: `estate/EstatePortfolio.tsx` (+ `portfolioWords.ts`,
  `estatePortfolio.css` = mock `portfolio.css` scoped to `.estate-portfolio`, print rules dropped, app additions
  last), `__tests__/estatePortfolio.test.tsx` (14 tests: all run-2 and run-3 named page tests incl.
  `rendersEmptyPendingHistoricalAndSourceConflict` five typed statuses and
  `rendersMeasuredPanelHierarchyAndScrollContainers` with `expectV69Panels`/`expectPlantedPanelRejected("portfolio")`),
  `__tests__/portfolioFixtures.ts`. `test/panelStructure.ts` LEADING_SELECTOR admits only
  `.portfolio-v2 > .portfolio-context|.value-grid|.portfolio-pulse` (proved: without it the panel test fails with 3
  leading intruders); `test/settled.ts` learns `Loading the Portfolio across the estate.`.
- `4a1fd7f9`, `c501d089` Lane A: `/portfolio` route (`PORTFOLIO_ROOT_PATH`, `EstatePortfolioFrame`, no `/` alias),
  rail `live|Portfolio|OPERATIONS|/portfolio`; rail/route tests, `navigation-truthfulness.ps1`,
  `navigation-rail-fixtures.ps1` (dead-link subject now Assets) and six shell/ui tests updated together;
  `estatePortfolioRoutes.test.tsx::test_w303_global_route_precedence_and_unavailable_multiset`.
- Not done here (run 3 per closure 4 S16): registry panel rows. Capture harness and script:
  `.agent/W3-03-evidence/test_serve_portfolio.py`, `capture-portfolio.mjs` (all Q24 caps + four panel caps).

### Run 2 readings (all eleven confirmed by r2; no replacement text)
1. Lane A shell wiring landed after the page commit (a route needs the page); client + API mount came first.
2. Matrix header is plain `site_name`/`site_code` (no wire Site link); every null cell destination shows
   `Site detail unavailable`; cell reason is `aria-description` + `title`.
3. Row Site link is `links.site` with visible `Opens current Site view`; cold/EV Finding and review line are inert
   `Finding detail unavailable`; W1 rows show `Review Finding` link to the exact Finding route.
4. Value first line: PRICED outward bounds, UNPRICED `Unpriced`, other states `Source unverified`, null source with
   no price `No consequence recorded`; PENDING_RECOMPUTE/HISTORICAL Site prefixes `Updating · `/`Historical · `
   and a priced row shows `Value withheld`. Second line always `Basis not recorded` (no basis field on the wire).
5. SITE_OWNED card uses outward rounding unless the line domain is `ev_charging` (half-even 2); detail built when
   the API detail is null. Footer amount uses half-even 2 and `quantityText`; `{amount}` includes the currency.
6. Evidence aside is a `div.note` with a `role=heading` title (panel-structure guard allows `.note` between panels;
   a `section`/`h3` there is flagged); it renders `Site {site_code}` from the server, no link.
7. R12 warning: another EV Site (by `scope_disclosure` domain) other than the footer line's Site whose coverage is
   UNKNOWN/PENDING_RECOMPUTE/STALE_SOURCE.
8. Load more refusal (401/409/503) replaces the whole page with the refusal (no stale names/cards/rows).
9. Mock `screen-foot` and topbar `portfolio-name`/search block are mock chrome; not reproduced or measured.
10. Unsupported opportunity quantities use neutral grey, 16px (13px at 390) to fit the 247/272 caps.
11. Real rows carry more honest-gap lines than mock examples; Findings cell spacing tightened (10px/7px padding,
    2px small margins) to keep each row within its cap.

### Run 2 captures (private `w303m_test`, dropped after; app via Vite :5781 -> API :9781)
| state | w | status | doc h | scrollW | priority | objectives | side | opp | progress | context | cards | rows | table scroll | matrix scroll |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| positive | 1440 | CURRENT | 1362 | 1425/1425 | 559 | 376 | 559 | 229 | 229 | 23 | 198x5 | 93,93,93 | 790=790 | 390>275 |
| positive | 390 | CURRENT | 2947 | 390/390 | 539 | 361 | 546 | 268 | 308 | 55 | 189,189,185,185,204 | 94,94,94 | 720>336 | 390>328 |
| partial (+W303-EMPTY-001) | 1440 | UNKNOWN | 1319 | 1425/1425 | 516 | 376 | 516 | 229 | 229 | 23 | 198x5 | 93x3 | 790=790 | 467>275 |
| partial | 390 | UNKNOWN | 2966 | 390/390 | 576 | 361 | 503 | 268 | 308 | 55 | as positive | 94x3 | 720>336 | 467>328 |
| historical (known_at 09-30, after empty Site) | 1440 | HISTORICAL | 1319 | 1425/1425 | 516 | 376 | 516 | 229 | 229 | 23 | 198x5 | empty row 36 | 790=790 | 467>275 |
| historical | 390 | HISTORICAL | 2732 | 390/390 | 329 | 361 | 503 | 268 | 308 | 55 | 178,178,185,185,204 | 36 | 720>336 | 467>328 |
All blocks within caps (`over=[]` in every JSON). Columns 1440 95/182/190/71/103/150 (mock 96/184/192/72/104/152);
390 86/166/173/65/94/137 (exact). Cards: positive/partial SITE_OWNED `$0.00–$3.44`/UNKNOWN/UNSUPPORTED x2/
NOT_ESTABLISHED; historical WITHHELD first. Viewed: positive 1440 and 390 PNGs.
Pending/empty/refusal captures remain run 3.

### Run 2 checks
- Frontend full suite 104 files / 2449 tests passed; `tsc --noEmit` clean; `npm run build` ok.
- `tools/check-all.ps1`: 9/11 pass; FAIL missing-claim orphan scan + its fixtures run, solely on the two ruled inert
  CTAs (P-2-1 in `.agent/W3-03-pending-rulings.md`). Architecture (shell-overflow: tables via `DataTable`) passes.
- Backend: `test_w303_portfolio_api.py` 4 passed 1 skipped; TestClient `/api/estate/portfolio` without DB -> 503
  frozen body. No full backend suite (per dispatch).

## Next: run 3 (packet + final review)
First resolve P-2-1. Run 3: registry panel rows (S16), pending/empty/refusal captures, packet, final review.

## Run 3 (after r2) - PARTIAL: P-2-1 landed; stopped on P-3-1
- Merged main (no conflicts). `63e83d83`: `G-portfolio-opportunity` in registry `mock_gaps.gaps` (after
  `G-asset-remaining-life`; `portfolio` not enrolled; no portfolio ledger `gap_ids` exists), mirror in
  `ui/gapCatalogue.ts`, `EstatePortfolio.tsx` `OpportunityPanel` wraps both inert spans in
  `<MissingClaim as="span" className="portfolio-inert" ...>` with literal inner spans. Scan passed (41 tagged uses),
  scan fixtures 24/24, check-all 11/11, portfolio page+route tests 15/15. r2 readings 1-11 all Confirm (no
  replacement text); P-2-1 marked resolved.
- Stopped: r2's four panel rows fail `check_v69_dependency_registry.cjs` (P-3-1). Reverted, uncommitted.
- Not done: registry rows, pending/empty/refusal captures, recaptures, packet. Frontend full suite/tsc/build not
  rerun this run (only the focused portfolio tests).

## Next: rule P-3-1, then resume run 3 (rows, captures, packet), then final review + full suite

## Run 3 resumed (after r3) - PARTIAL: registry landed; all eight captures taken; stopped on P-3-2
- Merged main (no conflicts). `8af47c17`: r3 literal nodes `I-estate-portfolio-read`/`-ui` (after
  `I-estate-money-root`), four portfolio `panels` rows (all `gap`), portfolio ledger `registry_dependencies`; registry
  checker exit 0, ledger valid, check-all 11/11, no checker change. P-3-1 marked resolved.
- Harness (`test_serve_portfolio.py`): `W303_DB` (default `w303o_test`), `W303_COLD_DRAIN=0` (pending),
  `W303_NO_CURSOR_KEY=1` (503), `W303_ROUTER=capture` (same router/service moved to the front of the route list; FastAPI
  keeps included routers as lazy entries, so a path filter cannot remove the mount) with `/__capture/mode`
  (`limit1`, `auth=deny`, `tenant=foreign`). `capture-portfolio.mjs`: `success <STATUS> <matrixSites>`,
  `refusal <CODE>`, `refusal-409 <api-base>` (one tab per width, page one at limit 1, add empty Site, click
  `Load more Findings`), `W303_FORBID` leak check, per-capture `checks`/`failed`.
- Captures (Vite :5781 -> API :9781, private `w303o_test` recreated per process and dropped; servers stopped by port):
  positive CURRENT 4 Sites 3 rows doc 1362/2947; refusal-409 (before click CURRENT 1 row + Load more; after: 409
  `ESTATE_BASIS_CHANGED`, 0 privileged blocks, no Site text); partial UNKNOWN P/P/P 5 Sites 1319/2966; historical
  HISTORICAL U/U/U 0 rows, first card WITHHELD 1319/2732; pending PENDING C/C/P, 3 rows, product-exposure group 0
  lines, `Updating selected Sites`, W1 SITE_OWNED `$0.00–$3.44` 1362/2947; empty EMPTY_SCOPE E/E/E 0 rows 0 Sites
  1232/2638; refusal-401 (401 + `WWW-Authenticate: Bearer`) and refusal-503 (frozen null body): 0 privileged blocks.
  All `over=[]` and `failed=[]` except empty 390: `card0 218>207; card1 218>207` and `matrixScrolls` (P-3-2).
  Mock re-measured (`tools/measure-mock-panels.mjs`, portfolio): panel heights equal the run-2 baseline the caps use.
  Viewed: pending 390, refusal-409 1440, empty 390.
- Checks: frontend 104 files, 2448/2449 (1 failure `s404SiteFindingIndex.test.tsx` "changing the dates writes a new
  window" `toHaveValue(2026-10-20)`; the file alone passes 37/37); tsc clean; build ok.
- Not done: review packet (waits on P-3-2, which may change the page and require recapture).

## Next: rule P-3-2, then finish run 3 (any fix + recapture, packet), then final review + full suite
