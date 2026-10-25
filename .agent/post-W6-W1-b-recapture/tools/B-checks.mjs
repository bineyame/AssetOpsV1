// CAPTURE-ONLY post-capture check (post-W6 W1-b recapture, agent B). node B-checks.mjs <targets.json> <out.json>
// Per target and width: titles + closed panel heights, doc overflowX, Site tab row count, R383 labels (count and
// whether directly after the Site tab row), active rail item. Navigates only; no clicks, no mutation.
import { readFileSync, writeFileSync } from "node:fs";
import { session } from "../probe/tools/B-cdp.mjs";
const [TG, OUT] = process.argv.slice(2);
const targets = JSON.parse(readFileSync(TG, "utf8"));
const Q = String.raw`(() => { const txt = (e) => (e?.textContent ?? "").replace(/\s+/g, " ").trim();
  const vis = (e) => e && e.getBoundingClientRect().height > 0;
  const tabs = [...document.querySelectorAll('nav[aria-label="Site sections"]')].filter(vis);
  const r383 = [...document.querySelectorAll('[data-mock-deviation="R383"]')];
  const rail = [...document.querySelectorAll('.nav-rail a[aria-current="page"], .nav-rail .nav-rail__link.active')].map((a) => txt(a.querySelector('.nav-rail__label') ?? a));
  const panels = [...document.querySelectorAll("main section.panel")].filter((p) => vis(p) && !p.parentElement.closest("section.panel")).map((p) => ({ t: txt(p.querySelector("h2")), h: Math.round(p.getBoundingClientRect().height) }));
  return { h1: txt(document.querySelector("main h1")).slice(0, 80), siteTabRows: tabs.length,
    r383: r383.length, r383Visible: r383.filter(vis).length, r383AfterTabs: r383.map((r) => !!r.previousElementSibling && r.previousElementSibling.matches('nav[aria-label="Site sections"]')),
    activeRail: [...new Set(rail)], railItems: [...document.querySelectorAll(".nav-rail .nav-rail__label")].map(txt), panels, overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth }; })()`;
const s = await session(); const res = [];
try { for (const t of targets) for (const w of [1440, 390]) { await s.open(t.url, w, w === 1440 ? 1000 : 900); const r = await s.js(Q); res.push({ screen: t.id, case: t.case, w, url: t.url, ...r }); console.log(t.id, t.case, w, JSON.stringify({ tabs: r.siteTabRows, r383: r.r383, rail: r.activeRail, ox: r.overflowX, panels: r.panels.map((p) => p.t + ":" + p.h).join("|") })); } }
finally { await s.close(); }
writeFileSync(OUT, JSON.stringify(res, null, 1));
