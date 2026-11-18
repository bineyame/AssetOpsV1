# Build spec, telemetry lane (Lane T), 2026-10-27

Architect: Claude (`.ai/ROLE_CONFIG.md` line 9). Owner instruction on depth, verbatim: `.agent/owner-build-plan-depth-2026-10-27.md`. Index and calendar: `.agent/build-sequence-2026-10-27.md`.

This file is what Lane T builders are briefed from, and it is the lane's task file (no separate `tasks/TEL-*.md` files; see Q-T2). It settles every design choice a builder would otherwise make. If something here is missing or wrong, it is a pre-flight question, not a builder decision (see "Implementer questions and resolutions" at the end).

**Revision 2 (2026-10-27, after the Implementer's 70 pre-flight questions).** The body below already carries every answer; each changed rule names its question as `(Q-Tn)`. The answers, with what was verified in code, are in the last section.

**Authority order:** this file, then `.agent/telemetry-rulings-2026-10-27.md` (D4, D10, D5, D6 and amendments 1 to 3), then `Docs/demo-sprint/telemetry-integration-plan-claude.html` rev 3 §10 cards. Where this file corrects a card, the correction is marked **Card correction**.

---

## 0. Lane rules (every task)

### 0.1 Worktree, branch and environment

- Worktree `C:\Users\assef\Bineyame\AssetOpsV1-tel`, created from `main` **after** the coordinator has merged this spec, the build sequence and the rulings (amendment 3) to `main` (Q-T1). The builder reads the specs inside the worktree. One branch per task group: `task/TEL-01-field-core` (TEL-01..03), `task/TEL-04-poller` (TEL-04..05), `task/TEL-08-bbb` (TEL-08, TEL-05b, TEL-07), `task/TEL-06-csv`. If TEL-03 slips, see Q-T67.
- Python: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe` (3.12).
- **PYTHONPATH (put this line at the top of the TEL-00 packet and of every packet):**

  PowerShell:
  ```
  $env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-tel\backend;C:\Users\assef\Bineyame\AssetOpsV1-tel\contracts;C:\Users\assef\Bineyame\AssetOpsV1-tel\simulator;C:\Users\assef\Bineyame\AssetOpsV1-tel\gateway;C:\Users\assef\Bineyame\AssetOpsV1-tel\host;C:\Users\assef\Bineyame\AssetOpsV1-tel\field;C:\Users\assef\Bineyame\AssetOpsV1-tel"
  ```
  The shared venv's editable installs point at `C:\Users\assef\Bineyame\AssetOPsV1` (feasibility §2.3). Without this line every test silently runs the main checkout's code. Open a new terminal per task, and print `python -c "import assetops_gateway,sys;print(assetops_gateway.__file__)"` once; it must name the `-tel` worktree.
- Never `pip install -e field`. Before TEL-03 the coordinator runs `pip download pymodbus==3.16.1 --no-deps -d %TEMP%\pymodbus-3.16.1`, records the wheel file name and its SHA-256 in the TEL-03 packet, then `pip install pymodbus==3.16.1` into the shared venv (Q-T7). pymodbus is a **test-only** dependency used as an independent conformance client (TEL-03).
- Test command form, from cwd `C:\Users\assef\Bineyame\AssetOpsV1-tel` (Q-T8):
  `<python> -m pytest <file> -q -p no:cacheprovider --basetemp "$env:TEMP\assetops-tel\<file stem>"`
- Postgres tests: `ASSETOPS_TEST_DATABASE_URL` names `assetops_tel_test` in `assetopsv1-postgres-1` (Lane T's own database; Lane C uses its own). `pg_harness.fresh_database()` resets it at the start of each test (Q-T56).

### 0.2 What Lane T must not touch

`backend/assetops_backend/**`, `backend/migrations/**`, `frontend/**`, `gateway/**`, `contracts/**`, `simulator/**`, host product modules (`host/*.py`), `tools/*.py`, any `tools/checks` file except additive sections in `module-roots.ps1` and `dependency-direction.ps1`, `.agent/mock-departure-register.md`, `.ai/**` and `tasks/**` (the coordinator updates those at merge, Q-T3). Allowed outside the lane's own new files: one additive line in `.gitattributes` (`contract-fixtures/telemetry/** -text`, Q-T44). If any other guard or document needs a `field/` entry, stop and ask (Q-T4). No dev server and no browser capture. Stop and ask on any need to cross this line.

### 0.3 Heavy-job queue

Lane T has first claim until 30 October 23:59. Heavy: every Postgres test (run alone), TEL-04 and TEL-06a end-to-end files (one file at a time, never during a capture or full suite), the TEL-08 bench run. Light: `field/tests`, `host/tests/test_field_observation_fixtures.py` (no gateway, no database; run as its own file, Q-T68), the two `.ps1` checks, `gateway/tests/test_wire_contracts.py`. Ask the coordinator for the queue slot before any heavy job.

### 0.4 Ports (fixed in TEL-00)

| Port | Use |
|---|---|
| 5020 | GX-shaped emulator, Modbus TCP (runbook and TEL-08). Tests bind an ephemeral port (port 0) and pass it to the poller. |
| 8443 | `serve_tls` for the runbook and TEL-08 only. Tests use `FakeCentral` (`gateway/tests/fake_central.py`), whose port is ephemeral (`127.0.0.1:0`). |
| Gateway IPC | Named pipe on Windows, Unix socket on Linux (`host/tests/gateway_process.py:20-23`). No TCP port. |

Commercial dev servers use 5173 and 8000; none of the above overlaps them. Port 7000 (RTU over TCP) is unused in October.

### 0.5 Module map (what exists when the lane is done)

```
field/
  pyproject.toml                     requires-python >=3.12; dependencies = []; extras dev=[pytest>=8.0, pymodbus==3.16.1], serial=[pyserial]
  assetops_field/
    __init__.py                      empty marker, version string only
    profile.py                       FieldProfile, ProfileRow, RegisterRef, CsvColumn, load_profile, ProfileRefused
    decode.py                        decode_words, encode_value, encode_sentinel, Decoded, DecodeFault, EncodeRefused
    clock.py                         Clock protocol, WallClock, ReplayClock
    aggregate.py                     PollOutcome, Poll, Result, IntervalAggregator, StateSampler, schedule helpers
    report.py                        build_report, report_key, report_text
    publish.py                       GatewayPublisher, IdentityMismatch
    modbus_tcp.py                    ModbusTcpClient, ReadResult, WriteForbidden, classify
    modbus_poller.py                 CLI and Poller loop
    export_csv.py                    (TEL-06) CsvCollector, CsvRefused
  profiles/
    gx-system-illustrative-1.json    TEL-03
    gx-system-illustrative-2.json    TEL-05b
    generic-interval-csv-illustrative-1.json   TEL-06
  tests/
    field_fixtures.py                shared helpers (no conftest.py)
    test_field_profile.py, test_field_decode.py, test_field_aggregate.py, test_field_report.py,
    test_field_publish.py, test_field_clock.py           (prefixed, Q-T10)
    test_field_modbus_tcp.py         TEL-02, stdlib in-test socket server
    field_emulators/__init__.py      (package renamed from `emulators`, Q-T9)
    field_emulators/gx_server.py     TEL-03, stdlib Modbus TCP server (Q-T37)
    test_field_gx_emulator.py        includes the pymodbus 3.16.1 client cross-check
    test_field_export_csv.py         TEL-06
contract-fixtures/telemetry/
  kobo-public-observations-v1/       TEL-03: observations.jsonl + manifest.json
  kobo-prolonged-public-observations-v1/   TEL-05b
  generic-interval-csv-v1/           TEL-06
host/tests/
  field_observation_fixtures.py      generators for both JSONL fixtures (imported by the freshness tests)
  test_field_observation_fixtures.py freshness tests for both JSONL fixtures (light)
  test_field_modbus_tcp_proof.py     TEL-04 focused E2E (GatewayProcess + FakeCentral)
  test_field_modbus_tcp_acceptance_postgres.py   TEL-05 and TEL-05b (two tests, each its own fresh database)
  field_bench.py                     stdlib helpers (expect_identity_from_snapshot, cohort_members) plus
                                     TEL-08 subcommands `setup`, `activate`, `read` (backend imports inside setup/read only)
  test_field_export_csv_proof.py     TEL-06a
```

Dependency rule (D4, amendment 2 item 2): non-test `field/` imports stdlib, `assetops_contracts.*` and `assetops_gateway.ipc` only. `field/tests` may add `pymodbus` and import `assetops_field`. `host/tests` may import `assetops_field` and, by `sys.path.insert(0, str(ROOT / "field" / "tests"))` and `sys.path.insert(0, str(ROOT / "gateway" / "tests"))` at the top of the file (the pattern of `host/tests/test_s6_verification_publication.py:33-35`), `field_emulators` and `fake_central` (Q-T9). Nothing else imports `assetops_field`.

### 0.6 Shared data shapes

**Field profile document (`assetops.field-profile` version 1).** JSON. Its SHA-256 is `hashlib.sha256(canonical_json(document).encode("utf-8")).hexdigest()` using `assetops_contracts.source_envelope.canonical_json` (sorted keys, so key order cannot move it; Q-T18).

```json
{
  "schema": {"id": "assetops.field-profile", "version": 1},
  "profile_id": "gx-system-illustrative-1",
  "profile_version": 1,
  "status": "UNPINNED",
  "interface": "MODBUS_TCP",
  "source_timestamps": "UTC_Z_REQUIRED",
  "coverage": "ALL_EXPECTED_POLLS",
  "state_skew_max_seconds": 2,
  "rows": [
    {
      "row_id": "pv-ac-output",
      "status": "UNPINNED",
      "source_document": "third-party summary (aggsoft.com), Victron CCGX register list; not a vendor document",
      "device_id": "pv-inverter-controller",
      "signal_id": "ac-power",
      "role": "pv_power",
      "source_unit": "kW",
      "quantity": {"kind": "AC_POWER", "point": "AC output bus, AC-coupled PV only",
                   "sign": "positive = power delivered to the AC bus",
                   "phase_aggregation": "EXACT_SUM_L1_L2_L3"},
      "registers": [
        {"unit_id": 100, "function": 3, "address": 808, "type": "uint16", "word_order": "BIG"},
        {"unit_id": 100, "function": 3, "address": 809, "type": "uint16", "word_order": "BIG"},
        {"unit_id": 100, "function": 3, "address": 810, "type": "uint16", "word_order": "BIG"}
      ],
      "decode": "NUMBER",
      "sentinels": [65535],
      "scale_exponent": 0,
      "register_unit": "W",
      "unit_exponent": -3,
      "register_quantum": "1",
      "output_resolution": "0.001",
      "reading_class": "INTERVAL_SIGNAL",
      "span_seconds": 900,
      "cadence_seconds": 900,
      "poll_period_seconds": 300
    }
  ]
}
```

**Field rules.** `load_profile` refuses with `ProfileRefused(code, field, detail)`; `field` is a JSON path such as `rows[0].registers[1].address`. The closed code set is the nine codes below; each has at least one test (Q-T11, Q-T17).

Top level:
- Exactly the keys shown (`schema`, `profile_id`, `profile_version`, `status`, `interface`, `source_timestamps`, `coverage`, `state_skew_max_seconds`, `rows`); a missing or extra key [`SCHEMA_INVALID`]. `schema` must equal `{"id": "assetops.field-profile", "version": 1}` [`SCHEMA_INVALID`]. `profile_id` matches `^[a-z0-9][a-z0-9-]{0,63}$`; `profile_version` integer ≥ 1; `state_skew_max_seconds` integer 1..10; `rows` non-empty [`SCHEMA_INVALID`].
- `status` and each row `status` in `PINNED | UNPINNED | ILLUSTRATIVE`. The profile `status` must equal the weakest row status, ordered `PINNED > UNPINNED > ILLUSTRATIVE` [`STATUS_INCONSISTENT`].
- `interface` in `MODBUS_TCP | EXPORT_CSV`; every row must suit the interface (below) [`SCHEMA_INVALID`]. `source_timestamps` must be `UTC_Z_REQUIRED`, `coverage` must be `ALL_EXPECTED_POLLS` in October [`UNSUPPORTED_VALUE`].

Every row:
- Common keys, all required: `row_id` (`^[a-z0-9][a-z0-9-]{0,63}$`, unique across rows), `status`, `source_document`, `device_id`, `signal_id`, `role`, `source_unit`, `quantity`, `reading_class`, `cadence_seconds`, plus the class and interface keys below. Any other key [`SCHEMA_INVALID`].
- `quantity` has exactly `kind`, `point`, `sign`, `phase_aggregation`, all non-empty strings. `phase_aggregation` is `SINGLE_REGISTER` for a one-register row and `EXACT_SUM_*` for a multi-register `NUMBER` row [`SCHEMA_INVALID`].
- `reading_class` `STATE_SIGNAL` (needs `cadence_seconds`; forbids `span_seconds`, `poll_period_seconds`) or `INTERVAL_SIGNAL` (needs `span_seconds`, `cadence_seconds`, and for `MODBUS_TCP` `poll_period_seconds`) [`SCHEMA_INVALID`].
- `span_seconds` and every `cadence_seconds` divide 86400; `cadence_seconds` is a whole multiple of `span_seconds` [`CADENCE_NOT_ALIGNED`].
- `poll_period_seconds` is even, ≥ 2, and divides `span_seconds` exactly [`POLL_PERIOD_NOT_DIVISOR`].
- `(device_id, signal_id)` unique across rows [`DUPLICATE_SIGNAL`]. `report_key` for source time `2026-12-31T23:59:59Z` at most 192 characters [`REPORT_KEY_TOO_LONG`].

`MODBUS_TCP` rows (all of `registers`, `decode`, `sentinels` required; `csv` forbidden):
- `registers` non-empty; each register has exactly `unit_id` (0..255), `function` (3 or 4 only in October), `address` (0..65535, the 0-based PDU address sent verbatim, Q-T38), `type` (`int16 | uint16 | int32 | uint32`), `word_order` (`BIG` = high word first `AB CD`, `LITTLE` = `CD AB`) [`SCHEMA_INVALID`]. A 32-bit type occupies two consecutive addresses; the row lists the first address only and the decoder reads two words. A 32-bit register at 65535 [`SCHEMA_INVALID`].
- `decode` `NUMBER` or `ENUM`.
  - `NUMBER` rows require `scale_exponent`, `unit_exponent` (integers −12..12), `register_unit`, `register_quantum`, `output_resolution` (finite decimal strings accepted by `assetops_contracts.observation.device_resolution`) and forbid `enum_map` [`SCHEMA_INVALID`]. More than one register means an exact sum of the decoded registers (phase sum) [`SCHEMA_INVALID` unless `phase_aggregation` is `EXACT_SUM_*`]. `output_resolution` must not be finer than the register quantum in the source unit, `register_quantum × 10^(scale_exponent + unit_exponent)` [`RESOLUTION_FINER_THAN_QUANTUM`].
  - `ENUM` rows require exactly one `uint16` register, `source_unit` `"state"`, and `enum_map` (object of decimal integer code strings 0..65535 to state text matching `^[A-Z][A-Z0-9_]*$`); they forbid `scale_exponent`, `unit_exponent`, `register_unit`, `register_quantum`, `output_resolution` and are `STATE_SIGNAL` only [`SCHEMA_INVALID`].
- `sentinels` is a list (possibly empty) of **unsigned** raw integers of the register's width (16 bit: 0..65535, 32 bit: 0..4294967295) [`SENTINEL_OUT_OF_RANGE`]. A signed sentinel is written as its unsigned bit pattern (int16 −32768 is `32768`) (Q-T14).

`EXPORT_CSV` rows (TEL-06; `csv` required; `registers`, `decode`, `sentinels`, `scale_exponent`, `unit_exponent`, `register_unit`, `register_quantum`, `poll_period_seconds`, `enum_map` forbidden) (Q-T65):
- `csv` has exactly `{"column": "<header name>"}` matching `^[a-z][a-z0-9_]{0,63}$`; `output_resolution` required; `reading_class` must be `INTERVAL_SIGNAL`; every row of one CSV profile has the same `span_seconds` [`SCHEMA_INVALID`].

**Value rule.** Value = `raw × 10^(scale_exponent + unit_exponent)` in `source_unit`, as `Fraction`.

**Raw capture line** (one JSON object per Modbus **attempt**, retries and failures included, appended to `<state-dir>/raw-<session-stamp>.jsonl` where `<session-stamp>` is `YYYYMMDDTHHMMSSZ-<8 hex>` from the session reference, Q-T35): `{"at": source instant Z of the send, "wall_at": wall instant Z with milliseconds, "scheduled_at": the poll or boundary instant Z, "row_id", "unit_id", "function", "address", "count", "attempt": 1|2, "request_hex", "response_hex" (null on no answer), "sha256" (of request||response bytes, response empty if none), "outcome": "WORDS|EXCEPTION_<hh>|NO_ANSWER_<kind>|SKIPPED_LATE", "profile_sha256"}`.

**Status file** (`<state-dir>/status.json`, rewritten after every publish instant by writing `status.json.tmp` then `os.replace`, Q-T35): `{"profile_id", "profile_version", "profile_sha256", "clock": {"mode": "WALL|REPLAY", "start", "rate", "wall_epoch"}, "session_ref", "session_start", "counters": {"VALUE", "NO_VALUE", "FAILED", "NO_ANSWER", "CONFIG_FAULT", "SKIPPED_LATE"}, "admissions": {"ADMITTED", "ALREADY_ADMITTED", "HELD"}, "holds_by_kind": {kind: count}, "seal_refusals", "retained_reports", "last_publish_instant", "faulted_rows": [row_id...]}` (Q-T32).

**Session file** (`<state-dir>/session.json`): `{"session_ref", "session_start", "profile_sha256"}`, written after `release_previous` succeeds.

**Expect-identity file** (`--expect-identity`, Q-T31). Written by `field_bench.expect_identity_from_snapshot(snapshot_text, profile_document, sequence_epoch)` (stdlib only), used by the TEL-04/05 harness and by `field_bench.py setup`:
```json
{"tenant_id": "<uuid>", "site_id": "<uuid>", "gateway_id": "<uuid>", "source_mode": "SIMULATED",
 "sequence_epoch": "epoch-1",
 "row_sources": {"pv-inverter-controller/ac-power": "<source uuid>", "battery-pcs-controller/state-of-charge": "<source uuid>"}}
```
`row_sources` is taken from the snapshot's `bindings[]` (`device_id`, `signal_id`, `source_id`) for exactly the profile's rows; a profile row without a binding makes the helper raise. `field_bench.cohort_members(expect)` returns `sorted({f"{gateway_id}:{source_id}:{sequence_epoch}" for each row source})` for `assess --cohort`.

**Pinned JSONL fixture.** `observations.jsonl`: one canonical JSON object per public `DeviceObservation`, fields exactly as the dataclass (`device_id`, `signal_id`, `reading_class`, `source_sample_time`, `outcome`, `reported_value` as exact decimal text or state text or null, `canonical_unit`), ordered by `(source_sample_time, device_id, signal_id)`. Written UTF-8, LF line ends, one final LF (Q-T44). `manifest.json`: `{"generator": "host/tests/field_observation_fixtures.py:<function>", "scenario", "window", "publication_profile", "timestep_minutes", "observation_count", "sha256"}`, canonical JSON plus one LF. Public observations only; nothing private crosses (no run cause, no kernel state).

### 0.7 Fault semantics (single table every module follows)

`classify` (Q-T22) maps the read results of one row at one attempt to an outcome. Precedence when a row needs several requests: `CONFIG_FAULT` > `NO_ANSWER` > `FAILED` > `NO_VALUE` > `VALUE`.

| Poll result (TEL-02 `ReadResult`) | `PollOutcome` | State boundary publishes | Interval (D10) |
|---|---|---|---|
| Words decoded to a value | `VALUE` | `GOOD` with the value | counts as answered |
| Words where any register equals a declared sentinel; or exception 02 | `NO_VALUE` | `UNAVAILABLE` / `NO_MEASUREMENT` | interval becomes `UNAVAILABLE` / `NO_MEASUREMENT` |
| Exception 04 or 06 after the one retry | `FAILED` | nothing (no sample) | missing poll: `NO_MEASUREMENT` if any poll was answered |
| Timeout, refused, reset, exception 0A or 0B, Unit ID or transaction ID mismatch (after the one retry for timeout) | `NO_ANSWER` | nothing | missing poll; if no poll answered, nothing |
| Exception 01 or 03, a decode type mismatch (wrong word count), an unmapped enum code | `CONFIG_FAULT` | nothing; the **whole row** is added to `faulted_rows` and not polled again this session (Q-T24) | that poll counts as missing; the interval closes normally; later intervals of the row publish nothing |
| Poll or retry not sendable inside its window (late) | `SKIPPED_LATE` counter; poll treated as `NO_ANSWER` | nothing | missing poll |

**Retries are owned by the poller, not the client (Q-T21).** One retry per poll for `TIMEOUT`, exception 04 and exception 06 only, and only if the retry can be sent inside the attempt window (0.8). Each attempt is one raw-capture line.

The first boundary of a session, and the first after a poller restart, gives `UNAVAILABLE` / `NO_COMPLETED_INTERVAL` with its span for each interval row whose span began before `session_start` (D10). `STALE` is never emitted. **Card correction (TEL-02):** "a timeout retries once, then reports UNAVAILABLE" becomes "the poller retries a timeout once inside the attempt window, then records `NO_ANSWER`; nothing is published for that read".

### 0.8 Clock and schedule model (shared by poller and emulator)

- `WallClock`: real UTC, whole seconds.
- `ReplayClock(start: datetime, rate: int, wall_epoch: datetime)`: `source_now = start + (wall_now − wall_epoch) × rate`, truncated to whole seconds (it is earlier than `start` before `wall_epoch`). Rate is an integer 1..600. Two processes agree on source time when given the same three arguments and synchronised wall clocks.
- Both clocks take injectable `wall: Callable[[], datetime]` and `sleep: Callable[[float], None]` (defaults `datetime.now(timezone.utc)` and `time.sleep`). `sleep_until(instant)`: computes the wall target; loops `sleep(min(remaining − 0.002, 0.5))` while more than 2 ms remain, then spins on `wall()`; returns at once for a past instant; re-reads `wall()` every loop so a wall step is absorbed (Q-T25).
- Replay is used only to play a simulator run's past public outputs. Every source time it produces is in the past, so the gateway's `SOURCE_TIME_IN_FUTURE` check (`gateway/assetops_gateway/service.py:856`) cannot fire unless a wall clock is wrong. The clock mode is printed in the start line, the status file and the claim record. Replay mode requires `--stop-at` (exit 2 without it, Q-T26).
- **Session start (Q-T19).** `session_start` is source time read after the identity check and `release_previous`. In replay mode, if that is before `--replay-start`, the poller sleeps until `--replay-start` and `session_start = replay_start`. The harness passes `--replay-wall-epoch` = now + 5 s to poller and emulator, so a session "started on" a boundary really starts there. Boundaries ≤ `session_start` are skipped (nothing published); a state boundary equal to `session_start` is sampled.
- **Interval poll instants (D10 amended, Q-T27).** For a published span `[start, end)` (end a multiple of `cadence_seconds`, start = end − span), the expected polls are `start + (k + ½) × poll_period` for `k = 0 … N−1`, `N = span / poll_period`. Mid-period placement keeps every poll `poll_period/2` away from a span edge, so a small clock offset between poller and emulator can never read the neighbouring interval's value.
- **State attempt window (Q-T20).** For boundary `B`, the first attempt is sent at `B + ⌈skew/2⌉` (1 s with the default skew 2); a retry is sent only if `clock.now()` at send is ≤ `B + skew`. The attempt's source time (`Poll.at`) is `clock.now()` read immediately before `sendall`. A first attempt that cannot be sent by `B + skew` is not sent: `SKIPPED_LATE`, no sample. The published `source_time` is always `B`.
- **Interval attempt window.** A retry for an interval poll at `P` is sent only if `clock.now() < P + poll_period/2`; a poll whose first send would be at or after `P + poll_period/2` is `SKIPPED_LATE`.
- `state_skew_max_seconds` is measured in source time and is never scaled by the rate (D4). At rate 120 the 1 s send offset is 8.3 ms of wall time and the window 16.7 ms; Python 3.12 on Windows uses a high-resolution waitable timer for `time.sleep`, and the final spin removes the remainder, so one-machine runs fit. Cross-machine runs (TEL-08) use rate 12, where the window is 167 ms of wall time, and gate on measured clock offset.
- **Rates.** TEL-04 rate 120 over 2026-09-30T06:00Z-08:00Z; TEL-05 and TEL-05b rate 60; TEL-08 rate 12 over 2026-09-30T08:00Z-12:00Z.
- **Rejected:** lockstep clock driven by a control channel between poller and emulator (a device has no such channel, so it would test a path that cannot exist); scaling the skew allowance by the rate (it would weaken D4 for real devices); a larger `state_skew_max_seconds` in bench profiles (same weakening, hidden in data).

---

## TEL-01 · Shared core: profile, decode, clock, aggregate, report, publish · 1.0 d

**Files.** Creates `field/pyproject.toml`, `field/assetops_field/{__init__,profile,decode,clock,aggregate,report,publish}.py`, `field/tests/{field_fixtures,test_field_profile,test_field_decode,test_field_clock,test_field_aggregate,test_field_report,test_field_publish}.py`. Extends `tools/checks/module-roots.ps1` and `tools/checks/dependency-direction.ps1` (additive only).

**Approach.** Pure modules first, each with its own focused test, then `publish.py` against a fake IPC link. No Modbus code here.

**Interfaces.**

```python
# profile.py
@dataclass(frozen=True)
class RegisterRef: unit_id: int; function: int; address: int; type: str; word_order: str
    # property words -> 1 for 16-bit, 2 for 32-bit; property bits -> 16 or 32; property signed -> bool
@dataclass(frozen=True)
class CsvColumn: column: str
@dataclass(frozen=True)
class ProfileRow:
    row_id: str; status: str; source_document: str; device_id: str; signal_id: str; role: str
    source_unit: str; quantity: Mapping[str, str]; reading_class: str
    span_seconds: int | None; cadence_seconds: int; poll_period_seconds: int | None
    output_resolution: Fraction | None              # None only for ENUM rows
    registers: tuple[RegisterRef, ...] = ()         # empty for EXPORT_CSV rows
    decode: str | None = None                       # "NUMBER" | "ENUM"; None for CSV rows
    enum_map: Mapping[int, str] | None = None
    sentinels: frozenset[int] = frozenset()         # unsigned raw values
    scale_exponent: int | None = None; unit_exponent: int | None = None
    register_unit: str | None = None; register_quantum: Fraction | None = None
    csv: CsvColumn | None = None
    @property
    def word_count(self) -> int: ...   # sum of register words
    @property
    def exponent(self) -> int: ...     # scale_exponent + unit_exponent (NUMBER rows)
@dataclass(frozen=True)
class FieldProfile:
    profile_id: str; profile_version: int; status: str; interface: str; state_skew_max_seconds: int
    rows: tuple[ProfileRow, ...]; sha256: str; document: Mapping[str, Any]
class ProfileRefused(ValueError):
    def __init__(self, code: str, field: str, detail: str) -> None: ...   # sets .code .field .detail
PROFILE_CODES = ("SCHEMA_INVALID", "UNSUPPORTED_VALUE", "STATUS_INCONSISTENT", "POLL_PERIOD_NOT_DIVISOR",
                 "CADENCE_NOT_ALIGNED", "DUPLICATE_SIGNAL", "REPORT_KEY_TOO_LONG",
                 "RESOLUTION_FINER_THAN_QUANTUM", "SENTINEL_OUT_OF_RANGE")
def load_profile(path: Path) -> FieldProfile: ...        # UTF-8 JSON; parse errors -> SCHEMA_INVALID
def parse_profile(document: Mapping[str, Any]) -> FieldProfile: ...
def profile_sha256(document: Mapping[str, Any]) -> str: ...

# decode.py
@dataclass(frozen=True)
class Decoded:
    kind: str                 # "VALUE" | "SENTINEL" | "STATE"
    value: Fraction | None    # VALUE: in source_unit, exact
    state: str | None         # STATE: enum text
class DecodeFault(ValueError): ...    # config error: wrong word count, unmapped enum code
class EncodeRefused(ValueError):
    def __init__(self, code: str, detail: str) -> None: ...   # code "OUT_OF_RANGE" | "NOT_A_MULTIPLE" | "UNKNOWN_STATE"
def decode_words(row: ProfileRow, words_per_register: Sequence[Sequence[int]]) -> Decoded: ...
def encode_value(row: ProfileRow, value: Fraction | str) -> list[list[int]]: ...   # emulator only (Q-T15)
def encode_sentinel(row: ProfileRow) -> list[list[int]]: ...                     # first sentinel on every register

# clock.py
class Clock(Protocol):
    def now(self) -> datetime: ...
    def sleep_until(self, instant: datetime) -> None: ...
class WallClock:
    def __init__(self, *, wall: Callable[[], datetime] = ..., sleep: Callable[[float], None] = time.sleep) -> None: ...
class ReplayClock:
    def __init__(self, start: datetime, rate: int, wall_epoch: datetime, *,
                 wall: Callable[[], datetime] = ..., sleep: Callable[[float], None] = time.sleep) -> None: ...

# aggregate.py
class PollOutcome(Enum): VALUE = "VALUE"; NO_VALUE = "NO_VALUE"; FAILED = "FAILED"; NO_ANSWER = "NO_ANSWER"; CONFIG_FAULT = "CONFIG_FAULT"
@dataclass(frozen=True)
class Poll: at: datetime; outcome: PollOutcome; decoded: Decoded | None
@dataclass(frozen=True)
class Result:
    quality: str              # "GOOD" | "UNAVAILABLE"
    reason: str | None        # None | "NO_MEASUREMENT" | "NO_COMPLETED_INTERVAL"
    value: Fraction | str | None
    source_time: datetime; interval_start: datetime | None
def interval_bounds(row: ProfileRow, end: datetime) -> tuple[datetime, datetime]: ...
def expected_polls(row: ProfileRow, start: datetime) -> list[datetime]: ...   # start + (k + 1/2) * poll_period
def publish_instants(row: ProfileRow, after: datetime, until: datetime) -> list[datetime]: ...  # multiples of cadence in (after, until]
class IntervalAggregator:
    def __init__(self, row: ProfileRow, session_start: datetime, end: datetime) -> None: ...  # one span, ending at `end`
    def add(self, poll: Poll) -> None: ...   # poll.at must be one of expected_polls; duplicate or unknown instant, or add after close -> ValueError
    def close(self) -> Result | None: ...    # None = publish nothing
class StateSampler:
    def __init__(self, row: ProfileRow, skew_max_seconds: int) -> None: ...
    def sample(self, boundary: datetime, attempts: Sequence[Poll]) -> Result | None: ...

# report.py
def report_key(profile: FieldProfile, row: ProfileRow, source_time: datetime) -> str: ...
def build_report(profile: FieldProfile, row: ProfileRow, result: Result) -> DeviceReport: ...
def report_text(report: DeviceReport) -> str: ...   # device_report_text, then parse_device_report_text round trip asserted

# publish.py
OPS_USED = ("identity", "admit", "seal", "release_run", "diagnostics")
ADMISSION_CHUNK = 256          # below the gateway's 1024; a smaller chunk is always accepted
class IdentityMismatch(RuntimeError): ...
@dataclass
class GatewayPublisher:
    link: GatewayLink; snapshot_sha256: str; session_ref: str
    expected: Mapping[str, Any]   # the expect-identity document (0.6)
    def check_identity(self) -> dict[str, Any]: ...
    def admit(self, texts: Sequence[str]) -> list[dict[str, Any]]: ...
    def seal_and_release(self) -> dict[str, Any]: ...
    def release_previous(self, previous_ref: str) -> dict[str, Any]: ...
    def diagnostics(self) -> dict[str, Any]: ...
```

**Architecture notes.**
- `decode_words`: per register, combine words per `word_order` into an unsigned integer of the register's width. **Sentinel check first, on that unsigned value, for every register** (any sentinel register makes the row `SENTINEL`, Q-T14, Q-T41). Then two's complement for `int*`. Multi-register `NUMBER` rows sum the signed raw values exactly before scaling. `ENUM`: raw integer looked up in `enum_map`; a missing code raises `DecodeFault`. A word count that does not match the row raises `DecodeFault`.
- `encode_value` (Q-T15), emulator only: `NUMBER` rows: `raw = value / 10^exponent` must be an integer (`Fraction` denominator 1) else `EncodeRefused("NOT_A_MULTIPLE")`; `raw` must fit the type of the first register, and must not equal a declared sentinel, else `EncodeRefused("OUT_OF_RANGE")`; the whole raw value goes on the **first** register and 0 on every other register of a multi-register row (by contract, stated in the claim record). `ENUM` rows: `value` is the state text; reverse lookup in `enum_map` else `EncodeRefused("UNKNOWN_STATE")`. Quantization to the register is the emulator's job, before it calls `encode_value` (TEL-03). `encode_sentinel` writes the first sentinel on every register.
- Exact arithmetic: `Fraction(raw) * Fraction(10) ** row.exponent`. No float anywhere; a test greps the package for `float(`.
- `IntervalAggregator(row, session_start, end)`: `start = end − span`. `close()`: if `session_start > start` → `UNAVAILABLE`/`NO_COMPLETED_INTERVAL`; else compare the polls received against `expected_polls(row, start)` (exact instant equality; the poller passes the **scheduled** instant as `Poll.at` for interval polls, and passes only the final attempt's outcome, Q-T23): all N `VALUE` → `GOOD` with the exact mean `sum/N`, then `quantize_half_even(mean, row.output_resolution)` once; any `NO_VALUE` → `UNAVAILABLE`/`NO_MEASUREMENT`; no poll answered (`VALUE` or `NO_VALUE`) → `None`; otherwise (some answered, some `FAILED`/`NO_ANSWER`/`CONFIG_FAULT`/missing) → `UNAVAILABLE`/`NO_MEASUREMENT`. Interval boundaries are multiples of `span_seconds` from 00:00:00Z; spans are published only when their end is a multiple of `cadence_seconds` (cadence ≥ span; e.g. span 900, cadence 3600 means the poller polls only in the last 15 min of each hour).
- `StateSampler.sample(boundary, attempts)`: `attempts` carry their real send instant as `Poll.at`; attempts outside `[boundary, boundary + skew]` are ignored; the last remaining attempt decides: `VALUE`/`STATE` → `GOOD` (value or state text); `NO_VALUE` → `UNAVAILABLE`/`NO_MEASUREMENT`; anything else or no attempt → `None`. Source time is always `boundary`.
- `build_report`: `measurement = MEASUREMENT_OF_READING_CLASS[row.reading_class]` (`contracts/assetops_contracts/gateway_report.py:42`); `interval_start` set for every `INTERVAL_MEAN` including `UNAVAILABLE` (V3 requires it); `unit = row.source_unit`; numeric value text `exact_decimal_text(value)`; state value is the enum text; `report_key = f"{profile_id}:{profile_version}:{device_id}:{signal_id}:{source_time Z}"`.
- `GatewayPublisher.check_identity`: `identity` must match `expected`: `tenant_id`, `site_id`, `gateway_id`, `sequence_epoch` equal; `source_mode == "SIMULATED"`; every `row_sources` value in `permitted_source_ids`; else `IdentityMismatch` naming the first differing key. `identity` carries no snapshot SHA (`gateway/assetops_gateway/service.py:407-418`); the snapshot is checked by passing `snapshot_sha256` on every `admit`.
- `admit(texts)`: chunks of 256 to op `admit` with body `{"snapshot_sha256", "lab_run_ref": session_ref, "reports": [...]}`; returns the admission dicts verbatim. `HELD` admissions are data, never fatal (Q-T32). `GatewayUnavailable` propagates to the caller; `GatewayRequestRefused` (a whole-request refusal such as disk `STOP` or `NOT_PROVISIONED`) propagates and the poller exits 3.
- `seal_and_release()` (Q-T29): calls `seal`; a `GatewayRequestRefused` of kind `SEAL_REFUSED` is caught (the gateway has committed every other group), recorded, and `release_run(session_ref)` still runs; any other refusal propagates. Returns `{"batch_ids": [...], "seal_refused": "<detail>" | None, "released_batch_ids": [...], "released_now": n, "delivery": {...}}` (the last three verbatim from `release_run`, `service.py:1383-1410`). The poller exits 3 after three consecutive publish instants with `seal_refused`.
- `release_previous(previous_ref)` (Q-T28): **first `seal`, then `release_run(previous_ref)`, before any new `admit`.** Reason, verified in `service.py:996-1044` and `:1383-1410`, `:1645-1658`: `seal` groups every unbatched envelope of any run by (source, epoch, snapshot, state), and `release_run` skips any batch holding an envelope without that run's provenance. A poller killed between `admit` and `seal` leaves unbatched envelopes; if the new session admitted first, the next `seal` would mix old and new envelopes in one batch that neither reference can release. Sealing first gives the old envelopes batches of their own, which `release_run(previous_ref)` releases. `SEAL_REFUSED` here: exit 3. Returns `{"sealed_batch_ids", "released_batch_ids", "released_now"}`.
- **Session reference (D4 item 6, amended, Q-T34):** `field:<profile_id>:<profile_version>:<session wall start, YYYYMMDDTHHMMSSZ>:<8 lowercase hex from secrets.token_hex(4)>`. Wall time, not replay time, plus a random suffix, so a restart within one second never repeats a reference. On start the poller reads `<state-dir>/session.json`; if present it calls `release_previous(old_ref)`; then it writes the new `session.json`.
- Checks: `module-roots.ps1` required dirs `field`, `field/assetops_field`, required files `field/pyproject.toml`, `field/assetops_field/__init__.py`. `dependency-direction.ps1` new section exactly as D4 "What must change in tools/checks", with the reverse rule on **non-test** host modules only and no change to the existing host counts (amendment 2 item 2).

**Test seams.** `field_fixtures.py` holds `profile_document(**overrides)`, `row_document(**overrides)`, `FakeLink` (records `(op, body)` and returns scripted bodies or raises), `FakeWall` (settable instant) and `RecordingSleep`. `test_field_clock.py` drives `ReplayClock` and `sleep_until` with `FakeWall` and a sleep that advances it: no real sleeping.

**Rejected alternatives.**
- Float scaling with rounding: produces non-decimal values and silent drift; exact `Fraction` is required by D4.
- A second rounding helper: duplicates `quantize_half_even` with possibly different semantics.
- Profile in YAML: needs a non-stdlib parser; JSON is stdlib and canonicalisable.
- Publisher calling `deliver`: forbidden by D4; upload is the gateway's background uploader.
- Polls on the span edges (`start + k × period`): a millisecond of clock offset reads the neighbouring interval (Q-T27).

**Acceptance gates.**
- Decoder vectors: `FF9C` int16 × 0.1 = −10; `7FFF` declared sentinel → `SENTINEL`; int16 sentinel `[32768]` with word `8000` → `SENTINEL`; `0001 86A0` uint32 BIG × 0.001 = 100; `86A0 0001` LITTLE = 100; three uint16 registers `03E8 0000 FFFF` with sentinel 65535 → `SENTINEL`; `03E8 0001 0002` × 0.001 = 1.003; `encode_value` then `decode_words` round trip for every row of `-1` and `-2`; `EncodeRefused` for 65.536 kW on a uint16 W row and for 0.0005 kW.
- **Card correction (D10):** an interval missing one expected poll → `UNAVAILABLE`/`NO_MEASUREMENT` with span; the session's first interval → `NO_COMPLETED_INTERVAL` with span; a fully failed interval → `None`; N = 3 with values 1, 1, 2 (mean 4/3) quantized once to `0.001` gives `1.333`; `expected_polls` for span 900, period 300 starting 06:00:00Z are 06:02:30Z, 06:07:30Z, 06:12:30Z.
- State: attempt at `B+1` → `GOOD`; attempt at `B+3` with skew 2 → `None`; failed first attempt then good retry at `B+2` → `GOOD`.
- Every report text round-trips through `parse_device_report_text`; profile SHA unchanged under key reordering; every code in `PROFILE_CODES` has one test.
- `FakeLink` sees only `OPS_USED`; `release_previous` sends `seal` before `release_run`; `seal_and_release` survives a scripted `SEAL_REFUSED`.
- Both `.ps1` checks green; `gateway/tests/test_wire_contracts.py` green.

**Stop.** A field rule cannot be written without editing an existing rule; or the exact-decimal helper would need to differ from `exact_decimal_text`.

---

## TEL-02 · Read-only Modbus TCP client · 0.5 d

**Files.** `field/assetops_field/modbus_tcp.py`, `field/tests/test_field_modbus_tcp.py`.

**Interfaces.**

```python
READ_FUNCTIONS = frozenset({1, 2, 3, 4})
MAX_REGISTERS = 125            # FC 03/04 per request
class WriteForbidden(ValueError): ...
@dataclass(frozen=True)
class ReadResult:
    kind: str                       # "WORDS" | "EXCEPTION" | "NO_ANSWER"
    words: tuple[int, ...] = ()
    exception_code: int | None = None
    no_answer: str | None = None    # "TIMEOUT" | "REFUSED" | "RESET" | "UNIT_MISMATCH" | "TID_MISMATCH"
    request: bytes = b""; response: bytes | None = None
class ModbusTcpClient:
    def __init__(self, host: str, port: int, *, timeout_s: float = 1.0) -> None: ...
    def read(self, unit_id: int, function: int, address: int, count: int) -> ReadResult: ...   # exactly one transaction
    def close(self) -> None: ...
def requests_for(row: ProfileRow) -> list[tuple[int, int, int, int]]: ...   # (unit_id, function, address, count)
def classify(results: Sequence[ReadResult], row: ProfileRow) -> tuple[PollOutcome, Decoded | None]: ...  # the 0.7 table, one place
```

**Approach.** stdlib `socket`, one persistent connection, reconnect on the next read after any `NO_ANSWER`. MBAP header built with `struct`; transaction ID starts at 1 and increments mod 65536. `read` validates `function in READ_FUNCTIONS` before opening or writing anything (raises `WriteForbidden`). **No retries in the client** (Q-T21): it is a single-transaction primitive; the poller owns the retry. Function 1/2 responses decode bits to words of 0/1 (not used in October profiles, kept for the RTU later).
- `requests_for` (Q-T13): one request per row when its registers are contiguous: same `unit_id`, same `function`, and `address[i+1] == address[i] + words[i]`, total ≤ 125 words; otherwise one request per register. Rows are never merged with each other.
- `classify` (Q-T22) splits the returned words per register by `RegisterRef.words`, calls `decode_words`, and applies 0.7 with its precedence. It imports `ProfileRow` from `profile`, `decode_words`, `Decoded`, `DecodeFault` from `decode`, and `PollOutcome` from `aggregate` (no import cycle: none of those import `modbus_tcp`).

**Test seam.** An in-test `socketserver` that records every received byte and replies from a script. No pymodbus.

**Rejected.** pymodbus as the client: would put a third-party dependency in non-test field code against D4. Async client: one poller per gateway and sequential reads are enough at these cadences.

**Acceptance gates.** FC 05, 06, 15, 16, 23 raise before any byte (server records 0 bytes). Request frames, transaction ID 1 (Q-T5; Figure 2a of `AssetOpsHardwareIntegrationPack\modbustcp.html:449` is the FC 04 case, unit 1, address 0, count 2):

| Case | Request bytes (hex) |
|---|---|
| Figure 2a, FC 04 unit 1 address 0 count 2 | `00 01 00 00 00 06 01 04 00 00 00 02` |
| FC 03, same | `00 01 00 00 00 06 01 03 00 00 00 02` |
| FC 02, same | `00 01 00 00 00 06 01 02 00 00 00 02` |
| FC 01, same | `00 01 00 00 00 06 01 01 00 00 00 02` |
| Profile `-1` PV, FC 03 unit 100 address 808 count 3 (Q-T38) | `00 01 00 00 00 06 64 03 03 28 00 03` |

Response `00 01 00 00 00 07 01 04 04 00 7B FF 9C` (Figure 2b) gives words `(0x007B, 0xFF9C)`; exception `00 01 00 00 00 03 01 84 02` (Figure 2c) gives `EXCEPTION 02`. Exception responses 01/02/03/04/06/0A/0B map through `classify` to the 0.7 table; TID and Unit ID mismatch → `NO_ANSWER`; a silent server → `NO_ANSWER TIMEOUT` after `timeout_s`, and the client sends nothing more.

**Stop.** Any need for a write function code.

---

## TEL-03 · GX-shaped emulator, profile `-1` and pinned JSONL · 0.75 d

**Files.** `field/tests/field_emulators/{__init__,gx_server}.py`, `field/tests/test_field_gx_emulator.py`, `field/profiles/gx-system-illustrative-1.json`, `host/tests/field_observation_fixtures.py`, `host/tests/test_field_observation_fixtures.py`, `contract-fixtures/telemetry/kobo-public-observations-v1/{observations.jsonl,manifest.json}`, the `.gitattributes` line (0.2).

**JSONL generator (host/tests, Q-T45).** `generate_daytime_fixture(out_dir: Path) -> dict` (returns the manifest): `store, _, _ = registered.converted()`; `draft = registered.setup_service(store).create_draft_run(registered.request())` (KOBO-001, `kobo-daytime`, 2026-09-30T03:00Z-15:00Z, timestep 15, seed 20260929; no overrides), exactly as the `draft` fixture of `host/tests/test_registered_gateway_publication.py`; then `port = HostLabExecution(artifacts=YamlExecutionArtifacts(root), stages=JsonSourceStages(root / "stages"), gateway=None)`, `port.start(draft)`, `assert port.run_to_end(draft).status == "COMPLETED"`, `session = port._sessions[draft.run_id]`, `observations = generate_observations(session.execution.boundaries, session.reporting)` (as `:143` and `:182`, "executes, but stages nothing"). No gateway process, so the freshness test is light. It writes only public fields (0.6). The freshness test regenerates into `tmp_path` and asserts byte equality with the checked-in file and the manifest SHA. It also asserts each `-1` row's `reading_class`, `span_seconds` and `cadence_seconds` equal the publication profile's declaration for that signal (`cadence_minutes × 60`; span = cadence for interval signals), so the profile cannot drift from the run it replays.

**Profile `-1` rows (D5).** `pv-ac-output` (808-810 as in 0.6, span 900, cadence 900, poll period 300, Q-T12) bound to `pv-inverter-controller/ac-power` role `pv_power`; `battery-soc` (unit 100, FC 3, 843, uint16, `register_unit "%"`, `scale_exponent 0`, `unit_exponent 0`, `register_quantum "1"`, `output_resolution "1"`, sentinels `[65535]`, `STATE_SIGNAL`, cadence 900; `quantity {"kind": "STATE_OF_CHARGE", "point": "battery bank as reported by the system", "sign": "not applicable", "phase_aggregation": "SINGLE_REGISTER"}`) bound to `battery-pcs-controller/state-of-charge` role `battery_soc`. Nothing else: no 842, no 817-819.

**Representability (Architect amendment, replaces the TEL-03 "do not round in the emulator" stop for GX rows).** Registered Kobo values are published at resolution `0.000001` in their canonical unit (`backend/assetops_backend/runs/profiles.py:1826`). A uint16 W or % register cannot hold them. The emulator models the device's register resolution: for each GX-layout row it presents `quantize_half_even(value / 10^(scale_exponent + unit_exponent), register_quantum)` as the raw value (with exponent 0 for `%` and −3 for `W`), and the TEL-03 equality is against that quantized value. The claim record says "values presented at the register's resolution (1 W, 1 %)". The stop fires only on **range** (`EncodeRefused("OUT_OF_RANGE")`, for example PV above 65.534 kW) or on `RESOLUTION_FINER_THAN_QUANTUM`. The builder may measure the maxima first: the emulator test prints the maximum PV kW and SoC % in the window and the packet records them (Q-T16). Illustrative block rows (TEL-05b) use int32 with exponent −6 and are never quantized.

**Emulator design (stdlib server, Q-T37).**
```python
STATE_LEAD_SECONDS = 1
class ObservationTimeline:
    def __init__(self, jsonl: Path, profile: FieldProfile) -> None: ...
        # refuses (ValueError) a profile row with no observation in the file, or whose source_unit differs
        # from the observations' canonical_unit (Q-T42)
    def registers_at(self, source_instant: datetime) -> dict[tuple[int, int], int | tuple[str, int]]: ...
        # (unit_id, address) -> word, or ("EXCEPTION", code)
@dataclass(frozen=True)
class FaultWindow:
    start: datetime; end: datetime            # source time, half-open [start, end)
    kind: str                                 # "PAUSE" | "EXCEPTION" | "SENTINEL" | "WRONG_UNIT_ID" | "WRONG_TID"
    row_id: str | None = None; code: int | None = None   # EXCEPTION: row and exception code; SENTINEL: row
class GxEmulator:
    def __init__(self, timeline: ObservationTimeline, clock: Clock, *, host: str, port: int,
                 faults: Sequence[FaultWindow] = ()) -> None: ...
    def start(self) -> int: ...      # returns the bound port; socketserver.ThreadingTCPServer in a daemon thread
    def stop(self) -> None: ...
    faults: list[FaultWindow]        # mutable in-process; evaluated against clock.now() per request
    writes: int                      # any write FC (05, 06, 15, 16, 23) increments this and answers exception 01
def main(argv=None) -> int: ...
    # CLI: --jsonl --profile --host --port --replay-start --replay-rate --replay-wall-epoch [--stop-at]
    # prints "READY <host>:<port>" (flush) once bound; runs until SIGINT/Ctrl-C or source time >= --stop-at; exit 0.
    # No fault flags: faults are in-process only (Q-T43).
```
- **Framing.** The server parses MBAP (7 bytes, length check) and PDU itself; it serves FC 03 and 04 from the timeline, answers exception 01 to any other function, exception 02 to an address no profile row declares, exception 0B to a unit ID no profile row declares, and exception 03 to a count of 0 or more than 125. Unit IDs come from the profile (Q-T43). `PAUSE` accepts and reads but never answers; `WRONG_UNIT_ID` answers with unit + 1; `WRONG_TID` answers with TID + 1; `EXCEPTION` answers the code for any request covering the row's registers; `SENTINEL` serves `encode_sentinel(row)`.
- **Value-at-instant rule.** A `STATE_SIGNAL` observation at `T` holds over `[T − STATE_LEAD_SECONDS, T_next − STATE_LEAD_SECONDS)`; the one-second lead means a poller that samples at `B + 1` tolerates an emulator clock up to 2 s behind (Q-T27). An `INTERVAL_SIGNAL` observation with source time `T` and span `S` is held constant over `[T − S, T)`. Outside any span, before the first observation and after `last state observation + cadence`, the registers hold the row's sentinel (Q-T26, Q-T42).
- **Outcome mapping (Q-T39).** `REPORTED` → encoded value; `NO_VALUE_AT_BOUNDARY` and `NO_PRECEDING_INTERVAL` → sentinel over that observation's hold period (a whole cadence for state, the whole span for intervals); `SUPPRESSED_BY_GAP` and `DROPPED` → exception 0B for that row's registers over that observation's hold period (no answer, so nothing is published, which matches "not published"). The emulator path therefore reports `NO_MEASUREMENT` where the simulator published `NO_COMPLETED_INTERVAL`; that difference is expected and is allowed at the aggregator layer in TEL-04/05 (Q-T40), not in TEL-03.
- **Phase split.** The whole PV value on 808, zero on 809 and 810 (exact and stated), by `encode_value`'s contract. The emulator uses `encode_value` and `encode_sentinel` from `decode.py` so encoding and decoding cannot disagree silently.

**Rejected.** Reading observations in-test from the simulator (field/tests may not import the simulator, D4). The pymodbus server (Q-T37): it writes into its datastore and silently ignores unknown unit IDs, so the never-answer, wrong-TID, wrong-unit and per-address-exception faults and the write counter would each need a hook into its internals; the stdlib server does them natively. pymodbus stays as the independent conformance check, used as a **client** against this server.

**Acceptance gates (Q-T40).** With a `ReplayClock` on a `FakeWall` set per case (no real time): for every observation in the window, the TEL-02 client read at `T − S/2` (interval) or `T` (state), decoded through profile `-1`, equals exactly the quantized value (`REPORTED`), `SENTINEL` (`NO_VALUE_AT_BOUNDARY`, `NO_PRECEDING_INTERVAL`) or `EXCEPTION 0B` (`DROPPED`, `SUPPRESSED_BY_GAP`). The pymodbus 3.16.1 `ModbusTcpClient` reads 808-810 and 843 at three instants and gets the same words as the TEL-02 client. Each `FaultWindow` kind gives its 0.7 outcome through `classify`; `writes == 0` after the suite except in the one test that sends a write frame by raw socket and asserts exception 01 and `writes == 1`. JSONL freshness green.

**Stop.** A value the emulator needs is not in the public observations; a range overflow; pymodbus 3.16.1 not installable (then the cross-check is skipped and recorded as a deviation).

---

## TEL-04 · Poller and focused end-to-end through a real gateway process · 1.0 d

**Files.** `field/assetops_field/modbus_poller.py`, `host/tests/test_field_modbus_tcp_proof.py`, the stdlib part of `host/tests/field_bench.py` (`expect_identity_from_snapshot`, `cohort_members`).

**CLI.**
```
python -m assetops_field.modbus_poller --profile <json> --host <h> --port <p>
    --gateway-address <ipc address> --ipc-credential <gateway.credential> --snapshot-sha256 <hex>
    --expect-identity <json file> --state-dir <dir> [--read-timeout-s 1.0]
    [--replay-start <Z> --replay-rate <n> --replay-wall-epoch <Z> --stop-at <Z>]  (all four together)
    [--stop-at <Z>]                                                              (wall mode, optional)
```
Exit codes: 0 after `--stop-at` and a final `seal_and_release`; 2 configuration refused (`ProfileRefused`, `IdentityMismatch`, bad arguments, replay without `--stop-at`); 3 admission refused (`GatewayRequestRefused` other than `SEAL_REFUSED`, three consecutive `SEAL_REFUSED`, or `SEAL_REFUSED` in `release_previous`); 4 gateway unavailable at 10 consecutive publish instants, or the retained-report queue over 4096 texts (Q-T33).

**Output (Q-T36).** stdout, one line each, flushed: `FIELD-POLLER START <canonical JSON {"profile_id","profile_version","profile_sha256","clock":{...},"session_ref","session_start","previous_ref"}>` after `release_previous`; `FIELD-POLLER HOLD <canonical JSON {"report_key","kind","field","detail"}>` per hold; `FIELD-POLLER EXIT <code> <canonical JSON of the final status file>`. Refusal details go to stderr.

**Loop.**
1. Load profile (exit 2 on refusal); build the clock; `check_identity` (exit 2); `release_previous` if `session.json` exists; write `session.json`; determine `session_start` (0.8); print START.
2. Build the schedule up to `--stop-at`: state boundaries at multiples of `cadence_seconds`; interval poll instants per 0.8 inside each published span after `session_start`; publish instants = every state boundary and every interval span end. Rows in `faulted_rows` drop out of the schedule.
3. At each poll instant, in profile row order: for each due row, send `requests_for(row)` (first attempt at the instant, or `B + 1` for state), append a raw-capture line per attempt, `classify`, retry once per 0.7/0.8 if allowed, feed the final outcome to the interval aggregator (with the scheduled instant) or every attempt to the state sampler (with send instants). A row whose first send falls outside its window is `SKIPPED_LATE`.
4. At each publish instant: close the due aggregators and samplers; build reports for every non-`None` result; order them by `(source_time, row order)`; prepend the retained texts from earlier unavailable instants (oldest first), so each source's sequence follows source-time order (the cohort's `SEQUENCE_ORDER_INVERTED` rule, `backend/assetops_backend/analytics/cohort.py:16-19`); `admit` them, then `seal_and_release`; update counters; rewrite the status file. On `GatewayUnavailable` keep all texts, in order, for the next publish instant (same keys, so the gateway answers `ALREADY_ADMITTED` for any that did land).
5. After `--stop-at`: a final `seal_and_release`; print EXIT; exit 0.
- **Crash hook for the restart gate (Q-T28).** If the environment variable `ASSETOPS_FIELD_CRASH_AFTER_ADMIT=<n>` is set and the identity's `source_mode` is `SIMULATED`, the poller calls `os._exit(9)` right after the n-th `admit` call returns, before `seal`. With any other source mode the variable makes the poller exit 2 at start.

**Test harness (host/tests).** File header: `sys.path.insert` of `backend/tests`, `gateway/tests`, `field/tests` (0.5). Snapshot from the registered daytime draft (`snapshot_canonical`); `snapshot_sha256 = sha256(snapshot_text.encode("utf-8"))` (`gateway/assetops_gateway/snapshot.py:221`); `write_config` + `provisioning_from_snapshot` (epoch `epoch-1`); upload block `{"server_url": central.url, "upload_credential_file": "upload.credential", "ca_file": str(CERT), "interval_seconds": 3600}` so the background pass stays away and the harness drives upload with `deliver` (Q-T46, the `test_s6_verification_publication.py:262-267` pattern; the upload credential written and `restrict_to_current_user`'d as there). `GatewayProcess` creates and protects `gateway.credential` itself (`ensure_credential`), and the poller subprocess runs as the same user, so it can read it (Q-T70). Activation: the harness sends one `activate` over `process.link` with `{"snapshot_text": ..., "claimed": claimed_references(basis)}` (`host/gateway_publication.py:96`, `:163`). Expect-identity written by `expect_identity_from_snapshot(snapshot_text, profile_document, "epoch-1")`. Emulator in-process (`GxEmulator` on port 0, `ReplayClock` with the same arguments); poller as a subprocess `[sys.executable, "-m", "assetops_field.modbus_poller", ...]` with the PYTHONPATH of 0.1 and `--read-timeout-s 0.25`; rate 120 over 2026-09-30T06:00Z-08:00Z; `--replay-wall-epoch` = now + 5 s. After the poller exits the harness calls `deliver` (`{"max_batches": 50}`) until `batches.attempted == 0` (the harness may; the adapter may not), then reads `FakeCentral.requests` and `diagnostics`.

**FakeCentral responder.** `lambda path, headers, body: (200, receipt_text(body.decode("utf-8")))`; for the drop case the responder returns `DROP` for the first two requests, then the normal answer.

**Test functions (each with its own gateway state dir).**
1. `test_clean_window_lands_acknowledged`: clean run; gates 1, 6, 9, 10, 11 below. The DROP responder is installed before the first `deliver` of this test, so the first two POSTs drop and the retries succeed (gate 6).
2. `test_faults_follow_the_table`: one run with `FaultWindow`s: `SENTINEL` on `pv-ac-output` 06:15Z-06:45Z; `EXCEPTION 02` on `battery-soc` 06:45Z-07:15Z; `PAUSE` 07:15Z-07:30Z (all rows); `WRONG_TID` 07:30Z-07:45Z. Gates 2, 7, 8.
3. `test_unit_w_is_held_and_conflicts_are_held`: profile copy with `pv-ac-output.source_unit = "W"`, window 06:00Z-06:30Z → gate 3; then in-process `GatewayPublisher` re-admits one admitted report text unchanged (gate 4: `ALREADY_ADMITTED`, same `message_id`) and one with the same key and another value (gate 5: `HELD CONFLICTING_REPORT`).
4. `test_restart_releases_the_killed_session`: run with `ASSETOPS_FIELD_CRASH_AFTER_ADMIT=3` (exit code 9), then restart the poller with the same arguments and state dir (gate 12).

**Acceptance gates (card list quoted, with corrections; Q-T6).**
1. Every admitted envelope is acknowledged with a 200 receipt.
2. Sentinel and exception 02 produce `UNAVAILABLE`/`NO_MEASUREMENT` envelopes, not holds.
3. A profile unit edited to `W` produces `UNIT_INCOMPATIBLE` holds with no sequence allocated; the poller continues and exits 0 (holds are not fatal, Q-T32); `holds_by_kind == {"UNIT_INCOMPATIBLE": n}`.
4. A repeated poll (same report text) reuses the same message ID (`ALREADY_ADMITTED`).
5. The same key with other content is held `CONFLICTING_REPORT`.
6. An uplink failure (`FakeCentral` `DROP`), then recovery, posts byte-identical bodies, and `FakeCentral` records them (the dropped and the retried request of each batch have equal `body` bytes).
7. **Card correction:** a paused emulator produces no admitted report for the paused boundaries, and contact age grows in `diagnostics` (Q-T69): the harness reads `diagnostics` at wall times just before and ≥ 3 s after the pause starts; for the paused sources `source_contacts[].last_contact_at` is unchanged and `observed_at − last_contact_at` grew by ≥ 2 s. This measures real wall seconds by design (contact is stamped on admit, `service.py:685`); no `inject_fault` is used.
8. Status-file counters match the injected faults (expected counts computed by the test from the fault windows and the schedule).
9. The emulator write counter is 0.
10. The gateway refuses nothing in the snapshot (activation succeeds unchanged).
11. The first interval after the session start (06:00Z replay start, epoch in the future) is `GOOD`, not `NO_COMPLETED_INTERVAL`.
12. Restart: the first interval after the restart is `NO_COMPLETED_INTERVAL` with its span; `START` names `previous_ref`; and no stranded batch: after the gateway is stopped, its SQLite (read-only) has no `upload_batch` in `STAGED` and no unbatched `envelope_outbox` row in `STAGED`/`READY`.

**Rejected.** Running the poller in-process (it would not prove the CLI, the IPC client process boundary or restart behaviour). A separate emulator process in focused tests (fault switches need in-process control; the CLI form is exercised in TEL-08). Batching every N publish instants (Q-T30): seal-and-release at every publish instant is intended; it bounds what a crash can leave unsealed to one instant.

**Stop.** Activation refused; any gateway/backend change seems needed; an unexpected hold kind (report with the hold row).

---

