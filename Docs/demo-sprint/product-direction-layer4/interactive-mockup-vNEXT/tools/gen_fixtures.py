"""Generate fixtures.js from the Layer 4 demo manifest (single source of figures).
Run: python3 tools/gen_fixtures.py   (from the interactive-mockup-vNEXT folder; strips the private oracle block)"""
import json, pathlib, yaml, datetime, hashlib
here = pathlib.Path(__file__).resolve().parent.parent
src = here.parent / 'demo-site-scenario-manifest.yaml'
raw = src.read_bytes()
data = yaml.safe_load(raw)
# The expectation oracle is private (manifest rule R1): never ship it in the mock-up bundle.
data.pop('oracle', None)
def conv(o):
    if isinstance(o, (datetime.date, datetime.datetime)): return o.isoformat()
    raise TypeError(type(o))
body = json.dumps(data, default=conv, ensure_ascii=False, separators=(',', ':'))

# ---- Structure evaluator (owner ninth message): every computed figure on screen comes from ../derived-values.json ----
import subprocess, sys
subprocess.run([sys.executable, str(here.parent / 'evaluate_structure.py')], check=True, cwd=str(here.parent), capture_output=True)
derived = json.loads((here.parent / 'derived-values.json').read_text(encoding='utf-8'))
# Report any figure where the evaluator and the manifest's stated field differ (expected: none).
diffs = []
for ten in data['tenants']:
    for s in ten['sites']:
        dv = derived['sites'].get(f"{ten['tenant']}/{s['site']}")
        if not dv: continue
        for side in ('plan', 'actual'):
            if dv[side].get('status') != 'evaluated': continue
            P = s['period'][side]
            for node, field in (('contribution', 'contribution'), ('revenue', 'revenue'), ('fuel_cost', 'diesel_cost'), ('energy', 'energy'), ('energy_cost', 'energy_cost'), ('cost_to_serve', 'total')):
                if node in dv[side]['nodes'] and field in P and abs(dv[side]['nodes'][node] - P[field]) > 0.005:
                    diffs.append(f"{s['site']} {side} {field}: stated {P[field]} derived {dv[side]['nodes'][node]}")
# Rev 12 (M5): the diff also covers option protect values, restore dates, option crew visits and plan crew visits, so it
# cannot report 0 differences while the checker fails on one of them.
def _opts(o):
    if isinstance(o, dict):
        if isinstance(o.get('id'), str) and o['id'] in derived['options']: yield o
        for v in o.values(): yield from _opts(v)
    elif isinstance(o, list):
        for v in o: yield from _opts(v)
_seen = set()
for o in _opts(data['tenants']):
    d = derived['options'][o['id']]
    if o['id'] in _seen: continue
    _seen.add(o['id'])
    if o.get('restore_by') and d.get('restore_date') and str(o['restore_by']) != d['restore_date']:
        diffs.append(f"{o['id']} restore: stated {o['restore_by']} derived {d['restore_date']}")
    if o.get('crew_visits') is not None and d.get('crew_visits') is not None and o['crew_visits'] != d['crew_visits']:
        diffs.append(f"{o['id']} crew visits: stated {o['crew_visits']} derived {d['crew_visits']}")
    if o.get('expected_penalties') is not None and d.get('monthly_or_horizon_change') is not None and abs(o['expected_penalties'] + d['monthly_or_horizon_change']) > 0.005:
        diffs.append(f"{o['id']} penalties: stated {o['expected_penalties']} derived {-d['monthly_or_horizon_change']}")
for ten in data['tenants']:
    for pe in (ten.get('portfolio') or {}).get('protect_effects') or []:
        for oid, v in (pe.get('options') or {}).items():
            d = derived['options'].get(oid)
            if d and isinstance(v, (int, float)) and pe['measure'] in (d.get('protect') or {}) and abs(d['protect'][pe['measure']] - v) > 0.005:
                diffs.append(f"{oid} protect {pe['measure']}: stated {v} derived {d['protect'][pe['measure']]}")
    A = ((ten.get('portfolio') or {}).get('allocation') or {})
    P = derived['plans'].get(ten['tenant'], {}).get('default', {})
    used = A.get('crew_visits_used', A.get('technician_visits_used'))
    if used is not None and P.get('crew_visits_used') is not None and used != P['crew_visits_used']:
        diffs.append(f"{ten['tenant']} plan crew visits used: stated {used} derived {P['crew_visits_used']}")
    C = ten.get('portfolio_constraints') or {}
    lim = C.get('crew_visits_nov', C.get('technician_visits_nov'))
    if lim is not None and P.get('crew_visits_limit') is not None and lim != P['crew_visits_limit']:
        diffs.append(f"{ten['tenant']} plan crew visit limit: stated {lim} derived {P['crew_visits_limit']}")
print('evaluator vs stated fields: %d differences' % len(diffs) + (': ' + '; '.join(diffs) if diffs else ''))


# ---- Replay-dependent values (rev 8, R7-L1): derived from the manifest, used by the design-value tagger ----
# Rule: options carrying forward_replay / replay / design_value -> their forward_replay quantities, their result
# economics (net, saving, bill, gross, revenue, fuel), their sensitivities; the allocation values, switch-case values and
# downsides of any tenant whose valued options include such an option; protect_effects flagged design_value.
# Quoted one-off costs are not replay-dependent. Money below $50 is not pattern-matched (it collides with unrelated
# unit prices such as $12 a kW); such figures sit in rows already tagged. Small litre values that collide with an
# observed litre quantity are matched only in "avoided" phrasing.
import re
def money(v):
    return '\\$' + (f'{v:,.0f}' if float(v).is_integer() else f'{v:,.2f}').replace(',', ',') + '(?![\\d,])'
def ints(v): return f'{int(v):,}'
observed_l = set()
for ten in data['tenants']:
    for s in ten['sites']:
        for b in s.get('period', {}).get('bridge', []) or []:
            m = re.match(r'([\d,]+) L x', str(b.get('basis', '')))
            if m: observed_l.add(int(m.group(1).replace(',', '')))
        fb = s.get('period', {}).get('fuel_balance') or {}
        for k in ('residual_l',): 
            if k in fb: observed_l.add(int(fb[k]))
pats, vals = [], []
def add(p, v): 
    if p not in pats: pats.append(p); vals.append(v)
for ten in data['tenants']:
    replay_tenant = False
    for s in ten['sites']:
        opts = (s.get('decision') or {}).get('options', []) + ((s.get('entitlement') or {}).get('options', []) if isinstance(s.get('entitlement'), dict) else [])
        for o in opts:
            if not any(k in o for k in ('forward_replay', 'replay', 'design_value')): continue
            if o.get('disposition') == 'RECOMMENDED': replay_tenant = True
            fr = o.get('forward_replay', {})
            for k, v in fr.items():
                if k.endswith('_l') and k != 'constrained_candidate_l':
                    if int(v) in observed_l: add(rf'(?:avoid(?:s|ed)?|remov(?:es|ed))(?: only)? {ints(v)} L|{ints(v)} L avoided', f'{v} L (avoided phrasing)')
                    else: add(rf'(?<![\d,]){ints(v)} L\b', f'{v} L')
                if k in ('kwh_from_battery_or_genset', 'added_battery_throughput_kwh'): add(rf'(?<![\d,]){ints(v)} kWh', f'{ints(v)} kWh')
                if k == 'soc_0500_below_35_days': add(rf'{61 - int(v)} of 61|{int(v)} of 61', f'{v} of 61 days')
            if 'replay' in o:
                m = re.match(r'(\d+) of (\d+)', o['replay'])
                if m: add(rf'{m.group(1)} of {m.group(2)}', m.group(0) + ' nights')
                kw = re.search(r'about (\d+) kW', o['replay'])
                if kw: add(rf'(?<![\d,]){kw.group(1)} kW\b', f'{kw.group(1)} kW')
                if 'deliverable_kwh' in o: add(rf'(?<![\d,]){ints(o["deliverable_kwh"])} kWh', f'{ints(o["deliverable_kwh"])} kWh')
            e = o.get('economics', {}) or {}
            for k in ('net_12m', 'net_monthly', 'saving_monthly', 'energy_cost_monthly', 'gross_monthly', 'fuel_monthly'):
                if k in e and abs(e[k]) >= 50: add(money(abs(e[k])), e[k])
            for v in (o.get('sensitivity') or {}).values():
                if abs(v) >= 50: add(money(abs(v)), v)
    # Plan values: every derived plan case (default, switch cases, sensitivities) whose valued options include a replay-dependent option.
    rids = {o['id'] for s in ten['sites'] for o in ((s.get('decision') or {}).get('options', []) + ((s.get('entitlement') or {}).get('options', []) if isinstance(s.get('entitlement'), dict) else [])) if any(k in o for k in ('forward_replay', 'replay', 'design_value'))}
    rids |= {oid for oid, e in derived['options'].items() if e.get('design_values')}
    plan = derived['plans'].get(ten['tenant'])
    if plan:
        for c in [plan['default']] + list(plan['switch_cases'].values()) + list(plan['sensitivity_values'].values()):
            if set(c['valued_options']) & rids and c['value'] >= 50: add(money(c['value']), c['value'])
    for pe in ten['portfolio'].get('protect_effects', []):
        if pe.get('design_value'):
            for v in pe['options'].values():
                if isinstance(v, (int, float)) and v >= 10: add(rf'(?<![\d,.]){ints(v)} ' + pe['measure'].replace('_', ' '), f'{ints(v)} ' + pe['measure'].replace('_', ' '))

sha = hashlib.sha256(raw).hexdigest()[:12]
(here / 'fixtures.js').write_text(
    "/* GENERATED by tools/gen_fixtures.py from ../demo-site-scenario-manifest.yaml (sha256 " + sha + "). Do not edit by hand.\n"
    "   Every figure on the Layer 4 screens is read from MANIFEST or derived by stated arithmetic (see fixture-mapping.md). */\n"
    "const MANIFEST = " + body + ";\nconst MANIFEST_SHA = '" + sha + "';\n"
    "/* Replay-dependent values derived from the manifest (rule above in tools/gen_fixtures.py) */\n"
    "const DERIVED = " + json.dumps(derived, ensure_ascii=False, separators=(',', ':')) + "; /* from ../evaluate_structure.py */\n"
    "const REPLAY_PATTERNS = " + json.dumps(pats) + ";\nconst REPLAY_VALUES = " + json.dumps([str(v) for v in vals]) + ";\n")
print('replay patterns', len(pats))
print('fixtures.js written', len(body), 'chars, sha', sha)
