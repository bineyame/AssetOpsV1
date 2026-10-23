// W6-01c C3 app capture: the work request Maintenance record at 1440 and 390 for one persisted state. Copied from
// the C2 capture with record-page measurements. Usage: node capture.mjs <out-dir> <state> <base-url> <app-path>
// Writes <state>-<width>.png and app-<state>.json (route, width, API responses, element heights, rendered text).
import { spawn } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [OUT, STATE, BASE, PATH] = process.argv.slice(2);
const PORT = Number(process.env.CDP_PORT ?? 9772);
const LIST = process.env.ROOT === "list";
const SIZES = [[1440, 1000], [390, 900]];
mkdirSync(OUT, { recursive: true });
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe",
  ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`,
   `--user-data-dir=${mkdtempSync(join(tmpdir(), "w601c3cap-"))}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let url = null;
for (let i = 0; i < 80 && !url; i++) {
  try { url = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page")?.webSocketDebuggerUrl; } catch {}
  if (!url) await sleep(250);
}
const ws = new WebSocket(url);
await new Promise((r) => ws.addEventListener("open", r));
let n = 0; const pending = new Map();
const responses = [];
ws.addEventListener("message", (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  if (m.method === "Network.responseReceived" && m.params.response.url.includes("/api/work/")) {
    responses.push({ url: m.params.response.url.replace(/^https?:\/\/[^/]+/, ""), status: m.params.response.status });
  }
});
const send = (method, params = {}) => new Promise((res, rej) => { const id = ++n; pending.set(id, (m) => m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result)); ws.send(JSON.stringify({ id, method, params })); });
const evalv = async (expression) => { const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true }); if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 600)); return r.result.value; };
await send("Page.enable"); await send("Runtime.enable"); await send("Network.enable");

const LIST_MEASURE = `(async () => {
  await document.fonts.ready;
  const rows = Array.from(document.querySelectorAll("[data-global-work-row]"));
  return { document_width: { scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth },
    page_height: document.documentElement.scrollHeight,
    text: { row_links: rows.map((r) => { const a = r.querySelector("[data-global-work-title] a"); return a ? [a.textContent, a.getAttribute("href")] : null; }) } };
})()`;

const PAGE_MEASURE = `(async () => {
  await document.fonts.ready;
  const R = (e) => { if (!e) return null; const b = e.getBoundingClientRect(); return { h: Math.round(b.height), w: Math.round(b.width) }; };
  const root = document.querySelector(".work-request");
  const q = (s) => root.querySelector(s);
  const tx = (e) => e ? e.textContent.replace(/\\s+/g, " ").trim() : null;
  const panels = Array.from(root.querySelectorAll("section.panel, .panel"));
  const byTitle = (t) => panels.find((p) => p.querySelector("h2")?.textContent === t) ?? null;
  const details = Array.from(root.querySelectorAll("details"));
  const header = q("header.page-header"), tabs = q("[data-work-request-tabs]"), mh = q(".v69-mheader"), crumb = q("[data-work-request-breadcrumb]");
  const bottom = mh ?? tabs;
  return {
    heights: {
      breadcrumb: R(crumb), page_header: R(header), tabs: R(tabs), date_bar_slot: R(q("[data-global-work-bar]")),
      mheader: R(mh), state_block: R(q("[data-page-refusal]")), record_panel: R(byTitle("Maintenance record · activity")),
      record_table_scroll: R(q(".data-table__scroll")), record_notice: R(q("[data-work-record-notice]")),
      request_header_with_tabs: header && bottom ? { h: Math.round(bottom.getBoundingClientRect().bottom - header.getBoundingClientRect().top), w: 0 } : null,
    },
    collapsed_details_max_h: details.length ? Math.max(...details.map((d) => Math.round(d.getBoundingClientRect().height))) : null,
    open_details: details.filter((d) => d.open).length,
    document_width: { scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth },
    page_height: document.documentElement.scrollHeight,
    text: {
      h1: tx(q("h1")), subtitle: tx(q("header.page-header p")), breadcrumb: tx(crumb),
      breadcrumb_links: Array.from(crumb ? crumb.querySelectorAll("a") : []).map((a) => [a.textContent, a.getAttribute("href")]),
      open_site: (() => { const e = q("[data-work-request-open-site]"); return e ? [e.tagName, e.getAttribute("href")] : null; })(),
      tabs: Array.from(tabs ? tabs.querySelectorAll("li") : []).map(tx),
      tab_links: Array.from(tabs ? tabs.querySelectorAll("a") : []).map((a) => [a.textContent, a.getAttribute("href")]),
      date_bar: tx(q("[data-global-work-bar]")), refusal: tx(q("[data-page-refusal]")),
      mheader: Array.from(root.querySelectorAll("[data-mheader-cell]")).map((c) => [c.getAttribute("data-mheader-cell"), tx(c.querySelector("[data-work-request-preview]") || c.querySelector("dd"))]),
      table_columns: Array.from(root.querySelectorAll(".data-table thead th")).map(tx),
      groups: Array.from(root.querySelectorAll("[data-work-record-group]")).map((g) => ({
        heading: tx(g.querySelector("[data-work-record-group-heading]")),
        rows: Array.from(g.querySelectorAll("[data-work-record-item]")).map((r) => Array.from(r.querySelectorAll("th, td")).map((c) => (tx(c) || "").slice(0, 140))),
      })),
      activity_clamp_h: R(q('[data-work-record-clamp="activity"]')),
      empty: tx(q("[data-work-record-empty]")), notice: tx(q("[data-work-record-notice]")),
      notice_links: Array.from(root.querySelectorAll("[data-work-record-notice] a")).map((a) => a.getAttribute("href")),
      oprecords_anchors: Array.from(document.querySelectorAll('a[href*="/operational-records"]')).length,
      table_width: (() => { const s = q(".data-table__scroll"); return s ? { scroll: s.scrollWidth, client: s.clientWidth } : null; })(),
      scroll_hint_visible: (() => { const e = q("[data-global-work-scroll-hint]"); return e ? getComputedStyle(e).display !== "none" : null; })(),
      panel_titles: panels.map((p) => tx(p.querySelector("h2"))),
    },
  };
})()`;

async function ready() {
  const sel = LIST ? ".global-work" : ".work-request";
  for (let i = 0; i < 160; i++) {
    await sleep(150);
    if (await evalv(`!!document.querySelector("${sel}") && !document.querySelector("[data-global-work-loading]")`)) return true;
  }
  return false;
}

const results = [];
for (const [w, h] of SIZES) {
  responses.length = 0;
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: w < 500 });
  await send("Page.navigate", { url: `${BASE}${PATH}` });
  const ok = await ready();
  await sleep(500);
  const m = await evalv(LIST ? LIST_MEASURE : PAGE_MEASURE);
  const png = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width: w, height: Math.min(m.page_height, 6000), scale: 1 } });
  const image = `${STATE}-${w}.png`;
  writeFileSync(join(OUT, image), Buffer.from(png.data, "base64"));
  results.push({ state: STATE, width: w, route: PATH, image, ready: ok, api: [...responses], ...m });
}
writeFileSync(join(OUT, `app-${STATE}.json`), JSON.stringify({ state: STATE, captured_at: new Date().toISOString(), results }, null, 2));
for (const r of results) {
  const hs = r.heights ? Object.entries(r.heights).filter(([, v]) => v).map(([k, v]) => `${k}=${v.h}`).join(" ") : "";
  console.log(`${r.state} ${r.width} ready=${r.ready} api=${JSON.stringify(r.api.map((a) => a.status))} doc=${r.document_width.scroll}/${r.document_width.client} ${hs}`);
}
ws.close();
chrome.kill();
