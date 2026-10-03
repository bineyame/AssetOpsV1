import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import type { SiteEvidenceClient } from "../../sites/siteEvidenceClient";
import {
  EMPTY_EVIDENCE_CLIENT,
  POPULATED_EVIDENCE,
  RECORD_DETAIL,
  evidenceClient,
} from "../../sites/__tests__/evidenceFixtures";
import { EMPTY_ANALYTICS_CLIENT } from "../../sites/__tests__/analyticsFixtures";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import { settledScreen } from "../../test/settled";
import { spacedText } from "../../test/text";
import { OPERATOR_SITE_TABS_LABEL } from "../operatorSiteTabs";

/**
 * Site > Evidence (T027 part A; AC12, AC18, AC20): source health, per-signal
 * coverage with named gaps, the configuration and mapping basis, rejections,
 * and the record inspector as an in-page drill-down that never changes the
 * Site root or the current tab.
 */

const SITE_ID = HYBRID_MINI_GRID_SITE.site_id;
const EVIDENCE_URL = `/sites/${SITE_ID}/evidence`;

const DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};
const DETAIL: SiteDetailClient = {
  getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }),
};

function LocationProbe() {
  const location = useLocation();
  return <output data-location>{`${location.pathname}${location.search}`}</output>;
}

function renderAt(path: string, evidence: SiteEvidenceClient, enabled = false) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={featureFlagsWith(enabled)}
        siteDirectory={DIRECTORY}
        siteDetail={DETAIL}
        siteEvidence={evidence}
        siteAnalytics={EMPTY_ANALYTICS_CLIENT}
      />
      <LocationProbe />
    </MemoryRouter>,
  );
}

function location(): string {
  return document.querySelector("[data-location]")?.textContent ?? "";
}

function currentTab(): string {
  const row = screen.getByRole("navigation", { name: OPERATOR_SITE_TABS_LABEL });
  return within(row).getByRole("link", { current: "page" }).textContent ?? "";
}

/** A body section, found by its heading (the panel and its table share it). */
function region(name: string): HTMLElement {
  return screen.getByRole("heading", { name }).closest("section") as HTMLElement;
}

const populated = () =>
  evidenceClient({ status: "loaded", value: POPULATED_EVIDENCE });

describe("Site > Evidence, populated", () => {
  it("renders source health per source as data quality with provenance and batches", async () => {
    renderAt(`${EVIDENCE_URL}?batch=artifact-1`, populated());
    await settledScreen();

    const sources = region("Source health");
    const row = sources.querySelector('[data-evidence-source="kobo-gw-1"]') as HTMLElement;
    expect(row).not.toBeNull();
    const text = spacedText(row);
    expect(text).toContain("kobo-gw-1 / gw-1");
    expect(row.querySelector("[data-evidence-provenance]")?.textContent).toBe(
      "Simulated source",
    );
    expect(text).toContain("2026-07-02T09:00:12Z");
    expect(text).toMatch(/artifact-0\s*: IN_PROGRESS, 4 of 10 processed/);
    expect(
      row.querySelector('[data-evidence-batch-highlighted="yes"]')?.getAttribute(
        "data-evidence-batch",
      ),
    ).toBe("artifact-1");
    expect(
      spacedText(screen.getByRole("main")),
    ).toMatch(/never asset health/);
  });

  it("names a signal no record reported as a coverage gap with no value", async () => {
    renderAt(EVIDENCE_URL, populated());
    await settledScreen();

    const coverage = region("Signal coverage");
    const rows = coverage.querySelectorAll("[data-evidence-coverage]");
    expect(rows).toHaveLength(2);
    const gap = coverage.querySelector('[data-coverage-status="NOT_REPORTED"]') as HTMLElement;
    expect(spacedText(gap)).toMatch(/Coverage gap/);
    expect(spacedText(gap)).toContain("Battery");
    expect(within(gap).queryByRole("button")).toBeNull();
    const reported = coverage.querySelector('[data-coverage-status="REPORTED"]') as HTMLElement;
    expect(spacedText(reported)).toMatch(/72 70 2 1/);
    expect(spacedText(reported)).toContain("900 seconds");
  });

  it("shows the accepted mapping and configuration basis against the current Foundation", async () => {
    renderAt(EVIDENCE_URL, populated());
    await settledScreen();

    const basis = screen
      .getByRole("heading", { name: "Configuration and mapping basis" })
      .closest("section") as HTMLElement;
    expect(spacedText(basis)).toContain("kobo-v3 v3");
    expect(spacedText(basis)).toContain("Foundation v2, valid from 2026-06-01T00:00:00Z");
    expect(basis.querySelector("[data-evidence-current-foundation]")?.textContent).toBe(
      "v3, valid from 2026-08-01T00:00:00Z",
    );
  });

  it("counts and lists rejections", async () => {
    renderAt(EVIDENCE_URL, populated());
    await settledScreen();

    expect(screen.getByText("2 records were rejected and never accepted.")).toBeInTheDocument();
    const items = document.querySelectorAll("[data-evidence-rejection]");
    expect(items).toHaveLength(2);
    expect(spacedText(items[0] as HTMLElement)).toMatch(
      /UNKNOWN_SIGNAL \(signal_id\)\s*: The signal is not in the mapping\. Batch artifact-1\./,
    );
  });

  // T028 AC20 keeps this: with no analytic declared for the site (the
  // declaration read is not_found here) nothing about capability appears. The
  // populated capability table is pinned in `t028Screens.test.tsx`.
  it("says nothing about capability readiness or claim ceilings", async () => {
    renderAt(EVIDENCE_URL, populated());
    await settledScreen();

    const words = spacedText(screen.getByRole("main"));
    expect(words).toContain("Source health");
    expect(words).not.toMatch(/readiness|claim ceiling|ceiling|capabilit/i);
  });
});

describe("the record inspector is a drill-down", () => {
  it("opens from a signal row and shows the record with three distinct timestamps", async () => {
    const client = populated();
    renderAt(EVIDENCE_URL, client);
    await settledScreen();

    fireEvent.click(
      screen.getByRole("button", { name: "Inspect records for GEN-1 / active_power" }),
    );
    await settledScreen();
    expect(location()).toBe(`${EVIDENCE_URL}?signal=GEN-1%2Factive_power`);
    expect(client.recordQueries.at(-1)).toMatchObject({
      device: "GEN-1",
      signal: "active_power",
      source: null,
      from: POPULATED_EVIDENCE.window.start,
      to: POPULATED_EVIDENCE.window.end,
    });

    fireEvent.click(screen.getByRole("button", { name: "Show record msg-gen-72" }));
    await settledScreen();
    expect(location()).toContain("record=msg-gen-72");

    const detail = document.querySelector(
      "[data-evidence-record-detail]",
    ) as HTMLElement;
    const times = ["source", "published", "received"].map(
      (kind) => detail.querySelector(`[data-record-time="${kind}"]`)?.textContent,
    );
    expect(times).toEqual([
      RECORD_DETAIL.source_time,
      RECORD_DETAIL.published_at,
      RECORD_DETAIL.received_at,
    ]);
    expect(new Set(times).size).toBe(3);
    const terms = Array.from(detail.querySelectorAll("dt")).map((term) => term.textContent);
    expect(terms).toEqual(
      expect.arrayContaining(["Source time", "Published", "Received"]),
    );
    const words = spacedText(detail);
    expect(words).toContain("kobo-gw-1 / GEN-1 / active_power");
    expect(words).toContain("kobo-v3 v3");
    expect(words).toContain(`Site ${SITE_ID}, Foundation v2, valid from 2026-06-01T00:00:00Z`);
    expect(words).toContain("Simulated source");
    expect(words).toContain("GOOD");
    expect(words).toMatch(/Original value 41\.5 kW/);
    expect(words).toMatch(/Normalized value 41\.5 kW\s*\.\s*Normalization is the identity/);

    // The root and the tab never change.
    expect(location().startsWith(`${EVIDENCE_URL}?`)).toBe(true);
    expect(currentTab()).toBe("Evidence");
  });

  it("opens from a source row and closes back to the tab body", async () => {
    const client = populated();
    renderAt(EVIDENCE_URL, client);
    await settledScreen();

    fireEvent.click(
      screen.getByRole("button", { name: "Inspect records from kobo-gw-1" }),
    );
    await settledScreen();
    expect(location()).toBe(`${EVIDENCE_URL}?source=kobo-gw-1`);
    expect(client.recordQueries.at(-1)).toMatchObject({
      device: null,
      signal: null,
      source: "kobo-gw-1",
    });
    expect(document.getElementById("site-evidence-inspector")).not.toBeNull();
    expect(screen.getByText("1 of 72 accepted records, newest source time first.")).toBeInTheDocument();
    expect(currentTab()).toBe("Evidence");

    fireEvent.click(screen.getByRole("button", { name: "Close records" }));
    await settledScreen();
    expect(location()).toBe(EVIDENCE_URL);
    expect(document.getElementById("site-evidence-inspector")).toBeNull();
    expect(region("Source health")).toBeInTheDocument();
  });

  it("reopens a deep-linked record from the address alone", async () => {
    renderAt(
      `${EVIDENCE_URL}?signal=GEN-1/active_power&record=msg-gen-72`,
      populated(),
    );
    await settledScreen();

    expect(
      document.querySelector('[data-evidence-record-detail="msg-gen-72"]'),
    ).not.toBeNull();
    expect(currentTab()).toBe("Evidence");
  });
});

describe("Site > Evidence, empty and unavailable", () => {
  it("says no batch has been accepted and shows no invented section", async () => {
    renderAt(EVIDENCE_URL, EMPTY_EVIDENCE_CLIENT);
    await settledScreen();

    expect(document.querySelector('[data-evidence-state="empty"]')).not.toBeNull();
    expect(screen.getByText(/No source batch has been accepted for this site/)).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Source health" })).toBeNull();
    expect(screen.queryByRole("heading", { name: "Signal coverage" })).toBeNull();
    expect(screen.queryByRole("heading", { name: "Rejections" })).toBeNull();
    expect(currentTab()).toBe("Evidence");
  });

  it("names an unreadable evidence store as unavailable, not empty", async () => {
    renderAt(
      EVIDENCE_URL,
      evidenceClient({
        status: "unavailable",
        message: "The evidence store could not be read.",
      }),
    );
    await settledScreen();

    expect(document.querySelector('[data-evidence-state="unavailable"]')?.textContent).toBe(
      "The evidence store could not be read.",
    );
    expect(document.querySelector('[data-evidence-state="empty"]')).toBeNull();
  });

  it("stays available with the Simulator Lab gate open or closed", async () => {
    renderAt(EVIDENCE_URL, populated(), true);
    await settledScreen();
    expect(region("Source health")).toBeInTheDocument();
  });
});
