"""Hand-typed figure scan (rev 12, review M5).

Fails when a loop-*.js file holds a digit-bearing string literal (quoted or template text, ${...} removed) that restates a
figure the structure evaluator produces (../derived-values.json), formatted the way the screen formats it:
  * money: "$1,234" or "$1,234.50" for every evaluated number of at least 10;
  * quantities with a unit: "1,050 kWh", "62 missed", "2 departures", "3 nights", "110 h", "46.67%" ... for every evaluated number;
  * plain numbers of at least 100 with thousands separators or decimals ("1,302", "25.16");
  * evaluated restore dates ("9 Nov") next to missed / restore / until / before / by / repair / replacement.
An explicit allow-list (ALLOW, below) names literal fragments that are declared constants, not evaluated figures, with a reason.
Prints JSON {"count": n, "hits": [...], "allow": {...}}.
Run: python3 tools/hand_typed_scan.py   (from the interactive-mockup-vNEXT folder)
"""
import json, pathlib, re, sys

here = pathlib.Path(__file__).resolve().parent.parent
dv = json.loads((here.parent / 'derived-values.json').read_text(encoding='utf-8'))
MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

nums, dates = set(), set()
def walk(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ('formula', 'how', 'reason', 'restore_basis', 'bound_failure'): continue
            walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
    elif isinstance(o, bool): return
    elif isinstance(o, (int, float)):
        if o != 0: nums.add(abs(float(o)))  # zero is never a restated figure ("0 L", "$0")
    elif isinstance(o, str) and re.fullmatch(r'2026-\d\d-\d\d', o):
        y, m, d = o.split('-'); dates.add(f'{int(d)} {MON[int(m) - 1]}')
walk(dv['sites']); walk(dv['options']); walk(dv['plans']); walk(dv['operations'])

def fmt(v):
    return f'{v:,.0f}' if float(v).is_integer() else f'{v:,.2f}'.rstrip('0').rstrip('.') if abs(v) < 1 else f'{v:,.2f}'

UNIT = r'(?:kWh|kW|L|h|hours?|nights?|days?|missed|departures?|buses|bus|crate-days|crates|%|asset-days|bus-nights)'
patterns = []
for v in sorted(nums):
    f = fmt(v)
    if v >= 10: patterns.append((re.escape('$' + f) + r'(?![\d,])', f'${f}'))
    patterns.append((r'(?<![\d,.$])' + re.escape(f) + r'\s?' + UNIT + r'\b' if not f.endswith('%') else re.escape(f), f'{f} <unit>'))
    patterns.append((r'(?<![\d,.$])' + re.escape(f) + r' of [\d,]+ (?:replayed |October |required |installed )?' + UNIT + r'\b', f'{f} of <n> <unit>'))
    if v >= 100 and (',' in f or '.' in f): patterns.append((r'(?<![\d,.$])' + re.escape(f) + r'(?![\d,])', f))
date_ctx = r'(?:missed|restore|until|before|by|repair|replacement)'
for d in sorted(dates):
    patterns.append((rf'{date_ctx}[^`\'"]{{0,40}}\b{re.escape(d)}\b|\b{re.escape(d)}\b[^`\'"]{{0,40}}{date_ctx}', f'{d} (date)'))

# Declared constants that are not evaluated figures (fragment -> reason). Matching is on the hit text.
ALLOW = {
    '35% at 5 am': 'declared dawn-adequacy policy (obligation), not an evaluated figure',
    '5 °C': 'declared commodity limit', '12 °C': 'declared commodity limit', '2–4 °C': 'declared chamber band',
    '15 minutes': 'declared contract threshold', '5% tolerance': 'declared model tolerance',
    '2% tolerance': 'declared fuel-balance tolerance', 'a 5% tolerance': 'declared model tolerance',
    '1 Nov': 'event date (fault, tariff start), declared', '6 Oct': 'incident date, declared', '30 Oct': 'event date, declared',
    '28 Oct': 'event date, declared', '3 Oct': 'event date, declared', '7 Oct': 'inspection date, declared',
    '14 days': 'declared trial length', '14 supervised nights': 'declared trial length', '14 matched days': 'declared trial window',
    '30 days': 'declared verification window', '60 days': 'declared model-fitting window', '61 days': 'declared replay window length',
    '12 months': 'declared horizon', '4 months': 'declared contract length', '7-year': 'declared life view',
    '1,000-hour': 'warranty condition text (declared contract term), not an evaluated figure',
    '80 kW': 'set-up of the preserved earlier-demo charger example (v70 detail views), not an evaluated figure',
    '42 kW': 'illustrative interval in a source sample row', '30 kW': 'illustrative interval in a source sample row (energy-management export)',
    '10%': 'declared comparability band', '60–90%': 'declared recovery range (assumption)', '80%': 'declared recovery share (assumption)',
}

def literals(src):
    out = []
    # template literals (may span lines); strip ${...} expressions (nested braces)
    for m in re.finditer(r'`((?:\\.|[^`\\])*)`', src, re.S):
        s = m.group(1)
        prev = None
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
        if s.startswith('/') or re.fullmatch(r'[\w\s.#/:-]*', s) and not re.search(r'\d{2,}', s): pass
        for p, label in patterns:
            for m in re.finditer(p, s):
                frag = s[max(0, m.start() - 25):m.end() + 25]
                if any(a in frag and (a in m.group(0) or m.group(0) in a) for a in ALLOW): continue
                line = src.count('\n', 0, pos) + 1
                hits.append({'file': f.name, 'line': line, 'figure': label, 'text': frag.strip()})
seen, uniq = set(), []
for h in hits:
    k = (h['file'], h['line'], h['figure'], h['text'])
    if k not in seen: seen.add(k); uniq.append(h)
json.dump({'count': len(uniq), 'hits': uniq, 'allow': ALLOW}, sys.stdout, ensure_ascii=False, indent=0)
