import type {
  RunExecution,
  RunExecutionResult,
  RunSetupClient,
  RunStepRequest,
} from "../runSetupClient";

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
    offset_minutes: 1490,
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
 * The four execution methods a fake client needs, answering one projection.
 *
 * Spelled once here rather than in five test files, because a fake that drifts
 * from the interface is a test asserting against a screen no build produces.
 */
export function executionMethods(
  answer: RunExecutionResult = { status: "loaded", execution: NOT_STARTED },
): Pick<
  RunSetupClient,
  "getExecution" | "startExecution" | "stepExecution" | "runExecutionToEnd"
> {
  return {
    getExecution: () => Promise.resolve(answer),
    startExecution: () => Promise.resolve(answer),
    stepExecution: (_runId: string, _request: RunStepRequest) =>
      Promise.resolve(answer),
    runExecutionToEnd: () => Promise.resolve(answer),
  };
}
