"""3C1b (spec §5 step 5, R7; Q-3C1b-1, Q-3C1b-2): the cases of the `action.*` statements (hand literals). The SYSTEM
cases are the texts on `main` before 3C1b, copied by hand; the USER cases name no person."""
from __future__ import annotations

from assetops_backend.i18n import Name, State

from statement_cases import Case

SYSTEM, USER = State("SYSTEM"), State("USER")
CODE, RULE = Name("ACT-0001", "action.action_code"), Name("reserve-trial-1", "action.rule_id")

CASES = [
    Case("action.actor_label", "system", {"actor": SYSTEM}, "SYSTEM demonstration"),
    Case("action.actor_label", "person", {"actor": USER}, "Recorded by a signed-in person"),
    Case("action.observe_note", "system", {"actor": SYSTEM},
         "A state-neutral SYSTEM demonstration note; it changes no application or verification state and claims no "
         "effect."),
    Case("action.observe_note", "person", {"actor": USER},
         "A state-neutral note recorded by a signed-in person; it changes no application or verification state and "
         "claims no effect."),
    Case("action.change_statement", "system", {"actor": SYSTEM},
         "The Site Foundation reserve was changed by a SYSTEM demonstration command. No measured effect, saving or "
         "verification is claimed."),
    Case("action.change_statement", "person", {"actor": USER},
         "The Site Foundation reserve was changed by a signed-in person. No measured effect, saving or verification "
         "is claimed."),
    Case("action.publish_note", "system", {"actor": SYSTEM, "action_code": CODE, "rule": RULE},
         "ACT-0001: SYSTEM demonstration application of reserve-trial-1 (a policy-sensitivity trial, not a predicted "
         "saving)"),
    Case("action.publish_note", "person", {"actor": USER, "action_code": CODE, "rule": RULE},
         "ACT-0001: application of reserve-trial-1 by a signed-in person (a policy-sensitivity trial, not a predicted "
         "saving)"),
    Case("action.client_authority_forbidden", "system", {"actor": SYSTEM},
         "A client cannot name an actor or grant authority; the server records the SYSTEM demonstration actor."),
    Case("action.client_authority_forbidden", "person", {"actor": USER},
         "A client cannot name an actor or grant authority; the server records the signed-in person."),
    Case("action.unknown_site", "plain", {"site": Name("'KOBO-001'", "site.code")},
         "No imported Site 'KOBO-001' in this tenant."),
]
