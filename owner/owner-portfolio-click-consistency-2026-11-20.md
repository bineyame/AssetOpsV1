# Owner: Portfolio drill-down consistency to the Architect (2026-11-20)

The owner asked:

> also, on the portfolio page, why is 'where the gaps come from' a panel that is diplayed by a click, decision paged, 'by outcome' brought up.

The coordinator read this as: why does clicking a step in "Where the gap comes from" go to a decision page, while clicking a "By outcome" tile opens a panel? The current rule (guide §8): an object with identity (a decision) opens as a page; a heading's detail opens in a side drawer. The coordinator's view that it is still wrong:
1. Inconsistent: two charts on the same page about money by heading behave differently on click.
2. Not every step has a decision ("kWh sold" −$25, "Fuel not explained" −$176, "Authorised adjustments" −$16), so a step-to-decision jump fails or surprises.
3. Navigating away loses the reading context; the drawer pattern exists to avoid that.
4. Overlap: the gap chart already shows Grow −$25 and Optimize −$827, and the outcome tiles restate those two headings in other words; only Protect and Assure add something new.

Proposed (Stripe, Ramp, Linear practice):
- One click behaviour: a gap step or an outcome tile opens the same side drawer for that driver or heading: amount and share of the gap; what is behind it (Findings, certainty); what is being done (the decision with an explicit "Open decision →", or "no decision yet"); the evidence. The user leaves the page only by choice. Queue rows keep their Decide/Review buttons (actions).
- No repetition: "By outcome" becomes a slim strip of Protect and Assure (what the gap chart cannot show), or all four stay with Grow and Optimize linking into the gap chart's groups instead of restating them.

The owner replied, verbatim:

> yes, send it to the architect
