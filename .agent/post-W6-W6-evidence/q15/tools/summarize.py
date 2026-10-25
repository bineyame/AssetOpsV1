# cap-q15: build summary.json from part-*/probe-results.json. SYNTHETIC LAYOUT PROBE - not product data.
import glob, json, math, os
Q = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPS = {  # (screen, panel): {width: cap or None (provisional)}
    ("incidents", "Incident cases"): {1440: 700, 390: 800},
    ("incidents", "Case boundaries"): {1440: None, 390: None},
    ("maintenance", "Corrective work requests"): {1440: 700, 390: 800},
    ("maintenance-preventive", "Preventive plan"): {1440: 600, 390: 690},
    ("oprecords", "Operational records"): {1440: 650, 390: 780},
    ("oprecords", "Record a manual reading"): {1440: None, 390: None},
    ("oprecords", "How records are used"): {1440: None, 390: None},
    ("wr-overview", "Work done"): {1440: 500, 390: None},
    ("wr-overview", "Lifecycle"): {1440: 500, 390: None},
    ("wr-record", "Maintenance record · activity"): {1440: 700, 390: None},
    ("wr-history", "History"): {1440: 550, 390: 690},
}
SCREEN = {"Incident cases": "incidents", "Case boundaries": "incidents", "Corrective work requests": "maintenance", "Preventive plan": "maintenance-preventive",
          "Operational records": "oprecords", "Record a manual reading": "oprecords", "How records are used": "oprecords", "Work done": "wr-overview",
          "Lifecycle": "wr-overview", "Maintenance record · activity": "wr-record", "History": "wr-history"}
res = []
for f in sorted(glob.glob(os.path.join(Q, "part-*", "probe-results.json"))):
    part = os.path.basename(os.path.dirname(f))
    for r in json.load(open(f, encoding="utf-8"))["results"]:
        r["part"] = part; res.append(r)
rows, assertions = [], []
for (screen, panel), caps in CAPS.items():
    for w, cap in caps.items():
        rs = [r for r in res if r.get("panel") == panel and r["w"] == w and "closed" in r]
        if not rs:
            rows.append({"screen": screen, "panel": panel, "w": w, "missing": True}); continue
        def real(r): return next((p["h"] for p in r["baselinePanels"] if p["t"] == panel), 0)
        base = max(rs, key=real)
        peak_r = max(rs, key=lambda r: max(real(r), r["closed"]["panelH"]))
        peak = max(real(peak_r), peak_r["closed"]["panelH"])
        prov = math.ceil(peak * 1.15 / 50) * 50
        c = base["closed"]
        row = {"screen": screen, "panel": panel, "w": w, "baseCase": base["name"], "basePart": base["part"], "baseRealClosedPx": real(base),
               "probeClosedPxOnBase": c["panelH"], "fiveRowHeights": c["rowHs"], "rowUnit": c.get("rowUnit", "table row (tr)"),
               "peakClosedPx": peak, "peakCase": peak_r["name"] + ("(probe)" if peak_r["closed"]["panelH"] >= real(peak_r) else "(real)"),
               "cap": cap, "provisionalCap": None if cap else prov, "pass": (peak <= cap) if cap else None,
               "clippedClosed": c["clippedCount"], "clippedClosedWithoutFullText": c["clippedWithoutFullText"], "vScrollers": c.get("vScrollers"),
               "scrollers": c["scrollers"], "docOverflowX": c["docOverflowX"],
               "allOpen": {"panelH": base["allOpen"]["panelH"], "clipped": base["allOpen"]["clippedCount"], "clippedWithoutFullText": base["allOpen"]["clippedWithoutFullText"], "vScrollers": base["allOpen"].get("vScrollers"), "docOverflowX": base["allOpen"]["docOverflowX"]},
               "allCases": sorted([[r["name"], real(r), r["closed"]["panelH"]] for r in rs], key=lambda x: -max(x[1], x[2]))}
        rows.append(row)
for r in [x for x in res if "closed" in x]:
    c = r["closed"]
    assertions.append({"case": r["name"], "w": r["w"], "kind": r["kind"], "verified": c["verified"], "rows": c.get("rows"), "fieldsPerRow": c.get("fieldsPerRow"),
                       "intendedFields": c["intendedFields"], "fields160": c["fields160"], "fieldNames": c.get("fieldNames"), "extraFields160": c.get("extraFields160")})
skipped = [[r["name"], r["w"], r.get("skipped") or r.get("error")] for r in res if "closed" not in r]
op = [{"case": r["name"], "w": r["w"], "real": r["baselineOpTable"], "probe": r["closed"].get("opTable")} for r in res if r.get("panel") == "Operational records" and "closed" in r]
tabs = [{"case": r["name"], "w": r["w"], "tabs": r["baselineTabs"]} for r in res if r["w"] == 390 and r.get("baselineTabs") and "closed" in r]
out = {"label": "SYNTHETIC LAYOUT PROBE - not product data (probe rows); real rows are the unmodified app", "product": "f3da6e90",
       "seed": "tools/w601_seed.py unmodified; DBs assetops_w601_w6q15<tag>_test", "caps": rows,
       "assertions": {"all_verified": all(a["verified"] for a in assertions), "count": len(assertions), "items": assertions},
       "skippedOrErrored": skipped, "R356": op, "R364": tabs}
json.dump(out, open(os.path.join(Q, "summary.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for r in rows:
    if r.get("missing"): print("MISSING", r["screen"], r["panel"], r["w"]); continue
    print(f'{r["screen"]:<22} {r["panel"][:28]:<28} {r["w"]:>4} base={r["baseCase"][:40]:<40} real={r["baseRealClosedPx"]:>4} probe={r["probeClosedPxOnBase"]:>4} peak={r["peakClosedPx"]:>4} rows={r["fiveRowHeights"]} cap={r["cap"]} prov={r["provisionalCap"]} pass={r["pass"]} clipNF={r["clippedClosedWithoutFullText"]} vS={[(v["sh"], v["ch"]) for v in (r["vScrollers"] or [])]} doc={r["docOverflowX"]} open={r["allOpen"]["panelH"]}/{r["allOpen"]["clippedWithoutFullText"]}')
print("ALL_VERIFIED", out["assertions"]["all_verified"], len(assertions))
