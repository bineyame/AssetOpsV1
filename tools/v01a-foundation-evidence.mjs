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
      sub: document.querySelector('.panel__description')?.textContent })`);
    claim(
      `${label}: app /sites lists the stored Site under "Site inventory" with its sub-line`,
      sites.h2.includes("Site inventory") && sites.rows.length === 1 && /Kobo/i.test(sites.rows[0]) && /Mode is provenance/.test(sites.sub ?? ""),
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
        /in effect now/i.test(n.sel?.label ?? "") && /configuration in effect now/i.test(n.text) && !/Scheduled period/i.test(n.text), n.sel);
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
