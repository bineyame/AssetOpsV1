# IA-1 mid-build questions (RULES §4 item 7)

Reset to 0 for IA-1b and IA-1c after their handshake (spec rev 3, 2026-11-20). IA-1a's count was 0.

A question about something the spec did not fix stops only the affected part. Write it here (Q1, Q2 ...): the unit,
the section, what is stopped, what is built, and what you ask. The Architect rules in `rulings.md`. Record the count
in the packet; a count above zero is a spec-template defect to fix.

Count: **2** (IA-1b: Q1; IA-1c: Q2).

**Q1 (IA-1b, spec §2.4 and §7; answered: D-IA.31, `rulings-2.md`; IA-1b fixes the trap's filter now).** On `#/portfolio` the reviewed Assure drawer (`uxd-<op>-assure`) loses its focus trap:
its last focusable was "Open Scope & coverage" (`portfolio/scope`), which `iaUnlink` now renders as text (IA-2d). The trap in
`loop-ux.js` (the drawer keydown handler) takes the last element with `offsetParent !== null`, which in Chromium includes the
links inside the drawer's closed `<details>`; focus never equals it, so Tab leaves the open drawer (uxi "overview drawer assure"
FAIL; main passes because the link is live there). **Stopped:** the fix only. **Built:** everything else; uxi carries this one
FAIL. **Asked:** may IA-1b correct the trap's filter (skip elements inside a closed `details` other than its `summary`), a change
to a reviewed function that D-IA.22/24/28 do not list? Or does it wait for IA-2d, when the Scope link becomes live again?

**Q2 (IA-1c, spec §4.2 and D-IA.26; answered: D-IA.38, option (a), `rulings-2.md`).** The decision page's way to its Site is the breadcrumb's Site crumb only ("Open site" is
withdrawn). The reviewed rule in `ux.css` hides `.canvas .breadcrumbs` at width ≤ 600 px and at width ≥ 1024 px with height ≤ 820 px, so at
390 × 844 and 1280 × 720 a decision has no link to its Site (the meta line's Site name is text). G1 is unaffected (measured from the
Portfolio), and the hub routes have the same rule (they have the rail and tabs). **Stopped:** nothing else; the rule is left as reviewed.
**Built:** the crumbs as spec'd, shown at 1440 × 900 and wider. **Asked:** may IA-1c (a) keep the crumbs on `decision/*` at every size
(an IA rule in `ia.css`), or (b) make the meta line's Site name a link (a change to reviewed `uxDecisionSlots`)? Or does it stay until
IA-2's wayfinding pass? Default if unanswered: as built (crumbs hidden where the reviewed rule hides them).

## IA-2a

Reset to 0 after the IA-2a handshake (spec rev 5, 2026-11-21).

Count: **2** (Q3, Q4), both answered by the coordinator 2026-11-21 (naming only); none open. Write each question as Q1, Q2 … (the unit, the section of `spec.md` §5.1, what is stopped, what is built,
what you ask). The Architect rules in `rulings-2.md`.

**Q3 (IA-2a unit 2, §5.1.8 `plan_switch_check` row; answered by the coordinator 2026-11-21, naming only: `PS_PLANT`, the existing name).** The spec and D-IA.48/49 name `PSW_PLANT=crewtile|release|leftout`, but
`plan_switch_check.cjs` already reads its plants from `PS_PLANT` (one plant, `resid`, line 349; an unknown value exits 2). **Stopped:** the
three plants and their runner row only. **Built:** the runner row is written as `PSW_PLANT` in `ia_gates.cjs` (uncommitted). **Asked:** add
the three under the existing `PS_PLANT` (and rename the runner row), or add a second variable `PSW_PLANT`? Default if unanswered: `PS_PLANT`,
one variable per check, as every other check has.

**Q4 (IA-2a unit 2, D-IA.52 R16; answered by the coordinator 2026-11-21, naming only: a new block in `copy_check.cjs`).** R16 says "`copy_check.cjs` list extended; plant `COPY_PLANT=plan` adds a stray word". `copy_check`
has no list of allowed strings: it applies regex rules (doubled word, placeholder, …) to `rendered-text.json`, and its only `ALLOW` is two
regexes (line 20). "Every string on the four routes and not on the reviewed pages is in the §5.1.6 list" needs a new comparison (rendered
strings of the four routes minus the reviewed plan page and What changed, against the §5.1.6 list). **Stopped:** that assertion and its plant.
**Asked:** build it as a new block in `copy_check.cjs` (its own jsdom render, independent of `rendered-text.json`), or in
`plan_shape_check.cjs`? Default if unanswered: a new block in `copy_check.cjs`.

**Numbering (coordinator, 2026-11-21, naming only).** `shape_check` already has items 10 to 13; the spec's "new item 10" (one tab group, distinct document titles) takes the next free number, item 14.

## IA-2b1

Reset to 0 after the IA-2b handshake (spec rev 2, 2026-11-21). Count: **4** (Q1 to Q4), each built on its default; Q1 waits for the
Architect's confirmation at review. Units 1 and 2 recorded them (Q1 and Q2 by the first builder, Q3 and Q4 by the unit 1-2 builder).

**Q1 (unit 3/4, spec §5 aliases, D-IA.78; default built later, Architect confirmation at review).** `resolveScreen` (`loop-core.js`, a
reviewed function) writes `'#/' + iaLiveAlias(id) + the typed query`, which drops an alias's own query (`findings-cost` would land on
`findings` without `heading=optimize`). **Stopped:** nothing. **Default:** `loop-core.js` is not touched; `iaLiveAlias` notes the alias it
last resolved (reset on every call), and `iaScreen` merges that alias's query and replaces the history entry with the canonical address.
**Asked:** does the Architect confirm this seam (the alternative is a change to the reviewed `resolveScreen`)?

**Q2 (unit 1, block D, D-IA.67 4(a) re-scope).** The fixture's Sites use fake keys (`fx01`..), so its group and Site scopes are undefined.
**Default:** block D uses scope `all` only; the scopes are asserted live in block B.

**Q3 (unit 1, block B, spec §4 sorts).** The spec names the Findings sort `site` "Site" and the Actions sort `item` "Plan item" without
their order. **Default (block B's own comparators, which unit 4's defs must match):** Findings by Site name (`localeCompare`), Actions by
the item's position in `planItemsV1(op)` (items not in it last); both stable, ties in store order. Decisions `due` and Actions `due`: by
date, no date last.

**Q4 (unit 1, the B plants and `qty_check` plants, D-IA.73).** The plants need seams the spec does not name. **Default:** `shapeList` and
`iaListModel` are top-level function declarations (a window property the plant can wrap); `IA_LIST_KEEP` is a top-level `let`;
`IA_LIST_DEFS[key].sorts` is an array and `.items` a function; the tiles come from `iaListTiles(def, m, ctx)` holding the exact string
`const n = m.n;` (plant `tile`). `qty_check`'s list plants are DOM plants (as `gap` and `items` are), each exiting 2 when it finds nothing.
