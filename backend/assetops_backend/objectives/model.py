"""OUT-D U3: the declaration of one outcome objective and its validation (build sheet OUT-D §3 U3).

Pure apart from the shared `SystemPrincipal`. `unit`, `measure_kind`, `comparison` and `window_rule` always come from
`outcomes.objectives.MEASURES`, never from the caller."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from assetops_backend.financials.assumptions import SYSTEM_CHANNELS, SystemPrincipal
from assetops_backend.outcomes.objectives import MEASURES, MONEY_UNIT, Measure

SOURCES = ("DECLARED", "RECORDED")
CHANNELS = SYSTEM_CHANNELS

SYSTEM_DECLARER = SystemPrincipal(
    actor_id="service:assetops-objective-declarer",
    authorization_basis=("SERVER_ADMINISTRATIVE_TRIGGER: declared by the server-side objective declarer for the "
                         "demonstration; not a customer target"))


class ObjectiveRefused(Exception):
    """A typed refusal: `status` is the HTTP-equivalent code (404 unknown Site, 409 conflict, 422 invalid)."""

    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.status, self.code, self.message = status, code, message


@dataclass(frozen=True)
class Declaration:
    site_code: str
    outcome_key: str
    measure_key: str
    target: Decimal
    currency: str | None
    source: str
    source_note: str
    expected_prior: UUID | None
    idempotency_key: str


def _invalid(message: str) -> ObjectiveRefused:
    return ObjectiveRefused(422, "OBJECTIVE_INVALID", message)


def measure_of(decl: Declaration) -> Measure:
    measure = MEASURES.get(decl.measure_key)
    if measure is None:
        raise _invalid(f"Unknown measure {decl.measure_key!r}.")
    if measure.outcome != decl.outcome_key:
        raise _invalid(f"Measure {decl.measure_key!r} belongs to {measure.outcome}, not {decl.outcome_key}.")
    return measure


def validate(decl: Declaration) -> None:
    measure = measure_of(decl)
    if not isinstance(decl.target, Decimal) or not decl.target.is_finite():
        raise _invalid("The target is a finite decimal number.")
    if decl.target < 0:
        raise _invalid("The target is never negative.")
    if measure.zero_only and decl.target != 0:
        raise _invalid(f"Measure {decl.measure_key!r} admits only a zero target.")
    if measure.unit == MONEY_UNIT:
        if decl.currency is None or not re.fullmatch(r"[A-Z]{3}", decl.currency):
            raise _invalid("A money target names a three-letter currency code.")
    elif decl.currency is not None:
        raise _invalid(f"Measure {decl.measure_key!r} carries no money; no currency is allowed.")
    if decl.source not in SOURCES:
        raise _invalid(f"Source {decl.source!r} is not one of {SOURCES}.")
    if not 1 <= len(decl.source_note) <= 500:
        raise _invalid("The source note is 1 to 500 characters.")
    if not 8 <= len(decl.idempotency_key) <= 128:
        raise _invalid("The idempotency key is 8 to 128 characters.")


def target_string(target: Decimal) -> str:
    """Canonical plain form: 0.20 and 0.2 are the same target; never exponent notation."""
    text = format(target.normalize(), "f")
    return "0" if text in ("-0", "") else text


def payload_sha256(decl: Declaration) -> str:
    """SHA-256 of the sorted compact JSON of the declaration without its idempotency key."""
    body = {"site_code": decl.site_code.lower(), "outcome_key": decl.outcome_key, "measure_key": decl.measure_key,
            "target": target_string(decl.target), "currency": decl.currency, "source": decl.source,
            "source_note": decl.source_note,
            "expected_prior": None if decl.expected_prior is None else str(decl.expected_prior)}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
