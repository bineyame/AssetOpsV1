# Mini-grid demo architecture and roadmap

This document is an execution and product-demonstration companion to
Docs/simulator_design_v4.md. It does not redefine the simulator architecture.
Where this document summarizes a simulator mechanism, v4 remains normative.

Architect execution guidance, 23 September 2026. This is a delivery proposal,
not an inventory of completed capabilities or a replacement task queue.
References to v4 sections mean [Simulator design v4](simulator_design_v4.md).

## 1. Executive intent

The mini-grid demo should make one proposition tangible:

> AssetOps shows distributed-energy owners where operating behaviour is
> affecting cost, service, asset value and opportunity, gives evidence for
> the conclusion, and helps verify whether an intervention worked.

The likely audience is a mini-grid owner, operations lead or asset manager,
accompanied by a technical reviewer who will ask where the numbers came from.
They should remember a short interaction: **show me what matters, show me why,
and show me whether the response helped**. The simulator supplies inspectable
operating situations before a customer site is connected. It is not the
client-facing value proposition.

Build one convincing path through one Site before widening the portfolio.
Start with fuel evidence because it is the current executable-contract wedge.
Finish that path through ingestion and operator screens before building a
broader electrical world. Then add the measurements and analytical contracts
needed for a fuel finding, its economic consequence and a verified response.
Dispatch, service, productive use and asset stress extend that same path.

The first demo is not a generic monitoring dashboard, a full CMMS, a full
power-system simulator, a digital-twin claim or a complete fleet-management
suite. Real protocol integrations, detailed network physics, calibrated asset
life prediction, comprehensive maintenance scheduling and all three verticals
are outside its scope. No screen needs fabricated completeness to tell the story.

Credibility depends on v4's causal world, explicit initial conditions,
component addressing, reproducible execution, and separation of requested
control from accepted physical behaviour. Equally essential are the one-crossing
source-envelope rule, truth isolation, normal ingestion, explicit uncertainty
and downstream economics. These protect the product's conclusions; file-backed
storage and a small recipe set are sufficient infrastructure.

### Delivery thresholds and what exists today

The inspected checkout at `1717d9c` contains Site/Foundation, topology,
devices/mappings, configured SLD, scenarios, frozen Draft setup and Runs
inventory/detail. The simulator package is still a scaffold; run execution,
gateway envelopes, ingestion, accepted evidence, Replay, Findings and financial
or verification objects are not implemented. Some planning status is stale:
`ACTIVE_CONTEXT.md` still describes T020 as unmerged, while the inspected
checkout contains its inventory and readiness disclosure. Do not count a
documented mechanism as implemented software.

| Delivery threshold | What can be demonstrated | Claims allowed |
| --- | --- | --- |
| Current build / M1B | Configure and inspect a Site; select a scenario; inspect frozen Draft inputs and blocking reasons. | Configuration and declared capabilities only. `READY` is not an executed result. |
| M1C: causal runtime | Run, pause and step the narrow fuel world; compare private state with generated readings in Lab. | A reproducible simulation, still no operator evidence. |
| Demo Ready v1: evidence loop | Stage, Commit, inspect ingestion acceptance/rejection, inspect operator evidence/provenance and Replay. | Earliest client-ready **evidence-loop** walkthrough under the current Product document. No analytical or economic claim. |
| Demo Ready v2: first conclusion | Follow accepted observations to fuel/runtime analysis and a bounded Finding with evidence and missing-data behaviour. | First business-outcome demonstration; preserve its existing review checkpoint. |
| Expanded proposition demo | Add a bounded financial bridge, intervention and verification; then dispatch/service, productive-use and stress stories as they become evidenced. | Only the portions actually built. A modeled opportunity is not realized revenue; modeled intervention impact is not field-proven causality. |

For outreach focused on the complete proposition, target the first Finding plus
its financial explanation and one verification loop. An earlier meeting can
use Demo Ready v1, explicitly scoped to the evidence loop, with later capabilities
described as a roadmap. Do not delay that useful meeting for the full v4 programme.

## 2. How v4 maps to the demo

Here **NOW** means the path to the first useful committed-evidence slice;
**LATER** means not a prerequisite to that slice. Some LATER capabilities are
needed before demonstrating a particular client claim, as stated below.

| v4 concept | Why it exists | What it enables in the demo | Priority |
| --- | --- | --- | --- |
| Causal world model (§§4, 8) | Causes produce trajectories; fixtures cannot prescribe results. | Remove a fuel-removal cause and the tank discontinuity disappears. | NOW: narrow fuel model. |
| Component-addressed state (§4.2) | Separate semantic state names from their Site/component targets. | Readings and initial values resolve to the right tank, generator and later each load. | NOW: T020A sizing/addressing work. |
| Controller intent vs accepted physical flows (§7) | Requested output cannot bypass physical limits. | Explain a 30 kW battery request with only 22 kW physically delivered. | LATER: before dispatch/service claims; preserve the seam in the initial kernel. |
| Boundary timing (§6) | Stock samples and preceding-interval measurements have different meanings. | A delivery at 11:00 appears in the 11:00 tank reading without changing the preceding interval's energy. | NOW. |
| Device observation transform (§11.1) | What a device reports can differ from truth or be missing. | A reporting gap hides the loss; a hand record later adds evidence. | NOW: cadence and gap; richer faults later. |
| Simulated gateway (§11.2) | Produce the same logical input a real source would produce. | Inspect mapping, source/publication times, message identity and quality. | NOW: deterministic publication; outage/retry breadth later. |
| Staged envelopes + Commit (§11.3) | Execution cannot silently change product history. | The operator Site stays unchanged during Draft execution, then receives only accepted released records. | NOW. |
| Normal ingestion (§§1, 3) | Product owns validation, mapping, acceptance and evidence. | Rebuild the Site evidence view from persisted envelopes with no simulator present. | NOW. |
| Operational records (§12) | Human/business records are observations with their own completeness and errors. | Hand dip first; later delivery and maintenance records constrain conclusions. | NOW: T023's dip only; extend by story. |
| Asset stress (§14) | Accumulate causal exposure without pretending to know a failure date. | Battery stress and generator wear context in asset views. | LATER: after the evidence and service paths. |
| Intervention model (§13) | A response changes world/configuration/reporting before it changes evidence. | A maintenance activity can complete while its Finding remains unresolved. | LATER: required for the verification story. |
| Paired experiment (§15) | Prove allowed differences across resolved frozen inputs. | Compare a reserve policy or added mill under controlled modeled conditions. | LATER: required before any all-else-equal claim. |
| BusinessContext (§22) | Prices and business assumptions do not belong in physics. | Explain fuel exposure from a quantity range and an explicit price assumption. | LATER: before economic claims. |
| Truth comparison (§21; canonical screen 8.17) | Evaluate model/product behaviour without feeding answers into analytics. | Developer verifies whether a Finding matches the modeled cause. | NOW: private regression proof; LATER: dedicated admin overlay. |

### Trade-off decisions

| Classification | Delivery choice |
| --- | --- |
| MUST GET RIGHT NOW | Source-envelope crossing and strict parsers; frozen input ownership and `StateRef`; v4 timing and existing bound/dispatch semantics; versioned exact arithmetic and RNG when used; dependency guards; private truth/observation separation; immutable Commit, overlap protection and ingestion-owned receipts; evidence lineage and honest unavailable states. |
| GOOD ENOUGH FOR DEMO | One Site, one fuel model, fixed authored forcings, one reproducible gap, deterministic publication, synchronous ingestion and file-backed artifacts behind ports. A strict small typed-record allowlist is enough; no plugin framework is needed. Use existing Foundation/SLD presentation and a small number of backed panels. |
| DEFER UNTIL SECOND VERTICAL / REAL SITE | General pack discovery, broad fault catalogue, real protocol emulation, distributed infrastructure, extensive fleet roll-ups, calibration tooling and sophisticated degradation laws. Develop these when another vertical or a real source proves the need. |

Deferral does not waive precision when a capability is introduced. Controller
ownership and physical acceptance become MUST GET RIGHT NOW at the first
controller slice; resolved-input comparability at the first paired experiment;
technical lineage and non-double-counting at the first financial line.

Before **any client evidence-loop demonstration**, finish the v1 acceptance
path, including an explainable rejection, provenance, Replay and the gate-off
test. Before **business-outcome outreach**, add a supported analytical claim,
an uncertainty/missing-record alternative, and, if cost or successful
intervention is in the pitch, the corresponding financial or verification
path. Stress, portfolio generation, productive-load pairing, a truth overlay
and other domain packs can remain design-only until those stories are promised.

### Material alignment decisions

Only differences affecting delivery or a protected boundary are listed here.
This document changes neither v4 nor the referenced task files.

| Existing source / issue | Execution instruction and landing point |
| --- | --- |
| `multi-vertical-build-plan.md` §§3–6 treats a flat `state_key` container and unchanged profiles/T020A as sufficient. | v4 §§4.2, 24 requires resolved `StateRef` through support declarations, bindings, scenario selectors and frozen initialization. Planner sizes the property carrier separately from addressing before implementation; component control properties use the carrier, Site Controls wait for a controller. |
| Older plan's three-phase description and decision shorthand “observe after the step” can imply pre-event samples or forward-looking interval values. | T020B declares v4 §6's boundary cycle. Preserve half-open dispatch, linear window quantities, unavailable out-of-window forcing and recorded bounded continuation. Do not introduce a second clock or silently reinterpret old frozen runs. |
| Older plan §4 leaves a fifth policy owner unresolved; §4 economics proposes extending physical units for money. | Both are settled by v4 §§5.2, 22: baseline policy is time-valid Foundation/Controls; `ControlAssumption` remains documentary; economics uses downstream `BusinessContext`. No monetary dimension in the kernel or simulator unit tables. |
| Existing run/scenario types and execution constants are backend-owned, but simulator needs frozen contracts. | At T021/T022 composition, expose the minimum shared execution contracts neutrally or adapt them through neutral `host/` ports. Simulator imports no `assetops_backend`; backend imports no simulator; neither imports `host/`. T023 source schema must also be neutral. Do not weaken the existing guard to wire execution. |
| T022 groups reporting faults under the observation transform. | v4 §11 assigns sampling/bias/dropout to observation and buffering/outage/retry/publication to gateway. A T022 sensor gap is sufficient now; put gateway outage behaviour in the gateway slice. |
| T022 still calls reconciliation-panel retirement undecided. | `D-2026-09-22-reconciliation-panel-retirement` and the scoped Planner handoff already settle removal with authored device readings in T022. Carry that decision into the task; do not ask for it again or retain reference arithmetic as product authority. |
| Canonical screen 8.12 / runtime examples include switching positions and controller modes. | v4 §5 and repository vocabulary guards defer those semantics, including renamed equivalents. Render supported physical states and configured topology only. A convincing SLD does not require invented switching evidence. |
| Older build plan suggests narrow fuel physics can deliver avoidable-runtime claims and that each new state automatically enables Findings. | Observed runtime can be assessed narrowly; **avoidable** runtime additionally needs feasible alternatives, policy and observations. New private states need observable bindings, allowlisted source records and a product derivation before appearing in a claim. |
| Feature-map milestone order places cold-chain T030–T033 before first conclusions T034–T038; this task asks for mini-grid-first product value. | Preserve the active T020A→T020B→T021→T021A→T022→T023 queue. Recommend a Planner milestone adjustment after T029 to bring the mini-grid conclusion chain forward, then extend it before a second pack. This is an explicit proposed programme-order change, not a silent task renumbering or a prerequisite to work through T029. |
| Paired runs may overlap, but canonical Site history cannot contain ambiguous overlapping runs. | Keep the overlap block. Pairing is comparison metadata, not permission to merge histories. §3.10 describes what can ship without a new history branch model. |

## 3. End-to-end technical walkthrough — mini-grid

### 3.1 Kobo: one stable Site, progressively executable capabilities

Use **Kobo Mini-grid** as the client story: PV + BESS + diesel generator + fuel
tank supplying households, a clinic and a productive mill. Its illustrative
component identities are `PV-001`, `INV-001`, `BAT-001`, `PCS-001`, `GEN-001`,
`TANK-001`, `AC-BUS`, `LOAD-RES`, `LOAD-CLINIC` and `LOAD-MILL`.
PV/inverter, battery/PCS and generator feed the bus; the bus supplies the loads;
the tank supplies the generator. This is causal topology, not an AC load-flow model.

Kobo is a proposed recipe, not a new checked-in fixture. The shipped scenario
currently targets `MG-001`; use that existing Site for the first queue acceptance
proof. Author a versioned Kobo definition/recipe later through normal contracts,
with an explicitly declared stable Site identity. Do not silently rename MG-001,
change scenario target policy or overwrite the retained local fixtures.

Initially the PV, BESS and load branches can appear as **configured** assets.
Only the fuel/generator model's supported states execute. Unsupported demand
and irradiance remain disclosed optional inputs as T020B specifies. Neither a
configured clinic nor a demand profile makes service reliability calculable.

| Input | Owner and frozen meaning | Product implication |
| --- | --- | --- |
| Tank capacity; generator specific fuel consumption in `L/kWh`; equipment ratings and connections | Site Foundation, resolved at its frozen version and validity instant. | Foundation screen explains the physical expectation's configuration basis. |
| Initial fuel, initial SOC, physical generator state, existing stress | Scenario/run-initial-condition ownership; explicit attributable values. | Private initialization is not an opening product measurement. Unknown existing-asset stress never becomes zero. |
| Consumption law; supported state/role/addressing rules; bound relationships | Versioned model profile and pack. | Readiness/conformance states what the model actually supports. |
| Dispatch forcing, fuel movement, load schedule, faults and evidence conditions | Scenario causes/conditions; not computed trajectories or Findings. | Lab timeline explains the test situation, not what AssetOps knows. |
| Cadence, reporting identity and observation behaviour | Frozen publication profile and resolved observation bindings. | Missing samples have a defined expected cadence; Foundation does not invent one. |
| Baseline reserve, start thresholds and source/critical-load priority | Foundation/Controls: typed component controls and later typed Site Controls. | Product analysis checks configuration valid during the interval, not the latest policy. |
| Fuel price, tariffs, maintenance cost, replacement assumptions | Downstream versioned BusinessContext. | Financials exposes assumptions independently of simulated physics. |

### 3.2 Freeze the experiment before execution

Run setup freezes Site/Foundation binding, scenario version and resolved
parameters, interval/timestep, seed, model/publication profiles, execution
contract, simulator version, initialization and ordered interventions. Every
frozen answer retains its answerer. Reuse `DeterministicIdentity`,
`FrozenInterval` and `frozen_inputs()`; do not create a parallel identity model.

Resolve addresses such as `StateRef(COMPONENT, "fuel-tank-volume", "TANK-001")`.
An unqualified component binding resolves only if exactly one candidate exists;
zero or multiple candidates block rather than selecting the first tank. Later,
household, clinic and mill demand use the same semantic state with different
component IDs. Do not encode those IDs into state-key strings.

Malformed/unfreezable requests are refused; resolvable Drafts with unsupported
required inputs or unresolved Foundation answers are persisted as `BLOCKED`.
`READY` does not override either boundary. The current declaration-only
disclosure ends when T021's real model conformance check makes it false.

For the arithmetic walkthrough below, use an **illustrative future fixture**:
24 September 2026, 08:00–12:01 Kobo local time, one-minute steps, a fixed declared
seed, and one-minute fuel/energy reporting. Freeze UTC instants; use the Site's
IANA timezone for display. The analysis window is 08:00–12:00; the run extends
past 12:00 so that its closing sample lies inside the half-open run interval.
These are fixture choices, not changes to `FrozenInterval` or shipped cadence.

### 3.3 Evolve the physical world with v4's boundary cycle

At every boundary `T`, apply events/configuration changes due at `T`; sample
post-event stocks/discrete state if due and attach measurements of the preceding
`[T-dt, T)` interval; transform/report them; then build the controller view,
produce `ControlIntent`, resolve `AcceptedFlowSet`, integrate `[T,T+dt)`, check
conservation/bounds and carry state to the next boundary. This is v4 §6, not a
new scheduling convention. No preceding-interval measurement exists at the
first boundary unless an explicit historical window is supplied.

The first fuel profile uses declared generator output forcing; it does not
need a dispatch controller. With a frozen coefficient of **0.35 L/kWh** and
**40 kW** output over four hours, generated energy is **160 kWh** and fuel use
is **56 L**. Declare the same 40 kW forcing through the 12:01 run end so the
extra closing-sample step has an explicit input; the calculation below covers
only the four-hour analysis window. Foundation owns the coefficient; the scenario owns the operating
window; the model owns multiplication and integration. The following example
does not correct the shipped Fuel Loss Event's numbers: T021 must compute that
trajectory and present the existing authored-cause decision at its checkpoint.

| Illustrative cause / boundary | Private world consequence | Potential observation |
| --- | --- | --- |
| 08:00 initialization: 430 L in a 500 L tank | Explicit initial stock. | A generated opening level of 430 L if its source samples. Initial interval energy unavailable. |
| 08:00–12:00 analysis within the declared 08:00–12:01 forcing | At 40 kW, consumption integrates to 56 L over the analysis window. | Metered interval power/energy after each completed interval, once this source type is supported. |
| 10:10–10:20, remove 80 L | Quantity ramps linearly through the declared window; removal does not land as a single end-of-window jump. | No device samples during the declared 10:00–10:30 reporting gap. |
| 10:30 sample | 430 − 35 − 80 = 315 L. | A generated 315 L reading in the error-free example; the gap limits timing attribution. |
| 11:00 point delivery: +50 L | Immediately before delivery: 308 L; after: 358 L. | 11:00 stock sample sees 358 L; interval energy at 11:00 still describes 10:59–11:00. A separate delivery record exists only if reported. |
| 12:00 closing sample | 430 − 56 − 80 + 50 = 344 L. | Generated closing level and an independently sourced hand dip may corroborate this quantity. |

Use the existing `DISPATCH_RULES`, `BOUND_POLICIES`/`BOUND_CASES`, canonical
units, rate integrals and non-negativity rules. Due causes apply exactly once.
Outside its declared window a forcing is unavailable, not implicitly zero or
held. Unsupported consumption intervals must fail or become unavailable as
the profile declares; no hidden operating assumption fills them. A bounded
delivery records accepted/refused quantities and continues from the bounded
state; a `FAIL_RUN` condition cannot be relabelled completion.

World arithmetic follows v4's `EXACT_RATIONAL` policy. Normalize authored
floats only at the input boundary, never by per-step denominator approximation.
When randomness is introduced, use the specified BLAKE2b-256 draw identity and
domain separation; adding a sensor-noise stream must not change demand or fuel
movement. No random library or elaborate noise model is necessary for the
first deterministic gap story.

### 3.4 Widen to a coupled mini-grid only when a screen needs it

The later dispatch slice makes PV, BESS and loads executable. For example, at
a boundary the controller may request 30 kW battery discharge for a 42 kW load
while PV supplies 20 kW. A 22 kW PCS limit permits only 22 kW discharge. The
control trace retains the 30 kW request; accepted flows are 20 kW PV-to-load
and 22 kW battery-to-load. Only accepted flows evolve stored energy and feed
meter observations. In another interval, insufficient accepted supply leaves
unserved demand; it cannot be erased by the requested setpoint.

The pack's declared cascade owns capability/priority/limit resolution,
curtailment, charging and unmet demand; exact source/sink conservation is
checked. Initialization and typed transitions govern physical generator states
such as STOPPED, STARTING, RUNNING and FAILED. Controller inputs can be local
and more frequent than AssetOps-visible telemetry. Neither local inputs nor
`ControlIntent` becomes evidence merely because the controller used it.

Introduce Site Controls when source merit order or critical-load priority is
actually consumed. A scenario may change a policy at an effective time but
does not own its baseline. Keep `ControlAssumption` prose-only. If minimum
runtime needs a typed duration property, define that carrier in the controller
slice; do not loosen the existing scenario `DURATION_UNIT_SPELLINGS` ban.

This slice unlocks measured/derived Service and Dispatch views. It still needs
product-side feasibility checks before labeling runtime **Candidate avoidable**.
A fuel-only profile can prove consumption and observations, not that PV/BESS
could have supplied the same service.

### 3.5 Transform truth into separate reported observations

Bindings use `(StateRef, device_id, signal_id)`. The fuel source samples at the
frozen cadence; during the reporting gap there is no fresh sample. Carry an old
reading only if a declared stale-reporting transform does so and labels it.
Do not interpolate a convincing-looking product trace through the gap.

An operator hand dip is a separate generated operational observation with its
non-device source, tank, occurrence time, value and declared error behaviour.
It is not a scenario timeline number copied into evidence. A fuel delivery's
physical addition and the human delivery report are also different events:
the addition can happen even when its record is delayed, wrong or absent.

Lab may show private tank level beside the reported level. A separate future
Sensor Bias recipe can demonstrate 274 L truth versus 289 L reported. Keep
the current Fuel Loss recipe free of sensor bias as T022 requires; use its
reporting gap to demonstrate imperfect evidence first.

### 3.6 Gateway: make the crossing inspectable

The gateway transforms supported observations into canonical source envelopes.
The envelope carries Site/source/gateway/device identity as applicable,
schema/message and sequence identity, source time, gateway publication time,
mapping/configuration identity/version, quality/transport metadata and allowed
simulation provenance. Exactly one strictly allowlisted typed record carries
the observation's measurement or occurrence semantics. Preserve source time
through buffering or delayed publication. Ingestion alone later adds
`received_at`.

The first T023 allowlist is deliberately small: fuel-level `Telemetry` and
`OperationalRecord` subtype `fuel.manual_dip`. No generic `{type, payload}`
escape hatch. No authored removal, private expectation, truth trace or cause
description may enter normal payload/provenance. Opaque run/scenario version
references are provenance, not permission to dereference private causes in
analytics.

T023 does **not** publish generator energy, `fuel.delivery`, command events,
maintenance records or policy-change evidence. Add each strict record/binding
with the product slice that consumes it. A delivery needs a reportable delivery
observation first. A private generator flow needs a modeled meter first.

Staging persists canonical output without changing the operator Site. Inspect
raw output shows the same validated content as the summary. Re-staging an
identical message is idempotent; the same identity with different content is a
conflict. T023 stages completed Drafts; do not imply paused-run staging exists
because the canonical product also describes later paused Commit eligibility.

### 3.7 Commit, ingestion and accepted Site history

Commit seals eligible staged envelopes and persists an immutable release
artifact/manifest. It then releases those artifacts through normal ingestion.
Commit never writes Evidence, Site history, Findings or financial objects.
Lifecycle (Draft/Committed), execution status and ingestion outcome remain
separate dimensions; a completed or committed run does not imply every record
was accepted.

Block ambiguous committed overlap for the same Site/time interval. Keep
successive non-overlapping runs under the same stable Site identity. For the
first end-to-end path, complete the Draft, stage, Commit and ingest
synchronously. Paused Commit, when added, must explicitly seal the eligible
covered interval and partial completeness; it must not claim the unexecuted
remainder. Reset affects Draft runtime/staging only; committed artifacts never
change and rerunning allocates a new run ID.

Ingestion validates envelope and record contracts, resolves Site/source and
mapping/configuration context, normalizes units, handles duplicate/conflicting
identities, assesses source quality and records acceptance or rejection with
its own receipt time. It persists accepted evidence separately from rejected
attempts. The first rejection demonstration should use a valid released
record whose mapping cannot be resolved at ingestion, or another explicitly
specified ingest-boundary failure. A staging parser refusal is not an
ingestion rejection; do not bypass T023 validation merely to populate a log.

Now operator Site + selected time window can show fuel readings and hand dips,
gaps and provenance. They remain observations, not yet a reconciliation.
Rebuilding this view must require only persisted canonical envelopes,
referenced configuration/mapping and the ingestion/product pipeline, with no
runtime, `WorldState`, `LabProjection` or raw `DeviceObservation` access.

Replay is recorded Site history as of `t`: evidence appears no earlier than
its ingestion `received_at`; late records do not appear retroactively at source
time. Derived/managed objects honor their own creation/change times and
configuration validity. Replay does not re-run physics or silently recompute
old analysis. Accelerated simulation may create many records received together
at Commit: show that honestly. Distinct receipt instants for a delayed-record
demonstration must come from controlled ingestion/release, never invented
simulator receipts.

### 3.8 AssetOps derives a claim, rather than receiving the answer

Before reconciliation, extend the source path to supply accepted generator
energy/runtime observations and reportable delivery records. Show their
coverage and configured meaning. The scenario's private 40 kW forcing and
80 L removal are never analytical inputs.

| Transformation | Product owner / output | Kobo result and claim ceiling |
| --- | --- | --- |
| Accepted messages → usable evidence | Ingestion/evidence: normalized observations, quality, timestamps and lineage. | Opening/closing levels, dip, energy and delivery records; gaps remain visible. |
| Evidence → capability readiness | Evidence sufficiency rules and `CapabilityEvidenceStatus`. | Fuel reconciliation is Full/Limited/None/N/A according to required records, coverage and uncertainty; “no record” is not a verified zero. |
| Generator observations → runtime/energy window | Product runtime assessment; later `DispatchInterval` for coupled feasibility. | Supports consumption estimation. It cannot infer avoidability from the fuel-only model. |
| Levels + deliveries + expected consumption → `FuelBalanceWindow` | Product fuel reconciliation with configuration-at-time and a versioned calculation. | An unexplained residual with uncertainty, not a declaration of the hidden cause. |
| Material supported residual → Finding | Product Findings: bounded claim, severity, confidence, alternatives, evidence refs and recommendation. | “Fuel movement is not fully explained by recorded delivery and expected use.” Not theft. |
| Finding/quantity + BusinessContext → financial consequence | Downstream financial bridge. | Bounded fuel-value exposure, with model/scenario basis, not guaranteed recoverable savings. |

For the illustrative error-free observations:

```text
expected generator use = accepted energy × configured specific consumption
                       = 160 kWh × 0.35 L/kWh = 56 L

unexplained residual = opening + recorded deliveries − expected use − closing
                     = 430 + 50 − 56 − 344 = 80 L
```

The planner must settle the product expectation basis at the existing
T034–T038 checkpoint: either a suitable time-valid Foundation coefficient or
a separately declared operating assumption. This example recommends the
Foundation coefficient for the narrow first calculation, visibly labelled
modelled, with its suitability and uncertainty declared. It does not authorize
reading the simulator's private consumption. Freeze/reference the selected
analytical basis and algorithm version on the derived object.

An illustrative conservative error budget makes the example reviewable:
opening/closing ±2 L each, delivery ±2 L, energy ±2 kWh and coefficient
0.33–0.37 L/kWh imply expected use 52.14–59.94 L and residual
**70.06–89.86 L**. These are authored example error bounds, not statistical
confidence intervals, field calibration or acceptance thresholds. The real
slice must derive its uncertainty from declared measurement/model errors and
review materiality before promoting a Finding. Do not select a threshold just
to guarantee that this recipe triggers.

If the delivery report is missing, its contribution is unknown: suppress the
complete balance or present a specifically bounded partial result. If energy
coverage is insufficient, expected consumption is unavailable. If the hand dip
is missing, remove its corroboration; a sufficient sensor-based balance may
remain, with the claim/confidence adjusted by the declared rule. If the sensor
and hand dip disagree, expose alternatives such as calibration or timing
error; do not consult truth to choose the explanation. This contrast is a
central demo feature: the same physical loss can support different conclusions.

For a **synthetic** price assumption of 1.20–1.40 currency units/L in a
versioned BusinessContext, that residual range corresponds to approximately
84–126 currency units of modelled fuel-value exposure for this window. The
screen must link quantity, uncertainty, currency, price basis and time scope.
No annual extrapolation by default, no assertion of theft, and no addition of
this exposure to an overlapping “avoidable fuel” line. Changing only price
changes the economic result, not physics, envelopes or the technical finding.

### 3.9 Continue from a Finding to intervention and verification

A Recommendation names what to do and how success will be judged. Acceptance
creates a managed Action with owner, due date, source Finding, target metric,
guardrails and verification window. A field task can become a maintenance work
request; building a full CMMS is unnecessary.

For Kobo's unexplained fuel gap, the first sensible response may be better
delivery/hand-dip evidence and an inspection, rather than asserting a repair
for an unproven cause. A follow-on recipe can model effective maintenance and
an ineffective look-alike. Both record work completion, but only one changes
the physical or reporting process. Run-scoped interventions are immutable,
canonically serialized content-addressed artifacts persisted before execution;
arbitrary labels in `intervention_history` are insufficient. Scenario-authored
changes remain frozen with their scenario version.

Subsequent non-overlapping committed windows supply new evidence through the
same path. Product `VerificationOutcome` compares the declared target and
guardrails, coverage, configuration, confounders and recurrence. Example
criterion for review: the residual returns within the declared uncertainty/
materiality band for a complete comparable post-window, with required delivery
and energy coverage. For a dispatch intervention also require no increase in
reserve breaches or unserved critical load.

“Completed” proves activity. During the observation window the UI may show
provisional progress; final Verified/Ineffective/Inconclusive follows the closed
window and its rule. An ineffective or evidence-poor response keeps or reopens
the Finding. Never let a maintenance record, simulator intervention result or
private success expectation close it directly.

### 3.10 Productive use, stress and controlled comparisons

Once coupled dispatch/service evidence exists, Renewable can identify
time-bounded renewable headroom after demand, reserve, storage, power and policy
constraints. Productive use then asks whether a scheduled load could consume
that headroom without harming service. For example, an added 12 kW mill from
10:00–15:00 requests 60 kWh; the model must compute what is actually served.
Do not quote 60 kWh of saleable output merely from the authored schedule.

Use v4 `PairedExperiment` for the baseline/intervention experiment. It is
immutable once both run identities freeze and is outside either deterministic
identity. Compare resolved effective frozen initialization by `StateRef`,
component/Site Controls, forcings, observation bindings, mappings, topology,
publication cadence, seed/RNG, numeric/model/kernel/contract versions and
ordered intervention artifacts. Remove only the exact declared allowed delta
path/artifact from equality; any unrelated difference yields `NOT_COMPARABLE`.
Foundation/scenario version labels remain provenance, not the proof grain.

Do not solve overlapping histories by quietly accepting both runs. Initially,
an overlapping pair can remain staged and be inspected privately in Lab; no
product financial or Finding comparison may derive from that staged output.
To show accepted evidence for both counterfactual worlds, a later comparison
slice must explicitly admit separate declared scenario-clone Sites with
equivalent effective input mappings and visible provenance, or a reviewed
history-selection contract. Run creation itself must never allocate those
Sites. Until that boundary is specified, defer the operator paired comparison.
Sequential before/after verification from §3.9 still ships without it and does
not claim all-else-equal causality. Use “simulated intervention comparison” for
the paired result, never “proven real-world causal impact”.

For asset value, the simulator can accumulate causal stress from temperature,
throughput, high C-rate or deep discharge. AssetOps separately derives a
`BatteryStressWindow` from accepted battery/temperature/energy observations,
configuration and declared analysis rules. Private accumulated stress is a
test oracle, not an asset-health feed. Unknown initial history limits cumulative
claims; a declared synthetic new asset may explicitly start at zero. Show
observed stress and uncertain capacity, not exact remaining life or an invented
replacement date. A replacement-value assumption belongs in BusinessContext;
it is exposure context, not a physical rating or automatic depreciation claim.

## 4. Screen outcomes and client narrative

Canonical screen references below are sections in the
[Product Experience and Canonical Screens v6.9](Product/AssetOps_Integrated_Product_Experience_and_Canonical_Screens_v6_9.pdf).
They define destination and content discipline, not a requirement to implement
every mocked panel before the first demonstration.

| Surface | What the user sees / where it comes from | First useful landing |
| --- | --- | --- |
| Sites (8.2), Foundation (8.10) | Stable Kobo identity, SIMULATED provenance, configured assets/topology/devices and time-valid properties. Later readiness/last-analysis values only when derived. | Existing substrate; T020A property/addressing proof. |
| Lab Site View, Devices, Gateway (8.12–8.13) | Private fuel trajectory, distinct generated reports, visible gaps, staged/raw envelopes and later ingestion acknowledgement. No Findings or confidence presented as simulator output. | T022, T023, then release/ingestion. |
| Scenarios and Runs (8.14–8.15) | Authored causes versus private expectations; frozen inputs; lifecycle/execution; Stage/Commit eligibility and explicit refusals. | Existing setup plus T020B–T026. |
| Site Overview (8.18) | At v1, supported accepted readings, window/coverage and unavailable analytics. Later a concise fuel issue and linked Finding; do not aggregate “Healthy” from silence. | Evidence views, then conclusion chain. |
| Site Health (8.19) | Physical condition separate from instrumentation/source health. Online/Stale/Offline and quality derive from receipts/cadence, not asset assessment. | Source-health analysis; physical condition later. |
| Performance: Fuel (8.22) | Opening/delivery/expected-use/closing bridge, residual range, evidence gaps and alternatives from `FuelBalanceWindow`. | First analytical chain. |
| Performance: Dispatch and Service (8.21, 8.20) | Necessary/Candidate avoidable/Indeterminate intervals; served/unserved energy and critical-load evidence from `DispatchInterval` / `ServiceWindow`. | Coupled world + observability + product feasibility rules. |
| Performance: Renewable and Backup (8.23–8.24) | Feasible headroom/opportunity; later `BackupEventChain` with missing links explicit. No asserted switching state from a configured diagram. | Renewable after dispatch; full backup chain deferred until event/topology evidence supports it. |
| Site Evidence (8.35), claim drawer (8.37) | Capability claim ceilings and next-best evidence; exact raw/normalized refs, quality, coverage, configuration-at-time and mapping/analysis versions. | Provenance at v1; claim-specific derivation links at v2. |
| Site Findings / Finding detail (8.25, 8.32) | One canonical bounded Finding; Overview separates observation, inference, consequence, confidence and boundary; Evidence, Alternatives and Recommendation drill deeper. | Conclusion chain. Site index is a filtered view of the same global objects, no second status model or KPI strip. |
| Site Financials (8.36) | Technical quantity × explicit business assumptions, basis, uncertainty and non-overlap; click through to source Finding. No independent health assessment. | Financial bridge after the first quantity-backed Finding. |
| Work / Action / Maintenance verification (8.26, 8.38, 8.34) | Owner, due, source, criterion, completed activity, observed outcome and target/guardrail comparison. | One intervention/verification slice family; incidents and broad work queues can wait. |
| Battery Health (8.27) | Evidence-derived stress, reserve/temperature/throughput context and unverified capacity. | Stress extension after metered dispatch/service. |
| Replay (8.16) | Site + selected window as of receipt/creation time; same accepted history across tabs, no future evidence. | Demo Ready v1. |
| Truth comparison (8.17) | Restricted read-only comparison with the same private truth used in Lab. | Optional later admin surface; never needed to substantiate the operator claim. |
| Portfolio (8.1) and global roll-ups | Ranked real Findings with Site links and evidence/financial basis, aggregating independent histories. | After one complete Site story; no fake 20–50-site counts. |

Maintain the existing operator/Lab split, route gate and shared presentation
substrate. Lab enriches named extension slots; it does not fork the Site read
model. Keep canonical entity tabs truthful, hide deferred actions/navigation
and disable built actions only with a real eligibility reason. Clicking a
Finding or Action changes the root object while retaining Site context.

Use this client sequence once the relevant capabilities exist:

1. **Where should we look?** Open Sites → Kobo; show its operating question and
   selected window. Start at Portfolio only when real roll-up content exists.
2. **What is the concern?** Open Fuel and its bounded unexplained residual.
   Show a quantity/uncertainty first, then the economic bridge if implemented.
3. **Why believe it?** Open the Finding's evidence drawer: tank samples, hand
   dip, energy, delivery and configuration basis. Show the reporting gap.
4. **What would change our mind?** Show a separately identified missing-record
   example whose claim weakens or becomes unavailable. Do not blend overlapping
   recipe runs into Kobo's canonical history.
5. **What happened after the response?** Show the Action's completed activity,
   post-window evidence and verification result, including an ineffective or
   inconclusive case. Completion alone never resolves the issue.
6. **What comes next?** If built, show dispatch/service guardrails, then renewable
   opportunity and stress. Otherwise describe them explicitly as next slices.

Keep the operator experience central. Use Lab afterward, or briefly for a
technical reviewer, to show how the evidence was generated. End with the
practical next step: identify one real Site's available telemetry and records
to test this same evidence contract. Do not imply a real importer is already built.

## 5. Reviewable delivery slices

The table groups work by observable outcome; each row is a delivery slice
family, not an instruction to bundle a programme into one task. Preserve
existing task identities and their acceptance checks. The Planner sizes the
named cuts; proposed followers beyond the written queue need task definitions
when their block becomes active. No calendar estimate is implied.

| Slice / sequence | Data and transformation to build | Human review and decisive acceptance |
| --- | --- | --- |
| **A. Trust the frozen setup** — T020A then T020B | Property carrier, model-rule answers, component-addressed bindings/frozen inputs, v4 timing declarations and first shipped `READY` path. Natural cuts: property representation → address resolution; Site Controls later. | Inspect Foundation property and frozen origin; ambiguous two-tank binding blocks; shipped scenario reaches `READY` with unsupported optional states disclosed. No apparent execution. |
| **B. Watch a cause become a reading** — T021 → T021A → T022 | Minimal causal fuel kernel/conformance, parser narrowing in its existing position, Lab execution and distinct cadence-driven device/hand observations. Neutral host composes execution. | Run/step/pause/reset the shipped recipe; removal changes the trajectory, a gap changes observations only; boundary stock sample includes due event; no operator history changes. Preserve T021 authored-cause and T022 UI checkpoints. |
| **C. Inspect exactly what could be ingested** — T023 | Strict neutral source envelope, fuel telemetry + dip, immutable/idempotent staging and raw inspection. | Reopen staged artifacts and inspect source/publication time and mapping; no receipt time or accepted evidence; a conflicting message writes nothing. Review envelope/record language. |
| **D. Release into normal evidence** — T024–T026 feature-map range | Commit eligibility/sealed manifest/overlap guard, normal ingestion validation/mapping/receipts, accepted store and rejection logs. Cut release and ingestion/log visibility into reviewable tasks. | Commit once; see accepted records and an ingest-boundary rejection with reasons; retry creates no duplicate history; overlapping canonical contribution is refused. Evidence store is populated only by ingestion. |
| **E. Make the Site history inspectable** — T027–T029 range | Accepted-evidence read model → Site/window views → provenance drawer → Replay. | Two non-overlapping runs appear under one Site; changed window changes all relevant tabs; late records stay absent before receipt. Gate off Lab and rebuild from persisted envelopes. This completes Demo Ready v1. |
| **F. Explain one operating problem** — T034–T038 conclusion family, programme-order proposal noted in §2 | First add reportable generator energy/runtime and delivery observations through the existing source path. Then source health/readiness → runtime basis → uncertain fuel balance → bounded Finding/drawer. | Fuel bridge can be followed to accepted records and Foundation; missing required evidence prevents a complete claim; healthy/look-alike case does not trigger the same claim. Review expectation basis, uncertainty/materiality and promotion before shipping it. |
| **G. Explain the economic stake** — proposed follower | One versioned BusinessContext and one quantity-backed financial line with source Finding and assumption references. | Change price only: financial line changes, trajectory/envelopes/technical claim do not. Remove the technical basis: no money appears. No overlapping sum. |
| **H. Close one intervention loop** — proposed follower | Recommendation with criterion → Action/optional work record → modeled intervention → new committed post-window → verification. Cut managed activity from outcome calculation if needed. | Work completion leaves the Finding open/awaiting verification. Effective, ineffective and missing-evidence post-windows produce the appropriate bounded outcomes. Sequential windows suffice; pairing is not a prerequisite. |
| **I. Show electrical consequences** — proposed follower | Typed Site Controls + controller/physical resolver + PV/BESS/load observations → Dispatch/Service views and supported runtime opportunity. Separate balance/service from candidate-avoidability analysis. | A request exceeds a limit and the meter reports accepted power; sources/sinks balance; clinic service can worsen under a bad policy; missing policy/alternative-source evidence yields Indeterminate. |
| **J. Show opportunity and asset pressure** — later, independently reviewable followers | Renewable feasibility then productive-load experiment/comparison; separately battery stress observations → asset analysis. | Mill energy reflects accepted service and guardrails; paired proof rejects unrelated effective-input changes; stress never imports private accumulator or claims precise life. |

F does not wait for the full electrical world: fuel reconciliation needs
observed generator output/energy and records, not optimized dispatch. I is
required before describing runtime as avoidable or claiming a productive-use
opportunity. H can use the fuel record/maintenance story to demonstrate
verification before I. This is how the programme reaches visible value early.

Keep the first stories small: healthy fuel control, a loss with a reporting gap,
then missing-record/contradictory-evidence variants. After that, add one policy
change with a service trade-off, one productive load and one stress exposure.
Full backup failure chains, many-site generation, cold-chain and e-mobility
are followers. The shared kernel must not branch on pack/site kind; new packs
reuse time, observation, gateway and ingestion contracts rather than triggering
a generalization project before this path works.

### Evidence required to call a slice done

A review packet should contain the actual screen interaction plus the smallest
artifact/automated proof that protects the new boundary. For this programme:

- A/B: resolved-address ambiguity, exact arithmetic, event/window/end-boundary
  tests, causal removal/retiming tests and kernel/profile conformance. Preserve
  existing execution-contract version movement and frozen-run compatibility.
- C/D: strict payload/privacy checks, canonical artifact reload, idempotence,
  Commit eligibility/overlap, rejection and receipt ownership. UI success alone
  cannot prove these boundaries.
- E/F: reconstruct product output without simulator objects; hold envelopes
  fixed while changing/removing private truth and get the same product result;
  missing-record/coverage and Replay as-of checks. Derived lineage reaches raw
  evidence, configuration and the recorded analysis version.
- G/H: price-only change, non-overlap of economic consequences, completed work
  without closure, effective/ineffective/inconclusive verification windows.
- I/J: requested versus accepted flows, conservation, service guardrails,
  independent stochastic streams when used, and rejection of undeclared
  resolved-input differences even behind changed version identifiers.

Run the existing architecture and workflow guards with each implementing
slice and relevant backend/frontend checks. Extend guards where v4 introduces
new seams: neutral host is a composition leaf, kernel cannot import packs and
shared observation/gateway mechanisms contain no domain dispatch branches.
Do not weaken guards or add a broad framework merely to satisfy a layout.

The next implementation action is the v4-required **T020A sizing pass**, then
the existing queue through the evidence loop. The next programme decision is
the explicit mini-grid conclusion-chain placement after T029. Neither requires
reopening policy ownership, timing, numeric policy, the source boundary or
counterfactual proof grain: v4 has already settled them.

## 6. Source basis and handoff

Read this companion for demo sequence and slice outcomes; read v4 for normative
simulator mechanics. The following sources anchor the interpretations above:

- [Simulator design v4](simulator_design_v4.md), especially §§2–15, 17 and
  21–25: binding contracts, boundary cycle, component addressing, observation/
  gateway, intervention, comparison and build alignment.
- [Canonical product/screens v6.9](Product/AssetOps_Integrated_Product_Experience_and_Canonical_Screens_v6_9.pdf),
  §§2–6, 8 and 9–10: product objects, navigation, source/Commit boundary,
  Site/window/Replay, screen outcomes and claim discipline.
- [Product](../.ai/PRODUCT.md), [Architecture](../.ai/ARCHITECTURE.md),
  [Project Rules](../.ai/PROJECT_RULES.md),
  [Active Context](../.ai/ACTIVE_CONTEXT.md) and
  [Feature Map](../.ai/FEATURE_MAP.md), particularly Client-Demo Roadmap and
  the four Early Feature sections from Draft Runtime through First Conclusion.
- [Current multi-vertical build plan](multi-vertical-build-plan.md): useful
  evidence-loop-first programme intent; simulator details are superseded by
  v4 where listed in §2, and slice/calendar estimates are not commitments here.
- [Planner handoff](../.ai/PLANNING_HANDOFF_T019_T022.md) and
  [Decisions](../.ai/DECISIONS.md): physical-property ownership, coefficient unit,
  forcing semantics, reconciliation retirement and milestone speed guidance.
- Written queue: [T020A](../tasks/T020A-foundation-physical-properties.md),
  [T020B](../tasks/T020B-execution-contract-alignment.md),
  [T021](../tasks/T021-minimal-fuel-loss-causal-kernel.md),
  [T021A](../tasks/T021A-reported-observation-requirement-closure.md),
  [T022](../tasks/T022-lab-execution-and-device-observation.md),
  [T023](../tasks/T023-staged-source-envelopes.md).
- Existing code contracts:
  [scenario execution](../backend/assetops_backend/scenarios/execution.py),
  [run models](../backend/assetops_backend/runs/models.py),
  [profiles](../backend/assetops_backend/runs/profiles.py),
  [frozen-input provenance](../backend/assetops_backend/runs/provenance.py),
  [dependency guard](../tools/checks/dependency-direction.ps1) and
  [simulator scaffold](../simulator/assetops_simulator/__init__.py).
  Envelope/ingestion/evidence contracts beyond T023 are planned contracts,
  not existing implementations to import.
