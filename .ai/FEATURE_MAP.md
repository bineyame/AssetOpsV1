# AssetOps Feature Map

Scope: the backend, simulator and frontend capabilities needed to reach a
client-credible mini-grid demo, sequenced by what becomes demonstrable.

This is a feature map, not a task list. Two things organise it. **Delivery
blocks** say what a person can be shown at the end of each stretch of work.
**Feature areas** say what must be true before a screen can make a claim. A
task range is a label on a block, never its purpose.

**Speed over pedantic purity governs this map.**
`D-2026-09-22-milestone-speed-over-purity` and the roadmap's own planner notes
say the same thing: escalate a choice that changes the client story, crosses a
protected boundary, is expensive to reverse, or blocks the next block. Do not
escalate naming, internal representation, file placement or API aesthetics.
This map is meant to make that easy to obey: if a block's *shown at the end*
does not move, the argument is not worth the round.

## How To Use This Map

Do not read this file end to end. Use `.ai/ACTIVE_CONTEXT.md` and the active
task file to pick sections.

| Need | Read |
| --- | --- |
| What becomes demonstrable, and in what order | Delivery Blocks |
| What already works | What Is Already True |
| Causal prerequisites for a screen or claim | Feature Areas |
| Boundaries a slice must not cross | Protected Seams |
| Rail, tab, column and viewport rules | Screen And Shell Architecture |
| T020A–T023 dependencies and the contract version | Near-Term Sequencing |
| Unresolved product questions | Open Questions |
| Normative simulator mechanics | `Docs/simulator_design_v4.md` |
| Demo sequence, slice outcomes, screen-by-screen landing | `Docs/mini-grid-demo-architecture-and-roadmap.md` |
| Client narrative, portfolio story, finish lines | `Docs/mini-grid-demo-architecture-and-roadmap (1).md` |
| Per-slice Planner guidance for the live range | `.ai/PLANNING_HANDOFF_T020A_T023.md` |
| Scenario authoring and runtime reasoning | `Docs/simulator-scenario-authoring-and-runtime.md` |

**The two roadmap files are different documents, not duplicates.** The
638-line one is the later, repository-grounded execution companion: it cites v4
sections, names task identities, and carries the alignment decisions. The
1771-line one is the earlier product-narrative companion: it carries the client
walkthrough, the portfolio story and the three finish lines. Where they differ
on sequencing, the shorter one is later and wins.

## What Is Already True

A ledger, not a plan. Per-slice detail is in `.ai/CODE_STATE.md`; the task
files are in `tasks/completed/`.

- **A user can configure a mini-grid Site and read it back.** Shipped template
  catalog through a port, create-from-template into a separate writable store,
  Sites index, Site Details, read-only Foundation, and the operator/Lab shell
  split behind `simulator_lab.enabled`. T001–T013.
- **The configured physical model is real.** Topology, devices, signal
  mappings, ratings, control assumptions, the hybrid mini-grid SLD archetype
  and its incompatible-topology state. T014–T016.
- **A scenario can be inspected and a run can be set up against it.** The
  ScenarioDefinition domain and its composed stores, the executable scenario
  contract with its four roles and its timing and bound semantics, Draft run
  setup with a frozen deterministic identity that has an answerer for every
  value, and the Runs inventory and Draft detail. T017–T020.
- **What is not built.** The simulator package is a scaffold. Run execution,
  the observation transform, gateway envelopes, ingestion, accepted evidence,
  Replay, Findings, financial and verification objects do not exist. A
  documented mechanism is not implemented software, and `READY` is not an
  executed result.

## Delivery Blocks

Each block names **what a person can be shown at the end of it**. Where the
honest answer is *nothing a client would care about*, the block says so; a
block that admits it is scaffolding is more useful than one that pretends.

Task identities are labels. They are preserved, not renumbered, and a block
may span a range or be one slice.

### Block A — Trust the frozen setup

**Slices:** T020A, then T020B.

**Shown at the end:** almost nothing a client would care about. This is
scaffolding and it is worth saying so. What a developer or the product owner
can see is two lines moving in tables they already read: the generator's
specific fuel consumption appears in Foundation's Key Parameters, and run
setup's frozen-inputs panel shows it resolving from *site foundation* rather
than from *scenario*. Then the shipped Fuel Loss Draft reaches `READY` through
the product path for the first time instead of `BLOCKED`, with demand and
irradiance disclosed as recorded unsupported optional inputs rather than as
blocking reasons.

**What it buys:** the physics of the machine stop living in the story, and the
run the next block has to execute becomes executable. Nothing between here and
a running simulator is cheaper to do later.

**Deliberately unavailable:** execution, runtime state, any trajectory on
screen, staging, ingestion.

**Review:** T020A carries a user-review checkpoint on the Foundation property
vocabulary and its units. T020B does not.

### Block B — Watch a cause become a reading

**Slices:** T021, then T021A, then T022.

**Shown at the end:** the first block whose end state is a demo. A person opens
the shipped Fuel Loss Draft in Simulator Lab, starts it, steps and pauses it,
and watches the tank level fall because the generator burned fuel and fall
further because fuel was removed — with the *true* tank level and the
*device-reported* level side by side, disagreeing across a declared reporting
gap. Remove the removal cause and the discontinuity disappears; move it and it
moves. The event timeline explains the situation being tested, not what
AssetOps knows.

**The claim it makes:** the world is computed, not scripted. This is the
proposition the whole simulator programme exists to protect, and it is the
first block where a human can check it by changing one cause.

**Honest limit, and it is a large one:** the executable world is fuel and
generator only. PV, battery and loads remain *configured* assets. The demo
cannot show dispatch, service, unserved load or named energy flows. The
roadmap's "a simulated mini-grid behaves credibly" is completed by Block I,
not here.

**Deliberately unavailable:** staged envelopes, ingestion, operator evidence,
any product conclusion. The operator Site is unchanged by a Draft run.

**Review:** T022 carries a user-review checkpoint on control behaviour,
private-truth visibility, truth-versus-reported labels, and the scenario detail
screen's new statement that the document declares causes and does not declare
what the tank holds or what a device reads.

### Block C — Inspect exactly what could be ingested

**Slice:** T023.

**Shown at the end:** the Lab's Gateway panel shows immutable `STAGED`
publications produced from the previous block's generated observations, with
source time, publication time, mapping identity, message identity and quality —
and no receipt time, because nothing has been received. Raw inspection shows
the same validated content as the summary. The panel says plainly that staged
output has not crossed into the product.

**Why it is separate from release:** this is the first evidence-boundary
contract. It is worth reviewing the envelope and record language before a
Commit action exists to obscure it.

**Deliberately unavailable:** Commit, accepted evidence, Site history, source
health, Replay.

**Review:** required, on envelope and typed-record language.

### Block D — Release into normal evidence

**Slices:** the T024–T026 range.

**Shown at the end:** a person commits one completed Draft and watches records
become `ACCEPTED` — and watches at least one become `REJECTED` with a readable
reason. Committing twice produces no duplicate history. A Draft whose interval
overlaps already committed simulated history for the same Site cannot commit,
and says why.

**Deliberately unavailable:** derived Site history beyond accepted evidence,
conclusions, Findings, replacement of committed history.

**Review:** required, on Commit action language and accepted/rejected evidence
interpretation.

### Block E — Make the Site history inspectable

**Slices:** the T027–T029 range. **This block completes Demo Ready v1.**

**Shown at the end:** the same fuel story seen twice. Once as private simulator
truth in the Lab, and once on an operator Site page built only from evidence
that crossed ingestion — then the Lab is switched off and the Site page still
works. Changing the time window changes every time-dependent panel
consistently. A provenance drawer says which records a value came from, under
which Foundation and mapping version. Replay shows history as of a time, with
late records absent before their receipt.

**The claim it makes:** the architecture claim, made visible. This is the
roadmap's *earliest internal demo* and the first genuinely meaningful
milestone. It is also the earliest honest client-facing walkthrough, scoped
explicitly to the evidence loop, with no analytical or economic claim.

**Deliberately unavailable:** generator runtime assessment, fuel
reconciliation, Findings, work, financials, recommendations.

### Block F — Explain one operating problem

**Slices:** the T034–T038 conclusion family. **This is a proposed programme
reorder; see *What moved and why*.**

**Shown at the end:** a mini-grid practitioner opens one simulated Site, sees
that fuel movement is not fully explained by the recorded delivery and the
expected generator use, asks *why are you saying this*, and can follow the
answer to the tank samples, the hand dip, the generator energy, the delivery
record and the Foundation coefficient that formed the expectation — including
the reporting gap that limits it. Removing one required record weakens or
suppresses the claim rather than changing it silently.

**The claim it makes:** the product infers, and it knows when not to accuse.
The finding is *unexplained residual*, never theft. This is the roadmap's
*earliest domain-expert feedback* milestone, and there is little value in
waiting for a portfolio before getting that feedback.

**It needs one thing added to the source path first:** accepted generator
energy or runtime observations and a reportable delivery record. Block C
deliberately ships neither, so the first slices of this block extend the
allowlist through the same strict contract before any analytic exists.

**It does not need the full electrical world.** Fuel reconciliation needs
observed generator output and records, not optimised dispatch. Describing
runtime as *avoidable* does need Block I, and must not be attempted before it.

**Review:** required, on the expectation basis, the uncertainty and materiality
rule, and Finding promotion.

### Block G — Explain the economic stake

**Slices:** proposed followers; no task files yet.

**Shown at the end:** the same residual, with a bounded currency figure beside
it and its price assumption named and versioned. Change only the price and the
money changes while the trajectory, the envelopes and the technical claim do
not. Remove the technical basis and no money appears at all.

**Deliberately unavailable:** annual extrapolation by default, adding this
exposure to any overlapping line, and any implication of recoverable savings.

### Block H — Close one intervention loop

**Slices:** proposed followers; no task files yet.

**Shown at the end:** a recommendation with a stated success criterion becomes
an accepted Action with a target, guardrails and a verification window. Work is
marked complete and **the Finding stays open**. A later non-overlapping
committed window supplies new evidence, and only then does the outcome become
Verified, Ineffective or Inconclusive. An evidence-poor post-window produces
Inconclusive rather than success.

**The claim it makes:** the difference between AssetOps and a work-order
system. Sequential before/after windows are enough here; paired experiments are
not a prerequisite.

### Block I — Show electrical consequences

**Slices:** proposed followers; no task files yet.

**Shown at the end:** what the roadmap's Slice A actually asks for. PV, load,
battery SOC and power, generator state and named energy flows on one Lab
screen, with a requested 30 kW battery discharge and an accepted 22 kW visible
as two different numbers that never collapse into one. Sources and sinks
balance exactly. On the product side this makes Dispatch and Service views
derivable, and it is what first permits the word *avoidable*.

**Why it is here and not earlier:** crossing the boundary on a thin world is
worth more than a wide world that has not crossed. Block E's claim does not get
better by adding PV, and Block F's claim does not need it. This block is where
v4's controller contract, physical resolver and component-addressed state
become load-bearing rather than anticipated.

### Block J — Opportunity and asset pressure

**Slices:** later, independently reviewable followers.

**Shown at the end:** recurring renewable headroom identified after demand,
reserve, storage and policy constraints, and a paired load-addition experiment
whose comparison rejects any undeclared difference in resolved effective
inputs. Separately, battery stress derived from accepted observations, shown as
state and trajectory rather than a remaining-life date.

**Deliberately unavailable:** any claim about local commercial demand; any
exact replacement date; any use of the simulator's private stress accumulator
as an asset-health feed.

### Blocks beyond J

Portfolio roll-up over several independently credible Site stories, then the
cold-chain pack — `Demo Ready v2.5` in `.ai/PRODUCT.md`, which the user moved
behind the mini-grid conclusion chain on 2026-09-23. Both are followers, and
neither starts a generalisation project: a new pack reuses the time,
observation, gateway and ingestion contracts or the seam is wrong.

**How blocks map to the milestone names in `.ai/PRODUCT.md`**, because the
Planner reads both files and the two vocabularies are not interchangeable.
Blocks A and B are `M1C`. Blocks C, D and E are `Demo Ready v1`. Block F is
`Demo Ready v2`. The cold-chain pack is `Demo Ready v2.5`. Blocks G through J
have no milestone name yet, which is honest rather than an omission: they are
followers with no task files. A milestone says what may be claimed; a block
says what can be shown.

### The three finish lines

| Finish line | Reached at | What it means |
| --- | --- | --- |
| Internal architecture demo ready | End of Block E | Run a mini-grid, inspect truth, inspect device-reported values, inspect staged envelopes, Commit, see Site history through normal ingestion. |
| Domain-expert feedback ready | End of Block F | A practitioner can open one Site, inspect one bounded Finding, ask why, and challenge the evidence. Do not wait for a portfolio to get this. |
| Credible client demo ready | End of Block J plus portfolio | Portfolio, one deep Finding, economic translation, one opportunity, one intervention and its verification, and the simulator proof last. |

### What moved and why

**Two changes to the previous ordering, both from the roadmap companions.**

1. **The mini-grid conclusion chain moves ahead of the cold-chain pack.** The
   previous order put cold-chain (then `Demo Ready v1.5`, T030–T033) between the
   evidence loop and the first Findings (T034–T038). Blocks F through H now
   follow Block E directly, and cold-chain follows them. The reason is that
   every finish line that matters commercially is on the mini-grid path, and a
   second vertical proves an abstraction rather than a proposition. **This is a
   proposed programme-order change, not a renumbering**, and it is listed in
   Open Questions because `.ai/PRODUCT.md` still states the old order.
2. **Fuel reconciliation, not avoidable generator runtime, is the first
   Finding.** The earlier narrative companion proposes candidate avoidable
   runtime as the first substantial Finding. The later companion resolves it
   the other way and is right: the fuel world already executes after Block B,
   whereas avoidability needs feasible alternatives, policy and observations
   that only Block I supplies. Do not reopen this.

## Feature Areas

Causal prerequisites, settled semantics, and what is still open — per area.
These are what makes a screen allowed to say something, independent of when.

### 1. Site Foundation And Site Index

Visible in: Sites, Site Details, Foundation, run setup. **Built.**

Settled and in code: canonical `site_id` independent of run identity; the
narrowed M1 Site schema with versioned `foundation`; mandatory IANA timezone;
the `SiteRepository` and `SiteTemplateCatalog` ports behind one composition
root; shipped read-only catalog and separate writable store with one globally
unique id space and no overlay; instantiation by copy with template provenance;
untrusted-input handling for user-authored configuration. See
`D-2026-09-13-site-foundation-persistence`, `.ai/ARCHITECTURE.md`
*Configuration Persistence*, and the T005–T013 entries in `.ai/CODE_STATE.md`.

Still forward-looking: Foundation gains named physical properties beyond the
single `rating` scalar in Block A, and gains component-addressed binding when a
Site first carries two components of the same type. Foundation stays read-only
for every Site for all of M1.

#### Provenance And Status Concepts: the single reference

Cite this block rather than restating it. Six concepts, all independent. None
is derived from, defaulted from, or rendered as a proxy for another.

| Concept | Field | Values | Answers |
| --- | --- | --- | --- |
| Configuration origin | `origin` | `SHIPPED`, `USER` | Where did this configuration *document* come from? |
| Source mode | `source.mode` | `LIVE`, `SIMULATED` | Where does this Site's *evidence* come from? The `Simulated` badge is the rendering of `SIMULATED`; it is provenance, never status or health. |
| Lifecycle status | `lifecycle_status` | `PLANNED`, `COMMISSIONED`, `ACTIVE`, `DECOMMISSIONED`, `ARCHIVED` | Where is this Site in its own life? This project's extension; v6.9 has no site lifecycle enum. |
| Integration readiness | see M1 schema | see M1 schema | Is the plumbing for evidence in place? |
| Evidence availability | derived | No evidence, Limited, Available | Is there accepted evidence for the selected window? |
| Source health | derived | `Online`, `Stale`, `Offline` plus quality | Is the source reporting as expected? Never uses assessment vocabulary. |

There are two provenance concepts, not three. The simulator tag *is*
`source.mode = SIMULATED`; no `created_in_lab` or `is_simulator_site` field
exists, and adding one would record which shell created a Site, which nothing
downstream consumes.

The trap: in M1 the only creation path is the Lab's, so every `USER`-origin
Site also has `source.mode = SIMULATED`. They coincide by circumstance, not by
definition, and must never be collapsed or defaulted from each other.

### 2. Topology, Components, Devices, And Single Line Diagram

Visible in: Foundation, Lab Site View, Devices & Sensors. **Built.**

Settled: canonical Foundation is the source of truth for components, topology,
connectivity, ratings, devices and signal availability. The SLD archetype owns
only presentation — visual roles, node positions, symbol placement, routing —
binds by canonical type and role rather than by Site-specific identifiers, and
must never create, remove, rename or reinterpret a component or connection.
Unsupported topology produces an explicit incompatible state rather than
silently hiding assets. A future layout engine may replace the archetype
strategy behind the same view model.

Settled vocabulary: a breaker is topology and, when instrumented, something a
device may report about — never both in one record. Position is evidence, not
Foundation configuration. See `D-2026-09-20-breaker-vocabulary`, and
`Docs/simulator_design_v4.md` §5, which extends the ban past the lexical guard:
a renamed switching position or controller mode is still the deferred concept.
Rename a physical state, an authored cause or an operational record; do not
rename `OPEN/CLOSED/TRIPPED/AUTO/MANUAL` into synonyms to clear CI.

Still to decide, at the first slice that renders or stores a breaker state:
whether topology names breakers as components, connection equipment, connection
attributes or inline elements; the accepted-evidence vocabulary for positions
and control modes; whether `tripped` is a position, an event, a protection
outcome, or several of those in different records; and the symbol set.

Component addressing, from v4 §4.2: the semantic state name (`state_key`) and
the runtime address (`StateRef`) are different concepts and must not be merged
by encoding a component id into a state-key string. Two same-type loads or
chargers are normal, not an edge case. This becomes load-bearing at Block I.

### 3. Scenario Authoring And Scenario Catalog

Visible in: Scenarios, Scenario Details, run setup. **Built.**

Settled: `ScenarioDefinition` is the saved, versioned artifact; timeline events
are sub-artifacts addressed by `(scenario_id, scenario_version, event_id)`;
shipped and writable stores share one disjoint id space behind a domain port;
the three timeline entry kinds and seven categories; the public authoring
parameter versus private expectation boundary, separated at the parser rather
than by presentation. See `D-2026-09-20-scenario-definition-model`,
`-storage`, `-detail-affordances` and `D-2026-09-21-scenario-authoring-semantics`.

Settled by the execution contract: four execution roles; initialization
ownership; canonical units; point, window and interval-wide timing with
half-open dispatch; four bound cases with no silent policy; declared cadence
ownership; observation-source resolution against Foundation. See
`D-2026-09-21-scenario-execution-contract` and its amendment.

The load-bearing consequence: **a scenario authors causes, not results.** It
does not author a computed trajectory, it does not author what a device reads,
and after Block A it does not state a value for any parameter whose declared
owner is Site Foundation — it declares the need and states no number. Run-scoped
injections are SimulationRun intervention history, never written back into a
scenario version, and each must be materialised as an immutable
content-addressed artifact before execution so that a bare identifier cannot
change behind itself (v4 §5.2).

### 4. SimulationRun Runtime And Simulator Lab Shell

Visible in: run setup, Runs, Lab Site View. **Setup built; runtime is Blocks A
and B.**

Causal prerequisites:
- `SimulationRun` as execution and provenance record, with separate lifecycle
  (`Draft`, `Committed`) and execution status (`Ready`, `Running`, `Paused`,
  `Completed`, `Failed`, `Blocked`).
- Half-open simulation intervals `[start_time, end_time)`.
- Overlapping Drafts are allowed for experimentation; Commit is blocked when a
  Draft interval overlaps already committed simulated history for the same
  `site_id`. Committed evidence is immutable; Rerun creates a new Draft
  `run_id`, Replay inspects committed history without rerunning. M1 has no
  product operation that replaces committed history.
- A frozen deterministic identity with an answerer for every value: Site and
  Foundation version, scenario version and resolved parameters, interval,
  timestep, seed, simulator and model-profile versions, execution-contract
  version, resolved initialization inputs, publication profile and cadence,
  source and gateway identities, mappings, and ordered intervention artifacts.
- Initialization ownership (v4 §10): Foundation owns what the asset *is*;
  scenario or run-initial-condition owns what dynamic condition the world is
  *in* when the run starts, including SOC, fuel level, physical generator state
  and accumulated stress; the publication profile owns how observations are
  reported and never owns physical initial truth. **Unknown stress never
  silently becomes zero.**
- A minimal deterministic causal kernel precedes any authoritative trace.
  Generated golden traces are reproducible regression and playback artifacts
  bound to an exact frozen identity, never an alternate state authority.
- An execution status states what it checked. `READY` means every required
  executable input resolved and the selected model profile declares it can
  consume them; it does not mean a kernel can execute them, and it discloses
  that until a conformance test derives the supported set from the kernel. The
  disclosure names that condition and the slice that lands the test retires it.

Settled, and expensive to get wrong later: **a `READY` run is still a frozen
intention.** Malformed or unfreezable requests are refused; a resolvable Draft
with unsupported required inputs or unresolved Foundation answers is persisted
as `BLOCKED`. `READY` overrides neither boundary. Who failed to answer decides
which side a case falls on: every failure of a Foundation-owned value blocks.
See `D-2026-09-21-run-setup-outcome-vocabulary` and its 2026-09-22 extension,
`D-2026-09-22-foundation-property-absent-blocks`, and `.ai/ARCHITECTURE.md`
*Refusal And Blocking Vocabularies* for the naming rule.

**A third vocabulary arrives with the kernel.** Execution failure is distinct
from setup refusal and setup blocking, and v4 §23 names its members
(`ORDER_DEPENDENT_GROUP`, `BALANCE_IDENTITY_VIOLATION`,
`PHYSICAL_RESOLUTION_FAILURE`, `UNSUPPORTED_MODEL_STATE`,
`INTEGRATION_BOUND_FAILURE`, `TOPOLOGY_INCONSISTENT`, `NOT_COMPARABLE`). The
existing naming rule applies unchanged: from the name alone, a reader must be
able to tell which of the three it is.

Deferred: explicit branch or context selection over committed history.

### 5. Simulated World, Environment, Devices, And Event Injection

Visible in: Lab Site View, Environment, Quick Actions, Event Timeline, Devices
& Sensors. **This is Block B, widened at Block I.**

Causal prerequisites:
- Private world state as stocks, flows and typed discrete state, addressed by
  `StateRef`. Stocks persist across steps; flows prevail over a step and are
  recomputed; discrete states are declared by the domain pack with allowed
  values, an initialization owner, transition rules and observable signals, and
  every transition emits a trace record.
- **The boundary cycle** (v4 §6.1): at instant `T`, apply due events and
  configuration changes; the post-event state at `T` now exists; sample stocks
  and discrete state if a sample is due, attaching interval measurements for
  `[T-dt, T)`; apply the reporting transform and hand the result to staging;
  build the controller view; emit `ControlIntent`; resolve `AcceptedFlowSet`;
  integrate over `[T, T+dt)`; check conservation, bounds and invariants; carry
  state forward. A stock reading at `T` is post-event. An interval or rate
  reading at `T` summarises the interval that just ended. At the first boundary
  no preceding interval exists, so interval signals are unavailable unless a
  profile declares an initial historical window.
- Exact-rational world arithmetic with a versioned numeric policy. Authored
  floats are normalised once at the input boundary; per-step denominator
  limiting is forbidden and would make the policy's name false (v4 §8.3).
- A deterministic draw identity, if and when randomness is introduced: a draw
  is a pure function of contract version, seed, stream name, step index and
  ordinal under a canonical encoding and domain separation, so that adding a
  stream cannot perturb an existing one (v4 §9).
- Controller intent and physical acceptance are different objects. A requested
  30 kW and an accepted 22 kW must never collapse into one number; only
  accepted flows evolve the world and feed meter observations. The resolver is
  a declared deterministic cascade, and a genuinely simultaneous coupled system
  would need a new resolver plus an explicit solver and tolerance contract
  rather than an implementer quietly adding one (v4 §7).
- **The observation transform is a component, not a step inside execution.**
  Bindings are keyed by `(StateRef, device_id, signal_id)` and may declare
  cadence, noise, bias, quantisation, dropout, delay, stale behaviour,
  duplication, out-of-order behaviour, clock drift and quality semantics. Truth
  exists at every step; a reading exists only at a declared sample instant. A
  scenario declares no reading: every device value the product will ever see is
  generated here. Reporting-path forcings need no new execution role — a
  forcing whose state names a state of the reporting path rather than of the
  world is the shape, and reporting availability, sensor bias and gateway
  outage are one family attaching here.
- Reporting faults divide cleanly: sampling, bias and dropout belong to the
  observation transform; buffering, outage, retry and publication timing belong
  to the gateway (v4 §11).

Settled minimum for the first kernel: resolve the configured tank and
generator; initialise every state value from an attributable frozen input;
account for consumption, removal and delivery in canonical units; apply
scheduled causes exactly once; and define rather than silently clamp or ignore
a bounds failure. Consume the shipped forcings with their declared timing and
expose the supported runtime state without claiming a power-flow model. A
required executable input the profile does not support blocks the run.
Metamorphic proofs vary removal magnitude and time, or remove the cause, and
observe the corresponding consequence while the unaffected prefix and unrelated
state stay fixed.

Deferred past Block B: run-scoped injection controls; broad physical realism;
sensor bias in the Fuel Loss recipe, which stays free of it so its one lesson
stays clean — a real loss hidden by a reporting gap.

### 6. Gateway Publication And Ingestion Visibility

Visible in: Gateway & Ingestion, Ingestion Logs, Logs. **Blocks C and D.**

Causal prerequisites:
- A canonical Source Envelope carrying Site identity, source and device
  identity where applicable, schema and message identity, sequencing,
  publication timing, mapping and configuration version, quality and transport
  metadata, allowed simulation provenance, and **exactly one** strictly
  allowlisted typed record. No permissive `{type, payload}` escape hatch.
- Typed evidence families — Telemetry, Event, Alarm, OperationalRecord,
  ControllerRecord — owning their own semantic timestamps: telemetry
  `observed_at`; events, alarms and operational records `occurred_at`;
  controller records `decided_at`. The envelope records `published_at`.
  **`received_at` is assigned by ingestion and by nothing else.**
- Operational-record subtypes such as `fuel.delivery` and `fuel.manual_dip` use
  strict typed schemas, not free-form detail maps. A human record is an
  observation with its own completeness and errors: a physical fuel addition
  and its delivery report are different events, and the addition can happen
  while its record is delayed, wrong or absent.
- Telemetry uses a canonical `signal_id`, a scalar value, a canonical unit, a
  mapping version where interpretation needs one, and bounded measurement
  quality. Missing or stale telemetry is an evidence-coverage condition, not a
  fabricated measurement; `STALE` is not intrinsic measurement quality.
- Publication lifecycle `STAGED -> RELEASED -> ACCEPTED | REJECTED`, with the
  Lab owning release and ingestion owning acceptance and rejection.
- Commit seals eligible staged envelopes, persists an immutable release
  manifest and releases them through normal ingestion. It does not copy,
  regenerate, reinterpret, reassign message identities or regenerate the run,
  and **it never writes Evidence, Site history, source health, analytics,
  Findings or financial objects**. It is atomic at release scope and
  idempotent. Committing does not imply acceptance.
- Layered validation: envelope, typed record, Foundation semantics, then
  stream and evidence assessment. Late, missing, duplicated, out-of-order or
  irregular evidence is preserved and classified rather than discarded. A
  duplicate message identity with identical content is idempotent; the same
  identity with different content is a conflict.
- Gateway and source health is derived by AssetOps from heartbeat and arrival
  evidence, expected cadence, gaps, sequence behaviour and validation outcomes.
  A raw self-reported health conclusion is never accepted.

**Keep the first allowlist small.** Block C publishes fuel-level telemetry and
the `fuel.manual_dip` operational record and nothing else. Generator energy,
`fuel.delivery`, command events, maintenance records and policy-change evidence
each arrive with the product slice that consumes them: a delivery needs a
reportable delivery observation first, and a private generator flow needs a
modelled meter first.

Still to decide: the persistence layout for immutable staged envelopes plus
release manifest, and the exact typed schemas for the records past the first
allowlist. Both are due in the slice that first needs them.

### 7. AssetOps Site Evidence Views

Visible in: Site tabs, Gateway, Ingestion, Events, Logs, Replay. **Block E.**

Causal prerequisites:
- Site plus selected time window as the normal historical context.
- Read models derived from persisted envelopes and typed records, never from
  simulator runtime objects. **Rebuilding an operator view must require only
  persisted canonical envelopes, referenced configuration and mapping, and the
  ingestion pipeline** — with no runtime, no `WorldState`, no `LabProjection`
  and no raw `DeviceObservation` access.
- Progressive provenance: primary screens show decision-relevant source mode,
  window, freshness and completeness, and limitations affecting a claim;
  technical transport detail stays in an evidence drawer and in ingestion and
  log views. The drawer exposes contributing records, timestamps, source and
  device identities, quality, Foundation and mapping version, and run
  provenance. Consequential claims expose stronger provenance than ordinary
  telemetry. Scenario causes and private truth are never product provenance.
- Evidence-availability states — `AVAILABLE`, `LIMITED`, `UNAVAILABLE` — that
  downstream analytics must honour.
- **Replay is recorded history as of a time.** Evidence appears no earlier than
  its ingestion `received_at`; a late record does not appear retroactively at
  its source time; derived objects honour their own creation times and
  configuration validity. Replay does not re-simulate and does not recompute
  old analysis. Accelerated simulation produces many records received together
  at Commit, and the screen shows that honestly rather than inventing distinct
  receipt instants.
- A configuration-only Site shows No evidence, Limited or Unavailable rather
  than zero values, `OFFLINE` health, flat charts or derived conclusions.
  Source health becomes applicable only once a source is expected to report.

Still to decide: whether "Live Data" means latest ingested evidence,
replay-as-now, or a separate stream view for simulated Sites.

### 8. Evidence-Backed Findings, Incidents, Work, And Financials

Visible in: Performance, Findings, Work, Financials. **Blocks F, G and H.**

Causal prerequisites, in order — the order is the point:
1. **Evidence coverage and capability readiness.** A capability is Full,
   Limited, None or Not-applicable against its required records, coverage and
   uncertainty. *No record* is never a verified zero.
2. **Source and gateway health** from accepted evidence and expected cadence.
3. **Generator runtime and energy** from accepted telemetry, events and
   controller records. This supports consumption estimation. It cannot infer
   avoidability from a fuel-only model.
4. **Fuel reconciliation.** Opening, plus recorded deliveries, minus expected
   use, minus observed closing, equals an unexplained residual with declared
   uncertainty. Expected use is accepted energy times a configured
   specific-consumption coefficient, with the analysis basis and algorithm
   version frozen on the derived object.
5. **Finding promotion.** Only a material, sufficiently supported residual
   becomes a Finding, with a bounded claim, severity, confidence, alternatives,
   evidence references and a recommendation.
6. **Financial consequence**, downstream of all of it, from a versioned
   business context. The economic layer never strengthens the technical claim.
7. **Verification**, from a comparable post-window, never from work completion.

Load-bearing constraints:
- **The coefficient the product uses comes from Foundation configuration, never
  from the simulator's private rate.** Reading the number the simulator used
  computes the right answer for the wrong reason.
- Uncertainty is derived from declared measurement and model errors, and
  materiality is reviewed. Do not pick a threshold that guarantees the recipe
  triggers.
- Missing-record behaviour is a feature of the demo, not a gap in it. A missing
  delivery report suppresses the complete balance or bounds it specifically;
  insufficient energy coverage makes expected consumption unavailable; a sensor
  and a hand dip that disagree expose alternatives such as calibration or
  timing error. **Never consult private truth to choose the explanation.**
- Fuel language stays bounded as unexplained variance and never asserts theft
  or hidden cause from a discrepancy alone.
- Financial lines must not double-count across overlapping findings, and no
  annual extrapolation appears by default.

Still to decide, at the Block F checkpoint: whether the product's expectation
uses the time-valid Foundation coefficient or a separately declared operating
assumption. The recommendation is the Foundation coefficient for the first
narrow calculation, visibly labelled modelled, with its suitability and
uncertainty declared.

## Protected Seams

One table. The first column is the invariant; the last says what enforces it.
`.ai/ARCHITECTURE.md` holds the durable rules these derive from and is not
restated here.

| Seam | Invariant | Check | Late failure mode |
| --- | --- | --- | --- |
| Stack and module direction | Modular monolith with FastAPI, React/TypeScript and a Python simulator; strict parsers; file-backed repositories until a reviewed slice changes it. | CI architecture check on roots and import direction. | Incompatible layers make vertical slices unreviewable. |
| Dependency direction | `backend/` imports no simulator package. `simulator/` imports **no `assetops_backend` package at all**. A neutral `host/` composition leaf may import both, and nothing imports `host/`. Shared execution and envelope contracts live in a dependency-neutral module rather than being imported from the backend. | CI import guard, extended when `host/` is created. | Private simulator types become product dependencies and the simulator stops being independently testable. |
| Simulator feature gate | With `simulator_lab.enabled=false`, simulator routes, entry points, execution APIs and truth overlays are not served. Operator routes, simulated Sites, accepted evidence and Replay still work. The gate covers surfaces and execution, never objects or stores. | Route, API and navigation tests in both gate states. | Truth or execution stays reachable by direct URL after "disabling" the feature. |
| The one crossing | The only simulator payload eligible for normal ingestion is a canonical source envelope. `WorldState`, `LabProjection`, private truth, `ControlIntent`, `AcceptedFlowSet`, scenario expectations, trace records and raw `DeviceObservation` are never accepted. | Integration test rebuilds the Site view from serialized envelopes with the simulator absent. | A demo shortcut bypasses validation and breaks against a real source. |
| Private truth isolation | Change private truth without changing published envelopes and every product conclusion and export is unchanged. | Contract test mutating truth. | Analytics pass by oracle leakage and fail on real sources. |
| Envelope versus typed evidence | The envelope carries identity, timing, provenance and transport plus exactly one strictly allowlisted typed record. | Parser tests reject unknown fields, missing or multiple records, and permissive payloads. | Ambiguous payload handling accumulates and schema migration becomes unsafe. |
| Site identity | `site_id` is the only universal Site identity. `run_id`, scenario labels and run names are provenance only. | Test changes run and scenario identity and asserts Site identity and object roots do not move. | Runs become duplicate Sites or fragment history. |
| Commit semantics | Commit releases immutable staged envelopes by manifest and writes no Evidence, history, health, analytics, Findings or financial objects. | Storage inspection after Commit and before acceptance: only release state and manifest changed. | Commit becomes an unreviewable product backdoor. |
| Committed overlap | Overlapping Drafts are allowed; overlapping committed simulated history for the same Site and half-open interval is blocked. | Interval tests for overlap, containment, equality and adjacency, plus a UI blocked reason. | Site history silently merges ambiguous alternative worlds. |
| Ingestion owns receipt | `received_at` is created by ingestion. Source and publication times are fixed before Commit and never change. | Contract test across the boundary. | Timestamps stop meaning what audit needs them to mean. |
| Evidence immutability | Committed evidence is immutable. Rerun creates a new Draft `run_id`; Replay reads persisted evidence without executing. | Contract test. | Reproducibility and deterministic comparison collapse. |
| Projection versus composition | Projecting a document is validation. Composing projections into a value-at-a-time is a kernel, whatever it is called. No validator, run setup or authoring surface reaches a verdict that requires composing declared causes. | Review-time plus the absence of such a call site. | A verdict is reached one layer too early and has to be unwound after it has shipped. |
| Causal authority before traces | A kernel precedes any authoritative trace. A generated golden trace is a reproducible output of a named kernel version bound to an exact frozen identity, and a mismatch is refused. | Determinism and provenance tests. | An authored fixture becomes simulator truth and every later kernel is fitted to it. |
| Physical property ownership | Foundation declares what the site *is*; the model profile how the simulator *reasons*; the scenario what *happens*; the publication profile how the reporting installation *behaves*. A machine's physical property never lives in a scenario, and a declarable owner with no carrier for its value is an incomplete seam. | Parser rules keyed on the declared owner. | A scenario run against a different machine carries the first machine's physics with it. |
| Readings are generated | No authored artifact declares what a device reads, and no executable path reads an authored reading. | Parser role separation plus the observation transform's exclusive ownership. | The document and the transform disagree on the same screen. |
| The product's coefficient | The coefficient the product uses to form an expectation comes from Foundation, never from the scenario's private rate. | Analytics contract test. | The product gets the right answer for the wrong reason and fails on a real site. |
| Control vocabulary | Switching position and controller operating mode stay deferred, including as renamed synonyms. Rename a physical state, an authored cause or an operational record only. | The unconditional banned-token scan plus review against v4 §5. | The product asserts control semantics its evidence model cannot substantiate. |
| Conclusion order | Evidence coverage precedes source health, which precedes runtime, which precedes reconciliation, which precedes Finding promotion. | Analytics tests suppress downstream claims when upstream status is Limited or Unavailable. | Findings overstate certainty and cannot explain what is missing. |
| Bounded fuel language | Unexplained variance, never theft or hidden cause. | Content checks over Finding titles, summaries, recommendations and exports. | The product makes an accusation it cannot support. |
| Verification needs evidence | Work completion never resolves a Finding. Only a comparable post-window does. | Contract test: complete the work, assert the Finding is still open. | The product becomes a work-order system with extra steps. |
| Comparability grain | A paired comparison proves all-else-equal over resolved effective frozen inputs at field grain, never over version identifiers. Any undeclared difference is `NOT_COMPARABLE`. | Pair-builder test with differing versions and identical resolved inputs, and the reverse. | An opaque version bump conceals unrelated changes inside a causal claim. |
| Shared Site substrate | One read model, one view model, one component set in `frontend/src/sites/`. Shells compose and add through named slots; neither forks; the substrate carries no shell, mode or variant discriminant and imports no shell, simulator or flag code. | Single-definition and leaf-direction CI checks now; render equivalence when the Lab's Site view exists. | Two shells drift into two Site models, and by the time anyone notices neither can be changed alone. |
| Configuration persistence | Configuration is reached only through domain ports; storage lives in adapters chosen in one composition root; ports speak domain records and never paths, handles, YAML text or store exceptions. | CI check on adapter imports and on store primitives inside the domain. | Replacing the store becomes a rewrite of every caller. |
| Shipped versus user configuration | Shipped configuration is read-only at runtime and outside the writable store. One globally unique id space, no overlay, no precedence. Templates instantiate by copy and a later template change never alters an existing instance. | Collision, disjointness and copy-provenance tests. | A template release silently rewrites a Foundation that committed history depends on. |
| Untrusted configuration input | The fully materialised document is validated before any write; unknown keys and oversized documents are rejected; identity is charset-constrained and cannot traverse or collide case-insensitively; writes are atomic. | Parser and adapter tests including a failed write leaving the store byte-identical. | A user document escapes the store directory or forks Site identity. |
| Read-only Foundation | Foundation renders read-only for every Site. Deferred-by-decision controls are **absent from the DOM**, not disabled. | UI test asserts absence, not `aria-disabled`; API test asserts no update or delete route. | A greyed-out Edit reads as *soon*, which is a promise M1 has declined to make. |
| Mockup fidelity versus honesty | A screen adopts canonical layout only for content the product can source. No mockup literal appears unless the record supplies it. Three treatments, never blurred: not rendered, labelled in place, disabled with a stated reason. | Per-screen tests for literals, backing capability, absent deferred controls, accessible disabled reasons, and Mode never sharing a column with lifecycle. | The product ships a convincing shell whose columns and controls teach capabilities that do not exist. |
| Navigation truthfulness | A destination appears only when its route renders a truthful surface. No placeholder destinations, no disabled nav, no coming-soon routes. Operator navigation does not grow on the strength of a mockup rail that is the Lab's own. | Rail inventory guards in both shells. | A rail of ten items where six are dead teaches a product that does not exist. |
| SLD archetype boundary | The archetype is presentation over canonical topology and never creates, removes, renames or reinterprets a component or connection. | View-model test comparing rendered identities against topology, plus the incompatible state. | The diagram becomes a second topology model. |
| Vocabulary separation | Source health uses Online/Stale/Offline plus quality. Asset and product assessment uses its own vocabulary. They never collapse. | Surface text checks. | Health, asset condition and evidence readiness blur into misleading status. |
| Pack neutrality | The shared kernel branches on no `site_kind`, component type or pack identity; the observation and gateway path contains no domain branch. | Structural checks; a second pack introduces no branch. | The seam is wrong and rationalising it makes the second vertical a rewrite. |
| Status disclosure | A status that checked less than its name suggests says so, on the record and on the screen, and the disclosure travels with the status. Anything existing only because a condition holds names the condition as its expiry, never a slice number. | Review-time, plus the retiring slice recognising the named condition. | A claim that has become false outlives the slice that falsified it. |

## Screen And Shell Architecture

Settled and enforced in code. `D-2026-09-17-foundation-screen-architecture`
holds the derivation from v6.9 and the mockups; the guards hold the current
inventories; `.ai/CODE_STATE.md` says what shipped. Do not re-derive any of it
from a mockup.

- **Two shells, two rails.** The operator rail's long-run target is v6.9's ten
  object classes; the Lab rail is the Lab's own developer workspace menu and is
  gated with the Lab. `ScreenMockups.png` draws the **Lab** shell, not the
  operator product; read correctly it agrees that Simulator Lab is not an
  operator navigation item. Each rail has a single definition module consumed
  by both rendering and tests.
- **Operator Site tabs** are v6.9's eight: Overview, Foundation, Health,
  Performance, Findings, Work, Financials, Evidence. Overview and Foundation
  are destinations; the rest are labelled in place until their content
  contracts exist. Devices, Gateway, Ingestion, Events and Logs are Lab run
  tabs or site-scoped future content, never operator Site tab vocabulary.
- **Foundation subtabs** are Definition, Topology, Controls and Readiness.
  `Changes` is not rendered until a reviewed configuration-change capability
  exists, because v6.9 makes it a real intervention capability rather than
  version history. The row is section navigation, not a tab switcher, and is
  visually subordinate to the Site tab row above it.
- **Sites index columns** are the nine the M1 record can source, with Mode and
  lifecycle as separate columns and `Last analysed` rendered `--`. Assessment,
  top issue and evidence readiness stay absent until their sources exist.
- **Viewport commitment.** M1 is a desktop product at `1280px` or wider. It
  claims no mobile, phone or portrait-tablet form. Below the committed width it
  degrades truthfully with desktop density and internal scrolling rather than
  adopting a second information architecture, a reduced Site model, a different
  rail inventory or a different tab vocabulary. Page-level overflow is not an
  allowed density mechanism: shell chrome stays anchored and dense content owns
  its own scroll region. A dense table keeps its milestone columns at every
  width where it renders; a column hidden by viewport would be a fourth
  treatment. Breakpoints, if introduced, are tokens in
  `frontend/src/ui/tokens.css` consumed by both shells and the substrate.
- **Fidelity follows content.** A surface adopts canonical layout after that
  surface's content is real. Fidelity applied to the shared substrate is
  inherited by the Lab's Site view rather than applied twice.

Needs user choice only to override: v6.9's Site tab and Foundation subtab
vocabulary, the accepted T008 naming checkpoint, the nine-column Sites index,
or the decision not to claim a mobile product form. Each of those would be
settling a product commitment, not a CSS technique.

## Near-Term Sequencing

The live range is T020A through T023 — Blocks A, B and C. Per-slice Planner
guidance is in `.ai/PLANNING_HANDOFF_T020A_T023.md`; this section holds only
what the sequence itself has to guarantee.

**Dependency structure.** Every row is a hard dependency, not a preference.

| Slice | Depends on | What it would produce without it |
| --- | --- | --- |
| T020A | T020's merged Drafts, for sequencing only; independent of the kernel | nothing blocked in front of it |
| T020B | T020A's Foundation coefficient and its `dispatched-output` promotion | a lowering that still leaves the shipped Draft blocked, so its outcome never appears |
| T021 | T020A's coefficient and model-rule carrier | a first kernel whose physics arrive from the scenario, teaching every later kernel to do the same |
| T021 | T020B's declared semantics and its `READY` shipped Draft | a kernel choosing contract semantics inside an implementation, and no run it is allowed to execute |
| T021A | T019's narrowing, merged | a version move whose free window has closed, or a parser change that alters a run-setup outcome |
| T022 | T021's kernel and its reported trajectory | an observation transform with no truth to sample, and a document that still authors the readings it is meant to generate |
| T022 | the corrected Fuel Loss document | a generated reading and an authored reading disagreeing on the same screen |
| T023 | T022's ordered observations and the frozen publication profile | envelopes whose source timing and identity are invented rather than sampled |

**Two insertions that must not be folded back in.**

*T020A is an insertion, not a narrowing.* The other changes in this sequence
withdraw overreach: run setup stopped adjudicating cause-to-observation
coupling, and the scenario stopped authoring what a device reads. T020A adds a
field that does not exist — Foundation carries one optional scalar per
component and the binding can address only that scalar, so a generator's
specific fuel consumption has nowhere to live. You cannot narrow your way into
a missing capability. `D-2026-09-21-physical-property-ownership`.

*T021A is its own slice.* The contract-version window is free only while no
golden trace exists, and T022 is the slice that first produces one. Folding the
parser narrowing into T022 makes that slice's internal ordering load-bearing
and closes the window entirely if T022 is ever split. It sits after T021
because the kernel never reads the field either way.

**The loop inside T021.** T021 runs the kernel against the shipped Fuel Loss
document and reports the resulting trajectory; the document's authored numbers
are then corrected from what the kernel computed. The document cannot be
finalised first, because choosing the number first fits the kernel to an
authored expectation. This is an acceptance criterion, not a resequencing.

#### The execution-contract version ledger

`EXECUTION_CONTRACT_VERSION` is stamped into every frozen run and a provenance
mismatch refuses playback, so what the number is after each slice is a fact the
sequence holds rather than a detail a slice picks.
`D-2026-09-22-contract-version-scope` says when it moves; this is the only
place the count is stated.

| After | Version | Why |
| --- | --- | --- |
| `main` today | 2 | T019 merged it |
| T020 | 2 | no contract change; the `READY` disclosure is not one |
| T020A | 3 | narrowing: a Foundation-owned parameter has no value position, and the shipped document as it stands is refused by the new parser |
| T020B | 4 | two narrowings, one number: the four semantics pinned, and a requirement conflict refused rather than resolved. They share a slice, so nothing ever conformed to the version between them |
| T021 | 4 | no move: the `TRAJECTORY` oracle widens the document space off every executable path |
| T021A | 5 | narrowing: no `execution_requirement` position on a reported observation |
| T022 | 5 | no move: one document's content and a new component, not a change to the space |
| T023 | 5 | no move: the envelope contract is a new contract, not a change to this one |

**Write the move, never the literal.** Four narrowings are in flight across
three slices and they spend three numbers, because a narrowing that never
leaves the branch it was made on does not spend one — nothing conformed to the
version it would have replaced. Anything that states an absolute version
number will be wrong by the time it is read. The frontend fixture deliberately
pins `1` so the payload and the constant cannot be one literal by accident, and
that is unaffected.

## Open Questions

Three are live. None blocks a planned slice.

- **The product's expectation basis.** Whether fuel reconciliation's expected
  consumption uses the time-valid Foundation coefficient the kernel also used,
  or a separately declared operating assumption that may differ from it. The
  recommendation is the Foundation coefficient, visibly labelled modelled, with
  its suitability and uncertainty declared. **Trigger: the Block F checkpoint.**
  The same checkpoint owns deriving the uncertainty tolerance from declared
  error sources rather than a picked number.
- **The Fuel Loss document's authored numbers.** The removal magnitude, and
  whether the 300 L delivery that overfills the tank is reduced or kept
  deliberately as a second evidence puzzle. **Answered during T021**, from what
  the kernel computes rather than before it.
- **Whether reset clears intervention history.** **Triggered by the slice that
  plans injection**, which is deferred past Block B.

One accepted change is scheduled the same way and is not a question. **Option
C, the model profile declaring that it needs a Foundation value** rather than
the scenario declaring the need on its behalf, is where the need belongs,
because the law is the thing that knows it needs a coefficient. It was not
taken in T020A because it changes the shape of the frozen deterministic
identity in the same slice that changes Foundation's schema. **Trigger: the
first model rule that needs a Foundation value without a scenario asking for
it.** See `D-2026-09-22-foundation-value-declaration`.

Closed and not to be reopened: the shell question; removal of a user-created
Site, which stays a developer action on the store for M1; whether the Lab needs
its own Sites index, deferred to the slice that builds the Lab's Site view; and
which Finding comes first, settled as fuel reconciliation under *What moved and
why*.
