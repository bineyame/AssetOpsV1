# 3A1 review, round 1 (discovery, W5)

Reviewer: fresh Claude reviewer (did not author 3A1), 2026-11-20. Branch `task/3A1-commercial-record-store` at
`6c98cb590` (commits `f7b8b5bb3`, `f1acaf201`, `6c98cb590`; base main `8c9af447b`). Read: spec rev 2, rulings
D-3A1.1-12 and handshake round 1, reviewer guide rev 2, packet, P3A, the full diff, and 2a's `parse_batch`/`parse_record`.
Ran everything in scratch worktrees at `6c98cb590` (since removed); the author's worktree was not touched.

## Summary (round 1)

- **Verdict: ACCEPT with Lows.** No High or Medium finding.
- Migration 0063 is byte-identical to spec §2's SQL (scripted diff). There are four append-only triggers, and the
  downgrade refuses when rows exist. The composite foreign keys (R11) and the REFUSED-only NULL envelope CHECK (R1) hold.
- Every semantic in the brief has a test that passes and that failed when I planted a violation: 15 plants of my
  own (8 service, 7 Postgres) and 5 guard plants.
- Concurrency holds. My probes (three writers on one new record, three writers on three versions of one record, and
  the same record ID in two tenants) passed. Moving the re-read before the lock, or switching to REPEATABLE READ,
  broke both the author's lock proof and my probes.
- Lows: L1, the downgrade test does not prove the per-table refusal. L2, three unstated choices against a mid-build
  count of 0; the Architect should ratify them. L3, `main` was not merged before review. L4 is a preference: the
  provenance list is duplicated.
- At merge, the second of 3A1 and 3C1a must be renumbered to 0064. The text merge is clean, but it leaves two Alembic
  heads (see the merge section).

## Checks I ran (revision `6c98cb590`)

PYTHONPATH = scratch tree's `backend:backend/tests:contracts:simulator:gateway:field:host:tools`. Module paths:
`assetops_backend`, `assetops_contracts`, `assetops_simulator` and `fixtures.__path__[0]` all resolved under the scratch
tree.

| Check | Result |
|---|---|
| `pytest backend/tests/test_3a1_commercial_service.py` | 24 passed, 0.92 s |
| `heavy-slot.sh --db -- pytest test_3a1_commercial_postgres.py test_pg_harness.py test_up1_reading_upload_postgres.py test_3c0a_accounts_postgres.py` (routed `assetops_test` clones) | **52 passed**, 191 s; this matches the packet. The 3C0a downgrade crosses 0063 green |
| `heavy-slot.sh -- pytest tools/checks/test_estate_guard.py -n 4` | 17 passed, 176 s |
| `check-architecture.ps1` (`ASSETOPS_GUARD_PYTHON` = main venv) | passed |
| `check-agent-workflow.ps1` | passed |
| Reviewer probe file (5 tests: 3 writers on one new record, 3 writers on 3 versions, two tenants, downgrade with only a REFUSED intake, TRUNCATE) via `--db` | 5 passed |
| Harness databases left behind (`assetops_pt%`) | none |

Not rerun: check-all fast mode (the packet cites it at `f1acaf201`; guard and arch were rerun above) and the full
suite (merge tier).

## Plants (each reverted; every one failed as it should)

Service (no DB):
1. Running in-batch state removed (R9): `test_two_versions_of_one_record_in_one_batch` failed.
2. Provenance check removed (R12): the provenance test and the R13 test failed.
3. Envelope stage off by one (R1): the `bad-source-type` case and the after-refused-value test failed.
4. Ref appended to a refusal path (KIND_CHANGED, and separately SITE_UNKNOWN): 3 and 1 tests failed.
5. Dry run returning `intake_id`: the dry-run test failed.
6. Tenant check removed: the isolation test and the R13 test failed.
7. `supersedes_revision_id = None` on REVISED: 2 tests failed.
8. Digest comparison removed (conflict becomes UNCHANGED): the conflict test and the R13 test failed.
9. Whole batch in the `LookupError` text: the unknown-tenant test failed.

Postgres (`--db`):
- **PA** re-read before the lock: the author's lock proof failed (`StoreRefused(..._source_record_id_key)`), and so did
  my 3-writer and 3-version probes (`..._revision_no_key`).
- **PF** REPEATABLE READ instead of READ COMMITTED: the same three failed. This shows that R4's isolation level is
  load-bearing.
- **PD** `DISTINCT ON` picking the earliest revision: the month-move test and the two-stores test failed.
- **PE** `hide_parameters=False` plus `raise ... from error`: the no-value test failed. Its `__cause__` printed the
  failing row (`1800.00, usd, ... PAID`), which shows why the bare raise matters.
- **PB** rejection trigger removed: the schema test and the append-only test failed.
- **PC** downgrade checks only `commercial_rejection`: the downgrade test failed.
- **PC2** downgrade check without `commercial_intake`: **the author's downgrade test still passed** and only my probe
  failed (L1).

Guard (`check-architecture.ps1 -Only configuration-persistence.ps1`): the baseline passed. Each of these failed:
UPDATE in the writer, `ON CONFLICT DO NOTHING` on the rejection insert (also anti-vacuity), INSERT...SELECT,
DELETE, and an INSERT into `commercial_record` from `service.py` ("second product database writer" plus the
storage-above-adapter rule).

## Reviewer guide and brief, item by item

- **Scope.** The diff is the migration, `commercial/**`, two test files, the guard block, the packet, the spec status,
  the `specs/INDEX.md` row and the built-state entry. Nothing else.
- **Tests first.** This cannot be shown from the history: the code and its tests are one commit (`f7b8b5bb3`). The
  substantive property (each rule has a test that fails on a violation) holds, per the plants above.
- **Schema.** The append-only triggers fire on UPDATE and DELETE for all four tables (tested; PB). They do not fire on
  TRUNCATE (my probe; the author's downgrade test uses TRUNCATE itself) or under trigger disabling by the owner role.
  That is the estate's 0005 precedent and the guard bans TRUNCATE in code, so it is residual, not a finding.
  `batch_sha256` is `sha256(data)` before parsing (`service.py:204`) and is asserted for all four envelope stages.
  No column holds the bytes.
- **Semantics.** All verified by rerun and plants:
  - R8: a repeated file adds 1 intake row and nothing else.
  - REVISED supersedes the previous latest revision.
  - INTAKE_VERSION_CONFLICT and INTAKE_PROVENANCE_CHANGED (R12).
  - R9 in input order.
  - R7 latest-then-filter, in both stores.
  - `intake()` returns an `IntakeSummary`, and only `ingest` returns outcomes (R6).
  - Tenant isolation: mismatched `tenant_code`, another tenant's Site, and my two-tenant probe (no cross-blocking,
    distinct records, no cross-read).
  - DS1b: 142 NEW, then 142 UNCHANGED, 0 rejections.
- **Personal data.**
  - `commercial/**` has no logging (grep test).
  - `StoreRefused` carries only the constraint name, with no cause or context (`adapter:185-192`, PE).
  - Stored refs are `to_canonical_json` of 2a's parse, with no enrichment.
  - The store never changes provenance: it stores the batch's declared value per revision. "Emulated" and "Recorded"
    labels are 3A5's, so nothing in 3A1 renders a label, and nothing says "accepted" (R17 is in the docstrings).
- **2a contract fit.** I checked 2a's bounds against every CHECK: `source_version` ≤64, refs ≤200, the site rule (only
  BUDGET_LINE and CONTRACT_DOCUMENT may omit `site_code`), units, currency, the period pattern,
  `effective_to > effective_from`, and finite decimals. A 2a-valid record cannot hit a CHECK, so `StoreRefused` is
  reachable only through a bug.

## Findings

**L1 (Low, test gap). The downgrade refusal is not proven per table.**
- Where: `backend/tests/test_3a1_commercial_postgres.py:417-425`.
- What is wrong: the test writes rows into intake, record and revision together, so removing any one table from
  `REFUSE_IF_USED` (`0063_commercial_records.py:130-137`) goes unnoticed. Plant PC2 proved it: the test passed with
  `commercial_intake` dropped from the check. A database holding only REFUSED intakes would then be downgraded,
  destroying the stored account.
- Why it matters: R14.
- Fix: add a case with only a REFUSED intake row (`ingest(world, b"not json")`, then expect the refusal), or one case
  per table. My probe `test_downgrade_refused_with_only_a_refused_intake` is a ready shape.
- Class sweep: the same class applies to 0061 and 0062, which are not in scope; the Architect may note it.

**L2 (Low, process / Architect ruling). Three implementer choices the spec did not fix, with a mid-build count of 0.**
RULES §7 says "an implementer choice the spec did not fix is a spec defect: raise it, don't decide it." The packet
names all three, which is honest, but the mid-build count should be 3. Each choice is sound. I recommend the Architect
ratify each one in `rulings.md`:
- (a) `ExistingRecord.provenances` (`model.py:122-132`). This was forced: R12 cannot be decided without each stored
  version's provenance, and spec §4.1's field list has no slot for it. It changes the store port, so it **should have
  been a mid-build question**. Ratify as is.
- (b) `StoreRefused(constraint)` (`model.py:151-157`, `adapter:185-192`). This is a new public error that 3A2 must
  map; it should probably be a 500, since it is reachable only through a bug. It **should have been a mid-build
  question**: it adds an error surface, and the spec only said `IntakeRefused` is not used. Only `IntegrityError` is
  scrubbed. Other `DBAPIError`s (DataError, OperationalError) pass through with the driver's text, with parameters
  hidden. 2a pre-validation makes a value-bearing DataError unreachable today, so this is residual. The ruling should
  say whether 3A2 treats every `DBAPIError` the same way.
- (c) `revision_no=None` for UNCHANGED (`service.py:168`). This matches the docstring ("the revision this intake
  wrote"), and the spec's §6 R8 "writes nothing" supports it. 3A2's copy may want the matched revision number. That is
  a 3A2 question; ratify by note only.

**L3 (Low, bookkeeping). `main` was not merged before review (spec §0 "merge `main` before review").**
- What is wrong: `git merge-tree main 6c98cb590` conflicts in `.ai/state/data.md`, `.ai/state/index-2.md` (line 147
  is also claimed by 3B1) and `specs/INDEX.md`. Code and guard merge cleanly.
- Fix: merge `main`, renumber the index line, and rerun the guard. Mechanical.

**L4 (Low, preference). `service.py:44-45` re-declares the provenance set.**
- What: 2a exports `PROVENANCES` (`records_v1.py:39`).
- Fix: import it. The DB CHECK would still need a migration on change, so this only removes one of three copies.
  Not blocking.

## Migration renumbering at merge (D-3A1.12)

`task/3C1a-person-on-work` adds `0063_person_on_work` with `down_revision = "0062_operator_accounts"`, the same parent
as `0063_commercial_records`. A text merge of the two is **clean**, which is the danger: it yields two Alembic heads,
and `upgrade head` and `pg_harness.alembic_head()` break.

For whichever slice merges second:
1. Rename the file to `0064_<name>.py`.
2. Set `revision = "0064_<name>"` and `down_revision` = the first slice's revision.
3. Update the docstring's `Revision ID`/`Revises` lines and its numbering note.
4. If it is 3A1: update the comment "migration 0063" in `tools/checks/configuration-persistence.ps1:967-969` and the
   `0063` mentions in `commercial/model.py` and the adapter docstrings (cosmetic).

Neither slice's tests hard-code a revision name (grep checked; 3A1 finds its migration by `TABLES`). After the
renumber, run these on the merged tree:
- the 3A1 Postgres file, the 3C1a Postgres file, `test_3c0a_accounts_postgres.py` (its downgrade then crosses both)
  and `test_pg_harness.py`;
- a single-head check (`alembic heads` shows one);
- the merge's full tier (`select-tests` gives full because of the migration).

## Residual risk the packet does not name

- **Append-only gaps.** TRUNCATE, and trigger disabling by the owner role, bypass the append-only triggers. This is
  estate-wide (0005); a statement-level `BEFORE TRUNCATE` trigger is a possible later estate item.
- **Invariants not enforced by the schema** (spec SQL, ruled):
  - no `UNIQUE (supersedes_revision_id)`, so a forked chain is refused only by the lock;
  - a REFUSED intake's zero counts;
  - "no revision on a REFUSED intake" (R2);
  - revision and record `site_id` agreement (R11).

  Each is covered by a test, not by a constraint. Fine while this adapter is the sole writer; DS3's bulk loader
  must keep them.
- **Provenance can change across versions.** A *new* version under a different provenance is REVISED, not refused, so
  a record's latest evidence word can change, up or down. This is correct per D-3A1.9 only once 3A2 caps
  provenance by path. Until then, any caller of `ingest` can declare `observed-financial`.
- **Reads outside the lock.** `site_ids` and `tenant_slug` are read before the lock. This is harmless while Sites are
  never deleted or re-coded.
