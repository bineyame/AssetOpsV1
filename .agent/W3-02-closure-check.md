# W3-02 spec closure check (2026-10-20)

Worktree `AssetOpsV1-plan2`, main `7aa54277`. Read-only check of `.agent/W3-02-build-spec.md` "Review closure (2026-10-20)" (lines 143-223) against `.agent/W3-02-spec-review.md` (48 items), `.agent/W3-02-mock-measurements.md` and `tasks/W3-02-estate-evidence-money-basis.md`.

**Result: 43 CLOSED, 5 OPEN** (Q4, Q6, Q7, Q19, Q27).

## Checks on the closure as a whole

- **Measured heights: used.** Maxima are mock + max(24px,10%) rounded up, and match the measurements. 1440/390: cards 137/291, capability 314/468, gaps 316/703, status 68/95, register 293/448, notices 66/102. The old 460 gaps cap is explicitly dropped. One arithmetic slip: Aggregation at 390 is 163+24 = 187, the spec says 188 (harmless, but fix it). The 390 cards are 2+1 grid as measured.
- **Every mock slot kept: yes.** Three cards (neutral tone, "Not assessed" copy), both panels with all columns, both notices, status bar, Aggregation prose with chips, the exact subtitles under titles and the inert CTA slots are all retained. Honest-gap copy replaces numbers; nothing is trimmed. Exception: the Unlocks column and the mock CTA text are not fully pinned (see Q27).
- **Seam spot-checks against merged code: no contradiction found.** Verified: cold `CAP_ROWS` (`coldSiteViews.tsx:108-113`, four rows as cited); EV `CAP_ROWS` (`EvSiteViews.tsx:86-91`, four rows as cited); `EvSiteReads` (`ev_site_reads.py:221`) and `NEXT_EVIDENCE` / `codes[:3]` (`:61,:658`); `MINOR_UNITS` (`consequence_read.py:44`); `screen_sentences` (`cold_consequence.py:88`); `COLD_ROLES_1` (`cold_site_reads.py:32,51`); EV half-even rounding (`EvSiteViews.tsx:153-162`); EV link helper `siteEvHref` with `/ev/evidence`, `/ev/financials` (`operatorSiteRoutes.ts:206-223`, `evSiteRoutes.tsx:17-19`); `money_eligibility.for_finding` is open-cutoff, so the new `for_finding_on` is genuinely new. `estate/` does not exist, so W3-01 seams stay unverifiable, and the closure states this as a precondition. `GENERATOR_SUPPORT` is not a backend capability key today, and the closure correctly makes it a single W1 display key.

## Per-item status

| Q | Status | Note |
| --- | --- | --- |
| 1 | CLOSED | `select_*_on` connection-taking helpers, `<= known_at` on every table, HISTORICAL rule, `HISTORICAL_SELECTION_UNAVAILABLE`. |
| 2 | CLOSED | One S3 revision per UTC day, row key `GENERATOR_SUPPORT@date`. |
| 3 | CLOSED | Single W1 key, COMPLETE/LIMITED/NONE mapping, other states to UNKNOWN. |
| 4 | OPEN | W1 gap labels use `{role label}` but only cold's `COLD_ROLES_1` label source is named; the W1 role label dictionary is not stated. |
| 5 | CLOSED | Value fingerprint replaces revision-ID equality; real two-EV fixture required, with a defined fallback. |
| 6 | OPEN | Column mapping is complete, but display words for the Category column are given only for `Recorded repair`. The W1 candidate-operating-cost and EV gross-tariff category labels are missing. |
| 7 | OPEN | W1 `UNPRICED` and `PRICED`+CURRENT but not ELIGIBLE or gate false are unmapped. Nothing maps to `CONFLICT`, though `withheld_line_count` counts it. |
| 8 | CLOSED | `$pgReaders`, three guard self-tests, domain module driver-free. |
| 9 | CLOSED | Commit 0 is Lane A; Lane B touches only new `estate/` files. |
| 10 | CLOSED | Literal per-domain link templates; `Opens current Site view` for mini-grid only. |
| 11 | CLOSED | W3-01 table adopted, literal bodies for all codes. |
| 12 | CLOSED | 403/404 deleted; tests deleted. |
| 13 | CLOSED | Unsigned W3-01 fence, 422 vs 409 split, limit not embedded. |
| 14 | CLOSED | Key list, version, per-domain ID arrays, empty-scope digest given. |
| 15 | CLOSED | Reuse `site_coverage`; domain wire values and display words given. |
| 16 | CLOSED | Placeholder counts, `NOT_APPLICABLE`, CONTRADICTORY handling fixed. |
| 17 | CLOSED | Enums and precedence given. |
| 18 | CLOSED | Gap rows deleted; one row per selected head. |
| 19 | OPEN | Group state precedence is partly given. Missing: precedence among INELIGIBLE / UNKNOWN_COVERAGE / OVERLAPPING_BASIS when several apply, what triggers `NO_LINES` (a partition cannot be empty), and the producer of `MIXED_SOURCE`. |
| 20 | CLOSED | Grouped Site rows, raw claims in disclosure. |
| 21 | CLOSED | `ceiling_source` enum and sources. |
| 22 | CLOSED | Literal EV and cold/W1 strings (except the W1 role labels counted in Q4). |
| 23 | CLOSED | Selected-ID sets per domain. |
| 24 | CLOSED | Card values, notes and tone. |
| 25 | CLOSED | Site cell format and domain words. |
| 26 | CLOSED | Mock wording and subtitle placement kept. |
| 27 | OPEN | The inert mock CTA strings (`ACT-049, ACT-061`, `Map transfer switch`, ...) are kept "as slots", but it is unstated whether they appear as literal rows beside real data. The gaps table's `Unlocks` column has no source or empty-state copy. |
| 28 | CLOSED | Page-local `estate-tone--*` classes with the full tone map. |
| 29 | CLOSED | Component mapping and notice tones. |
| 30 | CLOSED | Header strings exact; window label format. |
| 31 | CLOSED | Seven days, limit 50, shared date bar. |
| 32 | CLOSED | Per-domain rounding and unknown-currency copy. |
| 33 | CLOSED | Source of Basis/limit text per domain. |
| 34 | CLOSED | UTC format and unit words. |
| 35 | CLOSED | Overlap rule (group, technical ID, citation); cold RECORDED_REPAIR listed separately. |
| 36 | CLOSED | One as-of head; pending shows prior head as PENDING. |
| 37 | CLOSED | 19 backend and 8 frontend named tests; the count matches the list. |
| 38 | CLOSED | Measured rule binds (see above; 188 vs 187). |
| 39 | CLOSED | Fixtures and producer tests named; second currency via two persisted EV tariffs. |
| 40 | CLOSED | Five commits. Commit 0 is still large (see new question N1). |
| 41 | CLOSED | No new panel IDs. |
| 42 | CLOSED | `EvSiteReads` with `ctx`. |
| 43 | CLOSED | One-row example retired. |
| 44 | CLOSED | `domain` in row and `line_key`. |
| 45 | CLOSED | Two counts always null, including on empty scope. |
| 46 | CLOSED | Shared parser rejects unknown/repeated keys. |
| 47 | CLOSED | Empty copy outside the table. |
| 48 | CLOSED | Conditional on W4-01 merge. |

## New questions the closure creates

- N1. Commit 0 bundles five Lane A items (W1 selected-days and consequence helpers, `for_finding_on`, token array change, parser change, guard change) in one builder run. Is it one run, or does it split like Q40 asked of commit 1?
- N2. The closure calls the four extra token arrays "the amended W3-01 schema" but also says a changed W3-01 wire contract returns to Architect. Is the W3-01 compatibility amendment already approved, or does it need an Architect entry?
- N3. The closure bars `COMPARABLE` claims if the real two-EV fixture cannot be built, and returns the issue to Architect. If the commit 3 acceptance needs it, what is the stop rule (block or ship with `SINGLE_LINE`)?
- N4. Link templates use `site_code`, but `siteEvHref(siteId, ...)` takes an id-named parameter. Does it accept the code?
- N5. Aggregation 390 max is 188 in the spec, 187 by the stated rule. Pick one.
