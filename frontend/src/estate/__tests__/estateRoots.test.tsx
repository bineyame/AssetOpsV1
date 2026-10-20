/**
 * W3-01 commit 3 named frontend tests (`.agent/W3-01-build-spec.md` "Fixtures and named proof"): the five estate
 * roots under a local MemoryRouter (Lane A mounts the shell routes), against the v6.9 panel structure, with every
 * card, column, chip, link, empty/partial/historical/refusal string asserted.
 */
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { expectV69Panels } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import { EstateActionsPage, ESTATE_ACTIONS_PATH, ACTIONS_LIFECYCLE, ACTIONS_NOTICE } from "../actionIndex";
import { createEstateClient, type EstateClient, type EstateLens } from "../estateClient";
import { AWAITING_RULE, AWAITING_ZERO, ESTATE_FINDING_LENS_PATHS, EstateFindingsPage, FINDINGS_NOTICE } from "../findingIndex";
import {
  FROM,
  KNOWN,
  SITE_A,
  SITE_B,
  TO,
  actionRow,
  actionsBody,
  fakeClient,
  findingRow,
  findingsBody,
  loaded,
  site,
} from "./estateFixtures";

const LENSES: readonly EstateLens[] = ["all", "cost", "risks", "opportunities"];
const SCREEN: Readonly<Record<EstateLens, string>> = {
  all: "findings",
  cost: "findings-cost",
  risks: "findings-risks",
  opportunities: "findings-opportunities",
};

function LocationProbe() {
  const location = useLocation();
  return <output data-testid="location">{`${location.pathname}${location.search}`}</output>;
}

function renderAt(entry: string, client: EstateClient) {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <main>
        <Routes>
          {LENSES.map((lens) => (
            <Route
              key={lens}
              path={ESTATE_FINDING_LENS_PATHS[lens]}
              element={<EstateFindingsPage lens={lens} client={client} />}
            />
          ))}
          <Route path={ESTATE_ACTIONS_PATH} element={<EstateActionsPage client={client} />} />
        </Routes>
      </main>
      <LocationProbe />
    </MemoryRouter>,
  );
}

const WINDOW = `from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}`;

function location(): string {
  return decodeURIComponent(screen.getByTestId("location").textContent ?? "");
}

function main(): HTMLElement {
  return document.querySelector("main") as HTMLElement;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("W3-01 estate roots", () => {
  it("test_five_mock_panels_and_supported_links", async () => {
    const priced = findingRow(2, {
      lens_flags: ["COST"],
      consequence: {
        state: "PRICED",
        amount: "120.00",
        amount_low: "120.00",
        amount_high: "180.00",
        currency: "USD",
        source_revision_id: "10000000-0000-4000-8000-000000000301",
      },
    });
    const client = fakeClient((lens) =>
      loaded(findingsBody(lens, { rows: lens === "cost" ? [priced] : lens === "all" ? [findingRow(1), priced] : [] })),
    );
    for (const lens of LENSES) {
      const view = renderAt(`${ESTATE_FINDING_LENS_PATHS[lens]}?${WINDOW}&cursor=abc&state=supported`, client);
      await settledScreen();
      expectV69Panels(SCREEN[lens]);
      expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Findings");
      // Four live lens tabs keep window and state, drop the cursor; the active one is the page.
      const tabs = within(screen.getByRole("navigation", { name: "Finding lenses" })).getAllByRole("link");
      expect(tabs.map((t) => t.textContent)).toEqual(["All findings", "Cost", "Risks", "Opportunities"]);
      for (const [index, tab] of tabs.entries()) {
        const href = decodeURIComponent(tab.getAttribute("href") ?? "");
        expect(href).toBe(`${ESTATE_FINDING_LENS_PATHS[LENSES[index]]}?from=${FROM}&to=${TO}&state=supported`);
        expect(tab.getAttribute("aria-current")).toBe(LENSES[index] === lens ? "page" : null);
      }
      // Cards, chips and columns.
      const cards = within(screen.getByRole("list", { name: "Findings summary" })).getAllByRole("listitem");
      expect(cards.map((c) => c.querySelector(".v69-metric__label")?.textContent)).toEqual([
        "Supported findings",
        "High priority",
        "Low confidence",
        "Awaiting verification",
      ]);
      const chips = within(screen.getByRole("list", { name: "Workflow state" })).getAllByRole("link");
      expect(chips[0].textContent).toBe("All states");
      expect(chips.map((c) => c.textContent)).toContain("Supported");
      for (const chip of chips) expect(chip.getAttribute("href")).not.toContain("cursor=");
      expect(main().textContent).toContain(FINDINGS_NOTICE);
      expect(main().textContent).toContain("Lens is how a finding is read, not a second object · state is a filter");
      view.unmount();
    }
    // The All root: exact Finding and Site links, priced interval, lens column, and a state chip that restarts at
    // page one.
    renderAt(`/findings?${WINDOW}&cursor=abc`, client);
    await settledScreen();
    const headers = screen.getAllByRole("columnheader").map((h) => h.textContent);
    expect(headers).toEqual(["Finding", "Site", "Priority", "Confidence", "State", "Main consequence", "Lens"]);
    const links = screen.getAllByText("Stored finding title 2");
    expect(links[0].getAttribute("href")).toBe(priced.links.finding);
    expect(screen.getAllByText("KOBO-001")[0].getAttribute("href")).toBe("/sites/KOBO-001");
    expect(main().textContent).toContain("120.00–180.00 USD");
    expect(main().textContent).toContain("No supported lens");
    expect(screen.getByText("First page").getAttribute("href")).not.toContain("cursor=");
    fireEvent.click(screen.getByRole("link", { name: "Supported" }));
    await settledScreen();
    expect(location()).toBe(`/findings?from=${FROM}&to=${TO}&state=supported`);
    // Actions root: panel, cards, columns, exact Action and pinned source links.
    renderAt(`${ESTATE_ACTIONS_PATH}?${WINDOW}`, client);
    await settledScreen();
    expectV69Panels("actions", {}, document.querySelectorAll("main")[1] as HTMLElement);
  });

  it("test_null_cards_partial_and_unpriced_copy", async () => {
    // Partial coverage: null cards, partial line, limitation before the static notice; every consequence state.
    const rows = [
      findingRow(1),
      findingRow(2, {
        consequence: { state: "UNPRICED", amount: null, amount_low: null, amount_high: null, currency: null, source_revision_id: "c2" },
      }),
      findingRow(3, {
        consequence: { state: "UNKNOWN", amount: null, amount_low: null, amount_high: null, currency: null, source_revision_id: "c3" },
      }),
      findingRow(4, {
        lifecycle: "UNCONFIRMED",
        status: "PENDING_RECOMPUTE",
        site_id: SITE_B,
      }),
    ];
    const partial = findingsBody("all", {
      rows,
      status: "PENDING_RECOMPUTE",
      coverage: { state: "PARTIAL", sites: [site(SITE_A, "CURRENT"), site(SITE_B, "PENDING_RECOMPUTE")] },
      total_count: null,
      summary: { high_priority: null, low_confidence: null, awaiting_verification: null, basis_count: null, supported_findings: null },
    });
    let view = renderAt(`/findings?${WINDOW}`, fakeClient(() => loaded(partial)));
    await settledScreen();
    expectV69Panels("findings");
    const cards = within(screen.getByRole("list", { name: "Findings summary" })).getAllByRole("listitem");
    expect(cards.map((c) => c.querySelector(".v69-metric__value")?.textContent)).toEqual([
      "Coverage incomplete",
      "Not assessed",
      "Not assessed",
      "Coverage incomplete",
    ]);
    const text = main().textContent ?? "";
    for (const words of [
      "No consequence recorded",
      "Unpriced",
      "Source unverified",
      "Some sites have no selected result; totals are unknown.",
      "New evidence is being assessed.",
      "Some sites are not yet assessed; estate totals are unknown.",
    ]) {
      expect(text).toContain(words);
    }
    expect(screen.getByRole("link", { name: "Unconfirmed" })).toBeTruthy();
    expect(text).not.toContain("No findings match.");
    const notices = Array.from(main().querySelectorAll(".notice"));
    expect(notices.map((n) => n.hasAttribute("data-estate-limitation"))).toEqual([true, false]);
    view.unmount();

    // Run 12 ruling 3: a live page two read after its cutoff is HISTORICAL at the top level only; the pending Site
    // chip and a withheld historical amount keep their own copy.
    const pageTwo = findingsBody("all", {
      status: "HISTORICAL",
      rows: [
        findingRow(5, { status: "PENDING_RECOMPUTE" }),
        findingRow(6, {
          status: "HISTORICAL",
          consequence: { state: "UNKNOWN", amount: null, amount_low: null, amount_high: null, currency: null, source_revision_id: "c6" },
        }),
      ],
      coverage: { state: "COMPLETE", sites: [site(SITE_A, "CURRENT")] },
    });
    view = renderAt(`/findings?${WINDOW}&cursor=xyz`, fakeClient(() => loaded(pageTwo)));
    await settledScreen();
    expect(main().querySelector("[data-estate-historical]")?.textContent).toBe("This is an earlier evidence cutoff.");
    expect(main().querySelector("[data-estate-limitation]")?.textContent).toContain("This is an earlier evidence cutoff.");
    expect(main().querySelector('[data-estate-site-state="PENDING_RECOMPUTE"]')?.textContent).toBe(
      "New evidence is being assessed.",
    );
    expect(main().textContent).toContain(`Historical as of 2026-10-20 09:30:00 UTC`);
    expect(main().querySelector("[data-estate-cutoff]")?.textContent).toContain("2026-10-20 09:30:00 UTC");
    view.unmount();

    // Complete empty lenses: `No findings match.` plus the lens line; awaiting-verification honest zero.
    const empty = fakeClient((lens) => loaded(findingsBody(lens, { rows: [] })));
    for (const [lens, line] of [
      ["cost", "No supported priced consequence in this selection."],
      ["risks", "No supported risk classification in this selection."],
      ["opportunities", "No supported opportunity Finding in this selection."],
    ] as const) {
      view = renderAt(`${ESTATE_FINDING_LENS_PATHS[lens]}?${WINDOW}`, empty);
      await settledScreen();
      expect(main().querySelector("[data-estate-empty]")?.textContent).toBe(`No findings match.${line}`);
      expect(main().querySelector("tbody")).toBeNull();
      expect(main().textContent).toContain(AWAITING_ZERO);
      expect(main().textContent).toContain(AWAITING_RULE);
      view.unmount();
    }

    // Actions: Not set / No due dates recorded / No success criterion recorded / Verified chip / honest copy.
    const actions = actionsBody({
      rows: [actionRow(), actionRow({ action_id: "10000000-0000-4000-8000-000000000211", application_state: "APPLIED", resolution_state: "RESOLVED", verification_outcome: "VERIFIED" })],
      summary: { open_actions: 1, due_overdue: null, verification_window: 0, verified_in_30_days: 1, basis_count: 2 },
    });
    view = renderAt(`${ESTATE_ACTIONS_PATH}?${WINDOW}`, fakeClient(() => loaded(findingsBody("all")), loaded(actions)));
    await settledScreen();
    expectV69Panels("actions");
    expect(screen.getAllByRole("columnheader").map((h) => h.textContent)).toEqual([
      "Action",
      "Site",
      "Source",
      "Owner",
      "State",
      "Success criterion",
    ]);
    const actionCards = within(screen.getByRole("list", { name: "Actions summary" })).getAllByRole("listitem");
    expect(actionCards.map((c) => [c.querySelector(".v69-metric__label")?.textContent, c.querySelector(".v69-metric__value")?.textContent])).toEqual([
      ["Open actions", "1"],
      ["Due / overdue", "Not set"],
      ["Verification window", "0"],
      ["Verified in 30 days", "1"],
    ]);
    const actionText = main().textContent ?? "";
    for (const words of ["No due dates recorded", "Accepted work", "No success criterion recorded", "Pending", "Applied", "Verified", ACTIONS_LIFECYCLE, ACTIONS_NOTICE]) {
      expect(actionText).toContain(words);
    }
    expect(screen.getAllByText("Not set").length).toBeGreaterThanOrEqual(3);
    expect(screen.getAllByText("Action ACT-000001")[0].getAttribute("href")).toBe(actionRow().links.action);
    expect(screen.getAllByText("Finding 10000000")[0].getAttribute("href")).toBe(actionRow().links.source);
    view.unmount();

    // Refusals through the real client: exact UI copy; a 409/422 cursor refusal offers page one.
    for (const [status, code, copy] of [
      [409, "ESTATE_BASIS_CHANGED", "The list changed. Reload the first page."],
      [422, "INVALID_CURSOR", "Reload the first page."],
      [401, "UNAUTHENTICATED", "Sign in to see estate records."],
      [503, "ESTATE_STORE_UNAVAILABLE", "Estate records are unavailable right now. Try again."],
    ] as const) {
      const fetchMock = vi.fn((_input: RequestInfo | URL) =>
        Promise.resolve(new Response(JSON.stringify({ detail: { code, message: "x", rows: null, total_count: null } }), { status })),
      );
      vi.stubGlobal("fetch", fetchMock);
      view = renderAt(`/findings?${WINDOW}&cursor=old`, createEstateClient());
      await settledScreen();
      const refusal = main().querySelector("[data-page-refusal]") as HTMLElement;
      expect(refusal.getAttribute("data-page-refusal")).toBe(code);
      expect(refusal.textContent).toContain(copy);
      const first = within(refusal).queryByRole("link", { name: "First page" });
      expect(first !== null).toBe(code === "ESTATE_BASIS_CHANGED" || code === "INVALID_CURSOR");
      expect(String(fetchMock.mock.calls[0][0])).toBe(`/api/estate/findings?${WINDOW}&cursor=old`);
      view.unmount();
    }
    // A historical page-one cutoff from the URL is passed through; the default window is seven whole UTC days.
    const seen = fakeClient(() => loaded(findingsBody("all")));
    view = renderAt(`/findings?${WINDOW}&known_at=${encodeURIComponent(KNOWN)}`, seen);
    await settledScreen();
    expect(seen.calls[0]).toMatchObject({ from: FROM, to: TO, known_at: KNOWN, cursor: null, lens: "all" });
    view.unmount();
    const fresh = fakeClient(() => loaded(findingsBody("all")));
    renderAt("/findings", fresh);
    await settledScreen();
    const call = fresh.calls[0] as { from: string; to: string; known_at: string | null };
    expect(call.known_at).toBeNull();
    expect(Date.parse(call.to) - Date.parse(call.from)).toBe(7 * 24 * 60 * 60 * 1000);
    expect(call.to.endsWith("T00:00:00Z")).toBe(true);
  });

  it("test_390_scroll_and_static_missing_destinations", async () => {
    // jsdom has no layout: the 390 rules are asserted on the stylesheet; rectangles are commit 4's captures.
    // Read from disk: vitest serves imported CSS (even `?raw`) as empty text. Node's fs has no types in this
    // DOM-only tsconfig, so it is loaded untyped.
    const fs = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
    const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
    const estateCss = fs.readFileSync(`${cwd}/src/estate/estate.css`, "utf8");
    expect(estateCss).toContain("min-width: 900px");
    expect(estateCss).toContain("min-width: 820px");
    expect(estateCss).toMatch(/td:first-child[^}]*position: sticky/s);
    expect(estateCss).toMatch(/\.estate-state-chips \{[^}]*overflow-x: auto/s);
    const client = fakeClient((lens) => loaded(findingsBody(lens, { rows: [findingRow(1)] })));
    for (const entry of [`/findings?${WINDOW}`, `${ESTATE_ACTIONS_PATH}?${WINDOW}`]) {
      const view = renderAt(entry, client);
      await settledScreen();
      const panel = main().querySelector("section.panel") as HTMLElement;
      const scroll = panel.querySelector(".data-table__scroll") as HTMLElement;
      expect(scroll.contains(panel.querySelector("table"))).toBe(true);
      // Unsupported destinations are inert text: no unavailable chip/tab, no Incident/Maintenance link, and only
      // the exact Site/Finding/Action/lens/state/pager links render.
      expect(main().querySelector(".v69-chip--unavailable, [data-unavailable]")).toBeNull();
      const hrefs = Array.from(main().querySelectorAll("a")).map((a) => a.getAttribute("href") ?? "");
      for (const href of hrefs) {
        expect(href).toMatch(/^\/(findings|actions|sites\/KOBO-001)/);
        expect(href).not.toMatch(/incident|maintenance/i);
      }
      const text = main().textContent ?? "";
      expect(text).not.toMatch(/F-1\d\d|ACT-0[4-6]\d|Not available yet/);
      expect(screen.queryAllByText("Not assessed").every((n) => n.closest("a") === null)).toBe(true);
      view.unmount();
    }
  });
});
