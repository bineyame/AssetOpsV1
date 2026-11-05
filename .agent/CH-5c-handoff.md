# CH-5c handoff: partial; the pre-flight is done and the build has not started

I stopped at about 105k context, as the brief requires, after the CH5c-R4 rulings arrived. A fresh implementer
should build from sheet §8 (`AssetOpsV1-plan2/.agent/build-sheet-CH-5c.md`, lines 97+). Read §8 in full first. I
have not read past its headings.

## State
- Worktree: `C:\Users\assef\Bineyame\AssetOpsV1-ch5c`.
- Branch: `task/CH-5c-perf`, from main `fd03ae6b0`.
- Commit `fd3348fd7`: `.agent/CH-5c-preflight.md`, plus the probe's `findings_week` URL.
- No production code has been written yet.
- **The clone `assetops_chainclone_ch5c_test` still exists.** It was created with `--migrate`, backfilled and
  settled. It is the A side and is read-only from here on. Drop it at the end:
  `tools/chain_clone.py drop ch5c`. That also removes the 2 `var/` files that settle created.
- The scratch env lives in `...\scratchpad\ch5c\env.sh`. It defines `W`, `PY`, `PYTHONPATH`, `S`/`SW` and
  `CLONE`, and has the work dir `ch5c\work`.
- The scratch folder also holds these tools:
  - `survey.py`: an SQL table listener and `_window` argument log over a full collect;
  - `diff.py`: a JSON path diff of two bundles;
  - `prof.py`: a cProfile of one warm request;
  - the A bundles `bA` and `bB`, which are 2 collects on main code. They are the A side for the A/B, and `bA`
    contains `_survey.json`, the tables read per route.
- The baseline timings are in the table in pre-flight P1.

## Anchors (all under `backend/assetops_backend/` unless the path says otherwise)
- **`_window` path** (`analytics/adapters/postgres_assessment_store.py`):
  - `_window` 870 (the memo key; `_MEMO_NOW` 231);
  - `_window_read` 881-927, with `_EVIDENCE` 118, `_configuration` 292-334 and `_attestations` 170;
  - `select_dispatch_days_on` 929-957 (the per-day loop: the prefetch goes here), `_dispatch_day_on` 963;
  - `_snapshot` 841 (REPEATABLE READ), `_connect_engine` 243 (the one engine: Q6 read engine);
  - `claim_limit_snapshot_on` 1066.
- **Read scope:** `read_scope.py` (`memo` 135, `scope` 110). `perf.route` is at `perf.py:128`.
- **Routes:**
  - `outcome_api.py:188` (board), `outcome_api.py:209` (summary);
  - `estate_portfolio_api.py:40-66`, which returns `jsonable_encoder(body)`;
  - `estate_api.py:46` (`serve`, which has no `perf.route`: Q7) and `estate_api.py:67` (findings);
  - `chain_api.py:104,137,170`.
- **Estate snapshot read instants:** `estate/adapters/postgres_estate_read.py:92` and
  `postgres_evidence_money_read.py:38`. Under W3, the watermark is the first statement of these snapshots and of
  the outcome-board and summary composition.
- **Tick:** `scheduling/tick.py`:
  - `TickLimits` 60-117 (`site_lease_seconds` 113);
  - `chain_threads` 470;
  - `chain_snapshots` 503-513, then `release_site`;
  - the Site loop is around 361;
  - the stage functions are in `scheduling/stages.py`, `STAGES` 444.
- **Outbox producers:** `backend/migrations/versions/0044_chain_events.py:34-80` (PRODUCERS), and the
  `recompute_job` update trigger at 143. Head is `0044_chain_events`; the new migration is
  `0047_chain_response` (Q2).
- **Portfolio trim (Q9 ruling: a count plus the `/estate/portfolio/scope-ids` sub-route):** the frontend is
  `frontend/src/estate/EstatePortfolio.tsx:558-590` (`selected_revision_ids` renders at 562-571;
  `source_provenance` is only null-checked at 586), and the types are in `estateClient.ts:498-510`.
- **Probe:** `tools/chain_perf_probe.py` (URLS; R9 adds 3 modes).
- **Coherence:** `tools/checks/chain_coherence.py` (`collect` 1225; the URL set is in `Collector.estate`
  165-185).

## Next
1. Read §8.1-8.3.
2. u1: build the batching with the R2/R3 parity tests (L0 `test_ch5c_batch.py`, L2 `test_ch5c_batch_postgres.py`).
3. u2: build these, with the flip and stored-equals-fresh tests:
   - the migration (`chain_response` plus `chain_input_change` and its W2 triggers);
   - `chain/watermark.py` (W1-W4);
   - `chain/response_store.py`;
   - the route wiring;
   - the prebuild stage and `config/chain/prebuilt-routes-v1.json`.
4. u3: the scope-ids sub-route and the count.
5. Then the polish-clone settle, the A/B against `bA`, COH, the probe, the guards, and the packet.

## Risks
- The pre-build is about 45-60 s uncached against the tick's ≤50% rule (Q8).
- The W2 triggers cover about 40 tables (pre-flight P5). Measure the watermark cost against the 50 ms stop.
- Another session was running pytest during the baseline, so the timings are noisy.
