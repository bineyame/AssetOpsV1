/**
 * S4-02b phase 2b: browser evidence for the Finding fuel cost on Site > Financials at 1440x1000 and 390x900,
 * from the installed Chrome over the DevTools Protocol (the no-dependency approach of
 * tools/s402a-assumptions-evidence.mjs).
 *
 *   node tools/s402b-fuel-cost-evidence.mjs <app-base> <empty-app-base> <p01-finding> <f01-finding> \
 *       <earlier-finding> <earlier-revision> <out-dir>
 *
 * Run against servers from tools/s402b_fuel_cost_walkthrough.py on PRIVATE evidence databases (it publishes v4,
 * recomputes and closes/reopens the gate, so never point it at the owner's walkthrough databases):
 *   S402B_WALK_DB / S402B_EMPTY_DB / S402B_WORK (defaults assetops_s402bevwalk / assetops_s402bevempty /
 *   s402b-evidence).
 *
 * Claims (each PASS/FAIL with its measured value): priced range from zero with the plain wording and the
 * demonstration label; counted readings in the disclosure; identifiers only in closed disclosures; missing
 * (coverage gap), historical, pending, stale, unpriced and closed-source states with no amount; the v4
 * recompute's old/new versions over the same finding version and fuel amount; keyboard Enter, reload,
 * back/forward on a pinned version; Evidence round trip; price link into Assumptions; no page-level
 * horizontal overflow; mock references render.
 */
import { spawn, spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const BASE = process.argv[2] ?? "http://localhost:5406";
const EMPTY = process.argv[3] ?? "http://localhost:5407";
const P01 = process.argv[4];
const F01 = process.argv[5];
const OLD = process.argv[6];
const OLDREV = process.argv[7];
const OUT = process.argv[8] ?? join(tmpdir(), "s402b-evidence");
const SITE = "KOBO-001";
const WALK_DB = process.env.S402B_WALK_DB ?? "assetops_s402bevwalk";
const EMPTY_DB = process.env.S402B_EMPTY_DB ?? "assetops_s402bevempty";
const WORK = process.env.S402B_WORK ?? "s402b-evidence";
const PYTHON = ".venv\\Scripts\\python.exe";
const TOOL = "tools/s402b_fuel_cost_walkthrough.py";
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9406);
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  ["desktop", 1440, 1000],
  ["narrow", 390, 900],
];
if (!OLDREV) throw new Error("usage: see the header of tools/s402b-fuel-cost-evidence.mjs");
mkdirSync(OUT, { recursive: true });

const profile = mkdtempSync(join(tmpdir(), "assetops-s402b-cdp-"));
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
        const sock = new WebSocket(page.webSocketDebuggerUrl);
        await new Promise((res, rej) => {
          sock.addEventListener("open", res);
          sock.addEventListener("error", rej);
        });
        return sock;
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
  if (r.exceptionDetails) throw new Error(`page eval: ${JSON.stringify(r.exceptionDetails).slice(0, 400)}`);
  return r.result.value;
}
async function waitFor(expression, ms = 30000) {
  const end = Date.now() + ms;
  while (Date.now() < end) {
    if (await js(`Boolean(${expression})`)) return true;
    await sleep(150);
  }
  return false;
}
let viewport = [1440, 1000];
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
async function shot(name) {
  const tall = await js(`Math.max(document.documentElement.scrollHeight,
    ...[...document.querySelectorAll('*')].filter(e => e.scrollHeight > e.clientHeight + 1 && getComputedStyle(e).overflowY !== 'visible')
      .map(e => e.scrollHeight + e.getBoundingClientRect().top))`);
  const [w, h] = viewport;
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: Math.min(Math.ceil(tall), 7000), deviceScaleFactor: 1, mobile: w < 600 });
  await sleep(300);
  const r = await send("Page.captureScreenshot", { format: "png" });
  const file = join(OUT, `${name}.png`);
  writeFileSync(file, Buffer.from(r.data, "base64"));
  await size(w, h);
  await sleep(150);
  console.log(`      screenshot ${file}`);
}
async function key(name) {
  for (const type of ["keyDown", "keyUp"]) {
    await send("Input.dispatchKeyEvent", { type, key: name, code: name, windowsVirtualKeyCode: name === "Enter" ? 13 : 9 });
  }
}

const settled = `!document.body.innerText.match(/Loading (the site's prices|the finding's money view|the configured site|the fuel cost versions)/)`;
const bridgeReady = `document.querySelector('[data-financials-bridge]') && document.querySelector('[data-consequence-history]') && ${settled}`;
const OVERFLOW = `(() => { const d = document.scrollingElement; const page = d.scrollWidth - d.clientWidth;
  const shell = [...document.querySelectorAll('main, .operator-shell__content, .app-shell__main')]
    .map(e => e.scrollWidth - e.clientWidth); return { page, shell: Math.max(0, ...shell) }; })()`;
const UUID = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/g;
// visible text with closed <details> bodies removed (the summary stays)
const VISIBLE = `(() => { const m = document.querySelector('main').cloneNode(true);
  m.querySelectorAll('details:not([open])').forEach(d => [...d.children].forEach(c => { if (c.tagName !== 'SUMMARY') c.remove(); }));
  return m.innerText; })()`;
const STATE = `(() => { const b = document.querySelector('[data-financials-bridge]'); return b && { state: b.getAttribute('data-financials-bridge'),
  currentness: b.getAttribute('data-financials-currentness'), amount: b.getAttribute('data-financials-amount'), rev: b.getAttribute('data-finding-revision'),
  demo: b.querySelector('[data-financials-demonstration]')?.getAttribute('data-financials-demonstration') ?? null,
  why: b.querySelector('[data-financials-why]')?.innerText ?? null, range: b.querySelector('[data-financials-range]')?.innerText ?? null,
  text: b.innerText }; })()`;
const HISTORY = `[...document.querySelectorAll('[data-consequence-revision]')].map(li => li.getAttribute('data-consequence-revision') + '@' + li.getAttribute('data-consequence-current'))`;

function walk(...argv) {
  const r = spawnSync(PYTHON, [TOOL, "--db", WALK_DB, "--empty-db", EMPTY_DB, "--work-name", WORK, ...argv], { encoding: "utf-8" });
  console.log(`      $ walkthrough ${argv.join(" ")}: exit ${r.status} ${(r.stdout || "").trim().split("\n").slice(-2).join(" | ")}`);
  return r.status === 0;
}
async function api(base, path) {
  const r = await fetch(`${base}/api/sites/${SITE}${path}`);
  return r.json();
}
const money = (finding, rev, cons) =>
  `/sites/${SITE}/financials?finding_id=${finding}&revision_id=${rev}${cons ? `&consequence_revision_id=${cons}` : ""}`;

async function common(W, label) {
  const overflow = await js(OVERFLOW);
  claim(`${W} ${label}: no page-level horizontal overflow`, overflow.page <= 0 && overflow.shell <= 0, overflow);
  const visible = await js(VISIBLE);
  const ids = visible.match(UUID) ?? [];
  claim(`${W} ${label}: no identifier in visible text outside closed disclosures`, ids.length === 0, { ids: ids.length, scanned: visible.length });
  claim(`${W} ${label}: no simulator wording`, !/simulat/i.test(await js(`document.querySelector('main').innerText`)));
}

async function main() {
  ws = await connect();
  ws.addEventListener("message", (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id)(msg);
      pending.delete(msg.id);
    }
  });
  await send("Page.enable");
  await send("Runtime.enable");

  const p01 = await api(BASE, `/findings/${P01}/financial-consequences`);
  const P01REV = p01.selection.revision_id;
  const f01 = await api(BASE, `/findings/${F01}/financial-consequences`);
  const F01REV = f01.selection.revision_id;
  claim("API: P01-power CURRENT PRICED, display 0.00 to 15.82 USD", p01.currentness.state === "CURRENT" && p01.consequence.display.amount_high === "15.82", p01.consequence?.display);
  claim("API: F01-gateway QUANTITY_UNAVAILABLE POWER_COVERAGE_GAP", f01.consequence.quantity.reason === "POWER_COVERAGE_GAP");
  const old = await api(BASE, `/findings/${OLD}/financial-consequences?revision_id=${OLDREV}`);
  claim("API: the earlier finding version reads HISTORICAL", old.currentness.state === "HISTORICAL", old.currentness.state);

  // ---------- phase A: v1-v3 recomputed ----------
  for (const [W, width, height] of WIDTHS) {
    await size(width, height);
    claim(`${W}: P01-power money view loads`, await go(BASE + money(P01, P01REV), bridgeReady));
    let s = await js(STATE);
    claim(`${W} priced: amount shown as a range from zero`, s.state === "PRICED" && s.amount === "shown" && s.range === "0.00 to 15.82 USD", { state: s.state, range: s.range });
    claim(`${W} priced: plain wording, not a saving`, s.text.includes("Modelled potential fuel-cost exposure: 0.00 to 15.82 USD, under the reviewed fuel-cost-1 assumptions. This is not measured fuel saved or a physical maximum."));
    claim(`${W} priced: labelled as demonstration data`, s.demo === "P01-power" && /Demonstration data/.test(s.text));
    const readings = await js(`document.querySelectorAll('[data-consequence-reading]').length`);
    claim(`${W} priced: counted readings listed in the disclosure (non-empty set)`, readings === p01.consequence.lineage.power_intervals.length && readings > 0, { readings });
    await common(W, "priced");
    await js(`document.querySelectorAll('details').forEach(d => d.open = true)`);
    const opened = await js(`document.querySelector('main').innerText`);
    claim(`${W} priced: details hold the version ID, MODELLED_CONDITIONAL and multiplier (non-empty)`, opened.includes(p01.consequence.id) && opened.includes("MODELLED_CONDITIONAL") && opened.includes("sfc_upper_multiplier = 1.10"));
    await shot(`s402b-priced-details-${W}`);
    await js(`document.querySelectorAll('details').forEach(d => d.open = false)`);
    await shot(`s402b-priced-${W}`);
    await send("Page.reload");
    claim(`${W} priced: reload keeps the exact version and amount`, await waitFor(`${bridgeReady} && document.querySelector('[data-financials-range]')?.innerText === '0.00 to 15.82 USD'`));
    // round trip: Evidence and back
    await js(`[...document.querySelectorAll('[data-financials-bridge] a')].find(a => a.textContent.startsWith('See the evidence')).click()`);
    claim(`${W} priced: Evidence opens at the same finding version`, await waitFor(`location.pathname.endsWith('/evidence') && location.search.includes(${JSON.stringify(P01REV)})`));
    await js("history.back()");
    claim(`${W} priced: back returns to the same money view`, await waitFor(`${bridgeReady} && document.querySelector('[data-financials-bridge]').getAttribute('data-finding-revision') === ${JSON.stringify(P01REV)}`));

    claim(`${W}: F01-gateway money view loads`, await go(BASE + money(F01, F01REV), bridgeReady));
    s = await js(STATE);
    claim(`${W} missing: QUANTITY_UNAVAILABLE with its specific reason, no amount`, s.state === "QUANTITY_UNAVAILABLE" && s.amount === "none" && /cover too little/.test(s.why ?? "") && !s.demo && !/USD/.test(s.text), { why: s.why });
    await common(W, "missing");
    await shot(`s402b-missing-${W}`);

    claim(`${W}: earlier finding version loads`, await go(BASE + money(OLD, OLDREV), bridgeReady));
    s = await js(STATE);
    claim(`${W} historical: HISTORICAL, no current amount`, s.currentness === "HISTORICAL" && s.amount === "none", { state: s.state });
    await common(W, "historical");
    await shot(`s402b-historical-${W}`);

    claim(`${W}: empty store P01-power loads`, await go(EMPTY + money(P01, P01REV), bridgeReady));
    s = await js(STATE);
    claim(`${W} pending: not worked out yet, no amount`, s.state === "PENDING" && s.amount === "none" && (await js(`document.querySelector('[data-consequence-history]').getAttribute('data-consequence-history')`)) === "empty");
    await shot(`s402b-pending-${W}`);
  }

  // ---------- phase B: v4 published, not yet recomputed -> STALE ----------
  walk("publish-v4");
  for (const [W, width, height] of WIDTHS) {
    await size(width, height);
    await go(BASE + money(P01, P01REV), bridgeReady);
    const s = await js(STATE);
    claim(`${W} stale: out of date, no current amount, stored version labelled`, s.state === "STALE" && s.amount === "none" && /not a current cost/.test(s.text), { state: s.state });
    await shot(`s402b-stale-${W}`);
  }
  walk("recompute");
  walk("recompute", "--empty");
  const after = await api(BASE, `/findings/${P01}/financial-consequences`);
  const [c1, c2] = after.history.revisions;
  claim("API: after the v4 recompute, two versions over the same finding version and fuel amount", after.history.total === 2 && c2.display.amount_high === "16.20" && c1.finding_revision_id === c2.finding_revision_id && c1.digests.technical_input_sha256 === c2.digests.technical_input_sha256, { total: after.history.total });

  // ---------- phase C: old/new versions, keyboard, reload, back/forward; empty store unpriced ----------
  for (const [W, width, height] of WIDTHS) {
    await size(width, height);
    await go(BASE + money(P01, P01REV), bridgeReady);
    let s = await js(STATE);
    claim(`${W} new: version 2 current at 0.00 to 16.20 USD`, s.range === "0.00 to 16.20 USD" && s.amount === "shown", s.range);
    const hist = await js(HISTORY);
    claim(`${W} new: history lists version 1 (record) and version 2 (current)`, JSON.stringify(hist) === JSON.stringify([`${c1.id}@false`, `${c2.id}@true`]), hist);
    await shot(`s402b-versions-${W}`);
    await js(`[...document.querySelectorAll('a')].find(a => a.textContent === 'Open fuel cost version 1').focus()`);
    await key("Enter");
    const pinned = await waitFor(`location.search.includes(${JSON.stringify(c1.id)}) && document.querySelector('[data-consequence-pinned]') && ${settled}`);
    claim(`${W} old: keyboard Enter opens fuel cost version 1`, pinned, await js("location.search"));
    const pin = await js(`document.querySelector('[data-consequence-pinned]')?.innerText ?? ''`);
    claim(`${W} old: version 1 at 1.25 USD per litre, recorded not current, same fuel amount`, /0\.00 to 15\.82 USD/.test(pin) && /1\.25 USD per litre/.test(pin) && /not the current cost/.test(pin) && /fuel amount is the same/.test(pin));
    claim(`${W} old: the same finding version is held`, (await js(STATE)).rev === P01REV);
    await common(W, "old version");
    await shot(`s402b-old-version-${W}`);
    await send("Page.reload");
    claim(`${W} old: reload keeps version 1`, await waitFor(`document.querySelector('[data-consequence-pinned]')?.getAttribute('data-consequence-pinned') === ${JSON.stringify(c1.id)} && ${settled}`));
    await js("history.back()");
    claim(`${W} old: back returns to the current fuel cost`, await waitFor(`!document.querySelector('[data-consequence-pinned]') && ${bridgeReady} && !location.search.includes('consequence_revision_id')`));
    await js("history.forward()");
    claim(`${W} old: forward reopens version 1`, await waitFor(`document.querySelector('[data-consequence-pinned]')?.getAttribute('data-consequence-pinned') === ${JSON.stringify(c1.id)}`));
    // Assumptions reachable from the version: the exact price version used
    await js(`[...document.querySelectorAll('[data-consequence-pinned] a')].find(a => a.textContent === 'The site price version used').click()`);
    claim(`${W} old: its price link opens Assumptions at price version 1`, await waitFor(`document.querySelector('[data-price-exact-revision]')?.getAttribute('data-price-exact-revision') === ${JSON.stringify(c1.price.revision_id)}`));
    await shot(`s402b-assumptions-from-version-${W}`);
    await go(`${BASE}/sites/${SITE}/financials/assumptions`, `document.querySelector('[data-price-history="loaded"]') && ${settled}`);
    claim(`${W} assumptions: four price versions after v4`, (await js(`document.querySelectorAll('[data-price-history-revision]').length`)) === 4);
    claim(`${W} assumptions: no page-level overflow`, (await js(OVERFLOW)).page <= 0);
    await shot(`s402b-assumptions-${W}`);

    await go(EMPTY + money(P01, P01REV), bridgeReady);
    s = await js(STATE);
    claim(`${W} unpriced: empty store after recompute is no price for the whole window`, s.state === "UNPRICED" && s.amount === "none" && /No diesel price is recorded/.test(s.why ?? ""), { why: s.why });
    await shot(`s402b-unpriced-${W}`);
  }

  // ---------- phase D: closed source gate -> audit only ----------
  walk("close-gate");
  try {
    for (const [W, width, height] of WIDTHS) {
      await size(width, height);
      await go(BASE + money(P01, P01REV), bridgeReady);
      const s = await js(STATE);
      claim(`${W} closed source: for the record only, no amount`, s.state === "AUDIT_ONLY" && s.amount === "none", { state: s.state });
      await shot(`s402b-audit-only-${W}`);
    }
  } finally {
    walk("open-gate");
  }

  for (const [W, width, height] of WIDTHS) {
    await size(width, height);
    for (const [id, text] of [["financials", "Assumptions in use"], ["assumptions", "Financial assumptions"]]) {
      const ok = await go(`${BASE}/mockups/v69/index.html#/${id}`, `document.body && document.body.innerText.includes(${JSON.stringify(text)})`);
      claim(`${W}: mock #/${id} renders "${text}"`, ok);
      await shot(`s402b-mock-${id}-${W}`);
    }
  }
  const failed = results.filter((r) => !r.ok);
  console.log(`\n${results.length - failed.length}/${results.length} claims passed`);
  return failed.length;
}

let code = 1;
try {
  code = (await main()) === 0 ? 0 : 1;
} catch (error) {
  console.error(error);
} finally {
  ws?.close();
  chrome.kill();
  await sleep(500);
  try {
    rmSync(profile, { recursive: true, force: true });
  } catch {
    /* Chrome may still hold the profile */
  }
}
process.exit(code);
