"""Build batch-13.json and index.html from the part-*/evidence.json captures plus differences.json
(reads only; writes only into the batch folder). Adapted from batch-11/tools/build_ledger.py."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = "http://127.0.0.1:5183"
W = ("PYTHONPATH=backend;backend/tests;contracts;gateway;simulator;host .venv/Scripts/python.exe "
     "tools/w403_mini_decisions_walkthrough.py --db assetops_audit_b13_test --work var/w403_b13 {mode} "
     "(serve on API 127.0.0.1:9761, hard-coded by the producer); Vite 127.0.0.1:5183 ASSETOPS_API_PORT=9761")
FIX = "backend/tests/fixtures/w4/w403-mini-decisions.json: KOBO-001 (S4 F02, W1) + MG-W402-001 (W4-02 install), OPP-000001 850a3228-33f7-4ab7-9dab-ac88cc3b9a9e"
PRODUCERS = {
    "part-one": (W.format(mode="prepare; serve; replay-positive"), FIX + "; after replay-positive: 1 MG incident (INC-000001, linked to OPP/SCN), 1 request (WR-000002), SCN-000002/3"),
    "part-stocked": (W.format(mode="capture --phase positive (seeds 4 incidents + 2 requests through W4-01 WorkService)"), FIX + "; capture stock: 5 incidents, 3 requests"),
    "part-late": (W.format(mode="replay-late; capture --phase late"), FIX + "; after replay-late: late 13 Oct variant, rerun, k_before_late cutoff, 8-12 Oct missing branch (OPP-000004)"),
}
REV = "d1d91a55 (product code = fddf5cad)"
diffs = json.loads((ROOT / "differences.json").read_text(encoding="utf-8"))
REPRESENTATIVE = {("scenarios", "populated"), ("alternatives", "db-time-409"), ("opportunity-finding", "supported-current"),
                  ("sitework-incidents", "stocked"), ("sitework-maintenance", "stocked")}
pairs = []
for part in PRODUCERS:
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
        found = [d["id"] for d in diffs if p["screen"] in d["screens"] and (not d.get("cases") or p["case"] in d["cases"])]
        count_match = len(a["titles"]) == len(m["titles"])
        if a.get("consoleErrors"):
            verdict = "FAIL: console error"
        elif not a["titles"]:
            verdict = "refusal state: no panels (refusal copy only); see " + ", ".join(found)
        elif not count_match:
            verdict = "panel count differs from the mock"
        else:
            over = [x for x in panels if x["over_1_3"]]
            verdict = "panel count/order/titles match; differences listed as proposals" + (f"; {len(over)} panel(s) >1.3x (see B13-17)" if over else "; no panel >1.3x")
        pairs.append({
            "screen": p["screen"], "case": p["case"], "width": width, "viewport": p["viewport"], "part": part,
            "representative": (p["screen"], p["case"]) in REPRESENTATIVE,
            "route": p["app_url"].replace(B, ""), "app_url": p["app_url"], "mock": "frontend/mockups/v69/index.html" + p["mock_hash"],
            "producer_command": PRODUCERS[part][0], "producer_mode": PRODUCERS[part][1],
            "revision": REV, "captured_at": ev["captured_at"],
            "app_titles": a["titles"], "mock_titles": m["titles"], "title_order_match": a["titles"] == m["titles"], "panel_count_match": count_match,
            "panels": panels, "max_ratio": max([x["ratio"] or 0 for x in panels], default=None),
            "app_page_h": a["pageH"], "mock_page_h": m["pageH"], "overflow_x": a["overflowX"],
            "header": {"app": a.get("header"), "mock": m.get("header"), "app_dark_block": (a.get("dark") or [None])[0], "app_main_top": a.get("mainTop")},
            "h1": {"app": a.get("h1"), "mock": m.get("h1")}, "fonts": {"app": a["fonts"], "mock": m["fonts"]},
            "tab_rows": {"app": [t["items"] for t in a["tabRows"]], "mock": [t["items"] for t in m["tabRows"]]},
            "panel_text_sizes": {"app": a.get("pSizes"), "mock": m.get("pSizes")},
            "clipped_text": a["clipped"], "scroll_containers": a["hscroll"], "console_errors": a.get("consoleErrors", []),
            "app_text": a.get("mainText", "")[:1500], "app_links": a.get("links", []),
            "app_image": f"{part}/{p['app_image']}", "mock_image": f"{part}/{p['mock_image']}",
            "findings": found, "reviewer_verdict": verdict,
        })
order = ["scenarios", "alternatives", "opportunity-finding", "sitework-incidents", "sitework-maintenance"]
pairs.sort(key=lambda x: (order.index(x["screen"]), not x["representative"], list(PRODUCERS).index(x["part"]), x["case"], -int(x["width"])))
producer_extra = {"dir": "producer-w403-capture", "note": "Copied from the producer's own capture mode (tools/w403-mini-decisions-evidence.mjs, CDP 9763): 459 checks passed; its scoped fail503 rule states are not reproducible by a capture-only wrapper and are kept as producer evidence, not counted as pairs.",
                  "images": ["alternatives-read-503-1440-app.png", "alternatives-read-503-390-app.png", "incidents-refused-overlay-1440-app.png", "incidents-refused-overlay-390-app.png"],
                  "unproved_by_producer": ["alternatives-stocked", "alternatives-empty-current"]}
out = {"batch": "13", "name": "W4 decisions/cases", "ids": order, "frozen_main": REV, "branch": "audit/batch-13",
       "api": "W4-03 walkthrough serve 127.0.0.1:9761 (hard-coded in the unmodified producer)", "frontend": B + " (vite dev, ASSETOPS_API_PORT=9761)", "cdp": 9523,
       "db": "assetops_audit_b13_test (rule a; created before prepare, dropped by the producer's drop mode)",
       "viewports": ["1440x1000", "390x900"], "capture_tool": ".agent/post-W6-audit/batch-13/tools/capture-b13.mjs (capture-only)",
       "pair_count": len(pairs), "representative_pairs": [f"{p['screen']}/{p['case']}/{p['width']}" for p in pairs if p["representative"]],
       "differences": diffs, "pairs": pairs, "producer_capture_evidence": producer_extra}
(ROOT / "batch-13.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
e = html.escape
rows = []
for s in order:
    rows.append(f"<h2 id='{s}'>{s}</h2>")
    for p in [x for x in pairs if x["screen"] == s]:
        pan = "".join(f"<li>{e(x['title'])} {x['app_h']}/{x['mock_h']} = {x['ratio']}{' <b>&gt;1.3</b>' if x['over_1_3'] else ''}</li>" for x in p["panels"])
        fl = ", ".join(f"<a href='#{f}'>{f}</a>" for f in p["findings"])
        rows.append(f"<section><h3>{s} · {e(p['case'])} · {p['width']}{' · representative' if p['representative'] else ''}</h3><p><code>{e(p['route'])}</code><br>{e(p['producer_mode'])}<br>{e(p['reviewer_verdict'])}<br>Findings: {fl}</p>"
                    f"<p>App: {e(' | '.join(p['app_titles']) or '(refusal)')}<br>Mock: {e(' | '.join(p['mock_titles']))}</p><ul>{pan}</ul>"
                    f"<div class=pair><figure><figcaption>App</figcaption><img loading=lazy src='{p['app_image']}'></figure><figure><figcaption>Mock</figcaption><img loading=lazy src='{p['mock_image']}'></figure></div></section>")
rows.append("<h2 id='producer'>Producer capture evidence (not counted)</h2><p>" + e(producer_extra["note"]) + "</p><div class=pair>" +
            "".join(f"<figure><figcaption>{i}</figcaption><img loading=lazy src='producer-w403-capture/{i}'></figure>" for i in producer_extra["images"]) + "</div>")
dl = "".join(f"<tr id='{d['id']}'><td>{d['id']}{' (' + d['severity'] + ')' if d.get('severity') else ''}</td><td>{e(', '.join(d['screens']) or 'cross-check')}</td><td>{e(d['what'])}</td><td>{e(d['disp'])}</td></tr>" for d in diffs)
(ROOT / "index.html").write_text(
    "<!doctype html><meta charset=utf-8><title>Post-W6 audit batch 13</title><style>body{font:13px system-ui;margin:16px}"
    ".pair{display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:start}img{width:100%;border:1px solid #ccc}figure{margin:0}"
    "td{border-top:1px solid #ddd;padding:4px;vertical-align:top}</style>"
    f"<h1>Post-W6 audit batch 13 (W4 decisions/cases) · main {REV} · {len(pairs)} pairs</h1>"
    f"<p>Screens: {' · '.join(f'<a href=#{s}>{s}</a>' for s in order)} · <a href=#producer>producer captures</a>. All dispositions are PROPOSALS for the Architect.</p>"
    f"<table><tr><th>ID</th><th>Screens</th><th>Difference</th><th>Proposed disposition</th></tr>{dl}</table>" + "".join(rows), encoding="utf-8")
print(len(pairs), "pairs")
