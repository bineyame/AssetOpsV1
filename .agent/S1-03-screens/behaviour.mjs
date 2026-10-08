// S1-03 behaviour check: period selection across views, reload/share, keyboard
// focus, a binding removal at a new period with the earlier view recovered,
// overflow, and no false status or mock values. Drives installed Chrome over
// CDP (no deps). Run against a SCRATCH database: step 7 publishes a binding.
//   node .agent/S1-03-screens/behaviour.mjs http://localhost:5184 KOBO-001
import { spawn } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [BASE, SITE = "KOBO-001", INSTANT = "2026-11-01"] = process.argv.slice(2);
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe",
  ["--headless=new", "--remote-debugging-port=9343", `--user-data-dir=${mkdtempSync(join(tmpdir(), "s103b-"))}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let ws;
for (let i = 0; i < 50; i++) { try { const l = await (await fetch("http://127.0.0.1:9343/json")).json(); const p = l.find((t) => t.type === "page"); if (p) { ws = p.webSocketDebuggerUrl; break; } } catch {} await sleep(200); }
const sock = new WebSocket(ws); await new Promise((r) => sock.addEventListener("open", r));
let id = 0; const pending = new Map();
sock.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); sock.send(JSON.stringify({ id: i, method, params })); });
const ev = async (expression) => (await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true })).result.result.value;
await send("Page.enable");
await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });

let pass = 0, fail = 0;
const check = (name, ok, detail = "") => { console.log(`  ${ok ? "PASS" : "FAIL"}  ${name}${detail ? `  [${detail}]` : ""}`); ok ? pass++ : fail++; };
const go = async (path) => { await send("Page.navigate", { url: BASE + path }); await sleep(2500); };
const loc = () => ev("location.pathname + location.search");
const state = () => ev(`JSON.stringify({
  note: document.querySelector('[data-foundation-historical]')?.textContent ?? null,
  select: document.querySelector('select[aria-label="Foundation period"]')?.value ?? null,
  version: document.querySelector('.status-strip .badge')?.textContent ?? null,
  readiness: document.querySelector('[data-readiness-state]')?.getAttribute('data-readiness-state') ?? null,
  current: document.querySelector('nav[aria-label="Foundation views"] [aria-current="page"]')?.textContent ?? null,
  sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth })`).then(JSON.parse);
const setSelect = (selector, value) => ev(`(() => { const el = document.querySelector('${selector}');
  const set = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set; set.call(el, ${JSON.stringify(value)});
  el.dispatchEvent(new Event('change', { bubbles: true })); return el.value; })()`);
const clickView = (label) => ev(`[...document.querySelectorAll('nav[aria-label="Foundation views"] a')].find(a => a.textContent === ${JSON.stringify(label)}).click()`);

console.log("=== 1. Period selection travels with the views ===");
await go(`/sites/${SITE}/foundation`);
const options = JSON.parse(await ev(`JSON.stringify([...document.querySelectorAll('select[aria-label="Foundation period"] option')].map(o => [o.value, o.textContent]))`));
const earlier = options.find(([v, t]) => v !== "" && /\(past\)/.test(t)) ?? options.find(([v, t]) => v !== "" && !/\(current\)/.test(t));
check("the period selector lists stored periods", options.length > 1, options.map((o) => o[1]).join(" | "));
check("an earlier period exists to select", earlier !== undefined, earlier?.[1] ?? "none");
await setSelect('select[aria-label="Foundation period"]', earlier[0]); await sleep(1500);
const at = encodeURIComponent(earlier[0]);
let s = await state();
check("selecting it puts `at` in the URL", (await loc()) === `/sites/${SITE}/foundation?at=${at}`, await loc());
check("the Site model labels the historical period", s.note !== null, s.note ?? "no note");
for (const [label, path] of [["Single line diagram", "/sld"], ["Readiness", "/readiness"], ["Site model", ""]]) {
  await clickView(label); await sleep(1500); s = await state();
  check(`${label}: URL keeps the period`, (await loc()) === `/sites/${SITE}/foundation${path}?at=${at}`, await loc());
  check(`${label}: historical label and selector stay on the same period`, s.note !== null && s.select === earlier[0], `${s.version}; select ${s.select}`);
  check(`${label}: marked as the current view`, s.current === label, s.current ?? "none");
}

console.log("=== 2. Reload and a shared URL reopen the same view and period ===");
for (const path of ["", "/sld", "/readiness"]) {
  await go(`/sites/${SITE}/foundation${path}?at=${at}`);
  await send("Page.reload"); await sleep(2500); s = await state();
  check(`reload of ${path || "/ (Site model)"} keeps view and period`, (await loc()) === `/sites/${SITE}/foundation${path}?at=${at}` && s.select === earlier[0] && s.note !== null, `${await loc()}`);
}

console.log("=== 3. Keyboard focus reaches every view link visibly ===");
await go(`/sites/${SITE}/foundation`);
const focused = [];
for (let i = 0; i < 40; i++) {
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
  const f = JSON.parse(await ev(`JSON.stringify({ t: document.activeElement?.textContent?.trim().slice(0, 40), row: !!document.activeElement?.closest('nav[aria-label="Foundation views"]'), outline: getComputedStyle(document.activeElement).outlineStyle })`));
  if (f.row) focused.push(f);
}
check("Tab reaches Site model, Single line diagram and Readiness", ["Site model", "Single line diagram", "Readiness"].every((l) => focused.some((f) => f.t === l)), focused.map((f) => f.t).join(", "));
check("each focused view link shows an outline", focused.length > 0 && focused.every((f) => f.outline !== "none"), focused.map((f) => f.outline).join(", "));

console.log("=== 4. Remove a binding at a new period; the earlier view is recovered ===");
await go(`/sites/${SITE}/foundation/readiness`);
s = await state();
check("now: configuration readiness is Ready to report", s.readiness === "READY_TO_REPORT", s.readiness);
const soc = await ev(`[...document.querySelectorAll('form[aria-label="Remove a binding"] option')].find(o => /state-of-charge/.test(o.textContent))?.value ?? null`);
check("the battery SOC binding is offered for removal", soc !== null, soc ?? "none");
await setSelect('form[aria-label="Remove a binding"] select', soc);
await ev(`(() => { const el = document.querySelector('form[aria-label="Remove a binding"] input[type="datetime-local"]');
  const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set; set.call(el, '${INSTANT}T00:00');
  el.dispatchEvent(new Event('input', { bubbles: true })); })()`);
await ev(`[...document.querySelectorAll('form[aria-label="Remove a binding"] button')].find(b => b.textContent === 'Publish binding change').click()`);
await sleep(3000);
const message = await ev(`document.querySelector('form[aria-label="Remove a binding"] [role="status"]')?.textContent ?? null`);
check("the publication is confirmed with its period", new RegExp(`Published binding v[0-9]+, effective ${INSTANT} 00:00 UTC`).test(message ?? ""), message ?? "no message");
s = await state();
check(`now (before ${INSTANT}) stays Ready to report`, s.readiness === "READY_TO_REPORT", s.readiness);
await go(`/sites/${SITE}/foundation/readiness?at=${encodeURIComponent(`${INSTANT}T00:00:00Z`)}`);
s = await state();
const missing = await ev(`document.querySelector('[data-readiness-missing-role="battery_soc"]')?.textContent ?? null`);
check("at the new period Readiness is Incomplete", s.readiness === "INCOMPLETE", s.readiness);
check("and names the missing battery state-of-charge role", missing !== null, missing ?? "none");
check("and labels the binding period as scheduled", /Scheduled binding period/.test(s.note ?? ""), s.note ?? "no note");
await clickView("Single line diagram"); await sleep(1500);
const part = await ev(`document.querySelector('[data-sld-part="battery-pcs"]')?.textContent ?? null`);
check("the SLD at the new period shows the battery SOC channel as not bound", /Not bound: battery-pcs-controller \/ state-of-charge/.test(part ?? ""), part ?? "none");
await setSelect('select[aria-label="Foundation period"]', ""); await sleep(1500);
const partNow = await ev(`document.querySelector('[data-sld-part="battery"]')?.textContent ?? null`);
check("choosing In effect now recovers the bound channel on the SLD", /Battery state of charge: battery-pcs-controller \/ state-of-charge/.test(partNow ?? ""), partNow ?? "none");
check("and stays on the SLD view", (await loc()) === `/sites/${SITE}/foundation/sld`, await loc());

console.log("=== 5. No horizontal overflow; no false status or mock values ===");
const banned = /\b(Online|Offline|synced|Reporting|Connected|Healthy|commissioned)\b|MG-DEMO-01|GW-MG-01|Africa\/Nairobi|35% \/ 90%|CHG-019|Needs review/;
for (const [w, h] of [[1440, 900], [390, 844]]) {
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: false });
  for (const path of ["", "/sld", "/readiness"]) {
    await go(`/sites/${SITE}/foundation${path}`); s = await state();
    check(`${w}px ${path || "/"}: no horizontal page scroll`, s.sw <= s.cw, `${s.sw} vs ${s.cw}`);
    const text = await ev(`document.querySelector('main').innerText`);
    const hit = text.match(banned);
    check(`${w}px ${path || "/"}: no status word or mock value`, hit === null, hit?.[0] ?? "none");
  }
}
console.log(`\n${pass} PASS, ${fail} FAIL`);
sock.close(); chrome.kill(); process.exit(fail === 0 ? 0 : 1);
