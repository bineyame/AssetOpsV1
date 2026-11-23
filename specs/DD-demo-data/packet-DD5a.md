# Review packet: DD5a part 1, the contracts/bindings half (units 1-2; partial)

Branch `task/DD5a-load` (the card says `task/DD5a-seal`; the dispatch named this one). Card `cards/DD5a.md`; rulings
D-DD.138 (R2366-2382), D-DD.139 (R2383-2403), D-DD.91 (R1455-1477), D-DD.28/29 (R157-176), D-DD.103 (R1826-1858).
Scope by dispatch: the contracts/bindings half only. Units 3 (`load_world_inputs` seals and loads) and 4 (cold and EV
on the bulk path, `test_dd_parity_cold_ev_postgres.py`, the `:688` lift) and EV session events are not built; see
`DD5a-handoff.md`.
USER_REVIEW_REQUIRED: false (protected seams `contracts/`, binding service; no UI; one discovery review per the card).

## What was built
- Unit 1 (D-DD.138). `contracts/.../source_envelope_v4.py`: `world_ev_channel_mappings(device_ids)` generates a
  depot's closed table (`_ev_connector(prefix)` per `ch-<code>-c<n>` prefix, plus the Site import; any other device
  raises), `WORLD_EV_CONNECTOR_PREFIXES` per depot, `V4_WORLD_EV_CHANNEL_MAPPINGS` (union), added to
  `V4_CHANNEL_MAPPINGS` (the ledger's `_decide_v4` lookup). Lab EV and cold tables byte-identical (digest test).
  `sites/binding_service.py`: `publishes_v4_metadata(role_set, origin)`: a conversion publishes v4 metadata for
  `cold-roles-1` and `ev-roles-1`; mini-grid sets keep v3. `ev-roles-1` validates against lab + world tables
  (`_V4_VALIDATION_TABLE_BY_ROLE_SET`); `_V4_TABLE_BY_ROLE_SET` and `v4_mapping_profile` are unchanged, so the EV
  analytics profile check is unchanged. Each channel must still be declared by the Site's own Foundation (closed per
  Site). Cold world devices are all in the cold table (no fix needed).
- Unit 2 (D-DD.139, D-DD.91). `evidence/world_seal.py` `seal_readings(SealContext, days)`: pure; v3 for mini-grid,
  v4 for cold/EV; fields, batches of at most 256 per (Site, source, local day), names
  `<SITE>.<source uuid>.<day>.<n>.batch.json`, epoch "1", one sequence per source over all days given; cold event ids
  by `cold_event_id`/`cold_correlation_id` from the Site's foundation digest; EV connector energy with a row
  `session` object gets `session_id = ev_session_id(...)` and `connector_id`. `cold_correlation_id` moved to
  `contracts/.../gateway_report.py` beside `cold_event_id` (same bytes; host imports it from there and still exposes
  it); new `ev_session_id(foundation_digest, connector_id, session_ordinal)` = `ev-` + SHA-256.

## Tests (each shown failing first; logs in /opt/assetecon/evidence/DD5a/)
- `backend/tests/test_dd5a_world_v4_tables.py` (3, pure): lab tables identical; world table == each depot's declared
  channels and prefixes; out-of-shape device refuses. 2 failed before the contracts change.
- `backend/tests/test_dd5a_world_v4_bindings_postgres.py` (3): harvest-cold apply then COLD-THIKA accepts one v4
  meter and one door event; metro-bus EV-KAS accepts connector energy (session) and the Site import; lakeside
  KOBO-001 has no v4 rows and its digest equals main's v3 formation. On main code: 3 failed (`u1-failfirst.log`).
- `backend/tests/test_dd5a_world_seal.py` (3, pure): 288-row source-day -> 256 + 32, sequences 1..576 across two days,
  unique message ids, each batch parses; unbound channel refuses `WORLD_TELEMETRY_UNRESOLVED`; millesimal spelling.
- `host/tests/test_dd5a_world_seal_parity.py` (5): byte parity with the gateway's `_envelope_v3_text`,
  `_envelope_v4` and `_seal` for v3 mini, v4 cold measurement, v4 cold event, v4 EV energy with session, and the
  batch. In `host/tests` because the dependency-direction guard forbids the gateway in `backend/` (tests included).
  Both seal files failed at collection before `world_seal.py` existed.

## Plants
- (a) `publishes_v4_metadata` back to `origin != "CONVERSION"`: COLD-THIKA meter `REJECTED MAPPING_INCOMPATIBLE`
  (`plant-a.log`). Reverted.
- (b) sequence reset per day: `test_a_288_row...` fails at index 288 (1 != 289) (`plant-b.log`). Reverted. The
  load-level message-id collision needs unit 3.
- (c) revert `:688`: not run, unit 4 not built.

## Checks
- `tools/check-architecture.ps1` (guard python set): passed. `check-agent-workflow.ps1`: passed.
  `check-decision-index.py`: OK. `statement_catalogue.py`: exit 0.
- Reach set (card list minus the unbuilt parity file, plus the four host/backend files importing `cold_publication`
  and the dd5a files), one `--db-lane` call: RESULT_PLACEHOLDER
- D-DD.118: `grep -rn fuel_basis backend/assetops_backend/evidence/ backend/assetops_backend/load_world_inputs.py`:
  no match (bulk load does not call it).
- Largest batch seen: 256 envelopes (the split test). Mid-build questions to the lane Architect: 0.

## Known deviations
1. Card/ruling say the world Site import is `("site-meter-1", "import")`; the depots' `/2` files and conversions
   declare `site-meter`. Generated from the Foundation, so `("site-meter", "import")` (same entry as the lab's).
2. "Kobo's roles-4 conversion digest byte-equal to main": the world Kobo conversion is roles-5, and `bindings_sha256`
   includes fresh UUIDs, so no run-to-run pin exists. The test recomputes main's v3 formation from the stored rows and
   asserts equality, plus no v4 rows.
3. Readings values are millesimal text ("4.000"), which the envelope parsers refuse as non-canonical. The sealer
   writes the same exact value in canonical spelling ("4"). Not named in the card; flag for the Architect.
4. `ev_session_id` takes `connector_id` (the row's `session.connector_id`), not a device: the connector meter and the
   charger controller carry one session, so a device-keyed id would differ between them. EV session events refuse
   `WORLD_SEAL_EV_EVENT_PENDING` until DD4b fixes their row shape (D-DD.91 "EV (DD4b)" vs D-DD.139 differ on where
   `session_id` comes from).

## Moved pins
None. Lab EV/cold tables, Kobo v3 digest formation and cold correlation bytes are unchanged. Lab cold/EV conversions
(`cold-lab-001`, `ev-lab-001`) now publish v4 metadata (ruling), which changes those sets' digests; no test pins them
(reach set below).
