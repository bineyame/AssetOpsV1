# post-W6 W4-mini handoff (unit 5 partial)

Branch `task/post-W6-W4-mini` (worktree `AssetOpsV1-review9`). Main 4d51df61 merged (174a2401). Binding:
`.agent/post-W6-W4-rulings.md`, `.agent/post-W6-W4-build-rulings.md` (copied), UI guide. **Stopped mid unit 5**: Claude
Code reaped the background servers/captures for low system memory (3.2 GB free of 16 GB) and said not to restart them
unprompted. Everything was cleaned up (PIDs stopped, DBs dropped). No backend code changed.

## Commits since the merge

| SHA | What |
| --- | --- |
| 1fff014e | Build rulings 1 (R328 crumb note; R328 stays open, backend public-code dependency in register), 3 (neutral `Lens: Opportunity`, D1 R454 + register row), 5 (`miniRefusalScope.test.tsx`: 422 frame only, 401/403/404/503 keep their refusal, 4 screens x 5 statuses), 7 (inclusive end dates: `siteLocalLastDay`/`nextIsoDate`/`siteLocalEndUtc` in `siteTime.ts`; Scenarios `To (EAT, included)`, Work `to (EAT, included)`; month-end + Europe/London clock-change tests); R450 register text updated |
| 0dba1187 | W1-b siteAction test counts the R453 tab-row label separately (full-vitest failure after merge) |
| 4e6d55d1 | Refused frame keeps every v69 panel (service + What unlocks; fuel + interpretation; backup + Operating/Next evidence) - capture finding |
| 021fcf3c | Productive-use evaluation: overflow in focusable labelled `mini-scroll` (390 probe found an unfocusable 11 px body scroll) |
| 98c50573 | Mini Incident table bounded above 760 px (`max-height: 330px`, `[data-work-mini]`), `Scroll the incident table to see every row` hint outside the region; 1440 five-row 160-char stress now 488 <= ruled 500 |

Build ruling 2 (Work 422 copy/cause guard, expired-cursor strip) was already in code from unit 4 (tests exist).
Ruling 4: contrast measured - bars min 3.47:1 fill/track (PV, 1440), chips min 5.3:1; none below. Ruling 6: kept
mini-local refused frame (no lift; cold untouched).

## Checks so far

- Full vitest at 1fff014e: 3336 passed, 5 failed -> 4 fixed (siteAction R453 count), 1 `siteFinancials` S4-08 409 test
  failed only under full-suite load (3/3 isolated passes). Re-run full vitest once at final SHA.
- tsc clean; `npm run build` passes (chunk warning); check-all 11/11 at 1fff014e (re-run at final).
- Single-file revert proofs: MiniPerformance (Lens, frame panels, productive scroll), MiniScenarios, siteWorkCases
  (label; hint+CSS), w4-work-cases.css, frame-scope mutation - each failed the new tests, restored.

## Capture state

See `.agent/post-W6-W4-recapture/README.txt`. Done: batch-12 42 pairs (+probe), batch-13 one (28 pairs) + stocked
(4 pairs) + w403 (2). Q18 results so far (natural peak -> provisional `50*ceil(x*1.15/50)`): performance panels keep
the ruled W4-02 q12-7 caps (closed panel <= cap; overflow in focusable labelled region; 0 clipped; doc 0). Uncapped:
Backup event chains 423/618 -> 500/750; Fuel at a glance 294/310 -> 350/400; Opportunity panels <= 302 -> 250-350;
Financial scenarios (five 160-char rows + gap) 1014/1424 -> 1200/1650; Maintenance probe unverified (asset selector
absent when no asset: use `[data-work-asset], td:nth-child(2) .muted`).

## Resume

1. Re-run `tools/run_b_full.sh` (serial; fresh `w4rc_b_test`; API 9761, Vite 5452, CDP 9451), then walkthrough `drop`.
   Expect the producer's own `capture --phase late` gate to fail on its retired u9c caps (348/391 Scenarios, 460
   Incidents) - log, not a product failure (Q13 retired them; fix-slices rules Incidents 1440 = 500).
2. Phase C: `tools/w502_cold_work_walkthrough.py --work var/w502b_w4rc --tag w4rc prepare --modes positive,worstcase`,
   `serve` (ports 8971/8972 fixed), Vite per API port, targets from `post-W6-audit/batch-15/tools/mk_targets.py`
   (Work tabs only; change B); EV `tools/w504_ev_work_walkthrough.py` with `W504_API_PORT_BASE=18460`, batch-17
   `mk_targets.py`. Include the 390 tab-row pair for cold and EV (default and EV-href rows); mini row from part-b.
3. Full vitest, tsc, build, check-all at final SHA; packet `.agent/post-W6-W4-packet.md`; CODE_STATE; ACTIVE_CONTEXT.
4. Capture gaps to log: populated Alternatives (F02 future-dated; pure selected-row test), five long Work/Scenarios
   rows (DOM probe only), mini 503 (component tests).
