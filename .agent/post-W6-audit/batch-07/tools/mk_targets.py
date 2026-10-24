"""Writes targets-*.json (capture URLs only). Windows match .agent/W2-F-evidence/capture.mjs."""
import json, sys
B = "http://localhost:5187"; C = "/sites/COLD-LAB-001"
W = "from=2026-10-06T19:00:00Z&to=2026-10-06T20:05:00Z"
EMPTY = "from=2026-10-05T19:00:00Z&to=2026-10-05T20:05:00Z"
BAD = "from=2026-10-06T20:05:00Z&to=2026-10-06T19:00:00Z"
S = [("cold-findings", f"{C}/findings", "?"), ("cold", C, "?"), ("cold-evidence", f"{C}/evidence", "?"),
     ("cold-evidence-analysis", f"{C}/evidence", "?view=analysis&"), ("cold-financials", f"{C}/financials", "?"),
     ("cold-assumptions", f"{C}/financials/assumptions", "?")]
def url(path, sep, q):
    if q is None:
        return B + path + (sep.rstrip("&") if sep != "?" else "")
    return B + path + sep + q
exc = []
for sid, path, sep in S:
    exc.append(dict(id=sid, case="stocked", url=url(path, sep, W)))
    exc.append(dict(id=sid, case="no-selection", url=url(path, sep, EMPTY)))
    exc.append(dict(id=sid, case="refused", url=url(path, sep, BAD)))
    exc.append(dict(id=sid, case="no-window", url=url(path, sep, None)))
norm = [dict(id=sid, case="normal", url=url(path, sep, W)) for sid, path, sep in S]
json.dump(exc, open("targets-excursion.json", "w"), indent=1)
json.dump(norm, open("targets-normal.json", "w"), indent=1)
print(len(exc), len(norm))
