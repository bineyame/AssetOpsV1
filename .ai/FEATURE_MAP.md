# AssetOps Feature Map

Scope: backend and frontend capabilities needed to support the canonical
Simulator Lab, Sites, Site Details, Site Configuration, Scenarios, Devices,
Gateway and Ingestion screens shown in `Docs/UI Design/Motivation`.

This is a feature map, not an implementation task list. Features are sequenced
by causal dependency: if a screen displays a fact, state, diagram, or claim, the
product must first have a truthful source for that display.

## Product Spine

M1 should become real in this order:

1. Define one canonical Site with stable identity, time-valid foundation data,
   configured topology, devices, mappings, ratings, and control assumptions.
2. Render that Site in AssetOps as a normal Site, including simulated
   provenance when applicable.
3. Author a scenario against the declared `site_id`; the scenario describes
   world events, interventions, evidence quality, interval, seed, and private
   expectations, but not findings or product conclusions.
4. Execute a SimulationRun in Simulator Lab as a virtual physical site with its
   own clock, world state, device truth, sensor reporting, event log, and
   gateway output.
5. Publish canonical source envelopes through the ingestion boundary; only
   persisted envelopes, not simulator runtime objects or private truth, feed
   AssetOps evidence.
6. Resolve Site Details, Gateway, Logs, and later evidence-backed analytics from
   Site + selected time window + ingested evidence.

Resolved M1 schema decision:
- M1 uses a narrowed canonical Site Foundation schema, not the complete future
  Site schema and not an MG-001-specific fixture schema.
- A Site conceptually has stable Site identity plus versioned Site Foundation.
  A practical YAML file may hold both for M1.
- The M1 Site fields are `site_id`, `display_name`, `site_type`,
  `lifecycle_status`, location, timezone, source/provenance, optional
  presentation metadata, created/updated timestamps, and a versioned
  `foundation`.
- The versioned foundation includes validity interval, components, topology,
  devices, signal mappings, ratings, and control assumptions.
- M1 starts with `site_type` values `MINIGRID` and `COLDCHAIN`, and lifecycle
  values `PLANNED`, `COMMISSIONED`, `ACTIVE`, `DECOMMISSIONED`, and
  `ARCHIVED`.
- `timezone` is mandatory and uses an IANA timezone because it affects
  scenario timing, source timestamps, Site history, and time-window analytics.
- `source.mode` and `source.provenance` are provenance, not lifecycle status,
  gateway health, evidence quality, or asset condition. A valid M1 Site may be
  `lifecycle_status = ACTIVE` and `source.mode = SIMULATED`.
- Presentation metadata such as a Site image is optional and must never affect
  identity, simulation, ingestion, analytics, or evidence interpretation.

Resolved first execution-mode decision:
- The first Simulator Lab vertical slice uses a deterministic recorded-run
  player, not the complete physical runtime.
- The recorded player is a bootstrap state producer only. It must use the same
  runtime-facing interfaces, clock semantics, event representations,
  device-reporting path, gateway staging path, and downstream ingestion
  contracts intended for the real deterministic simulator.
- The implementation must not introduce a demo-only ingestion path or expose
  precomputed AssetOps conclusions.
- Wherever practical, recordings should represent simulator/world state and
  events rather than final gateway envelopes, so device reporting and gateway
  publication are exercised from the first slice.
- The following vertical slice should replace the recorded state source with
  the real deterministic runtime loop without redesigning the Simulator Lab UI,
  runtime contract, device layer, gateway publication, ingestion boundary, or
  AssetOps downstream path.

Resolved M1 source/evidence contract decision:
- M1 separates the canonical Source Envelope from typed AssetOps evidence
  records. The envelope carries transport, identity, timing, sequencing, and
  provenance infrastructure; typed records carry evidence semantics.
- Every envelope contains `site_id`, source identity, schema/message identity,
  publication timing, sequencing where applicable, provenance, and exactly one
  strongly typed source record.
- `site_id` is the only universal Site identity. `run_id` may appear only as
  provenance for simulated evidence and must never participate in Site identity.
- Gateway/device identities are mandatory for gateway/device-originated records,
  but are not fabricated for operator-entered, imported, or external-system
  operational records.
- M1 typed evidence families are Telemetry, Event, Alarm, OperationalRecord, and
  ControllerRecord. Operational-record subtypes such as `fuel.delivery` and
  `fuel.manual_dip` use strict typed schemas, not free-form detail maps.
- Typed families own semantic timestamps: telemetry uses `observed_at`, events,
  alarms, and operational records use `occurred_at`, and controller records use
  `decided_at`. The envelope records `published_at`; AssetOps assigns
  `received_at` only after successful ingestion.
- Telemetry uses canonical `signal_id`, scalar value, canonical unit, mapping
  version where source interpretation requires it, and bounded measurement
  quality. Missing/stale telemetry is an evidence-coverage/source-state
  condition, not a fabricated measurement; `STALE` is not intrinsic measurement
  quality.
- Events are occurrences. Alarms are abnormal conditions with lifecycle/state
  such as `RAISED`, `ACKNOWLEDGED`, and `CLEARED`.
- GatewayHealth is derived by AssetOps from heartbeat/arrival evidence,
  expected signal cadence, missing/stale streams, validation failures, and
  related source evidence. A raw gateway self-report is not accepted as an
  authoritative health conclusion.
- Validation is layered: source-envelope validation, typed-record validation,
  Foundation semantic validation, and stream/evidence assessment. Late,
  missing, duplicated, out-of-order, or irregular evidence is generally
  preserved and classified rather than automatically discarded.
- Duplicate `message_id` with identical content is idempotent; reuse of the same
  ID with different content is rejected.
- Simulator private truth, oracle expectations, scenario causes, and precomputed
  product findings are prohibited from both Source Envelopes and product-facing
  evidence contracts.

Resolved M1 Commit decision:
- Commit is a state transition that releases a completed Draft SimulationRun's
  staged Source Envelopes for AssetOps ingestion.
- Staged envelopes are immutable evidence publications. Commit does not copy,
  regenerate, reinterpret, modify semantic content, or assign new message
  identities.
- Publication lifecycle is `STAGED -> RELEASED -> ACCEPTED | REJECTED`.
  Simulator Lab Commit owns `STAGED -> RELEASED`; AssetOps ingestion owns
  `RELEASED -> ACCEPTED | REJECTED`.
- Commit is atomic at SimulationRun release scope and idempotent; all staged
  output for an eligible run is released together or none is, and repeat Commit
  does not duplicate publications or regenerate the run.
- M1 may persist immutable staged envelopes plus a small release/commit manifest
  instead of copying envelopes into a second committed representation. The
  manifest records exactly which message IDs were released for audit, replay,
  and idempotent ingestion.
- A run may be committed only when execution completed successfully and staged
  output exists. Failed, blocked, running, or paused runs cannot be committed in
  M1.
- Commit does not imply successful ingestion. Released envelopes remain subject
  to source-envelope, typed-record, and Foundation semantic validation; records
  may be accepted or rejected individually by AssetOps.
- `source_time` and `published_at` are fixed before Commit and remain unchanged;
  `received_at` is assigned only when AssetOps accepts the released envelope.
- Commit releases source evidence only and never directly creates Site history,
  health state, findings, incidents, analytics, or other derived product
  objects.

Resolved M1 Single-Line Diagram decision:
- M1 implements the Single-Line Diagram with a reusable archetype template and
  data bindings, not a fully automatic topology-layout engine.
- Canonical Site Foundation remains the source of truth for components,
  topology, connectivity, ratings, devices, and signal availability. The SLD
  archetype owns only presentation/layout concerns such as visual roles,
  approximate node positions, symbol placement, and connection routing.
- The first archetype represents the hybrid mini-grid topology required by the
  M1 demo and binds components by canonical type/role, not Site-specific
  identifiers such as MG-001.
- The template must never create, remove, rename, or reinterpret Site components
  or connections. Unsupported topology must produce an unavailable/incompatible
  state instead of silently hiding assets.
- Site Configuration and Simulator Lab use the same configured topology and SLD
  view model. Site Configuration overlays static names and ratings; Simulator
  Lab overlays simulator runtime values; later AssetOps operational views
  overlay only accepted product evidence.
- M1 does not attempt arbitrary topology auto-layout, drag-and-drop schematic
  editing, generic electrical CAD behavior, or automatic routing.
- A small logical SLD view-model layer separates canonical Site topology from
  rendering/layout. A future graph/layout engine may replace the archetype
  layout strategy while preserving Site Foundation, topology, component
  identities, bindings, and runtime/evidence interfaces.

Resolved M1 provenance visibility decision:
- M1 uses progressive disclosure for provenance. Primary product screens show
  decision-relevant provenance; detailed technical provenance remains available
  through an Evidence/Provenance inspection drawer and dedicated ingestion/log
  views.
- Primary screens must make source mode, time window, evidence freshness and
  completeness, and evidence limitations affecting assessments or Findings
  immediately clear.
- Site-level UI visibly distinguishes source provenance such as `SIMULATED` from
  Site lifecycle state and gateway/source health.
- Findings and consequential assessments expose stronger provenance than
  ordinary telemetry: evidence basis, confidence or evidence sufficiency, and
  material limitations appear on or next to the claim, with View Evidence for
  deeper inspection.
- The Evidence/Provenance drawer exposes contributing records, timestamps,
  source/device identities, quality, Foundation/configuration version, mapping
  version, and SimulationRun provenance where applicable.
- Low-level transport metadata belongs primarily in dedicated ingestion/log
  views rather than normal operator screens.
- Simulator Lab may expose richer execution provenance for reproducibility;
  AssetOps product screens collapse it into concise indicators while retaining
  detailed inspection.
- Scenario/private-truth causes are never exposed as product evidence
  provenance.

Resolved planned/non-simulated Site behavior decision:
- M1 allows canonical Sites to exist before they have live integrations or
  SimulationRun evidence. Such Sites are valid configuration-only Sites and may
  appear in Sites List, Site Details, and Site Configuration.
- Configuration-only Sites may expose identity, lifecycle, location, timezone,
  Site type, Foundation version, components, topology, SLD, devices, mappings,
  ratings, control assumptions, and intended source/integration configuration.
- Operational evidence and conclusions must never be fabricated merely because a
  Site exists. If no accepted evidence exists, operational panels show explicit
  No evidence, Unavailable, or equivalent states rather than zero values,
  offline states, flat charts, or derived conclusions.
- Source mode, Site lifecycle, integration readiness, evidence availability, and
  source health are separate concepts. A Site may be `PLANNED`, have
  `source.mode = LIVE`, be `AWAITING_CONNECTION`, and have no gateway-health
  state yet.
- Gateway/source health becomes applicable only once a source has been
  commissioned or otherwise declared expected to report. A configured but
  not-yet-connected gateway is not automatically `OFFLINE`.
- Configuration SLDs may render without operational evidence because they
  represent declared topology. Runtime values appear only when supported by
  simulator runtime or accepted AssetOps evidence.
- Configured devices may appear before they report, but should be labeled as
  configured/awaiting evidence rather than operationally healthy or unhealthy.
- Generator-runtime assessment, fuel reconciliation, Findings, and Replay remain
  unavailable until their required accepted evidence exists.
- M1 may expose setup/readiness information while configuration editing remains
  file-backed/YAML.
- A real/intended-live Site Foundation may be exercised in Simulator Lab later,
  provided resulting evidence is explicitly marked `SIMULATED` and does not
  alter the Site's live integration state.

Resolved M1 configuration-authoring decision:
- M1 keeps canonical Site/Foundation configuration file-backed in YAML. YAML is
  the authoritative source of truth for Site identity, Foundation version,
  components, topology, devices, mappings, ratings, control assumptions, and
  related configuration.
- AssetOps provides a read-only Site Configuration UI that renders and explains
  canonical configuration, including configured SLD and device/signal
  relationships, but does not implement in-product editing or persistence.
- Edit, Save, Publish, approval, configuration-history management, and similar
  controls are deferred. Future-oriented edit affordances must be disabled or
  clearly marked unavailable and must never imply persistence that does not
  exist.
- Configuration version and validity semantics remain in the canonical model, so
  the UI may truthfully show Foundation version and effective dates.
- YAML configuration must be strictly validated on load. Invalid Site
  references, topology, device mappings, duplicate identities, invalid ratings,
  and unsupported values fail explicitly rather than being silently ignored.
- The migration path preserves the canonical configuration model while replacing
  YAML-only authoring with persistent versioned configuration APIs and
  user-editable product workflows later.

Resolved M1 SimulationRun overlap/branching decision:
- M1 allows any number of overlapping Draft SimulationRuns for the same Site and
  simulation interval so Simulator Lab can support experimentation, reruns, and
  deterministic comparison.
- The overlap restriction applies at Commit. Until explicit branch/version
  selection exists, only one committed simulated history may cover a given
  `site_id` and simulation time interval.
- A Draft run whose interval overlaps an already committed simulated run for the
  same Site may execute and be inspected, but its Commit action is blocked.
- Simulation intervals use half-open semantics `[start_time, end_time)`, allowing
  adjacent runs while preventing ambiguous overlap.
- Committed source evidence is immutable and must never be silently overwritten.
  Re-running the same Site/scenario/time window creates a new Draft `run_id`.
- Rerun means execute the simulator again as a new run, optionally using previous
  deterministic inputs as defaults. Replay means inspect already
  committed/persisted evidence without rerunning the simulator.
- Once committed, the run's deterministic identity is frozen: Site
  Foundation/configuration, scenario version, seed, simulator version, mappings,
  intervention history, and simulation interval.
- M1 has no normal product Replace committed history operation. Development/demo
  data may be reset through explicit administrative tooling, but destructive
  replacement is not part of the domain model.
- M1 intentionally avoids branches while preserving a future path for live
  evidence, simulated what-if branches, or alternative committed runs behind an
  explicit branch/context selector.

Resolved M1 technology stack decision:
- M1 uses the product specification's preferred MVP stack: Python/FastAPI
  backend, React/TypeScript frontend, Python deterministic simulator, modular
  monolith, strict source/API parsers, file-backed repositories/artifacts where
  sufficient, single-host container deployment, and CI-enforced architecture
  guards.
- The stack is a durable implementation posture for early slices, not product
  semantics. A Site, envelope, run, finding, or evidence claim must mean the
  same thing if infrastructure changes later.
- Do not introduce Kubernetes, microservices, Kafka, service mesh, complex
  distributed storage, or dedicated time-series infrastructure unless a reviewed
  slice proves the need.

Resolved Simulator Lab feature-gating decision:
- M1 gates Simulator Lab with `simulator_lab.enabled`.
- The flag is deployment-wide for M1 and shaped so it can become per-tenant
  later without changing product semantics.
- When enabled, Simulator Lab, Scenarios, Site Templates, Runs, simulator entry
  points, execution actions, and truth overlays may be served to allowed users.
- When disabled, simulator routes, navigation, entry points, execution actions,
  and truth overlays are not rendered or served. This is route/API gating, not
  merely hidden navigation.
- Existing simulated Sites, SIMULATED provenance, accepted evidence, operator
  routes, analytics, and Replay remain available because they are product Site
  history, not simulator execution.
- The flag gates simulator surfaces and execution only; it never alters
  evidence, findings, provenance, claim ceilings, or operator object schemas.
## Feature Areas

### 1. Site Foundation And Site Index

Visible in: Sites List, Site Details, Site Configuration, Simulator run setup.

Causal prerequisites:
- Canonical Site identity (`site_id`) independent of run identity.
- Narrowed canonical M1 Site schema that supports arbitrary Sites such as
  MG-001, MG-002, CC-001, and future real customer Sites without code changes.
- Site type, name, location, mandatory IANA timezone, source mode, provenance,
  lifecycle status, integration readiness, and created/updated metadata.
- Time-valid foundation data for components, topology, devices, signal
  mappings, ratings, control assumptions, and operating obligations.
- Configuration-only Site state for Sites with no live integrations or
  SimulationRun evidence yet.
- Simulated provenance model: `SIMULATED` is provenance, not health or status.
- Component truth remains distinct from device-reported evidence: Component
  truth -> Device/sensor behavior -> Reported signal -> Gateway -> Canonical
  source envelope -> AssetOps.
- A `SiteRepository` port owned by the product domain, with storage supplied by
  an adapter chosen in one composition root, so the persistence mechanism can be
  replaced without changing callers.
- A shipped canonical configuration catalog that is read-only at runtime and a
  separate writable store for user-authored configuration, sharing one globally
  unique `site_id` space with no overlay.
- A `SiteTemplate` catalog with its own `template_id`/`template_version`
  identity. A template is not a Site: it has no `site_id`, cannot be listed as a
  Site, simulated, targeted by a scenario, or receive evidence.
- Configuration origin (`SHIPPED` or `USER`) plus template provenance on
  user-created Sites, kept distinct from `source.mode`, lifecycle status,
  integration readiness, and source health.
- Untrusted-input handling for user-authored configuration: one strict parser
  for both stores, whole-document validation before write, constrained
  `site_id`, and atomic writes.

Candidate tasks, after review:
- Add the `SiteRepository` port, domain records, port error vocabulary, and a
  read-only shipped-YAML adapter behind a single composition root.
- Add file-backed canonical M1 Site definitions and Site list/detail read model
  resolved through the port.
- Add strict YAML validation for Site identity, Foundation version, components,
  topology, devices, mappings, ratings, control assumptions, and unsupported
  values.
- Show Sites List and Site Details for configured, simulated, planned, and
  configuration-only Sites.
- Add read-only Site Configuration summary with Foundation version, effective
  dates, configured SLD, device/signal relationships, and disabled/unavailable
  edit affordances.
- Add explicit no-evidence/unavailable states for configuration-only Sites.
- Add a shipped `SiteTemplate` catalog and template inspection view, read-only
  and clearly not a Site.
- Add a create-Site-from-template flow with a write adapter, identity
  validation, cross-store collision refusal, and origin/template provenance on
  the created Site.

UI-verifiable outcomes:
- User sees MG-001 as a Site row and detail page with stable identity.
- User can inspect a read-only Site Configuration UI backed by canonical YAML,
  with no implied edit persistence.
- User can inspect a configuration-only Site without seeing fabricated
  operational evidence, zero-value charts, source-health state, or analytics.
- Simulated status appears as provenance and does not replace normal Site
  status, evidence state, integration readiness, or source health.
- User can browse shipped configuration templates and see what a template would
  produce, without a template appearing anywhere as a Site.
- User can create a Site from a template, see it persist across a restart, and
  see it listed alongside shipped Sites with an explicit configuration origin.
- A duplicate or malformed `site_id` is refused with a specific reason and the
  store is left unchanged.

Semantics to decide:
- No remaining M1 Site Foundation authoring semantics are open. Create-from-
  template is in scope; in-place Foundation editing, Save/Publish over an
  existing Foundation, rename, delete, approval, and configuration-history
  management remain deferred, and `site_id` is immutable after creation.
- Open product question, not an architecture question: whether M1 needs any
  user-facing way to remove a user-created Site, given that delete would later
  collide with committed simulated history keyed to `site_id`. Until the user
  decides, removal is a developer action on the store, not a product capability.

### 2. Topology, Components, Devices, And Single Line Diagram

Visible in: Site Configuration, Simulator Lab Site View, Devices & Sensors.

Causal prerequisites:
- Component model for PV, inverter/PCS, BESS, generator, AC bus, loads, cold
  room, meters, breakers, sensors, and gateway.
- Connection/topology model that can drive the configured SLD and live
  simulation SLD without making the visual diagram the topology source.
- Reusable hybrid mini-grid SLD archetype that binds components by canonical
  type/role and owns only presentation/layout concerns.
- SLD view-model layer that validates Site topology compatibility with the
  archetype and produces an unavailable/incompatible state for unsupported
  topology.
- Ratings and units: kW, kWh, V, Hz, L, deg C, W/m2, percent, sample cadence.
- Device-to-signal mapping and protocol metadata.

Candidate tasks, after review:
- Render a configured SLD using the hybrid mini-grid archetype template bound
  to canonical Site topology.
- Add topology-to-SLD view-model validation and incompatible-topology UI state.
- Add Devices & Sensors configuration table from the same component/mapping
  source.
- Add read-only device/signal relationship presentation from canonical YAML.
- Add SLD runtime value slots that can later bind to simulator/evidence values.

UI-verifiable outcomes:
- Site Configuration SLD and Simulator Lab SLD show the same configured assets
  through the same SLD view model.
- Device rows and SLD labels agree on names, ratings, and signal availability.
- A compatible Site can reuse the hybrid mini-grid archetype without code
  changes, while incompatible topology is explicit rather than hidden.

Semantics to decide:
- Breaker/control state vocabulary and whether breakers are devices, component
  state, or both.
- How cold-room process symbols relate to mini-grid electrical topology.

### 3. Scenario Authoring And Scenario Catalog

Visible in: Scenarios list, Scenario Details, Simulator Lab run setup.

Causal prerequisites:
- ScenarioTemplate and ScenarioDefinition identities, versions, types, and
  descriptions.
- Event timeline model with scheduled events, interventions, evidence
  conditions, parameters, and usage.
- Private expectations/test assertions kept outside the product evidence path.
- Scenario target: declared Site or template-derived Site with stable `site_id`.

Candidate tasks, after review:
- Add scenario catalog and scenario detail views for the Fuel Loss Event.
- Support run setup selection of Site, scenario, start, duration, timestep,
  seed, and execution speed.
- Represent event parameters such as fuel removal without creating a product
  finding directly.

UI-verifiable outcomes:
- User can inspect Fuel Loss Event events and parameters before running it.
- Run setup explains what will happen without claiming an AssetOps conclusion.

Semantics to decide:
- Required scenario versioning fields.
- Event taxonomy: load, weather, equipment, data quality, loss/fraud,
  intervention, maintenance.
- Which parameters are public authoring data versus private test-oracle
  expectations.

### 4. SimulationRun Runtime And Simulator Lab Shell

Visible in: Simulator Lab run setup, Simulator Lab Site View, Runs.

Causal prerequisites:
- SimulationRun as execution/provenance record with `run_id`, `site_id`,
  scenario version, seed, simulator version, interval, lifecycle and execution
  status.
- Separate lifecycle (`Draft`, `Committed`) and execution (`Ready`, `Running`,
  `Paused`, `Completed`, `Failed`, `Blocked`).
- Simulation intervals use half-open semantics `[start_time, end_time)`.
- Draft SimulationRuns may overlap for experimentation; Commit is blocked when a
  Draft interval overlaps already committed simulated history for the same
  `site_id`.
- Simulation clock, timestep, wall elapsed, simulated elapsed, progress,
  execution speed, pause/resume, step, fast-forward, reset, rerun, replay, and
  jump-to.
- Determinism identity includes Site definition/configuration, scenario version,
  seed, simulator version, mappings/config, intervention history, and simulation
  interval; this identity is frozen once committed.
- Recorded-run player contract that can later swap its upstream state producer
  for the real deterministic runtime loop without changing downstream device,
  gateway, ingestion, or UI contracts.

Candidate tasks, after review:
- Build Simulator Lab shell with run header, tabs, controls, and paused
  recorded demo run.
- Add run-management read model with Draft/Committed status columns and allowed
  actions.
- Implement deterministic recorded-run playback through the runtime-facing
  clock/state/event interface before full physics.
- Add Commit eligibility/blocked state for overlapping committed simulated
  history using half-open interval checks.
- Add Rerun as new Draft `run_id` with previous deterministic inputs as
  defaults, and Replay as inspection of committed/persisted evidence.

UI-verifiable outcomes:
- User can inspect a paused MG-001 run with truthful run metadata and controls.
- User can run overlapping Drafts for experimentation, but sees Commit blocked
  when the run would overlap already committed simulated history for the same
  `site_id`.
- Draft runs do not offer Open in AssetOps until Commit has released evidence
  and ingestion has accepted it.
- User can distinguish Rerun from Replay: rerun creates a new Draft execution;
  replay inspects committed evidence without rerunning.

Semantics to decide:
- No remaining M1 SimulationRun overlap/branch semantics are open; explicit
  branch/context selection and normal product replacement of committed history
  are deferred.

### 5. Simulated World, Environment, Devices, And Event Injection

Visible in: Simulator Lab Site View, Environment panel, Quick Actions, Event
Timeline, Devices & Sensors.

Causal prerequisites:
- Private simulator state for irradiance, temperature, cloud cover, wind,
  generation, load, battery SOC/power, generator state, fuel tank, cold-room
  temperature, breakers, and injected events.
- Recorded state/event source for M1, shaped as simulator/world state rather
  than final gateway envelopes wherever practical.
- Device realism layer translating truth to reported values with bias, cadence,
  stale/missing samples, failures, delay, duplicate/out-of-order messages, and
  quality.
- Event log separating scheduled scenario events, manual interventions, device
  events, and gateway publication events.

Candidate tasks, after review:
- Add deterministic recorded world-state frames/events for the MG-001 run.
- Bind runtime values to SLD, site state, environment, devices, and timeline.
- Add non-persistent inject-event controls for the first event types.

UI-verifiable outcomes:
- User sees truth and reported sensor values side by side inside Simulator Lab.
- Event injection changes the simulated world/evidence path, not downstream
  product conclusions directly.

Semantics to decide:
- Which simulator truth values may appear in Simulator Lab versus AssetOps admin
  overlays.
- Minimum physical causality needed for a credible M1 demo.
- Intervention log persistence and replay rules.

### 6. Gateway Publication And Ingestion Visibility

Visible in: Gateway & Ingestion, Ingestion Logs, Gateway Output panel, Logs.

Causal prerequisites:
- Canonical Source Envelope contract containing source identity, Site identity,
  schema/message identity, publication timing, sequencing where applicable,
  provenance, and exactly one strongly typed source record.
- Typed AssetOps evidence contracts for Telemetry, Event, Alarm,
  OperationalRecord, and ControllerRecord; no permissive universal
  `{type, payload}` evidence model.
- Family-owned semantic timestamps: telemetry `observed_at`, events/alarms and
  operational records `occurred_at`, controller records `decided_at`; envelope
  `published_at`; ingestion-assigned `received_at` only after receipt.
- Publication lifecycle STAGED -> RELEASED -> ACCEPTED | REJECTED, with
  Simulator Lab owning release and AssetOps ingestion owning acceptance or
  rejection.
- Layered validation for source envelopes, typed records, Foundation semantics,
  and stream/evidence assessment.
- Logs for gateway, parser, validator, ingestion storage, and quality issues.

Candidate tasks, after review:
- Show staged gateway output for a Draft run with no `received_at`.
- Add Commit path that atomically marks a completed Draft run release manifest
  and exposes released Source Envelopes to the canonical ingestion boundary.
- Add Ingestion Logs view and Site Gateway overview from ingested envelopes
  and derived source-health state.

UI-verifiable outcomes:
- User can inspect staged, released, accepted, and rejected publication states
  without seeing regenerated or remapped message identities.
- AssetOps Site Details reflects only ingested evidence, never simulator panels.

Semantics to decide:
- Immutable staged-envelope plus release-manifest persistence layout; network
  hop remains deferrable.
- Exact M1 allowlisted typed-record schemas for telemetry, events, alarms,
  operational records, controller records, and the first fuel record subtypes.
- Bounded measurement-quality vocabulary, excluding `STALE` as intrinsic
  measurement quality.

### 7. AssetOps Site Evidence Views

Visible in: Site Details tabs, Gateway, Ingestion, Events, Logs; later Replay
and evidence-backed findings.

Causal prerequisites:
- Site + selected time window as the normal historical context.
- Evidence read models derived from persisted Source Envelopes and typed
  evidence records, not simulator runtime objects or private truth.
- Provenance propagation from source mode, scenario, run, mappings, and
  configuration-at-time, with `run_id` only as simulated-evidence provenance.
- Gateway/source health derived first from heartbeat/arrival evidence, expected
  signal cadence, source activity, missing/stale streams, sequence behavior,
  validation failures, ingestion outcomes, and related source evidence.
- Evidence-availability states such as `AVAILABLE`, `LIMITED`, and
  `UNAVAILABLE` for downstream analytics.
- Explicit unavailable/invalid/limited states when evidence is missing, stale,
  irregular, or insufficient.

Candidate tasks, after review:
- Show Site Details overview, Gateway status, Events, and Logs from ingested
  demo evidence.
- Add no-evidence/unavailable operational panel states for configuration-only
  Sites.
- Add first derived gateway/source-health summary from accepted evidence and
  expected cadence.
- Add concise source mode, time-window, freshness/completeness, and limitation
  indicators on primary Site evidence screens.
- Add Evidence/Provenance inspection drawer for claim/evidence chains.
- Add View Live Data bridge and Open in Simulator Lab bridge with correct shell
  transitions.
- Add Replay/read-at-time behavior once committed run history exists.

UI-verifiable outcomes:
- User can move from Simulator Lab to AssetOps and verify the product view is
  built from accepted evidence.
- User sees configuration-only Sites show No evidence or Unavailable instead of
  zero values, OFFLINE health, flat charts, or derived conclusions.
- User sees `SIMULATED` provenance separately from lifecycle state and
  gateway/source health.
- User sees `ONLINE`, `STALE`, or `OFFLINE` source health as a derived state,
  separate from asset condition, only when a source is expected to report.
- User can open an Evidence/Provenance drawer to inspect contributing records,
  timestamps, source/device identities, quality, Foundation/configuration
  version, mapping version, and run provenance where applicable.
- Changing the Site time window changes time-dependent panels consistently.

Semantics to decide:
- Minimal Site Details tab set for M1 versus the broader canonical operator
  shell.
- Whether "Live Data" means latest ingested evidence, replay-as-now, or a
  separate stream view for simulated sites.

### 8. Evidence-Backed Findings, Incidents, Work, And Financials

Visible in the broader canonical product, not fully in the provided motivation
screens, but causally downstream of the simulator and ingestion wedge.

Causal prerequisites:
- Derived analytics that consume typed evidence/read models, not simulator truth.
- Product conclusion sequence: Gateway/Source Health, Generator Runtime
  Assessment, then Fuel Reconciliation/Fuel Discrepancy.
- Generator Runtime Assessment reconciles generator state, active power, runtime
  counters, start/stop events, and available controller records to determine
  operating duration and evidence consistency.
- Fuel Reconciliation reconciles tank telemetry, fuel-delivery and manual-dip
  operational records, generator operation, and configured fuel-consumption
  assumptions.
- Evidence-availability states such as `AVAILABLE`, `LIMITED`, and
  `UNAVAILABLE` must weaken or suppress conclusions when evidence is
  insufficient.
- Findings are distinct from routine derived states and assessments, and are
  created only when materiality/confidence criteria warrant operator attention.
- Claim boundaries, confidence, basis labels, alternatives, recommendations,
  consequence, and verification criteria.
- Managed-object identity for findings, actions, incidents, and maintenance
  without duplicating scoped site indexes.
- Verification outcomes that resolve only from declared success criteria and
  guardrails.

Candidate tasks, after review:
- Add Generator Runtime Assessment from accepted evidence once source health is
  available.
- Add Fuel Reconciliation from accepted telemetry, operational records,
  generator operation, and configured fuel-consumption assumptions.
- Detect one material unexplained fuel variance from ingested evidence and show
  bounded Finding language.
- Show evidence basis, confidence/evidence sufficiency, and material limitations
  on or adjacent to the Finding.
- Link Finding evidence to the Evidence/Provenance drawer with source envelopes,
  configuration-at-time, and mapping versions.
- Create one recommendation/action and later verify its outcome from a post
  window.

UI-verifiable outcomes:
- User sees source health, generator runtime, and fuel reconciliation as a
  causal assessment chain.
- User sees a fuel discrepancy as evidence-backed unexplained fuel variance, not
  asserted as theft or hidden cause.
- User sees stronger provenance on Findings and consequential assessments than
  on ordinary telemetry.
- Product conclusions remain unchanged when private truth changes without
  changing published evidence.

Semantics to decide:
- Materiality/confidence criteria that promote routine assessment results into
  Findings.
- Fuel balance uncertainty and whether missing records produce Limited,
  Unknown, or Indeterminate.
- Which analytics are allowed in M1 versus deferred P1.

## Protected Architecture Seams

- Simulator Lab owns world state, private truth, device realism, event
  causality, time, and staged gateway publication.
- AssetOps owns Site history, evidence, analytics, findings, incidents, work,
  financials, and operator presentation.
- The only normal simulator-to-product crossing is canonical source envelopes
  released through ingestion.
- Source Envelopes and typed evidence records are separate contracts; the
  envelope must not become a permissive product evidence payload.
- `site_id` is the only universal Site identity; `run_id` is simulated-evidence
  provenance only.
- GatewayHealth is derived by AssetOps and must not be accepted as an
  authoritative raw health conclusion.
- Product conclusions must be sequenced from source/evidence coverage to
  operational assessment to material Finding; Findings are not raw telemetry or
  routine derived states.
- Fuel discrepancy language must remain bounded as unexplained fuel variance and
  must not infer theft or hidden cause from discrepancy alone.
- Site identity is stable and declared; run identity is provenance, never Site
  identity.
- SLD archetypes are presentation strategies over canonical topology; they must
  not create, remove, rename, or reinterpret components or connections.
- Scenario labels and run names must not become Site names or Site identity.
- Draft runs stage immutable Source Envelopes. Commit releases them via a
  release manifest and does not directly write Site history or derived objects.
- Overlapping Draft SimulationRuns are allowed, but only one committed simulated
  history may cover a `site_id` and half-open simulation interval until an
  explicit branch/context selector exists.
- Committed source evidence is immutable; rerun creates a new Draft `run_id`,
  while replay inspects committed/persisted evidence without rerunning.
- M1 has no normal product Replace committed history operation; destructive demo
  resets belong only in explicit administrative tooling.
- Product screens must show missing, invalid, stale, or limited evidence
  explicitly instead of fabricating values.
- Configuration-only Sites are valid Sites, but they must show No evidence or
  Unavailable operational states instead of fabricated telemetry, source health,
  charts, analytics, Findings, or Replay.
- YAML is the authoritative M1 configuration representation in both the shipped
  catalog and the user-authored store. The Site Configuration UI stays read-only
  for every Site and must not imply in-place edit, Save, Publish, approval,
  rename, delete, or configuration history, none of which exist.
- Configuration reaches the product only through the `SiteRepository` and
  `SiteTemplateCatalog` ports. Storage technology lives in adapters selected in
  one composition root; ports speak domain records and never expose paths, file
  handles, YAML text, or store-specific exceptions.
- Shipped canonical configuration is read-only at runtime and lives outside the
  writable store. A template is not a Site and holds no `site_id`;
  `template_id`/`template_version` are origin provenance only.
- `site_id` is globally unique across the shipped and user-authored stores. There
  is no overlay and no precedence: the same `site_id` in both stores is a load
  failure, and creation refuses an id already present in either store.
- Templates are instantiated by copy with recorded provenance. A later template
  change never alters an already-created Site.
- Configuration origin is a fourth separate concept alongside source mode, Site
  lifecycle, integration readiness, evidence availability, and source health.
- User-authored configuration is untrusted input. It crosses the same strict
  parser as shipped configuration with no lenient path, the whole materialized
  document is validated before any write, and writes are atomic.
- YAML configuration must be strictly validated on load and fail explicitly for
  invalid references, topology, mappings, duplicate identities, invalid ratings,
  or unsupported values.
- Source mode, Site lifecycle, integration readiness, evidence availability, and
  source health are separate concepts.
- Provenance visibility is progressive: primary screens show decision-relevant
  source mode, time window, freshness/completeness, and limitations; technical
  transport detail stays in Evidence/Provenance drawers and ingestion/log views.
- Scenario causes and private truth are never product evidence provenance.
- Source/gateway health uses Online/Stale/Offline plus quality; asset condition
  uses assessment vocabulary. These vocabularies must not collapse.

## Candidate Vertical Slices

These are UI-verifiable outcomes that could become tasks after this map is
reviewed:

1. One demo Site appears in Sites List, Site Details, and Site Configuration
   from a canonical Site Foundation file, resolved through the `SiteRepository`
   port.
1b. Shipped configuration templates are browsable and visibly distinct from
   Sites.
1c. A user creates a Site from a template; it persists, appears beside shipped
   Sites with an explicit configuration origin, and stays read-only.
2. The configured topology renders as a single line diagram and Devices &
   Sensors table from the same source.
3. Fuel Loss Event appears in Scenarios and can be selected in run setup.
4. A paused Draft SimulationRun opens in Simulator Lab from a recorded-run
   player with clock, controls, SLD, environment, devices, gateway staging, and
   event timeline.
5. Commit releases staged Source Envelopes with typed records; Ingestion Logs
   and Gateway & Ingestion show released/accepted/rejected state with correct
   timestamps.
6. AssetOps Site Details reads accepted evidence for MG-001 and exposes
   provenance plus unavailable states where evidence is incomplete.
7. Replay inspects committed/persisted evidence without rerunning, while
   latest-time navigation proves Site + time-window consistency.
8. Gateway/source health, Generator Runtime Assessment, and Fuel
   Reconciliation form the first product conclusion chain; only material
   unexplained fuel variance becomes a bounded Finding.

## Causal Sequencing

Dependency direction: configuration truth -> displayable Site/configuration ->
scenario/run intent -> gated simulator execution -> staged gateway output ->
Commit/release -> ingestion/accepted evidence -> product Site evidence views ->
Replay/time-window consistency -> derived health/assessments -> bounded
Findings. The direction is testable because later screens must fail unavailable
when their named input does not exist.

1. MVP stack and app shell.
   - Becomes true: the repo has the chosen FastAPI + React/TypeScript + Python
     simulator modular-monolith shape, strict boundary-parser posture,
     file-backed repository posture, and CI guard slots.
   - Depends on: no product step; it is the enabling technical decision for all
     subsequent slices.
   - Real dependency: without a stack, the Planner cannot write executable,
     reviewable tasks or CI checks.
   - UI-verifiable outcome: operator shell and Simulator Lab-disabled shell can
     render a route frame from the chosen app stack.
   - Deliberately unavailable: no real Site data, simulator routes, ingestion,
     analytics, editing, or findings; the UI shows empty/no-data states.

2. Simulator Lab feature gate.
   - Becomes true: `simulator_lab.enabled` controls simulator routes,
     navigation, entry points, execution actions, and truth overlays at serving
     boundaries.
   - Depends on: step 1, because it needs the real routing/config mechanism.
   - Real dependency: once simulator routes exist, retrofitting route/API gating
     risks hidden but reachable truth surfaces.
   - UI-verifiable outcome: with the flag off, operator routes work while
     Simulator Lab URLs and entry points are unreachable; with it on, the empty
     Simulator Lab shell can be reached.
   - Deliberately unavailable: with the flag off, runs cannot be started,
     inspected, rerun, or compared to truth; the UI has no simulator entry
     points and direct routes return a served-unavailable/not-found state.

3. Canonical Site Foundation and configuration-only Site.

   Step 3 splits into three sub-steps. They are ordered by a real dependency,
   not by convenience: the port must have a real read consumer before it can be
   trusted, and templates must exist as a distinct concept before any write
   path, or the first create will copy a shipped Site and silently collapse the
   template/instance distinction.

   3a. Site repository port and canonical read path.
   - Becomes true: one file-backed YAML Site with stable `site_id`, mandatory
     timezone, lifecycle, source mode, Foundation version, components,
     topology, devices, mappings, ratings, and control assumptions validates and
     appears in Sites/Site Details/Site Configuration, resolved through a
     `SiteRepository` port with a read-only shipped-YAML adapter behind one
     composition root.
   - Depends on: step 1; may proceed before or after step 2, but after is
     recommended so simulator entry points never appear before the gate exists.
   - Real dependency: every later run, envelope, evidence record, SLD, and
     analytic needs stable Site/Foundation identity. The port ships with this
     slice rather than later because retrofitting it after Sites, SLD view
     models, and evidence resolution all reach storage directly is a rewrite of
     every caller; it ships no earlier because a port with no consumer is
     speculative architecture.
   - UI-verifiable outcome: user can inspect the Site and read-only
     configuration without operational values.
   - Deliberately unavailable: any write path at all, templates, create, edit,
     Save/Publish, source health, charts, analytics, Replay, Simulator Lab run
     actions, and Findings. The port has no mutator in this sub-step; the UI
     says No evidence, Unavailable, or read-only/unavailable controls.

   3b. Shipped configuration templates as a distinct concept.
   - Becomes true: a read-only `SiteTemplate` catalog with its own
     `template_id`/`template_version` identity is inspectable, and a template is
     visibly not a Site.
   - Depends on: 3a, for the port shape and the configuration parser.
   - Real dependency: the template/instance distinction has to be structural
     before anything can be created. If create lands first, its only source is
     an empty form or a copy of a shipped Site, and the precedence, identity,
     and provenance rules become retrofits over existing user data.
   - UI-verifiable outcome: user browses shipped templates and sees what a
     template would produce, while Sites List still contains only Sites.
   - Deliberately unavailable: instantiation, a Create action, user Sites, the
     writable store, template authoring, template upload, and template editing.

   3c. User-created Site from a template.
   - Becomes true: a user picks a template, supplies identity, and a validated
     Site document is persisted through the write adapter into the user store;
     the Site survives restart and appears in Sites List beside shipped Sites
     with an explicit configuration origin and template provenance.
   - Depends on: 3b.
   - Real dependency: this is the first untrusted-input write boundary in the
     product, and it inherits an already-validated read model and an already
     separate template namespace instead of inventing both under write pressure.
   - UI-verifiable outcome: the created Site is a normal configuration-only
     Site everywhere, and a duplicate or malformed `site_id` is refused with a
     specific reason while the store stays unchanged.
   - Deliberately unavailable: in-place Foundation editing, Save/Publish over an
     existing Foundation, rename, `site_id` change, delete, duplicate-into-
     existing-id, Foundation version bump in place, configuration diff, history,
     rollback, approvals, template authoring, and import of an arbitrary YAML
     document. Site Configuration stays read-only for every Site regardless of
     origin.

4. Topology, devices, and configured SLD.
   - Becomes true: Site Configuration and Simulator Lab can use the same SLD
     view model and device/signal relationships from canonical topology.
   - Depends on: step 3.
   - Real dependency: the SLD and device table cannot be truthful until
     component, connection, rating, and signal-mapping truth exists.
   - UI-verifiable outcome: configured SLD labels, ratings, and Devices &
     Sensors rows agree; incompatible topology shows an explicit unavailable
     state.
   - Deliberately unavailable: runtime values, evidence overlays, topology
     editing, arbitrary auto-layout, and CAD behavior; value slots are empty or
     marked Awaiting evidence/runtime.

5. Scenario catalog and run setup.
   - Becomes true: Fuel Loss Event can be inspected and selected against a
     declared Site with interval, seed, timestep, duration, and public event
     parameters.
   - Depends on: step 3; step 4 is optional for catalog work but needed before
     run setup can preview topology.
   - Real dependency: a scenario must target stable Site identity and time
     semantics before a run can be meaningful.
   - UI-verifiable outcome: user sees scenario events and setup choices without
     any claimed AssetOps conclusion.
   - Deliberately unavailable: execution, Commit, Open in AssetOps, product
     findings, private expectations, and persistence editing; the UI labels the
     scenario as authoring/setup only.

6. Draft SimulationRun shell and recorded runtime playback.
   - Becomes true: a Draft run opens in Simulator Lab with clock, controls,
     run metadata, SLD runtime slots, environment, devices, gateway staging
     panel, event timeline, and recorded world-state playback.
   - Depends on: steps 2, 3, 4, and 5.
   - Real dependency: simulator execution needs gated routes, Site/Foundation
     identity, topology/device bindings, and run intent.
   - UI-verifiable outcome: user can inspect a paused recorded MG-001 run,
     advance time, and see simulator truth/reported values change only inside
     Simulator Lab.
   - Deliberately unavailable: product conclusions, Commit if no staged output
     or ineligible state, Open in AssetOps for Draft evidence, and normal
     AssetOps updates; controls explain Draft envelopes are not released until
     Commit.
   - Split/merge note: recorded playback and full deterministic runtime should
     be split. The recorded player proves UI/contracts first; the deterministic
     runtime can replace the state producer later without changing downstream
     contracts.

7. Gateway staging and strict envelope preview.
   - Becomes true: Draft runs stage immutable canonical Source Envelopes with
     typed records and show raw/summary gateway output before ingestion.
   - Depends on: step 6.
   - Real dependency: gateway publications are produced from simulator runtime
     state and device reporting; there is nothing valid to stage before a run.
   - UI-verifiable outcome: Gateway & Ingestion shows STAGED messages with
     source/gateway times, identities, quality, and no `received_at`.
   - Deliberately unavailable: accepted evidence, Site history, source health,
     analytics, and Replay; the UI says staged output has not crossed ingestion.
   - Reorder note: strict schema/parser definitions can be started with step 3,
     but UI staging should follow runtime playback so examples prove the
     contract under simulator output.

8. Commit, release manifest, and ingestion logs.
   - Becomes true: eligible completed Drafts atomically release staged
     immutable envelopes through normal ingestion; ingestion validates and marks
     records ACCEPTED or REJECTED.
   - Depends on: step 7.
   - Real dependency: Commit releases existing staged publications and must not
     copy, regenerate, or derive product objects directly.
   - UI-verifiable outcome: user sees STAGED -> RELEASED -> ACCEPTED/REJECTED
     states, stable message IDs, `received_at` assigned only after acceptance,
     completed-run Commit eligibility, and overlap-blocked Commit for
     conflicting intervals.
   - Deliberately unavailable: derived Site history beyond accepted evidence,
     conclusions, Findings, replacement of committed history, and product
     branch selection; the UI marks blocked/ineligible Commit reasons.
   - Split/merge note: Commit/release and ingestion logs may split if needed,
     but must land close together so release is immediately observable.

9. AssetOps Site evidence views and provenance.
   - Becomes true: Site Details, Gateway, Events, Logs, and evidence panels read
     accepted evidence by Site + selected time window, with progressive
     provenance and explicit limitation states.
   - Depends on: step 8.
   - Real dependency: product evidence views must consume accepted evidence, not
     simulator staging or runtime objects.
   - UI-verifiable outcome: Open in AssetOps shows the same `site_id` and only
     accepted evidence; configuration-only or incomplete windows show No
     evidence, Limited, or Unavailable.
   - Deliberately unavailable: generator runtime assessment, fuel
     reconciliation, Findings, work, financials, and product recommendations;
     the UI names the missing evidence/assessment prerequisite.

10. Replay and time-window consistency.
    - Becomes true: user can inspect committed/persisted Site history as-of a
      time window without rerunning the simulator; changing the Site time window
      changes time-dependent panels consistently.
    - Depends on: steps 8 and 9.
    - Real dependency: Replay is an as-of view over persisted accepted history;
      it cannot exist from Draft runtime state.
    - UI-verifiable outcome: Replay uses committed evidence, preserves per-run
      provenance, and remains available when Simulator Lab is disabled.
    - Deliberately unavailable: rerun/Reset from Replay, simulator truth
      comparison when gated off, branch/context selection, and future leakage;
      the UI distinguishes Replay from Rerun.

11. Gateway/source health.
    - Becomes true: AssetOps derives source health from heartbeat/arrival
      evidence, expected cadence, gaps, validation outcomes, and related source
      evidence.
    - Depends on: step 9; step 10 is recommended first to prove time-window
      consistency, but source health can be built earlier for a fixed window.
    - Real dependency: health is a product assessment over accepted evidence and
      expected reporting, not a raw simulator or gateway assertion.
    - UI-verifiable outcome: user sees Online/Stale/Offline source vocabulary,
      separate from Site lifecycle and asset condition.
    - Deliberately unavailable: generator runtime, fuel reconciliation, and
      Findings; the UI shows source health as evidence readiness, not a
      conclusion about asset condition.

12. Generator Runtime Assessment.
    - Becomes true: accepted generator telemetry/events/controller records are
      reconciled into runtime and evidence-consistency assessment.
    - Depends on: step 11.
    - Real dependency: generator runtime conclusions need evidence coverage,
      freshness, validity, and source-health context.
    - UI-verifiable outcome: user sees measured/derived generator runtime with
      basis, confidence/evidence sufficiency, and provenance drawer links.
    - Deliberately unavailable: fuel discrepancy Finding and recommendation;
      the UI says fuel reconciliation waits for fuel movement and runtime
      evidence.

13. Fuel Reconciliation and bounded Finding.
    - Becomes true: AssetOps reconciles tank telemetry, deliveries/manual dips,
      generator runtime, and fuel-consumption assumptions; only material,
      sufficiently supported unexplained variance becomes a Finding.
    - Depends on: step 12.
    - Real dependency: expected fuel use depends on generator operation and
      evidence sufficiency; a discrepancy cannot be claimed before that chain.
    - UI-verifiable outcome: user sees an unexplained fuel variance with
      bounded language, evidence basis, alternatives/limitations, and View
      Evidence.
    - Deliberately unavailable: theft claims, hidden-cause assertions,
      automatic incident/work closure, financial double-counting, and
      recommendations without success criteria; the UI keeps claim boundaries
      adjacent to the Finding.
    - Split/merge note: reconciliation and Finding promotion may split if the
      materiality/confidence rule needs user review; do not merge with
      generator runtime.

## Enforceable Protected Seams

Prioritise the first seven seams for immediate guards because they are cheap to
protect while contracts are small and expensive after data, UI, and analytics
depend on them.

| Seam | Invariant | Concrete test/check | Late failure mode | Guard |
| --- | --- | --- | --- | --- |
| Stack and module direction | M1 is a modular monolith with FastAPI, React/TypeScript, Python simulator, strict parsers, and file-backed repositories unless a reviewed slice changes it. | CI architecture check verifies expected backend/frontend/simulator roots and bans direct UI-to-simulator imports or simulator-to-product writes. | Tasks build incompatible layers or infrastructure that make vertical slices hard to review. | CI guard |
| Simulator feature gate | `simulator_lab.enabled=false` means simulator routes, entry points, execution APIs, and truth overlays are not served, while operator routes and Replay still work. | Route/API/navigation test runs with flag off and asserts simulator URLs/actions are unreachable and operator simulated Site + Replay still render. | Simulator truth or execution remains reachable through direct URLs after "disabling" the feature. | CI guard |
| Simulator/product boundary | Simulator Lab owns world/truth/execution/staging; AssetOps owns evidence, analytics, findings, and operator presentation. | Contract/import test forbids AssetOps read models from importing simulator runtime/truth modules; UI test asserts Simulator Lab has no findings/health/reconciliation outputs. | Product conclusions silently depend on privileged simulator state and cannot generalize to live evidence. | CI guard |
| Source-envelope crossing | The only normal simulator-to-product crossing is released canonical Source Envelopes through ingestion. | Integration test proves Site Details can be rebuilt from serialized envelopes with simulator runtime unavailable. | A demo-only shortcut bypasses validation and later breaks live protocol adapters. | Contract test |
| Envelope versus typed evidence | Source Envelope carries identity/timing/provenance/transport and exactly one strict typed record; it is not a free-form product payload. | Parser tests reject unknown envelope fields, missing typed record, multiple records, and permissive `{type,payload}` records. | Analytics accumulate ambiguous payload handling and schema migration becomes unsafe. | Unit/contract test |
| Site identity | `site_id` is universal Site identity; `run_id`, scenario labels, and run names are provenance only. | Test changes `run_id`/scenario name and asserts Sites index row, downstream `site_id`, and object roots do not change. | Runs become duplicate Sites or product history fragments by run. | Contract test |
| Commit semantics | Commit releases immutable staged envelopes by manifest and never writes Site history, health, analytics, findings, or derived objects directly. | Integration test inspects storage/state after Commit before ingestion acceptance; only release state/manifest changes. | Commit path becomes an unreviewable product backdoor. | Contract test |
| Committed overlap | Overlapping Drafts are allowed; overlapping committed simulated history for same `site_id` and half-open interval is blocked until branch/context selection exists. | Interval test covers overlap, containment, equality, and adjacent `[start,end)` cases; UI test shows blocked Commit reason. | Site history silently combines ambiguous alternative histories. | Unit/contract test |
| Evidence immutability and rerun/replay | Committed source evidence is immutable; Rerun creates a new Draft `run_id`, Replay reads persisted evidence without rerunning. | Test Rerun creates a new Draft and Replay performs no simulator execution or envelope regeneration. | Audit, reproducibility, and deterministic comparisons collapse. | Contract test |
| YAML configuration authority | M1 Site/Foundation YAML is the authoritative representation and is strictly validated on load, in both the shipped catalog and the user-authored store, through one parser with no lenient path. | Schema/semantic validation tests reject invalid references, topology, duplicate IDs, mappings, ratings, units, timezone, and unsupported values, and run the same parser over a user-authored document fixture. | UI and simulator normalize different invalid assumptions, or user-authored documents are trusted more than shipped ones. | Unit/contract test |
| Read-only configuration UI | M1 Site Configuration UI renders every Site read-only regardless of origin and never implies in-place edit, Save, Publish, approval, rename, delete, or configuration history. Authoring exists only as create-from-template in a separate flow; `site_id` is immutable after creation. | UI test opens Site Configuration for a shipped Site and a user-created Site and asserts no edit/Save/Publish/rename/delete affordance and copy stating configuration is fixed at creation in M1; API test asserts no update or delete route exists for a Site. | Users infer an editing and version-history workflow the product does not have, or an edit path lands before Foundation re-versioning semantics exist. | Review-time + contract test |
| Configuration persistence port | Site and template configuration is reached only through domain-defined ports; storage technology lives in adapters selected in one composition root. Port signatures and errors use domain records, never paths, file handles, YAML text, or store-specific exceptions. | CI architecture check bans imports of `sites/adapters/**` from anywhere except the single allowlisted composition module, and bans `yaml`, `pathlib`, `sqlite3`, and `open(` inside `sites/` outside `adapters/`; a fake in-memory adapter satisfies the port in service tests without importing an adapter. | Storage assumptions leak into read models, API, and UI, and replacing the store becomes a rewrite of every caller instead of one adapter. | CI guard |
| Shipped versus user-authored configuration | Shipped canonical configuration is read-only at runtime and lives outside the writable store. Templates are not Sites and hold no `site_id`. `site_id` is globally unique across both stores with no overlay and no precedence; `template_id` is origin provenance and never Site identity. | Test asserts the same `site_id` in both stores fails loudly at load, create refuses an id present in either store case-insensitively, no write path resolves inside the shipped catalog, and changing a template does not alter an already-created Site. | Shipped and user configuration merge into one ambiguous namespace, or a template release silently rewrites Foundations that committed history depends on. | CI guard |
| User-authored configuration input | User-supplied configuration is untrusted input at a strict boundary: the fully materialized document is validated before any write, unknown keys and oversized documents are rejected, `site_id` is charset-constrained and cannot traverse or collide case-insensitively, free text is never identity or a path, and writes are atomic. | Parser/adapter tests cover unknown keys, oversized input, `..` and separator and absolute-looking ids, case-variant collision, and a failed write leaving the store byte-identical. | A user document takes down the Sites index, escapes the store directory, or forks Site identity. | Unit/contract test |
| SLD archetype boundary | SLD archetype owns presentation only and must not create, remove, rename, or reinterpret canonical components or connections. | View-model test compares rendered component/connection IDs against canonical topology and checks incompatible topology state. | Diagram becomes a second topology model and diverges from simulation/evidence. | Unit/contract test |
| Configuration-only Site states | A valid Site with no accepted evidence shows No evidence/Unavailable rather than fabricated telemetry, charts, source health, analytics, findings, or Replay. | UI test renders a configuration-only Site and asserts no zero-value operational defaults or OFFLINE health. | Demo placeholders become false product claims. | CI guard |
| Source/gateway health derivation | Gateway/source health is derived by AssetOps from accepted evidence and expected cadence, never accepted as an authoritative raw health conclusion. | Parser rejects raw `GatewayHealth` conclusion records; analytics test derives Online/Stale/Offline from evidence conditions. | Operators trust self-reported or simulator-assigned health. | Contract test |
| Vocabulary separation | Source health uses Online/Stale/Offline plus quality; asset/product assessment uses Healthy/Watch/Needs attention/Degraded/Unknown. | UI snapshot/accessibility text check scans relevant surfaces for vocabulary misuse. | Health, asset condition, and evidence readiness blur into misleading status. | CI/review check |
| Provenance disclosure | Primary screens show decision-relevant source mode, window, freshness/completeness, and limitations; technical detail lives in evidence/provenance drawers/logs. | UI test asserts simulated Site headers and findings expose provenance summary plus drawer links to records/config/mapping/run provenance. | Consequential claims become hard to audit or normal screens become transport dumps. | Review-time + UI test |
| Private truth isolation | Scenario causes, private expectations, and SimulationTruth never enter envelopes, evidence, operator UI, exports, or product provenance. | Contract test mutates private truth without changing envelopes and asserts product conclusions/exports do not change. | Analytics pass demos by oracle leakage and fail on real sources. | CI guard |
| Product conclusion order | Source/evidence coverage precedes generator runtime, which precedes fuel reconciliation, which precedes material Finding promotion. | Analytics tests block/suppress downstream conclusions when upstream evidence status is Limited/Unavailable. | Findings overstate certainty and cannot explain missing prerequisites. | Contract test |
| Fuel claim language | Fuel discrepancy is bounded as unexplained variance and never asserts theft or hidden cause from discrepancy alone. | Content/test fixture checks Finding titles, summaries, recommendations, and exports for banned causal assertions. | Product creates legally/operationally risky accusations. | Review-time + test |

## Feature-To-Task Guidance

This is Architect guidance for the Planner's later task writing. The Planner
still owns slice intent, acceptance criteria, scope limits, and user-review
placement in task files.

### Early Feature: Stack, Shell, And Gate

Divide into slices:
- Minimal FastAPI/React/TypeScript/Python simulator skeleton with file-backed
  repository pattern and CI guard placeholders.
- Operator shell with Sites/Site Details/Site Configuration route frames and
  empty states.
- `simulator_lab.enabled` route/API/navigation gate, tested both enabled and
  disabled.

Seams inside the feature: stack/module direction, simulator feature gate,
operator route stability.

Must not bundle: Site schema, simulator execution, ingestion, analytics, or
task-file creation.

User-review checkpoint: required for shell information hierarchy and the
enabled/disabled Simulator Lab surface because it fixes product direction and
UI/UX expectations.

### Early Feature: Site Foundation And Configuration-Only Site

Full architectural direction for this feature, including the port shape, module
tree, guard design, and Implementer guidance, is in
`.agent/M1-site-persistence-architecture.md`.

Divide into slices, in this order:
- `SiteRepository` port, domain records, port error vocabulary, read-only
  shipped-YAML adapter, single composition root, plus the canonical YAML
  Site/Foundation fixture and strict validation.
- Sites List and Site Details identity/configuration-only presentation resolved
  through the port.
- Read-only Site Configuration UI with Foundation version, validity, source
  mode, lifecycle, configuration origin, and explicit unavailable operational
  states.
- Shipped `SiteTemplate` catalog and template inspection, read-only, in its own
  identity space and visibly not a Site.
- Create Site from template: write adapter over the user store, identity and
  whole-document validation, cross-store collision refusal, atomic write, and
  origin/template provenance on the created Site.

The first slice may be split further if the port plus fixture plus validation is
too large to review at once, but the port must not be deferred past the first
slice that reads a Site, and the template slice must not be deferred past the
first slice that writes one.

Seams inside the feature: Site identity, YAML authority, configuration
persistence port, shipped versus user-authored configuration, user-authored
configuration input, configuration-only states, read-only configuration UI,
source mode versus lifecycle versus configuration origin versus source health.

Must not bundle: in-place configuration editing, Save/Publish over an existing
Foundation, rename, delete, configuration history or rollback, approvals,
template authoring or upload, arbitrary YAML import, simulator run setup, source
health, charts, analytics, Replay, or Findings.

Must not do: give the simulator a repository handle, gate any Site or template
route on `simulator_lab.enabled`, add `update`/`delete`/query-DSL/pagination to
the port before a slice needs them, or let the create path reach storage without
going through the port.

User-review checkpoint: required twice. First for Site/Foundation semantics and
configuration-only UI language, because they fix domain semantics. Second for
template-versus-instance semantics and the create flow's identity, origin, and
refusal language, because they fix what a user-authored Site means and what the
product does not promise about editing it.

### Early Feature: Topology, Devices, And SLD

Divide into slices:
- Topology/component/device/mapping validation from the Site Foundation.
- SLD view model using the hybrid mini-grid archetype.
- Site Configuration SLD and Devices & Sensors table from the same source.
- Runtime/evidence value slots without binding live values yet.

Seams inside the feature: SLD presentation boundary, canonical topology
authority, device-to-signal mapping, unsupported topology unavailable state.

Must not bundle: arbitrary graph auto-layout, drag/drop schematic editing,
runtime simulation, evidence overlays, or product health.

User-review checkpoint: required for SLD archetype, incompatible-topology UI,
and cold-room/electrical symbol treatment because they fix UI/UX and domain
representation.

### Early Feature: Scenario Catalog And Run Setup

Divide into slices:
- Scenario identity/version/detail view for Fuel Loss Event.
- Public event timeline/parameters and private expectation separation.
- Run setup selection of Site, scenario, interval, timestep, seed, duration,
  and speed defaults.

Seams inside the feature: scenario label not Site identity, public scenario
authoring versus private test oracle, deterministic run identity inputs.

Must not bundle: simulator execution, product conclusions, Commit, ingestion,
Finding creation, or in-product scenario editing persistence beyond the chosen
fixture/repository.

User-review checkpoint: required for event taxonomy, public/private scenario
parameters, and run setup language because they fix domain semantics and demo
narrative.

### Early Feature: Draft SimulationRun And Recorded Runtime

Divide into slices:
- Draft SimulationRun model/read model with lifecycle and execution status.
- Simulator Lab run header, controls, tabs, and disabled Draft product bridge.
- Recorded-run player through the runtime-facing clock/state/event interface.
- Runtime bindings to SLD/environment/devices/timeline.
- Non-persistent event injection that appends to intervention log semantics.

Seams inside the feature: simulator/product boundary, deterministic identity,
truth versus reported values, intervention causality, feature gate.

Must not bundle: full physical simulator replacement, accepted ingestion,
AssetOps conclusions, source health, or Findings.

User-review checkpoint: required for Simulator Lab control semantics, truth
visibility, and injection behavior because they fix UI/UX and simulator domain
semantics.

### Early Feature: Gateway Publication, Commit, And Ingestion

Divide into slices:
- Strict Source Envelope and first typed-record parsers/contracts.
- Staged gateway output UI for Draft runs.
- Commit eligibility and release manifest semantics, including overlap blocking.
- Ingestion Logs and accepted/rejected states from released envelopes.

Seams inside the feature: source-envelope crossing, envelope versus typed
evidence, Commit semantics, committed overlap, evidence immutability,
ingestion-assigned `received_at`.

Must not bundle: direct Site history writes from Commit, analytics, Replay,
findings, live protocol adapters, or replacement of committed history.

User-review checkpoint: required for envelope shape, Commit action language,
and accepted/rejected evidence interpretation because they fix architecture
and evidence semantics.

### Early Feature: AssetOps Evidence Views And Replay

Divide into slices:
- Site Details/Gateway/Events/Logs read models from accepted evidence only.
- Provenance summaries and Evidence/Provenance drawer.
- No-evidence/Limited/Unavailable states by Site + time window.
- Replay as as-of view over committed accepted history.
- Time-window consistency checks across tabs.

Seams inside the feature: accepted evidence only, provenance disclosure,
private truth isolation, source mode versus health, Replay versus Rerun.

Must not bundle: generator runtime, fuel reconciliation, findings,
recommendations, work/financial workflows, or simulator truth comparison in
operator UI.

User-review checkpoint: required for provenance placement, unavailable-state
language, and Replay behavior because they fix evidence interpretation and
operator UI semantics.

### Early Feature: First Product Conclusion Chain

Divide into slices:
- Gateway/source health from accepted evidence and expected cadence.
- Generator Runtime Assessment with evidence sufficiency and basis labels.
- Fuel Reconciliation with uncertainty and missing-record behavior.
- Promotion of one material unexplained fuel variance into a bounded Finding.
- Finding evidence drawer links and claim-boundary language.

Seams inside the feature: source-health derivation, conclusion order, evidence
availability suppressing claims, bounded fuel language, progressive provenance.

Must not bundle: theft/hidden-cause assertions, automatic incident or work
closure, financial roll-ups, recommendations without success criteria, or AI as
sole factual finding generator.

User-review checkpoint: required before fuel-reconciliation materiality and
Finding promotion because they fix product direction, evidence interpretation,
and operator consequence.

## Open Questions Before Task Breakdown

- Whether M1 needs any user-facing way to remove a user-created Site. This is a
  product call, not an architecture one. Delete is deliberately absent from the
  port because a later delete-then-recreate under the same `site_id` would
  resurrect orphaned committed simulated history under a different Foundation.
  Until the user decides, removing a user-created Site is a developer action on
  the store.
- Everything else in the M1 feature map is resolved and ready for task
  breakdown after user review.
