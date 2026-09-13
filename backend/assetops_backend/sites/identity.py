"""Site identity rules, owned by the product domain.

`site_id` is the only Site identity, and every later run, envelope, evidence
record, and analytic is keyed on it. So the constraints on it live here, above
the adapter layer, rather than in whichever store happens to be composed: a
`site_id` that is legal on one filesystem and illegal on another would make
Site identity depend on where the product is deployed.

Two rules carry the weight.

Shape. A `site_id` is a bounded run of letters, digits, hyphens, and
underscores that starts and ends with a letter or a digit. That refuses path
separators, `.`, `..`, absolute-looking and drive-lettered values, whitespace,
empty values, and over-length values without needing to know anything about a
filesystem. Windows reserved device names are refused by name as well, because
they are legal under the charset rule and are not file names on one of the two
platforms this project is developed on.

Case. Identity is compared case-insensitively, so `MG-002` and `mg-002` are the
same Site. That is enforced here rather than inherited from a case-insensitive
filesystem, so the same two documents collide the same way on every host.
"""

from __future__ import annotations

import re

from assetops_backend.sites.ports import SiteConfigurationInvalid

#: Bounds. Long enough for the identity schemes real operators use, short
#: enough that an id cannot become a payload.
MIN_SITE_ID_LENGTH = 2
MAX_SITE_ID_LENGTH = 64

SITE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*[A-Za-z0-9]$")

#: Legal under the charset rule, but not usable as a file name on Windows.
#: Refused for every store so identity does not depend on the host.
WINDOWS_RESERVED_NAMES = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{digit}" for digit in range(1, 10)}
    | {f"lpt{digit}" for digit in range(1, 10)}
)

#: What a refusal should tell the user they may use instead. Stated once so
#: the API, the UI, and the parser cannot describe the rule differently.
SITE_ID_RULE = (
    f"A site ID is {MIN_SITE_ID_LENGTH} to {MAX_SITE_ID_LENGTH} characters "
    "using letters, digits, hyphens, and underscores, starting and ending "
    "with a letter or a digit, for example MG-002."
)


def validate_site_id(value: object, *, where: str = "site_id") -> str:
    """Return `value` unchanged if it is a well-formed `site_id`.

    Raises:
        SiteConfigurationInvalid: with a message naming what is wrong and what
            would be acceptable.
    """
    if not isinstance(value, str) or not value:
        raise SiteConfigurationInvalid(
            f"{where} is required and must be text. {SITE_ID_RULE}"
        )

    if len(value) < MIN_SITE_ID_LENGTH or len(value) > MAX_SITE_ID_LENGTH:
        raise SiteConfigurationInvalid(
            f"{where} {value!r} is {len(value)} characters. {SITE_ID_RULE}"
        )

    if not SITE_ID_PATTERN.match(value):
        raise SiteConfigurationInvalid(
            f"{where} {value!r} is not a valid site ID. {SITE_ID_RULE}"
        )

    if value.casefold() in WINDOWS_RESERVED_NAMES:
        raise SiteConfigurationInvalid(
            f"{where} {value!r} is a reserved device name and cannot be used "
            f"as a site ID. {SITE_ID_RULE}"
        )

    return value


def site_id_key(site_id: str) -> str:
    """Return the comparison key for a `site_id`.

    Identity is case-insensitive, so this is what uniqueness, conflict
    detection, and lookup all compare. It is a comparison key only: the
    canonical spelling the user supplied is what the record carries and what
    the product shows.
    """
    return site_id.casefold()
