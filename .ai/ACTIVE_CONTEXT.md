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

**T020B is complete and accepted, awaiting merge.**
`tasks/completed/T020B-execution-contract-alignment.md`, branch
`task/T020B-execution-contract-alignment`, packet
`.agent/T020B-review-packet.md`, review `.agent/T020B-claude-review.md`.
Independent review verdict ACCEPT on all twelve criteria, from a fresh Claude
reviewer standing in for Codex at the user's instruction; the owner reviewed the
UI and approved it. `main` is untouched: the Implementer did not merge.

The shipped Fuel Loss Event now reaches `READY` through the form and API path.
The three states that blocked it were three different problems. Site demand and
irradiance are `OPTIONAL` at all five positions and are recorded on the run as
unsupported optional inputs rather than blocking it; reporting-path availability
was never the model profile's to answer, so `REPORTING_PATH_STATES` names it a
fact about the path and the publication profile declares it. Exactly one profile
answers for each state, decided by the state, and a profile claiming the other's
is refused at construction. A requirement conflict refuses instead of resolving
to `REQUIRED` - the parser for one authored address, run setup for two spellings
that resolve to one. The execution contract publishes the v4 boundary cycle, what
a reading timestamped T describes per reading class, the linear window ramp, a
forcing outside its window being unavailable, and what each bound policy commits
a kernel to; all of it renders on the scenario detail screen.
`EXECUTION_CONTRACT_VERSION` moved 4 to 5 and stored runs keep theirs.

F5 carried out of T020A1 is closed; the backlog records why - not a missing check
but two checks that could not see each other, so all three sites now ask one
authority record and share one statement. `.agent/T020B-guard-probes.py` breaks
each guard and asserts the tests notice.
`run-9f74603b06384126a627a5339fc78fbe` on `mg-006` is the READY Draft the owner
reviews.

**T020A1 and T020A before it are complete and merged**; full records in
`.ai/CODE_STATE.md`, packets and reviews in `.agent/`. A world state is named by
an ADDRESS - a semantic key plus the component it is claimed on, or `site:` for a
fact about the installation - carried by one `StateRef` from the document to the
frozen run; a Foundation declares typed unit-carrying properties that run setup
resolves through the profile's binding.

Four lessons those three slices paid for, worth more than their fixes. **Who
supplies a number and which asset it is about are two questions.** **Visiting a
reference is not resolving it.** **A check that answers a different question is
not an answer.** **Two checks that cannot see each other will disagree** -
T020B's F5. Plus the test shape that let each survive: a test written to prove
enforcement must not exempt what the code exempts.

**Three things T021 must know** are in the backlog beside the carried items, and
the T020B code-state entry adds a fourth.

Carried, not lost: five open inline-`float(value)` overflow sites in
`.ai/MILESTONE_REVIEW_BACKLOG.md`, the HTTP-reachable one first, and no sixth was
added. The run store's O(n) create wants a bounded fix with an owner before
T027; `var/runs` now holds 127 Drafts.

**Next task: T021**, then T021A, T022, T023 and T024 onward per that README.
None of the resequencing touches the starter path. A user-review checkpoint has
just passed, so `.ai/WORKFLOW.md` applies: do not assume the next planned slice
is still correct without the user confirming it.

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

The earlier Architect review corrected one forward dependency - T026 introduces
the first operational-record family, which T028 needs and T030 extends, and the
thinning preserved it - and replaced the workflow's task-spec size bands with
ceilings under `D-2026-09-24-task-spec-size-ceilings`.

Direction comes only from:
- `Docs/simulator_design_v4.md` for simulator mechanisms;
- `Docs/mini-grid-demo-architecture-and-roadmap.md` for demo path and order.

The old two-roadmap precedence, fuel-first Finding and late electrical-world/
StateRef plan are superseded by `D-2026-09-24-v4-roadmap-replan`.
Earlier feature-map revamps, alignment reviews and v3 assessments do not direct
this work. Do not reconcile the new plan back to them.

## Read For The Active Task

1. `tasks/T021-minimal-fuel-loss-causal-kernel.md` and `tasks/README.md`. T020B
   DECLARES the executable contract and T021 proves a kernel conforms to it;
   its packet and review are the built state T021 extends.
2. `.ai/CODE_STATE.md`: the T020B entry first - it names the boundary cycle, the
   reading conventions, the bound policies and the three things T021 must know -
   then T020A1, T020A and T018-T020 for the carriers and frozen setup.
   Completed tasks are regression/history evidence, not future direction.
3. `.ai/PLANNING_HANDOFF_T020A_T023.md`: Runtime; Placement; Contract Versions
   And Retirements, whose outstanding transition is T021A's.
4. `backend/assetops_backend/scenarios/execution.py` in full. It is the contract
   T021 implements, and `BOUNDARY_CYCLE`, `OBSERVATION_RULES`, `DISPATCH_RULES`
   and `BOUND_POLICY_STATEMENTS` are the parts that bind a kernel.
5. v4 sections 6, 7, 8, 9 and 23, plus the decisions those name.
6. `.ai/ARCHITECTURE.md`; `.ai/WORKFLOW.md` for seams, sizing and review shape.
7. `.ai/ROLE_CONFIG.md` for role bindings.

Site-scoped Controls land with the first controller (T024), not with T020A's
carrier. The narrow fuel runtime and initial staging do not complete A or B:
A completes at T025, B at T027 and the first Finding is T028. A declared
contract is not an implemented one - T020B settles what a kernel must do and
T021 is the first thing that does any of it.

## What Is Built

T001-T020 are complete and merged in the base: Site creation/readback,
Foundation topology/devices/mappings/SLD, Fuel Loss scenario inspection, frozen
Draft setup and Runs inventory/detail. T020A and T020A1 add typed component
properties and addressing on top; `.ai/CODE_STATE.md` has both.

**After T020B the shipped Fuel Loss Event reaches `READY` through the product
path**, so the fixture `READY` proof is retired as the demonstration. The
executable contract is declared in full - boundary cycle, reading conventions,
window ramp, forcing availability and bound policies - and
`EXECUTION_CONTRACT_VERSION` is 5. **Nothing executes any of it.** There is no
kernel, no clock, no generated observation, no staging, no ingestion, no
accepted history, no analytics and no Findings, and `READY` still carries the
disclosure that says the advertised supported set is unverified. T021 is the
first slice that makes a declaration true rather than declared.

The shipped scenario lives in `config/scenarios/fuel-loss-event.yaml`.
Shipped and writable stores have disjoint identities; the scenario store ships
nonempty because there is no authoring UI.

## Local Data To Preserve

The working checkout's gitignored `var/sites/` holds mg-001, mg-002 (cold room)
and mg-003 (two AC buses), which the user asked to preserve. Do not clear,
replace or delete that directory. Updated templates do not mutate existing
Sites: use a new explicit fixture for new property/schema demonstrations and
leave existing fixtures intact. An isolated checkout does not contain them.

T020B added **mg-006**, instantiated from the shipped hybrid template through
the product's create path, plus `var/scenarios/fuel-loss-event-mg006.yaml`, a
copy of the shipped document pointed at it. `run-80c45f818de543c3bbdc3db79e5e6f1f`
is the `READY` Draft the owner reviews. `fuel-loss-event-mg004.yaml` was left
exactly as T020A wrote it, at `REQUIRED`, so its Drafts stay blocked on the two
lowered states - a deliberate non-migration of user data, noted in the T020B
packet.

T020A1 added **mg-005**, instantiated from the new twin-tank archetype through
the product's create path, plus `var/scenarios/twin-tank-addressed-mg005.yaml`
and `twin-tank-ambiguous-mg005.yaml` - the two Drafts the owner reviews. The
local mg-004 scenario was migrated to the addressed form with the shipped one.

T020A added **mg-004**, instantiated from template version 2 through the
product's create path, and `var/scenarios/fuel-loss-event-mg004.yaml`, a local
copy of the shipped scenario pointed at it. A run is bound to the site the
scenario declares and run setup will not retarget one, so the resolved case
needs a scenario that names the new fixture; the shipped definition still
targets MG-001, whose Foundation declares no properties, and the Draft it
produces is the BLOCKED case the same review looks at. mg-001, mg-002 and
mg-003 were not touched.

`var/scenarios/` is the writable scenario store; `var/runs/` contains 127 local
Drafts, including T020's fixture-only READY run, which was left in place. A
local Draft is not shipped proof of anything: the reachable path is proved by
`backend/tests/test_execution_contract_alignment.py`, which builds the Site from
the shipped template rather than reading one out of `var/`.

## Standing Direction And Checks

`D-2026-09-22-milestone-speed-over-purity` binds every slice and review.
Stop for expensive-to-reverse defects, misleading claims or user-only decisions.
Carry cheap refinements in `.ai/MILESTONE_REVIEW_BACKLOG.md`; do not turn each
v4 concept into an independent task.

Run `tools/check-agent-workflow.ps1`, `tools/check-architecture.ps1` and checks
appropriate to the changed behavior. Layout-sensitive implementation requires
the workflow's browser evidence. `node tools/layout-evidence.mjs` now takes the
Site to measure as its second argument, or `ASSETOPS_LAYOUT_SITE`: a Foundation
section a site declares nothing for renders as a stated absence and not as a
table, so measuring containment against such a site measures an empty set.
