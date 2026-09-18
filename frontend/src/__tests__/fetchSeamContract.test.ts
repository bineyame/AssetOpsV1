import { afterEach, describe, expect, it, vi } from "vitest";

import fixture from "../../../contract-fixtures/site-foundation-fetch-seam.json";

import {
  SITES_API_PATH,
  createSiteDirectoryClient,
} from "../sites/siteDirectoryClient";
import {
  type CreateSiteInput,
  createSiteCreationClient,
} from "../shell/siteCreationClient";
import { createSiteTemplateCatalogClient } from "../shell/siteTemplateCatalogClient";

/**
 * The frontend half of the Site Foundation fetch seam.
 *
 * The other half is `backend/tests/test_fetch_seam_contract.py`, which drives
 * the real application and writes what every endpoint actually returns into
 * `contract-fixtures/site-foundation-fetch-seam.json`. This file reads that
 * same fixture back and puts the real clients in front of it.
 *
 * Neither side imports the other. The fixture is the only crossing, which is
 * what keeps `tools/checks/dependency-direction.ps1` intact.
 *
 * What this proves that nothing else did. Backend API tests prove what the
 * backend sends. UI tests inject fakes, so they prove what a screen does with a
 * body somebody wrote by hand. Between T006 and T009 nothing proved those two
 * agreed, and the failure mode is silent: a screen showing an empty list for an
 * unreadable store, or a generic failure where the backend sent renderable
 * refusal copy.
 *
 * The fixture cannot rot behind these assertions. A normal backend run fails
 * when the captured responses stop matching what the backend sends, so a
 * contract change breaks the generator before it can quietly teach this file
 * the wrong shape.
 */

interface FixtureCase {
  description: string;
  request: { method: string; path: string; body?: unknown };
  response: { status: number; body: unknown };
}

/**
 * Imported, not read from disk. Reading it needed `node:fs` and `process`,
 * which this project has no types for, and adding `@types/node` to typecheck
 * one test file is a worse trade than letting the bundler resolve the path.
 * The fixture stays outside both projects either way, so neither owns it.
 */
const FIXTURE = fixture as unknown as { cases: Record<string, FixtureCase> };

function fixtureCase(name: string): FixtureCase {
  const found = FIXTURE.cases[name];
  if (found === undefined) {
    throw new Error(
      `No case named ${name} in the fetch seam fixture. The backend generator ` +
        "names the cases; add it there rather than hand-writing a body here.",
    );
  }
  return found;
}

interface RecordedCall {
  url: string;
  init?: {
    method?: string;
    headers?: Record<string, string>;
    body?: string;
  };
}

/**
 * Put one captured response in front of the next `fetch`, and record the whole
 * request the client made.
 *
 * Both arguments are recorded, not just the URL. An earlier version took only
 * `input`, which meant the create tests could pass while the client stopped
 * sending `POST`, dropped its JSON body, or sent the wrong identity: the fake
 * would answer 201 regardless, and the real backend would not. Half a seam is
 * not a seam.
 *
 * Only `ok`, `status` and `json()` are modelled on the response, because that
 * is all the three clients read. A body of `null` throws from `json()`, which
 * is what a real empty or non-JSON response does and is how a malformed body
 * reaches a client.
 */
function serve(name: string): { calls: RecordedCall[] } {
  const { response } = fixtureCase(name);
  const calls: RecordedCall[] = [];

  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown, init?: unknown) => {
      calls.push({
        url: String(input),
        init: init as RecordedCall["init"],
      });
      return {
        ok: response.status >= 200 && response.status < 300,
        status: response.status,
        json: async () => {
          if (response.body === null) {
            throw new SyntaxError("Unexpected end of JSON input");
          }
          return response.body;
        },
      };
    }),
  );

  return { calls };
}

/**
 * Assert the client asked for exactly what the backend was asked for.
 *
 * The fixture records the method, path and body of every captured request, so
 * the request half of the contract is checked against the same source as the
 * response half rather than against literals written here.
 */
function expectRequestMatchedCapture(name: string, calls: RecordedCall[]): void {
  const { request } = fixtureCase(name);

  expect(calls).toHaveLength(1);
  const [call] = calls;

  expect(call.url).toBe(request.path);
  expect((call.init?.method ?? "GET").toUpperCase()).toBe(request.method);

  if (request.body === undefined) {
    expect(call.init?.body).toBeUndefined();
    return;
  }

  expect(JSON.parse(String(call.init?.body))).toEqual(request.body);
  expect(call.init?.headers?.["Content-Type"]).toBe("application/json");
}

/**
 * The create input, taken from the body the backend actually received for that
 * case. Binding the two means a create test cannot drift into asserting a
 * response the backend would never have sent for the request being made.
 */
function capturedCreateInput(name: string): CreateSiteInput {
  const { request } = fixtureCase(name);
  if (request.body === undefined) {
    throw new Error(`Case ${name} captured no request body.`);
  }
  return request.body as CreateSiteInput;
}

/** The base paths the app wires its clients with, spelled once. */
const TEMPLATES_BASE = "/api/simulator-lab/site-templates";
const CREATE_SITE_BASE = "/api/simulator-lab/sites";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("the fixture is the contract, not a convenience", () => {
  it("was generated by the backend and says how to regenerate it", () => {
    const fixture = FIXTURE as unknown as Record<string, unknown>;

    expect(fixture.generated_by).toBe(
      "backend/tests/test_fetch_seam_contract.py",
    );
    expect(String(fixture.regenerate_with)).toContain(
      "ASSETOPS_UPDATE_CONTRACT_FIXTURE=1",
    );
  });

  it("covers every case this file asserts against", () => {
    // Named here so that deleting a case from the generator fails loudly
    // rather than silently reducing what the seam covers.
    expect(Object.keys(FIXTURE.cases).sort()).toEqual([
      "create_site_created",
      "create_site_duplicate_identity",
      "create_site_invalid_request",
      "create_site_store_unavailable",
      "create_site_template_not_found",
      "gate_closed_create_site",
      "gate_closed_site_detail",
      "gate_closed_sites_list",
      "gate_closed_status",
      "gate_closed_template_detail",
      "gate_closed_template_list",
      "simulator_lab_status_enabled",
      "site_detail_loaded",
      "site_detail_not_found",
      "site_detail_store_unavailable",
      "sites_list_empty",
      "sites_list_loaded",
      "sites_list_store_unavailable",
      "template_detail_catalog_unavailable",
      "template_detail_loaded",
      "template_detail_not_found",
      "template_list_catalog_unavailable",
      "template_list_empty",
      "template_list_loaded",
    ]);
  });
});

describe("the Sites index client against real responses", () => {
  it("loads the configured Sites the backend sent", async () => {
    const { calls } = serve("sites_list_loaded");

    const result = await createSiteDirectoryClient().listSites();

    expectRequestMatchedCapture("sites_list_loaded", calls);
    expect(calls[0].url).toBe(SITES_API_PATH);
    expect(result.status).toBe("loaded");
    if (result.status !== "loaded") return;

    const captured = fixtureCase("sites_list_loaded").response.body as {
      sites: unknown[];
    };
    expect(result.sites).toEqual(captured.sites);
    expect(result.sites.length).toBeGreaterThan(0);
  });

  it("reads a first-run empty index as loaded and empty, never unavailable", async () => {
    const { calls } = serve("sites_list_empty");

    // The distinction this whole seam exists for. An empty store and an
    // unreadable one are different facts, and the index must not claim the
    // first when the second is true.
    expect(await createSiteDirectoryClient().listSites()).toEqual({
      status: "loaded",
      sites: [],
    });
    expectRequestMatchedCapture("sites_list_empty", calls);
  });

  it("reads an unreadable store as unavailable, never as an empty index", async () => {
    const { calls } = serve("sites_list_store_unavailable");

    expect(await createSiteDirectoryClient().listSites()).toEqual({
      status: "unavailable",
    });
    expectRequestMatchedCapture("sites_list_store_unavailable", calls);
  });
});

describe("the Site detail client against real responses", () => {
  it("loads a Site with its Foundation, including a component with no rating", async () => {
    const { calls } = serve("site_detail_loaded");

    const result = await createSiteDirectoryClient().getSite("MG-002");

    expectRequestMatchedCapture("site_detail_loaded", calls);
    expect(result.status).toBe("loaded");
    if (result.status !== "loaded") return;

    expect(result.site).toEqual(fixtureCase("site_detail_loaded").response.body);

    // The null-rating component is the case the guard added in T008 refuses to
    // infer: only an explicit null is the document declaring no rating.
    const ratings = result.site.foundation.components.map(
      (component) => component.rating,
    );
    expect(ratings).toContain(null);
    expect(ratings.some((rating) => rating !== null)).toBe(true);
  });

  it("reads an unknown Site as not found", async () => {
    const { calls } = serve("site_detail_not_found");

    expect(await createSiteDirectoryClient().getSite("MG-404")).toEqual({
      status: "not_found",
    });
    expectRequestMatchedCapture("site_detail_not_found", calls);
  });

  it("keeps an unreadable store distinct from a Site that is not configured", async () => {
    const { calls } = serve("site_detail_store_unavailable");

    expect(await createSiteDirectoryClient().getSite("MG-002")).toEqual({
      status: "unavailable",
    });
    expectRequestMatchedCapture("site_detail_store_unavailable", calls);
  });
});

describe("the template catalog client against real responses", () => {
  it("loads the shipped catalog", async () => {
    const { calls } = serve("template_list_loaded");

    const result =
      await createSiteTemplateCatalogClient(TEMPLATES_BASE).listTemplates();

    expectRequestMatchedCapture("template_list_loaded", calls);
    expect(calls[0].url).toBe(TEMPLATES_BASE);
    expect(result.status).toBe("loaded");
    if (result.status !== "loaded") return;

    const captured = fixtureCase("template_list_loaded").response.body as {
      templates: unknown[];
    };
    expect(result.templates).toEqual(captured.templates);
  });

  it("reads a build that ships no templates as loaded and empty", async () => {
    const { calls } = serve("template_list_empty");

    expect(
      await createSiteTemplateCatalogClient(TEMPLATES_BASE).listTemplates(),
    ).toEqual({ status: "loaded", templates: [] });
    expectRequestMatchedCapture("template_list_empty", calls);
  });

  it("reads an unreadable catalog as unavailable, never as an empty catalog", async () => {
    const { calls } = serve("template_list_catalog_unavailable");

    expect(
      await createSiteTemplateCatalogClient(TEMPLATES_BASE).listTemplates(),
    ).toEqual({ status: "unavailable" });
    expectRequestMatchedCapture("template_list_catalog_unavailable", calls);
  });

  it("loads one template's Foundation content", async () => {
    const { calls } = serve("template_detail_loaded");

    const result =
      await createSiteTemplateCatalogClient(TEMPLATES_BASE).getTemplate(
        "test-archetype",
      );

    expectRequestMatchedCapture("template_detail_loaded", calls);
    expect(result.status).toBe("loaded");
    if (result.status !== "loaded") return;

    expect(result.template).toEqual(
      fixtureCase("template_detail_loaded").response.body,
    );

    // A template is not a Site, and the response must not have acquired one's
    // fields on the way through.
    const asRecord = result.template as unknown as Record<string, unknown>;
    for (const field of ["site_id", "lifecycle_status", "location", "source"]) {
      expect(asRecord[field]).toBeUndefined();
    }
  });

  it("reads an unknown template identity as not found", async () => {
    const { calls } = serve("template_detail_not_found");

    expect(
      await createSiteTemplateCatalogClient(TEMPLATES_BASE).getTemplate(
        "no-such-template",
      ),
    ).toEqual({ status: "not_found" });
    expectRequestMatchedCapture("template_detail_not_found", calls);
  });

  it("keeps an unreadable catalog distinct from a template that does not exist", async () => {
    const { calls } = serve("template_detail_catalog_unavailable");

    expect(
      await createSiteTemplateCatalogClient(TEMPLATES_BASE).getTemplate(
        "test-archetype",
      ),
    ).toEqual({ status: "unavailable" });
    expectRequestMatchedCapture("template_detail_catalog_unavailable", calls);
  });
});

describe("the create client against real responses", () => {
  it("reads a created Site as the same summary shape the index accepts", async () => {
    const { calls } = serve("create_site_created");

    const result = await createSiteCreationClient(CREATE_SITE_BASE).createSite(
      capturedCreateInput("create_site_created"),
    );

    // The request half matters as much as the response half here: a 201 is
    // only meaningful if the client actually sent the POST and the body the
    // backend was answering.
    expectRequestMatchedCapture("create_site_created", calls);
    expect(calls[0].url).toBe(CREATE_SITE_BASE);
    expect(result.status).toBe("created");
    if (result.status !== "created") return;

    expect(result.site).toEqual(fixtureCase("create_site_created").response.body);
  });

  it.each([
    ["create_site_invalid_request", "a malformed identity"],
    ["create_site_duplicate_identity", "a Site ID already in use"],
    ["create_site_template_not_found", "an unknown template"],
    ["create_site_store_unavailable", "a store that could not be written"],
  ])(
    "renders the backend's own refusal copy for %s",
    async (name) => {
      const { calls } = serve(name);

      const result = await createSiteCreationClient(
        CREATE_SITE_BASE,
      ).createSite(capturedCreateInput(name));

      // Each refusal is the backend's answer to this exact request, so the
      // request is asserted too rather than assumed.
      expectRequestMatchedCapture(name, calls);

      expect(result.status).toBe("refused");
      if (result.status !== "refused") return;

      // Verbatim, not paraphrased. The backend is the only place that knows
      // why a create was refused, and T006 settled this copy at a checkpoint.
      const captured = fixtureCase(name).response.body as {
        detail: { message: string };
      };
      expect(result.message).toBe(captured.detail.message);
      expect(result.message.length).toBeGreaterThan(0);
    },
  );
});

describe("the closed gate, as the backend actually answers it", () => {
  it("leaves operator Site reads untouched", async () => {
    // The gate covers Lab surfaces and execution, never Site objects or
    // stores. These two responses are captured with the gate closed and must
    // be identical to the open-gate ones.
    expect(fixtureCase("gate_closed_sites_list").response).toEqual(
      fixtureCase("sites_list_loaded").response,
    );
    expect(fixtureCase("gate_closed_site_detail").response).toEqual(
      fixtureCase("site_detail_loaded").response,
    );

    const { calls } = serve("gate_closed_sites_list");
    const result = await createSiteDirectoryClient().listSites();
    expect(result.status).toBe("loaded");
    expectRequestMatchedCapture("gate_closed_sites_list", calls);
  });

  it("serves no Lab route at all", () => {
    for (const name of [
      "gate_closed_status",
      "gate_closed_template_list",
      "gate_closed_template_detail",
      "gate_closed_create_site",
    ]) {
      expect(fixtureCase(name).response.status).toBe(404);
    }
  });

  it("gives the template list client an unavailable catalog", async () => {
    const { calls } = serve("gate_closed_template_list");

    expect(
      await createSiteTemplateCatalogClient(TEMPLATES_BASE).listTemplates(),
    ).toEqual({ status: "unavailable" });
    expectRequestMatchedCapture("gate_closed_template_list", calls);
  });

  it("gives the template detail client a not-found template", async () => {
    const { calls } = serve("gate_closed_template_detail");

    // An unserved route and an unknown template are indistinguishable to this
    // client, because both are 404. That is acceptable only because a closed
    // gate serves no screen that could call it.
    expect(
      await createSiteTemplateCatalogClient(TEMPLATES_BASE).getTemplate(
        "test-archetype",
      ),
    ).toEqual({ status: "not_found" });
    expectRequestMatchedCapture("gate_closed_template_detail", calls);
  });

  it("gives the create client an unavailable store, not a refusal", async () => {
    const { calls } = serve("gate_closed_create_site");

    // FastAPI's own 404 body carries a string `detail`, not the product's
    // refusal envelope, so no renderable message can be read from it. Falling
    // back to `unavailable` rather than inventing one is the correct read.
    expect(
      await createSiteCreationClient(CREATE_SITE_BASE).createSite(
        capturedCreateInput("gate_closed_create_site"),
      ),
    ).toEqual({ status: "unavailable" });
    expectRequestMatchedCapture("gate_closed_create_site", calls);
  });
});

describe("a malformed body is never rendered as content", () => {
  it.each([
    ["sites_list_loaded", "the Sites index"],
    ["site_detail_loaded", "a Site page"],
  ])("refuses a truncated %s response", async (name) => {
    const { response } = fixtureCase(name);

    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: true,
        status: response.status,
        json: async () => {
          throw new SyntaxError("Unexpected end of JSON input");
        },
      })),
    );

    const directory = createSiteDirectoryClient();
    const result =
      name === "sites_list_loaded"
        ? await directory.listSites()
        : await directory.getSite("MG-002");

    expect(result).toEqual({ status: "unavailable" });
  });
});
