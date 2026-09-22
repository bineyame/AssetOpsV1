# Simulator design v2

The engineering design for the AssetOps simulator: what it is for, how it is built, and how its internals work. Written so an implementer can build from it without re-deriving the reasoning behind it.

This revision preserves the strongest parts of the previous design — causal truth, reproducibility, structural truth isolation, stock/flow separation, table-driven observation realism, explicit bounds, and domain-pack isolation — while aligning the simulator more directly with the product goal: a single causal simulator capable of producing convincing mini-grid, cold-chain and e-mobility operating worlds that enter AssetOps through the same source boundary as real sites.

---

## 0. Revision intent

### 0.1 What changed in this revision

The previous design was strongest as a deterministic kernel design. This revision widens it into a complete simulator design by making the following previously implicit or underspecified concerns first-class:

1. **Canonical ingestion boundary**
   - Simulator observations never enter Evidence directly.
   - Device observations are transformed into simulated gateway outputs.
   - Gateway outputs are serialized/persisted as canonical source envelopes.
   - Draft output remains staged.
   - Commit seals and releases those envelopes through normal AssetOps ingestion.
   - AssetOps derives Evidence only after validation, normalization and quality handling.

2. **Time convention**
   - Controller decisions occur at time `t`.
   - The world evolves during `[t, t + dt)`.
   - Resulting physical truth, observations, events and publications are timestamped at `t + dt`.
   - This restores the already chosen AssetOps simulator convention and avoids ambiguity about whether telemetry reflects pre- or post-decision state.

3. **Controller intent vs physical result**
   - Controllers issue intents/setpoints.
   - Physical coupling decides what can actually happen.
   - Accepted physical flows may differ from requested flows.
   - This distinction applies equally to battery dispatch, compressor operation and vehicle charging.

4. **Domain-pack contract**
   - A domain pack now has an explicit interface covering state schema, topology, component models, forcings, controllers, physical resolution, integration, events, observation bindings, maintenance effects and scenario recipes.

5. **Topology / component identity**
   - The world is not only a flat `state_key` map.
   - Components have identity, type, properties and declared connections.
   - The topology does not imply AC load-flow mathematics; it provides the minimum graph needed for causal composition and device mapping.

6. **Generic load model**
   - Fixed, profiled, event-driven, critical, controllable, deferrable and productive/revenue-generating loads are supported as common abstractions.

7. **Intervention and maintenance mechanics**
   - Maintenance changes the world, configuration or evidence path.
   - Completion of work never directly resolves a Finding.
   - Post-action AssetOps evidence must verify the result.

8. **Asset stress / degradation**
   - Generic stress accumulation is part of the world model.
   - Domain packs define stress contributors.
   - The simulator does not need to predict exact remaining useful life.

9. **Operational records**
   - Human/business records are separate from sensor observations.
   - They may be correct, delayed, missing or contradictory.

10. **Gateway realism**
    - Buffering, outage, delayed publication, duplication, sequence IDs and timestamp distinctions are explicit simulator concerns.

11. **Counterfactual pairing**
    - Baseline and intervention runs can share the same initial state, forcing realization and deterministic substreams so that one declared change can be compared cleanly.

12. **Portfolio recipes**
    - Scenario packs can generate whole demonstration portfolios, not only one site at a time.

13. **Policy ownership**
    - Baseline operating policy remains Site Foundation / Controls.
    - Scenarios may apply time-valid changes to policy.
    - Run identity freezes the effective configuration used.
    - No sixth conceptual property owner is introduced.

14. **Business/economic context**
    - Money remains outside simulator physics.
    - Financial translation uses a separate downstream, versioned `BusinessContext`.
    - Replacement value is not a physical `RATING_UNIT`.

15. **Reproducibility requirement**
    - Reworded from “byte-identical forever on any machine” to canonical, deterministic output for a frozen supported runtime/kernel contract.

16. **Exact arithmetic**
    - Per-step `limit_denominator()` approximation is removed from the canonical design.
    - Exact arithmetic is retained while practical; if precision control becomes necessary, it must be introduced as an explicit versioned numeric contract.

17. **Isolation checks**
    - Structural dependency guards replace lexical bans on words such as `generator`, `fuel`, `charger` or `compressor`.

### 0.2 Why these changes were necessary

The immediate product goal is not merely to prove that a deterministic kernel can evolve a mini-grid. It is to support a client demo in which AssetOps can show:

- where a portfolio is losing operating value,
- where productive-use or throughput opportunity exists,
- where service/reliability is at risk,
- where maintenance burden is accumulating,
- where asset life is being consumed unusually quickly,
- what intervention might change the outcome,
- and whether the intervention actually worked.

The simulator must therefore model not only physical evolution but also controllers, device realism, gateway behavior, operational records, interventions, maintenance and repeatable what-if comparisons across multiple verticals.

---

## 1. Design goals

In priority order. Where two conflict, the higher one wins.

1. **Causal truth.** A world state changes because a declared cause moved it. Remove the cause and the consequence disappears; change it and the consequence changes; leave unrelated frozen inputs alone and unrelated trajectories remain unchanged.

2. **Product-boundary fidelity.** A simulated site must cross into AssetOps through the same logical source boundary as a real site: device observation → simulated gateway → canonical source envelope → serialization/persistence → Commit/release → normal ingestion → Evidence.

3. **Reproducibility.** The same frozen deterministic identity, supported runtime, kernel version, scenario, interventions and profile versions produce the same canonical trajectory and source-envelope content.

4. **Structural truth isolation.** Private world state must be unable to reach product Evidence, analytics, Findings or Financials except through the normal observation/gateway/source path.

5. **Cross-vertical reuse.** Mini-grid, cold-chain and e-mobility packs must be addable without domain-specific branching in the shared kernel, observation layer or normal ingestion path.

6. **Intervention fidelity.** A policy change, maintenance action, component failure or added load must change the simulated world first. AssetOps then discovers the consequence from evidence.

7. **Honest refusal.** Where the kernel cannot resolve a required case, it produces a typed failure or explicit unavailable state. It never quietly clamps, invents a default or emits partial output as complete.

### 1.1 Non-goals

- Not a power-systems transient or phasor-domain simulator.
- Not a CFD or refrigeration engineering solver.
- Not an electrochemical cell simulator.
- Not real-time; simulated time is independent of wall time.
- Not a findings engine.
- Not a financial engine.
- Not a CMMS.
- Not a digital twin claim by default.
- Not a generic optimization solver.

The target is a **causal site/world simulator with enough physics and control fidelity to exercise AssetOps operational reasoning**.

---

## 2. Binding contracts carried forward

The kernel is new; the repository contracts it must honor are not.

The following remain binding:

- `EXECUTION_CONTRACT_VERSION`
- `DISPATCH_RULES`
- T020B window and forcing semantics
- `BOUND_POLICIES` / `BOUND_CASES`
- `CANONICAL_UNITS`
- `RATE_INTEGRALS`
- `NON_NEGATIVE_DIMENSIONS`
- `DURATION_UNIT_SPELLINGS`
- initialization ownership
- `DeterministicIdentity`
- `FrozenInterval`
- publication-profile cadence
- `ModelProfile.supported_states`
- projection vs composition rule
- dependency-direction guard

### 2.1 One semantic clarification

`DeterministicIdentity` must bind the **effective time-valid Site Foundation / Controls version** used by the run, plus scenario/intervention history. This does not create a new policy owner. It freezes the already owned policy so that a trace and run remain reproducible.

---

## 3. Architecture at a glance

```text
                       ASSETOPS PRODUCT

        L6  Findings / assessments / financial bridge
                              ▲
                              │ reads accepted Evidence only
        L5  Evidence / accepted operational store
                              ▲
                              │ normal ingestion only
                    validation / normalization
                              ▲
                              │
                     COMMIT / RELEASE
                              ▲
                              │
                  persisted source envelopes
                              ▲
                              │
                 simulated gateway publication
                              ▲
                              │
                    device observations
                              ▲
──────────────────────────────┼────────────────────────────
                       TRUTH BARRIER
                              │
                              ▼
        L4  Observation + device + gateway simulation
                              ▲
                              │ samples / reports world state
        L3  Shared causal kernel
                              ▲
                              │ domain-pack contract
        L2  Domain pack / model profile
                              ▲
        L1  vocabulary / topology / properties
```

### 3.1 The one crossing rule

The **only simulator-produced information that enters normal AssetOps ingestion is canonical source-envelope content**.

Neither `WorldState`, `LabProjection`, private truth, `ControlIntent`, physical resolver internals nor scenario expectations may be accepted by the product ingestion path.

---

## 4. Composition and dependency direction

### 4.1 Composition root

Preserve the no-product↔simulator dependency rule with a neutral composition root.

```text
simulator/assetops_simulator/
    kernel/
    transforms/
    gateway/
    packs/

backend/assetops_backend/
    ingestion/
    evidence/
    findings/
    financials/
    runs/

host/
    execution_adapter.py
    app.py
```

Rules:

- backend must not import simulator.
- simulator must not import backend product analytics.
- host may compose both.
- shared contracts crossing the composition root must not expose private truth to product-owned modules.

### 4.2 What crosses the execution adapter

The previous `RunExecutionPort.observations()` shape is intentionally narrowed.

The product-facing side does **not** receive `Observation`.

A practical split is:

```python
class RunExecutionPort(Protocol):
    def start(self, run: SimulationRun) -> RuntimeHandle: ...
    def step(self, handle: RuntimeHandle, steps: int = 1) -> LabProjection: ...
    def run_to_end(self, handle: RuntimeHandle) -> LabProjection: ...
    def staged_envelopes(self, handle: RuntimeHandle) -> Sequence[SourceEnvelope]: ...
    def commit(self, handle: RuntimeHandle) -> CommitResult: ...
```

Where:

- `LabProjection` is private simulator/Lab state.
- `SourceEnvelope` is the canonical release artifact.
- `CommitResult` identifies sealed persisted envelopes released through normal ingestion.

Draft envelopes are visible in Simulator Lab as **staging**, but not as Site history.

---

## 5. World model

### 5.1 Components and topology

A simulated Site is composed from identifiable components.

```text
Component
- component_id
- component_type
- properties
- ratings / limits
- state bindings
- ports / roles

Connection
- from_component
- from_port
- to_component
- to_port
- medium / relation
```

Examples:

Mini-grid:
```text
PV-001 → INV-001 → AC-BUS
BAT-001 → PCS-001 → AC-BUS
GEN-001 → AC-BUS
AC-BUS → LOAD-RES
AC-BUS → LOAD-MILL
TANK-001 → GEN-001
```

Cold-chain:
```text
GRID → AC-BUS
GEN-001 → AC-BUS
AC-BUS → CMP-001
CMP-001 → ROOM-001   (thermal influence)
DOOR-001 → ROOM-001  (heat-gain relation)
```

E-mobility:
```text
GRID → AC-BUS
PV → AC-BUS
BESS → AC-BUS
AC-BUS → CHG-01
AC-BUS → CHG-02
CHG-01 → VEH-017
CHG-02 → PACK-208
```

This graph provides causal composition and mapping. It does **not** imply network load-flow mathematics.

### 5.2 Stocks and flows

Two quantity classes remain canonical.

**Stock** persists across steps and is integrated or stateful.

Examples: fuel volume, battery SOC, chamber temperature, accumulated stress, cumulative energy.

**Flow** applies over one step and is recomputed each step.

Examples: generator power, PV power, battery charge/discharge power, fuel-consumption rate, cooling power, heat gain, charger power, served load, unserved load and curtailed power.

```python
@dataclass(frozen=True)
class WorldState:
    simulation_time: Instant
    step_index: int
    stocks: Mapping[StateRef, Fraction]
    flows: Mapping[StateRef, Fraction]
    discrete: Mapping[StateRef, DiscreteValue]
```

A `StateRef` should include component identity where appropriate, not only a global string.

### 5.3 Generic load abstraction

Shared load semantics:

```text
LoadKind
- FIXED
- PROFILED
- EVENT_DRIVEN
- CRITICAL
- CONTROLLABLE
- DEFERRABLE
- PRODUCTIVE
```

Mini-grid examples: household, clinic, mill, irrigation pump.

Cold-chain examples: compressor, fans, lights, auxiliaries.

E-mobility examples: charger session, fleet batch, swap-battery charging.

The kernel does not know business meaning such as “mill” or “motorcycle”; the pack does.

---

## 6. Time and step semantics

### 6.1 Frozen time convention

For one interval `[t, t + dt)`:

```text
S(t) available
    ↓
1. APPLY DUE EVENTS / CONFIG CHANGES at t
    ↓
2. BUILD CONTROLLER OBSERVATION at t
    ↓
3. CONTROLLER DECIDES intent for [t, t+dt)
    ↓
4. PHYSICAL RESOLVER / COUPLER accepts or limits intent
    ↓
5. WORLD EVOLVES / INTEGRATES over [t, t+dt)
    ↓
6. COMMIT resulting truth S(t+dt)
    ↓
7. BALANCE / INVARIANT CHECKS
    ↓
8. DEVICE OBSERVATION of result at t+dt
    ↓
9. GATEWAY PUBLICATION according to cadence/state
    ↓
10. EVENTS / OPERATIONAL RECORDS emitted at their defined result time
```

This is the canonical timing contract.

### 6.2 Why this convention

It gives a clean causal interpretation:

- decisions are made from the world known at `t`,
- physics evolves afterward,
- telemetry at `t+dt` describes the consequence of that interval,
- controller request and physical outcome are not conflated,
- generated evidence can be traced to the decision that preceded it.

### 6.3 Event dispatch

Keep the existing half-open interval rules, point/window semantics, bounded effects and intra-instant grouping.

If multiple effects at one instant are order-dependent and scenario semantics do not declare an order, fail with a typed execution error rather than invent one.

---

## 7. Controller intent and physical coupling

### 7.1 Controller contract

Controllers do not mutate world state.

They receive a declared observation of the current world and emit intent.

```text
ControlObservation
    ↓
Controller
    ↓
ControlIntent
```

Examples:

Mini-grid:
```text
battery_setpoint = -18 kW
genset_command = START
pv_limit = 45 kW
```

Cold-chain:
```text
compressor_command = ON
target_temp = 3 °C
```

E-mobility:
```text
charger_01_limit = 11 kW
charger_02_limit = 22 kW
bess_setpoint = -15 kW
```

### 7.2 Physical resolver contract

The physical resolver accepts current world state, exogenous forcing, component limits, controller intent, topology and applicable faults. It returns accepted physical flows.

```text
ControlIntent
     ↓
PhysicalResolver
     ↓
AcceptedFlowSet
```

Examples:

- controller requests 30 kW battery discharge, PCS can provide 22 kW → accepted 22 kW.
- controller commands compressor ON, degraded compressor provides 68% of rated cooling.
- scheduler allocates 22 kW to a vehicle, battery acceptance is 11 kW → accepted 11 kW.

This distinction is required across all three domain packs.

### 7.3 Mini-grid power allocation

For the first mini-grid pack, a declared cascade is sufficient:

1. available sources,
2. policy priority allocation,
3. storage charge/discharge,
4. residual curtailment / unserved load,
5. conservation check.

No network solver is required.

---

## 8. Integration, bounds and numeric behavior

### 8.1 Integration

For integrable stocks:

```text
stock_next = stock_now + integrated_flow
```

The domain pack declares which flows integrate into which stocks and which discrete state transitions apply.

Examples:

- battery power → stored energy / SOC,
- fuel-consumption rate → fuel volume,
- net heat flow → room temperature,
- charger power → vehicle battery energy,
- stress rate → accumulated stress.

### 8.2 Bounds

Preserve the three existing policies:

- `REFUSED_AT_PARSE`
- `FAIL_RUN`
- `BOUNDED_AND_RECORDED`

No silent clamp.

A bounded transition remains a first-class trace record.

### 8.3 Exact arithmetic

Use `Fraction` where the modeled equations remain rational and the operational cost is acceptable.

Do **not** perform `limit_denominator()` at each step in the canonical design. That would introduce repeated approximation while claiming exactness.

If future physical models require non-rational functions or denominator growth becomes operationally material, introduce a separate versioned numeric policy, for example:

```text
NumericPolicy
- EXACT_RATIONAL
- FIXED_POINT(scale=...)
- DECIMAL(precision=...)
```

Changing numeric policy is contract-significant and must be explicit.

---

## 9. Determinism and stochastic variation

Use independent deterministic substreams.

```text
draw(seed, stream_name, step_index, ordinal)
    = cryptographic_digest(...)
```

Examples:

```text
forcing:irradiance
forcing:vehicle-arrivals
sensor-noise:tank-001:level
sensor-bias:temp-001:temperature
failure:charger-02
```

Adding a new stream must not perturb existing streams.

### 9.1 Counterfactual pairing

A paired baseline/intervention experiment should be able to freeze:

- initial Site state,
- Foundation/configuration except the declared intervention,
- scenario forcing realization,
- seed,
- named stochastic substreams,
- simulation interval.

Then one declared change may differ.

Example:

```text
Baseline: reserve = 25%
Intervention: reserve = 32%
```

or:

```text
Baseline: no mill
Intervention: add 12 kW mill
```

The purpose is not to claim causal identification in the real world; it is to provide a controlled simulator comparison.

---

## 10. Observation, devices and sensors

### 10.1 Observation transform

Private world state is sampled into device-level observations.

A binding is keyed by:

```text
(component/state ref, device_id, signal_id)
```

and may declare sample cadence, quantization, noise, bias, dropout, delay, stale behavior, duplicate behavior, out-of-order behavior, clock drift and quality-flag rules.

Truth exists every step; a device reading exists only when sampled.

### 10.2 Device observation is not yet product evidence

`DeviceObservation` remains simulator/gateway-internal.

```text
World truth
    ↓
DeviceObservation
    ↓
SimulatedGateway
```

Only the gateway output may cross into normal ingestion.

---

## 11. Simulated gateway

### 11.1 Responsibilities

The gateway owns publication behavior, including:

- source/device mapping,
- publication cadence,
- message/sequence IDs,
- source time,
- gateway time / published_at,
- buffering,
- connection outage,
- recovery,
- retry,
- duplicate publication,
- delayed publication,
- out-of-order release,
- quality metadata,
- mapping version.

### 11.2 Timestamp semantics

At minimum distinguish:

```text
source_time
gateway_time / published_at
received_at
```

The simulator owns the first two before hand-off.

`received_at` belongs to AssetOps ingestion and exists only after receipt.

### 11.3 Draft / Commit semantics

**Draft**
- observations may be generated,
- gateway may produce staged envelopes,
- envelopes are persisted in staging,
- normal AssetOps Site history is unchanged.

**Commit**
- seals the staged canonical envelopes,
- persists immutable committed artifacts,
- releases them through normal ingestion,
- does not write Evidence, Findings, Site history or financial objects directly.

**After ingestion**
- normal validation/normalization produces accepted Evidence,
- Site history is populated through the product pipeline.

---

## 12. Operational records

Sensor evidence and human/business records are separate classes.

Examples:

Mini-grid:
- fuel delivery,
- manual tank dip,
- operator override,
- maintenance visit.

Cold-chain:
- product loading event,
- door inspection record,
- batch/product context,
- maintenance record.

E-mobility:
- charging session record,
- battery assignment,
- swap transaction,
- maintenance event.

The simulator must support:

- record exists and is correct,
- record exists but is delayed,
- record is missing,
- record conflicts with physical truth,
- record is partial.

Operational records are published through their normal source/manual-record contracts, not injected as product conclusions.

---

## 13. Maintenance and intervention model

### 13.1 Principle

Maintenance changes the world, configuration or evidence path.

It never sets Finding state, Action outcome, VerificationOutcome or financial conclusion.

### 13.2 Intervention types

```text
CONFIGURATION_CHANGE
MAINTENANCE_ACTION
COMPONENT_REPLACEMENT
CALIBRATION
LOAD_ADDITION
LOAD_REMOVAL
POLICY_CHANGE
FAILURE_INJECTION
RESTORE_COMPONENT
```

### 13.3 Examples

Mini-grid:
- change battery reserve,
- service generator,
- calibrate tank sensor,
- replace starter relay,
- add productive load.

Cold-chain:
- clean condenser,
- replace compressor,
- repair backup starter,
- calibrate temperature sensor,
- change thermostat band.

E-mobility:
- replace charger module,
- add chargers,
- change charging schedule,
- replace battery pack,
- add stationary BESS.

### 13.4 Verification implication

Because interventions alter the world first, AssetOps can later compare post-action evidence to declared success criteria.

That preserves the product rule:

```text
work completed ≠ problem solved
```

---

## 14. Asset stress and degradation

### 14.1 Generic abstraction

Introduce a pack-defined stress accumulator.

```text
StressAccumulator
- asset_ref
- stress_dimensions
- accumulated_exposure
- reference / expected band
```

The shared kernel integrates declared stress rates; domain packs define the meaning.

### 14.2 Mini-grid battery

Possible contributors:
- high temperature,
- deep discharge,
- high C-rate,
- high-SOC dwell,
- cumulative throughput.

### 14.3 Generator

Possible contributors:
- runtime,
- starts,
- low-load operation,
- overload.

### 14.4 Cold-chain compressor

Possible contributors:
- starts,
- short cycling,
- runtime,
- difficult operating context,
- degraded cooling efficiency.

### 14.5 E-mobility battery / charger

Possible contributors:
- high-rate charging,
- high temperature,
- high-SOC dwell,
- deep cycling,
- sustained charger high-load operation.

The simulator does not need to convert accumulated stress into an exact failure date. It needs to create a causal, inspectable trajectory that AssetOps can evaluate.

---

## 15. Domain-pack contract

A domain pack must implement or declare:

```text
DomainPack
├── model_profile
├── state_schema
├── component_types
├── topology_rules
├── property_tables
├── forcing_models
├── load_models
├── controller_factory
├── physical_resolver
├── integrators
├── event_handlers
├── stress_models
├── maintenance_effects
├── observation_bindings
├── operational_record_types
└── scenario_recipes
```

The shared kernel must not branch on `site_kind`, component names such as generator/compressor/charger, or domain-pack type.

Domain registration occurs by stable profile identity/version.

### 15.1 Structural isolation tests

Prefer structural checks:

- kernel imports no domain packs,
- shared modules contain no `if site_kind == ...`,
- observation/gateway modules contain no domain-specific branch,
- each pack satisfies the same protocol,
- adding a second pack does not require changing shared kernel logic.

Do not rely on lexical bans on domain words.

---

## 16. Mini-grid pack proof sketch

### 16.1 Components

- PV array / inverter
- battery / PCS
- generator
- fuel tank
- AC bus
- household load
- critical load
- productive load
- meters / sensors
- gateway

### 16.2 Core forcings

- irradiance
- ambient temperature if needed for derating
- household demand
- productive-use schedule
- fuel delivery / external adjustment
- faults

### 16.3 Controller

- reserve policy
- genset start/stop policy
- minimum run/off time
- source priority / merit order
- critical-load protection

### 16.4 Physical resolver

Produces named flows such as:

```text
pv_to_load
pv_to_battery
battery_to_load
generator_to_load
generator_to_battery
curtailed_pv
unserved_load
```

### 16.5 Required demo scenarios

- normal operation
- avoidable generator runtime
- fuel reconciliation gap
- reserve violation
- PV curtailment / unused capacity
- generator start failure
- productive-use load addition
- battery stress accumulation
- gateway / sensor degradation
- maintenance + verification

---

## 17. Cold-chain pack proof sketch

### 17.1 Components

- grid source
- optional PV / BESS
- backup generator
- compressor
- evaporator / condenser abstractions if needed
- cold-room thermal mass
- door
- temperature sensor
- power meter
- gateway

### 17.2 Thermal evolution

A first-order thermal model is sufficient initially.

```text
net_heat
=
ambient_gain
+ door_gain
+ product_loading_gain
+ defrost_gain
- compressor_cooling
```

Temperature is an integrated stock.

### 17.3 Controller

- thermostat / temperature band
- compressor on/off or staging
- minimum on/off time
- backup start policy

### 17.4 Required demo scenarios

- normal cold-room operation
- door-open excursion
- compressor efficiency degradation
- grid outage + backup START_FAIL
- slow cooling recovery
- product loading event
- sensor calibration drift
- excessive compressor cycling
- maintenance restores performance
- maintenance ineffective

---

## 18. E-mobility pack proof sketch

### 18.1 Components

- grid
- optional PV
- stationary BESS
- chargers
- vehicles and/or swappable battery packs
- charging queue / assignment state
- meters
- gateway

### 18.2 Session / arrival model

A charging demand instance declares or generates:

- arrival time,
- initial SOC,
- requested energy or target SOC,
- departure deadline,
- vehicle/battery acceptance limit,
- charger compatibility.

### 18.3 Controller / scheduler

May allocate:

- charger assignment,
- power limits,
- charging priority,
- BESS dispatch,
- tariff-window shifting,
- departure-energy priority.

### 18.4 Physical resolver

Constrains controller intent by:

- site power limit,
- charger rating,
- vehicle/battery charge-acceptance limit,
- stationary BESS limits,
- grid availability,
- fault state.

### 18.5 Required demo scenarios

- normal depot operation
- peak-tariff charging inefficiency
- charger outage
- stationary BESS underutilization
- charging-demand spike
- missed departure-energy target
- battery degradation stress
- solar-aligned charging opportunity
- charger maintenance intervention
- fleet / capacity expansion

---

## 19. Scenario authoring

Scenario authoring remains template-first, not blank-canvas.

A scenario describes:

- world events,
- control/configuration changes,
- faults,
- evidence-quality conditions,
- operational-record conditions,
- interventions,
- duration / interval,
- deterministic seed,
- private expectations.

A scenario never specifies a Finding, assessment state, severity, Action, VerificationOutcome or financial conclusion.

### 19.1 Scenario recipe packs

Examples:

```text
mini-grid-operations-assurance
cold-chain-assurance
e-mobility-depot-assurance
```

Each pack can generate one site or a portfolio.

---

## 20. Portfolio generation

Introduce a composition concept such as:

```text
PortfolioRecipe
- portfolio_id
- site_specs[]
- scenario_recipe per site
- interval
- seed policy
- business-context reference
```

Example mini-grid demo portfolio:

```text
Meki   healthy benchmark
Kobo   avoidable genset runtime
Genda  fuel reconciliation gap
Bahir  reliability / unserved energy
Desta  productive-use opportunity
Arsi   battery degradation trajectory
```

The recipe creates site/scenario/run inputs; it does not create product Findings directly.

---

## 21. Private truth, trace and replay

### 21.1 Private truth

Private simulator truth may include actual physical cause, true fuel movement, true component state, true available capability, true fault state and true intervention effect.

It must never enter source envelopes, normal ingestion, Evidence, analytics, operator UI or exports.

### 21.2 Trace

Trace records may contain:

- step identity,
- world stocks / flows,
- events applied,
- controller intents,
- accepted physical flows,
- bounded transitions,
- device observations,
- gateway publication state,
- failures.

A trace is a reproducibility/debug artifact, not a source of AssetOps Evidence.

### 21.3 Replay

AssetOps Replay remains a view over recorded Site history, not re-simulation.

Simulator trace playback and AssetOps Replay are different concepts.

---

## 22. Policy ownership

### 22.1 Decision

Operating policy belongs to the Site's time-valid Foundation / Controls.

Examples:

- battery reserve
- genset start threshold
- minimum generator runtime
- source merit order
- critical-load priority
- thermostat band
- charger priority policy

### 22.2 Scenario role

A Scenario may schedule a policy change:

```text
Aug 24 09:00
battery reserve 25% → 32%
```

The scenario does not own the baseline policy.

### 22.3 Run identity

The run freezes:

- Foundation/configuration version,
- policy version/effective values,
- scenario version,
- interventions,
- profiles,
- mappings,
- seed,
- interval.

No sixth conceptual property owner is introduced.

---

## 23. Business and monetary context

### 23.1 Decision

The simulator kernel never sees money.

Do not add a money dimension to physical `CANONICAL_UNITS`.

Do not encode replacement value as a physical component rating.

### 23.2 BusinessContext

Use a downstream versioned business/economic context.

Possible fields:

```text
fuel_price
energy_tariff
time_of_use_tariff
productive_use_tariff
charging_price
maintenance_labor_cost
travel_cost
service_event_cost
asset_replacement_value
product_value_band
downtime_cost_assumption
```

### 23.3 Financial bridge

```text
physical / operational evidence
        +
BusinessContext
        ↓
bounded financial consequence
```

Basis must remain explicit:

- measured
- modelled
- extrapolated
- scenario-based

The simulator supplies quantities and trajectories, not monetary conclusions.

---

## 24. Execution failures

Introduce a vocabulary distinct from setup blocking/refusal.

Examples:

```text
ORDER_DEPENDENT_GROUP
BALANCE_IDENTITY_VIOLATION
PHYSICAL_RESOLUTION_FAILURE
UNSUPPORTED_MODEL_STATE
INTEGRATION_BOUND_FAILURE
TOPOLOGY_INCONSISTENT
```

These are execution outcomes, not setup refusals.

---

## 25. Build order

The simulator should be built as vertical slices that prove the architecture, not as a complete generic framework before value is visible.

### Slice 1 — mini-grid causal kernel

Prove:
- one Site topology,
- one controller,
- one physical resolver,
- battery/fuel stocks,
- named power flows,
- deterministic time,
- observation sampling.

### Slice 2 — gateway / source-envelope path

Prove:
- device observations,
- gateway publication,
- staging,
- persistence,
- Commit,
- normal ingestion,
- no direct simulator→Evidence path.

### Slice 3 — first operational finding world

Create:
- normal baseline,
- avoidable generator runtime,
- fuel consequence,
- AssetOps finding/evidence.

### Slice 4 — intervention / verification

Change:
- reserve or generator stop policy,
- rerun paired scenario,
- publish post-change evidence,
- verify target and guardrails.

### Slice 5 — productive-use / load addition

Add:
- productive load,
- renewable headroom,
- curtailment change,
- energy-sales opportunity.

### Slice 6 — degradation / maintenance

Add:
- generic stress accumulator,
- battery stress,
- maintenance action,
- post-maintenance verification.

### Slice 7 — cold-chain pack

Prove the same kernel supports:
- thermal stock,
- cooling flow,
- compressor controller,
- backup event,
- degradation / recovery.

### Slice 8 — e-mobility pack

Prove:
- charger/vehicle assignment,
- SOC evolution,
- site power constraint,
- charging scheduler,
- throughput opportunity.

### Slice 9 — portfolio recipes

Generate:
- multi-site mini-grid demo portfolio,
- optional cold-chain portfolio,
- optional e-mobility depot portfolio.

---

## 26. Acceptance tests that matter most

The most important architecture tests are behavioral.

1. **Truth isolation** — deleting private truth must not change product output.
2. **Ingestion equivalence** — AssetOps can be reconstructed from committed source envelopes without simulator runtime objects.
3. **Time causality** — a decision at `t` cannot be observed as a resulting physical state before `t + dt`.
4. **Controller/physics separation** — requested flow may differ from accepted flow without corrupting the controller trace.
5. **Counterfactual stability** — adding an unrelated sensor or random stream does not perturb baseline physical trajectories.
6. **Cross-vertical isolation** — adding cold-chain or e-mobility requires no domain branch in the shared kernel.
7. **Maintenance semantics** — marking maintenance completed does not resolve a finding unless new evidence satisfies verification.
8. **Operational-record uncertainty** — missing/delayed records lower claim capability without changing private truth.
9. **Gateway realism** — source_time, gateway_time and received_at remain distinct through outage and recovery.
10. **Portfolio generation** — a scenario pack can produce multiple logical Sites with independent histories and normal portfolio roll-up behavior.

---

## 27. Design test

This design is successful if all three statements remain true:

1. **Mini-grid** can model dispatch, fuel, productive use, service, battery stress and maintenance without bypassing normal ingestion.
2. **Cold-chain** can model thermal dynamics, compressor degradation, backup failure, product-condition exposure and maintenance using the same kernel.
3. **E-mobility** can model charging demand, battery SOC, charger constraints, scheduling, asset stress and throughput using the same kernel.

If adding either later vertical requires:

- `if site_kind == ...` in the kernel,
- a simulator-only analytics path,
- a direct Observation→Evidence bridge,
- a new time engine,
- a second gateway/ingestion contract,

then the seam is wrong and should be corrected rather than rationalized.

---

# Change log from previous draft

## Preserved without material change

- causal runtime authority,
- non-goal of full power-system simulation,
- truth isolation,
- stock/flow separation,
- explicit bounds,
- deterministic named substreams,
- table-driven observation transform,
- composition root outside backend/simulator,
- domain packs,
- private expectations,
- trace identity binding.

## Changed

### CHG-01 — Source boundary hardened
**Before:** `Observation` could be interpreted as the object Layer 5 consumes.

**Now:** only canonical persisted source envelopes cross into normal ingestion.

**Reason:** this matches the frozen AssetOps architecture and makes the demo claim “the simulator ends where the real site begins” literally true.

### CHG-02 — Step timing changed
**Before:** observe before integrate; stock reading at `t`, flow for `[t,t+dt)`.

**Now:** controller decides at `t`; world evolves; resulting truth and telemetry appear at `t+dt`.

**Reason:** restores the already selected time convention and removes ambiguity between decision and consequence.

### CHG-03 — Control intent separated from physical acceptance
**Before:** controller/policy and physical resolution lived largely inside one `RESOLVE` phase.

**Now:** explicit `ControlIntent` → `PhysicalResolver` → `AcceptedFlowSet`.

**Reason:** essential for battery limits, degraded compressors and charger acceptance.

### CHG-04 — Topology made first-class
**Before:** world centered mainly on state keys.

**Now:** components, ports and connections are explicit.

**Reason:** multi-vertical worlds require component identity and causal connectivity without requiring network load flow.

### CHG-05 — Generic load model added
**Reason:** productive-use loads, compressor loads and charging sessions share important semantics that should not be reimplemented per vertical.

### CHG-06 — Maintenance/intervention model added
**Reason:** the desired AssetOps demo includes intervention and post-action verification; work must change the world, not product state.

### CHG-07 — Asset stress/degradation model added
**Reason:** battery, compressor, generator and charger lifecycle exposure is a core client-facing value story.

### CHG-08 — Operational-record path added
**Reason:** AssetOps relies on telemetry plus human/business records; claim ceilings depend on missing/delayed records.

### CHG-09 — Gateway realism made explicit
**Reason:** source/gateway/received timestamps, buffering and recovery are important to evidence semantics and client credibility.

### CHG-10 — Counterfactual pairing added
**Reason:** the client demo needs controlled “what if we change reserve / add a mill / add chargers?” comparisons.

### CHG-11 — Portfolio recipes added
**Reason:** the first client demo is portfolio-oriented, not a single-site lab.

### CHG-12 — Policy ownership resolved
**Before:** proposed sixth property owner.

**Now:** Foundation / Controls owns baseline policy; Scenario owns changes; run identity freezes effective policy.

**Reason:** preserves the existing Site Foundation model and avoids an unnecessary conceptual owner.

### CHG-13 — Money resolved downstream
**Before:** open between money in canonical units vs Layer 6.

**Now:** no money in physics; separate versioned `BusinessContext`.

**Reason:** physical truth and commercial assumptions must remain separate.

### CHG-14 — Reproducibility wording narrowed
**Before:** byte-identical forever on any machine.

**Now:** canonical deterministic output for a supported frozen runtime/kernel contract.

**Reason:** preserves meaningful reproducibility without creating unnecessary cross-runtime obligations.

### CHG-15 — `limit_denominator()` removed from canonical step
**Reason:** repeated denominator limiting is approximation and conflicts with an exact-arithmetic claim.

### CHG-16 — Structural isolation checks replace lexical word bans
**Reason:** architecture should be tested by dependencies and branching, not by whether a shared file contains a domain noun.

---

# Open-question decisions

## Q1. Who owns operating policy?

**Decision: Site Foundation / Controls.**

The baseline operating policy is time-valid Site configuration. Scenarios may change it during a simulation interval. `DeterministicIdentity` freezes the effective version and intervention history.

No sixth owner is introduced.

## Q2. Where does money belong?

**Decision: downstream `BusinessContext`, not simulator physics.**

The kernel models quantities and trajectories. AssetOps combines accepted evidence with time-valid business assumptions to calculate bounded financial consequence.

No money dimension is added to `CANONICAL_UNITS`, and replacement value is not a physical rating.

---

# Final rationale

The revised design keeps the previous draft's best engineering decisions but moves the center of gravity from “build a mathematically clean mini-grid kernel” to:

> **build one causally disciplined simulator that can create realistic, repeatable operating worlds for mini-grid, cold-chain and e-mobility, publish them through production-equivalent source boundaries, and support the exact intervention, lifecycle, productive-use and verification stories AssetOps needs to demonstrate to clients.**

That is the architecture test that matters most for the current product stage.
