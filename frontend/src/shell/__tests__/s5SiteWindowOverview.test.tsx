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
import type {
  OverviewSelection,
  SiteOverviewClient,
  SiteWindowSummary,
  WindowMoney,
} from "../../sites/siteOverviewClient";
import { createSiteOverviewClient } from "../../sites/siteOverviewClient";
import { POPULATED_EVIDENCE, evidenceClient } from "../../sites/__tests__/evidenceFixtures";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import { MONEY_STATE_WORDS } from "../../sites/SiteWindowOverview";
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";

const SITE_ID = HYBRID_MINI_GRID_SITE.site_id;
const FID = "11111111-1111-4111-8111-111111111111";
const RID = "22222222-2222-4222-8222-222222222222";
const RID_NEW = "23232323-2323-4232-8232-232323232323";
const CID = "33333333-3333-4333-8333-333333333333";
const PRICE = "44444444-4444-4444-8444-444444444444";
const EVIDENCE = "55555555-5555-4555-8555-555555555555";
const WA = "66666666-6666-4666-8666-666666666666";
const INTERVAL = "77777777-7777-4777-8777-777777777777";

const DIRECTORY: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [] }) };
const DETAIL: SiteDetailClient = {
  getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }),
};

function LocationProbe() {
  const location = useLocation();
  return <output data-location>{`${location.pathname}${location.search}`}</output>;
}

function money(over: Partial<WindowMoney> = {}): WindowMoney {
  return {
    state: "PRICED",
    amount_low: "0.00",
    amount_high: "15.82",
    currency: "USD",
    model_version: "fuel-cost-1",
    finding_id: FID,
    finding_revision_id: RID,
    consequence_revision_id: CID,
    eligibility: {
      version: "lr01-1",
      state: "ELIGIBLE",
      note: "gate note",
      pending_reasons: [],
      series_limits: [],
      latest_finding_revision_id: RID,
      end_reason: null,
    },
    quantity_state: "BOUNDED",
    price_state: "PRICED",
    limitation: null,
    demonstration: {
      label: "Demonstration data",
      statement: "This Finding comes from an authored demonstration case.",
      case_id: "P01-power",
      spec: "s4-power-demo-cases-v1",
    },
    label: "fuel-cost-1 model-conditioned potential fuel-cost exposure: zero lower bound. Not savings.",
    upstream: { status: "CURRENT", stage: null, reasons: [] },
    links: {
      assumption_revisions: { [PRICE]: `/api/sites/KOBO-001/financial-assumptions/${PRICE}` },
      evidence_records: { [EVIDENCE]: `/api/sites/KOBO-001/evidence/records/${EVIDENCE}` },
      assessment_revisions: { [INTERVAL]: `/api/x/${INTERVAL}` },
    },
    ...over,
  };
}

function summary(day = "2026-10-23", over: Partial<SiteWindowSummary> = {}, m: Partial<WindowMoney> = {}): SiteWindowSummary {
  return {
    schema_version: "site-window-summary-1",
    site_id: "site-uuid",
    site_code: "KOBO-001",
    access_basis: "DEVELOPMENT_UNAUTHENTICATED",
    window: { start: `${day}T00:00:00Z`, end: `${day}T23:59:59Z`, utc_date: day, bounds: "[start, end)" },
    built_at: `${day}T12:00:00Z`,
    db_now: `${day}T12:00:00Z`,
    freshness: { state: "CURRENT", stage: null, reasons: [], errors: [], source_open: true, source_reason: "open" },
    watermarks: {
      accepted_source: { count: 3, sha256: "abc" },
      accepted_source_reason: null,
      analytic_selection_seq: 4,
      input_sha256: "def",
      configuration_sha256: "ghi",
      match_pass_id: "mp",
      matched_through_selection_seq: 4,
    },
    model_version: "dispatch-3.1",
    assessment: {
      state: "CURRENT",
      status: "CURRENT",
      status_reasons: [],
      run_id: "run-1",
      window_assessment_revision_id: WA,
      claim_level: "CANDIDATE_AVOIDABLE",
      limitations: [],
      coverage: null,
      dispatch_intervals: [
        {
          revision_id: INTERVAL,
          start: `${day}T06:00:00Z`,
          end: `${day}T08:00:00Z`,
          claim_level: "CANDIDATE_AVOIDABLE",
          assessment_key: "k",
          link: `/api/sites/KOBO-001/performance/dispatch/revisions/${INTERVAL}`,
        },
      ],
      links: {},
    },
    context: {
      series: [
        {
          evidence_id: EVIDENCE,
          time: `${day}T06:05:00Z`,
          interval: null,
          device_id: "GEN-1",
          signal_id: "P",
          role: "generator_power",
          value: "20",
          unit: "kW",
          quality: "GOOD",
          unavailable_reason: null,
        },
      ],
      total: 1,
      truncated: false,
      coverage: [
        {
          device_id: "GEN-1",
          signal_id: "P",
          role: "generator_power",
          unit: "kW",
          records: 1,
          good: 1,
          first_source_time: `${day}T06:05:00Z`,
          last_source_time: `${day}T06:05:00Z`,
        },
      ],
      gaps: null,
      gaps_reason: "No reviewed gap rule exists for the Site context.",
      evidence_links: {},
    },
    money: money(m),
    known_finding: {
      id: FID,
      revision_id: m.finding_revision_id ?? RID,
      selection_rule: "greatest episode_start, then smallest Finding UUID",
      selected_by: "DISCOVERED",
      episode: { start: `${day}T06:00:00Z`, end: `${day}T08:00:00Z` },
      audit_only: false,
      several_intersect: false,
      note: "This card covers this Finding only; it is not a Site total.",
      excluded: [],
      previous_pin: null,
      link: { page: "", api: "" },
    },
    finding_list: { state: "UNAVAILABLE", reason: "Unavailable until the Site Finding index is delivered." },
    ...over,
  };
}

function clientOf(answer: (selection: OverviewSelection) => SiteWindowSummary) {
  const getOverview = vi.fn((_site: string, _w: unknown, selection: OverviewSelection = {}) =>
    Promise.resolve({ status: "loaded" as const, value: answer(selection) }),
  );
  return { client: { getOverview } as unknown as SiteOverviewClient, getOverview };
}

function renderAt(path: string, overview: SiteOverviewClient) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={featureFlagsWith(false)}
        siteDirectory={DIRECTORY}
        siteDetail={DETAIL}
        siteEvidence={evidenceClient({ status: "loaded", value: POPULATED_EVIDENCE })}
        siteOverview={overview}
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
    fireEvent.click(screen.getByRole("button", { name: "Next day" }));
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
  it("an unassessed day reads Unknown and the Finding list is unavailable, never empty", async () => {
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
    expect(document.querySelector('[data-finding-list="UNAVAILABLE"]')?.textContent).toBe(
      "Unavailable until the Site Finding index is delivered.",
    );
    expect(document.body.textContent).not.toMatch(/no findings/i);
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
