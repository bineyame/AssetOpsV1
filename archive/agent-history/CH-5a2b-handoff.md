# CH-5a2b handoff (phase 2: steps 1-4 built and committed; 5-8 open)

Branch `task/CH-5a2b-chain-counts`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-ch5a2b`, head: see `git log`.
Authority: `AssetOpsV1-plan2\.agent\build-sheet-CH-5a.md` §B13 as amended by §B14; pre-flight
`.agent/CH-5a2b-preflight.md`. `B` = `backend/assetops_backend`. Phase 1 is `a8c748b7c` (section below).

## Phase 2 (this session)

### `c10d51658`, step 1: one count computation in `B/chain/claims.py`
- `estate_count_claims(req, sites, lo, hi, opportunities, unavailable)` returns
  `EstateCounts{claims, days, threads}`.
- Thread set: threads with a Finding occurrence whose episode meets `[lo, hi)`, intersected with
  `site_chain.threads_of`. Each is read on `window_day` at `site_cutoff(domain, k, req.evidence_cutoff(site), k)`.
- New port `ChainReadPort.evidence_cutoff` / `ChainRequest.evidence_cutoff` (`_EVIDENCE_CUTOFF` in
  `postgres_chain_read.py`). Cold/EV only; mini never reads it.
- `opportunity_items` is one memoised `opportunity_threads` read. It returns None when the read fails.
- `EstateClaims` is the injected callable, built by `chain/composition.build_estate_claims`. `main.py` sets
  `.count_claims` on `estate_index` and `estate_portfolio`.
- Where the claims now appear:
  - `/estate/chain` `counts` are Claim wire objects; `sites[].threads` is the classify dict.
  - Findings `summary.claims` carries `count.opportunities`.
  - Portfolio `summary.claims` carries all 3 keys, and `summary.count_basis = count_basis(days)`.
- The old Portfolio basis value is renamed `coverage_basis`. It now drives only `finding_known` and
  `evidence_known`.
- When nothing is injected, every claim and `count_basis` is NOT_KNOWN.
- Golden regenerated: `estate_week_2026-10-25.json`.
- Unit tests updated:
  - `test_cov_partial_portfolio` uses a stub, which also proves that COMPLETE coverage over partly graded days
    reads CHECKED_DAYS.
  - `test_w301_estate_api` and `test_w303_portfolio_api`.

### `80d3ae477`, step 2: COH-17 (`coh17_count_claims`)
- Judges only manifests stamped `"claims": True`.
- In every estate and day window, compares chain `counts` with the Portfolio (3 keys) and with `findings_all`
  (`count.opportunities`) on value, basis and text. Windows whose Site sets differ are skipped.
- Also flags: no chain body, no claims, a moved window.
- The collector fetches `{prefix}chain_estate.{w}` and `chain_site.{day}`.
- Fixtures `clean_claims` and `coh17_claims_disagree`.
- Shown non-vacuous: a planted change that ignores text made the disagree case fail. Reverted.

### `0a7f369c2`, steps 3-4: R1 and Q11
- New reads `ChainRequest.placement_facts` and `ChainRequest.action_rows`, plus a pure `reduce_action_rows` over
  `actions.lifecycle`.
- Adapter `placement_facts`: at most 3 statements, imports `PublicProvenance` unchanged, and gets `link_rows` /
  `link_rows_many` injected.
- Adapter `action_rows`: the store's `site_window_on` is injected, plus SQL for plans and outcomes.
- `mini.py`:
  - The `estate` port and `estate_bounds` are deleted.
  - The chip is `place(row, None, {}, None)` for board-day heads only.
  - New diagnostic `ACTION_ROW_MISSING`. `failed` names are `placement_facts` and `action_rows`.
- The prefetch no longer includes `work_rows`.
- Q11: `SiteOutcomeBoardService.cold_ev_cutoff` is shared by `compose` and `thread_cutoff`. The thread route
  parses `board_window` (optional from/to).
- Board contract goldens: unchanged.

### `0cdae5f9f`: Postgres test edits, NOT RUN
- `test_ch5a2_chain_api_postgres`: asserts the claims.
- `test_out_b4_board_postgres`:
  - Spies on `ChainRequest.action_rows`.
  - Uses the Q5 `ACTION_KEYS`.
  - Day A now asserts no `estate` and no `action_rows` failure (before: `["estate"]`). When it runs, record the
    actual value.

### Test and guard state
- Unit tests green: claims 31, contract 24, board contract 13, b2 mini 32, b4/qw2 15, adjacent 419.
- One pre-existing failure, not from this slice: `test_out_a1_outcome_map::test_outcomes_package_is_pure`
  (`outcomes/warnings.py:12` imports `chain.refs`; the file is unchanged since main `27aa6a638`).
- Guards at `0a7f369c2`: check-all 12/14 PASS.
- The two missing-claim guards hit MODULE_NOT_FOUND `typescript`: this worktree has no `frontend/node_modules`.
  No frontend file is touched.

## Next (in order)
5. Postgres tests, one file per call, and only while no MD-0b `mechanism_dataset.py build` is running (one was
   looping `--resume` at 01:00).
   - Set `ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_ch5a2b_test`.
   - Order: `test_ch5a2_chain_api_postgres`, `test_ch5a1_reader_postgres`, `test_w301_estate_index_postgres`,
     `test_w303_portfolio_fixture_postgres`, `test_s6_action_store_postgres`.
   - Then the heavy R1 L2, `test_out_b4_board_postgres`.
6. MD-0 `status`, then one template rebuild at the slice head (`--budget 540`).
7. Polish clone and MD-0 L3m. Use a `--work` scratch copy under the session scratchpad. Checks:
   - A/B of chips and labels: only Q3 classes.
   - Every VERIFIED summary has a non-null `source_class`.
   - List each old -> new `count_basis` with the screen text it changes.
   - Where the claims differ from `verified_resolution_count` / `priority_site_count` (info for CH-6b).
   - COH-17 = 0.
   - "on the days checked" appears only in the GAP-K7/C3/E2 windows.
   - Payload sizes.
8. Guards again. The missing-claim pair needs `node_modules`. Then the packet `.agent/review-packet-CH-5a2b.md`.

## Risks
- `count_basis` now follows the day grades (Q9). A CHECKED_DAYS grade under COMPLETE coverage flips the client's
  checked-days texts. List them in the packet.
- The claims read opportunities at the request's `known_at`; the legacy `opportunity_count` reads them at
  `scope["k"]`. If they differ, report it and do not adapt.
- `/estate/chain` filters Sites by disclosure; the Portfolio does not. COH-17 skips windows where the Site sets
  differ.
- `EstatePortfolioService.site_work_rows*` is now unused by the board. It is kept, and
  `test_qw2_many_postgres` still covers it.

## Phase 1 (`a8c748b7c`, anchors)
- `B/chain/vocabulary.py`: `Claim` (+`to_json`), `count_basis` (accepts GradeCounts or the §S.2 subset mapping),
  `count_claim(key, value, days)`, `sum_days`, `COUNT_TEXT`, `NOT_KNOWN_TEXT`, `provenance_suffix`.
- `B/chain/reader.py`: public `grade_counts_of(facts, measures)` (L2); `chain_api.py` uses it (no `_counts`, no `_Row`).
- `B/chain/threads.py`: `classify(states)` + `OPEN_CLASS/IN_HAND_CLASS/VERIFIED_CLASS`; `estate/portfolio.py`
  `thread_progress` uses it (legacy fields, own set); `VERIFIED_/ATTENTION_THREAD_STATES` alias the classes.
- L1: `portfolio.progress` `origin_selected` per Finding row at that row's cutoff via new `_same_segment` (shared with
  `_action_for`).
- R2: `VerificationService._cost_check_read` returns `source_class` (`actions/verification.py` ~1057/1077) →
  `ChainRequest.action_facts` → `ActionFacts.source_class` (`chain/read.py`) → `ActionFact.source_class`
  (`site_outcomes/board.py`, set in `mini._actions`). Wording: `board.action_result()` ("Verified{suffix}"),
  `mini.VERIFICATION_TEXT`/`VERIFIED_WITH_COST` `{suffix}`.
- Q6: `postgres_estate_read.verification` adds `source_classes` (from `details->'source'->>'source_class'`);
  `coverage._actions` row `_source_class` (private, so not on the wire); `placement.place` passes
  `provenance_suffix(action._raw._source_class)` into the `VERIFIED_WATCH_RETURN` text.
- Tests: new `backend/tests/test_ch5a2b_claims.py` (26); `test_cc_placement.py` gains the B7 text test plus the two
  Q1 guards (chip ignores consequence; `_mini_grid_money` never returns WITHHELD). Both guards were proven
  non-vacuous: a planted `cons in (WITHHELD, UNKNOWN)` failed 24, and a planted WITHHELD return failed 1; both
  were reverted. Fixtures in `test_out_b1_board`, `test_out_b2_mini`, `test_out_e4_readback`,
  `test_polish_pa2a_server_copy` now carry `source_class="REGISTERED_SIMULATION"`.
- Result: 351 passed on board, mini, placement, e4, pa2a, ch5a2 contract and refs, and w303 reduction. No Postgres
  file has been run yet.

