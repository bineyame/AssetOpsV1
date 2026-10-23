# Architect request: rule on the W5-04 pre-flight (46 questions)

You are the AssetOps Architect. Read .ai/ROLE_CONFIG.md, in particular "Mock fidelity", "Departure categories and register" (D1-D6) and "Builder pre-flight". Also read .agent/W5-04-build-spec.md, tasks/W5-04-ev-work.md, .agent/W5-02-04-mock-measurements.md, .agent/mock-departure-register.md, .agent/W5-02-build-spec.md and .agent/W5-03-build-spec.md.

Input: .agent/W5-04-preflight-questions.md (46 questions from the W5-04 builder; their evidence cites main 8884d86b).

Rule on every question. The builder must not decide anything. For each question:
- give a concrete ruling: the schema, constraint names, file ownership, fixtures, names and clock points;
- cite the v69 mock (file and selector) wherever the question affects a screen;
- label any departure from the mock MOCK DEVIATION, with a D1-D6 category and a new register row (the next free ID after the register's last row). D3 items get a correction, not a register row.

Settle these explicitly:
- Q1/Q2: the gate order against W5-02 K2a-K5 and W5-03a/b. The planned order is W5-03a, then K2a/K2b, K3a/K3b, W5-03b, K4a/K4b/K5, then W5-04. Say which units wait and which, if any, can start earlier.
- Q5-Q8: the 0035 constraint design, including names, and whether rejecting three cold items stays a DB-level or becomes an app-level check.
- Q19-Q23: name the replay case, the Finding, the sessions and the clock points.
- Q41-Q43: the registry promotion order.
- Replace the stale pre-W6 wording (W6 is complete on main).

Write the rulings to .agent/W5-04-preflight-rulings.md, numbered to match the questions. Apply them to .agent/W5-04-build-spec.md and tasks/W5-04-ev-work.md. Add register rows to .agent/mock-departure-register.md, and fix the owning units of R03/R04. Do not touch product code. Do not commit.
