// W4-01 commit 5: app vs v69 mock at 1440 and 390 for `sitework-incidents` and `sitework-maintenance`.
// Stocked (seed.py), empty (window with no cases) and refused/unknown (422 window) through the real backend.
// The `test_w401_stocked_five_rows_1440_and_390` block asserts the spec caps (S31 and the Run 7 dry-read).
// Usage: node capture.mjs <out-dir> <revision> <app-base>
import { spawn } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const [, , OUT, REV, BASE = "http://localhost:6145"] = process.argv;
const PORT = 9747;
const MOCK = pathToFileURL("C:/Users/assef/Bineyame/AssetOpsV1-review/frontend/mockups/v69/index.html").href;
const S = "/sites/KOBO-001/work";
const STOCK = "from=2026-10-13T00:00:00Z&to=2026-10-21T00:00:00Z";
const EMPTY = "from=2026-09-01T00:00:00Z&to=2026-09-08T00:00:00Z";
const REFUSED = "from=2026-10-08T00:00:00Z&to=2026-10-01T00:00:00Z";
const CASES = [];
for (const kind of ["incidents", "maintenance"])
  for (const [state, q] of [["stocked", STOCK], ["empty", EMPTY], ["refused", REFUSED]])
    CASES.push({ screen: `sitework-${kind}`, kind, state, app: `${S}/${kind}?${q}` });
const SIZES = [[1440, 1000], [390, 900]];
// Caps: floor(1.30 x mock); the stocked five-row Incident panel cap at 1440 is 460 (S31).
const CAPS = {
  "sitework-incidents": { 1440: { status: 48, panel: 410, panelStocked: 460, notice: 54, page: 1431 }, 390: { status: 118, panel: 460, notice: 101, page: 1579 } },
  "sitework-maintenance": { 1440: { status: 48, panel: 384, panelStocked: 384, notice: 54, page: 1431 }, 390: { status: 118, panel: 410, notice: 101, page: 1579 } },
};
mkdirSync(OUT, { recursive: true });
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe",
  ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`,
   `--user-data-dir=${mkdtempSync(join(tmpdir(), "w401cap-"))}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let url = null;
for (let i = 0; i < 60 && !url; i++) {
  try { url = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page")?.webSocketDebuggerUrl; } catch {}
  if (!url) await sleep(250);
}
const ws = new WebSocket(url);
await new Promise((r) => ws.addEventListener("open", r));
let n = 0; const pending = new Map();
ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
const send = (method, params = {}) => new Promise((res, rej) => { const id = ++n; pending.set(id, (m) => m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result)); ws.send(JSON.stringify({ id, method, params })); });
const evalv = async (expression) => (await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true })).result.value;
await send("Page.enable"); await send("Runtime.enable");

// One measurement shape for both sides: the status strip, the panel and the notice (app and mock class names).
const MEASURE = `(async () => {
  await document.fonts.ready;
  const R = (e) => { if (!e) return null; const b = e.getBoundingClientRect(); return { y: Math.round(b.top + scrollY), w: Math.round(b.width), h: Math.round(b.height) }; };
  const main = document.querySelector("main") || document.body;
  const status = main.querySelector(".status-strip, .statusbar");
  const panel = main.querySelector("section.panel");
  const notice = main.querySelector("[data-work-notice], .notice");
  const sub = main.querySelector("nav[aria-label='Work lists'], .tabs.subtabs");
  const scroller = panel && panel.querySelector(".data-table__scroll, .table-wrap");
  const table = panel && panel.querySelector("table");
  const first = table && table.querySelector("tbody tr td:first-child");
  const clipped = Array.from(main.querySelectorAll("th, .status-strip span, .statusbar *, [data-work-state], .badge"))
    .filter((el) => el.scrollWidth > el.clientWidth + 1 && getComputedStyle(el).overflowX !== "visible").length;
  let stickyFirst = null;
  if (scroller && first && scroller.scrollWidth > scroller.clientWidth) {
    const before = first.getBoundingClientRect().left; scroller.scrollLeft = 200; await new Promise((r) => setTimeout(r, 50));
    stickyFirst = Math.round(first.getBoundingClientRect().left - before) === 0; scroller.scrollLeft = 0;
  }
  const hint = panel && panel.querySelector(".work-cases-scroll-hint");
  return { title: panel && panel.querySelector("h2")?.textContent.trim(), status: R(status), panel: R(panel), notice: R(notice),
    statusText: status ? status.textContent.replace(/\\s+/g, " ").trim().slice(0, 160) : null,
    emptyIcon: !!(panel && panel.querySelector("[data-work-empty] [data-work-empty-icon] svg[data-rail-icon='evidence']")),
    stripSpans: status ? status.querySelectorAll(":scope > span").length : 0,
    stripState: status ? status.querySelectorAll(".status-strip__state").length : 0,
    subrow: sub ? { h: Math.round(sub.getBoundingClientRect().height), scrollW: sub.scrollWidth, clientW: sub.clientWidth, labels: Array.from(sub.querySelectorAll("a")).map((a) => a.textContent.trim()) } : null,
    rows: table ? table.querySelectorAll("tbody tr").length : 0,
    cols: table ? Array.from(table.querySelectorAll("thead th")).map((th) => th.textContent.trim() + ":" + Math.round(th.getBoundingClientRect().width)) : [],
    tableScroll: scroller ? { client: scroller.clientWidth, scroll: scroller.scrollWidth } : null, stickyFirst,
    hintVisible: hint ? getComputedStyle(hint).display !== "none" : null,
    overflowX: document.documentElement.scrollWidth - innerWidth, clipped, pageH: document.documentElement.scrollHeight };
})()`;

async function shoot(target, w, h, file, ready) {
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: false });
  await send("Page.navigate", { url: target });
  for (let i = 0; i < 400; i++) { await sleep(150); if (await evalv(ready)) break; }
  await sleep(400);
  const m = await evalv(MEASURE);
  const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width: w, height: Math.min(m.pageH, 6000), scale: 1 } });
  writeFileSync(join(OUT, file), Buffer.from(shot.data, "base64"));
  return m;
}

const results = { revision: REV, captured_at: new Date().toISOString(), mock: {}, app: [], checks: [] };
for (const screen of ["sitework-incidents", "sitework-maintenance"]) for (const [w, h] of SIZES) {
  results.mock[`${screen}-${w}`] = await shoot(`${MOCK}#/${screen}`, w, h, `${screen}-${w}-mock.png`, `document.querySelectorAll("section.panel").length > 0`);
}
const fail = [];
for (const c of CASES) for (const [w, h] of SIZES) {
  const m = await shoot(`${BASE}${c.app}`, w, h, `${c.screen}-${c.state}-${w}-app.png`,
    `!!document.querySelector("main section.panel") && !/Loading the site's work records/.test(document.querySelector("main")?.textContent ?? "")`);
  const mock = results.mock[`${c.screen}-${w}`];
  const cap = CAPS[c.screen][w];
  const panelCap = w === 1440 && c.state === "stocked" ? cap.panelStocked : cap.panel;
  const row = { ...c, width: w, ...m, ratio: { status: +(m.status.h / mock.status.h).toFixed(2), panel: +(m.panel.h / mock.panel.h).toFixed(2), notice: +(m.notice.h / mock.notice.h).toFixed(2) } };
  results.app.push(row);
  // test_w401_stocked_five_rows_1440_and_390 and the empty/refused slot checks.
  const check = (ok, what) => { results.checks.push({ case: `${c.screen} ${c.state} ${w}`, what, ok }); if (!ok) fail.push(`${c.screen} ${c.state} ${w}: ${what}`); };
  check(m.title === mock.title, `panel title ${m.title} = mock ${mock.title}`);
  check(!!m.status && !!m.panel && !!m.notice, "status, panel and notice slots present");
  check(m.status.h <= cap.status, `status ${m.status.h} <= ${cap.status}`);
  check(m.panel.h <= panelCap, `panel ${m.panel.h} <= ${panelCap}`);
  check(m.notice.h <= cap.notice, `notice ${m.notice.h} <= ${cap.notice}`);
  check(m.pageH <= cap.page, `page ${m.pageH} <= ${cap.page}`);
  check(m.overflowX <= 0, `no page-level horizontal overflow (${m.overflowX})`);
  check(m.clipped === 0, `no clipped chip/header (${m.clipped})`);
  const want = { stocked: [/^Actions \(\d+\)$/, "Incidents (7)", "Maintenance (3)"], empty: ["Actions (0)", "Incidents (0)", "Maintenance (0)"],
    refused: ["Actions (—)", "Incidents (—)", "Maintenance (—)"] }[c.state];
  check(m.subrow && m.subrow.labels.length === 3 && m.subrow.labels.every((l, i) => (want[i] instanceof RegExp ? want[i].test(l) : l === want[i])),
    `one Work subrow, three live links with counts (${m.subrow && m.subrow.labels.join("|")})`);
  check(m.subrow.h <= 40, `subrow stays one row (${m.subrow.h})`);
  check(m.stripSpans === 3 && m.stripState === 0, `strip is lead, detail, Manage (${m.stripSpans}/${m.stripState})`);
  check(c.state === "empty" ? m.emptyIcon : true, "empty block carries the mock evidence icon");
  check(c.state === "empty" ? m.rows === 0 : true, "empty state has no rows");
  if (c.state === "stocked") {
    check(m.rows === 5 || (c.kind === "maintenance" && m.rows === 3), `stocked rows ${m.rows}`);
    if (w === 390) {
      check(m.tableScroll && m.tableScroll.scroll > m.tableScroll.client, `table scrolls in its own region (${JSON.stringify(m.tableScroll)})`);
      check(m.stickyFirst === true, "first column retained while scrolling");
      check(m.hintVisible === true, "scroll affordance visible");
    }
  } else check(m.rows === 0, `no row in ${c.state}`);
}
writeFileSync(join(OUT, "evidence.json"), JSON.stringify(results, null, 1));
for (const r of results.app) console.log(`${r.screen} ${r.state} ${r.width}: status ${r.status.h} panel ${r.panel.h} notice ${r.notice.h} page ${r.pageH} rows ${r.rows} ratio ${JSON.stringify(r.ratio)} overflowX ${r.overflowX} scroll ${JSON.stringify(r.tableScroll)} sticky ${r.stickyFirst} sub ${r.subrow?.h}/${r.subrow?.scrollW}/${r.subrow?.clientW}`);
for (const [k, m] of Object.entries(results.mock)) console.log(`mock ${k}: status ${m.status?.h} panel ${m.panel?.h} notice ${m.notice?.h} page ${m.pageH}`);
console.log(fail.length ? `test_w401_stocked_five_rows_1440_and_390 FAILED:\n  ${fail.join("\n  ")}` : `test_w401_stocked_five_rows_1440_and_390 passed (${results.checks.length} checks)`);
ws.close(); chrome.kill(); process.exit(fail.length ? 1 : 0);
