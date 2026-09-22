# Simulator: Scenario Authoring, Runtime, And Injectable World Perturbation

Status: **reviewed and accepted, 2026-09-21.** The user accepted all eight
proposals, (e) through (l). Read the `[PROPOSED]` tags below as accepted and
not yet built; the `[OPEN]` tags are still open. This document is now the
reference the 2026-09-21 decisions cite, and where it disagrees with
`.ai/DECISIONS.md`, the decision record wins.

What the acceptance produced, all on
`arch/simulator-authoring-and-runtime-sequence`:

- `.ai/DECISIONS.md` — `D-2026-09-21-scenario-execution-contract-amendment-1`
  carrying (c), (d), (e), (f), (g) and (i);
  `D-2026-09-21-run-setup-outcome-vocabulary` carrying (a), (b) and (l);
  `D-2026-09-21-projection-versus-composition` for (h);
  `D-2026-09-21-specification-reference-implementation` for (j);
  `D-2026-09-21-physical-property-ownership` for (k).
- `.ai/ARCHITECTURE.md` — the projection-versus-composition rule under Causal
  Runtime Authority, and a new Physical Property Ownership section.
- `.ai/FEATURE_MAP.md` — the M1C sequencing revision, T020A, the T021 loop, the
  dependency structure, and the three seams this work surfaced.
- `.ai/PLANNING_HANDOFF_T019_T022.md` — per-slice guidance for the Planner.

**Revised 2026-09-22.** The user placed (g) in its own slice, **T021A**,
between T021 and T022, rather than inside T022: the version-bump window is
free only while no golden trace exists and T022 is what first produces one.
T020A carries its own user-review checkpoint. And
`D-2026-09-22-expiry-follows-the-condition` corrects two expiries this
document stated as slice numbers — the reference implementation's removal
follows its last remaining caller and is gated on Open Question 5, and
T021 retires the `READY` disclosure because its conformance test is what makes
the disclosure false. The T019 user review then **moved the refusal line** —
the scenario's declared owner has no answer, refuse; the selected profile
cannot answer, block — which corrects two consequence statements below
that said a site without the T020A property would block. It is refused. See
the 2026-09-22 extension to `D-2026-09-21-run-setup-outcome-vocabulary`.

**Revised again 2026-09-22, after a cold read of the whole sequence.** Two
additions. `D-2026-09-22-contract-version-scope` answers whether the
`TRAJECTORY` oracle kind moves `EXECUTION_CONTRACT_VERSION` - it does not -
and says the absolute version numbers should stop being written as literals.
And [What declares the need](#what-declares-the-need-once-the-scenario-stops-declaring-it)
opens a decision due before T020A's task file: once `generator-fuel-rate`
leaves the scenario, nothing in the current design tells run setup the run
needs the coefficient. That section also finds that this document's own
statement about a non-re-created MG-001 producing **refused** runs does not
match the code, and marks it under decision rather than correcting it in a
direction the user has not chosen.

No code has been changed to match this document. Task files are the Planner's
and now exist for T019 through T023; the code changes belong to the slices
named in the per-task table below.

Date: 2026-09-21. Author: Architect (Claude), at the user's request following
the T019 checkpoint consults.

---

## How To Read This

Every substantive statement carries one of four tags. If a statement has no
tag, the tag of its section heading applies.

| Tag | Meaning |
| --- | --- |
| `[SHIPPED]` | Built, reviewed, and on `main` or on the reviewed T019 branch. You can run it today. |
| `[ACCEPTED]` | Decided by you at a checkpoint and recorded in `.ai/DECISIONS.md`, but not yet fully built. |
| `[PROPOSED]` | My recommendation at the time of writing. **All of (e) through (l) were accepted on 2026-09-21 and are now recorded in `.ai/DECISIONS.md`**; the tag is left in place because the surrounding argument reads as it was written. Some of these amend accepted ground, and each such case says so explicitly. A `[PROPOSED]` item outside (e)–(l) — a `[PROPOSED]` row in a table, a *my read* on an open question — was not part of that acceptance and is still a recommendation. |
| `[OPEN]` | A real question with no answer yet, listed in the Open Questions section. |

Where a `[PROPOSED]` item would change something you already accepted, it is
marked **`[PROPOSED — AMENDS ACCEPTED GROUND]`** and the cost is stated inline.

The four proposals that came out of the third Architect consult are referred
to throughout as (e), (f), (g) and (h). They are defined in
[The Four Proposals](#the-four-proposals) and each one is tied to the task
that would carry it.

---

## Table Of Contents

1. [The One Principle](#the-one-principle)
2. [Authoring Without A Kernel](#authoring-without-a-kernel) — *can a scenario mean anything before T021?*
3. [Where Physical Properties Live](#where-physical-properties-live) — *what Foundation must declare before T021*
4. [The Three Stages, In One Picture](#the-three-stages-in-one-picture)
5. [The Proposals](#the-proposals)
6. [Stage 1 — Scenario Authoring](#stage-1--scenario-authoring)
7. [Stage 2 — Runtime](#stage-2--runtime)
8. [Stage 3 — Injectable World Perturbation](#stage-3--injectable-world-perturbation)
9. [Worked Example: The Fuel Loss Event, End To End](#worked-example-the-fuel-loss-event-end-to-end)
10. [Mock Screens](#mock-screens)
11. [Per-Task Contribution](#per-task-contribution)
12. [Sequencing Constraints](#sequencing-constraints)
13. [Open Questions](#open-questions)

---

## The One Principle

Everything in this document follows from one sentence, and the sentence is a
generalisation of a decision you have already taken
(`D-2026-09-21-causal-runtime-before-golden-traces`):

> **An authored artifact may declare causes. It may never declare consequences.**

A scenario says *fuel was removed*. It does not say *and therefore the tank
held 155 litres*. It does not say *and therefore the sensor read 155 litres*.
It does not say *and therefore the product should conclude 120 litres went
missing*. Each of those is a consequence, and a consequence is only true if
something computed it.

There are exactly three places a consequence can be computed, and they are the
three stages of this document:

- the **kernel** computes world state from causes;
- the **observation transform and gateway** compute what is reported and
  published from world state;
- the **product** computes what can be concluded from published evidence
  alone.

A value that appears anywhere without having been computed by one of those
three is a hand-simulation. The project's word for the shipped example of this
is *placeholder*, and there are two of them: the 155 L sensor reading and the
150 L operator record in `config/scenarios/fuel-loss-event.yaml`.

The corollary, which is the second half of the principle:

> **A validation may check anything that is true of the document. It may not
> check anything that is only true of a run.**

This is the line that decides what run setup is allowed to do, and it is the
subject of proposals (e) and (h).

---

## Authoring Without A Kernel

*This section was added after the first draft, in answer to the question: how
can scenario authoring make sense without a runtime at all? An author writing
"120 L leaves the tank" has a mental model of what the tank then does and what
the sensor then reads. That model is doing real work and is written down
nowhere falsifiable. Is authoring separable from the kernel, or is it the same
circularity one layer up?*

**It is a fair charge, it is partly correct, and the part that is correct
locates a second defect nobody had named.** This section answers it directly
and then says what to do.

### The short answer

> **Authoring is separable from any particular kernel. It is not separable
> from the specification of kernels.**
>
> A `ScenarioDefinition` is a program. T021's kernel is an interpreter. T018's
> execution contract is the **language specification** — neither the program
> nor the interpreter, but the document that says what a conforming
> interpreter must do. Where the specification pins a meaning, authoring is
> genuinely independent of any implementation. Where it does not, the author
> is writing something whose meaning the first kernel will decide by accident,
> and *that* is the circularity — not authoring-before-kernel as such.

Specifications routinely precede implementations, and that is not circular. But
a specification with **zero** implementations is under-tested, and the standard
remedy is a reference implementation. That is what
`reconcile_reported_observations` accidentally became. The defect is not that
it exists; it is that it was shipped as **product behaviour** — a run-setup
blocking reason and a user-facing screen panel — rather than kept as a
**test-only conformance oracle** for the spec. See proposal (j).

### What the specification actually pins

For the shipped document, these are fixed for every conforming kernel. An
author can rely on them today with no runtime in existence:

| The author writes | Every conforming kernel must | Pinned by |
| --- | --- | --- |
| `volume-removed: 120 L`, `DECREASE`, window at 1500 for 45 min | decrease `fuel-tank-volume` by exactly 120 L, complete at 1545 | roles + canonical units + timing shapes |
| `generator-fuel-rate: 14 L/h` over a 240-minute window | apply exactly 56 L, not 55.99 or 56.0000001 | exact-ratio unit conversion |
| `scheduled-refuelling` at `POINT` offset 2400 | apply it in the step beginning at 2400 and in no other | half-open interval semantics |
| `tank-capacity` with `bounds: {state_key: fuel-tank-volume, bound_kind: UPPER}` | never silently clamp; refuse, fail, or record a bounded change with the refused quantity | bound policy |
| `starting-fuel-level`, owner `SCENARIO_INPUT` | initialize from it and from nothing else; refuse a second owner | initialization ownership |
| `fuel-level-reporting-gap`, `FORCING_INPUT`, no state effect | leave `fuel-tank-volume` untouched | role boundary |

That is a real language, and a scenario written against it is a real program.
"Better-formed" pre-kernel has a precise meaning: **a scenario is better-formed
when more of its meaning is pinned by the specification and less is left to the
interpreter's discretion.**

### What the specification does not pin — the actual defect

Four points where two conforming kernels could disagree today. Each is a place
the author's mental model is silently deciding something:

1. **Window apportionment.** 120 L over 45 minutes — does the tank drain
   linearly across the steps, or drop at 1545? The endpoint is fixed; the path
   is not. `state_transition_inputs` already commits to the endpoint reading by
   computing `applied_value = rate × duration`, which is the specification
   choosing without saying it is choosing.
2. **Observe before or after.** Within one step, does a sample see pre-event or
   post-event state? Changes the 2400 sample from 254 L to 500 L.
3. **A forcing outside its window.** `overcast-day` forces irradiance over
   `[720, 1080)`. What is irradiance at 1080? Undefined. Currently unreachable
   because the model profile does not support irradiance at all and blocks the
   run — but unreachable is not the same as decided.
4. **After a bounded change.** The spec says a bound produces "a bounded change
   recorded with the quantity it refused." It does not say whether the run
   continues, or whether later causes apply to the bounded value. For the
   shipped document this decides everything after offset 2400.

**This list is the deliverable of this section.** It is what makes authoring
safe before a kernel exists: not the absence of unpinned points, but a written
inventory of them. Each belongs in `EXECUTION_CONTRACT_VERSION`'s scope, and
pinning any of them narrows the conforming space and moves the number.

### The rule for where an expectation may live

The author has a mental model. It is unavoidable and it is not a flaw —
choosing an input because you anticipate its output is *experimental design*,
which is how every honest test is built. The circularity enters at one specific
point:

> **An expectation is legitimate when it occupies a position where being wrong
> causes a failure. It is circular when it occupies a position where being
> wrong causes agreement.**

Falsifiable position versus load-bearing position. This is the same rule as
projection-versus-composition, seen from the author's side rather than the
validator's.

### The shipped document, audited against that rule

| Element | Position | Verdict |
| --- | --- | --- |
| `starting-fuel-level: 430 L` | stipulated input | **Not an expectation.** Nothing can falsify "the tank started at 430 L"; the author decreed it. Legitimate. |
| `generator-fuel-rate: 14 L/h` | stipulated input, private truth | Legitimate. Its falsifiable counterpart is the Foundation consumption assumption the *product* uses, which may differ. |
| `tank-capacity: 500 L` | input **checked against Foundation** | Legitimate, and the best-shaped element in the document: an assertion about the site that run setup can refuse. |
| `evening-peak-load: 72 kW`, `peak-irradiance: 310 W/m2` | stipulated forcings | Legitimate as inputs. |
| `overcast-day` **description** — *"so the battery reaches the evening with less stored energy than usual and the generator is needed"* | prose | **A causal claim nothing computes.** No kernel in the M1C plan models PV, battery, or dispatch logic; the generator window is separately hand-authored at 1080. The chain overcast → low battery → dispatch exists only in the author's head. Harmless because nothing reads prose — but this is the clearest instance of the charge in the whole document, and it is worth seeing plainly. |
| `dispatched-output: 45 kW` | `NON_EXECUTABLE_CONDITION` | **The correct treatment of an unrecordable expectation.** The author believes it; the role says nothing consumes it. A good model for the rest. |
| `fuel-level-reporting-gap` | forcing on the reporting path | Legitimate. |
| `level-after-the-gap: 155 L` | **load-bearing input** | **Circular.** A consequence the author computed by hand, in a position the system reads as fact. Being wrong caused agreement for three slices, then caused a mislocated blocking reason. |
| `hand-recorded-level: 150 L` | **load-bearing input** | Circular, same shape. |
| `scheduled-refuelling: 300 L` | stipulated input | Legitimate as an input — **but** the author's unrecorded model of the tank at 2400 was wrong, and `254 + 300 = 554 > 500` went unnoticed because no expectation was in a position to fail. Being wrong caused silence. |

### Do the private expectations escape the charge?

Mostly yes, and one of them only partly — which is the finding this section
turns up that nobody had named.

| Oracle | Escapes? | Why |
| --- | --- | --- |
| `removal-is-separable-from-consumption` (`DETECTION`) | **Yes** | Asserts a capability of downstream analysis. The path from input to analysis runs through kernel → transform → gateway → ingestion → analytics, none of which the author controls. It can fail. |
| `gap-does-not-hide-the-removal` (`TIMING`) | **Yes** | Same. Can fail. |
| `refuelling-is-not-a-loss` (`NO_FALSE_POSITIVE`) | **Yes** | Same — and the capacity overfill found above is exactly the condition that would make it fail, which is an oracle doing its job. |
| `removed-volume-within-tolerance` (`MAGNITUDE`, 120 ± 10 L) | **Structurally yes, substantively partly** | The *structure* is a proper round-trip property: the analysis must recover the input across a path the author does not control. But **where did 10 come from?** The author imagined the error sources and picked a number. Nothing derives it, nothing falsifies it, and a tolerance that is too wide is an oracle that cannot fail. **An oracle that cannot fail is circularity wearing an assertion's clothes.** |

Concretely: the ±10 L band means the Finding passes for any Foundation
consumption assumption between 11.5 and 16.5 L/h. Nobody chose that range —
it fell out of a tolerance picked before anyone knew what the error sources
were. `[OPEN]` A tolerance should be *derived* from declared error sources
(Foundation coefficient spread, sample granularity, rounding), or at minimum
paired with a mutation test proving the oracle *can* fail.

So the private expectations do not merely relocate the circularity. Three
genuinely escape it. The fourth escapes in form and smuggles a smaller,
weaker version of the same thing in a constant.

### The missing oracle kind

Here is the gap that makes proposal (f) look like a deletion instead of a
relocation. `EXPECTATION_KINDS` in
`backend/assetops_backend/scenarios/models.py:289` holds exactly four values,
and its comment says each "names the kind of claim a future test would make
about a run." All four are about **analysis outcomes**. None is about **world
trajectory**.

So the author's most immediate and most confident expectation — *what the tank
does* — has nowhere falsifiable to go. That is why it ended up in the only
position available: a `REPORTED_OBSERVATION` value, which is a load-bearing
position, which made it circular.

**(i) `[PROPOSED]` Add a fifth oracle kind — `TRAJECTORY`.** A private
expectation asserting a private-state value at an offset, checked by the kernel
in tests, never published, never read by any executable path.

```yaml
- expectation_id: tank-level-when-reporting-resumes
  oracle_kind: TRAJECTORY
  state_key: fuel-tank-volume
  offset_minutes: 1590
  expected_value: 254
  unit: L
  statement: >-
    When reporting resumes, the declared causes have taken the tank to this
    level. If the kernel computes otherwise, one of the two is wrong.
```

**Is that a manually authored trace by another name?** No, and the difference
is exactly the rule above:

- A trace **as input**: the system reads it and reports it as the state. Being
  wrong causes agreement. Banished.
- A trajectory point **as oracle**: the kernel computes independently, the
  oracle is compared, disagreement fails a test. Being wrong causes a failure.
  This is a unit test's expected value.

`D-2026-09-21-causal-runtime-before-golden-traces` explicitly permits "independent
examples, boundary cases, and metamorphic checks." A `TRAJECTORY` oracle is the
first of those three.

**Two honest guards, or it becomes a trace again:**

1. **Sparse and purposeful.** One or two points that the scenario is *about* —
   not a sampled trajectory. A dense set of `TRAJECTORY` oracles is a trace in
   the oracle position, and it fits the kernel to the author's arithmetic.
2. **Weak proof, and say so.** If the author computes 254 L by hand and the
   kernel computes 254 L, what is proven is that two implementations of the
   same arithmetic agree. That catches unit errors, dispatch errors and
   half-open off-by-ones. It does **not** prove the physics is right. It is a
   regression guard, not a correctness proof.

### What fully escapes: relationships, not values

The strongest form of the author's knowledge is not a number. It is a
relationship:

- Doubling the removal doubles the loss.
- Moving the removal later leaves the earlier prefix identical.
- Removing the removal removes the discontinuity entirely.
- Changing the delivery changes nothing before offset 2400.

The author genuinely knows these, the kernel can genuinely violate them, and
**none of them requires the author to know the answer** — only the derivative.
T021's task file already requires exactly these as metamorphic tests.

> **The author's mental model is most legitimate when expressed as a
> relationship rather than as a value.** "Doubling the removal doubles the
> loss" is knowledge. "The tank is at 254 L" is arithmetic the author
> performed, which the kernel will either duplicate or contradict.

This is the real answer to the charge. The mental model does not have to be
banished — it has to be expressed in the form that can fail.

### The siphoning walk-through

An author sits down to write the Fuel Loss Event. No kernel exists anywhere.

**What they can write that is meaningful right now** — pinned by the
specification, identical under every conforming kernel:

```
  the tank starts at 430 L, and the scenario owns that value
  the generator draws 14 L/h from 1080 for 240 minutes  → exactly 56 L
  120 L leaves the tank over 45 minutes from 1500        → complete at 1545
  the sensor reports nothing from 1490 for 90 minutes    → reporting path only
  300 L arrives at 2400, bounded above by 500 L
  two sources exist: a configured device signal, and a human
```

**What they are forced to imagine** — none of it in the document, none of it
checkable today:

| The author imagines | Requires | Status pre-kernel |
| --- | --- | --- |
| the tank holds 254 L at 1590 | composition of causes | **imagined** — and they wrote 155 L, so they imagined it wrong |
| the sensor reads 254 L at 1590 | observation transform (T022) | **imagined** |
| the gap hides six samples | cadence × gap interaction | **imagined** — though the 15-minute cadence is frozen by run setup, so this is nearly computable and nothing computes it |
| overcast → low battery → generator dispatch | a PV/battery/dispatch model that will not exist | **imagined, and permanently** — the first kernel will never compute it |
| 300 L fits in the tank at 2400 | composition + bounds | **imagined, and false** |
| the product recovers ~120 L | the entire downstream chain | **imagined** |

**What of that can be recorded falsifiably today:**

- "A later analysis must attribute 120 ± 10 L" → `MAGNITUDE`. ✓
- "The gap must not prevent placing the removal" → `TIMING`. ✓
- "The removal must be separable from consumption" → `DETECTION`. ✓
- "The refuelling must not be attributed to the removal" → `NO_FALSE_POSITIVE`. ✓
- "The tank holds 254 L at 1590" → **nowhere.** Needs (i).
- "300 L fits at 2400" → **nowhere.** Needs (i), and would have caught the
  overfill before it shipped.

**What cannot be recorded at all:** overcast → dispatch. There is no model that
will compute it and therefore no oracle that can check it. The honest treatment
is the one `dispatched-output` already gets — say it in prose under
`NON_EXECUTABLE_CONDITION`, and accept that the document *hand-wires* a chain a
richer simulator would derive. That hand-wiring is not circularity; it is
**declared narrowness**, and the model profile's own statement already admits
it: *"Demand, irradiance and the availability of the reporting path are not
modelled."*

### The moment T021 disagrees

The kernel runs the shipped document and computes 254 L at 1590. The author
wrote 155 L. **Who is wrong?**

Nobody, automatically. The disagreement is information, and it has exactly
three resolutions:

| | Resolution | How you tell |
| --- | --- | --- |
| **a** | The kernel is wrong — a dispatch, unit, or boundary bug | Metamorphic tests also fail, or the arithmetic is checkable by hand |
| **b** | The author's arithmetic was wrong | The document's declared causes are what the author meant; the expectation was miscomputed |
| **c** | The author's **intent** was right and the document under-declares the cause | The causes are internally fine but reach a state the author never wanted |

For the shipped document it is **(c)**. The author wanted a tank near 155 L and
wrote causes reaching 254 L. The document under-declares the removal.

**Where the failure should surface:** in a test, when the kernel runs. A
disagreement between an author's expectation and computed behaviour is a test
failure — that is what test failures *are*.

**Where it actually surfaced:** at run setup, as a blocking reason on a Draft,
implying the *run* was the problem rather than the *document*. That is the
mislocation. It is worth being fair to T018 here: **reconciliation found a real
defect. It was not wrong to look. It was wrong about where to stand.**

### Was authoring-before-kernel a sequencing error?

**No — but the degree of separation was wrong, and the document's clean
layering is partly aspirational. Both halves of that are true and the second
half matters.**

Spec-before-implementation is the right order and T017 → T018 → T021 is not
the defect. What is a defect:

- A specification with no implementation cannot be tested, so it grew one, and
  the one it grew was shipped as a product feature.
- Three review rounds on `reconcile_reported_observations`, a simultaneity
  rule that had to be reversed after the first attempt, and four still-unpinned
  semantics are not four unrelated incidents. They are **one specification
  discovering it was underspecified by trying to implement itself.**
- A throwaway executable spike would have found them faster, cheaper, and
  without creating a second implementation to keep in sync.

**Honest correction to this document's own framing:** the three-stage diagram is
correct about *dependency direction* and about *what may cross which boundary*.
It is misleading if read as chronology. Authoring semantics and kernel semantics
are one language specification discovered in two places, and it is not finished.
Sections that read as a clean pipeline should be read as a clean *dependency
graph* built by iteration.

### What co-design actually looks like here

Not "build them together." Concretely:

1. **The spec is a document, not code.** `EXECUTION_CONTRACT_VERSION` versions
   a set of rules. It should not also implement them in the product path.
2. **The spec's falsifier is a spike, not a feature.** Where the spec needs
   exercising before a kernel exists, that belongs in the test suite, marked as
   a reference implementation, with a stated expiry.
3. **Unpinned points are inventoried, not discovered.** The four above are the
   current list. The question "what would two conforming kernels disagree
   about?" should be asked at every contract change, not found in review.
4. **The document is finalized after the kernel runs, not before.** This is the
   one real sequencing consequence, and it is
   [Open Question 9](#9-the-document-cannot-be-finalized-before-the-kernel-runs).

---

## Where Physical Properties Live

*Added after the second draft. The question: what do run setup's persist and
decide steps rest on, if the site is not faithfully modelled? The finding that
prompted it is that `generator-fuel-rate: 14 L/h` — a physical property of a
machine — lives in a scenario, because Foundation has no field that could hold
it.*

**The finding is correct, it is a live seam violation, and I filed its remedy
one milestone too late.** In [Open Question 4.2](#4-where-the-products-expectation-comes-from)
I placed the missing consumption coefficient with the product slices T034–T038,
as something the *product* needs to form an expectation. That is wrong. **The
kernel needs it at T021 to move the tank at all.** Corrected below and in that
question.

### What Foundation can express today

`SiteComponent` in `backend/assetops_backend/sites/models.py:367` has exactly
four fields:

```python
component_id: str
component_type: str
display_name: str
rating: Rating | None        # one scalar: value + unit
```

One optional scalar per component. `var/sites/mg-001.yaml` therefore says a
generator is `60.0 kW` and a fuel tank is `500.0 L`, and can say nothing else
about either.

And `FoundationBinding` at `runs/profiles.py:59` can address only that one
scalar:

```python
component_type: str
rating_unit: str
```

Run setup matches on `component_type == FUEL_TANK` and
`rating.unit == "L"` and takes the value when exactly one component matches.
**Even if Foundation grew a second physical property tomorrow, no binding
could reach it.** Two gaps, mutually reinforcing.

### The rule that decides ownership

Three owners are in play — Foundation, model profile, scenario — and a fourth,
the publication profile, for the reporting installation. The rule is two
swap tests:

> **Foundation declares what the site *is*. The model profile declares how the
> simulator *reasons* about things of that kind. The scenario declares what
> *happens* during one interval. The publication profile declares how the
> reporting installation *behaves*.**
>
> Swap the asset for another of the same type — does the value change? → **Foundation.**
> Swap the scenario — does it change? → **scenario.**
> Neither, but a better simulator would change it? → **model profile.**
> Neither, ever? → a universal constant, and it belongs in code.

Fuel consumption looked ambiguous — "a site-specific measured figure is a
Foundation fact; *diesel gensets consume X L/kWh* is a versioned model rule" —
but the ambiguity dissolves once you notice it is **two things wearing one
name**:

| | Swap the genset | Swap the scenario | Owner |
| --- | --- | --- | --- |
| *This* generator burns 14 L/h at its dispatch point | **changes** | unchanged | **Foundation** |
| Consumption is proportional to runtime (or to energy delivered) | unchanged | unchanged | **model profile** — a better simulator would use a load curve |
| The generator ran from 1080 for 240 minutes at 45 kW | unchanged | **changes** | **scenario** |

A coefficient and the law that consumes it are different objects with
different owners. The shipped document put the coefficient in the scenario,
which fails the first test decisively: run the same scenario against a
different generator and 14 L/h would follow the story rather than the machine,
which would mean the story had replaced the asset.

### The rule applied to everything the Fuel Loss path touches

| Property | Owner | Present today |
| --- | --- | --- |
| Fuel tank capacity, 500 L | Foundation | ✅ `rating` |
| Generator rated output, 60 kW | Foundation | ✅ `rating` |
| **Generator specific fuel consumption** | **Foundation** | ❌ **no field exists** |
| Fuel tank minimum usable level (the heel below the pickup) | Foundation | ❌ no field exists |
| Volume is non-negative | **model profile** — a modelling axiom, not a site fact | ❌ currently invented by the *validation layer*, see [Open Question 11](#11-physics-in-the-validation-layer) |
| Consumption is proportional to runtime | model profile | ❌ no carrier, see below |
| Generator starts stopped; cumulative consumption starts at 0 | model profile | ❌ no carrier |
| Starting fuel level, 430 L | scenario — *a Foundation says how large a tank is, never how full* | ✅ `[ACCEPTED]` |
| Dispatch window, removal, delivery quantities | scenario | ✅ |
| Reporting cadence, 15 min | publication profile | ✅ |

Note what the table does **not** say. Generator efficiency curve, minimum
load, ramp rate, tank geometry, sensor placement, battery chemistry, PV tilt,
orientation and derate are all absent from Foundation — and **none of them
blocks T021**, because the first kernel models none of the things they would
affect. The minimum set is not a wish list.

### The same gap from the other side: `MODEL_RULE` has no carrier

`INITIALIZATION_OWNERS` at `scenarios/models.py:208` declares four owners
including `MODEL_RULE`, and `ANSWERER_BY_INITIALIZATION_OWNER` at
`runs/models.py:83` faithfully maps it to `MODEL_PROFILE`. But `SupportedState`
at `runs/profiles.py:77` carries only `state_key`, `supported_roles`,
`foundation_binding` and `statement`. **There is no field a model-rule value
could live in.**

So a scenario may declare `owner: MODEL_RULE`, run setup will correctly name
`MODEL_PROFILE` as the answerer, and then there is nowhere for the answer to
come from. This is the T019 review's L9 finding, and it is the same defect the
Foundation gap is:

> **The vocabulary of owners is complete. The plumbing that carries their
> values is not.** Four owners are declarable; two of them —
> `MODEL_RULE` entirely, and `SITE_FOUNDATION` beyond one scalar per component
> — have no carrier.

Three holes, and they must move together or not at all:

1. `SiteComponent` and `TemplateComponent` can hold one scalar.
2. `FoundationBinding` can address only that scalar.
3. `SupportedState` can hold no model-rule value at all.

### The minimum set before T021

| # | What Foundation must declare | Blocks T021? |
| --- | --- | --- |
| 1 | **Generator specific fuel consumption**, as a named property with a unit | **Yes** — see below |
| 2 | Fuel tank minimum usable level | **No.** The shipped run never goes below 254 L. It can follow, and it is the honest home for the floor [Open Question 11](#11-physics-in-the-validation-layer) currently invents. |

And one carrier, from the other side:

| # | | Blocks T021? |
| --- | --- | --- |
| 3 | A `SupportedState` field for model-rule values | **Yes** — the first kernel initializes generator state and cumulative consumption from versioned model rules, and there is nowhere to declare them |

**Why (1) blocks, precisely.** It does not block *execution* — the kernel can
read 14 L/h from the scenario and run. It blocks *honesty*, and the cost is
asymmetric: T021 is the first kernel, and every kernel after it copies its
shape. A kernel whose physics arrive from the scenario teaches the next one to
do the same, and the separation this whole document exists to defend would be
violated at the exact moment it first becomes testable.

**Minimum versus better.** The simplest first kernel computes
`consumption = coefficient × elapsed runtime`, needing one Foundation scalar in
`L/h`. A slightly better one computes `consumption = coefficient × energy
delivered`, needing `L/kWh` plus a generator output — which is exactly the
`dispatched-output` promotion to `FORCING_INPUT` that
[Open Question 4.1](#4-where-the-products-expectation-comes-from) already
recommends for the *product's* sake. **One change, two payoffs**, and it avoids
migrating the coefficient's unit later. *My read: take the better one.*

### A consequence nobody has costed: templates copy

`.ai/ARCHITECTURE.md` is explicit — *"Configuration templates are instantiated
by copy… a later template change never alters an already-created instance."*

So adding the consumption property to
`config/site-templates/hybrid-mini-grid-100kw.yaml` **will not give it to
MG-001**, which was created by copy and lives in `var/sites/mg-001.yaml`. The
demo site must be re-created from the updated template, or the property
hand-added to the instance. Both are cheap — it is a development fixture —
but neither is automatic, and a slice that adds the field without saying this
will produce a site whose runs do not resolve the coefficient.

> **Whether that is a refusal or a block is under decision, and this sentence
> used to assert the refusal.** `runs/service.py` `_resolve_foundation_value`
> returns the blocking `INITIAL_VALUE_NOT_RESOLVED` when a binding matches
> nothing, and a Foundation carrying no such property is that case as the code
> stands. The refusal reading needs a way to say *the declared owner has no
> answer* that does not run through the profile's binding, and the T019
> review's discriminator argues there is none. See
> [What declares the need](#what-declares-the-need-once-the-scenario-stops-declaring-it),
> which is due before T020A. Do not read this paragraph as settled either way.
> What is not in doubt is that MG-001 must be re-created.

### What declares the need, once the scenario stops declaring it

**`[OPEN]` - decision due before T020A's task file. Options and a
recommendation below; the choice is the user's.**

(k) says the shipped template declares the generator's specific fuel
consumption, `generator-fuel-rate` leaves the scenario, and run setup freezes
the coefficient from Foundation. The three carriers (k) names are all
necessary, and none of them answers a fourth question the slice cannot avoid:
**once the scenario no longer declares the coefficient, what tells run setup
that the run needs it?**

Today nothing else could. `initialization_inputs()` in
`scenarios/execution.py` enumerates *scenario parameters* - those whose
ownership initializes, whose role is state-changing, and which carry a float
`value`. `_freeze` in `runs/service.py` walks that list and dispatches on the
owner, and the Foundation branch, `_resolve_foundation_value`, is reachable
only from it. Delete the parameter and run setup enumerates nothing, resolves
nothing and freezes nothing: the coefficient is not blocked and not refused,
it is absent, and T021's kernel has nothing to read.

A second thing is in the way and it is worth seeing before the options.
`generator-fuel-rate` is `initializes: false` today. It is a rate the dispatch
event consumes through `state_effect.rate_parameter_id`, not an initial world
value, and run setup's whole Foundation-resolution path is on the
initialization path. So "run setup freezes the coefficient from Foundation" is
not a small edit to an existing path under any option. Each option below
decides what kind of thing the coefficient is.

#### Option A - the scenario keeps the parameter and names Foundation the authority

Exactly the `fuel-tank-capacity` pattern already in the shipped document:
`owner: SITE_FOUNDATION`, `initializes: true`, value present and commented as
*the requirement run setup checks against that rating, not the value a run
would use*.

- **Cost: lowest.** `config/scenarios/fuel-loss-event.yaml` changes, plus the
  two carriers T020A already owns. No parser change, no `_freeze` change, no
  new answerer, no contract-version move.
- **Refuse versus block:** the contradiction refusal stays reachable, because
  the scenario still states a number for Foundation to contradict.
- **T021:** the coefficient arrives as a frozen initialization input in the
  shape the kernel already expects. No effect.
- **It preserves the thing (k) exists to remove.** The swap test in
  `D-2026-09-21-physical-property-ownership` says run the same scenario
  against a different generator and 14 L/h must not follow the story. Under A
  it does follow the story - as a requirement that now refuses the run. A
  scenario that cannot run against a 12 L/h genset has a physical property of
  a machine in it, wearing a checker's hat instead of an authority's.
  `fuel-tank-capacity` has the same defect today and nobody has called it; it
  is invisible only because tank capacity rarely varies between sites made
  from one template. If A is chosen, that is a second instance to schedule,
  not a precedent to lean on.

#### Option B - the scenario declares the need and states no value

`owner: SITE_FOUNDATION`, `initializes: true`, and **no value position at
all** for a Foundation-owned parameter - closed at the structure the way (g)
closes `execution_requirement` and T018 closed duration units, rather than as
a rule someone has to remember.

- **Cost: a parser change and a type change.** `InitializationInput.value`
  becomes optional, `initialization_inputs()` drops its
  `isinstance(parameter.value, float)` filter for this owner, and
  `_resolve_foundation_value`'s `declared` becomes optional.
- **It moves `EXECUTION_CONTRACT_VERSION`**, under
  `D-2026-09-22-contract-version-scope`: a document that was valid - one
  carrying a value beside a Foundation owner - is now refused, which is a
  narrowing and reaches documents that already exist. Worth pricing
  deliberately rather than discovering. It lands in the same free-window
  conversation as (g), and if B is chosen the sensible shape is for T020A's
  move and T021A's to be the two the sequence spends.
- **Refuse versus block:** with no stated value there are never two answers,
  so `INITIAL_VALUE_ANSWERS_DISAGREE` becomes unreachable for the
  coefficient. If B is later applied to `fuel-tank-capacity` too, that refusal
  kind has no producer at all - a vocabulary member naming a fact nothing can
  make, which is the `RUNNING` problem one layer down. Either keep a
  Foundation-owned parameter able to state a cross-check, or retire the kind
  when its last producer goes. Do not let it become unreachable by accident.
- **T021:** unchanged. The value still arrives frozen.
- **It is the option that satisfies the swap test.** The scenario says this
  run needs the generator's specific fuel consumption and Foundation answers;
  it states no number. Swap the genset and the run picks up the new number
  with no scenario edit. That is what (k) asked for.

#### Option C - the model profile declares the need

`SupportedState` already exists per state and already carries
`foundation_binding`. C says a supported state may also declare that it
*requires* a Foundation-supplied value at that address, and `_freeze`
enumerates from the profile as well as from the scenario.

- **Cost: highest, and it is the only option that changes the shape of the
  frozen identity.** `FrozenInitializationInput.parameter_id` is a scenario
  parameter id today; under C some frozen rows have no scenario parameter
  behind them. The deterministic identity is a protected seam, and T020A
  already changes Foundation's schema, so C makes two protected-seam changes
  in one slice.
- It also splits a column the frozen-inputs table does not have: the *need* is
  declared by the profile and the *value* is answered by Foundation, and
  "Answered by" carries one of those.
- Every run against this profile freezes the coefficient, including runs of
  scenarios that never dispatch a generator. Either right - the profile models
  a generator, so it always needs one - or noise on unrelated runs.
- **Refuse versus block: the cleanest of the three.** The need and the address
  are both the profile's, so a failure to answer is unambiguously a joint fact
  about the pair, everything blocks, and nothing is left to argue about.
- **It is where the need conceptually belongs.**
  `D-2026-09-21-physical-property-ownership` says *consumption is proportional
  to runtime* is a model rule and *this generator burns 14 L/h* is Foundation.
  The law is the thing that knows it needs a coefficient, and C puts the need
  beside the law.

#### Can run setup ever say Foundation declares no such property?

Six documents say a T020A that adds the property without re-creating MG-001
produces a site whose runs are **refused**. The code says otherwise, and so,
on inspection, does the discriminator the user chose.

`_resolve_foundation_value` reaches a refusal down exactly one path,
`rating.value != declared`: both owners answered and the numbers differ. Every
not-found - no binding, no match, more than one match, wrong unit - blocks. A
Foundation carrying no such property is a not-found, so it blocks.

The refusal reading needs run setup to establish *the declared owner has no
answer* without going through the binding. The T019 review's discriminator
says it cannot: a Foundation's answer is only locatable through the selected
profile's binding, so failing to locate it is a joint fact about the pair. And
after T020A the binding names the component type, the property and the unit,
so the property name is as much the profile's aim as the component type is. A
different profile naming a different property might find something MG-001 does
declare. Under the discriminator as chosen, that is a block.

The one way to keep the refusal is to **pin the property name outside the
profile**, so an absent property is the declared owner's silence rather than
the profile's aim missing - for instance by making the per-component-type
property vocabulary the register the scenario names and the binding only
locates. That vocabulary is authored rather than inferred, so consulting it is
not the match-by-spelling T019 forbade. The cost is that the address becomes a
three-part thing shared between scenario and profile, and the T019 principle
has to be restated rather than applied.

**This is the failure class this sequence keeps meeting.** The refusal claim
comes from `D-2026-09-21-physical-property-ownership`, written on 2026-09-21,
one day before the user moved the refusal line. It survived the move by being
re-asserted in the 2026-09-22 extension rather than re-derived against the new
discriminator, and five other documents copied it - plus
`tasks/T020A-foundation-physical-properties.md`, which is the Planner's.

#### Recommendation

**Option B, and correct the seven statements to say the runs block.**

B over A because A preserves the seam violation (k) exists to remove, and the
`fuel-tank-capacity` precedent is a second instance to schedule rather than a
reason to repeat it. B over C because C is more correct about where the need
lives but spends two protected-seam changes in one slice and puts a frozen row
behind no scenario parameter. C stays the right eventual home and should be
named as the follower: the first model rule that needs a Foundation value
without a scenario asking for it is what should carry it.

On the refusal, correct it. A block is what the code does, what the
discriminator implies, and the more useful outcome anyway, because the person
gets a persisted Draft naming the missing property instead of an error that
leaves nothing to inspect. T020A must still re-create MG-001; the reason
becomes *otherwise the demo site's runs never resolve the coefficient and the
slice's own UI-verifiable outcome never appears on screen*, which is a weaker
warning than a refusal and a sufficient one.

If the user would rather keep the refusal, the pinned-property-name variant
above is the way, and it should be decided as part of this rather than
discovered inside the slice.

### Does `READY` overreach?

**Yes, and it is the same pattern one layer up: a declaration with no
verifier.**

`ModelProfile.supported_states` is a hand-written tuple. Nothing checks it
against a kernel, because there is no kernel. So `READY` today means exactly:

> every required executable input names a state that appears in a hand-written
> tuple with a matching role, and every frozen value resolved.

Tested against this document's own rule — *an assertion is circular when being
wrong causes agreement* — if `minimal-fuel-tank` v1 claims `fuel-tank-volume`
and the eventual kernel does not implement it, the Draft is `READY` anyway.
Being wrong causes agreement. **Third instance of the same circularity.**

But it is not the same *kind* of defect as reconciliation, and the difference
decides the remedy. Reconciliation **computed** something it had no right to
compute. `supported_states` **declares** something it has no way to verify, and
declaring a capability you intend to build is what an interface is. The defect
is that the word `READY` reads as a claim about executability when what was
checked is agreement between two declarations.

**On the `RUNNING` precedent.** `runs/models.py:66` refused the executing
statuses because *"a status nothing can reach is a claim that execution
exists."* That argument does apply here — but there is a real distinction.
`RUNNING` could never be reached in this build: zero instances, pure fiction,
so deletion was the only honest move. `READY` **is** reached and **does**
assert something true, just less than its name suggests. Absence and
overstatement warrant different remedies.

**(l) `[PROPOSED]` — disclose now, verify at T021.**

- *Now, in T020:* state on the run record and on screen what `READY` does not
  assert. Something close to: *"Every required input resolved, and the selected
  model profile declares it can consume them. Nothing has verified that the
  model can execute them; no causal runtime exists yet."*
- *At T021:* a conformance test asserting that the shipped profile's
  `supported_states` equals the set of states the kernel actually implements —
  **derived from the kernel, not hand-maintained**. That closes it structurally
  rather than by discipline, which is the pattern this project already prefers
  for the cadence and duration-unit prohibitions.

*Why not rename.* `READY` becomes honest the moment the conformance test lands,
two slices away. Renaming ripples through the API payload, the frontend, the
tests and T020's screens — which are about to be built — to fix a word that is
about to become correct. **`[CLOSED]`** - the user took the disclosure and
declined the rename in `D-2026-09-21-run-setup-outcome-vocabulary` ("the
remedy is disclosure now and structural closure later, not a rename"), and
T020's task file carries it as a scope limit. The alternative, had it gone the
other way, was `RESOLVED` / `BLOCKED`: it names what was checked rather than
what is now possible.

---

## The Three Stages, In One Picture

```
  STAGE 1 · AUTHORING                    what a human writes down
  ┌──────────────────────────────────────────────────────────────────────┐
  │  ScenarioDefinition (versioned, immutable, strict-parsed)            │
  │                                                                      │
  │   CAUSAL_INPUT ──────────┐  may reach initialization and transitions │
  │   FORCING_INPUT ─────────┤  exogenous state the model does not solve │
  │   REPORTED_OBSERVATION ──┼─ presentation + expectation only          │
  │   NON_EXECUTABLE_COND ───┘  description; nothing consumes it         │
  │                                                                      │
  │   private_expectations ····· test oracle. Crosses NO boundary.       │
  └───────────────┬──────────────────────────────────────────────────────┘
                  │  frozen by run setup, with Site/Foundation version,
                  │  interval, timestep, seed, model + publication profile
                  ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │  SimulationRun (Draft)  ──  READY or BLOCKED, persisted, inspectable │
  └───────────────┬──────────────────────────────────────────────────────┘
                  │
  STAGE 2 · RUNTIME                      what the machine computes
                  ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │  KERNEL          initialize(frozen) → state₀                         │
  │                  step(state, t, Δt, due_events) → state′, events     │
  │                                                                      │
  │      PRIVATE WORLD STATE  ── fuel volume, generator state, forced    │
  │                              exogenous states. Never leaves the Lab. │
  └───────────────┬──────────────────────────────────────────────────────┘
                  │  sampled, not copied
                  ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │  OBSERVATION TRANSFORM                                               │
  │      cadence (publication profile) · reporting-path forcings         │
  │      (gap, bias, failure) · device + signal from Foundation          │
  │   → run-local Observation records, distinct objects from truth       │
  └───────────────┬──────────────────────────────────────────────────────┘
                  ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │  SOURCE ENVELOPES  STAGED → RELEASED                                 │
  └───────────────┬──────────────────────────────────────────────────────┘
       ═══════════╪═══════════ THE GATEWAY. The cause does not cross. ═══
                  ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │  INGESTION  → ACCEPTED | REJECTED  (received_at assigned here)       │
  └───────────────┬──────────────────────────────────────────────────────┘
                  ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │  PRODUCT                                                             │
  │    expectation built from Foundation configuration + accepted        │
  │    evidence only  →  observed − expected = unexplained variance      │
  │    →  Finding, with claim boundary and evidence basis                │
  └──────────────────────────────────────────────────────────────────────┘

  STAGE 3 · INJECTION runs against the kernel at simulation time, appending
  to run-scoped intervention history. It re-enters at the KERNEL box, never
  at the observation transform and never at the gateway.
```

The single most important property of this picture: **the 120 L removal never
crosses the gateway.** The product never learns that a removal was authored.
It learns that the tank lost 120 L that nothing it knows about explains. That
is what makes the Finding a finding rather than a readback.

---

## The Proposals

(e) through (h) came out of the third Architect consult; (i) and (j) come from
[Authoring Without A Kernel](#authoring-without-a-kernel); (k) and (l) from
[Where Physical Properties Live](#where-physical-properties-live). None is
accepted.

**(e) Run setup does not adjudicate cause-to-observation coupling.**
`[PROPOSED — AMENDS ACCEPTED GROUND]`
`OBSERVATION_NOT_ACCOUNTED_FOR` leaves the blocking-reason vocabulary.
Deciding whether declared causes reach a declared reading requires choosing a
transition rule, and whatever owns a transition rule is a kernel. Run setup
has no kernel. Amends the fourth proposal of
`D-2026-09-21-scenario-execution-contract`, specifically the clause *"later
run setup treats an unreached reading as a reason to block rather than as a
rounding matter."* Lands in T019.

**(f) A scenario does not author what a device reads.** `[PROPOSED]`
Reported observations are *generated* by the observation transform from
private state, at the cadence the publication profile declares, perturbed only
by declared reporting-path forcings. The authored 155 L and 150 L values are
replaced. Lands in T022, with the document edit due before T022 starts.

**(g) `execution_requirement` is forbidden on a `REPORTED_OBSERVATION`.**
`[PROPOSED — AMENDS ACCEPTED GROUND]`
Closed structurally at the parser, the way T018 closed duration units: there is
no position the field can occupy. With (e) in place, `REQUIRED` on a value no
executor reads is either vacuous or a category error. The displaced meaning —
"this run must produce such a reading" — already has a home in T017's private
expectations (`DETECTION`, `TIMING`). This narrows the space of conforming
behaviours, so `EXECUTION_CONTRACT_VERSION` moves 2 → 3. It is free now and
will not be after the first golden trace exists. Lands in T022 or a small slice
before it.

**(h) The projection-versus-composition line becomes a durable rule.**
`[PROPOSED]`
A candidate line for `.ai/ARCHITECTURE.md` under Causal Runtime Authority:

> Projecting a document is static validation. Composing projections into a
> value-at-a-time is a kernel. A component that owns a transition rule is a
> kernel regardless of what it is called, how narrow it is, or whether it
> emits a trajectory.

Lands as an Architect artifact, not in a code task.

**(i) Add a fifth oracle kind, `TRAJECTORY`.** `[PROPOSED]`
A private expectation asserting a private-state value at an offset, checked by
the kernel in tests, never published and never read by any executable path.
Without it, proposal (f) is a deletion: the author's expectation about what the
tank does has nowhere falsifiable to live, which is why it ended up as a
`REPORTED_OBSERVATION` value in the first place. With it, (f) is a relocation.
Rationale, guards and the "is this just a trace?" objection are in
[The missing oracle kind](#the-missing-oracle-kind). Lands in T021, because
T021 is what can check it.

**(j) Reconciliation survives as a test-only conformance oracle, not as
product behaviour.** `[PROPOSED — refines (e)]`
(e) removes the *feature*: the blocking reason and, later, the screen panel.
It does not have to remove the *arithmetic*. A specification with no
implementation cannot be tested, and the honest home for a reference
implementation is the test suite, explicitly labelled, with a stated expiry:
when T021 lands, the two are compared and whichever survives is the kernel.
This is a more precise diagnosis than "it crossed the line" — the line it
crossed was into the product path, not into existence. Lands in T019 alongside
(e).

**(k) Foundation gains physical properties, and the owner vocabulary gains its
missing carriers.** `[PROPOSED — new slice, before T021]`
`SiteComponent` and `TemplateComponent` gain named physical properties beyond
the single `rating` scalar; `FoundationBinding` gains the ability to address
one; `SupportedState` gains a carrier for model-rule values. Then
`generator-fuel-rate` moves out of the scenario and into the generator, where
it describes the machine rather than the story. This is the only proposal that
is **an insertion in the sequence rather than a narrowing** — see
[Sequencing Constraints](#sequencing-constraints). Lands in a new slice,
**T020A**.

**(l) `READY` discloses what it does not assert, and T021 verifies it.**
`[PROPOSED]`
`ModelProfile.supported_states` is hand-written and unverified, so `READY`
means two declarations agree rather than that execution is possible. Disclose
that on the record and on screen in T020; close it with a conformance test
in T021 that derives the supported set from the kernel rather than trusting
the tuple. Rationale, and why this is not the `RUNNING` case, in
[Does `READY` overreach?](#does-ready-overreach).

---

## Stage 1 — Scenario Authoring

### What a scenario is

`[SHIPPED]` A `ScenarioDefinition` is a versioned, immutable, strict-parsed
YAML document. The shipped one lives at
`config/scenarios/fuel-loss-event.yaml` and is read-only at runtime;
user-authored ones live under `var/scenarios/` and cross the same parser with
no lenient path. Identity is globally unique across both stores — no overlay,
no precedence.

`[SHIPPED]` It declares: identity and version
(`scenario_id`, `scenario_version`, `version_valid_from`, `supersedes`), a
target site requirement, observation sources, public parameters, a timeline of
entries, and private expectations.

### The four execution roles

`[ACCEPTED]` Every public parameter and every timeline entry carries exactly
one execution role. This is the axis that decides what an executor may do with
a value. It is orthogonal to the T017 entry kinds (`EVENT`, `INTERVENTION`,
`EVIDENCE_CONDITION`) and the seven categories.

| Role | May reach initialization? | May change private state? | What it is |
| --- | --- | --- | --- |
| `CAUSAL_INPUT` | yes | yes | A cause. The only role that can move the world. |
| `FORCING_INPUT` | no | no — it *is* state | An exogenous condition the model does not solve. Names the state it forces. May not declare a starting value: the profile answers at every instant including the first. |
| `REPORTED_OBSERVATION` | no | no | A reading through a named source. Carries no ownership and no state effect. |
| `NON_EXECUTABLE_CONDITION` | no | no | Description. Nothing consumes it. |

`[SHIPPED]` The role boundary is enforced at two independent layers, not
asserted: the parser refuses a state effect on a non-causal entry, and
`state_transition_inputs` in
`backend/assetops_backend/scenarios/execution.py` builds only from
`CAUSAL_INPUT` entries carrying a state effect.

`[PROPOSED]` (f) sharpens what `REPORTED_OBSERVATION` *is for* without changing
the vocabulary. Today it reads as "a value the contract checks the causes
against." It becomes "an expectation about what a run should produce, which no
executable path may read." The role survives untouched and is more necessary
under (f), not less — it is precisely what stops an authored reading reaching
a transition.

### Ownership of initial values

`[ACCEPTED]` Every initial world value has exactly one owner:
`SITE_FOUNDATION`, `SCENARIO_INPUT`, a run override, or a versioned model rule.
Two owners for one value is refused when the definition is read. This is the
model of a check that holds with no runtime — it is a property of the document,
decidable for every conforming kernel.

Worked through the shipped document:

| State | Owner | Why |
| --- | --- | --- |
| `fuel-tank-capacity` | `SITE_FOUNDATION` | A Foundation says how large a tank is. MG-001's `fuel-tank` component declares a 500 L rating. The scenario's 500 L is the *requirement run setup checks against*, not the value a run uses. |
| `fuel-tank-volume` | `SCENARIO_INPUT` | A Foundation never says how full a tank is. The scenario owns 430 L. A run may override it; nothing may leave it unstated. |

### Cadence

`[ACCEPTED]` **The scenario owns no cadence.** A Foundation declares that a
signal *can* report and declares its unit; it declares no rate. Nothing derives
a cadence from a device name, from displayed text, or from the spacing between
timeline rows.

`[SHIPPED]` The prohibition is closed at the unit vocabulary rather than per
position: no duration unit exists in `CANONICAL_UNITS`, so there is no position
a cadence can be written in. Cadence arrives only from a versioned publication
profile — today `LAB_PUBLICATION_PROFILE` with
`device_signal_cadence_minutes: 15`.

This is the cleanest example in the codebase of a prohibition made structural
rather than stated, and (g) proposes the same treatment for
`execution_requirement`.

### Timing shapes

`[ACCEPTED]` Three shapes, validated as distinct:

```
  POINT           │ applied by the step that begins at the offset
        ●         │ and by no other
  ────────────────┼──────────────────────────────────────────────
  WINDOW          │ declared length; a rate may only be declared
        ├────────┤│ over a window
  ────────────────┼──────────────────────────────────────────────
  INTERVAL_WIDE   │ the whole run interval
  ├──────────────┤│
```

`[ACCEPTED]` The run interval and every step are half-open, `[start, end)`. A
boundary entry is applied by the step that begins there and by no other, which
makes "applied exactly once" a property of the time model rather than a rule
someone has to remember.

### Bounds

`[ACCEPTED]` A bound is declared explicitly. Nothing is inferred from two state
keys sharing a prefix — `fuel-tank-capacity` bounds `fuel-tank-volume` only
because the document says so:

```yaml
bounds:
  state_key: fuel-tank-volume
  bound_kind: UPPER
```

`[ACCEPTED]` Every bound case does one of three things: refuse the definition,
fail the run, or produce a bounded change **recorded with the quantity it
refused**. There is deliberately no option meaning "clamp quietly" or "drop the
remainder."

`[PROPOSED]` `declared_bounds` stays where it is. It is a projection of the
document — it reports what the document declares and evolves nothing. What
leaves under (e) is the *bound walk* in `reconcile_reported_observations`,
which applies bounds to a running value, which is a transition rule.

### Observation sources

`[SHIPPED]` A source carries identity, kind, and cadence ownership. The shipped
document declares two:

- `fuel-level-sensor-reading` — `DEVICE_SIGNAL`, device `fuel-level-sensor`,
  signal `fuel-level`, `cadence_ownership: NOT_DECLARED`. The scenario
  validates the *shape* of those identities; whether MG-001 has them is
  resolved against the site store.
- `operator-hand-record` — `OPERATOR_RECORD`,
  `cadence_ownership: NOT_APPLICABLE`. A real source with its own identity and
  no device identity.

That second one matters more than it looks. It establishes that a human is a
source, publishes through a typed non-device path, and cannot be smuggled into
a device envelope.

### Private expectations

`[ACCEPTED]` Four oracle kinds — `DETECTION`, `MAGNITUDE`, `TIMING`,
`NO_FALSE_POSITIVE` — kept in their own parsed field with their own payload
builder. They never reach source envelopes, accepted evidence, operator UI,
exports, provenance, analytics, or Findings.

This is the correct home for "what a run should be able to demonstrate," and
under (g) it absorbs the meaning that `execution_requirement: REQUIRED` on a
reading was carrying badly.

**The rule that decides what belongs here** — derived in
[Authoring Without A Kernel](#the-rule-for-where-an-expectation-may-live):

> An expectation is legitimate when it occupies a position where being wrong
> causes a **failure**. It is circular when it occupies a position where being
> wrong causes **agreement**.

All four shipped oracle kinds are about *analysis outcomes*. None is about
*world trajectory*, which is why the author's expectation about the tank had
nowhere to go and ended up as an authored reading. **(i)** proposes a fifth
kind, `TRAJECTORY`, to close that. `[PROPOSED]`

`[OPEN]` The `MAGNITUDE` oracle's ±10 L tolerance is itself an unfalsifiable
constant — see [Open Question 10](#10-the-magnitude-tolerance-is-a-picked-number).

### What an author may not say, and why

This is the heart of Stage 1.

| An author may not… | Because |
| --- | --- |
| **declare what a device reads** `[PROPOSED (f)]` | A reading is a consequence of state plus a reporting path. Authoring it makes the scenario the sensor. |
| declare a resulting world state at a time | The kernel owns the transition from one state to the next. `[ACCEPTED]` |
| declare a cadence | A cadence is a property of the reporting installation, not of the story. `[ACCEPTED]` |
| declare a starting value beside a forcing input | The profile answers at every instant including the first; a starting value would be a second answer to one question. `[ACCEPTED]` |
| declare a breaker position or control mode | Whether a breaker is a device, component state, or both is a product decision nobody has made; naming one would make it by accident. `[ACCEPTED, T017]` |
| write a duration as a parameter unit | Structurally impossible — no duration unit exists in the vocabulary. `[SHIPPED]` |
| put a state effect on a non-causal entry | Structurally impossible — no such field exists on those entries. `[SHIPPED]` |
| let a private expectation reach a payload | Separate parsed field, separate builder, contract-tested. `[SHIPPED]` |

The pattern across the last three rows is the one worth keeping: **the best
prohibitions are the ones with no position to occupy.** (g) asks for one more
of those.

### What changes in Stage 1 under these proposals

| Item | Today | Under the proposals |
| --- | --- | --- |
| `level-after-the-gap: 155 L` | `REPORTED_OBSERVATION`, `REQUIRED`, reconciled against causes | Value removed. The entry survives as an `EVIDENCE_CONDITION` asserting *a reading arrives here and is materially below what dispatch accounts for*, backed by a `DETECTION` expectation. The run generates the number. |
| `hand-recorded-level: 150 L` | `REPORTED_OBSERVATION`, `REQUIRED` | The *act* survives — a person went and looked, at offset 1800, through `operator-hand-record`. The *value* is generated from truth at 1800, optionally perturbed by a declared reading-error forcing. `[OPEN]` whether to model that error. |
| `execution_requirement` on those entries | `REQUIRED` | Field forbidden on the role. `[PROPOSED (g)]` |
| `dispatched-output: 45 kW` | `NON_EXECUTABLE_CONDITION` | `[PROPOSED]` promote to `FORCING_INPUT` on `generator-output-power`, so the generator controller has something to publish and the product can derive run hours. See [Open Question 4](#4-where-the-products-expectation-comes-from). |
| Everything else | — | Unchanged. |

---

## Stage 2 — Runtime

### The contract

`[ACCEPTED]` The runtime contract is two operations and nothing else:

```
    initialize(frozen_run) ──────────────► state₀
    step(state, t, Δt, due_events) ──────► state′, runtime_events
```

`[ACCEPTED]` The kernel owns initialization and the transition from one private
world state to the next. It does not import UI, gateway, ingestion, or product
analytics.

### Initialization

`[ACCEPTED]` Every initialized value is attributable to a frozen Foundation
fact, an executable scenario input, a supported run override, or a versioned
model rule. Missing or ambiguous inputs produce a **typed refusal**, never a
hidden default.

For the shipped run:

```
  fuel-tank-capacity   500 L   ← Foundation: MG-001 fuel-tank rating
  fuel-tank-volume     430 L   ← Scenario: starting-fuel-level
  generator state      off     ← Model rule (versioned)
  cumulative consumed  0 L     ← Model rule (versioned)
```

`[OPEN]` There is a boundary question here that T019 and T021 answer
differently and neither is wrong: run setup **refuses** (no `run_id`, nothing
persisted) versus **blocks** (persisted Draft, inspectable reasons). See
[Open Question 6](#6-the-refuse-versus-block-boundary-at-initialization).

### Event dispatch

`[ACCEPTED]` Half-open steps. An event due at offset `o` is applied by the step
`[o, o+Δt)` and by no other. This holds at the run start boundary, at every
internal step boundary, and at the excluded final boundary.

`[OPEN]` Two within-step ordering questions the contract does not yet answer,
both of which would let two conforming kernels disagree and therefore both of
which are `EXECUTION_CONTRACT_VERSION` business:

1. **Apportionment.** A quantity declared over a window — 120 L over 45
   minutes — does it ramp linearly across the steps in the window, or land at
   the completion boundary? T018 explicitly said apportioning a window "would
   be a transition rule" and belongs to the kernel, so this is genuinely T021's
   to decide, but it must be *declared*, not left to the implementation.
2. **Observe before or after.** Within one step, does the observation transform
   sample the state before or after the step's due events are applied? For the
   shipped run this changes the sample at offset 2400 from 254 L to 500 L.

### Private world state

`[ACCEPTED]` For the first kernel: simulation time, fuel quantity, generator
operating state, and cumulative generator consumption, in canonical units. Plus
the accepted load and irradiance forcings *carried as supported runtime inputs
without claiming power-flow consequences the model does not calculate.*

That last clause is the honest core of a narrow kernel: carrying a forcing is
not a claim that all its consequences are modelled.

`[SHIPPED]` The shipped model profile `minimal-fuel-tank` v1 supports exactly
two states — `fuel-tank-volume` and `fuel-tank-capacity`. It does not support
`site-load-demand`, `plane-of-array-irradiance`, or
`fuel-level-reporting-availability`, which is why the shipped Draft is
`BLOCKED`.

### The observation transform: how a reading is made

`[ACCEPTED, T022]` This is the seam the whole document exists for. A device
observation is **generated**, never authored:

```
   private state at t          reporting-path forcings        Foundation
   ─────────────────           ───────────────────────        ──────────
   fuel-tank-volume            reporting availability         device_id
   = 254.0 L                   sensor bias                    signal_id
        │                      failure / dropout              unit
        │                               │                        │
        └───────────────┬───────────────┴────────────────────────┘
                        ▼
              ┌──────────────────────┐
              │ OBSERVATION TRANSFORM│   cadence from the frozen
              │                      │   publication profile (15 min)
              └──────────┬───────────┘
                         ▼
              Observation record (run-local)
                 source_id, device_id, signal_id, component_id
                 source_time (simulation time)
                 value, unit, quality
                 run_id, mapping version, Foundation version
```

Three properties make it a real seam rather than a copy:

1. **Sampled, not copied.** The transform runs on the profile's cadence, not on
   the kernel's timestep. Truth exists at every step; a reading exists only at a
   sample.
2. **Perturbable on the reporting path.** A reporting-path forcing changes what
   is reported without changing what is true. The shipped
   `fuel-level-reporting-gap` is exactly this — a `FORCING_INPUT` on
   `fuel-level-reporting-availability`, carrying no state effect, explicitly
   commented as "a condition forced on the reporting path, not on the tank."
3. **Distinct objects.** `SimulatorLab1.png` already draws this: the Site State
   panel shows `Fuel Level (true) 274 L` and `Fuel Level (sensor) 289 L`, and
   the Devices & Sensors table has separate `Truth Value` and `Sensor Value`
   columns. The mockup's sensor value is *above* truth because a `+5% tank
   bias` event is scheduled at 18:30. The design you drew already assumes
   generated observations. (f) is asking the code to catch up with the mockup.

`[PROPOSED]` The reporting-path forcing family needs no new execution role.
`fuel-level-reporting-availability` shows the shape: a `FORCING_INPUT` whose
`state_key` names a state of the reporting path rather than of the world. A
sensor bias would be a `FORCING_INPUT` on `fuel-level-sensor-bias`. The
Scenarios list in `ScreenMockups.png` already has a `Sensor Bias` scenario
typed `Data Quality — Meter over-reads by 5%`, so this is consistent with the
product you drew.

`[OPEN]` Which profile owns a reporting-path state — see
[Open Question 3](#3-model-profile-versus-publication-profile-authority).

### The operator record

`[ACCEPTED, T022]` The hand inspection becomes a run-local **manual operational
observation** with its explicit non-device source identity and occurrence time.
It is not copied from a scenario timeline row into an envelope; T023 may publish
only this persisted observation, through its typed non-device path.

`[PROPOSED (f)]` Its *value* is generated too — from truth at offset 1800,
optionally perturbed by a declared reading error. The timeline entry keeps the
act and loses the number.

### What the gateway publishes

`[ACCEPTED]` A Source Envelope carries source identity, Site identity,
schema/message identity, `source_time`, `published_at`, sequence identity,
provenance (run, Foundation version, mapping version), and exactly one
strongly-typed record. `received_at` is assigned by ingestion and by nothing
else.

`[ACCEPTED]` What may **never** cross: private world state, authored causes,
private expectations, run-scoped injection records as evidence, and the
scenario document itself.

For the shipped run, the envelopes are:

- fuel-level telemetry from `fuel-level-sensor` / `fuel-level`, every 15
  minutes, suppressed during the gap;
- generator telemetry from `generator-controller` / `ac-power`
  `[PROPOSED, see Open Question 4]`;
- one operational record for the operator's hand reading at offset 1800.

The 120 L removal appears in none of them. That is the point.

### Where the product's expectation comes from

`[ACCEPTED, T034–T038]` The conclusion chain is ordered: Gateway/Source Health
→ Generator Runtime Assessment → Fuel Reconciliation → Finding.

For Fuel Reconciliation to produce a number, the product needs three things
from accepted evidence and Foundation configuration **only**:

```
   observed decrease   ← accepted fuel-level telemetry, two samples
   recorded deliveries ← accepted operational records
   expected consumption← generator run hours (accepted generator telemetry)
                         × a consumption coefficient (Foundation configuration)

   unexplained variance = observed decrease − expected consumption
                                            + recorded deliveries
```

`[OPEN]` **Neither input for expected consumption exists today.** The generator
controller publishes `ac-power` and `output-voltage`, but the scenario types
generator output as `NON_EXECUTABLE_CONDITION` so nothing computes it and
nothing publishes it; and MG-001's Foundation declares a 60 kW generator rating
with no fuel-consumption assumption at all. This is the single largest gap
between here and a Finding, and it is
[Open Question 4](#4-where-the-products-expectation-comes-from).

The seam that must not be crossed, whatever the answer:

> The consumption coefficient the product uses must come from **Foundation
> configuration**, never from the scenario's `generator-fuel-rate`. The
> scenario's rate is private simulator truth. If the product read it, the
> Finding would be computed from the cause and the loop would be circular
> again — the same circularity, one layer down.

A pleasant consequence: because the coefficients differ, the product's answer
is *approximately* right rather than exactly right, which is why the
`MAGNITUDE` oracle has a ±10 L tolerance and why the Finding language is
bounded. The arithmetic is shown in the worked example.

---

## Stage 3 — Injectable World Perturbation

### What it is

`[ACCEPTED]` `D-2026-09-20-run-scoped-event-injection`: runtime event injection
is **run-scoped intervention history under SimulationRun identity**, not
authored scenario content and not a top-level scenario artifact.

`SimulatorLab1.png` draws it as the `Quick Actions (Inject Event)` panel:
Fuel Delivery, Remove Fuel, Change Load, Generator Fault, Inverter Fault,
Battery Fault, Sensor Failure, Gateway Outage, Weather Event, Door Open,
Maintenance, Custom Event. The Event Timeline distinguishes scheduled events
from injected ones — the mockup's entry reads
`14:00:00 · Fuel removed from tank · -40 L (injected)`.

### Why it is run history, not scenario content

Three reasons, in order of force:

1. **A scenario version is immutable.** Injecting during a run cannot modify the
   scenario, because the run froze a specific version and other runs share it.
2. **An injection has no authored time.** It happens at the simulation time the
   operator pressed the button, which is a fact about this run.
3. **Determinism.** The ordered intervention history is part of the run's
   deterministic identity. Rerunning with the same frozen inputs *and the same
   intervention history* must reproduce the run exactly. If injections lived in
   the scenario, "the same scenario" would mean different things to two runs.

### How it relates to authored causes

They meet inside the kernel and nowhere else:

```
   authored causes ─────┐
   (frozen at setup)    │
                        ├──► due-event queue ──► step() ──► state′
   injected causes ─────┘
   (appended at run time)
```

`[ACCEPTED]` An injection is dispatched through the *same* event path as an
authored cause, with the same role vocabulary, the same canonical units, the
same half-open exactly-once semantics, and the same bound behaviour. An
injection that would breach a bound gets the bound case, not a special case.

`[PROPOSED]` An injection carries the same four execution roles. A `Remove
Fuel` injection is a `CAUSAL_INPUT`; a `Sensor Failure` injection is a
`FORCING_INPUT` on a reporting-path state; a `Gateway Outage` injection is a
forcing on the publication path. This is why the roles are worth keeping
general — they were designed for authored content and they carry over to
injection unchanged.

### What it demands

Of the kernel:

- Events arriving *after* initialization, appended to a queue the kernel did not
  have at `t=0`.
- A stable identity for each injected event, distinct from authored event
  identities, so the timeline and the runtime event log can tell them apart.
- No retroactive injection. An injection applies at or after the current
  simulation time; injecting into the past would invalidate the state already
  computed. Pause, step, and fast-forward do not change this — the current
  simulation time is the floor.
- Reset restores the same frozen initial state **and** must decide whether it
  clears intervention history. `[OPEN]`

Of the frozen identity:

- Intervention history becomes an ordered, appended part of run provenance.
- A golden trace's provenance must bind the intervention history that produced
  it. A trace generated with injections replays only against the same ordered
  history; a mismatch **refuses playback** rather than falling back.

### When it lands

`[ACCEPTED]` **After** scheduled-event causality is proven. The feature map is
explicit: *"Add run-scoped injection only after scheduled-event causality is
proven; it is not part of the initial T020–T022 sequence."* It is deferred
beyond T022 unless explicitly replanned.

The reason is the same principle as everywhere else: an injection control that
appears to change the world before the world is computed from causes would be
the most convincing hand-simulation the product could ship.

---

## Worked Example: The Fuel Loss Event, End To End

One narrative, real numbers, checkable arithmetic. Interval start is offset 0;
all offsets are minutes. Cadence is 15 minutes, from
`LAB_PUBLICATION_PROFILE` v1.

### The authored document `[SHIPPED]`

| Offset | Entry | Role | Effect |
| --- | --- | --- | --- |
| — | `starting-fuel-level` 430 L | `CAUSAL_INPUT` | initializes `fuel-tank-volume` |
| — | `tank-capacity` 500 L | `CAUSAL_INPUT` | UPPER bound on `fuel-tank-volume` |
| — | `generator-fuel-rate` 14 L/h | `CAUSAL_INPUT` | rate for the dispatch window |
| 0 (interval-wide) | `baseline-load-profile` | `FORCING_INPUT` | `site-load-demand` |
| 720 (+360) | `overcast-day` | `FORCING_INPUT` | `plane-of-array-irradiance` |
| 1080 (+240) | `generator-run-window` | `CAUSAL_INPUT` | DECREASE at 14 L/h |
| 1490 (+90) | `fuel-level-reporting-gap` | `FORCING_INPUT` | `fuel-level-reporting-availability` — **no state effect** |
| 1500 (+45) | `unaccounted-fuel-removal` | `CAUSAL_INPUT` | DECREASE 120 L |
| 1590 | `fuel-level-after-the-gap` | `REPORTED_OBSERVATION` | authored 155 L ← **placeholder** |
| 1800 | `operator-tank-inspection` | `REPORTED_OBSERVATION` | authored 150 L ← **placeholder** |
| 2400 | `scheduled-refuelling` | `CAUSAL_INPUT` | INCREASE 300 L |

Private oracle: the volume any later analysis attributes to the removal must be
**within 10 L of 120 L**.

### Step 1 — What the tank truly does `[PROPOSED (f)]`

The kernel computes this. Nothing in the document states it.

| Offset | What happens | Δ | `fuel-tank-volume` |
| --- | --- | --- | --- |
| 0 | initialize from `starting-fuel-level` | — | **430.0 L** |
| 1080 → 1320 | dispatch, 14 L/h = 0.2333… L/min over 240 min | −56.0 | **374.0 L** at 1320 |
| 1490 → 1580 | reporting gap — reporting path only | 0 | 374.0 L |
| 1500 → 1545 | removal, 120 L | −120.0 | **254.0 L** at 1545 |
| 1800 | operator inspects — observation only | 0 | 254.0 L |
| 2400 | delivery, 300 L, against a 500 L upper bound | +246.0 | **500.0 L**, 54.0 L refused |

Check: `430 − 56 − 120 = 254`. The rate integrates exactly —
`14 L/h × 4 h = 56 L` — because `CANONICAL_UNITS` carries the conversion as an
exact ratio rather than a float, so the answer is 56 and not 56.000000000000001.

**The delivery breaches the capacity bound.** `254 + 300 = 554 > 500`. This is
the third bound case: a bounded change, recorded with the 54 L it refused. It is
correct behaviour, and it is also a signal worth your attention — see
[Open Question 2](#2-what-the-fuel-loss-document-should-author).

### Step 2 — What the device reports `[PROPOSED (f)]`

The observation transform samples truth every 15 minutes and suppresses samples
while `fuel-level-reporting-availability` is forced unavailable over
`[1490, 1580)`.

```
  L
 500 ┤                                                          ┌────────
     │                                                          │
 430 ┤────────────────────┐                                     │
     │                    ╲   dispatch                          │
 374 ┤                     ╲__________ ● ● ● ●                  │
     │                                          ┊ gap ┊         │
 254 ┤                                          ┊     ┊● ● ● ● ●┘
     │                                          ┊     ┊
   0 └─┬────────┬────────┬────────┬────────┬────┬─────┬─────┬────┬──►
       0      720     1080     1320     1485  1490  1590  1800  2400
                                                                  min
       ●  device sample (15 min cadence)
       ┊  suppressed — reporting gap
```

| Sample | Truth | Reported | Note |
| --- | --- | --- | --- |
| 0 | 430.0 | 430.0 L | |
| 1080 | 430.0 | 430.0 L | dispatch begins |
| 1095 | 426.5 | 426.5 L | 3.5 L per 15 min |
| 1320 | 374.0 | 374.0 L | dispatch ends |
| 1335 … 1485 | 374.0 | 374.0 L | eleven flat samples |
| **1485** | 374.0 | **374.0 L** | **last sample before the gap** |
| 1500, 1515, 1530, 1545, 1560, 1575 | 374.0 → 254.0 | *(none)* | **six samples suppressed — the step is hidden** |
| **1590** | 254.0 | **254.0 L** | **first sample after the gap** |
| 1800 | 254.0 | 254.0 L (device) + 254.0 L (operator record) | two independent accounts |
| 2400 | 500.0 | 500.0 L | post-delivery, subject to Open Question 1.2 |

Note what happened at 1590: offset 1590 sits exactly on the 15-minute grid and
is exactly the first sample after the gap ends at 1580. **The authored 155 L
was a hand-simulation of precisely this generated sample, and it was wrong by
99 L.** That is the clearest single piece of evidence for (f).

### Step 3 — What the gateway publishes `[ACCEPTED, T023]`

Staged Source Envelopes, one typed record each:

```
  ┌─ envelope ────────────────────────────────────────────────────┐
  │ schema      telemetry.v1                                      │
  │ site        MG-001                                            │
  │ source      simulator-lab-source   gateway  simulator-lab-gw  │
  │ device      fuel-level-sensor      signal   fuel-level        │
  │ component   fuel-tank              unit     L                 │
  │ source_time <interval start + 1590 min>                       │
  │ published_at <...>        received_at  — (ingestion assigns)  │
  │ provenance  run_id · foundation v · mapping v · scenario v1   │
  │ record      { observed_at: …, value: 254.0, quality: GOOD }   │
  └───────────────────────────────────────────────────────────────┘
```

Plus one `OperationalRecord` at 1800 from `operator-hand-record`, with
`occurred_at` and no device identity.

**Not published, at any point:** `unaccounted-fuel-removal`, `volume-removed:
120`, `generator-fuel-rate`, the private expectations, or any private state
value.

### Step 4 — What the product can explain `[ACCEPTED, T034–T038]`

The product now holds accepted telemetry and knows nothing about the removal.

**Path A — the gap-bracketed reconciliation.** This is the sharp one.

```
  last accepted fuel-level sample before the gap    374.0 L  @ 1485
  first accepted fuel-level sample after the gap    254.0 L  @ 1590
  ────────────────────────────────────────────────────────────────
  observed decrease                                 120.0 L  over 105 min

  generator ac-power over [1485, 1590]                0 kW   (accepted evidence)
  → generator run hours in window                     0.00 h
  → expected consumption                              0.0 L
  recorded deliveries in window                       0.0 L
  ────────────────────────────────────────────────────────────────
  UNEXPLAINED VARIANCE                              120.0 L
```

**Finding:** *120 litres left the generator fuel tank between minute 1485 and
minute 1590 with no generator operation and no recorded delivery to account for
it. The level was not reported for 90 minutes across that period, so the
variance is bracketed by the samples either side of the gap rather than
observed directly.*

Oracle check: 120.0 L is within 10 L of 120 L. **`MAGNITUDE` passes.**
`TIMING` passes — the gap did not prevent placing the removal in the interval.
`NO_FALSE_POSITIVE` requires the delivery not be attributed to the removal;
Path A's window ends at 1590, well before 2400, so it is not.

**Path B — whole-interval fuel reconciliation.** This is the one that needs a
Foundation coefficient, and it shows why the tolerance exists.

```
  opening accepted sample                           430.0 L  @ 0
  last accepted sample before the delivery          254.0 L  @ 2385
  recorded deliveries in that window                  0.0 L
  ────────────────────────────────────────────────────────────────
  observed decrease                                 176.0 L

  generator ac-power > 0 over [1080, 1320]         → 4.00 h run time
  × Foundation consumption assumption
        if Foundation declares 14 L/h  → expected  56.0 L → unexplained 120.0 L ✓
        if Foundation declares 15 L/h  → expected  60.0 L → unexplained 116.0 L ✓
        if Foundation declares 13 L/h  → expected  52.0 L → unexplained 124.0 L ✓
        if Foundation declares 11 L/h  → expected  44.0 L → unexplained 132.0 L ✗
        if Foundation declares 17 L/h  → expected  68.0 L → unexplained 108.0 L ✗
```

The oracle band is [110 L, 130 L], so the Finding survives any Foundation
consumption assumption between 11.5 and 16.5 L/h and fails outside it. That is
exactly the right behaviour: the product's answer is bounded by how well the
site is configured, the Finding language must say so, and a Foundation
assumption that is badly wrong should fail the oracle rather than be quietly
absorbed. It also
demonstrates the seam — if the product read `generator-fuel-rate` from the
scenario it would get 120.0 L every time and learn nothing.

### Step 5 — What becomes of 155 L and 150 L

| | Today | Under (f) |
| --- | --- | --- |
| **155 L** @ 1590 | Authored `REPORTED_OBSERVATION`, `REQUIRED`. Reconciliation computes a −99 L residual against declared causes and T019 blocks the Draft on it. | Gone. The generated sample at 1590 is 254.0 L. The entry survives as an `EVIDENCE_CONDITION` — *a reading arrives here and is materially below what dispatch accounts for* — with no number. |
| **150 L** @ 1800 | Authored `REPORTED_OBSERVATION`, `REQUIRED`. Residual −104 L, second blocking reason. | The *act* survives at 1800 through `operator-hand-record`. The *value* is generated: 254.0 L, or 254.0 L minus a declared reading error if you choose to model one. |
| **−99 L / −104 L** | Published on the scenario detail screen as `observation_reconciliation`, and converted into two `OBSERVATION_NOT_ACCOUNTED_FOR` blocking reasons. | Gone. Nothing computes them, because nothing should. The product-side **120.0 L** replaces them, and it is a different object: a disagreement between published evidence and product-side expectation, not between two authored numbers. |

The earlier Architect read warned that changing the causes would delete the
eventual product payload. The arithmetic above shows it does not. The payload
was never the scenario's residual — it is the product's inability to explain
observed evidence with what it knows.

---

## Mock Screens

ASCII, drawn against `SimulatorLab1.png` and `ScreenMockups.png`. Each says
which task delivers it and what is proposed versus shipped.

### 1. Scenario Detail, as it should end up — T017 `[SHIPPED]` + T018 `[SHIPPED]` + (f)(g) `[PROPOSED]`

```
 Scenarios › Fuel Loss Event (v1)                          [Edit] [Duplicate]
 ══════════════════════════════════════════════════════════════════════════
  Fuel Loss Event  (v1)   ⟨Loss/Fraud⟩
  Overview │ Events │ Parameters │ Execution Contract │ Usage
 ──────────────────────────────────────────────────────────────────────────
  EVENT TIMELINE                          │ ENTRY DETAIL
  ────────────────────────────────────    │ ──────────────────────────────
   0      ● Baseline load        FORCING  │ Unaccounted fuel removal
   720    ● Overcast day         FORCING  │ Loss/Fraud · EVENT
   1080   ● Generator dispatch   CAUSE    │ Role      CAUSAL_INPUT
          │ 240 min · 14 L/h              │ Timing    window, 45 min
   1490   ◌ Reporting gap        FORCING  │ Effect    DECREASE 120 L
          │ 90 min · reporting path       │ State     fuel-tank-volume
   1500   ● Fuel removal         CAUSE    │ Required  yes
          │ 45 min · −120 L               │
   1590   ◇ Level reported       EXPECTED │ "Fuel leaves the tank outside
          │ a reading arrives here        │  any dispatch or refuelling
   1800   ◇ Operator inspects    EXPECTED │  window. This is the authored
   2400   ● Scheduled refuelling CAUSE    │  cause the scenario exists for."
          │ +300 L                        │
 ──────────────────────────────────────────────────────────────────────────
  EXECUTION CONTRACT                         contract version 3
  ────────────────────────────────────────────────────────────────────────
  Initialization      fuel-tank-volume    430 L   scenario
                      fuel-tank-capacity  500 L   site foundation
  Declared bounds     fuel-tank-volume    upper 500 L  ·  lower 0 L
  Declared causes     3   ·  Forcings  3  ·  Expected readings  2
 ──────────────────────────────────────────────────────────────────────────
  ⓘ This scenario declares causes. It does not declare what the tank holds
    at any time, and it does not declare what a device reads. Those are
    computed by a run.
```

Changes from shipped: the two `REPORTED_OBSERVATION` rows lose their values and
read as expectations (`◇ EXPECTED`); the `observation_reconciliation` panel —
today rendered at `frontend/src/shell/ScenarioFrame.tsx:767` with its
`declared_value / reported_value / difference` columns — is gone; the footnote
replaces it. Removing that panel is a **visible product change on merged work**
and needs its own slice — see
[Open Question 5](#5-when-the-reconciliation-panel-leaves-the-scenario-screen).

The reference mockup's own version of the footnote is worth noting: screen 6 of
`ScreenMockups.png` carries *"Note: This creates a discrepancy between expected
and measured fuel consumption"* — authored intent, stated in words, with no
arithmetic. The mockup was right.

### 2. Run Setup — T019 `[SHIPPED]`, with (e) `[PROPOSED]`

```
 Simulator Lab › New Run
 ══════════════════════════════════════════════════════════════════════════
  ①  Select Site  ──  ②  Select Scenario  ──  ③  Configure  ──  ④  Review
 ──────────────────────────────────────────────────────────────────────────
  SITE                      SCENARIO                  TIME WINDOW
  ◉ MG-001 Demo Mini-Grid   Fuel Loss Event (v1) ▾    Start  2026-01-01
  ○ CR-001 Cold Room        View scenario details →   Length 7 days
  ○ C&I-001 Clinic                                    Step   1 second

  MODEL PROFILE             PUBLICATION PROFILE       SEED
  minimal-fuel-tank v1 ▾    simulator-lab v1     ▾    784331
 ──────────────────────────────────────────────────────────────────────────
  FROZEN INPUTS                                    no value is pre-filled
  ────────────────────────────────────────────────────────────────────────
  fuel-tank-capacity   500 L    site foundation   MG-001 fuel-tank rating
  fuel-tank-volume     430 L    scenario          starting-fuel-level
  cadence              15 min   publication profile
  source / gateway     simulator-lab-source / simulator-lab-gateway
 ──────────────────────────────────────────────────────────────────────────
  ⛔ THIS RUN WOULD BE BLOCKED — 3 reasons
  ────────────────────────────────────────────────────────────────────────
  ● site-load-demand                      STATE_NOT_SUPPORTED
    The selected model profile does not model demand. The scenario requires
    it, so this run cannot execute against this profile.
  ● plane-of-array-irradiance             STATE_NOT_SUPPORTED
  ● fuel-level-reporting-availability     STATE_NOT_SUPPORTED
 ──────────────────────────────────────────────────────────────────────────
                                            [Cancel]  [Create Draft anyway]
```

Under (e) this screen loses two reasons — the two
`OBSERVATION_NOT_ACCOUNTED_FOR` entries — and keeps three. The Draft is still
`BLOCKED`, still persisted, still inspectable. **The outcome you already
accepted at the T019 checkpoint does not change; only the reason count does.**

### 3. Runs Inventory — T020 `[ACCEPTED, planned]`

```
 Simulator Lab › Runs
 ══════════════════════════════════════════════════════════════════════════
  Run       Site     Scenario            Lifecycle  Execution  Interval
  ─────────────────────────────────────────────────────────────────────────
  MG-001-03 MG-001   Fuel Loss Event v1  Draft      ⛔ Blocked  Jan 1 → Jan 8
  MG-001-02 MG-001   Fuel Loss Event v1  Draft      ◷ Ready     Jan 1 → Jan 8
  MG-001-01 MG-001   Normal Day v1       Committed  ✓ Completed Dec 1 → Dec 8
 ──────────────────────────────────────────────────────────────────────────
  Record-backed facts only. No health, no progress, no evidence state.
```

### 4. Run Detail, Draft — T020 `[ACCEPTED, planned]`

```
 Simulator Lab › Runs › MG-001-03
 ══════════════════════════════════════════════════════════════════════════
  ⛔ Run MG-001-03   Draft · Blocked
  Site MG-001 · Scenario Fuel Loss Event v1 · Seed 784331
  Interval Jan 1 00:00 → Jan 8 00:00  ·  Step 1 s
 ──────────────────────────────────────────────────────────────────────────
  [ ▶ Run ]  disabled — this Draft is blocked; see the reasons below
  [ Commit ] disabled — a run must complete before it can be committed
  [ Open in AssetOps ] not rendered — no evidence has been released
 ──────────────────────────────────────────────────────────────────────────
  Summary │ Frozen Identity │ Blocking Reasons │ Provenance
 ──────────────────────────────────────────────────────────────────────────
  FROZEN DETERMINISTIC IDENTITY
   site MG-001 @ foundation v4      scenario fuel-loss-event v1
   model minimal-fuel-tank v1       publication simulator-lab v1
   contract version 3               simulator version —  (not yet executed)
   interval [2026-01-01T00:00Z, 2026-01-08T00:00Z)   step 1 s   seed 784331
   initialization  fuel-tank-volume 430 L (scenario)
                   fuel-tank-capacity 500 L (foundation)
   interventions   none
 ──────────────────────────────────────────────────────────────────────────
  No runtime state. This Draft has not executed.
```

### 5. The Running Lab — T022 `[ACCEPTED, planned]`

Truth and reported side by side, which is the whole demonstration.

```
 Simulator Lab › Runs › MG-001-04                        [Open in AssetOps]
 ══════════════════════════════════════════════════════════════════════════
  ● Run MG-001-04  ⟨Running⟩   Sim Clock  Day 2 · 02:30:00   ▓▓░░░░░░ 16%
  Step 1 s ▾   Speed 100× ▾   [ ⏸ Pause ] [ ⏭ Step ] [ ⏩ FF ] [ ⟳ Restart ]
 ──────────────────────────────────────────────────────────────────────────
  Site View │ Configuration │ Environment & Scenario │ Events │
  Devices & Sensors │ Gateway & Ingestion │ Logs
 ──────────────────────────────────────────────────────────────────────────
  PRIVATE WORLD STATE (simulator truth)   │ DEVICES & SENSORS
  ─── not evidence · Lab only ─────────   │ ────────────────────────────────
   Fuel level (true)        254.0 L       │ Device        Truth  Reported
   Generator                stopped       │ fuel-level-   254.0   254.0 L
   Cumulative consumption    56.0 L       │   sensor              @ 1590
   Tank capacity            500.0 L       │ generator-      0.0     0.0 kW
   ─ forced, not modelled ─────────────   │   controller
   Load demand          unavailable       │
   Irradiance           unavailable       │ ⌛ 6 samples suppressed
   Reporting path       unavailable       │    reporting gap 1490–1580
  ────────────────────────────────────────┴────────────────────────────────
  EVENT TIMELINE (simulation time)
   1590   ◇ fuel level reported          254.0 L   device
   1580   ⌛ reporting gap ended
   1545   ● unaccounted fuel removal     −120.0 L  scheduled cause
   1500   ● removal window opened
   1490   ⌛ reporting gap started                  reporting path forced
   1320   ● generator dispatch ended     −56.0 L   scheduled cause
   1080   ● generator dispatch started
      0   ● run initialized              430.0 L
 ──────────────────────────────────────────────────────────────────────────
  GATEWAY OUTPUT (staged — not accepted evidence, no receipt time)
   source_time  device              signal      value   quality  state
   …+1590 min   fuel-level-sensor   fuel-level  254.0   GOOD     STAGED
   …+1485 min   fuel-level-sensor   fuel-level  374.0   GOOD     STAGED
```

Against `SimulatorLab1.png`: the mockup's `Fuel Level (true) 274 L` /
`Fuel Level (sensor) 289 L` pairing and its `Truth Value` / `Sensor Value`
columns are reproduced exactly. What differs is honesty about the narrow first
kernel — load, irradiance, battery SOC, cold-room temperature and the SLD's
electrical values read `unavailable` rather than showing a number, because this
model profile does not compute them.

### 6. Injection Control — post-T022 `[ACCEPTED as deferred]`

```
  QUICK ACTIONS (Inject Event)            applies at or after Day 2 · 02:30
  ─────────────────────────────────────────────────────────────────────────
  [ ⛽ Fuel Delivery ]  [ ⚠ Remove Fuel ]  [ 📈 Change Load ]
  [ 🔧 Generator Fault ]  [ 📡 Sensor Failure ]  [ 🛰 Gateway Outage ]
  ─────────────────────────────────────────────────────────────────────────
  ┌─ Remove Fuel ─────────────────────────────────────────────────────────┐
  │  Volume      [  40 ] L                                                │
  │  At          ◉ now (Day 2 · 02:30:00)    ○ at simulation time [____]  │
  │  Role        CAUSAL_INPUT · fuel-tank-volume · DECREASE               │
  │                                                                       │
  │  ⓘ This appends to this run's intervention history and becomes part   │
  │    of its deterministic identity. It cannot be injected into the      │
  │    past. It changes the simulated world, not any product conclusion.  │
  │                                            [ Cancel ]  [ Inject ]     │
  └───────────────────────────────────────────────────────────────────────┘

  EVENT TIMELINE
   1620   ◆ Fuel removed from tank        −40.0 L   injected
   1590   ◇ fuel level reported           254.0 L   device
   1545   ● unaccounted fuel removal     −120.0 L   scheduled cause
```

`●` scheduled cause · `◆` injected cause · `◇` observation · `⌛` reporting-path
condition. The distinction is visible in the timeline, in the runtime event log,
and in the run's provenance.

---

## Per-Task Contribution

### The tasks in flight and planned

| Task | Status | Contributes | Leaves open | Depended on by |
| --- | --- | --- | --- | --- |
| **T017** Scenario catalog & detail | `[SHIPPED]` | Strict scenario source, composed shipped + writable stores, versioning fields, event taxonomy, public/private boundary as a parsed separation | On-screen provisional markings not yet removed | T018 |
| **T018** Executable scenario contract | `[SHIPPED]` | The four execution roles, initialization ownership, canonical units, point/window/interval shapes, half-open dispatch, bound policy, `EXECUTION_CONTRACT_VERSION`. Also `reconcile_reported_observations` and the scenario-detail reconciliation panel — the two things (e) and (f) retract | The Fuel Loss residual stated, not resolved | T019, T021, T022 |
| **T019** Draft run setup | `[REVIEWED, UNMERGED]` | Freeze-or-refuse, decide-never-default, persist. `READY`/`BLOCKED` Drafts with inspectable reasons. Frozen deterministic identity. Model and publication profile resolution | Which of the three ways out to take on the residual | T020, T021 |
| **T020** Runs inventory & Draft shell | `[PLANNED]` | Runs list, run-detail shell over persisted Drafts, disabled actions with named prerequisites, frozen-identity presentation | No runtime state | T021, T022 |
| **T020A** Foundation properties & carriers | `[PROPOSED — new]` | Named physical properties on components; `FoundationBinding` addressing them; a `SupportedState` carrier for model-rule values (L9). `generator-fuel-rate` moves from the scenario to the generator | Efficiency curves, geometry, battery and PV detail — none of which T021 needs | T021 |
| **T021** Minimal Fuel Loss kernel | `[PLANNED]` | `initialize` + `step`. Fuel volume, generator state, cumulative consumption. Exactly-once dispatch. Bound behaviour. Determinism. Metamorphic proofs | Apportionment and observe-order rules `[OPEN]` | T022 |
| **T022** Lab execution & device observation | `[PLANNED]` | Clock and controls, runtime bindings, **the observation transform** — the seam (f) depends on. Generated golden traces through the normal path | Gateway staging | T023 |
| **T023** Staged source envelopes | `[PLANNED]` | Strict Source Envelope + typed records, `STAGED` publication, the operator record's typed non-device path | Release, Commit, ingestion | T024–T026 |
| **T024–T026** Commit & ingestion | `[PLANNED]` | Release manifest, overlap blocking, ingestion accept/reject, `received_at`, Ingestion Logs | — | T027–T029 |
| **T027–T029** Evidence views & Replay | `[PLANNED]` | Site evidence from accepted evidence only, provenance drawer, unavailable states, Replay | — | T034–T038 |
| **T034–T038** First conclusion chain | `[PLANNED]` | Source health → Generator Runtime Assessment → **Fuel Reconciliation** → the 120 L Finding with claim boundary and evidence basis | Materiality criteria; the Foundation consumption coefficient `[OPEN]` | — |

### Where each proposal lands

| | Proposal | Task | Size | Notes |
| --- | --- | --- | --- | --- |
| **(e)** | Run setup does not adjudicate coupling | **T019, before merge** | Small | Delete `_observation_reasons` and its call in `backend/assetops_backend/runs/service.py`, the `OBSERVATION_NOT_ACCOUNTED_FOR` vocabulary member in `runs/models.py`, and three test assertions. Do **not** touch `execution.py` or the scenario-detail surface in this change. Reviewer re-reads the narrowed diff. |
| **(f)** | Observations are generated | **T022** | Already in scope | T022's criteria already say the transform "emits ordered run-local observations distinct from private truth" and that authored reported-observation inputs "affect only their defined observation/event presentation." (f) is the document edit that makes the shipped scenario consistent with criteria you have already accepted. |
| **(g)** | `execution_requirement` forbidden on a reading | **T022, or a small slice before it** | Small | Parser rule + two entries in `config/scenarios/fuel-loss-event.yaml` + `EXECUTION_CONTRACT_VERSION` 2 → 3. Free now; not free once a golden trace exists. |
| **(h)** | Projection-vs-composition rule | Architect artifact | — | A line in `.ai/ARCHITECTURE.md` under Causal Runtime Authority. No code task. |
| **(i)** | `TRAJECTORY` oracle kind | **T021** | Small | One vocabulary member in `EXPECTATION_KINDS`, three parsed fields, and the kernel test that checks them. Must land with T021 because T021 is what can check it. Without it, (f) deletes the author's expectation instead of relocating it. |
| **(j)** | Reconciliation as a test-only conformance oracle | **T019, with (e)** | Small | The arithmetic moves out of the product path rather than out of the repository. Note that `declared_bounds` and `IMPLICIT_LOWER_BOUND_DIMENSIONS` have exactly one non-test caller today — `reconcile_reported_observations` — so they move with it. |
| **(k)** | Foundation physical properties + owner carriers | **T020A (new)** | Boundary-changing | The only proposal that inserts a slice. Touches the Foundation schema, the template, the site store, `FoundationBinding`, `SupportedState` and run setup, and requires re-creating MG-001 from the updated template. |
| **(l)** | `READY` discloses; T021 verifies | **T020 + T021** | Small in both | T020 adds the disclosure to the record and the screen. T021 adds a conformance test deriving `supported_states` from the kernel. No rename — the word becomes correct when the test lands. |

### The residual decision, re-split

Handoff decision (b) said the residual is one scheduled decision with two
halves, both due before T021's task file is written. Under these proposals it
splits differently:

- **The `REQUIRED` forcing states** — `site-load-demand`,
  `plane-of-array-irradiance`, `fuel-level-reporting-availability`, and
  `generator-output-power` if it is promoted — stay a hard blocker for T022 and
  must still be resolved **before T021's task file is written**, because they
  decide what the first kernel must model. **Deadline unchanged.**
- **The two readings** stop being a run-setup blocker under (e) and become a
  scenario-authoring question, due **before T022** rather than before T021.

---

## Sequencing Constraints

Four constraints, three of which already exist and one of which this document
proposes.

**1. A kernel precedes authoritative traces.** `[ACCEPTED]`
`D-2026-09-21-causal-runtime-before-golden-traces`. A manually authored trace
can be schema-valid and internally consistent while still being causally
circular. T021 before any golden trace; T022 generates traces through the normal
execution path.

**2. A kernel precedes any verdict about cause-to-observation coupling.**
`[PROPOSED (e)/(h)]` The same principle with one word changed. Deciding whether
declared causes reach a declared reading requires a transition rule, so it
requires the thing that owns transition rules.

**3. The `REQUIRED` forcing states resolve before T021's task file.**
`[ACCEPTED, amended]` They decide the first kernel's scope. Either the scenario
lowers their requirement level, or the model profile grows to model them, or the
authority for the reporting-path one moves to the publication profile
([Open Question 3](#3-model-profile-versus-publication-profile-authority)).

**4. The readings resolve before T022 — but they are decided *during* T021.**
`[PROPOSED, revised]` T022 builds the observation transform and cannot generate
a reading while the document also authors one. But the first draft of this
document treated "what the Fuel Loss document should author" as a standalone
decision that could be taken any time before T022, and that is wrong. The
right removal magnitude depends on what the kernel computes and on what the
product can recover from it, so **the document cannot be finalized before the
kernel has run against it.** See
[Open Question 9](#9-the-document-cannot-be-finalized-before-the-kernel-runs).

**5. Foundation must be able to describe the generator before T021 initializes
from it.** `[PROPOSED (k)]` This is the one constraint that is **not** a
narrowing.

### "Narrowing, not reordering" — where it stops holding

I have twice concluded that narrowing beats reordering. **Both times that was
right, and this time it is not.** Stated plainly, because it was asked
plainly:

| | Issue | Remedy | Sequence |
| --- | --- | --- | --- |
| (e) | Run setup adjudicates coupling it cannot adjudicate | **remove a claim** | narrowing ✅ |
| (f) | The scenario authors a reading it should not author | **remove a value** | narrowing ✅ |
| **(k)** | **Foundation cannot describe a generator's fuel consumption** | **add a field that does not exist** | **insertion ❌** |

You cannot narrow your way into a field that is not there. The first two
issues were about withdrawing overreach; this one is about a missing
capability, and the remedy has to build something.

The mitigating fact: it is an **insertion, not a reordering**. Nothing moves
relative to anything else, T019 and T020 are untouched, and the merge in front
of this is not blocked.

### The new slice

**T020A — Foundation physical properties and model-rule carriers.** After
T020, before T021. Contents:

- `SiteComponent` / `TemplateComponent` gain named physical properties beyond
  the single `rating` scalar, with a per-component-type vocabulary the strict
  parser enforces.
- `FoundationBinding` gains the ability to address a named property, not only
  `rating` by unit.
- `SupportedState` gains a carrier for model-rule values, closing the T019
  review's L9 finding.
- The shipped template declares the generator's specific fuel consumption;
  **MG-001 is re-created from it**, because templates instantiate by copy and a
  template change never reaches an existing instance.
- `generator-fuel-rate` leaves the scenario. Run setup freezes the coefficient
  from Foundation. A selected profile whose binding cannot locate it blocks on
  `INITIAL_VALUE_NOT_RESOLVED`; a Foundation that declares no such property at
  all refuses, because that is the declared owner having no answer.

UI-verifiable, which it must be: Site Configuration's Key Parameters panel
shows the generator's fuel consumption, and run setup's frozen-inputs panel
shows it resolving from **site foundation** rather than from **scenario** —
which is the seam repair made visible in one line of a table the user already
reads.

**Resulting sequence — one insertion, one loop, no reordering:**

```
  T019 ────► T020 ────► T020A ────► T021 ──────────────► T022 ────► T023 ─► …
  narrowed   unchanged  NEW         kernel + (i)          (f) lands
  by (e)+(j) + (l)      (k)         TRAJECTORY oracles    (g) lands
      │        disclose  Foundation      │     ▲              ▲
      │        what      properties      │     │ document     │
      │        READY     + carriers      └─────┘ corrected    │
      │        does not                    loop  from what    │
      │        assert                            the kernel   │
      │                                          computed     │
      │                                                       │
      └── decision on the REQUIRED forcing states ────────────┘
          still due BEFORE T021's task file is written
          (it decides the kernel's scope)
```

T021 still does not need to move earlier, and nothing in a narrowed T019 or in
T020 makes a coupling claim. The two additions T021's task file needs are the
`TRAJECTORY` oracle check (i), the `supported_states` conformance test (l),
and **run the kernel against the shipped document and report the resulting
trajectory** as the input to the document correction. Those are acceptance
criteria, not resequencing.

---

## Open Questions

### 1. Four kernel semantics the contract does not yet declare

Each would let two conforming kernels disagree, which is precisely what
`EXECUTION_CONTRACT_VERSION` exists to prevent, so each must be declared rather
than left to whoever writes T021. This inventory is the main practical
deliverable of
[What the specification does not pin](#what-the-specification-does-not-pin--the-actual-defect):
what makes authoring safe before a kernel exists is not the absence of unpinned
points but a written list of them.

**1.1 Window apportionment.** A quantity over a window — 120 L over 45 minutes
— ramps linearly across the steps, or lands at the completion boundary?
T018 said apportioning a window "would be a transition rule" and belongs to the
kernel, so the decision is T021's, but the *rule* belongs in the contract.
*My read:* linear ramp. It is what an author means by a window, and it makes the
private-state panel show the drawdown rather than a jump.

**1.2 Observe before or after.** Within one step, does the observation transform
sample before or after that step's due events are applied? For the shipped run
this changes the 2400 sample from 254.0 L to 500.0 L.
*My read:* after. A sensor reads the world as it is at the sample instant, and
the step has happened by then.

**1.3 A forcing outside its declared window.** `overcast-day` forces
irradiance over `[720, 1080)`. What is irradiance at 1080? Undefined today.
Currently unreachable because the model profile does not support irradiance at
all and blocks the run — but unreachable is not decided, and it becomes
reachable the moment the profile grows.
*My read:* a forcing's declared window is the whole of its claim; outside it
the state is unavailable, not zero and not held. "Unavailable" is already the
product's honest vocabulary for this.

**1.4 What happens after a bounded change.** The bound policy says a breach
produces "a bounded change recorded with the quantity it refused." It does not
say whether the run continues, nor whether later causes apply to the bounded
value. For the shipped document this decides everything after offset 2400.
*My read:* the run continues and later causes apply to the bounded value —
otherwise a bound is a disguised run failure, which the policy already has a
separate case for.

### 2. What the Fuel Loss document should author

**This is yours, and it is the one that most changes the demo narrative.**

**2.1 The removal magnitude.** Keep 120 L. It matches the `MAGNITUDE` oracle and
it produces a clean 120.0 L Finding on Path A. *Recommended: keep.*

**2.2 The delivery overfills the tank.** At 2400 the tank holds 254 L and the
document delivers 300 L against a 500 L capacity — `254 + 300 = 554`. The kernel
would fill to 500 L and record 54 L refused. That is correct bound behaviour,
but it creates a 54 L discrepancy in the *opposite* direction at exactly the
moment the `NO_FALSE_POSITIVE` oracle says the refuelling must not be attributed
to the removal "in either direction." *My read:* reduce the delivery to 240 L,
which fits with 6 L to spare, and exercise the capacity bound in a dedicated
kernel test rather than in the demo narrative. Alternatively keep 300 L
deliberately, as a second, subtler evidence puzzle — but decide it, do not
inherit it.

Worth noting the arithmetic coincidence that pointed at this: if the removal
were 219 L rather than 120 L, truth at 1590 would be exactly **155 L** — the
authored sensor reading — and the delivery would fit at 455 L. The shipped
numbers look like a document that was hand-simulated to the readings and then
had its removal reduced. That is circumstantial, not proof, but it is one more
reason to re-derive the document from causes rather than patch it.

**2.3 Should sensor bias be modelled deliberately?** *My read: yes, but not in
this scenario.* `ScreenMockups.png` already lists a separate `Sensor Bias`
scenario typed `Data Quality — Meter over-reads by 5%`, and
`SimulatorLab1.png` shows a `+5% tank bias` event with the sensor reading above
truth. Keeping the Fuel Loss Event free of sensor bias keeps its one lesson
clean — a real loss, hidden by a reporting gap. Bias gets its own scenario and
its own lesson: evidence that disagrees with truth for a reporting reason.

**2.4 Should operator reading error be modelled?** *My read: yes, and here.* A
hand-dip is genuinely less precise than a sensor, and the document's stated
purpose is "the imperfect record of it." A small declared reading error — say
−4 L — on the reporting path would make the operator record 250.0 L against a
true 254.0 L, which teaches that two sources of the same quantity legitimately
disagree without either being wrong. This is a deliberate authoring choice, not
a placeholder, because it declares a *cause on the reporting path* rather than a
consequence.

### 3. Model-profile versus publication-profile authority

`runs/profiles.py` currently gives the model profile sole authority over every
forcing state, including `fuel-level-reporting-availability`. But that is a
state of the *reporting path*, not of the world. The model profile models
physics; the publication profile owns cadence and reporting identity.
Arguably the reporting-path forcings are the publication profile's to answer, or
T022's observation transform's.

Consequences either way:

- If it stays with the model profile, T021's kernel must model reporting
  availability, which is not physics, and the first kernel gets wider for no
  physical reason.
- If it moves to the publication profile, the shipped Draft drops from three
  `STATE_NOT_SUPPORTED` reasons to two — still `BLOCKED` — and the publication
  profile gains a `supported_reporting_states` concept it does not have.
- **A third consequence that was not on this list.** `FROZEN_INPUT_ANSWERERS`
  has four members, bound one-to-one to T018's `INITIALIZATION_OWNERS`, and
  there is no `PUBLICATION_PROFILE` among them. Run setup already stamps
  `answered_by="MODEL_PROFILE"` on the cadence row and on both publication
  identity rows, beside detail text that says the publication profile — so
  the mislabel exists today and T020 is about to put it on a permanent
  screen. Moving the authority makes it plainly wrong rather than merely
  confusing, and needs a fifth answerer. The subset assertion in
  `test_the_answerers_correspond_to_the_initialization_owners` permits a
  fifth member, so the cost is the wire value, the screen, and a vocabulary
  docstring that says "the four".

*My read:* move it. Reporting availability, sensor bias and gateway outage form
one family, and it is the observation transform's family. This was raised at the
T019 checkpoint and deliberately not decided; it is now more pressing because
(f) makes the observation transform a real component rather than a future one.

### 4. Where the product's expectation comes from

**The largest gap between here and a Finding.** Path B of the worked example
needs two things that do not exist:

**4.1 Published generator operation.** `dispatched-output: 45 kW` is
`NON_EXECUTABLE_CONDITION`, so nothing computes generator output and the
generator controller — which Foundation says can publish `ac-power` and
`output-voltage` — has nothing to publish. Three options:

| Option | What it takes | Assessment |
| --- | --- | --- |
| **A.** Promote `dispatched-output` to `FORCING_INPUT` on `generator-output-power`; the kernel carries it as a forced exogenous state during the window; the controller publishes `ac-power` | Role change on one parameter; one more supported state on the model profile; one more published signal | **Recommended.** It is exactly what `FORCING_INPUT` is for. The T018 comment in the YAML says authoring generator output "would be authoring a state trajectory" — but that conflates *computing* it with *forcing* it. Forcing an exogenous condition the model does not solve is the role's definition, the same as load and irradiance. |
| **B.** Kernel computes generator output from load minus PV minus battery | A power-flow model | Far beyond the first kernel. |
| **C.** Publish a generator running/stopped boolean instead of power | A Foundation signal that does not exist | Possible, but a new Foundation signal is a bigger change than a role change, and power is more useful downstream. |

Note that option A adds a fourth `STATE_NOT_SUPPORTED` reason to the shipped
Draft until the model profile grows, which is consistent with the existing three
and is part of the same decision due before T021's task file.

**4.2 A Foundation consumption coefficient.** MG-001's Foundation declares a
60 kW generator rating and no fuel-consumption assumption at all. Without one,
the product cannot form an expectation and the Finding cannot be computed from
evidence.

> ⚠️ **Corrected.** The first draft of this document placed this with the
> conclusion-chain slices T034–T038, as something only the *product* needs.
> **That was wrong and it is the most consequential error in this document.**
> The *kernel* needs the coefficient at T021 to move the tank at all. It is
> due before T021, not after T029, and it is now proposal **(k)** in
> [Where Physical Properties Live](#where-physical-properties-live).

What remains genuinely T034–T038's is narrower: whether the product's
expectation uses the same Foundation coefficient the kernel used, or a
separately declared *operating assumption* that may differ from it. The
worked example shows why that distinction earns its keep — a product reading
the same number the simulator used gets the right answer for the wrong reason.

The seam that holds whatever the answer: **the coefficient comes from
Foundation, never from `generator-fuel-rate`.**

### 5. When the reconciliation panel leaves the scenario screen

`reconcile_reported_observations` is published as `observation_reconciliation`
at `backend/assetops_backend/simulator_lab_api.py:435` and rendered at
`frontend/src/shell/ScenarioFrame.tsx:767`. That is T018, merged to `main`.

(e) removes only the *blocking* use in T019. It deliberately does not touch the
screen, because removing a visible panel is a product change that belongs to a
slice that says so — the same treatment T016's cold-room marker and T017's
provisional markings received.

Open: does the panel go when (f) lands in T022, or earlier, or does it survive
in a reduced form that states the disagreement in words the way
`ScreenMockups.png` screen 6 does? *My read:* it goes when (f) lands, because
(f) is when the authored readings disappear and the panel has nothing to
reconcile. Until then it is honest — it describes a real property of a document
that does contain two authored readings.

### 6. The refuse-versus-block boundary at initialization

T019 draws a line that T021 will have to draw again, and they are currently
drawn by different reasoning:

- **T019 refuses** when an input cannot be *resolved* — no `run_id` is
  allocated, nothing is persisted, there is nothing to inspect.
- **T019 blocks** when an input resolves but the profile cannot *execute* it —
  a Draft is persisted with inspectable reasons.
- **T021 refuses** on "missing or ambiguous inputs" at initialization.

But T019 has already frozen and validated everything T021 initializes from. So
what is left for T021 to refuse? Either the two layers genuinely overlap and
T021's refusals are defence in depth against a bad caller, or T019's freeze is
incomplete and something reaches the kernel unvalidated. *My read:* defence in
depth, with T021's refusals unreachable through the normal path and tested
directly. But it should be stated, because "unreachable" and "not yet reached"
look identical in a test suite.

### 7. Reset and intervention history

When an operator resets a run, does the intervention history clear? Reset
"restores the same frozen initial state without allocating a new `run_id`". If
history survives a reset, the interventions replay — which makes reset a replay
control. If it clears, reset is a true restart and the run's provenance changes
under a stable `run_id`, which is uncomfortable. *My read:* history survives and
replays, and a run that wants a clean start is a Rerun with a new `run_id`. Not
urgent — injection is deferred past T022 — but it should be settled before the
injection slice is planned.

### 8. `NOT_RECONCILABLE` as a second blocking kind — now moot

Raised at the T019 checkpoint and not decided: should `NOT_RECONCILABLE` be
machine-readably distinct from `NOT_ACCOUNTED_FOR` on the wire, so T020 can
render them differently? Under (e) both leave run setup together and the
question does not arise. Recording it as **closed by (e)** rather than leaving
it open.

### 9. The document cannot be finalized before the kernel runs — now closed

The first draft of this document listed "the readings resolve before T022" as
a standalone decision. On reflection that is wrong, and it is the one real
sequencing consequence of
[Authoring Without A Kernel](#authoring-without-a-kernel).

The right removal magnitude depends on what the kernel computes and on what the
product can recover from the published evidence. Both are unknown until T021
runs. Deciding the number first and then building the kernel would be fitting
the kernel to an authored expectation — the same inversion, one more time.

*My read:* the correction is a loop inside T021, not a decision before it.
T021 runs the kernel against the shipped document, reports the trajectory, and
the document is corrected from that. This needs one acceptance criterion added
to T021's task file and changes nothing else in the sequence. It does mean
Open Question 2 is answered **during** T021 rather than before it, which is a
change from this document's first draft.

**Closed.** Accepted and built into the sequence: it is T021's third addition
in `.ai/PLANNING_HANDOFF_T019_T022.md` and the loop drawn in the M1C
sequencing revision. What it produced — what the document should author —
is Open Question 2, which is still open and is answered during T021.

### 10. The `MAGNITUDE` tolerance is a picked number

`removed-volume-within-tolerance` requires a later analysis to attribute the
removal within **10 litres of 120 litres**. Where did 10 come from? An author
imagined the error sources and chose it. Nothing derives it and nothing
falsifies it.

That matters because a tolerance that is too wide is an oracle that cannot
fail, and an oracle that cannot fail is circularity wearing an assertion's
clothes. Concretely, ±10 L means the Finding passes for any Foundation
consumption assumption between 11.5 and 16.5 L/h. Nobody chose that range.

*My read:* two cheap fixes, and they compose. Derive the tolerance from
declared error sources — Foundation coefficient spread, sample granularity,
rounding — so it has a stated basis; and pair every oracle with a mutation test
proving it *can* fail. The second is worth doing for all four oracles, not just
this one.

### 11. Physics in the validation layer

`IMPLICIT_LOWER_BOUND_DIMENSIONS = {"VOLUME": 0.0}` at
`backend/assetops_backend/scenarios/execution.py:641` gives every volume state a
lower bound of zero *whether or not the document declares one*, justified from
the `insufficient-fuel` bound case's prose.

The fact asserted is true — volumes are non-negative. But it is a **model
rule**, not a projection of the document, and it is being injected by the
validation layer. This is the same category as reconciliation, one notch
smaller and previously unnoticed. It is the answer to "is anything *else* in
the authoring layer over the line": yes, this.

It is nearly free to fix. `declared_bounds` has exactly one non-test caller —
`reconcile_reported_observations` — so under (e) and (j) both move out of the
product path together, and the implicit floor lands where it belongs, in the
model profile.

*My read:* move it with (j) — **and give it a destination**, which
[Where Physical Properties Live](#the-rule-applied-to-everything-the-fuel-loss-path-touches)
now supplies. Two different facts are tangled in the current constant. *Volume
is non-negative* is a modelling axiom and belongs to the **model profile**.
*This tank cannot be drawn below its pickup* is a site fact and belongs to
**Foundation**, as the second item of (k)'s minimum set. Neither belongs in
the validation layer.

### 12. "Run" is a noun with no verb — fine as is, but the button is not

`SimulationRun`, `run_id`, the Runs inventory and "Create Draft Run" all name
a record for something that cannot run, and T020 is about to build screens
around it. Is this the shape of the two naming problems already on the table —
*position is evidence, not configuration*
(`D-2026-09-20-breaker-vocabulary`), and *fuel loss is a conclusion, not an
event*?

*My read: no, and it is worth saying why the test fails rather than just
clearing it.* Both precedents are about a name **asserting something untrue or
premature**. "Fuel Loss Event" names the conclusion the exercise exists to let
you discover, which pre-loads the answer. "Position as configuration" claims a
fact is settled when it is observed. In both, the word makes a claim.

"Run" makes no claim. It is the standard domain noun for a unit of execution,
and a scheduled, cancelled or failed run is ordinary English. The claim about
whether execution *happened* lives in `execution_status`, which says `READY`
or `BLOCKED` and — with (l) — will say what it does not assert. The noun is
carrying nothing it should not.

**But one adjacent thing does warrant the question.** T020's task file has *"a
`READY` Draft presents its native Run action disabled with an accessible
reason naming the missing causal-runtime prerequisite."* `.ai/ARCHITECTURE.md`
gives three treatments and says the test for an action control is whether the
feature map can name the causal step that makes it true — *"If it can, disable
it and name that prerequisite. If the answer is a decision to defer, do not
render it."*

The feature map **can** name the step (T021, T022), so disabled-with-reason is
defensible. The risk is cumulative rather than local: a Runs inventory, a run
detail, a frozen-identity panel and a disabled Run button together read as
*almost working*, when no execution capability exists at all. **`[CLOSED]`** —
not as a vocabulary change but as a review obligation. T020's task file makes
a cumulative presentation-honesty assessment a named item in the review
packet, and the M1C user-review note in `.ai/FEATURE_MAP.md` says the same. If
the reviewer or the user judges the whole misleading, the remedy returns to
planning rather than being chosen inside the slice.

### 13. What declares the need, once the coefficient leaves the scenario

**Due before T020A's task file, and it is the one open question in this range
that blocks a slice outright rather than scoping it.** (k) moves the
generator's specific fuel consumption to Foundation, and nothing in the
current design then tells run setup that a run needs it: initialization inputs
are enumerated from scenario parameters, and the coefficient is about to stop
being one. Three options, their costs, what each does to the refuse-versus-
block line and to T021, and a recommendation are in
[What declares the need](#what-declares-the-need-once-the-scenario-stops-declaring-it).

It also carries a correction the user has to make rather than ratify: six
documents say a T020A that does not re-create MG-001 produces **refused**
runs, and the code blocks. Which way that goes depends on this decision, so
those statements are marked under decision rather than corrected.

---

## What I Would Do Next, If You Accept This

1. Decide (e) and (j) together. They are the only ones that gate T019's merge,
   and T019 is otherwise mergeable today. (j) makes (e) cheaper: the arithmetic
   leaves the product path rather than the repository.
2. Let T019 merge narrowed. T020 proceeds, carrying (l)'s disclosure of what
   `READY` does not assert, and a look at the disabled Run action against the
   three-treatments rule (Open Question 12).
3. **Decide (k), and plan T020A.** This is the new item and the one with real
   cost: a boundary-changing slice between T020 and T021, including
   re-creating MG-001 from the updated template. It is an insertion, not a
   reordering, and nothing in front of it is blocked.
4. Decide Open Question 3 (profile authority) and Open Question 4.1 (generator
   output role) — together they fix the forcing-state list, which T021's task
   file needs *before* it is written. 4.1 now has a second reason to go the way
   recommended: energy-based fuel consumption uses the same promotion.
5. Add to T021's task file: (i) the `TRAJECTORY` oracle, (l)'s
   `supported_states` conformance test, and "run the kernel against the shipped
   document and report the trajectory."
6. Answer Open Question 2 (what the document authors) **during** T021, from
   what the kernel computes — not before it.
7. (f), (g) and the panel removal land in T022.
8. Open Questions 1 (the four unpinned semantics), 10 (the tolerance) and 11
   (physics in the validator, now with a destination) are cheap and ride along
   with the slices above.
9. Open Question 4.2 is **no longer a T034–T038 item** for the coefficient
   itself — that moved to (k). What remains there is narrower: whether the
   product's expectation uses the same Foundation coefficient the kernel used,
   or a separately declared operating assumption that may differ.

Durable artifacts were written on 2026-09-21 after the user accepted (e)
through (l); see the Status block at the top of this document for what landed
where. Task files remain the Planner's and none has been changed.
