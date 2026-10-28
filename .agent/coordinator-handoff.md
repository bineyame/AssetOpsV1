# Coordinator handoff — 2026-10-28 (replaces all earlier versions; older text is in git history)

Read this first. Main checkout: `C:\Users\assef\Bineyame\AssetOpsV1-plan2` (branch `main`). The session start dir `AssetOpsV1` is a stale detached checkout; do not work there.

## FIRST ACTION (owner, 2026-10-28, verbatim in `.agent/owner-test-pipeline-review-2026-10-28.md`)
"once the current test ends, i want a complete review of the test pipeline to dramatically cut the runtime and memory usage, it simply is not substainable and i don't believe it is optimized. that happens on a new session with your hand-off. Then the data lane and other tasks can be considered."

So: (1) confirm the CC-M gate result below and merge if green; (2) run a **complete test-pipeline review** with the Claude Architect (it plans) and an Implementer (it confirms against code), aiming to **dramatically** cut runtime and memory. Then present the plan to the owner before implementing. The data lane, CC-D2/CC-D1 and TEL-08 come after that, unless the owner says otherwise.

Evidence for the review:
- Backend collects 4138 tests. Split into 4 parts on 2026-10-28: part 1 (1011, 382 s), part 2 (965, 1643 s), part 3 (1121, 1419 s). Part 4 (1041) took about 2 h per half with reduced workers.
- Whole-suite runs were killed twice by Claude Code's low-memory reaper, at 29% and 80%.
- Idle memory is about 2.8 GB free of 16 GB. Commit is about 20 GB. Baseline: svchost 1.5 GB, claude 1.4 GB, Chrome 1.1 GB, memory compression 1.1 GB, vmmemWSL (Docker/Postgres) 0.9 GB.
- Each Postgres test creates and drops its own `*_test` DBs via `pg_harness`.
- Many tests spawn `assetops_gateway serve` subprocesses, and each Python process appears twice: the venv shim plus Python312.
- Single TEL acceptance tests run 9–12 min (replay-rate bound). The frontend vitest suite has 3400+ tests.
- The old speed-up task is in memory `turnaround-speed-rules` and `test-suite-policy` (tiered suites).
- Fix ideas the owner was told: a `.wslconfig` memory cap, closing Chrome during runs, a fresh session, and `CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1` (owner-set env var only).

## Gate in flight at handoff
CC-M (`task/CC-M-combined-schema`, worktree `AssetOpsV1-ccm`, migrations 0036 + 0037, review ACCEPT in `.agent/CC-M-review.md`).
- Merge gate: full backend = parts 1–3 (3096 passed, 1 failed) plus part 4 run as two halves.
- The part-1 failure was a missing gitignored `var/sites/mg-001.yaml`. The coordinator copied `var/sites/` into the worktree; the builder reruns that test alone.
- Gate: total equals 4138 with 0 real failures. Then merge into main, merging main into the branch first.
- Result: SEE `.agent/CC-M-review-packet.md` in that worktree (the builder updates it). If it is not recorded there, check before merging.

## State of the demo sprint (owner-approved two lanes; Architect = Claude subagent `assetops-architect`; Planner = Codex)
Docs (only HTML now; owner removed the .md files): `Docs/demo-sprint/` holds `commercial-capability-readiness.html` (Commercial Capability Architecture), `telemetry-integration-plan-claude.html`, `telemetry-integration-plan.html` (Codex, older), `demo-data-strategy.html` (rev 4) and `long_running_proposal.html` (owner ACCEPTED 2026-10-28, `.agent/owner-long-running-accepted-2026-10-28.md`).
Build specs: `.agent/build-sequence-2026-10-27.md`, `.agent/build-spec-telemetry-2026-10-27.md` (sections A–M), `.agent/build-spec-commercial-2026-10-27.md`. Rulings are in `.agent/telemetry-rulings-2026-10-27.md`.

Telemetry lane (merged to main): TEL-00..03, TEL-04, TEL-05, TEL-05b (source gate alone withholds money; step 6 proven), TEL-06 (CSV collector).
- TEL-07 runbook and claims: built on `task/TEL-07-claims-runbook` (worktree `AssetOpsV1-tel7`), not reviewed. Its runbook needs `field_bench.py` setup/activate/read, which comes from TEL-08.
- TEL-08 BeagleBone: blocked on the owner. They run a 2-min check: USB, `ssh debian@192.168.7.2`, `cat /etc/debian_version`, `python3 --version`. If Python is under 3.11, the recommended path is a self-contained prebuilt Python (python-build-standalone armv7) copied over USB, with no SD card. The Architect must confirm the exact build. Python is required (the gateway is Python). The owner was asked to have the board ready by Thu 29 Oct noon, and also needs a firewall rule for ports 8443/5020.

Commercial lane (merged): CC-R1, CC-R2 (portfolio placement; multi-group Portfolio evidence deferred to the demo sprint per Q6).
- CC-M: gate in flight (above).
- Next: CC-D2 (post-trial reassessment, 1.75 d), then CC-D1 (productive-use, 1.75 d).
- Owner open question: overlap CC-D2/CC-D1, and start the data lane's light tasks early. Superseded by the test-pipeline review first.

Demo data lane (Lane D): owner OD answers in `.agent/owner-answers-demo-data-2026-10-28.md`; replies in `.agent/architect-reply-demo-data-od-2026-10-28.md` and `-simpler-long-run-`. Rev 4 cards DD-00..13 (about 18.25 builder-days). Lane D opens next sprint (OD-6). The suggested doc addition (rounding-ledger worked example plus drift bound of about 0.00045 C) is not yet made.

Owner telemetry/commercial answers: `.agent/owner-answers-open-questions-1/2-2026-10-27.md`, `.agent/architect-reply-owner-q2-q3-2026-10-27.md`.

Logged Lows and regressions to fold into one Sonnet fix round: `.agent/demo-sprint-lows-2026-10-28.md`. It includes a real regression: `site-tabs__link` overflows to 421 px at 390 px on the Recommendation/hold pages, which came in on main after W1-UX-06.

Other owner decisions still open (pre-sprint): the 7 design-difference rows (R453, R382, R383, R384, R385, R111, R396) and whether to start the demo-planning round.

## Rules in force (unchanged; see `.ai/ROLE_CONFIG.md` and memory)
- Plain-language owner reports, no system vocabulary. Save owner text verbatim in `.agent/` before relaying it.
- Implementers never make isolated design decisions: the Architect rules and the answers are recorded in the specs.
- Fix rounds use a Sonnet implementer. Re-reviews use a fresh Claude reviewer. Merge on ACCEPT.
- One heavy job at a time (Postgres acceptance, full suites, browser capture). Telemetry had priority until 30 Oct.
- PYTHONPATH must name the worktree, using the venv `AssetOpsV1-plan2\.venv\Scripts\python.exe`. Guards need `ASSETOPS_GUARD_PYTHON`.
- **Never `-ExecutionPolicy Bypass` or any policy override.** Run guard scripts directly. A builder tried this once and was blocked; remind every brief.
- Test DBs: `*_test` and producers' own `<prefix>_audit*` only. Never a demo or non-test DB. Kill processes by PID only.
- Keep-awake (`tools/keep-awake-during-tests.ps1 -MaxHours 168 -IdleMinutes 10080`, from the PowerShell tool) was killed 3 times by the memory reaper. Restart it only when the owner asks.
- Don't purchase hardware; the owner said "Do not purchase the ~$100 kit yet".
- Working directly on main: the coordinator committed small `.agent` tracking files on main this session. Prefer a branch next time.

## Worktrees
Active: `AssetOpsV1-ccm` (CC-M), `AssetOpsV1-tel7` (TEL-07), `AssetOpsV1-demo-plan` (docs branch; merge into main after each doc).
Merged and safe to prune when convenient: `-cc`, `-cc2`, `-tel`, `-tel4`, `-tel5`, `-tel5b`, `-tel6`, and the old `-review*` / `-ops04` / `-gap-planning`.
