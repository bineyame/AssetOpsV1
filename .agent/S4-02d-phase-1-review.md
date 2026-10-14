# S4-02d phase 1 review (bounded orchestration and storage)

Reviewer: fresh Claude reviewer (did not author the slice), 2026-10-14. Branch
`task/S4-02d-analytic-finding-worker-schedule`, diff `dc5afad5..4c298b88` (7851b4da, 68109a9d, 98cd5d6d, 51801480,
4c298b88). Judged against the packet phase-1 row, contract items 1-3, fix rounds 1-2 and carries N2-N5,
`D-2026-10-14-s402d-schedule-storage-and-install-gate` and `.agent/architect-S4-02d-answers.md`.

## Verdict

**ACCEPT with carries.** F1 (guard robustness) and F2 (missing Site back-off proof) should be fixed on the branch in
a small fix round before phase 2 starts; F3 is a low-severity hardening that can ride along. None of them is a
runtime defect in the code as written. Storage, writer ownership, tick ordering, conditional S4, claims, timeouts,
typed outcomes and requeue match the ruling and the packet.

## Findings

### F1 - Medium - rule 8 schedule-writer line rules are case-sensitive and parse the SET list loosely (acceptance gap against the ruling's reverse ownership)

`tools/checks/configuration-persistence.ps1:778`, `:781-782`, `:785-786`. The schedule-specific checks use
`-cmatch` (case-sensitive) for `DELETE|TRUNCATE|...`, `INSERT` and `UPDATE`, and the generic `$sqlWrite` branch has
no case-insensitive "schedule writer writes only its four tables" rule (unlike the Finding/consequence/assumption
writers, whose "only inserts into own tables" rules are `(?i)` and run on every write line). I added each line
below to `postgres_schedule_store.py` in a `git archive` scratch copy and ran `tools/check-architecture.ps1`:

| Injected line in the schedule writer | Result |
| --- | --- |
| `"update site set lifecycle = :l where tenant_id = :t and id = :s"` | passed (missed) |
| `"insert into site_import (tenant_id, site_id) values (:t, :s)"` | passed (missed) |
| `"delete from schedule_cursor where environment = :e"` | passed (missed) |
| `"update schedule_site_head set created_at = now() where tenant_id = :t"` | passed (missed) |
| `"UPDATE schedule_site_head SET (tenant_id, site_id) = (:t, :s) WHERE tenant_id = :t"` | passed (missed) |
| `"UPDATE schedule_site_head SET " + _COLS + " WHERE tenant_id = :t"` | passed (missed) |
| `"UPDATE schedule_site_head SET CREATED_AT = now() WHERE tenant_id = :t"` | passed (missed) |
| control: `"UPDATE schedule_site_head SET created_at = now() WHERE tenant_id = :t"` | failed, named column (caught) |

Why it matters: the ruling says the schedule adapter "may write no other product table" (Foundation Site rows named
explicitly) and forbids DELETE; lowercase SQL is an ordinary, accidental way to write that, not a contrived
evasion, and the guard is the only enforcement. The implementer's probe set only tried uppercase forms, so it
reported 12/12.

Fix: (a) inside the `$sqlWrite` branch add a case-insensitive rule `if ($module.Path -eq $scheduleWriter -and
($null -eq $target -or $scheduleTables -notcontains $target))` -> failure, plus a case-insensitive refusal of
`DELETE FROM|TRUNCATE|DO UPDATE` there; (b) make the column parse case-insensitive (`(?i)` on the UPDATE/SET
regex, lowercase the column before lookup) and require the SET list to be a comma-separated sequence of
`identifier = expression` items, failing on `(`-tuple targets, quoted identifiers, `+`/`%`/`format` concatenation
or a nested `WHERE` inside the SET list (or simply: fail when the SET list contains `"`, `+`, `%` or starts with
`(`). Docstring prose with lowercase "update" is why `-cmatch` was chosen; restrict the line rules to lines that
match `$sqlWrite` (already case-insensitive) rather than to any line containing the keyword. Add the rows above
to `.agent/S4-02d-phase-1-probes.py guard`.

### F2 - Low/Medium - Site-level schedule back-off (`RETRY_DUE` per Site) has no proof (missing test)

`backend/assetops_backend/scheduling/tick.py:235-236`. Mutation `if head and head["retry_due_at"] ... :` -> `if
False:` left all 7 tests in `test_s4_schedule_tick_postgres.py` passing (scratch copy, DB
`assetops_s402drev1_test`). Packet item 2 requires schedule-level stage failures to get retry/back-off; only the
tick-level back-off is asserted (`RETRY_DUE` after the discovery lock timeout). Fix: after the S3 `TIMEOUT` in
`TestKillableStagesAndServerTimeouts` (or with a non-zero `backoff_base_seconds` elsewhere), tick again before the
Site's `retry_due_at` and assert the Site result is `RETRY_DUE`, no stage ran for it, and the cursor still advanced.

### F3 - Low - a lost Site claim does not stop the remaining stages

`tick.py:270`, `:278`, `:289` ignore the boolean from `set_stage`/`record_*`. If the Site claim lease
(`site_lease_seconds` = stage bounds + 60 s) expires because store calls between stages overrun (each may take up
to the 30 s statement timeout), another host can claim the Site and run S3 while this host proceeds to S4, which
is the overlap item 2 forbids. Unlikely with the default bounds and the matcher fence still protects Finding
writes, so this is hardening: when `set_stage` returns False, stop the Site, report `CLAIM_LOST` and run no
further stage. The tick-level equivalent (`finish_tick` -> `CLAIM_LOST`) is already handled.

### Observations (no change requested)

- The deterministic matcher defect is detected by substring (`"not accepted" in str(moved)`, `stages.py:122`),
  coupled to the message at `postgres_finding_store.py:173`. Acceptable for N3 (the streak also covers
  `FENCE_MOVED`); a dedicated subclass of `FindingFenceMoved` would be sturdier if the Finding store is next touched.
- `claim_tick` stamps `last_started_at` also for a tick that then returns `RETRY_DUE`; phase-2 health text should
  not read it as "a tick ran".
- A Site that leaves the active set (e.g. DECOMMISSIONED) with an unmatched new selection but no live S3 job and no
  pending consequence work is dropped silently. Within the packet's wording (only live S3 / pending consequence work
  keeps a Site), but the phase-2 report should derive S4 backlog per Site including non-selected Sites.
- `requeue` without `--job-id` raises a traceback rather than a usage error (`assess_dispatch.py`, `UUID(None)`);
  cosmetic.

## Ruled items from the focus list

- **Migration 0013 vs ruling:** exactly the four tables, one row per environment/Site, claim-shape CHECKs, FKs to
  `site(tenant_id, id)` (cross-tenant enrolment refused, proven), no trigger, downgrade drops only the four. Matches.
- **Eighth writer:** only INSERT ... ON CONFLICT DO NOTHING into the four tables and token-guarded UPDATEs of the
  named columns; no DELETE/TRUNCATE/DDL/upsert; all instants `clock_timestamp()`. Guard lists columns per table
  matching the ruling's categories; writer allowlist, non-vacuity, adapter-isolation domain `scheduling`, and
  reverse ownership against other modules are present and caught by the implementer's probes. The one-line UPDATE
  constraint holds for the code as written but is easy to evade (F1).
- **Existing seven writers:** their rule blocks are unchanged; the S3 writer gained a scoped `lease_job` (both the
  expire-to-FAILED and the lease UPDATE scoped identically; with no Site the SQL string is byte-identical to before,
  so global callers are unaffected) and two reads; the consequence writer gained one read; `finding_service` only
  returns the fence it applied under.
- **Active-Site rule:** imported (`site_import` exists), lifecycle not DECOMMISSIONED/ARCHIVED, any
  `accepted_evidence` row or enrolment; PLANNED KOBO-001 selected; gateway-only Site excluded (N4); live S3 or
  pending consequence work keeps an excluded Site, reported as `EXCLUDED_WITH_WORK`. Proven.
- **Fairness cursor:** durable, (tenant, site) order, wrap-around; mutation `fair_order(selected, None)` caught.
- **Conditional S4 / H1:** skip only when stored `matched_version == MATCHER_VERSION` and the stored fence equals
  the current `_fence`. A new selection raises `max(seq)`, so it always moves the fence; the completed fence is the
  applied fence plus the pass's own revisions, so a concurrent change after the read is never absorbed. Idle ticks
  append no pass; a new selection appends exactly one; day-B FAILED window unchanged and not CURRENT while day A
  advances. Proven, and the implementer's "S4 always runs" probe is caught.
- **Claims/expiry on DB time:** both claims taken on `claim_token IS NULL OR lease_until < clock_timestamp()`;
  every later write names the token; crashed holder writes nothing after takeover. Proven (concurrent ticks, held
  Site claim, crash/replay); my mutation removing the tick-claim guard was caught.
- **Killable children and PGOPTIONS:** each stage is a `subprocess.run(timeout=)` child with `PGOPTIONS`
  statement/lock timeouts; `TickLimits` enforces S3 bound < 300 s lease and statement timeout < every stage bound.
  Hung S3 killed with job LEASED ~5 min; server-side lock timeout in S4 and discovery typed `TIMEOUT`. Proven.
- **Typed outcomes:** `FENCE_MOVED` grows `fence_moved_streak`; `MATCH_EVIDENCE_NOT_ACCEPTED` is a Site failure
  without streak growth; MATCHED resets. Proven; my mutation `deterministic = False` caught.
- **Requeue:** only a live FAILED dispatch job of that tenant/Site; foreign Site, DONE and superseded refused (exit
  2); UUID tenants, no demo restriction; re-enqueues the exact window via `enqueue`. My mutation dropping the
  `live` check was caught.
- **No timer, no owner copy:** no scheduler/timer code, no `backend/README-db.md`, frontend or host change.

## Questions Q1-Q5

- **Q1 (heartbeat on a tick with Site failures): acceptable, with a binding phase-2 carry; include in the
  Architect batch as a confirmation, not a blocker.** A completed tick advancing the environment heartbeat while
  Site failures/skips stay on the Site head is the right split (otherwise one bad Site marks every Site STOPPED),
  and the failure path does not set `last_completed_at`, so Site staleness is observable. But the packet sentence
  "claimed/skipped, failed and timed-out ticks do not" is being read at tick level only. For the S5 seam this means:
  CURRENT eligibility for a window must require both a healthy environment heartbeat **and** a healthy Site head
  (`last_completed_at` within the stop threshold in DB time, no Site claim older than its lease, and
  `consecutive_failures`/`claim_skips`/`fence_moved_streak` under their alarm thresholds). A seam reading the tick
  heartbeat alone would let a permanently skipped or failing Site with empty queues read as observed.
- **Q2 (later stages after an earlier failure): acceptable.** S4 leaves non-CURRENT windows unchanged and the drain
  is independent; the extra stage time is bounded by the stage bounds inside the Site lease. See F3 for the
  lost-claim case.
- **Q3 (`CONSEQUENCE_CLAIMED` as a Site failure with back-off): acceptable.** It alarms rather than passing
  silently; phase 2 retires the per-Site timer and should name this code in the runbook.
- **Q4 (clocks): acceptable for phase 1; phase-2 carry (I3).** Schedule claims/retry/heartbeat are DB time and the
  scheduled drain already receives DB `now`; the S3 lease/cutoff and matcher `now` stay app clock. Phase 2's skew
  proof must cover them or state the residual explicitly; I3 stays open.
- **Q5 (one-off CLIs bypass the Site claim): acceptable with a runbook carry.** The matcher fence protects Finding
  writes and S3 leases are row-level; phase 2's runbook must say to stop the tick (or verify no Site claim is held)
  before a manual `process-jobs`/`match-findings`/consequence `run`. Optional hardening: have those CLIs report a
  held schedule Site claim.

## Checks as observed

- Full backend suite, DB `assetops_s402drev1_full_test` (on HEAD 4c298b88): **2097 passed**, 40 warnings,
  34 min 05 s. This confirms the head-pin fix the packet had only re-run in three classes.
- Focused suites, DB `assetops_s402drev1_test`: `test_s4_schedule_tick_postgres.py`,
  `test_s3_dispatch_assessment_postgres.py`, `test_s4_evidence_consequence_work_postgres.py`,
  `test_s4_consequence_recompute_postgres.py`: **42 passed** in 5 min 22 s.
- `tools/check-all.ps1`: **All 9 guards passed** (architecture, navigation, agent workflow, registry, delivery
  fixtures, mock-gap fixtures, missing-claim scan and fixtures, screen ledger).
- My mutation probes (scratch `git archive` copy, `PYTHONPATH` pointed at the copy): 6/7 caught - heartbeat on
  failed tick, cursor ignored, requeue accepts superseded, deterministic defect untyped, tick claim ignores holder,
  enrolment ignored; **missed: Site back-off ignored** (F2). Guard evasion probes: 7/7 missed, control caught (F1).
- Frontend: no frontend change in the diff; `npm.cmd test`, build and `tsc` not run (not applicable). Layout
  evidence not applicable (no UI).
- Scratch DBs dropped.

## Not verified / residual risk

- **I4 (two overlapping ingestion chunks against an active tick)** was not attempted in this phase review; it needs
  the phase-2 S5 seam to assert "no falsely CURRENT selected window". It remains open and belongs to the phase-2 or
  final independent review, as the packet requires.
- Tick cost per Site on Windows (~3 child starts of ~1-2 s each) and global `reconcile_all()` growth are measured
  only on a one-Site scratch DB; cadence/`max_sites` must be chosen from a demo-host measurement in phase 2.
- `pending_work_sites()` counts attempts with a correlated subquery over all dirty work each tick; fine now, grows
  with I1's uncapped attempts.

## Carries for phase 2

1. Fix F1 and F2 on the branch (F3 optional) before phase 2 builds on the guard and back-off.
2. S5 seam: Site-level health in addition to tick heartbeat (Q1 ruling above), in DB time.
3. I3 skew proof including S3 lease/cutoff and matcher `now`, or an explicit residual (Q4).
4. Runbook: stop-the-tick before manual Leg B commands (Q5); `CONSEQUENCE_CLAIMED` meaning and per-Site timer
   retirement (Q3); `last_started_at` semantics.
5. S4 backlog in the report for Sites that left the active set with an unmatched selection.
6. I4 race proof at the phase-2/final independent review.
