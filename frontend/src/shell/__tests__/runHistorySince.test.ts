import { afterEach, describe, expect, it, vi } from "vitest";

import { createRunSetupClient } from "../runSetupClient";
import wire from "./kobo-mini-grid-history-deltas.json";

/**
 * The live-follow read (T025e), against responses rather than a fake: how the
 * route's answer becomes an outcome. A delta is `loaded` only with its
 * envelope; a typed refusal is `refused` with its code, so the caller can
 * answer it with one full read; anything else is `unavailable`.
 */

const RUNS_PATH = "/api/simulator-lab/runs";
const RUN_ID = "run-1f0c2b7a4e5d4c8fa1b2c3d4e5f60718";
const client = () =>
  createRunSetupClient("/api/simulator-lab/run-profiles", RUNS_PATH);

const DELTA = (wire as unknown as { deltas: { history: unknown; delta: unknown }[] })
  .deltas[3];

function respondWith(body: unknown, status = 200): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        ok: status >= 200 && status < 300,
        status,
        json: () => Promise.resolve(body),
      } as unknown as Response),
    ),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("getExecutionHistorySince", () => {
  it("asks the history route for what was recorded after the count held", async () => {
    respondWith(DELTA);

    const result = await client().getExecutionHistorySince(RUN_ID, 3);

    expect(fetch).toHaveBeenCalledWith(
      `${RUNS_PATH}/${RUN_ID}/execution/history?since_boundary=3`,
    );
    expect(result).toEqual({
      status: "loaded",
      history: DELTA.history,
      delta: { since_boundary: 3, through_boundary: 4 },
    });
  });

  it("is unavailable when the answer has no envelope", async () => {
    respondWith({ history: DELTA.history });

    const result = await client().getExecutionHistorySince(RUN_ID, 3);

    expect(result).toEqual({ status: "unavailable", message: null });
  });

  it("carries a typed refusal's code and message", async () => {
    respondWith(
      {
        detail: {
          code: "HISTORY_SINCE_AHEAD",
          message: "This run has recorded 3 boundaries.",
        },
      },
      409,
    );

    const result = await client().getExecutionHistorySince(RUN_ID, 9);

    expect(result).toEqual({
      status: "refused",
      code: "HISTORY_SINCE_AHEAD",
      message: "This run has recorded 3 boundaries.",
    });
  });

  it("carries a malformed-count refusal the same way", async () => {
    respondWith(
      { detail: { code: "EXECUTION_REQUEST_INVALID", message: "Not a count." } },
      422,
    );

    expect(await client().getExecutionHistorySince(RUN_ID, -1)).toEqual({
      status: "refused",
      code: "EXECUTION_REQUEST_INVALID",
      message: "Not a count.",
    });
  });

  it("is not found for an unknown run and unavailable when nothing arrives", async () => {
    respondWith({ detail: "Not Found" }, 404);
    expect(await client().getExecutionHistorySince(RUN_ID, 0)).toEqual({
      status: "not_found",
    });

    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new TypeError("Failed to fetch"))),
    );
    expect(await client().getExecutionHistorySince(RUN_ID, 0)).toEqual({
      status: "unavailable",
      message: null,
    });

    respondWith({ detail: { message: "Down." } }, 503);
    expect(await client().getExecutionHistorySince(RUN_ID, 0)).toEqual({
      status: "unavailable",
      message: "Down.",
    });
  });
});
