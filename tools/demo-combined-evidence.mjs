/**
 * DEMO-B B1: browser captures of the combined three-Site demo dataset (DEMO-COMBINED §6, DEMO-SPARSE calendar).
 *
 *   node tools/demo-combined-evidence.mjs capture <work-dir> <out-dir> [web-base]
 *   node tools/demo-combined-evidence.mjs mock-ids
 *   node tools/demo-combined-evidence.mjs compare <out-dir> <mock-measure.json>
 *
 * capture: reads <work-dir>/story.json, kobo.json and days.json (written by `tools/demo_combined.py prepare`) for the
 *   story day S and the record ids, then opens each listed screen on <web-base> (default http://localhost:5490, the
 *   `serve` frontend) at 1440 and 390 px in its own headless Chrome. Per capture it waits for the reads to settle (no
 *   "Loading" sentence in <main>, text stable), writes a full-page PNG, and measures the same blocks as
 *   tools/measure-mock-panels.mjs (cards, status bar, panels, notices) plus document overflow. It also scans the
 *   visible text for words a client should not see (codes, enum names, ids, developer terms) and records each hit
 *   with its context. Writes <out>/product-measure.json and <out>/captures.json. `serve` must be running (it ticks
 *   every 120 s); a stale build reads STALE_PROJECTION, which this tool records but does not fix.
 * mock-ids: prints the v70 screen ids the captures map to, for
 *   `node tools/measure-mock-panels.mjs --mock frontend/mockups/v70 <out> <ids...>`.
 * compare: pairs every product capture with its mock measurement (same width) and writes <out>/comparison.json:
 *   panel headings in the mock and not on the product and the reverse, card counts, page height ratio, and
 *   horizontal overflow. It reports differences; triage into register rows or polish defects is the reviewer's.
 *
 * POLISH PB-0 (build sheet §2, §5 PB-0, Addendum 1):
 *   DEMOB_STRICT=1        exit 1 when any capture records a counted vocabulary hit (the strict client-mode gate).
 *   DEMOB_REVIEW_LABELS=1 open `/?review=labels` once before capturing (review mode for MOCK DEVIATION labels); label
 *                         hits are then recorded but not counted.
 *   The vocabulary scan and its region rules live in tools/demo-combined-vocabulary.mjs (Addendum 5): ids are checked
 *   on all visible <main> text except `[data-technical-details]`; `[data-vocabulary-exempt]` exempts product kinds
 *   only and `[data-time-zone-note]` only "UTC"; "MOCK DEVIATION" is never exempt; exempt hits go to `exempt_hits`.
 *   The `-open` stress capture counts ids and "MOCK DEVIATION" only. Settling also waits for no `[aria-busy="true"]` and no
 *   `[data-repeat-check="loading"]` in <main>, and treats only whole loading lines as loading (`mainSettled`).
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { SETTLE_PROBE, mainSettled, widthGuard } from "./evidence-checks.mjs";
import { CAPTURE_TEXTS, classifyCapture } from "./demo-combined-vocabulary.mjs";

const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9491);
const WIDTHS = [[1440, 1000], [390, 900]];
const DAY = 86400000;
const iso = (ms) => new Date(ms).toISOString().replace(/\.000Z$/, "Z");
const [CMD, ...REST] = process.argv.slice(2);

/** The capture list (DEMO-COMBINED §6 B1 on the DEMO-SPARSE days). `mock` is the v70 screen id compared against. */
function screens(work) {
  const story = JSON.parse(readFileSync(join(work, "story.json"), "utf-8"));
  const kobo = JSON.parse(readFileSync(join(work, "kobo.json"), "utf-8"));
  const days = JSON.parse(readFileSync(join(work, "days.json"), "utf-8")).days;
  const S = Date.parse(story.S);
  // The board renders on the Site Overview (`/sites/{code}/outcomes` and `/sites/{code}/overview`, which `demo_combined.py links` prints, are not routes). The
  // mini Overview takes `date`; the cold Overview (`/sites/{code}`) and the EV Overview (`/sites/{code}/ev`) take the `from`/`to` window.
  // Cold and EV boards read on their event window (DEMO-SPARSE Addendum 1 (a): "The EV board is checked on its event
  // window"; the build's own CO-7/CO-9 rows read days.json `start`/`end`). A whole-day EV window reads Unknown.
  const event = (site, kind) => {
    const d = days.find((x) => x.site === site && x.kind === kind);
    if (!d?.start || !d?.end) throw new Error(`days.json has no ${site} ${kind} start/end`);
    return `/sites/${site === "ev" ? "EV-LAB-001/ev" : "COLD-LAB-001"}?from=${d.start}&to=${d.end}`;
  };
  const board = (code, at) => code === "KOBO-001"
    ? `/sites/${code}?date=${iso(at).slice(0, 10)}`
    : `/sites/${code}${code.startsWith("EV-") ? "/ev" : ""}?from=${iso(at)}&to=${iso(at + DAY)}`;
  const week = `from=${iso(S - 6 * DAY)}&to=${iso(S + DAY)}`;
  // 31 days (the work index maximum) ending S+3: the global work lists place a record by its recorded time, which is
  // the build day (S+2), not the story day it occurred on, so the window must reach the build day to list anything.
  const month = `from=${iso(S - 28 * DAY)}&to=${iso(S + 3 * DAY)}`;
  return {
    story,
    list: [
      { key: "portfolio-week", label: "Portfolio, week to story day S", path: `/portfolio?${week}`, mock: "portfolio" },
      { key: "kobo-board-S", label: "Kobo board, day S (trial-before)", path: board("KOBO-001", S), mock: "mini" },
      { key: "kobo-board-S-open", label: "Kobo board, day S, every disclosure open", path: board("KOBO-001", S), mock: "mini", open: true },
      { key: "kobo-board-S1", label: "Kobo board, day S+1 (trial-after)", path: board("KOBO-001", S + DAY), mock: "mini" },
      // WALK1-5 Addendum 7 (G2, replaces `kobo-whatif`): the productive-use opportunity page reached from the S+1
      // board's Opportunity issue (Renewable evaluation, then its opportunity link); finish row WK-6 pins its Tariff.
      { key: "kobo-opportunity", label: "Kobo productive-use opportunity, from the S+1 board's Opportunity issue", find: board("KOBO-001", S + DAY),
        hops: ['main a[href*="/performance/renewable"]', 'main a[href*="/opportunities/"]'], mock: "opportunity-finding" },
      // WALK1-2 review L3 (G1): the lead Finding's version history, where each version's Basis disclosure nests the
      // related-findings detail; nothing else captures that cell at desktop width.
      { key: "finding-history", label: "Kobo lead finding, version history", path: `/sites/KOBO-001/findings/${kobo.finding}/history?revision_id=${kobo.finding_revision}`, mock: "finding-history" },
      { key: "kobo-verification", label: `${kobo.action_code} verification with its cost check (CO-4)`, path: `/sites/KOBO-001/actions/${kobo.action}/verification`, mock: "verification" },
      { key: "cold-board-failure", label: "GreenHarvest board, failure night (S), event window", path: event("cold", "failure"), mock: "cold" },
      { key: "cold-board-normal", label: "GreenHarvest board, normal night (S-7), event window", path: event("cold", "normal"), mock: "cold" },
      { key: "ev-board-fault", label: "Depot board, fault Tuesday, event window E", path: event("ev", "fault"), mock: "ev" },
      { key: "findings-all", label: "Estate Findings, all", path: `/findings?${week}`, mock: "findings" },
      { key: "findings-cost", label: "Estate Findings, Cost lens", path: `/findings/cost?${week}`, mock: "findings-cost" },
      { key: "findings-risks", label: "Estate Findings, Risks lens", path: `/findings/risks?${week}`, mock: "findings-risks" },
      { key: "findings-opportunities", label: "Estate Findings, Opportunities lens", path: `/findings/opportunities?${week}`, mock: "findings-opportunities" },
      { key: "maintenance-preventive", label: "Maintenance, Preventive (31 days to S+3)", path: `/maintenance/preventive?${month}`, mock: "maintenance-preventive" },
      { key: "wr-overview", label: "Work request overview (the cold starter/control inspection on Maintenance; else the first request)", find: `/maintenance?${month}`, mock: "wr-overview" },
    ].filter((s) => !ONLY || ONLY.includes(s.key)),
  };
}
const ONLY = process.env.DEMOB_ONLY ? process.env.DEMOB_ONLY.split(",") : null;
const STRICT = process.env.DEMOB_STRICT === "1";
const REVIEW_LABELS = process.env.DEMOB_REVIEW_LABELS === "1";

const MEASURE = `(()=>{const R=e=>{const b=e.getBoundingClientRect();return {top:Math.round(b.top+scrollY),h:Math.round(b.height),w:Math.round(b.width)}};
 const main=document.querySelector('main')||document.body; const out=[];
 const SEL='.cards,.v69-cards,.statusbar,.v69-statusbar,section.panel,.notice';
 for(const e of main.querySelectorAll(SEL)){ if(e.closest('section.panel')&&!e.matches('section.panel')) continue;
   const kind=e.matches('.cards,.v69-cards')?'cards':e.matches('.statusbar,.v69-statusbar')?'statusbar':e.matches('.notice')?'notice':'panel';
   const title=kind==='panel'?(e.querySelector('h2,h3')?.textContent||'').trim():kind==='cards'?[...e.querySelectorAll('.metric-label,.v69-metric__label')].map(x=>x.textContent).join(' | '):e.textContent.trim().slice(0,80);
   const o={kind,title,...R(e)}; if(kind==='cards') o.children=[...e.children].map(R);
   const tw=e.querySelector('.table-wrap,.data-table-wrap,table'); if(tw){o.tableClient=tw.clientWidth;o.tableScroll=tw.scrollWidth;}
   out.push(o);}
 const wide=[...main.querySelectorAll('*')].filter(e=>{const b=e.getBoundingClientRect();return b.width>0&&b.right>document.documentElement.clientWidth+1&&!e.closest('[class*=scroll],[class*=table-wrap],.cell-disclosure')}).slice(0,5).map(e=>(e.className||e.tagName)+'');
 const h1=document.querySelector('h1');
 return {h1:h1?.textContent.trim(), pageH:document.documentElement.scrollHeight, docScrollW:document.documentElement.scrollWidth, clientW:document.documentElement.clientWidth, wide, items:out, text:main.innerText};})()`;

async function capture([work, out, base = "http://localhost:5490"]) {
  if (!work || !out) throw new Error("usage: capture <work-dir> <out-dir> [web-base]");
  const { story, list } = screens(work);
  mkdirSync(out, { recursive: true });
  const profile = mkdtempSync(join(tmpdir(), "assetops-demob-cdp-"));
  const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
  console.log(`chrome pid ${chrome.pid}`);
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  let ws;
  // DEMO-B review L4: Chrome is stopped and its profile removed whatever happens below (no orphan headless Chrome).
  try {
  for (let i = 0; i < 80 && !ws; i += 1) {
    try {
      const p = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page");
      if (p) { ws = new WebSocket(p.webSocketDebuggerUrl); await new Promise((a, b) => { ws.onopen = a; ws.onerror = b; }); }
    } catch { ws = undefined; }
    if (!ws) await sleep(250);
  }
  if (!ws) throw new Error("Chrome did not expose a page target");
  let seq = 0;
  const pending = new Map();
  ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } };
  const send = (method, params = {}) => new Promise((res, rej) => {
    const id = ++seq;
    const t = setTimeout(() => rej(new Error(`timeout ${method}`)), 60000);
    pending.set(id, (m) => { clearTimeout(t); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); });
    ws.send(JSON.stringify({ id, method, params }));
  });
  const js = async (expression) => {
    const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) throw new Error(`page eval: ${JSON.stringify(r.exceptionDetails).slice(0, 300)}`);
    return r.result.value;
  };
  const requireWidth = widthGuard({ send });
  /** Settled: `mainSettled` (no loading line, no aria-busy, no loading repeat check), text unchanged over three reads 600 ms apart. */
  const settle = async () => {
    const end = Date.now() + 60000;
    let last = "";
    let same = 0;
    while (Date.now() < end) {
      const probe = await js(SETTLE_PROBE);
      const t = probe.text;
      const busy = !mainSettled(probe);
      same = !busy && t === last ? same + 1 : 0;
      last = t;
      if (same >= 3) return true;
      await sleep(600);
    }
    return false;
  };
  const openAll = async () => {
    for (let round = 0; round < 4; round += 1) {
      const n = await js(`(()=>{const m=document.querySelector('main');let n=0;
        for(const d of m.querySelectorAll('details:not([open])')){d.open=true;n++;}
        for(const b of m.querySelectorAll('button[aria-expanded="false"]')){b.click();n++;}
        return n;})()`);
      if (!n) break;
      await sleep(800);
      await settle();
    }
  };
  await send("Page.enable");
  if (REVIEW_LABELS) {
    // POLISH §2: review mode is session-scoped, so one visit per tab turns the labels on for every capture after it.
    await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
    await send("Page.navigate", { url: `${base}/?review=labels` });
    await requireWidth(1440, 1000, "review labels", { record: false });
    await settle();
    const on = await js(`document.documentElement.dataset.reviewLabels === "on"`);
    console.log(`review labels ${on ? "on" : "NOT on (this build has no review mode)"}`);
  }
  const measures = [];
  const records = [];
  for (const s of list) {
    let path = s.path;
    if (s.find) {
      await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
      await requireWidth(1440, 1000, `${s.key} find`, { record: false });
      await send("Page.navigate", { url: base + s.find });
      await settle();
      await requireWidth(1440, 1000, `${s.key} find loaded`, { record: false });
      if (s.hops) {
        // Follow each link in turn from the found page (WALK1-5: board issue, then the opportunity link).
        path = null;
        for (const [i, sel] of s.hops.entries()) {
          path = await js(`(()=>{const a=document.querySelector(${JSON.stringify(sel)});return a?new URL(a.href).pathname+new URL(a.href).search:null})()`);
          if (!path) break;
          if (i < s.hops.length - 1) { await send("Page.navigate", { url: base + path }); await settle(); }
        }
        if (!path) { records.push({ ...s, error: `no link along ${s.hops.join(" > ")} from ${s.find}` }); console.log(`FAIL  ${s.key}: no link along its hops`); continue; }
      } else {
        path = await js(`(()=>{const a=[...document.querySelectorAll('main a[href*="/maintenance/requests/"]')];const p=a.find(x=>/starter.control|control-circuit/i.test(x.closest('tr')?.innerText??x.innerText))??a[0];return p?new URL(p.href).pathname+new URL(p.href).search:null})()`);
        if (!path) { records.push({ ...s, error: `no work request link on ${s.find}` }); console.log(`FAIL  ${s.key}: no work request link`); continue; }
      }
    }
    for (const [w, h] of WIDTHS) {
      await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: w < 600 });
      await requireWidth(w, h, `${s.key} ${w}`, { record: false });
      await send("Page.navigate", { url: base + path });
      const settled = await settle();
      if (s.open) await openAll();
      await requireWidth(w, h, `${s.key} ${w} measure`, { record: false });
      const m = await js(MEASURE);
      const file = join(out, `${s.key}-${w}.png`);
      const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true });
      writeFileSync(file, Buffer.from(shot.data, "base64"));
      // Whole-diff review M2: the visible <main> text beside each PNG, so register rows can be checked against it.
      writeFileSync(join(out, `${s.key}-${w}.txt`), m.text ?? "", "utf-8");
      // Addendum 5: ids everywhere but Technical details; exemptions for product kinds only; exempt hits recorded.
      const { vocabulary: hits, exempt_hits, counted } = classifyCapture(await js(CAPTURE_TEXTS), { open: !!s.open, reviewLabels: REVIEW_LABELS });
      const states = [...new Set((m.text.match(/\b(?:STALE_PROJECTION|SCHEDULE_STOPPED|PRODUCER_NOT_SETTLED|UNASSESSED)\b/g) ?? []))];
      const { text, ...rest } = m;
      measures.push({ key: s.key, mock: s.mock, width: w, url: base + path, settled, ...rest });
      records.push({ key: s.key, label: s.label, mock: s.mock, width: w, url: base + path, png: file, settled, h1: m.h1, pageH: m.pageH, overflow: m.docScrollW > m.clientW, stale_words: states, vocabulary: hits, vocabulary_counted: counted, exempt_hits });
      console.log(`${settled ? "OK  " : "WAIT"}  ${s.key} ${w}  h1=${JSON.stringify(m.h1)} pageH=${m.pageH} overflow=${m.docScrollW > m.clientW} vocab=${hits.length} counted=${counted} exempt=${exempt_hits.length}`);
    }
  }
  writeFileSync(join(out, "product-measure.json"), JSON.stringify(measures, null, 1));
  const counted = records.reduce((n, r) => n + (r.vocabulary_counted ?? 0), 0);
  writeFileSync(join(out, "captures.json"), JSON.stringify({ story_S: story.S_date, code: story.code, base, strict: STRICT, review_labels: REVIEW_LABELS, vocabulary_counted: counted, captures: records }, null, 1));
  console.log(`wrote ${records.length} captures to ${out}`);
  // DEMO-B review L4: an unsettled (WAIT) capture or a missing work request fails the run; its files stay for reading.
  const bad = records.filter((r) => r.error || r.settled === false);
  if (bad.length) console.log(`FAIL  ${bad.length} capture(s) unsettled or missing: ${bad.map((r) => `${r.key}${r.width ? ` ${r.width}` : ""}`).join(", ")}`);
  console.log(`vocabulary: ${counted} counted hit(s) across ${records.length} capture(s)${STRICT ? " (strict)" : ""}`);
  if (STRICT && counted) console.log(`FAIL  strict gate: ${counted} vocabulary hit(s); see captures.json "vocabulary"`);
  return bad.length || (STRICT && counted) ? 1 : 0;
  } finally {
    try { ws?.close(); } catch { /* already closed */ }
    chrome.kill();
    await sleep(500);
    try { rmSync(profile, { recursive: true, force: true }); } catch { /* Chrome may still hold the profile */ }
  }
}

function compare([out, mockFile]) {
  if (!out || !mockFile) throw new Error("usage: compare <out-dir> <mock-measure.json>");
  const product = JSON.parse(readFileSync(join(out, "product-measure.json"), "utf-8"));
  const mock = JSON.parse(readFileSync(mockFile, "utf-8"));
  const norm = (t) => (t ?? "").toLowerCase().replace(/[^a-z ]+/g, " ").replace(/\s+/g, " ").trim();
  const rows = [];
  for (const p of product) {
    const m = mock.find((x) => x.screen === p.mock && x.width === p.width);
    if (!m) { rows.push({ key: p.key, width: p.width, mock: p.mock, error: "no mock measurement" }); continue; }
    const titles = (x) => x.items.filter((i) => i.kind === "panel" && i.title).map((i) => norm(i.title));
    const mt = titles(m);
    const pt = titles(p);
    const cards = (x) => x.items.filter((i) => i.kind === "cards").reduce((n, i) => n + (i.children?.length ?? 0), 0);
    rows.push({
      key: p.key, width: p.width, mock: p.mock,
      h1: { mock: m.h1, product: p.h1 },
      panels: { mock: mt.length, product: pt.length },
      missing_panels: mt.filter((t) => !pt.includes(t)),
      extra_panels: pt.filter((t) => !mt.includes(t)),
      cards: { mock: cards(m), product: cards(p) },
      pageH: { mock: m.pageH, product: p.pageH, ratio: Math.round((p.pageH / m.pageH) * 100) / 100 },
      overflow: { mock: m.docScrollW > m.clientW, product: p.docScrollW > p.clientW, wide: p.wide },
    });
  }
  writeFileSync(join(out, "comparison.json"), JSON.stringify(rows, null, 1));
  for (const r of rows) {
    if (r.error) { console.log(`${r.key} ${r.width}: ${r.error}`); continue; }
    console.log(`${r.key} ${r.width} vs ${r.mock}: panels ${r.panels.mock}/${r.panels.product} missing ${r.missing_panels.length} extra ${r.extra_panels.length} cards ${r.cards.mock}/${r.cards.product} pageH x${r.pageH.ratio} overflow ${r.overflow.product}`);
  }
}

if (CMD === "capture") process.exitCode = await capture(REST);
else if (CMD === "compare") compare(REST);
else if (CMD === "mock-ids") {
  const ids = ["portfolio", "mini", "finding-history", "verification", "cold", "ev", "findings", "findings-cost", "findings-risks", "findings-opportunities", "maintenance-preventive", "wr-overview", "opportunity-finding"];
  console.log(ids.join(" "));
} else {
  console.error("usage: see the header of tools/demo-combined-evidence.mjs");
  process.exit(2);
}
process.exit(process.exitCode ?? 0);
