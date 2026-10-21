// W4-02 unit 7: app vs v69 mock at 1440 and 390 for renewable, service, fuel, backup and the mini Overview, through
// the real backend (uvicorn on w402p_test seeded by seed.py) and vite. Positive = authored positive days; gap =
// the missing/conflicting variant (12 Oct) and, for renewable, a window holding a missing day and the 12 Oct day.
// Budgets: `.agent/W4-02-build-spec.md` "Height and overflow acceptance" (Run 9 rulings). Mock reference:
// mock-measure.json from `node tools/measure-mock-panels.mjs`. Only the Chrome this script spawns is killed.
// Usage: node capture.mjs <out-dir> <revision> [app-base]
import { spawn } from "node:child_process";
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [, , OUT, REV, BASE = "http://localhost:6146"] = process.argv;
const PORT = 9749;
const S = "/sites/MG-W402-001";
const HOUR = (d) => `from=2026-10-${d}T09:00:00Z&to=2026-10-${d}T10:00:00Z`;
const CASES = [
  { screen: "renewable", state: "positive", app: `${S}/performance/renewable?from=2026-10-05T21:00:00Z&to=2026-10-10T21:00:00Z` },
  { screen: "renewable", state: "gap", app: `${S}/performance/renewable?from=2026-10-07T21:00:00Z&to=2026-10-12T21:00:00Z` },
  { screen: "service", state: "positive", app: `${S}/performance/service?${HOUR("06")}` },
  { screen: "service", state: "gap", app: `${S}/performance/service?${HOUR("12")}` },
  { screen: "fuel", state: "positive", app: `${S}/performance/fuel?${HOUR("06")}` },
  { screen: "fuel", state: "gap", app: `${S}/performance/fuel?${HOUR("12")}` },
  { screen: "backup", state: "positive", app: `${S}/performance/backup?${HOUR("06")}` },
  { screen: "backup", state: "gap", app: `${S}/performance/backup?${HOUR("12")}` },
  { screen: "mini", state: "positive", app: `${S}?date=2026-10-06` },
  { screen: "mini", state: "gap", app: `${S}?date=2026-10-12` },
  // Final review M3: a served Overview on an authored positive day (07-10 Oct) whose selected local noon hour is eligible.
  { screen: "mini", state: "numeric", app: `${S}?date=2026-10-08` },
];
// Final fix round (q14) ruled texts.
const MINIGRID_OBJECTIVE = "Objective: serve residential, clinic and productive loads while protecting the battery reserve. Check each card for the supported result and its limits.";
const NO_LEGACY_REASON = "No legacy evidence was imported for this Site. Dispatch has no assessed comparison for this selection.";
const PREPARED = "Prepared example data, not field readings";
const CRITICAL_RECORD = "Critical-service delivered power record";
const CLINIC = "Clinic feeder delivered power";
const HEADROOM = /^Headroom \d+(\.\d+)?–\d+(\.\d+)? kW$/;
const SIZES = [[1440, 1000], [390, 900]];
const BUDGET = {
  renewable: { 1440: [69, 137, 269, 269, 401, 66], 390: [138, 291, 300, 266, 482, 102] },
  service: { 1440: [68, 137, 264, 289, 201, 201], 390: [122, 291, 282, 326, 166, 201] },
  fuel: { 1440: [68, 153, 299, 366, 66, 173], 390: [95, 291, 316, 579, 102, 216] },
  backup: { 1440: [68, 137, 207, 316, 179, 179], 390: [122, 256, 292, 471, 201, 201] },
};
const PAGE_W = { 1440: 1425, 390: 390 };
// 390 table scroll minimums by region index (spec): renewable windows, service loads, backup chains + readiness.
const TABLE_MIN = { renewable: { 4: 379 }, service: { 3: 511 }, backup: { 2: 719, 3: 326 } };
const MOCK = Object.fromEntries(JSON.parse(readFileSync(join(OUT, "mock-measure.json"), "utf8")).map((m) => [`${m.screen}-${m.width}`, m]));
mkdirSync(OUT, { recursive: true });
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe",
  ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`,
   `--user-data-dir=${mkdtempSync(join(tmpdir(), "w402cap-"))}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let url = null;
for (let i = 0; i < 80 && !url; i++) {
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
  const R = (e) => { const b = e.getBoundingClientRect(); return { top: Math.round(b.top + scrollY), h: Math.round(b.height), w: Math.round(b.width) }; };
  const T = (e) => e.textContent.replace(/\\s+/g, " ").trim();
  const main = document.querySelector("main") || document.body;
  const items = [];
  for (const e of main.querySelectorAll(".status-strip, .v69-cards, section.panel, .v69-notice")) {
    if (e.parentElement.closest("section.panel, .v69-cards, .status-strip")) continue;
    const kind = e.matches(".status-strip") ? "statusbar" : e.matches(".v69-cards") ? "cards" : e.matches(".v69-notice") ? "notice" : "panel";
    const o = { kind, title: kind === "panel" ? e.querySelector("h2")?.textContent.trim() : kind === "cards"
      ? [...e.querySelectorAll(".v69-metric__label")].map(T).join(" | ") : T(e).slice(0, 200), ...R(e) };
    if (kind === "cards") { o.values = [...e.querySelectorAll(".v69-metric__value")].map(T); o.notes = [...e.querySelectorAll(".v69-metric__note")].map(T); }
    const t = e.querySelector("table");
    if (t) { const s = t.parentElement; o.table = { client: s.clientWidth, scroll: s.scrollWidth, rows: [...t.querySelectorAll("tbody tr")].map((r) => [...r.cells].map(T)) }; }
    items.push(o);
  }
  return { h1: document.querySelector("h1")?.textContent.trim(),
    items, links: [...main.querySelectorAll("a[href]")].map((a) => T(a) + " -> " + a.getAttribute("href")),
    objective: [...main.querySelectorAll("[data-objective-card]")].map((c) => c.getAttribute("data-objective-card") + "|" + c.getAttribute("data-objective-card-state") + "|" + T(c).slice(0, 200)),
    docScrollW: document.documentElement.scrollWidth, overflowX: document.documentElement.scrollWidth - innerWidth,
    pageH: document.documentElement.scrollHeight };
})()`;

// Final fix round probes, taken on the fresh load (every disclosure closed).
const PROBE = `(() => {
  const main = document.querySelector("main") || document.body;
  const T = (e) => (e ? e.textContent.replace(/\\s+/g, " ").trim() : null);
  const p = { openDetails: main.querySelectorAll("details[open]").length };
  p.authored = /authored_demonstration/i.test(document.body.textContent);
  p.enums = [...new Set(document.body.textContent.match(/\\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\\b/g) || [])];
  p.prepared = document.body.innerText.includes(${JSON.stringify(PREPARED)});
  p.strip = T(main.querySelector(".v69-statusbar__other"));
  p.objective = T(main.querySelector("[data-objective-statement]"));
  p.refusal = T(main.querySelector("[data-overview-finding-refusal]"));
  p.closedCount = (main.innerText.match(/The Findings list is closed/g) || []).length;
  p.renewableValue = T(main.querySelector('[data-objective-card="renewable"] .v69-metric__value'));
  p.notes = [...main.querySelectorAll(".v69-metric__note")].map(T);
  p.clinic = [...main.querySelectorAll("td, th, span")].some((e) => T(e) === ${JSON.stringify(CLINIC)});
  p.buttons = [...main.querySelectorAll(".v69-claim-button")].map((b) => { const s = getComputedStyle(b);
    return { bw: s.borderTopWidth, bs: s.borderTopStyle, bg: s.backgroundColor, deco: s.textDecorationLine, text: T(b).slice(0, 40) }; });
  p.bars = [...main.querySelectorAll(".value-bars__value")].map(T);
  const panel = main.querySelector(".mini-max--backup-readiness");
  if (panel) {
    const box = (e) => { const b = e.getBoundingClientRect(); return { l: b.left + e.clientLeft, t: b.top + e.clientTop, r: b.left + e.clientLeft + e.clientWidth, b: b.top + e.clientTop + e.clientHeight }; };
    const clips = [panel];
    const rows = [...panel.querySelectorAll("tr[data-mini-readiness]")].map((r) => {
      const b = r.getBoundingClientRect(); const anc = [];
      for (let e = r.parentElement; e && e !== panel; e = e.parentElement) { const s = getComputedStyle(e); if (/(auto|scroll|hidden|clip)/.test(s.overflowX + s.overflowY)) anc.push(e); }
      const inside = [panel, ...anc].every((e) => { const c = box(e); return b.left >= c.l - 0.5 && b.right <= c.r + 0.5 && b.top >= c.t - 0.5 && b.bottom <= c.b + 0.5; });
      const scrolled = [panel, ...anc].some((e) => e.scrollTop !== 0 || e.scrollLeft !== 0);
      return { label: r.getAttribute("data-mini-readiness"), inside, scrolled, h: Math.round(b.height) };
    });
    p.readiness = { h: Math.round(panel.getBoundingClientRect().height), open: panel.querySelectorAll("details[open]").length, rows };
  }
  return p;
})()`;

async function shoot(target, w, h, file) {
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: w < 500 });
  await send("Page.navigate", { url: target });
  const ready = `!!document.querySelector("main section.panel, main [data-objective-card]") && !/Loading the site/.test(document.querySelector("main")?.textContent ?? "")`;
  for (let i = 0; i < 300; i++) { await sleep(150); if (await evalv(ready)) break; }
  await sleep(1500);
  const m = await evalv(MEASURE);
  m.probe = await evalv(PROBE);
  let opened = null;
  if (!file.startsWith("mini-")) {
    // q12-7: every disclosure and drawer opened; data stay reachable, regions stay within budget, no page overflow.
    await evalv(`(() => { document.querySelectorAll("main details").forEach((d) => { d.open = true; }); document.querySelectorAll("main [data-mini-drawer-open]").forEach((b) => b.getAttribute("aria-expanded") === "true" || b.click()); })()`);
    await sleep(400);
    opened = await evalv(MEASURE);
    opened.disclosures = await evalv(`document.querySelectorAll("main details[open], main [data-mini-drawer]").length`);
    await send("Page.reload"); 
    for (let i = 0; i < 300; i++) { await sleep(150); if (await evalv(ready)) break; }
    await sleep(1200);
  }
  const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width: w, height: Math.min(m.pageH, 6000), scale: 1 } });
  writeFileSync(join(OUT, file), Buffer.from(shot.data, "base64"));
  m.opened = opened;
  return m;
}

const results = { revision: REV, captured_at: new Date().toISOString(), app: [], checks: [] };
const fail = [];
const totals = { buttons: 0, unknownBars: 0 };
const ONLY = process.env.ONLY ? process.env.ONLY.split(",") : null;
for (const c of CASES.filter((x) => ONLY === null || ONLY.includes(x.screen))) for (const [w, h] of SIZES) {
  const m = await shoot(`${BASE}${c.app}`, w, h, `${c.screen}-${c.state}-${w}-app.png`);
  const row = { ...c, width: w, ...m };
  results.app.push(row);
  const check = (ok, what) => { results.checks.push({ case: `${c.screen} ${c.state} ${w}`, what, ok }); if (!ok) fail.push(`${c.screen} ${c.state} ${w}: ${what}`); };
  check(m.overflowX <= 0 && m.docScrollW <= PAGE_W[w], `no page horizontal overflow (scrollW ${m.docScrollW} <= ${PAGE_W[w]})`);
  if (m.opened) {
    check(m.opened.overflowX <= 0 && m.opened.docScrollW <= PAGE_W[w], `opened (${m.opened.disclosures} disclosures/drawers): no page horizontal overflow (scrollW ${m.opened.docScrollW})`);
    check(m.opened.items.length === m.items.length, `opened: ${m.opened.items.length} regions = ${m.items.length}`);
  }
  // Final fix round assertions (q14 rulings), on the fresh load.
  const p = m.probe;
  check(!p.authored, "H2: no authored_demonstration text");
  check(p.enums.length === 0, `H2: no raw enum text (${p.enums.join(",") || "none"})`);
  if (c.screen === "mini") {
    check(p.strip?.startsWith("Reads on this Overview:") === true, `H3: strip starts "Reads on this Overview:" ("${(p.strip ?? "").slice(0, 60)}")`);
    check(p.objective === MINIGRID_OBJECTIVE, `H3: mini-grid objective ("${(p.objective ?? "").slice(0, 60)}")`);
    check(p.refusal === NO_LEGACY_REASON, `M4: Needs-attention reason exact ("${p.refusal}")`);
    check(p.closedCount <= 1, `M4: "The Findings list is closed" at most once (${p.closedCount})`);
    if (c.state === "numeric") check(HEADROOM.test(p.renewableValue ?? ""), `M3: served Renewable card value "${p.renewableValue}" matches Headroom low–high kW`);
  } else {
    check(p.prepared, `H2: shows "${PREPARED}"`);
    check(p.bars.every((b) => !/not known/i.test(b)), `L1: hatched bars say Unknown (${p.bars.filter((b) => /unknown/i.test(b)).length} Unknown, 0 "not known")`);
    for (const b of p.buttons) check((b.bs === "none" || b.bw === "0px") && b.bg === "rgba(0, 0, 0, 0)", `M1: claim button "${b.text}" link styling (border ${b.bw} ${b.bs}, bg ${b.bg})`);
  }
  if (c.screen === "service") {
    check(p.notes.some((t) => t.startsWith(CRITICAL_RECORD)), `M2: critical card note starts "${CRITICAL_RECORD}" (${p.notes.find((t) => t.includes("Critical")) ?? "none"})`);
    check(p.clinic, `M2: clinic row says "${CLINIC}"`);
  }
  if (c.screen === "backup" && w === 1440) {
    const r = p.readiness;
    check(r !== undefined && p.openDetails === 0 && r.open === 0, "H4: readiness panel present with every detail closed");
    check(r !== undefined && r.h <= 316, `H4: closed readiness panel h ${r?.h} <= 316`);
    check(r !== undefined && r.rows.length === 4 && r.rows.every((x) => x.inside && !x.scrolled), `H4: all four readiness rows visible inside the closed panel without scrolling (${r?.rows.map((x) => x.label + ":" + (x.inside && !x.scrolled)).join(", ")})`);
    check(r?.rows.find((x) => x.label === "Witnessed outcome")?.inside === true, 'H4: "Witnessed outcome" row ("Readiness remains unverified") fully visible');
  }
  totals.buttons += p.buttons.length; totals.unknownBars += p.bars.filter((b) => b === "Unknown").length;
  if (c.screen === "mini") {
    const keys = m.objective.map((x) => x.split("|")[0]);
    check(JSON.stringify(keys) === JSON.stringify(["service", "dispatch", "battery", "fuel", "renewable"]), `five Overview cards in order (${keys.join(",")})`);
    row.mockCardsH = MOCK[`mini-${w}`]?.items.find((i) => i.kind === "cards")?.h ?? null;
    continue;
  }
  const budget = BUDGET[c.screen][w];
  const mockItems = MOCK[`${c.screen}-${w}`].items.filter((i) => i.kind !== "block");
  check(m.items.length === budget.length, `${m.items.length} measured regions = ${budget.length} budgeted`);
  m.items.forEach((it, i) => {
    if (i >= budget.length) return;
    check(it.kind === mockItems[i]?.kind, `region ${i} kind ${it.kind} = mock ${mockItems[i]?.kind}`);
    check(it.h <= budget[i], `region ${i} ${it.kind} "${(it.title ?? "").slice(0, 40)}" h ${it.h} <= ${budget[i]}`);
    if (it.kind === "panel") check(it.title === mockItems[i]?.title, `panel ${i} title "${it.title}" = mock "${mockItems[i]?.title}"`);
    const o = m.opened?.items[i];
    if (o) check(o.h <= budget[i], `opened: region ${i} ${o.kind} h ${o.h} <= ${budget[i]}`);
    const min = w === 390 ? TABLE_MIN[c.screen]?.[i] : undefined;
    if (min !== undefined && it.table) check(it.table.scroll >= min, `region ${i} table scrolls internally (${it.table.scroll}/${it.table.client}, min ${min})`);
  });
}
if (ONLY === null) for (const [ok, what] of [[totals.buttons > 0, `M1: claim buttons seen (${totals.buttons})`], [totals.unknownBars > 0, `L1: Unknown hatched bars seen (${totals.unknownBars})`]]) {
  results.checks.push({ case: "all", what, ok }); if (!ok) fail.push(`all: ${what}`);
}
writeFileSync(join(OUT, "evidence.json"), JSON.stringify(results, null, 1));
for (const r of results.app) console.log(`${r.screen} ${r.state} ${r.width}: ${r.screen === "mini" ? "cards " + (r.items.find((i) => i.kind === "cards")?.h ?? "-") + " (mock " + r.mockCardsH + ")" : r.items.map((i) => i.h).join("/")} page ${r.pageH} scrollW ${r.docScrollW}`);
console.log(fail.length ? `W4-02 unit-7 capture checks FAILED (${fail.length}):\n  ${fail.join("\n  ")}` : `W4-02 unit-7 capture checks passed (${results.checks.length} checks)`);
ws.close(); chrome.kill(); process.exit(fail.length ? 1 : 0);
