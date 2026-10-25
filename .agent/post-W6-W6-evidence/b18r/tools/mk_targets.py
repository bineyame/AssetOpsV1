"""cap-b18 W6 recapture copy of batch 18 (port 5392; adds the probe phase). Batch 18: writes targets-<phase>.json (capture URLs only). Page-two cursors come from a read-only GET of the
same API the phase's Vite proxies to (the frontend's own query: from, to, limit=5[, kind])."""
import json, sys, urllib.request
from urllib.parse import urlencode
B = "http://127.0.0.1:5392"
W = {"from": "2026-10-14T00:00:00Z", "to": "2026-10-21T00:00:00Z"}
PATHS = {"incidents": "/incidents", "maintenance": "/maintenance", "maintenance-preventive": "/maintenance/preventive",
         "oprecords": "/operational-records"}
API = {"incidents": "incidents", "maintenance": "maintenance", "maintenance-preventive": "preventive",
       "oprecords": "operational-records"}
def u(i, q): return B + PATHS[i] + ("?" + urlencode(q) if q else "")
def cursor(port, i, q):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/work/{API[i]}?{urlencode({**q, 'limit': 5})}") as r:
        return json.load(r)["next_cursor"]
phase, port = sys.argv[1], sys.argv[2]
REFUSED = lambda i: [dict(id=i, case="refused-reversed", url=u(i, {"from": W["to"], "to": W["from"]})),
                     dict(id=i, case="refused-span-32d", url=u(i, {"from": "2026-09-19T00:00:00Z", "to": "2026-10-21T00:00:00Z"})),
                     dict(id=i, case="refused-one-bound", url=u(i, {"from": W["from"]})),
                     dict(id=i, case="refused-bad-known-at", url=u(i, {**W, "known_at": "not-a-time"})),
                     dict(id=i, case="no-window", url=u(i, None))]
t = []
if phase == "inc":
    i = "incidents"
    t += [dict(id=i, case="positive", url=u(i, W)), dict(id=i, case="all-open", url=u(i, W), openAll=True),
          dict(id=i, case="page-two", url=u(i, {**W, "cursor": cursor(port, i, W)})), *REFUSED(i)]
elif phase == "maint":
    i = "maintenance"
    t += [dict(id=i, case="positive", url=u(i, W)), dict(id=i, case="all-open", url=u(i, W), openAll=True),
          dict(id=i, case="page-two", url=u(i, {**W, "cursor": cursor(port, i, W)})), *REFUSED(i)]
elif phase == "prev":
    i = "maintenance-preventive"
    t += [dict(id=i, case="positive", url=u(i, W)), dict(id=i, case="all-open", url=u(i, W), openAll=True), *REFUSED(i)]
elif phase == "op":
    i = "oprecords"
    t += [dict(id=i, case="positive", url=u(i, W)), dict(id=i, case="all-open", url=u(i, W), openAll=True),
          dict(id=i, case="page-two", url=u(i, {**W, "cursor": cursor(port, i, W)}))]
    for k in ("OPERATOR_LOG", "MANUAL_READING", "SHIFT_NOTE", "SITE_VISIT"):
        t.append(dict(id=i, case=f"kind-{k}", url=u(i, {**W, "kind": k})))
    t += [dict(id=i, case="historical", url=u(i, {**W, "known_at": "2026-10-21T12:00:00Z"})),
          dict(id=i, case="invalid-kind", url=u(i, {**W, "kind": "BOGUS"})), *REFUSED(i),
          dict(id="incidents", case="one-row", url=u("incidents", W))]
elif phase == "zero":
    t += [dict(id=i, case="zero", url=u(i, W)) for i in PATHS]
elif phase == "hist":
    t += [dict(id="incidents", case="historical", url=u("incidents", {**W, "known_at": "2026-10-21T12:00:00Z"})),
          dict(id="incidents", case="historical-current", url=u("incidents", W)),
          dict(id="maintenance-preventive", case="historical", url=u("maintenance-preventive", {**W, "known_at": "2026-10-21T12:00:03Z"})),
          dict(id="maintenance-preventive", case="historical-current", url=u("maintenance-preventive", W))]
elif phase == "stress":
    M = {"from": "2026-10-15T00:00:00Z", "to": "2026-10-22T00:00:00Z"}  # the stress request is created 2026-10-21 (B15-06)
    t += [dict(id="incidents", case="worstcase", url=u("incidents", W)),
          dict(id="incidents", case="worstcase-all-open", url=u("incidents", W), openAll=True),
          dict(id="maintenance", case="worstcase", url=u("maintenance", M)),
          dict(id="maintenance", case="worstcase-all-open", url=u("maintenance", M), openAll=True),
          dict(id="maintenance-preventive", case="worstcase", url=u("maintenance-preventive", W)),
          dict(id="maintenance-preventive", case="worstcase-all-open", url=u("maintenance-preventive", W), openAll=True),
          dict(id="oprecords", case="worstcase", url=u("oprecords", W)),
          dict(id="oprecords", case="worstcase-all-open", url=u("oprecords", W), openAll=True)]
elif phase == "linked":
    t += [dict(id="incidents", case="linked", url=u("incidents", W)), dict(id="maintenance", case="linked", url=u("maintenance", W)),
          dict(id="maintenance", case="linked-all-open", url=u("maintenance", W), openAll=True)]
elif phase == "probe":  # cap-b18 extra (not indexed): capture-only five-row 160-char DOM probe on the oprecords table (Q15/Q16)
    t += [dict(id="oprecords", case="probe5", url=u("oprecords", W), probe5=True)]
elif phase == "absent":
    t += [dict(id=i, case="unavailable-503", url=u(i, W)) for i in PATHS]
elif phase == "scope":
    t += [dict(id=i, case="empty-scope", url=u(i, W)) for i in PATHS]
elif phase in ("cold", "coldwc", "ev", "evwc"):
    q = json.loads(sys.argv[3])  # window that contains the producer's cases
    t += [dict(id=i, case=f"{phase}", url=u(i, q)) for i in PATHS]
    t += [dict(id=i, case=f"{phase}-all-open", url=u(i, q), openAll=True) for i in ("incidents", "maintenance")]
    t += [dict(id="incidents", case=f"{phase}-default-window", url=u("incidents", None))]
json.dump(t, open(f"targets-{phase}.json", "w"), indent=1)
print(phase, len(t))
