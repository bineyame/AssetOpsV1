import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createSiteDirectoryClient,
  isSiteDetail,
  SITES_API_PATH,
} from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { deriveSiteConfigurationView } from "../siteViewModel";

/**
 * The client, against responses rather than against a fake.
 *
 * Every other test in this tree supplies a client that already returns a
 * well-formed record, which is the right way to test a screen and the wrong
 * way to find out what the real client does with a response that is not one.
 * This file is the other side: what arrives over the wire is untrusted, and
 * the guard in the client is the only thing between it and a render.
 *
 * The rule being held here is the one the module states. A response that does
 * not match the expected shape is `unavailable` - a statement that the store
 * could not be read - and never a partially rendered site. "This site is not
 * configured", "the store could not be read", and "here is the site" stay
 * three different facts, so a 404 stays `not_found` and does not degrade into
 * either of the others.
 */

/** A well-formed detail response, as the API serves one. */
const SITE_DETAIL_BODY: SiteDetailReadModel = {
  site_id: "MG-002",
  display_name: "Kalangala Mini-Grid",
  site_type: "MINIGRID",
  location: { country: "Uganda", locality: "Kalangala" },
  timezone: "Africa/Kampala",
  lifecycle_status: "PLANNED",
  origin: "USER",
  source: { mode: "SIMULATED" },
  template: { template_id: "hybrid-mini-grid-100kw", template_version: 1 },
  foundation: {
    version: 1,
    valid_from: "2026-09-14T09:12:00Z",
    summary: "Solar-plus-storage mini-grid with a metered distribution load.",
    components: [
      {
        component_id: "pv-array",
        component_type: "PV_ARRAY",
        display_name: "PV array",
        rating: { value: 100, unit: "kW" },
      },
      {
        component_id: "site-meter",
        component_type: "METER",
        display_name: "Site meter",
        rating: null,
      },
    ],
  },
};

function bodyWithFoundation(foundation: unknown): unknown {
  return { ...SITE_DETAIL_BODY, foundation };
}

function bodyWithComponents(components: unknown): unknown {
  return bodyWithFoundation({ ...SITE_DETAIL_BODY.foundation, components });
}

/**
 * Bodies whose site fields are all correct and whose foundation is not, and
 * which break a render by throwing part-way through it.
 *
 * Each of these passed the guard as it stood before the configuration surface
 * read the foundation's content, because the guard checked the foundation's
 * version and validity and stopped there. Each one now reaches a render that
 * maps over `components`, and the map is where it fails.
 */
const SHAPES_THAT_THROW_WHILE_RENDERING: [string, unknown][] = [
  ["no foundation at all", { ...SITE_DETAIL_BODY, foundation: undefined }],
  ["a foundation that is not an object", bodyWithFoundation("v1")],
  ["no components key", bodyWithComponents(undefined)],
  ["components that are not an array", bodyWithComponents({})],
  ["a component that is not an object", bodyWithComponents(["pv-array"])],
  [
    "a component with no rating key",
    bodyWithComponents([
      {
        component_id: "pv-array",
        component_type: "PV_ARRAY",
        display_name: "PV array",
      },
    ]),
  ],
];

/**
 * Bodies that render without failing, and state something no record carries.
 *
 * These are the worse half. A render that throws is at least visibly broken;
 * these put `undefined` on a configuration screen as though the document said
 * it, which is the fabricated value every guard in this tree exists to stop.
 */
const SHAPES_THAT_FABRICATE_A_VALUE: [string, unknown][] = [
  [
    "no summary",
    bodyWithFoundation({
      version: 1,
      valid_from: "2026-09-14T09:12:00Z",
      components: [],
    }),
  ],
  [
    "a summary that is not a string",
    bodyWithFoundation({ ...SITE_DETAIL_BODY.foundation, summary: 3 }),
  ],
  [
    "a component with no display name",
    bodyWithComponents([
      { component_id: "pv-array", component_type: "PV_ARRAY", rating: null },
    ]),
  ],
  [
    "a rating that is a bare number",
    bodyWithComponents([
      {
        component_id: "pv-array",
        component_type: "PV_ARRAY",
        display_name: "PV array",
        rating: 100,
      },
    ]),
  ],
  [
    "a rating with no unit",
    bodyWithComponents([
      {
        component_id: "pv-array",
        component_type: "PV_ARRAY",
        display_name: "PV array",
        rating: { value: 100 },
      },
    ]),
  ],
];

const MALFORMED_DETAIL_BODIES: [string, unknown][] = [
  ...SHAPES_THAT_THROW_WHILE_RENDERING,
  ...SHAPES_THAT_FABRICATE_A_VALUE,
];

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

describe("one site is read from the operator sites path", () => {
  it("requests the site under its own site ID", async () => {
    respondWith(SITE_DETAIL_BODY);

    await createSiteDirectoryClient().getSite("MG-002");

    expect(fetch).toHaveBeenCalledWith(`${SITES_API_PATH}/MG-002`);
  });

  it("encodes a site ID rather than splicing it into the path", async () => {
    respondWith(SITE_DETAIL_BODY);

    await createSiteDirectoryClient().getSite("MG 002/extra");

    expect(fetch).toHaveBeenCalledWith(`${SITES_API_PATH}/MG%20002%2Fextra`);
  });

  it("loads the record a well-formed response carries", async () => {
    respondWith(SITE_DETAIL_BODY);

    const result = await createSiteDirectoryClient().getSite("MG-002");

    expect(result).toEqual({ status: "loaded", site: SITE_DETAIL_BODY });
  });
});

describe("a malformed detail response is unavailable, never half a site", () => {
  it.each(MALFORMED_DETAIL_BODIES)(
    "refuses a response with %s",
    async (_description, body) => {
      respondWith(body);

      const result = await createSiteDirectoryClient().getSite("MG-002");

      expect(isSiteDetail(body)).toBe(false);
      expect(result).toEqual({ status: "unavailable" });
    },
  );

  it("states an unreadable store rather than an unconfigured site", async () => {
    respondWith(bodyWithComponents(undefined));

    const result = await createSiteDirectoryClient().getSite("MG-002");

    // Not `not_found`. Nothing about this response says the site is not
    // configured; what is true is that the store could not be read.
    expect(result.status).toBe("unavailable");
  });

  it.each(SHAPES_THAT_THROW_WHILE_RENDERING)(
    "refuses %s, which would otherwise throw mid-render",
    (_description, body) => {
      // The guard is load-bearing rather than decorative. Without it the view
      // derives straight off the body and fails part-way through a render,
      // which is a broken screen rather than a stated refusal.
      expect(() =>
        deriveSiteConfigurationView(body as SiteDetailReadModel),
      ).toThrow();
    },
  );

  it.each(SHAPES_THAT_FABRICATE_A_VALUE)(
    "refuses %s, which would otherwise render a value no record carries",
    (_description, body) => {
      const view = deriveSiteConfigurationView(body as SiteDetailReadModel);
      const rendered: unknown[] = [
        view.foundationSummary,
        ...view.components.flatMap((component) => [
          component.displayName,
          component.componentType,
          component.rating,
        ]),
      ];

      expect(
        rendered.some(
          (value) => typeof value !== "string" || value.includes("undefined"),
        ),
      ).toBe(true);
    },
  );

  it("refuses a body whose site fields are wrong under a good foundation", async () => {
    respondWith({ ...SITE_DETAIL_BODY, site_id: 2 });

    const result = await createSiteDirectoryClient().getSite("MG-002");

    expect(result).toEqual({ status: "unavailable" });
  });
});

describe("the three outcomes of a read stay three", () => {
  it("states not found for a site the store does not have", async () => {
    respondWith({ detail: "no such site" }, 404);

    const result = await createSiteDirectoryClient().getSite("MG-404");

    expect(result).toEqual({ status: "not_found" });
  });

  it("states unavailable when the store itself fails", async () => {
    respondWith({ detail: "boom" }, 500);

    const result = await createSiteDirectoryClient().getSite("MG-002");

    expect(result).toEqual({ status: "unavailable" });
  });

  it("states unavailable when the request never lands", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new Error("network down"))),
    );

    const result = await createSiteDirectoryClient().getSite("MG-002");

    expect(result).toEqual({ status: "unavailable" });
  });

  it("states unavailable when the body is not JSON", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.reject(new SyntaxError("not JSON")),
        } as unknown as Response),
      ),
    );

    const result = await createSiteDirectoryClient().getSite("MG-002");

    expect(result).toEqual({ status: "unavailable" });
  });
});

describe("the index refuses a malformed list the same way", () => {
  it("loads the sites a well-formed list carries", async () => {
    respondWith({ sites: [SITE_DETAIL_BODY] });

    const result = await createSiteDirectoryClient().listSites();

    expect(result).toEqual({ status: "loaded", sites: [SITE_DETAIL_BODY] });
  });

  it("refuses a list holding anything that is not a site", async () => {
    respondWith({ sites: [SITE_DETAIL_BODY, { site_id: "MG-003" }] });

    const result = await createSiteDirectoryClient().listSites();

    // Not a shortened index. One unreadable row makes the read unavailable,
    // because an index missing a site states that the site is not configured.
    expect(result).toEqual({ status: "unavailable" });
  });

  it("refuses a body with no sites key", async () => {
    respondWith({});

    const result = await createSiteDirectoryClient().listSites();

    expect(result).toEqual({ status: "unavailable" });
  });
});
