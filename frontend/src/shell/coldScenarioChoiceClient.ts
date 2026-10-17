/**
 * W2-02: the registered cold-chain Lab choices for one selected Site
 * (`D-2026-10-17-w2-02-buildspec`, "Lab choice and run-request closure").
 *
 * Read after a Site is selected, and only for that Site: the backend answers
 * the six cold scenarios for the registered `COLD-LAB-001` Site and an empty
 * list for any other. The unfiltered legacy catalog never carries them. An
 * unreadable store is `unavailable`, never an empty list.
 */

export const COLD_SCENARIOS_API_PATH = "/api/simulator-lab/cold-scenarios";

export interface ColdScenarioChoice {
  scenario_id: string;
  scenario_version: number;
  display_name: string;
  schema: string;
  model_profile: string;
  publication_profile: string;
  observation_profile: string;
  start: string;
  end: string;
  seed: number;
}

export type ColdScenarioChoicesResult =
  | { status: "loaded"; siteId: string; scenarios: ColdScenarioChoice[] }
  | { status: "unavailable" };

export interface ColdScenarioChoiceClient {
  listColdScenarios(siteId: string): Promise<ColdScenarioChoicesResult>;
}

const STRING_KEYS = [
  "scenario_id",
  "display_name",
  "schema",
  "model_profile",
  "publication_profile",
  "observation_profile",
  "start",
  "end",
] as const;
const INTEGER_KEYS = ["scenario_version", "seed"] as const;
const CHOICE_KEY_COUNT = STRING_KEYS.length + INTEGER_KEYS.length;

function isChoice(value: unknown): value is ColdScenarioChoice {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const row = value as Record<string, unknown>;
  return (
    Object.keys(row).length === CHOICE_KEY_COUNT &&
    STRING_KEYS.every((key) => typeof row[key] === "string") &&
    INTEGER_KEYS.every((key) => Number.isInteger(row[key]))
  );
}

export function createColdScenarioChoiceClient(
  basePath: string = COLD_SCENARIOS_API_PATH,
): ColdScenarioChoiceClient {
  return {
    async listColdScenarios(siteId: string): Promise<ColdScenarioChoicesResult> {
      try {
        const response = await fetch(
          `${basePath}?site_id=${encodeURIComponent(siteId)}`,
        );
        if (!response.ok) {
          return { status: "unavailable" };
        }
        const body = (await response.json()) as Record<string, unknown> | null;
        const scenarios = body?.scenarios;
        if (
          body?.site_id !== siteId ||
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
