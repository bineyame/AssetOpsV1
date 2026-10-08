/**
 * Client for the gated run setup API.
 *
 * The client is created with its base paths rather than importing them, so
 * this module never spells a simulator URL: `tools/check-architecture.ps1`
 * allows that only in `simulatorLabRoutes.tsx`, which is where the paths live
 * and where this client is constructed.
 *
 * It reads the versioned profiles, it creates one Draft, and since T020 it lists
 * and reads the Drafts that exist. Since T022 it also STARTS one, steps it, runs
 * it to the end and reads where it got to.
 *
 * The absences that remain are the point, and they are still structural rather
 * than a convention: there is no pause, no commit, no stage, no release, no
 * ingest, no replay, no rerun, no reset, no event injection and no delete method
 * here, so no screen built on this client can offer one. A screen cannot call what
 * the client does not have, and the backend serves no such route either.
 *
 * ## The two outcomes are two shapes
 *
 * A refusal and a created Draft are different facts and they arrive
 * differently. `refused` carries the refusal kind and the backend's own copy,
 * and it means no run identity was allocated and nothing was written - there
 * is nothing to go and look at. `created` carries the persisted Draft,
 * whether it is `READY` or `BLOCKED`, because a blocked Draft exists and its
 * frozen inputs are the thing a reader inspects in order to decide what to
 * change.
 *
 * Collapsing them into one "it did not work" would lose exactly that.
 */

import {
  fetchRunHistory,
  fetchRunHistorySince,
  type RunHistoryDeltaResult,
  type RunHistoryResult,
} from "./runHistory";

/** One state a model profile can model, and in which execution roles. */
export interface RunSupportedState {
  state_key: string;
  /**
   * Whether this state is a fact about one component or about the whole
   * installation. `COMPONENT` or `SITE`, and never a component identity: a
   * profile says what kind of claim a state is, and which asset a run
   * resolves it on comes from the scenario and the site.
   */
  scope: string;
  supported_roles: string[];
  statement: string;
}

export interface RunModelProfile {
  model_profile_id: string;
  model_profile_version: number;
  display_name: string;
  statement: string;
  supported_states: RunSupportedState[];
}

/**
 * A versioned publication profile.
 *
 * Each of the three values it resolves may be `null`, and `null` is a real
 * answer rather than a gap: it means nobody has declared that input, which is
 * what blocks a run. Nothing in this client or in any screen built on it
 * supplies one.
 */
export interface RunPublicationProfile {
  publication_profile_id: string;
  publication_profile_version: number;
  display_name: string;
  statement: string;
  device_signal_cadence_minutes: number | null;
  simulator_source_id: string | null;
  gateway_id: string | null;
  /**
   * The reporting-path conditions this profile can model - whether a signal is
   * carrying readings, and the like. Same grain as a model profile's states: a
   * kind of claim, never a component identity. An empty list is a real answer
   * and is what blocks a scenario that requires one of them.
   */
  supported_reporting_states: RunSupportedState[];
  /**
   * S2-01b: the resolution each numeric signal's simulated device publishes
   * at, in the signal's source unit. Absent or empty: readings publish exactly.
   */
  device_resolutions?: RunDeviceResolution[];
  /** S2-01b: true when only a registered Site's Draft may select this profile. */
  requires_registered_site?: boolean;
}

/** S2-01b: one simulated device's declared publication resolution. */
export interface RunDeviceResolution {
  device_id: string;
  signal_id: string;
  unit: string;
  /** Exact positive decimal text, such as `0.000001`. */
  resolution: string;
}

/** One frozen value, and who answered for it. */
export interface RunFrozenInput {
  identity_field: string;
  field: string;
  value: string;
  answered_by: string;
  answered_by_detail: string;
  /**
   * Why this value has no answer, or `null` when it has one.
   *
   * The blocked run lists its reasons in their own table as well. This is
   * the one reason that explains THIS row, matched on the address the run
   * resolved, so a reader looking at two same-type assets sees which of the
   * two is unresolved and why without pairing the tables by eye.
   */
  blocking_statement: string | null;
}

/** Why a frozen Draft may not execute, and what the reason is about. */
export interface RunBlockingReason {
  kind: string;
  subject: string;
  statement: string;
}

export interface RunUnsupportedOptionalInput {
  state_key: string;
  execution_role: string;
  statement: string;
}

/**
 * The Site metadata a registered Draft froze at setup (S2-01a).
 *
 * Name, time zone and type are the Site's current record as read when the
 * Draft was created. They are not selected by the knowledge time: only the
 * Foundation and binding revisions are.
 */
export interface RunSiteMetadata {
  display_name: string;
  timezone: string;
  site_type: string;
  source: string;
}

/**
 * Which configuration a run was set up from (S2-01a).
 *
 * `LEGACY_FILE` for a run against a legacy Site document. `REGISTERED` for a
 * run against a registered Site: the exact revisions and snapshot hash it
 * froze. A registered basis is configuration, never accepted evidence.
 */
export type RunConfigurationBasis =
  | { store: "LEGACY_FILE" }
  | {
      store: "REGISTERED";
      selection: string;
      source_start: string;
      knowledge_at: string;
      foundation_revision_id: string;
      foundation_version: number;
      foundation_valid_from: string;
      foundation_valid_to: string | null;
      binding_set_revision_id: string;
      binding_set_version: number;
      binding_valid_from: string;
      binding_valid_to: string | null;
      snapshot_schema: string;
      snapshot_sha256: string;
      snapshot_byte_length: number;
      current_registration_gaps: string[];
      site_metadata: RunSiteMetadata;
      accepted_evidence: false;
    };

export interface RunSummary {
  run_id: string;
  lifecycle_status: string;
  execution_status: string;
  /**
   * What the execution status does not assert, or `null` when it asserts
   * nothing that needs qualifying.
   *
   * It arrives with the run rather than being written on a screen, because
   * it is a property of the status: a caller reading this over the wire gets
   * the same statement a person reading the screen does.
   */
  readiness_disclosure: string | null;
  created_at: string;
  site_id: string;
  /** The site's template lineage as run setup froze it (T025g AC9). */
  template_lineage: RunTemplateLineage;
  scenario_id: string;
  scenario_version: number;
  frozen_inputs: RunFrozenInput[];
  blocking_reasons: RunBlockingReason[];
  unsupported_optional_inputs: RunUnsupportedOptionalInput[];
  /**
   * Absent from a backend that predates S2-01a; the screen then says the
   * basis was not reported rather than guessing.
   */
  configuration_basis?: RunConfigurationBasis;
}

/**
 * The site's template lineage, frozen at run setup as provenance.
 *
 * `NOT_RECORDED` is a run stored before T025g froze lineage; it is never
 * inferred from the site today. `NO_TEMPLATE` is a site created from no
 * template.
 */
export interface RunTemplateLineage {
  state: "RECORDED" | "NO_TEMPLATE" | "NOT_RECORDED";
  template_id: string | null;
  template_version: number | null;
}

/** The lineage as a person reads it, the same words on every surface. */
export function templateLineageText(lineage: RunTemplateLineage): string {
  switch (lineage.state) {
    case "RECORDED":
      return `${lineage.template_id} v${lineage.template_version}`;
    case "NO_TEMPLATE":
      return "Not created from a template";
    default:
      return "Not recorded";
  }
}

function isTemplateLineage(value: unknown): value is RunTemplateLineage {
  if (!isRecord(value)) {
    return false;
  }
  if (value.state === "RECORDED") {
    return (
      typeof value.template_id === "string" &&
      typeof value.template_version === "number"
    );
  }
  return (
    (value.state === "NO_TEMPLATE" || value.state === "NOT_RECORDED") &&
    value.template_id === null &&
    value.template_version === null
  );
}

/** One value the run supplies because the scenario says the run owns it. */
export interface RunInputValue {
  parameter_id: string;
  value: number;
  unit: string;
}

export interface RunSetupInput {
  site_id: string;
  foundation_version: number;
  scenario_id: string;
  scenario_version: number;
  interval: { start_time: string; end_time: string };
  timestep_minutes: number;
  seed: number;
  model_profile: { profile_id: string; profile_version: number };
  publication_profile: { profile_id: string; profile_version: number };
  run_inputs: RunInputValue[];
}

/**
 * One row of the Runs inventory.
 *
 * There is no progress, no elapsed time, no health and no evidence state,
 * because nothing has produced any of them. A field for one would arrive as
 * a zero, and a zero is a measurement.
 */
export interface RunInventoryRow {
  run_id: string;
  lifecycle_status: string;
  execution_status: string;
  created_at: string;
  site_id: string;
  foundation_version: number;
  scenario_id: string;
  scenario_version: number;
  interval: {
    start_time: string;
    end_time: string;
    duration_minutes: number;
  };
  blocking_reason_count: number;
}

export type RunListResult =
  { status: "loaded"; runs: RunInventoryRow[] } | { status: "unavailable" };

export type RunDetailResult =
  | { status: "loaded"; run: RunSummary }
  | { status: "not_found" }
  | { status: "unavailable" };

export type RunProfilesResult =
  | {
      status: "loaded";
      modelProfiles: RunModelProfile[];
      publicationProfiles: RunPublicationProfile[];
    }
  | { status: "unavailable" };

export type CreateRunResult =
  | { status: "created"; run: RunSummary }
  /**
   * The Draft was created and persisted, and this client could not read the
   * summary that came back.
   *
   * A fourth member rather than `unavailable`, because the difference is the
   * only thing a reader needs: a run exists. Collapsing it would put "nothing
   * was written" on screen over a run that was, which is the worst sentence
   * this surface could say.
   */
  | { status: "created_but_unreadable" }
  | {
      status: "refused";
      code: string | null;
      refusalKind: string | null;
      /** The specific configuration reason, e.g. `BINDINGS_NOT_REGISTERED`. */
      reasonCode?: string | null;
      message: string;
    }
  /**
   * The request did not complete. `message` carries the backend's own copy
   * when it sent any - a store that could not be reached says so in product
   * words, and discarding them to show a generic sentence would be the
   * screen writing a second, worse version of the same fact.
   */
  | { status: "unavailable"; message: string | null };

/**
 * One world quantity at the instant a run has reached.
 *
 * `value` is a string and that is deliberate everywhere in this family. The
 * backend's numeric policy is exact rational arithmetic and it never rounds, so
 * the wire carries the exact decimal as text. Parsing it into a JavaScript
 * number here would reintroduce the one approximation the policy forbids, in the
 * layer furthest from anyone who could notice.
 */
export interface RunPrivateStateRow {
  address: string;
  state_key: string;
  value: string;
  canonical_unit: string;
  kind: string;
}

/**
 * One reporting path at one instant: what was true, and what was reported.
 *
 * The five things this screen exists to keep apart, each in its own field.
 * `true_value` is the world's, `reported_value` is the freshest reading at or
 * before this instant, `reported_source_time` is THAT reading's own time,
 * `quality` says whether it is fresh, retained or absent, and `outcome` says what
 * the sample attempt at this instant did - or is `null` when none was due.
 */
export interface RunObservationRow {
  address: string;
  state_key: string;
  device_id: string;
  signal_id: string;
  reading_class: string;
  at_offset_minutes: number;
  simulation_time: string;
  canonical_unit: string;
  true_value: string | null;
  reported_value: string | null;
  reported_source_time: string | null;
  reported_at_offset_minutes: number | null;
  quality: string;
  quality_statement: string;
  due: boolean;
  outcome: string | null;
  outcome_statement: string | null;
  suppression_reason: string | null;
  cadence_minutes: number;
  bias: string;
  dropout_per_thousand: number;
}

/** One configured reporting path, and everything the profile declares about it. */
export interface RunDeviceSignal {
  device_id: string;
  signal_id: string;
  address: string;
  state_key: string;
  reading_class: string;
  canonical_unit: string;
  cadence_minutes: number;
  bias: string;
  dropout_per_thousand: number;
  statement: string;
  /**
   * S2-01b: the frozen resolution this device publishes at, in the signal's
   * unit, or null when it publishes exactly. Absent on a run served before it.
   */
  resolution?: string | null;
}

/**
 * One span across which one signal's reporting path is forced unavailable.
 *
 * `timing_shape` is the shape the document declared and the two offsets are the
 * span it resolved to at this run's timestep. Both are carried because a reader
 * has to be able to see that a POINT condition covers one step rather than the
 * rest of the run - a collapse the first version of this made, by reading every
 * absent duration as the interval's end.
 */
export interface RunReportingGap {
  event_id: string;
  condition_address: string;
  device_id: string;
  signal_id: string;
  address: string;
  timing_shape: string;
  /** The instant the document declared, which for a POINT is not the
   * start of the outage: an entry at offset 1490 in a fifteen-minute run
   * silences the sample at 1485. Both are carried so a reader can see
   * what was written and what it came to. */
  declared_offset_minutes: number;
  start_offset_minutes: number;
  end_offset_minutes: number;
}

/** One sample attempt, as what it published or as why it did not. */
export interface RunRecentReport {
  device_id: string;
  signal_id: string;
  address: string;
  reading_class: string;
  at_offset_minutes: number;
  source_sample_time: string;
  outcome: string;
  outcome_statement: string;
  reported_value: string | null;
  canonical_unit: string;
  suppression_reason: string | null;
}

/** Why an execution stopped. Distinct from a refused control: this one ran. */
export interface RunExecutionFailure {
  kind: string;
  subject: string;
  statement: string;
  at_offset_minutes: number | null;
  detail: string[];
}

/**
 * One resolved step of the electrical world (T024), as mean powers in kW.
 *
 * Private truth for the gated Lab. `requested_battery_power` is what the
 * controller asked for and `battery_power` what the PCS accepted - positive
 * discharging, negative charging. Every quantity is exact text.
 */
export interface RunElectricalStep {
  from_offset: number;
  to_offset: number;
  simulation_time: string;
  soc_start: string;
  soc_end: string;
  reserve: string;
  reserve_origin: string;
  pv_potential: string;
  pv_output: string;
  curtailed: string;
  clipped: string;
  battery_power: string;
  requested_battery_power: string;
  limited_by: string[];
  demand: string;
  served: string;
  unserved: string;
}

export interface RunElectricalRule {
  rule_id: string;
  display_name: string;
  statement: string;
}

export interface RunElectricalViewEntry {
  name: string;
  address: string;
  value: string | null;
  unit: string;
}

export interface RunElectricalRequest {
  address: string;
  quantity: string;
  requested: string;
  unit: string;
  reason: string;
}

export interface RunElectricalControl {
  address: string;
  quantity: string;
  requested: string;
  accepted: string;
  unit: string;
  limited_by: string[];
}

export interface RunElectricalLoad {
  address: string;
  priority_rank: number;
  demand_power: string;
  served_power: string;
  unserved_power: string;
  demand_energy: string;
  served_energy: string;
  unserved_energy: string;
}

export interface RunElectricalFlow {
  flow_id: string;
  from_address: string;
  to_address: string;
  energy: string;
  mean_power: string;
}

export interface RunElectricalEffectiveControl {
  address: string;
  from_offset: number;
  to_offset: number;
  value: string;
  unit: string;
  origin: string;
  provenance: string;
}

/**
 * The electrical world of one execution: every step so far, and the latest
 * step's view, request, acceptance, loads, flows and reserve in effect - kept
 * as separate collections because the execution contract keeps them apart.
 */
export interface RunElectrical {
  battery_address: string;
  coupling_rules: RunElectricalRule[];
  steps: RunElectricalStep[];
  latest_view: RunElectricalViewEntry[];
  latest_requests: RunElectricalRequest[];
  latest_controls: RunElectricalControl[];
  latest_loads: RunElectricalLoad[];
  latest_flows: RunElectricalFlow[];
  latest_effective_controls: RunElectricalEffectiveControl[];
  latest_balances: string[];
  latest_segments: number[][];
  notes: string[];
  /** T025a: the generator of a `mini-grid` run; absent or `null` otherwise. */
  generator?: RunGenerator | null;
}

/**
 * One resolved generator step (T025a). Four things the contract keeps apart:
 * the physical state at T, the state over the step, the controller's request
 * and the accepted output (kW), plus fuel in litres.
 */
export interface RunGeneratorStep {
  from_offset: number;
  to_offset: number;
  simulation_time: string;
  state_at_t: string;
  state_for_step: string;
  requested: string;
  request_reason: string;
  output: string;
  to_load: string;
  to_battery: string;
  fuel_start: string;
  fuel_end: string;
  limited_by: string[];
  /**
   * T025b: the newest generator status reading at or before T - a lifecycle
   * member - and its quality. It is a READING beside the physical state, never
   * a replacement for it: at a 15-minute status cadence the steps between
   * samples show a STALE member while the world has moved on. The state is
   * `null` with quality UNAVAILABLE before any reading arrived, and both are
   * `null` when the run's publication profile publishes no status (every
   * profile-3 run).
   */
  reported_state: string | null;
  reported_quality: string | null;
}

/** One lifecycle transition, with its phase, cause and instant. */
export interface RunGeneratorTransition {
  address: string;
  previous: string;
  next: string;
  phase: string;
  cause: string;
  controller_ref: string | null;
  at_offset_minutes: number;
  simulation_time: string;
}

export interface RunGenerator {
  state_address: string;
  fuel_address: string;
  reported_status: string;
  discrete_state_rules: RunElectricalRule[];
  steps: RunGeneratorStep[];
  transitions: RunGeneratorTransition[];
}

/**
 * Where one Draft's execution is, and what it has produced.
 *
 * `status` is one of `NOT_STARTED`, `RUNNING`, `COMPLETED`, `FAILED` and
 * `INTERRUPTED`, and `statement` is the backend's own sentence for it. The screen
 * places that sentence rather than writing a second one, for the same reason it
 * places the readiness disclosure.
 *
 * `content_digest` is `null` until the run reaches a terminal outcome, because a
 * digest over a prefix would be an identity for something that is not yet a
 * thing. `observation_series_digest` is always present and is a second identity
 * on purpose: the world's identity excludes the reporting path, so one digest
 * could not tell two runs whose reports differ apart.
 */
export interface RunExecution {
  run_id: string;
  status: string;
  statement: string;
  boundaries_completed: number;
  boundaries_total: number;
  offset_minutes: number;
  simulation_time: string;
  interval_start_time: string;
  interval_end_time: string;
  timestep_minutes: number;
  seed: number;
  kernel_version: number;
  model_profile_id: string;
  model_profile_version: number;
  publication_profile_id: string;
  publication_profile_version: number;
  numeric_policy: string;
  numeric_policy_version: number;
  execution_contract_version: number;
  inputs_identity: string;
  content_digest: string | null;
  observation_series_digest: string;
  reported_count: number;
  suppressed_by_gap_count: number;
  dropped_count: number;
  notes: string[];
  failure: RunExecutionFailure | null;
  private_state: RunPrivateStateRow[];
  observations: RunObservationRow[];
  signals: RunDeviceSignal[];
  reporting_gaps: RunReportingGap[];
  recent_reports: RunRecentReport[];
  /** T024: the electrical world, or `null` for a model with no controller. */
  electrical: RunElectrical | null;
}

/**
 * The outcome of one execution read or one control request.
 *
 * `refused` and `unavailable` are kept apart for the reason `createRun`'s are: a
 * refusal means the request was judged and NOTHING was advanced, and the backend
 * says which of the eight refusals it was and why. `unavailable` means the
 * request did not complete, so nothing is known about whether it applied.
 */
export type RunExecutionResult =
  | { status: "loaded"; execution: RunExecution }
  | { status: "not_found" }
  | {
      status: "refused";
      code: string | null;
      refusalKind: string | null;
      message: string;
    }
  | { status: "unavailable"; message: string | null };

/**
 * One staged canonical source envelope, as the gated inspector receives it.
 *
 * `canonical` is the exact persisted text of the envelope - the bytes a later
 * ingestion will parse - and every other field is that same envelope's metadata
 * split out so a screen can put source time and publication time in separate
 * cells without parsing JSON. `value` is exact decimal text, never a number.
 */
export interface RunStagedEnvelope {
  canonical: string;
  message_id: string;
  sequence: number;
  device_id: string;
  signal_id: string;
  mapping_set_id: string;
  mapping_version: number;
  schema_version: number;
  source_time: string;
  published_at: string;
  measurement: string;
  value: string | null;
  unit: string;
  quality: string;
  unavailable_reason: string | null;
  interval_start: string | null;
  interval_end: string | null;
  /**
   * T026: `MEASUREMENT`, `POLICY` or `OPERATIONAL_RECORD`. A record has no
   * measurement class and no quality; the API puts its family in the
   * `measurement` column and `RECORDED` in `quality`, and a screen reads this
   * field rather than those. Absent on a stage served before T026.
   */
  family?: string;
}

/** One allowlisted signal in the mapping a stage froze. */
export interface RunStageMappingEntry {
  device_id: string;
  signal_id: string;
  measurement: string;
  unit: string;
  publishes_unavailable: boolean;
  /** T026: as on an envelope; absent on a stage served before T026. */
  family?: string;
  /** T026: an enum signal's declared members; null for a number or record. */
  members?: string[] | null;
}

export interface RunStageMapping {
  mapping_set_id: string;
  mapping_version: number;
  publication_latency_seconds: number;
  entries: RunStageMappingEntry[];
}

/**
 * One Draft's staged source envelopes, re-read from persistence and verified.
 *
 * `status` is `NOT_STAGED`, `STAGED` or `STAGE_UNREADABLE`; `statement` is the
 * backend's sentence for it. `release_eligible` is the condition Commit
 * requires (T027); the stage itself releases nothing, and whether this Draft
 * was committed and what ingestion accepted is `getCommit`'s answer, not the
 * stage's.
 */
export interface RunStage {
  run_id: string;
  status: string;
  statement: string;
  execution_status: string;
  release_eligible: boolean;
  release_blockers: { kind: string; statement: string }[];
  unreadable_detail: string | null;
  envelope_schema_id: string;
  envelope_schema_version: number;
  stage_schema_version: number;
  integrity_digest: string | null;
  /** How many of its run's boundaries the stage records as published. */
  boundaries_total: number | null;
  published_through: number | null;
  site_id: string | null;
  source_id: string | null;
  gateway_id: string | null;
  mapping: RunStageMapping | null;
  refused_publications: { message_id: string; kind: string }[];
  envelopes: RunStagedEnvelope[];
}

/** What the Stage read says about the configuration the Draft froze. */
export interface RunStageFrozenBasis {
  configuration_store: string;
  site_imported: boolean | null;
  can_release: boolean;
  statement: string;
  registered_basis?: RunConfigurationBasis;
}

/** S2-01b: one SourceEnvelope V3 row in the gateway's local outbox. */
export interface GatewayLedgerEnvelope {
  message_id: string;
  source_id: string;
  sequence_epoch: string;
  sequence: number;
  source_time: string;
  snapshot_sha256: string;
  /** The exact stored envelope text. */
  canonical: string;
  sha256: string;
  state: string;
  batch_id: string | null;
  ordinal: number | null;
}

/** S2-01b: one sealed, immutable Batch V2 in the gateway's local outbox. */
export interface GatewayLedgerBatch {
  batch_id: string;
  source_id: string;
  sequence_epoch: string;
  snapshot_sha256: string;
  /** The exact stored batch text. */
  canonical: string;
  sha256: string;
  state: string;
  attempt_count: number;
  message_ids: string[];
}

/** S2-01b: a report the gateway refused to sequence, with the field and why. */
export interface GatewayLedgerHold {
  hold_id: number;
  kind: string;
  field: string;
  detail: string;
  device_id: string | null;
  signal_id: string | null;
  source_time: string | null;
  seen_count: number;
}

/**
 * S2-01b: a registered run's Stage, read from the separate gateway process's
 * durable SQLite ledger. Upload is always pending in this build and
 * `receipts` is always empty; nothing here is accepted evidence.
 */
export interface GatewayLedgerStage {
  store: "GATEWAY_LEDGER";
  run_id: string;
  /** `STAGED`, `NOT_STAGED` or `GATEWAY_UNAVAILABLE`. */
  status: string;
  statement: string;
  execution_status: string;
  release_eligible: false;
  snapshot_sha256: string;
  site_id: string | null;
  gateway_id: string | null;
  sequence_epoch: string | null;
  upload_state: "PENDING";
  upload_statement: string;
  receipts: [];
  unavailable_detail: string | null;
  publication_notes: string[];
  queue_depth_by_state: Record<string, number>;
  envelopes: GatewayLedgerEnvelope[];
  batches: GatewayLedgerBatch[];
  holds: GatewayLedgerHold[];
}

export type RunStageResult =
  | {
      status: "loaded";
      stage: RunStage;
      /** Absent: not reported. Null: reported and unreadable. */
      frozenBasis?: RunStageFrozenBasis | null;
    }
  | {
      /** S2-01b: a registered run, whose Stage is the gateway ledger. */
      status: "gateway";
      stage: GatewayLedgerStage;
      frozenBasis?: RunStageFrozenBasis | null;
    }
  | { status: "not_found" }
  | { status: "unavailable"; message: string | null };

/**
 * One ingestion batch as ingestion reports it (T027). `status` is
 * `IN_PROGRESS`, `COMPLETED` or `REFUSED`; the counts are ingestion's, never
 * inferred from the stage, so `accepted` may be less than `total`.
 */
export interface ReleaseBatch {
  batch_id: string;
  site_id: string;
  source_id: string;
  gateway_id: string;
  source_mode: string;
  status: string;
  total: number;
  processed: number;
  accepted: number;
  duplicates: number;
  rejected: number;
  conflicts: number;
  refusal: { kind: string; detail: string } | null;
  started_at: string;
  completed_at: string | null;
  window_start: string | null;
  window_end: string | null;
}

/** The sealed artifact a Commit filed for this Draft. */
export interface CommitSummary {
  artifact_id: string;
  integrity_digest: string;
  envelope_count: number;
  sealed_at: string;
  run_id: string;
  site_id: string;
}

/** Where a release's accepted content can be read, by the operator route. */
export interface OpenInAssetOps {
  site_id: string;
  window_start: string;
  window_end: string;
  batch_id: string;
  href: string;
}

/**
 * Whether this Draft is committed and, separately, what ingestion did with it.
 * `release_error` is set only on a Commit answer whose release was interrupted.
 */
export interface RunCommit {
  commit: "NOT_COMMITTED" | CommitSummary;
  release: ReleaseBatch | null;
  open_in_assetops: OpenInAssetOps | null;
  release_error: string | null;
}

export type RunCommitResult =
  | { status: "loaded"; commit: RunCommit }
  | { status: "not_found" }
  | {
      status: "refused";
      code: string | null;
      message: string;
      releaseBlockers: { kind: string; statement: string }[];
    }
  | { status: "unavailable"; message: string | null };

/** What a step request says: how far, and from where it believes the run is. */
export interface RunStepRequest {
  boundaries: number;
  fromBoundary: number;
}

export interface RunSetupClient {
  listProfiles(): Promise<RunProfilesResult>;
  createRun(input: RunSetupInput): Promise<CreateRunResult>;
  listRuns(): Promise<RunListResult>;
  getRun(runId: string): Promise<RunDetailResult>;
  /**
   * Where this Draft's execution is. A read: it changes nothing, and a Draft
   * nothing has executed is a `loaded` `NOT_STARTED` rather than an error.
   */
  getExecution(runId: string): Promise<RunExecutionResult>;
  startExecution(runId: string): Promise<RunExecutionResult>;
  /**
   * Advance a started execution.
   *
   * `fromBoundary` is what makes the control safe to resubmit: it is the position
   * the caller believes the run is at, which the projection it is looking at
   * already told it. A double click sends the same number twice and the second
   * request advances nothing.
   */
  stepExecution(
    runId: string,
    request: RunStepRequest,
  ): Promise<RunExecutionResult>;
  runExecutionToEnd(runId: string): Promise<RunExecutionResult>;
  /**
   * This Draft's staged source envelopes. A read: there is no client method
   * that edits a stage. Releasing one is `commit`, which seals it first.
   */
  getStage(runId: string): Promise<RunStageResult>;
  /** Whether this Draft is committed and what ingestion did. A read (T027). */
  getCommit(runId: string): Promise<RunCommitResult>;
  /**
   * Seal this Draft's eligible stage once and release it through ingestion.
   * Posting again after an interrupted release resumes the same batch.
   */
  commit(runId: string): Promise<RunCommitResult>;
  /**
   * What this Draft's execution recorded (T025c). A read that executes
   * nothing: a run with no recorded history is a `loaded` history saying why.
   */
  getExecutionHistory(runId: string): Promise<RunHistoryResult>;
  /**
   * What this Draft's execution recorded after the first `sinceBoundary`
   * boundaries (T025e live follow): a delta for `appendHistory`, never a
   * history to render alone. A read that executes nothing.
   */
  getExecutionHistorySince(
    runId: string,
    sinceBoundary: number,
  ): Promise<RunHistoryDeltaResult>;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object";
}

function isNullableNumber(value: unknown): boolean {
  return value === null || typeof value === "number";
}

function isNullableString(value: unknown): boolean {
  return value === null || typeof value === "string";
}

function isSupportedState(value: unknown): value is RunSupportedState {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.state_key === "string" &&
    typeof value.scope === "string" &&
    Array.isArray(value.supported_roles) &&
    value.supported_roles.every((role) => typeof role === "string") &&
    typeof value.statement === "string"
  );
}

function isModelProfile(value: unknown): value is RunModelProfile {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.model_profile_id === "string" &&
    typeof value.model_profile_version === "number" &&
    typeof value.display_name === "string" &&
    typeof value.statement === "string" &&
    Array.isArray(value.supported_states) &&
    value.supported_states.every(isSupportedState)
  );
}

function isPublicationProfile(value: unknown): value is RunPublicationProfile {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.publication_profile_id === "string" &&
    typeof value.publication_profile_version === "number" &&
    typeof value.display_name === "string" &&
    typeof value.statement === "string" &&
    isNullableNumber(value.device_signal_cadence_minutes) &&
    isNullableString(value.simulator_source_id) &&
    isNullableString(value.gateway_id) &&
    Array.isArray(value.supported_reporting_states) &&
    value.supported_reporting_states.every(isSupportedState) &&
    (value.device_resolutions === undefined ||
      (Array.isArray(value.device_resolutions) &&
        value.device_resolutions.every(isDeviceResolution))) &&
    (value.requires_registered_site === undefined ||
      typeof value.requires_registered_site === "boolean")
  );
}

/** Exact positive decimal text: never a float exponent or a ratio. */
const EXACT_DECIMAL = /^(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$/;

function isDeviceResolution(value: unknown): value is RunDeviceResolution {
  return (
    isRecord(value) &&
    typeof value.device_id === "string" &&
    typeof value.signal_id === "string" &&
    typeof value.unit === "string" &&
    typeof value.resolution === "string" &&
    EXACT_DECIMAL.test(value.resolution)
  );
}

function isFrozenInput(value: unknown): value is RunFrozenInput {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.identity_field === "string" &&
    typeof value.field === "string" &&
    typeof value.value === "string" &&
    typeof value.answered_by === "string" &&
    typeof value.answered_by_detail === "string" &&
    isNullableString(value.blocking_statement)
  );
}

function isBlockingReason(value: unknown): value is RunBlockingReason {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.kind === "string" &&
    typeof value.subject === "string" &&
    typeof value.statement === "string"
  );
}

function isUnsupportedOptional(
  value: unknown,
): value is RunUnsupportedOptionalInput {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.state_key === "string" &&
    typeof value.execution_role === "string" &&
    typeof value.statement === "string"
  );
}

function isInventoryRow(value: unknown): value is RunInventoryRow {
  if (!isRecord(value)) {
    return false;
  }
  const interval = value.interval;
  return (
    typeof value.run_id === "string" &&
    typeof value.lifecycle_status === "string" &&
    typeof value.execution_status === "string" &&
    typeof value.created_at === "string" &&
    typeof value.site_id === "string" &&
    typeof value.foundation_version === "number" &&
    typeof value.scenario_id === "string" &&
    typeof value.scenario_version === "number" &&
    isRecord(interval) &&
    typeof interval.start_time === "string" &&
    typeof interval.end_time === "string" &&
    typeof interval.duration_minutes === "number" &&
    typeof value.blocking_reason_count === "number"
  );
}

export function isRunSummary(value: unknown): value is RunSummary {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.run_id === "string" &&
    typeof value.lifecycle_status === "string" &&
    typeof value.execution_status === "string" &&
    isNullableString(value.readiness_disclosure) &&
    typeof value.created_at === "string" &&
    typeof value.site_id === "string" &&
    isTemplateLineage(value.template_lineage) &&
    typeof value.scenario_id === "string" &&
    typeof value.scenario_version === "number" &&
    Array.isArray(value.frozen_inputs) &&
    value.frozen_inputs.every(isFrozenInput) &&
    Array.isArray(value.blocking_reasons) &&
    value.blocking_reasons.every(isBlockingReason) &&
    Array.isArray(value.unsupported_optional_inputs) &&
    value.unsupported_optional_inputs.every(isUnsupportedOptional) &&
    (value.configuration_basis === undefined ||
      isRunConfigurationBasis(value.configuration_basis))
  );
}

function isSiteMetadata(value: unknown): value is RunSiteMetadata {
  return (
    isRecord(value) &&
    typeof value.display_name === "string" &&
    typeof value.timezone === "string" &&
    typeof value.site_type === "string" &&
    typeof value.source === "string"
  );
}

/** A whole configuration basis; half of one is not rendered. */
export function isRunConfigurationBasis(
  value: unknown,
): value is RunConfigurationBasis {
  if (!isRecord(value)) {
    return false;
  }
  if (value.store === "LEGACY_FILE") {
    return true;
  }
  return (
    value.store === "REGISTERED" &&
    typeof value.selection === "string" &&
    typeof value.source_start === "string" &&
    typeof value.knowledge_at === "string" &&
    typeof value.foundation_revision_id === "string" &&
    typeof value.foundation_version === "number" &&
    typeof value.foundation_valid_from === "string" &&
    isNullableString(value.foundation_valid_to) &&
    typeof value.binding_set_revision_id === "string" &&
    typeof value.binding_set_version === "number" &&
    typeof value.binding_valid_from === "string" &&
    isNullableString(value.binding_valid_to) &&
    typeof value.snapshot_schema === "string" &&
    typeof value.snapshot_sha256 === "string" &&
    typeof value.snapshot_byte_length === "number" &&
    isStringArray(value.current_registration_gaps) &&
    isSiteMetadata(value.site_metadata) &&
    value.accepted_evidence === false
  );
}

/**
 * The Stage read's frozen basis: `undefined` when the backend reported none
 * (it predates S1-01), `null` when it reported one this client cannot read.
 */
function readFrozenBasis(value: unknown): RunStageFrozenBasis | null | undefined {
  if (value === undefined) {
    return undefined;
  }
  if (
    !isRecord(value) ||
    typeof value.configuration_store !== "string" ||
    !(value.site_imported === null || typeof value.site_imported === "boolean") ||
    typeof value.can_release !== "boolean" ||
    typeof value.statement !== "string" ||
    (value.registered_basis !== undefined &&
      !isRunConfigurationBasis(value.registered_basis))
  ) {
    return null;
  }
  return value as unknown as RunStageFrozenBasis;
}

function isStringArray(value: unknown): boolean {
  return (
    Array.isArray(value) && value.every((item) => typeof item === "string")
  );
}

function isPrivateStateRow(value: unknown): value is RunPrivateStateRow {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.address === "string" &&
    typeof value.state_key === "string" &&
    typeof value.value === "string" &&
    typeof value.canonical_unit === "string" &&
    typeof value.kind === "string"
  );
}

/**
 * T025b: a reading in unit `state` carries a member's text (`"RUNNING"`), never
 * a decimal, and a discrete signal has no numeric error. A decimal arriving
 * here would be a status disguised as a number - the thing the envelope
 * refuses - so the screen refuses it too rather than showing it.
 */
function isNullableMemberText(value: unknown): boolean {
  return (
    value === null ||
    value === undefined ||
    (typeof value === "string" && /^[A-Z][A-Z_]*$/.test(value))
  );
}

function isDiscreteReadingSound(value: Record<string, unknown>): boolean {
  return (
    value.canonical_unit !== "state" ||
    (isNullableMemberText(value.true_value) &&
      isNullableMemberText(value.reported_value) &&
      (value.bias === undefined || value.bias === "0"))
  );
}

function isObservationRow(value: unknown): value is RunObservationRow {
  if (!isRecord(value)) {
    return false;
  }
  return (
    isDiscreteReadingSound(value) &&
    typeof value.address === "string" &&
    typeof value.state_key === "string" &&
    typeof value.device_id === "string" &&
    typeof value.signal_id === "string" &&
    typeof value.reading_class === "string" &&
    typeof value.at_offset_minutes === "number" &&
    typeof value.simulation_time === "string" &&
    typeof value.canonical_unit === "string" &&
    isNullableString(value.true_value) &&
    isNullableString(value.reported_value) &&
    isNullableString(value.reported_source_time) &&
    isNullableNumber(value.reported_at_offset_minutes) &&
    typeof value.quality === "string" &&
    typeof value.quality_statement === "string" &&
    typeof value.due === "boolean" &&
    isNullableString(value.outcome) &&
    isNullableString(value.outcome_statement) &&
    isNullableString(value.suppression_reason) &&
    typeof value.cadence_minutes === "number" &&
    typeof value.bias === "string" &&
    typeof value.dropout_per_thousand === "number"
  );
}

function isDeviceSignal(value: unknown): value is RunDeviceSignal {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.device_id === "string" &&
    typeof value.signal_id === "string" &&
    typeof value.address === "string" &&
    typeof value.state_key === "string" &&
    typeof value.reading_class === "string" &&
    typeof value.canonical_unit === "string" &&
    typeof value.cadence_minutes === "number" &&
    typeof value.bias === "string" &&
    typeof value.dropout_per_thousand === "number" &&
    typeof value.statement === "string" &&
    (value.resolution === undefined ||
      value.resolution === null ||
      (typeof value.resolution === "string" && EXACT_DECIMAL.test(value.resolution))) &&
    isDiscreteReadingSound(value)
  );
}

function isReportingGap(value: unknown): value is RunReportingGap {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.event_id === "string" &&
    typeof value.condition_address === "string" &&
    typeof value.device_id === "string" &&
    typeof value.signal_id === "string" &&
    typeof value.address === "string" &&
    typeof value.timing_shape === "string" &&
    typeof value.declared_offset_minutes === "number" &&
    typeof value.start_offset_minutes === "number" &&
    typeof value.end_offset_minutes === "number"
  );
}

function isRecentReport(value: unknown): value is RunRecentReport {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.device_id === "string" &&
    typeof value.signal_id === "string" &&
    typeof value.address === "string" &&
    typeof value.reading_class === "string" &&
    typeof value.at_offset_minutes === "number" &&
    typeof value.source_sample_time === "string" &&
    typeof value.outcome === "string" &&
    typeof value.outcome_statement === "string" &&
    isNullableString(value.reported_value) &&
    typeof value.canonical_unit === "string" &&
    isNullableString(value.suppression_reason) &&
    isDiscreteReadingSound(value)
  );
}

function isExecutionFailure(value: unknown): value is RunExecutionFailure {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.kind === "string" &&
    typeof value.subject === "string" &&
    typeof value.statement === "string" &&
    isNullableNumber(value.at_offset_minutes) &&
    isStringArray(value.detail)
  );
}

function hasStrings(value: Record<string, unknown>, keys: string[]): boolean {
  return keys.every((key) => typeof value[key] === "string");
}

function isElectricalStep(value: unknown): value is RunElectricalStep {
  return (
    isRecord(value) &&
    typeof value.from_offset === "number" &&
    typeof value.to_offset === "number" &&
    hasStrings(value, [
      "simulation_time",
      "soc_start",
      "soc_end",
      "reserve",
      "reserve_origin",
      "pv_potential",
      "pv_output",
      "curtailed",
      "clipped",
      "battery_power",
      "requested_battery_power",
      "demand",
      "served",
      "unserved",
    ]) &&
    isStringArray(value.limited_by)
  );
}

function everyRecord(
  value: unknown,
  check: (item: Record<string, unknown>) => boolean,
): boolean {
  return (
    Array.isArray(value) && value.every((item) => isRecord(item) && check(item))
  );
}

/**
 * The electrical world, checked whole. `null` is the answer for a model with
 * no controller - the fuel model - and for a run nothing has executed.
 */
export function isRunElectrical(value: unknown): value is RunElectrical {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.battery_address === "string" &&
    everyRecord(value.coupling_rules, (item) =>
      hasStrings(item, ["rule_id", "display_name", "statement"]),
    ) &&
    Array.isArray(value.steps) &&
    value.steps.every(isElectricalStep) &&
    everyRecord(
      value.latest_view,
      (item) =>
        hasStrings(item, ["name", "address", "unit"]) &&
        isNullableString(item.value),
    ) &&
    everyRecord(value.latest_requests, (item) =>
      hasStrings(item, ["address", "quantity", "requested", "unit", "reason"]),
    ) &&
    everyRecord(
      value.latest_controls,
      (item) =>
        hasStrings(item, [
          "address",
          "quantity",
          "requested",
          "accepted",
          "unit",
        ]) && isStringArray(item.limited_by),
    ) &&
    everyRecord(
      value.latest_loads,
      (item) =>
        typeof item.priority_rank === "number" &&
        hasStrings(item, [
          "address",
          "demand_power",
          "served_power",
          "unserved_power",
          "demand_energy",
          "served_energy",
          "unserved_energy",
        ]),
    ) &&
    everyRecord(value.latest_flows, (item) =>
      hasStrings(item, [
        "flow_id",
        "from_address",
        "to_address",
        "energy",
        "mean_power",
      ]),
    ) &&
    everyRecord(
      value.latest_effective_controls,
      (item) =>
        typeof item.from_offset === "number" &&
        typeof item.to_offset === "number" &&
        hasStrings(item, ["address", "value", "unit", "origin", "provenance"]),
    ) &&
    isStringArray(value.latest_balances) &&
    Array.isArray(value.latest_segments) &&
    value.latest_segments.every(
      (item) =>
        Array.isArray(item) &&
        item.length === 2 &&
        item.every((part) => typeof part === "number"),
    ) &&
    isStringArray(value.notes) &&
    (value.generator === undefined ||
      value.generator === null ||
      isRunGenerator(value.generator))
  );
}

/** T025a: the declared lifecycle members and the request vocabulary. */
const GENERATOR_STATES: readonly string[] = [
  "STOPPED",
  "STARTING",
  "RUNNING",
  "FAILED",
];
const GENERATOR_REQUESTS: readonly string[] = ["RUN", "STOP"];
/** T025b: the reading qualities a reported generator status can carry. */
const REPORTED_QUALITIES: readonly string[] = ["GOOD", "STALE", "UNAVAILABLE"];

function isNullableMember(value: unknown, allowed: readonly string[]): boolean {
  return value === null || isMember(value, allowed);
}

function isMember(value: unknown, allowed: readonly string[]): boolean {
  return typeof value === "string" && allowed.includes(value);
}

/** T025a: the generator section, checked whole. */
export function isRunGenerator(value: unknown): value is RunGenerator {
  if (!isRecord(value)) {
    return false;
  }
  return (
    hasStrings(value, ["state_address", "fuel_address", "reported_status"]) &&
    everyRecord(value.discrete_state_rules, (item) =>
      hasStrings(item, ["rule_id", "display_name", "statement"]),
    ) &&
    everyRecord(
      value.steps,
      (item) =>
        typeof item.from_offset === "number" &&
        typeof item.to_offset === "number" &&
        hasStrings(item, [
          "simulation_time",
          "request_reason",
          "output",
          "to_load",
          "to_battery",
          "fuel_start",
          "fuel_end",
        ]) &&
        isMember(item.state_at_t, GENERATOR_STATES) &&
        isMember(item.state_for_step, GENERATOR_STATES) &&
        isMember(item.requested, GENERATOR_REQUESTS) &&
        isStringArray(item.limited_by) &&
        isNullableMember(item.reported_state, GENERATOR_STATES) &&
        isNullableMember(item.reported_quality, REPORTED_QUALITIES) &&
        // A member needs a quality; an UNAVAILABLE quality may carry none.
        (item.reported_state === null || item.reported_quality !== null),
    ) &&
    everyRecord(
      value.transitions,
      (item) =>
        typeof item.at_offset_minutes === "number" &&
        hasStrings(item, ["address", "phase", "cause", "simulation_time"]) &&
        isMember(item.previous, GENERATOR_STATES) &&
        isMember(item.next, GENERATOR_STATES) &&
        isNullableString(item.controller_ref),
    )
  );
}

/**
 * Whether a body is a whole execution projection.
 *
 * Checked field by field, like every other shape here, and for the reason the
 * module docstring gives: a screen must not render half an execution. Half of
 * this one would be worse than half a frozen identity - a true value with no
 * reported value beside it reads as a reading that did not happen.
 */
export function isRunExecution(value: unknown): value is RunExecution {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.run_id === "string" &&
    typeof value.status === "string" &&
    typeof value.statement === "string" &&
    typeof value.boundaries_completed === "number" &&
    typeof value.boundaries_total === "number" &&
    typeof value.offset_minutes === "number" &&
    typeof value.simulation_time === "string" &&
    typeof value.interval_start_time === "string" &&
    typeof value.interval_end_time === "string" &&
    typeof value.timestep_minutes === "number" &&
    typeof value.seed === "number" &&
    typeof value.kernel_version === "number" &&
    typeof value.model_profile_id === "string" &&
    typeof value.model_profile_version === "number" &&
    typeof value.publication_profile_id === "string" &&
    typeof value.publication_profile_version === "number" &&
    typeof value.numeric_policy === "string" &&
    typeof value.numeric_policy_version === "number" &&
    typeof value.execution_contract_version === "number" &&
    typeof value.inputs_identity === "string" &&
    isNullableString(value.content_digest) &&
    typeof value.observation_series_digest === "string" &&
    typeof value.reported_count === "number" &&
    typeof value.suppressed_by_gap_count === "number" &&
    typeof value.dropped_count === "number" &&
    isStringArray(value.notes) &&
    (value.failure === null || isExecutionFailure(value.failure)) &&
    Array.isArray(value.private_state) &&
    value.private_state.every(isPrivateStateRow) &&
    Array.isArray(value.observations) &&
    value.observations.every(isObservationRow) &&
    Array.isArray(value.signals) &&
    value.signals.every(isDeviceSignal) &&
    Array.isArray(value.reporting_gaps) &&
    value.reporting_gaps.every(isReportingGap) &&
    Array.isArray(value.recent_reports) &&
    value.recent_reports.every(isRecentReport) &&
    (value.electrical === null || isRunElectrical(value.electrical))
  );
}

function isStagedEnvelope(value: unknown): value is RunStagedEnvelope {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.canonical === "string" &&
    typeof value.message_id === "string" &&
    typeof value.sequence === "number" &&
    typeof value.device_id === "string" &&
    typeof value.signal_id === "string" &&
    typeof value.mapping_set_id === "string" &&
    typeof value.mapping_version === "number" &&
    typeof value.schema_version === "number" &&
    typeof value.source_time === "string" &&
    typeof value.published_at === "string" &&
    typeof value.measurement === "string" &&
    isNullableString(value.value) &&
    typeof value.unit === "string" &&
    typeof value.quality === "string" &&
    isNullableString(value.unavailable_reason) &&
    isNullableString(value.interval_start) &&
    isNullableString(value.interval_end) &&
    (value.family === undefined || typeof value.family === "string")
  );
}

function isStageMapping(value: unknown): value is RunStageMapping {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.mapping_set_id === "string" &&
    typeof value.mapping_version === "number" &&
    typeof value.publication_latency_seconds === "number" &&
    Array.isArray(value.entries) &&
    value.entries.every(
      (entry) =>
        isRecord(entry) &&
        typeof entry.device_id === "string" &&
        typeof entry.signal_id === "string" &&
        typeof entry.measurement === "string" &&
        typeof entry.unit === "string" &&
        typeof entry.publishes_unavailable === "boolean" &&
        (entry.family === undefined || typeof entry.family === "string") &&
        (entry.members === undefined ||
          entry.members === null ||
          (Array.isArray(entry.members) &&
            entry.members.every((member) => typeof member === "string"))),
    )
  );
}

const SHA256_HEX = /^[0-9a-f]{64}$/;

/**
 * S2-01b: whether a body is a whole gateway-ledger Stage. Anything short of
 * one - a receipt, an upload state other than pending, a release-eligible
 * flag - is not rendered as one, so the screen never shows a delivery claim.
 */
export function isGatewayLedgerStage(value: unknown): value is GatewayLedgerStage {
  if (!isRecord(value) || value.store !== "GATEWAY_LEDGER") {
    return false;
  }
  const depth = value.queue_depth_by_state;
  return (
    typeof value.run_id === "string" &&
    typeof value.status === "string" &&
    typeof value.statement === "string" &&
    typeof value.execution_status === "string" &&
    value.release_eligible === false &&
    typeof value.snapshot_sha256 === "string" &&
    isNullableString(value.site_id) &&
    isNullableString(value.gateway_id) &&
    isNullableString(value.sequence_epoch) &&
    value.upload_state === "PENDING" &&
    typeof value.upload_statement === "string" &&
    Array.isArray(value.receipts) &&
    value.receipts.length === 0 &&
    isNullableString(value.unavailable_detail) &&
    isStringArray(value.publication_notes) &&
    isRecord(depth) &&
    Object.values(depth).every((n) => Number.isInteger(n) && (n as number) >= 0) &&
    Array.isArray(value.envelopes) &&
    value.envelopes.every(isGatewayEnvelope) &&
    Array.isArray(value.batches) &&
    value.batches.every(isGatewayBatch) &&
    Array.isArray(value.holds) &&
    value.holds.every(isGatewayHold)
  );
}

function isGatewayEnvelope(value: unknown): value is GatewayLedgerEnvelope {
  return (
    isRecord(value) &&
    typeof value.message_id === "string" &&
    typeof value.source_id === "string" &&
    typeof value.sequence_epoch === "string" &&
    Number.isInteger(value.sequence) &&
    typeof value.source_time === "string" &&
    typeof value.snapshot_sha256 === "string" &&
    typeof value.canonical === "string" &&
    typeof value.sha256 === "string" &&
    SHA256_HEX.test(value.sha256) &&
    typeof value.state === "string" &&
    isNullableString(value.batch_id) &&
    (value.ordinal === null || Number.isInteger(value.ordinal))
  );
}

function isGatewayBatch(value: unknown): value is GatewayLedgerBatch {
  return (
    isRecord(value) &&
    typeof value.batch_id === "string" &&
    typeof value.source_id === "string" &&
    typeof value.sequence_epoch === "string" &&
    typeof value.snapshot_sha256 === "string" &&
    typeof value.canonical === "string" &&
    typeof value.sha256 === "string" &&
    SHA256_HEX.test(value.sha256) &&
    typeof value.state === "string" &&
    Number.isInteger(value.attempt_count) &&
    isStringArray(value.message_ids)
  );
}

function isGatewayHold(value: unknown): value is GatewayLedgerHold {
  return (
    isRecord(value) &&
    Number.isInteger(value.hold_id) &&
    typeof value.kind === "string" &&
    typeof value.field === "string" &&
    typeof value.detail === "string" &&
    isNullableString(value.device_id) &&
    isNullableString(value.signal_id) &&
    isNullableString(value.source_time) &&
    Number.isInteger(value.seen_count)
  );
}

/** Whether a body is a whole stage view; half of one is not rendered. */
export function isRunStage(value: unknown): value is RunStage {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.run_id === "string" &&
    typeof value.status === "string" &&
    typeof value.statement === "string" &&
    typeof value.execution_status === "string" &&
    typeof value.release_eligible === "boolean" &&
    Array.isArray(value.release_blockers) &&
    value.release_blockers.every(
      (item) =>
        isRecord(item) &&
        typeof item.kind === "string" &&
        typeof item.statement === "string",
    ) &&
    isNullableString(value.unreadable_detail) &&
    typeof value.envelope_schema_id === "string" &&
    typeof value.envelope_schema_version === "number" &&
    typeof value.stage_schema_version === "number" &&
    isNullableString(value.integrity_digest) &&
    isNullableNumber(value.boundaries_total) &&
    isNullableNumber(value.published_through) &&
    isNullableString(value.site_id) &&
    isNullableString(value.source_id) &&
    isNullableString(value.gateway_id) &&
    (value.mapping === null || isStageMapping(value.mapping)) &&
    Array.isArray(value.refused_publications) &&
    value.refused_publications.every(
      (item) =>
        isRecord(item) &&
        typeof item.message_id === "string" &&
        typeof item.kind === "string",
    ) &&
    Array.isArray(value.envelopes) &&
    value.envelopes.every(isStagedEnvelope)
  );
}

/**
 * Build a run setup client over the two API paths.
 *
 * A response that does not match the expected shape is `unavailable`, not a
 * partially rendered run: a screen must not display half a frozen identity
 * and let a reader believe the rest was frozen too.
 */
export function createRunSetupClient(
  profilesPath: string,
  runsPath: string,
): RunSetupClient {
  return {
    async listProfiles(): Promise<RunProfilesResult> {
      try {
        const response = await fetch(profilesPath);
        if (!response.ok) {
          return { status: "unavailable" };
        }
        const body = (await response.json()) as Record<string, unknown>;
        const models = body?.model_profiles;
        const publications = body?.publication_profiles;
        if (
          !Array.isArray(models) ||
          !models.every(isModelProfile) ||
          !Array.isArray(publications) ||
          !publications.every(isPublicationProfile)
        ) {
          return { status: "unavailable" };
        }
        return {
          status: "loaded",
          modelProfiles: models,
          publicationProfiles: publications,
        };
      } catch {
        return { status: "unavailable" };
      }
    },

    async listRuns(): Promise<RunListResult> {
      try {
        const response = await fetch(runsPath);
        if (!response.ok) {
          return { status: "unavailable" };
        }
        const body = (await response.json()) as Record<string, unknown>;
        const runs = body?.runs;
        if (!Array.isArray(runs) || !runs.every(isInventoryRow)) {
          return { status: "unavailable" };
        }
        return { status: "loaded", runs };
      } catch {
        return { status: "unavailable" };
      }
    },

    async getRun(runId: string): Promise<RunDetailResult> {
      try {
        const response = await fetch(
          `${runsPath}/${encodeURIComponent(runId)}`,
        );
        if (response.status === 404) {
          // Not another run, and not an empty one: a run that is not there.
          return { status: "not_found" };
        }
        if (!response.ok) {
          return { status: "unavailable" };
        }
        const body = (await response.json()) as Record<string, unknown>;
        if (!isRunSummary(body?.run)) {
          return { status: "unavailable" };
        }
        return { status: "loaded", run: body.run as RunSummary };
      } catch {
        return { status: "unavailable" };
      }
    },

    async createRun(input: RunSetupInput): Promise<CreateRunResult> {
      let response: Response;
      try {
        response = await fetch(runsPath, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(input),
        });
      } catch {
        // The request never arrived, so nothing was written.
        return { status: "unavailable", message: null };
      }

      // Parsed separately from the send, and separately from the status,
      // because a 201 whose body cannot be read is a run that exists. An
      // earlier version parsed inside one try and reported that case as
      // `unavailable`, and the screen then said nothing was written over a
      // persisted Draft.
      let body: Record<string, unknown> | null = null;
      try {
        body = (await response.json()) as Record<string, unknown>;
      } catch {
        body = null;
      }

      if (response.status === 201) {
        const run = body?.run;
        if (!isRunSummary(run)) {
          return { status: "created_but_unreadable" };
        }
        return { status: "created", run };
      }

      // The backend's own copy, placed rather than restated. A second copy of
      // the rules in the browser is a second copy to keep in agreement, and
      // the one in the browser is the one that drifts.
      const detail = body?.detail;
      const message =
        isRecord(detail) && typeof detail.message === "string"
          ? detail.message
          : null;

      if (response.status === 422) {
        return {
          status: "refused",
          code:
            isRecord(detail) && typeof detail.code === "string"
              ? detail.code
              : null,
          refusalKind:
            isRecord(detail) && typeof detail.refusal_kind === "string"
              ? detail.refusal_kind
              : null,
          reasonCode:
            isRecord(detail) && typeof detail.reason_code === "string"
              ? detail.reason_code
              : null,
          message: message ?? "The run setup request was refused.",
        };
      }

      // Every other status, a store failure among them. It is not a refusal -
      // the request was not judged - but the backend's message says which
      // store could not be reached, and that is worth more than a generic
      // sentence.
      return { status: "unavailable", message };
    },

    getExecution(runId: string): Promise<RunExecutionResult> {
      return executionRequest(`${executionPath(runsPath, runId)}`, "GET");
    },

    startExecution(runId: string): Promise<RunExecutionResult> {
      return executionRequest(
        `${executionPath(runsPath, runId)}/start`,
        "POST",
      );
    },

    stepExecution(
      runId: string,
      request: RunStepRequest,
    ): Promise<RunExecutionResult> {
      return executionRequest(
        `${executionPath(runsPath, runId)}/step`,
        "POST",
        {
          boundaries: request.boundaries,
          from_boundary: request.fromBoundary,
        },
      );
    },

    runExecutionToEnd(runId: string): Promise<RunExecutionResult> {
      return executionRequest(
        `${executionPath(runsPath, runId)}/run-to-end`,
        "POST",
      );
    },

    getExecutionHistory(runId: string): Promise<RunHistoryResult> {
      return fetchRunHistory(runsPath, runId);
    },

    getExecutionHistorySince(
      runId: string,
      sinceBoundary: number,
    ): Promise<RunHistoryDeltaResult> {
      return fetchRunHistorySince(runsPath, runId, sinceBoundary);
    },

    getCommit(runId: string): Promise<RunCommitResult> {
      return commitRequest(
        `${runsPath}/${encodeURIComponent(runId)}/commit`,
        "GET",
      );
    },

    commit(runId: string): Promise<RunCommitResult> {
      return commitRequest(
        `${runsPath}/${encodeURIComponent(runId)}/commit`,
        "POST",
      );
    },

    async getStage(runId: string): Promise<RunStageResult> {
      let response: Response;
      try {
        response = await fetch(
          `${runsPath}/${encodeURIComponent(runId)}/stage`,
        );
      } catch {
        return { status: "unavailable", message: null };
      }
      let parsed: Record<string, unknown> | null = null;
      try {
        parsed = (await response.json()) as Record<string, unknown>;
      } catch {
        parsed = null;
      }
      if (response.status === 404) {
        return { status: "not_found" };
      }
      if (response.ok && isGatewayLedgerStage(parsed?.stage)) {
        return {
          status: "gateway",
          stage: parsed.stage as GatewayLedgerStage,
          frozenBasis: readFrozenBasis(parsed.frozen_basis),
        };
      }
      if (response.ok && isRunStage(parsed?.stage)) {
        return {
          status: "loaded",
          stage: parsed.stage as RunStage,
          frozenBasis: readFrozenBasis(parsed.frozen_basis),
        };
      }
      const detail = parsed?.detail;
      return {
        status: "unavailable",
        message:
          isRecord(detail) && typeof detail.message === "string"
            ? detail.message
            : null,
      };
    },
  };
}

function isRunCommit(value: unknown): value is RunCommit {
  if (!isRecord(value)) {
    return false;
  }
  const commit = value.commit;
  const release = value.release;
  return (
    (commit === "NOT_COMMITTED" ||
      (isRecord(commit) &&
        typeof commit.artifact_id === "string" &&
        typeof commit.envelope_count === "number")) &&
    (release === null ||
      (isRecord(release) &&
        typeof release.status === "string" &&
        typeof release.total === "number" &&
        typeof release.processed === "number" &&
        typeof release.accepted === "number")) &&
    (value.open_in_assetops === null ||
      (isRecord(value.open_in_assetops) &&
        typeof value.open_in_assetops.href === "string"))
  );
}

/**
 * The Commit read or the Commit itself, outcomes kept apart: 404 a run that is
 * not there, 409 a refusal (with the stage's blockers when it is
 * `COMMIT_REFUSED`), anything else did not complete.
 */
async function commitRequest(
  path: string,
  method: "GET" | "POST",
): Promise<RunCommitResult> {
  let response: Response;
  try {
    response = await fetch(path, { method });
  } catch {
    return { status: "unavailable", message: null };
  }
  let parsed: Record<string, unknown> | null = null;
  try {
    parsed = (await response.json()) as Record<string, unknown>;
  } catch {
    parsed = null;
  }
  if (response.status === 404) {
    return { status: "not_found" };
  }
  if (response.ok) {
    if (!isRunCommit(parsed)) {
      return { status: "unavailable", message: null };
    }
    return {
      status: "loaded",
      commit: {
        ...parsed,
        release_error:
          typeof parsed.release_error === "string" ? parsed.release_error : null,
      },
    };
  }
  const detail = parsed?.detail;
  const message =
    isRecord(detail) && typeof detail.message === "string"
      ? detail.message
      : null;
  if (response.status === 409) {
    const blockers =
      isRecord(detail) && Array.isArray(detail.release_blockers)
        ? detail.release_blockers.filter(
            (item): item is { kind: string; statement: string } =>
              isRecord(item) &&
              typeof item.kind === "string" &&
              typeof item.statement === "string",
          )
        : [];
    return {
      status: "refused",
      code:
        isRecord(detail) && typeof detail.code === "string" ? detail.code : null,
      message: message ?? "The Commit was refused.",
      releaseBlockers: blockers,
    };
  }
  return { status: "unavailable", message };
}

function executionPath(runsPath: string, runId: string): string {
  return `${runsPath}/${encodeURIComponent(runId)}/execution`;
}

/**
 * One execution read or control, with the four outcomes kept apart.
 *
 * Shared by all four methods rather than written out four times, because the
 * outcome mapping is the same fact each time and four copies would be four things
 * to keep in agreement. 404 is a run that is not there, 409 is a control the run's
 * state does not admit, 422 is a request that was not one, and anything else did
 * not complete.
 */
async function executionRequest(
  path: string,
  method: "GET" | "POST",
  body?: Record<string, number>,
): Promise<RunExecutionResult> {
  let response: Response;
  try {
    response = await fetch(path, {
      method,
      ...(body === undefined
        ? {}
        : {
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          }),
    });
  } catch {
    return { status: "unavailable", message: null };
  }

  let parsed: Record<string, unknown> | null = null;
  try {
    parsed = (await response.json()) as Record<string, unknown>;
  } catch {
    parsed = null;
  }

  if (response.status === 404) {
    return { status: "not_found" };
  }

  if (response.ok) {
    if (!isRunExecution(parsed?.execution)) {
      return { status: "unavailable", message: null };
    }
    return { status: "loaded", execution: parsed.execution as RunExecution };
  }

  const detail = parsed?.detail;
  const message =
    isRecord(detail) && typeof detail.message === "string"
      ? detail.message
      : null;

  if (response.status === 409 || response.status === 422) {
    return {
      status: "refused",
      code:
        isRecord(detail) && typeof detail.code === "string"
          ? detail.code
          : null,
      refusalKind:
        isRecord(detail) && typeof detail.refusal_kind === "string"
          ? detail.refusal_kind
          : null,
      message: message ?? "The execution control was refused.",
    };
  }

  return { status: "unavailable", message };
}
