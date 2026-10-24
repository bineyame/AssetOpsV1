"""Build batch-11.json and index.html from the part-*/evidence.json captures plus differences.json
(reads only; writes only into the batch folder). Adapted from batch-09/tools/build_ledger.py."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
W303 = ("W303_DB=assetops_audit_b11_test {env} PYTHONPATH=backend;gateway;simulator;contracts;host "
        ".venv/Scripts/python.exe -m pytest .agent/W3-03-evidence/test_serve_portfolio.py -s -p no:cacheprovider "
        "(API 127.0.0.1:9781, hard-coded by the producer); Vite 127.0.0.1:5181 ASSETOPS_API_PORT=9781")
W302 = ("PYTHONPATH=backend;gateway;simulator;contracts;host .venv/Scripts/python.exe .agent/W3-02-evidence/serve.py "
        "(DB w302j_test and API 127.0.0.1:9751, both hard-coded by the producer); Vite 127.0.0.1:5181 ASSETOPS_API_PORT=9751")
FIX = "W3-03 clean four-Site fixture build_portfolio_fixture (KOBO-001 W1 priced, COLD-LAB-001 excursion drained, EV-LAB-001/002 gross-tariff), frozen read clock 2026-10-30T09:03Z"
PRODUCERS = {
    "part-w303-positive": (W303.format(env="W303_ROUTER=capture"), FIX + "; request [2026-10-06,2026-10-07)"),
    "part-w303-guards": (W303.format(env="W303_ROUTER=capture"), FIX + "; reversed window, 36-day window, bare route (default last 7 complete days)"),
    "part-w303-empty": (W303.format(env="W303_ROUTER=capture") + "; POST /__capture/mode?tenant=foreign", FIX + "; foreign tenant with zero authorized Sites"),
    "part-w303-401": (W303.format(env="W303_ROUTER=capture") + "; POST /__capture/mode?auth=deny", FIX + "; capture router refuses authentication"),
    "part-w303-partial": (W303.format(env="W303_ROUTER=capture") + "; POST /__capture/empty-site", FIX + " + authorized unselected W303-EMPTY-001 EV Site"),
    "part-w303-historical": (W303.format(env="W303_ROUTER=capture"), FIX + " + W303-EMPTY-001; known_at=2026-09-30T00:00Z"),
    "part-w303-pending": (W303.format(env="W303_COLD_DRAIN=0"), "W3-03 fixture, a_lineless_cold variant (cold_drain=False); fresh reset of the same DB"),
    "part-w303-503": (W303.format(env="W303_NO_CURSOR_KEY=1"), "W3-03 clean fixture, cursor key unset (fresh process)"),
    "part-w302-positive": (W302, "W3-02 harness: KOBO-001 S4 F01/F02 + S6 Action chain, COLD-LAB-001 late-reading settled, EV-LAB-001 interrupted + golden tariff + money, FOREIGN-001; request [10-06,10-07)"),
    "part-w302-partial-week": (W302 + "; POST /__capture/empty-site", "W3-02 harness + W301-EMPTY-001; request [10-05,10-12)"),
    "part-w302-pending": (W302 + "; POST /__capture/late-kobo", "W3-02 harness after one late accepted KOBO reading (open job); request [10-06,10-07)"),
}
LINKS = "part-w303-links"
diffs = json.loads((ROOT / "differences.json").read_text(encoding="utf-8"))
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
        refusal = not a["titles"]
        if a.get("consoleErrors"):
            verdict = "FAIL: console error"
        elif refusal:
            verdict = "refusal state: no panels by design (refusal copy only); see " + ", ".join(found)
        elif not count_match:
            verdict = "panel count differs from the mock"
        else:
            over = [x for x in panels if x["over_1_3"]]
            verdict = "panel count/order/titles match; differences listed as proposals" + (f"; {len(over)} panel(s) >1.3x" if over else "; no panel >1.3x")
        pairs.append({
            "screen": p["screen"], "case": p["case"], "width": width, "viewport": p["viewport"], "part": part,
            "route": p["app_url"].replace("http://127.0.0.1:5181", ""), "app_url": p["app_url"], "mock": "frontend/mockups/v69/index.html" + p["mock_hash"],
            "producer_command": PRODUCERS[part][0], "producer_mode": PRODUCERS[part][1],
            "revision": "0fc2b048 (product code = fddf5cad)", "captured_at": ev["captured_at"],
            "app_titles": a["titles"], "mock_titles": m["titles"], "title_order_match": a["titles"] == m["titles"], "panel_count_match": count_match,
            "panels": panels, "max_ratio": max([x["ratio"] or 0 for x in panels], default=None),
            "app_page_h": a["pageH"], "mock_page_h": m["pageH"], "overflow_x": a["overflowX"],
            "header": {"app": a.get("header"), "mock": m.get("header"), "app_dark_block": (a.get("dark") or [None])[0], "app_main_top": a.get("mainTop")},
            "h1": {"app": a.get("h1"), "mock": m.get("h1")}, "fonts": {"app": a["fonts"], "mock": m["fonts"]},
            "panel_text_sizes": {"app": a.get("pSizes"), "mock": m.get("pSizes")},
            "clipped_text": a["clipped"], "scroll_containers": a["hscroll"], "console_errors": a.get("consoleErrors", []),
            "app_links": a.get("links", []), "closed_disclosures": [{k: d[k] for k in ("summary", "bodyLen", "scrollH")} for d in a.get("closedDetails", [])],
            "app_image": f"{part}/{p['app_image']}", "mock_image": f"{part}/{p['mock_image']}",
            "findings": found, "reviewer_verdict": verdict,
        })
order = ["globalevidence", "globalfinancials", "portfolio"]
pairs.sort(key=lambda x: (order.index(x["screen"]), x["part"], x["case"], -int(x["width"])))
lk = json.loads((ROOT / LINKS / "evidence.json").read_text(encoding="utf-8"))
targets = {t["id"]: t for t in json.loads((ROOT / "tools" / "targets-w303-links.json").read_text(encoding="utf-8"))}
links = [{"check": p["screen"], "from_screen": p["case"], "link_text": targets[p["screen"]]["src"], "url": p["app_url"].replace("http://127.0.0.1:5181", ""),
          "landed_h1": p["app"]["h1"] and p["app"]["h1"]["text"], "landed_titles": p["app"]["titles"],
          "landed_tabs": [t["items"] for t in p["app"]["tabRows"]], "landed_text": p["app"].get("mainText", "")[:300], "image": f"{LINKS}/{p['app_image']}"} for p in lk["pairs"]]
out = {"batch": "11", "name": "W3 estate composition", "ids": order, "frozen_main": "0fc2b048 (product code identical to fddf5cad)", "branch": "audit/batch-11",
       "api": "W3-03 producer 127.0.0.1:9781 / W3-02 producer 127.0.0.1:9751 (ports hard-coded in the unmodified producers)",
       "frontend": "http://127.0.0.1:5181 (vite dev, ASSETOPS_API_PORT per phase)", "cdp": 9521,
       "viewports": ["1440x1000", "390x900"], "capture_tool": ".agent/post-W6-audit/batch-11/tools/capture-b11.mjs (capture-only)",
       "pair_count": len(pairs), "representative_pairs": [f"{p['screen']}/{p['case']}/{p['width']}" for p in pairs if p["case"] == "w303-positive"],
       "differences": diffs, "pairs": pairs, "link_destination_checks_not_counted": links}
(ROOT / "batch-11.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
e = html.escape
rows = []
for s in order:
    rows.append(f"<h2 id='{s}'>{s}</h2>")
    for p in [x for x in pairs if x["screen"] == s]:
        pan = "".join(f"<li>{e(x['title'])} {x['app_h']}/{x['mock_h']} = {x['ratio']}{' <b>&gt;1.3</b>' if x['over_1_3'] else ''}</li>" for x in p["panels"])
        fl = ", ".join(f"<a href='#{f}'>{f}</a>" for f in p["findings"])
        rows.append(f"<section><h3>{s} · {e(p['case'])} · {p['width']}</h3><p><code>{e(p['route'])}</code><br>{e(p['producer_mode'])}<br>{e(p['reviewer_verdict'])}<br>Findings: {fl}</p>"
                    f"<p>App: {e(' | '.join(p['app_titles']) or '(refusal)')}<br>Mock: {e(' | '.join(p['mock_titles']))}</p><ul>{pan}</ul>"
                    f"<div class=pair><figure><figcaption>App</figcaption><img loading=lazy src='{p['app_image']}'></figure><figure><figcaption>Mock</figcaption><img loading=lazy src='{p['mock_image']}'></figure></div></section>")
rows.append("<h2 id='links'>Link destination checks (1440, app only, not counted as pairs)</h2><table><tr><th>Check</th><th>From</th><th>Link</th><th>URL</th><th>Landed on</th></tr>")
for l in links:
    rows.append(f"<tr><td><a href='{l['image']}'>{l['check']}</a></td><td>{l['from_screen']}</td><td>{e(l['link_text'])}</td><td><code>{e(l['url'][:120])}</code></td>"
                f"<td>{e(str(l['landed_h1']))}: {e(' | '.join(l['landed_titles']))}<br><small>{e(l['landed_text'][:200])}</small></td></tr>")
rows.append("</table>")
dl = "".join(f"<tr id='{d['id']}'><td>{d['id']}{' ('+d['severity']+')' if d.get('severity') else ''}</td><td>{e(', '.join(d['screens']) or 'cross-check')}</td><td>{e(d['what'])}</td><td>{e(d['disp'])}</td></tr>" for d in diffs)
(ROOT / "index.html").write_text(
    "<!doctype html><meta charset=utf-8><title>Post-W6 audit batch 11</title><style>body{font:13px system-ui;margin:16px}"
    ".pair{display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:start}img{width:100%;border:1px solid #ccc}figure{margin:0}"
    "td{border-top:1px solid #ddd;padding:4px;vertical-align:top}</style>"
    f"<h1>Post-W6 audit batch 11 (W3 estate composition) · main 0fc2b048 (product = fddf5cad) · {len(pairs)} pairs</h1>"
    f"<p>Screens: {' · '.join(f'<a href=#{s}>{s}</a>' for s in order)} · <a href=#links>link checks</a>. All dispositions are PROPOSALS for the Architect.</p>"
    f"<table><tr><th>ID</th><th>Screens</th><th>Difference</th><th>Proposed disposition</th></tr>{dl}</table>" + "".join(rows), encoding="utf-8")
print(len(pairs), "pairs,", len(links), "link checks")
