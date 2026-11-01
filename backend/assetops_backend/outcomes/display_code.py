"""POLISH §3 record codes: the display form of a stored public record code.

Storage keeps the zero-padded `PREFIX-NNNNNN` codes (for example the `ACT-[0-9]{6,}` CHECK of migration 0016), and
every API `code`/`action_code`/`public_code` field stays as stored. Only server-composed sentences and labels show
the display form: the prefix plus the number zero-padded to at least 3 digits (`ACT-000001` -> `ACT-001`,
`WR-000006` -> `WR-006`, `ACT-001234` -> `ACT-1234`), matching the mock's `ACT-048`/`INC-203`.
"""
from __future__ import annotations


def display_code(code: str | None) -> str | None:
    """The display form of one stored record code; any other text (or None) is returned unchanged."""
    if code is None:
        return None
    prefix, sep, number = code.partition("-")
    # The outcomes package stays pure (no `re`): an upper-case ASCII prefix and an all-digit number, else unchanged.
    if (not sep or not prefix or not number or not prefix[0].isascii() or not prefix[0].isupper()
            or not all(c.isascii() and (c.isupper() or c.isdigit()) for c in prefix)
            or not all(c in "0123456789" for c in number)):
        return code
    return f"{prefix}-{int(number):03d}"


#: POLISH §3 (ids): a Finding link or label with no held title is plain "Finding" (never an 8-character id).
FINDING_LABEL = "Finding"


def finding_label(title: str | None) -> str:
    """The Finding's stored title as its visible label, else `FINDING_LABEL`."""
    return title or FINDING_LABEL
