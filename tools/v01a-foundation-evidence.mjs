/**
 * SUPERSEDED for these screens by tools/g02-gap-evidence.mjs: this tool asserts pre-G-02 copy and will fail on
 * the current tree. A failure here is not a regression; it is kept as the recorded historical evidence tool.
 *
 * V-01a: app-vs-mock evidence for Sites, Foundation (Site model), Readiness and the single line
 * diagram (`sites:1`, `foundation:1-3`, `readiness:1`, `sld:1-2`), with layout measurements,
 * keyboard interaction, period selection and reload checks, from the installed Chrome over the
 * DevTools Protocol (same approach as tools/s3-dispatch-evidence.mjs; no dependency).
 *
 * Run against the walkthrough servers (tools/v01a_foundation_walkthrough.py prepare + serve,
 * populated frontend on 5360, empty-store frontend on 5361):
 *   node tools/v01a-foundation-evidence.mjs http://localhost:5360 <screenshot-dir> http://localhost:5361
 *
 * A second copy runs on its own ports and databases (never the owner's 8860/8861/5360/5361):
 *   tools/v01a_foundation_walkthrough.py --db assetops_<x>walk --empty-db assetops_<x>empty --work-name <x> serve
 *     --port 8880 --web-port 5380 --empty-port 8881 --empty-web-port 5381
 *   node tools/v01a-foundation-evidence.mjs http://localhost:5380 <screenshot-dir> http://localhost:5381
 *
 * Every claim is measured and printed; the run exits non-zero if any fails. Set-based claims
 * report their size, so a claim over an empty set is visible.
 *
 * Round 3 gateway states. The stored KOBO-001 copy answers `/gateway-health` with one ENABLED
 * gateway whose contact is STALE (its last diagnostic is hours old), so STALE and the historical
 * and scheduled `at` notes are rendered from the real read. The other states are produced by
 * intercepting that one request in the browser (DevTools `Fetch`) and answering with a variant of
 * the real body: CURRENT (last contact = read time), UNKNOWN (no diagnostic), DISABLED
 * registration, no gateway (`gateways: []`), a 503 (read failed), a 404 (no record), and a held
 * request (loading). These prove what the UI renders for each response shape; they are not stored
 * states and claim nothing about the gateway itself.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const BASE = process.argv[2] ?? "http://localhost:5360";
const OUT = process.argv[3] ?? join(tmpdir(), "v01a-foundation-evidence");
const SITE = "KOBO-001";
const PORT = 9361;
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  ["desktop", 1440, 1000],
  ["narrow", 390, 900],
];
mkdirSync(OUT, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "assetops-v01a-cdp-"));
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
      wide: [...document.querySelectorAll('main *')].filter(e => e.getBoundingClientRect().right > d.clientWidth + 1
      && !e.closest('.data-table__scroll, .sld__scroll') && ![...e.children].some(c => c.getBoundingClientRect().right > d.clientWidth + 1))
      .map(e => (e.getAttribute('class') || e.tagName) + ':' + Math.round(e.getBoundingClientRect().width)).slice(0, 6) }; })()`);

const EMPTY = process.argv[4] ?? "http://localhost:5361";
const MOCK = (id) => `${BASE}/mockups/v69/index.html#/${id}`;
const CURRENT = "2026-10-22T00:00:00Z"; // inside the SCHEDULED period v13 (from 2026-10-21); not in effect until then
const IMPORTED = "2026-09-30T00:00:00Z"; // inside the imported period (2026-09-29 to 2026-10-01)
const NONE = "2026-09-01T00:00:00Z"; // before any stored version
const nowView = (path) => `${BASE}/sites/${SITE}/${path}`; // no ?at=: the configuration in effect now
const view = (path, at) => `${BASE}/sites/${SITE}/${path}?at=${encodeURIComponent(at)}`;
const H2 = `[...document.querySelectorAll('main h2')].map(h => h.textContent.trim())`;
const SEL = `(() => { const s = document.querySelector('select[aria-label="Foundation period"]');
  return s ? { value: s.value, label: s.selectedOptions[0]?.textContent ?? null } : null; })()`;
const PARTS = `Object.fromEntries([...document.querySelectorAll('[data-part-channels]')].map(r => [r.dataset.partChannels,
  [...r.querySelectorAll('[data-part-channel="bound"] code')].map(c => c.textContent).sort().join('|')]))`;
const STRIP = (scope) => `(() => { const s = document.querySelector('[data-part-strip-region="${scope}"] [data-selected-part]');
  const region = s?.closest('[data-part-strip-region]'); const choice = document.querySelector('[data-part-choice="battery"]');
  return { part: s?.dataset.selectedPart ?? null, counts: s?.querySelector('[data-part-channel-counts]')?.textContent ?? null,
    live: region?.getAttribute('aria-live') ?? null, regionId: region?.id ?? null, controls: choice?.getAttribute('aria-controls') ?? null,
    pressed: choice?.getAttribute('aria-pressed') ?? null, strips: document.querySelectorAll('[data-selected-part]').length,
    inScroll: !!s?.closest('.sld__scroll'), clear: !!s?.querySelector('button.part-clear'),
    channelsOpen: s?.querySelector('details')?.open ?? null }; })()`;
const loaded = (text) =>
  `!document.querySelector('[aria-busy="true"]') && document.body.innerText.includes(${JSON.stringify(text)})`;

async function key(name, code, vk, text) {
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: name, code, windowsVirtualKeyCode: vk, ...(text ? { text } : {}) });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: name, code, windowsVirtualKeyCode: vk });
}
async function layout(name) {
  const o = await overflow();
  claim(`${name}: no horizontal page overflow`, o.scrollWidth <= o.clientWidth && o.wide.length === 0, o);
}

// --- gateway-health response variants (see header) -------------------------------------------
let gatewayVariant = null; // null: pass the real response through; "hold": leave the request pending
const held = [];
listeners.set("Fetch.requestPaused", (p) => {
  const v = gatewayVariant;
  if (v === "hold") {
    held.push(p.requestId);
    return;
  }
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
async function release() {
  gatewayVariant = null;
  while (held.length) await send("Fetch.continueRequest", { requestId: held.shift() });
}
const GATEWAY = `(() => { const p = [...document.querySelectorAll('main section.panel')].find(s => s.querySelector('h2')?.textContent.trim() === 'Gateway status');
  if (!p) return null; const e = p.querySelector('[data-gateway-status]');
  return { state: p.querySelector('[data-gateway-panel-state]')?.dataset.gatewayPanelState ?? null,
    status: e?.dataset.gatewayStatus ?? null, registration: e?.dataset.gatewayRegistration ?? null,
    badge: e?.querySelector('.badge')?.className ?? null,
    period: p.querySelector('[data-gateway-period-note]')?.dataset.gatewayPeriodNote ?? null,
    note: p.querySelector('[data-gateway-period-note]')?.textContent ?? null,
    missing: p.querySelector('[data-not-available-yet="gateway"]')?.textContent ?? null,
    advancedOpen: p.querySelector('details[data-disclosure^="gateway-diagnostic-"]')?.open ?? null,
    text: p.innerText }; })()`;
const NOT_AVAILABLE_GATEWAY =
  "Not available yet: uptime trend, expected-versus-delivered completeness, signal strength and firmware. No reviewed source for these fields.";
const SLD_NOTE =
  "Protection and meter positions are not declared in this Foundation topology; monitoring links and reporting status are not assessed on this diagram. See Site Evidence for reported records.";
const panelOf = (heading) =>
  `[...document.querySelectorAll('main section.panel')].find(s => s.querySelector('h2')?.textContent.trim() === ${JSON.stringify(heading)})`;
const box = (sel) => `(() => { const e = ${sel}; if (!e) return null; const r = e.getBoundingClientRect();
  return { left: Math.round(r.left), right: Math.round(r.right), top: Math.round(r.top), bottom: Math.round(r.bottom),
    width: Math.round(r.width), height: Math.round(r.height), vw: document.documentElement.clientWidth }; })()`;
const within = (b) => b !== null && b.width > 0 && b.left >= 0 && b.right <= b.vw + 1;
const ADV = (name) => `(() => { const d = document.querySelector('details[data-disclosure="${name}"]'); if (!d) return null;
  const body = d.querySelector(':scope > .disclosure__body');
  return { open: d.open, summary: d.querySelector(':scope > summary')?.textContent.trim() ?? null,
    bodyHeight: body?.checkVisibility() ? Math.round(body.getBoundingClientRect().height) : 0,
    height: Math.round(d.getBoundingClientRect().height) }; })()`;
async function toggle(name) {
  await js(`document.querySelector('details[data-disclosure="${name}"] > summary').click()`);
  await sleep(300);
  return js(ADV(name));
}
/** A labelled Advanced disclosure is closed by default and shows its body only once opened by its summary. */
async function advanced(label, name, summary, shotName) {
  const closed = await js(ADV(name));
  const opened = closed === null ? null : await toggle(name);
  claim(`${label}: "${summary}" is closed by default and opens from its summary`,
    closed !== null && !closed.open && closed.bodyHeight === 0 && closed.summary === summary && opened.open && opened.bodyHeight > 0 && opened.height > closed.height,
    { closed, opened });
  if (opened !== null) {
    await layout(`${label}: ${summary} (open)`);
    await shot(shotName);
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

  for (const [label, width, height] of WIDTHS) {
    viewport = [width, height];
    await size(width, height);

    // --- v6.9 references ---------------------------------------------------------------------
    for (const [id, panels] of [
      ["sites", ["Site inventory"]],
      ["foundation", ["Configured topology", "Identity & operating obligations", "Time-valid control configuration"]],
      ["readiness", ["Readiness and commissioning evidence"]],
      ["sld", ["Kobo Mini-grid · AC-coupled mini-grid", "What each part does"]],
    ]) {
      await go(MOCK(id), `document.body && document.body.innerText.includes(${JSON.stringify(panels[0])})`);
      const found = await js(`${JSON.stringify(panels)}.filter(p => document.body.innerText.includes(p))`);
      claim(`${label}: mock #/${id} renders its compared panels`, found.length === panels.length, { found });
      await shot(`mock-${id}-${label}`);
    }

    // --- sites:1 -----------------------------------------------------------------------------
    await go(`${BASE}/sites`, loaded("Site inventory"));
    const sites = await js(`({ h2: ${H2}, rows: [...document.querySelectorAll('main tbody tr')].map(r => r.innerText.split('\\n')[0]),
      columns: [...document.querySelectorAll('main thead th')].map(t => t.textContent.trim()),
      note: document.querySelector('[data-testid="sites-analysis-absent"]')?.textContent ?? null,
      setup: document.querySelectorAll('main details.site-setup').length,
      aggregate: document.querySelector('[data-testid="sites-aggregate-absent"]')?.textContent ?? null })`);
    claim(
      `${label}: app /sites lists the stored Site compactly (Site, Type, Mode, Operating view, Setup details) with the analysis-absent note`,
      sites.h2.includes("Site inventory") && sites.rows.length === 1 && /Kobo/i.test(sites.rows[0])
        && JSON.stringify(sites.columns) === JSON.stringify(["Site", "Type", "Mode", "Operating view", "Setup details", "Actions"])
        && /not available in this directory/.test(sites.note ?? "") && sites.setup === 1,
      sites,
    );
    // Round 3 (addendum, sites:1): one grouped Operating view cell per Site and one aggregate note.
    const opv = await js(`(() => { const cells = [...document.querySelectorAll('main [data-operating-view]')];
      const sc = document.querySelector('main .data-table__scroll');
      return { cells: cells.length, rows: document.querySelectorAll('main tbody tr').length,
        texts: cells.map(c => c.innerText.replace(/\\s+/g, ' ').trim()),
        clipped: cells.flatMap(c => [...c.querySelectorAll('span')]).filter(e => e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).display !== 'inline').length,
        cell: (() => { const r = cells[0]?.getBoundingClientRect(); return r ? { left: Math.round(r.left), width: Math.round(r.width) } : null; })(),
        table: sc ? { scrollWidth: sc.scrollWidth, clientWidth: sc.clientWidth } : null }; })()`);
    claim(`${label}: every Site row has one Operating view cell saying "Not available yet" with its four named parts`,
      opv.cells >= 1 && opv.cells === opv.rows
        && opv.texts.every((t) => t.startsWith("Not available yet") && t.includes("Assessment · top issue · evidence limit · last analysed"))
        && opv.clipped === 0, opv);
    claim(`${label}: the aggregate and setup-progress gap is named once beside the inventory, with the registered Site count`,
      /^1 registered Site listed\. Needs attention and Evidence limited counts across Sites are not available yet/.test(sites.aggregate ?? "")
        && /Setup progress not tracked yet\./.test(sites.aggregate ?? ""), { aggregate: sites.aggregate });
    await layout(`${label}: /sites`);
    await shot(`app-sites-${label}`);
    await go(`${EMPTY}/sites`, loaded("No sites configured"));
    const empty = await js(`({ h2: ${H2}, rows: document.querySelectorAll('main tbody tr').length })`);
    claim(`${label}: empty store shows "No sites configured" and no row`, empty.h2.includes("No sites configured") && empty.rows === 0, empty);
    await layout(`${label}: /sites (empty)`);
    await shot(`app-sites-empty-${label}`);

    // --- foundation:1-3 ----------------------------------------------------------------------
    // --- in effect now (no ?at=): the configuration a user lands on ---------------------------
    for (const [name, path, text] of [["foundation", "foundation", "Time-valid control configuration"],
      ["sld", "foundation/sld", "What each configured part is"], ["readiness", "foundation/readiness", "Readiness and commissioning evidence"]]) {
      await go(nowView(path), loaded(text));
      const n = await js(`({ sel: ${SEL}, text: document.body.innerText })`);
      claim(`${label}: ${name} with no ?at= is the configuration in effect now`,
        /in effect now/i.test(n.sel?.label ?? "") && n.sel?.value === "" && (name === "foundation" || /configuration in effect now/i.test(n.text))
          && !/(Scheduled|Historical) period:/.test(n.text), n.sel);
      await layout(`${label}: ${name} (in effect now)`);
      await shot(`app-${name}-now-${label}`);
    }

    await go(view("foundation", CURRENT), loaded("Time-valid control configuration"));
    const model = await js(`({ h2: ${H2}, sel: ${SEL}, bus: document.querySelector('[data-topology-bus]')?.textContent,
      cards: document.querySelectorAll('.plant-card').length })`);
    claim(
      `${label}: Site model shows the three compared panels`,
      ["Configured topology", "Identity & operating obligations", "Time-valid control configuration"].every((h) => model.h2.includes(h)),
      model.h2,
    );
    claim(`${label}: topology draws declared cards on a bus labelled with its declared rating`,
      model.cards >= 4 && /AC bus · 400 V/.test(model.bus ?? ""), { cards: model.cards, bus: model.bus });
    const icons = await js(`(() => { const cards = [...document.querySelectorAll('.plant-card')];
      return { cards: cards.length, parts: cards.reduce((n, c) => n + c.querySelectorAll('[data-part-choice]').length, 0),
        icons: cards.reduce((n, c) => n + c.querySelectorAll('svg[role="img"][aria-label] [data-component-icon]').length, 0),
        names: [...new Set([...document.querySelectorAll('.plant-card svg[role="img"]')].map(i => i.getAttribute('aria-label')))] }; })()`);
    claim(`${label}: every topology-card part carries a type icon named by its declared type`,
      icons.parts >= 4 && icons.icons === icons.parts, icons);
    claim(`${label}: an address instant stays the selected period (never "In effect now")`,
      model.sel?.value === CURRENT && /from the address/.test(model.sel?.label ?? ""), model.sel);
    // Round 3 (foundation:2-3): two-column pair, identity facts, Evidence / change column, Advanced records.
    const pair = await js(`({ topo: ${box(panelOf("Configured topology"))}, id: ${box(panelOf("Identity & operating obligations"))} })`);
    claim(`${label}: Configured topology and Identity & operating obligations ${width > 760 ? "sit side by side, tops aligned" : "stack in reading order"} inside the viewport`,
      within(pair.topo) && within(pair.id) && (width > 760
        ? Math.abs(pair.topo.top - pair.id.top) <= 2 && pair.id.left >= pair.topo.right - 1
        : pair.id.top >= pair.topo.bottom - 1), pair);
    const ident = await js(`(() => { const p = ${panelOf("Identity & operating obligations")}; const q = (s) => p?.querySelector(s);
      return { critical: q('[data-critical-load]')?.dataset.criticalLoad ?? null, criticalText: q('[data-critical-load]')?.textContent ?? null,
        loads: q('[data-configured-loads]')?.textContent ?? null, productive: q('[data-productive-use]')?.textContent ?? null,
        financial: q('[data-financial-assumptions]')?.textContent ?? null }; })()`);
    claim(`${label}: Identity shows the typed critical-load priority and the stored loads, and names the undeclared productive use and missing financial assumptions`,
      (ident.critical === "configured" ? /^First in critical-load priority: \S/.test(ident.criticalText ?? "")
        : ident.criticalText === "Critical-load priority not configured")
        && (ident.loads ?? "").split(", ").filter((x) => x && x !== "No load declared").length >= 1
        && ident.productive === "Not declared" && /^Financial assumptions not available here\./.test(ident.financial ?? ""), ident);
    const ctl = await js(`(() => { const p = ${panelOf("Time-valid control configuration")};
      return { heads: [...(p?.querySelectorAll('thead th') ?? [])].map(t => t.textContent.trim()), rows: p?.querySelectorAll('tbody tr').length ?? 0,
        links: [...(p?.querySelectorAll('[data-control-link]') ?? [])].map(e => ({ kind: e.dataset.controlLink, text: e.textContent.trim(),
          href: e.querySelector('a')?.getAttribute('href') ?? (e.tagName === 'A' ? e.getAttribute('href') : null) })) }; })()`);
    const KINDS = { published: /^Published configuration · Foundation v\d+$/, "no-change-record": /^No proposed-change record here$/,
      "no-constraint-evidence": /^No linked constraint evidence$/, dispatch: /Open Dispatch; choose an assessed day/, "no-dispatch": /^Dispatch not available here/ };
    claim(`${label}: every control's Evidence / change position names a real destination or the exact missing record (no dummy link)`,
      ctl.heads.includes("Evidence / change") && ctl.links.length >= 1 && ctl.links.some((l) => l.kind === "published")
        && ctl.links.every((l) => KINDS[l.kind]?.test(l.text) && (l.kind === "dispatch" ? /\/performance/.test(l.href ?? "") : l.href === null)),
      { rows: ctl.rows, links: ctl.links });
    await layout(`${label}: Site model`);
    await shot(`app-foundation-scheduled-${label}`);
    await advanced(label, "foundation-advanced", "Advanced details — Foundation records", `app-foundation-advanced-open-${label}`);

    // Round 3 item 4: the chosen part's strip sits in the topology panel, with Clear returning focus.
    await go(view("foundation", CURRENT), loaded("Time-valid control configuration"));
    await js(`document.querySelector('[data-part-choice="battery"]').click()`);
    await waitFor(`location.search.includes('component=battery') && document.querySelector('[data-part-strip-region="model"] [data-selected-part="battery"]')`);
    await sleep(300);
    const strip = await js(`({ ...${STRIP("model")}, inTopology: !!(${panelOf("Configured topology")})?.contains(document.querySelector('[data-selected-part]')) })`);
    const stripBox = await js(box(`document.querySelector('[data-selected-part]')`));
    claim(`${label}: choosing a topology part shows one compact strip inside the topology panel (counts, Clear, polite live region, channels closed)`,
      strip.part === "battery" && strip.inTopology && strip.strips === 1 && /^\d+ bound; \d+ not bound$/.test(strip.counts ?? "")
        && strip.live === "polite" && strip.controls === strip.regionId && strip.pressed === "true" && strip.clear && strip.channelsOpen === false
        && within(stripBox), { strip, stripBox });
    await shot(`app-foundation-part-strip-${label}`);
    await advanced(label, "selected-part-channels-model", "Advanced details — selected part channels", `app-foundation-part-strip-open-${label}`);
    const listed = await js(`[...document.querySelectorAll('[data-selected-part] [data-part-channel]')].filter(e => e.checkVisibility()).length`);
    claim(`${label}: the open strip lists the part's channels (non-empty)`, listed >= 1, { listed });
    await js(`document.querySelector('[data-selected-part] button.part-clear').click()`);
    await waitFor(`!location.search.includes('component=') && !document.querySelector('[data-selected-part]')`);
    await sleep(300);
    const cleared = await js(`({ url: location.pathname + location.search, focus: document.activeElement?.getAttribute('data-part-choice') ?? null,
      strips: document.querySelectorAll('[data-selected-part]').length, region: !!document.querySelector('[data-part-strip-region="model"]') })`);
    claim(`${label}: Clear removes the strip and the address part, keeps the period, and returns focus to the part's own control`,
      cleared.strips === 0 && cleared.region && cleared.focus === "battery" && cleared.url.includes(`at=${encodeURIComponent(CURRENT)}`), cleared);
    await shot(`app-foundation-part-cleared-${label}`);
    await go(view("foundation", NONE), loaded("No stored version for this period"));
    claim(`${label}: a period before any stored version is stated, not filled with current data`,
      await js(`${H2}.includes("No stored version for this period") && !document.body.innerText.includes("Configured topology")`));
    await layout(`${label}: Site model (no stored version)`);
    await shot(`app-foundation-missing-${label}`);

    // --- sld:1-2 -----------------------------------------------------------------------------
    await go(view("foundation/sld", CURRENT), loaded("What each configured part is"));
    const sld = await js(`({ h2: ${H2}, parts: ${PARTS},
      unchanneled: [...document.querySelectorAll('[data-part-channels]')].filter(r => r.textContent.includes('No channel declared')).length,
      counts: [...document.querySelectorAll('[data-sld-part] td:last-child')].map(c => c.textContent.trim()),
      note: document.querySelector('[data-sld-missing]')?.textContent.trim() ?? null,
      noteLink: document.querySelector('[data-sld-missing] a')?.getAttribute('href') ?? null,
      noteInDrawing: !!document.querySelector('[data-sld-missing]')?.closest('svg, .sld__scroll'),
      svg: !!document.querySelector('main svg') })`);
    const boundParts = Object.values(sld.parts).filter((v) => v !== "").length;
    claim(
      `${label}: SLD shows the drawing and the parts table with bound channels per part`,
      sld.svg && sld.h2.some((h) => h.includes("configured single line diagram")) && boundParts >= 5 && sld.unchanneled >= 1,
      { boundParts, parts: Object.keys(sld.parts).length, unchanneled: sld.unchanneled },
    );
    claim(`${label}: the plain parts table shows channel counts only (the lists are under Advanced details)`,
      sld.counts.length === 10 && sld.counts.every((c) => /^\d+ bound; \d+ not bound$|^No channel declared$/.test(c))
        && (await js(`document.querySelectorAll('[data-sld-part] [data-part-channel]').length`)) === 0, { counts: sld.counts });
    claim(`${label}: beside the drawing, the protection/meter note is the addendum's sentence with a Site Evidence link, outside the drawing`,
      sld.note === `${SLD_NOTE} Site Evidence →` && /\/evidence/.test(sld.noteLink ?? "") && !sld.noteInDrawing,
      { note: sld.note, link: sld.noteLink });
    await layout(`${label}: SLD`);
    await shot(`app-sld-scheduled-${label}`);
    // Devices caption (backlog carry): open the device disclosure and read it.
    const caption = await js(`(() => { const d = document.querySelector('details[data-disclosure="sld-devices"]');
      if (!d) return null; d.open = true;
      return [...d.querySelectorAll('caption, p')].map(c => c.textContent).find(t => t.includes('devices this site')) ?? null; })()`);
    claim(`${label}: devices caption is consistent (not assessed here; no "none has reported")`,
      caption !== null && /reporting is not assessed here/.test(caption) && !/none has reported/.test(caption), { caption });
    await js(`document.querySelectorAll('details').forEach(d => { d.open = false; })`);
    await advanced(label, "sld-advanced", "Advanced details — diagram records", `app-sld-advanced-open-${label}`);
    await js(`document.querySelectorAll('details').forEach(d => { d.open = false; })`);

    // Bound components stay stable across reload; they follow the selected period.
    await send("Page.reload");
    await waitFor(loaded("What each configured part is"));
    await sleep(300);
    const reloaded = await js(`({ parts: ${PARTS}, sel: ${SEL}, url: location.pathname + location.search })`);
    claim(`${label}: reload keeps the selected period and every part's bound channels`,
      JSON.stringify(reloaded.parts) === JSON.stringify(sld.parts) && reloaded.sel?.value === CURRENT, { url: reloaded.url, sel: reloaded.sel });
    await go(view("foundation/sld", IMPORTED), loaded("What each configured part is"));
    const early = await js(PARTS);
    await shot(`app-sld-imported-${label}`);
    const differs = Object.keys(sld.parts).filter((k) => early[k] !== sld.parts[k]);
    claim(`${label}: another selected period shows that period's bindings (set differs)`, differs.length >= 1, { differs });

    // --- sld: bus-bar grammar, selection by keyboard, missing part -----------------------------
    await go(view("foundation/sld", CURRENT), loaded("What each configured part is"));
    const bus = await js(`(() => { const svg = document.querySelector('[data-sld-region] svg');
      const bar = svg?.querySelector('.sld-node__bar'); const x = Number(bar?.getAttribute('x1'));
      const runs = [...(svg?.querySelectorAll('[data-sld-connection]') ?? [])];
      const atBar = runs.filter(r => r.getAttribute('points').split(' ').some(p => Number(p.split(',')[0]) === x));
      const texts = [...(svg?.querySelectorAll('text') ?? [])];
      const sc = svg?.closest('.sld__scroll');
      return { layout: svg?.dataset.sldLayout, role: svg?.getAttribute('role'), bars: svg?.querySelectorAll('.sld-node__bar').length,
        nodes: svg?.querySelectorAll('[data-sld-node]').length, buttons: svg?.querySelectorAll('[data-sld-node][role="button"]').length,
        runs: runs.length, runsAtBar: atBar.length,
        stray: texts.filter(t => !t.matches('.sld-node__name, .sld-node__rating, .sld-node__slot, .sld-node__candidate')).map(t => t.textContent),
        label: document.querySelector('[data-sld-configured]')?.textContent ?? null,
        drawing: Math.round(svg?.getBoundingClientRect().width ?? 0), region: sc?.clientWidth, scrolls: sc ? sc.scrollWidth > sc.clientWidth + 1 : null }; })()`);
    claim(`${label}: SLD is drawn in the bus-bar grammar from the declared topology only, labelled "Configured, not live"`,
      bus.layout === "bus-bar" && bus.bars === 1 && bus.nodes === 10 && bus.runs === 9 && bus.runsAtBar >= 4
        && bus.stray.length === 0 && /Configured, not live/.test(bus.label ?? "") && bus.role === "group" && bus.buttons === bus.nodes, bus);
    // Reach the part by keyboard: focus the drawing's scroll region, then Tab through the parts.
    await js(`document.querySelector('[data-sld-region] .sld__scroll').focus()`);
    for (let i = 0; i < 12; i += 1) {
      await key("Tab", "Tab", 9);
      if ((await js(`document.activeElement?.getAttribute('data-sld-component')`)) === "battery") break;
    }
    const ring = await js(`(() => { const h = document.activeElement?.querySelector('.sld-node__halo'); const cs = h && getComputedStyle(h);
      return { focused: document.activeElement?.getAttribute('data-sld-component'), stroke: cs?.stroke, width: cs?.strokeWidth }; })()`);
    await key("Enter", "Enter", 13, "\r");
    await waitFor(`location.search.includes('component=battery')`);
    await sleep(300);
    const picked = await js(`({ url: location.pathname + location.search,
      pressed: document.querySelector('[data-sld-region] [data-sld-component="battery"]')?.getAttribute('aria-pressed'),
      panel: document.querySelector('[data-selected-part]')?.getAttribute('data-selected-part'), strip: ${STRIP("sld")},
      inPanel: !!document.querySelector('[data-sld-region]')?.closest('section.panel')?.contains(document.querySelector('[data-selected-part]')) })`);
    claim(`${label}: a drawn part takes visible keyboard focus and Enter chooses it by component ID`,
      ring.focused === "battery" && ring.stroke !== "none" && picked.url.includes(`at=${encodeURIComponent(CURRENT)}`)
        && picked.url.includes("component=battery") && picked.pressed === "true" && picked.panel === "battery", { ring, picked });
    claim(`${label}: on the SLD the strip sits after the drawing in the SLD panel, outside its horizontal scroll area`,
      picked.strip.part === "battery" && picked.inPanel && !picked.strip.inScroll && picked.strip.strips === 1 && picked.strip.live === "polite"
        && /^\d+ bound; \d+ not bound$/.test(picked.strip.counts ?? ""), picked.strip);
    await layout(`${label}: SLD (part selected)`);
    await shot(`app-sld-selected-${label}`);
    const panelBox = await js(`(() => { const r = document.querySelector('[data-selected-part]').getBoundingClientRect();
      return { left: Math.round(r.left), right: Math.round(r.right), vw: document.documentElement.clientWidth }; })()`);
    claim(`${label}: the chosen part and its channels are readable without horizontal scrolling`,
      panelBox.left >= 0 && panelBox.right <= panelBox.vw + 1, panelBox);
    await send("Page.reload");
    await waitFor(loaded("What each configured part is"));
    await sleep(300);
    const afterReload = await js(`document.querySelector('[data-selected-part]')?.getAttribute('data-selected-part')`);
    await go(view("foundation/readiness", CURRENT) + "&component=battery", loaded("Readiness and commissioning evidence"));
    const kept = await js(`({ chip: document.querySelector('[data-selected-part-chip]')?.getAttribute('data-selected-part-chip') ?? null,
      strips: document.querySelectorAll('[data-selected-part]').length, url: location.search })`);
    claim(`${label}: the chosen part survives reload, and Readiness keeps it in the address as a compact chip (no inspection panel)`,
      afterReload === "battery" && kept.chip === "battery" && kept.strips === 0 && kept.url.includes("component=battery"), { afterReload, kept });
    await shot(`app-readiness-part-chip-${label}`);
    await go(view("foundation/sld", CURRENT) + "&component=no-such-part", loaded("What each configured part is"));
    await waitFor(`!location.search.includes('component=')`);
    await sleep(300);
    const missing = await js(`({ url: location.pathname + location.search, notice: document.querySelector('[data-selected-part-missing]')?.textContent ?? null,
      chosen: document.querySelectorAll('[data-sld-region] [data-selected]').length })`);
    claim(`${label}: an address naming a part this period does not declare clears it and says so`,
      /Selected part is not in this Foundation period/.test(missing.notice ?? "") && !missing.url.includes("component=") && missing.chosen === 0, missing);
    await shot(`app-sld-missing-part-${label}`);

    // --- readiness:1 -------------------------------------------------------------------------
    await go(view("foundation/readiness", CURRENT), loaded("Readiness and commissioning evidence"));
    const ready = await js(`({ h2: ${H2}, state: document.querySelector('[data-readiness-state]')?.dataset.readinessState,
      text: document.querySelector('main').innerText, all: document.querySelector('main').textContent })`);
    const at = (h) => ready.h2.indexOf(h);
    claim(`${label}: Readiness leads with the verdict, then the evidence table and Gateway status; role coverage and bindings are kept under Advanced`,
      !!ready.state && at("Configuration readiness") >= 0 && at("Configuration readiness") < at("Readiness and commissioning evidence")
        && at("Readiness and commissioning evidence") < at("Gateway status") && at("Gateway status") < at("Role coverage")
        && at("Signal bindings") > at("Gateway status") && !ready.text.includes("Role coverage"),
      { h2: ready.h2, state: ready.state });
    const cards = await js(`[...document.querySelectorAll('[data-readiness-card]')].map(c => ({ key: c.dataset.readinessCard,
      state: c.dataset.cardState, word: c.querySelector('.badge')?.textContent ?? null, tone: c.querySelector('.badge')?.className ?? null }))`);
    const WORD = { CONFIGURED: ["Configured", /badge--configured/], NEEDS_CONFIGURATION: ["Needs configuration", /badge--config-gap/],
      UNKNOWN: ["Unknown", /badge--neutral/] };
    claim(`${label}: four category cards (Definition, Topology, Specifications, Controls), each Configured / Needs configuration / Unknown with its tone`,
      JSON.stringify(cards.map((c) => c.key)) === JSON.stringify(["definition", "topology", "specifications", "controls"])
        && cards.every((c) => WORD[c.state] && c.word === WORD[c.state][0] && WORD[c.state][1].test(c.tone ?? "")), cards);
    const cardBox = await js(`(() => { const l = document.querySelector('[data-readiness-cards]'); const items = [...l.children].map(c => c.getBoundingClientRect());
      return { columns: new Set(items.map(r => Math.round(r.left))).size, right: Math.round(Math.max(...items.map(r => r.right))),
        vw: document.documentElement.clientWidth }; })()`);
    claim(`${label}: the cards lay out in ${width > 900 ? "one row of four" : "a single column"} inside the viewport`,
      cardBox.columns === (width > 900 ? 4 : 1) && cardBox.right <= cardBox.vw + 1, cardBox);
    const table = await js(`(() => { const t = document.querySelector('[data-readiness-row]')?.closest('table');
      return { heads: [...(t?.querySelectorAll('thead th') ?? [])].map(h => h.textContent.trim()),
        rows: [...document.querySelectorAll('[data-readiness-row]')].map(r => ({ key: r.dataset.readinessRow,
          confirmed: r.querySelector('[data-confirmed]')?.dataset.confirmed ?? null, confirmedText: r.querySelector('[data-confirmed]')?.textContent.trim() ?? null,
          needs: r.textContent.includes('Commissioning confirmation not recorded'),
          next: r.querySelector('td:last-child')?.textContent.trim() ?? null })) }; })()`);
    claim(`${label}: the evidence table has Area / Declared / Confirmed / What is needed / Next step and six rows, each Confirmed "Not recorded" with commissioning named as needed`,
      JSON.stringify(table.heads) === JSON.stringify(["Area", "Declared", "Confirmed", "What is needed", "Next step"])
        && JSON.stringify(table.rows.map((r) => r.key)) === JSON.stringify(["definition", "topology", "controls", "roles", "gateway", "commissioning"])
        && table.rows.every((r) => r.confirmed === "not-recorded" && r.confirmedText === "Not recorded" && r.needs && (r.next ?? "") !== ""),
      table.rows);
    const wording = ["Configuration readiness is distinct from claim readiness", "operational status is not assessed here",
      "Whether any channel is reporting is not assessed here"];
    // The third sentence sits with the bindings under Advanced details: retained in the page, read from its text.
    const lower = ready.all.toLowerCase();
    // A health word may appear only inside a sentence that disclaims it ("It does not mean ... healthy").
    const healthWords = ready.text
      .split(/(?<=[.;:])\s+/)
      .filter((t) => /\b(online|offline|healthy)\b/i.test(t) && !/\bnot\b/i.test(t));
    claim(`${label}: Readiness separates configuration from operational status (PRE-S3-04 wording)`,
      wording.every((w) => lower.includes(w.toLowerCase())) && healthWords.length === 0,
      { missing: wording.filter((w) => !lower.includes(w.toLowerCase())), healthWords });
    const green = await js(`(() => { const c = document.querySelector('.badge--configured'); const m = document.querySelector('.badge--provenance');
      const st = (e) => e && { bg: getComputedStyle(e).backgroundColor, fg: getComputedStyle(e).color, mark: getComputedStyle(e, '::before').content };
      return { configured: st(c), mode: st(m) }; })()`);
    claim(`${label}: the configuration green carries a tick mark the Mode badge's green does not`,
      green.configured !== null && !["none", "normal"].includes(green.configured.mark)
        && (green.mode === null || ["none", "normal"].includes(green.mode.mark)), green);
    await layout(`${label}: Readiness`);
    await shot(`app-readiness-scheduled-${label}`);
    // Advanced: closed by default; the plain "Review or change bindings" next step opens it and focuses the binding control.
    const advClosed = await js(ADV("readiness-advanced"));
    await js(`document.querySelector('[data-review-bindings]').click()`);
    await sleep(400);
    const review = await js(`({ adv: ${ADV("readiness-advanced")}, focus: document.activeElement?.tagName ?? null,
      inside: !!document.activeElement?.closest('details[data-disclosure="readiness-advanced"]') })`);
    claim(`${label}: "Advanced details — roles, channels and records" is closed by default; "Review or change bindings" opens it and focuses the binding control`,
      advClosed !== null && !advClosed.open && advClosed.bodyHeight === 0 && advClosed.summary === "Advanced details — roles, channels and records"
        && review.adv.open && review.adv.bodyHeight > 0 && review.adv.height > advClosed.height && review.focus === "SELECT" && review.inside, { advClosed, review });
    await layout(`${label}: Readiness (Advanced open)`);
    await shot(`app-readiness-advanced-open-${label}`);

    // --- readiness gateway status: real read (STALE) and response variants (see header) -------
    const real = await (await fetch(`${BASE}/api/sites/${SITE}/gateway-health`)).json();
    claim(`${label}: precondition - the stored copy's gateway-health read answers with at least one gateway`,
      Array.isArray(real.gateways) && real.gateways.length >= 1, { read_at: real.read_at, gateways: real.gateways?.map((g) => [g.gateway_external_id, g.registration, g.status]) });
    const gw = await js(GATEWAY);
    claim(`${label}: gateway (real read): registration and central contact shown apart with a neutral badge, the scheduled-period note and the Not-available-yet line`,
      gw.state === "loaded" && gw.status === real.gateways[0].status && gw.registration === real.gateways[0].registration
        && /badge--neutral/.test(gw.badge ?? "") && gw.period === "FUTURE" && /it did not occur in that period/.test(gw.note ?? "")
        && gw.missing === NOT_AVAILABLE_GATEWAY && /Device connection not established here\./.test(gw.text) && gw.advancedOpen === false,
      { state: gw.state, status: gw.status, registration: gw.registration, period: gw.period });
    const gwBox = await js(box(panelOf("Gateway status")));
    claim(`${label}: the Gateway status panel fits the viewport`, within(gwBox), gwBox);
    for (const [name, url, period, re] of [["in effect now", nowView("foundation/readiness"), "CURRENT", /configuration in effect now/],
      ["historical at (imported period)", view("foundation/readiness", IMPORTED), "PAST", /a past Foundation period .* it did not occur in that period/]]) {
      await go(url, loaded("Gateway status") + ` && document.querySelector('[data-gateway-panel-state]')`);
      const g = await js(GATEWAY);
      claim(`${label}: gateway note for ${name} labels contact as checked now on the server clock (${period})`,
        g.period === period && re.test(g.note ?? "") && /server clock/.test(g.note ?? "") && g.state === "loaded", { period: g.period, note: g.note });
      await shot(`app-readiness-gateway-${period.toLowerCase()}-${label}`);
    }
    const g0 = real.gateways[0];
    const variants = [
      ["current", 200, { ...real, gateways: [{ ...g0, status: "CURRENT", last_server_contact: real.read_at }] },
        (g) => g.state === "loaded" && g.status === "CURRENT" && /badge--neutral/.test(g.badge ?? "") && /This is not a live device connection/.test(g.text)],
      ["unknown", 200, { ...real, gateways: [{ ...g0, status: "UNKNOWN", last_server_contact: null, diagnostic_id: null, gateway_observed_at: null }] },
        (g) => g.state === "loaded" && g.status === "UNKNOWN" && g.text.includes("Contact unknown — no central diagnostic received.") && g.text.includes("None received")],
      ["disabled", 200, { ...real, gateways: [{ ...g0, registration: "DISABLED" }] },
        (g) => g.registration === "DISABLED" && g.text.includes("Disabled — switched off for this Site")],
      ["no gateway", 200, { ...real, gateways: [] },
        (g) => g.state === "none" && g.text.includes("No gateway is registered for this Site")],
      ["read failed (503)", 503, { detail: "unavailable" },
        (g) => g.state === "unavailable" && g.text.includes("Gateway contact unavailable.") && g.text.includes("Registration is configuration and is not taken as contact")
          && /Device connection not established here\./.test(g.text) && !/badge/.test(g.badge ?? "")],
      ["no record (404)", 404, { detail: "not found" },
        (g) => g.state === "unavailable" && g.text.includes("Gateway contact unavailable.")],
    ];
    await send("Fetch.enable", { patterns: [{ urlPattern: "*gateway-health*" }] });
    try {
      for (const [name, code, body, ok] of variants) {
        gatewayVariant = { code, body };
        await go(view("foundation/readiness", CURRENT), loaded("Gateway status") + ` && document.querySelector('[data-gateway-panel-state]')`);
        const g = await js(GATEWAY);
        claim(`${label}: gateway variant "${name}" renders its state with the Not-available-yet line`, ok(g) && g.missing === NOT_AVAILABLE_GATEWAY,
          { state: g.state, status: g.status, registration: g.registration });
        await layout(`${label}: Readiness gateway ${name}`);
        await shot(`app-readiness-gateway-${name.replace(/[^a-z0-9]+/g, "-").replace(/-$/, "")}-${label}`);
      }
      gatewayVariant = "hold";
      await go(view("foundation/readiness", CURRENT), loaded("Gateway status"));
      const g = await js(GATEWAY);
      claim(`${label}: gateway variant "loading" (request held) says it is loading and claims no contact`,
        g.text.includes("Loading the site's gateway contact.") && g.state === null && g.status === null && g.missing === NOT_AVAILABLE_GATEWAY, { state: g.state });
      await shot(`app-readiness-gateway-loading-${label}`);
    } finally {
      await release();
      await send("Fetch.disable");
    }
    await go(view("foundation/readiness", CURRENT), loaded("Readiness and commissioning evidence"));

    // --- keyboard: focus the Site model subtab, Enter, period carried -----------------------
    // Reach the subtab by keyboard: focus the element before it, then Tab (so :focus-visible applies).
    await js(`(() => { const all = [...document.querySelectorAll('a[href], button, select, input')];
      const i = all.findIndex(a => a.closest('nav.foundation-views') && a.textContent === 'Site model'); all[i - 1]?.focus(); })()`);
    await key("Tab", "Tab", 9);
    const focus = await js(`(() => { const a = document.activeElement; const cs = getComputedStyle(a);
      return { text: a.textContent, outline: cs.outlineStyle !== 'none' && cs.outlineWidth !== '0px', shadow: cs.boxShadow !== 'none' }; })()`);
    claim(`${label}: a Foundation subtab takes visible keyboard focus`, focus.text === "Site model" && (focus.outline || focus.shadow), focus);
    await key("Enter", "Enter", 13, "\r");
    await waitFor(loaded("Time-valid control configuration"));
    await sleep(300);
    const after = await js(`({ url: location.pathname + location.search, sel: ${SEL},
      current: document.querySelector('nav.foundation-views [aria-current="page"]')?.textContent })`);
    claim(`${label}: Enter on the subtab opens Site model at the same selected period`,
      after.url.includes("/foundation?") && after.sel?.value === CURRENT && after.current === "Site model", after);
    await key("Tab", "Tab", 9);
    const next = await js(`document.activeElement?.textContent`);
    claim(`${label}: Tab moves on to the next subtab`, next === "Single line diagram", { next });

    // --- owner follow-ups: tab headers, type scale and the rail, app vs mock computed style --
    const STYLE = `(() => { const cs = (sel) => { const e = document.querySelector(sel); if (!e) return null; const s = getComputedStyle(e);
        return { size: s.fontSize, weight: s.fontWeight, color: s.color, bg: s.backgroundColor }; };
      return { h1: cs('main h1, .canvas h1'), panel: cs('main .panel__heading, .panel .panel-head h2'),
        note: cs('main .panel__description, .panel .panel-head p'), td: cs('main td'), th: cs('main th'),
        tab: cs('.site-tabs:not(.site-subtabs) .site-tabs__link:not([aria-current]), .tabs:not(.subtabs) a:not(.active)'),
        tabOn: cs('.site-tabs:not(.site-subtabs) .site-tabs__link[aria-current="page"], .tabs:not(.subtabs) a.active'),
        sub: cs('.site-subtabs .site-tabs__link:not([aria-current]), .tabs.subtabs a:not(.active)'),
        rail: cs('.nav-rail__link:not([aria-current]), .rail-group a:not(.active)'), railOn: cs('.nav-rail__link[aria-current="page"], .rail a.active'),
        railIcons: document.querySelectorAll('.nav-rail__link .nav-rail__icon').length,
        railLinks: document.querySelectorAll('.nav-rail__link').length }; })()`;
    await go(view("foundation/sld", CURRENT), loaded("What each configured part is"));
    const app = await js(STYLE);
    await go(MOCK("sld"), `document.body && document.body.innerText.includes("What each part does")`);
    const mock = await js(STYLE);
    const same = (k, f) => app[k] !== null && mock[k] !== null && app[k][f] === mock[k][f];
    claim(`${label}: tab headers are neutral ink with only the current tab accented, as in the mock`,
      same("tab", "color") && same("tab", "size") && same("tabOn", "color") && app.tab.color !== app.tabOn.color && same("sub", "size"),
      { app: [app.tab, app.tabOn, app.sub], mock: [mock.tab, mock.tabOn, mock.sub] });
    claim(`${label}: page title, panel title, panel note and table type match the mock's sizes`,
      ["h1", "panel", "note", "td", "th"].every((k) => same(k, "size")),
      Object.fromEntries(["h1", "panel", "note", "td", "th"].map((k) => [k, [app[k]?.size, mock[k]?.size]])));
    if (width > 760) {
      claim(`${label}: the rail matches the mock's type, ink and active fill, with one icon per root`,
        same("rail", "size") && same("rail", "color") && same("railOn", "bg") && app.railIcons === app.railLinks && app.railLinks >= 2,
        { app: [app.rail, app.railOn, app.railIcons, app.railLinks], mock: [mock.rail, mock.railOn] });
    } else {
      await go(nowView("foundation"), loaded("Time-valid control configuration"));
      const narrowRail = await js(`({ icons: document.querySelectorAll('.nav-rail__link .nav-rail__icon').length,
        links: [...document.querySelectorAll('.nav-rail__link')].filter(a => { const r = a.getBoundingClientRect();
          return r.width > 0 && r.right <= document.documentElement.clientWidth + 1; }).length })`);
      claim(`${label}: every rail root and its icon stay visible at phone width (the mock hides its rail below 760px)`,
        narrowRail.icons === narrowRail.links && narrowRail.links >= 2, narrowRail);
      await layout(`${label}: rail at phone width`);
      await shot(`app-rail-${label}`);
    }

    // --- regression: the shared tab, type and rail changes on Dispatch, Finding, Evidence, Lab --
    const firstFinding = async () => {
      for (const from of ["/findings", `/sites/${SITE}/performance`]) {
        await go(`${BASE}${from}`, `!document.querySelector('[aria-busy="true"]') && document.querySelector('main h1')`);
        await sleep(1200);
        const href = await js(`[...document.querySelectorAll('main a[href*="/findings/"]')].map(a => a.getAttribute('href'))[0] ?? null`);
        if (href !== null) return href;
      }
      return null;
    };
    const finding = await firstFinding();
    for (const [name, path] of [["Findings index", "/findings"], ["Finding detail", finding],
      ["Performance › Dispatch", `/sites/${SITE}/performance`], ["Site Evidence", `/sites/${SITE}/evidence`],
      ["Simulator Lab", "/simulator-lab"], ["Lab runs", "/simulator-lab/runs"]]) {
      if (path === null) {
        // A precondition, not a pass: the v01a store holds no assessed Finding, so no detail exists to open.
        console.log(`NOT RUN  ${label}: regression ${name} - this store has no Finding (the Findings index is empty)`);
        continue;
      }
      const ok = await go(`${BASE}${path}`, `!document.querySelector('[aria-busy="true"]') && document.querySelector('main h1')`);
      await sleep(600);
      const seen = await js(`({ h1: document.querySelector('main h1')?.textContent ?? null,
        icons: document.querySelectorAll('.nav-rail__icon').length, links: document.querySelectorAll('.nav-rail__link').length })`);
      claim(`${label}: regression ${name} renders with its rail icons`, ok && !!seen.h1 && seen.icons === seen.links && seen.links >= 2, { path, ...seen });
      await layout(`${label}: regression ${name}`);
      await shot(`app-regression-${name.replace(/[^A-Za-z]+/g, "-").toLowerCase()}-${label}`);
    }
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
