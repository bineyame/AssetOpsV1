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
//   R6 no visible text under 12 px.
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
const RANGE = "from=2026-10-01&to=2026-10-31";

/** Spec §2.1 after IA-P1's P1 (kind|label|group). */
const RAIL = [
  "live|Portfolio|OPERATIONS",
  "live|Sites|OPERATIONS",
  "unavailable|Assets & cover|OPERATIONS",
  "live|Findings|INTELLIGENCE",
  "unavailable|Decisions|WORK",
  "unavailable|Plan|WORK",
  "live|Actions|WORK",
  "live|Incidents|WORK",
  "live|Maintenance|WORK",
  "unavailable|Results|ASSURANCE",
  "live|Evidence & records|ASSURANCE",
  "live|Financials|BUSINESS",
  "unavailable|Settings|ADMIN",
];

/** Spec §2.4 aliases landed so far: [from, target pathname, target's own query]. */
const ALIASES = [
  ["/", "/portfolio", {}],
  ["/operational-records", "/evidence/records", {}],
];

/** Landed pages and their R3 regions. */
const PAGES = [
  { path: "/portfolio", rail: "Portfolio", regions: [] },
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
    const body = routes.get(url.pathname);
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
    for (const alias of ALIASES) report(await checkAlias(browser, args, routes, alias));
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
