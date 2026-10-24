"""Batch 18 compact digest (reads part-*/evidence.json only)."""
import json, glob
for f in sorted(glob.glob("part-*/evidence.json")):
    for p in json.load(open(f, encoding="utf8"))["pairs"]:
        a, m = p["app"], p["mock"]; b = a.get("b18", {})
        r = [(x["title"][:14], x["h"], round(x["h"] / y["h"], 2)) for x in a["panels"] for y in m["panels"] if y["title"] == x["title"]]
        print(f.split("\\")[0][5:], p["screen"], p["case"], p["viewport"][:4], "| T", len(a["titles"]), "/", len(m["titles"]), "| r", r, "| rows", [x["rows"] for x in a["panels"]],
              "| hdr", a["header"] and a["header"]["h"], "dark", (a["dark"][:1] or [{}])[0].get("h"), "h1top", a["h1"] and a["h1"]["top"], "| ovf", a["overflowX"], "| hs", [(h["sw"], h["cw"]) for h in a["hscroll"]][:1],
              "| clip", len(a["clipped"]), "| err", len(a["consoleErrors"]), "|", b.get("showing"), b.get("pager"), "| al", [x[:90] for x in b.get("alerts", [])][:3],
              "| pl", b.get("plural1"), "ev", b.get("evConnector"), "as", b.get("assetLabels"), "en", b.get("enums")[:5])
