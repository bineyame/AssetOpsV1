"""Q24 selection: greedy 21-producer representative cover (first case per screen, both widths) + every indexed
case of the 18 directly changed screens. Writes selection.json grouped by batch/part."""
import json, collections, pathlib
here = pathlib.Path(__file__).parent
d = json.load(open(here.parent / "post-W6-audit/audit-index.json"))
pairs = d["pairs"]
for p in pairs: p["width"] = str(p["width"])
CHANGED = {"sites","foundation","readiness","sld","changes","asset","evidence-analysis","sitework-incidents",
           "sitework-maintenance","cold-work-incidents","cold-work-maintenance","ev-work-incidents","ev-work-maintenance",
           "action-overview","action-plan","action-execution","action-evidence","action-history"}
prod = collections.OrderedDict()
for p in pairs: prod.setdefault((p["batch"], p["producer"]), []).append(p)
screens = {p["screen"] for p in pairs}
covered, cover = set(), []
while covered != screens:
    key = max(prod, key=lambda k: len({p["screen"] for p in prod[k]} - covered))
    new = {p["screen"] for p in prod[key]} - covered
    cover.append((key, sorted(new))); covered |= new
rep = []
for (key, new) in cover:
    for s in new:
        first = next(p for p in prod[key] if p["screen"] == s)
        rep += [p for p in prod[key] if p["screen"] == s and p["case"] == first["case"]]
chg = [p for p in pairs if p["screen"] in CHANGED]
sel = {}
for tag, lst in (("rep", rep), ("changed", chg)):
    for p in lst:
        k = (p["batch"], p["screen"], p["case"], p["width"])
        e = sel.setdefault(k, {"batch": p["batch"], "screen": p["screen"], "case": p["case"], "width": p["width"],
             "route": p["route"], "producer": p["producer"], "frozen_app": p["app"], "tags": [],
             "frozen_titles": p["titles_app"], "frozen_heights": [x.get("app_h") for x in p["panels"]]})
        if tag not in e["tags"]: e["tags"].append(tag)
out = sorted(sel.values(), key=lambda e: (e["batch"], e["frozen_app"]))
json.dump({"cover": [[k[0], k[1][:90], n] for k, n in cover], "pairs": out}, open(here / "selection.json", "w"), indent=1)
print("cover producers", len(cover), "rep pairs", len(rep), "changed", len(chg), "union", len(out))
c = collections.Counter((e["batch"], e["frozen_app"].split("/")[1]) for e in out)
for k, v in sorted(c.items()): print(k, v)
