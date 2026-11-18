# Architect rulings: post-W6 final whole-diff review

Authority: `.agent/architect-request-post-W6-final-review.md`, `.agent/post-W6-final-review-findings.md`, the post-W6 rulings, and `frontend/docs/architecture/ui-ux-decision-guide.md`. These are build decisions for one bounded fix round before full recapture and the owner walkthrough. They do not record review or owner acceptance.

1. **M1 — fix now.** The default on mini Site Work Incidents and Maintenance is seven **Site-local calendar days including today**: from local midnight six days before the Site's current date to local midnight tomorrow, converted to UTC instants in the URL and API. The untouched form must show those same seven inclusive dates; Search with no edit must retain the same bounds. Use the Site's configured zone to determine today, not the browser or UTC date; a missing or invalid zone uses UTC and says it is a fallback. Keep explicitly selected bounds exact. Cold and EV Site Work and Actions keep R338's seven UTC days and UTC date fields; global Work keeps W6 Q7. Test EAT near midnight, UTC fallback, and a clock-change zone.

2. **M2 — fix now in the shared Action shell.** Use **“Reload”** as its single recoverable-read button label for cold and EV. Cold mirrors EV's code/status map with its own domain noun: `INVALID_KNOWN_AT` → “Choose a valid evidence cutoff.”; 403 → “You do not have access to this site.”; 503 or an unreached read → “Cold work is unavailable right now. Try again.” with Reload; 409 → “The Action changed while it was being read.” with Reload; other loaded refusal → “The Action could not be read.” without Reload. Keep the existing 404 not-found state, selected valid inputs, and no write on Reload. Cold gets the same labelled **“Technical detail”** disclosure as EV, with status and code outside primary copy. The R349 409 Reload exception remains binding. Limit this round's button-label convergence to the Action shell; app-wide refusal labels belong to the backlog.

3. **M3 — fix now.** Scope the 640 px `152px` first-column `th`, `td`, and `col` rules to the Findings table identified by `col.estate-findings-col`, as the 672 px table rule already is. Do not change Financials, Evidence, Actions, or Portfolio column widths. Check the rendered 390 px Findings and those other estate tables for inner scroll and no document overflow.

4. **L1 — backlog.** Converge refusal live regions on one `role="alert"` per active area across mini, cold, EV, Finding and Financials; loading and empty stay `role="status"`. This predates the final diff and spans multiple surfaces.

5. **L2 — backlog.** Resolve Site Work's `Action {id8}` versus global Work's stored `ACT-…` code in a backend-contract follow-up. W6 Q10 deliberately excluded `work/site_index.py`. Use a stored public code only when resolved; keep the stored ID accessible and never derive or invent an `ACT` code from a UUID.

6. **L3 — fix now.** For both EV Site and estate pinned tariff-withheld reads, use the same plain sentence: **“No stored gross tariff estimate matches the evidence at this cutoff.”** Retain the existing withheld state and cutoff semantics; do not imply a refresh or a cash outcome. Update the focused copy expectations.

7. **L4 — fix now.** Cold Financials > Scenarios must pass the validated selected window and cutoff to its Site tab row, just as its breadcrumb does. An unselected or invalid selection must not be propagated.

8. **L5 — fix now.** `coldTabSearch` must apply the same valid-window gate as the EV tab helper: pass a complete, ordered window of at most 31 days; drop a one-sided, reversed or overlong window from destination tabs. Preserve a valid cutoff independently. The current page may still explain its bad input; tab navigation must reach a readable destination.

9. **L6 — fix now for the named mini surfaces.** A missing or invalid Site zone must show **“UTC (Site time zone unavailable)”** beside mini Scenarios and Work date fields, Finding history time, and mini Evidence Measured, Sent and Received times. Keep `siteZoneLabel`'s short `UTC` for valid UTC zones and internal formatting; add an explicit display label/suffix where the zone is unavailable. Exact stored UTC instants remain available. This does not change cold/EV time conversions.

10. **L7 — backlog.** Consolidate the three window controls and copied refusal/reporting blocks when their owning screens next change. Preserve mini Site-local inclusive dates and cold/EV UTC exclusive bounds; a shared helper must not erase that distinction.

11. **L8 — fix now.** Remove the unreachable Mini Performance 422 “Period cannot be read” branch. Keep its existing reachable invalid-window refusal and one alert.

12. **L9 — fix now.** A correctly ordered EV Action window whose bounds are not UTC instants says **“The selected window start and end must be UTC times.”** Keep the existing one-sided/reversed and over-31-day sentences for those proven causes. Do not issue the misleading order correction for a UTC-format error.

13. **L10 — backlog verification.** R350's replacement not-served test covers the three suffixes removed from the older `it.each`; no restoration of the old test is required in this fix round. Add 403/503 probe coverage with the R350 follow-up already recorded in backlog (i), without changing its ruled non-loaded W1 fallback here.

14. **L11 — fix the keyboard reach now; backlog the duplicate rule.** A horizontally overflowing key/value code must be keyboard reachable with a visible focus indicator and a useful accessible name; keep the full code and scrolling inside its value. Consolidate the two 760 px tab-row gap declarations in a later CSS tidy-up, preserving the current rendered wrap.

## Fix round scope

M1–M3; L3–L6; L8–L9; L11 keyboard reach. Add focused regressions for the changed semantics and capture the affected 1440/390 px surfaces on the final fix SHA before the owner walkthrough. Prefer a shared helper only where it cheaply prevents the observed drift. Do not widen the backend contract for L2 or refactor all window forms for L7.

## Backlog

L1, L2, L7, L10 probe verification, L11 duplicate CSS rule; app-wide Reload/Retry/Try again convergence from M2. Carry these alongside `.ai/MILESTONE_REVIEW_BACKLOG.md` “Post-W6 follow-ups” (a)–(i); this ruling file is the decision record and does not edit that backlog.
