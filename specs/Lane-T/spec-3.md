## Implementer questions and resolutions

Questions: `.agent/implementer-questions-telemetry-spec-2026-10-27.md` (70, numbered as there). Answered 2026-10-27 by the Architect (Claude). "Verified" names the code read; nothing was run. Every answer is already worked into the body above; the section it amends is named.

### A. Environment, branches, files

**Q-T1.** Coordinator matter. The coordinator merges this spec, `build-sequence-2026-10-27.md`, the rulings with amendment 3 and the HTML to `main` before the `-tel` worktree is cut; the builder then reads them inside the worktree. Main's rulings file must carry Amendment 2 and 3; the coordinator confirms with `git show main:.agent/telemetry-rulings-2026-10-27.md | findstr "Amendment"` before cutting. (0.1)

**Q-T2.** Coordinator matter. This spec is the task file; no `tasks/TEL-*.md` is written (a `TEL-*` name would also match `tools/check-agent-workflow.ps1`'s `tasks/T*.md` scan and fail its task-file format). The deliverables are the `.agent/TEL-*-review-packet.md` files; each packet header carries `Status: in_review` when handed to review. The PYTHONPATH line goes at the top of the TEL-00 packet and every packet. (0.1, TEL-00)

**Q-T3.** The builder edits no `.ai/` or `tasks/` file. The coordinator writes the Lane T lines in `.ai/ACTIVE_CONTEXT.md`, `.ai/CODE_STATE.md` and `tasks/README.md` at each merge, which removes the cross-lane edit conflict. (0.2)

**Q-T4.** Stop. Only the two named `.ps1` checks may change; if any other guard or `.ai/ARCHITECTURE.md` needs a `field/` entry, the builder reports it and the coordinator makes the edit at merge. (0.2)

**Q-T5.** Verified `modbustcp.html:430-470`: Figure 2a is FC 04, unit 1, address 0, count 2, transaction ID 1 (the builder's default). The expected frames for FC 01-04, the 808 frame and the Figure 2b/2c responses are now a table in TEL-02.

**Q-T6.** The TEL-04 and TEL-06 gate lists are quoted into the spec (TEL-04 gates 1-12; TEL-06 gates). The TEL-05 resolver is named (Q-T49).

**Q-T7.** Yes: the coordinator downloads and installs `pymodbus==3.16.1` before TEL-03 and records the wheel name and SHA-256 in the TEL-03 packet. No 3.13 test run on the board: the board has no pytest by design; the TEL-08 run is the Python 3.13 evidence. (0.1, TEL-08)

**Q-T8.** cwd is the worktree root; `--basetemp "$env:TEMP\assetops-tel\<file stem>"` is always passed. (0.1)

**Q-T9.** Verified `test_s6_verification_publication.py:33-35`. Host tests use `sys.path.insert` for `field/tests` and `gateway/tests`. The package is renamed `field_emulators` to avoid a generic name. The D4 scan covers non-test host modules only (amendment 2 item 2), so `host/tests` imports are allowed. `FakeCentral` is `gateway/tests/fake_central.py`. (0.4, 0.5)

**Q-T10.** Yes: every `field/tests` module is prefixed `test_field_`. (0.5)

### B. Profile and decode

**Q-T11.** The full rule set is now in 0.6: exact keys (extra or missing → `SCHEMA_INVALID` with a JSON path); `schema` must match exactly; ranges for `unit_id`, `address`, exponents, skew; `function` 3 or 4 only; `row_id` pattern and uniqueness; `quantity` keys `kind`, `point`, `sign`, `phase_aggregation` all required (`SINGLE_REGISTER` for one register). Unit-101 `quantity` values are in the TEL-05b table. The closed code set is `PROFILE_CODES` (nine codes), each with one test.

**Q-T12.** Unit-101 interval rows: span 300, cadence 300, poll period 60 (N = 5). `-1` PV: period 300 (N = 3) is final. At rate 60 that is about 8 reads per wall second, well within localhost. D10 in the Finding proof then means "all five one-minute polls answered". (TEL-03, TEL-05b)

**Q-T13.** "Contiguous" means same `unit_id`, same `function`, `address[i+1] == address[i] + words[i]`, at most 125 words; otherwise one request per register; rows are never merged. `requests_for(row)` in TEL-02.

**Q-T14.** Sentinels are compared on the **unsigned** combined raw value of each register, before two's complement, and are declared unsigned in the profile (`SENTINEL_OUT_OF_RANGE` otherwise). Vector added: int16 sentinel `[32768]` with word `8000` → `SENTINEL`. (0.6, TEL-01)

**Q-T15.** `encode_value` owns the split by contract: whole raw value on the first register, 0 on the rest. Not an integer multiple → `EncodeRefused("NOT_A_MULTIPLE")`; outside the type or equal to a sentinel → `EncodeRefused("OUT_OF_RANGE")`. Quantization is the emulator's step before encoding. `encode_sentinel(row)` writes the first sentinel on every register. (TEL-01)

**Q-T16.** Yes, measure first: the emulator test prints the window maxima and the packet records them. A value above the uint16 W range is a stop, as written. (TEL-03)

**Q-T17.** Added as `load_profile` refusals: cadence a multiple of span and both divide 86400 (`CADENCE_NOT_ALIGNED`); `output_resolution` finer than the quantum in the source unit (`RESOLUTION_FINER_THAN_QUANTUM`, moved from a TEL-03 stop to a load-time refusal); `ENUM` must be a single `uint16` (`SCHEMA_INVALID`); sentinels in range (`SENTINEL_OUT_OF_RANGE`). (0.6)

**Q-T18.** Confirmed: `.encode("utf-8")`. Verified `source_envelope.py:1076` uses `ensure_ascii=False`. (0.6)

### C. Aggregation, state sampling, clock

**Q-T19.** `session_start` is source time read after identity and `release_previous`. In replay it is clamped up to `--replay-start`, and the harness sets the wall epoch 5 s ahead, so a run started on a boundary really starts there and its first interval is `GOOD` (TEL-04 gate 11). Earlier boundaries are skipped, never published as `NO_COMPLETED_INTERVAL`. A state boundary equal to `session_start` is sampled. (0.8)

**Q-T20.** This is my decision, not the builder's: rate 120 stays for TEL-04, and the D4 skew (2 source seconds) is neither raised nor scaled. The first state attempt is sent at `B + 1`, a retry only if it can be sent by `B + 2`, and the attempt time is `clock.now()` just before `sendall`. A late first attempt is not sent: `SKIPPED_LATE`, no sample. `sleep_until` ends with a 2 ms spin. Python 3.12 on Windows has high-resolution `time.sleep` (the 15.6 ms tick no longer applies), so one-machine runs fit the 8-16 ms wall window. Cross-machine runs (TEL-08) drop to rate 12 (167 ms window) with an offset gate. Rejected: a larger bench skew (it weakens D4 in data); skew on the emulator clock (the poller cannot see it). (0.8, rulings amendment 3)

**Q-T21.** The poller owns every retry (TIMEOUT, 04, 06); the client is one transaction and never retries. Retries happen only inside the attempt window, so for a state read a 1 s timeout is never retried at rates ≥ 2. Each attempt is one raw-capture line. `--read-timeout-s` (default 1.0; TEL-04 0.25) keeps fault runs short. Card correction updated. (0.7, TEL-02, TEL-04)

**Q-T22.** `classify(results, row) -> (PollOutcome, Decoded | None)` decodes internally and lives in `modbus_tcp.py`. It imports `ProfileRow`, `decode_words`/`Decoded`/`DecodeFault` and `PollOutcome`; there is no cycle. The poller builds the `Poll`. (TEL-02)

**Q-T23.** Interval `Poll.at` is the **scheduled** instant, and only the final attempt's outcome is passed, so matching is exact equality. A duplicate instant, an instant not in `expected_polls`, or `add` after `close` raises `ValueError` (a programming error, caught by tests). The aggregator is built per span (`IntervalAggregator(row, session_start, end)`). State attempts carry real send instants and are filtered by the window. (TEL-01)

**Q-T24.** A `CONFIG_FAULT` on any register faults the whole row for the rest of the session, state or interval (RUL "the row"). The current interval closes normally with that poll missing, and later intervals publish nothing. The row is listed in `faulted_rows`. (0.7)

**Q-T25.** Both clocks take injectable `wall` and `sleep`; `sleep_until` returns at once for a past instant and re-reads the wall each loop, so an NTP step only shortens or lengthens the wait. `test_field_clock.py` uses `FakeWall` with a sleep that advances it: no real sleeping. (0.8, TEL-01)

**Q-T26.** After the JSONL window the emulator serves sentinels (interval) and, past last observation + cadence, sentinels for state. `--stop-at` is mandatory in replay mode (exit 2). (0.8, TEL-03)

**Q-T27.** Accepted as a real hole; closed three ways. (1) D10 is amended so interval polls sit at mid-period, `start + (k + ½) × period`, which tolerates ±period/2 of offset. (2) The first state attempt goes at `B + 1` and the emulator presents each state from `T − 1 s`, which tolerates an emulator up to 2 s behind. (3) TEL-08 runs at rate 12 and gates on measured NTP offsets of ±50 ms each. (0.8, TEL-03, TEL-08, rulings amendment 3)

### D. Report build and publisher

**Q-T28.** Yes. Verified `service.py:996-1044` (seal groups every unbatched envelope of any run), `:1383-1410` and `:1645-1658` (`release_run` skips a batch with another reference's envelope). `release_previous` is `seal` then `release_run(previous_ref)`, before any new `admit`. A kill between `admit` and `seal` is a TEL-04 test case, driven by the `ASSETOPS_FIELD_CRASH_AFTER_ADMIT` hook (SIMULATED only). The "no stranded batch" gate is checked on the gateway SQLite after shutdown. (TEL-01, TEL-04 gate 12)

**Q-T29.** On `SEAL_REFUSED` (raised after commit), the poller records it, still runs `release_run` for what did seal, retries at the next instant, and exits 3 after three consecutive refusals. The return keys are now defined. (TEL-01)

**Q-T30.** Sealing and releasing at every publish instant is intended. Small batches are the price of bounding what a crash leaves unsealed. TEL-04 gates count messages and receipts, not request totals. (TEL-04 Rejected)

**Q-T31.** The exact JSON is in 0.6: `tenant_id`, `site_id`, `gateway_id`, `source_mode`, `sequence_epoch` (compared), and `row_sources` (`"device/signal"` → source UUID, from snapshot `bindings[]`). It is written by `field_bench.expect_identity_from_snapshot` in the TEL-04/05 harness and by `field_bench.py setup`. Verified `snapshot.py:75-86`, `:281-330`.

**Q-T32.** Confirmed: `HELD` is data. It is counted, printed as a `FIELD-POLLER HOLD` line and tallied in `holds_by_kind`, and it is never fatal. The gateway persists the hold row itself. Only a whole-request `GatewayRequestRefused` stops the poller (exit 3). Verified `service.py:112-123`, `:771-776`. (0.6, TEL-01, TEL-04)

**Q-T33.** The retained queue is bounded at 4096 texts. Consecutive failures are counted at publish instants only, and exit 4 comes after 10 or on overflow. (TEL-04)

**Q-T34.** Wall time plus a random suffix: `field:<id>:<version>:<YYYYMMDDTHHMMSSZ>:<8 hex>`. D4 item 6 is amended in rulings amendment 3. (TEL-01)

**Q-T35.** The raw file is named `raw-<YYYYMMDDTHHMMSSZ>-<8 hex>.jsonl`, with no colons. Every attempt is captured, retries and no-answers included (`response_hex: null`), and late skips too. The status file is rewritten after every publish instant (line 148 corrected), atomically via temp file and `os.replace`. (0.6)

**Q-T36.** START, HOLD and EXIT line formats are defined in TEL-04 "Output".

### E. Modbus client and emulator

**Q-T37.** The emulator is a stdlib server with every fault native, and faults are in-process only (no CLI flags). pymodbus 3.16.1 stays as an independent **client** cross-check. Card correction recorded for the claim record. Verified the gap the question names (pymodbus' datastore server needs internal hooks for no-answer, wrong TID/unit and per-address exceptions). (TEL-03, TEL-07)

**Q-T38.** The profile `address` is the 0-based PDU address, sent verbatim. Gate: the 808 request carries `03 28`. (0.6, TEL-02)

**Q-T39.** Confirmed with one precision. A `DROPPED` interval gives 0B for every poll in its span. A `DROPPED` state gives 0B over its hold period, which the poller only samples at its boundary. `NO_VALUE_AT_BOUNDARY` holds the sentinel for its hold period (a whole cadence). (TEL-03)

**Q-T40.** TEL-03 compares the decode layer: a TEL-02 client read through `decode_words` against the timeline's expected value, at `T − S/2` (interval) or `T` (state), on a fake wall. The `NO_MEASUREMENT` versus `NO_COMPLETED_INTERVAL` allowance applies only at the aggregator layer (TEL-04/05). (TEL-03)

**Q-T41.** The sentinel goes on all three registers (`encode_sentinel`). A sentinel on one phase exists only as a decoder vector (`03E8 0000 FFFF` → `SENTINEL`). (TEL-01, TEL-03)

**Q-T42.** Outside the window the emulator serves sentinels. A profile row with no observation in the file, or a unit mismatch, makes `ObservationTimeline` refuse at construction. (TEL-03)

**Q-T43.** The emulator prints `READY <host>:<port>`, stops on SIGINT or `--stop-at`, and takes its unit IDs from the profile. (TEL-03)

**Q-T44.** Allowed: one `.gitattributes` line `contract-fixtures/telemetry/** -text`. Verified the file already pins W2/W4 fixtures this way and `core.autocrlf=true` is set. Generators write UTF-8, LF, one final LF. (0.2, 0.6)

**Q-T45.** Verified `test_registered_gateway_publication.py:182`: a run with `gateway=None` "executes, but stages nothing". The generators need no `GatewayProcess`, so the freshness file is light. `registered.request()` is called with no overrides. The exact calls are in TEL-03. (TEL-03, 0.3)

### F. Poller E2E and Postgres acceptance

**Q-T46.** TEL-04 and TEL-05 use `interval_seconds: 3600`, and the harness drives `deliver`; TEL-08 uses 30 with the real uploader. The responder is `(200, receipt_text(body))`, with `DROP` for the first two posts in test 1. The byte-identity count compares each dropped body with its retry. (TEL-04)

**Q-T47.** Verified by reading, not by running: the decision clock only stamps `decided_at` and job times (`postgres_evidence_ledger.py:14-21`, `:525-528`), and `submit`/`decide` have no age rule (`ledger_service.py:99-170`; `ledger.py:386-392` checks Foundation/binding periods only). TEL-05's first run is the check. A refusal is a stop with its row, as written, and the Architect decides; no override is added.

**Q-T48.** Confirmed. TEL-05 uses the same `converted()` and `configure()` clocks as the existing tests that admit these windows without `OUTSIDE_VALIDITY` (gateway `service.py:844-855`), and central `decide` checks the same periods. (TEL-05)

**Q-T49.** The resolver is `build_source_provenance(URL)` (`evidence/composition.py:36`), a `SourceProvenanceResolver` over `PostgresEvidenceLedger`, and `.resolve(tenant_id, site_id, evidence_ids)` works without a Finding. The gate is `state == "UNKNOWN"` with reason codes exactly `["NO_POSITIVE_BINDING"]` (`source_provenance.py:183-185`; precedent `backend/tests/test_s405_resolver_postgres.py:146-152`). TEL-05b uses `.finding_revision(...)`. (TEL-05)

**Q-T50.** The exact call: `assess --tenant-id --site-id --start 2026-09-30T03:00:00Z --end 2026-09-30T15:00:00Z --cohort <members>`, where the members are `field_bench.cohort_members(expect)` (`gateway:source:epoch` per profile source, epoch `epoch-1`), captured with `capsys`. Verified `assess_dispatch.py:44-56`, `:113-115`. The run is then read through `build_dispatch_read_service(URL).run(...)` for the evidence check. (TEL-05)

**Q-T51.** Correct, `--step v4` alone refuses `PRIOR_STEP_NOT_PUBLISHED` (verified `publish_assumption.py:79-86`). The test passes no `--step`, which publishes v1 to v4 in order. The tenant default is `demo` and `DATABASE_URL` is set to the test URL. (TEL-05b)

**Q-T52.** They are the same: the S4 Postgres tests seed through this same `publish_assumption.main(["fixture", ...])` (`test_s4_assumptions_postgres.py:68-75`). The fixture CLI is authoritative and amendment 3 says so. (TEL-05b)

**Q-T53.** Use `with TestClient(main.create_app()) as client` after `monkeypatch.setenv("DATABASE_URL", URL)`, copying `backend/tests/test_s5_overview_postgres.py:259-261`. No auth header is needed for these reads. The Finding id comes from `build_finding_store(URL).rows(...)["findings"][i]["id"]` and the revision from `build_finding_read_service(URL).finding(...)["selection"]["latest_revision_id"]`. The site list route is `/finding-index`, and both Finding reads pass `revision_id`. (TEL-05b)

**Q-T54.** I verified statically that dispatch-3.2 reads only generator state and power, feeder demand, PV available, discharge capability and SoC (`dispatch_v3.py:51-58`), all of which are in `-2`. The critical-load channels feed verification only. The scenario has raised a Finding through a gateway before (`tools/s4_finding_cases.py` F01-gateway, the prolonged scenario). TEL-05b now runs `process-jobs` then `match-findings`, the proven path (an explicit `assess` would not feed the default selection the matcher reads), and fails fast at the Finding check, so a separate probe run is not needed. If no Finding arises, the stop stands and the Architect decides. (TEL-05b)

**Q-T55.** Use `build_source_provenance(URL).finding_revision(T, S, frid)["cited_accepted_evidence_ids"]`, which reads the pinned citations of that exact revision (`source_provenance.py:255-263`). (TEL-05b)

**Q-T56.** `fresh_database()` takes no name; it resets the database named by `ASSETOPS_TEST_DATABASE_URL`, which Lane T sets to `assetops_tel_test` (Lane C uses its own). "Green twice" means two consecutive invocations of the test, each resetting through `fresh_database()`. (0.1, TEL-05)

### G. BeagleBone stage

**Q-T57.** Option (b), done without a firewall change: the builder stops `serve_tls` on the laptop for 5 wall minutes. The poller keeps publishing to the board's gateway, so a real backlog forms. The gate is `queue_count`/`sealed_pending_batches` rising then returning to 0, every batch COMPLETED, no `BATCH_ID_CONFLICT`, and no evidence gap. SSH is unaffected; processes still run under `nohup`. Card correction. (TEL-08)

**Q-T58.** `field_bench.py setup --laptop-ip --board-state-dir` writes `board/gateway.json` (shape given) and the other files; they reach the board by `scp -r` as `assetops` into `/opt/assetops/state` and `/opt/assetops/src`. Verified `__main__.py:46-92` and `uploader.py:102-141`. (TEL-08)

**Q-T59.** The command is given in TEL-08: `issue --tenant demo --site KOBO-001 --gateway <gateway_external_id> --enable-source <source_external_id>`, one per snapshot source, with `--credential-out`. Verified `provision_gateway.py:57-130` and snapshot `gateway`/`sources` keys (`snapshot.py:241-271`). (TEL-08)

**Q-T60.** TLS uses Git's `openssl.exe` (present; `cryptography` is not installed), with a self-signed certificate that is its own CA (precedent `tools/s2_demo_walkthrough.py:142`). The evidence read sends no auth header; the `Authorization` handling in `evidence_api.py` is for gateway uploads. (TEL-08)

**Q-T61.** No venv: board processes run `/usr/bin/python3` directly. LAN internet is assumed for `apt install systemd-timesyncd` if it is missing; no NTP is a stop. Credential files are mode 600, owned by `assetops`. (TEL-08)

**Q-T62.** `PYTHONDONTWRITEBYTECODE=1`, an explicit file set, and the hash command excludes `__pycache__` and `.pyc`, run identically on both ends. (TEL-08)

### H. Claim records, runbook, CSV

**Q-T63.** The showing uses `assetops_tel_show_test`, built by `field_bench.py setup` and never touched by pytest. The terminal reads are `field_bench.py read --what ...` (JSON); `findings` only after a `-2` run. (TEL-07, TEL-08)

**Q-T64.** The §10.0 field list is complete. The R-levels, the TEL-05 statement and the "Not claimed" lines are given in TEL-07.

**Q-T65.** CSV rows use `csv: {"column"}`, with the forbidden and required keys listed in 0.6. `ProfileRow` gains `csv` and its register fields become optional. `CsvRefused` is a plain class with `__init__`, since the frozen dataclass form would not construct. Codes, unit-header grammar (`name [unit]`, unit passed through), `.` decimal separator, timestamp format, ordering and duplicate rules are in TEL-06.

**Q-T66.** The rule applies to TEL-06 files only. (TEL-06)

### I. Small contradictions

**Q-T67.** If TEL-03 slips, the coordinator merges TEL-01+02 alone from `task/TEL-01-field-core` at the reviewed commit (review T1 then covers TEL-01+02). TEL-03 continues on `task/TEL-03-emulator`, cut from `main` after that merge, and is reviewed separately. Lane C always merges from `main`. (0.1; build-sequence edit listed in the report)

**Q-T68.** The freshness file is light: no gateway and no database (Q-T45). It runs as its own file. The "8 h prolonged run" is a simulator run in memory. (0.3)

**Q-T69.** The harness waits real wall time (≥ 3 s inside the pause window) and reads `source_contacts[].last_contact_at` before and after. Contact is stamped on admit, in wall time (`service.py:685`, `:1103-1117`). `inject_fault CLOCK_OFFSET` is not used. (TEL-04 gate 7)

**Q-T70.** Confirmed. `GatewayProcess` creates and protects `gateway.credential` via `serve` → `ensure_credential`, owner-only for the current user. The poller subprocess runs as that user and `GatewayLink` reads the file per call (`ipc.py:164-167`). (TEL-04)

### J. TEL-T1 rulings (Architect, Claude, 2026-10-27; questions in `.agent/TEL-T1-questions.md`)

**TEL-T1-Q1.** Confirmed: on a row with registers of mixed widths, every sentinel must fit the narrowest register of the row, or the profile is refused with `SENTINEL_OUT_OF_RANGE`. (TEL-01)

**TEL-T1-Q2.** Confirmed: `sentinels` stays a `frozenset`, and "first sentinel" (Q-T15, `encode_sentinel`) means the smallest declared sentinel, `min(row.sentinels)`. (TEL-01)

**TEL-T1-Q3.** Confirmed: a wrong function code (neither the request's nor its exception form), or a byte count that disagrees with the MBAP length, is `NO_ANSWER` kind `RESET`. The connection is dropped and the read is not retried. A well-framed answer with the wrong word count is `WORDS` → `CONFIG_FAULT`. (TEL-02, 0.7)

**TEL-T1-Q4.** Confirmed: exception codes the 0.7 table does not name (05, 07, 08, ≥ 0x80) → `FAILED`, with no sample and no retry; the raw capture keeps the code. (TEL-02, 0.7)

**TEL-T1-Q5.** Confirmed: the emulator decides quantization on **row** status (`row.status == "ILLUSTRATIVE"`), never on profile status. The `-2` unit-100 `pv-ac-output` row is copied from `-1` with row status `UNPINNED`, so it stays quantized. TEL-05b adds an emulator test for both cases. (TEL-03, TEL-05b)

**TEL-T1-Q6.** Deferred to TEL-04: `modbus_poller.new_session_ref(profile, wall_now, token=lambda: secrets.token_hex(4)) -> str`. It returns `field:<profile_id>:<profile_version>:<YYYYMMDDTHHMMSSZ>:<8 lowercase hex>` (Q-T34), and a unit test checks the format with an injected token. (TEL-04)

**TEL-T1-Q7 (finding: rational source values).** `registered.request()` uses `simulator-lab-publication:3`, so the `-1` JSONL carries exact rationals (e.g. `1035/19`). The 0.000001 premise in the TEL-03 representability paragraph holds only for the registered-Kobo profiles (V1-V4). The rule stands as built: the fixture keeps v3, and the emulator quantizes GX rows to the register resolution. **TEL-04/05 compare at the emulator register resolution, exactly, with no tolerance and no floats:**
- `expected = quantize_half_even(gx_server.presented_value(row, Fraction(obs.reported_value)), row.output_resolution)` (0.001 kW for PV, 1 % for SoC; the second step is a no-op for `-1`). Use only the existing helpers.
- For every `GOOD` report whose observation is `REPORTED`, `Fraction(envelope value text) == expected`.
- An independent bound check: `abs(arrived - Fraction(obs.reported_value)) <= q / 2`, with `q = register_quantum × 10^(scale_exponent + unit_exponent)` in the source unit.
- Outcomes are compared as in Q-T40.
- TEL-05b unit-101 (`ILLUSTRATIVE`) rows compare `arrived == Fraction(obs.reported_value)` exactly. V4 publishes at 0.000001, which is the int32 exponent −6 register resolution. `NOT_A_MULTIPLE` there is a stop, not a reason to quantize.
- The claim record adds "source values are exact rationals from simulator-lab-publication v3". (TEL-03 claim, TEL-04, TEL-05, TEL-05b)

### K. TEL-04 rulings (Architect, Claude, 2026-10-27; questions in `.agent/TEL-04-questions.md`)

**TEL-04-Q1. Change.** Any `GatewayUnavailable` before START (`check_identity` or `release_previous`) → exit 4, including a missing or unreadable credential file (`ipc.py:135-143`). There is no in-process retry. Stderr gets `FIELD-POLLER gateway unavailable before start: <detail>`. There is no START and no EXIT line, and `session.json` is not written or rewritten, so the next start retries `release_previous` with the same reference. Tests: a subprocess offline run → 4, with no START, no EXIT and no `session.json`; an in-process `main()` with `release_previous` monkeypatched to raise → 4, with `session.json` unchanged. Exit code 4 now also reads "or unavailable before START". (TEL-04)

**TEL-04-Q2. Change.** `GatewayUnavailable` at the final step → exit 4. Stderr gets one line, `status.json` is rewritten, and `FIELD-POLLER EXIT 4 <status>` prints with `retained_reports` = the texts still held. There is no retry. A refusal stays exit 3. (TEL-04)

**TEL-04-Q3. Change.** Loop step 5 becomes `Poller.finish()`: `sleep_until(stop_at)`; if any texts are retained, `admit` them in order through the publish path (crash-hook count, `_count`, HOLD lines, clear); then `seal_and_release` and `_sealed`. On `GatewayUnavailable`, keep `retained` and raise exit 4 (Q2). Tests use `finish()` in process over `FakeLink`: retained 2 → ops `admit, seal, release_run`, with reports in order and retained cleared; admit unavailable → 4, ops `admit`, `retained_reports == 2`; nothing retained and seal unavailable → 4, ops `seal`. (TEL-04)

**TEL-04-Q4. Confirmed.** An EXIT line prints if and only if START printed. Pre-START exits 2, 3 and 4 go to stderr only. Exit 9 prints nothing. Add an `exit_line is None` assertion to the exit-2 test and to the Q1 tests. (TEL-04)

**TEL-04-Q5. Accepted.** Gate 7 wording, corrected: the harness reads `diagnostics` once `status.last_publish_instant` equals the pause start (the last pre-pause admission), and again ≥ 3 s of wall time later, while the status still shows that instant. For the paused sources, `last_contact_at` is unchanged and `observed_at − last_contact_at` grew by ≥ 2 s. (TEL-04 gate 7, Q-T69)

**TEL-04-Dev1. Accepted (Q-T46 corrected).** The FakeCentral responder routes by path. The batch route gets `(200, receipt_text(body))`, with DROP for the first two **batch** posts. `.../diagnostics` posts get 201 `{"diagnostic_id", "received_at", "payload_sha256"}` (`gateway/tests/test_gateway_upload.py:503-506`), and any other path fails the test. Gate 6 counts batch requests only. TEL-05 uses the same diagnostics answer beside its real ingestion responder. (TEL-04, TEL-05)

**TEL-04-Dev2. Accepted (harness delivery rule).** `deliver_all`: `deliver {"max_batches": 50}` until `batches.attempted == 0`, then, while `diagnostics.queue.sealed_pending_batches > 0`, sleep 1 s and repeat. It asserts at a 120 s cap. This replaces "deliver until `attempted == 0`" in TEL-04, TEL-05 and TEL-05b. (TEL-04, TEL-05, TEL-05b)

**TEL-04-Dev3. Accepted.** This is the same item as TEL-04-Q5. (TEL-04)

### L. TEL-05b rulings (Architect, Claude, 2026-10-28; questions in `.agent/TEL-05b-questions.md`)

**TEL-05b-Q1. Confirmed, with one addition.** Step 5's bare path is a spec slip: `parse_request` requires `domain`, `from` and `to` (`analytics/finding_index.py:131-141`). The request is `GET /api/sites/KOBO-001/finding-index?domain=mini-grid-dispatch&from=2026-10-13T00:00:00Z&to=2026-10-14T00:00:00Z`. Two answers pass: (a) 200 where every row has `amount.state == "UNAVAILABLE"`, and, if the body's `status` is `CURRENT`, at least one row exists (the 2026-10-13 Finding lies in the window, so an empty CURRENT page is a defect, not a pass); (b) 409 `PERFORMANCE_CUTOVER_CLOSED` with `rows: null`. In both cases no `current_amount_shown` or `presented_as_current` is true anywhere in the body. Any other status fails the test. Step 5 of the TEL-05b card now reads with this query. (TEL-05b)

**TEL-05b-Q2. Yes: zero is a stop.** With no consequence head, `source_gate(None)` returns `MIXED_OR_UNKNOWN_SOURCE` (`evidence/provenance_read.py:35-39`, `financials/consequence_read.py:228-236`). The gate would then pass without any amount to withhold. That is the missing-amount case that owner Q5 and amendment 2 item 5 exclude. The test asserts, after step 4: (1) at least one `financial_consequence_revision` exists for (`fid`, `frid`); (2) at least one of them has `state == "PRICED"` with non-null `amount.low`/`amount.high`, which shows that a figure exists; (3) the head read and each pinned read show `presented_as_current == false`, `currentness.current_amount_shown == false`, and `"MIXED_OR_UNKNOWN_SOURCE"` in `withheld_reasons`; (4) each revision's own `source_provenance.state == "UNKNOWN"`. If (1) or (2) fails, stop and report the `recompute_consequences` output and the price selection for the window. Do not tune the prices, the window or the code; the Architect decides. Added to the TEL-05b Stop list. (TEL-05b)

**TEL-05b-Q3. Accepted as built, plus a source-gate isolation read (2026-10-28, after gate runs A and B).**

*Stricter stop.* The reviewer accepts the builder's rule: every gated Finding must have at least one consequence revision, or the test stops. It is stricter than L-Q2 (1). It cannot hide a money-gate defect. Its only cost is a stop that goes to the Architect, and with one Finding per run it changes nothing today. L-Q2 (2), at least one PRICED revision with amounts, still applies to the 2026-10-13 Finding.

*Confound: it matters.* The API reads withhold the amount for three reasons: `AUDIT_ONLY`, `SOURCE_CLOSED` and `MIXED_OR_UNKNOWN_SOURCE`. The S3 performance cutover is closed for the test Site, and `consequence_read.py:187-190` sets `AUDIT_ONLY` before the source gate is reached. The claim record wording ruled in amendment 2, item 6 ("Money: not shown, by the existing source gate") and owner Q5 ("withheld because the source is not established") both name the source gate as the reason. Runs A and B show that this gate fails. They do not show that this gate alone withholds the amount on this revision. Opening the cutover is rejected: it needs a PASSED Performance comparison for this run's field data, which is new setup that could need tuning. A fakes-only unit test is also rejected, because it would not read this revision. That generic case is already covered by `backend/tests/test_lr01_money_eligibility_postgres.py:290-315`.

*Ruling: one read-only step 6 in `test_gx_profile_2_raises_a_finding_with_no_money_shown`, after step 5, on the same `fid`, `frid` and head.* It follows the existing pattern in `test_lr01_money_eligibility_postgres.py:290-302`. Call `build_consequence_read_service(URL).read(T, S, fid, frid, finding_revision_is_latest=True, source_open=True)` and assert exactly:
1. `currentness.state == "CURRENT"` and `currentness.reasons == []`;
2. `currentness.money_eligibility == "ELIGIBLE"`;
3. `consequence.state == "PRICED"`, `consequence.is_head is True`, and `amount.low` and `amount.high` are non-null and equal the head's stored amounts;
4. `currentness.source_gate == {"state": "UNKNOWN", "permits_current_money": False, "reason": "MIXED_OR_UNKNOWN_SOURCE"}`;
5. `currentness.withheld_reasons == ["MIXED_OR_UNKNOWN_SOURCE"]`, as an exact list;
6. `consequence.presented_as_current is False` and `currentness.current_amount_shown is False`.

Print the whole `currentness` block past capsys for the claim record. Steps 1-5 and their assertions are unchanged. No production code changes, and nothing is tuned.

*Stop.* If assertion 1, 2 or 3 fails, the amount is also withheld for a reason other than the source. Stop and report the read. Do not tune. The TEL-07 claim then uses the fallback wording below. If assertion 4, 5 or 6 fails, the source gate has a defect. Stop immediately and report it to the Architect.

*Claim record (TEL-07).* If step 6 passes, keep the wording from item 6 and add: "On the same revision with the performance cutover treated as open, the only reason the amount is withheld is `MIXED_OR_UNKNOWN_SOURCE`. Through the API, it is also withheld as `AUDIT_ONLY`/`SOURCE_CLOSED`, because the test Site has no Performance comparison." Fallback wording, used only if 1-3 fail: "Money: not shown. The amount is withheld because the source is not established, and on this test Site also because the performance cutover is closed. This run does not show the source gate as the only reason."

*Runs.* One more Postgres run on a freshly created `assetops_tel5b_test` is needed. The new step only reads, and runs A and B already showed steps 1-5 green twice, so one green run of the amended test closes the gate. (TEL-05b, TEL-07)

**TEL-05b-Q4. The first-boundary state-read race (review H1). Ruling: a warm-up connect in the poller; the oracle stays exact (2026-10-28, after the review REJECT).**

*Cause, from the code.* `poll_state` checks lateness once, before the attempt (`modbus_poller.py:299-306`), and `clock.now()` floors to whole source seconds. A state read is therefore skipped only if its check happens at `B + 3` s or later. At rate 60, that is 33 ms of wall time after the `B + 1` wake. Profile `-1` (TEL-04, TEL-05) has one STATE row per boundary. Its check comes straight after the wake, so the connect cost falls after the check and is never inside the window. Profile `-2` has two STATE rows on each 300 s boundary, and both are read at `B + 1`. The SoC check has to wait for the generator-status read to finish. At 03:00:00Z (boundary = session start) the generator-status read is the first read of the session. It pays for `socket.create_connection` and for the emulator spawning its handler thread. On the failing run, that took more than 33 ms. The other 96 boundaries passed on all four runs, so the steady-state margin is sufficient. The failure is the cold first transaction, not the rate.

*Ruling.*
1. **Warm-up connect (product change, `field/assetops_field`).** Add `ModbusTcpClient.open() -> bool`. If `_socket` is set, it returns True. Otherwise it calls `socket.create_connection` with `timeout_s` and sets `TCP_NODELAY`, as `_connect` does. On any `OSError` it leaves `_socket` at None and returns False. It sends no bytes, writes no raw-capture line and changes no counter. In `main()`, build the client before `clock.sleep_until(session_start)` and call `open()` there. If it fails, print one stderr line, `FIELD-POLLER warm connect failed: <error>`, and continue. The first read then reconnects lazily as it does now, so every outcome and fault path is unchanged. The START line is not changed. This is what a real poller should do anyway: holding one persistent connection (the TEL-02 contract) means opening it before the first scheduled read, not inside it.
2. **The oracle stays exact.** `_expected_run_2` keeps zero `SKIPPED_LATE`, and `_arrived_2 == expected` and `counters == oracle counters` are unchanged. The expectation is not derived from the poller's recorded skips. That would be circular: the poller's own late check would excuse its own missing reads, and the gate would no longer claim coverage (every expected read landed and arrived exactly), only consistency. The only addition is a diagnostic. When the comparison fails, print the raw-capture lines (`at`, `wall_at`, `scheduled_at`, `row_id`, `outcome`) for each missing or extra key before the assertion, so that a timing skip is told apart from a value defect at once. It prints only. It does not tolerate anything.
3. **Rejected.** A wider `state_skew_max_seconds` changes D4 in the data, and Q-T20 already rejected it. A lower rate (30) would double the run to about 18 min, only doubles a margin that steady state does not need, and leaves the cold connect inside the window. An oracle that accepts a counted `SKIPPED_LATE` weakens the claim, as point 2 explains.
4. **Margin evidence.** From the raw capture of the green run, the packet records two numbers: at 03:00:00Z, the SoC send `wall_at` minus the generator-status send `wall_at`; and the maximum of that delta over all boundaries. Both are compared with the 33 ms budget. It also records the counters line.
5. **Stop.** If any `SKIPPED_LATE` occurs after the warm-up, stop and report the raw-capture lines for that boundary to the Architect. Do not rerun until green. Do not tune the rate, the skew or the oracle.

*TEL-04 and TEL-05 (at main).* They do not carry this race. Each boundary has one state read and the check precedes the connect. The only generic exposure left is a wake more than 2 source seconds late (33 ms at rate 60, 25 ms at rate 120 for TEL-04). It has never occurred, and the 2 ms spin bounds it. They need no test change. They inherit the warm-up through the poller, and their oracles stay exact (TEL-04 already asserts `SKIPPED_LATE == 0`, `test_field_modbus_tcp_proof.py:536`).

*TEL-08 (BeagleBone, rate 12).* It inherits the race in kind, at five times the margin. The skip point is `B + 3` = 250 ms of wall time, so the budget after the `B + 1` wake is 167 ms. It is exposed only on the `-2` stretch, where two state reads share a boundary. Profile `-1` is exposed only to a late wake. The warm-up removes the LAN connect from the window. What remains is the board's own latency: a slower CPU, and a raw-capture append to the SD card between the two state reads, which can occasionally stall for tens of milliseconds or more. The ruling is the same: an exact oracle, the same margin numbers in the TEL-08 packet, and any `SKIPPED_LATE` is a stop reported with the raw-capture lines. A skip on the board is a measured board fact for the claim record, not something to tune away.

*Runs and checks.* `field/tests` plus focused tests for `open()`: (a) against the emulator, `open()` returns True, the following read reuses the socket and the emulator accepts exactly one connection; (b) against a closed port, it returns False, `_socket` stays None and the next read returns `NO_ANSWER`/`REFUSED`, as now. One TEL-04 end-to-end file run, because the poller changed. One TEL-05b Postgres run on a freshly created `assetops_tel5b_test`, by the builder. Then the reviewer takes an independent fresh-DB run, which is the reproducibility test H1 asked for. The TEL-05 Postgres gate is not rerun: its poller path is the same as in TEL-04 apart from central. Run time is unchanged at about 9 min. The packet adds this risk and its closure to the residual-risk section. (TEL-05b, TEL-04, TEL-05, TEL-08, TEL-07)

### M. TEL-06 rulings (Architect, Claude, 2026-10-28; questions in `.agent/TEL-06-questions.md`)

This section is the current TEL-06 card. Where it is more specific than the TEL-06 body, it wins. Verified by reading: `backend/conversions/kobo-001-bindings.json` (roles), the `-1` JSONL and its manifest (SHA `3d62a831…` matches the file), `field/assetops_field/profile.py:340-357` (CSV rows skip the register and phase checks), `gateway/assetops_gateway/service.py:691-707` (the unit check runs before the `report_key` dedup; dedup returns `ALREADY_ADMITTED` with the earlier `message_id` and `sequence`) and `:996` (`seal` returns only new batch IDs), and `host/tests/test_field_modbus_tcp_proof.py:130-209` (`Bench`). Nothing was run.

**TEL-06-Q1. The profile.** The source is the `-1` JSONL (`kobo-public-observations-v1`), as the card's Fixture row says. The rows are the four KOBO-001 interval signals that have a role the plan card names and are present in that JSONL:

| `row_id` | `device_id` / `signal_id` | `role` | `csv.column` | `quantity.point` | `quantity.sign` |
|---|---|---|---|---|---|
| `pv-ac-power` | `pv-inverter-controller` / `ac-power` | `pv_power` | `pv_ac_power` | `PV inverter AC output, as exported` | `positive = power delivered to the AC bus` |
| `clinic-feeder` | `clinic-meter` / `active-power` | `feeder_demand` | `clinic_feeder_power` | `clinic feeder meter, as exported` | `positive = power drawn by the feeder` |
| `mill-feeder` | `mill-meter` / `active-power` | `feeder_demand` | `mill_feeder_power` | `mill feeder meter, as exported` | `positive = power drawn by the feeder` |
| `residential-feeder` | `residential-meter` / `active-power` | `feeder_demand` | `residential_feeder_power` | `residential feeder meter, as exported` | `positive = power drawn by the feeder` |

Every row has the same remaining fields: `"status": "ILLUSTRATIVE"`, `"source_document": "assetops-generic-interval-csv/1, an illustrative format defined by AssetOps; not a vendor format"` (the proposed wording is confirmed), `"source_unit": "kW"`, `quantity.kind` `"AC_POWER"`, `quantity.phase_aggregation` `"AS_EXPORTED"` (the file states one value per interval and its phase handling is not known), `"reading_class": "INTERVAL_SIGNAL"`, `"span_seconds": 900`, `"cadence_seconds": 900`, `"output_resolution": "0.001"`, `"csv": {"column": ...}`. The rows are in the table's order.

Top level: `"profile_id": "generic-interval-csv-illustrative-1"`, `"profile_version": 1`, `"status": "ILLUSTRATIVE"`, `"interface": "EXPORT_CSV"`, `"source_timestamps": "UTC_Z_REQUIRED"`, `"coverage": "ALL_EXPECTED_POLLS"` and `"state_skew_max_seconds": 2`. The loader requires the last two keys; they have no effect on a CSV profile, and the claim record says so.

Not carried, with reasons: `battery_soc` is a `STATE_SIGNAL`, and 0.6 allows only `INTERVAL_SIGNAL` rows in `EXPORT_CSV` (**card correction**: the card's "plus `battery_soc` as state" is dropped). `generator_power` is bound in KOBO-001, but the `-1` JSONL has no generator signal, and a column with no source would be invented data (**card correction**). `battery_power` is excluded by D5 and §6.1.1. `feeder_demand` is per feeder in KOBO-001 (three bindings), so there is no single feeder column. A repeated `role` is allowed, because `DUPLICATE_SIGNAL` is keyed on `(device_id, signal_id)`.

**Units and scaling.** The cells are in `kW`, the binding's `source_unit` and `canonical_unit` (IDENTITY conversion). The collector does not scale: the value is the cell, exponent 0, as an exact `Fraction`. The header writes every unit as `[kW]`.

**CSV column layout.** The header is `timestamp_utc,pv_ac_power [kW],clinic_feeder_power [kW],mill_feeder_power [kW],residential_feeder_power [kW]`, in that order. That fixes the fixture's bytes; the collector still accepts any column order. The card's `interval_start_utc, interval_end_utc, <device_id>/<signal_id> [<unit>]` layout stays replaced by the TEL-06 body's single `timestamp_utc` = interval end (**card correction**, already made in Q-T65).

**TEL-06-Q2. The fixture.**
- (a) **Window.** It covers the whole `-1` window: data rows `timestamp_utc` = 2026-09-30T03:00:00Z through 15:00:00Z at 900 s, which is 49 rows and 196 cells. Each `timestamp_utc` is the observation's `source_sample_time` verbatim. The generator asserts that it is whole-second `YYYY-MM-DDTHH:MM:SSZ` and a multiple of 900 s.
- (b) **Rounding.** Each cell is `exact_decimal_text(quantize_half_even(Fraction(obs.reported_value), Fraction("0.001")))`, half-even, once, with the existing helpers only. The text is in minimal form (`4`, `40.404`; no padded zeros), which is the same text the collector's `exact_decimal_text` sends. It is consistent with the rules: D4, because the value is an exact multiple of a power of ten (10^−3) and no float is used; `output_resolution`, because the multiple check passes by construction; TEL-T1-Q7, because the rule is the same `quantize_half_even` at the row's `output_resolution` that TEL-04/05 use for the GX PV row (0.001 kW), and the oracle compares exactly. Today only one carried value is non-terminating (`14586/361`); the rule covers every value anyway.
- (c) **Outcomes.** `REPORTED` → the rounded value. `NO_PRECEDING_INTERVAL` and `NO_VALUE_AT_BOUNDARY` → a blank cell, which the collector reports as `UNAVAILABLE`/`NO_MEASUREMENT` with its span. This is the mapping the emulator uses (Q-T39, Q-T40). The row is kept, so the 03:00Z row is the fixture's own instance of the blank-cell gate (4 blank cells, interval start 02:45Z). `DROPPED` and `SUPPRESSED_BY_GAP` on a carried signal → the generator raises `ValueError`. A CSV cannot omit one cell, and blanking it would publish what the simulator did not publish. None occurs in the `-1` window for the four signals (the only `DROPPED` is SoC at 12:45Z); if one appears, stop and ask.
- (d) **Generator home.** It goes in `host/tests/field_observation_fixtures.py`, as the new function `generate_interval_csv_fixture(out_dir: Path) -> dict` (it returns the manifest). The freshness case goes in `host/tests/test_field_observation_fixtures.py`. Both are lane-owned TEL-03 files, so the TEL-06 Files list adds them. The generator reads the **checked-in** `-1` JSONL, not a new simulator run, and first asserts that its SHA-256 equals the `-1` manifest's `sha256`. It loads the profile with `load_profile` (host/tests may import `assetops_field`, 0.5). The file stays light. The freshness test regenerates the fixture into `tmp_path` and asserts byte equality for both files. It also asserts that each profile row's `span_seconds` and `cadence_seconds` equal the publication profile's declaration for that signal, as TEL-03 does.
- (e) **Manifest.** Canonical JSON plus one LF, with exactly these keys: `{"generator": "host/tests/field_observation_fixtures.py:generate_interval_csv_fixture", "format": "assetops-generic-interval-csv/1", "profile_id", "profile_version", "profile_sha256", "source_fixture": "contract-fixtures/telemetry/kobo-public-observations-v1/observations.jsonl", "source_sha256", "scenario": "kobo-daytime:2", "publication_profile": "simulator-lab-publication:3", "window": {"start": "2026-09-30T03:00:00Z", "end": "2026-09-30T15:00:00Z"}, "rounding": "quantize_half_even at each row's output_resolution", "row_count": 49, "cell_count": 196, "blank_cell_count": 4, "sha256"}`. `sha256` is the CSV's SHA-256. The `generator` key is the card's "generating command". The CSV is written UTF-8 with no BOM, `csv.writer(..., lineterminator="\n")`, LF line ends and one final LF. The existing `.gitattributes` line already covers the directory.

**TEL-06-Q3. TEL-06a (`host/tests/test_field_export_csv_proof.py`, heavy, one file run).** It reuses the TEL-04 harness by import (`import test_field_modbus_tcp_proof as tel4`, as the Postgres file does): `tel4.Bench(tmp_path)` for the gateway process, activation and FakeCentral, `Bench.database()` and `Bench.deliver_all()`. The emulator and the poller are not started. Because `Bench.expect` is built from the GX profile, 06a builds its own expect with `field_bench.expect_identity_from_snapshot(tel4.basis().snapshot_canonical, <CSV profile document>, tel4.EPOCH)`. 06a does not edit the TEL-04 file. The collector runs in process: a `GatewayPublisher(GatewayLink(bench.address, credential), snapshot_sha256, session_ref, expect)` with `session_ref = modbus_poller.new_session_ref(profile, now)`, then `check_identity()` and `CsvCollector(profile, publisher)`. The test asserts, in this order:
1. **First collect of the fixture.** There are 196 admissions, all `ADMITTED` and none `HELD`. Once `deliver_all` returns, `sealed_pending_batches == 0`. The envelopes, keyed `(device_id, signal_id, source_time)`, equal the oracle exactly: GOOD with `Fraction(value) == quantize_half_even(Fraction(obs.reported_value), Fraction("0.001"))` for each `REPORTED` cell, and the independent bound `abs(arrived − Fraction(obs.reported_value)) <= Fraction("0.0005")`. The four 03:00Z cells are `UNAVAILABLE`/`NO_MEASUREMENT` with `interval_start` 02:45:00Z. Every envelope's unit is `kW`. The oracle is built from the JSONL, not from the CSV.
2. **Second collect of the same file, with a new publisher and a new `session_ref`, after `publisher.release_previous(first_ref)` (Q5).** All 196 are `ALREADY_ADMITTED`, and each one's `message_id` and `sequence` equal the first collect's at the same index. `sealed["batch_ids"] == []`. Before and after, the gateway SQLite (read-only) shows the same `SELECT source_id, last_sequence FROM sequence_state` rows, the same `COUNT(*)` of `envelope_outbox` and the same `COUNT(*)` of `upload_batch`. That is "no new sequence". Diagnostics are not used for this check.
3. **A renamed header** (a tmp copy with `pv_ac_power` → `pv_power`) raises `CsvRefused` `HEADER_MISMATCH` whose `profile_sha256` equals the profile's. The counts of `envelope_outbox`, `report_admission` and `mapping_hold` are unchanged. A file without `Z` (`2026-09-30T03:15:00`) raises `INVALID_TIMING`, with the same unchanged counts.
4. **A `[W]` header** (a tmp copy with `pv_ac_power [W]`) gives 49 `HELD` admissions of kind `UNIT_INCOMPATIBLE` on field `unit` for the PV row. The other 147 are `ALREADY_ADMITTED`. `envelope_outbox` and `sequence_state` are unchanged. The unit check comes before the dedup (`service.py:691`), so the PV holds are not `CONFLICTING_REPORT`.

The plan card's `SOURCE_TIME_IN_FUTURE` case is **out of scope**: it is not in the spec gate list, a future instant would first meet the snapshot validity check, and it is not a property of the CSV path.

**TEL-06-Q4. TEL-06b.** It is a new third test, `test_generic_csv_lands_as_accepted_evidence`, in `host/tests/test_field_modbus_tcp_acceptance_postgres.py`. "Its own Site" means its own fresh database (`pg_harness.fresh_database()`, Q-T56), with KOBO-001 converted again through the existing `_snapshot()`. It is not a different Site: a new Site conversion is new setup, and the CSV profile is bound to KOBO-001. Central is `_central(principal, receipts)`, with the real ingestion and the real clock, as in TEL-05. The gateway, activation and expect setup are as in TEL-05, with the CSV profile document. One in-process collect of the fixture follows (as 06a step 1), then `_deliver_all`. The test asserts:
- the receipts are all `COMPLETED`, with none refused (a timing refusal is a stop: print the row);
- `accepted_evidence` for the Site has 196 rows, equal to the envelope count, with an ID set equal to the receipts' ACCEPTED IDs and `Counter(role) == {"pv_power": 49, "feeder_demand": 147}`; every ID is printed past capsys;
- the 06a step 1 exact-value oracle holds on the envelopes;
- `build_source_provenance(URL).resolve(...)` gives `state == "UNKNOWN"` with reason codes exactly `["NO_POSITIVE_BINDING"]`;
- `_consequence_rows(site_id)` shows a zero count in every table.

There is no assess step, because the card does not ask for one. If central refuses the four UNAVAILABLE envelopes, stop and report. Do not drop them from the fixture. The test runs alone, only when the coordinator sends a go, as `-k test_generic_csv_lands_as_accepted_evidence`, green on two consecutive invocations. The two existing tests in the file are not rerun.

**TEL-06-Q5. (c), confirmed.** `CsvCollector` holds no session state and has no CLI. The module map lists none, and the card's "a CLI over one file" is dropped (**card correction**). The caller owns the session: it makes the reference with `modbus_poller.new_session_ref` and calls `publisher.release_previous(previous_ref)` before `collect` when it has a previous reference. The spec's "`release_previous` on start likewise" now reads "the caller calls `release_previous` before the first `collect` of a new session". 06a step 2 exercises it. A focused test checks with `FakeLink` that `collect` sends only `admit`, `seal` and `release_run`, in that order.

**TEL-06-Q6. `INVALID_VALUE`, confirmed.** A data row whose cell count differs from the header's raises `INVALID_VALUE` at `rows[i]`, with the two counts in the detail. This includes a blank line inside the file and a blank line after the last row (`csv` gives `[]`). A single final LF is not a blank line. `HEADER_MISMATCH` stays for the header line alone. `CSV_CODES` is unchanged. Remove the "provisional" marker.

**TEL-06-Q7. Changed.** `collect()` returns `{"profile_sha256", "file_sha256", "session_ref", "report_count", "admissions", "sealed"}`. `file_sha256` is the SHA-256 of the raw file bytes, as read for validation (the card's "raw file SHA-256 is recorded"). `session_ref` is `publisher.session_ref`. `CsvRefused` is unchanged.

**TEL-06-Q8. Confirmed: normalise.** The value is a number, not text. `Fraction(cell)` → `build_report` → `exact_decimal_text`, so `0.50` reaches the gateway as `0.5`. The check that a cell is a multiple of the row's resolution runs on the `Fraction`. The fixture already writes the minimal form (Q2 (b)), so for the fixture the two forms are identical. File-level byte identity is covered by `file_sha256`.

**TEL-06-Q9. Confirmed.** The key is the spec's `report_key`, `<profile_id>:<profile_version>:<device_id>:<signal_id>:<source_time Z>` (0.6, TEL-01). The card's "format, Site, column and interval start" key is superseded: the profile ID carries the format, and the gateway scopes the key by gateway and source. An overlapping file with the same profile deduplicates per interval end when its content is equal. When the content differs, the gateway holds the report `CONFLICTING_REPORT` (`service.py:700-705`), which is correct and is not a collector concern.

**Files (TEL-06, amended).** The TEL-06 Files list plus the generator function and its freshness case (Q2 (d)). The light tier is `field/tests/test_field_export_csv.py` and `host/tests/test_field_observation_fixtures.py`, each run as its own file. The heavy tier is 06a (one queue slot) and 06b (run alone, on a go). The claim record (TEL-07 pattern) has: R2 "generic interval CSV `assetops-generic-interval-csv/1` (illustrative, defined by AssetOps) · collector + gateway · Windows laptop"; "values rounded half-even to 0.001 kW from exact rationals of simulator-lab-publication v3"; "`coverage` and `state_skew_max_seconds` are required by the profile loader and have no effect on a CSV profile"; Not claimed: "any vendor export format, any real device, any money figure, any field performance". (TEL-06, TEL-07)
