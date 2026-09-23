# Aligning the implementation to simulator design v3

A verification pass over `Docs/simulator_design_v3.md`, checking each item the
v2 assessment raised against the repository rather than against v3's section
headings.

Prior documents: `Docs/simulator_design.md` (v1, mine),
`Docs/simulator_design_v2.md`, `Docs/simulator-design-v2-alignment.md`.

Nothing here is a decision. No task file or `.ai/` planning file is edited.

---

## 1. Headline

**v3 closes ten of the twelve items the v2 assessment raised, and closes the
two hard conflicts properly rather than by assertion.** I checked both
mechanically, not by reading the headings.

**The programme total does not change.** My v2 estimate of ~32 slices beyond
today still holds. What changes is *where* the cost sits: v3 concentrates it in
**T020A**, which is the next slice, and that slice is now carrying enough to be
worth a sizing conversation with the Planner.

Two things remain, one of which matters:

- **§4.3's power-path discrete state and four rows of §5.1's rename table
  clear the vocabulary *guard* while doing what the *decision* behind it
  forbids.** The guard is lexical; `D-2026-09-20-breaker-vocabulary` is
  semantic. Cheap to fix: nothing in any of the three proof sketches uses it.
- **§15's `PairedExperiment` is the right mechanism with an underdetermined
  projection.** Hashing frozen identities minus a declared delta cannot in fact
  prove all-else-equal, for a reason §5.2 creates.

Everything else can be built as written.

---

## 2. Verification of the v2 findings

| # | v2 finding | v3 § | Status | What I actually checked |
| --- | --- | --- | --- | --- |
| 3.1 | Sampling contradicts T020B's purpose | 6.1, 6.2 | **Closed** | §6.1's boundary cycle applies events at A, samples at C, builds the controller view at D. A reading at `T` carries stocks after events at `T` and interval rates over `[T−dt, T)`. This satisfies T020B's letter *and* its purpose clause. §6.2's asymmetry is correct and is what real instruments do; the first-boundary caveat is honest. |
| 3.2 | v2's names trip `BANNED_CONTROL_VOCABULARY` | 5.1 | **Closed for the guard, open for the decision** | Ran `banned_tokens_in` over every identifier-shaped token and every bare upper-snake value in code blocks across all 1,994 lines. **Three hits, all in §5.1's own "Avoid" column, plus the six tokens where §5.1 quotes the ban list.** No identifier v3 proposes for use trips the parser. See section 3 for what this does not settle. |
| 3.3 | Component addressing vs `FoundationBinding` | 4.2 | **Closed** | §4.2 keeps `state_key` as the semantic name and adds `StateRef(scope, state_key, component_id)`. Critically, it preserves the real behaviour rather than papering over it: "a component-scoped binding with no explicit id may resolve only when exactly one candidate exists; zero or multiple candidates remain unanswered and block as today." That is `FoundationBinding`'s actual rule, carried forward intact. §4.2's rejection of `"CHG-01.charger-power"` is right for the reason it gives. |
| 3.4 | CHG-12 needs `ControlAssumption` to carry setpoints | 5.2 | **Closed, and by the route I identified** | §5.2 leaves `ControlAssumption` as documentary prose and adds *typed control properties alongside it*, which avoids the T016 checkpoint problem entirely. §5.2's run-identity paragraph reaches the conclusion via `FrozenSiteBinding` already freezing `foundation_version` and `foundation_valid_from`, so `DeterministicIdentity` needs no new field. That is the route, and it is correct. One note in section 5. |
| 5.1 | Digest unnamed | 9.1–9.3 | **Closed, and more rigorous than asked** | BLAKE2b-256 pinned, `hash()` explicitly excluded, plus an `rng-contract-version` in the draw payload, canonical length-prefixed encoding rather than string concatenation, an `ordinal`, and a *separate* domain separator for identity digests so RNG and identity namespaces cannot collide. |
| 5.2 | `NumericPolicy` offered but not selected | 8.3 | **Closed** | `EXACT_RATIONAL`, version 1. And it gets my caveat exactly right: `_exact(value).limit_denominator(1_000_000)` stays legitimate at the authored-float boundary, forbidden per step. The allowed/forbidden pair is stated explicitly enough that an implementer cannot remove the wrong one. |
| 5.3 | Cascade justification did not carry forward | 7.3 | **Closed** | The reasoning is restored with the right emphasis — convergence criteria, tolerance, failure semantics and platform sensitivity must become versioned contract rather than appearing implicitly inside a pack — and the boundary is named (droop, voltage-dependent load, impedance network). |
| 5.4 | Discrete state has no contract | 4.3 | **Closed** | `DiscreteStateSpec` carries initialization owner, allowed values, transitions, trace record and observation mapping. It correctly excludes `RATE_INTEGRALS` and quantitative bound policies, adds a `DISCRETE_TRANSITION` trace record with a cause reference, and says timing faults apply while numeric noise does not. |
| 5.5 | Counterfactual pairing has no record | 15 | **Mechanism closed, projection underdetermined** | `PairedExperiment` is immutable, explicitly outside run identity so it cannot perturb trajectories, and rejects `NOT_COMPARABLE`. The shape is right. Section 4 is the gap. |
| 5.6 | Accumulated stress has no owner | 10.2 | **Closed, and better than I expected** | Scenario/initial-condition owned, with three labelled bases and — the part that matters — an explicit `UNKNOWN` case that must not silently become zero, with the consequence that a capability needing historical stress becomes unavailable or claim-limited. That is the honest-refusal principle applied to a case I only flagged as missing. |
| 6 | Build order omits T020A/T020B/T021A | 2.1, 24 | **Closed** | §2.1 and §24 both name all three as prerequisites, state that the build sections are programme phases rather than task-sized slices, and say v3 does not redefine them as nine monolithic tasks. This matches the real queue. One ordering note in section 5. |
| — | Port shape / `LabProjection` | 0, 3.3 | **Closed** | Device observations stay private and reach the Lab through `LabProjection`, never as product-side records — which is what T022 needs. |

---

## 3. The one place v3 resolves the guard but not the decision

§4.3 declares, as a domain-pack discrete state:

```
Power-path state:  CONDUCTING | ISOLATED | FAULT_ISOLATED
```

and §5.1's rename table maps `OPEN`/`CLOSED` → `ISOLATED`/`CONDUCTING`,
`TRIPPED` → `FAULT_ISOLATED`, `AUTO` → `CONTROLLER_ENABLED`, `MANUAL` →
`OPERATOR_COMMANDED`. §4.3 says "these spellings are intentional," so this is a
deliberate choice rather than an oversight.

**It clears the guard.** I verified that: none of those tokens is banned.

**It does not satisfy the decision the guard enforces.**
`D-2026-09-20-breaker-vocabulary` is not a rule about spellings. Its statement
is that a breaker's position "is a time-scoped operational fact, which in this
project means evidence," and that **"a closed set of positions or control modes
in configuration or in scenario schema would let a document assert an operating
condition nothing ever observed."** It bans `BREAKER` itself because "admitting
it as a device type or as a scenario category would answer half the question
early."

`CONDUCTING | ISOLATED | FAULT_ISOLATED` is a closed set of power-path
positions. `CONTROLLER_ENABLED | OPERATOR_COMMANDED` is a closed set of control
modes. Renaming the element from *breaker* to *power path* is admitting the
same thing under a different name, which is precisely the move the decision
anticipated. The token list is the enforcement mechanism, not the rule — and
because the enforcement is lexical, a rename passes CI while the product takes
the decision it declined to take.

**Three of v3's four discrete-state examples are fine and should stay.**
`STOPPED | STARTING | RUNNING | FAILED` is a generator's own machine state, not
a breaker position or a control mode. `SEALED | AJAR` is a door's physical
state. `AVAILABLE | UNAVAILABLE | DERATED` is component availability. None of
those asserts a control or switching position, and the brief requires the
first.

Likewise §5.1's first three rows are right: `door-ajar-excursion` and
`operator-hand-dip` rename *a physical state* and *a record*, and
`operator-commanded-override` names an authored **cause** — which is exactly
what the decision says to do instead ("Name the authored cause or action
instead"). §13's intervention categories are all causes and all clean.

**What this costs to fix: nothing.** I checked every occurrence of the
power-path vocabulary in v3 — it appears in §4.3's example list, §5.1's rename
table and the change log, and **in none of the three proof sketches.** The
mini-grid resolver in §7.3 works from source availability, merit order and
limits; it never needs a switching position. Delete the two rows and the
example line. If a later slice genuinely needs breaker position, it takes the
explicit topology-and-evidence slice that §5.1 itself says is required.

The narrow recommendation: **keep §5.1's rule, drop its last four rows, and
remove the power-path line from §4.3.** Rename where the concept is a cause, an
observable physical state or a record. Do not rename where the concept is a
switching position or a control mode — there, defer the concept, not its
spelling.

---

## 4. `PairedExperiment`'s projection cannot yet prove what it claims

§15.3 says the pair builder "computes a projection of both frozen identities
excluding only the declared permitted difference," and that the projections
"must otherwise hash identically."

That works if the permitted difference is addressable inside the projection. It
is not, for a reason §5.2 creates. Under §5.2, baseline policy lives in
Foundation, so two runs differing in a reserve threshold differ in
`FrozenSiteBinding.foundation_version`. A projection that excludes the
foundation version to permit the reserve change also conceals **every other
Foundation difference inside that version bump**. The digest then proves the
two runs agree on everything the projection still contains, which is not the
claim being made.

§15.4 half-sees this — it says to prefer a declared scenario intervention over
changing baseline Foundation, and that a genuine Foundation difference "must
declare that broader difference and must not be described as a single-variable
comparison." Good. But the same problem reappears one level over: a
scenario-authored policy change makes the two runs differ in
`FrozenScenarioBinding`'s version, and excluding *that* conceals every other
scenario difference.

**What is missing is the projection's granularity.** To prove all-else-equal,
the comparison has to be over **resolved effective values** — the
`FrozenInitializationInput` entries, the resolved control properties, the
observation bindings and signal mappings — not over version identifiers.
Version identifiers are exactly the wrong grain: they are opaque, and their
whole purpose is to summarise a set of changes.

This is an underspecification in a new mechanism rather than a flaw in its
shape, and naming it is cheap because `frozen_inputs()` already exists and
already produces the per-field, per-answerer projection this needs. v3 §15
should say the projection is over frozen inputs.

---

## 5. Two small notes

**`intervention_history` element shape.** §5.2 says "the ordered intervention
history already freezes scenario changes," and concludes no new
`DeterministicIdentity` field is needed. That holds if history entries are
identifiers pointing into the already-frozen scenario version — the field is
`tuple[str, ...]` today and that reading works unchanged. It does not hold for a
**run-scoped** intervention not authored in the scenario, which §13 wants: an
identifier alone cannot reconstruct a change that exists nowhere else. Either
run-scoped interventions are always materialised into a frozen artefact the id
refers to, or the tuple's element type has to become a record. v3 should say
which; the answer does not change §5.2's conclusion about policy.

**T021A's position.** §24 lists T021A among the prerequisites alongside T020A
and T020B. The queue places it *after* T021, and its task file gives the reason:
the kernel never reads `execution_requirement` on a reported observation, so
nothing about the kernel depends on it either way. Harmless, but an implementer
reading §24 as an ordering would move it earlier for no benefit.

---

## 6. What alignment costs now

**The programme total is unchanged at roughly 32 slices beyond today.** v3
resolves conflicts; it does not add work beyond what v2 already implied. My v2
mapping of v3's phases onto the build plan stands unaltered, and §2.1/§24 now
say the same thing from v3's side.

**The cost moved, and it moved into the slice that is next.** T020A now
carries, by v3's own §24:

- the per-component typed property table (already in T020A's criteria),
- component-addressed Foundation bindings, with `SupportedState`,
  `FoundationBinding`, scenario state references and
  `FrozenInitializationInput` all reached (§4.2),
- typed component-scoped control properties (§5.2).

That is three related contract extensions in one slice, on top of what T020A
already carries — the coefficient move, the `dispatched-output` promotion, the
`EXECUTION_CONTRACT_VERSION` move and the retirement of
`INITIAL_VALUE_ANSWERS_DISAGREE`. **I think this is now more than one
reviewable slice**, and the natural cut is between the property carrier and the
addressing change, because the second depends on the first but not the reverse.
Sizing is the Planner's, so this is a flag rather than a proposal — but it
should be flagged before implementation starts rather than discovered during it.

**One genuinely new item v3 adds that no slice covers:** §5.2's *site-scoped*
control properties — source merit order, critical-load priority. T020A's table
is component-scoped, and §5.2 says explicitly that site-scoped properties need
"a parallel typed Site Controls collection, not an abuse of the component
property table." That is correct and it is new work: roughly one small slice,
and it is not needed until a controller exists, so it belongs with the phase-2
controller work rather than with T020A.

**T020B's content changes, its size does not.** The boundary cycle in §6.1
replaces the wording of one of its four declared semantics. Same slice, same
shape, different text — and free only while T020B is unbuilt.

---

## 7. What I would do next

1. **Drop §4.3's power-path line and §5.1's last four rename rows** (section 3).
   Minutes, and it keeps a product decision from being reversed by a rename.
2. **Say that §15's projection is over frozen inputs, not version identifiers**
   (section 4). One sentence in v3.
3. **Put T020A's scope to the Planner before implementation starts**
   (section 6). It is the only sizing risk in the plan and it is immediate.
4. Settle the `intervention_history` element shape and correct §24's placement
   of T021A (section 5). Both one-liners.

Nothing else in v3 needs work before it can be built.
