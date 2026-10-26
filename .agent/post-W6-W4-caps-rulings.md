# Architect rulings: post-W6 W4-mini caps (Q18)

Caps below apply to the largest closed state at 1440 / 390 px, in that order. User-opened disclosures may grow beyond a closed cap, but their full content must remain readable and reachable. These rulings do not close owner-visible departures or R328.

1. **Backup event chains.** Ratify 500 / 750 px against the measured natural peaks of 423 / 618 px. Keep every row and value reachable without clipping.

2. **Fuel at a glance.** Ratify 350 / 400 px against the measured natural peaks of 294 / 310 px. Keep the full closed content visible or reachable.

3. **Opportunity panels.** Replace the 250–350 px range with per-panel caps: **Bounded opportunity 250 / 350 px** (natural 216 / 302), **Next decision 350 / 250 px** (267 / 199), and **Consequence basis 350 / 350 px** (267 / 267). These values follow `50 × ceil(peak × 1.15 / 50)` for each panel and viewport; the range is no longer an implementation rule.

4. **Financial scenarios.** Ratify 1200 / 1650 px against the five-row, 160-character natural peaks of 1014 / 1424 px. Do not restore a short inner vertical table cap or hide the second row to meet the panel cap.

5. **Incidents at this site.** Retain the already ruled 500 px closed cap and the labelled, focusable inner scroll region for the five long rows; the recorded natural peak is 488 px. Keep the scroll hint outside that region and all rows reachable by keyboard and touch.

6. **Maintenance at this site.** Ratify **1000 / 1400 px** for the whole named section, although it is not a card. The five-long-row probe measured 832–865 / 1123–1205 px; apply the cap to that section's closed layout and do not force it into a card or conceal rows.

7. **Performance panels.** Retain the existing W4-02 Q12-7 caps for their named panels. The W4-mini closed-state proof passes those caps with no clipped content or document horizontal overflow; overflow remains inside labelled, focusable regions.

8. **Fallback and final recapture.** No panel needs a code change solely to adopt these caps before final full recapture. If a current-state remeasure exceeds its cap, first improve wrapping and column widths, then use supported paging or disclosure, then an obvious labelled, focusable inner scroll region with keyboard and touch access; recapture after each change at 1440 and 390 px. Never truncate a value or omit a row to pass. If these steps cannot preserve all content within the ruled cap, return the fixture and measurements for a new Architect ruling before merge.
