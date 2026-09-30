/**
 * One run's recorded Lab history, as the gated history read returns it (T025c).
 *
 * Private truth and every observation attempt, for the Simulator Lab only: the
 * only caller is the Lab's run screen, reached through routes that exist only
 * while the Lab gate is open. Every exact quantity is text and stays text - a
 * screen that parsed it to a float would be the one place the exact policy
 * stopped holding - and an absent value is `null`, never zero.
 */

export interface RunHistoryCoverage {
  family: string;
  availability: string;
  availability_statement: string;
  statement: string;
}

export interface RunHistoryBoundary {
  step_index: number;
  offset_minutes: number;
  simulation_time: string;
  has_preceding_interval: boolean;
}

export interface RunHistorySample {
  offset_minutes: number;
  address: string;
  state_key: string;
  phase: string;
  unit: string;
  value: string;
}

export interface RunHistoryLoad {
  address: string;
  priority_rank: number;
  demand_energy: string;
  served_energy: string;
  unserved_energy: string;
  demand_power: string;
  served_power: string;
  unserved_power: string;
}

export interface RunHistoryFlow {
  flow_id: string;
  from_address: string;
  to_address: string;
  energy: string;
  mean_power: string;
}

export interface RunHistoryControl {
  address: string;
  quantity: string;
  requested: string;
  accepted: string;
  unit: string;
  limited_by: string[];
}

export interface RunHistoryRequest {
  address: string;
  quantity: string;
  requested: string;
  unit: string;
  reason: string;
}

export interface RunHistoryEffectiveControl {
  address: string;
  from_offset: number;
  to_offset: number;
  value: string;
  unit: string;
  origin: string;
  provenance: string;
}

export interface RunHistoryInterval {
  from_offset: number;
  to_offset: number;
  segments: [number, number][];
  view: { name: string; address: string; value: string | null; unit: string }[];
  requests: RunHistoryRequest[];
  controls: RunHistoryControl[];
  loads: RunHistoryLoad[];
  flows: RunHistoryFlow[];
  effective_controls: RunHistoryEffectiveControl[];
  balances: string[];
  /**
   * T025d: each balance identity with the exact sums of the flows it names.
   * The sums are absent (`null`) when a named flow is missing, never partial.
   */
  balance_identities: RunHistoryBalance[];
  notes: string[];
}

export interface RunHistoryBalance {
  identity_id: string;
  sources: string[];
  sinks: string[];
  source_energy: string | null;
  sink_energy: string | null;
  residual: string | null;
}

/** T025d: one resolved reporting-path window - a reporting condition, never a physical outage. */
export interface RunHistoryReportingGap {
  event_id: string;
  condition_address: string;
  device_id: string;
  signal_id: string;
  address: string;
  timing_shape: string;
  declared_offset_minutes: number;
  start_offset_minutes: number;
  end_offset_minutes: number;
}

export interface RunHistoryBoundAttachment {
  role: string;
  component_id: string;
  via_component_id: string | null;
  bus_component_id: string;
  connection_ids: string[];
}

/**
 * T025d: the run-bound basis for drawing this history on the configured SLD.
 * `VERIFIED` only when the recorded attachments are the frozen ones; the
 * screen must still find the Site at `foundation_version` before binding.
 */
export interface RunHistoryDrawingContext {
  site_id: string;
  foundation_version: number;
  status: "VERIFIED" | "NOT_RECORDED" | "DISAGREES";
  statement: string;
  attachments: RunHistoryBoundAttachment[];
}

export interface RunHistoryAttempt {
  at_offset_minutes: number;
  address: string;
  device_id: string;
  signal_id: string;
  state_key: string;
  reading_class: string;
  source_sample_time: string;
  outcome: string;
  reported_value: string | null;
  canonical_unit: string;
  suppression_reason: string | null;
}

export interface RunHistorySignal {
  address: string;
  device_id: string;
  signal_id: string;
  reading_class: string;
  canonical_unit: string;
  cadence_minutes: number;
}

export interface RunHistoryAppliedEvent {
  event_id: string;
  address: string;
  direction: string;
  at_offset_minutes: number;
  share: string;
  declared: string;
  origin: string;
  phase_id: string;
}

export interface RunHistoryBoundedTransition {
  address: string;
  at_offset_minutes: number;
  bound_case_id: string;
  bound_kind: string;
  bound_value: string;
  requested: string;
  accepted: string;
  refused: string;
  event_ids: string[];
}

export interface RunHistoryDiscreteTransition {
  address: string;
  state_key: string;
  previous: string;
  next: string;
  phase: string;
  cause: string;
  at_offset_minutes: number;
  simulation_time: string;
}

export interface RunHistoryAttachment {
  role: string;
  component_id: string;
  via_component_id: string | null;
  bus_component_id: string;
}

export interface RunHistory {
  run_id: string;
  status: string;
  source: string;
  statement: string;
  history_schema_version: number | null;
  boundaries_total: number;
  boundaries_recorded: number;
  recorded_through_offset_minutes: number | null;
  inputs_identity: string;
  content_digest: string | null;
  observation_series_digest: string | null;
  history_digest: string | null;
  notes: string[];
  failure: {
    kind: string;
    subject: string;
    statement: string;
    at_offset_minutes: number | null;
    detail: string[];
  } | null;
  coverage: RunHistoryCoverage[];
  sample_phases: { phase: string; statement: string }[];
  boundaries: RunHistoryBoundary[];
  samples: RunHistorySample[];
  intervals: RunHistoryInterval[];
  exposures: {
    address: string;
    event_id: string;
    parameter_id: string;
    value: string;
    from_offset: number;
    to_offset: number;
  }[];
  attempts: RunHistoryAttempt[];
  signals: RunHistorySignal[];
  applied_events: RunHistoryAppliedEvent[];
  bounded_transitions: RunHistoryBoundedTransition[];
  discrete_transitions: RunHistoryDiscreteTransition[];
  bus_attachments: RunHistoryAttachment[];
  reporting_gaps: RunHistoryReportingGap[];
  drawing_context: RunHistoryDrawingContext | null;
}

export type RunHistoryResult =
  | { status: "loaded"; history: RunHistory }
  | { status: "not_found" }
  | { status: "unavailable"; message: string | null };

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object";
}

function isNullable(value: unknown, type: "string" | "number"): boolean {
  return value === null || typeof value === type;
}

function every(
  value: unknown,
  check: (item: Record<string, unknown>) => boolean,
): boolean {
  return (
    Array.isArray(value) &&
    value.every((item) => isRecord(item) && check(item))
  );
}

/**
 * Whether a response is a history this screen can render.
 *
 * Checks the manifest, the coverage and every row family's shape on the
 * fields the inspector reads, so a malformed row is an unavailable history
 * rather than a blank cell that reads as a recorded absence.
 */
export function isRunHistory(value: unknown): value is RunHistory {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.run_id === "string" &&
    typeof value.status === "string" &&
    typeof value.source === "string" &&
    typeof value.statement === "string" &&
    isNullable(value.history_schema_version, "number") &&
    typeof value.boundaries_total === "number" &&
    typeof value.boundaries_recorded === "number" &&
    isNullable(value.recorded_through_offset_minutes, "number") &&
    isNullable(value.history_digest, "string") &&
    Array.isArray(value.notes) &&
    (value.failure === null || isRecord(value.failure)) &&
    every(
      value.coverage,
      (item) =>
        typeof item.family === "string" &&
        typeof item.availability === "string" &&
        typeof item.statement === "string",
    ) &&
    every(
      value.boundaries,
      (item) =>
        typeof item.offset_minutes === "number" &&
        typeof item.simulation_time === "string" &&
        typeof item.has_preceding_interval === "boolean",
    ) &&
    every(
      value.samples,
      (item) =>
        typeof item.offset_minutes === "number" &&
        typeof item.address === "string" &&
        typeof item.phase === "string" &&
        typeof item.unit === "string" &&
        typeof item.value === "string",
    ) &&
    every(
      value.intervals,
      (item) =>
        typeof item.from_offset === "number" &&
        typeof item.to_offset === "number" &&
        Array.isArray(item.loads) &&
        Array.isArray(item.flows) &&
        Array.isArray(item.controls) &&
        Array.isArray(item.requests) &&
        every(
          item.balance_identities,
          (balance) =>
            typeof balance.identity_id === "string" &&
            isNullable(balance.residual, "string"),
        ),
    ) &&
    every(
      value.attempts,
      (item) =>
        typeof item.at_offset_minutes === "number" &&
        typeof item.outcome === "string" &&
        isNullable(item.reported_value, "string"),
    ) &&
    Array.isArray(value.signals) &&
    Array.isArray(value.applied_events) &&
    Array.isArray(value.bounded_transitions) &&
    Array.isArray(value.discrete_transitions) &&
    Array.isArray(value.bus_attachments) &&
    Array.isArray(value.exposures) &&
    every(
      value.reporting_gaps,
      (item) =>
        typeof item.event_id === "string" &&
        typeof item.start_offset_minutes === "number" &&
        typeof item.end_offset_minutes === "number",
    ) &&
    (value.drawing_context === null || isDrawingContext(value.drawing_context))
  );
}

function isDrawingContext(value: unknown): boolean {
  return (
    isRecord(value) &&
    typeof value.site_id === "string" &&
    typeof value.foundation_version === "number" &&
    (value.status === "VERIFIED" ||
      value.status === "NOT_RECORDED" ||
      value.status === "DISAGREES") &&
    typeof value.statement === "string" &&
    every(
      value.attachments,
      (item) =>
        typeof item.component_id === "string" &&
        isNullable(item.via_component_id, "string") &&
        typeof item.bus_component_id === "string" &&
        Array.isArray(item.connection_ids) &&
        item.connection_ids.every((id) => typeof id === "string"),
    )
  );
}

/** The gated history read. A read: it changes nothing and executes nothing. */
export async function fetchRunHistory(
  runsPath: string,
  runId: string,
): Promise<RunHistoryResult> {
  let response: Response;
  try {
    response = await fetch(
      `${runsPath}/${encodeURIComponent(runId)}/execution/history`,
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
  if (response.ok && isRunHistory(parsed?.history)) {
    return { status: "loaded", history: parsed.history as RunHistory };
  }
  const detail = parsed?.detail;
  return {
    status: "unavailable",
    message:
      isRecord(detail) && typeof detail.message === "string"
        ? detail.message
        : null,
  };
}
