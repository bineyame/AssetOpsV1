"""The inline SVG figures of layer4-transformation-design.md (rev 16): Figure 2, the factor structure, and Figure 3,
plan against actual. Each shows a change, with today's construct as context on the left (owner, 19 Nov: diagrams only
where something changes).

Imported by render_design_html.py: a line `<!--diagram:NAME-->` in the .md, followed by a mermaid block (the plain-text
source a Markdown viewer shows), is replaced in the HTML by `FIGURES[NAME]()`. Each figure has a wide layout (two
panels side by side) and a narrow layout (stacked, 404 units wide, shown below 1000 px), so the smallest text stays at
about 11 px or more on a 390 px phone instead of shrinking. Every Kobo figure is read from derived-values.json (the
evaluator's output, which check_manifest.py checks against the independent model); none is typed here. Claims about
today's code are the document's, with their file:line citations, not this file's.
Check: python3 motivation_figures.py --check"""
import html, json, pathlib, zlib

DV = json.loads((pathlib.Path(__file__).resolve().parent / "derived-values.json").read_text(encoding="utf-8"))
KP = DV["sites"]["lakeside-power/Kobo"]["plan"]["nodes"]
KA = DV["sites"]["lakeside-power/Kobo"]["actual"]["nodes"]
OPT = DV["options"]

PW, FS, LH, GAP = 400, 13, 17, 26   # panel width, body font size, line height, gap between rows (SVG units)
CHAR = 0.56                         # mean glyph width / font size, used to refuse a line that would overflow its box


def esc(s): return html.escape(s, quote=True)


def n0(v): return f"{v:,.0f}"


def m2(v): return f"{v:,.2f}".replace("-", "−")


def text(x, y, s, cls="t", fs=FS, anchor="middle", weight=None):
    w = f' font-weight="{weight}"' if weight else ""
    return f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="{fs}"{w}>{esc(s)}</text>'


def box(x, y, w, b):
    """b = (lines, cls, tag): first line bold; the tag (what becomes of it) is the last line, in the accent colour."""
    lines, cls, tag = b
    rows = list(lines) + ([tag] if tag else [])
    for i, s in enumerate(rows):
        need = len(s) * FS * (CHAR + (0.05 if i == 0 else 0)) + 12
        assert need <= w, f"line too long for its box ({need:.0f} > {w:.0f}): {s!r}"
    h = len(rows) * LH + 12
    out = [f'<rect class="{cls}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="7"/>']
    for i, s in enumerate(rows):
        c = "tg" if tag and i == len(rows) - 1 else "t"
        out.append(text(x + w / 2, y + 6 + LH * (i + 1) - 4, s, cls=c, weight="600" if i == 0 else None))
    return h, "".join(out)


def arrow(x1, y1, x2, y2, cls="ar"):
    return f'<path class="{cls}" d="M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f}" marker-end="url(#m)"/>'


def panel(title, entries, up=False):
    """A column 400 units wide. Entries: ("h", text) panel title; ("n", text) muted note ("\\n" splits lines);
    ("x",) no arrows into the next row; ("r", [box, ...], parents) a row of boxes, each joined to the boxes of the
    previous row listed in parents[i] (default: the same index, or the last one). With up=True the arrows point from a
    row to the row above it (a structure read upward); otherwise downward (a sequence)."""
    b, y, prev = [text(0, 18, title, anchor="start", fs=15, weight="600")], 30, None
    for e in entries:
        if e[0] == "n":
            for ln in e[1].split("\n"):
                assert len(ln) * FS * CHAR <= PW, f"note too long: {ln!r}"
                b.append(text(0, y + 14, ln, cls="lb", anchor="start")); y += LH
            y += 6; prev = None
        elif e[0] == "x":
            prev = None; y += 8
        else:
            row, parents = e[1], (e[2] if len(e) > 2 else None)
            n = len(row); bw = (PW - (n - 1) * 10) / n
            y += GAP if prev is not None else 6
            xs = [i * (bw + 10) for i in range(n)]
            hs = []
            for x, bx in zip(xs, row):
                h, s = box(x, y, bw, bx); hs.append(h); b.append(s)
            if prev is not None:
                py, pxs, pbw, pys = prev
                for i, x in enumerate(xs):
                    ps = parents[i] if parents else [min(i, len(pxs) - 1)]
                    for p in (ps if isinstance(ps, list) else [ps]):
                        sx, cx = pxs[p] + pbw / 2, x + bw / 2
                        if up:
                            b.append(arrow(cx, y - 2, sx, pys[p] + 3))
                        else:
                            b.append(arrow(sx, pys[p] + 2, cx, y - 3))
            prev = (y + max(hs), xs, bw, [y + h for h in hs]); y += max(hs)
    return y + 8, "".join(b)


DEFS = ('<defs><marker id="m" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker></defs>')


def figure(title, desc, left, right):
    """Wide: the two panels side by side, 860 units. Narrow: stacked, 404 units."""
    (lh, lb), (rh, rb) = left, right
    k = zlib.crc32(title.encode())

    def one(cls, w, h, body, sfx):
        mid = f"m{k}{sfx}"
        defs = DEFS.replace('id="m"', f'id="{mid}"')
        return (f'<svg class="{cls}" viewBox="0 0 {w} {h:.0f}" role="img" aria-labelledby="t{k}{sfx} d{k}{sfx}">'
                f'<title id="t{k}{sfx}">{esc(title)}</title><desc id="d{k}{sfx}">{esc(desc)}</desc>'
                f'{defs}'
                f'{body.replace("url(#m)", f"url(#{mid})")}</svg>')

    lw, lwh, ln, lnh = legend()
    wh = max(lh, rh) + 20
    wide = (f'<g transform="translate(10,10)">{lb}</g>'
            f'<line class="div" x1="430" y1="10" x2="430" y2="{wh - 10:.0f}"/>'
            f'<g transform="translate(450,10)">{rb}</g>'
            f'<g transform="translate(10,{wh + 4:.0f})">{lw}</g>')
    nh = lh + rh + 40
    narrow = (f'<g transform="translate(2,6)">{lb}</g>'
              f'<line class="div" x1="2" y1="{lh + 18:.0f}" x2="402" y2="{lh + 18:.0f}"/>'
              f'<g transform="translate(2,{lh + 34:.0f})">{rb}</g>'
              f'<g transform="translate(2,{nh + 4:.0f})">{ln}</g>')
    return (f'<figure class="dg">{one("wide", 860, wh + lwh + 12, wide, "w")}{one("narrow", 404, nh + lnh + 10, narrow, "n")}'
            f'<figcaption>{esc(title)}</figcaption></figure>')


def B(lines, cls="bx", tag=None): return (lines, cls, tag)


def legend():
    """The one legend, drawn under each layout: (wide body, wide height, narrow body, narrow height)."""
    def sample(x, y, cls, t):
        return f'<rect class="{cls}" x="{x}" y="{y}" width="26" height="15" rx="4"/>' + text(x + 34, y + 12, t, cls="lb", anchor="start")
    exp = "Italic line: stays or changes"
    wide = sample(0, 0, "bxp", "not held today") + sample(170, 0, "bxa", "proposed") + text(300, 12, exp, cls="tg", anchor="start")
    narrow = sample(0, 0, "bxp", "not held today") + sample(170, 0, "bxa", "proposed") + text(0, 36, exp, cls="tg", anchor="start")
    return wide, 22, narrow, 44




def fig_structure():
    """Figure 2 (§2.1): the factor structure (B1) with today's Findings pinned to their factors (CH1)."""
    today = panel("Today (context): an outcome is flagged", [
        ("r", [B(["Outcome: supply cost per kWh", "state from Findings, warnings and", "objective verdicts"],
                 tag="changes: computed from its factors")]),
        ("r", [B(["Fixed map row", "mechanism → outcome key;", "no quantity between them"],
                 tag="changes: becomes a structure row")]),
        ("r", [B(["Finding: candidate running", "revised result of dispatch-3.2:", "history, thread, claim ceiling"],
                 tag="stays; gains its factor")]),
        ("r", [B(["Possible extra fuel cost", "0 up to an upper bound, per", "Finding, never summed"],
                 tag="stays: an at-stake bound, not a value")]),
        ("x",),
        ("r", [B(["Not held", "billing, receipts, O&M and", "staff costs, a money plan"], cls="bxp")]),
    ])
    fuel_p, fuel_a = KP["necessary_l"] + KP["candidate_l"] + KP["unexplained_l"], KA["diesel_l"]
    l4 = panel("With the factor structure (Kobo, October)", [
        ("r", [B(["Contribution", f"plan {n0(KP['contribution'])} · actual {n0(KA['contribution'])}"], cls="bxa")]),
        ("r", [B(["Revenue", "billed kWh × tariff", f"{n0(KP['revenue'])} → {n0(KA['revenue'])}"], cls="bxa"),
               B(["Cost to serve", "fuel + O&M + staff", f"{n0(KP['cost_to_serve'])} → {n0(KA['cost_to_serve'])}"],
                 cls="bxa")], [0, 0]),
        ("r", [B(["Billed kWh", f"{n0(KP['billed_kwh'])} → {n0(KA['billed_kwh'])}"], cls="bxa"),
               B(["Fuel litres", f"{n0(fuel_p)} → {n0(fuel_a)}", f"× {m2(KA['diesel_price'])} per L"], cls="bxa"),
               B(["O&M, staff", f"{n0(KP['om'] + KP['staff'])} → {n0(KA['om'] + KA['staff'])}"], cls="bxa")],
         [0, 1, 1]),
        ("r", [B(["Necessary", f"{n0(KP['necessary_l'])} → {n0(KA['necessary_l'])} L"], cls="bxa"),
               B(["Candidate", f"{n0(KP['candidate_l'])} → {n0(KA['candidate_l'])} L", "◆ Finding"], cls="bxa"),
               B(["Unexplained", f"{n0(KP['unexplained_l'])} → {n0(KA['unexplained_l'])} L", "◆ Finding"],
                 cls="bxa")], [1, 1, 1]),
        ("n", f"Cash: {n0(KA['collected'])} collected of {n0(KA['revenue'])} billed,\n"
              f"{n0(KA['outstanding'])} outstanding.\n◆ Today's Findings stay, pinned to their factor.\n"
              "Every leaf: factor ID, period, unit, plan, evidence\nclass and provenance."),
        ("r", [B(["Telemetry (held today)", "dispatch split,", "fuel balance, dips"]),
               B(["Commercial records", "billing, receipts, plan,", "O&M and staff invoices"], cls="bxp")]),
    ], up=True)
    return figure("Figure 2. The factor structure: Kobo's contribution read upward, with today's Findings pinned to "
                  "their factors",
                  "Left, today as context: an outcome's state is set from Findings, warnings and objective verdicts "
                  "through a fixed map row with no quantity between signal and outcome; the candidate-running "
                  "Finding stays and gains its factor; the possible extra fuel cost stays as an at-stake bound; "
                  "billing, receipts, O&M and staff costs and a money plan are not held. Right: Kobo's October "
                  "contribution read upward from revenue and cost to serve, billed kWh, fuel litres split into "
                  "necessary, candidate and unexplained, and O&M and staff; the two existing Findings pin to the "
                  "candidate and unexplained litres; leaves come from telemetry held today and from new commercial "
                  "records.", today, l4)


def fig_bridge():
    """Figure 3 (§2.2): performance against target, before and after (B2)."""
    ef = lambda k: -(KA[k] - KP[k]) * KA["diesel_price"]
    today = panel("Today (context): the Assure row", [
        ("r", [B(["Actual against plan", "\"N of M declared objectives met\""], tag="stays as operational targets")]),
        ("r", [B(["Objective: avoidable generator", "minutes per day at most a target;", "MET, MISSED or not judged"],
                 tag="stays; becomes a factor's plan")]),
        ("r", [B(["Declared by the system", "\"not a customer target\"; no money", "target is ever judged"],
                 tag="changes: the operator declares plans")]),
        ("x",),
        ("r", [B(["Not held", "a planned contribution, plan lines", "per factor, a month's bridge"], cls="bxp")]),
    ])
    l4 = panel("With plans at factor level (Kobo, October)", [
        ("r", [B(["Planned contribution", n0(KP["contribution"])], cls="bxa")]),
        ("r", [B(["Candidate running", f"{m2(ef('candidate_l'))}", "◆ Finding"], cls="bxa"),
               B(["Unexplained fuel", f"{m2(ef('unexplained_l'))}", "◆ Finding"], cls="bxa")], [0, 0]),
        ("r", [B(["Necessary running", f"{m2(ef('necessary_l'))}", "no Finding today"], cls="bxa"),
               B(["kWh billed", f"+{m2((KA['billed_kwh'] - KP['billed_kwh']) * KA['tariff'])}", "favourable"],
                 cls="bxa")], [0, 1]),
        ("r", [B(["Actual contribution", n0(KA["contribution"]),
                  f"{m2(KA['contribution'] - KP['contribution'])} in all"], cls="bxa")], [[0, 1]]),
        ("n", "O&M and staff on plan. Each effect is\n(actual − plan) × its price; they add up exactly.\n"
              "A month with no Finding still shows its bridge."),
    ])
    return figure("Figure 3. Performance against target: from objectives met to a plan-against-actual bridge",
                  "Left, today as context: the Assure row counts declared objectives met; an objective such as "
                  "avoidable generator minutes is judged MET or MISSED; objectives are declared by the system, not "
                  "the customer, and no money target is judged; a planned contribution and plan lines are not held. "
                  "Right: Kobo's planned contribution, the four factor effects (candidate running and unexplained "
                  "fuel, each with an existing Finding; necessary running; kWh billed, favourable) and the actual "
                  "contribution, with the effects adding up to the change.", today, l4)


FIGURES = {"factor-structure": fig_structure, "plan-against-actual": fig_bridge}


CSS = ('figure.dg{margin:16px 0;padding:12px;background:var(--card);border:1px solid var(--line);border-radius:6px}'
       'figure.dg svg{display:block;width:100%;height:auto}figure.dg svg.narrow{display:none;max-width:520px;margin:0 auto}\n'
       '@media (max-width:999px){figure.dg svg.wide{display:none}figure.dg svg.narrow{display:block}figure.dg{padding:6px}}\n'
       'figcaption{color:var(--muted);font-size:13px;margin-top:6px}\n'
       'svg .bx{fill:var(--card);stroke:var(--muted);stroke-width:1.2}svg .bxa{fill:var(--acard);stroke:var(--accent);stroke-width:1.4}'
       'svg .bxp{fill:var(--pcard);stroke:var(--muted);stroke-width:1.2;stroke-dasharray:5 4}\n'
       'svg .t{fill:var(--fg)}svg .lb{fill:var(--muted)}svg .tg{fill:var(--accent);font-style:italic}'
       'svg .ar{fill:none;stroke:var(--muted);stroke-width:1.5}svg .mk{fill:var(--muted)}svg .div{stroke:var(--line);stroke-width:1.5}\n')


def _check(md):
    """`--check`: every figure builds (each line is asserted to fit its box), every `<!--diagram:NAME-->` in the
    document has a figure, and every figure is used."""
    import re
    names = re.findall(r"<!--diagram:([\w-]+)-->", md)
    missing = [n for n in names if n not in FIGURES]
    unused = [n for n in FIGURES if n not in names]
    for n in FIGURES.values():
        n()
    print(f"{len(FIGURES)} figures built; markers {names}; missing {missing}; unused {unused}")
    return 1 if missing or unused else 0


if __name__ == "__main__":
    import sys
    if sys.argv[1:2] != ["--check"]:
        sys.exit("usage: python3 motivation_figures.py --check [layer4-transformation-design.md]")
    doc = sys.argv[2] if len(sys.argv) > 2 else str(pathlib.Path(__file__).resolve().parent / "layer4-transformation-design.md")
    sys.exit(_check(pathlib.Path(doc).read_text(encoding="utf-8")))
