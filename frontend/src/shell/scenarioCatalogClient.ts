/**
 * Read-only client for the gated scenario catalog and detail API.
 *
 * The client is created with its base path rather than importing one, so this
 * module never spells a simulator URL: `tools/check-architecture.ps1` allows
 * that only in `simulatorLabRoutes.tsx`, which is where the path lives and
 * where this client is constructed.
 *
 * It reads. There is no create, edit, save, publish, duplicate, delete, or run
 * method, so no screen built on it can offer one. That is not a convention: a
 * screen cannot call what the client does not have, and the backend port has
 * no write either.
 *
 * Failures are returned as named states rather than thrown or swallowed. A
 * scenario that is not saved is `not_found`; a store that could not be read is
 * `unavailable`. Neither is allowed to degrade into an empty catalog, because
 * "no scenario is saved" and "the store could not be read" are different facts
 * and a screen must not state the first when the second is true.
 *
 * The public and private halves of a scenario arrive as separate fields of the
 * detail result, exactly as they leave the backend. The client does not merge
 * them, so a screen cannot render one where it meant the other, and a future
 * payload that dropped the private section would produce an empty list rather
 * than silently reusing public content.
 */

/**
 * Who answers for a value an executor would consume.
 *
 * Absent for a reported observation, and that absence is a fact rather than a
 * gap: a reading has no owner because it initializes nothing.
 */
export interface ScenarioParameterOwnership {
  owner: string;
  initializes: boolean;
}

/** That this world value limits another one, and at which end. */
export interface ScenarioParameterBound {
  state_key: string;
  bound_kind: string;
}

/** A quantity in canonical terms, so nothing has to parse display text. */
export interface ScenarioCanonicalQuantity {
  value: number;
  unit: string;
  dimension: string;
}

/**
 * One authored parameter.
 *
 * `unit` is null for a text parameter. `value` is null for a parameter whose
 * declared owner is the site's foundation: such a parameter declares the need
 * - the state, the unit, and that the foundation answers - and states no
 * number, because a machine's physical property is not the scenario's to
 * carry. The unit is still present, and a run resolves the number from the
 * site through the selected model profile.
 */
export interface ScenarioParameter {
  parameter_id: string;
  display_name: string;
  value: number | string | null;
  unit: string | null;
  execution_role: string;
  state_key: string | null;
  execution_requirement: string | null;
  ownership: ScenarioParameterOwnership | null;
  bounds: ScenarioParameterBound | null;
  canonical: ScenarioCanonicalQuantity | null;
}

/** Where an entry sits in time: an instant, a window, or the whole interval. */
export interface ScenarioEntryTiming {
  shape: string;
  duration_minutes: number | null;
}

/** What a causal entry changes. Present only for a causal input. */
export interface ScenarioStateEffect {
  direction: string;
  quantity_parameter_id: string | null;
  rate_parameter_id: string | null;
}

/** Which source a reading arrives through. Present only for an observation. */
export interface ScenarioObservationBinding {
  source_id: string;
  reported_parameter_id: string;
}

/** One authored timeline row, placed by an offset from the interval start. */
export interface ScenarioTimelineEntry {
  event_id: string;
  sequence: number;
  offset_minutes: number;
  entry_kind: string;
  category: string;
  description: string;
  parameters: ScenarioParameter[];
  execution_role: string;
  state_key: string | null;
  execution_requirement: string | null;
  timing: ScenarioEntryTiming;
  state_effect: ScenarioStateEffect | null;
  observation: ScenarioObservationBinding | null;
}

/** A declared device or non-device source a reading arrives through. */
export interface ScenarioObservationSource {
  source_id: string;
  source_kind: string;
  device_id: string | null;
  signal_id: string | null;
  cadence_ownership: string;
  description: string;
}

export interface ScenarioDispatchRule {
  rule_id: string;
  display_name: string;
  statement: string;
}

export interface ScenarioBoundCase {
  case_id: string;
  display_name: string;
  policy: string;
  statement: string;
}

/**
 * One initial world value the scenario declares, with the owner that answers.
 *
 * `value` and `canonical_value` are null exactly when the owner is the site's
 * foundation: such a parameter declares the need and states no number, so this
 * projection of the document has none to report. They are absent together -
 * a value with no canonical form, or the reverse, would be a record that
 * disagreed with itself - and the unit is present either way, because what
 * kind of quantity the state is remains the scenario's to declare.
 */
export interface ScenarioInitializationInput {
  parameter_id: string;
  display_name: string;
  state_key: string;
  owner: string;
  value: number | null;
  unit: string;
  canonical_value: number | null;
  canonical_unit: string;
}

/**
 * One reported reading against the causes declared before it.
 *
 * `declared_value` and `difference` are null when the contract cannot answer:
 * no declared initial value for the state, or a causal window still open when
 * the reading is taken. A contract that guessed at half a window would be
 * making a transition rule up, and transition rules belong to the runtime.
 */
export interface ScenarioObservationReconciliation {
  event_id: string;
  source_id: string;
  parameter_id: string;
  state_key: string;
  offset_minutes: number;
  reported_value: number;
  declared_value: number | null;
  difference: number | null;
  unit: string;
  state: string;
  /** Which of the answers this is, in words. Always present. */
  reason: string;
  accounted_by: string[];
}

export interface ScenarioExecutionContract {
  contract_version: number;
  dispatch_rules: ScenarioDispatchRule[];
  bound_cases: ScenarioBoundCase[];
  initialization_inputs: ScenarioInitializationInput[];
  observation_reconciliation: ScenarioObservationReconciliation[];
}

/** What a declared observation source resolved to on this installation. */
export interface ScenarioObservationSourceResolution {
  source_id: string;
  state: string;
  device_display_name: string | null;
  signal_display_name: string | null;
  reason: string;
  cadence_statement: string;
}

export interface ScenarioVersionIdentity {
  scenario_version: number;
  version_valid_from: string;
  supersedes: number | null;
}

/** What the document declares it needs, not what this installation has. */
export interface ScenarioTargetSiteDeclaration {
  policy: string;
  site_id: string | null;
  template_id: string | null;
  requirement: string;
}

export interface ScenarioSummary {
  scenario_id: string;
  display_name: string;
  purpose: string;
  origin: string;
  version: ScenarioVersionIdentity;
  target_site: ScenarioTargetSiteDeclaration;
}

export interface ScenarioDetail extends ScenarioSummary {
  timeline: ScenarioTimelineEntry[];
  public_parameters: ScenarioParameter[];
  observation_sources: ScenarioObservationSource[];
  execution_contract: ScenarioExecutionContract;
}

/** Test-oracle metadata. Never operator content, never product evidence. */
export interface ScenarioPrivateExpectation {
  expectation_id: string;
  display_name: string;
  oracle_kind: string;
  statement: string;
}

/**
 * What the declared target Site resolved to on this installation.
 *
 * Four states and they are four different facts. `reason` is always present,
 * because a control that is unavailable without a visible reason is a dead
 * end, and the text comes from the backend so the screen and the API cannot
 * describe the same state differently.
 */
export interface ScenarioTargetResolution {
  state: string;
  site_id: string | null;
  display_name: string | null;
  reason: string;
}

export type ScenarioListResult =
  | { status: "loaded"; scenarios: ScenarioSummary[] }
  | { status: "unavailable" };

export type ScenarioDetailResult =
  | {
      status: "loaded";
      scenario: ScenarioDetail;
      targetResolution: ScenarioTargetResolution;
      observationSourceResolutions: ScenarioObservationSourceResolution[];
      privateExpectations: ScenarioPrivateExpectation[];
    }
  | { status: "not_found" }
  | { status: "unavailable" };

export interface ScenarioCatalogClient {
  listScenarios(): Promise<ScenarioListResult>;
  getScenario(scenarioId: string): Promise<ScenarioDetailResult>;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object";
}

function isNullableString(value: unknown): boolean {
  return value === null || typeof value === "string";
}

function isOwnership(value: unknown): boolean {
  if (value === null) {
    return true;
  }
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.owner === "string" && typeof value.initializes === "boolean"
  );
}

function isParameterBound(value: unknown): boolean {
  if (value === null) {
    return true;
  }
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.state_key === "string" && typeof value.bound_kind === "string"
  );
}

function isCanonical(value: unknown): boolean {
  if (value === null) {
    return true;
  }
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.value === "number" &&
    typeof value.unit === "string" &&
    typeof value.dimension === "string"
  );
}

function isParameter(value: unknown): value is ScenarioParameter {
  if (!isRecord(value)) {
    return false;
  }
  const parameter = value;
  return (
    typeof parameter.parameter_id === "string" &&
    typeof parameter.display_name === "string" &&
    (typeof parameter.value === "number" ||
      typeof parameter.value === "string" ||
      // A foundation-owned parameter carries no number, and `null` is that
      // statement. It is the only absence accepted: a missing key is a
      // response that does not carry the field.
      parameter.value === null) &&
    isNullableString(parameter.unit) &&
    typeof parameter.execution_role === "string" &&
    isNullableString(parameter.state_key) &&
    isNullableString(parameter.execution_requirement) &&
    isOwnership(parameter.ownership) &&
    isParameterBound(parameter.bounds) &&
    isCanonical(parameter.canonical)
  );
}

function isTiming(value: unknown): boolean {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.shape === "string" &&
    (value.duration_minutes === null ||
      typeof value.duration_minutes === "number")
  );
}

function isStateEffect(value: unknown): boolean {
  if (value === null) {
    return true;
  }
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.direction === "string" &&
    isNullableString(value.quantity_parameter_id) &&
    isNullableString(value.rate_parameter_id)
  );
}

function isObservationBinding(value: unknown): boolean {
  if (value === null) {
    return true;
  }
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.source_id === "string" &&
    typeof value.reported_parameter_id === "string"
  );
}

function isTimelineEntry(value: unknown): value is ScenarioTimelineEntry {
  if (!isRecord(value)) {
    return false;
  }
  const entry = value;
  return (
    typeof entry.event_id === "string" &&
    typeof entry.sequence === "number" &&
    typeof entry.offset_minutes === "number" &&
    typeof entry.entry_kind === "string" &&
    typeof entry.category === "string" &&
    typeof entry.description === "string" &&
    Array.isArray(entry.parameters) &&
    entry.parameters.every(isParameter) &&
    typeof entry.execution_role === "string" &&
    isNullableString(entry.state_key) &&
    isNullableString(entry.execution_requirement) &&
    isTiming(entry.timing) &&
    isStateEffect(entry.state_effect) &&
    isObservationBinding(entry.observation)
  );
}

function isObservationSource(
  value: unknown,
): value is ScenarioObservationSource {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.source_id === "string" &&
    typeof value.source_kind === "string" &&
    isNullableString(value.device_id) &&
    isNullableString(value.signal_id) &&
    typeof value.cadence_ownership === "string" &&
    typeof value.description === "string"
  );
}

function isDispatchRule(value: unknown): value is ScenarioDispatchRule {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.rule_id === "string" &&
    typeof value.display_name === "string" &&
    typeof value.statement === "string"
  );
}

function isBoundCase(value: unknown): value is ScenarioBoundCase {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.case_id === "string" &&
    typeof value.display_name === "string" &&
    typeof value.policy === "string" &&
    typeof value.statement === "string"
  );
}

function isInitializationInput(
  value: unknown,
): value is ScenarioInitializationInput {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.parameter_id === "string" &&
    typeof value.display_name === "string" &&
    typeof value.state_key === "string" &&
    typeof value.owner === "string" &&
    // Absent together or present together. A number with no canonical form,
    // or a canonical form with no number, is a record disagreeing with
    // itself, and accepting one would put `undefined` in a rendered string.
    ((typeof value.value === "number" &&
      typeof value.canonical_value === "number") ||
      (value.value === null && value.canonical_value === null)) &&
    typeof value.unit === "string" &&
    typeof value.canonical_unit === "string"
  );
}

function isReconciliation(
  value: unknown,
): value is ScenarioObservationReconciliation {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.event_id === "string" &&
    typeof value.source_id === "string" &&
    typeof value.parameter_id === "string" &&
    typeof value.state_key === "string" &&
    typeof value.offset_minutes === "number" &&
    typeof value.reported_value === "number" &&
    (value.declared_value === null ||
      typeof value.declared_value === "number") &&
    (value.difference === null || typeof value.difference === "number") &&
    typeof value.unit === "string" &&
    typeof value.state === "string" &&
    typeof value.reason === "string" &&
    Array.isArray(value.accounted_by) &&
    value.accounted_by.every((item) => typeof item === "string")
  );
}

function isExecutionContract(
  value: unknown,
): value is ScenarioExecutionContract {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.contract_version === "number" &&
    Array.isArray(value.dispatch_rules) &&
    value.dispatch_rules.every(isDispatchRule) &&
    Array.isArray(value.bound_cases) &&
    value.bound_cases.every(isBoundCase) &&
    Array.isArray(value.initialization_inputs) &&
    value.initialization_inputs.every(isInitializationInput) &&
    Array.isArray(value.observation_reconciliation) &&
    value.observation_reconciliation.every(isReconciliation)
  );
}

function isObservationSourceResolution(
  value: unknown,
): value is ScenarioObservationSourceResolution {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.source_id === "string" &&
    typeof value.state === "string" &&
    isNullableString(value.device_display_name) &&
    isNullableString(value.signal_display_name) &&
    typeof value.reason === "string" &&
    typeof value.cadence_statement === "string"
  );
}

export function isScenarioSummary(value: unknown): value is ScenarioSummary {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const scenario = value as Record<string, unknown>;
  const version = scenario.version as Record<string, unknown> | undefined;
  const target = scenario.target_site as Record<string, unknown> | undefined;

  return (
    typeof scenario.scenario_id === "string" &&
    typeof scenario.display_name === "string" &&
    typeof scenario.purpose === "string" &&
    typeof scenario.origin === "string" &&
    version !== undefined &&
    typeof version.scenario_version === "number" &&
    typeof version.version_valid_from === "string" &&
    (version.supersedes === null ||
      typeof version.supersedes === "number") &&
    target !== undefined &&
    typeof target.policy === "string" &&
    (target.site_id === null || typeof target.site_id === "string") &&
    (target.template_id === null || typeof target.template_id === "string") &&
    typeof target.requirement === "string"
  );
}

function isScenarioDetail(value: unknown): value is ScenarioDetail {
  if (!isScenarioSummary(value)) {
    return false;
  }
  const scenario = value as unknown as Record<string, unknown>;
  return (
    Array.isArray(scenario.timeline) &&
    scenario.timeline.every(isTimelineEntry) &&
    Array.isArray(scenario.public_parameters) &&
    scenario.public_parameters.every(isParameter) &&
    Array.isArray(scenario.observation_sources) &&
    scenario.observation_sources.every(isObservationSource) &&
    isExecutionContract(scenario.execution_contract)
  );
}

function isTargetResolution(
  value: unknown,
): value is ScenarioTargetResolution {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const resolution = value as Record<string, unknown>;
  return (
    typeof resolution.state === "string" &&
    (resolution.site_id === null ||
      typeof resolution.site_id === "string") &&
    (resolution.display_name === null ||
      typeof resolution.display_name === "string") &&
    typeof resolution.reason === "string"
  );
}

function isExpectation(
  value: unknown,
): value is ScenarioPrivateExpectation {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const expectation = value as Record<string, unknown>;
  return (
    typeof expectation.expectation_id === "string" &&
    typeof expectation.display_name === "string" &&
    typeof expectation.oracle_kind === "string" &&
    typeof expectation.statement === "string"
  );
}

/**
 * Build a scenario client over an API base path.
 *
 * A response that does not match the expected shape is `unavailable`, not a
 * partially rendered scenario: a screen must not display half a timeline and
 * imply the rest of the interval is empty.
 */
export function createScenarioCatalogClient(
  basePath: string,
): ScenarioCatalogClient {
  return {
    async listScenarios(): Promise<ScenarioListResult> {
      try {
        const response = await fetch(basePath);
        if (!response.ok) {
          return { status: "unavailable" };
        }
        const body: unknown = await response.json();
        const scenarios = (body as Record<string, unknown>)?.scenarios;
        if (!Array.isArray(scenarios) || !scenarios.every(isScenarioSummary)) {
          return { status: "unavailable" };
        }
        return { status: "loaded", scenarios };
      } catch {
        return { status: "unavailable" };
      }
    },

    async getScenario(scenarioId: string): Promise<ScenarioDetailResult> {
      try {
        const response = await fetch(
          `${basePath}/${encodeURIComponent(scenarioId)}`,
        );
        if (response.status === 404) {
          return { status: "not_found" };
        }
        if (!response.ok) {
          return { status: "unavailable" };
        }
        const body = (await response.json()) as Record<string, unknown>;
        const expectations = body?.private_expectations;
        const sources = body?.observation_source_resolutions;
        if (
          !isScenarioDetail(body?.scenario) ||
          !isTargetResolution(body?.target_resolution) ||
          !Array.isArray(sources) ||
          !sources.every(isObservationSourceResolution) ||
          !Array.isArray(expectations) ||
          !expectations.every(isExpectation)
        ) {
          return { status: "unavailable" };
        }
        return {
          status: "loaded",
          scenario: body.scenario as ScenarioDetail,
          targetResolution: body.target_resolution as ScenarioTargetResolution,
          observationSourceResolutions: sources,
          privateExpectations: expectations,
        };
      } catch {
        return { status: "unavailable" };
      }
    },
  };
}
