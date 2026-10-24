/**
 * W5-04 V2b browser evidence: the EV_CHARGING Site Work > Actions tab (`ev-work`) at 1440 and 390 px, measured against
 * the W5-04 build-spec caps (".agent/W5-04-build-spec.md" "Measurements, captures and deviations"; readiness rulings
 * 25, 26, 39, 50-55, 61, 62).
 *
 *   node tools/w504-ev-work-evidence.mjs <manifest.json> <out-dir> [web-host]
 *
 * <manifest.json> is the V1b walkthrough manifest (`tools/w504_ev_work_walkthrough.py prepare|serve|attest`): per-mode
 * Action IDs, Work window W, clocks, posted bodies and `processes.<name>.port`. Each API at port P is served by a Vite
 * dev server at P - 3500 on <web-host> (default http://localhost), started separately with `ASSETOPS_API_PORT=P`.
 *
 * Phase A, per width (producer state as prepared and attested):
 *   positive (W, CURRENT, the one seeded Action), historical (W + known_at = the manifest's own index read clock),
 *   zero (zero-mode DB, the complete-zero day before W), forbidden-403 (a principal granted no Site: real 403 in the
 *   Actions panel with a healthy Site read), unavailable-503 (the walkthrough's stopped API: the browser proxy fails
 *   every read, so this is a Site-level refusal, recorded as such) and window-error (a user-opened invalid Window,
 *   ruling 51: measured and reported, exempt from height caps).
 * Phase B, per width, on the walkthrough's own `worstcase` mode (pre-flight 23: V1b's walkthrough produces every
 *   fixture and this `.mjs` only captures; re-review M1): worst-folded (closed: four visible rows, `Show all 5 Actions`, every cap) and worst-expanded
 *   (Show all plus every `Read full text` open: ruling 26 exempts page/panel/strip heights; full text, containment,
 *   one-line codes and zero document overflow stay gated).
 *
 * W5-04 V3b, `W504B_EVIDENCE=cases`: the EV Incidents and Maintenance tabs (`ev-work-incidents`, `ev-work-maintenance`)
 *   per width and kind: submitted (the attested INC/WR + record + explicit case links), submitted-ids-open (every row
 *   disclosure open; exempt), historical, zero, forbidden-403 (W4 refusal in the case panel), worst (the walkthrough's
 *   five long rows, closed), worst-one-open (one `Read full text`; 390 cap 680) and worst-all-open (exempt). Writes
 *   <out>/w504b-cases-measurements.json.
 *
 * Pending, stale and unknown are not producer states (manifest `status: unavailable`, ruling 54): they are recorded
 * here as unavailable captures and remain pure component vectors (`frontend/src/sites/__tests__/evWorkActions.test.tsx`).
 * Every claim prints PASS/FAIL with its measured value; row claims require a non-empty measured row set. Writes
 * <out>/w504b-measurements.json. It launches and stops only its own headless Chrome.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { widthGuard } from "./evidence-checks.mjs";

const MANIFEST = process.argv[2];
const OUT = process.argv[3];
const HOST = process.argv[4] ?? "http://localhost";
if (!MANIFEST || !OUT) throw new Error("usage: see the header of tools/w504-ev-work-evidence.mjs");
const manifest = JSON.parse(readFileSync(MANIFEST, "utf-8"));
const SITE = manifest.site.code;
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9481);
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  ["desktop", 1440, 1000],
  ["narrow", 390, 900],
];
// Build spec "Measurements" caps [1440, 390]; ruling 50 adds the successful-zero Actions panel cap.
// Ruling 50 also caps the closed non-loaded (refused) state panel at 360/590 (re-review Low-1).
const CAPS = { main: [1600, 2000], strip: [100, 150], panel: [650, 850], zeroPanel: [460, 560], statePanel: [360, 590], notice: [110, 160] };
mkdirSync(OUT, { recursive: true });

const profile = mkdtempSync(join(tmpdir(), "assetops-w504b-cdp-"));
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
function info(name, detail) {
  results.push({ name, ok: true, info: true, detail });
  console.log(`INFO  ${name}  ${JSON.stringify(detail)}`);
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
    const timer = setTimeout(() => reject(new Error(`timeout ${method}`)), Number(process.env.W504B_CDP_TIMEOUT_MS ?? 60000));
    pending.set(id, (msg) => {
      clearTimeout(timer);
      msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
    });
    ws.send(JSON.stringify({ id, method, params }));
  });
}
async function js(expression) {
  // V3b: under a loaded machine an evaluation issued while a navigation commits can stay unanswered; retry it
  // (bounded) instead of waiting out the whole CDP timeout. Expressions here are read-only or idempotent.
  let r;
  for (let attempt = 1; ; attempt += 1) {
    const call = send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
    call.catch(() => {});
    r = await Promise.race([call, sleep(20000).then(() => null)]);
    if (r !== null) break;
    if (attempt >= 5) throw new Error("Runtime.evaluate unanswered after 5 attempts");
    console.log(`INFO  evaluate retry ${attempt}`);
  }
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

const READY = `(document.querySelector('[data-domain-work-state-panel]') && !document.querySelector('[data-domain-work-state-panel="loading"]')) || /unavailable|could not|not reachable/i.test(document.querySelector('main')?.innerText ?? '') && !document.querySelector('main[data-domain-work-page]')`;
const setDate = (selector, value) => `(() => { const el = document.querySelector('${selector}'); const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set; set.call(el, '${value}'); el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); return el.value; })()`;
const MEASURE = `(() => {
  const h = (e) => (e ? Math.round(e.getBoundingClientRect().height) : null);
  const main = document.querySelector('main[data-domain-work-page="actions"]');
  const panel = document.querySelector('#ev-work-actions-heading')?.closest('section.panel') ?? null;
  const scroller = document.querySelector('.domain-work-actions .data-table__scroll');
  const firstCell = scroller?.querySelector('tbody tr:not([hidden]) > :first-child') ?? scroller?.querySelector('thead th');
  const rows = [...document.querySelectorAll('[data-domain-work-row]')].filter((r) => !r.hidden);
  const lines = (e) => {
    const range = document.createRange();
    range.selectNodeContents(e);
    const tops = [...range.getClientRects()].filter((r) => r.width > 0).map((r) => r.top).sort((a, b) => a - b);
    return tops.reduce((n, t, i) => (i === 0 || t - tops[i - 1] > 4 ? n + 1 : n), 0);
  };
  const badges = [...document.querySelectorAll('[data-domain-work-row]:not([hidden]) [data-domain-work-state]')];
  const coldNames = [...document.querySelectorAll('main, main *')].flatMap((el) => [...el.attributes]
    .filter((a) => a.name.startsWith('data-cold-work') || (a.name === 'class' && /\\bcold-work/.test(a.value)) || (a.name === 'data-disclosure' && a.value.startsWith('cold-work')))
    .map((a) => a.name));
  return {
    href: location.pathname + location.search,
    h1: document.querySelector('main h1')?.textContent?.trim() ?? null,
    subtitle: document.querySelector('main header')?.innerText?.includes('EV charging operations at this site.') ?? false,
    panelState: document.querySelector('[data-domain-work-state-panel]')?.getAttribute('data-domain-work-state-panel') ?? null,
    currentness: document.querySelector('[data-domain-work-currentness]')?.getAttribute('data-domain-work-currentness') ?? null,
    currentnessText: document.querySelector('[data-domain-work-currentness]')?.innerText?.trim() ?? null,
    scope: document.querySelector('[data-site-work-scope]')?.textContent?.replace(/\\s+/g, ' ').trim() ?? null,
    stripText: document.querySelector('[data-domain-work-strip]')?.innerText?.replace(/\\s+/g, ' ').trim() ?? null,
    stripLinks: document.querySelectorAll('[data-domain-work-strip] a').length,
    panelDescription: panel?.querySelector('.panel__description')?.textContent?.trim() ?? null,
    subtabs: [...document.querySelectorAll('.site-subtabs a')].map((a) => ({ text: a.textContent.trim(), href: a.getAttribute('href') })),
    docScrollWidth: document.documentElement.scrollWidth,
    docClientWidth: document.documentElement.clientWidth,
    docHeight: document.documentElement.scrollHeight,
    main: h(main),
    strip: h(document.querySelector('[data-domain-work-strip]')),
    panel: h(panel),
    currentnessNotice: h(document.querySelector('[data-domain-work-currentness]')),
    contextNotice: h(document.querySelector('[data-domain-work-notice]')),
    scrollerScrollWidth: scroller?.scrollWidth ?? null,
    scrollerClientWidth: scroller?.clientWidth ?? null,
    stickyFirstColumn: firstCell ? getComputedStyle(firstCell).position === 'sticky' : null,
    rowCount: rows.length,
    rowsTotal: document.querySelectorAll('[data-domain-work-row]').length,
    anchorsInEvRows: document.querySelectorAll('[data-domain-work-row][data-domain-work-domain="EV_CHARGING"] td a').length,
    actionHrefs: [...document.querySelectorAll('main a')].map((a) => a.getAttribute('href') ?? '').filter((x) => /\\/actions\\//.test(x)),
    coldNames: coldNames.length,
    rows: rows.map((r) => {
      const codes = [...r.querySelectorAll('.domain-work-code')];
      const cells = [...r.querySelectorAll('td')];
      return { id: r.getAttribute('data-domain-work-row'), codeOneLine: codes.length > 0 && codes.every((c) => lines(c) === 1),
        codes: codes.map((c) => ({ text: c.textContent.trim().slice(0, 48), lines: lines(c) })), height: h(r),
        source: r.querySelector('[data-domain-work-source]')?.textContent?.trim() ?? null,
        cellText: cells.map((c) => c.innerText.replace(/\\s+/g, ' ').trim().slice(0, 60)),
        summaryLines: [...r.querySelectorAll('summary')].map((x) => lines(x)) };
    }),
    cells: rows.flatMap((r) => [...r.querySelectorAll('td')]).map((td) => {
      const box = td.getBoundingClientRect();
      const inside = (e) => { const b = e.getBoundingClientRect(); return b.width === 0 || (b.left >= box.left - 1 && b.right <= box.right + 1); };
      const lineBox = (e) => { const cs = getComputedStyle(e); const lh = parseFloat(cs.lineHeight); return Number.isFinite(lh) && lh > 0 ? lh : parseFloat(cs.fontSize) * 1.2; };
      const previews = [...td.querySelectorAll('.work-cases-clamp')];
      const bodies = [...td.querySelectorAll('details[open] .disclosure__body')];
      return { col: td.cellIndex, fits: td.scrollWidth <= td.clientWidth + 1, kidsInside: [...td.querySelectorAll('*')].every(inside),
        clampFits: previews.every((c) => c.scrollWidth <= c.clientWidth + 1),
        previewLines: previews.map((c) => Math.round(c.getBoundingClientRect().height / lineBox(c))),
        openBodyInside: bodies.every(inside), openBodyFits: bodies.every((b) => b.scrollWidth <= b.clientWidth + 1), openBodies: bodies.length,
        openText: bodies.map((b) => b.textContent.length) };
    }),
    badgesClipped: badges.filter((b) => b.scrollWidth > b.clientWidth + 1).length,
    badgeCount: badges.length,
    badgeLines: badges.map((x) => lines(x)),
    showAll: document.querySelector('[data-domain-work-show-all]')?.textContent?.trim() ?? null,
    titleDisclosures: document.querySelectorAll('details[data-disclosure^="domain-work-title-"]').length,
    openTitleDisclosures: document.querySelectorAll('details[data-disclosure^="domain-work-title-"][open]').length,
    refusal: document.querySelector('[data-domain-work-refusal]')?.getAttribute('data-domain-work-refusal') ?? null,
    refusalText: document.querySelector('[data-domain-work-refusal]')?.innerText?.replace(/\\s+/g, ' ').trim() ?? null,
    refusalMessage: document.querySelector('[data-domain-work-refusal-message]')?.textContent?.trim() ?? null,
    retryVisible: (() => { const b = document.querySelector('[data-domain-work-retry]'); if (!b) return null; const r = b.getBoundingClientRect(); return r.width > 0 && r.height > 0 && r.right <= document.documentElement.clientWidth; })(),
    siteRefusal: main ? null : (document.querySelector('main')?.innerText?.replace(/\\s+/g, ' ').trim().slice(0, 200) ?? null),
    pageMain: h(document.querySelector('main')),
    empty: document.querySelector('[data-domain-work-empty]')?.innerText?.replace(/\\s+/g, ' ').trim() ?? null,
    window: (() => {
      const form = document.querySelector('[data-domain-work-window]');
      if (!form) return null;
      const box = form.getBoundingClientRect();
      const pe = form.parentElement;
      const ps = getComputedStyle(pe);
      const pr = pe.getBoundingClientRect();
      const parent = { left: pr.left + parseFloat(ps.borderLeftWidth) + parseFloat(ps.paddingLeft), width: pe.clientWidth - parseFloat(ps.paddingLeft) - parseFloat(ps.paddingRight) };
      const apply = form.querySelector('[data-domain-work-window-apply]')?.getBoundingClientRect();
      const err = form.querySelector('[data-domain-work-window-error]');
      return {
        afterSubtabs: form.previousElementSibling?.matches('nav[aria-label="Work lists"]') === true,
        beforeStrip: form.nextElementSibling?.querySelector(':scope > [data-domain-work-strip]') !== null && form.nextElementSibling !== null,
        labels: form.innerText.replace(/\\s+/g, ' ').trim(),
        from: form.querySelector('[data-domain-work-window-from]')?.value ?? null,
        to: form.querySelector('[data-domain-work-window-to]')?.value ?? null,
        width: Math.round(box.width), parentWidth: Math.round(parent.width), height: Math.round(box.height),
        rightGap: apply ? Math.round(box.right - apply.right) : null,
        leftGap: Math.round(box.left - parent.left),
        error: err?.textContent?.trim() ?? null,
        errorInside: err ? (() => { const b = err.getBoundingClientRect(); return b.left >= box.left - 1 && b.right <= box.right + 1; })() : null,
      };
    })(),
  };
})()`;

function caps(W, label, m, wi, { panelCap = CAPS.panel, heights = true } = {}) {
  claim(`${W} ${label}: no document horizontal overflow (scrollWidth <= clientWidth + 1)`, m.docScrollWidth <= m.docClientWidth + 1, { scrollWidth: m.docScrollWidth, clientWidth: m.docClientWidth });
  claim(`${W} ${label}: no cold-named attribute, class or disclosure on the EV page (ruling 45)`, m.coldNames === 0, m.coldNames);
  if (!heights) {
    info(`${W} ${label}: expanded heights (ruling 26/51 exempt)`, { main: m.main, strip: m.strip, panel: m.panel, docHeight: m.docHeight });
    return;
  }
  claim(`${W} ${label}: page main <= ${CAPS.main[wi]}`, m.main !== null && m.main <= CAPS.main[wi], { main: m.main, docHeight: m.docHeight });
  claim(`${W} ${label}: strip <= ${CAPS.strip[wi]}`, m.strip !== null && m.strip <= CAPS.strip[wi], m.strip);
  if (panelCap) claim(`${W} ${label}: panel <= ${panelCap[wi]}`, m.panel !== null && m.panel <= panelCap[wi], { panel: m.panel, tableScrollWidth: m.scrollerScrollWidth, tableClientWidth: m.scrollerClientWidth });
  claim(`${W} ${label}: context notice <= ${CAPS.notice[wi]}`, m.contextNotice !== null && m.contextNotice <= CAPS.notice[wi], m.contextNotice);
  if (m.currentnessNotice !== null) claim(`${W} ${label}: currentness notice <= ${CAPS.notice[wi]}`, m.currentnessNotice <= CAPS.notice[wi], m.currentnessNotice);
}
function rowClaims(W, label, m, expectRows) {
  claim(`${W} ${label}: ${expectRows} visible row(s) measured`, m.rowCount === expectRows && m.rows.length > 0, m.rowCount);
  claim(`${W} ${label}: every row's code is on one line`, m.rows.length > 0 && m.rows.every((r) => r.codeOneLine), m.rows.map((r) => r.codes.map((c) => c.lines)));
  claim(`${W} ${label}: EV Action codes are plain text (R113), no /actions/ href on the page`, m.anchorsInEvRows === 0 && m.actionHrefs.length === 0, { anchors: m.anchorsInEvRows, hrefs: m.actionHrefs });
  const summaries = m.rows.flatMap((r) => r.summaryLines);
  if (summaries.length > 0) claim(`${W} ${label}: every disclosure summary is on one line`, summaries.every((n) => n === 1), summaries);
  claim(`${W} ${label}: every row cell contains its content`, m.cells.length > 0 && m.cells.every((c) => c.fits && c.kidsInside && c.clampFits), m.cells.filter((c) => !(c.fits && c.kidsInside && c.clampFits)));
  if (m.cells.some((c) => c.openBodies > 0)) claim(`${W} ${label}: every opened disclosure body stays inside its cell with no horizontal clip`, m.cells.every((c) => c.openBodyInside && c.openBodyFits), m.cells.filter((c) => !(c.openBodyInside && c.openBodyFits)));
  const previews = m.cells.flatMap((c) => c.previewLines);
  if (previews.length > 0) claim(`${W} ${label}: every long-text preview is at most two lines`, previews.every((n) => n >= 1 && n <= 2), previews);
  claim(`${W} ${label}: first column is position:sticky`, m.stickyFirstColumn === true, m.stickyFirstColumn);
  claim(`${W} ${label}: no clipped State badge, each on one line`, m.badgeCount > 0 && m.badgesClipped === 0 && m.badgeLines.every((n) => n === 1), { badges: m.badgeCount, clipped: m.badgesClipped, lines: m.badgeLines });
  if (W === "narrow") claim(`${W} ${label}: table scrolls inside its panel`, m.scrollerScrollWidth > m.scrollerClientWidth, { scrollWidth: m.scrollerScrollWidth, clientWidth: m.scrollerClientWidth });
}
function windowClaims(W, label, m, wi, want) {
  const w = m.window;
  claim(`${W} ${label}: Window control after the Work subtabs and before the scope strip (R112)`, w !== null && w.afterSubtabs && w.beforeStrip, w);
  if (w === null) return;
  claim(`${W} ${label}: Window labels are From (UTC) / To (UTC, exclusive) (R77)`, /From \(UTC\)/.test(w.labels) && /To \(UTC, exclusive\)/.test(w.labels), w.labels);
  if (want) claim(`${W} ${label}: Window shows the selected from/to dates`, w.from === want.from && w.to === want.to, { from: w.from, to: w.to, want });
  if (wi === 0) claim(`${W} ${label}: Window control right-aligned`, w.rightGap !== null && w.rightGap <= 1, { rightGap: w.rightGap });
  else claim(`${W} ${label}: Window control full width`, w.width >= w.parentWidth - 1 && w.leftGap <= 1, { width: w.width, parent: w.parentWidth, leftGap: w.leftGap });
}
async function record(W, wi, state, url, afterLoad) {
  const ok = await go(url, READY);
  if (afterLoad) await afterLoad();
  const m = await js(MEASURE);
  claim(`${W} ${state}: settled`, ok, m.panelState ?? m.siteRefusal);
  const file = await shot(`w504b-${W}-${state}`);
  captures.push({ state, width: WIDTHS[wi][1], file, url, measurements: m });
  return m;
}

const P = manifest.modes.positive;
const Z = manifest.modes.zero;
const WC = manifest.modes.worstcase;
const proc = manifest.processes ?? {};
const base = (name) => `${HOST}:${proc[name].port - 3500}`;
const q = (params) => new URLSearchParams(params).toString();
const W_ = P.work_window_W;
const dayBefore = (iso) => new Date(Date.parse(iso) - 86400000).toISOString().replace(".000Z", "Z");

// ---- W5-04 V3b: `W504B_EVIDENCE=cases` (EV Incidents / Maintenance, v69 `ev-work-incidents`, `ev-work-maintenance`) --
// Build spec "Measurements" and readiness rulings 25/26: populated case panel 650/650 (one open preview at 390: 680),
// empty case panel with the closed basis 460/560, Work page 1600/2000, strip 100/150, notice 110/160. A W4 case refusal
// keeps its titled case panel, so it is measured against the populated case-panel cap (the W5-02 K3b cold precedent).
// Every row is a walkthrough row (pre-flight 23): `positive` after `attest` (the submitted INC/WR + record + explicit
// domain Action case links), `zero`, `worstcase` (five long INC and five long WR from the walkthrough) and `forbidden`.
const CASE_CAPS = { main: [1600, 2000], strip: [100, 150], panel: [650, 650], panelOneOpen: [650, 680], emptyPanel: [460, 560], notice: [110, 160] };
// Every cases-mode state renders the case panel (no Site-level refusal is captured here), so only a settled case panel counts.
const CASE_READY = `document.querySelector('.work-cases [data-work-loaded], .work-cases [data-work-empty], .work-cases [data-work-refused]')`;
const caseMeasure = (kind) => `(() => {
  const h = (e) => (e ? Math.round(e.getBoundingClientRect().height) : null);
  const main = document.querySelector('main');
  const body = document.querySelector('.work-cases');
  const panel = document.querySelector('#site-work-${kind}-heading')?.closest('section.panel') ?? null;
  const scroller = document.querySelector('.work-cases .data-table__scroll');
  const firstCell = scroller?.querySelector('tbody tr > :first-child') ?? scroller?.querySelector('thead th');
  const rows = [...document.querySelectorAll('[data-work-row]')];
  const lines = (e) => {
    const range = document.createRange();
    range.selectNodeContents(e);
    const tops = [...range.getClientRects()].filter((r) => r.width > 0).map((r) => r.top).sort((a, b) => a - b);
    return tops.reduce((n, t, i) => (i === 0 || t - tops[i - 1] > 4 ? n + 1 : n), 0);
  };
  const coldNames = [...document.querySelectorAll('main, main *')].flatMap((el) => [...el.attributes]
    .filter((a) => a.name.startsWith('data-cold-') || (a.name === 'class' && /\\bcold-work/.test(a.value)) || (a.name === 'data-disclosure' && a.value.startsWith('cold-work')))
    .map((a) => a.name));
  const badges = [...document.querySelectorAll('[data-work-row] [data-work-state], [data-work-row] [data-work-outcome]')];
  const window = (() => {
    const form = document.querySelector('form[data-domain-work-window]');
    if (!form) return null;
    return { afterSubtabs: form.previousElementSibling?.matches('nav.site-subtabs') === true,
      beforeStrip: form.nextElementSibling?.querySelector(':scope > .status-strip') !== null && form.nextElementSibling !== null,
      labels: form.innerText.replace(/\\s+/g, ' ').trim() };
  })();
  return {
    href: location.pathname + location.search,
    h1: document.querySelector('main h1')?.textContent?.trim() ?? null,
    subtitle: document.querySelector('main header')?.innerText?.includes('EV charging operations at this site.') ?? false,
    domainCases: body?.getAttribute('data-domain-cases') ?? null,
    forms: document.querySelectorAll('main form').length,
    w4Form: document.querySelectorAll('main form[data-work-window]').length,
    window,
    scope: document.querySelector('[data-work-scope]')?.textContent?.replace(/\\s+/g, ' ').trim() ?? null,
    stripDetail: document.querySelector('[data-work-strip-detail]')?.textContent?.replace(/\\s+/g, ' ').trim() ?? null,
    manage: (() => { const a = document.querySelector('[data-work-manage-link]'); return a ? { text: a.textContent.trim(), href: a.getAttribute('href') } : null; })(),
    panelDescription: panel?.querySelector('.panel__description')?.textContent?.trim() ?? null,
    headings: [...document.querySelectorAll('.work-cases thead th')].map((t) => t.textContent.trim()),
    currentness: document.querySelector('[data-domain-work-currentness]')?.getAttribute('data-domain-work-currentness') ?? null,
    currentnessText: document.querySelector('[data-domain-work-currentness]')?.innerText?.trim() ?? null,
    currentnessBetween: (() => { const n = document.querySelector('[data-domain-work-currentness]'); return n ? n.previousElementSibling?.classList.contains('status-strip') === true && n.nextElementSibling?.matches('section.panel') === true : null; })(),
    noticeText: document.querySelector('[data-domain-work-notice]')?.innerText?.trim() ?? null,
    docScrollWidth: document.documentElement.scrollWidth,
    docClientWidth: document.documentElement.clientWidth,
    docHeight: document.documentElement.scrollHeight,
    main: h(main),
    strip: h(document.querySelector('.work-cases .status-strip')),
    panel: h(panel),
    currentnessNotice: h(document.querySelector('[data-domain-work-currentness]')),
    contextNotice: h(document.querySelector('[data-domain-work-notice]')),
    scrollerScrollWidth: scroller?.scrollWidth ?? null,
    scrollerClientWidth: scroller?.clientWidth ?? null,
    stickyFirstColumn: firstCell ? getComputedStyle(firstCell).position === 'sticky' : null,
    rowCount: rows.length,
    rowIds: rows.map((r) => r.getAttribute('data-work-row')),
    anchorsHrefs: [...document.querySelectorAll('.work-cases a')].map((a) => a.getAttribute('href') ?? ''),
    actionHrefs: [...document.querySelectorAll('main a')].map((a) => a.getAttribute('href') ?? '').filter((x) => /\\/actions\\//.test(x)),
    actionPlain: document.querySelectorAll('[data-work-action-plain]').length,
    coldNames: coldNames.length,
    rows: rows.map((r) => ({ id: r.getAttribute('data-work-row'), height: h(r),
      title: r.querySelector('[data-work-case-title]')?.innerText?.replace(/\\s+/g, ' ').trim().slice(0, 200) ?? null,
      titleHref: r.querySelector('[data-work-case-title] a')?.getAttribute('href') ?? null,
      window: r.querySelector('[data-work-window]')?.textContent?.trim() ?? null,
      windowLines: (() => { const w = r.querySelector('[data-work-window]'); return w ? lines(w) : null; })(),
      asset: r.querySelector('[data-work-asset]')?.textContent?.trim() ?? null,
      assetGap: /No asset linked/.test(r.querySelectorAll('td')[1]?.innerText ?? ''),
      state: r.querySelector('[data-work-state]')?.textContent?.trim() ?? null,
      outcome: r.querySelector('[data-work-outcome]')?.textContent?.trim() ?? null,
      next: r.querySelector('[data-work-next-evidence]')?.textContent?.trim() ?? null,
      findingCodes: [...r.querySelectorAll('.domain-work-code')].map((c) => lines(c)),
      cellSummaries: [...r.querySelectorAll('td')].map((td) => [...td.querySelectorAll('summary')].map((s) => s.textContent.trim())),
      summaryLines: [...r.querySelectorAll('summary')].map((x) => lines(x)) })),
    cells: rows.flatMap((r) => [...r.querySelectorAll('td')]).map((td) => {
      const box = td.getBoundingClientRect();
      const inside = (e) => { const b = e.getBoundingClientRect(); return b.width === 0 || (b.left >= box.left - 1 && b.right <= box.right + 1); };
      const lineBox = (e) => { const cs = getComputedStyle(e); const lh = parseFloat(cs.lineHeight); return Number.isFinite(lh) && lh > 0 ? lh : parseFloat(cs.fontSize) * 1.2; };
      const previews = [...td.querySelectorAll('.work-cases-clamp')].filter((c) => c.closest('[data-domain-work-longtext]'));
      const bodies = [...td.querySelectorAll('details[open] > .disclosure__body')];
      const codes = [...td.querySelectorAll('details[open] .disclosure__body > code, details[open] .fact-list__value > code')];
      // W5-02c rulings 12/14 (the cold K3b precedent): a UUID code may overflow only inside its own scroller (a
      // direct-code disclosure body or \`.fact-list__value:has(> code)\`), and only while that scroller stays in the cell.
      const codeScroller = (x) => x != null && x.matches('.disclosure__body, .fact-list__value') && x.querySelector(':scope > code') !== null && getComputedStyle(x).overflowX === 'auto';
      const contained = (e) => inside(e) || (e.tagName === 'CODE' && codeScroller(e.parentElement) && inside(e.parentElement));
      const outside = [...td.querySelectorAll('*')].filter((e) => !contained(e));
      return { col: td.cellIndex, fits: td.scrollWidth <= td.clientWidth + 1, kidsInside: outside.length === 0,
        outside: outside.slice(0, 3).map((e) => { const b = e.getBoundingClientRect(); return { tag: e.tagName, cls: e.className, attrs: e.getAttributeNames().join(' '), left: Math.round(b.left - box.left), right: Math.round(b.right - box.right), text: e.textContent.trim().slice(0, 40) }; }),
        clampFits: previews.every((c) => c.scrollWidth <= c.clientWidth + 1),
        previewLines: previews.map((c) => Math.round(c.getBoundingClientRect().height / lineBox(c))),
        openBodyInside: bodies.every(inside), openBodies: bodies.length,
        uuidOneLine: codes.every((c) => lines(c) === 1), uuidScrollerInside: codes.every((c) => codeScroller(c.parentElement) && inside(c.parentElement)), uuids: codes.length,
        fullText: [...td.querySelectorAll('[data-domain-work-longtext="open"] details[open] > .disclosure__body')].map((b) => b.textContent.trim().length) };
    }),
    badgesClipped: badges.filter((b) => b.scrollWidth > b.clientWidth + 1).length,
    badgeCount: badges.length,
    badgeLines: badges.map((x) => lines(x)),
    readFull: document.querySelectorAll('.work-cases [data-domain-work-longtext] > details').length,
    readFullOpen: document.querySelectorAll('.work-cases [data-domain-work-longtext] > details[open]').length,
    showing: document.querySelector('[data-work-showing]')?.textContent?.trim() ?? null,
    basis: [...document.querySelectorAll('.work-cases summary')].some((s) => s.textContent.trim() === 'What this list is based on'),
    basisOpen: [...document.querySelectorAll('.work-cases details[open] > summary')].some((s) => s.textContent.trim() === 'What this list is based on'),
    empty: document.querySelector('[data-work-empty]')?.innerText?.replace(/\\s+/g, ' ').trim() ?? null,
    refused: document.querySelector('[data-work-refused]')?.getAttribute('data-work-refused') ?? null,
    refusedText: document.querySelector('[data-work-refused]')?.innerText?.replace(/\\s+/g, ' ').trim() ?? null,
    siteRefusal: body ? null : (main?.innerText?.replace(/\\s+/g, ' ').trim().slice(0, 200) ?? null),
  };
})()`;

function caseCaps(W, label, m, wi, { panelCap = CASE_CAPS.panel, heights = true } = {}) {
  claim(`${W} ${label}: no document horizontal overflow`, m.docScrollWidth <= m.docClientWidth + 1, { scrollWidth: m.docScrollWidth, clientWidth: m.docClientWidth });
  claim(`${W} ${label}: no cold-named attribute, class or disclosure on the EV page (ruling 45)`, m.coldNames === 0, m.coldNames);
  claim(`${W} ${label}: data-domain-cases="EV_CHARGING", exactly one form (the page-local Window; ruling 57)`, m.domainCases === "EV_CHARGING" && m.forms === 1 && m.w4Form === 0 && m.window !== null, { domainCases: m.domainCases, forms: m.forms, w4Form: m.w4Form });
  claim(`${W} ${label}: Window after the subtabs and before the strip, UTC labels (R112, R77)`, m.window !== null && m.window.afterSubtabs && m.window.beforeStrip && /From \(UTC\)/.test(m.window.labels) && /To \(UTC, exclusive\)/.test(m.window.labels), m.window);
  if (m.currentness !== null) claim(`${W} ${label}: currentness notice between the strip and the panel (R80)`, m.currentnessBetween === true, m.currentnessBetween);
  if (!heights) {
    info(`${W} ${label}: expanded heights (ruling 26 exempt)`, { main: m.main, strip: m.strip, panel: m.panel, docHeight: m.docHeight });
    return;
  }
  claim(`${W} ${label}: page main <= ${CASE_CAPS.main[wi]}`, m.main !== null && m.main <= CASE_CAPS.main[wi], { main: m.main, docHeight: m.docHeight });
  claim(`${W} ${label}: strip <= ${CASE_CAPS.strip[wi]}`, m.strip !== null && m.strip <= CASE_CAPS.strip[wi], m.strip);
  claim(`${W} ${label}: case panel <= ${panelCap[wi]}`, m.panel !== null && m.panel <= panelCap[wi], { panel: m.panel, tableScrollWidth: m.scrollerScrollWidth, tableClientWidth: m.scrollerClientWidth });
  claim(`${W} ${label}: context notice <= ${CASE_CAPS.notice[wi]}`, m.contextNotice !== null && m.contextNotice <= CASE_CAPS.notice[wi], m.contextNotice);
  if (m.currentnessNotice !== null) claim(`${W} ${label}: currentness notice <= ${CASE_CAPS.notice[wi]}`, m.currentnessNotice <= CASE_CAPS.notice[wi], m.currentnessNotice);
}
function caseRowClaims(W, label, m, expectRows) {
  claim(`${W} ${label}: ${expectRows} row(s) measured`, m.rowCount === expectRows && m.rows.length > 0, m.rowCount);
  claim(`${W} ${label}: every row cell contains its content`, m.cells.length > 0 && m.cells.every((c) => c.fits && c.kidsInside && c.clampFits), m.cells.filter((c) => !(c.fits && c.kidsInside && c.clampFits)));
  const previews = m.cells.flatMap((c) => c.previewLines);
  if (previews.length > 0) claim(`${W} ${label}: every long-text preview is at most two lines (R107)`, previews.every((n) => n >= 1 && n <= 2), previews);
  if (m.cells.some((c) => c.openBodies > 0)) claim(`${W} ${label}: every opened disclosure body stays inside its cell`, m.cells.every((c) => c.openBodyInside), m.cells.filter((c) => !c.openBodyInside));
  if (m.cells.some((c) => c.uuids > 0)) claim(`${W} ${label}: every opened UUID is one line in its own contained scroller`, m.cells.every((c) => c.uuidOneLine && c.uuidScrollerInside), m.cells.filter((c) => !(c.uuidOneLine && c.uuidScrollerInside)));
  const summaries = m.rows.flatMap((r) => r.summaryLines);
  if (summaries.length > 0) claim(`${W} ${label}: every disclosure summary is on one line`, summaries.every((n) => n === 1), summaries);
  claim(`${W} ${label}: no clipped state/outcome badge, each on one line`, m.badgeCount > 0 && m.badgesClipped === 0 && m.badgeLines.every((n) => n === 1), { badges: m.badgeCount, clipped: m.badgesClipped, lines: m.badgeLines });
  claim(`${W} ${label}: no /actions/ href on the page (R113: the EV domain Action link is plain)`, m.actionHrefs.length === 0, m.actionHrefs);
  if (W === "narrow") {
    claim(`${W} ${label}: first column is position:sticky`, m.stickyFirstColumn === true, m.stickyFirstColumn);
    claim(`${W} ${label}: table scrolls inside its panel`, m.scrollerScrollWidth > m.scrollerClientWidth, { scrollWidth: m.scrollerScrollWidth, clientWidth: m.scrollerClientWidth });
  }
}
async function caseRecord(W, wi, kind, state, url, afterLoad) {
  // The previous capture's settled DOM would satisfy CASE_READY before the navigation commits: leave it first.
  await send("Page.navigate", { url: "about:blank" });
  await waitFor("location.href === 'about:blank' && document.readyState === 'complete'");
  const ok = await go(url, CASE_READY);
  if (afterLoad) await afterLoad();
  const m = await js(caseMeasure(kind));
  claim(`${W} ${kind} ${state}: settled`, ok, m.refused ?? m.siteRefusal ?? m.rowCount);
  const file = await shot(`w504b-cases-${W}-${kind}-${state}`);
  captures.push({ kind, state, width: WIDTHS[wi][1], file, url, measurements: m });
  return m;
}
const openAll = (selector) => `(() => { const ds = [...document.querySelectorAll(${JSON.stringify(selector)})]; ds.forEach((d) => { d.open = true; d.dispatchEvent(new Event('toggle')); }); return ds.length; })()`;
const KIND_WORDS = {
  incidents: { noun: "incidents", global: "Incidents", columns: ["Case", "Window", "What happened", "Linked findings", "State"], subtitle: "A case links chronology, findings and work without copying them",
    empty: "No incidents at this site No operational case was opened in the selected period. A case comes from a linked chain of events, not from a single data gap." },
  maintenance: { noun: "maintenance", global: "Maintenance", columns: ["Work request", "Asset", "Activity", "Outcome", "Next evidence"], subtitle: "Completed work is activity; the outcome is verified separately",
    empty: "No maintenance work at this site No inspection or repair has been raised here in the selected period." },
};

async function mainCases() {
  const S = P.submitted ?? {};
  const SW = S.work_window_W ?? W_;
  const WCC = WC?.worstcase_cases ?? null;
  claim("manifest: positive attested with the submitted INC, WR, record and two explicit case links (V3b; build spec EV producer)",
    P?.status === "ready" && Boolean(S.incident?.id && S.request?.id && S.record?.id && S.links?.incident && S.links?.request), { incident: S.incident?.id ?? null, request: S.request?.id ?? null, links: Object.keys(S.links ?? {}) });
  claim("manifest: zero ready (complete zero, no INC or WR posted)", Z?.status === "ready", Z?.status ?? null);
  claim("manifest: walkthrough worstcase has five 160-code-point INC and five WR with records, listed under W (pre-flight 23)",
    WC?.status === "ready" && WCC?.list_total_count?.incidents === 5 && WCC?.list_total_count?.maintenance === 5 && (WCC?.requests ?? []).every((r) => r.record_id) && Boolean(proc.worstcase),
    { status: WC?.status, totals: WCC?.list_total_count ?? null });
  claim("manifest: forbidden served", Boolean(proc.forbidden), proc.forbidden?.port ?? null);
  for (const k of ["pending", "stale", "unknown"]) {
    const mode = manifest.modes[k] ?? {};
    info(`manifest ${k}: case browser capture ${mode.status === "ready" ? "available" : "unavailable"} (ruling 54; pure component vector in evWorkCases.test.tsx)`, { status: mode.status ?? null, reason: mode.reason ?? null });
  }
  info("in-panel W4 case 503 with a healthy Site read: unavailable (the walkthrough stops the whole API; pure vector in evWorkCases.test.tsx)", manifest.vectors?.unavailable ?? null);

  const WW = WC.work_window_W;
  const want = { incidents: S.incident, maintenance: S.request };
  for (const [wi, [W, width, height]] of WIDTHS.entries()) {
    await size(width, height);
    for (const kind of ["incidents", "maintenance"]) {
      const words = KIND_WORDS[kind];
      const path = `/sites/${SITE}/work/${kind}`;
      let m;
      m = await caseRecord(W, wi, kind, "submitted", `${base("positive")}${path}?${q({ from: SW.from, to: SW.to })}`);
      claim(`${W} ${kind} submitted: stored Site name, R78 subtitle, mock strip and Manage link to the mounted W6 root`,
        m.h1?.includes(P.site.display_name) && m.subtitle && m.scope === `Scoped to ${P.site.display_name.split(/\s+/)[0]} · 1 ${words.noun}` && m.stripDetail?.startsWith(`Same records and states as the global ${words.global} list`)
          // W6-01a A2: the Site window plus the cutoff (no explicit `known_at` here, so the loaded list's own `known_at`).
          && m.manage?.text === `Manage in ${words.global} →` && (m.manage?.href ?? "").startsWith(`/${kind}?${q({ from: SW.from, to: SW.to })}&known_at=`),
        { h1: m.h1, scope: m.scope, strip: m.stripDetail, manage: m.manage });
      claim(`${W} ${kind} submitted: mock columns and panel-head subtitle`, JSON.stringify(m.headings) === JSON.stringify(words.columns) && m.panelDescription === words.subtitle, { headings: m.headings, subtitle: m.panelDescription });
      claim(`${W} ${kind} submitted: CURRENT, no notice; R105 basis and R106 pages`, m.currentness === null && m.basis && m.showing === "Showing 1–1 of 1", { currentness: m.currentness, showing: m.showing });
      claim(`${W} ${kind} submitted: R03 notice first sentence only`, m.noticeText === "Opening a record moves you to its own area; the breadcrumb keeps this site.", m.noticeText);
      const row = m.rows[0] ?? {};
      claim(`${W} ${kind} submitted: the row is the walkthrough's attested case`, row.id === want[kind]?.id, { row: row.id, want: want[kind]?.id });
      if (kind === "incidents") {
        claim(`${W} incidents submitted: plain INC code and title (R85), Site-zone Window, red Open`,
          row.title === `${S.incident.code} · Charging session fault` && row.titleHref === null && /^\d{1,2} [A-Z][a-z]{2} · from \d{2}:\d{2}$/.test(row.window ?? "") && row.windowLines === 1 && row.state === "Open",
          { title: row.title, href: row.titleHref, window: row.window, state: row.state });
      } else {
        const overview = `/maintenance/requests/${S.request.id}?site_id=${SITE}`;
        claim(`${W} maintenance submitted: WR opens the mounted W6 Overview with the Site ID (R83)`, row.title === `${S.request.code} · Connector diagnostic inspection` && row.titleHref === overview, { title: row.title, href: row.titleHref, want: overview });
        claim(`${W} maintenance submitted: asset label as selected or 'No asset linked' (ruling 13), Unverified, next-evidence copy (R82, R84)`,
          (row.asset !== null || row.assetGap) && row.outcome === "Unverified" && Boolean(row.next), { asset: row.asset, gap: row.assetGap, outcome: row.outcome, next: row.next, state: row.state });
        claim(`${W} maintenance submitted: Activity recorded and Outcome note disclosures (R81, R82)`, JSON.stringify(row.cellSummaries?.[2]) === JSON.stringify(["Activity recorded"]) && JSON.stringify(row.cellSummaries?.[3]) === JSON.stringify(["Outcome note"]), row.cellSummaries);
      }
      caseCaps(W, `${kind} submitted`, m, wi);
      caseRowClaims(W, `${kind} submitted`, m, 1);

      m = await caseRecord(W, wi, kind, "submitted-ids-open", `${base("positive")}${path}?${q({ from: SW.from, to: SW.to })}`, async () => {
        await js(openAll(".work-cases [data-work-row] details"));
        await sleep(400);
      });
      claim(`${W} ${kind} submitted-ids-open: the explicit EV domain Action case link is plain text (R113)`, m.actionPlain >= 1 && m.actionHrefs.length === 0, { plain: m.actionPlain, hrefs: m.actionHrefs });
      caseCaps(W, `${kind} submitted-ids-open`, m, wi, { heights: false });
      caseRowClaims(W, `${kind} submitted-ids-open`, m, 1);

      const historicalAt = S.list_known_at?.[kind];
      m = await caseRecord(W, wi, kind, "historical", `${base("positive")}${path}?${q({ from: SW.from, to: SW.to, known_at: historicalAt })}`);
      claim(`${W} ${kind} historical: the returned HISTORICAL state's notice (R80, R104 blue) with the row`, m.currentness === "HISTORICAL" && /^Read as of .* UTC\. Later work may differ\.$/.test(m.currentnessText ?? "") && m.rowCount === 1, { status: m.currentness, text: m.currentnessText, known_at: historicalAt });
      caseCaps(W, `${kind} historical`, m, wi);

      m = await caseRecord(W, wi, kind, "zero", `${base("zero")}${path}?${q({ from: Z.work_window_W.from, to: Z.work_window_W.to })}`);
      claim(`${W} ${kind} zero: exact mock empty card, '0 ${words.noun}', closed basis, no pages, no notice`, m.empty === words.empty && m.scope?.endsWith(`· 0 ${words.noun}`) && m.basis && !m.basisOpen && m.showing === null && m.currentness === null, { empty: m.empty, scope: m.scope });
      caseCaps(W, `${kind} zero`, m, wi, { panelCap: CASE_CAPS.emptyPanel });

      m = await caseRecord(W, wi, kind, "forbidden-403", `${base("forbidden")}${path}?${q({ from: SW.from, to: SW.to })}`);
      claim(`${W} ${kind} forbidden-403: Site read healthy, W4 refusal in the case panel; no zero, no Retry`, m.siteRefusal === null && m.refused === "forbidden" && /No access/.test(m.refusedText ?? "") && !/Retry|EV work unavailable/.test(m.refusedText ?? "") && !/· 0 /.test(m.scope ?? "") && m.empty === null, { refused: m.refused, text: m.refusedText, scope: m.scope });
      caseCaps(W, `${kind} forbidden-403`, m, wi);

      const worstPath = `${base("worstcase")}${path}?${q({ from: WW.from, to: WW.to })}`;
      const worstIds = ((kind === "incidents" ? WCC?.incidents : WCC?.requests) ?? []).map((r) => r.case_id);
      m = await caseRecord(W, wi, kind, "worst", worstPath);
      claim(`${W} ${kind} worst: five walkthrough rows with 36-character IDs, '5 ${words.noun}'`, m.rowCount === 5 && m.rowIds.every((id) => (id ?? "").length === 36 && worstIds.includes(id)) && m.scope?.endsWith(`· 5 ${words.noun}`), { rows: m.rowIds, scope: m.scope });
      caseCaps(W, `${kind} worst`, m, wi);
      caseRowClaims(W, `${kind} worst`, m, 5);

      m = await caseRecord(W, wi, kind, "worst-one-open", worstPath, async () => {
        await js(openAll(".work-cases [data-work-row]:first-child [data-work-case-title] [data-domain-work-longtext] > details"));
        await sleep(400);
      });
      claim(`${W} ${kind} worst-one-open: one Read full text open`, m.readFullOpen === 1, m.readFullOpen);
      caseCaps(W, `${kind} worst-one-open`, m, wi, { panelCap: CASE_CAPS.panelOneOpen });
      caseRowClaims(W, `${kind} worst-one-open`, m, 5);

      m = await caseRecord(W, wi, kind, "worst-all-open", worstPath, async () => {
        await js(openAll(".work-cases [data-work-row] details"));
        await sleep(300);
        await js(openAll(".work-cases [data-work-row] details"));
        await sleep(400);
      });
      const full = m.cells.flatMap((c) => c.fullText);
      claim(`${W} ${kind} worst-all-open: every Read full text open, full 160-code-point values`, m.readFull > 0 && m.readFullOpen === m.readFull && full.length > 0 && full.every((n) => n >= 160), { readFull: m.readFull, open: m.readFullOpen, full });
      caseCaps(W, `${kind} worst-all-open`, m, wi, { heights: false });
      caseRowClaims(W, `${kind} worst-all-open`, m, 5);
    }
  }

  const failed = results.filter((r) => !r.ok).length;
  writeFileSync(join(OUT, "w504b-cases-measurements.json"), JSON.stringify({ manifest_revision: manifest.revision, caps: CASE_CAPS, worstcase_cases: WCC, submitted: { incident: S.incident?.id, request: S.request?.id, record: S.record?.id }, captures, claims: results, failed }, null, 2));
  console.log(`${results.filter((r) => r.ok && !r.info).length} PASS, ${failed} FAIL, ${results.filter((r) => r.info).length} INFO`);
  return failed;
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
  if (process.env.W504B_EVIDENCE === "cases") return mainCases();

  claim("manifest: positive and zero ready (ruling 39)", P?.status === "ready" && Z?.status === "ready", { positive: P?.status, zero: Z?.status });
  const worstIds = [WC?.action?.id, ...(WC?.worstcase?.actions ?? []).map((a) => a.action_id)];
  claim("manifest: walkthrough worstcase ready with ACT-000001..5, four 160-code-point additions and intents, served (re-review M1)",
    WC?.status === "ready" && WC.worstcase?.index_total_count === 5 && JSON.stringify((WC.worstcase?.actions ?? []).map((a) => a.action_code)) === JSON.stringify(["ACT-000002", "ACT-000003", "ACT-000004", "ACT-000005"])
      && (WC.worstcase?.actions ?? []).every((a) => a.title_code_points === 160 && a.owner_code_points === 160 && a.intent_id) && Boolean(proc.worstcase),
    { status: WC?.status, total: WC?.worstcase?.index_total_count, actions: WC?.worstcase?.actions ?? null, port: proc.worstcase?.port ?? null });
  for (const k of ["pending", "stale", "unknown"]) {
    const mode = manifest.modes[k] ?? {};
    info(`manifest ${k}: browser capture ${mode.status === "ready" ? "available" : "unavailable"} (ruling 54; pure component vector)`, { status: mode.status ?? null, reason: mode.reason ?? null });
  }
  claim("manifest: forbidden and unavailable processes recorded; unavailable stopped by attest", Boolean(proc.forbidden && proc.unavailable && manifest.vectors?.unavailable?.stopped_pid), { vectors: manifest.vectors ?? null });

  const positiveUrl = `${base("positive")}/sites/${SITE}/work?${q({ from: W_.from, to: W_.to })}`;
  const historicalUrl = `${base("positive")}/sites/${SITE}/work?${q({ from: W_.from, to: W_.to, known_at: P.index_known_at })}`;
  const zeroUrl = `${base("zero")}/sites/${SITE}/work?${q({ from: dayBefore(Z.work_window_W.from), to: Z.work_window_W.from })}`;
  const forbiddenUrl = `${base("forbidden")}/sites/${SITE}/work?${q({ from: W_.from, to: W_.to })}`;
  const unavailableUrl = `${base("unavailable")}/sites/${SITE}/work?${q({ from: W_.from, to: W_.to })}`;

  for (const [wi, [W, width, height]] of WIDTHS.entries()) {
    await size(width, height);
    let m;
    m = await record(W, wi, "positive", positiveUrl);
    claim(`${W} positive: rows panel, CURRENT, stored Site name and R78 subtitle`, m.panelState === "rows" && m.currentness === null && m.h1?.includes(P.site.display_name) && m.subtitle, { panel: m.panelState, h1: m.h1, subtitle: m.subtitle });
    claim(`${W} positive: strip 'Scoped to … · 1 action' with the EV gap and no link (R79, R04)`, /· 1 action$/.test(m.scope ?? "") && /EV Actions recorded at this site/.test(m.stripText ?? "") && /Global Actions does not include EV Actions yet\./.test(m.stripText ?? "") && m.stripLinks === 0, { scope: m.scope, strip: m.stripText });
    claim(`${W} positive: row is the walkthrough Action with the mock criterion and Source label`, m.rows[0]?.id === P.action.id && /A complete witnessed session and no repeat fault/.test(m.rows[0]?.cellText?.[5] ?? "") && m.rows[0]?.source === `Finding ${P.action_posted.origin_finding_id.slice(0, 8)}`, m.rows[0]);
    claim(`${W} positive: 'Due dates are not yet set' (R76)`, m.panelDescription === "Due dates are not yet set", m.panelDescription);
    claim(`${W} positive: no 'Depot' text (ruling 52)`, !/Depot/.test(m.stripText ?? "") && !/Depot/.test(m.h1 ?? ""), { strip: m.stripText });
    caps(W, "positive", m, wi);
    rowClaims(W, "positive", m, 1);
    windowClaims(W, "positive", m, wi, { from: W_.from.slice(0, 10), to: W_.to.slice(0, 10) });
    claim(`${W} positive: subtabs keep from, to and drop the cursor`, m.subtabs.length === 3 && m.subtabs.every((t) => t.href.includes(`from=${encodeURIComponent(W_.from)}`) && !t.href.includes("cursor")), m.subtabs);

    m = await record(W, wi, "historical", historicalUrl);
    claim(`${W} historical: HISTORICAL notice (R80) with the row`, m.currentness === "HISTORICAL" && m.panelState === "rows" && /^Read as of .* UTC\. Later work may differ\.$/.test(m.currentnessText ?? ""), { status: m.currentness, text: m.currentnessText });
    caps(W, "historical", m, wi);
    rowClaims(W, "historical", m, 1);

    m = await record(W, wi, "zero", zeroUrl);
    claim(`${W} zero: exact mock successful zero, '0 actions'`, m.panelState === "empty" && m.rowCount === 0 && m.empty === "No actions at this site No accepted recommendation or evidence request has been raised here yet." && /· 0 actions$/.test(m.scope ?? ""), { panel: m.panelState, empty: m.empty, scope: m.scope });
    caps(W, "zero", m, wi, { panelCap: CAPS.zeroPanel });

    m = await record(W, wi, "forbidden-403", forbiddenUrl);
    claim(`${W} forbidden-403: Site read healthy, refusal inside the Actions panel`, m.siteRefusal === null && m.panelState === "refused" && Boolean(m.refusal), { siteRefusal: m.siteRefusal, panel: m.panelState, refusal: m.refusal });
    claim(`${W} forbidden-403: 'EV work unavailable', server message, Retry visible; no row, no zero`, /EV work unavailable/.test(m.refusalText ?? "") && Boolean(m.refusalMessage) && !/unexpected shape|could not be reached/.test(m.refusalMessage ?? "") && m.retryVisible === true && m.rowCount === 0 && /— actions$/.test(m.scope ?? ""), { text: m.refusalText, scope: m.scope });
    caps(W, "forbidden-403", m, wi, { panelCap: CAPS.statePanel });

    m = await record(W, wi, "unavailable-503", unavailableUrl);
    info(`${W} unavailable-503: the walkthrough stops this API, so every read fails at the proxy (Site-level refusal, not an in-panel EV 503)`, { siteRefusal: m.siteRefusal, panel: m.panelState });
    claim(`${W} unavailable-503: page states a refusal with no rows and no zero`, m.rowCount === 0 && !/· 0 actions/.test(m.scope ?? "") && (m.siteRefusal !== null || m.panelState === "refused"), { siteRefusal: m.siteRefusal, panel: m.panelState });
    claim(`${W} unavailable-503: no document horizontal overflow`, m.docScrollWidth <= m.docClientWidth + 1, { scrollWidth: m.docScrollWidth, clientWidth: m.docClientWidth });

    m = await record(W, wi, "window-error", positiveUrl, async () => {
      await js(setDate("[data-domain-work-window-from]", "2026-08-01"));
      await js(setDate("[data-domain-work-window-to]", W_.to.slice(0, 10)));
      await js(`document.querySelector('[data-domain-work-window-apply]').click()`);
      await waitFor(`document.querySelector('[data-domain-work-window-error]')`);
      await sleep(200);
    });
    claim(`${W} window-error: the window error is shown, readable and contained, URL unchanged (ruling 51)`, m.window?.error === "The window may span at most 31 days." && m.window?.errorInside === true && m.href === new URL(positiveUrl).pathname + new URL(positiveUrl).search, { error: m.window?.error, inside: m.window?.errorInside, href: m.href });
    caps(W, "window-error", m, wi, { heights: false });
    info(`${W} window-error: Window height`, m.window?.height ?? null);
  }

  const WW = WC.work_window_W;
  const worstUrl = `${base("worstcase")}/sites/${SITE}/work?${q({ from: WW.from, to: WW.to })}`;

  for (const [wi, [W, width, height]] of WIDTHS.entries()) {
    await size(width, height);
    let m;
    m = await record(W, wi, "worst-folded", worstUrl);
    claim(`${W} worst-folded: 5 rows on the page, 4 visible, 'Show all 5 Actions' (R108)`, m.rowsTotal === 5 && m.showAll === "Show all 5 Actions", { total: m.rowsTotal, visible: m.rowCount, showAll: m.showAll, panel: m.panelState, refusal: m.refusal, message: m.refusalMessage });
    claim(`${W} worst-folded: '5 actions' count and 36-character Action IDs from the manifest`, /· 5 actions$/.test(m.scope ?? "") && m.rows.every((r) => (r.id ?? "").length === 36 && worstIds.includes(r.id)), { scope: m.scope });
    caps(W, "worst-folded", m, wi);
    rowClaims(W, "worst-folded", m, 4);

    m = await record(W, wi, "worst-expanded", worstUrl, async () => {
      await js(`document.querySelector('[data-domain-work-show-all]')?.click()`);
      await waitFor(`!document.querySelector('[data-domain-work-show-all]')`);
      await js(`[...document.querySelectorAll('[data-domain-work-row] details[data-disclosure^="domain-work-title-"], [data-domain-work-row] details[data-disclosure^="domain-work-owner-"]')].forEach((d) => { d.open = true; d.dispatchEvent(new Event('toggle')); })`);
      await sleep(400);
    });
    claim(`${W} worst-expanded: all 5 rows visible, every long title disclosure open`, m.rowCount === 5 && m.titleDisclosures >= 4 && m.openTitleDisclosures === m.titleDisclosures, { rows: m.rowCount, title: m.titleDisclosures, open: m.openTitleDisclosures });
    caps(W, "worst-expanded", m, wi, { heights: false });
    rowClaims(W, "worst-expanded", m, 5);
    const full = m.cells.flatMap((c) => c.openText);
    claim(`${W} worst-expanded: opened bodies show the full 160-code-point values`, full.length > 0 && full.every((n) => n >= 160), full);
  }

  const failed = results.filter((r) => !r.ok).length;
  writeFileSync(join(OUT, "w504b-measurements.json"), JSON.stringify({ manifest_revision: manifest.revision, caps: CAPS, worstcase: WC?.worstcase ?? null, captures, claims: results, failed }, null, 2));
  console.log(`${results.filter((r) => r.ok && !r.info).length} PASS, ${failed} FAIL, ${results.filter((r) => r.info).length} INFO`);
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
