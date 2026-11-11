/**
 * SR-1 (proposal 2026-11-10 "Item 12.5", SR.3/SR.4; v71 `portfolio-tabs.html` Change 0b): one shared date range,
 * kept in the address only (D-UI.2). The hook reads both address forms, the rail carries the range, the shell fills
 * an estate address that has none, the presets (no "Today"), the `known_at` label and the picker's focus handling.
 */
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { fakeClient, findingsBody, loaded } from "../../estate/__tests__/estateFixtures";
import { loadedPortfolio, portfolioBody } from "../../estate/__tests__/portfolioFixtures";
import type { EstateClient, EstatePortfolioQuery } from "../../estate/estateClient";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import { settledScreen } from "../../test/settled";
import {
  RANGE_PRESETS,
  SHARED_RANGE_SESSION_KEY,
  fillsRangeOnEntry,
  isWorkPage,
  presetOf,
  presetRange,
  rangeSearch,
  readSharedRange,
  readsSharedRange,
  useSharedRange,
  withRange,
} from "../sharedRange";

/** Mock "today" (v7.1 Change 0b): 7 Oct 2026, so Last 7 days is 30 Sep - 6 Oct. */
const NOW = Date.parse("2026-10-07T10:00:00Z");
const WEEK = "from=2026-09-30T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z";

const DIRECTORY: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [] }) };
const DETAIL: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }) };

function LocationProbe() {
  const location = useLocation();
  return <output data-location>{`${location.pathname}${location.search}`}</output>;
}

const where = () => document.querySelector("[data-location]")?.textContent ?? "";

function estate(): EstateClient & { calls: EstatePortfolioQuery[] } {
  const base = fakeClient((lens) => loaded(findingsBody(lens)));
  const client = {
    ...base,
    calls: [] as EstatePortfolioQuery[],
    portfolio: (query: EstatePortfolioQuery) => {
      client.calls.push(query);
      return Promise.resolve(loadedPortfolio(portfolioBody()));
    },
  };
  return client;
}

function renderApp(path: string, client: EstateClient = estate()) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDirectory={DIRECTORY} siteDetail={DETAIL} estateIndex={client} />
      <LocationProbe />
    </MemoryRouter>,
  );
}

function Probe() {
  const range = useSharedRange();
  return <output data-range>{JSON.stringify(range)}</output>;
}

function hookAt(path: string) {
  const view = render(
    <MemoryRouter initialEntries={[path]}>
      <Probe />
    </MemoryRouter>,
  );
  const value = JSON.parse(document.querySelector("[data-range]")?.textContent ?? "null");
  view.unmount();
  return value;
}

const railHref = (label: string) =>
  within(screen.getByRole("navigation", { name: "Operator routes" })).getByRole("link", { name: label }).getAttribute("href");

const rangeButton = () => screen.getByRole("button", { name: /^Date range for every page/ });

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  window.sessionStorage.clear();
});

afterEach(() => {
  vi.useRealTimers();
  window.sessionStorage.clear();
});

describe("SR-1 useSharedRange reads both address forms", () => {
  it("reads the short day form and the instant form as the same range", () => {
    const day = hookAt("/portfolio?from=2026-09-30&to=2026-10-06");
    const instant = hookAt(`/portfolio?${WEEK}`);
    expect(day).toEqual({ status: "set", from: "2026-09-30", to: "2026-10-06", known_at: null, preset: "7d" });
    expect(instant).toEqual(day);
  });

  it("keeps known_at and names a range no preset matches Custom", () => {
    expect(hookAt("/findings?from=2026-09-02&to=2026-09-03&known_at=2026-10-04T12:00:00Z")).toEqual({
      status: "set",
      from: "2026-09-02",
      to: "2026-09-03",
      known_at: "2026-10-04T12:00:00Z",
      preset: "custom",
    });
  });

  it("an address without a range is absent; a bad range is invalid and never echoes dates", () => {
    expect(hookAt("/portfolio")).toEqual({ status: "absent" });
    for (const bad of [
      "from=2026-10-06",
      "from=2026-10-06&to=2026-10-01",
      "from=2026-08-01&to=2026-10-01",
      "from=yesterday&to=2026-10-01",
      "from=2026-10-01&to=2026-10-02&known_at=noon",
    ]) {
      expect(readSharedRange(new URLSearchParams(bad), NOW)).toEqual({ status: "invalid" });
    }
  });
});

describe("SR-1 presets", () => {
  it("offers Yesterday, Last 7 days, Last 30 days, This month, Last month and Custom, and no Today; Work pages add Last 7 days, including today", () => {
    expect(RANGE_PRESETS.map((p) => p.label)).toEqual(["Yesterday", "Last 7 days", "Last 7 days, including today", "Last 30 days", "This month", "Last month", "Custom"]);
    expect(presetRange("7dwork", NOW)).toEqual({ from: "2026-10-01", to: "2026-10-07" });
    expect(presetOf("2026-10-01", "2026-10-07", NOW)).toBe("7dwork");
    expect(isWorkPage("/incidents")).toBe(true);
    expect(isWorkPage("/maintenance/preventive")).toBe(true);
    expect(isWorkPage("/sites/KOBO-001/work/incidents")).toBe(true);
    expect(isWorkPage("/portfolio")).toBe(false);
    expect(isWorkPage("/actions")).toBe(false);
  });

  it("computes each preset from full UTC days ending yesterday, and recognises it back", () => {
    const expected = {
      yesterday: { from: "2026-10-06", to: "2026-10-06" },
      "7d": { from: "2026-09-30", to: "2026-10-06" },
      "30d": { from: "2026-09-07", to: "2026-10-06" },
      month: { from: "2026-10-01", to: "2026-10-06" },
      lastmonth: { from: "2026-09-01", to: "2026-09-30" },
    } as const;
    for (const [key, range] of Object.entries(expected)) {
      expect(presetRange(key as keyof typeof expected, NOW)).toEqual(range);
      expect(presetOf(range.from, range.to, NOW)).toBe(key);
    }
    expect(presetOf("2026-10-01", "2026-10-08", NOW)).toBe("custom");
  });
});

describe("SR-1 withRange and the rail search", () => {
  it("adds the current range in the instant form every page reads, and nothing page-only", () => {
    const params = new URLSearchParams("from=2026-09-30&to=2026-10-06&known_at=2026-10-04T12:00:00Z&cursor=c1&lens=cost&day=2026-10-02");
    const carried = "from=2026-09-30T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z&known_at=2026-10-04T12%3A00%3A00Z";
    expect(rangeSearch(params)).toBe(`?${carried}`);
    expect(withRange("/findings", params)).toBe(`/findings?${carried}`);
    expect(withRange("/findings?state=merged", params)).toBe(`/findings?state=merged&${carried}`);
    // A link that names its own range keeps it.
    expect(withRange("/sites/X?from=2026-01-01&to=2026-01-02", params)).toBe("/sites/X?from=2026-01-01&to=2026-01-02");
    // No range, or a bad one, carries nothing.
    expect(withRange("/findings", new URLSearchParams(""))).toBe("/findings");
    expect(withRange("/findings", new URLSearchParams("from=2026-10-06"))).toBe("/findings");
  });

  it("every live rail link carries the address range", async () => {
    renderApp(`/portfolio?${WEEK}&known_at=2026-10-04T12%3A00%3A00Z`);
    await settledScreen();
    const carried = `?${WEEK}&known_at=2026-10-04T12%3A00%3A00Z`;
    for (const label of ["Portfolio", "Sites", "Findings", "Actions", "Incidents", "Maintenance", "Operational records", "Evidence", "Financials"]) {
      expect(railHref(label)).toBe(`/${label === "Operational records" ? "operational-records" : label.toLowerCase()}${carried}`);
    }
  });

  it("an address with no range leaves the rail links bare", async () => {
    renderApp("/sites");
    await settledScreen();
    expect(railHref("Findings")).toBe("/findings");
    expect(where()).toBe("/sites");
  });
});

describe("SR-1 filling in the address on entry", () => {
  it("an estate page with no range gets the default range in its address, without a history entry", async () => {
    const client = estate();
    renderApp("/portfolio", client);
    await settledScreen();
    expect(where()).toBe(`/portfolio?${WEEK}`);
    // The page reads once, for the range now in the address (the same request it made before SR-1).
    expect(client.calls.map((q) => [q.from, q.to])).toEqual([["2026-09-30T00:00:00Z", "2026-10-07T00:00:00Z"]]);
  });

  it("uses the last range chosen in this browser tab", async () => {
    window.sessionStorage.setItem(SHARED_RANGE_SESSION_KEY, "from=2026-09-07T00:00:00Z&to=2026-10-07T00:00:00Z");
    renderApp("/findings");
    await settledScreen();
    expect(where()).toBe("/findings?from=2026-09-07T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z");
  });

  it("fills only the estate pages in SR-1; Work and Site pages keep their own default until SR-2", () => {
    for (const path of ["/portfolio", "/portfolio/act-first", "/findings", "/findings/risks", "/actions", "/evidence", "/financials"]) {
      expect(fillsRangeOnEntry(path)).toBe(true);
    }
    for (const path of ["/sites", "/sites/KOBO-001", "/incidents", "/maintenance", "/operational-records", "/findings/x/y"]) {
      expect(fillsRangeOnEntry(path)).toBe(false);
    }
  });
});

describe("SR-1 the shared range bar", () => {
  it("sits in the shell top bar above the demonstration banner and names the whole state", async () => {
    renderApp(`/portfolio?${WEEK}`);
    await settledScreen();
    const bar = document.querySelector("[data-shared-range-topbar]") as HTMLElement;
    const banner = document.querySelector("[data-demonstration-banner]") as HTMLElement;
    expect(bar.compareDocumentPosition(banner) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(rangeButton().getAttribute("aria-label")).toBe("Date range for every page: Last 7 days, 30 Sep 2026 to 6 Oct 2026. Change");
    expect(rangeButton().getAttribute("aria-expanded")).toBe("false");
    expect(within(rangeButton()).getByText("30 Sep – 6 Oct 2026")).toBeTruthy();
    expect(within(rangeButton()).getByText("All pages")).toBeTruthy();
    // The Portfolio no longer has its own date form.
    expect(document.querySelector("[data-estate-date-bar]")).toBeNull();
  });

  it("opens with focus on the selected preset; Escape and Cancel close it and return focus to the button", async () => {
    renderApp(`/portfolio?${WEEK}`);
    await settledScreen();
    fireEvent.click(rangeButton());
    const dialog = screen.getByRole("dialog", { name: "Date range for every page" });
    expect(rangeButton().getAttribute("aria-expanded")).toBe("true");
    expect(rangeButton().getAttribute("aria-controls")).toBe(dialog.id);
    const week = within(dialog).getByRole("button", { name: "Last 7 days" });
    expect(week.getAttribute("aria-pressed")).toBe("true");
    expect(document.activeElement).toBe(week);
    expect(within(dialog).queryByRole("button", { name: "Today" })).toBeNull();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("dialog", { name: "Date range for every page" })).toBeNull();
    expect(document.activeElement).toBe(rangeButton());

    fireEvent.click(rangeButton());
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Cancel" }));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(rangeButton());
    expect(where()).toBe(`/portfolio?${WEEK}`);
  });

  it("changes nothing until Apply; Apply writes the range, keeps the lens, restarts at page one and announces it", async () => {
    renderApp(`/portfolio/act-first?${WEEK}&lens=cost&cursor=c9`);
    await settledScreen();
    fireEvent.click(rangeButton());
    const dialog = screen.getByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "Last 30 days" }));
    expect(within(dialog).getByRole("button", { name: "Last 30 days" }).getAttribute("aria-pressed")).toBe("true");
    expect(within(dialog).getByRole("button", { name: "Last 7 days" }).getAttribute("aria-pressed")).toBe("false");
    expect(where()).toBe(`/portfolio/act-first?${WEEK}&lens=cost&cursor=c9`);
    fireEvent.click(within(dialog).getByRole("button", { name: "Apply" }));
    await settledScreen();
    expect(where()).toBe("/portfolio/act-first?from=2026-09-07T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z&lens=cost");
    expect(document.activeElement).toBe(rangeButton());
    expect(document.querySelector("[data-shared-range-live]")?.textContent).toBe("Every page now shows 7 Sep – 6 Oct 2026");
  });

  it("SR-2b L1: a range change clears an open record as well as the cursor, and keeps the lens", async () => {
    renderApp(`/portfolio/act-first?${WEEK}&lens=cost&cursor=c9&record=r1`);
    await settledScreen();
    fireEvent.click(rangeButton());
    const dialog = screen.getByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "Last 30 days" }));
    fireEvent.click(within(dialog).getByRole("button", { name: "Apply" }));
    await settledScreen();
    expect(where()).toBe("/portfolio/act-first?from=2026-09-07T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z&lens=cost");
  });

  it("a custom range has labelled date inputs and rejects a backwards range", async () => {
    renderApp(`/portfolio?${WEEK}`);
    await settledScreen();
    fireEvent.click(rangeButton());
    const dialog = screen.getByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "Custom" }));
    const from = within(dialog).getByLabelText("From") as HTMLInputElement;
    const to = within(dialog).getByLabelText("to (included)") as HTMLInputElement;
    expect([from.type, to.type]).toEqual(["date", "date"]);
    fireEvent.change(from, { target: { value: "2026-10-05" } });
    fireEvent.change(to, { target: { value: "2026-10-01" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Apply" }));
    expect(where()).toBe(`/portfolio?${WEEK}`);
    expect(within(dialog).getByRole("alert").textContent).toBe("Choose a first day on or before the last day, 31 days at most.");
    fireEvent.change(to, { target: { value: "2026-10-06" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Apply" }));
    await settledScreen();
    expect(where()).toBe("/portfolio?from=2026-10-05T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z");
  });

  it("an earlier point in time shows on the bar for every page and Return to latest clears it", async () => {
    renderApp(`/findings?${WEEK}&known_at=2026-10-04T12%3A00%3A00Z`);
    await settledScreen();
    const label = document.querySelector("[data-shared-range-asof]") as HTMLElement;
    expect(label.textContent).toContain("As known at 4 Oct 2026, 12:00 · every page");
    expect(rangeButton().getAttribute("aria-label")).toBe(
      "Date range for every page: Last 7 days, 30 Sep 2026 to 6 Oct 2026, as known at 4 Oct 2026, 12:00. Change",
    );
    fireEvent.click(within(label).getByRole("button", { name: "Return to latest" }));
    await settledScreen();
    expect(where()).toBe(`/findings?${WEEK}`);
    expect(document.querySelector("[data-shared-range-asof]")).toBeNull();
  });

  it("a bad address range says Window not valid and echoes no dates", async () => {
    renderApp("/portfolio?from=2026-10-07T00%3A00%3A00Z&to=2026-10-05T00%3A00%3A00Z");
    await settledScreen();
    expect(rangeButton().textContent).toContain("Window not valid");
    expect(rangeButton().textContent).not.toContain("Oct");
  });
});

describe("SR-1 review notes closed in SR-2", () => {
  it("Medium: the bar says All pages only on pages that read the range, and says so where it is not used", async () => {
    for (const path of ["/portfolio", "/portfolio/act-first", "/findings/risks", "/actions", "/evidence", "/financials", "/incidents", "/maintenance", "/maintenance/preventive", "/operational-records"]) {
      expect(readsSharedRange(path)).toBe(true);
    }
    for (const path of ["/sites", "/sites/KOBO-001", "/sites/COLD-LAB-001", "/sites/EV-LAB-001/ev", "/findings/f-1", "/maintenance/requests/c-1"]) {
      expect(readsSharedRange(path)).toBe(false);
    }
    const withRange = new URLSearchParams(WEEK);
    for (const path of ["/sites/KISIWA-001/findings", "/sites/COLD-LAB-001", "/sites/EV-LAB-001/ev", "/performance/service"]) {
      expect(readsSharedRange(path, withRange)).toBe(true);
    }
    expect(readsSharedRange("/sites", withRange)).toBe(false);
    expect(readsSharedRange("/findings/f-1", withRange)).toBe(false);
  });

  it("the label is true per route class, including a demo story link", async () => {
    // Estate page: the range is used.
    const estate = renderApp(`/findings?${WEEK}`);
    await settledScreen();
    expect(within(rangeButton()).getByText("All pages")).toBeTruthy();
    estate.unmount();
    // Site page that reads the range (demo story link shape).
    const story = renderApp(`/sites/KISIWA-001/findings?${WEEK}`);
    await settledScreen();
    expect(within(rangeButton()).getByText("All pages")).toBeTruthy();
    expect(within(rangeButton()).queryByText("Not used on this page")).toBeNull();
    story.unmount();
    // Site day board with no range in the address: no claim of a shared range, and no self-contradiction.
    const board = renderApp("/sites/MG-002");
    await settledScreen();
    expect(rangeButton().textContent).toContain("This page's own dates");
    expect(within(rangeButton()).queryByText("All pages")).toBeNull();
    expect(within(rangeButton()).queryByText("Not used on this page")).toBeNull();
    board.unmount();
    // Record page that ignores the range.
    renderApp(`/maintenance/requests/c-1?${WEEK}&known_at=2026-10-04T12%3A00%3A00Z`);
    await settledScreen();
    const button = screen.getByRole("button", { name: /^Date range for the other pages: Last 7 days/ });
    expect(button.getAttribute("aria-label")).toContain("This page shows its own dates, not this range. Change");
    expect(within(button).queryByText("All pages")).toBeNull();
    expect(within(button).getByText("Not used on this page")).toBeTruthy();
    expect(document.querySelector("[data-shared-range-asof]")?.textContent).toContain("· other pages");
  });

  it("Low: reopening the picker and pressing Apply keeps the cutoff's seconds", async () => {
    renderApp(`/findings?${WEEK}&known_at=2026-10-04T12%3A00%3A30Z`);
    await settledScreen();
    fireEvent.click(rangeButton());
    const dialog = screen.getByRole("dialog");
    expect((within(dialog).getByLabelText("As known at") as HTMLInputElement).value).toMatch(/^2026-10-04T12:00:30(\.000)?$/);
    fireEvent.click(within(dialog).getByRole("button", { name: "Apply" }));
    await settledScreen();
    expect(where()).toBe(`/findings?${WEEK}&known_at=2026-10-04T12%3A00%3A30Z`);
  });

  it("Low: only a range chosen in the bar is remembered, never one that arrived in an address", async () => {
    renderApp("/portfolio?from=2026-10-01T10%3A00%3A00Z&to=2026-10-01T14%3A00%3A00Z");
    await settledScreen();
    expect(window.sessionStorage.getItem(SHARED_RANGE_SESSION_KEY)).toBeNull();
    fireEvent.click(rangeButton());
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Last 30 days" }));
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Apply" }));
    await settledScreen();
    expect(window.sessionStorage.getItem(SHARED_RANGE_SESSION_KEY)).toBe("from=2026-09-07T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z");
  });
});

describe("SR-1 the Portfolio reads the shared range", () => {
  it("a day-form address makes the same request as the instant form, and Apply reads the new range", async () => {
    const client = estate();
    renderApp("/portfolio?from=2026-10-06&to=2026-10-06", client);
    await settledScreen();
    expect(client.calls.map((q) => [q.from, q.to, q.known_at, q.lens])).toEqual([
      ["2026-10-06T00:00:00Z", "2026-10-07T00:00:00Z", null, "all"],
    ]);
    expect(rangeButton().getAttribute("aria-label")).toBe("Date range for every page: Yesterday, 6 Oct 2026. Change");
    fireEvent.click(rangeButton());
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Last 7 days" }));
    await act(async () => {
      fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Apply" }));
    });
    await settledScreen();
    expect(client.calls.map((q) => [q.from, q.to])).toEqual([
      ["2026-10-06T00:00:00Z", "2026-10-07T00:00:00Z"],
      ["2026-09-30T00:00:00Z", "2026-10-07T00:00:00Z"],
    ]);
    // Tab links carry the shared range.
    const tabs = screen.getByRole("navigation", { name: "Portfolio sections" });
    expect(within(tabs).getByRole("link", { name: /^What changed/ }).getAttribute("href")).toBe(`/portfolio/changes?${WEEK}`);
  });
});
