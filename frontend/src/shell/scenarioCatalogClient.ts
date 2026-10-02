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
  /**
   * What the policy itself commits a kernel to, as distinct from which bound
   * carries it. A reader could see BOUNDED_AND_RECORDED with nothing on the
   * row saying whether the run continues afterwards.
   */
  policy_statement: string;
  statement: string;
}

/** One phase of the cycle a conforming kernel runs at each instant. */
export interface ScenarioBoundaryPhase {
  phase_id: string;
  /** The declared ordinal. The contract is the order, not the array index. */
  sequence: number;
  display_name: string;
  statement: string;
}

/** What a reading timestamped T describes, per class of reading. */
export interface ScenarioObservationRule {
  rule_id: string;
  reading_class: string;
  display_name: string;
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
  value: number | string | null;
  unit: string;
  canonical_value: number | string | null;
  canonical_unit: string;
}

/**
 * One rule about whether a reading exists at all, and as what.
 *
 * The companion to `ScenarioObservationRule`, which is about what a reading
 * MEANS once it exists. The two sets are kept apart on the wire for the reason
 * the contract keeps them apart: a timing convention and a reporting policy are
 * different kinds of statement, and one list holding both would invite a reader
 * to treat a cadence as a fact about the world.
 *
 * `observation_reconciliation` stood in this record until T022 and went with the
 * panel that rendered it, under
 * `D-2026-09-22-reconciliation-panel-retirement`.
 */
export interface ScenarioReportingRule {
  rule_id: string;
  display_name: string;
  statement: string;
}

export interface ScenarioExecutionContract {
  contract_version: number;
  dispatch_rules: ScenarioDispatchRule[];
  boundary_cycle: ScenarioBoundaryPhase[];
  observation_rules: ScenarioObservationRule[];
  reporting_rules: ScenarioReportingRule[];
  bound_cases: ScenarioBoundCase[];
  initialization_inputs: ScenarioInitializationInput[];
}

export interface ScenarioVersionIdentity {
  scenario_version: number;
  version_valid_from: string;
  supersedes: number | null;
}

/**
 * A legacy site declaration, as an older document carries it.
 *
 * Retired by `D-2026-10-01-run-binds-scenario-to-site`: a scenario names no
 * site, the declaration is never resolved, and run setup ignores it. It is
 * carried only so the detail screen can label it as legacy.
 */
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
  target_site: ScenarioTargetSiteDeclaration | null;
  site_contract: ScenarioSiteContract | null;
}

/** The document's prose about what a site must honour. Never evaluated. */
export interface ScenarioSiteContract {
  description: string;
}

/** One address the scenario names, and the roles it names it in. */
export interface ScenarioAddressNeed {
  address: string;
  scope: string;
  component_id: string | null;
  state_key: string;
  execution_roles: string[];
}

/** A device observation source the scenario reads through. */
export interface ScenarioDeviceSourceNeed {
  source_id: string;
  device_id: string;
  signal_id: string | null;
}

/**
 * What the scenario needs of whichever site a run binds it to.
 *
 * Derived from the document alone; no site was read to produce it, and it
 * says nothing about whether any site honours it.
 */
export interface ScenarioSiteNeeds {
  addresses: ScenarioAddressNeed[];
  device_sources: ScenarioDeviceSourceNeed[];
}

export interface ScenarioDetail extends ScenarioSummary {
  timeline: ScenarioTimelineEntry[];
  public_parameters: ScenarioParameter[];
  observation_sources: ScenarioObservationSource[];
  execution_contract: ScenarioExecutionContract;
  site_needs: ScenarioSiteNeeds;
}

/** Test-oracle metadata. Never operator content, never product evidence. */
export interface ScenarioPrivateExpectation {
  expectation_id: string;
  display_name: string;
  oracle_kind: string;
  statement: string;
}

export type ScenarioListResult =
  | { status: "loaded"; scenarios: ScenarioSummary[] }
  | { status: "unavailable" };

export type ScenarioDetailResult =
  | {
      status: "loaded";
      scenario: ScenarioDetail;
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

function isBoundaryPhase(value: unknown): value is ScenarioBoundaryPhase {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.phase_id === "string" &&
    typeof value.sequence === "number" &&
    typeof value.display_name === "string" &&
    typeof value.statement === "string"
  );
}

function isObservationRule(value: unknown): value is ScenarioObservationRule {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.rule_id === "string" &&
    typeof value.reading_class === "string" &&
    typeof value.display_name === "string" &&
    typeof value.statement === "string"
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
    typeof value.policy_statement === "string" &&
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
      (value.value === null && value.canonical_value === null) ||
      // T025a: a typed discrete member (unit `state`) is its own canonical
      // value, and is text rather than a number.
      (value.unit === "state" &&
        typeof value.value === "string" &&
        value.canonical_value === value.value)) &&
    typeof value.unit === "string" &&
    typeof value.canonical_unit === "string"
  );
}

function isReportingRule(value: unknown): value is ScenarioReportingRule {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.rule_id === "string" &&
    typeof value.display_name === "string" &&
    typeof value.statement === "string"
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
    Array.isArray(value.boundary_cycle) &&
    value.boundary_cycle.every(isBoundaryPhase) &&
    Array.isArray(value.observation_rules) &&
    value.observation_rules.every(isObservationRule) &&
    Array.isArray(value.bound_cases) &&
    value.bound_cases.every(isBoundCase) &&
    Array.isArray(value.reporting_rules) &&
    value.reporting_rules.every(isReportingRule) &&
    Array.isArray(value.initialization_inputs) &&
    value.initialization_inputs.every(isInitializationInput)
  );
}

export function isScenarioSummary(value: unknown): value is ScenarioSummary {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const scenario = value as Record<string, unknown>;
  const version = scenario.version as Record<string, unknown> | undefined;
  const target = scenario.target_site;
  const contract = scenario.site_contract;

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
    (target === null ||
      (isRecord(target) &&
        typeof target.policy === "string" &&
        isNullableString(target.site_id) &&
        isNullableString(target.template_id) &&
        typeof target.requirement === "string")) &&
    (contract === null ||
      (isRecord(contract) && typeof contract.description === "string"))
  );
}

function isAddressNeed(value: unknown): value is ScenarioAddressNeed {
  return (
    isRecord(value) &&
    typeof value.address === "string" &&
    typeof value.scope === "string" &&
    isNullableString(value.component_id) &&
    typeof value.state_key === "string" &&
    Array.isArray(value.execution_roles) &&
    value.execution_roles.every((role) => typeof role === "string")
  );
}

function isDeviceSourceNeed(value: unknown): value is ScenarioDeviceSourceNeed {
  return (
    isRecord(value) &&
    typeof value.source_id === "string" &&
    typeof value.device_id === "string" &&
    isNullableString(value.signal_id)
  );
}

function isSiteNeeds(value: unknown): value is ScenarioSiteNeeds {
  return (
    isRecord(value) &&
    Array.isArray(value.addresses) &&
    value.addresses.every(isAddressNeed) &&
    Array.isArray(value.device_sources) &&
    value.device_sources.every(isDeviceSourceNeed)
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
    isExecutionContract(scenario.execution_contract) &&
    isSiteNeeds(scenario.site_needs)
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
        if (
          !isScenarioDetail(body?.scenario) ||
          !Array.isArray(expectations) ||
          !expectations.every(isExpectation)
        ) {
          return { status: "unavailable" };
        }
        return {
          status: "loaded",
          scenario: body.scenario as ScenarioDetail,
          privateExpectations: expectations,
        };
      } catch {
        return { status: "unavailable" };
      }
    },
  };
}
