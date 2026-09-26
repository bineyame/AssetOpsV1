import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createRunSetupClient,
  type RunSetupInput,
  type RunSummary,
} from "../runSetupClient";

/**
 * The run setup client, against responses rather than against a fake.
 *
 * Every other test in this round supplies a `RunSetupClient` that already
 * returns a well-formed outcome, which is the right way to test a screen and
 * proves nothing about what the real client does with a response. That gap
 * was the point: the two review findings this file exists for - a 201 whose
 * body cannot be read, and a 503 whose message was discarded - are both about
 * how a RESPONSE becomes an outcome, and nothing measured that. A defect in
 * exactly that area survived the round and was found by the next reviewer
 * reading the code.
 *
 * The rule being held here is the one the module states. The four outcomes
 * are four facts, and the one that matters most is the difference between
 * "the request did not complete, nothing was written" and "a run exists and
 * this client could not read it". Collapsing those puts "Nothing was written"
 * on screen over a persisted Draft.
 */

const PROFILES_PATH = "/api/simulator-lab/run-profiles";
const RUNS_PATH = "/api/simulator-lab/runs";

const client = () => createRunSetupClient(PROFILES_PATH, RUNS_PATH);

const RUN: RunSummary = {
  run_id: "run-1f0c2b7a4e5d4c8fa1b2c3d4e5f60718",
  lifecycle_status: "DRAFT",
  execution_status: "BLOCKED",
  readiness_disclosure: null,
  created_at: "2026-09-22T09:00:00Z",
  site_id: "MG-001",
  scenario_id: "fuel-loss-event",
  scenario_version: 1,
  frozen_inputs: [
    {
      identity_field: "site",
      field: "Site",
      value: "MG-001",
      answered_by: "SITE_FOUNDATION",
      answered_by_detail: "site MG-001 foundation version 1",
      blocking_statement: null,
    },
  ],
  blocking_reasons: [
    {
      kind: "STATE_NOT_SUPPORTED",
      subject: "site-load-demand",
      statement: "The selected model profile does not model site-load-demand.",
    },
  ],
  unsupported_optional_inputs: [],
};

const INPUT: RunSetupInput = {
  site_id: "MG-001",
  foundation_version: 1,
  scenario_id: "fuel-loss-event",
  scenario_version: 1,
  interval: {
    start_time: "2026-09-21T00:00:00Z",
    end_time: "2026-09-22T17:00:00Z",
  },
  timestep_minutes: 15,
  seed: 20260921,
  model_profile: { profile_id: "minimal-fuel-tank", profile_version: 1 },
  publication_profile: {
    profile_id: "simulator-lab-publication",
    profile_version: 1,
  },
  run_inputs: [],
};

/** One response in front of the next `fetch`. */
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

/** A response whose body is not JSON at all, as a real one can be. */
function respondWithUnreadableBody(status: number): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        ok: status >= 200 && status < 300,
        status,
        json: () =>
          Promise.reject(new SyntaxError("Unexpected end of JSON input")),
      } as unknown as Response),
    ),
  );
}

function refuseToSend(): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.reject(new TypeError("Failed to fetch"))),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("the versioned profiles are read", () => {
  const BODY = {
    model_profiles: [
      {
        model_profile_id: "minimal-fuel-tank",
        model_profile_version: 1,
        display_name: "Minimal fuel tank model",
        statement: "Models the stored volume.",
        supported_states: [
          {
            state_key: "fuel-tank-volume",
            scope: "COMPONENT",
            supported_roles: ["CAUSAL_INPUT"],
            statement: "The stored volume can be caused.",
          },
        ],
      },
    ],
    publication_profiles: [
      {
        publication_profile_id: "simulator-lab-publication",
        publication_profile_version: 1,
        display_name: "Simulator Lab publication profile",
        statement: "Declares the cadence.",
        device_signal_cadence_minutes: 15,
        simulator_source_id: "simulator-lab-source",
        gateway_id: "simulator-lab-gateway",
      },
    ],
  };

  it("reads them from the path it was built with", async () => {
    respondWith(BODY);

    const result = await client().listProfiles();

    expect(fetch).toHaveBeenCalledWith(PROFILES_PATH);
    expect(result).toEqual({
      status: "loaded",
      modelProfiles: BODY.model_profiles,
      publicationProfiles: BODY.publication_profiles,
    });
  });

  it("keeps an undeclared value as null rather than dropping it", async () => {
    // `null` is a real answer: nobody has declared that input, which is what
    // blocks a run. A client that dropped it would turn a blocking fact into
    // a missing field.
    respondWith({
      ...BODY,
      publication_profiles: [
        { ...BODY.publication_profiles[0], gateway_id: null },
      ],
    });

    const result = await client().listProfiles();

    expect(result.status).toBe("loaded");
    expect(
      result.status === "loaded"
        ? result.publicationProfiles[0].gateway_id
        : "unreachable",
    ).toBeNull();
  });

  it.each([
    ["a body of the wrong shape", { model_profiles: [{}] }, 200],
    ["a body that is not an object", "profiles", 200],
    ["a server failure", { detail: "nope" }, 503],
  ])("is unavailable for %s", async (_name, body, status) => {
    respondWith(body, status);

    expect(await client().listProfiles()).toEqual({ status: "unavailable" });
  });

  it("is unavailable when the request never arrives", async () => {
    refuseToSend();

    expect(await client().listProfiles()).toEqual({ status: "unavailable" });
  });
});

describe("a setup request is sent as the backend expects it", () => {
  it("posts the input as JSON to the runs path", async () => {
    respondWith({ run: RUN }, 201);

    await client().createRun(INPUT);

    expect(fetch).toHaveBeenCalledWith(RUNS_PATH, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(INPUT),
    });
  });

  it("serializes an unfilled number as null rather than omitting it", async () => {
    // The screen sends `NaN` for text that is not a number, and the backend
    // refuses `null` with the rule it broke. A client that dropped the key
    // would turn "not a number" into "missing", which is a different refusal
    // about a field the person did fill in.
    respondWith({ run: RUN }, 201);

    await client().createRun({ ...INPUT, seed: Number.NaN });

    const body = JSON.parse(
      (vi.mocked(fetch).mock.calls[0][1] as { body: string }).body,
    ) as Record<string, unknown>;
    expect("seed" in body).toBe(true);
    expect(body.seed).toBeNull();
  });
});

describe("what a response becomes", () => {
  it("a 201 with a readable run is created", async () => {
    respondWith({ run: RUN }, 201);

    expect(await client().createRun(INPUT)).toEqual({
      status: "created",
      run: RUN,
    });
  });

  it("a 201 whose run does not match the shape is created, not lost", async () => {
    // The finding this file exists for. A run EXISTS; saying otherwise is
    // the worst sentence this surface can produce.
    respondWith({ run: { run_id: "run-1" } }, 201);

    expect(await client().createRun(INPUT)).toEqual({
      status: "created_but_unreadable",
    });
  });

  it("a 201 with no JSON body at all is created, not lost", async () => {
    respondWithUnreadableBody(201);

    expect(await client().createRun(INPUT)).toEqual({
      status: "created_but_unreadable",
    });
  });

  it("a 422 is a refusal carrying the backend's code, kind and copy", async () => {
    respondWith(
      {
        detail: {
          code: "RUN_INTERVAL_INVALID",
          refusal_kind: "INTERVAL_INVALID",
          run_created: false,
          message: "Entry generator-run-window runs until 1320 minutes.",
        },
      },
      422,
    );

    expect(await client().createRun(INPUT)).toEqual({
      status: "refused",
      code: "RUN_INTERVAL_INVALID",
      refusalKind: "INTERVAL_INVALID",
      message: "Entry generator-run-window runs until 1320 minutes.",
    });
  });

  it("a 422 with nothing to read is still a refusal", async () => {
    respondWithUnreadableBody(422);

    expect(await client().createRun(INPUT)).toEqual({
      status: "refused",
      code: null,
      refusalKind: null,
      message: "The run setup request was refused.",
    });
  });

  it("a 503 carries the message naming the store that failed", async () => {
    // The second finding this file exists for. The message is the only thing
    // that says WHICH store could not be reached, and a screen that replaced
    // it with a generic sentence would be writing a worse version of a fact
    // the backend already stated.
    respondWith(
      {
        detail: {
          code: "RUN_STORE_UNAVAILABLE",
          message:
            "The run store could not be written: var/runs. Nothing was written.",
        },
      },
      503,
    );

    expect(await client().createRun(INPUT)).toEqual({
      status: "unavailable",
      message:
        "The run store could not be written: var/runs. Nothing was written.",
    });
  });

  it("a 503 with no message is unavailable with none", async () => {
    respondWith({ detail: "a string, not an object" }, 503);

    expect(await client().createRun(INPUT)).toEqual({
      status: "unavailable",
      message: null,
    });
  });

  it("a request that never arrives wrote nothing", async () => {
    refuseToSend();

    expect(await client().createRun(INPUT)).toEqual({
      status: "unavailable",
      message: null,
    });
  });

  it("never reports a created run as unavailable", async () => {
    // The two outcomes, stated as the property rather than as two cases: no
    // 201 may produce an outcome whose copy says nothing was written.
    for (const body of [
      { run: RUN },
      { run: { run_id: "run-1" } },
      { nothing: true },
    ]) {
      respondWith(body, 201);
      const result = await client().createRun(INPUT);
      expect(["created", "created_but_unreadable"]).toContain(result.status);
      vi.unstubAllGlobals();
    }
  });
});
