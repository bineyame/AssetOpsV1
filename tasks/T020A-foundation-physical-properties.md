# T020A - Foundation Physical Properties And Model-Rule Carriers

Status: planned
USER_REVIEW_REQUIRED: true

Intended branch: `task/T020A-foundation-physical-properties`

## Feature

Draft SimulationRun And Causal Runtime. Block A of `.ai/FEATURE_MAP.md`.

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
to answer, and the document now declares the need and states no value.

## Why This Is Next

T021's kernel cannot move the tank without a consumption coefficient, and the
shipped Fuel Loss document supplies it as `generator-fuel-rate` - a machine's
physical property living in the story. The first kernel sets the shape every
kernel after it copies, so the coefficient comes from Foundation before the
kernel exists rather than after.

Three carriers are missing and must move together, because any one alone
leaves a declarable owner with no answer: Foundation carries one optional
scalar per component, `FoundationBinding` can address only that scalar, and
`SupportedState` has no field a model-rule value could occupy
(`D-2026-09-21-physical-property-ownership`). A fourth question none of them
answers is what tells run setup the run needs the coefficient once
`generator-fuel-rate` leaves the scenario, and
`D-2026-09-22-foundation-value-declaration` settles it: a Foundation-owned
scenario parameter has **no value position at all**. A value position an
author may fill is one an author will fill.

### What this slice carries and what it does not

v4 §24 and §27.2 require this sizing call before implementation. It is made
here and is not the Implementer's to revisit. Three separable concerns sit near
this slice:

**A. The typed per-component property carrier - this slice.** Foundation and
templates carry named physical properties; a binding addresses one by name;
`SupportedState` can carry a model-rule value; a Foundation-owned scenario
parameter loses its value position.

**B. Component-addressed binding and frozen `StateRef` resolution - not this
slice.** An explicit `component_id` on a binding, a `SITE`/`COMPONENT`
addressing rule on `SupportedState`, component selectors in scenario state
references, and a frozen resolved `StateRef` rather than a frozen string key.
MG-001 has one generator and one tank, so a component-scoped binding resolving
against a single candidate is already correct; `StateRef` exists to separate
two loads or two chargers, which is Block I and not a Site that exists today.
B also reshapes the frozen deterministic identity, which this slice already
reshapes once by giving it a Foundation answerer for a named property, and
doing that twice in one slice is the unreviewability v4 raised.

**C. Site-scoped typed control properties - excluded by v4 §5.2 and §24.**
They land with the first controller slice, when source merit order or
critical-load priority is actually consumed.

**One rule from B is not deferred**, because it is free now and a migration
later: the binding-resolution criterion below. Land it in the carrier and B
becomes an extension rather than a rewrite of every frozen binding.

## Dependencies

- T019's frozen-inputs resolution and blocking reasons, merged.
- T020 for sequencing only; nothing in front of this slice is blocked.

## Acceptance Criteria

- The coefficient's canonical unit is `L/kWh`, specific fuel consumption, a
  property of the machine alone. `L/h` is machine times operating point and the
  point is the scenario's (`D-2026-09-22-consumption-coefficient-unit`).
- `dispatched-output` is promoted from `NON_EXECUTABLE_CONDITION` to a
  `FORCING_INPUT` on `generator-output-power`, and `generator-output-power`
  joins the shipped model profile's supported states. Both belong here: under
  `L/kWh` the coefficient is not a rate over time, so the dispatch event stops
  naming a rate and the model rule - consumption is specific consumption times
  energy delivered - owns the transition. Promoting later would publish a
  document whose model rule depends on a state nothing declares, and T020B and
  T021 both depend on this slice carrying it.
- A Site component and a template component can declare named physical
  properties beyond `rating`, each with a value and a canonical unit. Which
  property names a component may declare is defined per component type and
  enforced by the strict parser: an unknown name, a name on the wrong component
  type, an unknown or dimensionally wrong unit, or a repeated name refuses the
  document rather than being ignored. User-authored configuration reaches these
  properties through that same parser; there is no second, lenient path.
- `FoundationBinding` can address a named property on a component type, not
  only `rating` by unit, and existing rating bindings keep their meaning and
  their resolution behaviour.
- **A component-scoped binding addresses a component either by an explicit
  identifier or by resolving against exactly one candidate.** Zero candidates
  and more than one candidate both leave the value unanswered and block the
  run; neither takes the first match. **A component identity is never encoded
  into a state-key string** - `GEN-001.specific-fuel-consumption` as a state
  key is precisely the failure this rule exists to prevent. The semantic state
  name and the runtime address are different concepts, and merging them costs
  the reusable state vocabulary and makes ambiguity undetectable.
- `SupportedState` can carry a model-rule value. A scenario declaring
  `owner: MODEL_RULE` resolves its value from the selected model profile and
  the frozen identity records `MODEL_PROFILE` as that value's origin, closing
  the T019 review's L9 finding: the owner was declarable and the answerer
  correctly named, with nowhere for the answer to live. An owner the selected
  profile carries no value for blocks on `INITIAL_VALUE_NOT_RESOLVED` and
  produces no default; one kind carries every such case and this slice adds no
  second.
- A scenario parameter whose declared owner is `SITE_FOUNDATION` has no value
  position. The parser gives it nowhere to state a number and refuses a
  document that states one; it still declares the state, the unit and the
  owner. The rule keys on the declared owner, the only thing the document
  carries that distinguishes these parameters: the binding lives in the model
  profile and the scenario parser sees no profile at all.
- So the shipped document loses two numbers, not one. `generator-fuel-rate`
  becomes Foundation-owned and its 14 L/h goes; `tank-capacity` is already
  Foundation-owned and its 500 L goes with it. Exempting the second would need
  a field invented for the exemption, and it carries the same defect today.
- The `fuel-tank-volume` upper bound leaves the document with `tank-capacity`'s
  number and the `bounds` declaration stays, so **the parser must keep
  accepting a `bounds` block on a parameter that states no value**: which world
  state caps which is a relationship between two states, not a property of a
  machine. `declared_bounds` then reporting no upper value for
  `fuel-tank-volume` is the right answer and not a gap
  (`D-2026-09-22-capacity-bound-source`).
- `ControlAssumption` is untouched and stays documentary: identity, subject,
  basis and prose. It gains no setpoint, no value and no state model. Typed
  control properties are a separate carrier that will sit alongside it, and
  they are concern C above (v4 §5.2).
- `EXECUTION_CONTRACT_VERSION` moves by one here. The shipped document as it
  stands is refused by the new parser, so this narrowing reaches a document
  that already exists. The count for the sequence is stated once, in
  `.ai/FEATURE_MAP.md` under *The execution-contract version ledger*; no task
  file writes the literal.
- `INITIAL_VALUE_ANSWERS_DISAGREE` is retired here, in the slice that removes
  its last producer: it compared a scenario-stated value against Foundation's,
  and no document can state one any more. `.ai/ARCHITECTURE.md` carries the
  consequence and the re-illustrated naming rule; this slice removes the kind
  and proves it has no producer left.
- The shipped site template declares the coefficient as a named property with
  its canonical unit, and run setup freezes it from Foundation and records its
  origin. All five ways it can fail block and produce no default: no binding
  declared, no match, more than one match, the wrong unit, and a Foundation
  that declares no such property at all. The last is a fifth case of the same
  thing rather than a refusal, because the binding now names the property as
  well as the component type, so a different profile naming a different
  property may find something this Foundation does declare
  (`D-2026-09-22-foundation-property-absent-blocks`).
- **MG-001 carries the property**, re-created from the updated template or with
  the property added to the instance. Templates instantiate by copy, so editing
  the template alone leaves a demo site whose Drafts block on the missing
  coefficient and this slice's own UI-verifiable outcome never appears.
  `mg-002` and `mg-003` stay in `var/sites/`; do not clear the directory.
- The header comment of `config/scenarios/fuel-loss-event.yaml` says its
  numbers are the T017 checkpoint's and unchanged. This is the first slice to
  edit that file, so the header stops being true here and is corrected with it.
- Site Configuration's Key Parameters panel shows the declared property with
  its unit. The panel's existing rule holds: an entry appears because the
  record declares it, and a component that declares nothing produces no row.

## Required Product And Domain Semantics

- The four owners and the two swap tests that decide between them are in
  `D-2026-09-21-physical-property-ownership`. What this slice needs: swap the
  asset and the value changes, so it is Foundation's.
- A coefficient and the law that consumes it are different objects with
  different owners. *What this generator burns per kWh delivered* is
  Foundation. *Consumption is specific consumption times energy* is the rule.
- Declaring an owner is not the same as being able to carry its value, and
  stating a number is not the same as declaring a need. Something must hold
  what an owner declares, something must be able to address it, and the
  document must be able to ask without answering.
- A Foundation says how large a tank is, never how full. Starting fuel level
  stays a scenario input and keeps its value position.

## Read When You Reach It

- `Docs/simulator_design_v4.md` §4.2, for why the semantic state name and the
  runtime address stay separate, and for the four contract changes the
  addressing extension will need when B lands.
- v4 §10.1, for the Foundation / scenario / publication ownership split, which
  this slice does not change.

## Protected Seams

- Physical property ownership: the coefficient a later product conclusion uses
  comes from Foundation configuration, never from the scenario's private rate,
  and the document has no position to state one from.
- Strict parsing at the configuration boundary: shipped and user-authored
  configuration cross the same parser.
- Template-instantiates-by-copy: a template change never reaches an existing
  instance, so the instance is updated deliberately and visibly.
- Frozen identity provenance: every frozen value names its origin, and the
  origin shown on screen is the origin recorded on the record.
- Standing for this range, one line rather than repeated per criterion: no
  product conclusion in a scenario fixture; no private oracle value turned into
  evidence; no manufactured default hiding a missing answer; no simulator
  import of the backend.

## Focused Tests And Review Evidence

- Parser tests covering an accepted property, an unknown property name, a
  property declared on a component type that does not allow it, an unknown or
  wrong-dimension unit, and a repeated name; plus a test that user-store
  configuration crosses the same strict path as shipped configuration. At least
  one deliberate violation must be one the rest of the system would otherwise
  accept, or it measures a different guard than the one it names.
- Binding tests for named-property resolution, unchanged rating-binding
  behaviour, blocking on zero and on multiple matching components, and a state
  key carrying a component identity refused rather than resolved.
- Model-rule carrier tests: a `MODEL_RULE` owner resolves from the profile with
  `MODEL_PROFILE` recorded as origin; an uncarried `MODEL_RULE` owner blocks.
- Run-setup tests: the coefficient freezes from Foundation with Foundation
  origin, the scenario no longer supplies it, each of the five ways it can fail
  to resolve blocks rather than refusing or falling back including an absent
  property, and the promoted `generator-output-power` blocks nothing.
- Parser test refusing a Foundation-owned parameter that states a value, whose
  deliberate violation is the shipped document as it stands today.
- A test proving `INITIAL_VALUE_ANSWERS_DISAGREE` has no producer left, and
  that the two vocabularies are still disjoint without it.
- `test_the_declared_bound_is_declared_rather_than_guessed` may not be updated
  to match the new return value: both of its halves return `(0.0, None)` after
  this slice, so a matching assertion leaves a test whose control and whose
  case are identical. The property splits: the bound is *declared* rather than
  inferred from a shared state-key prefix, where removing the `bounds` block is
  still observable; and the capacity *is 500 L resolved from MG-001's
  Foundation*, asserted on the frozen identity and new rather than moved,
  because both places asserting 500 today are removed here.
- A contract-version test that checks the move against the declared rule set
  rather than against a literal, and a frozen-identity test that a Draft
  frozen under the previous version keeps it.
- Fixture proof that MG-001 carries the property and that `mg-002` and `mg-003`
  still load.
- UI tests for the Key Parameters row, the frozen-inputs origin label with no
  digit the record does not supply, and `dispatched-output` presenting as a
  forcing input on `generator-output-power` with the dispatch event naming no
  rate. Layout evidence for both tables.
- `tools/check-architecture.ps1`, `tools/check-agent-workflow.ps1`, the backend
  and frontend suites this slice touches, typecheck, and build.

## Scope Limits

- Concerns B and C above are out, for the reasons under *What this slice
  carries*. An Implementer who finds A genuinely cannot land without a piece of
  B stops and says so rather than widening the carrier quietly.
- The minimum property set only: the generator's specific fuel consumption.
  Efficiency curves, minimum load, ramp rate, tank geometry, sensor placement,
  battery chemistry, PV tilt, orientation and derate stay absent; the first
  kernel models none of the things they affect. The tank's minimum usable level
  is the honest home for the floor the validation layer invents, and it is a
  follower: moving that floor belongs to a slice that says it is doing so and
  carries the test.
- No kernel, execution, runtime state, observation transform, golden trace,
  gateway staging, ingestion, analytics or Finding. No Foundation edit path.
- Option C in `.ai/FEATURE_MAP.md`'s Open Questions - the model profile
  declaring the need rather than the scenario - is a named follower with its
  own trigger. Whether the product's own later expectation reads this same
  coefficient or a separately declared operating assumption is a Block F
  question; this slice supplies the coefficient and decides nothing about who
  else reads it.

## User Review

User review is required; the user took this checkpoint on 2026-09-22. The
per-component-type physical property vocabulary is a durable configuration
contract in the same family as the breaker/control vocabulary, the Key
Parameters panel is a user-facing surface gaining a new row, and re-creating
MG-001 changes the demo site the rest of M1 is shown on.

Review focus: the property name and its unit; whether Key Parameters should
present a physical property differently from a design rating; and the
frozen-inputs origin label showing the coefficient coming from site foundation.
Two more the user should see rather than read about: a document that asks a
question it does not answer, the first time this product has one; and a
misconfigured Site producing a Draft to inspect where one of these failures
used to produce an error.
