import json, sys
for part in sys.argv[1:]:
    ev = json.load(open(f"{part}/evidence.json", encoding="utf8"))
    for p in ev["pairs"]:
        a, m = p["app"], p["mock"]
        print(f"=== {p['screen']} {p['case']} {p['viewport']} pageH app/mock {a['pageH']}/{m['pageH']} ovX {a['overflowX']} hdr {a['header'] and a['header']['h']} h1 {a['h1'] and a['h1']['text']!r} cerr {a['consoleErrors']}")
        print("  titles app", a["titles"], "| mock", m["titles"])
        for side, d in (("A", a), ("M", m)):
            for pn in d["panels"]:
                print(f"  {side} panel {pn['title']!r} h={pn['h']} w={pn['w']} rows={pn['rows']} cols={pn['columns']} chips={pn['chips'][:10]} links={pn['links']}")
        print("  A estate", {k: v for k, v in a["estate"].items() if v})
        print("  A cards", a["cardsDom"], "| M cards", m["cardsDom"])
        if "-v" in part or True:
            for pn in a["panels"]:
                for r, l in zip(pn["rowText"], pn["rowLinks"]): print("   row", r, l)
        print("  A fonts prose", a["fonts"]["prose"], "td", a["fonts"]["td"] and a["fonts"]["td"]["size"], "| M prose", m["fonts"]["prose"] and m["fonts"]["prose"]["size"], "td", m["fonts"]["td"] and m["fonts"]["td"]["size"])
        print("  A tabs", a["tabRows"], "clip", a["clipped"][:3], "hscroll", a["hscroll"][:3], "dark", a["dark"][:1])
