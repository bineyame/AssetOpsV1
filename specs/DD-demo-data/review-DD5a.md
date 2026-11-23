# Review: DD5a, sealing and the cold and EV bulk path (discovery)

## Round 1 (2026-11-23, branch `task/DD5a-load` at 2805d367a, fresh Claude reviewer)

**Summary (verdict: ACCEPT with the Lows fixed on the branch; none blocks).**
- Units 1-4 match the card and D-DD.138 to .140 as amended by D-DD.161/.162. I found no High or Medium.
- The guard-list addition is sound. `sealed_batch_files.py` is an evidence adapter that only `composition.py`
  reaches. It writes only `*.batch.json` into the caller's folder, never a product store, and it follows the
  `legacy_comparison_file.py` / `gateway_credential_file.py` precedent. The guard is not weakened.
- Deviation 6 accepted for DD5a. The writer gap is real on main (`telemetry_ev.py` drops the eighth tuple element). It
  is being closed on `task/DD4b-followup` (2facff231 adds the `session` pair to in-session connector rows). That branch
  must merge before DD5b seals real EV days.
- Deviation 7 accepted. The v4 contract requires `connector_id` on `EV_CONNECTOR_*` and leaves `session_id`
  optional (`source_envelope_v4.py:342-344`). On every connector event the writer sets `component_id` to the
  connector asset, the same value it uses as `connector_id` inside a session (`telemetry_ev.py` `_event`). The
  fallback therefore gives one connector one id. A preference, not a gap: the writer could carry `connector_id` on
  every connector event, and the sealer would then refuse when it is absent.
- 4 Lows (refusal coverage, refusal file naming, write durability, a stale state entry). There is one model question
  for the Architect, about re-seals against a rebuilt database.

### Findings

**L1 (Low, acceptance-adjacent). A contract rejection while sealing escapes as a traceback, not exit 2.**
`backend/assetops_backend/evidence/world_seal.py:117,124,139` build `SourceEnvelopeV3/V4`, whose `__post_init__`
validates. A row the contract refuses raises `EnvelopeRejected`, which neither `_seal_tenant`
(`load_world_inputs.py:110` catches only `WorldSealRefused`) nor `main` (`:214-218` re-raises non-database errors)
maps. Example: an EV session event with a `correlation` but no session. I reproduced it: `CORRELATION_INVALID at
payload.session_id`, uncaught. A missing `connector_id` beside a `session_id` (`world_seal.py:150`) is a bare
`KeyError`. Why it matters: the card's refusal grammar is `<CODE> <file> <what>`, exit 2. A traceback names no file
or channel, and DD5b's ladder will read the exit code. Fix: in `seal_readings` (or `_envelope_text`), catch
`EnvelopeRejected` and re-raise `WorldSealRefused("WORLD_SEAL_ENVELOPE_INVALID", f"{device}/{signal} {code}")`.
Require `connector_id` whenever `session_id` is present (refuse `WORLD_SEAL_EV_UNCORRELATED`). Add one test per case.

**L2 (Low). Row-level refusals name the Site's first readings file, not the file holding the row.**
`load_world_inputs.py:98,110`: `first = days[0][2]` is used for every `WorldSealRefused`, including an unbound
channel on day 30. The card says `WORLD_TELEMETRY_UNRESOLVED <file> <what>`. The unknown-Site and missing-digest
cases are correct, because they concern the Site. Fix: have `seal_readings` report the failing day (for example,
`WorldSealRefused` gains `day`), and map that day back to its file name.

**L3 (Low). `SealedBatchFiles.write_new` writes in place with no exclusive create and no fsync.**
`backend/assetops_backend/evidence/adapters/sealed_batch_files.py:21-28`. The precedent it joins in the guard list,
`legacy_comparison_file.py:33-37`, uses `O_CREAT|O_EXCL` plus fsync. A crash mid-write leaves a truncated file. The
next run would report it as `WORLD_SEALED_BYTES_DIFFER ... re-seal` and need a manual delete. That outcome is safe but
misleading. Fix: write to a temp name in the same folder, then `os.replace`, or use `O_EXCL` as the precedent does.

**L4 (Low, docs). The part-1 state entry contradicts the shipped code.**
`.ai/state/data.md:737-744` and `.ai/state/index-3.md:37` (entry 212) still say "new `ev_session_id`". They also list
units 3 and 4 as open. The code withdrew `ev_session_id` (D-DD.161), and entry 213 says so. A grep on the slice ID
returns both entries. Fix: mark 212 "superseded by 213", or fold it into 213.

### Deviations judged
- 1-5: confirmed by D-DD.161; the code matches (`publishes_v4_metadata` world-only, `("site-meter", "import")`,
  canonical `_value` with both asserts, pack session id copied, `ev_session_id` absent).
- 6, 7: see summary.
- 8 (plant (b) as `BATCH_ID_CONFLICT`): acceptable. The load fails, which is what the plant must prove. The batch
  id covers the sequence range, so the collision surfaces there first.
- 9 (guard list): accepted, see summary.
- 10, 11: fine. `world.env`, C6 and C-DD8 wiring belong to DD5b's card (`cards/DD5b.md:44-45`).

### Checks I ran (logs under `/opt/assetecon/evidence/DD5a/review/`)
- `tools/check-architecture.ps1`: passed (`arch.txt`). The first run without `ASSETOPS_GUARD_PYTHON` failed only
  because no interpreter was found (the worktree has no `.venv`). It passed with
  `ASSETOPS_GUARD_PYTHON=/opt/assetecon/AssetOpsV1/.venv/bin/python`.
- `tools/check-agent-workflow.ps1`: passed (`workflow.txt`).
- Pure tests through `tools/heavy-slot.sh` + `tools/run-host-tests.ps1`: `test_dd5a_world_seal.py`,
  `test_dd5a_load_world_inputs.py`, `test_dd5a_world_v4_tables.py`, `test_ds3_bulk_load.py`,
  `host/tests/test_dd5a_world_seal_parity.py`: 54 passed in 4.42 s (`pure.txt`; run with `--db-lane`, because the host-tests wrapper sets the test database URL).
- `git merge-tree main HEAD`: clean. Only `specs/DD-demo-data/spec.md` is touched on both sides since the merge base
  601bdb489.
- Builder's results cited, not rerun. Reach set at af5185c9f: 243 passed, 1 skipped, exit 0 (`reach-final.log`).
  Plant (b) `BATCH_ID_CONFLICT` and plant (c) `BULK_SITE_TYPE_UNPROVEN` are in `plant-b.txt`/`plant-c.txt`. The
  Lab plant failed 5 of 5 (`plant-dd161-lab.txt`). The cold/EV parity test is in the reach set.
  `af5185c9f..2805d367a` changes only the packet, handoff, state and spec status, so the run covers the reviewed
  code. No Postgres rerun was needed for any finding.

### Not verified
- The Postgres files (bindings, load, parity) were not rerun. I cite the builder's same-code run.
- No real EV readings day was sealed, because the writer on main lacks the session pair (deviation 6). The EV path is
  proven only on hand rows in the ruled shape.

### Residual risk the packet does not name
- **Re-seal against a rebuilt database.** Source, binding-set and gateway ids are `uuid4`
  (`binding_service.py:504,627,744`). `tools/world.py:606-608` reuses `inputs/<digest[:12]>` whenever it exists. So
  a second L2 build on a fresh database with unchanged inputs finds old `sealed/` bytes and refuses
  `WORLD_SEALED_BYTES_DIFFER` every time. This is D-DD.140 as ruled ("a function of the inputs and the database ids"),
  so it is not a DD5a defect, but DD5b's wiring will hit it (question below).
- Databases onboarded before DD5a keep their v3 world cold/EV conversions. `convert` is idempotent and "a rerun
  reports the existing one", so only a rebuilt world gains v4 metadata.
- `WORLD_EV_CONNECTOR_PREFIXES` (`source_envelope_v4.py`) is a typed list. A test pins it to
  `backend/tests/fixtures/on1/metro-bus.onboarding.json`, not to the generated world's `/2` files. That holds as long
  as that fixture is the depot source (D-DD.162 fact 2).
- The parity test compares the all-accepted path (evidence, batch, disposition, recompute job). Cold/EV rejection
  rows (`evidence_rejection`) are not compared between the two paths.

### Questions for the Architect
1. (Model, D-DD.140 to DD5b.) When the database is rebuilt but the inputs digest is unchanged, should `sealed/` be
   cleared by the caller, keyed by the database (for example, by the L2 key), or should the refusal apply only within
   one database's lifetime? As ruled, every rebuild on unchanged inputs refuses `WORLD_SEALED_BYTES_DIFFER`.
