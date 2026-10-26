"""Writes targets-<phase>.json (capture URLs only) from the W502 walkthrough manifest (var/w502b_b15/manifest.json).
COLD-LAB-001. Case tabs use the manifest `case_reads.<name>:<kind>.query`; the cold Action uses the manifest
`detail_reads` (positive CURRENT, positive known_at=K1, worstcase Action 1), cutoff K3 and each mode's returned cutoff."""
import json, sys
from urllib.parse import urlencode, quote
B = "http://localhost:5185"
S = "/sites/COLD-LAB-001"
M = json.load(open(sys.argv[2], encoding="utf8"))
phase = sys.argv[1]
mode = {"forbidden": "positive", "unavailable": "positive"}.get(phase, phase)
md = M["modes"][mode]
z = lambda s: s.replace(".000000Z", "Z")
KINDS = {"cold-work-incidents": "incidents", "cold-work-maintenance": "maintenance"}
cu = lambda i, q: f"{B}{S}/work/{KINDS[i]}" + (("?" + urlencode({k: z(v) for k, v in q.items() if v is not None})) if q else "")
cq = lambda name, i: md["case_reads"][f"{name}:{KINDS[i]}"]["query"]
au = lambda aid, ka=None: f"{B}{S}/actions/{aid}/verification" + (f"?known_at={quote(ka)}" if ka else "")
aid = md["actions"][0]["id"]
t = []
if phase == "positive":
    for i in KINDS:
        t += [dict(id=i, case="current", url=cu(i, cq("current", i))),
              dict(id=i, case="positive-cutoff", url=cu(i, cq("positive", i))),
              dict(id=i, case="historical", url=cu(i, cq("historical", i))),
              dict(id=i, case="zero", url=cu(i, cq("zero", i))),
              dict(id=i, case="refused-reversed", url=cu(i, {"from": cq("current", i)["to"], "to": cq("current", i)["from"]})),
              dict(id=i, case="refused-span-32d", url=cu(i, {"from": "2026-09-22T00:00:00Z", "to": "2026-10-24T00:00:00Z"})),
              dict(id=i, case="no-window", url=cu(i, None)),
              dict(id=i, case="all-open", url=cu(i, cq("current", i)), openAll=True)]
    D = md["detail_reads"]
    t += [dict(id="cold-action", case="positive", url=au(aid)),
          dict(id="cold-action", case="all-open", url=au(aid), openAll=True),
          dict(id="cold-action", case="not-linked", url=au(aid, D["action-not-linked"]["query"]["known_at"])),
          dict(id="cold-action", case="historical", url=au(aid, md["cutoffs"]["K3"])),
          dict(id="cold-action", case="not-found", url=au("00000000-0000-4000-8000-0000000000aa")),
          dict(id="cold-action", case="invalid-known-at", url=au(aid, "not-a-time")),
          dict(id="cold-action", case="future-known-at", url=au(aid, "2099-01-01T00:00:00Z"))]
elif phase == "worstcase":
    for i in KINDS:
        t += [dict(id=i, case="worstcase", url=cu(i, cq("worstcase", i))),
              dict(id=i, case="worstcase-all-open", url=cu(i, cq("worstcase", i)), openAll=True)]
    w = md["detail_reads"]["action-worstcase"]["action_id"]
    t += [dict(id="cold-action", case="worstcase", url=au(w)),
          dict(id="cold-action", case="worstcase-all-open", url=au(w), openAll=True)]
elif phase in ("pending", "stale", "unknown"):
    for i in KINDS:
        t += [dict(id=i, case=phase, url=cu(i, cq(phase, i)))]
    t += [dict(id="cold-action", case=phase, url=au(aid, md["reads"][phase]["query"]["known_at"]))]
elif phase in ("forbidden", "unavailable"):
    c = {"forbidden": "forbidden-403", "unavailable": "unavailable-503"}[phase]
    q = M["processes"][phase]["query"]
    for i in KINDS:
        t += [dict(id=i, case=c, url=cu(i, q))]
    t += [dict(id="cold-action", case=c, url=au(aid))]
json.dump(t, open(f"{sys.argv[3]}/targets-{phase}.json", "w"), indent=1)
print(phase, len(t))
