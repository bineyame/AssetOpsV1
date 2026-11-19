"""Render commercial-plan.md to its HTML twin, after checking every computed commercial table (plan F #9, rev 2).

Usage: python3 render_commercial_plan_html.py commercial-plan.md commercial-plan.html
       python3 render_commercial_plan_html.py --tables commercial-plan.md   -> print the computed tables, for pasting

Recreated with the document on 19 Nov 2026 (plan F: renderers kept, adapted to the new files). Two source layers (plan F, P4):
product claims come from the design and are checked by check_alignment.py and check_manifest.py; commercial and owner-time
figures come from the owner's decisions and the planning assumptions stated in the document, and are checked here.

Checks, run before writing (the build stops on the first failure, SystemExit):
- inputs are parsed from the .md itself: the <!--table:assumptions--> and <!--table:effort--> blocks; nothing is hand-copied;
- every other <!--table:NAME--> block (owner-month, durations, cost, fee-guide) must equal the table recomputed from those
  inputs, cell for cell;
- the five stage names of the engagement path (D1) appear in this document and in website-content.md;
- every demonstration figure anchored to a commercial-record node (contribution, revenue, collected, outstanding, billed kWh)
  sits on a line that says Emulated (D14);
- rendering is deterministic: the same .md gives the same .html byte for byte.
The page is plain HTML with the design twin's theme tokens; mermaid blocks render client-side from the jsDelivr CDN."""
import html, pathlib, re, sys

STAGES = ["Initial call", "Deep-dive with process owners", "Integration pack and pilot timeline", "Pilot and monitoring", "SaaS"]
WEEKS_MONTH = 4.33


def fail(msg):
    raise SystemExit(f"CHECK FAILED: {msg}")


# ---------------------------------------------------------------- table blocks
def blocks(md):
    out = {}
    for m in re.finditer(r"<!--table:([\w-]+)-->\n(.*?)\n<!--/table-->", md, re.S):
        out[m.group(1)] = m.group(2).strip("\n")
    return out


def rows(tbl):
    ls = [l for l in tbl.split("\n") if l.startswith("|")]
    return [[c.strip() for c in l.strip().strip("|").split("|")] for l in ls[2:]]


def plain(s):
    return re.sub(r"[*`]", "", s).strip()


def num(s):
    return float(plain(s).replace(",", "").replace("−", "-").replace("+", "").rstrip("%"))


def g(x):
    x = round(x, 2)
    return f"{x:g}"


def money(x, sign=False):
    r = round(x)
    s = f"{abs(r):,.0f}"
    return (("+" if r >= 0 else "−") + s) if sign else s


def rng(s):
    a, b = plain(s).split("–")
    return num(a), num(b)


def inputs(bl):
    if "assumptions" not in bl or "effort" not in bl:
        fail("the assumptions and effort blocks are both required")
    A = {}
    for r in rows(bl["assumptions"]):
        A[plain(r[0])] = (num(r[1]), num(r[2]), num(r[3]))
    need = ["Owner-day value", "Second-person cost per day", "Agent and compute cost up to the pilot", "Agent and compute cost per pilot",
            "Working days per month", "Owner minutes, ordinary day", "Owner minutes, peak day", "Minutes in an owner-day",
            "Selling floor, initial calls a month", "Minutes per initial call", "Deep-dive, calendar minimum (weeks)",
            "Integration pack, calendar minimum (weeks)", "First view, calendar minimum (weeks)", "Deep-dive start (weeks from approval)",
            "Partner discount"]
    for k in need:
        if k not in A:
            fail(f"assumption '{k}' missing from the assumptions block")
    E = {}
    for r in rows(bl["effort"]):
        E[plain(r[0])] = (rng(r[1]), rng(r[2]))
    for k in ["Alignment", "Deep-dive, to the first view", "Deep-dive, the rest", "Integration pack", "Pilot, three months"]:
        if k not in E:
            fail(f"effort row '{k}' missing")
    return A, E


def mid(t):
    return (t[0] + t[1]) / 2


# ---------------------------------------------------------------- computed tables
CASES = [("planning case (both defaults)", 8, 2), ("no peak days", 0, 2), ("four-day product reserve", 8, 4), ("no peak days, four-day reserve", 0, 4)]


def month(A, peak):
    wd, base, pk, odm = A["Working days per month"][1], A["Owner minutes, ordinary day"][1], A["Owner minutes, peak day"][1], A["Minutes in an owner-day"][1]
    return ((wd - peak) * base + peak * pk) / odm


def limit(A, peak, reserve):
    calls = A["Selling floor, initial calls a month"][1] * A["Minutes per initial call"][1] / A["Minutes in an owner-day"][1]
    return month(A, peak) - reserve - calls


def t_owner_month(A, E):
    out = ["| Case | Peak days a month (C14) | Product reserve, owner-days (C15) | Owner-days a month | For commercial work | Delivery limit, after the selling floor |",
           "|---|---:|---:|---:|---:|---:|"]
    for n, pk, rv in CASES:
        m = month(A, pk)
        out.append(f"| {n} | {pk} | {rv} | {g(m)} | {g(m - rv)} | {g(limit(A, pk, rv))} |")
    return "\n".join(out)


def weeks(days, lim, floor):
    return max(round(days / lim * WEEKS_MONTH, 1), floor)


def durations(A, E, lim):
    dd_floor = A["Deep-dive, calendar minimum (weeks)"]
    out = {}
    for i, c in enumerate(("low", "mid", "high")):
        pick = (lambda t: t[0]) if c == "low" else (mid if c == "mid" else (lambda t: t[1]))
        to_view = pick(E["Deep-dive, to the first view"][0])
        dd = to_view + pick(E["Deep-dive, the rest"][0])
        pack = pick(E["Integration pack"][0])
        bd = weeks(to_view, lim, A["First view, calendar minimum (weeks)"][1])
        d = weeks(dd, lim, dd_floor[i])
        p = weeks(pack, lim, A["Integration pack, calendar minimum (weeks)"][1])
        out[c] = dict(bd=bd, dd=d, pack=p, tot=round(d + p, 1))
    return out


def t_durations(A, E):
    s0, s1 = A["Deep-dive start (weeks from approval)"][0], A["Deep-dive start (weeks from approval)"][2]
    out = ["| Case | Delivery limit | First view of their target against actual (weeks into the deep-dive) | Deep-dive and integration pack (weeks) | Commitment (weeks from approval) | First change proved |",
           "|---|---:|---:|---:|---|---|"]
    for n, pk, rv in CASES:
        lim = limit(A, pk, rv)
        D = durations(A, E, lim)
        c0, c1 = int(s0 + D["low"]["tot"] + 0.5), int(s1 + D["high"]["tot"] + 0.5)
        p0, p1 = (round(int(c + 2 * WEEKS_MONTH + 0.5) / WEEKS_MONTH) for c in (c0, c1))
        out.append(f"| {n} | {g(lim)} | {g(D['low']['bd'])}–{g(D['high']['bd'])} | {g(D['low']['tot'])}–{g(D['high']['tot'])} | weeks {c0}–{c1} | about M{p0}–M{p1} |")
    return "\n".join(out)


def costs(A, E):
    """Value cost (owner time at its value, the second person, agents) and cash cost, per effort case."""
    res = {}
    for i, c in enumerate(("low", "mid", "high")):
        pick = (lambda t: t[0]) if c == "low" else (mid if c == "mid" else (lambda t: t[1]))
        ov, sc = A["Owner-day value"][i], A["Second-person cost per day"][i]
        own_pre = sum(pick(E[k][0]) for k in ("Alignment", "Deep-dive, to the first view", "Deep-dive, the rest", "Integration pack"))
        sec_pre = sum(pick(E[k][1]) for k in ("Alignment", "Deep-dive, to the first view", "Deep-dive, the rest", "Integration pack"))
        own_p, sec_p = pick(E["Pilot, three months"][0]), pick(E["Pilot, three months"][1])
        ag_pre, ag_p = A["Agent and compute cost up to the pilot"][i], A["Agent and compute cost per pilot"][i]
        res[c] = dict(own_pre=own_pre, own_p=own_p, v_pre=own_pre * ov + sec_pre * sc + ag_pre, v_p=own_p * ov + sec_p * sc + ag_p,
                      c_pre=sec_pre * sc + ag_pre, c_p=sec_p * sc + ag_p)
        res[c]["v"] = res[c]["v_pre"] + res[c]["v_p"]
        res[c]["c"] = res[c]["c_pre"] + res[c]["c_p"]
    return res


def t_cost(A, E):
    C = costs(A, E)
    out = ["| Effort case | Owner-days up to the pilot | Owner-days in the pilot | Cost at value, up to the pilot | Cost at value, the pilot | Cost at value, whole engagement | Cash only, whole engagement |",
           "|---|---:|---:|---:|---:|---:|---:|"]
    for c in ("low", "mid", "high"):
        x = C[c]
        out.append(f"| {c} | {g(x['own_pre'])} | {g(x['own_p'])} | {money(x['v_pre'])} | {money(x['v_p'])} | {money(x['v'])} | {money(x['c'])} |")
    return "\n".join(out)


FEES = [("A. Modest", 5000), ("B. Middle", 10000), ("C. Covers a mid-effort engagement", 15000)]


def t_fee(A, E):
    C = costs(A, E)
    disc = A["Partner discount"][1] / 100
    out = ["| Option (internal, never published) | Pilot fee, three Sites | Margin at low cost | Margin at mid cost | Margin at high cost | Cash margin at high cost |",
           "|---|---:|---:|---:|---:|---:|"]
    for n, f in FEES + [("C for a design partner (C4)", 15000 * (1 - disc))]:
        out.append(f"| {n} | {money(f)} | {money(f - C['low']['v'], True)} | {money(f - C['mid']['v'], True)} | {money(f - C['high']['v'], True)} | {money(f - C['high']['c'], True)} |")
    return "\n".join(out)


COMPUTED = {"owner-month": t_owner_month, "durations": t_durations, "cost": t_cost, "fee-guide": t_fee}


def check_tables(md):
    bl = blocks(md)
    A, E = inputs(bl)
    n = 0
    for name, fn in COMPUTED.items():
        if name not in bl:
            fail(f"computed table '{name}' missing")
        want = fn(A, E)
        if bl[name] != want:
            fail(f"table '{name}' differs from the recomputation:\n--- document\n{bl[name]}\n--- recomputed\n{want}")
        n += 1
    unknown = set(bl) - set(COMPUTED) - {"assumptions", "effort"}
    if unknown:
        fail(f"table blocks with no computation: {sorted(unknown)}")
    return n, A, E


def check_stages(md, other):
    for s in STAGES:
        if s not in md:
            fail(f"stage name '{s}' missing from this document")
        if other is not None and s not in other:
            fail(f"stage name '{s}' missing from website-content.md")


COMMERCIAL_NODE = re.compile(r"<!--figx?:[^>]*\.nodes\.(?:contribution|revenue|collected|outstanding|billed_kwh)\b")


def check_emulated(md):
    for i, l in enumerate(md.split("\n"), 1):
        if COMMERCIAL_NODE.search(l) and "Emulated" not in l and "sites.harvest-cold" not in l and "sites.metro-bus" not in l:
            fail(f"line {i}: a figure from the demonstration world's commercial records without 'Emulated' (D14)")


# ---------------------------------------------------------------- markdown to HTML (shared with render_website_content_html.py)
HEAD = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>{title}</title><style>:root{{--bg:#f6f7f9;--fg:#18212f;--muted:#5d6878;--line:#dfe3ea;--card:#fff;--accent:#1d4ed8;--code:#eef1f5}}\n'
        '@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#11161d;--fg:#e4e8ee;--muted:#9aa5b4;--line:#2a3340;--card:#171d26;--accent:#7aa2f7;--code:#1f2733}}}}\n'
        ':root[data-theme=dark]{{--bg:#11161d;--fg:#e4e8ee;--muted:#9aa5b4;--line:#2a3340;--card:#171d26;--accent:#7aa2f7;--code:#1f2733}}\n'
        'body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}}\n'
        '.wrap{{max-width:1040px;margin:0 auto;padding:24px 16px 80px}}h1{{font-size:28px;line-height:1.25}}h2{{margin-top:44px;padding-top:12px;border-top:1px solid var(--line)}}h3{{margin-top:28px}}\n'
        'a{{color:var(--accent)}}code{{background:var(--code);padding:1px 4px;border-radius:3px;font-size:.88em;overflow-wrap:anywhere}}pre{{background:var(--code);padding:12px;border-radius:6px;overflow-x:auto}}pre code{{background:none;padding:0}}\n'
        'pre.mermaid{{background:var(--card);border:1px solid var(--line);text-align:center}}\n'
        '.tw{{overflow-x:auto;margin:12px 0;border:1px solid var(--line);border-radius:6px;background:var(--card)}}table{{border-collapse:collapse;width:100%;font-size:13.5px}}th,td{{text-align:left;vertical-align:top;padding:7px 9px;border-bottom:1px solid var(--line)}}th{{background:var(--code);font-weight:600}}td.n,th.n{{text-align:right;white-space:nowrap}}\n'
        'blockquote{{margin:12px 0;padding:8px 14px;border-left:4px solid var(--accent);background:var(--card)}}hr{{border:0;border-top:1px solid var(--line);margin:32px 0}}\n'
        '.toc{{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:12px 16px;margin:20px 0}}.toc ul{{margin:6px 0;padding-left:18px}}.toc .l3{{margin-left:16px;font-size:.93em}}\n'
        ':focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}</style></head><body><main class="wrap">')
FOOT = ('<p style="color:var(--muted);font-size:13px">Rendered from {src}. Diagrams render with Mermaid from the jsDelivr CDN; offline, '
        'the diagram source is shown.</p></main>\n'
        '<script type="module">import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.esm.min.mjs";'
        'const dark=matchMedia("(prefers-color-scheme: dark)").matches;mermaid.initialize({{startOnLoad:false,theme:dark?"dark":"default",securityLevel:"strict"}});'
        'await mermaid.run({{querySelector:"pre.mermaid"}});</script></body></html>\n')


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
            continue
        p = html.escape(p, quote=False)
        p = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', p)
        p = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", p)
        p = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", p)
        out.append(p)
    return "".join(out)


def cells(row):
    return [c.strip() for c in re.split(r"(?<!\\)\|", row.strip().strip("|"))]


def to_html(md, title, src):
    lines = md.split("\n")
    body, toc, i = [], [], 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            lang = ln[3:].strip()
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            txt = html.escape("\n".join(lines[i + 1:j]))
            body.append(f'<pre class="mermaid">{txt}</pre>' if lang == "mermaid" else f"<pre><code>{txt}</code></pre>")
            i = j + 1
            continue
        m = re.match(r"^(#{1,4}) (.*)$", ln)
        if m:
            lvl, t = len(m.group(1)), inline(m.group(2))
            sid = slug(t)
            if lvl in (2, 3):
                toc.append((lvl, sid, t))
            body.append(f'<h{lvl} id="{sid}">{t}</h{lvl}>')
            i += 1
            continue
        if ln.startswith("|"):
            tb = []
            while i < len(lines) and lines[i].startswith("|"):
                tb.append(lines[i])
                i += 1
            head, rest = cells(tb[0]), [cells(r) for r in tb[2:]]
            align = ["n" if re.search(r"-+:\s*$", c) else "" for c in cells(tb[1])] if len(tb) > 1 else []
            cl = lambda k: f' class="{align[k]}"' if k < len(align) and align[k] else ""  # noqa: E731
            h = "".join(f"<th{cl(k)}>{inline(c)}</th>" for k, c in enumerate(head))
            r = "".join("<tr>" + "".join(f"<td{cl(k)}>{inline(c)}</td>" for k, c in enumerate(row)) + "</tr>" for row in rest)
            body.append(f'<div class="tw"><table><thead><tr>{h}</tr></thead><tbody>{r}</tbody></table></div>')
            continue
        if ln.startswith(">"):
            q = []
            while i < len(lines) and lines[i].startswith(">"):
                q.append(lines[i][1:].strip())
                i += 1
            body.append(f"<blockquote><p>{inline(' '.join(q))}</p></blockquote>")
            continue
        if re.match(r"^\s*(?:[-*]|\d+\.) ", ln):
            ordered = bool(re.match(r"^\s*\d+\. ", ln))
            items = []
            while i < len(lines) and (re.match(r"^\s*(?:[-*]|\d+\.) ", lines[i]) or (lines[i].startswith("  ") and lines[i].strip())):
                if re.match(r"^\s*(?:[-*]|\d+\.) ", lines[i]):
                    items.append(re.sub(r"^\s*(?:[-*]|\d+\.) ", "", lines[i]))
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1
            tag = "ol" if ordered else "ul"
            body.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            continue
        if ln.strip() == "---":
            body.append("<hr>")
            i += 1
            continue
        if not ln.strip() or re.fullmatch(r"\s*<!--.*?-->\s*", ln):
            i += 1
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,4} |\||>|```|\s*(?:[-*]|\d+\.) )", lines[i]):
            para.append(lines[i])
            i += 1
        body.append(f"<p>{inline(' '.join(para))}</p>")
    tochtml = '<nav class="toc" aria-label="Contents"><strong>Contents</strong><ul>' + "".join(
        f'<li class="l{l}"><a href="#{s}">{t}</a></li>' for l, s, t in toc) + "</ul></nav>"
    if body and body[0].startswith("<h1"):
        body.insert(1, tochtml)
    return HEAD.format(title=html.escape(title)) + "\n".join(body) + FOOT.format(src=html.escape(src))


def main(argv):
    if argv and argv[0] == "--tables":
        md = pathlib.Path(argv[1]).read_text(encoding="utf-8")
        A, E = inputs(blocks(md))
        for name, fn in COMPUTED.items():
            print(f"<!--table:{name}-->\n{fn(A, E)}\n<!--/table-->\n")
        return 0
    src, out = pathlib.Path(argv[0]), pathlib.Path(argv[1])
    md = src.read_text(encoding="utf-8")
    other = src.parent / "website-content.md"
    n, _, _ = check_tables(md)
    check_stages(md, other.read_text(encoding="utf-8") if other.is_file() else None)
    check_emulated(md)
    page = to_html(md, "Commercial Approach", src.name)
    if to_html(md, "Commercial Approach", src.name) != page:
        fail("rendering is not deterministic")
    out.write_text(page, encoding="utf-8")
    print(f"ok: {n} computed tables match their inputs; stage names consistent; Emulated labels present; wrote {out.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
