# Architect request: W5-04c Q1-Q2 (Q2 also binds W5-04b V3b)

Read:
- .ai/ROLE_CONFIG.md
- .agent/W5-04-build-spec.md: the V3b, V4a and V4b cards and the ledger rows
- .agent/W5-04-readiness-rulings.md (1-66, in particular 46)
- .agent/W5-02c-K4-preflight-rulings.md, for the cold-action ledger precedent
- .agent/W5-04c-questions.md
- the v69 mock (ev-work, ev-action)

The code is on task/W5-04c-ev-action. Read it with `git show task/W5-04c-ev-action:<path>`.

Rule on both questions:
1. Q1, ruling 46. Should the EV Work list's live Action link carry `from,to,known_at`? If yes, name the file and owner. SiteWorkActions.tsx is not on V4a's list, so say whether V4a may edit it, and say what the cold list does for parity. If no, correct ruling 46.
2. Q2. Give the exact `data_owner` and `supported_claim` strings for the `ev-action` ledger row, and for the three V3b rows (ev-work-incidents, ev-work-maintenance, and any other row V3b promotes).

Append the rulings, numbered from 67, to .agent/W5-04-readiness-rulings.md, and apply them to .agent/W5-04-build-spec.md. Do not touch product code. Do not commit.
