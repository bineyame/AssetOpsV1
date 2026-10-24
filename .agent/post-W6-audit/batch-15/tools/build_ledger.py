"""Build batch-15.json and index.html from the part-*/evidence.json captures plus differences.json
(reads only; writes only into the batch folder). Adapted from batch-14/tools/build_ledger.py."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
W502 = "tools/w502_cold_work_walkthrough.py --work var/w502b_b15 --tag b15 prepare / serve / attest (ATTEST OK) / drop (unmodified; DBs w502b_<mode>_b15_test; API ports 8971-8977 hard-coded, checked free first); Vite 127.0.0.1:5185 restarted per mode with ASSETOPS_API_PORT=<mode port>; CDP 9525"
SITE = "COLD-LAB-001 (Africa/Addis_Ababa); case window 23-25 Oct UTC days (manifest case_reads); Action detail reads = manifest detail_reads"
PRODUCERS = {
    "part-positive": (W502 + " [positive :8971]", SITE + ". positive mode: 1 INC, 1 completed WR + record, ACT-000001 with intent and both case links. Cases: current (from,to only, CURRENT), positive-cutoff (returned known_at, HISTORICAL), historical (K3), zero (15-22 Oct), refused-reversed, refused-span-32d, no-window, all-open (viewer-only details.open). Action: positive (CURRENT, WR COMPLETED), all-open (Finding version open), not-linked (known_at=K1, HISTORICAL, no intent/link), historical (K3), not-found (nil UUID), invalid-known-at (client refusal), future-known-at (server 422)"),
    "part-worstcase": (W502 + " [worstcase :8972]", SITE + ". worstcase mode: 5 INC/5 WR rows (160-code-point text; WR COMPLETED + 4 OPEN), worst-case Action 1 (160-code-point title and owner, no intent, no link); all-open = every <details> opened"),
    "part-pending": (W502 + " [pending :8973]", SITE + ". pending mode: PENDING_RECOMPUTE at the returned cutoff"),
    "part-stale": (W502 + " [stale :8974]", SITE + ". stale mode: STALE_SOURCE"),
    "part-unknown": (W502 + " [unknown :8975]", SITE + ". unknown mode: ruled seeded empty-support selection (UNKNOWN)"),
    "part-forbidden": (W502 + " [forbidden :8976]", SITE + ". real 403 SITE_SCOPE_FORBIDDEN (ungranted operator principal; W4 case router and domain-work router)"),
    "part-unavailable": (W502 + " [unavailable :8977]", SITE + ". real 503 WORK_STORE_UNAVAILABLE (work routers on an unreachable DB, Site read healthy); rerun with one warm-up navigation (B15-13)"),
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
        found = [d["id"] for d in diffs if p["screen"] in d["screens"] and (not d.get("cases") or p["case"] in d["cases"])]
        count_match = len(a["titles"]) == len(m["titles"])
        if a.get("consoleErrors") and not a["titles"]:
            verdict = "FAIL: page crashed (blank)"
        elif not count_match and a["titles"] == ["(untitled)"]:
            verdict = "state panel: one untitled panel in place of the two loaded panels (R101 D2); copy B15-04"
        elif not count_match:
            verdict = "panel count differs from the mock"
        else:
            over = [x for x in panels if x["over_1_3"]]
            verdict = "panel count/order/titles match; differences listed as proposals" + (f"; {len(over)} panel(s) >1.3x, measured reason in B15-09" if over else "")
        b = a.get("b15", {})
        pairs.append({
            "screen": p["screen"], "case": p["case"], "width": width, "viewport": p["viewport"], "part": part,
            "route": p["app_url"].replace("http://127.0.0.1:5185", ""), "app_url": p["app_url"], "mock": "frontend/mockups/v69/index.html" + p["mock_hash"],
            "producer_command": PRODUCERS[part][0], "producer_mode": PRODUCERS[part][1],
            "revision": "1e3e9e8a (product code = fddf5cad)", "captured_at": ev["captured_at"],
            "app_titles": a["titles"], "mock_titles": m["titles"], "title_order_match": a["titles"] == m["titles"], "panel_count_match": count_match,
            "panels": panels, "max_ratio": max([x["ratio"] or 0 for x in panels], default=None),
            "app_page_h": a["pageH"], "mock_page_h": m["pageH"], "overflow_x": a["overflowX"],
            "header": {"app": a.get("header"), "mock": m.get("header"), "app_dark_block": (a.get("dark") or [None])[0], "app_main_top": a.get("mainTop")},
            "h1": {"app": a.get("h1"), "mock": m.get("h1")}, "breadcrumb": {"app": b.get("crumbs"), "mock": m.get("b15", {}).get("crumbs")},
            "fonts": {"app": a["fonts"], "mock": m["fonts"]}, "panel_text_sizes": {"app": a.get("pSizes"), "mock": m.get("pSizes")},
            "tab_rows": {"app": [t["items"] for t in a["tabRows"]], "mock": [t["items"] for t in m["tabRows"]]},
            "strip": b.get("strip"), "notices": a["mini"]["notice"], "window_form": a["cold"]["windowForm"], "plural_1": a["cold"]["plural1"],
            "related_sentence": b.get("related"), "inspect": b.get("inspect"),
            "clipped_text": a["clipped"], "scroll_containers": a["hscroll"], "console_errors": a.get("consoleErrors", []),
            "app_image": f"{part}/{p['app_image']}", "mock_image": f"{part}/{p['mock_image']}",
            "findings": found, "reviewer_verdict": verdict,
        })
order = ["cold-work-incidents", "cold-work-maintenance", "cold-action"]
pairs.sort(key=lambda x: (order.index(x["screen"]), x["case"], -int(x["width"])))
out = {"batch": "15", "name": "W5 cold cases/Action", "ids": order, "frozen_main": "1e3e9e8a (product code identical to fddf5cad)", "branch": "audit/batch-15",
       "api": "http://127.0.0.1:8971-8977 (W502 walkthrough serve, hard-coded)", "frontend": "http://127.0.0.1:5185 (vite dev)",
       "viewports": ["1440x1000", "390x900"], "capture_tool": ".agent/post-W6-audit/batch-15/tools/capture-b15.mjs (capture-only)",
       "pair_count": len(pairs), "differences": diffs, "pairs": pairs}
(ROOT / "batch-15.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
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
dl = "".join(f"<tr id='{d['id']}'><td>{d['id']}</td><td>{e(', '.join(d['screens']) or 'capture')}</td><td>{e(d['what'])}</td><td>{e(d['disp'])}</td></tr>" for d in diffs)
(ROOT / "index.html").write_text(
    "<!doctype html><meta charset=utf-8><title>Post-W6 audit batch 15</title><style>body{font:13px system-ui;margin:16px}"
    ".pair{display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:start}img{width:100%;border:1px solid #ccc}figure{margin:0}"
    "td{border-top:1px solid #ddd;padding:4px;vertical-align:top}</style>"
    f"<h1>Post-W6 audit batch 15 (W5 cold cases/Action) · main 1e3e9e8a (product = fddf5cad) · {len(pairs)} pairs</h1>"
    f"<p>Screens: {' · '.join(f'<a href=#{s}>{s}</a>' for s in order)}. All dispositions are PROPOSALS for the Architect.</p>"
    f"<table><tr><th>ID</th><th>Screens</th><th>Difference</th><th>Proposed disposition</th></tr>{dl}</table>" + "".join(rows), encoding="utf-8")
print(len(pairs), "pairs")
