/* PR-3 layout evidence (rev 5 §5.3): the inline price form at 1440 and 390 px — open (filled), confirm with the
   Reason field, and the success note after Save — on the Kobo price page.
   No database: a fixture API on <api-port> answers /api/sites/{id}, /api/sites/{id}/prices (with the `entry` block)
   and POST /api/sites/{id}/financial-assumptions/entries (dry run: CORRECTION, reason required; save: 201).
   `npm run dev` proxies to it. Usage (never the demo ports 5490/8990):
     ASSETOPS_API_PORT=8996 npx vite --port 5496   (in frontend/)
     node tools/pr3-price-entry-evidence.mjs <web-base> <api-port> <out-dir>
   A measured claim needs a non-empty set: each capture asserts the form (or the note) is on screen with a width > 0
   before it reports page overflow. */
import { widthGuard } from "./evidence-checks.mjs";
import { createServer } from "node:http";
import { spawn, spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const [, , WEB = "http://localhost:5496", API = "8996", OUT = "var/pr3-evidence"] = process.argv;
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
mkdirSync(OUT, { recursive: true });

const used = (text, detail) => ({ text, detail });
const notSet = (key, label, stored, usedBy) => ({
  key, noun: label.toLowerCase(), label, detail: `${label} for this site.`, stored, state: "NOT_SET", current: null,
  not_set_text: "Not set", note: stored ? null : "Saving this price comes once a figure uses it.", used_by: usedBy,
  history: [], history_title: null,
});
const hist = (no, kind, headline, value, by, replaced) => ({
  revision_id: `d-${no}`, revision_no: no, change_kind: kind, headline, until_text: null, value_text: `${value} USD per litre`,
  basis_text: kind === "CORRECTION" ? "a contract rate" : "an estimate", source_reference: null,
  reason: kind === "CORRECTION" ? "Supplier invoice was higher" : null, set_by_label: by,
  recorded_text: "recorded 1 Jan 2026, 10:00", replaced, replaced_text: replaced ? "replaced by a later correction" : null,
});
let saved = false;
const diesel = () => ({
  key: "diesel_price_per_litre", noun: "diesel price", label: "Diesel price", detail: "Backup generator fuel.", stored: true,
  state: "SET", not_set_text: null, note: null, used_by: used("Fuel cost", "Backup running days"),
  current: {
    revision_id: saved ? "d-2" : "d-1", value: saved ? "2.00" : "1.25", currency: "USD", unit: "currency/L",
    value_text: `${saved ? "2.00" : "1.25"} USD per litre`, amount_text: saved ? "2.00" : "1.25", per_text: "USD per litre",
    basis_text: saved ? "A contract rate" : "An estimate", source_reference: saved ? "Supplier invoice INV-2209" : null,
    applies_from_text: saved ? "1 Oct 2026" : "1 Jan 2026", applies_until_text: null,
    set_by_label: saved ? "Entered by site admin" : "AssetOps administrator", recorded_text: "recorded 12 Nov 2026, 10:00",
  },
  history_title: `History of the diesel price · ${saved ? 2 : 1} version${saved ? "s" : ""}`,
  history: saved
    ? [hist(2, "CORRECTION", "Correction from 1 Oct 2026", "2.00", "Entered by site admin", false),
      hist(1, "INITIAL", "First price from 1 Jan 2026", "1.25", "AssetOps administrator", false)]
    : [hist(1, "INITIAL", "First price from 1 Jan 2026", "1.25", "AssetOps administrator", false)],
});
const rows = () => [diesel(),
  notSet("productive_use_price_per_kwh", "Productive-use price", true, used("Lost sales", "Late power")),
  notSet("repair_visit_cost", "Cost per visit", false, used("Repair cost", "Visits without a result")),
  notSet("planned_service_cost", "Planned service cost", false, used("Service cost", "Planned visits"))];
const detail = {
  site_id: "KOBO-001", display_name: "Kobo", site_type: "MINIGRID", timezone: "Africa/Nairobi", lifecycle_status: "ACTIVE",
  origin: "IMPORTED", location: { country: "Kenya", locality: "Kisumu" }, source: { mode: "IMPORTED" }, template: null,
  foundation: { version: 1, valid_from: "2026-01-01", summary: "x", components: [], topology: null, devices: null,
    signal_mappings: null, control_assumptions: null, site_controls: null },
};
const page = () => ({
  site_code: "KOBO-001", site_name: "Kobo", title: "Kobo · Prices", access_basis: "development_access",
  intro: "Every price this site's figures use: the current value, where it came from, and every earlier version.",
  sign_in_text: "Prices saved here are recorded as entered by site admin until sign-in is available.",
  table_title: "All prices for Kobo", table_note: "One row per price. \"Not set\" means the figures that need it read \"not priced\".",
  count_text: "4 prices · 1 set", cutoff: { known_at: null, text: null }, prices: rows(), need: null,
  entry: { enabled: true, keys: ["diesel_price_per_litre", "productive_use_price_per_kwh"], today: "2026-11-13",
    unit_text: { diesel_price_per_litre: "per litre", productive_use_price_per_kwh: "per kWh" },
    currencies: ["EUR", "KES", "USD"], live_view: null },
});
const DRY = { dry_run: true, change_kind: "CORRECTION", applies_from: "2026-10-01", reason_required: true,
  summary: "Correction from 1 Oct 2026. Figures from 1 Oct 2026 are recalculated with this price; the earlier version is kept in the history." };
const SAVED = { revision_id: "d-2", revision_no: 2, change_kind: "CORRECTION", applies_from: "2026-10-01",
  recorded_at: "2026-11-12T10:00:00Z", replayed: false, set_by: "Entered by site admin",
  summary: "Saved. Diesel price 2.00 USD per litre from 1 Oct 2026. Figures that use it read \"Updating…\" for a few minutes, then show the new price." };

const server = createServer((req, res) => {
  const url = new URL(req.url, "http://x");
  res.setHeader("content-type", "application/json");
  if (req.method === "POST" && url.pathname === "/api/sites/KOBO-001/financial-assumptions/entries") {
    let text = "";
    req.on("data", (c) => { text += c; });
    req.on("end", () => {
      const body = JSON.parse(text);
      if (body.dry_run) { res.end(JSON.stringify(DRY)); return; }
      saved = true;
      res.statusCode = 201;
      res.end(JSON.stringify(SAVED));
    });
    return;
  }
  if (url.pathname === "/api/sites/KOBO-001") { res.end(JSON.stringify(detail)); return; }
  if (url.pathname === "/api/sites/KOBO-001/prices") { res.end(JSON.stringify(page())); return; }
  res.statusCode = 404;
  res.end("{}");
});
await new Promise((r) => server.listen(Number(API), "127.0.0.1", r));

const CDP = Number(process.env.ASSETOPS_CDP_PORT ?? 9496);
const profile = mkdtempSync(join(tmpdir(), "assetops-pr3-"));
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

/** Fill the open form the way a person types (React reads the native value setter + input event). */
const FILL = `(() => {
  const f = document.querySelector('[data-price-entry-form]');
  const set = (el, v) => { Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), 'value').set.call(el, v);
    el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); };
  set(f.querySelector('input[name=value]'), '2.00');
  f.querySelector('input[type=radio][value=CONTRACT_RATE]').click();
  set(f.querySelector('input[name=source]'), 'Supplier invoice INV-2209');
  set(f.querySelector('input[name=applies_from]'), '2026-10-01');
  return true; })()`;
const REASON = `(() => { const el = document.querySelector('textarea[name=reason]');
  Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), 'value').set.call(el, 'Supplier invoice was higher');
  el.dispatchEvent(new Event('input', { bubbles: true })); return true; })()`;

async function shot(file, w, target) {
  const m = await js(`(() => { const t = document.querySelector('${target}'); const r = t ? t.getBoundingClientRect() : null;
    return { present: Boolean(t), targetW: r ? Math.round(r.width) : 0, targetRight: r ? Math.round(r.right) : 0,
      scrollW: document.documentElement.scrollWidth, innerW: window.innerWidth, h: document.documentElement.scrollHeight }; })()`);
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: Math.min(m.h, 6000), deviceScaleFactor: 1, mobile: false });
  await sleep(300);
  await requireWidth(w, null, `capture ${file}`, { record: false });
  const r = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(file, Buffer.from(r.data, "base64"));
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: 900, deviceScaleFactor: 1, mobile: false });
  return m;
}

let failed = false;
const report = (name, w, m) => {
  const ok = m.present && m.targetW > 0 && m.scrollW <= m.innerW && m.targetRight <= m.innerW;
  if (!ok) failed = true;
  console.log(`${ok ? "PASS" : "FAIL"}  ${name} @${w}: present=${m.present} width=${m.targetW} right=${m.targetRight} page scrollWidth=${m.scrollW} viewport=${m.innerW}`);
};
for (const w of [1440, 390]) {
  saved = false;
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: 900, deviceScaleFactor: 1, mobile: false });
  await requireWidth(w, 900, `resize to ${w}`, { record: false });
  await send("Page.navigate", { url: `${WEB}/sites/KOBO-001/financials/prices?key=diesel_price_per_litre&return=%2Fsites%2FKOBO-001` });
  if (!(await waitFor("document.querySelector('[data-price-entry-form]')"))) { failed = true; console.log(`FAIL form @${w}: not open`); continue; }
  await js(FILL);
  await sleep(300);
  report("open", w, await shot(resolve(OUT, `open-${w}.png`), w, "[data-price-entry-form]"));
  await js("document.querySelector('[data-price-entry-continue]').click()");
  await waitFor("document.querySelector('textarea[name=reason]')");
  await js(REASON);
  await sleep(300);
  report("confirm", w, await shot(resolve(OUT, `confirm-${w}.png`), w, "[data-price-entry-confirm]"));
  await js("document.querySelector('[data-price-entry-save]').click()");
  await waitFor("document.querySelector('[data-price-entry-saved]')");
  await sleep(500);
  report("saved", w, await shot(resolve(OUT, `saved-${w}.png`), w, "[data-price-entry-saved]"));
}
server.close();
spawnSync("taskkill", ["/PID", String(chrome.pid), "/T", "/F"]);
process.exit(failed ? 1 : 0);
