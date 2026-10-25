"""cap-b18: link-landing targets from the captured list evidence (hrefs exactly as rendered; capture URLs only).
usage: python mk_links.py <phase> <out targets json>
phases: linkmini (linked DB), linkinc (inc DB), r360hist (hist DB), linkcold (W502 positive serve), linkev (W504 positive serve), linkevwc (W504 worstcase serve)"""
import json, os, sys
from urllib.parse import urlsplit

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = "http://127.0.0.1:5392"


def pairs(part, screen, case):
    ev = json.load(open(os.path.join(B, f"part-{part}", "evidence.json"), encoding="utf8"))
    return [p for p in ev["pairs"] if p["screen"] == screen and p["case"] == case and p["viewport"].startswith("1440")]


def links(part, screen, case):
    out = []
    for p in pairs(part, screen, case):
        w6 = p["app"]["w6"]
        for s in w6["rowLinks"] + w6["siteLinks"] + w6["requestLinks"]:
            if " -> " in s and not s.endswith("(text)"):
                out.append(s.rsplit(" -> ", 1)[1])
    return list(dict.fromkeys(out))


def kind(h):
    path = urlsplit(h).path
    if "/work/incidents" in path: return "site-incidents"
    if "/work/maintenance" in path: return "site-maintenance"
    if "/findings/" in path: return "finding"
    if "/actions/" in path: return "action"
    if path.startswith("/maintenance/requests/"): return "request"
    if path.startswith("/sites/"): return "site-overview"
    return "other"


MOCK = {"mini": {"site-incidents": "sitework-incidents", "site-maintenance": "sitework-maintenance", "site-overview": "mini", "finding": "finding", "action": "action-overview", "request": "wr-overview"},
        "cold": {"site-incidents": "cold-work-incidents", "site-maintenance": "cold-work-maintenance", "site-overview": "cold", "finding": "cold-finding", "action": "cold-action", "request": "wr-overview"},
        "ev": {"site-incidents": "ev-work-incidents", "site-maintenance": "ev-work-maintenance", "site-overview": "ev", "finding": "ev", "action": "ev-action", "request": "wr-overview"}}


def mk(prefix, dom, hrefs, limit=None):
    t, seen = [], {}
    for h in hrefs:
        k = kind(h)
        if k == "other": continue
        seen[k] = seen.get(k, 0) + 1
        if limit and seen[k] > limit.get(k, 1): continue
        t.append(dict(id="link", case=f"{prefix}-{k}{'' if seen[k] == 1 else seen[k]}", url=V + h, mock=MOCK[dom].get(k, "wr-overview")))
    return t


phase, out = sys.argv[1], sys.argv[2]
t = []
if phase == "linkmini":
    lim = {"site-incidents": 1, "site-maintenance": 1, "site-overview": 1, "finding": 1, "action": 1, "request": 2}
    t += mk("linkmini", "mini", links("linked", "incidents", "linked") + links("linked", "maintenance", "linked"), lim)
elif phase == "linkinc":  # inc DB: the linked fixture's incident has no linked request; the incidents fixture row does
    # R359: WR landing from the linked incident row's WR code link
    req = [h for h in links("inc", "incidents", "positive") if kind(h) == "request"]
    t += [dict(id="link", case="r359-incident-wr", url=V + h, mock="wr-overview") for h in req[:1]]
    # R360 current: INC link (Site incidents tab) from a current read
    cur = [h for h in links("inc", "incidents", "positive") if kind(h) == "site-incidents"]
    t += [dict(id="link", case="r360-current-inc", url=V + h, mock="sitework-incidents") for h in cur[:1]]
elif phase == "r360hist":
    hist = [h for h in links("hist", "incidents", "historical") if kind(h) == "site-incidents"]
    t += [dict(id="link", case="r360-historical-inc", url=V + h, mock="sitework-incidents") for h in hist[:1]]
elif phase == "linkcold":
    lim = {"site-incidents": 1, "site-maintenance": 1, "site-overview": 1, "finding": 2, "action": 1, "request": 1}
    t += mk("linkcold", "cold", links("cold", "incidents", "cold") + links("cold", "maintenance", "cold"), lim)
elif phase == "linkev":
    lim = {"site-incidents": 1, "site-maintenance": 1, "site-overview": 1, "action": 1, "request": 1, "finding": 1}
    t += mk("linkev", "ev", links("ev", "incidents", "ev") + links("ev", "maintenance", "ev"), lim)
    # R353: EV Site link from the incidents and maintenance EV rows
    for scr in ("incidents", "maintenance"):
        for h in [h for h in links("ev", scr, "ev") if kind(h) == "site-overview"][:1]:
            t.append(dict(id="link", case=f"r353-ev-site-from-{scr}", url=V + h, mock="ev"))
elif phase == "linkevwc":
    for scr in ("incidents", "maintenance"):
        for h in [h for h in links("evwc", scr, "evwc") if kind(h) == "site-overview"][:1]:
            t.append(dict(id="link", case=f"r353-evwc-site-from-{scr}", url=V + h, mock="ev"))
json.dump(t, open(out, "w"), indent=1)
for x in t: print(x["case"], x["url"][21:160])
