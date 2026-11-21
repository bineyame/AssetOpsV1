# ENV-1 review

## Round 1: discovery review (W5), 2026-11-21

Reviewer: fresh Claude reviewer (not the author). Branch `task/ENV1-parse-limits`, head `24224eceb`, diff against
`git merge-base main HEAD` = `e9d6cdfb1`. Judged against `spec.md` rev 2, `rulings.md` D-ENV1.1-17 and
`reviewer-guide.md` rev 2.

### Summary (verdict: ACCEPT WITH FIXES)

- The code matches the spec. The slots, envelope, field limits, causes, API logs, loader and conftests are all as
  specified, and the focused tests pass when I rerun them.
- The limit arithmetic follows D-ENV1.10 exactly from the raw pre-flight JSONL. The bisection brackets are sound.
- **M1:** the send's 240 s wall was never measured in the production shape. That shape is two sends sharing **one**
  gateway. I measured it: 192.8 s and 194.2 s, a 1.24x margin. The pre-flight pairs used two gateways (about 122 s).
  A wall breach on `send` is the case that costs data (D-ENV1.9).
- **M2:** after `main` (SC-1 statement guard) is merged in, the branch fails `statement_catalogue.py` with 5
  `HAND_BUILT_NEW`. The merge also conflicts in `.ai/state/index-2.md`.
- L1: plant V5 hangs H5 with no end, because the venv has no pytest-timeout. L2: two 503s of the route are not
  logged. L3: the conftest-order deviation is sound, but the mid-build count should be 1, not 0.
- M1 needs an Architect ruling: applying the margin to the measured wall gives about 390 s, which is over the 300 s
  stop bound. M2 is mechanical but touches guard data. Neither is a design defect in what was built.

### Findings

**M1 (acceptance gap in the margin method; Architect ruling needed).**
`host/reading_upload_process.py:67` sets `SEND_LIMITS = FieldLimits(896 * 2**20, 120, 240.0, 60.0)`.

- What is wrong: D-ENV1.10 sets `wall_seconds = 2 x cpu_seconds` and justifies it as "two children may share a
  core". That assumes a CPU-bound child, and `send` is not CPU-bound. In the packet's own runs, an idle F2 send uses
  36 s of child CPU over 110 s of wall. Most of the wall is time spent waiting on the gateway.
- How the pre-flight measured it: pre-flight (c) and the packet's pair runs (`pf-pairs2.jsonl`) give each child its
  own fresh `tel4.Bench`, which means its own gateway. That measures 121.6 to 125.3 s.
- Production is different. `lab_app` wires one `ProcessReadingSender(gateway)` to one demo upload gateway, so the
  two `reading` slots mean two concurrent sends into **one** gateway. That gateway is one Python process with a
  thread per connection, sharing one GIL and one SQLite ledger.
- Measured by me, through the slot pool with the worktree's code and production `SEND_LIMITS` memory and CPU (wall
  widened to 600 s to observe it), with bench state on disk:
  - two concurrent F2 sends into one bench: **192.8 s and 194.2 s**;
  - a solo control in the same window: 124.0 s.
  - Host load average was about 3 to 4.5 during the runs (another heavy slot was busy).
  - Evidence: `/opt/assetecon/evidence/ENV1/review/shared-same.json`, `shared-solo.json`, `shared_gw_pair.py`.
- Why it matters: against 240 s that is a 1.24x margin, the thinnest of all eight constants. The others run 2.2x to
  3.3x, and the packet reports the send wall as "240 s against 125 s". D-ENV1.9 names a mis-sized send limit as "the
  one place a mis-sized limit costs data": a `wall` breach on send leaves unreleased admissions. A busier host or a
  larger gateway ledger would close the remaining 46 s.
- This is not the implementer's error. The spec said "each run in a fresh bench", and the method was followed to
  the letter. The method is what misses the shared-gateway case.
- What would fix it: the Architect rules on a send wall based on a measured wall, with the shared-gateway pair as
  the pair case. Applying D-ENV1.10's 2x to 194 s gives about 390 s, which is over the 300 s stop bound, so this is
  the stop-bound question §0 reserves for the Architect. Options I see:
  - a wall rule of its own for `send`;
  - a `reading` pool for sends of 1;
  - accepting the margin as a named residual.
- Whatever the ruling, the packet should then record the shared-gateway pair as a pre-flight figure, and H0 should
  pin the result.

**M2 (merge blocker from `main` moving; mechanical).**
- What fails: merging `main` (`c76111132`) into a scratch copy of `24224eceb` (not committed, since removed) makes
  `python tools/checks/statement_catalogue.py` exit 1. Log: `/opt/assetecon/evidence/ENV1/review/sc1.log`.
  - `backend/assetops_backend/reading_upload_api.py:112, :114, :122, :126` are the four `_LOG.warning/error`
    messages. The guard's `LOG_NAMES` does not include `_LOG`; that gap is already on the backlog (`2c7bc658f`).
  - `backend/assetops_backend/parse_slots.py:73` is the `SlotWaitExpired` f-string. It is never served, because
    `run_field` turns it into a cause code.
  - The same merge also conflicts in `.ai/state/index-2.md`.
- Why it matters: the post-merge check-all on `main` would fail.
- What would fix it: rebase or merge `main` onto the branch, then resolve the 5 lines by whatever the coordinator
  rules for SC-1's ratchet. Options:
  - the SC-1a precedent (rebaseline merged text as debt, a guard-data change);
  - or, within the spec's latitude, drop the f-string message of `SlotWaitExpired`, and for the logger take an
    Architect call on renaming `_LOG` (the spec names it).
- Not a guard change by the implementer.

**L1 (test robustness; fail-fast preferred).**
- V5 (`hold` ignores `timeout`) is detected, but not as a failure in a bounded time:
  - `host/tests/test_up1_reading_upload_process.py:267-281`, H5: the test holds the only slot in its own thread and
    then calls `check`, so under V5 it waits with no end.
  - The venv has no `pytest-timeout`. Under xdist, that hangs the whole run until the coordinator's 2x cap, holding a
    heavy slot.
  - S2 (`backend/tests/test_env1_parse_slots.py:141-150`) fails only after about 61 s, once the 60 s holder exits.
  - S2b fails at its `timeout=60`.
- So the plant "fails" only because the packet's harness killed it at 30 s.
- Answer to the dispatch: a hang is acceptable as detection, but not as the failure mode.
- Fix: in H5, run `check` in a daemon thread, `join(5)`, and assert it finished with `cause == "slot"`. In S2, hold
  the second child only until signalled, or bound the wait in a thread, so V5 fails in seconds.

**L2 (ruling wording versus scope).**
- `reading_upload_api.py:92` (`READING_UPLOAD_UNAVAILABLE`, Site scope store unavailable) is not logged.
- `reading_upload_api.py:180` (`READING_UPLOAD_TEMPLATE_UNAVAILABLE`) is not logged either, and the packet does not
  mention it.
- D-ENV1.11 and §6 Q3 say "every 503 of the reading-upload route", but §2.3 enumerates only the three service
  branches in `run`, and the build matches §2.3.
- Neither is a parse 503, so this is not an acceptance gap against the design. It is ambiguity.
- Fix: the Architect narrows the wording to "every 503 of the service", or the two branches get one log line each.
  Answer to the dispatch: the unlogged site-scope 503 is acceptable under §2.3 as written.

**L3 (process; the deviation itself is sound).**
- Verified at `backend/tests/conftest.py:141-146` and `host/conftest.py:48-54`:
  - the namespace line is the second statement, directly after T1's one-line `if ...: require(...)`;
  - `require` either calls `pytest.exit` or falls through;
  - no `return` or other statement comes before the namespace line, so it runs before every early `return` in both
    hooks (the worker `return` at backend `:155` included);
  - `tools/checks/test_heavy_slot_inventory.mjs:69-77` does require `require(` as the first statement.
- S6 passes both plain and under `-n 2`, which I reran.
- What is off: this is a spec-versus-guard conflict the implementer resolved without asking, yet the packet records
  "Mid-build questions: 0".
- Fix: count it as 1 mid-build question (a spec-template defect, `.ai/RULES.md` §4 point 7), and have the Architect
  ratify the order in `rulings.md`.

**Packet note, argv index (no finding).** `test_send_reads_the_field_summary` moving from `argv[3]` to `argv[7]`
follows from the four limit arguments, and the spec allows it. H1 pins the full prefix independently.

**Preference (not a gap).** The `lab_app.py` AST check (production builds the ports with no `limits` or `slots`)
lives only in the `slow` H6, as the spec places it, so a fast run never sees that regression. It could be split out
into a fast test.

### Measurements (dispatch item 1)

I recomputed every constant from the raw JSONL in `/opt/assetecon/evidence/ENV1/2026-11-21-preflight/`.

| Step, file | Floor (pass / fail) | Max CPU s (idle and pairs) |
|---|---|---|
| check F1 | 160 / 128 | 9.10 |
| check F2 | 224 / 192 | 8.99 |
| send F1 | 288 / 256 | 34.36 |
| send F2 | 416 / 384 | 36.85 |

- Check: 2 x 224 = 448, giving 512 MiB; 3 x 9.10 = 27.3, giving 30 s; wall 60 s.
- Send: 2 x 416 = 832, giving 896 MiB; 3 x 36.85 = 110.6, giving 120 s; wall 240 s.
- All match H0. Five idle runs and three pairs exist for each step and file. The sends used a real gateway. Admitted
  plus held equals 204,588 and 322,620 on every passing run.
- The failed first pair runs (`pf-send.jsonl`, `pf-pairs.jsonl`, exit 6 `GATEWAY_REFUSED`) are the tmpfs exhaustion
  the packet describes. They are correctly excluded and re-run on disk.
- Reproducibility: the CPU spread is ±4% and the floors are deterministic to 32 MiB.
- Caveat: near the floor, CPU rises (send F2 took 38.98 s at 416 MiB and 42.02 s at 384 MiB). The method excludes
  those runs, which is harmless at 896 MiB.
- The memory and CPU margins are sound. The send wall is not (M1).

### Plants (dispatch item 4)

`plants.log` shows V1 to V4 and V6 to V19 failing their named tests, with V13 covering segv, abort and no-json, and
V18 covering both H0 and H6s F2. V5 is L1. I did not re-plant; I relied on the log.

### Checks I ran (worktree code on `PYTHONPATH`; module paths confirmed to resolve to the worktree)

- Inside one `tools/heavy-slot.sh` job (after waiting for a slot):
  - `backend`: `test_env1_parse_slots`, `test_up1_reading_upload`, `test_3a3_load_emulated`,
    `test_3a6_parse_envelope`: **114 passed**.
  - `field/tests/test_field_csv_upload.py`: **24 passed**.
  - `host/tests/test_up1_reading_upload_process.py -m "not slow"`: **29 passed, 1 deselected**.
  - `test_env1_parse_slots.py -n 2`: **8 passed**.
  - The shared-gateway bench of M1.
- `check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON` set; without it the chain-structure guard cannot find
  Python): **passed**.
- `check-agent-workflow.ps1`: **passed**.
- `git diff e9d6cdfb1 HEAD -- backend/tests/test_3a6_parse_envelope.py`: empty.
- SC-1 guard on a scratch merge with `main`: exit 1 (M2).

### Not verified by me

- H6 and H6s under production limits: I cite the implementer's run at `2cc9a941d` (`slow.log`, 3 passed). The only
  change since then is in the conftests and docs.
- The UP-1 Postgres run (packet: 8 passed).
- The package-scan files and the full fast check-all at `2a4d93cae` (packet: 40 of 40).
- The plants (log only).
- `select-tests` gave the full suite (574 of 574), which was not run; it is the coordinator's to schedule.

### Residual risk the packet does not name

- **Production shape not measured:** the shared-gateway wall (M1). Also, the gateway ledger in production is
  persistent (`gateway.sqlite3`) and grows, while every measurement used a fresh ledger, so the send wall may grow
  with ledger size.
- **Loader error path:** `load_emulated_exports._source_system` catches only `CanonicalRefused`. An envelope child
  that dies with neither an answer nor a breach raises `RuntimeError` there (`envelope.py`'s last line of `read`),
  where `json.loads` could only raise `ValueError` before. The spec defines it this way, and the submission would hit
  the same error, but the loader now exits with a traceback in that case.
- **Misclassified memory breach on send:** a `MemoryError` raised inside the field `send`'s gateway link code would
  show as `GatewayUnavailable` (WARNING, cause `gateway`) if that code catches broadly, not as `memory` at ERROR. I
  did not trace the link's exception handling.
