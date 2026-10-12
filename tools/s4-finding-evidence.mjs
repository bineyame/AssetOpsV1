/**
 * S4-01 phase 3: app-vs-mock evidence for the Site Finding detail (`finding:1,2,4`), with layout
 * measurements, keyboard interaction and reload checks, from the installed Chrome over the DevTools
 * Protocol (same approach as tools/s3-dispatch-evidence.mjs; no dependency).
 *
 * Run against the walkthrough servers (tools/s4_finding_walkthrough.py prepare + serve, frontend on 5340):
 *   node tools/s4-finding-evidence.mjs http://localhost:5340 <screenshot-dir>
 *
 * Finding IDs come from the walkthrough's copy of the producer run record. Every claim is measured and
 * printed; the run exits non-zero if any fails. Set-based claims report their size.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const BASE = process.argv[2] ?? "http://localhost:5340";
const OUT = process.argv[3] ?? join(tmpdir(), "s4-finding-evidence");
const SITE = "KOBO-001";
const PORT = 9343;
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  ["desktop", 1440, 1000],
  ["narrow", 390, 900],
];
mkdirSync(OUT, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "assetops-s4-cdp-"));
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
      wide: [...document.querySelectorAll('.site-finding *')].filter(e => e.getBoundingClientRect().right > d.clientWidth + 1
      && !e.closest('.data-table__scroll') && ![...e.children].some(c => c.getBoundingClientRect().right > d.clientWidth + 1))
      .map(e => (e.className || e.tagName) + ':' + Math.round(e.getBoundingClientRect().width)).slice(0, 6) }; })()`);

const RUN = join(process.env.LOCALAPPDATA ?? tmpdir(), "AssetOps", "s4-finding-walkthrough", "s4-finding-cases-run.json");
const run = JSON.parse(readFileSync(RUN, "utf-8"));
const byAnchor = (prefix) => {
  const f = run.findings.find((x) => x.anchor_start.startsWith(prefix));
  if (!f) throw new Error(`no Finding anchored at ${prefix} in ${RUN}`);
  return f;
};
const F01 = byAnchor("2026-10-06 08:00");
const F02 = byAnchor("2026-10-08 23:20");
const F03 = byAnchor("2026-10-11 09:30");
const F04 = byAnchor("2026-10-13 08:30");
const F05 = byAnchor("2026-10-21 08:00");
const F06M = byAnchor("2026-10-15 13:00");
const READY = "document.querySelector('[data-finding-lifecycle], [data-finding-read]')";
const finding = (f, q = "") => `${BASE}/sites/${SITE}/findings/${f.finding_id}${q}`;
const STATE = `(() => ({
  url: location.pathname + location.search,
  lifecycle: document.querySelector('[data-finding-lifecycle]')?.dataset.findingLifecycle,
  revision: document.querySelector('[data-finding-revision]')?.dataset.findingRevision,
  lead: document.querySelector('.site-finding__lead h2')?.textContent,
  currentness: document.querySelector('[data-chip="currentness"]')?.textContent,
  headings: [...document.querySelectorAll('.site-finding h2')].map(h => h.textContent),
  cards: document.querySelectorAll('[data-finding-card]').length,
  records: document.querySelectorAll('[data-evidence-id]').length,
  blocks: document.querySelectorAll('[data-portion]').length,
  pressed: document.querySelector('[data-portion][aria-pressed="true"]')?.getAttribute('aria-label') ?? null,
  dispatchDays: [...document.querySelectorAll('[data-finding-dispatch-day]')].map(a => a.getAttribute('href')),
  recurrence: document.querySelector('[data-finding-recurrence]')?.textContent ?? null,
  sentence: document.querySelector('[data-finding-lifecycle-sentence]')?.textContent ?? null,
}))()`;
const PANELS = ["What happened", "What limits this conclusion", "What to do next", "Where to look next"];

async function enter() {
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13, text: "\r" });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
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
    await go(`${BASE}/mockups/v69/index.html#/finding`, "document.body && document.body.innerText.includes('Where to look next')");
    const mock = await js(`({ panels: ${JSON.stringify(PANELS)}.filter(p => document.body.innerText.includes(p)) })`);
    claim(`${label}: mock #/finding renders its four panels`, mock.panels.length === 4, mock);
    await shot(`mock-finding-${label}`);

    await go(finding(F01), READY);
    const s = await js(STATE);
    claim(`${label} F01: panels, cards and records render, up to date`,
      PANELS.every((p) => s.headings.includes(p)) && s.cards === 5 && s.records > 0 && s.lifecycle === "SUPPORTED" && s.currentness === "Up to date", s);
    claim(`${label} F01: Dispatch drill-down names the day and the assessed period`,
      s.dispatchDays.length === 1 && /day=2026-10-06&revision=/.test(s.dispatchDays[0]), s.dispatchDays);
    let o = await overflow();
    claim(`${label} F01: no sideways page scroll`, o.scrollWidth <= o.clientWidth && o.wide.length === 0, o);
    await shot(`app-finding-open-${label}`);

    await js(`document.querySelector('[data-portion="CANDIDATE_AVOIDABLE"]').focus()`);
    await enter();
    const keyed = await waitFor(`document.querySelector('[data-finding-portion-detail]')`);
    const before = await js(STATE);
    claim(`${label} F01: keyboard Enter selects a block and shows its Dispatch link`,
      keyed && before.blocks > 1 && before.pressed !== null && /portion=/.test(before.url), before);
    await send("Page.reload");
    await waitFor(`document.querySelector('[data-finding-portion-detail]')`);
    await sleep(300);
    const after = await js(STATE);
    claim(`${label} F01: reload keeps the Finding, version and selected block`,
      after.url === before.url && after.revision === before.revision && after.pressed === before.pressed, after);

    const r1 = F04.revisions[0].revision_id;
    await go(finding(F04, `?revision_id=${r1}`), READY);
    const pinned = await js(STATE);
    claim(`${label} F04: exact version 1 opens, labelled as an earlier version`,
      pinned.revision === r1 && /^Earlier version 1 of /.test(pinned.lead ?? "") && pinned.currentness === "Earlier version", pinned);
    await send("Page.reload");
    await waitFor(READY);
    await sleep(300);
    const pinnedAgain = await js(STATE);
    claim(`${label} F04: reload keeps the exact earlier version`, pinnedAgain.revision === r1 && pinnedAgain.url === pinned.url, pinnedAgain);
    await shot(`app-finding-earlier-version-${label}`);
    await go(finding(F04), READY);
    const latest = await js(STATE);
    claim(`${label} F04: the same Finding's latest version differs from version 1`,
      latest.revision !== r1 && latest.revision === F04.revisions.at(-1).revision_id, latest);

    const r2 = F05.revisions[1].revision_id;
    await go(finding(F05, `?revision_id=${r2}`), READY);
    const unconfirmed = await js(STATE);
    claim(`${label} F05: version 2 reads Not confirmed`, unconfirmed.lifecycle === "UNCONFIRMED" && unconfirmed.revision === r2, unconfirmed);
    await shot(`app-finding-unconfirmed-${label}`);
    await go(finding(F05), READY);
    const closed = await js(STATE);
    claim(`${label} F05: latest reads No longer supported, not a repair or a saving`,
      closed.lifecycle === "NO_LONGER_SUPPORTED" && /not mean the generator was repaired/.test(closed.sentence ?? ""), closed);
    await shot(`app-finding-closed-${label}`);

    await go(finding(F02), READY);
    const stale = await js(STATE);
    claim(`${label} F02: cross-midnight Finding with a pending day reads Out of date and stays visible`,
      stale.currentness === "Out of date" && stale.cards === 5 && stale.dispatchDays.length === 2, stale);
    await shot(`app-finding-stale-${label}`);

    await go(finding(F03), READY);
    const rec = await js(STATE);
    claim(`${label} F03: recurrence links the earlier Finding without saying it is still open`,
      /does not say the earlier Finding is still open/.test(rec.recurrence ?? ""), rec.recurrence);
    await go(finding(F06M), READY);
    const merged = await js(STATE);
    claim(`${label} F06: a Finding joined into another leads with that`, merged.lead === "Joined into an earlier Finding", merged.lead);

    await go(finding(F01, "?view=analysis"), "document.querySelector('[data-finding-technical]')");
    const tech = await js(`({ ids: document.querySelectorAll('[data-tech-evidence-id]').length, versions: document.querySelectorAll('[data-tech-version]').length })`);
    o = await overflow();
    claim(`${label} Analysis: full record and version identifiers, no sideways page scroll`,
      tech.ids > 0 && tech.versions > 0 && o.scrollWidth <= o.clientWidth && o.wide.length === 0, { ...tech, ...o });
    await shot(`app-finding-analysis-${label}`);

    for (const [day, expect, link] of [["2026-10-06", "FINDINGS_RECORDED", true], ["2026-10-19", "NOT_DETERMINABLE", false], ["2026-10-07", "NOT_ASSESSED", false]]) {
      await go(`${BASE}/sites/${SITE}/performance/dispatch?day=${day}`, "document.querySelector('[data-day-findings]')");
      const d = await js(`({ state: document.querySelector('[data-day-findings]')?.dataset.dayFindings,
        links: [...document.querySelectorAll('[data-dispatch-finding]')].map(a => a.getAttribute('href')) })`);
      claim(`${label} Dispatch ${day}: ${expect}${link ? " with a Finding link" : ", no Finding link"}`,
        d.state === expect && (link ? d.links.length > 0 : d.links.length === 0), d);
      if (link) await shot(`app-dispatch-finding-link-${label}`);
    }
  }
  const failed = results.filter((r) => !r.ok);
  console.log(`\n${results.length - failed.length}/${results.length} claims passed; screenshots in ${OUT}`);
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
