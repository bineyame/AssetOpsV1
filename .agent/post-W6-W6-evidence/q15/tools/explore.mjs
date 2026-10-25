// cap-q15 exploration: list panels and row containers on a page (no modification).
import { session } from "./cdp.mjs";
const urls = process.argv.slice(2);
const s = await session();
try { for (const u of urls) { await s.open(u, 1440, 1000);
  const r = await s.js(`(() => [...document.querySelectorAll("section.panel")].map((p) => { const h = (p.querySelector("h2")?.textContent ?? "").trim(); const trs = p.querySelectorAll("tbody > tr").length; const lis = p.querySelectorAll("li").length; const det = p.querySelectorAll("details").length; return h + " | " + p.innerText.slice(0,160).replace(/\s+/g," ") + " | h=" + Math.round(p.getBoundingClientRect().height) + " tr=" + trs + " li=" + lis + " det=" + det + " tbls=" + p.querySelectorAll("table").length; }))()`);
  console.log("URL", u); r.forEach((x) => console.log("  ", x)); } } finally { await s.close(); process.exit(0); }
