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
];
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

async function shoot(target, w, h, file) {
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: w < 500 });
  await send("Page.navigate", { url: target });
  const ready = `!!document.querySelector("main section.panel, main [data-objective-card]") && !/Loading the site/.test(document.querySelector("main")?.textContent ?? "")`;
  for (let i = 0; i < 300; i++) { await sleep(150); if (await evalv(ready)) break; }
  await sleep(1500);
  const m = await evalv(MEASURE);
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
writeFileSync(join(OUT, "evidence.json"), JSON.stringify(results, null, 1));
for (const r of results.app) console.log(`${r.screen} ${r.state} ${r.width}: ${r.screen === "mini" ? "cards " + (r.items.find((i) => i.kind === "cards")?.h ?? "-") + " (mock " + r.mockCardsH + ")" : r.items.map((i) => i.h).join("/")} page ${r.pageH} scrollW ${r.docScrollW}`);
console.log(fail.length ? `W4-02 unit-7 capture checks FAILED (${fail.length}):\n  ${fail.join("\n  ")}` : `W4-02 unit-7 capture checks passed (${results.checks.length} checks)`);
ws.close(); chrome.kill(); process.exit(fail.length ? 1 : 0);
