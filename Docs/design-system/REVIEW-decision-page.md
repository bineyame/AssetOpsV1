# Review: the Decision page redesign (task/uiux-decision-page, d1b5d5ea9)

Reviewer: a fresh, independent Claude reviewer. It did not write the redesign. Snapshot: `git archive d1b5d5ea9` (Docs, tools, .ai) in scratch. `node build.mjs` rebuilt `index.html` byte for byte. The author's worktree was not touched, and no database, server or Docker was used.
Brief: `owner/owner-decision-page-redesign-2026-11-20.md` (8 points). Rules held against: decision-loop §6 (choosing and release), §7 (plan items) and §8 (who chooses, who creates Actions), with design §2.4–§2.6.

## Summary (round 1)

- **Verdict: REVISE.** The layout delivers the owner's 8 points. The gates pass, every planted violation is caught, and the brand packs, dark mode and the 390 px width are clean. But the page's "one number" is wrong for 4 of the 14 decisions.
- **H1.** The recommendation line hard-codes "over 12 months against doing nothing" and drops the figure's real horizon and meaning. On screen, $60,000 of *avoided capital* (Ruiru), a *4-month contract* (Mwea) and two *to-the-restore* values (Mto inverter, Kasarani) are all labelled as 12-month results. The old table under "Why" still states them correctly, so the page contradicts itself.
- **H2.** The Ruiru expansion confirmation says "becomes the plan item … Released at once". The design lists the expansion *beside* the plan and leaves it unvalued (worked-portfolios §Ruiru). It is the executive's capital choice, and §6 never releases a capital item at creation. The capital test misses this option's kind.
- **M1.** For the 4 decisions waiting for a choice, the page says "Not in the proposed plan: choosing it adds it" and "becomes the plan item". §6 makes an option a plan item only if it spends shared budget or crew visits, and all 4 spend $0 with no crew visit. Three dialogs read "valued at No saving claimed over 12 months".
- **M2.** The status line marks "Awaiting approval" as done for the 3 released decisions. All 3 were released when created and never waited for approval.
- **M3.** "Who creates the Actions" in the dialog is generic, and it is wrong for claim and expansion items under §8.
- **Lows:** a dead CSS rule; the "No option recommended" state never occurs in the demo data; a whoPays line in lower case ("30 jun"); a MOCK DEVIATION chip in the product canvas; the question repeats the page title; Confirm does nothing; "in the demo data" wording; a stale guide row; check coverage.
- Rule fidelity holds for the 7 decisions awaiting approval and the 3 released ones: each matches §6 thresholds and capital, and every named person and every Action's creator and owner matches the manifest.

## Gates (run by the reviewer on the snapshot, browser gates inside `tools/heavy-slot.sh`)

| Gate | Result |
|---|---|
| build | `node build.mjs` reproduces `index.html` byte for byte |
| render_text | 205 renders, 0 script errors |
| vocab_check | 205 screens, 0 hits |
| copy_check | 13,107 segments, 0 hits; `COPY_PLANT=1`: 4 hits, exit 1 (as intended) |
| plan_switch_check | 777 passed, 0 failed |
| design_lint | exit 0 (residual colour literals in re-based v7.0 sheets, not failing) |
| ux_interaction_check | 140 PASS, 0 FAIL (matches the author's 140) |
| check_manifest.py | 4,472 passed, 7 failed. All 7 come from the snapshot and none from this diff: (a) "brief readable" because `.agent/` is not in the archive; (b) 5 × A1 owner references to `.agent/owner-*`, which main fixed after this commit (7e53f2ede); (c) the clean fixture, which fails on that same A1. The commit touches no design-pack file or check. The author reported 5 known FAILs. |
| check_alignment.py | 102 passed, 6 failed: the same A1 owner-reference set; 67 C4 words left for the reviewer (unchanged class) |
| screenshots | 135 captured, 0 page errors, `scrollWidth` equals the viewport on every one (no sideways scroll) |

### Planted violations (each in its own scratch copy, rebuilt, full `ux_interaction_check`)

| Plant (loop-ux.js) | Check it targets | Result |
|---|---|---|
| P1 question ends "." not "?" | question first | exit 1, 42 FAIL (14 decisions × 3 widths) |
| P2 "Choose another option" made primary | at most one primary | exit 1, 12 FAIL (the 4 waiting decisions × 3) |
| P3 no step marked current | status line | exit 1, 42 FAIL |
| P4 `whoDecides` grid rendered on the page | process grid not on the page | exit 1, 42 FAIL |
| P5 `is-base` removed from the do-nothing card | one dashed baseline | exit 1, 42 FAIL |
| P6 420 px pushed above the recommendation | recommendation above the 1280 × 720 fold | exit 1, 14 FAIL (every decision at 1280) |
| P7 queue button always "Decide" | button follows the state | exit 1, 3 FAIL (one per operator) |
| P8 "Recorded under" renamed | confirmation content | exit 1, 1 FAIL |
| P9 primary back on row 0 | primary on the first waiting decision | exit 1, 2 FAIL (Lakeside, Metro; Harvest has no waiting decision, so it cannot fail there) |

Every new check fails on its own plant. Coverage gaps are in L8.

## Findings

### H1. The headline number is labelled with the wrong period or meaning (acceptance gap: owner point 2; honesty)
`loop-ux.js:505` writes `${ev} over 12 months against doing nothing` for any money figure and discards `optEffect`'s second part, which carries the figure's horizon and meaning. `:519` adds "Results over 12 months, as above" to every card, and `:490` repeats "valued at … over 12 months" in the dialog. The old table (still under "Why") compared with the new L1:

| Decision | Old table (correct) | New recommendation line |
|---|---|---|
| ruiru-expansion | $60,000 · capital not spent (avoided, not a saving) | $60,000 over 12 months against doing nothing · Modelled (the dialog says the same) |
| mwea-occupancy | +$1,670 · over the 4-month contract | +$1,670 over 12 months |
| mto-inverter | −$367.50 · to the restore on 28 Nov | −$368 over 12 months |
| kasarani-charger | +$150 · to the restore on 9 Nov | +$150 over 12 months |
| mto-billing | +$672 · charges restored over 12 months (billed, not yet collected) | +$672 over 12 months (the "not yet collected" is lost) |

The cards repeat the error under "Results over 12 months": MTO-WELDING "−$8 a month", MTO-INV-BUYNOW −$2,948 (to 12 Nov). On Kirinyaga, the specific dagger "Assumption: recovery share 80%, range 60–90%" becomes the generic "† Design estimate" at L1.
Why it matters: this is the one number an executive reads. Presenting avoided capital as a 12-month result breaks the design's "never a saving" rule, and overstating a 3-night value as a 12-month result is the class of honesty fault the demo must not show.
Fix (the class, not the instances): carry `optEffect(x)[1]` (the horizon or meaning) into the recommendation line, the cards and the dialog. Say "over 12 months" only when that is the figure's basis, and change the cards' shared note to "Results as stated on each card", or state the basis per card when the bases differ. Keep the specific DV text when an option has one. Add a check: for every decision, the L1 qualifier equals the old table's qualifier.

Screens: `dec-metro-choose-ruiru-expansion-1280-neutral-light.png`, `dialog-metro-ruiru-expansion-1440-east-africa-light.png`, `dec-metro-released-kasarani-charger-390-east-africa-light.png`.

### H2. The Ruiru expansion confirmation contradicts the design's capital and plan rules (rule fidelity)
`loop-ux.js:475` treats only `CAPEX` and `DEMAND_CONNECTION` kinds, or `item.capital`, as capital. RUI-ABSORB6 is `CAPACITY_USE`, so its dialog reads "becomes the plan item for this decision … Released at once: $0 is within the $250 spend threshold, with no crew visit".
- worked-portfolios.md:582: "their cost is a service expansion, so they are listed beside the plan, not valued".
- decision-loop §8: the executive chooses only *capital* choices ("expansions, new connections, capital purchases"), and this decision's chooser is OPERATOR_EXECUTIVE.
- decision-loop §6: "a capital item (an expansion …) is never released at creation … its Actions are created after that approval".
- decision-loop §8, "Create an Action": the executive cannot create one, yet the dialog says "the person who owns the item" (Daniel) creates them.

Fix: read capital-ness from the decision (an executive-chosen expansion, or `capital` on the option or item), not from the option's kind. For Ruiru, say what the design says: listed beside the plan, not valued, waiting for the executive's approval of the version that holds it, with the Actions created after that approval by the roles §8 names. If the Architect rules otherwise, record the ruling. Do not let the page invent one.

### M1. "Not in the proposed plan: choosing it adds it" and "becomes the plan item" are wrong for all 4 waiting decisions (rule fidelity; the author's pushback)
`loop-ux.js:511` and `:490`. Under §6, "the chosen option becomes a reactive plan item **if it spends shared budget or crew visits**". KIS-OM-REVIEW, MTO-BILLING, RUI-CONN-CLAIM and RUI-ABSORB6 are each $0 with no crew visit, so choosing one adds nothing to the plan. Their Actions have no plan membership and no release state (§7, "An Action with no plan membership has no release state"). The note also claims "within the plan's budget and crew limits" without checking. In 3 dialogs, "What happens" reads "valued at No saving claimed over 12 months against doing nothing" (kisiwa-om, MTO-METER-AUDIT, ruiru-connector).
Judgement on the pushback (a recommendation outside the plan): explaining it is right, but the explanation must be the design's. "It spends no budget or crew visit, so it is not a plan item; its Actions go ahead once created." Fix as above, and only claim a fit after checking it (planCase).

### M2. The status line says released decisions passed "Awaiting approval" (owner point 7; rule fidelity)
`loop-ux.js:483`: for `released`, every earlier step is marked done. KOB-STOPSOC, THIKA-EPC-STOPGAP and KAS-OEM-STOPGAP are all `release: AT_CREATION` and never waited. Fix: for an item released at creation, mark the step "Released at once (within thresholds)" or skip it, never done. Also: for `none`, the current step is "Recommended" when nothing is recommended.

### M3. The dialog's "who creates the Actions" is generic and partly wrong (§8)
`loop-ux.js:489`: "The Actions are created after the choice by the person who owns the item". Under §8, the finance and commercial lead creates "every notice and claim Action, including one under an item another role chose". So for KIS-OM-REVIEW (credit request) and RUI-CONN-CLAIM (claim), that is Joseph or Lucy, not Halima or Tom. For the expansion, the executive cannot create Actions at all. Fix: name the creator by the §8 rule (the same rule the manifest's Actions already follow: BAT-EVIDENCE and the MTO-INV notice are Joseph's). Drop "in the demo data" from client-facing text.

### Lows
- L1 `ux.css:665`: `@media (max-width:1439px)` comes after the `(max-width:1279px)` rule at `:660` and overrides it below 1280, so `:660` is dead. The `@container` block is also declared twice (`:661-663`, `:666`). Merge them.
- L2 The fourth state ("No option recommended", `loop-ux.js:510`, `uxDecState`) never occurs in the 14 demo decisions (4 waiting, 7 awaiting approval, 3 released), so it is neither seen nor tested. Its wording ("No option fits the limits better than doing nothing") is not what `uxRec` tests: no RECOMMENDED disposition and nothing in the plan. On merit the state is right to have, since §6 lets the chooser choose "none" and a decision can have every option rejected. Add a fixture or a jsdom unit to render it, state the reason from the dispositions, and give the chooser a way to act (it says "can still choose one" but offers no control).
- L3 `loop-ux.js:505`: `whoPays(x).toLowerCase()` gives "we pay: the warranty ended on 30 jun 2026" (Kisiwa genset). Lower-case only the first letter.
- L4 `loop-ux.js:504`: the "MOCK DEVIATION · decision page redesign" chip sits in the product canvas, visible to a client in every pack and width. Wave 2c moved the D2 mark into the review bar for this reason (REVIEW-wave2c L2). Move it there.
- L5 The question repeats the page title in a second, larger line ("Ruiru route expansion: extra buses" / "What should we do about the Ruiru route expansion: extra buses?"), and the generic template reads stiffly with a colon. On merit, the generic wording is acceptable: a question naming the recommended option ("Connect the huller?") would prejudge the choice where several valid options exist, and Ramp and Linear phrase the item as the subject, not the verdict. Better: make the question the H1, or drop the title on this page, so the question really comes first.
- L6 "Confirm the choice" has no handler: the dialog stays open, and the note "Choosing is not wired in this mock-up." is the only signal. That is clear enough to a reviewer and harmless to a client, but a click that does nothing looks broken in a live demo. Close the dialog with a neutral toast ("Not recorded in this demonstration").
- L7 Guide: §7.1 still says **Decide** in the row anatomy (`uiux-guide.md:396`, phone line `:400`, and `:407`), against the new state rule at `:397`. Pre-existing, now on L1: the Mwea compressor card reads "Energy matches the occupancy model (0 more buses.6%)". The `fx()` rule `/\+(\d+)\b/ → '$1 more buses'` (`loop-decisions.js:120`) garbles "+0.6%" for a non-bus operator. copy_check does not catch it; route it as its own fix.
- L8 Check coverage: the dialog check opens only Mto billing (`ux_interaction_check.cjs:242`), and no check compares the approval line with §6 per decision, or the L1 qualifier with the table (see H1). The queue's primary check passes trivially for Harvest, which has no waiting decision.

## Verified by the reviewer
- States: 4 waiting (kisiwa-om, mto-billing, ruiru-expansion, ruiru-connector), 7 awaiting approval, 3 released, matching the claim. Harvest has no waiting decision, so "each state for each operator" is possible only for Lakeside and Metro.
- Approval and released states match §6 for all 10: BAT-EVIDENCE $430, KIS-REPAIR $1,800, MWEA-AGG $270, KIRI-REPAIR $350 and EMB-DEADLINE $1,500 are above $250; MTO-INV-CLAIM uses 1 crew visit, above 0; MTO-HULLER is a new connection (capital). KOB, THIKA and KAS are within both thresholds. The executive is named correctly (Amina, Esther, Daniel).
- Choosers equal the manifest's `chooser` role for all 14, with no CHOOSER_GAPS. The "See the Actions" drawers list each Action with the creator, owner and due date as in `demo_workflow.actions`.
- Queues on Act first: Lakeside Review / Awaiting approval ×3 / Decide (primary on mto-billing only); Harvest Awaiting ×2 / Review (no primary); Metro Review / Awaiting / Decide (primary) / Decide.
- Other numbers on cards equal the table (rounded to whole dollars), except where H1 applies. Kasarani and Thika's "wait" options show "The baseline", where the table shows −$240 or "No saving claimed". That is consistent, because they are the decision's no-action (`isNoAction`, /WAIT/).
- Owner intent, 5-second test: the question, the state pill, one blue "Choose this" and one figure sit above the fold at 1280×720 for all 14. That matches Ramp approvals and Stripe review (one item, one recommended action, the rest one click down) and Linear's state-led triage buttons. The design passes once the one figure is truthful (H1) and the dialog states the rule correctly (H2, M1).

## Not verified
- Real serif rendering (the host falls back to DejaVu). Pointer hover on figures. The fourth state (no data; L2).

Screenshots: `/tmp/claude-1001/-opt-assetecon-AssetOpsV1/36691a1d-3a44-455a-947e-9acaa1af47c0/scratchpad/review-decision/` (135 files, scratch, not committed).
