"""Writes targets-*.json (capture URLs only). Windows follow the W3-03 run-3 capture table (one-day 10-06 request,
historical known_at 2026-09-30) and the W3-02 capture URLs (10-06 day; 10-05..10-12 week)."""
import json
B = "http://localhost:5181"
S = [("globalevidence", "/evidence"), ("globalfinancials", "/financials"), ("portfolio", "/portfolio")]
DAY = "from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z"
WEEK = "from=2026-10-05T00%3A00%3A00Z&to=2026-10-12T00%3A00%3A00Z"
HIST = DAY + "&known_at=2026-09-30T00%3A00%3A00Z"
REV = "from=2026-10-07T00%3A00%3A00Z&to=2026-10-06T00%3A00%3A00Z"
LONG = "from=2026-09-01T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z"
u = lambda p, q: B + p + (("?" + q) if q else "")
T = {
 # W3-03 clean four-Site fixture (same-cutoff producer)
 "w303-positive": [dict(id=i, case="w303-positive", url=u(p, DAY)) for i, p in S],
 "w303-guards": [dict(id=i, case=c, url=u(p, q)) for i, p in S for c, q in (("refused-reversed", REV), ("refused-over-31d", LONG), ("no-window", None))],
 "w303-empty": [dict(id="portfolio", case="w303-empty-foreign-tenant", url=u("/portfolio", DAY))],
 "w303-401": [dict(id="portfolio", case="w303-refusal-401", url=u("/portfolio", DAY))],
 "w303-partial": [dict(id=i, case="w303-partial", url=u(p, DAY)) for i, p in S],
 "w303-historical": [dict(id=i, case="w303-historical", url=u(p, HIST)) for i, p in S],
 "w303-pending": [dict(id=i, case="w303-pending", url=u(p, DAY)) for i, p in S],
 "w303-503": [dict(id="portfolio", case="w303-refusal-503", url=u("/portfolio", DAY))],
 # W3-02 serve.py (KOBO action chain + late-reading cold + interrupted EV + foreign tenant)
 "w302-positive": [dict(id=i, case="w302-positive", url=u(p, DAY)) for i, p in S],
 "w302-partial-week": [dict(id=i, case="w302-partial-week", url=u(p, WEEK)) for i, p in S],
 "w302-pending": [dict(id=i, case="w302-pending-late-kobo", url=u(p, DAY)) for i, p in S],
}
for n, t in T.items():
    json.dump(t, open(f"targets-{n}.json", "w"), indent=1)
print({n: len(t) for n, t in T.items()})
