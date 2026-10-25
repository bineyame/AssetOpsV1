# SYNTHETIC LAYOUT EVIDENCE, NOT PRODUCT DATA (agent A, post-W6 W1-b recapture)
Method: W3 closeout ruling 1. `tools/probe.mjs` is the W1-a fix-probe tool copied, with W1-b variants `interp-160x5` and `tradeoffs-160x5` added. `cdp.mjs` sets the mobile flag per width. For each width the tool screenshots the real mounted page unmodified (`*-baseline-*-app.png`), then changes the DOM in the same session only (`*-synthetic.png`) and writes `probe-results.json` (`synthetic: true`). SHA 2af5fef6. No product code was changed.

> The next two sections are SUPERSEDED BY CORRECTION: the coordinator ruled their intended-field lists wrong (fixed vocabulary). See "Corrected fields" at the end.

## [Superseded] Interpretation history (assumptions): cap exceeded, stopped
- Pages: s408 owner `assumptions` default and recorded-T3 (`out-interp-s408/`). Five clones of a real row; Fuel price, Recorded amount and Status set to 160 chars each (15/15 fields). "Show this version" stays closed. verified=true.
- 1440: panel 2429 px (cap 800); rows 430/430/430/430/429; clipped 0; doc overflowX 0; table scroller 1117/1105.
- 390: panel 2572 px (cap 1400); rows 430/430/430/430/429; clipped 0; doc overflowX 0; table scroller 1117/318.
- Unmodified baselines match the capture (681 at 1440, 1045 at 390).
- Observation: the 160-char Status badge does not wrap. It holds the table at about 1117 px, so the Version, Fuel price and Recorded amount columns shrink to narrow strips. That drives the 430 px rows (see `assumptions-default-s408-interp-160x5-1440-synthetic.png`).

## [Superseded] Trade-offs and exclusions (financials): cap exceeded at 390, stopped
- Page: s405 `financials` priced-current, which has the method block (`out-tradeoffs-s405/`). The two real item paragraphs were replaced by five clones, each 160 chars (5/5). "Inspect technical basis" and the "Limits of this figure" method block are kept. verified=true.
- 1440: panel 550 px (no cap; recorded). 390: panel 550 px (cap 450). Rows 59 x5 at both widths; clipped 0; doc overflowX 0; no inner scroller.
- Unmodified baselines: 393 at 1440, 413 at 390.

## Corrected fields (coordinator correction, 2026-10-25), SYNTHETIC
Fresh s408 run (`s408-prepare-corr.log`, 427 s, 0 failed; serve 18131; dropped afterwards). Variants `interp-160-3rows`, `interp-160-5rows`, `tradeoffs-gap160` and `tradeoffs-method160` were added to `tools/probe.mjs`. Output is in `out-corr/` (`probe-results.json`, `*-synthetic.png`). `corr.try1-vite-exited.log` is the first run, abandoned after Vite exited silently; everything was rerun.

### Interpretation history: CAP EXCEEDED, work on this panel stopped
- Intended fields per row: the Fuel price cell (priceText) and the Recorded amount cell (amount span or amountWhy), each set to 160 chars as a single text leaf. The real badges ("Latest at this moment" / "Earlier version") and change lines are kept, and "Show this version" stays closed. verified=true on every run (3 rows 6/6 fields, 5 rows 10/10). Default and T3 gave identical results.
- 3 rows, 1440: panel 729 (cap 800), pass. Rows 150/150/149. Clipped 0, doc overflow 0, no inner scroller.
- 3 rows, 390: panel 1713 (cap 1400), **FAIL**. Rows 430/430/429. Clipped 0, doc overflow 0, table scroller 416/318.
- 5 rows, 1440: panel 1028 (cap 800), **FAIL**. Rows 150 x4, 149. Clipped 0, doc overflow 0.
- 5 rows, 390: panel 2572 (cap 1400), **FAIL**. Rows 430 x4, 429. Clipped 0, doc overflow 0, table scroller 416/318.
- Baselines: 681 / 1045.

### Trade-offs and exclusions: within cap
- Which nodes are variable, from reading `FindingConsequence.tsx` TradeoffsPanel and HowWorkedOut:
  - HowWorkedOut takes no free text from the read. "Limits of this figure" is fixed copy. The only node that depends on the read is the allowance line (`data-consequence-allowance-reviewed`), one of two fixed sentences chosen by `model.parameter_is_reviewed`. The longest real variant is 78 chars; it was set to 160 chars as a conservative stand-in.
  - The gap line (`.v69-gap-line`) appears only on a refused read. Its text is refusalWords(status) plus fixed words; it was set to 160 chars on the s408 notfound page.
  - The two paragraphs and the "never priced" sentence are fixed authored copy and were kept real.
- Gap (s408 notfound): 1440 panel 315; 390 panel 335 (cap 450), pass. Gap line 59 px. Clipped 0, doc overflow 0.
- Method (s408 priced, method block present): 1440 panel 410; 390 panel 446 (cap 450), pass, with 4 px margin. Allowance line 33 / 50 px. Clipped 0, doc overflow 0.
- Baselines: notfound 295 / 315; priced 393 / 413.

## Post-fix (SHA e6af4ff0, Q23 internal-scroll fallback), SYNTHETIC
Fresh s408 run (prepare 0 failed; served on 18131, dropped afterwards). `tools/probe.mjs` now also records `[data-consequence-history-scroll]` region and cue state, plus an "all details opened" pass. Rows were cloned or set inside the region's tbody. Output is in `out-postfix/`. Fields: Fuel price and Recorded amount set to 160 chars (3 rows: 6/6; 5 rows: 10/10). Real badges kept; "Show this version" closed. verified=true on every run.

| variant | w | closed panel | cap | region client/scroll | cue hidden | focusable | rows | clipped | doc ox | table scroller (390) |
|---|---|---|---|---|---|---|---|---|---|---|
| 3 rows | 1440 | 749 | 800 pass | 480/484 | false (shown) | yes (tabIndex 0, role=region "Fuel cost versions") | 150/150/149 | 0 | 0 | - |
| 3 rows | 390 | 1312 | 1400 pass | 900/1324 | false | yes | 430/430/429 | 0 | 0 | 416/318 |
| 5 rows | 1440 | 749 | 800 pass | 480/783 | false | yes | 150 x4, 149 | 0 | 0 | - |
| 5 rows | 390 | 1312 | 1400 pass | 900/2184 | false | yes | 430 x4, 429 | 0 | 0 | 416/318 |

- All disclosures opened (exempt from the cap): panel 1636 at 1440 and 2531 at 390. The region stays 480 / 900 high and scrolls (scrollH 11113-32658). Clipped 0, doc overflow 0. At 390 the table scroller is 437/318. Everything stays reachable through the focusable scroll region.
- Opening every disclosure in the panel also opens those outside the region (Price versions recorded, How this was worked out), which accounts for the growth above the closed height.
