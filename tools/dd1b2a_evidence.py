"""DD1b2-R2: compose the re-probe's evidence file from a stopped mill step (development only).

    python tools/dd1b2a_evidence.py --work var/demo3_dd1b2p --seam .agent/DD-1b2a-probe-2-seam.json --out .agent/DD-1b2a-probe-2.json

Reads `<work>/mill.json` (what the real mill step wrote, including its stop) and the seam tool's report; evidence id
lists in the study's limitations are replaced by their counts so the file stays readable. Adds nothing measured.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", required=True)
    parser.add_argument("--seam", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    mill = json.loads((Path(args.work) / "mill.json").read_text(encoding="utf-8"))
    for limitation in (mill.get("study") or {}).get("limitations", []):
        limitation["evidence_id_count"] = len(limitation.pop("evidence_ids", []))
    seam = json.loads(Path(args.seam).read_text(encoding="utf-8"))
    doc = {"mill": mill, "seam": {"dispositions": seam["dispositions"], "delivered_days": seam["delivered_days"],
                                   "stored": seam.get("stored")}}
    Path(args.out).write_text(json.dumps(doc, indent=1, default=str) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
