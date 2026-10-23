// W5-03a E2/E3: app vs v69 mock at 1440x1000 and 390x900 for the EV Availability and Energy pages
// (`.agent/W5-03-build-spec.md` "Capture producer method" and the measured caps). Served API (host lab_app) + Vite +
// own headless Chrome; no request is rewritten.
// usage: node capture.mjs <out-dir> <revision> <page> <state> [known_at]
//   page: availability | energy. state names the capture; `refused` uses from > to (422 EV_WINDOW_INVALID).
// Each capture first GETs the same /ev/<page> read the page makes and records its status, selection state and
// `window.committed_watermark` (the capture clock).
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [, , OUT, REV, PAGE, STATE, KNOWN = null] = process.argv;
const WEB = process.env.W503_WEB ?? "http://localhost:6191";
const API = process.env.W503_API ?? "http://127.0.0.1:9791";
const PORT = Number(process.env.W503_CDP ?? 9792);
const CODE = "EV-LAB-001";
const W = "from=2026-10-06T08:00:00Z&to=2026-10-06T09:00:00Z";
const BAD = "from=2026-10-06T09:00:00Z&to=2026-10-06T08:00:00Z";
const query = STATE === "refused" ? BAD : KNOWN ? `${W}&known_at=${encodeURIComponent(KNOWN)}` : W;
const EXPECT = { pending: "PENDING_RECOMPUTE", historical: "HISTORICAL" };
const SIZES = [[1440, 1000], [390, 900]];
// Spec "Mock measurement and rendering limits", app caps (inclusive), 1440 / 390.
const CAPS = PAGE === "availability" ? {
  1440: { status: 90, cards: 180, "Connector states over the service schedule": 340, "Full-schedule availability bound": 260, "Most useful next evidence": 260, page: 1300 },
  390: { status: 125, cards: 350, "Connector states over the service schedule": 390, "Full-schedule availability bound": 280, "Most useful next evidence": 280, page: 1950 },
} : {
  1440: { status: 90, cards: 180, "Import power and configured limit": 440, "What can be concluded": 440, "Technical-to-financial bridge": 350, page: 1500 },
  390: { status: 155, cards: 340, "Import power and configured limit": 430, "What can be concluded": 430, "Technical-to-financial bridge": 520, page: 2320 },
};
mkdirSync(OUT, { recursive: true });

const api = await fetch(`${API}/api/sites/${CODE}/ev/${PAGE}?${query}`);
const body = await api.json();
const read = {
  http: api.status,
  code: body?.error?.code ?? null,
  selection_state: body?.selection?.state ?? null,
  committed_watermark: body?.window?.committed_watermark ?? null,
  known_at: body?.window?.known_at ?? null,
  schedule_state: body?.availability?.schedule_state ?? null,
  seconds: body?.availability ? [body.availability.scheduled_seconds, body.availability.known_available_seconds, body.availability.known_unavailable_seconds, body.availability.unknown_seconds] : null,
  energy: body?.energy ? { complete: body.energy.metered_complete_kwh, partial: body.energy.partial_kwh, unknown_s: body.energy.unknown_seconds, samples: body.energy.import_sample_count, peak: body.energy.observed_peak_import_kw, consequence: body.energy.consequence?.state ?? null } : null,
};
const readOk = STATE === "refused" ? read.http === 422 && read.code === "EV_WINDOW_INVALID"
  : read.http === 200 && (EXPECT[STATE] === undefined ? read.selection_state === "CURRENT" : read.selection_state === EXPECT[STATE]);

const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe",
  ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`,
   `--user-data-dir=${mkdtempSync(join(tmpdir(), "w503cap-"))}`, "about:blank"], { stdio: "ignore" });
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
    status: h(root.querySelector(${isMock ? '".statusbar"' : '".status-strip"'})),
    cards: h(root.querySelector(${isMock ? '".cards"' : '"ul.v69-cards"'})),
    notice: h(${isMock ? 'Array.from(root.querySelectorAll(".notice")).pop()' : 'null'}),
    refusal: h(root.querySelector("[data-page-refusal]")),
    state_notice: h(root.querySelector("[data-ev-depth-state-notice]")),
  };
  for (const p of panels) blocks[p.title] = p.h;
  blocks.page = document.documentElement.scrollHeight;
  const ellipsized = Array.from(root.querySelectorAll("*")).filter((el) => getComputedStyle(el).textOverflow === "ellipsis" && el.scrollWidth > el.clientWidth).length;
  return { panels: panels.map((p) => p.title).filter(Boolean), blocks, scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth, ellipsized, text: root.innerText.slice(0, 4000) };
})()`;

async function shoot(target, w, hgt, file, isMock) {
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: hgt, deviceScaleFactor: 1, mobile: false });
  await send("Page.navigate", { url: target });
  for (let i = 0; i < 160; i++) {
    await sleep(150);
    const ready = await evalv(isMock ? `document.querySelectorAll("section.panel").length > 0`
      : `(() => { const m = document.querySelector("main"); return !!m && !/Loading /.test(m.innerText) &&
          (m.querySelector("[data-page-refusal]") !== null || m.querySelectorAll("section.panel").length === 3); })()`);
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
  const app = `${WEB}/sites/${CODE}/performance/${PAGE}?${query}`;
  const pair = { state: `${PAGE}-${STATE}`, viewport: `${w}x${hgt}`, app_url: app, read, read_ok: readOk };
  pair.app_image = `${PAGE}-${STATE}-${w}-app.png`;
  pair.app = await shoot(app, w, hgt, pair.app_image, false);
  pair.mock_image = `${PAGE}-${w}-mock.png`;
  pair.mock = await shoot(`${WEB}/mockups/v69/index.html#/${PAGE}`, w, hgt, pair.mock_image, true);
  pair.mock.text = undefined;
  pair.titles_equal = STATE === "refused" ? null : JSON.stringify(pair.app.panels) === JSON.stringify(pair.mock.panels);
  pair.no_overflow = pair.app.scrollWidth <= pair.app.clientWidth;
  pair.over_cap = Object.entries(CAPS[w]).filter(([k, cap]) => pair.app.blocks[k] != null && pair.app.blocks[k] > cap).map(([k, cap]) => `${k} ${pair.app.blocks[k]} > ${cap}`);
  pairs.push(pair);
}
writeFileSync(evidencePath, JSON.stringify({ revision: REV, pairs: [...prior.pairs.filter((p) => p.state !== `${PAGE}-${STATE}`), ...pairs] }, null, 2));
for (const p of pairs) {
  console.log(`${p.state} ${p.viewport} read=${p.read.http}/${p.read.code ?? p.read.selection_state} ok=${p.read_ok} wm=${p.read.committed_watermark} ` +
    `overflow=${!p.no_overflow} titlesEqual=${p.titles_equal} overCap=[${p.over_cap.join("; ")}] ellipsized=${p.app.ellipsized} blocks=${JSON.stringify(p.app.blocks)}`);
}
ws.close(); chrome.kill(); process.exit(0);
