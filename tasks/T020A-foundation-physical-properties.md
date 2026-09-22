# T020A - Foundation Physical Properties And Model-Rule Carriers

Status: planned
USER_REVIEW_REQUIRED: true

Intended branch: `task/T020A-foundation-physical-properties`

## Feature

Draft SimulationRun And Causal Runtime.

## UI-Verifiable Screen Behavior

Site Configuration's Key Parameters panel for MG-001 shows the diesel
generator's specific fuel consumption beside the ratings it already lists. Run
setup's frozen-inputs summary shows that coefficient resolving from *site
foundation* rather than from *scenario*, and a run against a Site whose
Foundation does not declare it is refused with an inspectable reason. That one
line in each of two tables the user already reads is the seam repair made
visible.

## Why This Is Next

T021's kernel cannot move the tank without a consumption coefficient, and the
shipped Fuel Loss document currently supplies it as `generator-fuel-rate`. A
physical property of a machine living in a scenario means the story has
replaced the asset: run the same scenario against a different generator and
14 L/h would follow the story. The first kernel sets the shape every kernel
after it copies, so the coefficient has to come from Foundation before the
kernel exists rather than after.

This is an insertion rather than a narrowing. Foundation carries one optional
scalar per component, `FoundationBinding` can address only that scalar, and
`SupportedState` has no field a model-rule value could occupy. Three holes that
must move together: any one alone still leaves a declarable owner with no
answer. Settled in `D-2026-09-21-physical-property-ownership`.

## Dependencies

- T019's frozen-inputs resolution and blocking reasons, merged.
- T020 for sequencing only. This slice is independent of the kernel and nothing
  in front of it is blocked.

## Decisions Due Before Implementation

The coefficient's canonical unit follows the `dispatched-output` half of the
`REQUIRED` forcing-state decision: whether generator output is promoted to a
`FORCING_INPUT` on `generator-output-power`. A runtime-based model rule wants
`L/h`; an energy-based one wants `L/kWh` and a generator-output forcing to
multiply it by. That half is due **before this slice is implemented**, earlier
than the rest of the forcing-state decision, because this slice writes the
property into the shipped template and into MG-001 and changing it afterwards
is a unit migration on a Foundation document and on an instance created by
copy. The carriers below are identical either way, so only the shipped value's
unit waits. A slice that picks a unit to get itself unblocked has taken the
user's decision.

## Acceptance Criteria

- A Site component and a template component can declare named physical
  properties beyond `rating`. Each property carries a value and a canonical
  unit. The set of property names a component may declare is defined per
  component type and enforced by the strict parser; an unknown name, a name on
  the wrong component type, an unknown or dimensionally wrong unit, or a
  repeated name refuses the document rather than being ignored.
- User-authored Site configuration reaches these properties through the same
  strict parser as shipped configuration. There is no second, lenient path.
- `FoundationBinding` can address a named property on a component type, not
  only `rating` by unit. Existing rating bindings keep their current meaning
  and resolution behaviour, and a binding matching zero or more than one
  component refuses rather than selecting one.
- `SupportedState` can carry a model-rule value. A scenario declaring
  `owner: MODEL_RULE` resolves its value from the selected model profile, and
  the frozen identity records `MODEL_PROFILE` as that value's origin the same
  way a Foundation-sourced value records Foundation. This is what closes the
  T019 review's L9 finding: the vocabulary already declares the owner and names
  the answerer correctly, and what was missing was somewhere for the answer to
  live.
- A `MODEL_RULE` owner the selected profile carries no value for blocks with an
  inspectable reason and produces no default. It uses the blocking kind T019
  introduced for an initial value the selected profile cannot answer, rather
  than a second kind for the same fact. If T019 moved only the Foundation case
  across the refusal line, this slice moves the model-rule case with it and
  says so.
- The shipped site template declares the generator's specific fuel consumption
  as a named property with its canonical unit.
- MG-001 carries the property, re-created from the updated template or with the
  property added to the instance. Templates instantiate by copy, so editing the
  template alone leaves a demo site whose runs are still refused. `mg-002` and
  `mg-003` remain in `var/sites/` as the fixtures the user asked to keep.
- `generator-fuel-rate` leaves `config/scenarios/fuel-loss-event.yaml`. Run
  setup freezes the coefficient from Foundation and records its origin. The two
  ways that can fail land on opposite sides of the refusal line: a selected
  model profile that declares no binding for it **blocks**, because a different
  profile fixes it, and a resolved Site whose Foundation declares no matching
  property **refuses**, because the declared owner has no answer and no profile
  helps. No scenario value and no default substitutes for either.
- Site Configuration's Key Parameters panel shows the declared property with
  its unit. The panel's existing rule holds: an entry appears because the
  record declares it, and a component that declares nothing produces no row.
- Foundation remains read-only. This slice adds no edit path for any Site.

## Required Product And Domain Semantics

- Four owners, decided by two swap tests. Foundation declares what the site
  *is*; the model profile how the simulator *reasons*; the scenario what
  *happens* in one interval; the publication profile how the reporting
  installation *behaves*. Swap the asset and the value changes: Foundation.
  Swap the scenario and it changes: scenario. Neither, but a better simulator
  would change it: model profile.
- A coefficient and the law that consumes it are different objects with
  different owners. *This generator burns its rate at its dispatch point* is
  Foundation. *Consumption is proportional to runtime* is a model rule.
- Declaring an owner is not the same as being able to carry its value. Where an
  owner is declarable, something must hold what it declares and something must
  be able to address it.
- The refusal line, as T019 settled it: the scenario's declared owner has no
  answer, so refuse, because no profile helps; the selected profile cannot
  answer, so block, because a different profile fixes it. Every new failure
  this slice adds is placed by that rule and by no other reasoning.
- A Foundation says how large a tank is, never how full. Starting fuel level
  stays a scenario input.

## Protected Seams

- Physical property ownership: the coefficient a later product conclusion uses
  comes from Foundation configuration, never from the scenario's private rate.
- Strict parsing at the configuration boundary: shipped and user-authored
  configuration cross the same parser.
- Template-instantiates-by-copy: a template change never reaches an existing
  instance, so the instance is updated deliberately and visibly.
- Frozen identity provenance: every frozen value names its Foundation,
  scenario, run, or versioned-profile origin, and the origin shown on screen is
  the origin recorded on the record.
- Simulator/product boundary: no runtime, no execution, no evidence.

## Focused Tests And Review Evidence

- Parser tests covering an accepted property, an unknown property name, a
  property declared on a component type that does not allow it, an unknown or
  wrong-dimension unit, and a repeated name. At least one deliberate violation
  must be one the rest of the system would otherwise accept, or it measures a
  different guard than the one it names.
- A test proving user-store Site configuration is parsed by the same strict
  path as shipped configuration for these properties.
- Binding tests for named-property resolution, unchanged rating-binding
  behaviour, and refusal on zero or multiple matching components.
- Model-rule carrier tests: a `MODEL_RULE` owner resolves from the profile with
  `MODEL_PROFILE` recorded as origin; an uncarried `MODEL_RULE` owner blocks.
- Run-setup tests: the coefficient freezes from Foundation with Foundation
  origin, the scenario no longer supplies it, a profile with no binding for it
  blocks, and a Site without the property is refused rather than falling back.
- Fixture proof that MG-001 carries the property and that `mg-002` and `mg-003`
  still load.
- UI tests for the Key Parameters row and the frozen-inputs origin label, with
  no digit that the record does not supply.
- Layout evidence for the Key Parameters panel and the frozen-inputs table.
- Run architecture/workflow checks, relevant suites, typecheck, and build.

## Scope Limits

- The minimum set only: the generator's specific fuel consumption and the
  model-rule carrier. Efficiency curves, minimum load, ramp rate, tank
  geometry, sensor placement, battery chemistry, PV tilt, orientation and
  derate stay absent; the first kernel models none of the things they affect.
- The fuel tank's minimum usable level is the honest home for the floor the
  validation layer currently invents, and it is a follower. Moving that floor
  belongs to a slice that says it is doing that and carries the test for it.
- No kernel, execution, runtime state, observation transform, golden trace,
  gateway staging, ingestion, analytics, or Finding.
- No Foundation edit path.
- Whether the product's own later expectation reads this same Foundation
  coefficient or a separately declared operating assumption is a T034-T038
  question. This slice supplies the coefficient and decides nothing about who
  else reads it.

## User Review

User review is required. The user took this checkpoint on 2026-09-22, and two
things in the slice are the kind the project reviews: the
per-component-type physical property vocabulary is a durable configuration
contract in the same family as the breaker/control vocabulary, and the Key
Parameters panel is a user-facing surface gaining a new row. Re-creating MG-001
also changes the demo site the rest of M1 is demonstrated on.

Review focus: the property name and its unit, whether the Key Parameters panel
should present a physical property differently from a design rating, and the
frozen-inputs origin label that shows the coefficient coming from site
foundation.
