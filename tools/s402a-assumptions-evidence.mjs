/**
 * S4-02a: browser evidence for Site > Financials (Overview, Finding bridge) and Financials > Assumptions at
 * 1440x1000 and 390x900, from the installed Chrome over the DevTools Protocol (the no-dependency approach of
 * tools/g02-gap-evidence.mjs).
 *
 *   node tools/s402a-assumptions-evidence.mjs <app-base-url> <empty-app-base-url> <finding-id> <out-dir>
 *
 * Run against private servers from tools/s402a_assumptions_walkthrough.py (populated store: demonstration
 * prices v1 INITIAL, v2 SUCCESSION, v3 CORRECTION; empty store: the same Findings, no price). Price IDs and
 * recorded instants are read from the app's own API, so the UI is compared with stored IDs, not literals.
 *
 * Claims: current price in plain words with the stored selected ID; schedule order v1, v3, v1, v2 (corrected
 * middle and both unaffected v1 slices); exact versions and recorded cutoffs survive reload; back/forward keep
 * the exact selection; keyboard Enter on a version link opens it; a foreign version is refused, never the
 * latest; the disabled edit and its catalogued gap pair; no identifier in visible text outside closed
 * disclosures; no Scenarios subtab; the empty store states no price; the Finding bridge holds the exact
 * FindingRevision, shows no amount and links to that version's Evidence; Finding -> bridge and Foundation ->
 * Assumptions links; no page-level horizontal overflow. Non-vacuity: S402A_ALTER=1 expects a wrong schedule
 * order, so that claim must FAIL. Every claim prints PASS/FAIL with its measured value.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { widthGuard } from "./evidence-checks.mjs";

const BASE = process.argv[2] ?? "http://localhost:5400";
const EMPTY = process.argv[3] ?? "http://localhost:5401";
const FINDING = process.argv[4];
const OUT = process.argv[5] ?? join(tmpdir(), "s402a-evidence");
const SITE = "KOBO-001";
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9402);
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  ["desktop", 1440, 1000],
  ["narrow", 390, 900],
];
const ALTER = process.env.S402A_ALTER === "1";
if (!FINDING) throw new Error("usage: node tools/s402a-assumptions-evidence.mjs <base> <empty-base> <finding-id> <out-dir>");
mkdirSync(OUT, { recursive: true });

const profile = mkdtempSync(join(tmpdir(), "assetops-s402a-cdp-"));
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

const settled = `!document.body.innerText.match(/Loading (the site's prices|the finding's money view|the configured site)/)`;
const pricePage = `document.querySelector('[data-price-cutoff]') && document.querySelector('#site-price-heading') && ${settled}`;
const OVERFLOW = `(() => { const d = document.scrollingElement; const page = d.scrollWidth - d.clientWidth;
  const shell = [...document.querySelectorAll('main, .operator-shell__content, .app-shell__main')]
    .map(e => e.scrollWidth - e.clientWidth); return { page, shell: Math.max(0, ...shell) }; })()`;
const schedule = `[...document.querySelectorAll('[data-price-assignment]')].map(r => r.getAttribute('data-price-revision'))`;
const gaps = `[...document.querySelectorAll('[data-gap-id]')].map(e => e.getAttribute('data-gap-id') + '@' + e.getAttribute('data-gap-placement') + '@' + e.getAttribute('data-gap-status') + '@' + (e.getBoundingClientRect().height > 0))`;
const UUID = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/g;

async function api(path) {
  const r = await fetch(`${BASE}/api/sites/${SITE}${path}`);
  return r.json();
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

  const all = await api("/financial-assumptions");
  const [v1, v2, v3] = all.revisions.map((r) => r.revision_id);
  const [r1, r2] = all.revisions.map((r) => r.recorded_at);
  claim("API: three stored versions read from the app's own API", all.revisions.length === 3, { v1, v2, v3 });
  const today = await api(`/financial-assumptions?valid_at=${encodeURIComponent(new Date().toISOString())}`);
  const assumptions = `${BASE}/sites/${SITE}/financials/assumptions`;

  for (const [W, width, height] of WIDTHS) {
    await size(width, height);
    // --- populated current ---
    claim(`${W}: Assumptions loads`, await go(assumptions, pricePage));
    // S4-08 (packet item 1): the default address stays unrewritten and the price list and the fuel cost history
    // report one identical cutoff string (the history's server-fixed instant, passed through unchanged).
    const where = await js(`location.pathname + location.search`);
    claim(`${W}: default Assumptions address is not rewritten`, where === `/sites/${SITE}/financials/assumptions`, where);
    const cuts = await js(`[document.querySelector('[data-price-recorded-cutoff]')?.getAttribute('data-price-recorded-cutoff') ?? null,
      document.querySelector('[data-history-cutoff]')?.getAttribute('data-history-cutoff') ?? null]`);
    claim(`${W}: price list and fuel cost history read at one identical cutoff`, Boolean(cuts[0]) && cuts[0] === cuts[1], cuts);
    const lead = await js(`document.querySelector('[data-price-selection]')?.innerText ?? ''`);
    claim(`${W}: plain current price, set by the system`, /^Diesel price, set by the system on \d+ \w+ 2026: 1\.25 USD per litre/.test(lead), lead.slice(0, 120));
    const selected = await js(`document.querySelector('[data-price-selection]')?.getAttribute('data-price-selected-revision')`);
    claim(`${W}: selected ID equals the API's selection`, selected === today.selection.revision_id && selected === v1, selected);
    const order = await js(schedule);
    const expected = ALTER ? [v1, v1, v3, v2] : [v1, v3, v1, v2];
    claim(`${W}: schedule is v1, corrected v3, v1, future v2`, JSON.stringify(order) === JSON.stringify(expected), { size: order.length });
    const pairs = await js(gaps);
    claim(`${W}: exactly the human-edit gap, open and visible`, JSON.stringify(pairs) === JSON.stringify(["G-assumptions-human-edit@assumptions.price.human-edit@open@true"]), pairs);
    claim(`${W}: edit control disabled`, await js(`document.querySelector('[data-price-edit] button')?.disabled === true`));
    const visible = await js(`document.querySelector('main').innerText`);
    const ids = visible.match(UUID) ?? [];
    claim(`${W}: no identifier in visible text (closed record details)`, ids.length === 0, { ids: ids.length, scanned: visible.length });
    claim(`${W}: no Scenarios subtab`, !/Scenario/i.test(visible) && (await js(`[...document.querySelectorAll('[data-financials-section]')].map(a=>a.textContent).join('|')`)) === "Overview|Assumptions");
    claim(`${W}: Financials tab is current`, await js(`[...document.querySelectorAll('nav[aria-label="Site sections"] a')].find(a=>a.getAttribute('aria-current')==='page')?.textContent === 'Financials'`));
    const overflow = await js(OVERFLOW);
    claim(`${W}: no page-level horizontal overflow on Assumptions`, overflow.page <= 0 && overflow.shell <= 0, overflow);
    await js(`document.querySelectorAll('details').forEach(d => d.open = true)`);
    const opened = (await js(`document.querySelector('main').innerText`)).match(UUID) ?? [];
    claim(`${W}: identifiers are present once the record details open (non-empty set)`, opened.includes(v1), { ids: opened.length });
    await js(`document.querySelectorAll('details').forEach(d => d.open = false)`);
    await shot(`s402a-assumptions-current-${W}`);

    // --- keyboard: Enter on a version link opens the exact version; back/forward keep it ---
    await js(`[...document.querySelectorAll('a')].find(a => a.textContent === 'Open version 3').focus()`);
    await key("Enter");
    const opened3 = await waitFor(`location.search.includes(${JSON.stringify(v3)}) && document.querySelector('[data-price-exact-revision]') && ${settled}`);
    claim(`${W}: keyboard Enter opens version 3`, opened3, await js("location.search"));
    claim(`${W}: version 3 shows its corrected price`, /1\.19 USD per litre/.test(await js(`document.querySelector('[data-price-exact-revision]')?.innerText ?? ''`)));
    await js("history.back()");
    claim(`${W}: back returns to the current list`, await waitFor(`location.search === '' && !document.querySelector('[data-price-exact-revision]') && ${pricePage}`));
    await requireWidth(viewport[0], viewport[1], "after reload or back");
    await js("history.forward()");
    claim(`${W}: forward reopens version 3`, await waitFor(`document.querySelector('[data-price-exact-revision]')?.getAttribute('data-price-exact-revision') === ${JSON.stringify(v3)}`));
    await requireWidth(viewport[0], viewport[1], "after forward");
    await send("Page.reload");
    claim(`${W}: reload keeps version 3`, await waitFor(`document.querySelector('[data-price-exact-revision]')?.getAttribute('data-price-exact-revision') === ${JSON.stringify(v3)} && ${settled}`));
    await requireWidth(viewport[0], viewport[1], "after reload or back");
    await shot(`s402a-assumptions-version3-${W}`);

    // --- historical cutoffs ---
    for (const [label, at, want] of [["after v1", r1, [v1]], ["after v2", r2, [v1, v2]]]) {
      await go(`${assumptions}?recorded_at=${encodeURIComponent(at)}`, `${pricePage} && document.querySelector('[data-price-recorded-at]')`);
      await send("Page.reload");
      await waitFor(`${pricePage} && document.querySelector('[data-price-recorded-at]')`);
      await requireWidth(viewport[0], viewport[1], "after reload or back");
      const got = await js(schedule);
      claim(`${W}: recorded cutoff ${label} selects ${want.length} stored slice(s) after reload`, JSON.stringify(got) === JSON.stringify(want), { size: got.length });
      if (label === "after v1") await shot(`s402a-assumptions-recorded-v1-${W}`);
    }

    // --- foreign version ---
    await go(`${assumptions}?revision_id=00000000-0000-4000-8000-000000000000`, `document.querySelector('[data-financials-read]') && ${settled}`);
    claim(`${W}: an unknown version is refused, never the latest`, (await js(`document.querySelector('[data-financials-read]')?.getAttribute('data-financials-read')`)) === "not_found" && !(await js(`Boolean(document.querySelector('[data-price-exact-revision]'))`)));

    // --- empty store ---
    claim(`${W}: empty store loads`, await go(`${EMPTY}/sites/${SITE}/financials/assumptions`, pricePage));
    claim(`${W}: empty store states no price, no schedule`, (await js(`document.querySelector('[data-price-selection]')?.getAttribute('data-price-selection')`)) === "NO_PRICE" && (await js(schedule)).length === 0);
    claim(`${W}: empty store keeps the human-edit gap`, (await js(gaps)).length === 1);
    claim(`${W}: no page-level overflow (empty store)`, (await js(OVERFLOW)).page <= 0);
    await shot(`s402a-assumptions-empty-${W}`);

    // --- Finding -> bridge -> Evidence -> back ---
    await go(`${BASE}/sites/${SITE}/findings/${FINDING}`, `document.querySelector('[data-finding-financials-link] a') && !document.body.innerText.includes('Loading the Finding')`);
    const findingRev = await js(`document.querySelector('[data-finding-revision]')?.getAttribute('data-finding-revision')`);
    await js(`document.querySelector('[data-finding-financials-link] a').click()`);
    const bridged = await waitFor(`document.querySelector('[data-financials-bridge]') && location.search.includes('revision_id=') && ${settled}`);
    claim(`${W}: Finding link opens its money view and pins the exact version`, bridged && (await js("location.search")).includes(findingRev ?? "none"), await js("location.search"));
    const bridge = await js(`(() => { const b = document.querySelector('[data-financials-bridge]'); return { state: b.getAttribute('data-financials-bridge'), rev: b.getAttribute('data-finding-revision'), text: b.innerText, evidence: [...b.querySelectorAll('a')].find(a => a.textContent.startsWith('See the evidence'))?.getAttribute('href') }; })()`);
    claim(`${W}: bridge state QUANTITY_UNAVAILABLE, no amount`, bridge.state === "QUANTITY_UNAVAILABLE" && !/USD|\$|\d+\.\d\d/.test(bridge.text.replace(UUID, "")) && /Not calculated/.test(bridge.text), bridge.state);
    claim(`${W}: bridge links that exact version's Evidence`, bridge.evidence === `/sites/${SITE}/findings/${FINDING}/evidence?revision_id=${bridge.rev}`, bridge.evidence);
    claim(`${W}: no page-level overflow (bridge)`, (await js(OVERFLOW)).page <= 0);
    await shot(`s402a-financials-bridge-${W}`);
    await send("Page.reload");
    claim(`${W}: reload keeps the bridged version`, await waitFor(`document.querySelector('[data-financials-bridge]')?.getAttribute('data-finding-revision') === ${JSON.stringify(bridge.rev)} && ${settled}`));
    await requireWidth(viewport[0], viewport[1], "after reload or back");
    await js(`[...document.querySelectorAll('[data-financials-bridge] a')].find(a => a.textContent.startsWith('See the evidence')).click()`);
    claim(`${W}: Evidence opens at the same version`, await waitFor(`location.pathname.endsWith('/evidence') && location.search.includes(${JSON.stringify(bridge.rev)})`));
    await js("history.back()");
    claim(`${W}: back returns to the same money view`, await waitFor(`document.querySelector('[data-financials-bridge]')?.getAttribute('data-finding-revision') === ${JSON.stringify(bridge.rev)}`));
    await requireWidth(viewport[0], viewport[1], "after reload or back");

    // --- Overview without a Finding, Foundation link ---
    await go(`${BASE}/sites/${SITE}/financials`, `document.querySelector('[data-financials-bridge="none"]') && document.querySelector('#site-financials-price-heading') && ${settled}`);
    claim(`${W}: Overview shows the price in use`, /1\.25 USD per litre/.test(await js(`document.querySelector('main').innerText`)));
    await shot(`s402a-financials-overview-${W}`);
    await go(`${BASE}/sites/${SITE}/foundation`, `document.querySelector('[data-financial-assumptions-link] a')`);
    claim(`${W}: Foundation links to Assumptions beside its open gap line`, (await js(`document.querySelector('[data-financial-assumptions-link] a').getAttribute('href')`)) === `/sites/${SITE}/financials/assumptions` && (await js(`document.querySelector('[data-gap-id="G-foundation-financial-assumptions"]')?.getAttribute('data-gap-status')`)) === "open");

    // --- mock references ---
    for (const [id, text] of [["assumptions", "Financial assumptions"], ["financials", "Assumptions in use"]]) {
      const ok = await go(`${BASE}/mockups/v69/index.html#/${id}`, `document.body && document.body.innerText.includes(${JSON.stringify(text)})`);
      claim(`${W}: mock #/${id} renders "${text}"`, ok);
      await shot(`s402a-mock-${id}-${W}`);
    }
  }
  const failed = results.filter((r) => !r.ok);
  console.log(`\n${results.length - failed.length}/${results.length} claims passed${ALTER ? " (S402A_ALTER=1: the schedule claims must fail)" : ""}`);
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
