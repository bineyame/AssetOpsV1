"""Post-W6 audit batch 02: run an existing reviewed producer/walkthrough UNCHANGED except for its database
and work-folder NAMES, so it writes only to this batch's audit-owned `assetops_audit_b2*_test` database and a
batch-owned work folder (the coordinator's isolation rule). Nothing else in the producer is altered: its
seeding, staging, comparisons and verification run exactly as reviewed.

    python run_renamed_producer.py <producer.py> <renames.json> -- <producer args...>

<renames.json> is a list of [old_text, new_text] pairs; each old_text must occur in the producer source exactly
as given (the run refuses otherwise), so a rename can never silently miss or widen. The source is executed as
`__main__` with `__file__` set to the original path so the producer resolves the repository exactly as before.
"""
import json
import sys
from pathlib import Path

producer, renames_file = Path(sys.argv[1]).resolve(), sys.argv[2]
rest = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
source = producer.read_text(encoding="utf-8")
for old, new in json.loads(Path(renames_file).read_text(encoding="utf-8")):
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"rename refused: {old!r} occurs {count} times in {producer.name} (must be exactly 1)")
    source = source.replace(old, new)
    print(f"[rename] {old!r} -> {new!r}", flush=True)
sys.argv = [str(producer), *rest]
sys.path.insert(0, str(producer.parent))
code = compile(source, str(producer), "exec")
exec(code, {"__name__": "__main__", "__file__": str(producer)})
