/**
 * W5-01a C2 (`.agent/W5-01-build-spec.md` C2): the cold depth client. This run builds and tests the exact
 * Cooling DTO validation and card labels; the page tests (`cooling_state_copy` and the page half of
 * `cooling_dto_and_labels`) are held on the C2 questions in `.agent/W5-01a-phase-handoff.md`.
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { NO_WINDOW } from "../coldAssessmentClient";
import {
  COOLING_CONTEXT_LABELS,
  coolingCardLabels,
  createColdDepthClient,
  isColdCoolingRead,
} from "../ColdDepthClient";

const DOOR_OPEN = "0f6c1a52-6f1d-4c6b-9a43-0d9d3b6d2a10";
const DOOR_CLOSE = "1a2b3c4d-5e6f-4a1b-8c2d-3e4f5a6b7c8d";
const GRID = "2b3c4d5e-6f70-4b2c-9d3e-4f5a6b7c8d9e";
const PROBE = "3c4d5e6f-7081-4c3d-ae4f-5a6b7c8d9eaf";
const Q = "from=2026-10-06T19%3A00%3A00Z&to=2026-10-06T20%3A05%3A00Z";

/** A C1 backup-failed shaped `/cold/cooling` answer (exact keys of the C1 "Cooling payload" table). */
function coolingBody(overrides: Record<string, unknown> = {}, cooling: Record<string, unknown> = {}) {
  return {
    schema_version: "cold-depth-1",
    site_id: "7d1e2f30-4a5b-4c6d-8e7f-901a2b3c4d5e",
    window: {
      from: "2026-10-06T19:00:00Z",
      to: "2026-10-06T20:05:00Z",
      known_at: "2026-10-22T08:00:00.123456Z",
      committed_watermark: "2026-10-22T08:00:00.123456Z",
    },
    selection: {
      state: "CURRENT",
      assessment_revision_ids: ["4d5e6f70-8192-4d4e-bf50-6b7c8d9eafb0"],
      accepted_evidence_ids: [DOOR_OPEN, DOOR_CLOSE, GRID, PROBE].sort(),
      source_provenance: { classification: "SIMULATED_REPLAY", source_ids: [], evidence_ids: [], basis_sha256: null },
    },
    cooling: {
      recovery_state: "LIMITED",
      policy_high_deg_c: "4",
      selected_points: [{ role: "chamber_temperature", source_time: "2026-10-06T19:20:00Z", evidence_ids: [PROBE] }],
      observed_restart_at: null,
      observed_return_to_policy_at: null,
      duration_lower_seconds: null,
      duration_upper_seconds: null,
      comparison_state: "CONTEXT_MISSING",
      context: [
        { label: "Ambient temperature", state: "Unknown", evidence_ids: [], duration_seconds: null },
        { label: "Power availability", state: "Observed", evidence_ids: [GRID], duration_seconds: null },
        { label: "Door-open duration", state: "Observed", evidence_ids: [DOOR_OPEN, DOOR_CLOSE].sort(), duration_seconds: 60 },
        { label: "Loading / batch", state: "Unknown", evidence_ids: [], duration_seconds: null },
        { label: "Defrost", state: "Unknown", evidence_ids: [], duration_seconds: null },
      ],
      ...cooling,
    },
    links: {
      temperature: `/api/sites/COLD-LAB-001/cold/temperature?${Q}`,
      backup: `/api/sites/COLD-LAB-001/cold/backup-chain?${Q}`,
      evidence: `/api/sites/COLD-LAB-001/cold/evidence?${Q}`,
      health: `/api/sites/COLD-LAB-001/cold/health?${Q}`,
    },
    ...overrides,
  };
}

const without = (value: Record<string, unknown>, key: string) => {
  const copy = { ...value };
  delete copy[key];
  return copy;
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("cooling_dto_and_labels", () => {
  it("accepts the exact C1 key sets in any order", () => {
    const body = coolingBody();
    expect(isColdCoolingRead(body)).toBe(true);
    const reordered: Record<string, unknown> = Object.fromEntries(Object.entries(body).reverse());
    reordered.cooling = Object.fromEntries(Object.entries(body.cooling).reverse());
    expect(isColdCoolingRead(reordered)).toBe(true);
    expect(isColdCoolingRead(coolingBody({}, { recovery_state: "CONTRADICTORY", policy_high_deg_c: null, selected_points: [] }))).toBe(true);
  });

  it("refuses a missing, extra or ill-typed key at every level as malformed", () => {
    const body = coolingBody();
    const bad: unknown[] = [
      without(body, "links"),
      { ...body, extra: 1 },
      { ...body, schema_version: "cold-depth-2" },
      { ...body, window: { ...body.window, committed_watermark: 7 } },
      { ...body, window: without(body.window, "known_at") },
      { ...body, selection: { ...body.selection, state: "SELECTED" } },
      { ...body, selection: { ...body.selection, accepted_evidence_ids: null } },
      { ...body, selection: { ...body.selection, source_provenance: null } },
      { ...body, links: { ...body.links, cooling: null } },
      { ...body, links: { ...body.links, health: 3 } },
      coolingBody({}, { recovery_state: "CURRENT" }),
      coolingBody({}, { policy_high_deg_c: 4 }),
      coolingBody({}, { observed_restart_at: "2026-10-06T19:30:00Z" }),
      coolingBody({}, { duration_lower_seconds: 0 }),
      coolingBody({}, { duration_upper_seconds: 2520 }),
      coolingBody({}, { comparison_state: "MATCHED" }),
      coolingBody({}, { extra: null }),
      coolingBody({}, { selected_points: [{ role: "x", source_time: "t" }] }),
      coolingBody({}, { context: body.cooling.context.slice(0, 4) }),
      coolingBody({}, { context: [...body.cooling.context].reverse() }),
      coolingBody({}, { context: body.cooling.context.map((r) => ({ ...r, state: r.state === "Observed" ? "Matched" : r.state })) }),
      coolingBody({}, { context: body.cooling.context.map((r, i) => (i === 0 ? { ...r, duration_seconds: 0 } : r)) }),
      coolingBody({}, { context: body.cooling.context.map((r, i) => (i === 2 ? { ...r, duration_seconds: 60.5 } : r)) }),
      coolingBody({}, { context: body.cooling.context.map((r, i) => (i === 0 ? { ...r, evidence_ids: [GRID] } : r)) }),
      coolingBody({}, { context: body.cooling.context.map((r, i) => (i === 1 ? without(r, "duration_seconds") : r)) }),
      [],
      null,
    ];
    for (const value of bad) expect(isColdCoolingRead(value)).toBe(false);
    expect(COOLING_CONTEXT_LABELS).toEqual(["Ambient temperature", "Power availability", "Door-open duration", "Loading / batch", "Defrost"]);
  });

  it("reads through the live route address and names a malformed 200 and a refusal", async () => {
    const calls: string[] = [];
    let answer: { body: unknown; status: number } = { body: coolingBody(), status: 200 };
    vi.stubGlobal("fetch", async (path: string) => {
      calls.push(path);
      return new Response(JSON.stringify(answer.body), { status: answer.status });
    });
    const client = createColdDepthClient();
    const window = { from: "2026-10-06T19:00:00Z", to: "2026-10-06T20:05:00Z", known_at: "2026-10-22T08:00:00Z" };
    expect((await client.getCooling("COLD LAB/1", window)).status).toBe("loaded");
    expect(calls[0]).toBe(
      "/api/sites/COLD%20LAB%2F1/cold/cooling?from=2026-10-06T19%3A00%3A00Z&to=2026-10-06T20%3A05%3A00Z&known_at=2026-10-22T08%3A00%3A00Z",
    );
    answer = { body: coolingBody({}, { context: [] }), status: 200 };
    expect(await client.getCooling("COLD-LAB-001", NO_WINDOW)).toEqual({
      status: "unavailable",
      message: "The cold depth read answered in an unexpected shape.",
    });
    expect(calls[1]).toBe("/api/sites/COLD-LAB-001/cold/cooling");
    answer = { body: { error: { code: "COLD_SOURCE_DISCLOSURE_FORBIDDEN", message: "Source disclosure is not permitted." } }, status: 403 };
    expect(await client.getCooling("COLD-LAB-001", NO_WINDOW)).toEqual({
      status: "refused",
      httpStatus: 403,
      code: "COLD_SOURCE_DISCLOSURE_FORBIDDEN",
      message: "Source disclosure is not permitted.",
    });
  });

  it("labels the first two cards from policy_high_deg_c verbatim, or back to policy when null", () => {
    expect(coolingCardLabels("4")).toEqual({ usual: "Usual time back to 4°C", current: "This time back to 4°C" });
    expect(coolingCardLabels("3.5")).toEqual({ usual: "Usual time back to 3.5°C", current: "This time back to 3.5°C" });
    expect(coolingCardLabels(null)).toEqual({ usual: "Usual time back to policy", current: "This time back to policy" });
  });
});
