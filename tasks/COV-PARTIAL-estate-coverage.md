# COV-PARTIAL estate coverage v2: partly checked Sites, gap days named

Status: in_review

Estate coverage `estate-coverage/2`: a live mini-grid Site whose period has a day with no assessed selection, and
whose checked days are all current, reads Partly checked (PARTIAL), not Unknown. It names its unchecked days, lists
Findings from the checked days with no amount, and is never counted as covered. No estate root reads Current while a
Site is PARTIAL, and the Portfolio status is Partial. Branch `task/COV-PARTIAL-estate-coverage`, worktree
`C:\Users\assef\Bineyame\AssetOpsV1-covp`, from main `15eed62c8` (build sheets at `0796218fc`). Implementation contract:
`C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-sheet-COV-PARTIAL.md` (§0 rules, §2 rule, §3 Portfolio status,
§4 units U1-U4, §5 tiers, §7 register, §8 decision) and its Addendum 1 (pre-flight Q1-Q3). Decision
`D-2026-10-31-estate-coverage-v2`. Packet `.agent/COV-PARTIAL-packet.md`.

## Gates (from the sheet)

- U1 gets a per-unit review (shared estate seam). U3 and U4 get a slice review.
- Focused tests per unit (§5) and check-all at every commit.
- Merge gate: one `-Tier all` on the tree that already contains LINK-LINEAGE, plus one full `npx vitest run`, both
  on the coordinator's go. Known failures: w301 estate index `INVALID_CURSOR` (pre-existing), and vitest
  `w1f4VerificationStructure` (3 tests).
- Captures at 390/1440: the Portfolio week (the note, then the open drawer) and the estate Findings notice.
- CO-6 in `tools/demo_combined_finish.py` is left to DEMO-A, which has not merged (coordinator Q4).

USER_REVIEW_REQUIRED: false (merges on a fresh independent slice review ACCEPT. The owner sees the partly checked
Portfolio week in the combined walkthrough.)
