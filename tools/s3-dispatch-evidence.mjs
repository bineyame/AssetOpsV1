/**
 * S3-01 phase 3b: V-01 app-vs-mock evidence for Performance > Dispatch, with
 * layout measurements, interaction and reload checks, from the Chrome already
 * installed here over the DevTools Protocol (same approach as
 * tools/layout-evidence.mjs; no dependency).
 *
 * Run against the walkthrough servers (tools/s3_dispatch_walkthrough.py):
 *   node tools/s3-dispatch-evidence.mjs http://localhost:5320 <screenshot-dir>
 *
 * Every claim is measured and printed; the run exits non-zero if any fails.
 * Each set-based claim also reports its size, so an empty set cannot pass.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const BASE = process.argv[2] ?? "http://localhost:5320";
const OUT = process.argv[3] ?? join(tmpdir(), "s3-dispatch-evidence");
const SITE = "KOBO-001";
const PORT = 9341;
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  ["desktop", 1440, 1000],
  ["narrow", 390, 900],
];
mkdirSync(OUT, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "assetops-s3-cdp-"));
const chrome = spawn(
  CHROME,
  ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "about:blank"],
  { stdio: "ignore" },
);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const results = [];
function claim(name, ok, detail) {
  results.push({ name, ok, detail });
  console.log(`${ok ? "PASS" : "FAIL"}  ${name}${detail === undefined ? "" : `  ${JSON.stringify(detail)}`}`);
}

async function connect() {
  for (let i = 0; i < 80; i += 1) {
    try {
      const page = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page");
      if (page?.webSocketDebuggerUrl) {
        const ws = new WebSocket(page.webSocketDebuggerUrl);
        await new Promise((res, rej) => {
          ws.addEventListener("open", res);
          ws.addEventListener("error", rej);
        });
        return ws;
      }
    } catch {
      /* not up yet */
    }
    await sleep(250);
  }
  throw new Error("Chrome did not expose a page target");
}

let ws;
let seq = 0;
const pending = new Map();
function send(method, params = {}) {
  seq += 1;
  const id = seq;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`timeout ${method}`)), 60000);
    pending.set(id, (msg) => {
      clearTimeout(timer);
      msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
    });
    ws.send(JSON.stringify({ id, method, params }));
  });
}
async function js(expression) {
  const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  return r.result.value;
}
async function waitFor(expression, ms = 45000) {
  const end = Date.now() + ms;
  while (Date.now() < end) {
    if (await js(`Boolean(${expression})`)) return true;
    await sleep(150);
  }
  return false;
}
async function size(width, height) {
  viewport = [width, height];
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 600 });
}
async function go(url, ready) {
  await send("Page.navigate", { url });
  const ok = await waitFor(ready);
  await sleep(300);
  return ok;
}
let viewport = [1440, 1000];
async function shot(name) {
  // The app shell scrolls inside its own frame, so grow the viewport to the tallest scroller for the capture.
  const tall = await js(`Math.max(document.documentElement.scrollHeight,
    ...[...document.querySelectorAll('*')].filter(e => e.scrollHeight > e.clientHeight + 1 && getComputedStyle(e).overflowY !== 'visible')
      .map(e => e.scrollHeight + e.getBoundingClientRect().top))`);
  const h = Math.min(Math.ceil(tall), 7000);
  await send("Emulation.setDeviceMetricsOverride", { width: viewport[0], height: h, deviceScaleFactor: 1, mobile: viewport[0] < 600 });
  await sleep(300);
  const r = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(join(OUT, `${name}.png`), Buffer.from(r.data, "base64"));
  await size(viewport[0], viewport[1]);
}
const overflow = () =>
  js(`(() => { const d = document.documentElement; return { scrollWidth: d.scrollWidth, clientWidth: d.clientWidth,
      wide: [...document.querySelectorAll('.durable-dispatch *')].filter(e => e.getBoundingClientRect().right > d.clientWidth + 1
      && !e.closest('.data-table__scroll') && ![...e.children].some(c => c.getBoundingClientRect().right > d.clientWidth + 1))
      .map(e => (e.className || e.tagName) + ':' + Math.round(e.getBoundingClientRect().width)).slice(0, 6) }; })()`);
const READY = "document.querySelector('[data-dispatch-status], [data-dispatch-cutover], [data-dispatch-window]')";
const app = (q) => `${BASE}/sites/${SITE}/performance/dispatch?${q}`;

async function main() {
  ws = await connect();
  ws.addEventListener("message", (e) => {
    const msg = JSON.parse(e.data);
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id)(msg);
      pending.delete(msg.id);
    }
  });
  await send("Page.enable");
  await send("Runtime.enable");

  for (const [label, width, height] of WIDTHS) {
    await size(width, height);
    // Mock reference.
    await go(`${BASE}/mockups/v69/index.html#/dispatch`, "document.body && document.body.innerText.includes('Sources and 15-minute blocks')");
    const mockPanels = await js(`[...document.querySelectorAll('h2,h3')].map(h => h.textContent.trim()).filter(Boolean).slice(0, 14)`);
    const mockOverflow = await js(`document.documentElement.scrollWidth - document.documentElement.clientWidth`);
    claim(`${label}: mock dispatch renders its panels`, mockPanels.length > 0, { mockPanels, mockOverflow });
    await shot(`mock-dispatch-${label}`);

    // Populated days.
    for (const [day, expect] of [
      ["2026-10-02", "CANDIDATE_AVOIDABLE"],
      ["2026-10-09", "NECESSARY"],
      ["2026-10-01", "INDETERMINATE"],
    ]) {
      const ok = await go(app(`day=${day}`), READY);
      const state = await js(`({ status: document.querySelector('[data-dispatch-status]')?.dataset.dispatchStatus,
        periods: [...document.querySelectorAll('.dispatch-period .claim-badge')].map(e => e.dataset.claimLevel),
        cards: document.querySelectorAll('[data-total]').length,
        coverageRows: document.querySelectorAll('[data-coverage-role]').length,
        panels: [...document.querySelectorAll('.durable-dispatch h2, .durable-dispatch h3')].map(h => h.textContent.trim()) })`);
      claim(`${label} ${day}: ${expect} period, cards and coverage render`, ok && state.periods.includes(expect) && state.cards === 4 && state.coverageRows > 0, state);
      const o = await overflow();
      claim(`${label} ${day}: no sideways page scroll`, o.scrollWidth <= o.clientWidth && o.wide.length === 0, o);
      await shot(`app-dispatch-${day}-${label}`);
    }

    // Interaction: select the period and a block, then reload; the exact revision and block stay.
    await go(app("day=2026-10-02"), READY);
    await js(`document.querySelector('.dispatch-period').click()`);
    await waitFor(`document.querySelector('[data-selected-revision]')`);
    const blocks = await js(`document.querySelectorAll('[data-block]').length`);
    await js(`document.querySelector('[data-block="2"]').focus()`);
    await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13, text: String.fromCharCode(13) });
    await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
    const keyed = await waitFor(`document.querySelector('[data-selected-block]') && document.querySelector('[data-evidence-id]')`);
    const before = await js(`({ url: location.search, revision: document.querySelector('[data-selected-revision]')?.dataset.selectedRevision,
      block: document.querySelector('[data-selected-block]')?.dataset.selectedBlock, rows: document.querySelectorAll('[data-evidence-id]').length,
      scope: document.querySelector('[data-evidence-scope]')?.dataset.evidenceScope })`);
    claim(`${label}: keyboard Enter selects a block and lists its accepted records`, keyed && blocks > 2 && before.rows > 0 && before.scope === "block", { blocks, ...before });
    await shot(`app-dispatch-selected-${label}`);
    await send("Page.reload");
    await waitFor(`document.querySelector('[data-selected-block]') && document.querySelector('[data-evidence-id]')`);
    await sleep(300);
    const after = await js(`({ url: location.search, revision: document.querySelector('[data-selected-revision]')?.dataset.selectedRevision,
      block: document.querySelector('[data-selected-block]')?.dataset.selectedBlock, rows: document.querySelectorAll('[data-evidence-id]').length })`);
    claim(`${label}: reload keeps the exact revision, block and records`, after.url === before.url && after.revision === before.revision && after.block === before.block && after.rows === before.rows, after);
    const o = await overflow();
    claim(`${label}: selected state has no sideways page scroll`, o.scrollWidth <= o.clientWidth && o.wide.length === 0, o);

    // Honest states.
    for (const [day, status] of [
      ["2026-10-05", "STALE_PROJECTION"],
      ["2026-10-07", "FAILED"],
      ["2027-01-01", "UNASSESSED"],
    ]) {
      await go(app(`day=${day}`), READY);
      const s = await js(`({ status: document.querySelector('[data-dispatch-status]')?.dataset.dispatchStatus,
        reasons: [...document.querySelectorAll('[data-status-reason]')].map(e => e.dataset.statusReason),
        text: document.querySelector('.dispatch-status')?.innerText.slice(0, 200) })`);
      claim(`${label} ${day}: shows ${status} with its reasons`, s.status === status && (status === "UNASSESSED" || s.reasons.length > 0), s);
      await shot(`app-dispatch-${status.toLowerCase()}-${label}`);
    }

    // A stored revision that is not the day's current one is labelled, not passed off as current.
    const pinnedId = before.revision;
    await go(app(`day=2026-10-05&revision=${pinnedId}`), "document.querySelector('[data-dispatch-pinned], [data-dispatch-selected-missing]')");
    const pinned = await js(`({ pinned: Boolean(document.querySelector('[data-dispatch-pinned]')), revision: document.querySelector('[data-selected-revision]')?.dataset.selectedRevision })`);
    claim(`${label}: a pinned stored revision on another day is labelled as not current`, pinned.pinned && pinned.revision === pinnedId, pinned);

    // Analysis view: S3-supported constraint and coverage portions; the rest typed unavailable.
    await go(app(`day=2026-10-02&revision=${pinnedId}&view=analysis`), "document.querySelector('[data-constraint-block]')");
    const a = await js(`({ constraintRows: document.querySelectorAll('[data-constraint-block]').length,
      unavailable: [...document.querySelectorAll('[data-unavailable]')].map(e => e.dataset.unavailable),
      gated: Boolean(document.querySelector('[data-dispatch-gated]')),
      comparison: document.querySelector('[data-comparison-outcome]')?.dataset.comparisonEmpty })`);
    claim(`${label}: Analysis shows constraint rows and names unavailable portions`, a.constraintRows > 0 && a.unavailable.length >= 3 && a.gated && a.comparison === "true", a);
    const ao = await overflow();
    claim(`${label}: Analysis has no sideways page scroll`, ao.scrollWidth <= ao.clientWidth && ao.wide.length === 0, ao);
    await shot(`app-analysis-${label}`);
    await go(`${BASE}/mockups/v69/index.html#/analysis`, "document.body && document.body.innerText.includes('Constraint comparison')");
    await shot(`mock-analysis-${label}`);
  }
  const failed = results.filter((r) => !r.ok);
  console.log(`\n${results.length - failed.length}/${results.length} claims passed; screenshots in ${OUT}`);
  return failed.length === 0 ? 0 : 1;
}

let code = 1;
try {
  code = await main();
} catch (error) {
  console.error(`ERROR ${error.message}`);
} finally {
  chrome.kill();
  await sleep(500);
  try {
    rmSync(profile, { recursive: true, force: true });
  } catch {
    /* Chrome may still hold the profile */
  }
}
process.exit(code);
