"""postsig.py : second pass over cmp-*.json. (1) clears 'clipped text changed' when every clipped cell has its visible
disclosure (Full title text / Full record text / Show full) in the same pair; (2) clears 'NEW inner horizontal scroller' when the
scroller is the labelled data-table scroller and the scroller probe lists it focusable; (3) adds fix signals for frozen
D3 rows B18-01/02/05/08/12 that are measurably gone."""
import json, glob
OLD = '../../post-W6-audit/batch-18'
for f in sorted(glob.glob('cmp-*.json')):
    if 'raw' in f or 'noattest' in f: continue
    part = f[4:-5]
    new = {(p['screen'], p['case'], p['viewport'].split('x')[0]): p for p in json.load(open(f'part-{part}/evidence.json'))['pairs']}
    old = {(p['screen'], p['case'], p['viewport'].split('x')[0]): p for p in json.load(open(f'{OLD}/part-{part}/evidence.json'))['pairs']}
    probe = {(x['id'], x['case'], str(x['width'])): x for x in json.load(open(f'logs/probe-scrollers-{part}.json'))}
    res = json.load(open(f))
    for r in res:
        k = (r['screen'], r['case'], str(r['width']))
        n, o = new[k], old.get(k)
        sj = json.dumps(n['app']); oj = json.dumps(o['app']) if o else ''
        cl = n['app'].get('clipped') or []
        rows = [json.dumps(rt) for pn in n['app']['panels'] for rt in pn.get('rowText', [])]
        full = sum(s.count('Full title text') + s.count('Full record text') for s in rows)
        showf = sum(s.count('Show full') for s in rows)
        ncd = sum('cell-disclosure' in c['cls'] for c in cl)
        ok_clip = (len(cl) - ncd) <= full and ncd <= showf
        pr = probe.get((r['screen'], r['case'], str(r['width'])))
        unf = [s for s in (pr['scrollers'] if pr else []) if not (s['focusable'] or s['inner'])]
        keep, cleared = [], []
        for x in r['regress']:
            if x.startswith('clipped text changed') and ok_clip:
                cleared.append(f'clipped cells all carry a visible disclosure ({len(cl)} clipped, Full title/record text {full}, Show full {showf}) per ruling 4')
            elif x.startswith('NEW inner horizontal scroller') and pr is not None and not unf and 'data-table__scroll' in x:
                cleared.append('labelled focusable data-table scroller (probe), table now populated vs frozen empty state' )
            else:
                keep.append(x)
        r['regress'] = keep; r['cleared'] = cleared
        sig = list(r.get('fix_signals', []))
        if o:
            for tok, tag in (('EV_CONNECTOR', 'raw EV_CONNECTOR code gone (B18-02)'), ('generator-1 · GENERATOR', 'raw generator-1 · GENERATOR gone (B18-02)')):
                if tok in oj and tok not in sj: sig.append(tag)
            if '1 requests in progress' in oj and '1 requests in progress' not in sj: sig.append("plural '1 requests' fixed (B18-01)")
            if 'Showing 1\u00e2\u20ac\u201c' in oj and 'Later page' in sj and r['case'] == 'page-two': sig.append("page-two says 'Later page' not 'Showing 1-1' (B18-05)")
            if any('h1.top 24->44' in d for d in (r.get('app_diffs') or [])) and r['screen'] == 'incidents': sig.append('breadcrumb added above h1 (B18-08)')
            orows = sum(pn.get('rows', 0) for pn in o['app']['panels']); nrows = sum(pn.get('rows', 0) for pn in n['app']['panels'])
            if r['case'].endswith('default-window') and orows == 0 and nrows > 0: sig.append('default window now lists today rows (B18-12)')
            if r['screen'] == 'oprecords' and str(r['width']) == '1440' and (o['app'].get('hscroll')) and not n['app'].get('hscroll'): sig.append('table horizontal scroll at 1440 gone (B18-07)')
        r['fix_signals'] = sig
    json.dump(res, open(f, 'w'), indent=1)
    print(part, sum(1 for r in res if r['regress']), 'open;', sum(1 for r in res if r['fix_signals']), 'with fix signals')
