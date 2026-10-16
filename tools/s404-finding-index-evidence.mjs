/**
 * S4-04 phase 2 browser evidence for Site > Findings (the scoped Site Finding index), at 1440 and 390 px.
 *
 *   node tools/s404-finding-index-evidence.mjs <app-base> <stage> <out-dir> <manifest>
 *
 * <app-base> is the web origin served over `tools/s404_finding_index_walkthrough.py serve` (e.g.
 * http://localhost:5434); <manifest> is <work>/s404-manifest.json from `prepare`. Stages:
 *
 *   initial  assessed empty (#a), positive day (#b), unassessed/stale/failed variants, positive pages 1 and 2
 *            (page 2 from the address alone, so a reload keeps it), exact pinned detail and history of row 1
 *   late     after `late`: the positive day reads not current with no rows; the old page-2 address restarts
 *   settled  after `settle`: the positive day reads CURRENT again with the new row; the pinned revision from
 *            `initial` still opens at that exact revision
 *   closed   after `gate --close`: the list is closed with no rows and no count; the pinned revision still opens
 *
 * Every claim prints PASS/FAIL with its measured value; each width checks no page-level horizontal overflow, and
 * the rows claim requires a non-empty measured row set. Writes <out>/s404-<stage>-claims.json and screenshots.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const BASE = process.argv[2];
const STAGE = process.argv[3];
const OUT = process.argv[4] ?? join(tmpdir(), "s404-evidence");
const MANIFEST = process.argv[5];
if (!BASE || !STAGE || !MANIFEST) throw new Error("usage: see the header of tools/s404-finding-index-evidence.mjs");
const manifest = JSON.parse(readFileSync(MANIFEST, "utf-8"));
const SITE = manifest.site_code;
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9434);
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  ["desktop", 1440, 1000],
  ["narrow", 390, 900],
];
mkdirSync(OUT, { recursive: true });
const PIN_FILE = join(OUT, "s404-pinned.json");

const profile = mkdtempSync(join(tmpdir(), "assetops-s404-cdp-"));
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

const INDEX_READY = `document.querySelector('[data-finding-index-state]') && !document.body.innerText.match(/Loading the site's findings/)`;
const FINDING_READY = `document.querySelector('[data-finding-revision]') || (document.querySelector('main') && !document.body.innerText.match(/Loading the Finding/) && document.querySelector('h2'))`;
const READ = `(() => {
  const rows = [...document.querySelectorAll('[data-finding-index-row]')];
  const text = document.body.innerText;
  return {
    href: location.pathname + location.search,
    state: document.querySelector('[data-finding-index-state]')?.getAttribute('data-finding-index-state') ?? null,
    heading: document.querySelector('#site-finding-index-heading')?.textContent ?? null,
    rows: rows.map((r) => [r.getAttribute('data-finding-index-row'), r.getAttribute('data-finding-revision')]),
    links: [...document.querySelectorAll('[data-finding-index-link]')].map((a) => a.getAttribute('href')),
    amounts: [...document.querySelectorAll('[data-finding-index-amount]')].map((c) => c.textContent),
    next: document.querySelector('[data-finding-index-next]')?.getAttribute('href') ?? null,
    token: document.querySelector('[data-finding-index-token]')?.textContent ?? null,
    emptyClaim: /No Findings in this window/.test(text),
    countClaim: /\\d+ Findings? in this window/.test(text),
    notVerdict: /not a statement that the window has no Findings/.test(text),
    overflow: document.documentElement.scrollWidth - window.innerWidth,
  };
})()`;

function page(from, to, extra = {}) {
  const q = new URLSearchParams({ from, to, domain: "mini-grid-dispatch", ...extra });
  return `${BASE}/sites/${SITE}/findings?${q.toString()}`;
}
const win = (name) => manifest.windows[name];

async function index(W, name, url, shotName = name) {
  const ok = await go(url, INDEX_READY);
  const s = await js(READ);
  claim(`${W} ${name}: settled`, ok, s.state);
  claim(`${W} ${name}: no page-level horizontal overflow`, s.overflow <= 0, s.overflow);
  await shot(`s404-${STAGE}-${W}-${shotName}`);
  return s;
}
function noClaim(W, name, s, state) {
  claim(`${W} ${name}: state ${state}, no rows, no count, no empty claim`,
    s.state === state && s.rows.length === 0 && !s.emptyClaim && !s.countClaim, s);
}
async function pinned(W, name, href) {
  const ok = await go(`${BASE}${href}`, FINDING_READY);
  const shown = await js(`document.querySelector('[data-finding-revision]')?.getAttribute('data-finding-revision') ?? null`);
  const want = new URL(`${BASE}${href}`).searchParams.get("revision_id");
  claim(`${W} ${name}: exact pinned revision opens`, ok && shown === want, { shown, want });
  await shot(`s404-${STAGE}-${W}-${name}`);
  return shown;
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
      const e = await index(W, "empty", page(...win("empty")));
      claim(`${W} empty (#a): assessed CURRENT zero with a watermark token`, e.state === "current-empty" && e.rows.length === 0 && Boolean(e.token), e);
      const p = await index(W, "positive", page(...win("positive")));
      claim(`${W} positive (#b): at least two rows, exact revision links, no amount`,
        p.state === "current-rows" && p.rows.length >= 2
          && p.links.every((l, i) => l.endsWith(`/findings/${p.rows[i][0]}?revision_id=${p.rows[i][1]}`))
          && p.amounts.every((a) => !/\d/.test(a)), { rows: p.rows.length, links: p.links.slice(0, 2), amounts: p.amounts.slice(0, 2) });
      const expectedOrder = (manifest.reads.positive.rows ?? []).map((r) => r[0]);
      claim(`${W} positive: order equals the API read`, JSON.stringify(p.rows.map((r) => r[0])) === JSON.stringify(expectedOrder), { ui: p.rows.map((r) => r[0]), api: expectedOrder });
      for (const [name, state] of [["unassessed", "UNASSESSED"], ["dirty", "STALE_PROJECTION"], ["failed", "FAILED"]]) {
        const v = await index(W, name, page(...win(name)));
        noClaim(W, name, v, state);
        claim(`${W} ${name}: says it is not a no-Findings verdict`, v.notVerdict, v.notVerdict);
      }
      const w1 = await index(W, "paged-page1", page(...win("positive"), { limit: "2" }));
      claim(`${W} page 1 of 2 per page: two rows and a next-page link`, w1.rows.length === 2 && Boolean(w1.next), w1.next);
      const w2 = await index(W, "paged-page2", `${BASE}${w1.next}`);
      claim(`${W} page 2 (loaded from the address alone): rows differ from page 1`,
        w2.state === "current-rows" && w2.rows.length > 0 && w2.rows.every((r) => !w1.rows.some((x) => x[0] === r[0])), w2.rows);
      writeFileSync(PIN_FILE, JSON.stringify({ page2: w1.next, pinned: p.links[0], findingRows: p.rows }, null, 2));
      await pinned(W, "pinned-detail", p.links[0]);
      const [path, query] = p.links[0].split("?");
      const hok = await go(`${BASE}${path}/history?${query}`, `document.querySelector('[data-history-revision]')`);
      claim(`${W} pinned history opens`, hok, `${path}/history?${query}`);
      await shot(`s404-${STAGE}-${W}-pinned-history`);
      record[W] = { e, p, w1, w2 };
    } else {
      const pin = JSON.parse(readFileSync(PIN_FILE, "utf-8"));
      if (STAGE === "late") {
        const p = await index(W, "positive-late", page(...win("positive")));
        noClaim(W, "positive after late evidence", p, "STALE_PROJECTION");
        const old = await index(W, "old-page2", `${BASE}${pin.page2}`);
        claim(`${W} old page-2 address restarts`, old.state === "basis-changed" && old.rows.length === 0, old.state);
        record[W] = { p, old };
      } else if (STAGE === "settled") {
        const p = await index(W, "positive-settled", page(...win("positive")));
        const before = new Set(pin.findingRows.map((r) => r[0]));
        claim(`${W} positive after settle: CURRENT with a new row`, p.state === "current-rows" && p.rows.some((r) => !before.has(r[0])), p.rows);
        const old = await index(W, "old-page2-settled", `${BASE}${pin.page2}`);
        claim(`${W} old page-2 address still restarts after settle`, old.state === "basis-changed", old.state);
        await pinned(W, "pinned-after-newer", pin.pinned);
        record[W] = { p, old };
      } else if (STAGE === "closed") {
        const p = await index(W, "positive-closed", page(...win("positive")));
        noClaim(W, "positive with the gate closed", p, "closed");
        const e = await index(W, "empty-closed", page(...win("empty")));
        noClaim(W, "empty with the gate closed", e, "closed");
        await pinned(W, "pinned-closed", pin.pinned);
        record[W] = { p, e };
      }
    }
  }
  writeFileSync(join(OUT, `s404-${STAGE}-claims.json`), JSON.stringify({ stage: STAGE, results, record }, null, 2));
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
