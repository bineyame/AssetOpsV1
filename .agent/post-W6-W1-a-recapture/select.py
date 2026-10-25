"""post-W6 W1-a selection (rulings cross-card 5, Q39, Q40): every indexed pair of the seven W1-a screens, plus the
first indexed case (both widths) of each Q40 representative screen."""
import json, collections, pathlib
here = pathlib.Path(__file__).parent
d = json.load(open(here.parent / "post-W6-audit/audit-index.json", encoding="utf-8"))
pairs = d["pairs"]
for p in pairs: p["width"] = str(p["width"])
W1A = ["mini", "evidence-analysis", "dispatch", "finding", "finding-evidence", "finding-history", "sitefindings"]
REP = ["alternatives", "opportunity-finding", "site", "cold-finding", "ev-finding", "recommendation"]
sel = [p for p in pairs if p["screen"] in W1A]
for s in REP:
    cands = [p for p in pairs if p["screen"] == s]
    if cands:
        first = cands[0]
        sel += [p for p in cands if p["case"] == first["case"] and p["batch"] == first["batch"]]
out = [{"batch": p["batch"], "screen": p["screen"], "case": p["case"], "width": p["width"], "route": p["route"],
        "producer": p["producer"], "frozen_app": p["app"], "tags": ["w1a" if p["screen"] in W1A else "q40"],
        "frozen_titles": p["titles_app"], "frozen_heights": [x.get("app_h") for x in p["panels"]]} for p in sel]
out.sort(key=lambda e: (e["batch"], e["frozen_app"]))
json.dump({"pairs": out}, open(here / "selection.json", "w"), indent=1)
print(collections.Counter(e["screen"] for e in out))
print(collections.Counter((e["batch"], e["frozen_app"].split("/")[1]) for e in out))
print("total", len(out))
