/**
 * S6-01b phase 2: app-vs-v6.9-mock evidence for `recommendation:1`, `action-overview`, `action-execution`,
 * `action-history` and `changes:1#a`, at 1440 and 390, from the installed Chrome over the DevTools Protocol
 * (same approach as tools/s4-finding-evidence.mjs; no dependency).
 *
 * Run against the walkthrough servers (tools/s601b_action_walkthrough.py prepare + serve, frontend on 5461):
 *   node tools/s601b-action-evidence.mjs http://localhost:5461 <screenshot-dir>
 * Environment:
 *   ASSETOPS_S601B_WORK  walkthrough work folder holding walkthrough.json (default var/s601b_owner)
 *   ASSETOPS_CDP_PORT    Chrome DevTools port (default 9461)
 *
 * Every claim is measured and printed; the run exits non-zero if any fails. It also writes
 * `<screenshot-dir>/comparison.md`: per screen and width, the mock's panel headings beside the app's, so the
 * reviewer and owner can read what the app keeps, adapts or leaves to S6-02.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const BASE = process.argv[2] ?? "http://localhost:5461";
const OUT = process.argv[3] ?? join(tmpdir(), "s601b-action-evidence");
const SITE = "KOBO-001";
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9461);
const WORK = process.env.ASSETOPS_S601B_WORK ?? resolve("var", "s601b_owner");
const IDS = JSON.parse(readFileSync(join(WORK, "walkthrough.json"), "utf8"));
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  ["desktop", 1440, 1000],
  ["narrow", 390, 900],
];
mkdirSync(OUT, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "assetops-s601b-cdp-"));
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

const site = `${BASE}/sites/${SITE}`;
const A = IDS.action;
const OBS = IDS.events.find((e) => e.kind === "OBSERVED");
const ACC = IDS.events.find((e) => e.kind === "ACCEPTED");
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
  // --- recommendation:1 ---
  const mockRec = await mockScreen(label, "recommendation", "document.body.innerText.includes('Proposed intervention')");
  const recAccepted = `${site}/findings/${IDS.finding_f01}/recommendation?revision_id=${IDS.finding_f01_origin_revision}`;
  await go(recAccepted, "document.querySelector('[data-recommendation-accepted]') && document.querySelector('[data-recommendation-live]')");
  const ra = await js(`({ accepted: document.querySelector('[data-recommendation-accepted]')?.textContent,
    action: document.querySelector('[data-recommendation-action-link]')?.getAttribute('href'),
    live: document.querySelector('[data-recommendation-live]')?.getAttribute('data-recommendation-live'),
    limitation: document.querySelector('[data-action-limitation]')?.getAttribute('data-action-limitation'),
    buttons: document.querySelectorAll('main button').length })`);
  claim(`${label} recommendation: accepted snapshot beside labelled live status, Action link, trial limitation`,
    /15/.test(ra.accepted ?? "") && ra.action === `/sites/${SITE}/actions/${A}` && ra.live !== null && ra.limitation === "POLICY_SENSITIVITY_TRIAL_ONLY", ra);
  await noOverflow(label, "recommendation accepted");
  comparison.push(["recommendation:1 (accepted snapshot)", label, mockRec, await headings()]);
  await shot(`app-recommendation-accepted-${label}`);
  const again = await reload("document.querySelector('[data-recommendation-accepted]')");
  claim(`${label} recommendation: reload keeps the exact Finding version`, again && (await url()) === new URL(recAccepted).pathname + new URL(recAccepted).search, await url());

  await go(`${site}/findings/${IDS.finding_f01}/recommendation`, "document.querySelector('[data-recommendation-state]')");
  const rl = await js(`({ state: document.querySelector('[data-recommendation-state]')?.getAttribute('data-recommendation-state'),
    block: document.querySelector('[data-recommendation-prior-block]')?.getAttribute('data-recommendation-prior-block'),
    blockLink: document.querySelector('[data-recommendation-prior-block-link]')?.getAttribute('href'),
    blockCode: document.querySelector('[data-recommendation-prior-block-link]')?.textContent,
    origin: document.querySelector('[data-recommendation-prior-block-origin]')?.getAttribute('href'),
    originText: document.querySelector('[data-recommendation-prior-block-origin]')?.textContent,
    live: document.querySelector('[data-recommendation-live]')?.getAttribute('data-recommendation-live'),
    liveText: document.querySelector('[data-recommendation-live]')?.textContent,
    proposal: !!document.querySelector('[data-recommendation-proposal]'),
    accept: [...document.querySelectorAll('main button')].map(b => ({ text: b.textContent, disabled: b.disabled })),
    held: document.querySelector('[data-action-command-unavailable=PRIOR_ACTION_UNRESOLVED]')?.textContent,
    listed: [...document.querySelectorAll('[data-recommendation-prior-action]')].map(e => ({ id: e.dataset.recommendationPriorAction, selected: e.dataset.priorActionSelectedRevision,
      app: e.querySelector('[data-prior-action-application]')?.dataset.priorActionApplication, outcome: e.querySelector('[data-prior-action-outcome]')?.dataset.priorActionOutcome })) })`);
  claim(`${label} recommendation latest Finding version: PRIOR_ACTION_UNRESOLVED notice names and links ${IDS.action_code} and its origin version 1`,
    rl.state === "PRIOR_ACTION_UNRESOLVED" && rl.block === A && rl.blockLink === `/sites/${SITE}/actions/${A}` && rl.blockCode === IDS.action_code &&
    rl.origin === `/sites/${SITE}/findings/${IDS.finding_f01}?revision_id=${IDS.finding_f01_origin_revision}` && rl.originText === "Finding version 1", rl);
  claim(`${label} recommendation latest Finding version: live reason shown separately (served clock: FOUNDATION_BASIS_STALE), no proposal offered`,
    rl.live === "UNAVAILABLE" && /FOUNDATION_BASIS_STALE/.test(rl.liveText ?? "") && !rl.proposal, { live: rl.live, liveText: rl.liveText, proposal: rl.proposal });
  claim(`${label} recommendation latest Finding version: Accept is disabled with the reason stated`,
    rl.accept.length === 1 && rl.accept[0].disabled === true && /Accept trial/.test(rl.accept[0].text) && new RegExp(`\\(${IDS.action_code}\\) is still open`).test(rl.held ?? ""), { accept: rl.accept, held: rl.held });
  claim(`${label} recommendation latest Finding version: the earlier Action is listed on its own version (not this one), applied, outcome pending`,
    rl.listed.length >= 1 && rl.listed.some((x) => x.id === A && x.selected === "no" && x.app === "APPLIED" && x.outcome === "PENDING"), rl.listed);
  await noOverflow(label, "recommendation latest (prior Action notice)");
  comparison.push(["recommendation:1 (newer version, earlier trial open)", label, mockRec, await headings()]);
  await shot(`app-recommendation-latest-${label}`);

  await go(`${site}/findings/${IDS.finding_ineligible}/recommendation`, "document.querySelector('[data-recommendation-unavailable]')");
  const ru = await js(`({ code: document.querySelector('[data-recommendation-unavailable]')?.getAttribute('data-recommendation-unavailable'), buttons: document.querySelectorAll('main button').length })`);
  claim(`${label} recommendation ineligible: typed unavailable reason, no control`, ru.code === "SOC_NOT_ABOVE_HEADROOM" && ru.buttons === 0, ru);
  await noOverflow(label, "recommendation unavailable");
  await shot(`app-recommendation-unavailable-${label}`);

  // --- action-overview ---
  const mockOv = await mockScreen(label, "action-overview", "document.body.innerText.length > 200");
  await go(`${site}/actions/${A}`, "document.querySelector('[data-action-id]')");
  const ov = await js(`({ id: document.querySelector('[data-action-id]')?.dataset.actionId, app: document.querySelector('[data-action-id]')?.dataset.actionApplication,
    outcome: document.querySelector('[data-action-id]')?.dataset.actionOutcome, h1: document.querySelector('h1')?.textContent,
    change: document.querySelector('[data-action-change-link]')?.getAttribute('href'),
    later: Boolean(document.querySelector('[data-action-later-sections]')),
    tabs: [...document.querySelectorAll('[data-action-section]')].map(a => a.textContent) })`);
  claim(`${label} action-overview: code, applied, pending outcome, change link, only Overview/Application/History`,
    ov.id === A && ov.app === "APPLIED" && ov.outcome === "PENDING" && ov.h1?.startsWith(IDS.action_code) &&
      ov.change === `/sites/${SITE}/foundation/changes/${IDS.change}` && ov.later && ov.tabs.join() === "Overview,Application,History", ov);
  await noOverflow(label, "action-overview");
  comparison.push(["action-overview:1#a", label, mockOv, await headings()]);
  await shot(`app-action-overview-${label}`);

  // --- action-execution ---
  const mockEx = await mockScreen(label, "action-execution", "document.body.innerText.length > 200");
  await go(`${site}/actions/${A}/execution`, "document.querySelectorAll('[data-action-event-kind]').length > 0");
  const ex = await js(`({ kinds: [...document.querySelectorAll('[data-action-event-kind]')].map(r => r.dataset.actionEventKind),
    failures: [...document.querySelectorAll('[data-action-event-failure]')].map(e => e.dataset.actionEventFailure),
    change: document.querySelector('[data-action-event-change-link]')?.getAttribute('href'),
    applied: Boolean(document.querySelector('[data-action-already-applied]')), buttons: document.querySelectorAll('main button').length })`);
  claim(`${label} action-execution: ACCEPTED, OBSERVED, FAILED and APPLIED with the change record linked; nothing more to apply`,
    ["ACCEPTED", "OBSERVED", "FAILED", "APPLIED"].every((k) => ex.kinds.includes(k)) && ex.failures.length === 3 &&
      ex.change === `/sites/${SITE}/foundation/changes/${IDS.change}` && ex.applied && ex.buttons === 0, ex);
  await noOverflow(label, "action-execution");
  comparison.push(["action-execution:1#a", label, mockEx, await headings()]);
  await shot(`app-action-execution-${label}`);

  // --- action-history ---
  const mockHi = await mockScreen(label, "action-history", "document.body.innerText.length > 200");
  await go(`${site}/actions/${A}/history`, "document.querySelectorAll('[data-action-event-kind]').length > 0");
  const backdated = await js(`(() => { const r = document.querySelector('[data-action-event-kind="OBSERVED"]');
    return { recorded: r?.querySelector('[data-action-recorded-at]')?.dataset.actionRecordedAt, occurred: r?.querySelector('[data-action-occurred-at]')?.dataset.actionOccurredAt,
      note: /recorded later than it happened/.test(r?.textContent ?? '') }; })()`);
  claim(`${label} action-history: the backdated observation shows both times`, backdated.note && backdated.recorded !== backdated.occurred, backdated);
  await noOverflow(label, "action-history");
  comparison.push(["action-history:1#a", label, mockHi, await headings()]);
  await shot(`app-action-history-${label}`);

  const byEvent = `/sites/${SITE}/actions/${A}/history?event_id=${ACC.id}`;
  await go(`${BASE}${byEvent}`, "document.querySelector('[data-action-selection=\"EVENT_ID\"]')");
  await js(`document.querySelector('[data-action-section="execution"]').click()`);
  await waitFor(`location.pathname.endsWith('/execution')`);
  await sleep(500);
  const carried = await url();
  const kept = await reload("document.querySelector('[data-action-selection=\"EVENT_ID\"]')");
  claim(`${label} history: event_id selection carried into Application and kept on reload`,
    carried === byEvent.replace("/history?", "/execution?") && kept && (await url()) === carried, { carried });
  await shot(`app-action-selected-accepted-${label}`);

  const byTime = `/sites/${SITE}/actions/${A}/history?recorded_at=${encodeURIComponent(OBS.recorded_at)}`;
  await go(`${BASE}${byTime}`, "document.querySelector('[data-action-selection=\"RECORDED_AT\"]')");
  const cut = await js(`[...document.querySelectorAll('[data-action-event-kind]')].map(r => r.dataset.actionEventKind)`);
  const keptTime = await reload("document.querySelector('[data-action-selection=\"RECORDED_AT\"]')");
  claim(`${label} history: recorded_at cutoff shows events through the observation and survives reload`,
    cut.join() === "ACCEPTED,OBSERVED" && keptTime, cut);

  await go(`${site}/actions/${A}/history?event_id=${OBS.id}&recorded_at=${encodeURIComponent(OBS.recorded_at)}`, "document.querySelector('[data-action-code]')");
  const conflict = await js(`({ code: document.querySelector('[data-action-code]')?.dataset.actionCode, http: document.querySelector('[data-action-http]')?.dataset.actionHttp })`);
  claim(`${label} history: both selectors give the typed ACTION_SELECTOR_CONFLICT 422`, conflict.code === "ACTION_SELECTOR_CONFLICT" && conflict.http === "422", conflict);

  await go(`${site}/actions/${A}/history?event_id=00000000-0000-4000-8000-000000000000`, "document.querySelector('[data-action-read]')");
  const missing = await js(`({ read: document.querySelector('[data-action-read]')?.dataset.actionRead, latest: document.querySelector('[data-action-open-latest]')?.getAttribute('href') })`);
  claim(`${label} history: an unknown event is the selection not found, with a link to the latest`,
    missing.read === "selection-not-found" && missing.latest === `/sites/${SITE}/actions/${A}/history`, missing);

  // --- changes:1#a ---
  const mockCh = await mockScreen(label, "changes", "document.body.innerText.includes('Change and effect')");
  await go(`${site}/actions/${A}`, "document.querySelector('[data-action-change-link]')");
  await js(`document.querySelector('[data-action-change-link]').click()`);
  await waitFor("document.querySelector('[data-change-id]')");
  await sleep(400);
  const ch = await js(`({ url: location.pathname, old: document.querySelector('[data-change-old]')?.textContent, now: document.querySelector('[data-change-new]')?.textContent,
    origins: [...document.querySelectorAll('[data-change-revision]')].map(r => r.dataset.changeRevisionOrigin),
    bindings: document.querySelectorAll('[data-change-binding]').length, attempts: document.querySelector('[data-change-attempts]')?.dataset.changeAttempts,
    outcome: document.querySelector('[data-change-id]')?.dataset.changeOutcome, applied: document.querySelector('[data-change-applied-event-link]')?.getAttribute('href'),
    tabs: [...document.querySelectorAll('[aria-current="page"]')].map(e => e.textContent), views: Boolean(document.querySelector('nav[aria-label="Foundation views"]')) })`);
  claim(`${label} changes:1#a: reached from the Action; 20% to 15%, PUBLISH/SPLIT/PUBLISH, assignment sets, 3 failed attempts, pending, application event`,
    ch.url === `/sites/${SITE}/foundation/changes/${IDS.change}` && ch.old === "20%" && ch.now === "15%" && ch.origins.join() === "PUBLISH,SPLIT,PUBLISH" &&
      ch.bindings === 3 && ch.attempts === "3" && ch.outcome === "PENDING" && ch.applied?.endsWith(`event_id=${IDS.events.find((e) => e.kind === "APPLIED").id}`), ch);
  claim(`${label} changes:1#a: Foundation tab current, no Foundation view row`, ch.tabs.includes("Foundation") && !ch.views, ch.tabs);
  // Review L2: each failure code renders on one line (one client rect), never broken mid-token.
  const codes = await js(`[...document.querySelectorAll('[data-change-failed-attempt] .action-ref')].map(e => {
    const r = e.getClientRects(); return { code: e.textContent, boxes: r.length, white: getComputedStyle(e).whiteSpace }; })`);
  claim(`${label} changes:1#a: failure codes in the attempts list stay whole (measured ${codes.length})`,
    codes.length === 3 && codes.every((c) => c.boxes === 1 && c.white === "nowrap"), codes);
  await noOverflow(label, "changes:1#a");
  comparison.push(["changes:1#a", label, mockCh, await headings()]);
  await shot(`app-change-${label}`);
  const keptChange = await reload("document.querySelector('[data-change-id]')");
  claim(`${label} changes:1#a: reload keeps the change`, keptChange && (await url()) === ch.url, await url());

  await go(`${site}/foundation/changes`, "document.querySelector('[data-change-index]')");
  const bare = await js(`({ state: document.querySelector('[data-change-index]')?.dataset.changeIndex, back: [...document.querySelectorAll('main a')].find(a => a.textContent === 'Back to the Foundation')?.getAttribute('href') })`);
  claim(`${label} bare /foundation/changes: explicit unavailable state with a link back`, bare.state === "unavailable" && bare.back === `/sites/${SITE}/foundation`, bare);
  await shot(`app-changes-unavailable-${label}`);

  // --- the second Action: failed no-change, still pending, SYSTEM demonstration control offered ---
  await go(`${site}/actions/${IDS.action_f02}/execution`, "document.querySelector('[data-action-id]')");
  const f02 = await js(`({ app: document.querySelector('[data-action-id]')?.dataset.actionApplication, failures: [...document.querySelectorAll('[data-action-event-failure]')].map(e => e.dataset.actionEventFailure),
    button: document.querySelector('[data-action-command="APPLY"]')?.textContent ?? null, still: Boolean(document.querySelector('[data-action-failed-still-pending]')) })`);
  claim(`${label} second Action: FAILED no-change keeps it pending; the granted control is labelled SYSTEM demonstration`,
    f02.app === "PENDING" && f02.failures.includes("ACTION_NO_CHANGE") && f02.still && f02.button === "Apply trial (SYSTEM demonstration)", f02);
  await noOverflow(label, "second Action application");
  await shot(`app-action-f02-failed-pending-${label}`);
}

function comparisonMarkdown() {
  const lines = ["# S6-01b app vs v6.9 mock (headings as rendered)", "", "| Screen | Width | Mock headings | App headings |", "| --- | --- | --- | --- |"];
  for (const [screen, width, mock, app] of comparison) {
    const cell = (list) => list.map((h) => h.replace(/\|/g, "/")).join(" · ");
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
