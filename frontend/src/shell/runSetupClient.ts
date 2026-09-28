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
  scenario_id: string;
  scenario_version: number;
  frozen_inputs: RunFrozenInput[];
  blocking_reasons: RunBlockingReason[];
  unsupported_optional_inputs: RunUnsupportedOptionalInput[];
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
  | { status: "loaded"; runs: RunInventoryRow[] }
  | { status: "unavailable" };

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
}

/** One span across which one signal's reporting path is forced unavailable. */
export interface RunReportingGap {
  event_id: string;
  condition_address: string;
  device_id: string;
  signal_id: string;
  address: string;
  offset_minutes: number;
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
    value.supported_reporting_states.every(isSupportedState)
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
    typeof value.scenario_id === "string" &&
    typeof value.scenario_version === "number" &&
    Array.isArray(value.frozen_inputs) &&
    value.frozen_inputs.every(isFrozenInput) &&
    Array.isArray(value.blocking_reasons) &&
    value.blocking_reasons.every(isBlockingReason) &&
    Array.isArray(value.unsupported_optional_inputs) &&
    value.unsupported_optional_inputs.every(isUnsupportedOptional)
  );
}

function isStringArray(value: unknown): boolean {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
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

function isObservationRow(value: unknown): value is RunObservationRow {
  if (!isRecord(value)) {
    return false;
  }
  return (
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
    typeof value.statement === "string"
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
    typeof value.offset_minutes === "number" &&
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
    isNullableString(value.suppression_reason)
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
    value.recent_reports.every(isRecentReport)
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
  };
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
