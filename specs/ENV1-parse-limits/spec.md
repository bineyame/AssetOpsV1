# ENV-1: every upload parse under hard limits, bounded per host (implementer spec)

Status: spec rev 1, handshake not started. Architect (Claude), 2026-11-21, on the owner's delegation
(`owner/owner-away-architect-decides-2026-11-21.md`). Queued by D-3A6.23 ("Outside 3A6") and the 3A6 round-6 review
(`specs/3A6-source-profiles/review.md` "Residual risk", R1 and R2). **0.75 unit** (queued as 0.25; the sweep found
the per-host bound and the field process's missing limits, `rulings.md` D-ENV1.1). Discovery review (W5): a protected
seam (upload parsing). Non-screen. No migration, no database, no served text, no guard change.
`USER_REVIEW_REQUIRED: false`. Decisions: `rulings.md` (D-ENV1.1 to D-ENV1.7). Reviewer guide: `reviewer-guide.md`.
Handshake: `handshake.md`.

- **What it is.** D-3A6.23's class, applied to every path that parses upload bytes: the parse runs in a child
  process that sets hard OS limits before it reads a byte, the parent waits a bounded wall time, a breach is a coded
  answer with its cause logged at the API layer, and the number of parse children is bounded **per host**, not per
  server process.
- **Why.** Three paths sit outside the class today (checked on `main` `02a16011d`):
  1. The reading upload (`reading_upload_api.py`, UP-1) does **not** parse in the server process: the service calls
     `host/reading_upload_process.py`, which runs `python -m assetops_field.csv_upload` (TEL-01 D4 forbids importing
     `field/`). That child has no memory or CPU limit, its 120 s timeout raises `subprocess.TimeoutExpired`, which
     the route does not catch (a 500), and any number of children may run at once (one per threadpool thread).
     A cell of more than 4,300 digits crashes the child (`ValueError` in `Fraction`), which the route answers as
     "could not be checked just now ... try again": retrying cannot help.
  2. The loader CLI (`load_emulated_exports.py:151`) runs `json.loads(path.read_bytes())` with no bound, and reads
     every file whole before the intake's 8 MiB check.
  3. `ParseEnvelope`'s 2 slots are per server process: N uvicorn workers carry 2N children.
- **Builds on (on `main`):** `backend/assetops_backend/commercial/envelope.py` (`ParseEnvelope`, `DEFAULT_LIMITS`,
  `EnvelopeBreach`, `default_envelope`), `commercial/uploads.py` (`MAX_UPLOAD_BYTES`, `UploadRefused`),
  `commercial_upload_api.py:150` (D-3A6.29's cause log, the pattern copied here), `reading_upload_api.py`,
  `reading_upload/service.py`, `host/reading_upload_process.py`, `field/assetops_field/csv_upload.py`,
  `field/assetops_field/export_csv.py`, `load_emulated_exports.py`.

## 0. Before you start (gates; each is a hard stop)

- **Start:** the handshake has no open question. No other gate (3A6 and D-3A6.29's fix are on `main`).
- **Branch** `task/ENV1-parse-limits` off `main`; worktree `/opt/assetecon/AssetOpsV1-env1`; symlink
  `frontend/node_modules` from the main checkout.
- **Pre-flight print (packet, first section).** On `main`, through the slot pool: (a) `/usr/bin/time -f "%M KB %U s"`
  of `python -m assetops_field.csv_upload check` on the two 2 MiB fixtures of §3 (F1, F2), under the backend venv's
  Python; (b) the same under a 512 MiB `RLIMIT_AS` (any launcher in scratch). The Architect's figures (this host,
  Python 3.12 venv): F1 150 MB RSS, 8.4 s CPU; F2 190 MB RSS, 8.9 s CPU, refused by `RLIMIT_AS` 192 MiB and passing
  at 224 MiB; a simulated `send` of F2 (three parses, the admission texts, the message ids) 455 MB RSS, 34 s CPU,
  12.9 MB of output, refused at 384 MiB and passing at 512 MiB. A figure more than 1.5 times these is a mid-build
  question (the limits of §2.3 were sized from them); smaller figures are not.
- **Read:** `rulings.md`; `commercial/envelope.py` (whole); `commercial_upload_api.py:130-160`;
  `reading_upload_api.py` (whole); `reading_upload/service.py:1-60, 199-275`; `host/reading_upload_process.py`
  (whole); `field/assetops_field/csv_upload.py` (whole); `export_csv.py:111-140`;
  `load_emulated_exports.py:144-256`; `backend/tests/test_3a6_parse_envelope.py:1-130`.
- **Tests** through the slot pool only (`tools/heavy-slot.sh -- ...`), no database. Files: §4. Then
  `python tools/select-tests.py --base main` and its set; the package-scan files of D-3A6.29
  (`test_3a1_commercial_service.py` R3 and R13, `test_3a4_commercial_months.py` test 12,
  `test_4b_money_leaves.py` 11a, `test_3a3_single_writer.py`) by hand; fast check-all at the end.
- **Files.** New: `backend/assetops_backend/parse_slots.py`, `backend/tests/test_env1_parse_slots.py`. Edited:
  `commercial/envelope.py`, `load_emulated_exports.py`, `reading_upload/service.py`, `reading_upload_api.py`,
  `host/reading_upload_process.py`, `field/assetops_field/csv_upload.py`, `field/assetops_field/export_csv.py`,
  `backend/tests/conftest.py`, `host/conftest.py`, and the test files of §4. Nothing under `contracts/`,
  `simulator/`, `gateway/`, `config/`, `frontend/` or any guard; no i18n key added or changed.
- **No user-facing text** (D-ENV1.5): every answer reuses an existing code's existing words. D-SC1.28 does not apply.

## 1. Outcome and gate questions

Is every upload parse (commercial, profile admission, reading upload check and send, the loader's JSON look-up) run
in a child under hard memory and CPU limits set before it reads a byte, with a bounded wall time? Does every breach
answer with a coded refusal (never a 500, a hung request or a dead server), its cause logged by the API layer as codes
and numbers only? Is the number of parse children bounded per host whatever the number of server processes, so the
host's worst case is a stated figure? Is every legitimate file within the limits by a measured margin? Is a cell that
crashed the field child now a refusal with its honest code?

## 2. Design

### 2.1 Host-wide parse slots (`backend/assetops_backend/parse_slots.py`, new; D-ENV1.3)

Imports exactly: `__future__`, `contextlib`, `fcntl`, `os`, `stat`, `tempfile`, `threading`, `time`, `pathlib`, `types`,
`typing`. No logging.

```python
SLOT_DIR_ENV = "ASSETOPS_PARSE_SLOT_DIR"
POOLS = MappingProxyType({"commercial": 2, "reading": 2})      # pinned by test S0
POLL_SECONDS = 0.05

class SlotWaitExpired(Exception):          # the wait passed its timeout; no slot was taken
    pass

class HostSlots:
    def __init__(self, directory: Path, pool: str, count: int) -> None
    @contextmanager
    def hold(self, timeout: float | None = None) -> Iterator[int]   # yields the slot index taken

def slot_directory(environ: Mapping[str, str] = os.environ) -> Path
def host_slots(pool: str) -> HostSlots        # production: POOLS[pool] slots in slot_directory(); one per (dir, pool)
```

- `slot_directory`: `environ[SLOT_DIR_ENV]` when set and non-empty, else
  `Path(tempfile.gettempdir()) / f"assetops-parse-slots-{os.getuid()}"`. It is created with mode `0o700` if absent
  (`mkdir(mode=0o700, exist_ok=True)`), then `os.lstat`: not a directory (a symlink included), not owned by
  `os.getuid()`, or any group or other permission bit set (`st_mode & 0o077`) raises `RuntimeError` naming the path
  and the reason. Read at each `host_slots` call (not at import), so a test's environment applies.
- `HostSlots.__init__`: `pool` fullmatches `[a-z][a-z0-9-]{0,31}`, `count` an `int` (not `bool`) `>= 1`, else
  `ValueError`. Slot `i` is the file `directory / f"{pool}-{i}.lock"`, `0 <= i < count`.
- `hold(timeout)`: `timeout` is `None` (wait without end) or a number `> 0` (`ValueError` otherwise). Loop: for `i` in
  `0 .. count-1`, `fd = os.open(path_i, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)`, then
  `fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)`; on `BlockingIOError` close `fd` and try the next. If none is
  free: past the deadline (`time.monotonic()` at entry plus `timeout`) raise `SlotWaitExpired`; else sleep
  `POLL_SECONDS` and loop. On success yield `i`; in `finally`, `fcntl.flock(fd, fcntl.LOCK_UN)` and `os.close(fd)`.
  Every hold opens its own descriptor, so two threads of one process exclude each other (flock binds to the open file
  description); a process that dies releases its slot (the kernel drops the lock with the descriptor).
- `host_slots(pool)`: `pool` not in `POOLS` is `KeyError`. Cached per `(slot_directory(), pool)` under a
  `threading.Lock`; returns `HostSlots(directory, pool, POOLS[pool])`.

### 2.2 The commercial envelope takes a host slot (`commercial/envelope.py`; D-ENV1.3)

- `ParseEnvelope.__init__(self, limits=DEFAULT_LIMITS, slots: HostSlots | None = None)`: `self._host = slots if slots
  is not None else host_slots("commercial")`. A `slots` that is not a `HostSlots` is `TypeError`.
- `read`: inside `with self._slots:` and around the call to `self._run(...)` only (not the active counter), `with
  self._host.hold(None):`. The wait has no timeout: D-3A6.23 ("further uploads wait for a slot; they are not
  refused") is unchanged. Nothing else in the file changes: limits, causes, `EnvelopeBreach`, the launcher.
- The import `from assetops_backend.parse_slots import HostSlots, host_slots` is the file's only new import (the
  package stays log-free, R13).

### 2.3 The reading upload's field process under limits (D-ENV1.2, D-ENV1.4)

**Field side (`field/assetops_field/csv_upload.py`).**

```python
EXIT_LIMIT = 7                                         # the child ran out of memory under its limit
LIMIT_FLAGS = ("--limit-memory-bytes", "--limit-cpu-seconds")

def _entry(argv: Sequence[str] | None = None) -> int   # the module's only __main__ path; never call it in-process
```

- `_entry`: `argv = list(sys.argv[1:] if argv is None else argv)`. It requires `argv[0] == "--limit-memory-bytes"`,
  `argv[2] == "--limit-cpu-seconds"`, and `argv[1]`, `argv[3]` decimal integers (`[0-9]{1,12}`) `> 0`; otherwise it
  emits `{"ok": false, "error": "CONFIGURATION", "detail": "the memory and CPU limits are required"}` and returns
  `EXIT_CONFIG`. Then `import resource` (an `ImportError` emits CONFIGURATION, detail `"resource limits need
  Linux"`, returns `EXIT_CONFIG`) and, in this order: `RLIMIT_AS (m, m)`, `RLIMIT_CPU (c, c + 1)`,
  `RLIMIT_FSIZE (0, 0)`, `RLIMIT_CORE (0, 0)`. Only then `return main(argv[4:])`, inside `try ... except
  MemoryError:` which emits `{"ok": false, "error": "LIMIT", "detail": "memory"}` and returns `EXIT_LIMIT`; if that
  emit itself raises `MemoryError`, `os._exit(EXIT_LIMIT)`.
- The module's last lines become `if __name__ == "__main__": raise SystemExit(_entry())`. `main(argv)` is unchanged
  and stays the in-process entry its tests use (it sets no limit). The module docstring's usage lines gain the two
  flags before the subcommand.
- `RLIMIT_FSIZE 0` is safe: neither command writes a file (it reads `--file`, prints to a pipe, talks to the gateway
  over its socket); the host sets `PYTHONDONTWRITEBYTECODE=1` (below) so imports write no bytecode.

**Field side (`export_csv.py`, `CsvCollector._value`; D-ENV1.6).** `value = Fraction(cell)` moves inside
`try ... except ValueError as error: raise self._refuse("INVALID_VALUE", field, "the number has too many digits")
from error`. Nothing else in the collector changes.

**Host side (`host/reading_upload_process.py`).**

```python
@dataclass(frozen=True)
class FieldLimits:
    memory_bytes: int           # RLIMIT_AS of the child
    cpu_seconds: int            # RLIMIT_CPU soft; hard = soft + 1
    wall_seconds: float         # subprocess timeout
    slot_wait_seconds: float    # how long a request waits for a host slot
    # __post_init__: each an int or float (not bool) > 0, memory_bytes and cpu_seconds int, else ValueError

CHECK_LIMITS = FieldLimits(512 * 2**20, 30, 60.0, 60.0)     # pinned by test H0
SEND_LIMITS = FieldLimits(2**30, 90, 120.0, 60.0)           # wall 120 s = today's TIMEOUT_SECONDS
EXIT_LIMIT = 7                                             # equal to the field module's (test H0 compares them)
```

- `TIMEOUT_SECONDS` is removed (its one use becomes `limits.wall_seconds`); `_env()` also sets
  `PYTHONDONTWRITEBYTECODE=1`.
- `run_field(argv, data, runner=subprocess.run, *, limits: FieldLimits, step: str, slots: HostSlots | None = None)
  -> tuple[int, dict]`: `step` in `("check", "send")` (`ValueError`). `slots` defaults to
  `host_slots("reading")`. Order:
  1. `with slots.hold(limits.slot_wait_seconds)`; `SlotWaitExpired` raises `ParseLimitBreach("slot", step)`.
  2. Inside the hold: the temp file as today; the command is `[sys.executable, "-m", "assetops_field.csv_upload",
     "--limit-memory-bytes", str(limits.memory_bytes), "--limit-cpu-seconds", str(limits.cpu_seconds), *argv,
     "--file", name]`, `timeout=limits.wall_seconds`, other keywords as today. `subprocess.TimeoutExpired` raises
     `ParseLimitBreach("wall", step)` (`subprocess.run` has already killed and reaped the child). The temp file is
     removed in `finally` as today.
  3. After the run: `returncode == EXIT_LIMIT` raises `("memory", step)`; `returncode == -signal.SIGXCPU`
     `("cpu", step)`; `returncode == -signal.SIGKILL` `("killed", step)`. Otherwise today's JSON reading (no JSON is
     still the `RuntimeError`).
- `ProcessFileChecker(profile=PROFILE, runner=subprocess.run, limits: FieldLimits = CHECK_LIMITS, slots=None)` and
  `ProcessReadingSender(gateway, profile=PROFILE, runner=subprocess.run, deliver=deliver_now, limits: FieldLimits =
  SEND_LIMITS, slots=None)` pass `limits`, `step` (`"check"` / `"send"`) and `slots` to `run_field`. A `limits` that
  is not a `FieldLimits` is `TypeError`. `lab_app.py` keeps constructing both with no `limits` or `slots` argument
  (test H6 reads its source).
- `ParseLimitBreach` propagates unchanged through `ProcessReadingSender.send` (it is not a `GatewayUnavailable`), so
  a breach during `send` never reaches `deliver_now`.

**Service (`reading_upload/service.py`).**

```python
PARSE_LIMIT_CAUSES = frozenset({"slot", "wall", "cpu", "memory", "killed"})
class ParseLimitBreach(Exception):
    def __init__(self, cause: str, step: str) -> None   # cause in PARSE_LIMIT_CAUSES, step in ("check", "send"),
                                                         # else ValueError; self.cause, self.step; message f"{step}: {cause}"
```
`ReadingUploadService` does not catch it: on `check` nothing was written; on `send` no `reading_upload` row is
written (the service writes the row only after `send` returns).

**API (`reading_upload_api.py`; D-ENV1.5).**

- `_LOG = logging.getLogger("assetops.reading_upload")`.
- `run(work, *, site: str | None = None, size: int | None = None)`: a new `except ParseLimitBreach as breach:`
  before `except GatewayUnavailable` logs once, `_LOG.warning("reading upload parse stopped by a limit",
  extra={"cause": breach.cause, "step": breach.step, "bytes": size, "site": site})`, and answers 503 with code and
  words by step: `check` → `READING_UPLOAD_CHECK_UNAVAILABLE`, `message("reading_upload.check_unavailable")`; `send` →
  `READING_UPLOAD_GATEWAY_UNAVAILABLE`, `message("reading_upload.gateway_unavailable")`. Both are today's codes and
  words. No file name, no content and no reading reach the log.
- `post_upload` calls `run(..., site=site_code.upper(), size=len(data))`; `get_upload` is unchanged (it parses
  nothing). The module docstring's refusal list gains one sentence: "A parse stopped by a limit answers 503 with the
  check's or the send's unavailable words (ENV-1)."

### 2.4 The loader reads bounded bytes and parses JSON only in the envelope (`load_emulated_exports.py`; D-ENV1.7)

- New helper `_bytes(path: Path) -> bytes`: opens the file, reads at most `MAX_UPLOAD_BYTES + 1` bytes; more than
  `MAX_UPLOAD_BYTES` raises `_Stop(2, "FILE_TOO_LARGE", path.name, render(refused.words))` with `refused =
  UploadRefused(413, "FILE_TOO_LARGE", {"limit_mb": MAX_UPLOAD_BYTES // 2**20})` (the intake's own words; no new
  sentence).
- In `_run`, right after `_mixed(files)` (handshake P7) and before `uploads.held`: `contents = {path: _bytes(path) for
  _, path, _, _ in files}`. The three reads (`_source_system`, the acceptor digests, the submission loop) use
  `contents[path]`; no other `read_bytes` remains in the function. A file over the cap now stops the run with exit 2
  before any submission (it was exit 3 at its turn).
- `_source_system(data: bytes, reader_id, rows, slug: str) -> str | None`: the two non-JSON branches as today; for
  `DEFAULT_READER`, `obj = default_envelope().read(READERS[DEFAULT_READER], data, ReadContext(slug,
  datetime.now(timezone.utc), False)).result.obj`; any `CanonicalRefused` (an `EnvelopeBreach` included) returns
  `None` (the submission then refuses the file with its own code, as today's `ValueError` branch does). The
  `json.loads` call is removed. `real_data=False`: the loader refuses operator databases (RC4), so its files are
  emulated.

### 2.5 Test isolation of the host slots (`backend/tests/conftest.py`, `host/conftest.py`)

Each `pytest_configure` (the existing hook; it runs in every xdist worker and in a plain run) sets
`os.environ["ASSETOPS_PARSE_SLOT_DIR"] = tempfile.mkdtemp(prefix="assetops-slots-")` unconditionally (a worker
overrides the directory it inherited from the controller), keeps the path, and removes it in `pytest_unconfigure`.
Each test process then has its own pools, as each had its own in-process semaphore before: suites, workers and lanes
never wait on each other's slots or on a running server's. S0-S5 pass their own directories. The production default
is used only outside tests.

## 3. Fixtures (built in the tests by hand, never by the code under test; W2)

- **F1** "the 2 MiB legitimate file": the profile header `timestamp_utc,pv_ac_power [kW],clinic_feeder_power
  [kW],mill_feeder_power [kW],residential_feeder_power [kW]\r\n`, then rows from `2026-01-01T00:15:00Z` every 15
  minutes, each `<t>,12.5,3.25,1.5,7.75\r\n`, as many as fit in 2,097,152 bytes (51,147 rows).
- **F2** "the 2 MiB blank file": the same header, rows `<t>,,,,\r\n` (80,655 rows): the most cells per byte.
- **F3** "the long number": the header, one row `2026-01-01T00:15:00Z,<5,000 digits "1">,1,1,1\r\n`.
- **F4**: the pinned `contract-fixtures/telemetry/generic-interval-csv-v1/kobo-window.csv` (49 rows).

## 4. Tests (written first)

`backend/tests/test_env1_parse_slots.py` (new, no database):
- **S0** `POOLS == {"commercial": 2, "reading": 2}`; `SLOT_DIR_ENV`; `host_slots("x")` is `KeyError`.
- **S1** One process: a `HostSlots(tmp, "t", 2)`; three threads each hold 0.3 s; peak concurrent holders is 2 and the
  third starts only after one releases.
- **S2** Across processes: a child process (`subprocess` running `python -c` that holds both slots of
  `HostSlots(tmp, "t", 2)` and prints `held`, then sleeps 1 s); the parent's `hold(0.2)` raises `SlotWaitExpired`;
  after the child exits, `hold(1.0)` succeeds. Then a child killed by `SIGKILL` while holding: the parent's
  `hold(1.0)` succeeds (the lock died with it).
- **S3** `slot_directory`: a directory with mode `0o755`, a symlink to a directory, and a regular file at the path
  each raise `RuntimeError`; an absent path is created `0o700`.
- **S4** `ParseEnvelope(DEFAULT_LIMITS)._host` is `host_slots("commercial")`; with `slots=HostSlots(tmp, "c", 1)`
  held by the test, a read of 3A6's `KOBO_SAMPLE` by the kobo profile reader (built as `survives()` in
  `test_3a6_parse_envelope.py` builds it) does not finish within 0.5 s, and after release it returns the same records
  as `reader.read(KOBO_SAMPLE, context=CTX)` in process.
- **S5** Constructor checks: `HostSlots` pool name, `count` `0`, `True`; `hold(0)`, `hold(-1)`; envelope `slots="x"`.

`field/tests/test_field_csv_upload.py` (added):
- **FL1** By `subprocess` (the module, never `_entry` in-process): without the flags, flags in the wrong order, `0`,
  and `-5` each exit 3 with `error == "CONFIGURATION"`.
- **FL2** With `--limit-memory-bytes 100663296 --limit-cpu-seconds 30` (96 MiB) on F2: exit 7, `error == "LIMIT"`;
  the same flags on F4: exit 0 with the preview.
- **FL3** `--limit-cpu-seconds 1` (memory 512 MiB) on F1: return code `-signal.SIGXCPU`.
- **FL4** F3 through `main` in-process: exit 2, `refusal.code == "INVALID_VALUE"`, detail `"the number has too many
  digits"`; and `CsvCollector.reports_from_bytes(F3)` raises `CsvRefused` (not `ValueError`).

`host/tests/test_up1_reading_upload_process.py` (added; existing tests change only to pass `limits=` and `step=`):
- **H0** `CHECK_LIMITS` and `SEND_LIMITS` field by field as §2.3; `up.EXIT_LIMIT == csv_upload.EXIT_LIMIT` (host
  tests may import `field/`); `TIMEOUT_SECONDS` is gone.
- **H1** A fake runner records argv: the four limit arguments follow `-m assetops_field.csv_upload` exactly, before
  the subcommand, with `CHECK_LIMITS` for `ProcessFileChecker` and `SEND_LIMITS` for `ProcessReadingSender`; the env
  holds `PYTHONDONTWRITEBYTECODE=1`; `timeout` is the limits' wall.
- **H2** Real child: `ProcessFileChecker(limits=FieldLimits(100663296, 30, 60.0, 60.0)).check(F2)` raises
  `ParseLimitBreach` with `cause == "memory"`, `step == "check"`.
- **H3** Real child: `FieldLimits(512 * 2**20, 1, 60.0, 60.0)` on F1 → `cause == "cpu"`; `FieldLimits(512 * 2**20,
  30, 0.5, 60.0)` on F1 → `cause == "wall"`, and the temp file is gone.
- **H4** Fake runners: return code `-9` → `"killed"`; return code 7 → `"memory"`; a sender whose runner returns 7
  raises `ParseLimitBreach(step="send")` and its `deliver` is never called.
- **H5** Slots: a test-held `HostSlots(tmp, "r", 1)` and `slot_wait_seconds=0.2` → `cause == "slot"`, and the runner
  was never called.
- **H6** Production limits hold the legitimate worst case: `ProcessFileChecker().check(F2)` returns a `Preview` with
  `rows == 80655`; `ProcessFileChecker().check(F1)` returns `rows == 51147`. `lab_app.py`'s source constructs
  `ProcessFileChecker()` and `ProcessReadingSender(gateway)` with no `limits` or `slots` keyword (AST read).
- **H7** After every breach of H2 to H5 the next `ProcessFileChecker().check(F4)` returns its preview (49 rows).

`backend/tests/test_up1_reading_upload.py` (added; the router with a stub service whose `upload` raises):
- **A1** `ParseLimitBreach(c, "check")` for each cause → 503, code `READING_UPLOAD_CHECK_UNAVAILABLE`, `words.key ==
  "reading_upload.check_unavailable"`; `"send"` → `READING_UPLOAD_GATEWAY_UNAVAILABLE`, its key.
- **A2** One `assetops.reading_upload` WARNING per breach with `cause`, `step`, `bytes == len(body)` (an `int`) and
  `site == "KOBO-001"`; a sentinel string placed in the body and in `file_name` appears in no captured record
  (message, args or any attribute); no other route logs.

`backend/tests/test_3a3_load_emulated.py` (added):
- **L10** A JSON batch file one byte over `MAX_UPLOAD_BYTES` (`b" " * (MAX_UPLOAD_BYTES - 1) + b"{}"`): exit 2, code
  `FILE_TOO_LARGE` on stderr with the intake's sentence, and the injected `uploads.submit` was never called, also for
  an earlier valid file in the same directory.
- **L11** `_source_system` goes through the envelope: with `default_envelope` monkeypatched to a recorder that
  delegates, a JSON batch file's look-up is one `read` with `READERS[DEFAULT_READER]` and `real_data is False`; a
  JSON file that does not parse returns `None` and the run continues to the submission (today's behaviour).
- **L12** No `json.loads` call remains in `load_emulated_exports.py` (AST).

Regression: `test_3a6_parse_envelope.py` (E0 to E9 unchanged and green), `test_3a6_source_profiles.py`,
`test_3a2_commercial_upload_service.py`, `test_up1_reading_upload.py`, the host and field files above, and D-3A6.29's
five package-scan files.

## 5. Units

| Unit | Content | Commits |
|---|---|---|
| 1 (0.35) | §2.1, §2.2, §2.4, §2.5; S0-S5, L10-L12; regression of the 3A6 files and the package scans | 1 |
| 2 (0.4) | §2.3 (field, host, service, API); FL1-FL4, H0-H7, A1-A2; select-tests set; check-all; packet | 1 to 2 |

Packet `specs/ENV1-parse-limits/packet.md`: the pre-flight figures; the host's worst case under §2 (2 × 512 MiB
commercial + 2 × 1 GiB reading, 3 GiB and 4 cores, whatever the worker count); the H6 timings; each plant of the
reviewer guide with the test that failed; the mid-build count.

## 6. Done (questions; each can fail)

1. Does every parse of upload bytes on these paths run in a child under memory and CPU limits set before its first
   read, with a bounded wall time, and is there no path that turns a limit off in production?
2. Does each breach (memory, CPU, wall, slot, killed) answer 503 or 422 with an existing code and words, never a 500
   or a hang, and does the next upload read normally?
3. Is the cause logged once, at the API layer, as codes and numbers only, with the file's content and name absent?
4. Are the parse children bounded per host across processes (S2), and does a dead holder free its slot?
5. Does the worst legitimate reading file pass under the production limits (H6), and does a 5,000-digit cell refuse
   `INVALID_VALUE`?
6. Does the loader read at most 8 MiB + 1 byte per file and parse JSON only in the envelope?
7. Are 3A6's E0 to E9 and the package-scan tests green, with no change to their files?
8. Does each plant of `reviewer-guide.md` fail its named test, and is the mid-build count 0?

## 7. Out of scope

New words for a breach (D-ENV1.5: existing words; a dedicated "too complex" sentence would wait for SC-1a, D-SC1.28);
the send's partial admission when a send is stopped mid-way (D-ENV1.4, a residual stated, today's behaviour on a
timeout too); reducing the send's three parses; request-body bounds of JSON API routes (`financial_api.py:123,190`
read the body whole, found by the sweep, D-ENV1.1: a different class, queued for the backlog); adding the
package-scan tests to fast check-all (held for the owner, row 30); cgroup or container limits.

## 8. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 | Route the reading upload through `ParseEnvelope`? | No: the field process is already the child (D4 forbids the import); it gets the same class of limits (D-ENV1.1) |
| Q2 | The reading path's limits | Measured and sized: check 512 MiB / 30 s / 60 s, send 1 GiB / 90 s / 120 s (D-ENV1.2) |
| Q3 | Per-process or per-host slots | Per host, two pools of 2 (D-ENV1.3) |
| Q4 | Words for a breach | The existing check or send "unavailable" words; no new text (D-ENV1.5; owner-away row 47, owner to weigh in) |
| Q5 | A send stopped mid-way | Answered as the send's unavailable words; partial admission stays today's residual (D-ENV1.4) |
| Q6 | A cell that crashed the child | `INVALID_VALUE` (D-ENV1.6) |
| Q7 | The loader | Bounded read before anything is submitted; JSON look-up in the envelope (D-ENV1.7) |
