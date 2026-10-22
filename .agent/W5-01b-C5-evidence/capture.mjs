// W5-01b C5: app vs v69 `cold-scenarios` mock at 1440x1000 and 390x900 for the cold Scenarios page and the refused cold
// Finding (`.agent/W5-01-build-spec.md` caps table row `cold-scenarios`, "Capture producer method", C5 lines 374/410/434/
// 444/446). Served API (host lab_app, read-only) + Vite + own headless Chrome; no request is rewritten. Template:
// `.agent/W5-01a-C3-evidence/capture.mjs`.
// usage: node capture.mjs <out-dir> <revision> <state> [scenario_at]
//   state: empty | authored | historical | pending | refused | finding-refused-unknown | mock
//   `historical` takes the saved pre-correction `scenario_at` (the C4 list GET right after the first POST).
// Each capture first GETs the same read the page makes and records status, selection state and
// `window.committed_watermark` (the capture clock; current captures omit `known_at`). Refusals assert 422 COLD_WINDOW_INVALID.
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [, , OUT, REV, STATE, SCENARIO_AT = null] = process.argv;
const WEB = process.env.W501_WEB ?? "http://localhost:6291";
const API = process.env.W501_API ?? "http://127.0.0.1:9891";
const PORT = Number(process.env.W501_CDP ?? 9892);
const CODE = "COLD-LAB-001";
const W = "from=2026-10-06T19:00:00Z&to=2026-10-06T20:05:00Z";
const BAD = "from=2026-10-06T20:05:00Z&to=2026-10-06T19:00:00Z";
const SIZES = [[1440, 1000], [390, 900]];
const EXPECT = { empty: "CURRENT", authored: "CURRENT", historical: "CURRENT", pending: "PENDING_RECOMPUTE" };
// Spec caps (inclusive) 1440/390: closed one-row/empty panel 430/560, expanded one-row 650/560, disclosure scroller 360 at
// both widths (ruling Q-C5b-4), notice 90/135, page 1250/1500. Pager counter `[data-scenarios-page-count]` (Q-C5b-2).
const CAPS = { 1440: { panel: 430, panel_expanded: 650, disclosure: 360, notice: 90, page: 1250 }, 390: { panel: 560, panel_expanded: 560, disclosure: 360, notice: 135, page: 1500 } };
mkdirSync(OUT, { recursive: true });

let query = W;
if (STATE === "historical") query = `${W}&scenario_at=${encodeURIComponent(SCENARIO_AT)}`;
if (STATE === "refused" || STATE === "finding-refused-unknown") query = BAD;

let read = null, readOk = true, findingId = null;
if (STATE === "finding-refused-unknown") {
  // A real imported W2 Finding for COLD-LAB-001 on the valid window, then its detail with from > to.
  const list = await (await fetch(`${API}/api/sites/${CODE}/cold/findings?${W}`)).json();
  const items = list.items ?? list.findings ?? [];
  findingId = items[0]?.id ?? items[0]?.finding_id ?? null;
  const ok = await fetch(`${API}/api/sites/${CODE}/cold/findings/${findingId}?${W}`);
  const api = await fetch(`${API}/api/sites/${CODE}/cold/findings/${findingId}?${query}`);
  const body = await api.json();
  read = { finding_id: findingId, finding_count: items.length, valid_window_http: ok.status, http: api.status, code: body?.error?.code ?? null };
  readOk = ok.status === 200 && read.http === 422 && read.code === "COLD_WINDOW_INVALID";
} else if (STATE !== "mock") {
  const api = await fetch(`${API}/api/sites/${CODE}/cold/financials/scenarios?${query}`);
  const body = await api.json();
  read = {
    http: api.status, code: body?.error?.code ?? null, selection_state: body?.selection?.state ?? null,
    committed_watermark: body?.window?.committed_watermark ?? null, known_at: body?.window?.known_at ?? null,
    scenario_at: body?.scenario_at ?? null, total_pages: body?.total_pages ?? null,
    items: body?.items?.map((i) => `${i.code} r${i.revision_no} ${i.scenario_state} cutoff=${i.authored_basis?.cutoff}`) ?? null,
  };
  readOk = STATE === "refused" ? read.http === 422 && read.code === "COLD_WINDOW_INVALID"
    : read.http === 200 && read.selection_state === EXPECT[STATE] && (STATE === "empty" ? read.items.length === 0 : read.items.length === 1)
      && (STATE !== "historical" || (read.scenario_at === SCENARIO_AT && read.items[0].includes("HISTORICAL")));
}

const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe",
  ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`,
   `--user-data-dir=${mkdtempSync(join(tmpdir(), "w501bcap-"))}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let url = null;
for (let i = 0; i < 60 && !url; i++) {
  try { url = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page")?.webSocketDebuggerUrl; } catch {}
  if (!url) await sleep(250);
}
const ws = new WebSocket(url);
await new Promise((r) => ws.addEventListener("open", r));
let n = 0; const pending = new Map();
ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
const send = (method, params = {}) => new Promise((res, rej) => { const id = ++n; pending.set(id, (m) => m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result)); ws.send(JSON.stringify({ id, method, params })); });
const evalv = async (expression) => (await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true })).result.value;
await send("Page.enable"); await send("Runtime.enable");

const MEASURE = (isMock) => `(async () => {
  await document.fonts.ready;
  const h = (el) => el ? Math.round(el.getBoundingClientRect().height) : null;
  const t = (el) => el ? el.textContent.replace(/\\s+/g, " ").trim() : null;
  const root = document.querySelector("main") ?? document.body;
  const q = (s) => root.querySelector(s);
  const parts = ${isMock ? `{
    h1: q(".page-heading h1"), description: q(".page-heading p"), state_notice: null,
    panel: q("section.panel"), panel_title: q("section.panel .panel-head h2"), panel_subtitle: q("section.panel .panel-head p"),
    empty: q("section.panel .empty"), table: null, closing_notice: q(".notice.blue"), refusal: null, finding_strip: null }` : `{
    h1: q("h1"), description: q(".page-header__subtitle"), state_notice: q("[data-scenarios-state-notice]"),
    panel: q("section.panel.cold-scenarios-panel"), panel_title: q("section.panel.cold-scenarios-panel .panel__heading"),
    panel_subtitle: q("section.panel.cold-scenarios-panel .panel__description"), empty: q("[data-scenarios-empty]"),
    table: q("section.panel.cold-scenarios-panel table"), closing_notice: q("[data-scenarios-closing-notice]"),
    refusal: q("[data-page-refusal]"), finding_strip: q("[aria-label='Finding state']") }`};
  const order = ["h1", "description", "state_notice", "panel", "empty", "table", "closing_notice"].filter((k) => parts[k]);
  const inOrder = order.every((k, i) => i === 0 || (parts[order[i - 1]].compareDocumentPosition(parts[k]) & Node.DOCUMENT_POSITION_FOLLOWING));
  const blocks = { panel: h(parts.panel), state_notice: h(parts.state_notice), closing_notice: h(parts.closing_notice), empty: h(parts.empty),
    refusal: h(parts.refusal), finding_strip: h(parts.finding_strip), page: document.documentElement.scrollHeight };
  const basis = Array.from(root.querySelectorAll(".cold-scenarios-basis")).map((el) => ({ h: h(el), maxHeight: getComputedStyle(el).maxHeight,
    overflowY: getComputedStyle(el).overflowY, scrollHeight: el.scrollHeight, scrolls: el.scrollHeight > el.clientHeight + 1 }));
  const ellipsized = Array.from(root.querySelectorAll("*")).filter((el) => getComputedStyle(el).textOverflow === "ellipsis" && el.scrollWidth > el.clientWidth).length;
  const fs = parts.finding_strip, rf = parts.refusal;
  return { text: { h1: t(parts.h1), description: t(parts.description), panel_title: t(parts.panel_title), panel_subtitle: t(parts.panel_subtitle),
      empty: t(parts.empty), closing_notice: t(parts.closing_notice), state_notice: t(parts.state_notice), refusal: t(rf), finding_strip: t(fs) },
    order, in_order: inOrder, blocks, basis, ellipsized,
    finding_strip_directly_above_refusal: fs && rf ? (fs.compareDocumentPosition(rf) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0 &&
      Array.from(root.querySelectorAll("*")).filter((e) => (fs.compareDocumentPosition(e) & Node.DOCUMENT_POSITION_FOLLOWING) && (e.compareDocumentPosition(rf) & Node.DOCUMENT_POSITION_FOLLOWING) && !fs.contains(e) && !e.contains(rf) && e.offsetParent !== null && e.textContent.trim()).length === 0 : null,
    page_count: t(root.querySelector("[data-scenarios-page-count]")),
    notice_icons: Array.from(root.querySelectorAll("[data-scenarios-closing-notice] svg")).length,
    rows: root.querySelectorAll("[data-scenario-row]").length, expansions: root.querySelectorAll("[data-scenario-expansion]").length,
    scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth };
})()`;

async function shoot(target, w, hgt, file, isMock, expand = false) {
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: hgt, deviceScaleFactor: 1, mobile: false });
  await send("Page.navigate", { url: target });
  for (let i = 0; i < 160; i++) {
    await sleep(150);
    const ready = await evalv(isMock ? `document.querySelectorAll("section.panel").length > 0`
      : `(() => { const m = document.querySelector("main"); return !!m && !/Loading /.test(m.innerText) &&
          (m.querySelector("[data-page-refusal]") !== null || m.querySelector("[data-scenarios-closing-notice]") !== null); })()`);
    if (ready) break;
  }
  if (expand) {
    await evalv(`document.querySelectorAll("[data-scenario-review]").forEach((b) => b.click())`);
    for (let i = 0; i < 40; i++) { await sleep(100); if (await evalv(`document.querySelectorAll("[data-scenario-expansion]").length > 0`)) break; }
  }
  await sleep(400);
  const m = await evalv(MEASURE(isMock));
  const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width: w, height: Math.min(m.blocks.page, 8000), scale: 1 } });
  writeFileSync(join(OUT, file), Buffer.from(shot.data, "base64"));
  return m;
}

const evidencePath = join(OUT, "evidence.json");
const prior = existsSync(evidencePath) ? JSON.parse(readFileSync(evidencePath, "utf8")) : { captures: [] };
const caps = [];
const variants = STATE === "authored" || STATE === "historical" ? [false, true] : [false];
for (const [w, hgt] of SIZES) {
  if (STATE === "mock") {
    const m = await shoot(`${WEB}/mockups/v69/index.html#/cold-scenarios`, w, hgt, `cold-scenarios-${w}-mock.png`, true);
    caps.push({ name: "cold-scenarios-mock", viewport: `${w}x${hgt}`, image: `cold-scenarios-${w}-mock.png`, measured: m,
      no_overflow: m.scrollWidth <= m.clientWidth });
    continue;
  }
  for (const expand of variants) {
    const name = STATE === "finding-refused-unknown" ? "cold-finding-refused-unknown" : `cold-scenarios-${STATE}${expand ? "-expanded" : ""}`;
    const app = STATE === "finding-refused-unknown" ? `${WEB}/sites/${CODE}/findings/${findingId}?${query}`
      : `${WEB}/sites/${CODE}/financials/scenarios?${query}`;
    const image = `${name}-${w}-app.png`;
    const m = await shoot(app, w, hgt, image, false, expand);
    const c = CAPS[w];
    const over = [];
    const panelCap = expand ? c.panel_expanded : c.panel;
    if (panelCap != null && m.blocks.panel != null && m.blocks.panel > panelCap) over.push(`panel ${m.blocks.panel} > ${panelCap}`);
    for (const k of ["state_notice", "closing_notice"]) if (m.blocks[k] != null && m.blocks[k] > c.notice) over.push(`${k} ${m.blocks[k]} > ${c.notice}`);
    if (m.blocks.page > c.page) over.push(`page ${m.blocks.page} > ${c.page}`);
    let disclosure = null;
    if (expand) {
      disclosure = { measured: m.basis.length, non_empty: m.basis.length > 0, max: Math.max(...m.basis.map((b) => b.h)),
        ok: m.basis.length > 0 && m.basis.every((b) => b.h <= c.disclosure) };
      if (!disclosure.ok) over.push(`disclosure ${disclosure.max} > ${c.disclosure} or empty set`);
    }
    if (m.rows > 0 && m.page_count !== "1 of 1") over.push(`page counter ${JSON.stringify(m.page_count)} != "1 of 1"`);
    caps.push({ name, viewport: `${w}x${hgt}`, app_url: app, image, read, read_ok: readOk,
      clock: read?.committed_watermark ?? null, scenario_at_param: STATE === "historical" ? SCENARIO_AT : null,
      measured: m, no_overflow: m.scrollWidth <= m.clientWidth, panel_cap: panelCap ?? null, over_cap: over, disclosure });
  }
}
const keep = prior.captures.filter((p) => !caps.some((c) => c.name === p.name && c.viewport === p.viewport));
writeFileSync(evidencePath, JSON.stringify({ ...prior, revision: REV, captures: [...keep, ...caps] }, null, 2));
for (const p of caps) {
  console.log(`${p.name} ${p.viewport} read=${p.read ? `${p.read.http}/${p.read.code ?? p.read.selection_state}` : "-"} ok=${p.read_ok ?? "-"} clock=${p.clock ?? "-"} ` +
    `overflow=${!p.no_overflow} ellipsized=${p.measured.ellipsized} order=${p.measured.order.join(">")} inOrder=${p.measured.in_order} rows=${p.measured.rows} exp=${p.measured.expansions} ` +
    `pageCount=${p.measured.page_count} overCap=[${(p.over_cap ?? []).join("; ")}] disclosure=${JSON.stringify(p.disclosure ?? null)} blocks=${JSON.stringify(p.measured.blocks)}`);
}
ws.close(); chrome.kill(); process.exit(0);
