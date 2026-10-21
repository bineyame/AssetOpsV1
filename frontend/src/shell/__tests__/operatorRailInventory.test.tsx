import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { describe, expect, it } from "vitest";

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

const UNAVAILABLE_ROOTS = [
  "Portfolio",
  "Assets",
  "Incidents",
  "Maintenance",
  "Operational records",
  "Financials",
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

  it("has exactly four links, Sites, Findings, Actions and Evidence, and they are the live roots", async () => {
    renderAt("/sites");
    await settledScreen();

    expect(
      within(rail())
        .getAllByRole("link")
        .map((link) => [link.textContent, link.getAttribute("href")]),
    ).toEqual([
      ["Sites", "/sites"],
      ["Findings", "/findings"],
      ["Actions", "/actions"],
      ["Evidence", "/evidence"],
    ]);
    expect(rail().querySelectorAll("a, button, [href], [tabindex], [role=link]")).toHaveLength(4);
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

  it("keeps the focusable rail order to the four live links (gate off)", async () => {
    renderAt("/sites");
    await settledScreen();

    const side = rail().parentElement as HTMLElement;
    const focusable = Array.from(
      side.querySelectorAll<HTMLElement>("a[href], button, input, [tabindex]"),
    ).filter((element) => element.getAttribute("tabindex") !== "-1");
    expect(focusable.map((element) => element.textContent)).toEqual(["Sites", "Findings", "Actions", "Evidence"]);
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
    ).toEqual(["Sites", "Findings", "Actions", "Evidence", "Open Simulator Lab"]);

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
      { kind: "unavailable", label: "Portfolio", group: "OPERATIONS", icon: "grid" },
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
    expect(within(nav).getByRole("listitem", { name: "Portfolio, Not available yet" })).toBeVisible();
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
