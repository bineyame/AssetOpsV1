# W2-01 phase 1 handoff (backend: persisted cold configuration and selected read)

Status: phase 1 complete on `task/W2-01-cold-foundation`. Phase 2 (frontend routes) not started. Nothing merged.

## What landed

- `backend/migrations/versions/0021_w2_cold_config.py`: no-op SQL revision after `0020` anchoring the code-owned cold vocabulary; downgrade touches no row. Head assertions in six Postgres modules moved to `0021_w2_cold_config`.
- Vocabulary (`backend/assetops_backend/sites/models.py`): component types `TEMPERATURE_PROBE|COMPRESSOR|TRANSFER_SWITCH` (COLD_ROOM existed), node roles `COLD_ROOM|SENSOR|COOLING|SWITCH`, media `SIGNAL|THERMAL`, `SIGNAL_UNITS` `event`, `RATING_UNITS` `degC`, the 13 `cold-*` properties, `COLD_PROPERTY_CARRIERS`, `SIGNED_PROPERTY_UNITS={degC}`. `foundation_parsing.py` `UNIT_RANGES` gains the six design ranges; negative values allowed only for degC (old properties keep the nonnegative rule).
- `sites/binding_roles.py`: `Role.value_kind` EVENT, `Role.states` (role-specific ENUM members), `Role.event_kinds`; immutable `COLD_ROLES_1` (`cold-roles-1`, 14 roles, `backup_start_event` + `grid_power_event` per the W2-02 channel closure; the two policy roles are FOUNDATION_CONTROL); registered in `ROLE_SET_BY_SITE_TYPE` and `SERVED_ROLE_SETS_BY_SITE_TYPE`; `COLD_PERIODIC_CADENCE_SECONDS=300`; `conversion_problem` accepts the event IDENTITY triple only on EVENT roles and checks ENUM against `role.enum_states`.
- W2-00 review Low 2 folded: `ChannelMapping.role` in `contracts/assetops_contracts/source_envelope_v4.py` names the cold role of every cold tuple (EV tuples None until W2-05a); `evidence/ledger.py` `_decide_v4` refuses `MAPPING_INCOMPATIBLE` when the pinned row's role differs; `binding_service.validate_bindings` refuses `BINDING_CHANNEL_ROLE_MISMATCH` for cold-roles-1 when a closed-table channel is bound to another role or event-kind set.
- Cold Foundation validator `sites/cold_foundation.py:79` (`validate_cold_foundation`), called from `site_parsing.parse_site_document` for COLDCHAIN, so it runs on import and on every later revision (`record_at`). Carrier types, >0/>=0 rules, ordered policy/control bands, hysteresis inside control band, node role per type, medium endpoint pairs (`COLD_EDGE_TYPES`), unique `(from,to,medium)`, one primary probe per room/room per probe, DAG.
- `FoundationService.publish_topology` (`sites/foundation_service.py:477`): later-effective topology revision through the existing split/supersede path (used by tests/fixtures; no operator route).
- Fixtures: `backend/tests/fixtures/w2/cold-001.yaml` (complete) and `cold-002.yaml` (no chamber probe), bindings `backend/conversions/cold-001-bindings.json` (11 bindings) and `cold-002-bindings.json` (9: no chamber_temperature, no transfer_result). Published through `import_site` + `binding_conversion.convert`.

## Read route (phase 2 contract)

`GET /api/sites/{code}/cold/foundation?at=<UTC Z>` — `backend/assetops_backend/cold_foundation_api.py:47`, registered in `main.py:377`, body built by `sites/cold_foundation.py:222` (`cold_foundation_document`).

```
{foundation_revision_id, valid_from, valid_to,
 rooms:[{asset_id, policy:{low,high,unit:'degC',revision_id}, probe_ids:[asset ids], compressor_ids:[asset ids]}],
 topology: null | {nodes:[{node_id,component_id,asset_id,component_type,display_name,node_role}],
                   edges:[{connection_id,from_node,to_node,medium}]},
 bindings:[{role,asset_id,source_id,unit,cadence_seconds:300|null,publication_mode:'periodic'|'transition'}],
 readiness:{state:'READY_TO_REPORT'|'CONFIGURATION_INCOMPLETE',
            messages:[{code,role,component_id,asset_id,message,blocking}]},
 commissioning:{state:'UNCONFIRMED',evidence_ids:[]},
 contact:{state:'RECENT'|'STALE'|'NEVER'|null, as_of, limitations:[...]}}
```

Message codes: `PROBE_MISSING`, `POLICY_MISSING`, `START_EVENT_MISSING` (design verbatim text), `TRANSFER_UNREPORTED` (verbatim, `blocking:false`), `ROLE_UNBOUND` ("Bind the <role label>"), `ROOM_MISSING`. Refusals `{error:{code,message}}`: 401 `UNAUTHENTICATED`, 403 `SITE_SCOPE_FORBIDDEN`, 404 `SITE_NOT_FOUND` (unknown or non-COLDCHAIN) / `FOUNDATION_REVISION_NOT_FOUND` (no revision at `at`), 422 `COLD_TIME_INVALID` / `COLD_PARAMETER_UNKNOWN`, 503 `COLD_FOUNDATION_UNAVAILABLE` / `GATEWAY_ACCESS_UNAVAILABLE`.

Title inputs for phase 2: Site name from the existing Site read (`/api/sites/{code}`); the gateway has no display name in the store (`GatewayRow` has `gateway_external_id` only; `/api/sites/{code}/gateway-health` serves it); the Foundation declares no topology type, so `cold-sld:1` falls back to the Site name alone.

## Seeding the dev server (Site codes COLD-001, COLD-002)

After `alembic upgrade head`, tenant `demo`, from the worktree root with the usual PYTHONPATH and `ASSETOPS_DATABASE_URL`:

```
python -m assetops_backend.sites.import_kobo --source backend/tests/fixtures/w2/cold-001.yaml --tenant demo
python -m assetops_backend.sites.convert_kobo_bindings --fixture backend/conversions/cold-001-bindings.json --tenant demo
python -m assetops_backend.sites.import_kobo --source backend/tests/fixtures/w2/cold-002.yaml --tenant demo
python -m assetops_backend.sites.convert_kobo_bindings --fixture backend/conversions/cold-002-bindings.json --tenant demo
```

Not exercised against a dev database in phase 1 (tests call the same `import_site`/`convert` functions); phase 2 should confirm the CLI run. Both fixtures are valid from `2026-10-01T00:00:00Z`; contact is `NEVER` until a gateway diagnostic exists.

## Tests run (private DB `assetops_w201_test`, serial)

- New: `tests/test_w201_cold_vocabulary.py` (28 passed, no DB) and `tests/test_w201_cold_foundation_postgres.py` (16 passed): complete/missing-probe persist and reload, old/current selection (policy, bindings, topology) with history kept, refusals (low>=high, wrong unit, duplicate probe-room link, duplicate edge, back edge/cycle guard, undeclared node/transfer, stale/overlapping/role-conflict bindings, channel-role mismatch, foreign-Site asset), read 401/403/404 (unknown, MINIGRID, before first revision)/422/503, contact RECENT/STALE/NEVER/null, tenant/Site-scoped health call, migration 0021->0020->0021 with row snapshots unchanged and KOBO/cold reads after.
- Adjacent, one serial run of 33 modules (S1/S2/S3 role and demo config/S4 migrations/S405/S7/W2-00/W2-01/template and parsing modules): 781 passed, 10 failed, 647 s wall. All 10 failures were in `test_w200_source_events_postgres.py`: its test-only basis injected roles `test-<device>-<signal>`, which the new Low-2 role check refuses. Fixed by having it use the table's role; rerun of that file: 13 passed. Every other module passed on the first run.
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed. Full backend suite: not run (per dispatch).

## Known deviations (for review)

1. Field additions beyond the route row, each required by section 3 D-I: `bindings[].cadence_seconds` (D-I supersedes the row's `cadence`) plus `publication_mode`; `contact.limitations` (holds "Contact time cannot be verified"); `contact.state=null` with limitation "Gateway contact is not available" when no gateway-health store is configured (the enum has no UNKNOWN and NEVER would be a false claim). Topology node/edge and message object shapes are not specified by the design; chosen as above.
2. Copy not specified by the design: `ROLE_UNBOUND` messages ("Bind the compressor state", etc.) and `ROOM_MISSING` "Declare a cold room". Plain-language pass may reword.
3. Event outcome allowlists are taken from the closed v4 kind-to-outcome table (`V4_EVENT_OUTCOMES`) rather than duplicated per role; roles carry `event_kinds` only.
4. Cold binding rows do not persist v4 metadata (no column, W2-00 deviation 7); W2-01 does not attach `v4_mapping` at publish. W2-02 must derive or persist it for snapshot/ledger use. The ledger role check is live for any pinned v4 row.
5. COLDCHAIN topology media/endpoint pairs are restricted to exactly the section 3 A pairs (no DC/FUEL edges, no meter->bus). The type table admits no cycle, so the DAG check is a second guard (proved by widening the table in a test).
6. `configuration_gaps` still returns `SITE_TYPE_UNSUPPORTED` for COLDCHAIN, so the acquisition snapshot download refuses cold Sites; W2-02 needs a cold branch there. The MINIGRID `readiness()` is untouched; cold readiness lives in `cold_foundation.py`.
7. Contact uses current gateway facts (not historical at `at`), matching the existing gateway-health read.
8. No rule-8 probe was run: no writer or SQL changed in `backend/assetops_backend` (fixtures publish through `FoundationService`/`BindingService`). No new guard added.

## Risks / next

- Phase 2 builds the three routes against this body; field names above are the contract.
- The full backend suite has not been run (per dispatch); it is due on the final slice revision.
