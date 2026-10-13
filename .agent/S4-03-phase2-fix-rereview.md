# S4-03 phase 2 fix round - fresh Claude re-review

Reviewer: fresh Claude Reviewer. I did not author this phase or its fix round. Date: 2026-10-13.
Branch `task/S4-03-finding-evidence-history`, HEAD `b876b9b`. Diff reviewed: `3897dcc..b876b9b` (`bc9a602`, `3dc9806`, `b876b9b`), judged against `.agent/S4-03-phase2-review.md` (M1-M4, L1-L4) and `.agent/architect-S4-03-answers.md` (Q1 and Q2 overruled, Q3 ratified).
I made no code edits. Mutation spot-checks were reverted with `git checkout`, and the tree was clean afterwards apart from the coordinator's unstaged `.agent/coordinator-handoff.md`.

## Verdict: ACCEPT

Every must-fix item is fixed as the Architect ruled, and each fix has a test that fails without it.

Four Low findings remain (N1-N4). None is an acceptance blocker. They should be fixed in phase 3 before the owner walkthrough, or carried explicitly.

The M4 shape the Implementer chose still needs Architect ratification (carry R1). The Architect answers do not rule on M4.

## Checks I ran

| Check | Result |
| --- | --- |
| `npx.cmd vitest run` (frontend) | 60 files, 1422 tests passed, exit 0 |
| `npx.cmd tsc --noEmit` | exit 0 |
| `npm.cmd run build` | exit 0 (chunk-size warning only). The bundle contains no backend source: `BROKEN_WORDS` does not appear in `dist/assets`. |
| `pytest test_s4_finding_api.py test_s4_finding_evidence_history_api.py test_s4_finding_evidence_history_postgres.py` with `ASSETOPS_TEST_DATABASE_URL` set to `assetops_test` | 26 passed, 0 skipped. This includes the Postgres file, rerun at HEAD. The packet had flagged that file as not rerun after the last commit. |
| `tools/check-all.ps1` | 9 of 9 guards passed. Missing-claim scan: 3 tagged, 16 baselined. Ledger valid. Dependency registry passed. Gap catalogue fixtures passed. |

The sandbox esbuild failure did not occur in this session, so the frontend suite and the build are verified by me.

### Mutation spot-checks (fail before, pass after)

- **Whole UI file reverted to `3897dcc`.** Command: `git checkout 3897dcc -- SiteFindingEvidence.tsx`. Result: 12 of 29 tests in `siteFindingEvidence.test.tsx` fail. They cover every new test for Q1/M1, M2, L1, L2, M4, the unknown-link case and the M3 assertion.
- **Strict overlap made inclusive** (`<=`). Exactly the two exclusion tests fail: "touches the window start" and "ends exactly at 00:00".
- **Backend `finding_read.py` reverted to `3897dcc`.**
  - The backend test `test_broken_lineage_words_are_product_safe_at_source` fails.
  - Both tests in `findingLinkWordsParity.test.ts` fail.

### Owed phase-2 check: Evidence read against stored rows and messages

I made a private copy:

- Command: `tools/s4_finding_walkthrough.py --db assetops_s403rr_walk --work %LOCALAPPDATA%\Temp\s403-rereview-walk prepare`.
- It copied `assetops_s4cases` read-only, and the comparison PASSED.

No server was started. I read through the real `build_finding_router` with a TestClient over the private database. I walked every Evidence page at limit 37, which forces several pages.

For each revision whose cited set lies within the manifest case, I checked independently:

- The API's evidence IDs equal the `finding_revision_evidence` rows, with no duplicates.
- Each record matches its `accepted_evidence` row:
  - SHA-256 of the stored `envelope_text` = stored `envelope_sha256` = the API's `envelope.sha256`, with `digest_verified` true.
  - The API's `message_id` = the row's, and that message ID appears inside the stored message text.
  - The API's role = the row's role.
  - `lineage_status` is RESOLVED.
- The writer's cited-set digest recomputed in Python equals both the stored `cited_evidence_sha256` and the read's `recorded` value.
- Every cited ID is in the `evidence_ids` of one of the revision's cited assessment revisions.

| Case | Finding / version | Cited = API | Row/message mismatches | Digest | Lineage |
| --- | --- | --- | --- | --- | --- |
| F01-gateway | `624f2558` v1 (`f6788262`) | 102 = 102 | 0 | match | COMPLETE |
| F04 | `d176a8f0` v1 (`026aa091`) | 42 = 42 | 0 | match | COMPLETE |
| F04 | `d176a8f0` v2 (`e2af70fd`) | 78 = 78 | 0 | match | COMPLETE |
| F04 | `d176a8f0` v3 (`d6b6a6e6`) | 78 = 78 | 0 | match | COMPLETE |

Cleanup:

- `drop` removed the database and the marked work folder. My scratch script was deleted.
- The L4 guard was also checked on a marker-less folder: `drop` kept it and said why.
- No owner port or non-private database was touched apart from `assetops_test`, which was used for tests.

### Not verified by me

- Browser and layout evidence at 1440/390 for the changed Evidence view: one new table and two to three new lines.
- The legacy tab.

The packet records these as not rerun and defers them to the owner walkthrough. That is acceptable for this fix round, but phase 3 or the walkthrough must cover them.

## Item by item

- **Q1 / M1 - fixed as ruled.**
  - The `<Navigate replace>` is gone. One result renders the same candidate link list as several results.
  - The heading is "Findings recorded for this day". The text says the list "only helps you find a Finding by its day: it does not say this assessment created or cites it".
  - `daysTouched` reads every UTC day the window touches. The end instant is excluded.
  - `overlapsWindow` is strict on both sides. The no-result, unreadable and partial-read states keep the records link.
  - Tests cover: no navigation on a single result; an unrelated same-day Finding; Findings touching the start or the end; a Finding ending at 00:00; and a window that crosses midnight.
  - Wording nit: N3.

- **Q2 - fixed as ruled.**
  - `BROKEN_WORDS`, `LINEAGE_STATEMENT` and `withheld` are product-safe at source. Codes are unchanged. Backend tests ban the engineering words.
  - The UI never renders `lineage.words`, `set_breaks.detail` or backend `withheld`. It uses `LINK_WORDS` and a local `WITHHELD`.
  - An unknown code renders "A record link could not be checked" with the code only inside `[data-evidence-technical-detail]`. The positive claim stays withheld (tested).
  - **Is the `?raw` parity test robust?** Yes for this repository:
    - It ran under the full vitest suite.
    - `tsc` accepts it through the ambient `src/test/rawSource.d.ts`.
    - Only the test imports it, so the production bundle is unaffected (checked).
    - The line regex reads only single-line, double-quoted `"KEY": "value"` entries. A reformatted value would be dropped and fail the key-equality assertion loudly, not pass silently.
    - Limitation: it needs `backend/` present wherever the frontend tests run. That is true for this monorepo, but it would break a frontend-only CI image (residual).

- **M2 - fixed.**
  - A non-SUPPORTED `revision.lifecycle` leads the Selection panel. Tested for MERGED, UNCONFIRMED and NO_LONGER_SUPPORTED as the panel's first element.
  - SUPPORTED reads after the version lines, so "Record only" still leads on a closed source.
  - Wording nit: N2.

- **M3 - fixed.** `sourceModeWords` gives "Demonstration data" or "Live data". The raw mode is kept only in `data-source-mode`. Both exemptions were removed and the test asserts that `SIMULATED` is absent.

- **L1 - fixed:** a dash appears when `minutes()` is null (tested).

- **L2 - fixed:** "(stored message missing)" appears for ENVELOPE (tested).

- **L3 - closed** by the parity test plus fixing at source.

- **L4 - fixed as asked:** `drop` deletes only a folder holding the `prepare` marker (verified both ways). Residual: N4.

- **M4 - built as option (a) plus a page-scoped table.** The G-01 consistency is clean:
  - Gap IDs `G-finding-evidence-coverage` and `-use` agree across the registry `mock_gaps`, `gapCatalogue.ts` and the ledger `finding-evidence.gap_ids`.
  - Each has a single unique placement (`finding-evidence.bundle.coverage` and `.use`). There is one claim per element and one element per gap.
  - The copy uses the bounded phrase "not available yet".
  - The scan counts 3 tagged placements, the baseline is unchanged, and the gap ID is not in product text (tested).
  - Whether the page-scoped table is honest: see N1 and carry R1.

## Findings

### N1 - Low (fix in phase 3 before the walkthrough): the page-scoped "by measurement" note implies counts accumulate

- **Where:** `frontend/src/sites/SiteFindingEvidence.tsx:458-461`.
- **What is wrong:** the scope note says "Counted from the N cited records on this page (records a-b of T); other pages are counted when opened."
  - The table is recomputed from `body.records` for each page. It never accumulates.
  - "Other pages are counted when opened" reads as though opening them adds to these counts.
  - The heading ("Inputs on this page, by measurement") and the first clause are honest; the last clause is not.
- **Why it matters:**
  - It stands in for the mock's whole-bundle Input/Source summary (`finding-evidence:1`).
  - It sits directly above "Where the cited records came from", which *is* whole-set (`provenance.cited_evidence_by_source`, computed over all rows).
  - Two adjacent tables with different scopes, one of them worded ambiguously, invite a reader to take page counts as bundle counts.
  - With 102 cited records (F01-gateway) at 50 per page, the first page shows about half the bundle.
- **Fix, in order of preference:**
  1. Add a whole-set `cited_evidence_by_role` aggregate to the read, next to `cited_evidence_by_source`. `rows` already carries `role`, so it is a few lines plus a test. Render that instead.
  2. Or keep the page table and reword the clause to "each page shows the counts for its own records".
- **Type:** acceptance-adjacent honesty issue, not a preference. Not blocking, because the heading and the first clause state the scope correctly.

### N2 - Low: the UNCONFIRMED lead says "the earlier versions stay available below", which is false on the Evidence page

- **Where:** `SiteFindingEvidence.tsx:258-264`, reusing `LIFECYCLE_WORDS.UNCONFIRMED.sentence` (`frontend/src/sites/findingWords.ts:22-23`).
- **What is wrong:** that sentence was written for the Finding root. The Evidence page lists no versions below it.
- **Fix:** use the label plus a page-neutral sentence on Evidence, for example "...the earlier versions stay available in this Finding's history". Add a test assertion.

### N3 - Low (wording): day-level labels on a cross-midnight window

- **Where:** `SiteFindingEvidence.tsx:899` (heading) and `:922` ("(recorded for the same day)").
- **What is wrong:** when the window touches two days, the label correctly reads "2026-10-09 to 2026-10-10". The heading still says "this day", and each link says "the same day", although a candidate may come from the other day.
- **Fix:** "Findings recorded for this period" or "for these days", and "(recorded for an overlapping day)". This is not a correctness issue: the overlap filter is right.

### N4 - Low (tooling residual): the marker proves `prepare` ran in a folder, not that it created it

- **Where:** `tools/s4_finding_walkthrough.py:168`.
- **What is wrong:** `prepare` writes the marker into any existing `--work` folder. A mistyped existing folder (for example the home folder) gets the marker on `prepare` and is then removed whole by `drop`.
- **Fix:** have `prepare` refuse an existing non-empty work folder that has no marker. This is outside the L4 wording, so it is a carry, not a regression.

## Carries

- **R1 (Architect):** ratify M4's shape: two catalogued `<MissingClaim>` gaps for Coverage and Use, plus an Input/Source table. Decide whether that table must be whole-set (N1 option 1) or may stay page-scoped. The Architect answers cover Q1-Q3 only. "Alternatives" and "Recommendation" stay in G-04.
- Phase 1 C1 (`ASSESSMENT_CITATION`): unchanged.
- Residual: refusal panels print the backend `message` verbatim ("Reason given:"). Inherited from S4-01; unchanged.
- Residual: the `?raw` parity test needs `backend/` present at frontend test time.
- Residual: no 1440/390 or browser evidence for the changed Evidence view or the legacy tab. It is owed in phase 3 or the owner walkthrough.
- Q3 phase-3 proof (old → new → Evidence → old, reload, back/forward, exact revision IDs) remains owed, as the Architect ruled.
- The phase-2 reviewer's owed row/envelope comparison is **discharged** by this re-review (table above).
