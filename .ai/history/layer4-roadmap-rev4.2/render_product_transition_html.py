# Superseded with product-transition-and-roadmap rev 4.2 (20 Nov 2026): it renders only that revision, whose nine figures it draws. Kept as history.
"""Render product-transition-and-roadmap.md to a self-contained HTML page with inline SVG diagrams (offline).

Usage: python3 render_product_transition_html.py product-transition-and-roadmap.md product-transition-and-roadmap.html
The diagrams are drawn here, in the order of the mermaid blocks in the .md (which stay as the plain-text source); a line
`<!--diagram:effort-->` in the .md places the effort chart. Each diagram has a wide layout and a stacked narrow layout
for phone widths (shown below 1000 px), so labels stay legible instead of shrinking. Demo figures in Figure 2 are read
from derived-values.json (the evaluator's output, which check_manifest.py checks against the independent model)."""
import html, json, pathlib, re, sys, zlib

SRC, OUT = sys.argv[1], sys.argv[2]
DV = json.loads((pathlib.Path(SRC).resolve().parent / "derived-values.json").read_text(encoding="utf-8"))

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

def svg(w, h, body, title, desc, narrow=None):
    """A figure with the wide layout and, when given, a narrow (nw, nh, body) layout for phone widths."""
    k = zlib.crc32(title.encode())
    def one(cls, w_, h_, b_, sfx):
        # marker ids are unique per svg: a hidden layout's markers would not render for the visible one
        mid = f"{k}{sfx}"
        defs = DEFS.replace('id="m"', f'id="m{mid}"').replace('id="mc"', f'id="mc{mid}"')
        b_ = b_.replace("url(#m)", f"url(#m{mid})").replace("url(#mc)", f"url(#mc{mid})")
        return (f'<svg class="{cls}" viewBox="0 0 {w_} {h_}" role="img" aria-labelledby="t{k}{sfx} d{k}{sfx}">'
                f'<title id="t{k}{sfx}">{esc(title)}</title><desc id="d{k}{sfx}">{esc(desc)}</desc>{defs}{b_}</svg>')
    parts = one("wide", w, h, body, "w")
    if narrow:
        parts += one("narrow", *narrow, "n")
    return f'<figure class="dg">{parts}<figcaption>{esc(title)}</figcaption></figure>'

# ---------------------------------------------------------------- narrow (stacked) layout, 400 units wide
NW, NFS = 400, 14

def vstack(entries):
    """Entries: ("h", text) header; ("n", text) muted note; ("x",) no arrow into the next row; ("a", label, cls) style of the next arrow;
    ("r", [(lines, cls), ...]) a row of one or two boxes, joined by arrows to the previous box row."""
    b, y, prev, nxt = [], 8, None, ("", "ar")
    for e in entries:
        if e[0] == "h":
            y += 8; b.append(label(10, y + 14, e[1], fs=15, cls="t", weight="600")); y += 26; prev = None
        elif e[0] == "n":
            for ln in e[1].split("\n"):
                b.append(label(10, y + 14, ln, fs=13)); y += 19
            y += 6; prev = None
        elif e[0] == "x":
            prev = None; y += 10
        elif e[0] == "a":
            nxt = (e[1], e[2])
        else:
            row = e[1]; n = len(row)
            bw = (NW - 20 - (n - 1) * 12) / n
            h = max(len(t) for t, _ in row) * (NFS + 4) + 16
            gap = 30 if prev is not None else 0
            y += gap
            xs = [10 + i * (bw + 12) for i in range(n)]
            if prev is not None:
                py, pxs, pbw = prev
                lbl, cls = nxt
                mk = "mc" if cls == "arc" else "m"
                for i, x in enumerate(xs):
                    src = pxs[min(i, len(pxs) - 1)] + pbw / 2 if len(pxs) > 1 else pxs[0] + pbw / 2
                    b.append(arrow([(src, py + 2), (x + bw / 2, y - 3)], cls=cls, marker=mk))
                if lbl:
                    b.append(label(NW / 2 + 12, y - gap / 2 + 4, lbl, fs=12.5))
            for x, (t, cls) in zip(xs, row):
                b.append(box(x, y, bw, h, t, cls=cls, fs=NFS))
            y += h; prev = (y, xs, bw); nxt = ("", "ar")
    return NW, y + 12, "".join(b)

# ---------------------------------------------------------------- diagram 1: today vs Layer 4, today's chain re-grounded (rev 4)
def d1():
    b = []
    bw, xs = 210, [10, 242, 474, 706, 938]
    cx = [x + bw / 2 for x in xs]
    b.append(label(10, 24, "Today: signal first", fs=14, weight="600"))
    today = [["Telemetry and", "operational records"], ["Analyses", "dispatch, fuel balance,", "excursions, faults"],
             ["Findings", "what looks wrong"], ["Gross exposure", "up to this much"], ["One setting trial,", "recorded work actions", "(verified: mini-grid)"]]
    for x, t in zip(xs, today): b.append(box(x, 38, bw, 70, t, fs=12))
    for i in range(4): b.append(arrow([(xs[i] + bw, 73), (xs[i + 1] - 2, 73)]))
    # how today's constructs take their places (Figure 8 and §3.7 give the full mapping)
    b.append(arrow([(cx[1], 108), (cx[1], 232)], cls="ard"))
    b.append(label(cx[1] - 8, 160, "become observers", anchor="end", fs=11.5)); b.append(label(cx[1] - 8, 175, "of factors", anchor="end", fs=11.5))
    b.append(arrow([(cx[2] - 30, 108), (cx[1] + 70, 232)], cls="ard"))
    b.append(label(cx[2] - 22, 160, "become conditions", fs=11.5)); b.append(label(cx[2] - 22, 175, "on factor keys", fs=11.5))
    b.append(label(cx[3], 130, "becomes an at-stake bound on", anchor="middle", fs=11.5))
    b.append(label(cx[3], 145, "its factor, never a value", anchor="middle", fs=11.5))
    b.append(arrow([(cx[4], 108), (cx[4], 232)], cls="ard"))
    b.append(label(cx[4] - 8, 172, "carry the chosen", anchor="end", fs=11.5)); b.append(label(cx[4] - 8, 187, "option as Actions", anchor="end", fs=11.5))
    b.append(label(cx[4] - 8, 202, "operational verdict kept", anchor="end", fs=11.5))
    # Layer 4, grounded on one registry
    b.append('<rect class="grp" x="2" y="200" width="1154" height="290" rx="10"/>')
    b.append(label(16, 222, "Layer 4: structure first, today's chain re-grounded on it", fs=14, weight="600"))
    l4 = [["Define", "each outcome as factors", "down to source records"],
          ["Observe", "factors from records; outcome", "computed upward; Findings:", "conditions on factor keys"],
          ["Evaluate", "decisions on factor keys:", "options, always with no action,", "valued against no action"],
          ["Choose", "one plan within budget, crews,", "rules, rights; the chosen", "option rides an Action"],
          ["Prove", "the same factors after;", "three verdicts"]]
    for x, t in zip(xs, l4): b.append(box(x, 234, bw, 84, t, cls="bxa", fs=12))
    for i in range(4): b.append(arrow([(xs[i] + bw, 276), (xs[i + 1] - 2, 276)]))
    b.append(arrow([(cx[4], 318), (cx[4], 336), (cx[1], 336), (cx[1], 320)]))
    b.append(label((cx[1] + cx[4]) / 2, 350, "the loop repeats each period", anchor="middle", fs=11.5))
    b.append(box(10, 376, 790, 96, ["One structure registry", "leaf factors → factors → outcomes, read upward · factor ID · period ID · unit · plan · bounds",
                                     "every leaf: evidence class and provenance; a node takes its weakest part",
                                     "Findings, decisions, options, Actions and verdicts all key to its factors"], cls="bxa", fs=12))
    b.append(arrow([(cx[0], 374), (cx[0], 320)], cls="ard"))
    b.append(label(cx[0] + 8, 354, "declares", fs=11.5))
    b.append(box(830, 376, 318, 96, ["Sources, one canonical contract", "telemetry and operational records;", "emulated exports as placeholders,",
                                      "then the operator's own exports;", "one contract test runs on both"], fs=12))
    b.append(arrow([(830, 424), (802, 424)]))
    b.append(label(10, 512, "No construct carries an outcome value of its own: Findings attach at a factor and outcomes are read upward through the factors (§3.7, §3.8).", fs=11.5))
    narrow = vstack([("h", "Today: signal first"),
                     ("r", [(["Telemetry and operational records"], "bx")]), ("r", [(["Analyses", "dispatch, fuel balance, excursions"], "bx")]),
                     ("r", [(["Findings", "what looks wrong"], "bx")]), ("r", [(["Gross exposure", "up to this much"], "bx")]),
                     ("r", [(["One setting trial, recorded work", "(verified: mini-grid only)"], "bx")]),
                     ("n", "Re-grounded: analyses become observers of\nfactors; Findings become conditions on factor\nkeys; gross exposure an at-stake bound, never\na value; trials and work carry the chosen\noption as Actions; the operational verdict stays."),
                     ("h", "Layer 4, on one registry"),
                     ("r", [(["Sources, one canonical contract", "telemetry and operational records;", "emulated exports as placeholders, then", "the operator's own; one contract test on both"], "bx")]),
                     ("r", [(["One structure registry", "leaf factors → factors → outcomes, read", "upward; every leaf: class and provenance;", "everything below keys to its factors"], "bxa")]),
                     ("a", "declares", "ar"),
                     ("r", [(["Define", "each outcome as factors, to records"], "bxa")]),
                     ("r", [(["Observe", "factors from records; outcome upward;", "Findings: conditions on factor keys"], "bxa")]),
                     ("r", [(["Evaluate", "decisions on factor keys: options,", "always with no action"], "bxa")]),
                     ("r", [(["Choose", "one plan within budget, crews, rights;", "the chosen option rides an Action"], "bxa")]),
                     ("r", [(["Prove", "the same factors after; three verdicts"], "bxa")]),
                     ("n", "The loop repeats each period: Prove feeds Observe.")])
    return svg(1160, 524, "".join(b), "Figure 1. Today's product and Layer 4: today's chain re-grounded on one registry",
               "Today: records, analyses, findings, gross exposure, one setting trial and recorded work actions. In Layer 4 analyses become observers of factors, "
               "Findings become conditions on factor keys, gross exposure an at-stake bound, and trials and work carry the chosen option as Actions. "
               "Define, observe, evaluate, choose and prove run in a loop over one structure registry, fed by telemetry and emulated exports, then the operator's own, through one canonical contract with one contract test.", narrow)


# ---------------------------------------------------------------- diagram 2: Kobo waterfall, from derived-values.json
def kobo_steps():
    P = DV["sites"]["lakeside-power/Kobo"]["plan"]["nodes"]; A = DV["sites"]["lakeside-power/Kobo"]["actual"]["nodes"]
    price, tariff = A["diesel_price"], A["tariff"]
    d = lambda k: A[k] - P[k]   # noqa: E731
    steps = [("Plan|contribution", P["contribution"], "tot"),
             (f"Candidate running|{d('candidate_l'):,.0f} L", -d("candidate_l") * price, "neg"),
             (f"Necessary above|plan, {d('necessary_l'):,.0f} L", -d("necessary_l") * price, "neg"),
             (f"Unexplained fuel|{d('unexplained_l'):,.0f} L", -d("unexplained_l") * price, "neg"),
             (f"More kWh billed|{d('billed_kwh'):,.0f} kWh", d("billed_kwh") * tariff, "pos"),
             ("Actual|contribution", A["contribution"], "tot")]
    # the bridge must close: other factors (O&M, staff, wear, collection cost) are on plan in the demo month
    assert abs(steps[0][1] + sum(v for _, v, k in steps[1:-1]) - steps[-1][1]) < 0.005, "Kobo bridge does not close"
    return steps, price, tariff

def money(v, kind):
    return f"{v:,.0f}" if kind == "tot" else f"{v:+,.2f}".replace("-", "−")

def d2():
    steps, price, tariff = kobo_steps()
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
        val = money(v, kind)
        b.append(f'<rect class="w{kind}" x="{x}" y="{y1:.1f}" width="{bw}" height="{max(y2-y1,2):.1f}" rx="4"><title>{esc(name.replace("|", " "))}: {esc(val)}</title></rect>')
        b.append(label(x + bw/2, y1 - 7, val, anchor="middle", fs=12.5, cls="t", weight="600"))
        l1, l2 = name.split("|")
        b.append(label(x + bw/2, base + 20, l1, anchor="middle", fs=11.5))
        if l2: b.append(label(x + bw/2, base + 35, l2, anchor="middle", fs=11.5))
        if i < len(steps) - 1:
            yr = base - run * scale
            b.append(f'<line class="conn" x1="{x+bw}" x2="{x+bw+gap}" y1="{yr:.1f}" y2="{yr:.1f}"/>')
    note = f"Demo values (derived-values.json). Orange lowers contribution, blue raises it; grey bars are totals. Diesel at {price:.2f} per litre, tariff {tariff:.2f} per kWh."
    b.append(label(x0, H - 8, note, fs=11))
    # narrow: horizontal waterfall, one row per step
    n, L, R, rh = [], 150, 318, 46
    sx = (R - L) / 1500
    for v in (0, 500, 1000, 1500):
        x = L + v * sx
        n.append(f'<line class="grid" x1="{x:.1f}" x2="{x:.1f}" y1="14" y2="{20 + len(steps)*rh}"/>')
        n.append(label(x, 12, f"{v:,}", anchor="middle", fs=12))
    run = 0
    for i, (name, v, kind) in enumerate(steps):
        y = 22 + i * rh
        if kind == "tot":
            lo, hi = 0, v; run = v
        else:
            lo, hi = sorted((run, run + v)); run += v
        l1, l2 = name.split("|")
        n.append(label(10, y + 16, l1, fs=13, cls="t")); n.append(label(10, y + 33, l2, fs=13))
        n.append(f'<rect class="w{kind}" x="{L + lo*sx:.1f}" y="{y + 8}" width="{max((hi-lo)*sx, 2):.1f}" height="24" rx="4"><title>{esc(name.replace("|", " "))}: {esc(money(v, kind))}</title></rect>')
        n.append(label(NW - 6, y + 25, money(v, kind), anchor="end", fs=13, cls="t", weight="600"))
    nh = 22 + len(steps) * rh
    n.append(label(10, nh + 16, "Demo values. Orange lowers contribution, blue", fs=12))
    n.append(label(10, nh + 33, f"raises it; grey are totals. Diesel {price:.2f}/L, tariff {tariff:.2f}/kWh.", fs=12))
    P, A = steps[0][1], steps[-1][1]
    title = f"Figure 2. Kobo, October: contribution {P:,.0f} planned, {A:,.0f} actual (demo values)"
    desc = "Waterfall: " + "; ".join(f"{nm.replace('|', ' ')} {money(v, k)}" for nm, v, k in steps) + "."
    return svg(W, H, "".join(b), title, desc, (NW, nh + 44, "".join(n)))

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
    narrow = vstack([("h", "What operators already have"),
                     ("r", [(["Monitoring / EMS / CPMS", "what the assets are doing"], "bx")]),
                     ("r", [(["Billing, vending, ERP", "what was charged and paid"], "bx")]),
                     ("r", [(["Contracts and spreadsheets", "warranties, SLAs, plans"], "bx")]),
                     ("n", "All three feed the outcome structure."),
                     ("h", "What AssetEcon adds: the join"),
                     ("r", [(["Outcome structure", "figures from factors, with evidence"], "bxa")]),
                     ("r", [(["Options", "vs no action, with rules and rights"], "bxa")]),
                     ("r", [(["One plan", "within budget and crews"], "bxa")]), ("r", [(["Proof", "in three verdicts"], "bxa")]),
                     ("n", "Proof feeds the next period's observation.")])
    return svg(1100, 300, "".join(b), "Figure 3. Where the differentiation sits: the join across systems the operator already has",
               "Monitoring, billing and contract systems feed an outcome structure, which leads to options, one plan, and proof, in a loop.", narrow)

# ---------------------------------------------------------------- diagram 4: engagement path
def d4():
    """The owner's engagement path (D1 as revised on 18 Nov), with its gates."""
    b = []
    y, h = 40, 86                       # row 1: demo, the call, the deep-dive and its gate; row 2: from the pack to SaaS
    cy = y + h / 2
    y2 = 290; cy2 = y2 + h / 2
    b.append(box(10, y, 150, h, ["Client demo", "loop on the mock-up;", "live: what runs today"], fs=12))
    b.append(diamond(270, cy, 170, 110, ["Initial call:", "aligned on privacy,", "processes and", "integrations?"]))
    b.append(box(380, y, 190, h, ["Deep-dive with", "process owners", "file exports through the", "canonical contract"], cls="bxa", fs=12))
    b.append(diamond(680, cy, 170, 110, ["Their plan", "against actual", "reconciled and", "compelling?"]))
    b.append(box(790, y, 160, h, ["Stop or rethink", "record why"], fs=12))
    b.append(box(180, 170, 180, 66, ["Data assessment", "cold and EV prospects", "until their vertical", "is built"], fs=12))
    b.append(box(10, y2, 190, h, ["Integration pack", "and pilot timeline", "pilot fee (C2, open)"], cls="bxa", fs=12))
    b.append(box(225, y2, 180, h, ["Pilot and", "monitoring", "options vs no action;", "first change proved"], cls="bxa", fs=12))
    b.append(diamond(515, cy2, 170, 110, ["Verdicts and", "the buyer's own", "judgement?"]))
    b.append(box(625, y2, 150, h, ["SaaS", "subscription", "and reference"], cls="bxa", fs=12))
    for x1, x2, yy in ((160, 183, cy), (355, 378, cy), (570, 593, cy), (765, 788, cy), (200, 223, cy2), (405, 428, cy2), (600, 623, cy2)):
        b.append(arrow([(x1, yy), (x2, yy)]))
    for x, yy, t in ((366, cy, "yes"), (776, cy, "no"), (611, cy2, "yes")): b.append(label(x, yy - 8, t, anchor="middle", fs=11))
    b.append(arrow([(270, cy + 55), (270, 168)])); b.append(label(277, 158, "not yet", fs=11))
    b.append(arrow([(680, cy + 55), (680, 256), (105, 256), (105, y2 - 2)])); b.append(label(687, 160, "yes", fs=11))
    b.append(arrow([(515, cy2 + 55), (515, 405), (870, 405), (870, y + h + 2)])); b.append(label(522, 400, "no", fs=11))
    b.append(label(10, 436, "The product computes the deep-dive's figures from the operator's own exports; nothing is transcribed by hand.", fs=11.5))
    b.append(label(10, 452, "Price is disclosed after the client conversation.", fs=11.5))
    narrow = vstack([("r", [(["Client demo", "loop on the mock-up, design values", "labelled; live: what runs today"], "bx")]),
                     ("r", [(["Initial call: aligned on data privacy,", "processes, integrations, who signs?", "not yet: data assessment (cold, EV)"], "bxp")]),
                     ("a", "yes", "ar"), ("r", [(["Deep-dive with process owners", "file exports through the canonical", "contract; first decision to test"], "bxa")]),
                     ("r", [(["Their plan against actual in the", "product, reconciled and compelling?", "no: stop or rethink, record why"], "bxp")]),
                     ("a", "yes", "ar"), ("r", [(["Integration pack and pilot timeline", "sources in order, files first;", "pilot fee (C2, open)"], "bxa")]),
                     ("r", [(["Pilot and monitoring", "options vs no action; one change proved"], "bxa")]),
                     ("r", [(["Verdicts and the buyer's judgement?", "no: stop or rethink"], "bxp")]),
                     ("a", "yes", "ar"), ("r", [(["SaaS subscription", "and reference case"], "bxa")])])
    return svg(960, 462, "".join(b), "Figure 4. The engagement path, with its gates (D1, as revised by the owner on 18 Nov)",
               "Demo of the loop on the mock-up, then the live product as what runs today; an initial call checks alignment on data privacy, processes, integrations and who signs; aligned prospects get a deep-dive with their process owners, in which their file exports go through the canonical contract, others a data assessment. If their plan against actual in the product is reconciled and compelling, an integration pack and pilot timeline follow, with a pilot fee whose form is open (C2); then the pilot and monitoring; if its verdicts hold, a SaaS subscription. Failed gates lead to stop or rethink.", narrow)

# ---------------------------------------------------------------- diagram 5: dependencies (rights and plan in parallel)
def d5():
    b = []
    W = 125; xs = [20 + i*147 for i in range(7)]
    yt, yc, yb, hc = 30, 150, 290, 74
    mid = [(0, ["2 Commercial", "records and", "file intake"]), (1, ["3 Structure and", "factor bridge"]), (2, ["4 Decisions:", "options, rules,", "no action"]),
           (3, ["5 Plan and the", "restructured", "Portfolio"]), (5, ["8a Cold", "(or EV first)"]), (6, ["8b EV", "(or cold)"])]
    for c, t in mid: b.append(box(xs[c], yc, W, hc, t, cls="bxa", fs=11.5))
    for i in range(3):
        b.append(arrow([(xs[i]+W, yc+hc/2), (xs[i+1]-2, yc+hc/2)], cls="arc", marker="mc"))
    b.append(arrow([(xs[3]+W, yc+hc/2), (xs[5]-2, yc+hc/2)]))
    b.append(arrow([(xs[5]+W, yc+hc/2), (xs[6]-2, yc+hc/2)]))
    for c, t in ((0, ["Pilot lane", "agreements,", "profiles,", "deep-dives"]), (1, ["Lane B", "build speed,", "re-benchmark"]),
                 (2, ["Calibration lane", "replays on", "demo data"]), (3, ["1 Honest screens", "(UI only)"])):
        b.append(box(xs[c], yt, W, 66, t, cls="bxp", fs=12))
    b.append(arrow([(xs[0]+W/2, yt+66), (xs[0]+W/2, yc-2)], cls="ard"))
    b.append(arrow([(xs[1]+W/2, yt+66), (xs[2]+20, yc-2)], cls="ard"))
    b.append(arrow([(xs[2]+W/2, yt+66), (xs[2]+W/2, yc-2)], cls="ard"))
    b.append(arrow([(xs[3]+W/2, yt+66), (xs[3]+W/2, yc-2)]))
    b.append(box(xs[2], yb, W, 66, ["7 Proof:", "three verdicts", "(lane 2, first)"], cls="bxa", fs=12))
    b.append(box(xs[3], yb, W, 66, ["6 Rights in", "repair decisions", "(lane 2, after 7)"], cls="bxa", fs=12))
    b.append(box(xs[5], yb, W, 66, ["9 Pilot hardening", "field calibration", "evidence pack"], cls="bxa", fs=12))
    b.append(arrow([(xs[2]+W/2, yc+hc), (xs[2]+W/2, yb-2)]))
    b.append(arrow([(xs[2]+W, yb+33), (xs[3]-2, yb+33)]))
    b.append(arrow([(xs[3]+W/2, yb), (xs[3]+W/2, yc+hc+2)], cls="ard"))
    b.append(label(xs[3]+W/2+6, yb-22, "full plan gate", fs=11))
    b.append(arrow([(xs[3]+W, yc+hc-14), (xs[4]+60, yc+hc-14), (xs[4]+60, yb+40), (xs[5]-2, yb+40)]))
    b.append(arrow([(xs[2]+W/2, yb+66), (xs[2]+W/2, yb+86), (xs[5]+W/2, yb+86), (xs[5]+W/2, yb+68)]))
    b.append(arrow([(xs[0]+20, yt), (xs[0]+20, 12), (1150, 12), (1150, yb+33), (xs[5]+W+2, yb+33)], cls="ard"))
    b.append(label(20, 410, "Thick orange arrows: the critical path (records → structure → decisions → plan). Proof, then rights, run in lane 2 after decisions; dashed: parallel lanes and the plan gate.", fs=11.5))
    narrow = vstack([("h", "Parallel from the start"),
                     ("r", [(["Pilot lane", "agreements, profiles"], "bxp"), (["Lane B", "build speed"], "bxp")]), ("x",),
                     ("r", [(["Calibration lane", "replays, demo data"], "bxp"), (["1 Honest screens", "UI only"], "bxp")]),
                     ("h", "Critical path (lane 1)"),
                     ("r", [(["2 Commercial records", "and file intake"], "bxa")]),
                     ("a", "", "arc"), ("r", [(["3 Structure and factor bridge"], "bxa")]),
                     ("a", "", "arc"), ("r", [(["4 Decisions", "options, rules, no action"], "bxa")]),
                     ("a", "", "arc"), ("r", [(["5 Plan, Portfolio", "lane 1"], "bxa"), (["7 Proof, then 6 Rights", "lane 2"], "bxa")]),
                     ("n", "The full plan gate waits for rights (6)."),
                     ("r", [(["8a Cold, then 8b EV", "(order set by prospect)"], "bxa"), (["9 Pilot hardening", "field calibration"], "bxa")])])
    return svg(1170, 420, "".join(b), "Figure 5. Transition steps, dependencies and the critical path",
               "Critical path: commercial records, structure and factor bridge, decisions, plan. Proof and then rights run in the second lane after decisions; the full plan gate waits for rights. Parallel lanes: pilot lane, Lane B, calibration lane, honest screens. Verticals follow plan and proof; pilot hardening follows plan and proof.", narrow)

# ---------------------------------------------------------------- diagram 6: emulators as placeholders, one adapter shape, one contract test
def d6():
    b = []
    b.append(box(10, 20, 262, 96, ["Emulator: a placeholder source", "native-shape files from the manifest;", "nothing a real source lacks;", "source-emulated, shown Emulated"], fs=12))
    b.append(box(10, 136, 262, 96, ["Real source", "bench: a device or sample export;", "pilot: the operator's export;", "bench-tested · field-integrated ·", "observed-financial"], fs=12))
    b.append('<rect class="grp" x="312" y="34" width="590" height="150" rx="10"/>')
    b.append(label(326, 56, "Adapter = transport + parser + profile, same authenticated intake", fs=13, weight="600"))
    b.append(box(326, 72, 176, 96, ["Transport", "emulator's file writer →", "upload or scheduled drop", "(API later)"], cls="bxa", fs=12))
    b.append(box(520, 72, 176, 96, ["Parser", "bytes to typed rows", "pure, versioned;", "the same for both"], cls="bxa", fs=12))
    b.append(box(714, 72, 176, 96, ["Profile", "columns, units, timezone,", "personal data;", "illustrative → pinned"], cls="bxa", fs=12))
    b.append(arrow([(502, 120), (518, 120)])); b.append(arrow([(696, 120), (712, 120)]))
    b.append(arrow([(272, 68), (292, 68), (292, 110), (310, 110)]))
    b.append(arrow([(272, 184), (292, 184), (292, 130), (310, 130)]))
    b.append(box(940, 34, 230, 100, ["Canonical records", "CHARGE · RECEIPT · PLAN_LINE ·", "EXPENSE …; telemetry: ledger;", "provenance on every revision"], fs=12))
    b.append(arrow([(902, 84), (938, 84)]))
    b.append(box(940, 166, 230, 100, ["Downstream, unchanged", "leaf factors · structure ·", "observers · Evaluate · screens;", "branches only on labels,", "coverage and the benefit gate"], fs=12))
    b.append(arrow([(1055, 134), (1055, 164)]))
    b.append(box(312, 214, 590, 84, ["Contract test, one suite per source type, run on both", "the emulator's output and the operator's pinned sample: kinds, fields, units,",
                                      "four clocks, idempotency key, disorder, refusals; same content gives", "the same canonical records and the same factor values"], cls="bxp", fs=12))
    b.append(arrow([(312, 256), (141, 256), (141, 234)], cls="ard"))
    b.append(label(160, 274, "runs on both sources", fs=11.5))
    b.append(arrow([(902, 256), (922, 256), (922, 110), (938, 110)], cls="ard"))
    b.append(label(10, 326, "From emulator to real source only transport and profile change. A real adapter replaces the emulator once it passes the contract test; the emulator stays as the test's fixture.", fs=11.5))
    narrow = vstack([("r", [(["Emulator", "placeholder;", "shown Emulated"], "bx"), (["Real source", "bench, then the", "operator's export"], "bx")]),
                     ("r", [(["Adapter: transport", "emulator's writer → upload or drop"], "bxa")]),
                     ("r", [(["Parser", "bytes to typed rows; the same for both"], "bxa")]),
                     ("r", [(["Profile", "columns, units, timezone, personal data;", "illustrative → pinned"], "bxa")]),
                     ("r", [(["Canonical records", "provenance on every revision"], "bx")]),
                     ("r", [(["Downstream, unchanged", "structure, observers, Evaluate, screens"], "bx")]),
                     ("n", "Contract test: one suite per source type, run\non the emulator's output and on the operator's\npinned sample; same content gives the same\ncanonical records and factor values. A real\nadapter replaces the emulator once it passes;\nonly transport and profile change.")])
    return svg(1180, 338, "".join(b), "Figure 6. File import first: emulators are placeholders, replaced by real adapters that pass the same contract test",
               "An emulator and a real source of the same type enter the same adapter (transport, parser, profile) and produce the same canonical records; everything downstream is unchanged. "
               "One contract test per source type runs on the emulator's output and on the operator's pinned sample. From emulator to real source only transport and profile change.", narrow)


# ---------------------------------------------------------------- diagram 7: visible first, screen by screen (from the §3.6 tables)
VINC = [("V1", ["findings on their", "factors, honest screens"], "lane 2", "W1 (observer rows)", "chw"),
        ("V2", ["factor views on", "observed factors"], "lane 2", "W1", "chw"),
        ("V3", ["the first live", "decision view"], "lane 2", "W1; 4b, spike K", "chw"),
        ("V4", ["contribution against", "plan, factor by factor"], "lane 1", "step 2 records", "chr"),
        ("V5", ["the whole loop"], "lanes 1, 2", "step 2 records", "chr")]
VSCREENS = [("Portfolio · Overview", "Findings on factors, thread counts, placement (triage)", {1: "attention on factors", 4: "outcome figures", 5: "first moves"}),
            ("Portfolio · Outcomes by site", "outcome catalogue, board driver rows, objectives, depth reads", {2: "operational factors", 4: "money"}),
            ("Portfolio · Demand and capacity", "headroom study, PRODUCTIVE_LOAD what-if", {1: "relabelled", 5: "valued demand"}),
            ("Portfolio · Act first", "Findings, decisions, placement as triage", {3: "decisions", 5: "plan"}),
            ("Portfolio · What changed", "Actions, domain actions, work cases, verdict", {3: "Actions, operational\nverdict", 5: "three verdicts,\nrights"}),
            ("Portfolio · Scope & coverage", "source health, evidence ledger, provenance labels", {2: "sources per leaf"}),
            ("Site · Overview", "the outcome board: drivers, issues, can be done, in hand", {1: "issues on factors", 2: "drivers as\nfactor rows", 3: "decisions from\n'can be done'"}),
            ("Site · Financials", "price assumptions, consequence history", {2: "prices, at stake", 4: "recorded money"}),
            ("Site · Performance and Findings", "dispatch-3.2, fuel balance, depth reads, Findings", {1: "observers per factor"}),
            ("Decision view", "reserve recommendation, what-ifs, tariff contexts", {3: "cost-side options", 5: "all decisions"}),
            ("Actions and Work", "today's carriers: trial, domain actions, work cases", {3: "chosen option's\ncarrier"})]

def d7v():
    b = []
    L, cw = 384, 156
    cxs = [L + i * cw + cw / 2 for i in range(5)]
    b.append(label(10, 30, "Screen", fs=13, cls="t", weight="600"))
    b.append(label(10, 47, "carried by (today's construct)", fs=11.5))
    for (vid, title, lane, wait, wcls), x in zip(VINC, cxs):
        b.append(label(x, 22, vid, anchor="middle", fs=15, cls="t", weight="700"))
        for k, t in enumerate(title): b.append(label(x, 40 + k * 15, t, anchor="middle", fs=11.5, cls="t"))
        b.append(label(x, 84, lane, anchor="middle", fs=11.5))
        b.append(f'<rect class="{wcls}" x="{x - cw/2 + 6}" y="94" width="{cw - 12}" height="24" rx="12"/>')
        b.append(label(x, 110, wait, anchor="middle", fs=11.5, cls="t"))
    b.append(label(L - 10, 110, "waits for", anchor="end", fs=11.5))
    top, rh = 130, 46
    for i in range(6):
        x = L + i * cw
        b.append(f'<line class="grid" x1="{x}" x2="{x}" y1="{top - 4}" y2="{top + len(VSCREENS) * rh}"/>')
    for r, (name, carried, cells_) in enumerate(VSCREENS):
        y = top + r * rh
        if r % 2 == 0: b.append(f'<rect class="lane" x="0" y="{y}" width="{L + 5 * cw + 6}" height="{rh}"/>')
        b.append(label(10, y + 19, name, fs=13, cls="t", weight="600"))
        b.append(label(10, y + 36, carried, fs=11.5))
        for v, t in cells_.items():
            x = L + (v - 1) * cw
            b.append(f'<rect class="bxa" x="{x + 6}" y="{y + 5}" width="{cw - 12}" height="{rh - 10}" rx="8"/>')
            ls = t.split("\n")   # every line of a cell in the same weight (box() would bold only the first)
            for k, ln in enumerate(ls):
                b.append(label(x + cw / 2, y + rh / 2 + 4 + (k - (len(ls) - 1) / 2) * 14, ln, anchor="middle", fs=11.5, cls="t", weight="600"))
    y = top + len(VSCREENS) * rh + 22
    b.append(f'<rect class="chw" x="10" y="{y - 13}" width="30" height="16" rx="8"/>')
    b.append(label(48, y, "W1: the owner's approval of the structure; lane 2's work starts after it (V1's findings on factors rest on the observer rows, 3a′).", fs=11.5, cls="t"))
    b.append(f'<rect class="chr" x="10" y="{y + 9}" width="30" height="16" rx="8"/>')
    b.append(label(48, y + 22, "Step 2 records: the commercial record store and its emulators. V4 on emulated records reads “demonstrated on emulated records”; on a deep-dive's exports it is reconciled.", fs=11.5, cls="t"))
    H = y + 40
    # narrow: one section per increment, the screens it makes useful and the construct that carries each
    n, ny = [], 10
    for v, (vid, title, lane, wait, wcls) in enumerate(VINC, start=1):
        ny += 8
        for k, t in enumerate(title):   # one title line per row, so no header leaves the 400-unit viewBox
            n.append(label(10, ny + 16, f"{vid} · {t}" if k == 0 else f"       {t}", fs=15, cls="t", weight="600")); ny += 20
        ny += 6
        n.append(f'<rect class="{wcls}" x="10" y="{ny}" width="380" height="24" rx="12"/>')
        n.append(label(22, ny + 17, f"{lane} · waits for {wait}", fs=13, cls="t")); ny += 34
        for name, carried, cells_ in VSCREENS:
            if v not in cells_: continue
            n.append(label(14, ny + 14, f"{name}: {cells_[v].replace(chr(10), ' ')}", fs=13, cls="t")); ny += 18
            parts = [carried] if len(carried) <= 50 else [carried[:50].rsplit(" ", 1)[0], carried[len(carried[:50].rsplit(" ", 1)[0]) + 1:]]
            for t in parts:   # wrapped, never truncated
                n.append(label(26, ny + 14, t, fs=13)); ny += 17
            ny += 5
    ny += 6
    for t in ("W1: the owner's structure approval. Step 2:", "commercial records (store and emulators).", "V4 on emulated records is labelled", "“demonstrated on emulated records”."):
        n.append(label(10, ny + 14, t, fs=13)); ny += 18
    return svg(L + 5 * cw + 10, H, "".join(b), "Figure 7. Visible first: when each client screen becomes economically useful, what carries it, and what it waits for",
               "Five increments. V1 findings on their factors and honest screens, lane 2, waits for W1 for the observer rows. V2 factor views on observed factors, lane 2, waits for W1. "
               "V3 the first live decision view, lane 2, waits for W1, the bounds (4b) and spike K. V4 contribution against plan, lane 1, waits for step 2's commercial records. "
               "V5 the whole loop, both lanes, waits for step 2's records. " +
               " ".join(f"{nm}: " + ", ".join(f"V{v} {t.replace(chr(10), ' ')}" for v, t in c.items()) + f" (carried by {cr})." for nm, cr, c in VSCREENS),
               (400, ny + 8, "".join(n)))

# ---------------------------------------------------------------- diagram 7: roadmap swimlanes
def _lanes():
    """The swimlanes, parsed from the mermaid gantt block of the .md, so the figure cannot drift from its source."""
    src = open(SRC, encoding="utf-8").read()
    blk = src[src.index("```mermaid\ngantt"):]; blk = blk[:blk.index("\n```", 4)]
    lanes = []
    for ln in blk.split("\n"):
        m = re.match(r"\s*section (.+)", ln)
        if m: lanes.append((m.group(1).strip(), [])); continue
        m = re.match(r"\s*(.+?)\s*:(?:milestone, )?\w+, ([\d.]+), ([\d.]+)\s*$", ln)
        if m and lanes: lanes[-1][1].append((m.group(1).strip(), float(m.group(2)), float(m.group(3))))
    return lanes
LANES = _lanes()

def gantt(L, R, top, rh, lbl_fs, stacked):
    mw = (R - L) / 10
    b = []
    rows = sum(len(x[1]) * (2 if stacked else 1) + 1 for x in LANES)
    for m in range(11):
        x = L + m * mw
        b.append(f'<line class="grid" x1="{x:.1f}" x2="{x:.1f}" y1="{top-6}" y2="{top + rows*rh}"/>')
        b.append(label(x, top - 12, f"M{m}", anchor="middle", fs=12 if stacked else 11))
    y = top
    for li, (lane, items) in enumerate(LANES):
        b.append(f'<rect class="lane" x="0" y="{y}" width="{R+10}" height="{rh}"/>')
        b.append(label(8, y + 17, lane, fs=13, weight="600", cls="t"))
        y += rh
        for name, s, e in items:
            if stacked:
                b.append(label(8, y + 17, name, fs=lbl_fs)); y += rh
            else:
                b.append(label(16, y + 16, name, fs=lbl_fs))
            if s == e:
                cx = L + s * mw; cy = y + rh/2
                b.append(f'<polygon class="ms" points="{cx},{cy-8} {cx+8},{cy} {cx},{cy+8} {cx-8},{cy}"><title>{esc(name)}: M{s:g}</title></polygon>')
            else:
                b.append(f'<rect class="bar{li}" x="{L + s*mw + 1:.1f}" y="{y+5}" width="{(e-s)*mw - 2:.1f}" height="{rh-10}" rx="4"><title>{esc(name)}: M{s:g} to M{e:g}</title></rect>')
            y += rh
    return "".join(b), top + rows * rh

def d7():
    body, end = gantt(300, 1150, 40, 24, 12, False)
    H = end + 72
    body += label(300, H - 44, "Months from the owner's approval of the path. Estimates; ranges in §4.3. Pilot timing depends on a qualified prospect.", fs=11)
    body += label(300, H - 28, "Pilot and commercial dates hold with eight peak days a month and a two-day product reserve (TW25, TW26, open).", fs=11)
    body += label(300, H - 12, "With no peak days and a 4-day reserve, the commitment comes about weeks 12–24 and the first proved change about M5–M8 (§2.3).", fs=11)
    nb, nend = gantt(22, NW - 14, 30, 22, 13, True)
    nb += label(8, nend + 22, "Months from approval. Estimates (§4.3).", fs=12)
    for k, t_ in enumerate(("Pilot and commercial dates hold with eight peak", "days a month and a two-day product reserve", "(TW25, TW26, open); with no peak days and a", "4-day reserve, the commitment about weeks 12–24", "and the first proved change about M5–M8 (§2.3).")):
        nb += label(8, nend + 42 + 17 * k, t_, fs=12)
    nend += 85
    return svg(1170, H, body, "Figure 10. Roadmap in four lanes: product, data, pilots, commercial",
               "Swimlane timeline over ten months: product steps, data work, pilots and commercial milestones, as listed in the mermaid source. Pilot and commercial dates hold with eight peak days a month and a two-day product reserve (TW25, TW26, open); with no peak days and a 4-day reserve, the commitment comes about weeks 12–24 and the first proved change about M5–M8 (§2.3).", (NW, nend + 34, nb))

# ---------------------------------------------------------------- diagram 8: Layer 4 pack rounds by cause
CAUSES = {"A": ("Direction not approved before building", "c1"), "B": ("New requirements added while a round ran", "c3"),
          "C": ("Figures typed; checks shared the author's assumptions", "c2"), "D": ("Fixed by instance, not by class", "c4"),
          "-": ("Accepted, or a new owner request", "cn")}
ROUNDS = [("rev 1", "A"), ("rev 2", "A"), ("rev 3", "A"), ("rev 4", "A"), ("rev 5", "B"), ("rev 6", "C"), ("rev 7", "B"), ("rev 8", "C"),
          ("rev 9", "C"), ("rev 10", "C"), ("rev 11", "C"), ("rev 12", "C"), ("rev 13", "-"), ("§7 r1", "-"), ("§7 r2", "D"),
          ("§7 r3", "D"), ("pack", "D")]

def d8():
    b = []
    sz, gap, x0, y0 = 54, 8, 20, 30
    for i, (nm, c) in enumerate(ROUNDS):
        x = x0 + i * (sz + gap)
        b.append(f'<rect class="{CAUSES[c][1]}" x="{x}" y="{y0}" width="{sz}" height="{sz}" rx="4"><title>{esc(nm)}: {esc(CAUSES[c][0])}</title></rect>')
        b.append(label(x + sz/2, y0 + sz/2 + 6, c if c != "-" else "✓", anchor="middle", fs=16, cls="on", weight="700"))
        b.append(label(x + sz/2, y0 + sz + 18, nm, anchor="middle", fs=11.5))
    b.append(label(x0, 18, "16 Nov 16:52  →  18 Nov 05:38 (commit times). Classification: the author's judgement from the review verdicts.", fs=12))
    ly = y0 + sz + 48
    for j, k in enumerate(("A", "B", "C", "D", "-")):
        cnt = sum(1 for _, c in ROUNDS if c == k)
        x = x0 + (j % 2) * 540; y = ly + (j // 2) * 26
        b.append(f'<rect class="{CAUSES[k][1]}" x="{x}" y="{y - 13}" width="16" height="16" rx="3"/>')
        b.append(label(x + 24, y, f"{k if k != '-' else '✓'}  {CAUSES[k][0]} ({cnt})", fs=12.5, cls="t"))
    H = ly + 3 * 26 + 6
    W = x0 + len(ROUNDS) * (sz + gap) + 12
    # narrow: one bar per cause, length = rounds
    n, y = [], 10
    for k in ("A", "B", "C", "D", "-"):
        cnt = sum(1 for _, c in ROUNDS if c == k)
        which = ", ".join(nm for nm, c in ROUNDS if c == k)
        words, lines_ = f"{k if k != '-' else '✓'}  {CAUSES[k][0]}".split(" "), [""]
        for w_ in words:   # wrap at about 40 characters so no label leaves the 400-unit viewBox
            lines_[-1:] = [lines_[-1] + " " + w_] if len(lines_[-1] + " " + w_) <= 41 else [lines_[-1], "   " + w_]
        for li_, t_ in enumerate(lines_):
            n.append(label(10, y + 14 + li_ * 17, t_.strip() if li_ == 0 else t_, fs=13, cls="t", weight="600"))
        y += (len(lines_) - 1) * 17
        n.append(f'<rect class="{CAUSES[k][1]}" x="10" y="{y + 22}" width="{cnt * 44}" height="18" rx="4"><title>{esc(which)}</title></rect>')
        n.append(label(16 + cnt * 44, y + 36, f"{cnt}: {which}" if len(which) < 22 else f"{cnt} rounds", fs=12.5))
        y += 52
    return svg(W, H, "".join(b), "Figure 12. The Layer 4 pack's review rounds, by the cause of the next round (the author's classification, a judgement)",
               "Seventeen rounds: four lost to a direction not approved before building, two to requirements added while a round ran (revisions 5 and 7), six to typed figures found one at a time (revisions 6 and 8-12), three to fixing instances rather than classes; two were accepted work or a new request.",
               (NW, y + 4, "".join(n)))

# ---------------------------------------------------------------- diagram 9: the build workflow
def d9():
    b = []
    steps = [(["Structure spec", "factors, decisions,", "screens, tests"], "bxa"), (["Owner approves", "the structure", "(one sitting)"], "bx"),
             (["Independent", "checks written", "and reviewed"], "bxa"), (["Readiness", "dry-read", "against code"], "bxa"),
             (["Build", "two lanes,", "small units"], "bxa"), (["Review", "depth by risk"], "bxa"), (["Class fix", "and sweep;", "stop rule"], "bxa"),
             (["Phase end:", "owner", "walkthrough", "(one sitting)"], "bx")]
    w, h, gx = 118, 76, 22
    for i, (t, c) in enumerate(steps):
        x = 20 + i * (w + gx)
        b.append(box(x, 70, w, h, t, cls=c, fs=12))
        if i: b.append(arrow([(x - gx, 108), (x - 2, 108)]))
        b.append(label(x + w/2, 62, f"W{[1, 1, 2, 4, 4, 5, 6, 8][i]}" + ("/W7" if i == 6 else "/W3" if i in (1, 7) else ""), anchor="middle", fs=11))
    xb = 20 + 4 * (w + gx)
    b.append(box(xb - 90, 190, 300, 52, ["Decision queue (W3)", "defaults applied; owner answers in batch"], cls="bxp", fs=12))
    b.append(arrow([(xb + w/2, 190), (xb + w/2, 148)], cls="ard"))
    b.append(box(20, 268, 1100, 46, ["Pilot calendar (W9): data agreement → deep-dive → after-window → closed month, alongside the build"], cls="bxp", fs=12.5))
    b.append(label(20, 30, "One phase of the build. Owner time sits in two fixed sittings plus the queue; agents never wait.", fs=12.5, cls="t"))
    narrow = vstack([("r", [(["Structure spec (W1)", "factors, decisions, screens, tests"], "bxa")]),
                     ("r", [(["Owner approves structure", "one sitting (W1, W3)"], "bx")]),
                     ("r", [(["Independent checks (W2)", "written and reviewed first"], "bxa")]),
                     ("r", [(["Readiness dry-read (W4)", "against the code"], "bxa")]),
                     ("r", [(["Build (W4)", "two lanes, small units"], "bxa")]),
                     ("n", "Decision queue (W3): defaults applied,\nthe owner answers in batches; no agent waits."),
                     ("r", [(["Review by risk (W5)"], "bxa")]),
                     ("r", [(["Class fix and sweep (W6)", "stop rule after two repeats (W7)"], "bxa")]),
                     ("r", [(["Phase-end walkthrough (W8)", "one sitting"], "bx")]),
                     ("n", "Pilot calendar (W9) runs alongside: agreement,\ndeep-dive, after-window, closed month.")])
    return svg(1140, 330, "".join(b), "Figure 13. The build workflow for one phase",
               "Structure specification, owner approval of the structure, independent checks, readiness dry-read, build in two lanes, review by risk, class fixes with a stop rule, phase-end walkthrough; a decision queue with defaults feeds the build; the pilot calendar runs alongside.", narrow)

# ---------------------------------------------------------------- diagram 10: effort ranges, revision 1 against revised (weeks)
# Revised bars: build at 1-3 days per reviewed change, five working days to the week (§4.3 table). The last row is the §4.3
# elapsed range (the 16-change chain plus 15-20% rework plus four weeks of owner time), not a sum of the bars above.
EFFORT = [("Calibration + step 1 (lane 2)", (2, 4), (1, 3.5)), ("Steps 2–3 (lane 1)", (6, 10), (2, 5.5)),
          ("Step 4 (both lanes)", (8, 14), (1.5, 5)), ("Step 5 ‖ step 7, then 6", (2, 4), (1, 3)),
          ("Core, elapsed (§4.3)", (17, 30), (8, 16))]
TOTAL = "Core, elapsed (§4.3)"

def d10():
    def body(L, R, rh, lab_above, fs):
        sx = (R - L) / 30
        b, y = [], 34
        for v in range(0, 31, 5):
            x = L + v * sx
            b.append(f'<line class="grid" x1="{x:.1f}" x2="{x:.1f}" y1="26" y2="{34 + len(EFFORT) * rh}"/>')
            b.append(label(x, 20, f"{v} wk", anchor="middle", fs=12 if lab_above else 11))
        for name, old, new in EFFORT:
            if name == TOTAL:
                b.append(f'<line class="conn" x1="8" x2="{R}" y1="{y - 4}" y2="{y - 4}"/>')
            if lab_above:
                b.append(label(8, y + 14, name, fs=fs, cls="t")); yb = y + 20
            else:
                b.append(label(L - 12, y + 22, name, anchor="end", fs=fs, cls="t")); yb = y + 6
            for k, (lo, hi), cls in ((0, old, "rold"), (1, new, "rnew")):
                yy = yb + k * 16
                b.append(f'<rect class="{cls}" x="{L + lo*sx:.1f}" y="{yy}" width="{(hi-lo)*sx:.1f}" height="12" rx="4"><title>{esc(name)}: {lo:g}–{hi:g} weeks ({"revision 1" if k == 0 else "revised"})</title></rect>')
                b.append(label(L + hi*sx + 6, yy + 11, f"{lo:g}–{hi:g}", fs=12))
            y += rh
        return "".join(b), y
    wb, wy = body(260, 900, 46, False, 12.5)
    wb += f'<rect class="rold" x="260" y="{wy + 8}" width="14" height="10" rx="3"/>' + label(280, wy + 17, "Revision 1 (1–2 weeks per reviewed change)", fs=12, cls="t")
    wb += f'<rect class="rnew" x="580" y="{wy + 8}" width="14" height="10" rx="3"/>' + label(600, wy + 17, "Revised (observed pace, workflow in §5)", fs=12, cls="t")
    wb += label(260, wy + 40, "Bars above the line: build on each lane. Below: the §4.3 elapsed range, with rework and owner time; not a sum.", fs=11.5)
    nb, ny = body(24, NW - 50, 60, True, 13)
    nb += f'<rect class="rold" x="10" y="{ny + 6}" width="14" height="10" rx="3"/>' + label(30, ny + 15, "Revision 1", fs=12.5, cls="t")
    nb += f'<rect class="rnew" x="150" y="{ny + 6}" width="14" height="10" rx="3"/>' + label(170, ny + 15, "Revised", fs=12.5, cls="t")
    nb += label(10, ny + 36, "Last row: the §4.3 elapsed range, not a sum.", fs=12.5)
    return svg(960, wy + 52, wb, "Figure 11. Build effort in weeks: revision 1 against the revised ranges (estimates)",
               "Revised bars are build time at one to three days per reviewed change, on the grounded path. Calibration and step 1 (lane 2, alongside steps 2-3): 2-4 weeks to about 1-3.5. Steps 2-3: 6-10 to about 2-5.5. Step 4: revision 1 counted it with steps 5 and 6 (8-14); revised about 1.5-5. Step 5 in lane 1 beside step 7 then step 6 in lane 2: revision 1 gave step 7 alone 2-4; revised about 1-3. Core elapsed, the §4.3 range with rework and owner time and not a sum of the bars: 17-30 weeks (4-7 months) to about 8-16 weeks (2-4 months).",
               (NW, ny + 46, nb))

# ---------------------------------------------------------------- diagram 11: grounding today's chain on the primitives
MAP_ROWS = [(["Finding and its thread", "dispatch, fuel balance, excursion,", "fault; recurrence history"],
             ["Observation on a factor key", "a deviation, a bound at risk or a", "latent factor; Evaluate acts on it"]),
            (["Outcome map", "moves / checks rows,", "contribution records"],
             ["Registry rows", "observer row per signal; roles;", "obligation bounds with a policy"]),
            (["What-ifs, scenarios,", "headroom opportunity,", "reserve recommendation"],
             ["Options", "factor changes valued against", "no action, net of their cost"]),
            (["Action, domain action,", "work case", "(the user acts and tracks)"],
             ["Carrier of the chosen option", "frozen prediction; the user", "acts and tracks through it"]),
            (["Verification", "plan freeze, operational", "verdict (mini-grid)"],
             ["Three verdicts", "operational kept; economic and", "causal beside it, same factors"])]

def d11():
    b = [label(10, 22, "Today's construct", fs=13, weight="600"), label(330, 22, "On the primitives", fs=13, weight="600"),
         label(740, 22, "One structure registry", fs=13, weight="600")]
    y0, rh, h = 40, 84, 68
    for i, (old, new) in enumerate(MAP_ROWS):
        y = y0 + i * rh
        b.append(box(10, y, 270, h, old, fs=12))
        b.append(box(330, y, 330, h, new, cls="bxa", fs=12))
        b.append(arrow([(280, y + h/2), (328, y + h/2)]))
    top, bot = y0, y0 + 4 * rh + h
    b.append(f'<rect class="grp" x="730" y="{top - 6}" width="440" height="{bot - top + 12}" rx="10"/>')
    yo, yf, yl = top + 8, top + 118, bot - 86
    b.append(box(750, yo, 400, 70, ["Outcomes", "contribution · cost per departure met ·", "Protect measures · evidence state"], cls="bx", fs=12))
    b.append(box(750, yf, 400, yl - yf - 40, ["Factors", "factor ID · period ID · unit · plan ·", "evidence class · bounds · who bears the cost"], cls="bxa", fs=12))
    b.append(box(750, yl, 400, 72, ["Leaf factors from source records", "telemetry · emulated exports, then", "the operator's own exports"], cls="bx", fs=12))
    b.append(arrow([(950, yl), (950, yl - 38)])); b.append(arrow([(950, yf), (950, yo + 72)]))
    b.append(label(960, yl - 16, "read upward", fs=11.5)); b.append(label(960, yf - 18, "read upward", fs=11.5))
    for i in range(5):
        y = y0 + i * rh + h/2
        ty = min(max(y, yf + 14), yl - 54)
        b.append(arrow([(660, y), (700, y), (700, ty), (748, ty)], cls="ard"))
    b.append(label(10, bot + 30, "Every role on the right is keyed to a factor of the one registry. Findings attach at a factor and outcomes are read upward through the factors; no construct carries an outcome value of its own.", fs=11.5))
    narrow = [("h", "Today → on the primitives")]
    for old, new in MAP_ROWS:
        narrow += [("r", [(old, "bx")]), ("r", [(new, "bxa")]), ("x",)]
    narrow += [("h", "One structure registry, read upward"),
               ("r", [(["Leaf factors", "from source records: telemetry,", "emulated, then the operator's exports"], "bx")]), ("a", "computed into", "ar"),
               ("r", [(["Factors", "factor and period IDs, unit, plan,", "evidence class, bounds, cost-bearer"], "bxa")]), ("a", "computed into", "ar"),
               ("r", [(["Outcomes", "contribution, Protect measures"], "bx")]),
               ("n", "Every role above is keyed to a factor.\nFindings attach at a factor; outcomes are\nread upward; nothing carries its own outcome.")]
    return svg(1180, bot + 46, "".join(b), "Figure 8. Grounding today's chain on the Layer 4 primitives",
               "Five of today's constructs, each mapped to its role on the primitives: a finding becomes an observation on a factor key that Evaluate acts on; the outcome map becomes registry rows and obligation bounds; what-ifs and the reserve recommendation become options against no action; actions, domain actions and work cases carry the chosen option, which the user acts on and tracks; verification becomes three verdicts. Every role is keyed to one structure registry, in which leaf factors from source records are read upward to outcomes.", vstack(narrow))

# ---------------------------------------------------------------- diagram 12: the compromise register, parsed from its table
STEP_COLS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

def _register():
    rows, on = [], False
    for ln in open(SRC, encoding="utf-8").read().split("\n"):
        if ln.startswith("| ID | Compromise taken early"): on = True; continue
        if on and ln.startswith("|---"): continue
        if on and ln.startswith("|"):
            c = cells(ln); nm = re.match(r"\*\*(.+?)\*\*", c[1]); rows.append((c[0], nm.group(1) if nm else c[1], int(c[5]), int(c[6])))
        elif on: break
    return rows

def d12():
    R = _register()
    def body(L, Rx, rh, fs, wrap):
        sx = (Rx - L) / 9.6
        b = []
        names = ["phase 0", "1 screens", "2 records", "3 structure", "4 decisions", "5 plan", "6 rights", "7 proof", "8 verticals", "9 pilot"]
        top = 52 if wrap else 40
        for k in range(10):
            x = L + (k + 0.3) * sx
            b.append(f'<line class="grid" x1="{x:.1f}" x2="{x:.1f}" y1="{top - 6}" y2="{top + len(R) * rh}"/>')
            if wrap:
                b.append(label(x, top - 26, names[k].split(" ")[0], anchor="middle", fs=12))
            else:
                b.append(label(x, top - 12, names[k], anchor="middle", fs=11))
        y = top
        for cid, text, t0, t1 in R:
            short = text if len(text) <= 58 else text[:56].rsplit(" ", 1)[0] + " …"
            if wrap:
                b.append(label(8, y + 14, f"{cid} {short[:44] + (' …' if len(short) > 44 else '')}", fs=fs, cls="t")); yb = y + 20
            else:
                b.append(label(L - 10, y + 17, f"{cid}  {short}", anchor="end", fs=fs, cls="t")); yb = y + 6
            x0, x1 = L + (t0 + 0.3) * sx, L + (t1 + 0.3) * sx
            b.append(f'<rect class="rnew" x="{x0:.1f}" y="{yb}" width="{max(x1 - x0, 4):.1f}" height="14" rx="4"><title>{esc(cid)}: taken at step {t0}, retired by step {t1}</title></rect>')
            b.append(f'<circle class="ms" cx="{x1:.1f}" cy="{yb + 7}" r="6"><title>{esc(cid)} retired by step {t1}</title></circle>')
            y += rh
        return "".join(b), y
    wb, wy = body(520, 1160, 34, 12, False)
    wb += label(10, wy + 22, "Bar: the compromise is in force, from the step that takes it to the step that retires it (dot). Steps as in §3.1; phase 0 is the calibration lane and the kit.", fs=11.5)
    nb, ny = body(24, NW - 16, 44, 12.5, True)
    nb += label(8, ny + 18, "Bar: in force from the step that takes it to the", fs=12.5)
    nb += label(8, ny + 36, "step that retires it (dot). Steps as in §3.1.", fs=12.5)
    return svg(1180, wy + 40, wb, "Figure 9. Purity catches up: when each early compromise is taken and retired",
               "One bar per compromise in the register of §3.9, from the step that takes it to the step that retires it: " +
               "; ".join(f"{c} step {a} to {z}" for c, _, a, z in R) + ".", (NW, ny + 48, nb))

DIAGRAMS = [d1, d2, d3, d4, d5, d6, d7, d8, d9]   # in the order of the mermaid blocks
MARKERS = {"visible": d7v, "effort": d10, "mapping": d11, "register": d12}

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
    return [c.strip() for c in re.split(r"(?<!\\)\|", row)]

lines = open(SRC, encoding="utf-8").read().split("\n")
body, toc, i, dg = [], [], 0, 0
while i < len(lines):
    ln = lines[i]
    if ln.startswith("```mermaid"):
        i += 1
        while not lines[i].startswith("```"):
            i += 1
        body.append(DIAGRAMS[dg]()); dg += 1; i += 1; continue
    mk = re.fullmatch(r"<!--diagram:(\w+)-->", ln.strip())
    if mk:
        body.append(MARKERS[mk.group(1)]()); i += 1; continue
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
tochtml = '<nav class="toc" aria-label="Contents"><strong>Contents</strong><ul>' + "".join(
    f'<li class="l{l}"><a href="#{s}">{t}</a></li>' for l, s, t in toc) + "</ul></nav>"
# place the contents after the header block (before the first <hr>)
first_hr = body.index("<hr>")
body.insert(first_hr, tochtml)

TOK_L = "--bg:#f6f7f9;--fg:#18212f;--muted:#5d6878;--line:#dfe3ea;--card:#fff;--accent:#1d4ed8;--code:#eef1f5;--acard:#eef3ff;--pcard:#f4f5f7;--neg:#c2410c;--pos:#2563eb;--tot:#8a94a3;--lane:#eef1f5;--c1:#2563eb;--c2:#c2410c;--c3:#7c3aed;--c4:#0d9488;--cn:#8a94a3"
TOK_D = "--bg:#11161d;--fg:#e4e8ee;--muted:#9aa5b4;--line:#2a3340;--card:#171d26;--accent:#7aa2f7;--code:#1f2733;--acard:#1a2540;--pcard:#1b212b;--neg:#ea580c;--pos:#3b82f6;--tot:#6b7584;--lane:#1f2733;--c1:#3b82f6;--c2:#ea580c;--c3:#8b5cf6;--c4:#0d9488;--cn:#6b7584"
CSS = f""":root{{{TOK_L}}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{{TOK_D}}}}}
:root[data-theme=dark]{{{TOK_D}}}
""" + """body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}
.wrap{max-width:1100px;margin:0 auto;padding:24px 16px 80px}h1{font-size:28px;line-height:1.25}h2{margin-top:44px;padding-top:12px;border-top:1px solid var(--line)}h3{margin-top:28px}
a{color:var(--accent)}code{background:var(--code);padding:1px 4px;border-radius:3px;font-size:.88em;overflow-wrap:anywhere}
.tw{overflow-x:auto;margin:12px 0;border:1px solid var(--line);border-radius:6px;background:var(--card)}table{border-collapse:collapse;width:100%;font-size:13.5px}th,td{text-align:left;vertical-align:top;padding:7px 9px;border-bottom:1px solid var(--line)}th{background:var(--code);font-weight:600}
blockquote{margin:16px 0;padding:10px 14px;border-left:4px solid var(--accent);background:var(--card)}hr{border:0;border-top:1px solid var(--line);margin:32px 0}
.toc{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:12px 16px;margin:20px 0}.toc ul{margin:6px 0;padding-left:18px}.toc .l3{margin-left:16px;font-size:.93em}
figure.dg{margin:16px 0;padding:12px;background:var(--card);border:1px solid var(--line);border-radius:6px}figure.dg svg{display:block;width:100%;height:auto}
figure.dg svg.narrow{display:none;max-width:520px;margin:0 auto}
@media (max-width:999px){figure.dg svg.wide{display:none}figure.dg svg.narrow{display:block}}
figcaption{color:var(--muted);font-size:13px;margin-top:6px}
svg .bx{fill:var(--card);stroke:var(--muted);stroke-width:1.2}svg .bxa{fill:var(--acard);stroke:var(--accent);stroke-width:1.4}svg .bxp{fill:var(--pcard);stroke:var(--muted);stroke-width:1.2;stroke-dasharray:5 4}
svg .grp{fill:none;stroke:var(--line);stroke-width:1.5;stroke-dasharray:6 4}
svg .t{fill:var(--fg)}svg .lb{fill:var(--muted)}svg .on{fill:#fff}svg .ar{fill:none;stroke:var(--muted);stroke-width:1.6}svg .ard{fill:none;stroke:var(--muted);stroke-width:1.4;stroke-dasharray:5 4}
svg .arc{fill:none;stroke:var(--neg);stroke-width:3.2}svg .mk{fill:var(--muted)}svg .mkc{fill:var(--neg)}
svg .grid{stroke:var(--line);stroke-width:1}svg .conn{stroke:var(--muted);stroke-width:1;stroke-dasharray:3 3}
svg .wneg{fill:var(--neg)}svg .wpos{fill:var(--pos)}svg .wtot{fill:var(--tot)}
svg .c1{fill:var(--c1)}svg .c2{fill:var(--c2)}svg .c3{fill:var(--c3)}svg .c4{fill:var(--c4)}svg .cn{fill:var(--cn)}svg .rold{fill:var(--tot)}svg .rnew{fill:var(--accent)}
svg .lane{fill:var(--lane)}svg .chw{fill:var(--acard);stroke:var(--accent);stroke-width:1.2;stroke-dasharray:4 3}svg .chr{fill:var(--pcard);stroke:var(--neg);stroke-width:1.4}svg .bar0,svg .bar1,svg .bar2,svg .bar3{fill:var(--accent)}svg .bar1{opacity:.75}svg .bar2{opacity:.6}svg .bar3{opacity:.45}svg .ms{fill:var(--neg)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}"""

page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Product Transition Roadmap</title><style>' + CSS + '</style></head><body><main class="wrap">' + "".join(body) + "</main></body></html>")
open(OUT, "w", encoding="utf-8").write(page)
print("ok", len(page), "diagrams", dg + sum(1 for x in lines if re.fullmatch(r"<!--diagram:(\w+)-->", x.strip())))
