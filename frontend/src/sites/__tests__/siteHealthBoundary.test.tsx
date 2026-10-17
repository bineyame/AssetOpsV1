/**
 * S7-01b Site Health (`health:2#a`) and battery boundary (`asset:3#a`) against
 * the committed S7-01a wire contract `backend/tests/fixtures/s7_health_api_contract.json`
 * (regenerated and compared by `backend/tests/test_s7_health_contract_postgres.py`).
 *
 * Recorded cases: KOBO-001 with the six central gateway cases, never received
 * and a disabled import gateway; KOBO-002 with only a disabled gateway and a
 * configured battery without signal channels set up; KOBO-NB with no battery;
 * the unknown Site (404), store failure (503), a foreign asset (404) and an
 * invalid asset ID (422). Derived cases (named where built): 401, 403, the
 * 409 inconsistent selection and an unbound battery.
 */
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import contract from "../../../../backend/tests/fixtures/s7_health_api_contract.json";
import { SiteAssetFrame, SiteAssetsFrame, SiteHealthFrame } from "../../shell/SiteHealthFrames";
import { describeViolations, scanDisclosureVocabulary, scanProductVocabulary } from "../../test/productVocabulary";
import { expectV69Panels, panelTitled } from "../../test/panelStructure";
import { expectStateLineVisible } from "../../test/productPresentation";
import { settledScreen } from "../../test/settled";
import type { SiteDetailClient } from "../siteDirectoryClient";
import { HYBRID_MINI_GRID_SITE } from "./sldFixtures";

interface Served {
  status: number;
  body: any;
}

const C = contract as unknown as Record<string, Served>;
const KOBO_001_ASSET: string = C.battery_entry_kobo001.body.batteries[0].asset_id;
const KOBO_002_ASSET: string = C.battery_entry_kobo002.body.batteries[0].asset_id;
const gatewayRow = (key: string) =>
  (C.health_kobo001.body.gateways as any[]).find((g) => g.gateway_external_id === key);

function serve(table: Record<string, Served>) {
  const requests: string[] = [];
  vi.stubGlobal("fetch", async (url: string) => {
    requests.push(url);
    const hit = table[url];
    if (!hit) {
      return new Response(JSON.stringify({ detail: { code: "TEST_UNMATCHED", message: url } }), { status: 599 });
    }
    return new Response(JSON.stringify(hit.body), { status: hit.status });
  });
  return requests;
}

/** The recorded answers at their real paths. */
function recorded(overrides: Record<string, Served> = {}): Record<string, Served> {
  return {
    "/api/sites/KOBO-001/source-health": C.health_kobo001,
    "/api/sites/KOBO-002/source-health": C.health_kobo002,
    "/api/sites/NOT-A-SITE/source-health": C.health_unknown_site,
    "/api/sites/KOBO-001/battery": C.battery_entry_kobo001,
    "/api/sites/KOBO-002/battery": C.battery_entry_kobo002,
    "/api/sites/KOBO-NB/battery": C.battery_entry_kobonb,
    "/api/sites/KOBO-NB/source-health": C.health_kobo002,
    [`/api/sites/KOBO-001/assets/${KOBO_001_ASSET}/battery`]: C.battery_detail_kobo001,
    [`/api/sites/KOBO-002/assets/${KOBO_002_ASSET}/battery`]: C.battery_detail_kobo002,
    [`/api/sites/KOBO-NB/assets/${KOBO_001_ASSET}/battery`]: C.battery_detail_foreign,
    "/api/sites/KOBO-001/assets/not-an-id/battery": C.battery_detail_invalid,
    ...overrides,
  };
}

const detail: SiteDetailClient = {
  getSite: async (siteId: string) => ({ status: "loaded", site: { ...HYBRID_MINI_GRID_SITE, site_id: siteId } }),
} as SiteDetailClient;

function Where() {
  const location = useLocation();
  return <output data-testid="where">{`${location.pathname}${location.search}`}</output>;
}

function mount(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/sites/:siteId/health" element={<><SiteHealthFrame detail={detail} sitesPath="/sites" /><Where /></>} />
        <Route path="/sites/:siteId/assets" element={<><SiteAssetsFrame detail={detail} sitesPath="/sites" /><Where /></>} />
        <Route
          path="/sites/:siteId/assets/:assetId"
          element={<><SiteAssetFrame detail={detail} sitesPath="/sites" /><Where /></>}
        />
      </Routes>
    </MemoryRouter>,
  );
}

const q = (selector: string) => document.body.querySelector(selector);
const qa = (selector: string) => Array.from(document.body.querySelectorAll(selector));
const main = () => document.body.querySelector("main") as HTMLElement;
const where = () => screen.getByTestId("where").textContent;

function noVocabularyViolations(page: string) {
  const { violations, scanned } = scanProductVocabulary(main(), page);
  expect(scanned).toBeGreaterThan(5);
  expect(violations, describeViolations(violations)).toEqual([]);
}

/** Visible text outside the closed "Technical details" disclosures. */
function defaultReading(): string {
  const clone = main().cloneNode(true) as HTMLElement;
  clone.querySelectorAll("details").forEach((d) => d.remove());
  return clone.textContent ?? "";
}

function atWidth(width: number) {
  Object.defineProperty(window, "innerWidth", { configurable: true, value: width });
  window.dispatchEvent(new Event("resize"));
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("Site Health: gateway contact (health:2#a)", () => {
  it("labels the summary Gateway contact with the enabled count, never Site or equipment health", async () => {
    serve(recorded());
    mount("/sites/KOBO-001/health");
    await settledScreen();
    const summary = q("[data-health-summary]") as HTMLElement;
    expect(summary.getAttribute("data-health-summary")).toBe("NOT_ALL_CURRENT");
    expect(summary.textContent).toContain("Some gateways are not in contact.");
    expect(summary.textContent).toContain("8 enabled gateways: 6 current, 1 stale, 1 unknown");
    expect(summary.textContent).toContain("1 disabled, not counted");
    // The only "healthy" on the page is the closing notice that denies it.
    expect(defaultReading().replace(q(".notice")?.textContent ?? "", "")).not.toMatch(
      /site health|equipment health|healthy/i,
    );
    // The Health tab is the current one.
    expect(q('nav[aria-label] a[aria-current="page"]')?.textContent).toBe("Health");
    noVocabularyViolations("health KOBO-001");
  });

  it("shows each central case in its own words, with no signed or untrusted age", async () => {
    serve(recorded());
    mount("/sites/KOBO-001/health");
    await settledScreen();
    const row = (key: string) => q(`[data-health-gateway="${key}"]`) as HTMLElement;
    expect(row("s7-current").getAttribute("data-health-contact")).toBe("CURRENT");
    // F5a fix round: the table row is one line per gateway (short status word with age, quality chip);
    // the long wording lives in the reported-detail rows (Technical details) and the selected-gateway view.
    const status = (key: string) => (row(key).querySelector("[data-health-status]") as HTMLElement).textContent;
    const quality = (key: string) => (row(key).querySelector("[data-health-quality] .badge") as HTMLElement).textContent;
    const reported = (key: string) => (q(`[data-health-reported="${key}"]`) as HTMLElement).textContent ?? "";
    expect(status("s7-current")).toBe("Current · 5 s ago");
    expect(quality("s7-current")).toBe("Current");
    expect(status("s7-stale-cadence")).toBe("Stale · 10 min");
    expect(status("s7-delayed-old")).toBe("Current · 5 s ago");
    expect(quality("s7-delayed-old")).toBe("Old");
    expect(reported("s7-delayed-old")).toContain("Old: observed 6 h ago; it reached the server 6 h after");
    expect(quality("s7-clock-offset")).toBe("Unknown age");
    expect(reported("s7-clock-offset")).toContain(
      "Unknown age: the gateway's clock is off by 95 s, more than the 5 s allowed",
    );
    expect(status("s7-never-received")).toBe("Never received");
    expect(quality("s7-never-received")).toBe("Nothing received");
    expect(reported("s7-never-received")).toContain("Nothing received yet");
    // The disabled import gateway: listed, marked and not counted.
    const disabled = row("edge-kobo-001");
    expect(disabled.getAttribute("data-health-registration")).toBe("DISABLED");
    expect(disabled.textContent).toContain("Disabled");
    expect((q("[data-health-summary]") as HTMLElement).textContent).toContain("1 disabled, not counted");
    // No age anywhere on the page is signed.
    expect(defaultReading()).not.toMatch(/-\d+\s?(s|min|h|d)\b/);
    expect(gatewayRow("s7-clock-offset").reported_facts.fact_age_seconds).toBeNull();
  });

  it("W1-UX-06: an observation after receipt carries a null receipt lag in the contract, and the page states no lag for it", async () => {
    expect(gatewayRow("s7-clock-offset").reported_facts.receipt_lag_seconds).toBeNull();
    expect(gatewayRow("s7-delayed-old").reported_facts.receipt_lag_seconds).toBe(21600);
    serve(recorded());
    mount("/sites/KOBO-001/health");
    await settledScreen();
    const clock = (q('[data-health-reported="s7-clock-offset"]') as HTMLElement).textContent ?? "";
    expect(clock).not.toMatch(/reached the server/);
    expect(clock).not.toMatch(/-\d+\s?(s|min|h|d)\b/);
    expect((q('[data-health-gateway="s7-clock-offset"]') as HTMLElement).textContent).not.toMatch(/reached the server/);
    expect((q('[data-health-reported="s7-delayed-old"]') as HTMLElement).textContent).toContain("it reached the server 6 h after");
  });

  it("keeps queue, storage and device contact as last reported, in separately qualified sections", async () => {
    serve(recorded());
    mount("/sites/KOBO-001/health");
    await settledScreen();
    // W1-F5a: v69 `health` - condition and data sources are separate panels; queue, storage and device contact
    // are qualified columns and rows of the data-sources panel, never condition.
    expectV69Panels("health");
    const sources = panelTitled("Data sources · data quality, not equipment condition");
    const condition = panelTitled("Physical asset condition");
    expect(sources.querySelector('[data-health-queue-row="s7-queue-growth"]')).not.toBeNull();
    expect(sources.querySelector('[data-health-source="s7-clock-offset-device"]')).not.toBeNull();
    expect(sources.textContent).toContain("Queue, as last reported");
    expect(sources.textContent).toContain("as its gateway reports");
    expect(condition.querySelector("[data-health-gateway], [data-health-queue-row], [data-health-source]")).toBeNull();
    const queue = q('[data-health-queue-row="s7-queue-growth"]') as HTMLElement;
    expect(queue.textContent).toContain("900");
    expect(queue.textContent).toContain("1 h 30 min");
    const stop = q('[data-health-queue-row="s7-disk-stop"]') as HTMLElement;
    expect(stop.querySelector("[data-health-disk]")?.getAttribute("data-health-disk")).toBe("STOP");
    expect(stop.textContent).toContain("Full: collection stopped");
    const recovery = q('[data-health-queue-row="s7-disk-recovery"]') as HTMLElement;
    expect(recovery.textContent).toContain("Normal");
    expect(recovery.textContent).toContain("none waiting");
    expect((q('[data-health-queue-row="s7-clock-offset"]') as HTMLElement).textContent).toContain("Unknown age");
    // The never-received gateway reported nothing: no queue row for it.
    expect(q('[data-health-queue-row="s7-never-received"]')).toBeNull();
    const device = q('[data-health-source="s7-clock-offset-device"]') as HTMLElement;
    expect(device.textContent).toContain("Unknown age");
    expect((q('[data-health-source="s7-never-received-device"]') as HTMLElement).textContent).toContain(
      "Not in the gateway's latest report",
    );
    // Disabled gateways' sources are not listed as device contact.
    expect(q('[data-health-source="clinic-meter"]')).toBeNull();
    // No stale-projection state exists in the read, so none is shown.
    expect(main().textContent).not.toMatch(/projection/i);
    // The battery entry: condition Unknown with a link by asset ID.
    const battery = condition.querySelector(`[data-health-battery="${KOBO_001_ASSET}"]`) as HTMLElement;
    expect(battery.textContent).toContain("Unknown");
    expect(battery.querySelector("a")?.getAttribute("href")).toBe(`/sites/KOBO-001/assets/${KOBO_001_ASSET}`);
    expect(condition.textContent).toContain("Condition cannot yet be judged.");
    expect(q(".notice")?.textContent).toContain("does not make equipment healthy");
  });

  it("puts exact IDs, rule and watermark in Technical details, closed by default", async () => {
    serve(recorded());
    mount("/sites/KOBO-001/health");
    await settledScreen();
    const technical = q('[data-disclosure="site-health-technical"]') as HTMLDetailsElement;
    expect(technical.open).toBe(false);
    expect(technical.textContent).toContain(C.health_kobo001.body.rule_id);
    expect(q("[data-health-watermark]")?.getAttribute("data-health-watermark")).toBe(
      C.health_kobo001.body.summary.source_watermark.selected_diagnostic_ids_sha256,
    );
    const current = q('[data-health-technical="s7-current"]') as HTMLElement;
    expect(current.textContent).toContain(gatewayRow("s7-current").diagnostic.diagnostic_id);
    expect(defaultReading()).not.toContain(C.health_kobo001.body.rule_id);
    expect(defaultReading()).not.toContain(gatewayRow("s7-current").gateway_id);
  });

  it("selects one gateway by an exact link that survives reload; an unknown one is refused", async () => {
    serve(recorded());
    mount("/sites/KOBO-001/health");
    await settledScreen();
    const target = gatewayRow("s7-clock-offset");
    const link = q('[data-health-open="s7-clock-offset"]') as HTMLAnchorElement;
    expect(link.getAttribute("href")).toBe(`/sites/KOBO-001/health?gateway=${target.gateway_id}`);
    link.focus();
    expect(document.activeElement).toBe(link);
    fireEvent.click(link);
    await settledScreen();
    expect(where()).toBe(`/sites/KOBO-001/health?gateway=${target.gateway_id}`);
    const selected = () => q("[data-health-selected-diagnostic]")?.getAttribute("data-health-selected-diagnostic");
    expect(selected()).toBe(target.diagnostic.diagnostic_id);
    // W1-F5a: the selection sits inside the data-sources panel, never as an extra panel.
    expect(q('[data-health-selected="found"]')?.textContent).toContain("Gateway s7-clock-offset");
    expect(panelTitled("Data sources · data quality, not equipment condition").contains(q('[data-health-selected="found"]'))).toBe(true);
    expectV69Panels("health");
    // Reload: the same address gives the same selection.
    cleanup();
    serve(recorded());
    mount(`/sites/KOBO-001/health?gateway=${target.gateway_id}`);
    await settledScreen();
    expect(selected()).toBe(target.diagnostic.diagnostic_id);
    fireEvent.click(screen.getByRole("link", { name: "Show all gateways" }));
    await settledScreen();
    expect(where()).toBe("/sites/KOBO-001/health");
    cleanup();
    serve(recorded());
    mount("/sites/KOBO-001/health?gateway=00000000-0000-4000-8000-999999999999");
    await settledScreen();
    expect(q('[data-health-selected="not-found"]')?.textContent).toContain("no gateway with that ID");
    expectV69Panels("health");
  });

  it("states no enabled gateway on the second Site instead of a healthy zero", async () => {
    serve(recorded());
    mount("/sites/KOBO-002/health");
    await settledScreen();
    const summary = q("[data-health-summary]") as HTMLElement;
    expect(summary.getAttribute("data-health-summary-reason")).toBe("NO_ENABLED_GATEWAY");
    expect(summary.textContent).toContain("No gateway is reporting.");
    expect(summary.textContent).toContain("No gateway is enabled for this site, so nothing is known about source contact.");
    expect(summary.textContent).not.toMatch(/\b0 current\b|all current/);
    expect(q('[data-health-gateway="edge-kobo-002"]')?.getAttribute("data-health-registration")).toBe("DISABLED");
    expect(q('[data-health-queue="none"]')).not.toBeNull();
    noVocabularyViolations("health KOBO-002");
  });

  it("refuses an unknown Site, store failure, inconsistent selection and the identity seam with no rows", async () => {
    const cases: [string, Served, RegExp][] = [
      ["404 recorded", C.health_unknown_site, /not configured/],
      ["503 recorded", C.health_unavailable, /could not be read, so nothing is known about gateway contact/],
      // Derived: the 409 the read returns when registrations and reports disagree.
      [
        "409 derived",
        { status: 409, body: { detail: { code: "SOURCE_HEALTH_SELECTION_INCONSISTENT", gateways: null, message: "x" } } },
        /did not agree/,
      ],
      // Derived: the identity seam's 401 and 403.
      ["401 derived", { status: 401, body: { detail: { code: "UNAUTHENTICATED", message: "x" } } }, /Sign in/],
      ["403 derived", { status: 403, body: { detail: { code: "SITE_SCOPE_FORBIDDEN", message: "x" } } }, /no access/],
    ];
    for (const [name, answer, text] of cases) {
      serve(recorded({ "/api/sites/KOBO-001/source-health": answer }));
      mount("/sites/KOBO-001/health");
      await settledScreen();
      const refused = q('[data-health-read="refused"]') as HTMLElement;
      expect(refused, name).not.toBeNull();
      expect(refused.getAttribute("data-health-http"), name).toBe(String(answer.status));
      expect(refused.textContent, name).toMatch(text);
      expect(qa("[data-health-gateway]"), name).toHaveLength(0);
      expect(q("[data-health-summary]"), name).toBeNull();
      expectV69Panels("health");
      cleanup();
      vi.unstubAllGlobals();
    }
  });

  it("renders at 1440 and 390 with the same sections", async () => {
    for (const width of [1440, 390]) {
      atWidth(width);
      serve(recorded());
      mount("/sites/KOBO-001/health");
      await settledScreen();
      expect(qa("[data-health-gateway]")).toHaveLength(9);
      // W1-F5a: the same v69 panels at both widths: the condition table, the data-sources table and the technical one.
      expectV69Panels("health");
      expect(qa("table").length).toBeGreaterThanOrEqual(3);
      cleanup();
      vi.unstubAllGlobals();
    }
  });
});

describe("Battery boundary (asset:3#a)", () => {
  it("shows the configured battery as Unknown with its named missing inputs and pinned IDs", async () => {
    serve(recorded());
    mount(`/sites/KOBO-001/assets/${KOBO_001_ASSET}`);
    await settledScreen();
    const body = C.battery_detail_kobo001.body;
    expect(q("[data-battery-condition]")?.getAttribute("data-battery-condition")).toBe("UNKNOWN");
    expect(await screen.findByRole("heading", { level: 1, name: "Battery energy storage" })).toBeTruthy();
    const missing = qa("[data-battery-missing]").map((r) => r.getAttribute("data-battery-missing"));
    expect(missing).toEqual(body.physical_condition.missing_causal_inputs.map((i: any) => i.input));
    expect(main().textContent).toContain("Temperature history");
    expect(main().textContent).toContain("Measured usable capacity");
    expect((q('[data-battery-metric="rating"]') as HTMLElement).textContent).toContain("200 kWh");
    expect((q('[data-battery-metric="rating"]') as HTMLElement).textContent).toContain("not a measurement");
    expect((q('[data-battery-metric="reserve"]') as HTMLElement).textContent).toContain("Not available");
    expect((q('[data-battery-metric="channels"]') as HTMLElement).textContent).toContain("1 connected");
    expectV69Panels("asset");
    expect(q("[data-battery-withheld]")?.textContent).toMatch(/Degradation, remaining life.*replacement exposure and diagnosis are not stated/);
    const reading = defaultReading();
    expect(reading).not.toMatch(/healthy|good condition|replace by|warranty at risk/i);
    expect(reading).not.toContain(body.asset.asset_id);
    // Pinned IDs: asset, Foundation revision, channel set revision and channel revision, in Technical details.
    expect(q("[data-battery-asset]")?.getAttribute("data-battery-asset")).toBe(body.asset.asset_id);
    expect(q("[data-battery-foundation]")?.getAttribute("data-battery-foundation")).toBe(body.basis.foundation_revision_id);
    expect(q("[data-battery-channel-set]")?.getAttribute("data-battery-channel-set")).toBe(body.basis.binding_set_revision_id);
    expect(q("[data-battery-channel]")?.getAttribute("data-battery-channel")).toBe(body.bound_channels[0].binding_revision_id);
    expect(qa("details").every((d) => !(d as HTMLDetailsElement).open)).toBe(true);
    noVocabularyViolations("battery KOBO-001");
  });

  it("names a battery whose channels are not set up, and an unbound battery, as Unknown", async () => {
    serve(recorded());
    mount(`/sites/KOBO-002/assets/${KOBO_002_ASSET}`);
    await settledScreen();
    expect(q("[data-battery-channels]")?.getAttribute("data-battery-channels")).toBe("NO_BINDING_SET");
    expect((q('[data-battery-metric="channels"]') as HTMLElement).textContent).toContain("Not set up");
    expect(q("[data-battery-condition]")?.getAttribute("data-battery-condition")).toBe("UNKNOWN");
    cleanup();
    vi.unstubAllGlobals();
    // Derived: the recorded KOBO-001 detail with no channel connected to the battery (UNBOUND).
    const unbound = structuredClone(C.battery_detail_kobo001);
    unbound.body.binding_status = "UNBOUND";
    unbound.body.bound_channels = [];
    unbound.body.physical_condition.reason = "UNBOUND";
    serve(recorded({ [`/api/sites/KOBO-001/assets/${KOBO_001_ASSET}/battery`]: unbound }));
    mount(`/sites/KOBO-001/assets/${KOBO_001_ASSET}`);
    await settledScreen();
    expect((q('[data-battery-metric="channels"]') as HTMLElement).textContent).toContain("None connected");
    expect(main().textContent).toContain("no signal channel is connected to this battery");
  });

  it("shows NOT_CONFIGURED without an asset ID when the Site has no battery", async () => {
    serve(recorded());
    mount("/sites/KOBO-NB/assets");
    await settledScreen();
    expect(q("[data-battery-configuration]")?.getAttribute("data-battery-configuration")).toBe("NOT_CONFIGURED");
    expect(main().textContent).toContain("No battery configured");
    expect(qa("[data-battery-link]")).toHaveLength(0);
    noVocabularyViolations("battery entry KOBO-NB");
    cleanup();
    vi.unstubAllGlobals();
    serve(recorded());
    mount("/sites/KOBO-NB/health");
    await settledScreen();
    expect(q('[data-health-battery="NOT_CONFIGURED"]')?.textContent).toBe("Battery page");
    // The state is said once, in the lead; the repeated "Unknown (not configured)" line was removed (F5a review L3).
    expect(q("[data-health-condition-lead]")?.textContent).toContain("No battery is part of this site's configuration");
  });

  it("lists the configured battery by asset ID on the entry page and follows it", async () => {
    serve(recorded());
    mount("/sites/KOBO-001/assets");
    await settledScreen();
    const link = q(`[data-battery-link="${KOBO_001_ASSET}"]`) as HTMLAnchorElement;
    fireEvent.click(link);
    await settledScreen();
    expect(where()).toBe(`/sites/KOBO-001/assets/${KOBO_001_ASSET}`);
    expect(q("[data-battery-condition]")).not.toBeNull();
  });

  it("refuses an asset outside the Site's configuration and an invalid ID, with no condition row", async () => {
    const cases: [string, string, number, RegExp][] = [
      ["foreign asset", `/sites/KOBO-NB/assets/${KOBO_001_ASSET}`, 404, /not a battery in this site's current configuration/],
      ["invalid id", "/sites/KOBO-001/assets/not-an-id", 422, /does not name an asset/],
    ];
    for (const [name, path, http, text] of cases) {
      serve(recorded());
      mount(path);
      await settledScreen();
      const refused = q('[data-health-read="refused"]') as HTMLElement;
      expect(refused.getAttribute("data-health-http"), name).toBe(String(http));
      expect(refused.textContent, name).toMatch(text);
      expect(q("[data-battery-condition]"), name).toBeNull();
      expectV69Panels("asset");
      cleanup();
      vi.unstubAllGlobals();
    }
  });
});

describe("W1-F5a: Health and battery state lines (the W1-UX-05/06 words, now in the v69 panels)", () => {
  const SOURCES = "Data sources · data quality, not equipment condition";
  const strip = () => q(".status-strip") as HTMLElement;
  const contact = () => q("[data-health-summary]") as HTMLElement;
  const contactLabel = () => contact().querySelector("[data-health-contact-label]")?.textContent;
  const w1 = (page: string) => {
    const { violations, scanned } = scanProductVocabulary(main(), page, { set: "w1" });
    expect(scanned).toBeGreaterThan(5);
    expect(violations, describeViolations(violations)).toEqual([]);
  };
  /** A refused read has no read instant, so its bound is the shared "As of: time not recorded" (never now). */
  const expectRefusedStateLine = (within: HTMLElement, label: string) => {
    expect(expectStateLineVisible(within)).toBe(label);
    expect(within.querySelector("[data-product-status-as-of]")?.textContent).toBe("As of: time not recorded");
  };
  const disclosureOf = (el: HTMLElement, page: string) => {
    const result = scanDisclosureVocabulary(el, page);
    expect(result.disclosures).toBe(1);
    expect(result.scanned).toBeGreaterThan(2);
    expect(result.violations, describeViolations(result.violations)).toEqual([]);
  };
  /** The state line is said once, in the status strip (W1-F5a self-check). */
  const expectOneStateLine = () => {
    expect(qa("[data-product-status]")).toHaveLength(1);
    expect(strip().querySelector("[data-product-status]")).not.toBeNull();
  };

  it("leads Health with asset condition in the status strip; contact and fact age stay in the data-sources panel", async () => {
    serve(recorded());
    mount("/sites/KOBO-001/health");
    await settledScreen();
    expectV69Panels("health");
    expect(q("[data-headline-card]")).toBeNull();
    expect(expectStateLineVisible(strip())).toBe("Asset condition cannot yet be judged");
    expect(strip().querySelector("[data-product-status-as-of]")?.textContent).toMatch(/^As of \d{1,2} \w{3} \d{4}, \d{2}:\d{2} UTC$/);
    expect(strip().querySelector("[data-product-status-scope]")?.textContent).toContain("1 configured battery");
    // Contact never leads and never decides condition.
    expect(strip().textContent).not.toMatch(/contact|gateway/i);
    expectOneStateLine();
    const sources = panelTitled(SOURCES);
    expect(sources.contains(contact())).toBe(true);
    expect(contactLabel()).toBe("Some gateways are not in contact.");
    expect(contact().getAttribute("data-health-contact-tone")).toBe("limited");
    // Contact and fact age are separate columns: old facts with a fresh receipt read as in contact, but old.
    const delayed = q('[data-health-gateway="s7-delayed-old"]') as HTMLElement;
    expect(delayed.children[1].textContent).toBe("Current · 5 s ago");
    expect(delayed.querySelector("[data-health-quality]")?.textContent).toBe("Old");
    expect(delayed.querySelector("[data-health-facts]")).toBeNull();
    expect((q('[data-health-reported="s7-delayed-old"] [data-health-facts]') as HTMLElement).textContent).toContain("Old: observed 6 h ago");
    expect((q('[data-health-gateway="s7-clock-offset"] [data-health-quality]') as HTMLElement).textContent).toBe("Unknown age");
    expect(sources.textContent).not.toMatch(/healthy|good condition/i);
    w1("health KOBO-001 (W1)");
    // One disclosure per panel: the data-sources panel keeps only its closed technical details.
    expect(sources.querySelectorAll("details")).toHaveLength(1);
    expect(panelTitled("Physical asset condition").querySelectorAll("details")).toHaveLength(0);
  });

  it("states no reporting gateway on KOBO-002 with no zero counts, and keeps the state line visible", async () => {
    serve(recorded());
    mount("/sites/KOBO-002/health");
    await settledScreen();
    expectV69Panels("health");
    expect(expectStateLineVisible(strip())).toBe("Asset condition cannot yet be judged");
    expect(contactLabel()).toBe("No gateway is reporting.");
    expect(contact().textContent).toContain("No gateway is enabled");
    expect(qa("[data-value-bar]")).toHaveLength(0);
    expect(main().textContent).not.toMatch(/\b0 (in contact|recent)\b/);
    w1("health KOBO-002 (W1)");
  });

  describe("W1-UX-06: selected-gateway old and unknown-age lines, unrecognised and zero-enabled summaries (D-2026-10-17-w1-ux-06)", () => {
    const clone = (served: Served): any => JSON.parse(JSON.stringify(served));
    const selected = () => q('[data-health-selected="found"]') as HTMLElement;
    const state = () => selected().querySelector("[data-health-selected-state]")?.textContent;

    it("in contact with an old, trusted report: the selected line says so outside the disclosure; the age is shown separately", async () => {
      serve(recorded());
      mount(`/sites/KOBO-001/health?gateway=${gatewayRow("s7-delayed-old").gateway_id}`);
      await settledScreen();
      expectV69Panels("health");
      expect(state()).toBe("In contact; its latest report is old");
      expect(selected().getAttribute("data-health-selected-tone")).toBe("limited");
      const sentence = selected().querySelector("[data-health-selected-sentence]")?.textContent ?? "";
      expect(sentence).toContain("The server received this gateway's report within its reporting interval");
      expect(sentence).toContain("This is not equipment condition.");
      expect(selected().textContent).toContain("Old: observed 6 h ago");
      expect(selected().closest("details")).toBeNull();
    });

    it("in contact with an untrusted clock: the report's age cannot be confirmed, never old", async () => {
      serve(recorded());
      mount(`/sites/KOBO-001/health?gateway=${gatewayRow("s7-clock-offset").gateway_id}`);
      await settledScreen();
      expect(state()).toBe("In contact; its latest report's age cannot be confirmed");
      expect(state()).not.toMatch(/is old/);
      expect(selected().querySelector("[data-health-selected-sentence]")?.textContent).toContain("cannot be confirmed");
    });

    it("in contact with a recent report stays plain In contact", async () => {
      serve(recorded());
      mount(`/sites/KOBO-001/health?gateway=${gatewayRow("s7-current").gateway_id}`);
      await settledScreen();
      expect(state()).toBe("In contact");
    });

    it("an unrecognised Health summary code says contact cannot be explained, whatever the enabled count", async () => {
      const odd = clone(C.health_kobo001);
      odd.body.summary.status = "SOMETHING_NEW";
      for (const g of odd.body.gateways) {
        g.contact.status = "CURRENT";
        g.reported_facts = { ...gatewayRow("s7-current").reported_facts };
      }
      serve(recorded({ "/api/sites/KOBO-001/source-health": odd }));
      mount("/sites/KOBO-001/health");
      await settledScreen();
      expect(contactLabel()).toBe("Contact state not recognised.");
      expect(contact().textContent).toContain("not recognised");
      expect(main().textContent).not.toMatch(/All \d+ enabled gateways|Every enabled gateway is in contact/);
      expect(defaultReading()).not.toContain("SOMETHING_NEW");
      expect(q('[data-disclosure="site-health-technical"]')?.textContent).toContain("SOMETHING_NEW");
    });

    it("zero enabled gateways: the recognised no-source states keep their own messages; any other state is non-positive", async () => {
      // All gateways disabled (recognised NO_REGISTERED_SOURCE / NO_ENABLED_GATEWAY).
      serve(recorded());
      mount("/sites/KOBO-002/health");
      await settledScreen();
      expect(contactLabel()).toBe("No gateway is reporting.");
      expect(contact().textContent).toContain("No gateway is enabled");
      cleanup();
      // None registered (recognised NO_REGISTERED_SOURCE / NO_REGISTERED_GATEWAY): kept distinct from all disabled.
      const none = clone(C.health_kobo002);
      none.body.summary.reason = "NO_REGISTERED_GATEWAY";
      none.body.summary.disabled_gateway_count = 0;
      none.body.gateways = [];
      serve(recorded({ "/api/sites/KOBO-002/source-health": none }));
      mount("/sites/KOBO-002/health");
      await settledScreen();
      expect(contact().textContent).toContain("No gateway is registered");
      expectV69Panels("health");
      cleanup();
      // Zero enabled under any other summary code: never "All 0 enabled gateways".
      const zero = clone(C.health_kobo002);
      zero.body.summary.status = "ALL_CURRENT";
      zero.body.summary.reason = null;
      serve(recorded({ "/api/sites/KOBO-002/source-health": zero }));
      mount("/sites/KOBO-002/health");
      await settledScreen();
      expect(contactLabel()).toBe("Gateway contact cannot be confirmed.");
      expect(main().textContent).not.toMatch(/All 0 enabled/);
      // W1-UX-06 phase-1 review L1: non-positive, with a next step, and visible.
      expect(main().textContent).not.toMatch(/Every enabled gateway is in contact/);
      expect(contact().textContent).toContain("no enabled gateway");
      expect(contact().textContent).toContain("Check that the site's gateway is registered and enabled.");
      expect(contact().closest("details")).toBeNull();
    });
  });

  it("selected gateway: never received keeps its line visible; IDs stay in the closed technical disclosure (S7-01b L3)", async () => {
    serve(recorded());
    const target = gatewayRow("s7-never-received");
    mount(`/sites/KOBO-001/health?gateway=${target.gateway_id}`);
    await settledScreen();
    expect(q('[data-health-selected="found"] [data-health-selected-state]')?.textContent).toBe("Never heard from");
    const references = q('[data-disclosure="site-health-technical"]') as HTMLDetailsElement;
    expect(references.open).toBe(false);
    expect(references.querySelector('[data-health-technical][aria-current="true"]')?.textContent).toContain(target.gateway_id);
    expect(defaultReading()).not.toContain(target.gateway_id);
    w1("health selected gateway (W1)");
  });

  it("an observed-after-receipt report shows Unknown age with its reason, never an age (S7-01b L1)", async () => {
    const doc = structuredClone(C.health_kobo001);
    const row = (doc.body.gateways as any[]).find((g) => g.gateway_external_id === "s7-current");
    row.reported_facts.reason = "OBSERVED_AFTER_RECEIPT";
    row.reported_facts.fact_age_seconds = 7;
    serve(recorded({ "/api/sites/KOBO-001/source-health": doc }));
    mount("/sites/KOBO-001/health");
    await settledScreen();
    expect((q('[data-health-gateway="s7-current"] [data-health-quality]') as HTMLElement).textContent).toBe("Unknown age");
    const facts = (q('[data-health-reported="s7-current"]') as HTMLElement).querySelector("[data-health-facts]") as HTMLElement;
    expect(facts.textContent).toBe("Unknown age: its reported time is later than the server received it");
    expect(facts.textContent).not.toMatch(/observed \d/);
    expect((q('[data-health-queue-row="s7-current"]') as HTMLElement).textContent).not.toMatch(/\b7 s\b/);
  });

  it("a refused Health read is stated inside the data-sources panel; the condition strip keeps its own state", async () => {
    const cases: [Served, string][] = [
      [C.health_unavailable, "This could not be read right now"],
      [{ status: 403, body: { detail: { code: "SITE_SCOPE_FORBIDDEN", message: "x" } } }, "This cannot be shown to you"],
      [C.health_unknown_site, "This record was not found"],
    ];
    for (const [answer, label] of cases) {
      serve(recorded({ "/api/sites/KOBO-001/source-health": answer }));
      mount("/sites/KOBO-001/health");
      await settledScreen();
      expectV69Panels("health");
      const gap = q('[data-health-read="refused"]') as HTMLElement;
      expect(panelTitled(SOURCES).contains(gap), label).toBe(true);
      expect(gap.textContent, label).toContain(label);
      expect(gap.textContent, label).toContain("this is not an empty result");
      expect(expectStateLineVisible(strip()), label).toBe("Asset condition cannot yet be judged");
      expect(q("[data-headline-card]"), label).toBeNull();
      cleanup();
      vi.unstubAllGlobals();
    }
    // A refused battery read: the strip states the refusal with no read time, and the condition panel holds the gap.
    serve(recorded({ "/api/sites/KOBO-001/battery": C.health_unavailable }));
    mount("/sites/KOBO-001/health");
    await settledScreen();
    expectV69Panels("health");
    expectRefusedStateLine(strip(), "This could not be read right now");
    expect(panelTitled("Physical asset condition").querySelector('[data-health-read="refused"]')).not.toBeNull();
    expect(qa("[data-health-gateway]").length).toBeGreaterThan(0);
  });

  it("leads the battery page with 'cannot yet be judged' in the strip, the missing inputs and separate rating and exposure facts", async () => {
    serve(recorded());
    mount(`/sites/KOBO-001/assets/${KOBO_001_ASSET}`);
    await settledScreen();
    const body = C.battery_detail_kobo001.body;
    expectV69Panels("asset");
    expect(q("[data-headline-card]")).toBeNull();
    expect(expectStateLineVisible(strip())).toBe("Cannot yet be judged");
    expect(strip().textContent).toContain("Capacity: unverified");
    expectOneStateLine();
    const interpretation = panelTitled("Interpretation and next evidence");
    const items = Array.from(interpretation.querySelectorAll("[data-battery-missing]"));
    expect(items).toHaveLength(body.physical_condition.missing_causal_inputs.length);
    expect(items.map((i) => (i.textContent ?? "").endsWith(" · missing") ? "MISSING" : "OTHER")).toEqual(
      body.physical_condition.missing_causal_inputs.map((i: any) => (i.status === "MISSING" ? "MISSING" : "OTHER")),
    );
    expect(interpretation.textContent).toContain("Temperature history");
    expect(interpretation.textContent).toContain("Battery condition cannot yet be judged.");
    expect(q(".notice")?.textContent).toContain("No warranty position and no remaining-life estimate are stated.");
    // Rating and exposure stay separate facts beside it; unsupported exposure is a stated gap, never zero.
    expect((q('[data-battery-metric="rating"]') as HTMLElement).textContent).toContain("200 kWh");
    expect((q('[data-battery-metric="reserve"]') as HTMLElement).textContent).toContain("Not available");
    expect((q('[data-battery-metric="power"]') as HTMLElement).textContent).toContain("Not available");
    expect(panelTitled("Observed reserve and power exposure").querySelector('[data-gap-id="G-asset-battery-exposure"]')).not.toBeNull();
    expect(panelTitled("Condition evidence and its limits").querySelector('[data-gap-id="G-asset-remaining-life"]')).not.toBeNull();
    const boundary = panelTitled("Condition evidence and its limits");
    expect(boundary.querySelectorAll("[data-battery-boundary]")).toHaveLength(4);
    const references = boundary.querySelector('[data-disclosure="site-battery-asset-technical"]') as HTMLDetailsElement;
    expect(references.open).toBe(false);
    expect(references.textContent).toContain(body.asset.asset_id);
    expect(defaultReading()).not.toContain(body.asset.asset_id);
    w1("battery KOBO-001 (W1)");
    // One disclosure per panel: only the claim-boundary panel holds the closed technical details.
    expect(boundary.querySelectorAll("details")).toHaveLength(1);
    expect(panelTitled("Observed reserve and power exposure").querySelectorAll("details")).toHaveLength(0);
    expect(interpretation.querySelectorAll("details")).toHaveLength(0);
    // The refused-read disclosure keeps plain words (scanned where one exists: the battery refusal below).
  });

  it("refuses a 409 configuration basis and a condition other than Unknown, with a state line, panel gaps and no condition (S7-01b L4)", async () => {
    const path = `/api/sites/KOBO-001/assets/${KOBO_001_ASSET}/battery`;
    const known = structuredClone(C.battery_detail_kobo001);
    known.body.physical_condition.status = "GOOD";
    const cases: [string, Served, RegExp][] = [
      [
        "409 derived",
        { status: 409, body: { detail: { code: "FOUNDATION_BASIS_UNAVAILABLE", message: "x" } } },
        /could not be read consistently/,
      ],
      ["condition not UNKNOWN (derived)", known, /could not be read/],
    ];
    for (const [name, answer, text] of cases) {
      serve(recorded({ [path]: answer }));
      mount(`/sites/KOBO-001/assets/${KOBO_001_ASSET}`);
      await settledScreen();
      const refused = q('[data-health-read="refused"]') as HTMLElement;
      expect(refused, name).not.toBeNull();
      expect(refused.textContent, name).toMatch(text);
      expectRefusedStateLine(strip(), "This could not be read right now");
      expectV69Panels("asset");
      expect(qa("[data-battery-gap]"), name).toHaveLength(3);
      expect(q("[data-battery-condition]"), name).toBeNull();
      expect(q("[data-headline-card]"), name).toBeNull();
      expect(defaultReading(), name).not.toMatch(/GOOD|good condition/);
      disclosureOf(refused, `battery refusal disclosure (${name})`);
      cleanup();
      vi.unstubAllGlobals();
    }
  });
});

describe("W1-F5a fix round: one row per gateway, attention first, state said once", () => {
  it("lists all gateways once, attention rows first, with devices counted and no device rows in the table", async () => {
    serve(recorded());
    mount("/sites/KOBO-001/health");
    await settledScreen();
    const rows = qa("[data-health-gateway]");
    expect(rows).toHaveLength(9);
    expect(qa("[data-health-gateway] [data-health-quality] .badge")).toHaveLength(9);
    expect(qa("tbody tr [data-health-source]")).toHaveLength(0);
    expect(qa("[data-health-gateway]").some((r) => r.closest("[data-disclosure]") !== null)).toBe(false);
    expect((q('[data-health-gateway="s7-current"] th small') as HTMLElement).textContent).toMatch(/^\d+ devices?$/);
    // Rows that need attention come before the current ones; the disabled gateway is last.
    const order = rows.map((r) => r.getAttribute("data-health-gateway"));
    expect(order.indexOf("s7-stale-cadence")).toBeLessThan(order.indexOf("s7-current"));
    expect(order.indexOf("s7-never-received")).toBeLessThan(order.indexOf("s7-current"));
    expect(order.indexOf("s7-delayed-old")).toBeLessThan(order.indexOf("s7-current"));
    expect(order[order.length - 1]).toBe("edge-kobo-001");
  });

  it("states the limit, when it stopped and the registration in the selected-gateway view", async () => {
    serve(recorded());
    const stale = gatewayRow("s7-stale-cadence");
    mount(`/sites/KOBO-001/health?gateway=${stale.gateway_id}`);
    await settledScreen();
    const selected = q('[data-health-selected="found"]') as HTMLElement;
    expect(selected.textContent).toContain("Stale: nothing received for 10 min (limit 1 min)");
    expect(selected.textContent).toContain("when it stopped is not known");
    expect(selected.textContent).toContain("Queue, as last reported");
    cleanup();
    const disabled = gatewayRow("edge-kobo-001");
    mount(`/sites/KOBO-001/health?gateway=${disabled.gateway_id}`);
    await settledScreen();
    expect((q('[data-health-selected="found"]') as HTMLElement).textContent).toContain("Disabled (not counted)");
  });

  it("says the Unknown-not-normal-nor-faulty sentence once on Health and once on the battery page", async () => {
    const said = (text: string) => (text.match(/does not mean normal/g) ?? []).length;
    serve(recorded());
    mount("/sites/KOBO-001/health");
    await settledScreen();
    expect(said(main().textContent ?? "")).toBe(1);
    expect((q(".status-strip") as HTMLElement).textContent).toContain("Unknown does not mean normal, and it does not mean faulty.");
    cleanup();
    mount(`/sites/KOBO-001/assets/${KOBO_001_ASSET}`);
    await settledScreen();
    expect(said(main().textContent ?? "")).toBe(1);
    expect((q(".status-strip") as HTMLElement).textContent).toContain("does not mean normal");
  });
});