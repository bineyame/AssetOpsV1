# T002 - Operator Shell Route Frames

Status: planned
USER_REVIEW_REQUIRED: false

Intended branch: `task/T002-operator-shell-route-frames`

## Feature

Stack, Shell, And Gate.

## UI-Verifiable Screen Behavior

The operator shell exposes route frames for Sites, Site Details, and Site
Configuration, each with explicit empty/no-data states. The frames make the
first operator navigation structure visible without introducing Site schema or
operational claims.

## Why This Is Next

This extends Causal Sequencing step 1 after the stack skeleton: later Site and
configuration slices need stable route frames before they can render truthful
Site/Foundation content.

## Acceptance Criteria

- Sites, Site Details, and Site Configuration routes render from the app shell.
- Navigation between these operator routes works without simulator surfaces.
- Each route shows a clear empty/no-data or unavailable state, not fabricated
  zero values, charts, health, analytics, Replay, or Findings.
- Site Details and Site Configuration frames do not require a real Site schema
  yet and do not hard-code MG-001 as product truth.
- The shell does not expose Simulator Lab entry points before the feature gate
  task defines serving behavior.

## Required Product And Domain Semantics

- Operator routes may exist before configured Sites exist.
- No evidence means no operational values, source health, analytics, Replay, or
  Findings.
- Route labels and empty states should preserve the distinction between product
  operator surfaces and simulator execution surfaces.

## Protected Seams

- Stack and module direction: CI guard.
  Operator presentation must stay inside the chosen frontend/backend shape and
  must not import simulator runtime modules.
- Simulator/product boundary: CI guard.
  Operator frames must not show simulator truth, findings, health,
  reconciliation, or other product conclusions from simulator modules.

## Focused Tests And Checks

- UI routing test for Sites, Site Details, and Site Configuration route frames.
- UI assertions that route frames show empty/no-data or unavailable states.
- Import/architecture check that operator read models and UI do not import
  simulator runtime/truth modules.
- Run `tools/check-agent-workflow.ps1`.

## Scope Limits

- Do not add Site schema, YAML Site/Foundation fixtures, simulator execution,
  ingestion, charts, source health, analytics, Replay, editing, Save/Publish, or
  Findings.
- The UI should say that Site/configuration content is unavailable or empty
  rather than implying hidden data exists.

## User Review

User review is not required at this intermediate slice. It contributes to the
shell information hierarchy, but the checkpoint is placed after T003 so the
user can review the shell and enabled/disabled Simulator Lab surface together.
