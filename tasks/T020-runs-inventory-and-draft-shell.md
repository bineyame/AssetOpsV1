# T020 - Runs Inventory And Draft Shell

Status: planned
USER_REVIEW_REQUIRED: false

Intended branch: `task/T020-runs-inventory-and-draft-shell`

## Feature

Draft SimulationRun And Causal Runtime.

## UI-Verifiable Screen Behavior

The gated Simulator Lab gains a Runs inventory and a Draft-run detail shell over
the SimulationRuns persisted by T019. A user can reopen a `READY` or `BLOCKED`
Draft, inspect its frozen identity and status, and see which execution actions
are unavailable and why. A `READY` run states, on the record and on the screen,
what that status does not assert. No runtime state is shown yet.

## Why This Is Next

T019 owns Draft creation and persistence. Before execution exists, the product
needs one truthful place to find those runs and distinguish a compatible Draft
from a blocked one. This slice establishes that presentation and route contract
without claiming that the causal kernel has run.

`READY` is the one status in this build that makes a claim about executability,
and what it checks is agreement between two declarations rather than an
executable model. Disclosing that here is cheaper than renaming a word that
becomes correct when T021's conformance test lands.

## Dependencies

- T018 executable scenario contract is accepted.
- T019 persists Draft SimulationRuns and returns their identities, narrowed so
  that run setup no longer adjudicates cause-to-observation coupling.

## Acceptance Criteria

- The Lab rail exposes Runs only while `simulator_lab.enabled=true`; direct run
  URLs use the existing unavailable behavior when the gate is off.
- Only the Simulator Lab route chokepoint names Runs and run-detail URLs.
- The inventory lists persisted Drafts from the SimulationRun domain port and
  shows record-backed run, Site, scenario-version, lifecycle, execution status,
  and interval facts. It does not infer health, progress, or evidence state.
- Selecting a row opens a run-detail shell for that `run_id`; an unknown run
  returns a stable not-found state rather than falling back to another run.
- The detail summary exposes the frozen deterministic identity established by
  T019, including initialization provenance and selected model profile, without
  exposing private scenario expectations.
- A `READY` run carries a disclosure of what the status does not assert: that
  every required executable input resolved and the selected model profile
  declares it can consume them, and that nothing has verified the model can
  execute them because no causal runtime exists. The disclosure is a property of
  the status, so it travels in the run payload a caller reads as well as
  appearing on the run-detail screen; a screen-only note does not satisfy this.
- The disclosure names the condition it exists for — that nothing verifies the
  profile's supported set against a kernel — rather than a slice number, so the
  slice that closes that condition can recognise what to retire. `BLOCKED`
  gains no equivalent claim and keeps its persisted reasons.
- A `READY` Draft presents its native Run action disabled with an accessible
  reason naming the missing causal-runtime prerequisite. A `BLOCKED` Draft
  presents no executable Run action and shows its persisted compatibility
  reasons.
- Runtime-only controls and values that have no capability yet are absent:
  clock advancement, pause/resume, step, reset, runtime overlays, observations,
  staged messages, Commit, Replay, and Open in AssetOps.
- The shell reserves no plausible numeric runtime values. Unsupported or
  not-yet-executed content is labelled as such rather than rendered as zero.
- Operator navigation and operator Site tabs remain unchanged.

## Required Product And Domain Semantics

- T019 remains the sole owner of Draft creation and persistence in this
  sequence. T020 adds inventory/detail read behavior and no second run store.
- `Draft` is lifecycle; `READY` and `BLOCKED` are execution eligibility states.
  Neither means running, completed, committed, accepted, or evidenced.
- A blocked run is inspectable history of a structurally valid frozen setup. A
  malformed setup never allocated a run and therefore cannot appear here.

## Protected Seams

- SimulationRun persistence port: inventory/detail callers consume domain
  records and errors, not files or serialization details.
- Site/scenario/run identity separation: displayed labels never replace IDs.
- Simulator gate and URL chokepoint: route/API/UI checks.
- Simulator/product boundary: the shell reads no accepted evidence or product
  analytics and adds nothing to operator navigation.
- Presentation honesty: disabled actions name real prerequisites; downstream
  actions belonging to other lifecycle objects are absent; a status discloses
  what it does not assert in the same place it makes its claim.

## Focused Tests And Review Evidence

- Domain/API tests for list, get-by-ID, stable ordering, READY/BLOCKED payloads,
  and not-found behavior through the existing SimulationRun repository.
- A test proving the `READY` disclosure is carried by the run payload and not
  only by the screen, and that `BLOCKED` carries no equivalent claim.
- Route/UI tests for gated inventory/detail navigation, gate-off absence, and
  the single URL chokepoint.
- UI tests proving READY and BLOCKED treatments, frozen-identity rendering,
  private-expectation absence, and absence of runtime/downstream claims.
- Layout evidence for the Runs table and run header at the required viewports;
  dense content owns its overflow and shell chrome remains fixed.
- Run architecture/workflow checks, relevant suites, typecheck, and build.

## Scope Limits

- No rename of `READY`. The word becomes correct when T021's conformance test
  lands, and renaming ripples through the payload, the frontend, the tests and
  the screens this slice builds.
- No `supported_states` conformance test; it needs a kernel.
- No new SimulationRun creation or persistence adapter; T019 owns them.
- No kernel execution, runtime state, device observation, golden trace,
  injection, gateway staging, Commit, ingestion, Replay, analytics, or Finding.
- No operator navigation or operator Site-tab changes.

## User Review

No additional user checkpoint. T019 reviews Draft identity and status language;
T020 applies that accepted contract without introducing new domain semantics.

The review packet must carry one named item beyond the usual evidence: a
cumulative presentation-honesty assessment of the finished screens. A Runs
inventory, a run detail, a frozen-identity panel and a disabled Run button
together can read as *almost working* when no execution capability exists at
all. The three-treatments rule is satisfied locally — the feature map names the
causal step, T021 and T022, that makes the Run action true — but local honesty
does not measure a cumulative impression. The packet states the assessment with
the screenshots that support it. If the reviewer or the user judges the whole
misleading, the remedy returns to planning rather than being chosen inside this
slice.
