# DS3 review

## Round 1 (discovery, W5): fresh Claude reviewer, 2026-11-21, head `0cf1dbb5c`

**Summary (verdict: ACCEPT WITH FIXES: one Medium, fix on the branch, then a verification re-review of F1)**

- Safety: `permitted_database` held against about 45 adversarial URLs of my own. Variants of case, suffix, deny and
  operator names, query keys (`host`, `hostaddr`, `port`, `service`, `options`, `dbname`), multi-host, socket host,
  IPv6, `LOCALHOST`, wrong port and `PG*` env all refuse. No way through to a non-permitted database was found.
- One writer: the set-based admission is a method of the ledger adapter. The guard passes unchanged (exit 0 with
  `ASSETOPS_GUARD_PYTHON`, no diff under `tools/`). `a7f7e7547` only moves types onto the port and composes through
  `composition.py`; nothing goes around the writer.
- Parity: at head, the census, the v4 slice of three shapes and the `event_outbox` cover pass. My own plant R1 (bulk
  dispatch job one hour longer) is caught only by the D-DS3.21 cover, so that rule really fails.
- Plants on the final head: 23 of 24 fail their named test. **P21 survives (F1, Medium)**: test 1's host and port cases
  became vacuous when D-DS3.22 narrowed the name rule.
- The 11 pre-existing failures are identical on `main` `04da33fac` and at head, per my own run. No clone was left.
- Low: F2 to F6 (stale packet and state text, a duplicate state-index number, the cover limit not stated, the cover
  ignoring unknown keys, harness drop guard). None blocks.

### Findings

**F1 Medium (acceptance gap: spec §7 item 8, reviewer guide P21, D-DS3.12).** `backend/tests/test_ds3_bulk_load.py:40-42`.
The host, port and missing-port cases use `assetops_test`, and D-DS3.22 now refuses that name on its own. They are false
whatever the host and port rule does. Plant P21 (remove `target.host in _LOCAL_HOSTS and target.port == port`) gives
`18 passed`. The only true case on a non-default port (`55433` with `ASSETOPS_PG_PORT`) does not catch it either. The
host and port check is D-DS3.12's gate against the right name on the wrong server, so today no test protects it. The
packet's P21 result predates D-DS3.22. **Fix:** use a permitted name in those three cases (for example
`assetops_ds3_audit1121` on `10.0.0.5:55432`, on `127.0.0.1:5432` and with no port, each false). Add one true case on
`localhost:55432`. Show P21 failing again.

**F2 Low (documentation).** Several texts still describe rev 2 after D-DS3.20 to D-DS3.22:
- The packet's header says "Mid-build questions: 3 open" and "Q1, Q2 each hold one xfail".
- The packet's Done items 1 and 8 say "The v4 slice is held" and "that assertion is held".
- `.ai/state/data.md`'s DS3 entry says "rulings D-DS3.1-19", "mid-build Q1-Q3 open", "(slice held, xfail)" and "census
  rule held, xfail".
- `load_world_inputs.py` (docstring and the `BULK_DATABASE_NOT_PERMITTED` detail) still says "a `*_test` or
  `<prefix>_audit*` database".

**Fix:** update these to rev 3 (no xfail, 0 open, audit names and harness clones only).

**F3 Low (documentation).** `.ai/state/index-2.md` has two lines numbered `169.` (DS3 and 0K1, from the main merge).
**Fix:** renumber the DS3 line.

**F4 Low (acceptance gap against D-DS3.21's text).** The ruling says "The limit is stated in the packet": a cover is a
least start and a greatest end, so a batch spanning gap days would resolve days the real path did not, and that is DS4's
to check. `packet.md` does not state it. **Fix:** add one line under Residual risk.

**F5 Low (test robustness, W6 class).** `test_ds3_parity_postgres.py:_cover` reads only the keys D-DS3.21 lists. A subject
key it does not know (`valid_from`, `ids`, `action_ids` from `0044`, or a future producer's key) is silently left out of
the cover, so such a group would be compared by count alone. No such group appears on this seed today (only
`reading.accepted` and `job.changed`). **Fix (preference):** fail when a subject holds a key the cover does not read.

**F6 Low (harness hardening).** `pg_harness.drop_database` (`pg_harness.py:356-364`) checks only the `*_test` suffix
before `DROP DATABASE ... WITH (FORCE)`. `clone_database(template_url=...)` likewise accepts any `*_test` source. Called
with the wrong URL, either would drop or lock `assetops_test` or `assetops_polish_walk1113_test`. Every current caller
passes clone URLs. **Fix (preference):** accept only names matching `_owned_pattern` for this run (or registered ones).

### Checked and found sound

- **Extractions.** `admit` moves submit's steps 2 to 5 verbatim. `_enqueue_admitted` keeps `decide_chunk`'s v3 and cold
  conditions and the first-id cause unchanged; only ACCEPTED ordinals are passed, as before.
- **`_bulk_evidence_params` against `_persist`.** I compared them column by column: same expressions, and the batch
  scalars equal what `open_batch` stored. Test 3's binding test checks all 42 columns with distinct values.
- **Transaction and refusal order.** One `self._run(write=True)`. Lock, publication, existing slot, decision instant,
  then the MINIGRID check, all before any write. Only `_COLLISION_INDEXES` map to `BULK_MESSAGE_COLLISION`; other
  `IntegrityError`s propagate (P5b caught). `_refuse` records nothing (P8 caught). `BatchRefused` is caught around `admit`
  only (P17 caught).
- **Commercial records.** They enter only through `load_emulated_exports.main` (same `DATABASE_URL`, checked first).
  `bulk_admit` has one caller, and no HTTP module imports the bulk path.
- **`_is_database_error`.** It classifies exceptions by package name, so the command need not import a driver. It opens
  no engine and runs no SQL, so it is not a way around the writer rule. I note it only so a later reviewer is not
  surprised.
- **Clones.** All come from `clone_database`, are dropped in `finally`, and are also registered for `cleanup()`. The
  xdist worker tag keeps workers apart, and `cleanup_run` drops by the owned pattern. After all my runs (plants failing
  mid-test included), `pg_database LIKE '%ds3%'` was `[]`.

### Checks run (real output)

- `pwsh -NoProfile -File tools/check-architecture.ps1` (worktree, `ASSETOPS_GUARD_PYTHON` set): "Architecture check
  passed.", exit 0.
- `pwsh -NoProfile -File tools/check-agent-workflow.ps1`: "Agent workflow check passed.", exit 0.
- `git diff main...0cf1dbb5c --stat -- tools/`: empty.
- `heavy-slot.sh --db` + `run-host-tests.ps1`, at head, `test_ds3_bulk_load.py`, `test_ds3_bulk_load_postgres.py`,
  `test_ds3_parity_postgres.py`, `test_pg_harness.py`: **67 passed**, 52.8 s. Parity with the v4 slice: census
  real/bulk accepted_evidence 963/963, ingestion_batch 11/11, ingestion_disposition 963/963, recompute_job 103/101,
  chain_input_change 4422/1533, event_outbox 1066/112 (reading.accepted 963/11, job.changed 103/101).
- Plants, each applied to a temporary detached worktree at `0cf1dbb5c`, run, then restored (the DS3 worktree was not
  touched):

  | Result | Plants |
  |---|---|
  | Fail as required | P1, P2, P3, P4, P5, P5b, P6, P7 (tests 5 and 7), P8, P9 (4 cases), P11, P12 (test 3), P13, P15 (test 3 and the v4 parity test), P16, P17, P18, P19, P22 (3 cases), P23, P24, P25 |
  | Fails, reviewer's own | R1 (D-DS3.21 cover) |
  | **Did not fail** | **P21** (F1) |
  | Not rerun | P10 (W2-03 regression; the extraction reads identical), P14 (3A3 scanner; no commercial write was added), P20 (needs P6's shape; P6 caught) |

- Pre-existing failures, `test_s4_evidence_decided_at_postgres.py` and `test_s2_rejection_placement.py`: `main`
  `04da33fac` gives **11 failed, 1 passed**; DS3 head gives **11 failed, 1 passed**, with the same 11 node ids. This
  confirms D-DS3.23.

### Not verified

- The full regression set (S2, S3, W2-03, 3A2, 3A3): not rerun. I cite the builder's run of 309 passed and the earlier
  run of 568 passed with the 11 known failures at `a7f7e7547` and `0cf1dbb5c`.
- check-all and the bench numbers: not rerun.
- The persistence guard's P12 message: not rerun (test 3 caught P12).

### Residual risk the packet does not name

- **`BulkEvidenceLoad` itself does not check `permitted_database`.** Only the command does. DS4's world commands must
  call the check or go through this command.
- **`ASSETOPS_PG_PORT` widens the accepted port.** If it is set to another server's port, an `_audit*` name there
  passes (as specified in D-DS3.12).
- **Merge with `main` (now `04da33fac`).** `main` has moved since `caaaa1174`. Expect text conflicts in
  `.ai/state/data.md`, `.ai/state/index-2.md` and `specs/INDEX.md` (no code overlap).
