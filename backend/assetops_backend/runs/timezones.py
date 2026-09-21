"""Real IANA time zone membership, for run timing.

A Site declares a time zone as text at creation and nothing has ever checked
that the text names a zone. That was tolerable while a time zone was something
a screen displayed. It stops being tolerable here: a run freezes an interval,
and `Africa/Kampala` and `Africa/Kampalla` are indistinguishable to a pattern
while only one of them can turn an instant into a local time.

So membership is checked against the real database rather than against a
shape. `Area/Location` is the shape of almost every zone name and of every
convincing typo, so a pattern test would accept `Africa/Atlantis` and refuse
`UTC`. Both answers would be wrong.

## Two different failures, deliberately not one

`TimeZoneNotFound` means the database was read and does not hold that name.
`TimeZoneDatabaseUnavailable` means the database could not be read at all, so
nothing is known about any name. Collapsing them would let a deployment
without a time zone database refuse every Site in the product with a message
saying its time zone is not a real one - which is the failure shape T017 and
T018 each paid for once: "we could not look" and "it is not there" are
different facts.

The database is the one Python resolves through `zoneinfo`: the host's if it
has one, and the `tzdata` package otherwise. Windows ships no system database,
so `tzdata` is declared as a backend dependency rather than left to chance -
without it `available_timezones()` finds nothing, and a membership test
against an empty set refuses every zone that exists.
"""

from __future__ import annotations

import zoneinfo
from functools import lru_cache


class TimeZoneNotFound(Exception):
    """The name is not in the IANA time zone database."""


class TimeZoneDatabaseUnavailable(Exception):
    """The IANA time zone database could not be read.

    Never degraded into `TimeZoneNotFound`. A run whose Site's time zone could
    not be checked is not a run whose time zone is wrong.
    """


#: What a refusal tells a reader. Stated once, so the API and a later surface
#: cannot describe the rule differently.
TIMEZONE_RULE = (
    "A site's time zone must be a name in the IANA time zone database, such "
    "as Africa/Kampala. Membership is checked against the database itself, "
    "not against the shape of the name."
)


@lru_cache(maxsize=1)
def _known_zones() -> frozenset[str]:
    """Every zone name the installed database holds.

    Cached because the lookup walks the whole database and the answer cannot
    change inside a process. An empty result is treated as no database rather
    than as a database with nothing in it: the second is not a state the IANA
    database is ever in, and reading it that way would refuse every zone.
    """
    try:
        zones = zoneinfo.available_timezones()
    except Exception as error:  # pragma: no cover - depends on the host
        raise TimeZoneDatabaseUnavailable(
            "The IANA time zone database could not be read, so whether a "
            "site's time zone is a real zone is unknown."
        ) from error

    if not zones:
        raise TimeZoneDatabaseUnavailable(
            "The IANA time zone database holds no zones, so it is not "
            "installed. Whether a site's time zone is a real zone is unknown."
        )

    return frozenset(zones)


def validate_iana_timezone(value: object, *, where: str) -> str:
    """Return `value` unchanged if it names a real IANA time zone.

    Comparison is exact. Zone names are case-sensitive in the database, so
    `africa/kampala` is not `Africa/Kampala`, and accepting it here would mean
    accepting a name the `zoneinfo` constructor will later refuse.

    Raises:
        TimeZoneNotFound: the database does not hold that name.
        TimeZoneDatabaseUnavailable: the database could not be read.
    """
    if not isinstance(value, str) or not value:
        raise TimeZoneNotFound(
            f"{where} is required and must be text. {TIMEZONE_RULE}"
        )

    if value not in _known_zones():
        raise TimeZoneNotFound(
            f"{where} {value!r} is not a name in the IANA time zone database, "
            f"so it cannot be used to place this run in local time. "
            f"{TIMEZONE_RULE}"
        )

    return value
