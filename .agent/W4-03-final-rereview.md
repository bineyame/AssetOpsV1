# W4-03 final fix round re-review

Branch `task/W4-03-fix-final`, head `7f42661e` (code 38552dbf, harness f545fbec). Base = `f06e9bab` (merge-base with `task/W4-03-mini-decisions-work`). Reviewer: fresh Claude reviewer, did not author.

## Verdict: ACCEPT

## Checked against uF (ad3d94d4)
- M1 (uF 1): same-Finding future revision/root returns 409 `DECISION_BASIS_CHANGED`; unknown/foreign/non-dispatch stays 404; applied in `alternatives.py`, vectors in the Postgres alternative test; capture asserts 409 after Site and Finding reads, exact copy, no not-found copy. Criterion 2 re-worded in the packet.
- M5 (uF 2): replay adds SCENARIO link via the authenticated POST with a distinct key, reads contexts at the W4-01 `known_at`, asserts `label` and `url:null`; capture asserts literal, zero links/focus targets, OPPORTUNITY then SCENARIO, 1440/390.
- M6 (uF 3): Site tabs removed only when `view === "alternatives"`; test asserts present on History, absent on Alternatives; capture check both widths.
- L8 (uF 8): key labels and plain UTC cutoff, `<time datetime>` keeps the token; API untouched.
- L10 (uF 6): FAILED retained for unchanged input on scan only (explicit reconcile unchanged); delayed PENDING counts via `created_at <= known`; tests for unchanged FAILED, changed input, delayed PENDING.
- L11 (uF 5): single retry then 503 `DECISION_STORE_UNAVAILABLE` (final flag, all four services); scenario correction race 503; empty DTO and predecessor 422/409 tests.
- L12 (uF 7): packet table maps every finding to commit and proof; PR-1 heading and readings corrections made.
- Others (M2, M3 1-2000 in 0030 and parsers, M4, M7, L1-L7, L9, H1-H3) match uF 4 and 8. No scope creep seen in the 29-file diff; migration change limited to the two CHECKs and the docstring count.

## Harness changes
a. 20px to 19px: v69 `index.html` `.big-claim{font-size:19px}` and `primitives.css` `.v69-big-claim` 19px. Correct; the check is now `>=19` and larger than prose (19 vs 14 observed). Supported.
b. `opportunity-supported-historical`: real producer. The positive-phase run is cut off at `known_at = capture start - 1s` (explicit past cutoff, after the selected revision was created, before late evidence). The check asserts the wire body is SUPPORTED/HISTORICAL, blue chip computed background, and the intercepted GET carries the cutoff; non-vacuity check requires green, amber and blue tones all measured. Not a fixture fabrication.

## Checks run
- `npm.cmd test -- miniDecisions.test.tsx`: 27/27 passed (ran here).
- Not run: backend suite, tsc, guards, build, DB creation (per dispatch); packet's counts (frontend 2465, tsc 0, build 0, 11 guards, backend focused 25 + 32 passed) are cited, not verified. Full real-Postgres suite is still pending with the coordinator.
- `var/w403s/capture/evidence.json`: 459 checks, 0 failing; unproved = `alternatives-stocked`, `alternatives-empty-current` (both allowed by uF 1).
- Viewed `opportunity-supported-current-1440-app.png` and `-390-app.png`: green chip, large Bounded claim, `Open site` action, panels in mock order, inline crumb with no leading separator at 390 (wraps at word boundary), no horizontal overflow.

## Findings
- Low (preference): L8 plain labels ("Stop at battery charge", "Proposed load", "Duration", "Tariff") are implementer wording; uF specifies plain language but not strings. Acceptable; ratify in the plain-language pass.
- Low: at 1440 the Opportunity breadcrumb reads "Global Findings unavailable; ..." in the crumb; unchanged from earlier rulings, not a regression.

No High or Medium findings. Residual: backend full-suite proof outstanding; the two Alternatives states unproved as noted.
