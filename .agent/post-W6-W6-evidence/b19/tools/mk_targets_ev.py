"""Writes targets-ev-*.json (capture URLs only) from the read-only WR code/ID listing of the w504 b19 DBs (../seed/ev-*.txt)."""
import json
from pathlib import Path
H = Path(__file__).resolve().parent
B = "http://127.0.0.1:5389"
SUF = {"wr-overview": "", "wr-record": "/record", "wr-history": "/history"}
def wr(db): return [l.split("|") for l in (H.parent / "seed" / f"ev-{db}.txt").read_text().split() if l]
u = lambda i, c: f"{B}/maintenance/requests/{c}{SUF[i]}?site_id=EV-LAB-001"
pos = wr("w504a_positive_w6r19_test"); wc = wr("w504a_worstcase_w6r19_test")
P = {"ev-positive": [dict(id=i, case=f"ev-{pos[0][0].lower()}", url=u(i, pos[0][1])) for i in SUF] + [dict(id=i, case=f"ev-all-open-{pos[0][0].lower()}", url=u(i, pos[0][1]), openAll=True) for i in SUF],
     "ev-worstcase": [dict(id=i, case=f"ev-worstcase-160-{c.lower()}", url=u(i, x)) for c, x in wc[1:2] for i in SUF] + [dict(id=i, case=f"ev-worstcase-160-all-open-{wc[1][0].lower()}", url=u(i, wc[1][1]), openAll=True) for i in SUF] + [dict(id="wr-overview", case=f"ev-worstcase-{c.lower()}", url=u("wr-overview", x)) for c, x in (wc[0], wc[2])],
     "ev-forbidden": [dict(id=i, case="ev-forbidden-403", url=u(i, pos[0][1])) for i in SUF],
     "ev-unavailable": [dict(id=i, case="ev-api-stopped-503", url=u(i, pos[0][1])) for i in SUF]}
for k, v in P.items():
    json.dump(v, open(H / f"targets-{k}.json", "w"), indent=1); print(k, len(v))
