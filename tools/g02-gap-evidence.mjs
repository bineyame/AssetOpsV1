/**
 * G-02: browser evidence for the V-01a mock-gap pilot at 1440x1000 and 390x900, from the installed
 * Chrome over the DevTools Protocol (same no-dependency approach as tools/g01-firmware-evidence.mjs
 * and tools/v01a-foundation-evidence.mjs).
 *
 *   node tools/g02-gap-evidence.mjs <app-base-url> <empty-app-base-url> <out-dir>
 *
 * Run against private walkthrough servers (tools/v01a_foundation_walkthrough.py with private
 * --db/--empty-db/--work-name, API + Vite on private ports). For site KOBO-001 it checks, per route
 * and viewport, the rendered `data-gap-id@data-gap-placement` pairs of every catalogued missing state
 * (exact set, exact text, status `open`, no nesting, visible, not inside an svg), page-level
 * horizontal overflow (inner table/diagram scroll containers are measured and reported separately,
 * V-01a carry C1), and that no gap ID reaches visible text.
 *
 * Readiness gateway branches: STALE is the real stored read; CURRENT, UNKNOWN, 503, 404 and a held
 * (pending) response are in-browser substitutions of the single `*gateway-health*` request. They
 * prove only what the screen renders for those responses, not any gateway state.
 *
 * Non-vacuity: G02_ALTER=<placement> appends " [altered]" to that placement's expected text, so its
 * text claims must FAIL.
 *
 * Every claim is printed PASS/FAIL with its measured value; set claims print their size. The run
 * exits non-zero if any claim fails.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { widthGuard } from "./evidence-checks.mjs";

const BASE = process.argv[2] ?? "http://localhost:5398";
const EMPTY = process.argv[3] ?? "http://localhost:5399";
const OUT = process.argv[4] ?? join(tmpdir(), "g02-gap-evidence");
const SITE = "KOBO-001";
const PORT = 9399;
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  [1440, 1000],
  [390, 900],
];
const ALTER = process.env.G02_ALTER ?? null;

// [gapId, placement, exact text, count rule: 1 or "rows"]
const T = (gap, placement, text, count = 1) => ({
  gap,
  placement,
  text: placement === ALTER ? `${text} [altered]` : text,
  count,
});
const SITES = [
  T("G-sites-operating-view", "sites.inventory.operating-view", "Not available yetAssessment · top issue · evidence limit · last analysed", "rows"),
  T("G-sites-operating-view", "sites.inventory.analysis-note",
    "Assessment, top issue, evidence limit and last analysis are not available in this directory. Open a Site for its selected-window evidence and assessments."),
  // W1-F1: the counts moved into the v69 metric cards, setup into the In setup panel.
  T("G-sites-attention-counts", "sites.inventory.attention-counts",
    "Needs attention and Evidence limited counts are not available from this list: there is no common window or aggregation contract for them."),
  T("G-sites-setup-progress", "sites.inventory.setup-progress", "Setup progress not available: no read returns who set up a site, its next step or when it was registered."),
];
const FOUNDATION = [
  T("G-foundation-productive-use", "foundation.identity.productive-use", "Not declared"),
  T("G-foundation-financial-assumptions", "foundation.identity.financial-assumptions",
    "Financial assumptions not available here. Physical ratings here are not financial assumptions."),
  T("G-foundation-change-record", "foundation.controls.change-record", "No proposed-change record here"),
  T("G-foundation-constraint-evidence", "foundation.controls.constraint-evidence", "No linked constraint evidence"),
];
const READINESS = [
  T("G-readiness-commissioning", "readiness.commissioning.definition",
    "Confirmed means an independent commissioning or field record; none exists yet."),
  T("G-readiness-commissioning", "readiness.commissioning.confirmed", "Not recorded", "rows"),
  T("G-readiness-commissioning", "readiness.commissioning.needed", "Commissioning confirmation not recorded", "rows"),
  T("G-readiness-commissioning", "readiness.commissioning.declared", "No commissioning record type exists in this Foundation"),
  T("G-readiness-commissioning", "readiness.commissioning.next-step", "No commissioning record available"),
  T("G-readiness-gateway-uptime", "readiness.gateway.uptime",
    "Uptime trend not available yet: no reviewed source reports a gateway's uptime over time."),
  T("G-readiness-gateway-completeness", "readiness.gateway.completeness",
    "Expected-versus-delivered completeness not available yet: no reviewed source compares the reports a gateway should send with those received."),
  T("G-readiness-gateway-signal-strength", "readiness.gateway.signal-strength",
    "Signal strength not available yet: no reviewed source reports a gateway's signal strength."),
  T("G-readiness-gateway-firmware", "readiness.gateway.firmware",
    "Firmware not available yet: no reviewed source reports what firmware a gateway has installed."),
  T("G-readiness-source-contact", "readiness.sources.arrival", "whether data is arriving is not assessed here."),
];
const CONTACT = T("G-readiness-source-contact", "readiness.gateway.source-connection", "Device connection not established here.");
const REGISTRATION = T("G-readiness-source-contact", "readiness.gateway.source-connection-registration",
  "Device connection not established here.");
const SLD = [
  T("G-sld-protection-metering", "sld.diagram.protection-metering",
    "Protection and meter positions are not declared in this Foundation topology;"),
  T("G-sld-reporting-status", "sld.diagram.reporting-status", "monitoring links and reporting status are not assessed on this diagram."),
  T("G-sld-reporting-status", "sld.diagram.readings-status", "Readings are not assessed in this view."),
  // Q1 fix round: one placement per Site-only slot kind. SVG slots are <text> elements; counts follow the drawn nodes.
  T("G-sld-reporting-status", "sld.diagram.bus-slot", "Readings not assessed here", "bus"),
  T("G-sld-reporting-status", "sld.diagram.node-slot", "Readings not assessed here", "nodes-1"),
  T("G-sld-reporting-status", "sld.contents.readings-slot", "Readings not assessed here", "nodes"),
  T("G-sld-reporting-status", "sld.contents.caption", "both are empty in this build, for every component, and neither holds a reading."),
  T("G-sld-reporting-status", "sld.intro.readings-status",
    "Whether any reading has arrived is not assessed in this view, so every value slot on it is empty."),
];

mkdirSync(OUT, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "assetops-g02-cdp-"));
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
const info = (name, detail) => console.log(`INFO  ${name}  ${JSON.stringify(detail)}`);

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
  if (r.exceptionDetails) throw new Error(`page eval: ${JSON.stringify(r.exceptionDetails).slice(0, 400)}`);
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
const requireWidth = widthGuard({ send, claim });
async function size(width, height) {
  viewport = [width, height];
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 600 });
  await requireWidth(width, height, `resize to ${width}x${height}`, { record: false });
}
async function go(url, ready) {
  await send("Page.navigate", { url });
  const ok = await waitFor(ready);
  await sleep(400);
  await requireWidth(viewport[0], viewport[1], `loaded ${url}`);
  return ok;
}
const shotNames = new Set();
let shotClash = [];
async function shot(name) {
  if (shotNames.has(name)) shotClash.push(name);
  shotNames.add(name);
  // The app shell scrolls inside its own frame, so grow the viewport to the tallest scroller for the capture.
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

// --- gateway-health response variants -------------------------------------------------------
let gatewayVariant = null; // null: real response; "hold": leave pending; else {code, body}
const held = [];
listeners.set("Fetch.requestPaused", (p) => {
  const v = gatewayVariant;
  if (v === "hold") {
    held.push(p.requestId);
    return;
  }
  if (v === null) {
    void send("Fetch.continueRequest", { requestId: p.requestId }).catch(() => {});
    return;
  }
  void send("Fetch.fulfillRequest", {
    requestId: p.requestId,
    responseCode: v.code,
    responseHeaders: [{ name: "Content-Type", value: "application/json" }],
    body: Buffer.from(JSON.stringify(v.body)).toString("base64"),
  }).catch(() => {});
});
async function release() {
  gatewayVariant = null;
  while (held.length) await send("Fetch.continueRequest", { requestId: held.shift() }).catch(() => {});
}

// --- page measurement -----------------------------------------------------------------------
const PAIR = `(e) => e.getAttribute('data-gap-id') + '@' + e.getAttribute('data-gap-placement')`;
/** Structure of the tagged elements, before any disclosure is opened. */
const STRUCTURE = `(() => { const pair = ${PAIR}; const els = [...document.querySelectorAll('[data-gap-id]')];
  const d = document.documentElement;
  return {
    pairs: [...new Set(els.map(pair))].sort(),
    counts: els.reduce((a, e) => { const k = pair(e); a[k] = (a[k] || 0) + 1; return a; }, {}),
    nodeCount: document.querySelectorAll('[data-sld-node]').length,
    texts: els.map(e => ({ pair: pair(e), ln: e.localName, ns: e.namespaceURI, slot: e.getAttribute('data-sld-slot'), text: e.textContent, status: e.getAttribute('data-gap-status'),
      nested: !!e.querySelector('[data-gap-id]'), inSvg: !!e.closest('svg'),
      inClosedDetails: (() => { let p = e.parentElement; while (p) { if (p.tagName === 'DETAILS' && !p.open) return true; p = p.parentElement; } return false; })() })),
    siteRows: document.querySelectorAll('main tbody tr').length,
    readinessRows: document.querySelectorAll('[data-readiness-row]').length,
    innerWidth: window.innerWidth, scrollWidth: d.scrollWidth,
    containers: [...document.querySelectorAll('.data-table__scroll, .sld__scroll')].map(c => ({
      cls: c.className, label: c.querySelector('[data-readiness-row]') ? 'readiness-table' : (c.closest('section')?.querySelector('h2')?.textContent.trim() ?? null),
      clientWidth: c.clientWidth, scrollWidth: c.scrollWidth, innerScroll: c.scrollWidth > c.clientWidth + 1,
      right: Math.round(c.getBoundingClientRect().right) })),
  }; })()`;
/** Opens every closed <details> that holds a tagged element (outermost first); returns how many. */
const OPEN = `(() => { let n = 0; for (const e of document.querySelectorAll('[data-gap-id]')) {
  const chain = []; let p = e.parentElement; while (p) { if (p.tagName === 'DETAILS' && !p.open) chain.unshift(p); p = p.parentElement; }
  for (const dd of chain) { if (!dd.open) { dd.querySelector(':scope > summary').click(); n += 1; } } } return n; })()`;
/** Visibility of every tagged element (after opening); an element beyond the viewport inside an
 * inner scroll container is scrolled into view there and re-measured (C1). */
const VISIBILITY = `(() => { const pair = ${PAIR}; const out = [];
  const iw = window.innerWidth;
  for (const e of document.querySelectorAll('[data-gap-id]')) {
    const m = () => { const r = e.getBoundingClientRect(); return { left: Math.round(r.left), right: Math.round(r.right), width: Math.round(r.width), height: Math.round(r.height) }; };
    let b = m(); let viaInnerScroll = false;
    const sc = e.closest('.data-table__scroll, .sld__scroll');
    if ((b.right > iw + 1 || b.left < -1) && sc) { e.scrollIntoView({ block: 'nearest', inline: 'nearest' }); b = m(); viaInnerScroll = true; }
    const vis = e.checkVisibility({ visibilityProperty: true, opacityProperty: true });
    out.push({ pair: pair(e), vis, box: b, viaInnerScroll, ok: vis && b.width > 0 && b.height > 0 && b.left >= -1 && b.right <= iw + 1 });
    if (sc) sc.scrollLeft = 0;
  }
  const d = document.documentElement;
  return { els: out, innerWidth: iw, scrollWidth: d.scrollWidth,
    idInText: (document.body.innerText.match(/G-(sites|foundation|readiness|sld)-[a-z-]*/g) || []) }; })()`;

const key = (t) => `${t.gap}@${t.placement}`;
/** Runs claims (a)-(f) for the current page against `expected` (array of T). */
async function verify(label, expected) {
  const s = await js(STRUCTURE);
  const want = [...new Set(expected.map(key))].sort();
  claim(`${label}: (a) distinct gap pair set equals expected`, JSON.stringify(s.pairs) === JSON.stringify(want),
    { size: s.pairs.length, expectedSize: want.length, missing: want.filter((k) => !s.pairs.includes(k)), extra: s.pairs.filter((k) => !want.includes(k)) });
  const rowsFor = (t) => (t.gap.startsWith("G-sites") ? s.siteRows : s.readinessRows);
  const wantCount = (t) => (t.count === "rows" ? rowsFor(t) : t.count === "nodes" ? s.nodeCount : t.count === "nodes-1" ? s.nodeCount - 1 : t.count === "bus" ? 1 : 1);
  const countBad = expected
    .map((t) => ({ pair: key(t), want: wantCount(t), got: s.counts[key(t)] ?? 0 }))
    .filter((c) => c.want !== c.got || c.want === 0);
  claim(`${label}: (a) each pair appears the expected number of times (rows: site ${s.siteRows}, readiness ${s.readinessRows})`,
    countBad.length === 0, { size: Object.keys(s.counts).length, bad: countBad });
  const textOf = Object.fromEntries(expected.map((t) => [key(t), t.text]));
  const badText = s.texts.filter((x) => textOf[x.pair] !== undefined && x.text !== textOf[x.pair]).map((x) => ({ pair: x.pair, text: x.text, want: textOf[x.pair] }));
  claim(`${label}: (b) every tagged element's text is exact`, s.texts.length > 0 && badText.length === 0, { size: s.texts.length, bad: badText });
  const badStatus = s.texts.filter((x) => x.status !== "open" || x.nested);
  claim(`${label}: (b) every data-gap-status is "open" and no tagged element contains another`, s.texts.length > 0 && badStatus.length === 0,
    { size: s.texts.length, bad: badStatus });
  claim(`${label}: (d) no horizontal page scroll (default state)`, s.scrollWidth <= s.innerWidth, { scrollWidth: s.scrollWidth, innerWidth: s.innerWidth });
  for (const c of s.containers.filter((c) => c.innerScroll)) info(`${label}: inner scroll container (C1, not a page claim)`, c);
  const closed = s.texts.filter((x) => x.inClosedDetails).map((x) => x.pair);
  const opened = await js(OPEN);
  await sleep(350);
  const v = await js(VISIBILITY);
  const badVis = v.els.filter((x) => !x.ok);
  const inner = v.els.filter((x) => x.viaInnerScroll).map((x) => x.pair);
  claim(`${label}: (c) every tagged element visible inside the viewport width (opened ${opened} closed disclosure(s) for ${closed.length} element(s); ${inner.length} reached via inner scroll)`,
    v.els.length > 0 && badVis.length === 0, { size: v.els.length, closedBefore: closed, viaInnerScroll: inner, bad: badVis });
  claim(`${label}: (d) no horizontal page scroll (disclosures open)`, v.scrollWidth <= v.innerWidth, { scrollWidth: v.scrollWidth, innerWidth: v.innerWidth });
  claim(`${label}: (e) no gap ID in visible text`, v.idInText.length === 0, { size: v.idInText.length, found: v.idInText });
  if (expected.some((t) => t.gap.startsWith("G-sld"))) {
    const SVG_NS = "http://www.w3.org/2000/svg";
    const inSvg = s.texts.filter((x) => x.inSvg);
    const badSvg = inSvg.filter((x) => !(["text", "tspan"].includes(x.ln) && x.ns === SVG_NS && x.slot === "unfilled")).map((x) => x.pair);
    const badHtml = s.texts.filter((x) => !x.inSvg && x.ns === SVG_NS).map((x) => x.pair);
    claim(`${label}: (f) SLD SVG-tagged elements are SVG text/tspan in the SVG namespace (never HTML inside svg); the non-SVG ones are HTML`,
      inSvg.length === s.nodeCount && badSvg.length === 0 && badHtml.length === 0, { size: inSvg.length, nodeCount: s.nodeCount, badSvg, badHtml });
  }
  return { pairs: s.pairs, containers: s.containers };
}

const loaded = (text) => `!document.querySelector('[aria-busy="true"]') && document.body.innerText.includes(${JSON.stringify(text)})`;
const route = (path, query = "") => `${BASE}/sites/${SITE}/${path}${query}`;
const PANEL = `[...document.querySelectorAll('main section')].find(s => s.querySelector('h2')?.textContent.trim() === 'Gateway status')`;
const LOADING_TEXT = "Loading the site's gateway contact.";
const GW_STATE = `(${PANEL})?.querySelector('[data-gateway-panel-state]')?.dataset.gatewayPanelState`;
const READY = {
  sites: `${loaded("Site inventory")} && document.querySelector('main tbody tr')`,
  foundation: `${loaded("Time-valid control configuration")} && document.body.innerText.includes('Identity & operating obligations')`,
  readiness: `!document.querySelector('[aria-busy="true"]') && document.querySelector('[data-readiness-row]') && ${GW_STATE} && ${GW_STATE} !== 'loading'`,
  // The pending branch has no data-gateway-panel-state; it renders the loading sentence instead.
  readinessLoading: `document.querySelector('[data-readiness-row]') && !(${GW_STATE}) && (${PANEL})?.innerText.includes(${JSON.stringify(LOADING_TEXT)})`,
  sld: `${loaded("configured single line diagram")}`,
};
const GW = `(() => { const p = ${PANEL}; return p ? { state: p.querySelector('[data-gateway-panel-state]')?.dataset.gatewayPanelState ?? null,
  status: p.querySelector('[data-gateway-status]')?.dataset.gatewayStatus ?? null,
  loadingText: p.innerText.includes(${JSON.stringify(LOADING_TEXT)}) } : null; })()`;

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
  if (ALTER) info("non-vacuity mode: expected text altered for placement", ALTER);

  const real = await (await fetch(`${BASE}/api/sites/${SITE}/gateway-health`)).json();
  claim("precondition: the stored gateway-health read answers with at least one gateway",
    Array.isArray(real.gateways) && real.gateways.length >= 1,
    { read_at: real.read_at, gateways: real.gateways?.map((g) => [g.gateway_external_id, g.registration, g.status]) });
  const g0 = real.gateways?.[0] ?? {};
  const branches = [
    ["stale", null, "loaded", "STALE", CONTACT],
    ["current", { code: 200, body: { ...real, gateways: [{ ...g0, status: "CURRENT", last_server_contact: real.read_at }] } }, "loaded", "CURRENT", CONTACT],
    ["unknown", { code: 200, body: { ...real, gateways: [{ ...g0, status: "UNKNOWN", last_server_contact: null, diagnostic_id: null }] } }, "loaded", "UNKNOWN", CONTACT],
    ["503", { code: 503, body: { detail: "unavailable" } }, "unavailable", null, REGISTRATION],
    ["404", { code: 404, body: { detail: "not found" } }, "unavailable", null, REGISTRATION],
    ["loading", "hold", null, null, null], // no panel-state attribute while pending; the loading sentence shows
  ];

  for (const [width, height] of WIDTHS) {
    await size(width, height);
    const W = String(width);

    // --- v6.9 mock references --------------------------------------------------------------
    for (const [id, panel] of [["sites", "Site inventory"], ["foundation", "Configured topology"],
      ["readiness", "Readiness and commissioning evidence"], ["sld", "What each part does"]]) {
      const ok = await go(`${BASE}/mockups/v69/index.html#/${id}`, `document.body && document.body.innerText.includes(${JSON.stringify(panel)})`);
      claim(`${W}: mock #/${id} renders "${panel}"`, ok);
      await shot(`g02-mock-${id}-${W}`);
    }

    // --- /sites (populated and empty) ---------------------------------------------------------
    claim(`${W} /sites: loaded`, await go(`${BASE}/sites`, READY.sites));
    await shot(`g02-app-sites-loaded-${W}`);
    const sitesBase = await verify(`${W} /sites`, SITES);
    claim(`${W} /sites (empty store): loaded`, await go(`${EMPTY}/sites`, loaded("No sites configured")));
    await shot(`g02-app-sites-empty-${W}`);
    const empty = await js(STRUCTURE);
    claim(`${W} /sites (empty store): no tagged element`, empty.texts.length === 0, { size: empty.texts.length, pairs: empty.pairs });
    claim(`${W} /sites (empty store): no horizontal page scroll`, empty.scrollWidth <= empty.innerWidth, { scrollWidth: empty.scrollWidth, innerWidth: empty.innerWidth });
    void sitesBase;

    // --- /foundation -------------------------------------------------------------------------
    claim(`${W} /foundation: loaded`, await go(route("foundation"), READY.foundation));
    const controls = await js(`[...document.querySelectorAll('[data-control-link]')].map(e => e.dataset.controlLink)`);
    info(`${W} /foundation: control-link positions rendered (measured)`, controls);
    const parts = await js(`[...document.querySelectorAll('[data-part-choice]')].map(e => e.dataset.partChoice)`);
    const periods = await js(`[...(document.querySelector('select[aria-label="Foundation period"]')?.options ?? [])]
      .map(o => ({ value: o.value, label: o.textContent }))`);
    info(`${W} /foundation: part choices (${parts.length})`, parts);
    info(`${W} /foundation: period choices (${periods.length})`, periods);
    await shot(`g02-app-foundation-now-${W}`);
    const foundationBase = await verify(`${W} /foundation`, FOUNDATION);

    // --- /foundation/readiness gateway branches -------------------------------------------------
    await send("Fetch.enable", { patterns: [{ urlPattern: "*gateway-health*" }] });
    let readinessBase = null;
    try {
      for (const [branch, variant, state, status, extra] of branches) {
        const label = `${W} /readiness [${branch}]`;
        gatewayVariant = variant;
        const ok = await go(route("foundation/readiness"), branch === "loading" ? READY.readinessLoading : READY.readiness);
        claim(`${label}: loaded`, ok);
        const gw = await js(GW);
        claim(`${label}: gateway panel state ${state === null ? "absent with the loading sentence" : `"${state}"`}, entry status ${status ?? "absent"}`,
          gw !== null && gw.state === state && gw.status === status && gw.loadingText === (state === null), gw);
        const expected = extra === null ? READINESS : [...READINESS, extra];
        await shot(`g02-app-readiness-${branch}-${W}`);
        const r = await verify(label, expected);
        const counts = (await js(STRUCTURE)).counts;
        const once = ["uptime", "completeness", "signal-strength", "firmware"].map((f) => [f, counts[`G-readiness-gateway-${f}@readiness.gateway.${f}`] ?? 0]);
        claim(`${label}: firmware, uptime, completeness and signal-strength each exactly once`, once.every(([, n]) => n === 1), Object.fromEntries(once));
        if (branch === "stale") readinessBase = r;
        if (branch === "loading") await release();
      }
    } finally {
      await release();
      await send("Fetch.disable").catch(() => {});
    }
    const table = readinessBase?.containers.find((c) => c.label === "readiness-table") ?? null;
    info(`${W} /readiness: Readiness table container (C1)`, table);

    // --- /foundation/sld -----------------------------------------------------------------------
    claim(`${W} /sld: loaded`, await go(route("foundation/sld"), READY.sld));
    await shot(`g02-app-sld-now-${W}`);
    await verify(`${W} /sld`, SLD);

    // --- selection, date, reload ---------------------------------------------------------------
    const component = parts[0] ?? null;
    const other = periods.find((p) => p.value !== "" && !/\(current\)/.test(p.label)) ?? null;
    claim(`${W}: a real component id and another stored period were read from the page`, component !== null && other !== null, { component, at: other });
    for (const [name, path, ready, base, expected] of [
      ["foundation", "foundation", READY.foundation, foundationBase, FOUNDATION],
      ["readiness", "foundation/readiness", READY.readiness, readinessBase, [...READINESS, CONTACT]],
    ]) {
      const variants = [];
      if (component !== null) variants.push(["component", `?component=${encodeURIComponent(component)}`]);
      if (other !== null) variants.push(["at", `?at=${encodeURIComponent(other.value)}`]);
      variants.push(["reload", ""]);
      for (const [v, query] of variants) {
        const label = `${W} /${name} [${v}${v === "component" ? `=${component}` : v === "at" ? `=${other.value}` : ""}]`;
        if (v === "reload") {
          await go(route(path), ready);
          await send("Page.reload", { ignoreCache: true });
          await waitFor(ready);
          await requireWidth(viewport[0], viewport[1], "after reload or back");
          await sleep(400);
        } else {
          claim(`${label}: loaded`, await go(route(path, query), ready));
        }
        const applied = await js(`({ search: location.search, pressed: document.querySelector('[data-part-choice][aria-pressed="true"]')?.dataset.partChoice ?? null,
          period: document.querySelector('select[aria-label="Foundation period"]')?.value ?? null })`);
        info(`${label}: address and selection after load`, applied);
        if (v !== "reload") await shot(`g02-app-${name}-${v}-${W}`);
        const r = await verify(label, expected);
        claim(`${label}: pair set unchanged from the default view`, base !== null && JSON.stringify(r.pairs) === JSON.stringify(base.pairs), { size: r.pairs.length, baseSize: base?.pairs.length ?? null });
      }
    }
  }
  claim("screenshot file names are unique per route+state+viewport", shotClash.length === 0, { size: shotNames.size, clashes: shotClash });
  info("screenshots", [...shotNames].map((n) => `${n}.png`));
}

main()
  .catch((error) => {
    claim("evidence run completed", false, String(error?.stack ?? error));
  })
  .finally(() => {
    const failed = results.filter((r) => !r.ok).length;
    console.log(`\n${results.length - failed}/${results.length} claims passed; screenshots in ${OUT}`);
    chrome.kill();
    setTimeout(() => {
      try {
        rmSync(profile, { recursive: true, force: true });
      } catch {
        /* Chrome may still hold the profile */
      }
      process.exit(failed === 0 ? 0 : 1);
    }, 500);
  });
