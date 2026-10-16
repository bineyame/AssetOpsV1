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
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
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
  it("shows the priced P01 amount with its demonstration label and exact links", async () => {
    const { client } = clientOf(() => summary());
    renderAt(`/sites/${SITE_ID}?date=2026-10-23`, client);
    await settledScreen();
    const card = moneyCard();
    expect(card.getAttribute("data-money-state")).toBe("PRICED");
    expect(within(card).getByText("0.00 to 15.82 USD")).toBeTruthy();
    expect(card.querySelector('[data-financials-demonstration="P01-power"]')).not.toBeNull();
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
    expect(within(moneyCard()).getByText("Source closed")).toBeTruthy();
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
    expect(document.querySelector('[data-freshness-state="UNASSESSED"]')?.textContent).toContain("Unknown");
    expect(document.querySelector('[data-assessment-state="UNKNOWN"]')?.textContent).toContain("Unknown");
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
    expect(document.querySelector('[data-freshness-state="FAILED"]')?.textContent).toContain("Failed");
    expect(document.querySelector('[data-assessment-state="FAILED"]')?.textContent).toContain("Reassessment failed");
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
});
