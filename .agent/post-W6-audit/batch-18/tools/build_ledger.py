"""Build batch-18.json and index.html from the part-*/evidence.json captures plus differences.json
(reads only; writes only into the batch folder). Adapted from batch-15/tools/build_ledger.py."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
W6 = "python tools/w601_seed.py --db assetops_w601_b18<tag>_test --fixture <f> --clock <c> (unmodified); plain product API assetops_backend.main:app (W6-01 run_state.sh form, per-start random ASSETOPS_WORK_CURSOR_KEY_HEX) on 127.0.0.1:<port>; Vite 127.0.0.1:5188 restarted per phase with ASSETOPS_API_PORT; CDP 9528"
WIN = "window [2026-10-14, 2026-10-21) UTC unless stated"
COLD = "tools/w502_cold_work_walkthrough.py --work var/w502b_b18 --tag b18 prepare --modes positive,worstcase (unmodified; DBs w502b_<mode>_b18_test) read by the plain product API on 18801/18802; window [2026-10-18, 2026-10-25)"
EV = "tools/w504_ev_work_walkthrough.py --work var/w504a_b18 --tag b18 prepare/serve/attest with W504_API_PORT_BASE=18800 (unmodified; DBs w504a_<mode>_b18_test) read by the plain product API on 18808/18809; window [2026-10-18, 2026-10-25)"
PRODUCERS = {
    "part-inc": (W6.replace("<tag>", "inc").replace("<f>", "incidents").replace("<c>", "2026-10-21T12:00:00Z").replace("<port>", "18801"), WIN + ". 6 demo incidents (KOBO-001 x4, KOBO-002 x2) + 1 other-tenant; positive, all-open, page-two (cursor from a read-only GET), refused (reversed, 32-day, one bound, bad known_at), no-window"),
    "part-maint": (W6.replace("<tag>", "maint").replace("<f>", "maintenance").replace("<c>", "2026-10-20T12:00:00Z").replace("<port>", "18802"), WIN + ". 7 demo requests in every reachable state + 1 other-tenant"),
    "part-prev": (W6.replace("<tag>", "prev").replace("<f>", "preventive").replace("<c>", "2026-10-20T12:00:00Z").replace("<port>", "18803"), WIN + ". 5 demo DRAFT plans (2 RUN_HOURS)"),
    "part-op": (W6.replace("<tag>", "op").replace("<f>", "operational").replace("<c>", "2026-10-21T12:00:00Z").replace("<port>", "18804"), WIN + ". 7 in-window records (+1 out-of-window SITE_VISIT, +1 other tenant), kind filters, historical known_at=2026-10-21T12:00:00Z, invalid kind; incidents one-row (the fixture's single incident)"),
    "part-zero": (W6.replace("<tag>", "zero").replace("<f>", "zero").replace("<c>", "2026-10-21T12:00:00Z").replace("<port>", "18805"), WIN + ". exact all-zero"),
    "part-hist": (W6.replace("<tag>", "hist").replace("<f>", "historical").replace("<c>", "2026-10-21T12:00:00Z").replace("<port>", "18806"), WIN + ". incidents known_at=2026-10-21T12:00:00Z vs current; preventive root known_at=2026-10-21T12:00:03Z vs correction head"),
    "part-stress": (W6.replace("<tag>", "stress").replace("<f>", "stress").replace("<c>", "2026-10-21T12:00:00Z").replace("<port>", "18807"), WIN + " (maintenance [2026-10-15, 2026-10-22): the stress request is created 21 Oct). 200-char incident title + 128-char owner, 5 short incidents; long request/plan/4000-char record; all-open"),
    "part-linked": (W6.replace("<tag>", "linked").replace("<f>", "linked").replace("<c>", "2026-10-20T12:00:00Z").replace("<port>", "18808"), WIN + ". real S4 Finding + S6 Action pinned to one incident and two requests"),
    "part-absent": ("plain product API on 18809 with DATABASE_URL naming assetops_w601_b18absent_test, never created (W6-01 A2/B2/B3/E2 503 precedent)", "real 503 WORK_STORE_UNAVAILABLE"),
    "part-scope": ("uvicorn api_empty_scope:app --app-dir .agent/W6-01-evidence/E2 (reviewed W6-01e TEST-ONLY composition, deny_every_site) over assetops_w601_b18op_test on 18809", "EMPTY_SCOPE: every Site denied; the global roots have no 403, this is their access-refusal state"),
    "part-cold": (COLD + " [positive :18801]", "COLD-LAB-001: 1 INC, 1 completed WR with record, ACT-000001 links; default-window case = bare route"),
    "part-coldwc": (COLD + " [worstcase :18802]", "COLD-LAB-001: five INC and five WR with 160-code-point text (the five-160-char-row worst case)"),
    "part-ev": (EV + " [positive :18808]", "EV-LAB-001: attested INC + WR (c1 EV connector asset) linked to ACT-000001; default-window case = bare route"),
    "part-evwc": (EV + " [worstcase :18809]", "EV-LAB-001: five INC and five WR with long titles"),
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
            verdict = "state panel differs"
        elif not count_match:
            verdict = "panel count differs from the mock"
        else:
            over = [x for x in panels if x["over_1_3"]]
            verdict = "panel count/order/titles match; differences listed as proposals" + (f"; {len(over)} panel(s) >1.3x, measured reason in B18-16" if over else "")
        b = a.get("b18", {}); b15 = a.get("b15", {})
        pairs.append({
            "screen": p["screen"], "case": p["case"], "width": width, "viewport": p["viewport"], "part": part,
            "route": p["app_url"].replace("http://127.0.0.1:5188", ""), "app_url": p["app_url"], "mock": "frontend/mockups/v69/index.html" + p["mock_hash"],
            "producer_command": PRODUCERS[part][0], "producer_mode": PRODUCERS[part][1],
            "revision": "f99bca2e (product code = fddf5cad)", "captured_at": ev["captured_at"],
            "app_titles": a["titles"], "mock_titles": m["titles"], "title_order_match": a["titles"] == m["titles"], "panel_count_match": count_match,
            "panels": panels, "max_ratio": max([x["ratio"] or 0 for x in panels], default=None),
            "app_page_h": a["pageH"], "mock_page_h": m["pageH"], "overflow_x": a["overflowX"],
            "header": {"app": a.get("header"), "mock": m.get("header"), "app_dark_block": (a.get("dark") or [None])[0], "app_main_top": a.get("mainTop")},
            "h1": {"app": a.get("h1"), "mock": m.get("h1")}, "breadcrumb": {"app": b15.get("crumbs"), "mock": m.get("b15", {}).get("crumbs")},
            "fonts": {"app": a["fonts"], "mock": m["fonts"]}, "panel_text_sizes": {"app": a.get("pSizes"), "mock": m.get("pSizes")},
            "tab_rows": {"app": [t["items"] for t in a["tabRows"]], "mock": [t["items"] for t in m["tabRows"]]},
            "status_line": b.get("status"), "showing": b.get("showing"), "pager": b.get("pager"), "plural_1": b.get("plural1"), "ev_connector_hits": b.get("evConnector"),
            "asset_labels": b.get("assetLabels"), "site_links": b.get("siteLinks"), "row_links": [x["rowLinks"] for x in a["panels"][:1]], "state_alerts": b.get("alerts"),
            "clipped_text": a["clipped"], "scroll_containers": a["hscroll"], "console_errors": a.get("consoleErrors", []),
            "app_image": f"{part}/{p['app_image']}", "mock_image": f"{part}/{p['mock_image']}",
            "findings": found, "reviewer_verdict": verdict,
        })
order = ["incidents", "maintenance", "maintenance-preventive", "oprecords"]
pairs.sort(key=lambda x: (order.index(x["screen"]), x["case"], -int(x["width"])))
out = {"batch": "18", "name": "W6 global lists", "ids": order, "frozen_main": "f99bca2e (product code identical to fddf5cad)", "branch": "audit/batch-18",
       "api": "http://127.0.0.1:18801-18809 (plain product API over producer DBs)", "frontend": "http://127.0.0.1:5188 (vite dev)", "link_checks": ["part-linkcold", "part-linkev", "part-linkmini"],
       "viewports": ["1440x1000", "390x900"], "capture_tool": ".agent/post-W6-audit/batch-18/tools/capture-b18.mjs (capture-only)",
       "pair_count": len(pairs), "differences": diffs, "pairs": pairs}
(ROOT / "batch-18.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
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
    "<!doctype html><meta charset=utf-8><title>Post-W6 audit batch 18</title><style>body{font:13px system-ui;margin:16px}"
    ".pair{display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:start}img{width:100%;border:1px solid #ccc}figure{margin:0}"
    "td{border-top:1px solid #ddd;padding:4px;vertical-align:top}</style>"
    f"<h1>Post-W6 audit batch 18 (W6 global lists) · main f99bca2e (product = fddf5cad) · {len(pairs)} pairs</h1>"
    f"<p>Screens: {' · '.join(f'<a href=#{s}>{s}</a>' for s in order)}. All dispositions are PROPOSALS for the Architect.</p>"
    f"<table><tr><th>ID</th><th>Screens</th><th>Difference</th><th>Proposed disposition</th></tr>{dl}</table>" + "".join(rows), encoding="utf-8")
print(len(pairs), "pairs")
