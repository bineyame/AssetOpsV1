# Review: DIESEL-K6c (DIESEL-1-R3u U2, U3 and U6)

**Reviewer:** a fresh Claude reviewer who did not author this work.
**Branch:** `task/DIESEL-K6c-assure-fuel-count`.
**Diff:** `main...HEAD`, base 886341aff. The build is 5a7192741 and the packet is d4dda0393.
**Reviewed with:** the K9 fix round, in one context (R3u cut 4).

## Verdict: FIX

The product change is correct and matches R3u exactly. One Medium finding is in the new test file only: it does not run under the repo's documented focused-test wrapper. Fixing it is a one-line test change. The product code needs no change.

## Findings

### M1 (Medium). `test_k6c_assure_fuel_count.py` imports `checks.chain_coherence` without putting `tools` on `sys.path`

**Where:** `backend/tests/test_k6c_assure_fuel_count.py:65`, in `_a1`: `from checks.chain_coherence import _coh17_a1`.

**What happens:**
- `tools\run-host-tests.ps1:80-81` sets the PYTHONPATH to `backend;contracts;simulator;gateway;host;field`. The Docker suite does the same (`docker-compose.test.yml:48`). Neither adds `tools`.
- The file does not insert `tools` itself. Other backend tests that use tools do insert it at module level, for example `test_ch5c2_clock_guard.py:23` and `test_demo_combined_finish_rows.py:12`.

**Failure I observed:** with the wrapper's PYTHONPATH, `pytest backend/tests/test_k6c_assure_fuel_count.py` gave 5 failed and 3 passed. Each failure is `ModuleNotFoundError: No module named 'checks'`, in tests 1, 2 (three cases) and 3.
- It passes in the packet's run only because the brief's PYTHONPATH includes `tools`.
- In a full suite it passes only because an earlier-collected module inserts `tools` first. That is fragile ordering.

**Fix:** add `sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))` at module top, as the sibling tests do. Then re-run the file under the wrapper-style PYTHONPATH.

### L1 (Low). The `_verified_results` comment is now stale

**Where:** `backend/assetops_backend/site_outcomes/read.py:519-520`.

The comment still says `_verified_results` is "the estate Assure card's verified count". After U3, the summary no longer sums it, and no production code reads it: the route strips it and the summary ignores it. R3u asked for the fuel term, so keeping the field is right.

**Fix (optional):** change the comment to say it mirrors the board's Assure headline number and no longer feeds the summary.

## Item-by-item against R3u

| R3u item | Result |
|---|---|
| U2 `mini.py` headline count gains `+ sum(1 for f in fuel if f.outcome == "VERIFIED")` | Matches. See `mini.py:572-574`. |
| U2 `read.py` `_verified_results` gains the term over `comp.facts.fuel_verdicts` | Matches. See `read.py:521-524`. Cold and EV facts default `fuel_verdicts` to `()`. |
| U3 `verified_result_count = None if counted is None else counted.claims[VERIFIED_RESULTS].value` | Matches. See `read.py:690`. `VERIFIED_RESULTS` was already imported at `:30`. `Claim.value` is an attribute: `vocabulary.py:124-126`. |
| U3 board-sum removed, `verified_read` kept for `verified_sites_unread` | Matches. |
| U6 five modules in sorted order | Matches the R3u table: `actions.fuel_verification`, `actions.verification_families`, `financials.assumptions`, `financials.composition`, `financials.fuel_cost_v2`. |
| Tests 1-7 | All present: test_1 to test_5, the extended `test_mb1_opportunity_board.py`, and `test_out_b4_read.py:255-256`. **M1** applies to tests 1-3. |

## Question 3: can the fuel verdict be counted twice?

No.
- **`facts.actions`.** It comes from the mini Action index (`mini.py:468`, `:482`, `_actions` at `:875`). That index is `ActionIndexService(actions.store)` (`main.py:578`). The store reads the `action` table, `SELECT ... FROM action` (`postgres_action_store.py:222`, `:231`). A FUEL_BALANCE Action is a `domain_action` row (migration `0057_fuel_verification.py:71`). Action codes are unique across the two tables (`postgres_action_store.py:303`). So a fuel Action cannot appear in the index.
- **`facts.opportunity_actions`.** `site_chain.opportunity_actions` requires `origin_opportunity_id` to be non-null (`site_chain.py:170`). The constraint `domain_action_mini_origin` (`0051:78-79`) pins `(domain = 'MINI') = (origin_opportunity_id IS NOT NULL)`, and 0057 leaves it in place. So every FUEL_BALANCE row has a null opportunity origin, and it is listed only by `fuel_verdict_actions` (`site_chain.py:198`).
- **Test coverage.** test_4 checks this at the fake-port level. The real-port exclusion above rests on the table split and the DB constraint, both of which I verified in code.

## Question 4: consumers of `verified_result_count` without a chain reader

Grep of the repo, excluding `.agent`:
- **Frontend.** `estateClient.ts:660` only types the field, and `portfolioFixtures.ts:538` is a fixture. Nothing renders it.
- **`estate` and the portfolio.** No backend reader outside `read.py`.
- **Goldens.** No golden or fixture holds the field. The `ch5a1_board_contract` fixtures hold `_verified_results: 0`, which is unchanged.
- **`chain_coherence` L2.** At `:1391-1393` it compares only when both values are non-None, so a None value skips L2 and does not fail it.
- **Docs.** `Docs/demo-sprint/implementation-logic-...html:749` says `PortfolioOutcomes.tsx` reads the field. That is stale prose; no such reader exists in `frontend/src`. This is not a code consumer.

Nothing breaks.

## Question 5: are the five modules legitimate?

Yes. The list is the clock-guard scan set (`test_ch5c2_clock_guard.py:1-13`). Listing a module adds it to the static wall-clock scan, which tightens the guard. It does not let stored composers run anything new.
- All five match the R3u table.
- Grep of the five files finds no `datetime.now`, `utcnow`, `date.today`, `time.time(`, `now()`, `clock_timestamp` or `current_timestamp`.
- `test_ch5c2_clock_guard.py` passes with them listed, and no allowlist entry was added.
- The packet's mutation M4 (a planted `datetime.now` in `fuel_cost_v2`) shows the new entry is actually scanned. I did not re-run M4.
- Whether the observed set equals the list exactly is proved later, by the guard `--modules-out` run in §9u.2 step 3.

## Question 6: are Kobo, Cold and EV unchanged?

- Cold and EV have no fuel verdicts.
- Kobo has no FUEL_BALANCE Action, so its board headline and `_verified_results` are unchanged.
- The only estate-wide change is the summary `verified_result_count`, which is now the claim value, as R3u allows. It has no on-screen reader.
- Adjacent outputs are unchanged. These suites pass: cold/EV, board contract, mini, portfolio cards, estate chain, and route.

## Question 7: K9 → K10 → K6c merge order

`git merge-tree --write-tree` predicts no textual conflict for any pair:
- K10 + K6c gives tree 19354fbc;
- K9 + K6c gives tree 6657bc9e;
- K9 + K10 gives tree 1e964115.

K10's `mini.py` hunks are the import, the copy, `finding_gap_line`, `decl`/`_productive_sales`, the Grow headline at `:605-609`, and `none_declared`. They are separated from K6c's `:572-574` by enough context to auto-merge. So R3u's expected conflict will probably not occur. If the rebase does conflict, it is textual only.

There is no semantic clash:
- `verified` is used only for the Assure headline text (`mini.py:581-582`).
- K10 settles the row states through `base`/MG-4/MG-5 and does not read `verified`.
- No K10 test asserts `NO_VERIFIED`, `verified_result_count` or `_verified_results`.

With both merged, Kisiwa's Assure row may settle while showing "1 verified result". That is consistent.

## Checks run

All were pure test runs using the plan2 venv, with an absolute PYTHONPATH under the k6c worktree and no database.
- With the brief's PYTHONPATH, `test_k6c_assure_fuel_count.py` alone: **8 passed**.
- `test_mb1_opportunity_board`, `test_out_b4_read`, `test_ch5c2_clock_guard`, `test_out_b3_cold_ev`, `test_ch5a1_board_contract`, `test_out_b2_mini`, `test_ch6b2_portfolio_cards`, `test_ch6b_estate_chain` and `test_out_b4_route`: **200 passed**.
- With the wrapper-style PYTHONPATH (no `tools`), `test_k6c_assure_fuel_count.py`: **5 failed, 3 passed**. This is finding M1.

Mutations used a scratch copy of `assetops_backend` placed first on the PYTHONPATH. No repo file was edited, and both worktrees were clean afterwards. The baseline was 47 passed.

| Mutation | Tests that failed |
|---|---|
| Fuel term dropped in `mini.py` | test_1, test_3, test_4, and the mb1 fuel board test |
| Fuel term dropped in `read.py` only | the mb1 fuel board test |
| Summary restored to the board sum | both test_5 tests, and `test_walk1_summary_verified_count_and_headline_money` |
| Fuel verdict counted whatever its outcome | the three test_2 parameter cases |

## Not verified

- The served Kisiwa board and the F-COH A1/L2 rows. These belong to the clone check in §9u.2 step 3.
- The guard `--modules-out` equality.
- The full backend suite.

## Rebase note for the coordinator

After the rebase onto K9 and K10, confirm that `git diff <new-base>...HEAD` equals this reviewed diff, with M1's fix added. If it does, no re-run is needed, per §9u.2.
