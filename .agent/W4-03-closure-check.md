# W4-03 spec-review closure check (2026-10-20)

Worktree AssetOpsV1-plan2, main 4b314405. Read-only check of "Review closure (2026-10-20)" in `.agent/W4-03-build-spec.md` against the 36 questions in `.agent/W4-03-spec-review.md`.

## Result: 32 CLOSED, 4 OPEN (Q1, Q4, Q11/Q6 residue, Q24)

Q2, Q3, Q5, Q7-Q10, Q12-Q23, Q25-Q36 are CLOSED. Q1, Q4, Q11/Q6 residue and Q24 are OPEN.

### OPEN
- Q1 (dev write path): the principal `service:w403-fixture`, attestation, grant string and refusals are literal. Missing: how a running dev backend receives the injected principal (W4-01 Q28 only specifies test injection), and which tool replays the fixture commands so a dev stack shows a persisted scenario for the reload capture. Name the injection hook, any env gate, and the replay tool.
- Q4 (enqueue): "on a committed mini_depth_selection(renewable) enqueue a mini_opportunity job" does not say whether this is a DB trigger or a worker scan. W4-02 is declared unchanged, and the `0030` catalog delta counts only the ten append-only triggers. Rule the mechanism and its catalog count (`recompute_job.domain` is text with no CHECK, so no DDL is needed).
- Q11/Q6 residue: build-spec L230 still says "W4-02 KOBO publication v5". Commit row 3 still names `test_site_and_estate_opportunity_lens_exact_route`. Neither appears in the supersession index. Add both, with a replacement test asserting that the chip and estate lens stay unavailable.
- Q24: the closure splits the Financials row by Site type but gives no literal resulting `Scenarios` count in the `navigation-truthfulness.ps1` `$expectedTabs` (now one occurrence). State the post-split multiset.

### Required checks
- **Write path executable in dev and fixture:** the fixture half is CLOSED (Q1-Q3 closure: literal request JSON for all 5 POSTs, responses, idempotency hashing, USER 403, attestation 422, client authorization_basis 422). The dev-runtime half is OPEN (Q1 above).
- **Estate-lens change:** CLOSED as an explicit deferral, not an amendment. It is recorded in the closure and the supersession index, and `tasks/W4-03-mini-decisions-work.md` carries it. W3-01 estate tokens and rows are untouched. Site chip gap copy is given (`Opportunity index unavailable; open the renewable evaluation...`). `Opportunities×1` stays in the guard multiset, so the guard is unaffected. Only the stale test and fixture text above remains.
- **Mock slots kept:** CLOSED. Four opportunity cards, Bounded opportunity, Next decision and Consequence basis keep their order. The Alternatives Explanation/Evidence/Disposition slots and geometry are kept. The Scenarios empty example sentence is retained. The Work column slots are preserved with a secondary line under Activity. The Analysis tab and the global breadcrumb are dropped as intentional deviations, recorded in the spec. Confidence keeps its slot, showing "Not assessed".

### Seams spot-checked against merged main
All held:
- `recompute_job.domain` is text with no CHECK (`0022:22`, `0025:17`).
- `0009_finding_store.py` has only `UNIQUE(tenant_id,site_id,id)` on `finding_revision` (`:105`), so the "no composite pair FK" ruling is right.
- `ledger_append_only()` exists at `0005:310`.
- `FINDING_CHILD_VIEWS = [evidence,history,recommendation]` (`operatorSiteRoutes.ts:235`).
- `UnavailableChip` Opportunities is at `SiteFindingIndex.tsx:82`.
- `UnavailableTab label="Scenarios"` is a single source occurrence in `SiteAnalyticsFrames.tsx:682`.
- `action_api.py` `command_access` and `finding_api.development_access` / `ACCESS_BASIS` exist.
- The guard `$expectedTabs` and `$expectedChips` match the spec's description.
- The catalog delta reconciles. The original DDL counts 9 tables, 18 UNIQUE, 17 REFERENCES, 4 indexes and 9 primary keys. Adding 1 scenario create-key UNIQUE, 1 link idempotency UNIQUE, 2 scenario-link UNIQUE and 3 FKs gives 10/22/20/5, plus 10 triggers, as stated.
- Nairobi bounds 2026-10-05T21:00Z through 2026-10-10T21:00Z are correct for UTC+3.
W4-01, W4-02, W3-01 and `mini_decisions/` are unmerged prerequisites. They were checked only against their frozen specs.

## New questions
- N1: the assumption table gives the tariff unit as `ISO4217/kWh`, but the example and the money rule use `USD/kWh`. State that the currency is the unit's prefix, validated against ISO 4217, and which literal the API accepts.
- N2: the per-screen registry paths are to be "independently reviewed" but are not named. Name the registry file and node paths, or leave them to the unit-9 reviewer.
