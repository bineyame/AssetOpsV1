# W5-01a C1 handoff — PARTIAL (Cooling built; Health held on an Architect question)

Branch `task/W5-01a-cold-selected-depth` from main `68b88dae`. Build commit `703807cf`.

## What was built

- `backend/assetops_backend/cold_site_api.py`: nested `opened`/`served` extracted to importable `build_cold_gate(registry, reads, access, disclosure)` and `cold_served(work)`; same refusal order, codes and messages. `build_cold_site_router` now uses them.
- `backend/assetops_backend/analytics/cold_depth.py`: `ColdDepthReadService.cooling(...)` on one `ColdReadService.within` connection: `selection_on` snapshot, `known_at > watermark` 422 `COLD_TIME_INVALID`, `envelope_on(...)["source_provenance"]` (EXC+START revision-ID selection), `accepted_on` for the exact selected IDs (door/grid event kind + source time). `recovery_state` from the W2 `COOLING_RESPONSE` capability (`ColdSiteReadService._capabilities`), restart/return/durations null, `comparison_state` `CONTEXT_MISSING`, five context rows. `door_pairs` pairs each OPEN with the next strictly later CLOSE.
- `backend/assetops_backend/cold_depth_api.py`: `GET /api/sites/{site_code}/cold/cooling` (WINDOW_KEYS, no 409). Mounted in `main.py` after the W2-04 cold Site router.
- Tests: `backend/tests/test_w501_cold_depth_router.py` (`test_cold_depth_gate_and_links`, `test_door_pairs`), `backend/tests/test_w501_cold_depth_postgres.py` (`test_cooling_first_steps_and_context` backup-failed: door Observed 60 s, power Observed, exact IDs/provenance/watermark, links, wrong Site 404, foreign tenant empty, disclosure 403, down store 503, future known_at 422; `test_late_reading_pending_then_historical` first cutoff, PENDING/LEASED/FAILED job, saved before-late `known_at` HISTORICAL, final cutoff; `test_stale_probe_window` enqueued 19:00-20:30 window gives STALE_SOURCE; `test_missing_probe_and_empty`; `test_no_w2_case_has_numeric_comparison` all six W2 cases).

## Response shape chosen (reviewer: confirm or rule)

`{schema_version, site_id, window{from,to,known_at,committed_watermark}, selection{state, assessment_revision_ids, accepted_evidence_ids, source_provenance}, cooling{recovery_state, selected_points[{role,source_time,evidence_ids}], observed_restart_at, observed_return_to_policy_at, duration_lower_seconds, duration_upper_seconds, comparison_state, context[{label,state,evidence_ids,duration_seconds}]}, links{temperature,backup,evidence,health}}`. These were not literal in the card:
1. The page payload key is `cooling`.
2. The context row keys are `label/state/evidence_ids/duration_seconds`, with state `Observed`/`Unknown`.
3. When several door pairs match, `duration_seconds` is their sum.
4. A point is dropped when its step evidence ID is not an accepted ledger record (the "missing selected ID" case).
5. `accepted_evidence_ids` is the union of the selected revisions' stored `evidence_ids`.
6. The spec's "`cooling_recovery.state`" does not exist in code. It is read as the W2 `COOLING_RESPONSE` capability state (`cold_site_reads.py:520-526`), which has exactly the LIMITED/CONTRADICTORY/UNAVAILABLE set.

## Held: Health read (`/cold/health`, `test_health_not_configured`). Not built. Question for the Architect

The card requires an "effective configured `asset_id`" per Health row from the "selected Foundation" and a NOT_CONFIGURED state from "a test-scoped selected Foundation without that asset". It does not say which read supplies it, so the following are open:
- **Source read.** `ColdReadService.basis_revisions_on` (`analytics/adapters/postgres_assessment_store.py:2443`) returns Foundation revision IDs and windows but not their content. The only cold Foundation projection is `sites/cold_foundation.py:260 cold_foundation_document`, which is reached through `cold_foundation_api.py:104` on a different store, not the snapshot connection. Which read, on the REPEATABLE READ connection, gives the Foundation content and asset IDs?
- **Per-row asset.** Should the generator come from `ColdStartPolicy.generator_asset_id` in the selected START result, or from Foundation components? Should the probe come from `ColdPolicy.probe_asset_id` or from room `probe_ids`? Should the compressor come from room `compressor_ids` (`cold_foundation.py:317`)?
- **Edge cases.** What applies with multiple rooms or compressors, or with no selected assessment? Is that NOT_CONFIGURED or UNKNOWN?
- **Payload keys.** What are the Health payload keys: a row list or keyed by asset kind?

## Test results (private DB `assetops_w501a_test`, dropped)

- C1 and adjacent tests: `pytest test_w501_cold_depth_router.py test_w501_cold_depth_postgres.py test_w204_cold_reads.py test_w203_cold_reads_postgres.py test_w202_cold_replay_postgres.py` → **51 passed** in 391 s.
- `tools/check-all.ps1`: **All 11 guards passed.**
- No frontend was touched, so tsc was not run.
- No processes are left running.

## Next

C1 per-unit review of the Cooling part (`703807cf`). The Architect rules on the Health questions above, then a follow-up C1 run adds `/cold/health` and `test_health_not_configured` before C2 starts.
