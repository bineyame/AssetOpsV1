"""Independent derivation of the replay-dependent figures, for tools/audit.mjs (rev 8, R7-L1).
Reads ../demo-site-scenario-manifest.yaml directly; does NOT read fixtures.js or the tagger's list.
Prints JSON {"patterns": [...regex sources...], "figures": [...]} to stdout.
Rule (main design §5, OE-6): an option is replay-dependent when it carries forward_replay, replay or design_value.
Its displayed results are: forward-replay quantities (litres avoided or added, battery or generator kWh, dawn days of the
replayed window), result economics (net, saving, monthly bill, gross, fuel; revenue is a tariff × load input, not a replay result), deliverable energy and the peak kW stated by the replay and sensitivities. Plan values
are replay-dependent when a recommended option is: modelled 12-month change, switch-case values, downsides.
protect_effects with design_value are replay-dependent. One-off quoted costs are not. Money under $50 and bare
integers under 10 are not searched (they collide with unrelated prices and counts)."""
import json, pathlib, re, sys
import yaml

root = pathlib.Path(__file__).resolve().parents[2]
doc = yaml.safe_load((root / 'demo-site-scenario-manifest.yaml').read_text(encoding='utf-8'))
doc.pop('oracle', None)
import copy
# Rev 13: manifest strings carry {fig:path} / {rec:path} placeholders (spec §7); render them before reading figures from text.
def _get(root, path):
    o = root
    for m in re.finditer(r'\[([^\]]+)\]|([^.\[\]]+)', path):
        k = m.group(1) if m.group(1) is not None else m.group(2)
        if isinstance(o, list): o = o[int(k)] if k.isdigit() else next((x for x in o if isinstance(x, dict) and k in (x.get('tenant'), x.get('site'), x.get('id'), x.get('driver'), x.get('measure'), x.get('batch'))), None)
        elif isinstance(o, dict): o = o.get(k)
        else: return None
    return o
def _fmt(v, neg):
    if isinstance(v, bool) or v is None: return 'not available'
    if isinstance(v, (int, float)):
        x = -v if neg else v
        return ('−' if x < 0 else '') + (f"{abs(x):,.0f}" if abs(x - round(x)) < 1e-9 else f"{abs(x):,.2f}")
    if hasattr(v, 'isoformat'): v = v.isoformat()
    if isinstance(v, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', v):
        y, mo, d = v.split('-'); return f"{int(d)} {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][int(mo)-1]}"
    return str(v)
def _render_all(o, man, der):
    if isinstance(o, dict):
        for k, v in o.items(): o[k] = _render_all(v, man, der)
    elif isinstance(o, list):
        for i, v in enumerate(o): o[i] = _render_all(v, man, der)
    elif isinstance(o, str) and '{' in o:
        return re.sub(r'\{(fig|rec):(-?)([^{}]+)\}', lambda m: _fmt(_get(der if m.group(1) == 'fig' else man, m.group(3)), bool(m.group(2))), o)
    return o
_der = json.loads((root / 'derived-values.json').read_text(encoding='utf-8'))
doc = _render_all(copy.deepcopy(doc), copy.deepcopy(doc), _der)

def fmt_money(x):
    x = abs(float(x))
    s = f'{x:,.0f}' if x == int(x) else f'{x:,.2f}'
    return re.escape('$' + s) + r'(?![\d,])'

def walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o, list):
        for v in o: yield from walk(v)

litres_seen = {int(m.group(1).replace(',', '')) for d in walk(doc) if isinstance(d.get('basis'), str)
               for m in [re.match(r'([\d,]+) L x', d['basis'])] if m}
litres_seen |= {int(d['residual_l']) for d in walk(doc) if 'residual_l' in d}

out = {}
def put(pattern, figure): out.setdefault(pattern, figure)

for tenant in doc['tenants']:
    recommended_replay = False
    for d in walk(tenant.get('sites', [])):
        if 'id' not in d or not ({'forward_replay', 'replay', 'design_value'} & set(d)):
            continue
        recommended_replay |= d.get('disposition') == 'RECOMMENDED'
        for key, val in (d.get('forward_replay') or {}).items():
            if key in ('avoidable_fuel_l', 'extra_fuel_l'):
                n = f'{int(val):,}'
                put(rf'(?:avoid(?:s|ed)?|remov(?:es|ed))(?: only)? {n} L|{n} L avoided' if int(val) in litres_seen else rf'(?<![\d,]){n} L\b', f'{n} L')
            elif key in ('kwh_from_battery_or_genset', 'added_battery_throughput_kwh'):
                put(rf'(?<![\d,]){int(val):,} kWh', f'{int(val):,} kWh')
            elif key == 'soc_0500_below_35_days':
                put(rf'{int(val)} of 61|{61 - int(val)} of 61', f'{int(val)} of 61 dawn days')
        if isinstance(d.get('replay'), str):
            m = re.match(r'(\d+ of \d+)', d['replay'])
            if m: put(re.escape(m.group(1)), m.group(1) + ' nights')
            k = re.search(r'about (\d+) kW', d['replay'])
            if k: put(rf'(?<![\d,]){k.group(1)} kW\b', f'{k.group(1)} kW')
            if 'deliverable_kwh' in d: put(rf'(?<![\d,]){int(d["deliverable_kwh"]):,} kWh', f'{int(d["deliverable_kwh"]):,} kWh')
        econ = d.get('economics') or {}
        for key in ('net_12m', 'net_monthly', 'saving_monthly', 'energy_cost_monthly', 'gross_monthly', 'fuel_monthly'):
            if key in econ and abs(econ[key]) >= 50: put(fmt_money(econ[key]), econ[key])
        for val in (d.get('sensitivity') or {}).values():
            if abs(val) >= 50: put(fmt_money(val), val)
    # rev 10: plan values are replay-dependent when the plan case they come from contains a replay-dependent valued option; the
    # cases and their option lists come from the structure evaluator's output (derived-values.json), not from the screen tagger.
    dv = json.loads((root / 'derived-values.json').read_text(encoding='utf-8'))
    replay_ids = {d['id'] for d in walk(doc['tenants']) if 'id' in d and ({'forward_replay', 'replay', 'design_value'} & set(d))}
    replay_ids |= {o for o, e in dv['options'].items() if e.get('design_values')}
    pl = dv['plans'].get(tenant['tenant'])
    if pl:
        cases = [pl['default']] + list(pl['switch_cases'].values())
        for c in cases:
            if c.get('value') is not None and set(c['valued_options']) & replay_ids and c['value'] >= 50: put(fmt_money(c['value']), c['value'])
        for sv in pl['sensitivity_values'].values():
            if sv.get('value') is not None and set(sv['valued_options']) & replay_ids and sv['value'] >= 50: put(fmt_money(sv['value']), sv['value'])
    for pe in tenant['portfolio'].get('protect_effects', []):
        if pe.get('design_value'):
            for v in pe['options'].values():
                if isinstance(v, (int, float)) and v >= 10: put(rf'(?<![\d,.]){int(v):,} ' + re.escape(pe['measure'].replace('_', ' ')), f'{int(v):,} ' + pe['measure'].replace('_', ' '))

json.dump({'patterns': list(out.keys()), 'figures': [str(v) for v in out.values()]}, sys.stdout)
