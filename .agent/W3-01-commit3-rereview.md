# W3-01 commit-3 re-review (read via git objects, b59575c0..2b7e18e1, nothing run)

**Verdict: ACCEPT.** No High or Medium finding.

Closed as ruled:
- q13-2: five fixed chips, no row inference; the test covers a filtered empty read.
- q13-3: cold/EV titles are inert and keep the Site link and disclosure. The notice is conditional, and the ledger text for the findings node and the three lens nodes follows.
- q13-7: the Verified note is `NO_VERIFIED_OUTCOME` on a complete response with `verified_in_30_days == 0`; a partial response gets no note. A RESOLVED/REFUTED row still shows the note.
- L1: the Actions Site cell links `siteDetailHref(site_code)`, with `site_code` as secondary text. Mini-grid, cold and EV fixtures carry distinct codes; the cold code includes `/` and a space, which exercises the encoding.
- L2: `cutoffBarText` matches the ruled loading, refusal, page-one, continuation and explicit-cutoff literals. The test rejects `latest (latest at read time)`.
- M1: each listed string has an exact, scoped assertion, including the five refusal copies with no First-page link.
- L3: `FindingsFrame` and `FINDINGS_HEADING_ID` are removed, with no remaining references. L4 is asserted.

Tests are non-vacuous: each uses distinct fixtures and exact `toBe`/`toEqual`.

**Strict reading of mini-grid = `match_state !== "NOT_APPLICABLE"`: sound, no Architect needed.**
- In `estate/coverage.py`, a Finding row exists only for a Site with selected cold/EV windows. `_windowed` sets `match_state` to `NOT_APPLICABLE` on that path (line 239).
- Mini-grid findings coverage uses MISSING, PENDING or COMPLETE.
- A cold/EV Site with no window gets MISSING (the `_empty` default) but has no rows, so it is never misclassified.
- A Site missing from coverage is unlinked, which is the safe direction (fails closed).
- Low, optional: this rests on an implicit backend invariant. If a later change gives cold/EV rows a non-NOT_APPLICABLE `match_state`, titles would link wrongly. A wire `domain` field would be sturdier, but the ruled "no wire change" rule is met without one.

Not verified: I ran no tests, `tsc` or builds (the worktree is read-only for this review). The frontend suite and build were never verified in the sandbox. The implementer's counts are unconfirmed.
