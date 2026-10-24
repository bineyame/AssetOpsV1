"""One line per pair plus one per panel: height ratio, rows/cols, chips, and the shell/typography flags."""
import json, sys
ev = json.load(open(sys.argv[1], encoding="utf-8"))
for p in ev["pairs"]:
    a, m = p["app"], p["mock"]
    w = p["viewport"].split("x")[0]
    tabs = [t["items"] for t in a["tabRows"]][2:] if len(a["tabRows"]) > 2 else []
    print(f"## {p['screen']}/{p['case']} {w} H {a['pageH']}/{m['pageH']} ovf {a['overflowX']} dark {[(d['w'],d['h']) for d in a.get('dark',[])][:1]} p {a.get('pSizes')} extra-tabs {tabs} clip {len(a['clipped'])} err {len(a.get('consoleErrors',[]))}")
    if [t['items'] for t in a['tabRows']][:2] != [t['items'] for t in m['tabRows']][:2]:
        print(f"   TABS app {[t['items'] for t in a['tabRows']][:2]} mock {[t['items'] for t in m['tabRows']][:2]}")
    for i, ap in enumerate(a["panels"]):
        mp = m["panels"][i] if i < len(m["panels"]) else {}
        r = ap["h"] / mp["h"] if mp.get("h") else 0
        flag = " >1.3" if r > 1.3 else ""
        print(f"   [{i}] {ap['title'][:38]!r}/{mp.get('title','')[:30]!r} {ap['h']}/{mp.get('h')} {r:.2f}{flag} rows {ap['rows']}/{mp.get('rows')} cols {len(ap['columns'])}/{len(mp.get('columns',[]))} chips {len(ap['chips'])}/{len(mp.get('chips',[]))} links {ap['links']}/{mp.get('links')} det {ap['details']}")
    if a["clipped"]:
        print(f"   CLIP {[(c['tag'], c['text'][:40], c['sw'], c['cw'], c['sh'], c['ch']) for c in a['clipped'][:3]]}")
