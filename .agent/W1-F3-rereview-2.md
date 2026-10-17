# W1-F3 fix round 2 re-review (revision 1bad5a47)

Verdict: ACCEPT

Checks run: `npx.cmd tsc --noEmit` clean; siteFinancials and siteFindingHistory test files 119/119 passed. Full suite and layout capture not rerun (cited from the packet: 2017/2017 at the first fix commit, later changes CSS/filter only, 8 focused files 246/246).

1. Interpretation history (M1 fixed): one panel-level `ExactReferences name="price-history"` after the table; rows hold only the badge and "Open version N" (nowrap). Fuel-cost rows untouched.
2. Version-1 dates (M2 fixed): pinned field relabelled "Entered as applying"; a visible "Applied: ..." line (periods with no replaced-on time) sits outside any disclosure; known-from/replaced-on stay in the panel disclosure; the in-use line reads "In use today, version N" (N is the series' in-use version, accurate; the pinned version is named by the region label). No contradiction found.
3. Lows fixed: L3 head link removed; L4 leading-space handled by margin and conditional space; L5 `waitFor` added.
4. Height: 408 vs 211 (1.93x) is honest. The content is the state line, a prices-only line, an eyebrow, 3 real version rows (the mock shows 2) and one closed disclosure. I see no clearly redundant text to cut. Not blocking.
5. No regression: the diff does not touch money gates. Re-pointed assertions are both justified: in-use text gained the version (the M2 requirement), and the Finding-history head-link href checks became null because the link was removed, with the exact version still asserted on the Finding tab. Stricter checks were added. State line is said once.

Findings: none blocking.
