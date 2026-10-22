// W6-01b B2/B3 app capture: one global work page (Maintenance or Preventive) at 1440 and 390 for one persisted state.
// Adapted from the A2 capture: the measured table panel is named by PANEL (env), default `Corrective work requests`.
// Usage: node capture.mjs <out-dir> <state> <base-url> <app-path> [--append "<seed --append command>"]
//   With --append (cursor_changed): page one loads at 1440, the command appends a selected row, then Next reuses
//   the page-one cursor (409) and the refused page is captured at 1440 and, resized, at 390.
// Writes <state>-<width>.png and app-<state>.json (route, width, response status/known_at, element heights,
// document and table widths). Chrome is headless and closed at the end.
import { execSync, spawn } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const argv = process.argv.slice(2);
const appendAt = argv.indexOf("--append");
const APPEND = appendAt >= 0 ? argv[appendAt + 1] : null;
const [OUT, STATE, BASE, PATH] = appendAt >= 0 ? argv.slice(0, appendAt) : argv;
const PORT = Number(process.env.CDP_PORT ?? 9771);
const PANEL = process.env.PANEL ?? "Corrective work requests";
const SIZES = [[1440, 1000], [390, 900]];
mkdirSync(OUT, { recursive: true });
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe",
  ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`,
   `--user-data-dir=${mkdtempSync(join(tmpdir(), "w601b2cap-"))}`, "about:blank"], { stdio: "ignore" });
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

const MEASURE = `(async () => {
  await document.fonts.ready;
  const R = (e) => { if (!e) return null; const b = e.getBoundingClientRect(); return { h: Math.round(b.height), w: Math.round(b.width) }; };
  const root = document.querySelector(".global-work");
  const q = (s) => root.querySelector(s);
  const panels = Array.from(root.querySelectorAll("section.panel"));
  const byTitle = (t) => panels.find((p) => p.querySelector("h2")?.textContent === t) ?? null;
  const cases = byTitle(${JSON.stringify(PANEL)});
  const wrap = cases?.querySelector(".data-table__scroll") ?? null;
  const rows = Array.from(cases?.querySelectorAll("tbody tr") ?? []);
  const details = Array.from(root.querySelectorAll("details"));
  const tx = (e) => e ? e.textContent.replace(/\\s+/g, " ").trim() : null;
  return {
    heights: {
      page_header: R(q("header.page-header")), control_bar: R(q("[data-global-work-controls]")), status_line: R(q("[data-global-work-status]")),
      date_bar_slot: R(q("[data-global-work-bar]")), cards: R(q("[data-global-work-cards]")), loading: R(q("[data-global-work-loading]")),
      state_block: R(q("[data-global-work-refusal], [data-global-work-empty-scope]")), zero_block: R(q("[data-global-work-zero]")),
      table_panel: R(cases), tabs: R(q("[data-global-work-tabs]")), breadcrumb: R(document.querySelector("nav.breadcrumbs")),
      notice: R(q("[data-global-work-notice]")), status_strip: R(q(".status-strip")), table: R(cases?.querySelector("table")), thead: R(cases?.querySelector("thead")),
      pager: R(q("[data-global-work-pager]")), scroll_hint: R(q("[data-global-work-scroll-hint]")),
      card_max: (() => { const c = Array.from(root.querySelectorAll("[data-global-work-card]")); return c.length ? { h: Math.max(...c.map((e) => Math.round(e.getBoundingClientRect().height))), w: 0 } : null; })(),
    },
    scroll_hint_visible: (() => { const e = q("[data-global-work-scroll-hint]"); return e ? getComputedStyle(e).display !== "none" : null; })(),
    row_heights: rows.map((r) => Math.round(r.getBoundingClientRect().height)),
    collapsed_details_max_h: details.length ? Math.max(...details.map((d) => Math.round(d.getBoundingClientRect().height))) : null,
    open_details: details.filter((d) => d.open).length,
    table_scroll: wrap ? { client: wrap.clientWidth, scroll: wrap.scrollWidth, overflowX: getComputedStyle(wrap).overflowX } : null,
    document_width: { scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth },
    page_height: document.documentElement.scrollHeight,
    text: {
      status: tx(q("[data-global-work-status]")), cards: Array.from(root.querySelectorAll("[data-global-work-card]")).map(tx),
      state: tx(q("[data-global-work-refusal], [data-global-work-empty-scope]")), zero: tx(q("[data-global-work-zero]")),
      showing: tx(q("[data-global-work-showing]")), first_row: rows[0] ? Array.from(rows[0].querySelectorAll("td")).map((td) => tx(td).slice(0, 80)) : null,
      codes: rows.map((r) => (tx(r.querySelector("[data-global-work-title]")) ?? "").split(" · ")[0]),
      lineage: rows.map((r) => tx(r.querySelector("[data-global-work-lineage]"))),
      lineage_links: rows.map((r) => Array.from(r.querySelectorAll("[data-global-work-lineage] a")).map((a) => [a.textContent, a.getAttribute("href")])),
      tabs: tx(q("[data-global-work-tabs]")), notice: tx(q("[data-global-work-notice]")),
    },
  };
})()`;

async function ready() {
  for (let i = 0; i < 160; i++) {
    await sleep(150);
    if (await evalv(`!!document.querySelector(".global-work") && !document.querySelector("[data-global-work-loading]")`)) return true;
  }
  return false;
}

async function shoot(width, height, label) {
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 500 });
  await sleep(500);
  const m = await evalv(MEASURE);
  const png = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width, height: Math.min(m.page_height, 6000), scale: 1 } });
  const image = `${STATE}-${width}${label ? `-${label}` : ""}.png`;
  writeFileSync(join(OUT, image), Buffer.from(png.data, "base64"));
  return { state: STATE, width, route: PATH, image, ...m };
}

const results = [];
if (APPEND === null) {
  for (const [w, h] of SIZES) {
    responses.length = 0;
    await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: w < 500 });
    await send("Page.navigate", { url: `${BASE}${PATH}` });
    const ok = await ready();
    results.push({ ...(await shoot(w, h, "")), ready: ok, api: [...responses] });
  }
} else {
  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  await send("Page.navigate", { url: `${BASE}${PATH}` });
  let ok = await ready();
  results.push({ ...(await shoot(1440, 1000, "page-one")), ready: ok, api: [...responses] });
  const appended = execSync(APPEND, { encoding: "utf8" });
  responses.length = 0;
  await evalv(`document.querySelector("[data-global-work-next]").click(), true`);
  ok = await ready();
  results.push({ ...(await shoot(1440, 1000, "")), ready: ok, api: [...responses], appended: JSON.parse(appended) });
  results.push({ ...(await shoot(390, 900, "")), ready: ok, api: [...responses], note: "same refused page, resized" });
}
writeFileSync(join(OUT, `app-${STATE}.json`), JSON.stringify({ state: STATE, captured_at: new Date().toISOString(), results }, null, 2));
for (const r of results) {
  const h = Object.entries(r.heights).filter(([, v]) => v).map(([k, v]) => `${k}=${v.h}`).join(" ");
  console.log(`${r.state} ${r.width} ${r.image} ready=${r.ready} api=${JSON.stringify(r.api.map((a) => a.status))} doc=${r.document_width.scroll}/${r.document_width.client} tbl=${JSON.stringify(r.table_scroll)} rows=${JSON.stringify(r.row_heights)} ${h}`);
}
ws.close();
chrome.kill();
