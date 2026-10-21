// W3-03 run 2 app capture: the mounted estate Portfolio root at 1440 and 390 (W3-02 capture pattern; closure 4 S17
// reviewed equivalent of tools/layout-evidence.mjs). Records every closure-2 Q24 block and the four named-panel caps.
// Usage: node capture-portfolio.mjs <out-dir> <state> <base> <app-path>  -> portfolio-<state>-<w>-app.png + app-portfolio-<state>.json
// Stops only the Chrome it started (finally block), never other Chrome processes.
import { spawn } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [, , OUT, STATE, BASE, PATH] = process.argv;
const PORT = 9783;
const SIZES = [[1440, 1000], [390, 900]];
// Max heights (px): mock + max(24, ceil(10%)) from .agent/W3-03-mock-measurements.md (closure 2 Q24 + named panels).
const MAX = {
  1440: { header: 85, context: 46, scope: 39, card0: 199, card1: 199, card2: 199, card3: 199, card4: 199, pulse0: 40, pulse1: 40, pulse2: 40, pulse3: 40, pulseNote: 36,
          priority: 780, objectives: 413, side: 780, opportunity: 247, progress: 247, footQty: 38, footLink: 38, footCoverage: 38, doc: 1714 },
  390: { header: 99, context: 73, scope: 39, card0: 207, card1: 207, card2: 193, card3: 193, card4: 205, pulse0: 40, pulse1: 40, pulse2: 40, pulse3: 40, pulseNote: 36,
         priority: 851, objectives: 413, side: 564, opportunity: 272, progress: 328, footQty: 53, footLink: 38, footCoverage: 38, doc: 3512 },
};
mkdirSync(OUT, { recursive: true });
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe",
  ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`,
   `--user-data-dir=${mkdtempSync(join(tmpdir(), "w303cap-"))}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let ws;
try {
  let url = null;
  for (let i = 0; i < 80 && !url; i++) {
    try { url = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page")?.webSocketDebuggerUrl; } catch {}
    if (!url) await sleep(250);
  }
  ws = new WebSocket(url);
  await new Promise((r) => ws.addEventListener("open", r));
  let n = 0; const pending = new Map();
  ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
  const send = (method, params = {}) => new Promise((res, rej) => { const id = ++n; pending.set(id, (m) => m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result)); ws.send(JSON.stringify({ id, method, params })); });
  const evalv = async (expression) => (await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true })).result.value;
  await send("Page.enable"); await send("Runtime.enable");

  const MEASURE = `(async () => {
    await document.fonts.ready;
    const R = (e) => { if (!e) return null; const b = e.getBoundingClientRect(); return { top: Math.round(b.top + scrollY), h: Math.round(b.height), w: Math.round(b.width) }; };
    const root = document.querySelector('[data-estate-root="portfolio"]');
    const q = (s) => root.querySelector(s);
    const panel = (k) => q('[data-portfolio-panel="' + k + '"]');
    const cards = Array.from(root.querySelectorAll("[data-portfolio-card]"));
    const pulse = Array.from(root.querySelectorAll("[data-portfolio-pulse] > span"));
    const foot = q("[data-portfolio-footer]");
    const scroll = (e) => e ? { client: e.clientWidth, scroll: e.scrollWidth, clientH: e.clientHeight, scrollH: e.scrollHeight } : null;
    const fscroll = q("[data-portfolio-scroll='findings'] .data-table__scroll");
    return {
      h1: document.querySelector("h1")?.textContent.trim() ?? null,
      main: document.querySelector("main")?.getAttribute("aria-label") ?? null,
      railCurrent: document.querySelector('nav[aria-label="Operator routes"] [aria-current="page"]')?.textContent ?? null,
      status: q("[data-portfolio-context]")?.getAttribute("data-portfolio-context") ?? null,
      contextText: q("[data-portfolio-context]")?.textContent.replace(/\\s+/g, " ").trim().slice(0, 200) ?? null,
      cardStates: cards.map((c) => c.getAttribute("data-portfolio-card") + ":" + c.getAttribute("data-portfolio-card-state") + ":" + (c.querySelector("[data-portfolio-card-value]")?.textContent ?? "")),
      rows: root.querySelectorAll("[data-portfolio-row]").length,
      matrixSites: root.querySelectorAll("[data-portfolio-matrix-site]").length,
      blocks: {
        header: R(document.querySelector("header.page-header")), context: R(q("[data-portfolio-context]")),
        scope: R(q("[data-disclosure='portfolio-scope'] > summary")),
        card0: R(cards[0]), card1: R(cards[1]), card2: R(cards[2]), card3: R(cards[3]), card4: R(cards[4]),
        pulse0: R(pulse[0]), pulse1: R(pulse[1]), pulse2: R(pulse[2]), pulse3: R(pulse[3]), pulseNote: R(q(".pulse-note")),
        priority: R(panel("priority")), objectives: R(panel("objectives")), side: R(q("[data-portfolio-side]")),
        opportunity: R(panel("opportunity")), progress: R(panel("progress")),
        footQty: R(foot?.children[0]), footLink: R(foot?.children[1]), footCoverage: R(q("[data-portfolio-footer-coverage]")),
        prompt: R(q("[data-portfolio-prompt]")),
      },
      findingsScroll: fscroll ? { ...scroll(fscroll), maxH: getComputedStyle(fscroll).maxHeight, rowHs: Array.from(fscroll.querySelectorAll("tbody tr")).map((r) => Math.round(r.getBoundingClientRect().height)), cols: Array.from(fscroll.querySelectorAll("thead th")).map((t) => Math.round(t.getBoundingClientRect().width)) } : null,
      matrixScroll: scroll(q("[data-portfolio-scroll='objectives']")),
      docScrollW: document.documentElement.scrollWidth, docClientW: document.documentElement.clientWidth,
      refusal: q("[data-page-refusal]")?.textContent ?? null,
      height: document.documentElement.scrollHeight };
  })()`;

  const results = [];
  for (const [w, h] of SIZES) {
    await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: w < 500 });
    await send("Page.navigate", { url: `${BASE}${PATH}` });
    let ready = false;
    for (let i = 0; i < 200 && !ready; i++) {
      await sleep(150);
      ready = await evalv(`!!document.querySelector('[data-estate-root="portfolio"]') && !document.querySelector("[data-estate-loading]")`);
    }
    await sleep(600);
    const m = await evalv(MEASURE);
    m.blocks.doc = { h: m.height };
    const over = Object.entries(MAX[w]).filter(([k, cap]) => m.blocks[k] && m.blocks[k].h > cap).map(([k, cap]) => `${k} ${m.blocks[k].h}>${cap}`);
    const missing = Object.keys(MAX[w]).filter((k) => !m.blocks[k]);
    const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width: w, height: Math.min(m.height, 6000), scale: 1 } });
    const file = `portfolio-${STATE}-${w}-app.png`;
    writeFileSync(join(OUT, file), Buffer.from(shot.data, "base64"));
    results.push({ width: w, file, ready, over, missing, docOverflow: m.docScrollW > m.docClientW, ...m });
  }
  writeFileSync(join(OUT, `app-portfolio-${STATE}.json`), JSON.stringify(results, null, 1));
  for (const r of results) console.log(`${STATE} ${r.width}: ready=${r.ready} status=${r.status} rows=${r.rows} doc=${r.height} scrollW=${r.docScrollW}/${r.docClientW} over=[${r.over.join("; ")}] missing=[${r.missing.join(",")}]`);
} finally {
  try { ws?.close(); } catch {}
  chrome.kill();
}
