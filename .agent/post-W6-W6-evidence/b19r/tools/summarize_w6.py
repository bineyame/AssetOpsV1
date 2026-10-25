"""W6 b19r recapture summary (6f54ad1b): per pair vs the frozen batch-19.json and vs the previous W6 run (../../b19/summary.json, f3da6e90); writes ../summary.json (compact)."""
import json, glob, os
from pathlib import Path
B = Path(__file__).resolve().parent.parent
F = json.load(open(B.parent.parent / "post-W6-audit/batch-19/batch-19.json", encoding="utf8"))
frozen = {(p["screen"], p["case"], p["width"]): p for p in F["pairs"]}
PREV = json.load(open(B.parent / "b19" / "summary.json", encoding="utf8"))
prev = {(p["screen"], p["case"], p["width"]): p for p in PREV["pairs"] + PREV["links"]}
changed_prev = []
def cmp_prev(rec):
    pz = prev.get((rec["screen"], rec["case"], rec["width"]))
    if pz is None:
        rec["changed_vs_previous"] = "no previous pair"; changed_prev.append({"pair": "/".join((rec["screen"], rec["case"], rec["width"])), "what": [["no previous pair", "unexpected"]]}); return
    d = []
    rec["titles_match_previous"] = pz["titles"] == rec["titles"]
    if pz["titles"] != rec["titles"]: d.append(["titles", pz["titles"], rec["titles"], "unexpected"])
    if (pz["overflow"] > 0) != (rec["overflow"] > 0): d.append(["page_overflow", pz["overflow"], rec["overflow"], "unexpected"])
    if sorted(set(pz["console_errors"])) != sorted(set(rec["console_errors"])): d.append(["console_errors", pz["console_errors"], rec["console_errors"], "unexpected"])
    if sorted(set(pz["console_warnings"])) != sorted(set(rec["console_warnings"])): d.append(["console_warnings", pz["console_warnings"], rec["console_warnings"], "unexpected"])
    ph, ch = pz.get("closed_panel_heights") or {}, rec.get("closed_panel_heights") or {}
    for t, h in ch.items():
        if t in ph and abs(h - ph[t]) > 2: d.append(["closed_panel_height", t, ph[t], h, "expected (list change)" if rec["screen"] == "link-check" and rec["case"] == "maintenance-list" else "unexpected"])
    rec["changed_vs_previous"] = d
    if d: changed_prev.append({"pair": "/".join((rec["screen"], rec["case"], rec["width"])), "what": d})
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
            cmp_prev(rec); links.append(rec); continue
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
        cmp_prev(rec); pairs.append(rec)
summary = {"revision": "6f54ad1b", "pairs_captured": len(pairs), "pairs_expected": 194, "link_captures": len(links),
           "reruns": reruns, "titles_match_mock": sum(p["titles"] == p["mock_titles"] for p in pairs),
           "titles_match_previous": sum(bool(p.get("titles_match_previous")) for p in pairs),
           "page_overflow_pairs": ["/".join((p["screen"], p["case"], p["width"])) for p in pairs + links if p["overflow"] > 0],
           "console_error_pairs": ["/".join((p["screen"], p["case"], p["width"])) for p in pairs + links if p["console_errors"]],
           "console_warning_pairs_count": sum(1 for p in pairs + links if p["console_warnings"]),
           "missing_vs_previous": ["/".join(k) for k in prev if k not in {(p["screen"], p["case"], p["width"]) for p in pairs + links}],
           "pairs": pairs, "links": links, "changed_vs_frozen": changed, "changed_vs_previous": changed_prev}
json.dump(summary, open(B / "summary.json", "w", encoding="utf8"), indent=1, ensure_ascii=False)
print("pairs", len(pairs), "links", len(links), "changed", len(changed), "titles=mock", summary["titles_match_mock"], "titles=prev", summary["titles_match_previous"],
      "overflow", len(summary["page_overflow_pairs"]), "errors", len(summary["console_error_pairs"]), "missing_prev", len(summary["missing_vs_previous"]), "changed_prev", len(changed_prev))
