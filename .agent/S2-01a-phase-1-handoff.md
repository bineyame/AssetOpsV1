# S2-01a phase 1 handoff: selection and freeze

Branch `task/S2-01a-registered-lab-basis`. Commits: `ce65b8d` (code), `fabbfc2` (tests, plus a typed refusal for an unparseable Site row), `f1b78bd` (run read reports the basis). Phase 1 is complete. Phase 2 is next.

Questions for the Architect are in `.agent/S2-01a-questions-1.md`. None is blocking; each was built on the fail-closed default:
- Q1: Site-row name, type and time zone are not in the snapshot.
- Q2: the definition of a current versus historical snapshot.
- Q3: run signal mappings come from the registered bindings.

## What landed

### Selection, `backend/assetops_backend/sites/registered_basis.py`
`select_registered_basis` (:76) chooses the Foundation revision with `revision_at`, and the binding set with `binding_set_at`, at the run start as recorded at `knowledge_at`. `knowledge_at` defaults to the store clock's now; a future value is refused.

Setup refuses with a `BasisRefused` code in these cases:
- `FOUNDATION_NOT_REGISTERED` or `BINDINGS_NOT_REGISTERED`: nothing was registered for that period.
- `BASIS_INCONSISTENT`: the selected set names a different Foundation.
- `BASIS_BOUNDARY`: either revision's original `valid_to` is at or before `end_time`. The end instant counts because the kernel can stamp a reading there.
- Any code returned by `acquisition_snapshot`.
- `SITE_RECORD_INVALID`: the current Site row fails the strict parser (Q1).

### Snapshot verification, `sites/binding_service.py`
- `is_current_snapshot` (:761): a set is current when it is not superseded and its period has not ended at now.
- `pinned_identity_problems` (:772): checks the stored document against immutable references. It covers tenant, Site UUID, Foundation and mapping IDs, versions, original valid periods and hashes, the gateway, and the binding rows and their sources.
- `acquisition_snapshot(..., now=)` (:837): a current set refuses on any gap. A historical set refuses only on Foundation-content gaps; current-row gaps (`foundation_content.CURRENT_ROW_GAP_CODES`) go into `Snapshot.current_gaps`. Without `now` the S1 behaviour is unchanged.
- The S1 download and summary pass `now`. Their output adds:
  - the header `X-AssetOps-Snapshot-Selection`;
  - the fields `selection` and `current_registration_gaps`.
- This closes S1-02 n5 for historical selection.

### Run adapter and setup
- `runs/registered_basis.py::RegisteredLabBasis` implements `runs/ports.py::RegisteredBasisPort` (:119). It returns a `RegisteredSiteSelection` (:147):
  - the Site record via `record_at`;
  - signal mappings from bindings that have an asset (`mapping_id` = binding revision ID);
  - a `RegisteredBasis`.
- Error mapping:
  - `BasisRefused` becomes `RunSetupRefused` of kind `REGISTERED_BASIS_UNAVAILABLE`, or `REGISTERED_BASIS_BOUNDARY` for a boundary, with `reason_code` set to the specific code.
  - `FoundationStoreError` becomes `SiteStoreUnavailable` (503, no Draft).
- `runs/service.py`:
  - `_resolve_site` (:466) routes registered codes to `_resolve_registered_site` (:482). That checks the requested `foundation_version` equals the selected one. Legacy codes keep the old path, and `knowledge_at` on a legacy Site is `REQUEST_INVALID`.
  - The registered mappings replace `identity.signal_mappings` (:440).
- `runs/parsing.py`:
  - optional request key `knowledge_at` (`_knowledge_at` :304);
  - `_render_registered_basis` (:886) and `_parse_registered_basis` (:942) are strict on keys;
  - a legacy document round-trips unchanged.
- `runs/models.py`:
  - `RegisteredBasis` (:805): its `__post_init__` re-hashes `snapshot_canonical`, so a tampered stored run is refused on reload.
  - `SimulationRun.registered_basis` (:938) defaults to None.
- `runs/refusals.py`: new kinds `REGISTERED_BASIS_UNAVAILABLE` and `REGISTERED_BASIS_BOUNDARY`. `RunSetupRefused.reason_code` is new.
- Wiring:
  - `main.py` passes `registered_bases=RegisteredLabBasis(registry)`.
  - `simulator_lab_api.build_simulator_lab_router(registered_bases=)` passes it to `RunSetupService`.
  - The 422 detail adds `reason_code`.
  - `run_summary` adds `configuration_basis` (`configuration_basis_payload` :1998): `LEGACY_FILE`, or `REGISTERED` with revisions, hash, instants, byte length and `accepted_evidence: false`.

The imported KOBO-001 Draft, as converted in tests, comes out `READY` with 10 registered links, including `generator-controller/status`, and a 5,562-byte snapshot.

## Tests and checks (actual)

- `backend/tests/test_s2_registered_basis.py` (27, in-memory) and `test_s2_registered_basis_postgres.py` (5, real Postgres) both pass.
- `test_run_setup.py`: the refusal-kind reachability test produces both new kinds through the real adapter.
- `test_s1_cutover.py`: the imported setup refusal is now `REGISTERED_BASIS_UNAVAILABLE` / `BINDINGS_NOT_REGISTERED`, with no Draft created.
- Non-vacuity: each of the four protections below was weakened and the named tests failed. Each was reverted with `git checkout`.
  1. Boundary `<=` changed to `<`: the end-equals-boundary test failed.
  2. Every snapshot forced to current: 4 historical tests failed.
  3. Reload hash check disabled: the reload-tamper test failed.
  4. Identity check skipped: the forged-gateway test failed.
- `tools/check-architecture.ps1` and `tools/check-agent-workflow.ps1` pass.
- Full suites at `f1b78bd`, with Postgres tests enabled:
  - backend 1609 passed;
  - host 619 passed;
  - simulator 244 passed;
  - frontend: build ok, vitest 1182 passed (49 files).
- Layout evidence was not run, because phase 1 has no UI change.

## What phase 2 needs

- **Execution guards.** `simulator_lab_api.py::_refuse_if_imported` (:2540, called at :2801/2885/2905/2920) still refuses start, step, run-to-end and Commit for every imported code, including new registered Drafts.
  - Start, step and run-to-end should pass for a Draft whose `record.registered_basis` is not None. They should refuse a pre-import YAML Draft of an imported code, as `LEGACY_FILE`.
  - Commit refuses every imported run.
  - `tools/checks/configuration-persistence.ps1` rule 8 (≈:675) requires `_refuse_if_imported(record)` in each of the four POST routes. Amend it, keeping one shared boundary call, rather than weakening it.
- **Stage read.** `_frozen_basis` (:2656) always reports `configuration_store: "LEGACY_FILE"`. Phase 2 must branch on `record.registered_basis`: registered, with no accepted-evidence claim.
- **Kernel.** The host reads `deterministic_identity.signal_mappings` (`host/execution_adapter.py:584`). For registered Drafts these are now binding-derived links (Q3); confirm the Kobo kernel and observation path behave the same.
- **Frontend.** The Lab setup does not yet list imported KOBO-001 or show the basis. `configuration_basis` is on the run read, and the setup refusal carries `refusal_kind` and `reason_code`. `knowledge_at` stays API-only.

## Open risks

- Q1: a historical selection still depends on the current Site row (name, type, time zone). An unparseable row gives a typed refusal, never a substitute.
- Asset codes for mappings are looked up from current `asset` rows by the pinned UUID (Q3).
- `knowledge_at` default carries microseconds (stored pattern allows `.ffffff`); request values must be whole-second `Z`.
- In Postgres every Kobo source is held by a binding FK, so the only permitted current-row edits are gateway identity and Site row. The source-rename gap path is proven in-memory only.
