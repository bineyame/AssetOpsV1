"""One line per pair (read-only): panels h/ratio, pageH, header/dark, plural, window form, alerts, notice, errors."""
import json, sys
for part in sys.argv[1:]:
    ev = json.load(open(f"{part}/evidence.json", encoding="utf8"))
    for p in ev["pairs"]:
        a, m = p["app"], p["mock"]; c = a["cold"]; b = a["b15"]
        mp = {x["title"]: x for x in m["panels"]}
        pan = "; ".join(f"{x['title'][:22]} {x['h']}/{mp[x['title']]['h'] if x['title'] in mp else '-'} r{x['rows']}" for x in a["panels"])
        dk = (a["dark"] or [{}])[0]
        wf = c["windowForm"]
        print(f"{p['screen'][10:] or p['screen']}|{p['case']}|{p['viewport'][:4]}| T{a['titles']} | {pan} | page {a['pageH']}/{m['pageH']} ovX{a['overflowX']} dark{dk.get('h')} | pl{c['plural1']} | win{wf and (wf['h'], wf['error'])} | al{[x[:90] for x in c['alerts']]} | nt{[x[:110] for x in a['mini']['notice']]} | ref{a['mini']['refusal'][:160]} | det{c['detailsOpen']}/{a['mini']['details']} clip{len(a['clipped'])} err{a['consoleErrors']}")
