# W3-01 commit-2 Lane A prerequisite: independent review

Reviewed: code commit `a75b0291` (handoff `04b00a25`), branch `task/W3-01-estate-claim-action-roots`, worktree
`AssetOpsV1-review2`. Authority: W3-01 build spec "Run 5 rulings (q5)" (signature table, rulings 1-3, readings 4-9),
the W3-02 "Run 5 dependency amendment", and handoff readings R1-R8. Reviewer did not author or edit the slice.

## Verdict: REVISE

One Medium finding (M1): the day selector reports an available-to-reconstruct job state as "unavailable".
Everything else conforms: signatures, no transaction ownership, the cutoff filters, byte-identical wrappers, the
guard allowance, and non-vacuous tests. M1 is a small change inside `_dispatch_day_on` plus one test assertion.

## Findings

### M1 (Medium, acceptance gap against ruling 1): DONE jobs whose completion is on record are reported unavailable
`backend/assetops_backend/analytics/adapters/postgres_assessment_store.py:723-735` (`_dispatch_day_on`, historical
branch). Below the transaction time, a job that is `DONE` now counts as finished only if one of its selections has
`selected_at <= k`; otherwise the whole day becomes `available=False` / `JOB_STATE_AT_CUTOFF_UNKNOWN`.

The stored records do settle the other case. `complete_job` (same file, lines 352-360) writes every selection for
the job (`_persist` -> `_select(..., job_id, now)`) and sets `status='DONE'` in **one** transaction with one `now`.
`DONE` is terminal: no `UPDATE recompute_job` path leaves `DONE` (lines 328, 333, 356, 368, 405, 923;
`postgres_evidence_ledger.py:671` only widens PENDING). So for a DONE job with any selection, `min(selected_at)` is
its completion instant on the same clock basis that ruling R6 already accepts. A DONE job created by `k` whose
selections are all after `k` was therefore **outstanding** at `k`, not unknown. Only a DONE job with **no**
selection (every window EMPTY) is truly unrecoverable.

Ruling 1 says to return the unavailable day only "if the stored records cannot reconstruct a consistent as-of day".
Here they can. The test locks the over-conservative behaviour: `test_dispatch_days_on_selects_each_day_at_cutoff`
asserts `early[1]` is unavailable, but at `queued` the day's job was provably pending.

Why it matters: a cutoff that falls while a job is in flight is the common shape of the q5 late-change story. Ruling 2
turns every unavailable day into Site `UNKNOWN` with null totals. Lane B's
`test_late_support_change_recurrence_at_exact_cutoff` can land on this if its later job is created before the
cutoff and completes after it.

Fix:
- DONE job with a selection: completed at `min(selected_at)`. Finished if that is `<= k`, outstanding if it is
  `> k` (report it as outstanding; do not invent a PENDING/LEASED split).
- DONE job without a selection: stays unavailable.
- Update the `early` assertion to the reconstructed state (no selection, `status=PENDING`, the job outstanding).
- Keep one unavailable-day case in the test, for example a DONE job with no selection, so the explicit-unavailable
  path is still proven.

FAILED is only partly recoverable. `fail_job` stores the failure instant in `available_at`, but lease-expiry
`FAILED` (line 328) does not. So `available_at > k` proves outstanding, and `available_at <= k` stays unavailable.
Adopting this is optional and not required for M1.

### L1 (Low, reading for the Architect): the selector's historical job semantics differ from cold/EV M3.2
The selector counts a job that is PENDING/LEASED now and was created by `k` as outstanding at `k`. That inference is
sound: those states cannot follow a terminal state. But the M3.2 ruling (build spec line 325) says, for cold/EV
historical reads, that "a presently open job cannot truthfully be reconstructed as historical pending ... do not show
it". The mini-grid day therefore carries pending reasons at a historical cutoff where cold/EV carry none.

Ruling 2's precedence makes the estate status `HISTORICAL` either way, so the wire label does not change. The
`status`/`status_reasons` handed to Lane B do differ by domain, and the Architect should confirm that this is
intended. Separately, the day's `jobs[].status` shows the job's **present** status (for example `LEASED`), not its
status at `k`. Either document that or replace it with an "outstanding at cutoff" marker.

### L2 (Low, disclosed limit): a job widened after `k` can appear to overlap at `k`
`_enqueue` and the evidence ledger widen a PENDING job's window in place. A job created before `k` and widened after
it is reported as outstanding for days it did not cover at `k`. That gives a pending status, not an unavailable
day. The handoff (R5) discloses this, and it lasts only while the job stays PENDING. Record it as residual risk;
no change is needed for this commit.

### L3 (Low, R1 timing): `$pgReaders` landed earlier than ruling 3 places it
Ruling 3 puts "this guard/domain change", meaning both the `$pgReaders`/`$isPgReader` allowance and the `estate`
`$domains` entry, in Lane A's **second** handoff. The builder followed the dispatch and landed the allowance now,
deferring only the domain entry and the three guard tests.

The allowance is exactly the ruled text: the line sits right after `$pgWriters`, `$isWriter` is kept, the refusal
is `elseif (-not $isPgReader)`, and readers are never added to `$pgWriters`, `$pgWritesSeen` or `$pgDriverSeen`.
It is inert until the files exist. Per-statement write refusal (`if (-not $isWriter)`, line 879) still applies to
readers. It also fails safe: if Lane B names the files differently, the driver import is still refused. The
deferral of the domain entry and of `test_pg_reader_import_allowed`, `test_pg_reader_write_rejected` and
`test_domain_driver_import_rejected` follows ruling 3 exactly.

The deviation is harmless. Ask the Architect to confirm the split in the next batched question, and make the
second handoff carry the three guard tests and the `estate` domain entry before commit-2 review.

## Contract check (signature table, rulings 1-3)
- `fence_on`, `index_snapshot_on`, `index_lineage_on`, `select_dispatch_days_on`, `site_window_on`: signatures
  match the table exactly. None of them calls `_read`, `_snapshot`, `_run`, `begin` or `commit`. All helpers they
  reach (`_fence`, `_index_*`, `_window`, `_configuration`, `_attestations`, `_run_detail`, `_site_window`) are
  connection-taking. The test asserts `c.in_transaction()` after every helper.
- Finding cutoff: `r.created_at <= k` selects the head (ordered by `revision_no DESC`). The `merged_into` subquery
  and `merges` are filtered by `finding_merge.created_at`, selections by `selected_at`, and the match pass by
  `completed_at`, so deferred windows come from that pass. There is no fence in the `_on` output.
  `index_lineage_on` refuses missing or later pins before reading.
- Day selector: it uses `EvidenceQuery(..., knowledge_at=known_at)`, so evidence and configuration
  (`_configuration`, `_KNOWN`) and attestations are read at `k`. `_window` filters the selection, assessment key
  heads and jobs at `k`, and the selected run's `completed_at` and revision `created_at` are checked. One entry is
  returned per intersecting UTC day; unselected days are explicit (`selection=None`). There is no `OPEN_CUTOFF`, no
  window-wide maximum and no independent `_snapshot`. `derive_status` does not consult `read_at`. The issue is M1.
- Actions: `a.created_at` is in `[start,end)` and `<= k`, `e.recorded_at <= k`, ordered by `(recorded_at,id)`.
  `occurred_at` is not used for selection.

## Wrapper output byte-identity (checked by reading SQL text with `known_at=None` / `cutoff=None`)
- `index_snapshot`: each SQL string is identical once the empty `by()` fragments are removed. `selection_seqs` comes
  from `DISTINCT ON (window_start) ... seq DESC`, which gives the same values as the former `max(seq) GROUP BY`. The
  dict keys and their order (`heads, merges, selection_seqs, match_pass, deferred_windows, fence`) are unchanged
  after `del snap["selected_runs"]`.
- `index_lineage`: the same three queries, moved verbatim.
- `site_window`: identical SQL with empty `created`/`recorded` fragments and the same `{"actions","events"}` shape.
- `_window` defaults (`cutoff=None, all_jobs=False`): identical SQL, still `_LIVE_JOBS`. The only change in any of
  these is an extra unused bind key `k`.

## Tests (non-vacuity)
- Finding test: the later revision, merge, match pass and selection seq are asserted to exist in the live read
  before the cutoff read is asserted to exclude them. Lineage equals the W1 wrapper for pins made before the
  cutoff, a later pin and a missing pin both refuse, and the wrapper keeps its fence and drops `selected_runs`.
- Day test: it asserts two selections, one on each side of the cutoff, and that the cutoff day keeps the first. The
  two neighbouring days are explicit UNASSESSED entries, the live day equals `DispatchReadService.window`, and
  `from_ >= to` returns `[]`.
- Action test: an event that occurred before the cutoff but was recorded after it is excluded, which proves
  `recorded_at` is the selection time rather than `occurred_at`.
- `monkeypatch` pins `PostgresAssessmentStore._transaction_time` on the class to the fixture's `present`. That is
  legitimate: without it the live/historical branch would depend on the wall-clock date relative to the fixture
  clock (2026-10-30), and the test would change behaviour as real time passes. Residual effect: the real
  `SELECT now()` comparison is never exercised by a test. This is Low and needs no change, but Lane B's default
  `known_at` must be `>=` the transaction's `now()` (for example `now()` itself) to get the live branch on current
  reads.
- The builder's mutation claims (dropping each of the three cutoffs makes a test fail) were not re-executed.

## Readings R1-R8
| Reading | Classification |
| --- | --- |
| R1 `$pgReaders` now, domain and guard tests deferred | Domain and test deferral: covered by ruling 3. Landing the allowance early contradicts ruling 3's timing but is harmless. **Architect to confirm** (L3). |
| R2 `index_snapshot_on` shape (`known_at`, `selected_runs`, no fence) | Covered by ruling 1 ("returns the selected IDs and match/deferred state"; fence is `fence_on`). |
| R3 `FindingPinRefused(LookupError)` before reading | Covered by ruling 1 ("refuses a later/missing pin"). The exception type is an implementation choice. |
| R4 day dict keys | Covered by ruling 1's field list and ruling 2 (unavailable means null fields, labelled by the estate layer). |
| R5 job state below the transaction time | **Needs a fix (M1) and Architect confirmation (L1, L2).** The fallback to explicit unavailable is covered by ruling 1, but the claim that "no stored record shows its state" is false for DONE jobs with a selection, and partly false for FAILED. |
| R6 `selected_at` as worker lease-time clock | Covered: ruling 1 says to filter selection timestamps at the cutoff, and `CUTOFF_LABEL` is existing W1 semantics. |
| R7 `monkeypatch` of `_transaction_time` | Covered. It is a test technique and has no contract impact (see Tests). |
| R8 adapter imports `assessment_worker` and `dispatch_read` | Covered by ruling 1 ("use the existing S3 selector"). `check-architecture` passes and there is no import cycle. |

## Checks run by the reviewer
- `tools/check-architecture.ps1`: **passed**.
- `tools/check-agent-workflow.ps1`: **passed**.
- Private DB `w301j_test` (created, then dropped with `--force`), serial runs:
  - `tests/test_w301_w1_snapshot_helpers_postgres.py`: **3 passed** (28.6 s).
  - Touched-store regressions: `test_s4_finding_index_postgres`, `test_s4_finding_store_postgres`,
    `test_s3_dispatch_assessment_postgres`, `test_s3_dispatch_read_postgres`, `test_s3_claim_limit_postgres`,
    `test_s6_action_store_postgres`, `test_s6_site_action_index_postgres`, `test_s6_site_action_index`:
    **85 passed** (475 s; matches the builder's 85).
- Not run: the full backend suite, the frontend (no frontend change), and `check-all` (I cite the builder's 10/10
  on `a75b0291`, which is the revision under review).

## Residual risk not named in the packet
- M1 can make Lane B's exact-cutoff proof report Site `UNKNOWN` if its later job straddles the cutoff.
- A DONE job with every window EMPTY makes its days unavailable at **every** historical cutoff after the job's
  creation, permanently, because there is no record to recover from. This is honest, but it is a permanent gap.
- `select_dispatch_days_on` calls `from_.astimezone(timezone.utc)`. A naive `from_` would be read as local time.
  The estate parser is expected to reject that first (`INVALID_WINDOW`).
