# Build spec, telemetry lane (Lane T), 2026-10-27

Architect: Claude (`.ai/ROLE_CONFIG.md` line 9). Owner instruction on depth, verbatim: `.agent/owner-build-plan-depth-2026-10-27.md`. Index and calendar: `.agent/build-sequence-2026-10-27.md`.

This file is what Lane T builders are briefed from. It settles every design choice a builder would otherwise make. If something here is missing or wrong, it is a pre-flight question, not a builder decision (see "Implementer questions and resolutions" at the end).

**Authority order:** this file, then `.agent/telemetry-rulings-2026-10-27.md` (D4, D10, D5, D6 and both amendments), then `Docs/demo-sprint/telemetry-integration-plan-claude.html` rev 3 §10 cards. Where this file corrects a card, the correction is marked **Card correction**.

---

## 0. Lane rules (every task)

### 0.1 Worktree, branch and environment

- Worktree `C:\Users\assef\Bineyame\AssetOpsV1-tel`, created from `main`. One branch per task group: `task/TEL-01-field-core` (TEL-01..03), `task/TEL-04-poller` (TEL-04..05), `task/TEL-08-bbb` (TEL-08, TEL-05b, TEL-07), `task/TEL-06-csv`.
- Python: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`.
- **PYTHONPATH (put this line at the top of the first task file and of every packet):**

  PowerShell:
  ```
  $env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-tel\backend;C:\Users\assef\Bineyame\AssetOpsV1-tel\contracts;C:\Users\assef\Bineyame\AssetOpsV1-tel\simulator;C:\Users\assef\Bineyame\AssetOpsV1-tel\gateway;C:\Users\assef\Bineyame\AssetOpsV1-tel\host;C:\Users\assef\Bineyame\AssetOpsV1-tel\field;C:\Users\assef\Bineyame\AssetOpsV1-tel"
  ```
  The shared venv's editable installs point at `C:\Users\assef\Bineyame\AssetOPsV1` (feasibility §2.3). Without this line every test silently runs the main checkout's code. Open a new terminal per task, and print `python -c "import assetops_gateway,sys;print(assetops_gateway.__file__)"` once; it must name the `-tel` worktree.
- Never `pip install -e field`. `pymodbus==3.16.1` is installed into the shared venv once by the coordinator before TEL-03.
- Test command form: `<python> -m pytest <file> -q -p no:cacheprovider`.

### 0.2 What Lane T must not touch

`backend/assetops_backend/**`, `backend/migrations/**`, `frontend/**`, `gateway/**`, `contracts/**`, `simulator/**`, host product modules (`host/*.py`), `tools/*.py`, any `tools/checks` file except additive sections in `module-roots.ps1` and `dependency-direction.ps1`, and `.agent/mock-departure-register.md`. No dev server and no browser capture. Stop and ask on any need to cross this line.

### 0.3 Heavy-job queue

Lane T has first claim until 30 October 23:59. Heavy: every Postgres test (run alone), TEL-04 and TEL-06a end-to-end files (one file at a time, never during a capture or full suite), the TEL-08 bench run. Light: `field/tests`, the two `.ps1` checks, `gateway/tests/test_wire_contracts.py`. Ask the coordinator for the queue slot before any heavy job.

### 0.4 Ports (fixed in TEL-00)

| Port | Use |
|---|---|
| 5020 | GX-shaped emulator, Modbus TCP (runbook and TEL-08). Tests bind an ephemeral port (port 0) and pass it to the poller. |
| 8443 | `serve_tls` for the runbook and TEL-08 only. Tests use `FakeCentral`, whose port is ephemeral. |
| Gateway IPC | Named pipe on Windows, Unix socket on Linux (`host/tests/gateway_process.py:20-23`). No TCP port. |

Commercial dev servers use 5173 and 8000; none of the above overlaps them. Port 7000 (RTU over TCP) is unused in October.

### 0.5 Module map (what exists when the lane is done)

```
field/
  pyproject.toml                     requires-python >=3.12; dependencies = []; extras dev=[pytest>=8.0, pymodbus==3.16.1], serial=[pyserial]
  assetops_field/
    __init__.py                      empty marker, version string only
    profile.py                       FieldProfile, ProfileRow, load_profile, ProfileRefused
    decode.py                        decode_words, Decoded, DecodeFault
    clock.py                         Clock protocol, WallClock, ReplayClock
    aggregate.py                     PollOutcome, IntervalAggregator, StateSampler
    report.py                        build_report, report_key
    publish.py                       GatewayPublisher, IdentityMismatch
    modbus_tcp.py                    ModbusTcpClient, ReadResult, WriteForbidden
    modbus_poller.py                 CLI and Poller loop
    export_csv.py                    (TEL-06) CsvCollector
  profiles/
    gx-system-illustrative-1.json    TEL-03
    gx-system-illustrative-2.json    TEL-05b
    generic-interval-csv-illustrative-1.json   TEL-06
  tests/
    field_fixtures.py                shared helpers (no conftest.py)
    test_profile.py, test_decode.py, test_aggregate.py, test_report.py, test_publish.py, test_clock.py
    test_modbus_tcp.py               TEL-02, stdlib in-test socket server
    emulators/__init__.py
    emulators/gx_server.py           TEL-03, pymodbus 3.16.1
    test_gx_emulator.py
    test_export_csv.py               TEL-06
contract-fixtures/telemetry/
  kobo-public-observations-v1/       TEL-03: observations.jsonl + manifest.json
  kobo-prolonged-public-observations-v1/   TEL-05b
  generic-interval-csv-v1/           TEL-06
host/tests/
  field_observation_fixtures.py      generators for both JSONL fixtures (imported by the freshness tests)
  test_field_observation_fixtures.py freshness tests for both JSONL fixtures
  test_field_modbus_tcp_proof.py     TEL-04 focused E2E (GatewayProcess + FakeCentral)
  test_field_modbus_tcp_acceptance_postgres.py   TEL-05 and TEL-05b (two tests, each its own fresh database)
  field_bench.py                     TEL-08 bench helper: `setup` (laptop) and `activate` (board)
  test_field_export_csv_proof.py     TEL-06a
```

Dependency rule (D4, amendment 2 item 2): non-test `field/` imports stdlib, `assetops_contracts.*` and `assetops_gateway.ipc` only. `field/tests` may add `pymodbus` and import `assetops_field`. `host/tests` may import `assetops_field`; nothing else does.

### 0.6 Shared data shapes

**Field profile document (`assetops.field-profile` version 1).** JSON. Its SHA-256 is `hashlib.sha256(canonical_json(document).encode()).hexdigest()` using `assetops_contracts.source_envelope.canonical_json` (sorted keys, so key order cannot move it).

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

Field rules (`load_profile` refuses with `ProfileRefused(code, field, detail)`; codes in brackets):
- `status` and each row `status` in `PINNED | UNPINNED | ILLUSTRATIVE`. The profile `status` must equal the weakest row status, ordered `PINNED > UNPINNED > ILLUSTRATIVE` [`STATUS_INCONSISTENT`].
- `interface` in `MODBUS_TCP | EXPORT_CSV`. `source_timestamps` must be `UTC_Z_REQUIRED`, `coverage` must be `ALL_EXPECTED_POLLS` in October [`UNSUPPORTED_VALUE`].
- `decode` in `NUMBER | ENUM`. `ENUM` needs `enum_map` (string of integer code to state text) and exactly one register; `NUMBER` forbids `enum_map` [`SCHEMA_INVALID`].
- `type` in `int16 | uint16 | int32 | uint32`. A 32-bit type occupies two consecutive addresses; the row lists the first address only and the decoder reads two words. `word_order` `BIG` (high word first, `AB CD`) or `LITTLE` (`CD AB`) [`SCHEMA_INVALID`].
- More than one register in a `NUMBER` row means an exact sum of the decoded registers (phase sum); `phase_aggregation` must then be `EXACT_SUM_*` [`SCHEMA_INVALID`].
- Value = `raw × 10^(scale_exponent + unit_exponent)` in `source_unit`, as `Fraction`. Both exponents are integers [`SCHEMA_INVALID`].
- `register_quantum` (in `register_unit`) and `output_resolution` (in `source_unit`) are finite decimal strings accepted by `assetops_contracts.observation.device_resolution` [`SCHEMA_INVALID`].
- `reading_class` `STATE_SIGNAL` (needs `cadence_seconds`; forbids `span_seconds`, `poll_period_seconds`) or `INTERVAL_SIGNAL` (needs all three; `poll_period_seconds` divides `span_seconds` exactly [`POLL_PERIOD_NOT_DIVISOR`]; `span_seconds <= cadence_seconds`).
- `(device_id, signal_id)` unique across rows [`DUPLICATE_SIGNAL`]. Report key length at most 192 characters for the longest source time [`REPORT_KEY_TOO_LONG`].

**Raw capture line** (one JSON object per Modbus transaction, appended to `<state-dir>/raw-<session>.jsonl`): `{"at": source instant Z, "wall_at": wall instant Z, "unit_id", "function", "address", "count", "request_hex", "response_hex" (null on no answer), "sha256" (of request||response bytes), "outcome": "WORDS|EXCEPTION_<hh>|NO_ANSWER_<kind>", "profile_sha256"}`.

**Status file** (`<state-dir>/status.json`, rewritten atomically after every boundary): `{"profile_id", "profile_sha256", "clock": {"mode": "WALL|REPLAY", "start", "rate", "wall_epoch"}, "session_ref", "counters": {"VALUE", "NO_VALUE", "FAILED", "NO_ANSWER", "CONFIG_FAULT"}, "admissions": {"ADMITTED", "ALREADY_ADMITTED", "HELD"}, "last_boundary", "faulted_rows": [row_id...]}`.

**Pinned JSONL fixture.** `observations.jsonl`: one canonical JSON object per public `DeviceObservation`, fields exactly as the dataclass (`device_id`, `signal_id`, `reading_class`, `source_sample_time`, `outcome`, `reported_value` as exact decimal text or state text or null, `canonical_unit`), ordered by `(source_sample_time, device_id, signal_id)`. `manifest.json`: `{"generator": "host/tests/field_observation_fixtures.py:<function>", "scenario", "window", "publication_profile", "timestep_minutes", "observation_count", "sha256"}`. Public observations only; nothing private crosses (no run cause, no kernel state).

### 0.7 Fault semantics (single table every module follows)

| Poll result (TEL-02 `ReadResult`) | `PollOutcome` | State boundary publishes | Interval (D10) |
|---|---|---|---|
| Words decoded to a value | `VALUE` | `GOOD` with the value | counts as answered |
| Words equal a declared sentinel; or exception 02 | `NO_VALUE` | `UNAVAILABLE` / `NO_MEASUREMENT` | interval becomes `UNAVAILABLE` / `NO_MEASUREMENT` |
| Exception 04 or 06 after the one retry | `FAILED` | nothing (no sample) | missing poll: `NO_MEASUREMENT` if any poll was answered |
| Timeout, refused, reset, exception 0A or 0B, Unit ID or transaction ID mismatch (after the one retry for timeout) | `NO_ANSWER` | nothing | missing poll; if no poll answered, nothing |
| Exception 01 or 03, a decode type mismatch, an unmapped enum code | `CONFIG_FAULT` | nothing; row added to `faulted_rows` and no longer polled this session | as `NO_ANSWER` for that interval, then the row stops |

The first boundary of a session, and the first after a poller restart, gives `UNAVAILABLE` / `NO_COMPLETED_INTERVAL` with its span for each interval row whose span began before the session (D10). `STALE` is never emitted. **Card correction (TEL-02):** "a timeout retries once, then reports UNAVAILABLE" becomes "a timeout retries once, then returns `NO_ANSWER`; nothing is published for that read".

### 0.8 Clock model (shared by poller and emulator)

- `WallClock`: real UTC, whole seconds.
- `ReplayClock(start: datetime, rate: int, wall_epoch: datetime)`: `source_now = start + (wall_now - wall_epoch) × rate`, truncated to whole seconds. Rate is an integer 1..600. Two processes, on one machine or on the laptop and the board, agree on source time when given the same three arguments and NTP-synced wall clocks.
- Replay is used only to play a simulator run's past public outputs. Every source time it produces is in the past, so the gateway's `SOURCE_TIME_IN_FUTURE` check (`gateway/assetops_gateway/service.py:856`) cannot fire unless a wall clock is wrong. The clock mode is printed in the status file and the claim record.
- `state_skew_max_seconds` is measured in source time. At rate 60 the 2 s skew allows about 33 ms of wall latency; that is enough on one laptop and on a LAN. TEL-04 uses rate 120 on a 2 h window; TEL-05, TEL-05b and TEL-08 use rate 60.
- **Rejected:** lockstep clock driven by a control channel between poller and emulator (a device has no such channel, so it would test a path that cannot exist); scaling the skew allowance by the rate (it would weaken D4 for real devices).

---

## TEL-00 · Pre-flight and card corrections (no code) · 0.25 d

**Scope.** Builder reads this file, the rulings and the HTML §10 cards; posts every question in one batch; records the port table (0.4) and confirms `gateway_process.py` and `fake_central.py` bind no fixed TCP port in 5173/8000. Applies all **Card corrections** in this file to the cards it works from (the packet carries them; the HTML is not edited by the builder).

**Gate.** Builder posts "no open questions", or the Architect answers the batch here (section at end).

**Stop.** Any ruling contradicts this file: ask; do not choose.

---

## TEL-01 · Shared core: profile, decode, clock, aggregate, report, publish · 0.75 d

**Files.** Creates `field/pyproject.toml`, `field/assetops_field/{__init__,profile,decode,clock,aggregate,report,publish}.py`, `field/tests/{field_fixtures,test_profile,test_decode,test_clock,test_aggregate,test_report,test_publish}.py`. Extends `tools/checks/module-roots.ps1` and `tools/checks/dependency-direction.ps1` (additive only).

**Approach.** Pure modules first, each with its own focused test, then `publish.py` against a fake IPC server. No Modbus code here.

**Interfaces.**

```python
# profile.py
@dataclass(frozen=True)
class RegisterRef: unit_id: int; function: int; address: int; type: str; word_order: str
@dataclass(frozen=True)
class ProfileRow:
    row_id: str; status: str; source_document: str; device_id: str; signal_id: str; role: str
    source_unit: str; quantity: Mapping[str, str]; registers: tuple[RegisterRef, ...]; decode: str
    enum_map: Mapping[int, str] | None; sentinels: frozenset[int]; scale_exponent: int; unit_exponent: int
    register_quantum: Fraction; output_resolution: Fraction; reading_class: str
    span_seconds: int | None; cadence_seconds: int; poll_period_seconds: int | None
    @property
    def word_count(self) -> int: ...   # 1 per 16-bit, 2 per 32-bit register
@dataclass(frozen=True)
class FieldProfile:
    profile_id: str; profile_version: int; status: str; interface: str; state_skew_max_seconds: int
    rows: tuple[ProfileRow, ...]; sha256: str; document: Mapping[str, Any]
class ProfileRefused(ValueError):
    def __init__(self, code: str, field: str, detail: str) -> None: ...
def load_profile(path: Path) -> FieldProfile: ...
def parse_profile(document: Mapping[str, Any]) -> FieldProfile: ...
def profile_sha256(document: Mapping[str, Any]) -> str: ...

# decode.py
@dataclass(frozen=True)
class Decoded:
    kind: str                 # "VALUE" | "SENTINEL" | "STATE"
    value: Fraction | None    # VALUE: in source_unit, exact
    state: str | None         # STATE: enum text
class DecodeFault(ValueError): ...   # config error: wrong word count, unmapped enum code
def decode_words(row: ProfileRow, words_per_register: Sequence[Sequence[int]]) -> Decoded: ...
def encode_value(row: ProfileRow, value: Fraction | str) -> list[list[int]]: ...  # used by the emulator only

# clock.py
class Clock(Protocol):
    def now(self) -> datetime: ...
    def sleep_until(self, instant: datetime) -> None: ...
class WallClock: ...
class ReplayClock:
    def __init__(self, start: datetime, rate: int, wall_epoch: datetime, *, wall: Callable[[], datetime] = ...) -> None: ...

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
def expected_polls(row: ProfileRow, start: datetime) -> list[datetime]: ...
class IntervalAggregator:
    def __init__(self, row: ProfileRow, session_start: datetime) -> None: ...
    def add(self, poll: Poll) -> None: ...
    def close(self, end: datetime) -> Result | None: ...     # None = publish nothing
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
    expected: Mapping[str, Any]   # tenant_id, site_id, gateway_id, source_mode, required device sources
    def check_identity(self) -> dict[str, Any]: ...
    def admit(self, texts: Sequence[str]) -> list[dict[str, Any]]: ...
    def seal_and_release(self) -> dict[str, Any]: ...
    def release_previous(self, previous_ref: str) -> dict[str, Any]: ...
    def diagnostics(self) -> dict[str, Any]: ...
```

**Architecture notes.**
- `decode_words`: per register, combine words per `word_order` into an unsigned integer, then two's-complement for `int*`. Sentinel check is on the raw integer of **any** register in the row (one sentinel register makes the whole row `SENTINEL`). Multi-register `NUMBER` rows sum the raw values exactly before scaling. `ENUM`: raw integer looked up in `enum_map`; a missing code raises `DecodeFault`.
- Exact arithmetic: `Fraction(raw) * Fraction(10) ** (scale_exponent + unit_exponent)`. No float anywhere; a test greps the package for `float(`.
- `IntervalAggregator.close(end)`: `start, end = interval_bounds(row, end)`; if `session_start > start` → `UNAVAILABLE`/`NO_COMPLETED_INTERVAL`; else compare the polls received against `expected_polls`: all `VALUE` → `GOOD` with the exact mean `sum/N`, then `quantize_half_even(mean, device_resolution(str(row.output_resolution)))` once; any `NO_VALUE` → `UNAVAILABLE`/`NO_MEASUREMENT`; no poll answered (`VALUE` or `NO_VALUE`) → `None`; otherwise (some answered, some `FAILED`/`NO_ANSWER`/missing) → `UNAVAILABLE`/`NO_MEASUREMENT`. Interval boundaries are multiples of `span_seconds` from 00:00:00Z; intervals are published only at multiples of `cadence_seconds` (cadence ≥ span; e.g. span 900, cadence 3600 means the poller polls only in the last 15 min of each hour).
- `StateSampler.sample`: first attempt sent at `boundary`; one retry allowed if it is still within `boundary + skew_max`; source time is always `boundary`. Value `VALUE`/`STATE` → `GOOD`; `NO_VALUE` → `UNAVAILABLE`/`NO_MEASUREMENT`; anything else → `None`.
- `build_report`: `measurement = MEASUREMENT_OF_READING_CLASS[row.reading_class]`; `interval_start` set for every `INTERVAL_MEAN` including `UNAVAILABLE` (V3 requires it); `unit = row.source_unit`; numeric value text `exact_decimal_text(value)`; state value is the enum text; `report_key = f"{profile_id}:{profile_version}:{device_id}:{signal_id}:{source_time Z}"`.
- `GatewayPublisher.check_identity`: `identity` must match `expected` (tenant, site, gateway, `source_mode == "SIMULATED"`, every row's device source in `permitted_source_ids`). **Correction to D4 wording:** `identity` does not return the active snapshot SHA (`gateway/assetops_gateway/service.py:407-418`); the snapshot is checked by passing `snapshot_sha256` on every `admit`, and any `GatewayRequestRefused` from `admit` stops the poller with the refusal printed. `admit` chunks to 256, returns the admission dicts verbatim; `GatewayUnavailable` propagates to the caller.
- Session reference: `field:<profile_id>:<profile_version>:<session start UTC Z>` (D4). The poller stores it in `<state-dir>/session.json`; on start it calls `release_previous(old_ref)` before starting a new session, so a crash never strands sealed `STAGED` batches.
- Checks: `module-roots.ps1` required dirs `field`, `field/assetops_field`, required files `field/pyproject.toml`, `field/assetops_field/__init__.py`. `dependency-direction.ps1` new section exactly as D4 "What must change in tools/checks", with the reverse rule on **non-test** host modules only and no change to the existing host counts (amendment 2 item 2).

**Test seams.** `field_fixtures.py` holds `profile_document(**overrides)`, `row(**overrides)`, `FakeLink` (records `(op, body)` and returns scripted bodies or raises). `ReplayClock` takes an injectable `wall` callable so `test_clock.py` needs no sleeping.

**Rejected alternatives.**
- Float scaling with rounding: produces non-decimal values and silent drift; exact `Fraction` is required by D4.
- A second rounding helper: duplicates `quantize_half_even` with possibly different semantics.
- Profile in YAML: needs a non-stdlib parser; JSON is stdlib and canonicalisable.
- Publisher calling `deliver`: forbidden by D4; upload is the gateway's background uploader.

**Acceptance gates.**
- Decoder vectors: `FF9C` int16 × 0.1 = −10; `7FFF` declared sentinel → `SENTINEL`; `0001 86A0` uint32 BIG × 0.001 = 100; `86A0 0001` LITTLE = 100.
- **Card correction (D10):** an interval missing one expected poll → `UNAVAILABLE`/`NO_MEASUREMENT` with span; the session's first interval → `NO_COMPLETED_INTERVAL` with span; a fully failed interval → `None`; N = 3 with values 1, 1, 2 (mean 4/3) quantized once to `0.001` gives `1.333`.
- Every report text round-trips through `parse_device_report_text`; profile SHA unchanged under key reordering; every `ProfileRefused` code has one test.
- `FakeLink` sees only `OPS_USED`.
- Both `.ps1` checks green; `gateway/tests/test_wire_contracts.py` green.

**Stop.** A field rule cannot be written without editing an existing rule; or the exact-decimal helper would need to differ from `exact_decimal_text`.

---

## TEL-02 · Read-only Modbus TCP client · 0.5 d

**Files.** `field/assetops_field/modbus_tcp.py`, `field/tests/test_modbus_tcp.py`.

**Interfaces.**

```python
READ_FUNCTIONS = frozenset({1, 2, 3, 4})
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
    def read(self, unit_id: int, function: int, address: int, count: int) -> ReadResult: ...
    def close(self) -> None: ...
def classify(result: ReadResult, row: ProfileRow) -> PollOutcome: ...   # the 0.7 table, one place
```

**Approach.** stdlib `socket`, one persistent connection, reconnect on the next read after any `NO_ANSWER`. MBAP header built with `struct`; transaction ID increments mod 65536. `read` validates `function in READ_FUNCTIONS` before opening or writing anything (raises `WriteForbidden`). One retry on `TIMEOUT` only; exceptions 04 and 06 are retried once by the poller (not the client), so the client stays a single-transaction primitive. Function 1/2 responses decode bits to words of 0/1 (not used in October profiles, kept for the RTU later).

**Test seam.** An in-test `socketserver` that records every received byte and replies from a script. No pymodbus.

**Rejected.** pymodbus as the client: would put a third-party dependency in non-test field code against D4. Async client: one poller per gateway and sequential reads are enough at these cadences.

**Acceptance gates.** FC 05, 06, 15, 16, 23 raise before any byte (server records 0 bytes); FC 01-04 request frames equal the bytes in `modbustcp.html` Figure 2a; exception responses 01/02/03/04/06/0A/0B map through `classify` to the 0.7 table; TID and Unit ID mismatch → `NO_ANSWER`; timeout retried once then `NO_ANSWER` (**card correction**).

**Stop.** Any need for a write function code.

---

## TEL-03 · GX-shaped emulator, profile `-1` and pinned JSONL · 0.75 d

**Files.** `field/tests/emulators/{__init__,gx_server}.py`, `field/tests/test_gx_emulator.py`, `field/profiles/gx-system-illustrative-1.json`, `host/tests/field_observation_fixtures.py`, `host/tests/test_field_observation_fixtures.py`, `contract-fixtures/telemetry/kobo-public-observations-v1/{observations.jsonl,manifest.json}`.

**JSONL generator (host/tests).** `generate_daytime_fixture(out_dir: Path) -> dict` builds the registered Kobo draft exactly as `backend/tests/test_s2_registered_basis.py` `request()` (KOBO-001, `kobo-daytime`, 2026-09-30T03:00Z-15:00Z, timestep 15, seed 20260929), runs it through the host Lab execution as `host/tests/test_registered_gateway_publication.py` `complete()` does, then calls `generate_observations(session.execution.boundaries, session.reporting)` (`:143`). It writes only public fields (0.6). The freshness test regenerates into `tmp_path` and asserts byte equality with the checked-in file and the manifest SHA. It also asserts each `-1` row's `reading_class`, `span_seconds` and `cadence_seconds` equal the publication profile's declaration for that signal, so the profile cannot drift from the run it replays.

**Profile `-1` rows (D5).** `pv-ac-output` (808-810 as in 0.6) bound to `pv-inverter-controller/ac-power` role `pv_power`; `battery-soc` (843, uint16, `register_unit "%"`, `scale_exponent 0`, `unit_exponent 0`, `register_quantum "1"`, `output_resolution "1"`, `STATE_SIGNAL`, cadence from the publication profile) bound to `battery-pcs-controller/state-of-charge` role `battery_soc`. Nothing else: no 842, no 817-819.

**Representability (Architect amendment, replaces the TEL-03 "do not round in the emulator" stop for GX rows).** Registered Kobo values are published at resolution `0.000001` in their canonical unit (`backend/assetops_backend/runs/profiles.py:1826`). A uint16 W or % register cannot hold them, so the original stop would fire on the first value. Ruling: the emulator models the device's register resolution. For each GX-layout row it presents `quantize_half_even(observation_value_in_register_unit, register_quantum)` and the TEL-03 equality is against that quantized value. The claim record says "values presented at the register's resolution (1 W, 1 %)". The stop now fires only on **range** (a value outside the register type's range after scaling) or on a row whose `output_resolution` is finer than its `register_quantum` (that would invent precision). Illustrative block rows (TEL-05b) use int32 with exponent −6 and are never quantized.

**Emulator design.**
```python
class ObservationTimeline:
    def __init__(self, jsonl: Path, profile: FieldProfile) -> None: ...
    def registers_at(self, source_instant: datetime) -> dict[tuple[int, int], int]: ...  # (unit_id, address) -> word
@dataclass
class Faults:
    paused: bool = False                       # accept the connection, never answer
    exception: dict[tuple[int, int], int] = field(default_factory=dict)  # (unit, address) -> code
    sentinel_rows: set[str] = field(default_factory=set)
    wrong_unit_id: bool = False; wrong_tid: bool = False
class GxEmulator:
    def __init__(self, timeline: ObservationTimeline, clock: Clock, *, host: str, port: int) -> None: ...
    def start(self) -> int: ...      # returns the bound port; runs pymodbus in a background thread
    def stop(self) -> None: ...
    faults: Faults
    writes: int                      # any write FC increments this and answers exception 01
def main(argv=None) -> int: ...      # CLI: --jsonl --profile --host --port --replay-start --replay-rate --replay-wall-epoch
```
Value-at-instant rule: a `STATE_SIGNAL` observation holds from its `source_sample_time` until the next one for that signal. An `INTERVAL_SIGNAL` observation with source time `T` and span `S` is held constant over `[T − S, T)`; outside any span the registers hold the row's first sentinel. Outcome mapping: `REPORTED` → encoded value; `NO_VALUE_AT_BOUNDARY` and `NO_PRECEDING_INTERVAL` → sentinel; `SUPPRESSED_BY_GAP` and `DROPPED` → exception 0B for that row's registers at that instant (no answer, so nothing is published, which matches "not published"). The emulator path therefore reports `NO_MEASUREMENT` where the simulator published `NO_COMPLETED_INTERVAL`; that difference is expected and the equality test allows it for `UNAVAILABLE` rows only. Phase split: the whole PV value on 808, zero on 809 and 810 (exact and stated). The emulator uses `encode_value` from `decode.py` so encoding and decoding cannot disagree silently (a round-trip test covers both directions).

**Rejected.** Reading observations in-test from the simulator (field/tests may not import the simulator, D4). A hand-written emulator (pymodbus is the standard reference server; the stdlib TEL-02 server remains the fallback if pymodbus will not install, which is an allowed recorded deviation).

**Acceptance gates.** For every observation in the window, TEL-02 client reads through profile `-1` decode to exactly the quantized value (GOOD) or `SENTINEL` (UNAVAILABLE); each fault switch gives its 0.7 outcome; `writes == 0` after the suite; JSONL freshness green.

**Stop.** A value the emulator needs is not in the public observations; a range overflow; pymodbus 3.16.1 not installable (then fall back and record).

---

## TEL-04 · Poller and focused end-to-end through a real gateway process · 0.75 d

**Files.** `field/assetops_field/modbus_poller.py`, `host/tests/test_field_modbus_tcp_proof.py`.

**CLI.**
```
python -m assetops_field.modbus_poller --profile <json> --host <h> --port <p>
    --gateway-address <ipc address> --ipc-credential <gateway.credential> --snapshot-sha256 <hex>
    --expect-identity <json file> --state-dir <dir>
    [--replay-start <Z> --replay-rate <n> --replay-wall-epoch <Z>] [--stop-at <Z>]
```
Exit codes: 0 after `--stop-at` and a final `seal_and_release`; 2 configuration refused (`ProfileRefused`, `IdentityMismatch`); 3 admission refused (`GatewayRequestRefused`); 4 gateway unavailable for longer than 10 consecutive boundaries.

**Loop.** Build a schedule of poll instants (state boundaries at multiples of `cadence_seconds`; interval polls at `start + k × poll_period` inside each published span). At each instant: read every due row (registers of one row in one request when contiguous, else one request per register), append raw capture lines, classify, feed aggregators/samplers, retry 04/06 once. At each publish instant: build reports for all rows due, `admit` them, then `seal_and_release`. On `GatewayUnavailable`, keep the report texts in memory and retry them first at the next publish instant (same keys, so the gateway answers `ALREADY_ADMITTED` for any that did land). Rewrite the status file after every publish instant.

**Test harness (host/tests).** Snapshot from the registered daytime draft (`snapshot_canonical`), `write_config` + `provisioning_from_snapshot`, `GatewayProcess` with an `upload` block pointing at `FakeCentral` (`receipt_text`, `CERT`), harness `activate` over the link, emulator in-process (`GxEmulator` on port 0), poller as a subprocess with `ReplayClock` rate 120 over 2026-09-30T06:00Z-08:00Z. After the poller exits the harness calls `deliver` until nothing is attempted (the harness may; the adapter may not), then reads `FakeCentral` records and `diagnostics`.

**Rejected.** Running the poller in-process (it would not prove the CLI, the IPC client process boundary or restart behaviour). A separate emulator process in focused tests (fault switches need in-process control; the CLI form is exercised in TEL-08).

**Acceptance gates.** The TEL-04 card list, with corrections: every admitted envelope acknowledged 200; sentinel and exception 02 → `UNAVAILABLE`/`NO_MEASUREMENT` envelopes, not holds; profile unit edited to `W` → `UNIT_INCOMPATIBLE` holds, no sequence; repeated poll reuses message ID; same key other content → `CONFLICTING_REPORT`; FakeCentral `DROP` then recovery posts byte-identical bodies; **a server pause produces no admitted report for the paused boundaries** and contact age grows in `diagnostics`; status-file counters match the injected faults; `writes == 0`; activation unchanged. Plus: poller killed mid-window and restarted yields `NO_COMPLETED_INTERVAL` for the first interval after restart, and no stranded `STAGED` batch.

**Stop.** Activation refused; any gateway/backend change seems needed; an unexpected hold kind (report with the hold row).

---

## TEL-05 · Postgres acceptance, profile `-1` · 0.5 d · run alone

**Files.** `host/tests/test_field_modbus_tcp_acceptance_postgres.py` (**card correction:** `host/tests`, not `backend/tests`; feasibility §2.4), test `test_gx_profile_1_lands_as_accepted_evidence`.

**Approach (reuses the proven central pattern in `host/tests/test_s6_verification_publication.py:233-300`).**
1. `pg_harness.fresh_database()`; `PostgresFoundationStore(URL)`; KOBO-001 converted with `test_s1_bindings_postgres.converted(store)`; enable gateway and sources as that test does (stand-in for provisioning); registered daytime draft from that store gives the snapshot.
2. Central: `BatchIngestionService(PostgresEvidenceLedger(URL), clock)` behind `FakeCentral(respond)`, with the **real** UTC clock (no decision-clock override: `admit` stamps real publication instants, so an override earlier than now could refuse batches). The HTTP route is exercised by TEL-08 through real `serve_tls`.
3. Gateway process, activation, in-process emulator and poller subprocess as TEL-04, replay rate 60 over 2026-09-30T03:00Z-15:00Z, then harness `deliver` until empty.
4. Reads: accepted evidence rows from `accepted_evidence` for the Site, per role; provenance through the resolver named in the card; `assess_dispatch.main(["assess", ...])` in-process with `DATABASE_URL` set (captures stdout JSON).

**Gates.** Receipts COMPLETED; accepted evidence for both bound roles, IDs printed; provenance UNKNOWN / `NO_POSITIVE_BINDING`; assess completes citing only these IDs and records `NO_GENERATOR_STATE`; no consequence row for the Site; green on two consecutive runs.

**Stop.** As the card; plus any central refusal for timing (report the refusal row; do not add a clock override).

---

## TEL-08 · BeagleBone Black repeat (stage 2, TCP only) · 0.75 d (+ owner 30 min) · October scope

**Preconditions (owner, physical, by 29 Oct 12:00).** microSD 8 GB or larger and a 5 V 2 A barrel supply on hand (buy only these if missing, about $16); flash Debian 13 IoT (kernel 6.12) to the microSD and boot from it; connect the board to the laptop's LAN by Ethernet; give the builder SSH access with a key; allow inbound TCP 8443 and 5020 on the laptop's Windows firewall for the LAN profile (admin action). The coordinator flags these to the owner.

**Design choices (settled).**
- Boot from microSD; no eMMC flash. **Rejected:** eMMC flashing (slower, irreversible, not needed to prove the path).
- Ethernet on the LAN. **Rejected:** USB gadget networking (Windows RNDIS driver risk on Windows 11).
- Deploy by copying `contracts/`, `gateway/` and `field/` source directories to `/opt/assetops/src` and setting `PYTHONPATH` there; record `git rev-parse HEAD` and a SHA-256 over the copied files (`find ... -type f | sort | xargs sha256sum | sha256sum`). **Rejected:** building wheels (field packaging untested; adds a step that proves nothing about the path).
- Run gateway and poller as two `nohup` processes under a non-root `assetops` user; no systemd units in October. **Rejected:** systemd hardening (§7.9 step 8-10 is post-October).
- Emulator and `serve_tls` stay on the laptop. Python 3.13 from Debian (`python3 -m venv /opt/assetops/venv`); stdlib only, so nothing is pip-installed on the board.
- Board clock must be NTP-synchronised (`timedatectl show -p NTPSynchronized` = yes) before the gateway starts; the gateway refuses future source times against its own clock.

**Laptop bench helper `host/tests/field_bench.py`.**
- `setup --database-url <...assetops_tel_bbb_test> --out <dir>`: migrates to head, converts KOBO-001, applies the same enabling as TEL-05, creates the daytime registered draft, runs `python -m assetops_backend.evidence.provision_gateway issue` for the bench gateway and all its sources, and writes `<dir>/{snapshot.json (text), activation.json ({snapshot_text, claimed}), provisioning.json, expect-identity.json, upload-credential.<selector>}`. Backend imports are inside `setup` only.
- `activate --address <ipc> --credential <file> --activation <activation.json>`: stdlib plus `assetops_gateway.ipc` only, so it runs on the board; sends one `activate`.
- TLS: a local CA and server certificate with SANs = the laptop's LAN IP; `python -m assetops_backend.serve_tls --cert ... --key ... --host 0.0.0.0 --port 8443` with `DATABASE_URL` = the bench database. Gateway `upload.ca_file` = the local CA.

**Run.** Emulator CLI on the laptop (`--port 5020`, replay rate 60, the daytime window); on the board: gateway `serve`, `field_bench.py activate`, poller CLI pointing at `<laptop IP>:5020` with the same replay arguments; background uploader `interval_seconds 30`. Then on the laptop: `assess_dispatch assess` for the window, and the evidence API read (`GET /api/sites/KOBO-001/evidence/records` through `serve_tls`).

**Gates.** The TEL-05 gates (COMPLETED receipts, accepted evidence per role, provenance UNKNOWN, assess completes, no consequence), now with real `serve_tls` and the board's gateway; one fault on the board: unplug Ethernet for 5 min of wall time then reconnect, and the backlog drains with byte-identical bodies (`diagnostics` queue rises then falls); BBB claim record names "BeagleBone Black · Debian 13 IoT · kernel <uname -r> · Python <version> · commit <sha> · tree <sha256>". R2.

**Stop.** Any change to gateway or field code needed for Linux (report the traceback); NTP not synchronisable; the board cannot reach the laptop after the firewall rule; any central refusal. **Slip rule:** if the board is not reachable by 30 Oct 09:00, TEL-08 moves to 31 Oct and the 30 Oct showing uses the laptop result.

**Stretch (only if TEL-05b is green first).** Repeat with profile `-2` and the prolonged JSONL.

---

## TEL-05b · Finding proof, profile `-2` · 0.75 d (focused parts can be built while the board is prepared)

**Files.** `field/profiles/gx-system-illustrative-2.json`, `contract-fixtures/telemetry/kobo-prolonged-public-observations-v1/`, additions to `host/tests/field_observation_fixtures.py` and its freshness test, `field/tests/test_gx_emulator.py` cases for unit 101, second test `test_gx_profile_2_raises_a_finding_with_no_money_shown` in the TEL-05 file. TEL-01 `decode.py` already supports `ENUM`.

**Profile `-2`.** Status `ILLUSTRATIVE`. Unit 100: the `pv-ac-output` row of `-1`, unchanged. Unit 101, AssetOps illustrative block (row status `ILLUSTRATIVE`, `source_document` "AssetOps illustrative block; not a vendor register map"), holding registers, all numeric rows `int32`, `word_order BIG`, `scale_exponent −6`, `unit_exponent 0`, `register_quantum "1"`, `output_resolution "0.000001"`, sentinel `[2147483647]`:

| Address | device_id / signal_id | role | unit | reading class |
|---|---|---|---|---|
| 1000 | `generator-controller/status` | `generator_state` | `state` | STATE, `ENUM` uint16 `{0: STOPPED, 1: STARTING, 2: RUNNING, 3: FAILED}`, sentinel 65535 |
| 1002 | `generator-controller/ac-power` | `generator_power` | kW | INTERVAL |
| 1004 | `residential-meter/active-power` | `feeder_demand` | kW | INTERVAL |
| 1006 | `clinic-meter/active-power` | `feeder_demand` | kW | INTERVAL |
| 1008 | `mill-meter/active-power` | `feeder_demand` | kW | INTERVAL |
| 1010 | `pv-inverter-controller/available-power` | `pv_available_power` | kW | INTERVAL |
| 1012 | `battery-pcs-controller/discharge-capability` | `pcs_discharge_capability` | kW | INTERVAL |
| 1014 | `battery-pcs-controller/state-of-charge` | `battery_soc` | % | as published |

Spans, cadences and reading classes are copied from the publication profile and asserted by the freshness test. SoC is on unit 101 at full resolution, so 843 is omitted from `-2`: a 1 % register could move a point across the dispatch reserve headroom (`dispatch_v3.py` `SOC_HEADROOM_POINTS`). Device and signal IDs are the Kobo bindings (`backend/conversions/kobo-001-bindings.json`, plus the roles-2/3 signals in `host/tests/test_s6_verification_publication.py:59-68`).

**JSONL.** `generate_prolonged_fixture(out_dir)` uses the in-memory converted store (`registered.converted()`), applies `kobo-001-s3-dispatch-demo-config.json` then `kobo-001-s6-verification-demo-config.json` exactly as `configure()` (`test_s6_verification_publication.py:82-87`), creates the registered `kobo-mini-grid-prolonged` draft over 2026-10-13T03:00Z-11:00Z with timestep 5 and `REGISTERED_KOBO_PUBLICATION_PROFILE_V4` as `draft()` (`:90-112`), executes it, and writes the public observations. Same freshness test pattern.

**Postgres test.** As TEL-05, but configure the Postgres store with the same two demo configs and build the same prolonged draft for the snapshot; replay rate 60 over the window; then in-process: `assess_dispatch.main(["assess", ... "--start", "2026-10-13T03:00:00Z", "--end", "2026-10-13T11:00:00Z", "--cohort", "GATEWAY:SOURCE:EPOCH"])`, `assess_dispatch.main(["match-findings", ...])`, `publish_assumption.main(["fixture", "--site", "KOBO-001", "--file", "backend/conversions/demo-diesel-price-publications.json", "--step", "v4"])` (1.28 USD/L from 2026-10-01, covers the window), `recompute_consequences.main(["run", "--tenant", "demo", "--site", "KOBO-001"])`. Reads over `TestClient(create_app(...))` with `DATABASE_URL` set, as the S2 Postgres API tests construct it: the Site findings list, the Finding read, and `GET /api/sites/KOBO-001/findings/{fid}/financial-consequences?revision_id={frid}`.

**Gates (amendment 2, N1 replaced).** A dispatch Finding exists for the window citing only this test's accepted evidence IDs; its `source_provenance` is UNKNOWN / `NO_POSITIVE_BINDING`; every consequence revision read has `currentness.current_amount_shown == false` and `"MIXED_OR_UNKNOWN_SOURCE"` in `currentness.withheld_reasons`; the Finding read and the Site findings list show no current amount; green twice.

**Rejected.** Mixing a field-sourced generator with the other roles from the simulated publisher (two gateways on one Site would split the cohort and blur what the proof shows). Placing the extension rows at real GX addresses (would imply a vendor claim). Attaching a publication to get a figure (D5(d)).

**Stop.** No Finding arises (report the window assessment; do not tune values or window); a current amount is shown anywhere (stop immediately; that is a money-gate defect, report to the Architect); any 4xx from ingestion; the price fixture cannot be applied without new code.

---

## TEL-07 · Claim records and demo runbook · 0.25 d

**Files.** `.agent/TEL-05-review-packet.md`, `.agent/TEL-08-review-packet.md`, `.agent/TEL-demo-runbook-2026-10-30.md`.

**Claim records** use the §10.0 template; the TEL-05b record carries the exact text in amendment 2 item 6. Every record names interface, format, profile ID/version/SHA-256, JSONL SHA-256, clock mode, environment, commit, accepted-evidence IDs and (TEL-05b) Finding ID, and a "Not claimed" line.

**Runbook.** Exact commands for the live showing, terminal only: bench `setup`, `serve_tls`, emulator, gateway, `activate`, poller, then the evidence read, provenance read, `finding-rows` and the consequence read JSON. The runbook may cite the existing screen labels ("Source unverified", "No current cost is shown", `frontend/src/sites/sourceProvenance.tsx:101-104`) but adds no UI and starts no dev server.

**Gate.** A reviewer reruns the showing from the runbook alone.

**Stop.** The showing needs the demo database or a UI change.

---

## TEL-06 · Minimal generic CSV collector (B1) · 0.5 d + 0.25 d · after TEL-07, may move to 31 Oct

**Files.** `field/assetops_field/export_csv.py`, `field/profiles/generic-interval-csv-illustrative-1.json`, `contract-fixtures/telemetry/generic-interval-csv-v1/{kobo-window.csv,manifest.json}`, `field/tests/test_export_csv.py`, `host/tests/test_field_export_csv_proof.py` (06a), a third test in the TEL-05 file (06b).

**Interfaces.**
```python
@dataclass(frozen=True)
class CsvRefused(ValueError): code: str; field: str; detail: str; profile_sha256: str
class CsvCollector:
    def __init__(self, profile: FieldProfile, publisher: GatewayPublisher) -> None: ...
    def reports(self, path: Path) -> list[DeviceReport]: ...     # whole-file validation first
    def collect(self, path: Path) -> dict[str, Any]: ...          # reports(), then admit, seal_and_release
```
CSV profile rows use `interface "EXPORT_CSV"` and replace `registers` with `{"column": "<header>", "unit_header": "<unit text in header>"}`. Columns: `timestamp_utc` (must end in `Z`), one column per row. Each row is one interval ending at `timestamp_utc` whose span must equal the profile row's `span_seconds` (D10: refused, not resampled). Blank cell → `UNAVAILABLE`/`NO_MEASUREMENT`. Header mismatch refuses the whole file before any IPC call. The collector is not an aggregator. Same op set and session-ref rule as the poller. No vendor name anywhere.

**Gates and stop.** The TEL-06 card list; stop on any request to name a vendor format.

---

## Implementer questions and resolutions

_Empty. The Implementer review of this spec posts its questions here as `Q-T<n>`; the Architect answers each in place, with the date and the section it amends._
