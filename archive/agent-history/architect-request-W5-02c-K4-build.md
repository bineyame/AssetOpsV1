# Architect request: W5-02c K4 build-time points

Read:
- .ai/ROLE_CONFIG.md (lesson 15)
- .agent/W5-02-build-spec.md (K3 ruling 20; K4 cards)
- .agent/W5-02c-K4-preflight-rulings.md (ruling 12)
- .agent/W5-02c-K4-questions.md (Q1 with three options)
- .agent/W5-02c-K4-handoff.md (judgment calls 1-8)
- the v69 mock (cold-action, cold-work-incidents, cold-work-maintenance)

The code is on task/W5-02c-K4-cold-action. Read it with `git show task/W5-02c-K4-cold-action:<path>`.

Rule on the following:
1. Q1: K4 ruling 12 contradicts K3 ruling 20 on the `UTC and IDs` IDs. Choose one option and give the exact CSS and capture-check behaviour, so that every state passes after one recapture.
2. Judgment calls 1-8: confirm or replace each one exactly. Pay most attention to:
   - 2: the strict client refusal;
   - 3: the Finding version full row;
   - 4: no-criteria at K1;
   - 5: the sentence when a WR is open or in progress;
   - 6: the unused COLD_ACTION_PREPARING.

Append the rulings, numbered 14 onward, to .agent/W5-02c-K4-preflight-rulings.md, and apply them to .agent/W5-02-build-spec.md. Add register rows from R102 if needed. Do not touch product code. Do not commit.
