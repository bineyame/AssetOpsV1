/* W4-03 unit 9b: app vs v69 mock captures at 1440 and 390 for the three W4-03 screens and both Site Work screens.
   `.agent/W4-03-build-spec.md` "Unit-9 rulings (u9)": capture matrix, inclusive height caps and width limits.
   Usage (through the walkthrough tool, which seeds the capture stock first):
     python tools/w403_mini_decisions_walkthrough.py --db <x_test> --work var/<dir> capture --web http://localhost:6147
   or directly: node tools/w403-mini-decisions-evidence.mjs <web> <work>/capture [positive|late]
   u9b PR-12.5: phase `positive` runs after `replay-positive` (reads `<work>/positive.json`, writes
   `evidence-positive.json`); phase `late` (default) runs after `replay-late` (reads `<work>/replay.json`, merges the
   positive checks and writes `evidence.json`). Both read `<work>/capture/stock.json` and write `<state>-<width>-app.png`
   and `<screen>-<width>-mock.png`. Every request is served by the real walkthrough backend except one named harness
   rule, a scoped 503 (`fail503`), whose exact hit is asserted. PR-12.6: the historical cutoff is the explicit
   `?known_at=` detail address; no request is rewritten. App and mock use the same emulation (`mobile:false`). */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { widthGuard } from "./evidence-checks.mjs";

const [, , WEB = "http://localhost:6147", OUT, PHASE = "late"] = process.argv;
if (!["positive", "late"].includes(PHASE)) { console.error(`unknown phase ${PHASE}`); process.exit(2); }
if (!OUT) { console.error("usage: node tools/w403-mini-decisions-evidence.mjs <web> <work>/capture"); process.exit(2); }
const REPO = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const MOCK = pathToFileURL(join(REPO, "frontend/mockups/v69/index.html")).href;
const WORK = dirname(resolve(OUT));
const replay = JSON.parse(readFileSync(join(WORK, PHASE === "positive" ? "positive.json" : "replay.json"), "utf-8"));
const stock = JSON.parse(readFileSync(join(resolve(OUT), "stock.json"), "utf-8"));
mkdirSync(OUT, { recursive: true });

const MG = "MG-W402-001";
const KOBO = "KOBO-001";
const [FINDING, FREV] = replay.finding;
const OPP = replay.writes.opportunity_id;
const MISSING = PHASE === "positive" ? null : replay.missing.rows.find((r) => r.opportunity.first_day === "2026-10-08")?.opportunity.id ?? null;
const OLD_HEAD = replay.positive_selection?.revision_id ?? null;
const SCENARIO_ROWS = replay.positive?.scenarios?.rows?.length ?? null;
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
const K = replay.k_before_late ?? null;
const POSITIVE_CASES = [
  { screen: "opportunity-finding", state: "opportunity-supported-current", app: `${S}/opportunities/${OPP}`, positive: true },
];
const LATE_CASES = [
  { screen: "scenarios", state: "scenarios-populated", app: `${S}/financials/scenarios` },
  { screen: "scenarios", state: "scenarios-empty", app: `${S}/financials/scenarios?from=1970-01-01T00:00:00.000000Z&to=2026-10-01T00:00:00.000000Z` },
  { screen: "scenarios", state: "scenarios-refused", app: `${S}/financials/scenarios?from=2026-10-21T00:00:00.000000Z&to=2026-10-01T00:00:00.000000Z` },
  { screen: "alternatives", state: "alternatives-db-time", app: `/sites/${KOBO}/findings/${FINDING}/alternatives?revision_id=${FREV}` },
  { screen: "alternatives", state: "alternatives-read-503", app: `/sites/${KOBO}/findings/${FINDING}/alternatives?revision_id=${FREV}`,
    rule: { fail503: `/api/sites/${KOBO}/findings/${FINDING}/alternatives?` } },
  { screen: "opportunity-finding", state: "opportunity-current-late-settled", app: `${S}/opportunities/${OPP}` },
  { screen: "opportunity-finding", state: "opportunity-late-stale-k-before-late",
    app: `${S}/opportunities/${OPP}?${new URLSearchParams({ known_at: K ?? "" })}`, cutoff: K },
  ...(MISSING ? [{ screen: "opportunity-finding", state: "opportunity-missing-day-limited", app: `${S}/opportunities/${MISSING}` }] : []),
  { screen: "sitework-incidents", state: "incidents-linked-stocked", app: `${S}/work/incidents?${WORK_WINDOW}`, overlay: true },
  { screen: "sitework-incidents", state: "incidents-refused-overlay", app: `${S}/work/incidents?${WORK_WINDOW}`, overlay: true,
    rule: { fail503: "/work/decision-contexts?" } },
  { screen: "sitework-maintenance", state: "maintenance-unlinked-stocked", app: `${S}/work/maintenance?${WORK_WINDOW}`, overlay: true },
];
const CASES = PHASE === "positive" ? POSITIVE_CASES : LATE_CASES;
const POSITIVE_FILE = join(resolve(OUT), "evidence-positive.json");
const positiveRun = PHASE === "late" ? (() => { try { return JSON.parse(readFileSync(POSITIVE_FILE, "utf-8")); } catch { return null; } })() : null;
const UNPROVED = PHASE === "positive" ? [] : [
  ...(positiveRun ? [] : [{ state: "opportunity-supported-current", reason: "No evidence-positive.json: capture --phase positive did not run before replay-late (PR-12.5)." }]),
  ...(MISSING ? [] : [{ state: "opportunity-missing-day-limited", reason: "replay.json has no 8 October study row." }]),
  { state: "alternatives-stocked", reason: "Not an exit gate while the resolved F02 revision is future dated (u9, PR-12.4); positive rows are component/API tests." },
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
let rule = null; const ruleHits = []; const apiLog = [];
const send = (method, params = {}) => new Promise((res, rej) => { const id = ++n; pending.set(id, (m) => m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result)); ws.send(JSON.stringify({ id, method, params })); });
ws.addEventListener("message", (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); return; }
  if (m.method === "Network.responseReceived") {
    const r = m.params.response; const u = new URL(r.url);
    if (u.pathname.startsWith("/api/")) apiLog.push({ path: u.pathname + u.search, status: r.status, at: apiLog.length });
    return;
  }
  if (m.method !== "Fetch.requestPaused") return;
  const { requestId, request } = m.params;
  const u = new URL(request.url);
  if (rule?.fail503 && (u.pathname + u.search).includes(rule.fail503)) {
    ruleHits.push(`503 ${u.pathname}${u.search} after ${JSON.stringify(apiLog.map((e) => `${e.status} ${e.path}`))}`);
    const body = Buffer.from(JSON.stringify({ detail: { code: "SERVICE_UNAVAILABLE", message: "Capture harness: scoped 503." } })).toString("base64");
    send("Fetch.fulfillRequest", { requestId, responseCode: 503, responseHeaders: [{ name: "Content-Type", value: "application/json" }], body }).catch(() => {});
  } else send("Fetch.continueRequest", { requestId }).catch(() => {});
});
const evalv = async (expression) => (await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true })).result.value;
await send("Page.enable"); await send("Runtime.enable"); await send("Network.enable");
await send("Fetch.enable", { patterns: [{ urlPattern: "*/api/*", requestStage: "Request" }] });
const widthClaims = [];
const requireWidth = widthGuard({ send, claim: (name, ok, detail) => widthClaims.push({ name, ok, ...detail }) });

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
  extra.rowContexts = main.querySelectorAll("table [data-work-decision-context]").length;
  extra.panelContexts = Array.from(main.querySelectorAll("[data-work-decision-context]")).filter((e) => !e.closest("table")).map((e) => e.textContent.trim());
  extra.findingLinks = main.querySelectorAll("table [data-work-finding-link]").length;
  extra.chipTone = main.querySelector("[data-opportunity-chip]")?.getAttribute("data-opportunity-chip") ?? null;
  extra.currentness = main.querySelector("[data-opportunity-currentness]")?.textContent.trim() ?? null;
  extra.refusal = main.querySelector("[data-opportunity-refusal]")?.getAttribute("data-opportunity-refusal") ?? null;
  extra.location = location.pathname + location.search;
  extra.scenarioNotice = main.querySelector("[data-scenarios-notice]")?.textContent.trim() ?? null;
  extra.scenarioRows = main.querySelectorAll("[data-scenario-row]").length;
  extra.alternativeRows = main.querySelectorAll("[data-alternative-row]").length;
  if (sc) { const cs = getComputedStyle(sc); extra.scrollBox = { maxHeight: cs.maxHeight, overflowY: cs.overflowY }; }
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
  await requireWidth(w, h, `resize ${file}`, { record: false });
  await send("Page.navigate", { url: target });
  await requireWidth(w, h, `navigate ${file}`, { record: false });
  let ok = false;
  for (let i = 0; i < 300 && !ok; i++) { await sleep(150); ok = await evalv(ready).catch(() => false); }
  await sleep(500);
  await requireWidth(w, h, `measure ${file}`);
  const m = await evalv(MEASURE(screen, side));
  m.ready = ok;
  if (side === "app" && screen === "scenarios") {
    m.extra.disclosure = await evalv(`(async () => { const b = document.querySelector("[data-scenario-inspect]"); if (!b) return null;
      const region = document.getElementById("mini-scenarios-pinned"); const closedH = region.getBoundingClientRect().height;
      b.click(); await new Promise((r) => setTimeout(r, 200)); const r = region.getBoundingClientRect();
      const out = { closedH: Math.round(closedH), h: Math.round(r.height), scrollH: region.scrollHeight, ids: Array.from(region.querySelectorAll("code"), (c) => c.textContent),
        expanded: b.getAttribute("aria-expanded"), inTable: !!region.closest("table"), tabIndex: region.tabIndex };
      b.click(); await new Promise((r) => setTimeout(r, 150)); return out; })()`);
  }
  if (side === "app" && screen === "opportunity-finding") {
    // The detail wire as this address reads it (same cutoff), for status/currentness/revision/link checks.
    m.extra.wire = await evalv(`(async () => { const parts = location.pathname.split("/"); const q = new URLSearchParams(location.search);
      const api = "/api/sites/" + parts[2] + "/opportunities/" + parts[4] + (q.has("known_at") ? "?" + new URLSearchParams(q.getAll("known_at").map((k) => ["known_at", k])) : "");
      const r = await fetch(api); const b = await r.json().catch(() => null);
      return { api, status: r.status, body: b && { status: b.status, currentness: b.currentness?.state, revision_id: b.opportunity?.revision_id ?? null,
        renewable: b.links?.renewable ?? null, days: (b.opportunity?.day_rows ?? []).map((d) => [d.local_day, d.selection_seq, d.mini_revision_id]) } }; })()`);

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

const results = { web: WEB, phase: PHASE, captured_at: new Date().toISOString(), replay: join(WORK, PHASE === "positive" ? "positive.json" : "replay.json"), stock: join(resolve(OUT), "stock.json"),
  ids: { finding: FINDING, finding_revision: FREV, opportunity: OPP, old_head: OLD_HEAD, missing_opportunity: MISSING, k_before_late: K, work_window: WORK_WINDOW },
  kobo_reads: replay.kobo_reads ?? null, performance_exits: replay.performance_exits ?? null,
  mock: {}, app: [], checks: [], unproved: UNPROVED };
const fail = [];
for (const screen of [...new Set(CASES.map((c) => c.screen))]) for (const [w, h] of SIZES) {
  rule = null;
  results.mock[`${screen}-${w}`] = await shoot(`${MOCK}#/${screen}`, screen, "mock", w, h, `${screen}-${w}-mock.png`, `document.querySelectorAll("main section.panel").length > 0`);
}
const READY = `(() => { const m = document.querySelector("main"); if (!m) return false; if (/Loading the /.test(m.textContent)) return false;
  return !!m.querySelector("section.panel"); })()`;
for (const c of CASES) for (const [w, h] of SIZES) {
  rule = c.rule ?? null; ruleHits.length = 0; apiLog.length = 0;
  const m = await shoot(`${WEB}${c.app}`, c.screen, "app", w, h, `${c.state}-${w}-app.png`,
    c.overlay && c.state !== "maintenance-unlinked-stocked" ? `(() => { const ok = ${READY}; return ok && document.querySelectorAll("[data-work-decision-context]").length > 0; })()` : READY);
  const mock = results.mock[`${c.screen}-${w}`];
  const row = { ...c, width: w, route: c.app, harness: [...ruleHits], api: apiLog.map((e) => `${e.status} ${e.path}`), ...m };
  results.app.push(row);
  const check = (ok, what) => { results.checks.push({ case: `${c.state} ${w}`, what, ok: !!ok }); if (!ok) fail.push(`${c.state} ${w}: ${what}`); };
  check(m.ready, "screen settled (panel rendered, no loading copy)");
  if (c.rule) check(ruleHits.length > 0, `harness rule applied (${ruleHits.join("; ") || "none"})`);
  const got = (pred) => apiLog.filter((e) => pred(new URL(e.path, "http://x")));
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
    const detailGets = got((u) => u.pathname === `/api/sites/${MG}/opportunities/${c.app.split("/")[4].split("?")[0]}`);
    if (c.positive) {
      const b = m.extra.wire?.body;
      check(b && b.status === "SUPPORTED" && b.currentness === "CURRENT", `status SUPPORTED, currentness CURRENT (${JSON.stringify(b && [b.status, b.currentness])})`);
      check(m.extra.chipTone === "green", `positive chip (${m.extra.chipTone} ${m.extra.chip})`);
      const pins = replay.pins.map((p) => [p.local_day, p.selection_seq, p.mini_revision_id]);
      check(b && JSON.stringify(b.days) === JSON.stringify(pins), `selected five-day rows = pins (${b?.days.length})`);
      check(detailGets.length > 0 && detailGets.every((e) => !new URL(e.path, "http://x").searchParams.has("known_at")), `current detail GET without cutoff (${JSON.stringify(detailGets)})`);
    }
    if (c.cutoff) {
      const b = m.extra.wire?.body;
      check(new URLSearchParams(m.extra.location.split("?")[1] ?? "").get("known_at") === c.cutoff, `browser URL carries the cutoff (${m.extra.location})`);
      check(detailGets.length > 0 && detailGets.every((e) => new URL(e.path, "http://x").searchParams.getAll("known_at").join() === c.cutoff), `intercepted detail GET carries the cutoff (${JSON.stringify(detailGets)})`);
      check(b && typeof b.renewable === "string" && new URLSearchParams(b.renewable.split("?")[1]).get("known_at") === c.cutoff, `links.renewable carries the same known_at (${b?.renewable})`);
      check(b && OLD_HEAD && b.revision_id === OLD_HEAD, `selected revision is the old head (${b?.revision_id} = ${OLD_HEAD})`);
      check(m.extra.chipTone !== "green" && !(b && b.status === "SUPPORTED" && b.currentness === "CURRENT"), `historical cutoff is not current/supported (${m.extra.chipTone}; ${JSON.stringify(b && [b.status, b.currentness])})`);
    }
  }
  if (c.screen === "scenarios") check(m.extra.scenarioNotice === "Scenarios never change measured results or the consequence lines on Overview. They are labelled what-ifs, kept separate from evidence.", "Scenarios notice unchanged");
  if (c.state === "scenarios-populated") {
    check(SCENARIO_ROWS !== null && m.extra.scenarioRows === SCENARIO_ROWS, `scenario rows ${m.extra.scenarioRows} = read ${SCENARIO_ROWS}`);
    check(m.extra.scrollBox && m.extra.scrollBox.maxHeight === "252px" && m.extra.scrollBox.overflowY === "auto", `Scenarios table inner vertical scroll box (${JSON.stringify(m.extra.scrollBox)}, ${JSON.stringify(m.extra.tableScroll)})`);
    const d = m.extra.disclosure;
    check(d && d.closedH === 0 && !d.inTable && d.expanded === "true" && d.h <= 96 && d.ids.length >= 1 && d.ids.every((x) => /^[0-9a-f-]{36}$/.test(x)),
      `pinned-revision disclosure: closed 0 px, outside the table, exact IDs in a bounded box (${JSON.stringify(d && { ...d, ids: d.ids.length })})`);
    if (w === 390) {
      check(m.extra.tableW >= 720, `Scenarios grid min-width 720 (${m.extra.tableW})`);
      check(m.extra.tableScroll && m.extra.tableScroll.scroll > m.extra.tableScroll.client, `Scenarios grid scrolls inside its panel (${JSON.stringify(m.extra.tableScroll)})`);
    }
  }
  if (c.state === "scenarios-empty") check(/No scenario defined yet/.test(m.text) && !/For example, a different stop setting|No authored what-if/.test(m.text) && /Scenario creation unavailable/.test(m.text), "empty block: mock sentence only, creation gap shown");
  if (c.screen === "alternatives") {
    const site = got((u) => u.pathname === `/api/sites/${KOBO}`), finding = got((u) => u.pathname === `/api/sites/${KOBO}/findings/${FINDING}`);
    check(site.some((e) => e.status === 200) && finding.some((e) => e.status === 200), `Site and Finding reads succeeded (${JSON.stringify(row.api)})`);
    check(m.extra.alternativeRows === 0, `no authored Alternative row (${m.extra.alternativeRows})`);
    if (c.state === "alternatives-read-503") {
      const alt = got((u) => u.pathname === `/api/sites/${KOBO}/findings/${FINDING}/alternatives`);
      check(alt.length > 0 && alt.every((e) => e.status === 503) && alt[0].at > Math.max(...site.map((e) => e.at), ...finding.map((e) => e.at)),
        `scoped 503 hit the exact Alternatives GET after the Site and Finding reads (${JSON.stringify(alt)})`);
      check(/Alternatives unavailable/.test(m.text), "Alternatives unavailable shown");
    }
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
    check(m.extra.rowContexts === 0 && JSON.stringify(m.extra.panelContexts) === JSON.stringify(["Decision context unavailable"]),
      `refused overlay: exactly one panel-level literal, no row-level copy (${JSON.stringify(m.extra.contexts)})`);
    check(!m.extra.contexts.some((t) => t.startsWith("Decision context:")), "refused overlay: no positive context");
  }
  if (c.screen === "sitework-incidents" && w === 390) {
    check(m.extra.tableScroll && m.extra.tableScroll.scrollH > m.extra.tableScroll.clientH, `Incident table scrolls vertically inside the panel (${JSON.stringify(m.extra.tableScroll)})`);
  }
  if (c.state === "maintenance-unlinked-stocked") check(m.extra.contexts.length === 0, `no context on unlinked requests (${JSON.stringify(m.extra.contexts)})`);
}
results.width_checks = widthClaims;
if (PHASE === "late" && positiveRun) {
  results.positive_phase = { file: POSITIVE_FILE, captured_at: positiveRun.captured_at, ids: positiveRun.ids };
  for (const k of Object.keys(positiveRun.mock)) results.mock[`positive:${k}`] = positiveRun.mock[k];
  results.app.unshift(...positiveRun.app);
  results.checks.unshift(...positiveRun.checks);
  results.width_checks.unshift(...positiveRun.width_checks);
  for (const ch of positiveRun.checks) if (!ch.ok) fail.push(`${ch.case}: ${ch.what} (positive phase)`);
}
writeFileSync(PHASE === "positive" ? POSITIVE_FILE : join(OUT, "evidence.json"), JSON.stringify(results, null, 1));
for (const r of results.app) console.log(`${r.state} ${r.width}: ${Object.entries(r.pieces).map(([k, v]) => `${k} ${v ? `${v.w}x${v.h}` : "-"}`).join(" | ")} | doc ${r.doc.scrollW}/${r.doc.clientW}${r.harness.length ? " | harness " + r.harness.length : ""}`);
for (const [k, m] of Object.entries(results.mock)) console.log(`mock ${k}: ${Object.entries(m.pieces).map(([p, v]) => `${p} ${v ? `${v.w}x${v.h}` : "-"}`).join(" | ")} | order ${JSON.stringify(m.panelOrder)}`);
console.log(fail.length ? `w403 capture checks FAILED (${fail.length}/${results.checks.length}):\n  ${fail.join("\n  ")}` : `w403 capture checks passed (${results.checks.length})`);
for (const u of UNPROVED) console.log(`unproved: ${u.state}: ${u.reason}`);
ws.close(); chrome.kill(); process.exit(fail.length ? 1 : 0);
