# Architect request: W5-04a questions Q6-Q12

Read:
- .ai/ROLE_CONFIG.md
- .agent/W5-04-build-spec.md (V1a/V1b and the producer)
- .agent/W5-04-readiness-rulings.md (1-31, in particular 27 and 29)
- .agent/W5-03b-e5-rulings.md
- .agent/W5-02-build-spec.md (the cold producer and walkthrough precedent)
- .agent/W5-04a-questions.md (Q6-Q12)
- .agent/W5-04a-handoff.md

The code is on task/W5-04a-ev-work-backend. Read it with `git show task/W5-04a-ev-work-backend:<path>`.

Rule on each question exactly:
- Q6: accepted-only max vs max(decided_at). Say whether cold, W4 and EV pins change, and if they do, state the migration and test impact.
- Q7: the EV detail with no intent whose Finding is no longer selected.
- Q8-Q10: the producer cannot make a shifted EV replay on merged code, because the parser pins EV-LAB-001 and the 2026-10-06 window, and the gateway and central runner exist only in test modules. Rule a path that keeps product integrity. One option is to use the registered `ev-interrupted` replay at its native site and window instead of shifting, with the clock, IDs and captures adjusted to match. Another is a named, minimal product change with an owner. Name the exact replay case, the clock points and any register row.
- Q11: give the exact work-request narrative literal.
- Q12: confirm "Depot" stays manifest-only (R78 fallback).

Append the rulings, numbered 32 onward, to .agent/W5-04-readiness-rulings.md, and apply them to .agent/W5-04-build-spec.md and the register, adding rows after its last row if needed. Do not touch product code. Do not commit.
