# LINK-LINEAGE The board links an Action across basis-only Finding revisions

Status: in_review

The Site outcome board joined a mini Action to its origin Finding only on the exact revision, so a Finding whose
revisions after the Action were pure basis refreshes lost the applied status signal and the Cost Must-not-harm line
(register R552). One narrow board rule widens that join.
Branch `task/LINK-LINEAGE-board-action`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-link`, from main `15eed62c8`.
Contract: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-sheet-LINK-LINEAGE.md` units U1-U3 (self-contained).
Decision `D-2026-10-31-board-action-refresh-lineage`. Packet `.agent/LINK-LINEAGE-packet.md`.

## Gates (from the sheet)

- `refresh_chain` (sheet §2): every revision after the origin up to and including the shown one is BASIS_REFRESHED
  with the origin's lifecycle and episode bounds; missing rows, a gap, origin >= shown or a failed read never link.
- The widened join drives only the applied signal and Must-not-harm (`board.py` `linked_actions`); Earlier lists,
  estate joins (`estate/portfolio.py`), cold and EV, the wire, the schema and the frontend are unchanged.
- Mini only: one `finding_history` port read per Finding, only when an Action points at an earlier revision; a failed
  read is a PARTIAL board and no link.
- Tests: the sheet §3 P/N/B/M cases and the b4/e4 Postgres pins with the inline history rule.
- Tier: sheet §4 scoped sets, check-all at every commit, one `-Tier all` on the coordinator's go.

USER_REVIEW_REQUIRED: false (a read-time board rule the owner approved; merges on a fresh independent review ACCEPT,
before DEMO-A edits CO-1)
