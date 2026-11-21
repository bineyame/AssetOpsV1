"""3C2 (spec section 2.5, D-3C2.14): the cases of `agreed_action.*`, one per variant. The English is section 2.5's
sentence and section 4's state words, written by hand (W2), never computed."""
from __future__ import annotations

from assetops_backend.i18n import Count, State, Word

from statement_cases import Case

#: The facts every refusal sentence is rendered with (`agreed.refusal_sentence`): the code and the title bounds.
_BOUNDS = {"least": Count(1, "character"), "most": Count(200, "character")}


def _refused(code: str, english: str) -> Case:
    return Case("agreed_action.refused", code.lower(), {"code": State(code), **_BOUNDS}, english)


CASES = [
    Case("agreed_action.state", "word", {"state": Word("action_state", "OPEN")}, "Open"),
    Case("agreed_action.state", "word", {"state": Word("action_state", "OVERDUE")}, "Overdue"),
    _refused("BAD_TITLE", "Write a title of 1 to 200 characters."),
    _refused("UNKNOWN_TENANT", "No operator has that name."),
    _refused("PERSON_NOT_FOUND", "The person agreeing is not an active person of this operator."),
    _refused("PERSON_ROLE_REQUIRED", "Only the operator's executive records an agreed change."),
    _refused("SITE_NOT_FOUND", "This operator has no Site with that code."),
    _refused("FACTOR_NEEDS_SITE", "Name the Site the factor belongs to (--site)."),
    _refused("FACTOR_UNKNOWN", "No factor has that name."),
    _refused("FACTOR_SITE_TYPE", "This factor does not apply to that Site's type."),
    _refused("OWNER_NOT_FOUND", "The owner is not an active person of this operator."),
    _refused("OWNER_SCOPE", "The owner's role does not cover where this change applies."),
    _refused("DUE_IN_PAST", "The due date is before today."),
    _refused("BAD_DUE", "Write the due date as YYYY-MM-DD, like 2026-12-15."),
    _refused("NO_DATABASE", "Set DATABASE_URL to the operator's database."),
    _refused("ACTIONS_UNAVAILABLE", "The Actions store cannot be reached right now."),
]
