# MD-0 phase 3 handoff (PARTIAL, Kobo-only scope MD0-S2: resume here)

- Branch `task/MD-0-mechanism`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-md0`. Read the phase-1 and phase-2 handoffs first. Authority: build sheet §0-§15 (`AssetOpsV1-plan2\.agent\build-sheet-MD-0.md`), with **§15 MD0-S2 (Kobo only)** as the scope.
- The third agent stopped by the context budget rule, after one measured `states` build.

## Landed (commits `eec9c0e5d` and the commit after it)

- **The fixture is now Kobo only** (`backend/conversions/mechanism-v1.json`). The Cold/EV sites, GAP-C3/E2, their threads and their day-set entries are removed, and `variants.main.removed` records why (MD0-S2).
  - Added `K-OVR-D14`, the one recurrence after the ACT-K1 apply (effective D12). It is on D14, so the D12/D13 noon days stay clean.
  - `validate` refuses any non-Kobo site.
  - L0 (`test_md0_fixture.py`) is updated: 20 passed.
- **`backend/tests/mechanism_dataset.py`:**
  - **Fixed `KoboSite` set selection.** It now takes the current `superseded_at IS NULL` set with the latest valid_from, which is roles-4 v14. Before, it took a superseded roles-3 row that tied on valid_from and recorded_at.
  - **Noon remap (`noon_planned`):** the w4 `positive` means and points, re-dated to the D12/D13 local noon hour on KOBO-001 bindings, with the backup chain omitted. KOBO-001 does not bind `residential-meter/requested-power` or `mill-meter/requested-power`. Those two are dropped and listed in `manifest.noon_dropped` (R7, for the packet). The normal rows of the channels this covers are replaced in that hour.
  - **Stepped seed:**
    - `seed_steps` / `seed_part(store, engine, day_set, steps, state, work)`, with the state resumable across processes (`KoboSite(resume=)`, `state()`);
    - `seed_database` runs every step.
  - **D11 is split at 13:00 local.** The morning is delivered and settled first, then `act_k1` runs (the s6 `applying` harness: accept at 13:00, apply at 14:00, effective D12 00:00), then the afternoon.
  - `derive` = step a, b+c, then `run_lifecycle`, kept verbatim, then `chain_snapshots` until empty, then `chain_threads`.
  - Also added: `_publish` (`publish_price`, `declare_objective`), `grades`, `late_fill` (real clock, epoch `mechanism-late-1`) and `build_work`.
- **`setup_cache.py`:**
  - The op is registered as `("mechanism_dataset","seed_database")`.
  - The fingerprint now covers `backend/conversions` and `FINGERPRINT_FILES`: `tools/demo_combined_kobo.py`, `tools/demo_story_days.py`, `tools/w402_mini_depth_cases.py`, and the s2/s4/s6 test modules the seed imports.
- **`tools/mechanism_dataset.py`** (L3m) provides `build [--day-set] [--budget 540]`, `build --resume` (exit 3 = resume) and `drop`. Its guards are a fixed name, a marker folder, and refusal of the close variant.
- **`tools/checks/chain_coherence.py`:** R8 (in-process collect reads story.json and days.json, plus `app_client`) and R9 (`check --threads`).
- **`tools/chain_clone.py`:** `settle_db` accepts `mechanism` / `mechanism_close` in settle only (P7).
- **`expected-mechanism.json`** is `[]`. The tool tests pass (88). The R8 and R9 tests were proven non-vacuous: with the change reverted, both failed; then `git checkout`.

## Measured: `states` first build via pytest (old code, before the studies fix)

- 904 s of seed (941 s wall): begin 1.0, D1 54.9, D2 44.3, D3 113.3, D4 147.1, D5 47.9, D10 146.0, D11 104.7, D12 64.2, D13 67.9, D14 54.8, studies 0.7, derive 57.4.
- 21,126 readings in 133 batches.
- Day times vary 44-147 s, with CH-5a1 and the cost probe running.
- **That is over the 600 s cap.** It was moved to the background automatically, not by choice. An uncached L2m pytest seed cannot meet the cap, so measure `full` and `states` through `tools/mechanism_dataset.py build --budget 540` in parts.

## Product facts seen (record in the packet)

- **D-AW-3 (verbatim, `states`):** `run_lifecycle(...)` returned `{"counts": {"ACTION_IN_HAND": 1, "CHANGE_APPLIED": 1}, "written": 2, "skipped": 0, "skipped_causes": []}`, thread state CHANGE_APPLIED effective 2026-10-30.
  - The D14 occurrence (Finding `6564b496…`, joined the thread as `ADDED`) produced **no event and no skip entry**. It is silent, as code reading predicted (`B/chain/lifecycle.py:45-56`).
- **The ACT-K1 apply value was "25".** The proposal came from the reserve of 20. Accepted at 10:12Z and applied at 11:00Z on 2026-10-29.
- **Step b:** `ADDED 2, ALREADY_PLACED 5, NEW_THREAD 1, skipped_ineligible 0`. Step c: `LINKED 1`.
- **Studies were both `[]`.** The opportunity job is enqueued at DB (real) time, and the story-time `test_lease_clock` never leased it. It is now fixed to the DB lease time (`KoboSite.studies`, **untested**). This is an R4 build-time fact → DD-1; name it in the packet and in `expected-mechanism.json` only if a check finding results.

## Resume here, in order

1. Run L0 and the tool tests, then `tools/mechanism_dataset.py build --day-set states --budget 540` (repeat `--resume` until exit 0). Time each part.
   - Check that `manifest.studies` now shows queued and DONE outcomes, and whether the headroom thread appears.
   - Then the same with `--day-set full`. This replaces the DB, so only one build at a time.
2. L3m:
   - `chain_coherence.py collect --work var/mechanism --database-url <mech url> --out <scratch>/mech-bundle`
   - `check --threads var/mechanism/expected-threads.json --expect …/expected-mechanism.json`
   - Record the summary line and `pg_database_size`, then `drop`.
3. **L2m** (`test_md0_mechanism_postgres.py`, rewritten but **not yet run**). It needs `ASSETOPS_SETUP_CACHE_DIR`, because each uncached seed takes 15 min or more.
   - Option: populate the cache once in parts (not possible in pytest). Otherwise ask the coordinator to approve one over-cap run, or a `states` set reduced further.
   - The cache-hit time then comes from `ASSETOPS_SETUP_CACHE_LOG`.
4. Review packet `.agent/review-packet-MD-0.md`, plus the ACTIVE_CONTEXT/CODE_STATE updates and the task status `in_review`.
   - Known deviations: Cold/EV removed (MD0-S2); the noon channels dropped; studies on DB time; the recurrence day D14 (my choice; MD0-S2 names no day); the fingerprint broadened to `backend/conversions`; `fresh()` not written (the tests use the store/engine fixtures).
