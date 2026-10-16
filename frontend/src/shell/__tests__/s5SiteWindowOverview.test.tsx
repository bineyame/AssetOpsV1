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
import { MONEY_STATE_WORDS } from "../../sites/SiteWindowOverview";
import { describeViolations, scanDisclosureVocabulary, scanProductVocabulary } from "../../test/productVocabulary";
import { expectStateLineVisible } from "../../test/productPresentation";
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
    expect(document.querySelector("[data-objective-statement]")?.textContent).toContain("does not state an operating objective");
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
    expect(document.querySelector('[data-freshness-state="FAILED"]')?.textContent).toContain("The latest check could not be completed");
    expect(expectStateLineVisible(freshnessCard())).toBe("The latest check could not be completed");
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
    const disclosure = scanDisclosureVocabulary(objectiveCard(), "overview objective disclosure");
    expect(disclosure.disclosures).toBe(1);
    expect(disclosure.scanned).toBeGreaterThan(2);
    expect(disclosure.violations, describeViolations(disclosure.violations)).toEqual([]);
    expect(expectStateLineVisible(objectiveCard())).toBe("Using the latest checked readings");
    expect(objectiveCard().querySelector("[data-product-status-as-of]")?.textContent).toMatch(/^As of \d{1,2} \w{3} \d{4}, \d{2}:\d{2} UTC$/);
  });
});

function objectiveCard(): HTMLElement {
  return document.querySelector('[data-headline-card="overview-objective"]') as HTMLElement;
}

function freshnessCard(): HTMLElement {
  return document.querySelector("[data-freshness-card]") as HTMLElement;
}

describe("W1-UX-02: the selected-day Overview (mini) on the W1 set", () => {
  it("leads with the day answer; the whole route, every exact-reference disclosure and each state line pass", async () => {
    const { client } = clientOf(() => summary());
    const { container } = renderAt(`/sites/${SITE_ID}?date=2026-10-23`, client);
    await settledScreen();
    const main = container.querySelector("main") as HTMLElement;
    // The day answer leads: the objective card is the first card under the day selector.
    const firstCard = main.querySelector("[data-headline-card]");
    expect(firstCard?.getAttribute("data-headline-card")).toBe("overview-objective");
    expect(within(objectiveCard()).getByText("Is the mini-grid meeting its operating objective?")).toBeTruthy();
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
    expect(expectStateLineVisible(freshnessCard())).toBe("Using the latest checked readings");
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
    expect(expectStateLineVisible(freshnessCard())).toBe("This result may miss newer readings");
    expect(expectStateLineVisible(moneyCard())).toBe("Upstream out of date");
    expect(expectStateLineVisible(objectiveCard())).toBe("This result may miss newer readings");
    expect(objectiveCard().querySelector(".headline-card__headline")?.textContent).toBe("No current answer for this day");
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
    expect(expectStateLineVisible(freshnessCard())).toBe("Not checked yet");
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
    expect(expectStateLineVisible(freshnessCard())).toBe("The latest check could not be completed");
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
