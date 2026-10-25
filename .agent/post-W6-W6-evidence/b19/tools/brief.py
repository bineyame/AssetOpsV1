import json, sys
ev = json.load(open(sys.argv[1], encoding="utf8"))
full = len(sys.argv) > 2
for p in ev["pairs"]:
    a, m = p["app"], p["mock"]
    print(f"== {p['screen']} {p['case']} {p['viewport']}")
    print("  titles app", a["titles"], "| mock", m["titles"])
    print("  h1", (a.get("h1") or {}).get("text"), "| crumb", a["extra"]["crumb"][:120], "| sub", a["extra"]["sub"][:120])
    print("  panels", [(x["title"][:30], x["h"], x["rows"], x["columns"]) for x in a["panels"]], "| mock", [(x["title"][:30], x["h"], x["rows"], x["columns"]) for x in m["panels"]])
    print("  tabs", [r["items"] for r in a["tabRows"]], "| mock", [r["items"] for r in m["tabRows"]])
    print("  ovx", a["overflowX"], "pageH", a["pageH"], "/", m["pageH"], "hdr", a["header"], "dark", a["dark"][:1], "mainTop", a["mainTop"], "| err", a["consoleErrors"], "| enums", a["mini"]["enums"], "uuids", a["mini"]["uuids"], "plural", a["cold"]["plural1"], "alerts", a["cold"]["alerts"])
    print("  buttons", a["extra"]["buttons"], "clipped", a["clipped"][:3], "hscroll", a["hscroll"][:3], "pSizes", a["pSizes"])
    if full: print("  TEXT", a["extra"]["mainText"][:1800])
