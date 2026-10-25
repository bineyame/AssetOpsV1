"""cap-b18: compact summary.json from part-*/evidence.json vs the frozen batch-18 part evidence (reads only).
usage: python summarize_w6.py <b18 dir> <frozen batch-18 dir>"""
import glob, json, os, sys

B, F = sys.argv[1], sys.argv[2]
INDEXED = {"inc", "maint", "prev", "op", "zero", "hist", "stress", "linked", "absent", "scope", "cold", "coldwc", "ev", "evwc"}


def load(root):
    out = {}
    for f in sorted(glob.glob(os.path.join(root, "part-*", "evidence.json"))):
        part = os.path.basename(os.path.dirname(f))[5:]
        for p in json.load(open(f, encoding="utf8"))["pairs"]:
            out[(part, p["screen"], p["case"], p["viewport"].split("x")[0])] = p
    return out


cur, frz = load(B), load(F)
pairs, changed = [], []
for k, p in cur.items():
    part, screen, case, w = k
    a = p["app"]; w6 = a.get("w6", {}); fz = frz.get(k)
    fa = fz["app"] if fz else None
    item = {"part": part, "screen": screen, "case": case, "width": w, "indexed": part in INDEXED,
            "titles": a["titles"], "mock_titles": p["mock"]["titles"],
            "titles_match_mock": a["titles"] == p["mock"]["titles"],
            "titles_match_frozen": (a["titles"] == fa["titles"]) if fa else None,
            "overflow": a["overflowX"], "hscroll": [(h["panel"], h["sw"], h["cw"]) for h in a["hscroll"]][:3],
            "closed_panel_heights": {x["title"]: x["h"] for x in a["panels"]} if "all-open" not in case else None,
            "panel_heights": {x["title"]: x["h"] for x in a["panels"]},
            "console": {"errors": a["consoleErrors"], "warnings": a.get("consoleWarnings", [])},
            "url": w6.get("url"), "h1": w6.get("h1"), "crumbs": w6.get("crumbs"), "status": w6.get("status"),
            "membership": w6.get("membership"), "showing": w6.get("showing"), "deviations": w6.get("deviations"),
            "table": w6.get("table"), "form": w6.get("form"), "plural1": a["b18"].get("plural1"),
            "assetLabels": a["b18"].get("assetLabels"), "findings": w6.get("findings"),
            "requestLinks": w6.get("requestLinks"), "siteLinks": w6.get("siteLinks")}
    if fa:
        diffs = []
        if a["titles"] != fa["titles"]: diffs.append(["titles", fa["titles"], a["titles"]])
        if (a["overflowX"] > 0) != (fa["overflowX"] > 0): diffs.append(["page_overflow", fa["overflowX"], a["overflowX"]])
        fh = [(h["panel"], h["sw"] > h["cw"]) for h in fa["hscroll"]]; ch = [(h["panel"], h["sw"] > h["cw"]) for h in a["hscroll"]]
        if sorted(set(fh)) != sorted(set(ch)): diffs.append(["inner_hscroll", [(h["panel"], h["sw"], h["cw"]) for h in fa["hscroll"]][:3], item["hscroll"]])
        if fa["consoleErrors"] != a["consoleErrors"]: diffs.append(["console_errors", fa["consoleErrors"], a["consoleErrors"]])
        fb, cb = fa["b18"], a["b18"]
        for key in ("showing", "plural1", "assetLabels"):
            if fb.get(key) != cb.get(key): diffs.append([key, fb.get(key), cb.get(key)])
        if fa["b15"].get("crumbs") != a["b15"].get("crumbs"): diffs.append(["crumbs", fa["b15"].get("crumbs"), a["b15"].get("crumbs")])
        if fb.get("status") != cb.get("status"): diffs.append(["status", fb.get("status")[:160], cb.get("status")[:160]])
        if fb.get("siteLinks") != cb.get("siteLinks"): diffs.append(["siteLinks", fb.get("siteLinks")[:3], cb.get("siteLinks")[:3]])
        item["changed_vs_frozen"] = diffs
        if diffs: changed.append({"part": part, "screen": screen, "case": case, "width": w, "diffs": diffs})
    else:
        item["changed_vs_frozen"] = "no frozen pair"
    pairs.append(item)

idx = [p for p in pairs if p["indexed"]]
summ = {"revision": "f3da6e90", "pairs_indexed": len(idx), "pairs_extra": len(pairs) - len(idx),
        "titles_match_mock": sum(p["titles_match_mock"] for p in idx), "titles_match_frozen": sum(bool(p["titles_match_frozen"]) for p in idx),
        "page_overflow_pairs": [f'{p["screen"]} {p["case"]} {p["width"]}' for p in pairs if p["overflow"] > 0],
        "console_error_pairs": [f'{p["screen"]} {p["case"]} {p["width"]}' for p in pairs if p["console"]["errors"]],
        "console_warning_pairs": [f'{p["screen"]} {p["case"]} {p["width"]}' for p in pairs if p["console"]["warnings"]],
        "missing_vs_frozen": [" ".join(k) for k in frz if k not in cur and k[0] in INDEXED],
        "changed_vs_frozen": changed, "pairs": pairs}
json.dump(summ, open(os.path.join(B, "summary.json"), "w", encoding="utf8"), indent=1)
print("indexed", len(idx), "extra", len(pairs) - len(idx), "titles=mock", summ["titles_match_mock"], "titles=frozen", summ["titles_match_frozen"],
      "overflow", len(summ["page_overflow_pairs"]), "errors", len(summ["console_error_pairs"]), "warnings", len(summ["console_warning_pairs"]),
      "missing", len(summ["missing_vs_frozen"]), "changed", len(changed))
