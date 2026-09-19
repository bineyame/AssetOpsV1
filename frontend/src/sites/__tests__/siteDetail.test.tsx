import { fireEvent, render, screen } from "@testing-library/react";
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

/**
 * The Quick Actions the substrate must never render on its own.
 *
 * Both are Simulator Lab actions. Deciding them means reading the feature flag
 * and naming the Lab's address, which this module may not do, so they reach the
 * panel through the slot the composing shell fills. With the slot empty - a
 * gate-off build, and every test in this file - they are absent.
 */
const SHELL_SUPPLIED_QUICK_ACTION_LABELS = [
  "Open in Simulator Lab",
  "Start Simulation",
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

    // The heading is the `site_id`, not the display name. What addresses a
    // site is what titles its page; the name is a label on the thing rather
    // than the thing, so it renders beneath. T007 titled this with the display
    // name because identity had nowhere else to go on that screen; canonical
    // screen 2 gives it a header of its own.
    expect(
      screen.getByRole("heading", { level: 1, name: "MG-002" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Kalangala Mini-Grid", { selector: "p" })).toBeInTheDocument();
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

  it("renders the identity header badge as mode, and never as status", async () => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    // Canonical screen 2 puts a badge beside the Site's identity. It is the
    // rendering of `source.mode`, which is the one thing about the subject
    // that belongs in its header - not lifecycle, not health, not an
    // assessment.
    const header = container.querySelector(".page-header__title");

    expect(header?.textContent).toContain("MG-002");
    expect(header?.textContent).toContain("Simulated");
    expect(header?.textContent).not.toMatch(/Planned|User|healthy|online/i);
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

describe("what renders is absent or disabled, and never enabled", () => {
  /**
   * T007 and T008 asserted that no control rendered at all. T012 changes that
   * deliberately, and the change is narrower than it looks.
   *
   * What T007 refused was a control for a capability M1 decided against -
   * editing, deleting, version history - and that refusal is unchanged and
   * still absolute below. What T012 adds is the other kind: a capability the
   * product can sequence but cannot yet perform, which renders disabled and
   * says what would make it work.
   *
   * The two must not blur, which is why the absence assertions stay exactly as
   * strong as they were and the new ones assert disabled rather than merely
   * "not enabled".
   */
  it.each([
    ["a site that is not found", { status: "not_found" }],
    ["an unreadable store", { status: "unavailable" }],
  ])("offers no control at all for %s", async (_name, result) => {
    const { container } = render(
      <SiteDetails siteId="MG-002" detail={clientFor(result as SiteDetailResult)} />,
    );
    await settledScreen();

    // A screen that could not read a site has nothing to act on, so the Quick
    // Actions panel is not rendered there at all - not rendered empty, and not
    // rendered with everything greyed out.
    expect(container.querySelectorAll(INTERACTIVE_SELECTOR)).toHaveLength(0);
    expect(container.querySelectorAll("[disabled]")).toHaveLength(0);
    expect(container.querySelectorAll("[aria-disabled]")).toHaveLength(0);
    expect(container.textContent ?? "").not.toMatch(/quick actions/i);
  });

  it("renders no enabled control for a configured site", async () => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    // Every control on this screen is disabled. Not "most of them": an enabled
    // control would be a capability that exists, and none does.
    const controls = Array.from(
      container.querySelectorAll(INTERACTIVE_SELECTOR),
    );

    expect(controls.length).toBeGreaterThan(0);
    for (const control of controls) {
      expect(control.tagName).toBe("BUTTON");
      expect((control as HTMLButtonElement).disabled).toBe(true);
    }
  });

  it("gives every disabled control a visible, associated reason", async () => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    // A disabled control with no reason is a dead end. A reason in a tooltip
    // is a reason a keyboard cannot reach, because a disabled button takes no
    // focus - so the reason is rendered as text and tied to the control.
    for (const control of Array.from(container.querySelectorAll("button"))) {
      const describedBy = control.getAttribute("aria-describedby");

      expect(describedBy).toBeTruthy();

      const reason = container.querySelector("#" + describedBy);

      expect(reason).not.toBeNull();
      expect((reason?.textContent ?? "").length).toBeGreaterThan(20);
    }
  });

  it("does nothing when a disabled control is clicked", async () => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    const before = container.innerHTML;
    for (const control of Array.from(container.querySelectorAll("button"))) {
      fireEvent.click(control);
    }
    await settledScreen();

    // Nothing to navigate to, nothing to submit, and no handler to call.
    expect(container.innerHTML).toBe(before);
    expect(container.querySelectorAll("form")).toHaveLength(0);
  });

  it.each(ABSENT_CONTROL_LABELS)("does not render %s anywhere", async (label) => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    // Unchanged from T007. These are deferred by decision, so they are absent
    // from the DOM rather than disabled: disabled would read as "soon", and
    // none of these is coming.
    expect(screen.queryByRole("button", { name: label })).toBeNull();
    expect(screen.queryByRole("link", { name: label })).toBeNull();
    expect(screen.queryByText(label)).toBeNull();
    expect(container.textContent ?? "").not.toMatch(FORBIDDEN_ACTION_PATTERN);
  });

  it.each(SHELL_SUPPLIED_QUICK_ACTION_LABELS)(
    "does not render %s from the substrate alone",
    async (label) => {
      const { container } = renderSite(USER_SIMULATED_SITE);
      await settledScreen();

      // The slot is empty here, and that is the gate-off shape. The substrate
      // cannot name the Lab, so with nothing filling the slot the Lab is not
      // named.
      expect(screen.queryByText(label)).toBeNull();
      expect(container.textContent ?? "").not.toMatch(/simulator|simulation/i);
    },
  );

  it("still renders the panel correctly with the slot empty", async () => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    // Not an empty frame waiting to be filled: `View Live Data` is an operator
    // capability, unavailable for an operator reason, so the panel says
    // something true on its own.
    const action = screen.getByRole("button", { name: "View Live Data" });

    expect((action as HTMLButtonElement).disabled).toBe(true);
    expect(container.textContent).toMatch(/Quick actions/);
    expect(container.querySelectorAll("button")).toHaveLength(1);
  });

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

describe("the Site information panel carries the facts assigned to it", () => {
  /**
   * The T012 review found the facts present on the screen but scattered:
   * Lifecycle in the provenance panel, foundation version and validity in a
   * panel of their own, while the acceptance criterion assigns all of them to
   * `Site information`. The tests missed it because every fact was queried
   * against the whole container, so a fact could be anywhere and still pass.
   *
   * These scope to the panel. A fact that moves out of it now fails here
   * rather than passing somewhere else on the page.
   */
  function sitePanel(container: HTMLElement): HTMLElement {
    const heading = container.querySelector("#site-detail-identity-heading");
    const panel = heading?.closest("section");

    if (!panel) {
      throw new Error("No Site information panel to scope to.");
    }
    return panel as HTMLElement;
  }

  function termsIn(panel: HTMLElement): string[] {
    return Array.from(panel.querySelectorAll("dt")).map(
      (term) => term.textContent ?? "",
    );
  }

  it("carries exactly the facts the task assigns to it", async () => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    expect(termsIn(sitePanel(container))).toEqual([
      "Site ID",
      "Name",
      "Type",
      "Location",
      "Timezone",
      "Lifecycle status",
      "Foundation version",
      "Valid from",
      "Summary",
    ]);
  });

  it("renders each of those facts from the record, inside that panel", async () => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    const panel = sitePanel(container);

    expect(factValue(panel, "Site ID")).toBe("MG-002");
    expect(factValue(panel, "Lifecycle status")).toBe("Planned");
    expect(factValue(panel, "Foundation version")).toBe("1");
    expect(factValue(panel, "Valid from")).toBe("2026-09-14T09:12:00Z");
  });

  it("keeps mode and configuration origin out of it", async () => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    // Lifecycle moved; provenance did not. Mode is about where evidence comes
    // from and configuration origin is about the document, and neither is a
    // fact about the site in the sense this panel collects.
    const terms = termsIn(sitePanel(container));

    expect(terms).not.toContain("Mode");
    expect(terms).not.toContain("Configuration origin");
    expect(terms).not.toContain("Created from template");
    expect(terms).not.toContain("Status");
  });

  it("still states lifecycle and mode as separate facts after the move", async () => {
    const { container } = renderSite(USER_SIMULATED_SITE);
    await settledScreen();

    // The seam this slice must not break while rearranging panels. Separate
    // terms, separate values, neither bleeding into the other, and no single
    // collapsed `Status`.
    expect(factValue(container, "Lifecycle status")).toBe("Planned");
    expect(factValue(container, "Mode")).toBe("Simulated");
    expect(factValue(container, "Lifecycle status")).not.toMatch(/simulated/i);
    expect(factValue(container, "Mode")).not.toMatch(/planned/i);
  });
});
