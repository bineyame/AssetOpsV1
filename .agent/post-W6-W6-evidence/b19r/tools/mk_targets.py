"""Writes targets-<phase>.json (capture URLs only) from the batch-19 w601_seed outputs in ../seed/.
Usage: mk_targets.py  (writes every phase). Fixture clock 2026-10-20T12:00:00Z; Sites KOBO-001/KOBO-002 (mini)."""
import json
from pathlib import Path
B = "http://127.0.0.1:5393"
H = Path(__file__).resolve().parent
S = H.parent / "seed"
def ids(fx):
    d = json.load(open(S / f"seed-{fx}.json", encoding="utf8"))
    return {w["code"]: (w.get("case_id"), w.get("site_code"), w.get("tenant")) for w in d["written"] if "code" in w}
SUF = {"wr-overview": "", "wr-record": "/record", "wr-history": "/history"}
ALL = list(SUF)
def u(i, case_id, site="KOBO-001", **q):
    qs = "&".join([f"site_id={site}"] * (site is not None) + [f"{k}={v}" for k, v in q.items()])
    return f"{B}/maintenance/requests/{case_id}{SUF[i]}" + (f"?{qs}" if qs else "")
ABSENT = "00000000-0000-4000-8000-000000000404"
P = {}
d = ids("detail"); w1, w2 = d["WR-000001"][0], d["WR-000002"][0]
t = []
for i in ALL:
    t += [dict(id=i, case="positive-wr1-in-progress", url=u(i, w1)),
          dict(id=i, case="all-open-wr1", url=u(i, w1), openAll=True),
          dict(id=i, case="cancelled-wr2", url=u(i, w2)),
          dict(id=i, case="not-found-404", url=u(i, ABSENT)),
          dict(id=i, case="no-site-id", url=u(i, w1, site=None)),
          dict(id=i, case="bad-known-at", url=u(i, w1, known_at="yesterday"))]
t += [dict(id="wr-history", case="page2-wr1", url=u("wr-history", w1), pageNext=1),
      dict(id="wr-history", case="page2-all-open-wr1", url=u("wr-history", w1), pageNext=1, openAll=True),
      dict(id="wr-history", case="historical-1159-04-wr1", url=u("wr-history", w1, known_at="2026-10-20T11:59:04Z")),
      dict(id="wr-overview", case="historical-1159-04-wr1-completed", url=u("wr-overview", w1, known_at="2026-10-20T11:59:04Z")),
      dict(id="wr-overview", case="wrong-site-kobo002", url=u("wr-overview", w1, site="KOBO-002")),
      dict(id="wr-overview", case="malformed-case-id", url=f"{B}/maintenance/requests/not-a-uuid?site_id=KOBO-001"),
      dict(id="wr-overview", case="before-created-known-at", url=u("wr-overview", w1, known_at="2026-10-20T11:00:00Z"))]
P["detail"] = t
links = [dict(id="link-check", case=f"unknown-subtab{v.replace('/', '-')}", url=f"{B}/maintenance/requests/{w1}{v}?site_id=KOBO-001", mock="wr-overview")
         for v in ["/overview", "/evidence", "/execution", "/records"]]
links += [dict(id="link-check", case="unknown-subtab-records-known-at", url=f"{B}/maintenance/requests/{w1}/records?site_id=KOBO-001&known_at=2026-10-20T11:59:04Z", mock="wr-overview")]
links += [dict(id="link-check", case="maintenance-list", url=f"{B}/maintenance?from=2026-10-14T00:00:00Z&to=2026-10-21T00:00:00Z", mock="maintenance")]
P["links"] = links
h = ids("detail-history"); hw1 = h["WR-000001"][0]
P["hist"] = [dict(id=i, case=c, url=u(i, hw1, **q)) for i in ALL for c, q in
             (("historical-120001-rev2", {"known_at": "2026-10-20T12:00:01Z"}), ("historical-current-rev3", {}))]
l = ids("detail-linked"); lw5 = l["WR-000005"][0]
P["linked"] = [dict(id=i, case="linked-source-wr5", url=u(i, lw5)) for i in ALL]
s = ids("stress"); sw7 = s["WR-000007"][0]
P["stress"] = [dict(id=i, case=c, url=u(i, sw7), openAll=o) for i in ALL for c, o in (("worstcase-200char-wr7", False), ("worstcase-all-open-wr7", True))]
m = ids("maintenance")
st = {"WR-000001": "open", "WR-000004": "cancelled-from-open", "WR-000005": "in-progress-assigned", "WR-000006": "completed"}
t = []
for code, name in st.items():
    cid, site, _ = m[code]
    t += [dict(id=i, case=f"{name}-{code.lower()}", url=u(i, cid, site=site)) for i in ALL]
t += [dict(id="wr-overview", case="other-tenant-wr8-404", url=u("wr-overview", m["WR-000008"][0], site="KOBO-001"))]
P["maint"] = t
P["forbidden"] = [dict(id=i, case="forbidden-403", url=u(i, w1)) for i in ALL]
P["unavailable"] = [dict(id=i, case="store-unavailable-503", url=u(i, w1)) for i in ALL]
for k, v in P.items():
    json.dump(v, open(H / f"targets-{k}.json", "w"), indent=1)
    print(k, len(v))
