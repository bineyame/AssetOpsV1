/**
 * S5-01 phase 2: browser evidence for the selected-window Site Overview at 1440x1000 and 390x900, from the installed
 * Chrome over the DevTools Protocol (the no-dependency approach of tools/lr01-money-evidence.mjs).
 *
 *   node tools/s5-overview-evidence.mjs <app-base> <stage> <out-dir> [p02-finding-id p02-revision-id]
 *
 * Serve a PRIVATE `assetops_s501_owner*` database with `tools/s5_overview_walkthrough.py serve` and the printed
 * frontend command first; this script only reads. <stage> follows the owner walkthrough:
 *
 *   initial    2026-10-02 ordinary (no current amount), 2026-11-10 Unknown, 2026-10-07 Failed, P01 2026-10-23 priced
 *              with its demonstration label and exact links, P02 2026-10-24 WITHHELD_GENERATOR_SERIES; the day and
 *              Finding pin are written to the address and survive a reload; Next day changes the day and drops the pin
 *   pending    after `attest`, before `tick`: P02 no amount, the raw money gate PENDING_REASSESSMENT, same Finding
 *   eligible   after `tick`: P02 priced with its demonstration label (Architect M3 ruling), gate ELIGIBLE
 *   stopped    after `stop-schedule`: P02 no amount, SCHEDULE_STOPPED named
 *   closed     after `gate --close`: SOURCE_CLOSED, no amount, the pinned Finding kept for audit
 *
 * Every claim prints PASS/FAIL with its measured value; each width also checks no page-level horizontal overflow.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const BASE = process.argv[2];
const STAGE = process.argv[3];
const OUT = process.argv[4] ?? join(tmpdir(), "s5-evidence");
const PIN = process.argv[5] && process.argv[6] ? [process.argv[5], process.argv[6]] : null;
const SITE = "KOBO-001";
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9425);
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  ["desktop", 1440, 1000],
  ["narrow", 390, 900],
];
const DAYS = { ordinary: "2026-10-02", failed: "2026-10-07", p01: "2026-10-23", p02: "2026-10-24", unknown: "2026-11-10" };
if (!BASE || !STAGE) throw new Error("usage: see the header of tools/s5-overview-evidence.mjs");
mkdirSync(OUT, { recursive: true });

const profile = mkdtempSync(join(tmpdir(), "assetops-s5-cdp-"));
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

const settled = `document.querySelector('[data-money-state]') && !document.body.innerText.match(/Loading the site's overview/)`;
const READ = `(() => {
  const m = document.querySelector('[data-money-state]');
  const q = (s) => document.querySelector(s);
  return {
    href: location.pathname + location.search,
    day: q('[data-window-date]')?.getAttribute('data-window-date') ?? null,
    freshness: q('[data-freshness-state]')?.getAttribute('data-freshness-state') ?? null,
    freshnessText: q('[data-freshness-state]')?.innerText ?? '',
    assessment: q('[data-assessment-state]')?.getAttribute('data-assessment-state') ?? null,
    money: m?.getAttribute('data-money-state') ?? null,
    gate: m?.getAttribute('data-money-gate') ?? null,
    amount: (() => { const a = m?.querySelector('[data-money-amount]'); if (!a) return null;
      return a.getAttribute('data-money-amount') === 'none' ? 'none' : a.innerText.trim(); })(),
    demo: m?.querySelector('[data-financials-demonstration]')?.getAttribute('data-financials-demonstration') ?? null,
    consequence: m?.getAttribute('data-consequence-revision-id') ?? null,
    financials: m?.querySelector('[data-window-financials-link]')?.getAttribute('href') ?? null,
    finding: q('[data-known-finding]')?.getAttribute('data-known-finding') ?? null,
    revision: q('[data-known-finding-revision]')?.getAttribute('data-known-finding-revision') ?? null,
    findingList: q('[data-finding-list]')?.innerText ?? null,
    reasons: q('[data-window-reasons="freshness"]')?.textContent ?? '',
    sourceOpen: q('[data-source-open]')?.getAttribute('data-source-open') ?? null,
    overflow: document.documentElement.scrollWidth - window.innerWidth,
  };
})()`;

const NONE = "none";
async function day(W, name, date, pin = null) {
  const pinQ = pin ? `&finding_id=${pin[0]}&finding_revision_id=${pin[1]}` : "";
  const ok = await go(`${BASE}/sites/${SITE}?date=${date}${pinQ}`, settled);
  claim(`${W} ${name} ${date}: Overview loaded`, ok);
  const s = await js(READ);
  claim(`${W} ${name}: Finding list unavailable, never empty`, s.findingList === "Unavailable until the Site Finding index is delivered.", s.findingList);
  claim(`${W} ${name}: no page-level horizontal overflow`, s.overflow <= 0, s.overflow);
  await shot(`s5-${STAGE}-${name}-${W}`);
  return s;
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
  const record = {};
  for (const [W, width, height] of WIDTHS) {
    await size(width, height);
    if (STAGE === "initial") {
      const o = await day(W, "ordinary", DAYS.ordinary);
      claim(`${W} ordinary: no current amount`, o.money !== "PRICED" && o.amount === NONE, { money: o.money, amount: o.amount });
      const u = await day(W, "unknown", DAYS.unknown);
      claim(`${W} unknown: reads Unknown, no amount`, u.freshness === "UNASSESSED" && u.freshnessText.includes("Unknown")
        && u.assessment === "UNKNOWN" && u.amount === NONE, { freshness: u.freshness, assessment: u.assessment });
      const f = await day(W, "failed", DAYS.failed);
      claim(`${W} failed: reads Failed, no amount`, f.assessment === "FAILED" && f.amount === NONE, { assessment: f.assessment, money: f.money });
      const p1 = await day(W, "p01", DAYS.p01);
      claim(`${W} P01: priced, demonstration label, gate ELIGIBLE`, p1.money === "PRICED" && /\d+\.\d\d to \d+\.\d\d [A-Z]{3}/.test(p1.amount ?? "")
        && p1.demo === "P01-power" && p1.gate === "ELIGIBLE", { money: p1.money, amount: p1.amount, demo: p1.demo, gate: p1.gate });
      claim(`${W} P01: exact Finding version and fuel cost version in the address and the link`,
        p1.href.includes(`finding_revision_id=${p1.revision}`) && (p1.financials ?? "").includes(`consequence_revision_id=${p1.consequence}`),
        { href: p1.href, financials: p1.financials });
      const p2 = await day(W, "p02", DAYS.p02);
      claim(`${W} P02: WITHHELD_GENERATOR_SERIES, no amount, Finding kept`, p2.money === "WITHHELD_GENERATOR_SERIES" && p2.amount === NONE
        && Boolean(p2.finding), { money: p2.money, finding: p2.finding, revision: p2.revision });
      record.p02 = { finding: p2.finding, revision: p2.revision, consequence: p2.consequence };
      // Reload keeps the day and the pin; Next day changes the day and drops the pin.
      const before = p2.href;
      await send("Page.reload");
      await sleep(300);
      await waitFor(settled);
      await sleep(300);
      const again = await js(READ);
      claim(`${W} reload keeps the day and the Finding version`, again.href === before && again.day === DAYS.p02, { before, after: again.href });
      await js(`[...document.querySelectorAll('button')].find(b => b.innerText === 'Next day').click()`);
      await waitFor(`document.querySelector('[data-window-date]')?.getAttribute('data-window-date') === '2026-10-25'`);
      await sleep(600);
      const next = await js(READ);
      claim(`${W} Next day: 2026-10-25 in the address, old pin dropped`, next.href.includes("date=2026-10-25")
        && !next.href.includes(`finding_revision_id=${p2.revision}`), next.href);
      await shot(`s5-${STAGE}-next-day-${W}`);
    } else {
      const s = await day(W, `p02-${STAGE}`, DAYS.p02, PIN);
      record[W] = s;
      if (STAGE === "pending") {
        claim(`${W} pending: no amount, raw gate PENDING_REASSESSMENT, same Finding`, s.amount === NONE && s.gate === "PENDING_REASSESSMENT"
          && (PIN === null || s.finding === PIN[0]), { money: s.money, gate: s.gate, finding: s.finding });
      } else if (STAGE === "eligible") {
        claim(`${W} eligible: priced with the demonstration label, gate ELIGIBLE`, s.money === "PRICED" && /\d+\.\d\d to \d+\.\d\d [A-Z]{3}/.test(s.amount ?? "")
          && s.demo !== null && s.gate === "ELIGIBLE", { money: s.money, amount: s.amount, demo: s.demo, gate: s.gate });
        claim(`${W} eligible: a new Finding version is selected`, PIN === null || s.revision !== PIN[1], { revision: s.revision });
      } else if (STAGE === "stopped") {
        claim(`${W} stopped: no amount, SCHEDULE_STOPPED named`, s.amount === NONE && s.money.startsWith("UPSTREAM_")
          && s.reasons.includes("SCHEDULE_STOPPED"), { money: s.money, reasons: s.reasons });
      } else if (STAGE === "closed") {
        claim(`${W} closed: SOURCE_CLOSED, no amount, pinned Finding kept for audit`, s.money === "SOURCE_CLOSED" && s.amount === NONE
          && s.sourceOpen === "closed" && (PIN === null || s.finding === PIN[0]), { money: s.money, finding: s.finding });
      } else {
        throw new Error(`unknown stage ${STAGE}`);
      }
    }
  }
  const failed = results.filter((r) => !r.ok);
  writeFileSync(join(OUT, `s5-${STAGE}-claims.json`), JSON.stringify({ results, record }, null, 2));
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
