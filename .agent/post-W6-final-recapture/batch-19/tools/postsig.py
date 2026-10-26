"""postsig.py (batch 19): second pass over cmp-*.json.
(1) clears 'clipped text changed' when the clipped cells are the same (class, text) as the frozen capture (pixel-only sh/ch/sw change);
(2) checks every closed panel against the ruled absolute WR caps (.agent/post-W6-W6-caps-rulings.md rulings 1-2);
(3) adds fix signals for frozen D3 rows B19-03/05/06/07/08/10/13/15 (register R364/R366/R367/R368/R370/R372/R373, Q18) that are measurably gone;
(4) flags new raw codes / UUIDs in the visible main text and any unfocusable scroller from the probe."""
import json, glob, re
OLD = '../../post-W6-audit/batch-19'
CAPS = {'Work done': (600, 800), 'Lifecycle': (500, 250), 'History': (650, 690), 'Maintenance record · activity': (700, 900)}
UU = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
CODE = re.compile(r'\b[A-Z]{2,}(?:_[A-Z0-9]+)+\b')
REFUSAL = re.compile(r'Work request unavailable\.')
viol = []
for f in sorted(glob.glob('cmp-*.json')):
    part = f[4:-5]
    new = {(p['screen'], p['case'], p['viewport'].split('x')[0]): p for p in json.load(open(f'part-{part}/evidence.json'))['pairs']}
    old = {(p['screen'], p['case'], p['viewport'].split('x')[0]): p for p in json.load(open(f'{OLD}/part-{part}/evidence.json'))['pairs']}
    probe = {(x['id'], x['case'], str(x['width'])): x for x in json.load(open(f'logs/probe-scrollers-{part}.json'))}
    tg = json.load(open(f'tools/targets-{part}.json'))
    res = json.load(open(f))
    for r in res:
        k = (r['screen'], r['case'], str(r['width']))
        n, o = new[k]['app'], old[k]['app']
        nt, ot = n['extra']['mainText'], o['extra']['mainText']
        opn = any(t['id'] == k[0] and t['case'] == k[1] and t.get('openAll') for t in tg)
        r['open_all'] = opn
        heights = {x['title']: x['h'] for x in n['panels']}
        r['panel_heights'] = heights
        w = 0 if k[2] == '1440' else 1
        over = [(t, h, CAPS[t][w]) for t, h in heights.items() if t in CAPS and h > CAPS[t][w] and not opn]
        r['over_ruled_cap'] = over
        if over: viol.append((part, k, over))
        keep, cleared = [], []
        sigc = lambda l: sorted((c.get('cls'), c.get('text', '')[:40]) for c in (l or []))
        for x in r['regress']:
            if x.startswith('cap exceeded'):
                if over: keep.append('closed panel over ruled cap: ' + str(over))
                else: cleared.append('within ruled absolute cap (' + x[:80] + ')')
            elif x.startswith('clipped text changed') and sigc(n.get('clipped')) == sigc(o.get('clipped')):
                cleared.append('same clipped cells as the frozen capture (pixel-only sh/ch change); designed clamp with its Full ... text disclosure')
            else:
                keep.append(x)
        newcodes = sorted(set(CODE.findall(nt)) - set(CODE.findall(ot)))
        if newcodes: keep.append('new raw code in visible text: ' + str(newcodes[:4]))
        pr = probe.get(k)
        unf = [s for s in (pr['scrollers'] if pr else []) if not (s['focusable'] or s['inner'])]
        r['probe_scrollers'] = pr['scrollers'] if pr else None
        if unf: keep.append('unfocusable scroller: ' + str(unf)[:200])
        if pr is None: keep.append('scroller probe missing')
        r['regress'] = keep; r['cleared'] = cleared
        sig = [s for s in r.get('fix_signals', []) if s not in ('fewer horizontal scrollers', 'panel set changed')]
        if any(h.get('cls') == 'site-tabs__list' for h in (o.get('hscroll') or [])) and not any(h.get('cls') == 'site-tabs__list' for h in (n.get('hscroll') or [])):
            sig.append('390 tab row wraps; History tab no longer cut (B19-03, R364)')
        if o['titles'] and not n['titles'] and REFUSAL.search(nt):
            if 'forbidden-principal' in k[1] or k[1] == 'ev-forbidden-403':
                sig.append("W5 forbidden principal now refused 'No access to this Site's work.' (B19-15, R373)")
            sig.append('refusal: header + one refusal, no empty shell panels (B19-07, R367)')
            if 'Reload' in o['extra']['buttons'] and 'Reload' not in n['extra']['buttons']:
                sig.append('false Reload gone on non-503 refusal (B19-07)')
        if any('validateDOMNesting' in e for e in (o.get('consoleErrors') or [])) and not n.get('consoleErrors'):
            sig.append('validateDOMNesting console warning gone (B19-08, R368)')
        if ('EV_CONNECTOR' in ot and 'EV_CONNECTOR' not in nt) or ('· GENERATOR' in ot and '· GENERATOR' not in nt):
            sig.append('raw asset label code · TYPE gone (B19-06, Q18)')
        if len(UU.findall(ot)) > len(UU.findall(nt)):
            sig.append('record UUID out of History text, Stored record ID disclosure (B19-05, R366)')
        if re.search(r'Action [0-9a-f]{8}', ot) and re.search(r'ACT-\d+', nt):
            sig.append('Action label uses ACT- code (B19-05, R366)')
        if re.search(r'Historical as of [^U]*\d\d:\d\d UTC', ot) and re.search(r'Historical as of [^U]*\d\d:\d\d:\d\d UTC', nt):
            sig.append('historical date bar shows seconds (B19-13, R372)')
        if re.search(r'Event \S+ · meaning not established', ot) and not re.search(r'Event \S+ · meaning not established', nt):
            sig.append('raw event fall-through gone (B19-10, R370)')
        r['fix_signals'] = sig
    json.dump(res, open(f, 'w'), indent=1)
    print(part, len(res), sum(1 for r in res if r['regress']), 'open;', sum(1 for r in res if r['fix_signals']), 'fix')
print('over-cap', viol)
