"""Build the post-W6 shell recapture index from each recaptured batch's evidence.json files.

Joins the recapture to selection.json by (batch, screen, case, width). For each pair it records the SHA, the producer,
the panel titles and order (against frozen), overflow, clipping and closed heights. It checks the closed heights
against the Q23 caps, and the other panels against frozen + 10% (preflight E: undocketed panels). It writes
index.json and index.md.
"""
import json, pathlib, re, collections
HERE = pathlib.Path(__file__).parent
sel = json.load(open(HERE / "selection.json"))["pairs"]
CAPS = {  # Q23: (screen, panel title) -> {width: cap}
    ("evidence-analysis", "Accepted records behind the conclusions"): {"1440": 1200, "390": 1800},
    ("foundation", "Identity and operating obligations"): {"1440": 850, "390": 1050},
}
OPEN_CASE = re.compile(r"all-open|open|expanded", re.I)

def width_of(v):
    s = str(v)
    return "1440" if "1440" in s else "390" if "390" in s else s

got = {}
for f in sorted(HERE.glob("batch-*/**/evidence*.json")):
    batch = int(re.search(r"batch-(\d+)", str(f)).group(1))
    e = json.load(open(f, encoding="utf-8"))
    for p in e.get("pairs", []):
        k = (batch, p["screen"], p["case"], width_of(p["viewport"]))
        got[k] = (e.get("revision"), str(f.relative_to(HERE)).replace("\\", "/"), p)

rows, problems = [], []
for s in sel:
    k = (s["batch"], s["screen"], s["case"], s["width"])
    r = {"batch": s["batch"], "screen": s["screen"], "case": s["case"], "width": s["width"], "tags": s["tags"],
         "producer": s["producer"][:140], "route": s["route"]}
    if k not in got:
        r["status"] = "not captured"; rows.append(r); continue
    rev, src, p = got[k]
    a = p.get("app") or {}
    titles = a.get("titles") or []
    heights = {x.get("title"): round(x.get("h") or 0) for x in a.get("panels") or []}
    r.update(sha=rev, evidence=src, app_image=p.get("app_image"), titles=titles,
             titles_match=titles == s["frozen_titles"], overflowX=a.get("overflowX"),
             clipped=a.get("clipped") or [], console_errors=len(a.get("consoleErrors") or []), heights=heights)
    flags = []
    if (a.get("overflowX") or 0) > 0: flags.append(f"overflowX {a.get('overflowX')}")
    if r["console_errors"]: flags.append(f"{r['console_errors']} console errors")
    is_open = bool(OPEN_CASE.search(s["case"]))
    frozen = dict(zip(s["frozen_titles"], s["frozen_heights"]))
    for t, h in heights.items():
        cap = CAPS.get((s["screen"], t), {}).get(s["width"])
        if cap is not None and s["screen"] == "evidence-analysis" and s["batch"] != 2:
            cap = None  # Q23 caps the mini evidence-analysis only (batch 2); other domains keep their docket
        if is_open: continue
        if cap is not None:
            if h > cap: flags.append(f"CAP {t} {h}>{cap}")
        elif frozen.get(t) and h > frozen[t] * 1.10 and h - frozen[t] > 20:
            flags.append(f"grew {t} {frozen[t]}->{h}")
    if not r["titles_match"]: flags.append("titles changed")
    r["flags"] = flags; r["status"] = "flag" if flags else "ok"
    rows.append(r)

json.dump({"pairs": rows}, open(HERE / "index.json", "w", encoding="utf-8"), indent=1)
c = collections.Counter(r["status"] for r in rows)
shas = collections.Counter(r.get("sha") for r in rows if r.get("sha"))
md = ["# post-W6 shell recapture index", "",
      f"Selected {len(rows)} pairs (Q24: 176 representative + 230 changed, overlapping). Status: {dict(c)}. SHAs: {dict(shas)}.",
      "Caps (Q23) apply to closed states; cases named open/expanded are exempt. Other panels flag above frozen + 10% and +20 px.",
      "", "| batch | screen | case | w | status | titles = frozen | overflowX | capped/flagged | image |", "|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    capinfo = "; ".join(r.get("flags", [])) or "; ".join(
        f"{t} {h}" for t, h in r.get("heights", {}).items() if (r["screen"], t) in CAPS)
    md.append(f"| {r['batch']} | {r['screen']} | {r['case']} | {r['width']} | {r['status']} | {r.get('titles_match', '')} | "
              f"{r.get('overflowX', '')} | {capinfo} | {r.get('app_image') or ''} |")
(HERE / "index.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(dict(c), dict(shas))
for r in rows:
    if r["status"] != "ok": print(r["batch"], r["screen"], r["case"], r["width"], r["status"], r.get("flags"))
