/**
 * S4-08: browser evidence for Site > Financials > Assumptions "Interpretation history" at 1440x1000 and 390x900,
 * from the installed Chrome over the DevTools Protocol (the approach of tools/s402a-assumptions-evidence.mjs).
 *
 *   node tools/s408-assumption-history-evidence.mjs <app-base-url> <var/s408_owner/s408-state.json> <out-dir> [owner|mixed|closed]
 *
 * Run against `tools/s408_assumption_history_walkthrough.py serve --case owner|mixed` (closed: after `close-gate`).
 * Claims: unchanged default address and one identical cutoff string for prices and history; latest and earlier
 * versions; recorded amounts only labelled as history beside their source; the price-only sentence; an unpriced
 * version; explicit cutoffs kept through reload with the price list at the same moment; the next-page address;
 * the exact fuel cost version link; no identifier in visible text outside closed disclosures; no current-amount
 * wording; no horizontal overflow; mixed and closed sources withhold every amount. Captures app and v69 mock.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { widthGuard } from "./evidence-checks.mjs";

const BASE = process.argv[2] ?? "http://localhost:5468";
const STATE_FILE = process.argv[3];
const OUT = process.argv[4] ?? join(tmpdir(), "s408-evidence");
const MODE = process.argv[5] ?? "owner";
const SITE = "KOBO-001";
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9468);
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  ["desktop", 1440, 1000],
  ["narrow", 390, 900],
];
if (!STATE_FILE) throw new Error("usage: node tools/s408-assumption-history-evidence.mjs <base> <s408-state.json> <out-dir> [owner|mixed|closed]");
const STATE = JSON.parse(readFileSync(STATE_FILE, "utf-8"));
mkdirSync(OUT, { recursive: true });

const profile = mkdtempSync(join(tmpdir(), "assetops-s408-cdp-"));
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
const requireWidth = widthGuard({ send, claim });
async function size(width, height) {
  viewport = [width, height];
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 600 });
  await requireWidth(width, height, `resize to ${width}x${height}`, { record: false });
}
async function go(url, ready) {
  await send("Page.navigate", { url });
  const ok = await waitFor(ready);
  await sleep(300);
  await requireWidth(viewport[0], viewport[1], `loaded ${url}`);
  return ok;
}
async function shot(name) {
  const tall = await js(`Math.max(document.documentElement.scrollHeight,
    ...[...document.querySelectorAll('*')].filter(e => e.scrollHeight > e.clientHeight + 1 && getComputedStyle(e).overflowY !== 'visible')
      .map(e => e.scrollHeight + e.getBoundingClientRect().top))`);
  const [w, h] = viewport;
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: Math.min(Math.ceil(tall), 7000), deviceScaleFactor: 1, mobile: w < 600 });
  await sleep(300);
  await requireWidth(viewport[0], null, `capture ${name}`, { record: false });
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

const settled = `!document.body.innerText.match(/Loading (the site's prices|the configured site)/)`;
const historyPage = `document.querySelector('[data-consequence-history]') && ${settled}`;
const OVERFLOW = `(() => { const d = document.scrollingElement; const page = d.scrollWidth - d.clientWidth;
  const shell = [...document.querySelectorAll('main, .operator-shell__content, .app-shell__main')]
    .map(e => e.scrollWidth - e.clientWidth); return { page, shell: Math.max(0, ...shell) }; })()`;
const UUID = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/g;
// Visible text outside closed disclosures (a closed <details> renders only its summary).
const VISIBLE = `(() => { const c = document.querySelector('main').cloneNode(true);
  c.querySelectorAll('details:not([open]) > :not(summary)').forEach(e => e.remove()); return c.innerText; })()`;
const ROWS = `[...document.querySelectorAll('[data-history-row]')].map(r => ({ id: r.getAttribute('data-history-row'),
  at: r.getAttribute('data-history-at-cutoff'), amount: r.getAttribute('data-history-amount'),
  text: r.innerText.slice(0, 3000) }))`;
const where = () => js(`location.pathname + location.search`);

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
  const page = `${BASE}/sites/${SITE}/financials/assumptions`;
  const q = (p) => `${page}?${new URLSearchParams(p).toString()}`;

  for (const [W, width, height] of WIDTHS) {
    await size(width, height);
    claim(`${W}: Assumptions with Interpretation history loads`, await go(page, historyPage));
    claim(`${W}: default address is not rewritten`, (await where()) === `/sites/${SITE}/financials/assumptions`, await where());
    const cuts = await js(`[document.querySelector('[data-price-recorded-cutoff]')?.getAttribute('data-price-recorded-cutoff') ?? null,
      document.querySelector('[data-history-cutoff]')?.getAttribute('data-history-cutoff') ?? null]`);
    claim(`${W}: prices and history at one identical cutoff string`, Boolean(cuts[1]) && cuts[0] === cuts[1], cuts);
    const rows = await js(ROWS);
    const visible = await js(VISIBLE);
    const ids = visible.match(UUID) ?? [];
    claim(`${W}: no identifier in visible text outside closed disclosures`, ids.length === 0, ids.slice(0, 3));
    claim(`${W}: no current amount wording`, !/current amount|today's (amount|cost)/i.test(visible));
    const overflow = await js(OVERFLOW);
    claim(`${W}: no horizontal overflow (page and shell)`, overflow.page <= 0 && overflow.shell <= 0, overflow);
    if (MODE === "owner") {
      const ats = new Set(rows.map((r) => r.at));
      claim(`${W}: latest and earlier versions listed`, ats.has("CURRENT_AT_CUTOFF") && ats.has("HISTORICAL_AT_CUTOFF"), [...ats]);
      const shown = rows.filter((r) => r.amount === "SHOWN");
      claim(
        `${W}: recorded amounts labelled as history beside the source`,
        shown.length > 0 && shown.every((r) => /Recorded amount — historical, assumption-conditioned audit history\. Not a current cost\./.test(r.text) && /Prepared example data|Generated test data/.test(r.text)),
        shown.length,
      );
      claim(`${W}: the price-only change is said plainly`, rows.some((r) => r.text.includes("The price changed; the measured result did not.")));
      claim(`${W}: an unpriced version states no amount`, rows.some((r) => r.amount === "UNPRICED" && /No amount\./.test(r.text)));
      await shot(`s408-default-${W}`);
      // Explicit cutoffs survive reload; each row was recorded by then.
      for (const name of ["T1", "T3"]) {
        const at = STATE.cutoffs[name];
        claim(`${W}: ${name} address loads`, await go(q({ recorded_at: at }), historyPage));
        await send("Page.reload");
        await sleep(300);
        await waitFor(historyPage);
        await requireWidth(viewport[0], viewport[1], "after reload or back");
        const kept = await js(`document.querySelector('[data-history-cutoff]')?.getAttribute('data-history-cutoff')`);
        claim(`${W}: ${name} cutoff kept after reload`, new Date(kept).getTime() === new Date(at).getTime() && (await where()).includes("recorded_at="), kept);
        const price = await js(`document.querySelector('[data-price-recorded-cutoff]')?.getAttribute('data-price-recorded-cutoff')`);
        claim(`${W}: ${name} price list at the same moment`, new Date(price).getTime() === new Date(at).getTime(), price);
        if (name === "T1") await shot(`s408-T1-${W}`);
      }
      const t1 = STATE.rows_T3.filter((r) => r.at_cutoff === "HISTORICAL_AT_CUTOFF").length;
      claim(`${W}: T3 lists earlier versions (state file)`, t1 > 0, t1);
      if (STATE.next_cursor_T3) {
        claim(`${W}: next page address loads`, await go(q({ recorded_at: STATE.cutoffs.T3, history_after: STATE.next_cursor_T3, history_limit: "2" }), historyPage));
        claim(`${W}: next page offers the way back`, await js(`Boolean(document.querySelector('[data-history-first-page]'))`));
      }
      await go(page, historyPage);
      const href = await js(`document.querySelector('[data-history-at-cutoff=CURRENT_AT_CUTOFF] [data-history-open]')?.getAttribute('href')`);
      claim(`${W}: exact fuel cost version link`, /consequence_revision_id=/.test(href ?? ""), href);
      await js(`document.querySelector('[data-history-at-cutoff=CURRENT_AT_CUTOFF] [data-history-open]').click()`);
      await sleep(1500);
      claim(`${W}: link opens the finding's own Financials view at that version`, (await where()) === href, await where());
      await shot(`s408-finding-financials-${W}`);
      const ok = await go(`${BASE}/mockups/v69/index.html#/assumptions`, `document.body && document.body.innerText.includes("Interpretation history")`);
      claim(`${W}: v69 assumptions mock renders`, ok);
      await shot(`s408-mock-assumptions-${W}`);
    } else if (MODE === "mixed") {
      claim(`${W}: mixed source withholds every recorded amount`, rows.length > 0 && rows.every((r) => r.amount !== "SHOWN"), rows.map((r) => r.amount));
      claim(`${W}: mixed source is labelled`, rows.some((r) => r.text.includes("Sources do not agree")));
      await shot(`s408-mixed-${W}`);
    } else {
      claim(`${W}: closed source lists every version without an amount`, rows.length > 0 && rows.every((r) => r.amount === "SOURCE_CLOSED"), rows.map((r) => r.amount));
      claim(`${W}: closed source is said`, await js(`Boolean(document.querySelector('[data-history-source-closed]'))`));
      await shot(`s408-closed-${W}`);
    }
  }
  const failed = results.filter((r) => !r.ok);
  console.log(`\n${results.length - failed.length}/${results.length} claims passed (${MODE})`);
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
