# AssetOps Mini-Grid Demo Architecture and Roadmap

**Architecture basis:** `Docs/simulator_design_v4.md`  
**Scope:** mini-grid demo path from simulated physical world to client-facing AssetOps experience

This document is an execution and product-demonstration companion to
`Docs/simulator_design_v4.md`. It does not redefine the simulator architecture.
Where this document summarizes a simulator mechanism, v4 remains normative.

---

# 1. Executive intent

The first mini-grid demo should prove one thing clearly:

> **AssetOps can reconstruct meaningful operating behaviour from ordinary site evidence, translate that behaviour into bounded operational and economic consequence, and show whether an intervention improved the outcome.**

The demo should leave a portfolio operator with four impressions:

1. **AssetOps identifies where operations are costing money or degrading service.**
2. **Its conclusions are evidence-backed rather than opaque scores.**
3. **It can distinguish an operating problem from missing or insufficient evidence.**
4. **It closes the loop from finding -> intervention -> verification.**

A useful first demo is not a complete mini-grid management platform. It does not need:

- full power-system simulation;
- predictive remaining useful life;
- generalized optimization;
- a full CMMS;
- exhaustive scenario authoring;
- sophisticated portfolio administration;
- cold-chain or e-mobility implementation;
- perfect UI polish.

The first mini-grid experience should instead make one operating story feel real enough that a practitioner can challenge it.

A representative story is:

```text
Kobo Mini-grid

PV + BESS + diesel generator
        |
generator remains online after support need appears to end
        |
AssetOps reconstructs the interval from inverter, BMS,
generator and meter evidence
        |
3.4 h classified as Candidate Avoidable
        |
bounded fuel + maintenance consequence
        |
operator changes control policy
        |
site is simulated again through the normal evidence path
        |
AssetOps measures whether runtime fell without harming
reserve discipline or service
```

The simulator architecture matters because it makes this demonstration credible. The most important v4 protections are:

- private simulator truth cannot enter product analytics;
- the canonical source envelope is the only simulator-to-product crossing;
- controller intent and physical acceptance are different objects;
- repeated assets are component-addressed;
- simulator events change the world, not Findings;
- paired comparisons are checked from resolved frozen inputs;
- financial interpretation stays downstream of physical evidence.

These are the seams worth protecting. Most other choices should remain pragmatic until the demo or a second vertical actually needs more.

---

# 2. How v4 maps to the demo

Not every capability described in `simulator_design_v4.md` must be implemented before useful feedback is possible.

| v4 capability | Why it exists | Demo value | Priority |
|---|---|---|---|
| Causal world model | Consequences arise from declared causes | Lets the demo withstand "what caused this?" | REQUIRED NOW |
| Component-addressed state | Distinguishes repeated loads/assets | Supports residential, clinic and productive loads on one site | REQUIRED NOW |
| Controller intent vs accepted flow | Separates requested behaviour from physical capability | Explains why a dispatch decision may differ from actual battery/generator response | REQUIRED NOW |
| Boundary timing | Makes cause, state and telemetry ordering unambiguous | Needed for defensible event reconstruction | REQUIRED NOW |
| Observation transform | Separates physical truth from reported measurements | Enables evidence quality, sensor bias and missing-data demonstrations | REQUIRED NOW |
| Simulated gateway | Reproduces the real reporting boundary | Makes the source-envelope claim credible | REQUIRED NOW |
| Staging + Commit | Prevents draft simulator output from becoming product history | Supports a clean Simulator Lab -> AssetOps handoff | REQUIRED NOW |
| Normal ingestion | Keeps simulated and live sites on the same product path | Critical credibility point | REQUIRED NOW |
| Operational records | Allows delivery/dip/override records to differ from telemetry | Required for fuel reconciliation | REQUIRED FOR CLIENT DEMO |
| Asset stress | Creates slow-burn degradation trajectories | Required for lifecycle story, not first valuable finding | DEMO USEFUL |
| Intervention model | Changes the physical/configured world without manipulating Findings | Required for closed-loop demo | REQUIRED FOR CLIENT DEMO |
| PairedExperiment | Proves controlled before/after simulator comparisons | Strong for what-if and intervention comparison | DEMO USEFUL |
| BusinessContext | Converts operational quantities into bounded money | Makes product economically legible | REQUIRED FOR CLIENT DEMO |
| Private truth comparison | Validates AssetOps inference without feeding it | Strong technical proof at end of demo | DEMO USEFUL |
| Generic second-vertical pack framework | Allows cold-chain/e-mobility later | Protects seam, but no need to fully implement now | DEFER IMPLEMENTATION |

The first useful vertical slice does **not** require fuel reconciliation, battery degradation, portfolio recipes or paired intervention comparison.

The minimum path is:

```text
simulated site
    ->
physical operation
    ->
device observations
    ->
canonical source envelopes
    ->
normal ingestion
    ->
one evidence-backed dispatch conclusion
    ->
one useful screen
```

That should be the first visible milestone.

---

# 3. End-to-end technical walkthrough - mini-grid

## 3.1 Representative site

Use one canonical site for the first end-to-end build:

**Kobo Mini-grid**

```text
Generation / storage
- PV-001 / INV-001
- BAT-001 / PCS-001
- GEN-001
- TANK-001

Loads
- LOAD-RES      residential demand
- LOAD-CLINIC   critical clinic demand
- LOAD-MILL     productive load

Control
- battery reserve
- generator start/stop policy
- minimum generator runtime
- source priority

Evidence
- site load meter
- inverter power
- BMS SOC / battery power
- generator status / power
- fuel-level sensor
- operational fuel-delivery / operator-hand-dip records
```

The site is deliberately small enough to understand in one screen but rich enough to support the main AssetOps stories.

---

## 3.2 Normal operation

Normal operation is not filler. It is the reference against which abnormal behaviour becomes credible.

### World

Inputs for a representative daytime interval:

```text
irradiance             -> PV potential
residential profile    -> LOAD-RES demand
clinic profile         -> LOAD-CLINIC demand
mill schedule          -> LOAD-MILL demand
battery SOC            -> available storage state
effective control policy
```

At simulation boundary `T`:

1. events/configuration changes due at `T` are applied;
2. state observations at `T` represent post-event state;
3. controller receives its declared local view;
4. controller emits `ControlIntent`;
5. physical resolver applies component limits and site topology;
6. accepted power flows evolve the world;
7. device observations are sampled according to their reporting profiles;
8. the simulated gateway stages canonical source envelopes.

Example:

```text
PV potential                45 kW
site demand                 31 kW
battery SOC                 63%
generator                   stopped

ControlIntent:
PV limit                    45 kW
battery requested charge    12 kW
generator request           stopped

AcceptedFlowSet:
pv_to_load                  31 kW
pv_to_battery               12 kW
curtailed_pv                 2 kW
generator_to_load            0 kW
unserved_load                0 kW
```

### Observation path

The product never sees the resolver result directly.

It may receive:

```text
INV-001 ac_power      42.8 kW
METER-001 load        30.9 kW
BMS-001 soc           63.1%
BMS-001 power        -11.7 kW
GEN-001 output         0.0 kW
```

Those readings may differ slightly from private truth because of reporting cadence, bias, noise, delay or quantization.

The gateway converts them into canonical envelopes carrying at least:

```text
site identity
source/device identity
signal/mapping identity
source_time
gateway_time
value / unit
quality
sequence/message identity
mapping version
```

Draft run output remains staged.

On Commit:

```text
staged source envelopes
        ->
sealed committed envelopes
        ->
normal AssetOps ingestion
        ->
accepted Evidence / Site history
```

### Product outcome

The site can show:

- served energy;
- renewable contribution;
- battery state;
- generator runtime;
- data coverage;
- no material current finding.

This provides the "healthy reference" necessary for later findings to mean something.

---

# 3.3 Candidate avoidable generator runtime

This should be the first substantial AssetOps finding because it demonstrates the full proposition with relatively little domain machinery.

## World cause

Suppose the generator starts legitimately during an earlier support interval, but a stop-policy condition keeps it running after PV and battery capability recover.

The simulator authors the cause, not the conclusion:

```text
effective generator stop policy
+
PV recovery
+
battery SOC/capability
+
load demand
```

No scenario field says "avoidable runtime".

## Controller and physical world

Example interval:

```text
14:20-16:50

load                         31-39 kW
PV available                 sufficient for part of load
battery SOC                  74% -> 58%
battery discharge capability 22 kW observed for most of interval
generator                    remains running
```

The controller may continue requesting generator operation because of the current stop policy.

The physical resolver then produces accepted flows such as:

```text
pv_to_load
battery_to_load
generator_to_load
generator_to_battery
curtailed_pv
unserved_load
```

The simulator does not label any of these "waste".

## Device evidence

Relevant source envelopes come from:

- PV inverter;
- BMS;
- load meter;
- generator controller;
- configuration/policy record;
- optional operator-commanded override record.

AssetOps sees what a real installation might expose, including gaps.

Example:

```text
PCS discharge-limit evidence missing for 13 minutes.
No operator-commanded override record observed.
```

## Product transformation

Normal ingestion produces accepted evidence.

The dispatch analytic reconstructs a `DispatchInterval` from evidence and policy.

Conceptually:

```text
generator ON
+
observed load
+
PV capability
+
battery SOC / discharge capability
+
effective reserve policy
+
controller / override evidence
        ->
constraint evaluation
        ->
Necessary | Candidate Avoidable | Indeterminate
```

If capability evidence is sufficient but not perfect:

```text
Candidate Avoidable
confidence: High
coverage: 94%
claim boundary:
PCS discharge limit missing for 13 min
```

The classification is deliberately not "generator waste".

## Financial bridge

The physical finding supplies a bounded operational quantity:

```text
candidate avoidable runtime
estimated associated fuel quantity
additional service/runtime accumulation
```

`BusinessContext` supplies:

```text
fuel price
generator maintenance basis
other approved operating-cost assumptions
```

The result may be:

```text
candidate fuel consequence       34-42 L
candidate daily value            $184-$226
basis                            modelled
```

The financial layer does not strengthen the technical claim.

## Screens

This one story feeds:

- Mini-grid Site Overview;
- Performance -> Dispatch;
- Finding Detail;
- Evidence drawer;
- Site Financials;
- Portfolio Value & Operations.

This is the first complete demo-quality vertical slice.

---

# 3.4 Fuel reconciliation discrepancy

Fuel reconciliation demonstrates a different strength: AssetOps can combine telemetry and operational records without overclaiming cause.

## World

Private world state may contain:

```text
opening tank level
generator consumption
fuel delivery
external unrecorded movement
sensor bias
```

Example private reality:

```text
opening true level      1,420 L
delivery                  +600 L
generator true use       -1,012 L
external adjustment         -54 L
closing true level          954 L
```

AssetOps must not receive the `external adjustment` truth.

## Evidence path

What AssetOps receives may instead be:

```text
opening tank sensor reading
fuel-delivery record
generator consumption evidence / model
closing tank sensor reading
optional operator-hand dip
```

One or more records may be delayed, missing or imperfect.

The product reconstructs:

```text
opening
+ deliveries
- expected generator use
- observed closing
= unexplained residual
```

Example:

```text
Residual: -54 L
Uncertainty: +/- 9 L
```

The correct conclusion is:

> **Material fuel movement is currently unexplained by the accepted records and expected generator consumption.**

Not:

> fuel theft.

## Product objects/screens

Feeds:

- Performance -> Fuel;
- Finding Detail;
- Evidence;
- Site Financials;
- Portfolio Value & Operations.

This story is important for a client demo because it shows the evidence discipline is not only academic: the system knows when not to make a stronger accusation.

---

# 3.5 Productive-use / renewable-headroom opportunity

This is where AssetOps stops being only a loss-detection system.

Use a site such as **Desta Mini-grid** that is technically healthy but commercially underutilized.

## Existing-world evidence

AssetOps observes:

```text
high service availability
healthy equipment
recurring daytime PV curtailment
low productive-load contribution
repeated renewable headroom
```

Example:

```text
productive-use demand vs operating case    -34%
PV curtailment                              340 kWh/month
recurring headroom                          17 kW average
primary window                              10:30-15:00
```

The base analytic should establish the physical opportunity without asserting local market demand.

A valid finding is:

> **Recurring renewable capacity is available during a predictable daytime window and could support additional load within the observed operating constraints.**

It should not conclude:

> A cold room will be commercially successful here.

## Intervention simulation

A paired experiment can add:

```text
LOAD-COLDROOM-02
rated load: 12 kW
window: 09:00-18:00
```

The pair comparison verifies all unrelated resolved inputs are identical.

Then:

```text
BASELINE                 INTERVENTION

energy sold   5.8 MWh -> 7.1 MWh
PV use          69%   -> 82%
curtailment     18%   -> 7%
diesel         284 L  -> 291 L
```

`BusinessContext` can provide an indicative tariff to show scenario revenue impact, clearly labelled as scenario-based.

## Product surface

The canonical Renewable screen supplies the operational basis.

A thin client-facing composition may add:

```text
Productive-use opportunity
        ->
Evaluate intervention
        ->
before / after scenario
```

This should be a composition over existing evidence + simulator comparison, not a new parallel analytics universe.

---

# 3.6 Battery stress / degradation trajectory

The first demo does not need precise remaining-life prediction.

It needs to show that operations can consume asset value before a failure occurs.

## World

The simulator tracks causal stress contributors, for example:

```text
energy throughput
depth-of-discharge exposure
high-SOC dwell
temperature exposure
high C-rate
```

These accumulate into domain-defined stress state.

For an existing synthetic asset, the initial stress state must be explicitly authored or unknown. It is never silently assumed to be zero.

## Product evidence

AssetOps may observe:

```text
SOC history
battery power
temperature
reserve violations
capacity evidence
alarms
```

From these it may establish:

```text
current SoH/state where evidence exists
trajectory
stress recurrence
comparison with expected/reference band
```

The product claim can remain:

> **Observed operation is accumulating battery stress faster than the configured/reference operating envelope.**

A later financial bridge can contextualize:

```text
replacement value
scenario replacement exposure
```

without claiming an exact replacement date unless evidence eventually supports it.

## Screens

- Battery Asset -> Health;
- Site Overview;
- Site Financials;
- Portfolio Value & Operations.

This story should come after the first dispatch and fuel stories because it requires more modelling and is less immediately verifiable.

---

# 3.7 Intervention and verification

The intervention loop differentiates AssetOps from a dashboard and from a conventional work-order system.

Use the dispatch finding.

## Before

```text
reserve policy           25%
candidate avoidable run  3.4 h/day
reserve breaches         5 / 7 days
```

## Intervention

A configuration change is applied to the simulated world:

```text
reserve policy 25% -> 32%
```

or:

```text
generator stop policy retuned
```

The intervention is frozen as immutable run input. It does not resolve the Finding.

## After

New physical operation is simulated.

New observations pass through:

```text
devices
-> gateway
-> source envelopes
-> Commit
-> normal ingestion
-> Evidence
```

AssetOps evaluates a comparable verification window.

Example:

```text
TARGET
candidate generator runtime    3.4 -> 1.1 h/day

GUARDRAILS
reserve breaches               5/7d -> 0/7d
unserved critical energy       stable
fuel use                       lower
battery high-power stress      acceptable
```

Only then may the workflow report:

```text
Verified
Ineffective
Inconclusive
Reopened
```

This is the clearest demonstration of AssetOps's closed-loop operating intelligence.

---

# 4. Major product screens and what feeds them

| Screen | User question | Main content | Primary inputs / derived objects | Demo role |
|---|---|---|---|---|
| Portfolio Value & Operations | Where should management act first? | priority sites, bounded OPEX/service/asset exposure, opportunities, evidence gaps | Site assessments, Findings, Site Financials, asset summaries | Opening client screen |
| Mini-grid Site Overview | Is this site fulfilling its operating objective and what matters now? | service, dispatch, battery, fuel, renewable, timeline, top findings | ServiceWindow, DispatchInterval, FuelBalanceWindow, battery evidence | Main site cockpit |
| Performance - Dispatch | Why did sources operate this way? | runtime, Necessary/Candidate Avoidable/Indeterminate, constraint evidence | generator, PV, battery, demand, controls | Hero technical story |
| Performance - Fuel | Does recorded fuel movement reconcile? | opening, delivery, expected use, closing, residual + uncertainty | tank evidence, deliveries, generator consumption | Accountability story |
| Performance - Renewable / Productive Use | Is renewable capacity being used economically? | renewable share, curtailment, headroom, opportunity windows | PV availability, demand, battery limits, dispatch | Growth/opportunity story |
| Finding Detail / Evidence | Why is AssetOps saying this? | bounded claim, facts, confidence, alternatives, evidence gaps, consequence | one canonical Finding + provenance | Trust-defining interaction |
| Site Financials | What does the technical behaviour mean economically? | OPEX, revenue/service, asset exposure, assumptions/basis | Findings + BusinessContext | Executive translation |
| Battery Asset Health | Is the battery merely healthy today, or on a harmful trajectory? | reserve stress, thermal exposure, trajectory, evidence limits | battery telemetry, stress analytic | Lifecycle story |
| Intervention / Verification | Did the change actually work? | target metric, guardrails, before/after, outcome | Action/Maintenance + post-action evidence | Closed-loop differentiator |
| Simulator Lab | Can we prove the product is inferring rather than reading scripted answers? | single-line world, device truth vs reported, gateway staging, run controls | private simulator state | Technical proof at end |

## Screen strategy

Most of the client demo should use the canonical product screens.

Only two thin compositions are worth adding early:

### Portfolio Value & Operations

The canonical Portfolio and Financials content should be presented together tightly enough that the opening question is economic/operational:

> Where is this portfolio losing value, carrying risk or leaving productive capacity unused?

This does not require a new object model.

### Productive-use intervention comparison

The canonical Renewable evidence can feed a simple:

```text
Evaluate intervention
```

experience that compares baseline and paired scenario.

Again, the comparison is a presentation over existing site evidence, simulator runs and financial assumptions, not a new source of truth.

---

# 5. Product-facing walkthrough

A strong client demonstration is approximately 12-15 minutes.

## 5.1 Portfolio - "Where should I look?"

**Presenter**

> "This is a six-site operating portfolio. AssetOps is not ranking sites by alarm count. It is showing where current operation is affecting cost, service, asset value or growth opportunity."

**Client sees**

```text
Kobo    avoidable generator runtime
Genda   fuel reconciliation gap
Bahir   unserved energy / backup issue
Desta   productive demand below case
Arsi    battery stress trajectory
Meki    within expected envelope
```

**Client should infer**

AssetOps is a decision layer over site operations, not another raw monitoring dashboard.

**Do not overclaim**

Do not add operating losses, revenue exposure and asset replacement exposure into one fake "total savings" number.

---

## 5.2 Kobo - "Why are we spending more diesel than necessary?"

Open Kobo.

Show:

- selected-day energy timeline;
- generator runtime;
- PV/BESS context;
- site policy;
- Candidate Avoidable interval.

Then open the Finding.

**Presenter**

> "AssetOps is not saying the generator should never have run. It is saying that for this interval the observed demand, PV, battery state and configured policy do not fully explain why it stayed online."

Open evidence.

**Client sees**

```text
PV available                       observed
battery SOC                        observed
battery capability                 94% coverage
load                               observed
operator-commanded override        none observed
claim boundary                     13 min capability gap
```

**Client should infer**

The conclusion can be challenged and traced.

---

## 5.3 Financial translation - "Does this matter?"

Show:

```text
candidate fuel quantity
runtime / maintenance consequence
bounded monthly extrapolation
basis + confidence
```

**Presenter**

> "The economic layer does not make the technical conclusion stronger. It simply translates the bounded operational quantity using your business assumptions."

This distinction is important for investor/operator credibility.

---

## 5.4 Desta - "Could the same portfolio earn/use more?"

Switch from loss to opportunity.

**Presenter**

> "This site is technically healthy. The issue is different: useful daytime generation is repeatedly unused."

Show:

```text
renewable headroom
productive-use share
curtailment
time window
```

Then:

> "Suppose you are considering an additional productive load."

Run the paired scenario.

Show before/after renewable utilization, energy sales, curtailment and diesel.

**Do not overclaim**

AssetOps can establish physical headroom. It cannot infer local customer demand, creditworthiness or commercial success unless those facts are separately provided.

---

## 5.5 Arsi - "What is becoming expensive before it fails?"

Show the battery.

**Presenter**

> "Nothing has failed. Availability is high. But repeated operating behaviour is accumulating battery stress unusually quickly."

Show state + trajectory + evidence limit.

This broadens the product from current OPEX to future asset value.

---

## 5.6 Intervention - "Can AssetOps tell whether we fixed it?"

Return to Kobo.

Apply or select a policy change.

Show:

```text
before
intervention
verification window
after
```

Target and guardrails appear together.

**Presenter**

> "A task being completed is not proof that the operating problem was solved."

This is an important distinction from a CMMS.

---

## 5.7 Simulator proof - "How do you know the analytics are not scripted?"

Only now open Simulator Lab.

Show:

```text
physical truth
reported sensor value
gateway output
committed envelopes
```

Then optionally compare private simulation truth to AssetOps inference.

**Presenter**

> "AssetOps never had access to this private truth. It received the same type of source evidence a live site would produce."

This is the technical credibility close.

---

# 6. Feature map

## 6.1 Core shared platform

| Capability | Priority | Why |
|---|---|---|
| simulation clock / boundary cycle | REQUIRED NOW | causal runtime |
| component topology | REQUIRED NOW | site composition |
| component-addressed state | REQUIRED NOW | multiple loads/assets |
| event/forcing handling | REQUIRED NOW | scenarios |
| ControlIntent | REQUIRED NOW | controller trace |
| physical resolver / AcceptedFlowSet | REQUIRED NOW | realistic dispatch |
| observation transform | REQUIRED NOW | evidence boundary |
| simulated gateway | REQUIRED NOW | live-equivalent source path |
| staging + Commit | REQUIRED NOW | clean Simulator Lab handoff |
| normal ingestion | REQUIRED NOW | product credibility |
| Evidence | REQUIRED NOW | analytics input |
| Findings | REQUIRED NOW | first product value |
| BusinessContext / financial bridge | REQUIRED FOR CLIENT DEMO | commercial value |
| Actions / Verification | REQUIRED FOR CLIENT DEMO | closed loop |
| paired experiment | DEMO USEFUL | intervention/productive-use comparisons |
| portfolio recipe | DEMO USEFUL | polished portfolio story |
| generalized pack plugin framework | DEFER | no second implementation yet |

## 6.2 Mini-grid domain

| Capability | Priority |
|---|---|
| PV potential/output | REQUIRED NOW |
| site load profiles | REQUIRED NOW |
| battery SOC + power limits | REQUIRED NOW |
| generator state + output | REQUIRED NOW |
| EMS/control policy | REQUIRED NOW |
| named energy flows | REQUIRED NOW |
| service/unserved load | REQUIRED NOW |
| fuel consumption | REQUIRED FOR CLIENT DEMO |
| tank inventory | REQUIRED FOR FUEL STORY |
| fuel delivery/dip records | REQUIRED FOR FUEL STORY |
| renewable curtailment/headroom | REQUIRED FOR OPPORTUNITY STORY |
| productive-load addition | DEMO USEFUL |
| battery stress | DEMO USEFUL |
| generator wear sophistication | DEFER |
| advanced battery electrochemistry | DEFER |

## 6.3 Demo-critical product capabilities

```text
Portfolio priority
Site Overview
Dispatch analytic
Finding + Evidence
Site Financials
Fuel reconciliation
Renewable/productive-use opportunity
Battery trajectory
Intervention verification
Simulator proof
```

Not all need to land before first domain feedback.

---

# 7. Demo roadmap

The roadmap is organized around what becomes visible, not around architectural nouns.

## Slice A - A simulated mini-grid behaves credibly

### Goal

Run one understandable mini-grid through the v4 causal runtime.

### Technical path

```text
site/topology
-> forcings
-> controller observation
-> ControlIntent
-> physical resolver
-> AcceptedFlowSet
-> state evolution
```

### Visible outcome

Simulator Lab can show:

- PV;
- load;
- battery SOC/power;
- generator;
- named flows;
- simulation clock.

### Review checkpoint

A human can change one forcing or policy input and see the physical consequence change coherently.

### Deferred

- AssetOps Finding;
- money;
- fuel reconciliation;
- portfolio.

---

## Slice B - The site crosses the real product boundary

### Goal

Prove the simulator ends where a real site begins.

### Technical path

```text
world
-> DeviceObservation
-> simulated gateway
-> staged canonical envelopes
-> Commit
-> normal ingestion
-> accepted Site history
```

### Product surface

Basic Site Overview populated from ingested evidence.

### Review checkpoint

The Site can be reconstructed entirely from committed source envelopes with no private simulator object.

### Earliest internal demo

**Here.**

This is the first meaningful architecture milestone.

---

## Slice C - First valuable AssetOps finding

### Goal

Detect candidate avoidable generator runtime.

### Technical path

```text
ingested PV + BMS + generator + meter + policy evidence
-> DispatchInterval
-> constraint evaluation
-> Candidate Avoidable
-> Finding
```

### Product surfaces

- Site Overview;
- Dispatch;
- Finding Detail / Evidence.

### Review checkpoint

A domain expert can answer:

> "Would this conclusion be useful, and what evidence would you require to trust it?"

### Earliest domain-expert feedback milestone

**Here.**

Do not wait for the full portfolio demo before talking to the former mini-grid colleague.

---

## Slice D - Translate operations into business consequence

### Goal

Make the first Finding economically legible.

### Technical path

```text
bounded runtime/fuel quantity
+
BusinessContext
->
bounded consequence
```

### Product surfaces

- Finding Detail;
- Site Financials;
- compact value on Site Overview.

### Review checkpoint

Technical quantity, business assumption, basis and confidence remain separately inspectable.

---

## Slice E - Fuel reconciliation

### Goal

Demonstrate multi-source evidence and restraint.

### Technical path

```text
tank readings
+ fuel-delivery record
+ generator consumption
+ closing evidence
-> FuelBalanceWindow
-> unexplained residual + uncertainty
```

### Product surfaces

- Performance -> Fuel;
- Finding Detail;
- Financials.

### Review checkpoint

Private fuel loss exists in the simulated world but AssetOps concludes only "unexplained residual".

---

## Slice F - Productive-use opportunity

### Goal

Show AssetOps can identify upside, not only faults.

### Technical path

```text
curtailment + demand + battery/generator constraints
-> recurring renewable headroom
-> opportunity Finding
```

Then:

```text
paired load-addition experiment
-> new source envelopes
-> before/after operating result
```

### Product surfaces

- Renewable/Productive-use;
- intervention comparison.

### Review checkpoint

The system clearly separates:

```text
physical capacity opportunity
```

from:

```text
market/business viability
```

---

## Slice G - Asset lifecycle

### Goal

Demonstrate slow-burn asset risk.

### Technical path

```text
battery operation
-> stress contributors
-> stress/trajectory evidence
-> bounded lifecycle interpretation
```

### Product surfaces

- Battery Health;
- Site Overview;
- Financials.

### Deferred

Exact RUL prediction.

---

## Slice H - Intervention verification

### Goal

Close the loop.

### Technical path

```text
Finding
-> accepted intervention
-> frozen world/config change
-> new simulation/evidence
-> comparable verification window
-> Verified / Ineffective / Inconclusive
```

### Product surfaces

- Configuration change;
- Action / Maintenance Verification;
- Finding state/history.

### Review checkpoint

A completed task cannot resolve the Finding without post-action evidence.

---

## Slice I - Portfolio demonstration

### Goal

Turn several individually credible stories into one management experience.

### Suggested portfolio

```text
Meki   healthy benchmark
Kobo   avoidable generator runtime
Genda  fuel reconciliation
Bahir  reliability / unserved energy
Desta  productive-use opportunity
Arsi   battery stress
```

### Product surface

Portfolio Value & Operations.

### Earliest credible client demo

**Here, although a prospective client can be approached earlier if Slice C-D is already compelling.**

A polished first external demo should ideally contain:

- portfolio;
- one deep finding;
- economic translation;
- one opportunity;
- one intervention/verification;
- simulator proof.

---

# 8. Priority and trade-off guide

## MUST GET RIGHT NOW

These are expensive to fake correctly later because they define whether the demo is trustworthy.

### 1. Truth isolation

Private world truth does not leak into product analytics.

### 2. Canonical source boundary

The product receives committed canonical source envelopes through normal ingestion.

### 3. Causal timing

An implementer can explain exactly when causes apply, when state changes, and what a reading timestamp means.

### 4. Controller intent vs physical result

Requested 30 kW and accepted 22 kW cannot collapse into one number.

### 5. Component identity

Two loads, two meters or two chargers must not become ambiguous global states.

### 6. Provenance

The site, Foundation/configuration, scenario, run and intervention inputs remain reconstructible.

### 7. Downstream Findings

Simulator scenarios cannot manufacture the product conclusions they are meant to test.

---

## GOOD ENOUGH FOR DEMO

These should be physically sensible and inspectable, not research-grade.

### Battery model

Enough to model:

- SOC;
- charge/discharge limits;
- efficiency;
- basic stress accumulation.

No electrochemical model required.

### Generator model

Enough to model:

- state;
- rated output;
- start/stop;
- minimum runtime;
- fuel use.

No detailed engine thermodynamics.

### Productive load

A scheduled controllable load is sufficient.

### Economics

Versioned assumptions with visible basis are enough.

Do not build a financial planning suite.

### Portfolio recipes

A small hand-curated scenario portfolio is acceptable.

### Scenario authoring

Configuration files/recipes are sufficient; a full authoring UI can wait.

---

## DEFER

- AC power-flow solver;
- droop / transient dynamics;
- generalized optimizer;
- precise battery remaining useful life;
- generalized maintenance planning;
- perfect component ontology;
- generalized pack/plugin framework;
- cold-chain implementation;
- e-mobility implementation;
- broad multi-tenant administration;
- advanced ML anomaly detection;
- chatbot/agent interface;
- exhaustive report builder.

A deferred item should move forward only when one of these occurs:

1. the mini-grid demo genuinely needs it;
2. a real pilot exposes the limitation;
3. the second vertical proves the abstraction is necessary.

---

# 9. Product roadmap and feature-map deltas

## Move earlier

### Finding Detail + Evidence

This should arrive as soon as the first dispatch analytic exists. It is the trust-defining interaction.

### Thin financial translation

Do not wait for a complete Financials module before showing why the first Finding matters.

A small, disciplined consequence bridge is more valuable than broad financial functionality.

### Site Overview composition

Once the first Finding exists, surface it on the Site Overview rather than requiring the user to discover it through deep navigation.

### Intervention verification

Move earlier than a conventional roadmap might suggest because it proves the core differentiation:

```text
AssetOps detects
-> operator acts
-> AssetOps verifies
```

---

## Keep later

### Broad asset inventory sophistication

Useful, but not central to the first story.

### Global maintenance management

Do not allow CMMS breadth to displace operational intelligence.

### Generic scenario authoring UI

Recipes are enough initially.

### Rich reports

Screens and exported evidence can come first.

---

## Missing but important for the demo roadmap

### Operational records

Fuel delivery/dip records should be treated as first-class evidence, not as a later convenience.

### Productive-use opportunity

This should be explicit on the roadmap because it changes AssetOps from "cost leakage detector" to an operational-economic intelligence product.

### Asset trajectory

Battery risk should be expressed as state + trajectory rather than a static health card.

### Paired intervention comparison

Useful once the basic productive-use or policy-change story exists.

---

# 10. Planner notes

## Plan toward reviewable outcomes

The primary planning unit should be:

> **What coherent thing can the product owner run and judge at the end of this work?**

Good task boundaries often cross layers.

Example:

```text
bad sequence:
build state registry
build controller abstraction
build resolver abstraction
build observation abstraction
build envelope abstraction
eventually build product

better sequence:
make one generator interval become a normal ingested Site history
then make that interval become one credible Finding
```

The second still builds the required abstractions, but each group is anchored to visible behavior.

## Preserve reviewability

The current v4 design puts pressure around the typed property carrier and component-addressed bindings.

Treat:

```text
typed per-component property carrier
        ↓
component-addressed binding/resolution
```

as a natural dependency boundary.

If the current task is too broad, split it before implementation rather than accepting a large architectural lump.

Site-scoped control properties should wait until the controller actually consumes them.

## Do not create tasks for every v4 noun

`StateRef`, `ControlIntent`, `AcceptedFlowSet`, `BusinessContext` and `PairedExperiment` are design concepts, not automatically separate tasks.

Create a separate task when:

- it has an independently reviewable outcome;
- it protects a risky boundary;
- or it can be implemented/tested independently without hiding progress.

## Escalate only meaningful decisions

Escalate when a choice:

- changes the client story;
- changes a protected boundary;
- is expensive to reverse;
- prevents the next demo slice.

Do not interrupt the product owner for:

- naming;
- cheap internal representation;
- exact file placement;
- generic API aesthetics.

## Keep second verticals as architecture tests, not current work

Mini-grid should stay clean enough that cold-chain/e-mobility do not require rewriting:

- time engine;
- truth barrier;
- gateway boundary;
- controller/physics separation.

That does not mean building their domain models now.

---

# 11. Implementer notes

## Do

- implement the smallest path that produces inspectable end-to-end behavior;
- keep private truth visibly distinct in Simulator Lab;
- make requested control and accepted physical outcome independently inspectable;
- publish exact canonical source envelopes through the normal boundary;
- preserve source time / gateway time distinctions;
- keep scenario causes independent of Findings;
- expose evidence gaps and uncertainty;
- ensure each demo scenario is reproducible;
- make before/after intervention inputs inspectable;
- write tests around protected seams and visible behavior.

## Do not

- bypass ingestion because it makes the demo easier;
- allow the product backend to read simulator state;
- put `candidate_avoidable=true` in a scenario fixture;
- turn private oracle values into evidence;
- generalize a framework before the second concrete use exists;
- model physical detail that the current analytic cannot observe or use;
- hide missing evidence by manufacturing defaults;
- turn a work item into a successful outcome without verification;
- block a demo slice on low-cost vocabulary or internal-style disagreement.

## Implementation freedom

Builders should be free to choose:

- internal helper functions;
- local data structures;
- small module boundaries;
- UI component composition;
- implementation algorithms inside a protected contract,

unless the choice affects:

- evidence semantics;
- causality;
- reproducibility;
- product boundary;
- stable provenance.

---

# 12. Open decisions

Only the following kinds of decisions should remain visible here.

## 12.1 First client-facing financial assumptions

### Why it matters

The first dispatch Finding needs to become economically meaningful.

### Blocks

Slice D.

### Latest decision point

Before Site Financials/Portfolio exposure is shown externally.

### Recommended default

Use a small versioned BusinessContext containing:

- fuel price;
- generator maintenance accrual assumption;
- mini-grid tariff where needed.

Keep every value visibly labelled as measured/modelled/scenario.

---

## 12.2 Productive-use intervention used in the demo

### Why it matters

The opportunity story is much easier to understand with a recognizable load.

### Blocks

Slice F polish, not its underlying analytic.

### Latest decision point

Before external demo recording.

### Recommended default

Use a small cold-room or milling load because both are recognizable productive-use cases and easy to explain electrically.

Do not imply local commercial demand.

---

## 12.3 How much battery degradation to monetize

### Why it matters

Too much precision will weaken credibility.

### Blocks

Only the lifecycle financial story.

### Latest decision point

Before Slice G is exposed externally.

### Recommended default

Show:

```text
stress trajectory
replacement value
scenario exposure
```

without exact remaining-life date.

---

# 13. Demo completion definition

There are three useful finish lines.

## 13.1 Internal architecture demo ready

The team can:

1. run one mini-grid;
2. inspect physical truth;
3. inspect device-reported values;
4. inspect staged canonical envelopes;
5. Commit the run;
6. see normal Site history populated through ingestion.

This proves the simulator/product boundary.

---

## 13.2 Domain-expert feedback ready

A mini-grid practitioner can:

1. open one simulated mini-grid Site;
2. see load/PV/battery/generator context;
3. inspect one Candidate Avoidable generator-runtime Finding;
4. click "Why are you saying this?";
5. inspect the evidence and claim boundary;
6. see an indicative bounded fuel consequence.

This is enough to ask the most important early questions:

> Is this problem real in your operation?

> Is the evidence sufficient?

> What would you need to trust this?

> What data do your sites actually expose?

There is little value in waiting for a complete six-site portfolio before obtaining this feedback.

---

## 13.3 Credible client demo ready

A user can:

1. open a portfolio with several deliberately different simulated sites;
2. identify where operational/economic attention is required;
3. open Kobo and inspect the operating context;
4. open a Finding and understand evidence, confidence and claim boundary;
5. see bounded financial consequence;
6. inspect a fuel reconciliation exception;
7. inspect a productive-use opportunity;
8. see a battery trajectory risk;
9. apply or inspect one intervention;
10. observe the resulting world through normal source-envelope ingestion;
11. see AssetOps verify whether the target improved without unacceptable guardrail trade-offs;
12. reveal Simulator Lab/private truth comparison to demonstrate how the system was validated.

At this point the client should be able to summarize AssetOps in roughly this form:

> **It tells me where my sites are operating in ways that affect cost, reliability, productive capacity or asset value, shows me the evidence, and helps me verify what to change.**

That is the first product milestone that matters.
