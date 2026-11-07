"""DD1b2-R2: write a Kobo-only probe day list from the v3 list (development only; never part of a prepare).

    python tools/dd1b2a_days.py --out <file> --pick S-13d,S-12d,S+0d,S+1d     # M0 / M1 style subset
    python tools/dd1b2a_days.py --out .agent/DD-1b2-probe-days.json --probe   # the re-probe list

Every entry is a v3 entry unchanged, taken in v3 order; Cold and EV keep their v3 lists (the probe is `--sites kobo`).
`--probe` is the DD1b2-R probe list (13 full days and the story-only neighbours) with S-14 and S-7 added (R2 section 4).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
V3 = ROOT / "backend" / "conversions" / "demo-story-days-v3.json"
PROBE_DAYS = ("S-20d", "S-19d", "S-18d", "S-17d", "S-16d", "S-15d", "S-14d", "S-13d", "S-12d", "S-11d", "S-10d",
              "S-9d", "S-8d", "S-7d", "S-6d", "S-5d", "S+0d", "S+1d")


def build(pick: tuple[str, ...]) -> dict:
    doc = json.loads(V3.read_text(encoding="utf-8"))
    entries = [e for e in doc["sites"]["kobo"] if e["day"] in pick]
    missing = sorted(set(pick) - {e["day"] for e in entries})
    if missing:
        raise SystemExit(f"not in the v3 Kobo list: {missing}")
    doc["sites"]["kobo"] = entries
    doc["label"] = f"DD-1b2a probe (DD1b2-R2): v3 Kobo entries unchanged, {len(entries)} days: {', '.join(pick)}"
    return doc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pick")
    group.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    pick = PROBE_DAYS if args.probe else tuple(args.pick.split(","))
    Path(args.out).write_text(json.dumps(build(pick), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
