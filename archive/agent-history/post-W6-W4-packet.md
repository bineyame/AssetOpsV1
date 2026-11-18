# Review packet: post-W6 W4-mini (mini depth, mini decisions, Site Work text)

Branch `task/post-W6-W4-mini`, final SHA = head of branch at packet commit (code last changed at `98c50573`; every later commit is evidence or docs).
Card `.agent/post-W6-audit/fix-slices.md:131-149`; rulings `.agent/post-W6-W4-rulings.md`, `.agent/post-W6-W4-build-rulings.md`; preflight `.agent/post-W6-W4-preflight.md`. USER_REVIEW_REQUIRED: fresh independent review gates merge; owner sees it in the post-W6 walkthrough.

## Outcome
D3 fixes R309-R333 (+ R450-R454 register rows) on the mini Performance, Scenarios, Alternatives, Opportunity and Site Work (mini, cold, EV) screens: tones/chips/bars, confidence, recurrence wording (Q19), refused-window frame that keeps every v69 panel, refusal copy by exact code (Q4), Scenarios rows + inclusive Site-local Window, Site time, plain Work refusals, count cause, long-text handling, Site tab row wrap (R453), mini Incident table bounded above 760 px with labelled scroll region. Build rulings 1-7 applied (summary in `.agent/post-W6-W4-handoff.md`).

## Files materially changed
`frontend/src/sites/Mini*.tsx`, `sites/w4-mini-performance.css`, `w4-work-cases.css`, `siteWorkCases`, `lib/siteTime.ts`, `shell/*` (tab row), tests `miniRefusalScope.test.tsx`, `miniDecisions`, `siteAction` count fix; no backend change. Evidence `.agent/post-W6-W4-recapture/`.

## Acceptance (card, criterion by criterion)
- Tones/bars/chips per mock: done; contrast measured, min bar 3.47:1, chips 5.3:1 (ruling 4), none below.
- Refusal copy by exact code, no raw codes, 422 frame scoped (401/403/404/503 keep their refusal): done, `miniRefusalScope.test.tsx` 4 screens x 5 statuses.
- Scenarios Window inclusive EAT end, month-end and Europe/London clock-change tests: done.
- Neutral `Lens: Opportunity` (D1 R454 + register row): done. R328 crumb note done; R328 stays open (backend public-code dependency).
- Site Work text (R320-R324), long text, hint outside the scroll region: done.
- Recapture of all card screens at 1440/390: see Checks. Q18 caps: provisional, below.

## Checks (final head, run alone, one heavy job at a time)
- Full vitest: 136 files, 3344 tests passed (5m43s, log `recapture/logs/vitest-full.log`). tsc clean. `npm run build` passes (chunk warning only). `tools/check-all.ps1 -Python <main venv>`: 11/11 guards.
- Revert proofs (unit 4/5, committed first): MiniPerformance (Lens, frame panels, productive scroll), MiniScenarios, siteWorkCases (label; hint+CSS), w4-work-cases.css, frame-scope mutation: each failed the new tests, restored.
- Captures (`recapture/README.txt`; rev noted per part):
  - batch-12 main 20 targets x 1440/390: 240/240 (rev 021fcf3c); Q18 probe `probe/part-a`.
  - batch-13 one 168/168; w403 12/12; stocked 24/24; late 130/132; production `w403 capture` positive 98 checks passed. All at the final code.
  - cold Work (w502, unmodified): positive 192/192, worstcase 48/48 (Work tabs only; 390 tab rows included).
  - EV Work (w504, unmodified, port base 18460): positive 144/144. EV worstcase mode is refused by the producer ("W does not list the five incidents"); not capturable.
  - Tab rows at 390 are measured in every pair (`app.tabRows`): default row `Actions (n) / Incidents (n)* / Maintenance (n)` for cold and EV.
- Late phase log entry (not a product fault): producer `w403 capture --phase late` FAILED 7/459, all retired u9c caps (Scenarios 348/391, Incidents 460) and "Scenarios table inner vertical scroll box" (client height == scroll height; only horizontal overflow). Q13 retired those caps; Scenarios 381/473 and Incidents 479/505 are inside the provisional caps below.
- The 2 late-pair failures are `opportunity-finding-refused-bad-known-at` "same panel count": the app shows the exact-copy refusal "Choose a valid evidence cutoff." with no panels by design (R313 Q4); the mock claim is inapplicable.

## Provisional caps (Q18; guide formula `50*ceil(natural*1.15/50)`, natural peak at 1440/390)
| Panel | natural | provisional cap |
| --- | --- | --- |
| Backup event chains | 423 / 618 | 500 / 750 |
| Fuel at a glance | 294 / 310 | 350 / 400 |
| Opportunity panels | <= 302 | 250-350 per panel |
| Financial scenarios (5 x 160-char rows + gap) | 1014 / 1424 | 1200 / 1650 |
| Incidents at this site (5 long rows, above 760 px) | 488 | ruled 500, inner scroll region |
| Maintenance at this site (5 long rows, probe) | 832-865 / 1123-1205 | 1000 / 1400 (not in a card; for the Architect) |
Performance panels keep ruled W4-02 q12-7 caps (closed panel within cap; overflow only inside focusable labelled regions; 0 clipped; doc overflow 0).

## Choices made
- Mini-local refused frame, no lift to shared UI (ruling 6; cold untouched).
- Productive-use evaluation: overflow in a focusable labelled `mini-scroll` (the 390 probe found an unfocusable 11 px body scroll).
- Incident table `max-height: 330px` (`[data-work-mini]`) plus hint "Scroll the incident table to see every row" outside the region.
- Opportunity bad-known-at keeps its panel-free refusal (see above).

## Capture gaps
- Populated Alternatives: F02 is future-dated in the producer, so stocked/empty-current are unproved by the producer; pure selected-row component test only.
- Five long Work/Scenarios rows: DOM probe with synthetic text, labelled "SYNTHETIC LAYOUT EVIDENCE, NOT PRODUCT DATA".
- Mini 503: component tests only (the producer cannot make the gate fail).
- EV worstcase mode refused by producer; cold pending/stale/unknown/forbidden/unavailable cold-Work phases were not recaptured (card names positive and worstcase only).

## Known deviations
None against the card. R328 remains open (register). One full-suite-only flake earlier (`siteFinancials` S4-08 409; passed 3/3 isolated, passed in the final full run).

## Residual risk
Caps above are provisional until the Architect confirms. The late producer gate still carries retired caps (producer unchanged by order). Process note: an overlapping launch ran three `run_b_full.sh` instances once; all killed, evidence restored from git and rerun single.

## Review focus
Mini frame panels vs v69 at both widths, Incident table scroll region/hint, Scenarios Window inclusive end, copy-by-code table, provisional caps table.
