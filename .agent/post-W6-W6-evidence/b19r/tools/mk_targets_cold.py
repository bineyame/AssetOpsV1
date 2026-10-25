"""Writes targets-cold-*.json (capture URLs only) from the read-only WR code/ID listing of the w502 b19 DBs (../seed/cold-*.txt)."""
import json
from pathlib import Path
H = Path(__file__).resolve().parent
B = "http://127.0.0.1:5393"
SUF = {"wr-overview": "", "wr-record": "/record", "wr-history": "/history"}
def wr(db): return [l.split("|") for l in (H.parent / "seed" / f"cold-{db}.txt").read_text().split() if l]
u = lambda i, c: f"{B}/maintenance/requests/{c}{SUF[i]}?site_id=COLD-LAB-001"
pos = wr("w502b_positive_w6r18r_test"); wc = wr("w502b_worstcase_w6r18r_test")
P = {"cold-positive": [dict(id=i, case=f"cold-{pos[0][0].lower()}", url=u(i, pos[0][1])) for i in SUF] + [dict(id=i, case=f"cold-all-open-{pos[0][0].lower()}", url=u(i, pos[0][1]), openAll=True) for i in SUF],
     "cold-worstcase": [dict(id=i, case=f"cold-worstcase-{c.lower()}", url=u(i, x)) for c, x in (wc[0], wc[1]) for i in SUF] + [dict(id=i, case=f"cold-worstcase-all-open-{wc[1][0].lower()}", url=u(i, wc[1][1]), openAll=True) for i in SUF],
     "cold-forbidden": [dict(id=i, case="cold-forbidden-principal", url=u(i, pos[0][1])) for i in SUF]}
for k, v in P.items():
    json.dump(v, open(H / f"targets-{k}.json", "w"), indent=1); print(k, len(v))
