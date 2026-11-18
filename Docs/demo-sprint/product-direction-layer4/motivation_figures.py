"""Figures 0.1-0.3 of layer4-transformation-design.md §0 (today's product against Layer 4), as inline SVG.

Imported by render_design_html.py: a line `<!--diagram:NAME-->` in the .md, followed by a mermaid block (the plain-text
source a Markdown viewer shows), is replaced in the HTML by `FIGURES[NAME]()`. Each figure has a wide layout (today and
Layer 4 side by side) and a narrow layout (stacked, 404 units wide, shown below 1000 px), so the smallest text stays at
about 11 px or more on a 390 px phone instead of shrinking. Every Kobo and Kirinyaga figure is read from
derived-values.json (the evaluator's output, which check_manifest.py checks against the independent model); none is
typed here. Claims about today's code are the section's, with their file:line citations, not this file's."""
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
    exp = "Italic line: what becomes of today's element"
    wide = sample(0, 0, "bxp", "not held today") + sample(170, 0, "bxa", "Layer 4") + text(300, 12, exp, cls="tg", anchor="start")
    narrow = sample(0, 0, "bxp", "not held today") + sample(170, 0, "bxa", "Layer 4") + text(0, 36, exp, cls="tg", anchor="start")
    return wide, 22, narrow, 44


def fig_data():
    today = panel("Today: separate stores, each keyed its own way", [
        ("r", [B(["Evidence ledger", "every reading: source, unit, quality,", "live or simulated, envelope hash"],
                 tag="kept: the telemetry source of leaves")]),
        ("r", [B(["Findings", "per site, mechanism", "and asset"], tag="re-keyed to factors"),
               B(["Threads", "per site, mechanism", "and subject"], tag="re-keyed: history")], [0, 0]),
        ("r", [B(["Outcome map", "16 signal rows point straight at", "outcome keys (moves, checks)"],
                 tag="reworked into registry rows")], [[0, 1]]),
        ("r", [B(["Outcome board per site", "drivers named in words, per outcome:",
                  "e.g. generator minutes, fuel, fuel price"], tag="reworked: drivers become factor rows")]),
        ("x",),
        ("r", [B(["Declared prices", "productive tariff,", "diesel price"], tag="kept: Estimated leaves"),
               B(["Objectives", "operational targets,", "e.g. generator minutes"], tag="re-keyed: factor plans")]),
        ("x",),
        ("r", [B(["Not held today", "billing, receipts, money plans, cost", "invoices, contracts; cold: occupancy,",
                  "cooling energy, repair costs"], cls="bxp")]),
        ("n", "Period reads (one revisioned row per site, kind and\nperiod) sit under the screens: kept as a pattern."),
    ])
    fuel_p, fuel_a = KP["necessary_l"] + KP["candidate_l"] + KP["unexplained_l"], KA["diesel_l"]
    l4 = panel("Layer 4: one structure, read upward (Kobo, Oct.)", [
        ("r", [B(["Contribution", f"plan {n0(KP['contribution'])} · actual {n0(KA['contribution'])}"], cls="bxa")]),
        ("r", [B(["Revenue", "billed kWh × tariff"], cls="bxa"),
               B(["Cost to serve", "fuel + O&M + staff"], cls="bxa")], [0, 0]),
        ("r", [B(["Billed kWh", f"{n0(KP['billed_kwh'])} → {n0(KA['billed_kwh'])}"], cls="bxa"),
               B(["Fuel litres", f"{n0(fuel_p)} → {n0(fuel_a)}", f"× {m2(KA['diesel_price'])} per L"], cls="bxa"),
               B(["O&M, staff", f"{n0(KP['om'] + KP['staff'])} → {n0(KA['om'] + KA['staff'])}"], cls="bxa")],
         [0, 1, 1]),
        ("r", [B(["Necessary", f"{n0(KP['necessary_l'])} → {n0(KA['necessary_l'])} L"], cls="bxa"),
               B(["Candidate", f"{n0(KP['candidate_l'])} → {n0(KA['candidate_l'])} L"], cls="bxa"),
               B(["Unexplained", f"{n0(KP['unexplained_l'])} → {n0(KA['unexplained_l'])} L"], cls="bxa")],
         [1, 1, 1]),
        ("n", "Every leaf: factor ID, period ID, unit, plan, evidence\nclass and provenance. Findings, decisions, "
              "options,\nActions and verdicts key to these factor IDs."),
        ("r", [B(["Telemetry ledger", "dispatch split,", "fuel balance"], cls="bxa"),
               B(["Commercial records", "billing, receipts, plan,", "cost invoices, contracts"], cls="bxp")]),
        ("n", "Commercial records come from emulated exports first,\nthen the operator's own."),
    ], up=True)
    return figure("Figure 0.1. How data is organised: today's stores beside one structure registry",
                  "Left, today: an evidence ledger (kept), Findings and threads keyed by site and mechanism (re-keyed "
                  "to factors), an outcome map pointing signals at outcome keys (reworked into registry rows), the "
                  "per-site outcome board whose drivers are named in words (reworked into factor rows), declared prices "
                  "and objectives; billing, receipts, money plans, cost invoices, contracts and, for cold rooms, "
                  "occupancy, cooling energy and repair costs are not held. Right, Layer 4: Kobo's contribution read "
                  "upward from revenue and cost to serve, billed kWh, fuel litres split into necessary, candidate and "
                  "unexplained, and O&M, over leaves fed by the telemetry ledger and new commercial records.",
                  today, l4)


def fig_processing():
    so, rs = OPT["KOB-STOPSOC"], OPT["KOB-RESERVE"]
    today = panel("Today: from readings to findings and trials", [
        ("r", [B(["Readings", "from the evidence ledger"])]),
        ("r", [B(["Mini-grid observers", "dispatch-3.2: necessary", "or candidate running;", "the fuel balance"],
                 tag="kept: observe factors"),
               B(["Cold and EV observers", "excursions, backup", "starts, interruptions"], tag="kept")], [0, 0]),
        ("r", [B(["Finding rules", "one episode per site, mechanism, asset;",
                  "a claim ceiling; next-step text"], tag="re-keyed: conditions on factors")], [[0, 1]]),
        ("r", [B(["Fuel money ranges", "extra fuel cost and", "unexplained fuel per", "night: modelled"],
                 tag="kept: at-stake bounds"),
               B(["One recommendation", "reserve −5 points,", "fixed; it predicts", "no saving"],
                 tag="must change: sole option")], [0, 0]),
        ("r", [B(["Trial and verdict", "frozen plan and", "comparability; reserve", "trial: guardrails"], tag="kept"),
               B(["Cost check", "modelled fuel cost per", "kWh; credited only", "when verified"], tag="reworked")],
         [1, 1]),
        ("r", [B(["Verification rules", "the change's own cost set to 0; positive",
                  "evidence simulated or authored; SYSTEM actor"], tag="must change")], [[0, 1]]),
        ("x",),
        ("r", [B(["What-ifs beside the chain", "productive load: energy × authored tariff,",
                  "gross sales; stop setting not calculated"], tag="reworked: option calculations")]),
        ("n", "No step re-computes an outcome under a choice."),
    ])
    l4 = panel("Layer 4: from factors to a plan and proof", [
        ("r", [B(["Leaf factors observed", "today's observers + commercial records"], cls="bxa")]),
        ("r", [B(["Structure evaluated upward", f"contribution: plan {n0(KP['contribution'])}, "
                  f"actual {n0(KA['contribution'])}"], cls="bxa")]),
        ("r", [B(["Attention on factors (Findings)", f"candidate +{n0(KA['candidate_l'])} L, "
                  f"unexplained +{n0(KA['unexplained_l'])} L"], cls="bxa")]),
        ("r", [B(["Decision on candidate litres", "options are factor changes, valued",
                  f"against no action ({n0(KA['contribution'])} a month)"], cls="bxa")]),
        ("r", [B(["Lower stop threshold", f"−{n0(so['params']['avoided_candidate_l'])} L diesel,",
                  f"+{n0(so['params']['added_throughput_kwh'])} kWh battery",
                  f"→ {m2(KA['contribution'] + so['monthly_or_horizon_change'])} a month"], cls="bxa"),
               B(["Reserve −5 points", "dawn charge below 35%",
                  f"on {n0(rs['params']['dawn_days_below_35pct'])} of 61 days:", "rejected by a bound"], cls="bxa")],
         [0, 0]),
        ("r", [B(["Plan within budget and crews", "approved by a named person"], cls="bxa")], [0]),
        ("r", [B(["Action carries the chosen option", "frozen prediction on the same factors"], cls="bxa")]),
        ("r", [B(["Three verdicts", "it happened · the money followed, net ·", "the action caused it"], cls="bxa")]),
        ("n", f"Stop threshold: {m2(so['value'])} over 12 months, net of its\n{m2(so['operator_one_off'])} one-off; "
              "design-world values, a design value\nuntil replay K runs."),
    ])
    return figure("Figure 0.2. How it is processed: from readings to proof (Kobo's generator decision, demo values)",
                  "Left, today: readings, observers (kept), Finding rules (re-keyed), modelled fuel money ranges "
                  "(kept as at-stake bounds), one fixed reserve recommendation that predicts no saving (must change: "
                  "the sole option), a trial with an operational verdict (kept), a modelled cost check credited only "
                  "when verified (reworked), verification rules with the change's cost at 0, simulated or authored "
                  "positive evidence and a SYSTEM actor (must change), and what-ifs beside the chain (reworked). "
                  "Right, Layer 4: observed leaf factors, the structure evaluated upward, Findings on factors, a "
                  "decision whose options are valued against no action, the reserve change rejected by the dawn "
                  "bound, one approved plan, an Action and three verdicts.", today, l4)


def fig_presentation():
    today = panel("Today: what the screens show", [
        ("r", [B(["Rail and Portfolio tabs", "Portfolio · Sites · Findings · Actions ·",
                  "Evidence · Financials; six Portfolio tabs"], tag="kept: no new menu")]),
        ("x",),
        ("r", [B(["Grow card", "estimated income,", "summed across sites"], tag="reworked"),
               B(["Optimize card", "possible extra fuel", "cost; mini-grid:", "the window's last day"],
                 tag="must change")]),
        ("x",),
        ("r", [B(["Protect card", "counts and fuel", "lines, per site"], tag="reworked"),
               B(["Assure card", "targets; verified", "results, listed"], tag="reworked")]),
        ("x",),
        ("r", [B(["Site outcome board", "what drives it · issues · what can be done",
                  "· in hand · earlier · must not harm"], tag="extended: the first factor view")]),
        ("x",),
        ("r", [B(["Act first", "Findings in placement groups: where to", "look first, never a value ranking"],
                 tag="reworked: the plan; placement kept")]),
        ("x",),
        ("r", [B(["Outcomes by site", "a status per site and outcome; row", "nodes computed but mostly not shown"],
                 tag="reworked: the factor view")]),
        ("x",),
        ("r", [B(["Finding page", "Overview · Analysis · Evidence ·", "Alternatives · Recommendation · History"],
                 tag="kept as the drill-down")]),
    ])
    l4 = panel("Layer 4: the same frame, organised by the movers", [
        ("r", [B(["Rail and tab frame", "unchanged; tabs in the loop's order"], cls="bxa")]),
        ("x",),
        ("r", [B(["Overview", "each outcome against plan, the factors", "moving it, the plan's first three moves"],
                 cls="bxa")]),
        ("x",),
        ("r", [B(["Site board and Outcomes by site · Kobo",
                  f"Contribution {n0(KP['contribution'])} → {n0(KA['contribution'])}",
                  f"Candidate running {m2(-(KA['candidate_l'] - KP['candidate_l']) * KA['diesel_price'])} · "
                  f"Unexplained fuel {m2(-(KA['unexplained_l'] - KP['unexplained_l']) * KA['diesel_price'])}",
                  f"Necessary running {m2(-(KA['necessary_l'] - KP['necessary_l']) * KA['diesel_price'])} · "
                  f"kWh billed +{m2((KA['billed_kwh'] - KP['billed_kwh']) * KA['tariff'])}",
                  "Emulated, with simulated telemetry"], cls="bxa")]),
        ("x",),
        ("r", [B(["Act first", "the plan within budget", "and crew visits"], cls="bxa"),
               B(["What changed", "Actions, frozen", "predictions, verdicts"], cls="bxa")]),
        ("x",),
        ("r", [B(["Decision page (drill-down)", "options with no action, value, who pays,",
                  "the bound or rule that rejected one"], cls="bxa")]),
        ("x",),
        ("r", [B(["A depot charging its own fleet", "revenue: not applicable;",
                  "cost per departure met"], cls="bxa")]),
        ("n", "Every figure carries its evidence class in words.\nHeadings name business content, never a question."),
    ])
    return figure("Figure 0.3. How it is presented: the same frame, different contents",
                  "Left, today: the rail and six Portfolio tabs (kept); four outcome cards of different kinds, an "
                  "estimated income total, a possible extra fuel cost that for mini-grid is the window's last day "
                  "(must change), counts and targets (the others reworked); the site outcome board with what drives "
                  "it, issues, what can be done, in hand, earlier and must not harm (extended into the first factor "
                  "view); Act first as Findings in placement groups and Outcomes by site as statuses (reworked); the "
                  "Finding page (kept). Right, Layer 4: the same frame; each outcome against plan with its factors "
                  "(Kobo's contribution and its four factor effects, labelled Emulated), the plan, Actions and "
                  "verdicts, a decision page, and a fleet operator's depot with revenue not applicable.", today, l4)


FIGURES = {"motivation-data": fig_data, "motivation-processing": fig_processing,
           "motivation-presentation": fig_presentation}

CSS = ('figure.dg{margin:16px 0;padding:12px;background:var(--card);border:1px solid var(--line);border-radius:6px}'
       'figure.dg svg{display:block;width:100%;height:auto}figure.dg svg.narrow{display:none;max-width:520px;margin:0 auto}\n'
       '@media (max-width:999px){figure.dg svg.wide{display:none}figure.dg svg.narrow{display:block}figure.dg{padding:6px}}\n'
       'figcaption{color:var(--muted);font-size:13px;margin-top:6px}\n'
       'svg .bx{fill:var(--card);stroke:var(--muted);stroke-width:1.2}svg .bxa{fill:var(--acard);stroke:var(--accent);stroke-width:1.4}'
       'svg .bxp{fill:var(--pcard);stroke:var(--muted);stroke-width:1.2;stroke-dasharray:5 4}\n'
       'svg .t{fill:var(--fg)}svg .lb{fill:var(--muted)}svg .tg{fill:var(--accent);font-style:italic}'
       'svg .ar{fill:none;stroke:var(--muted);stroke-width:1.5}svg .mk{fill:var(--muted)}svg .div{stroke:var(--line);stroke-width:1.5}\n')
