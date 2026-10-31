# IDX-GAPS Finding index v2: show Findings from assessed days, name the gaps

Status: in_review

Site Finding index `finding-index/2`: one unassessed day no longer blanks a multi-day Findings list. The read is
PARTIAL with the rows from assessed days, `gaps[]` names the days not checked, and a Finding that reaches into one of
those days is withheld. The mini board settles its Finding source on PARTIAL only when its own day is not a gap and
shows a gap line. Branch `task/IDX-GAPS-finding-index-v2`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-idxgaps`, from
main `ca6d7d61b`. Implementation contract: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-sheet-IDX-GAPS.md`
(§0 rules, §2 units U1-U4, §3 copy, §5 register, §8 acceptance, §9 review points) and its Addenda 1-3. Decision
`D-2026-10-31-finding-index-v2`. Packet `.agent/IDX-GAPS-packet.md`.

## Gates (from the sheet)

- Acceptance §8 #1-#8; review points §9. Per-unit review U1 and U2; U3 and U4 slice review.
- Focused tests per unit (§6); check-all at every unit; one full `npx vitest run` and one
  `run-backend-suite-in-container.ps1 -Tier all` at slice end (coordinator's go). Known failures: the 3
  `w1f4VerificationStructure` vitest tests.
- Captures at 390/1440: Findings page PARTIAL and the mini board line.

USER_REVIEW_REQUIRED: false (merges on a fresh independent slice review ACCEPT; the owner sees the PARTIAL Findings
view and the board gap line in the combined walkthrough)
