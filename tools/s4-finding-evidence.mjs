/**
 * S4-01 phase 3: app-vs-mock evidence for the Site Finding detail (`finding:1,2,4`), with layout
 * measurements, keyboard interaction and reload checks, from the installed Chrome over the DevTools
 * Protocol (same approach as tools/s3-dispatch-evidence.mjs; no dependency).
 *
 * Run against the walkthrough servers (tools/s4_finding_walkthrough.py prepare + serve, frontend on 5340):
 *   node tools/s4-finding-evidence.mjs http://localhost:5340 <screenshot-dir>
 *
 * Finding IDs come from the walkthrough's copy of the producer run record. Every claim is measured and
 * printed; the run exits non-zero if any fails. Set-based claims report their size.
 *
 * S4-03 phase 2 adds the Finding Evidence child view (`finding-evidence:1,2`,
 * `/sites/{site}/findings/{id}/evidence?revision_id=&offset=&record=`), compared with the read API's own counts.
 * Environment:
 *   ASSETOPS_S4_WALK_WORK      walkthrough work folder holding the run record (default: the S4-01 walkthrough's)
 *   ASSETOPS_CDP_PORT          Chrome DevTools port (default 9343)
 *   ASSETOPS_S4_EVIDENCE_SUITE all (default: finding + evidence) | finding | evidence | closed | broken
 *     closed: run after `s4_finding_walkthrough.py --db .. --work .. close-gate` on a private copy (audit-only read)
 *     broken: run after deliberately tampering one envelope in a PRIVATE copy (ASSETOPS_S4_BROKEN_FINDING names
 *             the Finding ID whose latest version cites it)
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const BASE = process.argv[2] ?? "http://localhost:5340";
const OUT = process.argv[3] ?? join(tmpdir(), "s4-finding-evidence");
const SITE = "KOBO-001";
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9343);
const SUITE = process.env.ASSETOPS_S4_EVIDENCE_SUITE ?? "all";
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  ["desktop", 1440, 1000],
  ["narrow", 390, 900],
];
mkdirSync(OUT, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "assetops-s4-cdp-"));
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
        const ws = new WebSocket(page.webSocketDebuggerUrl);
        await new Promise((res, rej) => {
          ws.addEventListener("open", res);
          ws.addEventListener("error", rej);
        });
        return ws;
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
  return r.result.value;
}
async function waitFor(expression, ms = 45000) {
  const end = Date.now() + ms;
  while (Date.now() < end) {
    if (await js(`Boolean(${expression})`)) return true;
    await sleep(150);
  }
  return false;
}
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
let viewport = [1440, 1000];
async function shot(name) {
  // The app shell scrolls inside its own frame, so grow the viewport to the tallest scroller for the capture.
  const tall = await js(`Math.max(document.documentElement.scrollHeight,
    ...[...document.querySelectorAll('*')].filter(e => e.scrollHeight > e.clientHeight + 1 && getComputedStyle(e).overflowY !== 'visible')
      .map(e => e.scrollHeight + e.getBoundingClientRect().top))`);
  const h = Math.min(Math.ceil(tall), 7000);
  await send("Emulation.setDeviceMetricsOverride", { width: viewport[0], height: h, deviceScaleFactor: 1, mobile: viewport[0] < 600 });
  await sleep(300);
  const r = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(join(OUT, `${name}.png`), Buffer.from(r.data, "base64"));
  await size(viewport[0], viewport[1]);
}
const overflow = () =>
  js(`(() => { const d = document.documentElement; return { scrollWidth: d.scrollWidth, clientWidth: d.clientWidth,
      wide: [...document.querySelectorAll('.site-finding *')].filter(e => e.getBoundingClientRect().right > d.clientWidth + 1
      && !e.closest('.data-table__scroll') && ![...e.children].some(c => c.getBoundingClientRect().right > d.clientWidth + 1))
      .map(e => (e.className || e.tagName) + ':' + Math.round(e.getBoundingClientRect().width)).slice(0, 6) }; })()`);

const WALK = process.env.ASSETOPS_S4_WALK_WORK ?? join(process.env.LOCALAPPDATA ?? tmpdir(), "AssetOps", "s4-finding-walkthrough");
const RUN = join(WALK, "s4-finding-cases-run.json");
const run = JSON.parse(readFileSync(RUN, "utf-8"));
const byAnchor = (prefix) => {
  const f = run.findings.find((x) => x.anchor_start.startsWith(prefix));
  if (!f) throw new Error(`no Finding anchored at ${prefix} in ${RUN}`);
  return f;
};
const F01 = byAnchor("2026-10-06 08:00");
const F02 = byAnchor("2026-10-08 23:20");
const F03 = byAnchor("2026-10-11 09:30");
const F04 = byAnchor("2026-10-13 08:30");
const F05 = byAnchor("2026-10-21 08:00");
const F06M = byAnchor("2026-10-15 13:00");
const READY = "document.querySelector('[data-finding-lifecycle], [data-finding-read]')";
const finding = (f, q = "") => `${BASE}/sites/${SITE}/findings/${f.finding_id}${q}`;
const STATE = `(() => ({
  url: location.pathname + location.search,
  lifecycle: document.querySelector('[data-finding-lifecycle]')?.dataset.findingLifecycle,
  revision: document.querySelector('[data-finding-revision]')?.dataset.findingRevision,
  lead: document.querySelector('.site-finding__lead h2')?.textContent,
  currentness: document.querySelector('[data-chip="currentness"]')?.textContent,
  headings: [...document.querySelectorAll('.site-finding h2')].map(h => h.textContent),
  cards: document.querySelectorAll('[data-finding-card]').length,
  records: document.querySelectorAll('[data-evidence-id]').length,
  blocks: document.querySelectorAll('[data-portion]').length,
  pressed: document.querySelector('[data-portion][aria-pressed="true"]')?.getAttribute('aria-label') ?? null,
  dispatchDays: [...document.querySelectorAll('[data-finding-dispatch-day]')].map(a => a.getAttribute('href')),
  recurrence: document.querySelector('[data-finding-recurrence]')?.textContent ?? null,
  sentence: document.querySelector('[data-finding-lifecycle-sentence]')?.textContent ?? null,
}))()`;
const PANELS = ["What happened", "What limits this conclusion", "What to do next", "Where to look next"];

async function enter() {
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13, text: "\r" });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
}

// ---- S4-03 phase 2: the Finding Evidence child view ----
const F01G = byAnchor("2026-10-02 05:15");
const EV_READY = "document.querySelector('[data-finding-evidence], [data-finding-read]')";
const evidenceUrl = (id, q = "") => `${BASE}/sites/${SITE}/findings/${id}/evidence${q}`;
const api = (id, q = "") =>
  js(`fetch('/api/sites/${SITE}/findings/${id}/evidence${q}', { credentials: 'include' })
    .then(async r => ({ status: r.status, body: await r.json().catch(() => null) }))`);
const EV_STATE = `(() => {
  const sec = document.querySelector('[data-finding-evidence]');
  const leads = [...document.querySelectorAll('.site-finding-evidence .site-finding__lead, .site-finding-evidence [data-evidence-latest-at-read], .site-finding-evidence [data-evidence-pinned-latest]')];
  return {
    url: location.pathname + location.search,
    read: document.querySelector('[data-finding-read]')?.dataset.findingRead ?? null,
    revision: sec?.dataset.findingRevision ?? null,
    selectedBy: sec?.dataset.evidenceSelectedBy ?? null,
    lineage: sec?.dataset.evidenceLineage ?? null,
    total: sec ? Number(sec.dataset.evidenceTotal) : null,
    citedText: document.querySelector('[data-evidence-cited-total]')?.textContent ?? null,
    inputText: document.querySelector('[data-evidence-input-total]')?.textContent ?? null,
    citedVsInput: document.querySelector('[data-evidence-cited-vs-input]')?.textContent ?? null,
    latestAtRead: Boolean(document.querySelector('[data-evidence-latest-at-read]')),
    pinnedLatest: Boolean(document.querySelector('[data-evidence-pinned-latest]')),
    earlier: Boolean(document.querySelector('[data-evidence-earlier-version]')),
    auditOnly: Boolean(document.querySelector('[data-evidence-audit-only]')),
    firstLead: leads[0] ? Object.keys(leads[0].dataset).join(',') : null,
    rows: document.querySelectorAll('[data-evidence-id]').length,
    firstRow: document.querySelector('[data-evidence-id]')?.dataset.evidenceId ?? null,
    pageRange: document.querySelector('[data-evidence-page-range]')?.textContent ?? null,
    next: document.querySelector('[data-evidence-page="next"]')?.getAttribute('href') ?? null,
    record: document.querySelector('[data-evidence-record]')?.dataset.evidenceRecord ?? null,
    recordLink: document.querySelector('[data-evidence-record-link]')?.getAttribute('href') ?? null,
    dispatchLinks: document.querySelectorAll('[data-evidence-dispatch-link]').length,
    lineageBroken: Boolean(document.querySelector('[data-evidence-lineage-broken]')),
    brokenRecords: [...document.querySelectorAll('[data-evidence-broken-record]')].map(e => e.dataset.evidenceBrokenRecord),
    recordBreaks: [...document.querySelectorAll('[data-evidence-record-break]')].map(e => e.dataset.evidenceRecordBreak),
    section: document.querySelector('[data-finding-section][aria-current="page"]')?.dataset.findingSection ?? null,
  };
})()`;
// Horizontal overflow inside the Evidence view; table content scrolls in its own frame and is excluded.
const evidenceOverflow = () =>
  js(`(() => { const d = document.documentElement;
    const all = [...document.querySelectorAll('.site-finding-evidence *')].filter(e => !e.closest('.data-table__scroll'));
    return { scrollWidth: d.scrollWidth, clientWidth: d.clientWidth, measured: all.length,
      wide: all.filter(e => e.getBoundingClientRect().right > d.clientWidth + 1
        && ![...e.children].some(c => c.getBoundingClientRect().right > d.clientWidth + 1))
        .map(e => (e.className || e.tagName) + ':' + Math.round(e.getBoundingClientRect().right)).slice(0, 6) }; })()`);
const noOverflow = (o) => o.measured > 0 && o.scrollWidth <= o.clientWidth && o.wide.length === 0;
async function key(name, code, vk) {
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: name, code, windowsVirtualKeyCode: vk });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: name, code, windowsVirtualKeyCode: vk });
}
/** Press Tab from the top of the page until the focused element matches `selector`; returns the presses used. */
async function tabTo(selector, max = 400) {
  await js(`(document.activeElement && document.activeElement.blur(), window.scrollTo(0, 0), true)`);
  for (let i = 1; i <= max; i += 1) {
    await key("Tab", "Tab", 9);
    if (await js(`Boolean(document.activeElement && document.activeElement.matches(${JSON.stringify(selector)}))`)) return i;
  }
  return -1;
}

async function evidenceSuite(label) {
  await go(`${BASE}/mockups/v69/index.html#/finding-evidence`, "document.body && document.body.innerText.includes('Evidence bundle')");
  const mock = await js(`({ panels: ['Evidence bundle', 'Inspect source lineage'].filter(p => document.body.innerText.includes(p)),
    rows: ['Generator state / power', 'Battery SOC', 'PCS capability', 'PV capability / delivered load'].filter(p => document.body.innerText.includes(p)) })`);
  claim(`${label}: mock #/finding-evidence renders finding-evidence:1 and :2`, mock.panels.length === 2, mock);
  await shot(`mock-finding-evidence-${label}`);

  // Latest at read time: F01-gateway, no revision_id.
  const id = F01G.finding_id;
  await go(evidenceUrl(id), EV_READY);
  const a = await api(id, "?limit=50");
  const s = await js(EV_STATE);
  const c = a.body?.counts ?? {};
  claim(`${label} evidence latest: API read 200 and the Evidence section is current`, a.status === 200 && s.section === "evidence", { status: a.status, section: s.section });
  claim(`${label} evidence latest: labelled latest at read time, selected by LATEST_RECORDED`,
    s.latestAtRead && s.selectedBy === "LATEST_RECORDED" && s.revision === a.body?.selection?.revision_id,
    { latestAtRead: s.latestAtRead, selectedBy: s.selectedBy, revision: s.revision, apiRevision: a.body?.selection?.revision_id });
  claim(`${label} evidence latest: total equals API counts.cited_total; cited and input counts stated separately`,
    s.total === c.cited_total && Number(s.citedText) === c.cited_total && Number(s.inputText) === c.input_distinct_total
      && c.cited_total !== c.input_distinct_total,
    { appTotal: s.total, citedText: s.citedText, inputText: s.inputText, apiCited: c.cited_total, apiInput: c.input_distinct_total });
  claim(`${label} evidence latest: page shows min(50, total) cited rows; first row equals the API's first`,
    s.rows === Math.min(50, c.cited_total) && s.firstRow === a.body?.records?.[0]?.evidence_id,
    { rows: s.rows, firstRow: s.firstRow, apiFirst: a.body?.records?.[0]?.evidence_id, range: s.pageRange });
  claim(`${label} evidence latest: lineage COMPLETE matches the API`, s.lineage === a.body?.lineage?.status && s.lineage === "COMPLETE",
    { app: s.lineage, api: a.body?.lineage?.status });
  let o = await evidenceOverflow();
  claim(`${label} evidence latest: no sideways overflow in .site-finding-evidence (outside table scrollers)`, noOverflow(o), o);
  await shot(`app-evidence-latest-${label}`);

  // Keyboard: Tab to the first record link, Enter, then reload.
  const presses = await tabTo("[data-evidence-select]");
  const focused = await js(`document.activeElement?.dataset?.evidenceSelect ?? null`);
  await key("Enter", "Enter", 13);
  await waitFor(`location.search.includes('record=') && document.querySelector('[data-evidence-record]')`, 15000);
  await sleep(300);
  const keyed = await js(EV_STATE);
  claim(`${label} evidence keyboard: Tab reaches the first record link and Enter selects it (record= in the address)`,
    presses > 0 && focused === s.firstRow && new URLSearchParams(keyed.url.split("?")[1]).get("record") === focused && keyed.record === focused,
    { presses, focused, url: keyed.url, record: keyed.record });
  await send("Page.reload");
  await waitFor(`document.querySelector('[data-evidence-record]')`);
  await sleep(300);
  const reloaded = await js(EV_STATE);
  claim(`${label} evidence keyboard: reload keeps site, Finding, version, offset and record`,
    reloaded.url === keyed.url && reloaded.revision === keyed.revision && reloaded.record === keyed.record
      && reloaded.url.startsWith(`/sites/${SITE}/findings/${id}/evidence`),
    { before: keyed.url, after: reloaded.url, record: reloaded.record, revision: reloaded.revision });
  if (s.next) {
    const nextPresses = await tabTo('[data-evidence-page="next"]');
    await key("Enter", "Enter", 13);
    await waitFor(`location.search.includes('offset=50') && document.querySelector('[data-evidence-id]')`, 15000);
    await sleep(300);
    const paged = await js(EV_STATE);
    claim(`${label} evidence keyboard: Tab to Next page and Enter opens offset=50 and drops the record`,
      nextPresses > 0 && /offset=50/.test(paged.url) && !/record=/.test(paged.url), { nextPresses, url: paged.url, range: paged.pageRange });
  }

  // Exact version + record.
  const rev = a.body.selection.revision_id;
  const rec = a.body.records[0].evidence_id;
  await go(evidenceUrl(id, `?revision_id=${rev}&record=${rec}`), "document.querySelector('[data-evidence-record], [data-finding-read]')");
  const p = await js(EV_STATE);
  const expectLink = `/sites/${SITE}/evidence?view=analysis&record=${rec}`;
  claim(`${label} evidence pinned record: exact version opens with the selected record and its inspector link`,
    p.pinnedLatest && p.revision === rev && p.record === rec && p.recordLink === expectLink && p.selectedBy === "EXACT_REVISION_ID",
    { pinnedLatest: p.pinnedLatest, revision: p.revision, record: p.record, recordLink: p.recordLink, expectLink });
  o = await evidenceOverflow();
  claim(`${label} evidence pinned record: no sideways overflow (record panel included)`, noOverflow(o), o);
  await shot(`app-evidence-pinned-record-${label}`);

  // Page 2.
  if (c.cited_total > 50) {
    await go(evidenceUrl(id, `?revision_id=${rev}&offset=50`), EV_READY);
    const a2 = await api(id, `?revision_id=${rev}&offset=50&limit=50`);
    const p2 = await js(EV_STATE);
    claim(`${label} evidence page 2: offset=50 rows match the API page and the range is stated`,
      p2.rows === a2.body?.page?.returned && p2.firstRow === a2.body?.records?.[0]?.evidence_id && /51/.test(p2.pageRange ?? ""),
      { rows: p2.rows, apiReturned: a2.body?.page?.returned, firstRow: p2.firstRow, apiFirst: a2.body?.records?.[0]?.evidence_id, range: p2.pageRange });
    await shot(`app-evidence-page2-${label}`);
  } else {
    claim(`${label} evidence page 2: not applicable (total ${c.cited_total} <= 50)`, true);
  }

  // Earlier version: F04 version 1 pinned.
  const r1 = F04.revisions[0].revision_id;
  const r2 = F04.revisions[1].revision_id;
  await go(evidenceUrl(F04.finding_id, `?revision_id=${r1}`), EV_READY);
  const e1 = await api(F04.finding_id, `?revision_id=${r1}&limit=1`);
  const e2 = await api(F04.finding_id, `?revision_id=${r2}&limit=1`);
  const el = await api(F04.finding_id, `?limit=1`);
  const ev = await js(EV_STATE);
  claim(`${label} evidence earlier version: F04 v1 leads with the earlier-version notice; total equals API v1, differs from v2`,
    ev.earlier && ev.firstLead === "evidenceEarlierVersion" && ev.revision === r1 && ev.total === e1.body?.counts?.cited_total
      && e1.body?.counts?.cited_total !== e2.body?.counts?.cited_total,
    { earlier: ev.earlier, firstLead: ev.firstLead, appTotal: ev.total, apiV1: e1.body?.counts?.cited_total, apiV2: e2.body?.counts?.cited_total,
      apiLatest: el.body?.counts?.cited_total, versions: F04.revisions.length });
  await shot(`app-evidence-earlier-${label}`);

  // Unknown version: refused, address kept.
  const unknown = "0b7e4c1a-5d1e-4f7a-9c2b-3e8d6f1a2b4c";
  const missingUrl = evidenceUrl(id, `?revision_id=${unknown}`);
  await go(missingUrl, EV_READY);
  const m = await js(EV_STATE);
  claim(`${label} evidence unknown version: not_found, address unchanged, latest not substituted`,
    m.read === "not_found" && m.url === `/sites/${SITE}/findings/${id}/evidence?revision_id=${unknown}` && m.revision === null,
    { read: m.read, url: m.url, revision: m.revision });
  await shot(`app-evidence-missing-version-${label}`);

  // Legacy assessment-keyed Evidence tab.
  const candidates = await js(`(async () => {
    const ids = new Set();
    const walk = (v) => { if (Array.isArray(v)) v.forEach(walk); else if (v && typeof v === 'object') for (const [k, x] of Object.entries(v)) {
      if (k === 'assessment_id' && typeof x === 'string') ids.add(x); else walk(x); } };
    for (const path of ['/api/sites/${SITE}/findings', '/api/findings', '/api/sites/${SITE}/dispatch']) {
      walk(await fetch(path).then(r => r.ok ? r.json() : null).catch(() => null));
    }
    const out = [];
    for (const x of ids) { const s = await fetch('/api/sites/${SITE}/assessments/' + encodeURIComponent(x)).then(r => r.status).catch(() => 0);
      out.push({ id: x, status: s }); if (s === 200) break; }
    return out; })()`);
  const usable = candidates.find((x) => x.status === 200);
  if (!usable) {
    claim(`${label} evidence legacy tab: skipped, no legacy assessment ID readable on this stack`, true, { candidates: candidates.slice(0, 4) });
  } else {
    await go(`${BASE}/findings/${SITE}/${usable.id}/evidence`, "document.querySelector('[data-finding-evidence], [data-legacy-evidence], [data-finding-read]')");
    const l = await js(`({ url: location.pathname + location.search, legacy: document.querySelector('[data-legacy-evidence]')?.dataset.legacyEvidence ?? null,
      durable: document.querySelector('[data-finding-evidence]')?.dataset.findingEvidence ?? null,
      links: [...document.querySelectorAll('[data-legacy-evidence-link]')].map(a => a.getAttribute('href')) })`);
    claim(`${label} evidence legacy tab: assessment-keyed tab opens the durable Evidence view or names the state`,
      (l.durable !== null && /\/sites\/KOBO-001\/findings\/[^/]+\/evidence/.test(l.url)) || ["none", "several"].includes(l.legacy ?? ""),
      { assessment: usable.id, ...l });
    await shot(`app-evidence-legacy-tab-${label}`);
  }
}

async function closedSuite(label) {
  const r1 = F04.revisions[0].revision_id;
  await go(evidenceUrl(F04.finding_id), EV_READY);
  const u = await js(EV_STATE);
  const ua = await api(F04.finding_id);
  claim(`${label} evidence closed: unpinned read refused as closed (API 409)`, u.read === "closed" && ua.status === 409,
    { read: u.read, apiStatus: ua.status, code: ua.body?.detail?.code ?? ua.body?.code ?? null });
  await go(evidenceUrl(F04.finding_id, `?revision_id=${r1}`), EV_READY);
  const p = await js(EV_STATE);
  const pa = await api(F04.finding_id, `?revision_id=${r1}`);
  claim(`${label} evidence closed: pinned version leads with Record only, no Dispatch link`,
    p.auditOnly && p.firstLead === "evidenceAuditOnly" && p.dispatchLinks === 0 && p.total === pa.body?.counts?.cited_total
      && pa.body?.currentness?.state === "SOURCE_CLOSED",
    { auditOnly: p.auditOnly, firstLead: p.firstLead, dispatchLinks: p.dispatchLinks, appTotal: p.total, apiTotal: pa.body?.counts?.cited_total,
      currentness: pa.body?.currentness });
  await shot(`app-evidence-closed-${label}`);
}

async function brokenSuite(label) {
  const id = process.env.ASSETOPS_S4_BROKEN_FINDING;
  if (!id) throw new Error("ASSETOPS_S4_BROKEN_FINDING is required for the broken suite");
  await go(evidenceUrl(id), EV_READY);
  const a = await api(id, "?limit=50");
  const s = await js(EV_STATE);
  const apiBroken = (a.body?.lineage?.broken_records ?? []).map((r) => r.evidence_id);
  claim(`${label} evidence broken: lineage BROKEN stated, broken records named as in the API`,
    s.lineageBroken && s.lineage === "BROKEN" && JSON.stringify(s.brokenRecords) === JSON.stringify(apiBroken) && s.total === a.body?.counts?.cited_total,
    { lineage: s.lineage, brokenRecords: s.brokenRecords, apiBroken, total: s.total, digest: a.body?.lineage?.cited_set_digest?.status });
  if (apiBroken[0]) {
    await go(evidenceUrl(id, `?revision_id=${a.body.selection.revision_id}&record=${apiBroken[0]}`), "document.querySelector('[data-evidence-record], [data-evidence-record-absent]')");
    const r = await js(EV_STATE);
    claim(`${label} evidence broken: selected broken record names its link`, r.recordBreaks.includes("ENVELOPE_DIGEST"),
      { record: r.record, breaks: r.recordBreaks });
  }
  const o = await evidenceOverflow();
  claim(`${label} evidence broken: no sideways overflow`, noOverflow(o), o);
  await shot(`app-evidence-broken-${label}`);
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

  for (const [label, width, height] of WIDTHS) {
    viewport = [width, height];
    await size(width, height);
    if (SUITE === "all" || SUITE === "evidence") await evidenceSuite(label);
    if (SUITE === "closed") await closedSuite(label);
    if (SUITE === "broken") await brokenSuite(label);
    if (SUITE !== "all" && SUITE !== "finding") continue;
    await go(`${BASE}/mockups/v69/index.html#/finding`, "document.body && document.body.innerText.includes('Where to look next')");
    const mock = await js(`({ panels: ${JSON.stringify(PANELS)}.filter(p => document.body.innerText.includes(p)) })`);
    claim(`${label}: mock #/finding renders its four panels`, mock.panels.length === 4, mock);
    await shot(`mock-finding-${label}`);

    await go(finding(F01), READY);
    const s = await js(STATE);
    claim(`${label} F01: panels, cards and records render, up to date`,
      PANELS.every((p) => s.headings.includes(p)) && s.cards === 5 && s.records > 0 && s.lifecycle === "SUPPORTED" && s.currentness === "Up to date", s);
    claim(`${label} F01: Dispatch drill-down names the day and the assessed period`,
      s.dispatchDays.length === 1 && /day=2026-10-06&revision=/.test(s.dispatchDays[0]), s.dispatchDays);
    let o = await overflow();
    claim(`${label} F01: no sideways page scroll`, o.scrollWidth <= o.clientWidth && o.wide.length === 0, o);
    await shot(`app-finding-open-${label}`);

    await js(`document.querySelector('[data-portion="CANDIDATE_AVOIDABLE"]').focus()`);
    await enter();
    const keyed = await waitFor(`document.querySelector('[data-finding-portion-detail]')`);
    const before = await js(STATE);
    claim(`${label} F01: keyboard Enter selects a block and shows its Dispatch link`,
      keyed && before.blocks > 1 && before.pressed !== null && /portion=/.test(before.url), before);
    await send("Page.reload");
    await waitFor(`document.querySelector('[data-finding-portion-detail]')`);
    await sleep(300);
    const after = await js(STATE);
    claim(`${label} F01: reload keeps the Finding, version and selected block`,
      after.url === before.url && after.revision === before.revision && after.pressed === before.pressed, after);

    const r1 = F04.revisions[0].revision_id;
    await go(finding(F04, `?revision_id=${r1}`), READY);
    const pinned = await js(STATE);
    claim(`${label} F04: exact version 1 opens, labelled as an earlier version`,
      pinned.revision === r1 && /^Earlier version 1 of /.test(pinned.lead ?? "") && pinned.currentness === "Earlier version", pinned);
    await send("Page.reload");
    await waitFor(READY);
    await sleep(300);
    const pinnedAgain = await js(STATE);
    claim(`${label} F04: reload keeps the exact earlier version`, pinnedAgain.revision === r1 && pinnedAgain.url === pinned.url, pinnedAgain);
    await shot(`app-finding-earlier-version-${label}`);
    await go(finding(F04), READY);
    const latest = await js(STATE);
    claim(`${label} F04: the same Finding's latest version differs from version 1`,
      latest.revision !== r1 && latest.revision === F04.revisions.at(-1).revision_id, latest);

    const r2 = F05.revisions[1].revision_id;
    await go(finding(F05, `?revision_id=${r2}`), READY);
    const unconfirmed = await js(STATE);
    claim(`${label} F05: version 2 reads Not confirmed`, unconfirmed.lifecycle === "UNCONFIRMED" && unconfirmed.revision === r2, unconfirmed);
    await shot(`app-finding-unconfirmed-${label}`);
    await go(finding(F05), READY);
    const closed = await js(STATE);
    claim(`${label} F05: latest reads No longer supported, not a repair or a saving`,
      closed.lifecycle === "NO_LONGER_SUPPORTED" && /not mean the generator was repaired/.test(closed.sentence ?? ""), closed);
    await shot(`app-finding-closed-${label}`);

    await go(finding(F02), READY);
    const stale = await js(STATE);
    claim(`${label} F02: cross-midnight Finding with a pending day reads Out of date and stays visible`,
      stale.currentness === "Out of date" && stale.cards === 5 && stale.dispatchDays.length === 2, stale);
    await shot(`app-finding-stale-${label}`);

    await go(finding(F03), READY);
    const rec = await js(STATE);
    claim(`${label} F03: recurrence links the earlier Finding without saying it is still open`,
      /does not say the earlier Finding is still open/.test(rec.recurrence ?? ""), rec.recurrence);
    await go(finding(F06M), READY);
    const merged = await js(STATE);
    claim(`${label} F06: a Finding joined into another leads with that`, merged.lead === "Joined into an earlier Finding", merged.lead);

    await go(finding(F01, "?view=analysis"), "document.querySelector('[data-finding-technical]')");
    const tech = await js(`({ ids: document.querySelectorAll('[data-tech-evidence-id]').length, versions: document.querySelectorAll('[data-tech-version]').length })`);
    o = await overflow();
    claim(`${label} Analysis: full record and version identifiers, no sideways page scroll`,
      tech.ids > 0 && tech.versions > 0 && o.scrollWidth <= o.clientWidth && o.wide.length === 0, { ...tech, ...o });
    await shot(`app-finding-analysis-${label}`);

    for (const [day, expect, link] of [["2026-10-06", "FINDINGS_RECORDED", true], ["2026-10-19", "NOT_DETERMINABLE", false], ["2026-10-07", "NOT_ASSESSED", false]]) {
      await go(`${BASE}/sites/${SITE}/performance/dispatch?day=${day}`, "document.querySelector('[data-day-findings]')");
      const d = await js(`({ state: document.querySelector('[data-day-findings]')?.dataset.dayFindings,
        links: [...document.querySelectorAll('[data-dispatch-finding]')].map(a => a.getAttribute('href')) })`);
      claim(`${label} Dispatch ${day}: ${expect}${link ? " with a Finding link" : ", no Finding link"}`,
        d.state === expect && (link ? d.links.length > 0 : d.links.length === 0), d);
      if (link) await shot(`app-dispatch-finding-link-${label}`);
    }
  }
  const failed = results.filter((r) => !r.ok);
  console.log(`\n${results.length - failed.length}/${results.length} claims passed; screenshots in ${OUT}`);
  return failed.length === 0 ? 0 : 1;
}

let code = 1;
try {
  code = await main();
} catch (error) {
  console.error(`ERROR ${error.message}`);
} finally {
  chrome.kill();
  await sleep(500);
  try {
    rmSync(profile, { recursive: true, force: true });
  } catch {
    /* Chrome may still hold the profile */
  }
}
process.exit(code);
