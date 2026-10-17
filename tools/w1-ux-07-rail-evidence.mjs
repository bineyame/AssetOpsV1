/**
 * W1-UX-07 (D-2026-10-17-w1-rail): browser evidence for the full v6.9 operator rail, beside the mock rail,
 * at 1440 and 390 px, from the installed Chrome over the DevTools Protocol (the tools/w1-ux-05-evidence.mjs
 * harness; widths enforced by tools/evidence-checks.mjs).
 *
 *   node tools/w1-ux-07-rail-evidence.mjs <screenshot-dir> <gate:on|off> <app-url> [<app-url> ...]
 * e.g. node tools/w1-ux-07-rail-evidence.mjs %TEMP%w1ux07 on http://localhost:5470/sites
 * The mock rail is read from the same origin: <origin>/mockups/v69/index.html#/sites.
 * Environment: ASSETOPS_CDP_PORT (default 9471).
 *
 * Claims per app page and width: the six groups and eleven roots in order; exactly two rail links (Sites,
 * Findings); nine unavailable rows, each with its label and visible status inside the row and inside the
 * viewport, readable contrast, no pointer, never focused by Tab; the keyboard order reaches the live links
 * (and the Lab footer link only with the gate on); the WORKSPACE footer present exactly when the gate is on;
 * no horizontal page overflow. Every claim is printed; the run exits non-zero if any fails.
 */
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { spawn } from "node:child_process";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { widthGuard } from "./evidence-checks.mjs";

const OUT = process.argv[2];
const GATE = process.argv[3];
const URLS = process.argv.slice(4);
if (!OUT || !["on", "off"].includes(GATE) || URLS.length === 0) {
  console.error("usage: node tools/w1-ux-07-rail-evidence.mjs <out-dir> <on|off> <app-url> ...");
  process.exit(2);
}
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9471);
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  ["desktop", 1440, 1000],
  ["narrow", 390, 900],
];
mkdirSync(OUT, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "assetops-w1ux07-cdp-"));
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
  await requireWidth(viewport[0], viewport[1], `loaded ${url}`);
  return ok;
}
async function shot(name) {
  const tall = await js(`Math.max(document.documentElement.scrollHeight,
    ...[...document.querySelectorAll('*')].filter(e => e.scrollHeight > e.clientHeight + 1 && getComputedStyle(e).overflowY !== 'visible')
      .map(e => e.scrollHeight + e.getBoundingClientRect().top))`);
  const h = Math.min(Math.ceil(tall), 7000);
  await send("Emulation.setDeviceMetricsOverride", { width: viewport[0], height: h, deviceScaleFactor: 1, mobile: viewport[0] < 600 });
  await sleep(300);
  await requireWidth(viewport[0], null, `capture ${name}`, { record: false });
  const r = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(join(OUT, `${name}.png`), Buffer.from(r.data, "base64"));
  await size(viewport[0], viewport[1]);
}


const GROUPS = ["OPERATIONS", "INTELLIGENCE", "WORK", "ASSURANCE", "BUSINESS", "ADMIN"];
const ROOTS = ["Portfolio", "Sites", "Assets", "Findings", "Actions", "Incidents", "Maintenance", "Operational records", "Evidence", "Financials", "Settings"];
const LIVE = [["Sites", "/sites"], ["Findings", "/findings"]];

const measureRail = () =>
  js(`(() => {
    const nav = document.querySelector('nav[aria-label="Operator routes"]');
    if (!nav) return null;
    const lum = (rgb) => { const [r, g, b] = rgb.match(/[0-9.]+/g).slice(0, 3).map(Number).map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
    const side = nav.parentElement;
    const bg = getComputedStyle(side).backgroundColor;
    const contrast = (fg) => { const a = lum(fg), b = lum(bg); return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05); };
    const vw = document.documentElement.clientWidth;
    const rows = [...nav.querySelectorAll('li.nav-rail__unavailable')].map((li) => {
      const r = li.getBoundingClientRect();
      const label = li.querySelector('.nav-rail__label'), status = li.querySelector('.nav-rail__status');
      const lr = label.getBoundingClientRect(), sr = status.getBoundingClientRect();
      const inside = (x) => x.left >= r.left - 0.5 && x.right <= r.right + 0.5 && x.top >= r.top - 0.5 && x.bottom <= r.bottom + 0.5;
      return { label: label.textContent, status: status.textContent, visible: sr.width > 0 && sr.height > 0 && getComputedStyle(status).visibility === 'visible',
        together: inside(lr) && inside(sr), inViewport: r.left >= 0 && r.right <= vw + 0.5,
        cursor: getComputedStyle(li).cursor, labelContrast: +contrast(getComputedStyle(label).color).toFixed(2), statusContrast: +contrast(getComputedStyle(status).color).toFixed(2),
        links: li.querySelectorAll('a,button,[tabindex]').length, ariaLabel: li.getAttribute('aria-label') };
    });
    const footer = document.querySelector('nav[aria-label="Workspace utilities"]');
    return {
      groups: [...nav.querySelectorAll('.nav-rail__group-label')].map((g) => g.textContent),
      roots: [...nav.querySelectorAll('li .nav-rail__label')].map((l) => l.textContent),
      links: [...nav.querySelectorAll('a')].map((a) => [a.textContent, a.getAttribute('href')]),
      rows,
      footer: footer ? { text: footer.innerText.replace(/[\\s]+/g, ' ').trim(), links: [...footer.querySelectorAll('a')].map((a) => [a.textContent, a.getAttribute('href')]),
        inViewport: footer.getBoundingClientRect().right <= vw + 0.5, afterRail: !!(nav.compareDocumentPosition(footer) & Node.DOCUMENT_POSITION_FOLLOWING) } : null,
      overflow: { scrollWidth: document.documentElement.scrollWidth, clientWidth: vw },
    };
  })()`);

async function tabOrder(max) {
  await js("document.activeElement && document.activeElement.blur(); window.scrollTo(0, 0); true");
  const seen = [];
  for (let i = 0; i < max; i += 1) {
    await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
    await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
    seen.push(await js(`(() => { const a = document.activeElement; return a ? (a.closest('li.nav-rail__unavailable') ? 'UNAVAILABLE:' + a.textContent : (a.textContent || a.tagName).trim().slice(0, 40)) : null; })()`));
  }
  return seen;
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
  for (const [label, width, height] of WIDTHS) {
    await size(width, height);
    for (const url of URLS) {
      const where = `${new URL(url).pathname} @${width} gate ${GATE}`;
      const ok = await go(url, "document.querySelector('nav[aria-label=\"Operator routes\"]') && document.querySelector('main h1')");
      claim(`${where}: page and rail render`, ok);
      const m = await measureRail();
      if (!m) {
        claim(`${where}: rail measured`, false);
        continue;
      }
      claim(`${where}: six groups in v6.9 order`, JSON.stringify(m.groups) === JSON.stringify(GROUPS), m.groups);
      claim(`${where}: eleven roots in v6.9 order`, JSON.stringify(m.roots) === JSON.stringify(ROOTS), m.roots);
      claim(`${where}: exactly two rail links, Sites and Findings`, JSON.stringify(m.links) === JSON.stringify(LIVE), m.links);
      claim(`${where}: nine unavailable rows measured (non-empty set)`, m.rows.length === 9, m.rows.map((r) => r.label));
      claim(`${where}: every status visible and kept with its label inside its row`,
        m.rows.length === 9 && m.rows.every((r) => r.status === "Not available yet" && r.visible && r.together),
        m.rows.filter((r) => !(r.visible && r.together)));
      claim(`${where}: every unavailable row inside the viewport`, m.rows.length === 9 && m.rows.every((r) => r.inViewport),
        m.rows.filter((r) => !r.inViewport).map((r) => r.label));
      claim(`${where}: unavailable rows are not controls (no pointer, no link, no tab stop)`,
        m.rows.length === 9 && m.rows.every((r) => r.cursor !== "pointer" && r.links === 0), [...new Set(m.rows.map((r) => r.cursor))]);
      const minContrast = Math.min(...m.rows.map((r) => Math.min(r.labelContrast, r.statusContrast)));
      claim(`${where}: muted but readable (min contrast >= 4.5)`, minContrast >= 4.5, { minContrast });
      claim(`${where}: accessible name carries label and status`, m.rows.every((r) => r.ariaLabel === `${r.label}, Not available yet`));
      if (GATE === "on") {
        claim(`${where}: WORKSPACE footer with the one Lab link, after the rail`,
          !!m.footer && m.footer.text.startsWith("WORKSPACE") &&
            JSON.stringify(m.footer.links) === JSON.stringify([["Open Simulator Lab", "/simulator-lab"]]) && m.footer.afterRail && m.footer.inViewport,
          m.footer);
      } else {
        const clean = await js("!document.querySelector('a[href*=\"simulator\"]') && !/simulator|workspace/i.test(document.body.innerText)");
        claim(`${where}: no workspace footer, no Lab link or label with the gate off`, m.footer === null && clean, m.footer);
      }
      claim(`${where}: no horizontal page overflow`, m.overflow.scrollWidth <= m.overflow.clientWidth, m.overflow);
      const expected = GATE === "on" ? ["Sites", "Findings", "Open Simulator Lab"] : ["Sites", "Findings"];
      const order = await tabOrder(expected.length + 1);
      claim(`${where}: Tab reaches the live links in order and never an unavailable row`,
        JSON.stringify(order.slice(0, expected.length)) === JSON.stringify(expected) && order.every((t) => !String(t).startsWith("UNAVAILABLE")), order);
      await shot(`app-${new URL(url).pathname.replace(/\W+/g, "_")}-${label}-gate-${GATE}`);
    }
    const origin = new URL(URLS[0]).origin;
    const mockOk = await go(`${origin}/mockups/v69/index.html#/sites`, "document.querySelector('.rail')");
    claim(`mock #/sites rail renders @${width}`, mockOk);
    const mockRail = await js(`[...document.querySelectorAll('.rail .rail-group')].map((g) => [g.querySelector('.eyebrow').textContent, [...g.querySelectorAll('a')].map((a) => a.textContent.trim())])`);
    claim(`mock rail has the same groups and roots @${width}`,
      JSON.stringify(mockRail.map((g) => g[0])) === JSON.stringify(GROUPS) && JSON.stringify(mockRail.flatMap((g) => g[1])) === JSON.stringify(ROOTS), mockRail);
    await shot(`mock-sites-${label}`);
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
