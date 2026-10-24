// W5-03b E4/E6: app vs v69 mock at 1440x1000 and 390x900 for EV Health and EV Scenarios
// (`.agent/W5-03-build-spec.md` "Capture producer method", measured caps, E4/E6 cards and
// `.agent/W5-03b-ui-preflight-rulings.md` point 8). Served API (host lab_app) + Vite + own headless Chrome; no request
// is rewritten. Adapted from `.agent/W5-03a-evidence/capture.mjs`.
// usage: node capture.mjs <out-dir> <revision> <page> <state> [known_at] [scenario_at] [--expand]
//   page: health | scenarios. state names the capture; `refused` uses from > to (422 EV_WINDOW_INVALID).
//   --expand clicks every `Review assumptions →` before measuring (the basis disclosure capture).
// Each capture first GETs the same read the page makes and records its status, selection state, rows/items and
// `window.committed_watermark` (the capture clock).
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const args = process.argv.slice(2).filter((a) => a !== "--expand");
const EXPAND = process.argv.includes("--expand");
const [OUT, REV, PAGE, STATE, KNOWN_RAW = "", AT_RAW = ""] = args;
if (!/^[0-9a-f]{8,40}$/.test(REV)) { console.error(`revision must be a commit SHA, got ${REV}`); process.exit(2); }  // S-L1: no "wip" stamps
const KNOWN = KNOWN_RAW || null;
const AT = AT_RAW || null;
const WEB = process.env.W503_WEB ?? "http://localhost:6191";
const API = process.env.W503_API ?? "http://127.0.0.1:9791";
const PORT = Number(process.env.W503_CDP ?? 9792);
const CODE = "EV-LAB-001";
const W = "from=2026-10-06T08:00:00Z&to=2026-10-06T09:00:00Z";
const BAD = "from=2026-10-06T09:00:00Z&to=2026-10-06T08:00:00Z";
let query = STATE === "refused" ? BAD : KNOWN ? `${W}&known_at=${encodeURIComponent(KNOWN)}` : W;
if (AT) query += `&scenario_at=${encodeURIComponent(AT)}`;
const NAME = `ev-${PAGE}-${STATE}${EXPAND ? "-expanded" : ""}`;
const EXPECT = {
  pending: "PENDING_RECOMPUTE", historical: "HISTORICAL", unknown: "UNKNOWN",
};
const SIZES = [[1440, 1000], [390, 900]];
const PANEL = PAGE === "health" ? "Condition and evidence" : "Financial scenarios";
const MOCK = PAGE === "health" ? "ev-health" : "ev-scenarios";
const apiPath = PAGE === "health" ? `/api/sites/${CODE}/ev/health` : `/api/sites/${CODE}/ev/financials/scenarios`;
const appPath = PAGE === "health" ? `/sites/${CODE}/health` : `/sites/${CODE}/ev/financials/scenarios`;
mkdirSync(OUT, { recursive: true });

const api = await fetch(`${API}${apiPath}?${query}`);
const body = await api.json();
const rows = body?.health?.rows ?? null;
const read = {
  http: api.status,
  code: body?.error?.code ?? null,
  selection_state: body?.selection?.state ?? null,
  committed_watermark: body?.window?.committed_watermark ?? null,
  known_at: body?.window?.known_at ?? null,
  scenario_at: body?.scenario_at ?? null,
  rows: rows ? rows.map((r) => `${r.kind}:${r.label}:${r.condition_state}:${r.evidence_ids.length}`) : null,
  items: body?.items ? body.items.map((i) => `${i.code}:r${i.revision_no}:${i.scenario_state}`) : null,
  next_cursor: body?.next_cursor ?? null,
};
// Scenarios `historical` is the authored clock (saved pre-correction `scenario_at`): the selection stays CURRENT and
// the returned earlier revision must be HISTORICAL (ruling 16).
const scenarioHistorical = PAGE === "scenarios" && STATE === "historical";
const expected = scenarioHistorical ? "CURRENT" : EXPECT[STATE] ?? (STATE === "scenarios-pending" ? "PENDING_RECOMPUTE" : "CURRENT");
const readOk = STATE === "refused" ? read.http === 422 && read.code === "EV_WINDOW_INVALID"
  : read.http === 200 && read.selection_state === expected &&
    (!scenarioHistorical || (read.items ?? []).some((i) => i.endsWith(":r1:HISTORICAL")));
// Health 3-row fixture cap 410/540 (ruling 8), 2-row 330/440; cards 200/380; page 1200/1550.
const tableRows = rows ? rows.filter((r) => r.kind !== "UNKNOWN").length : 0;
const CAPS = PAGE === "health" ? {
  1440: { cards: 200, [PANEL]: tableRows >= 3 ? 410 : 330, page: 1200 },
  390: { cards: 380, [PANEL]: tableRows >= 3 ? 540 : 440, page: 1550 },
} : {
  1440: { [PANEL]: EXPAND ? Infinity : 430, closing_notice: 90, basis: 360, page: EXPAND ? Infinity : 1250 },
  390: { [PANEL]: EXPAND ? Infinity : 560, closing_notice: 135, basis: 360, page: EXPAND ? Infinity : 1500 },
};

const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe",
  ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`,
   `--user-data-dir=${mkdtempSync(join(tmpdir(), "w503bcap-"))}`, "about:blank"], { stdio: "ignore" });
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
  const root = document.querySelector("main") ?? document.body;
  const panels = Array.from(root.querySelectorAll("section.panel")).map((p) => ({ title: (p.querySelector("h2")?.textContent ?? "").trim(), h: h(p) }));
  const blocks = {
    cards: h(root.querySelector(${isMock ? '".cards"' : '"ul.v69-cards"'})),
    closing_notice: h(${isMock ? 'Array.from(root.querySelectorAll(".notice")).pop()' : 'root.querySelector("[data-ev-scenarios-closing-notice], [data-ev-health-condition-notice]")'}),
    refusal: h(root.querySelector("[data-page-refusal]")),
    state_notice: h(root.querySelector("[data-ev-depth-state-notice], [data-ev-scenarios-state-notice]")),
    basis: h(root.querySelector("[data-ev-scenario-basis]")),
  };
  for (const p of panels) blocks[p.title] = p.h;
  blocks.page = document.documentElement.scrollHeight;
  const ellipsized = Array.from(root.querySelectorAll("*")).filter((el) => getComputedStyle(el).textOverflow === "ellipsis" && el.scrollWidth > el.clientWidth).length;
  // Cells whose content overflows them horizontally (long IDs must break inside the cell).
  const overflowingCells = Array.from(root.querySelectorAll("td, th")).filter((c) => c.scrollWidth > c.clientWidth + 1).length;
  // S-L1: `DataTable` renders `.data-table__scroll`; report each scroller's real widths. A Health table must not scroll.
  const tableScrolls = Array.from(root.querySelectorAll(".data-table__scroll")).map((s) => ({ scrollWidth: s.scrollWidth, clientWidth: s.clientWidth, overflows: s.scrollWidth > s.clientWidth + 1 }));
  // Ruling 25: browser-computed header backgrounds of every sticky table (first cell and the one after it).
  const headerBackgrounds = Array.from(root.querySelectorAll(".data-table__scroll--sticky thead tr")).map((tr) => Array.from(tr.children).slice(0, 2).map((c) => getComputedStyle(c).backgroundColor));
  const basisMaxHeight = (() => { const b = root.querySelector("[data-ev-scenario-basis]"); return b ? getComputedStyle(b).maxHeight : null; })();
  const order = Array.from(root.children).map((el) => el.matches("section.panel") ? "panel:" + (el.querySelector("h2")?.textContent ?? "").trim()
    : el.matches("ul.v69-cards") ? "cards" : el.matches(".v69-notice--blue") ? "blue-notice" : el.matches(".v69-notice") ? "notice" : null).filter(Boolean);
  return { panels: panels.map((p) => p.title).filter(Boolean), blocks, scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth, ellipsized, overflowingCells, tableScrolls, headerBackgrounds, basisMaxHeight, order, text: root.innerText.slice(0, 4000) };
})()`;

async function shoot(target, w, hgt, file, isMock) {
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: hgt, deviceScaleFactor: 1, mobile: false });
  await send("Page.navigate", { url: target });
  for (let i = 0; i < 160; i++) {
    await sleep(150);
    const ready = await evalv(isMock ? `document.querySelectorAll("section.panel").length > 0`
      : `(() => { const m = document.querySelector("main"); return !!m && !/Loading /.test(m.innerText) &&
          (m.querySelector("[data-page-refusal]") !== null || m.querySelectorAll("section.panel").length === 1); })()`);
    if (ready) break;
  }
  if (!isMock && EXPAND) {
    await evalv(`(() => { document.querySelectorAll("[data-ev-scenario-review]").forEach((b) => b.click()); return true; })()`);
    await sleep(300);
  }
  await sleep(400);
  const m = await evalv(MEASURE(isMock));
  const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width: w, height: Math.min(m.blocks.page, 8000), scale: 1 } });
  writeFileSync(join(OUT, file), Buffer.from(shot.data, "base64"));
  return m;
}

const evidencePath = join(OUT, "evidence.json");
const prior = existsSync(evidencePath) ? JSON.parse(readFileSync(evidencePath, "utf8")) : { pairs: [] };
const pairs = [];
for (const [w, hgt] of SIZES) {
  const app = `${WEB}${appPath}?${query}`;
  const pair = { state: NAME, viewport: `${w}x${hgt}`, app_url: app, read, read_ok: readOk };
  pair.app_image = `${NAME}-${w}-app.png`;
  pair.app = await shoot(app, w, hgt, pair.app_image, false);
  pair.mock_image = `${MOCK}-${w}-mock.png`;
  pair.mock = await shoot(`${WEB}/mockups/v69/index.html#/${MOCK}`, w, hgt, pair.mock_image, true);
  pair.mock.text = undefined;
  pair.titles_equal = STATE === "refused" ? null : JSON.stringify(pair.app.panels) === JSON.stringify(pair.mock.panels);
  pair.no_overflow = pair.app.scrollWidth <= pair.app.clientWidth;
  pair.over_cap = Object.entries(CAPS[w]).filter(([k, cap]) => pair.app.blocks[k] != null && pair.app.blocks[k] > cap).map(([k, cap]) => `${k} ${pair.app.blocks[k]} > ${cap}`);
  pair.revision = REV;
  const tables = pair.app.tableScrolls;
  pair.table_scrolls_nonempty = tables.length > 0;  // non-vacuity: the measured set is not empty when a table is rendered
  pair.hidden_columns = PAGE === "health" ? tables.filter((t) => t.overflows).length : null;
  pair.header_grey = pair.app.headerBackgrounds.every((r) => r.every((c) => c === "rgb(248, 250, 253)"));
  pairs.push(pair);
}
writeFileSync(evidencePath, JSON.stringify({ revision: REV, pairs: [...prior.pairs.filter((p) => p.state !== NAME), ...pairs] }, null, 2));
for (const p of pairs) {
  console.log(`${p.state} ${p.viewport} read=${p.read.http}/${p.read.code ?? p.read.selection_state} ok=${p.read_ok} wm=${p.read.committed_watermark} ` +
    `overflow=${!p.no_overflow} titlesEqual=${p.titles_equal} overCap=[${p.over_cap.join("; ")}] ellipsized=${p.app.ellipsized} ` +
    `cellOverflow=${p.app.overflowingCells} tables=${JSON.stringify(p.app.tableScrolls)} headerGrey=${p.header_grey} basisMax=${p.app.basisMaxHeight} order=${p.app.order.join(">")} blocks=${JSON.stringify(p.app.blocks)}`);
}
ws.close(); chrome.kill(); process.exit(0);
