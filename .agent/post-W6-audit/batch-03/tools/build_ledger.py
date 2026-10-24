"""Build batch-03.json and index.html from the part-*/evidence.json captures plus differences.json
(reads only; writes only into the batch folder)."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ".venv/Scripts/python.exe"
PRODUCERS = {
    "part-s404": (f"{PY} tools/s404_finding_index_walkthrough.py prepare|serve --db assetops_s404_owner_audit --work var/s404_owner_audit --api-port 18301 --tls-port 18302 --http-port 18303",
                  "s404_finding_index_walkthrough (S4-04 owner walkthrough: positive 2026-10-15 with 3 Findings, Finding 2ce656e8 revisions 1-4; empty 10-25; dirty/stale 10-27; failed 11-05; unassessed 10-30)"),
    "part-s404-late": (f"{PY} tools/s404_finding_index_walkthrough.py late --db assetops_s404_owner_audit ... then serve",
                       "s404 `late` mode: late Candidate block on 2026-10-15 delivered, not assessed (positive window reads not current)"),
    "part-s408-owner": (f"{PY} tools/s408_assumption_history_walkthrough.py prepare|serve --case owner --suffix _audit --api-port 18301 (prepare on 18304-18306)",
                        "s408_assumption_history_walkthrough owner case (DB assetops_s408_owner_audit): price v1-v6, cutoffs T1/T2/T3, P01 newest unpriced, P02 withheld (time order unproven)"),
    "part-s408-mixed": (f"{PY} tools/s408_assumption_history_walkthrough.py serve --case mixed --suffix _audit --api-port 18301",
                        "s408 mixed case (DB assetops_s408_mixed_audit): sources do not agree, every amount withheld"),
    "part-s405": (f"{PY} tools/s405_provenance_walkthrough.py prepare --only owner --suffix _audit; serve --case owner --suffix _audit --api-port 18301",
                  "s405_provenance_walkthrough owner case (DB assetops_s405_owner_audit): P01 2026-10-23 PRICED 0.00-15.82 USD current"),
}
diffs = json.loads((ROOT / "differences.json").read_text(encoding="utf-8"))
pairs = []
for part in sorted(PRODUCERS):
    ev = json.loads((ROOT / part / "evidence.json").read_text(encoding="utf-8"))
    for p in ev["pairs"]:
        a, m = p["app"], p["mock"]
        width = p["viewport"].split("x")[0]
        panels = []
        for i, ap in enumerate(a["panels"]):
            mp = m["panels"][i] if i < len(m["panels"]) else None
            ratio = round(ap["h"] / mp["h"], 2) if mp and mp["h"] else None
            panels.append({"title": ap["title"], "mock_title": mp["title"] if mp else None, "app_h": ap["h"], "mock_h": mp["h"] if mp else None,
                           "ratio": ratio, "over_1_3": bool(ratio and ratio > 1.3), "app_rows": ap["rows"], "mock_rows": mp["rows"] if mp else None,
                           "app_columns": ap["columns"], "mock_columns": mp["columns"] if mp else None,
                           "app_chips": ap["chips"], "mock_chips": mp["chips"] if mp else None,
                           "app_links": ap["links"], "mock_links": mp["links"] if mp else None, "app_details": ap["details"],
                           "app_bg": ap["background"], "mock_bg": mp["background"] if mp else None, "app_border": ap["border"], "mock_border": mp["border"] if mp else None})
        found = [d["id"] for d in diffs if p["screen"] in d["screens"] and (not d.get("cases") or p["case"] in d["cases"])
                 and (not d.get("widths") or width in d["widths"])]
        count_match = len(a["titles"]) == len(m["titles"])
        if a.get("consoleErrors") and not a["titles"]:
            verdict = "FAIL: page crashed (blank), see " + ", ".join(found)
        elif not count_match:
            verdict = "state without mock equivalent (refusal / non-mounted pattern); panel count differs by design"
        else:
            over = [x for x in panels if x["over_1_3"]]
            verdict = "panel count/order match; differences listed as proposals" + (f"; {len(over)} panel(s) >1.3x need ruling/reason" if over else "")
        pairs.append({
            "screen": p["screen"], "case": p["case"], "width": width, "viewport": p["viewport"], "part": part,
            "route": p["app_url"].replace("http://localhost:5183", ""), "app_url": p["app_url"], "mock": "frontend/mockups/v69/index.html" + p["mock_hash"],
            "producer_command": PRODUCERS[part][0], "producer_mode": PRODUCERS[part][1],
            "revision": "1db7360c (product code = fddf5cad)", "captured_at": ev["captured_at"],
            "app_titles": a["titles"], "mock_titles": m["titles"], "title_order_match": a["titles"] == m["titles"], "panel_count_match": count_match,
            "panels": panels, "max_ratio": max([x["ratio"] or 0 for x in panels], default=None),
            "app_page_h": a["pageH"], "mock_page_h": m["pageH"], "overflow_x": a["overflowX"],
            "header": {"app": a.get("header"), "mock": m.get("header"), "app_dark_block": (a.get("dark") or [None])[0], "app_main_top": a.get("mainTop")},
            "h1": {"app": a.get("h1"), "mock": m.get("h1")}, "fonts": {"app": a["fonts"], "mock": m["fonts"]},
            "panel_text_sizes": {"app": a.get("pSizes"), "mock": m.get("pSizes")},
            "tab_rows": {"app": [t["items"] for t in a["tabRows"]], "mock": [t["items"] for t in m["tabRows"]]},
            "clipped_text": a["clipped"], "scroll_containers": a["hscroll"], "console_errors": a.get("consoleErrors", []),
            "app_image": f"{part}/{p['app_image']}", "mock_image": f"{part}/{p['mock_image']}",
            "findings": found, "reviewer_verdict": verdict,
        })
order = ["finding", "finding-evidence", "finding-history", "sitefindings", "financials", "assumptions"]
pairs.sort(key=lambda x: (order.index(x["screen"]), x["case"], -int(x["width"])))
out = {"batch": "03", "name": "W1 Finding/money", "ids": order, "frozen_main": "1db7360c (product code identical to fddf5cad)", "branch": "audit/batch-03",
       "api": "http://127.0.0.1:18301", "frontend": "http://localhost:5183 (vite dev, ASSETOPS_API_PORT=18301)",
       "viewports": ["1440x1000", "390x900"], "capture_tool": ".agent/post-W6-audit/batch-03/tools/capture-b3.mjs (capture-only)",
       "pair_count": len(pairs), "differences": diffs, "pairs": pairs}
(ROOT / "batch-03.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
e = html.escape
rows = []
for s in order:
    rows.append(f"<h2 id='{s}'>{s}</h2>")
    for p in [x for x in pairs if x["screen"] == s]:
        pan = "".join(f"<li>{e(x['title'])} {x['app_h']}/{x['mock_h']} = {x['ratio']}{' <b>&gt;1.3</b>' if x['over_1_3'] else ''}</li>" for x in p["panels"])
        fl = ", ".join(f"<a href='#{f}'>{f}</a>" for f in p["findings"])
        rows.append(f"<section><h3>{s} · {e(p['case'])} · {p['width']}</h3><p><code>{e(p['route'])}</code><br>{e(p['reviewer_verdict'])}<br>Findings: {fl}</p>"
                    f"<p>App: {e(' | '.join(p['app_titles']))}<br>Mock: {e(' | '.join(p['mock_titles']))}</p><ul>{pan}</ul>"
                    f"<div class=pair><figure><figcaption>App</figcaption><img loading=lazy src='{p['app_image']}'></figure><figure><figcaption>Mock</figcaption><img loading=lazy src='{p['mock_image']}'></figure></div></section>")
dl = "".join(f"<tr id='{d['id']}'><td>{d['id']}</td><td>{e(', '.join(d['screens']))}</td><td>{e(d['what'])}</td><td>{e(d['disp'])}</td></tr>" for d in diffs)
(ROOT / "index.html").write_text(
    "<!doctype html><meta charset=utf-8><title>Post-W6 audit batch 03</title><style>body{font:13px system-ui;margin:16px}"
    ".pair{display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:start}img{width:100%;border:1px solid #ccc}figure{margin:0}"
    "td{border-top:1px solid #ddd;padding:4px;vertical-align:top}</style>"
    f"<h1>Post-W6 audit batch 03 (W1 Finding/money) · main 1db7360c (product = fddf5cad) · {len(pairs)} pairs</h1>"
    f"<p>Screens: {' · '.join(f'<a href=#{s}>{s}</a>' for s in order)}. All dispositions are PROPOSALS for the Architect.</p>"
    f"<table><tr><th>ID</th><th>Screens</th><th>Difference</th><th>Proposed disposition</th></tr>{dl}</table>" + "".join(rows), encoding="utf-8")
print(len(pairs), "pairs")
