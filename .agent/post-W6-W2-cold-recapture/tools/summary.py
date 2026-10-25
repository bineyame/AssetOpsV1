"""Count the r2 app captures per part and flag overflow, clipping or console errors (capture-only bookkeeping)."""
import json, glob, collections, pathlib
rows = []
for ev in sorted(pathlib.Path('.').glob('*/part-*/evidence.json')):
    d = json.loads(ev.read_text(encoding='utf8'))
    for p in d['pairs']:
        a = p['app']
        rows.append((ev.parts[0] + '/' + ev.parts[1], p['screen'], p['case'], p['viewport'].split('x')[0], a['overflowX'], len(a['clipped']), len(a.get('consoleErrors', [])), d.get('revision')))
c = collections.Counter((r[0], r[1]) for r in rows)
for k, v in sorted(c.items()): print(*k, v)
print('total', len(rows), 'revisions', sorted(set(str(r[7]) for r in rows)))
print('flags', [r for r in rows if r[4] or r[5] or r[6]])
