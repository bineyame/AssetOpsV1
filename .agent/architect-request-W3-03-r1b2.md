# Architect request: W3-03 run-1b readings R1–R13 (r1b2)

Read:
- `.agent/W3-03-build-spec.md`, through r1b;
- the "Run 1b resumed" readings R1–R13 in `git show 0dabc0ad:.agent/W3-03-phase-handoff.md`.

Code: `f5407e95`, `3a0d96bc` and `6c4e0449` on `task/W3-03-portfolio-composition`.

Confirm or replace each reading with a literal and a test. Pay particular attention to:
- **R4:** a PENDING line still counts as pending even without the guard.
- **R10:** there is no per-row "origin revision not selected" field, so the page must work it out. Should this be a wire field, and if so give its name and type. If not, give the exact UI predicate.
- **R11:** one extra same-connection provenance query per Site. Is that acceptable against the N+1 rule?

Also cover R1–R3:
- the key check runs before any DB read;
- a malformed cursor gets 422 before a missing key gets 503;
- the line-less guard test uses a fake snapshot.

3b is building in parallel. Say explicitly if any ruling changes 3b or run 2 (the page).

Append the result as "Run-1b reading rulings (r1b2)" to `.agent/W3-03-build-spec.md`. Write nothing else. Do not commit.
