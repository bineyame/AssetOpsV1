/**
 * What a person waits for on the Runs inventory and on Draft setup, measured
 * in a real browser. T022B's interaction evidence (`D-2026-09-29-run-store-libyaml`).
 *
 *   node tools/run-store-browser-evidence.mjs <baseUrl> <scenarioId> [samples] [--json out.json]
 *
 * Preconditions, because a missing one is not a pass: a composed app is up
 * (`tools/run-store-evidence.py serve <env> --port P`, which composes
 * `host/lab_app.py`'s application over an ISOLATED environment - never `var/`),
 * and `npm run dev` or `vite preview` proxies `/api` to it (`ASSETOPS_API_PORT`).
 * The scenario must be one whose setup form the target Site can fill. Every
 * sample creates one Draft in that isolated environment's run store, and the
 * counts before and after are reported.
 *
 * It drives the Chrome already installed on this machine over the DevTools
 * Protocol with Node's built-in fetch and WebSocket, exactly as
 * `tools/layout-evidence.mjs` does, and adds no dependency.
 *
 * ## Timing boundaries, stated because a number without one is not evidence
 *
 * Every time is taken INSIDE the page with `performance.now()`, and every
 * "ready" moment is the first DOM mutation after which the named content is
 * present - so a reading is at most one frame early of the paint that shows it.
 *
 * - inventory, full navigation: from the navigation's time origin to the Runs
 *   table holding its rows (and the row count is checked against the API's).
 * - inventory, in-app: from the click on the Lab's Runs link to the same state.
 * - setup: from the click on "Create draft run" to the created Draft's summary
 *   showing its run ID and a frozen-input table with rows.
 * - run detail: from the navigation's time origin to the run's frozen-input
 *   table holding rows.
 *
 * The first sample is reported apart from the rest: it pays for a cold browser
 * cache and, against `npm run dev`, for the dev server compiling modules.
 */

import { spawn } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir, cpus, totalmem, freemem, loadavg, release } from "node:os";
import { join } from "node:path";

const args = process.argv.slice(2);
const jsonAt = args.indexOf("--json");
const JSON_OUT = jsonAt >= 0 ? args[jsonAt + 1] : null;
const positional = args.filter((_, i) => jsonAt < 0 || (i !== jsonAt && i !== jsonAt + 1));
const BASE = positional[0] ?? "http://localhost:5173";
const SCENARIO = positional[1] ?? "fuel-loss-event";
const SAMPLES = Number(positional[2] ?? 7);
const PORT = 9351;
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const RUNS_API = `${BASE}/api/simulator-lab/runs`;

const profile = mkdtempSync(join(tmpdir(), "assetops-runstore-"));
const chrome = spawn(
  CHROME,
  [
    "--headless=new",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${profile}`,
    "about:blank",
  ],
  { stdio: "ignore" },
);

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function pageSocketUrl() {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      const page = (await res.json()).find((t) => t.type === "page");
      if (page?.webSocketDebuggerUrl) return page.webSocketDebuggerUrl;
    } catch {
      /* not up yet */
    }
    await sleep(250);
  }
  throw new Error("Chrome did not expose a page target");
}

class Cdp {
  constructor(ws) {
    this.ws = ws;
    this.id = 0;
    this.pending = new Map();
    ws.addEventListener("message", (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
      }
    });
  }

  send(method, params = {}, timeoutMs = 90000) {
    this.id += 1;
    const id = this.id;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`CDP ${method} (#${id}) got no reply within ${timeoutMs}ms`));
      }, timeoutMs);
      this.pending.set(id, {
        resolve: (v) => (clearTimeout(timer), resolve(v)),
        reject: (e) => (clearTimeout(timer), reject(e)),
      });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async value(expression) {
    const out = await this.send("Runtime.evaluate", {
      expression,
      returnByValue: true,
      awaitPromise: true,
    });
    if (out.exceptionDetails) {
      throw new Error(`Page script failed: ${JSON.stringify(out.exceptionDetails).slice(0, 400)}`);
    }
    return out.result.value;
  }
}

/**
 * Installed in every document before its own scripts: the first moment each
 * named piece of content is present, on the page's own clock.
 */
const MARKS = `(() => {
  const named = {
    runsRows: '[aria-labelledby="runs-table-heading"] tbody tr',
    runFrozenRows: '[aria-labelledby="run-frozen-heading"] tbody tr',
  };
  window.__marks = {};
  const check = () => {
    for (const [name, selector] of Object.entries(named)) {
      if (window.__marks[name]) continue;
      const count = document.querySelectorAll(selector).length;
      if (count > 0) window.__marks[name] = { t: performance.now(), count };
    }
  };
  new MutationObserver(check).observe(document, { subtree: true, childList: true });
})()`;

async function waitFor(cdp, expression, timeoutMs = 90000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    if (await cdp.value(expression)) return true;
    await sleep(50);
  }
  return false;
}

async function expectedRuns() {
  const res = await fetch(RUNS_API);
  if (!res.ok) throw new Error(`GET ${RUNS_API} answered ${res.status}`);
  return (await res.json()).runs.length;
}

async function navigate(cdp, path) {
  await cdp.send("Page.navigate", { url: `${BASE}${path}` });
}

async function inventoryByNavigation(cdp) {
  const expected = await expectedRuns();
  await navigate(cdp, "/simulator-lab/runs");
  if (!(await waitFor(cdp, "Boolean(window.__marks && window.__marks.runsRows)"))) {
    throw new Error("The Runs table never drew a row");
  }
  const mark = await cdp.value("window.__marks.runsRows");
  const api = await cdp.value(`(() => {
    const e = performance.getEntriesByType("resource").find((r) => r.name.endsWith("/api/simulator-lab/runs"));
    return e ? { start: e.startTime, duration: e.duration, end: e.responseEnd } : null;
  })()`);
  // Where the rest of the wait went: the document's own milestones, so the
  // part the run store owns (the API) can be told apart from page boot and
  // rendering.
  const page = await cdp.value(`(() => {
    const nav = performance.getEntriesByType("navigation")[0];
    const scripts = performance.getEntriesByType("resource").filter((r) => r.initiatorType === "script");
    return {
      domContentLoaded: nav ? nav.domContentLoadedEventEnd : null,
      scripts: scripts.length,
      lastScriptEnd: scripts.length ? Math.max(...scripts.map((s) => s.responseEnd)) : null,
    };
  })()`);
  return { ms: mark.t, rows: mark.count, expected, api, page };
}

async function inventoryInApp(cdp) {
  const expected = await expectedRuns();
  await navigate(cdp, "/simulator-lab");
  const link = 'document.querySelector(\'a[href="/simulator-lab/runs"]\')';
  if (!(await waitFor(cdp, `${link} !== null`, 30000))) return { ms: null, note: "no Runs link on /simulator-lab" };
  await sleep(300);
  const out = await cdp.value(`new Promise((resolve) => {
    const selector = '[aria-labelledby="runs-table-heading"] tbody tr';
    const t0 = performance.now();
    const done = () => {
      const count = document.querySelectorAll(selector).length;
      if (count > 0) {
        observer.disconnect();
        const ms = performance.now() - t0;
        const e = performance.getEntriesByType("resource").filter(
          (r) => r.name.endsWith("/api/simulator-lab/runs") && r.startTime >= t0)[0];
        resolve({ ms, rows: count,
          apiStart: e ? e.startTime - t0 : null, apiEnd: e ? e.responseEnd - t0 : null });
      }
    };
    const observer = new MutationObserver(done);
    observer.observe(document, { subtree: true, childList: true });
    ${link}.click();
    setTimeout(() => resolve({ ms: null, note: "timeout" }), 85000);
  })`);
  return { ...out, expected };
}

const FILL = `(() => {
  const setNative = (prototype, element, value) => {
    Object.getOwnPropertyDescriptor(prototype, "value").set.call(element, value);
    element.dispatchEvent(new Event("input", { bubbles: true }));
    element.dispatchEvent(new Event("change", { bubbles: true }));
  };
  const setValue = (id, value) => {
    const element = document.getElementById(id);
    if (!element) return false;
    setNative(window.HTMLInputElement.prototype, element, value);
    return true;
  };
  const chooseFirst = (id) => {
    const element = document.getElementById(id);
    if (!element) return false;
    const option = Array.from(element.options).find((item) => item.value !== "");
    if (!option) return false;
    setNative(window.HTMLSelectElement.prototype, element, option.value);
    return true;
  };
  const seed = String(20260000 + Math.floor(Math.random() * 90000));
  const filled =
    setValue("run-setup-start", "2026-09-21T00:00:00Z") &&
    setValue("run-setup-end", "2026-09-22T17:00:00Z") &&
    setValue("run-setup-timestep", "15") &&
    setValue("run-setup-seed", seed) &&
    chooseFirst("run-setup-model-profile") &&
    chooseFirst("run-setup-publication-profile");
  const submit = Array.from(document.querySelectorAll("main button")).find(
    (b) => (b.textContent || "").trim() === "Create draft run");
  if (!filled || !submit) return "controls-missing";
  if (submit.disabled) return "not-ready";
  return true;
})()`;

async function setup(cdp) {
  const before = await expectedRuns();
  await navigate(cdp, `/simulator-lab/scenarios/${SCENARIO}/run-setup`);
  let state = "not-ready";
  for (let attempt = 0; attempt < 200 && state !== true; attempt += 1) {
    await sleep(100);
    state = await cdp.value(FILL);
    if (state === "controls-missing" && attempt > 100) break;
  }
  if (state !== true) throw new Error(`The setup form was never ready to submit (${state})`);
  await sleep(300);
  const out = await cdp.value(`new Promise((resolve) => {
    const submit = Array.from(document.querySelectorAll("main button")).find(
      (b) => (b.textContent || "").trim() === "Create draft run");
    const t0 = performance.now();
    const done = () => {
      const heading = document.getElementById("run-setup-created-heading");
      const rows = document.querySelectorAll('[aria-labelledby="run-setup-frozen-heading"] tbody tr').length;
      if (!heading || rows === 0) return;
      const panel = heading.closest("section") || document.querySelector("main");
      const text = panel.textContent || "";
      const id = text.match(/run-[0-9a-f]{32}/);
      if (!id) return;
      observer.disconnect();
      const status = (text.match(/Execution status\\s*(READY|BLOCKED)/) || [])[1] || null;
      resolve({ ms: performance.now() - t0, runId: id[0], frozenRows: rows, status });
    };
    const observer = new MutationObserver(done);
    observer.observe(document, { subtree: true, childList: true, characterData: true });
    submit.click();
    setTimeout(() => resolve({ ms: null, note: "timeout" }), 85000);
  })`);
  return { ...out, storeBefore: before };
}

async function runDetail(cdp, runId) {
  await navigate(cdp, `/simulator-lab/runs/${runId}`);
  if (!(await waitFor(cdp, "Boolean(window.__marks && window.__marks.runFrozenRows)"))) {
    throw new Error(`Run detail for ${runId} never drew its frozen inputs`);
  }
  const mark = await cdp.value("window.__marks.runFrozenRows");
  const shown = await cdp.value(`(document.querySelector("main").textContent || "").includes(${JSON.stringify(runId)})`);
  return { ms: mark.t, frozenRows: mark.count, showsRunId: shown };
}

function stats(values) {
  const v = values.filter((x) => typeof x === "number").sort((a, b) => a - b);
  if (v.length === 0) return null;
  const mid = Math.floor(v.length / 2);
  const median = v.length % 2 ? v[mid] : (v[mid - 1] + v[mid]) / 2;
  return { n: v.length, median_ms: Math.round(median), min_ms: Math.round(v[0]), max_ms: Math.round(v[v.length - 1]) };
}

const ws = new WebSocket(await pageSocketUrl());
await new Promise((resolve) => ws.addEventListener("open", resolve, { once: true }));
const cdp = new Cdp(ws);
await cdp.send("Page.enable");
await cdp.send("Runtime.enable");
await cdp.send("Page.addScriptToEvaluateOnNewDocument", { source: MARKS });
await cdp.send("Emulation.setDeviceMetricsOverride", { width: 1280, height: 800, deviceScaleFactor: 1, mobile: false });

const startCount = await expectedRuns();
const samples = [];
let failure = null;
try {
  for (let i = 0; i < SAMPLES + 1; i += 1) {
    const navigation = await inventoryByNavigation(cdp);
    const inApp = await inventoryInApp(cdp);
    const created = await setup(cdp);
    const detail = created.runId ? await runDetail(cdp, created.runId) : null;
    const sample = { index: i, first: i === 0, navigation, inApp, setup: created, detail };
    samples.push(sample);
    console.log(
      `${i === 0 ? "first " : "sample"} ${i}: inventory nav ${Math.round(navigation.ms)} ms ` +
        `(${navigation.rows}/${navigation.expected} rows, api ${navigation.api ? Math.round(navigation.api.duration) : "?"} ms)` +
        ` | in-app ${inApp.ms === null ? inApp.note : Math.round(inApp.ms) + " ms"}` +
        ` (api ${inApp.apiStart == null ? "?" : Math.round(inApp.apiStart)}->${inApp.apiEnd == null ? "?" : Math.round(inApp.apiEnd)} ms)` +
        ` | page boot dcl ${navigation.page?.domContentLoaded == null ? "?" : Math.round(navigation.page.domContentLoaded)} ms` +
        ` | setup ${created.ms === null ? created.note : Math.round(created.ms) + " ms"} ${created.status ?? ""}` +
        ` | detail ${detail ? Math.round(detail.ms) + " ms" : "-"}`,
    );
  }
} catch (error) {
  failure = String(error && error.stack ? error.stack : error);
  console.error(failure);
}
const endCount = await expectedRuns().catch(() => null);

const quiet = samples.filter((s) => !s.first);
const summary = {
  base: BASE,
  scenario: SCENARIO,
  startCount,
  endCount,
  machine: { cpus: cpus().length, cpu: cpus()[0]?.model, totalmem: totalmem(), freemem: freemem(), loadavg: loadavg(), os: release() },
  first: samples.find((s) => s.first) ?? null,
  quiet: {
    inventoryNavigation: stats(quiet.map((s) => s.navigation.ms)),
    inventoryApi: stats(quiet.map((s) => s.navigation.api?.duration)),
    inventoryInApp: stats(quiet.map((s) => s.inApp.ms)),
    inventoryInAppApiEnd: stats(quiet.map((s) => s.inApp.apiEnd)),
    inventoryInAppAfterApi: stats(quiet.map((s) =>
      s.inApp.ms != null && s.inApp.apiEnd != null ? s.inApp.ms - s.inApp.apiEnd : null)),
    setup: stats(quiet.map((s) => s.setup.ms)),
    runDetail: stats(quiet.map((s) => s.detail?.ms)),
  },
  rowCountsMatched: samples.every((s) => s.navigation.rows === s.navigation.expected),
  samples,
  failure,
};
console.log(JSON.stringify({ startCount, endCount, quiet: summary.quiet, rowCountsMatched: summary.rowCountsMatched }, null, 2));
if (JSON_OUT) writeFileSync(JSON_OUT, JSON.stringify(summary, null, 2));

ws.close();
chrome.kill();
try {
  rmSync(profile, { recursive: true, force: true });
} catch {
  /* Windows sometimes holds the profile briefly */
}
process.exit(failure ? 1 : 0);
