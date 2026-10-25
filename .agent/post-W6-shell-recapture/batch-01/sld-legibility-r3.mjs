// capture-only SLD legibility measurement (Q13). node sld-legibility.mjs <outdir>
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
const OUT = process.argv[2]; mkdirSync(OUT, { recursive: true });
const PORT = 9521, BASE = "http://localhost:5181/sites/KOBO-001/foundation/sld";
const CASES = [["now", ""], ["battery", "?component=battery"], ["unknown-part", "?component=no-such-part"]];
const WIDTHS = [[390, 900], [1440, 1000]];
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe",
  ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), "sldleg2-"))}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let ws, seq = 0; const pending = new Map();
const send = (method, params = {}) => new Promise((res) => { const id = ++seq; pending.set(id, res); ws.send(JSON.stringify({ id, method, params })); });
const js = async (expr) => (await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true })).result?.result?.value;
for (let i = 0; i < 80 && !ws; i++) { try { const p = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page"); if (p) { ws = new WebSocket(p.webSocketDebuggerUrl); await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; }); } } catch { ws = null; await sleep(250); } }
ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } };
await send("Page.enable"); await send("Runtime.enable");
const MEASURE = `(() => {
  const svg = document.querySelector("svg.sld"); const sc = document.querySelector(".sld__scroll");
  const out = { url: location.href, overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth, svg: null };
  if (!svg) return out;
  const r = svg.getBoundingClientRect(); const vb = svg.viewBox && svg.viewBox.baseVal; const vbw = vb && vb.width ? vb.width : null;
  const scale = vbw ? r.width / vbw : null;
  let min = null, minText = null; const sizes = {};
  for (const t of svg.querySelectorAll("text")) { if (!t.textContent.trim()) continue; const fs = parseFloat(getComputedStyle(t).fontSize); const eff = scale ? +(fs * scale).toFixed(2) : null; sizes[fs] = (sizes[fs] || 0) + 1; if (eff !== null && (min === null || eff < min)) { min = eff; minText = t.textContent.trim().slice(0, 40); } }
  const sel = document.querySelector(".sld__selected, .sld__panel, .sld__key, [data-sld-selected], .sld-selected, .sld__legend, .sld__detail");
  out.svg = { renderedWidth: +r.width.toFixed(1), renderedHeight: +r.height.toFixed(1), viewBoxWidth: vbw, scale: scale && +scale.toFixed(4), svgFontSizes: sizes, minEffectiveLabelPx: min, minLabelText: minText,
    textNodes: svg.querySelectorAll("text").length,
    focusable: { tabindex: svg.querySelectorAll("[tabindex]").length, a: svg.querySelectorAll("a").length, button: svg.querySelectorAll("button").length,
      container: sc ? { tabindex: sc.querySelectorAll("[tabindex]").length, a: sc.querySelectorAll("a").length, button: sc.querySelectorAll("button").length } : null } };
  out.scroll = sc ? { scrollWidth: sc.scrollWidth, clientWidth: sc.clientWidth, scrolls: sc.scrollWidth > sc.clientWidth, overflowXStyle: getComputedStyle(sc).overflowX } : null;
  out.selectedPanel = sel ? { selector: sel.className && sel.className.baseVal !== undefined ? sel.className.baseVal : sel.className, text: sel.textContent.trim().split(String.fromCharCode(10)).join(" ").replace(/ +/g, " ").slice(0, 300), fontSize: getComputedStyle(sel).fontSize } : null;
  const cls = new Set(); for (const e of document.querySelectorAll("main [class*='sld']")) for (const c of e.classList) if (c.includes("sld")) cls.add(c);
  out.sldClasses = [...cls];
  const lg = document.querySelector(".sld-legend"); out.legend = lg ? { text: lg.textContent.trim().split(String.fromCharCode(10)).join(" ").replace(/ +/g, " ").slice(0, 200), fontSize: getComputedStyle(lg.querySelector(".sld-legend__item") || lg).fontSize } : null;
  const selN = document.querySelectorAll("main [aria-current], main [aria-selected=true], main [aria-pressed=true], main [class*=selected], main [class*=--active]");
  out.selectedMarkers = [...selN].map((e) => ({ tag: e.tagName, cls: (e.className && e.className.baseVal !== undefined) ? e.className.baseVal : e.className, aria: e.getAttribute("aria-current") || e.getAttribute("aria-selected") || e.getAttribute("aria-pressed"), text: e.textContent.trim().slice(0, 60) })).slice(0, 6);
  const st = document.querySelector(".sld-status"); out.status = st ? { text: st.textContent.trim().slice(0, 200), fontSize: getComputedStyle(st).fontSize } : null;
  const dev = document.querySelector("[data-mock-deviation='R382']");
  if (!dev) { out.deviationLabel = { present: false }; } else {
    const dr = dev.getBoundingClientRect(); const dcs = getComputedStyle(dev);
    out.deviationLabel = { present: true, text: dev.textContent.trim(), visible: dr.width > 0 && dr.height > 0 && dcs.display !== "none" && dcs.visibility !== "hidden",
      display: dcs.display, fontSize: dcs.fontSize, rect: { w: +dr.width.toFixed(1), h: +dr.height.toFixed(1) }, beforeKey: !!(dev.nextElementSibling && dev.nextElementSibling.hasAttribute("data-sld-key")) };
  }
  const key = document.querySelector("ul[data-sld-key]");
  const nodes = svg.querySelectorAll(".sld-node"); const busN = svg.querySelectorAll(".sld-node--bus");
  if (!key) { out.key = { present: false, drawnParts: nodes.length, drawnBus: busN.length }; } else {
    const kr = key.getBoundingClientRect(); const kcs = getComputedStyle(key);
    const visible = kr.width > 0 && kr.height > 0 && kcs.display !== "none" && kcs.visibility !== "hidden" && +kcs.opacity > 0;
    const items = key.querySelectorAll(":scope > li"); const btns = [...key.querySelectorAll("button")];
    const firstItem = items[0]; const firstBtn = btns[0];
    let focusOk = 0; for (const b of btns) { b.focus(); if (document.activeElement === b) focusOk++; } if (document.activeElement) document.activeElement.blur();
    const itemFs = {}; for (const e of key.querySelectorAll("li, button, span")) { const f = getComputedStyle(e).fontSize; itemFs[f] = (itemFs[f] || 0) + 1; }
    out.key = { present: true, visible, rect: { w: +kr.width.toFixed(1), h: +kr.height.toFixed(1) }, display: kcs.display, ulFontSize: kcs.fontSize,
      itemFontSize: firstItem ? getComputedStyle(firstItem).fontSize : null, buttonFontSize: firstBtn ? getComputedStyle(firstBtn).fontSize : null, fontSizeCounts: itemFs,
      itemCount: items.length, buttonCount: btns.length, drawnParts: nodes.length, drawnBus: busN.length, drawnNonBus: nodes.length - busN.length,
      buttonsFocusable: btns.length ? focusOk === btns.length : null, focusedCount: focusOk, tabindexNeg: btns.filter((b) => b.tabIndex < 0 || b.disabled).length,
      ariaPressed: btns.filter((b) => b.getAttribute("aria-pressed") === "true" || b.getAttribute("aria-current")).map((b) => b.textContent.trim().slice(0, 40)),
      firstItems: [...items].slice(0, 12).map((e) => e.textContent.trim().split(String.fromCharCode(10)).join(" ").replace(/ +/g, " ").slice(0, 60)) };
  }
  return out; })()`;
const res = [];
for (const [w, h] of WIDTHS) {
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: w < 600 });
  for (const [name, q] of CASES) {
    await send("Page.navigate", { url: BASE + q });
    let ok = false; for (let i = 0; i < 60; i++) { await sleep(250); if (await js(`!!document.querySelector("svg.sld") || !!document.querySelector("main [data-page-refusal]")`)) { ok = true; break; } }
    await sleep(600);
    const m = await js(MEASURE); m.case = name; m.width = w; m.ready = ok;
    const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true });
    const file = `sld-${name}-${w}-legibility-r3.png`; writeFileSync(join(OUT, file), Buffer.from(shot.result.data, "base64")); m.image = file;
    m.q13_illegible = w === 390 && m.svg && m.svg.minEffectiveLabelPx !== null ? m.svg.minEffectiveLabelPx < 8 : null;
    res.push(m); console.log(name, w, JSON.stringify(m.svg && { s: m.svg.scale, min: m.svg.minEffectiveLabelPx }), m.scroll && m.scroll.scrolls, JSON.stringify(m.key && { v: m.key.visible, fs: m.key.ulFontSize, ifs: m.key.itemFontSize, bfs: m.key.buttonFontSize, n: m.key.itemCount, b: m.key.buttonCount, parts: m.key.drawnParts, bus: m.key.drawnBus, foc: m.key.buttonsFocusable }));
  }
}
writeFileSync(join(OUT, "sld-legibility-r3.json"), JSON.stringify({ revision: process.env.AUDIT_REVISION ?? null, captured_at: new Date().toISOString(), rule: "Q13: effective label px under ~8 at 390 is illegible", results: res }, null, 2));
ws.close(); chrome.kill(); process.exit(0);
