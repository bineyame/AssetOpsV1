"""Tabulate the capped-panel probe results from an inspect.json (capture-only bookkeeping)."""
import json, sys
d = json.load(open(sys.argv[1], encoding="utf8"))
for a in d["results"]:
    for c in a.get("caps", []):
        out = []
        for k, v in c.items():
            if not isinstance(v, dict): continue
            if k == "real":
                out.append(f"real={v['closed']['panelH']} open={v['open']['panelH']} clip={len(v['closed']['clipped'])+len(v['open']['clipped'])}")
            else:
                sx = [(s['sw'], s['cw'], s['scrolls']) for s in v.get('innerScrollX', [])]
                out.append(f"{k}={v.get('panelH')} rows={v.get('rowHs')} ver={v.get('verified')} f={v.get('fieldsChanged')}/{v.get('intendedFields')} clip={len(v.get('clipped',[]))} openclip={len((v.get('openedAll') or {}).get('clipped',[]))} ovx={v.get('docOverflowX')} sx={sx}")
        print(a["screen"], a["case"], a["width"], c["panel"], "\n   " + "\n   ".join(out))
    if a["case"] in ("refused", "one-sided-from", "long-32d"):
        print("  REFUSAL", a["screen"], a["case"], a["width"], [v for v in a["sentenceCounts"].values()], "notAssessed", a["notAssessed"], "banners", len(a["banners"]))
