# Architect request: W5-04a V1a/V1b build questions (Q1-Q5)

Read:
- .ai/ROLE_CONFIG.md
- .agent/W5-04-build-spec.md (V1a/V1b)
- .agent/W5-04-preflight-rulings.md
- .agent/W5-04-readiness-rulings.md (rulings 6, 8, 10)
- .agent/W5-03b-e5-rulings.md (A6)
- .agent/W5-02-build-spec.md (the W5-02a core K1 rulings on how the cold intent stores and recomputes its pin, and on refusal order)
- .agent/W5-04a-questions.md
- .agent/W5-04a-handoff.md

The code is on task/W5-04a-ev-work-backend. Read it with `git show task/W5-04a-ev-work-backend:<path>`.

Rule on each question with exact keys, routes, messages, order and test cases:
1. Q1: where the Finding pin lives (a/b/c). Prefer consistency with how W5-02 cold recomputes its pin, unless EV needs something different, and say why.
2. Q2: the refusal message and the validation order for malformed intent or case-link bodies before the Action is resolved. Say whether domain-specific checks may move after the 404, and name the exact message for each case.
3. Q3: correct ruling 8's route (`/ev/financials/scenarios`) and the session-list watermark cross-check, or replace that check.
4. Q4: what "the selected accepted set" is. Stay consistent with E5 A6 unless there is a reason not to.
5. Q5: confirm the producer and walkthrough scope stays in V1b.

Append the rulings to .agent/W5-04-readiness-rulings.md, numbered 27 onward, and apply them to .agent/W5-04-build-spec.md. Do not touch product code. Do not commit.
