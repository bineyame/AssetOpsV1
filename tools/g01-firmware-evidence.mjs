/**
 * SUPERSEDED for these screens by tools/g02-gap-evidence.mjs: this tool asserts pre-G-02 copy and will fail on
 * the current tree. A failure here is not a regression; it is kept as the recorded historical evidence tool.
 *
 * G-01: browser layout evidence for the catalogued Readiness gateway firmware missing state
 * (`G-readiness-gateway-firmware`, placement `readiness.gateway.firmware`) at 1440x1000 and 390x900,
 * from the installed Chrome over the DevTools Protocol (same no-dependency approach as
 * tools/v01a-foundation-evidence.mjs).
 *
 * Run against private walkthrough servers (tools/v01a_foundation_walkthrough.py with private
 * --db/--empty-db/--work-name, populated API + Vite on private ports):
 *   node tools/g01-firmware-evidence.mjs http://localhost:5398 <screenshot-dir>
 *
 * Gateway-health response shapes. The stored KOBO-001 copy answers `/gateway-health` with one
 * gateway whose contact is STALE; shape "stale" is that real read. The other shapes are produced by
 * intercepting that one request in the browser (DevTools `Fetch`) and answering with a variant of
 * the real body: CURRENT (last contact = read time), UNKNOWN (no diagnostic), a 503 and a 404.
 * Substituted states are response substitutions proving UI rendering only; they are not stored
 * states and claim nothing about the gateway itself.
 *
 * Every claim is measured and printed; the run exits non-zero if any fails. Set-based claims print
 * their size, so a claim over an empty set is visible.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const BASE = process.argv[2] ?? "http://localhost:5398";
const OUT = process.argv[3] ?? join(tmpdir(), "g01-firmware-evidence");
const SITE = "KOBO-001";
const PORT = 9398;
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  [1440, 1000],
  [390, 900],
];
const GAP_ID = "G-readiness-gateway-firmware";
const PLACEMENT = "readiness.gateway.firmware";
const FIRMWARE_TEXT = "Firmware not available yet: no reviewed source reports what firmware a gateway has installed.";
const NOT_AVAILABLE_GATEWAY =
  "Not available yet: uptime trend, expected-versus-delivered completeness and signal strength. No reviewed source for these fields.";
const FIRMWARE_VALUE = /firmware v\d|firmware:\s*\S|version \d/i;
const ROUTE = `${BASE}/sites/${SITE}/foundation/readiness`;

mkdirSync(OUT, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "assetops-g01-cdp-"));
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
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 600 });
}
const PANEL = `[...document.querySelectorAll('h2')].find(h => h.textContent.trim() === 'Gateway status')?.closest('section')`;
const READY = `!document.querySelector('[aria-busy="true"]') && (${PANEL})?.querySelector('[data-gateway-panel-state]')`;
async function load() {
  await send("Page.navigate", { url: ROUTE });
  const ok = await waitFor(READY);
  await sleep(400);
  return ok;
}

/** Everything the claims need, measured in one evaluation. */
const MEASURE = `(() => { const p = ${PANEL}; const fw = [...document.querySelectorAll('[data-gap-id="${GAP_ID}"]')];
  const f = fw[0] ?? null; const r = f?.getBoundingClientRect(); const cs = f ? getComputedStyle(f) : null;
  const pr = p?.getBoundingClientRect(); const e = p?.querySelector('[data-gateway-status]');
  return { panel: !!p, state: p?.querySelector('[data-gateway-panel-state]')?.dataset.gatewayPanelState ?? null,
    status: e?.dataset.gatewayStatus ?? null, count: fw.length,
    gapId: f?.getAttribute('data-gap-id') ?? null, placement: f?.getAttribute('data-gap-placement') ?? null,
    gapStatus: f?.getAttribute('data-gap-status') ?? null, cls: f?.className ?? null, text: f?.textContent ?? null,
    outer: f?.outerHTML ?? null, inPanel: !!(f && p && p.contains(f)),
    box: r ? { left: Math.round(r.left), right: Math.round(r.right), top: Math.round(r.top), width: Math.round(r.width), height: Math.round(r.height) } : null,
    display: cs?.display ?? null, visibility: cs?.visibility ?? null, visible: f ? f.checkVisibility({ visibilityProperty: true, opacityProperty: true }) : false,
    panelBox: pr ? { left: Math.round(pr.left), right: Math.round(pr.right), top: Math.round(pr.top), bottom: Math.round(pr.bottom) } : null,
    innerWidth: window.innerWidth, scrollWidth: document.documentElement.scrollWidth,
    gapIds: [...new Set([...document.querySelectorAll('[data-gap-id]')].map(x => x.getAttribute('data-gap-id')))].sort(),
    idInText: document.body.innerText.includes('${GAP_ID}'),
    missing: p?.querySelector('[data-not-available-yet="gateway"]')?.textContent ?? null,
    panelText: p?.innerText ?? '' }; })()`;

async function shot(name) {
  // Clip to the gateway panel; the page is first grown so the panel is fully laid out on screen.
  const tall = await js(`Math.max(document.documentElement.scrollHeight,
    ...[...document.querySelectorAll('*')].filter(e => e.scrollHeight > e.clientHeight + 1 && getComputedStyle(e).overflowY !== 'visible')
      .map(e => e.scrollHeight + e.getBoundingClientRect().top))`);
  await send("Emulation.setDeviceMetricsOverride", { width: viewport[0], height: Math.min(Math.ceil(tall), 7000), deviceScaleFactor: 1, mobile: viewport[0] < 600 });
  await sleep(300);
  const b = await js(`(() => { const r = (${PANEL})?.getBoundingClientRect(); return r ? { x: r.left, y: r.top + window.scrollY, width: r.width, height: r.height } : null; })()`);
  const params = { format: "png", captureBeyondViewport: true };
  if (b && b.width > 0 && b.height > 0) {
    params.clip = { x: Math.max(0, b.x - 8), y: Math.max(0, b.y - 8), width: Math.min(viewport[0], b.width + 16), height: b.height + 16, scale: 1 };
  }
  const r = await send("Page.captureScreenshot", params);
  const file = join(OUT, `${name}.png`);
  writeFileSync(file, Buffer.from(r.data, "base64"));
  await size(viewport[0], viewport[1]);
  return file;
}
let viewport = [1440, 1000];

let gatewayVariant = null; // null: pass the real response through
listeners.set("Fetch.requestPaused", (p) => {
  const v = gatewayVariant;
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

function check(label, m, expectState, expectStatus) {
  claim(`${label}: gateway panel state is "${expectState}" and entry status is ${expectStatus ?? "absent"}`,
    m.panel && m.state === expectState && m.status === expectStatus, { state: m.state, status: m.status });
  claim(`${label}: the firmware element exists exactly once`, m.count === 1, { count: m.count });
  claim(`${label}: data-gap-id / placement / status exact`,
    m.gapId === GAP_ID && m.placement === PLACEMENT && m.gapStatus === "open", { gapId: m.gapId, placement: m.placement, status: m.gapStatus });
  claim(`${label}: firmware text exact`, m.text === FIRMWARE_TEXT && m.cls === "not-available-yet", { text: m.text, cls: m.cls });
  const pb = m.panelBox;
  claim(`${label}: firmware element rendered visibly inside the panel`,
    m.visible && m.inPanel && m.display !== "none" && m.visibility !== "hidden" && m.box?.width > 0 && m.box?.height > 0
      && pb !== null && m.box.left >= pb.left - 1 && m.box.right <= pb.right + 1 && m.box.top >= pb.top - 1,
    { box: m.box, panelBox: pb, display: m.display });
  claim(`${label}: firmware right edge <= innerWidth and no horizontal page overflow`,
    m.box !== null && m.box.right <= m.innerWidth && m.scrollWidth <= m.innerWidth,
    { right: m.box?.right, innerWidth: m.innerWidth, scrollWidth: m.scrollWidth });
  claim(`${label}: the page's data-gap-id set is exactly ["${GAP_ID}"]`,
    m.gapIds.length === 1 && m.gapIds[0] === GAP_ID, { size: m.gapIds.length, set: m.gapIds });
  claim(`${label}: the gap ID does not appear in the visible text`, !m.idInText, { idInText: m.idInText });
  claim(`${label}: no firmware value appears in the panel text`, !FIRMWARE_VALUE.test(m.panelText), { match: m.panelText.match(FIRMWARE_VALUE)?.[0] ?? null });
  claim(`${label}: the gateway Not-available-yet line reads the narrowed text`, m.missing === NOT_AVAILABLE_GATEWAY, { missing: m.missing });
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
  const real = await (await fetch(`${BASE}/api/sites/${SITE}/gateway-health`)).json();
  claim("precondition: the stored copy's gateway-health read answers with at least one gateway",
    Array.isArray(real.gateways) && real.gateways.length >= 1,
    { read_at: real.read_at, gateways: real.gateways?.map((g) => [g.gateway_external_id, g.registration, g.status]) });
  const g0 = real.gateways?.[0] ?? {};
  const shapes = [
    ["stale", null, "loaded", "STALE"],
    ["current", { code: 200, body: { ...real, gateways: [{ ...g0, status: "CURRENT", last_server_contact: real.read_at }] } }, "loaded", "CURRENT"],
    ["unknown", { code: 200, body: { ...real, gateways: [{ ...g0, status: "UNKNOWN", last_server_contact: null, diagnostic_id: null }] } }, "loaded", "UNKNOWN"],
    ["503", { code: 503, body: { detail: "unavailable" } }, "unavailable", null],
    ["404", { code: 404, body: { detail: "not found" } }, "unavailable", null],
  ];
  await send("Fetch.enable", { patterns: [{ urlPattern: "*gateway-health*" }] });
  try {
    for (const [width, height] of WIDTHS) {
      viewport = [width, height];
      await size(width, height);
      for (const [shape, variant, state, status] of shapes) {
        const label = `${width}x${height} ${shape}`;
        gatewayVariant = variant;
        const ready = await load();
        claim(`${label}: the Readiness gateway panel loaded`, ready);
        const m = await js(MEASURE);
        check(label, m, state, status);
        if (shape === "stale") {
          await send("Page.reload", { ignoreCache: true });
          await waitFor(READY);
          await sleep(400);
          const again = await js(MEASURE);
          claim(`${label}: firmware element outerHTML identical after reload`, m.outer !== null && again.outer === m.outer, { outer: again.outer });
        }
        const file = await shot(`g01-firmware-${width}-${shape}`);
        console.log(`      screenshot ${file}`);
      }
    }
  } finally {
    gatewayVariant = null;
    await send("Fetch.disable").catch(() => {});
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
