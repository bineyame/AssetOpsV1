# S2-01b phase 3a handoff: simulated device resolution profile

- **Branch:** `task/S2-01b-durable-simulated-gateway`
- **Commit:** `aca557a`, on top of `71f1ea1`.
- **Scope:** Q1 and Q3 of `D-2026-10-08-s2-simulated-device-resolution-and-delay-boundary` (`.agent/architect-S2-01b-answers-3.md`).
- **Open questions:** minor fail-closed defaults are in `.agent/S2-01b-questions-3.md`.

## What landed

### Contract (`contracts/assetops_contracts/observation.py`)

- **New functions.**
  - `device_resolution(text) -> Fraction`: a positive finite decimal, never a float or a ratio.
  - `quantize_half_even(value, quantum)`: exact rational round-half-even, via floor plus a remainder compared to 1/2.
- **`DeviceSignalSpec.resolution: Fraction | None = None`.**
  - An ENUM refuses it, through `refuse_numeric_error_on_a_discrete_signal(..., resolution=)`.
  - `as_fields()` appends it only when it is set, so the identity fields of earlier specs are unchanged.

### Simulator (`simulator/assetops_simulator/observation/transform.py`, end of `_attempt`)

- The value is `published = value + bias`. When the signal has a resolution, it is then quantized before the `DeviceObservation` is built.
- The exact world value never leaves the kernel.
- `report_from_observation` and `exact_decimal_text` are unchanged. A quantized Fraction already yields canonical finite text with trailing zeros stripped, and no `-0`.

### Profiles (`backend/assetops_backend/runs/profiles.py`)

- **`DeviceSignalDeclaration.resolution: str | None = None`.** It is validated, and refused on ENUM.
- **`REGISTERED_KOBO_PUBLICATION_PROFILE`** (`registered-kobo-publication` v1):
  - It is `replace(LAB_PUBLICATION_PROFILE /*v3*/)`, with every numeric signal set to `resolution="0.000001"`.
  - It is appended to `PUBLICATION_PROFILES`, so `/run-profiles` lists it.
  - v3/v4/v5 are untouched.
- **`resolve_signal_resolutions(profile)`** builds `FrozenSignalResolution`.

### Run identity (`runs/models.py`, `parsing.py`, `provenance.py`)

- **New record and field.** `FrozenSignalResolution(device_id, signal_id, unit, resolution)` is the record, and `DeterministicIdentity.signal_resolutions = ()` is the field.
- **Serialization.** The field is written only when it is non-empty, so every earlier run document keeps its bytes. A stored `[]` is refused, and so is a non-decimal value.
- **Provenance.** It adds a row with `identity_field="signal_resolutions"` to every run:
  - one row per resolution, answered by `PUBLICATION_PROFILE`;
  - or, when there is none, one row reading "none declared by this profile; readings publish exactly".

### Setup (`runs/service.py::_freeze_signal_resolutions`, called after the registered `signal_mappings` replace)

- **New input.** `RegisteredSiteSelection.source_units` comes from `runs/registered_basis.py`.
- **New refusals in `refusals.py`.**
  - `PUBLICATION_PROFILE_REQUIRES_REGISTERED_SITE`: a resolution-declaring profile used without a registered basis.
  - `PUBLICATION_UNIT_MISMATCH`: a declared unit that differs from the bound signal's `source_unit`.
- Both refusals are reachable in `test_run_setup.py::test_each_kind_has_a_request_that_produces_it`.

### Host

- **`execution_adapter.py::frozen_resolutions(run, profile)`.** The frozen identity is the authority. Any disagreement with the catalog, whether resolution, unit or presence, raises `FrozenRunNotReconstructible`. `reporting_inputs` passes the result into `DeviceSignalSpec`.
- **`lab_execution.py`.** The projection signal rows carry `resolution`, but only when it is set (persisted bytes are unchanged otherwise). The parse back is optional.

### API (`backend/assetops_backend/simulator_lab_api.py`)

- **Run projection.** Each entry of `signals[]` has `resolution`: a string, or `null`.
- **`publication_profile_summary`.** It adds:
  - `device_resolutions[]` with `device_id`, `signal_id`, `unit` and `resolution`;
  - `requires_registered_site: bool`.

### Guard

- `tools/checks/run-setup.ps1` adds `FrozenSignalResolution` to the records that only `profiles.py`/`parsing.py` may construct.
- I proved it non-vacuous: a construction in `service.py` fails the check, and I reverted it.

## Tests

### New files

- **`simulator/tests/test_device_resolution.py`** (21 tests):
  - ties to even, for both signs;
  - near-ties;
  - `1035/19 -> 54.473684`;
  - canonical text;
  - quantum validation;
  - ENUM refusal;
  - unchanged `as_fields` when the resolution is None.
- **`backend/tests/test_s2_registered_resolution.py`** (16 tests):
  - the catalog, where the new profile equals v3 except for the resolution;
  - old profiles declare none;
  - ENUM and invalid resolutions are refused;
  - a registered Draft freezes 8 resolutions, which round-trip;
  - the provenance rows;
  - a v3 registered Draft writes no key;
  - an empty or bad stored list is refused;
  - the unit-mismatch and legacy-Site refusals.
- **`host/tests/test_registered_kobo_resolution.py`** (5 tests, real gateway processes, about 9 s):
  - **Old versus new.**
    - v3 still gives 252 envelopes and 41 `INVALID_VALUE` holds.
    - The new profile gives 293 envelopes and zero holds, with every `REPORTED` value equal to `quantize_half_even(old exact)`. Every other observation field is identical, and exactly 41 of the changed readings were the old holds.
    - Every value matches the canonical-decimal regex.
  - **Replay and restart.**
    - A whole-series replay is `ALREADY_ADMITTED` 293.
    - A gateway restart gives identical message ids, sequences, envelope and batch bytes, and digests.
  - **Process boundary.**
    - No admitted report value equals any exact unrounded value; there are at least 41 such values.
    - No `/` appears in any value.
    - The run id appears in no report text; it is carried only in the admit body's local `lab_run_ref`, as built in phase 2.
  - **Q3 delay window.** I proved this test non-vacuous: with the refusal disabled, it fails.
  - **Host drift.** A host whose catalog disagrees with the frozen resolution refuses.

### Updated

- `backend/tests/test_run_setup.py`: the nested-field classification and refusal-kind reachability.

### Suites

Results are in the section at the end.

## What phase 3b needs

### Run setup UI: select the new profile for the registered Kobo daytime Draft

- `frontend/src/shell/runSetupClient.ts`:
  - `RunPublicationProfile` is at ~l.69-76. Add `device_resolutions` and `requires_registered_site`.
  - `isPublicationProfile` is at ~l.933. Its key check is not exact, so the extra keys already pass.
  - `listProfiles` is at ~l.1581.
  - `RunSetupInput` is at ~l.239. It sends `publication_profile: {profile_id, profile_version}`.
- `frontend/src/shell/RunSetupFrame.tsx`:
  - The dropdown is at ~l.852-877.
  - Auto-select applies only when exactly one profile is listed (~l.346-372).
- Show:
  - the resolution, "0.000001 in each signal's unit, simulated device";
  - the two new refusal kinds. Their messages are self-describing.
- There is no product code that creates a registered Draft. The request shape is `backend/tests/test_s2_registered_basis.py::request` with `publication_profile={"profile_id":"registered-kobo-publication","profile_version":1}`.

### Frozen-inputs summary

- A new "Device resolution" row appears on every run.
- Frontend fixtures that pin frozen-input rows from a live backend may need the row. JSON fixtures are not affected.

### Run projection `signals[].resolution`

Render it beside the bias. Do not state "reported - bias = true" exactly for a quantized run (questions Q4).

### Gateway Stage UI, F1, layout, packet

These are as in the phase-2 handoff, "What phase 3 needs". With the new profile the stage has 293 envelopes and no holds. The holds UI can be shown with the v3 Draft, or with the unknown-channel and unit probes.

## Risks

- **`frozen_inputs` change.** It now always has one more row, which changes a read-model payload for all runs. Stored bytes are unchanged.
- **Resolution in two places.** The resolution lives in the profile and is also frozen per run. The host refuses drift between them, so changing a published profile's resolution later strands its runs, which is intended.
- **Q3 regression shape.** It injects the delay window at the host, because no registered-selectable profile declares a delay state. See questions Q3.

## Suite results

Full runs, all after `aca557a`:

| Suite | Result |
| --- | --- |
| Backend, with `ASSETOPS_TEST_DATABASE_URL` set (Postgres on) | 1630 passed, 0 skipped |
| Host | 638 passed |
| Simulator | 265 passed |
| Gateway | 76 passed |
| `tools/check-architecture.ps1` | passes |
| `tools/check-agent-workflow.ps1` | passes |

The host run is the full host suite, which also covers phase 2's `1d98fa1` fix.

Not run in this phase, because they belong to 3b: the frontend suite, typecheck, the frontend build and layout evidence. Phase 3a changed no frontend code.
