import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type {
  SiteDetailClient,
  SiteDirectoryClient,
} from "../../sites/siteDirectoryClient";
import type { SiteOverviewClient } from "../../sites/siteOverviewClient";
import {
  POPULATED_EVIDENCE,
  evidenceClient,
} from "../../sites/__tests__/evidenceFixtures";
import {
  emptyOverview,
  overviewClient,
  populatedOverview,
} from "../../sites/__tests__/overviewFixtures";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import {
  orderedOverviewCards,
  presentationProfileFor,
} from "../../sites/presentationProfile";
import { createSiteOverviewClient } from "../../sites/siteOverviewClient";
import { expectV69Panels, panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import { spacedText } from "../../test/text";
import { OPERATOR_SITE_TABS_LABEL } from "../operatorSiteTabs";

/**
 * The mini-grid Site Overview (T027 phase 2; AC11, AC12, AC13, AC22): the
 * objective strip, one card per profile domain with backend state, named
 * coverage gaps, the timeline as context, and evidence links into the
 * Site > Evidence record inspector.
 */

const SITE_ID = HYBRID_MINI_GRID_SITE.site_id;
const OVERVIEW_URL = `/sites/${SITE_ID}`;

const DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};
const DETAIL: SiteDetailClient = {
  getSite: () =>
    Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }),
};

function LocationProbe() {
  const location = useLocation();
  return (
    <output data-location>{`${location.pathname}${location.search}`}</output>
  );
}

function renderAt(path: string, overview: SiteOverviewClient, enabled = false) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={featureFlagsWith(enabled)}
        siteDirectory={DIRECTORY}
        siteDetail={DETAIL}
        siteEvidence={evidenceClient({
          status: "loaded",
          value: POPULATED_EVIDENCE,
        })}
        siteOverview={overview}
      />
      <LocationProbe />
    </MemoryRouter>,
  );
}

const populated = () =>
  overviewClient({ status: "loaded", value: populatedOverview(SITE_ID) });

/**
 * W1-F2: each domain is now the mock's objective card (label, state word, note) in the card row above the
 * panels; its readings and coverage moved into Operating context. `cardHeadings` reads the card labels in DOM
 * order; `cardFor` returns the card and its context block together, so every fact the old card held is still
 * asserted for the same domain.
 */
function cards(): HTMLElement[] {
  return Array.from(document.querySelectorAll<HTMLElement>("main [data-overview-card]"));
}

function cardHeadings(): string[] {
  return cards().map((card) => card.querySelector(".v69-metric__label")?.textContent ?? "");
}

function cardFor(name: string): HTMLElement {
  const card = cards().find((c) => c.querySelector(".v69-metric__label")?.textContent === name);
  if (card === undefined) throw new Error(`No domain card "${name}".`);
  const domain = card.getAttribute("data-overview-card") ?? "";
  const context = document.querySelector<HTMLElement>(`[data-overview-domain-context="${domain}"]`);
  const both = document.createElement("div");
  both.append(card.cloneNode(true));
  if (context !== null) both.append(context.cloneNode(true));
  return both;
}

/** The live context block (links must be clicked on the rendered node, not a clone). */
function contextFor(domain: string): HTMLElement {
  return document.querySelector(`[data-overview-domain-context="${domain}"]`) as HTMLElement;
}

/** The objective facts (Operating context) with the site assessment (statusbar) in front. */
function objectiveStrip(): HTMLElement {
  const both = document.createElement("div");
  both.append(document.querySelector(".v69-statusbar")!.cloneNode(true));
  both.append(document.querySelector("[data-overview-objective]")!.cloneNode(true));
  return both;
}

function currentTab(): string {
  const row = screen.getByRole("navigation", {
    name: OPERATOR_SITE_TABS_LABEL,
  });
  return within(row).getByRole("link", { current: "page" }).textContent ?? "";
}

describe("Site Overview, populated", () => {
  it("renders one card per profile domain, in the profile's order", async () => {
    renderAt(OVERVIEW_URL, populated());
    await settledScreen();

    expect(cardHeadings()).toEqual([
      "Service",
      "Dispatch",
      "Battery",
      "Fuel",
      "Renewable",
    ]);
    expect(currentTab()).toBe("Overview");
    expectV69Panels("mini");
  });

  it("shows No assessment yet on every card and never Unknown", async () => {
    renderAt(OVERVIEW_URL, populated());
    await settledScreen();

    for (const name of [
      "Service",
      "Dispatch",
      "Battery",
      "Fuel",
      "Renewable",
    ]) {
      expect(spacedText(cardFor(name))).toContain("No assessment yet");
    }
    const main = spacedText(screen.getByRole("main"));
    expect(main).not.toMatch(/unknown/i);
    expect(main).toContain("no Finding exists");
  });

  it("shows the objective strip with window, measured service and evidence count", async () => {
    renderAt(OVERVIEW_URL, populated());
    await settledScreen();

    const strip = objectiveStrip();
    const text = spacedText(strip);
    expect(text).toContain("No assessment yet");
    expect(text).toContain("67.3 kWh");
    // Review F3: the strip names the metric and the measured share of the window.
    expect(text).toContain("Served energy, over measured time");
    expect(text).toContain("2.67 h of the 8.00 h window measured");
    expect(text).toContain(
      "2026-10-04T03:00:00Z to 2026-10-04T11:00:00Z (8.00 h, latest release)",
    );
    expect(text).toContain(
      "329 accepted records from 1 source and gateway pair",
    );
    expect(
      within(document.querySelector("[data-overview-objective]") as HTMLElement).getByRole("link", {
        name: "Open Site evidence",
      }),
    ).toHaveAttribute("href", `/sites/${SITE_ID}/evidence`);
  });

  it("names an uncovered card's coverage gap and shows no value for it", async () => {
    renderAt(OVERVIEW_URL, populated());
    await settledScreen();

    const fuel = spacedText(cardFor("Fuel"));
    expect(fuel).toContain(
      "Coverage gap: fuel-level-sensor/fuel-level reported no accepted record in this window.",
    );
    expect(fuel).toContain("Not available.");
    expect(fuel).not.toMatch(/\d+ L\b/);
    expect(spacedText(cardFor("Battery"))).toContain(
      "79.08 % at 2026-10-04T11:00:00Z",
    );
  });

  it("links a metric's evidence to the record inspector without changing the Site root", async () => {
    renderAt(OVERVIEW_URL, populated());
    await settledScreen();

    const link = within(contextFor("Dispatch")).getByRole("link", {
      name: /GEN-1\/active_power/,
    });
    expect(link).toHaveAttribute(
      "href",
      `/sites/${SITE_ID}/evidence?signal=GEN-1/active_power&record=msg-gen-72`,
    );
    fireEvent.click(link);
    await settledScreen();

    expect(document.querySelector("[data-location]")?.textContent).toBe(
      `/sites/${SITE_ID}/evidence?signal=GEN-1/active_power&record=msg-gen-72`,
    );
    expect(
      document.querySelector('[data-evidence-record-detail="msg-gen-72"]'),
    ).not.toBeNull();
    expect(currentTab()).toBe("Evidence");
  });

  it("draws the timeline as unit-separated context with a legend", async () => {
    renderAt(OVERVIEW_URL, populated());
    await settledScreen();

    const charts = screen.getAllByRole("img");
    expect(charts.map((chart) => chart.getAttribute("aria-label"))).toEqual([
      "Demand (three feeders) (kW) over the window",
      "Battery charge (%) over the window",
    ]);
    expect(charts[0].querySelectorAll("g line")).toHaveLength(2);
    expect(charts[1].querySelectorAll("circle")).toHaveLength(1);
  });

  it("states no evidence availability of its own beside the Overview body", async () => {
    renderAt(OVERVIEW_URL, populated());
    await settledScreen();

    // Review R1: on a populated Site no sentence anywhere on the page may say
    // that nothing was accepted, whatever panel it sits in. (The empty
    // window's "No window: no evidence has been accepted for this site." is
    // true on an empty Site, and the empty case below still allows it.)
    const page = spacedText(screen.getByRole("main"));
    expect(page).not.toMatch(/no accepted evidence/i);
    expect(page).not.toMatch(/no evidence has been accepted/i);
    expect(page).not.toMatch(/nothing (has been|was) accepted/i);
    expect(
      screen.queryByRole("heading", { name: "Not available for this site" }),
    ).toBeNull();
  });
});

describe("Site Overview, coverage reasons and response shape (fix round 1)", () => {
  it("names an overlap-only signal's gap with the backend's reason", async () => {
    const value = populatedOverview(SITE_ID);
    const battery = value.cards.find((c) => c.domain_id === "Battery");
    if (battery === undefined) throw new Error("fixture has no Battery card");
    battery.gaps = [
      {
        device_id: "battery-pcs-controller",
        signal_id: "state-of-charge",
        status: "OVERLAPPING_ONLY",
        reason:
          "has GOOD records in this window that all overlap; overlapping records are used by no metric",
      },
    ];
    battery.metrics = battery.metrics.map((m) => ({
      ...m,
      value: null,
      at: null,
      window_note: null,
      evidence: [],
      unavailable_because:
        "battery-pcs-controller/state-of-charge has GOOD records in this window that all overlap; overlapping records are used by no metric.",
    }));
    renderAt(OVERVIEW_URL, overviewClient({ status: "loaded", value }));
    await settledScreen();

    const text = spacedText(cardFor("Battery"));
    expect(text).toContain(
      "Coverage gap: battery-pcs-controller/state-of-charge has GOOD records in this window that all overlap",
    );
    expect(text).toMatch(
      /Not available\. battery-pcs-controller\/state-of-charge has GOOD records/,
    );
    expect(text).not.toMatch(/\d+(\.\d+)? %/);
  });

  it("reads a response missing a rendered field as unavailable, through the real client", async () => {
    const broken = populatedOverview(SITE_ID) as unknown as {
      cards: { metrics: Record<string, unknown>[] }[];
    };
    delete broken.cards[0].metrics[0].unavailable_because;
    const original = globalThis.fetch;
    globalThis.fetch = (() =>
      Promise.resolve(
        new Response(JSON.stringify(broken), { status: 200 }),
      )) as typeof fetch;
    try {
      const read = await createSiteOverviewClient("/api/sites").getOverview(
        SITE_ID,
        {},
      );
      expect(read.status).toBe("unavailable");
      globalThis.fetch = (() =>
        Promise.resolve(
          new Response(JSON.stringify(populatedOverview(SITE_ID)), {
            status: 200,
          }),
        )) as typeof fetch;
      const good = await createSiteOverviewClient("/api/sites").getOverview(
        SITE_ID,
        {},
      );
      expect(good.status).toBe("loaded");
    } finally {
      globalThis.fetch = original;
    }
  });
});

describe("Site Overview, empty, unavailable and gate", () => {
  it("names every gap, draws nothing and still assesses nothing", async () => {
    renderAt(
      OVERVIEW_URL,
      overviewClient({ status: "loaded", value: emptyOverview(SITE_ID) }),
    );
    await settledScreen();

    expectV69Panels("mini");
    expect(cardHeadings()).toHaveLength(5);
    for (const name of cardHeadings()) {
      const text = spacedText(cardFor(name));
      expect(text).toContain("No assessment yet");
      expect(text).toContain("Coverage gap:");
    }
    expect(screen.queryAllByRole("img")).toHaveLength(0);
    const main = spacedText(screen.getByRole("main"));
    expect(main).toContain(
      "No window: no evidence has been accepted for this site.",
    );
    expect(main).toContain("nothing to place on the timeline");
    expect(main).not.toMatch(/unknown/i);
  });

  it("states an unreadable Overview rather than an empty one", async () => {
    renderAt(
      OVERVIEW_URL,
      overviewClient({ status: "unavailable", message: "store down" }),
    );
    await settledScreen();

    // W1-F2: the refusal is stated before the five panel slots (never a different error-card layout), and each
    // panel says the read gap inside it; no domain card is drawn.
    expect(document.querySelector('[data-page-refusal="unavailable"]')?.textContent).toContain(
      "Overview unavailable",
    );
    expectV69Panels("mini");
    expect(spacedText(panelTitled("What happened in the selected hour"))).toContain("could not be read");
    expect(panelTitled("Bounded money consequence").textContent).toContain("No current amount");
    expect(cards()).toHaveLength(0);
  });

  it("renders the same Overview with the Lab gate closed and open", async () => {
    const closed = renderAt(OVERVIEW_URL, populated(), false);
    await settledScreen();
    const closedCards = cardHeadings();
    const closedStrip = spacedText(objectiveStrip());
    closed.unmount();

    renderAt(OVERVIEW_URL, populated(), true);
    await settledScreen();
    expect(cardHeadings()).toEqual(closedCards);
    expect(spacedText(objectiveStrip())).toBe(closedStrip);
  });
});

describe("the presentation profile (AC22)", () => {
  it("owns which cards exist and their order, never their state", () => {
    const profile = presentationProfileFor("MINIGRID");
    const served = populatedOverview(SITE_ID).cards;
    const ordered = orderedOverviewCards(profile, served);
    expect(ordered.map((item) => item.label)).toEqual([
      "Service",
      "Dispatch",
      "Battery",
      "Fuel",
      "Renewable",
    ]);
    // Each card's state is the backend card's object, untouched.
    for (const item of ordered) {
      expect(served).toContain(item.card);
    }
  });

  it("renders nothing for a profile card the backend does not serve", () => {
    const served = populatedOverview(SITE_ID).cards.filter(
      (c) => c.domain_id !== "Fuel",
    );
    const ordered = orderedOverviewCards(
      presentationProfileFor("MINIGRID"),
      served,
    );
    expect(ordered.map((item) => item.label)).not.toContain("Fuel");
  });

  it("has no profile for a Site type the product does not present", () => {
    expect(presentationProfileFor("COLD_CHAIN")).toBeNull();
    expect(
      orderedOverviewCards(null, populatedOverview(SITE_ID).cards),
    ).toEqual([]);
  });
});
