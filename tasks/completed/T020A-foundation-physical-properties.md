# T020A - Typed component properties and frozen Foundation answers

Status: complete
USER_REVIEW_REQUIRED: true

Map: A starter.
Depends on: completed T020.
Next: T020A1, then T020B.
Branch: task/T020A-foundation-physical-properties
Sizing: boundary-changing; carrier only, addressed resolution is T020A1.

## Outcome

Create a new mini-grid fixture from the updated template.
Its Foundation shows typed physical and component control properties beside
documentary ControlAssumption entries. A Draft resolves its physical inputs
from those configured properties and preserves the answers when reloaded.

This is the first cut because the kernel needs asset values rather than
scenario-owned duplicates. It independently proves the carrier before the
same-type component addressing extension.

## Read for detail

- Starter handoff: Properties and frozen answers; Existing property transition.
- v4 sections 4.1, 5.2, 10, 24 and 27.2.
- CODE_STATE entries T014, T018-T020 for existing carriers and frozen setup.
- DECISIONS: D-2026-09-22-foundation-value-declaration,
  D-2026-09-22-consumption-coefficient-unit,
  D-2026-09-22-capacity-bound-source,
  D-2026-09-22-foundation-property-absent-blocks.
- Shared checks and exclusions: tasks/README.md.

## Deliver

Extend the current single-rating representation to typed per-component
properties across template parsing, Site persistence, readback and Foundation.
Preserve existing ratings and provenance through an explicit compatibility path.

Property keys and their units come from a closed declared vocabulary, matching
the closed rating and signal vocabularies already in the Site parser. A slice
that needs a new property adds it to that vocabulary; authored documents cannot
introduce arbitrary keys. T024's model-owned need declaration extends this
vocabulary rather than opening it.

The minimum physical proof uses tank capacity and generator specific fuel
consumption. The coefficient is L/kWh; consumption laws belong to the profile.
The same carrier holds typed component control values, demonstrated with
battery reserve and generator minimum-runtime properties.
ControlAssumption remains documentary; it is not the executable setpoint.

Migrate the shipped Fuel Loss declarations and profile bindings together.
Foundation-owned parameters declare state, unit and owner with no value slot.
The rule includes capacity, not just the consumption coefficient.
Dispatched output becomes a forcing on generator-output-power.

Keep the tank bound declaration in the scenario.
Resolve its upper value from the frozen Foundation capacity at execution;
static declaration inspection cannot invent an upper numeric value.

## Acceptance criteria

1. A newly instantiated fixture shows multiple typed properties per component
   with units and source/version provenance; the persisted Site reload agrees.
2. Old Site documents remain readable through the documented compatibility
   behavior. A template change leaves pre-existing instances unchanged.
3. Physical and component control properties round-trip through strict parsers.
   Duplicate property identity, invalid unit/value and malformed controls
   produce inspectable validation errors before writes.
4. Foundation-owned scenario parameters containing a value are structurally
   rejected. All shipped Foundation declarations use the new shape.
5. Tank capacity and specific consumption resolve through the selected profile,
   appear in frozen inputs and retain their configured values after reload.
6. Changing one fixture's coefficient changes only its resolved answer.
   Changing scenario dispatch leaves the coefficient unchanged.
7. Missing binding, zero/multiple component matches, absent property or wrong
   unit yield BLOCKED with INITIAL_VALUE_NOT_RESOLVED tied to that input.
   No fallback searches for a convenient value on another asset.
8. INITIAL_VALUE_ANSWERS_DISAGREE and its only producer are retired together.
   Missing scenario/run-owned initialization keeps its existing refusal line.
9. Absent frozen value and canonical value remain absent together and have a
   matching blocking reason. READY has no blocking reasons.
10. The bound declaration survives without a scenario capacity number.
    The Draft freezes the actual Site capacity needed by T021.
11. The Foundation-value narrowing moves EXECUTION_CONTRACT_VERSION from the
    version found at implementation time. Old frozen runs retain their version.
12. New component controls are inspectable typed properties; no controller or
    Site-scoped Controls capability is implied by this screen.

## Proof

Use a newly created fixture, not a rewrite of mg-001/mg-002/mg-003.

| Case | Expected observation |
| --- | --- |
| New template instance | Capacity, L/kWh coefficient and component controls render |
| Existing instance after template update | Prior values and version unchanged |
| Same scenario, changed generator coefficient | Frozen coefficient follows Site |
| Changed dispatch forcing | Frozen coefficient stays fixed |
| Capacity declared with scenario value | Parse refusal |
| Missing property or wrong unit | Persisted BLOCKED, input-specific reason |
| Frozen record reload | Values, absence and provenance preserved |

Check relevant Site/scenario/run parsers and frontend Foundation/run readback.
Run the shared repository checks and layout evidence for changed tables.
The implementation packet identifies the compatibility path and version move.

## Scope limits

Addressed StateRef resolution across the scenario/profile/frozen contract is
T020A1. This task preserves the current unique-candidate behavior until then.
Site-scoped Controls and consumption of control properties arrive in T024-T025.
Kernel execution, model-owned need declaration and generated evidence wait for
their owning tasks. No Site migration or general property authoring UI is needed.

## Review

The owner reviews a new fixture's Foundation and frozen Draft, including the
missing-property BLOCKED case. The Reviewer checks the ownership/version seam.
Review outcome: pending. Packet: `.agent/T020A-review-packet.md`.
