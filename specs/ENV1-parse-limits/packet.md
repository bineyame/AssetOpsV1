# ENV-1 review packet

Branch `task/ENV1-parse-limits` (base `main` `e9d6cdfb1`): unit 1 `a001d6835`, unit 2 `2cc9a941d`, packet `351e1df92`,
conftest order and index cap `2a4d93cae`.
Spec `spec.md` rev 2, rulings D-ENV1.1-17. `USER_REVIEW_REQUIRED: false`. Mid-build questions: 0.
Evidence: `/opt/assetecon/evidence/ENV1/2026-11-21-preflight/` (every pre-flight run as JSON lines, the plants log, the
slow log) and `.../2026-11-21-checks/` (Postgres, check-all, reruns).

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

## 2. D-ENV1.10 arithmetic

- Check: memory 2 x 224 = 448 -> **512 MiB**; CPU 3 x 9.10 = 27.3 -> **30 s**; wall **60 s**. Equals rev 1's values.
- Send: memory 2 x 416 = 832 -> **896 MiB**; CPU 3 x 36.85 = 110.6 -> **120 s**; wall **240 s**. Both under the
  stop bounds (2 GiB, 300 s). Margin over the measured worst: check 2.3x memory, 3.3x CPU; send 2.2x, 3.3x; send
  wall 240 s against 125 s measured in a pair.
- `slot_wait_seconds` 60 both (policy). `CHECK_LIMITS = FieldLimits(512 MiB, 30, 60.0, 60.0)`,
  `SEND_LIMITS = FieldLimits(896 MiB, 120, 240.0, 60.0)`, pinned by H0.
- Worst case per network namespace: 2 x 512 MiB (commercial) + 2 x 896 MiB (reading) = 2.75 GiB address space and 4
  cores, whatever the worker count; a container or `PrivateNetwork` unit counts as another host.

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
8. Yes: §6 below; mid-build count 0.

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
- `select-tests.py --base main`: "full (574 of 574)" because both conftests changed; the full suite is the
  coordinator's to schedule (not run).

## 6. Plants (throwaway worktree at `2cc9a941d`, removed; `plants.log`)

All 19 fail their named tests: V1 FL2; V2 H1, H2; V3 H3; V4 S2, S2b; V5 H5 and S2 hang (killed at 30 s); V6 S4; V7 A1;
V8 A2; V9 FL4; V10 L11, L12; V11 L10; V12 H0, H6; V13 H4 (segv, abort, no-json); V14 S6; V15 S6 under `-n 2`;
V16 A2; V17 S2b; V18 H0 and H6s F2 (384 MiB); V19 L10b.

## 7. Known deviations and residuals

- **Conftest order (guard-forced).** Spec §2.5 and D-ENV1.13 say the namespace line is the *first* statement of each
  `pytest_configure`; T1's heavy-slot tripwire (`tools/checks/test_heavy_slot_inventory.mjs`) fails unless the first
  statement is the heavy-slot `require(`, and no guard change is allowed. The line is the second statement, right
  after that one-line `require` (which either exits pytest or continues) and before every early `return`, so the
  ruling's purpose holds: S6 passes plain and under `-n 2`; plant V15 (after the worker `return`) still fails S6.
- Existing host test `test_send_reads_the_field_summary` asserted `argv[3] == "send"`; the four limit arguments move it
  to `argv[7]` (an index change beside the `limits=`/`step=` edits the spec allows).
- `open_site`'s 503 `READING_UPLOAD_UNAVAILABLE` (the Site scope's store unavailable) is not a parse 503 and is not
  logged; the spec's class names the three service branches. Raise if the reviewer reads "every 503" wider.
- Hand-built server environments (D-ENV1.13): none found. `test_ch5c_env_parity._version` copies the demo env and runs
  a version probe (no parse); `test_w504` starts `sleep` processes. Every other server launch inherits `os.environ`.
- Residuals as spec §7: parked threadpool threads and a non-FIFO poll (D-ENV1.12); any process in the namespace can
  hold the names (row 49); `cpu`/`memory`/`crashed` served "try again" until SC-1a (row 49); a loader file growing
  past the cap mid-run stops at its turn. Added: the limits hold for this host class; a slower class re-runs §0.

## 8. Late checks

Fast check-all at `351e1df92`: 2 of 40 failed (T1 tripwire, see section 7; `.ai/state/index-2.md` 8,060 bytes over
the 8,000 cap, fixed by a shorter line, 7,976). After `2a4d93cae`: 40 of 40 blocking guards pass, exit 0, 750 s wall (slot wait included).
Reruns at `2a4d93cae`: `test_env1_parse_slots.py -n 2` 8 passed; host UP-1 file 29 passed (1 slow deselected).
