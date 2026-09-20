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

/** One authored parameter. `unit` is null for a text parameter. */
export interface ScenarioParameter {
  parameter_id: string;
  display_name: string;
  value: number | string;
  unit: string | null;
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
      privateExpectations: ScenarioPrivateExpectation[];
    }
  | { status: "not_found" }
  | { status: "unavailable" };

export interface ScenarioCatalogClient {
  listScenarios(): Promise<ScenarioListResult>;
  getScenario(scenarioId: string): Promise<ScenarioDetailResult>;
}

function isParameter(value: unknown): value is ScenarioParameter {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const parameter = value as Record<string, unknown>;
  return (
    typeof parameter.parameter_id === "string" &&
    typeof parameter.display_name === "string" &&
    (typeof parameter.value === "number" ||
      typeof parameter.value === "string") &&
    (parameter.unit === null || typeof parameter.unit === "string")
  );
}

function isTimelineEntry(value: unknown): value is ScenarioTimelineEntry {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const entry = value as Record<string, unknown>;
  return (
    typeof entry.event_id === "string" &&
    typeof entry.sequence === "number" &&
    typeof entry.offset_minutes === "number" &&
    typeof entry.entry_kind === "string" &&
    typeof entry.category === "string" &&
    typeof entry.description === "string" &&
    Array.isArray(entry.parameters) &&
    entry.parameters.every(isParameter)
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
    scenario.public_parameters.every(isParameter)
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
        if (
          !isScenarioDetail(body?.scenario) ||
          !isTargetResolution(body?.target_resolution) ||
          !Array.isArray(expectations) ||
          !expectations.every(isExpectation)
        ) {
          return { status: "unavailable" };
        }
        return {
          status: "loaded",
          scenario: body.scenario as ScenarioDetail,
          targetResolution: body.target_resolution as ScenarioTargetResolution,
          privateExpectations: expectations,
        };
      } catch {
        return { status: "unavailable" };
      }
    },
  };
}
