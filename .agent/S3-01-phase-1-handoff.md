# S3-01 phase 1 handoff - PARTIAL (stopped at the context budget)

Branch `task/S3-01-dispatch-assessment`. Phase 1 is **not complete**: the role vocabulary and the Foundation property seam landed (1a); the demo-configuration publication, the registered capability publication profile, the `s3-dispatch-cases-v1` producer/manifest and the Candidate before/after proof (1b) are not built. Resume at "Next (1b)". Task file Status stays `active`; no review packet yet.

## Landed (commit `e68da1c`)

- `backend/assetops_backend/sites/binding_roles.py`: `ROLE_SET_MINIGRID_1`, `ROLE_SET_MINIGRID_2`, `ROLE_SET_MINIGRID` (= roles-2, the publish set), `MINIGRID_ROLES_2` = roles-1 + optional `pv_available_power` (INVERTER, kW, ONE) and `pcs_discharge_capability` (POWER_CONVERSION_SYSTEM, kW, ONE); `SERVED_ROLE_SETS_BY_SITE_TYPE`, `serves(site_type, role_set)`.
- `binding_service.py`: `BindingService.publish(..., role_set=None)` - default is the Site type's current set; a named set must be served, else `BINDING_ROLE_SET_UNKNOWN`. `readiness()` reads a selected set under its own `role_set`.
- `binding_conversion.py`: conversion passes the fixture's `role_set`, so the replayed Kobo conversion still records `minigrid-roles-1` (old snapshots/history unchanged).
- `registered_basis.py:150-159`: `SITE_TYPE_ROLE_SET_MISMATCH` now means "Site type does not serve this set" (roles-1 historical bases stay selectable).
- `foundation_content.py::with_component_properties`, `foundation_service.py::publish_component_properties` (shares `_publish_content_change` with `publish_battery_reserve`): later-effective, split-preserving revision; strict parser validates keys/units/sources; `FOUNDATION_NO_CHANGE` on replay. Not exposed as an API route (deliberate: demo configuration only).
- Tests: `backend/tests/test_s3_role_vocabulary.py` (6 pass). Focused binding/foundation/registered-basis/readiness run with Postgres: 396 passed. Full backend run: see "Tests".
- Questions: `.agent/S3-01-questions-1.md` (contradictory case, poor quality, shared epoch, provenance) with fail-closed defaults.

## Survey facts the next agent needs (anchors)

- Template values (authorized demo candidates): `config/site-templates/kobo-mini-grid-60kw.yaml:149-168` - start 35 %, stop 90 %, start-delay 5 min, rated 40 kW, `source: TEMPLATE`, `source_version: 2`. Kobo generator component id `generator`; imported `minimum-runtime` 30 min stays.
- Capability signals: template `pv-inverter-controller/available-power`, `battery-pcs-controller/discharge-capability` (kW); assets `pv-inverter`, `battery-pcs`. Declare via `BindingService.publish(declare=[DeclaredSignal(...)])` with all current bindings + 2 new requests; that call records roles-2 and splits the roles-1 set at the effective instant.
- Models: `mini-grid` v1-v3 need GENERATOR rated-power/sfc/start/stop/min-runtime/start-delay + FUEL_TANK capacity; init states battery SoC, `fuel-tank-volume`, `generator-state` STOPPED (`runs/profiles.py:1124-1320`). Missing property = BLOCKED Draft (`runs/service.py::_freeze_model_needs` :1934). Only `mini-grid` v3 measures `pv-available-power` / `battery-discharge-capability` (`simulator/.../packs/mini_grid.py:1040-1086`); timestep must divide 5 and 30 min.
- Publication profiles: `registered-kobo-publication` v1/v2 (`profiles.py:1796-1843`) are based on Lab **v3** - no generator status, no capability signals. Lab v5 (`:1647-1776`) has status + both capability INTERVAL_SIGNALs + `battery-discharge-capability-reporting-availability` and `battery-soc-publication-delay` states, but also POLICY/OPERATIONAL_RECORD `record_channels` that must **not** be in a registered (measurement-only V3) profile. Register in `PUBLICATION_PROFILES` (:1853).
- Gateway: unbound channel -> held `UNKNOWN_CHANNEL` (`gateway/assetops_gateway/service.py:610-616`) - this is the "Candidate blocked before" evidence; epoch per gateway config (`provisioning.sequence_epoch`), new epoch via `reprovision_epoch` (`EPOCH_REUSED` on reuse); envelopes/batches carry no run field.
- Demo machinery: `tools/s2_demo_walkthrough.py` `Demo` (setup :103-149, start/stop :158-190, issue :247, gateway config :259-275, new_run :322, deliver :299-314, fault_fixture :397-435, readback :620-665). Use a new DB (`assetops_s3cases`), new ports (not 8000/5173/5183/5199/5213/5291, not S2's 8610/8643), new pipe name and a new `--work` dir; stop everything in `finally`.
- Registry: `frontend/docs/architecture/v69-dependency-registry-pilot.json:67` `I-sim-dispatch-cases` has only `capability`; add `acceptance_target` (G5). Layer must stay `producer`; status must equal `I-S3-01`'s (checker :130), so it stays `open`.
- Dispatch-2 rows for expected ceilings: `backend/tests/dispatch_decision_table.md:87-95` (row 3 reserve, row 4 capability shortfall, 5a/5b Candidate with 10 % headroom).

## Next (1b) - in order

1. Demo-config fixture `backend/conversions/kobo-001-s3-dispatch-demo-config.json` + CLI (e.g. `assetops_backend.sites.publish_demo_configuration`): one labelled step at an effective instant after the Kobo import (proposal 2026-10-01T00:00Z) - generator properties via `publish_component_properties`, then bindings roles-2 with the two declared capability channels. Idempotent; prints revision/binding versions. Tests with the in-memory store and Postgres.
2. Publication profile `registered-kobo-publication` v3: v2 + generator status + the two capability signals (resolution `0.000001`, RUN_VIRTUAL) + `battery-discharge-capability-reporting-availability`; no record channels. Host test that a registered `mini-grid` v3 run publishes both capability readings and that, on a roles-1 basis, they are held `UNKNOWN_CHANNEL`.
3. Producer `tools/s3_dispatch_cases.py` (reuse/import S2 `Demo` pieces): setup -> run a generator scenario on the **roles-1** basis before config (capability held; record "Candidate blocked") -> publish demo config -> cases on later windows: Necessary (night, PV 0, SoC near reserve), Candidate (generator charging, SoC > reserve+10, PV avail + discharge cap >= 1.1 x load), missing/poor-quality (capability reporting gap), late/out-of-order (SoC publication delay), overlap (two runs same epoch -> ambiguous) and fault/contradiction fixture epoch (labelled, Q1) -> deliver -> read accepted IDs -> write `fixtures/s3-dispatch-cases-v1.json` (public IDs, Foundation/binding versions, gateway/source IDs, epochs, batch/evidence IDs, expected ceilings, private oracle path separate) -> `verify` subcommand reloads from Postgres and compares IDs. Add a precondition check on accepted public values per case (not the analytic).
4. Registry `acceptance_target` for `I-sim-dispatch-cases`; CODE_STATE entry; review packet for phase 1.

## Tests

Full backend with Postgres (`ASSETOPS_TEST_DATABASE_URL=...assetops_test`) on `e68da1c`: **1766 passed** (296 s). `tools/check-all.ps1 -ExecutionPolicy Bypass`: **all 6 guards passed**. Host, simulator, gateway suites and `tools/check-all.ps1` not yet run for this phase. Known pre-existing: `tests/test_s2_site_evidence_postgres.py:51` raises NameError at collection when `ASSETOPS_TEST_DATABASE_URL` is unset.

## Risks

- `ROLE_SET_BY_SITE_TYPE` now publishes roles-2 for any Foundation-UI binding edit: the edited set changes version silently except in the role-set field; frontend shows `role_set` from the API (`FoundationBindingsPanel.tsx:256`). Reviewer should confirm this is acceptable.
- Same-epoch overlap is inseparable in public data (Q3); phase 2 must treat it as ambiguity.
