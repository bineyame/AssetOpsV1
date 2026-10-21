"""W4-03 unit 2a: the mini-decision refusal vocabulary (`.agent/W4-03-build-spec.md` "API, exact wire, ordering and
errors", closure 1 Q1-Q3/Q12-Q16, closure 4 N8).

`DecisionRefused` carries the code, HTTP status and API message of the error table. The W4-01 `WORK_*` codes stay
in `work/model.py`; this module does not remap them.
"""

from __future__ import annotations

MESSAGES = {
    "UNAUTHENTICATED": "Sign in to read decisions.",
    "DECISION_WRITE_FORBIDDEN": "This actor cannot change decisions at this Site.",
    "DECISION_USER_AUTH_REQUIRED": "A signed-in user identity is required for user-attested decisions.",
    "DECISION_NOT_FOUND": "No decision with this ID at this Site.",
    "DECISION_BASIS_CHANGED": "The selected basis changed; reload the first page.",
    "DECISION_DUPLICATE_KEY": "This key was used for different decision content.",
    "DECISION_CORRECTION_CONFLICT": "This decision has a newer correction; reload its latest version.",
    "DECISION_INPUT_INVALID": "A required decision field or unit is invalid.",
    "DECISION_ATTESTATION_INVALID": "Service attestation must name the authenticated service, job and rule version.",
    "DECISION_LINK_SCOPE_INVALID": "A linked record is not in this Site and tenant.",
    "DECISION_COUNTEREVIDENCE_INVALID": "Ruling out needs cited accepted counterevidence for this Finding's window.",
    "INVALID_WINDOW": "Select a valid Site-local window.",
    "INVALID_KNOWN_AT": "Select a time no later than now.",
    "INVALID_CURSOR": "Reload the first page.",
    "INVALID_LIMIT": "`limit` must be an integer from 1 to 100.",
    "DECISION_STORE_UNAVAILABLE": "Decision records could not be read or saved.",
}
STATUS = {
    "UNAUTHENTICATED": 401, "DECISION_WRITE_FORBIDDEN": 403, "DECISION_USER_AUTH_REQUIRED": 403,
    "DECISION_NOT_FOUND": 404, "DECISION_BASIS_CHANGED": 409, "DECISION_DUPLICATE_KEY": 409,
    "DECISION_CORRECTION_CONFLICT": 409, "DECISION_INPUT_INVALID": 422, "DECISION_ATTESTATION_INVALID": 422,
    "DECISION_LINK_SCOPE_INVALID": 422, "DECISION_COUNTEREVIDENCE_INVALID": 422, "INVALID_WINDOW": 422,
    "INVALID_KNOWN_AT": 422, "INVALID_CURSOR": 422, "INVALID_LIMIT": 422, "DECISION_STORE_UNAVAILABLE": 503,
}


class DecisionRefused(Exception):
    """A refused mini-decision request; nothing it would have written is committed."""

    def __init__(self, code: str, message: str | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.status = STATUS[code]
        self.message = MESSAGES[code] if message is None else message

    def detail(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


def invalid() -> DecisionRefused:
    return DecisionRefused("DECISION_INPUT_INVALID")
