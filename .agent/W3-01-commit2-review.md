# W3-01 commit 2 independent review (estate read core and integration)

Reviewer: fresh Claude reviewer, 2026-10-20. Branch `task/W3-01-estate-claim-action-roots`, head `4cf4475f`, range
`a75b0291^..4cf4475f` without merges. The prerequisite commits that were already accepted are excluded. In scope:
`estate/*`, `estate_api.py`, the `main.py` mount, the `estate` guard domain and `tools/checks/test_estate_guard.py`,
the golden manifest and its test, and the q8/q9/q10 changes. Authority: `.agent/W3-01-build-spec.md`, which includes
Run 1-10, token v2 and Finding wire `estate-finding-index-2`; the phase handoff; and pending q11.

## Verdict: REVISE

There is one Medium finding, M1: a page-two cursor fence fails on a mini-grid Site for every request while that Site is
pending or stale. M1 should be decided together with q11, because both have the same root cause and would take the
same fix. Everything else checked holds:
- one snapshot;
- scope and access;
- precedence;
- the q7 cutoffs;
- the token;
- the money gates;
- Action counts;
- the refusal table;
- the EV trigger.

## Checks run (this review)

- Private DB `w301u_test`, run once and serially: `test_w301_estate_coverage.py`, `test_w301_estate_api.py`,
  `test_w301_estate_index_postgres.py`, `test_w301_estate_index_ev_postgres.py`, `test_w301_estate_golden_postgres.py`
  (4 branches) and `tools/checks/test_estate_guard.py`. Result: **28 passed, 0 skipped, 0 failed, 734.8 s** (wall
  12 min 19 s). The DB was dropped afterwards.
- A pure probe of `coverage.site_coverage`, written in my scratchpad and not committed, reproduces M1. It used a fake
  mini-grid snapshot with one matched, selected day:

  | Day condition | Page one (live) | Page two (cursor, historical) |
  | --- | --- | --- |
  | Pending job | `PENDING_RECOMPUTE`, `selected_finding_revision_ids=[]` | `HISTORICAL`, `[<frid>]` |
  | S3 `STALE_PROJECTION` | `STALE_SOURCE`, `[]` | `HISTORICAL`, `[<frid>]` |
  | S3 `PENDING` | `PENDING_RECOMPUTE`, `[]` | `HISTORICAL`, `[<frid>]` |

- `tools/check-architecture.ps1`: see the addendum at the end of this file.
- Not run: the full backend suite (out of scope; another slice's suite was running). The frontend has no commit-2
  change.

## Findings

### M1 (Medium): page two always returns 409 while a mini-grid Site is pending or stale

**Where:** `backend/assetops_backend/estate/coverage.py:109-113` and `:124`, with `estate/index.py:95-96`.

**What goes wrong:**
- A cursor continuation runs with `snapshot.historical=True` (`index.py:95`).
- On a live page one, `_mini_grid` labels the Site `PENDING_RECOMPUTE` or `STALE_SOURCE` and returns no rows (`:124`).
  That happens when there is an overlapping PENDING/LEASED job, a PENDING/FAILED S3 status, or a STALE S3 status on a
  matched, selected day.
- On page two the same Site is "provable", so it becomes `HISTORICAL` and its selected rows are populated.
- `selected_finding_revision_ids`, `cited_accepted_evidence_ids` and the consequence arrays therefore change. The
  `estate-selection/2` token changes, and page two is `409 ESTATE_BASIS_CHANGED`.

**Why it matters:**
- Nothing changed between the two requests, and a reload reproduces the 409 every time until the Site settles. Paging
  is unusable for any estate with one late-evidence mini-grid Site and more than `limit` rows elsewhere.
- This is the mini-grid form of the defect that q10 ruling 3 fixed for cold/EV ("an unchanged open job is not a
  selection change"; "supersedes any q8 reading that makes page two fail solely because its cutoff became
  historical").
- Ruling 3's text names only `EstateSnapshot.open_jobs`, so the implementer is not off-ruling. The gap is in the ruling.

**Failure scenario:** take KOBO-001 with the `kobo-late-accepted-delivery` state and a second Site with 2 or more rows.
Read Findings with `limit=1` and no `known_at`. Page two returns 409, and every retry returns 409.

**Test gap:** no test pages a live estate that contains an unsettled mini-grid Site.

**Fix (needs the Architect, together with q11):**
- Record page one's mode (live or explicit historical) in the cursor (cursor `v:1` would need a key; that is the
  Architect's call).
- Evaluate page two with page one's state semantics at the cursor cutoff, for both mini-grid and cold/EV.
- Add a mixed paging test with a pending mini-grid Site.

### L1 (Low): a non-lineage provenance failure becomes 409 instead of 500/503

**Where:** `analytics/adapters/postgres_assessment_store.py:1668` maps any non-DB exception in cold/EV link reads to
`ColdReadUnavailable`/`EvReadUnavailable`. `estate/composition.py:43` and `estate/adapters/postgres_estate_read.py:64`
then turn those into `ESTATE_SELECTION_INCONSISTENT`. An unwired link reader gets the same 409 treatment.

**Why it matters:** a programming or wiring error surfaces as "Some records are being updated. Reload the list." after
one retry. Run 8 ruling 9 says arbitrary programming errors must not become 409.

**Fix:** narrow the estate mapping to the typed lineage refusals: the pinned-row `ColdReadUnavailable` /
`EvReadUnavailable` messages, or a dedicated subclass. Alternatively, record this as an accepted limitation.

### L2 (Low): a cold estate row is not tied to the pinned selected assessment

**Where:** `estate/adapters/postgres_estate_read.py:190-196`.

**What goes wrong:**
- The row is the latest `finding_revision` by `revision_no` with run `knowledge_cutoff <= evidence_cutoff` and
  `created_at <= k`. Nothing requires its `assessment_revision_id` to be among `snap["selected"]`.
- If a later run's revisions were created at or before `K` but that run's selection has `selected_at > K` (the gap
  between completion and selection), a read at `K` shows an unselected revision under the older pinned selection.
- The `_item` check only compares the episode's assessment with the revision's assessment.

**Status:** this is consistent with Run 6's literal instruction (the W2 `current_findings_on` semantics plus
`created_at <= k`), but it conflicts with "the selected-row set ... is the estate's Finding authority". The window is
narrow. The fix is to require `rev[8]` to be in the selected revision IDs, or the Architect can confirm the limitation.

### L3 (Low): Lane A's q11 readings 1-4 were dropped from the pending-rulings file

**Where:** `.agent/W3-01-pending-rulings.md` (the q11 section).
- `429f4499` recorded Lane A's "q11" readings 1-4 (UI DTO deferred to commit 3, guard-test home, the `main.py` mount,
  dependency direction).
- Lane B's merge took main's version and reused the label q11 for its own reading.
- The handoff (`:342`) still points to "Readings q11 1-4".

**Why it matters:** the Architect never sees those four readings, and two different items both carry the q11 label.

**Fix:** restore them, for example as q11-A 1-4 beside Lane B's q11-B 1.

### L4 (Low): no test proves the single transaction or the token rebuild independently

**Single transaction:** no test detects an injected service opening its own connection, for example by spying on
`_connect` or `create_engine` of the injected cold/EV/consequence/eligibility services during an estate read. Code
inspection confirms one connection today.

**Token rebuild:** the golden rebuild (`test_w301_estate_golden_postgres.py:485-517`) is independent only in
canonicalization. It reads the selected sets through the same `EstateSnapshot` methods as the code under test
(`selected_windows`, `dispatch_days`, `finding_lineage`, `consequence`, `action_basis`), and `$public` IDs come from
an estate reference read. That is q10 reading 4, which has not been ruled. A wrong-but-consistent selection would pass
the golden. `test_cold_ev_day_intersection_selects_exact_windows` does compare against direct stored heads, which
partly covers this.

**Fix:** add a connection-spy assertion. Have the Architect confirm or tighten q10 reading 4.

## Verified holding (summary)

- **Single snapshot:**
  - `PostgresEstateRead.read` uses one connection (`postgres_estate_read.py:59-61`): REPEATABLE READ, `SET TRANSACTION
    READ ONLY`, then one `now()`.
  - Every helper takes `self._c`. The cold/EV `_public(c)` and `link_rows_on` reads are bound to `c`.
  - There are no per-Site transactions. The retry opens a fresh whole snapshot.
- **Scope and access:**
  - Authentication runs before parsing and any store call (the API test asserts `store.calls == 0`).
  - The tenant comes only from `registry.tenant()`. Sites are tenant-filtered with `imported_at < to`, inactive Sites
    included.
  - A per-Site `access` check admits each Site before it enters any row, count or digest. There is no 403/404.
- **Coverage and precedence:**
  - Estate level: historical, then pending, then stale, then unknown, then current (`index.py:26-33`).
  - Cold/EV: jobs or pending, then stale probe, then unknown, then current. No windows gives UNKNOWN with null totals.
  - Mini-grid follows the Run 6 per-day order. Its rows appear only for CURRENT or HISTORICAL. NOT_APPLICABLE applies
    only to the Action root (`site_type` CHECK is exhaustive).
- **q7 cutoffs:** `evidence_cutoff = max(decided_at) <= requested k` goes to W2 `known_at`, `selection_cutoff = k`.
  The wire and token carry the requested `k`. A null watermark gives UNKNOWN.
- **Token and cursor:**
  - The token is canonical `/2` over full-set arrays plus the cursor fence on tenant, Sites, access basis, window,
    lens/state and token. It is checked after the full read, so it fires on an empty page too.
  - The cursor cutoff is authoritative, and a supplied cutoff must match at full precision or as its wire-second copy.
  - Page two at the cursor cutoff keeps the cold/EV work fence (q10 ruling 3; the test is non-vacuous: a changed job
    gives 409).
  - A malformed cursor is 422; a foreign digest is 409.
- **Money and Cost:**
  - `PRICED` and `COST` require all of: the exact `select_consequence_on` row, stored PRICED, a non-historical cutoff,
    `currentness=CURRENT`, `for_finding_on=ELIGIBLE`, `source_gate.permits_current_money`, ordered bounds and an
    uppercase ISO currency.
  - Otherwise the row is UNKNOWN with its revision ID, or UNPRICED. Cold/EV rows are UNPRICED.
  - Wire v2 has `amount_low`, `amount_high` and the `amount` alias.
- **Action counts:**
  - Open: PENDING or APPLIED, not RESOLVED.
  - Window: `later_start <= k < later_end`, unresolved.
  - Verified: the surviving RESOLVED VERIFIED outcome, with `recorded_at` in `[k-30d, k]`.
  - The awaiting-verification SQL uses the exact origin pair, an open window and no surviving RESOLVED.
- **Refusals:** all nine codes and messages match the frozen table byte for byte, including the
  `{code, message, rows: null, total_count: null}` body and the 401 `WWW-Authenticate: Bearer` header. Unknown or
  repeated keys give `INVALID_CURSOR` (Run 5 ruling 4), and a bad state gives `INVALID_LENS` (Run 8 ruling 1).
- **Golden:**
  - The manifest is `/2`, sorted, with LF. All four branches are nonempty, and markers appear only at dynamic leaves.
  - Responses are compared whole. The token and access digests are rebuilt, and the cursor is decoded and paged.
  - The mixed branch runs in one DB with one tenant, and its counts and NOT_APPLICABLE rule are asserted.
  - Cold/EV golden branches carry zero Finding rows (q10 reading 2). Positive cold/EV rows are proven in the index
    tests.
- **EV cutoff test keeps the trigger:** it has no `session_replication_role` and no `UPDATE ingestion_disposition`.
  `w205b.LATE_DECISION` is monkeypatched (read at call time by `decision_clock()`), and `decided == late_at > k1` is
  asserted. The backdated-limitation test is kept separately.
- **Guard:** the `estate` domain, plus `$pgReaders` covering the reader, still applies the write refusal. The three
  probe tests pass.
- **Mount:** after the Site Action index; 503 without a DB.

## Items for the Architect

**q11 (an explicit earlier `known_at` plus a pre-cutoff open job gives a page-two 409):**
- Confirmed by code: `coverage.py:211-212` suppresses `open_jobs` on an explicit historical page one (job_state
  SETTLED/NONE) but evaluates it on the continuation (PENDING/FAILED). The token moves, so page two is 409.
- Option (a), "client restarts", does not work. A restart reproduces the 409 deterministically for as long as the job
  stays open. A FAILED job may stay open indefinitely, which makes that historical window unpageable.
- Recommend (b): record page one's live or historical mode in the cursor and evaluate page two with the same mode.
  That also fixes M1.
- Option (c) contradicts Run 8 ruling 6.

**Mixed-branch read clock after 2026-10-30:**
- `frozen = max(runner.now + 1 min, db_now)` (`test_w301_estate_golden_postgres.py:296`). `runner.now` after F03 is
  2026-10-30T10:02Z, so from about 2026-10-30T10:03Z the DB-clock branch is taken. That branch has never run.
- By analysis the KOBO literals should not move:
  - `committed_watermark` is `max(decided_at) <= k`, and the S4 decisions are fixture-clocked, so it stays
    `2026-10-30T10:00:00Z` as `k` grows.
  - S3 STALE is basis-driven, not age-driven.
  - The `_transaction_time` pin moves with `frozen`.
  - KOBO rows carry no priced consequence.
- Cold/EV values in the mixed cases are `$derive` or fixture literals.
- The larger date risk is elsewhere. The `mini_grid` branch and the `mini`/`power_estate` fixtures pin `read_at` to
  the fixture clock without the `max()`. Any DB-clock-stamped row compared with `k` would then fall after the read
  time once the real date passes 2026-10-30 to 11-02 (for example `evidence_publication.recorded_at`, which uses
  `clock_timestamp()`). I found no such comparison on the estate path, but that is unproven.
- Recommendation (not blocking): run the golden mixed and mini-grid branches once with the frozen clock forced 30 days
  later, as a test-only parameter, to prove invariance before the date arrives. Alternatively, the Architect accepts
  this as a dated residual risk.

## Readings classification

| Reading | Status |
| --- | --- |
| q8 1-11 | Covered by Run 8 rulings 1-11 (built as ruled). |
| q9 1-2 | Covered by Run 9 (structural golden `/2`; exact-origin honest zero). |
| q10 1 | Covered by Run 10 ruling 1. |
| q10 3 | Covered by Run 10 ruling 2. |
| q10 2 (replay paths map to chain stems; cold/EV golden branches have zero rows) | Implicitly accepted by ruling 1 ("keep the three replay-local branches") but never ruled. **Needs the Architect** to confirm that zero-row cold/EV golden branches satisfy the original "one cold/EV selected Finding" fixture intent. |
| q10 4 (`$public` from an estate reference read; token rebuild through the same snapshot methods) | Not ruled. **Needs the Architect** (see L4). |
| q11 Lane B 1 | **Needs the Architect.** Recommend (b), which also resolves M1. |
| Lane A "q11" 1 (UI DTO in commit 3) | Covered by Run 8 preamble and Run 6 commit-3 dry-read. |
| Lane A "q11" 2 (guard tests run explicitly, outside the container suite; a W3-02 `$pgReaders` path is pre-listed) | **Needs the Architect.** The guard self-tests have no CI home, and a W3-02 path is allow-listed in W3-01. |
| Lane A "q11" 3 (`main.py` mount) | Covered by q5 ruling 5 and Run 6 reading 3. |
| Lane A "q11" 4 (no dependency-direction allowance needed) | Covered by S22-S24; check-all passes. |
| Carried L2 (widened-job historical limit) | Covered (Run 6 reading 4 puts it in the packet). It still needs to appear in the commit-2 packet. |
| Mixed read-clock drift | **Needs an Architect decision**: accept as a dated residual risk, or require the forced-clock proof above. |
| M1 (mini-grid page-two fence) | **Needs the Architect** (a ruling gap beside q11). |
| L2 (cold row not bound to the selected assessment) | **Needs the Architect**: confirm the limitation or require the bind. |

## Addendum: architecture guard

`tools/check-architecture.ps1`: passed. `w301u_test` was dropped (exit 0). The working tree is clean apart from this
file.

## Re-review r1 (head 68723d0a, diff 1492532c..68723d0a excluding merges)

Reviewer: fresh Claude reviewer, 2026-10-20.

### Verdict: ACCEPT

Reading 1 below is a user-visible label choice for the Architect. It does not block, because it does not change the token, the rows or the gating.

### Checks run
- Private DB `w301w_test`, run once and then dropped. Files run: `test_w301_estate_coverage.py`, `test_w301_estate_api.py`, `test_w301_estate_index_postgres.py`, `test_w301_estate_golden_postgres.py` (this includes `test_w301_golden_clock_plus_30_days`), `test_w206_ev_store_postgres.py` and `tools/checks/test_estate_guard.py`.
- Result: 52 passed, 0 failed, 0 skipped, 1136.6 s.
- I did not rerun the full suite or the frontend suite. This diff has no frontend change.

### Items closed as ruled
- **M1 and q11-B 1:**
  - `page_one_mode` is a required key in both cursor key sets, validated as `live` or `historical`; a missing, extra or other value gives 422.
  - `basis_historical` is set from the cursor on continuation. Mini-grid gates, the cold/EV work fence and rows use `basis_historical`. The response label uses `snapshot.historical`.
  - The token fields and digest algorithm are unchanged.
  - The endpoint tests cover the live pending case, live STALE and PENDING S3 (each paired with a changed-status 409 control), historical PENDING/LEASED/FAILED, the historical outstanding marker, and the cursor shape and cutoff 409.
  - None of these tests is vacuous. The mini-grid tests assert page-one `PENDING_RECOMPUTE` or `STALE_SOURCE`, no mini-grid rows on either page, and the same token. Each has a control that flips a real stored status and expects 409.
- **Forced clock:** the +30-day test passed for `mini_grid` and `mixed`. The fixer's reading 5 (named step clocks used as request cutoffs stay unshifted; echoed read instants are unshifted before comparison) is mechanical.
- **L1:**
  - The catch-all is removed from `_bound_link_rows`.
  - `ColdPinnedLineageUnavailable` and `EvPinnedLineageUnavailable` are typed subclasses used only for the pinned-lineage failures.
  - `inconsistent=` now holds only the two typed subclasses plus `SelectionPinRefused`; the broad W2 unavailable classes go to the new `unavailable=` mapping and answer 503.
  - The three API tests run the real `PostgresEstateRead.read`, and each asserts a call count to prove the retry behaviour: 500 on the first call for a `TypeError`, 409 after exactly two calls for the typed errors, 503 after one call for the broad unavailable errors.
- **L2:** `_cold_window` now requires the revision's assessment to be in the window's selected set, and the L2 test asserts both sides of the selection.
- **L3:** the q11-A and q11-B names are recorded in the build-spec rulings, as ruled.
- **L4:**
  - `test_estate_injected_reads_share_one_connection` runs on the real DB, counts the estate connections, and refuses `_connect` and `create_engine` on the injected services.
  - The golden oracle limit is stated in the handoff.
- **q11-A 2:** the guard self-tests now run on an isolated temporary copy, the W3-02 reader path is removed from `$pgReaders`, and `check-all.ps1` has an explicit step that names the three tests.

### Classification of the five readings
1. **Needs the Architect.**
   - On a live page two the Site state label is HISTORICAL while gating stays live. A pending or stale Site that page one labelled `PENDING_RECOMPUTE` or `STALE_SOURCE` shows HISTORICAL on page two. Only the `state` field differs; the tests exclude `state` from the comparison and the rest of the coverage is identical.
   - The ruling says "still reports HISTORICAL" for the response, and also says Site coverage comes from page one's mode. Those two lines conflict for the Site `state` field.
   - The label hides an outstanding pending or stale condition from the user, so the Architect should rule which label applies.
   - It is consistent with how cold/EV already behave: `_windowed` labels HISTORICAL when `snapshot.historical` is true.
2. **Mechanical.** The STALE test sets the day status through a wrapper over `dispatch_days`. It is scoped to the test, as the ruling's "same stored day status" control allows, and a DONE job without a completion selection would make the day unavailable instead.
3. **Mechanical.** The L2 test re-dates a revision by one second with triggers disabled in the test transaction. The worker stamps the revision, the assessment and the selection with one transaction time, so a natural gap does not exist.
4. **Mechanical.** The historical changed-selection control uses a forged digest plus a grant change. It exercises both the digest fence and the access fence, and it meets the ruling's "changed selected revision or grant" control through the grant change.
5. **Mechanical.** The second inline `except Exception` near EV line 2497 (an EV inline link read) is outside L1's ruled scope, which names `_bound_link_rows`. It can be recorded as a Low carry.

### Low notes (not blocking)
- In the L2 test, `assert at_k["selection_token"] != before["selection_token"] or seen == old` has a vacuous disjunct. The preceding loop already asserts the `seen == old` part, so the line adds nothing.
- The limits carried are unchanged: the widened-job historical overlap (Run 6 reading 4) and the digest-canonicalizer-only golden.
