"""cap-b18: compact summary.json from part-*/evidence.json vs the frozen batch-18 part evidence (reads only).
usage: python summarize_w6.py <b18r dir> <frozen batch-18 dir> <previous b18 dir>
b18r recapture (6f54ad1b): also compares every pair with the previous W6 run (b18, f3da6e90) -> changed_vs_previous."""
import glob, json, os, sys

B, F, P = sys.argv[1], sys.argv[2], sys.argv[3]
INDEXED = {"inc", "maint", "prev", "op", "zero", "hist", "stress", "linked", "absent", "scope", "cold", "coldwc", "ev", "evwc"}


def load(root):
    out = {}
    for f in sorted(glob.glob(os.path.join(root, "part-*", "evidence.json"))):
        part = os.path.basename(os.path.dirname(f))[5:]
        for p in json.load(open(f, encoding="utf8"))["pairs"]:
            out[(part, p["screen"], p["case"], p["viewport"].split("x")[0])] = p
    return out


cur, frz, prv = load(B), load(F), load(P)
prv_any = {k[1:]: v for k, v in prv.items()}
LIST = {"incidents", "maintenance", "maintenance-preventive", "oprecords"}
changed_prev = []


def classify(screen, kind, panel=None):
    if screen in LIST and kind in ("panel_height", "inner_hscroll", "clipped") and (panel is None or panel in LIST_PANELS.get(screen, set())):
        return "expected (list change: cell-disclosure two-line preview / Feeds 125)"
    return "unexpected"


LIST_PANELS = {}
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
    pz = prv_any.get(k[1:])
    if pz:
        pa = pz["app"]; d2 = []
        item["titles_match_previous"] = a["titles"] == pa["titles"]
        tbl = {x["title"] for x in a["panels"] if x["tables"]} | {x["title"] for x in pa["panels"] if x["tables"]}
        LIST_PANELS.setdefault(screen, set()).update(tbl)
        if a["titles"] != pa["titles"]: d2.append(["titles", pa["titles"], a["titles"], "unexpected"])
        if (a["overflowX"] > 0) != (pa["overflowX"] > 0): d2.append(["page_overflow", pa["overflowX"], a["overflowX"], "unexpected"])
        fh = sorted({(h["panel"], h["sw"] > h["cw"]) for h in pa["hscroll"]}); ch = sorted({(h["panel"], h["sw"] > h["cw"]) for h in a["hscroll"]})
        if fh != ch or [(h["panel"], h["sw"], h["cw"]) for h in pa["hscroll"]][:3] != item["hscroll"]:
            d2.append(["inner_hscroll", [(h["panel"], h["sw"], h["cw"]) for h in pa["hscroll"]][:3], item["hscroll"], classify(screen, "inner_hscroll", (item["hscroll"] or [(h["panel"],) for h in pa["hscroll"]] or [(None,)])[0][0])])
        if sorted(set(pa["consoleErrors"])) != sorted(set(a["consoleErrors"])): d2.append(["console_errors", pa["consoleErrors"], a["consoleErrors"], "unexpected"])
        if sorted(set(pa.get("consoleWarnings", []))) != sorted(set(a.get("consoleWarnings", []))): d2.append(["console_warnings", pa.get("consoleWarnings", []), a.get("consoleWarnings", []), "unexpected"])
        ph = {x["title"]: x["h"] for x in pa["panels"]}
        for x in a["panels"]:
            if x["title"] in ph and abs(x["h"] - ph[x["title"]]) > 2:
                d2.append(["panel_height" + (" (all-open)" if "all-open" in case or "probe" in case else ""), x["title"], ph[x["title"]], x["h"], classify(screen, "panel_height", x["title"])])
        item["changed_vs_previous"] = d2
        if d2: changed_prev.append({"part": part, "screen": screen, "case": case, "width": w, "diffs": d2})
    else:
        item["changed_vs_previous"] = "no previous pair"; item["titles_match_previous"] = None
    pairs.append(item)

idx = [p for p in pairs if p["indexed"]]
summ = {"revision": "6f54ad1b", "pairs_indexed": len(idx), "pairs_extra": len(pairs) - len(idx),
        "titles_match_mock": sum(p["titles_match_mock"] for p in idx), "titles_match_frozen": sum(bool(p["titles_match_frozen"]) for p in idx),
        "page_overflow_pairs": [f'{p["screen"]} {p["case"]} {p["width"]}' for p in pairs if p["overflow"] > 0],
        "console_error_pairs": [f'{p["screen"]} {p["case"]} {p["width"]}' for p in pairs if p["console"]["errors"]],
        "console_warning_pairs": [f'{p["screen"]} {p["case"]} {p["width"]}' for p in pairs if p["console"]["warnings"]],
        "missing_vs_frozen": [" ".join(k) for k in frz if k not in cur and k[0] in INDEXED],
        "changed_vs_frozen": changed,
        "titles_match_previous": sum(bool(p["titles_match_previous"]) for p in idx),
        "missing_vs_previous": [" ".join(k) for k in prv if k not in cur and k[1:] not in {c[1:] for c in cur}],
        "changed_vs_previous": changed_prev, "pairs": pairs}
json.dump(summ, open(os.path.join(B, "summary.json"), "w", encoding="utf8"), indent=1, ensure_ascii=False)
print("indexed", len(idx), "extra", len(pairs) - len(idx), "titles=mock", summ["titles_match_mock"], "titles=frozen", summ["titles_match_frozen"],
      "overflow", len(summ["page_overflow_pairs"]), "errors", len(summ["console_error_pairs"]), "warnings", len(summ["console_warning_pairs"]),
      "missing", len(summ["missing_vs_frozen"]), "changed", len(changed),
      "titles=prev", summ["titles_match_previous"], "missing_prev", len(summ["missing_vs_previous"]), "changed_prev", len(changed_prev),
      "unexpected", sum(1 for c in changed_prev for d in c["diffs"] if d[-1] == "unexpected"))
