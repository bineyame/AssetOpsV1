"""3C1b (`specs/3C1-person-on-commands/spec.md` §5 step 5, R7; Q-3C1b-1, Q-3C1b-2, review L1 and L3): the words a
trial action serves about who recorded it. Pure literal data (D-SC1.3). Each `SYSTEM` variant is today's text byte for
byte; each `USER` variant names no person (3C2 adds names). `actor` is the event's `actor_kind`."""
STATEMENTS = {
    # The actor's label: an event's `actor.label`, the change artifact's and the Action read's `label`, and the
    # capability block's `label` (who the command records for this caller).
    "action.actor_label": {
        "slots": {"actor": {"type": "state", "values": ["SYSTEM", "USER"]}},
        "variants": [{"id": "system", "when": {"is": ["actor", "SYSTEM"]}, "text": "SYSTEM demonstration"},
                     {"id": "person", "when": {"is": ["actor", "USER"]}, "text": "Recorded by a signed-in person"}],
        "exhaustive": "actor",
    },
    # The observe command's `statement`.
    "action.observe_note": {
        "slots": {"actor": {"type": "state", "values": ["SYSTEM", "USER"]}},
        "variants": [{"id": "system", "when": {"is": ["actor", "SYSTEM"]},
                      "text": "A state-neutral SYSTEM demonstration note; it changes no application or verification "
                              "state and claims no effect."},
                     {"id": "person", "when": {"is": ["actor", "USER"]},
                      "text": "A state-neutral note recorded by a signed-in person; it changes no application or "
                              "verification state and claims no effect."}],
        "exhaustive": "actor",
    },
    # The change artifact's `statement`, by the APPLIED event's actor.
    "action.change_statement": {
        "slots": {"actor": {"type": "state", "values": ["SYSTEM", "USER"]}},
        "variants": [{"id": "system", "when": {"is": ["actor", "SYSTEM"]},
                      "text": "The Site Foundation reserve was changed by a SYSTEM demonstration command. No measured "
                              "effect, saving or verification is claimed."},
                     {"id": "person", "when": {"is": ["actor", "USER"]},
                      "text": "The Site Foundation reserve was changed by a signed-in person. No measured effect, "
                              "saving or verification is claimed."}],
        "exhaustive": "actor",
    },
    # The note apply stores on the new Foundation revision (a stored value the Foundation history shows); `rule` is
    # the trial rule's ID (`reserve_trial.RULE_ID`).
    "action.publish_note": {
        "slots": {"action_code": {"type": "name"}, "rule": {"type": "name"},
                  "actor": {"type": "state", "values": ["SYSTEM", "USER"]}},
        "variants": [{"id": "system", "when": {"is": ["actor", "SYSTEM"]},
                      "text": "{action_code}: SYSTEM demonstration application of {rule} (a "
                              "policy-sensitivity trial, not a predicted saving)"},
                     {"id": "person", "when": {"is": ["actor", "USER"]},
                      "text": "{action_code}: application of {rule} by a signed-in person (a "
                              "policy-sensitivity trial, not a predicted saving)"}],
        "exhaustive": "actor",
    },
    # 422 `CLIENT_AUTHORITY_FORBIDDEN`: the body named an actor; the server says whom it records.
    "action.client_authority_forbidden": {
        "slots": {"actor": {"type": "state", "values": ["SYSTEM", "USER"]}},
        "variants": [{"id": "system", "when": {"is": ["actor", "SYSTEM"]},
                      "text": "A client cannot name an actor or grant authority; the server records the SYSTEM "
                              "demonstration actor."},
                     {"id": "person", "when": {"is": ["actor", "USER"]},
                      "text": "A client cannot name an actor or grant authority; the server records the signed-in "
                              "person."}],
        "exhaustive": "actor",
    },
    # The action routes' unknown-Site 404 (and the other-tenant person's, byte-equal; D-3C1.6). `site` is the code as
    # the route quotes it.
    "action.unknown_site": {
        "slots": {"site": {"type": "name"}},
        "variants": [{"id": "plain", "text": "No imported Site {site} in this tenant."}],
    },
}
