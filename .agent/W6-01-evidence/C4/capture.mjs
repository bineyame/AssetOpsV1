// W6-01d C4 app capture: the work request History at 1440 and 390 for one persisted state (adapted from C2).
// Usage: node capture.mjs <out-dir> <state> <base-url> <app-path>; ACTION=next|occurred|full optionally acts first.
// Writes <state>-<width>.png and app-<state>.json (route, width, API responses, element heights, rendered rows).
import { spawn } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [OUT, STATE, BASE, PATH] = process.argv.slice(2);
const PORT = Number(process.env.CDP_PORT ?? 9774);
const ACTION = process.env.ACTION ?? "";
const SIZES = [[1440, 1000], [390, 900]];
mkdirSync(OUT, { recursive: true });
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe",
  ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`,
   `--user-data-dir=${mkdtempSync(join(tmpdir(), "w601c4cap-"))}`, "about:blank"], { stdio: "ignore" });
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
const bodies = new Map();
ws.addEventListener("message", (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  if (m.method === "Network.responseReceived" && m.params.response.url.includes("/api/work/")) {
    responses.push({ requestId: m.params.requestId, url: m.params.response.url.replace(/^https?:\/\/[^/]+/, ""), status: m.params.response.status });
  }
});
const send = (method, params = {}) => new Promise((res, rej) => { const id = ++n; pending.set(id, (m) => m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result)); ws.send(JSON.stringify({ id, method, params })); });
const evalv = async (expression) => { const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true }); if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 600)); return r.result.value; };
await send("Page.enable"); await send("Runtime.enable"); await send("Network.enable");

const ACT = {
  next: `document.querySelector("[data-global-work-next]")?.click()`,
  occurred: `(() => { const d = document.querySelector("[data-history-row] [data-history-occurred]"); if (d) d.open = true; })()`,
  full: `(() => { const d = document.querySelector('[data-history-row="CORRECTION"] [data-history-full]'); if (d) d.open = true; })()`,
};

const MEASURE = `(async () => {
  await document.fonts.ready;
  const R = (e) => { if (!e) return null; const b = e.getBoundingClientRect(); return { h: Math.round(b.height), w: Math.round(b.width) }; };
  const root = document.querySelector(".work-request");
  const q = (s) => root.querySelector(s);
  const tx = (e) => e ? e.textContent.replace(/\\s+/g, " ").trim() : null;
  const panels = Array.from(root.querySelectorAll("section.panel, .panel"));
  const panel = panels.find((p) => p.querySelector("h2")?.textContent === "History") ?? null;
  const details = Array.from(root.querySelectorAll("details"));
  const closed = details.filter((d) => !d.open);
  const scroll = panel ? panel.querySelector(".data-table__scroll") : null;
  const table = panel ? panel.querySelector("table") : null;
  const cols = table ? Array.from(table.querySelectorAll("thead th")).map((th) => Math.round(th.getBoundingClientRect().width)) : [];
  const crumb = q("[data-work-request-breadcrumb]"), tabs = q("[data-work-request-tabs]");
  return {
    heights: {
      page_header: R(q("header.page-header")), tabs: R(tabs), date_bar_slot: R(q("[data-global-work-bar]")), mheader: R(q(".v69-mheader")),
      state_block: R(q("[data-page-refusal]")), history_panel: R(panel), pager: R(q("[data-global-work-pager]")),
      scroll_hint: R(q("[data-global-work-scroll-hint]")),
    },
    collapsed_details_max_h: closed.length ? Math.max(...closed.map((d) => Math.round(d.getBoundingClientRect().height))) : null,
    open_details: details.filter((d) => d.open).map((d) => ({ hook: Array.from(d.attributes).map((a) => a.name).find((a) => a.startsWith("data-")), h: Math.round(d.getBoundingClientRect().height) })),
    table_scroll: scroll ? { scroll: scroll.scrollWidth, client: scroll.clientWidth } : null,
    column_widths: cols,
    document_width: { scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth },
    page_height: document.documentElement.scrollHeight,
    text: {
      h1: tx(q("h1")), subtitle: tx(q("header.page-header p")), breadcrumb: tx(crumb),
      tabs: Array.from(tabs ? tabs.querySelectorAll("li") : []).map(tx),
      tab_links: Array.from(tabs ? tabs.querySelectorAll("a") : []).map((a) => [a.textContent, a.getAttribute("href")]),
      date_bar: tx(q("[data-global-work-bar]")), refusal: tx(q("[data-page-refusal]")),
      rows: Array.from(root.querySelectorAll("[data-history-row]")).map((tr) => ({ kind: tr.getAttribute("data-history-row"), id: tr.getAttribute("data-history-id"),
        time: tx(tr.querySelector("[data-history-time]")), event: (tx(tr.querySelector("[data-history-clamp]") ?? tr.querySelector("[data-history-event]")) || "").slice(0, 160),
        by: tx(tr.querySelector("[data-history-by]")), source_link: tr.querySelector("[data-history-source-link]")?.getAttribute("href") ?? null })),
      gaps: Array.from(root.querySelectorAll("[data-history-gap]")).map((tr) => Array.from(tr.querySelectorAll("td")).map(tx)),
      pager: tx(q("[data-global-work-pager]")), panel_titles: panels.map((p) => tx(p.querySelector("h2"))),
      open_text: details.filter((d) => d.open).map((d) => (tx(d) || "").slice(0, 200)),
    },
  };
})()`;

async function ready() {
  for (let i = 0; i < 160; i++) {
    await sleep(150);
    if (await evalv(`!!document.querySelector(".work-request") && !document.querySelector("[data-global-work-loading]")`)) return true;
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
  if (ACTION) { await evalv(ACT[ACTION]); await sleep(400); }
  const m = await evalv(MEASURE);
  const api = [];
  for (const r of responses) {
    let known_at = null;
    try { const b = await send("Network.getResponseBody", { requestId: r.requestId }); const j = JSON.parse(b.body); known_at = j?.selected?.known_at ?? null;
      api.push({ url: r.url, status: r.status, known_at, revision: j?.work_detail?.selected_revision?.revision_no ?? null, revision_id: j?.work_detail?.selected_revision?.id ?? null, state: j?.work_detail?.case?.state ?? null, code: j?.detail?.code ?? null });
    } catch { api.push({ url: r.url, status: r.status }); }
  }
  const png = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width: w, height: Math.min(m.page_height, 6000), scale: 1 } });
  const image = `${STATE}-${w}.png`;
  writeFileSync(join(OUT, image), Buffer.from(png.data, "base64"));
  results.push({ state: STATE, width: w, route: PATH, action: ACTION || null, image, ready: ok, api, ...m });
}
writeFileSync(join(OUT, `app-${STATE}.json`), JSON.stringify({ state: STATE, captured_at: new Date().toISOString(), results }, null, 2));
for (const r of results) {
  const hs = Object.entries(r.heights).filter(([, v]) => v).map(([k, v]) => `${k}=${v.h}`).join(" ");
  console.log(`${r.state} ${r.width} ready=${r.ready} api=${JSON.stringify(r.api.map((a) => a.status))} rows=${r.text.rows.length} gaps=${r.text.gaps.length} doc=${r.document_width.scroll}/${r.document_width.client} tbl=${JSON.stringify(r.table_scroll)} ${hs} det=${r.collapsed_details_max_h}`);
}
ws.close();
chrome.kill();
