# Active Context

Keep this file compact and current. Durable reasoning lives in
`.ai/FEATURE_MAP.md`, `.ai/DECISIONS.md`, `.ai/ARCHITECTURE.md`,
`.ai/CODE_STATE.md`, and the task files.

Size rule: this file stays under 200 lines, enforced by
`tools/check-agent-workflow.ps1`.

## Current Milestone

M1 - A user can configure one mini-grid site, simulate it, and inspect the
resulting operational evidence in the UI.

## Active Task

Active task: none. **T019 is complete, accepted at user review on 2026-09-22,
and merged.** Its file is `tasks/completed/T019-draft-run-setup.md`; what it
settled in code is the T019 entry in `.ai/CODE_STATE.md`.

**T020, Runs inventory and Draft shell, is next**:
`tasks/T020-runs-inventory-and-draft-shell.md`. It presents the Drafts T019
writes to `var/runs/`, which nothing presents yet.

T019 built the SimulationRun domain: a Draft is created from a scenario and a
resolved Site, freezes the whole deterministic identity with an answerer for
every value, persists behind its own port, and executes nothing. Cadence,
simulator source identity and gateway identity come from the selected
versioned profile or the run blocks - held by a module that cannot import a
Site record at all. The shipped Fuel Loss Event blocks on three
`STATE_NOT_SUPPORTED` reasons and cannot reach `READY` in this build;
`READY` is proved on fixtures.

**What the T019 user review carried into T020.** Form defaults are wanted, and
a default must be **visible and labelled** as a default, never a silent
pre-pick. `READY` must disclose what it does not assert, on the run record and
on screen, and T021 retires that disclosure in the slice landing the
conformance test. The re-review's N3-N6 residual risk in
`.agent/T019-review-packet.md` should be read before T020 reads the run store.

**The refusal line moved at that review** - who failed to answer decides it,
recorded in the 2026-09-22 extension to
`D-2026-09-21-run-setup-outcome-vocabulary`, with the naming rule that keeps
the two vocabularies legible in `.ai/ARCHITECTURE.md`. Since then
`D-2026-09-22-foundation-property-absent-blocks` settled the one case the
record had wrong, so **every failure of a Foundation-owned value blocks** and
`INITIAL_VALUE_ANSWERS_DISAGREE` is retired in T020A.

**T020A grew and a step follows it.** A Foundation-owned scenario parameter
has no value position at all, which reaches `tank-capacity` as well as the
coefficient, moves `EXECUTION_CONTRACT_VERSION`, retires
`INITIAL_VALUE_ANSWERS_DISAGREE` and takes the `fuel-tank-volume` upper bound
out of the document while keeping the `bounds` declaration. The coefficient is
`L/kWh` and `dispatched-output` is promoted in the same slice. Then a
**contract-alignment step** between T020A and T021 declares the four kernel
semantics, refuses a requirement conflict instead of resolving it, lowers two
forcing states to `OPTIONAL` and moves reporting authority to the publication
profile - after which **the shipped Fuel Loss Event can reach `READY`**, and
that step retires T020's fixture-only `READY` criterion. Decisions
`D-2026-09-22-foundation-value-declaration`,
`-capacity-bound-source`, `-consumption-coefficient-unit`,
`-forcing-state-requirements`, `-kernel-step-semantics`,
`-reconciliation-panel-retirement`. Version numbers are in
`.ai/FEATURE_MAP.md`, *The execution-contract version ledger*; write moves,
not literals.

**The T019 checkpoint proposals are accepted and recorded, 2026-09-21.**
Twelve of them, (a) through (l), reasoned in
`Docs/simulator-scenario-authoring-and-runtime.md` and recorded in five
`.ai/DECISIONS.md` entries. What changes planning: run setup stops
adjudicating cause-to-observation coupling; a scenario does not author what a
device reads, so the Fuel Loss residual is answered by (f) and the document is
corrected during T021 from what the kernel computes; and two slices are
inserted - **T020A** between T020 and T021 for Foundation physical properties
and model-rule carriers, and **T021A** between T021 and T022 to close
`execution_requirement` while the version-bump window is still free. Read
`.ai/PLANNING_HANDOFF_T019_T022.md` before writing or revising any task file
in that range.

Two of T018's four Low findings are closed by T019 and marked settled in
place in `.ai/CODE_STATE.md`; two remain, the unmeasured second
initialization layer and two forward constraints living only in comments.

## Current State

M1A is complete. T001-T016 are in `tasks/completed/` with Review Outcomes.
M1B is active: T017, T018 and T019 are complete; T020 is next.

Breaker/control vocabulary is settled by `D-2026-09-20-breaker-vocabulary`:
position is evidence, not configuration. The banned list lives in
`backend/tests/control_vocabulary.py`, is read by both scans, and is
unconditional; T017's entry in `.ai/CODE_STATE.md` says what it covers.

`config/scenarios/fuel-loss-event.yaml` is tracked, read-only, and the one
shipped scenario. Unlike `config/sites/`, that store deliberately does not ship
empty: there is no scenario create flow, so an empty store would leave a fresh
checkout nothing to inspect.

`var/sites/` holds `mg-001`, `mg-002` (cold room), and `mg-003` (two AC buses).
The user asked that these be kept as fixtures. They are gitignored, so add
fixtures when needed and do not clear, replace, or delete that directory.
`var/scenarios/` is the writable scenario store; it is gitignored, empty, and
nothing in the product can write to it yet. `var/runs/` is the run store T019
added: gitignored, written by run setup, and holding whatever Drafts this
machine has created. Nothing presents them yet - that is T020.

## Read For T020

- `tasks/T020-runs-inventory-and-draft-shell.md` and, for residual risk,
  `.agent/T019-review-packet.md`
- `.ai/DECISIONS.md` decision-index entries:
  - `D-2026-09-21-run-setup-outcome-vocabulary` - the refusal line, the
    `READY` disclosure, and what T020 must show
  - `D-2026-09-21-scenario-execution-contract`
- `.ai/CODE_STATE.md` - T018, T019
- `.ai/FEATURE_MAP.md`
  - `### 4. SimulationRun Runtime And Simulator Lab Shell`
  - `### Early Feature: Draft SimulationRun And Causal Runtime`
- `.ai/ARCHITECTURE.md` - Causal Runtime Authority, Refusal And Blocking
  Vocabularies, Presentation Honesty
- `.ai/WORKFLOW.md` - Review Packet, Closeout, User Review

Running the layout tool creates Drafts in `var/runs/`. That is expected and
gitignored.

## Settled Direction For M1B

- Scenario catalog is a Simulator Lab surface, not an operator surface, and is
  gated with `simulator_lab.enabled`.
- Only `frontend/src/shell/simulatorLabRoutes.tsx` may name simulator URLs.
- Adding a truthful Scenarios route may add Scenarios to the Lab rail; operator
  navigation and operator Site tabs do not grow.
- ScenarioDefinition answers what happens during the simulated interval. Site
  Foundation answers what the Site is. The two do not duplicate each other.
- The shipped Fuel Loss Event is a directly selectable ScenarioDefinition at
  `config/scenarios/fuel-loss-event.yaml`, read through composed shipped and
  writable stores behind a scenario-domain port. Writable user definitions live
  under gitignored `var/scenarios/`.
- Scenario events are authored sub-artifacts inside a scenario version, not
  top-level stored entities. Future runtime injections are run-scoped
  SimulationRun intervention-history records and are not written back into the
  scenario version.
- Scenario labels, scenario versions, run names, and `run_id` never become
  `site_id`.
- Private expectations are test-oracle metadata only. They never enter source
  envelopes, accepted evidence, operator UI, normal product provenance, exports,
  analytics, or Findings.
- Scenario authors specify causes, external conditions/observations, and
  non-executable evidence conditions; they do not author computed private-state
  trajectories. T018 made those roles explicit and machine-readable, and made
  a reported value structurally unable to initialize or change private state.
- Initial state must resolve from attributable Foundation, scenario, run, or
  versioned model inputs. A recording may not hide initialization.
- A minimal deterministic causal kernel precedes authoritative golden traces.
  Generated traces are reproducible regression/playback artifacts bound to the
  exact frozen deterministic identity, never an alternate state authority.
- M1B has no ingestion, no accepted evidence, no Draft run yet, and no Findings.
  T017 and T018 screens must describe intention, not report outcome.
- No invented digits: a count, timestamp, duration, seed, volume, confidence, or
  parameter value appears only when the record supplies it.
- Dense tables and timeline layouts require browser layout evidence in the
  review packet.

## Standard Checks

- `tools/check-architecture.ps1`
- `tools/check-agent-workflow.ps1`
- Existing backend and frontend tests relevant to the active slice.

## What The Code Already Settles

Per-slice details live in `.ai/CODE_STATE.md`.

- T006-T008 settled Site records, stores, read paths, Foundation basics, and
  frontend/backend Site client shape.
- T009-T013 settled shared visual vocabulary, canonical Site screens,
  Foundation naming, operator tab inventory, and overflow posture.
- T014-T016 settled Foundation topology/devices/mappings, SLD view model, and
  configured SLD/device presentation.
- T017 settled the ScenarioDefinition domain, its port and composed stores, the
  parser/service split over target-site resolution, the parsed-field
  public/private boundary, and the Lab's scenario surfaces. Its three checkpoint
  semantics were accepted on 2026-09-21 and its provisional markers are gone.
- T018 settled the execution contract over that domain: four execution roles,
  initialization ownership, canonical units, point/window/interval-wide timing
  with half-open dispatch, four bound cases with no silent policy, declared
  cadence ownership, and observation-source resolution against Foundation. Its
  vocabularies and the Fuel Loss reconciliation were accepted on 2026-09-21.
- T019 settled the SimulationRun domain and Draft run setup: the frozen
  deterministic identity with an answerer for every value, the refusal versus
  `BLOCKED` line as the user moved it, allocated run identity, real IANA
  membership, profile-only resolution of cadence and the two publication
  identities, and the run store. Accepted and merged 2026-09-22.
