"""Build per-producer capture target lists for the W2-cold recapture from the audit index (capture-only bookkeeping)."""
import json, re
from pathlib import Path
R = Path(__file__).resolve().parents[1]
d = json.load(open(R.parents[0] / "post-W6-audit/audit-index.json", encoding="utf8"))
S = {"temperature", "coldbackup", "cold-finding", "cold", "cold-findings", "cold-evidence", "cold-evidence-analysis", "cold-financials", "cold-assumptions"}
BASE = "http://127.0.0.1:5195"
out = {"x": [], "n": [], "b": []}
seen = set()
for p in d["pairs"]:
    if p["screen"] not in S: continue
    k = (p["screen"], p["case"])
    if k in seen: continue
    seen.add(k)
    prod = p["producer"]
    m = "n" if "cold normal" in prod else "b" if "backup-failed" in prod else "x"
    path = re.sub(r"^https?://[^/]+", "", p["route"])
    t = {"id": p["screen"], "case": p["case"], "url": BASE + path, "index_batch": p["batch"]}
    if p["screen"] == "cold-finding" and p["case"] == "excursion-finding": t["mock"] = "cold-finding-excursion"
    out[m].append(t)
# URL-only window refusals (new, Q15) on the excursion DB
for sid, path in [("cold", "/sites/COLD-LAB-001"), ("temperature", "/sites/COLD-LAB-001/performance/temperature"),
                  ("coldbackup", "/sites/COLD-LAB-001/performance/backup"), ("cold-findings", "/sites/COLD-LAB-001/findings")]:
    out["x"].append({"id": sid, "case": "one-sided-from", "url": f"{BASE}{path}?from=2026-10-06T19:00:00Z", "index_batch": "new"})
    out["x"].append({"id": sid, "case": "long-32d", "url": f"{BASE}{path}?from=2026-10-01T00:00:00Z&to=2026-11-02T00:00:00Z", "index_batch": "new"})
# shell Q24 representative: excursion Finding against the excursion mock
out["x"].append({"id": "cold-finding", "case": "excursion-rep", "mock": "cold-finding-excursion", "url": f"{BASE}/sites/COLD-LAB-001/findings/00000002-0000-4000-8000-000000000170", "index_batch": "rep"})
# main tab row keeps from/to/known_at on a cold screen
out["x"].append({"id": "cold-findings", "case": "tabs-known-at", "url": f"{BASE}/sites/COLD-LAB-001/findings?from=2026-10-06T19:00:00Z&to=2026-10-06T20:05:00Z&known_at=2026-10-06T20:00:00Z", "index_batch": "rep"})
for k, v in out.items():
    (R / "tools" / f"targets-{k}.json").write_text(json.dumps(v, indent=1), encoding="utf8")
    print(k, len(v))
