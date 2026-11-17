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
    if recommended_replay:
        alloc = tenant['portfolio'].get('allocation', {})
        nums = [v for v in (alloc.get('modelled_12m_change') or {}).values() if isinstance(v, (int, float))]
        nums += [c['value'] for s in alloc.get('switches', []) for c in (s.get('cases') or {}).values()]
        dn = alloc.get('downside') or {}
        nums += [dn.get('value', 0)] + list((dn.get('others') or {}).values())
        for v in nums:
            if v >= 50: put(fmt_money(v), v)
    for pe in tenant['portfolio'].get('protect_effects', []):
        if pe.get('design_value'):
            for v in pe['options'].values():
                if isinstance(v, (int, float)) and v >= 10: put(rf'(?<![\d,.]){int(v):,} ' + re.escape(pe['measure'].replace('_', ' ')), f'{int(v):,} ' + pe['measure'].replace('_', ' '))

json.dump({'patterns': list(out.keys()), 'figures': [str(v) for v in out.values()]}, sys.stdout)
