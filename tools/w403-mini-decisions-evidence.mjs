/* W4-03 unit 9b: app vs v69 mock captures at 1440 and 390 for the three W4-03 screens and both Site Work screens.
   `.agent/W4-03-build-spec.md` "Unit-9 rulings (u9)": capture matrix, inclusive height caps and width limits.
   Usage (through the walkthrough tool, which seeds the capture stock first):
     python tools/w403_mini_decisions_walkthrough.py --db <x_test> --work var/<dir> capture --web http://localhost:6147
   or directly: node tools/w403-mini-decisions-evidence.mjs <web> <work>/capture
   Reads `<work>/replay.json` and `<work>/capture/stock.json`; writes `<state>-<width>-app.png`, `<screen>-<width>-mock.png`
   and `evidence.json` (rectangles, caps and check results) to the capture folder. Every request is served by the real
   walkthrough backend except two named harness rules: a scoped 503 (`fail503`) and a historical cutoff (`knownAt`)
   appended to one exact detail GET, because the Opportunity detail route carries no `known_at` (recorded per state). */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const [, , WEB = "http://localhost:6147", OUT] = process.argv;
if (!OUT) { console.error("usage: node tools/w403-mini-decisions-evidence.mjs <web> <work>/capture"); process.exit(2); }
const REPO = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const MOCK = pathToFileURL(join(REPO, "frontend/mockups/v69/index.html")).href;
const WORK = dirname(resolve(OUT));
const replay = JSON.parse(readFileSync(join(WORK, "replay.json"), "utf-8"));
const stock = JSON.parse(readFileSync(join(resolve(OUT), "stock.json"), "utf-8"));
mkdirSync(OUT, { recursive: true });

const MG = "MG-W402-001";
const KOBO = "KOBO-001";
const [FINDING, FREV] = replay.finding;
const OPP = replay.writes.opportunity_id;
const MISSING = replay.missing.rows.find((r) => r.opportunity.first_day === "2026-10-08")?.opportunity.id ?? null;
const day = (offset) => { const d = new Date(); d.setUTCHours(0, 0, 0, 0); d.setUTCDate(d.getUTCDate() + offset); return d.toISOString().replace(".000Z", "Z"); };
const WORK_WINDOW = `from=${day(-7)}&to=${day(1)}`;
const SIZES = [[1440, 1000], [390, 900]];

// u9 inclusive caps (1440 / 390). Work caps are the reviewed W4-01 caps; the stocked five-row Incident panel is 460.
const CAPS = {
  scenarios: { 1440: { "Financial scenarios": 348, notice: 66 }, 390: { "Financial scenarios": 391, notice: 102 } },
  alternatives: { 1440: { "Alternatives to investigate": 268, notice: 66 }, 390: { "Alternatives to investigate": 365, notice: 84 } },
  "opportunity-finding": {
    1440: { status: 69, cards: 137, "Bounded opportunity": 232, "Next decision": 295, "Consequence basis": 295 },
    390: { status: 96, cards: 273, "Bounded opportunity": 339, "Next decision": 217, "Consequence basis": 295 },
  },
  "sitework-incidents": { 1440: { status: 48, panel: 460, notice: 54 }, 390: { status: 118, panel: 460, notice: 101 } },
  "sitework-maintenance": { 1440: { status: 48, panel: 384, notice: 54 }, 390: { status: 118, panel: 410, notice: 101 } },
};
const MAX_W = { 1440: 1161, 390: 360 };
// Pieces: [name, app selector, mock selector]; a name that is a title means the section.panel whose own h2 is it.
const PIECES = {
  scenarios: [["Financial scenarios"], ["notice", "[data-scenarios-notice]", ".notice"]],
  alternatives: [["Alternatives to investigate"], ["notice", "[data-alternatives-notice]", ".notice"]],
  "opportunity-finding": [["status", "[data-opportunity-status]", ".statusbar"], ["cards", "[data-opportunity-cards]", ".cards"],
    ["Bounded opportunity"], ["Next decision"], ["Consequence basis"]],
  "sitework-incidents": [["status", ".status-strip", ".statusbar"], ["panel", "section.panel", "section.panel"], ["notice", "[data-work-notice]", ".notice"]],
  "sitework-maintenance": [["status", ".status-strip", ".statusbar"], ["panel", "section.panel", "section.panel"], ["notice", "[data-work-notice]", ".notice"]],
};

const S = `/sites/${MG}`;
const CASES = [
  { screen: "scenarios", state: "scenarios-populated", app: `${S}/financials/scenarios` },
  { screen: "scenarios", state: "scenarios-empty", app: `${S}/financials/scenarios?from=1970-01-01T00:00:00.000000Z&to=2026-10-01T00:00:00.000000Z` },
  { screen: "scenarios", state: "scenarios-refused", app: `${S}/financials/scenarios?from=2026-10-21T00:00:00.000000Z&to=2026-10-01T00:00:00.000000Z` },
  { screen: "alternatives", state: "alternatives-db-time", app: `/sites/${KOBO}/findings/${FINDING}/alternatives?revision_id=${FREV}` },
  { screen: "alternatives", state: "alternatives-read-503", app: `/sites/${KOBO}/findings/${FINDING}/alternatives?revision_id=${FREV}`,
    rule: { fail503: "/alternatives?" } },
  { screen: "opportunity-finding", state: "opportunity-current-late-settled", app: `${S}/opportunities/${OPP}` },
  { screen: "opportunity-finding", state: "opportunity-late-stale-k-before-late", app: `${S}/opportunities/${OPP}`,
    rule: { knownAt: { path: `/api/sites/${MG}/opportunities/${OPP}`, value: replay.k_before_late } } },
  ...(MISSING ? [{ screen: "opportunity-finding", state: "opportunity-missing-day-limited", app: `${S}/opportunities/${MISSING}` }] : []),
  { screen: "sitework-incidents", state: "incidents-linked-stocked", app: `${S}/work/incidents?${WORK_WINDOW}`, overlay: true },
  { screen: "sitework-incidents", state: "incidents-refused-overlay", app: `${S}/work/incidents?${WORK_WINDOW}`, overlay: true,
    rule: { fail503: "/work/decision-contexts?" } },
  { screen: "sitework-maintenance", state: "maintenance-unlinked-stocked", app: `${S}/work/maintenance?${WORK_WINDOW}`, overlay: true },
];
const UNPROVED = [
  { state: "opportunity-supported-current", reason: "After replay the late variant's fixed 13 October receipt is visible at every cutoff (PR-11.2), so no read of the study returns SUPPORTED with CURRENT; see PR-12." },
  ...(MISSING ? [] : [{ state: "opportunity-missing-day-limited", reason: "replay.json has no 8 October study row." }]),
  { state: "alternatives-stocked", reason: "Not an exit gate while the resolved F02 revision is future dated (u9); positive rows are component/API tests." },
];

// ---- CDP ----
const PORT = 9763;
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe",
  ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`,
   `--user-data-dir=${mkdtempSync(join(tmpdir(), "w403cap-"))}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let url = null;
for (let i = 0; i < 80 && !url; i++) {
  try { url = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page")?.webSocketDebuggerUrl; } catch {}
  if (!url) await sleep(250);
}
const ws = new WebSocket(url);
await new Promise((r) => ws.addEventListener("open", r));
let n = 0; const pending = new Map();
let rule = null; const ruleHits = [];
const send = (method, params = {}) => new Promise((res, rej) => { const id = ++n; pending.set(id, (m) => m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result)); ws.send(JSON.stringify({ id, method, params })); });
ws.addEventListener("message", (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); return; }
  if (m.method !== "Fetch.requestPaused") return;
  const { requestId, request } = m.params;
  const u = new URL(request.url);
  if (rule?.fail503 && (u.pathname + u.search).includes(rule.fail503)) {
    ruleHits.push(`503 ${u.pathname}${u.search}`);
    const body = Buffer.from(JSON.stringify({ detail: { code: "SERVICE_UNAVAILABLE", message: "Capture harness: scoped 503." } })).toString("base64");
    send("Fetch.fulfillRequest", { requestId, responseCode: 503, responseHeaders: [{ name: "Content-Type", value: "application/json" }], body }).catch(() => {});
  } else if (rule?.knownAt && u.pathname === rule.knownAt.path && !u.searchParams.has("known_at")) {
    u.searchParams.set("known_at", rule.knownAt.value);
    ruleHits.push(`known_at ${u.pathname}${u.search}`);
    send("Fetch.continueRequest", { requestId, url: u.toString() }).catch(() => {});
  } else send("Fetch.continueRequest", { requestId }).catch(() => {});
});
const evalv = async (expression) => (await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true })).result.value;
await send("Page.enable"); await send("Runtime.enable");
await send("Fetch.enable", { patterns: [{ urlPattern: "*/api/*", requestStage: "Request" }] });

const MEASURE = (screen, side) => `(async () => {
  await document.fonts.ready;
  const pieces = ${JSON.stringify(PIECES[screen])};
  const side = ${JSON.stringify(side)};
  const main = document.querySelector("main") || document.body;
  const R = (e) => { if (!e) return null; const b = e.getBoundingClientRect(); return { y: Math.round(b.top + scrollY), w: Math.round(b.width), h: Math.round(b.height) }; };
  const own = (p) => Array.from(p.querySelectorAll("h2")).find((h) => h.closest("section.panel") === p);
  const panels = Array.from(main.querySelectorAll("section.panel")).filter((p) => !p.parentElement.closest("section.panel"));
  const titled = (t) => panels.find((p) => own(p)?.textContent.trim() === t) || null;
  const out = {};
  for (const [name, app, mock] of pieces) out[name] = R(app ? main.querySelector(side === "app" ? app : mock) : titled(name));
  const extra = {};
  const scroller = (p) => p && p.querySelector(".data-table__scroll, .table-wrap");
  const firstTitled = panels[0] || null;
  const sc = scroller(firstTitled);
  const table = firstTitled && firstTitled.querySelector("table");
  if (sc) extra.tableScroll = { client: sc.clientWidth, scroll: sc.scrollWidth, clientH: sc.clientHeight, scrollH: sc.scrollHeight };
  if (table) {
    extra.tableW = Math.round(table.getBoundingClientRect().width);
    extra.cols = Array.from(table.querySelectorAll("thead th")).map((th) => th.textContent.trim() + ":" + Math.round(th.getBoundingClientRect().width));
    extra.rows = table.querySelectorAll("tbody tr").length;
    const first = table.querySelector("tbody tr > :first-child");
    if (sc && first && sc.scrollWidth > sc.clientWidth) {
      const before = first.getBoundingClientRect().left; sc.scrollLeft = 200; await new Promise((r) => setTimeout(r, 60));
      extra.stickyFirst = Math.round(first.getBoundingClientRect().left - before) === 0; sc.scrollLeft = 0;
    }
  }
  const hint = main.querySelector(".work-cases-scroll-hint");
  if (hint) extra.hintVisible = getComputedStyle(hint).display !== "none";
  extra.cardCount = main.querySelectorAll("[data-opportunity-cards] > li, .cards > .card, .cards > *").length;
  extra.contexts = Array.from(main.querySelectorAll("[data-work-decision-context]")).map((e) => e.textContent.replace(/\\s+/g, " ").trim());
  extra.workRows = main.querySelectorAll("[data-work-row]").length;
  extra.chip = main.querySelector("[data-opportunity-chip]")?.textContent.trim() ?? null;
  return { pieces: out, extra,
    panelOrder: panels.map((p) => own(p)?.textContent.trim() ?? "(untitled)"),
    text: main.textContent.replace(/\\s+/g, " ").trim().slice(0, 600),
    doc: { scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth },
    pageH: document.documentElement.scrollHeight };
})()`;

async function shoot(target, screen, side, w, h, file, ready) {
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: false });
  await send("Page.navigate", { url: target });
  let ok = false;
  for (let i = 0; i < 300 && !ok; i++) { await sleep(150); ok = await evalv(ready).catch(() => false); }
  await sleep(500);
  const m = await evalv(MEASURE(screen, side));
  m.ready = ok;
  if (side === "app" && screen === "opportunity-finding") {
    m.extra.drawer = await evalv(`(async () => { const b = Array.from(document.querySelectorAll("main button")).find((x) => x.textContent.trim() === "Inspect opportunity evidence");
      if (!b) return null; b.click(); await new Promise((r) => setTimeout(r, 300));
      const d = document.querySelector("[data-opportunity-evidence]"); if (!d) return null; const r = d.getBoundingClientRect();
      const out = { h: Math.round(r.height), scrollH: d.scrollHeight, overflowY: getComputedStyle(d).overflowY }; b.click(); await new Promise((r) => setTimeout(r, 200)); return out; })()`);
  }
  const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width: w, height: Math.min(m.pageH, 6000), scale: 1 } });
  writeFileSync(join(OUT, file), Buffer.from(shot.data, "base64"));
  m.image = join(OUT, file);
  return m;
}

const results = { web: WEB, captured_at: new Date().toISOString(), replay: join(WORK, "replay.json"), stock: join(resolve(OUT), "stock.json"),
  ids: { finding: FINDING, finding_revision: FREV, opportunity: OPP, missing_opportunity: MISSING, k_before_late: replay.k_before_late, work_window: WORK_WINDOW },
  mock: {}, app: [], checks: [], unproved: UNPROVED };
const fail = [];
for (const screen of Object.keys(PIECES)) for (const [w, h] of SIZES) {
  rule = null;
  results.mock[`${screen}-${w}`] = await shoot(`${MOCK}#/${screen}`, screen, "mock", w, h, `${screen}-${w}-mock.png`, `document.querySelectorAll("main section.panel").length > 0`);
}
const READY = `(() => { const m = document.querySelector("main"); if (!m) return false; if (/Loading the /.test(m.textContent)) return false;
  return !!m.querySelector("section.panel"); })()`;
for (const c of CASES) for (const [w, h] of SIZES) {
  rule = c.rule ?? null; ruleHits.length = 0;
  const m = await shoot(`${WEB}${c.app}`, c.screen, "app", w, h, `${c.state}-${w}-app.png`,
    c.overlay && c.state !== "maintenance-unlinked-stocked" ? `(() => { const ok = ${READY}; return ok && document.querySelectorAll("[data-work-decision-context]").length > 0; })()` : READY);
  const mock = results.mock[`${c.screen}-${w}`];
  const row = { ...c, width: w, route: c.app, harness: [...ruleHits], ...m };
  results.app.push(row);
  const check = (ok, what) => { results.checks.push({ case: `${c.state} ${w}`, what, ok: !!ok }); if (!ok) fail.push(`${c.state} ${w}: ${what}`); };
  check(m.ready, "screen settled (panel rendered, no loading copy)");
  if (c.rule) check(ruleHits.length > 0, `harness rule applied (${ruleHits.join("; ") || "none"})`);
  check(JSON.stringify(m.panelOrder) === JSON.stringify(mock.panelOrder), `panel order ${JSON.stringify(m.panelOrder)} = mock ${JSON.stringify(mock.panelOrder)}`);
  for (const [name] of PIECES[c.screen]) {
    const a = m.pieces[name], k = mock.pieces[name], cap = CAPS[c.screen][w][name];
    check(!!a, `${name} present (mock ${k ? `${k.w}x${k.h}` : "absent"})`);
    if (a && cap !== undefined) check(a.h <= cap, `${name} height ${a.h} <= ${cap} (mock ${k?.h ?? "-"})`);
    if (a && (name === "panel" || !["status", "cards", "notice"].includes(name))) check(a.w <= MAX_W[w], `${name} width ${a.w} <= ${MAX_W[w]}`);
  }
  check(m.doc.scrollW <= m.doc.clientW, `document scrollWidth ${m.doc.scrollW} <= clientWidth ${m.doc.clientW}`);
  if (c.screen === "opportunity-finding") {
    check(m.extra.cardCount === 4, `four cards (${m.extra.cardCount})`);
    if (m.extra.drawer) check(m.extra.drawer.h <= 96, `evidence list ${m.extra.drawer.h} <= 96 (scrollH ${m.extra.drawer.scrollH}, ${m.extra.drawer.overflowY})`);
  }
  if (c.state === "scenarios-populated" && w === 390) {
    check(m.extra.tableW >= 720, `Scenarios grid min-width 720 (${m.extra.tableW})`);
    check(m.extra.tableScroll && m.extra.tableScroll.scroll > m.extra.tableScroll.client, `Scenarios grid scrolls inside its panel (${JSON.stringify(m.extra.tableScroll)})`);
  }
  if (c.screen.startsWith("sitework")) {
    const want = c.screen === "sitework-incidents" ? 1 + Object.keys(stock.incidents).length : 1 + Object.keys(stock.requests).length;
    const shown = Math.min(want, 5);
    check(m.extra.workRows === shown, `work rows ${m.extra.workRows} = ${shown} (fixture 1 + stock ${want - 1})`);
    if (w === 390) {
      check(m.extra.tableScroll && m.extra.tableScroll.scroll > m.extra.tableScroll.client, `Work table scrolls in its panel (${JSON.stringify(m.extra.tableScroll)})`);
      check(m.extra.stickyFirst === true, "first column sticky while scrolling");
      check(m.extra.hintVisible === true, "scroll hint visible");
    }
  }
  if (c.state === "incidents-linked-stocked") check(m.extra.contexts.some((t) => t.startsWith("Decision context: OPP-")), `linked Opportunity context shown (${JSON.stringify(m.extra.contexts)})`);
  if (c.state === "incidents-refused-overlay") {
    check(m.extra.contexts.length === m.extra.workRows && m.extra.contexts.every((t) => t === "Decision context unavailable"),
      `refused overlay: literal copy on every row, no prefix (${JSON.stringify(m.extra.contexts)})`);
  }
  if (c.state === "maintenance-unlinked-stocked") check(m.extra.contexts.length === 0, `no context on unlinked requests (${JSON.stringify(m.extra.contexts)})`);
}
writeFileSync(join(OUT, "evidence.json"), JSON.stringify(results, null, 1));
for (const r of results.app) console.log(`${r.state} ${r.width}: ${Object.entries(r.pieces).map(([k, v]) => `${k} ${v ? `${v.w}x${v.h}` : "-"}`).join(" | ")} | doc ${r.doc.scrollW}/${r.doc.clientW}${r.harness.length ? " | harness " + r.harness.length : ""}`);
for (const [k, m] of Object.entries(results.mock)) console.log(`mock ${k}: ${Object.entries(m.pieces).map(([p, v]) => `${p} ${v ? `${v.w}x${v.h}` : "-"}`).join(" | ")} | order ${JSON.stringify(m.panelOrder)}`);
console.log(fail.length ? `w403 capture checks FAILED (${fail.length}/${results.checks.length}):\n  ${fail.join("\n  ")}` : `w403 capture checks passed (${results.checks.length})`);
for (const u of UNPROVED) console.log(`unproved: ${u.state}: ${u.reason}`);
ws.close(); chrome.kill(); process.exit(fail.length ? 1 : 0);
