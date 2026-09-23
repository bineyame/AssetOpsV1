# T023 - Staged Source Envelopes

Status: planned
USER_REVIEW_REQUIRED: true

Intended branch: `task/T023-staged-source-envelopes`

## Feature

Gateway Publication, Commit, And Ingestion. Block C of `.ai/FEATURE_MAP.md`,
which is this slice alone.

## UI-Verifiable Screen Behavior

For a completed T022 Fuel Loss run, the Simulator Lab Gateway panel shows
immutable `STAGED` publications produced from that run's generated
observations, with source time, publication time, mapping identity, message
identity and quality - and **no receipt time, because nothing has been
received**. A user can inspect a validated raw representation and see the same
content the summary shows. The panel says plainly that staged output has not
crossed into the product, and the operator Site page is unchanged.

## Why This Is Next

T022 establishes causally computed truth and distinct generated observations.
The next honest crossing is publication staging: turning supported observations
into canonical transport records without releasing them to AssetOps.

**This is the first evidence-boundary contract, and that is why it is its own
block.** The envelope and typed-record vocabulary it fixes travels to every
later record, and it is worth reviewing that language before a Commit action
exists to obscure it.

## Dependencies

- T022's ordered persisted observations with explicit source, device, signal,
  Site, run and simulation-time context, and the composition leaf it created.
- T019 froze the versioned observation and publication profile and the source
  and gateway identities.
- T018 and T019 provide frozen scenario, Foundation, mapping and run
  provenance.

## Acceptance Criteria

### The allowlist, and how small it stays

- **The first allowlist is exactly two records and it stays that small**:
  fuel-level `Telemetry` for the configured fuel-level device's samples, and
  `OperationalRecord` subtype `fuel.manual_dip` for T022's persisted run-local
  hand-inspection observation. **There is no generic `{type, payload}` escape
  hatch.**
- **This slice does not publish generator energy, `fuel.delivery`, command
  events, maintenance records or policy-change evidence.** Each arrives with
  the product slice that consumes it: a delivery needs a reportable delivery
  observation first, and a private generator flow needs a modelled meter first.
  Every one of them is a record the later fuel story will want and none has a
  consumer yet, which is exactly why adding one here would be unreviewable.
- A scenario timeline row is not itself publishable, and a scheduled delivery
  or authored loss cause is not published merely because it exists in simulator
  truth. Publications originate from reportable observations, never from
  privileged truth.

### The envelope and its one record

- **Exactly one typed record per envelope.** The envelope carries Site
  identity, source, gateway and device identity as applicable, schema and
  message identity, sequence identity, source time, gateway publication time,
  mapping and configuration identity and version, quality and transport
  metadata, and allowed simulation provenance. The typed record carries the
  measurement or occurrence semantics and nothing about transport.
- Envelope and typed-record parsers reject unknown fields, missing or multiple
  records, malformed identity, timestamps, units or quality, and any permissive
  generic payload.
- The first `Telemetry` schema carries `signal_id`, `observed_at`, a scalar
  value, a canonical unit, bounded measurement quality and a mapping version,
  with gateway and device identities in the envelope. The first
  `fuel.manual_dip` schema carries `occurred_at`, the tank component identity,
  a quantity and a canonical unit; its non-device source identity is explicit
  and no gateway or device identity is fabricated for it.
- **The envelope schema must be dependency-neutral.** Both the simulator and
  the backend will construct or read it, and the simulator may not import the
  backend to do so. It belongs in the neutral contract module T021 introduced,
  or in one shaped the same way. If the concrete type is backend-owned today,
  move or expose it neutrally rather than weakening the guard - v4 §3.2, rule
  5.

### Time, identity and immutability

- **Source time is preserved through buffering or delayed publication, and this
  slice assigns no receipt time.** `received_at` is created by ingestion and by
  nothing else; a staged message carrying one is a boundary violation rather
  than a convenience. No fault behaviour that would delay a publication is
  built here, but the contract is shaped so that one could not rewrite source
  time when it arrives.
- Typed-record measurement or occurrence time follows its record semantics, and
  `published_at` comes from the run's deterministic gateway-publication clock
  rather than the wall time of the Stage-output click. `source_time` and
  `published_at` are fixed before Commit and stable across repeated staging.
- **Re-staging an identical message is idempotent.** The same message identity
  with different content is a **conflict and writes nothing** - not a
  last-writer-wins update and not a partial write. Staged content is immutable;
  changed deterministic inputs require a different Draft `run_id`.
- Stable message identity and ordering make repeated staging of the same run
  output produce the same message set.
- **This slice stages completed Drafts.** Do not build or imply paused-run
  staging because the canonical product describes paused Commit eligibility
  later; a completed Draft with reportable persisted observations exposes a
  native Stage-output action, ineligible runs show a stable reason, and
  repeating the action reruns nothing and regenerates no value.

### Privacy at the boundary

- **No private content crosses.** No authored removal, private expectation,
  truth trace or cause description enters a payload or a provenance field.
- An opaque run or scenario version reference is provenance and not permission:
  it does not license a later analytic to dereference a private cause through
  it. State this where the provenance fields are defined, because the reference
  looks harmless at the moment it is added.
- The gateway publication transform resolves configured device and signal
  mappings and canonical units. Missing identity or mapping, or an unsupported
  observation, produces an inspectable staging refusal and never a partial
  envelope.

### Presentation, and what does not move

- **Staging changes nothing operator-visible.** The Site page is unchanged
  while a Draft stages, and raw inspection shows the same validated content as
  the summary rather than a second rendering of it.
- The Gateway panel lists record-backed `STAGED` messages and exposes a
  validated raw representation, showing message, type, source, simulation and
  publication facts and quality where present, without inventing acceptance,
  freshness, health, severity or conclusions.
- Refused publications are visibly distinct from staged messages with bounded
  reasons. They are not shown as ingestion `REJECTED`, which belongs to Block D.
- Staged output is stored behind a staging and publication domain port. Callers
  do not depend on files, storage format or adapter exceptions.
- Commit remains absent or disabled with a named release prerequisite. No
  message is released, no manifest is created, and operator views remain
  unchanged.

## Required Product And Domain Semantics

- `STAGED` means an immutable canonical publication exists inside the Draft run
  boundary. It does not mean released, received, accepted or evidenced.
- The Source Envelope owns transport, identity, timing, sequencing and
  provenance; its one typed record owns evidence semantics. The division is the
  contract, not a layout.
- An operational record is an observation with its own completeness and error
  modes, not a fact. A physical fuel addition and its human record are
  different events, and the record can be delayed, wrong or absent while the
  addition happened.
- Commit and release, ingestion validation, evidence storage and product
  conclusions remain separate later transitions.

## Read When You Reach It

- `Docs/simulator_design_v4.md` §11.2, the full gateway responsibility list.
  This slice implements the identity, timing and mapping parts; the buffering,
  outage, retry and duplicate-publication behaviours arrive with a slice that
  needs them.
- v4 §11.3, Draft versus Commit, which this slice only half-implements -
  Commit is Block D.
- v4 §12, operational records as a family with their own completeness and error
  modes. This slice ships one of them.

## Protected Seams

- The one crossing: only released canonical envelopes may later reach
  ingestion. This slice creates staged envelopes and no shortcut product write.
- Envelope versus typed evidence: a strict union with an exactly-one-record
  proof.
- Private-truth isolation: changing private truth without changing reportable
  observations changes no envelope byte.
- Immutable and idempotent staging: stable identity, and a conflicting identity
  writing nothing.
- Ingestion owns receipt: `received_at` cannot be set in the simulator or at
  the gateway stage.
- Dependency direction: the envelope schema is neutral and the simulator still
  imports no `assetops_backend`.
- Persistence port and feature gate: staged output stays behind domain
  contracts and gated Lab routes.
- Standing for this range, one line rather than repeated per criterion: no
  product conclusion in a scenario fixture; no private oracle value turned into
  evidence; no manufactured default hiding a missing answer; no simulator
  import of the backend.

## Focused Tests And Review Evidence

**UI success alone cannot prove any of the following**, and the packet says so
rather than offering a screenshot of a populated panel as evidence.

- Parser and contract tests for both accepted record types, with refusals for
  unknown keys and types, zero or multiple records, invalid units, timestamps
  or quality, missing provenance, and any `received_at`.
- A test that the allowlist is exactly two members, which fails if a third is
  added without a slice that says it is adding one.
- **Canonical reload test**: a staged artifact reloads through the port to the
  same content, so the canonical form is proved rather than assumed.
- **Idempotence and conflict tests**: repeated staging yields the same message
  set; a conflicting message identity writes nothing, asserted by inspecting
  the store after the attempt rather than by the absence of an error.
- **Leakage test**: vary private truth, authored cause descriptions and private
  expectations without changing reportable observations, and prove envelope
  bytes and semantics do not change. A second half proves a private cause
  description appears in no payload or provenance field.
- End-to-end Lab test executes the T022 run, transforms observations through
  configured mappings, stages envelopes, reloads them through the port, and
  renders the same identities and values in the Gateway panel.
- Action test proves Stage-output eligibility, refusal for incomplete or failed
  runs, and that staging consumes persisted observations without execution or
  wall-clock-dependent timestamps.
- A test proving the operator Site page is byte-identical before and after a
  Draft stages.
- Failure-state tests distinguish a staging refusal from `STAGED` and from
  ingestion `REJECTED`.
- UI tests assert no receipt time, accepted evidence, health, analytics,
  Finding or operator update, and that raw content parses through the same
  strict contract the summary displays.
- Layout evidence for the staged-message table and the raw-detail region,
  including non-empty measured rows and internal overflow.
- `tools/check-architecture.ps1` including the dependency guard over the
  neutral envelope schema, `tools/check-agent-workflow.ps1`, the backend,
  simulator and frontend suites, typecheck, and build.

## Scope Limits

- No third record type, and no generic payload shape that would admit one.
- No Commit or release manifest, overlap eligibility decision, ingestion,
  `ACCEPTED`/`REJECTED` evidence state, evidence store, Replay, source health,
  analytics or Finding.
- No gateway fault behaviour: no outage, retry, duplicate publication or
  delayed release. The contract must not preclude them; this slice does not
  build them.
- No paused-run staging.
- No live protocol adapter, network broker, distributed queue or generic event
  bus.
- No new physical model, runtime injection or scenario editing.

## User Review

User review is required. Review the envelope and typed-record **language**
here, rather than after a Commit action exists to obscure it: this is the first
visible evidence-boundary contract and the vocabulary it fixes travels to every
later record. `STAGED` and refusal language, and the raw-versus-summary
presentation, are part of that review.

The next Commit and ingestion slice must incorporate the outcome, and does not
assume this presentation survives unchanged if the user redirects it.
