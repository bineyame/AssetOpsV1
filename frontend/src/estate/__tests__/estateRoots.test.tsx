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
import { createEstateClient, invalidWindowCopy, type EstateClient, type EstateLens } from "../estateClient";
import { AWAITING_RULE, AWAITING_ZERO, ESTATE_FINDING_LENS_PATHS, EstateFindingsPage, FINDINGS_LINKED_NOTICE, FINDINGS_NOTICE, FINDINGS_UNLINKED_NOTICE } from "../findingIndex";
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
  scopeBody,
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
      // W3-02 c2b: a root without an eyebrow prop draws no empty eyebrow node.
      expect(screen.getByRole("heading", { level: 1 }).closest("header")?.querySelector(".page-header__eyebrow")).toBeNull();
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
      // Run 13 ruling 2: five stable chips in fixed order, whatever rows are on the page.
      expect(chips.map((c) => c.textContent)).toEqual(["All states", "Supported", "Unconfirmed", "No longer supported", "Merged"]);
      expect(chips.map((c) => c.getAttribute("aria-current"))).toEqual([null, "true", null, null, null]);
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
    // Actions root: panel, exact Action and pinned source links, and a Site link per domain row (L1, L4).
    const coldRow = actionRow({
      action_id: "10000000-0000-4000-8000-000000000221",
      site_code: "COLD 7/a",
      site_name: "Cold Store",
      links: { action: "/sites/COLD%207%2Fa/actions/x?event_id=y", source: null },
    });
    const evRow = actionRow({
      action_id: "10000000-0000-4000-8000-000000000231",
      site_code: "EV-02",
      site_name: "Depot Chargers",
      links: { action: "/sites/EV-02/actions/z?event_id=w", source: null },
    });
    const three = actionsBody({ rows: [actionRow(), coldRow, evRow] });
    renderAt(`${ESTATE_ACTIONS_PATH}?${WINDOW}`, fakeClient(() => loaded(findingsBody("all")), loaded(three)));
    await settledScreen();
    const actionsMain = document.querySelectorAll("main")[1] as HTMLElement;
    expectV69Panels("actions", {}, actionsMain);
    const actionRows = Array.from(actionsMain.querySelectorAll("tbody tr")) as HTMLElement[];
    expect(actionRows).toHaveLength(3);
    const first = actionRows[0];
    expect(within(first).getByText("Action ACT-000001").getAttribute("href")).toBe(actionRow().links.action);
    expect(within(first).getByText("Finding 10000000").getAttribute("href")).toBe(actionRow().links.source);
    for (const [row, name, code] of [
      [actionRows[0], "Kobo Mini-grid", "KOBO-001"],
      [actionRows[1], "Cold Store", "COLD 7/a"],
      [actionRows[2], "Depot Chargers", "EV-02"],
    ] as const) {
      const siteAnchor = within(row).getByText(name);
      expect(siteAnchor.tagName).toBe("A");
      expect(siteAnchor.getAttribute("href")).toBe(`/sites/${encodeURIComponent(code)}`);
      expect(within(row).getByText(code).closest("a")).toBeNull();
    }
    const actionHrefs = Array.from(actionsMain.querySelectorAll("a")).map((a) => a.getAttribute("href") ?? "");
    expect(actionHrefs.some((href) => /incident|maintenance/i.test(href))).toBe(false);
  });

  it("test_cold_ev_titles_inert_and_notice", async () => {
    // Run 13 ruling 3: only a mini-grid row links its Finding; cold/EV titles are inert text with the Site link
    // and disclosure kept, and the notice describes the mixed list.
    const cold = { ...site(SITE_B, "CURRENT"), match_state: "NOT_APPLICABLE" };
    const coldLinks = { finding: "/sites/COLD-1/findings/f?revision_id=r", site: "/sites/COLD-1" };
    const mixed = findingsBody("all", {
      rows: [findingRow(1), findingRow(2, { site_id: SITE_B, site_code: "COLD-1", links: coldLinks })],
      coverage: { state: "COMPLETE", sites: [site(SITE_A, "CURRENT"), cold] },
    });
    let view = renderAt(`/findings?${WINDOW}`, fakeClient(() => loaded(mixed)));
    await settledScreen();
    const rows = Array.from(main().querySelectorAll("tbody tr")) as HTMLElement[];
    expect(within(rows[0]).getByText("Stored finding title 1").tagName).toBe("A");
    const inert = within(rows[1]).getByText("Stored finding title 2");
    expect(inert.tagName).toBe("SPAN");
    expect(inert.closest("a")).toBeNull();
    expect(rows[1].querySelector("[data-estate-finding-link]")).toBeNull();
    expect(within(rows[1]).getByText("COLD-1").getAttribute("href")).toBe("/sites/COLD-1");
    expect(rows[1].querySelector("details")).not.toBeNull();
    expect(main().querySelector("[data-estate-notice]")?.textContent).toBe(`${FINDINGS_NOTICE} ${FINDINGS_LINKED_NOTICE}`);
    view.unmount();
    const onlyCold = findingsBody("all", {
      rows: [findingRow(2, { site_id: SITE_B })],
      coverage: { state: "COMPLETE", sites: [cold] },
    });
    view = renderAt(`/findings?${WINDOW}`, fakeClient(() => loaded(onlyCold)));
    await settledScreen();
    expect(main().querySelector("[data-estate-finding-link]")).toBeNull();
    expect(main().querySelector("[data-estate-notice]")?.textContent).toBe(`${FINDINGS_NOTICE} ${FINDINGS_UNLINKED_NOTICE}`);
    view.unmount();
  });

  it("test_date_bar_cutoff_copy_by_state", async () => {
    // L2: loading and refusal read `latest`; page one adds the suffix; a continuation and an explicit cutoff do not.
    const cutoff = () => main().querySelector("[data-estate-cutoff]")?.textContent;
    const pending = new Promise<never>(() => undefined);
    const loading = { ...fakeClient(() => loaded(findingsBody("all"))), findings: () => pending } as EstateClient;
    let view = renderAt(`/findings?${WINDOW}`, loading);
    expect(cutoff()).toBe("Evidence cutoff latest");
    expect(cutoff()).not.toContain("latest (latest at read time)");
    view.unmount();
    const refused = fakeClient(() => ({ status: "refused", httpStatus: 422, code: "INVALID_LENS", copy: "Choose a supported Findings lens." }));
    view = renderAt(`/findings?${WINDOW}`, refused);
    await settledScreen();
    expect(cutoff()).toBe("Evidence cutoff latest");
    view.unmount();
    view = renderAt(`/findings?${WINDOW}`, fakeClient(() => loaded(findingsBody("all"))));
    await settledScreen();
    expect(cutoff()).toBe("Evidence cutoff 2026-10-20 09:30:00 UTC (latest at read time)");
    view.unmount();
    view = renderAt(`/findings?${WINDOW}&cursor=abc`, fakeClient(() => loaded(findingsBody("all"))));
    await settledScreen();
    expect(cutoff()).toBe("Evidence cutoff 2026-10-20 09:30:00 UTC");
    view.unmount();
    const explicit = "2026-10-18T06:00:00Z";
    view = renderAt(`/findings?${WINDOW}&known_at=${encodeURIComponent(explicit)}`, loading);
    expect(cutoff()).toBe("Evidence cutoff 2026-10-18 06:00:00 UTC");
    view.unmount();
    const explicitBody = actionsBody({ window: { from: FROM, to: TO, bounds: "[from, to)", known_at: explicit } });
    view = renderAt(
      `${ESTATE_ACTIONS_PATH}?${WINDOW}&known_at=${encodeURIComponent(explicit)}`,
      fakeClient(() => loaded(findingsBody("all")), loaded(explicitBody)),
    );
    await settledScreen();
    expect(cutoff()).toBe("Evidence cutoff 2026-10-18 06:00:00 UTC");
    view.unmount();
  });

  it("test_every_state_and_empty_string", async () => {
    // M1: strings previously unasserted, each in its stated state/element.
    const staleBody = findingsBody("all", {
      rows: [
        findingRow(1, { status: "STALE_SOURCE", lifecycle: "SUPPORTED" }),
        findingRow(2, { status: "UNKNOWN", lifecycle: "UNCONFIRMED" }),
        findingRow(3, { status: "HISTORICAL", lifecycle: "NO_LONGER_SUPPORTED" }),
        findingRow(4, { status: "PENDING_RECOMPUTE", lifecycle: "MERGED" }),
        findingRow(5, { status: "CURRENT" }),
        findingRow(6, { status: "NOT_APPLICABLE" }),
      ],
      coverage: { state: "COMPLETE", sites: [site(SITE_A, "STALE_SOURCE")] },
    });
    let view = renderAt(`/findings?${WINDOW}`, fakeClient(() => loaded(staleBody)));
    await settledScreen();
    const rows = Array.from(main().querySelectorAll("tbody tr")) as HTMLElement[];
    const chip = (row: HTMLElement) => row.querySelector("[data-estate-site-state]")?.textContent;
    expect(chip(rows[0])).toBe("This result may miss newer readings.");
    expect(chip(rows[1])).toBe("Not yet assessed");
    expect(chip(rows[2])).toBe("Earlier evidence cutoff");
    expect(chip(rows[3])).toBe("New evidence is being assessed.");
    expect(rows[4].querySelector("[data-estate-site-state]")).toBeNull();
    expect(rows[5].querySelector("[data-estate-site-state]")).toBeNull();
    const lifecycle = (row: HTMLElement) => row.querySelector("[data-estate-lifecycle]");
    expect(rows.slice(0, 4).map((r) => lifecycle(r)?.getAttribute("data-estate-lifecycle"))).toEqual([
      "SUPPORTED",
      "UNCONFIRMED",
      "NO_LONGER_SUPPORTED",
      "MERGED",
    ]);
    expect(rows.slice(0, 4).map((r) => lifecycle(r)?.textContent)).toEqual([
      "Supported",
      "Unconfirmed",
      "No longer supported",
      "Merged",
    ]);
    expect(main().querySelector("[data-estate-limitation]")?.textContent).toContain(
      "Some sites' results may miss newer readings.",
    );
    view.unmount();

    // An empty filtered read keeps the five chips and the empty state.
    view = renderAt(`/findings?${WINDOW}&state=merged`, fakeClient(() => loaded(findingsBody("all", { rows: [] }))));
    await settledScreen();
    const stable = within(screen.getByRole("list", { name: "Workflow state" })).getAllByRole("link");
    expect(stable.map((c) => c.textContent)).toEqual(["All states", "Supported", "Unconfirmed", "No longer supported", "Merged"]);
    expect(main().querySelector("[data-estate-empty]")?.textContent).toContain("No findings match.");
    view.unmount();

    // Actions: complete empty, no pinned source, NONE_AT_CUTOFF chip, state-scoped chips.
    const actionsRead = (body: ReturnType<typeof actionsBody>) => fakeClient(() => loaded(findingsBody("all")), loaded(body));
    view = renderAt(`${ESTATE_ACTIONS_PATH}?${WINDOW}`, actionsRead(actionsBody({ rows: [] })));
    await settledScreen();
    expect(main().querySelector("[data-estate-empty]")?.textContent).toBe("No actions match.");
    view.unmount();
    const none = actionRow({ application_state: "NONE_AT_CUTOFF", links: { ...actionRow().links, source: null } });
    view = renderAt(`${ESTATE_ACTIONS_PATH}?${WINDOW}`, actionsRead(actionsBody({ rows: [none] })));
    await settledScreen();
    expect(main().querySelector("[data-estate-application]")?.textContent).toBe("No action yet");
    const sourceCell = main().querySelectorAll("tbody tr td")[2];
    expect(sourceCell.textContent).toBe("Source unavailable");
    expect(sourceCell.querySelector("a")).toBeNull();
    view.unmount();
    const verifiedRow = actionRow({
      action_id: "10000000-0000-4000-8000-000000000241",
      application_state: "APPLIED",
      resolution_state: "RESOLVED",
      verification_outcome: "VERIFIED",
    });
    view = renderAt(`${ESTATE_ACTIONS_PATH}?${WINDOW}`, actionsRead(actionsBody({ rows: [actionRow(), verifiedRow] })));
    await settledScreen();
    const stateCells = Array.from(main().querySelectorAll("tbody tr")).map((r) => r.querySelectorAll("td")[4]);
    const chipsIn = (cell: Element) => Array.from(cell.querySelectorAll(".estate-chip")).map((c) => c.textContent);
    expect(chipsIn(stateCells[0])).toEqual(["Pending"]);
    expect(chipsIn(stateCells[1])).toEqual(["Applied", "Verified"]);
    view.unmount();

    // Partial Actions cards, and the complete zero-outcome note (Run 13 ruling 7).
    const partialActions = actionsBody({
      rows: [],
      status: "UNKNOWN",
      coverage: { state: "PARTIAL", sites: [site(SITE_A, "UNKNOWN")] },
      total_count: null,
      summary: { open_actions: null, due_overdue: null, verification_window: null, verified_in_30_days: null, basis_count: null },
    });
    view = renderAt(`${ESTATE_ACTIONS_PATH}?${WINDOW}`, actionsRead(partialActions));
    await settledScreen();
    const card = (label: string) =>
      Array.from(main().querySelectorAll(".v69-metric")).find(
        (c) => c.querySelector(".v69-metric__label")?.textContent === label,
      ) as HTMLElement;
    for (const label of ["Open actions", "Due / overdue", "Verification window", "Verified in 30 days"]) {
      expect(card(label).querySelector(".v69-metric__value")?.textContent).toBe("Coverage incomplete");
    }
    expect(main().textContent).not.toContain("No verified outcome in the last 30 days");
    view.unmount();
    view = renderAt(`${ESTATE_ACTIONS_PATH}?${WINDOW}`, actionsRead(actionsBody()));
    await settledScreen();
    expect(card("Verified in 30 days").textContent).toContain("No verified outcome in the last 30 days");
    expect(card("Due / overdue").querySelector(".v69-metric__value")?.textContent).toBe("Not set");
    expect(main().textContent).not.toContain("No closed verification yet");
    view.unmount();
    // The note does not depend on the rows on this page: a RESOLVED, unverified row still shows it.
    const refuted = actionsBody({ rows: [actionRow({ resolution_state: "RESOLVED", verification_outcome: "REFUTED" })] });
    view = renderAt(`${ESTATE_ACTIONS_PATH}?${WINDOW}`, actionsRead(refuted));
    await settledScreen();
    expect(card("Verified in 30 days").textContent).toContain("No verified outcome in the last 30 days");
    view.unmount();

    // Refusal copy by code: exact message, and no First page link for these five.
    for (const [status, code, copy] of [
      [409, "ESTATE_SELECTION_INCONSISTENT", "Some records are being updated. Reload the list."],
      [422, "INVALID_WINDOW", "The selected window is invalid."],
      [422, "INVALID_KNOWN_AT", "Choose a valid evidence cutoff."],
      [422, "INVALID_LENS", "Choose a supported Findings lens."],
      [422, "INVALID_LIMIT", "Choose a page size from 1 to 100."],
    ] as const) {
      const body = JSON.stringify({ detail: { code, message: "x", rows: null, total_count: null } });
      vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(body, { status }))));
      view = renderAt(`/findings?${WINDOW}`, createEstateClient());
      await settledScreen();
      const refusal = main().querySelector("[data-page-refusal]") as HTMLElement;
      expect(refusal.getAttribute("data-page-refusal")).toBe(code);
      expect(refusal.querySelector("p")?.textContent).toBe(copy);
      expect(within(refusal).queryByRole("link", { name: "First page" })).toBeNull();
      expect(refusal.querySelector("[data-refusal-title]")?.textContent ?? null).toBe(code === "INVALID_WINDOW" ? "Window cannot be read" : null);
      view.unmount();
    }
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
    // Post-W6 W3-estate Q8: no line clamp on any estate primary cell, wrapping allowed, a 152px sticky first
    // column at 640px and below, and the horizontal scroller kept.
    const estateCssFiles = ["estate.css", "estateEvidence.css", "estateFinancials.css", "estatePortfolio.css"].map((f) =>
      fs.readFileSync(`${cwd}/src/estate/${f}`, "utf8"),
    );
    for (const css of estateCssFiles) expect(css).not.toMatch(/line-clamp/);
    expect(estateCss).toMatch(/\.estate-cell__primary \{[^}]*overflow-wrap: anywhere/s);
    expect(estateCss).toMatch(/\.estate-page \.data-table__scroll \{[^}]*overflow-x: auto/s);
    const narrow = estateCss.slice(estateCss.indexOf("@media (max-width: 640px)"));
    expect(narrow).toMatch(/td:first-child \{[^}]*width: 152px;[^}]*max-width: 152px/s);
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

describe("post-W6 W3-estate Findings and Actions roots", () => {
  const SITE_C = "10000000-0000-4000-8000-000000000013";
  const coldLink = (n: number) =>
    `/sites/COLD-7/findings/f${n}?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(KNOWN)}`;
  const long = (label: string) => `${label} `.padEnd(160, "w").slice(0, 160);

  it("coldAndEvTitlesAreLiveOnlyWithAProvableWindowedLinkOnEveryLens", async () => {
    // Q4: SITE_B (cold) and SITE_C (EV) report match_state NOT_APPLICABLE; the cold row carries its own from/to/known_at,
    // the EV row only the legacy revision link the server sends when the window is not provable.
    const rows = [
      findingRow(1),
      findingRow(2, { site_id: SITE_B, site_code: "COLD-7", site_name: "Cold Store", links: { finding: coldLink(2), site: "/sites/COLD-7" } }),
      findingRow(3, {
        site_id: SITE_C,
        site_code: "EV-02",
        site_name: "Depot Chargers",
        links: { finding: "/sites/EV-02/findings/f3?revision_id=r3", site: "/sites/EV-02/ev" },
      }),
    ];
    const coverage = {
      state: "COMPLETE" as const,
      sites: [site(SITE_A, "CURRENT"), { ...site(SITE_B, "CURRENT"), match_state: "NOT_APPLICABLE" }, { ...site(SITE_C, "CURRENT"), match_state: "NOT_APPLICABLE" }],
    };
    const client = fakeClient((lens) => loaded(findingsBody(lens, { rows, coverage })));
    for (const lens of LENSES) {
      const view = renderAt(`${ESTATE_FINDING_LENS_PATHS[lens]}?${WINDOW}`, client);
      await settledScreen();
      const trs = Array.from(main().querySelectorAll("tbody tr")) as HTMLElement[];
      expect(trs).toHaveLength(3);
      expect(trs[0].querySelector("[data-estate-finding-link]")?.getAttribute("href")).toBe(rows[0].links.finding);
      expect(trs[1].querySelector("[data-estate-finding-link]")?.getAttribute("href")).toBe(coldLink(2));
      expect(trs[1].querySelector("[data-estate-finding-unavailable]")).toBeNull();
      // The unprovable EV link is never followed (it would 404): inert title with the labelled unavailable detail.
      expect(trs[2].querySelector("[data-estate-finding-link]")).toBeNull();
      expect(trs[2].querySelector("[data-estate-finding-inert]")?.textContent).toBe("Stored finding title 3");
      expect(trs[2].querySelector("[data-estate-finding-unavailable]")?.textContent).toBe("Finding detail unavailable");
      expect(main().querySelector("a[href*='revision_id=r3']")).toBeNull();
      expect(trs[2].querySelector("[data-estate-site-link]")?.getAttribute("href")).toBe("/sites/EV-02/ev");
      expect(main().querySelector("[data-estate-notice]")?.textContent).toContain(FINDINGS_LINKED_NOTICE);
      view.unmount();
    }
  });

  it("partialCopyNamesTheSiteByCauseAndFallsBackWhenScopeFails", async () => {
    // Q7: the identical window and cutoff are sent to scope; names join on site_id.
    const pendingSel = { ...site(SITE_A, "PENDING_RECOMPUTE"), selection_id: "sel-a" };
    const pendingSelB = { ...site(SITE_B, "PENDING_RECOMPUTE"), selection_id: "sel-b" };
    const unassessed = site(SITE_B, "UNKNOWN");
    const selected = (id: string) => ({ ...site(id, "CURRENT"), selection_id: `sel-${id}` });
    const scope = scopeBody([
      [SITE_A, "Kobo Mini-grid"],
      [SITE_B, "Cold Store"],
    ]);
    const partial = (sites: ReturnType<typeof site>[]) =>
      findingsBody("all", { coverage: { state: "PARTIAL", sites }, total_count: null, summary: { ...findingsBody("all").summary, supported_findings: null, awaiting_verification: null } });
    const cases: [ReturnType<typeof site>[], string[], string[]][] = [
      [
        [pendingSel, selected(SITE_B)],
        ["Totals are unknown while new evidence for Kobo Mini-grid is assessed; its rows are held until then."],
        ["New evidence for Kobo Mini-grid is being assessed."],
      ],
      [
        [selected(SITE_A), unassessed],
        ["Cold Store has no selected result; totals are unknown."],
        ["Cold Store is not yet assessed; estate totals are unknown."],
      ],
      [
        [pendingSel, pendingSelB],
        ["Totals are unknown while new evidence for Kobo Mini-grid, Cold Store is assessed; their rows are held until then."],
        ["New evidence for Kobo Mini-grid, Cold Store is being assessed."],
      ],
    ];
    for (const lens of LENSES) {
      for (const [sites, panelLines, noticeLines] of cases) {
        const client = fakeClient(() => loaded({ ...partial(sites), lens }), undefined, loaded(scope));
        const view = renderAt(`${ESTATE_FINDING_LENS_PATHS[lens]}?${WINDOW}&known_at=${encodeURIComponent(KNOWN)}`, client);
        await settledScreen();
        expect(client.calls.find((c) => (c as { kind: string }).kind === "scope")).toEqual({ kind: "scope", from: FROM, to: TO, known_at: KNOWN });
        expect(Array.from(main().querySelectorAll("[data-estate-partial]")).map((p) => p.textContent)).toEqual(panelLines);
        expect(Array.from(main().querySelectorAll(".estate-limitation__line")).map((l) => l.textContent?.trim())).toEqual(noticeLines);
        expect(main().textContent).not.toContain("Some sites");
        view.unmount();
      }
    }
    // A failed scope read keeps the generic sentences.
    const failed = fakeClient(() => loaded(partial([pendingSel, unassessed])));
    const view = renderAt(`/findings?${WINDOW}`, failed);
    await settledScreen();
    expect(Array.from(main().querySelectorAll("[data-estate-partial]")).map((p) => p.textContent)).toEqual([
      "Some sites have no selected result; totals are unknown.",
    ]);
    expect(main().textContent).toContain("New evidence is being assessed.");
    expect(main().textContent).toContain("Some sites are not yet assessed; estate totals are unknown.");
    view.unmount();
    // Actions wording is unchanged by the Finding-lens variant.
    const actions = fakeClient(() => loaded(findingsBody("all")), loaded(actionsBody({ coverage: { state: "PARTIAL", sites: [pendingSel, unassessed] }, total_count: null })), loaded(scope));
    const actionsView = renderAt(`${ESTATE_ACTIONS_PATH}?${WINDOW}`, actions);
    await settledScreen();
    expect(main().textContent).toContain("New evidence is being assessed.");
    expect(main().textContent).not.toContain("Kobo Mini-grid is being assessed");
    actionsView.unmount();
  });

  it("refusedWindowOnFindingsAndActionsUsesTheSharedSentences", async () => {
    // Q14: classified from the page query; the window line says `Window not valid` without echoing the dates.
    const cases: [string, string][] = [
      ["from=2026-10-07T00:00:00Z&to=2026-10-05T00:00:00Z", "The selected window needs both a start and an end, with the start before the end."],
      ["from=2026-08-01T00:00:00Z&to=2026-10-01T00:00:00Z", "The selected window is longer than 31 days."],
      [WINDOW, "The selected window is invalid."],
    ];
    const refusedRead = { status: "refused" as const, httpStatus: 422, code: "INVALID_WINDOW", copy: "server copy" };
    for (const path of ["/findings", ESTATE_ACTIONS_PATH]) {
      for (const [query, copy] of cases) {
        const view = renderAt(`${path}?${query}`, fakeClient(() => refusedRead, refusedRead));
        await settledScreen();
        expect(main().querySelector("[data-page-refusal='INVALID_WINDOW'] p")?.textContent).toBe(copy);
        expect(main().querySelector("[data-estate-window]")?.textContent).toBe("Window not valid");
        view.unmount();
      }
    }
    // The real client classifies the same way from the query it sent.
    const body = JSON.stringify({ detail: { code: "INVALID_WINDOW", message: "x" } });
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(body, { status: 422 }))));
    const read = await createEstateClient().findings({ from: "2026-10-07T00:00:00Z", to: "2026-10-05T00:00:00Z", known_at: null, cursor: null, lens: "all", state: "all" });
    expect(read).toEqual({ status: "refused", httpStatus: 422, code: "INVALID_WINDOW", copy: "The selected window needs both a start and an end, with the start before the end." });
    expect(invalidWindowCopy({ from: "2026-10-01T00:00:00Z", to: null })).toBe("The selected window needs both a start and an end, with the start before the end.");
    expect(invalidWindowCopy({ from: "2026-10-01T00:00:00Z", to: "2026-11-01T00:00:00Z" })).toBe("The selected window is invalid.");
    expect(invalidWindowCopy({ from: "2026-10-01T00:00:00Z", to: "2026-11-01T00:00:01Z" })).toBe("The selected window is longer than 31 days.");
    // A non-window refusal keeps its copy and the requested window line (UTC header, Q22).
    const store = { status: "refused" as const, httpStatus: 503, code: "ESTATE_STORE_UNAVAILABLE", copy: "Estate records are unavailable right now. Try again." };
    const view = renderAt(`/findings?${WINDOW}`, fakeClient(() => store));
    await settledScreen();
    expect(main().querySelector("[data-page-refusal] p")?.textContent).toBe(store.copy);
    expect(main().querySelector("[data-estate-window]")?.textContent).toBe("Window 2026-10-13 to 2026-10-19 (UTC days)");
    view.unmount();
  });

  it("actionTitleIsTheSelectedTitleOrTheCodeAlone", async () => {
    // Q5: no Action-kind wording; Q6: the criterion stays `No success criterion recorded`.
    const titled = actionRow({ action_title: "Review generator stop setting" });
    const untitled = actionRow({ action_id: "10000000-0000-4000-8000-000000000299", action_title: null as unknown as string });
    const view = renderAt(`${ESTATE_ACTIONS_PATH}?${WINDOW}`, fakeClient(() => loaded(findingsBody("all")), loaded(actionsBody({ rows: [titled, untitled] }))));
    await settledScreen();
    const links = Array.from(main().querySelectorAll("[data-estate-action-link]")).map((a) => a.textContent);
    expect(links).toEqual(["Review generator stop setting", "ACT-000001"]);
    expect(main().textContent).not.toContain("Battery reserve trial");
    expect(main().textContent).toContain("No success criterion recorded");
    view.unmount();
  });

  it("fiveLongRowsRenderInFullOnFindingsAndActions", async () => {
    // Q20: pure selected-DTO render of five 160-character rows; nothing is truncated in the DOM.
    const findings = Array.from({ length: 5 }, (_, i) => findingRow(i + 1, { title: long(`Finding ${i + 1}`) }));
    const actions = Array.from({ length: 5 }, (_, i) =>
      actionRow({ action_id: `10000000-0000-4000-8000-00000000030${i}`, action_title: long(`Action ${i + 1}`) }),
    );
    for (const t of [...findings.map((f) => f.title), ...actions.map((a) => a.action_title)]) expect(t).toHaveLength(160);
    const client = fakeClient((lens) => loaded(findingsBody(lens, { rows: findings })), loaded(actionsBody({ rows: actions })));
    let view = renderAt(`/findings?${WINDOW}`, client);
    await settledScreen();
    expect(Array.from(main().querySelectorAll("tbody tr .estate-cell__primary[data-estate-finding-link]")).map((a) => a.textContent)).toEqual(
      findings.map((f) => f.title),
    );
    view.unmount();
    view = renderAt(`${ESTATE_ACTIONS_PATH}?${WINDOW}`, client);
    await settledScreen();
    expect(Array.from(main().querySelectorAll("[data-estate-action-link]")).map((a) => a.textContent)).toEqual(actions.map((a) => a.action_title));
    view.unmount();
  });

  it("M1: the Findings index table renders a colgroup whose first column is the 152px Finding column at narrow width", async () => {
    const fs = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
    const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
    const css = fs.readFileSync(`${cwd}/src/estate/estate.css`, "utf8");
    const narrow = css.slice(css.indexOf("@media (max-width: 640px)"));
    const client = fakeClient((lens) => loaded(findingsBody(lens, { rows: [findingRow(1)] })));
    for (const entry of [`/findings?${WINDOW}`, `/findings/cost?${WINDOW}`]) {
      const view = renderAt(entry, client);
      await settledScreen();
      const table = main().querySelector("table.data-table") as HTMLElement;
      const cols = Array.from(table.querySelectorAll("colgroup > col.estate-findings-col"));
      // Rendered structure: one col per header, so the pixel rules below address real columns.
      expect(cols).toHaveLength(table.querySelectorAll("thead th").length);
      expect(cols).toHaveLength(7);
      // The narrow rules give every column a pixel width; the first is 152px and the table is a fixed 672px.
      expect(narrow).toMatch(/col\.estate-findings-col:nth-child\(1\) \{ width: 152px !important; \}/);
      expect(narrow).toMatch(/:has\(col\.estate-findings-col\) \{[^}]*table-layout: fixed;[^}]*width: 672px/s);
      const px = Array.from(narrow.matchAll(/col\.estate-findings-col:nth-child\((\d)\) \{ width: (\d+)px/g)).map((m) => Number(m[2]));
      expect(px).toHaveLength(7);
      expect(px.reduce((a, b) => a + b, 0)).toBe(672);
      view.unmount();
    }
  });
});
