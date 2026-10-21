// W2-F unit 5: app vs v69 mock at 1440 and 390 for the 22 W2 screens, plus no-selection and refused paths.
// usage: node capture.mjs <out-dir> <revision> <phase: cold-excursion|cold-normal|ev> [finding ids as name=uuid ...]
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [, , OUT, REV, PHASE, ...IDS] = process.argv;
const ids = Object.fromEntries(IDS.map((a) => a.split("=")));
const BASE = "http://localhost:6181";
const PORT = 9782;
const C = "/sites/COLD-LAB-001";
const W = "from=2026-10-06T19:00:00Z&to=2026-10-06T20:05:00Z";
const EMPTY = "from=2026-10-05T19:00:00Z&to=2026-10-05T20:05:00Z";
const BAD = "from=2026-10-06T20:05:00Z&to=2026-10-06T19:00:00Z";
const E = "/sites/EV-LAB-001";
const Q = "from=2026-10-06T08:00:00.000000Z&to=2026-10-06T09:05:00.000000Z&known_at=2026-10-06T09:00:00.000000Z";
const QBAD = "from=2026-10-06T09:05:00.000000Z&to=2026-10-06T08:00:00.000000Z";
const cold = (screen, path, sep = "?") => [
  { screen, case: "stocked", app: `${path}${sep}${W}` },
  { screen, case: "no-selection", app: `${path}${sep}${EMPTY}` },
  { screen, case: "refused", app: `${path}${sep}${BAD}` },
];
const PLANS = {
  "cold-excursion": [
    { screen: "cold-foundation", case: "stocked", app: `${C}/foundation` },
    { screen: "cold-readiness", case: "stocked", app: `${C}/foundation/readiness` },
    { screen: "cold-sld", case: "stocked", app: `${C}/foundation/sld` },
    ...cold("cold", C),
    ...cold("temperature", `${C}/performance/temperature`),
    { screen: "coldbackup", case: "stocked", app: `${C}/performance/backup?${W}` },
    ...cold("cold-evidence", `${C}/evidence`),
    { screen: "cold-evidence-analysis", case: "stocked", app: `${C}/evidence?${W}&view=analysis` },
    ...cold("cold-financials", `${C}/financials`),
    { screen: "cold-assumptions", case: "stocked", app: `${C}/financials/assumptions?${W}` },
    { screen: "cold-finding", case: "stocked", app: `${C}/findings/${ids.start}` },
    { screen: "cold-finding-excursion", case: "stocked", app: `${C}/findings/${ids.excursion}` },
  ],
  "cold-normal": [
    { screen: "cold", case: "normal", app: `${C}?${W}` },
    { screen: "coldbackup", case: "normal", app: `${C}/performance/backup?${W}` },
    { screen: "cold-evidence", case: "normal", app: `${C}/evidence?${W}` },
    { screen: "cold-financials", case: "normal", app: `${C}/financials?${W}` },
  ],
  ev: [
    { screen: "ev-foundation", case: "interrupted", app: `${E}/foundation` },
    { screen: "ev-readiness", case: "interrupted", app: `${E}/foundation/readiness` },
    { screen: "ev-sld", case: "interrupted", app: `${E}/foundation/sld` },
    { screen: "ev", case: "interrupted", app: `${E}/ev?${Q}` },
    { screen: "ev", case: "refused", app: `${E}/ev?${QBAD}` },
    { screen: "sessions", case: "interrupted", app: `${E}/performance/sessions?${Q}` },
    { screen: "ev-evidence", case: "interrupted", app: `${E}/ev/evidence?${Q}` },
    { screen: "ev-evidence-analysis", case: "interrupted", app: `${E}/ev/evidence/analysis?${Q}` },
    { screen: "ev-financials", case: "interrupted", app: `${E}/ev/financials?${Q}` },
    { screen: "ev-assumptions", case: "interrupted", app: `${E}/ev/financial-assumptions?${Q}` },
    { screen: "ev-finding", case: "interrupted", app: `${E}/findings/${ids.finding}?${Q}` },
    { screen: "ev-finding", case: "refused", app: `${E}/findings/${ids.finding}?${QBAD}` },
  ],
};
const SIZES = [[1440, 1000], [390, 900]];
mkdirSync(OUT, { recursive: true });
// Only this run's own headless Chrome is started and killed (its own profile and debugging port).
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe",
  ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`,
   `--user-data-dir=${mkdtempSync(join(tmpdir(), "w2fcap-"))}`, "about:blank"], { stdio: "ignore" });
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

const MEASURE = `(async () => {
  await document.fonts.ready;
  const panels = Array.from(document.querySelectorAll("section.panel")).filter((p, i, a) => a.indexOf(p) === i);
  const out = panels.map((p) => { const h = p.querySelector("h2"); const r = p.getBoundingClientRect();
    return { title: h ? h.textContent.trim().replace(/\\s+/g, " ") : "", x: Math.round(r.x), y: Math.round(r.y + scrollY), w: Math.round(r.width), h: Math.round(r.height) }; })
    .filter((p) => p.title && p.w > 0);
  const clipped = Array.from(document.querySelectorAll("section.panel td, section.panel th, section.panel p, section.panel dd"))
    .filter((el) => el.scrollWidth > el.clientWidth + 1 && getComputedStyle(el).overflowX !== "visible").length;
  return { panels: out, overflowX: document.documentElement.scrollWidth - innerWidth, clipped,
    text: (document.querySelector("main") ?? document.body).innerText.slice(0, 6000), height: document.documentElement.scrollHeight };
})()`;

async function shoot(target, w, h, file, isMock) {
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: false });
  await send("Page.navigate", { url: target });
  for (let i = 0; i < 120; i++) {
    await sleep(150);
    const ready = await evalv(isMock ? `document.querySelectorAll("section.panel").length > 0`
      : `(() => { const m = document.querySelector("main"); return !!m && m.innerText.length > 40 && !/Loading/.test(m.innerText)
          && (document.querySelectorAll("section.panel").length > 0 || ${i} > 60); })()`);
    if (ready) break;
  }
  if (isMock) { const hash = target.slice(target.indexOf("#")); await evalv(`(()=>{ if (location.hash !== ${JSON.stringify(hash)}) location.hash = ${JSON.stringify(hash)}; return true; })()`); await sleep(400); }
  await sleep(400);
  const m = await evalv(MEASURE);
  const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width: w, height: Math.min(m.height, 8000), scale: 1 } });
  writeFileSync(join(OUT, file), Buffer.from(shot.data, "base64"));
  return m;
}

const evidencePath = join(OUT, "evidence.json");
const prior = existsSync(evidencePath) ? JSON.parse(readFileSync(evidencePath, "utf8")) : { pairs: [] };
const keep = prior.pairs.filter((p) => p.phase !== PHASE);
const mocks = {};
const pairs = [];
for (const s of PLANS[PHASE]) for (const [w, h] of SIZES) {
  const pair = { phase: PHASE, screen: s.screen, case: s.case, viewport: `${w}x${h}`, app_url: `${BASE}${s.app}`, mock_hash: `#/${s.screen}` };
  const appFile = `${s.screen}-${s.case}-${w}-app.png`;
  pair.app_image = appFile; pair.app = await shoot(`${BASE}${s.app}`, w, h, appFile, false);
  const mk = `${s.screen}-${w}`;
  if (!mocks[mk]) mocks[mk] = { file: `${s.screen}-${w}-mock.png`, m: await shoot(`${BASE}/mockups/v69/index.html#/${s.screen}`, w, h, `${s.screen}-${w}-mock.png`, true) };
  pair.mock_image = mocks[mk].file; pair.mock = { panels: mocks[mk].m.panels, overflowX: mocks[mk].m.overflowX };
  const at = pair.app.panels.map((p) => p.title), mt = pair.mock.panels.map((p) => p.title);
  pair.titles_equal = JSON.stringify(at) === JSON.stringify(mt);
  pairs.push(pair);
}
writeFileSync(evidencePath, JSON.stringify({ revision: REV, captured_at: new Date().toISOString(), pairs: [...keep, ...pairs] }, null, 2));
for (const p of pairs) {
  console.log(`${p.screen}/${p.case} ${p.viewport} overflowX=${p.app.overflowX} clipped=${p.app.clipped} panels app=${p.app.panels.length} mock=${p.mock.panels.length} titlesEqual=${p.titles_equal}`);
  if (!p.titles_equal) { console.log(`  app:  ${p.app.panels.map((x) => x.title).join(" | ")}`); console.log(`  mock: ${p.mock.panels.map((x) => x.title).join(" | ")}`); }
}
ws.close(); chrome.kill(); process.exit(0);
