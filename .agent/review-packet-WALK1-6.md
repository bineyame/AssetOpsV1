# WALK1-6 review packet: G2 defect fixes D1-D5

Task: build sheet `AssetOpsV1-plan2/.agent/build-sheet-WALK1.md` **Addendum 9** (D-W1-19..23); context
`AssetOpsV1-polC/.agent/WALK1-G2-report.md`. Branch `task/WALK1-6-g2-fixes` from main `c08f2e287`, worktree
`AssetOpsV1-w1h`. Build commit `88b61ee39`. Frontend only; no backend, no prepare, no add-day, no drop.

## Outcome delivered

| Defect | Change | Files |
|---|---|---|
| D1 (R694, R699) | EV money panel title "Possible cost" → **"Estimated income"** (`v69PanelTitles` `ev:4`; cold keeps "Possible cost"). ESTIMATED value split: `.ev-site-amount` (nowrap) holds only "{cur} {money2(amount)}"; then a wrapping `<p class="v69-metric__note" data-ev-money-caption>` "estimated charging income". Prose line and other states unchanged | `sites/EvSiteViews.tsx`, `test/v69PanelTitles.ts` |
| D2 (R695, R655) | The seven Addendum 9 strings in `MiniOpportunity.tsx`, exactly as tabled. Sweep for any other visible `\bload\b`: none left ("Loading the opportunity.", "Loading the opportunity decision.", "could not be loaded" are not `\bload\b`; `proposed_load_kw` is a wire field) | `sites/MiniOpportunity.tsx` |
| D3 (R696) | `money2` moved to `frontend/src/ui/money.ts` (imported by `EvSiteViews.tsx` and `OutcomeBoard.tsx`); `boardMoneyText` formats each bound with it; equal-bounds test compares formatted bounds | `ui/money.ts`, `sites/OutcomeBoard.tsx` |
| D4 (R697) | Portfolio card dots: `NO_OBJECTIVE` reads **"No target for this outcome"** (title and hidden text; `dotStateWord`); matrix and board chips keep the server word. Assure clause "targets declared at {n} sites**, for any outcome**" (before the ", {k} not checked" part when present) | `estate/PortfolioOutcomes.tsx` |
| D5 (R698) | Strip label **"Opportunity findings"** (singular "opportunity finding" for a count of exactly 1); suffix **" · {k} site with an open opportunity on its board"** ("sites" for k > 1) when a Site's Grow row has state OPPORTUNITY or non-null `short_value`. Zero/withheld texts as Addendum 1 | `estate/EstatePortfolio.tsx`, `estate/PortfolioOutcomes.tsx` (`openOpportunitySiteCount`, `openOpportunitySuffix`) |

Register: `.agent/mock-departure-register.md` rows R694-R699 added after R693; R655 gains the WALK1-6 strings.
R699 is used for the D1 amount/caption split (the sheet reserved R694-R699 without assigning R695/R696/R699;
mapping chosen D1 title R694, D2 R695, D3 R696, D4 R697, D5 R698, D1 split R699).

## Acceptance (Addendum 9)

- D1: vitest `evSiteMoneyRoutes` pins `[data-ev-money]` = "KES 8.33" and caption "estimated charging income" under
  "Estimated income"; 390 capture no overflow. **Met.**
- D2: vitest `walk1_6_d2_opportunity_page_never_says_load` scans two page states (non-empty text) for `\bload\b`;
  existing card/basis/claim tests updated to the new strings. **Met.**
- D3: `outcomeBoard.test` "4.50000" → "4.50 USD", "42.075" → "42.08 USD" (half even), "8.325" → "8.32 USD", range
  "12.40 to 18.76 USD", no currency "3.00", null bound → null. **Met.**
- D4: vitest `walk1_6_d4_card_dots_say_no_target_for_this_outcome`, `outcomeCardDots…` adjusted, Assure clause cases
  updated. **Met.**
- D5: vitest `walk1_6_d5_strip_names_open_board_opportunities` (1 site, 2 sites via `short_value` only, none). **Met.**

## Strict capture gate (G2 build, read only)

Serve from polC (`tools/demo_combined.py --db assetops_polish_full_test --work var/polish_full serve`, polC
PYTHONPATH; `ready:` HTTP 200 in 14 s); Vite from `AssetOpsV1-w1h/frontend`, `ASSETOPS_API_PORT=8990`, port 5490.
`DEMOB_STRICT=1 DEMOB_ONLY=ev-board-fault,kobo-opportunity,portfolio-week,kobo-board-S-minus-1,kobo-board-S,kobo-board-S1
node tools/demo-combined-evidence.mjs capture <polC>/var/polish_full <scratch>/w16-cap` → **exit 0, 12/12 OK, settled,
overflow=false, 0 counted hits (strict)** at 1440 and 390 for all six keys (ev-board-fault 390 page height 3465, no
width overflow; it failed at 415 px in G2). Serve tree PID 6960 and Vite tree PID 17164 stopped with
`taskkill /T /F`; ports 8990 and 5490 free afterwards.

Key captured texts:
- **D5 strip:** "Opportunity findings: None found on the days checked · 1 site with an open opportunity on its board" (1440 and 390).
- **Portfolio Grow:** "4.50 USD estimated"; detail "Depot Charging Hub 4.50 USD · each site's latest assessed period".
- **Assure detail:** "1 verified result · targets declared at 3 sites, for any outcome · evidence gap at 1 site · 3 of 7 days checked at Kobo mini-grid"; Kobo dot ": No target for this outcome" (matrix cell keeps "No objective declared").
- **EV panel (390):** heading "Estimated income", value "USD 4.50", caption "estimated charging income".
- **Kobo opportunity:** "Proposed new use · No new use proposed", "No what-if for a new use", "…before deciding on a new use."
- Kobo board S-1 headline "42.08 USD estimated productive-use sales".

## Checks

- `npx tsc --noEmit`: clean.
- Targeted vitest (4 changed files): 159/159 after the dot-test fix; `estatePortfolio.test.tsx` 54/54.
- Full frontend vitest (`88b61ee39`, 455 s): 3618 passed, 2 failed — `generatorLifecycle.test.tsx` ("store read has
  not settled") and `evDepth.test.tsx` R347 (tab href without window). Neither file is touched by this slice; both
  pass alone (29/29), so these are load-timing flakes in the full run.
- `tools/check-all.ps1`: **All 12 guards passed** (needed a `.venv` junction to the plan2 venv in the worktree; the
  first run failed only on "no Python interpreter").
- Production build: not run (tsc clean; no build config touched).

## Known deviations

- Count of exactly 1 reads "1 opportunity finding" (singular); the sheet names only the label "Opportunity findings".
- Suffix keeps the sheet's literal "on its board" also for k > 1.

## Residual risk / user-review focus

- The EV caption uses `v69-metric__note` (10 px secondary); check it reads well under the 27 px amount.
- USER_REVIEW: owner-away; held for the combined walkthrough per the standing rule. Reviewer gate applies.
