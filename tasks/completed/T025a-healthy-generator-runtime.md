# T025a - Generator lifecycle and healthy full-site runtime

Status: complete
USER_REVIEW_REQUIRED: false

Map: A, healthy full-site physics.
Depends on: T024.
Next: T025b policy recipes and reported status completes A.
Branch: task/T025a-healthy-generator-runtime
Sizing: electrical runtime extension with one healthy full-site story.

## Outcome

Start and step a freshly frozen Kobo-like full mini-grid in Lab. Watch PV,
three addressed loads, storage, generator and fuel form one coherent world
through a sunny-to-low-PV interval, start delay and minimum-runtime behavior.
Inspect requests separately from physical state, accepted power and service.

## Read for detail

- Controlling: `.ai/DECISIONS.md`, D-2026-09-29-t025-generator-policy-package.
- `.agent/T025-architect-recommendation.md` and `.agent/T025-implementer-plan.md`
  are supporting context; the decision resolves their questions and conflicts.
- v4 sections 4.3, 5-10, 17, 23 and 25; roadmap sections 3.1-3.3 and 7/A.
- Shared checks and exclusions: tasks/README.md.

## Deliver

Add `mini-grid` v1 under execution contract 9, preserving `daytime-mini-grid`
v1 and the fuel model. Own original T025 criteria 1-6, 10, 14; criterion 13 for
healthy runs; and the balance/timing portions of 15, with request/output proof.
T025b owns the remaining criteria and integrated A acceptance.

## Acceptance criteria

1. Declare addressed STOPPED, STARTING, RUNNING and FAILED discrete state with
   scope, allowed values, initialization owner, transition rules and observable
   signals. Each transition records state address, previous/next value,
   causal event/controller reference and simulation instant. Preserve typed
   enums through state, trajectory, controller view, artifact and gated Lab.
2. Resolve/freeze Option C needs with addressed provenance, units and effective
   Foundation version: CONTROL `start-soc-threshold` (%), `stop-soc-threshold`
   (%) and `minimum-runtime` (min); PHYSICAL `start-delay` (min) and
   `generator-rated-power` (kW); existing `specific-fuel-consumption` (L/kWh)
   and tank capacity (L). The power property is runtime authority. Freeze the
   unambiguous generator-battery-tank-bus relationship and effective Site
   Controls; absent or ambiguous inputs block setup.
3. Control policy belongs to the Site. Start only at SOC <= its frozen start
   threshold; stop only when RUNNING, its minimum runtime has elapsed and
   SOC >= its stop threshold. Add no model-owned trigger, including a
   shortfall start. Dispatch follows frozen `source-priority`, including Kobo's
   `[pv-array, battery, generator]`, without substituting another order.
4. Lifecycle transitions occur only at step boundaries. Generator fixtures use
   5-minute steps; start delay, policy windows and minimum runtime are aligned
   or refused. Count minimum runtime from actual RUNNING. Specify due-event,
   sampling and new-intent phases without retroactive transitions. Preserve old
   daytime timing, including within-step reserve windows.
5. Keep controller requests distinct from actual state and accepted output.
   Start delay produces no invented generation. Initial FAILED is inert/no
   output and is not an execution failure; authored failure causes are refused
   until T035. Retain v4 section 5.1's lexical and semantic control limits;
   physical state is not switching position or controller mode.
6. Resolve generator-to-load and generator-to-battery with PV/storage flows.
   Rating is a ceiling; accept only load and shared battery/PCS headroom,
   respecting losses and preventing simultaneous battery charge/discharge.
   Check fuel before accepting energy; consumption follows accepted generator
   energy to both load and battery using the Foundation coefficient. Exact
   electrical/fuel balances include service, losses and curtailment. Disclose
   the linear law's lack of idle/start fuel.
7. Healthy operation serves intended demand with inspectable reserve/service.
   Declare scenario-owned initial fuel, SOC, lifecycle state and required timer
   history; refuse unsupported initialization rather than inventing history.
8. Lab shows simulation time, addressed component states, per-load service,
   SOC/power, fuel, named flows, transitions and requested/accepted controls.
   Reported generator status remains explicitly pending T025b; staging it
   remains T026's work. Private physical state is not a reported reading.
9. Same frozen healthy identity reproduces trajectories. Persist/read back
   state and transitions with reconstructible run-start state and time-valid
   policy. Move artifact schema 4/publication profile 4 only when their
   contracts change, keeping prior readers and reporting behavior.
10. **Contract-9 merge gate:** representative pre-change frozen fuel and
    daytime inputs parse and execute, retain deterministic identities and
    reproduce trajectories, digests and numeric observations. Cover old reserve
    windows (including within-step boundaries) and stored artifact readback;
    newly generated fixtures alone are insufficient. If this fails, return
    with the concrete incompatibility and a case for contract 10; do not
    silently invalidate or reinterpret existing v9 Drafts.

## Proof

| Case | Expected observation |
| --- | --- |
| Healthy sunny-to-low-PV run | Coherent source transitions and per-load service |
| Start request and delay | Request visible before physical RUNNING/output |
| Stop threshold before minimum runtime | RUNNING persists until Site policy permits stop |
| Output/headroom or fuel bound | Accepted energy and fuel respect limits exactly |
| Initial FAILED; unsupported failure cause | Inert physical state; explicit setup refusal |
| Repeated healthy run and stored readback | Same identity, trajectory and persisted state |
| Pre-change frozen fuel/daytime cases | Contract-9 merge gate passes |

Include independent energy/fuel calculations and boundary-timing evidence.
Run simulator/host, setup and frontend tests, shared checks and populated Lab
layout evidence. Map criteria to the review packet.

## Scope limits

This is a vertical healthy-run slice, not a generic discrete-kernel project.
Envelope schema 1 and the fuel-only mapping stay unchanged. T025b owns recipes,
reported status and A acceptance; T026 owns generator staging; T035 owns
failure/recovery causes and service assessment. No accepted operator history,
Finding, economics, intervention UI or paired-comparison claim.

## Review

Independent review checks physical balances, boundary timing, Site-policy
execution, request/output separation and the contract-9 merge gate. A's owner
acceptance remains at T025b; this task does not complete A.
Review outcome: accepted on independent review 2026-09-29. No owner review
required; the owner accepts A at T025b.

**Independent review.** Codex returned R1 (a lifecycle deadline due at the
terminal boundary was never applied) and R2 (schema-4 readback accepted
numeric and undeclared lifecycle values). A fresh Sonnet round fixed both. At
the owner's decision the contract-9 gate's fixtures, first copied from the
owner's `var/runs`, were replaced by stand-ins generated with pre-change
`96618d9`; the owner's copies never reached `main` (squash merge). A Sonnet
verification pass accepted R1, R2 and the stand-ins, having regenerated the
baselines from `96618d9` itself and confirmed no owner data remains. Reviews:
`.agent/T025a-codex-review.md`, `.agent/T025a-claude-verification-round2.md`.
Carried in the backlog: the gate no longer covers the owner's real stored
Drafts, and three owner artifacts already failed to re-render equal before
T025a. For T025b's hands-on check: the owner's `kobo-001` lacks the four new
generator properties, and with source priority `[pv-array, battery,
generator]` SOC holds near the reserve while the generator runs.
