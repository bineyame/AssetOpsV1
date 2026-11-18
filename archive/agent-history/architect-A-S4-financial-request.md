# Architect request: A-S4-financial (2026-10-13)

Owner choice (verbatim selection, 2026-10-13): "Money decision (A-S4-financial)". It was picked from a contested next-work ranking (`.agent/next-work-2026-10-13i.json` on main `9fde68f`: A-S4-financial 2.215 vs A-S5-overview 2.144, gap 3.21%) and recorded in `.agent/owner-next-work-2026-10-13c.md`. Owner Codex rule: batch questions and keep usage efficient.

State: main `9fde68f`. S1, S2, S3-01, S4-01 (Finding identity), S4-03 (Finding Evidence/History), V-01a/b and G-01/G-02 are merged. Branch `plan/A-S4-financial` (from main) is for this decision.

Already verified by the coordinator on this tree (do not repeat):
- `tools/check-all.ps1` passes all 9 guards.
- `--next-work` / `--verify-report` exit 0.
- `A-S4-financial` is eligible: its requires `A-finding-episode` and `A-actor-identity` are resolved.
- `D-financial-basis` (2.415) and the other S4-02 nodes rank higher but are technically blocked only by this decision.

One batched call:

1. **Record `A-S4-financial`** in `.ai/DECISIONS.md`. The registry node says: "Financial assumption author_id, versioned price basis and bounded consequence for S4-02." Decide the contract that S4-02 ([tasks/S4-02-bounded-financials.md](../tasks/S4-02-bounded-financials.md), an outline) builds on. Cover:
   - FinancialAssumptionRevision identity, versioning and time validity (`assumption_key`, revision, currency, unit, valid window), with `author_id` under `A-actor-identity` (server-derived, never client-asserted).
   - Price/maintenance basis kinds for the first mini-grid Finding (fuel price at minimum), and what "bounded" means: range vs point, the unit/quantity source, and rounding.
   - FinancialConsequenceRevision lineage to the exact FindingRevision and assessment revision plus the assumption revisions used. A price change makes a new consequence revision while the Finding claim and quantity stay fixed.
   - Honest states: no price gives "unpriced", never zero. Incompatible currency/unit/basis never silently sums. Stale or superseded assumptions.
   - What S4-02 persists and reads, and which v69 panels (`financials`, `assumptions`, `mini`) it may claim versus leave as named gaps.
   - The boundary to the later `A-money-comparability` (outside W1 ranking) and to `financial_scenario`. The parts that cold-chain/EV will reuse.

   Use the existing technical design (`frontend/docs/architecture/production-shaped-mvp-technical-design.md`, the `financial_assumption_revision` / `financial_consequence_revision` rows and the FinancialConsequence shape), `D-2026-10-09-pre-s3-claim-routes-and-actor`, `D-2026-10-09-pre-s3-shared-contract-scope`, your A-finding-episode decision, and the v6.9 mock screens. Then update the registry node `A-S4-financial` (status resolved, with evidence) in `frontend/docs/architecture/v69-dependency-registry-pilot.json`, or list the exact edit. Say what S4-02's Planner refinement must take from the decision, and whether S4-02 stays one S/M slice or must split.

2. **Small batched ruling (G-02 review carry C-c, `.ai/MILESTONE_REVIEW_BACKLOG.md` "G-02 carries").** `G-readiness-commissioning` is typed `data_source/absent`, but its copy ("No commissioning record type exists") reads as a contract gap, like productive-use. State the rule for choosing `missing_kind` (data_source vs contract) so that G-03..G-05 apply it consistently. Say whether this gap's kind should change now or at W1-exit allocation. Both kinds are unrankable today.

Write `.agent/architect-A-S4-financial-answers.md`. Say whether you want the owner to weigh in, with your decision and justification. No product code. Leave edits uncommitted (the coordinator commits; your sandbox cannot write `.git`).
