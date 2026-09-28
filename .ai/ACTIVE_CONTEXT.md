# Active Context

Routing only; hard cap 200 lines. Built history is in `.ai/CODE_STATE.md`,
durable rules in `.ai/ARCHITECTURE.md` and `.ai/DECISIONS.md`.

## Current Milestone

Credible mini-grid runtime (feature-map A), then internal architecture demo (B),
a dispatch Finding for domain-expert feedback (C), its economic translation (D)
and the verified intervention (H). E, F, G and I follow.

## Active Work

The Planner recreated the queue, the Architect reviewed it on 2026-09-24, and
the user's own review then resequenced it under
`D-2026-09-24-queue-resequenced-for-demo`. `tasks/README.md` is authoritative.

**T021 and T021A are complete and merged.** **T022 is built, reviewed once and
back in review**; packet in `.agent/T022-review-packet.md`, the review in
`.agent/T022-codex-review.md`, record in `.ai/CODE_STATE.md`. It returned three
defects, all fixed: the draw's identity was not v4 section 9.2's, a 30-minute
timestep answered HTTP 500 on Start, and a POINT reporting condition became a
run-long outage.

**Something runs, and somebody can watch it.** The Lab starts a frozen Draft,
steps it, and runs it to the end, and the Draft's own screen shows the world at
the instant it has reached beside what each device reported. The row the slice
exists for is offset 1545, inside the shipped gap `[1490, 1580)` and past the
removal `[1500, 1545)`: the tank holds **254.02 L**, the newest reading is the
**373.52 L** published before the gap opened, carrying its own source time.
The columns differ by 119.50 L; the removal is 120 L, that difference with the
sensor's -0.5 L bias taken back out.

**`EXECUTION_CONTRACT_VERSION` is 8 and the publication profile is version 2**,
and the two are one move. `REPORTING_RULES` answers what a version-seven
implementation could have answered any way it liked - when a sample is due, what
a forced gap does to one, how long an outage of each declared shape lasts, what a
consumer sees when nothing fresh arrived, and whether a publication failure is
drawn or chosen - and the profile now declares which signal reports which state,
at what cadence, with what bias and with what dropout. Eight was amended in place
after its review and the ledger says so. **Every stored Draft is below 8 and
refused execution**: T023 creates a fresh one, as T022 did.

Four mechanisms carry it and `.ai/CODE_STATE.md` records each in full: the
resumable execution **handle**, the **separate observation transform** kept so by
two records neither of which has a field for the other's content, the
**`DeviceObservation` that carries no true value**, and the **draw under
`assetops-sim-rng-v1`** on v4 section 9.2's identity.

**Only the leaf can implement the execution port.** `assetops_backend.main:app`
answers `EXECUTION_PORT_NOT_COMPOSED`; **`host/lab_app.py` is the entry point for
a build that executes**. Private artifacts live under `var/executions`.

**T022 completed the reconciliation retirement**
(`D-2026-09-22-reconciliation-panel-retirement`): the reference implementation,
its vocabulary, `declared_bounds` and `IMPLICIT_LOWER_BOUND_DIMENSIONS` went with
the panel that was their last caller. The frozen run's own `declared_bounds` is a
different thing with the same name, untouched.

One thing it left that a later reader meets first: **the MG-001 in `var/sites`
predates the two Foundation properties the model profile binds to**, so the
shipped document blocks against it and the browser evidence executes the user's
own `fuel-loss-event-mg006` instead. That and five others are in
`.ai/MILESTONE_REVIEW_BACKLOG.md`. Five trees, three Python-importable;
`contracts/` now also holds what a device reports and the gated projection,
`simulator/` the observation transform, and `host/` the application that
executes. Three editable installs - see `README.md`.

**T020B, T020A1 and T020A before them are complete and merged**; full records in
`.ai/CODE_STATE.md` and `.agent/`.
The lessons those slices paid for are in `.ai/CODE_STATE.md` beside the slice
that paid for each. T022 adds one with four instances: **a check written from the
code rather than from the contract, or from the surface a user meets, does not
fail when the code is wrong.** A test recomputing the implementation's own hash
payload; a test one layer below the HTTP composition; tests covering only the
shape the shipped document declares; a suite whose fixtures are all at the
current version.

Carried, not lost. `.ai/MILESTONE_REVIEW_BACKLOG.md` is the list and T022 adds
six. Five inline `float(value)` overflow sites are still open, the run store's
O(n) create wants a bounded fix before T027, and `var/runs` now grows by FOUR per
layout-evidence run rather than three.

**Next task: T023**, then T024 onward per `tasks/README.md`. None of the
resequencing touches the starter path. **T022 requires a user checkpoint**
(`USER_REVIEW_REQUIRED: true`): the owner steps a real run and distinguishes
truth, reporting gap and measured value.

`tasks/README.md` is authoritative for the queue: what the resequencing changed,
which two positions are deliberately not load-bearing, and the four demo points.
Delivery order is A, B, C, D, H, then E, F, G, I.

Direction comes only from `Docs/simulator_design_v4.md` for simulator mechanisms
and `Docs/mini-grid-demo-architecture-and-roadmap.md` for the demo path, under
`D-2026-09-24-v4-roadmap-replan`. What that supersedes is in `.ai/START_HERE.md`.

## Read For The Active Task

1. **While T022 is `in_review` its own file is the active one**:
   `tasks/T022-lab-execution-and-device-observation.md`, with
   `.agent/T022-review-packet.md`, `.agent/T022-codex-review.md` and the two probe
   suites. Once it moves to `tasks/completed/`, read `tasks/T023-*.md`.
2. `.ai/CODE_STATE.md`: the T022 entry, then T021A, T021 and T020B. Completed
   tasks are regression evidence, not direction.
3. `.ai/PLANNING_HANDOFF_T020A_T023.md`: Contract Versions And Retirements, which
   records T021A at version 7 and T022 at 8.
4. `contracts/assetops_contracts/`: `execution_contract.py` for what a conforming
   implementation must do including `REPORTING_RULES`, `observation.py` for what a
   device reports and the draw contract, `lab_projection.py` for the gated record
   and the control refusals. Then
   `simulator/assetops_simulator/observation/transform.py` and
   `host/lab_execution.py`.
5. v4 sections 3, 6, 7, 8, 9, 11.1, 21, 23 and 25, plus the decisions those name.
6. `.ai/ARCHITECTURE.md`; `.ai/WORKFLOW.md`; `.ai/ROLE_CONFIG.md`.

Site-scoped Controls land with the first controller (T024). The narrow fuel runtime
does not complete A or B: A completes at T025, B at T027, first Finding T028.

## What Is Built

T001-T020B are complete and merged: Site creation/readback, Foundation, Fuel Loss
scenario inspection, frozen Draft setup, Runs inventory/detail, typed component
properties, addressing, reachable readiness and the declared boundary contract.

**After T022 a Draft executes where somebody can watch it.** There is a kernel, a
clock, a boundary cycle, a private trajectory, a trajectory identity, a resumable
handle, a separate observation transform, a reading series with its own identity,
a private artifact per run, and a gated screen that starts, steps and finishes a
run and shows truth beside what was reported. There is still **no gateway, no
envelope, no staging, no ingestion, no accepted history, no analytics and no
Findings**, no Commit, no reset and no event injection, and nothing an execution
produces has reached an operator surface.

The shipped scenario lives in `config/scenarios/fuel-loss-event.yaml`.
Shipped and writable stores have disjoint identities; the scenario store ships
nonempty because there is no authoring UI.

## Local Data To Preserve

The working checkout's gitignored `var/sites/` holds mg-001, mg-002 (cold room),
mg-003 (two AC buses), mg-004, mg-005 (twin tank) and mg-006, which the user asked
to preserve. Do not clear, replace or delete that directory. Updated templates do
not mutate existing Sites: use a new explicit fixture for new property or schema
demonstrations. An isolated checkout does not contain them.

**T021 and T022 added no Site and no scenario document to `var/`.** Every fixture
either needs is built in process for the length of one test, and a second scenario
document lives in `host/tests/second_site.py` rather than in the writable store,
because a document that exists to prove a kernel property would appear on the
scenario catalog screen.

`var/runs/` held 165 local Drafts before T022 and grows by **four** per run of
`tools/layout-evidence.mjs` since it: three BLOCKED MG-001 Drafts from the
run-setup measurement at three widths, plus the READY MG-006 Draft the execution
measurements need. Nothing executes a stored Draft and every test regenerates: the
reachable path is proved by `backend/tests/test_execution_contract_alignment.py`
and the executable path by `host/tests/`, both building the Site from the
template.

**`var/executions/` is new in T022**: gitignored user data, one private artifact
per executed run, written by `host/lab_execution.py` and by nothing else. It is
the leaf's rather than the product's, because a product store of private truth
would put a filing cabinet inside the truth barrier. Safe to delete; a run whose
artifact is gone reads as never executed.

The version guard is an equality test on an integer and cannot tell a Draft frozen
before a build from one frozen by it, so every executed Draft is regenerated in
process. **T022 took the build to 8, so every Draft written before it is below
it** - as was already true at 7. A Draft below the current version stays readable,
renders whole, and is refused execution with the contract version named. T022
corrected the ORDER of two refusals here: such a run also names an earlier
publication profile, and it was reporting the narrower fact.

**The shipped document cannot reach READY against the MG-001 in `var/sites`**,
which predates the two Foundation properties the model profile binds to, so every
Draft of `fuel-loss-event` against it is BLOCKED - truthfully. Do not "fix" MG-001
by editing it; a new Site from the current template is the move if a demo needs
one.

**`var/scenarios/` holds four user-authored documents** - two Fuel Loss variants
on MG-004 and MG-006 and two twin-tank documents on MG-005. T021A edited them
because a narrowing made them unparseable, and **one unparseable document there
takes the whole scenario catalog down**. A future narrowing should expect to pay
the same cost; the catalog fragility has no owner yet. T022 edited none of them,
and `fuel-loss-event-mg006` is now what the browser evidence executes.

## Standing Direction And Checks

`D-2026-09-22-milestone-speed-over-purity` binds every slice and review.
Stop for expensive-to-reverse defects, misleading claims or user-only decisions.
Carry cheap refinements in `.ai/MILESTONE_REVIEW_BACKLOG.md`; do not turn each
v4 concept into an independent task.

Run `tools/check-agent-workflow.ps1`, `tools/check-architecture.ps1` and checks
appropriate to the changed behavior, plus the backend, frontend, simulator and
host suites. Layout-sensitive implementation requires the workflow's browser
evidence. `node tools/layout-evidence.mjs` takes the Site to measure as its second
argument, or `ASSETOPS_LAYOUT_SITE`: a Foundation section a site declares nothing
for renders as a stated absence and not as a table, so measuring containment
against such a site measures an empty set.
