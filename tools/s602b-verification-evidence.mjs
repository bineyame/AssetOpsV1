/**
 * S6-02b: app-vs-v6.9-mock evidence for the Action Plan / Evidence / Verification views, the Recommendation
 * success panels and the Foundation change later effect, at 1440 and 390, from the installed Chrome over the
 * DevTools Protocol (same approach as tools/s601b-action-evidence.mjs; no dependency).
 *
 * Run through `tools/s602b_verification_walkthrough.py ... capture` (or directly):
 *   node tools/s602b-verification-evidence.mjs <replay-web> <cases-web> <screenshot-dir>
 * Environment:
 *   ASSETOPS_S602B_WORK  walkthrough work folder holding replay.json and cases.json (default var/s602b_owner)
 *   ASSETOPS_CDP_PORT    Chrome DevTools port (default 9466)
 *
 * The replay frontend serves the real VERIFIED Action of manifest d-verification-window-v2; the cases frontend
 * serves the TEST-SCOPED examples. Every claim is measured and printed; the run exits non-zero if any fails. It
 * writes `<screenshot-dir>/comparison.md` (mock vs app headings per screen and width).
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { widthGuard } from "./evidence-checks.mjs";

const BASE = process.argv[2] ?? "http://localhost:5466";
const CASES_BASE = process.argv[3] ?? "http://localhost:5467";
const OUT = process.argv[4] ?? join(tmpdir(), "s602b-verification-evidence");
const SITE = "KOBO-001";
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9466);
const WORK = process.env.ASSETOPS_S602B_WORK ?? resolve("var", "s602b_owner");
const R = JSON.parse(readFileSync(join(WORK, "replay.json"), "utf8"));
const CASES = JSON.parse(readFileSync(join(WORK, "cases.json"), "utf8")).cases;
const PART = process.env.ASSETOPS_S602B_PART ?? "all";
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [
  ["desktop", 1440, 1000],
  ["narrow", 390, 900],
];
mkdirSync(OUT, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "assetops-s602b-cdp-"));
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
  await sleep(400);
  await requireWidth(viewport[0], viewport[1], `loaded ${url}`);
  return ok;
}
async function reload(ready) {
  await send("Page.reload");
  await sleep(300);
  const ok = await waitFor(ready);
  await requireWidth(viewport[0], viewport[1], "after reload or back");
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
  await requireWidth(viewport[0], null, `capture ${name}`, { record: false });
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
const A = R.action;
const csite = `${CASES_BASE}/sites/${SITE}`;
const settled = "document.querySelector('main') && !/Loading the/.test(document.querySelector('main').innerText)";
const attr = (sel, name) => js(`document.querySelector(${JSON.stringify(sel)})?.getAttribute(${JSON.stringify(name)}) ?? null`);
const text = (sel) => js(`document.querySelector(${JSON.stringify(sel)})?.textContent ?? null`);

/** Dense slot tables: the page never scrolls sideways; at least two table scrollers are measured (non-empty set). */
async function denseTables(label, what) {
  const t = await js(`[...document.querySelectorAll('[data-verification-evidence-window] .data-table__scroll')].map(e => ({ sw: e.scrollWidth, cw: e.clientWidth }))`);
  claim(`${label} ${what}: dense slot tables measured (${t.length}), each scrolls inside its own scroller`, t.length >= 2 && t.every((x) => x.cw > 0), t);
}

async function suite(label) {
  if (PART === "all" || PART === "replay") await replaySuite(label);
  if (PART !== "replay") await casesSuite(label);
}

async function replaySuite(label) {
  // --- verification:1-3, current (the replayed VERIFIED Action) ---
  const mockVer = await mockScreen(label, "verification", "document.body.innerText.includes('Target and guardrails evaluated together')");
  await go(`${site}/actions/${A}/verification`, `${settled} && document.querySelector('[data-verification-outcome]')`);
  const v = await js(`({ state: document.querySelector('[data-verification-current-state]')?.dataset.verificationCurrentState,
    outcome: document.querySelector('[data-verification-outcome]')?.dataset.verificationOutcome,
    id: document.querySelector('[data-verification-outcome]')?.dataset.verificationOutcomeId,
    label: document.querySelector('[data-verification-outcome]')?.dataset.verificationLabel,
    historical: !!document.querySelector('[data-verification-historical]'),
    source: document.querySelector("[data-verification-row='source_provenance']")?.textContent,
    target: document.querySelector("[data-verification-row='target_reduction']")?.textContent,
    trial: document.querySelector('[data-verification-trial-label]')?.textContent,
    resolved: [...document.querySelectorAll('[data-verification-resolution-kind]')].map(e => e.dataset.verificationResolutionKind),
    withdrawable: document.querySelector('[data-verification-resolved-withdrawable]')?.textContent })`);
  claim(`${label} verification current: the replayed VERIFIED outcome ${R.outcome} is current, not historical`,
    v.state === "VERIFIED" && v.outcome === "VERIFIED" && v.id === R.outcome && !v.historical && v.label === "Target met within every limit", v);
  claim(`${label} verification current: registered Lab source, target passes, policy-trial / no-savings label`,
    /Registered Lab trial data/.test(v.source ?? "") && /Pass/.test(v.target ?? "") && /no savings or realized benefit/.test(v.trial ?? ""), { source: v.source, target: v.target });
  claim(`${label} verification current: RESOLVED shown as activity and as withdrawable, never permanent`,
    v.resolved.includes("RESOLVED") && /not permanent/.test(v.withdrawable ?? ""), v.resolved);
  await noOverflow(label, "verification current");
  comparison.push(["verification:1-3 (replayed VERIFIED, current)", label, mockVer, await headings()]);
  await shot(`app-verification-current-${label}`);

  // Explicit historical selector: label, carried into every section link, kept across a child link and reload.
  await go(`${site}/actions/${A}/verification?outcome_id=${R.outcome}`, `${settled} && document.querySelector('[data-verification-outcome]')`);
  const links = await js(`[...document.querySelectorAll('[data-action-section]')].map(a => a.getAttribute('href'))`);
  claim(`${label} historical selector: Historical label; every section link keeps outcome_id`,
    !!(await text("[data-verification-historical]")) && links.length === 6 && links.every((h) => h.includes(`outcome_id=${R.outcome}`)), links);
  await shot(`app-verification-historical-${label}`);
  await js(`document.querySelector("[data-action-section='plan']").click()`);
  await waitFor(`${settled} && document.querySelector('[data-verification-plan-id]')`);
  const planUrl = `/sites/${SITE}/actions/${A}/plan?outcome_id=${R.outcome}`;
  claim(`${label} historical selector: Plan child keeps the selection and reads the outcome's plan`,
    (await url()) === planUrl && (await attr("[data-verification-plan-id]", "data-verification-plan-id")) === R.plan, await url());
  const again = await reload(`${settled} && document.querySelector('[data-verification-plan-id]')`);
  claim(`${label} historical selector: reload keeps it`, again && (await url()) === planUrl, await url());

  // --- action-plan:1 ---
  const mockPlan = await mockScreen(label, "action-plan", "document.body.innerText.includes('Success criteria')");
  await go(`${site}/actions/${A}/plan`, `${settled} && document.querySelector('[data-verification-plan-id]')`);
  const p = await js(`({ id: document.querySelector('[data-verification-plan-id]')?.dataset.verificationPlanId,
    current: document.querySelector('[data-verification-plan-id]')?.dataset.verificationPlanCurrent,
    later: document.querySelector("[data-verification-window='later']")?.dataset.verificationLaterBound,
    old: document.querySelector('[data-verification-old-foundation]')?.textContent, neu: document.querySelector('[data-verification-new-foundation]')?.textContent })`);
  claim(`${label} plan: exact plan, current, later selection appended, old -> new Foundation versions`,
    p.id === R.plan && p.current === "yes" && p.later === "yes" && p.old === R.old_foundation && p.neu === R.new_foundation, p);
  await noOverflow(label, "plan");
  comparison.push(["action-plan:1", label, mockPlan, await headings()]);
  await shot(`app-plan-${label}`);

  // --- action-evidence:1 (dense) ---
  const mockEv = await mockScreen(label, "action-evidence", "document.body.innerText.includes('Evidence requirements')");
  await go(`${site}/actions/${A}/evidence`, `${settled} && document.querySelector('[data-verification-evidence-window]')`);
  const e = await js(`({ slots: document.querySelectorAll('[data-verification-slot]').length,
    complete: [...document.querySelectorAll('[data-verification-evidence-window]')].map(w => w.dataset.verificationWindowComplete),
    sources: [...document.querySelectorAll('[data-verification-window-source]')].map(w => w.dataset.verificationWindowSource),
    counts: [...document.querySelectorAll('[data-verification-evidence-ids]')].map(w => Number(w.dataset.verificationEvidenceCount)) })`);
  claim(`${label} evidence: 2 x 12 complete five-minute slots, REGISTERED_SIMULATION per window, accepted IDs listed`,
    e.slots === 24 && e.complete.join() === "yes,yes" && e.sources.join() === "REGISTERED_SIMULATION,REGISTERED_SIMULATION" && e.counts.length === 2 && e.counts.every((n) => n > 0), e);
  await noOverflow(label, "evidence");
  await denseTables(label, "evidence");
  comparison.push(["action-evidence:1", label, mockEv, await headings()]);
  await shot(`app-evidence-${label}`);

  // Selector conflict.
  await go(`${site}/actions/${A}/verification?outcome_id=${R.outcome}&recorded_at=${encodeURIComponent(R.outcome_recorded_at)}`, `${settled} && document.querySelector('[data-verification-selector-conflict]')`);
  claim(`${label} conflicting selectors: typed VERIFICATION_SELECTOR_CONFLICT, nothing chosen`,
    (await attr("[data-verification-selector-conflict]", "data-verification-selector-conflict")) === "VERIFICATION_SELECTOR_CONFLICT" && !(await text("[data-verification-outcome]")));

  // --- recommendation:2-3 ---
  const mockRec = await mockScreen(label, "recommendation", "document.body.innerText.includes('Declare success before evaluating')");
  await go(`${site}/findings/${R.finding}/recommendation?revision_id=${R.finding_revision}`, `${settled} && document.querySelector('[data-recommendation-plan-link]')`);
  const rc = await js(`({ plan: document.querySelector('[data-recommendation-plan-link] a')?.getAttribute('href'),
    state: document.querySelector('[data-trial-verification-state]')?.dataset.trialVerificationState, accepted: !!document.querySelector('[data-recommendation-accepted]') })`);
  claim(`${label} recommendation: accepted snapshot kept; success panel links the frozen plan; verification state VERIFIED`,
    rc.accepted && rc.plan === `/sites/${SITE}/actions/${A}/plan?plan_revision_id=${R.plan}` && rc.state === "VERIFIED", rc);
  await noOverflow(label, "recommendation");
  comparison.push(["recommendation:2-3", label, mockRec, await headings()]);
  await shot(`app-recommendation-${label}`);

  // --- changes:1#b, changes:2 ---
  const mockChg = await mockScreen(label, "changes", "document.body.innerText.includes('Decision path')");
  await go(`${site}/foundation/changes/${R.change}`, `${settled} && document.querySelector('[data-change-decision-path]')`);
  const ch = await js(`({ state: document.querySelector('[data-trial-verification-state]')?.dataset.trialVerificationState,
    plan: document.querySelector('[data-change-plan-link]')?.getAttribute('href'), body: document.querySelector('main').innerText })`);
  claim(`${label} change: later effect from the verification block, plan link, applied is not success`,
    ch.state === "VERIFIED" && ch.plan === `/sites/${SITE}/actions/${A}/plan?plan_revision_id=${R.plan}` && /being applied is not success/.test(ch.body), { state: ch.state, plan: ch.plan });
  await noOverflow(label, "change");
  comparison.push(["changes:1#b, changes:2", label, mockChg, await headings()]);
  await shot(`app-change-${label}`);
}

// --- CC-R2-Q4 ruling: the estate Portfolio placement claims (case `estate`, cases.json `placement`) ---
const GROUPS = ["NEEDS_INVESTIGATION", "ACT_NOW", "COMPARE_VALUE", "UNPRICED_RISK", "MONITOR"];
const GROUP_LABEL = {
  NEEDS_INVESTIGATION: "Needs investigation first",
  ACT_NOW: "Act now",
  COMPARE_VALUE: "Compare value",
  UNPRICED_RISK: "Unpriced risk",
  MONITOR: "Monitor",
};
const POLICY_LINES = [
  "Needs investigation first: the evidence source is mixed or unresolved, the Finding is unconfirmed, or its cost is withheld.",
  "Act now: the episode is open, returned or reopened, and no Action is underway or its resolution was withdrawn.",
  "Monitor (checked next): a change was applied or verified.",
  "Compare value: the Finding has a priced cost exposure.",
  "Unpriced risk: the Finding has no price basis.",
];
const POLICY_FOOTER =
  "Groups say where to look first; they are not a value ranking. Within a group, most recent first. Policy estate-placement/1.";
const BOTTOM_LINE = "Placement and confidence answer different questions.";

async function portfolioSuite(label, c) {
  const p = c.placement;
  const ready = `${settled} && document.querySelector('[data-estate-root="portfolio"] [data-portfolio-row]')`;
  const loaded = await go(`${CASES_BASE}/portfolio?from=2026-10-03T00:00:00Z&to=2026-11-03T00:00:00Z`, ready);
  claim(`${label} estate Portfolio loads with rows`, loaded);
  // 1. Group headings: no repeats, GROUPS order, the three expected groups, exact label · count text.
  const heads = await js(`[...document.querySelectorAll('tr[data-placement-group]')].map(t => [t.dataset.placementGroup, t.textContent.trim()])`);
  const order = heads.map(([g]) => GROUPS.indexOf(g));
  const texts = heads.every(([g, t]) => t === (p.counts === null || p.counts[g] === null ? GROUP_LABEL[g] : `${GROUP_LABEL[g]} · ${p.counts[g]}`));
  claim(`${label} estate Portfolio: group headings once each, in group order, with label and count`,
    new Set(heads.map(([g]) => g)).size === heads.length && order.every((v, i) => v >= 0 && (i === 0 || v > order[i - 1]))
      && ["NEEDS_INVESTIGATION", "ACT_NOW", "MONITOR"].every((g) => heads.some(([h]) => h === g)) && texts, heads);
  // 2-3. The three placements, the nearest heading above each row, and the reason lines.
  const expected = { F01: "MONITOR", F03: "ACT_NOW", F05: "NEEDS_INVESTIGATION" };
  for (const [name, group] of Object.entries(expected)) {
    const got = await js(`(() => { const r = document.querySelector('[data-portfolio-row=' + JSON.stringify(${JSON.stringify(p.rows[name])}) + ']');
      if (!r) return null; let h = r.previousElementSibling; while (h && !h.matches('tr[data-placement-group]')) h = h.previousElementSibling;
      return { placement: r.querySelector('[data-portfolio-placement]')?.dataset.portfolioPlacement ?? null, heading: h?.dataset.placementGroup ?? null,
        reasons: r.querySelector('[data-portfolio-placement-reasons]')?.textContent ?? null }; })()`);
    const reasons = got?.reasons ?? "";
    const reasonOk = name === "F01" ? reasons === "Change verified on test data; watch for a return"
      : name === "F03" ? /Returned after an earlier episode \(Finding [0-9a-f]{8}\)/.test(reasons) && reasons.includes("No accepted Action; open the recommendation")
      : reasons.includes("The latest assessment no longer confirms this Finding; check its basis");
    claim(`${label} estate Portfolio: ${name} is ${group} under its own heading, with its reason line`,
      got !== null && got.placement === group && got.heading === group && reasonOk, got);
  }
  // 4. Confidence on every row; no guarded word in the priority panel.
  const conf = await js(`({ rows: [...document.querySelectorAll('[data-portfolio-row] [data-portfolio-confidence]')].map(e => [e.dataset.portfolioConfidence, e.textContent.trim()]),
    count: document.querySelectorAll('[data-portfolio-row]').length, panel: document.querySelector('[data-portfolio-panel="priority"]')?.textContent ?? '' })`);
  const words = [/\bclaims?\b/i, /simulat/i, /\bscenarios?\b/i].filter((re) => re.test(conf.panel)).map(String);
  claim(`${label} estate Portfolio: every row has a confidence code and text; no guarded word in the panel`,
    conf.rows.length === conf.count && conf.count > 0 && conf.rows.every(([code, t]) => ["SUPPORTED_SOURCE_COHERENT", "LIMITED", "UNKNOWN"].includes(code) && t !== "")
      && words.length === 0 && !/[A-Z]+_[A-Z_]+/.test(conf.panel), { rows: conf.rows.length, count: conf.count, words });
  // 5. Bottom line and the closed policy disclosure.
  const policy = await js(`(() => { const d = document.querySelector('[data-placement-policy]');
    return { bottom: document.querySelector('[data-portfolio-panel="priority"] .panel-bottom span')?.textContent ?? null,
      summary: d?.querySelector('summary')?.textContent ?? null, open: d?.open ?? null }; })()`);
  claim(`${label} estate Portfolio: bottom line and the closed "How placement works" disclosure`,
    policy.bottom === BOTTOM_LINE && policy.summary === "How placement works" && policy.open === false, policy);
  // 6. Layout, then 7. screenshots before and after opening the disclosure.
  await noOverflow(label, "estate Portfolio");
  await shot(`app-case-estate-portfolio-${label}`);
  const opened = await js(`(() => { const d = document.querySelector('[data-placement-policy]'); d.open = true;
    return { lines: [...d.querySelectorAll('li')].map(l => l.textContent.trim()), footer: d.querySelector('p')?.textContent.trim() ?? null }; })()`);
  claim(`${label} estate Portfolio: the opened disclosure shows the five policy lines and the footer`,
    JSON.stringify(opened.lines) === JSON.stringify(POLICY_LINES) && opened.footer === POLICY_FOOTER, opened);
  await shot(`app-case-estate-portfolio-policy-${label}`);
  const app = await headings();
  const mock = await mockScreen(label, "portfolio", "document.querySelector('.priority-panel')");
  comparison.push(["portfolio (priority panel)", label, mock, app]);
}

async function casesSuite(label) {
  // --- TEST-SCOPED cases (cases.json: { cases: { name: { label, action, expect, recommendation? } } }) ---
  // ASSETOPS_S602B_PART=<case> runs one case: the walkthrough serves one case database at a time.
  for (const [name, c] of Object.entries(CASES).filter(([n]) => PART === "all" || PART === n)) {
    await go(`${csite}/actions/${c.action}/verification`, `${settled} && document.querySelector('[data-verification-current-state]')`);
    const got = await js(`({ state: document.querySelector('[data-verification-current-state]')?.dataset.verificationCurrentState,
      outcome: document.querySelector('[data-verification-outcome]')?.dataset.verificationOutcome ?? null,
      label: document.querySelector('[data-verification-outcome]')?.dataset.verificationLabel ?? null,
      source: document.querySelector("[data-verification-row='source_provenance']")?.textContent ?? null,
      failed: [...document.querySelectorAll('[data-verification-failed-metric]')].map(e => e.dataset.verificationFailedMetric),
      resolved: [...document.querySelectorAll('[data-verification-resolution-kind]')].map(e => e.dataset.verificationResolutionKind),
      prior: document.querySelector('[data-verification-prior-outcome-link]')?.getAttribute('href') ?? null })`);
    const x = c.expect;
    const ok = got.state === x.current_state && (x.outcome === undefined || got.outcome === x.outcome) &&
      (x.label === undefined || got.label === x.label) && (x.failed === undefined || x.failed.every((m) => got.failed.includes(m))) &&
      (x.resolution === undefined || x.resolution.every((k) => got.resolved.includes(k))) && (x.prior_link !== true || got.prior !== null);
    claim(`${label} TEST-SCOPED ${name}: ${c.label}`, ok, got);
    if (c.authored_windows) {
      claim(`${label} TEST-SCOPED ${name}: the served source row says authored test data (test-scoped example)`,
        /test-scoped example/.test(got.source ?? ""), got.source);
    }
    await noOverflow(label, `case ${name}`);
    await shot(`app-case-${name}-${label}`);
    if (c.placement) await portfolioSuite(label, c); // CC-R2-Q4: case estate only
    if (c.withdrawn_outcome) {
      // The withdrawn VERIFIED, selected explicitly: Historical, never current; the separate current state stays.
      const hist = `/sites/${SITE}/actions/${c.action}/verification?outcome_id=${c.withdrawn_outcome}`;
      const ready = `${settled} && document.querySelector('[data-verification-outcome]')`;
      await go(`${CASES_BASE}${hist}`, ready);
      const read = () => js(`({ historical: !!document.querySelector('[data-verification-historical]'),
        outcome: document.querySelector('[data-verification-outcome]')?.dataset.verificationOutcome ?? null,
        id: document.querySelector('[data-verification-outcome]')?.dataset.verificationOutcomeId ?? null,
        current: document.querySelector('[data-verification-current-state]')?.dataset.verificationCurrentState ?? null })`);
      const h = await read();
      claim(`${label} TEST-SCOPED ${name}: the withdrawn VERIFIED reads Historical with a separate, non-VERIFIED current state`,
        h.historical && h.outcome === "VERIFIED" && h.id === c.withdrawn_outcome && h.current === x.current_state, h);
      const kept = await reload(ready);
      const h2 = await read();
      claim(`${label} TEST-SCOPED ${name}: reload keeps the historical selection`, kept && (await url()) === hist && h2.historical, await url());
      await shot(`app-case-${name}-historical-${label}`);
    }
    if (c.recommendation) {
      await go(`${csite}/findings/${c.recommendation.finding}/recommendation?revision_id=${c.recommendation.revision}`, `${settled} && document.querySelector('[data-recommendation-state]')`);
      const hold = await js(`({ state: document.querySelector('[data-recommendation-state]')?.dataset.recommendationState,
        code: document.querySelector('[data-recommendation-prior-block-code]')?.dataset.recommendationPriorBlockCode ?? null,
        other: document.querySelector('[data-recommendation-prior-block-other-finding]') !== null,
        link: document.querySelector('[data-recommendation-prior-block-link]')?.getAttribute('href') ?? null,
        disabled: [...document.querySelectorAll('main button')].every(b => b.disabled) })`);
      claim(`${label} TEST-SCOPED ${name} hold ${c.recommendation.state}${c.recommendation.other_finding ? " (different Finding)" : ""}`,
        hold.state === c.recommendation.state && hold.code === c.recommendation.state && hold.other === Boolean(c.recommendation.other_finding) && hold.link !== null && hold.disabled, hold);
      await noOverflow(label, `case ${name} hold`);
      await shot(`app-case-${name}-hold-${label}`);
    }
  }
}

function comparisonMarkdown() {
  const lines = ["# S6-02b app vs v6.9 mock (headings as rendered)", "", "| Screen | Width | Mock headings | App headings |", "| --- | --- | --- | --- |"];
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
  if (comparison.length > 0) writeFileSync(join(OUT, "comparison.md"), comparisonMarkdown());
  writeFileSync(join(OUT, `results-${PART}.json`), JSON.stringify(results, null, 2));
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
