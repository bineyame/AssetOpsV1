// W3-03 run 2 app capture: the mounted estate Portfolio root at 1440 and 390 (W3-02 capture pattern; closure 4 S17
// reviewed equivalent of tools/layout-evidence.mjs). Records every closure-2 Q24 block and the four named-panel caps.
// Usage: node capture-portfolio.mjs <out-dir> <state> <base> <app-path> [success <STATUS> <matrixSites> | refusal <CODE> | refusal-409 <api-base>]
//   -> portfolio-<state>-<w>-app.png + app-portfolio-<state>.json. Run 3 (r2 "Run-3 captures"): success captures assert
//   the exact status, four named panels, five cards, full-scope matrix count, over=[], no document overflow and 390
//   internal table/matrix scrolling; refusals record refusal + document dimensions and require every privileged block
//   absent (no positive cap applies to null rectangles); refusal-409 loads page one (limit 1 via the harness control)
//   in one tab per width, adds W303-EMPTY-001, clicks `Load more Findings` in each tab and records the cleared refusal.
//   W303_FORBID (comma list) names Site codes/names that must not appear in refusal or EMPTY_SCOPE text.
// Stops only the Chrome it started (finally block), never other Chrome processes.
import { spawn } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [, , OUT, STATE, BASE, PATH, KIND = "success", ARG1 = null, ARG2 = null] = process.argv;
const FORBID = (process.env.W303_FORBID ?? "").split(",").filter(Boolean);
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
const socks = [];
try {
  const connect = async (wsUrl) => {
    const sock = new WebSocket(wsUrl);
    await new Promise((r) => sock.addEventListener("open", r));
    let n = 0; const pending = new Map();
    sock.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
    const send = (method, params = {}) => new Promise((res, rej) => { const id = ++n; pending.set(id, (m) => m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result)); sock.send(JSON.stringify({ id, method, params })); });
    const evalv = async (expression) => (await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true })).result.value;
    await send("Page.enable"); await send("Runtime.enable");
    socks.push(sock);
    return { send, evalv };
  };
  let url = null;
  for (let i = 0; i < 80 && !url; i++) {
    try { url = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page")?.webSocketDebuggerUrl; } catch {}
    if (!url) await sleep(250);
  }
  const tab0 = await connect(url);
  const newTab = async () => connect((await (await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: "PUT" })).json()).webSocketDebuggerUrl);
  const control = async (path) => { const r = await fetch(`${ARG1}${path}`, { method: "POST" }); if (!r.ok) throw new Error(`control ${path} ${r.status}`); return r.json(); };

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
      matrixSiteTexts: Array.from(root.querySelectorAll("[data-portfolio-matrix-site]")).map((e) => e.textContent.replace(/\\s+/g, " ").trim()),
      panels: Array.from(root.querySelectorAll("[data-portfolio-panel]")).map((e) => e.getAttribute("data-portfolio-panel")),
      cardCount: cards.length,
      loadMore: Array.from(root.querySelectorAll("button")).some((b) => b.textContent.trim() === "Load more Findings"),
      privileged: root.querySelectorAll("[data-portfolio-panel],[data-portfolio-card],[data-portfolio-row],[data-portfolio-matrix-site],[data-portfolio-context],[data-portfolio-footer],[data-portfolio-side],[data-portfolio-pulse]").length,
      rootText: root.textContent.replace(/\\s+/g, " ").trim(),
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
      refusal: q("[data-page-refusal]")?.textContent.replace(/\\s+/g, " ").trim() ?? null,
      refusalCode: q("[data-page-refusal]")?.getAttribute("data-page-refusal") ?? null,
      refusalBlock: R(q("[data-page-refusal]")),
      height: document.documentElement.scrollHeight };
  })()`;

  const ready = async (tab, cond) => { let ok = false; for (let i = 0; i < 200 && !ok; i++) { await sleep(150); ok = await tab.evalv(cond); } await sleep(600); return ok; };
  const LOADED = `!!document.querySelector('[data-estate-root="portfolio"]') && !document.querySelector("[data-estate-loading]")`;
  const REFUSED = `!!document.querySelector('[data-estate-root="portfolio"] [data-page-refusal]')`;
  const open = async (tab, w, h) => {
    await tab.send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: w < 500 });
    await tab.send("Page.navigate", { url: `${BASE}${PATH}` });
  };
  const leaks = (m) => FORBID.filter((f) => m.rootText.includes(f));
  const record = async (tab, w, ok, extra = {}) => {
    const m = await tab.evalv(MEASURE);
    m.blocks.doc = { h: m.height };
    const refused = KIND !== "success";
    const caps = refused ? { doc: MAX[w].doc } : MAX[w];
    const over = Object.entries(caps).filter(([k, cap]) => m.blocks[k] && m.blocks[k].h > cap).map(([k, cap]) => `${k} ${m.blocks[k].h}>${cap}`);
    const missing = refused ? [] : Object.keys(MAX[w]).filter((k) => !m.blocks[k]);
    const checks = refused ? {
      code: m.refusalCode === (KIND === "refusal-409" ? "ESTATE_BASIS_CHANGED" : ARG1),
      privilegedAbsent: m.privileged === 0 && m.rows === 0 && m.cardCount === 0 && m.matrixSites === 0,
      noForbiddenText: leaks(m).length === 0,
      noDocOverflow: m.docScrollW <= m.docClientW,
    } : {
      status: m.status === ARG1,
      fourPanels: JSON.stringify(m.panels) === JSON.stringify(["priority", "objectives", "opportunity", "progress"]),
      fiveCards: m.cardCount === 5,
      matrixFullScope: m.matrixSites === Number(ARG2),
      overEmpty: over.length === 0,
      noDocOverflow: m.docScrollW <= m.docClientW,
      ...(w === 390 ? { tableScrolls: !!m.findingsScroll && m.findingsScroll.scroll > m.findingsScroll.client,
                        matrixScrolls: !!m.matrixScroll && m.matrixScroll.scroll > m.matrixScroll.client } : {}),
      ...(ARG1 === "EMPTY_SCOPE" ? { noForbiddenText: leaks(m).length === 0, zeroRows: m.rows === 0 } : {}),
    };
    const shot = await tab.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width: w, height: Math.min(m.height, 6000), scale: 1 } });
    const file = `portfolio-${STATE}-${w}-app.png`;
    writeFileSync(join(OUT, file), Buffer.from(shot.data, "base64"));
    const leaked = leaks(m);
    delete m.rootText;
    return { width: w, file, ready: ok, kind: KIND, checks, failed: Object.entries(checks).filter(([, v]) => !v).map(([k]) => k), leaked, over, missing, docOverflow: m.docScrollW > m.docClientW, ...extra, ...m };
  };

  const results = [];
  if (KIND === "refusal-409") {
    await control("/__capture/mode?limit1=1");
    const tabs = [];
    for (const [w, h] of SIZES) { const tab = tabs.length ? await newTab() : tab0; await open(tab, w, h); tabs.push([tab, w]); }
    const before = [];
    for (const [tab, w] of tabs) {
      const ok = await ready(tab, `${LOADED} && Array.from(document.querySelectorAll("button")).some((b) => b.textContent.trim() === "Load more Findings")`);
      const m = await tab.evalv(MEASURE);
      before.push({ width: w, ok, status: m.status, rows: m.rows, cards: m.cardCount, matrixSites: m.matrixSiteTexts, loadMore: m.loadMore });
    }
    await control("/__capture/empty-site");
    for (const [i, [tab, w]] of tabs.entries()) {
      await tab.evalv(`(Array.from(document.querySelectorAll("button")).find((b) => b.textContent.trim() === "Load more Findings").click(), true)`);
      const ok = await ready(tab, REFUSED);
      results.push(await record(tab, w, ok, { beforeClick: before[i] }));
    }
    await control("/__capture/mode?limit1=0");
  } else {
    for (const [w, h] of SIZES) {
      await open(tab0, w, h);
      const ok = await ready(tab0, KIND === "success" ? LOADED : REFUSED);
      results.push(await record(tab0, w, ok));
    }
  }
  writeFileSync(join(OUT, `app-portfolio-${STATE}.json`), JSON.stringify(results, null, 1));
  for (const r of results) console.log(`${STATE} ${r.width}: ready=${r.ready} status=${r.status} refusal=${r.refusalCode} rows=${r.rows} cards=${r.cardCount} matrix=${r.matrixSites} doc=${r.height} scrollW=${r.docScrollW}/${r.docClientW} over=[${r.over.join("; ")}] missing=[${r.missing.join(",")}] failed=[${r.failed.join(",")}] leaked=[${r.leaked.join(",")}]`);
} finally {
  for (const s of socks) { try { s.close(); } catch {} }
  chrome.kill();
}
