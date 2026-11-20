"""Render build-pipeline-and-checks-speedup.md to a self-contained HTML page with inline SVG figures (offline).

Usage: python3 render_build_pipeline_html.py build-pipeline-and-checks-speedup.md build-pipeline-and-checks-speedup.html
A line `<!--diagram:name-->` in the .md places a figure. Each figure has a wide layout and a stacked narrow layout for
phone widths (shown below 1000 px), so labels stay legible. Approach follows
Docs/demo-sprint/product-direction-layer4/render_product_transition_html.py. Figures carry the measured or recorded
values stated in the .md (section 10 names the sources); the two-series palette (before = amber, after = blue) passed
the dataviz palette validator in light and dark."""
import html, re, sys, textwrap, zlib

SRC, OUT = sys.argv[1], sys.argv[2]

def esc(s): return html.escape(str(s), quote=True)

def label(x, y, t, anchor="start", fs=12, cls="lb", weight=None):
    w = f' font-weight="{weight}"' if weight else ''
    return f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}" font-size="{fs}"{w}>{esc(t)}</text>'

def box(x, y, w, h, lines, cls="bx", fs=13):
    out = [f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>']
    lh = fs + 3; y0 = y + h / 2 - (len(lines) - 1) * lh / 2 + fs * 0.35
    for i, t in enumerate(lines):
        wt = ' font-weight="600"' if i == 0 else ''
        out.append(f'<text class="t" x="{x + w/2}" y="{y0 + i*lh:.1f}" text-anchor="middle" font-size="{fs}"{wt}>{esc(t)}</text>')
    return "".join(out)

def arrow(pts):
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    return f'<path class="ar" d="{d}" marker-end="url(#m)"/>'

DEFS = ('<defs><marker id="m" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker></defs>')

def svg(w, h, body, title, desc, narrow):
    k = zlib.crc32(title.encode())
    def one(cls, w_, h_, b_, sfx):
        mid = f"{k}{sfx}"
        b_ = b_.replace("url(#m)", f"url(#m{mid})")
        return (f'<svg class="{cls}" viewBox="0 0 {w_} {h_}" role="img" aria-labelledby="t{mid} d{mid}">'
                f'<title id="t{mid}">{esc(title)}</title><desc id="d{mid}">{esc(desc)}</desc>'
                f'{DEFS.replace(chr(34) + "m" + chr(34), chr(34) + "m" + mid + chr(34))}{b_}</svg>')
    return (f'<figure class="dg">{one("wide", w, h, body, "w")}{one("narrow", *narrow, "n")}'
            f'<figcaption>{esc(title)}</figcaption></figure>')

NW = 400

def legend(x, y, items, fs=12.5):
    out, cx = [], x
    for cls, text in items:
        out.append(f'<rect class="{cls}" x="{cx}" y="{y - 10}" width="14" height="10" rx="3"/>')
        out.append(label(cx + 20, y, text, fs=fs, cls="t"))
        cx += 28 + len(text) * fs * 0.52
    return "".join(out)

def fmt(v, unit):
    s = f"{v:,.1f}".rstrip("0").rstrip(".") if isinstance(v, float) else f"{v:,}"
    return f"{s} {unit}".strip()

def hbars(rows, vmax, unit, title, desc, series=None, note=None):
    """rows: (label, [values], tooltip). One value = single series (bar class s1); two = before (s0) / after (s1)."""
    def body(L, R, lab_above, fs):
        sx = (R - L) / vmax
        b, y = [], 14
        nser = max(len(v) for _, v, _ in rows)
        bh = 14 if nser == 1 else 11
        for name, vals, tip in rows:
            if lab_above:
                b.append(label(8, y + 13, name, fs=fs, cls="t")); yb = y + 20
            else:
                b.append(label(L - 10, y + 10 + (nser - 1) * 6.5, name, anchor="end", fs=fs, cls="t")); yb = y
            for k, v in enumerate(vals):
                cls = "s1" if (nser == 1 or k == 1) else "s0"
                yy = yb + k * (bh + 2)
                w = max(v * sx, 2)
                b.append(f'<rect class="{cls}" x="{L}" y="{yy}" width="{w:.1f}" height="{bh}" rx="4">'
                         f'<title>{esc(name)}: {esc(fmt(v, unit))}{(" - " + esc(tip)) if tip else ""}</title></rect>')
                b.append(label(L + w + 6, yy + bh - 2, fmt(v, unit), fs=fs - 1))
            y = yb + nser * (bh + 2) + (12 if lab_above else 10)
        b.append(f'<line class="axis" x1="{L}" x2="{L}" y1="8" y2="{y - 4}"/>')
        if series:
            b.append(legend(L if not lab_above else 10, y + 12, series)); y += 22
        if note:
            parts = note.split("\n")
            if lab_above:  # narrow layout: wrap so no line runs past the 400-unit viewBox
                parts = [w for p in parts for w in textwrap.wrap(p, 50, break_on_hyphens=False)]
            for ln in parts:
                b.append(label(L if not lab_above else 10, y + 14, ln, fs=fs - 0.5)); y += 18
        return "".join(b), y + 8
    wb, wh = body(330, 880, False, 12.5)
    nb, nh = body(10, NW - 70, True, 13)
    return svg(980, wh, wb, title, desc, (NW, nh, nb))

# ---------------------------------------------------------------- figures
def f_pipeline():
    st = [(["Spec and", "pre-flight"], "bx", "Architect"), (["Build", "focused tests"], "bx", "~40 min"),
          (["Fresh review", "+ fix round"], "bx", "~30 + 25 min"), (["check-all", "central queue"], "bxw", "~45 min, 2.5 runs"),
          (["Live check", "on demo DB"], "bx", "~15 min"), (["Merge"], "bx", ""), (["Demo DB", "prepare"], "bxw", "~2 h when needed")]
    b, x, w, gap = [], 8, 122, 17
    for i, (t, cls, tm) in enumerate(st):
        b.append(box(x, 30, w, 62, t, cls=cls, fs=12.5))
        if tm: b.append(label(x + w / 2, 112, tm, anchor="middle", fs=11.5))
        if i < len(st) - 1: b.append(arrow([(x + w, 61), (x + w + gap - 2, 61)]))
        x += w + gap
    b.append(label(8, 18, "Around every slice (VPS, since 12 Nov)", fs=13, cls="t", weight="600"))
    b.append(f'<rect class="bxw" x="8" y="132" width="14" height="10" rx="3"/>')
    b.append(label(28, 141, "where the machine time and the waiting are; the other stages are agent work this evaluation does not shorten", fs=12, cls="t"))
    nb, y = [], 8
    nb.append(label(10, y + 14, "Around every slice", fs=14, cls="t", weight="600")); y += 26
    for i, (t, cls, tm) in enumerate(st):
        nb.append(box(10, y, 250, 46, [" ".join(t)], cls=cls, fs=14))
        if tm: nb.append(label(270, y + 28, tm, fs=13))
        if i < len(st) - 1: nb.append(arrow([(135, y + 46), (135, y + 62)]))
        y += 64
    nb.append(f'<rect class="bxw" x="10" y="{y}" width="14" height="10" rx="3"/>')
    nb.append(label(30, y + 10, "machine time and waiting", fs=13, cls="t"))
    return svg(980, 152, "".join(b), "Figure 1. What runs around a change, with typical elapsed time per stage",
               "Spec and pre-flight; build with focused tests, about 40 minutes; fresh review and fix round, about 30 plus 25; check-all in the central queue, about 45 minutes over 2.5 runs; live check on the demo database, about 15; merge; demo database prepare, about 2 hours when needed. check-all and the prepare are highlighted as the machine-time and waiting stages.",
               (NW, y + 24, "".join(nb)))

def f_guardtimes():
    rows = [("Estate guard self-tests (17)", [464.3], "79% of check-all"), ("Dependency direction (seam)", [30.8], ""),
            ("Configuration persistence (seam)", [17.2], "writer guard, rule 8"), ("Navigation truthfulness, standalone", [16.3], "duplicate of the seam module"),
            ("Navigation truthfulness (seam)", [15.8], ""), ("Navigation rail fixtures (seam)", [12.5], ""),
            ("Simulator gate (seam)", [8.1], ""), ("Shell overflow (seam)", [7.6], ""), ("Site substrate (seam)", [6.1], ""),
            ("Run setup (seam)", [5.2], ""), ("Fuel wording", [4.6], ""), ("Missing-claim scan fixtures", [4.0], ""),
            ("20 other guards and modules", [20.3], "each under 5 s")]
    return hbars(rows, 500, "s", "Figure 2. check-all, each guard timed on its own (measured 2026-11-18, seconds)",
                 "Estate guard self-tests 464.3 s; dependency direction 30.8; configuration persistence 17.2; navigation truthfulness standalone 16.3 (a duplicate) and in the seams 15.8; navigation rail fixtures 12.5; simulator gate 8.1; shell overflow 7.6; site substrate 6.1; run setup 5.2; fuel wording 4.6; missing-claim fixtures 4.0; the 20 others 20.3 together. The whole command took 589.6 s.",
                 note="Whole command, run as today: 589.6 s wall, 1.24 GB peak, 21/21 passed.")

def f_checkall():
    rows = [("Today, as run (measured)", [589.6], "serial"), ("Self-tests only when the guard changes (A2)", [126.0], "estimate from measured parts"),
            ("Duplicate check removed (A5)", [110.0], "estimate"), ("Four guards at a time (A4)", [40.0], "estimate; critical path 31 s"),
            ("Full mode, guard changed: self-tests at -n 4", [165.0], "estimate")]
    b = hbars(rows, 620, "s", "Figure 4. check-all wall time today and after each step (seconds)",
              "Today 589.6 s measured. Estimates: self-tests only when their guard changes 126 s; duplicate removed 110 s; four at a time about 40 s; full mode with the self-tests in parallel about 165 s.",
              series=[("s0", "Measured today"), ("s1", "Estimate after the step")],
              note="Estimates are built from the measured per-guard times.")
    return b.replace('class="s1" x="330" y="14"', 'class="s0" x="330" y="14"', 1).replace('class="s1" x="10" y="34"', 'class="s0" x="10" y="34"', 1)

def f_prepare():
    rows = [("KOBO-001: 72 runs", [28.7], "1,724.7 s"), ("Other: tree, mini-depth, objectives, comparisons, ticks", [26.4], "remainder of 1 h 59 min"),
            ("Self-check: 54 rows", [24.6], "1,473.9 s, one row at a time"), ("KISIWA-001: 10 nights", [19.9], "1,195.1 s"),
            ("Drains (snapshots, threads)", [14.4], "817.2 + 47.6 s"), ("Stored period and day rows", [3.0], "178.2 s"),
            ("EV-LAB-001 and COLD-LAB-001", [1.3], "52.4 + 22.4 s"), ("Backfills and mill step", [0.7], "42.2 s")]
    return hbars(rows, 32, "min", "Figure 3. Where the 1 h 59 min demo database build goes (recorded, walk1113, minutes)",
                 "KOBO-001 28.7 minutes; other steps 26.4; self-check 24.6; KISIWA-001 19.9; drains 14.4; stored rows 3.0; EV and cold Sites 1.3; backfills and mill 0.7. Kobo, Kisiwa and the self-check run one after another.",
                 note="Kobo and Kisiwa run one after the other; the self-check runs one row at a time.\nSource: /opt/assetecon/AssetOpsV1-walk/var/polish_walk1113-prepare.log (read only).")

def f_cycle():
    rows = [("Build with focused tests", [40, 40], ""), ("Fresh review", [30, 30], ""), ("Fix round + re-review (avg)", [25, 23], ""),
            ("check-all, 2.5 runs + queue", [45, 2], "measured 589.6 s quiet; loaded and queued before"),
            ("Live check or parity", [15, 15], ""), ("Total per slice", [155, 110], "range 130-185 before, 100-125 after")]
    return hbars(rows, 170, "min", "Figure 6. Elapsed minutes per typical slice, before and after the 'now' actions (estimate)",
                 "Build 40 and 40; review 30 and 30; fix round 25 and 23; check-all with queue 45 and 2; live check 15 and 15; total about 155 before and about 110 after.",
                 series=[("s0", "Before (today)"), ("s1", "After PIPE-1")])

def f_ranking():
    rows = [("A2 Self-tests only on guard change", [38.4], ""), ("A3 End the central check-all queue", [21.0], ""),
            ("A5 Remove the duplicate check", [6.7], ""), ("A4 Guards four at a time", [2.4], ""),
            ("A8 Verified DB snapshots", [2.0], ""), ("A10 tsc incremental", [1.6], ""), ("A6 Retire stale v69/S1-S7 guards", [1.1], ""),
            ("A7 Parallel self-check rows", [0.65], ""), ("A12 Two Sites at once in prepare", [0.28], "later")]
    return hbars(rows, 42, "", "Figure 5. Action score = hours saved per fortnight x confidence / lane-days (estimate)",
                 "A2 38.4; A3 21.0; A5 6.7; A4 2.4; A8 2.0; A10 1.6; A6 1.1; A7 0.65; A12 0.28. A1, the defect fix, ranks first regardless of score.",
                 note="A1 (the PYTHONPATH defect fix) ranks first regardless of score.")

MARKERS = {"pipeline": f_pipeline, "guardtimes": f_guardtimes, "checkall": f_checkall, "prepare": f_prepare,
           "cycle": f_cycle, "ranking": f_ranking}

# ---------------------------------------------------------------- markdown subset
def slug(t):
    t = re.sub(r"<[^>]+>", "", t).lower(); t = re.sub(r"[^\w\s-]", "", t)
    return re.sub(r"[\s_]+", "-", t).strip("-")

def inline(s):
    out = []
    for p in re.split(r"(`[^`]+`)", s):
        if p.startswith("`") and p.endswith("`") and len(p) > 1:
            out.append(f"<code>{html.escape(p[1:-1])}</code>")
        else:
            p = html.escape(p, quote=False)
            p = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", p)
            p = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", p)
            out.append(p)
    return "".join(out)

def cells(row):
    return [c.strip() for c in re.split(r"(?<!\\)\|", row.strip().strip("|"))]

lines = open(SRC, encoding="utf-8").read().split("\n")
body, toc, i, used = [], [], 0, []
while i < len(lines):
    ln = lines[i]
    mk = re.fullmatch(r"<!--diagram:(\w+)-->", ln.strip())
    if mk:
        body.append(MARKERS[mk.group(1)]()); used.append(mk.group(1)); i += 1; continue
    m = re.match(r"^(#{1,4}) (.*)", ln)
    if m:
        lvl, txt = len(m.group(1)), m.group(2); sid = slug(txt)
        body.append(f'<h{lvl} id="{sid}">{inline(txt)}</h{lvl}>')
        if lvl == 2: toc.append((sid, inline(txt)))
        i += 1; continue
    if ln.strip() == "---":
        body.append("<hr>"); i += 1; continue
    if ln.startswith("|"):
        rows = []
        while i < len(lines) and lines[i].startswith("|"):
            rows.append(lines[i]); i += 1
        head, data = cells(rows[0]), [cells(r) for r in rows[2:]]
        aligns = ["num" if c.strip().endswith(":") else "" for c in cells(rows[1])]
        t = ['<div class="tw" tabindex="0" role="region" aria-label="table"><table><thead><tr>']
        t += [f'<th class="{a}">{inline(c)}</th>' for c, a in zip(head, aligns)]
        t.append("</tr></thead><tbody>")
        for r in data:
            t.append("<tr>" + "".join(f'<td class="{a}">{inline(c)}</td>' for c, a in zip(r, aligns)) + "</tr>")
        t.append("</tbody></table></div>"); body.append("".join(t)); continue
    if re.match(r"^\d+\. ", ln):
        items = []
        while i < len(lines) and re.match(r"^\d+\. ", lines[i]):
            items.append(re.sub(r"^\d+\. ", "", lines[i])); i += 1
        body.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>"); continue
    if ln.startswith("- "):
        items = []
        while i < len(lines) and lines[i].startswith("- "):
            items.append(lines[i][2:]); i += 1
        body.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>"); continue
    if not ln.strip():
        i += 1; continue
    para = []
    while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||- |\d+\. |---|<!--)", lines[i]):
        para.append(lines[i]); i += 1
    body.append(f"<p>{inline(' '.join(para))}</p>")

assert sorted(used) == sorted(MARKERS), (used, list(MARKERS))
tochtml = '<nav class="toc" aria-label="Contents"><strong>Contents</strong><ul>' + "".join(
    f'<li><a href="#{s}">{t}</a></li>' for s, t in toc) + "</ul></nav>"
body.insert(body.index("<hr>"), tochtml)

TOK_L = ("--bg:#f6f7f9;--fg:#18212f;--muted:#5d6878;--line:#dfe3ea;--card:#fff;--accent:#1d4ed8;--code:#eef1f5;"
         "--warn:#fdf2e3;--warnline:#b45309;--s0:#b45309;--s1:#1d4ed8")
TOK_D = ("--bg:#11161d;--fg:#e4e8ee;--muted:#9aa5b4;--line:#2a3340;--card:#171d26;--accent:#7aa2f7;--code:#1f2733;"
         "--warn:#2a2116;--warnline:#d97706;--s0:#d97706;--s1:#3b82f6")
CSS = f""":root{{{TOK_L}}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{{TOK_D}}}}}
:root[data-theme=dark]{{{TOK_D}}}
""" + """body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}
.wrap{max-width:1100px;margin:0 auto;padding:24px 16px 80px}h1{font-size:28px;line-height:1.25}
h2{margin-top:44px;padding-top:12px;border-top:1px solid var(--line)}h3{margin-top:28px}
a{color:var(--accent)}code{background:var(--code);padding:1px 4px;border-radius:3px;font-size:.88em;overflow-wrap:anywhere}
.tw{overflow-x:auto;margin:12px 0;border:1px solid var(--line);border-radius:6px;background:var(--card)}
table{border-collapse:collapse;width:100%;font-size:13.5px}th,td{text-align:left;vertical-align:top;padding:7px 9px;border-bottom:1px solid var(--line)}
th{background:var(--code);font-weight:600}td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
hr{border:0;border-top:1px solid var(--line);margin:32px 0}
.toc{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:12px 16px;margin:20px 0}.toc ul{margin:6px 0;padding-left:18px}
figure.dg{margin:16px 0;padding:12px;background:var(--card);border:1px solid var(--line);border-radius:6px}
figure.dg svg{display:block;width:100%;height:auto}figure.dg svg.narrow{display:none;max-width:520px;margin:0 auto}
@media (max-width:999px){figure.dg svg.wide{display:none}figure.dg svg.narrow{display:block}}
figcaption{color:var(--muted);font-size:13px;margin-top:6px}
svg .bx{fill:var(--card);stroke:var(--muted);stroke-width:1.2}svg .bxw{fill:var(--warn);stroke:var(--warnline);stroke-width:1.6}
svg .t{fill:var(--fg)}svg .lb{fill:var(--muted)}svg .ar{fill:none;stroke:var(--muted);stroke-width:1.6}svg .mk{fill:var(--muted)}
svg .axis{stroke:var(--muted);stroke-width:1}svg .s0{fill:var(--s0)}svg .s1{fill:var(--s1)}
svg rect.s0:hover,svg rect.s1:hover{opacity:.8}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}"""

page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Pipeline Speed-up Evaluation</title><style>' + CSS + '</style></head><body><main class="wrap">' + "".join(body) + "</main></body></html>")
open(OUT, "w", encoding="utf-8").write(page)
print("ok", len(page), "figures", len(used))
