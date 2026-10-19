import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createEvScenarioChoiceClient,
  EV_SCENARIOS_API_PATH,
} from "../evScenarioChoiceClient";

/** W2-05b (Q10, Q11): the EV choice read distinguishes 403, 404 and 503 and
 *  refuses any row with a missing, extra or mistyped key as unavailable. */

const ROW = {
  scenario_id: "ev-complete",
  scenario_version: 1,
  display_name: "Complete session",
  schema: "ev-scenario/1",
  model_profile: "ev-charger/1",
  publication_profile: "ev-publication/1",
  observation_profile: "ev-observation/1",
  window: { start: "2026-10-06T08:00:00Z", end: "2026-10-06T09:00:00Z", end_exclusive: true },
  seed: 20517,
  site_code: "EV-LAB-001",
};

function respond(status: number, body: unknown) {
  const fetchMock = vi.fn(() =>
    Promise.resolve(new Response(JSON.stringify(body), { status })),
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("EV scenario choice client (W2-05b)", () => {
  it("reads the Site-filtered path and returns the rows", async () => {
    const fetchMock = respond(200, { site_id: "EV-LAB-001", scenarios: [ROW] });
    const result = await createEvScenarioChoiceClient().listEvScenarios("EV-LAB-001");
    expect(fetchMock).toHaveBeenCalledWith(`${EV_SCENARIOS_API_PATH}?site_id=EV-LAB-001`);
    expect(result).toEqual({ status: "loaded", siteId: "EV-LAB-001", scenarios: [ROW] });
  });

  it.each([
    [403, "forbidden"],
    [404, "not_found"],
    [503, "unavailable"],
  ])("maps HTTP %i to %s", async (status, expected) => {
    respond(status, { detail: { code: "X", message: "x" } });
    expect(await createEvScenarioChoiceClient().listEvScenarios("EV-LAB-001")).toEqual({
      status: expected,
    });
  });

  it.each([
    ["a missing key", (() => { const { seed: _seed, ...rest } = ROW; return rest; })()],
    ["an extra key", { ...ROW, timestep: 1 }],
    ["a start/end row", { ...ROW, window: undefined, start: "a", end: "b" }],
    ["a string version", { ...ROW, scenario_version: "1" }],
    ["a malformed window", { ...ROW, window: { start: "a", end: "b" } }],
    ["a string end_exclusive", { ...ROW, window: { ...ROW.window, end_exclusive: "true" } }],
  ])("refuses %s as unavailable", async (_name, row) => {
    respond(200, { site_id: "EV-LAB-001", scenarios: [row] });
    expect(await createEvScenarioChoiceClient().listEvScenarios("EV-LAB-001")).toEqual({
      status: "unavailable",
    });
  });

  it("refuses an answer for another Site or with extra top-level keys", async () => {
    respond(200, { site_id: "EV-LAB-002", scenarios: [] });
    expect((await createEvScenarioChoiceClient().listEvScenarios("EV-LAB-001")).status).toBe(
      "unavailable",
    );
    respond(200, { site_id: "EV-LAB-001", scenarios: [], extra: true });
    expect((await createEvScenarioChoiceClient().listEvScenarios("EV-LAB-001")).status).toBe(
      "unavailable",
    );
  });

  it("returns an empty loaded list as empty, not unavailable", async () => {
    respond(200, { site_id: "MG-001", scenarios: [] });
    expect(await createEvScenarioChoiceClient().listEvScenarios("MG-001")).toEqual({
      status: "loaded",
      siteId: "MG-001",
      scenarios: [],
    });
  });
});
