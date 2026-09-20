"""Scenario identity rules, owned by the product domain.

`scenario_id` is the only scenario identity. A future run freezes a
`(scenario_id, scenario_version)` pair, so the constraints on the first half of
that pair live here, above the adapter layer, rather than in whichever store
happens to be composed: an identity that is legal on one filesystem and illegal
on another would make scenario identity depend on where the product is
deployed.

This is a parallel module to `sites/identity.py` and deliberately not a reuse
of it. The two answer questions about different identity spaces, raise
different errors, and are free to diverge: a scenario is a document a developer
authors and a Site is an operational subject, and the day one of those needs a
longer id or a different charset, the other must not move with it. The values
coincide today, and that is a fact about today.

Two rules carry the weight, and they are the same two the Site rule carries,
for the same reasons.

Shape. A `scenario_id` is a bounded run of letters, digits, hyphens and
underscores that starts and ends with a letter or a digit. That refuses path
separators, `.`, `..`, absolute-looking and drive-lettered values, whitespace,
empty values and over-length values without knowing anything about a
filesystem. Windows reserved device names are refused by name too, because they
are legal under the charset rule and are not file names on one of the two
platforms this project is developed on.

Case. Identity is compared case-insensitively, so `Fuel-Loss-Event` and
`fuel-loss-event` are the same scenario. Mixed case is accepted by the shape
rule on purpose: if the shape refused it, the case-variant conflict the storage
decision requires could never arise and the rule that detects it would be a
rule about an empty set.
"""

from __future__ import annotations

import re

from assetops_backend.scenarios.ports import ScenarioConfigurationInvalid

#: Bounds. Long enough for a descriptive scenario name, short enough that an
#: id cannot become a payload.
MIN_SCENARIO_ID_LENGTH = 2
MAX_SCENARIO_ID_LENGTH = 64

SCENARIO_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*[A-Za-z0-9]$")

#: Legal under the charset rule, but not usable as a file name on Windows.
#: Refused for every store so identity does not depend on the host.
WINDOWS_RESERVED_NAMES = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{digit}" for digit in range(1, 10)}
    | {f"lpt{digit}" for digit in range(1, 10)}
)

#: What a refusal should tell the author they may use instead. Stated once so
#: the API, the UI and the parser cannot describe the rule differently.
SCENARIO_ID_RULE = (
    f"A scenario ID is {MIN_SCENARIO_ID_LENGTH} to {MAX_SCENARIO_ID_LENGTH} "
    "characters using letters, digits, hyphens, and underscores, starting and "
    "ending with a letter or a digit, for example fuel-loss-event."
)


def validate_scenario_id(value: object, *, where: str = "scenario_id") -> str:
    """Return `value` unchanged if it is a well-formed `scenario_id`.

    Raises:
        ScenarioConfigurationInvalid: with a message naming what is wrong and
            what would be acceptable.
    """
    if not isinstance(value, str) or not value:
        raise ScenarioConfigurationInvalid(
            f"{where} is required and must be text. {SCENARIO_ID_RULE}"
        )

    if (
        len(value) < MIN_SCENARIO_ID_LENGTH
        or len(value) > MAX_SCENARIO_ID_LENGTH
    ):
        raise ScenarioConfigurationInvalid(
            f"{where} {value!r} is {len(value)} characters. {SCENARIO_ID_RULE}"
        )

    if not SCENARIO_ID_PATTERN.match(value):
        raise ScenarioConfigurationInvalid(
            f"{where} {value!r} is not a valid scenario ID. {SCENARIO_ID_RULE}"
        )

    if value.casefold() in WINDOWS_RESERVED_NAMES:
        raise ScenarioConfigurationInvalid(
            f"{where} {value!r} is a reserved device name and cannot be used "
            f"as a scenario ID. {SCENARIO_ID_RULE}"
        )

    return value


def scenario_id_key(scenario_id: str) -> str:
    """Return the comparison key for a `scenario_id`.

    Identity is case-insensitive, so this is what uniqueness, conflict
    detection and lookup all compare. It is a comparison key only: the
    canonical spelling the document declares is what the record carries and
    what the product shows.
    """
    return scenario_id.casefold()
