# Architect request: amend the owner delivery-strategy proposal (2026-10-09)

The owner reviewed the revised proposal `.agent/D-2026-10-09-owner-delivery-strategy-proposal.md` and says they would approve it with amendments. Their feedback, addressed to the Architect, is verbatim in `.agent/owner-delivery-strategy-review-2-2026-10-09.md` (authoritative; read it fully).

Please amend the proposal in place (keep it **proposed**, not in `.ai/DECISIONS.md`):
1. Panel leverage: raise/remove the 5-panel cap (keeping the distance discount) or add a small uncapped-downstream-panels term; give the exact formula, keep the score bounded/comparable, and recompute the four worked examples plus one high-fan-out example showing breadth now registers against demo value.
2. Item 2 is explicitly your call: decide between accepting the pre-S3 pause or allowing the planning-only pieces (shared-contract decisions, drafting the W1 panel mapping, reconciliation of already-merged S1/S2-01 work) to start during S2-02. State the decision and reason, how it respects the owner's Codex-usage batching rule (`.ai/ROLE_CONFIG.md`, owner rule 2026-10-09), and which pieces still wait for S2-02 closeout.
3. W2 thinness: move `cold-scenarios`, `ev-scenarios` and (probably) `availability` to W4+, or say why not; keep the total at 110.
4. Split W4+ into sub-waves (e.g. W4 mini-grid depth, W5 cold/EV depth, W6 work/Asset/admin) and/or add a periodic owner review; recommend one.
5. Note that the score undervalues optional shared-contract decisions and say how that is handled (e.g. a rule that cross-domain contracts are mandatory gates, not scored candidates).
Update "Changes from the previous proposal" (map review-2 items to changes) and "Owner confirmation needed". Keep everything the owner marked "fine as written".

Do not execute prerequisites. An implementer is working on the S2-02 branch concurrently; touch only the proposal file (and `.agent/` notes). No product code; leave edits uncommitted.
