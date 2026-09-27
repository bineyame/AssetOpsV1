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

**T021 is built and in review.** `tasks/T021-minimal-fuel-loss-causal-kernel.md`,
packet `.agent/T021-review-packet.md`, probes `.agent/T021-guard-probes.py`.
**Something executes.** A frozen READY Draft of the shipped Fuel Loss Event runs
in `assetops_simulator` and produces a private trajectory: 430 L, 374.02 L when
the dispatch window closes, 254.02 L after the removal, and 500 L at the delivery
with 54.02 L recorded refused. Exact rationals throughout, derived by hand before
the code ran.

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
the observation transform is its condition. `EXECUTION_CONTRACT_VERSION` did NOT
move and stays 5; the code-state entry says why for each change that might have.

Two authored readings in the shipped document were corrected from 155 L and 150 L
to the computed 254.02 L, and `refuelling-is-not-a-loss` was corrected because the
trajectory made it inconsistent - the delivery overfills the tank, so 54.02 L never
arrive. The computed trajectory is recorded as a private `TRAJECTORY` expectation.
The reconciliation reference implementation has lost its authority and stays until
its last product-path caller goes, which is T022's.

**T020B, T020A1 and T020A before it are complete and merged**; full records in
`.ai/CODE_STATE.md`, packets and reviews in `.agent/`. The shipped Fuel Loss Event
reaches `READY` through the form and API path. A world state is named by an ADDRESS
- a semantic key plus the component it is claimed on, or `site:` for a fact about
the installation - carried by one `StateRef`; a Foundation declares typed
unit-carrying properties that run setup resolves through the profile's binding;
exactly one profile answers for each state, decided by the state.

Five lessons those four slices paid for, worth more than their fixes. **Who
supplies a number and which asset it is about are two questions.** **Visiting a
reference is not resolving it.** **A check that answers a different question is
not an answer.** **Two checks that cannot see each other will disagree.** And
T021's: **a derived set is only a falsifier if the derivation has run** - two
tables kept in step by hand would have satisfied the same sentence.

Carried, not lost: `.ai/MILESTONE_REVIEW_BACKLOG.md` has four new entries out of
T021, of which the one to know is that a definition edited IN PLACE at an unchanged
scenario version can still move an entry's offset undetected. Five inline
`float(value)` overflow sites are still open, the HTTP-reachable one first. The run
store's O(n) create wants a bounded fix with an owner before T027; `var/runs` now
holds 149 Drafts.

**Next task: T021A**, then T022, T023 and T024 onward per `tasks/README.md`. None
of the resequencing touches the starter path. T021A is a narrow parser closure to
be time-boxed and is not a checkpoint.

What the resequencing changed, from position 10 onward: T026 is thinned to
dispatch-essential evidence and the gateway-failure work moved to T026A; a new
T029A extracts the minimal immutable policy-intervention mechanism so T034
verification runs right after T029 instead of behind T030-T033; T033 no longer
gates verification and adds battery stress to T034's guardrail rule set
afterwards. Delivery order is now A, B, C, D, H, then E, F, G, I. Feature-map
letters are outcomes, not order.

Two ordering facts the queue states deliberately. T026A is unscheduled and a
prerequisite of nothing, including T036; run it whenever feedback and time
justify it. T033 and T035 are an interchangeable pair, because neither consumes
the other's artifacts and the choice is a product-priority call from T028/T029
feedback. Every other position in `tasks/README.md` is load-bearing.

There are four demo points, not one: T027 internal architecture, T028/T029
domain-expert and early prospect, T034 strong product, T036 full portfolio.
Seek expert feedback at T028/T029 and reassess T030-T036 from what is said.

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
   only the projections of a document.
5. v4 sections 3, 6, 7, 8, 9 and 23, plus the decisions those name.
6. `.ai/ARCHITECTURE.md`; `.ai/WORKFLOW.md` for seams, sizing and review shape.
7. `.ai/ROLE_CONFIG.md` for role bindings.

Site-scoped Controls land with the first controller (T024), not with T020A's
carrier. The narrow fuel runtime does not complete A or B: A completes at T025,
B at T027 and the first Finding is T028. T021 is the first slice that makes a
declaration true rather than declared; what it does not have is a controller, a
generated observation, a gateway, staging, ingestion, accepted history, analytics
or a Finding.

## What Is Built

T001-T020 are complete and merged in the base: Site creation/readback, Foundation
topology/devices/mappings/SLD, Fuel Loss scenario inspection, frozen Draft setup
and Runs inventory/detail. T020A, T020A1 and T020B add typed component properties,
addressing, reachable readiness and the declared boundary contract.

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

`var/runs/` holds 149 local Drafts. Six were added by two runs of
`tools/layout-evidence.mjs`, one per run-setup visit, which is what that tool has
done since T019; nothing clears them. A local Draft is not shipped proof of
anything: the reachable path is proved by
`backend/tests/test_execution_contract_alignment.py` and the executable path by
`host/tests/`, both of which build the Site from the shipped template.

`run-9f74603b06384126a627a5339fc78fbe` on `mg-006` is T020B's READY Draft. It is
at contract version 5 and T021 did not execute it: the version guard is an
equality test on an integer and cannot tell a Draft frozen before this build from
one frozen by it, so every executed Draft is regenerated in process.

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
