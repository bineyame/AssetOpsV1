"""compare2.py old.json new.json : evidence format of batches 02-04 (app.panels[].h/rows/columns/chips/links/details, header, tabRows...)."""
import json, sys, re

UUID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.I)
CODE = re.compile(r'\b[A-Z]{2,}(?:_[A-Z0-9]+)+\b')


def load(path):
    t = open(path, encoding='utf-8', errors='replace').read().replace('�', '·')
    return json.loads(t)


UU = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.I)


def nu(x):
    return UU.sub('<uuid>', json.dumps(x))


def key(p):
    return (p['screen'], p.get('case'), p['viewport'].split('x')[0])


def vocab(a):
    out = []
    for t in list(a['titles']) + [c for x in a['panels'] for c in (x.get('chips') or [])] + [(a.get('h1') or {}).get('text', '')]:
        if isinstance(t, str) and (UUID.search(t) or CODE.search(t)):
            out.append(t[:80])
    return out


def tabs(a):
    return [t['items'] for t in a.get('tabRows', [])]


def diff(o, n):
    d = []
    if o['titles'] != n['titles']:
        d.append(f"titles {o['titles']} -> {n['titles']}")
    op = {x['title']: x for x in o['panels']}
    for x in n['panels']:
        y = op.get(x['title'])
        if not y:
            continue
        t = x['title']
        if abs(y['h'] - x['h']) > max(8, 0.1 * y['h']):
            d.append(f"[{t}] height {y['h']}->{x['h']}")
        for f in ('rows', 'links', 'details', 'buttons', 'tables'):
            if y.get(f) != x.get(f):
                d.append(f"[{t}] {f} {y.get(f)}->{x.get(f)}")
        if y.get('columns') != x.get('columns'):
            d.append(f"[{t}] columns {y.get('columns')}->{x.get('columns')}")
        if y.get('chips') != x.get('chips'):
            d.append(f"[{t}] chips {(y.get('chips') or [])[:6]}->{(x.get('chips') or [])[:6]}")
    if o['overflowX'] != n['overflowX']:
        d.append(f"overflowX {o['overflowX']}->{n['overflowX']}")
    oh, nh = o.get('header') or {}, n.get('header') or {}
    if abs((oh.get('h') or 0) - (nh.get('h') or 0)) > 6:
        d.append(f"header h {oh.get('h')}->{nh.get('h')}")
    a, b = o.get('h1') or {}, n.get('h1') or {}
    for f in ('text', 'size', 'family', 'weight', 'color'):
        if a.get(f) != b.get(f):
            d.append(f"h1.{f} {a.get(f)!r}->{b.get(f)!r}")
    if abs((a.get('top') or 0) - (b.get('top') or 0)) > 8:
        d.append(f"h1.top {a.get('top')}->{b.get('top')}")
    of, nf = o.get('fonts') or {}, n.get('fonts') or {}
    for k in ('prose', 'h2', 'td', 'th', 'body'):
        p, q = of.get(k), nf.get(k)
        if p and q:
            for f in ('size', 'family', 'weight', 'color'):
                if p.get(f) != q.get(f):
                    d.append(f"{k}.{f} {p.get(f)}->{q.get(f)}")
        elif bool(p) != bool(q):
            d.append(f"{k} presence {bool(p)}->{bool(q)}")
    if of.get('proseSizes') != nf.get('proseSizes'):
        d.append(f"proseSizes {of.get('proseSizes')}->{nf.get('proseSizes')}")
    if o.get('pSizes') != n.get('pSizes'):
        d.append(f"pSizes {o.get('pSizes')}->{n.get('pSizes')}")
    if tabs(o) != tabs(n):
        d.append(f"tabRows {tabs(o)}->{tabs(n)}")
    if abs(o['pageH'] - n['pageH']) > 0.1 * o['pageH']:
        d.append(f"pageH {o['pageH']}->{n['pageH']}")
    if nu(o.get('clipped')) != nu(n.get('clipped')):
        d.append(f"clipped {str(o.get('clipped'))[:120]}->{str(n.get('clipped'))[:120]}")
    if json.dumps(o.get('hscroll')) != json.dumps(n.get('hscroll')):
        d.append(f"hscroll {str(o.get('hscroll'))[:150]}->{str(n.get('hscroll'))[:150]}")
    if o.get('consoleErrors') != n.get('consoleErrors'):
        d.append(f"consoleErrors {str(o.get('consoleErrors'))[:100]}->{str(n.get('consoleErrors'))[:100]}")
    if abs((o.get('mainTop') or 0) - (n.get('mainTop') or 0)) > 8:
        d.append(f"mainTop {o.get('mainTop')}->{n.get('mainTop')}")
    return d


def main(oldp, newp):
    old = {key(p): p for p in load(oldp)['pairs']}
    res = []
    for p in load(newp)['pairs']:
        k = key(p)
        q = old.get(k)
        na = p['app']
        r = {'screen': p['screen'], 'case': p.get('case'), 'width': k[2], 'new_app_titles': na['titles'],
             'mock_titles': p['mock']['titles'], 'vocab_new': vocab(na), 'overflowX': na['overflowX'],
             'app_image': p['app_image'], 'mock_image': p['mock_image'], 'app_url': p['app_url']}
        mh = {x['title']: x['h'] for x in p['mock']['panels']}
        newr = {x['title']: round(x['h'] / mh[x['title']], 2) for x in na['panels'] if mh.get(x['title'])}
        r['ratios_over_1.3'] = [(t, v) for t, v in newr.items() if v > 1.3]
        if not q:
            r['gap'] = 'no original pair'
            res.append(r)
            continue
        oa = q['app']
        r['app_diffs'] = diff(oa, na)
        r['mock_diffs'] = diff(q['mock'], p['mock'])
        r['old_app_titles'] = oa['titles']
        r['vocab_old'] = vocab(oa)
        omh = {x['title']: x['h'] for x in q['mock']['panels']}
        oldr = {x['title']: round(x['h'] / omh[x['title']], 2) for x in oa['panels'] if omh.get(x['title'])}
        r['ratio_worse'] = [(t, oldr.get(t), v) for t, v in newr.items() if v > 1.3 and v > oldr.get(t, 1.0) + 0.1]
        sig = []
        oh, nh = oa.get('h1') or {}, na.get('h1') or {}
        if oh.get('text') != nh.get('text'):
            sig.append('h1 text changed')
        if p['viewport'].startswith('390') and (oa.get('header') or {}).get('h', 0) - (na.get('header') or {}).get('h', 0) >= 20:
            sig.append('390 header band shorter')
        if (oa.get('pSizes') or {}).get('14px', 0) > (na.get('pSizes') or {}).get('14px', 0):
            sig.append('14px prose reduced')
        if tabs(oa) != tabs(na):
            sig.append('tab rows changed')
        if oa.get('hscroll') and len(na.get('hscroll') or []) < len(oa['hscroll']):
            sig.append('fewer horizontal scrollers')
        for t, v in oldr.items():
            if v > 1.3 and newr.get(t, v) < v - 0.1:
                sig.append(f'{t} ratio {v}->{newr.get(t)}')
        opn = {x['title']: x for x in oa['panels']}
        for x in na['panels']:
            y = opn.get(x['title'])
            if y and y.get('columns') != x.get('columns'):
                sig.append(f"[{x['title']}] table columns changed")
        if oa['titles'] != na['titles'] and set(oa['titles']) != set(na['titles']):
            sig.append('panel set changed')
        r['fix_signals'] = sig
        rg = []
        if na['overflowX'] > 0 and oa['overflowX'] <= 0:
            rg.append('new horizontal overflow')
        if set(r['vocab_new']) - set(r['vocab_old']):
            rg.append('new raw vocabulary: ' + str(sorted(set(r['vocab_new']) - set(r['vocab_old']))[:3]))
        if r['ratio_worse']:
            rg.append('cap exceeded ' + str(r['ratio_worse']))
        if na.get('clipped') and nu(na['clipped']) != nu(oa.get('clipped')):
            rg.append('clipped text changed: ' + str(na['clipped'])[:100])
        if na.get('consoleErrors') and na['consoleErrors'] != oa.get('consoleErrors'):
            rg.append('console errors: ' + str(na['consoleErrors'])[:100])
        if r['mock_diffs']:
            rg.append('mock measure changed')
        r['regress'] = rg
        r['review_panel_set'] = oa['titles'] != na['titles']
        res.append(r)
    return res


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(main(sys.argv[1], sys.argv[2]), indent=1, ensure_ascii=False))
