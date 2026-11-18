# Architect request: W3-02 c3-q3 (second EV Site has no scenario)

Read `.agent/W3-02-build-spec.md` ("Commit-3 rulings (c3)") and `.agent/W3-02-pending-rulings.md` c3-q3.

Code: `fefa5ab4` on `task/W3-02-estate-evidence-money-basis`.

EV-LAB-002 imports and publishes its bindings in the same DB, but `create_draft_run` refuses it with VERSION_UNAVAILABLE, because every `config/scenarios/ev-*.yaml` names EV-LAB-001.

Rule the exact honest path:
- either a test-only scenario file for EV-LAB-002 (give its path, its content delta from an existing ev scenario, and where it is allowed to live, test fixtures or config);
- or a parameterised Site code on the existing scenario, with the exact loader change and its owner;
- or the closure-2 N3 stop rule, with the exact limitation copy.

Give the assertions the two skipped tests must then satisfy.

Append the result as "Commit-3 rulings (c3b)" to `.agent/W3-02-build-spec.md`. Write nothing else. Do not commit.
