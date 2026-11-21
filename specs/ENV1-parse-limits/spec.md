# ENV-1: every upload parse under hard limits, bounded per network namespace (implementer spec)

Status: spec rev 2, handshake round 1 answered (`rulings.md` D-ENV1.8 to D-ENV1.17). Architect (Claude), 2026-11-21, on the owner's delegation
(`owner/owner-away-architect-decides-2026-11-21.md`). Queued by D-3A6.23 ("Outside 3A6") and the 3A6 round-6 review
(`specs/3A6-source-profiles/review.md` "Residual risk", R1 and R2). **1.0 unit** (queued as 0.25; 0.75 at rev 1; the
handshake added the real-send measurement, `crashed` and the margin method, D-ENV1.17). Discovery review (W5): a protected
seam (upload parsing). Non-screen. No migration, no database, no served text, no guard change.
`USER_REVIEW_REQUIRED: false`. Decisions: `rulings.md` (D-ENV1.1 to D-ENV1.17). Reviewer guide: `reviewer-guide.md`.
Handshake: `handshake.md`.

- **What it is.** D-3A6.23's class, applied to every path that parses upload bytes: the parse runs in a child
  process that sets hard OS limits before it reads a byte, the parent waits a bounded wall time, a breach is a coded
  answer with its cause logged at the API layer, and the number of parse children is bounded **per network
  namespace** (the host, for every process started on it outside a container; D-ENV1.8), not per server process.
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
- **Pre-flight measurement (packet, first section; D-ENV1.9, D-ENV1.10). Before code, on `main`, through the slot
  pool**, with a scratch launcher that sets `RLIMIT_AS` in `preexec_fn` (deleted after) and the backend venv's Python:
  (a) the host class: `nproc`, the CPU model from `lscpu`, `sys.version`, `os.getloadavg()` before and after;
  (b) `check` of F1 and F2: the passing `RLIMIT_AS` floor by bisection at 32 MiB between 128 MiB and 4 GiB; user
  plus system CPU (`resource.getrusage(RUSAGE_CHILDREN)` deltas) of 5 idle runs and 3 runs with two children at once;
  (c) the real `send` of F1 and F2 through `ProcessReadingSender` (its default runner, no limits yet) against TEL-06a's
  real gateway (`host/tests/test_field_export_csv_proof.py`: `tel4.Bench`, the `_publisher` identity, written to the
  `gateway` mapping the sender takes; `deliver` a no-op), the same floor and CPU figures, each run in a fresh bench;
  (d) the arithmetic of D-ENV1.10 giving `CHECK_LIMITS` and `SEND_LIMITS`. The Architect's single-run check figures
  (F1 8.4 s CPU; F2 8.9 s, floor 224 MiB) give check 512 MiB / 30 s / 60 s. **Stop and ask** if any `memory_bytes`
  is above 2 GiB, a send `wall_seconds` above 300 s, the check's values differ from 512 MiB / 30 / 60, or the
  gateway refuses a 2 MiB send for a reason of its own (D-ENV1.9).
- **Read:** `rulings.md`; `commercial/envelope.py` (whole); `commercial_upload_api.py:130-160`;
  `reading_upload_api.py` (whole); `reading_upload/service.py:1-60, 199-275`; `host/reading_upload_process.py`
  (whole); `field/assetops_field/csv_upload.py` (whole); `export_csv.py:111-140`;
  `load_emulated_exports.py:144-256`; `backend/tests/test_3a6_parse_envelope.py:1-130`;
  `host/tests/test_field_export_csv_proof.py` (the bench, for pre-flight (c) and H6s);
  `tools/checks/configuration-persistence.ps1` rule 4 (why `parse_slots.py` makes no file system call).
- **Tests** through the slot pool only (`tools/heavy-slot.sh -- ...`), no database. Files: §4. Then
  `python tools/select-tests.py --base main` and its set; the package-scan files of D-3A6.29
  (`test_3a1_commercial_service.py` R3 and R13, `test_3a4_commercial_months.py` test 12,
  `test_4b_money_leaves.py` 11a, `test_3a3_single_writer.py`) by hand; fast check-all at the end.
- **Files.** New: `backend/assetops_backend/parse_slots.py`, `backend/tests/test_env1_parse_slots.py`,
  `host/tests/test_env1_real_send.py` (H6s). Edited:
  `commercial/envelope.py`, `load_emulated_exports.py`, `reading_upload/service.py`, `reading_upload_api.py`,
  `host/reading_upload_process.py`, `field/assetops_field/csv_upload.py`, `field/assetops_field/export_csv.py`,
  `backend/tests/conftest.py`, `host/conftest.py`, and the test files of §4. Nothing under `contracts/`,
  `simulator/`, `gateway/`, `config/`, `frontend/` or any guard; no i18n key added or changed.
- **No user-facing text** (D-ENV1.5): every answer reuses an existing code's existing words. D-SC1.28 does not apply.

## 1. Outcome and gate questions

Is every upload parse (commercial, profile admission, reading upload check and send, the loader's JSON look-up) run
in a child under hard memory and CPU limits set before it reads a byte, with a bounded wall time? Does every breach
answer with a coded refusal (never a 500, a hung request or a dead server), its cause logged by the API layer as codes
and numbers only? Is the number of parse children bounded per network namespace whatever the number of server processes, so the
host's worst case is a stated figure? Is every legitimate file within the limits by a measured margin? Is a cell that
crashed the field child now a refusal with its honest code?

## 2. Design

### 2.1 Parse slots per network namespace (`backend/assetops_backend/parse_slots.py`, new; D-ENV1.3, D-ENV1.8)

Imports exactly: `__future__`, `contextlib`, `errno`, `os`, `re`, `socket`, `threading`, `time`, `types`, `typing`.
No logging, no file system call of any kind (the persistence guard's rule 4 holds without an exception).

```python
NAMESPACE_ENV = "ASSETOPS_PARSE_SLOT_NAMESPACE"
DEFAULT_NAMESPACE = "assetops-parse"
POOLS = MappingProxyType({"commercial": 2, "reading": 2})      # pinned by test S0
POLL_SECONDS = 0.05

class SlotWaitExpired(Exception):          # the wait passed its timeout; no slot was taken
    pass

class HostSlots:
    def __init__(self, namespace: str, pool: str, count: int) -> None
    @contextmanager
    def hold(self, timeout: float | None = None) -> Iterator[int]   # yields the slot index taken

def slot_namespace(environ: Mapping[str, str] = os.environ) -> str
def host_slots(pool: str) -> HostSlots        # production: POOLS[pool] slots in slot_namespace(); one per (ns, pool)
```

- `slot_namespace`: `environ[NAMESPACE_ENV]` when set and non-empty, else `DEFAULT_NAMESPACE`. The value must
  fullmatch `[a-z0-9][a-z0-9-]{0,47}`, else `ValueError` naming `ASSETOPS_PARSE_SLOT_NAMESPACE` and the rule (not the
  value). Read at each `host_slots` call (not at import), so a test's environment applies.
- `HostSlots.__init__`: `namespace` as above, `pool` fullmatches `[a-z][a-z0-9-]{0,31}`, `count` an `int` (not
  `bool`) `>= 1`, else `ValueError`. Slot `i` is the abstract socket name `"\0" + f"{namespace}.{pool}.{i}"`,
  `0 <= i < count` (at most 86 bytes, under the 107-byte limit).
- `hold(timeout)`: `timeout` is `None` (wait without end) or a number `> 0` (`ValueError` otherwise). Loop: for `i` in
  `0 .. count-1`, `sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)`, then `sock.bind(name_i)`; an `OSError`
  with `errno == errno.EADDRINUSE` closes `sock` and tries the next; any other `OSError` closes it and propagates. If
  none is free: past the deadline (`time.monotonic()` at entry plus `timeout`) raise `SlotWaitExpired`; else sleep
  `POLL_SECONDS` and loop. On success yield `i`; in `finally`, `sock.close()`. Every hold binds its own socket, so
  two threads of one process exclude each other; the kernel frees the name when the descriptor closes, so a process
  that dies (`SIGKILL` included) releases its slot. Sockets are non-inheritable (PEP 446): no child holds a slot.
- `host_slots(pool)`: `pool` not in `POOLS` is `KeyError`. Cached per `(slot_namespace(), pool)` under a
  `threading.Lock`; returns `HostSlots(namespace, pool, POOLS[pool])`.
- **Scope, stated (D-ENV1.8).** Every process in one network namespace with the variable unset shares one pool:
  `serve_tls`, the lab app and the loader on this host, whatever their uid or temporary directory. A container or a
  `PrivateNetwork` unit has its own namespace and counts as another host. Any process in the namespace can bind the
  names (residual, row 49): the slots bound resources; they are not a security boundary.

### 2.2 The commercial envelope takes a host slot (`commercial/envelope.py`; D-ENV1.3)

- `ParseEnvelope.__init__(self, limits=DEFAULT_LIMITS, slots: HostSlots | None = None)`: stores `self._slots_given =
  slots` and resolves nothing (D-ENV1.14: `default_envelope()` built at import never freezes a namespace and cannot
  raise for the slots). A `slots` that is neither `None` nor a `HostSlots` is `TypeError`.
- `read`: inside `with self._slots:` and around the call to `self._run(...)` only (not the active counter), `host =
  self._slots_given or host_slots("commercial")` (resolved at each read), then `with host.hold(None):`. The wait has no timeout: D-3A6.23 ("further uploads wait for a slot; they are not
  refused") is unchanged. Nothing else in the file changes: limits, causes, `EnvelopeBreach`, the launcher.
- The import `from assetops_backend.parse_slots import HostSlots, host_slots` is the file's only new import (the
  package stays log-free, R13).

### 2.3 The reading upload's field process under limits (D-ENV1.2, D-ENV1.4)

**Field side (`field/assetops_field/csv_upload.py`).** (Limits below are D-ENV1.10's method outputs; the check's
are expected to be 512 MiB / 30 s / 60 s, the send's come from pre-flight (c).)

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
  but for argparse's `prog`, which becomes `"python -m assetops_field.csv_upload --limit-memory-bytes N
  --limit-cpu-seconds N"`; it stays the in-process entry its tests use (it sets no limit). The module docstring's
  usage lines gain the two flags before the subcommand. `--help` without the flags is the configuration refusal
  (D-ENV1.16).
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

CHECK_LIMITS = FieldLimits(512 * 2**20, 30, 60.0, 60.0)     # D-ENV1.10's method on pre-flight (b); pinned by H0
SEND_LIMITS = FieldLimits(<m>, <c>, <2c>, 60.0)            # D-ENV1.10's method on pre-flight (c); pinned by H0
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
  3. After the run, before any JSON is read: `returncode == EXIT_LIMIT` raises `("memory", step)`; `returncode ==
     -signal.SIGXCPU` `("cpu", step)`; `returncode == -signal.SIGKILL` `("killed", step)`; any other negative
     `returncode` `("crashed", step)` (D-ENV1.11). Then today's JSON reading, except that a run printing no JSON line
     raises `("crashed", step)` instead of the `RuntimeError`.
- `ProcessFileChecker(profile=PROFILE, runner=subprocess.run, limits: FieldLimits = CHECK_LIMITS, slots=None)` and
  `ProcessReadingSender(gateway, profile=PROFILE, runner=subprocess.run, deliver=deliver_now, limits: FieldLimits =
  SEND_LIMITS, slots=None)` pass `limits`, `step` (`"check"` / `"send"`) and `slots` to `run_field`. A `limits` that
  is not a `FieldLimits` is `TypeError`. `lab_app.py` keeps constructing both with no `limits` or `slots` argument
  (test H6 reads its source).
- `ParseLimitBreach` propagates unchanged through `ProcessReadingSender.send` (it is not a `GatewayUnavailable`), so
  a breach during `send` never reaches `deliver_now`.

**Service (`reading_upload/service.py`).**

```python
PARSE_LIMIT_CAUSES = frozenset({"slot", "wall", "cpu", "memory", "killed", "crashed"})
LOAD_CAUSES = frozenset({"slot", "wall"})          # load: WARNING; the others: ERROR (D-ENV1.10)
class ParseLimitBreach(Exception):
    def __init__(self, cause: str, step: str) -> None   # cause in PARSE_LIMIT_CAUSES, step in ("check", "send"),
                                                         # else ValueError; self.cause, self.step; message f"{step}: {cause}"
```
`ReadingUploadService` does not catch it: on `check` nothing was written; on `send` no `reading_upload` row is
written (the service writes the row only after `send` returns).

**API (`reading_upload_api.py`; D-ENV1.5).**

- `_LOG = logging.getLogger("assetops.reading_upload")`.
- `run(work, *, site: str | None = None, size: int | None = None)`: a new `except ParseLimitBreach as breach:`
  before `except GatewayUnavailable` logs once with `extra={"cause": breach.cause, "step": breach.step, "bytes":
  size, "site": site}`: a cause in `LOAD_CAUSES` at WARNING, `"reading upload parse stopped by load"`; any other at
  ERROR, `"reading upload parse stopped by its CPU, memory or crash limit; a file within the upload cap should not
  reach it: re-measure FieldLimits for this host (ENV-1 section 0)"`. It answers 503 with code and words by step: `check` → `READING_UPLOAD_CHECK_UNAVAILABLE`, `message("reading_upload.check_unavailable")`; `send` →
  `READING_UPLOAD_GATEWAY_UNAVAILABLE`, `message("reading_upload.gateway_unavailable")`. Both are today's codes and
  words. No file name, no content and no reading reach the log.
- The class (D-ENV1.11): the existing `except GatewayUnavailable` logs once at WARNING, `"reading upload send
  unavailable"`, `cause "gateway"`, `step "send"`; the existing `except RuntimeError` logs once at ERROR, `"reading
  upload check failed without an answer"`, `cause "error"`, `step "check"`; same `bytes` and `site` fields. Their
  codes and words are unchanged. Every 503 of the route is now logged exactly once.
- `post_upload` calls `run(..., site=site_code.upper(), size=len(data))`; `get_upload` is unchanged (it parses
  nothing). The module docstring's refusal list gains one sentence: "A parse stopped by a limit answers 503 with the
  check's or the send's unavailable words (ENV-1)."

### 2.4 The loader reads bounded bytes and parses JSON only in the envelope (`load_emulated_exports.py`; D-ENV1.7)

- New helper `_bytes(path: Path) -> bytes`: opens the file, reads at most `MAX_UPLOAD_BYTES + 1` bytes; more than
  `MAX_UPLOAD_BYTES` raises `_Stop(2, "FILE_TOO_LARGE", path.name, render(refused.words))` with `refused =
  UploadRefused(413, "FILE_TOO_LARGE", {"limit_mb": MAX_UPLOAD_BYTES // 2**20})` (the intake's own words; no new
  sentence).
- In `_run`, right after `_mixed(files)` (handshake P7) and before `uploads.held`: one pass `digests = {path:
  hashlib.sha256(_bytes(path)).hexdigest() for _, path, _, _ in files}` (the bytes are not kept; D-ENV1.15). The
  acceptor check uses `set(digests.values())`; `_source_system` and the submission loop each call `_bytes(path)`
  again, so at most one file's bytes are held at once. No `read_bytes` remains in the function. A file over the cap
  now stops the run with exit 2 before any submission (it was exit 3 at its turn); one that grows past the cap
  between passes stops it at its turn with the same exit and words (stated residual).
- `_source_system(data: bytes, reader_id, rows, slug: str) -> str | None` (called with `_bytes(path)`): the two non-JSON branches as today; for
  `DEFAULT_READER`, `obj = default_envelope().read(READERS[DEFAULT_READER], data, ReadContext(slug,
  datetime.now(timezone.utc), False)).result.obj`; any `CanonicalRefused` (an `EnvelopeBreach` included) returns
  `None` (the submission then refuses the file with its own code, as today's `ValueError` branch does). The
  `json.loads` call is removed. `real_data=False`: the loader refuses operator databases (RC4), so its files are
  emulated.

### 2.5 Test isolation of the host slots (`backend/tests/conftest.py`, `host/conftest.py`)

The **first statement** of each `pytest_configure` (before the heavy-slot check and every early `return`; it runs
in every xdist worker and in a plain run) sets `os.environ["ASSETOPS_PARSE_SLOT_NAMESPACE"] =
f"assetops-test-{os.getpid()}-{secrets.token_hex(4)}"` unconditionally (a worker overrides the controller's value;
D-ENV1.13). Nothing is created, so there is no `pytest_unconfigure`. Each test process then has its own pools, as
each had its own in-process semaphore before: suites, workers and lanes never wait on each other's slots or on a
running server's. Servers the tests start inherit `os.environ`; the packet lists every test that builds a server
environment by hand and shows it copies the variable. S0-S6 pass their own namespaces. The production default is
used only outside tests.

## 3. Fixtures (built in the tests by hand, never by the code under test; W2)

- **F1** "the 2 MiB legitimate file": the profile header `timestamp_utc,pv_ac_power [kW],clinic_feeder_power
  [kW],mill_feeder_power [kW],residential_feeder_power [kW]\r\n`, then rows from `2026-01-01T00:15:00Z` every 15
  minutes, each `<t>,12.5,3.25,1.5,7.75\r\n`, as many as fit in 2,097,152 bytes (51,147 rows).
- **F2** "the 2 MiB blank file": the same header, rows `<t>,,,,\r\n` (80,655 rows): the most cells per byte.
- **F3** "the long number": the header, one row `2026-01-01T00:15:00Z,<5,000 digits "1">,1,1,1\r\n`.
- **F4**: the pinned `contract-fixtures/telemetry/generic-interval-csv-v1/kobo-window.csv` (49 rows).

## 4. Tests (written first)

`backend/tests/test_env1_parse_slots.py` (new, no database):
Each test uses its own namespace `ns = f"t-{uuid4().hex[:12]}"`.
- **S0** `POOLS == {"commercial": 2, "reading": 2}`; `NAMESPACE_ENV`, `DEFAULT_NAMESPACE`; `host_slots("x")` is
  `KeyError`.
- **S1** One process: a `HostSlots(ns, "t", 2)`; three threads each hold 0.3 s; peak concurrent holders is 2 and the
  third starts only after one releases. During a hold, every descriptor in `/proc/self/fd` that was not there before
  it has `os.get_inheritable(fd) is False`.
- **S2** Across processes: a child process (`subprocess` running `python -c` that holds both slots of
  `HostSlots(ns, "t", 2)` and prints `held`, then sleeps 1 s); the parent's `hold(0.2)` raises `SlotWaitExpired`;
  after the child exits, `hold(1.0)` succeeds. Then a child killed by `SIGKILL` while holding: the parent's
  `hold(1.0)` succeeds (the name died with it).
- **S2b** (R1) Through `host_slots()` itself: two children started with `ASSETOPS_PARSE_SLOT_NAMESPACE=ns` each run
  `host_slots("reading").hold(None)`, print the slot index and sleep; a third with `ns` sees `hold(0.2)` raise
  `SlotWaitExpired`; one started with another namespace takes slot 0 at once.
- **S3** `slot_namespace`: unset and `""` give `DEFAULT_NAMESPACE`; `"a-1"` gives itself; `"A"`, `"a b"`, `"a/b"`,
  `"-a"` and 49 characters each raise `ValueError` whose message names `ASSETOPS_PARSE_SLOT_NAMESPACE` and not the
  value; a `ParseEnvelope()` built while a bad value is set does not raise, and its first `read` does (D-ENV1.14).
- **S4** `ParseEnvelope(DEFAULT_LIMITS)._slots_given is None`; with `slots=HostSlots(ns, "c", 1)`
  held by the test, a read of 3A6's `KOBO_SAMPLE` by the kobo profile reader (built as `survives()` in
  `test_3a6_parse_envelope.py` builds it) does not finish within 0.5 s, and after release it returns the same records
  as `reader.read(KOBO_SAMPLE, context=CTX)` in process.
- **S5** Constructor checks: `HostSlots` namespace and pool name, `count` `0`, `True`; `hold(0)`, `hold(-1)`;
  envelope `slots="x"`.
- **S6** (I1, I2) Under pytest `slot_namespace() != DEFAULT_NAMESPACE` and it contains `f"-{os.getpid()}-"` (so an
  xdist worker set its own, not the controller's). An envelope built with no `slots`; then the
  variable is set to a new `ns` and the test holds both slots of `HostSlots(ns, "commercial", 2)`: a read of
  `KOBO_SAMPLE` does not finish within 0.5 s, and finishes after release (the namespace is read at the read).

`field/tests/test_field_csv_upload.py` (added):
- **FL1** By `subprocess` (the module, never `_entry` in-process): without the flags, flags in the wrong order, `0`,
  and `-5` each exit 3 with `error == "CONFIGURATION"`.
- **FL2** With `--limit-memory-bytes 100663296 --limit-cpu-seconds 30` (96 MiB) on F2: exit 7, `error == "LIMIT"`;
  the same flags on F4: exit 0 with the preview.
- **FL3** `--limit-cpu-seconds 1` (memory 512 MiB) on F1: return code `-signal.SIGXCPU`.
- **FL4** F3 through `main` in-process: exit 2, `refusal.code == "INVALID_VALUE"`, detail `"the number has too many
  digits"`; and `CsvCollector.reports_from_bytes(F3)` raises `CsvRefused` (not `ValueError`).

`host/tests/test_up1_reading_upload_process.py` (added; existing tests change only to pass `limits=` and `step=`):
- **H0** `CHECK_LIMITS` and `SEND_LIMITS` field by field as the packet's D-ENV1.10 arithmetic gives them; `up.EXIT_LIMIT == csv_upload.EXIT_LIMIT` (host
  tests may import `field/`); `TIMEOUT_SECONDS` is gone.
- **H1** A fake runner records argv: the four limit arguments follow `-m assetops_field.csv_upload` exactly, before
  the subcommand, with `CHECK_LIMITS` for `ProcessFileChecker` and `SEND_LIMITS` for `ProcessReadingSender`; the env
  holds `PYTHONDONTWRITEBYTECODE=1`; `timeout` is the limits' wall.
- **H2** Real child: `ProcessFileChecker(limits=FieldLimits(100663296, 30, 60.0, 60.0)).check(F2)` raises
  `ParseLimitBreach` with `cause == "memory"`, `step == "check"`.
- **H3** Real child: `FieldLimits(512 * 2**20, 1, 60.0, 60.0)` on F1 → `cause == "cpu"`; `FieldLimits(512 * 2**20,
  30, 0.5, 60.0)` on F1 → `cause == "wall"`, and the temp file is gone.
- **H4** Fake runners: return code `-9` → `"killed"`; return code 7 → `"memory"`; `-11` and `-6` → `"crashed"`
  (with a valid JSON line on stdout too: the signal wins); return code 1, empty stdout, a traceback on stderr →
  `"crashed"`; a sender whose runner returns 7 or `-11` raises `ParseLimitBreach(step="send")` and its `deliver` is
  never called.
- **H5** Slots: a test-held `HostSlots(ns, "r", 1)` and `slot_wait_seconds=0.2` → `cause == "slot"`, and the runner
  was never called.
- **H6** (`slow`) Production memory and CPU hold the legitimate worst case: with `limits =
  dataclasses.replace(CHECK_LIMITS, wall_seconds=600.0, slot_wait_seconds=600.0)` (D-ENV1.16, I5),
  `ProcessFileChecker(limits=limits).check(F2)` returns a `Preview` with `rows == 80655`, and F1 `rows == 51147`.
  `lab_app.py`'s source constructs `ProcessFileChecker()` and `ProcessReadingSender(gateway)` with no `limits` or
  `slots` keyword (AST read), so production runs the constants H0 pins.
- **H7** After every breach of H2 to H5 the next `ProcessFileChecker().check(F4)` returns its preview (49 rows).

`host/tests/test_env1_real_send.py` (new, `slow`; D-ENV1.9):
- **H6s** TEL-06a's real gateway bench (as pre-flight (c)): `ProcessReadingSender(gateway, deliver=lambda g: 0,
  limits=dataclasses.replace(SEND_LIMITS, wall_seconds=600.0, slot_wait_seconds=600.0)).send(F1)` returns a `Sent`
  whose `admitted + held` equals the file's 204,588 cells; F2 in a fresh bench the same with 322,620; neither raises
  `ParseLimitBreach`.

`backend/tests/test_up1_reading_upload.py` (added; the router with a stub service whose `upload` raises):
- **A1** `ParseLimitBreach(c, "check")` for each of the six causes → 503, code `READING_UPLOAD_CHECK_UNAVAILABLE`,
  `words.key == "reading_upload.check_unavailable"`; `"send"` → `READING_UPLOAD_GATEWAY_UNAVAILABLE`, its key.
- **A2** One `assetops.reading_upload` record per breach, WARNING for `slot` and `wall`, ERROR for the other four,
  with `cause`, `step`, `bytes == len(body)` (an `int`) and `site == "KOBO-001"`; `GatewayUnavailable` → one WARNING
  `cause "gateway"`, `RuntimeError` → one ERROR `cause "error"`, codes and words unchanged; a sentinel string placed
  in the body and in `file_name` appears in no captured record (message, args or any attribute); no other route
  logs.

`backend/tests/test_3a3_load_emulated.py` (added):
- **L10** A JSON batch file one byte over `MAX_UPLOAD_BYTES` (`b" " * (MAX_UPLOAD_BYTES - 1) + b"{}"`): exit 2, code
  `FILE_TOO_LARGE` on stderr with the intake's sentence, and the injected `uploads.submit` was never called, also for
  an earlier valid file in the same directory.
- **L10b** (I3) Two files, the first valid and sorted first, the second one byte over the cap: exit 2 and
  `uploads.submit` never called. With `_bytes` wrapped by a recorder of `(name, len)`, the first two calls are the
  size pass over both files in order. `_run`'s AST holds no comprehension, dict or list whose element is a
  `_bytes(...)` call (no file's bytes are kept beyond its use).
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
| 1 (0.4) | §2.1, §2.2, §2.4, §2.5; S0-S6, L10-L12 (L10b); regression of the 3A6 files and the package scans; guards | 1 |
| 2 (0.6) | §0 pre-flight measurement and its arithmetic; §2.3 (field, host, service, API); FL1-FL4, H0-H7, H6s, A1-A2; select-tests set; check-all; packet | 1 to 2 |

Packet `specs/ENV1-parse-limits/packet.md`: the host class and the pre-flight figures (every run, min and max); the
D-ENV1.10 arithmetic giving each constant; the worst case per network namespace under §2 (2 × 512 MiB commercial +
2 × the send's `memory_bytes` reading, and 4 cores, whatever the worker count; a container counts as another host);
the H6 and H6s timings; the tests that build a server environment by hand (D-ENV1.13); the residuals of §7; each
plant of the reviewer guide with the test that failed; the mid-build count.

## 6. Done (questions; each can fail)

1. Does every parse of upload bytes on these paths run in a child under memory and CPU limits set before its first
   read, with a bounded wall time, and is there no path that turns a limit off in production?
2. Does each breach (memory, CPU, wall, slot, killed, crashed) answer 503 with an existing code and words, never a
   500 or a hang, and does the next upload read normally?
3. Is every 503 of the reading route logged once, at the API layer, as codes and numbers only, at ERROR for a cause
   that is not load, with the file's content and name absent?
4. Are the parse children bounded per network namespace across processes, through `host_slots()` itself (S2b), and
   does a dead holder free its slot?
5. Were the limits set by D-ENV1.10's method from measured runs, and does the worst legitimate reading file pass
   under the production memory and CPU for both `check` (H6) and the real `send` (H6s)? Does a 5,000-digit cell
   refuse `INVALID_VALUE`?
6. Does the loader read at most 8 MiB + 1 byte per file, hold one file at a time, refuse an over-cap file before any
   submission, and parse JSON only in the envelope?
7. Are 3A6's E0 to E9 and the package-scan tests green, with no change to their files?
8. Does each plant of `reviewer-guide.md` fail its named test, and is the mid-build count 0?

## 7. Out of scope

New words for a breach (D-ENV1.5: existing words; a dedicated "too complex" sentence would wait for SC-1a, D-SC1.28);
the send's partial admission when a send is stopped mid-way (D-ENV1.4, a residual stated, today's behaviour on a
timeout too); reducing the send's three parses; request-body bounds of JSON API routes (`financial_api.py:123,190`
read the body whole, found by the sweep, D-ENV1.1: a different class, queued for the backlog); adding the
package-scan tests to fast check-all (held for the owner, row 30); cgroup or container limits; a cap on waiting
requests (D-ENV1.12). **Residuals, stated:** threadpool threads parked in the slot poll under an upload burst, and a
polled wait that is not first come first served (D-ENV1.12); any process in the network namespace can hold the slot
names (D-ENV1.8, row 49); a `cpu`, `memory` or `crashed` breach is served "try again" until SC-1a (D-ENV1.10, row 49);
a loader file that grows past the cap during a run stops it at its turn (D-ENV1.15).

## 8. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 | Route the reading upload through `ParseEnvelope`? | No: the field process is already the child (D4 forbids the import); it gets the same class of limits (D-ENV1.1) |
| Q2 | The reading path's limits | By a stated margin method on measured runs, the send through a real gateway: check 512 MiB / 30 s / 60 s, send from pre-flight (c) (D-ENV1.2, D-ENV1.9, D-ENV1.10) |
| Q3 | Per-process or per-host slots | Per network namespace, two pools of 2, by abstract socket names (D-ENV1.3, D-ENV1.8; row 49) |
| Q4 | Words for a breach | The existing check or send "unavailable" words; no new text (D-ENV1.5; owner-away row 47, owner to weigh in) |
| Q5 | A send stopped mid-way | Answered as the send's unavailable words; partial admission stays today's residual (D-ENV1.4) |
| Q6 | A cell that crashed the child | `INVALID_VALUE` (D-ENV1.6) |
| Q7 | The loader | Bounded read before anything is submitted; JSON look-up in the envelope (D-ENV1.7) |
| Q8 | Words for a `cpu`, `memory` or `crashed` breach after SC-1a | One SC-1 statement that does not advise retrying (D-ENV1.10; row 49, owner to weigh in) |
| Q9 | A cap on requests waiting for a slot | None; a stated residual (D-ENV1.12) |
