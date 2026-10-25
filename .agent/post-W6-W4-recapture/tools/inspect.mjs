// post-W6 W4 recapture (copied from W2-cold inspect.mjs; adds the bar/chip contrast read for build ruling 4). Origin: W2-cold recapture: behaviour inspection + capped-panel measurement + labelled synthetic DOM probe.
// CAPTURE-ONLY. Navigates the real mounted page, reads the DOM, opens disclosures in the browser only and, for the
// probe, replaces rendered rows/fields in that browser session only (never persisted, never posted).
// Probe output is SYNTHETIC LAYOUT EVIDENCE, NOT PRODUCT DATA (Architect W3 closeout ruling 1 method).
//   node inspect.mjs <out-dir> <targets.json>
//   targets: [{ id, case, url, caps?: [{ panel: "<h2 prefix>", kind: "rows" | "conclusion" }] }]
// Env: ASSETOPS_CDP_PORT (default 9561), AUDIT_REVISION.
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [OUT, TFILE] = process.argv.slice(2);
const TARGETS = JSON.parse(readFileSync(TFILE, "utf8"));
const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9595);
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const WIDTHS = [[1440, 1000], [390, 900]];
mkdirSync(OUT, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "assetops-w4rc-insp-"));
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
console.log(`chrome pid ${chrome.pid}`);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let ws; let seq = 0; let consoleErrors = []; const pending = new Map();
async function connect() {
  for (let i = 0; i < 240; i += 1) {
    try {
      const page = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page");
      if (page?.webSocketDebuggerUrl) { const s = new WebSocket(page.webSocketDebuggerUrl); await new Promise((res, rej) => { s.addEventListener("open", res); s.addEventListener("error", rej); }); return s; }
    } catch { /* not up */ }
    await sleep(250);
  }
  throw new Error("Chrome did not expose a page target");
}
function send(method, params = {}) {
  seq += 1; const id = seq;
  return new Promise((res, rej) => { const t = setTimeout(() => rej(new Error(`timeout ${method}`)), 60000);
    pending.set(id, (m) => { clearTimeout(t); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); }); ws.send(JSON.stringify({ id, method, params })); });
}
async function js(expression) {
  const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 400));
  return r.result.value;
}
async function waitFor(expr, ms = 45000) { const end = Date.now() + ms; while (Date.now() < end) { if (await js(`Boolean(${expr})`)) return true; await sleep(150); } return false; }
let vp = [1440, 1000];
async function size(w, h) { vp = [w, h]; await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: w < 600 }); }
const READY = String.raw`document.querySelector("main h2, main [data-page-refusal], main h1") && ![...document.querySelectorAll("main p")].some((p) => /^Loading [^.]+\.$/.test(p.textContent.trim()))`;
async function go(url) { consoleErrors = []; await send("Page.navigate", { url }); const ok = await waitFor(READY); await sleep(1500); return ok; }
async function shot(file) {
  const tall = await js(`document.documentElement.scrollHeight`);
  await send("Emulation.setDeviceMetricsOverride", { width: vp[0], height: Math.min(Math.ceil(tall), 9000), deviceScaleFactor: 1, mobile: vp[0] < 600 });
  await sleep(300);
  const r = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(join(OUT, file), Buffer.from(r.data, "base64"));
  await size(vp[0], vp[1]); await sleep(200);
}
const COMMON = String.raw`
const txt = (e) => (e?.textContent ?? "").replace(/\s+/g, " ").trim();
const base = "Synthetic layout probe text that wraps across several lines in this narrow panel and keeps going ";
const L = (n, tag) => { const s = (tag + " " + base.repeat(5)).slice(0, n); return s.endsWith(" ") ? s.slice(0, n - 1) + "." : s; };
const GAP = L(320, "SYNTHETIC-GAP");
const panelOf = (t) => [...document.querySelectorAll("main section.panel")].find((p) => txt(p.querySelector("h2")).startsWith(t));
const inClosed = (n, root) => { for (let e = n; e && e !== root; e = e.parentElement) { const d = e.parentElement; if (d && d.tagName === "DETAILS" && !d.open && e.tagName !== "SUMMARY") return true; } return false; };
const leaves = (el) => { const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); const out = []; for (let n = w.nextNode(); n; n = w.nextNode()) if (n.textContent.trim()) out.push(n); return out; };
const measure = (p, clones) => { const r = p.getBoundingClientRect();
  const clipped = [...p.querySelectorAll("*")].filter((e) => { if (inClosed(e, p) || !e.firstChild || e.getBoundingClientRect().width === 0) return false; const s = getComputedStyle(e);
    if (s.position === "absolute" && (e.clientWidth <= 1 || e.clientHeight <= 1)) return false;
    return (((s.overflowX === "hidden" || s.overflowX === "clip" || s.textOverflow === "ellipsis") && e.scrollWidth > e.clientWidth + 1) || ((s.overflowY === "hidden" || s.overflowY === "clip") && e.scrollHeight > e.clientHeight + 2)) && txt(e).length > 0; })
    .map((e) => ({ el: e.tagName + "." + String(e.className).slice(0, 40), text: txt(e).slice(0, 60), sw: e.scrollWidth, cw: e.clientWidth, sh: e.scrollHeight, ch: e.clientHeight }));
  const innerScrollX = [...p.querySelectorAll("*")].filter((e) => { const s = getComputedStyle(e); return (s.overflowX === "auto" || s.overflowX === "scroll") && e.clientWidth > 0; })
    .map((e) => ({ cls: String(e.className).slice(0, 40), sw: e.scrollWidth, cw: e.clientWidth, scrolls: e.scrollWidth > e.clientWidth + 1 }));
  // W4: the natural (uncapped) closed height: lift the panel's own cap and its inner scroll caps, measure, restore.
  const capped = [p, ...p.querySelectorAll(".mini-scroll, .data-table__scroll")];
  const saved = capped.map((e) => e.style.maxHeight); capped.forEach((e) => { e.style.maxHeight = "none"; });
  const naturalH = Math.round(p.getBoundingClientRect().height); capped.forEach((e, i) => { e.style.maxHeight = saved[i]; });
  const scrollers = [p, ...p.querySelectorAll("*")].filter((e) => { const s = getComputedStyle(e); return (s.overflowY === "auto" || s.overflowY === "scroll") && e.scrollHeight > e.clientHeight + 1; })
    .map((e) => ({ cls: String(e.className).slice(0, 40), sh: e.scrollHeight, ch: e.clientHeight, focusable: e.tabIndex >= 0, label: e.getAttribute("aria-label") ?? e.getAttribute("aria-labelledby"), maxH: getComputedStyle(e).maxHeight }));
  return { panelH: Math.round(r.height), naturalH, scrollers, maxH: getComputedStyle(p).maxHeight, panelW: Math.round(r.width), rowHs: (clones ?? []).map((c) => Math.round(c.getBoundingClientRect().height)), clipped, innerScrollX,
    details: p.querySelectorAll("details").length, detailsOpen: p.querySelectorAll("details[open]").length,
    docOverflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth };
};
const openAll = (p) => { p.querySelectorAll("details").forEach((d) => { d.open = true; }); };
const closeAll = (p) => { p.querySelectorAll("details").forEach((d) => { d.open = false; }); };
const label = () => { const d = document.createElement("div"); d.id = "synthetic-label"; d.textContent = "SYNTHETIC LAYOUT EVIDENCE, NOT PRODUCT DATA";
  d.style.cssText = "position:absolute;top:0;left:0;right:0;z-index:99999;background:#b00020;color:#fff;font:700 14px sans-serif;padding:4px 8px;text-align:center;pointer-events:none"; document.body.appendChild(d); };
`;
const INSPECT = String.raw`(() => {
  const root = document.querySelector("main") ?? document.body;
  const panels = [...root.querySelectorAll("section.panel")].filter((p) => !p.parentElement.closest("section.panel"))
    .map((p) => ({ title: txt(p.querySelector("h2")), h: Math.round(p.getBoundingClientRect().height), details: p.querySelectorAll("details").length, detailsOpen: p.querySelectorAll("details[open]").length }));
  const tabs = [...document.querySelectorAll(".tabs, .site-tabs, .site-subtabs, [role='tablist']")].filter((e) => e.getBoundingClientRect().height > 0)
    .map((e) => [...e.querySelectorAll("a")].map((a) => ({ text: txt(a), href: a.getAttribute("href") })));
  const links = [...root.querySelectorAll("a[href]")].filter((a) => /Inspect (session lineage|claim evidence)|Energy ↗|Financial assumptions|Assumptions/.test(txt(a))).map((a) => ({ text: txt(a), href: a.getAttribute("href") }));
  const strip = [...root.querySelectorAll("strong")].map(txt).filter((t) => t.startsWith("Scoped to"));
  const refusalTitles = [...root.querySelectorAll("strong, h2, h3, [data-refusal-title]")].map(txt).filter((t) => t === "Window cannot be read");
  const sentences = ["The selected window needs both a start and an end, with the start before the end.", "The selected window is longer than 31 days.", "The selected window is invalid."];
  const bodyText = root.innerText;
  const sentenceCounts = Object.fromEntries(sentences.map((s) => [s, bodyText.split(s).length - 1]));
  const notAssessed = bodyText.split("Not assessed").length - 1;
  const banners = [...document.querySelectorAll("[data-page-refusal], .page-banner, [role='alert']")].filter((e) => e.getBoundingClientRect().height > 0).map((e) => ({ cls: String(e.className).slice(0, 50), text: txt(e).slice(0, 120), inPanel: !!e.closest("section.panel") }));
  const statusBars = [...root.querySelectorAll(".status-bar, [class*='status-bar'], [class*='strip']")].filter((e) => e.getBoundingClientRect().height > 0).map((e) => txt(e).slice(0, 200)).slice(0, 4);
  const tiles = [...root.querySelectorAll(".tile, .kpi, [class*='tile'], [class*='kpi']")].filter((e) => e.getBoundingClientRect().height > 0 && !e.parentElement.closest(".tile, .kpi, [class*='tile'], [class*='kpi']")).map((e) => txt(e).slice(0, 80)).slice(0, 8);
  const clippedDoc = [...root.querySelectorAll("*")].filter((e) => { if (!e.firstChild || e.getBoundingClientRect().width === 0 || inClosed(e, root)) return false; const s = getComputedStyle(e);
    if (s.position === "absolute" && (e.clientWidth <= 1 || e.clientHeight <= 1)) return false;
    return ((s.overflowX === "hidden" || s.overflowX === "clip" || s.textOverflow === "ellipsis") && e.scrollWidth > e.clientWidth + 1 && txt(e).length > 0); }).slice(0, 6).map((e) => ({ el: e.tagName + "." + String(e.className).slice(0, 40), text: txt(e).slice(0, 60) }));
  const rgb = (c) => { const m = /rgba?\(([^)]+)\)/.exec(c); if (!m) return null; const v = m[1].split(",").map((x) => parseFloat(x)); return v.length > 3 && v[3] === 0 ? null : v.slice(0, 3); };
  const lum = (v) => { const f = (x) => { x /= 255; return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(v[0]) + 0.7152 * f(v[1]) + 0.0722 * f(v[2]); };
  const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((m, n) => n - m); return Math.round(((x + 0.05) / (y + 0.05)) * 100) / 100; };
  const bgOf = (e) => { for (let n = e; n; n = n.parentElement) { const c = rgb(getComputedStyle(n).backgroundColor); if (c) return c; } return [255, 255, 255]; };
  const bars = [...root.querySelectorAll(".value-bars__fill")].filter((e) => e.getBoundingClientRect().width > 0).map((e) => { const fill = rgb(getComputedStyle(e).backgroundColor); const track = bgOf(e.parentElement);
    return { cls: String(e.className).replace("value-bars__fill ", ""), fill, track, page: bgOf(e.closest("section.panel") ?? root), ratioTrack: fill ? ratio(fill, track) : null, ratioPanel: fill ? ratio(fill, bgOf(e.closest("section.panel") ?? root)) : null }; });
  const chips = [...root.querySelectorAll(".badge[class*='status-tone--']")].filter((e) => e.getBoundingClientRect().width > 0).map((e) => { const fg = rgb(getComputedStyle(e).color); const bg = bgOf(e);
    return { text: txt(e).slice(0, 40), tone: (/status-tone--(\w+)/.exec(e.className) ?? [])[1], ratio: fg ? ratio(fg, bg) : null }; });
  return { h1: txt(root.querySelector("h1")).slice(0, 120), bars, chips, panels, tabs, links, strip, refusalTitles, sentenceCounts, notAssessed, banners, statusBars, tiles, clippedDoc,
    docOverflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth, viewport: innerWidth, location: location.pathname + location.search };
})()`;
// Probe bodies; each returns { verified, intendedFields, fieldsChanged, ...measure }.
const PROBE = {
  rows: (title, gap, firstOnly) => String.raw`(() => { const p = panelOf(${JSON.stringify(title)}); if (!p) return { verified: false, reason: "panel not found" };
    const tbody = p.querySelector("table tbody"); if (!tbody) return { verified: false, reason: "no table body in panel" };
    const tmpl = tbody.querySelector(":scope > tr"); if (!tmpl) return { verified: false, reason: "no row to clone" };
    const realRows = tbody.querySelectorAll(":scope > tr").length; const cells = tmpl.children.length;
    tbody.replaceChildren(); const cl = []; let want = 0; let got = 0;
    for (let i = 0; i < 5; i += 1) { const c = tmpl.cloneNode(true);
      [...c.children].forEach((cell, j) => { if (${Array.isArray(firstOnly) ? `!${JSON.stringify(firstOnly)}.includes(j)` : firstOnly ? "j > 0" : "false"}) return; want += 1; const ls = leaves(cell); const s = L(160, "SYN-r" + i + "c" + j);
        if (!ls.length) cell.textContent = s; else ls.forEach((n, k) => { n.textContent = k === 0 ? s : ""; });
        if (txt(cell).length === 160 && txt(cell).startsWith("SYN-r" + i + "c" + j)) got += 1; });
      tbody.appendChild(c); cl.push(c); }
    ${gap ? `const g = document.createElement("p"); g.className = "not-available-yet v69-chart-note"; g.textContent = GAP; p.querySelector("table").closest("div, section").before(g);` : ""}
    closeAll(p);
    const verified = tbody.children.length === 5 && want === 5 * ${Array.isArray(firstOnly) ? firstOnly.length : firstOnly ? 1 : "cells"} && got === want ${gap ? "&& p.textContent.includes(GAP)" : ""};
    label();
    return { synthetic: true, verified, realRows, cellsPerRow: cells, intendedFields: want, fieldsChanged: got, ...measure(p, cl) }; })()`,
  // W4: five rows; only the named free-text fields (CSS selectors within a row) become 160 characters; typed values
  // (codes, dates, state chips, counts) stay as rendered. Rows past the real count are clones of the first real row.
  fields: (title, gap, sels) => String.raw`(() => { const p = panelOf(${JSON.stringify(title)}); if (!p) return { verified: false, reason: "panel not found" };
    const tbody = p.querySelector("table tbody"); if (!tbody) return { verified: false, reason: "no table body in panel" };
    const real = [...tbody.querySelectorAll(":scope > tr")]; if (!real.length) return { verified: false, reason: "no row to clone" };
    const realRows = real.length; const sels = ${JSON.stringify(sels)};
    const rows = real.slice(0, 5); while (rows.length < 5) rows.push(real[0].cloneNode(true));
    tbody.replaceChildren(...rows); let want = 0; let got = 0;
    rows.forEach((row, i) => sels.forEach((q, j) => { const el = row.querySelector(q); want += 1; if (!el) return; const ls = leaves(el); if (!ls.length) return;
      const target = ls.reduce((a, b) => (b.textContent.trim().length > a.textContent.trim().length ? b : a)); const s = L(160, "SYN-r" + i + "f" + j); target.textContent = s;
      if (txt(el).includes(s)) got += 1; }));
    ${gap ? `const g = document.createElement("p"); g.className = "not-available-yet v69-chart-note"; g.textContent = GAP; p.querySelector("table").closest("div, section").before(g);` : ""}
    closeAll(p);
    const verified = tbody.children.length === 5 && got === want ${gap ? "&& p.textContent.includes(GAP)" : ""};
    label();
    const t = p.querySelector("table"); const wrap = t.parentElement;
    return { synthetic: true, verified, realRows, intendedFields: want, fieldsChanged: got, table: { cw: t.clientWidth, sw: t.scrollWidth, wrapCw: wrap.clientWidth, wrapSw: wrap.scrollWidth, wrapCh: wrap.clientHeight, wrapSh: wrap.scrollHeight }, ...measure(p, rows) }; })()`,
  list: (title, gap, firstOnly) => String.raw`(() => { const p = panelOf(${JSON.stringify(title)}); if (!p) return { verified: false, reason: "panel not found" };
    const ul = p.querySelector("ul[data-ev-sources]"); const tmpl = ul?.querySelector(":scope > li"); if (!tmpl) return { verified: false, reason: "no source list" };
    const realRows = ul.children.length; ul.replaceChildren(); const cl = []; let got = 0;
    const n = ${firstOnly ? "Math.max(5, realRows)" : 5}; for (let i = 0; i < n; i += 1) { const c = tmpl.cloneNode(true); const ls = leaves(c); const s = L(160, "SYN-r" + i); ls.forEach((n, k) => { n.textContent = k === 0 ? s : ""; }); if (txt(c) === s) got += 1; ul.appendChild(c); cl.push(c); }
    ${gap ? `const g = p.querySelector("[data-ev-contact-note]") ?? p.querySelector("p"); g.textContent = GAP;` : ""}
    closeAll(p);
    const verified = ul.children.length === n && got === n ${gap ? "&& p.textContent.includes(GAP)" : ""};
    label();
    return { synthetic: true, verified, realRows, intendedFields: n, fieldsChanged: got, ...measure(p, cl) }; })()`,
  conclusion: (title, gap) => String.raw`(() => { const p = panelOf(${JSON.stringify(title)}); if (!p) return { verified: false, reason: "panel not found" };
    const sel = ["[data-ev-conclusion]", "[data-ev-delivered]", "[data-ev-delivered] + p.prose", "[data-ev-claim-evidence] a", "[data-ev-record]"];
    const els = sel.map((q) => p.querySelector(q)); let got = 0;
    els.forEach((e, i) => { if (!e) return; if (i === 4) { const ls = leaves(e); ls.forEach((n, k) => { n.textContent = k === 0 ? L(160, "SYN-f" + i) : ""; }); } else e.textContent = L(160, "SYN-f" + i); if (txt(e).length === 160) got += 1; });
    ${gap ? `const g = document.createElement("p"); g.className = "prose"; g.textContent = GAP; p.querySelector("[data-ev-record]").before(g);` : ""}
    closeAll(p);
    const present = els.filter(Boolean).length;
    const verified = present === 5 && got === 5 ${gap ? "&& p.textContent.includes(GAP)" : ""};
    label();
    return { synthetic: true, verified, intendedFields: 5, fieldsPresent: present, fieldsChanged: got, ...measure(p, els.filter(Boolean)) }; })()`,
  // Cold Findings index: variable free text is the Finding title link (cell 0) and, in the stricter variant, its
  // episode-period line; typed words (Temperature/Backup, Not assessed, claim and lifecycle words) stay real.
  coldrows: (title, gap, withEpisode) => String.raw`(() => { const p = panelOf(${JSON.stringify(title)}); if (!p) return { verified: false, reason: "panel not found" };
    const tbody = p.querySelector("table tbody"); if (!tbody) return { verified: false, reason: "no table body in panel" };
    const tmpl = tbody.querySelector(":scope > tr"); if (!tmpl) return { verified: false, reason: "no row to clone" };
    const realRows = tbody.querySelectorAll(":scope > tr").length;
    tbody.replaceChildren(); const cl = []; let want = 0; let got = 0;
    for (let i = 0; i < 5; i += 1) { const c = tmpl.cloneNode(true); c.setAttribute("data-synthetic", "true");
      const a = c.children[0].querySelector("a"); const sm = c.children[0].querySelector("small");
      want += 1; a.textContent = L(160, "SYN-title-r" + i); if (txt(a).length === 160) got += 1;
      ${withEpisode ? `want += 1; sm.textContent = L(160, "SYN-episode-r" + i); if (txt(sm).length === 160) got += 1;` : ""}
      tbody.appendChild(c); cl.push(c); }
    ${gap ? `const g = document.createElement("p"); g.className = "not-available-yet v69-chart-note"; g.textContent = GAP; p.querySelector("table").closest("div, section").after(g);` : ""}
    closeAll(p);
    const verified = tbody.children.length === 5 && got === want ${gap ? "&& p.textContent.includes(GAP)" : ""};
    label();
    const t = p.querySelector("table"); const wrap = t.parentElement;
    return { synthetic: true, verified, realRows, intendedFields: want, fieldsChanged: got, table: { cw: t.clientWidth, sw: t.scrollWidth, wrapCw: wrap.clientWidth, wrapSw: wrap.scrollWidth }, ...measure(p, cl) }; })()`,
};
const results = [];
try {
  ws = await connect();
  ws.addEventListener("message", (event) => { const m = JSON.parse(event.data);
    if (m.method === "Runtime.exceptionThrown") consoleErrors.push(String(m.params.exceptionDetails?.exception?.description ?? m.params.exceptionDetails?.text).slice(0, 300));
    if (m.method === "Runtime.consoleAPICalled" && m.params.type === "error") consoleErrors.push(m.params.args.map((a) => a.value ?? a.description ?? "").join(" ").slice(0, 300));
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
  await send("Page.enable"); await send("Runtime.enable");
  for (const t of TARGETS) {
    for (const [w, h] of WIDTHS) {
      const name = `${t.id}-${t.case}-${w}`;
      await size(w, h);
      const ready = await go(t.url);
      const ins = await js("(() => {" + COMMON + "return " + INSPECT + "})()");
      const rec = { screen: t.id, case: t.case, width: w, url: t.url, ready, revision: process.env.AUDIT_REVISION ?? null, ...ins, consoleErrors: [...new Set(consoleErrors)].slice(0, 5), caps: [] };
      console.log(`${ready ? "OK  " : "FAIL"} ${name} h1=${JSON.stringify(ins.h1)} overflowX=${ins.docOverflowX} panels=${ins.panels.length} console=${rec.consoleErrors.length}`);
      for (const cap of t.caps ?? []) {
        const slug = cap.panel.replace(/[^A-Za-z]+/g, "-").replace(/^-|-$/g, "").toLowerCase().slice(0, 30);
        // 1. real closed + real all-open (browser-only disclosure toggles)
        const real = await js("(() => {" + COMMON + `const p = panelOf(${JSON.stringify(cap.panel)}); if (!p) return null; closeAll(p); const closed = measure(p); openAll(p); const open = measure(p); return { closed, open }; })()`);
        if (real) await shot(`${name}-${slug}-real-all-open.png`);
        const out = { panel: cap.panel, kind: cap.kind, real };
        // 2. synthetic variants on a fresh load of the same page
        for (const [v, gap, firstOnly] of cap.kind === "none" ? [] : cap.kind === "fields" ? [["fields160", false, cap.fields], ["fields160-gap", true, cap.fields]] : [[cap.kind === "coldrows" ? "title160" : "rows160", false, false], [cap.kind === "coldrows" ? "title160-gap" : "rows160-gap", true, false], ...(cap.varCells ? [["varcells160", false, cap.varCells], ["varcells160-gap", true, cap.varCells]] : []), ...(cap.kind === "coldrows" ? [["title-episode160", false, true], ["title-episode160-gap", true, true]] : []), ...(cap.kind === "rows" ? [["firstcell160", false, true]] : cap.kind === "list" ? [["allrows160", false, true]] : [])]) {
          await go(t.url);
          const syn = await js("(() => {" + COMMON + "return " + PROBE[cap.kind](cap.panel, gap, firstOnly) + "})()");
          if (syn.verified) await shot(`${name}-${slug}-${v}-synthetic.png`);
          const opened = syn.verified ? await js("(() => {" + COMMON + `const p = panelOf(${JSON.stringify(cap.panel)}); openAll(p); return measure(p); })()`) : null;
          if (opened) await shot(`${name}-${slug}-${v}-synthetic-all-open.png`);
          out[v] = { ...syn, openedAll: opened };
          console.log(`  ${cap.panel} ${v} ${w}: real=${real?.closed.panelH ?? "n/a"} synthetic=${syn.panelH} verified=${syn.verified} fields=${syn.fieldsChanged}/${syn.intendedFields} clipped=${syn.clipped?.length} open=${opened?.panelH} openClipped=${opened?.clipped.length} doc=${syn.docOverflowX}${syn.reason ? " reason=" + syn.reason : ""}`);
        }
        rec.caps.push(out);
      }
      results.push(rec);
    }
  }
} catch (e) { console.log("FAIL run", String(e).slice(0, 400)); }
finally { writeFileSync(join(OUT, "inspect.json"), JSON.stringify({ revision: process.env.AUDIT_REVISION ?? null, label: "Probe sections (rows160*, title160*, title-episode160*) are SYNTHETIC LAYOUT EVIDENCE, NOT PRODUCT DATA", results }, null, 1)); ws?.close(); chrome.kill(); }
console.log(`done ${results.length} records`);
