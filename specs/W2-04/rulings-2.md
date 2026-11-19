## Run 9 rulings (D-2026-10-18-w2-04-buildspec, review r1)

These rulings close M2, M4, M5, L1, L2 and confirm M1 in `.agent/W2-04-review-r1.md`. They amend presentation only; the selected evidence, consequence bounds and exact-link gates above still apply.

**M2 — Accepted records height.** Approve the measured 344 px closed panel (limit 345 px) and the existing `line-height: 1.25` on all six column headers and cells. The two-line Record cell is required by D2, and the 370 px result with shared line height misses the agreed panel bound. The exact rule is `line-height: 1.25` on `[data-cold-view="cold-evidence-analysis"] table[aria-labelledby="cold-site-records-heading"] :is(th, td)` inside the existing `@media (min-width: 641px)` block in `frontend/src/sites/w2-cold-site.css`; retain `padding-top: 6px` and `padding-bottom: 6px` on the same scope. Do not apply this line height to the disclosure, other tables or the 390 px layout. The header and single-line cells share the row height, so narrowing the rule to Record cells would not reproduce the measured 344 px bound. Preserve font size, content, wrapping and accessible Record ID.

**M4 — Financials null Finding link.** In the `Source` cell of `cold-financials` panel 1, when the selected exposure's exact Finding cannot produce a proved destination, render the noninteractive string `No linked page for this item`. Replace `Finding link not available`; never construct a guessed link. A proved destination keeps the selected Finding title as its link.

**M5 — W2 cold chip tones.** Use these presentation tone tokens for cold assessment/evidence chips only: `cold-green` = `background: #e3f4ed; color: #166b50; border-color: #b5dfcd`; `cold-amber` = `background: #fff1d9; color: #8e580c; border-color: #c9a24a`; `cold-red` = `background: #fcebea; color: #a13838; border-color: #d26565`; `cold-neutral` retains the current `.badge--neutral` background, colour and border tokens. In `w2-cold-site.css`, use selectors `[data-cold-view] .badge.cold-tone--green`, `[data-cold-view] .badge.cold-tone--amber`, and `[data-cold-view] .badge.cold-tone--red`, setting exactly the three properties and values above; the neutral case adds no override. In the W2-03 follow-up, use `.cold-temperature-tone--green.badge` and `.cold-temperature-tone--amber.badge` in `w2-cold-assessment.css` with the same three properties and values; its existing `.cold-result--danger .badge` and `.cold-result--warning .badge` own red/amber backup results. Add the indicated class only to the badge whose selected value maps to that tone. Keep the word visible and do not recolour shared provenance, lifecycle, origin or configuration badges. These are visual states, not new source/claim classifications.

| Chip location and exact visible value | Tone token |
| --- | --- |
| D1 Contact: `Recent` | `cold-green` |
| D1 Contact: `Old`, `Never`, `Mixed`, `Not declared` | `cold-amber` |
| D1 Contact: `Unknown` | `cold-neutral` |
| D1 accepted Quality: `Good` | `cold-green` |
| D1 accepted Quality: `Limited`, `Mixed` | `cold-amber` |
| D1 accepted Quality: `No fact` | `cold-neutral` |
| Evidence capability: `Full`; evidence strip: `Evidence supported` | `cold-green` |
| Evidence capability: `Limited`; evidence strip: `Evidence limited` | `cold-amber` |
| Evidence capability: `Contradictory`; evidence strip: `Evidence contradictory` | `cold-red` |
| Evidence capability: `None`; evidence strip: `Evidence unknown` | `cold-neutral` |
| W2-03 temperature state: `Within policy` | `cold-green` |
| W2-03 temperature state: `Outside policy`, `Readings disagree` | `cold-amber` |
| W2-03 temperature state: `Not assessed` | `cold-neutral` |
| W2-03 backup result: `Started` | `cold-green` |
| W2-03 backup result: `Start failed` | `cold-red` |
| W2-03 backup result: `Results disagree` | `cold-amber` |
| W2-03 backup result: `Not established` | `cold-neutral` |

The existing W2-03 `.cold-result--danger .badge` and `.cold-result--warning .badge` already supply the red and amber result treatment; keep their current CSS rather than layering a second rule. Correct W2-03's other cold result chips and its temperature chip in the **W2-03 follow-up**, not in W2-04. W2-04 implements the D1 Quality/Contact and capability/strip mapping on its own cold Site views. A `Coverage: {known} / {expected} readings` count, `Evidence: {claim_level}` claim-level chip, and other informational chips stay `cold-neutral`; the table above does not imply quality, equipment health or claim confidence from them.

**L1 — Financials quantity copy.** For `consequences[].quantity_bounds.low/high`, the quantity phrase is `{low}–{high} °C-minutes` when both bounds are known, `at least {low} °C-minutes (upper bound unknown)` when only the lower bound is known, and `Exposure amount not established` when the lower bound is null. The panel-1 Exposure cell is `Chamber temperature exposure: {quantity phrase}`. The Product exposure card keeps its ruled `Unpriced` value; its note uses the quantity phrase only in the `UNPRICED` case. The `Quantity bounds` value in Basis details uses the same phrase for every exposure, including `WITHHELD`; the reason and limitation remain separate rows. Never display `degC_min`, `Unknown bound`, or a range separator beside a null bound. The source field for all three placements is the selected consequence's `quantity_bounds`, not W2-03's observed-segment high.

**L2 — non-primary accepted role in closed What.** If a source row has accepted facts for its primary role, keep its Run-8 short `CLOSED_SOURCE[row.label].what` summary. If it has no accepted primary role but exactly one accepted non-primary role, render that role's existing plain display label from the Run-7 role map (for `generator_state`, exactly `Generator state`). If it has two or more accepted non-primary roles, render `Other recorded roles` and enumerate their exact role labels in Source details. If no role has an accepted fact, render `No accepted report for this role`. A configured role or bound source alone cannot select the first three cases; do not show a role label as evidence without an accepted fact.

**M1 — unbound Affects confirmation.** Confirm R1: the closed Affects cell is the Run-8 capability summary even when no source is bound or no fact was accepted. For unbound `transfer_result`, render `Backup`; for unbound `door_event`, render `Temperature · cooling`. Use `CLOSED_SOURCE[row.label].affects` in the unbound branch; `Claim effect not assessed` remains only for a row whose Run-8 summary is exactly that string, including the undeclared inverter/battery row. The What cell remains `No accepted report for this role` for these unbound rows.

**Implementer dry-read.** The six reviewed paths resolve to one change each: keep the existing panel-scoped M2 CSS; replace the one M4 null-link string; map only the specified W2-04 chip values to the four tokens; format the Financials quantity from nullable selected bounds; choose closed What from accepted role counts; and use the fixed capability summary for unbound Affects. W2-03's chip correction has an explicit follow-up owner. No path requires a new data field, claim inference, route or selection rule. At 1440 remeasure the Accepted records panel with disclosures closed; at 390 verify its table remains scrollable. Verify the unbound Transfer switch and Loading / door log rows and the open-upper-bound Financials row in the existing focused UI proof.

**Copy dry-read.** The closed Financials Source fallback is exactly `No linked page for this item`. Exposure and card strings are fixed for both-bounds, lower-only and no-lower cases above. Closed What uses `Generator state` for the cited non-primary example, `Other recorded roles` only for multiple accepted non-primary roles, and `No accepted report for this role` for zero accepted facts. Unbound Affects is `Backup` or `Temperature · cooling` as applicable. Contact, quality, capability and W2-03 result values retain their existing visible words; only their mapped colours change. No raw unit token, null sentinel or unproved Finding link reaches these closed cells.
