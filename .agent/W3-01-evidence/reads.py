"""W3-01 commit 4: record the public estate reads for one capture state (full bodies, unedited).
Usage: python reads.py <state> <name>=<path?query> ...  -> reads-<state>.json; prints a one-line digest per read."""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:9741"
OUT = Path(__file__).resolve().parent
state, pairs = sys.argv[1], sys.argv[2:]
reads = {}
for pair in pairs:
    name, path = pair.split("=", 1)
    try:
        with urllib.request.urlopen(BASE + path) as r:
            status, body = r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        status, body = e.code, json.loads(e.read() or b"null")
    reads[name] = {"path": path, "http": status, "body": body}
    b = body if isinstance(body, dict) else {}
    cov = [(s.get("site_id", "")[-4:], s.get("state")) for s in b.get("coverage", {}).get("sites", [])]
    print(name, status, b.get("status"), "total", b.get("total_count"), "rows", len(b.get("rows", [])),
          "summary", b.get("summary"), "cov", cov, "token", (b.get("selection_token") or "")[:20],
          "cursor", bool(b.get("next_cursor")), b.get("detail") or b.get("code") or "")
(OUT / f"reads-{state}.json").write_text(json.dumps(reads, indent=2, sort_keys=True) + "\n", encoding="utf-8")
