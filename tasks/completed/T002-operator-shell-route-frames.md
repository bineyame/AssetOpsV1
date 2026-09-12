# T002 - Operator Shell Route Frames

Status: completed
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

## Review Outcome

Reviewer verdict: accept with follow-ups. No blocking findings. All five
acceptance criteria assessed as met, plus the focused-test line requiring an
import/architecture check that operator code does not import simulator modules.

Reviewer notes on the task spec: parameterless `/site-details` and
`/site-configuration` were judged correct, because `/sites/:siteId` before a
Site identity contract would have implied a product decision T002 explicitly
avoids. It does not foreclose Site Foundation later adding identified routes or
redirects. Deferring the user-review checkpoint to T003 was judged reasonable.

Follow-ups raised:

1. `tools/check-architecture.ps1` was brittle around excluded directories. It
   recursed before filtering, so an unreadable `.pytest_cache` aborted the whole
   scan under `$ErrorActionPreference = "Stop"`. ADDRESSED in this slice: all
   three scans now use a shared `Get-SourceFiles` helper that prunes ignored
   directories before descending and reports unreadable directories without
   failing the run. Verified by injecting one violation per banned direction
   plus a decoy inside `.pytest_cache`: all three real violations were reported,
   the decoy was correctly ignored, and the guard returned clean after removal.
2. The "no digits inside `<main>`" assertion in `operatorRouteFrames.test.tsx`
   is acceptable for this empty-frame slice but intentionally brittle. It must
   be REPLACED with evidence-specific "no fabricated operational values"
   assertions once legitimate identifiers, dates or counts become truthful UI
   content — not loosened.
