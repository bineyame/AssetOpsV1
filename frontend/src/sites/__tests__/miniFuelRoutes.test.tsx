import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { FuelRead, FuelRow, MiniDepthClient, MiniRead } from "../miniDepthClient";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { expectPlantedPanelRejected, expectV69Panels, panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";

/*
 * W4-02 unit 6: a MINIGRID Site's Performance/Fuel route renders the v69 `fuel` panels from the q9 public read
 * (build spec q3-3 state table, "Run 9 rulings (q9) and pages dry-read" fuel row, copy ledger, Q20): no SUPPORTED
 * fuel status, `Delivery completeness unconfirmed` and `Cannot compute` instead of `0 L`, expected use always
 * labelled Modelled, and the dispatch consequence stays unlinked while `links.financials` is null.
 */

afterEach(cleanup);

const CODE = "MG-W402-001";
const TZ = "Africa/Addis_Ababa";
const id = (n: number) => `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const SELECTED = { classification: "REGISTERED_SIMULATION", source_ids: [id(2)], evidence_ids: [id(100)] };
const FULL = { required_seconds: 3600, observed_seconds: 3600, source_count: 1, gaps: [] };
const ZERO = { required_seconds: 3600, observed_seconds: 0, source_count: 0, gaps: [{ from: "2026-10-06T09:00:00Z", to: "2026-10-06T10:00:00Z" }] };

function term(term: string, over: Partial<FuelRow> = {}): FuelRow {
  return { term, basis: "MISSING", treatment: "MISSING", value: null, coverage: ZERO, evidence_ids: [], ...over };
}

const USE_BOUND = { low: 0, high: 3.3 };

function rows(): FuelRow[] {
  return [
    term("OPENING", { basis: "ACCEPTED_READING", coverage: { ...ZERO, source_count: 1 }, evidence_ids: [id(300)] }),
    term("DELIVERIES", { basis: "AUTHORED_EVIDENCE_UNAVAILABLE", treatment: "COMPLETENESS_UNCONFIRMED" }),
    term("USE", { basis: "FOUNDATION_MODEL", treatment: "MODELLED", value: USE_BOUND, coverage: FULL, evidence_ids: [id(301)] }),
    term("CLOSING"),
    term("RESIDUAL"),
  ];
}

function read(over: Partial<FuelRead> = {}): FuelRead {
  return {
    schema_version: "w4-02.mini.v1",
    domain: "fuel",
    site: { id: id(1), code: CODE, timezone: TZ },
    window: { from: "2026-10-06T09:00:00Z", to: "2026-10-06T10:00:00Z", known_at: "2026-10-07T00:00:00Z", bounds: "[from,to)" },
    currentness: {
      state: "CURRENT",
      job_state: "SETTLED",
      windows: [
        {
          local_day: "2026-10-06",
          window_start: "2026-10-06T09:00:00Z",
          window_end: "2026-10-06T10:00:00Z",
          selection_id: 1,
          assessment_revision_id: id(501),
          input_sha256: "a".repeat(64),
          committed_watermark: null,
          state: "CURRENT",
          job_state: "SETTLED",
        },
      ],
    },
    source_provenance: SELECTED,
    selected_source_provenance: SELECTED,
    pending_source_provenance: null,
    status: "UNKNOWN",
    coverage: FULL,
    cards: { opening_l: null, deliveries_l: null, expected_use_l: USE_BOUND, closing_l: null, residual_l: null },
    rows: rows(),
    limitations: [
      { code: "DELIVERY_COMPLETENESS_MISSING", evidence_ids: [] },
      { code: "CLOSING_READING_MISSING", evidence_ids: [] },
    ],
    basis: {
      specific_fuel_consumption_property_revision_id: id(700),
      specific_fuel_consumption_property_revision_ids: [id(700)],
      generator_power_evidence_ids: [id(301)],
    },
    links: { dispatch: null, evidence: `/sites/${CODE}/evidence`, financials: null, actions: "/actions" },
    ...over,
  } as FuelRead;
}

const SITE = {
  site_id: CODE,
  display_name: "W4-02 mini-grid",
  site_type: "MINIGRID",
  location: { country: "Ethiopia", locality: "Addis Ababa" },
  timezone: TZ,
  lifecycle_status: "PLANNED",
  origin: "USER",
  source: { mode: "SIMULATED" },
  template: null,
  configuration_store: "POSTGRES",
} as unknown as SiteDetailReadModel;
const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: SITE }) };
const directory: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [SITE] }) };

const CAPS = [
  { id: "service", display_name: "Service" },
  { id: "fuel", display_name: "Fuel" },
  { id: "renewable", display_name: "Renewable" },
  { id: "backup", display_name: "Backup" },
];

function renderFuel(answers: MiniRead<FuelRead>[], path = `/sites/${CODE}/performance/fuel?date=2026-10-06`) {
  const queue = [...answers];
  const client: MiniDepthClient = {
    getCapabilities: vi.fn(() => Promise.resolve({ status: "loaded" as const, value: CAPS })),
    getRenewable: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
    getService: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
    getFuel: vi.fn(() => Promise.resolve(queue.length > 1 ? queue.shift()! : queue[0])),
    getBackup: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
  };
  render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} miniDepth={client} />
    </MemoryRouter>,
  );
  return client;
}

const ok = (value: FuelRead): MiniRead<FuelRead> => ({ status: "loaded", value });
const main = () => document.querySelector("main") as HTMLElement;
const strip = () => (document.querySelector(".status-strip") as HTMLElement).textContent ?? "";
const cardValues = () => Array.from(document.querySelectorAll("[data-mini-cards] .v69-metric__value")).map((x) => x.textContent);
const subtabs = () =>
  Array.from(document.querySelectorAll('nav[aria-label="Performance sections"] li')).map((li) => [
    li.textContent,
    li.querySelector("a")?.getAttribute("aria-current") ?? null,
  ]);
const bodyRows = () =>
  Array.from(document.querySelectorAll("tbody tr")).map((tr) => Array.from(tr.querySelectorAll("td")).map((td) => td.textContent));

describe("W4-02 unit 6: fuel keeps the v69 panels, strip, cards, bars, bridge, notice and interpretation", () => {
  it("modelled use without a balance: Fuel balance Unknown, modelled cards, five fixed bridge rows, tab order", async () => {
    const client = renderFuel([ok(read())]);
    await settledScreen();
    await screen.findByText("Fuel balance: Unknown");
    expectV69Panels("fuel");
    expectPlantedPanelRejected("fuel");
    expect(subtabs()).toEqual([
      ["Service", null],
      ["Dispatch", null],
      ["Fuel", "page"],
      ["Renewable", null],
      ["Backup", null],
    ]);
    expect(client.getFuel).toHaveBeenCalledWith(CODE, {
      from: "2026-10-06T09:00:00.000Z",
      to: "2026-10-06T10:00:00.000Z",
      known_at: null,
    });
    expect(main().textContent).toContain("Review the generator-use model and incomplete inventory balance.");
    expect(strip()).toContain("A complete inventory balance needs deliveries and closing evidence.");
    expect(strip()).toContain("Selected sources: Generated test data, not field readings");
    // q12-7: the ordered limitations sit behind the closed strip disclosure (count line visible).
    expect(document.querySelector("[data-mini-limitations]")).not.toHaveAttribute("open");
    expect(document.querySelector("[data-mini-limitations] summary")?.textContent).toMatch(/^(Limited by \d+ conditions?|Outage-chain assessment: evidence limited)$/);
    expect(Array.from(document.querySelectorAll("[data-mini-limitations] li"), (li) => li.textContent).join("; ")).toContain("Delivery completeness unconfirmed; No accepted closing tank reading");
    expect(cardValues()).toEqual(["Unknown", "Delivery completeness unconfirmed", "0–3.3 L", "Cannot compute"]);
    const cards = document.querySelector("[data-mini-cards]")?.textContent ?? "";
    expect(cards).toContain("Modelled expected use");
    expect(cards).toContain("Modelled: generator output for 60 min × selected fuel coefficient with selected bound");
    const glance = panelTitled("Fuel balance at a glance");
    expect(glance.textContent).toContain("Opening + deliveries − use − closing");
    expect(glance.querySelector('[data-value-bar-key="deliveries"]')?.getAttribute("data-value-bar")).toBe("not-known");
    expect(glance.querySelector('[data-value-bar-key="residual"]')?.getAttribute("data-value-bar")).toBe("not-known");
    expect(glance.querySelectorAll("[data-value-bar-key]").length).toBe(5);
    // Final review L1: missing terms say `Unknown`; L4: the lone numeric term is an unscaled range marker.
    expect(glance.querySelector('[data-value-bar-key="residual"] .value-bars__value')?.textContent).toBe("Unknown");
    expect(glance.textContent).not.toContain("not known");
    const use = glance.querySelector('[data-value-bar-key="use"]') as HTMLElement;
    expect(use.querySelector('[data-value-bar-mark="range-marker"]')).not.toBeNull();
    expect(use.querySelector(".value-bars__fill")).toBeNull();
    expect(use.querySelector(".value-bars__value")?.textContent).toBe("0–3.3 L");
    expect(bodyRows()).toEqual([
      ["Opening inventory · Unknown", "Accepted tank reading · 1 cited record · Evidence", "No bounded tank uncertainty is registered"],
      ["Plus deliveries · Delivery completeness unconfirmed", "No attested delivery record · 0 cited records", "Delivery completeness unconfirmed"],
      ["Less generator consumption · 0–3.3 L", "Generator output × selected fuel coefficient · 1 cited record · Evidence", "Modelled range, not a fuel-meter reading"],
      ["Less closing inventory · Unknown", "Missing · 0 cited records", "Missing"],
      ["Unexplained residual · Cannot compute", "Missing · 0 cited records", "Needs every term with a supported range; never infers theft"],
    ]);
    expect(document.querySelector('[data-mini-notice="fuel"]')?.textContent).toBe(
      "A fuel residual is unexplained inventory movement with uncertainty. It cannot establish theft or be added to dispatch fuel exposure.",
    );
    const interp = panelTitled("Inspect existing generator fuel interpretation");
    expect(interp.textContent).toContain("Dispatch may have a separate modelled fuel quantity for a selected Finding.");
    expect(interp.querySelector('[data-link-unavailable="dispatch-consequence"]')?.textContent).toBe("No linked dispatch consequence");
    expect(interp.querySelector("a")).toBeNull();
    expect(main().textContent).not.toMatch(/200 L|4\.9|0 L\b|theft detected/i);
  });

  it("final review L2: an accepted closing reading that cannot bound says No bounded closing tank reading", async () => {
    const accepted = rows().map((r) =>
      r.term === "CLOSING" ? term("CLOSING", { basis: "ACCEPTED_READING", coverage: { ...ZERO, source_count: 1 }, evidence_ids: [id(302)] }) : r,
    );
    renderFuel([ok(read({ rows: accepted, limitations: [{ code: "DELIVERY_COMPLETENESS_MISSING", evidence_ids: [] }, { code: "CLOSING_READING_MISSING", evidence_ids: [id(302)] }] }))]);
    await settledScreen();
    await screen.findByText("Fuel balance: Unknown");
    const limits = Array.from(document.querySelectorAll("[data-mini-limitations] li"), (li) => li.textContent).join("; ");
    expect(limits).toContain("No bounded closing tank reading");
    expect(limits).not.toContain("No accepted closing tank reading");
    expect(limits).not.toContain("Closing tank reading missing");
    // The bridge keeps citing the accepted closing record, and the residual stays null.
    const closing = bodyRows().find((r) => r[0].startsWith("Less closing inventory")) ?? [];
    expect(closing[1]).toContain("Accepted tank reading · 1 cited record");
    expect(cardValues()[3]).toBe("Cannot compute");
  });

  it("the fuel basis drawer cites the selected SFC revisions and generator power records as Modelled", async () => {
    const two = { specific_fuel_consumption_property_revision_id: null, specific_fuel_consumption_property_revision_ids: [id(700), id(701)], generator_power_evidence_ids: [id(301)] };
    renderFuel([ok(read({ basis: two }))]);
    await settledScreen();
    await screen.findByText("Fuel balance: Unknown");
    fireEvent.click(screen.getByRole("button", { name: "Inspect fuel basis" }));
    const drawer = document.querySelector('[data-mini-drawer="fuel"]') as HTMLElement;
    expect(drawer.textContent).toContain("Treatment: Modelled · 0–3.3 L");
    expect(drawer.textContent).toContain(`Fuel coefficient revisions: ${id(700)}, ${id(701)}`);
    expect(drawer.textContent).toContain(`Generator power records: ${id(301)}`);
    expect(drawer.textContent).toContain(`Opening inventory: ${id(300)}`);
    expectV69Panels("fuel");
  });

  it("q3-3 limited row: Fuel balance evidence limited, conflict treatment, Residual Cannot compute", async () => {
    const conflict = rows();
    conflict[2] = term("USE", { basis: "FOUNDATION_MODEL", treatment: "CONFLICT", evidence_ids: [id(301), id(302)] });
    renderFuel([
      ok(read({
        status: "LIMITED",
        rows: conflict,
        cards: { opening_l: null, deliveries_l: null, expected_use_l: null, closing_l: null, residual_l: null },
        limitations: [{ code: "CONFLICT", evidence_ids: [id(301), id(302)] }],
      })),
    ]);
    await settledScreen();
    await screen.findByText("Fuel balance: evidence limited");
    expectV69Panels("fuel");
    // q12-7: the ordered limitations sit behind the closed strip disclosure (count line visible).
    expect(document.querySelector("[data-mini-limitations]")).not.toHaveAttribute("open");
    expect(document.querySelector("[data-mini-limitations] summary")?.textContent).toMatch(/^(Limited by \d+ conditions?|Outage-chain assessment: evidence limited)$/);
    expect(Array.from(document.querySelectorAll("[data-mini-limitations] li"), (li) => li.textContent).join("; ")).toContain("Conflicting evidence");
    expect(cardValues()).toEqual(["Unknown", "Delivery completeness unconfirmed", "Unknown", "Cannot compute"]);
    expect(bodyRows()[2]).toEqual(["Less generator consumption · Unknown", "Generator output × selected fuel coefficient · 2 cited records · Evidence", "Conflicting records"]);
  });

  it("no selected revision keeps the page shell: Unknown cards and the empty bridge copy", async () => {
    renderFuel([
      ok(read({
        currentness: { state: "UNKNOWN", job_state: "NONE", windows: [] },
        selected_source_provenance: null,
        source_provenance: null,
        coverage: null,
        cards: null,
        rows: [],
        limitations: [],
        basis: null,
      })),
    ]);
    await settledScreen();
    await screen.findByText("Fuel balance: Unknown");
    expectV69Panels("fuel");
    expect(cardValues()).toEqual(["Unknown", "Delivery completeness unconfirmed", "Unknown", "Cannot compute"]);
    expect(panelTitled("Balance bridge").textContent).toContain("No fuel hour has been assessed for this period.");
    expect(strip()).toContain("No selected assessment");
  });

  it("q11-2: a SUPPORTED read says Supported, a bounded tank reading is named, and no USE minutes means no modelled note", async () => {
    const bounded = rows().map((r) =>
      r.term === "OPENING" ? { ...r, value: { low: 400, high: 410 } } : r.term === "USE" ? { ...r, coverage: null } : r,
    );
    renderFuel([ok(read({ status: "SUPPORTED", rows: bounded }))]);
    await settledScreen();
    await screen.findByText("Fuel balance: Supported");
    expect(panelTitled("Balance bridge").textContent).toContain("Accepted tank reading with bounded uncertainty");
    const cards = document.querySelector("[data-mini-cards]")?.textContent ?? "";
    expect(cards).toContain("Modelled quantity unavailable");
    expect(cards).not.toContain("× selected fuel coefficient");
  });

  it("q12-5: zero observed USE seconds is no observed minute; under a minute states the seconds, never `for 0 min`", async () => {
    const withUse = (coverage: FuelRow["coverage"]) => rows().map((r) => (r.term === "USE" ? { ...r, coverage } : r));
    renderFuel([ok(read({ rows: withUse({ ...FULL, observed_seconds: 0, gaps: ZERO.gaps }) }))]);
    await settledScreen();
    await screen.findByText("Fuel balance: Unknown");
    let cards = document.querySelector("[data-mini-cards]")?.textContent ?? "";
    expect(cards).toContain("Modelled quantity unavailable");
    expect(cards).not.toContain("0 min");
    cleanup();
    renderFuel([ok(read({ rows: withUse({ ...FULL, observed_seconds: 30 }) }))]);
    await settledScreen();
    await screen.findByText("Fuel balance: Unknown");
    cards = document.querySelector("[data-mini-cards]")?.textContent ?? "";
    expect(cards).toContain("Modelled: generator output for 30 s × selected fuel coefficient with selected bound");
    expect(cards).not.toContain("0 min");
  });

  it("503 shows the retry copy and retries", async () => {
    const unavailable: MiniRead<FuelRead> = { status: "refused", httpStatus: 503, code: "MINI_DEPTH_STORE_UNAVAILABLE", message: "x" };
    const client = renderFuel([unavailable, ok(read())]);
    await settledScreen();
    expect(await screen.findByText("Mini-grid evidence is unavailable right now. Try again.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await screen.findByText("Fuel balance: Unknown");
    expect(client.getFuel).toHaveBeenCalledTimes(2);
  });
});

describe("post-W6 W4 R313: fuel refused frame", () => {
  const CASES: Array<[string, string, string]> = [
    ["two hours", "from=2026-10-06T09:00:00Z&to=2026-10-06T11:00:00Z", "Choose one complete Site-local hour or one day."],
    ["a reversed range", "from=2026-10-06T10:00:00Z&to=2026-10-06T09:00:00Z", "The end must be after the start."],
    ["an unprovable cause", "from=2026-10-06T09:30:00Z&to=2026-10-06T10:30:00Z", "Choose a valid Site-local window."],
  ];
  // unit-5 capture: the refused frame keeps every v69 panel of the screen, in page order.
  const REFUSED_PANELS = ["Fuel balance at a glance", "Balance bridge", "Inspect existing generator fuel interpretation"];

  it.each(CASES)("R313: a refused window (%s) keeps strip, muted tiles and the named panels with one client reason", async (_name, query, reason) => {
    const message = "SERVER MESSAGE `INVALID_WINDOW` must not show";
    renderFuel([{ status: "refused", httpStatus: 422, code: "INVALID_WINDOW", message }], `/sites/${CODE}/performance/fuel?${query}`);
    await settledScreen();
    expect(await screen.findByText(reason)).toBeTruthy();
    expect(main().textContent).not.toContain("SERVER MESSAGE");
    expect(main().textContent).not.toContain("INVALID_WINDOW");
    expect(strip()).toContain("Window cannot be read");
    expect(strip()).toContain("Confidence: Not assessed");
    expect(cardValues()).toEqual(["Not assessed", "Not assessed", "Not assessed", "Not assessed"]);
    expect(panelTitled(REFUSED_PANELS[0]).textContent).toContain(reason);
    for (const title of REFUSED_PANELS.slice(1)) expect(panelTitled(title).textContent).toContain("Not assessed");
    expect(Array.from(document.querySelectorAll("main section.panel h2"), (h) => h.textContent?.trim())).toEqual(REFUSED_PANELS);
    expect(screen.getAllByText(reason)).toHaveLength(1);
  });
});
