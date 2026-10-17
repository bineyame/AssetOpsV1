# W2-02 handoff after spec commit (1) — PARTIAL (context budget)

Branch `task/W2-02-cold-producer`, worktree `AssetOpsV1-review2`. Spec commit (1) landed in `d23db231` and `4906d6a5`. Spec commits (2), (3) and (4) have not started. Resume at spec commit (2), "cold pack/profile/run identity", in `.agent/W2-02-build-spec.md`.

## What landed (commit 1)
- `backend/tests/fixtures/w2/cold-lab-001.yaml`: COLD-LAB-001, built from COLD-001 with the component codes renamed. It carries the thirteen exact properties, and the compressor rating is set to 3 kW to match its cooling capacity.
- `backend/conversions/cold-lab-001-bindings.json`: the eleven channels.
- `sites/binding_service.py:validate_bindings(..., v4_metadata=False)` sets `BindingRow.v4_mapping = V4_CHANNEL_MAPPINGS[...].metadata()` on `cold-roles-1` rows. It refuses with `BINDING_CHANNEL_V4_UNKNOWN` when the tuple is absent, `BINDING_CHANNEL_ROLE_MISMATCH` on a family mismatch, and `BINDING_UNIT_MISMATCH` on a unit mismatch. `publish` passes `v4_metadata = origin != "CONVERSION"`.
  - **Interpretation, which needs Architect confirmation:** the spec says both that the first conversion is "historical v3-compatible" with W2-01 hashes unchanged, and that validate always sets v4. If every cold row got v4, COLD-001's conversion bytes would change, and the 00:01 publish would be refused with `BINDING_NO_CHANGE` (identical digest). Gating on the origin is the only reading under which every sentence of the spec holds.
- `sites/adapters/postgres_foundation_store.py:_select_binding_sets` reads `v4_mapping` back from the set's persisted `snapshot_canonical` bindings. The rows have no column for it; the spec's "persists the row JSON" did not hold for the rows.
- `sites/cold_lab.py`: `install_cold_lab` imports, converts, then runs `publish_v4_revision` at `V4_EFFECTIVE_FROM = 2026-10-01T00:01Z`. It is idempotent, and its CLI is `python -m assetops_backend.sites.cold_lab --tenant demo`.
- `scenarios/cold_parsing.py`: `parse_cold_scenario_document`, `ColdScenarioDefinition`, and the canonical-JSON SHA-256.
  - Canonical decimals follow `is_canonical_decimal`, so `"3"`, `"3.8"`, `"10"` and `"20"` are accepted and `"3.00"` is refused.
  - Instants must be quoted `YYYY-MM-DDTHH:MM:SSZ` strings.
  - Each kind is pinned to one asset and one value or action: PROBE_REPORT → probe-1 with DROP or HOLD; START_RESULT → generator-1 with ADD.
- The six `config/scenarios/cold-*.yaml` documents are in place.
- `yaml_shipped_scenario_store.py` dispatches by `schema`. `ports.AnyScenarioDefinition` is the union, and the service is typed with it.
- Interim guards:
  - `simulator_lab_api.py` leaves cold definitions out of the legacy catalog list, and the legacy detail route returns 404 for them.
  - `runs/service.py:_resolve_scenario` refuses cold with `VERSION_UNAVAILABLE`. Commit (2) must replace this with the cold-only freeze path.
- Legacy tests `test_scenario_fingerprints.py` and `test_run_binds_scenario_to_site.py` now exclude the cold documents.

## Tests run (all passed)
- `test_w202_cold_scenario.py` (3), plus the fingerprints, run_binds and scenarios_api tests: 89 passed.
- Run against a private DB, `assetops_w202c_test` (Docker 127.0.0.1:55432; drop it at the end):
  - `test_w202_cold_lab_bindings_postgres.py` (3), with W2-01 cold foundation and vocabulary: 49 passed.
  - The binding, w200 and run_setup files: 262 passed.
- `tools/check-architecture.ps1` passed.

## Open questions for the Architect (genuinely unspecified)
1. **Lab choices.** "Add the six to the Lab choices only for the registered fixture." `GET` scenarios takes no Site parameter, scenarios name no Site by design, and the frontend lists the catalog unfiltered. What is the endpoint or field shape for presenting cold scenarios, and how is the filter to COLD-LAB-001 expressed? Until this is answered they are left out of the legacy list.
2. **Run request for cold.** `RunSetupRequest` names `model_profile_id/version` explicitly. Does a cold run request still name them, with the cold freeze path checking them against the document? Or does the document's profile triple decide?
3. Confirm the origin-gated v4 metadata described above.

## Next (spec order)
- **(2)** Profiles: `runs/profiles.py` MODEL/PUBLICATION, host `execution_adapter`, `lab_execution`, simulator `gateway/mappings.py`, `kernel/execute.py`. Then `packs/errors.py` (move `PhysicallyUnacceptable` from `packs/fuel.py:73`), `packs/cold.py`, `simulator/tests/test_cold_pack.py`, and the run identity fields in `runs/models.py` and `runs/parsing.py`.
- **(3)** DeviceReportV2 and the gateway `_admit_in` v4 branch (`gateway/assetops_gateway/service.py`, around 647-679), plus the observation transform.
- **(4)** Replay read, manifests, and the full suites.

## Environment notes
- In Git Bash, PYTHONPATH must use `C:/...` paths separated by `;` (not `/c/...`).
- Python: `<wt>/.venv/Scripts/python.exe`.
