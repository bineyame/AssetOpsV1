"""Hand-typed figure scan (rev 12 M5; rev 13 L4 and M3).

Part A, screen code. Fails when a digit-bearing string literal in a loop-*.js file (quoted or template text, ${...}
removed) restates a figure the structure evaluator produces (../derived-values.json), formatted as the screen formats it:
  * money "$1,234" / "$1,234.50" for every evaluated number of at least 10;
  * a quantity with a unit ("1,050 kWh", "62 missed", "3 nights", "110 h") and "n of m <unit>" counts;
  * plain numbers of at least 100 with thousands separators or decimals ("1,302", "25.16");
  * evaluated dates ("9 Nov") next to missed / restore / until / before / by / repair / replacement.
Part B, rendered manifest strings (spec §7). For every manifest string the screen renders (the list in
tools/rendered-manifest-strings.json, recorded by tools/rendered_strings.cjs), the text outside {fig:}/{rec:}
placeholders must not hold a number equal to an evaluated figure. Clock times, ID codes, and day-month dates or
ranges are not figures and are masked first; a bare integer below 10 with no unit and no "of n" is an ordinal or
label and is not tested.

Allow-list: one entry per (file or manifest path, exact literal, context substring) with a reason. An entry that
suppresses nothing is reported as unused and fails the scan (L4: keep only entries in use). Zero is never a figure.
Prints JSON {"count", "hits", "manifest_count", "manifest_hits", "allow_used", "allow_unused", "allow_total"}.
Run: python3 tools/hand_typed_scan.py   (from the interactive-mockup-vNEXT folder)
"""
import json, pathlib, re, sys
import yaml

here = pathlib.Path(__file__).resolve().parent.parent
dv = json.loads((here.parent / 'derived-values.json').read_text(encoding='utf-8'))
MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

nums, dates = set(), set()
def walk(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ('formula', 'how', 'reason', 'restore_basis', 'bound_failure', 'dependencies', 'not_connectable'): continue
            walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
    elif isinstance(o, bool): return
    elif isinstance(o, (int, float)):
        if o != 0: nums.add(abs(float(o)))
    elif isinstance(o, str) and re.fullmatch(r'2026-\d\d-\d\d', o):
        y, m, d = o.split('-'); dates.add(f'{int(d)} {MON[int(m) - 1]}')
for k in ('sites', 'options', 'plans', 'operations', 'horizons'): walk(dv.get(k, {}))

def fmt(v):
    return f'{v:,.0f}' if float(v).is_integer() else f'{v:,.2f}'.rstrip('0').rstrip('.') if abs(v) < 1 else f'{v:,.2f}'

UNIT = r'(?:kWh|kW|L|h|hours?|nights?|days?|missed|departures?|buses|bus|crate-days|crates|%|asset-days|bus-nights)'
patterns = []
for v in sorted(nums):
    f = fmt(v)
    if v >= 10: patterns.append((re.escape('$' + f) + r'(?![\d,])', f'${f}'))
    patterns.append((r'(?<![\d,.$])' + re.escape(f) + r'\s?' + UNIT + r'\b', f'{f} <unit>'))
    patterns.append((r'(?<![\d,.$])' + re.escape(f) + r' of [\d,]+ (?:replayed |October |required |installed )?' + UNIT + r'\b', f'{f} of <n> <unit>'))
    if v >= 100 and (',' in f or '.' in f): patterns.append((r'(?<![\d,.$])' + re.escape(f) + r'(?![\d,])', f))
date_ctx = r'(?:missed|restore|until|before|by|repair|replacement)'
for d in sorted(dates):
    patterns.append((rf'{date_ctx}[^`\'"]{{0,40}}\b{re.escape(d)}\b|\b{re.escape(d)}\b[^`\'"]{{0,40}}{date_ctx}', f'{d} (date)'))

# ---- allow-list: (where, exact literal, context substring, reason) ----
ALLOW = [
    ('loop-core.js', '80 kW', 'with that example’s 2-connector', 'set-up of the preserved v7.0 earlier-demo charger example (v70 detail views), not an evaluated figure'),
    ('loop-core.js', '30 kW', '30 kW', 'illustrative interval of the energy-management source sample row ("Example interval")'),
    ('loop-core.js', '60 days', 'fitted on 60 days', 'declared model-fitting window of the proposed occupancy energy model'),
    ('loop-site.js', '60 days', 'fitted on 60 days', 'declared model-fitting window of the proposed occupancy energy model'),
    ('loop-decisions.js', '30 days', 'over 30 days', 'declared verification window'),
    ('loop-init.js', '80 kW', 'earlier demo (2 connectors', 'set-up of the preserved v7.0 earlier-demo charger example, not an evaluated figure'),
    ('loop-decisions.js', '1,000', '1,000-hour service', 'warranty condition text (declared contract term)'),
]
used = set()
def allowed(where, lit, frag):
    for i, (w, l, c, r) in enumerate(ALLOW):
        if w == where and l in lit and c in frag: used.add(i); return True
    return False

def literals(src):
    out = []
    for m in re.finditer(r'`((?:\\.|[^`\\])*)`', src, re.S):
        s = m.group(1); prev = None
        while prev != s:
            prev = s; s = re.sub(r'\$\{[^{}]*\}', ' ', s)
        out.append((m.start(), s))
    nt = re.sub(r'`(?:\\.|[^`\\])*`', lambda m: ' ' * len(m.group(0)), src, flags=re.S)
    for m in re.finditer(r"'((?:\\.|[^'\\\n])*)'|\"((?:\\.|[^\"\\\n])*)\"", nt):
        out.append((m.start(), m.group(1) if m.group(1) is not None else m.group(2)))
    return out

hits = []
for f in sorted(here.glob('loop-*.js')):
    src = f.read_text(encoding='utf-8')
    for pos, s in literals(src):
        if not re.search(r'\d', s): continue
        for p, label in patterns:
            for m in re.finditer(p, s):
                frag = s[max(0, m.start() - 40):m.end() + 40]
                if allowed(f.name, m.group(0), frag): continue
                hits.append({'file': f.name, 'line': src.count('\n', 0, pos) + 1, 'figure': label, 'text': frag.strip()})
seen, uniq = set(), []
for h in hits:
    k = (h['file'], h['line'], h['figure'], h['text'])
    if k not in seen: seen.add(k); uniq.append(h)

# ---- Part B: rendered manifest strings ----
MALLOW = [
    # (manifest path, exact literal, context substring, reason)
    ('sources.cold_chain[1].cadence', '5', '5 min', 'declared source cadence'),
    ('sources.mini_grid[0].cadence', '5', '5 min in evidence', 'declared source cadence'),
    ('sources.mini_grid[0].cadence', '15', '15 min context', 'declared source cadence'),
    ('tenants[harvest-cold].sites[Room A · Mwea].decision.options[MWEA-AGG].compatibility', '5', '5 C setpoint', 'declared commodity setpoint'),
    ('tenants[harvest-cold].sites[Room A · Mwea].period.bridge[ENERGY_EFFICIENCY].basis', '5', '5% tolerance', 'declared model tolerance'),
    ('tenants[lakeside-power].sites[Kisiwa].period.bridge[UNEXPLAINED_RESIDUAL].basis', '2', '2% tolerance', 'declared fuel-balance tolerance'),
    ('tenants[harvest-cold].sites[Room B · Thika].entitlement.contract.remedy', '30', 'within 30 days', 'contract term quoted as text'),
    ('tenants[harvest-cold].sites[Room B · Thika].entitlement.evidence.quarterly_tests', '3', '3 of 3 logged', 'recorded evidence, stated only in the record text'),
    ('tenants[harvest-cold].sites[Room B · Thika].period.bridge[CUSTOMER_COMPENSATION].basis', '6', '6 crates downgraded', 'QA record quoted from the credit note (no numeric record field)'),
    ('tenants[harvest-cold].sites[Room C · Kirinyaga].decision.options[KIRI-REPLACE].reason', '12', '12 months', 'declared horizon'),
    ('tenants[harvest-cold].sites[Room C · Kirinyaga].decision.options[KIRI-REPLACE].reason', '60', 'below 60%', 'declared revisit threshold (low end of the assumed recovery range)'),
    ('tenants[lakeside-power].sites[Kisiwa].entitlements[1].contract.service_credit', '10', '10% of monthly fee', 'contract term quoted as text'),
    ('tenants[lakeside-power].sites[Kisiwa].entitlements[1].contract.service_credit', '700', 'fee (700)', 'contract fee quoted as text (no numeric record field)'),
    ('tenants[metro-bus].sites[Kasarani].entitlement.contracts[1].service_credit', '5', '5% of monthly', 'contract term quoted as text'),
    ('tenants[metro-bus].sites[Kasarani].entitlement.contracts[1].service_credit', '400', 'fee (400)', 'contract fee quoted as text (no numeric record field)'),
    ('tenants[metro-bus].sites[Kasarani].entitlement.options[KAS-OEM-STOPGAP].detail', '10', 'energy 10', 'cost-per-bus-night quote breakdown (record text)'),
    ('tenants[lakeside-power].sites[Kobo].daytime_headroom.usable_kw', '20', '18-20', 'recorded headroom range'),
    ('tenants[lakeside-power].sites[Kobo].decision.options[KOB-RESERVE].carrier', '25', '-> 25', 'declared option setting (reserve after the change)'),
    ('tenants[lakeside-power].sites[Kobo].decision.options[KOB-STOPSOC].carrier', '90', 'threshold 90 -> 70', 'declared controller settings (current and new)'),
    ('tenants[lakeside-power].sites[Kobo].entitlement.evidence.cycles', '6000', 'of 6000', 'warranty limit quoted in the evidence record'),
    ('tenants[lakeside-power].sites[Kobo].entitlement.evidence.throughput', '600', 'of 600 MWh', 'warranty limit quoted in the evidence record'),
    ('tenants[lakeside-power].sites[Kisiwa].period.bridge[DEMAND_VOLUME].basis', '100', '100 kWh', 'bridge quantity = actual - plan billed kWh; no single node (export requested)'),
    ('tenants[lakeside-power].sites[Mto].period.bridge[DEMAND_VOLUME].basis', '20', '20 kWh', 'bridge quantity = actual - plan metered kWh; no single node (export requested)'),
    ('tenants[metro-bus].sites[Embakasi].period.bridge[PEAK_ENERGY_SHARE].basis', '30', 'against 30%', 'plan peak share; no node (export requested)'),
    ('tenants[metro-bus].sites[Embakasi].period.bridge[PEAK_ENERGY_SHARE].basis', '0.12', '0.12 premium', 'peak minus off-peak price; no single node (export requested)'),
    ('tenants[metro-bus].portfolio.operations.measures[deliverable_energy_used].binding_limit.Embakasi', '600', 'chargers 600 kW', 'chargers x charger kW; no node (export requested)'),
    ('tenants[metro-bus].portfolio.operations.measures[deliverable_energy_used].binding_limit.Ruiru', '720', 'chargers 720 kW', 'chargers x charger kW; no node (export requested)'),
    ('tenants[harvest-cold].portfolio.protect.measures[crate_minutes_above_limit].portfolio', '2,400', '2,400-3,600', 'crates x minutes range; no node (export requested)'),
    ('tenants[harvest-cold].portfolio.protect.measures[crate_minutes_above_limit].sites.Room B · Thika', '2,400', '2,400-3,600', 'crates x minutes range; no node (export requested)'),
    ('tenants[harvest-cold].portfolio.rights.measures[tracked_assets_with_complete_contract_evidence].share', '1', '1 of 1', 'rights evidence share typed; no node (export requested)'),
    ('tenants[lakeside-power].portfolio.rights.measures[tracked_assets_with_complete_contract_evidence].share', '1', '1 of 3', 'rights evidence share typed; no node (export requested)'),
    ('tenants[metro-bus].portfolio.rights.measures[tracked_assets_with_complete_contract_evidence].share', '2', '2 of 2', 'rights evidence share typed; no node (export requested)'),
    ('tenants[lakeside-power].portfolio.protect_effects[tracked_assets_with_complete_contract_evidence].options.BAT-CLAIM-NOW', '1', '1 of 3', 'per-option evidence share typed; no node (export requested)'),
    ('tenants[lakeside-power].portfolio.protect_effects[tracked_assets_with_complete_contract_evidence].options.BAT-EVIDENCE', '2', '2 of 3', 'per-option evidence share typed; no node (export requested)'),
    ('tenants[lakeside-power].portfolio.protect_effects[tracked_assets_with_complete_contract_evidence].options.BAT-NOACT', '1', '1 of 3', 'per-option evidence share typed; no node (export requested)'),
]
man = yaml.safe_load((here.parent / 'demo-site-scenario-manifest.yaml').read_text(encoding='utf-8'))
def mget(root, path):
    o = root
    for m in re.finditer(r'\[([^\]]+)\]|([^.\[\]]+)', path):
        k = m.group(1) if m.group(1) is not None else m.group(2)
        if isinstance(o, list): o = o[int(k)] if k.isdigit() else next((x for x in o if isinstance(x, dict) and k in (x.get('tenant'), x.get('site'), x.get('id'), x.get('driver'), x.get('measure'), x.get('batch'))), None)
        elif isinstance(o, dict): o = o.get(k)
        else: return None
    return o
rs_file = here / 'tools' / 'rendered-manifest-strings.json'
rendered = json.loads(rs_file.read_text(encoding='utf-8')) if rs_file.exists() else []
MASKS = [r'\{(?:fig|rec):[^{}]+\}',                                   # placeholders
         r'\b\d{1,2}:\d{2}(?::\d{2})?\b',                               # clock times
         r'\b[A-Za-z][A-Za-z0-9]*(?:[-.][A-Za-z0-9]+)*-[A-Za-z0-9]*\d[A-Za-z0-9-]*\b',  # ID codes (CN-0412, GEN-KS-02, MG-L5)
         r'\b[A-Z]{1,3}\d+(?:\.\d+)*[A-Za-z]?\b',                       # short codes (P1, O2, L1.1, A17, 1.6J)
         r'\b\d{1,2}(?:/\d{1,2})?(?:-\d{1,2}(?:/\d{1,2})?)?\s(?:' + '|'.join(MON) + r')\b(?:/\d{1,2}\s(?:' + '|'.join(MON) + r'))?',  # dates and ranges
         r'\b\d{4}-\d{2}-\d{2}(?:T[\d:+.-]+)?\b', r'\b24/7\b', r'\bv\d+(?:\.\d+)*\b', r'\b\d+-(?:day|hour|year|month|minute)\b']
mhits = []
for path in rendered:
    s = mget(man, path)
    if not isinstance(s, str): continue
    t = s
    for mk in MASKS: t = re.sub(mk, lambda m: ' ' * len(m.group(0)), t)
    for m in re.finditer(r'(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?', t):
        v = float(m.group(0).replace(',', ''))
        if v == 0 or v not in nums: continue
        after = t[m.end():m.end() + 14]
        # a bare integer below 10 with no unit and no "of n" is an ordinal or a label (connector 2, 1 - share), not a figure
        if v < 10 and float(v).is_integer() and not re.match(r'\s?(?:' + UNIT[3:-1] + r'|min|MWh|C\b)|\s+of\s+\d', after): continue
        frag = s[max(0, m.start() - 40):m.end() + 40]
        hit = False
        for i, (w, l, c, r) in enumerate(MALLOW):
            if w == path and l == m.group(0) and c in frag: used.add(len(ALLOW) + i); hit = True; break
        if not hit: mhits.append({'path': path, 'literal': m.group(0), 'text': frag})
allow_all = [{'where': w, 'literal': l, 'context': c, 'reason': r} for (w, l, c, r) in ALLOW + MALLOW]
unused = [a for i, a in enumerate(allow_all) if i not in used]
json.dump({'count': len(uniq) + len(mhits) + len(unused), 'hits': uniq, 'manifest_strings_scanned': len(rendered), 'manifest_count': len(mhits),
           'manifest_hits': mhits, 'allow_total': len(allow_all), 'allow_used': len(used), 'allow_unused': unused, 'allow': allow_all},
          sys.stdout, ensure_ascii=False, indent=0)
# 0K4m (spec §4): exit 1 on any hit not on the allow-list, and on an allow entry that suppresses nothing
sys.exit(1 if (len(uniq) + len(mhits) + len(unused)) else 0)
