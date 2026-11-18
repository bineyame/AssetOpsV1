# Architect request: W6-global-Work caps, R356 and clipped list cells

You are the AssetOps Architect. The W6 verification (worktree `../AssetOpsV1-review8`, branch `task/post-W6-W6-global`, evidence commit 6d82f084 under `.agent/post-W6-W6-evidence/`, product f3da6e90) ran the accepted synthetic probe (five rows, every intended text field at exactly 160 chars, asserted; 136 runs) on the real mounted pages. Rulings: `.agent/post-W6-W6-rulings.md` (Q15 caps, Q16 widths). Apply the owner's standing UI bar (`.agent/owner-ui-ux-guidance-2026-10-25.md`; name the pattern) and Lesson 15.

Results (px 1440/390): Incident cases 647/737 vs 700/800 pass; Corrective WRs 657/737 vs 700/800 pass; Preventive plan 599/690 vs 600/690 pass (390 exactly at cap); Operational records 631/744 vs 650/780 pass; wr-record activity 622/763 vs 700/provisional 900 pass; Lifecycle 442/194 vs 500/prov 250 pass.
**Over:** Work done 503 at 1440 vs 500 (real 442); History 558 at 1440 vs 550 (6-event request + pager; real 485).
**Provisional (unruled) caps to ratify:** Case boundaries 150/150 (fixed copy, 103/126); Record a manual reading 400/600 (325/513); How records are used 400/300 (325/223); Work done 390 800 (690); Lifecycle 390 250; wr-record activity 390 900.

Decide:
1. Work done and History at 1440: revised caps or a layout fallback (target caps), no hidden rows.
2. Ratify or set the provisional caps.
3. **R356 fails on the real page:** columns match Q16 (1100 px total), but when five rows trigger the operational records table's 500 px vertical scroller, its 15 px scrollbar reduces client width to 1090 (scrollWidth 1100 > clientWidth 1090). Builder's cheap fix within Q16's retune clause: take ~10 px off one column. Rule which column(s)/values (or another fix, e.g. scrollbar-gutter).
4. **Clipped list cells (new finding):** two-line clamped list cells with no full-text disclosure or title clip 160-char text (closed and all-open), contradicting Q15's no-clipping rule. Affected: Incident cases (Site, Severity, Owner, Findings); Corrective WRs (Asset/site, Owner); Preventive plan (Asset/site, Trigger, Last done, Next due, What it proves); Operational records (Record, Type, Site, By, Feeds). WR panels show none. Rule the fix (e.g. unclamped wrap, or clamp with accessible full value via disclosure/tooltip), and re-state the caps under it.

Write numbered rulings to `.agent/post-W6-W6-caps-rulings.md`. Do not edit product code or `.gitignore`.
