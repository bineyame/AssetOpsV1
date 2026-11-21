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
