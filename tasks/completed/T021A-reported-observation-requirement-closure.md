# T021A - Narrow reported-observation declarations

Status: complete
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

## Execution rule

This slice is in the queue because it is cheap now and expensive after traces
freeze, not because it is product progress. Implement the narrow parser closure
and stop. No architectural discussion, no readiness rework, no vocabulary
debate. If it grows beyond the narrow closure, stop, say so, and move it out of
the critical path rather than delaying T022.
`Docs/queue-review-feedback-verbatim.md` asked for exactly this time-box.

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
Review outcome: accepted.

**Independent review, 2026-09-27**, by a fresh Claude `assetops-reviewer` under
`.ai/ROLE_CONFIG.md`'s verification routing rather than by Codex, to conserve
Codex quota for discovery. Seven of seven criteria met, the slice stayed inside
its Execution-rule time-box, 8 of 8 guard probes reproduced independently, and
the reviewer verified criterion 5 across all 165 stored runs rather than the
packet's sample of two. It judged the round correctly classified - nothing it
found required a reader to decide anything - and named two places a Codex pass
would add something: the 6-to-7 move itself, since a contract version move is
listed as Codex work, and R-3's strictness question.

Two findings were fixed before closeout, both coordinator errors in durable
records rather than product defects: `.ai/CODE_STATE.md` said no backlog entry
was written when the coordinator had written one after the packet closed, and
the backlog's account of the `var/scenarios/` edit blamed an incomplete
instruction when `tasks/README.md:134` already covered all of `var/`. The
correct account is that a standing scope limit was overridden by necessity and
ratified by the owner.

Carried rather than fixed, in `.ai/MILESTONE_REVIEW_BACKLOG.md` and the review
file: a present-but-null requirement on a reading is ignored rather than refused,
which is the parser's convention at every comparable position; criterion 6's
behavioural negative is unasserted though its regressions are caught; a repeated
test literal; and that no stored Draft is executable under version 7, which
T022's dispatch needs.

No owner checkpoint was outstanding - `USER_REVIEW_REQUIRED` is false and the
owner had already ruled on the `var/scenarios/` edit.
