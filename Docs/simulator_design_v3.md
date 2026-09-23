# Simulator design v3

The engineering design for the AssetOps simulator: what it is for, how it is
built, and how its internals work. This document is intended to be implementable
without requiring the implementer to re-derive product, timing, ownership or
cross-vertical decisions.

v3 incorporates the Architect review of v2, especially the conflicts and
clarifications identified in review sections 3, 4 and 5. Where the review
requested a decision, this document takes it. Where the repository already
enforces a contract, this document aligns to that contract rather than
reopening it.

The strategic target remains unchanged:

> Build one causally disciplined simulator that can create realistic,
> repeatable operating worlds for mini-grid, cold-chain and e-mobility, publish
> them through production-equivalent source boundaries, and support the
> intervention, lifecycle, productive-use and verification stories AssetOps
> needs to demonstrate to clients.

---

## 0. v3 decisions at a glance

The following items were open, conflicting or underspecified in v2 and are now
resolved.

| Topic | v3 decision |
| --- | --- |
| Boundary sampling | A reading timestamped `T` is emitted at the start of the step beginning at `T`, **after events due at `T` are applied**. Stocks/discrete values are state at `T`; rate/interval measurements summarize `[T-dt, T)`. |
| Control vocabulary ban | Preserve the existing ban. Use compatible names now (`door-ajar`, `operator-hand-dip`, `operator-commanded`, etc.). Retiring the ban requires its own explicit topology/evidence slice. |
| Component addressing | Add component-addressed runtime state in T020A. `state_key` remains the semantic state name; `StateRef` adds site/component scope. |
| Policy ownership | Baseline policy remains Site Foundation / Controls. Do **not** turn `ControlAssumption` into a setpoint carrier. Add typed control properties alongside it. |
| Composition root | Keep the neutral `host/` composition root. Build to the stronger rule: simulator imports **no** `assetops_backend` package at all. |
| Lab observations | Device observations remain private and may be displayed through `LabProjection`; they never become product-side records. |
| RNG digest | Pin to BLAKE2b-256 with canonical input encoding and domain separation. |
| Numeric policy | `EXACT_RATIONAL` is the current versioned policy. `_exact(...).limit_denominator(1_000_000)` remains allowed only at the authored-float → Fraction boundary; never per simulation step. |
| Coupled-flow solver | Use a declared deterministic cascade for current verticals. A numerical solver is outside the current contract and would require an explicit solver/tolerance/numeric-policy revision. |
| Discrete state | Add a typed discrete-state contract: initialization owner, allowed values, transitions, trace record and observation mapping. |
| Counterfactual pairing | Add an immutable `PairedExperiment` record. It is **not** part of either run's identity and therefore cannot perturb trajectories. It proves the declared shared inputs and allowed difference. |
| Dynamic initial state | Run-start dynamic conditions, including accumulated stress/degradation state, are scenario/initial-condition owned. They may be populated from a labeled site snapshot for clones/replay, but are frozen as initialization inputs. Unknown stress is never silently set to zero. |
| Business context | Remains downstream of simulator physics. No money dimension enters the kernel. |

---

# 1. Design goals

In priority order. Where two goals conflict, the earlier goal wins.

1. **Causal truth.**
   A world state changes because a declared cause moved it. Remove the cause and
   the consequence disappears; change it and the consequence changes; unrelated
   frozen inputs remain unaffected.

2. **Product-boundary fidelity.**
   A simulated site crosses into AssetOps through the same logical source
   boundary as a real site:

   ```text
   world
     → device observation
     → simulated gateway
     → canonical source envelope
     → serialization / persistence
     → Commit / release
     → normal AssetOps ingestion
     → validation / normalization
     → Evidence
   ```

3. **Reproducibility.**
   A frozen deterministic identity, supported runtime, kernel version, model
   profiles, intervention history and numeric policy produce the same canonical
   trajectory and source-envelope content.

4. **Structural truth isolation.**
   Private world state cannot reach Evidence, Findings, Financials or normal
   operator views except through the source boundary.

5. **Cross-vertical reuse.**
   Mini-grid, cold-chain and e-mobility packs plug into the same time engine,
   truth model, observation/gateway path and ingestion boundary without shared
   code branching on domain identity.

6. **Intervention fidelity.**
   Configuration changes, maintenance actions, failures and added loads change
   the simulated world first. AssetOps discovers their consequence from
   evidence; simulator code never writes product conclusions.

7. **Honest refusal.**
   Unsupported or ambiguous cases produce typed unavailable/failure outcomes.
   There is no quiet clamp, hidden default or partial result presented as
   complete.

## 1.1 Non-goals

- Not a phasor, transient-stability or full AC load-flow simulator.
- Not CFD or a detailed refrigeration solver.
- Not an electrochemical cell simulator.
- Not a financial engine.
- Not a findings engine.
- Not a CMMS.
- Not a default claim of calibrated digital-twin fidelity.
- Not a generic optimization platform.
- Not wall-clock real-time; simulated time is independent of execution speed.

The simulator is a **causal site/world engine with sufficient physical,
control and evidence-path fidelity to exercise AssetOps operational reasoning**.

---

# 2. Binding repository contracts

The following remain binding unless a named task explicitly changes them:

- `EXECUTION_CONTRACT_VERSION`
- `DISPATCH_RULES`
- T020B forcing/window semantics
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
- projection-versus-composition rule
- dependency-direction guard
- the current `BANNED_CONTROL_VOCABULARY`

## 2.1 Existing queue is not replaced

The v2/v3 build sections are **programme phases**, not task-sized slices.

The existing queue remains authoritative:

- **T020A** is the cheapest landing for component-addressed Foundation bindings
  and typed component properties.
- **T020B** owns the step/boundary semantics clarified in §6.
- **T021A** remains a prerequisite parser narrowing.
- **T021/T022** are the first reviewable pieces of the causal runtime.
- **T023 onward** begins the source/gateway/ingestion path.

Nothing in v3 supersedes or reorders those tasks.

---

# 3. Architecture and dependency direction

```text
                        ASSETOPS PRODUCT

       L6 Findings / assessments / financial bridge
                              ▲
       L5 Evidence / accepted operational store
                              ▲
                  normal ingestion only
                              ▲
                    COMMIT / RELEASE
                              ▲
              persisted canonical envelopes
                              ▲
                 simulated gateway
                              ▲
                  device observations
                              ▲
──────────────────────────────┼──────────────────────────
                       TRUTH BARRIER
                              │
       L4 device / sensor / gateway simulation
                              ▲
       L3 shared causal kernel
                              ▲
       L2 domain pack / model profile
                              ▲
       L1 vocabulary / topology / properties
```

## 3.1 The one-crossing rule

The only simulator-produced payload eligible for normal AssetOps ingestion is a
**canonical source envelope**.

The following are private and never accepted by the product evidence path:

- `WorldState`
- `LabProjection`
- private truth
- `ControlIntent`
- `AcceptedFlowSet`
- scenario expectations
- simulator trace records
- raw `DeviceObservation`

This is a structural rule, not a UI convention.

## 3.2 Composition root

Preserve the neutral composition root:

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

1. `backend/` imports no simulator package.
2. `simulator/` imports **no `assetops_backend` package at all**. This is
   deliberately stronger than saying "no product analytics".
3. `host/` is the composition leaf and may import both.
4. Nothing imports `host/`.
5. Canonical source-envelope schemas used on both sides must live in an
   already-neutral contract module. If the current concrete type is
   backend-owned, expose/move the schema through a dependency-neutral contract;
   do not make the simulator import backend merely to construct an envelope.

### Why

The repository guard is stronger than a stylistic layering preference. Building
to the stronger rule prevents private simulator types from becoming product
dependencies and keeps the simulator independently testable.

## 3.3 Execution adapter

```python
class RunExecutionPort(Protocol):
    def start(self, run: SimulationRun) -> RuntimeHandle: ...
    def step(self, handle: RuntimeHandle, steps: int = 1) -> LabProjection: ...
    def run_to_end(self, handle: RuntimeHandle) -> LabProjection: ...
    def staged_envelopes(
        self, handle: RuntimeHandle
    ) -> Sequence[SourceEnvelope]: ...
    def commit(self, handle: RuntimeHandle) -> CommitResult: ...
```

`LabProjection` may contain private generated device observations required by
Simulator Lab. That does **not** make them product-side records.

Example:

```text
Simulator Lab
  fuel sensor generated reading: 289 L
  true tank level:               274 L
```

The Lab may show both because it is gated simulator UI.

The product receives neither value directly. It receives only the committed
source envelope containing the simulated device's 289 L report.

---

# 4. World model

## 4.1 Components and topology

The world is composed of identifiable components and declared relations.

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
- relation / medium
```

Examples:

```text
Mini-grid
PV-001 → INV-001 → AC-BUS
BAT-001 → PCS-001 → AC-BUS
GEN-001 → AC-BUS
AC-BUS → LOAD-RES
AC-BUS → LOAD-MILL
TANK-001 → GEN-001
```

```text
Cold chain
GRID → AC-BUS
GEN-001 → AC-BUS
AC-BUS → CMP-001
CMP-001 → ROOM-001      # thermal influence
DOOR-001 → ROOM-001     # heat-gain relation
```

```text
E-mobility
GRID → AC-BUS
PV-001 → AC-BUS
BESS-001 → AC-BUS
AC-BUS → CHG-01
AC-BUS → CHG-02
CHG-01 → VEH-017
CHG-02 → PACK-208
```

This topology provides causal composition and addressability. It does **not**
imply network load-flow equations.

## 4.2 Component-addressed state — resolved decision

A flat global `state_key` cannot distinguish two loads or two chargers.

v3 therefore separates:

- **semantic state name**: `state_key`
- **runtime address**: `StateRef`

```python
@dataclass(frozen=True)
class StateRef:
    scope: Literal["SITE", "COMPONENT"]
    state_key: str
    component_id: str | None = None
```

Examples:

```text
StateRef(COMPONENT, "load-demand", "LOAD-RES")
StateRef(COMPONENT, "load-demand", "LOAD-MILL")
StateRef(COMPONENT, "charger-power", "CHG-01")
StateRef(COMPONENT, "charger-power", "CHG-02")
StateRef(SITE, "unserved-load", None)
```

### Contract changes to land in T020A

The component-addressing extension must reach the same places that already
freeze initial bindings:

1. `SupportedState`
   - retains `state_key` as the semantic state name;
   - gains/uses an addressing rule such as `SITE` or `COMPONENT`.

2. `FoundationBinding`
   - may carry an explicit `component_id`;
   - a component-scoped binding with no explicit id may resolve only when
     exactly one candidate exists;
   - zero or multiple candidates remain unanswered and block as today.

3. scenario state references
   - use an explicit component selector rather than encoding the id into the
     state-key string.

4. `FrozenInitializationInput`
   - freezes the resolved `StateRef`, not only a string state key.

### Why not `state_key = "CHG-01.charger-power"`?

Because identity and semantics are different concepts. Keeping them separate:

- preserves reusable state vocabulary,
- keeps profile support independent of one site's ids,
- makes ambiguity mechanically detectable,
- allows the same state type on N components.

## 4.3 Stocks, flows and discrete state

```python
@dataclass(frozen=True)
class WorldState:
    simulation_time: Instant
    step_index: int
    stocks: Mapping[StateRef, Fraction]
    flows: Mapping[StateRef, Fraction]
    discrete: Mapping[StateRef, DiscreteValue]
```

### Stock

Persists across steps.

Examples:
- fuel volume,
- battery stored energy / SOC,
- room temperature,
- vehicle battery energy,
- accumulated stress,
- cumulative energy.

### Flow

Prevails over a step and is recomputed.

Examples:
- generator power,
- PV power,
- battery charge/discharge power,
- fuel-consumption rate,
- cooling power,
- heat gain,
- charger power,
- served/unserved load.

### Discrete state — resolved contract

A discrete state is explicitly specified by the domain pack:

```text
DiscreteStateSpec
- state_key
- address scope
- allowed values
- initialization owner
- transition rules
- observable signals
```

Discrete values do not use `RATE_INTEGRALS` or quantitative bound policies.

Every transition emits:

```text
DISCRETE_TRANSITION
- StateRef
- previous value
- next value
- cause/event/controller reference
- simulation instant
```

The same observation transform may sample a discrete state when a signal binding
exists. Timing faults, dropout, delay, duplication and stale behavior still
apply. Numeric noise/quantization do not apply unless a pack defines a
domain-specific reporting transform.

Examples using vocabulary-compatible values:

```text
Generator physical state: STOPPED | STARTING | RUNNING | FAILED
Door physical state:      SEALED | AJAR
Power-path state:         CONDUCTING | ISOLATED | FAULT_ISOLATED
Charger availability:     AVAILABLE | UNAVAILABLE | DERATED
```

These spellings are intentional; see §5.

## 4.4 Generic load abstraction

Shared load semantics:

```text
FIXED
PROFILED
EVENT_DRIVEN
CRITICAL
CONTROLLABLE
DEFERRABLE
PRODUCTIVE
```

A load may carry more than one characteristic.

Examples:

- clinic: `PROFILED + CRITICAL`
- mill: `PROFILED + PRODUCTIVE`
- irrigation pump: `DEFERRABLE + PRODUCTIVE`
- compressor: `CONTROLLABLE + CRITICAL`
- vehicle session: `DEFERRABLE + CONTROLLABLE`

---

# 5. Vocabulary compatibility and control semantics

## 5.1 Existing control-vocabulary ban remains binding

v3 does **not** interpret structural isolation guidance as permission to remove
the existing product-level control-vocabulary ban.

The currently banned tokens include concepts such as:

```text
OPEN
CLOSED
TRIPPED
AUTO
MANUAL
BREAKER
```

The ban protects the product from asserting operational/control semantics before
the topology/evidence contract can substantiate them.

### Decision

**Keep the ban now. Rename simulator identifiers and scenario recipe names to
compatible vocabulary.**

Examples:

| Avoid | Use now |
| --- | --- |
| `door-open-excursion` | `door-ajar-excursion` |
| `manual-tank-dip` | `operator-hand-dip` |
| `manual-override` | `operator-commanded-override` |
| `AUTO` | `CONTROLLER_ENABLED` or domain-specific policy label |
| `MANUAL` | `OPERATOR_COMMANDED` |
| `OPEN` / `CLOSED` power path | `ISOLATED` / `CONDUCTING` |
| `TRIPPED` | `FAULT_ISOLATED` |

### Why renaming is the correct immediate choice

The simulator already needs truthful physical states, but changing a parser
guard is a product-contract decision, not a simulator convenience.

Renaming:

- costs almost nothing,
- keeps current contracts intact,
- avoids accidentally weakening evidence discipline.

A later task may deliberately retire or narrow the ban once topology and
observability make those stronger words truthful. That change must be explicit.

## 5.2 Policy ownership — resolved without changing `ControlAssumption`

Baseline operating policy belongs to the Site's time-valid Foundation /
Controls.

Examples:

- battery reserve,
- generator start threshold,
- minimum runtime,
- source merit order,
- critical-load priority,
- temperature band,
- charging-priority rule.

However, **`ControlAssumption` remains what it was designed to be**: a
documentary assumption with identity, subject, basis and prose. It does not
become a setpoint/state model.

### Typed control properties

Introduce typed control properties alongside `ControlAssumption`.

Component-scoped examples:

```text
BAT-001.minimum-reserve-soc = 30 %
GEN-001.start-soc-threshold = 24 %
GEN-001.minimum-runtime = 10 min
ROOM-001.temperature-upper-limit = 4 °C
```

Site-scoped examples:

```text
site.source-priority =
    [PV, BATTERY, GENERATOR]

site.critical-load-priority =
    [CLINIC, WATER_PUMP, OTHER]
```

The component property carrier should land with T020A's typed property work.
Site-scoped control properties need a parallel typed Site Controls collection,
not an abuse of the component property table.

### Scenario changes

A scenario may apply a time-valid change:

```text
2026-08-24T09:00
BAT-001.minimum-reserve-soc: 25% → 32%
```

or:

```text
2026-08-24T09:00
site.source-priority:
    [PV, BATTERY, GENERATOR]
    →
    [PV, GENERATOR, BATTERY]
```

The scenario owns the **change event**, not the baseline policy.

### Run identity

No new `policy` field is required on `DeterministicIdentity`.

`FrozenSiteBinding` already freezes the Foundation version and valid-from
instant. The ordered intervention history already freezes scenario changes.

Therefore:

```text
Foundation version
+ intervention history
= reproducible effective policy
```

This is one of the reasons policy should remain in Foundation / Controls.

---

# 6. Time, sampling and step semantics

This section resolves the v2/T020B collision.

## 6.1 Boundary semantics

A sample timestamped `T` must never show the pre-event stock state for an event
that is due at `T`.

At the same time, the client/product model benefits from telemetry whose rate
measurement summarizes the physical interval that just completed.

v3 therefore defines a **boundary cycle**.

At instant `T`:

```text
A. APPLY EVENTS / CONFIG CHANGES due exactly at T
       ↓
B. STATE AT T now exists (post-event stocks/discrete state)
       ↓
C. IF SAMPLE/PUBLICATION DUE AT T:
       - sample stock/discrete state at T
       - attach interval-rate / interval-energy measurement for [T-dt, T)
       - apply device/reporting transform
       - hand result to gateway staging/publication
       ↓
D. BUILD CONTROLLER VIEW at T
       ↓
E. CONTROLLER emits ControlIntent for [T, T+dt)
       ↓
F. PHYSICAL RESOLVER returns AcceptedFlowSet
       ↓
G. INTEGRATE / EVOLVE world over [T, T+dt)
       ↓
H. CHECK CONSERVATION / BOUNDS / INVARIANTS
       ↓
I. carry resulting stocks/discrete state to next boundary T+dt
```

For the first simulation boundary there is no preceding interval. Interval-flow
signals are therefore unavailable until one interval has completed unless a
profile explicitly defines an initial historical window.

## 6.2 What a timestamped reading means

A reading at `T` may contain different semantic classes:

### Instantaneous/state signal

```text
fuel level at T
battery SOC at T
room temperature at T
door state at T
```

These are sampled **after events due at T**.

### Interval signal

```text
average generator power ending at T
energy delivered over [T-dt, T)
cooling energy over [T-dt, T)
charger energy over [T-dt, T)
```

These summarize the interval that just ended.

Example:

```text
13:00 reserve-setting change becomes effective
13:00 SOC reading = state after the 13:00 event
13:00 generator average power = average over 12:59–13:00
```

This looks asymmetric only if stock and rate signals are assumed to mean the
same thing. Real instrumentation commonly has exactly this distinction.

## 6.3 Controller observation versus published device observation

Do not conflate:

- what the controller is permitted to see,
- what the gateway publishes to AssetOps.

The controller view is built at `T` from its declared local inputs after due
events.

A remote/public sensor may publish only every 15 minutes and may be noisy,
delayed or missing.

Example:

```text
13:07 true SOC               47.2%
13:07 EMS local SOC input    47.1%
13:07 AssetOps-visible BMS   no new sample
13:15 AssetOps-visible BMS   46.4%, published 13:15:03
```

This separation is required to simulate realistic control while independently
testing evidence limitations.

---

# 7. Controller intent and physical coupling

## 7.1 Controller contract

Controllers do not mutate world state.

```text
ControlObservation
    ↓
Controller
    ↓
ControlIntent
```

Examples:

```text
Mini-grid:
BAT-001 requested power = +30 kW discharge
GEN-001 requested state = RUNNING
PV inverter limit = 45 kW
```

```text
Cold chain:
CMP-001 requested state = RUNNING
target temperature band = 0–4 °C
```

```text
E-mobility:
CHG-01 requested allocation = 22 kW
CHG-02 requested allocation = 11 kW
BESS requested discharge = 15 kW
```

## 7.2 Physical resolver

The resolver combines:

- current state,
- topology,
- forcing,
- component limits,
- failures/degradation,
- controller intent.

It produces `AcceptedFlowSet` plus physical discrete-state transitions.

Example:

```text
Controller request:
BAT-001 discharge 30 kW

Physical constraints:
PCS limit        22 kW
SOC reserve       satisfied
thermal derate    none

Accepted:
22 kW
```

The requested 30 kW remains visible in the control trace. The accepted 22 kW is
what changes physics and can later be observed by a meter.

## 7.3 Why the current resolver is a declared cascade, not an iterative solver

For the current three verticals the required coupling is site-level priority and
limit resolution, not a simultaneous network equation.

Mini-grid example:

1. determine available PV/generator/grid capability,
2. serve load according to declared policy,
3. apply battery charge/discharge subject to SOC and PCS limits,
4. compute curtailment and unserved load,
5. assert exact source/sink conservation.

Cold-chain example:

1. determine electrical supply available to compressor,
2. apply controller request and compressor availability,
3. derive accepted compressor electrical power,
4. derive cooling power under current degradation/context,
5. integrate room thermal state.

E-mobility example:

1. determine site power headroom,
2. apply charger/scheduler priorities,
3. clip by charger ratings,
4. clip by vehicle/battery charge acceptance,
5. allocate BESS/grid/PV according to policy,
6. compute unmet requested charging power.

### Named boundary

A future case such as:

- droop control,
- voltage-dependent load,
- impedance network,
- genuinely simultaneous coupled equations,

would not be forced into this cascade.

It would require a new physical-resolver implementation **plus an explicit
solver/convergence/numeric policy**.

That is intentionally outside the current execution contract.

The reason is not that numerical solvers are forbidden in principle. It is that
introducing an iterative solver also introduces:

- convergence criteria,
- numerical tolerance,
- failure semantics,
- potential platform/runtime sensitivity,

all of which must become versioned contract rather than appearing implicitly
inside a domain pack.

---

# 8. Integration, bounds and numeric policy

## 8.1 Integration

Pack-declared relationships define stock evolution.

Examples:

```text
battery power          → stored energy / SOC
fuel-consumption rate  → tank volume
net heat flow          → room temperature
charger power          → vehicle battery energy
stress rate            → accumulated stress
```

## 8.2 Bounds

Preserve:

- `REFUSED_AT_PARSE`
- `FAIL_RUN`
- `BOUNDED_AND_RECORDED`

No silent clamp.

## 8.3 Numeric policy — resolved decision

The current policy is:

```text
NumericPolicy = EXACT_RATIONAL
NumericPolicyVersion = 1
```

World arithmetic uses `Fraction` while the model remains rational.

### Authored float boundary

The existing `_exact()` conversion behavior remains legitimate at the
**input boundary**:

```text
author wrote decimal
→ parser/runtime has binary float
→ _exact(value).limit_denominator(1_000_000)
→ recover intended practical rational
```

Example:

```text
14 L/h × 4 h
→ 56 L
```

The important distinction:

- **allowed:** one-time authored/input float → rational normalization;
- **forbidden:** calling `limit_denominator()` after every integration step.

Per-step denominator limiting would repeatedly approximate the world and make
the phrase "exact rational runtime" false.

### Future numeric policy

If later models need non-rational functions or denominator growth becomes
material, introduce a new explicit policy such as fixed-point or Decimal with a
version move. Do not change arithmetic silently.

---

# 9. Determinism and RNG contract

## 9.1 Digest — resolved decision

Use:

```text
BLAKE2b-256
```

implemented as:

```python
hashlib.blake2b(payload, digest_size=32).digest()
```

Do not use Python's `hash()`.

## 9.2 Canonical draw identity

Each stochastic draw is a pure function of:

```text
rng-contract-version
seed
stream_name
step_index
ordinal
```

The payload uses an unambiguous canonical encoding (length-prefixed UTF-8
fields or another repository-canonical byte encoding), not ad-hoc string
concatenation.

Domain separation prefix:

```text
assetops-sim-rng-v1
```

Conceptually:

```text
digest(
  "assetops-sim-rng-v1",
  seed,
  stream_name,
  step_index,
  ordinal
)
```

The digest bytes are converted to an integer and mapped deterministically to the
required distribution.

Examples:

```text
forcing:irradiance
forcing:vehicle-arrival
sensor-noise:TANK-001:level
sensor-bias:TEMP-001:temperature
failure:CHG-02
```

Adding a new stream does not perturb any existing stream.

## 9.3 Identity digest

Trace/run identity binding should use the same named hash family and an
independent domain separator:

```text
assetops-sim-identity-v1
```

This avoids accidental reuse of RNG and identity namespaces.

---

# 10. Initial conditions

Every dynamic state at the beginning of a run must have an explicit answer.

## 10.1 Ownership rule

Use existing ownership semantics rather than inventing a new "degradation
owner".

### Foundation-owned

What the asset/site *is*:

```text
battery nominal capacity
fuel-tank capacity
compressor rated cooling
charger rating
site topology
```

### Scenario / run-initial-condition owned

What dynamic condition the world is *in when this run starts*:

```text
fuel level
battery SOC
room temperature
vehicle SOC
generator RUNNING/STOPPED state
door SEALED/AJAR state
accumulated asset stress / degradation state
```

### Publication-owned

How observations are reported, never physical initial truth.

## 10.2 Accumulated stress — resolved decision

Accumulated stress is a run-start dynamic condition and therefore uses the
scenario/initial-condition answerer.

Examples:

### Synthetic new asset

```text
BAT-001 accumulated stress = 0
basis = synthetic-new-asset
```

Zero is acceptable because the scenario explicitly declares a new asset.

### Synthetic aged asset

```text
BAT-001 accumulated throughput = 182 MWh
high-temperature exposure index = 0.34
basis = scenario fixture
```

### Clone / historical setup

A run may initialize from a labeled site snapshot:

```text
source = site-history snapshot 2026-08-01T00:00
battery SOC = 61%
estimated stress state = available model snapshot
```

The snapshot is provenance for resolving the initial condition; once run setup
freezes the answer, the kernel receives a resolved initialization input.

### Unknown

If existing-asset stress is unknown:

```text
stress = UNKNOWN / unavailable
```

Do **not** silently use zero.

A capability requiring historical stress may then be unavailable or claim-limited.

---

# 11. Device observation and gateway path

## 11.1 Observation transform

Bindings are keyed by:

```text
(StateRef, device_id, signal_id)
```

They may declare:

- cadence,
- noise,
- bias,
- quantization,
- dropout,
- delay,
- stale behavior,
- duplication,
- out-of-order behavior,
- clock drift,
- quality semantics.

Truth exists continuously on simulator steps; a device reading exists only at a
declared sample instant.

## 11.2 Gateway responsibilities

The simulated gateway owns:

- source/device mapping,
- source-time preservation,
- gateway time / publication time,
- buffering,
- outage,
- retry,
- delayed release,
- duplicate publication,
- sequence/message ids,
- mapping version,
- quality metadata.

Timestamp distinction:

```text
source_time
gateway_time / published_at
received_at
```

`received_at` is created by AssetOps ingestion, not by simulator runtime.

## 11.3 Draft and Commit

### Draft

- world may run;
- observations may be generated;
- gateway may generate canonical envelopes;
- envelopes are persisted as staging;
- no Site history is changed.

### Commit

- seals eligible staged canonical envelopes;
- persists the committed immutable artifact;
- releases through normal ingestion;
- writes no Evidence/Finding/Financial object directly.

---

# 12. Operational records

Operational/human records are separate from sensor observations.

Examples:

Mini-grid:
- fuel delivery,
- operator-hand tank dip,
- operator-commanded override,
- maintenance visit.

Cold chain:
- product loading record,
- door inspection,
- batch context,
- service record.

E-mobility:
- charging session record,
- battery assignment,
- swap transaction,
- maintenance event.

Each may be:

- present and correct,
- delayed,
- missing,
- partial,
- contradictory.

This is required to make AssetOps claim ceilings demonstrable rather than merely
described.

---

# 13. Intervention and maintenance model

Maintenance and interventions modify:

- physical component state,
- component property/configuration,
- sensor/reporting state,
- topology where the intervention explicitly changes it.

They never set product conclusions.

Typed intervention categories:

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

Examples:

```text
Mini-grid
- change battery reserve
- service generator
- calibrate tank sensor
- replace starter relay
- add productive load
```

```text
Cold chain
- clean condenser
- replace compressor
- repair starter
- calibrate temperature sensor
```

```text
E-mobility
- replace charger module
- add charger
- change charging schedule
- replace battery pack
- add stationary BESS
```

Product rule preserved:

```text
work completed ≠ problem resolved
```

Only subsequent evidence may satisfy verification.

---

# 14. Asset stress and degradation

Use a pack-defined stress accumulator.

```text
StressAccumulator
- asset_ref
- dimensions
- accumulated exposure
- optional expected/reference band
```

Examples:

Battery:
- high-temperature exposure,
- deep discharge,
- high C-rate,
- high-SOC dwell,
- throughput.

Generator:
- runtime,
- starts,
- low-load operation,
- overload.

Compressor:
- start count,
- short cycling,
- runtime,
- difficult thermal lift,
- degraded efficiency.

E-mobility battery/charger:
- high-rate charge,
- high temperature,
- high-SOC dwell,
- deep cycling,
- sustained charger high load.

The simulator produces causal degradation/stress state. It does not need to
predict an exact failure date.

---

# 15. Counterfactual / paired experiment contract

v2 described paired runs but did not record the relationship. v3 makes the
relationship explicit.

## 15.1 `PairedExperiment`

```text
PairedExperiment
- experiment_id
- baseline_run_id
- intervention_run_id
- comparison_kind
- declared_intervention_delta
- shared_identity_projection_digest
- created_from
- status
```

The record is immutable once both run identities are frozen.

## 15.2 Not part of run identity

The pair record is **not** included in either run's deterministic identity.

Reason:

- associating two already-defined runs must not change either trajectory;
- the run must remain reproducible independently;
- pairing is comparison metadata, not physics.

## 15.3 Proving "all else equal"

The pair builder computes a projection of both frozen identities excluding only
the declared permitted difference.

Example:

```text
baseline:
BAT-001.minimum-reserve-soc = 25%

intervention:
BAT-001.minimum-reserve-soc = 32%

allowed delta:
POLICY_CHANGE BAT-001.minimum-reserve-soc 25% → 32%
```

The projected identities must otherwise hash identically.

If they differ in another uncontrolled field, the pair is rejected as
`NOT_COMPARABLE`.

## 15.4 More complex intervention

Example:

```text
add 12 kW mill from 10:00–15:00
```

Prefer representing this as a declared scenario intervention rather than
silently changing the baseline Foundation. Then weather realization, site
identity, policy, seed and all other inputs remain shared.

If an experiment genuinely requires a different Foundation version, the pair
must declare that broader difference and must not be described as a
single-variable comparison.

## 15.5 Product language

The UI should say:

> simulated intervention comparison

not:

> proven real-world causal impact

The simulator establishes causality inside the modeled world only.

---

# 16. Domain-pack contract

A domain pack declares or implements:

```text
DomainPack
├── model_profile
├── state_schema
├── discrete_state_specs
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

The shared kernel may not branch on:

- `site_kind`,
- generator/compressor/charger type,
- pack identity.

Structural checks should enforce:

- kernel imports no pack implementation,
- observation/gateway path has no domain-specific branch,
- pack registrations satisfy the same protocol,
- no `if site_kind == ...` inside shared mechanism.

This structural guidance does **not** remove the product control-vocabulary ban
described in §5.

---

# 17. Mini-grid proof sketch

Components:

- PV / inverter,
- battery / PCS,
- generator,
- fuel tank,
- AC bus,
- household load,
- critical load,
- productive load,
- devices/gateway.

Forcings:

- irradiance,
- demand profiles,
- productive-use schedules,
- faults,
- fuel movement.

Controller:

- reserve,
- start/stop thresholds,
- minimum runtime,
- source priority,
- critical-load protection.

Named physical flows:

```text
pv_to_load
pv_to_battery
battery_to_load
generator_to_load
generator_to_battery
curtailed_pv
unserved_load
```

Required demo recipes:

- healthy baseline,
- candidate avoidable generator runtime,
- fuel reconciliation gap,
- reserve violation,
- renewable headroom / productive-use opportunity,
- generator start failure,
- battery stress trajectory,
- evidence degradation,
- maintenance + verification.

---

# 18. Cold-chain proof sketch

Components:

- grid,
- optional PV/BESS,
- backup generator,
- compressor,
- cold-room thermal mass,
- door,
- sensors/gateway.

First-order thermal evolution:

```text
net heat
=
ambient gain
+ door gain
+ product/loading gain
+ defrost gain
- accepted compressor cooling
```

Controller:

- configured temperature band,
- compressor request,
- minimum cycle timing,
- backup behavior.

Recipes:

- normal operation,
- door-ajar excursion,
- compressor degradation,
- grid outage + backup start failure,
- slow cooling recovery,
- product loading,
- sensor drift,
- excessive cycling,
- effective maintenance,
- ineffective maintenance.

---

# 19. E-mobility proof sketch

Components:

- grid,
- optional PV,
- stationary BESS,
- chargers,
- vehicles/swappable packs,
- assignment/queue state,
- devices/gateway.

A charging request may declare:

- arrival,
- initial SOC,
- target SOC/requested energy,
- departure deadline,
- charge-acceptance limit,
- compatibility.

Controller/scheduler may decide:

- charger assignment,
- power allocation,
- BESS dispatch,
- time-of-use shifting,
- departure priority.

Physical resolver clips by:

- site limit,
- charger rating,
- battery acceptance,
- BESS limits,
- grid availability,
- fault/derate state.

Recipes:

- healthy depot,
- peak-cost charging inefficiency,
- charger unavailability,
- BESS underutilization,
- demand spike,
- missed departure target,
- battery stress,
- solar-aligned charging,
- maintenance intervention,
- fleet/capacity expansion.

---

# 20. Scenario and portfolio recipes

Scenario authoring is template-first and configures:

- world events,
- policy/config changes,
- faults,
- evidence conditions,
- operational records,
- interventions,
- interval,
- seed,
- private test expectations.

A scenario never specifies a Finding or financial conclusion.

Portfolio composition may generate:

```text
Meki   healthy benchmark
Kobo   avoidable runtime
Genda  fuel reconciliation
Bahir  service failure
Desta  productive-use opportunity
Arsi   battery stress trajectory
```

Each remains a normal independent Site/run history.

---

# 21. Truth, trace and replay

Private truth may include actual:

- cause,
- physical state,
- fuel movement,
- capability,
- failure,
- intervention effect.

It never enters normal product evidence.

Trace record kinds include:

```text
STEP
EVENT_APPLIED
CONTROL_INTENT
ACCEPTED_FLOW
DISCRETE_TRANSITION
BOUNDED_TRANSITION
DEVICE_OBSERVATION
GATEWAY_PUBLICATION
FAILURE
```

Simulator trace playback is a debug/reproducibility mechanism.

AssetOps Replay remains a historical view over recorded Site history and is not
re-simulation.

---

# 22. Business context

Money stays downstream of physics.

A versioned `BusinessContext` may hold:

```text
fuel price
energy tariff
time-of-use tariff
productive-use tariff
charging price
maintenance labour/travel cost
service-event cost
asset replacement value
product-value scenario band
downtime assumptions
```

AssetOps combines accepted operational evidence with these facts/assumptions to
produce bounded financial consequence.

A battery's `$38,000` replacement assumption is not a physical rating.

---

# 23. Execution-failure vocabulary

Execution failures are distinct from setup blocking/refusal.

Examples:

```text
ORDER_DEPENDENT_GROUP
BALANCE_IDENTITY_VIOLATION
PHYSICAL_RESOLUTION_FAILURE
UNSUPPORTED_MODEL_STATE
INTEGRATION_BOUND_FAILURE
TOPOLOGY_INCONSISTENT
NOT_COMPARABLE          # paired-experiment construction
```

Names and ownership should make it obvious whether a condition occurred during
setup, execution or comparison.

---

# 24. Build alignment

The following is programme sequencing, not task sizing.

## Prerequisites

1. **T020A**
   - component-addressed Foundation binding,
   - typed component control properties,
   - per-component property table.

2. **T020B**
   - boundary sampling semantics in §6.

3. **T021A**
   - parser narrowing already planned.

## Runtime programme

Then proceed through reviewable tasks covering:

- time/state/events,
- controller intent,
- physical resolver,
- observation,
- gateway staging,
- Commit/normal ingestion,
- first finding world,
- intervention/verification,
- productive-use comparison,
- stress/maintenance,
- cold-chain pack,
- e-mobility pack,
- portfolio recipes.

v3 does not redefine those as nine monolithic implementation tasks.

---

# 25. Acceptance tests

## Immediately/mechanically valuable

1. **Truth isolation**
   - remove private truth; committed product output is unchanged.

2. **Ingestion equivalence**
   - rebuild AssetOps output from committed envelopes without simulator runtime
     objects.

3. **Boundary semantics**
   - an event due at `T` is visible in a stock/discrete reading timestamped `T`.

4. **Interval measurement semantics**
   - a rate/energy measurement timestamped `T` represents the declared preceding
     interval.

5. **Controller/physics separation**
   - request 30 kW, accept 22 kW; both records remain distinct.

6. **RNG stability**
   - adding an unrelated stochastic stream does not alter existing streams.

7. **Component addressing**
   - two same-type loads/chargers resolve independently; unqualified ambiguous
     binding blocks.

8. **Numeric exactness**
   - no per-step denominator approximation occurs under `EXACT_RATIONAL`.

## Later product-level design tests

9. maintenance completion alone does not resolve a finding;

10. missing operational records reduce claim capability without changing truth;

11. gateway outage/recovery preserves source/gateway/received timestamp
    semantics;

12. a second domain pack introduces no branch in shared kernel;

13. `PairedExperiment` rejects undeclared identity differences;

14. portfolio recipes create independent Sites whose committed histories roll up
    normally.

---

# 26. Change log: v2 → v3

## V3-01 — Sampling semantics reconciled with T020B

**v2:** physical result and telemetry were placed at `t+dt`, but a reading at a
boundary could therefore precede events due at the same boundary.

**v3:** at boundary `T`, apply events first; then sample stocks/discrete state at
`T` while interval/rate values summarize `[T-dt,T)`.

**Justification:** preserves both requirements:
- no boundary sample sees pre-event state;
- telemetry can still describe the physical interval that just completed.

---

## V3-02 — Existing control-vocabulary ban explicitly preserved

**v2:** structural lexical-ban guidance could be misread as authorizing removal
of the product control-vocabulary ban.

**v3:** structural pack-isolation checks and product control-vocabulary safety
are explicitly different mechanisms.

**Immediate naming choices:**
- `door-ajar-excursion`
- `operator-hand-dip`
- `operator-commanded`
- `CONDUCTING / ISOLATED`
- `SEALED / AJAR`

**Justification:** naming is cheap; weakening a product evidence guard is not.

---

## V3-03 — Component addressing made a concrete T020A contract

**v2:** `StateRef` suggested component identity but did not say how built binding
contracts change.

**v3:** semantic `state_key` remains reusable; runtime `StateRef` carries scope
and component id. `FoundationBinding`, scenario refs and frozen initialization
carry the resolved address.

**Justification:** two loads or two chargers are normal, not edge cases.

---

## V3-04 — Policy ownership refined without repurposing `ControlAssumption`

**v2:** policy correctly moved to Foundation/Controls but did not account for
the existing `ControlAssumption` contract.

**v3:** leave `ControlAssumption` documentary; introduce typed component/site
control properties.

**Justification:** avoids silently turning a reviewed prose-assumption model
into a control model.

---

## V3-05 — Frozen identity clarification

No extra `policy` field is required.

Foundation version + ordered intervention history already freeze effective
policy.

---

## V3-06 — Composition-root wording strengthened

Simulator imports no `assetops_backend` package at all, matching the actual
guard.

---

## V3-07 — RNG algorithm pinned

BLAKE2b-256 + canonical encoding + explicit domain separation.

**Justification:** changing digest changes every stochastic trajectory, so it is
contract, not implementation trivia.

---

## V3-08 — Numeric policy selected

`EXACT_RATIONAL` is explicit and versioned.

The existing authored-float `_exact(...).limit_denominator(1_000_000)` boundary
is retained; per-step denominator limiting remains forbidden.

---

## V3-09 — Resolver/cascade rationale restored

The declared cascade is appropriate for current site-level control. More
complex simultaneous physics requires an explicit solver and tolerance contract
rather than an implementer quietly adding one.

---

## V3-10 — Discrete-state contract added

Initialization, allowed vocabulary, transitions, trace behavior and observation
mapping are specified.

---

## V3-11 — Paired experiment record added

The relationship between baseline and intervention runs is now recorded and
mechanically validated.

It is intentionally outside run identity.

---

## V3-12 — Dynamic initial-state ownership resolved

SOC, fuel level, room temperature, vehicle SOC and accumulated stress are
run-start dynamic conditions resolved by scenario/initial-condition ownership.

Unknown existing-asset stress does not default to zero.

---

## V3-13 — Build order aligned to current queue

T020A, T020B and T021A are prerequisites, not replaced work. v3 programme phases
must still be decomposed into the project's normal review-sized tasks.

---

# 27. Final architecture test

The design is successful if all of these remain true:

### Mini-grid

Can model:

- dispatch,
- fuel,
- productive use,
- service,
- battery stress,
- maintenance,

through normal source-envelope ingestion.

### Cold-chain

Can model:

- thermal dynamics,
- compressor degradation,
- backup failure,
- product-condition exposure,
- maintenance,

using the same kernel/time/evidence path.

### E-mobility

Can model:

- charging demand,
- battery SOC,
- charger/site constraints,
- scheduling,
- asset stress,
- throughput,

using the same kernel/time/evidence path.

If either later vertical requires:

- `if site_kind == ...` in shared kernel,
- a new time engine,
- a second ingestion contract,
- direct Observation→Evidence,
- product analytics inside the simulator,

then the seam is wrong and must be corrected rather than rationalized.
