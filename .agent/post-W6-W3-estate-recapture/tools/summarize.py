"""Per-pair summary of a part's evidence.json: panels (title:h), worst-case probe, overflow, clipped, console errors."""
import json, sys
d = json.load(open(sys.argv[1] + "/evidence.json"))
for p in d["pairs"]:
    a = p["app"]; w = p["viewport"].split("x")[0]
    panels = ", ".join(f'{x["title"][:28]}:{x["h"]}r{x["rows"]}' for x in a["panels"])
    wc = "; ".join(f'{x["title"][:20]}:{x["before"]}->{x.get("after","-")} clip{x.get("clipped","-")} iv{len(x.get("innerV",[]))}' for x in a.get("worstCase", []) if x.get("rows"))
    print(f'{p["screen"]}/{p["case"]} {w}: ox{a["overflowX"]} clip{len(a["clipped"])} err{len(a.get("consoleErrors",[]))} | {panels} | WC {wc}')
