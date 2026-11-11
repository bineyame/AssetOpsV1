import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { FuelBalanceClient, FuelNightBody, FuelNightSummary, FuelNightsBody } from "../fuelBalanceClient";
import type { FuelRead, MiniDepthClient, MiniRead } from "../miniDepthClient";
import { FUEL_NOTICE, MiniFuel } from "../MiniPerformance";
import nightsSource from "../MiniFuelNights.tsx?raw";
import findingSource from "../SiteFuelFinding.tsx?raw";
import { LinkedMemoryRouter } from "../../test/refLinks";
import { settledScreen } from "../../test/settled";

/*
 * DIESEL-K5 F1-F5 (build sheet DIESEL-1 §9l.2): the Fuel page's night mode renders the server's strings verbatim, the
 * night selector carries `?night=`, the records table and its empty text, the Finding panel, and hour mode is
 * unchanged with `mode: "NONE"`, a failed nights read or no fuel-balance client.
 */

afterEach(cleanup);

const CODE = "KISIWA-001";
const TZ = "Africa/Dar_es_Salaam";
const WINDOW = { from: "2026-10-04T15:00:00Z", to: "2026-10-04T16:00:00Z", known_at: null };
const PROV = { source_provenance: null, selected_source_provenance: { classification: "REGISTERED_SIMULATION" }, pending_source_provenance: null };

const summary = (night_date: string, label: string, state: string, status: string): FuelNightSummary => ({
  night_date,
  label,
  state,
  status,
  tone: state === "UNEXPLAINED" ? "amber" : "neutral",
  revision: 1,
});
const NIGHTS = [
  summary("2026-10-03", "Night of 3 Oct · 6 pm to noon", "WITHIN_MARGIN", "Fuel balance: accounted for within the margin"),
  summary("2026-10-04", "Night of 4 Oct · 6 pm to noon", "UNEXPLAINED", "Fuel balance: unexplained fuel"),
  summary("2026-10-06", "Night of 6 Oct · 6 pm to noon", "WITHIN_MARGIN", "Fuel balance: accounted for within the margin"),
];

function night(date: string, over: Partial<FuelNightBody> = {}): FuelNightBody {
  const s = NIGHTS.find((n) => n.night_date === date) ?? NIGHTS[1];
  return {
    ...s,
    site_code: CODE,
    time_zone: TZ,
    known_at: "2026-10-10T00:00:00+00:00",
    window_start: "2026-10-04T15:00:00+00:00",
    window_end: "2026-10-05T09:00:00+00:00",
    cards: [
      { key: "OPENING", label: "Opening evidence", value: "869.2 L", note: "Tank reading at 18:00", word: false },
      { key: "DELIVERIES", label: "Recorded deliveries", value: "None recorded", note: "Absence of record does not prove none occurred", word: true },
      { key: "USE", label: "Modelled expected use", value: "39.1–47.8 L", note: "Modelled: 122.3 kWh × 0.355 L/kWh, 10 % either way", word: false },
      { key: "RESIDUAL", label: "Residual", value: "95.7–144.3 L", note: "Above the 40 L the check flags", word: false },
    ],
    bars: [
      { key: "opening", label: "Opening tank", value_l: 869.215, text: "869.2 L" },
      { key: "deliveries", label: "+ Deliveries", value_l: null, text: "None recorded" },
      { key: "use", label: "− Modelled generator use", value_l: 47.771, text: "39.1–47.8 L" },
      { key: "closing", label: "− Closing tank", value_l: 705.787, text: "705.8 L" },
      { key: "residual", label: "= Unexplained", value_l: 144.343, text: "95.7–144.3 L" },
    ],
    bridge: [
      { term: "OPENING", label: "Opening inventory", value: "869.2 L", basis: "Tank reading at 18:00", treatment: "Declared sensor accuracy ±10 L", evidence_count: 1 },
      { term: "DELIVERIES", label: "Plus deliveries", value: "None recorded", basis: "No delivery record", treatment: "1 % allowance on each ticket", evidence_count: 0 },
      { term: "USE", label: "Less generator consumption", value: "39.1–47.8 L", basis: "Generator output × declared fuel coefficient", treatment: "Modelled range, not a fuel-meter reading", evidence_count: 3 },
      { term: "CLOSING", label: "Less closing inventory", value: "705.8 L", basis: "Tank reading at 12:00", treatment: "Declared sensor accuracy ±10 L", evidence_count: 1 },
      { term: "RESIDUAL", label: "Unexplained residual", value: "95.7–144.3 L", basis: "Opening + deliveries − use − closing", treatment: "Compared with the combined margin; never says why fuel left", evidence_count: 3 },
    ],
    notes: ["The tank sensor sent no readings from 00:45 to 02:30."],
    margin: "The range allows for the tank sensor's declared accuracy of 10 L at each reading, 10 % either way on the generator's modelled use, and 1 % on each recorded delivery.",
    records: [{ code: "REC-000004", kind: "Tank dip", when: "07:00, 5 Oct", volume: "706 L", occurred_at: "2026-10-05T04:00:00+00:00" }],
    records_empty: "No delivery or tank dip recorded this night",
    finding: null,
    finding_note: "Not available yet · the finding for this night has not been raised",
    provenance: PROV,
    links: { evidence: `/sites/${CODE}/evidence`, fuel_page: `/sites/${CODE}/performance/fuel?night=${date}` },
    ...over,
  } as FuelNightBody;
}

function fuelClient(nights: MiniRead<FuelNightsBody>, bodies: (date: string) => FuelNightBody = (d) => night(d)) {
  const client: FuelBalanceClient = {
    getNights: vi.fn(() => Promise.resolve(nights)),
    getNight: vi.fn((_code: string, date: string) => Promise.resolve({ status: "loaded" as const, value: bodies(date) })),
    getFuelFindings: vi.fn(() => Promise.resolve({ status: "loaded" as const, value: { site_code: CODE, rows: [] } })),
    getFuelFinding: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
  };
  return client;
}

const nightsBody = (mode: "NIGHTS" | "NONE", nights: FuelNightSummary[] = NIGHTS): MiniRead<FuelNightsBody> => ({
  status: "loaded",
  value: { site_code: CODE, mode, time_zone: TZ, known_at: "2026-10-10T00:00:00+00:00", nights: mode === "NONE" ? [] : nights, provenance: PROV },
});

/** A minimal hour-mode read (the W4-02 shape); only its rendering is compared. */
const HOUR = {
  schema_version: "w4-02.mini.v1",
  domain: "fuel",
  site: { id: "s", code: CODE, timezone: TZ },
  window: { from: WINDOW.from, to: WINDOW.to, known_at: "2026-10-07T00:00:00Z", bounds: "[from,to)" },
  currentness: { state: "CURRENT", job_state: "SETTLED", windows: [] },
  source_provenance: PROV.selected_source_provenance,
  selected_source_provenance: PROV.selected_source_provenance,
  pending_source_provenance: null,
  status: "UNKNOWN",
  coverage: null,
  cards: { opening_l: null, deliveries_l: null, expected_use_l: null, closing_l: null, residual_l: null },
  rows: [{ term: "RESIDUAL", basis: "MISSING", treatment: "MISSING", value: null, coverage: null, evidence_ids: [] }],
  limitations: [],
  basis: null,
  links: { dispatch: null, evidence: `/sites/${CODE}/evidence`, financials: null, actions: null },
} as unknown as FuelRead;

const miniClient = (): MiniDepthClient => ({
  getCapabilities: vi.fn(() => Promise.resolve({ status: "loaded" as const, value: [] })),
  getRenewable: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
  getService: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
  getFuel: vi.fn(() => Promise.resolve({ status: "loaded" as const, value: HOUR })),
  getBackup: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
});

let lastLocation = "";
function LocationProbe() {
  const location = useLocation();
  lastLocation = `${location.pathname}${location.search}`;
  return null;
}

function renderFuel(fuelBalance: FuelBalanceClient | undefined, path = `/sites/${CODE}/performance/fuel`) {
  return render(
    <LinkedMemoryRouter initialEntries={[path]}>
      <MiniFuel client={miniClient()} siteCode={CODE} timeZone={TZ} window={WINDOW} pageHref={(s) => `/x${s}`} fuelBalance={fuelBalance} />
      <LocationProbe />
    </LinkedMemoryRouter>,
  );
}

const flush = () => act(() => new Promise<void>((resolve) => setTimeout(resolve, 0)));

describe("DIESEL-K5 night mode", () => {
  it("F1: renders the server's strings verbatim, in the v69 order with the records table and the Finding panel", async () => {
    renderFuel(fuelClient(nightsBody("NIGHTS")));
    await screen.findByText("Night of 4 Oct · 6 pm to noon · Fuel balance: unexplained fuel", { selector: "option" });
    await screen.findByText("95.7–144.3 L", { selector: ".v69-metric__value" });
    await settledScreen();
    const text = document.body.textContent ?? "";
    for (const literal of [
      "Fuel balance: unexplained fuel",
      "The tank sensor sent no readings from 00:45 to 02:30.",
      "Modelled: 122.3 kWh × 0.355 L/kWh, 10 % either way",
      "Absence of record does not prove none occurred",
      "Compared with the combined margin; never says why fuel left",
      "07:00, 5 Oct",
      "706 L",
      "REC-000004",
      FUEL_NOTICE,
      "A residual is shown only when every term has a supported range. The range allows for the tank sensor's declared accuracy",
    ]) {
      expect(text).toContain(literal);
    }
    const headings = Array.from(document.querySelectorAll(".panel h2, .panel h3"), (h) => h.textContent);
    expect(headings).toEqual(["Fuel balance at a glance", "Balance bridge", "Deliveries and tank dips", "Finding for this night"]);
    expect(Array.from(document.querySelectorAll('[aria-labelledby="fuel-night-records-heading"] th, table[aria-labelledby="fuel-night-records-heading"] th'), (th) => th.textContent)).toEqual([
      "Time",
      "Record",
      "Volume",
      "Reference",
    ]);
    // no hour bar in night mode
    expect(document.querySelector("[data-mini-period]")).toBeNull();
  });

  it("F1: the night and fuel Finding components format no number in the browser", () => {
    for (const source of [nightsSource, findingSource]) {
      expect(source).not.toMatch(/toFixed|Intl\.NumberFormat|NUMBER\.format|toLocaleString/);
    }
  });

  it("F2: opens the latest night without ?night=, Previous/Next change the address and are disabled at the ends", async () => {
    const client = fuelClient(nightsBody("NIGHTS"));
    renderFuel(client);
    await screen.findByText("95.7–144.3 L", { selector: ".v69-metric__value" });
    expect(client.getNight).toHaveBeenLastCalledWith(CODE, "2026-10-06");
    const prev = screen.getByRole("button", { name: "Previous night" });
    const next = screen.getByRole("button", { name: "Next night" });
    expect(next).toBeDisabled();
    expect(prev).toBeEnabled();
    fireEvent.click(prev);
    await flush();
    expect(lastLocation).toBe(`/sites/${CODE}/performance/fuel?night=2026-10-04`);
    expect(client.getNight).toHaveBeenLastCalledWith(CODE, "2026-10-04");
    fireEvent.click(screen.getByRole("button", { name: "Previous night" }));
    await flush();
    expect(lastLocation).toBe(`/sites/${CODE}/performance/fuel?night=2026-10-03`);
    expect(screen.getByRole("button", { name: "Previous night" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Next night" }));
    await flush();
    expect(lastLocation).toBe(`/sites/${CODE}/performance/fuel?night=2026-10-04`);
  });

  it("F2: a reload with ?night= reopens that night", async () => {
    const client = fuelClient(nightsBody("NIGHTS"));
    renderFuel(client, `/sites/${CODE}/performance/fuel?night=2026-10-03`);
    await screen.findByText("95.7–144.3 L", { selector: ".v69-metric__value" });
    expect(client.getNight).toHaveBeenLastCalledWith(CODE, "2026-10-03");
    expect((screen.getByRole("combobox") as HTMLSelectElement).value).toBe("2026-10-03");
  });

  it("F3: the records table and its empty text", async () => {
    renderFuel(fuelClient(nightsBody("NIGHTS"), (d) => night(d, { records: [] })));
    await screen.findByText("No delivery or tank dip recorded this night");
    expect(document.querySelector('table[aria-labelledby="fuel-night-records-heading"]')).toBeNull();
  });

  it("F3: more than six records sit behind Show all", async () => {
    const many = Array.from({ length: 8 }, (_, i) => ({ code: `REC-00000${i}`, kind: "Tank dip", when: `0${i}:00, 5 Oct`, volume: "700 L", occurred_at: `2026-10-05T0${i}:00:00Z` }));
    renderFuel(fuelClient(nightsBody("NIGHTS"), (d) => night(d, { records: many })));
    await screen.findByText("Show all 8 records");
    expect(document.querySelectorAll("[data-fuel-record]")).toHaveLength(8);
  });

  it("F5: the Finding panel links the Finding, or states why there is none", async () => {
    const href = `/sites/${CODE}/fuel-findings/f-1`;
    renderFuel(
      fuelClient(nightsBody("NIGHTS"), (d) =>
        night(d, {
          finding: { finding_id: "f-1", title: "Unexplained fuel overnight", text: "About 95.7–144.3 L left the tank on the night of 4 Oct.", href },
          finding_note: null,
        }),
      ),
    );
    const link = await screen.findByRole("link", { name: "Unexplained fuel overnight" });
    expect(link).toHaveAttribute("href", href);
    expect(document.body.textContent).toContain("About 95.7–144.3 L left the tank on the night of 4 Oct.");
    cleanup();
    renderFuel(fuelClient(nightsBody("NIGHTS"), (d) => night(d, { finding_note: "No finding: the fuel was accounted for within the margin." })));
    await screen.findByText("No finding: the fuel was accounted for within the margin.");
    cleanup();
    renderFuel(fuelClient(nightsBody("NIGHTS")));
    await screen.findByText("Not available yet · the finding for this night has not been raised");
  });
});

describe("DIESEL-K5 F4: hour mode is unchanged", () => {
  async function hourDom(fuelBalance: FuelBalanceClient | undefined): Promise<string> {
    const { container, unmount } = renderFuel(fuelBalance);
    await screen.findByText("Fuel balance: Unknown");
    await settledScreen();
    await flush();
    const html = container.innerHTML;
    unmount();
    return html;
  }

  it("mode NONE, a failed nights read and no client render the same DOM; NIGHTS does not", async () => {
    const without = await hourDom(undefined);
    const none = await hourDom(fuelClient(nightsBody("NONE")));
    const failed = await hourDom(fuelClient({ status: "unavailable", message: null }));
    const refused = await hourDom(fuelClient({ status: "refused", httpStatus: 503, code: "FUEL_BALANCE_STORE_UNAVAILABLE", message: "x" }));
    expect(none).toBe(without);
    expect(failed).toBe(without);
    expect(refused).toBe(without);
    expect(without).toContain("data-mini-period");
    expect(without).not.toContain("data-fuel-nights");
    // the control: NIGHTS leaves hour mode
    renderFuel(fuelClient(nightsBody("NIGHTS")));
    await screen.findByText("95.7–144.3 L", { selector: ".v69-metric__value" });
    expect(document.querySelector("[data-mini-period]")).toBeNull();
    expect(document.querySelector("[data-fuel-nights]")).not.toBeNull();
  });
});

describe("PB-8: the Fuel tab shows loading, not hour mode, while the nights read is in flight", () => {
  it("no 'Fuel balance: Unknown' before the nights resolve, then the nights", async () => {
    let release: (v: MiniRead<FuelNightsBody>) => void = () => undefined;
    const pending = new Promise<MiniRead<FuelNightsBody>>((resolve) => {
      release = resolve;
    });
    const base = fuelClient(nightsBody("NIGHTS"));
    renderFuel({ ...base, getNights: vi.fn(() => pending) } as FuelBalanceClient);
    await flush();
    expect(screen.queryByText("Fuel balance: Unknown")).toBeNull();
    expect(document.querySelector("[data-mini-period]")).toBeNull();
    expect(screen.getByRole("status").textContent).toContain("Loading");
    release(nightsBody("NIGHTS"));
    await screen.findByText("95.7–144.3 L", { selector: ".v69-metric__value" });
    expect(screen.queryByText("Fuel balance: Unknown")).toBeNull();
  });
});
