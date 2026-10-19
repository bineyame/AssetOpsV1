/**
 * W2-05b: the registered EV charging Lab choices for one selected Site
 * (`.agent/W2-05b-build-spec.md`, Run 1 rulings Q8-Q11).
 *
 * Read after an EV_CHARGING Site is selected, and only for that Site: the
 * backend answers the six EV test runs for the registered `EV-LAB-001` Site
 * and an empty list for any other known Site. 403 (no Lab owner access), 404
 * (unknown Site) and an unreadable store are distinct answers, never an
 * empty list. A row with a missing, extra or mistyped key is unavailable.
 */

import { EV_SCENARIOS_API_PATH } from "./simulatorLabRoutes";

export { EV_SCENARIOS_API_PATH };

export interface EvScenarioWindow {
  start: string;
  end: string;
  end_exclusive: boolean;
}

export interface EvScenarioChoice {
  scenario_id: string;
  scenario_version: number;
  display_name: string;
  schema: string;
  model_profile: string;
  publication_profile: string;
  observation_profile: string;
  window: EvScenarioWindow;
  seed: number;
  site_code: string;
}

export type EvScenarioChoicesResult =
  | { status: "loaded"; siteId: string; scenarios: EvScenarioChoice[] }
  | { status: "forbidden" }
  | { status: "not_found" }
  | { status: "unavailable" };

export interface EvScenarioChoiceClient {
  listEvScenarios(siteId: string): Promise<EvScenarioChoicesResult>;
}

const STRING_KEYS = [
  "scenario_id",
  "display_name",
  "schema",
  "model_profile",
  "publication_profile",
  "observation_profile",
  "site_code",
] as const;
const INTEGER_KEYS = ["scenario_version", "seed"] as const;
const CHOICE_KEY_COUNT = STRING_KEYS.length + INTEGER_KEYS.length + 1;

function isWindow(value: unknown): value is EvScenarioWindow {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  const window = value as Record<string, unknown>;
  return (
    Object.keys(window).length === 3 &&
    typeof window.start === "string" &&
    typeof window.end === "string" &&
    typeof window.end_exclusive === "boolean"
  );
}

function isChoice(value: unknown): value is EvScenarioChoice {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  const row = value as Record<string, unknown>;
  return (
    Object.keys(row).length === CHOICE_KEY_COUNT &&
    STRING_KEYS.every((key) => typeof row[key] === "string") &&
    INTEGER_KEYS.every((key) => Number.isInteger(row[key])) &&
    isWindow(row.window)
  );
}

export function createEvScenarioChoiceClient(
  basePath: string = EV_SCENARIOS_API_PATH,
): EvScenarioChoiceClient {
  return {
    async listEvScenarios(siteId: string): Promise<EvScenarioChoicesResult> {
      try {
        const response = await fetch(
          `${basePath}?site_id=${encodeURIComponent(siteId)}`,
        );
        if (response.status === 403) {
          return { status: "forbidden" };
        }
        if (response.status === 404) {
          return { status: "not_found" };
        }
        if (!response.ok) {
          return { status: "unavailable" };
        }
        const body = (await response.json()) as Record<string, unknown> | null;
        const scenarios = body?.scenarios;
        if (
          body === null ||
          typeof body !== "object" ||
          Object.keys(body).length !== 2 ||
          body.site_id !== siteId ||
          !Array.isArray(scenarios) ||
          !scenarios.every(isChoice)
        ) {
          return { status: "unavailable" };
        }
        return { status: "loaded", siteId, scenarios };
      } catch {
        return { status: "unavailable" };
      }
    },
  };
}
