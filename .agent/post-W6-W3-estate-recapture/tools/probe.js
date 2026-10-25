(() => {
  // LAYOUT PROBE ONLY (post-W6 W3-estate cap proof, rulings item 8 / Q17): runs after the app screenshot and measurement,
  // in the capture browser only; the page is navigated away (mock) right after, so nothing persists. Hides the real
  // rows of each top-level panel, appends five clones of its first row, sets each clone's first visible text to 160
  // characters and every other visible text of 25+ characters to 160 characters (the longest gap/refusal budget),
  // then measures the closed panel. Never screenshotted as product evidence except the labelled -worstcase-probe.png.
  const base = "Worst case layout probe text that wraps across several lines in the narrow sticky column of this table ";
  const L = (n) => base.repeat(3).slice(0, n);
  const root = document.querySelector("main") ?? document.body;
  const out = [];
  for (const p of root.querySelectorAll("section.panel")) {
    if (p.parentElement.closest("section.panel")) continue;
    const title = (p.querySelector("h2")?.textContent ?? "").replace(/\s+/g, " ").trim();
    const before = Math.round(p.getBoundingClientRect().height);
    const inClosed = (n) => { for (let e = n; e && e !== p; e = e.parentElement) { const d = e.parentElement; if (d && d.tagName === "DETAILS" && !d.open && e.tagName !== "SUMMARY") return true; } return false; };
    const rows = [...p.querySelectorAll("tbody tr, .matrix-row[role='row']")].filter((r) => !r.querySelector("td[colspan]") && !inClosed(r));
    if (!rows.length) { out.push({ title, before, rows: 0 }); continue; }
    const tmpl = rows[0]; const parent = tmpl.parentElement;
    rows.forEach((r) => { r.style.display = "none"; });
    const clones = [];
    for (let i = 0; i < 5; i += 1) { const c = tmpl.cloneNode(true); c.style.display = ""; parent.appendChild(c); clones.push(c); }
    let changed = 0;
    for (const c of clones) {
      const w = document.createTreeWalker(c, NodeFilter.SHOW_TEXT); const leaves = [];
      while (w.nextNode()) { const n = w.currentNode; if (n.textContent.trim() && !inClosed(n.parentElement)) leaves.push(n); }
      leaves.forEach((n, i) => { if (i === 0 || n.textContent.trim().length >= 25) { n.textContent = L(160); changed += 1; } });
    }
    const r = p.getBoundingClientRect();
    const clipped = [...p.querySelectorAll("*")].filter((e) => { if (inClosed(e) || !e.firstChild) return false; const s = getComputedStyle(e);
      return ((s.overflowX === "hidden" || s.overflowX === "clip" || s.textOverflow === "ellipsis") && e.scrollWidth > e.clientWidth + 1)
        || ((s.overflowY === "hidden" || s.overflowY === "clip") && e.scrollHeight > e.clientHeight + 2); }).length;
    const innerV = [...p.querySelectorAll("*")].filter((e) => { const s = getComputedStyle(e); return (s.overflowY === "auto" || s.overflowY === "scroll") && e.scrollHeight > e.clientHeight + 1 && e.clientHeight > 0; })
      .map((e) => ({ cls: String(e.className).slice(0, 50), sh: e.scrollHeight, ch: e.clientHeight }));
    out.push({ title, before, rows: rows.length, after: Math.round(r.height), changedLeaves: changed,
      cloneRowHs: clones.map((c) => Math.round(c.getBoundingClientRect().height)), clipped, innerV,
      docOverflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth });
  }
  return out;
})()
