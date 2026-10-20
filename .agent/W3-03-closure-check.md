# W3-03 spec review closure check (2026-10-20)

Worktree `AssetOpsV1-plan2`, main `5faddeff`. Read-only. Inputs: `W3-03-spec-review.md` (35 questions), "Review closure (2026-10-20)" in `W3-03-build-spec.md` (L161-236), `W3-03-mock-measurements.md`, and the frozen W3-01 (q1-q4, token v2 amendment, refusal table) and W3-02 (closures 1-3) wire.

Result: **31 CLOSED, 4 OPEN** (Q6, Q9, Q24, Q31).

## Per question

| Q | Status | Note |
|---|---|---|
| 1 | CLOSED | `coverage.sites` is the exact seven-key W3-01/02 `site_coverage`. Root states are reductions with a literal enum. "Three roots" is disambiguated from Site domain. |
| 2 | CLOSED | `MINIGRID|COLDCHAIN|EV_CHARGING`, status `CURRENT|HISTORICAL|PENDING|UNKNOWN|EMPTY_SCOPE` and precedence match W3-02 L155. |
| 3 | CLOSED | Cursor is unsigned, `after` tuple, `kind:"portfolio"`, `state_filter:null`, no `limit`, and has 422/409 rules. This matches the W3-02 L161 envelope. |
| 4 | CLOSED | `selected_lines`, `scope_disclosure`, `footer` and card keys are literal. Rounding is by reference to W3-02 L181 (`$a-$b` outward; EV half-even). See N1 for `group_key`. |
| 5 | CLOSED | `Disclosure` is named. Titles, table columns, row sources and prose/notice copy are literal for both drawers. |
| 6 | **OPEN** | The workflow line is derived from `application_state/resolution_state/verification_outcome`, but the row wire (L36) carries only `action_id/action_title/action_state`. Rule the literal row keys (add the three fields, or enumerate `action_state`). |
| 7 | CLOSED | Closed state enum, a literal slot table (value, detail, basis, tone), non-link `div` for a null destination, and `/findings/risks`. See N2. |
| 8 | CLOSED | In-panel `aria-pressed` buttons, `lens=` in the URL, `total_count` span, literal labels. |
| 9 | **OPEN** | The clock (`2026-10-07T00:00:00Z`, window 09-30..10-07) and the four literal assertions are frozen. Missing: the per-variant (a)-(e) literal expectations (`status`, `coverage.*_state`, card states), and how the W1 priced-eligible line is produced. |
| 10 | CLOSED | "Historical" is based on the explicit `known_at` parameter. Links omit `known_at` unless the user supplied it. |
| 11 | CLOSED | `INVALID_LENS` is literal and matches W3-01 L61. Parser keys are exactly `from,to,known_at,lens,limit,cursor`. Repeated/unknown keys map per W3-02 L159. |
| 12 | CLOSED | Test renamed `clearsPrivilegedRowsOn401And503`. The root 403/404 test is removed. |
| 13 | CLOSED | The token literally reuses `estate-selection/2`: 13 keys, one item per Site's physical domain, requested `lens`, `state_filter:null`. This matches the W3-02 amendment (L267). |
| 14 | CLOSED | Only `SUPPORTED|UNCONFIRMED` rows enter the table and `finding_count`, filtered after the canonical selection and before paging. |
| 15 | CLOSED | Stored title/mechanism columns. Anchors are `finding.anchor_start`, `cold_episode.anchor_time` and `ev_session.anchor_time`. Null is reachable only when the projection has no anchor, and sorts last. |
| 16 | CLOSED | The row joins `coverage.sites` by `site_id`. The prefix goes on the Value first line only: `Updating · ` or `Historical · `. |
| 17 | CLOSED | Predicates, windows, applicability, `progress.rows[]` shape, fixed `progress.state` and the three line slots with dot tones are literal. |
| 18 | CLOSED | Site selection, text template, state enum and null-step skipping are literal. See N5. |
| 19 | CLOSED | Enum, labels, `Unassessed` rule, header, inner scroll, historical Evidence rule and the unavailable-destination text are literal. See N5 for `reason` strings. |
| 20 | CLOSED | Badge and sentence are separate and literal, with tones and the domain-summary template. |
| 21 | CLOSED | Slots, neutral chip and arrow, and inert CTA text are literal. |
| 22 | CLOSED | Footer line selection (first eligible EV line), sentence template, warning predicate and rounding are literal. |
| 23 | CLOSED | `Load more Findings` placement, a 564px body maximum, and page-two behaviour are literal. |
| 24 | **OPEN** | The measurements file still holds only the four panels. Context, cards, pulse, evidence aside, footer and document height have no caps. The closure only instructs the builder to measure later (a decision deferred to the implementer). |
| 25 | CLOSED | jsdom test renamed `rendersMeasuredPanelHierarchyAndScrollContainers`. Browser proof uses `tools/layout-evidence.mjs` with listed states and widths. |
| 26 | CLOSED | `$pgReaders`, dependency-direction allowance and the `estate/composition.py` builder are named. |
| 27 | CLOSED | 1a/1b split, mount after 1b, no capture before the route, and node deltas (>=7 backend, >=9 frontend). See N6. |
| 28 | CLOSED | `/portfolio` with no alias. The rail tuple is `live|Portfolio|OPERATIONS|/portfolio`. The route test is the named Vitest file. |
| 29 | CLOSED | W3-01/02 pages are verified, not edited, and no backlinks are required. |
| 30 | CLOSED | Branch after the reviewed W3-01/02 merge. `0030` is not a gate. |
| 31 | **OPEN** | Nit. L9 still says `analytics/ev_site_reads.py`. The file is `backend/assetops_backend/ev_site_reads.py` (verified with `ls`). The closure does not correct it. |
| 32 | CLOSED | `coverage/summary/evidence_prompt/opportunity/progress` are absent on error. |
| 33 | CLOSED | `d MMM yyyy · HH:mm UTC`. |
| 34 | CLOSED | `portfolio:2` stays on `A-evidence-shared-projections` and Cost-control also depends on `A-money-projections`. `portfolio:3` is only the exclusion path. |
| 35 | CLOSED | `UNSUPPORTED` and `NOT_COMPARABLE` are stated as fixed literals. |

## Checks requested

**1. W3-03 wire literally matches W3-01/02: YES, with caveats.**
- `site_coverage` has seven keys, equal to W3-02 L155.
- Token `estate-selection/2` (9 + 4 keys, sorted, `sha256:`) equals W3-01 L267.
- Cursor is unsigned, `v:1`, no `limit`, 422 `INVALID_CURSOR` vs 409 `ESTATE_BASIS_CHANGED`, equal to W3-02 L161.
- Refusal codes and messages match W3-01 L59-63 (INVALID_LENS, INVALID_CURSOR literal).
- Domain enum and status vocabulary match W3-02.
- Differences, all deliberate: the Portfolio `after` tuple has five members (W3-01 Findings use `[timestamp,id]`), and `kind:"portfolio"`.
- Caveat: the pre-closure body still contains superseded text (see N3).

**2. Every mock element is mapped or has gap copy: YES.**
- Covered: header, date bar, badge and sentence, five cards, pulse, four lens chips, six table columns, footer, matrix, evidence aside, opportunity, change lines, business footer, and both drawers.
- The closure fills the earlier gaps: card slots, drawer tables, workflow, confidence, priority and footer.
- Residual: icons/tones per card are asserted only through "same label/icon/slots".

**3. Three-domain proof: PARTIAL, see Q9.**
- Frozen clock: yes (`2026-10-07T00:00:00Z`, window `[2026-09-30, 2026-10-07)`).
- Explicit fixtures: yes. Kobo, COLD-LAB and EV-LAB YAMLs, the two replay files, the second EV Site, `W303-EMPTY-001`, a foreign tenant, the cold later record and unsettled job, and `RESOLUTION_WITHDRAWN`.
- Literal assertions: yes for `combined_value is None`, `combined_value_state=="NOT_COMPARABLE"`, `money.estate_total is None`, the pulse note, the same window and `known_at`, and the three categories.
- Not literal: per-variant status and coverage states, and the card state in each variant. IDs are "captured from public reads", which is acceptable.

## New questions created by the closure

- **N1 `group_key` construction.** W3-02 gives only the format `sha256:<64hex>|null` (L179). W3-03 defines a canonical-JSON SHA-256 of six fields and says "match on merge". Name one owner and a shared function (W3-02) so there is not a second hash.
- **N2 Operating-cost card precedence.** The slot table has no "first match wins". One COMPARABLE group plus another partition (another currency, or a SITE_OWNED line) matches both row 1 and the WITHHELD row. Give an ordered rule.
- **N3 Stale contradictory body text.** Superseded but unedited: "signed" cursor (L7, L23), `PARTIAL` status (L17, L57), the JSON `coverage.sites` shape (L31), links-or-query lens chips (L99), "403 clears" (L114, L134), and test `clearsPrivilegedRowsOn403And503` (L156). The closure says it supersedes them, but an implementer reads the body first. Add a supersession index or patch the lines.
- **N4 Portfolio row order versus W3-01.** The Portfolio order inserts `site_code_key, site_id` before `finding_id`, while W3-01's order is `episode_start desc, finding_id asc`. State that Portfolio re-sorts the canonical set after the lifecycle filter, and that it is not the W3-01 `after:[timestamp,id]`.
- **N5 Unenumerated strings.** Objective cell `reason` text values are not listed. `evidence_prompt` has no ruling for "gaps exist but none has a non-null `next_step`" (`NO_GAP` text versus `COVERAGE_INCOMPLETE`).
- **N6 Test allocation 1a/1b.** The eight backend tests at L155 are not assigned to 1a or 1b, and the Evidence-gap and footer tests are not named.
- **N7 Fixture W1 producer.** Name the reviewed W1 producer or fixture that yields a priced, eligible, current line in the 09-30..10-07 window.

## OPEN items

1. Q6: the row wire lacks the `application_state/resolution_state/verification_outcome` fields that the workflow line needs.
2. Q9: no per-variant literal expectations (status, coverage states, card states), and no named W1 priced-line producer.
3. Q24: context, card, pulse, aside, footer and document-height caps are not measured or capped.
4. Q31: stale path `analytics/ev_site_reads.py` at L9.
