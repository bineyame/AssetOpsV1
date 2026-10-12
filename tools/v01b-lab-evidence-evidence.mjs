/**
 * V-01b: app-vs-mock evidence for Site Evidence (`evidence:1-3`, `evidence-analysis:1-2`) and the Simulator
 * Lab run's Gateway & Ingestion overview (`lab:1-4`), with layout measurements at 1440 and 390, missing states
 * and honest empty states, from the installed Chrome over the DevTools Protocol (same approach as
 * tools/v01a-foundation-evidence.mjs; no dependency).
 *
 * Run against the V-01b walkthrough servers (tools/v01b_lab_evidence_walkthrough.py; populated KOBO-001 copy
 * with a gateway and one released registered run, plus an empty store with no Site):
 *   node tools/v01b-lab-evidence-evidence.mjs <base> <screenshot-dir> <empty-base>
 * defaults http://localhost:5362, %TEMP%/v01b-lab-evidence-evidence, http://localhost:5363.
 * Env: ASSETOPS_CDP_PORT (default 9362); V01B_RUN (released run id; otherwise the first run in
 * `GET <base>/api/simulator-lab/runs`, oldest first, whose Commit read is RELEASED_TO_GATEWAY with a registered
 * release). The not-committed state uses the newest stored READY draft whose Commit read is NOT_COMMITTED (the
 * layout tool's run-setup creates these); only if none exists is it shown via an intercepted `*commit*` response.
 *
 * Every claim is measured and printed; the run exits non-zero if any fails. Set-based claims report their size,
 * so a claim over an empty set is visible.
 *
 * Intercepted shapes (DevTools `Fetch`): Evidence "gateway contact unavailable" answers `*gateway-health*` with a
 * 503. It proves what the UI renders for that response shape; it is not a stored state.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const BASE = process.argv[2] ?? "http://localhost:5362";
const OUT = process.argv[3] ?? join(tmpdir(), "v01b-lab-evidence-evidence");
const EMPTY = process.argv[4] ?? "http://localhost:5363";
const SITE = "KOBO-001";
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9362);
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  ["desktop", 1440, 1000],
  ["narrow", 390, 900],
];
mkdirSync(OUT, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "assetops-v01b-cdp-"));
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
const listeners = new Map();
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
  // The app shell scrolls inside its own frame, so grow the viewport to the tallest scroller for the capture.
  const tall = await js(`Math.max(document.documentElement.scrollHeight,
    ...[...document.querySelectorAll('*')].filter(e => e.scrollHeight > e.clientHeight + 1 && getComputedStyle(e).overflowY !== 'visible')
      .map(e => e.scrollHeight + e.getBoundingClientRect().top))`);
  const h = Math.min(Math.ceil(tall), 9000);
  await send("Emulation.setDeviceMetricsOverride", { width: viewport[0], height: h, deviceScaleFactor: 1, mobile: viewport[0] < 600 });
  await sleep(300);
  const r = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(join(OUT, `${name}.png`), Buffer.from(r.data, "base64"));
  await size(viewport[0], viewport[1]);
}
/** The first screen only (no growth), for pages taller than a readable full capture. */
async function topShot(name) {
  const r = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(join(OUT, `${name}.png`), Buffer.from(r.data, "base64"));
}
// Elements that end past the viewport, excluding content inside a region that owns its own inline scroll.
const overflow = () =>
  js(`(() => { const d = document.documentElement;
      const scroller = (e) => { for (let p = e.parentElement; p; p = p.parentElement) { const o = getComputedStyle(p).overflowX; if (o === 'auto' || o === 'scroll') return true; } return false; };
      return { scrollWidth: d.scrollWidth, clientWidth: d.clientWidth,
      wide: [...document.querySelectorAll('body *')].filter(e => e.getBoundingClientRect().right > d.clientWidth + 1 && e.checkVisibility()
      && !scroller(e) && ![...e.children].some(c => c.getBoundingClientRect().right > d.clientWidth + 1))
      .map(e => (e.getAttribute('class') || e.tagName) + ':' + Math.round(e.getBoundingClientRect().right)).slice(0, 6) }; })()`);
async function layout(name) {
  const o = await overflow();
  claim(`${name}: no horizontal page scroll`, o.scrollWidth <= o.clientWidth && o.wide.length === 0, o);
}
const loaded = (text) =>
  `!document.querySelector('[aria-busy="true"]') && document.body.innerText.includes(${JSON.stringify(text)})`;
const TITLES = `[...document.querySelectorAll('main .panel__heading')].map(h => h.textContent.trim())`;
const H2 = `[...document.querySelectorAll('main h2')].map(h => h.textContent.trim())`;
const panelOf = (heading) =>
  `[...document.querySelectorAll('main section.panel')].find(s => s.querySelector('.panel__heading')?.textContent.trim() === ${JSON.stringify(heading)})`;
const box = (sel) => `(() => { const e = ${sel}; if (!e) return null; const r = e.getBoundingClientRect();
  return { left: Math.round(r.left), right: Math.round(r.right), top: Math.round(r.top), bottom: Math.round(r.bottom),
    width: Math.round(r.width), vw: document.documentElement.clientWidth }; })()`;
const within = (b) => b !== null && b.width > 0 && b.left >= 0 && b.right <= b.vw + 1;
/** Two boxes side by side (desktop) or stacked within the viewport (narrow). */
function arranged(label, a, b) {
  return label === "desktop"
    ? a !== null && b !== null && a.right <= b.left + 1 && Math.abs(a.top - b.top) < 4
    : within(a) && within(b) && b.top >= a.bottom - 1;
}
const ADVANCED = `[...document.querySelectorAll('main details')].filter(d => d.querySelector(':scope > summary')?.textContent.trim().startsWith('Advanced details —'))
  .map(d => ({ name: d.dataset.disclosure ?? null, open: d.open }))`;
async function openAllAdvanced() {
  await js(`[...document.querySelectorAll('main details')].filter(d => !d.open && d.querySelector(':scope > summary')?.textContent.trim().startsWith('Advanced details —'))
    .forEach(d => d.querySelector(':scope > summary').click())`);
  await sleep(800);
}
const text = (sel) => `(document.querySelector(${JSON.stringify(sel)})?.innerText.replace(/\\s+/g, ' ').trim() ?? null)`;

// --- intercepted responses (see header) ------------------------------------------------------
let intercept = null; // { code, body } or null to pass through
listeners.set("Fetch.requestPaused", (p) => {
  const v = intercept;
  if (v === null) {
    void send("Fetch.continueRequest", { requestId: p.requestId });
    return;
  }
  void send("Fetch.fulfillRequest", {
    requestId: p.requestId,
    responseCode: v.code,
    responseHeaders: [{ name: "Content-Type", value: "application/json" }],
    body: Buffer.from(JSON.stringify(v.body)).toString("base64"),
  });
});
async function intercepted(pattern, variant, body) {
  intercept = variant;
  await send("Fetch.enable", { patterns: [{ urlPattern: pattern }] });
  try {
    return await body();
  } finally {
    intercept = null;
    await send("Fetch.disable");
  }
}

// --- copy (exact strings from the product) ---------------------------------------------------
const MISSING_E1 =
  "Not available yet: capability-by-capability conclusions (what can be said, what is missing and the next step for each). They need a reviewed capability assessment over accepted Evidence, which does not exist yet.";
const MISSING_E2 =
  "Not available yet: a status at the end of the period, a quality grade and which conclusions each source affects. No reviewed rule sets these.";
const MISSING_E3 = "Not available yet: ranking the next evidence needs a reviewed rule linking missing readings to conclusions.";
const MISSING_EA2 =
  "Not available yet: the rule that turns accepted readings into a positive capability conclusion and sets its limit (a later capability assessment).";
const E_TITLES = ["What we can conclude now", "Data sources · data quality, not equipment condition", "Most useful next evidence"];
const EA_TITLES = ["Accepted records behind the conclusions", "How each limit is set"];
const LAB_TITLES = ["Selected canonical envelope", "Truth versus observed", "Release and ingestion", "What never crosses"];
const NOTHING_RECEIVED = "Nothing from this run has been received centrally.";
const STAGE_LABEL = "This is the gateway's local Stage statement. Central receipt is shown under Release and ingestion.";
const GATEWAY_UNAVAILABLE = "The gateway contact record could not be read, so whether the gateway is in touch is not known.";
const NO_SITE =
  "No site with that site ID is configured, so there is no evidence to read. This is a statement that the site does not exist, not a site with no evidence.";
const NO_RUNS = "No run has been set up on this installation.";

const POPULATED = "from=2026-10-02T00:00:00Z&to=2026-10-03T00:00:00Z";
const EMPTY_WINDOW = "from=2026-09-01T00:00:00Z&to=2026-09-02T00:00:00Z";
const evidenceUrl = (base, query, analysis = false) =>
  `${base}/sites/${SITE}/evidence${query ? `?${query}${analysis ? "&view=analysis" : ""}` : analysis ? "?view=analysis" : ""}`;
const MOCK = (id) => `${BASE}/mockups/v69/index.html#/${id}`;
const missingTexts = `[...document.querySelectorAll('main')].map(m => m.innerText)[0] ?? ''`;

async function api(path) {
  const r = await fetch(`${BASE}${path}`);
  return r.ok ? r.json() : null;
}
async function discoverRuns() {
  const list = (await api("/api/simulator-lab/runs"))?.runs ?? [];
  const oldest = [...list].sort((a, b) => a.created_at.localeCompare(b.created_at));
  let released = null;
  if (process.env.V01B_RUN) released = list.find((r) => r.run_id === process.env.V01B_RUN) ?? { run_id: process.env.V01B_RUN, interval: null };
  for (const r of oldest) {
    if (released !== null) break;
    const c = await api(`/api/simulator-lab/runs/${r.run_id}/commit`);
    if (c?.commit === "RELEASED_TO_GATEWAY" && c.registered_release) released = r;
  }
  let draft = null;
  for (const r of [...oldest].reverse()) {
    if (r.execution_status !== "READY" || r.run_id === released?.run_id) continue;
    const c = await api(`/api/simulator-lab/runs/${r.run_id}/commit`);
    if (c?.commit === "NOT_COMMITTED") {
      draft = r;
      break;
    }
  }
  return { released, draft, count: list.length };
}

async function evidenceOverview(label) {
  await go(evidenceUrl(BASE, POPULATED), loaded("Most useful next evidence"));
  const s = await js(`({ bar: ${text("[data-evidence-statusbar]")}, titles: ${TITLES}, body: ${missingTexts},
    earlier: (() => { const d = document.querySelector('details[data-disclosure="evidence-earlier-store"]'); return d ? d.open : null; })() })`);
  claim(`${label}: Evidence status bar states window facts and no "Evidence limited"`,
    /readings? accepted/.test(s.bar ?? "") && /of \d+ sources with accepted readings/.test(s.bar ?? "") && !/Evidence limited/.test(s.body), { bar: s.bar });
  const order = E_TITLES.map((t) => s.titles.indexOf(t));
  claim(`${label}: Evidence overview panel titles in mock order`, order.every((i, k) => i >= 0 && (k === 0 || i > order[k - 1])), { titles: s.titles });
  const src = await js(box(panelOf(E_TITLES[1])));
  const next = await js(box(panelOf(E_TITLES[2])));
  claim(`${label}: sources and next-evidence panels are ${label === "desktop" ? "side by side (sources left)" : "stacked within the viewport"}`,
    arranged(label, src, next), { src, next });
  for (const [k, m] of [["evidence:1", MISSING_E1], ["evidence:2", MISSING_E2], ["evidence:3", MISSING_E3]]) {
    claim(`${label}: ${k} "Not available yet" statement is visible`, s.body.includes(m));
  }
  claim(`${label}: "Advanced details — earlier store" is closed by default`, s.earlier === false, { open: s.earlier });
  await layout(`${label}: Evidence overview (populated)`);
  const button = await js(`(() => { const b = [...document.querySelectorAll('main button')].find(b => b.textContent.trim() === 'Show this period');
    if (!b) return null; const c = getComputedStyle(b); return { bg: c.backgroundColor, color: c.color }; })()`);
  const accent = await js(`getComputedStyle(document.documentElement).getPropertyValue('--accent').trim()`);
  claim(`${label}: "Show this period" is styled as the primary action`, button !== null && button.bg !== "rgba(0, 0, 0, 0)" && button.color === "rgb(255, 255, 255)",
    { button, accent });
  await shot(`app-evidence-populated-${label}`);
}

async function evidenceAnalysis(label) {
  await go(evidenceUrl(BASE, POPULATED, true), loaded("How each limit is set") + ` && document.querySelector('[data-evidence-record]')`);
  const s = await js(`({ titles: ${TITLES}, rows: document.querySelectorAll('[data-evidence-record]').length, adv: ${ADVANCED}, body: ${missingTexts} })`);
  claim(`${label}: Evidence analysis shows the two mock panel titles in order`,
    s.titles.indexOf(EA_TITLES[0]) >= 0 && s.titles.indexOf(EA_TITLES[1]) > s.titles.indexOf(EA_TITLES[0]), { titles: s.titles });
  claim(`${label}: accepted records table is non-empty`, s.rows >= 1, { rows: s.rows });
  claim(`${label}: every "Advanced details — …" disclosure is closed by default`, s.adv.length > 0 && s.adv.every((d) => !d.open),
    { count: s.adv.length, open: s.adv.filter((d) => d.open).map((d) => d.name) });
  claim(`${label}: evidence-analysis:2 "Not available yet" statement is visible`, s.body.includes(MISSING_EA2));
  await layout(`${label}: Evidence analysis (populated)`);
  await shot(`app-evidence-analysis-populated-${label}`);

  // Follow one visible accepted value to its SourceEnvelope through the read API.
  const row = await js(`(() => { const rows = [...document.querySelectorAll('[data-evidence-record]')];
    const r = rows.find(r => !r.querySelector('.evidence-records__quality')) ?? rows[0];
    return { id: r.dataset.evidenceRecord, value: r.children[1].textContent.trim(), good: !r.querySelector('.evidence-records__quality') }; })()`);
  await js(`[...document.querySelectorAll('[data-evidence-record="${row.id}"] button')].find(b => b.textContent.trim() === 'Open record').click()`);
  const opened = await waitFor(`document.body.innerText.includes('Exact message as received') && document.querySelector('[data-record-message]')`, 20000);
  await sleep(400);
  const shown = await js(`(document.querySelector('[data-record-message]')?.textContent ?? '')`);
  const apiRecord = await js(`fetch('/api/sites/${SITE}/evidence/records/' + encodeURIComponent(${JSON.stringify(row.id)})).then(r => r.ok ? r.json() : null)`);
  claim(`${label}: "Open record" shows "Exact message as received" with the SourceEnvelope text`, opened && shown.trim().length > 0, { id: row.id });
  const apiValue = apiRecord === null ? null : apiRecord.normalized.value === null ? "no value" : `${apiRecord.normalized.value}${apiRecord.normalized.unit ? ` ${apiRecord.normalized.unit}` : ""}`;
  let payloadValue = null;
  try {
    payloadValue = JSON.parse(apiRecord?.envelope?.text ?? "null")?.payload?.value ?? null;
  } catch {
    payloadValue = "unparseable";
  }
  claim(`${label}: the displayed accepted value and message equal the read API record and its SourceEnvelope`,
    apiRecord !== null && row.value === apiValue && shown.trim() === apiRecord.envelope.text.trim()
      && (apiRecord.original.value === null ? payloadValue === null : String(payloadValue) === String(apiRecord.original.value)
        || Number(payloadValue) === Number(apiRecord.original.value)),
    { id: row.id, good: row.good, displayed: row.value, api: apiValue, envelopePayloadValue: payloadValue, original: apiRecord?.original ?? null });
  await layout(`${label}: Evidence record detail`);
  await shot(`app-evidence-record-detail-${label}`);

  await go(evidenceUrl(BASE, POPULATED, true), loaded("How each limit is set") + ` && document.querySelector('[data-evidence-record]')`);
  await openAllAdvanced();
  const adv = await js(ADVANCED);
  claim(`${label}: every analysis "Advanced details — …" disclosure opens`, adv.length > 0 && adv.every((d) => d.open), { count: adv.length });
  await layout(`${label}: Evidence analysis with advanced details open`);
  await shot(`app-evidence-analysis-advanced-open-${label}`);
}

async function evidenceEmptyAndMissing(label) {
  await go(evidenceUrl(BASE, EMPTY_WINDOW), loaded("Most useful next evidence"));
  const o = await js(`({ bar: ${text("[data-evidence-statusbar]")}, headline: ${text("[data-evidence-headline]")}, body: ${missingTexts},
    rows: document.querySelectorAll('main [data-evidence-source]').length,
    accepted: [...document.querySelectorAll('main [data-evidence-source]')].map(r => r.children[1]?.textContent.trim()) })`);
  claim(`${label}: empty window overview states zero accepted readings`, /(^|\s)0 readings accepted/.test(o.bar ?? "") && /\b0 of \d+ sources/.test(o.bar ?? ""), { bar: o.bar });
  claim(`${label}: empty window overview headline says nothing was received (no fabricated result)`,
    o.headline !== null && /no|nothing/i.test(o.headline) && !/Evidence limited/.test(o.body), { headline: o.headline });
  claim(`${label}: empty window keeps the three "Not available yet" statements`,
    [MISSING_E1, MISSING_E2, MISSING_E3].every((m) => o.body.includes(m)));
  claim(`${label}: empty window shows no source with an accepted reading`,
    o.rows > 0 && o.accepted.every((a) => /^0$|No accepted reading/.test(a ?? "")), { rows: o.rows, cells: [...new Set(o.accepted)] });
  await layout(`${label}: Evidence overview (empty window)`);
  await shot(`app-evidence-empty-${label}`);

  await go(evidenceUrl(BASE, EMPTY_WINDOW, true), loaded("How each limit is set") + ` && (document.querySelector('[data-evidence-records-empty]') || document.querySelector('[data-evidence-record]'))`);
  const a = await js(`({ rows: document.querySelectorAll('[data-evidence-record]').length, empty: ${text("[data-evidence-records-empty]")}, body: ${missingTexts} })`);
  claim(`${label}: empty window analysis has no record rows and says so`, a.rows === 0 && a.empty === "No accepted reading in this period.", a.rows === 0 ? { rows: 0, empty: a.empty } : { rows: a.rows });
  claim(`${label}: empty window analysis keeps the evidence-analysis:2 statement`, a.body.includes(MISSING_EA2));
  await layout(`${label}: Evidence analysis (empty window)`);
  await shot(`app-evidence-analysis-empty-${label}`);

  await go(`${EMPTY}/sites/${SITE}/evidence`, `document.body.innerText.includes('No such site') || document.body.innerText.includes('Evidence not found') || document.body.innerText.includes('could not')`);
  const n = await js(`({ titles: ${TITLES}, body: ${missingTexts} })`);
  claim(`${label}: Evidence for a Site the store does not hold says it was not found`,
    n.titles.includes("No such site") && n.body.includes(NO_SITE) && !/readings accepted/.test(n.body), { titles: n.titles });
  await layout(`${label}: Evidence missing Site`);
  await shot(`app-evidence-no-site-${label}`);

  await intercepted("*gateway-health*", { code: 503, body: { detail: "unavailable" } }, async () => {
    await go(evidenceUrl(BASE, POPULATED), loaded("Most useful next evidence") + ` && document.querySelector('[data-gateway-contact]')`);
    const g = await js(`({ state: document.querySelector('[data-gateway-contact]')?.dataset.gatewayContact ?? null, text: ${text("[data-gateway-contact]")} })`);
    claim(`${label}: intercepted gateway-health 503 (response shape, not a stored state) renders the unavailable copy`,
      g.state === "unavailable" && (g.text ?? "").trim() === GATEWAY_UNAVAILABLE, g);
    await shot(`app-evidence-gateway-unavailable-${label}`);
  });
}

async function labRun(label, released) {
  const runUrl = `${BASE}/simulator-lab/runs/${released.run_id}`;
  await go(runUrl, `document.querySelector('[data-run-ingestion]') && ${loaded("What never crosses")} && document.querySelector('[data-ingestion-envelope]')`);
  await sleep(800);
  const s = await js(`({ h2: ${H2}, titles: ${TITLES}, bar: ${text("[data-ingestion-status]")},
    href: document.querySelector('[data-ingestion-evidence-link]')?.getAttribute('href') ?? null,
    flow: [...document.querySelectorAll('[data-flow-box]')].map(b => b.dataset.flowBox),
    pre: !!document.querySelector('pre[data-ingestion-envelope]'),
    missing: Object.fromEntries([...document.querySelectorAll('[data-ingestion-missing]')].map(m => [m.dataset.ingestionMissing, m.textContent.replace(/\\s+/g, ' ').trim()])) })`);
  const gi = s.h2.indexOf("Gateway & Ingestion");
  const ex = s.h2.indexOf("Execution and recorded history");
  claim(`${label}: Lab run "Gateway & Ingestion" h2 is above "Execution and recorded history"`, gi >= 0 && ex > gi, { h2: s.h2.slice(0, 4) });
  claim(`${label}: Lab status bar shows the central receipt fact`, /of \d+ batches have a central receipt/.test(s.bar ?? ""), { bar: s.bar });
  let linkOk = false;
  let linkDetail = { href: s.href, interval: released.interval };
  if (s.href !== null && released.interval) {
    const q = new URL(s.href, BASE).searchParams;
    linkOk = q.get("from") === released.interval.start_time && q.get("to") === released.interval.end_time && s.href.startsWith(`/sites/${released.site_id}/evidence`);
  }
  claim(`${label}: "Open Site Evidence →" links to the run interval on Site Evidence`, linkOk, linkDetail);
  claim(`${label}: four flow boxes`, s.flow.length === 4, { flow: s.flow });
  const order = LAB_TITLES.map((t) => s.titles.indexOf(t));
  claim(`${label}: four Lab panel titles in mock order`, order.every((i, k) => i >= 0 && (k === 0 || i > order[k - 1])), { titles: s.titles.slice(0, 6) });
  const p = await Promise.all(LAB_TITLES.map((t) => js(box(panelOf(t)))));
  claim(`${label}: Lab panel rows are ${label === "desktop" ? "two-column" : "stacked within the viewport"}`,
    arranged(label, p[0], p[1]) && arranged(label, p[2], p[3]), { boxes: p.map((b) => b && [b.left, b.top, b.right]) });
  claim(`${label}: the selected canonical envelope is a <pre>`, s.pre);
  claim(`${label}: lab:2 and lab:4 "Not available yet" statements are visible`,
    (s.missing["product-consequence"] ?? "").startsWith("Not available yet: the product consequence of each report")
      && (s.missing["dispatch-link"] ?? "").startsWith("Not available yet: a link from this run's accepted records to the Dispatch analysis"),
    { missing: Object.keys(s.missing) });
  await layout(`${label}: Lab run (released)`);
  await shot(`app-lab-run-${label}`);
  await topShot(`app-lab-run-top-${label}`);

  await js(`document.querySelector('details[data-disclosure="stage"] > summary')?.click()`);
  const staged = await waitFor(`document.querySelector('details[data-disclosure="stage"]')?.innerText.includes(${JSON.stringify(STAGE_LABEL)})`, 20000);
  claim(`${label}: the Stage disclosure, opened, carries the Q1 label`, staged);
  await openAllAdvanced();
  await sleep(1500);
  const adv = await js(ADVANCED);
  claim(`${label}: every Lab "Advanced details — …" disclosure opens`, adv.length > 0 && adv.every((d) => d.open), { count: adv.length });
  await layout(`${label}: Lab run with advanced details open`);
  await shot(`app-lab-run-advanced-open-${label}`);
}

async function labStates(label, draft) {
  await go(`${EMPTY}/simulator-lab/runs`, `document.body.innerText.includes('No draft runs yet') || document.body.innerText.includes('could not')`);
  const e = await js(missingTexts);
  claim(`${label}: Lab runs on the empty store say no run has been set up`, e.includes("No draft runs yet") && e.includes(NO_RUNS), { text: e.slice(0, 200) });
  await layout(`${label}: Lab runs (empty store)`);
  await shot(`app-lab-runs-empty-${label}`);

  const check = async (url, how) => {
    await go(url, `document.querySelector('[data-run-ingestion]') && document.querySelector('[data-ingestion-status]')?.innerText.includes(${JSON.stringify(NOTHING_RECEIVED)})`);
    const n = await js(`({ bar: ${text("[data-ingestion-status]")}, link: !!document.querySelector('[data-ingestion-evidence-link]'),
      flow: [...document.querySelectorAll('[data-flow-box]')].map(b => b.innerText.replace(/\\s+/g, ' ').trim()) })`);
    claim(`${label}: ${how} not-committed run says nothing was received centrally and has no Site Evidence link`,
      (n.bar ?? "").includes(NOTHING_RECEIVED) && /Not committed/.test(n.bar ?? "") && !n.link, { bar: n.bar });
    const accepted = n.flow.find((f) => f.includes("Accepted evidence")) ?? "";
    claim(`${label}: ${how} not-committed run's accepted-evidence flow box shows nothing accepted and no central receipt`,
      accepted.includes("Not committed: nothing released, nothing accepted centrally.")
        || (/\b0 accepted\b/.test(accepted) && /\b0 of \d+ batches have a central receipt/.test(accepted)), { box: accepted });
    await layout(`${label}: Lab run (not committed, ${how})`);
    await shot(`app-lab-run-not-committed-${label}`);
  };
  if (draft !== null) {
    await check(`${BASE}/simulator-lab/runs/${draft.run_id}`, `stored draft ${draft.run_id}`);
  } else {
    claim(`${label}: a stored READY draft exists for the not-committed state (else intercepted below)`, false, { draft: null });
  }
}

async function main() {
  ws = await connect();
  ws.addEventListener("message", (e) => {
    const msg = JSON.parse(e.data);
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id)(msg);
      pending.delete(msg.id);
    } else if (msg.method && listeners.has(msg.method)) {
      listeners.get(msg.method)(msg.params);
    }
  });
  await send("Page.enable");
  await send("Runtime.enable");

  const runs = await discoverRuns();
  claim("a released registered run was found", runs.released !== null, { run: runs.released?.run_id ?? null, runs: runs.count });
  console.log(`released run ${runs.released?.run_id ?? "none"}; not-committed draft ${runs.draft?.run_id ?? "none"}`);

  for (const [label, width, height] of WIDTHS) {
    await size(width, height);

    for (const [id, title] of [
      ["lab", "Selected canonical envelope"],
      ["evidence", "What we can conclude now"],
      ["evidence-analysis", "Accepted records behind the conclusions"],
    ]) {
      const ok = await go(MOCK(id), `document.body && document.body.innerText.includes(${JSON.stringify(title)})`);
      claim(`${label}: mock #/${id} renders "${title}"`, ok);
      await shot(`mock-${id}-${label}`);
    }

    await evidenceOverview(label);
    await evidenceAnalysis(label);
    await evidenceEmptyAndMissing(label);
    if (runs.released !== null) await labRun(label, runs.released);
    await labStates(label, runs.draft);
  }
}

main()
  .catch((error) => {
    claim("evidence run completed", false, String(error?.stack ?? error));
  })
  .finally(() => {
    const failed = results.filter((r) => !r.ok).length;
    console.log(`\n${results.length - failed}/${results.length} claims passed; screenshots in ${OUT}`);
    chrome.kill();
    try {
      rmSync(profile, { recursive: true, force: true });
    } catch {
      /* Chrome may still hold the profile */
    }
    process.exit(failed === 0 ? 0 : 1);
  });
