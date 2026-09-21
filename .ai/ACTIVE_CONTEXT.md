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

Active task: `tasks/T019-draft-run-setup.md`, **built and in review**. It
carries `USER_REVIEW_REQUIRED: true`, so it needs an independent review and
then a user decision before T020 starts. Evidence is in
`.agent/T019-review-packet.md`.

T019 built the SimulationRun domain: a Draft is created from a scenario and a
resolved Site, freezes the whole deterministic identity with an answerer for
every value, persists behind its own port, and executes nothing. The line the
slice is organised around: a request that cannot be frozen is **refused**,
allocating no `run_id` and writing nothing; a request that freezes and still
cannot be executed by the selected profile is **persisted as `BLOCKED`** with
inspectable reasons. Cadence, simulator source identity and gateway identity
come from the selected versioned profile or the run blocks - held by a module
that cannot import a Site record at all.

T018 closed out 2026-09-21. Independent review accepted it over two rounds -
five findings fixed, then four Low findings left open - and user review
returned **"it looks good"**, accepting all four proposals. The execution
contract is settled in `D-2026-09-21-scenario-execution-contract`: every
authored value carries a machine-readable execution role, and initialization
ownership, canonical units, timing, dispatch and bound behaviour are settled.

**The Fuel Loss residual is accepted as stated, not resolved.** The declared
causes reach 254 L where the sensor reports 155 L and the operator records
150 L, leaving -99 L and -104 L `NOT_ACCOUNTED_FOR`. The three ways out -
model the missing cause, declare a reporting behaviour, or change the causes -
are open and the user's to direct. T019 applied the consequence the decision
names: an unreached reading is a reason to block. **The shipped Fuel Loss
Event therefore cannot reach `READY` in this build**, by construction - two of
its five blocking reasons are the residual, and three are forcing states the
first kernel does not model. `READY` is proved against fixtures.

Two of T018's four Low findings are closed by T019 and marked settled in
place: intra-instant ordering is now a `DISPATCH_RULES` entry, because a
persisted Draft's blocking reasons made the authored order observable from
outside the contract, and `EXECUTION_CONTRACT_VERSION` moved to 2, which also
made the weak contract-version test strong. Two remain: the unmeasured second
initialization layer and two forward constraints that live only in code
comments.

### The lesson T017 paid for

The vocabulary guard built to be unconditional had a hole exactly where a
parameter key lives, and four deliberate violations missed it. The parameter
proof added `breaker_position` as a mapping *key*, which the strict parser
already refuses as unknown - so it failed loudly and proved nothing about the
rule it was written for. **A deliberate violation has to be one the rest of
the system would otherwise accept**, or it measures the wrong guard. Found by
the independent Reviewer, not by the proofs. That is the eighth member of the
family and it is written into `backend/tests/control_vocabulary.py` rather
than only into a packet.

T018 paid it twice more. A deliberate "power applied as a rate" was refused
by the role rule before the dimension rule was consulted, and two attempts to
get a reading into the initialization inputs tripped a different guard first.
Both were rewritten until they measured what they named.

T018's review added the other half of the same family: a guard, a sentence
and a number each have to be checked against the thing they describe, not
against themselves. A legend claimed a guarantee the parser did not hold, a
cadence rule written for one position left three open, and the reconciliation
reported a volume its own bound policy refuses. The T018 entry in
`.ai/CODE_STATE.md` has all three.

## Current State

M1A is complete. T001-T016 are in `tasks/completed/` with Review Outcomes.
M1B is active: T017 and T018 are complete and T019 is in review.

Breaker/control vocabulary is settled by `D-2026-09-20-breaker-vocabulary`:
position is evidence, not configuration. T017 grew that protection to the
scenario domain and moved the banned list to
`backend/tests/control_vocabulary.py`, read by both scans. It is unconditional
and covers the scenario model, the parser key vocabularies, the shipped
definition and the parser fixtures.

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

## Read For Reviewing T019

- `tasks/T019-draft-run-setup.md` and `.agent/T019-review-packet.md`
- `.ai/DECISIONS.md` decision-index entries:
  - `D-2026-09-21-scenario-execution-contract` - above all what it says run
    setup does with an unreached reading
  - `D-2026-09-21-causal-runtime-before-golden-traces`
- `.ai/CODE_STATE.md`
  - T018, T019
- `.ai/FEATURE_MAP.md`
  - `### 4. SimulationRun Runtime And Simulator Lab Shell`
  - `### Early Feature: Scenario Catalog And Run Setup`
- `.ai/ARCHITECTURE.md`
  - Causal Runtime Authority
- `.ai/WORKFLOW.md`
  - Review Packet, Closeout, User Review

A reviewer who runs the layout tool will create Drafts in `var/runs/`. That is
expected and gitignored.

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
  `BLOCKED` line, allocated run identity, real IANA membership, profile-only
  resolution of cadence and the two publication identities, and the run store.
  It is in review, not accepted.
