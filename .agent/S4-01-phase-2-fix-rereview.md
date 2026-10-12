# S4-01 phase 2 fix round 1: independent re-review

Reviewer: a fresh Claude reviewer (no part in authoring the slice or the fix), 2026-10-12.
Branch `task/S4-01-finding-identity`, diff `d2599de..HEAD` (`254b843` code and tests, `90e9a1e` closeout).
Against: `.agent/S4-01-phase-2-review.md` (B1, B2, C3), `.agent/architect-S4-01-answers-3.md` /
`D-2026-10-12-s4-finding-phase-2-read-boundaries` (Q16-Q20), packet "Fix round 1", questions Q21-Q24.

## Verdict

**Accept.** B1, B2 and C3 are closed, and Q17, Q18, Q19 and Q20 are implemented as ruled. Each one has a test
that pins it. I found no blocking issue. Three low carries are listed below (C7-C9). Phase 3 may start.

## Closure of the earlier findings and rulings

- **B1 closed.** In `finding_read.py` `window_state`, a CURRENT window whose window revision is INDETERMINATE and
  has no Finding now returns `NOT_DETERMINABLE`. The body now carries `window_claim_level`, `window_limitations`,
  `selected_run_id`, `watermarks` and `finding_match`.
  - The Postgres test now checks the expected state for every day from 10-05 to 10-23 (`EXPECTED_DAYS`). I
    reran it.
  - 10-19 is `NOT_DETERMINABLE`, with claim level INDETERMINATE and an `AMBIGUOUS_COHORT` limitation.
  - 10-15 is LIMITED and discloses its limitations.
  - A complete day with no Candidate (10-25) has its own test, which expects `NO_FINDING`.
- **Q18 closed.** Each committed matcher pass now writes an append-only `finding_match_pass` row. The row is
  written inside the fenced `apply` transaction, under the advisory lock and after the fence check.
  - `match_state` reports `matched` only when the latest `finding-episode-2` pass has a `selection_seq` at or
    above the window's current maximum selection `seq`.
  - The window is read before `match_state`, and selection seqs only grow. A race can therefore only show a
    pending state, never an early `NO_FINDING`.
  - The test shows `FINDING_MATCH_PENDING` before the pass and `NO_FINDING` after it.
- **B2 closed.** Pinning an older revision now gives `SUPERSEDED_BY_LATER_REVISION`, with `latest_revision_id`,
  and keeps the per-window detail. `state.claim_is_current_refers_to` is `LATEST_REVISION`.
  - In my probe, pinning the *latest* revision by ID still reads `CURRENT`, not superseded.
  - The F04 r1 assertions are in the Postgres test.
- **C3 closed.** `TestWindowRouteMatrix` covers `/finding-windows/{day}`: 401 with `WWW-Authenticate` before any
  lookup, then 403, 404 and 503.
- **Q19 closed.** The Finding router uses the same `performance_gate` function as the S3 Performance router. It
  is checked after access and Site scope.
  - An unconfigured gate is closed. A gate that raises a store error gives a typed 503.
  - While the gate is closed, the default Finding read and the window read both return 409
    `PERFORMANCE_CUTOVER_CLOSED`.
  - While the gate is closed, a pinned `revision_id` returns 200 with `audit_only.non_current`, projection
    `SOURCE_CLOSED` and `claim_is_current` false. The S3 `assessment_revisions` and `windows` links are empty,
    and `links.performance` gives the reason.
  - While the gate is open, both S3 links are emitted.
- **Q17 closed.** `FindingMatcher.bases` reads each CURRENT window's selected-run evidence once per run. This is
  the exact `analytic_run_evidence` set, joined to `ingestion_disposition` with no row limit. `_stop_proof`
  refuses the bridge in any of these cases:
  - a window is not usable, not covered, unread or Indeterminate;
  - a generator cohort limit overlaps the stop;
  - a report strictly between the last ON and the next first ON is unaccepted, not GOOD, from outside the
    cohort, or not OFF;
  - an OFF endpoint is absent.

  A confirmed proof cites the endpoint and checked evidence IDs, the run and window revision IDs, and
  `reports_sha256`. `TestStopProof` covers each refusal, including the Architect's case of a contradictory state
  between two valid OFFs. Each refusal yields two Findings with no continuity. On Postgres, all 3 recorded
  bridging stops in the full fixture are `CONFIRMED`.
- **Q20 closed.** `MATCHER_VERSION` is now `finding-episode-2`. The normalized relation facts are in
  `support_sha256`, and the full continuity and recurrence records are in `basis_sha256`. The opening recurrence
  is read from revision 1 and carried on `Episode.recurrence` into later supported and merged writes.
  - I checked that a rerun changes nothing after the version bump. After all specified cases ran on Postgres, a
    further `match()` planned 0 writes and appended no revisions.
  - That rerun added exactly one `finding_match_pass` row.

## Findings (none block)

### C7 (carry, low): pinned audit body still carries recorded positive claim fields
`finding_api.py:111-133`. When the gate is closed, the pinned 200 body still includes `state.lifecycle:
SUPPORTED`, the claim's Candidate minutes and its spans, as recorded. The marking is correct and matches what
Q19 permits: `audit_only`, `SOURCE_CLOSED` and `claim_is_current: false`.

The risk is in phase 3. The UI must lead with the closed-source, audit-only state and must never show the
recorded lifecycle as a live badge. Phase 3 should add a UI assertion for this.

### C8 (carry, low): unsupported revisions omit the recurrence record
`finding_episode.py:503-531` (`_unsupported_write`). UNCONFIRMED and NO_LONGER_SUPPORTED revisions have no
`claim.recurrence`, so the relation facts hashed for those revisions leave recurrence out. Nothing visible is
wrong: the read takes recurrence from the opening revision, and a later SUPPORTED revision carries it again.

Q20 asks to "show the selected revision's recorded relation proof". That is met through the immutable opening
record, not per revision. Recording it on every revision would make each revision self-describing.

### C9 (carry, low): `finding_match_pass` grows by one row per pass
`postgres_finding_store.py:132-137`. A row is written even for passes that write nothing. This is harmless at
fixture scale, and only the latest row is read, through an index. S4-04 should bound it, together with the
per-run evidence read the packet already names.

C5 (one-hop canonical) and C6 (window read cost, midnight boundary) still carry, as the packet says.

## Q21-Q24: is each built default safe?

- **Q21, recurrence uses the stop proof: safe.** It fails toward "relation unknown", never toward a false link.
  It is also the only way to stop a refused bridge from coming back as a LINKED recurrence.
- **Q22, editing the unmerged migration 0009: safe.** I checked every database on the Compose Postgres (55432),
  read-only: `assetops`, `assetops_test`, `assetops_s2demo`, `assetops_s102_scratch`, `assetops_s3cases` and
  `assetops_s3walk`. All are at 0008 or earlier, and none has a `finding` table. No persistent database has
  applied 0009, so a 0010 is not needed. A database elsewhere that had applied the old 0009 would fail with
  `UndefinedTable` on `finding_match_pass`, but I found none.
- **Q23, the ungated operator CLI: safe.** It is a labelled operator and fixture tool, not a product route.
- **Q24, pinned audit read while the gate is closed: safe.** It uses only the Finding store's immutable
  citations. I confirmed it makes no S3 read: I replaced DispatchReadService with a stub that raises on any
  attribute except the in-memory manifest `_annotate`, and the read still returned 200. Phase 3 should handle
  the body as described in C7.

## Checks run by this reviewer

- `pytest backend/tests/test_s4_finding_api.py backend/tests/test_s4_finding_episode.py` (no DB): `48 passed`.
- The four S4 Postgres suites (`test_s4_finding_api`, `_episode`, `_read_postgres`, `_store_postgres`) on an
  isolated `assetops_s4p2rr_test`: `57 passed in 108.53s`, which matches the packet.
- A scratch probe on the same isolated DB, kept in the scratchpad and not committed. It covered:
  - rerunning the matcher: `planned=0`, revisions stayed at 29, passes went from 16 to 17, all
    `finding-episode-2`;
  - with the gate closed, a pinned read using the stub that raises on S3 calls returned 200 `SOURCE_CLOSED`;
  - with the gate closed, the default read returned 409, and the window read returned 409 with a typed body;
  - a gate raising `AssessmentStoreUnavailable` returned 503;
  - pinning the latest revision returned `CURRENT`;
  - 10-19 returned `NOT_DETERMINABLE`;
  - the stored stop proofs were 3 CONFIRMED.
- The full backend suite with Postgres on the isolated DB: `1893 passed in 873.84s`, which matches the packet.
- `tools/check-architecture.ps1` and `tools/check-agent-workflow.ps1`: both passed.
- `assetops_s4p2rr_test` was dropped afterwards. No owner server, port or `var/` was touched.

## Not verified

- I did not rerun the producer (`tools/s4_finding_cases.py run`), so its result is unchecked: VERIFY PASSED, 11
  Findings / 30 revisions. It starts TLS, lab-api and gateway processes. I read its recorded output instead. That
  output agrees with my Postgres probe, which gave 10 Findings / 29 revisions without the gateway case.
- I did not rerun the host, gateway or simulator suites, or check-all. Those numbers are the packet's.
- I did not repeat the implementer's mutation runs. I read each test against its fix instead.
- There is no frontend change, so I ran no frontend checks. Layout evidence does not apply.

## Residual risk not named in the packet

- Phase 3 must not show the recorded SUPPORTED lifecycle in the closed-gate audit body as current (C7).
- A long stop with sparse reporting still bridges when both OFF endpoints are present and nothing contrary lies
  between them. Missing reports are not treated as contrary. This is consistent with the Q11 and Q17 rule
  ("every intervening report"). It is still a model choice, and the owner walkthrough may want it labelled.
