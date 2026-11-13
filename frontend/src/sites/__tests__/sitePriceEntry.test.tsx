import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LinkedMemoryRouter as MemoryRouter } from "../../test/refLinks";
import { settledScreen } from "../../test/settled";
import { SitePricesFrame } from "../../shell/SitePricesFrame";
import { SITE_PRICES_ROUTE_PATH } from "../../shell/operatorSiteRoutes";
import { PRICE_ENTRY_WORDS } from "../SitePriceEntry";
import {
  createPriceEntryClient,
  type PriceEntryClient,
  type PriceEntryDryRun,
  type PriceEntryRequest,
  type PriceEntryResult,
  type PriceEntrySaved,
} from "../priceEntryClient";
import type { PriceEntryBlock, PricePage, PricePageClient, PriceRowBody } from "../pricePageClient";
import type { SiteDetailClient } from "../siteDirectoryClient";

/** PR-3 form half (rev 5 §5.3 UI and honest states; owner defaults 6-9). */

const ENTRY_SIGN_IN = "Prices saved here are recorded as entered by site admin until sign-in is available.";
const OFF_SIGN_IN = "Prices are set by your AssetOps administrator until sign-in is available.";

const DIESEL: PriceRowBody = {
  key: "diesel_price_per_litre",
  noun: "diesel price",
  label: "Diesel price",
  detail: "backup generator fuel",
  stored: true,
  state: "SET",
  not_set_text: null,
  note: null,
  current: {
    revision_id: "r1",
    value: "1.2500",
    currency: "USD",
    unit: "currency/L",
    value_text: "1.25 USD per litre",
    amount_text: "1.25",
    per_text: "USD per litre",
    basis_text: "An estimate",
    source_reference: null,
    applies_from_text: "1 Jan 2026",
    applies_until_text: null,
    set_by_label: "AssetOps administrator",
    recorded_text: "recorded 1 Jan 2026, 10:00",
  },
  used_by: { text: "Fuel cost", detail: "Backup running days" },
  history_title: "History of the diesel price · 1 version",
  history: [
    {
      revision_id: "r1",
      revision_no: 1,
      change_kind: "INITIAL",
      headline: "First price from 1 Jan 2026",
      until_text: null,
      value_text: "1.25 USD per litre",
      basis_text: "an estimate",
      source_reference: null,
      reason: null,
      set_by_label: "AssetOps administrator",
      recorded_text: "recorded 1 Jan 2026, 10:00",
      replaced: false,
      replaced_text: null,
    },
  ],
};

const notSet = (key: string, label: string, stored: boolean): PriceRowBody => ({
  key,
  noun: label.toLowerCase(),
  label,
  detail: "detail",
  stored,
  state: "NOT_SET",
  current: null,
  not_set_text: "Not set",
  note: stored ? null : "Saving this price comes once a figure uses it.",
  used_by: { text: "Used", detail: "by something" },
  history: [],
  history_title: null,
});

const ENTRY: PriceEntryBlock = {
  enabled: true,
  keys: ["diesel_price_per_litre", "productive_use_price_per_kwh"],
  today: "2026-11-13",
  unit_text: { diesel_price_per_litre: "per litre", productive_use_price_per_kwh: "per kWh" },
  currencies: ["EUR", "KES", "USD"],
  live_view: null,
};

const PAGE: PricePage = {
  site_code: "KOBO-001",
  site_name: "Kobo",
  title: "Kobo · Prices",
  intro: "intro",
  sign_in_text: ENTRY_SIGN_IN,
  table_title: "All prices for Kobo",
  table_note: "One row per price.",
  count_text: "3 prices · 1 set",
  cutoff: { known_at: null, text: null },
  prices: [DIESEL, notSet("productive_use_price_per_kwh", "Productive-use price", true), notSet("repair_visit_cost", "Cost per visit", false)],
  need: null,
  entry: ENTRY,
};

const SAVED_DIESEL: PriceRowBody = {
  ...DIESEL,
  current: { ...DIESEL.current!, revision_id: "r2", amount_text: "2.00", set_by_label: "Entered by site admin" },
  history_title: "History of the diesel price · 2 versions",
  history: [
    { ...DIESEL.history[0], revision_id: "r2", revision_no: 2, change_kind: "CORRECTION", headline: "Correction from 1 Oct 2026", set_by_label: "Entered by site admin" },
    { ...DIESEL.history[0], replaced: true, replaced_text: "replaced by a later correction" },
  ],
};

const detail = {
  async getSite() {
    return { status: "loaded", site: { site_id: "KOBO-001", display_name: "Kobo", site_type: "MINIGRID" } } as never;
  },
} as unknown as SiteDetailClient;

function pageClient(pages: PricePage[]) {
  const calls: { knownAt?: string | null }[] = [];
  const client: PricePageClient = {
    async getPrices(_siteId, query) {
      calls.push(query);
      return { status: "loaded", value: pages[Math.min(calls.length - 1, pages.length - 1)] };
    },
  };
  return { client, calls };
}

const DRY: PriceEntryDryRun = {
  dry_run: true,
  change_kind: "SUCCESSION",
  applies_from: "2026-11-13",
  reason_required: false,
  summary: "New diesel price from 13 Nov 2026. Earlier figures keep the current price.",
};
const SAVED: PriceEntrySaved = {
  revision_id: "r2",
  revision_no: 2,
  change_kind: "SUCCESSION",
  applies_from: "2026-11-13",
  recorded_at: "2026-11-12T10:00:00Z",
  replayed: false,
  set_by: "Entered by site admin",
  summary: 'Saved. Diesel price 2.00 USD per litre from 13 Nov 2026. Figures that use it read "Updating…" for a few minutes, then show the new price.',
};

function entryClient(
  dry: PriceEntryResult<PriceEntryDryRun>[] = [{ status: "ok", value: DRY }],
  save: PriceEntryResult<PriceEntrySaved>[] = [{ status: "ok", value: SAVED }],
) {
  const dryCalls: PriceEntryRequest[] = [];
  const saveCalls: PriceEntryRequest[] = [];
  const client: PriceEntryClient = {
    async dryRun(_siteId, request) {
      dryCalls.push(request);
      return dry[Math.min(dryCalls.length - 1, dry.length - 1)];
    },
    async save(_siteId, request) {
      saveCalls.push(request);
      return save[Math.min(saveCalls.length - 1, save.length - 1)];
    },
  };
  return { client, dryCalls, saveCalls };
}

function Where() {
  const location = useLocation();
  return <span data-where>{`${location.pathname}${location.search}`}</span>;
}

function renderPage(entry: string, pages: PricePageClient, entries: PriceEntryClient) {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <Routes>
        <Route
          path={SITE_PRICES_ROUTE_PATH}
          element={
            <>
              <SitePricesFrame detail={detail} client={pages} entryClient={entries} />
              <Where />
            </>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
}

const slot = (key: string) => document.querySelector(`[data-price-slot="${key}"]`) as HTMLElement | null;
const form = () => document.querySelector("[data-price-entry-form]") as HTMLElement;

function fill(scope: HTMLElement, values: { value?: string; source?: string; basis?: string; date?: string }) {
  const f = within(scope);
  fireEvent.change(f.getByLabelText(PRICE_ENTRY_WORDS.amount), { target: { value: values.value ?? "2.00" } });
  fireEvent.click(f.getByLabelText(values.basis ?? "A contract rate"));
  fireEvent.change(f.getByLabelText(PRICE_ENTRY_WORDS.source), { target: { value: values.source ?? "Supplier contract SC-88" } });
  if (values.date) fireEvent.change(f.getByLabelText(PRICE_ENTRY_WORDS.appliesFrom), { target: { value: values.date } });
}

async function openAndContinue(key = "diesel_price_per_litre", values = {}) {
  fireEvent.click(within(slot(key)!).getByRole("button", { name: PRICE_ENTRY_WORDS.open }));
  fill(form(), values);
  fireEvent.click(within(form()).getByRole("button", { name: PRICE_ENTRY_WORDS.continue }));
  await screen.findByRole("button", { name: PRICE_ENTRY_WORDS.save });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("PR-3 inline price form", () => {
  it("closed: a 'Set a new price' button on entry-key rows only, with the entry sentence", async () => {
    renderPage("/sites/KOBO-001/financials/prices", pageClient([PAGE]).client, entryClient().client);
    await settledScreen();
    expect(screen.getByText(ENTRY_SIGN_IN)).toBeInTheDocument();
    for (const key of ["diesel_price_per_litre", "productive_use_price_per_kwh"]) {
      expect(within(slot(key)!).getByRole("button", { name: PRICE_ENTRY_WORDS.open })).toBeInTheDocument();
    }
    expect(slot("repair_visit_cost")).toBeNull();
    expect(document.querySelector("[data-price-entry-form]")).toBeNull();
  });

  it("entry off: the administrator sentence, no button and no form", async () => {
    const off = { ...PAGE, sign_in_text: OFF_SIGN_IN, entry: { ...ENTRY, enabled: false } };
    renderPage("/sites/KOBO-001/financials/prices?key=diesel_price_per_litre", pageClient([off]).client, entryClient().client);
    await settledScreen();
    expect(screen.getByText(OFF_SIGN_IN)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: PRICE_ENTRY_WORDS.open })).toBeNull();
    expect(document.querySelector("[data-price-entry-form]")).toBeNull();
  });

  it("known_at view: the live-view words, a link that drops known_at, and no form", async () => {
    const past = {
      ...PAGE,
      cutoff: { known_at: "2026-10-01T00:00:00Z", text: "Prices as known at 1 Oct 2026, 03:00." },
      entry: { ...ENTRY, enabled: false, live_view: { text: "You are viewing prices as known at 1 Oct 2026, 03:00.", link_label: "Set a price from the live view →" } },
    };
    renderPage("/sites/KOBO-001/financials/prices?known_at=2026-10-01T00%3A00%3A00Z&key=diesel_price_per_litre", pageClient([past]).client, entryClient().client);
    await settledScreen();
    expect(document.querySelector("[data-prices-live-view]")).toHaveTextContent("You are viewing prices as known at 1 Oct 2026, 03:00.");
    expect(screen.queryByRole("button", { name: PRICE_ENTRY_WORDS.open })).toBeNull();
    fireEvent.click(screen.getByRole("link", { name: "Set a price from the live view →" }));
    expect(document.querySelector("[data-where]")).toHaveTextContent("/sites/KOBO-001/financials/prices?key=diesel_price_per_litre");
  });

  it("open: ?key= opens that row's form on arrival with today, the unit and a fixed currency", async () => {
    renderPage("/sites/KOBO-001/financials/prices?key=diesel_price_per_litre", pageClient([PAGE]).client, entryClient().client);
    await settledScreen();
    const f = form();
    expect(slot("diesel_price_per_litre")).toContainElement(f);
    expect(within(f).getByLabelText(PRICE_ENTRY_WORDS.appliesFrom)).toHaveValue("2026-11-13");
    expect(f.querySelector("[data-price-entry-unit]")).toHaveTextContent("USD per litre");
    expect(f.querySelector('[data-price-entry-currency="fixed"]')).toHaveTextContent("USD");
    expect(within(f).queryByLabelText(PRICE_ENTRY_WORDS.reason)).toBeNull();
    expect(within(slot("productive_use_price_per_kwh")!).queryByRole("form")).toBeNull();
  });

  it("a key with no price yet offers a currency select", async () => {
    renderPage("/sites/KOBO-001/financials/prices?key=productive_use_price_per_kwh", pageClient([PAGE]).client, entryClient().client);
    await settledScreen();
    const select = within(form()).getByLabelText(PRICE_ENTRY_WORDS.currency) as HTMLSelectElement;
    expect(select.value).toBe("USD");
    expect(form().querySelector("[data-price-entry-unit]")).toHaveTextContent("USD per kWh");
  });

  it("confirm → saving → saved: one key, no actor field, the success note, the re-read and the Back link", async () => {
    const pages = pageClient([PAGE, { ...PAGE, prices: [SAVED_DIESEL, ...PAGE.prices.slice(1)] }]);
    let release: (v: PriceEntryResult<PriceEntrySaved>) => void = () => undefined;
    const entries = entryClient();
    entries.client.save = async (_s, request) => {
      entries.saveCalls.push(request);
      return new Promise((resolve) => {
        release = resolve;
      });
    };
    renderPage("/sites/KOBO-001/financials/prices?return=%2Fsites%2FKOBO-001%2Fperformance", pages.client, entries.client);
    await settledScreen();
    await openAndContinue();
    expect(document.querySelector("[data-price-entry-summary]")).toHaveTextContent(DRY.summary);
    expect(within(form()).queryByLabelText(PRICE_ENTRY_WORDS.reason)).toBeNull();
    expect(entries.dryCalls).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: PRICE_ENTRY_WORDS.save }));
    expect(await screen.findByRole("button", { name: PRICE_ENTRY_WORDS.saving })).toBeDisabled();
    release({ status: "ok", value: SAVED });
    const note = await screen.findByRole("status");
    expect(note).toHaveTextContent(SAVED.summary);
    expect(note).toHaveTextContent("Updating…");
    expect(within(note).getByRole("link", { name: "← Back to where you were" })).toHaveAttribute("href", "/sites/KOBO-001/performance");
    const body = entries.saveCalls[0];
    expect(body.idempotency_key).toMatch(/^price-entry-[0-9a-f]{32}$/);
    expect(body.idempotency_key).toBe(entries.dryCalls[0].idempotency_key);
    expect(Object.keys(body).sort()).toEqual(["applies_from", "basis", "currency", "dry_run", "idempotency_key", "key", "reason", "source", "value"]);
    expect(body).toMatchObject({ key: "diesel_price_per_litre", value: "2.00", currency: "USD", basis: "CONTRACT_RATE", applies_from: "2026-11-13", reason: null });
    await screen.findByText("2.00");
    expect(pages.calls).toHaveLength(2);
    expect(document.querySelector('[data-price-history="diesel_price_per_litre"]')).toHaveTextContent("Entered by site admin");
    expect(document.querySelector("[data-price-entry-form]")).toBeNull();
  });

  it("reason required: the dry run shows the Reason field; Save waits for it and sends it", async () => {
    const entries = entryClient([{ status: "ok", value: { ...DRY, change_kind: "CORRECTION", reason_required: true, summary: "Correction from 1 Oct 2026. Figures from 1 Oct 2026 are recalculated with this price; the earlier version is kept in the history." } }]);
    renderPage("/sites/KOBO-001/financials/prices", pageClient([PAGE]).client, entries.client);
    await settledScreen();
    await openAndContinue("diesel_price_per_litre", { date: "2026-10-01" });
    const reason = within(form()).getByLabelText(PRICE_ENTRY_WORDS.reason);
    expect(screen.getByRole("button", { name: PRICE_ENTRY_WORDS.save })).toBeDisabled();
    fireEvent.change(reason, { target: { value: "Supplier invoice was higher" } });
    fireEvent.click(screen.getByRole("button", { name: PRICE_ENTRY_WORDS.save }));
    await screen.findByRole("status");
    expect(entries.saveCalls[0]).toMatchObject({ applies_from: "2026-10-01", reason: "Supplier invoice was higher" });
  });

  const REFUSALS: [number, string, string, string[]][] = [
    [403, "PRICE_ENTRY_OFF", "Saving prices is switched off on this server.", []],
    [422, "PRICE_ENTRY_INVALID", "Some fields are missing or not valid.", ["value", "basis"]],
    [422, "PRICE_KEY_NOT_ENTERABLE", "No figure uses this price yet, so it cannot be saved here.", []],
    [422, "APPLIES_FROM_OUT_OF_RANGE", "The date must be within 400 days before and 366 days after today at this site.", []],
    [422, "CURRENCY_DIFFERS", "This site's diesel price is kept in USD.", []],
    [422, "REASON_REQUIRED", "This date changes figures already shown. Say why.", []],
  ];

  it.each(REFUSALS)("refused on save (%s %s): the server's words and 'Nothing was saved.'", async (status, code, message, fields) => {
    const fetchMock = vi.fn(async (_url: string, init?: RequestInit) => {
      const sent = JSON.parse(String(init?.body)) as PriceEntryRequest;
      if (sent.dry_run) return new Response(JSON.stringify(DRY), { status: 200 });
      return new Response(JSON.stringify({ detail: { code, message, ...(fields.length ? { fields } : {}) } }), { status });
    });
    vi.stubGlobal("fetch", fetchMock);
    renderPage("/sites/KOBO-001/financials/prices", pageClient([PAGE]).client, createPriceEntryClient());
    await settledScreen();
    await openAndContinue();
    fireEvent.click(screen.getByRole("button", { name: PRICE_ENTRY_WORDS.save }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(message);
    expect(alert).toHaveTextContent("Nothing was saved.");
    if (fields.length) expect(alert).toHaveTextContent("Check: Amount, Basis.");
    if (code === "REASON_REQUIRED") expect(within(form()).getByLabelText(PRICE_ENTRY_WORDS.reason)).toBeInTheDocument();
    expect(screen.queryByRole("status")).toBeNull();
    const url = String(fetchMock.mock.calls[0][0]);
    expect(url).toBe("/api/sites/KOBO-001/financial-assumptions/entries");
  });

  it("refused on the dry run: back to the fields with the server's words", async () => {
    const entries = entryClient([{ status: "refused", code: "PRICE_ENTRY_INVALID", message: "Some fields are missing or not valid.", fields: ["source"] }]);
    renderPage("/sites/KOBO-001/financials/prices", pageClient([PAGE]).client, entries.client);
    await settledScreen();
    fireEvent.click(within(slot("diesel_price_per_litre")!).getByRole("button", { name: PRICE_ENTRY_WORDS.open }));
    fireEvent.click(within(form()).getByRole("button", { name: PRICE_ENTRY_WORDS.continue }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Some fields are missing or not valid. Check: Where this price comes from. Nothing was saved.");
    expect(within(form()).getByLabelText(PRICE_ENTRY_WORDS.source)).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByRole("button", { name: PRICE_ENTRY_WORDS.continue })).toBeEnabled();
  });

  it("503: 'Prices cannot be saved right now. Nothing was saved.'", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ detail: { code: "ASSUMPTION_STORE_UNAVAILABLE", message: "x" } }), { status: 503 })));
    renderPage("/sites/KOBO-001/financials/prices", pageClient([PAGE]).client, createPriceEntryClient());
    await settledScreen();
    fireEvent.click(within(slot("diesel_price_per_litre")!).getByRole("button", { name: PRICE_ENTRY_WORDS.open }));
    fill(form(), {});
    fireEvent.click(within(form()).getByRole("button", { name: PRICE_ENTRY_WORDS.continue }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Prices cannot be saved right now. Nothing was saved.");
  });

  it("network loss on save: 'Saving again is safe.' and the retry reuses the same key", async () => {
    const entries = entryClient(undefined, [{ status: "lost" }, { status: "ok", value: { ...SAVED, replayed: true } }]);
    renderPage("/sites/KOBO-001/financials/prices", pageClient([PAGE]).client, entries.client);
    await settledScreen();
    await openAndContinue();
    fireEvent.click(screen.getByRole("button", { name: PRICE_ENTRY_WORDS.save }));
    expect(await screen.findByRole("alert")).toHaveTextContent("We could not confirm the save. Saving again is safe.");
    fireEvent.click(screen.getByRole("button", { name: PRICE_ENTRY_WORDS.save }));
    await screen.findByRole("status");
    expect(entries.saveCalls).toHaveLength(2);
    expect(entries.saveCalls[1].idempotency_key).toBe(entries.saveCalls[0].idempotency_key);
  });

  it("502 on save (not the route's 503): 'lost', never 'Nothing was saved.'", async () => {
    vi.stubGlobal("fetch", vi.fn(async (_url: string, init?: RequestInit) => {
      const sent = JSON.parse(String(init?.body)) as PriceEntryRequest;
      if (sent.dry_run) return new Response(JSON.stringify(DRY), { status: 200 });
      return new Response("Bad gateway", { status: 502 });
    }));
    renderPage("/sites/KOBO-001/financials/prices", pageClient([PAGE]).client, createPriceEntryClient());
    await settledScreen();
    await openAndContinue();
    fireEvent.click(screen.getByRole("button", { name: PRICE_ENTRY_WORDS.save }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("We could not confirm the save. Saving again is safe.");
    expect(alert).not.toHaveTextContent("Nothing was saved");
  });

  it("409 key reused (the store's real words): an honest sentence, no key, no uuid, no 'Nothing was saved.'", async () => {
    const message = "Idempotency key 'price-entry-0123456789abcdef0123456789abcdef' already published revision 7c1f2d3e-0000-4000-8000-000000000001 with a different request; nothing was written.";
    vi.stubGlobal("fetch", vi.fn(async (_url: string, init?: RequestInit) => {
      const sent = JSON.parse(String(init?.body)) as PriceEntryRequest;
      if (sent.dry_run) return new Response(JSON.stringify(DRY), { status: 200 });
      return new Response(JSON.stringify({ detail: { code: "IDEMPOTENCY_KEY_REUSED", message } }), { status: 409 });
    }));
    renderPage("/sites/KOBO-001/financials/prices", pageClient([PAGE]).client, createPriceEntryClient());
    await settledScreen();
    await openAndContinue();
    fireEvent.click(screen.getByRole("button", { name: PRICE_ENTRY_WORDS.save }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("An earlier save from this form may already have been recorded.");
    expect(alert).toHaveTextContent("check History");
    expect(alert.textContent).not.toMatch(/Nothing was saved|Idempotency|price-entry-|7c1f2d3e/);
  });

  it("Change after a lost save starts a new idempotency key", async () => {
    const entries = entryClient(undefined, [{ status: "lost" }, { status: "ok", value: SAVED }]);
    renderPage("/sites/KOBO-001/financials/prices", pageClient([PAGE]).client, entries.client);
    await settledScreen();
    await openAndContinue();
    fireEvent.click(screen.getByRole("button", { name: PRICE_ENTRY_WORDS.save }));
    await screen.findByRole("alert");
    fireEvent.click(screen.getByRole("button", { name: PRICE_ENTRY_WORDS.change }));
    expect(within(form()).getByLabelText(PRICE_ENTRY_WORDS.amount)).toHaveFocus();
    fireEvent.change(within(form()).getByLabelText(PRICE_ENTRY_WORDS.amount), { target: { value: "2.50" } });
    fireEvent.click(within(form()).getByRole("button", { name: PRICE_ENTRY_WORDS.continue }));
    fireEvent.click(await screen.findByRole("button", { name: PRICE_ENTRY_WORDS.save }));
    await screen.findByRole("status");
    expect(entries.saveCalls[1].idempotency_key).not.toBe(entries.saveCalls[0].idempotency_key);
    expect(entries.dryCalls[1].idempotency_key).toBe(entries.saveCalls[1].idempotency_key);
  });

  it("focus: Amount on open, the summary on confirm, Reason when required, the invalid field on a refusal, the note after save", async () => {
    const entries = entryClient(
      [{ status: "ok", value: DRY }, { status: "refused", code: "PRICE_ENTRY_INVALID", message: "Some fields are missing or not valid.", fields: ["source"] }],
    );
    renderPage("/sites/KOBO-001/financials/prices", pageClient([PAGE, PAGE]).client, entries.client);
    await settledScreen();
    fireEvent.click(within(slot("diesel_price_per_litre")!).getByRole("button", { name: PRICE_ENTRY_WORDS.open }));
    expect(within(form()).getByLabelText(PRICE_ENTRY_WORDS.amount)).toHaveFocus();
    fill(form(), {});
    fireEvent.click(within(form()).getByRole("button", { name: PRICE_ENTRY_WORDS.continue }));
    await screen.findByRole("button", { name: PRICE_ENTRY_WORDS.save });
    expect(document.activeElement).toBe(document.querySelector("[data-price-entry-summary]"));
    fireEvent.click(screen.getByRole("button", { name: PRICE_ENTRY_WORDS.change }));
    fireEvent.click(within(form()).getByRole("button", { name: PRICE_ENTRY_WORDS.continue }));
    await screen.findByRole("alert");
    expect(within(form()).getByLabelText(PRICE_ENTRY_WORDS.source)).toHaveFocus();
  });

  it("focus: Reason on confirm when required; the success note after save", async () => {
    const entries = entryClient([{ status: "ok", value: { ...DRY, change_kind: "CORRECTION", reason_required: true, summary: "Correction." } }]);
    renderPage("/sites/KOBO-001/financials/prices", pageClient([PAGE, PAGE]).client, entries.client);
    await settledScreen();
    await openAndContinue("diesel_price_per_litre", { date: "2026-10-01" });
    const reason = within(form()).getByLabelText(PRICE_ENTRY_WORDS.reason);
    expect(reason).toHaveFocus();
    fireEvent.change(reason, { target: { value: "Supplier invoice" } });
    fireEvent.click(screen.getByRole("button", { name: PRICE_ENTRY_WORDS.save }));
    const note = await screen.findByRole("status");
    expect(note).toHaveFocus();
  });

  it("the re-read after a save fails: the success note and Back link stay", async () => {
    let pagesCalls = 0;
    const pages = {
      async getPrices() {
        return pagesCalls++ === 0 ? { status: "loaded", value: PAGE } : { status: "unavailable" };
      },
    } as PricePageClient;
    renderPage("/sites/KOBO-001/financials/prices?return=%2Fsites%2FKOBO-001%2Fperformance", pages, entryClient().client);
    await settledScreen();
    await openAndContinue();
    fireEvent.click(screen.getByRole("button", { name: PRICE_ENTRY_WORDS.save }));
    const note = await screen.findByRole("status");
    expect(note).toHaveTextContent(SAVED.summary);
    await waitFor(() => expect(pagesCalls).toBe(2));
    expect(screen.getByRole("status")).toHaveTextContent(SAVED.summary);
    expect(within(screen.getByRole("status")).getByRole("link", { name: "← Back to where you were" })).toBeInTheDocument();
    expect(document.querySelector("[data-prices-refused]")).toBeNull();
  });

  it("the client maps a dropped connection to 'lost' and sends dry_run per step", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => {
      throw new TypeError("Failed to fetch");
    }));
    const client = createPriceEntryClient();
    const request = { key: "diesel_price_per_litre", value: "1", currency: "USD", basis: null, source: "s", applies_from: "2026-11-13", reason: null, dry_run: false, idempotency_key: "price-entry-" + "a".repeat(32) };
    expect(await client.save("KOBO-001", request)).toEqual({ status: "lost" });
  });
});
