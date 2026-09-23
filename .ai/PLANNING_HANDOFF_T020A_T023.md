# Planner Handoff — T020A Through T023

**Supersedes `.ai/PLANNING_HANDOFF_T019_T022.md`**, which is deleted. T019 and
T020 are merged and their sections are spent; what they settled is in
`.ai/CODE_STATE.md` and in the decision record, not here.

Scope: Blocks A, B and C of `.ai/FEATURE_MAP.md` — T020A, T020B, T021, T021A,
T022, T023. Written by the Architect. **The Planner writes the task files.**
Nothing here is a task file and nothing should be copied verbatim; task specs
are implementation guardrails and this is the reasoning they are cut from.

Disposable. Delete it when T023 closes out.

## The one thing this file is for

For each slice, what an Implementer must be told, and **where it should live**.

- **Inline** means the sentence goes in the task file, because it changes what
  gets built. An Implementer who does not read it builds the wrong thing.
- **Pointer** means a citation to a `Docs/simulator_design_v4.md` section,
  because it is reference the Implementer reads when they reach that part of
  the work.

The distinction is the useful part. A task file that inlines all of v4 is
unreadable and will be skimmed. One that only cites v4 lets an Implementer skip
the thing that mattered. When in doubt, ask whether a wrong answer would be
caught by a test the slice already has: if yes, pointer; if no, inline.

## Where the authority is

| Need | Read |
| --- | --- |
| Normative simulator mechanics | `Docs/simulator_design_v4.md` |
| Demo sequence, slice outcomes, alignment calls | `Docs/mini-grid-demo-architecture-and-roadmap.md` §§2, 3, 5 |
| What becomes demonstrable and in what order | `.ai/FEATURE_MAP.md`, Delivery Blocks |
| Dependencies and the contract version | `.ai/FEATURE_MAP.md`, Near-Term Sequencing |
| The durable rules | `.ai/ARCHITECTURE.md` |
| What was decided and why it binds | `.ai/DECISIONS.md` |
| The full scenario/runtime argument | `Docs/simulator-scenario-authoring-and-runtime.md` |

The decisions that bind this whole range:
`D-2026-09-21-physical-property-ownership`,
`-run-setup-outcome-vocabulary`, `-projection-versus-composition`,
`-specification-reference-implementation`,
`-scenario-execution-contract-amendment-1`;
`D-2026-09-22-expiry-follows-the-condition`, `-contract-version-scope`,
`-foundation-value-declaration`, `-capacity-bound-source`,
`-foundation-property-absent-blocks`, `-consumption-coefficient-unit`,
`-forcing-state-requirements`, `-kernel-step-semantics`,
`-reconciliation-panel-retirement`, `-milestone-speed-over-purity`.

Every gate these slices were waiting on was met on 2026-09-22. Nothing in this
range is waiting on the user.

## Standing instructions for every task file in this range

**Speed over pedantic purity.** `D-2026-09-22-milestone-speed-over-purity` and
the roadmap's planner notes agree. Escalate a choice that changes the client
story, crosses a protected boundary, is expensive to reverse, or blocks the
next block. **Do not escalate naming, internal representation, file placement
or API aesthetics.** If a block's *shown at the end* does not move, the
argument is not worth a round. Record the rest in
`.ai/MILESTONE_REVIEW_BACKLOG.md`.

**Write the move, never the literal**, for `EXECUTION_CONTRACT_VERSION`. Four
narrowings are in flight across three slices. Any task file stating an absolute
number will be wrong by the time it is read. The ledger is in
`.ai/FEATURE_MAP.md`.

**Checks with every implementing slice:** `tools/check-architecture.ps1`,
`tools/check-agent-workflow.ps1`, and the backend and frontend tests relevant
to the slice. Extend guards where a slice introduces a seam; never weaken one
to wire something up.

**Four standing prohibitions**, worth one line in each task file rather than a
paragraph: do not put a product conclusion in a scenario fixture; do not turn a
private oracle value into evidence; do not hide missing evidence by
manufacturing a default; do not let the simulator import the backend.

---

## T020A — Foundation physical properties and model-rule carriers

`tasks/T020A-foundation-physical-properties.md`. `USER_REVIEW_REQUIRED: true`,
on the property vocabulary and its units.

### The sizing call the Planner has to make first

**v4 §24 and §27.2 require a sizing pass before implementation starts.** v4
places three separable concerns near T020A and says the design must not force
them into one unreviewable slice:

```
A. typed per-component property carrier
        ↓
B. component-addressed binding / frozen StateRef resolution
        ↓
C. site-scoped typed control properties
```

**C is excluded by v4 itself** (§5.2, §24): Site Controls wait for the first
controller slice, when source merit order or critical-load priority is actually
consumed. That is Block I.

**The Architect recommendation is that T020A ships A and not B.** MG-001 has
one generator and one tank. A component-scoped binding that resolves against a
single candidate is already correct, and `StateRef` exists to distinguish two
loads or two chargers — which is Block I's Kobo with `LOAD-RES`,
`LOAD-CLINIC` and `LOAD-MILL`, not a Site that exists today. Building the
addressing layer now is generalising before the second concrete use, which v4's
own planner notes forbid, and it doubles a slice that already carries a
schema change, a unit decision, a contract-version move and a template
re-instantiation.

**What is not deferred, because it is free now and expensive later** — this is
the inline part:

> A component-scoped binding addresses a component by an explicit identifier
> or by resolving against exactly one candidate. Zero candidates or more than
> one **block**; neither selects the first match. The component identity is
> never encoded into the state-key string: the semantic state name and the
> runtime address are different concepts, and merging them costs the reusable
> state vocabulary and makes ambiguity undetectable.

Get that rule into the carrier and the addressing layer becomes an extension
rather than a migration. If the Planner decides the addressing layer is cheap
enough to ride along after all, it is a legitimate call — but then it is its
own reviewable cut inside the slice, not a widening of the carrier work.

### Inline in the task file

- **The Foundation-owned-parameter rule and its blast radius.** A scenario
  parameter whose declared owner is Site Foundation has **no value position at
  all**: it declares the need and states no number. The rule keys on the
  declared owner because that is the only thing the scenario parser can see, so
  it reaches `tank-capacity` as well as the coefficient. Exempting
  `tank-capacity` would need a field invented for the exemption.
- **`INITIAL_VALUE_ANSWERS_DISAGREE` is retired here**, because
  `rating.value != declared` was its only producer and no document can state a
  `declared` any more. A refusal kind nothing can produce is a false claim one
  layer down.
- **Every failure of a Foundation-owned value blocks**, on
  `INITIAL_VALUE_NOT_RESOLVED`: no binding declared, no match, more than one
  match, wrong unit, and a Foundation that declares no such property at all.
  None refuses. `D-2026-09-22-foundation-property-absent-blocks`.
- **The coefficient is `L/kWh` and `dispatched-output` is promoted here.**
  Under `L/kWh` the coefficient is not a rate over time, so this slice rewires
  the dispatch event's effect from a rate parameter to the model rule
  *consumption is specific consumption times energy delivered*. Leaving the
  promotion later would publish a document whose model rule depends on a state
  nothing declares.
- **The `fuel-tank-volume` upper bound stops being something the document can
  state, and the `bounds` declaration stays anyway.** A bound's state key and
  kind say which world state caps which — a relationship between two states,
  not a property of a machine. The parser must keep accepting a `bounds` block
  on a parameter that states no value. `D-2026-09-22-capacity-bound-source`.
- **MG-001 is re-created from the updated template.** Templates instantiate by
  copy, so adding the property to the template does not give it to
  `var/sites/mg-001.yaml`. A slice that skips this produces a Site whose runs
  block on the unresolved coefficient, so the slice's own UI-verifiable outcome
  never appears on screen. `var/sites/` also holds `mg-002` and `mg-003` as
  fixtures the user asked to keep — do not clear the directory.
- **`ControlAssumption` stays documentary.** It has identity, subject, basis
  and prose, and it does not become a setpoint or state model. Typed control
  properties are a separate carrier alongside it. v4 §5.2.

### Pointer only

- `Docs/simulator_design_v4.md` §4.2, for why the semantic state name and the
  runtime address are separate and what the addressing extension will need when
  it lands.
- v4 §10.1, for the Foundation / scenario / publication ownership split, which
  this slice does not change.

### May not

Grow Foundation into a wish list. Efficiency curves, minimum load, ramp rate,
tank geometry, sensor placement, battery chemistry, PV tilt, orientation and
derate are all absent and none of them blocks T021. The tank's minimum usable
level is the honest home for the floor the validation layer currently invents,
and it is a follower. Add a Foundation edit path. Move the validation-layer
volume floor unless the slice says it is doing that and carries the test.

### The open question this slice must not settle by accident

Whether the product's own expectation later uses the same Foundation
coefficient the kernel used or a separately declared operating assumption.
That belongs to Block F. T020A supplies the coefficient; it does not decide who
else reads it.

---

## T020B — Execution contract alignment and the first `READY` shipped run

`tasks/T020B-execution-contract-alignment.md`. `USER_REVIEW_REQUIRED: false`.

### Inline in the task file

- **The nine-step boundary cycle, spelled out.** The shorthand *observe after
  the step* is ambiguous and has already been read both ways: it can be taken
  to permit a pre-event sample, or a forward-looking interval value. Neither is
  correct. What T020B declares is v4 §6.1's cycle at instant `T`: apply events
  and configuration changes due at `T`; the post-event state at `T` now exists;
  if a sample is due, sample stocks and discrete state at `T` and attach
  interval measurements for `[T-dt, T)`; apply the reporting transform and hand
  the result to staging; build the controller view; emit control intent;
  resolve accepted flows; integrate `[T, T+dt)`; check conservation, bounds and
  invariants; carry state to `T+dt`.
- **A stock reading and an interval reading at the same timestamp mean
  different things.** A stock or discrete reading at `T` is post-event. A rate
  or energy reading at `T` summarises the interval that just ended. This looks
  asymmetric only if the two are assumed to mean the same thing; real
  instrumentation has exactly this distinction, and the contract text has to
  say it because a later reader will otherwise reconcile it wrongly.
- **At the first boundary there is no preceding interval**, so interval signals
  are unavailable unless a profile explicitly declares an initial historical
  window. This is a contract statement, not a kernel behaviour, and it belongs
  here rather than in T021.
- **No second clock, and no reinterpretation of already-frozen runs.** A run
  frozen under an earlier contract version keeps what it was frozen under.
- The other three semantics, unchanged: a quantity declared over a window ramps
  linearly across it; a forcing outside its declared window is **unavailable**,
  not implicitly zero and not held; a bounded change records the accepted and
  refused quantities and the run continues from the bounded value.
  `D-2026-09-22-kernel-step-semantics`.
- **A requirement conflict is refused, not resolved.** Retire the
  `REQUIRED`-wins collapse; a `(state_key, role)` pair must agree on its
  requirement, and a document where it does not is refused at the parser, which
  is the layer that sees every position. Lowering a state does nothing while
  the collapse exists, which is why the two must land together.
- **`site-load-demand` and `plane-of-array-irradiance` drop to `OPTIONAL`** at
  all five positions, three and two respectively.
- **Reporting-path authority moves to the publication profile**, which gains a
  supported-reporting-states concept. T020 already introduced
  `PUBLICATION_PROFILE` into the answerer vocabulary and relabelled the three
  mislabelled frozen rows; what is new here is the authority, not the
  vocabulary.
- **This slice retires a T020 acceptance criterion, and that is not optional.**
  T020 proves every `READY` claim against a fixture record because no `READY`
  run existed through the product path. This slice makes the shipped Fuel Loss
  Event reach `READY`, so the premise becomes false here and the replacement is
  a `READY` proof on the shipped scenario.

### Pointer only

- v4 §6.1–6.3, for the full cycle, the worked 13:00 example, and the separation
  between what a controller may see and what a gateway publishes.
- v4 §8.2, for the bound policies, which are already implemented.

### May not

Touch the kernel. Widen the shipped model profile beyond the
`generator-output-power` that T020A adds. Correct the document's authored
numbers, which is T021's loop. Relabel the three frozen rows or change the
answerer vocabulary a second time.

---

## T021 — Minimal Fuel Loss causal kernel

`tasks/T021-minimal-fuel-loss-causal-kernel.md`. `USER_REVIEW_REQUIRED: false`.

### The placement call the Planner has to make before the task file

v4 §3.2 is stronger than the current guard: **`simulator/` imports no
`assetops_backend` package at all**, `host/` is a composition leaf that may
import both, and nothing imports `host/`. The run, scenario and
execution-contract types the kernel needs are backend-owned today, and `host/`
does not exist yet.

Two legal shapes:

- **(a) Kernel in `simulator/assetops_simulator/kernel/` now**, with the
  minimum execution contracts it needs moved to a dependency-neutral module
  both sides import. `host/` appears at T022, when execution is wired to the
  Lab.
- **(b) Kernel backend-side for T021**, moving to `simulator/` at T022.

**Recommendation: (a).** The neutral-contract move is at its cheapest while the
kernel has exactly one caller and no UI, and (b) puts a structural relocation
inside T022 — the slice that already carries a user-review checkpoint on
control behaviour and truth visibility. Either way, **the sizing is the
Planner's and the invariant is not**: no slice in this range weakens
`tools/checks/dependency-direction.ps1` to wire execution up.

### Inline in the task file

- **Exact-rational arithmetic.** World arithmetic uses `Fraction` while the
  model stays rational. An authored decimal is normalised **once**, at the
  input boundary. Calling a denominator limiter after an integration step is
  forbidden: doing it per step would repeatedly approximate the world and make
  the policy's own name false. This changes code and will not be caught by any
  test the slice would otherwise write.
- **Execution failure is a third vocabulary.** It is distinct from setup
  refusal and from setup blocking, and the naming rule in `.ai/ARCHITECTURE.md`
  applies unchanged: from the name alone, a reader must be able to say which of
  the three it is. v4 §23 supplies the member names to reuse rather than
  reinvent — `ORDER_DEPENDENT_GROUP`, `BALANCE_IDENTITY_VIOLATION`,
  `PHYSICAL_RESOLUTION_FAILURE`, `UNSUPPORTED_MODEL_STATE`,
  `INTEGRATION_BOUND_FAILURE`, `TOPOLOGY_INCONSISTENT`. A `FAIL_RUN` condition
  is never relabelled as completion.
- **The tank's capacity comes from the frozen identity, not from
  `declared_bounds`.** After T020A that function reports no upper value for
  `fuel-tank-volume`, and that is the correct answer: the document declares
  *which* state caps which, and the frozen run carries *how big* the tank is.
  An implementer who reaches for `declared_bounds`, finds `(0.0, None)` and
  fills the gap will either invent 500 or conclude the bound was dropped, and
  both are wrong. Say this in the task file rather than letting it be
  discovered.
- **The non-negativity floor comes from the model profile**, never from the
  injected `IMPLICIT_LOWER_BOUND_DIMENSIONS` constant. *Volume is
  non-negative* is a model rule; the validation layer only ever injected it,
  and that layer leaves the product path in T022.
- **The `TRAJECTORY` oracle kind**, with two guards that are part of the
  deliverable rather than commentary: it must be **sparse and purposeful**,
  because a dense set is a trace in the oracle position and fits the kernel to
  the author's arithmetic; and the slice states that it is a regression guard
  rather than a correctness proof, because two implementations of the same
  arithmetic agreeing proves only that they agree. It is checked by the kernel
  in tests, never published, and never read by an executable path.
- **The `supported_states` conformance test is derived from the kernel, not
  hand-maintained.** A test that restates the tuple closes nothing. When it
  lands, `READY` means what its name says — and **this slice retires T020's
  `READY` disclosure**, because this is the slice that makes it false.
- **The loop.** Run the kernel against the shipped Fuel Loss document and
  report the resulting trajectory. The document's authored numbers are then
  corrected from what the kernel computes, not from what an author expects.
  Expect disagreement and expect the document to be what is wrong. The
  correction itself is the user's call at the checkpoint; the slice's
  obligation is to produce the trajectory that makes the call answerable.
- **The refusals here are defence in depth, and they are unreachable through
  the normal path.** T019 already froze and validated everything this slice
  initialises from. They must be tested directly, because *unreachable* and
  *not yet reached* look identical in a test suite and only one of them is a
  guarantee.
- **Causal proof is not schema proof.** Schema validity, internal invariants
  and causal correctness are three separate claims. Causality is demonstrated
  by executable transitions plus independent example, boundary and metamorphic
  tests: vary the removal magnitude and time, or remove the cause, and observe
  the corresponding consequence while the unaffected prefix and unrelated state
  stay fixed.

### Pointer only

- v4 §9, the deterministic draw identity — BLAKE2b-256, canonical encoding,
  domain separation, and a draw as a pure function of contract version, seed,
  stream name, step index and ordinal. **The first kernel draws nothing**, so
  this is reference now. **It becomes inline at the first slice that introduces
  randomness**, and the property that matters there is that adding a stream
  cannot perturb an existing one.
- v4 §21, the trace record kinds, when the kernel starts emitting a trace.
- v4 §8.1–8.2, integration and the three bound outcomes, both already
  implemented.
- v4 §7, controller intent and the physical resolver. The first kernel has no
  controller. **Preserve the seam without building it**: nothing in T021 should
  make a requested value and an accepted value the same object later.

### May not

Accept a hand-authored trace as execution input. Persist or check in a golden
artifact — T022 owns that. Read physics from the scenario. Decide a contract
semantic inside the implementation. Display a trajectory in the Lab. Model
power flow, battery, weather synthesis or dispatch logic; carrying a forcing is
not a claim that its consequences are modelled. **Remove the reference
implementation** — this slice compares the kernel against it and reports
disagreement, with the kernel as the surviving authority; removal follows its
last product-path caller, in T022.

---

## T021A — Reported observations carry no execution requirement

`tasks/T021A-reported-observation-requirement-closure.md`.
`USER_REVIEW_REQUIRED: false`. Small, and it stays small.

### Inline in the task file

- The parser gives `execution_requirement` **no position** on a
  `REPORTED_OBSERVATION`, closed at the structure rather than as a rule applied
  after parsing.
- The shipped document's reported-observation entries lose the field.
- `EXECUTION_CONTRACT_VERSION` moves by one. The new version reaches runs set
  up after it; a Draft already frozen keeps what it was frozen under. **Write
  the move, not the literals.**

### Pointer only

v4 §2.1 and §24, which confirm this slice is not a kernel prerequisite and
stays after T021 in the queue. The kernel never reads the field either way.

### May not

Remove the authored reading *values* — that is T022's. Touch the reconciliation
panel or its payload. Change anything else in the execution contract, the
kernel, or the observation transform.

---

## T022 — Lab execution and device observation

`tasks/T022-lab-execution-and-device-observation.md`.
`USER_REVIEW_REQUIRED: true`.

### Inline in the task file

- **The observation transform is a component, not a step inside execution.**
  Bindings are keyed by `(StateRef, device_id, signal_id)`. It samples at the
  frozen publication profile's cadence, not at the kernel's timestep, and its
  output objects are distinct from truth rather than copies of it. **Truth
  exists at every step; a reading exists only at a declared sample instant.**
- **Do not interpolate through the reporting gap.** During the gap there is no
  fresh sample. Carrying an old reading forward is legitimate only if a
  declared stale-reporting transform does it and labels it as stale. A
  convincing-looking trace through the gap is exactly the failure this slice
  exists to make visible.
- **Reporting faults divide, and T022 gets one half.** Sampling, bias, dropout
  and quantisation belong to the observation transform. Buffering, outage,
  retry, delayed release, duplicate publication and publication timing belong
  to the gateway and are T023's. A cadence-driven sampling gap is sufficient
  here; do not build the gateway's half early.
- **The hand dip is a generated operational observation, not a copied number.**
  It has its own non-device source, its tank, its occurrence time, a value
  generated from truth at that offset, and a declared error behaviour if one is
  modelled. A physical fuel addition and its human delivery report are
  different events: the addition can happen while the record is delayed, wrong
  or absent.
- **(f), in the document and in the code.** The authored 155 L at 1590 and
  150 L at 1800 are removed. The entry at 1590 survives as an evidence
  condition asserting that a reading arrives there and is materially below what
  dispatch accounts for, backed by a `DETECTION` expectation. The operator's
  inspection at 1800 keeps the act and loses the number.
- **The reconciliation panel leaves the scenario detail screen here**, with its
  payload, `reconcile_reported_observations`, `declared_bounds` and
  `IMPLICIT_LOWER_BOUND_DIMENSIONS`. This is a visible change to merged work,
  so the slice says it is making it.
  `D-2026-09-22-reconciliation-panel-retirement` already settles it — carry the
  decision into the task and do not ask for it again.
- **The Lab may show both values and neither becomes a product record.** The
  execution adapter returns a private Lab projection that may carry generated
  device observations; the Lab is gated simulator UI and may render private
  tank level beside reported level. The product receives neither directly.
- **At the first boundary no preceding interval exists**, so an interval signal
  is unavailable there.

### Pointer only

- v4 §11.1, the full declarable fault list. T022 builds cadence and gap.
- v4 §3.3, the execution adapter's shape — start, step, run to end, staged
  envelopes, commit — as the port the Lab drives. Useful when wiring, not a
  constraint the slice has to reason about.
- v4 §21, trace record kinds and the distinction between simulator trace
  playback as a debug mechanism and AssetOps Replay as a historical view.

### May not

Let an authored reading reach a transition or an initialisation. Infer a
cadence from anything but the frozen publication profile. Stage a Source
Envelope — that is T023. Introduce an injection control. **Introduce sensor
bias into the Fuel Loss Event**: a separate Sensor Bias recipe already exists
in the mockups, and keeping Fuel Loss free of bias keeps its one lesson clean —
a real loss, hidden by a reporting gap.

### Review

Already `true`, for control behaviour, private-truth visibility,
truth-versus-reported labels and unavailable-value treatment. One addition that
is not a control: the scenario detail screen now says, in words, that the
document declares causes and does not declare what the tank holds or what a
device reads. That sentence is the product-facing statement of the whole
sequence and is worth reviewing as copy, not only as layout.

---

## T023 — Staged source envelopes

`tasks/T023-staged-source-envelopes.md`. `USER_REVIEW_REQUIRED: true`.

### Inline in the task file

- **The allowlist is exactly two records and it stays that small.** Fuel-level
  `Telemetry` and `OperationalRecord` subtype `fuel.manual_dip`. **No generic
  `{type, payload}` escape hatch.** T023 does **not** publish generator energy,
  `fuel.delivery`, command events, maintenance records or policy-change
  evidence. Each of those arrives with the product slice that consumes it: a
  delivery needs a reportable delivery observation first, and a private
  generator flow needs a modelled meter first. This is the single most
  important scoping sentence in the slice, because every one of those records
  is one the later fuel story will want and none of them has a consumer yet.
- **Exactly one typed record per envelope.** The envelope carries Site, source,
  gateway and device identity as applicable, schema and message identity,
  sequence identity, source time, gateway publication time, mapping and
  configuration identity and version, quality and transport metadata, and
  allowed simulation provenance. The typed record carries the measurement or
  occurrence semantics.
- **Source time is preserved through buffering or delayed publication, and
  T023 assigns no receipt time.** `received_at` is created by ingestion and by
  nothing else. A staged message with a receipt time is a boundary violation,
  not a convenience.
- **Idempotence and conflict.** Re-staging an identical message is idempotent.
  The same message identity with different content is a conflict and **writes
  nothing**.
- **No private content crosses.** No authored removal, private expectation,
  truth trace or cause description enters a payload or provenance field. An
  opaque run or scenario version reference is provenance, not permission to
  dereference a private cause in analytics later.
- **T023 stages completed Drafts.** Do not imply paused-run staging exists
  because the canonical product describes paused Commit eligibility later.
- **The envelope schema must be dependency-neutral.** Both the simulator and
  the backend will construct or read it, and the simulator may not import the
  backend to do so. If the concrete type is backend-owned today, move or expose
  it through a neutral contract module rather than weakening the guard. v4
  §3.2, rule 5.
- **Staging changes nothing operator-visible.** The Site page is unchanged
  while a Draft stages, and raw inspection shows the same validated content as
  the summary.

### Pointer only

- v4 §11.2, the full gateway responsibility list, of which T023 implements the
  identity, timing and mapping parts.
- v4 §11.3, Draft versus Commit, which T023 only half-implements: Commit is
  Block D.
- v4 §12, operational records as a family with their own completeness and error
  modes. T023 ships one of them.

### Review

Already `true`. Review the envelope and typed-record **language** here rather
than after a Commit action exists to obscure it. This is the first
evidence-boundary contract and the vocabulary it fixes travels to every later
record.

---

## Evidence that lets a slice be called done

The roadmap's acceptance discipline, condensed. A review packet should carry
the actual screen interaction plus the smallest artifact or automated proof
that protects the new boundary.

| Slices | Proof that matters |
| --- | --- |
| T020A, T020B | Resolved-address ambiguity blocks rather than picking a candidate. Exact arithmetic at the authored-float boundary. Event, window and end-boundary tests. Existing contract-version movement and frozen-run compatibility preserved. |
| T021, T021A, T022 | Causal removal and retiming tests. Kernel-derived profile conformance. A boundary stock sample includes the event due at that boundary. A reporting gap changes observations and nothing else. No operator history changes during a Draft run. |
| T023 | Strict payload and privacy checks. Canonical artifact reloads to the same content. Idempotent re-stage; a conflicting identity writes nothing. No receipt time anywhere. **UI success alone cannot prove any of these.** |

## What this handoff deliberately does not decide

- Task file contents, acceptance-criteria wording, scope-limit lists, test
  structure and user-review placement. All the Planner's.
- Whether T020A's addressing layer rides along or waits. Recommended above,
  decided by the Planner at the sizing pass.
- Whether T021's kernel lands in `simulator/` or moves there at T022.
  Recommended above, decided by the Planner. The dependency guard is not
  negotiable either way.
- Every open question under `Open Questions` in `.ai/FEATURE_MAP.md`. A task
  file that closes one by implementation rather than by decision is the failure
  this whole sequence exists to stop.
