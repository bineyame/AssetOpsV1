# W2-05a phase handoff - run 4 (spec commits 1-3 landed; QE-QG applied)

Branch `task/W2-05a-ev-foundation`, worktree `AssetOpsV1-review5`. Commit 1 `2d8b323d`; QC/QD `932ad981`; commit 2 `880384d3`; main merged with the QE-QG amendment; spec commit 3 `5a7b46c6`. Architect rulings Q1-Q8, QA-QG live in `.agent/W2-05a-build-spec.md` (`D-2026-10-18-w2-05-buildspec`).

## What landed in commit 3

- `backend/assetops_backend/ev_foundation_api.py:build_ev_foundation_router` - `GET /api/sites/{site_code}/ev/foundation?at=`, the cold Access/source gate: 401 `UNAUTHENTICATED`, 403 `SITE_SCOPE_FORBIDDEN`, 404 `SITE_NOT_FOUND` (unknown or non-EV after access), 422 `EV_SELECTION_INVALID` (bad `at`, extra or repeated field), 503 `EV_FOUNDATION_UNAVAILABLE` (Foundation store or gateway-health read). No revision at `at` passes `FoundationRefused` through (404 `FOUNDATION_REVISION_NOT_FOUND`), as cold does. `ev_contact` maps the cold `contact_document` to `{state,as_of,gateway_id,reason}`; gateway = binding set's gateway, else the single registered one. Included in `main.py` after the cold router.
- `sites/ev_foundation.py:ev_foundation_document` - pure projection with the spec's exact fields. `_gap_items` is the one gap list behind both `ev_blocking_gaps` (Draft gate, output unchanged) and the read. Nonblocking: `SITE_IMPORT_NOT_BOUND` (no `ev_site_import` binding), `SOURCE_NOT_CONTACTED` (contact `NEVER`), `COMMISSIONING_UNCONFIRMED` (always). Messages use the cold shape `{code,role,component_id,asset_id,message,blocking}`. Decimals via `_decimal_text` ("80", "0.001"); cadence `_seconds` = min x 60 (int when whole). QE: Site import = min connector `ev-meter-cadence`.
- `sites/cold_foundation.py:topology_parts` - the cold topology builder extracted unchanged and shared (cold tests green).
- QG: `binding_service.py:validate_bindings` refuses `BINDING_SOURCE_ASSET_MISMATCH` for `ev-roles-1` when `SourceRow.asset_id != asset.id`. QF: no code change needed (publish passes `v4_metadata=True`, so a tuple outside the EV profile already gets `BINDING_CHANNEL_V4_UNKNOWN`); test added.
- Tests: `test_w205a_ev_foundation_api_postgres.py` (9: stocked exact values, contact RECENT/STALE/NEVER, three missing-binding revisions at pinned `at` with the original still READY, optional Site import absent, missing-limit revision, QE minimum cadence, all refusals); `test_w205a_ev_foundation_postgres.py` +3 (QG x2, QF); `test_w205a_ev_roles.py` +1 (main serves the route).

## Interpretations to confirm at review (not blocking)

- `enabled_schedule` = `{enabled, time_zone, weekly}`, where `enabled` is the connector's `ev-connector-enabled`; null when the connector has no schedule entry. `ev-clock-error-bound` and the cadence minutes are not echoed outside `bindings[].cadence_seconds`; the spec's field list has no slot for them.
- `feed` is always an object (`asset_id` null when no feed); `meter_asset_id` is the single METER fed by the feed over AC, else null. Connectors are listed under their charger (SIGNAL edge); the validator refuses orphan connectors.
- Contact freshness is measured at request time (`clock()`), as the cold read does, not at `at`.

## Checks (run 4)

- Postgres `assetops_w205a_test`: API file 9 passed; EV Foundation file 11 passed; with cold Foundation, S1 bindings, W2-02 replay, EV roles and vocabulary: 152 passed. Roles + health 26 passed.
- Non-vacuous: QG check disabled -> both QG tests fail; Site import cadence from bound asset -> QE test fails; reverted via `git checkout`.
- `tools/check-all.ps1`: 10/10.

## Next: spec commit 4 (UI routes and captures)

Per the spec section "Three routes and fidelity proof" and the brief's UI phase rules: client for this read; `ev-foundation`, `ev-readiness`, `ev-sld` via `SiteFoundationFrame.tsx` and the `ColdFoundationViews.tsx` pattern; `APPROVED_TITLE_CHANGES` for `ev-readiness:2` and `ev-sld:1` (append only - W2-04 owns the shared file); `evFoundation.test.tsx` with `expectV69Panels` stocked/missing-role/403/503 plus planted-panel failure; 1440/390 captures with `tools/w1-fidelity-evidence.mjs` (ports 9800-9850 / 6200-6250).

Later: commit 5 is `0024_w2_ev_config` after W2-04's `0023` is merged here; then final guards, one full backend suite and host suite (check no other pytest is running first), frontend suite and the packet.
