# Review packet MB-1a: the mill in the Kobo Assure row and the verified count

- Task: FUEL-1 MB-1a, as ruled in `.agent/build-sheet-FUEL-1.md` "MB-1-R" §1 (Q1, Q4, Q5) and §2 (main `7d49ff2d3`).
- Branch `task/FUEL-MB1-mill-on-board`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-mb1`. Main was merged in (`7d49ff2d3`). Build commit `845ece111`.
- **Status: built, with STOP S-d open plus one allowlist conflict (§Stops).** Two guards in the scoped fast tier fail because of this unit. Both need an Architect ruling. Do not merge before that.

## Outcome delivered

- `_SITE_ACTIONS` returns the decisive domain outcome and its `recorded_at`, via a LEFT JOIN LATERAL. No schema change and no `k` in the SQL.
- `site_chain.opportunity_actions` is the single selection of mill Actions, used by both the board and the claim.
- Kobo's Assure row lists the trials and the mill together, in code order. The mill entry links to the DOMAIN_VERDICT page. The headline counts the mill.
- `count.verified_results` = Finding-verified threads + `verified_actions`. A later RECURRED does not remove a verified mill.
- COH-17 L3 is re-expected. A new board-internal row, A1, is added. MILL-5 is written; it runs at E3.

## Files materially changed

| File | Change |
|---|---|
| `backend/assetops_backend/chain/adapters/postgres_chain_read.py` | Q1(a): two columns on `_SITE_ACTIONS`; comment above `_ACTION_PLANS` |
| `backend/assetops_backend/chain/site_chain.py` | Q1(b): `opportunity_actions`, signature and docstring verbatim |
| `backend/assetops_backend/chain/claims.py` | §2.2: `verified_actions`; `threads[code]["verified_actions"]`; `verified_n`; docstrings |
| `backend/assetops_backend/site_outcomes/board.py` | `OpportunityActionFact`; `SiteFacts.opportunity_actions` (last field). No line logic |
| `backend/assetops_backend/site_outcomes/mini.py` | `MiniPorts.chain_threads`, `ChainThreads`, the `opp` read, `verified`, `_assure(..., opp)`, MD-FUEL-MB1-1 comment |
| `backend/assetops_backend/site_outcomes/read.py` | `chain_threads` binding (None without a chain reader); `_verified_results` + mill |
| `tools/checks/chain_coherence.py` | L3 adds `threads.verified_actions`; new `_coh17_a1` |
| `tools/checks/test_chain_coherence.py` | L3 pass, fail and legacy; A1 pass, fail, zero, unreadable and cold-skipped |
| `tools/demo_combined_finish.py` | MILL-5 row, after F-THREADS |
| `tools/demo_combined_rows.py` | `mill_assure`, the pure MILL-5 check (deviation D3) |
| `backend/tests/test_mb1_opportunity_board.py` (new, L0) | Truth table, claims, compose, board service (24 tests) |
| `backend/tests/test_mb1_site_actions_postgres.py` (new, L2) | Real rows: SQL columns, cutoff, `opportunity_actions`, claim |
| `backend/tests/test_ch5a2_contract.py` | Both fakes carry the one-line "no DOMAIN_INTENT row" comment; Kobo `threads` gains `verified_actions` |
| `backend/tests/test_ch5a2b_claims.py`, `test_ch6b2_portfolio_cards.py` | `threads` dict gains `verified_actions`; the ch6b2 helper stubs `verified_actions` |
| `backend/tests/test_demo_combined_ex1.py` | The 3 verified-count headlines are computed with `mini.plural` |
| `backend/tests/test_demo_combined_finish_rows.py` | MILL-5 L0 self-test, beside MILL-3b |
| `backend/tests/fixtures/ch5a2_chain_contract/estate_week_2026-10-25.json` | Regenerated (D2) |

## Mock deviations

| ID | Where | Deviation |
|---|---|---|
| MD-FUEL-MB1-1 | `mini.py` `_assure` header comment | v69 lists verified Actions under Assure "Verified results", each opening its Action. The mill has no Action page (v70 D1), so its entry opens the verdict page (DOMAIN_VERDICT), as the chain wire already does (DD1b2-R6 O1). |

## Acceptance (MB-1-R §2)

- **Q1(a) SQL: met.**
  - L2 test: the mill row has `outcome == "VERIFIED"` and `outcome_recorded_at` equal to the stored row.
  - MINI_TRIAL rows carry NULL in both columns.
- **Q1(b) `opportunity_actions`: met.** The L0 truth table covers:
  - MINI_TRIAL ignored;
  - a Finding-origin intent ignored;
  - `accepted_at == hi` excluded;
  - `accepted_at` after the cutoff excluded;
  - no opportunity occurrence in the window excluded;
  - an outcome recorded after the cutoff reads None;
  - cutoff None sees the outcome;
  - a row without the new keys reads None;
  - the ref is DOMAIN_VERDICT;
  - items are in code order.
- **Q1(c) port and binding: met.**
  - `chain_threads` returns `ChainThreads(rows, k, policy)`.
  - The policy comes from a local `thread_lifecycle_policy` import, as ruled. **This import is S-d, see Stops.**
- **§2.2 claims: met.** These L0 cases pass:
  - Finding + mill = 2 (`verified_actions` 1);
  - INEFFECTIVE = 1;
  - a mill on a thread already counted is counted once;
  - recurred after verified = still 2;
  - `open_threads` unchanged;
  - a failed read gives NOT_KNOWN.
  - L2 on real rows: `verified_actions == 1`.
- **§2.3 Assure row: met.** These compose and board-service cases pass:
  - S+0 shape: headline `f"{2} verified results"`, from `plural`;
  - entries in code order;
  - the mill entry's `link_ref` is DOMAIN_VERDICT;
  - outcome None reads "… not yet verified" with the Pending chip;
  - INEFFECTIVE and INCONCLUSIVE use their texts;
  - `chain_threads` raising gives PARTIAL, `chain_threads` in `failed`, and no mill;
  - the default port leaves the body byte-equal;
  - `read.py` `_verified_results` equals the headline number through `SiteOutcomeBoardService.board`.
- **R4: met.**
  - Kobo Grow, Optimize and Protect rows are byte-equal with and without the mill (L0).
  - Cold and EV are byte-equal (below).
- **§2.4 COH: met.**
  - L3 and A1 are implemented, each with a must-fail case.
  - Two small additions:
    - A1 skips a stored board body that has no Assure row (D4);
    - A1 excludes the `NO_VERIFIED` entry (D5).
- **§2.5 MILL-5: written.** It runs at E3 and has an L0 self-test with pass and must-fail bodies.

## Measurements

- **M1:** no database carries the mill story. `assetops_mechanism_test` has 0 `domain_action` rows. M1 is proved on L0 and L2 fixtures per MB-1-R M1. E3 confirms through MILL-5 and COH L2/L3/A1.
- **L2, real rows:**
  - one VERIFIED `verification_outcome` for the mill;
  - `site_threads` returns it with its stored `recorded_at`;
  - `opportunity_actions` with cutoff = `recorded_at − 1 s` gives outcome None;
  - over `[episode_start, accepted_at + 1 s)` it gives exactly 1 item (DOMAIN_VERDICT);
  - `estate_count_claims` gives `verified_actions` 1 and the claim = verified + 1.
- **What the board shows for the mill (L0 compose, Kobo S+0 shape):**
  - Assure headline "2 verified results";
  - entries "ACT-002 verified" (mill → DOMAIN_VERDICT) and "ACT-048 verified on example data" (trial → ACTION), in code order;
  - with a cutoff before the verdict, "ACT-002 not yet verified" with the Pending chip.
- **Cold and EV unchanged:**
  - `test_ch5a1_board_contract.py` goldens `cold_2026-10-31` and `ev_2026-10-27` pass unchanged (no golden file touched);
  - `test_out_b3_cold_ev.py` passes unchanged;
  - `git diff 7d49ff2d3 -- backend/assetops_backend/site_outcomes/cold.py ev.py` is empty.
  - The only Cold/EV wire change is the additive `sites[].threads.verified_actions: 0` on `/api/estate/chain`, as ruled.

## Checks run

- **L0 targeted:** 13 files, **299 passed**. Files: `test_mb1_opportunity_board`, `test_out_b2_mini`, `test_out_b3_cold_ev`, `test_ch6b2_portfolio_cards`, `test_ch5a2b_claims`, `test_ch5a2_contract`, `test_ch5a1_board_contract`, `test_ch6_contract`, `test_demo_combined_ex1`, `test_dd1b2b_action_ref`, `test_demo_combined_finish_rows`, `test_ch9b3_mill_verdict`, `test_ch4_opportunities`.
- **`tools/checks/test_chain_coherence.py`:** 152 passed.
- **L2 on `assetops_mb1_test`:** `test_mb1_site_actions_postgres.py` 1 passed in 51 s.
- **Adjacent L2:** `test_ch5a1_reader_postgres.py` and `test_ch9b2_midday_plan_postgres.py` gave 12 passed and 2 not passed. Neither is caused by MB-1a:
  - `test_ch9b2::test_0052_round_trip_and_refusal` expects alembic head 0052; main is at 0053 since A1 merged.
  - `test_ch5a1_mechanism_postgres` errors at setup with `TEMPLATE_STALE` (the mechanism template needs a rebuild, which is not ruled).
- **Guards (`tools/check-all.ps1`):** 15 of 17 PASS.
  - PASS includes Architecture (A), Agent workflow (W), Navigation (N), Mock deviation labels and client vocabulary (V/M), chain coherence, and the frontend hard-wiring ratchet (no rise: api 12, href 24, lit 70, cmp 51, code 3).
  - FAIL: Missing-claim orphan scan and its fixtures. Both are `MODULE_NOT_FOUND` because `frontend/node_modules` is absent in this worktree. The frontend is untouched and `npm ci` was not run (coordinator rule).
- **Fast tier, scoped:** `-m "not slow"` over the 48 non-Postgres backend test files that import `site_outcomes`, `chain.claims` or `site_chain`. **749 passed, 10 failed:**
  - 8 × `test_ch9b1_origin_readers.py`: `chain/site_chain.py: 8 origin references, allowlist 4` (Stops, item 2);
  - 1 × `test_out_b4_imports.py`: `{'read.py': ['assetops_backend.chain.composition', 'assetops_backend.chain.composition.thread_lifecycle_policy']}` (S-d);
  - 1 × `test_out_d2_objectives.py::test_policy_is_v2`: expects `outcome-status/3`, but code has `/4` since CH-6a3. This is pre-existing and unrelated.
- **Not run:** full suite, prepare, baseline build, Docker fast tier.

## Stops

1. **S-d.** The dependency-direction guard `test_out_b4_imports.py` (OUT-B4 §B.3: only `site_outcomes/composition.py` may import another package's `composition`) rejects the ruled local import in `site_outcomes/read.py`:
   - Message: `{'read.py': ['assetops_backend.chain.composition', 'assetops_backend.chain.composition.thread_lifecycle_policy']}`.
   - Architecture check A itself passes.
   - The import is left as ruled; it is not designed around.
   - The policy is unused in MB-1a (MB-1b reads it).
   - One option for the Architect: `site_outcomes/composition.py` injects `thread_lifecycle_policy` into `BoardServices`.
2. **Origin-reader allowlist.** `test_ch9b1_origin_readers.py` caps `chain/site_chain.py` at 4 `origin_*_id` tokens. The ruled `opportunity_actions` brings it to 8: the verbatim docstring, the filter, and the item key and value. Raising the cap means editing a guard file that is not in the approved list, so it is not done. It needs a ruling: cap 8, class "both" unchanged.

## Known deviations

- **D1.** `opportunity_actions` also returns `outcome_recorded_at` None when the outcome is not yet known at the cutoff, so a later time does not leak.
- **D2.** The `estate_week_2026-10-25` golden is regenerated (`ASSETOPS_REGEN_CH5A2_GOLDENS=1`).
  - The diff is `verified_actions: 0` on each Site, plus an `OPTIMIZE_COST` card.
  - The card is pre-existing drift from CH-5d1, which added the card but did not regenerate this golden; its last update is CH-6b3 R3. Please confirm.
- **D3.** The MILL-5 assertions live in `tools/demo_combined_rows.py` `mill_assure`, so the L0 self-test can sit beside MILL-3b (`test_demo_combined_finish_rows.py`), as MILL-3b's own logic does. That file is not in §2.1's list.
- **D4.** A1 counts a mini board body with no Assure row as skipped, not judged. The stored `clean_full` fixtures carry only a Grow row.
- **D5.** A1 also excludes the `NO_VERIFIED` entry ("No verified result yet"), because the ruled pattern `\S+ verified\b.*` matches it. Without this, A1 would fire on every board with no verified result.
- **D6.** The §2.5 item-4 check is done twice: the same expression on the composed facts, and the real `read.py` path through `SiteOutcomeBoardService.board`, using a `test_ch5a1_board_contract.Port` subclass that carries the mill row.

## Residual risk

- The `test_ch5a1_board_contract` fixture Port has no `site_threads`, so its Kobo board now also records `chain_threads` as a failed read. Its goldens were PARTIAL already, so this is invisible there.
- No database run covers the full story; E3 (MILL-5, COH L2/L3/A1) is the first whole-story proof.

## Review focus

- S-d and the allowlist ruling.
- The D2 golden regen.
- A1's D4 and D5.
- User review: not required for MB-1a (no new client literal). The DS-1 narration of S-8/S+0 follows MB-1-R Q4.

## DB

- `assetops_mb1_test` was created empty and is still present. No `_pt*` run databases remain. Drop it after the merge, as ruled.
