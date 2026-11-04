# Review packet: CH-5a2a (chain endpoints, Refs, lens, threads)

- **Branch:** `task/CH-5a2-chain-endpoints`, worktree `AssetOpsV1-ch5a2`.
- **Base:** main `ff499d54d` (FIX-MAIN-1), merged in at `bf73f236b`.
- **Authority:** the build sheet `AssetOpsV1-plan2\.agent\build-sheet-CH-5a.md`. Part B is amended by §B13 (CH5a2-R). This packet covers the CH-5a2a cut only.
- **Status:** ready for review at `2f8b114d9`. The private DB `assetops_ch5a2_test` is dropped; no clone or L3m DB remains. The sheet sets no USER_REVIEW_REQUIRED flag, so the coordinator decides. Do not merge from here.
- **Owner decision R7 (Q7), verbatim:** "fix the summary now as recommended". It is built in `eb2378398`.

## Outcome delivered

1. **Refs and links** (B1/B2, R4, R5).
   - `chain/refs.py` holds the Ref kinds and `href_for`. `routeFor` lives in `F/shell/operatorSiteRoutes.ts`. Both read the shared fixture `route-refs.json`.
   - Every legacy linked item gains a sibling `link_ref`, and its `href` is built by `href_for(link_ref)`. The client renders only `routeFor(link_ref)`.
   - Cold/EV Finding links are screen routes with their proven window. COH-1 finds 0 `/api` links.
2. **Three `outcome-chain-1` routes** (B1).
   - The routes are `GET /api/sites/{code}/chain`, `GET /api/estate/chain` and `GET /api/sites/{code}/threads/{id}`.
   - They live in `B/chain_api.py`, with the pure builders in `B/chain/site_chain.py`. They are wired in `main.py` beside `build_outcome_router`, and each runs inside `perf.route`.
   - The counts (`counts.*`, `sites[].threads`) are null until CH-5a2b (R3). `money_total` is null.
3. **Lens from the chain** (B5). There is one lens per Finding, taken from `outcome_map`. Board FINDING issues carry `primary`.
4. **Structured `thread_lines`** (B4).
5. **`origin_selected`** (B6). It is rendered by the Portfolio.
6. **Removed joins** (B3, bullets 2 and 3). The exact-revision Action join is deleted, and there is one per-Site cutoff map.
7. **One day rule, `window_day`** (R7). It is shared by the board route, the board thread day, the summary card and COH-7a.
8. **Deleted wiring** (R8). The dead finding-index wiring is gone.
9. **Structural AST guard** (B8/R6), with a shrink-only owned baseline.

## Commits (main..HEAD, newest first)

`688bb574c` estate index tests follow B5 · `a543c4aa2` W301 manifest follows B5 · `5f007b5b4` L2 chain routes ·
`0e495772e` three routes + L1 goldens · `e38d18cb6` handoff · `77fa4cb80` Portfolio origin_selected · `9a6101c14`
guard A substrate fix · `c6212571f` B8/R6 · `eb2378398` R7+R8 · `503a7c3e2` handoff · `e2d0d277a` B4 · `3cea423fd`
B5/B3/B6 · `6d0ffacd2`, `1f8f56ecd` W301 parity · `cbf53f92b`, `cef9c6dee`, `c82f34c7d`, `1c3e3a075`, `4e7547e63`
refs phase 1/1b · `bf73f236b` merge main · `6d2d37881` pre-flight.

## Files materially changed (phase 3)

- **New:**
  - `backend/assetops_backend/chain_api.py`;
  - `backend/assetops_backend/chain/site_chain.py`;
  - `backend/tests/test_ch5a2_contract.py` and its 6 goldens in `backend/tests/fixtures/ch5a2_chain_contract/`;
  - `backend/tests/test_ch5a2_chain_api_postgres.py`.
- **Edited:**
  - `chain/read.py`: `ChainReadPort.site_threads`, `ChainRequest.threads` and `window_days`;
  - `chain/adapters/postgres_chain_read.py`: three SELECTs on one read-only connection;
  - `outcome_api.py`: `board_site`, `board_window` and `estate_sites`, factored out unchanged;
  - `main.py`;
  - `chain/composition.py`: `chain_policy_versions`, injected.
- **Test fixtures** following B5:
  - `tests/fixtures/w3/w301-estate-golden.json`;
  - `tests/test_w301_estate_index_postgres.py`.

## Acceptance (CH-5a2a cut, §B13 S1)

| Item | Status | Evidence |
|---|---|---|
| B1 refs, `href_for`/`routeFor`, shared `route-refs.json` | met | phase 1; vitest `routeRefs.test.ts` 59; pytest `test_ch5a2_refs` |
| B1 three endpoints, counts null (R3) | met | L1 22 passed, L2 6 passed |
| B1 thread of another Site → 404 `THREAD_NOT_FOUND` | met | L1 (Cold Site asking for the Kobo thread; unknown id; non-UUID); L2 (unknown id) |
| B1 refusals: >31 d, bad `known_at` | met | L1 + L2 `test_refusals` |
| Ledger max 1 per route | met | L1 (6 cases), L2 (3 routes), clone and L3m (all 8 / 6 probes `ledger_max 1`) |
| B2 / R4 `link_ref` on every legacy linked item; client renders only `routeFor(link_ref)` | met | phase 1b; `link_parity.checked` on every unit board and W301 golden |
| R5 cold/EV FINDING `link_ref` carries the row window | met | COH-1 0 on the clone |
| B3 bullets 2-3 (exact join deleted, per-Site cutoff map) | met | `3cea423fd` |
| B4 `thread_lines` | met | `e2d0d277a`; CH-5a1 board goldens additive only |
| B5 lens from chain, `primary` | met | COH-5 0 on both datasets |
| B6 `origin_selected` | met | COH-8 0 on both datasets; `EstatePortfolio.tsx:504` renders it (`77fa4cb80`) |
| B8 / R6 AST guard registered, non-vacuous | met | planted probe failed check-architecture (phase 3 handoff) |
| R7 (owner yes) | met | `eb2378398`; tests per rule; 31 Oct card = 31 Oct Kobo board |
| R8 deletions | met | `eb2378398` |
| L3: COH-1/5/8 entries removed, COH-1 0 `/api` | met | clone check below |
| L3m: 0 unexpected | met | L3m check below |
| L1 frontend renders the chain goldens in vitest with no server | **not met** | D12 |

## Tests run (localised only; no full suite, no demo prepare, no `test_demo_combined_postgres`)

**Phase 3, at `688bb574c`** (L1 rerun at `2f8b114d9`: 22 passed):
- L1 `test_ch5a2_contract.py`: 22 passed.
- L2 `test_ch5a2_chain_api_postgres.py`: 6 passed (32 s).
- The scoped unit set: 1098 passed, 0 failed (285 s). That is the 69 files matching `grep -lE "site_outcomes|outcomes\.warnings|estate\.|chain\.|chain import|finding_index|chain_coherence|outcome_api|chain_api" tests/*.py | grep -v postgres`, plus `tools/checks/test_chain_structure.py`.
- Postgres, scoped (`assetops_ch5a2_test`):
  - `test_w301_estate_golden_postgres`: 6 passed (207 s), after the manifest write;
  - `test_w301_estate_index_postgres` + `test_w403_opportunity_links_postgres`: 19 passed and 2 failed. The two failures followed B5 and were fixed (rerun 2 passed);
  - `test_ch4_opportunity_postgres` + `test_w303_portfolio_fixture_postgres`: 5 passed;
  - `test_s6_action_store_postgres` + `test_idx_gaps_postgres`: 19 passed;
  - `test_ch5a1_reader_postgres`: 7 passed.

**Earlier phases** (handoffs):
- unit 1158 passed;
- `test_chain_structure` 11 passed;
- `test_out_b4_board_postgres` + `test_out_c4_ev_warnings_postgres`: 6 passed;
- `tsc` clean;
- vitest across `src/estate src/shell src/work src/sites`: 136 files, all passing;
- `overflowContainment` / `sharedVisualVocabulary`: 31 passed.

Phase 3 changed no frontend code.

## COH results

**Polish clone `assetops_chainclone_ch5a2_test`:**
- Steps, all exit 0:
  - create + migrate: 3 s;
  - backfill a-d: 15 s (a 139, b 9, c 3, d 6);
  - settle: 72 s (tick COMPLETED);
  - collect: 85 s (56 requests, all 200, `--work` the scratch `polish_work`);
  - check against `expected-today.json`;
  - drop (the 2 `var/` files were deleted).
- COH-1 0, COH-5 0, COH-8 0, COH-2 2/2 expected, COH-7 8/8 expected, every other rule 0. 0 new, self-check 10 pass.
- **COH-7a:** R7 resolves none of the 8 entries ("0 resolved"). All 8 are still produced, so none was deleted. They are the cold/EV event windows and `window_basis` mixing, owned by CH-6.

**L3m (MD-0):**
- `status` read `usable: false`, so the template was rebuilt with `build --variant states --budget 540` in 2 parts (8 m 9 s with exit 3, then a resume of 2 m 34 s). The new template is `assetops_mechanism_tpl_7ed8e064_test`. Per the tool's keep-two-newest policy it **dropped `assetops_mechanism_tpl_457ce2a1_test`** (see residual risk).
- Then:
  - derive: 63 s;
  - `chain_clone.py settle mechanism`: 46 s;
  - collect: 40 × 200;
  - `check --threads var/mechanism/expected-threads.json --expect expected-mechanism.json`.
- **COH-0 to COH-16 all 0; 0 unexpected.** Then `drop --variant full`, and settle's 2 `var/` files were removed.

## Payload sizes (`/chain` routes, in-process TestClient, read-only)

| Dataset | Request | Bytes | ms | Contents |
|---|---|---|---|---|
| clone | site KOBO 31 Oct | 5803 | 5173 (cold) | 2 threads, 1 action |
| clone | site KOBO 1 Nov | 5372 | 2036 | 2 threads, 1 action |
| clone | site COLD (overview window) | 4737 | 1227 | 2 threads, 1 action |
| clone | site EV (overview window) | 3137 | 1394 | 1 thread, 1 action |
| clone | estate week 25 Oct-1 Nov | 3948 | 5330 | 3 Sites |
| clone | estate 4 Oct-4 Nov | 3942 | 3215 | 3 Sites |
| clone | thread KOBO / COLD | 1313 / 1862 | 39 / 45 | |
| L3m | site KOBO 31 Oct (D13) | 3468 | 5976 (cold) | 1 thread |
| L3m | site KOBO 1 Nov (D14) | 4146 | 5838 | 1 thread, 1 action |
| L3m | site KOBO 25 Oct (D7) | 1831 | 1421 | 0 threads |
| L3m | estate week 26 Oct-2 Nov / 14 days | 2955 / 2959 | 3967 / 3858 | 1 Site |
| L3m | thread KOBO | 1836 | 46 | |

- Every body is well under the 60 KB / 100 KB budgets.
- Site and estate chain times are dominated by the board composition they reuse (the CH-5a1 time budgets are missed as before). This is reported, never relaxed.

## Guards

Run through `tools/check-all.ps1` (14 guards).
- **First run at `62cca39d0`: 12 of 14 passed.**
  - Failed: A (architecture). `chain_api.py` imported `chain.adapters.file_chain_config`, and only `chain/composition.py` may import chain adapters.
  - Failed: the estate guard self-tests (3, the same cause).
  - Passed: W (agent workflow), N (navigation truthfulness), V (mock-deviation labels and vocabulary), M (missing-claim scan and fixtures), L (screen ledger), D (dependency registry), delivery and mock-gap fixtures, evidence width, chain-coherence fixtures (98), event register (12).
- **Fixed in `2f8b114d9`.** `chain.composition.chain_policy_versions` is injected into `build_chain_router` from `main.py`. The L1 goldens are unchanged (22 passed).
- **Rerun:** guard A passed. The estate guard self-tests passed 15 of 15 (1004 s, run from PowerShell as check-all runs them; a run from Git Bash fails all 15 in 40 s for environment reasons). So all 14 guards pass at `2f8b114d9`.

## Known deviations

- **D1. Query encoding.** One builder means one encoding (`%3A`). The mini renewable link and the CH-4 `links.evidence` change from a raw `:` to `%3A`, and the Kobo CH-5a1 goldens show encoding-only diffs.
- **D2. Ref fields beyond B1:**
  - `FINDING.view`;
  - `ACTION.recorded_at`;
  - `SITE.window`;
  - `EVIDENCE.window` with `from`/`to` only;
  - `ESTATE` without `query`;
  - performance capabilities as `EVIDENCE{capability}`.
- **D3.** The `test_out_b1_board` purity guard admits exactly `from assetops_backend.chain import refs`, and refs.py is pinned to stdlib.
- **D4. Cold/EV CH-5a1 golden behaviour changes:**
  - unproven fake-fixture Finding links render no link;
  - domain-intent Actions point at `/verification`.
- **D5.** The estate Actions `source` is null when `source_finding_id` is null.
- **D6.** An empty mini `selected_event` id drops `?event_id=`.
- **D7. W301 golden.** `link_parity.checked(body)` asserts every href equals `href_for(Ref)` before `normalize` strips the Refs. The manifest was byte-identical to main until B5 (see D16).
- **D8.** `origin_selected` was not rendered after phase 2. This is resolved in `77fa4cb80`: `r.origin_selected ?? r.origin_revision_selected`, with the legacy flag used only on an older body.
- **D9.** The coherence fixture bundles were edited: FINDING issues gain `primary`, and progress rows gain `origin_selected`. Two new self-tests, both non-vacuous.
- **D10. Guard A substrate fix (`9a6101c14`).**
  - The Ref types and `FINDING_CHILD_VIEWS` moved to `F/sites/chainRef.ts`, and the shell re-exports them.
  - `routeFor`/`linkFor` stay the one builder in the shell. They reach Site components through `RefLinkProvider`, and `useLinkFor()` throws outside one.
  - Tests use `LinkedMemoryRouter`.
- **D11. Cold/EV board thread day under R7 rule 3.** A UTC-midnight `to` is now read in UTC, where before it was read in Site-local time. In `test_out_w2_summary_window::test_mini_site_unchanged`, 7 Oct becomes 6 Oct: this is the fixed defect.
- **D12. L1 "frontend renders the goldens in vitest" is not built.** No client consumer of `/chain` exists in CH-5a2a; CH-5b and CH-6 read these goldens as their start.
- **D13. Finding occurrences carry `code: null`.** No Finding public code is stored. Opportunities carry `OPP-%06d`, as CH-4 does.
- **D14. `/estate/chain` days use `chain.read.window_days`.**
  - A window with both ends at UTC midnight names its UTC dates, the R7 frame rule the summary card uses: a 7-day week gives `requested` 7.
  - Any other window names the Site-local days it meets.
  - `/sites/{c}/chain` days use the board window's Site-local days, as board readiness does.
- **D15. The router signature differs from B1's `build_chain_router(reader, registry, …)`.** It is `build_chain_router(service, registry, …)` and reads `service.s.chain_reader` and `service.s.threads`, so the outcomes are the board composition's own rows.
- **D16. B5 follow-on fixtures.**
  - The W301 manifest has 14 `lens_flags` `[] → ["COST"]`, on the unpriced or withheld generator Findings. There is no other diff.
  - Two `test_w301_estate_index_postgres` tests asserted the deleted PRICED → COST rule. They now assert lens by mechanism, with the money state still in the consequence column.
- **D17. The mini `/sites/{c}/chain` takes the board's parsing (one day).** A multi-day mini window is refused exactly as the board refuses it.

## CO-6

**Not run.** No current demo DB exists:
- `assetops_demo3_full_test` is forbidden;
- `assetops_demo3_fixmainone_test` predates CH-5a1, and migrating it would be a write.

R7 is expected to make it pass (31 Oct card = 31 Oct board, unit-proven).

## Residual risk

- **Frozen dataclasses hold dict Refs.** Facts are frozen dataclasses that now carry dict Refs. Nothing hashes them today, but a `set()` of facts would raise.
- **The MD-0 template pruning dropped `assetops_mechanism_tpl_457ce2a1_test`.** That is the tool's keep-two-newest rule (CH5a1-R3 M4). If lane 2 (MD-0b) was using that fingerprint, its next `status` reads stale and it rebuilds. The template now held is `7ed8e064` (this branch), plus `c3470a30`.
- **`site_threads` reads all of a Site's threads and events per request, then filters in pure code.** That is fine at demo volume; window-bounded SQL would be needed at scale.
- **Site and estate chain latency equals the board/summary composition's** (5-6 s cold on Kobo). It is reported, not addressed (EX-3).

## User-review focus

- D14: the day-set rule of the estate chain.
- D15/D17: the router reuses the board composition.
- D16: lens by mechanism puts unpriced generator Findings under Cost.
- D12: no frontend consumer of `/chain` yet.
