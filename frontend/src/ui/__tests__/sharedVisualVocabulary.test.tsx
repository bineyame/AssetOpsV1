import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type {
  SiteDetailClient,
  SiteDirectoryClient,
} from "../../sites/siteDirectoryClient";
import type { SiteSummary } from "../../sites/siteReadModel";
import { SITES_PATH } from "../../shell/operatorSiteRoutes";
import {
  SCENARIOS_PATH,
  SIMULATOR_LAB_PATH,
  SITE_TEMPLATES_PATH,
} from "../../shell/simulatorLabRoutes";
import { settledScreen } from "../../test/settled";

/**
 * The parts of the shared visual vocabulary that are claims rather than
 * styling.
 *
 * Most of T009 is chrome and is proved by the suites it did not break: if a
 * value, control, column or destination had changed, the T003-T008 tests would
 * have said so. Two things it does are claims, and they are tested here.
 *
 * The rail is navigation, and navigation is a stronger claim than a button. So
 * what the Lab rail lists, and that it does not exist at all when the gate is
 * closed, is asserted rather than assumed.
 *
 * A badge is chrome, but a badge around an absence is a claim: it dresses "no
 * template" as a state the site is in. So the rule that a badge renders only
 * where a record supplies a value is asserted against a record that supplies
 * none.
 */

const DISABLED = featureFlagsWith(false);
const ENABLED = featureFlagsWith(true);

/** A site created from a template: every badge-eligible field has a value. */
const FROM_TEMPLATE: SiteSummary = {
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

/** The same site with no template provenance. `template` is null, not absent. */
const FROM_NO_TEMPLATE: SiteSummary = { ...FROM_TEMPLATE, template: null };

function directoryOf(
  ...sites: SiteSummary[]
): SiteDirectoryClient & SiteDetailClient {
  return {
    listSites: () => Promise.resolve({ status: "loaded" as const, sites }),
    // No test here opens a site page; the detail client exists so `App` can be
    // constructed, and it refuses rather than inventing a record.
    getSite: () => Promise.resolve({ status: "unavailable" as const }),
  };
}

function renderAt(path: string, flags = ENABLED, sites: SiteSummary[] = []) {
  const directory = directoryOf(...sites);
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={flags} siteDirectory={directory} siteDetail={directory} />
    </MemoryRouter>,
  );
}

describe("the Simulator Lab rail lists only truthful destinations", () => {
  it("lists exactly the surfaces that render real content", () => {
    renderAt(SIMULATOR_LAB_PATH, ENABLED);

    const rail = screen.getByRole("navigation", {
      name: "Simulator Lab routes",
    });

    // An exact allowlist, in order. A further item, or a different one, fails.
    //
    // T017 adds `Scenarios` and T020 adds `Runs`. Each moved out of the
    // absent list below for the only reason that list allows: the route now
    // renders real records from a real store. The rest of the mockup rail is
    // still absent, and still absent rather than dead.
    expect(
      within(rail)
        .getAllByRole("link")
        .map((link) => [link.getAttribute("href"), link.textContent]),
    ).toEqual([
      [SIMULATOR_LAB_PATH, "Simulator Lab"],
      [SITE_TEMPLATES_PATH, "Site Templates"],
      [SCENARIOS_PATH, "Scenarios"],
      ["/simulator-lab/runs", "Runs"],
    ]);
  });

  it.each([
    "Home",
    "Devices",
    "Ingestion",
    "Events",
    "Library",
    "Documentation",
    "Settings",
  ])(
    "does not add the mockup rail item %s, which has no route behind it",
    (label) => {
      renderAt(SIMULATOR_LAB_PATH, ENABLED);

      const rail = screen.getByRole("navigation", {
        name: "Simulator Lab routes",
      });

      expect(within(rail).queryByRole("link", { name: label })).toBeNull();
      expect(within(rail).queryByText(label)).toBeNull();
    },
  );

  it("does not exist at all when the gate is closed", () => {
    renderAt(SIMULATOR_LAB_PATH, DISABLED);

    // The route is not registered, so there is no Lab shell to carry a rail.
    expect(
      screen.queryByRole("navigation", { name: "Simulator Lab routes" }),
    ).toBeNull();
    expect(document.body.textContent).not.toMatch(/simulator/i);
  });

  it("is a separate item set from the operator rail", async () => {
    renderAt(SITES_PATH, ENABLED, [FROM_TEMPLATE]);
    await settledScreen();

    const operatorRail = screen.getByRole("navigation", {
      name: "Operator routes",
    });

    // The two rails share a component and nothing else. Neither shell can
    // reach the other's contents, so no Lab destination appears here.
    expect(
      within(operatorRail)
        .getAllByRole("link")
        .map((link) => link.getAttribute("href")),
    ).toEqual(["/", SITES_PATH]);
    expect(
      screen.queryByRole("navigation", { name: "Simulator Lab routes" }),
    ).toBeNull();
  });
});

describe("a badge renders only where a record supplies its value", () => {
  it("badges the three fields the record always carries", async () => {
    const { container } = renderAt(SITES_PATH, ENABLED, [FROM_TEMPLATE]);
    await settledScreen();

    const row = within(container).getByRole("row", { name: /MG-002/ });

    // Lifecycle, mode and origin are three vocabularies and three tones. They
    // are never one status pill, which is the collapse this product refuses.
    const tones = Array.from(row.querySelectorAll(".badge")).map((badge) => [
      badge.className,
      badge.textContent,
    ]);
    // Order follows the canonical column set T011 settled: Mode before
    // Lifecycle, each in its own column. Three vocabularies, three tones, and
    // never one status pill, which is what this assertion is really about.
    expect(tones).toEqual([
      ["badge badge--provenance", "Simulated"],
      ["badge badge--lifecycle", "Planned"],
      ["badge badge--origin", "User"],
    ]);
  });

  it("renders an absent template provenance as text, never as a badge", async () => {
    const { container } = renderAt(SITES_PATH, ENABLED, [FROM_NO_TEMPLATE]);
    await settledScreen();

    const row = within(container).getByRole("row", { name: /MG-002/ });

    // The site came from no template. That is an absence, not a value, and a
    // badge around it would dress it as a state the site is in.
    const absence = within(row).getByText("Not created from a template");
    expect(absence.closest(".badge")).toBeNull();

    // The three that do have values are unaffected: this is a rule about
    // absent values, not a rule against badges.
    expect(row.querySelectorAll(".badge")).toHaveLength(3);
  });

  it("renders no badge at all on a screen with no site record", () => {
    renderAt("/", ENABLED);

    // The operator home has no record behind it. Defining a badge vocabulary
    // does not cause a badge to appear.
    expect(document.querySelectorAll(".badge")).toHaveLength(0);
  });
});
