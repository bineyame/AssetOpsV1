# T003 - Simulator Lab Feature Gate

Status: completed
USER_REVIEW_REQUIRED: true

Intended branch: `task/T003-simulator-lab-feature-gate`

## Feature

Stack, Shell, And Gate.

## UI-Verifiable Screen Behavior

`simulator_lab.enabled` controls Simulator Lab routes, navigation, entry
points, execution actions, and truth overlays at serving boundaries. With the
flag off, operator routes still work and Simulator Lab URLs/entry points are
unreachable. With the flag on, the empty Simulator Lab shell can be reached.

## Why This Is Next

This is Causal Sequencing step 2 and completes the first review-bounded
feature. Once simulator routes exist, gating must be enforced immediately so
truth and execution surfaces are not left reachable by direct URL or API calls.

## Acceptance Criteria

- Configuration includes `simulator_lab.enabled` with tested enabled and
  disabled behavior.
- With the flag disabled, Simulator Lab navigation and entry points are absent
  from the UI.
- With the flag disabled, direct Simulator Lab routes and execution-related API
  paths return a served-unavailable/not-found state.
- With the flag disabled, operator routes from T002 still render.
- With the flag enabled, an empty Simulator Lab shell route renders without run
  execution, truth overlays, ingestion, analytics, or Findings.
- The UI makes runs unavailable when disabled: runs cannot be started,
  inspected, rerun, or compared to truth.
- The gate is enforced at route/API serving boundaries, not only hidden in
  navigation.

## Required Product And Domain Semantics

- Simulator Lab gating controls simulator surfaces and execution only.
- Existing or future product Site history, simulated provenance, accepted
  evidence, operator routes, analytics, and Replay must remain separate from
  simulator execution gating.
- Simulator truth overlays are not product evidence and must not be reachable
  when the gate is disabled.

## Protected Seams

- Simulator feature gate: CI guard.
  `simulator_lab.enabled=false` must mean simulator routes, entry points,
  execution APIs, and truth overlays are not served while operator routes still
  work.
- Simulator/product boundary: CI guard.
  Simulator Lab owns world/truth/execution/staging; AssetOps owns evidence,
  analytics, findings, and operator presentation.
- Stack and module direction: CI guard.
  Gate implementation must preserve modular roots and avoid UI-to-simulator
  imports or simulator-to-product writes.

## Focused Tests And Checks

- Route/API/navigation test with `simulator_lab.enabled=false` for absent
  navigation, unreachable direct routes, unreachable execution APIs, and working
  operator routes.
- Route/API/navigation test with `simulator_lab.enabled=true` for reachable
  empty Simulator Lab shell.
- UI test that disabled mode exposes no run start, inspect, rerun, truth
  comparison, or execution action.
- Architecture/import check for simulator/product boundary.
- Run `tools/check-agent-workflow.ps1`.

## Scope Limits

- Do not add Site schema, simulator execution, run setup, recorded playback,
  gateway staging, ingestion, analytics, Replay, source health, configuration
  editing, or Findings.
- With the flag off, the UI has no simulator entry points and direct routes
  return unavailable/not-found.
- With the flag on, the Simulator Lab shell is empty and explicitly has no run
  behavior yet.

## User Review

User review is required because this completes the first checkpoint named by the
Architect: shell information hierarchy and enabled/disabled Simulator Lab
surface. Planning stops here until the user approves or redirects this product
direction and UI/UX expectation.

## Review Outcome

Reviewer verdict: accept with follow-ups. No blocking findings. All seven
acceptance criteria assessed as met. The Reviewer confirmed independently that
this is "a real gate, not navigation hiding with extra ceremony", and verified
the author's vacuous-test claim directly: naive `app.routes` saw only docs and
openapi paths, while `route_inventory.served_paths` saw `/api/health` and
`/api/simulator-lab/status`.

Reviewer notes on the task spec: the "entry points" requirement would have been
partly vacuous without an enabled-state nav entry, so the added Simulator Lab
nav item was justified scope. The task says "CI guard" but the repository still
has manually run guard scripts and no CI runner — consistent with prior slices,
but the wording remains stronger than the environment.

Packet correction accepted: "one file means no drift" was an overstatement. One
source file reduces drift, but frontend build time and backend process start are
separate evaluation moments.

Follow-ups raised, none actionable inside T003:

1. ARCHITECT ACTION NEEDED. Runtime frontend gating is acceptable here, but the
   disabled bundle still contains `SimulatorLabFrame.tsx`, because the gate
   removes route reachability rather than code. Harmless while the frame is
   empty. Before simulator truth overlays land, this must become an explicit
   seam with a concrete check: simulator truth must arrive only from gated APIs
   and must never be embedded in frontend modules or build-time fixtures. The
   existing "Private truth isolation" seam row names operator UI but its
   concrete test covers only envelopes and conclusions, so this is a genuine
   gap in `.ai/FEATURE_MAP.md`, not something an implementation slice can close.
2. `backend/tests/route_inventory.py` depends on FastAPI's internal
   `original_router`. The replacement is non-vacuous, but upgrade-sensitive.
   Keep the loud failure; revisit on FastAPI upgrades.
3. The URL guard in `tools/check-architecture.ps1` blocks quoted simulator URL
   literals outside gated modules but cannot catch dynamically constructed
   paths, and exempts tests. Acceptable for this slice; route/API inventory
   tests remain the stronger boundary proof.
4. The carried-forward "no digits inside `<main>`" assertion was correctly NOT
   replaced, because no truthful operator values render yet. It now exists in
   two places: `operatorRouteFrames.test.tsx` and `simulatorLabGate.test.tsx`.
   The instruction still stands for both — replace with evidence-specific
   assertions once real identifiers, dates, counts, ratings or values render.
   Never loosen.

This slice completes the Stack, Shell and Gate feature and carries the
checkpoint deferred from T001 and T002.

## User Review Outcome

User review completed 2026-09-12. Verdict: accept with one follow-up action.

The gate itself is accepted as implemented and tested: with
`simulator_lab.enabled=false` no simulator route, entry point, execution API or
truth overlay is served while operator routes still render, and with the flag
enabled the empty Simulator Lab shell is reachable. No rework is required inside
this slice, and its route/API boundary tests stand as written.

One correction was raised against the enabled-state shell hierarchy. Compared
with the v6.9 product document, Simulator Lab is a separate developer workspace,
not an operator navigation item, so the Simulator Lab entry this slice added to
operator navigation sits at the wrong boundary. The gate is correct; the visible
entry point is not.

That follow-up is not reopened here. It is carried as
`tasks/T004-simulator-lab-developer-entry-point.md`, which moves the enabled
entry point to a workspace/utility boundary outside operator navigation, keeps
operator navigation identical in both flag states, and must preserve every T003
route/API boundary test unchanged.

Reviewer follow-ups 1-4 above remain open as recorded. Follow-up 1 stays an
Architect action against `.ai/FEATURE_MAP.md` and is not absorbed by T004.
