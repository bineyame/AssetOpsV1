# Viewer clicks, agent A (Q43: read/viewer navigation links only, no mutations)
Tool: `probe/tools/viewer.mjs` (finds the link, calls `.click()`, waits for the URL to change, then measures). Raw data and screenshots are in `viewer-clicks/<producer>/viewer-results.json` and `*.png`. SHA 2af5fef6.
Columns: start rows/Interpretation history height -> after each click (rows/height). URLs before and after each click are in the JSON.

| producer | case | w | start | Previous versions | Next versions | Back to newest |
|---|---|---|---|---|---|---|
| s405 | single-price | 1440 | 3r/681 | 1r/375 | 3r/681 | not offered |
| s405 | single-price | 390 | 3r/1068 | 1r/630 | 3r/1068 | not offered |
| s408 owner | default | 1440 | 3r/681 | 3r/681 | 3r/681 | not offered |
| s408 owner | default | 390 | 3r/1045 | 3r/1068 | 3r/1045 | not offered |
| s408 owner | recorded-T1 | 1440 | 3r/681 | 1r/375 | 3r/681 | not offered |
| s408 owner | recorded-T1 | 390 | 3r/1068 | 1r/630 | 3r/1068 | not offered |
| s408 owner | recorded-T3 | 1440 | 3r/681 | 3r/681 | 3r/681 | not offered |
| s408 owner | recorded-T3 | 390 | 3r/1045 | 3r/1068 | 3r/1045 | not offered |
| s408 owner | T3-page2 (cold cursor URL) | 1440 | 2r/470 | 2r/547 | 2r/470 ("Back to newest" link on the cursor-only page) | 2r/547 |
| s408 owner | T3-page2 | 390 | 2r/837 | 2r/861 | 2r/837 | 2r/837 |
| s408 mixed | mixed-withheld | both | 1r/354 (1440), 1r/609 (390) | not offered (single version) | - | - |

Every height after a click is within the cap (<= 800 at 1440, <= 1400 at 390). Overflow X was 0 in every state.
On T3-page2 the start page has no back stack, so it offers "Back to newest" (R200). The sequence logged was Previous versions, then the offered newer link, then "Back to newest" where it was offered again.
