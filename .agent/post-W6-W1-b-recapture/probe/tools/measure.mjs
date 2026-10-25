// Capture-only post-capture measurement (post-W6 W1-b recapture). Navigates only; no clicks, no mutation.
//   node measure.mjs <out.json> <targets.json> [<targets2.json> ...]   (targets: [{id,case,url}])
// Per target and width (1440x1000, 390x900): panel titles/closed heights, doc overflowX, Site tab rows, R383 marker
// placement, active rail item, page header height.
import { readFileSync, writeFileSync } from "node:fs";
import { session } from "./cdp.mjs";
const [OUT, ...TF] = process.argv.slice(2);
const targets = TF.flatMap((f) => JSON.parse(readFileSync(f, "utf8")));
const EXPR = `(() => {
  const panels = [...document.querySelectorAll("section.panel")].map((p) => ({ t: (p.querySelector("h2")?.textContent ?? "").trim(), h: Math.round(p.getBoundingClientRect().height), openDetails: p.querySelectorAll("details[open]").length }));
  const siteTabs = [...document.querySelectorAll("nav.site-tabs")].filter((n) => !n.classList.contains("site-subtabs"));
  const r383 = [...document.querySelectorAll('[data-mock-deviation="R383"]')];
  const r383AfterTabs = r383.length === 1 && siteTabs.length === 1 && siteTabs[0].nextElementSibling === r383[0];
  const rail = [...document.querySelectorAll(".nav-rail__link.active, .nav-rail [aria-current=page]")].map((a) => (a.querySelector(".nav-rail__label")?.textContent ?? a.textContent).trim());
  const hdr = document.querySelector("header.page-header");
  return { h1: document.querySelector("h1")?.textContent?.trim() ?? null, titles: panels.map((p) => p.t), panels, overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    siteTabRows: siteTabs.length, r383Count: r383.length, r383AfterTabs, railActive: [...new Set(rail)], headerH: hdr ? Math.round(hdr.getBoundingClientRect().height) : null, url: location.href };
})()`;
const s = await session();
const out = [];
try {
  for (const t of targets) for (const [w, h] of [[1440, 1000], [390, 900]]) {
    let r = null;
    for (let a = 0; a < 3 && !r; a += 1) { try { await s.open(t.url, w, h); r = await s.js(EXPR); } catch (e) { console.log("retry", t.id, t.case, w, String(e).slice(0, 120)); } }
    out.push({ screen: t.id, case: t.case, width: String(w), ...(r ?? { error: "measure failed" }) });
    console.log(t.id, t.case, w, r ? JSON.stringify({ ox: r.overflowX, tabs: r.siteTabRows, r383: r.r383Count, after: r.r383AfterTabs, rail: r.railActive, p: r.panels.map((p) => p.t.slice(0, 18) + "=" + p.h).join("; ") }) : "FAILED");
  }
} finally { await s.close(); }
writeFileSync(OUT, JSON.stringify(out, null, 1));
