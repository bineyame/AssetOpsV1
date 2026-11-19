# Owner review 2 of the delivery-strategy proposal (verbatim, 2026-10-09)

Owner's message: "i have the following feedback regarding the delivery strategy to the architect: [text below]"

---

The revision addresses all eight of my earlier comments, and the worked scores check out arithmetically. I'd approve it with a few amendments. In order of importance:

1. The 5-panel cap weakens your "leverage" criterion

P(c) counts only the five nearest approved core panels, and reach is capped at 5 areas. A node that unblocks 40 panels therefore scores the same as one that unblocks exactly 5 nearby. Your stated principle was "unblocked and unblocks a lot." As written:
- Demo value dominates. It contributes up to 2.0. Since D is the highest downstream value, nearly every upstream W1 node will inherit a 5.
- Breadth of unblocking barely registers. Panels contribute up to 1.5, but only for the nearest 5.

Suggested change: raise or remove the 5-panel cap, keeping the distance discount. Alternatively, add a small term for the uncapped count of approved core panels downstream.

2. Startup now waits until after S2-02, so expect a pause before S3

We'd discussed doing setup in parallel with S2-02. The revision moves all startup work to after S2-02 closeout. Before S3-01 can start, all of the following must then happen in sequence:
- reconciliation
- the 58-panel W1 mapping (size L)
- the schema, checker and report work
- the workflow rule and the check path
- the loop instruction
- the shared-contract decisions
- V-01 adoption
- your W1 core-panel and demo-value input

That's a real gap with no product progress. The benefit is that it doesn't compete with S2-02 for agents and usage. Your call: accept the pause, or allow the planning-only pieces to start during S2-02, since they don't touch S2 code. Those pieces are the shared-contract decisions, drafting the W1 panel mapping and the reconciliation of already-merged S1/S2-01 work.

3. W2 isn't thin

At 25 screens, W2 includes cold-scenarios and ev-scenarios, which are what-if scenario screens. Meanwhile the mini-grid scenarios screen sits in W4+, and the earlier ledger treated it as an estate/finance root. W2 also includes availability, a separate EV analytic. The proposal does say W2 screens are "destinations, not a promise to fill every panel," which softens this. Still, I'd move both scenario screens to W4+ for consistency, and probably availability too.

4. W4+ is one 56-screen wave

Your wave-exit review is the main point where you see results. With 56 screens in a single wave, that review would come very late. Consider splitting W4+ into sub-waves. The table already groups it three ways: mini-grid depth, cold/EV depth, and work/Asset/admin. Alternatively, add a periodic owner review, e.g. every N merged tasks.

5. Shared-contract decisions get no credit from the score

Reach counts only approved consumers, and in W1 only W1 screens are approved. So the pulled-forward cross-domain decisions earn nothing for their W2/W3 reach. That's acceptable, because the proposal makes them mandatory before S3-01 rather than relying on the score. Just be aware the score will undervalue them later as well, whenever they're optional.

Fine as written

- Option (b), with technical and ordering-only edges classified explicitly before any reordering
- The XL rule
- The V-01 adoption gate. No screen is fully Real without recorded V-01 acceptance.
- Review routing, which keeps your S2 Codex batching
- The fail-closed behaviour on unmapped panels and missing owner input
- The allocation table, which totals 110 correctly
