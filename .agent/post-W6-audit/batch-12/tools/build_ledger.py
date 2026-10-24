"""Build batch-12.json and index.html from the part-*/evidence.json captures plus differences.json
(reads only; writes only into the batch folder). Adapted from batch-09/tools/build_ledger.py."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = "docker exec assetopsv1-postgres-1 createdb -U assetops w402r_test; PYTHONPATH=backend;backend/tests;gateway;simulator;contracts;host .venv/Scripts/python.exe .agent/W4-02-evidence/seed.py (unmodified W4-02 unit-7 seed; DB name w402r_test hard-coded); API host/ uvicorn lab_app:app 127.0.0.1:18201 DATABASE_URL=w402r_test; Vite 5182 ASSETOPS_API_PORT=18201; CDP 9522"
W403 = "docker exec assetopsv1-postgres-1 createdb -U assetops assetops_audit_b12_test; tools/w403_mini_decisions_walkthrough.py --db assetops_audit_b12_test --work var/w403_b12 prepare / serve (API 127.0.0.1:9761 hard-coded) / replay-positive (unmodified); Vite 5182 ASSETOPS_API_PORT=9761; CDP 9522"
SITE = "MG-W402-001 (Africa/Nairobi, UTC+3), site 35be594a-153b-49bb-ac73-867febe7adec; accepted positive 3321 / missing-conflicting 326; 123 mini jobs DONE, 123 selections (logs/replay-b12.json)"
PRODUCERS = {
    "part-main": (SEED, f"{SITE}. positive = renewable 06-10 Oct local / hour 06 Oct 12:00-13:00 local; gap-limited = renewable 08-12 Oct / hour 12 Oct; no-window = bare route (browser today 2026-10-24); refused-invalid = renewable 6 days / 2-hour window (422 INVALID_WINDOW); known-before-evidence = positive window + known_at=2026-10-01T00:00:00Z"),
    "part-w403": (W403, "W4-03 positive phase: KOBO-001 + MG-W402-001, opportunity da69590b-9c14-4f3f-94b4-0729c5c4386b (SUPPORTED) over 06-10 Oct; renewable window 06-10 Oct"),
}
CHECK = "part-links"
diffs = json.loads((ROOT / "differences.json").read_text(encoding="utf-8"))
pairs = []
for part in sorted(PRODUCERS):
    ev = json.loads((ROOT / part / "evidence.json").read_text(encoding="utf-8"))
    for p in [q for q in ev["pairs"] if q["screen"] != "link-check"]:
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
        elif not count_match and not a["titles"] and "refused" in p["case"]:
            verdict = "refused window: period bar + Period cannot be read box, strip/cards/panels dropped (B12-06; header B1-02/B2-04 at 390)"
        elif not count_match:
            verdict = "panel count differs from the mock"
        else:
            over = [x for x in panels if x["over_1_3"]]
            verdict = "panel count/order match; differences listed as proposals" + (f"; {len(over)} panel(s) >1.3x need ruling/reason" if over else "")
        pairs.append({
            "screen": p["screen"], "case": p["case"], "width": width, "viewport": p["viewport"], "part": part,
            "route": p["app_url"].replace("http://127.0.0.1:5182", ""), "app_url": p["app_url"], "mock": "frontend/mockups/v69/index.html" + p["mock_hash"],
            "producer_command": PRODUCERS[part][0], "producer_mode": PRODUCERS[part][1],
            "revision": "6813b477 (product code = fddf5cad)", "captured_at": ev["captured_at"],
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
order = ["renewable", "service", "fuel", "backup"]
pairs.sort(key=lambda x: (order.index(x["screen"]), x["case"], -int(x["width"])))
cross = []
for part in ("part-links", "part-w403"):
    chk = json.loads((ROOT / part / "evidence.json").read_text(encoding="utf-8"))
    cross += [{"screen": p["screen"], "case": p["case"], "viewport": p["viewport"], "app_url": p["app_url"], "app_titles": p["app"]["titles"],
          "overview_cards": p["app"]["mini"]["objective"], "console_errors": p["app"].get("consoleErrors", []),
          "app_image": f"{part}/{p['app_image']}", "mock_image": f"{part}/{p['mock_image']}", "finding": "B12-12 Overview link check"} for p in chk["pairs"] if p["screen"] == "link-check"]
out = {"batch": "12", "name": "W4 mini depth", "ids": order, "frozen_main": "6813b477 (product code identical to fddf5cad)", "branch": "audit/batch-12",
       "api": "http://127.0.0.1:18201 (W4-02 seed DB) and http://127.0.0.1:9761 (W4-03 walkthrough serve, hard-coded)", "frontend": "http://127.0.0.1:5182 (vite dev)",
       "viewports": ["1440x1000", "390x900"], "capture_tool": ".agent/post-W6-audit/batch-12/tools/capture-b12.mjs (capture-only)",
       "pair_count": len(pairs), "differences": diffs, "pairs": pairs, "cross_check_not_counted": cross}
(ROOT / "batch-12.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
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
rows.append("<h2 id='cross-check'>Link check (not counted): mini Overview cards to these pages</h2>")
for c in cross:
    rows.append(f"<section><h3>{c['screen']} · {e(c['case'])} · {c['viewport']}</h3><p><code>{e(c['app_url'])}</code> · {c['finding']}</p>"
                f"<div class=pair><figure><figcaption>App</figcaption><img loading=lazy src='{c['app_image']}'></figure><figure><figcaption>Mock</figcaption><img loading=lazy src='{c['mock_image']}'></figure></div></section>")
dl = "".join(f"<tr id='{d['id']}'><td>{d['id']}</td><td>{e(', '.join(d['screens']) or 'link check')}</td><td>{e(d['what'])}</td><td>{e(d['disp'])}</td></tr>" for d in diffs)
(ROOT / "index.html").write_text(
    "<!doctype html><meta charset=utf-8><title>Post-W6 audit batch 12</title><style>body{font:13px system-ui;margin:16px}"
    ".pair{display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:start}img{width:100%;border:1px solid #ccc}figure{margin:0}"
    "td{border-top:1px solid #ddd;padding:4px;vertical-align:top}</style>"
    f"<h1>Post-W6 audit batch 12 (W4 mini depth) · main 6813b477 (product = fddf5cad) · {len(pairs)} pairs</h1>"
    f"<p>Screens: {' · '.join(f'<a href=#{s}>{s}</a>' for s in order)} · <a href=#cross-check>cross-check</a>. All dispositions are PROPOSALS for the Architect.</p>"
    f"<table><tr><th>ID</th><th>Screens</th><th>Difference</th><th>Proposed disposition</th></tr>{dl}</table>" + "".join(rows), encoding="utf-8")
print(len(pairs), "pairs")
