"""Summarise the W2-cold recapture evidence.json files: overflow, clipping, console, panel order vs mock,
MOCK DEVIATION label visibility, refusal copy (capture-only bookkeeping). Writes summary.json."""
import json, pathlib, sys
R = pathlib.Path(__file__).resolve().parents[1]
rows = []
for ev in sorted(R.glob("part-*/evidence.json")):
    d = json.loads(ev.read_text(encoding="utf8"))
    for p in d["pairs"]:
        a, m, x = p["app"], p["mock"], p["app"].get("extra", {})
        rows.append({"part": ev.parent.name, "screen": p["screen"], "case": p["case"], "w": p["viewport"].split("x")[0],
            "url": p["app_url"], "revision": d.get("revision"), "overflowX": a["overflowX"], "clipped": a["clipped"],
            "console": a.get("consoleErrors", []), "titles": a["titles"], "mock_titles": m["titles"],
            "order_match": a["titles"] == m["titles"],
            "closed_heights": {pp["title"]: pp["h"] for pp in a["panels"]},
            "labels": {k: len(v) for k, v in x.get("labels", {}).items()}, "sentences": x.get("sentenceCounts"),
            "windowTitle": x.get("windowTitle"), "notAssessed": x.get("notAssessed"), "banners": x.get("banners"),
            "globalNote": x.get("globalNote"), "tabs": x.get("tabs"), "h1": (a.get("h1") or {}).get("text")})
(R / "summary.json").write_text(json.dumps({"captures": len(rows), "revisions": sorted({str(r["revision"]) for r in rows}), "rows": rows}, indent=1), encoding="utf8")
print("captures", len(rows), "revisions", sorted({str(r["revision"]) for r in rows}))
for r in rows:
    flags = []
    if r["overflowX"] > 0: flags.append(f"ovx={r['overflowX']}")
    if r["clipped"]: flags.append(f"clip={[c['text'][:40] for c in r['clipped']]}")
    if r["console"]: flags.append(f"console={r['console']}")
    if not r["order_match"]: flags.append("ORDER")
    lab = "".join(k[-1] if v else "-" for k, v in sorted(r["labels"].items()))
    s = r["sentences"] or {}
    print(f"{r['part']:7} {r['screen']:24} {r['case']:22} {r['w']:4} lab={lab} inv={s.get('invalid')} long={s.get('tooLong')} wt={r['windowTitle']} na={r['notAssessed']} ban={len(r['banners'] or [])} {' '.join(flags)}")
