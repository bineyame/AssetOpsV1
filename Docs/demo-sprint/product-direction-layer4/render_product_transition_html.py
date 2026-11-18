"""Render product-transition-and-roadmap.md to a self-contained HTML page with inline SVG diagrams (offline).

Usage: python3 render_product_transition_html.py product-transition-and-roadmap.md product-transition-and-roadmap.html
The seven diagrams are drawn here, in the order of the mermaid blocks in the .md (which stay as the plain-text source)."""
import html, re, sys, zlib

SRC, OUT = sys.argv[1], sys.argv[2]

# ---------------------------------------------------------------- SVG helpers
def esc(s): return html.escape(s, quote=True)

def box(x, y, w, h, lines, cls="bx", fs=13):
    out = [f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>']
    n = len(lines); lh = fs + 3
    y0 = y + h / 2 - (n - 1) * lh / 2 + fs * 0.35
    for i, t in enumerate(lines):
        weight = ' font-weight="600"' if i == 0 else ''
        out.append(f'<text class="t" x="{x + w/2}" y="{y0 + i*lh:.1f}" text-anchor="middle" font-size="{fs}"{weight}>{esc(t)}</text>')
    return "".join(out)

def arrow(pts, cls="ar", marker="m"):
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    return f'<path class="{cls}" d="{d}" marker-end="url(#{marker})"/>'

def label(x, y, t, anchor="start", fs=12, cls="lb", weight=None):
    w = f' font-weight="{weight}"' if weight else ''
    return f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}" font-size="{fs}"{w}>{esc(t)}</text>'

def diamond(cx, cy, w, h, lines):
    pts = f"{cx},{cy-h/2} {cx+w/2},{cy} {cx},{cy+h/2} {cx-w/2},{cy}"
    out = [f'<polygon class="bx" points="{pts}"/>']
    lh = 14; y0 = cy - (len(lines)-1)*lh/2 + 4
    for i, t in enumerate(lines):
        out.append(f'<text class="t" x="{cx}" y="{y0+i*lh}" text-anchor="middle" font-size="11.5">{esc(t)}</text>')
    return "".join(out)

DEFS = ('<defs><marker id="m" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>'
        '<marker id="mc" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        '<path d="M0,0 L10,5 L0,10 z" class="mkc"/></marker></defs>')

def svg(w, h, body, title, desc):
    return (f'<figure class="dg"><svg viewBox="0 0 {w} {h}" role="img" aria-labelledby="t{zlib.crc32(title.encode())} d{zlib.crc32(title.encode())}">'
            f'<title id="t{zlib.crc32(title.encode())}">{esc(title)}</title><desc id="d{zlib.crc32(title.encode())}">{esc(desc)}</desc>{DEFS}{body}</svg>'
            f'<figcaption>{esc(title)}</figcaption></figure>')

# ---------------------------------------------------------------- diagram 1: today vs Layer 4
def d1():
    b = []
    b.append(label(10, 24, "Today: signal first", fs=14, weight="600"))
    xs = [10, 206, 402, 598, 794]
    today = [["Telemetry and", "operational records"], ["Analyses", "dispatch, fuel balance,", "excursions, faults"],
             ["Findings", "what looks wrong"], ["Gross exposure", "up to this much"], ["One fixed trial", "(mini-grid only)"]]
    for x, t in zip(xs, today): b.append(box(x, 38, 186, 70, t, fs=12))
    for i in range(4): b.append(arrow([(xs[i]+186, 73), (xs[i+1]-2, 73)]))
    b.append(label(10, 190, "Layer 4: structure first", fs=14, weight="600"))
    l4 = [["Define", "each outcome as factors", "down to source records"], ["Observe", "factors from records;", "outcome computed upward"],
          ["Evaluate", "options as factor changes,", "against no action"], ["Choose", "one plan within budget,", "crews, rules, rights"],
          ["Prove", "same factors after;", "three verdicts"]]
    for x, t in zip(xs, l4): b.append(box(x, 204, 186, 76, t, cls="bxa", fs=12))
    for i in range(4): b.append(arrow([(xs[i]+186, 242), (xs[i+1]-2, 242)]))
    b.append(arrow([(887, 280), (887, 306), (299, 306), (299, 282)]))
    b.append(label(593, 320, "the loop repeats each period", anchor="middle", fs=11.5))
    b.append(arrow([(299, 108), (299, 202)], cls="ard"))
    b.append(label(310, 150, "today's analyses become", fs=11.5))
    b.append(label(310, 165, "observers of factors", fs=11.5))
    return svg(990, 330, "".join(b), "Figure 1. Today's product and Layer 4",
               "Today: records, analyses, findings, gross exposure, one fixed trial. Layer 4: define, observe, evaluate, choose, prove, in a loop; today's analyses become observers of factors.")

# ---------------------------------------------------------------- diagram 2: Kobo waterfall
def d2():
    steps = [("Plan|contribution", 1445, "tot"), ("Avoidable running|330 L", -412.5, "neg"), ("Necessary above|plan, 30 L", -37.5, "neg"),
             ("Unexplained fuel|120 L", -150.0, "neg"), ("More kWh billed|95 kWh", 38.0, "pos"), ("Actual|contribution", 883, "tot")]
    W, H, top, base = 960, 360, 30, 280
    scale = (base - top) / 1500
    bw, gap, x0 = 110, 30, 70
    b = []
    for v in (0, 500, 1000, 1500):
        y = base - v * scale
        b.append(f'<line class="grid" x1="{x0-10}" x2="{W-10}" y1="{y:.1f}" y2="{y:.1f}"/>')
        b.append(label(x0 - 14, y + 4, f"{v:,}", anchor="end", fs=11))
    run = 0
    for i, (name, v, kind) in enumerate(steps):
        x = x0 + i * (bw + gap)
        if kind == "tot":
            lo, hi = 0, v; run = v
        else:
            lo, hi = sorted((run, run + v)); run += v
        y1, y2 = base - hi * scale, base - lo * scale
        val = f"{v:,.0f}" if kind == "tot" else (f"{v:+,.2f}".replace("+", "+").replace("-", "−"))
        b.append(f'<rect class="w{kind}" x="{x}" y="{y1:.1f}" width="{bw}" height="{max(y2-y1,2):.1f}" rx="4"><title>{esc(name.replace("|", " "))}: {esc(val)}</title></rect>')
        b.append(label(x + bw/2, y1 - 7, val, anchor="middle", fs=12.5, cls="t", weight="600"))
        l1, l2 = name.split("|")
        b.append(label(x + bw/2, base + 20, l1, anchor="middle", fs=11.5))
        if l2: b.append(label(x + bw/2, base + 35, l2, anchor="middle", fs=11.5))
        if i < len(steps) - 1:
            yr = base - run * scale
            b.append(f'<line class="conn" x1="{x+bw}" x2="{x+bw+gap}" y1="{yr:.1f}" y2="{yr:.1f}"/>')
    b.append(label(x0, H - 8, "Demo values (derived-values.json). Orange lowers contribution, blue raises it; grey bars are totals. Diesel at 1.25 per litre, tariff 0.40 per kWh.", fs=11))
    return svg(W, H, "".join(b), "Figure 2. Kobo, October: contribution 1,445 planned, 883 actual (demo values)",
               "Waterfall: plan 1,445; minus 412.50 avoidable running; minus 37.50 necessary running above plan; minus 150.00 unexplained fuel; plus 38.00 more kWh billed; actual 883.")

# ---------------------------------------------------------------- diagram 3: what operators have vs what AssetEcon adds
def d3():
    b = []
    b.append(label(10, 22, "What operators typically already have", fs=13, weight="600"))
    have = [["Monitoring / EMS / CPMS", "what the assets are doing"], ["Billing, vending, ERP", "what was charged and paid"],
            ["Contracts and spreadsheets", "warranties, SLAs, plans"]]
    for i, t in enumerate(have): b.append(box(10, 36 + i*88, 250, 70, t))
    b.append(f'<rect class="grp" x="330" y="36" width="760" height="246" rx="10"/>')
    b.append(label(345, 58, "What AssetEcon adds: the join, in money", fs=13, weight="600"))
    S = (350, 120, 180, 92); O = (556, 120, 160, 92); PL = (742, 120, 150, 92); PR = (918, 120, 155, 92)
    b.append(box(*S, ["Outcome structure", "each figure built", "from factors, with", "its evidence class"], cls="bxa", fs=11.5))
    b.append(box(*O, ["Options", "against no action,", "with service rules", "and rights"], cls="bxa", fs=11.5))
    b.append(box(*PL, ["One plan", "within budget", "and crews"], cls="bxa", fs=12))
    b.append(box(*PR, ["Proof", "in three verdicts"], cls="bxa", fs=12))
    for i in range(3): b.append(arrow([(260, 71 + i*88), (300, 71 + i*88), (300, 166), (348, 166)]))
    b.append(arrow([(530, 166), (554, 166)])); b.append(arrow([(716, 166), (740, 166)])); b.append(arrow([(892, 166), (916, 166)]))
    b.append(arrow([(995, 212), (995, 250), (440, 250), (440, 214)]))
    b.append(label(718, 268, "proof feeds the next period's observation", anchor="middle", fs=11.5))
    return svg(1100, 300, "".join(b), "Figure 3. Where the differentiation sits: the join across systems the operator already has",
               "Monitoring, billing and contract systems feed an outcome structure, which leads to options, one plan, and proof, in a loop.")

# ---------------------------------------------------------------- diagram 4: engagement path
def d4():
    b = []
    y, h = 40, 76
    b.append(box(10, y, 150, h, ["Client demo", "mock-up, design", "values labelled"], fs=12))
    b.append(diamond(255, y + h/2, 150, 96, ["Qualified?", "data access, a decision", "to investigate"]))
    b.append(box(345, y, 175, h, ["Paid diagnostic", "3 sites, ~4 weeks after", "data; analyst-prepared"], cls="bxa", fs=12))
    b.append(diamond(615, y + h/2, 150, 96, ["Factor bridge", "reconciled and", "compelling?"]))
    b.append(box(705, y, 175, h, ["Pilot / field validation", "~3 months; product on", "their data; one change"], cls="bxa", fs=12))
    b.append(diamond(975, y + h/2, 150, 96, ["Verdicts and", "the buyer's own", "judgement?"]))
    b.append(box(1065, y, 135, h, ["Paid", "continuation", "and reference"], cls="bxa", fs=12))
    cy = y + h/2
    for x1, x2 in ((160, 180), (330, 343), (520, 540), (690, 703), (880, 900), (1050, 1063)):
        b.append(arrow([(x1, cy), (x2, cy)]))
    for x, t in ((337, "yes"), (697, "yes"), (1057, "yes")): b.append(label(x - 4, cy - 8, t, anchor="end", fs=11))
    b.append(box(165, 200, 180, 70, ["Data assessment", "for cold and EV", "prospects until their", "vertical is built"], fs=12))
    b.append(arrow([(255, cy + 48), (255, 198)])); b.append(label(262, 170, "not yet", fs=11))
    b.append(box(705, 200, 175, 70, ["Stop or rethink", "record why"], fs=12))
    b.append(arrow([(615, cy + 48), (615, 235), (703, 235)])); b.append(label(622, 170, "no", fs=11))
    b.append(arrow([(975, cy + 48), (975, 235), (882, 235)])); b.append(label(982, 170, "no", fs=11))
    return svg(1210, 290, "".join(b), "Figure 4. The engagement path, with its gates",
               "Demo, then a qualification gate; qualified prospects get a paid diagnostic, others a data assessment. If the factor bridge is reconciled and compelling, a pilot follows; if its verdicts hold, paid continuation. Failed gates lead to stop or rethink.")

# ---------------------------------------------------------------- diagram 5: dependencies
def d5():
    b = []
    W = 125; xs = [20 + i*147 for i in range(7)]
    crit = [["2 Commercial", "records and", "file intake"], ["3 Structure and", "factor bridge"], ["4 Decisions:", "options, rules,", "no action"],
            ["6 Rights in", "repair decisions"], ["5 Plan and the", "restructured", "Portfolio"], ["8a Cold", "(or EV first)"], ["8b EV", "(or cold)"]]
    yc, hc = 150, 74
    for x, t in zip(xs, crit): b.append(box(x, yc, W, hc, t, cls="bxa", fs=11.5))
    for i in range(6):
        cls = "arc" if i < 5 else "ar"
        b.append(arrow([(xs[i]+W, yc+hc/2), (xs[i+1]-2, yc+hc/2)], cls=cls, marker="mc" if i < 5 else "m"))
    yt = 30
    b.append(box(xs[0], yt, W, 66, ["Pilot lane", "agreements,", "profiles,", "diagnostics"], cls="bxp", fs=12))
    b.append(box(xs[1], yt, W, 66, ["Lane B", "build speed,", "re-benchmark"], cls="bxp", fs=12))
    b.append(box(xs[2], yt, W, 66, ["Calibration lane", "replays on", "demo data"], cls="bxp", fs=12))
    b.append(box(xs[4], yt, W, 66, ["1 Honest screens", "(UI only)"], cls="bxp", fs=12))
    b.append(arrow([(xs[0]+W/2, yt+66), (xs[0]+W/2, yc-2)], cls="ard"))
    b.append(arrow([(xs[1]+W/2, yt+66), (xs[2]+20, yc-2)], cls="ard"))
    b.append(arrow([(xs[2]+W/2, yt+66), (xs[2]+W/2, yc-2)], cls="ard"))
    b.append(arrow([(xs[4]+W/2, yt+66), (xs[4]+W/2, yc-2)]))
    yb = 290
    b.append(box(xs[3], yb, W, 66, ["7 Proof:", "three verdicts"], cls="bxa", fs=12))
    b.append(box(xs[6], yb, W, 66, ["9 Pilot hardening", "field calibration", "evidence pack"], cls="bxa", fs=12))
    b.append(arrow([(xs[2]+W/2, yc+hc), (xs[3]+20, yb-2)]))
    b.append(arrow([(xs[3]+W, yb+12), (xs[5]+30, yb+12), (xs[5]+30, yc+hc+2)]))
    b.append(f'<path class="ar" d="M{xs[4]+W/2},{yc+hc} L{xs[4]+W/2},{yb+46}"/>')
    b.append(arrow([(xs[3]+W, yb+46), (xs[6]-2, yb+46)]))
    b.append(arrow([(xs[0]+20, yt), (xs[0]+20, 12), (1150, 12), (1150, yb+33), (xs[6]+W+2, yb+33)], cls="ard"))
    b.append(label(20, 392, "Thick orange arrows: the critical path (records → structure → decisions → rights → plan). Dashed: parallel lanes that feed a step.", fs=11.5))
    return svg(1170, 400, "".join(b), "Figure 5. Transition steps, dependencies and the critical path",
               "Critical path: commercial records, structure and factor bridge, decisions, rights, plan, then cold and EV. Parallel lanes: pilot lane, Lane B, calibration lane, honest screens. Proof follows decisions and precedes the second vertical; pilot hardening follows plan and proof.")

# ---------------------------------------------------------------- diagram 6: adapters
def d6():
    b = []
    srcs = [["Demo: emulated export", "'source-emulated'"], ["Bench: real device or", "sample export, 'bench-tested'"],
            ["Pilot: operator's export", "'field-integrated' /", "'observed-financial'"]]
    for i, t in enumerate(srcs): b.append(box(10, 20 + i*90, 230, 72, t, fs=12))
    b.append(f'<rect class="grp" x="280" y="70" width="680" height="150" rx="10"/>')
    b.append(label(295, 92, "Adapter = transport + parser + profile", fs=13, weight="600"))
    b.append(box(300, 110, 190, 90, ["Transport", "upload, scheduled drop", "(later: API)"], cls="bxa", fs=12))
    b.append(box(530, 110, 190, 90, ["Parser", "bytes to typed rows", "(pure, versioned)"], cls="bxa", fs=12))
    b.append(box(760, 110, 185, 90, ["Profile", "columns, units, timezone,", "personal-data fields"], cls="bxa", fs=12))
    b.append(box(990, 110, 180, 90, ["Commercial record store", "or evidence ledger"], fs=12))
    for i in range(3): b.append(arrow([(240, 56 + i*90), (265, 56 + i*90), (265, 155), (298, 155)]))
    b.append(arrow([(490, 155), (528, 155)])); b.append(arrow([(720, 155), (758, 155)])); b.append(arrow([(945, 155), (988, 155)]))
    b.append(label(620, 250, "From demo to pilot only transport and profile change; parser, records, observers and structure stay the same.", anchor="middle", fs=11.5))
    return svg(1180, 270, "".join(b), "Figure 6. File import first: one adapter shape from demo to pilot",
               "Emulated, bench and pilot exports enter through transport, parser and profile into the commercial record store or the evidence ledger.")

# ---------------------------------------------------------------- diagram 7: roadmap swimlanes
def d7():
    lanes = [("Product", [("Calibration lane + honest screens", 0, 1), ("Records and factor bridge (steps 2–3)", 0, 3),
                          ("Decisions and rights (steps 4, 6)", 2, 5), ("Plan and Portfolio (step 5)", 4, 6), ("Proof (step 7)", 4, 6),
                          ("Second vertical (8a or 8b)", 6, 8), ("Third vertical", 8, 10)]),
             ("Data", [("Diagnostic kit and profiles", 0, 1), ("Pilot profiles pinned", 2, 5), ("Field calibration on pilot data", 5, 7)]),
             ("Pilots", [("First mini-grid diagnostic", 1, 3), ("Mini-grid pilot (field validation)", 3, 7), ("Second-vertical diagnostic", 5, 7)]),
             ("Commercial", [("Demos and qualification", 0, 10), ("First conversion decision", 7, 7), ("Investor and lender evidence pack", 7, 9)])]
    L, R, top, rh = 300, 1150, 40, 24
    mw = (R - L) / 10
    b = []
    rows = sum(len(x[1]) + 1 for x in lanes)
    H = top + rows * rh + 40
    for m in range(11):
        x = L + m * mw
        b.append(f'<line class="grid" x1="{x:.1f}" x2="{x:.1f}" y1="{top-6}" y2="{top + rows*rh}"/>')
        b.append(label(x, top - 12, f"M{m}", anchor="middle", fs=11))
    y = top
    for li, (lane, items) in enumerate(lanes):
        b.append(f'<rect class="lane" x="0" y="{y}" width="{R+10}" height="{rh}"/>')
        b.append(label(8, y + 17, lane, fs=13, weight="600", cls="t"))
        y += rh
        for name, s, e in items:
            b.append(label(16, y + 16, name, fs=12))
            if s == e:
                cx = L + s * mw; cy = y + rh/2
                b.append(f'<polygon class="ms" points="{cx},{cy-8} {cx+8},{cy} {cx},{cy+8} {cx-8},{cy}"><title>{esc(name)}: M{s}</title></polygon>')
            else:
                b.append(f'<rect class="bar{li}" x="{L + s*mw + 1:.1f}" y="{y+5}" width="{(e-s)*mw - 2:.1f}" height="{rh-10}" rx="4"><title>{esc(name)}: M{s} to M{e}</title></rect>')
            y += rh
    b.append(label(L, H - 12, "Months from the owner's approval of the path. Estimates; ranges in §4.3. Pilot timing depends on a qualified prospect.", fs=11))
    return svg(R + 20, H, "".join(b), "Figure 7. Roadmap in four lanes: product, data, pilots, commercial",
               "Swimlane timeline over ten months: product steps, data work, pilots and commercial milestones, as listed in the table below it.")

DIAGRAMS = [d1, d2, d3, d4, d5, d6, d7]

# ---------------------------------------------------------------- markdown subset
def slug(t):
    t = re.sub(r"<[^>]+>", "", t).lower()
    t = re.sub(r"[^\w\s-]", "", t)
    return re.sub(r"[\s_]+", "-", t).strip("-")

def inline(s):
    s = re.sub(r"<!--.*?-->", "", s)
    parts = re.split(r"(`[^`]+`)", s)
    out = []
    for p in parts:
        if p.startswith("`") and p.endswith("`") and len(p) > 1:
            out.append(f"<code>{html.escape(p[1:-1])}</code>")
        else:
            p = html.escape(p, quote=False)
            p = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", p)
            p = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", p)
            out.append(p)
    return "".join(out)

def cells(row):
    row = row.strip().strip("|")
    return [c.strip() for c in row.split("|")]

lines = open(SRC, encoding="utf-8").read().split("\n")
body, toc, i, dg = [], [], 0, 0
while i < len(lines):
    ln = lines[i]
    if ln.startswith("```mermaid"):
        i += 1
        while not lines[i].startswith("```"):
            i += 1
        body.append(DIAGRAMS[dg]()); dg += 1; i += 1; continue
    m = re.match(r"^(#{1,4}) (.*)", ln)
    if m:
        lvl, txt = len(m.group(1)), m.group(2)
        sid = slug(txt)
        body.append(f'<h{lvl} id="{sid}">{inline(txt)}</h{lvl}>')
        if lvl in (2, 3): toc.append((lvl, sid, inline(txt)))
        i += 1; continue
    if ln.strip() == "---":
        body.append("<hr>"); i += 1; continue
    if ln.startswith("|"):
        rows = []
        while i < len(lines) and lines[i].startswith("|"):
            rows.append(lines[i]); i += 1
        head = cells(rows[0]); data = [cells(r) for r in rows[2:]]
        t = ['<div class="tw" tabindex="0" role="region" aria-label="table"><table><thead><tr>']
        t += [f"<th>{inline(c)}</th>" for c in head]
        t.append("</tr></thead><tbody>")
        for r in data: t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
        t.append("</tbody></table></div>")
        body.append("".join(t)); continue
    if ln.startswith("> "):
        q = []
        while i < len(lines) and lines[i].startswith(">"):
            q.append(lines[i][1:].strip()); i += 1
        body.append(f"<blockquote>{inline(' '.join(q))}</blockquote>"); continue
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
    if not ln.strip() or re.fullmatch(r"(<!--.*?-->)+", ln.strip()):
        i += 1; continue
    para = []
    while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||> |- |\d+\. |```|---)", lines[i]):
        para.append(lines[i]); i += 1
    body.append(f"<p>{inline(' '.join(para))}</p>")

assert dg == len(DIAGRAMS), (dg, len(DIAGRAMS))
h1_end = next(k for k, x in enumerate(body) if x.startswith("<h1"))
tochtml = '<nav class="toc" aria-label="Contents"><strong>Contents</strong><ul>' + "".join(
    f'<li class="l{l}"><a href="#{s}">{t}</a></li>' for l, s, t in toc) + "</ul></nav>"
# place the contents after the header block (before the first <hr>)
first_hr = body.index("<hr>")
body.insert(first_hr, tochtml)

CSS = """:root{--bg:#f6f7f9;--fg:#18212f;--muted:#5d6878;--line:#dfe3ea;--card:#fff;--accent:#1d4ed8;--code:#eef1f5;--acard:#eef3ff;--pcard:#f4f5f7;--neg:#c2410c;--pos:#2563eb;--tot:#8a94a3;--lane:#eef1f5}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#11161d;--fg:#e4e8ee;--muted:#9aa5b4;--line:#2a3340;--card:#171d26;--accent:#7aa2f7;--code:#1f2733;--acard:#1a2540;--pcard:#1b212b;--neg:#ea580c;--pos:#3b82f6;--tot:#6b7584;--lane:#1f2733}}
:root[data-theme=dark]{--bg:#11161d;--fg:#e4e8ee;--muted:#9aa5b4;--line:#2a3340;--card:#171d26;--accent:#7aa2f7;--code:#1f2733;--acard:#1a2540;--pcard:#1b212b;--neg:#ea580c;--pos:#3b82f6;--tot:#6b7584;--lane:#1f2733}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}
.wrap{max-width:1100px;margin:0 auto;padding:24px 16px 80px}h1{font-size:28px;line-height:1.25}h2{margin-top:44px;padding-top:12px;border-top:1px solid var(--line)}h3{margin-top:28px}
a{color:var(--accent)}code{background:var(--code);padding:1px 4px;border-radius:3px;font-size:.88em;overflow-wrap:anywhere}
.tw{overflow-x:auto;margin:12px 0;border:1px solid var(--line);border-radius:6px;background:var(--card)}table{border-collapse:collapse;width:100%;font-size:13.5px}th,td{text-align:left;vertical-align:top;padding:7px 9px;border-bottom:1px solid var(--line)}th{background:var(--code);font-weight:600}
blockquote{margin:16px 0;padding:10px 14px;border-left:4px solid var(--accent);background:var(--card)}hr{border:0;border-top:1px solid var(--line);margin:32px 0}
.toc{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:12px 16px;margin:20px 0}.toc ul{margin:6px 0;padding-left:18px}.toc .l3{margin-left:16px;font-size:.93em}
figure.dg{margin:16px 0;padding:12px;background:var(--card);border:1px solid var(--line);border-radius:6px;overflow-x:auto}figure.dg svg{display:block;width:100%;min-width:640px;height:auto}
figcaption{color:var(--muted);font-size:13px;margin-top:6px}
svg .bx{fill:var(--card);stroke:var(--muted);stroke-width:1.2}svg .bxa{fill:var(--acard);stroke:var(--accent);stroke-width:1.4}svg .bxp{fill:var(--pcard);stroke:var(--muted);stroke-width:1.2;stroke-dasharray:5 4}
svg .grp{fill:none;stroke:var(--line);stroke-width:1.5;stroke-dasharray:6 4}
svg .t{fill:var(--fg)}svg .lb{fill:var(--muted)}svg .ar{fill:none;stroke:var(--muted);stroke-width:1.6}svg .ard{fill:none;stroke:var(--muted);stroke-width:1.4;stroke-dasharray:5 4}
svg .arc{fill:none;stroke:var(--neg);stroke-width:3.2}svg .mk{fill:var(--muted)}svg .mkc{fill:var(--neg)}
svg .grid{stroke:var(--line);stroke-width:1}svg .conn{stroke:var(--muted);stroke-width:1;stroke-dasharray:3 3}
svg .wneg{fill:var(--neg)}svg .wpos{fill:var(--pos)}svg .wtot{fill:var(--tot)}
svg .lane{fill:var(--lane)}svg .bar0,svg .bar1,svg .bar2,svg .bar3{fill:var(--accent)}svg .bar1{opacity:.75}svg .bar2{opacity:.6}svg .bar3{opacity:.45}svg .ms{fill:var(--neg)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}"""

page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Product Transition Roadmap</title><style>' + CSS + '</style></head><body><main class="wrap">' + "".join(body) + "</main></body></html>")
open(OUT, "w", encoding="utf-8").write(page)
print("ok", len(page), "diagrams", dg)
