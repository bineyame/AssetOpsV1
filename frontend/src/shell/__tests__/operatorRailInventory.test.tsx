import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith, type FeatureFlags } from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { EMPTY_ANALYTICS_CLIENT } from "../../sites/__tests__/analyticsFixtures";
import { settledScreen } from "../../test/settled";
import { spacedText } from "../../test/text";
import { NavRail, type NavRailItem } from "../../ui";

/**
 * W1-UX-07 (owner decision 2026-10-17, `D-2026-10-17-w1-rail`): the operator
 * rail shows the full v6.9 root inventory. Sites and Findings are live links,
 * and W3-01 makes Actions the third (the estate Actions root); the other eight roots are text with the visible status `Not available yet`,
 * and are never a link, a route, a handler or a tab stop.
 */

const EMPTY_SITE_DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};

const gateOff = featureFlagsWith(false);
const gateOn = featureFlagsWith(true);

// W6-01e: Operational records rail root is live.
const UNAVAILABLE_ROOTS = [
  "Assets",
  "Settings",
];

function LocationProbe() {
  const location = useLocation();
  return <output data-testid="location">{location.pathname}</output>;
}

function renderAt(path: string, flags: FeatureFlags = gateOff) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={flags}
        siteDirectory={EMPTY_SITE_DIRECTORY}
        siteAnalytics={EMPTY_ANALYTICS_CLIENT}
      />
      <LocationProbe />
    </MemoryRouter>,
  );
}

function rail() {
  return screen.getByRole("navigation", { name: "Operator routes" });
}

function unavailableRow(label: string): HTMLElement {
  return within(rail()).getByRole("listitem", {
    name: `${label}, Not available yet`,
  });
}

describe("operator rail inventory (W1-UX-07)", () => {
  it("lists the eleven v6.9 roots in order, under six headed groups", async () => {
    renderAt("/sites");
    await settledScreen();

    expect(
      Array.from(rail().querySelectorAll(".nav-rail__group-label")).map(
        (header) => header.textContent,
      ),
    ).toEqual(["OPERATIONS", "INTELLIGENCE", "WORK", "ASSURANCE", "BUSINESS", "ADMIN"]);
    expect(
      Array.from(rail().querySelectorAll("li .nav-rail__label")).map(
        (label) => label.textContent,
      ),
    ).toEqual([
      "Portfolio",
      "Sites",
      "Assets",
      "Findings",
      "Actions",
      "Incidents",
      "Maintenance",
      "Operational records",
      "Evidence",
      "Financials",
      "Settings",
    ]);
    // The old one-item group caption is gone, not kept beside the new one.
    expect(spacedText(rail())).not.toMatch(/\bOPERATE\b/);
  });

  // W6-01e: Operational records rail root is live.
  it("has exactly nine links, Portfolio, Sites, Findings, Actions, Incidents, Maintenance, Operational records, Evidence and Financials, and they are the live roots", async () => {
    renderAt("/sites");
    await settledScreen();

    expect(
      within(rail())
        .getAllByRole("link")
        .map((link) => [link.textContent, link.getAttribute("href")]),
    ).toEqual([
      ["Portfolio", "/portfolio"],
      ["Sites", "/sites"],
      ["Findings", "/findings"],
      ["Actions", "/actions"],
      ["Incidents", "/incidents"],
      ["Maintenance", "/maintenance"],
      ["Operational records", "/operational-records"],
      ["Evidence", "/evidence"],
      ["Financials", "/financials"],
    ]);
    expect(rail().querySelectorAll("a, button, [href], [tabindex], [role=link]")).toHaveLength(9);
  });

  it.each(UNAVAILABLE_ROOTS)(
    "renders %s as visible, named, non-interactive text",
    async (label) => {
      renderAt("/sites");
      await settledScreen();

      const row = unavailableRow(label);
      // Visible status in the row itself, not a tooltip or colour.
      expect(within(row).getByText(label)).toBeVisible();
      expect(within(row).getByText("Not available yet")).toBeVisible();
      expect(row).not.toHaveAttribute("title");
      expect(row.querySelector("[title]")).toBeNull();
      // Not a link, not a control, not a disabled control, not a tab stop.
      expect(row.tagName).toBe("LI");
      expect(row.querySelector("a, button, input, [href], [role]")).toBeNull();
      expect(row).not.toHaveAttribute("tabindex");
      expect(row).not.toHaveAttribute("aria-disabled");
      expect(row).not.toHaveAttribute("href");
      row.focus();
      expect(document.activeElement).not.toBe(row);
      // The icon is decorative.
      const icon = row.querySelector("svg");
      expect(icon).not.toBeNull();
      expect(icon).toHaveAttribute("aria-hidden", "true");
    },
  );

  it("does nothing when an unavailable row is clicked or keyed", async () => {
    renderAt("/sites");
    await settledScreen();

    for (const label of UNAVAILABLE_ROOTS) {
      const row = unavailableRow(label);
      fireEvent.click(row);
      fireEvent.keyDown(row, { key: "Enter" });
      fireEvent.keyDown(row, { key: " " });
      fireEvent.click(within(row).getByText(label));
      expect(screen.getByTestId("location")).toHaveTextContent(/^\/sites$/);
    }
    expect(screen.getByRole("heading", { level: 1, name: "Sites" })).toBeInTheDocument();
  });

  it("navigates from both live roots", async () => {
    renderAt("/sites");
    await settledScreen();

    fireEvent.click(within(rail()).getByRole("link", { name: "Findings" }));
    await settledScreen();
    expect(screen.getByTestId("location")).toHaveTextContent(/^\/findings$/);
    expect(screen.getByRole("heading", { level: 1, name: "Findings" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { level: 1, name: "Page not available" })).toBeNull();

    fireEvent.click(within(rail()).getByRole("link", { name: "Sites" }));
    await settledScreen();
    expect(screen.getByTestId("location")).toHaveTextContent(/^\/sites$/);
    expect(screen.getByRole("heading", { level: 1, name: "Sites" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { level: 1, name: "Page not available" })).toBeNull();
  });

  it("keeps the focusable rail order to the nine live links (gate off)", async () => {
    renderAt("/sites");
    await settledScreen();

    const side = rail().parentElement as HTMLElement;
    const focusable = Array.from(
      side.querySelectorAll<HTMLElement>("a[href], button, input, [tabindex]"),
    ).filter((element) => element.getAttribute("tabindex") !== "-1");
    expect(focusable.map((element) => element.textContent)).toEqual(["Portfolio", "Sites", "Findings", "Actions", "Incidents", "Maintenance", "Operational records", "Evidence", "Financials"]);
  });
});

/**
 * W5-02c K4a (`.agent/W5-02c-K4-preflight-rulings.md` rulings 1-2; register R69 resolved): every Site Action detail
 * path, for any Site type, selects the Actions root as the v69 rail does (`index.html:729,742,1114`). Only Actions has
 * `nav-rail__link active` and `aria-current="page"` there; ordinary Site paths, global Actions and Operational records
 * keep their NavLink selection. The nine live links and their focus order never change.
 */
describe("Site Action detail rail selection (W5-02c K4a)", () => {
  afterEach(() => vi.unstubAllGlobals());
  const LIVE = ["Portfolio", "Sites", "Findings", "Actions", "Incidents", "Maintenance", "Operational records", "Evidence", "Financials"];

  async function railAt(path: string) {
    vi.stubGlobal("fetch", async () => new Response(JSON.stringify({ detail: { code: "UNAVAILABLE", message: "No read in this test." } }), { status: 503 }));
    renderAt(path);
    await settledScreen();
    const links = within(rail()).getAllByRole("link");
    return {
      links,
      current: links.filter((l) => l.getAttribute("aria-current") === "page").map((l) => l.textContent),
      active: links.filter((l) => l.classList.contains("active")).map((l) => l.textContent),
    };
  }

  it.each([
    ["a cold domain Action Verification", "/sites/CR-TEST-01/actions/6f1c2a7e-0d4b-4c3e-9a51-1b2c3d4e5f60/verification"],
    // W5-04 V4a (R-3): the EV domain Action reuses K4a's pathname-scoped override unchanged.
    ["an EV domain Action Verification", "/sites/EV-LAB-001/actions/3e0a9b1c-7d2f-4e6a-8b5c-0f1e2d3c4b5a/verification?from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z"],
    ["a W1 mini-grid Action detail", "/sites/KOBO-001/actions/0b5d7f1e-2c3a-4b6d-8e9f-a1b2c3d4e5f6"],
    ["a W1 mini-grid Action section", "/sites/KOBO-001/actions/0b5d7f1e-2c3a-4b6d-8e9f-a1b2c3d4e5f6/plan"],
  ])("selects Actions alone on %s", async (_name, path) => {
    const { links, current, active } = await railAt(path);
    expect(current).toEqual(["Actions"]);
    expect(active).toEqual(["Actions"]);
    const actions = links.find((l) => l.textContent === "Actions") as HTMLElement;
    const sites = links.find((l) => l.textContent === "Sites") as HTMLElement;
    expect(actions.className).toBe("nav-rail__link active");
    expect(actions.getAttribute("href")).toBe("/actions");
    expect(sites.className).toBe("nav-rail__link");
    expect(sites.getAttribute("aria-current")).toBeNull();
    // Same nine live links, hrefs and focus order as every other route.
    const side = rail().parentElement as HTMLElement;
    const focusable = Array.from(side.querySelectorAll<HTMLElement>("a[href], button, input, [tabindex]")).filter(
      (element) => element.getAttribute("tabindex") !== "-1",
    );
    expect(focusable.map((element) => element.textContent)).toEqual(LIVE);
    expect(links.map((l) => l.getAttribute("href"))).toEqual([
      "/portfolio", "/sites", "/findings", "/actions", "/incidents", "/maintenance", "/operational-records", "/evidence", "/financials",
    ]);
  });

  // post-W6 W1-b Q25 / R202 (pre-flight ruling 6): every Site Finding detail path and child selects Findings.
  it.each([
    ["a W1 mini-grid Finding overview", "/sites/KOBO-001/findings/7d3c1f2e-0a4b-4c5d-8e9f-0a1b2c3d4e5f"],
    ["a W1 mini-grid Finding Recommendation", "/sites/KOBO-001/findings/7d3c1f2e-0a4b-4c5d-8e9f-0a1b2c3d4e5f/recommendation"],
    ["a W1 mini-grid Finding Evidence", "/sites/KOBO-001/findings/7d3c1f2e-0a4b-4c5d-8e9f-0a1b2c3d4e5f/evidence"],
    ["a W1 mini-grid Finding History", "/sites/KOBO-001/findings/7d3c1f2e-0a4b-4c5d-8e9f-0a1b2c3d4e5f/history"],
    ["a W1 mini-grid Finding Alternatives", "/sites/KOBO-001/findings/7d3c1f2e-0a4b-4c5d-8e9f-0a1b2c3d4e5f/alternatives"],
    ["a cold Finding", "/sites/CR-TEST-01/findings/6f1c2a7e-0d4b-4c3e-9a51-1b2c3d4e5f60"],
    ["an EV Finding child", "/sites/EV-LAB-001/findings/3e0a9b1c-7d2f-4e6a-8b5c-0f1e2d3c4b5a/evidence"],
  ])("selects Findings alone on %s", async (_name, path) => {
    const { links, current, active } = await railAt(path);
    expect(current).toEqual(["Findings"]);
    expect(active).toEqual(["Findings"]);
    const findings = links.find((l) => l.textContent === "Findings") as HTMLElement;
    expect(findings.getAttribute("href")).toBe("/findings");
    expect((links.find((l) => l.textContent === "Sites") as HTMLElement).getAttribute("aria-current")).toBeNull();
    expect(links.map((l) => l.textContent)).toEqual(LIVE);
  });

  it.each([
    ["the Site Findings index", "/sites/KOBO-001/findings", "Sites"],
    ["the global Findings root", "/findings", "Findings"],
    ["an ordinary Site page", "/sites/KOBO-001", "Sites"],
    ["a Site Work page", "/sites/KOBO-001/work", "Sites"],
    ["the global Actions root", "/actions", "Actions"],
    ["the Operational records root", "/operational-records", "Operational records"],
  ])("keeps NavLink selection on %s", async (_name, path, label) => {
    const { links, current, active } = await railAt(path);
    expect(current).toEqual([label]);
    expect(active).toEqual([label]);
    expect(links.map((l) => l.textContent)).toEqual(LIVE);
  });
});

describe("operator rail workspace footer (W1-UX-07)", () => {
  it("places one Simulator Lab link in the WORKSPACE footer when the gate is open", async () => {
    renderAt("/sites", gateOn);
    await settledScreen();

    const footer = screen.getByRole("navigation", { name: "Workspace utilities" });
    // A workspace utility landmark beside the rail, not an operator group.
    expect(rail().contains(footer)).toBe(false);
    expect(footer.parentElement).toBe(rail().parentElement);
    expect(within(footer).getByText("WORKSPACE")).toBeVisible();
    expect(
      within(footer)
        .getAllByRole("link")
        .map((link) => [link.textContent, link.getAttribute("href")]),
    ).toEqual([["Open Simulator Lab", "/simulator-lab"]]);
    // Rendered once in the shell: no second copy of the entry point.
    expect(screen.getAllByRole("link", { name: "Open Simulator Lab" })).toHaveLength(1);
    expect(screen.getAllByRole("navigation", { name: "Workspace utilities" })).toHaveLength(1);

    // Focus order: the two live roots, then the workspace link.
    const side = rail().parentElement as HTMLElement;
    expect(
      Array.from(side.querySelectorAll<HTMLElement>("a[href]")).map((a) => a.textContent),
    ).toEqual(["Portfolio", "Sites", "Findings", "Actions", "Incidents", "Maintenance", "Operational records", "Evidence", "Financials", "Open Simulator Lab"]);

    fireEvent.click(within(footer).getByRole("link", { name: "Open Simulator Lab" }));
    expect(screen.getByRole("heading", { level: 1, name: "Simulator Lab" })).toBeInTheDocument();
  });

  it("omits the footer, its label and any Lab link when the gate is closed", async () => {
    const { container } = renderAt("/sites", gateOff);
    await settledScreen();

    expect(screen.queryByRole("navigation", { name: "Workspace utilities" })).toBeNull();
    expect(spacedText(container)).not.toMatch(/workspace|simulator|\blab\b/i);
    for (const link of Array.from(container.querySelectorAll("a"))) {
      expect(link.getAttribute("href")).not.toMatch(/simulator/i);
    }
    // The mock's illustrative footer count is not asserted for a tenant.
    expect(spacedText(container)).not.toMatch(/Demo workspace|illustrative records/i);
  });

  it("never shows the mock's illustrative workspace line with the gate open", async () => {
    const { container } = renderAt("/sites", gateOn);
    await settledScreen();
    expect(spacedText(container)).not.toMatch(/Demo workspace|3 sites|illustrative records/i);
  });
});

describe("NavRail item model (W1-UX-07)", () => {
  it("renders an unavailable item with no destination, whatever the shell passes", () => {
    const items: NavRailItem[] = [
      { kind: "unavailable", label: "Assets", group: "OPERATIONS", icon: "asset" },
      { kind: "live", to: "/sites", label: "Sites", group: "OPERATIONS", icon: "site" },
    ];
    render(
      <MemoryRouter initialEntries={["/sites"]}>
        <Routes>
          <Route path="*" element={<NavRail label="Test rail" items={items} />} />
        </Routes>
      </MemoryRouter>,
    );
    const nav = screen.getByRole("navigation", { name: "Test rail" });
    expect(within(nav).getAllByRole("link").map((a) => a.textContent)).toEqual(["Sites"]);
    expect(within(nav).getByRole("listitem", { name: "Assets, Not available yet" })).toBeVisible();
  });

  it("rejects a destination on an unavailable item at compile time", () => {
    // The type is the first line of defence; the navigation-truthfulness guard
    // is the second. If this stops being an error, `tsc` fails here.
    // @ts-expect-error an unavailable root cannot carry a route
    const bad: NavRailItem = { kind: "unavailable", label: "Assets", to: "/assets" };
    expect(bad.label).toBe("Assets");
  });
});

describe("W1-F5a carry 5: the operator rail collapses behind a Menu button at phone width", () => {
  function stubWidth(narrow: boolean) {
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      writable: true,
      value: (query: string) => ({
        matches: narrow && query === "(max-width: 640px)",
        media: query,
        addEventListener: () => undefined,
        removeEventListener: () => undefined,
      }),
    });
  }

  it("adds no control beside the rail at desktop width", async () => {
    stubWidth(false);
    const { container } = renderAt("/sites");
    await settledScreen();
    expect(screen.queryByRole("button", { name: "Menu" })).toBeNull();
    expect(container.querySelector(".app-frame--rail-open")).toBeNull();
    delete (window as { matchMedia?: unknown }).matchMedia;
  });

  it("opens the collapsed rail from Menu, keeps every destination, and closes it on navigation", async () => {
    stubWidth(true);
    const { container } = renderAt("/sites");
    await settledScreen();
    const menu = screen.getByRole("button", { name: "Menu" });
    expect(menu).toHaveAttribute("aria-expanded", "false");
    expect(menu).toHaveAttribute("aria-controls", "operator-rail-body");
    expect(container.querySelector("#operator-rail-body")?.contains(rail())).toBe(true);
    expect(container.querySelector(".app-frame--rail-open")).toBeNull();
    fireEvent.click(menu);
    expect(menu).toHaveAttribute("aria-expanded", "true");
    expect(container.querySelector(".app-frame--operator.app-frame--rail-open")).not.toBeNull();
    fireEvent.click(within(rail()).getByRole("link", { name: "Findings" }));
    await settledScreen();
    expect(screen.getByTestId("location")).toHaveTextContent(/^\/findings$/);
    expect(container.querySelector(".app-frame--rail-open")).toBeNull();
    expect(screen.getByRole("button", { name: "Menu" })).toHaveAttribute("aria-expanded", "false");
    delete (window as { matchMedia?: unknown }).matchMedia;
  });
});
