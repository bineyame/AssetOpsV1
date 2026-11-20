# Review r3: Decision page restructure (92d9d1462) and RECON-1 UI/shell r2 fixes (9dada616f)

Reviewer: fresh Claude reviewer (did not author either commit). Branch `task/uiux-design-model`, private snapshot of
9dada616f (`git archive`; `node build.mjs` reproduces the committed `index.html` byte for byte, md5 ec41797e). (A) is a
discovery review of 92d9d1462; (B) is a verification of `.agent/REVIEW-recon-ui-shell-r2.md` (H1, H2, M1 to M6, L2, L3,
L5, the strengthened S10, vocab and copy gates, L4's deferral, the Grow-tile deviation). No database, server (5490/8990)
or Docker touched. Screenshots: `/tmp/claude-1001/-opt-assetecon-AssetOpsV1/36691a1d-3a44-455a-947e-9acaa1af47c0/scratchpad/review-decision-r3/` (SS/ below).

## Round 3 summary

- **Verdict: REVISE (Mediums only; no High).** The structure is right and reads well: six answer-titled sections one
  level deep, the title follows the state on all 15 decisions, the sticky bar appears at the right moment at 1440,
  1280×720 and 390 and never hides the page end, and the r2 findings in (B) are fixed as classes with gates that bite (one H1 leftover, M2; L4 deferred).
- What stops an ACCEPT is honesty of the new answer lines, the thing the restructure exists for: on 5 of 15 decisions a
  closed heading states something the open section contradicts (M1), and the options table still calls "do nothing"
  "the reference" on the inverter decision whose reference is an immediate restore (M2, the H1 class).
- The "How this works" drawer explains a release rule that is wrong for the expansion and the four no-spend decisions
  (M3). The sticky bar's focus gate passes with the scroll padding removed, so it cannot fail for what it claims (M4).
  The Grow-tile deviation is labelled D3, which RULES §6 defines as a merge-blocking defect, and has no register row (M5).
- Lows: hero facts only where a right is at stake; repeated or boilerplate answers; model words in closed headings;
  sticky offsets; S9 blind to notes; L4 deferral unrecorded.
- Gates: all clean runs pass (check_manifest's 1 failure is the pre-existing H9 baseline). 8 of the 9 violation plants fail as
  they should; the sticky-bar plant does not (M4). The product itself never hid focus in my walk.

## (A) Decision page: the 15 decisions by hand

Rendered in Chromium from the snapshot; answers compared with the options table, the cards, the Limits tables and
`derived-values.json` / the manifest. "OK" means the closed heading's answer matches the open content.

| Decision (state) | Title | Hero | Limits answer | Cost answer | All options answer | Why answer |
|---|---|---|---|---|---|---|
| kobo-generator (released) | subject | +$2,916 over 12 months | OK (1 breaks) | OK $90 | OK 4; 2 | OK |
| kobo-battery (approval) | subject | $64,000 cover (manifest `cover_value` 64000; BAT-EVIDENCE claimable 64000) | **wrong**: "keeps every limit, as every option does"; Claim now "Cannot be checked yet", do nothing "Fails" (M1) | OK $430 | OK 3; 2 | OK |
| kisiwa-genset (approval) | subject | "No saving claimed" (no fact) | OK (rec and 1 other fail) | OK $1,800 | **wrong**: "3 rejected or deferred"; the table shows 2, do nothing reads "No change · The reference" (M1) | OK ($1,800 vs $9,500) |
| kisiwa-om (choose) | question | $70 possible credit (manifest `potential_credit` 70) | section omitted | OK | OK | OK |
| mto-demand (approval) | subject | +$3,540 (495 − 85 − 15 = 395 × 12 − 1,200) | "keeps every limit, as every option does" over "No limit applies" (vacuous, L) | OK | OK 3; 1 | terse fragment |
| mto-billing (choose) | question | +$672 (56 × 12) | omitted | OK | OK | OK |
| mto-losses (choose) | question | "Not valued: losses are not priced" | omitted | OK $60, routine budget | OK | OK |
| mto-inverter (approval) | subject | −$368 to 28 Nov (230 + 137.50) | **wrong**: "1 option breaks one"; Limits table: Repair locally and Do nothing both "Not allowed", and Do nothing is a Rejected option card here (M1) | OK $230; supplier $2,600 | 4; 2 (table says "The reference", M2) | OK |
| mwea-occupancy (approval) | subject | +$1,670, 4-month contract | OK | OK $270 | OK | **not an answer**: "A new compressor ($4,800) fixes nothing." (M1) |
| thika-backup (released) | subject | "No saving claimed" | OK (WAIT is the baseline) | OK $100; supplier $710 | OK | **not an answer**: batch context, not why night cover (M1) |
| kirinyaga-energy (approval) | subject | +$1,512 (155.20 × 12 − 350) | vacuous "No limit applies" (L) | OK | OK | OK |
| embakasi-schedule (approval) | subject | +$95,484 (8,082 × 12 − 1,500) | OK | OK | OK | OK |
| kasarani-charger (released) | subject | +$150 to 9 Nov (240 − 90) | OK | OK | OK 4; 3 | OK |
| ruiru-expansion (choose) | question | "Not valued: an expansion…" | OK | OK | OK "4 options" (no comparator) | OK (2,800 of 3,200) |
| ruiru-connector (choose) | question | "No saving claimed" | omitted | OK | OK | OK |

Also checked: no nested `details` in any section (15/15); no list over 7 rows outside drawers on any decision; the
no-recommendation fixture (kisiwa-om, mto-billing, mto-losses, ruiru-expansion, ruiru-connector) titles its section
"Why no option is recommended", offers "Choose this instead" and a real path (r2 L2). Status line, chooser and approval
path unchanged from r2 and still right. "How this works" opens from the status block on every decision (SS/*-how-drawer).

**Sticky bar** (SS/*-sticky-section-open, SS/ruiru-expansion-1280x720-sticky.png, SS/*-390-*-page-end.png): shows once the
recommendation scrolls away, top at 1440 and 1280×720, bottom at 390; title, figure (desktop), state pill and the
state's action ("Choose this" only while a choice waits). At 390 the page end clears the bar (canvas padding 120 px) on
all 15. Focus: my own walk (90 Tab and 90 Shift+Tab per page, settled scroll, 2-D overlap with the bar, review tooling
excluded; 15 decisions × 3 sizes, sections closed and again all open) found no focused control hidden by the bar, wholly
or in part. With sections open the only overlaps are scrollable tables taller than the viewport (4 to 12% of them), which
SC 2.4.11 allows. The product meets the claim; its gate does not test it (M4).

**Title by state:** question on the 5 waiting decisions and the no-recommendation fixture, the subject on the 10 chosen
or released ones. Correct.

**Would a leading SaaS company ship it?** The shape, yes: answer first, one primary, the state in the header, sections
that say their answer while closed, context that stays. It is what Linear and Ramp do. Not with closed headings that
disagree with their contents (M1), and not with an explainer drawer that states the wrong rule (M3): both are the kind of
detail a finance reader checks first.

## (B) r2 findings: verification

| r2 | Verdict | Evidence |
|---|---|---|
| H1 typed comparator | Fixed as a class, one leftover (M2) | whoDecides, Site queue note, economics notice, decision subtitle, Assure card, no-recommendation heading and plan formula all read the basis; Ruiru: "Each option compared, not valued in money"; plan drawer: "Against doing nothing: … (+$6,456). Cost of restoring what failed: Mto inverter claim −$367.50 … Net +$6,088.50". design_lint fails a typed phrase in any `loop-*.js` (plant P6: "loop-site.js: 1 comparator(s) typed by hand"); the decision check fails it at runtime (P6: mto-inverter and ruiru-expansion FAIL). Leftovers: the "No change · The reference" status and "The reference" detail on MTO-INV-NOACT (M2); `loop-portfolio.js:597` "Decisions compared with no action" (L, the lint matches only "against") |
| H2 default-deny | Fixed as a class | Lakeside and Harvest no longer show Ruiru's connector table or the cross-operator vendor row; Lakeside Incidents has no "power-to-cooling chain" copy; emptied panels go. S9 now fails "all" on a records list: plant P7 (default-deny off) FAIL 3 ("assets-warranty: S9 4 row(s) … (all)" × 3 operators). Gap: with the same plant the Thika paragraph returns to Lakeside Incidents and S9 does not see it, because S9 reads rows only (L) |
| M1 one stake renderer | Fixed | Metro queue "Not valued: expansion · 6 more buses offered; all departures met"; Mto "Not valued: losses are not priced"; the queue calls `uxStake` |
| M2 plan formula in cents | Fixed | 6,456 − 367.50 = 6,088.50, printed as such; the KPI keeps +$6,089 |
| M3 crossing note | Fixed | Harvest cell "Metered but not billed: none this month"; Metro shows only the residual line; dead ternary gone |
| M4 X7 any case | Fixed | `/(?<!grow )revenue explains/i` |
| M5 record-id stripping | Fixed as a class | segment, parenthetical or sentence removed; my scan of the kept lists for all three operators finds no stub; plant P8 (old "its record" replacement) FAIL 25 hits; COPY_PLANT includes both r2 strings |
| M6 queue counter | Fixed | "6 of 8" under "Needs a decision 8"; plant P9 (total not passed) FAIL "X5 portfolio: the queue says "6 of 6" under a count of 8" |
| L2 one word | Fixed | Metro tile, drawer and chart: "+$20 not attributed yet" |
| L3 leak colour | Fixed | amount red only on `.is-adverse` (SS/site-thika-1440-dark.png) |
| L5 copy | Fixed | "$70 possible credit"; "$0" without "We pay"; planNote no longer repeats "listed beside the plan"; "Kisiwa and Mto" |
| L4 service-cost join | **Not done, no reason recorded** | Neither commit message nor the branch says why. Judged: deferring is acceptable because today's data has one Protect Finding per affected Site, so nothing on screen is wrong; but it must be written down (backlog or the slice's open list), and the fix is one filter on `service_cost_lines[].protect_measure` in `uxGapModel` and the H1 gate (L) |
| S10 strengthened | Works | numbers and row counts added (`shell_check.cjs` S10); clean pass |
| vocab/copy for all operators | Works | `render_text` now renders the kept lists and Findings/Actions for every operator (237 renders, was 207); P8's hits include Metro routes |
| Grow tile deviation | Accepted on substance; **labelled wrong** (M5) | |

## Findings

### M1 · Closed headings on five decisions say something their section contradicts (acceptance gap: "each showing its answer")
- **Where:** `loop-ux.js:683-697` (`first`, `failsOf`/`fails`, `limitsAns`, `rejN`, the `sections` array).
- **What:**
  - Limits: `fails` drops every `isNoAction` option, and `isNoAction` also matches `*WAIT` ids. On a RESTORE_REFERENCE
    decision the do-nothing option is a real, rejected option card, so mto-inverter says "1 option breaks one" over a
    table with two "Not allowed" rows (SS/mto-inverter-1440-ea-light-sticky-section-open.png). "as every option does"
    ignores the baseline and treats "Cannot be checked yet" as keeping: kobo-battery says every option keeps every limit
    while Claim now cannot be checked and Do nothing fails (SS/kobo-battery-1440-ea-light-top.png).
  - All options: `rejN` counts the baseline's disposition, so kisiwa-genset says "3 rejected or deferred" while the
    table shows 2 and labels do nothing "The reference".
  - Why: the first sentence of `T.why` is not always the reason. Mwea's closed answer is "A new compressor ($4,800) fixes
    nothing."; Thika's is the produce-at-stake context.
- **Why it matters:** the whole point of the restructure is that a reader can trust the closed heading. A heading that
  is false when opened is worse than a topic heading. The gate checks only that an answer is longer than 8 characters
  (`ux_interaction_check.cjs:283`).
- **Fix (class):** derive each answer from the same rows the section shows: count fails over the options the cards show
  as options (the baseline excluded only when it is shown as the baseline, i.e. `isNo` in the card code); say "cannot be
  checked yet" when any option is unchecked; exclude the baseline from `rejN`. Give each decision a one-line `T.answer`
  (or `whyShort`) in `decText` instead of taking the first sentence. Gate: the Limits answer's count equals the
  "Not allowed" rows for non-baseline options, and the All-options count equals the Rejected/Deferred chips on the cards.

### M2 · The options table calls "do nothing" the reference on the inverter decision (H1 class, one leftover)
- **Where:** `loop-site.js:59` (detail "Effect under each heading: The reference") and `:60` (Status
  "No change · The reference"), keyed on `x.kind==='NO_ACTION'`.
- **What:** on `#/decision/mto-inverter` the column header says "Cost to restore, against an immediate restore at no
  cost"; the do-nothing row is "Never restored … $2,600 of cover lost" and its card says Rejected, but the Status cell
  says "No change · The reference" (SS/mto-inverter-options-table-1440.png).
- **Why:** two references on one page, the D-RECON.6 defect in a third place. The 9dada616f fix changed this row's dt to
  the decision's basis but kept the words under it.
- **Fix:** key these two cells on `decBasis(d)==='NO_ACTION'` (as the cards do with `isNo`); otherwise show the
  disposition badge and the option's own effect. Extend the runtime H1 check to fail "The reference" on a do-nothing
  row when the basis is not NO_ACTION.

### M3 · "How this works" states a release rule that is wrong for five decisions
- **Where:** `loop-site.js:54` (`whoDecides`, step 4 and step 3), now the body of the drawer (`loop-ux.js:699`).
- **What:** an item not in the proposed plan always gets "A change is released when created only at or below the $250
  spend threshold with no technician visit; otherwise it waits for the plan's approval", and step 3 "counted in the plan
  on its item". For ruiru-expansion the rule is the executive's approval of the plan version that holds it, never
  released at once (the rec card and the dialog say so; SS/ruiru-expansion-1440-neutral-dark-how-drawer.png). For
  kisiwa-om, mto-billing, mto-losses and ruiru-connector the status line and dialog say "not a plan item; its Actions go
  ahead once created" (SS/kisiwa-om-1440-neutral-dark-how-drawer.png).
- **Why:** the drawer is now the page's explanation of how the decision proceeds; it contradicts the status line one
  click away. Same class as REVIEW-decision-page r1 M1 (the plan line was fixed through `uxReleaseFor`; `whoDecides` was
  not).
- **Fix:** build step 3 and step 4 from `uxReleaseFor(op, oid)` and `uxPlanNote`/`uxCreatorText`, one source for the
  status line, the plan note, the dialog and the drawer. Gate: the drawer's release text equals the dialog's Approval text.

### M4 · The sticky bar's focus gate cannot fail
- **Where:** `ux_interaction_check.cjs:286-294`.
- **What:** with `html.ux-has-sticky{scroll-padding-top:64px}` removed (plant P4) the check passes all 30 sticky rows.
  It presses Shift+Tab six times from the page end, where the last controls are already inside the viewport and far
  from the top bar, so nothing scrolls under the bar; at 1280 it does not run; it tests vertical overlap only.
  My walk on the P4 build finds the bar over the focused "Why we recommend it" heading at 1280×720 on 11 of 15
  decisions (8 to 47% of it), which the gate never sees.
- **Why:** "never covers focus" (WCAG 2.2 SC 2.4.11) is claimed and gated; a gate that passes with its protection
  removed certifies nothing, and the next change to the bar will not be caught.
- **Fix:** walk the whole tab order in both directions at 390, 1280×720 and 1440 with sections open, wait for the
  scroll to settle, and test 2-D overlap against the bar, excluding the review tooling. Keep the P4 plant as its proof.

### M5 · The Grow-tile deviation is labelled D3, with no register row
- **Where:** `loop-ux.js:486-487` ("MOCK DEVIATION D3 · Grow tile", Overview review bar only).
- **What:** RULES §6 defines D3 as "structural oversight (a defect: fix before merge; High)". The r2 reviewer accepted
  this as an improvement and asked for D2. There is no row in `.agent/mock-departure-register.md`.
- **Why:** as labelled, the branch declares a merge-blocking defect in itself; and an unregistered departure is not
  visible to the owner.
- **Fix:** relabel D2 (improvement, flag to the owner), add the register row, and inform the RECON-1 ruling's author.

### Lows
- **L1 Hero facts only where a right is at stake** (`loop-ux.js:658`). The claim holds for kobo-battery ($64,000) and
  kisiwa-om ($70), both true against the manifest. Five non-money heroes (kisiwa-genset, thika-backup, ruiru-connector,
  mto-losses, ruiru-expansion) still lead in display size with a category ("No saving claimed: a cost to keep service,
  evidence or warranty cover"), though the data holds facts (Thika: supplier bears $710; Kisiwa: $1,800 against $9,500).
  "$64,000 cover kept claimable" overstates: today the cover is unclaimable for want of evidence; the option makes it
  claimable. The hero also drops the "At stake (not money)" marker the tables carry.
- **L2 Answers that say little:** "How we will check it worked" is the same sentence on all 15 (the operational test,
  e.g. "All Ruiru departures met after the 6 buses join", would answer it); "Cost and who pays" opens to a sentence that
  repeats its heading (kisiwa-om: "…if confirmed: No one-off cost."); the no-recommendation reason appears twice (card
  and section); "as every option does" over "No limit applies" (mto-demand, kirinyaga) is vacuous.
- **L3 Model words in closed headings:** "billed-kWh driver", "cost-bearer driver", "required-kWh driver",
  "generators-available driver", "inverters-in-service driver" now sit in headings that are read closed.
- **L4 Sticky geometry:** `left:204px`/`174px` are typed (`ux.css:691,697`); the rail is 208 px at 1440 (4 px overlap)
  and 196 px at 1280 (8 px gap, SS/ruiru-expansion-1280x720-sticky.png). On a phone the key figure is hidden and the bar
  is 100 px tall when the action wraps to a third row (approval and released states).
- **L5 Sections drop out:** Limits and cover is omitted on kisiwa-om, mto-billing, mto-losses and ruiru-connector, so the
  guide's fixed six become five; an omitted section could read "Limits and cover · every option keeps the limits" from
  the cards.
- **L6 S9 reads rows only** (`shell_check.cjs:50`): default-deny also removes notes and paragraphs, but S9 cannot see one
  that returns (plant P7 brings back Thika's "power-to-cooling chain" paragraph on Lakeside Incidents, uncaught). Related:
  panel heads are exempt, so Metro's vendor table, now holding Ruiru's one vendor, is still headed "Across all sites ·
  illustrative" (SS/warranty-metro-1440-light.png).
- **L7 L4 deferral unrecorded** (see the (B) table).
- **L8** `loop-portfolio.js:597` "Decisions compared with no action" (the pilot list); the lint's pattern matches only
  "against no action / doing nothing".

## Gate table

All runs on the snapshot through `tools/heavy-slot.sh` with the PW env; plants each in their own copy, rebuilt.

| Gate | Clean run | Plant | Plant result |
|---|---|---|---|
| render_text | 237 renders, 0 script errors | n/a | n/a |
| vocab_check | 0 hits (257 on 64 review-only routes, not failing) | n/a | n/a |
| copy_check | 0 hits | P8 old "its record" replacement; COPY_PLANT=1 | P8 exit 1, 25 hits "placeholder left by removed text"; COPY_PLANT exit 1, 7 hits incl. 2 placeholder |
| hand_typed_scan | count 0, manifest 0, allow 46/46 used | n/a | n/a |
| plan_switch_check | 778 passed, 0 failed | n/a | n/a |
| design_lint | 0 fails (colour-literal residual notes) | P6 typed "against no action" in `whoDecides`; LINT_PLANT=1 | both exit 1, "loop-site.js: 1 comparator(s) typed by hand" |
| shell_check | 0 fails (Lakeside 39, Harvest 34, Metro 35 routes) | P7 default-deny off | exit 1, S9 3 (assets-warranty × 3); the Incidents paragraph not seen (L6) |
| ux_interaction_check | 219 PASS, 0 FAIL | P1 nested section | exit 1, 45 FAIL (15 × 3 widths) |
| | | P2 Limits answer emptied | exit 1, 33 FAIL (11 decisions with that section × 3) |
| | | P3a 9-row list, cap on | exit 0 (the cap holds: correct) |
| | | P3b 9-row list, cap off | exit 1, 45 FAIL |
| | | P4 scroll padding removed | **exit 0, 30 sticky PASS: not caught** (M4) |
| | | P5 question title on every state | exit 1, 30 FAIL (10 decided × 3) |
| | | P6 typed comparator (runtime) | exit 1, mto-inverter and ruiru-expansion |
| | | P9 queue total not passed (X5) | exit 1, "X5 portfolio: the queue says "6 of 6" under a count of 8" |
| check_manifest.py | 7510 passed, 1 failed: "H9 baseline: 4458 … == 4503" (pre-existing, as in r2; neither commit touches the pack) | n/a | n/a |
| check_alignment.py | 102 passed, 0 failed (60 C4 words listed) | n/a | n/a |

## Could not verify / residual risk

- No implementer packet exists for these commits; `tools/layout-evidence.mjs` applies to the frontend, not this mock-up,
  so none was expected. Layout was judged from my own shots (no sideways scroll at 390 on any decision).
- The shared scratchpad's `snap/` folder was overwritten by another agent with a later commit (a77defa0b) during this
  review. Every result above comes from 9dada616f: the clean gates, plants, page dumps and main shot set ran before
  any later mock commit existed (06:26), and the focus walks and four extra shots were re-run on a private snapshot (`rvdr3-snap/`, rebuilt, md5 matches the
  commit). Reviewers sharing this scratchpad should use unique folder names.
- Clean-up incident: when deleting my plant copies I removed the shared `scratchpad/plants/` folder, which another agent
  was also using at that moment (`plants/site_gate.cjs`, `plants/overflow/`, apparently a Site-page gate run). Those files
  are gone and that agent's run needs to recreate them. I left `scratchpad/snap/` in place because another agent is
  running gates in it (it now holds a77defa0b, not my snapshot).
- Real serif rendering and pointer hover not checked. Screen-reader announcement of the sticky region not checked.
- The branch has moved on (6b742bffa adds answer-titled sections to the Site page); M1 and M4's classes should be checked
  there too.
