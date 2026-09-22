# T020 - Runs Inventory And Draft Shell

Status: complete
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

The run setup form also stops arriving empty. It offers defaults for the fields
it can honestly default, each one visibly marked as a default and each one still
selectable, so a person can see what the form chose for them and change it.

## Why This Is Next

T019 owns Draft creation and persistence. Before execution exists, the product
needs one truthful place to find those runs and distinguish a compatible Draft
from a blocked one, without claiming the causal kernel has run.

`READY` is the one status in this build that makes a claim about executability,
and what it checks is agreement between two declarations rather than an
executable model. Disclosing that here is cheaper than renaming a word that
becomes correct when T021's conformance test lands.

The form defaults land here rather than reopening T019, with a constraint. M4
found the browser auto-selecting two components of the frozen deterministic
identity while the screen said nothing was prefilled, and the fix left the form
empty. A shown default a person can override is honest, an invisible pre-pick
is the defect M4 removed, and that difference is this half of the slice.

## Dependencies

- T018 executable scenario contract is accepted.
- T019 persists Draft SimulationRuns, narrowed so that run setup no longer
  adjudicates cause-to-observation coupling.

## Acceptance Criteria

- The Lab rail exposes Runs only while `simulator_lab.enabled=true`; direct run
  URLs use the existing unavailable behavior when the gate is off.
- Only the Simulator Lab route chokepoint names Runs and run-detail URLs.
- The inventory lists persisted Drafts from the SimulationRun domain port with
  record-backed run, Site, scenario-version, lifecycle, execution status and
  interval facts. It does not infer health, progress, or evidence state.
- Selecting a row opens a run-detail shell for that `run_id`; an unknown run
  returns a stable not-found state rather than falling back to another run.
- The detail summary exposes the frozen deterministic identity established by
  T019, including initialization provenance and selected model profile, without
  exposing private scenario expectations.
- Every frozen row names the profile that actually answered it: every row whose
  value came from the publication profile now says so. That is a shape, not a
  count of three - both cadence branches that resolve a cadence carry the
  mislabel, and a run with two device-signal sources has two cadence rows. The
  slice adds `PUBLICATION_PROFILE` to `FROZEN_INPUT_ANSWERERS` and corrects
  with it the docstring saying there are four and
  `test_every_row_names_one_of_the_four_answerers`. No guard stops that: the
  correspondence assertion's second half is a subset, so a fifth member passes
  it silently. T020 puts this table on a permanent linkable screen, so the
  label is corrected before it has been read.
- `cadence_resolution` is deleted from the frozen observation binding rather
  than renamed. It is a total function of `source_kind` and `cadence_minutes` -
  a cadence present means a profile declared one, absent on an operator record
  means no rate to own, absent on a device signal means nobody declared one -
  so the parser's biconditional spends fourteen lines checking a record against
  a restatement of itself, and `provenance.py` branches on the two fields
  instead. A stored run document accepts unknown keys, so the 34 existing
  Drafts stay readable with the key ignored and nothing is cleared. This is a
  run-record shape change, not a scenario-document one, so
  `EXECUTION_CONTRACT_VERSION` does not move
  (`D-2026-09-22-contract-version-scope`). The rule it restores is in
  `.ai/ARCHITECTURE.md`: store what was contingent, compute what follows from
  structure.
- A `READY` run carries a disclosure of what the status does not assert: that
  every required executable input resolved and the selected model profile
  declares it can consume them, and that nothing has verified the model can
  execute them because no causal runtime exists. It is a property of the
  status, so it travels in the run payload a caller reads as well as on the
  screen; a screen-only note does not satisfy this. It names the condition it
  exists for — that nothing verifies the profile's supported set against a
  kernel — rather than a slice number, so the slice closing that condition can
  recognise what to retire. `BLOCKED` gains no equivalent claim.
- A `READY` Draft presents its native Run action disabled with an accessible
  reason naming the missing causal-runtime prerequisite. A `BLOCKED` Draft
  presents no executable Run action and shows its persisted reasons.
- Runtime-only controls and values that have no capability yet are absent:
  clock advancement, pause/resume, step, reset, runtime overlays, observations,
  staged messages, Commit, Replay, and Open in AssetOps.
- The shell reserves no plausible numeric runtime values. Unsupported or
  not-yet-executed content is labelled as such rather than rendered as zero.
- The run setup form arrives with a default in every field it can honestly
  default: the interval, the timestep, the seed, and a profile selection with
  exactly one available option, which both profiles are in this build. A
  defaulted field shows, in the field rather than only in surrounding help
  text, that the value is a default and what it is, and stays selectable. A
  value the form chose that a person cannot tell it chose does not satisfy
  this, whatever the value is.
- A value the scenario declares the run owns is never defaulted: it is an
  initial world value, and a form supplying one is the fabricated default T019
  refuses setup over. The shipped scenario declares none.
- Any other field arrives empty rather than prefilled with a plausible-looking
  value, and the request is refused or blocked on it as it is today rather
  than proceeding on a guess.
- Operator navigation and operator Site tabs remain unchanged.

## Required Product And Domain Semantics

- `Draft` is lifecycle; `READY` and `BLOCKED` are execution eligibility states.
  Neither means running, completed, committed, accepted, or evidenced.
- A blocked run is inspectable history of a structurally valid frozen setup; a
  malformed setup never allocated a run and cannot appear here.
- A default the person accepted is a run input, the same as a typed one, and
  not a new kind of answerer: the frozen-inputs summary keeps answering who
  owns a value rather than how the form came to hold it. The honesty
  obligation is discharged at the form, where the person can still act on it.

## Protected Seams

- SimulationRun persistence port: inventory/detail callers consume domain
  records and errors, not files or serialization details.
- Site/scenario/run identity separation: displayed labels never replace IDs.
- Simulator gate and URL chokepoint: route/API/UI checks.
- Simulator/product boundary: the shell reads no accepted evidence or product
  analytics and adds nothing to operator navigation.
- Presentation honesty: disabled actions name real prerequisites, downstream
  actions belonging to other lifecycle objects are absent, a status discloses
  what it does not assert where it makes its claim, a frozen row names the
  answerer that answered it, and a value the form supplied is visible as one
  before it joins a frozen identity.

## Focused Tests And Review Evidence

- Domain/API tests for list, get-by-ID, stable ordering, READY/BLOCKED payloads,
  and not-found behavior through the existing SimulationRun repository.
- A test proving the `READY` disclosure is carried by the run payload and not
  only by the screen, and that `BLOCKED` carries no equivalent claim.
- No `READY` run is reachable through the product path in this build: the
  shipped scenario blocks and the layout tool creates blocked Drafts. Every
  `READY` claim here — disclosure, disabled Run action, UI treatment, layout
  evidence — is proved against a fixture run record written through the
  SimulationRun port, as T019 proved `READY`, and the packet says which runs
  in `var/runs/` are fixtures.
- A test proving no row's answerer disagrees with the detail beside it, which
  is the shape rather than a list of the rows that carry the mislabel today,
  and one covering a run with two device-signal sources.
- Form tests proving each defaulted field is marked as defaulted, shows the
  chosen value, and can be changed; that a field with no honest default is
  empty; and the M4 regression on the two profile selections, that no field
  carries a value the screen does not disclose.
- Route/UI tests for gated inventory/detail navigation, gate-off absence, and
  the single URL chokepoint.
- UI tests proving READY and BLOCKED treatments, frozen-identity rendering,
  private-expectation absence, and absence of runtime/downstream claims.
- Layout evidence for the Runs table and run header at the required viewports:
  dense content owns its overflow, shell chrome stays fixed.
- Run architecture/workflow checks, relevant suites, typecheck, and build.

## Scope Limits

- No rename of `READY`. The word becomes correct when T021's conformance test
  lands, and renaming ripples through the payload, the frontend and the tests.
- No `supported_states` conformance test; it needs a kernel. No widening of the
  shipped model profile to make a `READY` run reachable, which is the cheapest
  wrong way to satisfy the criteria above and is T019's prohibition standing.
- No move of reporting-path authority. This slice corrects a label on a value
  the publication profile already supplies. Moving authority over
  `fuel-level-reporting-availability` to that profile is T020B's, and it
  changes behaviour rather than a label.
- No new SimulationRun creation or persistence adapter; T019 owns them, and
  defaults change only what the form offers, not what run setup does with the
  request.
- No Rerun, which allocates a new Draft identity and remains a later
  capability.
- No kernel execution, runtime state, device observation, golden trace,
  injection, gateway staging, Commit, ingestion, Replay, analytics, or Finding.

## User Review

No additional user checkpoint. T019 reviewed Draft identity and status
language, and the defaults constraint is the one the user set at that review:
visible, labelled, still selectable. T020 implements it and adds no question
the user has not already answered.

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

## Review Outcome

Independent review, one blocking finding and six carried to
`.ai/MILESTONE_REVIEW_BACKLOG.md` under
`D-2026-09-22-milestone-speed-over-purity`.

The finding took three rounds, and the shape is the transferable part. Each
guard was written over the property of the violation known at the time - first
a word, then an element type, then a URL - and each next probe varied the
property nobody had closed. An anchor saying "Execute this run now" passed a
ban written over what a control says. A button saying "Proceed" then passed a
closed set of links. What ended it was not a better predicate but coverage:
the blocked branch became a screen every existing claim visits, and the
blocked test counts controls rather than naming one.

Both the Implementer and the Reviewer verified an intermediate fix with the
probe matching their own model of the defect, and both were wrong in the same
way. The coordinator ran the button probe against the tree and found 112 tests
green where the report said the hole was closed. A guard over element type is
only tested by a probe that varies element type.

Checks at acceptance: backend 831 passed, frontend 770 across 24 files,
typecheck clean, production build clean, both `.ps1` checks, and layout
evidence `ALL CLAIMS HOLD`, 204 PASS / 0 FAIL from a fresh build with ports
verified free. The final probe fails two claims by name and the tree is
byte-identical after revert.

Not a user checkpoint: `USER_REVIEW_REQUIRED: false`. The presentation-honesty
assessment the task names as a packet item was made against four screenshots
and independently agreed by the Reviewer, which reads the whole as not
almost-working, with the inventory's bare `READY` cell as its thinnest point
and carried as B2.
