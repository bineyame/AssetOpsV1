# T001 - Stack Shell Skeleton

Status: completed
USER_REVIEW_REQUIRED: false

Intended branch: `task/T001-stack-shell-skeleton`

## Feature

Stack, Shell, And Gate.

## UI-Verifiable Screen Behavior

The chosen FastAPI + React/TypeScript app stack can render an operator shell
route frame and a Simulator Lab-disabled shell frame from the running app, with
empty/no-data states and no real Site, simulator, ingestion, analytics, editing,
or Finding behavior.

## Why This Is Next

This is Causal Sequencing step 1: there is no executable product surface or CI
shape until the MVP stack and modular-monolith skeleton exist.

## Acceptance Criteria

- The app starts with a FastAPI backend, React/TypeScript frontend, and Python
  simulator root in the modular-monolith shape named by the architecture docs.
- The UI renders a minimal operator shell route frame without real Site data.
- The UI renders a Simulator Lab-disabled shell frame or equivalent unavailable
  frame without serving simulator execution behavior.
- Empty route frames explicitly communicate empty/no-data states rather than
  placeholder operational values.
- CI guard placeholders exist for expected backend/frontend/simulator roots and
  dependency direction.
- No Site schema, simulator execution, ingestion, analytics, configuration
  editing, or Findings are implemented.

## Required Product And Domain Semantics

- This slice establishes implementation posture only; it does not define Site,
  evidence, simulator run, or finding semantics.
- Empty states must not imply operational evidence exists.
- Simulator execution remains unavailable.

## Protected Seams

- Stack and module direction: CI guard.
  The skeleton must preserve FastAPI, React/TypeScript, Python simulator,
  strict parser posture, file-backed repository posture, and no direct
  UI-to-simulator imports or simulator-to-product writes.

## Focused Tests And Checks

- Backend smoke test for a health or root route.
- Frontend smoke/render test for the operator shell empty route.
- Frontend smoke/render test for the Simulator Lab-disabled shell frame.
- CI architecture check placeholder for expected roots and banned dependency
  directions.
- Run `tools/check-agent-workflow.ps1`.

## Scope Limits

- Do not add real Site data, Site schema, simulator routes, simulator execution,
  ingestion, analytics, editing, or Findings.
- The UI should show empty/no-data states for product content that does not
  exist yet.

## User Review

User review is not required for this slice because it creates the technical
skeleton and non-final empty frames. The review checkpoint is held for the
completed Stack, Shell, And Gate feature when the shell hierarchy and simulator
gate surface are both visible.

## Review Outcome

Reviewer verdict: accept with follow-ups. No blocking findings. All six
acceptance criteria assessed as met, including criterion 5 as written
("CI guard placeholders", not a wired pipeline).

Follow-ups raised:

1. Run commands were not reliably invocable under a restrictive PowerShell
   execution policy (`npm.ps1` and unsigned `tools\*.ps1` are blocked).
   Addressed by `README.md`, which documents policy-proof invocations.
2. The "zero buttons and zero links" assertion in
   `SimulatorLabUnavailableFrame.test.tsx` is acceptable for T001 but is not a
   simulator boundary test. T003 must test route/API unreachability and
   specific forbidden run actions rather than relying on this pattern.

Reviewer note on the task spec: "CI guard placeholders" did not say whether CI
requires a pipeline hook or an executable guard script. Resolved in favour of
the script for T001; wiring a runner remains open.
