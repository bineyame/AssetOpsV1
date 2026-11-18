# S4-08 plan re-review: Site assumption and consequence history

Reviewer: fresh independent Claude reviewer (plan re-review; nothing built).
Reviewed: `tasks/S4-08-assumption-consequence-history.md` at `275d8a92` (`git diff 3b772205 275d8a92`), against `.agent/S4-08-plan-review.md` (RETURN, M1-M3, L1-L5), `.agent/architect-S4-08-answers.md` / `D-2026-10-16-s408` (also in `.ai/DECISIONS.md`), and `.agent/planner-S4-08-fix-brief.md`. Planner logs were not read in detail.

## Verdict: ACCEPT

All three Mediums are resolved in the packet text with named mechanisms and tests. L1-L5 are addressed. The packet agrees with `D-2026-10-16-s408`. Two new Lows are below; neither blocks.

## Checks run

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: `Registry valid: 240 nodes, 11 linked pilot panels`, exit 0. The fix round changed no registry node or queue status.
- I ran no suites, as the dispatch asked.
- Code spot-checks: `financials/assumption_read.py:1-9,82-84` (half-open `recorded_from <= c < recorded_to`; it echoes `selected_by` as `CURRENT` or `RECORDED_CUTOFF`); `frontend/src/sites/SiteFinancials.tsx:185-235` (price paging is in React state, not the URL; the notice shows only for a URL cutoff); `actions/site_index.py:10-14,170-182` (the S6-03 fence, typed 409 and page-one instruction).

## Prior findings

| Finding | Status | Where in packet |
| --- | --- | --- |
| M1 no current amount at any cutoff | Resolved | Item 3 says the endpoint and panel "never claim or display a current amount at any cutoff, including the server-defaulted cutoff". It adds the constant `current_amount_shown: false` and the label "Recorded amount — historical, assumption-conditioned audit history". The per-Site `derive()` is forbidden, and `CURRENT_AT_CUTOFF` links to Finding Financials. Test: "no **current** amount at the defaulted cutoff even with all current-money gates passing". |
| M2 cursor fence and typed 409 | Resolved | Item 1 fences count plus max `(recorded_at, id)` over all in-scope rows, computed in the page's snapshot. The cursor binds tenant, Site, cutoff, limit, last pair and fence. It refuses with 409 `CONSEQUENCE_HISTORY_BASIS_CHANGED` and the UI reloads page one, keeps 400 for tampering, and cites `site_index.py:10-14,174-182`. The late-commit reload limit is recorded. Test: a deterministic interleaving with the row stamped before the cutoff, page one taken while it is uncommitted, then commit, then page two, which must return 409. A post-cutoff exclusion test is also kept. Rows are immutable, so a count-plus-max fence detects every insert below the max. |
| M3 one shared cutoff | Resolved | Mechanism (a): the default view requests consequence page one first, then passes the returned `cutoff.recorded_at` to the price read and to every later page. The default URL is not rewritten, because the cutoff is held in UI state. The S4-02a notice stays explicit-URL-only, the S4-02a walkthrough asserts the unchanged URL and identical instants, and the price API's no-cutoff `CURRENT` contract is kept for other callers. Test: both reads report the same instant on the default view and on an explicit URL, and reload semantics are covered. |
| L1 path | Fixed | `backend/assetops_backend/financial_read_api.py`. |
| L2 FindingRevision clock | Fixed | It names `finding_revision.created_at` (application clock). A FindingRevision with a consequence at or before C qualifies; the latest is chosen by `revision_no`. Test: injected or skewed `created_at`, plus the same-instant boundary. |
| L3 price filter | Fixed | Dropped: "no `price_revision_id` filter"; the foreign price-ID refusal is removed. |
| L4 walkthrough tool | Fixed | `tools/s408_assumption_history_walkthrough.py`, which may wrap `s402a_assumptions_walkthrough.py`. |
| L5 merge order | Fixed | S4-08 merges before W1-UX-02. W1-UX-02 applies its presentation to the new panel. |

## Architect ruling agreement

- Q1: unpriced versions are included with a typed missing-price state and a null amount, and are not omitted from paging (items 2 and 4, test list). Agrees.
- Q2: item 3 matches the ruling's wording. If the latest FindingRevision has no consequence, no row is current. The classification uses the same scoped, fenced read. Agrees.
- Q3: amounts are historical, assumption-conditioned audit history with the exact-version S4-05b label. A closed source hides them, and missing or withheld amounts are null. Only the separate Finding Financials read may claim current money. The packet applies this to the default cutoff as well, which is stricter than the ruling and consistent with it. Agrees.

## New findings (Low, non-blocking)

### L-R1 (Low): pass the returned cutoff verbatim

M3 relies on the UI passing `cutoff.recorded_at` from the consequence response to the price read. If the client round-trips it through `Date` (`toISOString()` truncates to milliseconds), the price read could select an instant up to 1 ms earlier than the consequence cutoff. A consequence row stamped in that gap could then cite a price assignment missing from the displayed timeline. Fix at build: pass the server string unchanged, in the UI state and in the next-page and explicit URLs. The same-instant test should compare the exact strings, with sub-millisecond precision.

### L-R2 (Low): the default price list now depends on the new read

Under mechanism (a), the default Assumptions price list cannot load until consequence page one returns its cutoff. The packet does not say what the price list shows when the consequence read fails or is refused. Previously the price list was independent of it. Also, `frontend/src/sites/__tests__/siteFinancials.test.tsx:334` asserts that the default view sends `recordedAt: null`, and `data-price-cutoff` changes from `CURRENT` to `RECORDED_CUTOFF` on the default view. These are intended consequences of M3, but they are not named. Fix at build, recorded in the review packet: either fall back to the existing `CURRENT` price read with no shared-cutoff claim and a visible notice, or show the price list as unavailable. Name and update the existing test expectation and marker deliberately; do not silently rewrite them.

## Residual risk

- Size S remains tight. The proof matrix is wide: interleaving, the skewed clock, shared-cutoff plumbing, five UI states at two widths, and the walkthrough tool. It is credible now that the per-row `derive()` is gone.
- The frontend suite and build cannot run in the reviewer sandbox on this machine (a known esbuild ancestor-read denial). Implementation review must rely on `tsc` and the implementer's recorded runs for those.
