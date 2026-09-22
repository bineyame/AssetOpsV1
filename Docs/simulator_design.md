# Simulator design

The engineering design for the AssetOps simulator: what it is for, how it is
built, and how its internals work. Written so an implementer can build from it
without re-deriving the reasoning behind it.

**Scope.** This is a design, not a task file. It sets no acceptance criteria,
no slice boundaries and no sizes; the Planner owns those. It also does not
re-argue strategy — `Docs/multi-vertical-capability-read.md` establishes what
exists today and `Docs/multi-vertical-build-plan.md` establishes the phases and
the six-layer seam model. This document is the layer-3 and layer-4 engineering
those two point at, plus the module structure that holds all six.

**Starting point.** `simulator/assetops_simulator/__init__.py` is thirteen
lines with an empty `__all__`. There is no kernel, no RNG and no numeric
dependency. Everything below is new code, and almost none of it is new
*contract* — section 2 is the inventory of what is already decided and binding.

---

## 1. Design goals

In priority order. Where two conflict, the higher one wins.

1. **Causal truth.** A world state changes because a declared cause moved it.
   Remove the cause and the consequence disappears; change it and the
   consequence changes; leave every unrelated frozen input alone and nothing
   else moves. This is the existing *Causal Runtime Authority* rule and it is
   the reason the simulator exists at all.
2. **Reproducibility.** The same frozen `DeterministicIdentity` plus the same
   kernel version produces byte-identical output, on any machine, forever. A
   run that cannot be reproduced cannot anchor evidence.
3. **Structural truth isolation.** Private world state must be unable to reach
   product evidence — prevented by module structure and CI guards, not by
   reviewer attention. Section 7.
4. **Additive widening.** Adding a modelled state, a sensor, a record type or a
   whole domain pack must not modify shared code. The seam model in the build
   plan is the target; section 8 is the mechanism.
5. **Honest refusal.** Where the kernel cannot decide something, it says so in
   a typed way and stops. There is no quiet clamp, no invented default and no
   partial output presented as complete. The existing `BOUND_POLICIES` already
   encodes this and the kernel inherits it.

**Non-goals**, stated because each is a plausible misreading:

- Not a power-systems simulator. No phasors, no load flow convergence, no
  transient stability. Simplified site-level balance only.
- Not real-time. Simulated time is decoupled from wall time.
- Not a findings engine. The simulator changes the world; AssetOps discovers
  the consequence. No scenario ever creates a Finding.
- Not a numerical solver. Section 5.4 explains why the coupled case is resolved
  by a declared cascade rather than an iterative solve, and what would have to
  change if that ever stops being enough.

---

## 2. What is already built, and therefore binding

The kernel is new; the contract it must conform to is not. Everything in this
table exists in code today and this design honours it as written. Section 9
lists the three places where the design asks a contract to grow, with costs.

| Contract | Where | What it binds |
| --- | --- | --- |
| `EXECUTION_CONTRACT_VERSION` | `scenarios/execution.py` | The version a run freezes and a kernel conforms to. Bump policy: a **narrowing** of the space a conforming kernel may occupy moves it; a pure widening off every executable path does not. |
| `DISPATCH_RULES` (7) | `scenarios/execution.py` | Half-open interval and steps; a point applies once; a window's active span; a quantity across a window; interval-wide entries; the intra-instant group rule; entries outside the interval. |
| T020B's four semantics | landing beside `DISPATCH_RULES` | A window quantity **ramps linearly** across the steps it spans; the observation transform **samples after due events are applied**; a forcing outside its window is **unavailable**, not zero and not held; a bounded change **lets the run continue** and later causes apply to the bounded value. |
| `BOUND_POLICIES` / `BOUND_CASES` | `scenarios/execution.py` | Three policies — `REFUSED_AT_PARSE`, `FAIL_RUN`, `BOUNDED_AND_RECORDED` — and deliberately no fourth meaning "clamp quietly". |
| `CANONICAL_UNITS`, `RATE_INTEGRALS`, `NON_NEGATIVE_DIMENSIONS` | `scenarios/execution.py` | Canonical dimensions, exact rational conversion factors, and which rates may be integrated into which quantities. |
| `DURATION_UNIT_SPELLINGS` | `scenarios/execution.py` | A duration has no unit to be written in, so no parameter can encode a cadence. |
| Initialization ownership | `execution.py`, `runs/models.py` | Four initialization owners mapping to answerers via `ANSWERER_BY_INITIALIZATION_OWNER`; `FROZEN_INPUT_ANSWERERS` carries five answerers in total, the fifth being `PUBLICATION_PROFILE` for the reporting path. |
| `DeterministicIdentity` | `runs/models.py` | Site and Foundation version, scenario version, interval, seed, both profile versions and the contract version, resolved initialization inputs, observation bindings, publication identity, signal mappings, ordered intervention history. |
| `FrozenInterval` | `runs/models.py` | Half-open `[start_time, end_time)` in UTC, `duration_minutes`, `timestep_minutes`, with the interval a whole multiple of the step. |
| Publication profile cadence | `runs/profiles.py` | The only source of a device-signal cadence; a Site fact structurally cannot reach it. |
| `ModelProfile.supported_states` | `runs/profiles.py` | Which states a profile models and in which roles; a required state it does not model blocks the run. |
| Projection versus composition | `.ai/ARCHITECTURE.md` | Projecting a document is static validation; composing projections into a value-at-a-time is a kernel. Whatever owns a transition rule is a kernel however narrow it is. |
| Dependency direction | `tools/checks/dependency-direction.ps1` | No UI→simulator, no simulator→product, **no product→simulator**. Section 4 is largely about the third. |

---

## 3. Architecture at a glance

The six layers from the build plan, with dependency direction and where the CI
guards sit.

```
                        ┌───────────────────────────────┐
   L6  Findings,        │  assessments (variant)        │
       financial bridge │  sufficiency, claim bounds    │
                        └───────────────▲───────────────┘
                                        │ reads accepted evidence only
                        ┌───────────────┴───────────────┐
   L5  Evidence         │  ingestion → accepted store   │
       (shared)         │  ▲ commit/release             │
                        │  │ Source Envelope (registry) │
                        └──┼────────────────────────────┘
                           │  ══ THE ONLY CROSSING ══
                        ┌──┴────────────────────────────┐
   L4  Devices,         │  observation transform        │
       sensors (shared) │  table: (state_key, signal)   │
                        └───────────────▲───────────────┘
                                        │ samples, never copies
   ─────────────────────────────────────┼────────────────── truth barrier
                        ┌───────────────┴───────────────┐
   L3  Kernel           │  kernel/  (shared mechanism)  │
                        │     ▲                          │
                        │     │ registry lookup only     │
                        │  packs/minigrid/ (variant)    │
                        └───────────────▲───────────────┘
                        ┌───────────────┴───────────────┐
   L2  Model profile    │  ModelProfile.supported_states │  ← already built
                        └───────────────▲───────────────┘
                        ┌───────────────┴───────────────┐
   L1  Vocabulary       │  state keys, component types,  │  ← already built
       (data)           │  units, property tables        │
                        └───────────────────────────────┘

Guards:  dependency-direction.ps1   bans L3→L5/L6 and L6→L3 (both ways)
         (new) pack-isolation       bans domain words outside packs/
         (new) truth-projection     bans the Lab truth type outside Lab modules
```

Read it as: **everything below the truth barrier is private and reproducible;
everything above it is evidence and may be wrong in the ways real evidence is
wrong.** Layer 4 is the only thing that touches both, and it samples rather
than copies.

---

## 4. Module structure, and the composition problem

### 4.1 The problem

`tools/checks/dependency-direction.ps1` bans *any* file under `backend/` from
importing `assetops_simulator`, in three regex forms including
`import_module`. That is correct and must not be weakened — its own header says
so. But it means the obvious design does not work: the backend cannot construct
a kernel, so `create_app` cannot wire one.

### 4.2 The resolution: a composition root outside both roots

```
simulator/assetops_simulator/
    kernel/                  shared mechanism  (section 5)
        state.py             WorldState: stocks, flows
        step.py              the four positions
        events.py            due-event resolution, intra-instant groups
        bounds.py            the three bound policies
        rng.py               seed substream derivation
        trace.py             trace records and identity binding
        registry.py          state_key → integrator, profile_id → pack
    packs/
        minigrid/            variant content  (section 8)
            resolver.py      phase 2 occupant
            integrators.py   per-state-key integration rules
            controller.py    dispatch/EMS, later

backend/assetops_backend/
    runs/ports.py            + RunExecutionPort  (domain records only)
    runs/models.py           + RuntimeProjection, Observation (domain records)

host/                        NEW. The only place that imports both.
    execution_adapter.py     implements RunExecutionPort over the kernel
    app.py                   create_app(..., run_execution=adapter)
```

Dependency arrows, and note that **no arrow points from `backend` to
`simulator`**:

```
        host/  ──────────────┬──────────────────┐
          │ imports          │ imports          │
          ▼                  ▼                  │
    assetops_backend    assetops_simulator      │
          │                  │                  │
          │  defines the     │  implements      │
          │  port ───────────┘  nothing of it   │
          │                                     │
          ▼                                     │
      FastAPI app  ◄─────── wired by ───────────┘
```

Three properties this buys:

- **The guard stays exactly as written**, and gains a fourth rule: nothing may
  import `host`. It is a leaf in the other direction.
- **`create_app` needs no structural change.** It already takes injected ports
  (`site_repository`, `scenario_repository`, `run_repository`). Execution
  becomes one more optional argument.
- **Today's honest state becomes the default.** With no execution adapter
  injected, the Lab reports execution unavailable — which is precisely what
  `/api/simulator-lab/status` returns today. The design's zero state is the
  current behaviour rather than a regression to it.

### 4.3 What crosses the port

`RunExecutionPort` speaks domain records owned by `runs/`, never simulator
types — the same rule `runs/ports.py` already holds for persistence ("no
`Path`, no file handle, no YAML text"). Concretely:

```python
class RunExecutionPort(Protocol):
    def start(self, run: SimulationRun) -> RuntimeHandle: ...
    def step(self, handle: RuntimeHandle, steps: int = 1) -> RuntimeProjection: ...
    def run_to_end(self, handle: RuntimeHandle) -> RuntimeProjection: ...
    def observations(self, handle: RuntimeHandle) -> Sequence[Observation]: ...
```

Two distinct return types, and the distinction is the truth barrier in the type
system: `RuntimeProjection` is Lab-only private state, `Observation` is what
layer 5 may consume. Section 7.

---

## 5. Internal mechanics

### 5.1 The state container: stocks and flows

Two kinds of quantity, and conflating them is the mistake the build plan's
amendment was written to prevent.

- A **stock** is integrated state that persists across steps: fuel volume,
  state of charge, chamber temperature, accumulated stress, cumulative energy.
- A **flow** is a rate prevailing over one step: fuel consumption, charge or
  discharge power, cooling power, curtailed power, served load.

```python
@dataclass(frozen=True)
class WorldState:
    simulation_time: str            # ISO instant, the step's start
    step_index: int
    stocks: Mapping[str, Fraction]  # state_key -> canonical value
    flows: Mapping[str, Fraction]   # state_key -> canonical rate, this step only
```

Both maps are keyed by `state_key`, which is already a free identifier in the
scenario parser, so a new state needs no parser change. Stocks carry forward;
flows are recomputed every step and never carry forward — a flow read in the
next step would be a persistence rule nobody declared, which is the same defect
T020B's *a forcing outside its window is unavailable* rule closes for forcings.

Why flows are first-class rather than derived on demand: every economic
quantity in the brief is a flow times a price, integrated. A kernel that emits
only stocks gives curtailed kWh and served kWh nowhere to come from, and the
first observable flow arrives in T022 — T020A's promotion of `dispatched-output`
gives the generator controller's `ac-power` signal something to publish, and
power is a flow.

### 5.2 The step: four positions

One step covers `[t, t + timestep)`. Four positions, in this order, and what
each may read and write:

```
  carry-in stocks S(t⁻)        from the previous step's integration
        │
  ┌─────▼──────────────────────────────────────────────────────┐
  │ ① EVENTS      apply causes due at instant t                │
  │               reads : S(t⁻), frozen scenario, interventions │
  │               writes: stocks                                │
  └─────┬──────────────────────────────────────────────────────┘
        │  S(t) — the state AT instant t
  ┌─────▼──────────────────────────────────────────────────────┐
  │ ② RESOLVE     compute this step's flows under limits        │
  │               and policy                                    │
  │               reads : S(t), forcings, Foundation limits,    │
  │                       policy, seeded substreams             │
  │               writes: flows  (stocks are READ-ONLY here)    │
  └─────┬──────────────────────────────────────────────────────┘
        │  S(t) + F[t, t+Δ)
  ┌─────▼──────────────────────────────────────────────────────┐
  │ ③ OBSERVE     sample, if this instant is a sample instant   │
  │               reads : S(t), flows                           │
  │               writes: NOTHING in the world  (emits records) │
  └─────┬──────────────────────────────────────────────────────┘
        │
  ┌─────▼──────────────────────────────────────────────────────┐
  │ ④ INTEGRATE   advance stocks over the step, under bounds    │
  │               reads : S(t), flows, declared bounds          │
  │               writes: stocks → S(t+Δ⁻)                      │
  └─────┬──────────────────────────────────────────────────────┘
        │
  carry-out stocks S(t+Δ⁻)     → next step's carry-in
```

**Why ③ sits between ② and ④, which is the subtlest decision in this design.**
T020B requires that the transform sample *after* the step's due events are
applied, so a boundary sample never sees pre-event state — that rules out
sampling before ①. Sampling after ④ would be wrong in a different way: a reading
labelled `t` would carry the state at `t + Δ`. Sampling between ② and ③ gives
the reading the stock *at instant t* and the flow *prevailing over the step
beginning at t*, which is what a level sensor and a power meter respectively
measure. Stocks are read-only in ②, so sampling there is identical to sampling
immediately after ① for stocks, and is the only position where flows exist at
all.

Phase ② is **not a stub in the fuel case.** It converts a forcing in kW into a
consumption flow in litres per minute via the model rule *specific consumption
times energy delivered*. It has one term today and a bus balance later; the
position is the commitment, the occupant is not.

### 5.3 Event dispatch: due, once, and grouped

Finding what is due follows `DISPATCH_RULES` exactly and needs no
interpretation:

- **Point entry**: due in the one step whose half-open span contains its
  offset. An offset exactly on a boundary belongs to the step that *begins*
  there. Implementation: `step_index = offset // timestep_minutes`, which gives
  that property for free and is why the interval must be a whole multiple of
  the step.
- **Window entry**: active for every step whose start lies in
  `[offset, offset + length)`. The step beginning exactly at the window's end
  is outside it.
- **Interval-wide entry**: offset zero until the interval ends.
- **Window quantity**: ramps linearly across the steps it spans (T020B), so a
  quantity `Q` over `n` steps contributes `Q/n` per step. `n` divides exactly
  because the window length is a whole number of steps, and `Fraction`
  arithmetic makes the sum land on `Q` exactly rather than on `Q ± 1e-15`.
- **Window rate**: multiplied by the step length and integrated via
  `RATE_INTEGRALS`, which is the only table that says what quantity a rate
  accumulates to.

**The intra-instant group** is the one rule with a decision in it. All effects
due at instant `t` on one `state_key` form a group with a net effect; the bound
is evaluated on the net, not between members; and the authored row order is
presentation and decides nothing.

```
  effects due at t on one state:   +40   −15   +5   −60
                                   ╰─ positive ─╯  ╰ negative ╯
  net        = S − 30
  max extreme = S + 45     ← tests the UPPER bound
  min extreme = S − 75     ← tests the LOWER bound

  ┌────────────────────────────────────────────────────────────┐
  │ neither extreme reaches a bound   → apply net. Order could  │
  │                                     not have mattered.      │
  │ the NET itself reaches a bound    → apply that bound's      │
  │                                     policy (5.5)            │
  │ an EXTREME reaches a bound while  → ORDER_DEPENDENT_GROUP:  │
  │ the net stays inside                the contract declines.  │
  │                                     Typed run failure,      │
  │                                     naming state and group. │
  └────────────────────────────────────────────────────────────┘
```

The third branch is a refusal, not an error to be smoothed. Two orderings that
reach different bounds are no more decidable than one that reaches a bound and
one that does not, and a scenario needing one thing before another says so by
separating the offsets.

### 5.4 Resolving flows when they are coupled

Fuel consumption is independent: it depends on its own forcing and a
coefficient. Everything in phase 2 of the build plan is not — state of charge
needs dispatch, dispatch needs generation and load, curtailment is the residual
of all three.

**The resolution is a declared, ordered cascade, not an iterative solve.**

```
  inputs: forcings (PV potential, demand), stocks (SOC, fuel),
          Foundation limits, policy

  ① available sources    PV potential, genset capability, grid availability
  ② priority allocation  serve load from sources in the policy's declared
                         order, clipping each at its limit
  ③ storage              absorb surplus into the battery up to charge limit,
                         SOC headroom and PCS limit; discharge to cover
                         deficit down to the reserve the policy declares
  ④ residuals            surplus that nothing absorbed  → curtailed-power
                         deficit that nothing covered   → unserved-load
  ⑤ identity check       Σ sources = Σ sinks, exactly, in Fractions
```

Three reasons this is right for this product rather than a shortcut:

- **It is what mini-grid dispatch actually is.** An EMS applies a priority
  order and limits; it does not solve a network.
- **It preserves exactness.** An iterative solver needs a convergence
  tolerance, and a tolerance is a floating-point quantity whose result can
  differ across platforms — which would break goal 2 outright.
- **It makes the policy visible.** The cascade's order *is* the policy, so
  "change policy → world changes → AssetOps discovers a different consequence"
  falls out of the structure rather than being bolted on.

Step ⑤ is a real assertion, not a comment: with `Fraction` arithmetic the
balance closes exactly, so a violation is a bug and the run fails rather than
reporting a world that does not add up.

**The known boundary.** A genuinely simultaneous case — droop control, a
voltage-dependent load, an AC network with real impedance — cannot be cascaded
and would need a solver, a tolerance and a numeric dependency. None of the
three verticals in the brief needs one. If one ever does, it replaces the
occupant of phase ②, not the step, and that is the whole point of the phase
being a named position.

### 5.5 Integration and bounds

Integration is `stock += flow × timestep`, in `Fraction`, then the declared
bounds are applied under `BOUND_CASES`. The three policies already exist and
the kernel implements them literally:

- `REFUSED_AT_PARSE` — never reaches the kernel; the parser already enforces it
  end to end.
- `FAIL_RUN` — a typed execution failure naming the entry and the bound. The
  run reaches `FAILED` with an inspectable reason and does **not** display
  partial output as complete.
- `BOUNDED_AND_RECORDED` — the stock lands on the bound and a **bounded
  transition record** is emitted carrying the quantity refused. Per T020B the
  run then continues, and later causes apply to the bounded value; recording a
  refused quantity only means something if the run goes on.

The bounded transition is a first-class trace record, not a log line, because
a delivery that partly did not fit is a fact a later analysis must be able to
see — the alternative is fuel that arrives in the record and never in the tank.

There is deliberately no fourth policy. A kernel that clamped quietly would
produce a trajectory nothing in the evidence path could account for.

### 5.6 Exact arithmetic

All world quantities are `fractions.Fraction`. Conversion to `float` happens
exactly once, at the boundary where a trace record or an observation is
emitted.

This is not a preference; it is inherited. `CanonicalUnit` already carries its
factor as an exact ratio for a stated reason: fourteen litres an hour over four
hours is fifty-six litres, and through binary floats it is
`56.00000000000001`, which a screen would render as a precision the scenario
does not have. A kernel using floats would reintroduce exactly that.

Consequences worth stating:

- **No numpy, no scipy.** Exact rational arithmetic does not vectorise, and at
  this scale — one site, minute resolution, a handful of states — it does not
  need to. The repository's current absence of a numeric dependency is
  preserved deliberately rather than by accident.
- `Fraction` denominators grow under repeated addition. Normalise at each step
  boundary with the same `limit_denominator(1_000_000)` that `_exact` already
  uses, so a long run cannot degrade into unbounded integers.

### 5.7 Determinism and the seed

The seed is frozen on `DeterministicIdentity` today and nothing consumes it,
because nothing yet draws a random number. The first consumers are seeded
forcing variation in phase ② and sensor realism in layer 4.

**A single global PRNG would be wrong**, and the reason is specific: draws
happen in whatever order states are visited, so adding one noisy signal shifts
every subsequent draw and silently changes every previously recorded
trajectory. Reproducibility would hold only for a frozen feature set, which is
not reproducibility.

Instead, derive an independent substream per purpose:

```
  substream(seed, stream_name, step_index)
      = blake2b( seed ‖ stream_name ‖ step_index ).digest()
        → uniform draw

  stream_name examples:
      "forcing:site-load-demand"
      "sensor-noise:fuel-level-sensor:fuel-level"
      "sensor-bias:fuel-level-sensor:fuel-level"
```

Properties: adding a stream perturbs no existing stream; streams are
independent; a draw is a pure function of the frozen seed, the stream name and
the step index, so a step can be recomputed in isolation. `blake2b` rather than
Python's `hash()`, which is salted per process and would make runs
irreproducible across invocations.

### 5.8 The trace and its identity binding

A trace is a reproducible output of a named kernel version against one frozen
identity. It is a regression and playback artifact and is **never** an
alternate source of world truth — that is an existing architecture rule and it
is why traces may only be generated, never authored.

```
  TraceHeader
    identity_digest      blake2b over the canonical serialization of
                         DeterministicIdentity
    kernel_version       semantic version of the kernel
    contract_version     EXECUTION_CONTRACT_VERSION at generation
    model_profile        id + version
  TraceRecord*  (ordered, one or more per step)
    STEP                 step index, simulation time, stocks, flows
    EVENT_APPLIED        entry id, state key, applied quantity
    BOUNDED_TRANSITION   state key, bound case, quantity refused
    OBSERVATION_SAMPLED  source id, state key, sampled value
    FAILURE              typed reason, entry id
```

Replay recomputes `identity_digest` from the run record and refuses if it
differs. That makes "this trace belongs to this run" a checked property rather
than a filename convention, and it is what stops a trace surviving a change to
the inputs that produced it.

---

## 6. The observation transform

Layer 4, wholly shared, and the only component that touches both sides of the
truth barrier.

```
   private world              transform                  emitted
   ───────────────            ─────────                  ───────
   stocks{fuel-tank-volume}   ┌──────────────────┐
   flows {generator-power} ──►│ row lookup:      │
                              │ (state_key,      │
   publication profile ──────►│  device, signal) │──► Observation
     cadence = 15 min         │ cadence gate     │     source_time
                              │ reporting avail. │     value (float)
   frozen signal mappings ───►│ noise / bias     │     quality flags
                              │ quantization     │
   seeded substreams ────────►│ drop / delay     │
                              └──────────────────┘
```

Four rules, each of which already has a reason on the record:

1. **It samples; it never copies.** Truth exists at every step; a reading
   exists only at a sample instant. These are different objects with different
   lifetimes, and the transform's output is a distinct record, not a view of
   state.
2. **Cadence comes only from the publication profile.** Never from Foundation,
   never from a device name, never from the spacing of authored rows —
   `runs/profiles.py` enforces this structurally and `tools/checks/run-setup.ps1`
   fails the build if the frozen binding is constructed elsewhere.
3. **It is a table keyed by `(state_key, device, signal)`, not code that knows
   about fuel.** A compressor probe or a charger power meter is then a row plus
   a Foundation mapping, with no simulator code at all. This is the single
   largest reuse claim in the design.
4. **It samples stocks and flows alike.** A level sensor reads a stock, a power
   meter reads a flow, an energy meter reads an integrated flow. A transform
   that only knows how to sample a stored quantity is the stock-only defect one
   layer up.

Sensor realism — noise, bias, quantization, latency, gaps, duplicates,
out-of-order, clock drift — enters as **columns on a row**, not as new code
paths, each drawing from its own named substream. A reporting-path forcing
changes what is reported without changing what is true, which is the cleanest
demonstration available that the two are different objects.

---

## 7. The truth barrier

Structural, in three independent mechanisms. Any one of them failing leaves the
other two standing.

```
   private world state ──► RuntimeProjection ──► Lab UI only  (gated)
          │
          └──► observation transform ──► Observation ──► envelope ──► ingestion
                                                                        │
                                                                        ▼
                                                              accepted evidence
                                                                        │
                                                                        ▼
                                                        operator views, analytics,
                                                              Replay, findings
   ════════════════════════════════════════════════════════════════════════
   Nothing on the lower path can reach the upper one. There is no edge.
```

1. **Module direction.** No file under `backend/` may import
   `assetops_simulator`, in any of three forms including `import_module`. The
   product literally cannot name a simulator type, so a truth value cannot
   appear in a product read model even by accident. Section 4 is what makes
   this survivable.
2. **Type separation at the port.** `RuntimeProjection` (private, Lab-only) and
   `Observation` (evidence-eligible) are different domain types. Layer 5
   accepts only the second. A new CI guard in the style of the existing
   `sldViewModel` field-name ban should reject any reference to
   `RuntimeProjection` outside the gated Lab modules.
3. **The gate.** Simulator surfaces and execution are gated by
   `simulator_lab.enabled`; a gate-off build serves no Lab route, action or
   API. Existing simulated Sites and accepted evidence stay visible, because
   they are product history rather than simulator execution.

The oracle side is the same barrier read backwards. `PrivateExpectation`
already carries `oracle_kind ∈ {DETECTION, MAGNITUDE, NO_FALSE_POSITIVE,
TIMING}` and is served under its own payload key. An expectation is legitimate
where being wrong causes a failure and circular where being wrong causes
agreement — so the kernel never reads one, and only the test suite compares
truth against what AssetOps concluded.

---

## 8. How a domain pack plugs in

A pack is **a model profile plus the rules behind it**, and nothing else.

```
  ┌─────────────────────────── SHARED ───────────────────────────┐
  │  kernel/      step, state, events, bounds, rng, trace         │
  │  transform    table-driven, sensor realism                    │
  │  envelope     registry of typed records                       │
  │  ingestion    acceptance, rejection, accepted store           │
  │  findings     sufficiency, claim bounds, financial bridge     │
  └───────────────────────────▲──────────────────────────────────┘
                              │  registry lookup by model_profile_id
  ┌───────────────────────────┴──────────────────────────────────┐
  │                        A DOMAIN PACK                          │
  │                                                               │
  │  DATA (no code)          CODE (pack-local only)               │
  │  ─────────────           ────────────────────────             │
  │  state keys              phase ② resolver                     │
  │  component types         per-state integrators                │
  │  property tables         controller                            │
  │  topology roles          assessments (L6)                     │
  │  transform rows                                               │
  │  record types                                                 │
  │  a ModelProfile                                               │
  └───────────────────────────────────────────────────────────────┘
```

Registration is data, not a plugin framework: `MODEL_PROFILES` is already a
tuple resolved by identity and version, and a pack registers its resolver and
integrators against a `model_profile_id` in `kernel/registry.py`. The kernel
imports nothing from `packs/`.

**The mechanical test that keeps this honest**, worth a CI guard once a second
pack exists: no shared module contains `generator`, `fuel`, `charger` or
`compressor` outside a `packs/` directory. It would pass trivially today, which
is the right time to add it.

**The prediction this design makes, recorded so it can be checked rather than
rationalised later:** a second vertical costs four to six slices. If it costs
fifteen, the seam was wrong, and it will have been wrong in layer 3 or layer 5.

---

## 9. What this design asks of the built contracts

Three requests, stated explicitly rather than made silently. None is required
before T021; all three are named here so the cost is visible when they arrive.

| Ask | Where | Cost |
| --- | --- | --- |
| **A state may be a flow, not only a stock.** `SupportedState` declares what a profile models; it has no way to say whether a state is integrated or rate-valued, and the transform and trace both need to know. | `runs/profiles.py` | One field on `SupportedState`. A *widening*, off every currently executable path — under the stated bump policy it does **not** move `EXECUTION_CONTRACT_VERSION`. |
| **Typed execution failures need a vocabulary.** `ORDER_DEPENDENT_GROUP`, `FAIL_RUN` bound cases and balance-identity violations are run outcomes that no existing frozenset covers. `BLOCKING_REASON_KINDS` is explicitly about run *setup* and a seventh member was removed to keep it so — this must not be bolted there. | new, beside `refusals.py` | A third vocabulary, disjoint from the refusal and blocking sets, obeying the existing naming rule: from the name alone, which side of the line is it on? |
| **`RUN_LIFECYCLE_STATUSES` is `frozenset({"DRAFT"})`.** Execution needs `RUNNING`, `PAUSED`, `COMPLETED`, `FAILED`. | `runs/models.py` | T022 already owns this; noted so it is not mistaken for new. |

And one that is **not** requested: the kernel does not need `DISPATCH_RULES`,
`BOUND_CASES` or `CANONICAL_UNITS` to change at all. It conforms to them as
written. That is the strongest evidence that the contract work of T017–T020B
was the right thing to do first.

---

## 10. Where the two open questions land

Both are user decisions, named here with their landing sites and left open.

**The fifth property owner, for policy.** Policy is the ordered cascade in
phase ② — reserve, genset start SOC, minimum runtime, critical-load priority.
It is neither what the site *is* (Foundation), how the simulator *reasons*
(model profile), what *happens* in one interval (scenario), nor how the
installation *reports* (publication profile). Its landing site is precise:
`DeterministicIdentity` gains a frozen `policy` field, `FROZEN_INPUT_ANSWERERS`
gains a sixth member, and run setup resolves and freezes it like any other
answered value. Deciding it costs a frozen-record field and a version move;
deferring it past the first controller costs a retrofit of every trace already
bound to an identity without it. The decision is due when phase ② first has a
controller in it, not before.

**The monetary dimension.** Two candidate sites and they are not the same
choice. Either `CANONICAL_UNITS` admits a money dimension — which puts prices
inside the scenario parameter vocabulary and therefore inside physics, against
the brief's explicit instruction to keep them separate — or layer 6 carries its
own unit table and Foundation carries asset replacement value as a component
property with a money `RATING_UNIT`. The second is almost certainly right, but
it is a product decision and this document does not take it. What can be said
now: **the kernel never sees money in either case.** Economics is downstream of
evidence, and the simulator supplies quantities, not value.

---

## 11. Build order

Not restated — `Docs/multi-vertical-build-plan.md` section 4 has the phases and
section 6 has what changes in the current queue. Two pointers only:

- Sections 5.1 through 5.8 and section 4 are what T021 builds, at the narrowest
  scope that exercises them: one modelled state, one term in phase ②.
- Section 6 is T022. Section 8's pack split costs nothing to adopt in T021
  because the directories do not yet exist, and it is what makes the isolation
  guard writable once instead of retrofitted.

The design's own test of whether it was right is in section 8, and it is
falsifiable.
