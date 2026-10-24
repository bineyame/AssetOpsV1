"""Writes targets-<phase>.json (capture URLs only) from the W504 walkthrough manifest (var/w504a_b16/manifest.json).
EV-LAB-001 (Etc/UTC). W5-03 depth reads use the evidence window E (2026-10-06 08:00-09:00Z); the Work window W is the
manifest per-mode work_window_W (current UTC day). Usage: mk_targets.py <phase> <manifest> <outdir>"""
import json, sys
from urllib.parse import urlencode
B = "http://127.0.0.1:5186"
S = "/sites/EV-LAB-001"
M = json.load(open(sys.argv[2], encoding="utf8"))
phase = sys.argv[1]
mode = {"forbidden": "positive", "unavailable": "positive", "links": "positive"}.get(phase, phase)
md = M["modes"][mode]
E = M["windows"]["E"]
DEPTH = f"from={E['from']}&to={E['to']}"
BAD = f"from={E['to']}&to={E['from']}"
EMPTY = DEPTH.replace("2026-10-06", "2026-10-05")
EARLY = DEPTH + "&known_at=2026-10-06T08:30:00Z"
PAGES = {"availability": "/performance/availability", "energy": "/performance/energy", "ev-health": "/health",
         "ev-scenarios": "/ev/financials/scenarios", "ev-work": "/work"}
DEPTHS = ["availability", "energy", "ev-health", "ev-scenarios"]
u = lambda i, q: f"{B}{S}{PAGES[i]}" + (("?" + q) if q else "")
W = md.get("work_window_W") or {}
wq = lambda w, **x: urlencode({"from": w["from"], "to": w["to"], **x})
t = []
if phase == "positive":
    t += [dict(id=i, case="current", url=u(i, DEPTH)) for i in DEPTHS]
    t += [dict(id="ev-work", case="positive", url=u("ev-work", wq(W)))]
    t += [dict(id=i, case="empty-window", url=u(i, EMPTY)) for i in DEPTHS]
    t += [dict(id=i, case="known-at-before-watermark", url=u(i, EARLY)) for i in DEPTHS]
    t += [dict(id="ev-work", case="historical", url=u("ev-work", wq(W, known_at=md["index_known_at"])))]
    t += [dict(id=i, case="refused-reversed", url=u(i, BAD if i != "ev-work" else wq({"from": W["to"], "to": W["from"]}))) for i in PAGES]
    t += [dict(id="ev-work", case="refused-span-32d", url=u("ev-work", "from=2026-09-22T00:00:00Z&to=2026-10-24T00:00:00Z"))]
    t += [dict(id=i, case="no-window", url=u(i, None)) for i in PAGES]
    t += [dict(id=i, case="work-day-window", url=u(i, wq(W))) for i in DEPTHS]
    t += [dict(id=i, case="all-open", url=u(i, DEPTH if i != "ev-work" else wq(W)), openAll=True) for i in PAGES]
elif phase == "zero":
    z = md["work_window_W"]
    from datetime import datetime, timedelta
    prev = (datetime.fromisoformat(z["from"].replace("Z", "+00:00")) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    t += [dict(id="ev-work", case="zero", url=u("ev-work", urlencode({"from": prev, "to": z["from"]})))]
    t += [dict(id="ev-work", case="zero-mode-current-day", url=u("ev-work", wq(z)))]
elif phase == "links":  # app-only link checks, not pairs
    t += [dict(id="link-check", case="ev-overview", url=f"{B}{S}?{DEPTH}", mock="ev"),
          dict(id="link-check", case="ev-overview-bare", url=f"{B}{S}", mock="ev"),
          dict(id="link-check", case="ev-site-findings", url=f"{B}{S}/findings?{DEPTH}", mock="ev-findings"),
          dict(id="link-check", case="ev-sessions", url=f"{B}{S}/performance?{DEPTH}", mock="ev"),
          dict(id="link-check", case="ev-generic-financial-scenarios", url=f"{B}{S}/financials/scenarios?{DEPTH}", mock="ev-scenarios"),
          dict(id="link-check", case="ev-financials", url=f"{B}{S}/ev/financials?{DEPTH}", mock="ev-financials")]
elif phase == "worstcase":
    t += [dict(id="ev-work", case="worstcase", url=u("ev-work", wq(W))),
          dict(id="ev-work", case="worstcase-all-open", url=u("ev-work", wq(W)), openAll=True)]
    t += [dict(id=i, case="worstcase-db", url=u(i, DEPTH)) for i in ["ev-health", "ev-scenarios"]]
elif phase == "unknown":
    t += [dict(id=i, case="unknown-missing-meter", url=u(i, DEPTH)) for i in DEPTHS]
    t += [dict(id=i, case="unknown-missing-meter-all-open", url=u(i, DEPTH), openAll=True) for i in ["energy", "ev-scenarios"]]
    if W: t += [dict(id="ev-work", case="unknown", url=u("ev-work", wq(W)))]
elif phase in ("forbidden", "unavailable"):
    c = {"forbidden": "forbidden-403", "unavailable": "store-unavailable-503"}[phase]
    t += [dict(id="ev-work", case=c, url=u("ev-work", wq(W))), dict(id="availability", case=c, url=u("availability", DEPTH))]
json.dump(t, open(f"{sys.argv[3]}/targets-{phase}.json", "w"), indent=1)
print(phase, len(t))
