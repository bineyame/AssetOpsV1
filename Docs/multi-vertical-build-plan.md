# Multi-vertical build plan

How to get from today's repository to a simulator that starts fulfilling the
need the verbatim brief states — mini-grid first, then a second vertical —
building with shared foundations and deliberate room for variant-specific
paths.

Source material: `Docs/multi-vertical-brief-verbatim.md`. Prior analysis, and
the two positions it corrected: `Docs/multi-vertical-capability-read.md`. This
document is a plan, not a decision. No task file or `.ai/` planning file is
edited by it.

Costs are stated in **slices**, because that is the project's unit and the one
I can reason about from history. Where I convert to calendar time I say I am
guessing, because I do not know this project's velocity.

---

## 1. What "fulfilling the stated need" actually means

The paraphrase I worked from in the first two rounds understated this. Read
verbatim, the brief is not asking for a simulator that produces a finding. It
is asking for a simulator that can drive **a portfolio command centre with a
financial bridge**. The opening line of the mini-grid demo is:

> "Imagine you operate 20–50 sites. Which sites are costing you money, which
> ones have growth opportunities, and where should your team intervene?"

and the path through it is `Portfolio → Kobo → finding → evidence → financial
consequence → productive-use opportunity → lifecycle risk → verification`.

Four things follow from reading it that way, and all four change the target:

1. **The unit of demonstration is a portfolio, not a site.** The e-mobility
   mock header carries `12 LOCATIONS`, energy delivered, availability, peak
   utilization, and dollar exposure per month. One site cannot produce that
   screen no matter how good its physics.
2. **A financial bridge is a named core component**, sitting between the
   findings engine and actions/verification in the brief's own architecture
   diagram. Every number on the demo screen is a physical quantity times a
   price. There is no monetary dimension anywhere in the codebase today.
3. **The demo's repeated interaction is "Why are you saying this?"** — evidence
   interrogation behind every claim. That is the provenance drawer, and it is
   what makes the difference between AssetOps and a dashboard.
4. **The product sits *above* existing monitoring.** That is stated directly:
   "Could AssetOps sit above your existing monitoring systems and tell your
   operating team what matters economically?" The simulator is a stand-in for
   the customer's monitoring system, not for the product. This matters more
   than it first appears, and section 7 is about it.

And the brief names six mini-grid stories, not one: avoidable generator
runtime, fuel reconciliation, productive-use and unused renewable capacity,
service reliability, battery degradation, maintenance burden. Its MG-01..10
recipe list is more specific still and is a usable spine for sequencing.

One point of alignment worth noting because it costs nothing: the brief's key
architectural rule — *the simulator changes the world; AssetOps discovers the
consequence; no scenario directly creates a Finding* — is already a protected
seam in `.ai/PROJECT_RULES.md` and is guarded in CI. The plan below never
relaxes it.

---

## 2. The gap from where the code is

Established in `Docs/multi-vertical-capability-read.md` and not re-argued here:
`simulator/assetops_simulator/__init__.py` is 13 lines with an empty `__all__`,
there is no RNG, no numeric dependency, and `/api/simulator-lab/status` returns
`run_execution: not_implemented`.

Mapped onto the brief's own seven core boxes:

| Brief's core box | State today |
| --- | --- |
| Evidence / ingestion | Absent. No envelope type exists. |
| Site / portfolio | Sites, Foundation, topology, devices, SLD: **built**. Portfolio: absent. |
| Findings engine | Absent. |
| Financial bridge | Absent, and `CANONICAL_UNITS` has no monetary dimension. |
| Actions + verification | Absent. |
| Asset lifecycle | Absent. |
| Scenario engine | Authoring contract **built**; execution absent. |

One and a half boxes of seven. The brief's remark that "your existing simulator
direction already supports this well" is true of the *design documents* in
`Docs/` and not of the code; that gap is itemised in the capability read and is
not relitigated here. The design documents remain a good guide — they are just
not an inventory.

---

## 3. The design: where shared ends and variant begins

This is the part the instruction says matters most, so it comes before the
schedule.

Six layers. **Variant-specific content exists in exactly three of them, and in
two of those three it is data rather than code.**

### Layer 1 — Vocabulary (data)

*Shared:* the vocabularies themselves and the strict parsers over them.

*Variant:* the entries. A pack contributes component types, the physical
properties permitted per component type, topology node roles, and state keys.

*Where the seam sits:* `state_key` is already parsed as a free identifier in
`scenarios/parsing.py`, so state keys need no seam work at all — a pack adds
`chamber-air-temperature` or `charger-session-energy` and the parser is
untouched. The closed vocabularies are the ones that must grow:
`COMPONENT_TYPES` and `RATING_UNITS` in `sites/models.py`, and
`TOPOLOGY_NODE_ROLES`, which today holds only the electrical positions the
shipped mini-grid template needs. T020A's per-component-type property table is
the third, and it was already designed to be a table.

*Cost to make it a seam:* zero now. These are closed frozensets that a second
pack extends by adding entries. The one thing to avoid is a conditional keyed
on `site_type`, which is what the architecture's ban on variant discriminants
already forbids.

### Layer 2 — Model profile (already correct)

*Shared:* `ModelProfile`, `SupportedState`, `FoundationBinding`, and the rule
that an unsupported required state blocks the run with a reason naming it.

*Variant:* which profile, and what it declares it can model.

*Where the seam sits:* `MODEL_PROFILES` in `runs/profiles.py` is already a
tuple of profiles resolved by identity and version. **A domain pack is a model
profile plus the rules behind it.** This layer needs no change.

### Layer 3 — Kernel (the new seam, and the only structurally interesting one)

*Shared:* the step's structure — resolve forcings and due events, resolve this
step's flows, integrate stocks — plus the state container keyed by `state_key`,
the stock/flow distinction, bound handling, event dispatch, determinism and
seeding, and the trace format.

*Variant:* the **occupant of phase 2** (the resolver: a mini-grid bus balance,
a depot's charger allocation, a cold room's thermostat) and the per-state
integrators.

*Where the seam sits, concretely:*

```
simulator/assetops_simulator/
  kernel/        shared: step(), WorldState (stocks + flows), events,
                 bounds, determinism, trace
  packs/
    minigrid/    variant: resolver, integrators, controller
```

The kernel imports nothing from `packs/`. A pack registers against a model
profile id. That direction is guardable in exactly the style
`tools/checks/dependency-direction.ps1` already uses for the three bans it
enforces today.

*Cost:* this is the shape change the amendment already put into T021, and
putting the files in these two directories rather than one costs nothing
because the directories do not exist yet. Adopting the layout with one pack is
what makes the guard writable once.

### Layer 4 — Devices, sensors, observation (100% shared)

*Shared:* everything. The transform that samples a stock or a flow at the
publication profile's cadence, plus noise, bias, quantization, gaps, latency,
duplicates and clock drift when they arrive.

*Variant:* which `(state_key, signal)` rows exist — and those are Foundation
data, not pack code.

*Where the seam sits:* in the transform table T022 creates. This is the
strongest reuse claim in the plan: **a compressor probe and a charger power
meter need no simulator code, only a row and a Foundation mapping.**

### Layer 5 — Envelope, ingestion, evidence (shared; one registry)

*Shared:* the Source Envelope, commit/release, ingestion acceptance and
rejection, `received_at`, the accepted-evidence store, read models, provenance,
Replay.

*Variant:* the typed record types in the allowlist.

*Where the seam sits:* T023's "exactly one allowlisted typed record" criterion.
Make the allowlist a registry keyed by record type with a parser per type. A
charging session and a fuel delivery are then two registry entries, not two
branches. This is the caution from the capability read, now a firm
recommendation, because it is the variant seam for the entire evidence half of
the product.

### Layer 6 — Findings and the financial bridge (shared machinery, variant content)

*Shared:* evidence sufficiency, claim boundaries, confidence, provenance links,
unavailable-state suppression, and the financial bridge's flow-times-price
machinery.

*Variant:* the assessments themselves. Fuel reconciliation, curtailment
valuation, degradation-versus-expected-band, productive-use headroom, missed
charging sessions — **these are the variant-specific features** the instruction
asks to leave room for.

*Where the seam sits:* an assessment should be a registered unit that declares
which signals and records it requires, and that refuses rather than degrades
when they are unavailable. That declaration is what lets a portfolio screen say
*this site cannot be assessed for curtailment because it has no irradiance
signal* instead of showing a zero. PRODUCT.md's prohibited-claims list already
demands that behaviour; making it a property of a registered assessment is how
it scales past the first one.

### Variant-specific *screens*

The instruction says "variant specific path (feature)", which is broader than
physics. A vertical will want surfaces mini-grid has no analogue for — a
session log, a battery pool, a swap queue. The architecture already answers
this: the shared presentation substrate declares **named extension slots**, and
each shell composes and adds without forking the core. A pack's screens attach
there. No new mechanism is needed, and the existing rule that the substrate
carries no shell/mode/variant discriminant is exactly the rule that keeps this
from rotting.

---

## 4. The build, in phases

Each phase is stated by what it unlocks. Slice counts for work that has task
files are counts; everything beyond `T023` has no task file and those numbers
are **estimates I am inferring from the size of comparable slices, and should
be treated as a range, not a commitment.**

### Phase 0 — A world that moves. *In flight, 5 slices, all specified.*

`T020A → T020B → T021 → T021A → T022`.

Ends with: a fuel tank whose level moves because a declared cause moved it,
sampled by a device at a declared cadence, with truth and reading as two
distinct objects, controllable from the Lab.

Changes from the amendment, already recorded: T021 becomes a three-phase step
emitting flows alongside stocks (+1–2 days), T022's transform samples flows as
well as stocks (small). Section 6 adds two zero-cost file-layout choices.

**This phase is the whole foundation of layers 3 and 4.** Nothing later
re-opens it if the shape is right.

### Phase 1 — The evidence loop closes. *~7 slices (`T023`–`T029`), one specified.*

Staged Source Envelopes → commit/release → ingestion with explainable
acceptance and rejection → accepted-evidence store → operator evidence views →
provenance drawer → Replay over committed history.

Ends with: the first time anything crosses from a simulated world into product
evidence, and the first time the demo's "Why are you saying this?" interaction
is real.

**This phase is indifferent to how wide the world is.** It carries whatever
signals exist. That is the reason it comes before widening rather than after,
and the reason is optionality rather than purity — see section 7.

### Phase 2 — The world gets wide enough for the six mini-grid stories. *~5 slices, estimated.*

Families 2, 3, 4, 5, 6 and 12 from the brief, populated for mini-grid only:

- **2a — The balance.** Phase 2 of the step gains a real occupant: generation,
  load, battery power, curtailment and unserved load resolved under limits.
  Adds `pv-output`, `site-load-demand`, `battery-power`, `curtailed-power`,
  `unserved-load` as states. This is the single largest slice in the plan and
  may need splitting.
- **2b — Generator and dispatch.** The state machine the brief lists — start
  delay, minimum runtime and off time, loading limits, start failures, runtime
  and service accumulation — plus the EMS controller that decides dispatch.
- **2c — Policy as a configurable object.** Reserve, genset start SOC, minimum
  runtime, critical-load priority. **This is where the fifth property owner is
  decided**, because a policy is the controller's configuration and the current
  four-owner model has nowhere to put it. The decision is cheap here and
  expensive once three controllers exist.
- **2d — Stress and degradation.** If flows are first-class from phase 0, a
  stress accumulator is a stock whose flow derives from other states, so this
  slice is content rather than machinery.
- **2e — Sensor realism.** Noise, bias, calibration error, drift, outage as
  rows in the layer-4 table.

Ends with: MG-01, MG-02, MG-04, MG-05, MG-07 and MG-08 from the brief's recipe
list become expressible, and curtailment, headroom and degradation become
computable quantities.

**The payoff sentence for the whole plan:** because the evidence loop is
signal-agnostic, each state key added here lights up new findings without
touching phase 1.

### Phase 3 — Findings and the financial bridge. *~6 slices, estimated.*

`T034`–`T038` as mapped, plus one for economics. The economics slice is small
but is **a unit-system change, not a new field**: `CANONICAL_UNITS`,
`PARAMETER_UNITS` and `RATING_UNITS` are closed and physical, so a monetary
dimension has to be admitted deliberately, with tariff, fuel price, service and
maintenance cost, replacement value and revenue-per-unit-activity kept separate
from physics as the brief insists.

Ends with: findings with claim boundaries and evidence basis, each carrying a
financial consequence.

Note that the first two findings — avoidable generator runtime and fuel
reconciliation — land on the **narrow** world from phase 0. They do not wait
for phase 2. If the ordering ever needs compressing, this is where the slack
is.

### Phase 4 — Portfolio and what-if. *~3 slices, estimated.*

Portfolio generation with varied operating personalities; the portfolio
command-centre screen with per-site exposure; clone-a-baseline-and-vary-one-
intervention comparison.

Ends with: **the screen the brief actually opens with.**

Both of these are cheaper than they look and neither is ornament — I called
family 20 ornament in the first version and the verbatim brief calls it
"especially important for the client-facing demo", which is the better read.
The frozen deterministic identity that T019 already built is precisely what
makes clone-and-vary a comparison rather than a re-run, and sites are already a
list behind a repository port.

### Phase 5 — The second vertical. *~4–6 slices if the seams hold.*

A pack: vocabulary entries, a model profile, a phase-2 resolver, integrators, a
controller, record types, and any variant screens.

**This number is the test of the whole design.** If a second pack costs 4–6
slices, the seams were right. If it costs 15, they were not, and the place it
will have gone wrong is layer 3 or layer 5. It is worth writing that prediction
down now so it can be checked rather than rationalised later.

### Total

Roughly **26 slices beyond today**, five of them in flight. I do not know the
calendar conversion and will not invent one; what I will say plainly is that
this is a multi-quarter programme, and **both meetings will happen long before
it finishes.** That is not an argument against the plan. It is an argument that
the meetings are narrated rather than demoed, which the capability read already
concluded for other reasons and which this count now quantifies.

---

## 5. Mini-grid first, then expansion — what that sequencing actually buys

The instruction is explicit that mini-grid comes first and the others follow,
so this section is about *how* to take the first vertical without making the
second one expensive, not about whether.

Three rules, each of which costs something small now:

1. **Build every shared layer once, in mini-grid, without a mini-grid name on
   it.** The kernel is `kernel`, not `energy_kernel`. The transform table is
   keyed by `(state_key, signal)`, not by fuel. The record allowlist is a
   registry, not a union of mini-grid record types. Each of these is a naming
   and placement choice at the moment of writing and a refactor afterwards.
2. **Let the pack be the only place a domain word appears.** The test is
   mechanical and worth a CI guard once a second pack exists: the shared layers
   should contain no occurrence of `generator`, `fuel`, `charger` or
   `compressor` outside a pack directory. Today that guard would pass trivially
   and would then keep passing.
3. **Do not generalise from one example.** Layer 3's resolver is the one place
   where a single instance genuinely cannot tell you the right abstraction. The
   discipline that protects against both errors — premature generality and
   painted-in corners — is that phase 2 of the step exists as a *named
   position* from T021 while its *contents* stay minimal. The position is the
   commitment; the occupant is not.

The brief's own claim that "you probably already have much more of the
e-mobility simulator than it first appears" becomes true only if these three
hold. It is false today, and it will be false in a year if the fuel pack is
written straight into the kernel.

---

## 6. What changes in the existing queue

**Mostly nothing, and that is a real answer rather than a dodge.**

| Slice | Change from this plan |
| --- | --- |
| T020A | **None.** Its per-component-type physical-property table is layer 1's variant seam, already in the right shape. |
| T020B | **None.** Its four declared step semantics are layer 3's shared contract. |
| T021 | **As already amended** (three-phase step, flows first-class, ~1–2 days). **Plus one zero-cost addition:** put the shared step in `simulator/assetops_simulator/kernel/` and the fuel rules in `simulator/assetops_simulator/packs/minigrid/`, with the kernel importing nothing from packs. The directories do not exist yet, so this is where files go, not extra work — and it is what makes the dependency guard writable once instead of retrofitted. |
| T021A | **None.** |
| T022 | **As already amended** (transform samples flows as well as stocks). **Plus one zero-cost addition:** the transform table should be a structure a pack can contribute rows to, rather than a literal owned by the fuel path. |
| T023 | **One recommendation, upgraded from a caution:** make the typed-record allowlist a registry keyed by record type with a parser per type. It is layer 5's only variant seam and the whole evidence half of the product sits behind it. Small inside the slice; a schema and contract-version change afterwards. |

No slice is added to, removed from, or reordered within the current queue.

**What the plan does need that does not exist yet:** `T024`–`T029` need task
files when their block becomes active, which is already the project's rule.
Phases 2 through 5 need feature-map sections before they need task files. So
the next Architect deliverable, whenever the user wants it, is **a feature-map
section for phase 2** — the balance, the controller, and the policy owner — not
a task file and not another plan.

Two things in this document are user decisions rather than Architect calls, and
are flagged rather than taken: the fifth property owner in phase 2c, and
whether the monetary dimension enters the unit system in phase 3 or earlier.

---

## 7. The branch point that matters more than any of this

The evidence loop in phase 1 needs a producer. There are two, and **the loop
cannot tell them apart**: the simulator, and an importer for a real operator's
historical exports.

The brief asks for exactly that second thing, in the mini-grid meeting's
closing ask:

> "Could we take one site, or even historical exports from one site, and see
> whether AssetOps can reconstruct something useful?"

If that ask lands, the shortest path to the first real customer value is
**phase 1 plus phase 3 with an importer in place of phases 0 and 2** — the
evidence loop, the findings, the financial bridge, and no simulator at all for
the first finding. Roughly 13 slices instead of 26, and it produces a result
about a real site rather than a simulated one.

That is not an argument for abandoning the simulator, which remains how you
build scenarios nobody's history contains, how you test findings against known
truth, and how you demo without a customer. It is the strongest argument for
**building the loop before widening the world**: a narrow world plus a finished
loop keeps both producers available, and a wide world plus no loop commits you
to the simulator and gives the meeting's best possible outcome nowhere to land.

Which is also why the deliberately domain-neutral shape of T023's envelope
matters beyond multi-vertical concerns. An envelope shaped around *the
simulator staged this* cannot accept a spreadsheet.

---

## 8. What I would do first

In order, and the first two are not build work:

1. **Answer the scope question the capability read flagged**: is the mini-grid
   product fuel reconciliation, or the six stories the brief names? Everything
   in phases 2 and 3 follows from it, and it belongs in `.ai/FEATURE_MAP.md`'s
   open questions.
2. **Say when the meetings are.** Two dozen slices do not fit in front of
   either one, so the meeting artifacts are a storyboard and a list of
   questions. That conclusion is now arithmetic rather than judgement.
3. **Take T021 with the shape from section 6** — three phases, flows
   first-class, kernel and pack in separate directories. One to two days over
   the slice as specified, and it is the only thing in this entire plan that
   becomes materially more expensive if it is deferred, because T022's
   presentation, T023's records and the first golden traces all bind to it.
4. **Then phase 1, unwidened.** Close the loop with one state moving. Resist
   the pull to widen the world first; section 7 is why.
5. **Write the phase-2 feature-map section before any phase-2 task file.** The
   balance, the controller and the policy owner are a feature with causal
   prerequisites, and treating them as a task list first is how the position
   ends up occupied before it is named.
