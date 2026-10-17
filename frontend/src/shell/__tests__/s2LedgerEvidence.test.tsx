import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { createSiteEvidenceClient, type SiteEvidenceClient } from "../../sites/siteEvidenceClient";
import { EMPTY_ANALYTICS_CLIENT } from "../../sites/__tests__/analyticsFixtures";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import {
  EVIDENCE_UUID,
  GATEWAY_HEALTH,
  LEDGER_EVIDENCE,
  LEDGER_RECORD,
  ledgerClient,
  ledgerEvidence,
} from "../../sites/__tests__/ledgerEvidenceFixtures";
import { scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";
import { expectStateLineVisible } from "../../test/productPresentation";

/**
 * S2-02 phase 3b: Site Evidence for an imported Site read from the central
 * ledger. Overview stays plain; Analysis carries clocks, deliveries, refused
 * readings and the reading detail (as reported, converted, receipt, exact
 * message). The gateway contact is CURRENT/STALE/UNKNOWN from the server's own
 * receive time and is never a reading or equipment health.
 */

const SITE_ID = HYBRID_MINI_GRID_SITE.site_id;
const EVIDENCE_URL = `/sites/${SITE_ID}/evidence`;
const ANALYSIS_URL = `${EVIDENCE_URL}?view=analysis`;

const DIRECTORY: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [] }) };
const DETAIL: SiteDetailClient = {
  getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }),
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

function body(): HTMLElement {
  return document.querySelector("[data-evidence-store='POSTGRES']") as HTMLElement;
}

function loc(): string {
  return document.querySelector("[data-location]")?.textContent ?? "";
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("Site Evidence from the central ledger: overview", () => {
  it("states what arrived, counts the outcomes and shows the gateway contact in plain words", async () => {
    renderAt(EVIDENCE_URL, ledgerClient({ status: "loaded", value: LEDGER_EVIDENCE }));
    await settledScreen();
    expect(body().getAttribute("data-evidence-state")).toBe("ACCEPTED");
    expect(screen.getByText(/288 readings were accepted for this period from 1 source\./)).toBeTruthy();
    const outcomes = document.querySelectorAll("[data-evidence-conclusion] [data-value-bar-key]");
    expect(Array.from(outcomes).map((row) => row.getAttribute("data-value-bar-key"))).toEqual([
      "accepted",
      "duplicates",
      "rejected",
      "conflicts",
    ]);
    const contact = document.querySelector("[data-gateway-contact='CURRENT']") as HTMLElement;
    expect(contact.textContent).toMatch(/in contact\. Last report received/);
    expect(contact.textContent).toMatch(/expected to report every 60 seconds/);
    expect(screen.getByText(/says nothing about the\s+condition of the equipment/)).toBeTruthy();
    // Empty-set comparison: nothing carried over, never "matched".
    const migration = document.querySelector("[data-evidence-migration]") as HTMLElement;
    expect(migration.getAttribute("data-evidence-migration")).toBe("empty_set");
    expect(migration.textContent).toMatch(/held no readings for this site, so none were carried over/);
    expect(document.body.textContent).not.toMatch(/matched/i);
    expect(document.querySelector("[data-evidence-limits]")?.textContent).toMatch(/draws no conclusion/);
  });

  it.each([
    ["NO_DATA", ["NO_DATA"], /No readings were received for this period\./],
    ["REJECTED_ONLY", ["REJECTED_ONLY"], /none could be accepted/],
  ] as const)("names the %s state", async (state, states, text) => {
    renderAt(
      EVIDENCE_URL,
      ledgerClient({
        status: "loaded",
        value: ledgerEvidence({ state, states: [...states], counts: { ...LEDGER_EVIDENCE.counts, accepted: 0 } }),
      }),
    );
    await settledScreen();
    expect(body().getAttribute("data-evidence-state")).toBe(state);
    expect(screen.getByText(text)).toBeTruthy();
    // W1-UX-01: the state line, scope and as-of stay outside the closed exact-reference disclosure.
    const card = document.querySelector("[data-evidence-conclusion]") as HTMLElement;
    expect(expectStateLineVisible(card)).toBe(
      state === "NO_DATA" ? "No readings received for this period" : "Readings arrived, but none were accepted",
    );
    expect(card.querySelector("[data-product-status]")?.getAttribute("data-product-status")).not.toBe("positive");
  });

  it("an unrecognised state reads as not judged, never as accepted", async () => {
    renderAt(
      EVIDENCE_URL,
      ledgerClient({
        status: "loaded",
        value: ledgerEvidence({ state: "SOMETHING_NEW" as never, states: ["SOMETHING_NEW" as never] }),
      }),
    );
    await settledScreen();
    const card = document.querySelector("[data-evidence-conclusion]") as HTMLElement;
    expect(expectStateLineVisible(card)).toBe("We cannot judge this yet");
    expect(card.querySelector("[data-product-status]")?.getAttribute("data-product-status")).toBe("limited");
    expect(card.querySelector("[data-product-status]")?.textContent ?? "").not.toMatch(/accepted/i);
  });

  it("notes partial, conflicting and outdated-configuration evidence", async () => {
    renderAt(
      EVIDENCE_URL,
      ledgerClient({
        status: "loaded",
        value: ledgerEvidence({ states: ["ACCEPTED", "PARTIAL_BATCH", "CONFLICTING", "OUTDATED_CONFIGURATION"] }),
      }),
    );
    await settledScreen();
    const notes = Array.from(document.querySelectorAll("[data-evidence-note]")).map((n) => n.getAttribute("data-evidence-note"));
    expect(notes).toEqual(["PARTIAL_BATCH", "CONFLICTING", "OUTDATED_CONFIGURATION"]);
    expect(screen.getByText(/still being processed, so the counts for this period may still grow/)).toBeTruthy();
  });

  it.each([
    ["STALE", { status: "loaded", value: { ...GATEWAY_HEALTH, gateways: [{ ...GATEWAY_HEALTH.gateways[0], status: "STALE" }] } }, /not heard from recently/],
    ["UNKNOWN", { status: "loaded", value: { ...GATEWAY_HEALTH, gateways: [{ ...GATEWAY_HEALTH.gateways[0], status: "UNKNOWN", last_server_contact: null }] } }, /no report has been received yet/],
    ["unavailable", { status: "unavailable", message: null }, /whether the gateway is in touch is not known/],
    ["none", { status: "not_found" }, /No gateway is registered for this site/],
  ] as const)("shows a %s gateway contact honestly", async (state, health, text) => {
    renderAt(EVIDENCE_URL, ledgerClient({ status: "loaded", value: LEDGER_EVIDENCE }, { health: health as never }));
    await settledScreen();
    expect(document.querySelector(`[data-gateway-contact='${state}']`)?.textContent).toMatch(text);
  });

  it("keeps the awaiting-migration state when the comparison does not permit the switch", async () => {
    renderAt(
      EVIDENCE_URL,
      ledgerClient({ status: "unavailable", message: "awaiting", transition: "AWAITING_EVIDENCE_MIGRATION" } as never),
    );
    await settledScreen();
    expect(document.querySelector("[data-evidence-state='awaiting_migration']")).not.toBeNull();
    expect(document.querySelector("[data-evidence-store]")).toBeNull();
  });

  it("writes a chosen period into the address as a half-open UTC window", async () => {
    renderAt(EVIDENCE_URL, ledgerClient({ status: "loaded", value: LEDGER_EVIDENCE }));
    await settledScreen();
    fireEvent.change(screen.getByLabelText(/From \(UTC\)/), { target: { value: "2026-09-22T08:00" } });
    fireEvent.change(screen.getByLabelText(/To \(UTC\)/), { target: { value: "2026-09-22T09:00" } });
    fireEvent.click(screen.getByRole("button", { name: "Show this period" }));
    await settledScreen();
    expect(loc()).toContain("from=2026-09-22T08%3A00%3A00Z");
    expect(loc()).toContain("to=2026-09-22T09%3A00%3A00Z");
    expect(screen.getAllByText(/up to but not including the end time/).length).toBeGreaterThan(0);
  });
});

describe("Site Evidence from the central ledger: analysis", () => {
  it("separates analysis status from evidence freshness and draws no conclusion", async () => {
    renderAt(
      ANALYSIS_URL,
      ledgerClient({
        status: "loaded",
        value: ledgerEvidence({
          states: ["ACCEPTED", "STALE_PROJECTION"],
          projection: { ...LEDGER_EVIDENCE.projection, status: "STALE", pending_jobs: 2, oldest_job_created_at: "2026-10-09T09:00:00.000001Z" },
        }),
      }),
    );
    await settledScreen();
    const status = document.querySelector("[data-evidence-analysis-status]") as HTMLElement;
    expect(status.getAttribute("data-evidence-analysis-status")).toBe("STALE");
    expect(status.textContent).toMatch(/do not yet include the newest readings: 2 updates are waiting/);
    expect(screen.getByText(/not whether readings are arriving/)).toBeTruthy();
    expect(document.body.textContent).not.toMatch(/healthy|dispatch/i);
  });

  it("names the clocks and lists refused readings, including those with no readable time", async () => {
    renderAt(ANALYSIS_URL, ledgerClient({ status: "loaded", value: LEDGER_EVIDENCE }));
    await settledScreen();
    expect(document.querySelector("[data-evidence-clocks]")?.textContent).toMatch(/server clock \(UTC\)/);
    expect(screen.getByText(/the gap between a taken and a\s+received time is not a delivery delay/)).toBeTruthy();
    const untimed = document.querySelector("[data-evidence-untimed]") as HTMLElement;
    expect(untimed.getAttribute("data-evidence-untimed")).toBe("1");
    expect(untimed.textContent).toMatch(/operational audit record/);
    expect(document.querySelector("[data-evidence-rejection]")?.textContent).toMatch(/No readable time/);
    expect(document.querySelector("[data-evidence-delivery='batch-0001']")?.getAttribute("data-delivery-partial")).toBe("false");
  });

  it("reports the untimed count as unavailable, not zero, when the server omits it", async () => {
    const counts = { ...LEDGER_EVIDENCE.counts } as Record<string, number>;
    delete counts.rejected_without_source_time;
    renderAt(ANALYSIS_URL, ledgerClient({ status: "loaded", value: ledgerEvidence({ counts: counts as never }) }));
    await settledScreen();
    expect(document.querySelector("[data-evidence-untimed]")?.getAttribute("data-evidence-untimed")).toBe("unavailable");
  });

  it("pages readings by cursor and opens one reading's full lineage by its evidence id", async () => {
    const client = ledgerClient({ status: "loaded", value: LEDGER_EVIDENCE });
    renderAt(`${ANALYSIS_URL}&source=${LEDGER_EVIDENCE.sources[0].source_id}`, client);
    await settledScreen();
    expect(client.recordQueries.at(-1)).toMatchObject({
      source: LEDGER_EVIDENCE.sources[0].source_id,
      from: LEDGER_EVIDENCE.window.start,
      to: LEDGER_EVIDENCE.window.end,
      cursor: null,
    });
    fireEvent.click(screen.getByRole("button", { name: "Next page" }));
    await settledScreen();
    expect(client.recordQueries.at(-1)?.cursor).toMatch(/~/);

    fireEvent.click(screen.getByRole("button", { name: `Open record ${EVIDENCE_UUID}` }));
    await settledScreen();
    expect(client.recordKeys.at(-1)).toBe(EVIDENCE_UUID);
    const detail = document.querySelector(`[data-record-detail='${EVIDENCE_UUID}']`) as HTMLElement;
    const text = detail.textContent ?? "";
    expect(text).toMatch(/Value as reported by the source12500 W/);
    expect(text).toMatch(/Value in site units12\.5 kW/);
    expect(text).toContain(LEDGER_RECORD.accepted_as.foundation_revision_id);
    expect(text).toContain(LEDGER_RECORD.accepted_as.binding_revision_id);
    // The receipt keeps the delivery's first receipt apart from this reading's later decision.
    expect(text).toMatch(/Delivery first received \(server clock, UTC\)9 Oct 2026 09:00 UTC/);
    expect(text).toMatch(/This reading decided \(server clock, UTC\)9 Oct 2026 09:07 UTC/);
    expect(detail.querySelector("[data-record-message]")?.textContent).toBe(LEDGER_RECORD.envelope.text);
    expect(detail.querySelector(`[data-record-conflict]`)?.textContent).toContain('"value":"99999"');
    expect(detail.querySelector("[data-record-duplicate]")).not.toBeNull();
  });

  it("opens a repeat's first accepted reading from the refused list", async () => {
    const client = ledgerClient({ status: "loaded", value: LEDGER_EVIDENCE });
    renderAt(ANALYSIS_URL, client);
    await settledScreen();
    fireEvent.click(screen.getByRole("button", { name: `reading ${EVIDENCE_UUID}` }));
    await settledScreen();
    expect(loc()).toContain(`record=${EVIDENCE_UUID}`);
    expect(client.recordKeys.at(-1)).toBe(EVIDENCE_UUID);
  });
});

describe("Site Evidence from the central ledger: product vocabulary", () => {
  it.each([
    ["overview", EVIDENCE_URL],
    ["analysis with a reading open", `${ANALYSIS_URL}&source=${LEDGER_EVIDENCE.sources[0].source_id}&record=${EVIDENCE_UUID}`],
  ])("uses no implementation vocabulary on the %s", async (_name, path) => {
    renderAt(
      path,
      ledgerClient({
        status: "loaded",
        value: ledgerEvidence({ states: ["ACCEPTED", "PARTIAL_BATCH", "CONFLICTING", "STALE_PROJECTION", "OUTDATED_CONFIGURATION"] }),
      }),
    );
    await settledScreen();
    // W1-F2 known deviation (packet): the binding v69 title "How a claim limit is set" uses a listed word; until
    // the Architect rules, only that exact heading text is left out of the scan.
    const copy = document.body.cloneNode(true) as HTMLElement;
    copy.querySelectorAll("h2").forEach((h) => {
      if ((h.textContent ?? "").trim() === "How a claim limit is set") h.textContent = "";
    });
    const result = scanProductVocabulary(copy, path);
    expect(result.scanned).toBeGreaterThan(0);
    expect(result.violations).toEqual([]);
  });
});

describe("central-ledger evidence client", () => {
  function stub(status: number, body: unknown) {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify(body), { status }))));
  }

  it("accepts the ledger overview and refuses a ledger page missing its cursor", async () => {
    const client = createSiteEvidenceClient("/api/sites");
    stub(200, LEDGER_EVIDENCE);
    const overview = await client.getEvidence("KOBO-001", {});
    expect(overview.status).toBe("loaded");
    stub(200, { store: "POSTGRES", total: 1, records: [] });
    expect((await client.ledger?.listRecords("KOBO-001", {}))?.status).toBe("unavailable");
  });

  it("names a 409 awaiting migration and a missing gateway", async () => {
    const client = createSiteEvidenceClient("/api/sites");
    stub(409, { detail: { code: "AWAITING_EVIDENCE_MIGRATION", message: "awaiting" } });
    expect(await client.getEvidence("KOBO-001", {})).toMatchObject({ transition: "AWAITING_EVIDENCE_MIGRATION" });
    stub(404, { detail: { code: "GATEWAY_HEALTH_UNAVAILABLE" } });
    expect((await client.gatewayHealth?.getGatewayHealth("KOBO-001"))?.status).toBe("not_found");
  });
});
