"""postcap.py : annotate cmp-*.json; resolves 'cap exceeded' (ratio vs frozen) against the ruled absolute closed-panel caps
(.agent/post-W6-W6-caps-rulings.md ruling 2: 1440/390) and records Show-full / Full-title disclosure evidence for clipped cells."""
import json, glob, os
CAPS = {'Incident cases': (700, 800), 'Case boundaries': (150, 150), 'Corrective work requests': (700, 800),
        'Preventive plan': (600, 690), 'Operational records': (650, 780), 'Record a manual reading': (400, 600),
        'How records are used': (400, 300)}
viol = []
for f in sorted(glob.glob('cmp-*.json')):
    if 'noattest' in f or f.endswith('.raw.json'): continue
    part = f[4:-5]
    ev = json.load(open(f'part-{part}/evidence.json'))
    pm = {(p['screen'], p['case'], p['viewport'].split('x')[0]): p for p in ev['pairs']}
    res = json.load(open(f))
    for r in res:
        p = pm[(r['screen'], r['case'], str(r['width']))]
        opn = any(t.get('case') == r['case'] and t.get('openAll') for t in json.load(open(f'targets-{part}.json')))
        r['open_all'] = opn
        heights = {x['title']: x['h'] for x in p['app']['panels']}
        r['panel_heights'] = heights
        w = 0 if str(r['width']) == '1440' else 1
        over = [(t, h, CAPS[t][w]) for t, h in heights.items() if t in CAPS and h > CAPS[t][w] and not opn]
        r['over_ruled_cap'] = over
        rg = []
        for x in r.get('regress', []):
            if x.startswith('cap exceeded'):
                if over: rg.append('closed panel over ruled cap: ' + str(over))
                continue
            rg.append(x)
        r['regress_raw'] = r.get('regress', [])
        r['regress'] = rg
        if over: viol.append((part, r['screen'], r['case'], r['width'], over))
        # clipped disclosure evidence
        r['clipped_cells'] = [(c.get('cls'), c.get('text', '')[:40]) for c in (p['app'].get('clipped') or [])]
    json.dump(res, open(f, 'w'), indent=1)
print('over-cap violations:', len(viol))
for v in viol: print(v)
