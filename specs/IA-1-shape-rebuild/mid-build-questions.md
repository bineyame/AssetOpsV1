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

Count: **2** (Q3, Q4). Write each question as Q1, Q2 … (the unit, the section of `spec.md` §5.1, what is stopped, what is built,
what you ask). The Architect rules in `rulings-2.md`.

**Q3 (IA-2a unit 2, §5.1.8 `plan_switch_check` row; open).** The spec and D-IA.48/49 name `PSW_PLANT=crewtile|release|leftout`, but
`plan_switch_check.cjs` already reads its plants from `PS_PLANT` (one plant, `resid`, line 349; an unknown value exits 2). **Stopped:** the
three plants and their runner row only. **Built:** the runner row is written as `PSW_PLANT` in `ia_gates.cjs` (uncommitted). **Asked:** add
the three under the existing `PS_PLANT` (and rename the runner row), or add a second variable `PSW_PLANT`? Default if unanswered: `PS_PLANT`,
one variable per check, as every other check has.

**Q4 (IA-2a unit 2, D-IA.52 R16; open).** R16 says "`copy_check.cjs` list extended; plant `COPY_PLANT=plan` adds a stray word". `copy_check`
has no list of allowed strings: it applies regex rules (doubled word, placeholder, …) to `rendered-text.json`, and its only `ALLOW` is two
regexes (line 20). "Every string on the four routes and not on the reviewed pages is in the §5.1.6 list" needs a new comparison (rendered
strings of the four routes minus the reviewed plan page and What changed, against the §5.1.6 list). **Stopped:** that assertion and its plant.
**Asked:** build it as a new block in `copy_check.cjs` (its own jsdom render, independent of `rendered-text.json`), or in
`plan_shape_check.cjs`? Default if unanswered: a new block in `copy_check.cjs`.
