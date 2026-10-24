"""Batch 18: one-line-per-pair digest of every part-*/evidence.json (reads only)."""
import json, glob, sys
for f in sorted(glob.glob("part-*/evidence.json")):
    for p in json.load(open(f, encoding="utf8"))["pairs"]:
        a, m = p["app"], p["mock"]; b = a.get("b18", {})
        ph = [(x["title"][:22], x["h"], next((y["h"] for y in m["panels"] if y["title"] == x["title"]), None)) for x in a["panels"]]
        print(f"## {f.split('/')[0]} {p['screen']} {p['case']} {p['viewport']}")
        print("  titles app", a["titles"], "| mock", m["titles"])
        print("  panels(app,mock h)", [(t, h, mh, round(h / mh, 2) if mh else None) for t, h, mh in ph], "rows", [x["rows"] for x in a["panels"]], "cols", [x["columns"] for x in a["panels"]][:1], "mockcols", [x["columns"] for x in m["panels"]][:1])
        print("  pageH", a["pageH"], m["pageH"], "ovf", a["overflowX"], "hdr", a["header"] and a["header"]["h"], "dark", a["dark"][:1], "console", a["consoleErrors"], "clipped", [(c["tag"], c["text"][:30]) for c in a["clipped"]][:3], "hscroll", [(h["sw"], h["cw"]) for h in a["hscroll"]][:2])
        print("  showing", b.get("showing"), "pager", b.get("pager"), "alerts", b.get("alerts"), "plural", b.get("plural1"), "ev", b.get("evConnector"), "assets", b.get("assetLabels"), "enums", b.get("enums"), "utc", b.get("utcHits"))
        print("  sites", b.get("siteLinks")[:6], "work", b.get("workLinks")[:8])
        print("  fonts prose", a["fonts"]["prose"] and a["fonts"]["prose"]["size"], "mock", m["fonts"]["prose"] and m["fonts"]["prose"]["size"], "pSizes", a["pSizes"], "mock", m["pSizes"], "td", a["fonts"]["td"] and a["fonts"]["td"]["size"], m["fonts"]["td"] and m["fonts"]["td"]["size"])
