# DD5a handoff (PARTIAL: units 1-2 done; units 3-4 and EV events next)

Branch `task/DD5a-load`, worktree `/opt/assetecon/AssetOpsV1-dd5a`. Packet `packet-DD5a.md`. Evidence
`/opt/assetecon/evidence/DD5a/`.

## Done
- Unit 1: world v4 tables and conversion metadata (`source_envelope_v4.py` `world_ev_channel_mappings`,
  `V4_WORLD_EV_CHANNEL_MAPPINGS`; `binding_service.py` `publishes_v4_metadata`, `_V4_VALIDATION_TABLE_BY_ROLE_SET`).
- Unit 2: `backend/assetops_backend/evidence/world_seal.py` (`SealContext`, `seal_readings`, `WorldSealRefused`);
  `gateway_report.py` `cold_correlation_id` (moved), `ev_session_id`.

## Next (unit 3, then unit 4)
- `load_world_inputs.py`: build `SealContext` per Site from `PostgresEvidenceLedger.site_scope(slug, code)` and the
  binding snapshot download (`binding_service.py` ~1143); `foundation_digest` from `F` (`site-inputs.json`); `v4` =
  role set is cold/EV. Accept `staged/`, `sealed/`, `disorder/` (layout check in `_tenants`), write `<slug>/sealed/`
  once, re-run re-seals and refuses differing bytes; output adds `readings_files`, `sealed_batches`; refusal
  `WORLD_TELEMETRY_UNRESOLVED <file> <what>` exit 2 (map `WorldSealRefused` there). Plant (b) at load level.
- Unit 4: `postgres_evidence_ledger.py:688` admit the three types; `test_ds3_bulk_load_postgres.py`
  `case_coldchain_site` -> unknown type; new `test_dd_parity_cold_ev_postgres.py` (cold day now; EV day after DD4b);
  plant (c).
- EV half after DD4b: EV session events in `world_seal._envelope_text` (now refuse `WORLD_SEAL_EV_EVENT_PENDING`).

## Risks
- Known deviations 1-4 in the packet (site-meter name, Kobo digest form, decimal spelling, `ev_session_id` key).
- `host/tests/test_dd5a_world_seal_parity.py` imports helpers from `backend/tests/test_dd5a_world_seal.py` by path.
