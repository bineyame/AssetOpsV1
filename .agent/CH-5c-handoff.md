# CH-5c handoff 2: partial. u1 is built; u2 is part-built. Resume at "Next"

I stopped at about 105k context. Branch `task/CH-5c-perf`, worktree `AssetOpsV1-ch5c`. Spec: sheet §8. The scratch
env is in `...\scratchpad\ch5c\env.sh`; the A bundles are `bA` and `bB`.

## Commits
- `b38bcaf45` u1: the batched dispatch-day prefetch (R1), the R3 key normalisation and the R2/R3 parity tests.
- `e59cdf35b` u2 (part): migration 0047, `chain/watermark.py`, the W5 reset, and the trigger and commit-order tests.

## What landed (under `backend/assetops_backend/`)
- `analytics/adapters/postgres_assessment_store.py`:
  - `_window(prefetched=)`, with `_window_key` (R3: a cutoff at or after the bound snapshot instant becomes live;
    `all_jobs` reads are excluded);
  - `_window_read(prefetched=)`, which splits by `_ev_overlaps` and the jobs predicate;
  - `_prefetch_days`, which reads 5 statements per range;
  - `select_dispatch_days_on`, which skips the prefetch when every key is memoised;
  - the test-only `_select_dispatch_days_each`, **deleted at merge (R2)**.

  `_configuration` and `_run_detail` stay per day (P2 default).
- `read_scope.py`: `memoised`, `snapshot(c, read_at)` and `at_or_after_snapshot`. The scope is bound in the
  `read()` of `estate/adapters/postgres_estate_read.py` and `postgres_evidence_money_read.py`, with read_at =
  `SELECT now()`.
- **Tests:**
  - `tests/test_ch5c_batch_postgres.py` passes;
  - the L2m clone parity (`ASSETOPS_CH5C_CLONE_URL`): **279 day dicts equal**;
  - `test_w301_w1_snapshot_helpers_postgres.py`: 4 passed.
- **Migration** `0047_chain_response.py`, `down_revision` 0044:
  - `chain_input_change` (append-only) and `chain_response`;
  - INS, UPD, DEL and TRUNC statement triggers on the 82 frozen `INPUT_TABLES`. These equal
    `config/chain/watermark-inputs-v1.json` minus the view `chain_action`, and come from the listener survey.

  **Known Deviation of W1:** every input, including the append-only ones, is W2-triggered. The watermark is then
  one count, `cic:<n>`. These tables write NULL rows and over-invalidate:
  - `event_consumption` (every consume invalidates every route);
  - `site`;
  - `tenant`;
  - a TRUNCATE on any input.
- `chain/watermark.py`: `read_watermark` and `code_version()`. The code version is a sha of the backend `.py`
  files, the migrations and `config/**`. The Q5 env-settings survey is **not done**.
- `tests/pg_harness.py`: `RESPONSE_TABLES`, which are always emptied together (W5).
- `tests/test_ch5c_watermark_postgres.py`, 5 tests, all pass:
  - declared list = migration list;
  - the four triggers on every input, from `pg_trigger`;
  - another Site does not flip, and a NULL row does;
  - T1/T2 out of order;
  - the W5 reset.

## Next
1. **Flip tests on real input tables:** INSERT, UPDATE and DELETE on seeded rows (the F06 `CaseRunner`), plus a
   late outbox row with an earlier `recorded_at`. Prove the trigger guard is non-vacuous by dropping a trigger in
   a rolled-back transaction.
2. **`chain/response_store.py`:**
   - `request_key`: canonical, with the route, the sorted Sites, the window, `known_at` normalised as in R3, the
     params, the cursor and `selection_token`;
   - lookup;
   - insert on the write engine in its own transaction, `ON CONFLICT DO NOTHING`, with a failure logged;
   - prune to 3, from the pre-build only;
   - `etag`.
3. **Wiring**, inside `perf.route`:
   - `outcome_api.py:188/209`;
   - `estate_portfolio_api.py:40-66`;
   - `estate_api.py:67` (add `perf.route`);
   - `chain_api.py`.

   **W3 caveat.** The board and summary compose over several transactions (`site_outcomes/read.py:390,460`).
   Proposal: read the watermark and the hit lookup in one RR transaction *before* any compose read. That is sound:
   the counts are monotone and every compose read starts later. This needs the Architect's ruling, because the
   literal W3 says High.
4. **Pre-build** after the tick's Site loop (`scheduling/tick.py` ~361), using `config/chain/prebuilt-routes-v1.json`.
   It holds no lease, prunes the store, and its seconds are reported against the ≤50% rule.
5. **The W6 listener guard**, with views resolved through `pg_depend`/`pg_rewrite` and a planted untracked table
   to prove it fails. Then the stored-equals-fresh tests (Q4 fields only).
6. **u3:** `selected_revision_count`, plus the stored `GET /estate/portfolio/scope-ids`, loaded on disclosure open
   (`EstatePortfolio.tsx:558-590`, `estateClient.ts:498-510`). Trim `source_provenance` to the fields that are
   consumed.
7. **R4** (`prepare_threshold`) is not done: measure it per Q6.
8. **L3:** the clone is still at 0044 (the A side, `bA` is saved). Upgrade it, settle, run the A/B, COH, the probe
   (3 modes), the size check and the guards, write the packet, then `tools/chain_clone.py drop ch5c`.

## Risks
- Replica-mode writes (`session_replication_role`) skip the change log. Grep `backend/assetops_backend` for them.
- The trigger write cost on settle is not measured yet, and the watermark count time is not measured on the clone
  yet (the 50 ms stop).
