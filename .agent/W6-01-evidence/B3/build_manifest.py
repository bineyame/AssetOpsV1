"""Builds manifest.json for a W6-01b capture set from app-<state>.json and seed-<state>.json (B2/B3 evidence)."""
import json, sys
from pathlib import Path
here = Path(sys.argv[1]); unit = sys.argv[2]; states = json.loads(sys.argv[3]); extra = json.loads(sys.argv[4])
out = {"unit": unit, **extra, "r8_note": "Record the actual requests and identify the response rendered by this capture; "
       "duplicate development reads do not prove a second stored result.", "states": []}
for state, meta in states.items():
    app = json.loads((here / "screenshots" / f"app-{state}.json").read_text(encoding="utf-8"))
    seed = here / f"seed-{state}.json"
    stored = json.loads(seed.read_text(encoding="utf-8")) if seed.exists() and seed.stat().st_size else None
    out["states"].append({"state": state, **meta, "stored": stored, "captured_at": app["captured_at"],
                          "results": [{k: r.get(k) for k in ("width", "route", "image", "ready", "api", "heights", "row_heights",
                                                             "collapsed_details_max_h", "table_scroll", "document_width", "text", "appended", "note")}
                                      for r in app["results"]]})
(here / "manifest.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print("states", len(out["states"]))
