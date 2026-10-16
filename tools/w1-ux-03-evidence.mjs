/**
 * W1-UX-03: app-vs-v6.9-mock evidence for the Evidence and Performance screens (`evidence`,
 * `evidence-analysis`, `dispatch`, `analysis`), at 1440 and 390. Sibling of tools/w1-ux-01-evidence.mjs;
 * from the installed Chrome over the DevTools Protocol (the tools/s601b-action-evidence.mjs pattern;
 * no dependency).
 *
 * Run against one walkthrough's served app at a time (its prepare + serve, then its frontend command):
 *   node tools/w1-ux-03-evidence.mjs <screenshot-dir> <mock-id>[:<case>]=<app-url> [...]
 * e.g. node tools/w1-ux-03-evidence.mjs %TEMP%\w1ux03 dispatch=http://localhost:5461/sites/KOBO-001/performance/dispatch?day=<day>
 * The mock is read from the same origin: <origin>/mockups/v69/index.html#/<mock-id>.
 * Environment: ASSETOPS_CDP_PORT (default 9471).
 *
 * Every claim is measured and printed; the run exits non-zero if any fails.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const OUT = process.argv[2];
const TARGETS = process.argv.slice(3).map((arg) => {
  const at = arg.indexOf("=");
  const [id, tag] = arg.slice(0, at).split(":");
  return { id, tag: tag ?? null, url: arg.slice(at + 1) };
});
if (!OUT || TARGETS.length === 0) {
  console.error("usage: node tools/w1-ux-03-evidence.mjs <out-dir> <mock-id>=<app-url> ...");
  process.exit(2);
}
// The measured region of each screen, and its closed disclosure's plain summary.
const CARD = {
  evidence: '[data-headline-card="evidence-conclusion"]',
  "evidence-analysis": "[data-claim-limit-section]",
  dispatch: '[data-headline-card="dispatch-story"]',
  analysis: "[data-dispatch-status]",
};
const SUMMARY = {
  evidence: "How this was worked out",
  "evidence-analysis": "Technical details: rule, versions and record references",
  dispatch: "How this was worked out",
  analysis: "Technical details: stored record, versions and references",
};
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9471);
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  ["desktop", 1440, 1000],
  ["narrow", 390, 900],
];
mkdirSync(OUT, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "assetops-w1ux03-cdp-"));
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
  await sleep(500);
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

/** Measurements of one migrated card: state line visible, disclosure closed, no overflow, keyboard reach. */
const measure = (card) =>
  js(`(() => {
    const c = document.querySelector('${card}');
    if (!c) return null;
    const box = (e) => { if (!e) return null; const r = e.getBoundingClientRect(); return { w: Math.round(r.width), h: Math.round(r.height), right: Math.round(r.right) }; };
    const d = document.documentElement;
    const details = c.querySelector('details[data-exact-references]') ?? c.querySelector('details');
    const inside = [...c.querySelectorAll('*')];
    const wide = inside.filter(e => e.getBoundingClientRect().right > d.clientWidth + 1 && !e.closest('details:not([open]) > :not(summary)'))
      .map(e => (e.className || e.tagName) + ':' + Math.round(e.getBoundingClientRect().right)).slice(0, 6);
    const focusable = [...c.querySelectorAll('a[href], summary, button, [tabindex]:not([tabindex="-1"])')].map(e => e.tagName + ':' + e.textContent.trim().slice(0, 40));
    return {
      label: c.querySelector('[data-product-status-label]')?.textContent ?? null,
      labelBox: box(c.querySelector('[data-product-status-label]')),
      scopeBox: box(c.querySelector('[data-product-status-scope]')),
      asOf: c.querySelector('[data-product-status-as-of]')?.textContent ?? null,
      asOfBox: box(c.querySelector('[data-product-status-as-of]')),
      disclosureOpen: details ? details.open : null,
      summary: details?.querySelector('summary')?.textContent ?? null,
      measured: inside.length, wide, scrollWidth: d.scrollWidth, clientWidth: d.clientWidth,
      focusable,
      visual: Boolean(c.querySelector('[data-value-bars], [data-step-strip], [data-period-strip], [data-dispatch-story]')),
      strip: c.querySelectorAll('[data-period-strip-row]').length,
    };
  })()`);

/** Tab from the top of the page until the card's disclosure summary takes focus. */
async function tabReaches(card) {
  await js("document.activeElement && document.activeElement.blur(); window.scrollTo(0, 0); true");
  for (let i = 0; i < 120; i += 1) {
    await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
    await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
    const hit = await js(`(() => { const a = document.activeElement; return Boolean(a && a.tagName === 'SUMMARY' && a.closest('${card}')); })()`);
    if (hit) return i + 1;
  }
  return 0;
}

try {
  ws = await connect();
  ws.addEventListener("message", (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id)(msg);
      pending.delete(msg.id);
    }
  });
  await send("Page.enable");
  await send("Runtime.enable");
  for (const { id: mockId, tag, url } of TARGETS) {
    const id = tag === null ? mockId : `${mockId}-${tag}`;
    const card = CARD[mockId];
    const origin = new URL(url).origin;
    for (const [label, width, height] of WIDTHS) {
      await size(width, height);
      const ok = await go(url, `document.querySelector('${card} [data-product-status-label]')`);
      claim(`${id} ${label}: the migrated card renders at ${url}`, ok);
      const m = await measure(card);
      if (m === null) {
        claim(`${id} ${label}: card measured`, false);
        continue;
      }
      const shown = (b) => b !== null && b.w > 0 && b.h > 0;
      claim(`${id} ${label}: state, scope and as-of are drawn with the disclosure closed`, m.disclosureOpen === false && shown(m.labelBox) && shown(m.scopeBox) && shown(m.asOfBox) && /^As of /.test(m.asOf ?? ""), { label: m.label, asOf: m.asOf });
      claim(`${id} ${label}: the closed summary is plain text`, m.summary === SUMMARY[mockId], m.summary);
      claim(`${id} ${label}: no sideways scroll from the card (measured ${m.measured} elements)`, m.measured > 0 && m.scrollWidth <= m.clientWidth && m.wide.length === 0, { scrollWidth: m.scrollWidth, clientWidth: m.clientWidth, wide: m.wide });
      claim(`${id} ${label}: the screen has a small visual with readable text`, m.visual, { visual: m.visual, stripRows: m.strip });
      const tabs = await tabReaches(card);
      claim(`${id} ${label}: keyboard Tab reaches the disclosure summary`, tabs > 0, { tabs, focusable: m.focusable });
      const here = new URL(await js("location.href"));
      const asked = new URL(url);
      const kept = here.pathname === asked.pathname && [...asked.searchParams].every(([k, v]) => here.searchParams.get(k) === v);
      claim(`${id} ${label}: the address keeps its path and selectors after load`, kept, here.pathname + here.search);
      await shot(`app-${id}-${label}`);
      if (tag === null || TARGETS.find((t) => t.id === mockId) === TARGETS.find((t) => t.url === url)) {
        const mockOk = await go(`${origin}/mockups/v69/index.html#/${mockId}`, "document.querySelector('h1, h2')");
        claim(`${mockId} ${label}: mock #/${mockId} renders`, mockOk);
        await shot(`mock-${mockId}-${label}`);
      }
    }
  }
} catch (error) {
  claim("evidence run completed", false, String(error));
} finally {
  try {
    ws?.close();
  } catch {
    /* closing */
  }
  chrome.kill();
}
const failed = results.filter((r) => !r.ok);
console.log(`${results.length - failed.length}/${results.length} claims passed; screenshots in ${OUT}`);
process.exit(failed.length === 0 ? 0 : 1);
