/**
 * S7-01b: app-vs-v6.9-mock evidence for Site Health (`health:2#a`, mock #/health) and the battery boundary
 * (`asset:3#a`, mock #/asset) at 1440 and 390, from the installed Chrome over the DevTools Protocol
 * (same approach as tools/s601b-action-evidence.mjs; no dependency).
 *
 * Run against the walkthrough servers (tools/s701_health_walkthrough.py prepare + serve, frontend on 5447), right
 * after `deliver`:
 *   node tools/s701-health-evidence.mjs http://127.0.0.1:5447 <screenshot-dir>
 * Environment:
 *   ASSETOPS_S701_WORK   walkthrough work folder holding walkthrough.json (default var/s701_owner1)
 *   ASSETOPS_CDP_PORT    Chrome DevTools port (default 9447)
 *
 * Every claim is measured and printed; the run exits non-zero if any fails. It also writes
 * `<screenshot-dir>/comparison.md` (mock headings beside the app's per screen and width).
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const BASE = process.argv[2] ?? "http://127.0.0.1:5447";
const OUT = process.argv[3] ?? join(tmpdir(), "s701-health-evidence");
const SITE = "KOBO-001";
const OTHER = "KOBO-002";
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9447);
const WORK = process.env.ASSETOPS_S701_WORK ?? resolve("var", "s701_owner1");
const IDS = JSON.parse(readFileSync(join(WORK, "walkthrough.json"), "utf8"));
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  ["desktop", 1440, 1000],
  ["narrow", 390, 900],
];
mkdirSync(OUT, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "assetops-s701-cdp-"));
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
  return new Promise((res, rej) => {
    const timer = setTimeout(() => rej(new Error(`timeout ${method}`)), 60000);
    pending.set(id, (msg) => {
      clearTimeout(timer);
      msg.error ? rej(new Error(JSON.stringify(msg.error))) : res(msg.result);
    });
    ws.send(JSON.stringify({ id, method, params }));
  });
}
async function js(expression) {
  const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
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
async function reload(ready) {
  await send("Page.reload");
  await sleep(300);
  const ok = await waitFor(ready);
  await sleep(300);
  return ok;
}
async function shot(name) {
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
/** Sideways page scroll, and the elements (outside a table's own scroller) that poke past the viewport. */
const overflow = () =>
  js(`(() => { const d = document.documentElement; const main = document.querySelector('main');
    const all = main ? [...main.querySelectorAll('*')] : [];
    return { scrollWidth: d.scrollWidth, clientWidth: d.clientWidth, measured: all.length,
      wide: all.filter(e => e.getBoundingClientRect().right > d.clientWidth + 1 && !e.closest('.data-table__scroll, .data-table-scroll, [data-scroll]')
        && ![...e.children].some(c => c.getBoundingClientRect().right > d.clientWidth + 1))
        .map(e => (e.className || e.tagName) + ':' + Math.round(e.getBoundingClientRect().right)).slice(0, 6) }; })()`);
const headings = () =>
  js(`[...document.querySelectorAll('main h1, main h2, main h3, .panel h2, .panel h3')].map(h => h.textContent.trim()).filter(Boolean)`);
const mockHeadings = () =>
  js(`[...document.querySelectorAll('h1, h2, h3, .panel-title, .panel h3, .metric .label, .metric-label')].map(h => h.textContent.trim()).filter(Boolean).slice(0, 24)`);
const url = () => js("location.pathname + location.search");

const comparison = [];

async function noOverflow(label, what) {
  const o = await overflow();
  claim(`${label} ${what}: no sideways page scroll (measured ${o.measured} elements)`, o.measured > 0 && o.scrollWidth <= o.clientWidth && o.wide.length === 0, o);
}

async function mockScreen(label, id, ready) {
  const ok = await go(`${BASE}/mockups/v69/index.html#/${id}`, ready);
  const h = await mockHeadings();
  claim(`${label} mock #/${id} renders`, ok && h.length > 0, h.slice(0, 6));
  await shot(`mock-${id}-${label}`);
  return h;
}


async function suite(label) {
  const site = `${BASE}/sites/${SITE}`;
  // --- health:2#a ---
  const mockHealth = await mockScreen(label, "health", "document.body.innerText.includes('Data sources')");
  const ready = "document.querySelector('[data-health-summary]') && !document.body.innerText.includes('Loading the site')";
  await go(`${site}/health`, ready);
  const h = await js(`({ summary: document.querySelector('[data-health-summary]')?.innerText,
    rows: Object.fromEntries([...document.querySelectorAll('[data-health-gateway]')].map(r => [r.dataset.healthGateway,
      { contact: r.dataset.healthContact, reg: r.dataset.healthRegistration, text: r.innerText.replace(/\\s+/g, ' ') }])),
    tab: document.querySelector('.site-tabs a[aria-current="page"]')?.textContent,
    technicalOpen: document.querySelector('[data-disclosure="site-health-technical"]')?.open,
    text: document.querySelector('main').innerText })`);
  claim(`${label} health: summary labelled Gateway contact with enabled count and disabled not counted`,
    /Gateway contact:/.test(h.summary ?? "") && /8 enabled gateways/.test(h.summary ?? "") &&
      /1 disabled, not counted/.test(h.summary ?? "") && h.tab === "Health", h.summary);
  const r = h.rows;
  const want = {
    "s7-current": "CURRENT", "s7-delayed-old": "CURRENT", "s7-queue-growth": "CURRENT", "s7-clock-offset": "CURRENT",
    "s7-disk-stop": "CURRENT", "s7-disk-recovery": "CURRENT", "s7-stale-cadence": "STALE", "s7-never-received": "UNKNOWN",
  };
  const got = Object.fromEntries(Object.keys(want).map((k) => [k, r[k]?.contact]));
  claim(`${label} health: each case's contact after deliver (stale-cadence STALE, never-received UNKNOWN)`,
    Object.entries(want).every(([k, v]) => got[k] === v), got);
  claim(`${label} health: disabled import gateway listed with Disabled`,
    r["edge-kobo-001"]?.reg === "DISABLED" && /Disabled/.test(r["edge-kobo-001"]?.text ?? ""), r["edge-kobo-001"]);
  claim(`${label} health: delayed case reads Old facts beside current contact`,
    /Old: observed 6 h/.test(r["s7-delayed-old"]?.text ?? ""), r["s7-delayed-old"]?.text);
  claim(`${label} health: untrusted clock shows Unknown age with the clock reason`,
    /Unknown age: the gateway.s clock is off by 95 s/.test(r["s7-clock-offset"]?.text ?? ""), r["s7-clock-offset"]?.text);
  claim(`${label} health: no signed age, no "Site health"/projection wording, details closed`,
    !/-\d+\s?(s|min|h|d)\b/.test(h.text) && !/site health|projection/i.test(h.text) && h.technicalOpen === false, null);
  await noOverflow(label, "health KOBO-001");
  comparison.push(["health (KOBO-001)", label, mockHealth, await headings()]);
  await shot(`app-health-kobo001-${label}`);
  const again = await reload(ready);
  claim(`${label} health: reload keeps the address and the read`, again && (await url()) === `/sites/${SITE}/health`, await url());

  // exact gateway link by keyboard, reload, Back
  const gw = IDS.gateways["s7-clock-offset"];
  await js(`document.querySelector('[data-health-open="s7-clock-offset"]').focus()`);
  const focused = await js(`document.activeElement?.dataset?.healthOpen`);
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
  const sel = await waitFor("document.querySelector('[data-health-selected-diagnostic]')");
  claim(`${label} health: keyboard Enter on a gateway's Details opens its exact address`,
    focused === "s7-clock-offset" && sel && (await url()) === `/sites/${SITE}/health?gateway=${gw}`, await url());
  const diag = await js(`document.querySelector('[data-health-selected-diagnostic]')?.dataset.healthSelectedDiagnostic`);
  await reload("document.querySelector('[data-health-selected-diagnostic]')");
  const diag2 = await js(`document.querySelector('[data-health-selected-diagnostic]')?.dataset.healthSelectedDiagnostic`);
  claim(`${label} health: the selected gateway survives reload with the same report ID`, Boolean(diag) && diag === diag2, diag2);
  await js("history.back()");
  await waitFor("!document.querySelector('[data-health-selected-diagnostic]') && document.querySelector('[data-health-summary]')");
  claim(`${label} health: Back returns to the unselected page`, (await url()) === `/sites/${SITE}/health`, await url());

  // battery, by the Health link
  const battery = await js(`document.querySelector('[data-health-battery] a')?.getAttribute('href')`);
  await go(`${BASE}${battery}`, "document.querySelector('[data-battery-condition]')");
  const b = await js(`({ cond: document.querySelector('[data-battery-condition]')?.dataset.batteryCondition,
    missing: [...document.querySelectorAll('[data-battery-missing]')].map(e => e.dataset.batteryMissing),
    rating: document.querySelector('[data-battery-metric="rating"]')?.innerText })`);
  claim(`${label} battery KOBO-001: condition Unknown with three named missing inputs and the declared rating labelled`,
    b.cond === "UNKNOWN" && b.missing.length === 3 && /200 kWh/.test(b.rating ?? "") && /not a measurement/.test(b.rating ?? ""), b);
  const mockAsset = await mockScreen(label, "asset", "document.body.innerText.includes('Condition evidence')");
  await go(`${BASE}${battery}`, "document.querySelector('[data-battery-condition]')");
  await noOverflow(label, "battery KOBO-001");
  comparison.push(["asset (KOBO-001 battery)", label, mockAsset, await headings()]);
  await shot(`app-battery-kobo001-${label}`);

  // second Site
  await go(`${BASE}/sites/${OTHER}/health`, ready);
  const o = await js(`({ reason: document.querySelector('[data-health-summary]')?.dataset.healthSummaryReason,
    text: document.querySelector('[data-health-summary]')?.innerText,
    battery: document.querySelector('[data-health-battery]')?.dataset.healthBattery })`);
  claim(`${label} ${OTHER} health: no enabled gateway stated, no healthy zero; battery not configured`,
    o.reason === "NO_ENABLED_GATEWAY" && !/0 current|all current/.test(o.text ?? "") && o.battery === "NOT_CONFIGURED", o);
  await noOverflow(label, `health ${OTHER}`);
  comparison.push([`health (${OTHER})`, label, mockHealth, await headings()]);
  await shot(`app-health-kobo002-${label}`);
  await go(`${BASE}/sites/${OTHER}/assets`, "document.querySelector('[data-battery-configuration]')");
  const nc = await js(`({ conf: document.querySelector('[data-battery-configuration]')?.dataset.batteryConfiguration,
    links: document.querySelectorAll('[data-battery-link]').length })`);
  claim(`${label} ${OTHER} battery entry: NOT_CONFIGURED with no asset link`, nc.conf === "NOT_CONFIGURED" && nc.links === 0, nc);
  await noOverflow(label, `battery entry ${OTHER}`);
  await shot(`app-battery-kobo002-${label}`);
  await go(`${BASE}/sites/${OTHER}/assets/${battery.split("/").pop()}`, "document.querySelector('[data-health-read=refused]')");
  const rf = await js(`({ http: document.querySelector('[data-health-read=refused]')?.dataset.healthHttp,
    row: !!document.querySelector('[data-battery-condition]') })`);
  claim(`${label} ${OTHER}: KOBO-001's battery ID is refused (404), no condition row`, rf.http === "404" && !rf.row, rf);
}

function comparisonMarkdown() {
  const lines = ["# S7-01b app vs v6.9 mock (headings as rendered)", "", "| Screen | Width | Mock headings | App headings |", "| --- | --- | --- | --- |"];
  for (const [screen, width, mock, app] of comparison) {
    const cell = (list) => list.map((x) => x.replace(/\|/g, "/")).join(" · ");
    lines.push(`| ${screen} | ${width} | ${cell(mock)} | ${cell(app)} |`);
  }
  return lines.join("\n") + "\n";
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
    await size(width, height);
    await suite(label);
  }
  writeFileSync(join(OUT, "comparison.md"), comparisonMarkdown());
  const failed = results.filter((r) => !r.ok);
  console.log(`\n${results.length - failed.length}/${results.length} claims passed; screenshots and comparison.md in ${OUT}`);
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
