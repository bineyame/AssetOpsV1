# T004 - Simulator Lab Developer Entry Point

Status: completed
USER_REVIEW_REQUIRED: true

Intended branch: `task/T004-simulator-lab-developer-entry-point`

## Feature

Stack, Shell, And Gate.

## UI-Verifiable Screen Behavior

When `simulator_lab.enabled` is true, a developer can open the empty Simulator
Lab shell from a workspace-level or utility entry point outside the operator
route navigation. Operator navigation remains unchanged in both flag states.
When the flag is false, no Simulator Lab route, workspace entry point, operator
entry point, execution action, or truth overlay is reachable.

## Why This Is Next

T003 implemented and verified the serving-boundary feature gate, but user
review compared the enabled entry point with the v6.9 product document and
identified a shell hierarchy correction: Simulator Lab is a separate developer
workspace, not an operator navigation item.

This is the smallest follow-up before Site Foundation work because later Site,
Replay, and Simulator Lab bridges should attach to the correct shell boundary.
It preserves the T003 gate while aligning the visible entry point with the
documented workspace model.

## Acceptance Criteria

- With `simulator_lab.enabled=false`, the UI exposes no Simulator Lab workspace
  entry point, operator navigation entry, route content, run action, truth
  overlay, or simulator hint.
- With `simulator_lab.enabled=true`, the operator route navigation remains the
  same as the disabled state and does not include Simulator Lab.
- With `simulator_lab.enabled=true`, a workspace-level or utility entry point
  outside operator navigation links to the Simulator Lab.
- Following the enabled workspace entry point renders the empty Simulator Lab
  shell outside the operator route layout.
- The empty Simulator Lab shell makes clear that it is a developer/simulator
  workspace surface, not an operator product page, while still exposing no run
  execution, run setup, truth overlay, gateway staging, ingestion, analytics,
  Replay, Site schema, Findings, or product conclusions.
- Direct Simulator Lab URLs and API paths remain governed by the existing T003
  route/API boundary tests in both flag states.
- Tests assert that the enabled entry point is outside the operator navigation
  landmark or operator route list, so this cannot regress into an operator
  left-nav item.

## Required Product And Domain Semantics

- Simulator Lab is a gated developer workspace surface. It may own simulator
  world, truth, execution, staging, and publication surfaces only when enabled.
- Operator routes, operator navigation, product Site history, simulated
  provenance, accepted evidence, analytics, and Replay remain separate from
  simulator execution gating.
- `Open in Simulator Lab` bridges from product screens are deferred until a
  real Site/run/provenance context exists. This task adds only the global
  developer access path needed for the empty gated shell.

## Protected Seams

- Simulator feature gate: CI guard.
  `simulator_lab.enabled=false` must mean simulator routes, workspace entry
  points, operator entry points, execution APIs, and truth overlays are not
  served while operator routes still work.
- Operator shell versus Simulator Lab workspace: UI test.
  Simulator Lab access must not appear as an operator route navigation item.
  The enabled entry point belongs to a workspace/utility boundary outside the
  operator route list.
- Simulator/product boundary: CI guard.
  Simulator Lab owns world/truth/execution/staging; AssetOps owns evidence,
  analytics, findings, and operator presentation.
- Stack and module direction: CI guard.
  The correction must preserve modular roots and avoid UI-to-simulator imports
  or simulator-to-product writes.

## Focused Tests And Checks

- UI routing/navigation test with `simulator_lab.enabled=false` for no
  workspace entry point, no operator entry point, unreachable direct Simulator
  Lab routes, and working operator routes.
- UI routing/navigation test with `simulator_lab.enabled=true` proving:
  operator navigation labels are unchanged, the workspace/utility entry point
  appears outside operator navigation, and following it opens the empty
  Simulator Lab shell.
- UI test that the enabled Simulator Lab shell still exposes no run start,
  inspect, rerun, truth comparison, staging, ingestion, analytics, Replay, or
  Findings controls.
- Backend gate tests from T003 continue to pass unchanged.
- Architecture/import check for simulator/product boundary.
- Run `tools/check-agent-workflow.ps1`.

## Scope Limits

- Do not add Site schema, Site fixtures, Site Foundation, simulator execution,
  run setup, recorded playback, gateway staging, ingestion, analytics, Replay,
  source health, configuration editing, or Findings.
- Do not add contextual `Open in Simulator Lab` product bridges yet; those need
  real Site/run/provenance context from later slices.
- Do not implement the full Simulator Lab navigation set beyond what is needed
  to establish the separate empty workspace shell. Stub labels are acceptable
  only if they are inert, clearly unavailable, and covered by tests that no
  run/truth/product behavior exists.
- Do not weaken T003's route/API boundary tests or the carried-forward
  "replace, never loosen" instruction for fabricated-value assertions.

## User Review

User review is required because this task resolves the T003 checkpoint
redirection: whether the shell hierarchy and enabled/disabled Simulator Lab
surface match the v6.9 workspace model. After this task is accepted, planning
may proceed to Site Foundation slices unless the user redirects again.

## Review Outcome

Reviewer verdict: accept. No blocking findings, no rework requested.

Unlike T001 and T003, no detailed reviewer findings were relayed into the
implementing session, so this section records the verdict and the verification
that was actually performed rather than reviewer commentary. Anything the
Reviewer raised outside that channel is not captured here.

Implementer verification carried out against the review packet
(`.agent/T004-review-packet.md`, local-only) before merge:

- `.agent/T004-review.diff` byte-identical to `git diff main` over `README.md`
  and `frontend/`, so the packet described the merged code exactly.
- All eight acceptance-criteria line citations resolved to the tests claimed.
- Checks re-run green: backend 28 passed, frontend 116 passed, typecheck clean,
  production build 44 modules, `tools/check-architecture.ps1` and
  `tools/check-agent-workflow.ps1` both passed.
- Criterion 7 proven non-vacuous by mutation. Restoring the T003 placement
  (flags back into `OperatorShellLayout`, Simulator Lab item back in the
  operator nav list) failed exactly 14 tests: four placement, four
  identical-navigation, four exclusion, one shell-opens, and the rewritten T003
  gate test. The tree was restored and re-verified byte-identical and green.

The one rewritten T003 test, `simulatorLabGate.test.tsx`
"reaches the Simulator Lab through a gated entry point outside operator
navigation", keeps the reachability half unchanged and adds absence assertions,
so it is stricter than the version it replaces. No other T003 boundary
assertion was touched, loosened, or deleted.

Carried forward, not actionable inside T004:

1. T003 follow-up 1 remains open and remains an ARCHITECT ACTION against
   `.ai/FEATURE_MAP.md`: the disabled bundle still contains
   `SimulatorLabFrame.tsx`, because the gate removes route reachability rather
   than code. This must become an explicit seam before simulator truth overlays
   land. T004 does not absorb it.
2. T003 follow-up 3 remains open: the URL guard cannot catch dynamically
   constructed simulator paths. Route and API inventory tests remain the
   stronger boundary proof.
3. Operator routes now expose two navigation landmarks. Future unnamed
   `getByRole("navigation")` queries become ambiguous, and the placement tests
   are anchored on the name "Workspace utilities"; renaming it requires
   updating them together.
4. Workspace chrome wraps only operator routes, not the Simulator Lab route or
   the not-available frame. If a later slice wants persistent workspace chrome
   inside the Lab, it collides with T003's "exactly one link in the Lab shell"
   assertion, and that needs a deliberate documented update rather than a quiet
   loosening.
5. The carried-forward "no digits inside `<main>`" assertions in
   `operatorRouteFrames.test.tsx` and `simulatorLabGate.test.tsx` are untouched.
   The standing instruction still applies to both: replace with
   evidence-specific assertions when truthful values render. Never loosen.
6. No `.ai/DECISIONS.md` entry was added. The workspace-versus-operator boundary
   is recorded in T003's User Review Outcome and in this file. Flagged in case
   the Architect wants it recorded durably.

## User Review Outcome

User review completed 2026-09-13. Verdict: accept, merge to `main`.

The user confirmed reviewer approval and instructed the merge. The shell
hierarchy question that this task existed to settle is therefore closed:
Simulator Lab is reached from workspace-level chrome outside operator
navigation, operator navigation is structurally identical in both flag states,
and the Lab renders outside the operator route layout.

This closes the T003 checkpoint redirection and completes the Stack, Shell, And
Gate feature. Planning may now proceed to Site Foundation slices.

The user did not raise the four open questions the packet posed for user review
(the utility-bar boundary, the `Open Simulator Lab` and `Workspace utilities`
labels, the developer-workspace framing text, and the plain back link). They
are settled as implemented, and remain changeable in a later slice.
