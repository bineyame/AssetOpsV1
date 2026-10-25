"""post-W6 W1-b selection (rulings cross-card 5, Q39, Q40, Q50/51): every indexed pair of the eleven W1-b screens,
plus the first indexed case (both widths) of each Q40 representative screen this card's shared changes reach."""
import json, collections, pathlib
here = pathlib.Path(__file__).parent
d = json.load(open(here.parent / "post-W6-audit/audit-index.json", encoding="utf-8"))
pairs = d["pairs"]
for p in pairs: p["width"] = str(p["width"])
W1B = ["sitefindings", "financials", "assumptions", "recommendation", "action-overview", "action-execution",
       "action-history", "action-plan", "action-evidence", "verification", "sitework"]
# Q40 reach: rail (cold/EV Finding + Action), FinancialsStatusBar/paging (cold/EV financials + assumptions),
# R383 label (finding, finding-evidence, finding-history) and its absence on alternatives.
REP = ["cold-finding", "ev-finding", "cold-action", "ev-action", "cold-financials", "ev-financials",
       "cold-assumptions", "ev-assumptions", "finding", "finding-evidence", "finding-history", "alternatives"]
sel = [p for p in pairs if p["screen"] in W1B]
for s in REP:
    cands = [p for p in pairs if p["screen"] == s]
    if cands:
        first = cands[0]
        sel += [p for p in cands if p["case"] == first["case"] and p["batch"] == first["batch"]]
out = [{"batch": p["batch"], "screen": p["screen"], "case": p["case"], "width": p["width"], "route": p["route"],
        "producer": p["producer"], "frozen_app": p["app"], "tags": ["w1b" if p["screen"] in W1B else "q40"],
        "frozen_titles": p["titles_app"], "frozen_heights": [x.get("app_h") for x in p["panels"]]} for p in sel]
out.sort(key=lambda e: (e["batch"], e["frozen_app"]))
json.dump({"pairs": out}, open(here / "selection.json", "w"), indent=1)
print(collections.Counter(e["tags"][0] for e in out))
print(collections.Counter((e["batch"], e["frozen_app"].split("/")[1]) for e in out))
print("total", len(out))
