import json,sys
ev=json.load(open(sys.argv[1]+"/evidence.json",encoding="utf-8"))
for p in ev["pairs"]:
    a,m=p["app"],p["mock"]; w=p["viewport"].split("x")[0]
    print(f"\n## {p['screen']} {p['case']} {w}  pageH {a['pageH']}/{m['pageH']} ovX {a['overflowX']} hdr {a['header'] and a['header']['h']}/{m['header'] and m['header']['h']} dark {(a['dark'] or [{}])[0].get('h')} err {a.get('consoleErrors')}")
    print("  h1:", a['h1'] and a['h1']['text'], '|', m['h1'] and m['h1']['text'])
    print("  tabs app:", [t['items'] for t in a['tabRows']]); print("  tabs mock:", [t['items'] for t in m['tabRows']])
    print("  pSizes", a['pSizes'], m['pSizes'])
    for i in range(max(len(a['panels']),len(m['panels']))):
        ap=a['panels'][i] if i<len(a['panels']) else {}; mp=m['panels'][i] if i<len(m['panels']) else {}
        r=round(ap.get('h',0)/mp['h'],2) if mp.get('h') else None
        print(f"  [{i}] {ap.get('title')!r} {ap.get('h')} | {mp.get('title')!r} {mp.get('h')} r={r} rows {ap.get('rows')}/{mp.get('rows')} cols {ap.get('columns')}/{mp.get('columns')} chips {ap.get('chips')}/{mp.get('chips')} links {ap.get('links')}/{mp.get('links')} det {ap.get('details')} xy {ap.get('x')},{ap.get('y')} w{ap.get('w')}|{mp.get('x')},{mp.get('y')} w{mp.get('w')}")
    if a['clipped']: print("  clipped", a['clipped'][:3])
    if a['hscroll']: print("  hscroll", a['hscroll'][:3])
