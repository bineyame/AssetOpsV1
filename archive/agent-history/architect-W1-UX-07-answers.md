# Architect ruling - W1-UX-07 full operator rail (2026-10-17)

The owner chose the full v69 menu with unbuilt entries greyed out and labelled "Not available yet". This ruling authorizes that narrow exception to the earlier live-items-only rail rule. It does not authorize placeholder pages, routes, inferred site selection, or new capability claims. The W1-UX-07 implementer changes code and tests; this document is the decision, not an implementation.

## Inventory and destinations

Render the following groups, root labels, and order exactly as `ROOTS` and `rail()` in `frontend/mockups/v69/screens.js`. Use `OPERATIONS`, not the current `OPERATE`. Group labels remain visible even when all their roots are unavailable.

| Group | Root | W1 treatment |
| --- | --- | --- |
| OPERATIONS | Portfolio | Unavailable |
| OPERATIONS | Sites | Live link to `/sites` |
| OPERATIONS | Assets | Unavailable |
| INTELLIGENCE | Findings | Live link to `/findings` |
| WORK | Actions | Unavailable |
| WORK | Incidents | Unavailable |
| WORK | Maintenance | Unavailable |
| WORK | Operational records | Unavailable |
| ASSURANCE | Evidence | Unavailable |
| BUSINESS | Financials | Unavailable |
| ADMIN | Settings | Unavailable |

Only Sites and Findings have cross-site index routes that can own these roots today. A site-scoped Asset, Action, Evidence, Financials, Work, or other screen does not make its root live: the rail cannot choose a site or object silently. Promote another root only in the slice that supplies and reviews a truthful cross-site destination, with the route and tests changed together. The inventory does not itself pass the grammar ownership test for a future live destination.

## Unavailable entry contract

Render each unavailable root as text in a list item, with the same icon slot and label as a live root, but visibly muted with sufficient readable contrast. Show the plain visible status `Not available yet` with each entry; do not rely on color, hover, a tooltip, or an icon to communicate it. The accessible name includes both the root label and that status. A noninteractive element with `aria-disabled="true"` is acceptable if it is announced consistently; do not use a disabled button. It has no `href`, `to`, click handler, route, pointer affordance, or tab stop. Tab and Shift+Tab move among live links and other real controls; Enter and Space on an unavailable row do nothing because the row is not focusable. Keep icons decorative to assistive technology.

No per-item reason is needed in W1. A future short reason may be shown only if it is an exact, evidenced product limitation, in plain words, and does not imply an available route or a temporary runtime outage. The standard status must remain visible. Never attach a `title`-only explanation. This rail treatment is an owner-directed inventory exception, not a general change to the rule that unsupported Site tabs and subtabs are absent.

## Workspace footer and Lab boundary

Use the v69 `WORKSPACE` footer placement for the `Simulator Lab` link only when `simulator_lab.enabled` is true and `/simulator-lab` is registered. It is a workspace utility link, not a seventh operator group or operator root; preserve the existing separation between operator and Lab shells. With the gate off, omit the Lab link and any Lab label or hint. Do not duplicate the current workspace utility link in the same rendered shell. Keep the route and link under the same gate and verify both gate states.

Omit `Demo workspace / 3 sites - illustrative records` for W1. The site count and illustrative status are mock data and cannot be asserted for a persisted tenant. A later footer may show a tenant/workspace label or count only from an authoritative current read, with loading, error, and empty states that do not invent a value.

## Guard, tests, and narrow screen

Amend `tools/checks/navigation-truthfulness.ps1` rather than bypassing it. Keep its parameterless Site route bans, identified Site route proof, legacy Foundation address rule, and Site tab/subtab checks. Those tab rules still reject disabled affordances and labelled-in-place absent capabilities. Add an operator-rail-specific invariant over the actual inventory/rendering contract: exactly the six groups and eleven labels above in order; exactly two live destinations (`Sites` -> `/sites`, `Findings` -> `/findings`); each live target registered in the operator route table and rendering a truthful frame; every other root has no destination or navigation handler. A typo, missing route, accidental `to`/`href`, or an unknown root must fail, not silently pass. Prefer a typed discriminated item model so unavailable entries cannot carry `to`; make the guard fail closed if it can no longer parse or locate the inventory. Do not weaken the old checks to accept disabled Site tabs.

Add component/route tests for order, all six headers, visible and accessible unavailable status, no links or keyboard activation for the nine unavailable roots, and successful navigation from both live roots. Check both Lab gate states, including no dead Lab link with the gate off. Include guard mutation fixtures or equivalent negative tests for an unavailable root accidentally gaining a destination and a live root pointing to a missing route. An unregistered route must never be "validated" by the catch-all `Page not available` frame.

At 390 px, the rail may move above the content as the existing narrow shell does, but all six groups, eleven roots, statuses, and the gated workspace footer remain readable in DOM order without horizontal page overflow. Use a single-column or bounded wrapping layout that keeps each label with its status; do not hide unavailable rows in an inaccessible overflow strip. The primary page content and live links must remain reachable by touch and keyboard. Verify at 390 px in the browser, including the longest label `Operational records`, status wrapping, focus order, and gate-on/off footer. The 1440 px rail preserves v69 grouping and order.

## Relationship to prior decisions

This is a scoped owner-directed amendment to the 2026-09-13 navigation rule and `D-2026-10-02-grammar-ownership-test`: the full root inventory is visible, while only truthful owned cross-site destinations are links. `D-2026-10-16-w1-ux` still gives truthful state and material limits priority over mockup fidelity. The G-01 missing-claim/orphan-scan boundary remains: `Not available yet` here describes a missing cross-site destination, not a claim that a site has no evidence or data. If the orphan scan sees these new literals, exempt only the identified rail status element with a reviewed reason or register its specific placement; do not globally suppress that phrase or weaken detection on product panels. This ruling does not promote W1 panels or record owner acceptance; the combined W1 walkthrough remains the visual checkpoint.
