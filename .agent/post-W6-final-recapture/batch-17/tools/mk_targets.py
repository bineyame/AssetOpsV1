"""Writes targets-<phase>.json (capture URLs only) from the W504 walkthrough manifest (var/w504a_b17/manifest.json).
EV-LAB-001 (Etc/UTC). Work window W = manifest per-mode work_window_W (current UTC day); Action detail URLs are the
manifest's own work_urls.action_detail. Usage: mk_targets.py <phase> <manifest> <outdir>"""
import json, sys
from datetime import datetime, timedelta
from urllib.parse import urlencode
B = "http://localhost:5187"
S = "/sites/EV-LAB-001"
M = json.load(open(sys.argv[2], encoding="utf8"))
phase = sys.argv[1]
mode = {"forbidden": "positive", "unavailable": "positive", "links": "positive"}.get(phase, phase)
md = M["modes"][mode]
W = md.get("work_window_W") or {}
wq = lambda w, **x: urlencode({"from": w["from"], "to": w["to"], **{k: v for k, v in x.items() if v}})
REV = {"from": W.get("to"), "to": W.get("from")}
SPAN = {"from": "2026-09-22T00:00:00Z", "to": "2026-10-24T00:00:00Z"}
iso = lambda d: d.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
P = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
CASES = {"ev-work-incidents": "/work/incidents", "ev-work-maintenance": "/work/maintenance"}
act_path = md["work_urls"]["action_detail"].split("?")[0] if md.get("work_urls") else None
A = lambda q: f"{B}{act_path}" + (("?" + q) if q else "")
u = lambda i, q: f"{B}{S}{CASES[i]}" + (("?" + q) if q else "")
t = []
if phase == "positive":
    k1 = P(md["action"]["recorded_at"]); ki = P(md["intent"]["recorded_at"])
    between = iso(k1 + (ki - k1) / 2)
    before = iso(k1 - timedelta(seconds=1))
    for i in CASES:
        t += [dict(id=i, case="positive", url=u(i, wq(W))),
              dict(id=i, case="historical-index-known-at", url=u(i, wq(W, known_at=md["index_known_at"]))),
              dict(id=i, case="refused-reversed", url=u(i, wq(REV))),
              dict(id=i, case="refused-span-32d", url=u(i, wq(SPAN))),
              dict(id=i, case="no-window", url=u(i, None)),
              dict(id=i, case="all-open", url=u(i, wq(W)), openAll=True)]
    t += [dict(id="ev-action", case="positive-current", url=A(wq(W))),
          dict(id="ev-action", case="historical-before-intent", url=A(wq(W, known_at=between))),
          dict(id="ev-action", case="historical-before-action", url=A(wq(W, known_at=before))),
          dict(id="ev-action", case="not-found-404", url=f"{B}{S}/actions/00000000-0000-4000-8000-000000000000/verification?{wq(W)}"),
          dict(id="ev-action", case="refused-reversed", url=A(wq(REV))),
          dict(id="ev-action", case="refused-span-32d", url=A(wq(SPAN))),
          dict(id="ev-action", case="refused-bad-known-at", url=A(wq(W, known_at="yesterday"))),
          dict(id="ev-action", case="no-window", url=A(None)),
          dict(id="ev-action", case="all-open", url=A(wq(W)), openAll=True)]
elif phase == "zero":
    prev = (P(W["from"]) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    for i in CASES:
        t += [dict(id=i, case="zero", url=u(i, wq(W))),
              dict(id=i, case="zero-prior-day", url=u(i, urlencode({"from": prev, "to": W["from"]})))]
    t += [dict(id="ev-action", case="zero-mode-current", url=A(wq(W)))]
elif phase == "worstcase":
    ids = [{"id": a["action_id"]} for a in (md.get("worstcase") or {}).get("actions", [])]
    t += [dict(id="ev-action", case="worstcase-positive-action", url=A(wq(W)))]
    for n, a in enumerate(ids if isinstance(ids, list) else []):
        aid = a.get("id") if isinstance(a, dict) else a
        if aid and aid not in (act_path or ""):
            t += [dict(id="ev-action", case=f"worstcase-160-{n+2}", url=f"{B}{S}/actions/{aid}/verification?{wq(W)}")]
            if n == 0:
                t += [dict(id="ev-action", case="worstcase-160-all-open", url=f"{B}{S}/actions/{aid}/verification?{wq(W)}", openAll=True)]
    for i in CASES:
        t += [dict(id=i, case="worstcase-five-160", url=u(i, wq(W))),
              dict(id=i, case="worstcase-five-160-all-open", url=u(i, wq(W)), openAll=True)]
elif phase == "links":  # app-only link checks, not pairs
    q = wq(W)
    for v in ["", "/verification", "/overview", "/execution", "/history", "/plan", "/evidence"]:
        t += [dict(id="link-check", case="ev-action-tab" + (v.replace("/", "-") or "-bare"), url=f"{B}{act_path.rsplit('/verification', 1)[0]}{v}?{q}", mock="ev-action")]
    t += [dict(id="link-check", case="ev-work-actions-tab", url=f"{B}{S}/work?{q}", mock="ev-work"),
          dict(id="link-check", case="global-incidents", url=f"{B}/incidents?{q}", mock="ev-work-incidents"),
          dict(id="link-check", case="global-maintenance", url=f"{B}/maintenance?{q}", mock="ev-work-maintenance")]
elif phase in ("forbidden", "unavailable"):
    c = {"forbidden": "forbidden-403", "unavailable": "store-unavailable-503"}[phase]
    t += [dict(id=i, case=c, url=u(i, wq(W))) for i in CASES] + [dict(id="ev-action", case=c, url=A(wq(W)))]
json.dump(t, open(f"{sys.argv[3]}/targets-{phase}.json", "w"), indent=1)
print(phase, len(t))
