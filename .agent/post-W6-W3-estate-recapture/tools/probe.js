(() => {
  // SYNTHETIC LAYOUT EVIDENCE, NOT PRODUCT DATA (post-W6 W3-estate fix round, Architect ruling 1/2). Runs after the
  // unmodified app screenshot and measurement, in the capture browser only; the page is navigated away (mock) right
  // after, so nothing persists. For each top-level panel: hide the real rows, append five clones of the first real row,
  // set EVERY intended variable text field of EVERY clone to exactly 160 characters, assert that it did (verified),
  // then measure the closed panel. Typed value columns (Value, Priority, Confidence, State, Lens, rank) keep their real
  // text. Objectives has five fixed rows; its worst case pads the matrix to five Sites and sets every Site name and
  // every cell label/note to 160 characters.
  const base = "Synthetic layout probe text that wraps across several lines in the narrow sticky column of this table ";
  const L = (n) => base.repeat(3).slice(0, n);
  const TYPED = /^(value|priority|confidence|state|lens|rank|#)$/i;
  const root = document.querySelector("main") ?? document.body;
  const out = [];
  for (const p of root.querySelectorAll("section.panel")) {
    if (p.parentElement.closest("section.panel")) continue;
    const title = (p.querySelector("h2")?.textContent ?? "").replace(/\s+/g, " ").trim();
    const before = Math.round(p.getBoundingClientRect().height);
    const inClosed = (n) => { for (let e = n; e && e !== p; e = e.parentElement) { const d = e.parentElement; if (d && d.tagName === "DETAILS" && !d.open && e.tagName !== "SUMMARY") return true; } return false; };
    const leavesOf = (el) => { const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); const a = [];
      while (w.nextNode()) { const n = w.currentNode; if (n.textContent.trim() && !inClosed(n.parentElement) && !n.parentElement.closest("summary")) a.push(n); } return a; };
    const measure = (clones, extra) => {
      const r = p.getBoundingClientRect();
      const clipped = [...p.querySelectorAll("*")].filter((e) => { if (inClosed(e) || !e.firstChild) return false; const s = getComputedStyle(e);
        return ((s.overflowX === "hidden" || s.overflowX === "clip" || s.textOverflow === "ellipsis") && e.scrollWidth > e.clientWidth + 1)
          || ((s.overflowY === "hidden" || s.overflowY === "clip") && e.scrollHeight > e.clientHeight + 2); }).length;
      const innerV = [...p.querySelectorAll("*")].filter((e) => { const s = getComputedStyle(e); return (s.overflowY === "auto" || s.overflowY === "scroll") && e.scrollHeight > e.clientHeight + 1 && e.clientHeight > 0; })
        .map((e) => ({ cls: String(e.className).slice(0, 50), sh: e.scrollHeight, ch: e.clientHeight }));
      const scr = [...p.querySelectorAll("*")].filter((e) => { const s = getComputedStyle(e); return (s.overflowX === "auto" || s.overflowX === "scroll") && e.clientWidth > 0 && e.scrollWidth > e.clientWidth + 1; })
        .map((e) => ({ cls: String(e.className).slice(0, 40), sw: e.scrollWidth, cw: e.clientWidth }));
      return { synthetic: true, h: Math.round(r.height), cloneRowHs: clones.map((c) => Math.round(c.getBoundingClientRect().height)), clipped, innerV, tableScrollers: scr,
        docOverflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth, ...extra };
    };
    if (p.querySelector(".objective-matrix")) {
      const head = p.querySelector(".matrix-head"); const mrows = [...p.querySelectorAll(".matrix-row")];
      const heads = [...head.querySelectorAll("[role=columnheader]")].slice(1);
      let sites = heads.length; let added = 0;
      while (sites < 5) { // pad to five Sites by cloning the last Site column
        head.appendChild(head.lastElementChild.cloneNode(true)); mrows.forEach((r) => r.appendChild(r.lastElementChild.cloneNode(true))); sites += 1; added += 1; }
      for (const r of [head, ...mrows]) r.style.gridTemplateColumns = `1.2fr repeat(${sites}, minmax(64px, 1fr))`;
      let want = 0; let got = 0;
      for (const h of head.querySelectorAll("[role=columnheader]")) { if (h.textContent.trim() === "Objective") continue;
        const t = leavesOf(h).filter((n) => !n.parentElement.closest("small")); t.forEach((n) => { n.textContent = L(160); want += 1; if (n.textContent.length === 160) got += 1; }); }
      for (const r of mrows) for (const c of r.querySelectorAll("[role=cell]")) { const ls = leavesOf(c); ls.forEach((n) => { n.textContent = L(160); want += 1; if (n.textContent.length === 160) got += 1; }); }
      out.push({ title, before, rows: mrows.length, paddedSites: added, sites, verified: want > 0 && want === got, intendedFields: want, fields160: got, primary: measure(mrows, {}) });
      continue;
    }
    const rows = [...p.querySelectorAll("tbody tr")].filter((r) => !r.querySelector("td[colspan]") && !inClosed(r));
    if (!rows.length) { out.push({ title, before, rows: 0 }); continue; }
    const tmpl = rows[0]; const parent = tmpl.parentElement;
    const heads = [...tmpl.closest("table").querySelectorAll("thead th")].map((h) => h.textContent.trim());
    const intended = heads.map((h, i) => (TYPED.test(h) ? -1 : i)).filter((i) => i >= 0);
    rows.forEach((r) => { r.style.display = "none"; });
    const clones = [];
    for (let i = 0; i < 5; i += 1) { const c = tmpl.cloneNode(true); c.style.display = ""; parent.appendChild(c); clones.push(c); }
    let want = 0; let got = 0; const cols = new Set();
    for (const c of clones) {
      const tds = [...c.children];
      for (const i of intended) { const td = tds[i]; if (!td) continue; const ls = leavesOf(td); if (!ls.length) { want += 1; continue; } cols.add(heads[i]);
        ls.forEach((n) => { n.textContent = L(160); want += 1; if (n.textContent.length === 160) got += 1; }); }
      const full = c.querySelector("[data-estate-limits]"); if (full) full.textContent = L(160);
    }
    out.push({ title, before, rows: rows.length, clones: clones.length, intendedColumns: intended.map((i) => heads[i]), changedColumns: [...cols], verified: clones.length === 5 && want > 0 && want === got, intendedFields: want, fields160: got, primary: measure(clones, {}) });
  }
  return out;
})()
