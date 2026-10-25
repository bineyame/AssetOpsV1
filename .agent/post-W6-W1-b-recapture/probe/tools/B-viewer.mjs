// Capture-only viewer click (post-W6 W1-b recapture, agent B, Q43): action-history "Show all N entries" only.
//   node B-viewer.mjs <out-dir> <targets.json> <out.json>   Per target/width: open, measure, click the toggle when it
// reads "Show all", measure again, screenshot both states. No other clicks, no mutation.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { session } from "./B-cdp.mjs";
const [OUT, TG, RES] = process.argv.slice(2);
mkdirSync(OUT, { recursive: true });
const M = String.raw`(() => { const p = [...document.querySelectorAll("section.panel")].find((x) => (x.querySelector("h2")?.textContent ?? "").trim() === "Action history");
  const b = p?.querySelector("[data-action-history-show-all]"); const t = (e) => (e?.textContent ?? "").replace(/\s+/g, " ").trim();
  return { url: location.href, panelH: p ? Math.round(p.getBoundingClientRect().height) : null, rows: p ? p.querySelectorAll("tbody tr").length : 0,
    button: b ? t(b) : null, expanded: b ? b.getAttribute("aria-expanded") : null, truncated: t(p?.querySelector("[data-action-history-truncated]")) || null,
    overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth }; })()`;
const s = await session(); const res = [];
try {
  for (const t of JSON.parse(readFileSync(TG, "utf8"))) for (const w of [1440, 390]) {
    await s.open(t.url, w, w === 1440 ? 1000 : 900);
    const before = await s.js(M); await s.shot(`${OUT}/${t.id}-${t.case}-${w}-before.png`);
    const r = { screen: t.id, case: t.case, w, before, clicked: false };
    if (before.button && before.button.startsWith("Show all")) {
      await s.js(`document.querySelector("[data-action-history-show-all]").click()`);
      await new Promise((ok) => setTimeout(ok, 800));
      r.clicked = true; r.click = before.button; r.after = await s.js(M); await s.shot(`${OUT}/${t.id}-${t.case}-${w}-after-show-all.png`);
    }
    res.push(r); console.log(JSON.stringify(r));
  }
} finally { await s.close(); }
writeFileSync(RES, JSON.stringify(res, null, 1));
