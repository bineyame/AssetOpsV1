/* PR-2a layout evidence (D-PRICE.3 action 1): the price page at 1440, 760 and 390 px for a mini Site, a cold Site with
   ?key=repair_visit_cost and an EV Site, beside frontend/mockups/v71/price-it.html (Parts B and C).
   No database: a tiny fixture API on <api-port> answers /api/sites/{id} and /api/sites/{id}/prices, and `npm run dev`
   proxies to it (ASSETOPS_API_PORT=<api-port>). Usage:
     ASSETOPS_API_PORT=8995 npx vite --port 5495   (in frontend/)
     node tools/pr2a-price-page-evidence.mjs <web-base> <api-port> <out-dir>
   Captures are PNGs from headless Chrome; the script also reports horizontal overflow of the page at each width.
   A measured claim needs a non-empty set: the script asserts the price table has rows before it reports overflow. */
import { widthGuard } from "./evidence-checks.mjs";
import { createServer } from "node:http";
import { spawn, spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const [, , WEB = "http://localhost:5495", API = "8995", OUT = "var/pr2a-evidence"] = process.argv;
const REPO = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
mkdirSync(OUT, { recursive: true });

const used = (text, detail) => ({ text, detail });
const notSet = (key, label, stored, usedBy) => ({
  key, label, detail: `${label} for this site.`, stored, state: "NOT_SET", current: null, not_set_text: "Not set",
  note: stored ? null : "Saving this price comes once a figure uses it.", used_by: usedBy, history: [], history_title: null,
});
const setRow = (key, label, valueText, per, usedBy) => ({
  key, label, detail: `${label} for this site.`, stored: true, state: "SET", not_set_text: null, note: null, used_by: usedBy,
  current: {
    revision_id: `${key}-2`, value: "1.42", currency: "USD", unit: "currency/L", value_text: valueText, amount_text: "1.42",
    per_text: per, basis_text: "A contract rate", source_reference: "Supplier contract SC-88", applies_from_text: "1 Sep 2026",
    applies_until_text: null, set_by_label: "Entered by site admin", recorded_text: "recorded 2 Sep 2026, 09:14",
  },
  history_title: `History of the ${label.toLowerCase()} · 2 versions`,
  history: [
    { revision_id: `${key}-2`, revision_no: 2, change_kind: "CORRECTION", headline: "Correction from 1 Sep 2026", until_text: null,
      value_text: valueText, basis_text: "a contract rate", source_reference: "SC-88", reason: "supplier contract rate replaces the estimate",
      set_by_label: "Entered by site admin", recorded_text: "recorded 2 Sep 2026, 09:14", replaced: false, replaced_text: null },
    { revision_id: `${key}-1`, revision_no: 1, change_kind: "INITIAL", headline: "First price from 1 Aug 2026", until_text: "until 1 Sep 2026",
      value_text: "1.38 USD per litre", basis_text: "an estimate", source_reference: null, reason: null,
      set_by_label: "AssetOps administrator", recorded_text: "recorded 1 Aug 2026, 07:30", replaced: true, replaced_text: "replaced by a later correction" },
  ],
});
const SITES = {
  "KOBO-001": { type: "MINIGRID", name: "Kobo", rows: [
    setRow("diesel_price_per_litre", "Diesel price", "1.42 USD per litre", "USD per litre", used("Fuel cost", "Backup running days")),
    notSet("productive_use_price_per_kwh", "Productive-use price", true, used("Lost sales", "Late power")),
    notSet("repair_visit_cost", "Cost per visit", false, used("Repair cost", "Visits without a result")),
    notSet("planned_service_cost", "Planned service cost", false, used("Service cost", "Planned visits")) ] },
  "GH-001": { type: "COLDCHAIN", name: "GreenHarvest", rows: [
    notSet("repair_visit_cost", "Cost per visit", false, used("Repair cost", "Visits without a result")),
    notSet("planned_service_cost", "Planned service cost", false, used("Service cost", "Planned visits")),
    notSet("stock_value_at_risk", "Stock value at risk", false, used("Stock at risk", "Warm hours")) ] },
  "EV-001": { type: "EV_CHARGING", name: "Harbour EV", rows: [
    setRow("ev_gross_tariff_per_kwh", "Gross tariff", "1.42 USD per kWh", "USD per kWh", used("Revenue", "Charging sessions")),
    notSet("charger_repair_cost", "Charger repair cost", false, used("Repair cost", "Charger faults")),
    notSet("interrupted_session_cost", "Interrupted session cost", false, used("Lost sessions", "Interrupted sessions")),
    notSet("repair_visit_cost", "Cost per visit", false, used("Repair cost", "Visits without a result")),
    notSet("planned_service_cost", "Planned service cost", false, used("Service cost", "Planned visits")) ] },
};
const detailOf = (id, s) => ({
  site_id: id, display_name: s.name, site_type: s.type, timezone: "UTC", lifecycle_status: "ACTIVE", origin: "IMPORTED",
  location: { country: "Kenya", locality: "Kisumu" }, source: { mode: "IMPORTED" }, template: null,
  foundation: { version: 1, valid_from: "2026-01-01", summary: "x", components: [], topology: null, devices: null,
    signal_mappings: null, control_assumptions: null, site_controls: null },
});
const pageOf = (id, s, need) => ({
  site_code: id, site_name: s.name, title: `${s.name} · Prices`, access_basis: "development_access",
  intro: "Every price this site's figures use: the current value, where it came from, and every earlier version.",
  sign_in_text: "Prices are set by your AssetOps administrator until sign-in is available.",
  table_title: `All prices for ${s.name}`, table_note: "One row per price. \"Not set\" means the figures that need it read \"not priced\".",
  count_text: `${s.rows.length} prices · ${s.rows.filter((r) => r.state === "SET").length} set`,
  cutoff: { known_at: null, text: null }, prices: s.rows,
  need: need ? { need_key: need, title: "What is needed to price this", text: "This needs a model, data or an integration before a price can fix it.",
    meanwhile: "Until then the figure stays unpriced.", link_label: "Review what is needed" } : null,
});

const server = createServer((req, res) => {
  const url = new URL(req.url, "http://x");
  const m = url.pathname.match(/^\/api\/sites\/([^/]+)(\/prices)?$/);
  const s = m && SITES[m[1]];
  res.setHeader("content-type", "application/json");
  if (!s) { res.statusCode = 404; res.end("{}"); return; }
  res.end(JSON.stringify(m[2] ? pageOf(m[1], s, url.searchParams.get("need")) : detailOf(m[1], s)));
});
await new Promise((r) => server.listen(Number(API), "127.0.0.1", r));

const CDP = Number(process.env.ASSETOPS_CDP_PORT ?? 9495);
const profile = mkdtempSync(join(tmpdir(), "assetops-pr2a-"));
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${CDP}`,
  `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
console.log(`chrome pid ${chrome.pid}`);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let ws;
for (let i = 0; i < 80 && !ws; i += 1) {
  try {
    const t = (await (await fetch(`http://127.0.0.1:${CDP}/json/list`)).json()).find((x) => x.type === "page");
    if (t?.webSocketDebuggerUrl) {
      ws = new WebSocket(t.webSocketDebuggerUrl);
      await new Promise((res, rej) => { ws.addEventListener("open", res); ws.addEventListener("error", rej); });
    }
  } catch { await sleep(250); }
}
if (!ws) throw new Error("Chrome did not expose a page target");
let seq = 0;
const pending = new Map();
ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); pending.get(m.id)?.(m); });
const send = (method, params = {}) => new Promise((resolveCall, reject) => {
  seq += 1;
  const id = seq;
  const timer = setTimeout(() => reject(new Error(`timeout ${method}`)), 60000);
  pending.set(id, (m) => { clearTimeout(timer); m.error ? reject(new Error(JSON.stringify(m.error))) : resolveCall(m.result); });
  ws.send(JSON.stringify({ id, method, params }));
});
const js = async (expression) => (await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true })).result.value;
async function waitFor(expression, ms = 30000) {
  const end = Date.now() + ms;
  while (Date.now() < end) { if (await js(`Boolean(${expression})`)) return true; await sleep(200); }
  return false;
}
const requireWidth = widthGuard({ send });
/** Open `url` at `w` px, wait for `ready`, save a full-height PNG and return the measurements. */
async function capture(url, file, w, ready) {
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: 900, deviceScaleFactor: 1, mobile: false });
  await requireWidth(w, 900, `resize to ${w}`, { record: false });
  await send("Page.navigate", { url });
  const ok = await waitFor(ready);
  await sleep(500);
  await requireWidth(w, 900, `loaded ${url}`, { record: false });
  const m = await js(`(() => ({ rows: document.querySelectorAll('[data-price-row]').length,
    scrollW: document.documentElement.scrollWidth, innerW: window.innerWidth, h: document.documentElement.scrollHeight,
    tableScroll: (() => { const t = document.querySelector('[data-site-prices] table'); return t ? t.getBoundingClientRect().width : null; })() }))()`);
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: Math.min(m.h, 6000), deviceScaleFactor: 1, mobile: false });
  await sleep(300);
  await requireWidth(w, null, `capture ${file}`, { record: false });
  const r = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(file, Buffer.from(r.data, "base64"));
  return { ok, ...m };
}

const PAGES = [
  ["mini", "/sites/KOBO-001/financials/prices?key=repair_visit_cost"],
  ["cold", "/sites/GH-001/financials/prices?key=repair_visit_cost"],
  ["ev", "/sites/EV-001/financials/prices"],
  ["need", "/sites/GH-001/financials/prices?need=bus_roster"],
];
let failed = false;
for (const [name, path] of PAGES) {
  for (const w of [1440, 760, 390]) {
    const m = await capture(`${WEB}${path}`, resolve(OUT, `${name}-${w}-app.png`), w, "document.querySelector('[data-price-row]') || document.querySelector('[data-prices-refused]')");
    const ok = m.ok && m.rows > 0 && m.scrollW <= m.innerW;
    if (!ok) failed = true;
    console.log(`${ok ? "PASS" : "FAIL"}  ${name} @${w}: rows=${m.rows} page scrollWidth=${m.scrollW} viewport=${m.innerW} table=${m.tableScroll} height=${m.h}`);
  }
}
const mock = pathToFileURL(join(REPO, "frontend/mockups/v71/price-it.html")).href;
for (const w of [1440, 760, 390]) await capture(`${mock}#page`, resolve(OUT, `mock-${w}.png`), w, "document.querySelector('h1')");
server.close();
spawnSync("taskkill", ["/PID", String(chrome.pid), "/T", "/F"]);
process.exit(failed ? 1 : 0);
