# Architect request: W5-02b K3 build-time points

You are the AssetOps Architect. Read the following:
- .ai/ROLE_CONFIG.md ("Mock fidelity", D1-D6)
- .agent/W5-02-build-spec.md: K3 cards, K3 pre-flight rulings, spec :76
- .agent/W5-02b-K2-rulings.md: in particular 20 and 24
- .agent/W5-02b-K3-handoff.md: the ruling-8 conflict and judgment calls 1-6
- the v69 mock frontend/mockups/v69/index.html (cold-work-incidents, cold-work-maintenance, and any refusal/error panel patterns)

The code is on task/W5-02b-K3-cold-cases. Read it with `git show task/W5-02b-K3-cold-cases:<path>`.

Rule on each point below:
1. The ruling-8 conflict. The W4 refusal block shows a title and a fixed W4 sentence. It shows the server message only for non-cursor `invalid` refusals and has no Retry; basis_changed and cursor refusals show `Reload the first page`. Choose:
   (a) keep W4 as is and correct ruling 8; or
   (b) on COLDCHAIN only, add the server message and Retry. If you choose (b), give the exact copy, the placement and a register row.
   Cite what the mock does.
2. Judgment calls 1-6 in the handoff. Confirm or replace each one exactly:
   - WR link cutoff
   - extra worst-case WR shape
   - nested Read full text inside the Activity/Outcome disclosures
   - case-zero window vs the K2 Actions zero window
   - the CaseLongText duplicate vs a shared extraction, including which file may own it
   - the ledger fields
3. Pre-empt the K2 loop. Rule now, consistently with K2 ruling 24, whether the K3 worst-case all-disclosures-open state is exempt from the 440/650 panel cap while the page caps, containment and no-overflow still apply.

Append the rulings, numbered, to the K3 pre-flight rulings in .agent/W5-02-build-spec.md. Add register rows from R95 if needed. Do not touch product code. Do not commit.
