# T021A - Narrow reported-observation declarations

Status: planned
USER_REVIEW_REQUIRED: false

Map: A starter.
Depends on: T021 in queue order; existing strict scenario parser.
Next: T022.
Branch: task/T021A-reported-observation-requirement-closure
Sizing: small boundary narrowing, independently reviewable.

## Outcome

Scenario detail shows reported-observation declarations without an execution
requirement claim. An authored observation carrying execution_requirement is
refused with an inspectable structural error.

Keep this after T021 and before T022, as required by v4.
The kernel does not consume this field and did not need the change to execute.

## Read for detail

- v4 sections 2.1 and 24.
- Starter handoff: T021A row and Contract Versions.
- DECISIONS: D-2026-09-22-contract-version-scope.
- Shared checks and exclusions: tasks/README.md.

## Acceptance criteria

1. REPORTED_OBSERVATION has no execution_requirement field in the strict
   authored-document structure. Presence is rejected rather than ignored.
2. Shipped Fuel Loss observations use the narrowed structure and still render
   as declarations in scenario inspection.
3. Executable causes retain their requirement fields and existing validation.
4. Advance EXECUTION_CONTRACT_VERSION from the version found after T021.
   Newly frozen runs carry the new version; existing runs retain their identity.
5. Older frozen content remains inspectable under the existing readback policy.
   Unsupported execution is refused rather than reinterpreted.
6. Reported observations do not become setup support/blocking requirements.
   Publication behavior is still answered by the publication profile.
7. Generated trace, observation values and reconciliation-panel retirement
   remain T022; this task changes only the requirement position and its claims.

## Proof

Use a valid shipped document and a mutation adding execution_requirement to
one reported observation. The valid document parses; the mutation fails at the
strict boundary and identifies the invalid position.

Exercise REQUIRED and OPTIONAL on executable inputs to show that their
contract still works. A previously supported executable cause must not lose
its requirement because the observation field was removed.

Inspect scenario detail and newly frozen run version.
Reload an old frozen run and verify its stored identity remains unchanged.
Run scenario/parser/run regression tests, relevant frontend tests and shared
repository checks. Browser evidence is required only if layout changes.

## Scope limits

This is not another readiness or runtime task.
Do not migrate old runs in place, change executable causes, regenerate the
kernel trajectory or change authored observation values as part of narrowing.

## Review

Independent review is required; no new user checkpoint is needed for this
already-directed parser closure.
Review outcome: pending.
