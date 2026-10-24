"""Compact per-pair comparison printout of a capture-b2 evidence.json (reviewer aid; reads only)."""
import json
import sys

ev = json.load(open(sys.argv[1], encoding="utf-8"))
only = sys.argv[2] if len(sys.argv) > 2 else None
for p in ev["pairs"]:
    if only and p["screen"] + "-" + p["case"] != only and p["screen"] != only:
        continue
    a, m = p["app"], p["mock"]
    print(f"=== {p['screen']}/{p['case']} {p['viewport']}  pageH app {a['pageH']} mock {m['pageH']}  overflowX {a['overflowX']}")
    print(f"  titles app: {a['titles']}")
    print(f"  titles mok: {m['titles']}")
    for i, ap in enumerate(a["panels"]):
        mp = m["panels"][i] if i < len(m["panels"]) else None
        r = f"{ap['h'] / mp['h']:.2f}" if mp and mp["h"] else "-"
        print(f"  [{i}] {ap['title'][:40]!r} h {ap['h']}/{mp['h'] if mp else '-'} r{r} w {ap['w']}/{mp['w'] if mp else '-'}"
              f" rows {ap['rows']}/{mp['rows'] if mp else '-'} cols {ap['columns']} | {mp['columns'] if mp else ''}")
        if ap["chips"] or (mp and mp["chips"]):
            print(f"       chips {ap['chips'][:8]} | {mp['chips'][:8] if mp else ''}")
        print(f"       links {ap['links']}/{mp['links'] if mp else '-'} details {ap['details']}/{mp['details'] if mp else '-'} h3 {ap['h3'][:5]} | {mp['h3'][:5] if mp else ''}")
    ah, mh = a.get("header") or {}, m.get("header") or {}
    print(f"  header app {ah.get('cls')} {ah.get('h')} {ah.get('bg')} | mock {mh.get('cls')} {mh.get('h')} {mh.get('bg')}")
    a1, m1 = a.get("h1") or {}, m.get("h1") or {}
    print(f"  h1 app {a1.get('text','')[:40]!r} top {a1.get('top')} {a1.get('size')}/{a1.get('weight')} {a1.get('family')} | mock {m1.get('text','')[:30]!r} top {m1.get('top')} {m1.get('size')}/{m1.get('weight')} {m1.get('family')}")
    af, mf = a["fonts"], m["fonts"]
    g = lambda f, k: (f.get(k) or {}).get("size")
    print(f"  fonts body {af['body']['family']}|{mf['body']['family']} prose {af['proseSizes']}|{mf['proseSizes']} first-p {g(af,'prose')}|{g(mf,'prose')} h2 {g(af,'h2')}|{g(mf,'h2')} td {g(af,'td')}|{g(mf,'td')} th {g(af,'th')}|{g(mf,'th')}")
    print(f"  tabs app {[t['items'] for t in a['tabRows']]}")
    print(f"  tabs mok {[t['items'] for t in m['tabRows']]}")
    print(f"  pSizes app {a.get('pSizes')} mock {m.get('pSizes')}  dark app {a.get('dark')} mock {m.get('dark')} mainTop {a.get('mainTop')}/{m.get('mainTop')}")
    if a["clipped"]:
        print(f"  CLIPPED {a['clipped'][:4]}")
    if a["hscroll"]:
        print(f"  hscroll {a['hscroll'][:4]}")
    if a.get("consoleErrors"):
        print(f"  CONSOLE {[e[:120] for e in a['consoleErrors']]}")
