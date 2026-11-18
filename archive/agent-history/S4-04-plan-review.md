# S4-04 plan review (fresh Claude reviewer, no code)

Date: 2026-10-15
Reviewed: `tasks/S4-04-site-finding-index.md` on `plan/S4-04-refine`, packet commit `ae617221` (HEAD `2c101807` adds only the Architect request). Main is `87dc7201`; the plan branch is one log-only commit behind it. Stacked base: `task/S5-01-site-overview` (`bb4fc95d`, which contains LR-01).
Inputs: brief `.agent/planner-S4-04-brief.md`; `D-2026-10-15-a-finding-index`; `.agent/architect-A-finding-index-answers.md`; `.agent/A-finding-index-review.md`; `D-2026-10-15-s501-finding-choice`; registry nodes and panel `sitefindings:1`; v69 mock and manifest; code on main and on the stacked base (read with `git show`). `.agent/architect-S4-04-answers.md` arrived during the review. I read it and checked the rulings against the packet.

## Verdict: RETURN (one Medium; the fix is a few lines in the packet)

The packet is otherwise accurate, complete against the decision and the A-finding-index review fixes, and honest about failure cases. One Medium contract gap can produce a false assessed-zero claim.

## Findings

### M1 (Medium, fail-closed contract gap): the `domain` token has no mapping, and an unsupported domain has no refusal

- Where: packet "Read contract", the route `?domain=mini-grid-dispatch`, and "Require explicit domain ... typed 422 otherwise". The same token appears in the walkthrough URL.
- What: the token `mini-grid-dispatch` does not appear anywhere in the code. Stored Findings carry `finding.domain = 'mini_grid'` (`analytics/finding_episode.py:68`, `0009_finding_store.py` `finding.domain`) and `analytic_id = 'dispatch'` (`analytics/dispatch.py:27`). The S3 assessment `DOMAIN` is `"dispatch"` (`analytics/assessment_worker.py:51`). The packet does not mark the token as new and does not say how it maps to the stored domain or analytic, or to the S3/S4 discovery basis. The 422 rule covers only a missing domain and a bad window. It does not cover an unsupported domain.
- Why it matters: the index's "complete discovery" is computed over the dispatch analytic. A request whose domain filter matches no stored rows can then return `CURRENT` with zero rows. That happens with a literal `finding.domain = 'mini-grid-dispatch'` filter, or with `domain=cold-chain`. It is the false no-Findings claim that `D-site-finding-index-empty` exists to prevent, and it contradicts "do not silently expand to another domain". The positive fixture would catch the literal-filter mistake. Nothing in the packet catches the unsupported-domain case.
- Fix (packet text): mark `mini-grid-dispatch` as a **new** API token. Map it to `finding.domain='mini_grid' AND finding.analytic_id='dispatch'` and to the S3 `dispatch` analytic, matcher `MATCHER_VERSION`, for discovery. Return a typed 422 for any other domain value, with no status, rows or count. Add a phase-1 test that an unsupported domain gets 422, never `CURRENT` zero. Echo the resolved domain and analytic in the response.

### L1 (Low): line citations are main lines, but the stated base is S5-01

The table heading "Existing code on this base" cites main line numbers. On `task/S5-01-site-overview`, LR-01 shifts them: `_insert_revision` 161 to 162, `match_state` 400 to 404, `findings_over` 418 to 422, `scheduling/health.py:252` to 254, and `scheduling/upstream.py:133` to 139. LR-01 also changes `_insert_revision` replay to check the latest revision only, which is relevant to the extension and returned-basis revisions in the positive fixture. Fix: say "main lines; +1..+6 on the stacked base", or re-cite the lines on the base.

### L2 (Low): snapshot scope, migration and writer guard are not stated

The Architect's Q2 ruling allows `STALE_PROJECTION`/`FAILED` rows only from a durable prior selected snapshot. The packet does not say whether S4-04 builds that snapshot. If it does, the snapshot needs:

- a new migration after the base head `0015_finding_returning_basis`, re-chained against S6-01a's `0014_action_store` and S4-05a's `0014_evidence_publication`, which merge earlier;
- an architecture guard rule-8 writer entry, which OPS-02 absorbs when it merges last.

If S4-04 does not build it, STALE/FAILED return no rows, which is safe. The walkthrough step "see stale" must then expect Unknown with no rows. Fix: pick one, and recommend no snapshot in S4-04 to keep the slice size M.

### L3 (Low): focused test and evidence entry points are not named

- Phase 1 says only "new focused real-Postgres tests adjacent to ...". Name the new file, for example `backend/tests/test_s4_finding_index_postgres.py`, and add it to the `backend/TESTING.md` "S4 Finding and money" area command so reviewers can run it focused.
- Phase 2 is layout-sensitive: a dense list at 1440 and 390 px, with pagination. Name the evidence script, either `tools/layout-evidence.mjs` or a new `tools/s404-*-evidence.mjs`. Require a skipped run to be recorded as `not run` with its precondition.

### L4 (Low): the walkthrough has no explicit settle or tick step

`serve` correctly does not install the schedule. However, `late` and "gate --open, settle matching" both need S3/S4 work to run, and the subcommand list (`prepare|serve|gate|late|drop`) has no way to run it. Fix: add an explicit `settle`/`tick` subcommand, like the `recover` subcommand in `tools/s4_finding_walkthrough.py`.

### L5 (Low): wording that the Architect answers change

- Replace the three Architect questions with the rulings: Q1 409 `INDEX_BASIS_CHANGED` versus a 422 malformed cursor; Q2 the snapshot rules; Q3 the fixed-point closure, the 62-day cap and 409 `INDEX_CONTINUITY_LIMIT`.
- Add the rulings' tests: both 409s, no-snapshot reads, a bridge chain beyond one neighbour, and cap failure. Add the continuity-limit Unknown state to the phase-2 UI states.
- State that `total_count` is null unless the status is `CURRENT`, or is labelled historical for snapshot rows. The packet currently implies this through "None authorizes current count".

## Checks against the dispatch

1. **Code reality.** Every cited path exists and matches on main:
   - `postgres_finding_store.py`: lines 161-209 (insert), 213-228 (`rows`), 233-270 (detail), 274-306 (lineage), 400-416 (`match_state`), 418-430 (`findings_over`: inclusive `lo <= episode_end`, ascending).
   - `upstream.py:83-136`: the bracket match fence.
   - `findings_over` consumers: `health.py:252`, `upstream.py:133`, `finding_read.py:617`.
   - `finding_api.py`: 56-90 (open_scope 401/403/404, source_gate, `closed()` 409 `PERFORMANCE_CUTOVER_CLOSED`) and 112-135 (exact `revision_id` audit route).
   - Frontend: `App.tsx:248-255`, `operatorSiteRoutes.ts:135-139`, `FindingsIndexes.tsx:118-176` (legacy filter and empty copy), `siteAnalyticsClient.ts:242-245,338,402-406`.
   - Registry line 332 is `sitefindings:1`. Mock `index.html:329-334,640-641` and manifest `633-650` are the `sitefindings` screen.
   - Tests and tools: the three adjacent test files, `tools/s4_finding_cases.py`, `tools/s4_finding_walkthrough.py`, `tools/check-all.ps1` and `backend/TESTING.md:5-21,96-124` exist.
   - New items are marked new: the route, DTO, cursor, read, client/UI and `tools/s404_finding_index_walkthrough.py`, which is absent from main as expected.
   - Stacked items are marked stacked: S5-01 `site_overview/read.py` has `intersects`, `choose` (greatest start, smallest `str(uuid)`) and `known_finding`.
   - Exception: L1 line offsets. Walkthrough ports 8934/5434 do not collide with recorded walkthrough ports.
2. **Decision and review-fix coverage.**
   - Closed gate: 409 `PERFORMANCE_CUTOVER_CLOSED` with its reason, no rows, count or empty claim, and the pinned audit route kept separate.
   - Complete-discovery definition with continuity neighbours and the 31-day bound with 422.
   - A new read that leaves `findings_over` unchanged, with all three consumers named.
   - A same-basis test that the first row equals the S5-01 card Finding **and revision**, including a UUID tie.
   - All are present. Each of the five registry nodes' acceptance targets maps to a phase-1/2 proof, and all keep `task: S4-04` and `open`.
3. **Fail-closed honesty and stable IDs.**
   - Zero is allowed only with complete current discovery under an open gate. PENDING, UNASSESSED, STALE, FAILED and closed reads give no count or empty claim.
   - A filtered empty page is explicitly not the fixture.
   - Mock F-108/F-109, chips, "N open", the global link and money are excluded.
   - Order is `episode_start` desc then UUID asc, which matches S5-01 `choose()`. The cursor is bound to the basis, with no splicing.
   - Gap: M1, the unsupported-domain zero.
4. **Base branch, phases and owner walkthrough.**
   - Stacking on S5-01 is sensible. The decision requires the parity test inside S4-04. `.agent/coordinator-handoff.md` fixes the merge order as LR-01 then S5-01, and S4-04 follows S5-01. S4-04 touches no money path, so S4-05b's change to the S5-01 money read does not conflict.
   - Size M in two phases, with phase 2 as the slice review, focused tests per phase and one full suite at the end (command per `TESTING.md`, keep-awake, 2x cap, JUnit).
   - `USER_REVIEW_REQUIRED: true`. The walkthrough covers serve mode, 1440/390, independent empty and positive fixtures, unassessed/dirty/failed variants and close/open of the gate. Merge and registry promotion are held for the owner.
   - Gaps: L2, L4.
5. **Registry and queue.**
   - `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: "Registry valid: 228 nodes, 11 linked pilot panels", exit 0.
   - `--next-work --json`: status `ranked`, `global_stops: []`. It selects `I-finding-index` 2.143 over `I-late-reading-series-and-money-limit` 2.021, a 5.69% gap that is a notice-band tie-break, not an owner contest.
   - `queue_baseline_nodes` holds all five S4-04 nodes. The `tasks/README.md:41` row reads implementation-ready, stacked on S5-01, and the stale "remain open" text at `:9` is fixed.

**Architect rulings.** I checked the rulings in `.agent/architect-S4-04-answers.md` and they are sound and fail-closed: separate route, 409 basis change versus 422 malformed cursor, rows only from a durable snapshot, and fixed-point closure with a 62-day cap and 409. The packet still has to absorb them (L5). They do not address M1.

## Not run

No test suites and no build: this is a plan review with no code. Only the registry checker and `--next-work` were run.
