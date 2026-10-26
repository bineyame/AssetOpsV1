"""Extra W5-EV targets (URLs only): one-sided and >31-day windows on the four depth pages and ev-action, the R373
case-detail landing (work request overview/record/history), cold-independent. Usage: mk_extra.py <manifest> <out>"""
import json, sys
from urllib.parse import urlencode, quote
B = "http://127.0.0.1:5197"; S = "/sites/EV-LAB-001"
M = json.load(open(sys.argv[1], encoding="utf8")); md = M["modes"]["positive"]; E = M["windows"]["E"]
PAGES = {"availability": "/performance/availability", "energy": "/performance/energy", "ev-health": "/health", "ev-scenarios": "/ev/financials/scenarios"}
t = []
for i, p in PAGES.items():
    for case, q in (("one-sided-from", {"from": E["from"]}), ("one-sided-to", {"to": E["to"]}),
                    ("span-32d", {"from": "2026-09-01T00:00:00Z", "to": "2026-10-06T09:00:00Z"})):
        t.append(dict(id=i, case=case, url=f"{B}{S}{p}?{urlencode(q)}"))
act = md["work_urls"]["action_detail"].split("?")[0]
for case, q in (("one-sided-from", {"from": md["work_window_W"]["from"]}), ("one-sided-to", {"to": md["work_window_W"]["to"]})):
    t.append(dict(id="ev-action", case=case, url=f"{B}{act}?{urlencode(q)}"))
wr = md["submitted"]["request"]["id"]
for v, m in (("", "wr-overview"), ("/record", "wr-record"), ("/history", "wr-history")):
    t.append(dict(id="case-detail", case="r373-landing" + (v.replace("/", "-") or "-overview"), url=f"{B}/maintenance/requests/{wr}{v}?site_id=EV-LAB-001", mock=m))
json.dump(t, open(sys.argv[2], "w"), indent=1); print(len(t))
