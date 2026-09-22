# Aligning the implementation to simulator design v2

An Architect assessment of `Docs/simulator_design_v2.md`, read as a
specification to be built rather than a document to be scored.

`Docs/simulator_design.md` (v1) is mine; v2 supersedes parts of it and this
assessment accepts those changes rather than defending them. Where v2 asks for
something the repository's built contracts forbid, that is in section 3, and it
is the part worth reading first.

Nothing here is a decision. No task file or `.ai/` planning file is edited.

---

## 1. Verdict

**v2 is a better simulator design than v1 and a substantially larger
programme. It is right on essentially every point where it changed v1.**

Of its sixteen changes, I accept fourteen without reservation, accept one with
a caveat an implementer needs (CHG-15), and accept one only in the narrow scope
it was aimed at (CHG-16, which must not be read as reaching the existing
control-vocabulary ban — section 3.2).

The alignment cost is not in the design. It is that **v2's nine build slices
are roughly this project's twenty-six**, and two of its decisions collide with
contracts that are already built and enforced in code. Both collisions are
cheap to resolve now and expensive after T022, which is the only urgency in
this document.

Three things v2 got right that v1 had wrong, stated plainly because they are
the reason to adopt it:

- **CHG-01, the source boundary.** v1's `RunExecutionPort.observations()` would
  have let device observations cross into the backend. Only canonical source
  envelopes may cross. v2 is right, and this matches the frozen architecture:
  the Source Envelope *is* the boundary object.
- **CHG-03, control intent versus physical acceptance.** v1 collapsed decision
  and acceptance into one resolve phase. A controller requesting 30 kW from a
  PCS that can deliver 22 kW is the normal case across all three packs, and it
  needs two objects, not one.
- **CHG-04, topology as first-class.** v1 centred the world on a flat
  `state_key` map. That does not survive two loads or two chargers — and
  section 3.3 shows it does not survive the *built* binding contract either.

---

## 2. What alignment costs

### 2.1 The phase mapping

My build plan's phases survive unchanged. v2's build order is a phase list in
slice clothing, and the mapping is clean, which is good news: no re-planning is
required, only re-labelling.

| v2 slice | Build-plan phases | Project slices |
| --- | --- | --- |
| — (unstated prerequisite) | T020A, T020B, T021A | 3, specified |
| Slice 1 — mini-grid causal kernel | Phase 0 (T021, T022) + Phase 2a, 2b, 2c | ~8–10 |
| Slice 2 — gateway / source-envelope path | Phase 1 (T023–T029) | ~7 |
| Slice 3 — first operational finding world | Phase 3 (T034–T038) | ~6 |
| Slice 4 — intervention / verification | Phase 3 + new intervention work | ~3 |
| Slice 5 — productive-use / load addition | Phase 2a residue + Phase 3 | ~2 |
| Slice 6 — degradation / maintenance | Phase 2d + maintenance model | ~3 |
| Slice 7 — cold-chain pack | Phase 5 | ~4–6 |
| Slice 8 — e-mobility pack | Phase 5 | ~4–6 |
| Slice 9 — portfolio recipes | Phase 4 | ~3 |

**v2's Slice 1 is not a slice.** It asks for one topology, one controller, one
physical resolver, battery *and* fuel stocks, named power flows, deterministic
time and observation sampling — against an empty simulator package. That is
eight to ten reviewable slices by this project's standards, and treating it as
one would produce exactly the unreviewable lump the task-shape rule exists to
prevent. The same applies to Slice 2, which is the whole evidence loop.

This is a naming difference, not a disagreement, and the user should read v2's
numbers as phases.

### 2.2 What v2 adds that no phase covered

Four bodies of work my build plan did not have. Rough sizes, and I am
estimating from comparable slices because none of these has a task file.

| Addition | v2 § | Size |
| --- | --- | --- |
| Maintenance and intervention as world events, with typed intervention kinds | 13 | ~2 slices, and it is a prerequisite for the verification story rather than a nice-to-have |
| Operational records as a separate class with missing / delayed / conflicting / partial variants | 12 | ~2 slices; it is what makes claim ceilings demonstrable |
| Gateway realism — buffering, outage, recovery, retry, duplicate, out-of-order, the three timestamps | 11 | ~1–2 slices on top of T023–T026, which assumed a clean gateway |
| Counterfactual pairing | 9.1 | ~1 slice, and cheaper than it looks because the frozen identity already exists — but see 5.5 |

Net: the programme grows by roughly six to seven slices, from ~26 to ~32
beyond today. That is a quarter of additional work, and every item of it is
load-bearing for the demo the verbatim brief describes rather than optional
polish.

### 2.3 What costs nothing

Worth saying because it is most of the document: sections 5.2 (stocks and
flows), 6.3 (event dispatch), 8.1–8.2 (integration and bounds), 9 (substreams),
10.1 (observation transform), 15 (pack contract), 19 (scenario authoring), 21
(truth, trace, replay), 23 (business context) and 24 (execution failures) are
either already v1's design or already the built contract. They need no
alignment work at all.

---

## 3. Conflicts with what is already built

Four. The first two are hard — a guard or a parser will refuse the code — and
both are cheapest to resolve before T020B and T021 are implemented.

### 3.1 CHG-02's time convention contradicts T020B's declared semantic — HARD

**What is built, or about to be.** T020B's acceptance criteria declare four
semantics that a conforming kernel obeys, one of which is:

> the observation transform samples after the step's due events are applied,
> so a boundary sample can never see pre-event state

**What v2 specifies.** §6.1 places device observation at position 8, after
integration, timestamped `t + dt`; events are applied at position 1,
timestamped `t`.

**Why these collide.** Under v2, a sample timestamped `T` is produced by the
step that *ends* at `T`. Events due at `T` belong to the step that *begins* at
`T` and have not been applied yet. So a boundary sample at instant `T` sees
pre-event state with respect to the events at `T`. The letter of T020B's rule
is satisfied — the step's own due events, at `t`, were applied first — but the
purpose clause it states is not.

This is not a quibble: it decides what the shipped Fuel Loss document means. If
a reading and a cause land on the same instant, one convention shows the
reading before the cause and the other after.

**The reconciliation, which keeps v2's causal intent intact.** Emit the sample
at the *start of the following step*, after that step's due events are applied,
labelled with that step's instant. Concretely, a reading timestamped `T`
reports:

- **stocks** at `T`, after the events due at `T` — satisfying T020B;
- **flows** over `[T − dt, T)`, the interval that just ended — satisfying v2's
  requirement that telemetry describes the consequence of the preceding
  interval.

This is also what real instruments do: a level sensor reads the level now, a
power meter reports average power over the interval just ended. v2's positions
1 through 7 are unchanged; only where position 8 sits relative to the next
step's position 1 moves.

**Cost.** Free now. T020B is `planned`, not built, so the semantic can be
worded to match before anything conforms to it. After T022 it is a narrowing of
the space a conforming kernel may occupy, so it moves
`EXECUTION_CONTRACT_VERSION` and regenerates every golden trace.

**This is the single most time-sensitive item in this assessment.**

### 3.2 v2's vocabulary will be refused at parse time — HARD, and it will bite on day one

`backend/assetops_backend/control_vocabulary.py` bans six tokens —
`OPEN`, `CLOSED`, `TRIPPED`, `AUTO`, `MANUAL`, `BREAKER` — in mapping keys,
upper-snake enumerated values, and identifier-valued fields including
`parameter_id`, `event_id` and `scenario_id`. Comparison is by token, so
`door-open` and `DOOR_OPEN` are both caught. It is enforced by the scenario
parser at parse time, it lives in product code rather than in a test, and
`D-2026-09-20-breaker-vocabulary` makes it unconditional until a slice adds the
topology and evidence contract that makes such statements truthful.

v2 collides with it in at least these places:

| v2 content | Token | Result |
| --- | --- | --- |
| §17.4 *door-open excursion* — a required cold-chain scenario | `OPEN` | Refused as a `scenario_id` or `event_id` |
| §12 *manual tank dip* — a required operational record | `MANUAL` | Refused as a record-type identifier |
| The brief's *forced-on / manual override* generator capability | `MANUAL` | Refused |
| Any genset or compressor mode spelled `AUTO` / `MANUAL` (§7.1, §14.3) | `AUTO`, `MANUAL` | Refused |

Confirming evidence that the ban is live rather than theoretical: the shipped
Fuel Loss scenario names its operator source `operator-hand-record`, not
*manual record*. That spelling was chosen to clear this ban.

**The fix is naming, not architecture** — `door-ajar-excursion`,
`operator-hand-dip` — or a deliberate slice that retires the ban, which is what
the rule itself says makes these statements truthful. Either is fine. What is
not fine is discovering it when an implementer writes the first scenario recipe
pack and the parser refuses the document.

**And a distinction v2 should not be read as erasing.** CHG-16 says structural
isolation checks should replace lexical bans on domain words. **I accept that
completely** — it was aimed at my proposed guard banning `generator` and `fuel`
outside `packs/`, and v2 is right that dependency and branching checks are the
better instrument. But `BANNED_CONTROL_VOCABULARY` is a different mechanism for
a different purpose: it is not about module isolation, it is about a document
being unable to assert an operating condition nothing ever observed. CHG-16's
reasoning does not reach it, and an implementer who deletes it citing CHG-16
would be removing a decision the product took for unrelated reasons.

### 3.3 Component-addressed state versus the built binding contract — STRUCTURAL

v2 §5.2 says a `StateRef` "should include component identity where appropriate,
not only a global string." Its own proof sketches require this: §16.1 has
household, critical *and* productive loads; §5.1 shows `LOAD-RES` and
`LOAD-MILL`; §18.1 shows `CHG-01` and `CHG-02`.

What is built cannot address them. `SupportedState.state_key` is a plain
string. `FoundationBinding` resolves by `(component_type, rating_unit)`, and
T020A's criteria state that **a binding matching zero or more than one
component selects neither — the value stays unanswered and the run blocks.**
Two loads or two chargers of the same type are therefore not addressable today;
they block by design.

So v2's world model needs component-addressed state, and the contract that
resolves initial values needs to grow with it. This reaches
`SupportedState.state_key`, `FoundationBinding`, the scenario parser's
`state_key`, and `FrozenInitializationInput`.

**Cost, and where it is cheapest.** T020A is the slice that touches
`FoundationBinding` and builds the per-component property table. Adding
component addressing there is an extension of work already being done. Adding
it after runs are frozen and traces are bound means a contract-version move and
regeneration. **T020A is the right place and it is next.**

### 3.4 CHG-12 requires `ControlAssumption` to become what it was built not to be — NEEDS A CHECKPOINT

v2 §22 puts baseline operating policy — battery reserve, genset start
threshold, minimum runtime, source merit order, critical-load priority,
thermostat band — in the Site's time-valid Foundation / Controls.

**The good news first, and it is better than v2 claims.** §2.1 says the frozen
identity must bind the effective Foundation/Controls version.
`FrozenSiteBinding` already carries `foundation_version` and
`foundation_valid_from`, and `DeterministicIdentity.intervention_history`
already exists as an ordered tuple. **If policy lives in Foundation, the run
identity already freezes it with no change to `DeterministicIdentity` at all.**
That is the strongest argument for CHG-12's "no sixth owner", and v2 does not
quite make it.

**The problem.** `ControlAssumption` as built carries an identity, a subject, a
basis and *the assumption in words*. Its docstring is explicit: "Deliberately
not a control model. It declares no control state, no setpoint, no mode." A
battery reserve of 30% is a setpoint. So CHG-12 requires that model to grow a
typed value carrier — and the vocabulary of that model was owned by T016's
user-review checkpoint.

This is the same defect shape T020A exists to fix: a declarable owner with
nowhere for the answer to live. And the cheapest landing is the same carrier —
T020A's named properties with a value and a canonical unit, parser-enforced per
component type. Component-scoped policy falls out naturally (reserve on the
battery, start threshold on the generator, band on the cold room). Site-scoped
policy — merit order, critical-load priority — has no home in T020A's
component-scoped table and would need a site-level bag.

**This needs a user-review checkpoint**, because it changes a model whose
vocabulary a previous checkpoint settled. It is not an implementation detail.

---

## 4. What v2 did to v1's two forced decisions

**The `host/` composition root: kept, and v2 is right to keep it.** I
re-checked `tools/checks/dependency-direction.ps1` before writing this. It bans
every file under `backend/` from importing the simulator in three forms
including the `import_module` string form, and its header says not to weaken
the checks to make a task pass. v2 §4.1 preserves the neutral root. No conflict
and nothing to decide.

One instruction v2's §4.1 adds that is worth honouring literally: "simulator
must not import backend **product analytics**" is weaker than the guard, which
bans importing `assetops_backend` at all. Build to the guard, not to §4.1's
wording.

**The observation sampling point: changed, and partly wrongly — section 3.1.**
v2's split of the step is better than v1's in every other respect; only the
position of the sample needs the correction above.

**The port shape: changed, and rightly.** v1's `observations()` is replaced by
`staged_envelopes()` and `commit()`. One consequence to state so it is not
mistaken for a regression: **T022 requires the Lab to show the fuel-level
device's generated observations.** Under v2 those travel inside `LabProjection`
— private, Lab-only, gated — rather than as a product-side type. That is
compatible with T022 and strictly safer than v1.

---

## 5. What v2 leaves for an implementer to invent

Not stylistic gaps. Places where two competent implementers would choose
differently and their outputs would not match.

### 5.1 The digest function is unnamed

§9 specifies `draw(seed, stream_name, step_index, ordinal) =
cryptographic_digest(...)`. The `ordinal` is an improvement on v1. But the
digest is not named, and two choices are not interchangeable: changing it
changes every trajectory ever generated. **Pin it as contract** — v1 §5.7
proposed `blake2b`, and the reason matters more than the choice: Python's
`hash()` is salted per process and would make runs irreproducible across
invocations.

### 5.2 `NumericPolicy` is offered but not selected

§8.3 introduces `NumericPolicy` with three example values and does not say
which is in force. The design needs to state `EXACT_RATIONAL` explicitly, or
the first implementer picks.

**And a caveat on CHG-15, which I otherwise accept.** Removing per-step
`limit_denominator()` is correct — it was approximation contradicting an
exactness claim, and v1 was wrong to put it in the canonical step. But
`_exact()` in `scenarios/execution.py` already applies
`limit_denominator(1_000_000)` at the float-to-`Fraction` *boundary*, and that
one is legitimate: it recovers the decimal the author wrote rather than its
binary expansion. An implementer applying CHG-15 broadly would remove the wrong
one and reintroduce `56.00000000000001`.

The practical risk CHG-15 accepts is denominator growth. With the current unit
table — factors of `1/1` and `1/60` — and integer timesteps, denominators stay
on divisors of a small least common multiple and the risk is nil. It becomes
real when efficiency fractions and state-of-charge percentages arrive, which is
Slice 1. `NumericPolicy` should therefore be versioned before Slice 1 ships,
not kept as a future escape hatch.

### 5.3 The cascade's justification did not carry forward

§7.3 keeps the declared cascade and says no network solver is required. It does
not say *why* a solver is excluded. The reason is not preference: an iterative
solver needs a convergence tolerance, a tolerance is a floating-point quantity
whose result can differ across platforms, and that breaks reproducibility
outright. An implementer told only "no solver required" will reach for one when
droop or a voltage-dependent load appears. Carry v1 §5.4's reasoning and its
named boundary forward into v2.

### 5.4 Discrete state has no contract

§5.2 adds `discrete: Mapping[StateRef, DiscreteValue]` — compressor on/off, a
genset state machine, charger availability. Nothing says how a discrete state
is initialized, bounded, observed or traced. `BOUND_CASES` and `RATE_INTEGRALS`
are quantitative and do not apply. Three specific unknowns: which of the four
initialization owners answers for a discrete initial state; whether a discrete
transition is a trace record kind of its own; and whether a discrete state may
be observed through the same transform table as a stock.

Note also that discrete state is where section 3.2's vocabulary ban is most
likely to be tripped, because machine modes are spelled with exactly the banned
words.

### 5.5 Counterfactual pairing has no record

§9.1 wants a baseline and an intervention run sharing initial state, forcing
realization, substreams and interval, differing in one declared change. Today
two such runs are simply two runs with two frozen identities; nothing records
that they are a pair or that they differ in exactly one thing. Without that,
the comparison is asserted rather than proved, which is the same defect the
frozen identity was built to prevent elsewhere. Where the pairing record lives,
and whether it is part of run identity, is unspecified.

### 5.6 Initial values for the new stocks

Every initial world value needs one of the four initialization owners.
v2 adds battery state of charge, chamber temperature, vehicle state of charge
and accumulated stress. The first three have natural owners — a Foundation says
how large a tank is, never how full it is, so an initial level is scenario-owned
by the same reasoning. **Accumulated stress has no obvious owner at all**: it is
neither what the site is, nor what happens during this interval, and a run that
starts every asset at zero stress cannot tell a degradation story about an
existing fleet. This needs an answer before Slice 6.

---

## 6. The build order and the acceptance tests against the existing queue

**v2's build order does not mention T020A, T020B or T021A**, and read literally
it replaces the queue. It should not. Those three are prerequisites of v2's
Slice 1, not alternatives to it:

- **T020A** carries the Foundation property table that v2 §15's
  `property_tables` and §22's policy values both need, and is the cheapest
  landing for conflicts 3.3 and 3.4.
- **T020B** declares the step semantics v2 §6 depends on, and is where conflict
  3.1 must be resolved.
- **T021A** is an unrelated parser narrowing that is free while no golden trace
  exists and expensive afterwards.

With those in front, **T021 and T022 are the first half of v2's Slice 1, and
T023 is the first third of Slice 2.** No slice in the current queue is
superseded, reordered or made redundant by v2. That is worth saying plainly.

**The acceptance tests are good and mostly not yet runnable.** Tests 1
(deleting private truth does not change product output), 3 (time causality), 4
(controller/physics separation) and 5 (counterfactual stability) are sharp,
mechanical and should be written as tests rather than kept as prose — test 1 in
particular is a stronger statement of the truth barrier than anything in v1 and
is nearly checkable today. Tests 7, 8 and 10 depend on findings, claim ceilings
and portfolio roll-up, which are phases 3 and 4; they are design tests for now
and cannot join CI until then. Test 6 can only be run once a second pack
exists, which makes it the falsifiable prediction both documents already carry.

---

## 7. What I would do next

In order, and the first three are the whole of the urgency:

1. **Settle the sampling position (3.1) before T020B is implemented.** It is
   free this week and costs a contract version and a trace regeneration after
   T022. The reconciliation in 3.1 keeps v2's convention and satisfies T020B's
   purpose; it needs the user's yes, not new design.
2. **Decide the vocabulary question (3.2)**: rename v2's colliding identifiers,
   or schedule the slice that retires the ban. Renaming is minutes; discovering
   it mid-implementation costs a refused document and an argument about whether
   to weaken a guard.
3. **Fold component-addressed state (3.3) into T020A**, which is next and is
   already opening the binding.
4. **Put CHG-12 (3.4) to a user-review checkpoint**, because it changes a model
   a previous checkpoint settled. The good news — that the frozen identity
   needs no change — should be part of that review.
5. **Pin the three unnamed things** (5.1 digest, 5.2 numeric policy, 5.3 the
   cascade's reasoning) into v2 itself, so the document an implementer builds
   from is the one that answers them.

Everything else in v2 can be built as written.
