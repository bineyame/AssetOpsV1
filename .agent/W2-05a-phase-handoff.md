# W2-05a phase handoff - run 3 (spec commits 1 and 2 landed)

Branch `task/W2-05a-ev-foundation`, worktree `AssetOpsV1-review5`. Commit 1 `2d8b323d`; QC/QD fix `932ad981`; spec commit 2 `880384d3`. Next run builds spec commit 3 (selected API). Architect rulings Q1-Q8 and QA-QD live in `.agent/W2-05a-build-spec.md` (`D-2026-10-18-w2-05-buildspec`); they are not repeated here.

## What landed

- **QC/QD (`932ad981`)** `sites/ev_foundation.py:_validate_ev_topology`: a second `AC_BUS` refuses with the path to the extra feed (checked from components, with or without topology). Every `METER` refuses more than one parent and, once a feed is declared, no parent. A charger refuses more than one meter and, once a feed is declared, no meter->feed path. Nonempty schedules still need `_has_supply_path`. Tests in `test_w205a_ev_vocabulary.py::TestTopology` (second feed, second feed without topology, unfed meter, absent feed publishable, absent feed with hours refused).
- **Commit 2 (`880384d3`)**
  - `sites/binding_roles.py`: `ROLE_SET_EV_1="ev-roles-1"`, `EV_ROLES_1` (8 roles; required = session event, state, energy per EV_CONNECTOR; `ev_site_import` ONE on METER), `EV_CONNECTOR_STATES`, `EV_CADENCE_PROPERTY_BY_ROLE` (role -> `ev-status-cadence`/`ev-meter-cadence`, events None), `IDENTITY_KWH` closed both ways to the INTERVAL_DELTA role (`_identity_kwh_problem`). `CONVERSION_KINDS` is unchanged.
  - `contracts/.../source_envelope_v4.py`: `V4_COLD_CHANNEL_MAPPINGS` (the 12 cold entries, byte-identical), `V4_EV_CHANNEL_MAPPINGS` (the 14 c1/c2 tuples + `(site-meter,import)`), `V4_CHANNEL_MAPPINGS` = cold + the 2 reserved W2-00 tuples (now labelled `ev_session_event`/`ev_connector_fault`) + EV, `V4_EV_MAPPING_PROFILE_ID/VERSION` (`simulator-lab-gateway-ev`/1), `V4_CHANNEL_MAPPINGS_BY_PROFILE`. `simulator/.../gateway/mappings.py` now builds the cold gateway set from `V4_COLD_CHANNEL_MAPPINGS` (the same 11 channels as before).
  - `sites/binding_service.py`: `_V4_TABLE_BY_ROLE_SET` (cold keeps the whole table; EV uses the EV profile table) in the `validate_bindings` closed-table branch; `ev_snapshot_gaps` + EV branch in `acquisition_snapshot` (the role set must be `ev-roles-1`; gaps come from `ev_foundation.ev_blocking_gaps`).
  - `sites/ev_foundation.py:ev_blocking_gaps(content, bound)`: CONNECTOR_NOT_DECLARED, FEED_OR_LIMIT_MISSING, and per connector METER_NOT_BOUND / SESSION_EVENTS_NOT_BOUND / STATUS_NOT_BOUND. Commit 3's readiness builds on it.
  - `sites/ev_lab.py:install_ev_lab`: imports `tests/fixtures/w2/ev-lab-001.yaml`, then publishes `conversions/ev-lab-001-bindings.json` (15 bindings, `ev-roles-1`) at Foundation `valid_from` 2026-10-01 through `BindingService.publish`. There is no conversion replay: it would carry no v4 metadata, and EV has no v3 history.
  - Tests: `test_w205a_ev_roles.py` (25, no DB) and `test_w205a_ev_foundation_postgres.py` (8). The Postgres tests cover persist/reload; v4 metadata equal to each entry; the 6 October snapshot served; missing meter, event and status binding revisions from 2026-10-08 and a missing-limit Foundation revision from 2026-10-12 (via `FoundationService._publish_content_change`), each refusing Draft while 6 October stays served; optional roles absent not blocking; and energy role/conversion refusals. Adjusted: `test_w201_cold_vocabulary` and the gateway `test_source_envelope_v4` table assertions now use the cold table and 29 entries; `test_w202_cold_replay_postgres` binds the reserved session tuple with `entry.role`, because the ledger enforces labelled roles.

## Checks (run 3)

- `test_w205a_ev_vocabulary.py` + `test_w201_cold_vocabulary.py`: 102 passed after QC/QD. `test_w205a_ev_roles.py` + vocab: 95 passed.
- Postgres, private `assetops_w205a_test`: `test_w205a_ev_foundation_postgres.py` 8 passed. Non-vacuous proof: with the EV branch disabled, 6 failed; reverted.
- Adjacent (16 files: bindings, S1/S3 roles, W2-00/01/02 Postgres and API): 297 passed, plus 1 cold-vocab table assertion fixed and rerun green.
- Simulator 271 passed, gateway 233 passed (after the count fix), contracts 6 passed.
- `tools/check-all.ps1`: 10/10.

## Questions for the Architect (none blocks commit 3's structure)

- **QE, Site import cadence.** `ev-meter-cadence` is a per-connector property, but `ev_site_import` binds the METER. Which value gives `bindings[].cadence_seconds` for the Site import row? The options are a connector's value (which one, if c1 and c2 differ?), the minimum, or null. The fixture has 5 min on both, so the value is the same today.
- **QF, reserved W2-00 tuples.** They are in `V4_CHANNEL_MAPPINGS` with EV role labels but not in the `simulator-lab-gateway-ev/1` table, so an `ev-roles-1` publication cannot bind them. Please confirm they stay outside the EV profile.
- **QG, device-to-connector check.** Q1 says each cX device binds the cX connector asset. The fixture test asserts this, but `validate_bindings` does not refuse a c1 device bound to the c2 asset. Ingestion's `EV_CONNECTOR_MISMATCH` compares only the envelope connector to the bound asset. Should publication refuse it, and under which code?

## Next: spec commit 3 (selected API)

1. `backend/assetops_backend/ev_foundation_api.py` beside `cold_foundation_api.py:build_cold_foundation_router`, with `GET /api/sites/{site_code}/ev/foundation?at=`. The response shape, error codes and contact/commissioning rules are in the spec section "Role set, binding and selected read". Use the cold Access/source gate. Decimals are strings; unknowns are null.
2. A pure readiness/projection in `sites/ev_foundation.py`: `READY_TO_REPORT|CONFIGURATION_INCOMPLETE` from `ev_blocking_gaps`, plus the nonblocking `SITE_IMPORT_NOT_BOUND`, `SOURCE_NOT_CONTACTED` and `COMMISSIONING_UNCONFIRMED`. Cadence uses `EV_CADENCE_PROPERTY_BY_ROLE` (min -> s), pending QE for Site import.
3. Main include; API tests (stocked, gap revisions at pinned `at`, 401/403/404/422/503, extra query field refused).

Later: commit 4 is the UI routes and captures. Commit 5 is `0024_w2_ev_config`, after W2-04's `0023` lands on this branch; then the final guards, one full backend suite and host suite, and the packet.
