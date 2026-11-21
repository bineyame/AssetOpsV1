"""3C2 (spec section 2.5; D-3C2.14): the agreed change's state word and the record command's refusal sentences.

Pure literal data (D-SC1.3). One refusal statement keyed by the refusal code (a `state` slot, exhaustive), because a
key names a kind of statement in two segments (`KEY_FORM`); each variant carries section 2.5's exact sentence. The
title bounds come in as counts and the due-date example as an `example` slot, so no digit sits in a template
(D-SC1.21).
"""
STATEMENTS = {
    "agreed_action.state": {
        "slots": {"state": {"type": "word", "vocabulary": "action_state", "form": "label"}},
        "variants": [{"id": "word", "text": "{state}"}],
    },
    "agreed_action.refused": {
        "slots": {
            "code": {"type": "state", "values": [
                "BAD_TITLE", "UNKNOWN_TENANT", "PERSON_NOT_FOUND", "PERSON_ROLE_REQUIRED", "SITE_NOT_FOUND",
                "FACTOR_NEEDS_SITE", "FACTOR_UNKNOWN", "FACTOR_SITE_TYPE", "OWNER_NOT_FOUND", "OWNER_SCOPE",
                "DUE_IN_PAST", "BAD_DUE", "NO_DATABASE", "ACTIONS_UNAVAILABLE"]},
            "least": {"type": "count", "bare": True},
            "most": {"type": "count"},
            "due_example": {"type": "example", "text": "2026-12-15"},
        },
        "exhaustive": "code",
        "variants": [
            {"id": "bad_title", "when": {"is": ["code", "BAD_TITLE"]},
             "text": "Write a title of {least} to {most}."},
            {"id": "unknown_tenant", "when": {"is": ["code", "UNKNOWN_TENANT"]},
             "text": "No operator has that name."},
            {"id": "person_not_found", "when": {"is": ["code", "PERSON_NOT_FOUND"]},
             "text": "The person agreeing is not an active person of this operator."},
            {"id": "person_role_required", "when": {"is": ["code", "PERSON_ROLE_REQUIRED"]},
             "text": "Only the operator's executive records an agreed change."},
            {"id": "site_not_found", "when": {"is": ["code", "SITE_NOT_FOUND"]},
             "text": "This operator has no Site with that code."},
            {"id": "factor_needs_site", "when": {"is": ["code", "FACTOR_NEEDS_SITE"]},
             "text": "Name the Site the factor belongs to (--site)."},
            {"id": "factor_unknown", "when": {"is": ["code", "FACTOR_UNKNOWN"]},
             "text": "No factor has that name."},
            {"id": "factor_site_type", "when": {"is": ["code", "FACTOR_SITE_TYPE"]},
             "text": "This factor does not apply to that Site's type."},
            {"id": "owner_not_found", "when": {"is": ["code", "OWNER_NOT_FOUND"]},
             "text": "The owner is not an active person of this operator."},
            {"id": "owner_scope", "when": {"is": ["code", "OWNER_SCOPE"]},
             "text": "The owner's role does not cover where this change applies."},
            {"id": "due_in_past", "when": {"is": ["code", "DUE_IN_PAST"]},
             "text": "The due date is before today."},
            {"id": "bad_due", "when": {"is": ["code", "BAD_DUE"]},
             "text": "Write the due date as YYYY-MM-DD, like {due_example}."},
            {"id": "no_database", "when": {"is": ["code", "NO_DATABASE"]},
             "text": "Set DATABASE_URL to the operator's database."},
            {"id": "actions_unavailable", "when": {"is": ["code", "ACTIONS_UNAVAILABLE"]},
             "text": "The Actions store cannot be reached right now."},
        ],
    },
}
