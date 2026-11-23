# Review packet: DD5a, sealing and the cold and EV bulk path (units 1-4, EV session events)

Branch `task/DD5a-load` (the card says `task/DD5a-seal`; the dispatch named this one). Card `cards/DD5a.md` (with
D-DD.162's "Facts the code fixes"); rulings D-DD.138 to D-DD.140 (R2366-2419), D-DD.161 and D-DD.162 (R3035-3087),
D-DD.91 (R1455-1477), D-DD.28/29 (R157-176), D-DD.103, D-DD.118. Main merged at b8edd4425 (DD4b, D-DD.155-162).
USER_REVIEW_REQUIRED: false (protected seams `contracts/`, binding service, evidence ledger; no UI; one discovery
review per the card).

## What was built
- Unit 1 (D-DD.138, narrowed by D-DD.161). `source_envelope_v4.py`: `world_ev_channel_mappings`,
  `V4_WORLD_EV_CHANNEL_MAPPINGS` (generated from the depots' `/2` devices; Site import `("site-meter", "import")`).
  `binding_service.publishes_v4_metadata(role_set, origin, world_conversion=)`: v4 metadata at conversion only when
  `convert(..., world_conversion=True)` (passed only by `onboard_operator apply --bindings`) and the set is
  `cold-roles-1`/`ev-roles-1`. Lab tables and Lab W2-02 design unchanged.
- Unit 2 (D-DD.139, D-DD.91, D-DD.161). `evidence/world_seal.py` `seal_readings`: v3 mini, v4 cold/EV, at most 256 per
  (Site, source, local day), epoch "1", one sequence per source over the span; cold event ids by `cold_event_id` /
  `cold_correlation_id` (moved to `contracts/.../gateway_report.py`). Values written canonically, asserting
  `Decimal(out) == Decimal(in)` and `is_canonical_decimal`.
- D-DD.161 EV session change. `ev_session_id` withdrawn from `contracts/`. The sealer copies `session_id` and
  `connector_id` from an EV event's object or a row's `session` object; a session event's `correlation_id` is its
  `session_id`. Only connector energy (`INTERVAL_DELTA`) claims a session; means and states seal null ids (the v4
  contract). An EV event without a session forms cold ids over its `correlation`; with neither, or energy with no
  session, `WORLD_SEAL_EV_UNCORRELATED`. `WORLD_SEAL_EV_EVENT_PENDING` removed.
- Unit 3 (spec §4.6 as amended by D-DD.139/140). `load_world_inputs.py`: globs `*.readings.json` beside `*.batch.json`;
  per Site resolves `PostgresEvidenceLedger.site_scope(slug, code)`, then the pinned snapshot over the readings span
  (`sites.registered_basis.select_registered_basis`, which calls `acquisition_snapshot`), checked by
  `world_seal.context_from_snapshot` (same Site, gateway `edge-<code lower>`, every binding's source listed);
  `foundation_digest` from `site-inputs.json` (F) beside the tenant folders. Writes `<slug>/sealed/` once through the
  new adapter `evidence/adapters/sealed_batch_files.py` (`composition.build_sealed_batch_files`); a re-run re-seals and
  refuses `WORLD_SEALED_BYTES_DIFFER` on any differing or stray file. Layout accepts `staged/`, `sealed/`, `disorder/`.
  Output line adds `readings_files`, `sealed_batches`. Refusals exit 2 (`WORLD_TELEMETRY_UNRESOLVED <file> <what>`).
- Unit 4 (spec §4.7 as amended by D-DD.140). `postgres_evidence_ledger.py` `:688` guard: `site_type not in
  BULK_PROVEN_SITE_TYPES` (= MINIGRID, COLDCHAIN, EV_CHARGING); `BULK_SITE_TYPE_UNPROVEN` stays in `BULK_REFUSALS`.
  New `test_dd_parity_cold_ev_postgres.py`; `case_coldchain_site` became `case_unknown_site_type` (the clone's
  site_type CHECK dropped, type `HYDRO`).

## Tests (each shown failing first; logs in /opt/assetecon/evidence/DD5a/)
- `backend/tests/test_dd5a_world_v4_tables.py` (3), `test_dd5a_world_v4_bindings_postgres.py` (3): part 1, as before.
- `backend/tests/test_dd5a_world_seal.py` (10, pure): split 256+32 and sequences across days; unbound refuses;
  canonical spelling; D-DD.161: session event and in-session energy share the pack id (= correlation id); means claim
  no session; EV event without session forms cold ids; neither refuses (event, energy); `ev_session_id` absent;
  value equality. 6 failed before the change (`red-ev-session.txt`).
- `host/tests/test_dd5a_world_seal_parity.py` (6): byte parity with the gateway for v3 mini, v4 cold measurement,
  cold event, EV energy with the pack session, EV session event (hand rows in DD4b's shape; event and energy
  correlate), and the batch seal.
- `backend/tests/test_dd5a_load_world_inputs.py` (6, pure, injected resolver): sealed beside the inputs and loaded;
  re-run writes no bytes; a changed sealed byte refuses and loads nothing; unknown Site exit 2 naming the file; Site
  missing from F refuses; `staged/`/`sealed/`/`disorder/` accepted. 6 failed first (`red-unit3.txt`).
- `backend/tests/test_dd5a_load_world_postgres.py` (3): the real resolver on the converted Kobo seed: two days load,
  sequences 1..6, six message ids; re-run `already_loaded` 2 and no sealed bytes rewritten; unknown Site exit 2, nothing
  stored.
- `backend/tests/test_dd_parity_cold_ev_postgres.py` (2): `harvest-cold` and `metro-bus` onboarded with world bindings
  (in a subprocess, so the seed can be cloned); one COLD-THIKA day (meter means, door open/close) and one EV-KAS day
  (session start, in-session energy x2, depot import, session end) sealed by `world_seal`, submitted centrally to one
  clone and bulk-loaded into the other: evidence, batch, disposition and recompute-job rows equal; the
  `_enqueue_admitted` spy saw the same ordinals under the same Site type; EV rows carry the pack session id. Red first
  via plant (c).
- Moved pin: `test_ds3_bulk_load.py::test_success_passes_the_commercial_folder...` output keys gain the two counts.

## Plants (each reverted)
- (a) part 1: COLD-THIKA meter `REJECTED MAPPING_INCOMPATIBLE` (`plant-a.log`).
- D-DD.161 narrowing: `world_conversion` default True (a Lab replay passing True): 5 of 5
  `test_w202_cold_lab_bindings_postgres.py` fail, incl. `test_cold_001_conversion_carries_no_v4_keys`
  (`plant-dd161-lab.txt`).
- (b) at load level: sequences reset per day: `test_two_days_seal_and_load...` and the re-run test fail, exit 2
  `BATCH_ID_CONFLICT` (the second day reuses the first day's sequence range, hence its batch id) (`plant-b.txt`).
- (c) `:688` back to MINIGRID only: both parity cases `BULK_SITE_TYPE_UNPROVEN ... COLDCHAIN` / `EV_CHARGING`
  (`plant-c.txt`).

## Checks
- `tools/check-architecture.ps1` (guard python set): passed after two fixes (`guards-1.txt` -> `guards-2.txt`): the
  configuration-persistence scan refused file writes in `load_world_inputs.py`; moved to the new evidence adapter,
  named in that guard's evidence `Writer` list (as `legacy_comparison_file.py` was). `check-agent-workflow.ps1`:
  passed. `check-decision-index.py`: OK. `statement_catalogue.py`: OK after refusal details became codes and names
  only, and `--prune` dropped the one stale print of the old bulk-guard sentence.
- Reach set, ONE `--db-lane` call at af5185c9f (card list + host/backend files importing `cold_publication` + Lab cold
  bindings + all dd5a files; `reach-final.log`, file list `reach-final-files.txt`): **243 passed, 1 skipped**, 620.8 s pytest, 624 s wall incl. slot wait, exit 0. Main: `.agent/main-baseline/` (not rerun).
- D-DD.118: `grep -rn fuel_basis` over `bulk_load.py`, `load_world_inputs.py`, `world_seal.py`, the Postgres ledger,
  `ledger.py`, `ledger_service.py`: no match.
- Largest batch seen: 256 envelopes (the split test); world days in these tests are under 256 per source.
- Mid-build questions to the lane Architect: 0 (deviation 7 is an inference to confirm).

## Known deviations
1-5. As part 1, all confirmed or accepted by D-DD.161 (site-meter name, Kobo digest form, canonical decimals, EV
   session id now the pack's, `world_conversion` narrowing).
6. DD4b's writer on main does not yet carry `"session": {"session_id", "connector_id"}` on in-session connector rows
   (D-DD.161's DD4b follow-up; `telemetry_ev.py` drops the eighth tuple element before binding). Until it does, a real
   EV readings day refuses `WORLD_SEAL_EV_UNCORRELATED` at its first energy row. Built and tested on hand rows in the
   ruled shape. Needs the DD4b follow-up before DD5b runs EV days.
7. An EV connector event outside a session (`EV_CONNECTOR_FAULT`/`CLEAR`) must carry `connector_id` (v4 contract);
   the writer's event object has none then. The sealer uses the event's `connector_id` if present, else its
   `component_id` (the writer sets both to the connector). Architect to confirm.
8. Plant (b) surfaces as `BATCH_ID_CONFLICT`, not a message-id code: the batch id covers the sequence range.
9. New file writer `evidence/adapters/sealed_batch_files.py`, added to `configuration-persistence.ps1`'s evidence
   writers (the guard admits no write elsewhere in `backend/`).
10. The bulk guard reads `BULK_PROVEN_SITE_TYPES` (named constant, same three types); its refusal detail is the Site
   type only (statement catalogue). Codes named here: `WORLD_SEALED_BYTES_DIFFER` (re-seal mismatch or stray sealed
   file), `WORLD_SEAL_EVENT_UNCORRELATED` (a cold event with no `correlation`), `WORLD_SEAL_VALUE_NOT_CANONICAL`.
11. "Runs under `world.env` for the tenant" is the caller's (`tools/world.py`, DD5b); the module takes `DATABASE_URL`
   and `--tenant` as before. C-DD8 on the store and C6's glob are DD5b's wiring.

## Moved pins
1. `test_w205a_ev_foundation_postgres.py::test_legacy_w200_tuples_cannot_bind_under_the_ev_profile` (part 1).
2. `test_ds3_bulk_load.py` output-line keys (+`readings_files`, `sealed_batches`).
3. `test_ds3_bulk_load_postgres.py` `case_coldchain_site` -> `case_unknown_site_type` (D-DD.140).

## Fix round (review-DD5a.md round 1 Lows plus D-DD.167; Claude Opus 5.5)
- D-DD.167 (DD5a part): `load_world_inputs.seal_context_key` = first 12 hex of SHA-256 over the canonical JSON of the
  sorted `[site_code, gateway_id, source_id, binding_set_id, foundation_digest]` lists of the Sites sealed; sealed files
  go to `<slug>/sealed/<context12>/`. A re-run against the same database finds the same folder (re-seal and `stray`
  refusals hold there); a rebuilt database writes a new folder and reads or deletes no sibling.
- L1: `seal_readings` maps `EnvelopeRejected` to `WORLD_SEAL_ENVELOPE_INVALID <device>/<signal> <kind> at <field>` and a
  missing `connector_id` beside a `session_id` to `WORLD_SEAL_EV_UNCORRELATED`; both exit 2.
- L2: `WorldSealRefused` carries `day`; the loader names that day's readings file (Site-level refusals keep the first).
- L3: `SealedBatchFiles.write_new` uses `O_CREAT|O_EXCL` plus fsync.
- L4: state entry 212 marked superseded by 213; `ev_session_id` claim removed.
- Tests (each shown failing first, `/opt/assetecon/evidence/DD5a/fix/red.txt`: 10 failed): new `test_dd5a_sealed_batch_files.py`,
  additions to `test_dd5a_world_seal.py` and `test_dd5a_load_world_inputs.py`. Existing sealed-dir reads in two tests
  moved to the context folder (moved pin).
- Plant: a re-seal in the same context with changed bytes still refuses (`test_a_changed_sealed_byte_refuses...`, green).
- Run: `--db-lane`, 6 files incl. `test_dd5a_load_world_postgres.py`: 64 passed (`fix/db.txt`). Main baseline:
  `.agent/main-baseline/23d2cd9f6.md`. Guards: `fix/arch.txt`, `fix/workflow.txt`, `fix/cat.txt`.
- Not done: the card's `"sealed_dir"` output key was not added (not in this round's list).
