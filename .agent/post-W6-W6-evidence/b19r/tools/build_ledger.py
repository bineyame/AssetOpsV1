"""Build batch-19.json and index.html from the part-*/evidence.json captures plus differences.json
(reads only; writes only into the batch folder). Adapted from batch-17/tools/build_ledger.py."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
W601 = "tools/w601_seed.py --db assetops_w601_b19<tag>_test --fixture <fixture> --clock 2026-10-20T12:00:00Z (unmodified); uvicorn assetops_backend.main:app on 127.0.0.1:18901 (tools/run_phase.ps1); Vite 127.0.0.1:5189 -> 18901; CDP 9529"
SITE = "KOBO-001 / KOBO-002 mini (stored timezone Africa/Addis_Ababa; app shows UTC). Fixture clock 2026-10-20T12:00:00Z"
W504 = "W504_API_PORT_BASE=18900 tools/w504_ev_work_walkthrough.py --work var/w504a_b19 --tag b19 prepare / serve / attest / drop (unmodified; DBs w504a_<mode>_b19_test); Vite 5189 -> mode port; CDP 9529"
PRODUCERS = {
    "part-detail": (W601.replace("<tag>", "detail").replace("<fixture>", "detail"), SITE + ". detail: WR-000001 IN_PROGRESS after COMPLETE+REOPEN+revision (6 history rows, 2 pages), WR-000002 CANCELLED; 404/no-site/bad known_at/wrong site/malformed id/before-created; historical known_at 11:59:04Z (revision 1, COMPLETED); all-open; history page 2 (client pager)"),
    "part-hist": (W601.replace("<tag>", "hist").replace("<fixture>", "detail-history"), SITE + ". detail-history: known_at 12:00:01Z selects revision 2; current selects revision 3"),
    "part-linked": (W601.replace("<tag>", "linked").replace("<fixture>", "detail-linked"), SITE + ". detail-linked: WR-000005 raised from INC-000004 with lineage-true Finding and Action pins"),
    "part-stress": (W601.replace("<tag>", "stress").replace("<fixture>", "stress"), SITE + ". stress: WR-000007 200-char unbroken title, 128-char owner, 4000-char narrative/activity, 500-char correction reason"),
    "part-maint": (W601.replace("<tag>", "maint").replace("<fixture>", "maintenance"), SITE + ". maintenance: WR-000001 OPEN, WR-000004 CANCELLED from OPEN, WR-000005 IN_PROGRESS (KOBO-002, assigned), WR-000006 COMPLETED (KOBO-002); WR-000008 other tenant -> 404"),
    "part-forbidden": (W601.replace("<tag>", "detail").replace("<fixture>", "detail").replace("assetops_backend.main:app", "api_403:app --app-dir .agent/W6-01-evidence/C2 (reviewed TEST-ONLY composition)"), SITE + ". real 403 SITE_SCOPE_FORBIDDEN from the C2 test-only access callback (not a production grant outcome)"),
    "part-unavailable": (W601.replace("<tag>", "detail").replace("<fixture>", "detail").replace("assetops_backend.main:app", "api_503:app --app-dir .agent/W6-01-evidence/C4 (reviewed TEST-ONLY composition)"), SITE + ". real 503 WORK_STORE_UNAVAILABLE from the C4 outage Site scope"),
}
W502 = "tools/w502_cold_work_walkthrough.py --work var/w502b_b19 --tag b19 prepare / serve / attest / drop (unmodified; hard-coded API ports 8971-8977, confirmed free first; DBs w502b_<mode>_b19_test); Vite 5189 -> mode port; CDP 9529"
EV = "EV-LAB-001 (Etc/UTC). "
COLD = "COLD-LAB-001 (stored Africa/Addis_Ababa; app shows UTC). "
PRODUCERS.update({
    "part-ev-positive": (W504 + " [positive :18901]", EV + "attested WR-000002 + record on the EV connector, Action-linked (OPEN)"),
    "part-ev-worstcase": (W504 + " [worstcase :18903]", EV + "worstcase requests with 160-code-point title/narrative/activity (WR-000004; overviews WR-000002/6)"),
    "part-ev-forbidden": (W504 + " [forbidden :18906]", EV + "walkthrough principal granted no Site: the global request route still answers 200 (B19-15)"),
    "part-ev-unavailable": (W504 + " [unavailable :18907, stopped by attest]", EV + "whole API stopped: browser proxy 503"),
    "part-cold-positive": (W502 + " [positive :8971]", COLD + "WR-000002 COMPLETED, raised from INC-000001, Finding/Action linked, with record"),
    "part-cold-worstcase": (W502 + " [worstcase :8972]", COLD + "WR-000002 COMPLETED and WR-000004 OPEN with 160-code-point title/activity"),
    "part-cold-forbidden": (W502 + " [forbidden :8976]", COLD + "walkthrough principal granted no Site: the global request route still answers 200 (B19-15)"),
})
CHECK = ["part-links"]
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
        elif "B19-07" in found:
            verdict = "refused/no-fetch: typed copy; empty shell panels and Reload/Open site issues (B19-07)"
        elif not count_match:
            verdict = "panel count differs from the mock"
        else:
            over = [x for x in panels if x["over_1_3"]]
            verdict = "panel count/order match; differences listed as proposals" + (f"; {len(over)} panel(s) >1.3x (measured reasons in B19-11)" if over else "") + ("; console warning (B19-08)" if a.get("consoleErrors") else "")
        pairs.append({
            "screen": p["screen"], "case": p["case"], "width": width, "viewport": p["viewport"], "part": part,
            "route": p["app_url"].replace("http://127.0.0.1:5189", ""), "app_url": p["app_url"], "mock": "frontend/mockups/v69/index.html" + p["mock_hash"],
            "producer_command": PRODUCERS[part][0], "producer_mode": PRODUCERS[part][1],
            "revision": "731126a9 (product code = fddf5cad)", "captured_at": ev["captured_at"],
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
order = ["wr-overview", "wr-record", "wr-history"]
pairs.sort(key=lambda x: (order.index(x["screen"]), x["case"], -int(x["width"])))
cross = []
for part in CHECK:
    chk = json.loads((ROOT / part / "evidence.json").read_text(encoding="utf-8"))
    cross += [{"screen": p["screen"], "case": p["case"], "viewport": p["viewport"], "app_url": p["app_url"], "app_titles": p["app"]["titles"],
          "overview_cards": p["app"]["cold"]["cardLinks"], "console_errors": p["app"].get("consoleErrors", []),
          "app_image": f"{part}/{p['app_image']}", "mock_image": f"{part}/{p['mock_image']}", "finding": "B19-12/B19-14 link check"} for p in chk["pairs"] if p["screen"] == "link-check"]
out = {"batch": "19", "name": "W6 work request", "ids": order, "frozen_main": "731126a9 (product code identical to fddf5cad)", "branch": "audit/batch-19",
       "api": "http://127.0.0.1:18701-18707 (W504 walkthrough serve, W504_API_PORT_BASE=18700)", "frontend": "http://127.0.0.1:5189 (vite dev)",
       "viewports": ["1440x1000", "390x900"], "capture_tool": ".agent/post-W6-audit/batch-19/tools/capture-b19.mjs (capture-only)",
       "pair_count": len(pairs), "differences": diffs, "pairs": pairs, "cross_check_not_counted": cross}
(ROOT / "batch-19.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
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
rows.append("<h2 id='cross-check'>Link check (not counted): unknown request sub-tab addresses, global Maintenance row link</h2>")
for c in cross:
    rows.append(f"<section><h3>{c['screen']} · {e(c['case'])} · {c['viewport']}</h3><p><code>{e(c['app_url'])}</code> · {c['finding']}</p>"
                f"<div class=pair><figure><figcaption>App</figcaption><img loading=lazy src='{c['app_image']}'></figure><figure><figcaption>Mock</figcaption><img loading=lazy src='{c['mock_image']}'></figure></div></section>")
dl = "".join(f"<tr id='{d['id']}'><td>{d['id']}</td><td>{e(', '.join(d['screens']) or 'link check')}</td><td>{e(d['what'])}</td><td>{e(d['disp'])}</td></tr>" for d in diffs)
(ROOT / "index.html").write_text(
    "<!doctype html><meta charset=utf-8><title>Post-W6 audit batch 19</title><style>body{font:13px system-ui;margin:16px}"
    ".pair{display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:start}img{width:100%;border:1px solid #ccc}figure{margin:0}"
    "td{border-top:1px solid #ddd;padding:4px;vertical-align:top}</style>"
    f"<h1>Post-W6 audit batch 19 (W6 work request) · main 731126a9 (product = fddf5cad) · {len(pairs)} pairs</h1>"
    f"<p>Screens: {' · '.join(f'<a href=#{s}>{s}</a>' for s in order)} · <a href=#cross-check>cross-check</a>. All dispositions are PROPOSALS for the Architect.</p>"
    f"<table><tr><th>ID</th><th>Screens</th><th>Difference</th><th>Proposed disposition</th></tr>{dl}</table>" + "".join(rows), encoding="utf-8")
print(len(pairs), "pairs")
