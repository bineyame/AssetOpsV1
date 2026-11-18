# Architect request: W5-04a review items (V1a/V1b ACCEPT, V2a ACCEPT)

Read the following:
- .ai/ROLE_CONFIG.md, lesson 15
- .agent/W5-04-build-spec.md
- .agent/W5-04-readiness-rulings.md (1-52)
- .agent/W5-04a-review.md: V1a/V1b review, Lows L1-L6, Architect items 1-4
- .agent/W5-04-V2a-review.md: V2a review, Lows 1-4, Architect items 1-10
- .agent/W5-04-V2a-questions.md
- the v69 mock (ev-work)

The code is on task/W5-04a-ev-work-backend and task/W5-04b-ev-work-ui. Read it with `git show <branch>:<path>`.

Rule on all 14 Architect items exactly. Cite the mock for each.
- V1 item 1, list/detail disagreement after a later head: decide whether the EV index row resolves at the intent pin, as the detail does under ruling 27, or at the read cutoff, and what V2a shows. Give the code location, literals and tests.
- V1 item 2, pending/stale capture: confirm pure vectors only, or authorise a registered-path late event.
- V1 items 3-4: the fixture clock artifact and the unused ev_selected_provenance port.
- V2a items 1-10: confirm the reviewer's recommendations or replace them.

Then state the fix list per branch, so each builder fixes in one round:
- V1: L1-L6.
- V2a: Low-1 to Low-4, plus anything V1 item 1 requires.

Also confirm that V2b (producer-backed captures, now that V1b is reviewed) may start immediately after these rulings, and that the first merge is V1a+V1b+V2a+V2b together.

Append the rulings, numbered from 53, to .agent/W5-04-readiness-rulings.md. Apply them to .agent/W5-04-build-spec.md. Amend register rows R75 and R77 as needed. Do not touch product code. Do not commit.
