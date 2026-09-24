import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith, type FeatureFlags } from "../../config/featureFlags";
import type {
  SiteDetailClient,
  SiteDirectoryClient,
} from "../../sites/siteDirectoryClient";
import type {
  SiteDetailReadModel,
  SiteSummary,
} from "../../sites/siteReadModel";
import { settledScreen } from "../../test/settled";
import { spacedText } from "../../test/text";

/**
 * Canonical screen two, at the route.
 *
 * The substrate's own tests cover what a Site renders from a record. What is
 * here is what only the assembled screen can show: the breadcrumb trail the
 * shell supplies, and the Quick Actions panel, which is the one place in this
 * product where all three affordance states appear at once and where the gate
 * rule and the sequencing rule apply to different controls on the same panel.
 *
 * Those two rules are the reason most of this file exists:
 *
 * - The **gate rule** is about existence. With `simulator_lab.enabled` false a
 *   Simulator Lab action is not rendered, not named, and not hinted at.
 * - The **sequencing rule** is about eligibility. With the flag true the same
 *   action renders, disabled, naming the step that would make it work.
 *
 * A control that obeyed the gate rule by rendering disabled would leak the
 * existence of a developer workspace into a build that has none. A control
 * that obeyed the sequencing rule by disappearing would hide a capability the
 * product genuinely intends to have. So they are tested separately, per
 * control, in both states.
 */

const DISABLED = featureFlagsWith(false);
const ENABLED = featureFlagsWith(true);

/** Absent in every state: M1 decided against each of these. */
const DECIDED_AGAINST = [
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

/** Rendered disabled when the gate is open, absent when it is closed. */
const GATED_ACTIONS = ["Open in Simulator Lab", "Start Simulation"];

/** Rendered disabled in both gate states: not a simulator capability. */
const UNGATED_ACTION = "View Live Data";

const SITE: SiteSummary = {
  site_id: "MG-002",
  display_name: "Kalangala Mini-Grid",
  site_type: "MINIGRID",
  location: { country: "Uganda", locality: "Kalangala" },
  timezone: "Africa/Kampala",
  lifecycle_status: "PLANNED",
  origin: "USER",
  source: { mode: "SIMULATED" },
  template: { template_id: "hybrid-mini-grid-100kw", template_version: 1 },
};

const SITE_DETAIL: SiteDetailReadModel = {
  ...SITE,
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
        properties: null,
      },
    ],
    // This site's foundation declares none of the four sections
    // T014 added. `null` is that statement; the backend refuses an
    // empty list, so there is no other way to say it.
    topology: null,
    devices: null,
    signal_mappings: null,
    control_assumptions: null,
  },
};

function directoryWith(sites: SiteSummary[]): SiteDirectoryClient {
  return { listSites: () => Promise.resolve({ status: "loaded", sites }) };
}

/** A detail client that counts what it was asked for. */
function countingDetailClient(): SiteDetailClient & { reads: () => number } {
  let reads = 0;

  return {
    reads: () => reads,
    getSite: (siteId: string) => {
      reads += 1;

      return Promise.resolve(
        siteId.toLowerCase() === SITE_DETAIL.site_id.toLowerCase()
          ? { status: "loaded" as const, site: SITE_DETAIL }
          : { status: "not_found" as const },
      );
    },
  };
}

function renderAt(
  path: string,
  flags: FeatureFlags = ENABLED,
  detail: SiteDetailClient = countingDetailClient(),
) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={flags}
        siteDirectory={directoryWith([SITE])}
        siteDetail={detail}
      />
    </MemoryRouter>,
  );
}

const SITE_PATH = "/sites/MG-002";

describe("the breadcrumb trail leads from the Sites index to this Site", () => {
  it("names the parent and then the Site, and only those", async () => {
    renderAt(SITE_PATH);
    await settledScreen();

    const trail = screen.getByRole("navigation", { name: "Breadcrumb" });

    expect(
      Array.from(trail.querySelectorAll("li")).map((item) => item.textContent),
    ).toEqual(["Sites", "MG-002"]);
  });

  it("does not link the page to itself", async () => {
    renderAt(SITE_PATH);
    await settledScreen();

    const trail = screen.getByRole("navigation", { name: "Breadcrumb" });

    expect(
      within(trail)
        .getAllByRole("link")
        .map((link) => [link.textContent, link.getAttribute("href")]),
    ).toEqual([["Sites", "/sites"]]);
    expect(
      trail.querySelector('[aria-current="page"]')?.textContent,
    ).toBe("MG-002");
  });

  it("spells the Site the way the record spells it", async () => {
    // The crumb is built from the loaded record, not from the address. A trail
    // built from the address would render the requested case and disagree with
    // the heading directly above it.
    renderAt("/sites/mg-002");
    await settledScreen();

    const trail = screen.getByRole("navigation", { name: "Breadcrumb" });

    expect(trail.textContent).toContain("MG-002");
    expect(trail.textContent).not.toContain("mg-002");
  });

  it("renders no trail for a Site that is not configured", async () => {
    renderAt("/sites/MG-404");
    await screen.findByRole("heading", { level: 2, name: "No such site" });

    // A crumb for a site that does not exist would name it as though it did.
    expect(
      screen.queryByRole("navigation", { name: "Breadcrumb" }),
    ).toBeNull();
  });
});

describe("Quick actions obey the gate rule and the sequencing rule separately", () => {
  it.each(GATED_ACTIONS)(
    "does not render %s at all with the gate closed",
    async (label) => {
      const { container } = renderAt(SITE_PATH, DISABLED);
      await settledScreen();

      const main = within(container).getByRole("main");

      // The gate rule. Not disabled, not greyed, not named: a build without a
      // developer workspace must not mention one.
      expect(within(main).queryByRole("button", { name: label })).toBeNull();
      expect(main.textContent).not.toContain(label);
    },
  );

  it.each(GATED_ACTIONS)(
    "renders %s disabled, with its prerequisite, when the gate is open",
    async (label) => {
      const { container } = renderAt(SITE_PATH, ENABLED);
      await settledScreen();

      const main = within(container).getByRole("main");
      const action = within(main).getByRole("button", { name: label });

      // The sequencing rule. The capability is one the product intends to
      // have, so it is named, disabled, and carries what is missing.
      expect((action as HTMLButtonElement).disabled).toBe(true);

      const reason = main.querySelector(
        "#" + action.getAttribute("aria-describedby"),
      );

      expect(reason).not.toBeNull();
      expect(reason?.textContent ?? "").toMatch(/\w+/);
      expect(action.closest("a")).toBeNull();
      expect(action.getAttribute("href")).toBeNull();
    },
  );

  it.each([
    ["closed", DISABLED],
    ["open", ENABLED],
  ])(
    `renders ${UNGATED_ACTION} disabled with the gate %s`,
    async (_name, flags) => {
      const { container } = renderAt(SITE_PATH, flags);
      await settledScreen();

      // Not a simulator capability, so the gate says nothing about it. It is
      // unavailable for an evidence reason, identically in both states.
      const action = within(within(container).getByRole("main")).getByRole(
        "button",
        { name: UNGATED_ACTION },
      );

      expect((action as HTMLButtonElement).disabled).toBe(true);
    },
  );

  it.each([
    ["closed", DISABLED, 1],
    ["open", ENABLED, 3],
  ])(
    "offers exactly the actions the gate allows, all disabled, with the gate %s",
    async (_name, flags, expected) => {
      const { container } = renderAt(SITE_PATH, flags as FeatureFlags);
      await settledScreen();

      const main = within(container).getByRole("main");
      const actions = within(main).getAllByRole("button");

      expect(actions).toHaveLength(expected as number);
      for (const action of actions) {
        expect((action as HTMLButtonElement).disabled).toBe(true);
        expect(action.getAttribute("aria-describedby")).toBeTruthy();
      }
    },
  );

  it("does nothing at all when every action is clicked", async () => {
    const detail = countingDetailClient();
    const { container } = renderAt(SITE_PATH, ENABLED, detail);
    await settledScreen();

    const main = within(container).getByRole("main");
    const readsBefore = detail.reads();
    const markupBefore = main.innerHTML;

    for (const action of within(main).getAllByRole("button")) {
      fireEvent.click(action);
    }
    await settledScreen();

    // No navigation, no re-render, and no second read of the store. There is
    // no handler to call and nothing for a click to follow.
    expect(main.innerHTML).toBe(markupBefore);
    expect(detail.reads()).toBe(readsBefore);
    expect(
      within(container).getByRole("heading", { level: 1 }).textContent,
    ).toBe("MG-002");
  });
});

describe("what canonical screen two draws and this product does not", () => {
  it.each(DECIDED_AGAINST)("renders no %s control in any state", async (label) => {
    const { container } = renderAt(SITE_PATH, ENABLED);
    await settledScreen();

    const main = within(container).getByRole("main");

    // Absent, not disabled. Disabled would say the capability exists and is
    // unavailable to you; what is true is that M1 decided configuration is
    // fixed at creation and that nothing removes a site.
    expect(within(main).queryByRole("button", { name: label })).toBeNull();
    expect(within(main).queryByRole("link", { name: label })).toBeNull();
  });

  it("renders no site image, no map, and nothing to change one with", async () => {
    const { container } = renderAt(SITE_PATH, ENABLED);
    await settledScreen();

    const main = within(container).getByRole("main");

    // The foundation carries no image, so a frame for one would be chrome
    // pretending to content.
    expect(main.querySelectorAll("img, figure, picture, svg, canvas, map")).toHaveLength(0);
    expect(spacedText(main)).not.toMatch(/\b(map|photo|image|upload)\b/i);
  });

  it("renders no diagram, no frame for one, and no signal selector", async () => {
    const { container } = renderAt(SITE_PATH, ENABLED);
    await settledScreen();

    const main = within(container).getByRole("main");

    expect(spacedText(main)).not.toMatch(
      /\b(single line diagram|one-line|schematic|signal|topology)\b/i,
    );
    expect(main.querySelectorAll("select, [role='combobox']")).toHaveLength(0);
  });

  it("renders no operational value, health state, or evidence timestamp", async () => {
    const { container } = renderAt(SITE_PATH, ENABLED);
    await settledScreen();

    const main = within(container).getByRole("main");

    expect(spacedText(main)).not.toMatch(
      /\b(online|offline|stale|degraded|healthy|kwh|kw\b|last data|uptime)\b/i,
    );

    // The one timestamp on this screen is the foundation's validity start,
    // which is configuration metadata from the record.
    const timestamps = (main.textContent ?? "").match(
      /\d{4}-\d{2}-\d{2}T[\d:]+Z/g,
    );

    expect(timestamps).toEqual(["2026-09-14T09:12:00Z"]);
  });
});
