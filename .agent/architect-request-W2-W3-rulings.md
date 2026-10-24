# Architect request: W2-cold, W2-EV and W3-estate pre-flight rulings (one batch)

You are the AssetOps Architect. Three builders pre-flighted in parallel against main 7554111e, with the shell slice being built first:
- `.agent/post-W6-W2-cold-preflight.md` (Q0–Q15 + per-ID defaults + cap asks)
- `.agent/post-W6-W2-EV-preflight.md` (Q1–Q31)
- `.agent/post-W6-W3-estate-preflight.md` (Q1–Q23)

Read them with `.agent/post-W6-audit/fix-slices.md` (cards, sequencing, rulings, cap docket), `.agent/post-W6-shell-rulings.md` (precedent), the register and lesson 15.

Write three files, `.agent/post-W6-W2-cold-rulings.md`, `.agent/post-W6-W2-EV-rulings.md` and `.agent/post-W6-W3-estate-rulings.md`. Each has one numbered ruling per question: accept the default or state an alternative, with exact files, copy, behaviour, tests and recapture set. First resolve these cross-card conflicts, once, in a short "Cross-card ownership" section at the top of each file (identical text):

1. **EV Site Findings (B9-10, merged into R253).** W2-cold owns the shared frame `SiteFindingsFrame`/`SiteAnalyticsFrames.tsx` and `App.tsx` prop. Decide who builds the EV branch. Both builders defaulted to "the other card".
2. **EV main tabs (R347, now in W5-EV-Work), the EV-aware `operatorSiteTabs.tsx`, and bare `/sites/:id` for EV (`SiteDetailFrame.tsx`, raised by W3 Q2).** W2-EV proposes an optional tab override. Assign one owner, and say whether W2-cold uses the same override for cold tabs (B14-10).
3. **EV copies of the cold defects B7-03/B7-07/B7-08 (R254/R258/R259) in `EvSiteViews.tsx`.** W2-EV proposes to fix them using W2-cold's ruled copy.
4. **One window-refusal copy set for all three cards** (cold R261 with `COLD_*` codes, EV `EV_WINDOW_*`, estate `INVALID_WINDOW` classified client-side), and the refused-state layout (strip, tiles and banner kept). Give the exact sentences.
5. **Shared files.** `SiteAnalyticsFrames.tsx` (shell, W1-a/b, W2-cold, W2-EV, W4), `SiteFoundationFrame.tsx` (shell, W2-EV R265), `FINDING_SECTION_UNAVAILABLE` (R280, cold and EV), `operatorSiteTabs.tsx`. State the serialization order and which card edits which lines.
6. **W3 backend edits (B11-01 `site_home_href`, B11-02 Portfolio cold/EV Finding links with own from/to/known_at, matrix destinations).** The card bars backend estate files without a demonstrated DTO omission. Rule on it.
7. **Caps.** Rule caps once per lesson 15 for: cold-findings (W2-cold asks 550/850), ev-evidence-analysis records, EV Sessions table, EV Finding conclusion, and the W3 panels (Findings across the estate, Managed actions, Consequence register, Objectives). Include the all-open exemption and the fallback.
8. **Time basis** (W2-cold Q11, `eatTime` shared with EV): apply your earlier time-basis ruling concretely.

Then update `fix-slices.md` if any ownership moves, including W5-EV-Work if R347 moves. Do not edit product code. Keep it tight.
