# T023 - Staged Source Envelopes

Status: planned
USER_REVIEW_REQUIRED: true

Intended branch: `task/T023-staged-source-envelopes`

## Feature

Gateway Publication, Commit, And Ingestion.

## UI-Verifiable Screen Behavior

For a T022 Fuel Loss run, the Simulator Lab Gateway panel shows immutable
`STAGED` publications produced from device/reported observations through a
strict Source Envelope and typed-record contract. A user can inspect summary
and raw validated content before release. The panel clearly states that staged
messages are not accepted evidence and carries no ingestion receipt time.

## Why This Is Next

T022 establishes causally computed truth and distinct device observations. The
next honest crossing is publication staging: converting supported observations
into canonical transport records without yet releasing them to AssetOps. This
slice settles the first evidence-boundary contract before Commit or ingestion.

## Dependencies

- T022 execution produces ordered observations with explicit source, device,
  signal, Site, run, and simulation-time context; T019 froze the versioned
  observation/publication profile and source/gateway identities.
- T018/T019 provide frozen scenario, Foundation/mapping, and run provenance.

## Acceptance Criteria

- A strict canonical Source Envelope carries schema/message identity, Site,
  source/gateway/device identity as applicable, `source_time`, publication time,
  sequence/deduplication identity, quality/transport metadata, and run/config/
  mapping provenance, plus exactly one allowlisted typed record.
- Envelope and typed-record parsers reject unknown fields, missing or multiple
  records, malformed identity/timestamps/units/quality, and permissive generic
  `{type, payload}` content.
- The first allowlist is exactly `Telemetry` for configured fuel-level device
  samples and `OperationalRecord` subtype `fuel.manual_dip` for the accepted
  persisted run-local hand-inspection observation from T022. A scenario timeline
  row is not itself publishable. A scheduled delivery or authored loss cause is
  not published merely because it exists in simulator truth; adding
  `fuel.delivery` waits for a reportable delivery observation.
- The first `Telemetry` schema carries `signal_id`, `observed_at`, scalar value,
  canonical unit, bounded measurement quality, and mapping version, with
  gateway/device identities in the envelope. The first `fuel.manual_dip`
  schema carries `occurred_at`, tank component identity, quantity, and canonical
  unit; its non-device source identity is explicit and gateway/device identity
  is not fabricated.
- Private simulator state, authored cause labels, non-executable evidence
  conditions, and private expectations cannot enter envelope payload or normal
  provenance. Publications originate from reportable observations, not from
  privileged truth.
- The gateway publication transform resolves configured device/signal mappings
  and canonical units. Missing identity/mapping or an unsupported observation
  produces an inspectable staging refusal; it never emits a partial envelope.
- Stable message identity and ordering make repeated staging of the same run
  output idempotent. Existing staged content is immutable; changed deterministic
  inputs require a different Draft `run_id`, not mutation of prior messages.
- Duplicate `message_id` with byte/semantic-equivalent canonical content is
  idempotent; reuse with different content is a conflict and writes nothing.
- Typed-record measurement/occurrence time follows its record semantics and
  `published_at` comes from the run's deterministic gateway-publication clock,
  not the wall time of the Stage-output click. `source_time` and `published_at`
  are fixed before Commit and remain stable across repeated staging;
  `received_at` is absent because only ingestion may assign it.
- Draft output is stored behind a staging/publication domain port. Callers do
  not depend on files, YAML/JSON storage, or adapter exceptions.
- A completed Draft with reportable persisted observations exposes a native
  Stage output action. Ineligible runs show a stable reason; repeating the
  action is idempotent and does not rerun the simulator or regenerate values.
- The Gateway panel lists record-backed STAGED messages and exposes a validated
  raw representation. It shows message/type/source/simulation/publication facts
  and quality where present, without inventing acceptance, freshness, health,
  severity, or conclusions.
- Malformed/refused publications are visibly distinct from staged messages with
  bounded reasons; they are not shown as ingestion `REJECTED`, which belongs to
  a later slice.
- Commit remains absent or disabled with a named future release prerequisite.
  No message is released, no manifest is created, and AssetOps/operator views
  remain unchanged.

## Required Product And Domain Semantics

- `STAGED` means an immutable canonical publication exists inside the Draft run
  boundary. It does not mean released, received, accepted, or evidenced.
- Source Envelope owns transport, identity, timing, sequencing, and provenance;
  its one typed record owns evidence semantics.
- Simulator truth reaches publication only through the device/observation path.
  A manual operational observation may use its own typed source path when that
  path is explicit in the accepted scenario contract.
- Commit/release, ingestion validation, evidence storage, and product
  conclusions remain separate later transitions.

## Protected Seams

- Simulator-to-product crossing: only released canonical envelopes may later
  reach ingestion; T023 creates staged envelopes and no shortcut product write.
- Envelope-versus-record separation: strict union and exactly-one-record proof.
- Private-truth isolation: mutation/leakage checks across runtime, scenario
  oracle, envelope, and public provenance shapes.
- Immutable/idempotent staging: stable identity and refusal of conflicting
  rewrites.
- Ingestion timestamp ownership: `received_at` cannot be set in the simulator or
  gateway stage.
- Persistence port and feature gate: staged output stays behind domain contracts
  and gated Lab routes.

## Focused Tests And Review Evidence

- Parser/contract tests for every accepted first record type and refusals for
  unknown keys/types, zero/multiple records, invalid units/timestamps/quality,
  missing provenance, and forbidden `received_at`.
- End-to-end Lab test executes the T022 run, transforms observations through
  configured mappings, stages envelopes, reloads them through the port, and
  renders the same identities/values in the Gateway panel.
- Action test proves Stage output eligibility, refusal for incomplete/failed
  runs, and that staging consumes persisted observations without execution or
  wall-clock-dependent timestamps.
- Leakage test varies private truth, authored cause descriptions, and private
  expectations without changing reportable observations and proves envelope
  bytes/semantics do not change.
- Idempotency/immutability tests prove repeated staging yields the same message
  set and a conflicting rewrite is refused.
- Failure-state tests distinguish staging refusal from `STAGED` and from future
  ingestion `REJECTED`.
- UI tests assert no `received_at`, accepted evidence, health, analytics,
  Finding, or operator update; raw content parses through the same strict
  contract displayed by the summary.
- Layout evidence for staged-message table and raw-detail region, including
  non-empty measured rows and internal overflow.
- Run architecture/workflow checks, relevant suites, typecheck, and build.

## Scope Limits

- No Commit/release manifest, overlap eligibility decision, ingestion,
  ACCEPTED/REJECTED evidence state, evidence store, Replay, source health,
  analytics, or Finding.
- No live protocol adapter, network broker, distributed queue, or generic event
  bus.
- No new physical model, runtime injection, or scenario editing.

## User Review

User review is required because Source Envelope shape, typed-record vocabulary,
STAGED/refusal language, and raw-versus-summary presentation establish the
first visible evidence-boundary semantics. The next Commit/ingestion task must
incorporate that outcome.
