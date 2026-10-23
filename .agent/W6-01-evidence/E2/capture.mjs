// W6-01e E2 app capture (adapted from the B3/C3 captures): one page at 1440 and 390 for one persisted state.
// Usage: node capture.mjs <out-dir> <state> <base-url> <app-path> [--next] [--expand] [--cursor-kind <KIND>]
//   --next         page one loads, then Next is clicked and page two is captured.
//   --expand       after the collapsed capture, every `Full record text` disclosure is opened and captured again.
//   --cursor-kind  page one loads at 1440, Next yields the page-two cursor URL, then the same URL with the given
//                  `kind` is opened (a changed filter on a valid cursor: 409) and captured at 1440 and 390.
// ROOT (env) is the page root selector (default `.global-work`); LINKS (env) selects anchors whose text/href are
// recorded. Writes <state>-<width>[-label].png and app-<state>.json (route, width, the /api responses observed,
// element heights, panel heights, document/table widths, key text). Chrome is headless and closed at the end.
import { spawn } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const argv = process.argv.slice(2);
const flag = (name) => argv.includes(name);
const opt = (name) => (argv.indexOf(name) >= 0 ? argv[argv.indexOf(name) + 1] : null);
const [OUT, STATE, BASE, PATH] = argv;
const CURSOR_KIND = opt("--cursor-kind");
const PORT = Number(process.env.CDP_PORT ?? 9781);
const ROOT = process.env.ROOT ?? ".global-work";
const LINKS = process.env.LINKS ?? "[data-global-work-feeds] a, [data-global-work-site] ";
const SIZES = [[1440, 1000], [390, 900]];
mkdirSync(OUT, { recursive: true });
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe",
  ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`,
   `--user-data-dir=${mkdtempSync(join(tmpdir(), "w601e2cap-"))}`, "about:blank"], { stdio: "ignore" });
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
  if (m.method === "Network.responseReceived" && m.params.response.url.includes("/api/")) {
    responses.push({ url: m.params.response.url.replace(/^https?:\/\/[^/]+/, ""), status: m.params.response.status });
  }
});
const send = (method, params = {}) => new Promise((res, rej) => { const id = ++n; pending.set(id, (m) => m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result)); ws.send(JSON.stringify({ id, method, params })); });
const evalv = async (expression) => { const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true }); if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 600)); return r.result.value; };
await send("Page.enable"); await send("Runtime.enable"); await send("Network.enable");

const MEASURE = `(async () => {
  await document.fonts.ready;
  const R = (e) => { if (!e) return null; const b = e.getBoundingClientRect(); return { h: Math.round(b.height), w: Math.round(b.width) }; };
  const root = document.querySelector(${JSON.stringify(ROOT)}) ?? document.querySelector("main");
  const q = (s) => root.querySelector(s);
  const tx = (e) => e ? e.textContent.replace(/\\s+/g, " ").trim() : null;
  const panels = Array.from(root.querySelectorAll("section.panel"));
  const table = root.querySelector(".data-table__scroll");
  const rows = Array.from(root.querySelectorAll("tbody tr[data-global-work-row]"));
  const details = Array.from(root.querySelectorAll("details"));
  return {
    location: location.pathname + location.search,
    heights: {
      breadcrumb: R(document.querySelector("nav.breadcrumbs")), page_header: R(document.querySelector("header.page-header")),
      date_bar_slot: R(q("[data-global-work-bar]")), status_line: R(q("[data-global-work-status]")), cards: R(q("[data-global-work-cards]")),
      chips: R(q("[data-global-work-chips]")), state_block: R(q("[data-page-refusal]")), zero_block: R(q("[data-global-work-zero]")),
      loading: R(q("[data-global-work-loading]")), scroll_hint: R(q("[data-global-work-scroll-hint]")), pager: R(q("[data-global-work-pager]")),
      table: R(table?.querySelector("table")), thead: R(table?.querySelector("thead")), notice: R(q(".notice")),
    },
    panels: panels.map((p) => ({ title: tx(p.querySelector("h2")), ...R(p) })),
    row_heights: rows.map((r) => Math.round(r.getBoundingClientRect().height)),
    collapsed_details_max_h: details.filter((d) => !d.open).length ? Math.max(...details.filter((d) => !d.open).map((d) => Math.round(d.getBoundingClientRect().height))) : null,
    open_details: details.filter((d) => d.open).length,
    table_scroll: table ? { client: table.clientWidth, scroll: table.scrollWidth, overflowX: getComputedStyle(table).overflowX, maxHeight: getComputedStyle(table).maxHeight } : null,
    document_width: { scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth },
    page_height: document.documentElement.scrollHeight,
    text: {
      h1: tx(document.querySelector("h1")), status: tx(q("[data-global-work-status]")),
      cards: Array.from(root.querySelectorAll("[data-global-work-card]")).map(tx),
      chips: Array.from(root.querySelectorAll("[data-global-work-chips] button")).map((b) => [tx(b), b.getAttribute("aria-pressed")]),
      state: tx(q("[data-page-refusal]")), zero: tx(q("[data-global-work-zero]")), showing: tx(q("[data-global-work-showing]")),
      rows: rows.map((r) => Array.from(r.querySelectorAll("td")).map((td) => tx(td).slice(0, 90))),
      heads: rows.map((r) => [r.getAttribute("data-global-work-row"), r.getAttribute("data-global-work-head")]),
      links: Array.from(root.querySelectorAll(${JSON.stringify(LINKS)})).filter((a) => a.tagName === "A").map((a) => [tx(a), a.getAttribute("href")]),
      notice: tx(q("[data-work-record-notice]")), examples: tx(document.querySelector("[data-estate-examples]")),
    },
  };
})()`;

async function ready() {
  for (let i = 0; i < 160; i++) {
    await sleep(150);
    if (await evalv(`!!document.querySelector("main") && !document.querySelector("[data-global-work-loading], [data-work-request-loading], .estate-loading")`)) { await sleep(300); return true; }
  }
  return false;
}

async function shoot(width, height, label) {
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 500 });
  await sleep(500);
  const m = await evalv(MEASURE);
  const png = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width, height: Math.min(m.page_height, 8000), scale: 1 } });
  const image = `${STATE}-${width}${label ? `-${label}` : ""}.png`;
  writeFileSync(join(OUT, image), Buffer.from(png.data, "base64"));
  return { state: STATE, width, route: m.location, image, ...m };
}

const results = [];
for (const [w, h] of SIZES) {
  responses.length = 0;
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: w < 500 });
  await send("Page.navigate", { url: `${BASE}${PATH}` });
  let ok = await ready();
  if (flag("--next") || CURSOR_KIND) {
    await evalv(`document.querySelector("[data-global-work-next]").click(), true`);
    ok = await ready();
  }
  if (CURSOR_KIND) {
    const page2 = await evalv("location.pathname + location.search");
    responses.length = 0;
    await send("Page.navigate", { url: `${BASE}${page2}&kind=${CURSOR_KIND}` });
    ok = await ready();
  }
  results.push({ ...(await shoot(w, h, "")), ready: ok, api: [...responses] });
  if (flag("--expand")) {
    await evalv(`document.querySelectorAll("[data-global-work-full-body]").forEach((d) => { d.open = true; }), true`);
    results.push({ ...(await shoot(w, h, "expanded")), ready: ok, api: [...responses], note: "every Full record text disclosure open" });
  }
}
writeFileSync(join(OUT, `app-${STATE}.json`), JSON.stringify({ state: STATE, captured_at: new Date().toISOString(), results }, null, 2));
for (const r of results) {
  const p = r.panels.map((x) => `${x.title}=${x.h}`).join(" | ");
  console.log(`${r.state} ${r.width} ${r.image} ready=${r.ready} api=${JSON.stringify(r.api.map((a) => a.status))} doc=${r.document_width.scroll}/${r.document_width.client} tbl=${JSON.stringify(r.table_scroll)} rows=${r.text.rows.length} showing=${r.text.showing} state=${r.text.state} zero=${r.text.zero} || ${p}`);
}
ws.close();
chrome.kill();
