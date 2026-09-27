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

**T021 is built, reviewed once and corrected.**
`tasks/T021-minimal-fuel-loss-causal-kernel.md`, packet
`.agent/T021-review-packet.md`, review `.agent/T021-codex-review.md`, probes
`.agent/T021-guard-probes.py` and `.agent/T021-codex-probes-rerun.py`.
**Something executes.** A frozen READY Draft of the shipped Fuel Loss Event runs
in `assetops_simulator` and produces a private trajectory: 430 L, 374.02 L when
the dispatch window closes, 254.02 L after the removal, and 500 L at the delivery
with 54.02 L recorded refused. Exact rationals throughout, derived by hand before
the code ran.

The Codex review returned five defects and the user asked for all five. The one to
know: **a frozen run did not determine the experiment it executed.** A Draft froze
the values a scenario declared and left their timing in a mutable document, so the
same persisted run with one offset moved on the live document produced a different
trajectory. Run setup now freezes the whole causal projection - causes, forcings,
bound relationships and reporting-path conditions, each with its resolved address
and its span - and the executing component takes the run alone. There is no
parameter through which a different experiment can arrive.
**`EXECUTION_CONTRACT_VERSION` moved 5 to 6 for that**, and for nothing else the
slice did. The other four: adjacent windows sharing a step are no longer mistaken
for ambiguous simultaneous values; a law's operands are resolved before the first
boundary so a missing coefficient is a classified failure rather than silence; a
declared cause survives whichever frozen carrier holds its magnitude; and an
address the run records as unsupported neither acts nor invents a machine.

Five trees now, three of them Python-importable. `contracts/assetops_contracts`
holds what both sides of the truth barrier agree about, including the versioned
execution semantics moved out of `scenarios/execution.py`;
`simulator/assetops_simulator` the kernel and the fuel pack; `host/` the
composition leaf that nothing imports, and the only place a test may compose both
sides. Setup needs three editable installs - see `README.md`.

Three mechanisms make it conform rather than resemble, and each is the alternative
to a claim nobody checks. The boundary cycle's order is read from
`BOUNDARY_CYCLE.sequence`, so a phase added to the contract stops the kernel until
it is implemented. The `window-overlap` predicate and the `window-ramp` share are
executable functions in the module that publishes the sentences describing them,
and the kernel calls them. And a model's advertised supported set is DERIVED by
grouping its table of executable handlers, with every advertised pair required to
have been reached by a real execution.

**`supported_states` has a falsifier**, which closes the backlog's oldest entry,
and half the readiness disclosure retired with it. The publication profile's
reporting-path half stays: nothing here can suppress a reading or deliver one, and
the observation transform is its condition.

Two authored readings in the shipped document were corrected from 155 L and 150 L
to the computed 254.02 L, and `refuelling-is-not-a-loss` was corrected because the
trajectory made it inconsistent - the delivery overfills the tank, so 54.02 L never
arrive. The computed trajectory is recorded as a private `TRAJECTORY` expectation.
The reconciliation reference implementation has lost its authority and stays until
its last product-path caller goes, which is T022's.

**T020B, T020A1 and T020A before it are complete and merged**; full records in
`.ai/CODE_STATE.md`, packets and reviews in `.agent/`. What they settled - the
addressed world state, typed Foundation properties, and exactly one profile
answering for each state - is in those entries and is not restated here.

Six lessons those slices paid for are in `.ai/CODE_STATE.md` beside the slice that
paid for each. The two newest: **a derived set is only a falsifier if the
derivation has run**, and **a probe says nothing unless the test it breaks passed
first** - two of fourteen reported CAUGHT against an already-red suite, because a
fixture pinned a contract version it did not own.

Carried, not lost. Two of T021's own four carries are now closed by its correction
round, including the one that mattered; `.ai/MILESTONE_REVIEW_BACKLOG.md` keeps
both entries with what the carry rationale got wrong, because **a carry can be
honest in form and still wrong about whose slice it is.** Four entries out of the
correction round, of which the one to know is that `ModelSpec` is not a general law
executor and T024 must not mistake it for one. Five inline `float(value)` overflow
sites are still open, the HTTP-reachable one first. The run store's O(n) create
wants a bounded fix with an owner before T027; `var/runs` now holds 159 Drafts.

**Next task: T021A**, then T022, T023 and T024 onward per `tasks/README.md`. None
of the resequencing touches the starter path. T021A is a narrow parser closure to
be time-boxed and is not a checkpoint.

What the resequencing changed from position 10 onward, the two positions that are
deliberately not load-bearing (T026A unscheduled, T033 and T035 interchangeable)
and the four demo points are all in `tasks/README.md`, which is authoritative for
the queue. They were restated here and the restatement is what the line cap is
for. Delivery order is A, B, C, D, H, then E, F, G, I; feature-map letters are
outcomes, not order.

Direction comes only from:
- `Docs/simulator_design_v4.md` for simulator mechanisms;
- `Docs/mini-grid-demo-architecture-and-roadmap.md` for demo path and order.

The old two-roadmap precedence, fuel-first Finding and late electrical-world/
StateRef plan are superseded by `D-2026-09-24-v4-roadmap-replan`.
Earlier feature-map revamps, alignment reviews and v3 assessments do not direct
this work. Do not reconcile the new plan back to them.

## Read For The Active Task

1. **While T021 is `in_review` its own file is the active one**:
   `tasks/T021-minimal-fuel-loss-causal-kernel.md`, with
   `.agent/T021-review-packet.md`. Once it moves to `tasks/completed/`, read
   `tasks/T021A-*.md` and `tasks/README.md` instead.
2. `.ai/CODE_STATE.md`: the T021 entry first - it names the three trees, the three
   conformance mechanisms, where a bound's number comes from and what the slice
   leaves open - then T020B for the boundary cycle and the reading conventions,
   then T020A1 and T020A for the carriers and frozen setup. Completed tasks are
   regression and history evidence, not future direction.
3. `.ai/PLANNING_HANDOFF_T020A_T023.md`: Placement is now built; Contract Versions
   And Retirements carries the outstanding T021A transition.
4. `contracts/assetops_contracts/execution_contract.py` in full for what a kernel
   must do, and `simulator/assetops_simulator/kernel/execute.py` for what one that
   conforms looks like. `backend/assetops_backend/scenarios/execution.py` now holds
   only the projections of a document. `runs/models.py`'s four frozen projection
   records are what makes a run determine its own experiment.
5. v4 sections 3, 6, 7, 8, 9 and 23, plus the decisions those name.
6. `.ai/ARCHITECTURE.md`; `.ai/WORKFLOW.md` for seams, sizing and review shape.
7. `.ai/ROLE_CONFIG.md` for role bindings.

Site-scoped Controls land with the first controller (T024), not with T020A's
carrier. The narrow fuel runtime does not complete A or B: A completes at T025,
B at T027 and the first Finding is T028.

## What Is Built

T001-T020B are complete and merged: Site creation/readback, Foundation
topology/devices/mappings/SLD, Fuel Loss scenario inspection, frozen Draft setup,
Runs inventory/detail, typed component properties, addressing, reachable readiness
and the declared boundary contract.

**After T021 a Draft executes, privately.** There is a kernel, a clock, a boundary
cycle, a private trajectory and a trajectory identity. There is still no generated
observation, no gateway, no staging, no ingestion, no accepted history, no
analytics and no Findings, and **no visible execution**: T022 wires the Lab
controls, and no product surface starts, steps or shows a run.

The shipped scenario lives in `config/scenarios/fuel-loss-event.yaml`.
Shipped and writable stores have disjoint identities; the scenario store ships
nonempty because there is no authoring UI.

## Local Data To Preserve

The working checkout's gitignored `var/sites/` holds mg-001, mg-002 (cold room),
mg-003 (two AC buses), mg-004, mg-005 (twin tank) and mg-006, which the user asked
to preserve. Do not clear, replace or delete that directory. Updated templates do
not mutate existing Sites: use a new explicit fixture for new property or schema
demonstrations and leave existing fixtures intact. An isolated checkout does not
contain them.

**T021 added no Site and no scenario document to `var/`.** Every fixture it needs
- including the twin-tank second Site whose 800 L tank proves the capacity bound
comes from the frozen Foundation answer - is built in process for the length of one
test, and its second scenario document lives in `host/tests/second_site.py` rather
than in the writable store, because a document that exists to prove a kernel
property would appear on the scenario catalog screen.

`var/runs/` holds 159 local Drafts. Sixteen were added across this slice by runs
of `tools/layout-evidence.mjs`, one per run-setup visit, which is what that tool
has done since T019, plus one manual POST against the live backend; nothing clears
them. A local Draft is not shipped proof of
anything: the reachable path is proved by
`backend/tests/test_execution_contract_alignment.py` and the executable path by
`host/tests/`, both of which build the Site from the shipped template.

`run-9f74603b06384126a627a5339fc78fbe` on `mg-006` is T020B's READY Draft. It is
at contract version 5, the build is at 6, and T021 did not execute it: the version
guard is an equality test on an integer and cannot tell a Draft frozen before a
build from one frozen by it, so every executed Draft is regenerated in process.
Every Draft below 6 now carries no causal projection at all and is refused
execution, which is what makes an empty projection safe to read back.

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
