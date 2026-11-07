"""DD1b1-R Q6: story-time clocks are for a demo prepare or a test database, never anywhere else.

`require_prepare_database` is the one check. A store override that exists only for prepare calls it at
construction, and the demo children call it where they switch their story clock on. It reads the database name from
the URL and opens no connection. Production composition never imports this module and never sets such an override.
"""

from __future__ import annotations

import re
from urllib.parse import unquote, urlsplit

PREPARE_DATABASE = re.compile(r"^assetops_polish_.*$|^.*_test$")


class PrepareClockRefused(RuntimeError):
    code = "PREPARE_CLOCK_REFUSED"


def require_prepare_database(url: str | None) -> None:
    """Refuse a story clock unless the database is `assetops_polish_*` or `*_test`."""
    database = None if not url else (unquote(urlsplit(url).path).lstrip("/") or None)
    if database is None or PREPARE_DATABASE.match(database) is None:
        raise PrepareClockRefused(f"PREPARE_CLOCK_REFUSED: a story clock is not allowed on database {database!r}; "
                                  "it needs assetops_polish_* or *_test.")
