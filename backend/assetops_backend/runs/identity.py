"""Run identity rules, owned by the product domain.

`run_id` is the only run identity, and it is a third identity space beside
`site_id` and `scenario_id`. This is a parallel module to `sites/identity.py`
and `scenarios/identity.py` and deliberately not a reuse of either: the three
answer questions about different identity spaces and are free to diverge.

Where it differs from both, and why.

**A run identity is allocated, never authored.** A Site is named by the person
configuring it and a scenario by the person writing it, so both have a charset
rule and a refusal message an author reads. Nobody names a run: run setup
allocates one, and the request has no field to put one in. That is what makes
"a scenario label never becomes a `site_id`" hold one level further along -
there is no path from any authored text to a run identity, because no authored
text is consulted when one is made.

**It is allocated here and nowhere else.** `tools/checks/run-setup.ps1` fails
the build if any other module in the runs package generates one, so the
chokepoint is structural rather than a convention. A second allocator is how
two runs end up with one identity.

**The shape is machine-made on purpose.** `run-` followed by a hexadecimal
identifier is a shape no Site and no scenario in this product carries, and a
reader can tell which identity space a value belongs to by looking at it. The
prefix is not what makes it distinct - the allocation is - but a value whose
space is readable is one nobody has to check twice.
"""

from __future__ import annotations

import re
import uuid

from assetops_backend.runs.ports import RunConfigurationInvalid

#: The one prefix a run identity carries.
RUN_ID_PREFIX = "run-"

#: `uuid4().hex` is thirty-two hexadecimal characters. The pattern is written
#: out rather than derived from a length constant, so a change to the shape is
#: a visible change to the rule.
RUN_ID_PATTERN = re.compile(r"^run-[0-9a-f]{32}$")

#: What a refusal tells a reader a run identity is. Stated once so the store,
#: the API and a later inventory cannot describe it differently.
RUN_ID_RULE = (
    "A run ID is allocated by run setup and has the form run- followed by a "
    "thirty-two character hexadecimal identifier. It is never supplied by a "
    "request and is never derived from a site ID or a scenario ID."
)


def allocate_run_id() -> str:
    """Allocate a new run identity.

    It consults nothing. No Site, no scenario, no display text, no version, no
    clock, and no counter reaches this function, so nothing about the run can
    leak into the name of the run.
    """
    return f"{RUN_ID_PREFIX}{uuid.uuid4().hex}"


def validate_run_id(value: object, *, where: str = "run_id") -> str:
    """Return `value` unchanged if it is a well-formed run identity.

    Applied when a stored document is read back, so a hand-edited run document
    cannot introduce an identity the product would never have allocated.

    Raises:
        RunConfigurationInvalid: with a message naming what is wrong.
    """
    if not isinstance(value, str) or not value:
        raise RunConfigurationInvalid(
            f"{where} is required and must be text. {RUN_ID_RULE}"
        )

    if not RUN_ID_PATTERN.match(value):
        raise RunConfigurationInvalid(
            f"{where} {value!r} is not a valid run ID. {RUN_ID_RULE}"
        )

    return value


def run_id_key(run_id: str) -> str:
    """The comparison key for a run identity.

    Allocated identities are already lower case, so this exists for the same
    reason its two siblings do: identity comparison happens in one place, and a
    hand-edited document that capitalised one must not become a second run.
    """
    return run_id.casefold()
