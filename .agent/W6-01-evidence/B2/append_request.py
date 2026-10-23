"""W6-01b B2 cursor-change capture step: append one selected `demo` KOBO-001 request after page one was read.

    python append_request.py <db> <clock>

Writes through the same `tools/w601_seed.py` Writer (real W4 `WorkService`, fixture principal) at `<clock> + 2s`,
which is before the page-one cutoff (real DB time) and inside `[2026-10-14, 2026-10-21)`, so the reused page-one
cursor is refused 409. Prints the stored row as JSON. The tool file itself is B1-owned and is not edited here.
"""
import importlib.util
import json
import sys
from datetime import timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("w601_seed", REPO / "tools" / "w601_seed.py")
seed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed)
db, clock = sys.argv[1], seed.utc(sys.argv[2])
if not seed.DB_NAME.match(db):
    raise SystemExit("a private assetops_w601_*_test database is required")
url = seed.db_url(db)
writer = seed.Writer(url, seed.WriteClock(clock + timedelta(seconds=2)), seed._existing_sites(url), clock)
try:
    writer.request(seed.A, None, "Late request appended after page one")
finally:
    writer.close()
print(json.dumps({"append": True, "written": writer.written}))
