# T018 - Executable Scenario Contract

Status: planned
USER_REVIEW_REQUIRED: true

Intended branch: `task/T018-executable-scenario-contract`

## Feature

Scenario Catalog And Run Setup.

## UI-Verifiable Screen Behavior

The Fuel Loss Event detail no longer presents accepted T017 semantics as
provisional. It shows, for every public timeline entry and parameter, whether
the value is an executable causal input, external forcing input, reported
observation input, or non-executable evidence condition. The screen explains
which inputs initialize a future run and which describe later observations; it
does not claim that a run exists.

## Why This Is Next

T017 settled scenario identity, taxonomy, and the public/private boundary but
did not settle execution meaning. Run setup cannot freeze honest inputs while a
timeline row can ambiguously prescribe both a cause and its expected result.
The shipped Fuel Loss example currently makes that risk concrete: starting fuel
and declared generator consumption/removal imply a different later tank level
from the public post-gap and hand-inspection values unless another cause or
observation interpretation is made explicit.

## Acceptance Criteria

- Each public parameter and timeline entry has one machine-readable execution
  role: causal input, external forcing input, reported observation input, or
  non-executable evidence condition. Forcing may influence private state;
  reported observations cannot initialize or mutate private state.
- Private expectations remain test-oracle metadata and never become runtime
  inputs, public provenance, evidence, or product conclusions.
- Initial fuel and every other initial world value have declared ownership:
  Site/Foundation fact, scenario input, run override, or versioned model rule.
- Observation cadence, reporting gaps, and authored reported values have
  explicit machine-readable ownership and timing. Foundation declares that a
  signal can report, but currently declares no cadence; T018 must not derive
  cadence from a device name, display text, or timeline spacing.
- Quantity and rate units are canonical and convertible without display-text
  parsing. Point events and window events have distinct validated semantics.
- Event dispatch semantics use the run's half-open time model and specify how a
  boundary event is applied exactly once.
- Fuel capacity, insufficient-fuel, delivery overflow, and invalid-rate cases
  have explicit executable semantics. A later kernel must fail or apply an
  accepted bounded transition visibly; it may not choose a silent clamp or
  silently discard quantity.
- The Fuel Loss contract resolves the apparent 254 L versus 155/150 L conflict:
  later values are either explicitly reported/external observations, or every
  additional causal input needed to compute them is modeled. They never
  silently prescribe private tank state.
- The post-gap fuel level is a device observation input with the configured
  device/signal identity it reports through. The hand inspection is a manual
  operational observation with an explicit non-device source identity; neither
  is a private-state transition input.
- Baseline load and irradiance are explicit forcing inputs with defined
  point/window shapes. The first kernel may expose a forcing as runtime
  environment state without claiming a complete power-flow consequence, but it
  may not ignore an entry classified as executable. Unsupported required input
  makes later run setup `BLOCKED`.
- Scenario detail/API payloads expose the execution role and timing semantics
  needed by later run setup without exposing private expectations to normal
  product consumers.
- Accepted T017 review markers and provisional wording are removed without
  changing the accepted versioning, taxonomy, or public/private vocabularies.
- The screen remains intention/authoring only: no Draft run, execution,
  runtime state, gateway publication, ingestion, Finding, or conclusion.

## Protected Seams

- Authored causes are distinct from computed state trajectories.
- External/reported observations are distinct from private world truth.
- Scenario private expectations remain outside runtime and evidence paths.
- Scenario identity remains distinct from Site and future run identity.

## Focused Proof

- Strict-parser/API tests cover execution roles, canonical units, point/window
  timing, initialization/observation-source declarations, cadence ownership,
  and malformed combinations.
- A scenario-contract test accounts for every Fuel Loss public value and proves
  that no observation or evidence-condition value reaches initialization or
  the private-state transition inputs.
- Frontend tests show the accepted contract and no remaining provisional
  language while retaining the T017 vocabulary and leakage guards.
- Run architecture and workflow checks.

## Scope Limits

- No SimulationRun creation, runtime kernel, trace, gateway output, ingestion,
  or product analysis.
- Do not broaden scenario editing or add arbitrary physical-model parameters.

## User Review

Review the executable meaning of the Fuel Loss entries, especially initial
conditions, point/window and bound behavior, and whether post-gap/manual levels
are external observations rather than prescribed simulator state. T019 does
not begin until this is accepted or redirected.
