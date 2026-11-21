#!/usr/bin/env node
// 5c (spec §5.3, §5.4; D-5C.14): the hub gates of "The month", checked on the built React page.
//
// usage: node tools/deep_dive_gates.cjs <base-url> <fixture.json> [--plant NAME] [--shots DIR] [--world NAME]
// `--world` names the views and shots (default "A"; "X" for the currency-mismatch world).
// Needs /opt/assetecon/tools/pw/env.sh sourced (PW, CHROME) and LD_LIBRARY_PATH=$AUDIT_LD_LIBRARY_PATH; runs inside
// the heavy-tool slot pool. The script answers `/api/portfolio/month*` with the fixture through `page.route`, opens
// `<base-url>/portfolio/month?month=2026-10` at 1440 x 900, 1280 x 720 and 390 x 844, each light and dark, plus A with
// D's headline (the longest) at 1440 and 1280 light, runs the checks on each and G2's static part over
// `frontend/src/estate/deepDiveMonth.css`. One JSON line per view; exit 1 on any failure.
//
// Plants (`--plant`), each must fail its named check: block, headline, levels, height, fold, status, scroll, lint.
"use strict";
const fs = require("fs");
const path = require("path");
const { assertHeavySlot } = require("./heavy_slot_check.cjs");

assertHeavySlot("browser capture"); // a browser capture runs only inside the heavy-tool slot pool

const SCALE = [12, 13, 14, 16, 20, 24, 32];
const D_HEADLINE = "Contribution is $747.00 below target in October; cost and efficiency explain $730.00 of it. Compared for 2 of 3 Sites.";
const PLANTS = ["block", "headline", "levels", "height", "fold", "status", "scroll", "lint"];
const CSS_PATH = path.join(__dirname, "..", "frontend", "src", "estate", "deepDiveMonth.css");

function parseArgs(argv) {
  const out = { base: argv[0], fixture: argv[1], plant: null, shots: null, world: "A" };
  for (let i = 2; i < argv.length; i += 1) {
    if (argv[i] === "--plant") out.plant = argv[++i];
    else if (argv[i] === "--shots") out.shots = argv[++i];
    else if (argv[i] === "--world") out.world = argv[++i];
  }
  if (!out.base || !out.fixture) throw new Error("usage: deep_dive_gates.cjs <base-url> <fixture.json> [--plant NAME] [--shots DIR] [--world NAME]");
  if (out.plant !== null && !PLANTS.includes(out.plant)) throw new Error(`unknown plant ${out.plant}`);
  return out;
}

/** G2's static part: every px font size on the scale; no colour literal outside `:root` and dark token blocks. */
function lintCss(text) {
  const failures = [];
  for (const m of text.matchAll(/font-size\s*:\s*([\d.]+)px/g)) {
    if (!SCALE.includes(Number(m[1]))) failures.push(`font-size ${m[1]}px is off the scale`);
  }
  // Remove the token blocks (`:root { ... }` and any `prefers-color-scheme: dark` block) and comments, then look for colours.
  let rest = text.replace(/\/\*[\s\S]*?\*\//g, "");
  rest = rest.replace(/:root\s*\{[^}]*\}/g, "");
  rest = rest.replace(/@media[^{]*prefers-color-scheme:\s*dark[^{]*\{(?:[^{}]*\{[^}]*\})*[^{}]*\}/g, "");
  for (const m of rest.matchAll(/#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(/g)) failures.push(`colour literal ${m[0]} outside the token blocks`);
  return failures;
}

async function checkView(browser, args, fixture, view) {
  const ctx = await browser.newContext({ viewport: { width: view.w, height: view.h }, colorScheme: view.dark ? "dark" : "light" });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const body = view.dHeadline ? { ...fixture, headline: { ...fixture.headline, text: D_HEADLINE } } : fixture;
  await page.route("**/api/**", (route) => {
    const url = new URL(route.request().url());
    if (url.pathname === "/api/portfolio/month") {
      return route.fulfill({ status: 200, contentType: "application/json", headers: { "Cache-Control": "no-store" }, body: JSON.stringify(body) });
    }
    return route.fulfill({ status: 404, contentType: "application/json", body: "{}" });
  });
  await page.goto(`${args.base.replace(/\/$/, "")}/portfolio/month?month=2026-10`);
  await page.waitForSelector(".dd-status", { timeout: 20000 });
  await page.evaluate(() => document.fonts.ready);
  if (args.plant !== null && args.plant !== "lint") {
    await page.evaluate(({ plant, narrow }) => {
      const hub = document.querySelector('[data-shape="hub"]');
      const block = (h, w) => {
        const d = document.createElement("div");
        d.setAttribute("data-plant", "");
        d.style.height = `${h}px`;
        if (w) d.style.width = `${w}px`;
        d.textContent = "plant";
        return d;
      };
      if (plant === "block") hub.querySelector('[data-level="L3"]').appendChild(block(20));
      if (plant === "headline") {
        const h = hub.querySelector(".dd-headline");
        h.textContent = `${h.textContent} ${h.textContent} ${h.textContent}`;
      }
      if (plant === "levels") hub.querySelector('[data-level="L2"]').removeAttribute("data-level");
      if (plant === "height") hub.querySelector('[aria-labelledby="dd-bridge-h"]').appendChild(block(3000));
      if (plant === "fold") hub.querySelector(".dd-lead").prepend(block(800));
      if (plant === "status") hub.querySelector(".dd-status").style.display = "none";
      if (plant === "scroll" && narrow) hub.querySelector(".dd-lead").appendChild(block(20, 600));
    }, { plant: args.plant, narrow: view.w <= 600 });
  }
  const m = await page.evaluate(({ statusText, scale, w, h }) => {
    const hub = document.querySelector('[data-shape="hub"]');
    const visible = (e) => {
      const r = e.getBoundingClientRect();
      const cs = getComputedStyle(e);
      return r.width > 0 && r.height > 0 && cs.visibility !== "hidden" && cs.display !== "none";
    };
    const levels = ["L1", "L2", "L3"].map((l) => hub.querySelector(`:scope > [data-level="${l}"]`) !== null);
    let blocks = 0;
    for (const region of hub.querySelectorAll(":scope > [data-level]")) {
      for (const child of region.children) if (!child.classList.contains("dd-drawer") && visible(child)) blocks += 1;
    }
    const headline = hub.querySelector(".dd-headline");
    const hcs = getComputedStyle(headline);
    const headlineLines = Math.round(headline.getBoundingClientRect().height / parseFloat(hcs.lineHeight));
    const l1 = hub.querySelector('[data-level="L1"]');
    const l1Bottom = l1 ? Math.max(...[...l1.children].map((c) => c.getBoundingClientRect().bottom + scrollY)) : Infinity;
    const status = hub.querySelector(".dd-status");
    const statusVisible = status !== null && visible(status) && status.textContent === statusText;
    const leadBottom = Math.max(headline.getBoundingClientRect().bottom, status ? status.getBoundingClientRect().bottom : Infinity) + scrollY;
    const hubHeight = Math.round(hub.getBoundingClientRect().height);
    const pageWidth = document.documentElement.scrollWidth;
    const sizes = {};
    let under12 = 0;
    const off = new Set();
    for (const e of document.body.querySelectorAll("*")) {
      if (!visible(e) || ![...e.childNodes].some((c) => c.nodeType === 3 && c.textContent.trim())) continue;
      const fs = parseFloat(getComputedStyle(e).fontSize);
      sizes[fs] = (sizes[fs] || 0) + 1;
      if (fs < 12) under12 += 1;
      if (!scale.includes(fs) && hub.contains(e)) off.add(fs);
    }
    return { levels, blocks, headlineLines, l1Bottom: Math.round(l1Bottom), leadBottom: Math.round(leadBottom), statusVisible, hubHeight, pageWidth, w, h, sizes, under12, offScale: [...off] };
  }, { statusText: body.status_line, scale: SCALE, w: view.w, h: view.h });
  const failures = [];
  if (!m.levels.every(Boolean)) failures.push("levels: a data-level region is missing");
  if (m.blocks > 6) failures.push(`block: ${m.blocks} blocks, at most 6`);
  if ((view.w === 1440 || view.w === 1280) && m.headlineLines > 2) failures.push(`headline: ${m.headlineLines} lines, at most 2`);
  if ((view.w === 1440 || view.w === 1280) && m.l1Bottom > view.h) failures.push(`fold: L1 ends at ${m.l1Bottom} px, below the ${view.h} px fold`);
  if (view.w === 390 && m.leadBottom > view.h) failures.push(`fold: the headline and status end at ${m.leadBottom} px, below ${view.h} px`);
  if (view.w === 1440 && m.hubHeight > 2500) failures.push(`height: the hub is ${m.hubHeight} px, at most 2,500`);
  if (!m.statusVisible) failures.push("status: the status line is not visible with its text");
  if (view.w === 390 && m.pageWidth !== view.w) failures.push(`scroll: page width ${m.pageWidth} px at a ${view.w} px viewport`);
  if (errors.length > 0) failures.push(`errors: ${errors.length} page errors (${errors[0]})`);
  if (m.under12 > 0) failures.push(`text: ${m.under12} visible texts under 12 px`);
  if (m.offScale.length > 0) failures.push(`scale: font sizes ${m.offScale.join(", ")} px are off the guide's scale`);
  if (args.shots && args.plant === null) {
    fs.mkdirSync(args.shots, { recursive: true });
    await page.screenshot({ path: path.join(args.shots, `${view.name}.png`), fullPage: true });
  }
  await ctx.close();
  return { view: view.name, plant: args.plant, ...m, errors: errors.length, failures, pass: failures.length === 0 };
}

(async () => {
  const args = parseArgs(process.argv.slice(2));
  const fixture = JSON.parse(fs.readFileSync(args.fixture, "utf8"));
  let failed = false;
  let css = fs.readFileSync(CSS_PATH, "utf8");
  if (args.plant === "lint") css += "\n.dd-plant { font-size: 11px; color: #123456; }\n";
  const lint = lintCss(css);
  console.log(JSON.stringify({ view: "lint", plant: args.plant, failures: lint.map((f) => `lint: ${f}`), pass: lint.length === 0 }));
  if (lint.length > 0) failed = true;
  const { chromium } = require(process.env.PW);
  const browser = await chromium.launch({ executablePath: process.env.CHROME });
  const views = [];
  for (const [w, h] of [[1440, 900], [1280, 720], [390, 844]]) {
    for (const dark of [false, true]) views.push({ name: `${args.world}-${w}x${h}-${dark ? "dark" : "light"}`, w, h, dark, dHeadline: false });
  }
  views.push({ name: `${args.world}-with-D-headline-1440x900-light`, w: 1440, h: 900, dark: false, dHeadline: true });
  views.push({ name: `${args.world}-with-D-headline-1280x720-light`, w: 1280, h: 720, dark: false, dHeadline: true });
  try {
    for (const view of views) {
      const r = await checkView(browser, args, fixture, view);
      console.log(JSON.stringify(r));
      if (!r.pass) failed = true;
    }
  } finally {
    await browser.close();
  }
  process.exit(failed ? 1 : 0);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
