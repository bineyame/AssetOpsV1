# Proposal: Simulator Lab cockpit elements, their merit, and where they fit the queue

Status: owner draft for Architect and Planner review. Not a decision, not a task.
Date: 2026-09-29.
Author: owner, drafted with Claude.

## 1. The ask

Decide whether, when and how to bring the Simulator Lab run screen closer to the
canonical cockpit in `Docs/UI Design/Motivation/SimulatorLab1.png`, given that no
task in T020-T036 currently schedules it.

The proposal is a **split**: a small cockpit core right after T025, a per-slice
rule that keeps it current, and the remaining polish after T036. Section 5 gives
the sequencing. Section 8 lists the decisions requested.

## 2. Context

- `D-2026-09-13-canonical-fidelity`: a surface is dressed to the mockup only after
  it has truthful content. This proposal keeps that rule. Every element below is
  proposed only once its content exists.
- The mockups show the **Simulator Lab developer shell**, not the operator product
  (DECISIONS, 2026-09-13). Operator surfaces (T027 Site Overview, T028 Findings,
  T029 Financials, T036 Portfolio) keep following v6.9 and are out of scope here.
- Current direction keeps Lab surfaces utilitarian (queue review on T023 and T029A;
  roadmap non-goal "perfect UI polish"). That is right for the inspectors. The
  consequence is that the run screen stays a set of tables through T036.
- By T025, the content the cockpit needs is truthful: PV, battery, three addressed
  loads, generator state, named accepted flows, requested vs accepted control,
  generated device readings (T022/T024) and staged envelopes (T023).
- T036 ends its client walkthrough with the gated Lab truth-versus-inference
  reveal. That moment is currently planned to be shown with tables.

## 3. Candidate elements

| Id | Element | Content source | Earliest truthful |
| --- | --- | --- | --- |
| C1 | Live values on the configured SLD (T016 SLD re-used, accepted flows and states overlaid, direction of flow) | AcceptedFlowSet, stocks, discrete state | T025 |
| C2 | Time-series charts: PV potential/accepted/curtailed, per-load demand/served, SOC, fuel; truth and reported on one axis with gaps drawn as gaps | Per-boundary trajectory + observation series | T024/T025 |
| C3 | Event and transition timeline: applied scenario events, discrete transitions (generator STOPPED/STARTING/RUNNING/FAILED), bounded transitions, reporting gaps | Kernel ledger | T025 |
| C4 | Requested vs accepted control panel ("asked 30 kW, accepted 22 kW, why") | ControlIntent + AcceptedFlowSet | T024 |
| C5 | Auto-play: steps on a wall-clock timer, pause, resume; speed changes wall time only, never simulated time | Existing step port | T022 (any time) |
| C6 | Run header: simulated window, progress bar, seed, versions | Existing projection | T022 |
| C7 | Gateway output lane beside device readings (published vs source time) | T023 stage | T023, richer at T026 |
| C8 | Gateway/ingestion health dashboard, ingestion log viewer (mockup screens 8-9) | T027 accepted/rejected records, T026A delivery behaviour | T027/T026A |
| C9 | Run-setup wizard, scenario authoring (mockup screens 4-5 New/Edit) | New authoring model | Not scheduled |

Not proposed, because they conflict with settled design. The mockup should be
corrected instead:

- **1-second step and 100x speed.** The kernel runs declared boundaries (15 min in
  the shipped documents), and execution speed must not change simulated time
  (T022 AC2). C5 gives the "live" feel without this.
- **Live Quick Actions that inject events mid-run.** `D-2026-09-20-run-scoped-event-injection`
  and T029A make interventions frozen, run-scoped artifacts declared before
  execution. A cockpit may offer "declare an intervention and re-run", not live buttons.
- **Device "Online / last seen" inside the Lab.** Source health is backed by
  accepted source observations (`D-2026-09-17-source-health-backing`) and belongs
  to the operator side after T027.
- **Cold room on the mini-grid SLD.** Cold chain is a later vertical.

## 4. Merit by audience

Scale: ●●● high, ●● moderate, ● low, - none.

| Element | Client demo | Investor demo | Owner tracking | Electrical engineer onboarding | Software engineer onboarding |
| --- | --- | --- | --- | --- | --- |
| C1 Live SLD | ●●● | ●●● | ●● | ●●● | ● |
| C2 Charts truth vs reported | ●●● | ●●● | ●●● | ●●● | ●●● |
| C3 Timeline | ●● | ●● | ●●● | ●● | ●●● |
| C4 Requested vs accepted | ●● | ● | ●●● | ●●● | ●● |
| C5 Auto-play | ●●● | ●●● | ● | ● | ● |
| C6 Run header/progress | ● | ●● | ●● | ● | ● |
| C7 Gateway lane | ● | ●● | ●● | ● | ●●● |
| C8 Health dashboard, logs | ●● | ● | ●● | ● | ●●● |
| C9 Wizard, authoring | ● | ● | ● | ● | ● |

What the merit rests on:

- **Client demo (operators, domain experts).** They read power systems through an
  SLD and daily curves. A live SLD and an SOC/PV/load day curve make the site
  recognisable in seconds. They let the T028 finding ("generator ran while the
  battery could have covered it") be seen rather than explained. Truth vs reported
  on one chart shows why AssetOps must reason about evidence gaps.
- **Investor demo.** The claim to land is "the analytics are not scripted"
  (roadmap 5.7). Watching a world run with auto-play, then showing that the product
  inferred the cause from gappy readings, is the strongest version of that claim.
  Tables carry the same fact with far less impact.
- **Owner tracking.** Each owner checkpoint (T024 "physical response coherent",
  T025 "site behaves credibly", T029A "change takes effect at the declared time")
  is a judgement about shapes over time. A chart shows a wrong curve instantly; a
  table of 96 boundaries hides it. The timeline shows *why* something happened
  without reading the kernel ledger. Charts also become the standard evidence
  in review packets, beside the existing layout evidence.
- **Electrical engineer onboarding.** An electrical engineer checks a simulator by
  looking at the SLD, the power balance and SOC against reserve. C1 + C2 + C4 let
  them validate the physics model (limits, priorities, efficiency, curtailment)
  without reading Python. That is also how the project gets domain review of T024/T025.
- **Software engineer onboarding.** The architecture's core idea is the pipeline:
  truth → device observation → envelope → ingestion. Lanes for truth, reported and
  published (C2 + C7) and the timeline (C3) show every boundary and what crosses
  it. That matches `Docs/AssetOps_MiniGrid_Technical_Walkthrough.md` and shortens
  the time to understand the invariants.

Cost, relative to the queue: C1-C6 are presentation over data that already exists,
with one architectural exception (section 6). C8 depends on T027/T026A content.
C9 needs a new authoring model and is the most expensive for the least merit.

## 5. Cadence and sequencing

Current order (tasks/README.md): T024, T025, T026, T027, T028, T029, T029A, T034,
T030, T031, T032, T033/T035, T036; T026A unscheduled.

Proposed:

```text
T024 ─ T025 ─ [L1 cockpit core] ─ T026 ─ T027 ─ T028 ─ T029 ─ … ─ T036 ─ [L3 cockpit polish]
                     │
                     └─ L2 rule applies to every slice from T026 on
```

**L1 - cockpit core, one slice, immediately after T025 merges.**
Scope: C1, C2, C3, C4, C5, C6. Nothing else.
Why here:
- T025 completes roadmap A; its content is the first that is both truthful and
  broad enough. Before T025, generator states and the full flow set do not exist,
  so C1/C3 would be rebuilt.
- It precedes T028/T029 (demo point 2, first external exposure), which is the
  first time a client or investor sees the product.
- It precedes T026-T035, so every later slice is reviewed with charts rather than tables.
- It sits outside the protected finding path (T027 → T028 → T029 → T034). It
  delays T026 by one slice and does not touch any protected seam.

Alternative if the Planner prefers not to delay T026: run L1 in parallel with T026,
which touches the observation/gateway side rather than the run-screen presentation.
This only works if the frontend areas are clearly separated.

**L2 - keep it current, standing rule from T026 on.**
Any slice that adds a physical state, flow, signal, discrete transition or
intervention also adds it to the cockpit's charts or timeline as part of its
definition of done. The expected size per slice is small. Examples: T026 adds
reported series for the new signals; T029A marks the intervention on the timeline;
T033 adds the stress trajectory; T035 adds the FAILED transition.
This replaces a big-bang restyle at the end with steady growth, and it prevents
the cockpit from falling behind the world.

**L3 - polish, after T036 or when demo feedback asks for it.**
Scope: C7 enriched, C8 (only if feedback asks), mockup-level layout and visual
polish, and C9 only if the product needs in-app authoring.
Deciding L3 after T028/T029 and T036 feedback means building what audiences
actually reacted to.

Operator side: unchanged. T027/T028/T029/T036 follow v6.9. The only link is an
"Open in AssetOps" action from a committed run to its operator Site (available
from T027).

## 6. Architectural implications for the Architect

1. **Series persistence.** T022 persists a completed run's final projection, not
   its whole trajectory (T022 packet, "Criterion 12 persists a completed
   projection"). C2 and C3 need the per-boundary series for completed and reloaded
   runs. Options:
   - (a) persist the trajectory and observation series in the execution artifact,
     which is size-bound by the run length;
   - (b) re-execute deterministically from frozen inputs to rebuild the series on
     demand, which relies on T021's determinism and the kernel version matching.
   This is the one non-presentation decision in L1, and it should be made before L1.
2. **One gated read model.** The cockpit reads a series form of `LabProjection`
   only, through gated Lab routes. No new path lets private truth reach operator
   surfaces. Gate-off tests extend to the new routes.
3. **Unavailable is not zero.** Charts draw gaps, stale and unavailable readings
   as absences, never as zero or interpolated lines. This is invariant 8 in visual form.
4. **Auto-play uses the existing step port** with the `fromBoundary` guard. It
   adds no server-side clock and no simulated-time dependence on wall time.
5. **Run-store read cost.** Charts on a Runs inventory would repeat the T022A
   problem. The cockpit stays on the single-run read path. The inventory decision
   carried by T022A stands on its own.

## 7. Risks

- **Scope creep toward C8/C9.** L1 is fixed at C1-C6; anything else goes to L3.
- **Polish before substance.** L1 is presentation of existing truth, not new
  modelling. If it needs new kernel output, stop and return that to the owning slice.
- **Mockup drift.** Update or annotate `SimulatorLab1.png` for the conflicts in
  section 3, so implementers are not held to a 1-second step or live injection.
- **Layout evidence cost.** Charts and SLD overlays are layout-sensitive. Browser
  evidence applies (`D-2026-09-20-layout-evidence-standing`), measured against a
  copy of `var/`, as in T022.

## 8. Decisions requested

1. Adopt the L1 / L2 / L3 split, or keep the cockpit entirely after T036.
2. L1 placement: after T025 and before T026 (recommended), or in parallel with T026.
3. Series persistence for C2/C3: persisted series (a) or deterministic re-execution (b).
4. Adopt the L2 per-slice cockpit rule into `tasks/README.md` shared checks.
5. Record the mockup corrections (1-second step, 100x speed, live injection,
   Lab-side Online status, cold room) against `Docs/UI Design/Motivation/`.
