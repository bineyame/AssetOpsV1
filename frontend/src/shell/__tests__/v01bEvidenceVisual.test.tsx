import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import type { SiteEvidenceClient } from "../../sites/siteEvidenceClient";
import { EMPTY_ANALYTICS_CLIENT } from "../../sites/__tests__/analyticsFixtures";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import {
  EVIDENCE_UUID,
  GATEWAY_HEALTH,
  LEDGER_EVIDENCE,
  LEDGER_RECORD,
  LEDGER_REJECTIONS,
  ledgerClient,
  ledgerEvidence,
} from "../../sites/__tests__/ledgerEvidenceFixtures";
import { describeViolations, scanDisclosureVocabulary, scanProductVocabulary } from "../../test/productVocabulary";
import { expectStateLineVisible } from "../../test/productPresentation";
import { settledScreen } from "../../test/settled";

/**
 * V-01b phase b1: Site Evidence (ledger path) follows the v6.9 mock's hierarchy.
 * Overview: a status bar of window facts with a neutral badge, "What we can
 * conclude now", a two-column Data sources / Most useful next evidence row and
 * a closing notice. Analysis: accepted records behind the conclusions, how each
 * limit is set (the mock's "claim" is banned product vocabulary) and the long
 * technical panels behind Advanced details.
 * Every mock fact without a data source is a visible "Not available yet"
 * statement, never a mock value.
 */

const SITE_ID = HYBRID_MINI_GRID_SITE.site_id;
const WINDOW = "from=2026-09-22T00:00:00Z&to=2026-09-23T00:00:00Z";
const EVIDENCE_URL = `/sites/${SITE_ID}/evidence?${WINDOW}`;
const ANALYSIS_URL = `${EVIDENCE_URL}&view=analysis`;

const DIRECTORY: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [] }) };
const DETAIL: SiteDetailClient = {
  getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }),
};

const SILENT_SOURCE = {
  ...LEDGER_EVIDENCE.sources[0],
  source_id: "aaaa0000-0000-4000-8000-000000000002",
  external_id: "fuel-level-sensor",
  accepted_in_window: 0,
  duplicates_in_window: 0,
  conflicts_in_window: 0,
  rejected_in_window: 0,
  last_source_time: null,
  last_published_at: null,
  last_received_at: null,
};
const TWO_SOURCES = ledgerEvidence({ sources: [LEDGER_EVIDENCE.sources[0], SILENT_SOURCE] });

const CONFLICT_ID = "dddd0000-0000-4000-8000-00000000000c";
const WITH_CONFLICT = {
  ...LEDGER_REJECTIONS,
  rejections: [
    ...LEDGER_REJECTIONS.rejections,
    {
      ...LEDGER_REJECTIONS.rejections[0],
      rejection_id: CONFLICT_ID,
      message_id: "msg-0001",
      kind: "MESSAGE_CONFLICT",
      detail: "message_id already accepted with different contents",
      source_time: "2026-09-22T09:00:00Z",
      conflicts_with_evidence_id: EVIDENCE_UUID,
      conflicts_with_source_time: "2026-09-22T08:00:00Z",
    },
  ],
};

function LocationProbe() {
  const location = useLocation();
  return <output data-location>{`${location.pathname}${location.search}`}</output>;
}

function renderAt(path: string, evidence: SiteEvidenceClient) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={featureFlagsWith(false)}
        siteDirectory={DIRECTORY}
        siteDetail={DETAIL}
        siteEvidence={evidence}
        siteAnalytics={EMPTY_ANALYTICS_CLIENT}
      />
      <LocationProbe />
    </MemoryRouter>,
  );
}

function panel(heading: string): HTMLElement {
  return screen.getByRole("heading", { name: heading }).closest("section") as HTMLElement;
}

function loc(): string {
  return document.querySelector("[data-location]")?.textContent ?? "";
}

afterEach(() => {
  cleanup();
});

describe("V-01b Site Evidence overview", () => {
  it("leads with a status bar of window facts and a neutral no-conclusion badge", async () => {
    renderAt(EVIDENCE_URL, ledgerClient({ status: "loaded", value: TWO_SOURCES }));
    await settledScreen();
    const bar = document.querySelector("[data-evidence-statusbar='overview']") as HTMLElement;
    expect(bar).not.toBeNull();
    expect(bar.querySelector(".badge--neutral")?.textContent).toBe("No capability conclusion yet");
    expect(bar.textContent).toContain("288 readings accepted · 1 of 2 sources with accepted readings · 3 not accepted");
    expect(document.body.textContent).not.toMatch(/Evidence limited|\bscore\b/i);
    const analysis = within(bar).getByRole("link", { name: "Analysis →" });
    expect(analysis.getAttribute("href")).toContain("view=analysis");
    expect(analysis.getAttribute("href")).toContain("from=2026-09-22");
  });

  it("titles the panels as the mock does and states each missing capability fact plainly", async () => {
    renderAt(EVIDENCE_URL, ledgerClient({ status: "loaded", value: TWO_SOURCES }));
    await settledScreen();
    const conclude = panel("What we can conclude now");
    expect(conclude.querySelector(".panel__description")?.textContent).toBe("Evidence readiness is not equipment condition");
    expect(conclude.textContent).toMatch(/288 readings were accepted for this period from 1 source\./);
    // W1-UX-01: the outcome counts are the card's small visual, one labelled bar per outcome, in order.
    const outcomes = Array.from(conclude.querySelectorAll("[data-value-bars] [data-value-bar-key]"));
    expect(outcomes.map((o) => o.getAttribute("data-value-bar-key"))).toEqual(["accepted", "duplicates", "rejected", "conflicts"]);
    expect(outcomes.map((o) => o.querySelector(".value-bars__value")?.textContent)).toEqual(["288", "3", "2", "1"]);
    expect(conclude.querySelector("[data-evidence-limits]")?.textContent).toMatch(/draws no conclusion/);
    expect(conclude.querySelector("[data-not-available='capability-conclusions']")?.textContent).toBe(
      "Not available yet: capability-by-capability conclusions (what can be said, what is missing and the next step for each). They need a reviewed capability assessment over accepted Evidence, which does not exist yet.",
    );
    // No mock capability rows are rendered as data.
    expect(document.body.textContent).not.toMatch(/Generator support|Battery condition|Fuel balance|Backup readiness/);

    const sources = panel("Data sources · data quality, not equipment condition");
    expect(sources.querySelector("[data-not-available='source-judgements']")?.textContent).toBe(
      "Not available yet: a status at the end of the period, a quality grade and which conclusions each source affects. No reviewed rule sets these.",
    );
    const next = panel("Most useful next evidence");
    expect(next.querySelector("[data-not-available='next-evidence']")?.textContent).toBe(
      "Not available yet: ranking the next evidence needs a reviewed rule linking missing readings to conclusions.",
    );
  });

  it("lists sources in a compact table beside the next-evidence panel, naming a silent source plainly", async () => {
    renderAt(EVIDENCE_URL, ledgerClient({ status: "loaded", value: TWO_SOURCES }));
    await settledScreen();
    const pair = document.querySelector(".evidence-pair") as HTMLElement;
    expect(pair).not.toBeNull();
    const sources = panel("Data sources · data quality, not equipment condition");
    expect(pair.contains(sources)).toBe(true);
    expect(pair.contains(panel("Most useful next evidence"))).toBe(true);
    const heads = Array.from(sources.querySelectorAll("thead th")).map((th) => th.textContent);
    expect(heads).toEqual(["Source", "Accepted in period", "Latest taken", "Latest received", "Readings"]);
    const silent = sources.querySelector(`[data-evidence-source='${SILENT_SOURCE.source_id}']`) as HTMLElement;
    expect(silent.textContent).toContain("No accepted reading in this period");
    // The gateway's central contact is a compact block inside the sources panel.
    const contact = sources.querySelector("[data-gateway-contact='CURRENT']") as HTMLElement;
    expect(contact.textContent).toMatch(/in contact\. Last report received/);
    expect(sources.textContent).toMatch(/says nothing about the\s+condition of the equipment/);

    const next = panel("Most useful next evidence");
    const silentList = next.querySelector("[data-evidence-silent-sources]") as HTMLElement;
    expect(silentList.textContent).toContain("fuel-level-sensor");
    expect(silentList.textContent).not.toContain("kobo-inverter-1");
    expect(next.textContent).toMatch(/a fact, not a recommendation/);
  });

  it("closes with a notice linking to Evidence › Analysis", async () => {
    renderAt(EVIDENCE_URL, ledgerClient({ status: "loaded", value: LEDGER_EVIDENCE }));
    await settledScreen();
    const notice = document.querySelector("[data-evidence-closing-notice]") as HTMLElement;
    expect(notice.textContent).toBe("Record-level detail, timing and how each limit is set are on Evidence › Analysis.");
    const link = within(notice).getByRole("link", { name: "Evidence › Analysis" });
    expect(link.getAttribute("href")).toContain("view=analysis");
  });

  it("uses no implementation vocabulary", async () => {
    renderAt(EVIDENCE_URL, ledgerClient({ status: "loaded", value: TWO_SOURCES }));
    await settledScreen();
    expect(scanProductVocabulary(document.body, EVIDENCE_URL).violations).toEqual([]);
  });

  it("W1-UX-01: the Evidence overview uses the W1 set, its disclosure the narrower list, and the state line stays visible", async () => {
    renderAt(EVIDENCE_URL, ledgerClient({ status: "loaded", value: TWO_SOURCES }));
    await settledScreen();
    const main = document.querySelector("main") as HTMLElement;
    const w1 = scanProductVocabulary(main, `${EVIDENCE_URL} (W1)`, { set: "w1" });
    expect(w1.scanned).toBeGreaterThan(10);
    expect(describeViolations(w1.violations)).toBe("");
    const card = document.querySelector("[data-headline-card='evidence-conclusion']") as HTMLElement;
    const disclosure = scanDisclosureVocabulary(card, "evidence conclusion disclosure");
    expect(disclosure.disclosures).toBe(1);
    expect(disclosure.scanned).toBeGreaterThan(2);
    expect(describeViolations(disclosure.violations)).toBe("");
    expect(expectStateLineVisible(card)).toBe("Readings received and accepted");
    // The destination keeps the selected period.
    const link = card.querySelector("[data-evidence-analysis-link]") as HTMLElement;
    expect(link.getAttribute("href")).toContain("view=analysis");
    expect(link.getAttribute("href")).toContain("from=2026-09-22");
  });
});

describe("V-01b Site Evidence analysis", () => {
  it("shows accepted records behind the conclusions and how each limit is set", async () => {
    const client = ledgerClient({ status: "loaded", value: LEDGER_EVIDENCE });
    renderAt(ANALYSIS_URL, client);
    await settledScreen();
    const bar = document.querySelector("[data-evidence-statusbar='analysis']") as HTMLElement;
    expect(bar.querySelector(".badge")?.textContent).toBe("Evidence · Analysis");
    expect(bar.textContent).toContain("Accepted records, timing and how each limit is set");

    const records = panel("Accepted records behind the conclusions");
    expect(records.querySelector(".panel__description")?.textContent).toBe("Measured time is kept even when a report arrives late");
    // Read for the whole site in the selected window when no source is chosen.
    expect(client.recordQueries.at(-1)).toMatchObject({ source: null, device: null, signal: null, cursor: null, limit: 10 });
    const heads = Array.from(records.querySelectorAll("thead th")).map((th) => th.textContent);
    expect(heads).toEqual(["Source · reading", "Value", "Taken", "Sent", "Received", "Record"]);
    expect(within(records).getByRole("button", { name: `Open record ${EVIDENCE_UUID}` })).toBeTruthy();

    const limit = panel("How each limit is set");
    expect(limit.textContent).toContain("Data-source status describes reporting, not equipment condition");
    expect(limit.querySelector("[data-not-available='claim-limit-rule']")?.textContent).toBe(
      "Not available yet: the rule that turns accepted readings into a positive capability conclusion and sets its limit (a later capability assessment).",
    );
  });

  it("keeps the technical panels behind closed Advanced details disclosures", async () => {
    renderAt(ANALYSIS_URL, ledgerClient({ status: "loaded", value: LEDGER_EVIDENCE }));
    await settledScreen();
    const expected: [string, string][] = [
      ["evidence-clocks", "[data-evidence-clocks]"],
      ["evidence-sources", "[data-evidence-source-row]"],
      ["evidence-deliveries", "[data-evidence-delivery]"],
      ["evidence-coverage", "[data-evidence-coverage]"],
      ["evidence-analysis-status", "[data-evidence-analysis-status]"],
      ["evidence-comparison", "[data-evidence-migration]"],
      ["evidence-gateway", "[data-gateway-contact='CURRENT']"],
      ["evidence-not-accepted", "[data-evidence-rejection]"],
    ];
    for (const [name, inner] of expected) {
      const details = document.querySelector(`details[data-disclosure='${name}']`) as HTMLDetailsElement;
      expect(details, name).not.toBeNull();
      expect(details.open, name).toBe(false);
      expect(details.querySelector("summary")?.textContent, name).toMatch(/^Advanced details — /);
      expect(details.querySelector(inner), name).not.toBeNull();
    }
    // The not-accepted count stays visible outside its disclosure.
    const visible = document.querySelector("[data-evidence-not-accepted-line]") as HTMLElement;
    expect(visible.closest("details")).toBeNull();
    expect(visible.textContent).toMatch(/3 readings in this period were not accepted/);
  });

  it("shows a conflicting reading beside the original reading's taken time and opens it", async () => {
    renderAt(ANALYSIS_URL, ledgerClient({ status: "loaded", value: LEDGER_EVIDENCE }, { rejections: { status: "loaded", value: WITH_CONFLICT } }));
    await settledScreen();
    const row = document.querySelector(`[data-evidence-rejection='${CONFLICT_ID}']`) as HTMLElement;
    const original = row.querySelector("[data-conflict-original]") as HTMLElement;
    expect(original.textContent).toContain("Original reading taken 22 Sep 2026 08:00 UTC");
    fireEvent.click(within(original).getByRole("button", { name: `reading ${EVIDENCE_UUID}` }));
    await settledScreen();
    expect(loc()).toContain(`record=${EVIDENCE_UUID}`);
  });

  it("opens a record from the accepted records table to its exact message as received", async () => {
    const client = ledgerClient({ status: "loaded", value: LEDGER_EVIDENCE });
    renderAt(ANALYSIS_URL, client);
    await settledScreen();
    fireEvent.click(screen.getByRole("button", { name: `Open record ${EVIDENCE_UUID}` }));
    await settledScreen();
    expect(client.recordKeys.at(-1)).toBe(EVIDENCE_UUID);
    const detail = document.querySelector(`[data-record-detail='${EVIDENCE_UUID}']`) as HTMLElement;
    expect(detail.textContent).toContain("Exact message as received");
    expect(detail.querySelector("[data-record-message]")?.textContent).toBe(LEDGER_RECORD.envelope.text);
  });

  it("W1-UX-03: readings, gateway contact and analysis are three separate facts; a fresh contact never makes analysis current", async () => {
    const stale = { ...TWO_SOURCES, projection: { ...TWO_SOURCES.projection, status: "STALE", pending_jobs: 2, failed_jobs: 0 } };
    renderAt(EVIDENCE_URL, ledgerClient({ status: "loaded", value: stale }));
    await settledScreen();
    const facts = document.querySelector("[data-evidence-reporting-facts]") as HTMLElement;
    const fact = (key: string) => facts.querySelector(`[data-evidence-reporting-fact='${key}']`) as HTMLElement;
    expect(fact("readings").dataset.factTone).toBe("known");
    expect(fact("contact").dataset.factTone).toBe("known");
    expect(fact("analysis").dataset.factTone).toBe("waiting");
    expect(fact("analysis").textContent).toMatch(/do not yet include the newest readings/);
    expect(document.querySelector("[data-evidence-reporting-note]")?.textContent).toMatch(/do not make the analysis up\s+to date\. As of \d/);
    // The per-source strip: a source with accepted readings has a "latest taken" mark; a silent one has none and says so.
    const strip = document.querySelector("[data-period-strip='evidence-sources']") as HTMLElement;
    const rows = Array.from(strip.querySelectorAll<HTMLElement>("[data-period-strip-row]"));
    expect(rows).toHaveLength(2);
    const silent = rows.find((r) => /No accepted reading in this period/.test(r.textContent ?? "")) as HTMLElement;
    expect(silent.querySelector("[data-period-strip-segment]")).toBeNull();
    const reporting = rows.find((r) => r !== silent) as HTMLElement;
    expect(reporting.querySelector("[data-period-strip-segment='marker']")).not.toBeNull();
    expect(reporting.textContent).toMatch(/288 readings accepted; latest taken/);
  });

  it("W1-UX-03: unknown analysis and contact states stay 'Not known', never positive", async () => {
    const odd = { ...TWO_SOURCES, projection: { ...TWO_SOURCES.projection, status: "SOMETHING_NEW", failed_jobs: 0 } };
    renderAt(EVIDENCE_URL, ledgerClient({ status: "loaded", value: odd }));
    await settledScreen();
    const analysis = document.querySelector("[data-evidence-reporting-fact='analysis']") as HTMLElement;
    expect(analysis.dataset.factTone).toBe("not-known");
    expect(analysis.textContent).not.toContain("SOMETHING_NEW");
  });

  it("W1-UX-03 fix round 1 (F3): one gateway in contact and one not known reads as a mixed state, never 'no report received'", async () => {
    const [first] = GATEWAY_HEALTH.gateways;
    const mixed = {
      ...GATEWAY_HEALTH,
      gateways: [first, { ...first, gateway_id: "bbbb0000-0000-4000-8000-000000000002", gateway_external_id: "kobo-gw-2", status: "UNKNOWN", last_server_contact: null }],
    };
    renderAt(EVIDENCE_URL, ledgerClient({ status: "loaded", value: TWO_SOURCES }, { health: { status: "loaded", value: mixed } }));
    await settledScreen();
    const contact = document.querySelector("[data-evidence-reporting-fact='contact']") as HTMLElement;
    expect(contact.dataset.factTone).toBe("not-known");
    expect(contact.textContent).toContain("Some gateways are in contact; the others' contact is not known.");
    expect(contact.textContent).not.toMatch(/No gateway report has been received/);
    expect(contact.textContent).not.toMatch(/Every gateway is in contact/);
  });

  it("W1-UX-03: the Evidence Analysis view uses the W1 set", async () => {
    renderAt(ANALYSIS_URL, ledgerClient({ status: "loaded", value: LEDGER_EVIDENCE }, { rejections: { status: "loaded", value: WITH_CONFLICT } }));
    await settledScreen();
    const main = document.querySelector("main") as HTMLElement;
    const w1 = scanProductVocabulary(main, `${ANALYSIS_URL} (W1)`, { set: "w1" });
    expect(w1.scanned).toBeGreaterThan(10);
    expect(describeViolations(w1.violations)).toBe("");
    expect(main.querySelector("[data-evidence-analysis-question]")?.textContent).toMatch(/Which accepted readings sit behind/);
  });

  it("uses no implementation vocabulary", async () => {
    renderAt(ANALYSIS_URL, ledgerClient({ status: "loaded", value: LEDGER_EVIDENCE }, { rejections: { status: "loaded", value: WITH_CONFLICT } }));
    await settledScreen();
    expect(scanProductVocabulary(document.body, ANALYSIS_URL).violations).toEqual([]);
  });
});
