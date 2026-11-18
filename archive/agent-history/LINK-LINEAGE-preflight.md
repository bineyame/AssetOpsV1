# LINK-LINEAGE pre-flight (build sheet §8)

Checklist results (worktree `C:\Users\assef\Bineyame\AssetOpsV1-link`, branch `task/LINK-LINEAGE-board-action`):

- [x] HEAD `0796218fc` (build-sheets commit directly on `15eed62c8`; no code change), tree clean.
- [x] `exact_actions` appears only in `site_outcomes/board.py` (3 hits: `:468` def, `:477`, `:494`; plus the `_row`
      parameter `:500` and use `:608`). No other file.
- [x] `FindingReadService.history(tenant_id, site_id, finding_id, revision_id=None, *, after_revision_no=0, limit=200)`
      (`analytics/finding_read.py:570`); `page.next_after_revision_no` present (`:613`); rows carry `transition`,
      `lifecycle`, `revision_no`, `episode {start,end}` via `_summary` (`:257-275`).
- [x] `FindingFact` constructions (b1 test fakes, `cold.py:214`, `ev.py:245`, `mini.py:493`) are positional only up to
      `href` and use keywords after; a last defaulted field is safe.
- Never `-ExecutionPolicy`; files written with Edit/Write (no BOM).

Questions (batched):
1. DB names: the b4/e4 Postgres tests U3 edits already build `assetops_out_b_<case>_test` / `assetops_out_e_board_test`
   (their own helpers). The sheet says only `assetops_link_<x>_test`. Keep the existing helper names (no new DB name)?
2. CO-1: `tools/demo_combined_finish.py` is not on this branch (it is in the `-demo3` tree). Confirm DEMO-A has not
   merged, so this slice does not edit CO-1 (sheet §5 "Who edits CO-1").
3. Register = `.agent/mock-departure-register.md` row R552 (stays `open`, note appended)?
