/**
 * 5c unit 3 (spec §6 tests 10 to 13): "The month" renders the server's JSON as given (D-5C.2). World A is the
 * hand-written fixture of spec §3.5 (`backend/tests/fixtures/5c/deep_dive_lakeside_2026-10.json`); World H is A with
 * §3.5 H's changes written here by hand (with unit 1's KD1 for the Diesel price driver).
 */
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import { settledScreen } from "../../test/settled";
import { DeepDiveMonthFrame } from "../DeepDiveMonth";
import type { DeepDiveMonthBody, DeepDiveMonthClient, DeepDiveResult } from "../deepDiveMonthClient";
import { PORTFOLIO_TABS } from "../portfolioWords";
import { fakeClient, findingsBody, loaded } from "./estateFixtures";
import { loadedPortfolio, portfolioBody } from "./portfolioFixtures";
import FIXTURE_TEXT from "../../../../backend/tests/fixtures/5c/deep_dive_lakeside_2026-10.json?raw";
import TABS_BEFORE from "./fixtures/portfolioTabsOverview.before.html?raw";

const worldA = (): DeepDiveMonthBody => JSON.parse(FIXTURE_TEXT) as DeepDiveMonthBody;

/** Keys whose values are codes or numbers for the page, not words for the reader. */
const NOT_SHOWN = new Set(["schema", "month", "nav", "state", "as_of", "reason", "reconciled", "key", "bar", "connected", "more", "standing"]);

function strings(value: unknown, out: string[] = []): string[] {
  if (typeof value === "string") out.push(value);
  else if (Array.isArray(value)) value.forEach((v) => strings(v, out));
  else if (value !== null && typeof value === "object") {
    for (const [k, v] of Object.entries(value)) if (!NOT_SHOWN.has(k) && k !== "drawer") strings(v, out);
  }
  return out;
}

function worldH(): DeepDiveMonthBody {
  const h = worldA();
  const SETUP = "a generator and a fuel tank declared in the Site's setup (litres are worked out for each)";
  const stop =
    "Not split further until the EMS interval export (generator running and output, solar available power, battery charge), " +
    "the generator's fuel curve (litres per kWh; litres per hour idle), tank dips at the start and end of the month, fuel delivery " +
    `notes and ${SETUP}.`;
  const untracked =
    "Not checked for later changes: Diesel not shown to be avoidable (Kobo), Diesel run while solar and battery could carry the " +
    "load (Kobo) and Unexplained fuel (Kobo).";
  h.tiles![1].lines[1] = "$252.00 of it not split to its drivers yet";
  const fuel = h.bridge!.groups[1].steps[0].drawer;
  fuel.sites = [
    { site: "Kobo", value: "−$600.00", text: null },
    { site: "Kisiwa", value: "−$130.00", text: stop },
    { site: "Mto", value: "−$25.00", text: stop },
  ];
  const m = "Modelled, not yet reconciled";
  fuel.drivers = [
    { label: "Diesel used", value: "−$600.00", sites: "1 of 3 Sites", detail: "Actual 1,180 L · Target 700 L", word: m },
    { label: "Diesel not shown to be avoidable", value: "−$37.50", sites: "1 of 3 Sites", detail: "Actual 730 L · Target 700 L", word: m },
    { label: "Diesel run while solar and battery could carry the load", value: "−$412.50", sites: "1 of 3 Sites", detail: "Actual 330 L · Target 0 L", word: m },
    { label: "Unexplained fuel", value: "−$150.00", sites: "1 of 3 Sites", detail: "Actual 120 L · Target 0 L", word: m },
    { label: "Diesel price", value: "$0.00", sites: "1 of 3 Sites", detail: null, word: m },
  ];
  h.fresh = { current: true, text: null, untracked_text: untracked };
  h.outcomes![3].drawer!.lines = [...h.outcomes![3].drawer!.lines, untracked];
  return h;
}

function stateBody(state: "NO_SNAPSHOT" | "REBUILD_NEEDED", text: string): DeepDiveMonthBody {
  return {
    schema: "deep-dive-month-1",
    operator: "Lakeside Power",
    month: state === "NO_SNAPSHOT" ? "2026-09" : "2026-10",
    month_words: state === "NO_SNAPSHOT" ? "September 2026" : "October 2026",
    nav: state === "NO_SNAPSHOT" ? { previous: "2026-08", next: "2026-10" } : { previous: "2026-09", next: null },
    state,
    state_text: text,
  };
}

function clientOf(answer: (month?: string) => DeepDiveResult): DeepDiveMonthClient & { calls: (string | undefined)[] } {
  const calls: (string | undefined)[] = [];
  return {
    calls,
    fetchDeepDiveMonth: (month?: string) => {
      calls.push(month);
      return Promise.resolve(answer(month));
    },
  };
}

function LocationProbe() {
  const location = useLocation();
  return <div data-location>{`${location.pathname}${location.search}`}</div>;
}

function renderMonth(client: DeepDiveMonthClient, path = "/portfolio/month?month=2026-10") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/portfolio/month" element={<DeepDiveMonthFrame client={client} />} />
      </Routes>
      <LocationProbe />
    </MemoryRouter>,
  );
}

async function settled() {
  await settledScreen();
  expect(document.body.textContent).not.toContain("Preparing the month…");
}

function openDialog(): HTMLElement {
  return screen.getByRole("dialog");
}

describe("5c test 10: World A renders", () => {
  it("shows every string of spec §3.5 outside the drawers, the notice visible and the status line a status", async () => {
    const a = worldA();
    const view = renderMonth(clientOf(() => ({ status: "loaded", body: a })));
    await settled();
    expect(screen.queryByRole("dialog")).toBeNull();
    // Show all the not-available rows (8 shown, then "Show all {n}").
    fireEvent.click(screen.getByRole("button", { name: `Show all ${a.not_available!.rows.length}` }));
    const text = view.container.textContent ?? "";
    for (const s of strings(a)) expect(text, s).toContain(s);
    expect(text).toContain(a.headline!.evidence[0]);
    // D-5C.13: never the uncarried composition.
    expect(text).not.toContain("$1,693.00");
    // The notice is visible with every drawer closed, never inside a dialog (P5).
    const note = screen.getByRole("note");
    expect(note.textContent).toBe(a.notices![0]);
    expect(note.closest("[role=dialog]")).toBeNull();
    expect(note.closest("details")).toBeNull();
    // The status line is a status and names Kisiwa (P18).
    const status = screen.getByRole("status");
    expect(status.textContent).toBe(a.status_line);
    expect(status.textContent).toContain("Kisiwa");
    // Kisiwa's carried O&M reads "(estimate)" in the by-Site table (P6).
    expect(text).toContain("$0.00 (estimate)");
  });

  it("opens every step drawer and the Assure drawer with their lines", async () => {
    const a = worldA();
    renderMonth(clientOf(() => ({ status: "loaded", body: a })));
    await settled();
    for (const group of a.bridge!.groups) {
      for (const step of group.steps) {
        fireEvent.click(screen.getByRole("button", { name: new RegExp(`^${step.label.replace(/[&]/g, "\\$&")} `) }));
        const dialog = openDialog();
        const dtext = dialog.textContent ?? "";
        for (const s of strings(step.drawer)) expect(dtext, s).toContain(s);
        fireEvent.keyDown(dialog, { key: "Escape" });
        expect(screen.queryByRole("dialog")).toBeNull();
      }
    }
    const assure = a.outcomes!.find((o) => o.key === "assure")!;
    fireEvent.click(screen.getByRole("button", { name: assure.value }));
    const dialog = screen.getByRole("dialog", { name: assure.drawer!.title });
    const items = within(dialog).getAllByRole("listitem").map((li) => li.textContent);
    expect(items).toEqual([a.standing!.text, ...a.standing!.details!]);
  });

  it("World B: no 'not yet reconciled' suffix is added by the page", async () => {
    const b = worldA();
    const strip = (s: string) => s.replace(", not yet reconciled", "");
    b.tiles!.forEach((t) => (t.word = t.word === null ? null : strip(t.word)));
    b.status_line = "Figures as of 20 November 2026, 08:00 UTC. Reconciled with the management accounts. Kisiwa's budget disagrees with its own lines.";
    b.bridge!.groups.forEach((g) => g.steps.forEach((s) => (s.word = s.word === null ? null : strip(s.word))));
    b.cash!.word = strip(b.cash!.word!);
    b.outcomes!.forEach((o) => (o.word = o.word === null ? null : strip(o.word)));
    b.outcomes![3].value = "Reconciled";
    const view = renderMonth(clientOf(() => ({ status: "loaded", body: b })));
    await settled();
    expect(view.container.textContent).not.toContain("not yet reconciled");
  });
});

describe("5c test 11: drawers keep and return focus; drivers carry their words", () => {
  it("a step drawer is a labelled dialog, focus moves to Close, Escape closes and returns focus", async () => {
    const h = worldH();
    renderMonth(clientOf(() => ({ status: "loaded", body: h })));
    await settled();
    const opener = screen.getByRole("button", { name: /^Fuel cost / });
    opener.focus();
    fireEvent.click(opener);
    const dialog = screen.getByRole("dialog", { name: "Fuel cost" });
    expect(dialog.getAttribute("aria-modal")).toBe("true");
    expect(document.activeElement).toBe(within(dialog).getByRole("button", { name: "Close" }));
    // Every driver shows label, value, word chip, sites and detail (P13).
    const rows = dialog.querySelectorAll("[data-dd-driver]");
    expect(rows.length).toBe(h.bridge!.groups[1].steps[0].drawer.drivers.length);
    h.bridge!.groups[1].steps[0].drawer.drivers.forEach((d, i) => {
      const row = rows[i] as HTMLElement;
      expect(row.textContent).toContain(d.label);
      expect(row.textContent).toContain(d.value);
      expect(row.textContent).toContain(d.sites);
      if (d.detail !== null) expect(row.textContent).toContain(d.detail);
      expect(row.querySelector("[data-dd-word]")?.textContent).toBe(d.word);
    });
    expect(dialog.textContent).toContain("Modelled, not yet reconciled");
    fireEvent.keyDown(dialog, { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(opener);
  });

  it("a driver with a depth nests inside its parent, never beside it (coordinator note L2)", async () => {
    const h = worldH();
    const drivers = h.bridge!.groups[1].steps[0].drawer.drivers;
    drivers.forEach((d, i) => (d.depth = i >= 1 && i <= 3 ? 1 : 0));
    renderMonth(clientOf(() => ({ status: "loaded", body: h })));
    await settled();
    fireEvent.click(screen.getByRole("button", { name: /^Fuel cost / }));
    const dialog = screen.getByRole("dialog", { name: "Fuel cost" });
    const top = dialog.querySelectorAll(".dd-drivers:not(.dd-drivers--parts) > [data-dd-driver]");
    expect([...top].map((li) => li.querySelector(".dd-driver__label")!.textContent)).toEqual(["Diesel used", "Diesel price"]);
    const parts = within(dialog).getByRole("list", { name: "Parts of Diesel used" });
    expect(parts.closest("[data-dd-driver]")!.querySelector(".dd-driver__label")!.textContent).toBe("Diesel used");
    expect(within(parts).getAllByRole("listitem").map((li) => li.querySelector(".dd-driver__label")!.textContent)).toEqual([
      "Diesel not shown to be avoidable",
      "Diesel run while solar and battery could carry the load",
      "Unexplained fuel",
    ]);
  });

  it("the scrim and Close close the drawer and return focus (P12)", async () => {
    renderMonth(clientOf(() => ({ status: "loaded", body: worldH() })));
    await settled();
    const opener = screen.getByRole("button", { name: /^Revenue / });
    fireEvent.click(opener);
    fireEvent.click(document.querySelector("[data-dd-scrim]")!);
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(opener);
    fireEvent.click(opener);
    fireEvent.click(within(openDialog()).getByRole("button", { name: "Close" }));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(opener);
  });

  it("World H's Assure drawer adds the not-checked line", async () => {
    const h = worldH();
    renderMonth(clientOf(() => ({ status: "loaded", body: h })));
    await settled();
    fireEvent.click(screen.getByRole("button", { name: "Not yet reconciled" }));
    const items = within(openDialog()).getAllByRole("listitem").map((li) => li.textContent);
    expect(items).toEqual(h.outcomes![3].drawer!.lines);
    expect(items[items.length - 1]).toBe(h.fresh!.untracked_text);
  });
});

describe("5c test 12: states and the month links", () => {
  it("NO_SNAPSHOT and REBUILD_NEEDED show the header and the state text only", async () => {
    for (const [state, text] of [
      ["NO_SNAPSHOT", "The figures for September 2026 have not been prepared yet."],
      ["REBUILD_NEEDED", "The figures for October 2026 must be prepared again before they can be shown."],
    ] as const) {
      const view = renderMonth(clientOf(() => ({ status: "loaded", body: stateBody(state, text) })));
      await settled();
      expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Portfolio");
      expect(view.container.textContent).toContain(text);
      expect(view.container.querySelector("[data-level]")).toBeNull();
      expect(screen.queryByRole("status")).toBeNull();
      view.unmount();
    }
  });

  it("503 shows the served text with Try again, which reads again", async () => {
    let n = 0;
    const client = clientOf(() => {
      n += 1;
      return n === 1
        ? { status: "refused", httpStatus: 503, code: "DEEP_DIVE_UNAVAILABLE", text: "The month's figures cannot be read right now." }
        : { status: "loaded", body: worldA() };
    });
    renderMonth(client);
    await settled();
    expect(document.body.textContent).toContain("The month's figures cannot be read right now.");
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    });
    await settled();
    expect(client.calls.length).toBe(2);
    expect(screen.getByRole("status").textContent).toBe(worldA().status_line);
  });

  it("401 asks to sign in", async () => {
    renderMonth(clientOf(() => ({ status: "refused", httpStatus: 401, code: "PERSON_REQUIRED", text: "Sign in to continue." })));
    await settled();
    expect(document.body.textContent).toContain("Sign in to see this operator's figures.");
    expect(document.querySelector("[data-level]")).toBeNull();
  });

  it("the month links set ?month= and read that month; next is disabled without a next month", async () => {
    const client = clientOf((month) =>
      month === "2026-09"
        ? { status: "loaded", body: stateBody("NO_SNAPSHOT", "The figures for September 2026 have not been prepared yet.") }
        : { status: "loaded", body: worldA() },
    );
    renderMonth(client);
    await settled();
    expect(client.calls).toEqual(["2026-10"]);
    const next = screen.getByRole("button", { name: /November 2026/ });
    expect((next as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(screen.getByRole("link", { name: /September 2026/ }));
    await settled();
    expect(document.querySelector("[data-location]")!.textContent).toBe("/portfolio/month?month=2026-09");
    expect(client.calls).toEqual(["2026-10", "2026-09"]);
    expect(screen.getByRole("link", { name: /October 2026/ }).getAttribute("href")).toBe("/portfolio/month?month=2026-10");
  });

  it("with no ?month= the client is asked for the server's default month", async () => {
    const client = clientOf(() => ({ status: "loaded", body: worldA() }));
    renderMonth(client, "/portfolio/month");
    await settled();
    expect(client.calls).toEqual([undefined]);
  });
});

describe("5c test 13: the tab row moves to PortfolioTabs.tsx unchanged", () => {
  const DIRECTORY: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [] }) };
  const DETAIL: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }) };
  const normal = (html: string) => html.replace(/from=[^&"]*&amp;to=[^&"]*/g, "from=FROM&amp;to=TO").trim();

  it("the Overview's tab row (with counts) equals its markup before the move, plus the month tab", async () => {
    const before = TABS_BEFORE;
    const client = { ...fakeClient((lens) => loaded(findingsBody(lens))), portfolio: () => Promise.resolve(loadedPortfolio(portfolioBody())) };
    const view = render(
      <MemoryRouter initialEntries={["/portfolio"]}>
        <App flags={featureFlagsWith(false)} siteDirectory={DIRECTORY} siteDetail={DETAIL} estateIndex={client} />
      </MemoryRouter>,
    );
    await settledScreen();
    const row = view.container.querySelector("[data-portfolio-tabs]")!;
    const items = row.querySelectorAll("li");
    expect(items[1].textContent).toBe("The month");
    expect(items[1].querySelector("a")!.getAttribute("href")).toBe("/portfolio/month");
    expect(items[1].querySelector("[data-pf-tab-count]")).toBeNull();
    const clone = row.cloneNode(true) as HTMLElement;
    clone.querySelectorAll("li")[1].remove();
    expect(normal(clone.outerHTML)).toBe(normal(before));
    expect(PORTFOLIO_TABS[1]).toEqual({ tab: "month", label: "The month", segment: "month" });
  });

  it("the month page shows the tab row with The month current and no counts", async () => {
    renderMonth(clientOf(() => ({ status: "loaded", body: worldA() })));
    await settled();
    const row = document.querySelector("[data-portfolio-tabs]")!;
    expect(row.querySelector("[aria-current=page]")!.textContent).toBe("The month");
    expect(row.querySelector("[data-pf-tab-count]")).toBeNull();
    const overview = within(row as HTMLElement).getByRole("link", { name: "Overview" });
    expect(overview.getAttribute("href")).toMatch(/^\/portfolio\?from=/);
  });
});
