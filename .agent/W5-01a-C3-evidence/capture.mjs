// W5-01a C3: app vs v69 `cold-health` mock at 1440x1000 and 390x900 for the cold Health page (`.agent/W5-01-build-spec.md`
// C3, C3 rulings Q-C3-1..4 and "Capture producer method"). Served API (host lab_app) + Vite + own headless Chrome; no request is rewritten.
// usage: node capture.mjs <out-dir> <revision> <state> [known_at]
//   state: failed-start | unknown | pending | historical | refused. `historical` takes the saved before-late watermark W0.
// Each capture first GETs the same /cold/health read the page makes and records its status, selection state and
// `window.committed_watermark` (the capture clock); refused asserts 422 COLD_WINDOW_INVALID.
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [, , OUT, REV, STATE, KNOWN = null] = process.argv;
const WEB = process.env.W501_WEB ?? "http://localhost:6191";
const API = process.env.W501_API ?? "http://127.0.0.1:9791";
const PORT = Number(process.env.W501_CDP ?? 9792);
const CODE = "COLD-LAB-001";
const W = "from=2026-10-06T19:00:00Z&to=2026-10-06T20:05:00Z";
const BAD = "from=2026-10-06T20:05:00Z&to=2026-10-06T19:00:00Z";
// `unknown`: the C1 backup-failed seed read over the no-selection window (C3 readiness pass 3).
const EMPTY = "from=2026-10-05T19:00:00Z&to=2026-10-05T20:05:00Z";
const query = STATE === "refused" ? BAD : STATE === "unknown" ? EMPTY : KNOWN ? `${W}&known_at=${encodeURIComponent(KNOWN)}` : W;
const EXPECT = { "failed-start": "CURRENT", unknown: "UNKNOWN", pending: "PENDING_RECOMPUTE", historical: "HISTORICAL" };
const SOURCES = "Data sources · data quality, not equipment condition";
const SIZES = [[1440, 1000], [390, 900]];
// Spec "Measured mock and content caps" `cold-health` and the C3 composed caps (inclusive), 1440 / 390.
const CAPS = {
  1440: { cards: 200, "Condition and evidence": 330, [SOURCES]: 700, page: 1900 },
  390: { cards: 430, "Condition and evidence": 430, [SOURCES]: 800, page: 2350 },
};
mkdirSync(OUT, { recursive: true });

const api = await fetch(`${API}/api/sites/${CODE}/cold/health?${query}`);
const body = await api.json();
const read = {
  http: api.status,
  code: body?.error?.code ?? null,
  selection_state: body?.selection?.state ?? null,
  foundation_revision_id: body?.health?.foundation_revision_id ?? null,
  committed_watermark: body?.window?.committed_watermark ?? null,
  known_at: body?.window?.known_at ?? null,
  rows: body?.health?.rows?.map((r) => `${r.kind}=${r.condition_state}/${r.observation}/ids:${r.evidence_ids.length}`) ?? null,
};
const readOk = STATE === "refused" ? read.http === 422 && read.code === "COLD_WINDOW_INVALID" : read.http === 200 && read.selection_state === EXPECT[STATE];

const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe",
  ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`,
   `--user-data-dir=${mkdtempSync(join(tmpdir(), "w501cap-"))}`, "about:blank"], { stdio: "ignore" });
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
    notice: h(${isMock ? 'null' : 'root.querySelector("[data-health-condition-notice]")'}),
    refusal: h(root.querySelector("[data-page-refusal]")),
    state_notice: h(root.querySelector("[data-health-state-notice]")),
    empty_sentence: h(root.querySelector("[data-health-empty]")),
  };
  for (const p of panels) blocks[p.title] = p.h;
  blocks.page = document.documentElement.scrollHeight;
  const ellipsized = Array.from(root.querySelectorAll("*")).filter((el) => getComputedStyle(el).textOverflow === "ellipsis" && el.scrollWidth > el.clientWidth).length;
  // Q-C3-5: each full asset ID sits on one line inside its sticky Asset cell, not clipped or overflowing it.
  const ids = Array.from(root.querySelectorAll("[data-health-asset-id]")).map((el) => {
    const cell = el.closest("th").getBoundingClientRect(); const r = el.getBoundingClientRect();
    return { text: el.textContent, lines: Math.round(r.height / parseFloat(getComputedStyle(el).lineHeight || "14")),
      inside: r.left >= cell.left - 0.5 && r.right <= cell.right + 0.5, clipped: el.scrollWidth > el.clientWidth + 1,
      sticky: getComputedStyle(el.closest("th")).position };
  });
  return { panels: panels.map((p) => p.title).filter(Boolean), blocks, ids, scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth, ellipsized, text: root.innerText.slice(0, 4000) };
})()`;

async function shoot(target, w, hgt, file, isMock) {
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: hgt, deviceScaleFactor: 1, mobile: false });
  await send("Page.navigate", { url: target });
  for (let i = 0; i < 160; i++) {
    await sleep(150);
    const ready = await evalv(isMock ? `document.querySelectorAll("section.panel").length > 0`
      : `(() => { const m = document.querySelector("main"); return !!m && !/Loading /.test(m.innerText) &&
          (m.querySelector("[data-page-refusal]") !== null || m.querySelectorAll("section.panel").length === 2); })()`);
    if (ready) break;
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
  const app = `${WEB}/sites/${CODE}/health?${query}`;
  const pair = { state: `cold-health-${STATE}`, viewport: `${w}x${hgt}`, app_url: app, read, read_ok: readOk };
  pair.app_image = `cold-health-${STATE}-${w}-app.png`;
  pair.app = await shoot(app, w, hgt, pair.app_image, false);
  pair.mock_image = `cold-health-${w}-mock.png`;
  pair.mock = await shoot(`${WEB}/mockups/v69/index.html#/cold-health`, w, hgt, pair.mock_image, true);
  pair.mock.text = undefined;
  // The S7 Data sources panel is the labelled Q-C3-1 mock deviation; every other title must equal the mock's.
  pair.titles_equal = STATE === "refused" ? null : JSON.stringify(pair.app.panels.filter((t) => t !== SOURCES)) === JSON.stringify(pair.mock.panels);
  pair.sources_last = pair.app.panels[pair.app.panels.length - 1] === SOURCES;
  pair.no_overflow = pair.app.scrollWidth <= pair.app.clientWidth;
  pair.over_cap = Object.entries(CAPS[w]).filter(([k, cap]) => pair.app.blocks[k] != null && pair.app.blocks[k] > cap).map(([k, cap]) => `${k} ${pair.app.blocks[k]} > ${cap}`);
  pairs.push(pair);
}
writeFileSync(evidencePath, JSON.stringify({ revision: REV, pairs: [...prior.pairs.filter((p) => p.state !== `cold-health-${STATE}`), ...pairs] }, null, 2));
for (const p of pairs) {
  console.log(`${p.state} ${p.viewport} read=${p.read.http}/${p.read.code ?? p.read.selection_state} ok=${p.read_ok} wm=${p.read.committed_watermark} ` +
    `overflow=${!p.no_overflow} titlesEqual=${p.titles_equal} sourcesLast=${p.sources_last} overCap=[${p.over_cap.join("; ")}] ellipsized=${p.app.ellipsized} blocks=${JSON.stringify(p.app.blocks)}`);
}
ws.close(); chrome.kill(); process.exit(0);
