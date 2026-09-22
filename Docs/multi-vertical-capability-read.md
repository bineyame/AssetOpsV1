# Multi-vertical capability read

An Architect response to the multi-vertical demo strategy and 23-family
simulator capability inventory brought in on 2026-09-23.

This is analysis, not a decision and not a plan. Nothing here is recorded in
`.ai/DECISIONS.md`, no task file is edited, and no slice changes until the user
says so. Read it as a second opinion on a strategy document, grounded in what
the repository contains today.

---

## 1. The fact that reframes the whole brief

`simulator/assetops_simulator/__init__.py` is thirteen lines long and its
`__all__` is empty. It has been that way since T001. Its own docstring says
"there is no simulated world, no run execution, and no published output," and
that is still literally true on `main` at `54bcc01`.

There is no simulator. There is a very good *contract for* a simulator.

Four more facts in the same direction, each independently checkable:
`RUN_LIFECYCLE_STATUSES` is `frozenset({"DRAFT"})` — there is no `RUNNING`, no
`COMPLETED`, no `FAILED`. The seed is frozen on every run record and nothing
consumes it, because there is no RNG anywhere in the repository.
`/api/simulator-lab/status` returns, literally, `{"run_execution":
"not_implemented", "truth_overlays": "not_implemented"}`. And the backend has
no numeric dependency at all — no numpy, no scipy, no pandas — which is worth
knowing before anyone scopes a power-flow solver or a first-order thermal
model.

Everything built so far — T001 through T020 — is authoring vocabulary, run
setup, persistence, provenance and presentation. Sites, Foundations, topology,
devices, signal mappings, single-line diagrams, a scenario document format with
execution roles, a frozen deterministic run identity, a runs inventory, a run
detail shell. Not one line of physics. The first line of physics is T021, and
it moves a fuel tank.

The brief says "your existing simulator direction already supports this well."
That is true of the *direction* and false of the *inventory*, and the gap
between those two readings is large enough to make a plan built on the brief's
premise land three to six months early. Section 3 is the itemisation.

---

## 2. Reconciling the two answers you have been given

Hours ago I told you: the simulator ends at T022; the first kernel models a
fuel tank, a forced generator output and fuel consumption and nothing else; PV,
battery, load and dispatch are not on any roadmap; do not widen the kernel;
more physical realism never gets you to findings faster; the gate to the
findings layer is the evidence path, not physics.

The brief asks for power flow, battery degradation, thermal models, compressor
models, charging schedulers, portfolio generation and what-if comparison.

**I am not retracting the earlier advice, and it is the one that applies to the
next three months.** The reason is narrow and checkable rather than a matter of
taste: the first finding this product will produce is unaccounted fuel
variance, and it reads a fuel level series, a generator runtime or dispatch
record, a Foundation consumption coefficient, and fuel delivery records. It
reads no power flow, no state of charge, no irradiance and no temperature. The
thing standing between you and that finding is not the richness of the world
model. It is that nothing has ever crossed from a simulated world into accepted
product evidence — `T023` staged envelopes, `T024–T026` commit and ingestion,
`T027–T029` evidence views and Replay, `T034–T038` the conclusion chain. That
is eleven unwritten slices of plumbing and zero of them are physics.

**Three places the earlier advice was too flat, and I should say so.**

- *"PV, battery, load and dispatch are not on any roadmap"* was accurate about
  task files and misleading as a statement about the product. `COMPONENT_TYPES`
  in `backend/assetops_backend/sites/models.py` already contains `PV_ARRAY`,
  `INVERTER`, `BATTERY`, `POWER_CONVERSION_SYSTEM`, `AC_BUS`, `LOAD` and
  `COLD_ROOM`; `SITE_TYPES` already contains `COLDCHAIN`; the shipped Fuel Loss
  document already declares `site-load-demand` and `plane-of-array-irradiance`
  as required forcing inputs; `.ai/PRODUCT.md` carries `Demo Ready v1.5:
  Cold-Chain Evidence Loop` as a named milestone and `.ai/FEATURE_MAP.md`
  reserves `T030–T033` for it. The product has always intended to get there.
  What has no roadmap is the *physics*, which is a different and smaller claim.
- *"Do not widen the kernel"* is right about scope and says nothing about
  shape, and shape is where the brief has a real point. A kernel whose step is
  fuel-tank-shaped and a kernel whose step dispatches on `state_key` cost the
  same to write in T021 and differ by a rewrite afterwards. Section 6 names the
  two places where that matters and what each costs.
- *"More physical realism never gets you to findings faster"* is true and was
  answering a question about the shortest path. The brief introduces a fact I
  did not have — two meetings with two named people — which changes the
  *deadline*, not the sequence. A deadline you cannot reach by building is
  reached by narrating, and section 4 is about that.

**And one place the brief is larger than the commercial situation requires.**
Twenty-three capability families is a platform inventory. You have two
conversations with two former colleagues, one of which is explicitly
exploratory. The number of families either meeting requires is closer to zero
than to twenty-three, because neither meeting's stated objective is a product
demonstration: the mini-grid objective is *find the first real site or
historical data set* and the e-mobility objective is *find out whether the
abstraction transfers*. Both are discovery. Build for a discovery meeting and
you have pre-committed the answer you went there to learn.

---

## 3. What actually exists, family by family

Four verdicts. **Built** means code on `main` that runs. **Specified** means a
task file in `tasks/` commits to it. **Map** means it is named in
`.ai/FEATURE_MAP.md` or `.ai/PRODUCT.md` roadmap ranges only. **Absent** means
nothing anywhere.

A fifth distinction does most of the work and has no single word: several
families have a **built contract with no model behind it**. The document format
can declare the thing, the parser enforces it, the run record freezes it, the
screen shows it — and nothing computes it. That is a genuine asset and it is
not the same asset the brief thinks it is.

| # | Family | Verdict | What is actually there |
| --- | --- | --- | --- |
| 1 | Common physical-world engine | Contract built, engine specified | Interval, timestep, seed and timezone are frozen on the run record (T019, `runs/models.py`). Step semantics are declared in T020B. The loop itself is T021; pause/step/fast-forward is T022. Component-level state: absent. |
| 2 | Electrical power-flow model | Absent | Foundation *declares* PV, inverter, battery, PCS, AC bus, load components with ratings and topology, and the SLD draws them (T014–T016, built). Nothing computes a flow, a bus balance, curtailment or unserved load. No slice proposes to. |
| 3 | Environment / forcing engine | Contract built, engine absent | `FORCING_INPUT` is a real execution role; the shipped scenario declares `site-load-demand` and `plane-of-array-irradiance` with windows and profiles. `MINIMAL_FUEL_TANK_MODEL` supports neither, so the run blocks — correctly. No environment engine exists. |
| 4 | Generic load model with classes | Absent | `LOAD` component type and the `site-load-demand` state key are declarable. No classes, no profiles, no controllability. |
| 5 | Battery model as shared service | Absent | `BATTERY` component type declarable. No SOC, no limits, no efficiency, no degradation, no pool. |
| 6 | Generator model | Partial, specified | T020A promotes `dispatched-output` to a forcing input on `generator-output-power` and moves specific fuel consumption to Foundation as `L/kWh`. No state machine, no start delay, no min runtime, no start failures, no availability. |
| 7 | Fuel system model | Specified (T021/T022) | The nearest thing to real. T021 computes tank volume under a capacity bound; T022 makes truth and reading two distinct objects. Deliveries, manual dips and a declared reading error are partly in the authoring vocabulary; sensor bias and calibration error are absent. |
| 8 | Thermal model (cold-chain) | Map only | `COLD_ROOM` component type exists, `MG-002` is a cold-room fixture Site, `T030–T033` is reserved. No model. |
| 9 | Compressor model | Map only | Same range, nothing built. |
| 10 | E-mobility charging model | Absent | No component types, no state keys, no roadmap range, no mention anywhere in `.ai/`. |
| 11 | Charger / depot controller | Absent | As above. No controller of any kind exists for any vertical. |
| 12 | Operational-policy engine | Absent, and the seam is missing too | Worth flagging: `.ai/ARCHITECTURE.md`'s *Physical Property Ownership* names four owners — Foundation, model profile, scenario, publication profile. None of them is a policy. The brief's headline demo mechanic ("change policy → world changes → AssetOps discovers a different consequence") has no home in the current contract. It does not need one yet, because there is no controller for a policy to configure. |
| 13 | Stress accumulator | Absent | No degradation state anywhere. |
| 14 | Maintenance model | Taxonomy only | `EVENT_CATEGORIES` includes `MAINTENANCE` and the shipped document authors a `scheduled-refuelling` entry. Nothing models a maintenance effect on efficiency, reliability, bias or fault probability. |
| 15 | Failure / degradation injection | Contract built, partial | `unaccounted-fuel-removal` and `fuel-level-reporting-gap` are typed authored causes in the shipped document and they parse. Runtime injection is specified as run-scoped intervention history; nothing injects yet. |
| 16 | Commercial / operational record simulation | Contract built, model absent | `OPERATOR_RECORD` is a real source kind; T022 makes the operator's hand reading a run-local generated observation rather than an authored number. Deliveries, tariffs, customer categories, maintenance visits: absent. |
| 17 | Device / sensor realism | Contract partly built, model absent | The cadence seam is real and well defended — `runs/profiles.py` resolves it from the publication profile and a CI check fails the build if the record is constructed anywhere else. A reporting gap is declarable, and `DURATION_UNIT_SPELLINGS` refuses `min`/`h`/`s` as any parameter unit so an author cannot smuggle a sampling rate in. Noise, bias, quantization, latency, duplicates, out-of-order, clock drift: no code, no task file. |
| 18 | Gateway / ingestion emulation | Specified (T023) then map (T024–T026) | `simulator_source_id` and `gateway_id` are frozen on the run record today. No `Envelope` class exists in the codebase — the word appears only in prose. Ingestion, acceptance, rejection and `received_at`: map only. |
| 19 | Scenario recipe packs | Absent | One shipped scenario, `config/scenarios/fuel-loss-event.yaml`. No pack concept, no second scenario, no authoring UI. |
| 20 | What-if / intervention comparison | Absent, prerequisite built | The frozen deterministic identity is exactly what makes clone-and-vary cheap later, and it exists. The comparison does not. |
| 21 | Multi-site portfolio generation | Absent, substrate built | Three fixture sites, a Sites index, a shared presentation substrate. No generation, no portfolio view, no operating personalities. |
| 22 | Ground-truth oracle | Contract built, strongly | The best-defended thing in the repository. The public/private parameter boundary (T017/T018), the rule that a scenario may carry oracles and may not carry consequences, the architecture rule that private truth never crosses into envelopes, and a CI architecture guard on the dependency direction. `PrivateExpectation` already carries `oracle_kind ∈ {DETECTION, MAGNITUDE, NO_FALSE_POSITIVE, TIMING}` and is served under its own payload key. There is no `SimulationTruth` class, because nothing runs; the separation is a parser-enforced vocabulary, and nothing evaluates the oracles yet. |
| 23 | Cross-domain economic configuration | Absent | No tariff, fuel price, service cost, replacement value or revenue anywhere in the domain. `CANONICAL_UNITS`, `PARAMETER_UNITS` and `RATING_UNITS` are closed and physical — `L, L/h, kW, kWh, kVA, V, A, Hz, degC, W/m2, %` — with no monetary dimension, so economics is a unit-system change and not just a new field. |

Counting it: roughly two families are genuinely built, six are a built contract
over an absent model, four are specified in a live task file, three are map
only, and eight are absent in every sense. Nothing in the physical-model half
of the brief — families 2, 4, 5, 8, 9, 10, 11, 12, 13 — exists at all.

**The honest one-line summary for the user.** The brief is right about the
architecture and wrong about the inventory. What you have is a domain-neutral
authoring, provenance and honesty contract that is unusually well built for
this stage. What you do not have is any physics, any device, any envelope, any
ingestion, any evidence store and any finding.

---

## 4. What the two meetings actually require

### Mini-grid: the artifact is not a demo, it is a thesis plus a shopping list

The brief proposes 70% demo. Today a demo means: Sites index, Site detail and
Foundation, topology and devices, a configured single-line diagram, the
scenario catalog, the Fuel Loss document, run setup, the runs inventory, and a
Draft run whose Run button is disabled. That is a genuinely impressive
configuration product and it shows zero operational evidence, because
`.ai/PRODUCT.md`'s prohibited-claims list forbids exactly that until accepted
evidence exists — no charts, no health, no fuel variance, no findings.

So the mini-grid meeting has two honest shapes and you should pick one
deliberately:

- **Walk the built screens and narrate the finding.** Show the configuration
  depth, which is real and is the part most competitors fake. Then show the
  finding as an explicitly labelled storyboard — "this is what the product will
  say, here is the evidence it will say it from, here is why it will not say it
  until it can." That labelling is not a weakness in front of an operator; it
  is the product's actual thesis made visible. This is available today.
- **Wait for Demo Ready v1 plus the first finding.** That is `T023–T029` and
  `T034–T038`. Do not plan the meeting around it.

**The thing I would push hardest on.** The meeting's stated objective is a real
site or a historical data set, and that is an *input*, not something a demo
produces. A historical mini-grid data set — fuel dips, delivery records,
generator runtime logs, a tank sensor series — would let you produce the first
finding *with no simulator at all*. The ingestion path in `T023–T026` does not
care whether its records came from a simulated device or from a spreadsheet a
site manager emailed you. If that meeting lands a data set, the fastest route
to a first finding changes shape entirely and the simulator becomes a
regression harness rather than a critical path. That possibility is worth going
into the meeting wanting more than a warm reception.

The right question to ask is the one the brief already has: *which of these
problems is genuinely painful today?* Add one: *would you give me six months of
whatever records you already keep?*

### E-mobility: build nothing

The brief itself says 40% discovery and frames the meeting as "tell me where it
breaks." The deliverable of that conversation is a list of ways the abstraction
fails. An adapted mockup is the right artifact and a real run is the wrong one,
for three reasons:

- Anything you build first encodes a guess about a depot's operating model, and
  the guess will be shown to the one person who can correct it, which converts
  a discovery conversation into a critique of your guess.
- The shared conceptual core in the brief — asset → telemetry and records →
  observed behaviour → deviation → operational consequence → financial
  consequence → intervention → verification — is a slide. It is also, and this
  is the interesting part, an accurate description of what `T017–T029` builds.
  You can show the mini-grid instance of it on screen and talk about the
  abstraction in the same breath.
- A charger model costs weeks. Discovering that depot operators care about
  missed departure deadlines rather than kWh costs one question.

The one thing worth preparing: two or three static frames that re-label the
built mini-grid screens with depot vocabulary — chargers where generators are,
sessions where dispatch windows are, a missed-departure finding where the fuel
variance finding is. Half a day of design work, no code, clearly marked as a
sketch. If the meeting says the abstraction holds, those frames become the
first e-mobility feature map. If it says it breaks, you have lost half a day.

---

## 5. How the capability set could be achieved, if you decide to

### What is genuinely shared, and it is not power flow

The brief's claim that the electrical power-flow model is "70%+ of the useful
foundation across the three verticals" puts a defensible number on the wrong
family. Test it against the three wedges:

- Mini-grid's wedge is fuel: consumption against dispatch, variance, theft or
  leak or mis-recording. Power flow is context, not the computation.
- Cold-chain's wedge is temperature excursion and spoilage exposure. Power flow
  matters only as *was the compressor powered*, which is one availability
  signal, not a flow model.
- E-mobility's wedge, per the brief's own metrics, is sessions per day, missed
  sessions, queue wait, energy cost and throughput. That is scheduling and
  session accounting under a site power limit — one scalar constraint, not a
  bus balance.

Power flow is the mini-grid pack's largest single item. It is not the kernel's.

What *is* 70% shared is the skeleton that has no domain content in it at all:
family 1 (deterministic time, state, step ordering), family 3's forcing
mechanism (not its physics), family 17 (a device samples a state through a
transform at a cadence), family 18 (envelope, gateway, ingestion), family 22
(truth versus observed versus claimed), family 16's record mechanism, family 20
(clone a frozen identity and vary one input), and family 23 (economics held
separate from physics). Those eight are the kernel. They are also, with the
exception of 20 and 23, exactly the eight the current roadmap already
sequences. That is a strong result: **the existing plan is already building the
shared 70%, and it is building it for mini-grid because you have to build it
for something.**

### The seam that makes packs possible already exists

Two things in the code deserve to be named, because they are why this is
achievable at all and why almost none of it needs doing now:

- `state_key` is parsed as a free identifier, not a closed vocabulary
  (`scenarios/parsing.py`, `_require_identifier`). A new domain adds
  `chamber-air-temperature` or `charger-session-energy` without touching the
  parser.
- `ModelProfile.supported_states` in `backend/assetops_backend/runs/profiles.py`
  is a tuple of `SupportedState(state_key, supported_roles,
  foundation_binding, statement)`. A domain pack *is* a model profile plus the
  transition rules for its state keys. Widening is additive by construction,
  and a scenario that needs a state the profile does not model already blocks
  with a reason naming it.

That is the domain-pack boundary, in code, today, with a CI guard on the
dependency direction and a run-setup check that fails the build if a Site fact
reaches a cadence. Nobody planned it as a multi-vertical seam and it is one.

### Sequencing, if the three verticals are ever actually wanted

One ordering principle: **a pack is worth building only after the evidence path
it plugs into has carried one finding end to end.** Before that, a pack is a
world model with nowhere to send its output.

1. Finish the mini-grid path to one finding: `T021`, `T022`, `T023–T026`,
   `T027–T029`, `T034–T038`. This builds seven of the eight shared families as
   a side effect.
2. Harvest the seam, do not design it. After the first finding, look at what
   the fuel pack needed and factor the parts that were obviously generic. That
   is a refactor against evidence, which is what
   `D-2026-09-22-milestone-speed-over-purity` explicitly schedules for after
   milestone completion.
3. Second pack second, chosen by whichever meeting produced a real contact and
   a real pain, not by which one has the nicer physics.
4. Families 19, 20, 21, 23 — recipe packs, what-if comparison, portfolio
   generation, economics — are the demo-polish layer and are cheap once a
   finding exists and the run identity is frozen, which it already is. They are
   ornament before then, and expensive ornament, because each one needs a world
   to operate on.

### Load-bearing versus ornament for the first finding

Load-bearing: 1 (narrow), 7, 16 (minimal), 17 (cadence and gap; bias is what
makes the finding *interesting* rather than arithmetic), 18, 22. Six families,
four of which have a built contract already.

Ornament until much later: 2, 4, 5, 8, 9, 10, 11, 12, 13, 14, 19, 20, 21, 23.
Fourteen families, none of which the first finding reads.

---

## 6. Slice by slice: what changes

The standing direction is speed over pedantic purity, and a premature
abstraction is not free. So the default answer below is *nothing changes*, and
I only depart from it where a seam is meaningfully cheaper now than as a
retrofit.

### T020A — Foundation physical properties and model-rule carriers

**Nothing changes, and it is already the most multi-vertical slice in the
queue.** Its acceptance criteria give a component *named physical properties
beyond `rating`*, each with a value and a canonical unit, with the permitted
property names defined per component type and enforced by the strict parser;
they let `FoundationBinding` address a named property rather than only a rating
by unit; and they give `SupportedState` somewhere a model-rule value can live.

That is precisely the carrier every domain pack needs — a compressor's rated
cooling capacity, a battery's usable capacity, a charger's rated output are all
the same shape as a generator's specific fuel consumption. It was designed to
fix one seam defect and it generalises for free. Do not widen it; it already
has the right shape. The only thing worth a moment's thought at implementation
time is that the per-component-type property table is a table and not a chain
of conditionals, which it already reads as.

### T020B — Execution contract alignment

**Nothing changes.** The four semantics it declares — how a quantity declared
over a window moves across it, where within a step a reading is taken, what a
forcing is outside its declared window, what a run does after a bounded change
— are kernel semantics that every future pack inherits whether or not it wants
to. An ambient temperature profile and a charging-session arrival profile both
need "what is a forcing outside its window" answered identically to an
irradiance profile. Settling it now for one vertical settles it for three. This
is the multi-vertical investment already in the plan, and it is already paid
for.

### T021 — Minimal Fuel Loss causal kernel

**One thing, and it costs about an hour inside the slice.**

`.ai/ARCHITECTURE.md` already mandates the right interface: "initialization
plus a step operation over current state, simulation time, timestep, and events
due in that step." That is generic. The risk is not the signature, it is the
body: a step that reads `state.fuel_volume` and writes `state.fuel_volume`
directly is a fuel-tank kernel wearing a generic signature, and the second
state key rewrites it.

What I would ask for: **the mapping from `state_key` to transition rule is a
registry, with one entry, and a test that asserts it.** Not a plugin system,
not a pack loader, not an extension point — a dict and a conformance test that
the kernel's supported state keys equal the model profile's
`supported_states`. T021 already has a conformance test in scope (its
UI-verifiable outcome is that the profile's executability claim is backed by a
test rather than a hand-written tuple), so this is a shape requirement on work
already being done rather than new work.

Why it is worth stopping for under the speed-over-purity rule: it qualifies as
a defect expensive to reverse. The first kernel sets the shape every kernel
after it copies — that sentence is already in T020A's own rationale about the
coefficient — and after T022 there are golden traces bound to it.

**What I would not add to T021:** any second state. Not PV, not battery, not a
generator state machine. The registry with one entry proves the shape. A second
entry proves nothing more and costs a week.

### T021A — Reported observations carry no execution requirement

**Nothing changes.** A parser narrowing on the authoring contract, unrelated to
anything in the brief.

### T022 — Lab execution and device observation

**This is the one slice where a seam is materially cheaper now, and the task
file has most of it already.**

Its acceptance criteria already say the observation transform "samples private
state rather than copying it," runs on the publication profile's cadence rather
than the kernel's timestep, resolves device and signal from the frozen
Foundation, and lets a reporting-path forcing change what is reported without
changing what is true. That is the generic sensor seam, written generically.

The one shape question the criteria leave open: **whether the transform is a
function that knows about fuel levels, or a table keyed by (state key, device
signal) that declares how that state is observed.** If it is the second, family
17 — sensor realism, the whole family — becomes configuration rather than code
for every future vertical, and a compressor temperature sensor or a charger
power meter is a row rather than a branch. If it is the first, every new sensor
type reopens it.

Cost of the table version inside T022: small. The transform is being written
either way, there is exactly one row, and the frozen publication profile is
already the natural place for the declaration to live. Cost of retrofitting it
after T023 exists and golden traces are bound to it: a contract version move
and a trace regeneration.

The related note: T022 already carries an open question about whether the
operator's hand reading declares a reading error. That is the first instance of
family 17's *bias*. It is worth saying out loud that a declared reading error
is not a detail — a fuel reconciliation whose inputs are perfect is arithmetic,
and the finding is only interesting because truth, reading and record disagree.
I would answer that open question *yes*.

### T023 — Staged Source Envelopes

**Nothing changes, and it is the highest-value slice in the queue for a
multi-vertical future.** A Source Envelope carrying source identity, timing,
sequencing, provenance, transport structure and exactly one typed record
payload is domain-neutral by construction, and every vertical in the brief
crosses the same boundary in the same shape.

One caution rather than a change: the acceptance criterion says "exactly one
allowlisted typed record." Keep the allowlist a registry keyed by record type
rather than a union with mini-grid record names structurally baked in. That is
where a second domain bolts on, and it is a naming choice rather than extra
work.

Second note, contingent on section 4: if the mini-grid meeting produces a
historical data set, the natural home for a record importer is this envelope
contract with a non-simulator producer. That would be a *new* slice in the
`T024–T026` range and not a change to T023. Worth knowing in advance so the
envelope is not accidentally shaped around "the simulator staged this."

### Summary

| Slice | Change |
| --- | --- |
| T020A | None. Already carries the generic Foundation property carrier every pack needs. |
| T020B | None. Already settles the kernel semantics every pack inherits. |
| T021 | One: state-key → rule registry with one entry, plus the conformance test the slice already plans. ~1 hour. |
| T021A | None. |
| T022 | One: make the observation transform table-driven by (state key, signal) rather than fuel-specific. Plus answer the reading-error open question yes. Small inside the slice, a version move afterwards. |
| T023 | None. One naming caution on the typed-record allowlist. |

Nothing in the brief justifies adding, reordering or deferring a slice.

---

## 7. What I would not do

- **Do not build three verticals before one finding exists.** Two of the three
  packs would be built against an untested theory of what a finding is. The
  first finding is the thing that proves the abstraction, and no amount of
  breadth substitutes for it.
- **Do not widen the kernel because the site diagram shows PV.** `MG-001`'s
  Foundation already declares PV, a battery and loads; the shipped Fuel Loss
  scenario already declares irradiance and demand as required forcings; the
  minimal profile supports neither and the run blocks with a reason naming
  each. That block is correct and it is the system working. The specific trap
  is the urge to make the shipped scenario stop blocking by adding physics —
  the right fix, which T020B already does, is to lower those two forcings to
  optional and disclose them as unsupported.
- **Do not treat the e-mobility conversation as a product requirement.** The
  brief itself calls it exploratory and asks the contact to say where it
  breaks. Writing a charger model before that conversation converts free
  information into a sunk cost.
- **Do not add a `vertical`, `domain`, or `pack` discriminant to the code.**
  `.ai/ARCHITECTURE.md` already bans variant discriminants inside the shared
  presentation substrate, on the grounds that a branch inside a shared core is
  a fork with extra steps. The same argument holds for the simulator. A pack
  should be *data* — state keys, component types, permitted properties, a model
  profile, transition rules — not a branch. The current shape already gets this
  right by accident; do not spend a slice formalising it.
- **Do not add component types for chargers, vehicles or EVSEs now.**
  `COMPONENT_TYPES` is deliberately closed, with a comment explaining why: an
  unsupported component type is a configuration error rather than a passthrough
  string, because topology, devices and signal mappings bind to these values.
  Adding `CHARGER` before anything can draw it in an SLD or simulate it creates
  a declarable component that produces an empty diagram node.
- **Do not write the 23 families into `.ai/FEATURE_MAP.md`.** That file's job
  is causal order, and twenty-three families with no causal order between them
  would read six months from now as a commitment. If anything from this
  document graduates, it should be one or two lines under an existing feature
  section, after a decision.
- **Do not defer `T023–T029` in favour of breadth.** It is the only unbuilt
  thing that every vertical in the brief needs and no vertical can substitute
  for.
- **Do not record cold-chain as dropped without deciding it.** `COLDCHAIN` is
  in `SITE_TYPES`, `COLD_ROOM` is in `COMPONENT_TYPES`, `MG-002` is a cold-room
  fixture the user asked to be kept, and `Demo Ready v1.5` is a named milestone
  in `.ai/PRODUCT.md`. "I know nobody there" is a go-to-market reason and it
  does not by itself make any of that false. Leave it standing as deferred
  unless you decide otherwise, in which case it is a recorded decision and a
  feature-map edit.

---

## 8. Open questions only you can answer

1. **When are the two meetings?** Inside six weeks, nothing in the queue
   reaches a finding and the mini-grid artifact is a narrated walkthrough of
   built screens. Three months or more and `T023–T026` could plausibly land,
   which changes the meeting from "here is the thesis" to "here is evidence
   crossing a real boundary." This single answer changes more than everything
   else in the brief combined.
2. **Is the mini-grid meeting a demo or a discovery?** The brief says 70% demo,
   which presumes a demo exists. If the real objective is a data set, the demo
   percentage should probably fall and the asking percentage rise.
3. **Would your mini-grid contact plausibly share historical records, and would
   you take a data set over a pilot?** If yes, the fastest path to a first
   finding may not run through the simulator at all, and that reorders
   `T024–T026` around an importer. This is the highest-leverage question here.
4. **Cold-chain: deferred or dropped?** Deferred costs nothing and leaves the
   roadmap alone. Dropped is a decision, frees `T030–T033`, and should be
   recorded — the code and the product document both currently assert it.
5. **How much of the e-mobility story are you willing to tell with mini-grid
   pixels?** If you are comfortable showing the built screens and talking about
   the abstraction, the preparation is half a day of static frames. If you feel
   you need e-mobility pixels that move, that is a real build and it should be
   a decision taken with its cost visible, not absorbed into a slice.
6. **Does the "change policy → world changes" demo mechanic matter to you?**
   It is the brief's most compelling single idea and it has no owner in the
   current four-owner model, because no controller exists. If you want it, the
   place it enters is whenever the first controller does — and that is a
   decision about a fifth property owner, not a slice.

---

## 9. The headline

The brief's architecture is right and its inventory is wrong by about a year.
The shared 70% is not the power-flow model; it is the time-state-observation-
envelope-ingestion-truth skeleton, and the current roadmap is already building
it. Nothing in the brief changes what T020A, T020B, T021A or T023 should do.
Two slices carry a cheap seam worth getting right now — a state-key registry in
T021 and a table-driven observation transform in T022 — and both are shape
requirements on work already planned rather than new scope. Neither meeting
needs a vertical built for it; the mini-grid meeting needs a thesis and a
shopping list, and the e-mobility meeting needs questions. Keep going.
