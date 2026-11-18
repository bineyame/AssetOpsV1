# Architect request: W3-estate closeout questions

You are the AssetOps Architect. Rule on three points raised by the W3-estate verification batch (branch `task/post-W6-W3-estate`, head 76f66f25; packet at `../AssetOpsV1-review6/.agent/post-W6-W3-estate-packet.md`; recapture in `../AssetOpsV1-review6/.agent/post-W6-W3-estate-recapture/`). Governing rulings: `.agent/post-W6-W3-estate-rulings.md` (point 8, Q10, Q17) and `.agent/post-W6-W3-estate-build-rulings.md`. Read only what you need.

1. **Cap-proof method.** Producers cannot emit five 160-character rows. The batch measured caps with a layout probe on the real captured pages: after the screenshot of record, it replaces the rows with five clones carrying 160-character text and measures the closed panel. Accept or reject this as the cap proof (and if rejected, state the required method).
2. **Meaning of "five 160-character rows" for the Consequence register.** Only the Limit text at 160 chars: 626/726 (cap 800/1200, passes). Every cell at 160 chars (Site name, Category, Window too): 938/1575 (fails). Rule which reading applies, per Lesson 15 (caps ruled once, from the worst case). If the every-cell reading applies, give the layout fix (wrapping/truncation-with-full-text/column rules) or a revised cap, with the fallback.
3. **Stale Portfolio copy.** `frontend/src/estate/portfolioWords.ts:26` (in review6) still says "Site detail is unavailable for these cells", but Q10 now links every cell except EV Backup. Give the exact replacement copy (or removal) and where it applies.

Write the rulings to `.agent/post-W6-W3-closeout-rulings.md` as numbered, exact, implementable rulings. Do not edit product code or `.gitignore`.
