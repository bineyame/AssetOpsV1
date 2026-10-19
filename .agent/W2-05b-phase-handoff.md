# W2-05b phase handoff - run 1 (stopped on rulings; no product code)

Branch `task/W2-05b-ev-producer` from main `ed57b2f4`, worktree `AssetOpsV1-review5`.

## Done
- Read task, build spec (dry-read + Run 8 amendment), EV design §3, ROLE_CONFIG sections, cold producer.
- Spec commits 1 and 2 **not started**: 14 unruled items in `.agent/W2-05b-pending-rulings.md`
  (document `window` shape, same-minute forcing kind rank, forcing/observation vocabularies and value
  types, `scenario_version`, observation SHA row form, Lab frame placement and copy, catalog route
  403/404 codes and row shape, profile registry copy, pack states outside the six cases).
- Focused tests: none run (no code). `toolseck-all.ps1`: 10/10 passed on this head. No tsc (frontend untouched).

## Anchors for commit 1 (cold precedent to mirror)
- Parser: `backend/assetops_backend/scenarios/cold_parsing.py` (constants :21-25, key sets :27-33,
  `scenario_digest` :100, `observation_sha256` :104, `parse_cold_scenario_document` :124). Errors are
  `ScenarioConfigurationInvalid` (`scenarios/ports.py:57`); union `AnyScenarioDefinition` :35.
- Loader dispatch: `scenarios/adapters/yaml_shipped_scenario_store.py:95-113`.
- Catalog route: `simulator_lab_api.py` `COLD_SCENARIOS_ROUTE` :231, labels :233, handler :2626-2681 in
  `build_simulator_lab_router` :2403; legacy list excludes cold :2618-2623, detail :2710; mounted
  `main.py:462`. Tests `backend/tests/test_w202_cold_scenarios_api.py`.
- Freeze: `runs/service.py` `_create_cold_draft` :491 (request-vs-document :518-534, SHA :574, obs
  :559/:589-591), routing :425-437, `_resolve_scenario` :713/:725. Fields already exist:
  `runs/models.py` `FrozenScenarioBinding.scenario_sha256` :342, `FrozenProfileBinding.observation_*`
  :375; `runs/parsing.py` `_render_present` :1219 omits None, `_parse_cold_identity` :1224 (all-or-none,
  `_COLD_PROFILE_KEYS` :1216) - needs an EV-aware variant. Fingerprint `runs/source_publication.py:27`.
- Profiles: `runs/profiles.py` `COLD_THERMAL_MODEL` :2026, `COLD_PUBLICATION_PROFILE` :2043, tuples :2064/:2075.
- Frontend: `frontend/src/shell/simulatorLabRoutes.tsx` :113/:122/:270/:392-405,
  `coldScenarioChoiceClient.ts` (:49 shape check, :61), `ColdRunSetupFrame.tsx` (:58 copy, :139-156 stale
  drop), `SimulatorLabFrame.tsx:92-100`; tests `coldRunSetup.test.tsx`, `coldScenarioChoiceClient.test.ts`.
- EV inputs from 05a: `sites/ev_lab.py:25` `EV_LAB_SITE_CODE`; `contracts/.../source_envelope_v4.py:600`
  `V4_EV_MAPPING_PROFILE_ID`; fixture `backend/tests/fixtures/w2/ev-lab-001.yaml`.

## Anchors for commit 2
- Pack precedent `simulator/assetops_simulator/packs/cold.py` (`MODEL_PROFILE` :31, `ColdState` :174,
  `ColdPack` :253, `run_window` :441); `packs/errors.py:10`; test `simulator/tests/test_cold_pack.py`.
- Kernel `simulator/assetops_simulator/kernel/execute.py` `COLD_PROFILE_PAIR` :1972,
  `execution_path_for` :1979; host `host/execution_adapter.py:127-161`, `host/lab_execution.py`
  `_is_cold` :2128 / start branch :2205; observation `observation/transform.py:350`.

## Anchors for commit 3 (public transform / v4 mapping / gateway Stage)
- `simulator/assetops_simulator/gateway/mappings.py:175,189` (cold mapping keyed `("cold-publication",1)`);
  `contracts/assetops_contracts/source_envelope_v4.py:600,685,693` (EV mapping tables);
  `contracts/assetops_contracts/gateway_report.py:DeviceReportV2`; `host/cold_publication.py`;
  `host/lab_execution.py:_stage_registered_virtual_cold` :2335.

## Next
Architect rules Q1-Q14 (amend the build spec), then a fresh run builds commit 1, then commit 2.
