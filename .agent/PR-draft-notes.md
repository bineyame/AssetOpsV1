# Price it: draft for owner approval (2026-11-11)

Draft: `frontend/mockups/v71/price-it.html` (open it in a browser; "Show change notes" explains each change).
Spec: `.agent/architect-answer-price-it-2026-11-10.md` §3, §4.1, §4.2, §5, §7; card PR-1 + PR-2a (sequence rev 4).

## What you are approving

1. **Part A, where "Price it" appears.** Every unpriced item gets one link under its "what it needs" line:
   - early warnings (Portfolio and boards), money lines reading "Price not established", Finding "Cost exposure: Not available" tiles, and verification "No sales estimate";
   - "Set a {price} for {Site} →" when one price fixes it; "What is needed to price this →" when it needs a model, data or an integration. The server writes the words.
2. **Part B, the Site price page** (Site > Financials > Prices). Read-only:
   - a "Back to …" bar that returns you to where you were, with the date range kept;
   - the line "Prices are set by your AssetOps administrator until sign-in is available. Saving a price from this page comes with sign-in." Plain words, not an error, no greyed-out Save;
   - the item you came to price: what is measured, which price it needs (unit, basis, applies-from), what it shows today, and a receipt of how the figure will be worked out ("3 visits × cost per visit (not set) = not priced");
   - every price the Site can use, set or "Not set", with basis, applies from, who set it, what uses it, and a History disclosure per price.
3. **Part C, model items.** The server's "what is needed" text for battery wear, peak, bus roster or fault history. Measurements stay; no amount, range or "≈".
4. **Not in this step:** the form, preview and Save; roles; "Updating…" and "Restated on" notes. These come with sign-in (PR-3, PR-4). The "Tell your AssetOps contact" button (PR-5) is also out.

## Open choices (with recommendation)

1. **Page address.** The card says `/sites/:id/prices`; the spec says `/sites/:code/financials/prices`. **Recommend the spec's**, under the Financials tab, so the Site tabs show where you are. PR-1 builds it this way; the address is one server constant, so a change is one line.
2. **Rename "Assumptions" to "Prices".** The Financials > Assumptions subtab already shows the diesel price and its versions for some Sites. **Recommend: PR-2a turns it into "Prices"** (one page, not two), and the old address forwards to it.
3. **Keys that are not stored yet** (cost per visit, planned service cost, repair cost, cost per interrupted session, stock value at risk). They are added by PR-3 (out). **Recommend: list them as "Not set"** now, so the link from a warning lands on its row. The alternative is to show only the 3 stored prices, and the "cost per visit" link would then land on a page without that row.
4. **Half-simple warnings** (plan overdue or due soon, charger fault). **Recommend "Set a repair cost →"** (the simple part), with the "fault history" half named on the page. The alternative is "What is needed" only.
5. **Model items before PR-5.** **Recommend:** they open the same price page with the Part C block, and no "Tell your contact" button yet.

## Until PR-2a lands

The PR-1 link opens `/sites/:id/financials/prices`, which says plainly that the price page is not available yet. It keeps the item's "what it needs" words, a link back, and a link to Financials > Assumptions where that exists.
