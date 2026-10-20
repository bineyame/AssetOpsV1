# Architect request: W3-01 q14 (final review)

Read:
- `.agent/W3-01-final-review.md`;
- `.agent/W3-01-build-spec.md`, all rulings;
- q14-1 in `git show 60e0bf55:.agent/W3-01-pending-rulings.md`, on branch `task/W3-01-estate-claim-action-roots`.

Rule with exact artifacts:
1. q14-1. On the Finding lenses at 1440, the card row is 150 px against a cap of 146, caused by the ruled honest zero copy on Awaiting verification. The reviewer recommends accepting it with a cap waiver. Rule it: either a waiver with its recorded rationale and a new cap value, or an exact copy or layout change.
2. Confirm the High fix: `.estate-page .data-table thead th:first-child{background:var(--surface-sunken);z-index:2}`, plus a recapture of one Findings shot and one Actions shot at 1440 and 390. Alternatively, give the exact replacement.
3. The Lows: `FindingsIndex` is orphaned. Delete it now, or carry it.

Append the result as "Run 14 rulings (q14)" to `.agent/W3-01-build-spec.md`. Write nothing else. Do not commit.
