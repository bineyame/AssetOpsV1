# T021A - Reported Observations Carry No Execution Requirement

Status: planned
USER_REVIEW_REQUIRED: false

Intended branch: `task/T021A-reported-observation-requirement-closure`

## Feature

Scenario Catalog And Run Setup. It sits in the M1C range because of when it
has to happen, not because of what it is about.

## UI-Verifiable Screen Behavior

The scenario detail screen for the Fuel Loss Event shows its reported
observations without an execution-requirement claim, and the execution contract
version it reports is the one this slice moved it to. An authored document that tries to put an execution
requirement on a reported observation is refused with an inspectable reason
rather than parsed and ignored.

## Why This Is Next

With run setup no longer adjudicating cause-to-observation coupling, `REQUIRED`
on a value no executor reads is either vacuous or a category error. The meaning
it was carrying — *this run must produce such a reading* — already has a home
in the private expectations under `DETECTION` and `TIMING`. Closing it at the
parser is free while no golden trace exists, and T022 is the slice that first
produces one.

**Why this is its own slice, decided by the user on 2026-09-22.** Folding this
into T022 would make that slice's internal ordering load-bearing, because the
parser change would have to land before trace generation inside one slice, and
would close the window entirely if T022 were ever split. It also keeps T022's
user-review checkpoint on runtime control semantics rather than mixing an
authoring-contract change into it. It sits after T021 rather than before
because the kernel never reads `execution_requirement` on a reported
observation, so nothing about the kernel depends on it either way.

## Dependencies

- T018's execution contract and its strict parser.
- T019's narrowing, merged: the observation blocking reasons are already gone,
  so removing the field changes no run-setup outcome.
- The version ledger, for what the number is when this slice starts. It is not
  2 by the time this runs and no criterion here assumes a value.

## Acceptance Criteria

- The strict parser gives `execution_requirement` no position on a
  `REPORTED_OBSERVATION`. Its presence refuses the document, closed at the
  structure the way duration units were closed at the unit vocabulary rather
  than as a rule applied after parsing.
- The shipped Fuel Loss document's reported-observation entries lose the field.
  Nothing else in that document changes in this slice; the authored values and
  their removal belong to T022.
- `EXECUTION_CONTRACT_VERSION` moves by one from whatever this slice finds,
  under the policy that the number moves when the space of conforming
  behaviours changes, including when it narrows, and never for wording. The
  literal is not written here: the count for the sequence is stated once, in
  `.ai/FEATURE_MAP.md` under *The execution-contract version ledger*, and
  T020A and the four-semantics declaration both move it before this slice.
- The new version reaches the frozen identity of runs set up after it. A Draft
  already frozen under the previous version keeps what it was frozen under;
  nothing rewrites a persisted identity.
- The scenario detail screen reports the new contract version and shows no
  execution-requirement claim on a reported observation.

## Required Product And Domain Semantics

- The `REPORTED_OBSERVATION` role is unchanged and becomes more necessary, not
  less: it is precisely what stops an authored reading reaching a transition.
  Its meaning is an expectation about what a run should produce, which no
  executable path may read.
- A contract version identifies a space of conforming behaviours, not a text.
  Playback refuses a provenance mismatch, so a version that moved for prose
  would force regeneration of valid traces.

## Protected Seams

- Authoring-contract closure at the parser: a prohibition is structural, not a
  rule someone has to remember.
- Contract-version identity: the number moves with the space and reaches frozen
  provenance.
- Expectation position: the meaning `REQUIRED` was carrying is not recreated
  under another name on the executable path.

## Focused Tests And Review Evidence

- Parser refusal test whose deliberate violation is one the rest of the system
  would otherwise accept, so it measures the new prohibition rather than an
  existing guard.
- A test proving the field remains accepted where it is still legitimate.
- A contract-version test that checks the move against the declared rule set
  rather than against a literal, which is also the T018 round-two finding
  about a weak version test.
- Frozen-identity test: a new Draft freezes the moved version and an existing
  persisted Draft is unchanged, asserted against the constant rather than
  against a literal.
- UI test for the scenario detail screen's reported-observation rows and
  version display.
- Run architecture/workflow checks, relevant suites, typecheck, and build.

## Scope Limits

- No other execution-contract change, no kernel change, and no observation
  transform.
- No removal of the authored reading values; T022 owns that.
- No change to the reconciliation panel or its payload.

## User Review

No new user checkpoint. The semantics were accepted in amendment 1 on
2026-09-21 and the slice's placement was accepted on 2026-09-22; this slice
implements both.
