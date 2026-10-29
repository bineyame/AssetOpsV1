"""PERF-02: drop saved set-ups of old code fingerprints (backend/tests/setup_cache.py), keeping the newest three.

    python tools/sweep-setup-cache.py <cache dir>

Saved set-up folders are <cache dir>/<code8>/<key>/ and their databases assetops_sc_<code8>_<key>_test on the server
named by ASSETOPS_TEST_DATABASE_URL (a *_test base). Only databases with that prefix are dropped.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

KEEP = 3


def main() -> None:
    root = Path(sys.argv[1])
    url = os.environ.get("ASSETOPS_TEST_DATABASE_URL", "")
    if not root.is_dir() or not url:
        return
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url
    from sqlalchemy.pool import NullPool

    assert (make_url(url).database or "").endswith("_test")
    codes = sorted((p for p in root.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime, reverse=True)
    stale = codes[KEEP:]
    engine = create_engine(url, poolclass=NullPool, isolation_level="AUTOCOMMIT")
    dropped = 0
    try:
        with engine.connect() as admin:
            for folder in stale:
                names = admin.execute(text("SELECT datname FROM pg_database WHERE datname LIKE :p"),
                                      {"p": f"assetops_sc_{folder.name}_%"}).scalars().all()
                for name in names:
                    assert name.startswith("assetops_sc_") and name.endswith("_test"), name
                    admin.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
                    dropped += 1
                shutil.rmtree(folder, ignore_errors=True)
            # half-published saves of a crashed run
            for name in admin.execute(text("SELECT datname FROM pg_database WHERE datname LIKE 'assetops_sc_%_wip_test'"
                                           )).scalars().all():
                admin.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
    finally:
        engine.dispose()
    print(f"setup cache: {len(codes)} code fingerprints, swept {len(stale)} ({dropped} databases)")


if __name__ == "__main__":
    main()
