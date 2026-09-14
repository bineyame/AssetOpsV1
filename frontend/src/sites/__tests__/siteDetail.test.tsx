import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SiteDetails } from "../SiteDetails";
import type { SiteDetailClient } from "../siteDirectoryClient";
import type {
  SiteDetailReadModel,
  SiteDetailResult,
} from "../siteReadModel";
import { deriveSiteDetailView } from "../siteViewModel";
import { settledScreen } from "../../test/settled";

/**
 * Tests for one site, presented from the shared substrate.
 *
 * The substrate is rendered directly here, over records, with no shell and no
 * router around it. That is the point: nothing in `frontend/src/sites/` may
 * depend on which shell is rendering it, so nothing in these tests supplies a
 * shell, a mode, or a flag.
 *
 * Two things carry the weight. Independence: the six provenance-and-status
 * concepts must render as six facts, and the two combinations M1 cannot reach
 * must each render both of their facts correctly, so neither can have been
 * implemented as a derivation. And honesty: a configuration-only site has no
 * evidence, so the page must state that rather than render a zero, an empty
 * chart, a flat series, a health state, or a timestamp it does not have.
 */

const USER_SIMULATED_SITE: SiteDetailReadModel = {
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
    summary:
      "Solar-plus-storage mini-grid with a diesel generator for backup and a " +
      "metered distribution load.",
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

/** `USER` with `LIVE`: a site registered against a real integration. */
const USER_LIVE_SITE: SiteDetailReadModel = {
  ...USER_SIMULATED_SITE,
  site_id: "MG-003",
  display_name: "Buvuma Mini-Grid",
  lifecycle_status: "ACTIVE",
  source: { mode: "LIVE" },
};

/** `SHIPPED` with `SIMULATED`: a shipped demo site, from no template. */
const SHIPPED_SIMULATED_SITE: SiteDetailReadModel = {
  site_id: "CC-001",
  display_name: "Mbale Cold Room",
  site_type: "COLDCHAIN",
  location: { country: "Uganda", locality: "Mbale" },
  timezone: "Africa/Kampala",
  lifecycle_status: "COMMISSIONED",
  origin: "SHIPPED",
  source: { mode: "SIMULATED" },
  template: null,
  foundation: {
    version: 2,
    valid_from: "2026-08-01T00:00:00Z",
    summary: "Single cold room with a metered supply.",
    components: [
      {
        component_id: "cold-room",
        component_type: "COLD_ROOM",
        display_name: "Cold room",
        rating: { value: 30, unit: "kWh" },
      },
    ],
  },
};

const INTERACTIVE_SELECTOR = [
  "a[href]",
  "button",
  "input",
  "select",
  "textarea",
  "form",
  "details",
  "summary",
  "[onclick]",
  "[role='button']",
  "[role='link']",
  "[role='menuitem']",
  "[role='tab']",
  "[contenteditable='true']",
].join(", ");

/**
 * The controls the mockups show on canonical screen 2 that this slice does not
 * render in any state. Deferred by decision, so absent from the DOM rather
 * than disabled: disabled reads as "soon", and none of these is coming.
 */
const ABSENT_CONTROL_LABELS = [
  "Edit",
  "Edit Configuration",
  "Version History",
  "Duplicate Site",
  "Delete Site",
  "Save",
  "Publish",
  "Rename",
  "Change",
];

/** Quick Actions belongs to canonical screen 2 chrome and arrives with it. */
const ABSENT_QUICK_ACTION_LABELS = [
  "Open in Simulator Lab",
  "Start Simulation",
  "View Live Data",
];

const FORBIDDEN_ACTION_PATTERN =
  /\b(edit|save|publish|rename|duplicate|clone|delete|remove|archive|approve|diff|history|rollback|revert)\b/i;

/** Source health vocabulary, which must not appear where no health exists. */
const SOURCE_HEALTH_VOCABULARY = /\b(online|offline|stale|degraded|healthy)\b/i;

function clientFor(result: SiteDetailResult): SiteDetailClient {
  return { getSite: () => Promise.resolve(result) };
}

function renderSite(site: SiteDetailReadModel, siteId = site.site_id) {
  return render(
    <SiteDetails
      siteId={siteId}
      detail={clientFor({ status: "loaded", site })}
    />,
  );
}

/** Every digit run in a string, so screen values can be traced to a record. */
function digitRuns(text: string): string[] {
  return text.match(/\d+(?:\.\d+)?/g) ?? [];
}

/** The value rendered against one term in a definition list. */
function factValue(container: HTMLElement, term: string): string {
  const terms = Array.from(container.querySelectorAll("dt"));
  const match = terms.find((entry) => entry.textContent === term);

  expect(match, `no fact named ${term}`).toBeDefined();
  return (match as HTMLElement).nextElementSibling?.textContent ?? "";
}

describe("a site is rendered from its record", () => {
  it("shows the identity, configuration, and provenance the record carries", async () => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    expect(
      screen.getByRole("heading", { level: 1, name: "Kalangala Mini-Grid" }),
    ).toBeInTheDocument();
    expect(factValue(container, "Site ID")).toBe("MG-002");
    expect(factValue(container, "Name")).toBe("Kalangala Mini-Grid");
    expect(factValue(container, "Type")).toBe("Mini-grid");
    expect(factValue(container, "Location")).toBe("Kalangala, Uganda");
    expect(factValue(container, "Timezone")).toBe("Africa/Kampala");
    expect(factValue(container, "Lifecycle status")).toBe("Planned");
    expect(factValue(container, "Mode")).toBe("Simulated");
    expect(factValue(container, "Configuration origin")).toBe("User");
    expect(factValue(container, "Created from template")).toBe(
      "hybrid-mini-grid-100kw v1",
    );
    expect(factValue(container, "Foundation version")).toBe("1");
    expect(factValue(container, "Valid from")).toBe("2026-09-14T09:12:00Z");
  });

  it("renders the stored canonical site ID, not the one in the address", async () => {
    // A case variant addresses the same site, because identity is compared
    // without regard to case. One site must never present as two, so what is
    // rendered is what the store holds.
    const { container } = renderSite(USER_SIMULATED_SITE, "mg-002");
    await settledScreen();

    expect(factValue(container, "Site ID")).toBe("MG-002");
    expect(container.textContent).not.toMatch(/mg-002/);
  });

  it("says plainly when a site came from no template", async () => {
    const { container } = renderSite(SHIPPED_SIMULATED_SITE);
    await settledScreen();

    expect(factValue(container, "Created from template")).toBe(
      "Not created from a template",
    );
  });

  it("renders no digit the record does not supply", async () => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    // This replaces the "no digits inside `<main>`" rule that the empty T002
    // frame carried. It is stricter, not looser: digits may appear, and every
    // one of them must trace to the record under test.
    const fromRecord = new Set(digitRuns(JSON.stringify(USER_SIMULATED_SITE)));
    const onScreen = digitRuns(container.textContent ?? "");

    expect(onScreen.length).toBeGreaterThan(0);
    for (const value of onScreen) {
      expect(fromRecord).toContain(value);
    }
  });

  it("renders the site's own timestamp verbatim and invents no other", async () => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    const timestamps =
      (container.textContent ?? "").match(
        /\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2})?Z?)?/g,
      ) ?? [];

    expect(timestamps).toEqual(["2026-09-14T09:12:00Z"]);
  });
});

describe("the site is addressed by site ID and nothing else", () => {
  it("states not found for a site that is not configured", async () => {
    render(
      <SiteDetails siteId="MG-404" detail={clientFor({ status: "not_found" })} />,
    );

    expect(
      await screen.findByRole("heading", { level: 2, name: "No such site" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/No site with that site ID is configured/i),
    ).toBeInTheDocument();
  });

  it("renders no site at all when the site is not found", async () => {
    const { container } = render(
      <SiteDetails siteId="MG-404" detail={clientFor({ status: "not_found" })} />,
    );
    await screen.findByRole("heading", { level: 2, name: "No such site" });

    // Not found is a refusal, never a site with empty fields.
    expect(container.querySelectorAll("dl")).toHaveLength(0);
    expect(container.textContent).not.toMatch(/Lifecycle status/i);
    expect(container.textContent).not.toMatch(/Configuration origin/i);
  });

  it("names no site when the address identifies none", async () => {
    render(
      <SiteDetails
        siteId={undefined}
        detail={clientFor({ status: "loaded", site: USER_SIMULATED_SITE })}
      />,
    );

    expect(
      await screen.findByRole("heading", { level: 2, name: "No such site" }),
    ).toBeInTheDocument();
  });

  it("drops the site on screen the moment the address names another", async () => {
    // Navigation from one site URL to another. The second read is still in
    // flight when the assertions run, which is the whole point: the site from
    // the previous address must not still be standing under the new one, or
    // /sites/MG-404 briefly presents MG-002 as the site it addresses.
    let answerSecond: (result: SiteDetailResult) => void = () => {};
    const detail: SiteDetailClient = {
      getSite: (siteId) =>
        siteId === USER_SIMULATED_SITE.site_id
          ? Promise.resolve<SiteDetailResult>({
              status: "loaded",
              site: USER_SIMULATED_SITE,
            })
          : new Promise<SiteDetailResult>((resolve) => {
              answerSecond = resolve;
            }),
    };

    const { container, rerender } = render(
      <SiteDetails siteId="MG-002" detail={detail} />,
    );
    await settledScreen();
    expect(factValue(container, "Site ID")).toBe("MG-002");

    rerender(<SiteDetails siteId="MG-404" detail={detail} />);

    expect(container.textContent ?? "").not.toMatch(/MG-002|Kalangala/);
    expect(container.querySelectorAll("dl")).toHaveLength(0);
    expect(
      screen.getByText(/Loading the configured site\./),
    ).toBeInTheDocument();

    answerSecond({ status: "not_found" });

    expect(
      await screen.findByRole("heading", { level: 2, name: "No such site" }),
    ).toBeInTheDocument();
    expect(container.textContent ?? "").not.toMatch(/MG-002|Kalangala/);
  });

  it("states an unreadable store rather than an absent site", async () => {
    render(
      <SiteDetails
        siteId="MG-002"
        detail={clientFor({ status: "unavailable" })}
      />,
    );

    expect(
      await screen.findByRole("heading", { level: 2, name: "Site unavailable" }),
    ).toBeInTheDocument();
    expect(screen.queryByText(/No such site/i)).toBeNull();
  });
});

describe("the six provenance and status concepts are six facts", () => {
  it("renders each of the six separately", async () => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    expect(factValue(container, "Configuration origin")).toBe("User");
    expect(factValue(container, "Mode")).toBe("Simulated");
    expect(factValue(container, "Lifecycle status")).toBe("Planned");
    expect(factValue(container, "Integration readiness")).toMatch(
      /^Not recorded\./,
    );
    expect(factValue(container, "Evidence availability")).toMatch(
      /^No evidence\./,
    );
    expect(factValue(container, "Source health")).toMatch(/^Not recorded\./);
  });

  it("puts the Simulated badge next to lifecycle status, never inside it", async () => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    // The canonical mockup puts `Simulated` and `Planned` in one `Status`
    // field, which collapses provenance into status. That is a mockup error to
    // correct rather than copy.
    expect(factValue(container, "Lifecycle status")).not.toMatch(/simulated/i);
    expect(factValue(container, "Mode")).not.toMatch(/planned/i);
    expect(container.textContent).not.toMatch(/Simulated \/ Planned/);

    const terms = Array.from(container.querySelectorAll("dt")).map(
      (term) => term.textContent,
    );

    expect(terms).not.toContain("Status");
  });

  it("renders both facts correctly for the combinations M1 cannot reach", async () => {
    const userLive = renderSite(USER_LIVE_SITE);
    await settledScreen(userLive.container);

    // Origin USER with mode LIVE: neither is derived from the other.
    expect(factValue(userLive.container, "Configuration origin")).toBe("User");
    expect(factValue(userLive.container, "Mode")).toBe("Live");
    expect(factValue(userLive.container, "Lifecycle status")).toBe("Active");
    userLive.unmount();

    const shippedSimulated = renderSite(SHIPPED_SIMULATED_SITE);
    await settledScreen(shippedSimulated.container);

    // Origin SHIPPED with mode SIMULATED: the mirror case.
    expect(factValue(shippedSimulated.container, "Configuration origin")).toBe(
      "Shipped",
    );
    expect(factValue(shippedSimulated.container, "Mode")).toBe("Simulated");
    expect(factValue(shippedSimulated.container, "Lifecycle status")).toBe(
      "Commissioned",
    );
  });

  it("derives neither fact from the other in the view model", () => {
    const live = deriveSiteDetailView(USER_LIVE_SITE);
    const shipped = deriveSiteDetailView(SHIPPED_SIMULATED_SITE);

    expect([live.configurationOrigin, live.sourceMode]).toEqual([
      "User",
      "Live",
    ]);
    expect([shipped.configurationOrigin, shipped.sourceMode]).toEqual([
      "Shipped",
      "Simulated",
    ]);
  });

  it("states the same unavailable facts whatever the mode and origin are", () => {
    // Evidence availability and source health are not a function of source
    // mode: a LIVE site with no accepted evidence has no evidence either.
    const live = deriveSiteDetailView(USER_LIVE_SITE);
    const simulated = deriveSiteDetailView(USER_SIMULATED_SITE);

    expect(live.evidenceAvailability).toEqual(simulated.evidenceAvailability);
    expect(live.sourceHealth).toEqual(simulated.sourceHealth);
    expect(live.integrationReadiness).toEqual(simulated.integrationReadiness);
  });
});

describe("a configuration-only site fabricates nothing", () => {
  it("states why each unavailable fact is unavailable", async () => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    expect(factValue(container, "Evidence availability")).toMatch(
      /No evidence has been accepted for this site/i,
    );
    expect(factValue(container, "Source health")).toMatch(
      /This build records no source health for a site/i,
    );
    expect(factValue(container, "Integration readiness")).toMatch(
      /This build records no integration readiness for a site/i,
    );
  });

  it("states what this build records, never what the site has", async () => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    // The record carries no integration field and no source-health field, so
    // neither fact may describe this site's integration or its source. A site
    // registered against a real integration arrives with exactly these fields,
    // and copy saying no integration is configured would describe it wrongly.
    const readiness = factValue(container, "Integration readiness");
    const health = factValue(container, "Source health");

    expect(readiness).toMatch(/this build records no integration readiness/i);
    expect(health).toMatch(/this build records no source health/i);
    expect(readiness).not.toMatch(/no integration is configured/i);
    expect(health).not.toMatch(/expected to report|has no health state/i);
  });

  it("renders no chart, image, figure, or diagram surface", async () => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    expect(
      container.querySelectorAll("svg, canvas, img, picture, figure, iframe"),
    ).toHaveLength(0);
    expect(screen.queryAllByRole("figure")).toHaveLength(0);
    expect(screen.queryAllByRole("img")).toHaveLength(0);
    expect(container.textContent ?? "").not.toMatch(
      /single line diagram|diagram|signal/i,
    );
    expect(screen.queryByRole("combobox")).toBeNull();
  });

  it("renders no site image or map panel", async () => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    expect(container.textContent ?? "").not.toMatch(/\b(image|photo|map)\b/i);
  });

  it("renders no tab bar", async () => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    expect(screen.queryAllByRole("tab")).toHaveLength(0);
    expect(screen.queryAllByRole("tablist")).toHaveLength(0);
    expect(
      container.querySelectorAll("[role='tab'], [role='tablist']"),
    ).toHaveLength(0);
  });

  it("uses no source health vocabulary where no source health exists", async () => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    expect(container.textContent ?? "").not.toMatch(SOURCE_HEALTH_VOCABULARY);
  });

  it("renders no evidence-derived value, count, or column", async () => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    const terms = Array.from(container.querySelectorAll("dt")).map(
      (term) => term.textContent ?? "",
    );

    expect(terms.length).toBeGreaterThan(0);
    for (const term of terms) {
      expect(term).not.toMatch(
        /\b(last data|last analysed|last seen|telemetry|analytics|replay|findings?|uptime|availability %|kw|kwh)\b/i,
      );
    }
    expect(container.querySelectorAll("table")).toHaveLength(0);
    expect(container.querySelectorAll("meter, progress")).toHaveLength(0);
  });
});

describe("no action control renders, in any state", () => {
  it.each([
    ["a configured site", { status: "loaded", site: USER_SIMULATED_SITE }],
    ["a site that is not found", { status: "not_found" }],
    ["an unreadable store", { status: "unavailable" }],
  ])("offers no control at all for %s", async (_name, result) => {
    const { container } = render(
      <SiteDetails siteId="MG-002" detail={clientFor(result as SiteDetailResult)} />,
    );
    await settledScreen();

    // Absence, not disablement: nothing here is rendered and then greyed out,
    // so there is no control to check `disabled` or `aria-disabled` on.
    expect(container.querySelectorAll(INTERACTIVE_SELECTOR)).toHaveLength(0);
    expect(container.querySelectorAll("[disabled]")).toHaveLength(0);
    expect(container.querySelectorAll("[aria-disabled]")).toHaveLength(0);
  });

  it.each(ABSENT_CONTROL_LABELS)("does not render %s anywhere", async (label) => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    expect(screen.queryByRole("button", { name: label })).toBeNull();
    expect(screen.queryByRole("link", { name: label })).toBeNull();
    expect(screen.queryByText(label)).toBeNull();
    expect(container.textContent ?? "").not.toMatch(FORBIDDEN_ACTION_PATTERN);
  });

  it.each(ABSENT_QUICK_ACTION_LABELS)(
    "does not render %s, enabled or disabled",
    async (label) => {
      const { container } = renderSite(USER_SIMULATED_SITE);
      await settledScreen();

      // These belong to the Quick Actions panel, which is canonical screen 2
      // chrome. Nothing here invents a container in order to hold a disabled
      // control.
      expect(screen.queryByText(label)).toBeNull();
      expect(container.textContent ?? "").not.toMatch(/quick actions/i);
    },
  );

  it("offers no crossing into the Simulator Lab", async () => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    for (const anchor of Array.from(container.querySelectorAll("a"))) {
      expect(anchor.getAttribute("href")).not.toMatch(/simulat/i);
    }
  });
});

describe("the substrate is a leaf with no shell discriminant", () => {
  it("renders identically whichever shell composes it", async () => {
    const first = renderSite(USER_SIMULATED_SITE);
    await settledScreen(first.container);
    const firstMarkup = first.container.innerHTML;
    first.unmount();

    const second = renderSite(USER_SIMULATED_SITE);
    await settledScreen(second.container);

    // There is no shell, mode, or variant prop to vary, which is why this can
    // only be a same-input assertion today. The real render-equivalence guard
    // needs a second consumer and ships with the Lab's site view at step 6.
    expect(second.container.innerHTML).toBe(firstMarkup);
  });
});
