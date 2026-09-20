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

Active planned task: `tasks/T019-draft-run-setup.md`.

T018 closed out 2026-09-21. Independent review accepted it over two rounds -
five findings fixed, then four Low findings left open - and user review
returned **"it looks good"**, accepting all four proposals. The execution
contract is settled and recorded in
`D-2026-09-21-scenario-execution-contract`. T019 owns Draft creation,
persistence and frozen inputs without execution.

T018 gave every authored scenario value a machine-readable execution role -
causal input, forcing input, reported observation, non-executable condition -
and settled initialization ownership, canonical units, point/window timing,
half-open dispatch and bound behaviour. T017's three provisional regions are
gone and its accepted vocabularies are unchanged.

**The Fuel Loss residual is accepted as stated, not resolved.** The declared
causes reach 254 L where the sensor reports 155 L and the operator records
150 L, leaving -99 L and -104 L `NOT_ACCOUNTED_FOR`. Both readings are
observations from a named source, so neither prescribes tank state. The three
ways out - model the missing cause, declare a reporting behaviour, or change
the causes - are open and the user's to direct in a later slice. **Until one
is chosen, T019 treats an unreached reading as a reason to block, not a
rounding matter.** No authored number was edited.

Four Low findings from T018's second review round are unfixed and are the
first cleanup available: undeclared intra-instant ordering in `DISPATCH_RULES`,
an unmeasured second initialization layer, a weak contract-version test, and
two forward constraints that live only in code comments. `.ai/CODE_STATE.md`,
"What round two left open", has all four.

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
M1B is active: T017 and T018 are complete and T019 is planned.

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
nothing in the product can write to it yet.

## Read For T019

- `tasks/T019-draft-run-setup.md`
- `tasks/completed/T018-executable-scenario-contract.md` - its User Review
  Outcome, which is what makes T019 implementable.
- `.ai/FEATURE_MAP.md`
  - `### 3. Scenario Authoring And Scenario Catalog`
  - `### 4. SimulationRun Runtime And Simulator Lab Shell`
  - `### Early Feature: Scenario Catalog And Run Setup`
- `.ai/ARCHITECTURE.md`
  - Causal Runtime Authority
- `.ai/DECISIONS.md` decision-index entries:
  - `D-2026-09-21-scenario-authoring-semantics`
  - `D-2026-09-21-scenario-execution-contract`
  - `D-2026-09-21-causal-runtime-before-golden-traces`
- `.ai/CODE_STATE.md`
  - T017, T018
- `.ai/WORKFLOW.md`
  - Task Spec Size, Review Packet, Closeout

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
