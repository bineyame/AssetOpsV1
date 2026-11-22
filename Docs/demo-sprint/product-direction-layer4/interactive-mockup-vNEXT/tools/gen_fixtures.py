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


# ---- Source-dependent values (0K4m, spec §4): derived from the manifest's replay_studies and source: / information:
# entries, and the evaluator's replay_sources; used by the Simulated-chip tagger. Each figure maps to the study it rests on.
# Rule: an option rests on a study when a param carries `source:` or the option carries `information.source`, or its
# evaluated output lists replay_sources. Its figures are its evaluated value, monthly change and sensitivities (null ones
# are not shown, D-0K4.48). A plan case's value rests on the studies of its valued options. Money below $50 is not
# pattern-matched (it collides with unrelated unit prices); figures stated as information are chipped where they render.
import re, copy
def money(v):
    return '\\$' + (f'{v:,.0f}' if float(v).is_integer() else f'{v:,.2f}') + '(?![\\d,])'
studies = {k for k, v in (data.get('replay_studies') or {}).items() if isinstance(v, dict) and v.get('days')}
opt_src = {}
for oid, ev in ((data.get('evaluation') or {}).get('options') or {}).items():
    st = {v['source']['study'] for v in (ev.get('params') or {}).values() if isinstance(v, dict) and isinstance(v.get('source'), dict)}
    if isinstance((ev.get('information') or {}).get('source'), dict): st.add(ev['information']['source']['study'])
    if st: opt_src[oid] = st
for oid, d in derived['options'].items():
    if d.get('replay_sources'): opt_src.setdefault(oid, set()).update(d['replay_sources'])
opt_src = {k: sorted(v & studies) for k, v in opt_src.items() if v & studies}
pats, labels = [], []
def add(v, st):
    if v is None or abs(v) < 50: return
    p = money(abs(v))
    if p not in pats: pats.append(p); labels.append(st)
for oid in sorted(opt_src):
    d, st = derived['options'][oid], opt_src[oid][0]
    if d.get('value') is None: continue
    add(d['value'], st); add(d.get('monthly_or_horizon_change'), st)
    for v in (d.get('sensitivities') or {}).values(): add(v.get('value') if isinstance(v, dict) else v, st)
for plan in derived['plans'].values():
    for c in [plan['default']] + list(plan['switch_cases'].values()) + list(plan['sensitivity_values'].values()):
        st = sorted({s for o in c.get('valued_options', []) for s in opt_src.get(o, [])})
        if st and c.get('value') is not None: add(c['value'], st[0])
# Kobo's verification line (D-0K4.55): the matched days, read from the leading integers of verification_plan; kept outside
# the MANIFEST literal so K11's parse-back of that literal is untouched.
verify = {}
for ten in data['tenants']:
    for s in ten['sites']:
        vp = (s.get('decision') or {}).get('verification_plan')
        if vp:
            n = lambda t: int(re.match(r'\s*(\d+)', str(t or '')).group(1)) if re.match(r'\s*(\d+)', str(t or '')) else None
            verify[s['site']] = {'matched_days': n(vp.get('baseline')), 'after_days': n(vp.get('after'))}

sha = hashlib.sha256(raw).hexdigest()[:12]
(here / 'fixtures.js').write_text(
    "/* GENERATED by tools/gen_fixtures.py from ../demo-site-scenario-manifest.yaml (sha256 " + sha + "). Do not edit by hand.\n"
    "   Every figure on the Layer 4 screens is read from MANIFEST or derived by stated arithmetic (see fixture-mapping.md). */\n"
    "const MANIFEST = " + body + ";\nconst MANIFEST_SHA = '" + sha + "';\n"
    "/* Source-dependent values derived from the manifest (rule above in tools/gen_fixtures.py) */\n"
    "const DERIVED = " + json.dumps(derived, ensure_ascii=False, separators=(',', ':')) + "; /* from ../evaluate_structure.py */\n"
    "const SOURCE_PATTERNS = " + json.dumps(pats) + ";\nconst SOURCE_LABELS = " + json.dumps(labels) + ";\n"
    "const VERIFY = " + json.dumps(verify) + ";\n")
print('source patterns', len(pats))
print('fixtures.js written', len(body), 'chars, sha', sha)
