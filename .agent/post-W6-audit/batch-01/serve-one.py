"""Post-W6 audit batch 01 launcher (capture-only): starts ONE API of the reviewed
v01a_foundation_walkthrough `serve` mode, with that tool's own env() and tree, on one port.
The tool's serve always starts two APIs on two ports; the audit has a single API port, so the
populated and empty APIs are served one after the other. No data is written.

  python serve-one.py --db <db> --empty-db <db> --work-name <name> --which populated|empty --port 18101
"""
import argparse, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
import v01a_foundation_walkthrough as w  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--db"); p.add_argument("--empty-db"); p.add_argument("--work-name")
p.add_argument("--which", choices=("populated", "empty")); p.add_argument("--port", type=int)
a = p.parse_args()
w.configure(a.db, a.empty_db, a.work_name)
db, tree = (w.DB, w.WORK / "tree") if a.which == "populated" else (w.EMPTY_DB, w.WORK / "tree-empty")
print(f"api {a.which} on 127.0.0.1:{a.port} ({db})", flush=True)
sys.exit(subprocess.call([str(w.PY), "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port", str(a.port)],
                         cwd=str(tree / "host"), env=w.env(db, tree)))
