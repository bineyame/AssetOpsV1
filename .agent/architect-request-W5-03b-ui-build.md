# Architect request: W5-03b E4/E6 build-time points (7)

Read:
- .ai/ROLE_CONFIG.md ("Mock fidelity", D1-D6, lesson 15)
- .agent/W5-03-build-spec.md (E4/E6)
- .agent/W5-03b-ui-preflight-rulings.md
- .agent/W5-03b-ui-questions.md (points 1-7, each with the choice the builder built)
- .agent/W5-03b-ui-handoff.md
- the v69 mock (EV health, EV scenarios)

The code is on task/W5-03b-ev-health-ui. Read it with `git show task/W5-03b-ev-health-ui:<path>`.

Rule on each point exactly. Confirm the builder's choice, or replace it with exact literals, placement and fixture. Cite the mock for each. Pay particular attention to:
- 1: the fault fixture `interrupted` vs `fault`, and the c1/c2 swap. Rule whether the E1b test gap is tracked or fixed here.
- 3: `Sessions →` vs the mock's `View detail →`. If it departs from the mock, add a register row or restore the mock text.
- 4: plurals for n=1. Give the exact singular literals.
- 6: the EV Health subtitle vs the mock. Restore the mock subtitle or record a departure.
- 7: the evEvidenceHref prop route around the substrate guard.

Append the rulings, numbered from 17, to .agent/W5-03b-ui-preflight-rulings.md, and apply them to .agent/W5-03-build-spec.md. Add register rows from R103. Do not touch product code. Do not commit.
