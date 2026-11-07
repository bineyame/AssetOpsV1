"""DD1b1-R2 S3: declare one Site's demo objectives at that Site's story instant, for `demo_combined.finish`.

    python tools/demo_declare_objectives.py <database-url> <fixture-file> <site-code> <iso-instant>

The product CLI (`declare_objective fixture`) with its own store swapped for one carrying the prepare-only recording
clock. Same writer, same stdout (`objectives.json` is unchanged in shape). The store refuses any database that is not
`assetops_polish_*` or `*_test`.
"""

from __future__ import annotations

import sys
from datetime import datetime

from assetops_backend import declare_objective
from assetops_backend.objectives.adapters.postgres_objective_store import PostgresObjectiveStore


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        raise SystemExit("usage: demo_declare_objectives.py <database-url> <fixture-file> <site-code> <iso-instant>")
    url, fixture, site, instant = argv
    recorded = datetime.fromisoformat(instant.replace("Z", "+00:00"))
    store = PostgresObjectiveStore(url, test_recorded_clock_override=lambda: recorded)
    try:
        return declare_objective.main(["fixture", "--file", fixture, "--site", site], store=store)
    finally:
        store.dispose()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
