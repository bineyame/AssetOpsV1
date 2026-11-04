# CH-5a2a phase 3 handoff: PARTIAL (stopped near the context limit)

Branch `task/CH-5a2-chain-endpoints`, worktree `AssetOpsV1-ch5a2`. B = `backend/assetops_backend`, F = `frontend/src`.
Read the phase-2 handoff for environment notes (env file, run pytest from `backend/`).

## Landed this session
- **`eb2378398` R7 (owner-approved, verbatim: "fix the summary now as recommended") + R8.**
  - `B/chain/read.py` `window_day(lo, hi, tz)` replaces `summary_day`. The rules are 1 (an exact Site-local day pair
    gives that date), 2 (a UTC-midnight one-day pair gives the picked date) and 3 (otherwise, the date of `to − 1 µs`
    in the frame where `to` is a midnight).
  - It is used by `outcome_api._mini_day_params`, by the board thread day (`site_outcomes/read.py` `board()`, which
    replaces `_last_local_day`, now deleted), and by both summary uses (`_prefetch` `estate_days`, `_summary` mini
    `b_day`). COH-7a `_coh7a_window` imports it.
  - Tests:
    - `test_out_b4_read.py`: one test per rule, plus `test_31_oct_summary_card_is_the_31_oct_kobo_board`;
    - `test_ch5a1_reader.py`;
    - the COH-7a self-test gains the old card day as a failing case;
    - in `test_out_w2_summary_window.py::test_mini_site_unchanged`, 7 Oct becomes 6 Oct. This is the fixed defect;
      record it in the packet.
  - **Behaviour change to note in the packet.** Cold/EV board thread days also follow rule 3: a UTC-midnight `to` is
    now read in UTC, where before it was read in Site-local time.
  - R8 deletes `BoardServices.finding_index`, `parse_finding_index` and `covering_days`, together with their wiring
    (`main.py`, `composition.py`) and the `covering_days` unit test.
- **`c6212571f` B8/R6.**
  - `tools/checks/check_chain_structure.py` implements rules (a) and (b), and has `--list`.
  - The baseline `tools/checks/fixtures/chain_structure_baseline.json` has 7 entries, all owned by CH-6:
    - `_days_block` (call and def);
    - `_productive_month` (call and def);
    - `_action_for`, `linked_actions` and `latest_window` (defs).

    Rule (a) has 0 violations today.
  - `tools/checks/test_chain_structure.py`: 11 pass.
  - `tools/checks/chain-structure.ps1` is registered in `check-architecture.ps1`.
  - **Proved non-vacuous.** A planted `estate/planted_probe.py` calling `_days_block` made check-architecture fail
    (exit 1, "calls a replaced day/window function"). The probe was then removed.
- **`9a6101c14` Guard A fix (a deviation to record).**
  - Phase 1 left `sites/{OutcomeBoard,EarlyWarnings,outcomeBoardClient}` importing `../shell/operatorSiteRoutes`, so
    site-substrate rule 8 failed.
  - The Ref types (and `FINDING_CHILD_VIEWS`) moved to `F/sites/chainRef.ts`; the shell re-exports them.
  - `routeFor`/`linkFor` stay the one builder in the shell, and reach Site components through `RefLinkProvider`
    (`App.tsx` wraps `<Routes>`). `useLinkFor()` throws outside a provider.
  - Tests use `F/test/refLinks.tsx` `LinkedMemoryRouter`.
  - check-architecture now passes.
- **`77fa4cb80`.**
  - `EstatePortfolio.tsx:504` reads `r.origin_selected ?? r.origin_revision_selected`, and the vitest gains rows
    act-3 and act-4.
  - `estatePortfolio`/`estateRoots` tests use `LinkedMemoryRouter`.

## Tests run this session
- Unit, the 68-file set (`grep -lE "site_outcomes|outcomes\.warnings|estate\.|chain\.|chain import|finding_index|chain_coherence|outcome_api" tests/*.py | grep -v postgres`)
  plus `tools/checks/test_chain_coherence.py`: 1158 passed. The 2 fails/errors were fixed and their files rerun: 25
  passed.
- `test_chain_structure.py`: 11 passed.
- Postgres `test_out_b4_board_postgres.py` + `test_out_c4_ev_warnings_postgres.py`: 6 passed (200 s).
- `tsc`: clean.
- vitest:
  - `src/estate src/shell src/work src/sites`: 136 files, all passing after the router alias (3510 tests before the
    2 fixes);
  - `ui/overflowContainment`, `ui/sharedVisualVocabulary`: 31 passed.

  `vitest related` errors on a `.py` import (raw source), so list the files explicitly.
- Guard A (check-architecture): passed.

## Resume here (in order)
1. **Phase 3 endpoints.** `B/chain_api.py` `build_chain_router(...)` with the 3 routes per sheet §B1, counts null
   (R3 → CH-5a2b), each inside `perf.route`.
   - Reuse the board route's registry, access and day parsing (`outcome_api.py:84-150`, `_mini_day_params` +
     `selected_day`, `MAX_WINDOW`).
   - Wire it in `main.py` beside `build_outcome_router` (about line 625).
   - Then the L1 goldens (`tests/test_ch5a2_contract.py`) and L2 (`tests/test_ch5a2_chain_api_postgres.py`):
     refusals (>31 d, a bad `known_at`, another Site's thread → 404 `THREAD_NOT_FOUND`) and ledger max 1.
2. **Rerun the scoped Postgres set** (phase-2 edits are still unchecked there), 1–2 files per call:
   - `test_w301_estate_golden_postgres`, `test_w301_estate_index_postgres`, `test_w403_opportunity_links_postgres`;
   - `test_ch4_opportunity_postgres`, `test_w303_portfolio_fixture_postgres`, `test_s6_action_store_postgres`;
   - `test_idx_gaps_postgres`.
3. **L3 polish clone.**
   - Run create → migrate → backfill → settle → collect (`--work` = the scratchpad `polish_work`) → check → drop.
   - Targets: COH-1/5/8 = 0.
   - **COH-7a:** the 8 remaining entries are all cold/EV event windows or `window_basis` mixing (owner CH-6), so R7
     is expected to resolve none of them. Confirm this, and delete any entry that does resolve.
   - Record the payload sizes.
4. **MD-0.**
   - `status` gives `usable: false`, so rebuild the template with `--budget 540`, in parts.
   - Then derive → collect → `check --threads` against `expected-mechanism.json`. The target is 0 unexpected.
   - Record the payload sizes.
5. **Guards** W, N, V, M, L, D (A already passes).
6. **The packet `.agent/review-packet-CH-5a2.md`.** It covers:
   - D1–D9 per the phase-2 handoff;
   - D10: the substrate fix above;
   - D11: the cold/EV rule-3 day change;
   - the frozen-dict-Refs risk;
   - the owner's Q7 words.
7. **CO-6 finish check: not run.** The only demo DBs are `assetops_demo3_full_test` (forbidden) and
   `assetops_demo3_fixmainone_test`. The latter was built before CH-5a1, so its schema would need migrating, which
   is a write. Record this in the packet.
8. Drop `assetops_ch5a2_test` at the end, unless the packet needs it.
