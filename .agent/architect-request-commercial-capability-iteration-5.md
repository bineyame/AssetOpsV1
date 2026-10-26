# Architect request: commercial capability — short final clarification (iteration 5)

You are the AssetOps Architect. The authority for this task is the owner's deep review, word for word, in `.agent/owner-commercial-capability-deep-review-2026-10-26.md`. Read all of it.

The owner says the document has reached diminishing returns. Do not start another broad revision. The owner asks for **a short final clarification, no more than two to three pages**, covering their section 10 table. The five items are in their priority order:

1. **Critical: effort-scope consistency.** For every proposed addition, state its level and its effort separately. The levels are:
   - illustrative commercial context;
   - working modeled decision (declared inputs, enforced constraints, qualified result, persisted basis);
   - integrated demonstrated workflow (reachable from Portfolio/Site, with evidence, limitations and meaningful tests).

   Resolve the Small-versus-Medium inconsistency the owner lists, and define exactly what each estimate includes.
2. **High: decisions that change an outcome.** Make the mini-grid, EV and cold leading decisions show operationally feasible alternatives and a qualified change in the modelled commercial outcome. Detection or exposure alone is not enough. Address the owner's EV questions (other charger allocation, lower-SoC route feasibility, alternatives and their cost) and cold questions:
   - lots under an explicit product/location/exposure rule;
   - the value of potentially affected inventory;
   - no inferred loss fraction;
   - a backup/handling intervention that changes future exposure.
3. **High: minimal portfolio prioritisation policy.** This means an inspectable structure, not a scoring engine:
   - keep comparable opportunities separate from unpriced risks;
   - show urgency, confidence, actionability and explicit unknowns;
   - show a visible placement reason;
   - make a source-quality gap read as "needs investigation", never as low priority.

   Use the owner's MG-A/MG-B/MG-C illustration.
4. **High: opportunity continuity.** Inspect whether existing objects preserve opportunity → finding → intervention → Action → verified technical outcome → revised modelled estimate under compatible assumptions. Test whether that link is needed before proposing any new persistence, and name the smallest gap. Also assess the "post-intervention modelled commercial improvement" middle ground: for example, recomputing the fuel-cost model on comparable accepted later observations after a passing generator trial.
5. **Medium: materiality.** Replace the arbitrary ranges with:
   - break-even thresholds (the owner's contribution equation and hurdle);
   - recurrence and frequency, with persistence, uncertainty and payback rather than one-day × month;
   - customer-value sensitivity.

   Label the inputs as assumptions to validate in discovery, not market magnitudes.

Also, briefly:
- separate event/incident history from performance trajectory, and record trajectory as a gap to assess;
- apply the owner's known quantity / modelled economic effect / unverified business outcome distinction, so that declared demo-tenant contracts, tariffs and inventory feed working calculations rather than reading "unavailable";
- end with the tighter cut the owner asks for: which outcomes are shown through working system behaviour, which through declared commercial context, and which belong in technical walkthroughs or pilot discussions.

**Where to write it:** add it as one concise section near the top of `Docs/demo-sprint/commercial-capability-readiness.md`, titled "Final clarification (iteration 5)". In the same edit:
- correct the effort labels in the coverage and gaps tables so they match it;
- reword the materiality table's ranges as assumptions;
- leave the rest unchanged.

**Owner section 8 verification gate:** this branch now includes current main (`319d8ad6`, which contains the merged final-review fixes). Update the header's inspected HEAD. Spot-check that the files you cite still match: portfolio, finding_episode, actions and verification. Re-run the focused rule tests you cite with the project venv `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe` and `PYTHONPATH="backend;contracts;simulator;gateway;host;."`, and record the counts.

**Limits:**
- no full suites, dev servers or DB creation;
- no product code, test or `.gitignore` edits;
- no five-day plan, scripts or fixtures.
