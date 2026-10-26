"""build_batch.py NN : read batch-NN/cmp-*.json (+ original batch json) -> batch-NN.json, batch-NN.md.
Optional batch-NN/notes.json: {"screen|case|width" or "screen|case": {"class":..., "why":...}, "_md": "extra text"}"""
import json, sys, glob, os

nn = sys.argv[1]
root = 'C:/Users/assef/Bineyame/AssetOpsV1-plan2/.agent'
base = f'{root}/post-W6-final-recapture/batch-{nn}'
orig = json.load(open(f'{root}/post-W6-audit/batch-{nn}/batch-{nn}.json'))
op = {(p['screen'], p['case'], str(p['width'])): p for p in orig['pairs']}
notes = json.load(open(f'{base}/notes.json')) if os.path.exists(f'{base}/notes.json') else {}
sha = open(f'{base}/sha.txt').read().strip()
pairs = []
counts = {}
for f in sorted(glob.glob(f'{base}/cmp-*.json')):
    part = os.path.basename(f)[4:-5]
    for r in json.load(open(f)):
        k = (r['screen'], r['case'], r['width'])
        o = op.get(k, {})
        if 'gap' in r:
            cls, why = 'GAP', r['gap']
        elif r['regress'] and all(x.startswith('cap exceeded') for x in r['regress']) and notes.get(f"{k[0]}|*cap"):
            n = notes[f"{k[0]}|*cap"]
            cls = 'FIXED' if r['fix_signals'] else 'PASS'
            why = n['why'] + ('; ' + '; '.join(r['fix_signals']) if r['fix_signals'] else '')
        elif r['regress']:
            cls, why = 'REGRESSION-OPEN', '; '.join(r['regress'])
        elif r['fix_signals']:
            cls, why = 'FIXED', '; '.join(r['fix_signals'])
        else:
            cls, why = 'PASS', 'no measured difference from the frozen capture beyond standing/ruled rows'
        ov = notes.get(f'{k[0]}|{k[1]}|{k[2]}') or notes.get(f'{k[0]}|{k[1]}')
        if ov:
            cls, why = ov['class'], ov['why']
        counts[cls] = counts.get(cls, 0) + 1
        pairs.append({'screen': k[0], 'case': k[1], 'width': k[2], 'part': part, 'route': o.get('route'),
                      'producer': o.get('producer'), 'sha': sha, 'classification': cls, 'reason': why,
                      'frozen_findings': o.get('findings'), 'app_titles': r.get('new_app_titles'),
                      'mock_titles': r.get('mock_titles'), 'ratios_over_1.3': r.get('ratios_over_1.3'),
                      'overflowX': r['overflowX'], 'vocab': r['vocab_new'], 'app_diffs_vs_frozen': r.get('app_diffs'),
                      'app_image': f"{part}/{r.get('app_image')}", 'mock_image': f"{part}/{r.get('mock_image')}"})
out = {'batch': nn, 'name': orig['name'], 'main_sha': sha, 'pair_count': len(pairs),
       'frozen_pair_count': orig['pair_count'], 'counts': counts, 'pairs': pairs}
json.dump(out, open(f'{base}/batch-{nn}.json', 'w'), indent=1)
md = [f"# Final recapture batch {nn}: {orig['name']}", '',
      f"Main SHA {sha}. Pairs {len(pairs)} (frozen {orig['pair_count']}). Counts: " +
      ', '.join(f'{k} {v}' for k, v in sorted(counts.items())), '',
      'Method: original capture tool and producers (unmodified), same ports, fresh DBs; each pair compared with the frozen '
      'evidence (panel titles, heights, rows, columns, links, chips, typography, overflow, header band, tab-row scroll, caps) '
      'and the frozen mock (unchanged). Classification derived from measured deltas plus register/rulings; standing '
      'D1/D2/D4 rows and ruled caps count as PASS. FIXED = a measured signal that a frozen D3 difference is gone.', '']
for sec in ('REGRESSION-OPEN', 'GAP'):
    rows = [p for p in pairs if p['classification'] == sec]
    md.append(f'## {sec} ({len(rows)})')
    for p in rows:
        md.append(f"- {p['screen']} / {p['case']} / {p['width']}: {p['reason']} (evidence {p['app_image']})")
    if not rows:
        md.append('- none')
    md.append('')
if notes.get('_md'):
    md += [notes['_md'], '']
md += ['## All pairs', '| Screen | Case | Width | Class | Why |', '|---|---|---|---|---|']
for p in pairs:
    md.append(f"| {p['screen']} | {p['case']} | {p['width']} | {p['classification']} | {p['reason'][:160]} |")
open(f'{base}/batch-{nn}.md', 'w').write('\n'.join(md) + '\n')
print(nn, counts)
