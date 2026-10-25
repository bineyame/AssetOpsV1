"""r3 assertions per capture: refusal sentence count exactly 1, other panels say Not assessed, 0 overflow/clipping/console,
panel titles equal the mock's. Writes r3-8bfd4730/summary-r3.json (capture-only bookkeeping)."""
import json, pathlib
R = pathlib.Path(__file__).resolve().parents[1] / "r3-8bfd4730"
rows = []
for ev in sorted(R.glob("part-*/evidence.json")):
    d = json.loads(ev.read_text(encoding="utf8"))
    for p in d["pairs"]:
        a, x = p["app"], p["app"]["extra"]
        sc = sum(x["sentenceCounts"].values())
        pr = x["panelRefusal"]
        others = [q for q in pr if q["sentences"] == 0]
        others_na = all(q["notAssessed"] > 0 for q in others)
        r = {"screen": p["screen"], "case": p["case"], "w": p["viewport"].split("x")[0], "url": p["app_url"], "revision": d["revision"],
             "sentenceTotal": sc, "panels": pr, "othersNotAssessed": others_na, "overflowX": a["overflowX"], "clipped": len(a["clipped"]),
             "console": a["consoleErrors"], "titles": a["titles"], "titlesMatchMock": a["titles"] == p["mock"]["titles"],
             "windowTitle": x["windowTitle"], "banners": x["banners"]}
        r["pass"] = sc == 1 and others_na and r["overflowX"] <= 0 and not r["clipped"] and not r["console"] and r["titlesMatchMock"]
        rows.append(r)
(R / "summary-r3.json").write_text(json.dumps({"captures": len(rows), "passed": sum(r["pass"] for r in rows), "rows": rows}, indent=1), encoding="utf8")
print("captures", len(rows), "passed", sum(r["pass"] for r in rows), "revisions", sorted({r["revision"] for r in rows}))
for r in rows:
    print(("PASS" if r["pass"] else "FAIL"), r["screen"], r["case"], r["w"], "sent", r["sentenceTotal"], "panels", [(q["title"][:28], q["sentences"], q["notAssessed"]) for q in r["panels"]], "wt", r["windowTitle"], "ban", len(r["banners"]), "ovx", r["overflowX"], "clip", r["clipped"], "con", len(r["console"]), "mock", r["titlesMatchMock"])
