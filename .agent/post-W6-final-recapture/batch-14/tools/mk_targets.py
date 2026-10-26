"""Writes targets-<phase>.json (capture URLs only) from the W502 walkthrough manifest (var/w502b_b14/manifest.json).
COLD-LAB-001 (Africa/Addis_Ababa). The W5-01 selected depth window is the manifest `w501.window` (16:00-17:05Z on
23 Oct; stale 16:00-17:30Z); the Work window is the manifest `reads.<name>.query` (UTC days 23-25 Oct)."""
import json, sys
from urllib.parse import urlencode
B = "http://localhost:5184"
S = "/sites/COLD-LAB-001"
M = json.load(open(sys.argv[2], encoding="utf8"))
phase = sys.argv[1]
mode = {"forbidden": "positive", "unavailable": "positive", "links": "positive"}.get(phase, phase)
md = M["modes"][mode]
z = lambda s: s.replace(".000000Z", "Z")
dw = [z(x) for x in md["w501"]["window"]]
DEPTH = f"from={dw[0]}&to={dw[1]}"
BAD = f"from={dw[1]}&to={dw[0]}"
EMPTY = DEPTH.replace("2026-10-23", "2026-10-22")
PAGES = {"cooling": "/performance/cooling", "cold-health": "/health", "cold-scenarios": "/financials/scenarios", "cold-work": "/work"}
u = lambda i, q: f"{B}{S}{PAGES[i]}" + (("?" + q) if q else "")
wq = lambda name: urlencode({k: z(v) for k, v in md["reads"][name]["query"].items()})
t = []
DEPTHS = ["cooling", "cold-health", "cold-scenarios"]
if phase == "positive":
    t += [dict(id=i, case="current-limited", url=u(i, DEPTH)) for i in DEPTHS]
    t += [dict(id="cold-work", case="positive", url=u("cold-work", wq("positive")))]
    t += [dict(id=i, case="empty-window", url=u(i, EMPTY)) for i in DEPTHS]
    t += [dict(id="cold-work", case="zero", url=u("cold-work", wq("zero")))]
    t += [dict(id="cold-work", case="historical", url=u("cold-work", wq("historical")))]
    t += [dict(id=i, case="refused-reversed", url=u(i, BAD)) for i in PAGES]
    t += [dict(id="cold-work", case="refused-span-32d", url=u("cold-work", "from=2026-09-22T00:00:00Z&to=2026-10-24T00:00:00Z"))]
    t += [dict(id=i, case="no-window", url=u(i, None)) for i in PAGES]
    t += [dict(id=i, case="work-day-window", url=u(i, wq("positive"))) for i in DEPTHS]
    t += [dict(id=i, case="all-open", url=u(i, DEPTH if i != "cold-work" else wq("positive")), openAll=True) for i in PAGES]
elif phase == "links":  # app-only link checks, not pairs
    t += [dict(id="link-check", case="cold-overview", url=f"{B}{S}?{DEPTH}", mock="cold"),
          dict(id="link-check", case="cold-overview-bare", url=f"{B}{S}", mock="cold"),
          dict(id="link-check", case="cold-findings", url=f"{B}{S}/findings?{DEPTH}", mock="cold-findings"),
          dict(id="link-check", case="cold-performance", url=f"{B}{S}/performance/temperature?{DEPTH}", mock="temperature")]
elif phase == "worstcase":
    t += [dict(id="cold-work", case="worstcase", url=u("cold-work", wq("worstcase"))),
          dict(id="cold-work", case="worstcase-all-open", url=u("cold-work", wq("worstcase")), openAll=True)]
elif phase == "pending":
    t += [dict(id=i, case="pending", url=u(i, DEPTH)) for i in DEPTHS]
    t += [dict(id=i, case="historical", url=u(i, DEPTH + "&known_at=" + md["cutoffs"]["K0"])) for i in DEPTHS]
    t += [dict(id="cold-work", case="pending", url=u("cold-work", wq("pending")))]
elif phase in ("stale", "unknown"):
    t += [dict(id=i, case=phase, url=u(i, DEPTH)) for i in DEPTHS]
    t += [dict(id="cold-work", case=phase, url=u("cold-work", wq(phase)))]
elif phase in ("forbidden", "unavailable"):
    t += [dict(id="cold-work", case={"forbidden": "forbidden-403", "unavailable": "store-unavailable-503"}[phase], url=u("cold-work", wq("positive")))]
json.dump(t, open(f"{sys.argv[3]}/targets-{phase}.json", "w"), indent=1)
print(phase, len(t))
