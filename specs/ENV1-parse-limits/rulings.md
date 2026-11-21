# ENV-1 rulings

Architect (Claude), 2026-11-21, on the owner's delegation (`owner/owner-away-architect-decides-2026-11-21.md`).
D-ENV1.1 to D-ENV1.7 are applied by `spec.md` rev 1. Checked against `main` (`02a16011d`) by reading the four paths
and by measuring the field process on hand-built 2 MiB files under `RLIMIT_AS` (scratch launcher, since deleted).
The owner-level call is logged as row 47 of `specs/OWNER-AWAY/decisions-2026-11-21.md` (owner to weigh in).

## D-ENV1.1 The class, and what the queue line got wrong

- **Ruling.** The class is D-3A6.23's: *upload bytes are parsed only in a child process that sets hard OS limits
  before it reads a byte; the parent waits a bounded wall time; a breach is a coded answer; the parse children are
  bounded.* ENV-1 brings every path into the class, and adds one bound the class lacked: the count of children per
  **host**.
- **The queue line was inaccurate, and the honest statement is this.** `reading_upload_api.py` does not parse in the
  server process. The service's `FileChecker` and `ReadingSender` are `host/reading_upload_process.py`, which runs
  `python -m assetops_field.csv_upload` as its own process (TEL-01 D4: the backend may not import `field/`). The parse
  is already out of process; what it lacks is the rest of the class: memory and CPU limits, a breach that is answered
  (the 120 s timeout raises `subprocess.TimeoutExpired`, which the route does not catch: a 500), and a bound on how
  many run at once (one per threadpool thread, about 40).
- **Why not route it through `ParseEnvelope`.** The envelope's child rebuilds a `SourceReader` from a forkserver that
  preloads `assetops_contracts.native` only; the CSV collector is a field adapter the backend may not import (D4), and
  `send` needs the gateway channel. Wrapping the field process in the envelope would put a process inside a process
  for no bound the field process cannot set itself. So the reading path keeps its own child and gets the same limits,
  set by that child before its first read (§2.3), and the same kind of answers.
- **The sweep (W6), all of `backend/assetops_backend/` for request bodies and file reads that reach a parser:**
  - Commercial intake, profile admission, the source-profile command, the loader's submissions: in the envelope
    (D-3A6.23's sweep).
  - Reading upload: the field process, now limited (D-ENV1.2).
  - The loader's JSON look-up (`load_emulated_exports.py:151`) and its whole-file reads: now bounded and in the
    envelope (D-ENV1.7).
  - Found outside the class, not upload parsing: `financial_api.py:123` and `:190` read a JSON request body whole with
    no byte cap (`evidence_api.py` and `gateway_api.py` cap theirs). Authenticated form posts, not files: a request
    body bound is a different class. Recorded for the backlog, not built here.
  - Local operator commands (`publish_assumption.py`, `declare_objective.py`, `onboard_operator.py`,
    `load_world_inputs.py`, `sites/adapters/import_files.py`) read files the operator names on the server; not
    uploads, out of the class.

## D-ENV1.2 The reading path's limits, measured

- **Ruling.** `CHECK_LIMITS`: 512 MiB address space, 30 s CPU (hard 31), 60 s wall. `SEND_LIMITS`: 1 GiB, 90 s CPU
  (hard 91), 120 s wall (today's timeout, unchanged). Both wait at most 60 s for a host slot. `RLIMIT_FSIZE` 0 and
  `RLIMIT_CORE` 0 as the envelope. Limits are set by the field process in its `__main__` entry, before it reads the
  profile or the file; the flags are required, so a run without limits is a configuration refusal. Tests may lower
  them; production constructs the ports with the defaults only (test H6).
- **Why not the envelope's 512 MiB / 6 s / 12 s.** The reading parser is slower per byte than the commercial readers.
  Measured on this host, Python 3.12, through `python -m assetops_field.csv_upload check`:
  - F1, 2 MiB of full rows (51,147 rows, 204,588 cells): 150 MB RSS, 8.4 s CPU.
  - F2, 2 MiB of blank rows (80,655 rows, 322,620 cells, the most cells per byte): 190 MB RSS, 8.9 s CPU; refused
    by `RLIMIT_AS` 192 MiB, passes at 224 MiB.
  - Adversarial shapes are cheaper: 2 MiB of newlines 184 MB and 0.4 s; 2 MiB of commas 56 MB and 0.2 s. The parser
    is linear: the 2 MiB cap, the fixed four columns and the per-row checks bound it by construction.
  - A simulated `send` of F2 (the preview, `collect`'s second parse and texts, the admission records, the third
    parse, the printed ids): 455 MB RSS, 34 s CPU, 12.9 MB of output; refused at 384 MiB, passes at 512 MiB.
  - So 6 s CPU would refuse a legitimate 2 MiB file. The chosen limits leave 2.3x on memory and 3.4x on CPU for
    `check`, 2.2x and 2.6x for `send`.
- **Output is not capped separately.** Unlike the envelope's pickled result, the field process prints its own
  summary of a file of at most 2 MiB: at most about 13 MB (`send`'s message ids). That is linear and bounded by the
  upload cap; the parent's `capture_output` holds it once.

## D-ENV1.3 Parse children are bounded per host

- **Ruling.** `parse_slots.py`: two host-wide pools by `flock` on lock files, `commercial` with 2 slots and `reading`
  with 2, in one directory (`ASSETOPS_PARSE_SLOT_DIR`, default `<tmp>/assetops-parse-slots-<uid>`, mode 0700, checked
  before use). `ParseEnvelope.read` takes a commercial slot around each child, waiting without end (D-3A6.23 is
  unchanged: an upload waits, it is never refused for waiting). The reading ports take a reading slot, waiting at
  most 60 s, then answer as unavailable.
- **Worst case per host, whatever the number of uvicorn workers:** 2 × 512 MiB + 2 × 1 GiB = 3 GiB of child address
  space and 4 cores, plus one forkserver of about 64 MB per worker. The host has 22 GB and 8 cores. Today every
  launch in the repo is one uvicorn process, so nothing changes in practice; the bound now holds by construction
  rather than by how the server is started (3A6 review R2).
- **Why `flock`.** Standard library, crash-safe (the kernel releases a dead holder's lock), testable across processes
  (S2), no daemon and no database. A POSIX named semaphore is not freed when its holder dies; a database lock would
  put a database round trip and a connection on the parse path.
- **Why two pools.** The paths have different costs and waits: a reading `send` can hold a slot for up to 120 s, and
  a commercial upload must not wait behind it. Separate pools keep each path's stated wait true.
- **Not a widened authorisation.** The directory holds empty lock files, no secret and no data; it is created by the
  server process at run time in its own temporary area. Tests use a directory of their own (spec §2.5).

## D-ENV1.4 A breach is answered as unavailable, and a send stopped mid-way is today's residual

- **Ruling.** Causes: `slot`, `wall`, `cpu`, `memory`, `killed` (`PARSE_LIMIT_CAUSES`). Classified by the parent
  from the run alone: a slot wait past its bound, `TimeoutExpired`, exit 7 (the child's own `MemoryError` handler),
  `-SIGXCPU`, `-SIGKILL`. Any other run without JSON stays today's `RuntimeError` (503 check unavailable).
- **A send stopped mid-way.** A `send` killed after some admissions leaves them in the gateway's unreleased session
  and writes no `reading_upload` row; the answer says "could not be sent just now, so nothing was saved". This is
  today's behaviour on the 120 s timeout too (then as a 500). It is not made worse: the limits are sized so that a
  file that passed `check` under its limits stays well inside `send`'s, and a retry re-admits as
  `ALREADY_ADMITTED`. Recorded as a residual; making a send all-or-nothing is the gateway's design, not ENV-1's.

## D-ENV1.5 No new words: the existing "unavailable" words (owner-level; row 47, owner to weigh in)

- **Ruling.** A breach on `check` answers 503 `READING_UPLOAD_CHECK_UNAVAILABLE` with
  `reading_upload.check_unavailable` ("The file could not be checked just now. Nothing was saved; try again."); on
  `send`, 503 `READING_UPLOAD_GATEWAY_UNAVAILABLE` with its words. The cause is logged at the API layer
  (`assetops.reading_upload`, WARNING, `cause`, `step`, `bytes`, `site`), never in the service or the field process,
  as D-3A6.29 placed the commercial cause log.
- **Why these words are honest.** No file within the 2 MiB cap reaches the limits (D-ENV1.2: the worst legitimate
  file uses under half of each, and the parser is linear), so a breach means the host is loaded (a slot wait or a slow
  wall) or a defect, not a file that is too complex. "Try again" is the right advice for load. A dedicated "too
  large or complex" sentence like `NATIVE_TOO_LARGE`'s would be new served text, which waits for SC-1a (D-SC1.28),
  and would be untrue for the load case.
- **Owner to weigh in:** whether a reading breach should get its own sentence after SC-1a.

## D-ENV1.6 A cell that crashed the field child is `INVALID_VALUE`

- **Ruling.** `CsvCollector._value` turns the `ValueError` of `Fraction` on a number past Python's 4,300-digit
  integer-text limit into `INVALID_VALUE` with detail "the number has too many digits". Its served words ("a reading
  is not a plain number ...") are true of it.
- **The class and its sweep.** File content that raises something other than `CsvRefused`, `csv.Error` or
  `UnicodeError` in `check` is served as "try again", which cannot help. Swept `export_csv.py` and `csv_upload.py`:
  `_text` (caught), the header regex (no raise), `_timestamp` (`strptime`'s `ValueError` caught), `_value`
  (`Fraction`: the one uncaught raise), `build_report` (values already checked). One instance, fixed.

## D-ENV1.7 The loader reads bounded bytes and looks up JSON in the envelope

- **Ruling.** The loader reads each file once, at most 8 MiB + 1 byte, before any submission; a larger file stops
  the run with exit 2 and the intake's own `FILE_TOO_LARGE` words. The JSON batch's `source_system` look-up runs
  through `default_envelope()` with the canonical reader, never `json.loads` in the loader's process.
- **Why, although the loader is a local command.** 3A6 review R1: the loader may one day read operator-supplied files,
  and the look-up was the one JSON parse of upload bytes outside the envelope. The submission parses the same bytes in
  the envelope anyway, so the cost is one more child per JSON file.
- **Behaviour change, listed.** A file over the cap was refused at its turn with exit 3 after earlier files were
  submitted; now the run stops with exit 2 before any submission. Earlier is safer and the words are the same.

## Handshake answers (round 1)

Architect (Claude), 2026-11-21, on the owner's delegation. Each answer is checked against `main` (`5f8ae6c94`) and
folded into `spec.md` rev 2 and `reviewer-guide.md` rev 2. D-ENV1.8 amends D-ENV1.3; D-ENV1.10 amends D-ENV1.2's
figures into a method; D-ENV1.11 amends D-ENV1.4's cause list. Owner-level parts: row 49 of
`specs/OWNER-AWAY/decisions-2026-11-21.md` (owner to weigh in).

### D-ENV1.8 Slots are abstract socket names in one network namespace (R1, I6; amends D-ENV1.3)

- **Ruling.** A slot is an abstract-namespace Unix socket name, `"\0" + f"{namespace}.{pool}.{i}"`; holding it is
  `bind`, releasing it is `close`. The namespace is `ASSETOPS_PARSE_SLOT_NAMESPACE` when set and non-empty, else
  `assetops-parse`. No directory, no lock file, no `flock`. The scope is stated as it is: **one pool per network
  namespace**. The server (`serve_tls`), the lab app and the loader all run in the host's network namespace with the
  variable unset, so they share one pool by construction, whatever their uid, `TMPDIR` or `PrivateTmp`; a container
  or a `PrivateNetwork` unit gets its own pool and is counted as another host. The worst case is stated per network
  namespace (spec §5 packet). S2b proves two processes started with one namespace exclude each other through
  `host_slots()` itself, and a different namespace does not.
- **Why not the `flock` directory.** R1 is right: `<tmp>/assetops-parse-slots-<uid>` is shared only by processes
  with one uid and one temporary directory, so "per host" was untrue for a `PrivateTmp` unit or the loader run as
  another user. A fixed path (`/run/assetops`) would be host-wide but needs a provisioned directory, which is an
  authorisation (row 40's precedent: server directories are held for the owner). And I6 found a second problem on
  `main`: `tools/checks/configuration-persistence.ps1` rule 4 fails any backend module outside a registered writer
  that calls `.mkdir(` or `os.open(`; the spec forbids a guard change. A socket name writes nothing to disk, so the
  rule holds without an exception, and it is not a way round the rule: no file is created.
- **Why sockets are sound here.** The kernel frees the name when the holder's descriptor closes, including on
  `SIGKILL` (measured on this host: a second `bind` fails `EADDRINUSE`, succeeds after `close`). Python sockets are
  non-inheritable (PEP 446), and both the forkserver and `subprocess.run(close_fds=True)` start children without the
  descriptor. Linux only, as the envelope's forkserver and the field limits already are.
- **Residual (row 49).** An abstract name carries no permission: any process in the namespace can bind the names and
  hold the slots (commercial uploads then wait, reading answers `slot` after 60 s). Local processes are trusted for
  availability (any of them can already exhaust the host's memory or CPU); the slots are a resource bound, not a
  security boundary.

### D-ENV1.9 The send limits come from the real send through a real gateway (R2)

- **Ruling.** Pre-flight (c) runs the real `send` of F1 and F2 through `ProcessReadingSender` against a real
  `python -m assetops_gateway serve` (TEL-06a's bench: `host/tests/test_field_export_csv_proof.py`, its
  `tel4.Bench` and `_publisher` identity; the profile is the same file as `reading_upload_process.PROFILE`), and
  measures it as §0 states. `SEND_LIMITS` is set from those figures by D-ENV1.10's method, not from the simulated
  send. New test H6s: the same real send of F1 and F2 under the production memory and CPU of `SEND_LIMITS` returns a
  `Sent` (admitted plus held equal to the file's cells), never a `ParseLimitBreach`.
- **Why.** `RLIMIT_AS` counts virtual size, and the real child imports the gateway link and holds the admission
  answers; a simulated send cannot stand for it. A send killed by its own limit leaves unreleased admissions
  (D-ENV1.4), so this is the one place a mis-sized limit costs data.
- **If the gateway refuses a 2 MiB send** for a reason of its own (an IPC frame cap, a session cap), the legitimate
  worst case cannot be sent today regardless of ENV-1: a pre-flight question, before code.

### D-ENV1.10 Limits are set by a stated margin method for a stated host class (R3; amends D-ENV1.2)

- **Ruling.** For each command (`check`, `send`) over F1 and F2: the memory figure is the smallest `RLIMIT_AS` that
  passes, found by bisection at 32 MiB resolution between 128 MiB and 4 GiB; the CPU figure is the largest user plus
  system CPU of five idle runs and three runs with two children of that command at once (the pool's size). Then
  `memory_bytes` is the next multiple of 128 MiB at or above twice the largest memory figure; `cpu_seconds` the next
  multiple of 10 at or above three times the largest CPU figure; `wall_seconds` twice `cpu_seconds` (two children
  may share a core); `slot_wait_seconds` 60 (a policy, not a measurement). The Architect's single-run figures give
  check 512 MiB / 30 s / 60 s, the values spec rev 1 pinned; the send's values are outputs of pre-flight (c).
- **Stop bounds (a pre-flight question, before code):** any `memory_bytes` above 2 GiB, or a send `wall_seconds`
  above 300 s (the upload request is synchronous).
- **Host class.** The packet records the reference host (`nproc`, the CPU model from `lscpu`, `sys.version`,
  `os.getloadavg()` during the runs). The limits hold for hosts of that class. The constants live only in
  `CHECK_LIMITS` and `SEND_LIMITS` (`host/reading_upload_process.py`); retuning for a slower class means re-running
  §0's measurement on it and applying this method, with H0 and H6 moving together.
- **The cause named honestly.** A `slot` or `wall` breach is load, and "try again" is true of it. A `cpu`, `memory`
  or `crashed` breach of a file within the cap, after a 2x to 3x margin, means a host slower than its class or a
  defect, and "try again" is not true of it. Now: the log says so at ERROR (spec §2.3), so the operator sees which
  limit to re-measure. The served words stay D-ENV1.5's until SC-1a (D-SC1.28 forbids new text now). **Owner to weigh
  in (row 49):** after SC-1a, these three causes get one sentence of SC-1's statement form that says the server could
  not check the file within its limits and does not advise retrying. Default: yes, in the first unit that adds
  reading-upload text after SC-1a.

### D-ENV1.11 A child that dies without an answer is `crashed`, coded and logged (R4; amends D-ENV1.4)

- **Ruling.** `PARSE_LIMIT_CAUSES` gains `crashed`. `run_field` raises `ParseLimitBreach("crashed", step)` for a
  negative return code other than `-SIGXCPU` and `-SIGKILL` (checked before any JSON is read), and for a run that
  prints no JSON line (today's `RuntimeError`). The class (W6): every 503 of the reading-upload route is logged once
  at the API layer with codes and numbers. So the two remaining 503 branches log too: `GatewayUnavailable` with
  `cause "gateway"`, `step "send"`; `RuntimeError` (a JSON answer that is neither a preview nor a refusal, for example
  a `CONFIGURATION` exit) with `cause "error"`, `step "check"`. Their codes and words are unchanged.
- **Why.** `RLIMIT_AS` exhaustion surfaces as `MemoryError` only when Python itself allocates; a C allocation, a
  thread start or a fatal error ends in `SIGSEGV` or `SIGABRT` with no JSON, which was an unlogged 503. A limit that
  kills the child silently defeats D-3A6.29.

### D-ENV1.12 Waiting requests: a stated residual, no cap (R5)

- **Ruling.** No cap on waiting requests this unit. Residual, stated in spec §7 and the packet: a burst of uploads
  parks up to about 36 of anyio's 40 threadpool threads in the slot poll (commercial without end, reading 60 s), which
  can starve other threadpool routes; polling at 50 ms is not a queue, so a reading wait can expire while later
  requests succeed. Today the same threads run children, so this is a trade, not a regression. A cap with a coded
  refusal would be a new answer on the commercial path, whose D-3A6.23 rule is "wait, never refused".

### D-ENV1.13 Test isolation is the first statement of each hook (I1)

- **Ruling.** Confirmed as the implementer proposes, with the socket namespace (D-ENV1.8): the first statement of
  each `pytest_configure` (`backend/tests/conftest.py`, `host/conftest.py`, before the heavy-slot check and every
  early `return`) sets `os.environ["ASSETOPS_PARSE_SLOT_NAMESPACE"] = f"assetops-test-{os.getpid()}-
  {secrets.token_hex(4)}"` unconditionally, so an xdist worker overrides the controller's value. Nothing to remove
  in `pytest_unconfigure` (no file exists). Subprocess servers the tests start inherit `os.environ` and so the test
  namespace; a test that builds a server environment by hand must copy the variable (the implementer greps
  `serve_tls`/`uvicorn` launches in tests and lists them in the packet). Test S6: under pytest, `slot_namespace()`
  is not `DEFAULT_NAMESPACE`.

### D-ENV1.14 The envelope resolves its host slots at each read (I2)

- **Ruling.** `ParseEnvelope.__init__` stores `slots` as given (`None` allowed) and resolves nothing.
  `read` uses `self._slots_given or host_slots("commercial")`, so `default_envelope()` built at import or app
  construction never freezes a namespace, and construction cannot raise for the slots. A malformed
  `ASSETOPS_PARSE_SLOT_NAMESPACE` raises `ValueError` naming the variable at the first read: a configuration error of
  the operator, not a breach (test S3). S6 proves an envelope built before the variable changes reads under the new
  namespace.

### D-ENV1.15 The loader checks every file's size first and holds one file at a time (I3)

- **Ruling.** Confirmed: the look-up adds one envelope child per JSON file only; the submissions already use
  `default_envelope()`. The dict of all files is dropped. Right after `_mixed(files)`, one pass reads each file
  through `_bytes(path)` and keeps only its SHA-256 (the acceptor check uses these digests); a file over the cap stops
  the run with exit 2 before any submission. The look-up and the submission each read the file again through
  `_bytes`, so at most one file's bytes (8 MiB + 1) are held at once. A file that grows past the cap between passes
  stops the run at its turn with the same exit 2 and words (stated residual: the operator changed a file during the
  run). L10b: two files, the second over the cap, and the first is never submitted.

### D-ENV1.16 Confirmations (I4, I5, I6)

- **I4.** Confirmed: the only launcher on `main` is `host/reading_upload_process.py` (`run_field`). The module
  docstring and argparse `prog` show the two flags before the subcommand (`prog="python -m assetops_field.csv_upload
  --limit-memory-bytes N --limit-cpu-seconds N"`); `--help` without the flags is the configuration refusal, by design.
- **I5.** H6 and H6s keep the production `memory_bytes` and `cpu_seconds` and replace `wall_seconds` and
  `slot_wait_seconds` with 600 (`dataclasses.replace`), and are marked `slow`; the packet shows them run. FL3 and H3
  stand (1 s CPU and 0.5 s wall against an 8 s parse).
- **I6.** The rule stands: run `check-architecture.ps1` and `check-agent-workflow` after unit 1; an inventory entry
  a guard asks for is a mid-build question, never a guard edit. D-ENV1.8 removes the write calls the persistence
  guard would have failed on.

### D-ENV1.17 Size: 1.0 unit (was 0.75)

- Unit 1 0.4 (sockets, lazy envelope, two-pass loader, conftests); unit 2 0.6 (the field limits, `crashed`, the
  route's logs, the measured method and H6s through a real gateway).
