"""W3-01 commit 4: compare every app capture piece with the build-spec 30% caps (spec "Per-screen panel/copy/layout
dry-read"); writes measure-summary.json and prints one line per screen/width (max over states)."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
F = {1440: {"cards": 146, "chips": 40, "notice": 54, "page": 1431}, 390: {"cards": 322, "chips": 40, "notice": 101}}
CAPS = {
    "findings": {1440: {**F[1440], "panel": 575}, 390: {**F[390], "panel": 975, "page": 2245}},
    "findings-cost": {1440: {**F[1440], "panel": 240}, 390: {**F[390], "panel": 341, "page": 1579}},
    "findings-risks": {1440: {**F[1440], "panel": 439}, 390: {**F[390], "panel": 721, "page": 1937}},
    "findings-opportunities": {1440: {**F[1440], "panel": 240}, 390: {**F[390], "panel": 341, "page": 1579}},
    "actions": {1440: {"cards": 146, "panel": 436, "notice": 54, "page": 1431},
                390: {"cards": 322, "panel": 767, "notice": 78, "page": 1820}},
}
CAPS["findings-page-two"] = CAPS["findings"]
out, worst = [], {}
for f in sorted(HERE.glob("app-*.json")):
    for r in json.loads(f.read_text(encoding="utf-8"))["results"]:
        caps = CAPS.get(r["screen"])
        if not caps:
            continue
        cap = caps[r["width"]]
        vals = {k: (v or {}).get("h") for k, v in r["pieces"].items()}
        vals["page"] = r["height"]
        over = {k: [vals[k], c] for k, c in cap.items() if vals.get(k) is not None and vals[k] > c}
        row = {"state": r["state"], "screen": r["screen"], "width": r["width"], "values": vals, "over_cap": over,
               "overflowX": r["overflowX"], "clipped": r["clipped"], "tableScroll": r["tableScroll"],
               "chipScroll": r["chipScroll"], "lensRows": r["lensRows"], "firstColumn": r["firstColumnPosition"]}
        out.append(row)
        print(f"{r['state']:<10} {r['screen']:<22} {r['width']:>4} " + " ".join(f"{k}={v}" for k, v in vals.items() if v is not None)
              + f" ovX={r['overflowX']} over={over or '-'}")
(HERE / "measure-summary.json").write_text(json.dumps({"caps": CAPS, "rows": out}, indent=2) + "\n", encoding="utf-8")
