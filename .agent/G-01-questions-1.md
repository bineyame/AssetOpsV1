# G-01 questions for the Architect (batch 1, 2026-10-13)

All defaults below are shipped and fail closed. None changes scoring, K=10, W1 core paths or ranking fixtures.

## Q1. Orphan-scan phrase set

The scan matches `not available yet`, `not yet available` and `no reviewed source` in product string literals and JSX
text (`tools/checks/missing-claim-scan.mjs` `PATTERNS`). It does not match `not recorded`, `unavailable` or
`no results`: of 20 product `not recorded` hits, about 17 are runtime states of an existing capability (for example
"generator operation not recorded" in Dispatch and Finding).

- A. Keep the three phrases. G-02 tags the commissioning copy (`COMMISSIONING_NOT_RECORDED`) as a gap on its own.
- B. Add `not recorded` and baseline every hit. The baseline would then hold runtime copy that is not a gap and can
  never shrink honestly.
- C. Add a per-file opt-in phrase list that G-02..G-05 extend.

Recommendation: A, with G-02 recording the commissioning claim. Shipped default: A. The phrase list sits in the
scanner, so widening it changes the guard and goes to review.

## Q2. The firmware placement shows in every gateway branch, including loading

`G-readiness-gateway-firmware` is rendered once, after the contact branch body, so it appears whatever the contact read
returns (loaded, unknown, unavailable, not found, no gateway, loading). Firmware is missing whatever the contact
state is.

- A. Keep one unconditional placement, `readiness.gateway.firmware`.
- B. Give each branch its own placement ID (`readiness.gateway.firmware.loaded` and so on).

Recommendation: A, because the claim and its absence do not depend on contact. Shipped: A. Vitest and the
1440/390 evidence cover every branch.

## Q3. Baseline identity and the main comparison

Each baseline entry is keyed by file and normalised literal text, with an exact count. Line numbers are not part of
the key, so unrelated edits that move lines do not churn it. The scan compares against the merge-base baseline on
`main` when one exists. At G-01 none exists, so the frozen `SEED_CEILING = 16` is what blocks growth.

- A. Keep this.
- B. Key entries by file and line.

Recommendation: A. Shipped: A.

## Q4. An invalid catalogue refuses `next-work`

When `mock_gaps` exists and is invalid, `nextWork` returns `refused` with type `mock_gaps`. That is a validation stop,
not a scoring input. When the catalogue is absent, it counts as empty.

- A. Keep the refusal.
- B. Report a warning and keep ranking.

Recommendation: A, which matches every other structural refusal. Shipped: A. The invariance fixture proves that a
valid catalogue changes no decision, eligible ID, score or path distance.
