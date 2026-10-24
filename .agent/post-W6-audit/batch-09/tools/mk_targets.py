"""Writes targets-*.json (capture URLs only). Windows match .agent/W2-F-evidence/capture.mjs (Q / QBAD)."""
import json
B = "http://localhost:5189"; E = "/sites/EV-LAB-001"
Q = "from=2026-10-06T08:00:00.000000Z&to=2026-10-06T09:05:00.000000Z&known_at=2026-10-06T09:00:00.000000Z"
EMPTY = "from=2026-10-05T08:00:00.000000Z&to=2026-10-05T09:05:00.000000Z"
BAD = "from=2026-10-06T09:05:00.000000Z&to=2026-10-06T08:00:00.000000Z"
S = [("ev", f"{E}/ev"), ("ev-evidence", f"{E}/ev/evidence"), ("ev-evidence-analysis", f"{E}/ev/evidence/analysis"),
     ("ev-financials", f"{E}/ev/financials"), ("ev-assumptions", f"{E}/ev/financial-assumptions")]
u = lambda p, q: B + p + (("?" + q) if q else "")
main = []
for sid, p in S:
    main += [dict(id=sid, case="interrupted", url=u(p, Q)), dict(id=sid, case="no-selection", url=u(p, EMPTY)),
             dict(id=sid, case="refused", url=u(p, BAD)), dict(id=sid, case="no-window", url=u(p, None))]
comp = [dict(id=sid, case="complete", url=u(p, Q)) for sid, p in S]
# B7-01 cross-check only (ev-findings is NOT a batch-09 ID; not counted as pairs)
chk = [dict(id="ev-findings", case="check-interrupted", url=u(f"{E}/findings", Q)), dict(id="ev-findings", case="check-no-window", url=u(f"{E}/findings", None))]
for n, t in (("interrupted", main), ("complete", comp), ("findings-check", chk)):
    json.dump(t, open(f"targets-{n}.json", "w"), indent=1)
print(len(main), len(comp), len(chk))
