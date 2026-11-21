# ENV-1 handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

## Reviewer questions

**R1 (done). §2.1, D-ENV1.3: is "host-wide" real, and for whom?** The slot directory defaults to
`tempfile.gettempdir()/assetops-parse-slots-<uid>`. Two server processes share a pool only if they share uid and
`TMPDIR` (a unit with `PrivateTmp`, a container, another user, a `TMPDIR` override each get their own directory and
their own 2+2 slots). The loader CLI, run as the operator, shares the commercial pool only on the same terms.
`serve_tls.py` today runs one uvicorn process, so nothing is exercised across workers. I expect: the spec says "per
slot directory", states the worst case per directory, and names how the production start (`serve_tls`, the lab app
and the loader) gets one directory (`ASSETOPS_PARSE_SLOT_DIR` set, or a fixed path); and a test (S2 variant) that two
processes launched with the same `ASSETOPS_PARSE_SLOT_DIR` exclude each other through `host_slots()` itself, not only
through a hand-built `HostSlots`. Done changes: the "worst case ... whatever the number of workers" claim (§5
packet, D-ENV1.3) holds only under that condition.

**R2 (done). §2.3, D-ENV1.2: is `SEND_LIMITS` measured on the real send?** The send figures (455 MB RSS, 34 s CPU,
512 MiB passes, 384 MiB refuses) come from a "simulated `send`" (the preview, the second parse, admission records,
the third parse). The real child also imports `assetops_gateway.ipc`, `publish` and the credential and socket
path, and `RLIMIT_AS` counts virtual size, not RSS. Pre-flight (a) of §0 measures only `check`. H6 proves the
worst legitimate file under production limits for `check` only; nothing proves a legitimate 2 MiB `send` stays under
`SEND_LIMITS` (1 GiB, 90 s, with a 34 s simulated CPU). I expect: the pre-flight also runs the real `send` on F1 and
F2 against a stub or test gateway and prints VmPeak and CPU, and an H6 case does the same under `SEND_LIMITS`
(or the spec says why it cannot). A send killed by its own limit leaves unreleased admissions (D-ENV1.4), so this is
the case where a mistaken limit costs data, not only a retry.

**R3 (done). §0 pre-flight, D-ENV1.2: are the figures honest, and what is the margin on another host?** One
measurement per file on this host, no repeats, no stated load, and the margins (3.4x CPU, 2.3x memory on `check`)
are sized from them. `RLIMIT_CPU` is deterministic: a host 3.4x slower per CPU-second than this one (an older
laptop, a shared CI runner, the optional BeagleBone of the demo sequence) refuses a legitimate 2 MiB file, and the
answer is "try again", which cannot help. I expect: the pre-flight prints three runs (min, max) under idle and under
two concurrent children, the packet records the host (cores, Python build), and the spec states the limits are
tuned to this host class and where to change them (`FieldLimits` constants only, with H0 and H6 moving together).
Also a ruling on whether a `cpu`/`memory` breach of a file that passed on the reference host should have different
words than "try again" once SC-1a allows new text (D-ENV1.5 already records it).

**R4. §2.3 step 3 and H4: what does an unclassified death do?** `RLIMIT_AS` exhaustion does not always surface as
`MemoryError`: a C-level allocation failure, a thread start, `Fatal Python error` or a segfault gives
`-SIGSEGV` / `-SIGABRT` and no JSON. Today that falls to the `RuntimeError` branch (503 "try again") and, in the API,
is not logged (A2 says "no other route logs", but this is the same route). I expect: a negative return code other
than XCPU/KILL is its own logged cause (`crashed`, added to `PARSE_LIMIT_CAUSES`) or the `RuntimeError` branch logs
with the same `cause`/`step`/`bytes` fields, and H4 gains a case for return code `-11`. A limit that kills the child
silently, with no log, defeats D-3A6.29's purpose.

**R5. §2.1 and §2.3: what do waiting requests cost?** `hold` polls with `time.sleep` inside a threadpool thread. The
commercial wait has no end (D-3A6.23), the reading wait is 60 s; with 2+2 slots, up to about 36 of the default 40
anyio threads can sit parked in a poll loop and starve every other threadpool route (including the status
reads). Today the same threads run children, so this is a trade, not a regression, but the spec names no bound.
I expect: a stated residual (threadpool starvation under an upload burst) or a cap on waiting requests with a coded
refusal; and a note that polling at 50 ms across threads is unfair (no queue), so a 60 s wait can fail while others
succeed. Not (done) unless a cap is chosen.

## Implementer questions

**I1 (done). §2.5: the conftest hook returns early.** Both `pytest_configure` functions end with early `return`s
(`host/conftest.py`: `if config.option.basetemp is not None: return`; `backend/tests/conftest.py`: the xdist-worker
branch ends in `return`). "Set the directory unconditionally" has to go before the first return, and an xdist worker
overrides what the controller exported. I will set it as the first statement of each hook and remove it in
`pytest_unconfigure` (neither file has one today). I expect confirmation, and that tests which start their own
subprocess servers or `serve_tls` inherit the per-process directory, so none writes the production default (add a
tiny check that `slot_directory()` under pytest is not the production path).

**I2 (done). §2.2: `default_envelope()` freezes the slot directory.** `commercial/profiles.py:170` and
`composition.py:114` call `default_envelope()` at construction, which now calls `host_slots("commercial")` and
`slot_directory()` once and caches. A process whose first call happens before the test environment is set (an import-
time construction, a module-level app in `main.py`) keeps the wrong directory for its life, and a `RuntimeError`
from the directory check (§2.1) at construction would stop an app from starting. I expect: `ParseEnvelope` resolves
its `HostSlots` lazily at first `read`, or the spec says construction may raise and which message the operator sees;
and a test that `default_envelope()` built before `ASSETOPS_PARSE_SLOT_DIR` is set does not point at a stale path.

**I3. §2.4: the loader now takes the host's commercial slot and an 8 MiB x N dict.** `default_envelope().read` in the
loader process waits without end behind server uploads and, at a slot, starts a forkserver in the CLI process (not
today: the loader's submissions go through `uploads.submit`, which uses the same `default_envelope()` already,
so only the look-up is new). `contents = {path: _bytes(path) ...}` holds every file whole; a directory of many 8 MiB
files holds them all. I expect: confirmation the look-up adds one child per JSON file only, and either a per-file
read (read, look up, release) with a cap check pass first, or a stated bound on total bytes. L11 covers the
recorder; add L10 variant for a directory of two files where the second is too large and the first is not submitted.

**I4. §2.3 `_entry` and existing callers.** `python -m assetops_field.csv_upload` now refuses without the four
arguments (exit 3). The only caller on `main` is `host/reading_upload_process.py:91` (grep over `*.py`, `*.ps1`,
`*.sh`, `*.md` finds no other launcher, runbook or script). `host/tests/test_up1_reading_upload_process.py` line 3
runs the real child through the old default runner and must pass `limits=`; `field/tests/test_field_csv_upload.py`
calls `main(argv)` in process (unchanged, safe). I expect: confirmation, and that the `--help` text and the
module docstring show the flags, as the spec says.

**I5. §2.3 H2/H3/H6 timing and flake.** H6 runs two real 2 MiB parses (about 9 s CPU each) under production limits
on a possibly loaded, xdist-shared host; FL3 and H3 rely on 1 s CPU and 0.5 s wall landing before completion. A
`wall=0.5` on F1 cannot pass legitimately, but H6 under load could exceed 60 s wall only if the host is badly
starved. I expect: H6 marked for the slow tier or given its own generous wall via `FieldLimits(..., wall=120)` that
still pins the production memory and CPU values, so a loaded run cannot turn a correctness test into a timing test.

**I6. Architecture guard.** `parse_slots.py` imports `fcntl` and writes to `tempfile.gettempdir()`;
`tools/check-architecture.ps1` and its module inventories (package scans of D-3A6.29, the import-set guards) may
need `parse_slots` registered or may flag `fcntl`. I will run both guards and `check-agent-workflow` after the first
unit and report any needed inventory entry as a mid-build question, not edit a guard (spec §0 forbids it). I expect
that rule to stand.

## Architect answers

Round 1 answered in `rulings.md` "Handshake answers (round 1)" (D-ENV1.8 to D-ENV1.17), folded into `spec.md` rev 2 and
`reviewer-guide.md` rev 2. No question is left open by the Architect; the handshake closes when the Reviewer and
Implementer raise none on rev 2.
