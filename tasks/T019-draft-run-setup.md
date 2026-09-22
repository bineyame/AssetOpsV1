# T019 - Draft Run Setup

Status: in_review
USER_REVIEW_REQUIRED: true

Built on `task/T019-draft-run-setup`, from `main` at `a0dc56c`, and narrowed
before merge by Amendment 1's proposals (e) and (j) - the two criteria at the
end of the list below. Evidence is in `.agent/T019-review-packet.md`,
including the layout measurement, the deliberate violations that prove each
guard, and the disposition of the fourteen independent review findings.

Intended branch: `task/T019-draft-run-setup`

## Feature

Scenario Catalog And Run Setup.

## UI-Verifiable Screen Behavior

From an executable ScenarioDefinition, a user configures a Draft run against a
resolved Site and sees the complete frozen deterministic input summary. The
setup creates and persists a Draft with a minimal returned summary when the
request is structurally complete: `READY` when compatible with the selected
model profile, or `BLOCKED` with inspectable compatibility reasons. It does not
execute the simulator.

## Why This Is Next

T018 gives every scenario value executable meaning. Run setup can then freeze
the inputs that the first causal kernel will consume without inventing initial
state or treating a golden trace as authority.

## Acceptance Criteria

- Run setup selects a concrete Site/Foundation version and scenario version,
  and accepts validated interval, timestep, seed, simulator/model-profile
  version, supported public overrides, and explicit initialization inputs.
- Real IANA timezone membership is validated before Site time participates in
  executable run timing.
- The frozen deterministic identity includes Site/Foundation, scenario and
  resolved parameters, interval, timestep, seed, simulator/model profile,
  initialization inputs, observation cadence/profile, simulator source and
  gateway publication identities, mappings/config, and initially empty ordered
  intervention history. Each value names its Foundation, scenario, run, or
  versioned-profile origin.
- Unsupported target topology, unresolved components/signals, missing initial
  inputs, invalid units, or malformed intervals refuse setup and allocate no
  `run_id`. A structurally valid, fully frozen request whose executable inputs
  are unsupported by the selected model profile may persist as `BLOCKED` with
  inspectable reasons; no fabricated defaults make it `READY`.
- **Which side of that line a failure falls on is decided by who failed to
  answer**, settled at the T019 user review and aligned with T020A. The
  scenario's declared owner has no answer, so nothing can be frozen and no
  profile would help: refuse. The selected profile cannot answer, so a
  different profile would: persist a `BLOCKED` Draft. An initial world value
  the selected model profile cannot supply or locate is therefore a blocking
  reason and not a refusal, the frozen identity can record a value as having
  no answer, and a `READY` run may not carry one.
- A created Draft has a new `run_id` distinct from `site_id` and `scenario_id`.
  It persists behind a SimulationRun domain port and survives restart;
  overlapping Drafts remain allowed. T019 returns only the setup summary; run
  inventory/detail presentation belongs to T020.
- The setup and Draft summary make clear that no execution, state trajectory,
  staged envelope, Commit eligibility, accepted evidence, or Finding exists.
- No recording or trace is selected as an input or created as run authority.
- Run setup does not infer cadence, source identity, or gateway identity from
  Site provenance, device display names, or source mode. The selected versioned
  model/publication profile must resolve those inputs or the run is `BLOCKED`.

Added by Amendment 1 after the slice was built, and binding on it before merge
(`.ai/PLANNING_HANDOFF_T019_T022.md`, T019; the proposals are (e) and (j)):

- Run setup does not decide whether the causes a scenario declares reach a
  reading the same scenario declares. It has no kernel, so that comparison is
  not its to make: the observation blocking reasons, their call site, and the
  `OBSERVATION_NOT_ACCOUNTED_FOR` member of the blocking vocabulary are gone,
  and every remaining blocking kind is a statement about what the selected
  profile can execute. The shipped Fuel Loss Draft blocks on three
  `STATE_NOT_SUPPORTED` reasons rather than five. `BLOCKED` is unchanged as an
  outcome: the shipped model profile still models neither site demand, nor
  plane-of-array irradiance, nor the availability of the reporting path.
- `reconcile_reported_observations` is labelled in the test suite as a
  specification reference implementation rather than a product feature, with
  its expiry stated as a condition and not a slice number
  (`D-2026-09-22-expiry-follows-the-condition`). It stops being an authority
  when a kernel exists and the two are compared, which is T021's comparison;
  it leaves the repository when its last remaining product-path caller goes,
  and that caller is the `observation_reconciliation` payload and the scenario
  detail panel that renders it. When that happens is Open Question 5 and is
  undecided, so T019 does not touch the panel, the payload, or the
  reconciliation logic, and no slice before that decision treats the removal
  as in scope.

## Protected Seams

- Frozen deterministic identity and explicit initialization provenance.
- Site, scenario, and run identity separation.
- Simulator Lab gate and URL chokepoint.
- Scenario intent remains separate from runtime state and product evidence.

## Focused Proof

- Domain/API tests cover persistence, frozen identity, validation/refusal
  states, timezone membership, stable version references, no hidden defaults,
  and whether each failure does or does not allocate a run identity.
- UI tests cover READY and BLOCKED setup, backed digits only, and absence of
  execution/downstream claims.
- Gate, route, architecture, workflow, typecheck, and relevant suites pass.

## Scope Limits

- No runtime stepping, event injection, golden traces, gateway staging, Commit,
  ingestion, Replay, analytics, or Findings.

## User Review

Review setup language, frozen input/provenance summary, and READY/BLOCKED
treatment before M1C execution work begins.
