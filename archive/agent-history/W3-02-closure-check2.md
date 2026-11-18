# W3-02 closure check 2 (2026-10-20)

Checked against "Review closure 2" in W3-02-build-spec.md and the W3-01 "Versioned amendment: estate selection token v2".

| Item | Status | Note |
| --- | --- | --- |
| Q4 | CLOSED | Literal role-ID to label table and the four gap-code templates. |
| Q6 | CLOSED | Four-category display dictionary, with sources. |
| Q7 | CLOSED | Ordered, exhaustive eligibility table. W1 UNPRICED, PRICED-but-not-ELIGIBLE and CONFLICT are all mapped. |
| Q19 | OPEN | The order is given and NO_LINES and MIXED_SOURCE are defined. Missing: which partition(s) carry UNKNOWN_COVERAGE, because the uncovered Site has no lines. Also missing: whether a category with zero heads on a covered Site but missing coverage on another gets NO_LINES or UNKNOWN_COVERAGE. |
| Q27 | CLOSED | Inert example slots with literal text and accessible names. Unlocks dictionary and empty copy given. |
| N1 | CLOSED | Commits 0a/0b/0c, seven commits in total. |
| N2 | CLOSED | `estate-selection/2` approved, with four arrays, an old-cursor 409 and fixture recompute. |
| N3 | CLOSED | Hard stop and return to Architect. |
| N4 | CLOSED | `siteEvHref(row.site_code, ...)`, not pre-encoded, with a query rule. |
| N5 | CLOSED | 187px. |

Result: 9 CLOSED, 1 OPEN (Q19).

## New questions
- C1. UNKNOWN_COVERAGE: which group(s) does it attach to, and how does it interact with NO_LINES (see Q19)?
- C2. The W3-01 amendment says to apply token /2 "before the W3-02 Evidence read". Commit 0c is the stated carrier. Confirm the W3-01 endpoints' own tests are in 0c's scope, not left to a W3-01 run.
