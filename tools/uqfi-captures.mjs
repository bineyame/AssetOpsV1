#!/usr/bin/env node
/**
 * UQ-FI visual evidence (rev 6 6.3 "Visual evidence", architect-sequence-client-scope-2026-11-11.md).
 *
 *   node tools/uqfi-captures.mjs capture <links.json> <out-dir> [web-base] [--widths 1440,1280] [--narrow 390]
 *
 * - <links.json>: an array of { "case" | "page" | "id": name, "url": absolute URL or a path on [web-base] } in
 *   demo order (the DS-1f links output for the chosen DB). A name starting "P1"/"P2"/"P3" also gets the narrow
 *   sideways-scroll measurement (no picture).
 * - <out-dir>: `Docs/demo-sprint/uqfi-img/before` or `.../after`. Writes `{nn}-{page}-{width}.png` (full page)
 *   and `measure.json`.
 * - Per page and width, measure.json records: the smallest computed font-size of visible text (must be >= 12),
 *   page-level sideways scroll (must be none), the h1 count (must be 1 after), the count of visible gap-fact lines,
 *   and whether Inter is the rendered font. The run exits 1 when any of the first three fails.
 *
 * Same CDP approach as tools/layout-evidence.mjs (Node's fetch and WebSocket, the installed Chrome, no new
 * dependency). Chrome: ASSETOPS_CHROME (default `google-chrome`); port ASSETOPS_CDP_PORT (default 9334).
 * Light theme: the page is emulated with prefers-color-scheme: light. One serve, one Chrome; no DB writes.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const args = process.argv.slice(2);
const flag = (name, fallback) => {
  const i = args.indexOf(name);
  if (i < 0) return fallback;
  const value = args[i + 1];
  args.splice(i, 2);
  return value;
};
const WIDTHS = flag("--widths", "1440,1280").split(",").map(Number);
const NARROW = Number(flag("--narrow", "390"));
const [command, linksPath, outDir, webBase = "http://127.0.0.1:5173"] = args;
if (command !== "capture" || !linksPath || !outDir) {
  console.error("usage: node tools/uqfi-captures.mjs capture <links.json> <out-dir> [web-base] [--widths 1440,1280] [--narrow 390]");
  process.exit(2);
}

const links = JSON.parse(readFileSync(linksPath, "utf8")).map((l, i) => ({
  name: String(l.case ?? l.page ?? l.id ?? `page-${i + 1}`).replace(/[^A-Za-z0-9._-]+/g, "-"),
  url: /^https?:/.test(l.url) ? l.url : new URL(l.url, webBase).toString(),
}));
mkdirSync(outDir, { recursive: true });

const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9334);
const CHROME = process.env.ASSETOPS_CHROME ?? "google-chrome";
const profile = mkdtempSync(join(tmpdir(), "uqfi-cdp-"));
const chrome = spawn(
  CHROME,
  ["--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--hide-scrollbars",
    `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "about:blank"],
  { stdio: "ignore" },
);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const finish = (code) => {
  chrome.kill();
  try { rmSync(profile, { recursive: true, force: true }); } catch { /* best effort */ }
  process.exit(code);
};

async function pageSocketUrl() {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    try {
      const targets = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
      const page = targets.find((t) => t.type === "page");
      if (page?.webSocketDebuggerUrl) return page.webSocketDebuggerUrl;
    } catch { /* not up yet */ }
    await sleep(250);
  }
  throw new Error(`Chrome (${CHROME}) did not expose a page target on port ${PORT}`);
}

class Cdp {
  constructor(ws) {
    this.ws = ws; this.id = 0; this.pending = new Map();
    ws.addEventListener("message", (event) => {
      const msg = JSON.parse(event.data);
      const waiter = msg.id ? this.pending.get(msg.id) : undefined;
      if (!waiter) return;
      this.pending.delete(msg.id);
      clearTimeout(waiter.timer);
      msg.error ? waiter.reject(new Error(JSON.stringify(msg.error))) : waiter.resolve(msg.result);
    });
  }
  send(method, params = {}, timeoutMs = 60000) {
    const id = ++this.id;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { this.pending.delete(id); reject(new Error(`CDP ${method} got no reply in ${timeoutMs}ms`)); }, timeoutMs);
      this.pending.set(id, { resolve, reject, timer });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }
}

// The gap facts a page states (D-E5.46 and the rev 6 collapse targets). A visible line is the nearest block
// element holding one of them; a GapGroup line counts once however many subjects it names.
const MEASURE = `(() => {
  const GAP = /Not available yet|not assessed|No cold assessment|not worked out yet|\\bUnknown\\b|could not be (?:read|loaded)/i;
  const visible = (el) => {
    const s = getComputedStyle(el);
    if (s.display === "none" || s.visibility === "hidden" || Number(s.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  let minFont = Infinity, minAt = null;
  const lines = new Set();
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const el = n.parentElement;
    if (!el || !n.textContent.trim() || !visible(el) || el.closest("[aria-hidden='true'], script, style")) continue;
    const size = parseFloat(getComputedStyle(el).fontSize);
    if (size < minFont) { minFont = size; minAt = n.textContent.trim().slice(0, 60); }
    if (GAP.test(n.textContent)) {
      const group = el.closest("[data-gap-group]");
      let block = group ?? el;
      while (!group && block.parentElement && getComputedStyle(block).display.startsWith("inline")) block = block.parentElement;
      lines.add(block);
    }
  }
  const doc = document.documentElement;
  const interLoaded = [...document.fonts].some((f) => /Inter/.test(f.family) && f.status === "loaded");
  const bodyFamily = getComputedStyle(document.body).fontFamily;
  return {
    minFontPx: minFont === Infinity ? null : minFont, minFontText: minAt,
    sidewaysScroll: doc.scrollWidth > doc.clientWidth + 1, scrollWidth: doc.scrollWidth, clientWidth: doc.clientWidth,
    h1Count: [...document.querySelectorAll("h1")].filter(visible).length,
    gapFactLines: lines.size, gapGroupLines: document.querySelectorAll("[data-gap-group]").length,
    inter: interLoaded && /^"?Inter/.test(bodyFamily) && document.fonts.check('14px "Inter"'), bodyFamily,
    height: Math.ceil(Math.max(doc.scrollHeight, document.body.scrollHeight)),
  };
})()`;

const SETTLED = `(() => document.readyState === "complete" &&
  !/\\bLoading (?:the|how|outcomes|evidence|financials|configured|shipped|saved|persisted)\\b/.test(document.body.innerText))`;

async function open(cdp, url, width, height = 900) {
  await cdp.send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false });
  await cdp.send("Page.navigate", { url });
  const deadline = Date.now() + 45000;
  while (Date.now() < deadline) {
    const r = await cdp.send("Runtime.evaluate", { expression: SETTLED, returnByValue: true });
    if (r.result.value === true) break;
    await sleep(300);
  }
  await cdp.send("Runtime.evaluate", { expression: "document.fonts.ready.then(() => true)", awaitPromise: true, returnByValue: true });
  await sleep(400);
  return (await cdp.send("Runtime.evaluate", { expression: MEASURE, returnByValue: true })).result.value;
}

let failed = false;
try {
  const ws = new WebSocket(await pageSocketUrl());
  await new Promise((resolve) => ws.addEventListener("open", resolve));
  const cdp = new Cdp(ws);
  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");
  await cdp.send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-color-scheme", value: "light" }] });
  const results = [];
  for (const [index, link] of links.entries()) {
    const nn = String(index + 1).padStart(2, "0");
    for (const width of WIDTHS) {
      const m = await open(cdp, link.url, width);
      await cdp.send("Emulation.setDeviceMetricsOverride", { width, height: Math.min(m.height, 16000), deviceScaleFactor: 1, mobile: false });
      const shot = await cdp.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true }, 120000);
      const file = `${nn}-${link.name}-${width}.png`;
      writeFileSync(join(outDir, file), Buffer.from(shot.data, "base64"));
      const checks = { minFontOk: m.minFontPx === null || m.minFontPx >= 12, noSidewaysScroll: !m.sidewaysScroll, oneH1: m.h1Count === 1 };
      failed ||= Object.values(checks).includes(false);
      results.push({ page: link.name, url: link.url, width, file, ...m, checks });
      console.log(`${file}: min ${m.minFontPx}px, sideways ${m.sidewaysScroll}, h1 ${m.h1Count}, gap lines ${m.gapFactLines}, Inter ${m.inter}`);
    }
    if (/^P[123]\b/i.test(link.name)) {
      const m = await open(cdp, link.url, NARROW, 844);
      results.push({ page: link.name, url: link.url, width: NARROW, file: null, sidewaysScroll: m.sidewaysScroll, scrollWidth: m.scrollWidth, clientWidth: m.clientWidth });
      console.log(`${link.name} @${NARROW}: sideways ${m.sidewaysScroll} (no picture)`);
    }
  }
  writeFileSync(join(outDir, "measure.json"), `${JSON.stringify({ webBase, widths: WIDTHS, narrow: NARROW, results }, null, 1)}\n`);
  ws.close();
} catch (error) {
  console.error(String(error?.stack ?? error));
  finish(2);
}
console.log(failed ? "AT LEAST ONE CHECK FAILED (see measure.json)" : "ALL CHECKS HOLD");
finish(failed ? 1 : 0);
