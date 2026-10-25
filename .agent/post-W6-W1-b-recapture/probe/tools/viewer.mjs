// Capture-only viewer clicks (post-W6 W1-b recapture, Q43): read/viewer navigation links only, no mutations.
//   node viewer.mjs <out-dir> <targets.json>   (assumptions targets: [{id,case,url}])
// Per target and width: open; measure the Interpretation history; click "Previous versions" when offered, measure; then
// click "Next versions" (or "Back to newest") when offered, measure. Screens each state.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { session } from "./cdp.mjs";
const [OUT, TF] = process.argv.slice(2);
mkdirSync(OUT, { recursive: true });
const targets = JSON.parse(readFileSync(TF, "utf8"));
const M = `(() => { const p = [...document.querySelectorAll("section.panel")].find((x) => (x.querySelector("h2")?.textContent ?? "").trim().startsWith("Interpretation history"));
  const rows = p ? [...p.querySelectorAll("tr[data-history-row]")].map((r) => (r.querySelector("strong")?.textContent ?? "").trim()) : null;
  return { url: location.href, historyH: p ? Math.round(p.getBoundingClientRect().height) : null, rows, rowCount: rows ? rows.length : null,
    prev: !!document.querySelector("[data-history-next]"), newer: document.querySelector("[data-history-newer]")?.getAttribute("data-history-newer") ?? null,
    overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth }; })()`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const s = await session();
const log = [];
async function settle(prevUrl) { for (let i = 0; i < 60; i += 1) { await sleep(250); const ok = await s.js(`location.href !== ${JSON.stringify(prevUrl)} && !document.querySelector('[aria-busy=true]')`).catch(() => false); if (ok) break; } await sleep(1500); }
try {
  for (const t of targets) for (const [w, h] of [[1440, 1000], [390, 900]]) {
    await s.open(t.url, w, h);
    const a = await s.js(M); const entry = { screen: t.id, case: t.case, width: w, start: a, clicks: [] };
    await s.shot(`${OUT}/${t.id}-${t.case}-${w}-0-start.png`);
    if (a.prev) {
      await s.js(`document.querySelector("[data-history-next]").click()`); await settle(a.url);
      const b = await s.js(M); entry.clicks.push({ click: "Previous versions", before: a.url, after: b }); await s.shot(`${OUT}/${t.id}-${t.case}-${w}-1-previous.png`);
      if (b.newer) {
        const label = b.newer === "next" ? "Next versions" : "Back to newest";
        await s.js(`document.querySelector("[data-history-newer]").click()`); await settle(b.url);
        const c = await s.js(M); entry.clicks.push({ click: label, before: b.url, after: c }); await s.shot(`${OUT}/${t.id}-${t.case}-${w}-2-${b.newer}.png`);
        if (c.newer === "newest") { await s.js(`document.querySelector("[data-history-newer]").click()`); await settle(c.url); const d = await s.js(M); entry.clicks.push({ click: "Back to newest", before: c.url, after: d }); await s.shot(`${OUT}/${t.id}-${t.case}-${w}-3-newest.png`); }
      }
    } else if (a.newer) {
      const label = a.newer === "next" ? "Next versions" : "Back to newest";
      await s.js(`document.querySelector("[data-history-newer]").click()`); await settle(a.url);
      const c = await s.js(M); entry.clicks.push({ click: label, before: a.url, after: c }); await s.shot(`${OUT}/${t.id}-${t.case}-${w}-1-${a.newer}.png`);
    }
    log.push(entry);
    console.log(t.id, t.case, w, "start", a.rowCount, a.historyH, entry.clicks.map((c) => `${c.click}->${c.after.rowCount}r/${c.after.historyH}px`).join(" | "));
  }
} finally { await s.close(); }
writeFileSync(`${OUT}/viewer-results.json`, JSON.stringify(log, null, 1));
