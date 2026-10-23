/**
 * W5-02b part 1 browser evidence: the cold Site Work > Actions list (K2a/K2b) and the domain Action shell, at
 * 1440 and 390 px, measured against the W5-02 build-spec caps (".agent/W5-02-build-spec.md", "Measurement,
 * capture and deviations" and U4).
 *
 *   node tools/w502-cold-work-evidence.mjs <manifest.json> <out-dir> [web-host]
 *
 * <manifest.json> is var/w502b_cold_work/manifest.json (per-mode API port, Action IDs, reads.<name>.query).
 * Each API at port P is served by a Vite dev server at P - 3500 on <web-host> (default http://localhost).
 * Per state and width: waits until the panel state is not `loading`, measures document overflow, page main,
 * strip, panel and notice heights, the table scroller, the sticky first column, visible rows and whether each
 * row's code is on one line, then writes a full-page PNG. Every claim prints PASS/FAIL with its measured value;
 * row claims require a non-empty measured row set. Writes <out>/w502b-measurements.json.
 * It launches and stops only its own headless Chrome.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { widthGuard } from "./evidence-checks.mjs";

const MANIFEST = process.argv[2];
const OUT = process.argv[3];
const HOST = process.argv[4] ?? "http://localhost";
if (!MANIFEST || !OUT) throw new Error("usage: see the header of tools/w502-cold-work-evidence.mjs");
const manifest = JSON.parse(readFileSync(MANIFEST, "utf-8"));
const SITE = manifest.site_code;
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9471);
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  ["desktop", 1440, 1000],
  ["narrow", 390, 900],
];
// Build-spec caps [1440, 390].
const WORK_CAPS = { main: [1400, 1800], strip: [100, 150], panel: [440, 650], notice: [110, 160] };
const ACTION_CAPS = { main: [1350, 1750], strip: [100, 120], notice: [100, 140] };
mkdirSync(OUT, { recursive: true });

const profile = mkdtempSync(join(tmpdir(), "assetops-w502b-cdp-"));
const chrome = spawn(
  CHROME,
  ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "about:blank"],
  { stdio: "ignore" },
);
console.log(`chrome pid ${chrome.pid}`);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const results = [];
const captures = [];
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
  await sleep(500);
  await requireWidth(viewport[0], viewport[1], `loaded ${url}`, { record: false });
  return ok;
}
async function shot(name) {
  const tall = await js("document.documentElement.scrollHeight");
  const [w, h] = viewport;
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: Math.min(Math.ceil(tall), 7000), deviceScaleFactor: 1, mobile: w < 600 });
  await sleep(300);
  await requireWidth(viewport[0], null, `capture ${name}`, { record: false });
  const r = await send("Page.captureScreenshot", { format: "png" });
  const file = `${name}.png`;
  writeFileSync(join(OUT, file), Buffer.from(r.data, "base64"));
  await size(w, h);
  await sleep(150);
  return file;
}

const WORK_READY = `(document.querySelector('[data-cold-work-state-panel]') && !document.querySelector('[data-cold-work-state-panel="loading"]')) || /Site unavailable/.test(document.querySelector('main')?.innerText ?? '')`;
const ACTION_READY = `document.querySelector('main[data-domain-action-shell]') && !document.querySelector('main[data-domain-action-shell="loading"]')`;
const MEASURE_WORK = `(() => {
  const h = (e) => (e ? Math.round(e.getBoundingClientRect().height) : null);
  const main = document.querySelector('main[data-cold-work-page="actions"]');
  const panel = document.querySelector('#cold-work-actions-heading')?.closest('section.panel') ?? null;
  const scroller = document.querySelector('.cold-work-actions .data-table__scroll');
  const firstCell = scroller?.querySelector('tbody tr:not([hidden]) > :first-child') ?? scroller?.querySelector('thead th');
  const firstHead = scroller?.querySelector('thead th');
  const rows = [...document.querySelectorAll('[data-cold-work-row]')].filter((r) => !r.hidden);
  // Text lines of an element, from a Range over its contents (a block box has one client rect however it wraps).
  const lines = (e) => {
    const range = document.createRange();
    range.selectNodeContents(e);
    const tops = [...range.getClientRects()].filter((r) => r.width > 0).map((r) => r.top).sort((a, b) => a - b);
    return tops.reduce((n, t, i) => (i === 0 || t - tops[i - 1] > 4 ? n + 1 : n), 0);
  };
  const badges = [...document.querySelectorAll('[data-cold-work-row]:not([hidden]) [data-cold-work-state]')];
  return {
    href: location.pathname + location.search,
    panelState: document.querySelector('[data-cold-work-state-panel]')?.getAttribute('data-cold-work-state-panel') ?? null,
    currentness: document.querySelector('[data-cold-work-currentness]')?.getAttribute('data-cold-work-currentness') ?? null,
    scope: document.querySelector('[data-site-work-scope]')?.textContent?.trim() ?? null,
    docScrollWidth: document.documentElement.scrollWidth,
    docClientWidth: document.documentElement.clientWidth,
    docHeight: document.documentElement.scrollHeight,
    main: h(main),
    strip: h(document.querySelector('[data-cold-work-strip]')),
    panel: h(panel),
    currentnessNotice: h(document.querySelector('[data-cold-work-currentness]')),
    contextNotice: h(document.querySelector('[data-cold-work-notice]')),
    scrollerScrollWidth: scroller?.scrollWidth ?? null,
    scrollerClientWidth: scroller?.clientWidth ?? null,
    stickyFirstColumn: firstCell ? getComputedStyle(firstCell).position === 'sticky' : null,
    stickyHead: firstHead ? getComputedStyle(firstHead).position === 'sticky' : null,
    rowCount: rows.length,
    rowsTotal: document.querySelectorAll('[data-cold-work-row]').length,
    rows: rows.map((r) => {
      const codes = [...r.querySelectorAll('.cold-work-code')];
      return { id: r.getAttribute('data-cold-work-row'), codes: codes.map((c) => ({ text: c.textContent.trim().slice(0, 48), lines: lines(c) })),
        codeOneLine: codes.length > 0 && codes.every((c) => lines(c) === 1), height: h(r),
        summaryLines: [...r.querySelectorAll('summary')].map((x) => lines(x)) };
    }),
    badgesClipped: badges.filter((b) => b.scrollWidth > b.clientWidth + 1).length,
    badgeCount: badges.length,
    showAll: document.querySelector('[data-cold-work-show-all]')?.textContent?.trim() ?? null,
    next: document.querySelector('[data-cold-work-next]')?.getAttribute('href') ?? null,
    first: Boolean(document.querySelector('[data-cold-work-first]')),
    disclosures: document.querySelectorAll('details[data-disclosure^="cold-work-title-"]').length,
    openDisclosures: document.querySelectorAll('details[data-disclosure^="cold-work-title-"][open]').length,
    refusal: document.querySelector('[data-cold-work-refusal]')?.getAttribute('data-cold-work-refusal') ?? null,
    refusalMessage: document.querySelector('[data-cold-work-refusal-message]')?.textContent?.trim() ?? null,
    retryVisible: (() => { const b = document.querySelector('[data-cold-work-retry]'); if (!b) return null; const r = b.getBoundingClientRect(); return r.width > 0 && r.height > 0 && r.right <= document.documentElement.clientWidth; })(),
    siteRefusal: main ? null : (document.querySelector('main')?.innerText?.replace(/\\s+/g, ' ').trim().slice(0, 200) ?? null),
    pageMain: h(document.querySelector('main')),
    empty: document.querySelector('[data-cold-work-empty]')?.innerText?.replace(/\\s+/g, ' ').trim() ?? null,
  };
})()`;
const MEASURE_ACTION = `(() => {
  const h = (e) => (e ? Math.round(e.getBoundingClientRect().height) : null);
  const main = document.querySelector('main[data-domain-action-shell]');
  return {
    href: location.pathname + location.search,
    shell: main?.getAttribute('data-domain-action-shell') ?? null,
    panelState: document.querySelector('[data-domain-action-panel]')?.getAttribute('data-domain-action-panel') ?? null,
    heading: document.querySelector('main h1')?.textContent?.trim() ?? null,
    docScrollWidth: document.documentElement.scrollWidth,
    docClientWidth: document.documentElement.clientWidth,
    docHeight: document.documentElement.scrollHeight,
    main: h(main),
    strip: h(document.querySelector('[data-domain-action-strip]')),
    panel: h(document.querySelector('[data-domain-action-panel]')),
    notice: h(document.querySelector('[data-domain-action-notice]')),
    currentnessNotice: h(document.querySelector('[data-domain-action-currentness]')),
    panelText: document.querySelector('[data-domain-action-panel]')?.innerText?.replace(/\\s+/g, ' ').trim().slice(0, 240) ?? null,
  };
})()`;
const workUrl = (base, query, extra = {}) => `${base}/sites/${SITE}/work?${new URLSearchParams({ ...query, ...extra }).toString()}`;

function capWork(W, label, m, wi, notices = true) {
  const caps = WORK_CAPS;
  claim(`${W} ${label}: no document horizontal overflow`, m.docScrollWidth <= m.docClientWidth, { scrollWidth: m.docScrollWidth, clientWidth: m.docClientWidth });
  claim(`${W} ${label}: page main <= ${caps.main[wi]}`, m.main !== null && m.main <= caps.main[wi], m.main);
  claim(`${W} ${label}: strip <= ${caps.strip[wi]}`, m.strip !== null && m.strip <= caps.strip[wi], m.strip);
  claim(`${W} ${label}: panel <= ${caps.panel[wi]}`, m.panel !== null && m.panel <= caps.panel[wi], m.panel);
  if (notices) {
    claim(`${W} ${label}: context notice <= ${caps.notice[wi]}`, m.contextNotice !== null && m.contextNotice <= caps.notice[wi], m.contextNotice);
    if (m.currentnessNotice !== null) claim(`${W} ${label}: currentness notice <= ${caps.notice[wi]}`, m.currentnessNotice <= caps.notice[wi], m.currentnessNotice);
  }
}
function rowClaims(W, label, m, expectRows) {
  claim(`${W} ${label}: ${expectRows} visible row(s) measured`, m.rowCount === expectRows && m.rows.length > 0, m.rowCount);
  claim(`${W} ${label}: every row's code is on one line`, m.rows.length > 0 && m.rows.every((r) => r.codeOneLine), m.rows.map((r) => r.codes.map((c) => c.lines)));
  const summaries = m.rows.flatMap((r) => r.summaryLines);
  if (summaries.length > 0) claim(`${W} ${label}: every 'Read full text' summary is on one line`, summaries.every((n) => n === 1), summaries);
  claim(`${W} ${label}: first column is position:sticky`, m.stickyFirstColumn === true, m.stickyFirstColumn);
  claim(`${W} ${label}: no clipped State badge`, m.badgeCount > 0 && m.badgesClipped === 0, { badges: m.badgeCount, clipped: m.badgesClipped });
  if (W === "narrow") claim(`${W} ${label}: table scrolls inside its panel`, m.scrollerScrollWidth > m.scrollerClientWidth, { scrollWidth: m.scrollerScrollWidth, clientWidth: m.scrollerClientWidth });
}

async function record(W, wi, state, url, ready, measure, afterLoad) {
  const ok = await go(url, ready);
  if (afterLoad) await afterLoad();
  const m = await js(measure);
  claim(`${W} ${state}: settled`, ok, m.panelState ?? m.shell);
  const file = await shot(`w502b-${W}-${state}`);
  captures.push({ state, width: WIDTHS[wi][1], file, url, measurements: m });
  return m;
}

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
  const P = manifest.modes.positive;
  const WC = manifest.modes.worstcase;
  const pBase = `${HOST}:${8971 - 3500}`;
  const portOf = { positive: 8971, worstcase: 8972, pending: 8973, stale: 8974, unknown: 8975 };
  const B = (k) => `${HOST}:${portOf[k] - 3500}`;
  const forbidden = manifest.processes.forbidden;
  const unavailable = manifest.processes.unavailable;
  const fBase = `${HOST}:${Number(new URL(forbidden.api_base).port) - 3500}`;
  const uBase = `${HOST}:${Number(new URL(unavailable.api_base).port) - 3500}`;
  const positiveAction = P.actions[0].id;
  const NOT_FOUND = "00000000-0000-4000-8000-0000000000aa";

  for (const [wi, [W, width, height]] of WIDTHS.entries()) {
    await size(width, height);
    let m;
    // Positive CURRENT, one row.
    m = await record(W, wi, "positive", workUrl(pBase, P.reads.positive.query), WORK_READY, MEASURE_WORK);
    claim(`${W} positive: rows panel, CURRENT`, m.panelState === "rows" && m.currentness === null, { panel: m.panelState, currentness: m.currentness });
    capWork(W, "positive", m, wi);
    rowClaims(W, "positive", m, 1);
    // Complete zero.
    m = await record(W, wi, "zero", workUrl(pBase, P.reads.zero.query), WORK_READY, MEASURE_WORK);
    claim(`${W} zero: empty panel`, m.panelState === "empty" && m.rowCount === 0, { panel: m.panelState, empty: m.empty });
    capWork(W, "zero", m, wi);
    // Historical (known_at = K3).
    m = await record(W, wi, "historical", workUrl(pBase, P.reads.historical.query), WORK_READY, MEASURE_WORK);
    claim(`${W} historical: HISTORICAL notice`, m.currentness === "HISTORICAL" && m.panelState === "rows", m.currentness);
    capWork(W, "historical", m, wi);
    rowClaims(W, "historical", m, 1);
    // Worst case page 1, folded.
    const wq = WC.reads.worstcase.query;
    m = await record(W, wi, "worstcase-folded", workUrl(B("worstcase"), wq), WORK_READY, MEASURE_WORK);
    claim(`${W} worstcase-folded: 'Show all 5 Actions' visible`, m.showAll === "Show all 5 Actions", m.showAll);
    claim(`${W} worstcase-folded: 5 rows on page, 4 visible`, m.rowsTotal === 5, { total: m.rowsTotal, visible: m.rowCount });
    capWork(W, "worstcase-folded", m, wi);
    rowClaims(W, "worstcase-folded", m, 4);
    // Worst case expanded.
    m = await record(W, wi, "worstcase-expanded", workUrl(B("worstcase"), wq), WORK_READY, MEASURE_WORK, async () => {
      await js(`document.querySelector('[data-cold-work-show-all]').click()`);
      await waitFor(`!document.querySelector('[data-cold-work-show-all]')`);
      await sleep(300);
    });
    capWork(W, "worstcase-expanded", m, wi);
    rowClaims(W, "worstcase-expanded", m, 5);
    // Worst case, one long-title disclosure open (folded page).
    m = await record(W, wi, "worstcase-disclosure", workUrl(B("worstcase"), wq), WORK_READY, MEASURE_WORK, async () => {
      await js(`document.querySelector('details[data-disclosure^="cold-work-title-"] > summary').click()`);
      await waitFor(`document.querySelector('details[data-disclosure^="cold-work-title-"][open]')`);
      await sleep(300);
    });
    claim(`${W} worstcase-disclosure: one disclosure open`, m.openDisclosures === 1, { open: m.openDisclosures, of: m.disclosures });
    capWork(W, "worstcase-disclosure", m, wi);
    rowClaims(W, "worstcase-disclosure", m, 4);
    const next = m.next;
    claim(`${W} worstcase: Next page link present`, Boolean(next), next);
    // Worst case Next page (cursor).
    if (next) {
      m = await record(W, wi, "worstcase-next", `${B("worstcase")}${next}`, WORK_READY, MEASURE_WORK);
      claim(`${W} worstcase-next: cursor + known_at in URL, First page link`, /cursor=/.test(m.href) && /known_at=/.test(m.href) && m.first, m.href);
      capWork(W, "worstcase-next", m, wi);
      rowClaims(W, "worstcase-next", m, 1);
    }
    // PENDING / STALE / UNKNOWN.
    for (const [k, status] of [["pending", "PENDING_RECOMPUTE"], ["stale", "STALE_SOURCE"], ["unknown", "UNKNOWN"]]) {
      const mode = manifest.modes[k];
      m = await record(W, wi, k, workUrl(B(k), mode.reads[k].query), WORK_READY, MEASURE_WORK);
      claim(`${W} ${k}: ${status} notice`, m.currentness === status && m.panelState === "rows", m.currentness);
      capWork(W, k, m, wi);
      rowClaims(W, k, m, 1);
    }
    // 403 / 503.
    for (const [k, b, proc] of [["forbidden-403", fBase, forbidden], ["unavailable-503", uBase, unavailable]]) {
      m = await record(W, wi, k, workUrl(b, proc.query), WORK_READY, MEASURE_WORK);
      if (m.siteRefusal) claim(`${W} ${k}: page states a refusal (Site frame), no rows`, m.rowCount === 0, { main: m.siteRefusal, height: m.pageMain });
      claim(`${W} ${k}: refused panel ${proc.expected.code}`, m.panelState === "refused" && m.refusal === proc.expected.code, { panel: m.panelState, refusal: m.refusal, message: m.refusalMessage });
      if (m.siteRefusal) {
        claim(`${W} ${k}: no document horizontal overflow`, m.docScrollWidth <= m.docClientWidth, { scrollWidth: m.docScrollWidth, clientWidth: m.docClientWidth });
        continue;
      }
      claim(`${W} ${k}: Retry visible`, m.retryVisible === true, m.retryVisible);
      claim(`${W} ${k}: no row and no mock zero`, m.rowCount === 0 && !/^0\b/.test(m.scope ?? ""), { rows: m.rowCount, scope: m.scope });
      capWork(W, k, m, wi);
    }
    // Domain Action shell: positive Action and a not-found ID.
    for (const [k, id] of [["action-positive", positiveAction], ["action-not-found", NOT_FOUND]]) {
      m = await record(W, wi, k, `${pBase}/sites/${SITE}/actions/${id}/verification`, ACTION_READY, MEASURE_ACTION);
      const want = k === "action-positive" ? ["loaded", "preparing"] : ["not_found", "not-found"];
      claim(`${W} ${k}: shell/panel state`, m.shell === want[0] && m.panelState === want[1], { shell: m.shell, panel: m.panelState });
      claim(`${W} ${k}: no document horizontal overflow`, m.docScrollWidth <= m.docClientWidth, { scrollWidth: m.docScrollWidth, clientWidth: m.docClientWidth });
      claim(`${W} ${k}: page main <= ${ACTION_CAPS.main[wi]}`, m.main !== null && m.main <= ACTION_CAPS.main[wi], m.main);
      if (m.strip !== null) claim(`${W} ${k}: strip <= ${ACTION_CAPS.strip[wi]}`, m.strip <= ACTION_CAPS.strip[wi], m.strip);
      if (m.notice !== null) claim(`${W} ${k}: notice <= ${ACTION_CAPS.notice[wi]}`, m.notice <= ACTION_CAPS.notice[wi], m.notice);
    }
  }
  const failed = results.filter((r) => !r.ok).length;
  writeFileSync(join(OUT, "w502b-measurements.json"), JSON.stringify({ manifest_revision: manifest.revision, caps: { work: WORK_CAPS, action: ACTION_CAPS }, captures, claims: results, failed }, null, 2));
  console.log(`${results.length - failed} PASS, ${failed} FAIL`);
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
