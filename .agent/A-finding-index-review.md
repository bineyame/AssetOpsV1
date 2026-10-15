# A-finding-index - independent review (fresh Claude reviewer)

Date: 2026-10-15
Reviewed: branch `plan/A-finding-index`, HEAD `002f8cfe` ("A-finding-index resolved"), base `789d76d1`.
Inputs: `.agent/architect-A-finding-index-request.md`, `.agent/architect-A-finding-index-answers.md`, `D-2026-10-15-a-finding-index` (`.ai/DECISIONS.md`), registry diff, `tasks/S4-04-site-finding-index.md`, `tasks/S5-02-overview-finding-list.md`, related decisions, v69 `sitefindings` mock, S4-01 code on this base, S5-01 read on `task/S5-01-site-overview` (via `git show`).

## Verdict: RETURN (one Medium; fix is a short contract amendment)

The contract is otherwise sound and implementable. One Medium fail-closed gap: the decision never applies the existing S3 performance-cutover source gate to the index rows/zero claim.

## Findings

### M1 (Medium, acceptance/contract gap) - S3 source gate missing from index currentness

- Where: `.agent/architect-A-finding-index-answers.md:18` (currentness) and `:28` (money); `.ai/DECISIONS.md` `D-2026-10-15-a-finding-index`.
- What: "source-open" appears only as a money gate ("unresolved source-open state means no current amount"). The currentness rules for `CURRENT` (complete discovery, no dirty/leased/failed work, no watermark mismatch) do not mention the Site's S3 performance-cutover gate.
- Why it matters: on this base `backend/assetops_backend/finding_api.py:86-90,104-107,116-117` refuses with 409 `PERFORMANCE_CUTOVER_CLOSED` when the gate is closed: "no current Finding or no-Finding verdict is shown. An exact revision_id reads audit material." The S5-01 read on `task/S5-01-site-overview` (`site_overview/read.py`) does the same: it drops to `STALE_PROJECTION`, chooses no unpinned Finding (`SOURCE_CLOSED_NO_UNPINNED_FINDING`) and allows `ABSENT` only on an open source. As written, an S4-04 implementer can return `CURRENT` positive rows, or a `CURRENT` zero-row "no Findings", for a closed-source Site. That contradicts Finding detail, which would then 409 or show audit-only, and contradicts S5-01 on the same Site/day. S5-02 would then show list rows next to an S5-01 card that says no current Finding.
- Fix: add one rule to the answers file and the decision. A closed S3 source gate (whatever reviewed form it takes, including S4-05 stored provenance once merged) forbids `CURRENT` and any zero-row claim. Either refuse the way the existing Finding routes do (409 `PERFORMANCE_CUTOVER_CLOSED`), or return the rows as audit-only/historical with exact revision links and the gate's reason, and say which. Add a closed-gate variant to the `D-site-finding-index-empty` fixture list (alongside unassessed/dirty/failed) and the matching registry acceptance target.

### L1 (Low) - discovery fence for multi-day and boundary-crossing windows not pinned

- `answers:17-18`: "complete scoped discovery" is not tied to a concrete set of analytic windows. On this base, completeness is per UTC-day analytic window (`postgres_finding_store.match_state`: `analytic_run_selection.seq` vs `finding_match_pass.selection_seq`). An episode that intersects `[from,to)` can be anchored in an earlier day through the 20-minute continuity bridge. The Planner should require every intersecting UTC-day window and its continuity neighbours to be matched through their current selection seq (as LR-01 requeue scope already does) before `CURRENT`. The Planner should also bound the selectable window length, since page size is bounded but window span is not.

### L2 (Low) - "reconcile `findings_over`" could break existing consumers

- `answers:32`: the helper's inclusive end and ascending order are correctly identified as non-conforming (`postgres_finding_store.py:418-430`). It is also consumed by `scheduling/health.py:252`, `scheduling/upstream.py:133` and `analytics/finding_read.py:617`, which S5-01 extends. The S4-04 packet should add a new index read, or prove those consumers unaffected, rather than change the helper's semantics in place.

### L3 (Low) - S5-01 card and index head should provably agree

- Ordering (episode_start desc, Finding UUID asc) matches `D-2026-10-15-s501-finding-choice` and S5-01's `choose()` (greatest start, smallest `str(uuid)`). PostgreSQL uuid byte order equals lowercase-hex string order, so they agree. Recommend that S4-04/S5-02 include a test showing that, for the same basis, the first index row equals the S5-01 card Finding.

### L4 (Low, housekeeping) - stale planning text and anchor style

- `tasks/README.md:9` still says `A-finding-index` "remain[s] open", and `tasks/S4-04-site-finding-index.md:14` still says "Decide `A-finding-index`". The Planner should refresh both at S4-04 refinement.
- The registry evidence uses the lowercase anchor `#d-2026-10-15-a-finding-index`, while sibling nodes use `#D-...`. Cosmetic only, since decisions are not headings.

## What was verified

- Implementability on this base: `finding`/`finding_revision` (append-only, `revision_no`, `episode_start <= episode_end`), `finding_merge` (superseded -> canonical), `finding_match_pass` and `analytic_run_selection` seq exist (`0009_finding_store.py`, `postgres_finding_store.py:400-416`). Canonicalization, latest revision selection, the per-window matcher watermark and the strict half-open overlap can all be built without new architecture. The exact detail URL with `revision_id` already exists (`finding_api.py:110-135`).
- Fail-closed honesty: apart from M1, a zero-row claim requires complete current discovery. PENDING/STALE_PROJECTION/FAILED/UNASSESSED never authorize a count or empty claim. Positive rows come only from persisted immutable revisions, with mock F-108/F-109 excluded. A stale list keeps its selected revision links.
- Stable IDs and ordering: the row key is `(tenant, site, finding_id)`; there is no ordering by money or arrival time; the cursor is bound to the basis and invalidated on change; the provisional priority tuple is withdrawn until a producer exists.
- Consistency: matches `D-2026-10-15-s501-finding-choice` (half-open, canonical-only, no lifecycle/money filter, same tie-break) and `D-2026-10-14-s5-selected-window-overview` (mini:3 belongs to S4-04/S5-02). LR-01 `money_eligibility` and S4-05 exact-revision provenance are consumed only for the optional amount cell. If S4-04 starts before those merge, the cell stays unavailable. Mixed/unknown source and withheld/pending eligibility show no current amount, consistent with `D-2026-10-15-lr01-source-time-cohort` and `D-2026-10-15-s405-stored-demo-provenance`.
- Mock: the decision correctly excludes the v69 `sitefindings` lens chips (All/Cost/Risks/Opportunities), the "N open" count and the "Manage in Findings" global link, none of which have producers.
- Registry: `node frontend/docs/architecture/check_v69_dependency_registry.cjs` -> "Registry valid: 228 nodes, 11 linked pilot panels", exit 0. `--next-work --json` -> `status: ranked`, not refused, no global stops. It selects `I-finding-index` 2.143 vs `I-late-reading-series-and-money-limit` 2.021 (5.69% gap, 5-10% tie-break band, `user_review_required: true`, owner notice). Removing `A-finding-index` from `outside_ranking` is correct now that it is resolved, and it stays in `queue_baseline_nodes`, still owned by S4-04. The follow-on nodes `I-finding-index`, `I-site-findings-ui`, `D-site-finding-index-empty/-rows`, `I-S4-04`, `I-overview-finding-list-ui` and `I-S5-02` remain `open`, with acceptance targets consistent with the answers.
- No owner acceptance is claimed: the decision, answers and registry targets all state that the owner walkthrough and copy acceptance remain pending.

Not run: no test suites (out of scope for a no-code architecture review).
