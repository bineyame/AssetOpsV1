"""Batch 18 read-only probe: GET each global work list on each batch API and print counts (no writes)."""
import json, sys, urllib.request, urllib.error
W = "from=2026-10-14T00:00:00Z&to=2026-10-21T00:00:00Z"
ports = sys.argv[1].split(",")
win = sys.argv[2] if len(sys.argv) > 2 else W
for p in ports:
    for k in ("incidents", "maintenance", "preventive", "operational-records"):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{p}/api/work/{k}?{win}&limit=5") as r:
                d = json.load(r); print(p, k, r.status, d.get("total_count"), d.get("status"), [x.get("site_code") for x in d.get("rows", [])], (d.get("next_cursor") or "")[:6])
        except urllib.error.HTTPError as e:
            print(p, k, e.code, e.read()[:160])
