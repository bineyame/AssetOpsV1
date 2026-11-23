/**
 * 5c unit 3 (spec §6 tests 10 to 13): "The month" renders the server's JSON as given (D-5C.2). World A is the
 * hand-written fixture of spec §3.5 (`backend/tests/fixtures/5c/deep_dive_lakeside_2026-10.json`); World H is A with
 * §3.5 H's changes written here by hand (D-5C.24 for the Diesel price driver), checked against the backend's own World H
 * (`fixtures/deep_dive_world_h.json`). World X (`fixtures/deep_dive_currency_mismatch.json`) is the backend's view with
 * Kobo in KES, Kisiwa in USD and Mto's actual in KES against a USD target. Both JSON files are written by
 * `backend/tests/fixtures/5c/make_screen_worlds.py`, never by hand.
 */
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { settledScreen } from "../../test/settled";
import { DeepDiveMonthFrame } from "../DeepDiveMonth";
import type { DeepDiveDriver, DeepDiveMonthBody, DeepDiveMonthClient, DeepDiveResult } from "../deepDiveMonthClient";
import { fakeClient, findingsBody, loaded } from "./estateFixtures";
import { loadedPortfolio, portfolioBody } from "./portfolioFixtures";
import FIXTURE_TEXT from "../../../../backend/tests/fixtures/5c/deep_dive_lakeside_2026-10.json?raw";
import WORLD_H_TEXT from "./fixtures/deep_dive_world_h.json?raw";
import WORLD_X_TEXT from "./fixtures/deep_dive_currency_mismatch.json?raw";
import PAGE_SOURCE from "../DeepDiveMonth.tsx?raw";

const worldA = (): DeepDiveMonthBody => JSON.parse(FIXTURE_TEXT) as DeepDiveMonthBody;
const servedH = (): DeepDiveMonthBody => JSON.parse(WORLD_H_TEXT) as DeepDiveMonthBody;
const worldX = (): DeepDiveMonthBody => JSON.parse(WORLD_X_TEXT) as DeepDiveMonthBody;

/** Every money figure in a text: a sign, a currency ("$" or an ISO code) and digits. */
const MONEY = /[−+]?(?:\$|[A-Z]{3} )\d[\d,]*(?:\.\d+)?/g;

/** Keys whose values are codes or numbers for the page, not words for the reader. */
const NOT_SHOWN = new Set(["schema", "month", "nav", "state", "as_of", "reason", "reconciled", "key", "bar", "scale", "connected", "more", "standing"]);
// `fresh.untracked_text` is read in the Assure drawer (its last line), not on the page itself.
NOT_SHOWN.add("untracked_text");
// IA-P2 P3b (spec §6 P3b): the month JSON's `decisions` panel is replaced by the Decisions list (HomeList over the estate
// rows); its served text is no longer drawn, so it is not among the strings expected on the page.
NOT_SHOWN.add("decisions");

function strings(value: unknown, out: string[] = []): string[] {
  if (typeof value === "string") out.push(value);
  else if (Array.isArray(value)) value.forEach((v) => strings(v, out));
  else if (value !== null && typeof value === "object") {
    for (const [k, v] of Object.entries(value)) if (!NOT_SHOWN.has(k) && k !== "drawer") strings(v, out);
  }
  return out;
}

function worldH(): DeepDiveMonthBody {
  const h = worldA();
  const fuel = h.bridge!.groups[1].steps[0].drawer;
  const m = "Modelled, not yet reconciled";
  // D-5C.21: Diesel used holds its three parts; Diesel price is its sibling (D-5C.24: no detail, Modelled).
  const leaf = (key: string, label: string, value: string, detail: string | null): DeepDiveDriver => ({
    key, label, value, sites: "3 of 3 Sites", detail, word: m, children: [],
  });
  fuel.drivers = [
    {
      ...leaf("diesel_l", "Diesel used", "+$2,233.60", "Actual 1,569 L · Target 3,300 L"),
      children: [
        leaf("necessary_l", "Diesel not shown to be avoidable", "+$2,681.80", "Actual 1,214 L · Target 3,300 L"),
        leaf("candidate_l", "Diesel run while solar and battery could carry the load", "−$279.70", "Actual 221 L · Target 0 L"),
        leaf("unexplained_l", "Unexplained fuel", "−$168.50", "Actual 134 L · Target 0 L"),
      ],
    },
    leaf("diesel_price", "Diesel price", "$0.00", null),
  ];
  return h;
}

function stateBody(state: "NO_SNAPSHOT" | "REBUILD_NEEDED", text: string): DeepDiveMonthBody {
  return {
    schema: "deep-dive-month-1",
    operator: "Lakeside Power",
    month: state === "NO_SNAPSHOT" ? "2026-09" : "2026-10",
    month_words: state === "NO_SNAPSHOT" ? "September 2026" : "October 2026",
    nav: state === "NO_SNAPSHOT" ? { previous: "2026-08", next: "2026-10" } : { previous: "2026-09", next: null },
    state,
    state_text: text,
  };
}

function clientOf(answer: (month?: string) => DeepDiveResult): DeepDiveMonthClient & { calls: (string | undefined)[] } {
  const calls: (string | undefined)[] = [];
  return {
    calls,
    fetchDeepDiveMonth: (month?: string) => {
      calls.push(month);
      return Promise.resolve(answer(month));
    },
  };
}

function LocationProbe() {
  const location = useLocation();
  return <div data-location>{`${location.pathname}${location.search}`}</div>;
}

/**
 * IA-P2 P3b (spec §6 P3b): the month page takes `month`, `nav` and `notes` as props (E2 serves them) and reads no
 * `?month=`. The mount is the Overview's mode `month` body at the October range, with E2's nav for September (October
 * is the latest served month, so no next).
 */
const SEPTEMBER = { month_words: "September 2026", from: "2026-09-01", to: "2026-09-30" };
const NOVEMBER = { month_words: "November 2026", from: "2026-11-01", to: "2026-11-30" };
const OCT_RANGE = "from=2026-10-01&to=2026-10-31";

function renderMonth(
  client: DeepDiveMonthClient,
  props: { month?: string; nav?: { previous: typeof SEPTEMBER | null; next: typeof NOVEMBER | null } | null; notes?: string[] } = {},
) {
  const estate = { ...fakeClient((lens) => loaded(findingsBody(lens))), portfolio: () => Promise.resolve(loadedPortfolio(portfolioBody())) };
  return render(
    <MemoryRouter initialEntries={[`/portfolio?${OCT_RANGE}`]}>
      <Routes>
        <Route
          path="/portfolio"
          element={
            <DeepDiveMonthFrame
              client={client}
              estate={estate}
              month={props.month ?? "2026-10"}
              nav={props.nav === undefined ? { previous: SEPTEMBER, next: null } : props.nav}
              notes={props.notes ?? []}
            />
          }
        />
      </Routes>
      <LocationProbe />
    </MemoryRouter>,
  );
}

async function settled() {
  await settledScreen();
  expect(document.body.textContent).not.toContain("Preparing the month…");
}

function openDialog(): HTMLElement {
  return screen.getByRole("dialog");
}

/** Every not-available row: 8 are shown, and a 9th puts the rest behind "Show all {n}" (the caps test). */
function showAllNotAvailable(body: DeepDiveMonthBody) {
  const n = body.not_available!.rows.length;
  const more = screen.queryByRole("button", { name: `Show all ${n}` });
  expect(more !== null).toBe(n > 8);
  if (more !== null) fireEvent.click(more);
}

describe("5c test 10: World A renders", () => {
  it("shows every string of spec §3.5 outside the drawers, the notice visible and the status line a status", async () => {
    const a = worldA();
    const view = renderMonth(clientOf(() => ({ status: "loaded", body: a })));
    await settled();
    expect(screen.queryByRole("dialog")).toBeNull();
    showAllNotAvailable(a);
    const text = view.container.textContent ?? "";
    for (const s of strings(a)) expect(text, s).toContain(s);
    expect(text).toContain(a.headline!.evidence[0]);
    // D-5C.2 (P8): each figure is the JSON's string, character for character, in its own place.
    for (const tile of a.tiles!) {
      expect(view.container.querySelector(`[data-dd-tile="${tile.key}"] .dd-kpi__value`)!.textContent).toBe(tile.value);
    }
    for (const step of a.bridge!.groups.flatMap((g) => g.steps)) {
      expect(view.container.querySelector(`[data-dd-step="${step.key}"] .dd-wf__value`)!.textContent).toBe(step.value);
    }
    // D-5C.13: never the uncarried composition.
    expect(text).not.toContain("$1,693.00");
    // The notice is visible with every drawer closed, never inside a dialog (P5).
    const note = screen.getByRole("note");
    expect(note.textContent).toBe(a.notices![0]);
    expect(note.closest("[role=dialog]")).toBeNull();
    expect(note.closest("details")).toBeNull();
    // The status line is a status and names Kisiwa (P18).
    const status = screen.getByRole("status");
    expect(status.textContent).toBe(a.status_line);
    expect(status.textContent).toContain("Kisiwa");
    // Kisiwa's carried O&M cell reads as served (D-5C.23: "(at budget)"), in its own cell (P6).
    const kisiwa = a.bridge!.by_site.rows.find((r) => r[0] === "Kisiwa")!;
    const cells = [...view.container.querySelectorAll("tbody tr")].find((tr) => tr.querySelector("th")?.textContent === "Kisiwa")!;
    expect([...cells.querySelectorAll("th, td")].map((c) => c.textContent)).toEqual(kisiwa);
  });

  it("the page never formats a figure: no number formatting in its source (D-5C.2, P8)", () => {
    const code = PAGE_SOURCE.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
    for (const banned of ["toFixed", "toLocaleString", "Intl.NumberFormat", "parseFloat", "toPrecision"]) {
      expect(code, banned).not.toContain(banned);
    }
    // The bar's ratio is the one arithmetic: Number( appears only inside barWidths.
    const outside = code.replace(/function barWidths[\s\S]*?\n\}\n/, "");
    expect(outside).not.toContain("Number(");
  });

  it("opens every step drawer and the Assure drawer with their lines", async () => {
    const a = worldA();
    renderMonth(clientOf(() => ({ status: "loaded", body: a })));
    await settled();
    for (const group of a.bridge!.groups) {
      for (const step of group.steps) {
        fireEvent.click(screen.getByRole("button", { name: new RegExp(`^${step.label.replace(/[&]/g, "\\$&")} `) }));
        const dialog = openDialog();
        const dtext = dialog.textContent ?? "";
        for (const s of strings(step.drawer)) expect(dtext, s).toContain(s);
        fireEvent.keyDown(dialog, { key: "Escape" });
        expect(screen.queryByRole("dialog")).toBeNull();
      }
    }
    const assure = a.outcomes!.find((o) => o.key === "assure")!;
    fireEvent.click(screen.getByRole("button", { name: assure.value }));
    const dialog = screen.getByRole("dialog", { name: assure.drawer!.title });
    const items = within(dialog).getAllByRole("listitem").map((li) => li.textContent);
    // DD3d.4: World A's litres are no commercial record, so the drawer's last line is the not-checked line.
    expect(items).toEqual([a.standing!.text, ...a.standing!.details!, a.fresh!.untracked_text]);
  });

  it("World B: no 'not yet reconciled' suffix is added by the page", async () => {
    const b = worldA();
    const strip = (s: string) => s.replace(", not yet reconciled", "");
    b.headline!.evidence = b.headline!.evidence.map(strip);
    b.tiles!.forEach((t) => (t.word = t.word === null ? null : strip(t.word)));
    b.status_line = "Figures as of 20 November 2026, 08:00 UTC. Revenue and fuel bought are reconciled with the management accounts. Kisiwa's budget disagrees with its own lines.";
    b.bridge!.groups.forEach((g) => g.steps.forEach((s) => (s.word = s.word === null ? null : strip(s.word))));
    b.cash!.word = strip(b.cash!.word!);
    b.outcomes!.forEach((o) => (o.word = o.word === null ? null : strip(o.word)));
    b.outcomes![3].value = "Reconciled";
    const view = renderMonth(clientOf(() => ({ status: "loaded", body: b })));
    await settled();
    expect(view.container.textContent).not.toContain("not yet reconciled");
  });
});

describe("5c test 11: drawers keep and return focus; drivers carry their words", () => {
  it("a step drawer is a labelled dialog, focus moves to Close, Escape closes and returns focus", async () => {
    const h = worldH();
    renderMonth(clientOf(() => ({ status: "loaded", body: h })));
    await settled();
    const opener = screen.getByRole("button", { name: /^Fuel cost / });
    opener.focus();
    fireEvent.click(opener);
    const dialog = screen.getByRole("dialog", { name: "Fuel cost" });
    expect(dialog.getAttribute("aria-modal")).toBe("true");
    expect(document.activeElement).toBe(within(dialog).getByRole("button", { name: "Close" }));
    // Every driver shows label, value, word chip, sites and detail (P13).
    const rows = dialog.querySelectorAll("[data-dd-driver]");
    const flat = (ds: DeepDiveDriver[]): DeepDiveDriver[] => ds.flatMap((d) => [d, ...flat(d.children ?? [])]);
    const all = flat(h.bridge!.groups[1].steps[0].drawer.drivers);
    expect(rows.length).toBe(all.length);
    all.forEach((d, i) => {
      const row = rows[i] as HTMLElement;
      expect(row.textContent).toContain(d.label);
      expect(row.textContent).toContain(d.value);
      expect(row.textContent).toContain(d.sites);
      if (d.detail !== null) expect(row.textContent).toContain(d.detail);
      expect(row.querySelector(":scope > [data-dd-word]")?.textContent).toBe(d.word);
    });
    expect(dialog.textContent).toContain("Modelled, not yet reconciled");
    fireEvent.keyDown(dialog, { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(opener);
  });

  it("World H's three parts sit inside Diesel used's list item, never beside it (D-5C.21)", async () => {
    renderMonth(clientOf(() => ({ status: "loaded", body: worldH() })));
    await settled();
    fireEvent.click(screen.getByRole("button", { name: /^Fuel cost / }));
    const dialog = screen.getByRole("dialog", { name: "Fuel cost" });
    const label = (li: Element) => li.querySelector(":scope > .dd-driver__label")!.textContent;
    const top = dialog.querySelectorAll(".dd-drivers:not(.dd-drivers--parts) > [data-dd-driver]");
    expect([...top].map(label)).toEqual(["Diesel used", "Diesel price"]);
    const parts = top[0].querySelectorAll(":scope > ul > [data-dd-driver]");
    expect([...parts].map(label)).toEqual([
      "Diesel not shown to be avoidable",
      "Diesel run while solar and battery could carry the load",
      "Unexplained fuel",
    ]);
    expect(within(dialog).getByRole("list", { name: "Parts of Diesel used" }).closest("[data-dd-driver]")).toBe(top[0]);
    expect(top[1].querySelector("ul")).toBeNull();
  });

  it("caps: 12 by-Site rows and 12 drawer Sites show 10 and Show all 12; 9 not-available rows show 8 (D-5C.22)", async () => {
    const a = worldA();
    const bySite = a.bridge!.by_site.rows;
    a.bridge!.by_site.rows = Array.from({ length: 12 }, (_, i) => [`Site ${i + 1}`, ...bySite[i % 3].slice(1)]);
    const revenue = a.bridge!.groups[0].steps[0].drawer;
    revenue.sites = Array.from({ length: 12 }, (_, i) => ({ ...revenue.sites[i % 3], site: `Site ${i + 1}` }));
    const na = a.not_available!.rows;
    a.not_available!.rows = Array.from({ length: 9 }, (_, i) => ({ ...na[i % na.length], needs: `${na[i % na.length].needs} (${i + 1})` }));
    const view = renderMonth(clientOf(() => ({ status: "loaded", body: a })));
    await settled();
    const table = view.container.querySelector("details.dd-details tbody")!;
    expect(table.querySelectorAll("tr").length).toBe(10);
    const bridge = screen.getByRole("heading", { name: "Where the gap comes from" }).closest("section")!;
    fireEvent.click(within(bridge as HTMLElement).getByRole("button", { name: "Show all 12" }));
    expect(table.querySelectorAll("tr").length).toBe(12);
    expect(document.activeElement).toBe(table.querySelectorAll("tr")[10]);
    expect((document.activeElement as HTMLElement).tabIndex).toBe(-1);
    expect(view.container.querySelectorAll(".dd-gaps__row").length).toBe(8);
    fireEvent.click(screen.getByRole("button", { name: "Show all 9" }));
    expect(view.container.querySelectorAll(".dd-gaps__row").length).toBe(9);
    fireEvent.click(screen.getByRole("button", { name: /^Revenue / }));
    const dialog = screen.getByRole("dialog", { name: "Revenue" });
    expect(dialog.querySelectorAll(".dd-site").length).toBe(10);
    fireEvent.click(within(dialog).getByRole("button", { name: "Show all 12" }));
    expect(dialog.querySelectorAll(".dd-site").length).toBe(12);
  });

  it("the scrim and Close close the drawer and return focus (P12)", async () => {
    renderMonth(clientOf(() => ({ status: "loaded", body: worldH() })));
    await settled();
    const opener = screen.getByRole("button", { name: /^Revenue / });
    fireEvent.click(opener);
    fireEvent.click(document.querySelector("[data-dd-scrim]")!);
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(opener);
    fireEvent.click(opener);
    fireEvent.click(within(openDialog()).getByRole("button", { name: "Close" }));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(opener);
  });

  it("World H's Assure drawer adds the not-checked line", async () => {
    const h = worldH();
    renderMonth(clientOf(() => ({ status: "loaded", body: h })));
    await settled();
    fireEvent.click(screen.getByRole("button", { name: "Not yet reconciled" }));
    const items = within(openDialog()).getAllByRole("listitem").map((li) => li.textContent);
    expect(items).toEqual(h.outcomes![3].drawer!.lines);
    expect(items[items.length - 1]).toBe(h.fresh!.untracked_text);
  });
});

describe("5c test 11: the served worlds (backend-written H and the currency mismatch X)", () => {
  /** The money figures a text shows; each must be one the JSON serves, in its own currency, never re-formatted. */
  const money = (text: string) => text.match(MONEY) ?? [];
  /** The money figures shown under `root`, one text node at a time (adjacent cells never run together). */
  const moneyIn = (root: Element) => {
    const out: string[] = [];
    const walk = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    for (let n = walk.nextNode(); n !== null; n = walk.nextNode()) {
      // IA-P2 P3b (spec §6 P3b): L2's Decisions are the list component's rows over the estate Findings (the estate
      // read's own figures, pinned in portfolioHub), no longer part of the month JSON, so they are not checked here.
      if (n.parentElement?.closest("[data-home-list]")) continue;
      out.push(...money(n.textContent ?? ""));
    }
    return out;
  };
  const served = (body: unknown) => new Set(money(JSON.stringify(body)));

  it("the hand-written World H equals the backend's World H wherever it is drawn", () => {
    const h = worldH();
    const b = servedH();
    expect(h.tiles).toEqual(b.tiles);
    expect(h.bridge).toEqual(b.bridge);
    expect(h.fresh).toEqual(b.fresh);
    expect(h.outcomes).toEqual(b.outcomes);
    expect(h.headline).toEqual(b.headline);
  });

  it("World X: the headline, tiles and cards read Not available yet as served; each figure in its own currency", async () => {
    const x = worldX();
    const view = renderMonth(clientOf(() => ({ status: "loaded", body: x })));
    await settled();
    showAllNotAvailable(x);
    const text = view.container.textContent ?? "";
    for (const s of strings(x)) expect(text, s).toContain(s);
    // L7: the headline is the served sentence; no evidence chip beside a sentence with no figure.
    expect(x.headline!.text).toBe("Contribution for October is not available yet: the Sites' figures are in different currencies.");
    const headline = view.container.querySelector(".dd-headline")!;
    expect(headline.textContent!.trim()).toBe(x.headline!.text);
    expect(headline.querySelector("[data-dd-word]")).toBeNull();
    // No bar is drawn for a tile with no figure.
    for (const tile of x.tiles!) {
      const el = view.container.querySelector(`[data-dd-tile="${tile.key}"]`)!;
      expect(el.querySelector(".dd-kpi__value")!.textContent).toBe(tile.value);
      expect(el.querySelector(".dd-bar")).toBeNull();
    }
    // D-5C.26 (revises L9): the Optimize heading would add KES to USD: its card states Not available yet once, no word.
    const card = view.container.querySelector('[data-dd-outcome="optimize"]')!;
    expect(card.querySelector(".dd-card__value")!.textContent).toBe("Not available yet");
    expect(card.querySelector("[data-dd-word]")).toBeNull();
    const optimize = x.bridge!.groups.find((g) => g.key === "OPTIMIZE_COST")!;
    expect(optimize.value).toBe("Not available yet");
    const rows = [...view.container.querySelectorAll(".dd-wf__grouprow")].map((r) => r.textContent);
    expect(rows).toContain(`${optimize.label} Not available yet`);
    // Each step prints in its own currency, character for character (fuel cost KES, O&M USD).
    for (const step of x.bridge!.groups.flatMap((g) => g.steps)) {
      expect(view.container.querySelector(`[data-dd-step="${step.key}"] .dd-wf__value`)!.textContent).toBe(step.value);
    }
    expect(view.container.querySelector('[data-dd-step="fuel_cost"] .dd-wf__value')!.textContent).toBe("+KES 82.50");
    // Every money figure on the page is one the JSON serves (the page never puts "$" on a KES figure).
    const shown = moneyIn(view.container);
    expect(shown.some((m) => m.includes("KES"))).toBe(true);
    const ok = served(x);
    expect(shown.filter((m) => !ok.has(m))).toEqual([]);
  });

  it("World X: each step drawer names Mto's currency mismatch and keeps every figure in its served currency", async () => {
    const x = worldX();
    renderMonth(clientOf(() => ({ status: "loaded", body: x })));
    await settled();
    const line = "Mto: not compared: its actual and its target are in different currencies (KES and USD).";
    for (const step of x.bridge!.groups.flatMap((g) => g.steps)) {
      fireEvent.click(screen.getByRole("button", { name: new RegExp(`^${step.label.replace(/[&]/g, "\\$&")} `) }));
      const dialog = openDialog();
      const dtext = dialog.textContent ?? "";
      for (const s of strings(step.drawer)) expect(dtext, s).toContain(s);
      expect(within(dialog).getByText(line)).toBeTruthy();
      const ok = served(step);
      expect(moneyIn(dialog).filter((m) => !ok.has(m))).toEqual([]);
      fireEvent.keyDown(dialog, { key: "Escape" });
    }
    fireEvent.click(screen.getByRole("button", { name: /^Fuel cost / }));
    const drivers = openDialog().querySelectorAll("[data-dd-driver] > .dd-num");
    expect(drivers.length).toBeGreaterThan(0);
    for (const d of drivers) expect(d.textContent).not.toContain("$");
  });

  it("World A: every money figure on the page is one the JSON serves", async () => {
    const a = worldA();
    const view = renderMonth(clientOf(() => ({ status: "loaded", body: a })));
    await settled();
    const shown = moneyIn(view.container);
    expect(shown.length).toBeGreaterThan(0);
    const ok = served(a);
    expect(shown.filter((m) => !ok.has(m))).toEqual([]);
  });
});

describe("5c test 12: states and the month links", () => {
  it("NO_SNAPSHOT and REBUILD_NEEDED show the header and the state text only", async () => {
    for (const [state, text] of [
      ["NO_SNAPSHOT", "The figures for September 2026 have not been prepared yet."],
      ["REBUILD_NEEDED", "The figures for October 2026 must be prepared again before they can be shown."],
    ] as const) {
      const view = renderMonth(clientOf(() => ({ status: "loaded", body: stateBody(state, text) })));
      await settled();
      expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Portfolio");
      expect(view.container.textContent).toContain(text);
      expect(view.container.querySelector("[data-level]")).toBeNull();
      expect(screen.queryByRole("status")).toBeNull();
      view.unmount();
    }
  });

  it("503 shows the served text with Try again, which reads again", async () => {
    let n = 0;
    const client = clientOf(() => {
      n += 1;
      return n === 1
        ? { status: "refused", httpStatus: 503, code: "DEEP_DIVE_UNAVAILABLE", text: "The month's figures cannot be read right now." }
        : { status: "loaded", body: worldA() };
    });
    renderMonth(client);
    await settled();
    expect(document.body.textContent).toContain("The month's figures cannot be read right now.");
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    });
    await settled();
    expect(client.calls.length).toBe(2);
    expect(screen.getByRole("status").textContent).toBe(worldA().status_line);
  });

  it("401 asks to sign in", async () => {
    renderMonth(clientOf(() => ({ status: "refused", httpStatus: 401, code: "PERSON_REQUIRED", text: "Sign in to continue." })));
    await settled();
    expect(document.body.textContent).toContain("Sign in to see this operator's figures.");
    expect(document.querySelector("[data-level]")).toBeNull();
  });

  // IA-P2 P3b (spec §6 P3b, I1; D-IAP.17): the ‹ › links are E2's `nav` days and set the range to that month's days;
  // the page reads no `?month=`, so it no longer re-reads a month on a click (the Overview remounts it per month).
  it("the ‹ › links are E2's nav days: they set the range to that month and no ?month=; next is absent when null", async () => {
    const client = clientOf(() => ({ status: "loaded", body: worldA() }));
    renderMonth(client);
    await settled();
    expect(client.calls).toEqual(["2026-10"]);
    const nav = screen.getByRole("navigation", { name: "Month" });
    expect(within(nav).queryByRole("link", { name: /November 2026/ })).toBeNull();
    expect(within(nav).queryByRole("button")).toBeNull();
    const previous = within(nav).getByRole("link", { name: /September 2026/ });
    expect(previous.getAttribute("href")).toBe("/portfolio?from=2026-09-01&to=2026-09-30");
    fireEvent.click(previous);
    expect(document.querySelector("[data-location]")!.textContent).toBe("/portfolio?from=2026-09-01&to=2026-09-30");
  });

  it("with a next month in E2's nav the next link sets the range to its days", async () => {
    renderMonth(clientOf(() => ({ status: "loaded", body: worldA() })), { nav: { previous: SEPTEMBER, next: NOVEMBER } });
    await settled();
    const next = within(screen.getByRole("navigation", { name: "Month" })).getByRole("link", { name: /November 2026/ });
    expect(next.getAttribute("href")).toBe("/portfolio?from=2026-11-01&to=2026-11-30");
  });

  it("the page reads the month it is given, never one from the address (the month prop, not ?month=)", async () => {
    const client = clientOf(() => ({ status: "loaded", body: worldA() }));
    renderMonth(client, { month: "2026-09" });
    await settled();
    expect(client.calls).toEqual(["2026-09"]);
  });

  it("E2's notes are drawn as period notes in the header", async () => {
    renderMonth(clientOf(() => ({ status: "loaded", body: stateBody("NO_SNAPSHOT", "x") })), { notes: ["A note from E2."] });
    await settled();
    const note = document.querySelector(".dd-head .dd-period[role=note]");
    expect(note!.textContent).toBe("A note from E2.");
  });
});

// IA-P2 P3b (spec §2.2, D-IAP.4): 5c test 13 pinned the tab row of the old five-tab Portfolio (counts, "The month" as a
// second tab) against a before-file. The spec replaced that row with three tabs and no counts; its
// replacement is `portfolioHub.test.tsx` "shows exactly three tabs in order, each keeping the address's range".

describe("5c rev 4 screen fix: bars and scale (D-5C.27), the mute rule (D-5C.26), drawers (L1, L2)", () => {
  const track = (root: ParentNode, key: string) => root.querySelector(`[data-dd-step="${key}"] .dd-wf__track`) as HTMLElement;

  it("World A: each step's served bar on its track, O&M and staff tracks empty, the two scale marks", async () => {
    const a = worldA();
    const view = renderMonth(clientOf(() => ({ status: "loaded", body: a })));
    await settled();
    const bar = (key: string) => track(view.container, key).querySelector(".dd-wf__bar") as HTMLElement | null;
    // jsdom's CSSOM writes the served "0.00%" as "0%"; the served string is the source (fixture literal, spec §6).
    expect(a.bridge!.groups[0].steps[0].bar).toEqual({ left: "0.00", width: "4.34", tone: "lowers" });
    expect(bar("revenue")!.style.left).toBe("0%");
    expect(bar("revenue")!.style.width).toBe("4.34%");
    expect(bar("revenue")!.classList.contains("dd-wf__bar--lowers")).toBe(true);
    expect(bar("fuel_cost")!.style.left).toBe("0%");
    expect(bar("fuel_cost")!.style.width).toBe("100%");
    expect(bar("om")).toBeNull();
    expect(bar("staff")).toBeNull();
    for (const step of a.bridge!.groups.flatMap((g) => g.steps)) {
      expect(track(view.container, step.key).getAttribute("aria-hidden")).toBe("true");
    }
    const scale = view.container.querySelector(".dd-wf__scale")!;
    expect(scale.closest("[aria-hidden='true']")).not.toBeNull();
    const marks = [...scale.querySelectorAll<HTMLElement>(".dd-wf__mark")];
    const t = a.bridge!.totals;
    expect(marks.map((m) => [m.textContent, m.style.left])).toEqual([
      [`${t.target_label} ${t.target}`, "4.34%"],
      [`${t.actual_label} ${t.actual}`, "100%"],
    ]);
    expect(marks[1].classList.contains("dd-wf__mark--end")).toBe(true);
    expect(a.bridge!.scale).toEqual({ target_at: "4.34", actual_at: "100.00" });
  });

  it("D-5C.29: the cash sentence and the table's Billed column render exactly as served", async () => {
    const a = worldA();
    renderMonth(clientOf(() => ({ status: "loaded", body: a })));
    await settled();
    const cash = screen.getByRole("heading", { name: a.cash!.title }).closest("section")!;
    expect(a.cash!.text).toBe(
      "Of $9,688.00 billed for October, $8,870.00 has been collected, $150.00 is paid but in transit and $668.00 is still outstanding.",
    );
    expect(within(cash as HTMLElement).getByText(a.cash!.text).tagName).toBe("P");
    const heads = [...cash.querySelectorAll("thead th")].map((th) => th.textContent);
    expect(heads).toEqual(a.cash!.table.columns);
    expect(heads[1]).toBe("Billed");
    const rows = [...cash.querySelectorAll("tbody tr")].map((tr) => [...tr.children].map((c) => c.textContent));
    expect(rows).toEqual(a.cash!.table.rows.slice(0, 10));
    expect([...cash.querySelectorAll("tfoot tr > *")].map((c) => c.textContent)).toEqual(a.cash!.table.total);
    expect(cash.textContent).not.toContain("expected");
  });

  it("World X: no bar, no scale, no chip reads Not available yet; no-figure slots carry dd-na, Assure does not", async () => {
    const x = worldX();
    const view = renderMonth(clientOf(() => ({ status: "loaded", body: x })));
    await settled();
    expect(view.container.querySelector(".dd-wf__bar")).toBeNull();
    expect(view.container.querySelector(".dd-wf__scale")).toBeNull();
    expect(view.container.querySelectorAll(".dd-wf__track").length).toBe(x.bridge!.groups.flatMap((g) => g.steps).length);
    expect([...view.container.querySelectorAll("[data-dd-word]")].map((c) => c.textContent)).not.toContain("Not available yet");
    const muted = (sel: string) => view.container.querySelector(sel)!.classList.contains("dd-na");
    expect(muted('[data-dd-tile="contribution"] .dd-kpi__value')).toBe(true);
    expect(muted('[data-dd-tile="gap"] .dd-kpi__value')).toBe(true);
    expect(muted('[data-dd-step="revenue"] .dd-wf__value')).toBe(true);
    expect(muted('[data-dd-step="fuel_cost"] .dd-wf__value')).toBe(false);
    expect(muted('[data-dd-outcome="optimize"] .dd-card__value')).toBe(true);
    expect(muted('[data-dd-outcome="assure"] .dd-card__value')).toBe(false);
  });

  it("the mute follows the served shape, never a key: word null mutes, a word unmutes, on any tile, step or driver", async () => {
    const a = worldA();
    a.tiles![0].word = null; // contribution with no word: muted
    a.tiles![2].word = "Recorded"; // a plan tile with a word: not muted
    const fuel = a.bridge!.groups[1].steps[0];
    fuel.word = null;
    a.bridge!.groups[0].steps[0].drawer.drivers = [
      { key: "kwh", label: "Energy sold", value: "−$10.00", sites: "1 of 3 Sites", detail: null, word: null, children: [] },
    ];
    const view = renderMonth(clientOf(() => ({ status: "loaded", body: a })));
    await settled();
    const muted = (sel: string) => view.container.querySelector(sel)!.classList.contains("dd-na");
    expect(muted('[data-dd-tile="contribution"] .dd-kpi__value')).toBe(true);
    expect(muted(`[data-dd-tile="${a.tiles![2].key}"] .dd-kpi__value`)).toBe(false);
    expect(muted(`[data-dd-tile="${a.tiles![3].key}"] .dd-kpi__value`)).toBe(true);
    expect(muted('[data-dd-step="fuel_cost"] .dd-wf__value')).toBe(true);
    expect(muted('[data-dd-step="revenue"] .dd-wf__value')).toBe(false);
    fireEvent.click(screen.getByRole("button", { name: /^Revenue / }));
    expect(openDialog().querySelector("[data-dd-driver] > .dd-num")!.classList.contains("dd-na")).toBe(true);
  });

  it("L1: after Show all 12 focus is on row 11 inside the dialog; Escape and Tab work wherever focus is", async () => {
    const a = worldA();
    const revenue = a.bridge!.groups[0].steps[0].drawer;
    revenue.sites = Array.from({ length: 12 }, (_, i) => ({ ...revenue.sites[i % 3], site: `Site ${i + 1}` }));
    renderMonth(clientOf(() => ({ status: "loaded", body: a })));
    await settled();
    const opener = screen.getByRole("button", { name: /^Revenue / });
    opener.focus();
    fireEvent.click(opener);
    const dialog = screen.getByRole("dialog", { name: "Revenue" });
    fireEvent.click(within(dialog).getByRole("button", { name: "Show all 12" }));
    const rows = dialog.querySelectorAll<HTMLElement>(".dd-site");
    expect(document.activeElement).toBe(rows[10]);
    expect(rows[10].tabIndex).toBe(-1);
    expect(rows[10].textContent).toContain("Site 11");
    // Focus on a row (tabindex -1, outside the cycle): Tab wraps to the first control instead of leaving the dialog.
    const cycle = [...dialog.querySelectorAll<HTMLElement>("button, a[href], summary, [tabindex='0']")];
    fireEvent.keyDown(document.activeElement as HTMLElement, { key: "Tab" });
    expect(document.activeElement).toBe(cycle[0]);
    expect(dialog.contains(document.activeElement)).toBe(true);
    // Focus lost to the page: Tab brings it back into the dialog, Escape on the document still closes.
    (document.activeElement as HTMLElement).blur();
    expect(document.activeElement).toBe(document.body);
    fireEvent.keyDown(document.body, { key: "Tab" });
    expect(dialog.contains(document.activeElement)).toBe(true);
    (document.activeElement as HTMLElement).blur();
    fireEvent.keyDown(document.body, { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(opener);
  });

  it("L2: body carries dd-locked while a drawer is open, not after it closes or the page unmounts", async () => {
    const view = renderMonth(clientOf(() => ({ status: "loaded", body: worldA() })));
    await settled();
    expect(document.body.classList.contains("dd-locked")).toBe(false);
    fireEvent.click(screen.getByRole("button", { name: /^Revenue / }));
    expect(document.body.classList.contains("dd-locked")).toBe(true);
    fireEvent.click(within(openDialog()).getByRole("button", { name: "Close" }));
    expect(document.body.classList.contains("dd-locked")).toBe(false);
    fireEvent.click(screen.getByRole("button", { name: /^Revenue / }));
    expect(document.body.classList.contains("dd-locked")).toBe(true);
    view.unmount();
    expect(document.body.classList.contains("dd-locked")).toBe(false);
  });
});
