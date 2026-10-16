/**
 * S3-02b focused layout, whole-day wording and keyboard evidence over CDP (Chrome installed here; no dependency).
 * Stands in for tools/layout-evidence.mjs, whose journeys need the registered Lab run store.
 *
 * Run against the walkthrough servers (tools/s302_claim_limit_walkthrough.py prepare + serve, plus the dev server):
 *   node tools/s302-claim-limit-evidence.mjs http://localhost:5442 var/s302_owner1 <screenshot-dir>
 * Prints every measurement as JSON and exits non-zero when a claim fails.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { widthGuard } from "./evidence-checks.mjs";

const [BASE, WORK, OUT] = process.argv.slice(2);
mkdirSync(OUT, { recursive: true });
const manifest = JSON.parse(readFileSync(join(WORK, "manifest.json"), "utf8"));
const C = manifest.cases;
const q = (day, rev) => `/sites/KOBO-001/evidence?view=analysis&day=${day}${rev ? `&revision=${rev}` : ""}`;
const links = [
  ["unassessed", "/sites/KOBO-001/evidence?view=analysis"],
  ["day-only", q(C["full-candidate"].day)],
  ["full", q(C["full-candidate"].day, C["full-candidate"].interval_revision_ids[0])],
  ["missing-pv", q(C["missing-pv"].day, C["missing-pv"].interval_revision_ids[0])],
  ["poor-conflict", q(C["poor-quality-conflict"].day, C["poor-quality-conflict"].interval_revision_ids[0])],
  ["historical", q(C["late-revision"].day, C["late-revision"].withdrawn.interval_revision_ids[0])],
  ["stale", q(C["stale-selection"].day, C["stale-selection"].interval_revision_ids[0])],
  ["window-current", q(C["full-candidate"].day, C["full-candidate"].window_revision_id)],
  ["window-historical", q(C["late-revision"].day, C["late-revision"].withdrawn.window_revision_id)],
  ["window-stale", q(C["stale-selection"].day, C["stale-selection"].window_revision_id)],
].filter(([, path]) => !path.includes("revision=null") && !path.includes("revision=undefined"));
let failed = 0;
const PORT = 9347;
const chrome = spawn("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`,
   `--user-data-dir=${mkdtempSync(join(tmpdir(), "s302-cdp-"))}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let wsUrl;
for (let i = 0; i < 60 && !wsUrl; i++) {
  try { wsUrl = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page")?.webSocketDebuggerUrl; } catch {}
  if (!wsUrl) await sleep(250);
}
const ws = new WebSocket(wsUrl);
await new Promise((r) => ws.addEventListener("open", r));
let id = 0; const pending = new Map();
ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pending.set(i, (m) => m.error ? rej(new Error(method + JSON.stringify(m.error))) : res(m.result)); ws.send(JSON.stringify({ id: i, method, params })); setTimeout(() => rej(new Error("timeout " + method)), 30000); });
const requireWidth = widthGuard({ send });
/** W1-UX-06 shared width check: a failure is counted and logged, and nothing is measured at that width. */
async function widthHolds(width, where) {
  try {
    const w = await requireWidth(width, 900, where);
    console.log(`PASS  ${where}: laid out at ${width}px (innerWidth ${w.innerWidth}, clientWidth ${w.clientWidth})`);
    return w;
  } catch (error) {
    failed++;
    console.error(`FAIL  ${error.message}`);
    return null;
  }
}
const ev = async (expression) => (await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true })).result.value;
async function settle() {
  for (let i = 0; i < 200; i++) {
    await sleep(150);
    const ok = await ev(`(() => { const s = document.querySelector('[data-claim-limit-section]'); return !!s && !/Loading /.test(document.body.textContent) && !!s.querySelector('[data-claim-limit-state]'); })()`);
    if (ok) return true;
  }
  return false;
}
const MEASURE = `(() => {
  const s = document.querySelector('[data-claim-limit-section]');
  const st = s?.querySelector('[data-claim-limit-state]');
  const r = s?.getBoundingClientRect();
  const over = [...(s?.querySelectorAll('*') ?? [])].filter((n) => { const b = n.getBoundingClientRect(); return b.width > 0 && b.right > window.innerWidth + 1 && !n.closest('.data-table__scroll'); }).length;
  const tbl = s?.querySelector('.data-table__scroll');
  return { innerWidth: window.innerWidth, docScrollWidth: document.documentElement.scrollWidth,
    pageScrollsSideways: document.documentElement.scrollWidth > window.innerWidth,
    sectionLeft: r && Math.round(r.left), sectionRight: r && Math.round(r.right), sectionHeight: r && Math.round(r.height),
    elementsPastViewport: over, state: st?.dataset.claimLimitState, currentness: st?.dataset.currentness ?? null,
    ceiling: st?.dataset.ceiling ?? null,
    wholeDay: st?.dataset.scope === "WINDOW" ? { scope: "WINDOW",
      coverageCells: [...(s?.querySelectorAll('tr[data-claim-role] td:nth-child(2)') ?? [])].map((n) => n.textContent),
      earlierIntro: s?.querySelector('[data-claim-limit-earlier-periods]')?.textContent ?? null,
      ownLevel: s?.querySelector('[data-claim-limit-window-level]')?.textContent ?? null,
      periodItems: [...(s?.querySelectorAll('[data-interval-ceiling]') ?? [])].map((n) => n.textContent) } : null, support: st?.dataset.support ?? null,
    headline: s?.querySelector('[data-claim-limit-headline]')?.textContent ?? null,
    roleRows: s?.querySelectorAll('tr[data-claim-role]').length ?? 0,
    acceptedLinks: s?.querySelectorAll('a[data-accepted-evidence]').length ?? 0,
    tableScrollWidth: tbl?.scrollWidth ?? null, tableClientWidth: tbl?.clientWidth ?? null,
    technicalOpen: s?.querySelector('[data-disclosure=claim-limit-technical]')?.open ?? null,
    s2Before: (() => { const a = document.querySelector('[data-evidence-claim-limit]'); return !!a && !!s && !!(a.compareDocumentPosition(s) & 4); })() };
})()`;
const results = {};
for (const [label, path] of links) {
  for (const width of [1440, 390]) {
    await send("Emulation.setDeviceMetricsOverride", { width, height: 900, deviceScaleFactor: 1, mobile: false });
    await send("Page.navigate", { url: BASE + path });
    const ok = await settle();
    const widthCheck = await widthHolds(width, `${label} @${width}`);
    if (widthCheck === null) { results[`${label} @${width}`] = { settled: ok, widthCheck: "failed; not measured" }; continue; }
    const m = await ev(MEASURE);
    results[`${label} @${width}`] = { settled: ok, widthCheck, ...m };
    if (!ok || m.pageScrollsSideways || m.elementsPastViewport > 0) { failed++; console.error(`FAIL layout ${label} @${width}`); }
    if (m.wholeDay) {
      const w = m.wholeDay;
      const good = w.coverageCells.length > 0 && w.coverageCells.every((c) => /\d+ min of \d+ min/.test(c) && !/(^|\D)0 min of/.test(c)) &&
        (m.currentness === "CURRENT" ? w.ownLevel !== null : w.earlierIntro !== null);
      if (!good) { failed++; console.error(`FAIL whole-day wording ${label} @${width}: ${JSON.stringify(w)}`); }
    }
    await ev(`document.querySelector('[data-claim-limit-section]')?.scrollIntoView()`);
    await sleep(200);
    const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
    writeFileSync(join(OUT, `${label.replace(/[^a-z0-9]+/gi, "-")}-${width}.png`), Buffer.from(shot.data, "base64"));
  }
}
// Keyboard: day without revision -> Tab to the first assessed interval link -> Enter; then reload and Back.
await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
const dayOnly = links.find(([l]) => l === "day-only")[1];
await send("Page.navigate", { url: BASE + dayOnly });
await settle();
await widthHolds(1440, "keyboard day-only @1440");
const target = await ev(`document.querySelectorAll('a[data-assessed-period]')[1]?.getAttribute('data-assessed-period')`);
let tabs = 0; let focused = null;
for (; tabs < 80; tabs++) {
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
  focused = await ev(`document.activeElement?.getAttribute('data-assessed-period')`);
  if (focused === target) break;
}
await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13, text: "\r" });
await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
await settle();
const afterEnter = await ev(`({ search: location.search, currentness: document.querySelector('[data-claim-limit-state]')?.dataset.currentness, selected: document.querySelector('a[aria-current=true][data-assessed-period]')?.getAttribute('data-assessed-period') })`);
const firstRecord = await ev(`document.querySelector('a[data-claim-record]')?.getAttribute('data-claim-record')`);
await ev(`document.querySelector('a[data-claim-record]').click()`);
await sleep(1500);
const record = await ev(`({ search: location.search, recordShown: !!document.querySelector('[data-record-message]'), text: (document.querySelector('[data-record-message]')?.closest('section')?.textContent ?? '').slice(0, 200) })`);
await send("Page.reload");
await settle(); await sleep(800);
await widthHolds(1440, "keyboard after reload @1440");
const afterReload = await ev(`({ search: location.search, currentness: document.querySelector('[data-claim-limit-state]')?.dataset.currentness, recordShown: !!document.querySelector('[data-record-message]') })`);
await ev(`history.back()`);
await settle();
await widthHolds(1440, "keyboard after back @1440");
const afterBack = await ev(`({ search: location.search })`);
results.keyboard = { target, tabs: tabs + 1, focused, afterEnter, firstRecord, record, afterReload, afterBack };
writeFileSync(join(OUT, "layout.json"), JSON.stringify(results, null, 2));
console.log(JSON.stringify(results, null, 1));
ws.close(); chrome.kill();
const kb = results.keyboard;
if (!(kb.focused === kb.target && kb.afterEnter.currentness)) { failed++; console.error("FAIL keyboard selection"); }
console.log(failed === 0 ? "EVIDENCE PASSED" : `EVIDENCE FAILED (${failed})`);
process.exit(failed === 0 ? 0 : 1);
