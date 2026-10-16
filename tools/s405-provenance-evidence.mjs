/**
 * S4-05b phase 2: browser layout evidence for the stored source label on Finding, Evidence, Financials and the
 * Site Overview at 1440x1000 and 390x900, from the installed Chrome over the DevTools Protocol (the no-dependency
 * approach of tools/s402b-fuel-cost-evidence.mjs).
 *
 *   node tools/s405-provenance-evidence.mjs <app-base> <case> <out-dir>
 *
 * Serve the case first with `tools/s405_provenance_walkthrough.py serve --case <case>` and the dev server on
 * <app-base>. The pages and expected states come from `var/s405_<case>/s405-state.json` (written by `prepare`),
 * so every claim is measured against a populated page: a missing notice FAILS rather than passing on an empty set.
 *
 * Claims per page and width: the source notice is present with the stored state; its label is rendered, inside the
 * viewport, outside any closed disclosure and not hidden from assistive technology; MIXED/UNKNOWN pages state that
 * no current cost is shown; the document has no page-level horizontal overflow. Also the v6.9 mock references
 * render (the comparison screenshots).
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const BASE = process.argv[2] ?? "http://localhost:5435";
const CASE = process.argv[3] ?? "owner";
const OUT = process.argv[4] ?? join(tmpdir(), "s405-evidence");
const SITE = "KOBO-001";
const STATE_FILE = process.env.S405_STATE ?? join("var", `s405_${CASE}`, "s405-state.json");
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9435);
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  ["desktop", 1440, 1000],
  ["narrow", 390, 900],
];
const LABELS = {
  AUTHORED_DEMONSTRATION: "Prepared example data",
  REGISTERED_SIMULATION: "Generated test data",
  MIXED: "Sources do not agree",
  UNKNOWN: "Source unverified",
};
mkdirSync(OUT, { recursive: true });
const state = JSON.parse(readFileSync(STATE_FILE, "utf-8"));

const profile = mkdtempSync(join(tmpdir(), "assetops-s405-cdp-"));
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
async function shot(name) {
  const tall = await js(`document.documentElement.scrollHeight`);
  const [w, h] = viewport;
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: Math.min(Math.ceil(tall), 7000), deviceScaleFactor: 1, mobile: w < 600 });
  await sleep(300);
  const r = await send("Page.captureScreenshot", { format: "png" });
  const file = join(OUT, `${name}.png`);
  writeFileSync(file, Buffer.from(r.data, "base64"));
  await size(w, h);
  await sleep(150);
  console.log(`      screenshot ${file}`);
}

// Every rendered source notice on the page and the measurements the claims need.
const MEASURE = `(() => {
  const vw = document.documentElement.clientWidth;
  const notices = [...document.querySelectorAll('[data-source-provenance]')].map((el) => {
    const label = el.querySelector('.notice strong');
    const r = label ? label.getBoundingClientRect() : { width: 0, height: 0, left: -1, right: 1e9 };
    const closed = label ? Boolean(label.closest('details:not([open])')) : true;
    const hidden = label ? Boolean(label.closest('[aria-hidden="true"]')) : true;
    const style = label ? getComputedStyle(label) : null;
    return { state: el.getAttribute('data-source-provenance'), subject: el.getAttribute('data-source-provenance-subject'),
      label: label ? label.textContent.trim() : null, statement: el.querySelector('.notice') ? el.querySelector('.notice').textContent.trim() : '',
      width: Math.round(r.width), height: Math.round(r.height), left: Math.round(r.left), right: Math.round(r.right),
      inViewport: r.width > 0 && r.height > 0 && r.left >= 0 && r.right <= vw + 1, closed, hidden,
      displayed: style ? style.visibility !== 'hidden' && style.display !== 'none' : false };
  });
  return { vw, scrollWidth: document.documentElement.scrollWidth, notices,
    noCost: document.body.innerText.includes('No current cost is shown.') };
})()`;

function pages() {
  const out = [];
  for (const [name, line] of Object.entries(state.verify)) {
    out.push({ key: `${name}-overview`, url: `${BASE}/sites/${SITE}?date=${line.day}`, subject: "overview-money" });
    line.picks.forEach((pick, i) => {
      const seen = line.findings[i] ?? {};
      if (i > 0) return; // one Finding per day is enough for layout
      const q = `revision_id=${pick.revision_id}`;
      out.push({ key: `${name}-finding`, url: `${BASE}/sites/${SITE}/findings/${pick.finding_id}?${q}`, subject: "finding", want: seen.finding_source });
      out.push({ key: `${name}-evidence`, url: `${BASE}/sites/${SITE}/findings/${pick.finding_id}/evidence?${q}`, subject: "evidence", want: seen.finding_source });
      out.push({ key: `${name}-financials`, url: `${BASE}/sites/${SITE}/financials?finding_id=${pick.finding_id}&${q}`, subject: null, want: seen.consequence_source ?? seen.finding_source });
    });
  }
  return out;
}

async function main() {
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
  for (const [W, width, height] of WIDTHS) {
    await size(width, height);
    for (const page of pages()) {
      const sel = page.subject ? `[data-source-provenance-subject="${page.subject}"]` : "[data-source-provenance]";
      const ready = await go(page.url, `document.querySelector('${sel}')`);
      const m = await js(MEASURE);
      const notices = m.notices.filter((n) => !page.subject || n.subject === page.subject);
      claim(`${CASE} ${W} ${page.key}: source notice rendered (non-empty set)`, ready && notices.length > 0, { count: notices.length });
      const wanted = page.want ?? notices[0]?.state;
      const first = notices.find((n) => n.state === wanted) ?? notices[0] ?? {};
      claim(`${CASE} ${W} ${page.key}: label "${LABELS[wanted]}" for stored ${wanted}`, first.label === `${LABELS[wanted]}.`, { label: first.label, state: first.state });
      claim(`${CASE} ${W} ${page.key}: label visible without a disclosure, in the viewport, exposed to assistive technology`,
        Boolean(first.inViewport && !first.closed && !first.hidden && first.displayed), { width: first.width, left: first.left, right: first.right, vw: m.vw, closed: first.closed, hidden: first.hidden });
      if (wanted === "MIXED" || wanted === "UNKNOWN") {
        claim(`${CASE} ${W} ${page.key}: states that no current cost is shown`, m.noCost);
      }
      claim(`${CASE} ${W} ${page.key}: no page-level horizontal overflow`, m.scrollWidth <= m.vw + 1, { scrollWidth: m.scrollWidth, vw: m.vw });
      await shot(`s405-${CASE}-${page.key}-${W}`);
    }
    if (CASE === "owner") {
      for (const [id, text] of [["financials", "Assumptions in use"]]) {
        const ok = await go(`${BASE}/mockups/v69/index.html#/${id}`, `document.body && document.body.innerText.includes(${JSON.stringify(text)})`);
        claim(`${W}: v6.9 mock #/${id} renders "${text}"`, ok);
        await shot(`s405-mock-${id}-${W}`);
      }
    }
  }
  const failed = results.filter((r) => !r.ok);
  writeFileSync(join(OUT, `s405-${CASE}-claims.json`), JSON.stringify(results, null, 2));
  console.log(`\n${results.length - failed.length}/${results.length} claims passed`);
  return failed.length;
}

let code = 1;
try {
  code = (await main()) === 0 ? 0 : 1;
} catch (error) {
  console.error(error);
} finally {
  ws?.close();
  chrome.kill();
  await sleep(500);
  try {
    rmSync(profile, { recursive: true, force: true });
  } catch {
    /* Chrome may still hold the profile */
  }
}
process.exit(code);
