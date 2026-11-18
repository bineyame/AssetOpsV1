# Architect request: revise the owner delivery-strategy proposal (2026-10-09)

The owner reviewed `.agent/D-2026-10-09-owner-delivery-strategy-proposal.md` and gave four substantive and four smaller comments, verbatim in `.agent/owner-delivery-strategy-review-1-2026-10-09.md` (authoritative; read it fully). The original owner draft is `.agent/owner-delivery-strategy-draft-2026-10-09.md`.

Please revise the proposal in place (keep it **proposed**, not in `.ai/DECISIONS.md`), addressing every comment explicitly:
1. Scoring for non-screen work (inherited downstream demo value; panels term over downstream approved core panels discounted by distance, or discounted closure-unlock) — give the exact formula and show it on a few real current candidates (e.g. registry reconciliation, an S3 architecture decision, S3-01, S7-01) with their numbers, so the owner can see it no longer collapses to reach − effort.
2. Make mapping the W1 screens' panels to registry nodes an explicit part of prerequisite 3 (say how many panels/screens that is today).
3. Recommend (a) or (b) for whether the score may reorder S3–S7, with reasons, and state how `sequenced_after` interacts.
4. An explicit V-01 adoption decision at the S2-02 closeout / pre-S3 gate as a W1 item, consistent with "Real requires V-01 acceptance".
5. Fix the > L rule (XL bucket or another rule); recommend one.
6. Propose W2/W3/W4+ allocations for every remaining manifest screen (a table), for owner confirmation.
7. Phase the prerequisites as the owner suggests (or say why not).
8. State the timing: loop activation relative to the S2-02 closeout, and that shared-contract decisions are made before S3-01 is activated.
Add a short "Changes from the previous proposal" section at the top mapping each owner comment to the change, and refresh "Owner confirmation needed".

Do not execute the prerequisites. An implementer is working on the S2-02 branch concurrently; touch only the proposal file (and `.agent/` notes). No product code; leave edits uncommitted.
