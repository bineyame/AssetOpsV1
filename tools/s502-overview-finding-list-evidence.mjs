/**
 * S5-02 browser evidence for the Overview's selected-day Finding list (`mini:3#a/b`), at 1440 and 390 px.
 *
 *   node tools/s502-overview-finding-list-evidence.mjs <app-base> <stage> <out-dir> <s502-manifest> <s404-manifest>
 *
 * <app-base> is the web origin served over `tools/s502_overview_finding_list_walkthrough.py serve` (default
 * http://localhost:5452). Run from the repository root. Stages:
 *
 *   initial  assessed zero, unassessed, dirty and failed days (no rows, no count), the positive day (rows in index
 *            order, exact revision links, first-page preview, full-list link with the identical window, parity
 *            outcome), Enter on a row link then Back, reload, date change, and the v6.9 mock `#/mini` captures
 *   late     after `late`: the positive day's list reads not current with no rows
 *   settled  after `settle`: the positive day's list is CURRENT again
 *   closed   after `gate --close`: the list is closed with no rows and no count; the Overview stays visible
 *
 * Every claim prints PASS/FAIL with its measured value; each width checks no page-level horizontal overflow, and
 * the rows claim requires a non-empty measured row set. Writes <out>/s502-<stage>-claims.json and screenshots.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const BASE = process.argv[2];
const STAGE = process.argv[3];
const OUT = process.argv[4] ?? join(tmpdir(), "s502-evidence");
const MANIFEST = process.argv[5];
const S404 = process.argv[6];
if (!BASE || !STAGE || !MANIFEST || !S404) throw new Error("usage: see the header of tools/s502-overview-finding-list-evidence.mjs");
const manifest = JSON.parse(readFileSync(MANIFEST, "utf-8"));
const s404 = JSON.parse(readFileSync(S404, "utf-8"));
const SITE = s404.site_code;
const DAYS = s404.days;
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9452);
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  ["desktop", 1440, 1000],
  ["narrow", 390, 900],
];
const MOCK = `${pathToFileURL(resolve("frontend/mockups/v69/index.html")).href}#/mini`;
mkdirSync(OUT, { recursive: true });

const profile = mkdtempSync(join(tmpdir(), "assetops-s502-cdp-"));
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

const READY = `document.querySelector('[data-overview-finding-list]') && !/Loading the (findings|site's overview)/.test(document.body.innerText)`;
const READ = `(() => {
  const list = document.querySelector('[data-overview-finding-list]');
  const rows = [...document.querySelectorAll('[data-overview-finding-row]')];
  const text = list?.innerText ?? '';
  return {
    href: location.pathname + location.search,
    listFor: document.querySelector('[data-overview-finding-list-for]')?.getAttribute('data-overview-finding-list-for') ?? null,
    state: list?.getAttribute('data-overview-finding-list') ?? null,
    rows: rows.map((r) => [r.getAttribute('data-overview-finding-row'), r.getAttribute('data-finding-revision')]),
    links: [...document.querySelectorAll('[data-overview-finding-link]')].map((a) => a.getAttribute('href')),
    shown: document.querySelector('[data-overview-finding-shown]')?.textContent ?? null,
    full: document.querySelector('[data-overview-finding-full-list]')?.getAttribute('href') ?? null,
    parity: document.querySelector('[data-overview-finding-parity]')?.getAttribute('data-overview-finding-parity') ?? null,
    parityText: document.querySelector('[data-overview-finding-parity]')?.innerText ?? null,
    known: document.querySelector('[data-known-finding]')?.getAttribute('data-known-finding') ?? null,
    knownRevision: document.querySelector('[data-known-finding-revision]')?.getAttribute('data-known-finding-revision') ?? null,
    freshness: document.querySelector('[data-freshness-state]')?.getAttribute('data-freshness-state') ?? null,
    money: document.querySelector('[data-money-state]')?.getAttribute('data-money-state') ?? null,
    token: list?.querySelector('[data-finding-index-token]')?.textContent ?? null,
    emptyClaim: /No Findings for this day/.test(text),
    countClaim: /\\d+ Findings? overlap this day/.test(text),
    overflow: document.documentElement.scrollWidth - window.innerWidth,
  };
})()`;

const overviewUrl = (day) => `${BASE}/sites/${SITE}?date=${day}`;

async function overview(W, name, url) {
  const ok = await go(url, READY);
  const s = await js(READ);
  claim(`${W} ${name}: settled`, ok, s.state);
  claim(`${W} ${name}: no page-level horizontal overflow`, s.overflow <= 0, s.overflow);
  claim(`${W} ${name}: imported Overview sections stay visible`, Boolean(s.freshness && s.money), [s.freshness, s.money]);
  await shot(`s502-${STAGE}-${W}-${name}`);
  return s;
}
function noClaim(W, name, s, state) {
  claim(`${W} ${name}: list state ${state}, no rows, no count, no empty claim`,
    s.state === state && s.rows.length === 0 && !s.emptyClaim && !s.countClaim, { state: s.state, rows: s.rows.length });
}
async function settle() {
  await waitFor(READY);
  await sleep(400);
  return js(READ);
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
      const e = await overview(W, "empty", overviewUrl(DAYS.empty));
      claim(`${W} empty (#a): assessed zero with a token, no rows`,
        e.state === "current-empty" && e.rows.length === 0 && Boolean(e.token) && e.emptyClaim, e.state);
      for (const [name, state] of [["unassessed", "UNASSESSED"], ["dirty", "STALE_PROJECTION"], ["failed", "FAILED"]]) {
        noClaim(W, name, await overview(W, name, overviewUrl(DAYS[name])), state);
      }
      const p = await overview(W, "positive", overviewUrl(DAYS.positive));
      claim(`${W} positive (#b): rows with exact revision links`,
        p.state === "current-rows" && p.rows.length > 0
          && p.links.every((l, i) => l.endsWith(`/findings/${p.rows[i][0]}?revision_id=${p.rows[i][1]}`)), { rows: p.rows, links: p.links });
      const api = (s404.reads?.positive?.rows ?? []).map((r) => r[0]).slice(0, p.rows.length);
      claim(`${W} positive: order equals the API index read`,
        JSON.stringify(p.rows.map((r) => r[0])) === JSON.stringify(api), { ui: p.rows.map((r) => r[0]), api });
      claim(`${W} positive: first-page preview says it is not the whole list`, /first \d+ of \d+/.test(p.shown ?? ""), p.shown);
      const q = new URLSearchParams((p.full ?? "").split("?")[1] ?? "");
      claim(`${W} positive: full-list link has the identical window and domain`,
        q.get("from") === `${DAYS.positive}T00:00:00Z` && q.get("domain") === "mini-grid-dispatch" && Boolean(q.get("to")), p.full);
      const mp = manifest.positive_parity ?? {};
      claim(`${W} positive: parity outcome shown`, p.parity !== null,
        { ui: p.parity, apiFirstEqualsKnown: mp.equal, known: [p.known, p.knownRevision], first: p.rows[0], text: p.parityText });
      claim(`${W} positive: parity follows the Overview's own freshness (same only when CURRENT)`,
        p.freshness === "CURRENT" ? (mp.equal ? p.parity === "same" : p.parity !== "same") : p.parity === "not-compared",
        { freshness: p.freshness, ui: p.parity });
      // Enter on the first row link opens its exact revision; Back returns to the selected Overview day.
      const before = p.href;
      await js(`document.querySelector('[data-overview-finding-link]').focus()`);
      await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13, text: "\r" });
      await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
      await waitFor(`location.pathname.includes('/findings/')`);
      await sleep(600);
      const opened = await js("location.pathname + location.search");
      claim(`${W} Enter on a row link opens the exact revision`, opened === p.links[0], { opened, want: p.links[0] });
      await shot(`s502-${STAGE}-${W}-row-detail`);
      await js("history.back()");
      const back = await settle();
      claim(`${W} Back returns to the selected Overview day`, back.href === before && back.state === "current-rows", { back: back.href, before });
      await send("Page.reload");
      const reloaded = await settle();
      claim(`${W} reload keeps the day, the Finding pin and the rows`,
        reloaded.href === before && JSON.stringify(reloaded.rows) === JSON.stringify(p.rows), reloaded.href);
      const fullOk = await go(`${BASE}${p.full}`,
        `document.querySelector('[data-finding-index-state]') && !/Loading the site's findings/.test(document.body.innerText)`);
      const fullState = await js(`document.querySelector('[data-finding-index-state]')?.getAttribute('data-finding-index-state')`);
      claim(`${W} full Site Findings page opens on the identical window`, fullOk && fullState === "current-rows", fullState);
      await shot(`s502-${STAGE}-${W}-full-list`);
      await go(overviewUrl(DAYS.positive), READY);
      await sleep(400);
      await js(`document.querySelector('[data-window-day-link="next"]').click()`);
      await waitFor(`(document.querySelector('[data-overview-finding-list-for]')?.getAttribute('data-overview-finding-list-for') ?? '${DAYS.positive}') !== '${DAYS.positive}'`);
      const nd = await settle();
      const oldRow = (r) => p.rows.some((x) => x[0] === r[0] && x[1] === r[1]);
      claim(`${W} date change: the next day's list, none of the old day's rows`,
        nd.listFor !== DAYS.positive && !nd.rows.some(oldRow), { listFor: nd.listFor, state: nd.state, rows: nd.rows, href: nd.href });
      await send("Page.reload");
      const nr = await settle();
      claim(`${W} reload after date change keeps the new day and no old rows`, nr.listFor === nd.listFor && !nr.rows.some(oldRow), nr.listFor);
      await shot(`s502-${STAGE}-${W}-date-change`);
      await go(MOCK, `document.body && document.body.innerText.length > 100`);
      await sleep(800);
      await shot(`s502-mock-${W}-mini`);
      record[W] = { e, p, back, reloaded, nd, nr };
    } else if (STAGE === "late") {
      const p = await overview(W, "positive-late", overviewUrl(DAYS.positive));
      noClaim(W, "positive after late evidence", p, "STALE_PROJECTION");
      record[W] = { p };
    } else if (STAGE === "settled") {
      const p = await overview(W, "positive-settled", overviewUrl(DAYS.positive));
      claim(`${W} positive after settle: CURRENT rows again`, p.state === "current-rows" && p.rows.length > 0,
        { rows: p.rows, parity: p.parity, known: [p.known, p.knownRevision], text: p.parityText });
      claim(`${W} positive after settle: parity follows the Overview's own freshness`,
        p.freshness === "CURRENT" ? p.parity === "same" : p.parity === "not-compared", { freshness: p.freshness, ui: p.parity });
      record[W] = { p };
    } else if (STAGE === "closed") {
      const p = await overview(W, "positive-closed", overviewUrl(DAYS.positive));
      noClaim(W, "positive with the gate closed", p, "closed");
      const e = await overview(W, "empty-closed", overviewUrl(DAYS.empty));
      noClaim(W, "empty with the gate closed", e, "closed");
      record[W] = { p, e };
    }
  }
  writeFileSync(join(OUT, `s502-${STAGE}-claims.json`), JSON.stringify({ stage: STAGE, results, record }, null, 2));
  const failed = results.filter((r) => !r.ok).length;
  console.log(`${results.length - failed}/${results.length} claims passed`);
  return failed;
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
