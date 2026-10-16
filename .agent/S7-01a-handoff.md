# S7-01a handoff - fixture and read contract for S7-01b

Branch `task/S7-01a-health-read`. Non-UI; S7-01b consumes exactly this.

## Fixture: `backend/tests/s7_health_cases.py` (`D-edge-health-cases`)

`HealthCases(url, site_code, work_dir, clock, tenant_slug="demo")`; call `close()` when done.

- `register()`: on an already imported Site (KOBO-001), inserts one gateway plus one source per case
  (fixture SQL, DISABLED as an import leaves them), then enables each with the provisioning CLI
  `issue --enable-source <key>-device --cadence-seconds N` (credential files `work/cred-<key>.*`).
  Writes `work/s7_health_cases.json`: `site_code, site_id, tenant_id, epoch, gateways{key: gateway_id,
  source_id, cadence_seconds, meaning, credential_path}`. A later `HealthCases(...)` on the same work dir
  reloads it (so `deliver` works from a fresh process).
- `publish(advance)`: the six central cases through the authenticated central path (TLS boundary,
  bearer resolver, `DiagnosticIngestionService`, `POST /api/gateways/{id}/diagnostics`). Tests pass
  `advance(seconds)` to move a test clock 600 s; the walkthrough passes nothing (real clock).
- `deliver()`: next local sequence on `s7-current` and `s7-delayed-old` (fresh server receipt; the
  delayed case keeps 6 h old facts). Returns `{key: receipt}`.
- Gateway external IDs and what the read shows (test clock: read 605 s after the first posts):

| key | cadence | contact | reported_facts |
| --- | --- | --- | --- |
| `s7-current` | 60 | CURRENT | CURRENT |
| `s7-stale-cadence` | 30 | STALE (real clock: after 60 s) | OLD |
| `s7-delayed-old` | 60 | CURRENT | OLD (receipt lag 6 h) |
| `s7-queue-growth` | 60 | CURRENT | queue 900 / 5400 s (seq 2; seq 1 was 40 / 600 s) |
| `s7-clock-offset` | 60 | CURRENT | UNKNOWN, clock UNTRUSTED (95 000 ms) |
| `s7-disk-stop` | 60 | CURRENT | disk STOP, queue 300 (seq 1 WARN) |
| `s7-disk-recovery` | 60 | CURRENT | disk OK, queue 0 (seq 1 STOP) |
| `s7-never-received` | 60 | UNKNOWN (`NEVER_RECEIVED`) | UNKNOWN, no diagnostic |
| `edge-kobo-001` (import) | 60 | registration DISABLED, UNKNOWN | not counted as a source |

Second Site: any other imported Site with only its disabled import gateway reads
`summary.status = NO_REGISTERED_SOURCE`. For an absent battery the second Site needs a Foundation without a
BATTERY component; `without_battery(store, tmp_path, code)` in `backend/tests/test_s7_asset_boundary_postgres.py`
builds one from the KOBO fixture (an unconverted KOBO copy instead gives a configured, `NO_BINDING_SET` battery).

## Read 1: `GET /api/sites/{site_code}/source-health`

`backend/assetops_backend/source_health_api.py`, DTO `evidence/source_health.py::source_health_document`,
schema `{"id": "assetops.site-source-health", "version": 1}`, `rule_id assetops.source-health.two-clock.v1`.
Top level: `site_code, site_id, read_at, read_at_clock, access_basis, claim_scope, not_claimed[],
snapshot{isolation: REPEATABLE_READ, selection: CONSISTENT}, stale_projection{applicable: false, reason},
summary{status NO_REGISTERED_SOURCE|ALL_CURRENT|NOT_ALL_CURRENT, enabled_gateway_count,
disabled_gateway_count, contact_counts{CURRENT,STALE,UNKNOWN}, source_watermark{selected_diagnostic_count,
latest_received_at, selected_diagnostic_ids_sha256}}, gateways[]` sorted by external ID.
Per gateway: `gateway_id, gateway_external_id, mode, registration ENABLED|DISABLED, registered_at,
declared_cadence_seconds, contact{status CURRENT|STALE|UNKNOWN, basis SERVER_RECEIVED_AT, last_received_at,
threshold_seconds, since_last_receipt_seconds, reason}, diagnostic{diagnostic_id, sequence_epoch,
diagnostic_sequence, received_at, observed_at, observed_at_clock, payload_sha256}|null,
reported_facts{status CURRENT|OLD|UNKNOWN, reason, observed_at, fact_age_seconds, receipt_lag_seconds,
clock{offset_ms, trust WITHIN_TOLERANCE|UNTRUSTED|UNKNOWN, reason, tolerance_ms}, queue{count,
oldest_age_seconds, as LAST_REPORTED}|null, disk_pressure{value, as LAST_REPORTED, provenance}|null,
mapping_error_count}, sources[{source_id, source_external_id, registration, reported_contact,
reported_contact_status REPORTED|REPORTED_NEVER_HEARD|NOT_IN_SELECTED_DIAGNOSTIC,
reported_contact_age_seconds, contact_basis GATEWAY_REPORTED_DEVICE_CONTACT}], source_watermark|null`.
Refusals: 401/403 (`finding_api.Access`), 404 unknown/foreign Site, 503 `SOURCE_HEALTH_UNAVAILABLE`
(`gateways: null`), 409 `SOURCE_HEALTH_SELECTION_INCONSISTENT` (`gateways: null`). No `STALE_PROJECTION`
state exists: the UI must not show one. S2 `gateway-health` is unchanged.

## Read 2: battery boundary

`backend/assetops_backend/asset_boundary_api.py`, DTO `sites/battery_boundary.py`, schema
`{"id": "assetops.asset-boundary", "version": 1}`, `rule_id assetops.battery-condition-boundary.w1`.
- `GET /api/sites/{code}/battery`: `configuration CONFIGURED|NOT_CONFIGURED`, `basis{foundation_revision_id,
  foundation_version, binding_set_revision_id|null, binding_set_version, binding_set_foundation_revision_id,
  effective_at, knowledge_at}`, `batteries[{asset_id, asset_code, display_name, detail_path}]`;
  NOT_CONFIGURED has `reason NO_BATTERY_IN_EFFECTIVE_FOUNDATION`, `batteries []`, physical_condition UNKNOWN
  `NOT_CONFIGURED`, and no asset ID.
- `GET /api/sites/{code}/assets/{asset_id}/battery`: `asset{asset_id, asset_code, asset_type, display_name}`,
  `binding_status BOUND|UNBOUND|NO_BINDING_SET`, `bound_channels[{binding_revision_id, role, gateway_id,
  source_id, device_id, signal_id, label}]`, `declared_nameplate{value, unit, label
  DECLARED_FOUNDATION_RATING, foundation_revision_id, component_id}`, `accepted_state_of_charge{included:
  false, reason}`, `physical_condition{status UNKNOWN, reason, missing_causal_inputs[{input, status, reason}]}`,
  `withheld[]`. 404 `ASSET_NOT_IN_EFFECTIVE_BASIS` for foreign/unknown/non-battery asset; 422
  `INVALID_ASSET_ID`; 503 `ASSET_BOUNDARY_UNAVAILABLE`; 409 `FOUNDATION_BASIS_UNAVAILABLE`.

## Open for S7-01b

- Accepted SOC values are not selected (`included: false`); show only the bound channel ID.
- The walkthrough imports from `backend/tests` (precedent `tools/s601b_action_walkthrough.py`).
- `s7-stale-cadence` is STALE only 60 s after `publish` on the real clock; `attest` should assert it.
