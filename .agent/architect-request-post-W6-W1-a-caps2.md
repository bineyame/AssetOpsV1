# Architect request: W1-a caps under synthetic stress

You are the AssetOps Architect. The W1-a fix round (worktree `../AssetOpsV1-review4`, branch `task/post-W6-W1-a`, head 273fac91) ran the accepted synthetic probe (W3 closeout ruling 1 method) on the real s404 `late-stale` Finding page. Evidence: `../AssetOpsV1-review4/.agent/post-W6-W1-a-fix-probe/` and the packet's fix-round section (`.agent/post-W6-W1-a-packet.md`). Caps from `.agent/post-W6-W1-rulings.md`.

Results (px, 1440/390; clipped 0, document overflow 0 everywhere):
- Where to look next (650/1000): five related rows at 160 chars inline 753/986 → builder applied the Q15 fallback (more than **two** related Findings behind "Show all N related Findings"; threshold 2 is the builder's choice, ruling silent) → 614/682 pass.
- **What limits this conclusion (450/800):** five rows at 160 chars 465/632 — over at 1440 by 15 px (real-cloned rows 357/611 pass).
- **Revision history (850/2000):** every version text field at 160 chars plus five related rows 858/2800 — over at both widths (five real version rows + five 160-char related rows: 728/1683 pass).
- How each limit is set (400/800): 266/497-517 closed, pass (opened exempt).

Rule per Lesson 15 (caps ruled once, from the worst case, all-open exemption, fallback): (1) confirm or set the Q15 threshold; (2) for What limits and Revision history, either revised caps or a specific layout fallback (with target caps), without hiding rows or silently truncating. Write numbered rulings to `.agent/post-W6-W1-a-caps2-rulings.md`. Do not edit product code or `.gitignore`.
