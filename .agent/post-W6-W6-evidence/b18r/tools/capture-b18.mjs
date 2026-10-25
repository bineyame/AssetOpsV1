/**
 * W6 recapture (cap-b18; CDP 9642, adds console warnings, a w6 DOM block and an optional probe5 DOM probe) of the post-W6 audit batch 18 capture wrapper (copied from batch 15, from batch 14, from batch 12, itself from batch 10) (CAPTURE-ONLY). Derived from tools/w1-fidelity-evidence.mjs (same
 * Chrome-over-CDP pattern, same panelStructure.ts title rule, same width guard). It only navigates to the given
 * URLs, waits for stable content, takes screenshots and measures the DOM. It never clicks, types, posts or
 * mutates anything; it adds per-panel structure (rows, columns, chips, links, disclosures), typography, colour,
 * shell-header, tab-row, clipped-text and scroll-container measurements to each pair.
 *
 *   node capture-b18.mjs <out-dir> <targets.json>
 * targets.json: [{ "id": "<mock id>", "case": "<case>", "url": "<app url>", "mock": "<mock hash id, default id>" }]
 * Optional per-target "openAll": true opens every <details> disclosure (viewer-only DOM toggle, no request, no
 * mutation) before measuring, for the all-disclosures-open state.
 * Environment: ASSETOPS_CDP_PORT (default 9528), AUDIT_REVISION.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const { widthGuard } = await import(pathToFileURL(resolve(here, "../../../../tools/evidence-checks.mjs")).href);
const OUT = process.argv[2];
const TARGETS = JSON.parse(readFileSync(process.argv[3], "utf8"));
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9642);
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [["1440", 1440, 1000], ["390", 390, 900]];
mkdirSync(OUT, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "assetops-w6r18r-cdp-"));
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
console.log(`chrome pid ${chrome.pid}`);
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
        const socket = new WebSocket(page.webSocketDebuggerUrl);
        await new Promise((res, rej) => { socket.addEventListener("open", res); socket.addEventListener("error", rej); });
        return socket;
      }
    } catch { /* not up yet */ }
    await sleep(250);
  }
  throw new Error("Chrome did not expose a page target");
}
let ws; let seq = 0; let consoleErrors = []; let consoleWarnings = []; const pending = new Map();
function send(method, params = {}) {
  seq += 1; const id = seq;
  return new Promise((res, rej) => {
    const timer = setTimeout(() => rej(new Error(`timeout ${method}`)), 60000);
    pending.set(id, (msg) => { clearTimeout(timer); msg.error ? rej(new Error(JSON.stringify(msg.error))) : res(msg.result); });
    ws.send(JSON.stringify({ id, method, params }));
  });
}
async function js(expression) {
  const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 400));
  return r.result.value;
}
async function waitFor(expression, ms = 30000) {
  const end = Date.now() + ms;
  while (Date.now() < end) { if (await js(`Boolean(${expression})`)) return true; await sleep(150); }
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
  await sleep(1200);
  await requireWidth(viewport[0], viewport[1], `loaded ${url}`);
  return ok;
}
async function shot(file) {
  const tall = await js(`Math.max(document.documentElement.scrollHeight,
    ...[...document.querySelectorAll('*')].filter(e => e.scrollHeight > e.clientHeight + 1 && getComputedStyle(e).overflowY !== 'visible')
      .map(e => e.scrollHeight + e.getBoundingClientRect().top))`);
  const h = Math.min(Math.ceil(tall), 9000);
  await send("Emulation.setDeviceMetricsOverride", { width: viewport[0], height: h, deviceScaleFactor: 1, mobile: viewport[0] < 600 });
  await sleep(300);
  const r = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(join(OUT, file), Buffer.from(r.data, "base64"));
  await size(viewport[0], viewport[1]);
}
const MEASURE = String.raw`(() => {
  const root = document.querySelector("main") ?? document.body;
  const txt = (e) => (e?.textContent ?? "").replace(/\s+/g, " ").trim();
  const hidden = (el) => {
    for (let n = el; n && n !== root; n = n.parentElement) {
      if (n.hidden || n.getAttribute("aria-hidden") === "true") return true;
      const p = n.parentElement;
      if (p && p.tagName === "DETAILS" && !p.open && n.tagName !== "SUMMARY") return true;
    }
    return false;
  };
  const sel = "section.panel, .panel, [data-headline-card]";
  const titles = []; const seen = new Set();
  for (const el of root.querySelectorAll("h2, " + sel)) {
    if (hidden(el)) continue;
    if (el.tagName === "H2") { const o = el.closest(sel); if (o) seen.add(o); titles.push(txt(el)); continue; }
    const own = [...el.querySelectorAll("h2")].find((h) => h.closest(sel) === el);
    if (!own && !seen.has(el)) titles.push("(untitled)");
  }
  const cs = (e) => e ? getComputedStyle(e) : null;
  const font = (e) => { const s = cs(e); return s ? { family: s.fontFamily.split(",")[0].replace(/"/g, "").trim(), size: s.fontSize, weight: s.fontWeight, lineHeight: s.lineHeight, color: s.color } : null; };
  const CHIP = ".badge, .chip, .v69-chip, [class*='chip'], [class*='badge']";
  const panels = [...root.querySelectorAll("section.panel")].filter((p) => !hidden(p) && !p.parentElement.closest("section.panel"))
    .map((p) => {
      const r = p.getBoundingClientRect(); const s = cs(p);
      const table = p.querySelector("table");
      return { title: txt(p.querySelector("h2")), x: Math.round(r.x), y: Math.round(r.y + scrollY), w: Math.round(r.width), h: Math.round(r.height),
        tables: p.querySelectorAll("table").length,
        rows: table ? table.querySelectorAll("tbody tr").length : 0,
        columns: table ? [...table.querySelectorAll("thead th")].map(txt) : [],
        chips: [...p.querySelectorAll(CHIP)].filter((c) => !c.parentElement.closest(CHIP)).map(txt).slice(0, 20),
        links: p.querySelectorAll("a[href]").length, buttons: p.querySelectorAll("button").length,
        details: p.querySelectorAll("details").length, rowText: table ? [...table.querySelectorAll("tbody tr")].slice(0, 12).map((tr) => [...tr.querySelectorAll("td, th")].map(txt)) : [], rowLinks: table ? [...table.querySelectorAll("tbody tr")].slice(0, 12).map((tr) => [...tr.querySelectorAll("a[href]")].map((a) => txt(a) + " -> " + a.getAttribute("href"))) : [], panelText: txt(p).slice(0, 600), h3: [...p.querySelectorAll("h3")].map(txt).slice(0, 12),
        background: s.backgroundColor, border: s.borderTopColor + " " + s.borderTopWidth, radius: s.borderTopLeftRadius };
    });
  const firstVisible = (q) => [...document.querySelectorAll(q)].find((e) => e.getBoundingClientRect().height > 0 && !hidden(e));
  const prose = firstVisible("main .prose, main .v69-prose, main p");
  const proseAll = [...root.querySelectorAll(".prose, .v69-prose")].filter((e) => e.getBoundingClientRect().height > 0).map((e) => getComputedStyle(e).fontSize);
  const header = firstVisible(".app-header, .topbar, body > header, #root > header, header");
  const hr = header ? header.getBoundingClientRect() : null;
  const h1 = firstVisible("main h1, h1"); const h1r = h1 ? h1.getBoundingClientRect() : null;
  const tabRows = [...document.querySelectorAll(".tabs, .site-tabs, .site-subtabs, [role='tablist']")]
    .filter((e) => e.getBoundingClientRect().height > 0)
    .map((e) => ({ cls: String(e.className).slice(0, 60), items: [...e.querySelectorAll("a, button, [role='tab'], span")].filter((a) => !a.parentElement.closest("a, button, span") && txt(a)).map((a) => txt(a) + ((a.getAttribute("aria-current") || a.classList.contains("active") || a.getAttribute("aria-selected") === "true") ? "*" : "") + ((a.getAttribute("aria-disabled") === "true" || a.tagName === "SPAN") ? "(off)" : "")) }));
  const clipped = [...root.querySelectorAll("*")].filter((e) => {
    if (!e.firstChild || hidden(e) || e.getBoundingClientRect().width === 0) return false;
    const s = getComputedStyle(e);
    if (s.position === "absolute" && (e.clientWidth <= 1 || e.clientHeight <= 1)) return false;
    const clipX = (s.overflowX === "hidden" || s.overflowX === "clip" || s.textOverflow === "ellipsis") && e.scrollWidth > e.clientWidth + 1;
    const clipY = (s.overflowY === "hidden" || s.overflowY === "clip") && e.scrollHeight > e.clientHeight + 2;
    return (clipX || clipY) && txt(e).length > 0;
  }).slice(0, 10).map((e) => ({ tag: e.tagName, cls: String(e.className).slice(0, 60), text: txt(e).slice(0, 80), sw: e.scrollWidth, cw: e.clientWidth, sh: e.scrollHeight, ch: e.clientHeight }));
  const hscroll = [...root.querySelectorAll("*")].filter((e) => { const s = getComputedStyle(e); return (s.overflowX === "auto" || s.overflowX === "scroll") && e.scrollWidth > e.clientWidth + 1 && e.clientWidth > 0; })
    .slice(0, 10).map((e) => ({ cls: String(e.className).slice(0, 60), sw: e.scrollWidth, cw: e.clientWidth, panel: txt(e.closest("section.panel")?.querySelector("h2")) }));
  const pSizes = {}; for (const e of root.querySelectorAll("section.panel p, section.panel li, section.panel dd")) { if (hidden(e) || e.getBoundingClientRect().height === 0) continue; const k = getComputedStyle(e).fontSize; pSizes[k] = (pSizes[k] ?? 0) + 1; }
  const lum = (c) => { const m = c.match(/\d+(\.\d+)?/g); if (!m || (m[3] !== undefined && Number(m[3]) === 0)) return 1; return (0.299 * m[0] + 0.587 * m[1] + 0.114 * m[2]) / 255; };
  const dark = [...document.body.querySelectorAll("*")].filter((e) => !root.contains(e) && !e.contains(root) && lum(getComputedStyle(e).backgroundColor) < 0.25)
    .map((e) => { const r = e.getBoundingClientRect(); return { cls: String(e.className).slice(0, 50), tag: e.tagName, x: Math.round(r.x), y: Math.round(r.y + scrollY), w: Math.round(r.width), h: Math.round(r.height) }; })
    .filter((d) => d.w * d.h > 0).sort((a, b) => b.w * b.h - a.w * a.h).slice(0, 2);
  const td = firstVisible("main td"); const th = firstVisible("main th"); const h2 = firstVisible("main h2");
  return { titles, panels, overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    pageH: document.documentElement.scrollHeight,
    header: hr ? { cls: String(header.className).slice(0, 60), h: Math.round(hr.height), bg: getComputedStyle(header).backgroundColor } : null,
    h1: h1 ? { text: txt(h1).slice(0, 120), top: Math.round(h1r.top + scrollY), ...font(h1) } : null,
    fonts: { body: font(document.body), prose: font(prose), proseSizes: [...new Set(proseAll)], h2: font(h2), td: font(td), th: font(th) },
    mini: (() => { const q = (x) => document.querySelector(x); const body = root.innerText; return { strip: txt(q("main .status-strip")), cards: [...root.querySelectorAll(".v69-cards .v69-metric")].map(txt), notice: [...root.querySelectorAll(".v69-notice")].map(txt), refusal: txt(q("main [data-page-refusal]")), refusalKey: q("main [data-page-refusal]")?.getAttribute("data-page-refusal") ?? null, notRecorded: (body.match(/Not recorded/g) || []).length, notAvailableYet: (body.match(/Not available yet/g) || []).length, prepared: body.includes("Prepared example data, not field readings"), enums: [...new Set(body.match(/\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b/g) || [])], uuids: (body.match(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/g) || []).length, utc: (body.match(/UTC|Z\b/g) || []).length, periodBar: txt(q("main form, main [data-mini-period], main [data-mini-hour]")).slice(0, 300), details: root.querySelectorAll("details").length, objective: [...root.querySelectorAll("[data-objective-card]")].map((c) => c.getAttribute("data-objective-card") + "|" + txt(c).slice(0, 160) + "|" + [...c.querySelectorAll("a[href]")].map((a) => txt(a) + " -> " + a.getAttribute("href")).join(" ; ")) }; })(), cold: (() => { const body = root.innerText; const q = (x) => document.querySelector(x); const win = q("main form[aria-label='Window'], main form[data-work-window]"); const wr = win ? win.getBoundingClientRect() : null;
      return { plural1: (body.match(/\b1 (incidents|maintenance requests|records|Actions|cases|findings)\b/gi) || []), evConnector: (body.match(/EV_CONNECTOR/g) || []).length,
        windowForm: win ? { x: Math.round(wr.x), w: Math.round(wr.width), h: Math.round(wr.height), text: txt(win).slice(0, 200), error: txt(win.querySelector("[role='alert']")) } : null,
        alerts: [...root.querySelectorAll("[role='alert']")].map(txt).slice(0, 5),
        cardLinks: [...root.querySelectorAll(".v69-cards > *")].map((c) => txt(c).slice(0, 90) + " | " + [...c.querySelectorAll("a[href]")].map((a) => txt(a) + " -> " + a.getAttribute("href")).join(" ; ")),
        svg: root.querySelectorAll("svg").length, readFull: [...root.querySelectorAll("summary")].filter((x) => /Read full text/.test(txt(x))).length,
        detailsOpen: [...root.querySelectorAll("details")].filter((d) => d.open).length }; })(), b15: (() => { const q = (x) => document.querySelector(x); const t = (e) => (e?.textContent ?? "").replace(/\s+/g, " ").trim();
      return { crumbs: t(q("nav[aria-label*='readcrumb' i], .breadcrumb, .breadcrumbs")), subtitle: t(q("main header p, main .page-subtitle, main .subtitle")).slice(0, 200),
        headerButtons: [...document.querySelectorAll("main header a, main header button")].map(t).filter(Boolean).slice(0, 8),
        strip: t(q("[data-domain-action-strip], main .status-strip, [data-site-work-scope]")).slice(0, 400),
        related: t(q("[data-domain-action-related-sentence]")), inspect: (() => { const e = q("[data-domain-action-inspect]"); return e ? { tag: e.tagName, text: t(e), disabled: e.disabled === true || e.getAttribute("aria-disabled") === "true", href: e.getAttribute("href") } : null; })(),
        finding: t(q("[data-domain-action-finding-control]")), intentMissing: t(q("[data-domain-action-intent-missing]")),
        criteria: [...document.querySelectorAll("[data-domain-action-criterion]")].map(t).slice(0, 8),
        showing: t(q("[data-site-work-pages]")).slice(0, 160), rowStates: [...document.querySelectorAll("[data-work-state]")].map((e) => e.getAttribute("data-work-state") + "=" + t(e)).slice(0, 12),
        bodyText: root.innerText.replace(/\s+/g, " ").slice(0, 2500) }; })(), b18: (() => { const q = (x) => document.querySelector(x); const t = (e) => (e?.textContent ?? "").replace(/\s+/g, " ").trim(); const body = root.innerText;
      return { status: t(q("[data-global-work-status], main .status-strip, main [data-global-work-provenance]")).slice(0, 300), showing: t(q("[data-global-work-showing]")),
        pager: [...document.querySelectorAll("main button, main a")].filter((e) => /^(Next|Previous|First page|Back to first page)/i.test(t(e))).map((e) => t(e) + (e.disabled ? "(disabled)" : "") + (e.getAttribute("href") ? " -> " + e.getAttribute("href").slice(0, 80) : "")),
        siteLinks: [...document.querySelectorAll("[data-global-work-site]")].map((e) => e.getAttribute("data-global-work-site") + " -> " + (e.getAttribute("href") ?? "(text)")),
        workLinks: [...document.querySelectorAll("[data-global-work-link]")].map((e) => t(e) + " -> " + (e.getAttribute("href") ?? "(text)")).slice(0, 20),
        chipsTop: [...root.querySelectorAll("[role='tablist'] a, .chips a, .chip, [data-global-work-kind] a, [data-operational-kind] a")].map((e) => t(e) + (e.getAttribute("aria-current") ? "*" : "")).slice(0, 20),
        windowInputs: [...root.querySelectorAll("input[type='date'], input[type='datetime-local'], select")].map((e) => e.name + "=" + e.value),
        alerts: [...root.querySelectorAll("[role='alert'], [role='status']")].map(t).filter(Boolean).slice(0, 6),
        plural1: (body.match(/\b1 (incidents|requests|plans|records|cases|maintenance)\b/gi) || []), evConnector: (body.match(/EV_CONNECTOR/g) || []).length,
        assetLabels: [...new Set(body.match(/\b[a-z0-9]+ · [A-Z_]+\b/g) || [])].slice(0, 10), enums: [...new Set(body.match(/\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b/g) || [])].slice(0, 20),
        utcHits: (body.match(/UTC/g) || []).length, bodyText: body.replace(/\s+/g, " ").slice(0, 3000) }; })(), mainLinks: [...root.querySelectorAll("a[href]")].map((a) => txt(a).slice(0, 60) + " -> " + a.getAttribute("href")).slice(0, 60), cardsDom: [...root.querySelectorAll(".v69-cards > *, [data-estate-cards] > *")].map((c) => ({ t: txt(c).slice(0, 80), h: Math.round(c.getBoundingClientRect().height) })), tabRows, clipped, hscroll, pSizes, dark, mainTop: Math.round(root.getBoundingClientRect().top + scrollY), viewportH: innerHeight };
})()`;
const W6 = String.raw`(() => {
  const t = (e) => (e?.textContent ?? "").replace(/\s+/g, " ").trim(); const q = (x) => document.querySelector(x);
  const op = q("main [data-global-work-root] table, main section.panel table");
  const wrap = op ? op.parentElement : null;
  const sel = q("[data-global-work-form-site]"); const tm = q("[data-global-work-form-time]");
  return { url: location.href, title: document.title, h1: t(q("main h1, h1")),
    crumbs: t(q("nav[aria-label*='readcrumb' i], .breadcrumbs, .breadcrumb")),
    status: [...document.querySelectorAll("[data-global-work-status]")].map(t),
    membership: [...document.querySelectorAll("[data-global-work-membership]")].map(t),
    deviations: [...document.querySelectorAll("[data-mock-deviation]")].map((e) => e.getAttribute("data-mock-deviation") + "|" + t(e).slice(0, 160) + "|" + getComputedStyle(e).fontSize),
    showing: t(q("[data-global-work-showing]")),
    findings: [...document.querySelectorAll("[data-global-work-findings], [data-global-work-source]")].map((e) => t(e).slice(0, 120) + " | anchors=" + [...e.querySelectorAll("a[href]")].map((a) => a.getAttribute("href")).join(" ; ")).slice(0, 12),
    requestLinks: [...document.querySelectorAll("[data-global-work-request-link]")].map((e) => t(e) + " -> " + (e.getAttribute("href") ?? "(text)")).slice(0, 12),
    rowLinks: [...document.querySelectorAll("main tbody a[href]")].map((a) => t(a).slice(0, 50) + " -> " + a.getAttribute("href")).slice(0, 40),
    siteLinks: [...document.querySelectorAll("[data-global-work-site]")].map((e) => t(e) + " -> " + (e.getAttribute("href") ?? "(text)")),
    form: sel || tm ? { siteOptions: sel ? [...sel.options].map((o) => o.value + "=" + o.text) : null, timeValue: tm ? tm.value : null, timePlaceholder: tm ? tm.placeholder : null,
      formText: t(q("[data-global-work-manual-form]")).slice(0, 400) } : null,
    table: op ? { tag: op.tagName, sw: op.scrollWidth, cw: op.clientWidth, w: Math.round(op.getBoundingClientRect().width), layout: getComputedStyle(op).tableLayout,
      wrapCls: String(wrap?.className ?? "").slice(0, 60), wrapSw: wrap?.scrollWidth, wrapCw: wrap?.clientWidth,
      cols: [...op.querySelectorAll("thead th")].map((th) => t(th) + ":" + Math.round(th.getBoundingClientRect().width)),
      over: (() => { const R = op.getBoundingClientRect().right; return [...op.querySelectorAll("tbody td *, tbody td")].filter((e) => e.getBoundingClientRect().right > R + 1 || e.scrollWidth > e.clientWidth + 1 && e.clientWidth > 0).slice(0, 8).map((e) => e.tagName + "." + String(e.className).slice(0, 40) + " ws=" + getComputedStyle(e).whiteSpace + " col=" + (e.closest("td")?.cellIndex) + " r=" + Math.round(e.getBoundingClientRect().right) + " sw=" + e.scrollWidth + " cw=" + e.clientWidth + " t=" + t(e).slice(0, 30)); })(),
      rowH: [...op.querySelectorAll("tbody tr")].slice(0, 8).map((r) => Math.round(r.getBoundingClientRect().height)) } : null,
    historicalNotice: [...document.querySelectorAll("main .v69-notice, main [data-global-work-notice], main [role='note']")].map(t).slice(0, 4),
    tabs: [...document.querySelectorAll("main nav a, main nav span, [data-global-work-tab]")].map((e) => t(e)).filter(Boolean).slice(0, 12) };
})()`;
const PROBE5 = String.raw`(() => {
  const tb = document.querySelector("main section.panel table tbody"); if (!tb || !tb.rows.length) return false;
  const long = "Probe text ".repeat(20).slice(0, 160);
  const base = tb.rows[0]; while (tb.rows.length < 5) tb.appendChild(base.cloneNode(true));
  [...tb.rows].slice(0, 5).forEach((r) => [...r.cells].forEach((c) => { c.querySelectorAll("a, span, p, div").forEach((n) => { if (!n.children.length && !/badge|chip/.test(String(n.className))) n.textContent = long; }); if (!c.children.length) c.textContent = long; }));  // enum State/Type chips (badge|chip) keep their value: not variable text fields (Q15)
  return true;
})()`;
const evidence = { revision: process.env.AUDIT_REVISION ?? null, captured_at: new Date().toISOString(), pairs: [] };
try {
  ws = await connect();
  ws.addEventListener("message", (event) => { const msg = JSON.parse(event.data);
    if (msg.method === "Runtime.exceptionThrown") consoleErrors.push(String(msg.params.exceptionDetails?.exception?.description ?? msg.params.exceptionDetails?.text).slice(0, 300));
    if (msg.method === "Runtime.consoleAPICalled" && msg.params.type === "warning") consoleWarnings.push(msg.params.args.map((a) => a.value ?? a.description ?? "").join(" ").slice(0, 300));
    if (msg.method === "Runtime.consoleAPICalled" && msg.params.type === "error") consoleErrors.push(msg.params.args.map((a) => a.value ?? a.description ?? "").join(" ").slice(0, 300));
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); } });
  await send("Page.enable"); await send("Runtime.enable");
  for (const t of TARGETS) {
    const name = `${t.id}-${t.case}`;
    const mockUrl = `${new URL(t.url).origin}/mockups/v69/index.html#/${t.mock ?? t.id}`;
    for (const [label, width, height] of WIDTHS) {
      await size(width, height);
      consoleErrors = []; consoleWarnings = [];
      const appReady = await go(t.url, String.raw`document.querySelector("main h2, main [data-page-refusal], main h1") && ![...document.querySelectorAll("main p")].some((p) => /^Loading [^.]+\.$/.test(p.textContent.trim()))`);
      claim(`${name} ${label}: app rendered`, appReady);
      if (t.openAll) { await js(`[...document.querySelectorAll("main details")].forEach((d) => { d.open = true; d.dispatchEvent(new Event("toggle")); }); true`); await sleep(600); }
      if (t.probe5) { await js(PROBE5); await sleep(600); }  // capture-only DOM probe (Q15/Q16): five rows, 160-char text cells; viewer-only, no request
      const app = await js(MEASURE);
      app.w6 = await js(W6);
      app.consoleErrors = [...new Set(consoleErrors)].slice(0, 5);
      app.consoleWarnings = [...new Set(consoleWarnings)].slice(0, 5);
      await shot(`${name}-${label}-app.png`);
      const mockReady = await go(mockUrl, `document.querySelector("main section.panel h2")`);
      claim(`${name} ${label}: mock rendered`, mockReady);
      const mock = await js(MEASURE);
      await shot(`${name}-${label}-mock.png`);
      claim(`${name} ${label}: same panel count`, app.titles.length === mock.titles.length, { app: app.titles, mock: mock.titles });
      claim(`${name} ${label}: no app page overflow`, app.overflowX <= 0, { overflowX: app.overflowX });
      evidence.pairs.push({ screen: t.id, case: t.case, viewport: `${width}x${height}`, app_url: t.url, mock_hash: `#/${t.mock ?? t.id}`,
        app_image: `${name}-${label}-app.png`, mock_image: `${name}-${label}-mock.png`, app, mock });
    }
  }
} catch (error) {
  claim("capture run completed", false, String(error));
} finally {
  writeFileSync(join(OUT, "evidence.json"), JSON.stringify(evidence, null, 2));
  ws?.close(); chrome.kill();
}
const failed = results.filter((r) => !r.ok);
console.log(`\n${results.length - failed.length}/${results.length} claims passed; evidence in ${OUT}`);
