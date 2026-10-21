/**
 * S5-01 phase 2: the imported-Site selected-window Overview at the existing Site Overview route.
 *
 * The server's `site-window-summary-1` is the only authority: these tests feed exact server states and check that
 * the screen names them, shows an amount only for `PRICED` with both display bounds, keeps the selected day and
 * Finding version in the address across reloads, and links to exact versions.
 */
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import type { FindingIndexClient } from "../../sites/findingIndexClient";
import type {
  OverviewSelection,
  SiteOverviewClient,
  SiteWindowSummary,
} from "../../sites/siteOverviewClient";
import { createSiteOverviewClient } from "../../sites/siteOverviewClient";
import { POPULATED_EVIDENCE, evidenceClient } from "../../sites/__tests__/evidenceFixtures";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import { MINIGRID_OBJECTIVE, MONEY_STATE_WORDS, OVERVIEW_MINI_UNAVAILABLE, SiteWindowOverview, overviewReadsStrip } from "../../sites/SiteWindowOverview";
import type { MiniDepthClient, MiniRead, MiniWindowQuery } from "../../sites/miniDepthClient";
import { describeViolations, scanDisclosureVocabulary, scanProductVocabulary } from "../../test/productVocabulary";
import { expectStateLineVisible, visibleOutsideClosedDisclosure } from "../../test/productPresentation";
import { expectV69Panels } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import { FID, RID, RID_NEW, CID, PRICE, EVIDENCE, WA, money, summary } from "./s5WindowFixtures";

const SITE_ID = HYBRID_MINI_GRID_SITE.site_id;
const DIRECTORY: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [] }) };
const DETAIL: SiteDetailClient = {
  getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }),
};

function LocationProbe() {
  const location = useLocation();
  return <output data-location>{`${location.pathname}${location.search}`}</output>;
}

function clientOf(answer: (selection: OverviewSelection) => SiteWindowSummary) {
  const getOverview = vi.fn((_site: string, _w: unknown, selection: OverviewSelection = {}) =>
    Promise.resolve({ status: "loaded" as const, value: answer(selection) }),
  );
  return { client: { getOverview } as unknown as SiteOverviewClient, getOverview };
}

/** S5-02: the Finding list's own read; these S5-01 tests keep it unavailable (S5-02 cases live in their own file). */
const NO_INDEX: FindingIndexClient = { getFindingIndex: () => Promise.resolve({ status: "unavailable", message: null }) };

/** W4-02: these S5-01 tests keep the mini reads unavailable (the mini card cases have their own block). */
const NO_MINI: MiniDepthClient = (() => {
  const no = () => Promise.resolve({ status: "unavailable" as const, message: null });
  return { getCapabilities: no, getService: no, getFuel: no, getRenewable: no, getBackup: no };
})();

function renderAt(path: string, overview: SiteOverviewClient) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={featureFlagsWith(false)}
        siteDirectory={DIRECTORY}
        siteDetail={DETAIL}
        siteEvidence={evidenceClient({ status: "loaded", value: POPULATED_EVIDENCE })}
        siteOverview={overview}
        siteFindingIndex={NO_INDEX}
        miniDepth={NO_MINI}
      />
      <LocationProbe />
    </MemoryRouter>,
  );
}

function where(): string {
  return document.querySelector("[data-location]")?.textContent ?? "";
}

function moneyCard(): HTMLElement {
  return document.querySelector("[data-money-state]") as HTMLElement;
}

const NO_AMOUNT_STATES = Object.keys(MONEY_STATE_WORDS).filter((s) => s !== "PRICED");

describe("S5-01 selected-window Overview: date and selection in the address", () => {
  it("writes the server's default day and selected Finding version to the address without reading twice", async () => {
    const { client, getOverview } = clientOf(() => summary("2026-10-23"));
    renderAt(`/sites/${SITE_ID}`, client);
    await settledScreen();
    expect(screen.getByText("0.00 to 15.82 USD")).toBeTruthy();
    expect(where()).toBe(`/sites/${SITE_ID}?date=2026-10-23&finding_id=${FID}&finding_revision_id=${RID}`);
    expect(getOverview).toHaveBeenCalledTimes(1);
    expect(getOverview.mock.calls[0][2]).toEqual({ date: null, finding_id: null, finding_revision_id: null });
  });

  it("reloads with the day and the pinned Finding version from the address", async () => {
    const { client, getOverview } = clientOf((s) => summary(s.date ?? "x", {}, { finding_revision_id: s.finding_revision_id ?? RID }));
    renderAt(`/sites/${SITE_ID}?date=2026-10-24&finding_id=${FID}&finding_revision_id=${RID}`, client);
    await settledScreen();
    expect(getOverview.mock.calls[0][2]).toEqual({ date: "2026-10-24", finding_id: FID, finding_revision_id: RID });
    expect(getOverview).toHaveBeenCalledTimes(1);
    expect(document.querySelector("[data-window-date]")?.getAttribute("data-window-date")).toBe("2026-10-24");
  });

  it("changes the UTC day, drops the Finding pin and keeps the new day", async () => {
    const { client, getOverview } = clientOf((s) => summary(s.date ?? "2026-10-23"));
    renderAt(`/sites/${SITE_ID}?date=2026-10-23&finding_id=${FID}&finding_revision_id=${RID}`, client);
    await settledScreen();
    fireEvent.click(screen.getByRole("link", { name: "Next day" }));
    await settledScreen();
    expect(getOverview.mock.calls.at(-1)?.[2]).toEqual({ date: "2026-10-24", finding_id: null, finding_revision_id: null });
    expect(where()).toContain("date=2026-10-24");
    fireEvent.change(document.querySelector("[data-window-date-input]") as HTMLInputElement, {
      target: { value: "2026-11-10" },
    });
    await settledScreen();
    expect(getOverview.mock.calls.at(-1)?.[2]).toEqual({ date: "2026-11-10", finding_id: null, finding_revision_id: null });
  });

  it("follows the server when the settled Finding version changes (new version after reassessment)", async () => {
    const { client } = clientOf(() => summary("2026-10-24", {}, { finding_revision_id: RID_NEW }));
    renderAt(`/sites/${SITE_ID}?date=2026-10-24&finding_id=${FID}&finding_revision_id=${RID}`, client);
    await settledScreen();
    expect(where()).toContain(`finding_revision_id=${RID_NEW}`);
  });

  it("sends date and pin as query parameters on the existing Overview route", async () => {
    const fetchMock = vi.fn(() => Promise.resolve(new Response(JSON.stringify(summary()), { status: 200 })));
    vi.stubGlobal("fetch", fetchMock);
    try {
      const read = await createSiteOverviewClient("/api/sites").getOverview("KOBO-001", {}, {
        date: "2026-10-23",
        finding_id: FID,
        finding_revision_id: RID,
      });
      expect(read.status).toBe("loaded");
      expect(fetchMock.mock.calls[0]).toEqual([
        `/api/sites/KOBO-001/overview?date=2026-10-23&finding_id=${FID}&finding_revision_id=${RID}`,
      ]);
      const broken = { ...summary(), finding_list: { state: "EMPTY", reason: "" } };
      fetchMock.mockImplementationOnce(() => Promise.resolve(new Response(JSON.stringify(broken), { status: 200 })));
      expect((await createSiteOverviewClient("/api/sites").getOverview("KOBO-001", {})).status).toBe("unavailable");
    } finally {
      vi.unstubAllGlobals();
    }
  });
});

describe("S5-01 selected-window Overview: money states", () => {
  it("shows the priced P01 amount with its stored source label and exact links", async () => {
    const { client } = clientOf(() => summary());
    renderAt(`/sites/${SITE_ID}?date=2026-10-23`, client);
    await settledScreen();
    const card = moneyCard();
    expect(card.getAttribute("data-money-state")).toBe("PRICED");
    expect(within(card).getByText("0.00 to 15.82 USD")).toBeTruthy();
    expect(card.querySelector('[data-source-provenance="AUTHORED_DEMONSTRATION"]')).toHaveTextContent("Prepared example data.");
    // Slice review L3: the Operating objective panel reads the day's claim level and coverage; no objective is implied.
    // Final review ruling 1 (H3): a MINIGRID Overview states the mini-grid objective, not the dispatch-only line.
    expect(document.querySelector("[data-objective-statement]")?.textContent).toBe(MINIGRID_OBJECTIVE);
    expect(document.querySelector('[data-assessment-claim="CANDIDATE_AVOIDABLE"]')?.textContent).toContain("Possibly avoidable");
    const financials = card.querySelector("[data-window-financials-link]")?.getAttribute("href");
    expect(financials).toContain(`finding_id=${FID}`);
    expect(financials).toContain(`revision_id=${RID}`);
    expect(financials).toContain(`consequence_revision_id=${CID}`);
    expect(card.querySelector(`[data-window-assumption-link="${PRICE}"]`)?.getAttribute("href")).toContain(
      `revision_id=${PRICE}`,
    );
    expect(card.querySelector(`[data-window-lineage-evidence="${EVIDENCE}"]`)?.getAttribute("href")).toContain(
      `record=${EVIDENCE}`,
    );
    const finding = document.querySelector(`[data-window-finding-link="${FID}"]`)?.getAttribute("href");
    expect(finding).toBe(`/sites/${SITE_ID}/findings/${FID}?revision_id=${RID}`);
    expect(document.querySelector(`[data-window-evidence-link="${EVIDENCE}"]`)?.getAttribute("href")).toContain(
      `record=${EVIDENCE}`,
    );
    expect(document.querySelector("[data-window-dispatch-link]")?.getAttribute("href")).toContain(
      `day=2026-10-23&revision=${WA}`,
    );
  });

  it.each(NO_AMOUNT_STATES)("%s shows no amount, names the state and keeps the selected Finding", async (state) => {
    const { client } = clientOf(() =>
      summary("2026-10-24", {}, { state, amount_low: null, amount_high: null, currency: null, limitation: [state] }),
    );
    renderAt(`/sites/${SITE_ID}?date=2026-10-24`, client);
    await settledScreen();
    const card = moneyCard();
    expect(card.getAttribute("data-money-state")).toBe(state);
    expect(card.querySelector('[data-money-amount="none"]')).not.toBeNull();
    expect(within(card).getByText(MONEY_STATE_WORDS[state].label)).toBeTruthy();
    expect(card.textContent).not.toMatch(/\d+\.\d\d to \d/);
    expect(document.querySelector(`[data-known-finding="${FID}"]`)).not.toBeNull();
  });

  it.each([["amount_low"], ["amount_high"]])("a PRICED read missing %s shows no amount and no positive Current amount label", async (missing) => {
    const { client } = clientOf(() => summary("2026-10-24", {}, { state: "PRICED", [missing]: null }));
    renderAt(`/sites/${SITE_ID}?date=2026-10-24`, client);
    await settledScreen();
    const card = moneyCard();
    expect(card.querySelector('[data-money-amount="none"]')).not.toBeNull();
    expect(card.querySelector("[data-money-amount]:not([data-money-amount='none'])")).toBeNull();
    expect(within(card).queryByText("Current amount")).toBeNull();
    expect(card.textContent).not.toMatch(/\d+\.\d\d to \d/);
    expect(card.querySelector("[data-product-status-tone='positive']")).toBeNull();
  });

  it("never shows an amount the server did not price, even when amount fields are present", async () => {
    const { client } = clientOf(() => summary("2026-10-24", {}, { state: "WITHHELD_GENERATOR_SERIES" }));
    renderAt(`/sites/${SITE_ID}?date=2026-10-24`, client);
    await settledScreen();
    expect(moneyCard().querySelector("[data-money-amount]")?.getAttribute("data-money-amount")).toBe("none");
    expect(screen.queryByText("0.00 to 15.82 USD")).toBeNull();
  });

  it.each(["MIXED", "UNKNOWN"] as const)(
    "a %s stored source withholds the amount and names the source state (S4-05b)",
    async (source) => {
      const base = summary().money;
      const { client } = clientOf(() =>
        summary("2026-10-23", {}, {
          state: "MIXED_OR_UNKNOWN_SOURCE",
          amount_low: null,
          amount_high: null,
          limitation: ["MIXED_OR_UNKNOWN_SOURCE"],
          source_provenance: { ...base.source_provenance!, state: source, problematic_accepted_evidence_ids: [EVIDENCE] },
          source_gate: { state: source, permits_current_money: false, reason: "MIXED_OR_UNKNOWN_SOURCE" },
        }),
      );
      const { container } = renderAt(`/sites/${SITE_ID}?date=2026-10-23`, client);
      await settledScreen();
      const card = moneyCard();
      expect(card.getAttribute("data-money-state")).toBe("MIXED_OR_UNKNOWN_SOURCE");
      expect(card.querySelector("[data-money-amount]")?.getAttribute("data-money-amount")).toBe("none");
      expect(card.querySelector(`[data-source-provenance="${source}"]`)).toHaveTextContent(
        source === "MIXED" ? "Sources do not agree." : "Source unverified.",
      );
      expect(card).toHaveTextContent("No current cost is shown.");
      const { violations } = scanProductVocabulary(container, `overview ${source}`);
      expect(violations, describeViolations(violations)).toEqual([]);
    },
  );

  it("after attestation and before reassessment: upstream out of date while the gate reads pending reassessment", async () => {
    const { client } = clientOf(() =>
      summary(
        "2026-10-24",
        { freshness: { state: "STALE_PROJECTION", stage: "S3", reasons: ["S3_STALE_PROJECTION", "LIVE_JOB"], errors: [], source_open: true, source_reason: "open" } },
        {
          state: "UPSTREAM_STALE",
          amount_low: null,
          amount_high: null,
          eligibility: { ...money().eligibility!, state: "PENDING_REASSESSMENT" },
          upstream: { status: "STALE_PROJECTION", stage: "S3", reasons: ["S3_STALE_PROJECTION", "LIVE_JOB"] },
        },
      ),
    );
    renderAt(`/sites/${SITE_ID}?date=2026-10-24`, client);
    await settledScreen();
    const card = moneyCard();
    expect(within(card).getByText("Upstream out of date")).toBeTruthy();
    expect(card.querySelector("[data-money-gate-state]")?.textContent).toBe("Pending reassessment");
    expect(card.querySelector('[data-money-amount="none"]')).not.toBeNull();
  });

  it("a stopped schedule and a closed source are named, with no amount", async () => {
    const stopped = clientOf(() =>
      summary(
        "2026-10-24",
        { freshness: { state: "STALE_PROJECTION", stage: "SCHEDULE", reasons: ["SCHEDULE_STOPPED"], errors: [], source_open: true, source_reason: "open" } },
        { state: "UPSTREAM_STALE", amount_low: null, amount_high: null, upstream: { status: "STALE_PROJECTION", stage: "SCHEDULE", reasons: ["SCHEDULE_STOPPED"] } },
      ),
    );
    const view = renderAt(`/sites/${SITE_ID}?date=2026-10-24`, stopped.client);
    await settledScreen();
    expect(document.querySelector('[data-window-reasons="freshness"]')?.textContent).toContain("SCHEDULE_STOPPED");
    expect(document.querySelector("[data-money-gate-state]")?.textContent).toBe("Eligible");
    view.unmount();
    const closed = clientOf(() =>
      summary(
        "2026-10-24",
        {
          freshness: { state: "STALE_PROJECTION", stage: null, reasons: ["SOURCE_CLOSED"], errors: [], source_open: false, source_reason: "no comparison" },
          assessment: { ...summary().assessment, state: "CLOSED", dispatch_intervals: [], window_assessment_revision_id: null },
        },
        { state: "SOURCE_CLOSED", amount_low: null, amount_high: null },
      ),
    );
    renderAt(`/sites/${SITE_ID}?date=2026-10-24`, closed.client);
    await settledScreen();
    expect(document.querySelector('[data-source-open="closed"]')).not.toBeNull();
    expect(document.querySelector('[data-assessment-state="CLOSED"]')).not.toBeNull();
    // W1-UX-02: the closed-source money words are plain; the state line is checked with the disclosure closed.
    expect(within(moneyCard()).getByText("No current amount: source not open")).toBeTruthy();
    expect(expectStateLineVisible(moneyCard())).toBe("No current amount: source not open");
  });
});

describe("S5-01 selected-window Overview: day states and the Finding list", () => {
  it("an unassessed day reads Unknown and the Finding list is not known, never empty", async () => {
    const { client } = clientOf(() =>
      summary(
        "2026-11-10",
        {
          freshness: { state: "UNASSESSED", stage: "S3", reasons: ["S3_UNASSESSED"], errors: [], source_open: true, source_reason: "open" },
          assessment: { ...summary().assessment, state: "UNKNOWN", status: "UNASSESSED", dispatch_intervals: [], run_id: null, window_assessment_revision_id: null },
          known_finding: null,
        },
        { state: "UPSTREAM_UNASSESSED", amount_low: null, amount_high: null, finding_id: null, finding_revision_id: null, consequence_revision_id: null, eligibility: null },
      ),
    );
    renderAt(`/sites/${SITE_ID}?date=2026-11-10`, client);
    await settledScreen();
    // W1-UX-02: the freshness strip uses the shared currentness words (was the local "Unknown").
    expect(document.querySelector('[data-freshness-state="UNASSESSED"]')?.textContent).toContain("We have not checked this period");
    expect(expectStateLineVisible(freshnessCard())).toBe("We have not checked this period");
    expect(freshnessCard().querySelector("[data-freshness-in-statusbar]")?.getAttribute("data-freshness-in-statusbar")).toBe("no");
    // W1-UX-01: the shared state words; the state line stays outside the closed exact-reference disclosure.
    const unknownState = document.querySelector('[data-assessment-state="UNKNOWN"]') as HTMLElement;
    expect(unknownState.textContent).toContain("We cannot judge this yet");
    expect(unknownState.textContent).toContain("No assessment is selected for this day");
    expect(expectStateLineVisible(objectiveCard())).toBe("We cannot judge this yet");
    expect(document.querySelector('[data-overview-finding-list="unavailable"]')?.textContent).toContain("no count is given");
    expect(document.body.textContent).not.toMatch(/no findings (for|in) this/i);
    expect(document.querySelector('[data-overview-finding-list="current-empty"]')).toBeNull();
    expect(where()).toBe(`/sites/${SITE_ID}?date=2026-11-10`);
  });

  it("states the server's gap reason in plain words, never verbatim (review fix M5a)", async () => {
    const raw = "No reviewed gap rule exists for the Site context; coverage counts and the selected S3 coverage are shown instead.";
    const { client } = clientOf(() => summary("2026-10-24", { context: { ...summary().context, gaps_reason: raw } }));
    renderAt(`/sites/${SITE_ID}?date=2026-10-24`, client);
    await settledScreen();
    const gaps = document.querySelector("[data-window-gaps]") as HTMLElement;
    expect(gaps.textContent).toBe("No rule yet says which gaps in the readings matter here; the reading counts are shown instead.");
    expect(document.body.textContent).not.toContain(raw);
  });

  it("names a Finding pin the server did not honour for this day", async () => {
    const { client } = clientOf(() =>
      summary("2026-10-24", {
        known_finding: null,
        previous_pin: { finding_id: FID, finding_revision_id: RID, reason: "NOT_IN_SELECTED_DAY" },
      }),
    );
    renderAt(`/sites/${SITE_ID}?date=2026-10-24&finding_id=${FID}&finding_revision_id=${RID}`, client);
    await settledScreen();
    expect(document.querySelector('[data-previous-pin="NOT_IN_SELECTED_DAY"]')?.textContent).toContain(
      "does not overlap this day",
    );
    expect(where()).toBe(`/sites/${SITE_ID}?date=2026-10-24`);
  });

  it("a failed day reads Failed", async () => {
    const { client } = clientOf(() =>
      summary(
        "2026-10-07",
        {
          freshness: { state: "FAILED", stage: "S3", reasons: ["S3_FAILED"], errors: [], source_open: true, source_reason: "open" },
          assessment: { ...summary().assessment, state: "FAILED", status: "FAILED", dispatch_intervals: [] },
          known_finding: null,
        },
        { state: "UPSTREAM_FAILED", amount_low: null, amount_high: null, finding_id: null, finding_revision_id: null, consequence_revision_id: null, eligibility: null },
      ),
    );
    renderAt(`/sites/${SITE_ID}?date=2026-10-07`, client);
    await settledScreen();
    // W1-UX-02: the freshness strip uses the shared currentness words (was the local "Failed").
    // Review fix M3: the FAILED freshness state is marked on panel 1's line; its words are the statusbar's (next lines).
    expect(document.querySelector('[data-freshness-state="FAILED"]')).not.toBeNull();
    // Review fix M3: the freshness words equal the statusbar's, so they are said once, in the statusbar (asserted below).
    expectFreshnessInStatusbar();
    expect(document.querySelector('[data-assessment-state="FAILED"]')?.textContent).toContain("The latest check could not be completed");
    expect(expectStateLineVisible(objectiveCard())).toBe("The latest check could not be completed");
    expect(moneyCard().getAttribute("data-money-state")).toBe("UPSTREAM_FAILED");
  });

  it("uses product vocabulary only", async () => {
    const { client } = clientOf(() => summary());
    const { container } = renderAt(`/sites/${SITE_ID}?date=2026-10-23`, client);
    await settledScreen();
    const { violations, scanned } = scanProductVocabulary(container, "selected-day overview");
    expect(scanned).toBeGreaterThan(5);
    expect(violations, describeViolations(violations)).toEqual([]);
  });

  it("W1-UX-01: the objective card uses the W1 vocabulary set, its disclosure the narrower list, and its state line stays visible", async () => {
    const { client } = clientOf(() => summary());
    const { container } = renderAt(`/sites/${SITE_ID}?date=2026-10-23`, client);
    await settledScreen();
    const w1 = scanProductVocabulary(container.querySelector("main") as HTMLElement, "selected-day overview (W1)", { set: "w1" });
    expect(w1.scanned).toBeGreaterThan(5);
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
    const disclosure = scanDisclosureVocabulary(dayReading(), "overview objective disclosure");
    expect(disclosure.disclosures).toBe(1);
    expect(disclosure.scanned).toBeGreaterThan(2);
    expect(disclosure.violations, describeViolations(disclosure.violations)).toEqual([]);
    expect(expectStateLineVisible(objectiveCard())).toBe("Using the latest checked readings");
    expect(objectiveCard().querySelector("[data-product-status-as-of]")?.textContent).toMatch(/^As of \d{1,2} \w{3} \d{4}, \d{2}:\d{2} UTC$/);
  });
});

/**
 * W1-F2: the former objective answer card is gone (v69 `mini` has no leading card). Its state line is the mock's
 * statusbar above the panels; its exact references sit with the day reading in panel 1.
 */
function objectiveCard(): HTMLElement {
  return document.querySelector("[data-overview-status]") as HTMLElement;
}

function dayReading(): HTMLElement {
  return document.querySelector('[data-disclosure="window-assessment"]')?.parentElement as HTMLElement;
}

function dispatchObjective(): string {
  return document.querySelector('[data-objective-card="dispatch"] .v69-metric__value')?.textContent ?? "";
}

function freshnessCard(): HTMLElement {
  return document.querySelector("[data-freshness-card]") as HTMLElement;
}

/** Review fix M3: panel 1 renders no second state line when the freshness words equal the statusbar's. */
function expectFreshnessInStatusbar(): void {
  const card = freshnessCard();
  expect(card.querySelector("[data-freshness-in-statusbar]")?.getAttribute("data-freshness-in-statusbar")).toBe("yes");
  expect(card.querySelector(".product-status")).toBeNull();
  expect(card.querySelector("[data-source-open]")).not.toBeNull();
}

describe("W1-UX-02: the selected-day Overview (mini) on the W1 set", () => {
  it("leads with the day answer; the whole route, every exact-reference disclosure and each state line pass", async () => {
    const { client } = clientOf(() => summary());
    const { container } = renderAt(`/sites/${SITE_ID}?date=2026-10-23`, client);
    await settledScreen();
    const main = container.querySelector("main") as HTMLElement;
    // W1-F2: the day state leads as the mock's statusbar; no answer card precedes the five v69 panels.
    expect(main.querySelector("[data-headline-card]")).toBeNull();
    // Review Low 7b: the day chooser chip row comes first (as on Dispatch and Evidence), then the statusbar leads the content.
    expect(main.querySelector(".site-window-overview")?.firstElementChild?.classList.contains("window-day")).toBe(true);
    expect(main.querySelector(".site-window-overview .window-day")?.nextElementSibling).toBe(objectiveCard());
    expectV69Panels("mini");
    const w1 = scanProductVocabulary(main, "selected-day overview (W1-UX-02)", { set: "w1" });
    expect(w1.scanned).toBeGreaterThan(30);
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
    for (const [name, card] of [
      ["freshness", freshnessCard()],
      ["money", moneyCard()],
      ["known finding", document.querySelector(`[data-known-finding="${FID}"]`) as HTMLElement],
    ] as const) {
      const d = scanDisclosureVocabulary(card, `overview ${name} disclosure`);
      expect(d.disclosures, name).toBe(1);
      expect(d.scanned, name).toBeGreaterThan(2);
      expect(d.violations, describeViolations(d.violations)).toEqual([]);
    }
    // Current and priced claims keep a plain "as of" beside them.
    // Review fix M3: said once, in the statusbar; panel 1 keeps only the source sentence.
    expectFreshnessInStatusbar();
    expect(expectStateLineVisible(objectiveCard())).toBe("Using the latest checked readings");
    // Review fix M3: panel 1 has one "How this was worked out" disclosure (day reading and freshness merged).
    const happened = freshnessCard().closest(".panel") as HTMLElement;
    expect([...happened.querySelectorAll("summary")].filter((x) => x.textContent === "How this was worked out")).toHaveLength(1);
    expect(expectStateLineVisible(moneyCard())).toBe("Current amount");
    // The amount is drawn as two bounded bars; the raw recorded label and method reference are exact detail only.
    expect(moneyCard().querySelectorAll('[data-value-bar="known"]')).toHaveLength(2);
    const label = summary().money.label;
    const moneyDetail = moneyCard().querySelector("[data-exact-references]") as HTMLElement;
    expect(moneyDetail.textContent).toContain(label);
    expect(moneyDetail.textContent).toContain("fuel-cost-1");
    expect((moneyCard().textContent ?? "").replace(moneyDetail.textContent ?? "", "")).not.toContain(label);
    expect(moneyCard().querySelector("[data-money-qualifier]")?.textContent).toContain("not money lost or saved");
    // The timeline is a readable figure with a legend; no raw device or signal name labels a row.
    const figure = main.querySelector("[data-window-timeline-figure]") as HTMLElement;
    expect(figure.getAttribute("aria-label")).toContain("06:00 to 08:00: generator possibly avoidable");
    expect(figure.querySelector("[data-window-timeline-legend]")?.textContent).toContain("Generator possibly avoidable");
    expect(figure.querySelector("[data-window-timeline-legend]")?.textContent).toContain("Readings received");
    // Exact links still work.
    expect(document.querySelector(`[data-window-finding-link="${FID}"]`)?.getAttribute("href")).toBe(
      `/sites/${SITE_ID}/findings/${FID}?revision_id=${RID}`,
    );
  });

  it("W1-F2 compaction: amount, state, source and qualifier stay visible; bars, gate, links and readings detail are closed", async () => {
    const { client } = clientOf(() => summary("2026-10-23"));
    const { container } = renderAt(`/sites/${SITE_ID}?date=2026-10-23`, client);
    await settledScreen();
    const card = moneyCard();
    const shown = (el: Element | null) => el !== null && visibleOutsideClosedDisclosure(el);
    // Visible, in the mock's short form: amount, inline state line, source line, qualifier, header link.
    expect(shown(card.querySelector("[data-money-amount]"))).toBe(true);
    expect(card.querySelector("[data-money-state-line] .product-status--inline")).not.toBeNull();
    expect(shown(card.querySelector("[data-source-provenance] .source-provenance__line"))).toBe(true);
    expect(shown(card.querySelector("[data-money-qualifier]"))).toBe(true);
    expect(container.querySelector("[data-window-financials-action]")?.getAttribute("href")).toBe(
      card.querySelector("[data-window-financials-link]")?.getAttribute("href"),
    );
    // One closed detail disclosure holds the bars, the gate and upstream facts, the links and the exact references.
    const detail = card.querySelector('details[data-disclosure="window-money-detail"]') as HTMLDetailsElement;
    expect(detail.open).toBe(false);
    for (const sel of ["[data-value-bars]", "[data-money-gate-state]", "[data-money-upstream]", "[data-window-money-links]", "[data-exact-references]"]) {
      expect(detail.querySelector(sel), sel).not.toBeNull();
      expect(shown(card.querySelector(sel)), sel).toBe(false);
    }
    // W1-F5b carry 8: the panel has exactly one closed row; the cost's source record folds into it.
    const topLevelRows = [...card.querySelectorAll("details")].filter((d) => d.parentElement?.closest("details") === null);
    expect(topLevelRows).toEqual([detail]);
    expect(card.querySelector('details[data-disclosure="source-provenance-overview-money"]')).toBeNull();
    expect(detail.querySelector("[data-source-record='overview-money'] [data-source-method]")).not.toBeNull();
    // Context: the count line stays visible; the per-input table and record links are closed detail.
    expect(shown(container.querySelector("[data-window-context]"))).toBe(true);
    const coverage = container.querySelector('details[data-disclosure="window-coverage"]') as HTMLDetailsElement;
    expect(coverage.open).toBe(false);
    expect(coverage.querySelector("table")).not.toBeNull();
    expect(coverage.querySelector("[data-window-readings]")).not.toBeNull();
    // The day chooser is the leading chip row (before panel 1, outside every panel), with the day's bounds in it;
    // Next step keeps its button and Dispatch link on one line.
    expect(container.querySelector(".window-day [data-window-bounds]")?.textContent).toContain("start included, end excluded");
    expect(container.querySelector(".window-day")?.closest(".panel")).toBeNull();
    const actions = container.querySelector(".overview-next__actions") as HTMLElement;
    expect(actions.querySelector("[data-overview-next-finding]")).not.toBeNull();
    expect(actions.querySelector("[data-overview-next-dispatch]")).not.toBeNull();
  });

  it("a stale day: the freshness strip, the money card and the timeline say so with the disclosure closed", async () => {
    const { client } = clientOf(() =>
      summary(
        "2026-10-24",
        {
          freshness: { state: "STALE_PROJECTION", stage: "S3", reasons: ["S3_STALE_PROJECTION"], errors: [], source_open: true, source_reason: "open" },
          assessment: { ...summary().assessment, state: "STALE_PROJECTION", status: "STALE_PROJECTION" },
        },
        { state: "UPSTREAM_STALE", amount_low: null, amount_high: null, upstream: { status: "STALE_PROJECTION", stage: "S3", reasons: ["S3_STALE_PROJECTION"] } },
      ),
    );
    const { container } = renderAt(`/sites/${SITE_ID}?date=2026-10-24`, client);
    await settledScreen();
    // Review fix M3: the freshness words equal the statusbar's, so they are said once, in the statusbar (asserted below).
    expectFreshnessInStatusbar();
    expect(expectStateLineVisible(moneyCard())).toBe("Upstream out of date");
    expect(expectStateLineVisible(objectiveCard())).toBe("This result may miss newer readings");
    // W1-F2: the Dispatch objective card names the same not-current state, never a current answer.
    expect(dispatchObjective()).toBe("This result may miss newer readings");
    expect(moneyCard().querySelector('[data-money-amount="none"]')).not.toBeNull();
    expect(moneyCard().querySelector("[data-value-bars]")).toBeNull();
    expect(container.querySelector("[data-window-timeline-figure] figcaption")?.textContent).toContain("not current");
    // The raw reason is exact detail only.
    expect(freshnessCard().querySelector("[data-exact-references]")?.textContent).toContain("S3_STALE_PROJECTION");
    const w1 = scanProductVocabulary(container.querySelector("main") as HTMLElement, "overview stale (W1)", { set: "w1" });
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
  });

  it("a pending day: freshness and money are waiting, never current, and show no amount", async () => {
    const { client } = clientOf(() =>
      summary(
        "2026-10-24",
        {
          freshness: { state: "PENDING", stage: "S3", reasons: ["S3_PENDING"], errors: [], source_open: true, source_reason: "open" },
          assessment: { ...summary().assessment, state: "PENDING", status: "PENDING" },
        },
        { state: "UPSTREAM_PENDING", amount_low: null, amount_high: null, upstream: { status: "PENDING", stage: "S3", reasons: ["S3_PENDING"] } },
      ),
    );
    const { container } = renderAt(`/sites/${SITE_ID}?date=2026-10-24`, client);
    await settledScreen();
    // Review fix M3: the freshness words equal the statusbar's, so they are said once, in the statusbar (asserted below).
    expectFreshnessInStatusbar();
    expect(expectStateLineVisible(moneyCard())).toBe("No amount yet: checks still waiting");
    expect(expectStateLineVisible(objectiveCard())).toBe("Not checked yet");
    expect(moneyCard().querySelector('[data-money-amount="none"]')).not.toBeNull();
    expect(moneyCard().querySelector("[data-product-status]")?.getAttribute("data-product-status")).toBe("waiting");
    const w1 = scanProductVocabulary(container.querySelector("main") as HTMLElement, "overview pending (W1)", { set: "w1" });
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
  });

  it("an unassessed day: freshness, objective and money each name it, with no amount", async () => {
    const { client } = clientOf(() =>
      summary(
        "2026-11-10",
        {
          freshness: { state: "UNASSESSED", stage: "S3", reasons: ["S3_UNASSESSED"], errors: [], source_open: true, source_reason: "open" },
          assessment: { ...summary().assessment, state: "UNKNOWN", status: "UNASSESSED", dispatch_intervals: [], run_id: null, window_assessment_revision_id: null },
          known_finding: null,
        },
        { state: "UPSTREAM_UNASSESSED", amount_low: null, amount_high: null, finding_id: null, finding_revision_id: null, consequence_revision_id: null, eligibility: null },
      ),
    );
    const { container } = renderAt(`/sites/${SITE_ID}?date=2026-11-10`, client);
    await settledScreen();
    expect(expectStateLineVisible(freshnessCard())).toBe("We have not checked this period");
    expect(expectStateLineVisible(objectiveCard())).toBe("We cannot judge this yet");
    expect(expectStateLineVisible(moneyCard())).toBe("No amount: day not checked");
    expect(moneyCard().querySelector("[data-money-qualifier]")).toBeNull();
    expect(container.querySelector("[data-window-timeline-figure]")?.getAttribute("aria-label")).toContain("No assessed period is drawn");
    const w1 = scanProductVocabulary(container.querySelector("main") as HTMLElement, "overview unassessed (W1)", { set: "w1" });
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
  });

  it("a proved-zero day (no Finding overlaps it): the money card says so with a plain as-of, never an amount", async () => {
    const { client } = clientOf(() =>
      summary(
        "2026-10-25",
        { known_finding: null },
        { state: "ABSENT", amount_low: null, amount_high: null, finding_id: null, finding_revision_id: null, consequence_revision_id: null, eligibility: null },
      ),
    );
    const { container } = renderAt(`/sites/${SITE_ID}?date=2026-10-25`, client);
    await settledScreen();
    expect(expectStateLineVisible(moneyCard())).toBe("No Finding on this day");
    expect(moneyCard().querySelector("[data-product-status-as-of]")?.textContent).toBe("As of 25 Oct 2026, 12:00 UTC");
    expect(moneyCard().querySelector('[data-money-amount="none"]')).not.toBeNull();
    expect(moneyCard().textContent).not.toMatch(/\d+\.\d\d/);
    expect(moneyCard().querySelector("[data-value-bars]")).toBeNull();
    const w1 = scanProductVocabulary(container.querySelector("main") as HTMLElement, "overview proved zero (W1)", { set: "w1" });
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
  });

  it("a historical selection (audit-only Finding, earlier version): the Finding and money cards say it is not current", async () => {
    const base = summary("2026-10-24");
    const { client } = clientOf(() =>
      summary(
        "2026-10-24",
        { known_finding: { ...base.known_finding!, audit_only: true, selected_by: "PINNED_AUDIT" } },
        { state: "SUPERSEDED", amount_low: null, amount_high: null },
      ),
    );
    const { container } = renderAt(`/sites/${SITE_ID}?date=2026-10-24&finding_id=${FID}&finding_revision_id=${RID}`, client);
    await settledScreen();
    const known = document.querySelector(`[data-known-finding="${FID}"]`) as HTMLElement;
    expect(expectStateLineVisible(known)).toBe("For the record only");
    expect(expectStateLineVisible(moneyCard())).toBe("Earlier Finding version");
    expect(moneyCard().querySelector('[data-money-amount="none"]')).not.toBeNull();
    // The raw choice code is exact detail only.
    expect(known.querySelector("[data-exact-references]")?.textContent).toContain("PINNED_AUDIT");
    const w1 = scanProductVocabulary(container.querySelector("main") as HTMLElement, "overview historical (W1)", { set: "w1" });
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
  });

  it("a failed day: freshness, objective and money each say the check did not finish", async () => {
    const { client } = clientOf(() =>
      summary(
        "2026-10-07",
        {
          freshness: { state: "FAILED", stage: "S3", reasons: ["S3_FAILED"], errors: [], source_open: true, source_reason: "open" },
          assessment: { ...summary().assessment, state: "FAILED", status: "FAILED", dispatch_intervals: [] },
          known_finding: null,
        },
        { state: "UPSTREAM_FAILED", amount_low: null, amount_high: null, finding_id: null, finding_revision_id: null, consequence_revision_id: null, eligibility: null },
      ),
    );
    const { container } = renderAt(`/sites/${SITE_ID}?date=2026-10-07`, client);
    await settledScreen();
    // Review fix M3: the freshness words equal the statusbar's, so they are said once, in the statusbar (asserted below).
    expectFreshnessInStatusbar();
    expect(expectStateLineVisible(objectiveCard())).toBe("The latest check could not be completed");
    expect(expectStateLineVisible(moneyCard())).toBe("No amount: a check did not finish");
    const w1 = scanProductVocabulary(container.querySelector("main") as HTMLElement, "overview failed (W1)", { set: "w1" });
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
  });

  it("an unrecognised money state falls back to the neutral words, never a positive claim or an amount", async () => {
    const { client } = clientOf(() => summary("2026-10-24", {}, { state: "SOMETHING_NEW" }));
    renderAt(`/sites/${SITE_ID}?date=2026-10-24`, client);
    await settledScreen();
    expect(expectStateLineVisible(moneyCard())).toBe("We cannot judge this yet");
    expect(moneyCard().querySelector("[data-product-status]")?.getAttribute("data-product-status")).not.toBe("positive");
    expect(moneyCard().querySelector('[data-money-amount="none"]')).not.toBeNull();
  });
});

/*
 * W4-02 B3/Q24: the five Overview cards. Service, Fuel and Renewable read the mini endpoints (one Site-local day for
 * renewable, its local noon hour for service and fuel, one shared cutoff); Dispatch and Battery are unchanged; there
 * is no Backup card and no Overview backup read.
 */
describe("W4-02 Overview mini cards", () => {
  // HYBRID_MINI_GRID_SITE is Africa/Kampala (UTC+3): UTC day 2026-10-23 starts on local 2026-10-23.
  const HOUR = { from: "2026-10-23T09:00:00.000Z", to: "2026-10-23T10:00:00.000Z" };
  const DAY = { from: "2026-10-22T21:00:00.000Z", to: "2026-10-23T21:00:00.000Z" };
  const FULL = { required_seconds: 3600, observed_seconds: 3600, source_count: 1, gaps: [] };
  const HALF = { required_seconds: 3600, observed_seconds: 1800, source_count: 1, gaps: [{ from: "2026-10-23T09:30:00Z", to: "2026-10-23T10:00:00Z" }] };

  function envelope<C>(domain: string, status: string, cards: C, currentness = "CURRENT") {
    return {
      schema_version: "w4-02.mini.v1",
      domain,
      site: { code: SITE_ID, timezone: "Africa/Kampala" },
      window: { from: HOUR.from, to: HOUR.to, known_at: null, bounds: "[from,to)" },
      currentness: { state: currentness, job_state: "SETTLED", windows: [] },
      source_provenance: null,
      selected_source_provenance: { classification: "REGISTERED_SIMULATION", source_ids: [], evidence_ids: [] },
      pending_source_provenance: null,
      status,
      coverage: FULL,
      cards,
      rows: [],
      limitations: [],
      basis: null,
      links: { dispatch: null, evidence: null, financials: null, actions: null },
    };
  }
  const loaded = <T,>(value: T) => Promise.resolve({ status: "loaded" as const, value } as MiniRead<never>);
  const SERVICE = { delivered_load_kw: 12.5, interruptions_seen: null, critical_delivered_kw: null, unserved_kwh: null };
  const FUEL = { opening_l: null, deliveries_l: null, expected_use_l: { low: 0, high: 3.3 }, closing_l: null, residual_l: null };
  const RENEWABLE = { capability_kw: null, used_kw: null, headroom_kw: { low: 1, high: 2 }, eligible_days: 1, assessed_days: 1 };
  // q12 (q11-5 c): the selected local-noon window and its exactly matching assessed row.
  const NOON_WINDOW = { local_day: "2026-10-23", window_start: "2026-10-23T09:00:00Z", window_end: "2026-10-23T10:00:00Z", selection_id: 7 };
  const NOON_ROW = { day: "2026-10-23", from: "2026-10-23T09:00:00Z", to: "2026-10-23T10:00:00Z", decision: "ELIGIBLE",
    opportunity_kwh: { low: 1, high: 2 }, constraints: [], evidence_ids: [] };
  function renewableEnvelope(status = "SUPPORTED", cards: unknown = RENEWABLE, rows: unknown[] = [NOON_ROW]) {
    const base = envelope("renewable", status, cards);
    return { ...base, currentness: { ...base.currentness, windows: [NOON_WINDOW] }, rows };
  }

  function miniClient(over: Partial<Record<"service" | "fuel" | "renewable", () => Promise<MiniRead<never>>>> = {}) {
    const unavailable = () => Promise.resolve({ status: "unavailable" as const, message: null });
    return {
      getCapabilities: vi.fn(() => Promise.resolve({ status: "loaded" as const, value: [] })),
      getService: vi.fn(over.service ?? (() => loaded(envelope("service", "SUPPORTED", SERVICE)))),
      getFuel: vi.fn(over.fuel ?? (() => loaded(envelope("fuel", "UNKNOWN", FUEL)))),
      getRenewable: vi.fn(over.renewable ?? (() => loaded(renewableEnvelope()))),
      getBackup: vi.fn(unavailable),
    };
  }

  function renderMini(mini: MiniDepthClient) {
    const { client } = clientOf(() => summary("2026-10-23"));
    return render(
      <MemoryRouter initialEntries={[`/sites/${SITE_ID}?date=2026-10-23`]}>
        <App
          flags={featureFlagsWith(false)}
          siteDirectory={DIRECTORY}
          siteDetail={DETAIL}
          siteEvidence={evidenceClient({ status: "loaded", value: POPULATED_EVIDENCE })}
          siteOverview={client}
          siteFindingIndex={NO_INDEX}
          miniDepth={mini}
        />
      </MemoryRouter>,
    );
  }

  const card = (key: string) => document.querySelector(`[data-objective-card="${key}"]`) as HTMLElement;
  const value = (key: string) => card(key).querySelector(".v69-metric__value")?.textContent;
  const note = (key: string) => card(key).querySelector(".v69-metric__note")?.textContent ?? "";
  const detail = (key: string) => card(key).querySelector(`[data-objective-card-detail="${key}"]`)?.getAttribute("href") ?? null;

  it("keeps the five mock cards in order and reads Service, Fuel and Renewable with one shared cutoff", async () => {
    const mini = miniClient();
    renderMini(mini);
    await settledScreen();
    await screen.findByText("Delivered 12.5 kW");
    const keys = [...document.querySelectorAll("[data-objective-card]")].map((n) => n.getAttribute("data-objective-card"));
    expect(keys).toEqual(["service", "dispatch", "battery", "fuel", "renewable"]);
    expect(document.querySelector('[data-objective-card="backup"]')).toBeNull();
    expect(mini.getBackup).not.toHaveBeenCalled();
    expect(mini.getService).toHaveBeenCalledTimes(1);
    const [serviceSite, serviceWindow] = mini.getService.mock.calls[0] as unknown as [string, MiniWindowQuery];
    const [, fuelWindow] = mini.getFuel.mock.calls[0] as unknown as [string, MiniWindowQuery];
    const [, renewableWindow] = mini.getRenewable.mock.calls[0] as unknown as [string, MiniWindowQuery];
    expect(serviceSite).toBe(SITE_ID);
    expect({ from: serviceWindow.from, to: serviceWindow.to }).toEqual(HOUR);
    expect({ from: fuelWindow.from, to: fuelWindow.to }).toEqual(HOUR);
    expect({ from: renewableWindow.from, to: renewableWindow.to }).toEqual(DAY);
    expect(serviceWindow.known_at).not.toBeNull();
    expect(fuelWindow.known_at).toBe(serviceWindow.known_at);
    expect(renewableWindow.known_at).toBe(serviceWindow.known_at);

    expect(value("service")).toBe("Delivered 12.5 kW");
    expect(note("service")).toContain("Local 2026-10-23 12:00–13:00 · 60 of 60 min covered");
    expect(value("fuel")).toBe("Expected use 0–3.3 L");
    expect(note("fuel")).toContain("Inventory residual unavailable");
    expect(value("renewable")).toBe("Headroom 1–2 kW");
    expect(note("renewable")).toContain("Local 2026-10-23 · One selected day; recurrence not established");
    expect(value("battery")).toBe("Not available");
    expect(card("dispatch").getAttribute("data-objective-card-state")).toBe(summary("2026-10-23").assessment.state);
    const known = encodeURIComponent(serviceWindow.known_at as string);
    expect(detail("service")).toBe(
      `/sites/${SITE_ID}/performance/service?from=${encodeURIComponent(HOUR.from)}&to=${encodeURIComponent(HOUR.to)}&known_at=${known}`,
    );
    expect(detail("renewable")).toBe(
      `/sites/${SITE_ID}/performance/renewable?from=${encodeURIComponent(DAY.from)}&to=${encodeURIComponent(DAY.to)}&known_at=${known}`,
    );
    expect(card("fuel").textContent).toContain("View detail →");
  });

  it("shows Unknown for an unsettled answer and Unavailable without a link for a failed read, never zero", async () => {
    const mini = miniClient({
      service: () => loaded(envelope("service", "SUPPORTED", SERVICE, "STALE_SOURCE")),
      fuel: () => Promise.resolve({ status: "refused", httpStatus: 503, code: "MINI_STORE_UNAVAILABLE", message: null }),
      renewable: () => loaded(envelope("renewable", "LIMITED", RENEWABLE)),
    });
    renderMini(mini);
    await settledScreen();
    await screen.findByText(OVERVIEW_MINI_UNAVAILABLE, { exact: false });
    expect(value("service")).toBe("Unknown");
    expect(detail("service")).not.toBeNull();
    expect(value("renewable")).toBe("Unknown");
    expect(detail("renewable")).not.toBeNull();
    expect(value("fuel")).toBe("Unavailable");
    expect(note("fuel")).toBe(OVERVIEW_MINI_UNAVAILABLE);
    expect(detail("fuel")).toBeNull();
    for (const key of ["service", "fuel", "renewable"]) expect(value(key)).not.toMatch(/^0\b|Delivered 0/);
    expect(card("dispatch").getAttribute("data-objective-card-state")).toBe(summary("2026-10-23").assessment.state);
  });

  it("keeps a null value Unknown even when the read is SUPPORTED", async () => {
    const mini = miniClient({
      service: () => loaded(envelope("service", "SUPPORTED", { ...SERVICE, delivered_load_kw: null })),
      fuel: () => loaded(envelope("fuel", "LIMITED", { ...FUEL, expected_use_l: { low: 0, high: null } })),
      renewable: () => loaded(envelope("renewable", "SUPPORTED", { ...RENEWABLE, headroom_kw: null })),
    });
    renderMini(mini);
    await settledScreen();
    await screen.findAllByText("Unknown");
    expect([value("service"), value("fuel"), value("renewable")]).toEqual(["Unknown", "Unknown", "Unknown"]);
    expect(note("fuel")).toContain("Inventory residual unavailable");
  });

  it("q11-1: an unknown selected source withholds the positive headroom value", async () => {
    const mini = miniClient({
      renewable: () =>
        loaded({
          ...renewableEnvelope(),
          selected_source_provenance: { classification: "UNKNOWN", source_ids: [], evidence_ids: [] },
        }),
    });
    renderMini(mini);
    await settledScreen();
    await screen.findAllByText("Unknown");
    expect(value("renewable")).toBe("Unknown");
    expect(value("service")).toBe("Delivered 12.5 kW");
  });

  it("q12 (q11-5 b, c): a partial service hour and a one-day read without the matching noon row stay Unknown", async () => {
    const mini = miniClient({
      service: () => loaded({ ...envelope("service", "SUPPORTED", SERVICE), coverage: HALF }),
      renewable: () => loaded(renewableEnvelope("SUPPORTED", RENEWABLE, [])),
    });
    renderMini(mini);
    await settledScreen();
    await screen.findAllByText("Unknown");
    expect(value("service")).toBe("Unknown");
    expect(note("service")).toContain("30 of 60 min covered");
    expect(value("renewable")).toBe("Unknown");
    expect(value("fuel")).toBe("Expected use 0–3.3 L");
  });

  // Final review ruling 1 (H3): the strip names only the readable reads, in Service, Dispatch, Fuel, Renewable order.
  const stripText = () => document.querySelector("[data-overview-status]")?.textContent ?? "";
  const READS = (names: string) => `Reads on this Overview: ${names}. Each card shows what its selected period supports.`;

  it("H3: a numeric MINIGRID set names every read and states the mini-grid objective", async () => {
    renderMini(miniClient({ fuel: () => loaded(envelope("fuel", "SUPPORTED", FUEL)) }));
    await settledScreen();
    await screen.findByText("Delivered 12.5 kW");
    await screen.findByText("Headroom 1–2 kW");
    expect(stripText()).toContain(READS("Service, Dispatch, Fuel, Renewable"));
    expect(stripText()).not.toContain("dispatch only");
    expect(document.querySelector("[data-objective-statement]")?.textContent).toBe(MINIGRID_OBJECTIVE);
    expect(document.body.textContent).not.toContain("Objective: nothing here is a current answer.");
  });

  it("H3: a partial set lists only the readable reads; 409 and 503 are not readable", async () => {
    renderMini(
      miniClient({
        fuel: () => Promise.resolve({ status: "refused", httpStatus: 503, code: "MINI_STORE_UNAVAILABLE", message: null }),
        renewable: () => Promise.resolve({ status: "refused", httpStatus: 409, code: "MINI_NOT_SETTLED", message: null }),
      }),
    );
    await settledScreen();
    await screen.findByText("Delivered 12.5 kW");
    await screen.findAllByText(OVERVIEW_MINI_UNAVAILABLE, { exact: false });
    expect(stripText()).toContain(READS("Service, Dispatch"));
  });

  it("H3: an UNKNOWN read is listed while its card stays Unknown; malformed reads are not listed", async () => {
    renderMini(
      miniClient({
        service: () => loaded(envelope("service", "UNKNOWN", { ...SERVICE, delivered_load_kw: null })),
        fuel: () => Promise.resolve({ status: "unavailable", message: "malformed" }),
      }),
    );
    await settledScreen();
    await screen.findByText("Headroom 1–2 kW");
    expect(value("service")).toBe("Unknown");
    expect(stripText()).toContain(READS("Service, Dispatch, Renewable"));
  });

  it("H3: an empty readable set says no objective read is available", () => {
    expect(overviewReadsStrip({ service: false, dispatch: false, fuel: false, renewable: false })).toBe(
      "No objective read is available for this selection.",
    );
    expect(overviewReadsStrip({ service: false, dispatch: true, fuel: false, renewable: true })).toBe(READS("Dispatch, Renewable"));
  });

  it("H3: a non-MINIGRID Overview (no mini reads) keeps the dispatch-only strip and objective", async () => {
    const href = () => "/x";
    const links = { dispatchDay: href, finding: href, financials: href, assumption: href, evidenceRecord: href };
    render(
      <MemoryRouter>
        <SiteWindowOverview summary={summary("2026-10-23")} links={links} onSelectDay={() => undefined} />
      </MemoryRouter>,
    );
    await settledScreen();
    expect(stripText()).toContain("Assessed for this day: dispatch only · the other objectives have no read on this Overview");
    expect(document.querySelector("[data-objective-statement]")?.textContent).toContain("does not state an operating objective");
    expect(document.body.textContent).not.toContain("Reads on this Overview");
  });
});
