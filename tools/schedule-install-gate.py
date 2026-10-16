"""Installation gate for the S4-02d environment schedule tick (D-2026-10-14-s402d-schedule-storage-and-install-gate).

    python tools/schedule-install-gate.py --host-class private|walkthrough|demo|pilot [--registry PATH]

Installs nothing. It reads the delivery registry and says whether a persistent tick timer may be installed for the
host class, printing the reason; exit 0 when open, 2 when closed.

- `private`: a developer's private database; open (optional one-minute tick, the per-Site timer removed).
- `walkthrough`: an isolated walkthrough database; never a timer (explicit `tick` invocations only); exit 2.
- `demo`: owner-visible; open only when `I-late-reading-series-and-money-limit` is `resolved`.
- `pilot`: a real-Site pilot; open only when that node, `I-attested-real-source-provenance` (always required, even
  if `real_pilot_requires` omits it or is stale; S4-05b) and every `real_pilot_requires` node are `resolved`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "frontend" / "docs" / "architecture" / "v69-dependency-registry-pilot.json"
F1 = "I-late-reading-series-and-money-limit"
#: S4-05b phase 2: real-source provenance is a pilot requirement independent of the registry's own list.
REAL_SOURCE = "I-attested-real-source-provenance"


def decide(registry: dict, host_class: str) -> tuple[bool, str]:
    status = {n["id"]: n.get("status") for n in registry.get("nodes", [])}
    if host_class == "private":
        return True, "private development database: an optional one-minute tick is allowed; remove the per-Site timer"
    if host_class == "walkthrough":
        return False, "isolated walkthrough database: explicit tick invocations only, no persistent timer"
    needed = [F1] + ([REAL_SOURCE] + list(registry.get("real_pilot_requires") or []) if host_class == "pilot" else [])
    needed = list(dict.fromkeys(n if isinstance(n, str) else n.get("id") for n in needed))  # each listed once
    open_ = [f"{n} ({status.get(n, 'missing')})" for n in needed if status.get(n) != "resolved"]
    if open_:
        return False, (f"{host_class} host is owner-visible or real: do not install the tick until resolved: "
                       + ", ".join(open_))
    return True, f"{host_class} host: gate nodes resolved ({', '.join(needed)}); install one timer and retire the " \
                 "per-Site consequence timer (backend/README-db.md)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="schedule-install-gate")
    parser.add_argument("--host-class", required=True, choices=("private", "walkthrough", "demo", "pilot"))
    parser.add_argument("--registry", default=str(REGISTRY))
    args = parser.parse_args(argv)
    registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    ok, reason = decide(registry, args.host_class)
    print(("OPEN: " if ok else "CLOSED: ") + reason)
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
