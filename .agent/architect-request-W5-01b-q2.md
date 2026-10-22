# Architect request: W5-01b build follow-ups (Q-C5b-1..4 and builder choices)

You are the AssetOps Architect (Codex). W5-01b C4 and C5 are built on `task/W5-01b-cold-scenarios` (C4 `8fbaf1ed`, C5 `e8147420`, captures `65f1bef0`). Read the handoff and Run entries with `MSYS_NO_PATHCONV=1 git show task/W5-01b-cold-scenarios:.agent/W5-01b-phase-handoff.md`. Also read the C4/C5 cards with their pre-flight rulings in `.agent/W5-01-build-spec.md`, the mock-fidelity rules in `.ai/ROLE_CONFIG.md`, and the v69 `cold-scenarios` screen; the captures are in `.agent/W5-01b-C5-evidence/` on the branch.

Rule with literals:
1. **Q-C5b-1:** `miniDecisions.test.tsx:459` still expects the old cold fallback text, and the file is not on the card. Give the literal edit and add the file to the card.
2. **Q-C5b-2:** the pager's `{page} of {total pages}` has no total in the C4 DTO. Either add the total to the wire (literal field, source and test) or restore the mock's pager another way. Prefer the mock.
3. **Q-C5b-3:**
   - The builder added three ruled literals to the vocabulary gloss list, marked "pending Architect confirmation". Confirm them or replace them.
   - The HISTORICAL notice contains the banned word "committed". Give the replacement literal.
   - The builder added a new `coldScenarios` description key. Confirm it or replace it.
4. **Q-C5b-4:** at 1440 the expanded panel is 2203 px against a 650 cap, because the basis lists 95 IDs and the scroller is ruled only for 390. Rule a mock-faithful fix at 1440 (for example a scroller or a collapsed ID list) with literal CSS and markup, and a test.
5. **The C4 builder's Low deviation:** a stored revision missing its `from`/`to`/`cutoff` keys is left out of the list instead of answering 503. Rule which one.
6. **The blue notice** lacks the mock's info icon. Restore it to the mock, with the literal markup.
7. **Builder choices.** Review the builder choices the handoff lists for C4, and confirm each one or replace it with a literal.

Append "W5-01b build rulings (Q-C5b)" to the C4/C5 section of `.agent/W5-01-build-spec.md`. Write nothing else. Do not commit. End your output with one line per item, and say whether code must change.
