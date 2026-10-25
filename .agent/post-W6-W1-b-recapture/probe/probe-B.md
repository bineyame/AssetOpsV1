# Synthetic cap probes, agent B (SYNTHETIC LAYOUT EVIDENCE, NOT PRODUCT DATA)

Method: W3 closeout ruling 1. Tool `tools/B-probe.mjs` (+ `tools/B-cdp.mjs`). Real mounted page, unmodified screenshot
first (`B-*-baseline-*-app.png`), then in-session: first real row cloned into five rows, intended fields set to 160
chars, `verified` asserted, closed panel measured (`B-*-synthetic.png`, `B-probe-results-*.json`).

| panel | page | variant | width | verified | panel h | cap | row heights | clipped | doc overflowX | table scroller |
|---|---|---|---|---|---|---|---|---|---|---|
| Action history | s601b action-history all | ah-160x5 (meaning prose leaf; codes kept) | 1440 | yes 5/5, counts line | 558 | (record) | 74,75,75,75,74 | caption (visually hidden) only | 0 | 1120/1120 |
| Action history | same | ah-160x5 | 390 | yes | 963 | 800 | 145 x5 | caption only | 0 | 461/318 |
| Action history | same | ah-160x5-cell (whole meaning cell = prose) | 1440 | yes | 454 | (record) | 54 x5 | caption only | 0 | 1120/1120 |
| Action history | same | ah-160x5-cell | 390 | yes | 2266 | 800 | 406 x5 (meaning column 70px) | caption only | 0 | 366/318 |
| Evidence requirements | s602b guardrail action-evidence | er-160x5 (requirement + status detail) | 1440 | yes 10/10 | 521 | 450 | 58,59,59,59,58 | caption only | 0 | 1120/1120 |
| Evidence requirements | same | er-160x5 | 390 | yes 10/10 | 1114 | 800 | 157,158,158,158,157 | caption only | 0 | 318/318 |

Baselines (unmodified): Action history 355 (1440) / 451 (390); Evidence requirements 396 / 605.
Result: Action history 390 cap EXCEEDED (963; 2266 when the meaning cell has no unbreakable reference token, because the
auto-layout table shrinks the Meaning column to ~70px). Evidence requirements cap EXCEEDED at both widths (521 > 450,
1114 > 800). Per brief, work on both panels stopped; no product change.

## Follow-up (coordinator correction)

Fresh producer runs: s601b (`--db assetops_s601b_audit_w1brc --work var/s601b_w1brc` prepare|links|serve --port 18141|drop) and s602b
(`--db assetops_s602b_audit_w1brc --work var/s602b_w1brc` prepare|links|serve --case guardrail --port 18142 (case API 18143)|drop);
Vite 5186, CDP 9526. Outputs in `followup/` (`B-*-synthetic.png`, `B-*-baseline-*-app.png`, `B-probe-results-{hist,evreq}.json`).

**B-evreq-real4-160** (s602b guardrail action-evidence): the four real rows, labels and "Available" chips kept. Variable nodes (7):
the detail text after the chip in rows 1-3; `[data-verification-window-gaps]` / `[data-verification-window-problems]` span in rows 1-2
(this case shows "· no gaps"); and in row 4 the comparability and source `RequirementCell` detail spans. The " · " separator is not
counted. Row 3 has no `[data-verification-target-reasons]` span in this case (target met). Verified 7/7 at 160 chars, 4 rows.
| width | panel h | cap | rows | clipped | doc overflowX | table scroller |
|---|---|---|---|---|---|---|
| 1440 | 458 | 450 EXCEEDED (+8) | 58,59,54,58 | visually hidden caption only | 0 | 1120/1120 |
| 390 | 956 | 800 EXCEEDED | 174,174,108,174 | caption only | 0 | 318/318 |
Baseline 396 / 605. Work on this panel stopped.

**Action history context** (s601b `all`; meaning sentence leaf -> 160 chars; leaves inside code/a/small kept):
| variant | width | rows | panel h | row heights | truncation + toggle | clipped | doc | table scroller |
|---|---|---|---|---|---|---|---|---|
| B-hist-160-default3 | 1440 | 3 | 408 | 74,75,74 | "Showing the latest 3 of 6..." + "Show all 6 entries" | caption + 2 `code.action-ref` (truncated reference codes) | 0 | 1120/1120 |
| B-hist-160-default3 | 390 | 3 | 566 | 110 x3 | present | same | 0 | 576/318 |
| B-hist-160-expanded | 1440 | 6 (real, clicked "Show all 6 entries") | 612 | 54,75,75,75,75,74 | toggle "Show the latest 3" | same | 0 | 1120/1120 |
| B-hist-160-expanded | 390 | 6 | 649 | 54,75,75,75,75,74 | same | same | 0 | 1006/318 |
Q37 measurement unchanged: five 160-char meanings at 390 = 963 (> 800). At 390 the expanded table lays out at 1006px wide (wider than
the viewport, so row heights equal those at 1440) and scrolls sideways inside its scroller. Note: a first expanded run chose the FAILED-stale row's
`<small>` explanation as the "longest leaf". That text does not wrap, so it pushed the table to 1425px. It was discarded and rerun with the sentence leaf.
