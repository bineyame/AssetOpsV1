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
 *
 * K2 rulings (`.agent/W5-02b-K2-rulings.md`): ruling 2 caps the cold Actions panel at 650/850 px and the page at
 * 1600/2000 px (1440/390), with document.scrollWidth <= clientWidth + 1, per-cell containment, a preview of at most
 * two lines and no horizontal clip of an opened `Read full text` (including five 160-code-point rows with every
 * disclosure open); ruling 3 captures the real WORK_STORE_UNAVAILABLE 503 inside the cold-work panel (healthy Site
 * read) as `cold-work-503`, separate from the earlier Site-level `unavailable-503` refusal images; ruling 1 asserts
 * the page-local `Window` control (placement, right-aligned at 1440, full width at 390, Apply keeps known_at and
 * drops the cursor, invalid input shows the window error and does not navigate).
 * Ruling 20: an opened `Read full text` replaces its cell's two-line preview (the preview is unmounted while open).
 * Ruling 21: the manifest's UNKNOWN INC has one link (COLD_START_FAILURE) and a recorded `fixture.incident.limit`;
 * every other mode links both selected Findings. Ruling 23: `cold-incidents` and `cold-maintenance` show one visible
 * date form (the page-local Window control) and keep from, to and known_at in the URL and every Work subtab href.
 * K3b (K3 pre-flight rulings 7-8): `W502B_EVIDENCE=cases node tools/w502-cold-work-evidence.mjs <manifest> <out>`
 * captures only the cold Incidents and Maintenance tabs (positive, historical, complete zero, five-row worst case
 * with one and all disclosures open, pending/stale/unknown, W4 403/503) at both widths against the "other Work" caps
 * (page 1400/1800, panel 440/650, strip 100/150, notice 110/160) and writes <out>/w502b-k3-measurements.json.
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
// Build-spec caps [1440, 390]. K2 ruling 2: the cold Actions Work page <= 1600/2000 and its panel <= 650/850.
const WORK_CAPS = { main: [1600, 2000], strip: [100, 150], panel: [650, 850], notice: [110, 160] };
// W5-02c K4b (`.agent/W5-02c-K4-preflight-rulings.md` ruling 7): final closed `cold-action` caps [1440, 390]; each
// panel is measured on its own. Any user-opened disclosure is exempt from every height cap (recorded as INFO).
const ACTION_CAPS = { main: [1500, 1900], strip: [140, 200], criteria: [500, 760], related: [360, 500], notice: [110, 160] };
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
// K2 ruling 1: set a React-controlled date input the way a user edit does (native setter + input/change events).
const setDate = (selector, value) => `(() => { const el = document.querySelector('${selector}'); const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set; set.call(el, '${value}'); el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); return el.value; })()`;
const dayShift = (instant, days) => new Date(Date.parse(instant) + days * 86400000).toISOString().slice(0, 10);
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
    // Review H1: every row cell (and each open disclosure body and clamped preview) keeps its content inside its own box.
    cells: rows.flatMap((r) => [...r.querySelectorAll('td')]).map((td) => {
      const box = td.getBoundingClientRect();
      const inside = (e) => { const b = e.getBoundingClientRect(); return b.width === 0 || (b.left >= box.left - 1 && b.right <= box.right + 1); };
      const kids = [...td.querySelectorAll('*')];
      // K2 ruling 2/13: the clamped preview shows at most two lines (its box height over its line height).
      const lineBox = (e) => { const cs = getComputedStyle(e); const lh = parseFloat(cs.lineHeight); return Number.isFinite(lh) && lh > 0 ? lh : parseFloat(cs.fontSize) * 1.2; };
      const previews = [...td.querySelectorAll('.work-cases-clamp')];
      const bodies = [...td.querySelectorAll('details[open] .disclosure__body')];
      return { col: td.cellIndex, fits: td.scrollWidth <= td.clientWidth + 1, kidsInside: kids.every(inside),
        clampFits: previews.every((c) => c.scrollWidth <= c.clientWidth + 1),
        previewLines: previews.map((c) => Math.round(c.getBoundingClientRect().height / lineBox(c))),
        openBodyInside: bodies.every(inside), openBodyFits: bodies.every((b) => b.scrollWidth <= b.clientWidth + 1),
        openBodies: bodies.length };
    }),
    badgesClipped: badges.filter((b) => b.scrollWidth > b.clientWidth + 1).length,
    badgeCount: badges.length,
    badgeLines: badges.map((x) => lines(x)),
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
    refusalText: document.querySelector('[data-cold-work-refusal]')?.innerText?.replace(/\\s+/g, ' ').trim() ?? null,
    // K2 ruling 1: the page-local Window control.
    window: (() => {
      const form = document.querySelector('[data-cold-work-window]');
      if (!form) return null;
      const box = form.getBoundingClientRect();
      // The parent's content box (its padding excluded), for the full-width claim at 390.
      const pe = form.parentElement;
      const ps = getComputedStyle(pe);
      const pr = pe.getBoundingClientRect();
      const parent = { left: pr.left + parseFloat(ps.borderLeftWidth) + parseFloat(ps.paddingLeft), width: pe.clientWidth - parseFloat(ps.paddingLeft) - parseFloat(ps.paddingRight) };
      const apply = form.querySelector('[data-cold-work-window-apply]')?.getBoundingClientRect();
      return {
        afterSubtabs: form.previousElementSibling?.matches('nav[aria-label="Work lists"]') === true,
        beforeStrip: form.nextElementSibling?.querySelector(':scope > [data-cold-work-strip]') !== null && form.nextElementSibling !== null,
        from: form.querySelector('[data-cold-work-window-from]')?.value ?? null,
        to: form.querySelector('[data-cold-work-window-to]')?.value ?? null,
        width: Math.round(box.width), parentWidth: Math.round(parent.width), height: Math.round(box.height),
        rightGap: apply ? Math.round(box.right - apply.right) : null,
        leftGap: Math.round(box.left - parent.left),
        error: form.querySelector('[data-cold-work-window-error]')?.textContent?.trim() ?? null,
      };
    })(),
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
// K2 ruling 23: a cold Incidents or Maintenance page has one visible date form (the page-local Window control after
// the Work subtabs, no W4 in-panel form) and every Work subtab href keeps from, to and known_at.
const CASES_READY = `document.querySelector('main [data-cold-work-window]') && document.querySelector('main section.panel') && !document.querySelector('[data-work-loading]')`;
const MEASURE_CASES = `(() => {
  const h = (e) => (e ? Math.round(e.getBoundingClientRect().height) : null);
  const main = document.querySelector('main');
  const visible = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && !e.closest('[hidden]'); };
  const forms = [...(main?.querySelectorAll('form') ?? [])].filter(visible);
  const form = main?.querySelector('[data-cold-work-window]') ?? null;
  return {
    href: location.pathname + location.search,
    panelState: document.querySelector('[data-work-loading]') ? 'loading' : 'settled',
    docScrollWidth: document.documentElement.scrollWidth,
    docClientWidth: document.documentElement.clientWidth,
    docHeight: document.documentElement.scrollHeight,
    main: h(main),
    panel: h(main?.querySelector('section.panel')),
    visibleForms: forms.map((f) => f.getAttribute('data-cold-work-window') !== null ? 'cold-window' : f.matches('form[data-work-window]') ? 'w4-window' : (f.getAttribute('aria-label') ?? 'form')),
    w4Form: Boolean(main?.querySelector('form[data-work-window]')),
    windowAfterSubtabs: form?.previousElementSibling?.matches('nav[aria-label="Work lists"]') === true,
    windowFrom: form?.querySelector('[data-cold-work-window-from]')?.value ?? null,
    windowTo: form?.querySelector('[data-cold-work-window-to]')?.value ?? null,
    subtabs: [...document.querySelectorAll('nav[aria-label="Work lists"] a')].map((a) => a.getAttribute('href')),
  };
})()`;
// ---- W5-02b K3b: the cold case tabs (v69 cold-work-incidents / cold-work-maintenance) ----------------------------
// K3 ruling 17 (FINAL, supersedes ruling 16 and Measurement :38 for the case tabs): case panel <= 650 and page main
// <= 1400 at 1440, panel <= 650 and page main <= 1800 at 390, strip <= 100/150, notice <= 110/160, for every state
// except the expanded ones. Ruling 18: `worstcase-all-open` (every `Read full text` open) and the INFO-only
// `worstcase-every-disclosure` have no panel or page-main height cap; their page height is reported against 1600/2000
// as information, and every other gate (strip, notice, rows, columns, containment, keyboard, values once, horizontal
// table scrolling, no document overflow or clipping) still applies.
const CASE_CAPS = { main: [1400, 1800], strip: [100, 150], panel: [650, 650], notice: [110, 160] };
const CASE_INFO_PAGE = [1600, 2000];
const CASE_BANNER = "Cold-room operating capabilities and consequence vocabulary within the stable Site shell.";
const CASE_READY = `document.querySelector('main [data-site-work] section.panel') && !document.querySelector('[data-work-loading]') && (document.querySelector('[data-work-loaded], [data-work-empty], [data-work-refused]'))`;
const MEASURE_CASE = `(() => {
  const h = (e) => (e ? Math.round(e.getBoundingClientRect().height) : null);
  const main = document.querySelector('main');
  const body = document.querySelector('main [data-site-work]');
  const panel = body?.querySelector('section.panel') ?? null;
  const scroller = body?.querySelector('.data-table__scroll') ?? null;
  const rows = [...(body?.querySelectorAll('tbody tr[data-work-row]') ?? [])];
  const firstCell = scroller?.querySelector('tbody tr > :first-child') ?? scroller?.querySelector('thead th');
  const t = (e) => e?.innerText?.replace(/\\s+/g, ' ').trim() ?? null;
  const lineBox = (e) => { const cs = getComputedStyle(e); const lh = parseFloat(cs.lineHeight); return Number.isFinite(lh) && lh > 0 ? lh : parseFloat(cs.fontSize) * 1.2; };
  const badges = [...(body?.querySelectorAll('tbody [data-work-state], tbody [data-work-outcome]') ?? [])];
  const visible = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && !e.closest('[hidden]'); };
  return {
    href: location.pathname + location.search,
    kind: body?.getAttribute('data-site-work') ?? null,
    panelState: body?.querySelector('[data-work-refused]') ? 'refused' : body?.querySelector('[data-work-empty]') ? 'empty' : body?.querySelector('[data-work-loaded]') ? 'rows' : 'loading',
    currentness: document.querySelector('[data-cold-work-currentness]')?.getAttribute('data-cold-work-currentness') ?? null,
    currentnessTone: document.querySelector('[data-cold-work-currentness]')?.classList.contains('v69-notice--blue') ? 'blue' : document.querySelector('[data-cold-work-currentness]') ? 'amber' : null,
    noticeAfterStrip: document.querySelector('[data-cold-work-currentness]')?.previousElementSibling?.classList.contains('status-strip') ?? null,
    noticeBeforePanel: document.querySelector('[data-cold-work-currentness]')?.nextElementSibling === panel || null,
    stripText: t(body?.querySelector('.status-strip')),
    manageHref: body?.querySelector('[data-work-manage-link]')?.getAttribute('href') ?? null,
    statusLabel: Boolean(body?.querySelector('[data-work-status]')),
    coverageLine: Boolean(body?.querySelector('[data-work-coverage-line]')),
    docScrollWidth: document.documentElement.scrollWidth,
    docClientWidth: document.documentElement.clientWidth,
    docHeight: document.documentElement.scrollHeight,
    main: h(main),
    strip: h(body?.querySelector('.status-strip')),
    panel: h(panel),
    currentnessNotice: h(document.querySelector('[data-cold-work-currentness]')),
    contextNotice: h(document.querySelector('[data-cold-work-notice]')),
    contextNoticeText: t(document.querySelector('[data-cold-work-notice]')),
    banner: (main?.innerText ?? '').includes(${JSON.stringify(CASE_BANNER)}),
    // textContent: the header cells are uppercased by CSS only.
    headings: [...(body?.querySelectorAll('thead th') ?? [])].map((x) => x.textContent.replace(/\\s+/g, ' ').trim()),
    scrollerScrollWidth: scroller?.scrollWidth ?? null,
    scrollerClientWidth: scroller?.clientWidth ?? null,
    stickyFirstColumn: firstCell ? getComputedStyle(firstCell).position === 'sticky' : null,
    rowCount: rows.length,
    windows: rows.map((r) => t(r.querySelector('[data-work-window]'))).filter((x) => x !== null),
    findings: rows.map((r) => [...r.querySelectorAll('[data-work-finding-unlinked]')].map((x) => t(x))),
    findingAnchors: body?.querySelectorAll('tbody a[data-work-finding-link]').length ?? 0,
    caseAnchors: rows.map((r) => r.querySelector('[data-work-case-title] a')?.getAttribute('href') ?? null),
    assets: rows.map((r) => t(r.querySelector('[data-work-asset]'))),
    activityChips: rows.map((r) => t(r.querySelector('[data-work-activity-cell] [data-work-state]'))),
    nextEvidence: rows.map((r) => t(r.querySelector('[data-work-next-evidence]'))),
    showing: t(body?.querySelector('[data-work-showing]')),
    basis: [...(body?.querySelectorAll('summary') ?? [])].some((s) => t(s) === 'What this list is based on'),
    empty: t(body?.querySelector('[data-work-empty]')),
    refused: body?.querySelector('[data-work-refused]')?.getAttribute('data-work-refused') ?? null,
    refusedCode: body?.querySelector('[data-work-refused]')?.getAttribute('data-work-code') ?? null,
    refusedText: t(body?.querySelector('[data-work-refused]')),
    siteRefusal: body ? null : (t(main)?.slice(0, 200) ?? null),
    visibleForms: [...(main?.querySelectorAll('form') ?? [])].filter(visible).map((f) => f.getAttribute('data-cold-work-window') !== null ? 'cold-window' : 'other'),
    openDetails: body?.querySelectorAll('tbody details[open]').length ?? 0,
    allDetails: body?.querySelectorAll('tbody details').length ?? 0,
    badgeCount: badges.length,
    badgesClipped: badges.filter((b) => b.scrollWidth > b.clientWidth + 1).length,
    // K3 ruling 20: the Window value is one line.
    windowLines: rows.map((r) => r.querySelector('[data-work-window]')).filter(Boolean).map((e) => { const rg = document.createRange(); rg.selectNodeContents(e);
      const tops = [...rg.getClientRects()].filter((x) => x.width > 0).map((x) => Math.round(x.top)); return new Set(tops).size; }),
    // K3 ruling 21: no row hidden below the table scroller's visible box (no vertical case box).
    rowsInsideScroller: (() => { if (!scroller) return null; const sb = scroller.getBoundingClientRect(); return rows.every((r) => r.getBoundingClientRect().bottom <= sb.bottom + 1); })(),
    scrollerOverflowY: scroller ? getComputedStyle(scroller).overflowY : null,
    scrollerMaxHeight: scroller ? getComputedStyle(scroller).maxHeight : null,
    // K3 ruling 18: the 'Read full text' controls, their open state, and whether each opened value is shown once.
    readFull: (() => { const ds = [...(body?.querySelectorAll('tbody details') ?? [])].filter((d) => d.querySelector(':scope > summary')?.textContent.trim() === 'Read full text');
      return { total: ds.length, open: ds.filter((d) => d.open).length,
        previewsWhileOpen: ds.filter((d) => d.open && d.parentElement.querySelector(':scope > [data-cold-work-preview]')).length,
        valuesOnce: ds.filter((d) => d.open).every((d) => { const v = d.querySelector('.disclosure__body').textContent.trim(); return d.closest('td').textContent.split(v).length - 1 === 1; }) }; })(),
    otherOpen: [...(body?.querySelectorAll('tbody details[open]') ?? [])].map((d) => d.querySelector(':scope > summary')?.textContent.trim()).filter((x) => x !== 'Read full text' && x !== 'Activity recorded' && x !== 'Outcome note'),
    // K3 ruling 20: each UUID in an opened 'UTC and IDs' / 'Finding version' body is one line and fully reachable by
    // scrolling that body (overflow-x auto), without widening the cell.
    openCodes: [...(body?.querySelectorAll('tbody details[open] .disclosure__body code') ?? [])].map((c) => { const b = c.closest('.disclosure__body'); const rg = document.createRange(); rg.selectNodeContents(c);
      const tops = new Set([...rg.getClientRects()].filter((x) => x.width > 0).map((x) => Math.round(x.top))).size; const td = c.closest('td');
      return { chars: c.textContent.length, lines: tops, reachable: b.scrollWidth >= c.scrollWidth && (getComputedStyle(b).overflowX === 'auto' || b.scrollWidth <= b.clientWidth + 1), cellFits: td.scrollWidth <= td.clientWidth + 1 }; }),
    cells: rows.flatMap((r) => [...r.querySelectorAll('td')]).map((td) => {
      const box = td.getBoundingClientRect();
      // W5-02c ruling 12: the scroll relaxation applies only inside a disclosure body whose direct child is the code.
      const codeScroller = (x) => x != null && x.querySelector(':scope > code') !== null && getComputedStyle(x).overflowX === 'auto';
      const inside = (e) => { const b = e.getBoundingClientRect(); const sc = e.parentElement?.closest('.disclosure__body'); return b.width === 0 || (b.left >= box.left - 1 && b.right <= box.right + 1) || codeScroller(sc); };
      const previews = [...td.querySelectorAll('[data-cold-work-preview]')];
      const bodies = [...td.querySelectorAll('details[open] .disclosure__body')];
      return { col: td.cellIndex, fits: td.scrollWidth <= td.clientWidth + 1, kidsInside: [...td.querySelectorAll('*')].every(inside),
        previewLines: previews.map((c) => Math.round(c.getBoundingClientRect().height / lineBox(c))),
        openBodyInside: bodies.every(inside), openBodyFits: bodies.every((b) => b.scrollWidth <= b.clientWidth + 1 || codeScroller(b)), openBodies: bodies.length };
    }),
  };
})()`;

function capCase(W, label, m, wi, heightCaps = true, panelCap = null) {
  const c = CASE_CAPS;
  const pc = panelCap ?? c.panel[wi];
  claim(`${W} ${label}: no document horizontal overflow (scrollWidth <= clientWidth + 1)`, m.docScrollWidth <= m.docClientWidth + 1, { scrollWidth: m.docScrollWidth, clientWidth: m.docClientWidth });
  if (heightCaps) claim(`${W} ${label}: page main <= ${c.main[wi]}`, m.main !== null && m.main <= c.main[wi], { main: m.main, docHeight: m.docHeight });
  else console.log(`INFO  ${W} ${label}: page main ${m.main} vs ${CASE_INFO_PAGE[wi]} (K3 ruling 18: information only, no page-height cap)`);
  claim(`${W} ${label}: strip <= ${c.strip[wi]}`, m.strip !== null && m.strip <= c.strip[wi], m.strip);
  if (heightCaps) claim(`${W} ${label}: panel <= ${pc}`, m.panel !== null && m.panel <= pc, { panel: m.panel, tableScrollWidth: m.scrollerScrollWidth, tableClientWidth: m.scrollerClientWidth });
  else console.log(`INFO  ${W} ${label}: panel height ${m.panel} (K3 ruling 18: no panel-height cap; recorded)`);
  claim(`${W} ${label}: context notice <= ${c.notice[wi]} and is the domain notice`, m.contextNotice !== null && m.contextNotice <= c.notice[wi] && m.contextNoticeText === "Opening a record moves you to its own area; the breadcrumb keeps this site.", { height: m.contextNotice, text: m.contextNoticeText });
  if (m.currentnessNotice !== null) claim(`${W} ${label}: currentness notice <= ${c.notice[wi]}`, m.currentnessNotice <= c.notice[wi], m.currentnessNotice);
  claim(`${W} ${label}: no banner on the product screen (K3 ruling 1)`, m.banner === false, m.banner);
  claim(`${W} ${label}: one visible date form (the page-local Window control)`, m.visibleForms.length === 1 && m.visibleForms[0] === "cold-window", m.visibleForms);
}
function caseRowClaims(W, label, m, expectRows) {
  claim(`${W} ${label}: ${expectRows} row(s) measured`, m.rowCount === expectRows && m.cells.length > 0, m.rowCount);
  claim(`${W} ${label}: every row cell contains its content`, m.cells.length > 0 && m.cells.every((c) => c.fits && c.kidsInside), m.cells.filter((c) => !(c.fits && c.kidsInside)));
  if (m.cells.some((c) => c.openBodies > 0)) claim(`${W} ${label}: every opened disclosure body stays inside its cell`, m.cells.every((c) => c.openBodyInside && c.openBodyFits), m.cells.filter((c) => !(c.openBodyInside && c.openBodyFits)));
  const previews = m.cells.flatMap((c) => c.previewLines);
  if (previews.length > 0) claim(`${W} ${label}: every long-text preview is at most two lines`, previews.every((n) => n >= 1 && n <= 2), previews);
  if (W === "narrow") claim(`${W} ${label}: first column is position:sticky (spec: at 390 px)`, m.stickyFirstColumn === true, m.stickyFirstColumn);
  claim(`${W} ${label}: no clipped chip or badge`, m.badgeCount > 0 && m.badgesClipped === 0, { badges: m.badgeCount, clipped: m.badgesClipped });
  claim(`${W} ${label}: R93 Pages block and R92 basis disclosure present`, /^Showing /.test(m.showing ?? "") && m.basis, { showing: m.showing, basis: m.basis });
  if (W === "narrow") claim(`${W} ${label}: table scrolls inside its panel`, m.scrollerScrollWidth > m.scrollerClientWidth, { scrollWidth: m.scrollerScrollWidth, clientWidth: m.scrollerClientWidth });
  // K3 ruling 21: both cold case tabs grow with their rows; no vertical case box hides a row.
  claim(`${W} ${label}: every row visible inside the table scroller (no vertical case box)`, m.rowsInsideScroller === true && m.scrollerMaxHeight === "none", { inside: m.rowsInsideScroller, maxHeight: m.scrollerMaxHeight, overflowY: m.scrollerOverflowY });
  if (m.windowLines.length > 0) claim(`${W} ${label}: Window value on one line (ruling 20)`, m.windowLines.every((n) => n === 1), m.windowLines);
  if (m.openCodes.length > 0) claim(`${W} ${label}: every opened UUID is one line and fully reachable in its body without widening the cell (ruling 20)`, m.openCodes.every((c) => c.lines === 1 && c.reachable && c.cellFits), m.openCodes.filter((c) => !(c.lines === 1 && c.reachable && c.cellFits)));
}
function caseContentClaims(W, label, m, kind, mode) {
  const want = kind === "incidents" ? ["Case", "Window", "What happened", "Linked findings", "State"] : ["Work request", "Asset", "Activity", "Outcome", "Next evidence"];
  claim(`${W} ${label}: mock columns in order`, JSON.stringify(m.headings) === JSON.stringify(want), m.headings);
  const noun = kind === "incidents" ? "Incidents" : "Maintenance";
  claim(`${W} ${label}: strip reads the mock sentence and Manage in ${noun} →, no strip status label`,
    (m.stripText ?? "").includes(`Same records and states as the global ${noun} list`) && (m.stripText ?? "").includes(`Manage in ${noun} →`) && !m.statusLabel && (m.manageHref ?? "").startsWith(`/${kind}?`),
    { strip: m.stripText, href: m.manageHref, statusLabel: m.statusLabel });
  claim(`${W} ${label}: no in-panel coverage line on cold`, m.coverageLine === false, m.coverageLine);
  if (kind === "incidents") {
    // K2 ruling 4: `6 Oct · from 19:11`-shaped Site-local Window; the fixture INC is at D+16h11m (19:11 Africa/Addis_Ababa).
    claim(`${W} ${label}: Site-local Window text ("{d} {Mon} · from HH:MM"), fixture INC at 19:11`, m.windows.length > 0 && m.windows.every((x) => /^\d{1,2} [A-Z][a-z]{2} · from \d{2}:\d{2}$/.test(x)) && m.windows.includes(`${Number(manifest.modes[mode].fixture.incident.occurred_at.slice(8, 10))} ${["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][Number(manifest.modes[mode].fixture.incident.occurred_at.slice(5, 7)) - 1]} · from 19:11`), m.windows);
    const links = mode === "unknown" ? 1 : 2;
    claim(`${W} ${label}: every INC shows ${links} plain Finding label(s), no Finding anchor, plain INC code (R65/R66/R73)`,
      m.findings.length > 0 && m.findings.every((f) => f.length === links && f.every((x) => /^Finding [0-9a-f]{8}$/.test(x))) && m.findingAnchors === 0 && m.caseAnchors.every((a) => a === null),
      { findings: m.findings, anchors: m.findingAnchors, caseAnchors: m.caseAnchors });
  } else {
    claim(`${W} ${label}: Asset cell reads generator-1 · backup generator (R89)`, m.assets.length > 0 && m.assets.every((a) => a === "generator-1 · backup generator"), m.assets);
    // K3 rulings 3/22: the chip is the selected request state. The fixture WR is COMPLETED (ASSIGN + COMPLETE before its
    // case link); the four extra worst-case WRs stay OPEN. A historical cutoff before completion would read Open.
    const want = mode === "worstcase" ? ["Completed", "Open", "Open", "Open", "Open"] : ["Completed"];
    claim(`${W} ${label}: Activity chips are the selected states ${want.join("/")}`, JSON.stringify([...m.activityChips].sort()) === JSON.stringify(want), m.activityChips);
    claim(`${W} ${label}: Next evidence is the honest gap (R72)`, m.nextEvidence.length > 0 && m.nextEvidence.every((x) => x === "No next evidence recorded"), m.nextEvidence);
    claim(`${W} ${label}: WR code opens the W6 C2 Overview with site_id (R68)`, m.caseAnchors.length > 0 && m.caseAnchors.every((a) => a !== null && a.startsWith("/maintenance/requests/") && a.includes(`site_id=${SITE}`)), m.caseAnchors);
  }
}
// K3 ruling 12: run after the capture (focusing scrolls the table): every disclosure summary takes keyboard focus and
// sits inside its cell. The table scroller is restored to its start afterwards.
const FOCUS_CHECK = `(() => { const out = [...document.querySelectorAll('main [data-site-work] tbody details > summary')].map((x) => { x.focus(); const r = x.getBoundingClientRect(); const td = x.closest('td').getBoundingClientRect();
  return { text: x.textContent.trim(), focusable: document.activeElement === x, inside: r.width > 0 && r.left >= td.left - 1 && r.right <= td.right + 1 && x.scrollWidth <= x.clientWidth + 1 }; });
  document.activeElement?.blur(); const sc = document.querySelector('main [data-site-work] .data-table__scroll'); if (sc) sc.scrollLeft = 0; return out; })()`;
// K3 ruling 18: open every `Read full text`, opening only its `Activity recorded`/`Outcome note` parent when needed;
// `UTC and IDs`, `Finding version`, identity and basis disclosures stay closed.
const OPEN_READ_FULL = `(async () => { const q = () => [...document.querySelectorAll('main [data-site-work] tbody details')];
  for (const d of q()) { const s = d.querySelector(':scope > summary')?.textContent.trim(); if ((s === 'Activity recorded' || s === 'Outcome note') && !d.open && d.querySelector('details > summary')) d.querySelector(':scope > summary').click(); }
  await new Promise((r) => setTimeout(r, 150));
  for (const d of q()) { if (d.querySelector(':scope > summary')?.textContent.trim() === 'Read full text' && !d.open) d.querySelector(':scope > summary').click(); }
  await new Promise((r) => setTimeout(r, 150)); return true; })()`;
// INFO-only `worstcase-every-disclosure` (ruling 18): every tbody disclosure open, nested ones as they appear.
const openAll = `(async () => { for (let i = 0; i < 6; i += 1) { const closed = [...document.querySelectorAll('main [data-site-work] tbody details:not([open])')]; if (closed.length === 0) break; closed.forEach((d) => d.querySelector(':scope > summary').click()); await new Promise((r) => setTimeout(r, 150)); } return document.querySelectorAll('main [data-site-work] tbody details:not([open])').length; })()`;

async function casesMain() {
  const caseUrl = (k, kind, q) => `${HOST}:${({ positive: 8971, worstcase: 8972, pending: 8973, stale: 8974, unknown: 8975 })[k] - 3500}/sites/${SITE}/work/${kind}?${new URLSearchParams(Object.fromEntries(Object.entries(q).filter(([, v]) => v != null))).toString()}`;
  const read = (k, name, kind) => manifest.modes[k].case_reads?.[`${name}:${kind}`];
  for (const k of ["positive", "worstcase", "pending", "stale", "unknown"]) {
    const doc = manifest.modes[k];
    const names = Object.keys(doc.case_reads ?? {});
    claim(`manifest ${k}: not blocked, case reads present with expected counts`, !doc.blocked && names.length > 0 && names.every((n) => doc.case_reads[n].total_count === doc.case_reads[n].expected.total_count && doc.case_reads[n].rows === doc.case_reads[n].expected.rows), { blocked: doc.blocked ?? null, reads: names.map((n) => [n, doc.case_reads[n].status, doc.case_reads[n].total_count]) });
  }
  claim("manifest worstcase: four extra INC/WR pairs at the ruled minute offsets", (manifest.modes.worstcase.fixture?.extra_cases ?? []).length === 4, (manifest.modes.worstcase.fixture?.extra_cases ?? []).map((x) => [x.incident.occurred_at, x.request.occurred_at, x.request.record_occurred_at]));
  const forbidden = manifest.processes.forbidden;
  const unavailable = manifest.processes.unavailable;
  const procBase = (p) => `${HOST}:${Number(new URL(p.api_base).port) - 3500}`;
  for (const [wi, [W, width, height]] of WIDTHS.entries()) {
    await size(width, height);
    for (const kind of ["incidents", "maintenance"]) {
      let m;
      const s = (x) => `${kind}-${x}`;
      // Positive (the Action read's window at its returned cutoff, which W4 reads as HISTORICAL), historical (K3),
      // complete zero (ruled [D-8 days, D-1 day) window, CURRENT).
      m = await record(W, wi, s("positive"), caseUrl("positive", kind, read("positive", "positive", kind).query), CASE_READY, MEASURE_CASE);
      // K3 rulings 7/13: the capture uses its recorded query (the Action read's window and returned cutoff); the
      // notice follows the returned case-list status (an explicit cutoff reads HISTORICAL), never a fixed expectation.
      const ps = read("positive", "positive", kind).status;
      claim(`${W} ${s("positive")}: rows, notice follows the returned status ${ps}`, m.panelState === "rows" && m.currentness === (ps === "CURRENT" ? null : ps), { panel: m.panelState, currentness: m.currentness });
      capCase(W, s("positive"), m, wi); caseRowClaims(W, s("positive"), m, 1); caseContentClaims(W, s("positive"), m, kind, "positive");
      // K3 ruling 19: the CURRENT capture uses only the recorded from,to (no known_at); the returned case status is
      // CURRENT and no currentness notice shows.
      const cur = read("positive", "current", kind);
      m = await record(W, wi, s("current"), caseUrl("positive", kind, { from: cur.query.from, to: cur.query.to }), CASE_READY, MEASURE_CASE);
      claim(`${W} ${s("current")}: URL has no known_at, manifest status CURRENT, no currentness notice`,
        !/known_at=/.test(m.href) && cur.status === "CURRENT" && m.currentness === null && m.panelState === "rows", { href: m.href, status: cur.status, returnedKnownAt: cur.known_at, currentness: m.currentness });
      capCase(W, s("current"), m, wi); caseRowClaims(W, s("current"), m, 1); caseContentClaims(W, s("current"), m, kind, "positive");
      m = await record(W, wi, s("historical"), caseUrl("positive", kind, read("positive", "historical", kind).query), CASE_READY, MEASURE_CASE);
      claim(`${W} ${s("historical")}: notice reads the returned status ${read("positive", "historical", kind).status}`, m.currentness === read("positive", "historical", kind).status, m.currentness);
      capCase(W, s("historical"), m, wi); caseRowClaims(W, s("historical"), m, 1);
      m = await record(W, wi, s("zero"), caseUrl("positive", kind, read("positive", "zero", kind).query), CASE_READY, MEASURE_CASE);
      const empty = kind === "incidents"
        ? "No incidents at this site No operational case was opened in the selected period. A case comes from a linked chain of events, not from a single data gap."
        : "No maintenance work at this site No inspection or repair has been raised here in the selected period.";
      claim(`${W} ${s("zero")}: v69 WORK_EMPTY title/body, basis kept, no Pages block`, m.panelState === "empty" && m.empty === empty && m.basis && m.showing === null, { empty: m.empty, basis: m.basis, showing: m.showing, status: m.currentness });
      capCase(W, s("zero"), m, wi);
      // Worst case: five 160-code-point rows; then one opened `Read full text`; then every disclosure open.
      const wq = read("worstcase", "worstcase", kind).query;
      m = await record(W, wi, s("worstcase"), caseUrl("worstcase", kind, wq), CASE_READY, MEASURE_CASE);
      claim(`${W} ${s("worstcase")}: Showing 1–5 of 5, notice follows the returned status`, m.showing?.startsWith("Showing 1–5 of 5") && m.currentness === (read("worstcase", "worstcase", kind).status === "CURRENT" ? null : read("worstcase", "worstcase", kind).status), { showing: m.showing, currentness: m.currentness });
      capCase(W, s("worstcase"), m, wi); caseRowClaims(W, s("worstcase"), m, 5); caseContentClaims(W, s("worstcase"), m, kind, "worstcase");
      m = await record(W, wi, s("worstcase-one-open"), caseUrl("worstcase", kind, wq), CASE_READY, MEASURE_CASE, async () => {
        await js(`document.querySelector('main [data-site-work] tbody [data-work-case-title] details > summary').click()`);
        await waitFor(`document.querySelector('main [data-site-work] tbody [data-work-case-title] details[open]')`);
        await sleep(300);
      });
      claim(`${W} ${s("worstcase-one-open")}: one Read full text open`, m.openDetails === 1, { open: m.openDetails, of: m.allDetails });
      // K3 ruling 25 (FINAL): only cold-work-incidents at 390, five rows with one `Read full text` open, has a 680 px
      // panel cap (measured 664); every other cap, including its 1800 page main, is unchanged.
      capCase(W, s("worstcase-one-open"), m, wi, true, kind === "incidents" && W === "narrow" ? 680 : null);
      caseRowClaims(W, s("worstcase-one-open"), m, 5);
      m = await record(W, wi, s("worstcase-all-open"), caseUrl("worstcase", kind, wq), CASE_READY, MEASURE_CASE, async () => {
        await js(OPEN_READ_FULL);
        await sleep(300);
      });
      // Ruling 18: every expected long-text control open, its preview replaced and its full value shown once; the
      // identity/version/basis disclosures stay closed.
      claim(`${W} ${s("worstcase-all-open")}: every Read full text open, previews replaced, each value once, other disclosures closed`,
        m.readFull.total > 0 && m.readFull.open === m.readFull.total && m.readFull.previewsWhileOpen === 0 && m.readFull.valuesOnce && m.otherOpen.length === 0,
        { readFull: m.readFull, otherOpen: m.otherOpen });
      capCase(W, s("worstcase-all-open"), m, wi, false); // K3 ruling 18: no panel/page-main height cap
      caseRowClaims(W, s("worstcase-all-open"), m, 5);
      // K3 ruling 12: every (nested) disclosure control is a native, keyboard-focusable summary, inside the viewport width.
      const focus = await js(FOCUS_CHECK);
      claim(`${W} ${s("worstcase-all-open")}: every disclosure summary takes keyboard focus and is not clipped`, focus.length > 0 && focus.every((x) => x.focusable && x.inside), { summaries: focus.length, failing: focus.filter((x) => !(x.focusable && x.inside)) });
      // Ruling 18: the INFO-only every-disclosure state (cannot supply the all-open gate); no height caps, other gates kept.
      m = await record(W, wi, s("worstcase-every-disclosure"), caseUrl("worstcase", kind, wq), CASE_READY, MEASURE_CASE, async () => {
        await js(openAll);
        await sleep(300);
      });
      claim(`${W} ${s("worstcase-every-disclosure")}: every row disclosure open`, m.allDetails > 0 && m.openDetails === m.allDetails, { open: m.openDetails, of: m.allDetails });
      capCase(W, s("worstcase-every-disclosure"), m, wi, false);
      caseRowClaims(W, s("worstcase-every-disclosure"), m, 5);
      // Late / stale / unknown: the returned case-list status drives the notice (R91 tones).
      for (const k of ["pending", "stale", "unknown"]) {
        const rd = read(k, k, kind);
        m = await record(W, wi, s(k), caseUrl(k, kind, rd.query), CASE_READY, MEASURE_CASE);
        const tone = rd.status === "PENDING_RECOMPUTE" || rd.status === "STALE_SOURCE" ? "amber" : rd.status === "CURRENT" ? null : "blue";
        claim(`${W} ${s(k)}: notice follows the returned status ${rd.status} (${tone ?? "none"}), between strip and panel`,
          m.currentness === (rd.status === "CURRENT" ? null : rd.status) && m.currentnessTone === tone && (tone === null || (m.noticeAfterStrip && m.noticeBeforePanel)),
          { currentness: m.currentness, tone: m.currentnessTone, afterStrip: m.noticeAfterStrip, beforePanel: m.noticeBeforePanel });
        capCase(W, s(k), m, wi); caseRowClaims(W, s(k), m, 1); caseContentClaims(W, s(k), m, kind, k);
      }
      // 403 / 503 (K3 ruling 8): the real W4 refusals from the tool-local case router, inside the case panel.
      // K3 ruling 9 (ruling 8 corrected): W4 `Refused` unchanged; the title and its fixed W4 sentence, no Retry.
      for (const [k, proc, status, title, sentence] of [
        ["forbidden-403", forbidden, "forbidden", "No access", "You do not have access to this site's work."],
        ["unavailable-503", unavailable, "unavailable", "Work records unavailable", "Work records are unavailable right now. Try again."],
      ]) {
        const q = { from: proc.query.from, to: proc.query.to };
        m = await record(W, wi, s(k), `${procBase(proc)}/sites/${SITE}/work/${kind}?${new URLSearchParams(q).toString()}`, CASE_READY, MEASURE_CASE);
        claim(`${W} ${s(k)}: Site read healthy, W4 refusal ${status}/${proc.expected.code} titled '${title}' inside the case panel`,
          m.siteRefusal === null && m.panelState === "refused" && m.refused === status && m.refusedCode === proc.expected.code && (m.refusedText ?? "").includes(title) && (m.refusedText ?? "").includes(sentence) && !/Retry/.test(m.refusedText ?? ""),
          { siteRefusal: m.siteRefusal, refused: m.refused, code: m.refusedCode, text: m.refusedText, sentence });
        claim(`${W} ${s(k)}: no row and no zero count`, m.rowCount === 0 && !/· 0 /.test(m.stripText ?? ""), { rows: m.rowCount, strip: m.stripText });
        capCase(W, s(k), m, wi);
      }
    }
  }
  const failed = results.filter((r) => !r.ok).length;
  writeFileSync(join(OUT, "w502b-k3-measurements.json"), JSON.stringify({ manifest_revision: manifest.revision, caps: { cases: CASE_CAPS }, captures, claims: results, failed }, null, 2));
  console.log(`${results.length - failed} PASS, ${failed} FAIL`);
  return failed;
}

const workUrl = (base, query, extra = {}) => `${base}/sites/${SITE}/work?${new URLSearchParams({ ...query, ...extra }).toString()}`;

function capWork(W, label, m, wi, notices = true, panelCap = true) {
  const caps = WORK_CAPS;
  claim(`${W} ${label}: no document horizontal overflow (scrollWidth <= clientWidth + 1)`, m.docScrollWidth <= m.docClientWidth + 1, { scrollWidth: m.docScrollWidth, clientWidth: m.docClientWidth });
  claim(`${W} ${label}: page main <= ${caps.main[wi]}`, m.main !== null && m.main <= caps.main[wi], { main: m.main, docHeight: m.docHeight });
  claim(`${W} ${label}: strip <= ${caps.strip[wi]}`, m.strip !== null && m.strip <= caps.strip[wi], m.strip);
  // K2 ruling 24 (FINAL): the five-row state with every `Read full text` disclosure open has no Actions-panel height
  // cap; the page-main caps, containment and no-overflow claims still apply. Every other state keeps the panel cap.
  if (panelCap) claim(`${W} ${label}: panel <= ${caps.panel[wi]}`, m.panel !== null && m.panel <= caps.panel[wi], { panel: m.panel, tableScrollWidth: m.scrollerScrollWidth, tableClientWidth: m.scrollerClientWidth });
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
  claim(`${W} ${label}: every row cell contains its content (scrollWidth <= clientWidth + 1, children inside the cell rect)`, m.cells.length > 0 && m.cells.every((c) => c.fits && c.kidsInside && c.clampFits), m.cells.filter((c) => !(c.fits && c.kidsInside && c.clampFits)));
  if (m.cells.some((c) => c.openBodies > 0)) claim(`${W} ${label}: every opened Read full text body stays inside its cell with no horizontal clip`, m.cells.every((c) => c.openBodyInside && c.openBodyFits), m.cells.filter((c) => !(c.openBodyInside && c.openBodyFits)));
  const previews = m.cells.flatMap((c) => c.previewLines);
  if (previews.length > 0) claim(`${W} ${label}: every long-text preview is at most two lines`, previews.every((n) => n >= 1 && n <= 2), previews);
  claim(`${W} ${label}: first column is position:sticky`, m.stickyFirstColumn === true, m.stickyFirstColumn);
  claim(`${W} ${label}: no clipped State badge`, m.badgeCount > 0 && m.badgesClipped === 0, { badges: m.badgeCount, clipped: m.badgesClipped });
  claim(`${W} ${label}: every State badge is on one line`, m.badgeLines.length > 0 && m.badgeLines.every((n) => n === 1), m.badgeLines);
  if (W === "narrow") claim(`${W} ${label}: table scrolls inside its panel`, m.scrollerScrollWidth > m.scrollerClientWidth, { scrollWidth: m.scrollerScrollWidth, clientWidth: m.scrollerClientWidth });
}

function windowClaims(W, label, m, wi, want) {
  const w = m.window;
  claim(`${W} ${label}: Window control after the Work subtabs and before the scope strip`, w !== null && w.afterSubtabs && w.beforeStrip, w);
  if (w === null) return;
  if (want) claim(`${W} ${label}: Window shows the selected from/to dates`, w.from === want.from && w.to === want.to, { from: w.from, to: w.to, want });
  if (wi === 0) claim(`${W} ${label}: Window control right-aligned`, w.rightGap !== null && w.rightGap <= 1, { rightGap: w.rightGap });
  else claim(`${W} ${label}: Window control full width`, w.width >= w.parentWidth - 1 && w.leftGap <= 1, { width: w.width, parent: w.parentWidth, leftGap: w.leftGap });
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
  // K3b: `W502B_EVIDENCE=cases` captures only the cold case tabs (into their own measurements file).
  if (process.env.W502B_EVIDENCE === "cases") return casesMain();
  // W5-02c K4b: `W502B_EVIDENCE=action` captures only the cold Action detail (into its own measurements file).
  if (process.env.W502B_EVIDENCE === "action") return actionMain();
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

  // K2 ruling 21 (manifest): the positive INC links both selected Findings; UNKNOWN has its one ruled link and limit.
  for (const k of ["positive", "worstcase", "pending", "stale", "unknown"]) {
    const inc = manifest.modes[k].fixture?.incident ?? {};
    const mechs = (inc.finding_links ?? []).map((x) => x.mechanism);
    const want = k === "unknown" ? ["COLD_START_FAILURE"] : ["COLD_START_FAILURE", "COLD_EXCURSION"];
    claim(`manifest ${k}: not blocked, INC links ${want.join("+")}${k === "unknown" ? " with the one-link limit recorded" : ""}`,
      !manifest.modes[k].blocked && JSON.stringify(mechs) === JSON.stringify(want) && (k === "unknown") === Boolean(inc.limit),
      { blocked: manifest.modes[k].blocked ?? null, links: mechs, limit: inc.limit ?? null });
  }
  for (const [wi, [W, width, height]] of WIDTHS.entries()) {
    await size(width, height);
    let m;
    // Positive CURRENT, one row.
    m = await record(W, wi, "positive", workUrl(pBase, P.reads.positive.query), WORK_READY, MEASURE_WORK);
    claim(`${W} positive: rows panel, CURRENT`, m.panelState === "rows" && m.currentness === null, { panel: m.panelState, currentness: m.currentness });
    capWork(W, "positive", m, wi);
    rowClaims(W, "positive", m, 1);
    windowClaims(W, "positive", m, wi, { from: P.reads.positive.query.from.slice(0, 10), to: P.reads.positive.query.to.slice(0, 10) });
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
    // K2 ruling 2: five 160-code-point rows with every `Read full text` disclosure open (the worst-case cap).
    m = await record(W, wi, "worstcase-expanded-open", workUrl(B("worstcase"), wq), WORK_READY, MEASURE_WORK, async () => {
      await js(`document.querySelector('[data-cold-work-show-all]').click()`);
      await waitFor(`!document.querySelector('[data-cold-work-show-all]')`);
      await js(`[...document.querySelectorAll('[data-cold-work-row] details[data-disclosure^="cold-work-title-"], [data-cold-work-row] details[data-disclosure^="cold-work-owner-"]')].forEach((d) => { if (!d.open) d.querySelector(':scope > summary').click(); })`);
      await waitFor(`document.querySelectorAll('[data-cold-work-row] details[data-disclosure^="cold-work-title-"][open]').length >= 5`);
      await sleep(300);
    });
    claim(`${W} worstcase-expanded-open: five title disclosures open`, m.openDisclosures >= 5 && m.rowCount === 5, { open: m.openDisclosures, of: m.disclosures, rows: m.rowCount });
    capWork(W, "worstcase-expanded-open", m, wi, true, false); // K2 ruling 24: panel-cap exemption only
    rowClaims(W, "worstcase-expanded-open", m, 5);
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
      // K2 ruling 1: from the cursor page, Apply a new window: known_at kept, cursor dropped, page one read.
      const knownAt = new URL(m.href, "http://x").searchParams.get("known_at");
      const newFrom = dayShift(wq.from, -1);
      const newTo = wq.to.slice(0, 10);
      m = await record(W, wi, "window-apply", `${B("worstcase")}${next}`, WORK_READY, MEASURE_WORK, async () => {
        await js(setDate("[data-cold-work-window-from]", newFrom));
        await js(setDate("[data-cold-work-window-to]", newTo));
        await js(`document.querySelector('[data-cold-work-window-apply]').click()`);
        await waitFor(`!/cursor=/.test(location.search) && document.querySelector('[data-cold-work-state-panel]') && !document.querySelector('[data-cold-work-state-panel="loading"]')`);
        await sleep(300);
      });
      const q = new URL(m.href, "http://x").searchParams;
      claim(`${W} window-apply: URL carries the new from,to and the same known_at, no cursor`,
        q.get("from") === `${newFrom}T00:00:00Z` && q.get("to") === `${newTo}T00:00:00Z` && q.get("known_at") === knownAt && !q.has("cursor"), m.href);
      claim(`${W} window-apply: page one read (rows panel, 'Show all 5 Actions')`, m.panelState === "rows" && m.rowsTotal === 5 && !m.first, { panel: m.panelState, rows: m.rowsTotal, first: m.first });
      windowClaims(W, "window-apply", m, wi, { from: newFrom, to: newTo });
      capWork(W, "window-apply", m, wi);
    }
    // K2 ruling 1: invalid Window input (from = to) shows the window error, stays on the page and does not navigate.
    {
      const url = workUrl(pBase, P.reads.positive.query);
      m = await record(W, wi, "window-invalid", url, WORK_READY, MEASURE_WORK, async () => {
        const day = P.reads.positive.query.from.slice(0, 10);
        await js(setDate("[data-cold-work-window-from]", day));
        await js(setDate("[data-cold-work-window-to]", day));
        await js(`document.querySelector('[data-cold-work-window-apply]').click()`);
        await waitFor(`document.querySelector('[data-cold-work-window-error]')`);
        await sleep(300);
      });
      claim(`${W} window-invalid: window error shown, URL unchanged`, m.window?.error === "The window may span at most 31 days." && `${pBase}${m.href}` === url, { error: m.window?.error, href: m.href });
      windowClaims(W, "window-invalid", m, wi, null);
      capWork(W, "window-invalid", m, wi);
    }
    // K2 ruling 23: cold Incidents and Maintenance (existing W4 content; K3 not built) with one visible date form.
    {
      const q = { ...P.reads.positive.query };
      if (!q.known_at) q.known_at = P.cutoffs.K3;
      const keep = new URLSearchParams({ from: q.from, to: q.to, known_at: q.known_at }).toString();
      const wantTabs = [`/sites/${SITE}/work?${keep}`, `/sites/${SITE}/work/incidents?${keep}`, `/sites/${SITE}/work/maintenance?${keep}`];
      for (const kind of ["incidents", "maintenance"]) {
        const state = `cold-${kind}`;
        m = await record(W, wi, state, `${pBase}/sites/${SITE}/work/${kind}?${new URLSearchParams(q).toString()}`, CASES_READY, MEASURE_CASES);
        claim(`${W} ${state}: exactly one visible date form, the page-local Window control (no W4 in-panel form)`,
          m.visibleForms.length === 1 && m.visibleForms[0] === "cold-window" && !m.w4Form, { forms: m.visibleForms, w4Form: m.w4Form });
        claim(`${W} ${state}: Window control after the Work subtabs, showing the selected dates`,
          m.windowAfterSubtabs && m.windowFrom === q.from.slice(0, 10) && m.windowTo === q.to.slice(0, 10), { after: m.windowAfterSubtabs, from: m.windowFrom, to: m.windowTo });
        const hq = new URL(m.href, "http://x").searchParams;
        claim(`${W} ${state}: page URL keeps from,to,known_at`, hq.get("from") === q.from && hq.get("to") === q.to && hq.get("known_at") === q.known_at, m.href);
        claim(`${W} ${state}: every Work subtab href keeps from,to,known_at`, JSON.stringify(m.subtabs) === JSON.stringify(wantTabs), { got: m.subtabs, want: wantTabs });
        claim(`${W} ${state}: no document horizontal overflow (scrollWidth <= clientWidth + 1)`, m.docScrollWidth <= m.docClientWidth + 1, { scrollWidth: m.docScrollWidth, clientWidth: m.docClientWidth });
      }
    }
    // PENDING / STALE / UNKNOWN.
    for (const [k, status] of [["pending", "PENDING_RECOMPUTE"], ["stale", "STALE_SOURCE"], ["unknown", "UNKNOWN"]]) {
      const mode = manifest.modes[k];
      m = await record(W, wi, k, workUrl(B(k), mode.reads[k].query), WORK_READY, MEASURE_WORK);
      claim(`${W} ${k}: ${status} notice`, m.currentness === status && m.panelState === "rows", m.currentness);
      capWork(W, k, m, wi);
      rowClaims(W, k, m, 1);
    }
    // 403 / 503. K2 ruling 3: `cold-work-503` is the real WORK_STORE_UNAVAILABLE inside the cold-work panel with a
    // healthy Site read; the earlier `unavailable-503` images were a Site-level refusal and are not this proof.
    for (const [k, b, proc] of [["forbidden-403", fBase, forbidden], ["cold-work-503", uBase, unavailable]]) {
      m = await record(W, wi, k, workUrl(b, proc.query), WORK_READY, MEASURE_WORK);
      if (k === "cold-work-503") claim(`${W} ${k}: Site read healthy (cold Work page mounted, no Site refusal)`, m.siteRefusal === null && m.main !== null, { siteRefusal: m.siteRefusal });
      if (m.siteRefusal) claim(`${W} ${k}: page states a refusal (Site frame), no rows`, m.rowCount === 0, { main: m.siteRefusal, height: m.pageMain });
      claim(`${W} ${k}: refused panel ${proc.expected.code}`, m.panelState === "refused" && m.refusal === proc.expected.code, { panel: m.panelState, refusal: m.refusal, message: m.refusalMessage });
      if (m.siteRefusal) {
        claim(`${W} ${k}: no document horizontal overflow`, m.docScrollWidth <= m.docClientWidth, { scrollWidth: m.docScrollWidth, clientWidth: m.docClientWidth });
        continue;
      }
      claim(`${W} ${k}: Retry visible`, m.retryVisible === true, m.retryVisible);
      if (k === "cold-work-503") {
        claim(`${W} ${k}: panel says 'Cold work unavailable' with the server message and Retry`,
          /Cold work unavailable/.test(m.refusalText ?? "") && Boolean(m.refusalMessage) &&
            !/unexpected shape|could not be reached/.test(m.refusalMessage ?? "") && /Retry/.test(m.refusalText ?? ""),
          { text: m.refusalText, message: m.refusalMessage });
      }
      claim(`${W} ${k}: no row and no mock zero`, m.rowCount === 0 && !/^0\b/.test(m.scope ?? ""), { rows: m.rowCount, scope: m.scope });
      capWork(W, k, m, wi);
    }
    // Domain Action shell: positive Action and a not-found ID.
    for (const [k, id] of [["action-positive", positiveAction], ["action-not-found", NOT_FOUND]]) {
      m = await record(W, wi, k, `${pBase}/sites/${SITE}/actions/${id}/verification`, ACTION_READY, MEASURE_ACTION);
      // W5-02c K4a: a loaded read renders the two mock panels (no state panel); the K4 mode captures them in full.
      const want = k === "action-positive" ? ["loaded", null] : ["not_found", "not-found"];
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

// ---------------------------------------------------------------------------------------------------------------
// W5-02c K4b (`.agent/W5-02c-K4-preflight-rulings.md` rulings 4-8, 12): `W502B_EVIDENCE=action`. The v69
// `cold-action` detail at 1440/390 from the producer's served reads: positive CURRENT (four criteria, completed WR),
// the open `Finding version` (user expansion, no height cap), the explicit K1 cutoff with no linked work, historical,
// pending/stale/unknown, worstcase Action 1 (160-code-point title/owner, intent null, no WR), not found, 403/503
// from the tool-local processes, and the client-side invalid `known_at` refusal beside the server's real 422 body.
const ACTION_K4_READY = `document.querySelector('main[data-domain-action-shell]') && !document.querySelector('main[data-domain-action-shell="loading"]')`;
const MEASURE_ACTION_K4 = `(() => {
  const h = (e) => (e ? Math.round(e.getBoundingClientRect().height) : null);
  const t = (e) => (e?.textContent ?? '').replace(/\\s+/g, ' ').trim();
  const main = document.querySelector('main[data-domain-action-shell]');
  const panels = [...(main?.querySelectorAll('section.panel') ?? [])];
  const titled = (x) => panels.find((p) => t(p.querySelector('h2')) === x) ?? null;
  const crit = titled('Declared outcome criteria');
  const rel = titled('Related activity');
  const strip = document.querySelector('[data-domain-action-strip]');
  // Ruling 12: only a disclosure body whose direct child is the code may scroll; everything else stays in its box.
  const codeBody = (e) => { const b = e.closest('.disclosure__body'); return b !== null && b.querySelector(':scope > code') !== null && getComputedStyle(b).overflowX === 'auto' ? b : null; };
  const outside = (root) => root === null ? [] : [...root.querySelectorAll('*')].filter((e) => {
    const r = e.getBoundingClientRect(); if (r.width === 0 && r.height === 0) return false;
    if (e.closest('.data-table__scroll') && e.closest('.data-table__scroll') !== e) return false;
    const box = (e.tagName === 'CODE' && codeBody(e) ? codeBody(e) : root).getBoundingClientRect();
    return r.left < box.left - 1 || r.right > box.right + 1;
  }).map((e) => e.tagName + (e.className ? '.' + String(e.className).split(' ')[0] : '') + ':' + t(e).slice(0, 40));
  const scrollers = [...(crit?.querySelectorAll('.data-table__scroll') ?? [])];
  const inspect = document.querySelector('[data-domain-action-inspect]');
  const finding = document.querySelector('[data-domain-action-finding-control]');
  const rail = document.querySelector('nav[aria-label="Operator routes"]');
  const body = document.querySelector('[data-domain-action-strip] .disclosure[open] .disclosure__body');
  const code = body?.querySelector(':scope > code') ?? null;
  return {
    href: location.pathname + location.search,
    shell: main?.getAttribute('data-domain-action-shell') ?? null,
    panelState: document.querySelector('[data-domain-action-panel]')?.getAttribute('data-domain-action-panel') ?? null,
    refusal: document.querySelector('[data-domain-action-refusal]')?.getAttribute('data-domain-action-refusal') ?? null,
    refusalText: t(document.querySelector('[data-domain-action-panel="refused"]')),
    refusalMessage: t(document.querySelector('[data-domain-action-refusal-message]')),
    retryVisible: (() => { const b = document.querySelector('[data-domain-action-retry]'); if (!b) return false; const r = b.getBoundingClientRect(); return r.width > 0 && r.right <= innerWidth + 1; })(),
    heading: t(document.querySelector('main h1')),
    headingFits: (() => { const e = document.querySelector('main h1'); return e ? e.scrollWidth <= e.clientWidth + 1 : null; })(),
    headings: panels.map((p) => t(p.querySelector('h2'))),
    panelCount: panels.length,
    statusLine: t(document.querySelector('[data-domain-action-status-line]')),
    owner: t(document.querySelector('[data-domain-action-owner]')),
    ownerWrap: (() => { const e = document.querySelector('[data-domain-action-owner]'); return e ? getComputedStyle(e).overflowWrap : null; })(),
    headingWrap: (() => { const e = document.querySelector('main h1'); return e ? getComputedStyle(e).overflowWrap : null; })(),
    revisionOpen: Boolean(body),
    revisionText: t(code),
    revisionOneLine: code ? getComputedStyle(code).whiteSpace === 'nowrap' && code.getClientRects().length === 1 : null,
    revisionBodyInsideStrip: body && strip ? (() => { const b = body.getBoundingClientRect(), s = strip.getBoundingClientRect(); return b.left >= s.left - 1 && b.right <= s.right + 1; })() : null,
    revisionReadable: body && code ? body.scrollWidth <= body.clientWidth + 1 || getComputedStyle(body).overflowX === 'auto' : null,
    rows: [...(crit?.querySelectorAll('tbody tr') ?? [])].map((tr) => [...tr.querySelectorAll('td')].map(t)),
    columns: [...(crit?.querySelectorAll('thead th') ?? [])].map(t),
    intentMissing: t(document.querySelector('[data-domain-action-intent-missing]')),
    related: document.querySelector('[data-domain-action-related]')?.getAttribute('data-domain-action-related') ?? null,
    relatedSentence: t(document.querySelector('[data-domain-action-related-sentence]')),
    inspect: inspect ? { tag: inspect.tagName, type: inspect.getAttribute('type'), cls: inspect.className, disabled: inspect.disabled, text: t(inspect), describedBy: inspect.getAttribute('aria-describedby'), target: inspect.getAttribute('data-domain-action-inspect-target') } : null,
    inspectNote: (() => { const id = inspect?.getAttribute('aria-describedby'); const n = id ? document.getElementById(id) : null; return n ? { text: t(n), visible: n.getBoundingClientRect().width > 0 } : null; })(),
    finding: finding ? { tag: finding.tagName, text: t(finding), interactive: finding.closest('a,button') !== null || finding.hasAttribute('href') || finding.hasAttribute('tabindex'), note: t(finding.nextElementSibling) } : null,
    relatedLinks: rel ? rel.querySelectorAll('a').length : null,
    currentness: document.querySelector('[data-domain-action-currentness]')?.getAttribute('data-domain-action-currentness') ?? null,
    currentnessAfterStrip: (() => { const n = document.querySelector('[data-domain-action-currentness]'); return n ? n.previousElementSibling === strip && n.nextElementSibling === crit : null; })(),
    noticeText: t(document.querySelector('[data-domain-action-notice]')),
    noticeLast: (() => { const n = document.querySelector('[data-domain-action-notice]'); return n ? n.previousElementSibling === rel && n.nextElementSibling === null : null; })(),
    railCurrent: rail ? [...rail.querySelectorAll('a[aria-current="page"]')].map(t) : null,
    railActive: rail ? [...rail.querySelectorAll('a.active')].map(t) : null,
    railLinks: rail ? rail.querySelectorAll('a').length : null,
    hasDue: /\\bDue\\b/.test(main?.innerText ?? ''),
    docScrollWidth: document.documentElement.scrollWidth,
    docClientWidth: document.documentElement.clientWidth,
    main: h(main), strip: h(strip), criteria: h(crit), relatedPanel: h(rel),
    notice: h(document.querySelector('[data-domain-action-notice]')),
    currentnessNotice: h(document.querySelector('[data-domain-action-currentness]')),
    statePanel: h(document.querySelector('[data-domain-action-panel]')?.closest('section.panel')),
    stripOutside: outside(strip), critOutside: outside(crit), relOutside: outside(rel),
    tableScrollsInPanel: scrollers.length > 0 && scrollers.every((x) => { const r = x.getBoundingClientRect(), p = crit.getBoundingClientRect(); return r.left >= p.left - 1 && r.right <= p.right + 1; }),
  };
})()`;
const RESULTS_K4 = ["Not tested", "Not tested", "Not established", "Pending"];
const CRITERIA_K4 = [
  ["Automatic start", "Accepted command followed by successful running status"],
  ["Power delivery", "Generator supply reaches the cooling system"],
  ["Cooling recovery", "Temperature recovery within declared test conditions"],
  ["Recurrence", "Covered observation window without a qualifying repeat"],
];
async function recordK4(W, wi, state, url, afterLoad) {
  const ok = await go(url, ACTION_K4_READY);
  if (afterLoad) await afterLoad();
  await sleep(200);
  const m = await js(MEASURE_ACTION_K4);
  claim(`${W} ${state}: settled`, ok, m.shell);
  const file = await shot(`w502c-k4-${W}-${state}`);
  captures.push({ state, width: WIDTHS[wi][1], file, url, measurements: m });
  return m;
}
function capK4(W, k, m, wi, expanded = false) {
  claim(`${W} ${k}: no document horizontal overflow`, m.docScrollWidth <= m.docClientWidth, { scrollWidth: m.docScrollWidth, clientWidth: m.docClientWidth });
  claim(`${W} ${k}: heading text fits its box`, m.headingFits !== false, m.headingFits);
  claim(`${W} ${k}: strip and panel content inside their boxes`, m.stripOutside.length === 0 && m.critOutside.length === 0 && m.relOutside.length === 0, { strip: m.stripOutside, criteria: m.critOutside, related: m.relOutside });
  const caps = [["page main", m.main, ACTION_CAPS.main[wi]], ["strip", m.strip, ACTION_CAPS.strip[wi]], ["criteria panel", m.criteria, ACTION_CAPS.criteria[wi]],
    ["Related activity panel", m.relatedPanel, ACTION_CAPS.related[wi]], ["concluding notice", m.notice, ACTION_CAPS.notice[wi]], ["currentness notice", m.currentnessNotice, ACTION_CAPS.notice[wi]]];
  for (const [name, got, cap] of caps) {
    if (got === null) continue;
    if (expanded) results.push({ name: `${W} ${k}: INFO ${name} ${got} px (user-expanded; height cap ${cap} exempt, ruling 7)`, ok: true, detail: got });
    else claim(`${W} ${k}: ${name} <= ${cap}`, got <= cap, got);
  }
}
function loadedK4(W, k, m, want) {
  claim(`${W} ${k}: loaded, two mock panels in order, no state panel`, m.shell === "loaded" && m.panelState === null && JSON.stringify(m.headings) === JSON.stringify(["Declared outcome criteria", "Related activity"]), { shell: m.shell, panel: m.panelState, headings: m.headings });
  claim(`${W} ${k}: Actions alone selected in the rail (nine links)`, JSON.stringify(m.railCurrent) === '["Actions"]' && JSON.stringify(m.railActive) === '["Actions"]' && m.railLinks === 9, { current: m.railCurrent, active: m.railActive, links: m.railLinks });
  claim(`${W} ${k}: concluding notice last with the mock text`, m.noticeLast === true && m.noticeText === "Completed inspection does not establish successful service restoration.", { last: m.noticeLast, text: m.noticeText });
  claim(`${W} ${k}: currentness ${want.status === "CURRENT" ? "absent" : `${want.status} right after the strip, before criteria`}`, want.status === "CURRENT" ? m.currentness === null : m.currentness === want.status && m.currentnessAfterStrip === true, { currentness: m.currentness, placed: m.currentnessAfterStrip });
  if (want.intent) {
    claim(`${W} ${k}: four declared criteria with the stored initial results in the mock columns`, JSON.stringify(m.columns) === JSON.stringify(["Criterion", "Required evidence", "Current result"]) && JSON.stringify(m.rows) === JSON.stringify(CRITERIA_K4.map((c, i) => [...c, RESULTS_K4[i]])), { columns: m.columns, rows: m.rows });
    claim(`${W} ${k}: criteria table scroller inside its panel`, m.tableScrollsInPanel === true, m.tableScrollsInPanel);
  } else {
    claim(`${W} ${k}: criteria heading kept, exact missing sentence, no table`, m.intentMissing === "No outcome criteria have been declared for this Action." && m.rows.length === 0 && m.columns.length === 0, { missing: m.intentMissing, rows: m.rows.length });
  }
  if (want.work) {
    claim(`${W} ${k}: completed selected WR sentence`, m.related === "completed" && m.relatedSentence === `${want.work.case_title} ${want.work.case_code} is complete. A witnessed outcome test remains required.`, m.relatedSentence);
    claim(`${W} ${k}: Inspect is a live secondary button to the selected WR Overview`, m.inspect?.tag === "BUTTON" && m.inspect.type === "button" && m.inspect.cls === "button" && !m.inspect.disabled && (m.inspect.target ?? "").startsWith(`/maintenance/requests/${want.work.case_id}?site_id=${SITE}`), m.inspect);
  } else {
    claim(`${W} ${k}: no completed inspection sentence`, m.related === "not-linked" && m.relatedSentence === "No completed inspection is linked to this Action.", m.relatedSentence);
    claim(`${W} ${k}: Inspect disabled, described by the visible adjacent sentence`, m.inspect?.tag === "BUTTON" && m.inspect.cls === "button" && m.inspect.disabled === true && m.inspectNote?.visible === true && m.inspectNote.text === "Maintenance detail is unavailable for this record.", { inspect: m.inspect, note: m.inspectNote });
  }
  claim(`${W} ${k}: Open source Finding is muted noninteractive text with its sentence; no link in Related activity`, m.finding?.tag === "SPAN" && m.finding.text === "Open source Finding →" && m.finding.interactive === false && m.finding.note === "The selected Finding revision cannot be opened here yet." && m.relatedLinks === 0, m.finding);
  claim(`${W} ${k}: owner and heading wrap anywhere; no Due date`, m.ownerWrap === "anywhere" && m.headingWrap === "anywhere" && m.hasDue === false, { owner: m.ownerWrap, heading: m.headingWrap, due: m.hasDue });
}
async function actionMain() {
  const portOf = { positive: 8971, worstcase: 8972, pending: 8973, stale: 8974, unknown: 8975 };
  const B = (k) => `${HOST}:${portOf[k] - 3500}`;
  const P = manifest.modes.positive;
  const D = P.detail_reads ?? {};
  const WD = manifest.modes.worstcase.detail_reads ?? {};
  const forbidden = manifest.processes.forbidden;
  const unavailable = manifest.processes.unavailable;
  const procBase = (p) => `${HOST}:${Number(new URL(p.api_base).port) - 3500}`;
  const aid = P.actions[0].id;
  const worst = manifest.modes.worstcase.actions[1];
  const url = (base, id, knownAt) => `${base}/sites/${SITE}/actions/${id}/verification${knownAt ? `?known_at=${encodeURIComponent(knownAt)}` : ""}`;
  claim("manifest: positive detail reads (CURRENT completed WR; K1 cutoff with no work) and worstcase Action 1 read present",
    D["action-current"]?.work?.request_state === "COMPLETED" && D["action-not-linked"]?.work?.case_id === null && WD["action-worstcase"]?.intent === false &&
      WD["action-worstcase"]?.title_code_points === 160 && WD["action-worstcase"]?.owner_code_points === 160,
    { current: D["action-current"]?.work, notLinked: D["action-not-linked"]?.query, worst: WD["action-worstcase"] });
  // P-K4b-1: the server's own 422 for an invalid known_at, read directly (the browser refuses it before fetching).
  const api422 = await fetch(`http://127.0.0.1:${portOf.positive}/api/sites/${SITE}/domain-work/actions/${aid}?known_at=not-a-time`)
    .then(async (r) => ({ status: r.status, body: await r.json().catch(() => null) }))
    .catch((e) => ({ status: 0, body: String(e) }));
  claim("API 422: invalid known_at answers 422 INVALID_KNOWN_AT (captured beside the client refusal, P-K4b-1)",
    api422.status === 422 && api422.body?.detail?.code === "INVALID_KNOWN_AT", api422);
  const notLinkedAt = D["action-not-linked"]?.query?.known_at;
  const cut = P.cutoffs;
  const modeCut = (k) => manifest.modes[k].reads?.[k]?.query?.known_at;
  for (const [wi, [W, width, height]] of WIDTHS.entries()) {
    await size(width, height);
    let m;
    m = await recordK4(W, wi, "action-positive", url(B("positive"), aid, null));
    loadedK4(W, "action-positive", m, { status: "CURRENT", intent: true, work: D["action-current"]?.work });
    claim(`${W} action-positive: status line owner · short Site · Finding id8`, /^Maintenance lead · \S+ · Finding [0-9a-f]{8}/.test(m.statusLine), m.statusLine);
    capK4(W, "action-positive", m, wi);
    // The user-opened Finding version: exempt from height caps; full UUID on one line inside the strip, no overflow.
    m = await recordK4(W, wi, "action-positive-version-open", url(B("positive"), aid, null), async () => {
      await js(`(() => { const d = document.querySelector('[data-domain-action-strip] details'); if (d) d.open = true; return Boolean(d); })()`);
    });
    claim(`${W} action-positive-version-open: full revision UUID readable on one line inside the strip`,
      m.revisionOpen && /^[0-9a-f-]{36}$/.test(m.revisionText) && m.revisionOneLine === true && m.revisionBodyInsideStrip === true && m.revisionReadable === true,
      { open: m.revisionOpen, text: m.revisionText, oneLine: m.revisionOneLine, inside: m.revisionBodyInsideStrip, readable: m.revisionReadable });
    capK4(W, "action-positive-version-open", m, wi, true);
    m = await recordK4(W, wi, "action-not-linked", url(B("positive"), aid, notLinkedAt));
    loadedK4(W, "action-not-linked", m, { status: D["action-not-linked"]?.status, intent: D["action-not-linked"]?.intent, work: null });
    capK4(W, "action-not-linked", m, wi);
    m = await recordK4(W, wi, "action-historical", url(B("positive"), aid, cut.K3));
    loadedK4(W, "action-historical", m, { status: "HISTORICAL", intent: true, work: D["action-current"]?.work });
    capK4(W, "action-historical", m, wi);
    for (const [k, status] of [["pending", "PENDING_RECOMPUTE"], ["stale", "STALE_SOURCE"], ["unknown", "UNKNOWN"]]) {
      const id = manifest.modes[k].actions[0].id;
      m = await recordK4(W, wi, `action-${k}`, url(B(k), id, modeCut(k)));
      claim(`${W} action-${k}: ${status} notice right after the strip, two panels`, m.shell === "loaded" && m.currentness === status && m.currentnessAfterStrip === true && m.headings.length === 2, { currentness: m.currentness, headings: m.headings });
      capK4(W, `action-${k}`, m, wi);
    }
    m = await recordK4(W, wi, "action-worstcase", url(B("worstcase"), worst.id, null));
    loadedK4(W, "action-worstcase", m, { status: WD["action-worstcase"]?.status ?? "CURRENT", intent: false, work: null });
    claim(`${W} action-worstcase: full 160-code-point title and owner shown whole`, [...m.heading].length >= 160 && [...m.owner].length === 160 && !/…/.test(m.heading + m.owner), { heading: [...m.heading].length, owner: [...m.owner].length });
    capK4(W, "action-worstcase", m, wi);
    m = await recordK4(W, wi, "action-not-found", url(B("positive"), "00000000-0000-4000-8000-0000000000aa", null));
    claim(`${W} action-not-found: one untitled not-found panel`, m.shell === "not_found" && m.panelState === "not-found" && m.panelCount === 1 && m.headings[0] === "", { shell: m.shell, panel: m.panelState, headings: m.headings });
    capK4(W, "action-not-found", m, wi);
    for (const [k, proc] of [["action-403", forbidden], ["action-503", unavailable]]) {
      m = await recordK4(W, wi, k, url(procBase(proc), aid, null));
      claim(`${W} ${k}: one untitled refusal panel, 'Cold work unavailable', server message and Retry (${proc.expected.http} ${proc.expected.code})`,
        m.shell === "refused" && m.panelCount === 1 && m.headings[0] === "" && m.refusal === proc.expected.code && /Cold work unavailable/.test(m.refusalText) &&
          m.refusalMessage.length > 0 && !/unexpected shape|could not be reached/.test(m.refusalMessage) && m.retryVisible === true,
        { refusal: m.refusal, text: m.refusalText, message: m.refusalMessage, retry: m.retryVisible });
      capK4(W, k, m, wi);
    }
    m = await recordK4(W, wi, "action-422-client", url(B("positive"), aid, "not-a-time"));
    claim(`${W} action-422-client: the client refuses the invalid known_at before fetching (INVALID_KNOWN_AT), one untitled panel`,
      m.shell === "refused" && m.refusal === "INVALID_KNOWN_AT" && m.panelCount === 1 && m.retryVisible === true, { refusal: m.refusal, message: m.refusalMessage });
    capK4(W, "action-422-client", m, wi);
  }
  const failed = results.filter((r) => !r.ok).length;
  writeFileSync(join(OUT, "w502c-k4-measurements.json"), JSON.stringify({ manifest_revision: manifest.revision, caps: { action: ACTION_CAPS }, api422, captures, claims: results, failed }, null, 2));
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
