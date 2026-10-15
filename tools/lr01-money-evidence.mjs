/**
 * LR-01 phase 2: browser evidence for the money eligibility states on Site > Financials and the Finding page at
 * 1440x1000 and 390x900, from the installed Chrome over the DevTools Protocol (the no-dependency approach of
 * tools/s402b-fuel-cost-evidence.mjs).
 *
 *   node tools/lr01-money-evidence.mjs <app-base> <state> <finding-id> <out-dir> [recorded-consequence-id]
 *
 * <state> is WITHHELD_GENERATOR_SERIES, PENDING_REASSESSMENT, ELIGIBLE (admission run after attestation) or
 * ELIGIBLE_ON_TIME. Serve a PRIVATE `assetops_lr01*` database with
 * `tools/s402c_late_power_walkthrough.py serve` and the printed frontend command first; this script only reads.
 *
 * Claims per width (each PASS/FAIL with its measured value): the bridge state; no current amount and no headline
 * for withheld/pending, with the exact recorded-cost link and the recorded 7.57 USD row kept for the record (not
 * current); the 15.82 USD headline when eligible; the refused span in plain words when withheld; the Finding
 * page's SERIES_LIMIT statement only when withheld; no page-level horizontal overflow.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const BASE = process.argv[2];
const STATE = process.argv[3];
const FINDING = process.argv[4];
const OUT = process.argv[5] ?? join(tmpdir(), "lr01-evidence");
const RECORDED = process.argv[6] ?? null;
const SITE = "KOBO-001";
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9421);
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  ["desktop", 1440, 1000],
  ["narrow", 390, 900],
];
if (!FINDING) throw new Error("usage: see the header of tools/lr01-money-evidence.mjs");
mkdirSync(OUT, { recursive: true });

const profile = mkdtempSync(join(tmpdir(), "assetops-lr01-cdp-"));
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
  await sleep(400);
  return ok;
}
async function shot(name) {
  const tall = await js("document.documentElement.scrollHeight");
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

const settled = `!document.body.innerText.match(/Loading (the site's prices|the finding's money view|the configured site|the fuel cost versions|the finding)/)`;
const bridgeReady = `document.querySelector('[data-financials-bridge]') && document.querySelector('[data-consequence-history]') && ${settled}`;
const findingReady = `document.querySelector('#site-finding-limits-heading') && ${settled}`;
const READ = `(() => {
  const b = document.querySelector('[data-financials-bridge]');
  const rows = [...document.querySelectorAll('[data-consequence-revision]')].map(r => ({
    id: r.getAttribute('data-consequence-revision'), current: r.getAttribute('data-consequence-current'), text: r.innerText }));
  return {
    state: b?.getAttribute('data-financials-bridge'), amount: b?.getAttribute('data-financials-amount'),
    headline: b?.querySelector("[data-financials-headline='amount']")?.innerText ?? null,
    limits: [...(b?.querySelectorAll('[data-financials-series-limit]') ?? [])].map(x => x.innerText),
    pendingNote: Boolean(b?.querySelector("[data-financials-pending-reassessment='true']")),
    recordedLink: b?.querySelector('[data-financials-recorded-link]')?.getAttribute('href') ?? null,
    recordedId: b?.querySelector('[data-financials-recorded-link]')?.getAttribute('data-financials-recorded-link') ?? null,
    rows,
    overflow: document.documentElement.scrollWidth - window.innerWidth,
  };
})()`;

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
  const tag = STATE.toLowerCase().replace(/_/g, "-");
  const gated = STATE === "WITHHELD_GENERATOR_SERIES" || STATE === "PENDING_REASSESSMENT";
  for (const [W, width, height] of WIDTHS) {
    await size(width, height);
    const ok = await go(`${BASE}/sites/${SITE}/financials?finding_id=${FINDING}`, bridgeReady);
    claim(`${W} ${STATE}: Financials loaded`, ok);
    const s = await js(READ);
    if (gated) {
      claim(`${W} ${STATE}: bridge state, no current amount, no headline`, s.state === STATE && s.amount === "none" && s.headline === null,
        { state: s.state, amount: s.amount, headline: s.headline });
      claim(`${W} ${STATE}: exact link to the recorded consequence revision`, Boolean(s.recordedLink)
        && (RECORDED === null || (s.recordedId === RECORDED && s.recordedLink.includes(`consequence_revision_id=${RECORDED}`))),
        { recordedId: s.recordedId, href: s.recordedLink });
      const rec = s.rows.find((r) => r.id === s.recordedId);
      claim(`${W} ${STATE}: the recorded 7.57 USD row is kept for the record, not current`, Boolean(rec) && rec.current === "false"
        && rec.text.includes("7.57 USD") && rec.text.includes("kept for the record"), rec);
      claim(`${W} ${STATE}: no row is called the current fuel cost`, s.rows.every((r) => r.current === "false"), s.rows.map((r) => r.current));
      if (STATE === "WITHHELD_GENERATOR_SERIES") {
        claim(`${W} withheld: the refused span in plain words`, s.limits.length > 0 && s.limits.every((t) => t.includes("not judged")), s.limits);
      } else {
        claim(`${W} pending: the reassessment wording`, s.pendingNote, s.pendingNote);
      }
    } else {
      claim(`${W} ${STATE}: current 15.82 USD headline`, s.state === "PRICED" && s.amount === "shown" && (s.headline ?? "").includes("15.82"),
        { state: s.state, amount: s.amount, headline: s.headline });
      claim(`${W} ${STATE}: exactly one current row`, s.rows.filter((r) => r.current === "true").length === 1, s.rows.map((r) => r.current));
    }
    claim(`${W} ${STATE}: no page-level horizontal overflow on Financials`, s.overflow <= 0, s.overflow);
    await shot(`lr01-${tag}-financials-${W}`);
    if (gated && s.recordedLink) {
      await go(`${BASE}${s.recordedLink}`, `document.querySelector('[data-consequence-pinned]') && ${settled}`);
      const pinned = await js(`(() => { const p = document.querySelector('[data-consequence-pinned]');
        return { id: p?.getAttribute('data-consequence-pinned'), current: p?.getAttribute('data-consequence-pinned-current'),
                 text: p?.innerText ?? '', headline: Boolean(document.querySelector("[data-financials-headline='amount']")) }; })()`);
      claim(`${W} ${STATE}: the opened recorded revision is a record, not the current cost`, pinned.current === "false"
        && !pinned.headline && pinned.text.includes("7.57"), { id: pinned.id, current: pinned.current, headline: pinned.headline });
      await shot(`lr01-${tag}-recorded-${W}`);
    }
    const fok = await go(`${BASE}/sites/${SITE}/findings/${FINDING}`, findingReady);
    const f = await js(`({ end: document.querySelector("[data-finding-end-reason='SERIES_LIMIT']")?.innerText ?? null,
      overflow: document.documentElement.scrollWidth - window.innerWidth })`);
    claim(`${W} ${STATE}: Finding page loaded`, fok);
    if (STATE === "WITHHELD_GENERATOR_SERIES" || STATE === "PENDING_REASSESSMENT") {
      claim(`${W} ${STATE}: the Finding states its SERIES_LIMIT end`, (f.end ?? "").includes("07:00"), f.end);
    } else {
      claim(`${W} ${STATE}: no SERIES_LIMIT end on the full episode`, f.end === null, f.end);
    }
    claim(`${W} ${STATE}: no page-level horizontal overflow on the Finding`, f.overflow <= 0, f.overflow);
    await shot(`lr01-${tag}-finding-${W}`);
  }
  const failed = results.filter((r) => !r.ok);
  writeFileSync(join(OUT, `lr01-${tag}-claims.json`), JSON.stringify(results, null, 2));
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
