"""Independent derivation of the source-dependent figures, for tools/audit.mjs (0K4m, spec §4; was rev 8, R7-L1).
Reads ../demo-site-scenario-manifest.yaml and ../derived-values.json directly; does NOT read fixtures.js, the tagger's list
or tools/gen_fixtures.py. Prints JSON {"patterns": [...regex sources...], "figures": [...]} to stdout.
Rule: an option rests on a study when one of its `evaluation.options.<id>.params` carries `source: {study: ...}` or the
option carries `information: {source: {study: ...}}`, and that study is declared in `replay_studies` with its `days`.
Its displayed figures are its evaluated `value`, its monthly change and its non-null sensitivities. A plan case's value
rests on a study when one of its valued options does. Figures that are not available (null) are never searched. Money under
$50 is not searched (it collides with unrelated unit prices); information figures are chipped where they render."""
import json, pathlib, sys
import yaml

root = pathlib.Path(__file__).resolve().parents[2]
doc = yaml.safe_load((root / 'demo-site-scenario-manifest.yaml').read_text(encoding='utf-8'))
dv = json.loads((root / 'derived-values.json').read_text(encoding='utf-8'))

declared = {sid for sid, st in (doc.get('replay_studies') or {}).items() if isinstance(st, dict) and st.get('days')}
resting = set()
for oid, ev in ((doc.get('evaluation') or {}).get('options') or {}).items():
    uses = [p['source'].get('study') for p in (ev.get('params') or {}).values() if isinstance(p, dict) and isinstance(p.get('source'), dict)]
    info = ev.get('information') or {}
    if isinstance(info.get('source'), dict): uses.append(info['source'].get('study'))
    if any(u in declared for u in uses): resting.add(oid)

out = {}
def put(v):
    if v is None or isinstance(v, bool) or abs(v) < 50: return
    a = abs(v)
    text = f'{a:,.0f}' if float(a).is_integer() else f'{a:,.2f}'
    out.setdefault('\\$' + text + '(?![\\d,])', v)

for oid in sorted(resting):
    o = dv['options'].get(oid) or {}
    if o.get('value') is None: continue
    put(o['value']); put(o.get('monthly_or_horizon_change'))
    for s in (o.get('sensitivities') or {}).values(): put(s.get('value') if isinstance(s, dict) else s)
for plan in dv['plans'].values():
    for case in [plan['default'], *plan['switch_cases'].values(), *plan['sensitivity_values'].values()]:
        if case.get('value') is not None and set(case.get('valued_options') or []) & resting: put(case['value'])

json.dump({'patterns': list(out.keys()), 'figures': [str(v) for v in out.values()]}, sys.stdout)
