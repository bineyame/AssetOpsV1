"""Writes targets-<phase>.json (capture URLs only) from the W4-03 walkthrough's own replay records
(var/w403_b13/positive.json or replay.json). Windows mirror tools/w403-mini-decisions-evidence.mjs.
    python mk_targets.py <phase: one|stocked|late>"""
import json, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
REPO = Path(__file__).resolve().parents[4]
WORK = REPO / "var" / "w403_b13"
B = "http://127.0.0.1:5183"
MG, KOBO = "MG-W402-001", "KOBO-001"
S = f"/sites/{MG}"
phase = sys.argv[1]
rec = json.loads((WORK / ("positive.json" if phase in ("one", "stocked") else "replay.json")).read_text(encoding="utf-8"))
d0 = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
z = lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ")
WIN = urlencode({"from": z(d0 - timedelta(days=7)), "to": z(d0 + timedelta(days=1))})
REV = urlencode({"from": z(d0 + timedelta(days=1)), "to": z(d0 - timedelta(days=7))})
LONG = urlencode({"from": "2025-01-01T00:00:00Z", "to": z(d0 + timedelta(days=1))})
PAST = urlencode({"from": "2026-09-01T00:00:00Z", "to": "2026-09-08T00:00:00Z"})
FINDING, FREV = rec["finding"]
OPP = rec["writes"]["opportunity_id"]
u = lambda p, q=None: B + p + (("?" + q) if q else "")
T = []
if phase == "one":
    T += [dict(id="sitework-incidents", case="one-incident", url=u(f"{S}/work/incidents", WIN)),
          dict(id="sitework-maintenance", case="one-request", url=u(f"{S}/work/maintenance", WIN)),
          dict(id="sitework-incidents", case="empty-kobo", url=u(f"/sites/{KOBO}/work/incidents", WIN)),
          dict(id="sitework-maintenance", case="empty-kobo", url=u(f"/sites/{KOBO}/work/maintenance", WIN)),
          dict(id="sitework-incidents", case="empty-past-window", url=u(f"{S}/work/incidents", PAST)),
          dict(id="sitework-incidents", case="refused-reversed", url=u(f"{S}/work/incidents", REV)),
          dict(id="sitework-maintenance", case="refused-reversed", url=u(f"{S}/work/maintenance", REV)),
          dict(id="sitework-incidents", case="refused-long", url=u(f"{S}/work/incidents", LONG)),
          dict(id="sitework-incidents", case="no-window", url=u(f"{S}/work/incidents")),
          dict(id="opportunity-finding", case="supported-current", url=u(f"{S}/opportunities/{OPP}")),
          dict(id="opportunity-finding", case="supported-historical", url=u(f"{S}/opportunities/{OPP}", urlencode({"known_at": (datetime.now(timezone.utc) - timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")}))),
          dict(id="scenarios", case="positive-default", url=u(f"{S}/financials/scenarios")),
          dict(id="alternatives", case="db-time-409", url=u(f"/sites/{KOBO}/findings/{FINDING}/alternatives", urlencode({"revision_id": FREV}))),
          dict(id="alternatives", case="no-revision", url=u(f"/sites/{KOBO}/findings/{FINDING}/alternatives"))]
elif phase == "stocked":
    T += [dict(id="sitework-incidents", case="stocked", url=u(f"{S}/work/incidents", WIN)),
          dict(id="sitework-maintenance", case="stocked", url=u(f"{S}/work/maintenance", WIN))]
else:
    K = rec["k_before_late"]
    miss = next((r["opportunity"]["id"] for r in (rec.get("missing") or {}).get("rows", []) if r["opportunity"].get("first_day") == "2026-10-08"), None)
    T += [dict(id="scenarios", case="populated", url=u(f"{S}/financials/scenarios")),
          dict(id="scenarios", case="empty-window", url=u(f"{S}/financials/scenarios", "from=1970-01-01T00:00:00.000000Z&to=2026-10-01T00:00:00.000000Z")),
          dict(id="scenarios", case="refused-reversed", url=u(f"{S}/financials/scenarios", "from=2026-10-21T00:00:00.000000Z&to=2026-10-01T00:00:00.000000Z")),
          dict(id="scenarios", case="kobo-no-scenarios", url=u(f"/sites/{KOBO}/financials/scenarios")),
          dict(id="alternatives", case="db-time-409-late", url=u(f"/sites/{KOBO}/findings/{FINDING}/alternatives", urlencode({"revision_id": FREV}))),
          dict(id="opportunity-finding", case="late-settled-current", url=u(f"{S}/opportunities/{OPP}")),
          dict(id="opportunity-finding", case="stale-k-before-late", url=u(f"{S}/opportunities/{OPP}", urlencode({"known_at": K}))),
          dict(id="opportunity-finding", case="refused-bad-known-at", url=u(f"{S}/opportunities/{OPP}", "known_at=not-a-time")),
          dict(id="sitework-incidents", case="late-stocked", url=u(f"{S}/work/incidents", WIN)),
          dict(id="sitework-maintenance", case="late-stocked", url=u(f"{S}/work/maintenance", WIN))]
    if miss:
        T.append(dict(id="opportunity-finding", case="missing-day-limited", url=u(f"{S}/opportunities/{miss}")))
out = Path(__file__).with_name(f"targets-{phase}.json")
out.write_text(json.dumps(T, indent=1), encoding="utf-8")
print(out.name, len(T))
