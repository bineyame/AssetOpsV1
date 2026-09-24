# T020A1 - Addressed bindings from scenario to frozen initialization

Status: planned
USER_REVIEW_REQUIRED: true

Map: A starter.
Depends on: T020A.
Next: T020B.
Branch: task/T020A1-addressed-foundation-bindings
Sizing: boundary-changing; immediate follow-on to the property carrier.

## Outcome

A Draft containing two components of the same type freezes distinct addressed
answers. Its detail shows which asset supplied each input.
An unqualified binding that could refer to either asset blocks visibly.

This is immediate work: T021 must receive resolved addresses, and T024's three
loads must not require replacing a global-state identity contract later.

## Read for detail

- v4 sections 4.2, 5.2, 10, 24 and 27.2.
- Starter handoff: Properties and frozen answers; Contract Versions.
- DECISIONS: D-2026-09-22-contract-version-scope.
- Shared checks and exclusions: tasks/README.md.

## Deliver

Carry StateRef through SupportedState addressing rules, FoundationBinding,
scenario state references, input resolution and FrozenInitializationInput.
Keep state_key semantic; keep component identity in its selector.

SITE references have no component id.
COMPONENT references resolve a concrete component id before READY.
An explicit id selects that component and validates its required type/property.
An omitted id resolves only a unique valid candidate.

Move every affected frozen-input comparison and lookup to the addressed key.
This includes duplicate detection, matching blocking reasons and inspection.
Two components using the same semantic state are independent requirements.

## Acceptance criteria

1. A strict parser accepts explicit component selectors and valid SITE refs,
   and rejects malformed scope/id combinations with an inspectable reason.
2. Two same-type components with different properties resolve independently
   under the same state_key. Frozen values keep their respective StateRefs.
3. SupportedState declares scope independently of concrete fixture ids;
   reusing the profile on another Site resolves that Site's components.
4. Explicit selection of a missing/wrong component or missing property blocks
   the affected input. Another matching component cannot satisfy that selector.
5. An unqualified component binding with one candidate resolves; zero or more
   than one leaves it unanswered and BLOCKED.
6. Unit mismatch remains a Foundation-resolution blocking condition.
7. Duplicate declarations for one addressed input are handled consistently;
   two different component ids are not collapsed as duplicate global state.
8. Requirement conflicts are detectable at the resolved address/role grain.
   T020B owns their final refusal behavior.
9. Scenario/run-owned dynamic initialization uses addressed states too.
   A component's initial fuel/SOC value cannot initialize a sibling.
10. Frozen inputs, deterministic identity serialization and Draft reload retain
    the resolved address and provenance. Reordering unrelated components does
    not change the selected answer.
11. Run detail distinguishes same-type assets and places a blocking reason
    beside the matching unresolved input.
12. The shipped Fuel Loss contract is migrated to the addressed form without
    claiming that its remaining T020B readiness work is complete.
13. Advance the execution contract when addressed resolution changes outcomes
    for previously valid documents; record the relative transition.
    Preserve prior frozen runs for inspection and refuse incompatible execution.
14. Component controls use the T020A carrier and remain associated with their
    component through freezing; no Site Controls table is introduced here.

## Proof

Create a fixture with two fuel-bearing components and different capacities.
Resolve both explicitly, reload the Draft and inspect the two answers.
Repeat after reordering the components and after changing only the second value.
The first answer must stay stable.

Repeat setup with the selector removed: the same declaration blocks for
ambiguity. Remove one candidate: it resolves to the sole remaining component.
Use a missing explicit id with another suitable component present: it blocks.

Add a repeated-load binding fixture for LOAD-RES and LOAD-MILL.
It proves addressability at setup only; electrical execution belongs to T024.

Test strict source parsing and frozen record reconstruction.
Exercise SITE refs, wrong type, unit mismatch and distinct dynamic initial values.
Run the shared repository checks and layout evidence for input tables.

## Scope limits

No late deferred StateRef migration remains after this task.
Profile capability expansion, forcing windows and boundary timing belong to
T020B; physical evolution belongs to T021/T024.
Do not introduce a general topology editor or repeated-component authoring UI.

## Review

The owner reviews two resolved same-type inputs and the ambiguous BLOCKED case.
The Reviewer checks every frozen identity/readback path, not just the setup form.
Review outcome: pending.
