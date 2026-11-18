# Review packet: OWN-G3a, saving operational records from the screen (backend)

Branch `task/OWN-G3a-operational-entry-api` (main merged at `1d666d410`). Spec: `.agent/build-sheet-OWN-GAPS-2026-11-08.md`
§3.1, §3.2, §3.4 (G3a) and §3.5 (G3a), with Rev 1 and the R2-G3a rulings 1-6. Pre-flight: `.agent/preflight-G3a.md`.
Commits: `9d65b92f7` (pre-flight), `ad9c2cdc2` (build and no-DB tests), `b1cd17701` (Postgres tests), plus this packet.

## Outcome

`POST /api/sites/{site_code}/work/operational-entries` takes the closed screen entry, composes an
`operational-record-1` command server-side under `service:operator-entry`, and writes it through the existing
`WorkService.post_operational_record`. That path gives the same validation, idempotency, hash, REC code and audit
columns as other records. The route is on only when `host/lab_app.py` reads `ASSETOPS_OPERATIONAL_ENTRY=on`. The demo
`serve_env` sets it. With the variable unset, the route is 403, and any other value refuses startup.

## Files

| File | Change |
|---|---|
| `backend/assetops_backend/work/operational_entry.py` (new) | `validate_entry` (§3.2 steps 1-5, R2-4), `compose_entry` (mapping table, R2-3 normalised value), `occurred_utc`, `entry_site_context` (R2-2), the actor and attestation constants |
| `backend/assetops_backend/work_api.py` | `SiteContext` type; `build_work_router(entry_principal=, site_context=None)`; the new route, refusal order per R2-1 |
| `backend/assetops_backend/work/model.py` | `OPREC_ENTRY_INVALID`, `OPREC_ENTRY_TICKET_REQUIRED`, `OPREC_ENTRY_NO_TANK` in `MESSAGES` (R2-5 literals) and `STATUS` (422) |
| `backend/assetops_backend/main.py` | `create_app(operational_entry_principal=no_service_principal)`; one `fuel_store` shared by `FuelNightRead` and `site_context` (R2-2) |
| `host/lab_app.py` | `OPERATIONAL_ENTRY_ENV`, `operational_entry_principal`, `operational_entry_from_environment()`; `build_app` refuses before building and calls `setdefault` (R2-6) |
| `tools/demo_combined.py` | `serve_env()` adds `ASSETOPS_OPERATIONAL_ENTRY=on` (serve child and tick children, so env parity holds) |
| `backend/tests/test_own_g3_operational_entry.py` (new) | 55 unit tests |
| `host/tests/test_own_g3_entry_env.py` (new) | 7 env and startup tests |
| `backend/tests/test_own_g3_operational_entry_postgres.py` (new) | 8 Postgres tests |

## Spec item to evidence

| Spec item | Evidence |
|---|---|
| §3.2 mapping: kind, unit, asset, body, digest for each entry | `test_tank_dip_maps_to_a_tank_record`, `test_fuel_delivery_maps_with_the_ticket_digest` (checked against `hashlib.sha256` of the literal), `test_stock_and_meter_are_manual_readings_without_an_asset` |
| Actor and attestation `job=site-admin-entry` (Rev 1) | `test_tank_dip_maps_to_a_tank_record`; Postgres `test_the_stored_row_carries_the_server_identity_and_audit_columns` |
| Dar es Salaam 06:00 local becomes 03:00Z | `test_dar_es_salaam_six_local_is_three_utc` |
| R2-3: `198`, `198.0` and `0198` compose identical commands; `198.50` becomes `198.5` | `test_value_is_normalised_in_body_digest_and_quantity`; Postgres body "... 198.5 L." |
| Each invalid shape gives `OPREC_ENTRY_INVALID` (R2-4: all five keys required; empty or bad ticket) | `test_each_invalid_shape_is_oprec_entry_invalid` (27 cases), `test_a_missing_key_is_invalid` (5), `test_non_objects_are_invalid` |
| A delivery without a ticket gives `OPREC_ENTRY_TICKET_REQUIRED` | unit test and the wire test `test_ticket_required_and_no_tank_over_the_wire` |
| No tank gives `OPREC_ENTRY_NO_TANK`; a meter reading still saves | `test_a_fuel_entry_with_no_single_tank_is_no_tank`, wire test |
| R2-5 message and status literals | `test_a_fuel_entry_with_no_single_tank_is_no_tank` |
| R2-1 refusal order: access, 404, grant, principal, store, shape, context, service | `test_access_404_and_the_write_grant_precede_the_principal`, `test_no_principal_is_403_even_with_an_invalid_body_and_no_store`, `test_a_principal_with_no_store_is_503_before_shape`, `test_shape_is_checked_before_the_site_context` |
| The browser cannot send an actor | `test_the_browser_cannot_send_an_actor` (422, service not called) |
| The service's codes pass through with their statuses | `test_service_refusals_pass_through_with_their_status` (4 codes) |
| R2-2: a Site context outage gives 503; a programming error is not masked | `test_site_context_maps_store_failures_to_unavailable`, `test_a_site_context_outage_is_503` |
| The existing `/operational-records` route keeps `no_service_principal` | `test_the_existing_record_route_keeps_its_own_principal` |
| R2-6: env `on`, unset, empty and `yes` (`ON` and `on ` also refuse); explicit override wins | `host/tests/test_own_g3_entry_env.py`, 7 passed |
| Postgres: 201, then an identical retry gives 200 with the same body | `test_saved_then_identical_retry_returns_the_stored_body` |
| Postgres: the same key with another value gives 409 `WORK_EVENT_DUPLICATE_KEY` | `test_the_same_key_with_another_value_is_a_duplicate` |
| Postgres: stored actor, attestation, `authorization_basis`, REC, `payload_sha256`, key; `recorded_at` within DB `clock_timestamp()` bounds | `test_the_stored_row_carries_the_server_identity_and_audit_columns` |
| Postgres: 31 days back and 10 minutes ahead are refused with zero rows | `test_too_old_and_future_entries_are_refused_with_zero_rows` |
| Postgres: an app with no principal gives 403 with zero rows | `test_an_app_with_no_entry_principal_is_403_with_zero_rows` |
| Postgres: a saved dip is returned by `build_fuel_records_reader` | `test_a_saved_dip_is_read_by_the_fuel_balance_records_reader` |
| Postgres: `MANUAL_READING` rows keep their unit and have no `asset_id` | `test_manual_readings_are_stored_with_their_unit_and_no_asset` |
| Postgres: the stored delivery digest | `test_a_delivery_is_stored_with_its_ticket_digest` |

## Checks run

- `backend/tests/test_own_g3_operational_entry.py`: **55 passed**.
- `host/tests/test_own_g3_entry_env.py`: **7 passed**.
- `backend/tests/test_own_g3_operational_entry_postgres.py`: **8 passed, 0 skipped**, 21 s pytest, 23 s wall. Base
  `assetops_g3a_test` (own; the harness routes the run to `assetops_g3a_pt<run>_main_test`). Revision `b1cd17701`. RAM was
  4.3 GB free before the run.
- Adjacent no-DB files (`test_w401_work_api`, `test_w402_*`, `test_w403_*` non-Postgres, `test_w601e_operational_index`,
  `test_ch5c_env_parity`, `test_ch5c_store_off`, `test_health`, `test_k2_fuel_records`, `test_ch0_tick_timing`): 184
  passed, 26 skipped (Postgres modules without a URL), 1 failed. The failure is
  `test_ch5c_env_parity.py::test_the_tick_child_and_the_serve_child_compute_one_code_version`, with
  `SystemExit: Run prepare first.`. The same test fails the same way with my changes stashed. It needs a prepared demo
  work directory, so this slice did not cause it.
- Non-vacuity proof (on committed code, reverted with `git checkout`): with the principal and store checks swapped, and
  the pre-context `validate_entry` removed, 2 tests fail (`..._403_even_with_an_invalid_body_and_no_store`,
  `test_shape_is_checked_before_the_site_context`). After the revert, 55 passed.
- `tools/check-architecture.ps1` at `b1cd17701`: "Architecture check passed.", exit 0, 214 s.
- No full suites were run (per the brief).

## Known deviations

- **D1 (R2-2 wording):** the ruling names `SQLAlchemyError` and the no-URL `RuntimeError`. `configuration-persistence.ps1`
  forbids driver imports outside the adapters (`:295`, `:1036`), so `entry_site_context` instead maps every non-programming
  exception to `WorkStoreUnavailable`. `ValueError`, `TypeError`, `KeyError` and `AttributeError` re-raise. This is the
  existing `fuel_balance/night_read.py` `_guard` pattern. The behaviour is a superset of the ruling.
- **D2 (R2-6 form):** the principal is the named function `lab_app.operational_entry_principal` rather than an inline
  lambda, so `build_app`'s `setdefault` can be asserted by identity. It returns the same literal.
- **D3 (helper split):** `validate_entry` is public and the route calls it before reading the Site context (R2-1 order:
  shape, then context). `compose_entry` still validates first, so it stays pure and self-contained.

## Residual risk

- The route is a new write path. Its only gate is the server variable. The identity is a labelled service, not a
  person (§3.1).
- G1 posting through this route meets the 30-day refusal and records deliveries late (ruled in R2-G1; no G3a change).

## User review

Not required for this backend slice. The fresh Opus reviewer gates the merge (§3.6).
