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

**T021 through T022A are complete and merged.** Their packets, reviews and the
record in `.ai/CODE_STATE.md` carry the detail; three artifact layouts exist and
each reads back as the result it is. A single-run read reads one document: 216
parses become 1, and the run detail, the execution read and a Lab step each drop
about two orders of magnitude. **Quote that ratio, not the seconds** - the same
measurement varied 3x across three readers; `CODE_STATE` says why. **The
inventory is measured, deliberately unfixed and not acceptable**: 99% is the
pure-Python YAML scanner and it passes one second between about 20 and 65
records. The bounded fix trades a parser, so it is the owner's.

**T023 is complete and merged**: an executed Draft stages canonical source
envelopes (envelope schema 1, stage schema 2, under
`D-2026-09-29-source-envelope-schema-v1`) with a published-through watermark
whose `STAGING_INCOMPLETE` blocker keeps an incomplete stage ineligible,
inspected on the Draft's own screen. Accepted on independent review (two Codex
passes, one Claude verification) and on owner review 2026-09-29. The owner's
review of T022 and T022A is also recorded, 2026-09-29. The libyaml
decision above is **made**: `D-2026-09-29-run-store-libyaml` adopts
`CSafeLoader` for the run store in its own slice **T022B, before T024**.

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
drawn or chosen - and the profile declares which signal reports which state, at
what cadence, bias and dropout. Eight was amended in place after its review.
**Every stored Draft is below 8 and refused execution**: T023 creates a fresh
one, as T022 did. Its four mechanisms are recorded in `.ai/CODE_STATE.md`.

**Only the leaf can implement the execution port.** `assetops_backend.main:app`
answers `EXECUTION_PORT_NOT_COMPOSED`; **`host/lab_app.py` executes**. Private
artifacts live under `var/executions`.

**T022 completed the reconciliation retirement**
(`D-2026-09-22-reconciliation-panel-retirement`): the reference implementation,
its vocabulary, `declared_bounds` and `IMPLICIT_LOWER_BOUND_DIMENSIONS` went with
the panel that was their last caller. The frozen run's own `declared_bounds` is a
different thing with the same name, untouched. One thing it left that a later
reader meets first: **the MG-001 in `var/sites` predates the two Foundation
properties the model profile binds to**, so the shipped document blocks against
it and the browser evidence executes the user's own `fuel-loss-event-mg006`
instead. Five trees, three Python-importable;
`contracts/` now also holds what a device reports and the gated projection,
`simulator/` the observation transform, and `host/` the application that
executes. Three editable installs - see `README.md`.

**T020B, T020A1 and T020A before them are complete and merged**; records in
`.ai/CODE_STATE.md`. T022 adds one lesson with four instances: **a check written from the
code rather than from the contract, or from the surface a user meets, does not
fail when the code is wrong.** T022A adds the measuring half: a benchmark on a
ten-record fixture cannot see a cost that only appears at two hundred.

Carried, not lost. `.ai/MILESTONE_REVIEW_BACKLOG.md` is the list; T022 adds six
and T022A seven. Five `float(value)` overflow sites are open, the inventory AND
`create_run` still cost the whole store, `var/runs` grows by FOUR per
layout-evidence run. T022A had to WRITE the run-store entry three documents
already cited: a residual living only in a packet is one nobody reads first.

**T022B is next** (being planned), then T024 per `tasks/README.md`.

`tasks/README.md` is authoritative for the queue: what the resequencing changed,
which two positions are deliberately not load-bearing, and the four demo points.
Delivery order is A, B, C, D, H, then E, F, G, I.

Direction comes only from `Docs/simulator_design_v4.md` for simulator mechanisms
and `Docs/mini-grid-demo-architecture-and-roadmap.md` for the demo path, under
`D-2026-09-24-v4-roadmap-replan`. What that supersedes is in `.ai/START_HERE.md`.

## Read For The Active Task

1. **T022B** once planned, then `tasks/T024-daytime-mini-grid-runtime.md`; T023, T022 and
   T022A in `tasks/completed/` as regression evidence.
2. `.ai/CODE_STATE.md`: the T023 entry, then T022, T021A, T021 and T020B.
   Completed tasks are regression evidence, not direction.
3. `.ai/PLANNING_HANDOFF_T020A_T023.md`: Contract Versions And Retirements, which
   records T021A at version 7 and T022 at 8.
4. `contracts/assetops_contracts/`: `execution_contract.py` for what a conforming
   implementation must do including `REPORTING_RULES`, `observation.py` for what a
   device reports and the draw contract, `lab_projection.py` for the gated record
   and the control refusals, `source_envelope.py` and `source_stage.py` for
   the crossing and the stage. Then `simulator/assetops_simulator/gateway/`,
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
run and shows truth beside what was reported. **T023 adds the
gateway, the canonical envelope and an immutable stage** with a gated inspector.
There is still **no Commit, no ingestion, no accepted history, no analytics and
no Findings**, and nothing an execution produces reaches an operator surface.

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
artifact is gone reads as never executed. `var/stages/` (T023) is the same kind
of data: one staged-envelope stage per executed run, safe to delete.

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
