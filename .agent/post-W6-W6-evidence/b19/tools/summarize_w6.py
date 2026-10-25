"""W6 b19 recapture summary: per pair vs the frozen batch-19.json; writes ../summary.json (compact)."""
import json, glob, os
from pathlib import Path
B = Path(__file__).resolve().parent.parent
F = json.load(open(B.parent.parent / "post-W6-audit/batch-19/batch-19.json", encoding="utf8"))
frozen = {(p["screen"], p["case"], p["width"]): p for p in F["pairs"]}
frozen_links = {(p["screen"], p["case"], p["viewport"].split("x")[0]): p for p in F["cross_check_not_counted"]}
pairs, links, changed = [], [], []
def rendered(p):
    a = p["app"]; x = a.get("extra2", {})
    return bool(a["titles"]) or bool(x.get("refusalKey")) or bool(x.get("unknownSection"))
chosen, reruns = {}, []
for ev in sorted(glob.glob(str(B / "part-*/evidence.json"))) + sorted(glob.glob(str(B / "rerun-*/evidence.json"))):
    part = Path(ev).parent.name
    for p in json.load(open(ev, encoding="utf8"))["pairs"]:
        k = (p["screen"], p["case"], p["viewport"])
        if k in chosen and not rendered(p):
            continue
        if k in chosen: reruns.append({"pair": "/".join(k), "first": chosen[k][0], "used": part, "first_rendered": rendered(chosen[k][1])})
        chosen[k] = (part, p)
for part, p in chosen.values():
    if True:
        w = p["viewport"].split("x")[0]; a = p["app"]; x = a.get("extra2", {})
        rec = {"part": part, "screen": p["screen"], "case": p["case"], "width": w,
               "titles": a["titles"], "mock_titles": p["mock"]["titles"], "overflow": a["overflowX"],
               "closed_panel_heights": None if "all-open" in p["case"] else {q["title"]: q["h"] for q in a["panels"]},
               "console_errors": a.get("consoleErrors", []), "console_warnings": a.get("consoleWarnings", []),
               "alerts": x.get("alerts"), "statuses": x.get("statuses"), "refusal": x.get("refusalKey"), "reload": x.get("reload"),
               "open_site": x.get("openSite"), "subtitle": x.get("subtitle"), "asof": x.get("asof"), "api": a.get("apiRequests", []),
               "tabs": x.get("tabs"), "deviations": x.get("deviations"), "source_links": x.get("sourceLinks"),
               "act_codes": x.get("actCodes"), "mr_labels": x.get("maintRecordLabels"), "unknown_section": x.get("unknownSection"),
               "crumb": x.get("crumb"), "raw_connector": a["cold"].get("rawConnector"), "h1": (a.get("h1") or {}).get("text"),
               "image": f"{part}/{p['app_image']}"}
        key = (p["screen"], p["case"], w)
        if p["screen"] == "link-check":
            fz = frozen_links.get(key)
            rec["frozen_titles"] = fz["app_titles"] if fz else None
            links.append(rec); continue
        fz = frozen.get(key)
        if fz is None:
            rec["frozen"] = "missing"; pairs.append(rec); changed.append({"pair": key, "what": "no frozen pair"}); continue
        rec["titles_match_frozen"] = fz["app_titles"] == a["titles"]
        rec["frozen_titles"] = fz["app_titles"]
        rec["frozen_overflow"] = fz["overflow_x"]; rec["frozen_console"] = fz["console_errors"]
        rec["frozen_tabs"] = fz["tab_rows"]["app"]
        if rec["closed_panel_heights"] is not None:
            rec["frozen_heights"] = {q["title"]: q["app_h"] for q in fz["panels"] if q.get("app_h") is not None}
        diffs = []
        if not rec["titles_match_frozen"]: diffs.append(f"titles {fz['app_titles']} -> {a['titles']}")
        if (fz["overflow_x"] > 0) != (a["overflowX"] > 0): diffs.append(f"overflow {fz['overflow_x']} -> {a['overflowX']}")
        if bool(fz["console_errors"]) != bool(a.get("consoleErrors")): diffs.append(f"console {len(fz['console_errors'])} -> {len(a.get('consoleErrors', []))}")
        if diffs: changed.append({"pair": "/".join(key), "what": diffs})
        pairs.append(rec)
summary = {"revision": "f3da6e90", "pairs_captured": len(pairs), "pairs_expected": 194, "link_captures": len(links),
           "reruns": reruns, "pairs": pairs, "links": links, "changed_vs_frozen": changed}
json.dump(summary, open(B / "summary.json", "w", encoding="utf8"), indent=1, ensure_ascii=False)
print("pairs", len(pairs), "links", len(links), "changed", len(changed))
