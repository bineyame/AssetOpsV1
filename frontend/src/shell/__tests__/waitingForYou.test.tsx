/**
 * IA-P P6 (spec §6 P6; D-IAP.37 Q12 to Q16): "Waiting for you", the top-bar control and its drawer. The badge is the
 * Decisions tile's "Waiting for a choice" figure from the one shared function, read through the Decisions read's
 * cache key (one read for both). Each figure is a literal.
 */
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { computeAccessibleName } from "dom-accessibility-api";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { LinkedMemoryRouter as MemoryRouter } from "../../test/refLinks";
import { settledScreen } from "../../test/settled";
import type { EstateClient, EstatePortfolioBody, EstatePortfolioRow, EstateProgressRow, EstateResult } from "../../estate/estateClient";
import { EstateReadCacheProvider } from "../../estate/estateReadCache";
import { DecisionsListPage, decisionItems, waitingForAChoice } from "../../estate/homeLists";
import { loaded } from "../../estate/__tests__/estateFixtures";
import { portfolioBody, row } from "../../estate/__tests__/portfolioFixtures";
import { WaitingForYou } from "../WaitingForYou";

beforeEach(() => {
  window.scrollTo = vi.fn();
});
afterEach(cleanup);

const RANGE = "from=2026-10-13T00:00:00Z&to=2026-10-20T00:00:00Z";

function id(n: number): string {
  return `f1f1f1f1-0000-4000-8000-${String(n).padStart(12, "0")}`;
}

/** n placed Findings: the 1st is Monitor (watching), the 2nd has an Action (underway), the rest wait. */
function decisionRows(n: number): EstatePortfolioRow[] {
  return Array.from({ length: n }, (_, k) => {
    const i = k + 1;
    const base: Partial<EstatePortfolioRow> = {
      finding_id: id(i),
      finding_revision_id: id(10000 + i),
      title: `Decision ${i}`,
      site_name: i % 2 === 0 ? "Kobo" : "Aliyu",
      links: { site: "/sites/KOBO-001", finding: `/sites/KOBO-001/findings/${id(i)}?revision_id=${id(10000 + i)}`, action: null },
    };
    if (i === 1) base.placement = { policy_version: "estate-placement/1", group: "MONITOR", group_rank: 5, reasons: [] };
    if (i === 2) base.action_id = "a2a2a2a2-0000-4000-8000-000000000002";
    return row(base);
  });
}

function progressRow(n: number, outcome: string | null): EstateProgressRow {
  return {
    action_id: `a0a0a0a0-0000-4000-8000-${String(n).padStart(12, "0")}`,
    action_code: `ACT-00${n}`,
    selected_action_event_id: null,
    verification_plan_id: null,
    verification_outcome_id: null,
    application_state: null,
    resolution_state: null,
    verification_outcome: outcome,
    recorded_at: null,
    origin_revision_selected: true,
  };
}

function client(rows: EstatePortfolioRow[], over: Partial<EstatePortfolioBody> = {}, size = 50): EstateClient & { calls: number } {
  const pages: EstateResult<EstatePortfolioBody>[] = [];
  for (let at = 0; at < Math.max(rows.length, 1); at += size) {
    const last = at + size >= rows.length;
    pages.push(loaded(portfolioBody({ ...over, rows: rows.slice(at, at + size), total_count: rows.length, next_cursor: last ? null : `c${at + size}` })));
  }
  const fake = {
    calls: 0,
    findings: async () => Promise.reject(new Error("no findings")),
    actions: async () => Promise.reject(new Error("no actions")),
    scope: async () => Promise.reject(new Error("no scope")),
    portfolio: async (query: { cursor: string | null }) => {
      if (query.cursor === null) fake.calls += 1;
      return pages[query.cursor === null ? 0 : Number(query.cursor.slice(1)) / size];
    },
  };
  return fake as unknown as EstateClient & { calls: number };
}

/** The shell's control beside a page, under one read cache (as `OperatorShellLayout` mounts them). */
function mount(reads: EstateClient, at = `/decisions?${RANGE}`) {
  return render(
    <MemoryRouter initialEntries={[at]}>
      <EstateReadCacheProvider>
        <WaitingForYou client={reads} />
        <Routes>
          <Route path="/decisions" element={<DecisionsListPage client={reads} />} />
          <Route path="*" element={<p>Elsewhere</p>} />
        </Routes>
      </EstateReadCacheProvider>
    </MemoryRouter>,
  );
}

const control = () => document.querySelector<HTMLButtonElement>("button.ia-inbox")!;
const badge = () => control().querySelector(".ia-inbox__badge");
const tileWaiting = () => screen.getByText("Waiting for a choice", { selector: ".hl-tile__label" }).parentElement!.querySelector("strong")!.textContent;

async function openDrawer() {
  fireEvent.click(control());
  return screen.getByRole("dialog", { name: "Waiting for you" });
}

describe("the badge is the Decisions tile's Waiting for a choice (W1, D-IAP.37 Q13)", () => {
  it("25 placed Findings, 23 waiting: badge = tile = 23, from one read", async () => {
    const reads = client(decisionRows(25));
    mount(reads);
    await settledScreen();
    expect(tileWaiting()).toBe("23");
    expect(badge()!.textContent).toBe("23, 23 waiting");
    expect(control().getAttribute("aria-haspopup")).toBe("dialog");
    expect(control().getAttribute("aria-controls")).toBe("ia-inbox");
    expect(control().getAttribute("type")).toBe("button");
    // jsdom puts a space between the label's and the hidden text's spans; a browser joins inline spans as written.
    expect(computeAccessibleName(control()).replace(/ ,/g, ",")).toBe("Waiting for you, 23 waiting");
    expect(reads.calls).toBe(1);
  });

  it("truncated at 1,000: badge = tile = the server's waiting_count", async () => {
    const reads = client(decisionRows(1010), { summary: { ...portfolioBody().summary, waiting_count: 1007 } });
    mount(reads);
    await settledScreen();
    expect(tileWaiting()).toBe("1007");
    expect(badge()!.textContent).toBe("1007, 1007 waiting");
  });

  it("the badge is absent at 0", async () => {
    mount(client(decisionRows(2)), `/elsewhere?${RANGE}`);
    await settledScreen();
    expect(control()).toBeTruthy();
    expect(badge()).toBeNull();
  });

  it("waitingForAChoice: the server's total when given, else the waiting rows", () => {
    const body = portfolioBody();
    const items = decisionItems(body, decisionRows(5));
    expect(waitingForAChoice(items, null)).toBe(3);
    expect(waitingForAChoice(items, 40)).toBe(40);
  });
});

describe("the drawer's sections", () => {
  it("For you is not available yet; In your portfolio lists the waiting rows in server order, capped at 10", async () => {
    mount(client(decisionRows(25), { progress: { ...portfolioBody().progress, rows: [1, 2, 3, 4].map((n) => progressRow(n, "SUCCESS")) } }), `/elsewhere?${RANGE}`);
    await settledScreen();
    const dialog = await openDrawer();
    expect(dialog.getAttribute("aria-modal")).toBe("true");
    const forYou = within(dialog).getByRole("region", { name: "For you" });
    expect(forYou.textContent).toContain("Not available yet");
    const portfolio = within(dialog).getByRole("region", { name: "In your portfolio" });
    const links = within(portfolio).getAllByRole("link");
    expect(links).toHaveLength(11);
    expect(links[0].textContent).toBe("Decision 3 Aliyu · Compare value");
    expect(links[0].querySelector("small")!.textContent).toBe("Aliyu · Compare value");
    expect(links[0].getAttribute("href")).toMatch(/^\/sites\/KOBO-001\/findings\/f1f1f1f1-0000-4000-8000-000000000003/);
    expect(links.slice(0, 10).map((l) => l.firstChild!.textContent)).toEqual([3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((n) => `Decision ${n}`));
    const all = links[10];
    expect(all.textContent).toBe("View all 23");
    expect(all.getAttribute("href")).toBe("/decisions?state=waiting&from=2026-10-13T00%3A00%3A00Z&to=2026-10-20T00%3A00%3A00Z");
    const since = within(dialog).getByRole("region", { name: "Since you last looked" });
    const lines = Array.from(since.querySelectorAll("li")).map((li) => li.textContent);
    expect(lines).toHaveLength(3);
    expect(lines[0]).toMatch(/^Action ACT-001 · /);
    const results = within(since).getByRole("link", { name: "See all in Results" });
    expect(results.getAttribute("href")).toBe("/results?from=2026-10-13T00%3A00%3A00Z&to=2026-10-20T00%3A00%3A00Z");
  });

  it("the empty states", async () => {
    mount(client([]), `/elsewhere?${RANGE}`);
    await settledScreen();
    const dialog = await openDrawer();
    expect(within(dialog).getByRole("region", { name: "In your portfolio" }).textContent).toContain("Nothing else is waiting for a choice");
    expect(within(dialog).queryByRole("link", { name: /View all/ })).toBeNull();
    expect(within(dialog).getByRole("region", { name: "Since you last looked" }).textContent).toContain("No change recorded in this range");
  });
});

describe("the focus cycle", () => {
  it("focus moves to Close; Escape closes and focus returns to the control", async () => {
    mount(client(decisionRows(5)), `/elsewhere?${RANGE}`);
    await settledScreen();
    control().focus();
    await openDrawer();
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Close" }));
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(control());
  });

  it("the scrim closes and focus returns; Tab from the last stop wraps to Close", async () => {
    mount(client(decisionRows(5)), `/elsewhere?${RANGE}`);
    await settledScreen();
    control().focus();
    const dialog = await openDrawer();
    const stops = Array.from(dialog.querySelectorAll<HTMLElement>("button, a[href]"));
    stops[stops.length - 1].focus();
    fireEvent.keyDown(document, { key: "Tab" });
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Close" }));
    fireEvent.click(document.querySelector("[data-dd-scrim]")!);
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(control());
  });
});
