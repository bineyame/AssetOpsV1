# Architect request - W2-05a QA-QD (2026-10-18). Brief rulings; edit `.agent/W2-05a-build-spec.md` in place; amend `D-2026-10-18-w2-05-buildspec`. No code.

From `.agent/W2-05a-phase-handoff.md` (copied from branch task/W2-05a-ev-foundation, commit 1 done):
- QA: Site timezone check accepts only Area/Location names, refusing bare `UTC` named in Q5. Fixture uses `Etc/UTC`, or widen the shared check to accept exactly `UTC`?
- QB: physical/control kind for eight EV properties (implementer's provisional: physical = both power ratings, meter resolution, meter error bound, clock error bound; control = site import limit, both cadences). Confirm or correct each.
- QC: "charger without one feed/meter" refusal vs Q3 (Site with no feed is publishable). Provisional: >1 parent always refused; unfed charger or unfed meter refused only when the Site declares a feed; schedule hours need full feed-meter-charger path. Confirm or correct.
- QD: refuse a second feed on an EV Site (the read returns a single feed)? Rule.
Print a 3-line summary.
