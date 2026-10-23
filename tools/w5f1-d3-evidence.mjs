#!/usr/bin/env node
// W5-F1 F1-3 (`.agent/W5-F1-build-spec.md`): capture producer for the three D3 corrections R22, R37 and R38.
// usage: node tools/w5f1-d3-evidence.mjs <out-dir> <revision> <web-base> <api-base>
//   <out-dir> must sit under .agent/W5-F1-evidence/. <web-base> serves the app and v69 (`/mockups/v69/index.html`)
//   from one origin; <api-base> is the real API on the private test DB. No browser fetch is mocked or rewritten.
// Env: W5F1_CDP_PORT (default 9861).
// For each state (stocked, empty/unknown, 422 refused) it first GETs the real cold Health, Temperature and Evidence
// Analysis reads and records status, selection state, `known_at` and the watermark from each response. It then
// captures the three app routes and their v69 hashes plus the Foundation -> Evidence source-panel click at 1440x1000
// and 390x900, and exits nonzero on a response, title/order, link, clipped-ID or overflow failure.
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, relative, resolve, sep } from "node:path";
import { widthGuard } from "./evidence-checks.mjs";

const [, , OUT_ARG, REV, WEB, API] = process.argv;
if (!OUT_ARG || !REV || !WEB || !API) {
  console.error("usage: node tools/w5f1-d3-evidence.mjs <out-dir> <revision> <web-base> <api-base>");
  process.exit(2);
}
const OUT = resolve(OUT_ARG);
const rel = relative(resolve(".agent", "W5-F1-evidence"), OUT);
if (rel.startsWith("..") || rel.includes(`..${sep}`) || resolve(rel) === rel) {
  console.error(`out-dir must be under .agent/W5-F1-evidence/: ${OUT}`);
  process.exit(2);
}
mkdirSync(OUT, { recursive: true });

const CODE = "COLD-LAB-001";
const STATES = {
  stocked: { query: "from=2026-10-06T19:00:00Z&to=2026-10-06T20:05:00Z", http: 200 },
  empty: { query: "from=2026-10-05T19:00:00Z&to=2026-10-05T20:05:00Z", http: 200, selection: "UNKNOWN" },
  refused: { query: "from=2026-10-06T20:05:00Z&to=2026-10-06T19:00:00Z", http: 422, code: "COLD_WINDOW_INVALID" },
};
const READS = {
  health: `/api/sites/${CODE}/cold/health`,
  temperature: `/api/sites/${CODE}/cold/temperature`,
  analysis: `/api/sites/${CODE}/cold/evidence/analysis`,
};
const SCREENS = {
  health: { mock: "cold-health", app: (q) => `/sites/${CODE}/health?${q}` },
  temperature: { mock: "temperature", app: (q) => `/sites/${CODE}/performance/temperature?${q}` },
  analysis: { mock: "cold-evidence-analysis", app: (q) => `/sites/${CODE}/evidence?${q}&view=analysis` },
};
const SIZES = [[1440, 1000], [390, 900]];
const HEALTH_TITLES = ["Condition and evidence"];
const CONTEXT_TAIL = ["Peak observed", "Power outage", "Door opening", "Loading / batch", "Defrost"];
const SOURCES_TITLE = "Data sources · data quality, not equipment condition";
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const failures = [];
const fail = (msg) => { failures.push(msg); console.log(`FAIL ${msg}`); };

/* ---------- 1. the served reads, before any navigation ---------- */
const responses = {};
for (const [state, spec] of Object.entries(STATES)) {
  for (const [name, path] of Object.entries(READS)) {
    const url = `${API}${path}?${spec.query}`;
    const res = await fetch(url);
    const body = await res.json().catch(() => null);
    const selection = body?.selection?.state ?? body?.currentness?.state ?? null;
    const r = {
      url, http: res.status, code: body?.error?.code ?? null, selection_state: selection,
      known_at: body?.window?.known_at ?? null,
      committed_watermark: body?.window?.committed_watermark ?? null,
      watermark_decided_at: body?.currentness?.watermark?.decided_at ?? null,
    };
    if (name === "analysis" && Array.isArray(body?.accepted_records?.items)) {
      const items = body.accepted_records.items;
      r.total_count = body.accepted_records.total_count ?? null;
      r.first_evidence_ids = items.slice(0, 3).map((i) => i.evidence_id);
      r.target_states = [...new Set(items.map((i) => i.record_target_state))];
      r.target_links = items.filter((i) => i.link !== null && i.link !== undefined).length;
    }
    responses[`${state}:${name}`] = r;
    const ok = r.http === spec.http && (spec.code ? r.code === spec.code : spec.selection ? selection === spec.selection : selection !== null && selection !== "UNKNOWN");
    if (!ok) fail(`response ${state}:${name} http=${r.http} code=${r.code} selection=${selection}`);
    console.log(`read ${state}:${name} http=${r.http} ${r.code ?? r.selection_state} known_at=${r.known_at} watermark=${r.committed_watermark ?? r.watermark_decided_at}` +
      (r.first_evidence_ids ? ` first_ids=${r.first_evidence_ids.join(",")} targets=${r.target_states.join("/")} links=${r.target_links}` : ""));
  }
}
if ((responses["stocked:analysis"].first_evidence_ids ?? []).length === 0) fail("stocked analysis has no accepted records (empty set)");
if (responses["stocked:analysis"].target_links !== 0) fail("stocked analysis offers record target links");

/* ---------- 2. own headless Chrome over CDP ---------- */
const PORT = Number(process.env.W5F1_CDP_PORT ?? 9861);
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe",
  ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`,
   `--user-data-dir=${mkdtempSync(join(tmpdir(), "w5f1cap-"))}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let wsUrl = null;
for (let i = 0; i < 80 && !wsUrl; i++) {
  try { wsUrl = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page")?.webSocketDebuggerUrl; } catch {}
  if (!wsUrl) await sleep(250);
}
if (!wsUrl) { console.error("Chrome did not expose a page target"); chrome.kill(); process.exit(1); }
const ws = new WebSocket(wsUrl);
await new Promise((r) => ws.addEventListener("open", r));
let n = 0; const pending = new Map();
ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
const send = (method, params = {}) => new Promise((res, rej) => { const id = ++n; pending.set(id, (m) => m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result)); ws.send(JSON.stringify({ id, method, params })); });
const evalv = async (expression) => (await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true })).result.value;
await send("Page.enable"); await send("Runtime.enable");
// W1-UX-06 shared width check: each resize/navigation must lay out at the requested width before it is measured.
const widthClaims = [];
const requireWidth = widthGuard({ send, claim: (name, ok, detail) => { widthClaims.push({ name, ok, ...detail }); if (!ok) fail(name); } });

// Route-specific settle markers; never `/Loading /` text, which matches the required Loading / batch row.
const READY = {
  health: `!!m.querySelector("[data-health-card], [data-page-refusal], [data-cold-depth-error]")`,
  temperature: `!!m.querySelector('[data-page-refusal], [data-key-value="loading"]')`,
  analysis: `!!m.querySelector("[data-page-refusal], [data-accepted-record], #cold-site-records-heading ~ * [data-panel-gap], section.panel [data-panel-gap]")`,
  evidence: `!!document.getElementById("cold-site-sources-heading") && !/Loading the site/.test(m.innerText)`,
  foundation: `[...m.querySelectorAll("a")].some((a) => a.textContent === "Evidence › Data sources →")`,
};
const MOCK_READY = `document.querySelectorAll("section.panel").length > 0`;

const MEASURE = `(async () => {
  await document.fonts.ready;
  const root = document.querySelector("main") ?? document.body;
  const title = (p) => ((p.querySelector(".panel__heading, h2, h3")?.textContent) ?? "").trim();
  const panels = Array.from(root.querySelectorAll("section.panel")).map(title).filter(Boolean);
  const context = Array.from(root.querySelectorAll("[data-key-value] dt")).filter((dt) => dt.closest("section.panel") && title(dt.closest("section.panel")) === "Excursion context").map((dt) => dt.textContent);
  const loadingRow = root.querySelector('[data-key-value="loading"] dd')?.textContent ?? null;
  const recordCells = Array.from(root.querySelectorAll("tr[data-accepted-record]")).map((tr) => {
    const td = tr.querySelectorAll("td")[4];
    const code = td?.querySelector("code[data-record-id]");
    const scroller = tr.closest(".data-table__scroll") ?? tr.closest("table");
    const c = code?.getBoundingClientRect(); const s = scroller?.getBoundingClientRect();
    return {
      id: tr.getAttribute("data-accepted-record"), text: td?.innerText ?? null, code: code?.textContent ?? null,
      links: td ? td.querySelectorAll("a").length : -1,
      clipped: !code || code.scrollWidth > code.clientWidth + 1 || (c && s && (c.left < s.left - 0.5 || c.right > s.right + 0.5 && scroller.scrollWidth <= scroller.clientWidth)),
      hidden: tr.hidden,
    };
  });
  return { url: location.pathname + location.search + location.hash, panels, context, loadingRow, recordCells,
    // A 422 is shown as a page refusal (cold Health) or as the refusal sentence inside every kept slot (W2 cold views).
    refusal: !!root.querySelector("[data-page-refusal], [data-cold-depth-error]") ||
      Array.from(root.querySelectorAll("[data-panel-gap]")).some((g) => /not a valid UTC window/.test(g.textContent ?? "")),
    sourcesTarget: !!document.getElementById("cold-site-sources-heading"),
    sourcesTitle: document.getElementById("cold-site-sources-heading")?.textContent ?? null,
    healthSources: !!document.getElementById("site-health-sources-heading"),
    scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth,
    pageHeight: document.documentElement.scrollHeight };
})()`;

async function settle(expr) {
  for (let i = 0; i < 200; i++) {
    await sleep(150);
    if (await evalv(`(() => { const m = document.querySelector("main") ?? document.body; return ${expr}; })()`)) return true;
  }
  return false;
}
async function shot(file, w, height) {
  const s = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width: w, height: Math.min(height, 9000), scale: 1 } });
  writeFileSync(join(OUT, file), Buffer.from(s.data, "base64"));
}
async function capture(url, ready, file, w, h) {
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: false });
  await send("Page.navigate", { url });
  const settled = await settle(ready);
  await requireWidth(w, h, url);
  await sleep(400);
  const m = await evalv(MEASURE);
  await shot(file, w, m.pageHeight);
  return { settled, ...m, image: file };
}

/* ---------- 3. captures ---------- */
const captures = [];
const mockTitles = {};
for (const [w, h] of SIZES) {
  for (const [screen, def] of Object.entries(SCREENS)) {
    const mock = await capture(`${WEB}/mockups/v69/index.html#/${def.mock}`, MOCK_READY, `${def.mock}-${w}-mock.png`, w, h);
    mockTitles[`${def.mock}@${w}`] = mock.panels;
    captures.push({ kind: "mock", screen, viewport: `${w}x${h}`, hash: `#/${def.mock}`, ...mock });
    for (const [state, spec] of Object.entries(STATES)) {
      const app = await capture(`${WEB}${def.app(spec.query)}`, READY[screen], `${screen}-${state}-${w}-app.png`, w, h);
      const c = { kind: "app", screen, state, viewport: `${w}x${h}`, mock_hash: `#/${def.mock}`, mock_titles: mock.panels, ...app };
      const tag = `${screen}/${state}@${w}`;
      if (!app.settled) fail(`${tag} did not settle`);
      if (app.scrollWidth > app.clientWidth) fail(`${tag} document overflow ${app.scrollWidth}>${app.clientWidth}`);
      if (state === "refused") {
        if (!app.refusal) fail(`${tag} shows no refusal`);
      } else {
        c.titles_equal = JSON.stringify(app.panels) === JSON.stringify(mock.panels);
        if (!c.titles_equal) fail(`${tag} titles ${JSON.stringify(app.panels)} != mock ${JSON.stringify(mock.panels)}`);
      }
      if (screen === "health") {
        if (app.healthSources) fail(`${tag} mounts the S7 Data sources panel`);
        if (state !== "refused" && JSON.stringify(app.panels) !== JSON.stringify(HEALTH_TITLES)) fail(`${tag} titles ${JSON.stringify(app.panels)}`);
      }
      if (screen === "temperature" && state !== "refused") {
        const ok = app.context.length === 7 && app.context[0] === "Excursion window" && /^(Upper|Lower) policy limit$/.test(app.context[1] ?? "") &&
          JSON.stringify(app.context.slice(2)) === JSON.stringify(CONTEXT_TAIL) && app.loadingRow === "Not established";
        if (!ok) fail(`${tag} context rows ${JSON.stringify(app.context)} loading=${app.loadingRow}`);
      }
      if (screen === "temperature" && state === "refused" && app.context.length !== 0) fail(`${tag} fabricates context rows`);
      if (screen === "analysis") {
        for (const r of app.recordCells) {
          if (r.links !== 0) fail(`${tag} record ${r.id} has ${r.links} link(s)`);
          if (r.code !== `REC ${r.id}` || !UUID.test(r.id ?? "")) fail(`${tag} record ${r.id} code ${r.code}`);
          if (!r.hidden && r.clipped) fail(`${tag} record ${r.id} clipped`);
          if (!/Record page unavailable/.test(r.text ?? "")) fail(`${tag} record ${r.id} lacks the unavailable destination`);
        }
        if (state === "stocked" && app.recordCells.filter((r) => !r.hidden).length === 0) fail(`${tag} shows no record cells (empty set)`);
      }
      captures.push(c);
      console.log(`${tag} settled=${app.settled} titles=${JSON.stringify(app.panels)} ` +
        `${screen === "temperature" ? `context=${JSON.stringify(app.context)} ` : ""}` +
        `${screen === "analysis" ? `records=${app.recordCells.length} links=${app.recordCells.reduce((a, r) => a + r.links, 0)} first=${app.recordCells.slice(0, 3).map((r) => r.code).join(" | ")} ` : ""}` +
        `width=${app.scrollWidth}/${app.clientWidth} height=${app.pageHeight}`);
    }
  }
  // Foundation -> Evidence: the Gateway status action resolves to the existing cold-evidence Data sources panel.
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: false });
  await send("Page.navigate", { url: `${WEB}/sites/${CODE}/foundation/readiness` });
  const tag = `foundation-click@${w}`;
  const foundationReady = await settle(READY.foundation);
  await requireWidth(w, h, tag);
  const href = await evalv(`[...document.querySelectorAll("a")].find((a) => a.textContent === "Evidence › Data sources →")?.getAttribute("href") ?? null`);
  const before = await evalv(MEASURE);
  await shot(`foundation-readiness-${w}-app.png`, w, before.pageHeight);
  await evalv(`[...document.querySelectorAll("a")].find((a) => a.textContent === "Evidence › Data sources →")?.click()`);
  const evidenceReady = await settle(READY.evidence);
  await requireWidth(w, h, `${tag} after click`);
  await sleep(400);
  const after = await evalv(MEASURE);
  await shot(`foundation-to-evidence-${w}-app.png`, w, after.pageHeight);
  const click = { kind: "click", viewport: `${w}x${h}`, foundation_ready: foundationReady, href, landed: after.url, evidence_ready: evidenceReady,
    sources_target: after.sourcesTarget, sources_title: after.sourcesTitle, before_image: `foundation-readiness-${w}-app.png`,
    after_image: `foundation-to-evidence-${w}-app.png`, scrollWidth: after.scrollWidth, clientWidth: after.clientWidth, pageHeight: after.pageHeight };
  if (href !== `/sites/${CODE}/evidence#cold-site-sources-heading`) fail(`${tag} href ${href}`);
  if (!after.url.startsWith(`/sites/${CODE}/evidence`) || !after.url.endsWith("#cold-site-sources-heading")) fail(`${tag} landed ${after.url}`);
  if (!after.sourcesTarget || after.sourcesTitle !== SOURCES_TITLE) fail(`${tag} target panel missing (${after.sourcesTitle})`);
  if (after.scrollWidth > after.clientWidth) fail(`${tag} document overflow`);
  captures.push(click);
  console.log(`${tag} href=${href} landed=${after.url} target=${after.sourcesTitle}`);
}

writeFileSync(join(OUT, "evidence.json"), JSON.stringify({
  producer: "tools/w5f1-d3-evidence.mjs", revision: REV, web: WEB, api: API, site: CODE,
  windows: Object.fromEntries(Object.entries(STATES).map(([k, v]) => [k, v.query])),
  responses, mock_titles: mockTitles, width_claims: widthClaims, captures: captures.map((c) => ({ ...c })), failures, result: failures.length === 0 ? "PASS" : "FAIL",
}, null, 2));
console.log(`result ${failures.length === 0 ? "PASS" : `FAIL (${failures.length})`}`);
ws.close(); chrome.kill();
process.exit(failures.length === 0 ? 0 : 1);
