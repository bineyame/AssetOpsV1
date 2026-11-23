"""DD1b1-R Q6: story-time clocks are for a demo prepare or a test database, never anywhere else.

`require_prepare_database` is the one check. A store override that exists only for prepare calls it at
construction, and the demo children call it where they switch their story clock on. It reads the database name from
the URL and opens no connection. Production composition imports this module (the objective store, at import) but never sets such an override, so the check only runs with one.
"""

from __future__ import annotations

import re
from urllib.parse import unquote, urlsplit

from assetops_backend.database_target import is_operator_name

#: The demo prepares, the test databases, and the world rung names `tools/world.py` makes (D-DD.168).
PREPARE_DATABASE = re.compile(r"^assetops_polish_.*$|^.*_test$"
                              r"|^assetops_[a-z0-9]{1,24}_audit_(l0|l1|l2)_[0-9a-f]{12}$"
                              r"|^assetops_[a-z0-9]{1,24}_audit_c_[a-z0-9]{1,20}$")


class PrepareClockRefused(RuntimeError):
    code = "PREPARE_CLOCK_REFUSED"


def require_prepare_database(url: str | None) -> None:
    """Refuse a story clock unless the database is `assetops_polish_*`, `*_test` or a world rung. An operator's
    database (`database_target.is_operator_name`) is refused whatever the rest of its name (D-DD.168)."""
    database = None if not url else (unquote(urlsplit(url).path).lstrip("/") or None)
    if database is None or is_operator_name(database) or PREPARE_DATABASE.match(database) is None:
        raise PrepareClockRefused(f"PREPARE_CLOCK_REFUSED: a story clock is not allowed on database {database!r}; "
                                  "it needs assetops_polish_* or *_test.")
