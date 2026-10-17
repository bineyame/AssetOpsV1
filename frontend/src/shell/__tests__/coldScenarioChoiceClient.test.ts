import { afterEach, describe, expect, it, vi } from "vitest";

import {
  COLD_SCENARIOS_API_PATH,
  createColdScenarioChoiceClient,
} from "../coldScenarioChoiceClient";

const NORMAL = {
  scenario_id: "cold-normal",
  scenario_version: 1,
  display_name: "Normal",
  schema: "cold-scenario/1",
  model_profile: "cold-thermal/1",
  publication_profile: "cold-publication/1",
  observation_profile: "cold-observation/1",
  start: "2026-10-06T19:00:00Z",
  end: "2026-10-06T20:00:00Z",
  seed: 20417,
};

function respondWith(body: unknown, status = 200) {
  const fetcher = vi.fn(() =>
    Promise.resolve({
      ok: status >= 200 && status < 300,
      status,
      json: () => Promise.resolve(body),
    } as unknown as Response),
  );
  vi.stubGlobal("fetch", fetcher);
  return fetcher;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("the cold Lab choices are read for the selected Site only", () => {
  it("asks for the selected Site and keeps the returned choices", async () => {
    const fetcher = respondWith({ site_id: "COLD-LAB-001", scenarios: [NORMAL] });
    const result = await createColdScenarioChoiceClient().listColdScenarios(
      "COLD-LAB-001",
    );
    expect(fetcher).toHaveBeenCalledWith(
      `${COLD_SCENARIOS_API_PATH}?site_id=COLD-LAB-001`,
    );
    expect(result).toEqual({
      status: "loaded",
      siteId: "COLD-LAB-001",
      scenarios: [NORMAL],
    });
  });

  it("keeps an empty answer for another Site as empty", async () => {
    respondWith({ site_id: "MG-900", scenarios: [] });
    const result =
      await createColdScenarioChoiceClient().listColdScenarios("MG-900");
    expect(result).toEqual({ status: "loaded", siteId: "MG-900", scenarios: [] });
  });

  it("states an unreadable store as unavailable, never as empty", async () => {
    respondWith({ detail: { code: "SITE_STORE_UNAVAILABLE" } }, 503);
    expect(
      await createColdScenarioChoiceClient().listColdScenarios("COLD-LAB-001"),
    ).toEqual({ status: "unavailable" });
  });

  it("refuses an answer for a different Site or a malformed choice", async () => {
    respondWith({ site_id: "COLD-001", scenarios: [NORMAL] });
    expect(
      await createColdScenarioChoiceClient().listColdScenarios("COLD-LAB-001"),
    ).toEqual({ status: "unavailable" });
    respondWith({
      site_id: "COLD-LAB-001",
      scenarios: [{ ...NORMAL, seed: "20417" }],
    });
    expect(
      await createColdScenarioChoiceClient().listColdScenarios("COLD-LAB-001"),
    ).toEqual({ status: "unavailable" });
    respondWith({
      site_id: "COLD-LAB-001",
      scenarios: [{ ...NORMAL, world_truth: 1 }],
    });
    expect(
      await createColdScenarioChoiceClient().listColdScenarios("COLD-LAB-001"),
    ).toEqual({ status: "unavailable" });
  });

  it("states a failed request as unavailable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new TypeError("Failed to fetch"))),
    );
    expect(
      await createColdScenarioChoiceClient().listColdScenarios("COLD-LAB-001"),
    ).toEqual({ status: "unavailable" });
  });
});
