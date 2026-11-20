# Owner: the Decide page, redesign to the Architect (2026-11-20)

The owner said, verbatim:

> also , i don't understand how 'decide' is supposed to work , i click on it and see a very elaborate text , links, grids and content

The coordinator opened Mto's "Decide" (new daytime demand) at 1440 on `task/uiux-guide` (853013d13) and agreed it fails the guide's own rules:
1. It never asks the user to decide anything. There is no stated question and no "Choose this option" at the top. This decision is already Chosen (by David), yet the queue button says "Decide"; all five queue rows say "Decide" whatever their state.
2. A four-box process grid (AssetOps recommends → who chooses → Actions created → release) explains how the product works, in dense text, where the decision should be.
3. About ten stacked blocks with no hierarchy: recommendation, chosen strip, process grid, "what this decision changes", options table, four collapsibles, reasoning, "what would change it", verification plan, records. The Glance → Decide → Explain → Evidence levels are all on one page.
4. Noise: "Modelled" four times, † three times, "Details" on every row, dotted underlines back on numbers.

What best practice looks like (Ramp approvals, Linear triage, Stripe's review queue):
1. The question in one line ("Connect the cooperative's rice huller?") with who decides, due date and state.
2. The recommendation with one number ("+$3,540 over 12 months against doing nothing · costs $1,200, we pay"), one primary **Choose this** and a secondary **Choose another option**.
3. Two or three option cards side by side with the same three numbers (result, cost, limits pass/fail); do nothing shown as the baseline.
4. "Why we recommend it", collapsed: reasoning, what would change it, drivers, limits, cover, who pays.
5. Evidence in a side drawer.
6. Choosing opens a short confirmation: what happens next, which Actions are created and by whom, whether it needs Amina's approval, recorded under your name.
7. The four-box process becomes a slim status line in the header: Recommended → Chosen → Awaiting approval → Actions.
8. The queue button follows the state: **Decide** when a choice is waiting, **Review** once chosen, **Awaiting approval** when waiting on the executive.

The owner replied, verbatim:

> yes, send it to the architect
