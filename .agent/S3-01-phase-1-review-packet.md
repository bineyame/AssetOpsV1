# S3-01 phase 1 review packet - `I-sim-dispatch-cases` (phases 1a + 1b)

Task: `tasks/S3-01-dispatch-assessment.md`, phase 1 ("Role vocabulary and fixture"). Status stays `active`; this phase gets a fresh Claude review before phase 2. USER_REVIEW_REQUIRED for the task: true (owner checkpoint is at task close, not this phase).
Branch `task/S3-01-dispatch-assessment`; commits `e68da1c` (1a) and `7e9da8c`, `4ce6e69`, `38d851b`, `677875d`, `0f68635`, `f508bae`, `eb29aaf` (1b).
Authority: `D-2026-10-11-s3-dispatch-interval-assessment`, `.agent/architect-S3-dispatch-answers.md`, `D-2026-10-08-s2-registered-kobo-demo-configuration`; open questions `.agent/S3-01-questions-1.md` Q1-Q6 (unanswered, fail-closed defaults built).

## Outcome delivered

A registered KOBO-001 gains `minigrid-roles-2` and a labelled simulated demo configuration; registered `mini-grid` v3 runs publish both capability channels through `registered-kobo-publication` v3; `tools/s3_dispatch_cases.py` produces the replayable `s3-dispatch-cases-v1` manifest with eight named cases, all through the registered gateway, sealed Batch V2 over TLS and central acceptance (except the labelled contradiction fault fixture, Q1), and `verify` reloads every case's accepted IDs from Postgres. No analytic, persistence or UI (phases 2-3).

## Files materially changed

- `backend/assetops_backend/sites/binding_roles.py`, `binding_service.py`, `binding_conversion.py`, `registered_basis.py` (1a) - roles-2 vocabulary, served sets.
- `backend/assetops_backend/sites/foundation_content.py`, `foundation_service.py` (1a) - `publish_component_properties`.
- `backend/assetops_backend/sites/demo_configuration.py` (new) + `backend/conversions/kobo-001-s3-dispatch-demo-config.json` (new).
- `backend/assetops_backend/runs/profiles.py` - `REGISTERED_KOBO_PUBLICATION_PROFILE_V3`.
- `config/scenarios/kobo-s3-dispatch-degraded-reporting.yaml` (new; pinned in `test_scenario_fingerprints.py`, listed in `test_run_binds_scenario_to_site.py`).
- `tools/s3_dispatch_cases.py` (new).
- `frontend/docs/architecture/v69-dependency-registry-pilot.json` - `I-sim-dispatch-cases.acceptance_target`.
- Tests: `backend/tests/test_s3_role_vocabulary.py` (1a), `backend/tests/test_s3_demo_configuration.py`, `host/tests/test_s3_registered_capability_publication.py`.
- Evidence: `.agent/S3-01-dispatch-cases-run.txt`, `.agent/S3-01-dispatch-cases-v1.manifest.json`.

## Acceptance criteria (phase 1)

| Criterion | Status | Evidence |
| --- | --- | --- |
| `minigrid-roles-2` with optional `pv_available_power` (INVERTER, kW, ONE) and `pcs_discharge_capability` (PCS, kW, ONE); roles-1 readable | Met | `binding_roles.py`; `test_s3_role_vocabulary.py`; roles-1 bases at 10-01 still selected (run log step 4) |
| Each capability channel has a registered simulated binding/source and accepted report | Met | demo config binds `pv-inverter-controller/available-power`, `battery-pcs-controller/discharge-capability` (existing sources); main case accepts both roles (manifest `two-capability-candidate.roles`) |
| Observed `pv_power`/`battery_power` are not capabilities; no static/Lab value fills a missing channel | Met | separate roles; roles-1 run accepts zero capability readings (case `candidate-blocked-before`) |
| Versioned manifest names Foundation/binding revisions, gateway/source IDs, batch/evidence IDs, epochs, expected ceiling, private oracle location separately | Met | `.agent/S3-01-dispatch-cases-v1.manifest.json` (`site`, `demo_configuration.periods/as_published`, per-case IDs, `private_oracle`) |
| Cases: physical Necessary; two-capability Candidate; missing/poor-quality; contradictory same-role; late/out-of-order; overlapping-run/fault-epoch isolation | Met with named limits | 8 cases, all preconditions met on accepted public values; limits: contradiction is a labelled fixture (Q1), poor quality = UNAVAILABLE + gap (Q2), late but not out-of-order within a source (Q5) |
| Every public report through registered gateway -> sealed Batch V2 -> central acceptance; fault fixture labelled, never blended | Met | run log: 1,387 sealed batches over 7 runs, every pass `refused 0 retrying 0`; fixture under `s3-contradiction-fixture-epoch`, its own window (10-06), `fault_fixture: true` |
| Manifest replayable; compares accepted IDs after reload | Met | `verify` in a fresh process: 8/8 match, `all evidence digest match=True`, `VERIFY PASSED`; tampered manifest -> `VERIFY FAILED: ['physical-necessary']` |
| Candidate blocked before both channels exist and available after acceptance | Met | 10-01 roles-1 run: generator RUNNING at 20 instants, capability roles `[]`, rows 5a/5b unsatisfiable; 10-02 roles-2: row 5b at 13 instants, 5a at 15 |
| No analytic cutover | Met | no analytics/Performance code touched |
| Registry `acceptance_target` for `I-sim-dispatch-cases` (G5) | Met | registry guard passes; status stays `open` (tied to `I-S3-01`) |

## Case summary (final run, HEAD `0f68635` tree)

| Case | Window (UTC) | Epoch | Accepted | Expected claim ceiling |
| --- | --- | --- | --- | --- |
| candidate-blocked-before | 10-01 03-11 | epoch-1 | 260 | Indeterminate: missing capability roles |
| physical-necessary | 10-02 03-11 | epoch-1 | 326 | Necessary (rows 3: 5 instants, 4: 3 instants) |
| two-capability-candidate | 10-02 03-11 | epoch-1 | 326 | Candidate, bounded segments |
| missing-poor-quality | 10-03 03-11 | epoch-1 | 322 | Indeterminate across 06:00-06:45 gap; 8 UNAVAILABLE |
| late-out-of-order | 10-03 03-11 | epoch-1 | 322 | late SOC 07:00 published 07:10 |
| overlap-same-epoch | 10-04 03-11 | epoch-1 x2 runs | 654 | Limited/Indeterminate, ambiguity named (325 doubled channel-times, 42 differing) |
| overlap-separable-epoch | 10-05 03-11 | epoch-1 + epoch-2 | 656 | one cohort per epoch |
| contradiction-fault-fixture | 10-06 05:00 | fixture epoch | 2 | Indeterminate: contradictory SOC 91.75 / 99.25 |

Preconditions are computed from accepted public values only (`classify_public`: dispatch-2 rows 3/4/5a/5b at 15-min instants while generator status is RUNNING; reserve from the selected Foundation revision, 30 %). They are fixture checks, not the `dispatch-3` analytic.

## Checks run

- Backend, Postgres on (`ASSETOPS_TEST_DATABASE_URL=...assetops_test`): `1770 passed` (318 s).
- Host: `666 passed` (398 s). Simulator: `265 passed`. Gateway: `164 passed`.
- `tools/check-all.ps1 -ExecutionPolicy Bypass`: `All 6 guards passed`.
- Producer: `tools/s3_dispatch_cases.py run` exit 0 (224 s), separate `verify` exit 0; no process left on 8710/8743.
- Non-vacuity: dropping the discharge-capability binding from the demo fixture fails `test_s3_demo_configuration.py` (2 failed) and `test_s3_registered_capability_publication.py` (2 failed); reverted with `git checkout`. Tampered manifest fails `verify`.
- Layout evidence: not applicable (no UI change).

## Known deviations

- **Candidate-blocked mechanism.** The handoff expected a gateway `UNKNOWN_CHANNEL` hold; the Lab publishes only basis-mapped signals (`host/execution_adapter.py:690-705`), so on roles-1 capability readings never reach the gateway. The proof is absence of capability roles in accepted evidence plus the roles-1 basis, not a hold.
- **Two effective instants.** Generator values from 2026-10-01, roles-2 bindings from 2026-10-02 (`--steps properties` first), because `mini-grid` blocks without generator values; this lets a generator run on a roles-1 basis before any capability channel exists.
- **Profile v3 also moves generator power to 15 min** (Lab v4's cadence) so status and power share instants; not named in the task.
- **New scenario** `kobo-s3-dispatch-degraded-reporting` v1: `kobo-mini-grid-degraded-evidence` minus the override and its record (V3 is measurement-only).
- **Out-of-order** (Q5): not produced; recorded `out_of_order_within_source: false`.
- **`fuel_level`** (Q6): not published by these runs; unused by dispatch.

## Residual risk

- Manifest IDs are environment-specific (fresh import each `run`); phase 2 must consume the manifest of the environment it tests, or regenerate.
- Same-epoch overlap is inseparable in public data; phase 2 must not split it by sequence or receipt.
- Any Foundation-UI binding edit on a MINIGRID Site now records roles-2 (1a carry).
- Overlap-b and separable-epoch-2 use `kobo-mini-grid-stop-60` (a `mini-grid` v2 scenario) on `mini-grid` v3; READY and executed, but its stop-threshold forcing is a scenario cause, not a public record.

## Reviewer focus

1. The fixture boundary: precondition helpers vs the phase 2 analytic (`tools/s3_dispatch_cases.py::classify_public`).
2. Q1-Q6 defaults, especially the fault-fixture contradiction and the absent out-of-order case.
3. Private oracle separation in the manifest (`private_oracle` only holds Lab run IDs and the Lab store path).
4. `registered-kobo-publication` v3 contents (`profiles.py`, after v2) and that v1/v2 are untouched.
