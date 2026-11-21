# ENV-1 review packet

Branch `task/ENV1-parse-limits` (base `main` `e9d6cdfb1`): unit 1 `a001d6835`, unit 2 `2cc9a941d`, packet `351e1df92`,
conftest order and index cap `2a4d93cae`; fix round (rev 3): merge of `main` `1b564a773`, code and tests `987d62e3d`.
Spec `spec.md` rev 3, rulings D-ENV1.1-24. `USER_REVIEW_REQUIRED: false`. Mid-build questions: 1 (D-ENV1.21: the
spec's conftest order contradicted T1's guard; a spec-template defect, `.ai/RULES.md` §4 point 7).
Evidence: `/opt/assetecon/evidence/ENV1/2026-11-21-preflight/` (every pre-flight run as JSON lines, the plants log, the
slow log) and `.../2026-11-21-checks/` (Postgres, check-all, reruns); fix round `.../ENV1/fix/` (`m1_bench.py`,
`m1.jsonl`, `plants.log`, focused, slow and check-all logs; benches removed).

## 1. Pre-flight (spec §0, on `main` `e9d6cdfb1` in a detached checkout, scratch launcher deleted)

Host class: 8 cores (`nproc`), "Intel Core Processor (Haswell, no TSX)", Python 3.12.16, load 2.50 / 2.23 / 2.60
before, 2.43 / 2.53 / 2.52 after (pairs: 1.13 before, 2.27 after). CPU = user + system of the child (`os.wait4`, one
reading per child, the same figure as a `RUSAGE_CHILDREN` delta).

| Step, file | `RLIMIT_AS` floor (bisection, 32 MiB) | CPU s, 5 idle | CPU s, 3 pairs (6 children) | max RSS | wall s |
|---|---|---|---|---|---|
| check F1 | 160 MiB (128 fails) | 8.25-8.79 | 8.78-9.10 | 146 MiB | 8.3-9.1 |
| check F2 | 224 MiB (192 fails) | 8.32-8.62 | 8.65-8.99 | 185 MiB | 8.3-9.0 |
| send F1 (real gateway) | 288 MiB (256 fails) | 31.92-32.31 | 32.60-34.36 | 275 MiB | 84-96 |
| send F2 (real gateway) | 416 MiB (384 fails) | 35.88-36.43 | 35.86-36.85 | 448 MiB | 110-125 |

Each send ran in a fresh TEL-06a bench (`tel4.Bench`, the bench's expect-identity file, `deliver` a no-op); admitted +
held = 204,588 (F1) and 322,620 (F2) on every passing run. The gateway refused no 2 MiB send for a reason of its own.
**Harness note:** the first pair runs failed `GATEWAY_REFUSED` (`GATEWAY_ERROR: OperationalError`): two gateway
ledgers of 200k+ admissions filled the 12 GB `/tmp` tmpfs (2.9 GB free). Re-run with the bench directories on disk,
all 12 pair children passed (`pf-pairs2.jsonl`); not an ENV-1 limit. H6s removes its gateway directory after each case.

### Production shape (rev 3; D-ENV1.18, D-ENV1.19)

One send at a time into one real gateway (TEL-06a `tel4.Bench`), the bench on disk under `/opt/assetecon/evidence`
(41 GB free), through `tools/heavy-slot.sh`, production `SEND_LIMITS` memory and CPU, wall and slot wait 600 s, at
`987d62e3d`'s parent (`1b564a773`; the send path is unchanged by the fix). Wall = parent side around `run_field`; CPU =
the child's user + system (`RUSAGE_CHILDREN` delta). Every run below admitted + held every cell (F1 204,588; F2 322,620).

| Run | Shape | wall s | CPU s | admitted / held | load before -> after (1 min) | ledger bytes | outbox rows |
|---|---|---|---|---|---|---|---|
| (c1) F1-0 | fresh gateway | 91.5 | 31.63 | 20,408 / 184,180 | 4.49 -> 3.09 | | |
| (c1) F1-1 | fresh gateway | 92.4 | 31.98 | 20,408 / 184,180 | 3.09 -> 2.15 | | |
| (c1) F1-2 | fresh gateway | 93.0 | 32.24 | 20,408 / 184,180 | 2.15 -> 1.80 | | |
| (c1) F2-0 | fresh gateway | **129.2** | 37.97 | 20,408 / 302,212 | 1.80 -> 2.08 | | |
| (c1) F2-1 | fresh gateway | 124.2 | 37.14 | 20,408 / 302,212 | 2.08 -> 1.83 | | |
| (c1) F2-2 | fresh gateway | 122.0 | 36.08 | 20,412 / 302,208 | 1.83 -> 3.11 | | |
| (c2) F2 +0 span | one gateway, send 1 | 124.1 | 36.31 | 20,412 / 302,208 | 2.94 -> 2.58 | 480,148,752 | 20,412 |
| (c2) F2 +1 span | send 2 | 118.1 | 37.62 | 0 / 322,620 | 2.58 -> 3.29 | 861,687,056 | 20,412 |
| (c2) F2 +2 span | send 3 | 124.6 | 37.92 | 0 / 322,620 | 3.29 -> 5.59 | 1,244,359,952 | 20,412 |
| (c2) F2 +3 span | send 4 | 127.7 | 37.22 | 0 / 322,620 | 5.59 -> 6.56 | 1,627,442,448 | 20,412 |
| Review pair (M1) | two F2 at once, one gateway | 192.8, 194.2 | | 20,404 / 302,216 each | 3.20 (after) | | |
| Review solo (M1) | one F2, fresh gateway | 124.0 | | 20,404 / 302,216 | 2.84 (after) | | |

(c2) shifts every F2 timestamp by `k` x the file's span (80,655 x 15 min), `k = 0..3`; `f2_shift(0) == F2` is
asserted. **Arithmetic:** `W` = 129.2 s (c1 F2-0); 2 x `W` = 258.4 -> `SEND_LIMITS.wall_seconds` **270 s**, under the
300 s stop bound. Memory and CPU stay as built: the largest send CPU here is 37.97 s (3 x = 113.9, still 120 s); no
memory floor was re-bisected (D-ENV1.10's memory figure stands from §1). Stop conditions (D-ENV1.19): `W` 129.2 <= 150;
send 4 / send 1 = 127.7 / 124.1 = +2.9% (<= 10%); every cell admitted or held. None hit. The reviewer's pair (192.8 s,
194.2 s against 124.0 s solo) is why sends now take the one `reading-send` slot: the pair shape no longer occurs from
this network namespace.

## 2. D-ENV1.10 arithmetic

- Check: memory 2 x 224 = 448 -> **512 MiB**; CPU 3 x 9.10 = 27.3 -> **30 s**; wall **60 s**. Equals rev 1's values.
- Send: memory 2 x 416 = 832 -> **896 MiB**; CPU 3 x 36.85 = 110.6 -> **120 s**; wall **240 s**. Both under the
  stop bounds (2 GiB, 300 s). Margin over the measured worst: check 2.3x memory, 3.3x CPU; send 2.2x, 3.3x; send
  wall 240 s against 125 s measured in a pair.
- `slot_wait_seconds` 60 both (policy). `CHECK_LIMITS = FieldLimits(512 MiB, 30, 60.0, 60.0)`,
  `SEND_LIMITS = FieldLimits(896 MiB, 120, 240.0, 60.0)`, pinned by H0. **Rev 3 (D-ENV1.18/19):** the send wall is
  the production-shape rule above, `SEND_LIMITS = FieldLimits(896 MiB, 120, 270.0, 60.0)`; `STEP_POOLS = {"check":
  "reading", "send": "reading-send"}`; `POOLS["reading-send"] = 1`. All pinned by H0 / S0.
- Worst case per network namespace (rev 3, replaces the rev 2 figure): 2 x 512 MiB (commercial) + 2 x 512 MiB (check)
  + 1 x 896 MiB (send) = 2,944 MiB address space and 5 cores, whatever the worker count; a container or
  `PrivateNetwork` unit counts as another host.

## 3. Files

New: `backend/assetops_backend/parse_slots.py`, `backend/tests/test_env1_parse_slots.py`,
`host/tests/test_env1_real_send.py`. Edited: `commercial/envelope.py`, `load_emulated_exports.py`,
`reading_upload/service.py`, `reading_upload_api.py`, `host/reading_upload_process.py`, `field/.../csv_upload.py`,
`field/.../export_csv.py`, both conftests, `test_3a3_load_emulated.py`, `test_up1_reading_upload.py`,
`test_up1_reading_upload_process.py`, `test_field_csv_upload.py`. No i18n key, no guard, nothing under `contracts/`,
`gateway/`, `simulator/`, `config/`, `frontend/`. `test_3a6_parse_envelope.py` unchanged.

## 4. Done questions (spec §6)

1. Yes: field `_entry` sets the four limits before `main`; flags required (FL1); lab app builds both ports with no
   keyword (H6). Envelope and loader paths as §2.2/§2.4.
2. Yes: A1 (six causes x two steps, 503 with existing codes and words); H7 after H2-H5 breaches.
3. Yes: A2 (one record each, WARNING for `slot`/`wall`/`gateway`, ERROR otherwise, `bytes` an int, sentinel in body and
   name absent from message, args and every attribute; no other answer logs).
4. Yes: S2 (separate process, `SIGKILL` frees), S2b (through `host_slots()` and the variable).
5. Yes: §1-2; H6 (check F2 8.5 s, F1 8.5 s) and H6s (send F1 82.6 s, F2 108.8 s) passed under production memory and
   CPU; FL4 (5,000 digits -> `INVALID_VALUE`).
6. Yes: L10, L10b (size pass first, AST: no held bytes), L11, L12.
7. Yes: E0-E9 and the package scans green, files unchanged.
8. Yes: §6 below; mid-build count 1 (D-ENV1.21).
9. (rev 3) Yes: H8 (a send with no `slots` waits on `reading-send` and answers `slot` with runner and `deliver` never
   called; a check runs meanwhile); S0, H0 pin the pool, `STEP_POOLS` and the 270 s wall; plants V20 and V21 fail.

## 5. Checks (real output)

- `pytest backend/tests/test_env1_parse_slots.py`: 8 passed. `test_3a3_load_emulated.py`: 33 passed.
- 3A6 + package scans (`test_3a6_parse_envelope`, `test_3a6_source_profiles`, `test_3a2_commercial_upload_service`,
  `test_3a1_commercial_service`, `test_3a4_commercial_months`, `test_4b_money_leaves`, `test_3a3_single_writer`,
  `-n 4`): 198 passed.
- `field/tests/test_field_csv_upload.py` 24 passed; `host/tests/test_up1_reading_upload_process.py -m "not slow"` 29
  passed; `backend/tests/test_up1_reading_upload.py` 53 passed.
- Slow (`-m slow`, H6 + H6s, revision `2cc9a941d`): 3 passed in 212.9 s.
- UP-1 Postgres (`run-host-tests.ps1` via `heavy-slot --db`; `test_up1_reading_upload_flow_postgres.py` with the real
  field process and gateway, `test_up1_reading_upload_postgres.py`): 8 passed in 172 s.
- `check-architecture.ps1`: pass. `check-agent-workflow.ps1`: pass. Fast `check-all.ps1`: section 8.
- **Fix round (rev 3), at `987d62e3d` (code) / `5809f5f77` (check-all); logs in `evidence/ENV1/fix/`:**
  `test_env1_parse_slots.py` 8 passed (5.2 s); `test_field_csv_upload.py` 24 passed; `test_up1_reading_upload_process.py
  -m "not slow"` 30 passed, 1 deselected (H8 new); `test_up1_reading_upload.py` 53 passed. Slow (`-m slow`, H6 + H6s,
  via `heavy-slot.sh`): 3 passed in 228.9 s (H6s send F1 90.7 s, F2 115.9 s; H6 check F2 8.9 s, F1 8.7 s).
  `statement_catalogue.py` exit 0 after the merge, no baseline or allow-file change. `check-architecture.ps1` (with
  `ASSETOPS_GUARD_PYTHON`) pass; `check-agent-workflow.ps1` pass; `check-decision-index.py` OK. Fast check-all through
  `heavy-slot.sh --wait-seconds 3000`: "All 42 guards passed (blocking; 0 advisory, 0 warned)", exit 0, 270 s wall
  (131 s inside the slot), including both SC-1 lines (catalogue; self-test 72 of 72 plants); estate and heavy-slot
  pool self-tests skipped by their diff gates, tsc shim main-only. Postgres UP-1 files not re-run (no database code
  changed; the send path's only change is its default slot pool, covered by H8 and H6s).
- `select-tests.py --base main`: "full (574 of 574)" because both conftests changed; the full suite is the
  coordinator's to schedule (not run).

## 6. Plants (throwaway worktree at `2cc9a941d`, removed; `plants.log`)

All 19 fail their named tests: V1 FL2; V2 H1, H2; V3 H3; V4 S2, S2b; V5 H5 and S2 hang (killed at 30 s); V6 S4; V7 A1;
V8 A2; V9 FL4; V10 L11, L12; V11 L10; V12 H0, H6; V13 H4 (segv, abort, no-json); V14 S6; V15 S6 under `-n 2`;
V16 A2; V17 S2b; V18 H0 and H6s F2 (384 MiB); V19 L10b.

Rev 3 (in place at `987d62e3d`, each undone by `git checkout --`, tree clean after; `fix/plants.log`): V5 (`hold`
ignores `timeout`) fails S2 in 3.3 s, H5 in 6.2 s, H8 in 6.2 s (wall of the whole pytest process; each test bounded by
`join(5)`); V20 (`run_field`'s default `host_slots("reading")` for both steps) fails H8 in 1.1 s; V21
(`POOLS["reading-send"]` = 2) fails S0 in 2.1 s and H8 in 1.1 s.

## 7. Known deviations and residuals

- **Conftest order (guard-forced).** Spec §2.5 and D-ENV1.13 say the namespace line is the *first* statement of each
  `pytest_configure`; T1's heavy-slot tripwire (`tools/checks/test_heavy_slot_inventory.mjs`) fails unless the first
  statement is the heavy-slot `require(`, and no guard change is allowed. The line is the second statement, right
  after that one-line `require` (which either exits pytest or continues) and before every early `return`, so the
  ruling's purpose holds: S6 passes plain and under `-n 2`; plant V15 (after the worker `return`) still fails S6.
- Existing host test `test_send_reads_the_field_summary` asserted `argv[3] == "send"`; the four limit arguments move it
  to `argv[7]` (an index change beside the `limits=`/`step=` edits the spec allows).
- (L2, D-ENV1.20) The logged-503 class is every 503 that `run` answers (a parse limit, a gateway outcome, or a field
  answer that is neither preview nor refusal). The site-scope 503 (`READING_UPLOAD_UNAVAILABLE`) and the template 503
  (`READING_UPLOAD_TEMPLATE_UNAVAILABLE`) start no child and are outside it; no code change.
- (L3, D-ENV1.21) The conftest order above is ratified as built; the mid-build count is 1.
- (Rev 3) Ledger growth, named (D-ENV1.19). Over four 2 MiB F2 sends into one gateway the ledger grew by about
  382 MB per send (480 MB -> 1.63 GB); the send wall's least-squares slope is **+1.73 s per send** (about 4.5 s per GB
  of ledger), send 4 +2.9% over send 1, with the host load rising from 2.6 to 6.6 over sends 3 and 4, so the slope is
  an upper bound that includes load. The three shifted sends were all held (admitted 0; the outbox stayed at 20,412
  rows), so the growth measured is the gateway's hold path. Production's ledger persists; retuning re-runs (c2) on a
  copy of the production ledger's size class. The growth is the gateway's, not ENV-1's.
- (Rev 3) Sends run one at a time from this network namespace only; another writer into the same gateway (a lab
  replay, a server in another namespace) can still slow a send. The 270 s wall over 129.2 s measured is the margin;
  a breach logs WARNING `wall` with the step (D-ENV1.18).
- (Rev 3, merge) `.ai/state/index-2.md` is 7,990 bytes on `main` with SC-1a's line 178, so no ENV-1 line fits under
  its 8,000-byte cap however short. Per `.ai/state/INDEX.md` ("a new part when it passes the 2k-token cap") ENV-1's
  line is 180 in a new `index-3.md` (header and `INDEX.md` updated). 0K3's 179 will also need `index-3.md`, before 180.
- Hand-built server environments (D-ENV1.13): none found. `test_ch5c_env_parity._version` copies the demo env and runs
  a version probe (no parse); `test_w504` starts `sleep` processes. Every other server launch inherits `os.environ`.
- Residuals as spec §7: parked threadpool threads and a non-FIFO poll (D-ENV1.12); any process in the namespace can
  hold the names (row 49); `cpu`/`memory`/`crashed` served "try again" until SC-1a (row 49); a loader file growing
  past the cap mid-run stops at its turn. Added: the limits hold for this host class; a slower class re-runs §0.

## 8. Late checks

Fast check-all at `351e1df92`: 2 of 40 failed (T1 tripwire, see section 7; `.ai/state/index-2.md` 8,060 bytes over
the 8,000 cap, fixed by a shorter line, 7,976). After `2a4d93cae`: 40 of 40 blocking guards pass, exit 0, 750 s wall (slot wait included).
Reruns at `2a4d93cae`: `test_env1_parse_slots.py -n 2` 8 passed; host UP-1 file 29 passed (1 slow deselected).
