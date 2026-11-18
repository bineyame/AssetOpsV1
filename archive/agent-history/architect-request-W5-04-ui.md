# Architect request: W5-04 UI readiness, 14 points (V2a-V5)

Read:
- .ai/ROLE_CONFIG.md (lesson 15)
- tasks/W5-04-ev-work.md
- .agent/W5-04-build-spec.md
- .agent/W5-04-preflight-rulings.md
- .agent/W5-04-readiness-rulings.md (1-38)
- .agent/W5-02c-K4-preflight-rulings.md
- .agent/W5-02-build-spec.md
- .agent/W5-02-04-mock-measurements.md
- .agent/mock-departure-register.md
- the v69 mock (ev-work, ev-work-incidents, ev-work-maintenance, ev-action)
- .agent/W5-04-ui-readiness-questions.md

Main includes merged K4/K5. The V1 backend is on task/W5-04a-ev-work-backend; read it with `git show task/W5-04a-ev-work-backend:<path>`. Rulings 32-38 unblock its producer.

Rule on all 14 points exactly: the gate, file lists, generalisation seams, literals, attribute names, caps and register rows. Cite the mock for each.
- Point 1: say whether V2a may start before V1b merges.
- Point 3: say where the EV status line lives, given the K4 code shape. Recommended: generalise ColdDomainActionShell with a presentation object.
- Point 8: rule the interim EV index and link behaviour without a dead link. Recommended: pull the EV detail parser and route branch into V2a, or show plain text until V4a.
- Point 12, under lesson 15: give the missing caps and exemptions.

Append the rulings, numbered from 39, to .agent/W5-04-readiness-rulings.md, and apply them to .agent/W5-04-build-spec.md and tasks/W5-04-ev-work.md. Add register rows after the last row, and fix R77, R78, R80 and R104 as needed. Do not touch product code. Do not commit.
