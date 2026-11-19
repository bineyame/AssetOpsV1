# Owner review of the delivery-strategy proposal (verbatim, 2026-10-09)

Owner's message: "regarding the delivery-strategy, [text below]"

---

I have four substantive comments and four smaller ones.

Substantive

1. The formula starves foundational work.
- Demo value has no rule for work that touches no screen. It's defined per screen, and a task takes the highest value among the screens it touches. Architecture decisions, data fixtures, edge work and the registry reconciliation touch no screen, so their demo value is undefined, effectively 0.
- The panels term will mostly be 0. It counts only newly ready core panels. Earlier we saw that ready-now is zero for every node today, because each panel needs both a read/UI branch and a data branch.
- What's left rewards the wrong thing. The score collapses to roughly reach − effort. It favours small screen tasks over the high-leverage, unblocked work your method is meant to surface.
- Suggested fix: a non-screen node inherits the highest demo value among the approved screens downstream of it. Score the panels term on downstream approved core panels discounted by distance, or allow closure-unlock with a discount, rather than only on newly ready panels.

2. W1 core panels can't be recorded yet, and no prerequisite fixes that.
Line 36 admits the registry can't support per-screen core panels. The checker accepts core_panels only for mapped panels, and only 11 pilot panels are mapped. Of the 21 W1 screens, only finding and sitework have any. Prerequisite 3 should explicitly include mapping the W1 screens' panels to registry nodes. Without it, your W1 confirmation can't be recorded and the loop can't score W1.

3. It's unclear whether the score can reorder S3–S7.
W1 "is the current S1–S7 queue", but the proposal never says whether the score may change that order. For example, S7 Health isn't technically blocked by S5/S6. Decide one of these:
- (a) the queue order is fixed, and scoring applies only from W2, or
- (b) within W1, the score may reorder tasks unless they're technically dependent.

As written, sequenced_after would silently win.

4. V-01 is left ambiguous.
W1 includes "a mock comparison on each supported screen slice". But line 36 says V-01 stays non-executable, and the comparison "does not silently activate V-01". Real requires V-01 acceptance, so leaving V-01 unadopted blocks the end state. Add an explicit decision: adopt V-01 at the S2-02 closeout / pre-S3 gate as a W1 item, which is what we discussed.

Smaller

5. The "> L" rule can never trigger. L is the largest bucket on the S/M/L scale. Either add an XL size, or say "any L candidate must be split or escalated." The second is stricter, and probably too strict.

6. About 89 screens have no wave. "All others require a planned wave before they can be scored" is right, but no one is asked to assign them. Have the Architect propose W2/W3/W4+ allocations for every remaining screen as part of your confirmation. Otherwise W4+ can never be ranked.

7. The setup is large. It's two M, one L, two S and one M, alongside S2-02. Consider phasing it:
- Before the loop starts: 1 (reconcile), 3 (minimal schema, score and next-work), 4 (closeout rule), 5 (check path)
- At W2 start: 2 (split P-work-cases and the EV evidence screens). It only matters from W2/W4 onward.

8. The timing isn't stated. It says "activate only after 1–5 pass and owner confirms" but never ties that to the S2-02 closeout. It also never says shared-contract decisions must be made before S3-01 is activated. That second part is the main reason for switching over early, so state both.
