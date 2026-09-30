import type {
  RunExecution,
  RunExecutionResult,
  RunSetupClient,
  RunStage,
  RunStageResult,
  RunStagedEnvelope,
  RunStepRequest,
} from "../runSetupClient";
import type { RunHistory, RunHistoryResult } from "../runHistory";

/**
 * Execution projections shaped like the ones the backend actually sends.
 *
 * Every number here was read off a real execution of the shipped Fuel Loss Event
 * against MG-001's own Foundation, not invented: 430 L at the start, 374.02 L when
 * the dispatch window closes, 254.02 L after the removal, and the sensor reading
 * half a litre low throughout. A fixture with plausible round numbers would let a
 * screen test pass against a payload the backend never produces.
 *
 * `RUNNING_IN_THE_GAP` is the one that carries the slice. The run has reached
 * offset 1545, inside the declared reporting gap `[1490, 1580)` and past the
 * removal `[1500, 1545)`: the world holds 254.02 L, the newest reading is the
 * 373.52 L published at offset 1485 before the gap opened, and the two columns
 * therefore differ by 119.50 L, which is the 120 L removal with the sensor's
 * declared -0.5 L bias taken back out. That is the demonstration,
 * and a test that asserts against page text rather than against the two cells
 * would pass with the columns merged.
 */

const SIGNALS: RunExecution["signals"] = [
  {
    device_id: "fuel-level-sensor",
    signal_id: "fuel-level",
    address: "fuel-tank-volume@fuel-tank",
    state_key: "fuel-tank-volume",
    reading_class: "STATE_SIGNAL",
    canonical_unit: "L",
    cadence_minutes: 15,
    bias: "-0.5",
    dropout_per_thousand: 40,
    statement:
      "The fuel level sensor publishes the tank's stored volume every fifteen minutes, reading half a litre low.",
  },
  {
    device_id: "generator-controller",
    signal_id: "ac-power",
    address: "generator-output-power@generator",
    state_key: "generator-output-power",
    reading_class: "INTERVAL_SIGNAL",
    canonical_unit: "kW",
    cadence_minutes: 60,
    bias: "0",
    dropout_per_thousand: 0,
    statement:
      "The generator controller publishes its average output over the span that just ended, once an hour.",
  },
];

const GAPS: RunExecution["reporting_gaps"] = [
  {
    event_id: "fuel-level-reporting-gap",
    condition_address: "fuel-level-reporting-availability@fuel-tank",
    device_id: "fuel-level-sensor",
    signal_id: "fuel-level",
    address: "fuel-tank-volume@fuel-tank",
    // The shape the document declared, beside the span it resolved to. A POINT
    // and a WINDOW can resolve to the same offsets at some timesteps, and a
    // fixture that carried only the offsets would render them identically.
    timing_shape: "WINDOW",
    declared_offset_minutes: 1490,
    start_offset_minutes: 1490,
    end_offset_minutes: 1580,
  },
];

const BASE: RunExecution = {
  run_id: "run-0123456789abcdef0123456789abcdef",
  status: "NOT_STARTED",
  statement:
    "This Draft has not been executed. Its frozen inputs are eligible and nothing has run.",
  boundaries_completed: 0,
  boundaries_total: 165,
  offset_minutes: 0,
  simulation_time: "2026-09-21T00:00:00Z",
  interval_start_time: "2026-09-21T00:00:00Z",
  interval_end_time: "2026-09-22T17:00:00Z",
  timestep_minutes: 15,
  seed: 20260921,
  kernel_version: 1,
  model_profile_id: "minimal-fuel-tank",
  model_profile_version: 1,
  publication_profile_id: "simulator-lab-publication",
  publication_profile_version: 2,
  numeric_policy: "EXACT_RATIONAL",
  numeric_policy_version: 1,
  execution_contract_version: 8,
  inputs_identity: "",
  content_digest: null,
  observation_series_digest: "a".repeat(64),
  reported_count: 0,
  suppressed_by_gap_count: 0,
  dropped_count: 0,
  notes: [],
  failure: null,
  private_state: [],
  observations: [],
  signals: SIGNALS,
  reporting_gaps: GAPS,
  recent_reports: [],
  electrical: null,
};

export const NOT_STARTED: RunExecution = BASE;

export const RUNNING_IN_THE_GAP: RunExecution = {
  ...BASE,
  status: "RUNNING",
  statement:
    "This execution has reached the instant shown and has not finished.",
  boundaries_completed: 104,
  offset_minutes: 1545,
  simulation_time: "2026-09-22T01:45:00Z",
  inputs_identity: "b".repeat(64),
  observation_series_digest: "c".repeat(64),
  reported_count: 96,
  suppressed_by_gap_count: 4,
  dropped_count: 5,
  private_state: [
    {
      address: "fuel-tank-capacity@fuel-tank",
      state_key: "fuel-tank-capacity",
      value: "500",
      canonical_unit: "L",
      kind: "STOCK",
    },
    {
      address: "fuel-tank-volume@fuel-tank",
      state_key: "fuel-tank-volume",
      value: "254.02",
      canonical_unit: "L",
      kind: "STOCK",
    },
  ],
  observations: [
    {
      address: "fuel-tank-volume@fuel-tank",
      state_key: "fuel-tank-volume",
      device_id: "fuel-level-sensor",
      signal_id: "fuel-level",
      reading_class: "STATE_SIGNAL",
      at_offset_minutes: 1545,
      simulation_time: "2026-09-22T01:45:00Z",
      canonical_unit: "L",
      true_value: "254.02",
      reported_value: "373.52",
      reported_source_time: "2026-09-22T00:45:00Z",
      reported_at_offset_minutes: 1485,
      quality: "STALE",
      quality_statement:
        "No reading was published at this instant, and the newest one before it is shown with its own time.",
      due: true,
      outcome: "SUPPRESSED_BY_GAP",
      outcome_statement:
        "The sample was due and the reporting path was forced unavailable across a declared window.",
      suppression_reason:
        "fuel-level-reporting-gap forces fuel-level-reporting-availability@fuel-tank unavailable from offset 1490 up to but not including 1580, so this signal took no sample here.",
      cadence_minutes: 15,
      bias: "-0.5",
      dropout_per_thousand: 40,
    },
    {
      address: "generator-output-power@generator",
      state_key: "generator-output-power",
      device_id: "generator-controller",
      signal_id: "ac-power",
      reading_class: "INTERVAL_SIGNAL",
      at_offset_minutes: 1545,
      simulation_time: "2026-09-22T01:45:00Z",
      canonical_unit: "kW",
      true_value: null,
      reported_value: "45",
      reported_source_time: "2026-09-21T22:00:00Z",
      reported_at_offset_minutes: 1320,
      quality: "STALE",
      quality_statement:
        "No reading was published at this instant, and the newest one before it is shown with its own time.",
      due: false,
      outcome: null,
      outcome_statement: null,
      suppression_reason: null,
      cadence_minutes: 60,
      bias: "0",
      dropout_per_thousand: 0,
    },
  ],
  recent_reports: [
    {
      device_id: "fuel-level-sensor",
      signal_id: "fuel-level",
      address: "fuel-tank-volume@fuel-tank",
      reading_class: "STATE_SIGNAL",
      at_offset_minutes: 1485,
      source_sample_time: "2026-09-22T00:45:00Z",
      outcome: "REPORTED",
      outcome_statement:
        "The sample was due, the reporting path was carrying readings, and the device published a value.",
      reported_value: "373.52",
      canonical_unit: "L",
      suppression_reason: null,
    },
    {
      device_id: "fuel-level-sensor",
      signal_id: "fuel-level",
      address: "fuel-tank-volume@fuel-tank",
      reading_class: "STATE_SIGNAL",
      at_offset_minutes: 1545,
      source_sample_time: "2026-09-22T01:45:00Z",
      outcome: "SUPPRESSED_BY_GAP",
      outcome_statement:
        "The sample was due and the reporting path was forced unavailable across a declared window.",
      reported_value: null,
      canonical_unit: "L",
      suppression_reason:
        "fuel-level-reporting-gap forces fuel-level-reporting-availability@fuel-tank unavailable from offset 1490 up to but not including 1580, so this signal took no sample here.",
    },
  ],
};

export const COMPLETED: RunExecution = {
  ...RUNNING_IN_THE_GAP,
  status: "COMPLETED",
  statement: "This execution covered its whole interval.",
  boundaries_completed: 165,
  offset_minutes: 2460,
  simulation_time: "2026-09-22T17:00:00Z",
  content_digest: "d".repeat(64),
  private_state: [
    {
      address: "fuel-tank-capacity@fuel-tank",
      state_key: "fuel-tank-capacity",
      value: "500",
      canonical_unit: "L",
      kind: "STOCK",
    },
    {
      address: "fuel-tank-volume@fuel-tank",
      state_key: "fuel-tank-volume",
      value: "500",
      canonical_unit: "L",
      kind: "STOCK",
    },
  ],
};

export const INTERRUPTED: RunExecution = {
  ...BASE,
  status: "INTERRUPTED",
  statement:
    "An execution of this Draft was running when the process holding it ended.",
};

/**
 * A record this build cannot interpret, which is a fact about the RECORD.
 *
 * Deliberately not INTERRUPTED and not FAILED: both of those report an
 * execution event, and nothing happened to this run. The note is where the
 * reason lives, because a per-status sentence cannot name a schema number.
 */
export const ARTIFACT_UNREADABLE: RunExecution = {
  ...BASE,
  status: "ARTIFACT_UNREADABLE",
  statement:
    "This Draft has an execution record and this build cannot interpret it.",
  notes: [
    "The execution record for run-a is written in artifact schema 3 and this " +
      "build reads schema 2. A later build wrote it, so what its fields mean " +
      "is that build's to say. The record is left exactly as it is.",
  ],
};

/**
 * Three staged envelopes, copied byte for byte from a real stage.
 *
 * Read off `host/lab_execution.py` staging the shipped Fuel Loss Event against
 * MG-001 to offset 1545: sequences 89 to 91 are the fuel sensor's last three
 * publications before the reporting gap opened, the last one at 00:45:00Z and
 * published three seconds later. Nothing after it is staged, because nothing
 * after it was published - which is the gap, seen from the boundary.
 */
function staged(
  sequence: number,
  messageId: string,
  sourceTime: string,
  publishedAt: string,
): RunStagedEnvelope {
  return {
    canonical:
      `{"mapping":{"mapping_set_id":"simulator-lab-gateway-fuel","mapping_version":1},` +
      `"message":{"message_id":"${messageId}","sequence":${sequence}},` +
      `"payload":{"interval_end":null,"interval_start":null,"measurement":"STATE_AT_INSTANT",` +
      `"quality":"GOOD","unavailable_reason":null,"unit":"L","value":"373.52"},` +
      `"schema":{"id":"assetops.source-envelope","version":1},` +
      `"source":{"device_id":"fuel-level-sensor","gateway_id":"simulator-lab-gateway",` +
      `"signal_id":"fuel-level","site_id":"MG-001","source_id":"simulator-lab-source"},` +
      `"timing":{"published_at":"${publishedAt}","source_time":"${sourceTime}"}}`,
    message_id: messageId,
    sequence,
    device_id: "fuel-level-sensor",
    signal_id: "fuel-level",
    mapping_set_id: "simulator-lab-gateway-fuel",
    mapping_version: 1,
    schema_version: 1,
    source_time: sourceTime,
    published_at: publishedAt,
    measurement: "STATE_AT_INSTANT",
    value: "373.52",
    unit: "L",
    quality: "GOOD",
    unavailable_reason: null,
    interval_start: null,
    interval_end: null,
  };
}

const MAPPING: RunStage["mapping"] = {
  mapping_set_id: "simulator-lab-gateway-fuel",
  mapping_version: 1,
  publication_latency_seconds: 3,
  entries: [
    {
      device_id: "fuel-level-sensor",
      signal_id: "fuel-level",
      measurement: "STATE_AT_INSTANT",
      unit: "L",
      publishes_unavailable: true,
    },
  ],
};

export const NOT_STAGED: RunStage = {
  run_id: "run-a",
  status: "NOT_STAGED",
  statement:
    "No source envelope has been staged for this draft. Envelopes are staged as an execution publishes readings, so a draft nothing has executed has none.",
  execution_status: "NOT_STARTED",
  release_eligible: false,
  release_blockers: [
    { kind: "NOTHING_STAGED", statement: "There is nothing staged to release." },
    {
      kind: "EXECUTION_NOT_COMPLETED",
      statement:
        "The execution that publishes into this stage has not completed, so the stage may still be missing envelopes a completed run would have published.",
    },
  ],
  unreadable_detail: null,
  envelope_schema_id: "assetops.source-envelope",
  envelope_schema_version: 1,
  stage_schema_version: 2,
  integrity_digest: null,
  boundaries_total: null,
  published_through: null,
  site_id: null,
  source_id: null,
  gateway_id: null,
  mapping: null,
  refused_publications: [],
  envelopes: [],
};

export const STAGED_IN_THE_GAP: RunStage = {
  ...NOT_STAGED,
  status: "STAGED",
  statement:
    "These are the canonical source envelopes the simulated gateway published for this draft, exactly as persisted and re-read from the stage. They are staged, not released: nothing has been committed, nothing has reached ingestion, and no site history, evidence or finding has been written from them.",
  execution_status: "RUNNING",
  release_blockers: [
    NOT_STAGED.release_blockers[1],
    {
      kind: "STAGING_INCOMPLETE",
      statement:
        "The stage has not yet recorded publication through the last boundary of its run. That is expected while the run is still executing; after it has finished, it can mean a stage write failed or a publication was refused. Either way the stage may not hold every envelope the run publishes, and a stage that may be incomplete is not releasable.",
    },
  ],
  integrity_digest:
    "27bccb8e5da84e80e41291d5211ff337cad675ee5a755d4c6f51c31ab8920ab7",
  boundaries_total: 165,
  published_through: 104,
  site_id: "MG-001",
  source_id: "simulator-lab-source",
  gateway_id: "simulator-lab-gateway",
  mapping: MAPPING,
  envelopes: [
    staged(
      89,
      "7bb4f91a0c124591beff1b44dbfe680024da0a99ab30d2dc66c390429934ee5b",
      "2026-09-22T00:15:00Z",
      "2026-09-22T00:15:03Z",
    ),
    staged(
      90,
      "1d38b354cafb5aeb8272d632f03abc40c248363594a76a57d80d833d1c890074",
      "2026-09-22T00:30:00Z",
      "2026-09-22T00:30:03Z",
    ),
    staged(
      91,
      "52c9a7f22a1e4893fb07b4663fdd22fa1d3c56885d5fb3b9c57a0a42d7f8b77e",
      "2026-09-22T00:45:00Z",
      "2026-09-22T00:45:03Z",
    ),
  ],
};

export const STAGE_UNREADABLE: RunStage = {
  ...NOT_STAGED,
  status: "STAGE_UNREADABLE",
  statement:
    "A stage exists for this draft and it failed its integrity check, so none of its content is presented as releasable. The stage is left exactly as it is; the detail names what failed.",
  execution_status: "COMPLETED",
  release_blockers: [
    {
      kind: "INTEGRITY_FAILURE",
      statement:
        "The persisted stage failed its integrity check, and content that cannot be verified is not releasable.",
    },
  ],
  unreadable_detail:
    "its integrity digest does not match its content, so the content was changed after it was staged",
};

/**
 * A run with no recorded history, as the host states it (T025c): nothing has
 * executed it, so every family is UNAVAILABLE for that one reason.
 */
export const NOT_RECORDED: RunHistory = {
  run_id: "run-00000000000000000000000000000001",
  status: "NOT_STARTED",
  source: "NOT_RECORDED",
  statement:
    "This run has no recorded history: it has not been executed, or its live session ended with the process that ran it.",
  history_schema_version: null,
  boundaries_total: 0,
  boundaries_recorded: 0,
  recorded_through_offset_minutes: null,
  inputs_identity: "",
  content_digest: null,
  observation_series_digest: null,
  history_digest: null,
  notes: [],
  failure: null,
  coverage: [
    "state_samples",
    "intervals",
    "observation_attempts",
    "timeline",
    "drawing",
  ].map((family) => ({
    family,
    availability: "UNAVAILABLE",
    availability_statement:
      "Not recorded for this run; nothing is shown in its place.",
    statement:
      "This run has no recorded history: it has not been executed, or its live session ended with the process that ran it.",
  })),
  sample_phases: [],
  boundaries: [],
  samples: [],
  intervals: [],
  exposures: [],
  attempts: [],
  signals: [],
  applied_events: [],
  bounded_transitions: [],
  discrete_transitions: [],
  bus_attachments: [],
};

/**
 * The execution methods, and the stage read, a fake client needs.
 *
 * Spelled once here rather than in five test files, because a fake that drifts
 * from the interface is a test asserting against a screen no build produces.
 */
export function executionMethods(
  answer: RunExecutionResult = { status: "loaded", execution: NOT_STARTED },
  stage: RunStageResult = { status: "loaded", stage: NOT_STAGED },
  history: RunHistoryResult = { status: "loaded", history: NOT_RECORDED },
): Pick<
  RunSetupClient,
  | "getExecution"
  | "startExecution"
  | "stepExecution"
  | "runExecutionToEnd"
  | "getStage"
  | "getExecutionHistory"
> {
  return {
    getExecution: () => Promise.resolve(answer),
    startExecution: () => Promise.resolve(answer),
    stepExecution: (_runId: string, _request: RunStepRequest) =>
      Promise.resolve(answer),
    runExecutionToEnd: () => Promise.resolve(answer),
    getStage: () => Promise.resolve(stage),
    getExecutionHistory: () => Promise.resolve(history),
  };
}
