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
    expect(summary.textContent).toContain("Gateway contact: not all current");
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
    expect(row("s7-current").textContent).toContain("Current: received 5 s ago");
    expect(row("s7-stale-cadence").textContent).toContain("Stale: nothing received for 10 min (limit 1 min)");
    expect(row("s7-stale-cadence").textContent).toContain("when it stopped is not known");
    expect(row("s7-delayed-old").textContent).toContain("Current: received 5 s ago");
    expect(row("s7-delayed-old").textContent).toContain("Old: observed 6 h ago; it reached the server 6 h after");
    const clock = row("s7-clock-offset").textContent ?? "";
    expect(clock).toContain("Unknown age: the gateway's clock is off by 95 s, more than the 5 s allowed");
    expect(row("s7-never-received").textContent).toContain("Never received");
    expect(row("s7-never-received").textContent).toContain("Nothing received yet");
    // The disabled import gateway: listed, marked and not counted.
    const disabled = row("edge-kobo-001");
    expect(disabled.getAttribute("data-health-registration")).toBe("DISABLED");
    expect(disabled.textContent).toContain("Disabled");
    expect(disabled.textContent).toContain("Disabled, not counted.");
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
    const clock = (q('[data-health-gateway="s7-clock-offset"]') as HTMLElement).textContent ?? "";
    expect(clock).not.toMatch(/reached the server/);
    expect(clock).not.toMatch(/-\d+\s?(s|min|h|d)\b/);
    expect((q('[data-health-gateway="s7-delayed-old"]') as HTMLElement).textContent).toContain("it reached the server 6 h after");
  });

  it("keeps queue, storage and device contact as last reported, in separately qualified sections", async () => {
    serve(recorded());
    mount("/sites/KOBO-001/health");
    await settledScreen();
    expect(screen.getByRole("heading", { name: "Queue and storage, as last reported" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Device contact reported by gateways" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Battery condition" })).toBeTruthy();
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
    const battery = q(`[data-health-battery="${KOBO_001_ASSET}"]`) as HTMLElement;
    expect(battery.textContent).toContain("Unknown");
    expect(battery.querySelector("a")?.getAttribute("href")).toBe(`/sites/KOBO-001/assets/${KOBO_001_ASSET}`);
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
    expect(screen.getByRole("heading", { name: "Gateway s7-clock-offset" })).toBeTruthy();
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
  });

  it("states no enabled gateway on the second Site instead of a healthy zero", async () => {
    serve(recorded());
    mount("/sites/KOBO-002/health");
    await settledScreen();
    const summary = q("[data-health-summary]") as HTMLElement;
    expect(summary.getAttribute("data-health-summary-reason")).toBe("NO_ENABLED_GATEWAY");
    expect(summary.textContent).toContain("Gateway contact: no enabled gateway");
    expect(summary.textContent).toContain("No gateway is enabled for this site, so nothing is known about contact.");
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
      expect(qa("table").length).toBeGreaterThanOrEqual(4);
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
    expect((q('[data-battery-metric="charge"]') as HTMLElement).textContent).toContain("Not shown");
    expect((q('[data-battery-metric="channels"]') as HTMLElement).textContent).toContain("1 connected");
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
    expect(q('[data-health-battery="NOT_CONFIGURED"]')?.textContent).toContain("Unknown (not configured)");
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
      cleanup();
      vi.unstubAllGlobals();
    }
  });
});

describe("W1-UX-05: Health and battery answer cards", () => {
  const card = (name: string) => q(`[data-headline-card="${name}"]`) as HTMLElement;
  const w1 = (page: string) => {
    const { violations, scanned } = scanProductVocabulary(main(), page, { set: "w1" });
    expect(scanned).toBeGreaterThan(5);
    expect(violations, describeViolations(violations)).toEqual([]);
  };
  /** A refused read has no read instant, so its bound is the shared "As of: time not recorded" (never now). */
  const expectRefusedStateLine = (panel: HTMLElement, label: string) => {
    expect(expectStateLineVisible(panel)).toBe(label);
    expect(panel.querySelector("[data-product-status-as-of]")?.textContent).toBe("As of: time not recorded");
  };
  const disclosureOf = (el: HTMLElement, page: string) => {
    const result = scanDisclosureVocabulary(el, page);
    expect(result.disclosures).toBe(1);
    expect(result.scanned).toBeGreaterThan(2);
    expect(result.violations, describeViolations(result.violations)).toEqual([]);
  };

  it("leads Health with which source needs attention, contact and fact age in separate lanes, W1 words", async () => {
    serve(recorded());
    mount("/sites/KOBO-001/health");
    await settledScreen();
    const answer = card("site-health");
    expect(answer.querySelector(".headline-card__question")?.textContent).toBe("Which source needs attention?");
    expect(answer.querySelector(".headline-card__headline")?.textContent).toMatch(/^\d of 8 enabled gateways need attention$/);
    expect(expectStateLineVisible(answer)).toBe("Some gateways are not in contact");
    expect(answer.querySelector("[data-product-status-as-of]")?.textContent).toMatch(/^As of \d{1,2} \w{3} \d{4}, \d{2}:\d{2} UTC$/);
    // Two lanes: contact by server receipt, and how old the reported facts are.
    const lanes = answer.querySelectorAll("[data-health-lanes] [data-value-bars]");
    expect(Array.from(lanes).map((l) => l.querySelector("figcaption")?.textContent)).toEqual([
      "Contact: when the server last heard from each gateway",
      "Reports: how old the latest reported facts are",
    ]);
    // Old facts with a fresh receipt: in contact, but its report is old, so it needs attention.
    const delayed = answer.querySelector('[data-health-attention-gateway="s7-delayed-old"]') as HTMLElement;
    expect(delayed.textContent).toContain("in contact; its latest report is old");
    expect(answer.querySelector('[data-health-attention-gateway="s7-current"]')).toBeNull();
    expect(answer.querySelector('[data-health-attention-gateway="s7-never-received"]')?.textContent).toContain("never heard from");
    expect(answer.querySelector('[data-health-attention-gateway="s7-clock-offset"]')?.textContent).toContain(
      "age of its latest report not known",
    );
    expect(answer.textContent).not.toMatch(/healthy|good condition/i);
    w1("health KOBO-001 (W1)");
    disclosureOf(answer, "health answer disclosure");
  });

  it("states no reporting gateway on KOBO-002 with no zero bars, and keeps the state line visible", async () => {
    serve(recorded());
    mount("/sites/KOBO-002/health");
    await settledScreen();
    const answer = card("site-health");
    expect(expectStateLineVisible(answer)).toBe("No gateway is reporting");
    expect(answer.querySelector(".product-status__sentence")?.textContent).toContain("No gateway is enabled");
    expect(answer.querySelectorAll("[data-value-bar]")).toHaveLength(0);
    expect(answer.textContent).not.toMatch(/\b0 (in contact|recent)\b/);
    w1("health KOBO-002 (W1)");
  });

  describe("W1-UX-06: selected-gateway old and unknown-age lines, unrecognised and zero-enabled headlines (D-2026-10-17-w1-ux-06)", () => {
    const clone = (served: Served): any => JSON.parse(JSON.stringify(served));
    const selected = () => (q("#site-health-selected-heading") as HTMLElement).closest("section") as HTMLElement;

    it("in contact with an old, trusted report: the state line says so outside the disclosure; the age is shown separately", async () => {
      serve(recorded());
      mount(`/sites/KOBO-001/health?gateway=${gatewayRow("s7-delayed-old").gateway_id}`);
      await settledScreen();
      const panel = selected();
      expect(expectStateLineVisible(panel)).toBe("In contact; its latest report is old");
      expect(panel.querySelector("[data-product-status]")?.getAttribute("data-product-status")).toBe("limited");
      const sentence = panel.querySelector(".product-status__sentence")?.textContent ?? "";
      expect(sentence).toContain("The server received this gateway's report within its reporting interval");
      expect(sentence).toContain("This is not equipment condition.");
      expect(panel.textContent).toContain("Old: observed 6 h ago");
    });

    it("in contact with an untrusted clock: the report's age cannot be confirmed, never old", async () => {
      serve(recorded());
      mount(`/sites/KOBO-001/health?gateway=${gatewayRow("s7-clock-offset").gateway_id}`);
      await settledScreen();
      const panel = selected();
      expect(expectStateLineVisible(panel)).toBe("In contact; its latest report's age cannot be confirmed");
      expect(panel.querySelector("[data-product-status-label]")?.textContent).not.toMatch(/is old/);
      expect(panel.querySelector(".product-status__sentence")?.textContent).toContain("cannot be confirmed");
    });

    it("in contact with a recent report stays plain In contact", async () => {
      serve(recorded());
      mount(`/sites/KOBO-001/health?gateway=${gatewayRow("s7-current").gateway_id}`);
      await settledScreen();
      expect(expectStateLineVisible(selected())).toBe("In contact");
    });

    it("an unrecognised Health summary code headlines that contact cannot be confirmed, whatever the enabled count", async () => {
      const odd = clone(C.health_kobo001);
      odd.body.summary.status = "SOMETHING_NEW";
      for (const g of odd.body.gateways) {
        g.contact.status = "CURRENT";
        g.reported_facts = { ...gatewayRow("s7-current").reported_facts };
      }
      serve(recorded({ "/api/sites/KOBO-001/source-health": odd }));
      mount("/sites/KOBO-001/health");
      await settledScreen();
      const answer = card("site-health");
      expect(answer.querySelector(".headline-card__headline")?.textContent).toBe("Gateway contact cannot be confirmed");
      expect(expectStateLineVisible(answer)).toBe("Contact state not recognised");
      expect(answer.textContent).not.toMatch(/All \d+ enabled gateways/);
      expect(answer.querySelector("[data-exact-references]")?.textContent).toContain("SOMETHING_NEW");
    });

    it("zero enabled gateways: the recognised no-source states keep their own messages; any other state is non-positive", async () => {
      // All gateways disabled (recognised NO_REGISTERED_SOURCE / NO_ENABLED_GATEWAY).
      serve(recorded());
      mount("/sites/KOBO-002/health");
      await settledScreen();
      let answer = card("site-health");
      expect(answer.querySelector(".headline-card__headline")?.textContent).toBe("No gateway is reporting, so nothing is known about this site's sources");
      expect(answer.querySelector(".product-status__sentence")?.textContent).toContain("No gateway is enabled");
      cleanup();
      // None registered (recognised NO_REGISTERED_SOURCE / NO_REGISTERED_GATEWAY): kept distinct from all disabled.
      const none = clone(C.health_kobo002);
      none.body.summary.reason = "NO_REGISTERED_GATEWAY";
      none.body.summary.disabled_gateway_count = 0;
      none.body.gateways = [];
      serve(recorded({ "/api/sites/KOBO-002/source-health": none }));
      mount("/sites/KOBO-002/health");
      await settledScreen();
      answer = card("site-health");
      expect(answer.querySelector(".product-status__sentence")?.textContent).toContain("No gateway is registered");
      cleanup();
      // Zero enabled under any other summary code: never "All 0 enabled gateways".
      const zero = clone(C.health_kobo002);
      zero.body.summary.status = "ALL_CURRENT";
      zero.body.summary.reason = null;
      serve(recorded({ "/api/sites/KOBO-002/source-health": zero }));
      mount("/sites/KOBO-002/health");
      await settledScreen();
      answer = card("site-health");
      expect(answer.querySelector(".headline-card__headline")?.textContent).toBe("Gateway contact cannot be confirmed");
      expect(answer.textContent).not.toMatch(/All 0 enabled/);
      // W1-UX-06 phase-1 review L1: the state line is non-positive too, with a next step, and stays visible.
      expect(expectStateLineVisible(answer)).toBe("Gateway contact cannot be confirmed");
      expect(answer.textContent).not.toMatch(/Every enabled gateway is in contact/);
      expect(answer.querySelector(".product-status__sentence")?.textContent).toContain("no enabled gateway");
      expect(answer.querySelector("[data-product-status]")?.textContent).toContain("Check that the site's gateway is registered and enabled.");
    });
  });

  it("selected gateway: never received keeps its state line visible; IDs move to the closed disclosure (S7-01b L3)", async () => {
    serve(recorded());
    const target = gatewayRow("s7-never-received");
    mount(`/sites/KOBO-001/health?gateway=${target.gateway_id}`);
    await settledScreen();
    const panel = (q("#site-health-selected-heading") as HTMLElement).closest("section") as HTMLElement;
    expect(expectStateLineVisible(panel)).toBe("Never heard from");
    const references = panel.querySelector('[data-disclosure="site-health-selected-references"]') as HTMLDetailsElement;
    expect(references.open).toBe(false);
    expect(references.textContent).toContain(target.gateway_id);
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
    const facts = (q('[data-health-gateway="s7-current"]') as HTMLElement).querySelector("[data-health-facts]") as HTMLElement;
    expect(facts.textContent).toBe("Unknown age: its reported time is later than the server received it");
    expect(facts.textContent).not.toMatch(/observed \d/);
    expect(card("site-health").querySelector('[data-health-attention-gateway="s7-current"]')?.textContent).toContain(
      "age of its latest report not known",
    );
  });

  it("a refused Health read keeps a plain state line and its scope, never an empty site", async () => {
    const cases: [Served, string][] = [
      [C.health_unavailable, "This could not be read right now"],
      [{ status: 403, body: { detail: { code: "SITE_SCOPE_FORBIDDEN", message: "x" } } }, "This cannot be shown to you"],
      [C.health_unknown_site, "This record was not found"],
    ];
    for (const [answer, label] of cases) {
      serve(recorded({ "/api/sites/KOBO-001/source-health": answer }));
      mount("/sites/KOBO-001/health");
      await settledScreen();
      const panel = (q('[data-health-read="refused"]') as HTMLElement).closest("section") as HTMLElement;
      expectRefusedStateLine(panel, label);
      expect(q('[data-headline-card="site-health"]'), label).toBeNull();
      cleanup();
      vi.unstubAllGlobals();
    }
  });

  it("leads the battery page with 'cannot yet be judged', the missing inputs and separate rating and charge facts", async () => {
    serve(recorded());
    mount(`/sites/KOBO-001/assets/${KOBO_001_ASSET}`);
    await settledScreen();
    const body = C.battery_detail_kobo001.body;
    const answer = card("battery-condition");
    expect(answer.querySelector(".headline-card__headline")?.textContent).toBe("Battery condition: cannot yet be judged");
    expect(expectStateLineVisible(answer)).toBe("Cannot yet be judged");
    const steps = Array.from(answer.querySelectorAll("[data-step]"));
    expect(steps).toHaveLength(body.physical_condition.missing_causal_inputs.length);
    expect(steps.map((s) => s.getAttribute("data-step"))).toEqual(
      body.physical_condition.missing_causal_inputs.map((i: any) => (i.status === "MISSING" ? "waiting" : "not-known")),
    );
    expect(answer.textContent).toContain("Temperature history");
    expect(answer.textContent).toContain("No remaining life, warranty position or replacement date is stated.");
    // Rating and charge stay separate facts beside it.
    expect((q('[data-battery-metric="rating"]') as HTMLElement).textContent).toContain("200 kWh");
    expect((q('[data-battery-metric="charge"]') as HTMLElement).textContent).toContain("Not shown");
    const references = answer.querySelector("details[data-exact-references]") as HTMLDetailsElement;
    expect(references.textContent).toContain(body.asset.asset_id);
    expect(defaultReading()).not.toContain(body.asset.asset_id);
    w1("battery KOBO-001 (W1)");
    disclosureOf(answer, "battery answer disclosure");
  });

  it("refuses a 409 configuration basis and a condition other than Unknown, with a state line and no condition (S7-01b L4)", async () => {
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
      expectRefusedStateLine(refused.closest("section") as HTMLElement, "This could not be read right now");
      expect(q("[data-battery-condition]"), name).toBeNull();
      expect(q('[data-headline-card="battery-condition"]'), name).toBeNull();
      expect(defaultReading(), name).not.toMatch(/GOOD|good condition/);
      cleanup();
      vi.unstubAllGlobals();
    }
  });
});
