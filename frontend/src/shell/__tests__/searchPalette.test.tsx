/**
 * IA-P P7 (spec §6 P7 "Search"; D-IAP.40 Q25): the search palette. Sites, Decisions, Findings and Actions, plus every
 * live rail item; words ANDed, case-blind; the first 20 in kind order; only live targets (plant deadlink); the arrow
 * keys move, Enter opens, Escape closes, Ctrl K and ⌘ K open and close with focus returned. Each word is a literal.
 */
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { EstateActionRow, EstateClient, EstatePortfolioBody } from "../../estate/estateClient";
import type { DecisionItem, FindingItem } from "../../estate/homeLists";
import type { PortfolioSites, PortfolioSitesClient } from "../../estate/portfolioSitesClient";
import { loaded } from "../../estate/__tests__/estateFixtures";
import PORTFOLIO from "../../estate/__tests__/fixtures/iap/portfolio.json?raw";
import SITES_OCT from "../../estate/__tests__/fixtures/iap/sites-2026-10.json?raw";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import type { SiteSummary } from "../../sites/siteReadModel";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import { settledScreen } from "../../test/settled";
import type { NavRailItem } from "../../ui/NavRail";
import { SEARCH_CAP, SEARCH_LABEL, searchEntries, searchMatches } from "../SearchPalette";

beforeEach(() => {
  window.scrollTo = vi.fn();
});
afterEach(cleanup);

const OCT = "from=2026-10-01&to=2026-10-31";
const DETAIL: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }) };

function site(site_id: string, display_name: string, site_type = "MINIGRID"): SiteSummary {
  return { site_id, display_name, site_type, lifecycle_status: "ACTIVE" } as unknown as SiteSummary;
}

const decision = (title: string, site_name: string, target: string | null): DecisionItem =>
  ({ row: { title, site_name }, target }) as unknown as DecisionItem;
const finding = (title: string, site_name: string, target: string | null): FindingItem =>
  ({ row: { title, site_name }, target }) as unknown as FindingItem;
const action = (action_title: string, owner: string | null, site_name: string, live = true): EstateActionRow =>
  ({ action_title, owner, site_name, link_refs: live ? { action: { kind: "ACTION", site: "KOBO-001", id: "a1" } } : { action: null } }) as unknown as EstateActionRow;

const RAIL: NavRailItem[] = [
  { kind: "live", to: "/portfolio", label: "Portfolio", end: false, group: "OPERATIONS", icon: "grid" },
  { kind: "unavailable", label: "Plan", group: "WORK", icon: "clock" },
  { kind: "live", to: "/decisions", label: "Decisions", end: false, group: "WORK", icon: "decide" },
];

describe("the entries and the match rule", () => {
  const entries = searchEntries({
    sites: [site("KOBO-001", "Kobo"), site("COLD-001", "Cold Room", "COLDCHAIN")],
    decisions: [decision("Cut diesel at night", "Kobo", "/sites/KOBO-001/findings/f1"), decision("Dead decision", "Kobo", null)],
    findings: [finding("Battery cycling high", "Kobo", "/sites/KOBO-001/findings/f2")],
    actions: [action("Swap the inverter", null, "Kobo"), action("Dead action", "Amina", "Kobo", false), action("Call the crew", "Amina", "Cold Room")],
    rail: RAIL,
  });

  it("each kind in order with its words; only live targets are indexed (plant deadlink)", () => {
    expect(entries.map((e) => [e.label, e.kind])).toEqual([
      ["Kobo", "Site"],
      ["Cold Room", "Site"],
      ["Cut diesel at night", "Decision · Kobo"],
      ["Battery cycling high", "Finding · Kobo"],
      ["Swap the inverter", "Action · Kobo"],
      ["Call the crew", "Action · Amina"],
      ["Portfolio", "Go to"],
      ["Decisions", "Go to"],
    ]);
    expect(entries[0].to).toBe("/sites/KOBO-001");
    expect(entries.every((e) => typeof e.to === "string" && e.to !== "")).toBe(true);
  });

  it("words are ANDed, case-blind, across the label and its kind", () => {
    expect(searchMatches(entries, "KOBO decision").map((e) => e.label)).toEqual(["Cut diesel at night"]);
    expect(searchMatches(entries, "kobo").map((e) => e.label)).toEqual(["Kobo", "Cut diesel at night", "Battery cycling high", "Swap the inverter"]);
    expect(searchMatches(entries, "kobo crew")).toEqual([]);
    expect(searchMatches(entries, "  go   PORT ").map((e) => e.label)).toEqual(["Portfolio"]);
  });

  it("shows the first 20 matches", () => {
    const many = searchEntries({ sites: Array.from({ length: 30 }, (_, i) => site(`S-${i}`, `Site ${i}`)), decisions: [], findings: [], actions: [], rail: [] });
    expect(SEARCH_CAP).toBe(20);
    const shown = searchMatches(many, "site");
    expect(shown).toHaveLength(20);
    expect(shown[19].label).toBe("Site 19");
  });
});

function estateClient(): EstateClient {
  return {
    findings: () => Promise.reject(new Error("no findings")),
    actions: () => Promise.reject(new Error("no actions")),
    scope: () => Promise.reject(new Error("no scope")),
    portfolio: () => Promise.resolve(loaded(JSON.parse(PORTFOLIO) as EstatePortfolioBody)),
    getOutcomeSummary: () => Promise.resolve({ status: "refused", httpStatus: 503, code: "ESTATE_STORE_UNAVAILABLE", copy: "" }),
  } as unknown as EstateClient;
}
const e1: PortfolioSitesClient = { fetchSites: () => Promise.resolve({ status: "loaded", body: JSON.parse(SITES_OCT) as PortfolioSites }) };
const directory = (): SiteDirectoryClient => ({ listSites: () => Promise.resolve({ status: "loaded", sites: [site("KOBO-001", "Kobo"), site("COLD-001", "Cold Room", "COLDCHAIN")] }) });

function LocationProbe() {
  const location = useLocation();
  return <div data-location>{`${location.pathname}${location.search}`}</div>;
}

function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory()} siteDetail={DETAIL} estateIndex={estateClient()} portfolioSites={e1} />
      <LocationProbe />
    </MemoryRouter>,
  );
}
const searchButton = () => screen.getByRole("button", { name: SEARCH_LABEL });

describe("the palette in the shell", () => {
  it("Ctrl K opens it with the input focused; Ctrl K again closes it and focus returns (gate K1's cycle)", async () => {
    renderAt(`/decisions?${OCT}`);
    await settledScreen();
    expect(SEARCH_LABEL).toBe("Search Sites, decisions and Findings");
    searchButton().focus();
    fireEvent.keyDown(document, { key: "k", ctrlKey: true });
    await settledScreen();
    const dialog = screen.getByRole("dialog", { name: SEARCH_LABEL });
    expect(document.activeElement).toBe(within(dialog).getByRole("combobox"));
    fireEvent.keyDown(document, { key: "k", ctrlKey: true });
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(searchButton());
    fireEvent.keyDown(document, { key: "K", metaKey: true });
    await settledScreen();
    expect(screen.getByRole("dialog", { name: SEARCH_LABEL })).toBeTruthy();
  });

  it("the arrow keys move, Enter opens the entry, Escape closes; an unavailable rail item is not offered", async () => {
    renderAt(`/decisions?${OCT}`);
    await settledScreen();
    fireEvent.click(searchButton());
    await settledScreen();
    const input = screen.getByRole("combobox");
    fireEvent.change(input, { target: { value: "plan" } });
    await settledScreen();
    expect(screen.queryAllByRole("option").map((o) => o.textContent)).toEqual([]);
    fireEvent.change(input, { target: { value: "cold" } });
    await settledScreen();
    const options = screen.getAllByRole("option");
    expect(options[0].textContent).toContain("Cold Room");
    expect(options[0].getAttribute("aria-selected")).toBe("true");
    fireEvent.keyDown(input, { key: "ArrowDown" });
    expect(screen.getAllByRole("option")[1].getAttribute("aria-selected")).toBe("true");
    expect(input.getAttribute("aria-activedescendant")).toBe(screen.getAllByRole("option")[1].id);
    fireEvent.keyDown(input, { key: "ArrowUp" });
    fireEvent.keyDown(input, { key: "Enter" });
    await settledScreen();
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.querySelector("[data-location]")!.textContent!.startsWith("/sites/COLD-001?")).toBe(true);
    fireEvent.click(searchButton());
    await settledScreen();
    fireEvent.keyDown(screen.getByRole("combobox"), { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(searchButton());
  });

  it("no read is made until the palette opens", async () => {
    const listSites = vi.fn(() => Promise.resolve({ status: "loaded" as const, sites: [] }));
    render(
      <MemoryRouter initialEntries={[`/decisions?${OCT}`]}>
        <App flags={featureFlagsWith(false)} siteDirectory={{ listSites }} siteDetail={DETAIL} estateIndex={estateClient()} portfolioSites={e1} />
      </MemoryRouter>,
    );
    await settledScreen();
    expect(listSites).not.toHaveBeenCalled();
    fireEvent.click(searchButton());
    await settledScreen();
    expect(listSites).toHaveBeenCalled();
  });
});
