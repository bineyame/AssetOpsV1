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

**T021 is complete and merged**, and **T021A is built and in review**.
`.agent/T021-review-packet.md` and `.agent/T021A-review-packet.md`; full records
for both in `.ai/CODE_STATE.md`.

**Something executes.** A frozen READY Draft of the shipped Fuel Loss Event runs
in `assetops_simulator` and produces a private trajectory: 430 L, 374.02 L when
the dispatch window closes, 254.02 L after the removal, and 500 L at the delivery
with 54.02 L recorded refused. Exact rationals throughout, derived by hand before
the code ran. T021's two review rounds returned nine defects and the user asked
for all of them; what they settled is in `.ai/CODE_STATE.md` under T021, and the
two headlines are that **a run now freezes its whole causal projection** so the
run alone determines the experiment, and that **every number a run freezes crosses
one checked conversion** that refuses what a frozen float cannot carry.

**T021A closed one position in the authored document.** A `REPORTED_OBSERVATION`
carries no `execution_requirement` and a document declaring one is refused with
the position named; `REQUIREMENT_BEARING_ROLES` is the single list the parser and
run setup both read, so a reading is no longer a support question that can block a
Draft. A reading's ADDRESS is still resolved and can still block.
**`EXECUTION_CONTRACT_VERSION` is 7**, and it is the first move in the ledger
where no conforming kernel behaves differently: the test is narrowing DIRECTION
against documents that already exist, not executor behaviour. Two things it left
for someone: the intent that field used to carry has no home in the vocabulary
yet, and **one unparseable document in `var/scenarios/` takes the whole scenario
catalog down** - pre-existing, unowned, found by this slice. The four local user
scenarios there had the same field removed from their readings, because otherwise
they no longer parse.

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
`.ai/CODE_STATE.md` and `.agent/`.

The lessons those slices paid for are in `.ai/CODE_STATE.md` beside the slice that
paid for each. The three newest: **a derived set is only a falsifier if the
derivation has run**; **a probe says nothing unless the test it breaks passed
first**; and **a test can be satisfied by an adjacent mechanism** - one topology
guard used a `site:` address the scope filter removes before the exclusion is
consulted, so it passed with the guard deleted, and the probe written for it found
that.

Carried, not lost. Two of T021's own four carries are closed by its first correction
round, including the one that mattered; `.ai/MILESTONE_REVIEW_BACKLOG.md` keeps both
entries with what the carry rationale got wrong, because **a carry can be honest in
form and still wrong about whose slice it is.** Seven entries across the two rounds;
the two to know are that `ModelSpec` is not a general law executor and T024 must not
mistake it for one, and that a frozen record carries a `float` so a value needing a
denominator above a million is refused rather than frozen. Five inline
`float(value)` overflow sites are still open, the HTTP-reachable one first. The run
store's O(n) create wants a bounded fix with an owner before T027; `var/runs` holds
165 Drafts, some frozen at version 6 by pre-fix code.

**Next task: T022**, then T023 and T024 onward per `tasks/README.md`. None of the
resequencing touches the starter path. T021A needed no user checkpoint and asked
for none; T022 owns the generated trace, the observation values and the
reconciliation panel's retirement.

`tasks/README.md` is authoritative for the queue: what the resequencing changed,
which two positions are deliberately not load-bearing, and the four demo points.
Delivery order is A, B, C, D, H, then E, F, G, I.

Direction comes only from `Docs/simulator_design_v4.md` for simulator mechanisms
and `Docs/mini-grid-demo-architecture-and-roadmap.md` for the demo path, under
`D-2026-09-24-v4-roadmap-replan`. What that supersedes is in `.ai/START_HERE.md`.

## Read For The Active Task

1. **While T021A is `in_review` its own file is the active one**:
   `tasks/T021A-reported-observation-requirement-closure.md`, with
   `.agent/T021A-review-packet.md` and `.agent/T021A-guard-probes.py`. Once it
   moves to `tasks/completed/`, read `tasks/T022-*.md` and `tasks/README.md`.
2. `.ai/CODE_STATE.md`: the T021A entry, then the T021 entry and its two correction
   rounds, then T020B for the boundary cycle and the reading conventions, then
   T020A1 and T020A. Completed tasks are regression evidence, not direction.
3. `.ai/PLANNING_HANDOFF_T020A_T023.md`: Placement is built; Contract Versions And
   Retirements records the T021A transition as done at version 7.
4. `contracts/assetops_contracts/execution_contract.py` for what a kernel must do,
   `simulator/assetops_simulator/kernel/execute.py` for one that conforms, and
   `runs/models.py`'s four frozen projection records for what makes a run determine
   its own experiment. `scenarios/execution.py` now holds only document projections.
5. v4 sections 3, 6, 7, 8, 9 and 23, plus the decisions those name.
6. `.ai/ARCHITECTURE.md`; `.ai/WORKFLOW.md`; `.ai/ROLE_CONFIG.md`.

Site-scoped Controls land with the first controller (T024). The narrow fuel runtime
does not complete A or B: A completes at T025, B at T027, first Finding T028.

## What Is Built

T001-T020B are complete and merged: Site creation/readback, Foundation, Fuel Loss
scenario inspection, frozen Draft setup, Runs inventory/detail, typed component
properties, addressing, reachable readiness and the declared boundary contract.

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

`var/runs/` holds 165 local Drafts, added by runs of `tools/layout-evidence.mjs`
- one per run-setup visit since T019 - plus one manual POST. Some are at version 6
and were frozen by code T021's second review then corrected, so one could carry a
wrongly normalized rate. Nothing executes a local Draft and every test regenerates:
the reachable path is proved by `backend/tests/test_execution_contract_alignment.py`
and the executable path by `host/tests/`, both building the Site from the template.

`run-9f74603b06384126a627a5339fc78fbe` on `mg-006` is T020B's READY Draft. It is
at contract version 5 and the build is at 7, so it is refused execution: the
version guard is an equality test on an integer and cannot tell a Draft frozen
before a build from one frozen by it, so every executed Draft is regenerated in
process. **T021A took the build to 7, so every local Draft is now below it.**
Both cases were read back to check the policy holds: a version-5 Draft carrying
no projection and a version-6 one carrying a full projection each parse whole and
each are refused execution.

**`var/scenarios/` holds four user-authored documents** - two Fuel Loss variants
on MG-004 and MG-006 and two twin-tank documents on MG-005. T021A edited them: a
narrowing of the authored-document structure makes an existing document
unparseable, and one unparseable document there takes the whole scenario catalog
down. Only the `execution_requirement` line on each reading was removed; no value,
address, source or identity changed. A future narrowing should expect to pay the
same cost, and the catalog fragility has no owner yet.

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
