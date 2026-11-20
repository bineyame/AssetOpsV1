# IA-1 mid-build questions (RULES §4 item 7)

Reset to 0 for IA-1b and IA-1c after their handshake (spec rev 3, 2026-11-20). IA-1a's count was 0.

A question about something the spec did not fix stops only the affected part. Write it here (Q1, Q2 ...): the unit,
the section, what is stopped, what is built, and what you ask. The Architect rules in `rulings.md`. Record the count
in the packet; a count above zero is a spec-template defect to fix.

Count: **1**.

**Q1 (IA-1b, spec §2.4 and §7; open).** On `#/portfolio` the reviewed Assure drawer (`uxd-<op>-assure`) loses its focus trap:
its last focusable was "Open Scope & coverage" (`portfolio/scope`), which `iaUnlink` now renders as text (IA-2d). The trap in
`loop-ux.js` (the drawer keydown handler) takes the last element with `offsetParent !== null`, which in Chromium includes the
links inside the drawer's closed `<details>`; focus never equals it, so Tab leaves the open drawer (uxi "overview drawer assure"
FAIL; main passes because the link is live there). **Stopped:** the fix only. **Built:** everything else; uxi carries this one
FAIL. **Asked:** may IA-1b correct the trap's filter (skip elements inside a closed `details` other than its `summary`), a change
to a reviewed function that D-IA.22/24/28 do not list? Or does it wait for IA-2d, when the Scope link becomes live again?
