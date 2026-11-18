"""Render layer4-transformation-design.md to its HTML twin (mermaid diagrams drawn client-side from the jsDelivr CDN).

Usage: python3 render_design_html.py layer4-transformation-design.md layer4-transformation-design.html
Reproduces the twin that was previously rendered by hand-run tooling outside the repository (rev 4 of the transition
document added this script so the twin can be rebuilt and checked: rendering the committed .md must give the committed
.html byte for byte)."""
import html, re, sys

SRC, OUT = sys.argv[1], sys.argv[2]

HEAD = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Layer 4 Design</title><style>:root{--bg:#f6f7f9;--fg:#18212f;--muted:#5d6878;--line:#dfe3ea;--card:#fff;--accent:#1d4ed8;--code:#eef1f5}\n'
        '@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#11161d;--fg:#e4e8ee;--muted:#9aa5b4;--line:#2a3340;--card:#171d26;--accent:#7aa2f7;--code:#1f2733}}\n'
        ':root[data-theme=dark]{--bg:#11161d;--fg:#e4e8ee;--muted:#9aa5b4;--line:#2a3340;--card:#171d26;--accent:#7aa2f7;--code:#1f2733}\n'
        'body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}\n'
        '.wrap{max-width:1040px;margin:0 auto;padding:24px 16px 80px}h1{font-size:28px;line-height:1.25}h2{margin-top:44px;padding-top:12px;border-top:1px solid var(--line)}h3{margin-top:28px}\n'
        'a{color:var(--accent)}code{background:var(--code);padding:1px 4px;border-radius:3px;font-size:.88em;overflow-wrap:anywhere}pre{background:var(--code);padding:12px;border-radius:6px;overflow-x:auto}pre code{background:none;padding:0}\n'
        'pre.mermaid{background:var(--card);border:1px solid var(--line);text-align:center}\n'
        '.tw{overflow-x:auto;margin:12px 0;border:1px solid var(--line);border-radius:6px;background:var(--card)}table{border-collapse:collapse;width:100%;font-size:13.5px}th,td{text-align:left;vertical-align:top;padding:7px 9px;border-bottom:1px solid var(--line)}th{background:var(--code);font-weight:600}\n'
        'blockquote{margin:16px 0;padding:10px 14px;border-left:4px solid var(--accent);background:var(--card)}hr{border:0;border-top:1px solid var(--line);margin:32px 0}\n'
        '.toc{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:12px 16px;margin:20px 0}.toc ul{margin:6px 0;padding-left:18px}.toc .l3{margin-left:16px;font-size:.93em}\n'
        ':focus-visible{outline:2px solid var(--accent);outline-offset:2px}</style></head><body><main class="wrap">')
FOOT = ('<p style="color:var(--muted);font-size:13px">Rendered from layer4-transformation-design.md. Diagrams render with Mermaid from the '
        'jsDelivr CDN; offline, the diagram source is shown.</p></main>\n'
        '<script type="module">import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.esm.min.mjs";'
        'const dark=matchMedia("(prefers-color-scheme: dark)").matches;mermaid.initialize({startOnLoad:true,theme:dark?"dark":"default",securityLevel:"strict"});'
        '</script></body></html>')


def slug(t):
    t = re.sub(r"<[^>]+>", "", t).lower()
    t = re.sub(r"[^\w\s-]", " ", t)
    return re.sub(r"[\s_-]+", "-", t).strip("-")


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
body, toc, i = [], [], 0
while i < len(lines):
    ln = lines[i]
    if ln.startswith("```"):
        lang = ln[3:].strip(); i += 1; code = []
        while not lines[i].startswith("```"):
            code.append(lines[i]); i += 1
        i += 1
        txt = html.escape("\n".join(code), quote=False)
        body.append(f'<pre class="mermaid">{txt}</pre>' if lang == "mermaid" else f"<pre><code>{txt}</code></pre>")
        continue
    m = re.match(r"^(#{1,6}) (.*)", ln)
    if m:
        lvl, txt = len(m.group(1)), m.group(2)
        sid = slug(txt)
        body.append(f'<h{lvl} id="{sid}">{inline(txt)}</h{lvl}>' if lvl <= 3 else f'<h{lvl}>{inline(txt)}</h{lvl}>')
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
    para = [ln]; i += 1
    while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||> |- |\d+\. |```|---)", lines[i]):
        para.append(lines[i]); i += 1
    body.append(f"<p>{inline(' '.join(para))}</p>")

tochtml = '<nav class="toc" aria-label="Contents"><strong>Contents</strong><ul>' + "".join(
    f'<li class="l{l}"><a href="#{s}">{t}</a></li>' for l, s, t in toc) + "</ul></nav>"
body.insert(next(k for k, x in enumerate(body) if x.startswith("<h2")), tochtml)
page = HEAD + "".join(body) + FOOT
# the pack index row links the sibling rendered page (the .md has no link syntax in this subset)
page = page.replace("<td><code>product-transition-and-roadmap.md</code> + <code>.html</code>",
                    '<td><a href="product-transition-and-roadmap.html"><code>product-transition-and-roadmap.md</code> + <code>.html</code></a>', 1)
open(OUT, "w", encoding="utf-8").write(page)
print("ok", OUT)
