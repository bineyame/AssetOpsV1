"""W4-03 unit 2a: the mini-decision refusal vocabulary (`.agent/W4-03-build-spec.md` "API, exact wire, ordering and
errors", closure 1 Q1-Q3/Q12-Q16, closure 4 N8).

`DecisionRefused` carries the code, HTTP status and API message of the error table. The W4-01 `WORK_*` codes stay
in `work/model.py`; this module does not remap them.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

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

    def __init__(self, code: str, message: str | None = None, status: int | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.status = STATUS[code] if status is None else status
        self.message = MESSAGES[code] if message is None else message

    def detail(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


def invalid() -> DecisionRefused:
    return DecisionRefused("DECISION_INPUT_INVALID")


def case_not_found() -> DecisionRefused:
    """u5 unit 8: an unknown or foreign W4-01 case is W4-01's own 404 `WORK_CASE_NOT_FOUND` (code and message from
    `work/model.py`, not remapped)."""
    from assetops_backend.work.model import MESSAGES as WORK_MESSAGES
    return DecisionRefused("WORK_CASE_NOT_FOUND", WORK_MESSAGES["WORK_CASE_NOT_FOUND"], status=404)


#: Closure 1 Q1-Q3: the server-side W4-03 write grant prefix (`SITE_DECISION_WRITE:<principal id>`).
GRANT_PREFIX = "SITE_DECISION_WRITE:"


@dataclass(frozen=True)
class DecisionPrincipal:
    """Closure 2 Q1 / closure 4 N6: the server-derived W4-03 SERVICE principal, scoped to one tenant/Site.

    Only a server-side injection (`create_app(mini_decision_principal=...)`) returns one; a request body never
    installs or overrides it. W4-01's string `Principal` is a different type and never authorizes a decision."""
    kind: str
    id: str
    tenant_id: UUID
    site_id: UUID
    grant: str
