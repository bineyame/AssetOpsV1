#!/usr/bin/env node
// IA-P (spec §6 "tools/iap_gates.cjs"; the deep_dive_gates.cjs pattern): the frame gates of the IA shape, checked on
// the built React app. New in P1; each unit extends it.
//
// usage: node tools/iap_gates.cjs <base-url> [--plant NAME] [--shots DIR]
// Needs /opt/assetecon/tools/pw/env.sh sourced (PW, CHROME) and LD_LIBRARY_PATH=$AUDIT_LD_LIBRARY_PATH; runs inside the
// heavy-tool slot pool. `/api/*` is answered from `frontend/src/estate/__tests__/fixtures/iap/` through `page.route`
// (`routes.json` maps an API pathname to a fixture file); any other `/api/*` answers 404 (handshake I11).
//
// Checks (per landed unit):
//   R1 the rail's groups, items, order and live or unavailable states equal spec §2.1;
//   R2 every live alias lands on its target with the query kept;
//   R3 each landed page's regions (P1: the Evidence & records H1 and its tab row with the current tab);
//   R4 at 390 the page width equals the viewport;
//   R5 no page error;
//   R6 no visible text under 12 px;
//   R7 /findings on a 61-day range sends from=2026-10-01 and the bar tags it "inside";
//   R8 the rail Portfolio link from that page keeps from=2026-09-01;
//   L1 each list page (Decisions, Findings, Actions) draws one data-shape="list" of its own key;
//   L2 each list row holds exactly one interactive element (its title link) and Tab moves one stop per row;
//   L3 /portfolio/act-first?lens=cost lands on /decisions?lens=cost and shows the chip "Cost · All findings";
//   H1 the Portfolio shows three tabs in spec 2.2's order (Overview, Outcomes, Demand & capacity), each keeping the range;
//   H2 in every mode (month, period, none) the Overview has at most 6 blocks and no [data-portfolio-card-value];
//   H3 deep_dive_gates.cjs passes at /portfolio?from=2026-10-01&to=2026-10-31 (run separately, with its URL argument);
//   H4 mode period (2026-09-01 to 2026-10-31): the hub regions, R4 at 390, the bar's "All pages", each month row lands on its month;
//   H5 mode none (2026-11-15 to 2026-11-21): the notes are visible, "Show October 2026" lands on October's range and renders the month;
//   H6 /portfolio?from=2026-10-01&to=2026-11-21: the bar's tag is data-shared-range-focus="inside".
// Expected values are spec literals held here, never read from the app's modules (W2 independence).
//
// In-page plants (`--plant`): `wide` (a 600 px block at 390 fails R4), `tiny` (an 11 px text fails R6). The source
// plants of spec §6 (`rail`, `alias`, …) are one-line edits rebuilt and run without `--plant`.
"use strict";
const fs = require("fs");
const path = require("path");
const { assertHeavySlot } = require("./heavy_slot_check.cjs");

assertHeavySlot("browser capture");

const FIXTURES = path.join(__dirname, "..", "frontend", "src", "estate", "__tests__", "fixtures", "iap");
const PLANTS = ["wide", "tiny"];
const WORLD_A_MONTH = path.join(__dirname, "..", "backend", "tests", "fixtures", "5c", "deep_dive_lakeside_2026-10.json");
/** E2 (`/api/portfolio/period`) by the range asked (IA-P2 P3b): a range not listed answers the one-month body. */
const PERIOD_BY_RANGE = {
  "2026-09-01|2026-10-31": "period-period-2026-09-10.json",
  "2026-11-15|2026-11-21": "period-none-2026-11.json",
};
const PERIOD_DEFAULT = "period-month-2026-10.json";
const RANGE = "from=2026-10-01&to=2026-10-31";

/** Spec §2.1 after IA-P1's P2 (kind|label|group): Decisions is live. */
const RAIL = [
  "live|Portfolio|OPERATIONS",
  "live|Sites|OPERATIONS",
  "unavailable|Assets & cover|OPERATIONS",
  "live|Findings|INTELLIGENCE",
  "live|Decisions|WORK",
  "unavailable|Plan|WORK",
  "live|Actions|WORK",
  "live|Incidents|WORK",
  "live|Maintenance|WORK",
  "live|Results|ASSURANCE",
  "live|Evidence & records|ASSURANCE",
  "live|Financials|BUSINESS",
  "unavailable|Settings|ADMIN",
];

/** Spec §2.4 aliases landed so far: [from, target pathname, target's own query]. */
const ALIASES = [
  ["/", "/portfolio", {}],
  ["/operational-records", "/evidence/records", {}],
  // IA-P2 P3b (spec 2.4)
  ["/portfolio/opportunity", "/portfolio/demand-and-capacity", {}],
  ["/portfolio/changes", "/results", {}],
  ["/portfolio/scope", "/evidence", {}],
];

/** Landed pages and their R3 regions. */
const PAGES = [
  { path: "/portfolio", rail: "Portfolio", regions: [] },
  { path: "/portfolio/outcomes", rail: "Portfolio", h1: "Portfolio", tabs: ["Overview", "Outcomes", "Demand & capacity"], current: "Outcomes" },
  { path: "/portfolio/demand-and-capacity", rail: "Portfolio", h1: "Portfolio", tabs: ["Overview", "Outcomes", "Demand & capacity"], current: "Demand & capacity" },
  { path: "/results", rail: "Results", h1: "Results", tabs: [], current: "" },
  { path: "/decisions", rail: "Decisions", list: "decisions" },
  { path: "/findings", rail: "Findings", list: "findings" },
  { path: "/actions", rail: "Actions", list: "actions" },
  { path: "/evidence", rail: "Evidence & records", h1: "Evidence & records", tabs: ["Coverage", "Records"], current: "Coverage" },
  { path: "/evidence/records", rail: "Evidence & records", h1: "Evidence & records", tabs: ["Coverage", "Records"], current: "Records" },
];

function parseArgs(argv) {
  const out = { base: argv[0], plant: null, shots: null };
  for (let i = 1; i < argv.length; i += 1) {
    if (argv[i] === "--plant") out.plant = argv[++i];
    else if (argv[i] === "--shots") out.shots = argv[++i];
  }
  if (!out.base) throw new Error("usage: iap_gates.cjs <base-url> [--plant NAME] [--shots DIR]");
  if (out.plant !== null && !PLANTS.includes(out.plant)) throw new Error(`unknown plant ${out.plant}`);
  out.base = out.base.replace(/\/$/, "");
  return out;
}

function loadRoutes() {
  const map = JSON.parse(fs.readFileSync(path.join(FIXTURES, "routes.json"), "utf8"));
  const out = new Map();
  for (const [api, file] of Object.entries(map)) {
    if (api.startsWith("_")) continue;
    out.set(api, fs.readFileSync(path.join(FIXTURES, file), "utf8"));
  }
  return out;
}

async function openPage(browser, routes, view) {
  const ctx = await browser.newContext({ viewport: { width: view.w, height: view.h }, colorScheme: view.dark ? "dark" : "light" });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.route("**/api/**", (route) => {
    const url = new URL(route.request().url());
    let body = routes.get(url.pathname);
    if (url.pathname === "/api/portfolio/period") {
      const key = `${url.searchParams.get("from")}|${url.searchParams.get("to")}`;
      body = fs.readFileSync(path.join(FIXTURES, PERIOD_BY_RANGE[key] ?? PERIOD_DEFAULT), "utf8");
    } else if (url.pathname === "/api/portfolio/month") body = fs.readFileSync(WORLD_A_MONTH, "utf8");
    if (body !== undefined) return route.fulfill({ status: 200, contentType: "application/json", headers: { "Cache-Control": "no-store" }, body });
    return route.fulfill({ status: 404, contentType: "application/json", body: "{}" });
  });
  return { ctx, page, errors };
}

/** R1: the rail as rendered, kind|label|group in order. */
async function readRail(page) {
  return page.evaluate(() => {
    const nav = document.querySelector('nav[aria-label="Operator routes"]');
    if (!nav) return [];
    const out = [];
    let group = "";
    for (const el of nav.querySelectorAll("[data-rail-group], .nav-rail__group-label, li")) {
      if (el.matches("[data-rail-group], .nav-rail__group-label")) {
        group = (el.getAttribute("data-rail-group") || el.textContent || "").trim();
        continue;
      }
      if (el.hasAttribute("data-rail-unavailable")) out.push(`unavailable|${el.getAttribute("data-rail-unavailable")}|${group}`);
      else {
        const label = el.querySelector(".nav-rail__label");
        if (label && el.querySelector("a")) out.push(`live|${label.textContent.trim()}|${group}`);
      }
    }
    return out;
  });
}

async function measure(page, plant, narrow) {
  if (plant !== null) {
    await page.evaluate(({ plant, narrow }) => {
      const main = document.querySelector("main") || document.body;
      const d = document.createElement("div");
      d.setAttribute("data-plant", "");
      d.textContent = "plant";
      if (plant === "wide" && narrow) d.style.width = "600px";
      if (plant === "tiny") d.style.fontSize = "11px";
      main.appendChild(d);
    }, { plant, narrow });
  }
  return page.evaluate(() => {
    let under12 = 0;
    for (const e of document.querySelectorAll("body *")) {
      if (e.children.length > 0 && ![...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim() !== "")) continue;
      if (!(e.textContent || "").trim()) continue;
      const st = getComputedStyle(e);
      const r = e.getBoundingClientRect();
      if (st.visibility === "hidden" || st.display === "none" || r.width === 0 || r.height === 0) continue;
      if (st.clip === "rect(0px, 0px, 0px, 0px)" || st.clipPath === "inset(50%)") continue;
      if (parseFloat(st.fontSize) < 12) under12 += 1;
    }
    return { pageWidth: document.documentElement.scrollWidth, under12 };
  });
}

async function checkPage(browser, args, routes, spec, view) {
  const { ctx, page, errors } = await openPage(browser, routes, view);
  await page.goto(`${args.base}${spec.path}?${RANGE}`);
  await page.waitForSelector('nav[aria-label="Operator routes"]', { state: "attached", timeout: 20000 });
  await page.waitForTimeout(600);
  await page.evaluate(() => document.fonts.ready);
  const failures = [];
  const rail = await readRail(page);
  if (rail.join(";") !== RAIL.join(";")) failures.push(`R1: rail is [${rail.join("; ")}], spec §2.1 is [${RAIL.join("; ")}]`);
  const current = await page.evaluate(() => [...document.querySelectorAll('nav[aria-label="Operator routes"] a[aria-current="page"] .nav-rail__label')].map((e) => e.textContent.trim()));
  if (current.join() !== spec.rail) failures.push(`R1: the current rail item is [${current.join(", ")}], expected ${spec.rail}`);
  if (spec.h1) {
    const r3 = await page.evaluate(() => ({
      h1: (document.querySelector("h1") || {}).textContent || "",
      tabs: [...document.querySelectorAll("[data-section-tabs] a")].map((a) => ({ text: a.textContent.trim(), current: a.getAttribute("aria-current"), href: a.getAttribute("href") })),
    }));
    if (r3.h1.trim() !== spec.h1) failures.push(`R3: H1 is "${r3.h1.trim()}", expected "${spec.h1}"`);
    if (r3.tabs.map((t) => t.text).join("|") !== spec.tabs.join("|")) failures.push(`R3: tabs are [${r3.tabs.map((t) => t.text).join(", ")}]`);
    const cur = r3.tabs.filter((t) => t.current === "page").map((t) => t.text);
    if (cur.join() !== spec.current) failures.push(`R3: current tab is [${cur.join(", ")}], expected ${spec.current}`);
    for (const t of r3.tabs) if (!/from=2026-10-01/.test(t.href || "")) failures.push(`R3: tab ${t.text} drops the range (${t.href})`);
  }
  // M3: a refusal on a served page is a failure. A list page's fixtures are all served, so any refusal fails; on every
  // page, a refusal of the range itself fails (the range in this gate is a valid 1 to 31 October).
  const refusals = await page.evaluate(() => [...document.querySelectorAll("[data-page-refusal]")].map((e) => e.getAttribute("data-page-refusal")));
  for (const code of refusals) if (spec.list || /^INVALID_/.test(code)) failures.push(`R3: ${spec.path} shows a refusal screen (${code})`);
  if (spec.list) failures.push(...(await checkList(page, spec, view)));
  if (view.menu) {
    await page.click(".app-frame__menu-toggle");
    await page.waitForTimeout(200);
  }
  const m = await measure(page, args.plant, view.w === 390);
  if (view.w === 390 && m.pageWidth !== view.w) failures.push(`R4: page width ${m.pageWidth} px at a ${view.w} px viewport`);
  if (errors.length > 0) failures.push(`R5: ${errors.length} page errors (${errors[0]})`);
  if (m.under12 > 0) failures.push(`R6: ${m.under12} visible texts under 12 px`);
  if (args.shots && args.plant === null) {
    fs.mkdirSync(args.shots, { recursive: true });
    const name = `${spec.path.replace(/\//g, "_") || "_root"}-${view.name}${view.menu ? "-menu" : ""}.png`;
    await page.screenshot({ path: path.join(args.shots, name), fullPage: !view.menu });
  }
  await ctx.close();
  return { gate: "page", page: spec.path, view: view.name, menu: !!view.menu, plant: args.plant, ...m, errors: errors.length, failures, pass: failures.length === 0 };
}

/** L1 and L2 on a list page (the page waits for its rows first: the lists read every page before they draw). */
async function checkList(page, spec, view) {
  const failures = [];
  await page.waitForSelector("[data-shape='list'] tbody tr[data-row]", { timeout: 10000 }).catch(() => failures.push(`L1: ${spec.path} drew no list rows`));
  const shapes = await page.evaluate(() => [...document.querySelectorAll("[data-shape='list']")].map((e) => e.getAttribute("data-home-list")));
  if (shapes.join() !== spec.list) failures.push(`L1: ${spec.path} draws lists [${shapes.join(", ")}], expected one "${spec.list}"`);
  const rows = await page.evaluate(() =>
    [...document.querySelectorAll("[data-shape='list'] tbody tr[data-row]")].map((tr) => ({
      n: tr.querySelectorAll("a, button, input, select, textarea, [tabindex]:not([tabindex='-1'])").length,
      said: /Detail not available yet/.test(tr.textContent || ""),
    })),
  );
  if (rows.length === 0) failures.push(`L2: ${spec.path} has no rows to check`);
  // Spec 5.2: a row holds its one control, or none and says "Detail not available yet" (a text row).
  const bad = rows.filter((r) => r.n > 1 || (r.n === 0 && !r.said)).length;
  if (bad > 0) failures.push(`L2: ${bad} of ${rows.length} rows on ${spec.path} do not hold one interactive element, or none with the words Detail not available yet`);
  if (!rows.some((r) => r.n === 0 && r.said)) failures.push(`L2: ${spec.path} fixtures hold no text row, so the no-link path is not covered`);
  if (view.w === 1440 && !view.dark && rows.length >= 2) {
    const first = await page.$("[data-shape='list'] tbody tr[data-row] a");
    if (first) {
      await first.focus();
      await page.keyboard.press("Tab");
      const stops = await page.evaluate(() => {
        const rowsEl = [...document.querySelectorAll("[data-shape='list'] tbody tr[data-row]")];
        const at = rowsEl.findIndex((tr) => tr.contains(document.activeElement));
        return at;
      });
      if (stops !== 1) failures.push(`L2: Tab from row 1 of ${spec.path} landed in row ${stops + 1}, expected row 2`);
    }
  }
  return failures;
}

/** L3: the old Act first lens address lands on the Decisions list with the lens chip. */
async function checkLensAlias(browser, args, routes) {
  const { ctx, page, errors } = await openPage(browser, routes, { w: 1440, h: 900, dark: false });
  await page.goto(`${args.base}/portfolio/act-first?lens=cost&${RANGE}`);
  await page.waitForSelector("[data-shape='list']", { timeout: 10000 }).catch(() => {});
  const failures = [];
  const url = new URL(page.url());
  if (url.pathname !== "/decisions") failures.push(`L3: /portfolio/act-first landed on ${url.pathname}, expected /decisions`);
  if (url.searchParams.get("lens") !== "cost") failures.push(`L3: the lens was lost (${url.search})`);
  const chips = await page.evaluate(() => [...document.querySelectorAll(".hl-chip")].map((e) => (e.textContent || "").trim()));
  if (!chips.includes("Cost · All findings")) failures.push(`L3: chips are [${chips.join(" | ")}], expected "Cost · All findings"`);
  if (errors.length > 0) failures.push(`R5: ${errors.length} page errors (${errors[0]})`);
  await ctx.close();
  return { gate: "lens-alias", landed: `${url.pathname}${url.search}`, chips, failures, pass: failures.length === 0 };
}

async function checkAlias(browser, args, routes, [from, target, own]) {
  const { ctx, page, errors } = await openPage(browser, routes, { w: 1440, h: 900, dark: false });
  await page.goto(`${args.base}${from}?${RANGE}`);
  const failures = [];
  // An address that is not aliased lands on the catch-all, outside the operator shell: that is an R2 failure.
  await page.waitForSelector('nav[aria-label="Operator routes"]', { state: "attached", timeout: 10000 }).catch(() => failures.push(`R2: ${from} rendered no operator page`));
  await page.waitForTimeout(300);
  const url = new URL(page.url());
  if (url.pathname !== target) failures.push(`R2: ${from} landed on ${url.pathname}, expected ${target}`);
  // The range is kept (in either address form) and the target's own query is set.
  if (!/^2026-10-01/.test(url.searchParams.get("from") || "")) failures.push(`R2: ${from} dropped the range (${url.search})`);
  for (const [k, v] of Object.entries(own)) if (url.searchParams.get(k) !== v) failures.push(`R2: ${from} lost ${k}=${v} (${url.search})`);
  if (errors.length > 0) failures.push(`R5: ${errors.length} page errors (${errors[0]})`);
  await ctx.close();
  return { gate: "alias", from, landed: `${url.pathname}${url.search}`, failures, pass: failures.length === 0 };
}

/** R7 and R8 (spec-period.md P.9): a 61-day range on /findings reads the last 31 days; Portfolio keeps the whole range. */
async function checkLongRange(browser, args, routes) {
  const { ctx, page, errors } = await openPage(browser, routes, { w: 1440, h: 900, dark: false });
  const sent = [];
  page.on("request", (r) => {
    const u = new URL(r.url());
    if (u.pathname === "/api/estate/findings") sent.push(u.searchParams.get("from") || "");
  });
  await page.goto(`${args.base}/findings?from=2026-09-01&to=2026-10-31`);
  await page.waitForSelector("[data-shared-range-focus]", { timeout: 10000 }).catch(() => {});
  await page.waitForTimeout(500);
  const failures = [];
  if (sent.length === 0) failures.push("R7: no request reached /api/estate/findings");
  else if (!/^2026-10-01/.test(sent[0])) failures.push(`R7: /api/estate/findings got from=${sent[0]}, expected 2026-10-01`);
  const tag = await page.evaluate(() => document.querySelector("[data-shared-range-focus]")?.getAttribute("data-shared-range-focus") ?? null);
  if (tag !== "inside") failures.push(`R7: the bar's tag is ${tag}, expected inside`);
  const href = await page.evaluate(() => {
    const a = Array.from(document.querySelectorAll('nav[aria-label="Operator routes"] a')).find((x) => x.textContent.trim() === "Portfolio");
    return a ? decodeURIComponent(a.getAttribute("href") || "") : "";
  });
  if (!/from=2026-09-01/.test(href)) failures.push(`R8: the Portfolio rail link is ${href}, expected from=2026-09-01`);
  if (errors.length > 0) failures.push(`R5: ${errors.length} page errors (${errors[0]})`);
  await ctx.close();
  return { gate: "long-range", sent, tag, href, failures, pass: failures.length === 0 };
}


/** The Overview hub as drawn: its levels, its blocks (the visible children of each level, drawers aside) and the old card value. */
async function readHub(page) {
  return page.evaluate(() => {
    const visible = (e) => {
      const r = e.getBoundingClientRect();
      const cs = getComputedStyle(e);
      return r.width > 0 && r.height > 0 && cs.visibility !== "hidden" && cs.display !== "none";
    };
    const hub = document.querySelector('[data-shape="hub"]');
    let blocks = 0;
    const levels = [];
    if (hub) {
      for (const region of hub.querySelectorAll(":scope > [data-level]")) {
        levels.push(region.getAttribute("data-level"));
        for (const child of region.children) if (!child.classList.contains("dd-drawer") && visible(child)) blocks += 1;
      }
    }
    return {
      hub: hub !== null,
      levels,
      blocks,
      cardValues: document.querySelectorAll("[data-portfolio-card-value]").length,
      tabs: [...document.querySelectorAll("[data-section-tabs] a")].map((a) => ({ text: a.textContent.trim(), href: a.getAttribute("href") || "" })),
      notes: [...document.querySelectorAll(".dd-head [role=note]")].filter(visible).map((n) => n.textContent.trim()),
      tag: document.querySelector("[data-shared-range-focus]")?.getAttribute("data-shared-range-focus") ?? null,
      barText: document.querySelector("[data-shared-range-button] .shared-range__tag")?.textContent ?? "",
      bodyText: document.body.textContent,
      pageWidth: document.documentElement.scrollWidth,
    };
  });
}

async function openPortfolio(browser, routes, url, view = { w: 1440, h: 900, dark: false }) {
  const o = await openPage(browser, routes, view);
  await o.page.goto(url);
  await o.page.waitForSelector('nav[aria-label="Operator routes"]', { state: "attached", timeout: 20000 });
  await o.page.waitForSelector("[data-shape='hub'], .dd-head", { timeout: 20000 }).catch(() => {});
  await o.page.waitForTimeout(700);
  return o;
}

/** H1 and H2 over the three modes; then H4, H5 and H6 for their ranges. One result per gate. */
async function checkOverview(browser, args, routes) {
  const results = [];
  const modes = [
    ["month", "from=2026-10-01&to=2026-10-31"],
    ["period", "from=2026-09-01&to=2026-10-31"],
    ["none", "from=2026-11-15&to=2026-11-21"],
  ];
  const TABS = ["Overview", "Outcomes", "Demand & capacity"];
  for (const [mode, range] of modes) {
    const { ctx, page, errors } = await openPortfolio(browser, routes, `${args.base}/portfolio?${range}`);
    const h = await readHub(page);
    const failures = [];
    if (h.tabs.map((t) => t.text).join("|") !== TABS.join("|")) failures.push(`H1: ${mode}: tabs are [${h.tabs.map((t) => t.text).join(", ")}], expected [${TABS.join(", ")}]`);
    for (const t of h.tabs) if (!new RegExp(`from=${range.split("&")[0].slice(5)}`).test(t.href)) failures.push(`H1: ${mode}: tab ${t.text} drops the range (${t.href})`);
    if (h.blocks > 6) failures.push(`H2: ${mode}: ${h.blocks} blocks, at most 6`);
    if (h.cardValues > 0) failures.push(`H2: ${mode}: ${h.cardValues} [data-portfolio-card-value] on the Overview`);
    if (errors.length > 0) failures.push(`R5: ${errors.length} page errors (${errors[0]})`);
    results.push({ gate: "H1H2", mode, levels: h.levels, blocks: h.blocks, tabs: h.tabs.map((t) => t.text), failures, pass: failures.length === 0 });
    await ctx.close();
  }
  // H4: mode period, at 390.
  {
    const range = "from=2026-09-01&to=2026-10-31";
    const failures = [];
    const { ctx, page, errors } = await openPortfolio(browser, routes, `${args.base}/portfolio?${range}`, { w: 390, h: 844, dark: false });
    const h = await readHub(page);
    if (h.levels.join() !== "L1,L2,L3") failures.push(`H4: hub regions are [${h.levels.join(", ")}], expected L1, L2, L3`);
    if (h.pageWidth !== 390) failures.push(`H4/R4: page width ${h.pageWidth} px at 390`);
    if (!/All pages/.test(h.barText)) failures.push(`H4: the bar's tag text is "${h.barText}", expected "All pages"`);
    const hrefs = await page.evaluate(() => [...document.querySelectorAll("[data-period-months] tbody tr th a")].map((a) => a.getAttribute("href")));
    if (hrefs.length !== 2) failures.push(`H4: ${hrefs.length} month row links, expected 2`);
    const landed = [];
    for (let i = 0; i < hrefs.length; i += 1) {
      await page.goto(`${args.base}/portfolio?${range}`);
      await page.waitForSelector("[data-period-months]", { timeout: 20000 }).catch(() => {});
      await (await page.$$("[data-period-months] tbody tr th a"))[i].click();
      await page.waitForTimeout(500);
      const u = new URL(page.url());
      landed.push(`${u.pathname}?from=${u.searchParams.get("from")}&to=${u.searchParams.get("to")}`);
    }
    const want = ["/portfolio?from=2026-09-01&to=2026-09-30", "/portfolio?from=2026-10-01&to=2026-10-31"];
    if (landed.join() !== want.join()) failures.push(`H4: month rows landed on [${landed.join(", ")}], expected [${want.join(", ")}]`);
    if (errors.length > 0) failures.push(`R5: ${errors.length} page errors (${errors[0]})`);
    results.push({ gate: "H4", levels: h.levels, hrefs, landed, bar: h.barText, failures, pass: failures.length === 0 });
    await ctx.close();
  }
  // H5: mode none.
  {
    const failures = [];
    const { ctx, page, errors } = await openPortfolio(browser, routes, `${args.base}/portfolio?from=2026-11-15&to=2026-11-21`);
    const h = await readHub(page);
    if (h.notes.length === 0) failures.push("H5: no visible note in the header");
    // Spec 3 (MD-IAP-11): mode none draws the header, the notes, the link and L2; L1 and L3 are omitted.
    if (h.levels.includes("L1") || h.levels.includes("L3")) failures.push(`H5: L1 or L3 is drawn in mode none ([${h.levels.join(", ")}])`);
    await page.getByRole("link", { name: "Show October 2026" }).click();
    await page.waitForSelector("[data-shape='hub'] [data-level='L1']", { timeout: 20000 }).catch(() => failures.push("H5: October's month did not render after the click"));
    const u = new URL(page.url());
    if (!(u.pathname === "/portfolio" && u.searchParams.get("from") === "2026-10-01" && u.searchParams.get("to") === "2026-10-31")) failures.push(`H5: landed on ${u.pathname}${u.search}, expected October's range`);
    if (errors.length > 0) failures.push(`R5: ${errors.length} page errors (${errors[0]})`);
    results.push({ gate: "H5", notes: h.notes, landed: `${u.pathname}${u.search}`, failures, pass: failures.length === 0 });
    await ctx.close();
  }
  // H6: a range reaching past the served month.
  {
    const failures = [];
    const { ctx, page, errors } = await openPortfolio(browser, routes, `${args.base}/portfolio?from=2026-10-01&to=2026-11-21`);
    const h = await readHub(page);
    if (h.tag !== "inside") failures.push(`H6: the bar's tag is ${h.tag}, expected inside`);
    if (errors.length > 0) failures.push(`R5: ${errors.length} page errors (${errors[0]})`);
    results.push({ gate: "H6", tag: h.tag, failures, pass: failures.length === 0 });
    await ctx.close();
  }
  return results;
}

(async () => {
  const args = parseArgs(process.argv.slice(2));
  const routes = loadRoutes();
  const { chromium } = require(process.env.PW);
  const browser = await chromium.launch({ executablePath: process.env.CHROME });
  let failed = false;
  const report = (r) => {
    console.log(JSON.stringify(r));
    if (!r.pass) failed = true;
  };
  try {
    report(await checkLongRange(browser, args, routes));
    for (const alias of ALIASES) report(await checkAlias(browser, args, routes, alias));
    report(await checkLensAlias(browser, args, routes));
    for (const r of await checkOverview(browser, args, routes)) report(r);
    const views = [];
    for (const [w, h] of [[1440, 900], [390, 844]]) for (const dark of [false, true]) views.push({ name: `${w}x${h}-${dark ? "dark" : "light"}`, w, h, dark });
    for (const spec of PAGES) {
      for (const view of views) report(await checkPage(browser, args, routes, spec, view));
    }
    // 390 with the menu open (spec §6 P1 shots), on the Portfolio.
    report(await checkPage(browser, args, routes, PAGES[0], { name: "390x844-light", w: 390, h: 844, dark: false, menu: true }));
  } finally {
    await browser.close();
  }
  process.exit(failed ? 1 : 0);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
