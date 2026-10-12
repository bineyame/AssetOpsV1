/**
 * V-01a: app-vs-mock evidence for Sites, Foundation (Site model), Readiness and the single line
 * diagram (`sites:1`, `foundation:1-3`, `readiness:1`, `sld:1-2`), with layout measurements,
 * keyboard interaction, period selection and reload checks, from the installed Chrome over the
 * DevTools Protocol (same approach as tools/s3-dispatch-evidence.mjs; no dependency).
 *
 * Run against the walkthrough servers (tools/v01a_foundation_walkthrough.py prepare + serve,
 * populated frontend on 5360, empty-store frontend on 5361):
 *   node tools/v01a-foundation-evidence.mjs http://localhost:5360 <screenshot-dir> http://localhost:5361
 *
 * Every claim is measured and printed; the run exits non-zero if any fails. Set-based claims
 * report their size, so a claim over an empty set is visible.
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
const PARTS = `Object.fromEntries([...document.querySelectorAll('[data-sld-part]')].map(r => [r.dataset.sldPart,
  [...r.querySelectorAll('[data-part-channel="bound"] code')].map(c => c.textContent).sort().join('|')]))`;
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
      setup: document.querySelectorAll('main details.site-setup').length })`);
    claim(
      `${label}: app /sites lists the stored Site compactly (Site, Type, Mode, Setup details) with the analysis-absent note`,
      sites.h2.includes("Site inventory") && sites.rows.length === 1 && /Kobo/i.test(sites.rows[0])
        && JSON.stringify(sites.columns) === JSON.stringify(["Site", "Type", "Mode", "Setup details", "Actions"])
        && /not available in this directory/.test(sites.note ?? "") && sites.setup === 1,
      sites,
    );
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
      ["sld", "foundation/sld", "What each configured part is"], ["readiness", "foundation/readiness", "Role coverage"]]) {
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
    await layout(`${label}: Site model`);
    await shot(`app-foundation-scheduled-${label}`);
    await go(view("foundation", NONE), loaded("No stored version for this period"));
    claim(`${label}: a period before any stored version is stated, not filled with current data`,
      await js(`${H2}.includes("No stored version for this period") && !document.body.innerText.includes("Configured topology")`));
    await layout(`${label}: Site model (no stored version)`);
    await shot(`app-foundation-missing-${label}`);

    // --- sld:1-2 -----------------------------------------------------------------------------
    await go(view("foundation/sld", CURRENT), loaded("What each configured part is"));
    const sld = await js(`({ h2: ${H2}, parts: ${PARTS},
      unchanneled: [...document.querySelectorAll('[data-sld-part]')].filter(r => r.innerText.includes('No channel declared')).length,
      svg: !!document.querySelector('main svg') })`);
    const boundParts = Object.values(sld.parts).filter((v) => v !== "").length;
    claim(
      `${label}: SLD shows the drawing and the parts table with bound channels per part`,
      sld.svg && sld.h2.some((h) => h.includes("configured single line diagram")) && boundParts >= 5 && sld.unchanneled >= 1,
      { boundParts, parts: Object.keys(sld.parts).length, unchanneled: sld.unchanneled },
    );
    await layout(`${label}: SLD`);
    await shot(`app-sld-scheduled-${label}`);
    // Devices caption (backlog carry): open the device disclosure and read it.
    const caption = await js(`(() => { const d = [...document.querySelectorAll('details')].find(x => x.innerText.includes('Devices and the binding set'));
      if (!d) return null; d.open = true;
      return [...d.querySelectorAll('caption, p')].map(c => c.textContent).find(t => t.includes('devices this site')) ?? null; })()`);
    claim(`${label}: devices caption is consistent (not assessed here; no "none has reported")`,
      caption !== null && /reporting is not assessed here/.test(caption) && !/none has reported/.test(caption), { caption });

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
      panel: document.querySelector('[data-selected-part]')?.getAttribute('data-selected-part') })`);
    claim(`${label}: a drawn part takes visible keyboard focus and Enter chooses it by component ID`,
      ring.focused === "battery" && ring.stroke !== "none" && picked.url.includes(`at=${encodeURIComponent(CURRENT)}`)
        && picked.url.includes("component=battery") && picked.pressed === "true" && picked.panel === "battery", { ring, picked });
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
    await go(view("foundation/readiness", CURRENT) + "&component=battery", loaded("Role coverage"));
    const kept = await js(`document.querySelector('[data-selected-part]')?.getAttribute('data-selected-part')`);
    claim(`${label}: the chosen part survives reload and the Readiness view`, afterReload === "battery" && kept === "battery", { afterReload, kept });
    await go(view("foundation/sld", CURRENT) + "&component=no-such-part", loaded("What each configured part is"));
    await waitFor(`!location.search.includes('component=')`);
    await sleep(300);
    const missing = await js(`({ url: location.pathname + location.search, notice: document.querySelector('[data-selected-part-missing]')?.textContent ?? null,
      chosen: document.querySelectorAll('[data-sld-region] [data-selected]').length })`);
    claim(`${label}: an address naming a part this period does not declare clears it and says so`,
      /Selected part is not in this Foundation period/.test(missing.notice ?? "") && !missing.url.includes("component=") && missing.chosen === 0, missing);
    await shot(`app-sld-missing-part-${label}`);

    // --- readiness:1 -------------------------------------------------------------------------
    await go(view("foundation/readiness", CURRENT), loaded("Role coverage"));
    const ready = await js(`({ h2: ${H2}, state: document.querySelector('[data-readiness-state]')?.dataset.readinessState,
      text: document.querySelector('main').innerText })`);
    claim(`${label}: Readiness shows configuration readiness, role coverage and bindings`,
      ["Configuration readiness", "Role coverage", "Signal bindings"].every((h) => ready.h2.includes(h)) && !!ready.state,
      { h2: ready.h2, state: ready.state });
    const wording = ["Configuration readiness is distinct from claim readiness", "operational status is not assessed here",
      "Whether any channel is reporting is not assessed here"];
    const lower = ready.text.toLowerCase();
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
      await go(`${BASE}/findings`, `!document.querySelector('[aria-busy="true"]') && document.querySelector('main h1')`);
      await sleep(600);
      return js(`[...document.querySelectorAll('main a[href^="/findings/"]')].map(a => a.getAttribute('href'))[0] ?? null`);
    };
    const finding = await firstFinding();
    for (const [name, path] of [["Findings index", "/findings"], ["Finding detail", finding],
      ["Performance › Dispatch", `/sites/${SITE}/performance`], ["Site Evidence", `/sites/${SITE}/evidence`],
      ["Simulator Lab", "/simulator-lab"], ["Lab runs", "/simulator-lab/runs"]]) {
      if (path === null) {
        claim(`${label}: regression ${name} reachable`, false, { reason: "no Finding link on /findings" });
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
