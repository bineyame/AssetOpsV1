"""caps.py <inspect.json>... : per (panel, width) the real and synthetic closed heights (capped and natural), the
inner scroll regions, clipping and doc overflow; plus bar/chip contrast. Synthetic rows are layout evidence only."""
import json, math, sys
from collections import defaultdict
peak = defaultdict(lambda: {"capped": 0, "natural": 0, "maxH": None, "src": "", "clipped": 0, "doc": 0, "scroll_ok": True, "unverified": []})
bars, chips = [], []
for f in sys.argv[1:]:
    for r in json.load(open(f, encoding="utf-8"))["results"]:
        w = r["width"]
        for b in r.get("bars", []): bars.append((r["screen"], r["case"], w, b["cls"], b["ratioTrack"], b["ratioPanel"]))
        for c in r.get("chips", []): chips.append((r["screen"], w, c["tone"], c["text"], c["ratio"]))
        for cap in r.get("caps", []):
            variants = [("real", cap["real"]["closed"] if cap.get("real") else None)] + [(k, v) for k, v in cap.items() if isinstance(v, dict) and k not in ("real",) and "panelH" in v]
            for name, m in variants:
                if not m: continue
                if name != "real" and not m.get("verified"):
                    peak[(cap["panel"], w)]["unverified"].append(name); continue
                if name.startswith("rows160") or name == "firstcell160": continue  # all-cell overstress / first-cell only: reference, not the guide stress
                p = peak[(cap["panel"], w)]
                if m["panelH"] > p["capped"]: p["capped"] = m["panelH"]
                if m.get("naturalH", 0) > p["natural"]: p["natural"], p["src"] = m["naturalH"], f"{r['screen']}/{r['case']}/{name}"
                p["maxH"] = m.get("maxH"); p["clipped"] += len(m.get("clipped", [])); p["doc"] = max(p["doc"], m.get("docOverflowX", 0))
                for s in m.get("scrollers", []):
                    if not s["focusable"] or not s["label"]: p["scroll_ok"] = False
print("panel | width | ruled max-height | closed peak (capped) | natural peak | provisional 50*ceil(nat*1.15/50) | clipped | doc | scroll regions focusable+labelled | source")
for (panel, w), p in sorted(peak.items()):
    prov = 50 * math.ceil(p["natural"] * 1.15 / 50) if p["natural"] else None
    print(f"{panel} | {w} | {p['maxH']} | {p['capped']} | {p['natural']} | {prov} | {p['clipped']} | {p['doc']} | {p['scroll_ok']} | {p['src']}")
if bars:
    lo = min(bars, key=lambda b: b[4] or 99)
    print(f"bars measured {len(bars)}; min fill/track ratio {lo[4]} ({lo[3]} {lo[0]}/{lo[1]} {lo[2]}); below 3:1: {[b for b in bars if (b[4] or 0) < 3]}")
if chips:
    lo = min(chips, key=lambda c: c[4] or 99)
    print(f"chips measured {len(chips)}; min text ratio {lo[4]} ({lo[2]} '{lo[3]}' {lo[0]} {lo[1]}); below 4.5: {sorted(set((c[2], c[3], c[4]) for c in chips if (c[4] or 0) < 4.5))}")
