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
Foundation does not declare it persists a Draft that blocks on the unresolved
value, inspectable and naming the property it could not find. That one line in
each of two tables the user already reads is the seam repair made visible.

The scenario detail screen loses two numbers. The Fuel Loss document stops
stating 14 L/h for the generator and 500 L for the tank: both are Foundation's
to answer, and the document now declares the need and no value.

## Why This Is Next

T021's kernel cannot move the tank without a consumption coefficient, and the
shipped Fuel Loss document currently supplies it as `generator-fuel-rate`. A
physical property of a machine living in a scenario means the story has
replaced the asset: run the same scenario against a different generator and
14 L/h would follow the story. The first kernel sets the shape every kernel
after it copies, so the coefficient has to come from Foundation before the
kernel exists rather than after.

Three carriers are missing and must move together, because any one alone still
leaves a declarable owner with no answer. Foundation carries one optional
scalar per component, `FoundationBinding` can address only that scalar, and
`SupportedState` has no field a model-rule value could occupy. Settled in
`D-2026-09-21-physical-property-ownership`.

A fourth question none of the three answers: what tells run setup the run
needs the coefficient, once `generator-fuel-rate` leaves the scenario.
`D-2026-09-22-foundation-value-declaration` settles it — a scenario parameter
whose declared owner is Site Foundation has **no value position at all**. It
declares the state, the unit and that Foundation answers, and states no
number, closed at the structure the way T018 closed duration units. A value
position an author may fill is one an author will fill.

## Dependencies

- T019's frozen-inputs resolution and blocking reasons, merged.
- T020 for sequencing only; nothing in front of this slice is blocked.

## Decisions Due Before Implementation

The coefficient's canonical unit follows the `dispatched-output` half of the
`REQUIRED` forcing-state decision: whether generator output is promoted to a
`FORCING_INPUT` on `generator-output-power`. A runtime-based model rule wants
`L/h`; an energy-based one wants `L/kWh` and a generator-output forcing to
multiply it by. It is due **before this slice is implemented**, earlier than
the rest of that decision, because this slice writes the property into the
shipped template and into MG-001, and changing it afterwards is a unit
migration on a Foundation document and on an instance created by copy. The
carriers are identical either way, so only the shipped value's unit waits. A
slice that picks a unit to get itself unblocked has taken the user's decision.

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
  component selects neither: the value stays unanswered and the run blocks.
- `SupportedState` can carry a model-rule value. A scenario declaring
  `owner: MODEL_RULE` resolves its value from the selected model profile, and
  the frozen identity records `MODEL_PROFILE` as that value's origin the same
  way a Foundation-sourced value records Foundation. This closes the T019
  review's L9 finding: the owner was declarable and the answerer correctly
  named, with nowhere for the answer to live.
- A `MODEL_RULE` owner the selected profile carries no value for blocks on
  `INITIAL_VALUE_NOT_RESOLVED`, the kind T019 introduced for exactly this, and
  produces no default. One kind carries every such case and this slice adds no
  second.
- A scenario parameter whose declared owner is `SITE_FOUNDATION` has no value
  position. The parser gives it nowhere to state a number and refuses a
  document that states one; it still declares the state, the unit and the
  owner. The rule keys on the owner, the only thing the document carries that
  distinguishes these parameters: the binding lives in the model profile and
  the scenario parser sees no profile at all.
- So the shipped document loses two numbers, not one. `generator-fuel-rate`
  becomes Foundation-owned and its 14 L/h goes; `tank-capacity` is already
  Foundation-owned and its 500 L goes with it. Exempting the second would need
  a field invented for the exemption, and it carries the same defect today.
- The `fuel-tank-volume` upper bound currently comes from `tank-capacity`'s
  stated 500 L, and `declared_bounds` skips a parameter with no numeric value,
  so the bound disappears silently unless this slice places it. The slice says
  where the capacity bound comes from once the scenario states no number, and
  proves it. A bound that vanished because nobody looked is the failure this
  sequence exists to stop.
- `EXECUTION_CONTRACT_VERSION` moves by one here. The shipped document as it
  stands is refused by the new parser, so this narrowing reaches a document
  that already exists. The count for the sequence is stated once, in
  `.ai/FEATURE_MAP.md` under *The execution-contract version ledger*; no task
  file writes the literal.
- `INITIAL_VALUE_ANSWERS_DISAGREE` is retired. Its only producer compares a
  scenario-stated value against Foundation's, and no document can state one
  any more, so the kind names a failure nothing can cause. It goes in the
  slice that removes its last producer. The consequence to state plainly:
  **every failure of a Foundation-owned value now blocks and none refuses**,
  and a reader meeting that should not take it for an oversight.
- `.ai/ARCHITECTURE.md`'s Refusal And Blocking Vocabularies illustrates *within
  one subject, the shape must carry it* with the pair this slice breaks up.
  The rule survives; its worked example stops existing. This slice
  re-illustrates it from the pair that remains or says the example is
  historical, because a rule illustrated by a vocabulary member nobody can
  find reads as a rule that was not followed.
- The shipped site template declares the generator's specific fuel consumption
  as a named property with its canonical unit, and run setup freezes the
  coefficient from Foundation and records its origin. Every way that can fail
  blocks and produces no default: no binding declared, no match, more than one
  match, the wrong unit, and a Foundation that declares no such property at
  all. The last is a fifth case of the same thing, not a refusal, because
  after this slice the binding names the property as well as the component
  type, so a different profile naming a different property may find something
  this Foundation does declare. Settled in
  `D-2026-09-22-foundation-property-absent-blocks`.
- MG-001 carries the property, re-created from the updated template or with the
  property added to the instance. Templates instantiate by copy, so editing the
  template alone leaves a demo site whose Drafts block on the missing
  coefficient - which means the slice's own UI-verifiable outcome, the Key
  Parameters row and the frozen-inputs row resolving from site foundation,
  never appears. `mg-002` and `mg-003` remain in `var/sites/` as the fixtures
  the user asked to keep.
- The header comment of `config/scenarios/fuel-loss-event.yaml` says its
  numbers are the ones the T017 checkpoint shipped and are unchanged. This is
  the first slice to edit that file, so the header stops being true here and
  is corrected with the edit.
- Site Configuration's Key Parameters panel shows the declared property with
  its unit. The panel's existing rule holds: an entry appears because the
  record declares it, and a component that declares nothing produces no row.
- Foundation remains read-only. This slice adds no edit path for any Site.

## Required Product And Domain Semantics

- Four owners and the two swap tests that decide between them are stated in
  `D-2026-09-21-physical-property-ownership`. What this slice needs from them:
  swap the asset and the value changes, so it is Foundation's.
- A coefficient and the law that consumes it are different objects with
  different owners. *This generator burns its rate at its dispatch point* is
  Foundation. *Consumption is proportional to runtime* is a model rule.
- Declaring an owner is not the same as being able to carry its value, and
  stating a number is not the same as declaring a need. Where an owner is
  declarable, something must hold what it declares, something must be able to
  address it, and the document must be able to ask without answering.
- The line, as the user settled it and as it now stands for this slice: the
  selected profile cannot answer, so block, because a different profile fixes
  it. Every Foundation-owned failure this slice adds is on that side, and
  after the contradiction kind is retired none of them refuses. A refusal
  still exists for other subjects; it no longer exists for this one.
- A Foundation says how large a tank is, never how full. Starting fuel level
  stays a scenario input, and it keeps its value position because the scenario
  owns it.

## Protected Seams

- Physical property ownership: the coefficient a later product conclusion uses
  comes from Foundation configuration, never from the scenario's private rate,
  and the document has no position to state one from.
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
  origin, the scenario no longer supplies it, and each of the five ways it can
  fail to resolve blocks rather than refusing or falling back, including a
  Foundation that declares no such property.
- Parser test refusing a Foundation-owned parameter that states a value, whose
  deliberate violation is the shipped document as it stands today.
- A test proving `INITIAL_VALUE_ANSWERS_DISAGREE` has no producer left, and
  that the two vocabularies are still disjoint without it.
- A bound test proving the `fuel-tank-volume` upper bound still exists and
  still comes from a declared capacity rather than from two state keys sharing
  a prefix. The existing bound test asserts the scenario's 500 L and has to
  move with the number rather than be weakened to match it.
- A contract-version test that checks the move against the declared rule set
  rather than against a literal, and a frozen-identity test that a Draft
  frozen under the previous version keeps it.
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
- Option C, the model profile declaring the need rather than the scenario, is
  a named follower with its own trigger: the first model rule that needs a
  Foundation value without a scenario asking for it. It is not this slice's.
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

Two more the user should see rather than read about. The scenario detail
screen loses 14 L/h and 500 L, which is the visible half of the seam repair
and the first time the document asks a question it does not answer. And every
failure of a Foundation-owned value now blocks where one of them used to
refuse, so the demo path for a misconfigured Site is a Draft to inspect
instead of an error.
