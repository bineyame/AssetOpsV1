"""Build batch-05.json and index.html from the part-*/evidence.json captures plus differences.json
(reads only; writes only into the batch folder)."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ".venv/Scripts/python.exe"
PRODUCERS = {
    "part-s603": (f"{PY} tools/s603_site_work_walkthrough.py --db assetops_s603_owner_audit --work var/s603_owner_audit prepare|attest|serve --port 18501 --web-port 5185|drop",
                  "s603_site_work_walkthrough (S6-03 owner walkthrough, D-action-records: ACT-000001/ACT-000002 created 2026-11-01; positive window 11-01..11-02, zero window 10-01..11-01, limit=1 page, no window; invalid window = URL from>to, capture-only); attest OK"),
    "part-s602b-replay": (f"{PY} tools/s602b_verification_walkthrough.py --db assetops_s602b_audit --work var/s602b_audit prepare|serve --port 18502 --web-port 5185|drop (replay API on 18502)",
                          "s602b public replay of d-verification-window-v2: real VERIFIED Action, exact historical outcome, selector conflict; unknown Action id = refused (capture-only URL)"),
    "part-s602b-cases": (f"{PY} tools/s602b_verification_walkthrough.py --db assetops_s602b_audit --work var/s602b_audit serve --case <name> --port 18502 (case API on 18503)",
                         "s602b TEST-SCOPED cases (S6-02a evaluator builders, not Lab runs): target_miss, guardrail, inconclusive, withdrawn"),
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
            "route": p["app_url"].replace("http://localhost:5185", ""), "app_url": p["app_url"], "mock": "frontend/mockups/v69/index.html" + p["mock_hash"],
            "producer_command": PRODUCERS[part][0], "producer_mode": PRODUCERS[part][1],
            "revision": "73d538ab (product code = fddf5cad)", "captured_at": ev["captured_at"],
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
order = ["verification", "sitework"]
pairs.sort(key=lambda x: (order.index(x["screen"]), x["case"], -int(x["width"])))
out = {"batch": "05", "name": "W1 verification", "ids": order, "frozen_main": "73d538ab (product code identical to fddf5cad)", "branch": "audit/batch-05",
       "api": "http://127.0.0.1:18501-18503", "frontend": "http://localhost:5185 (vite dev, ASSETOPS_API_PORT=18501/18502/18503)",
       "viewports": ["1440x1000", "390x900"], "capture_tool": ".agent/post-W6-audit/batch-05/tools/capture-b5.mjs (capture-only)",
       "pair_count": len(pairs), "differences": diffs, "pairs": pairs}
(ROOT / "batch-05.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
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
    "<!doctype html><meta charset=utf-8><title>Post-W6 audit batch 05</title><style>body{font:13px system-ui;margin:16px}"
    ".pair{display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:start}img{width:100%;border:1px solid #ccc}figure{margin:0}"
    "td{border-top:1px solid #ddd;padding:4px;vertical-align:top}</style>"
    f"<h1>Post-W6 audit batch 05 (W1 verification) · main 73d538ab (product = fddf5cad) · {len(pairs)} pairs</h1>"
    f"<p>Screens: {' · '.join(f'<a href=#{s}>{s}</a>' for s in order)}. All dispositions are PROPOSALS for the Architect.</p>"
    f"<table><tr><th>ID</th><th>Screens</th><th>Difference</th><th>Proposed disposition</th></tr>{dl}</table>" + "".join(rows), encoding="utf-8")
print(len(pairs), "pairs")
