"""Render uiux-guide.md to uiux-guide.html (a small Markdown subset: headings, paragraphs, lists, tables, code blocks,
inline code, bold, italic, links). Usage: python3 render_guide.py [uiux-guide.md] [uiux-guide.html]"""
import html, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / 'uiux-guide.md'
OUT = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / 'uiux-guide.html'

CSS = """:root{--bg:#f3f5f9;--surface:#fff;--text:#17243b;--text-2:#566479;--line:#e3e8ef;--accent:#1d4ed8;--code:#eef1f6}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0e131b;--surface:#151b25;--text:#e5eaf1;--text-2:#a2adbd;--line:#283243;--accent:#8cb0ff;--code:#1a212d}}
:root[data-theme=dark]{--bg:#0e131b;--surface:#151b25;--text:#e5eaf1;--text-2:#a2adbd;--line:#283243;--accent:#8cb0ff;--code:#1a212d}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.6 Inter,system-ui,-apple-system,"Segoe UI",sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:24px 16px 80px}h1{font-size:28px;line-height:1.25}
h2{margin-top:44px;padding-top:12px;border-top:1px solid var(--line);font-size:21px}h3{margin-top:28px;font-size:17px}
a{color:var(--accent)}code{background:var(--code);padding:1px 4px;border-radius:4px;font-size:.88em;overflow-wrap:anywhere}
pre{background:var(--surface);border:1px solid var(--line);padding:12px;border-radius:8px;overflow-x:auto;line-height:1.25}
pre code{background:none;padding:0;font-size:12.5px;font-family:ui-monospace,"DejaVu Sans Mono",Menlo,monospace}
.tw{overflow-x:auto;margin:12px 0;border:1px solid var(--line);border-radius:8px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:13.5px}th,td{text-align:left;vertical-align:top;padding:8px 10px;border-bottom:1px solid var(--line)}
th{background:var(--code);font-weight:600}hr{border:0;border-top:1px solid var(--line);margin:32px 0}
.toc{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:12px 16px;margin:20px 0}.toc ul{margin:6px 0;padding-left:18px}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}"""


def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![\w*])\*([^*\s][^*]*)\*(?!\w)', r'<em>\1</em>', t)
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', t)


def slug(t):
    return 's-' + re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')


def render(md):
    out, toc, lines, i = [], [], md.split('\n'), 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith('```'):
            j = i + 1
            while not lines[j].startswith('```'):
                j += 1
            out.append('<pre><code>' + html.escape('\n'.join(lines[i + 1:j])) + '</code></pre>'); i = j + 1; continue
        m = re.match(r'(#{1,4}) (.*)', ln)
        if m:
            n, t = len(m.group(1)), m.group(2); s = slug(t)
            if n == 2: toc.append((t, s))
            out.append(f'<h{n} id="{s}">{inline(t)}</h{n}>'); i += 1; continue
        if ln.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
            head, body = rows[0], [r for r in rows[1:] if not re.match(r'^:?-+:?$', r[0] or '-')]
            out.append('<div class="tw"><table><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in head) + '</tr></thead><tbody>'
                       + ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in body) + '</tbody></table></div>')
            continue
        if re.match(r'\s*(- |\d+\. )', ln):
            out.append(render_list(lines, i));
            while i < len(lines) and (re.match(r'\s*(- |\d+\. )', lines[i]) or (lines[i].startswith('  ') and lines[i].strip())):
                i += 1
            continue
        if ln.strip() == '---':
            out.append('<hr>'); i += 1; continue
        if not ln.strip():
            i += 1; continue
        para = [ln]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'(#|\||```|\s*- |\s*\d+\. |---)', lines[i]):
            para.append(lines[i]); i += 1
        out.append('<p>' + inline(' '.join(para)) + '</p>')
    return out, toc


def render_list(lines, i):
    """Nested lists by indentation (2 or 3 spaces per level); continuation lines join the previous item."""
    items = []
    while i < len(lines) and (re.match(r'\s*(- |\d+\. )', lines[i]) or (lines[i].startswith('  ') and lines[i].strip())):
        m = re.match(r'(\s*)(- |\d+\. )(.*)', lines[i])
        if m: items.append([len(m.group(1)), 'ol' if m.group(2)[0].isdigit() else 'ul', m.group(3), m.group(2).rstrip('. ')])
        else: items[-1][2] += ' ' + lines[i].strip()
        i += 1
    html_, stack = '', []
    for ind, kind, text, num in items:
        while stack and stack[-1][0] > ind:
            html_ += f'</li></{stack.pop()[1]}>'
        if not stack or stack[-1][0] < ind:
            stack.append((ind, kind)); start = f' start="{num}"' if kind == 'ol' and num != '1' else ''; html_ += f'<{kind}{start}><li>{inline(text)}'
        else:
            html_ += f'</li><li>{inline(text)}'
    while stack:
        html_ += f'</li></{stack.pop()[1]}>'
    return html_


body, toc = render(SRC.read_text(encoding='utf-8'))
toc_html = '<nav class="toc" aria-label="Contents"><strong>Contents</strong><ul>' + ''.join(f'<li><a href="#{s}">{inline(t)}</a></li>' for t, s in toc) + '</ul></nav>'
body.insert(2, toc_html)
OUT.write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
               f'<title>AssetOps UI/UX guide</title><style>{CSS}</style></head><body><main class="wrap">' + '\n'.join(body)
               + '<p style="color:var(--text-2);font-size:13px">Rendered from uiux-guide.md by render_guide.py.</p></main></body></html>\n', encoding='utf-8')
print('wrote', OUT)
