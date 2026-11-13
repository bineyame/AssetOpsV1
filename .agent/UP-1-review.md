# UP-1 review (fresh Claude Reviewer, 2026-11-13)

Branch `task/UP-1-reading-upload`, head `b5ccd7e40`, diff `git diff 482e25a06 HEAD` (merge base with main; main since
then adds only `.agent/` planning files). Judged against rev 7 section 7.5 (D-17N.5), D-UP.1-11, `.agent/UP-1-packet.md`
and `frontend/mockups/v72/upload-readings.html`. I re-read `service.py` in full (D-UP.11).

## Verdict: REJECT. Two Medium findings must be fixed on the branch. Both are small.

The server design is sound and holds the safety properties asked for. Site scope comes only from the switch, on the
server and on the page. A dry run writes nothing. The column-to-role mapping is never guessed. 0061 is the only head.
The Analysed read follows D-UP.3, and the Postgres flow reaches ANALYSED. The two Medium findings are that system
codes reach the client, and that the blocking upload runs on the event loop. A third, smaller robustness gap is
listed with them.

## Findings

### M1 (Medium; acceptance gap: owner's plain-words rule and the mockup): system codes are shown on the refusal
- `backend/assetops_backend/reading_upload/service.py:211` passes the raw collector path as `{field}`.
  - `i18n/messages.py:57` (header_mismatch) and `:67` (invalid_value) print it, so the client reads, verbatim,
    "... Row 5 (rows[4].mill_feeder_power)." and "... do not match the template (header[2]).".
  - `:70` (already_recorded) prints `{latest}` as `2026-11-16T20:45:00Z (UTC)`. The mock has "16 Nov, 23:45" in
    Site time.
- `frontend/src/sites/ReadingUpload.tsx:396` shows `refusal.field` raw in the "where" chip:
  - `rows[6].timestamp_utc` for row refusals;
  - `header[2]` for header refusals;
  - the role code `pv_power` for ALREADY_RECORDED.
- The mock draws `row 7 · timestamp_utc`. The file's own MOCK DEVIATION note (line 10) says the page shows
  "row · column", which the page does not do.
- The tests cannot catch this:
  - `readingUpload.test.tsx:171` feeds `field: "row 7 timestamp_utc"`, a shape the server never sends.
  - The backend plain-words test (`test_up1_reading_upload.py:111`) only checks that the code word is absent.
- **Fix:**
  - The server sends display parts: the row number (1-based) and the CSV column name. Headers get the column
    position or the heading the file has.
  - The page renders `row N · <column>`. For ALREADY_RECORDED there is no chip, or the chip says the role in words.
  - Messages drop the raw `{field}`. `latest` is passed in Site time ("16 Nov, 23:45"), or the page formats it.
  - Add one test with the real server field shape, end to end through `_rendered`.

### M2 (Medium; correctness and availability): the upload blocks the API's event loop
- `reading_upload_api.py:130` and `:169` call `service.upload` and `service.status` synchronously inside
  `async def` handlers.
- `upload` runs one or two `subprocess.run` field processes, each up to 120 s. On confirm it also runs
  `deliver_now`, bounded at 30 s, plus the Postgres queries.
- While that runs, the single event loop serves nothing else. That includes the page's own 3 s status poll and every
  other page open in the demo.
- The flow test shows a few seconds per send in the normal case. The worst case is minutes.
- The codebase's precedent for blocking work in async handlers is `await run_in_threadpool(...)` (`evidence_api.py:308`,
  `gateway_api.py:79`).
- **Fix:** `await run_in_threadpool(service.upload, ...)` and `await run_in_threadpool(service.status, ...)`. Also
  the scope lookup, if it is easy to include.

### L1 (Low; robustness, asked for in the brief: huge rows): a field over 128 KB returns 500, and the page shows nothing
- I reproduced it by running `python -m assetops_field.csv_upload check` with one 200,000-character cell.
  - The `csv.reader` call in `export_csv.py:143` raises `_csv.Error: field larger than field limit (131072)`.
    Nothing catches it, so the child prints no JSON.
  - `host/reading_upload_process.py:99` then raises `RuntimeError`. The router does not catch it, so the answer
    is a 500.
- On the page, `ReadingUpload.tsx:255` maps a 5xx with no message to `note: null`. The page silently returns to
  "choose a file", with no sentence.
- Nothing is admitted or stored, so this is safe. It is not honest, though.
- **Fix:**
  - In `csv_upload.main`, map `csv.Error` (and `UnicodeError`, if any escapes `_text`) to an `INVALID_VALUE` or
    `ENCODING` refusal.
  - The router turns `RuntimeError` from a port into a 503 with words.
  - The page shows a fallback sentence when `message` is null.
- Formula injection: no risk. Every cell must match the timestamp or decimal patterns, nothing is echoed into a CSV,
  and the template is static. Encoding: BOM and non-UTF-8 are refused (D-UP.6 words are present).
- Size: 2 MB is enforced by `Content-Length` and by a bounded stream read (`_body_within`).
- `file_name` is display-only. Slashes are refused, and React escapes it.
- CSRF: `text/csv` is not a CORS-safelisted type, so a cross-site POST needs a preflight.

### L2 (Low; Architect question, not a builder defect): a stale FAILED job pins "Not analysed"
- `postgres_reading_upload_store.py:69` treats any FAILED `recompute_job` overlapping the span as failed. That
  includes jobs that failed before the upload.
- Failure also wins over a later successful run (`:115-118`, failed > ran).
- If the demo day has an old FAILED job, the page shows "Not analysed" even though the upload was assessed.
- This is the literal reading of D-UP.3.
- **Suggestion to the Architect:** count only FAILED jobs created or updated at or after the upload's earliest
  `decided_at`, or let a covering run after the decision win.
- Also check `SELECT status, count(*) FROM recompute_job` for KOBO-001 on the client4 copy (resume point 3).

### L3 (Low): spec items not built and not listed in the packet
- The demo file generator's `--day` option is not in the diff. Section 7.5 demo beat:
  `field_observation_fixtures.py interval-csv --day`.
- The flow test does not show "byte-equal to the same file admitted through the TEL-06b path" (section 7.5 Tests).
- State both in the packet, or build them before merge.

## Judgments asked for

- **`decided_at` as accepted_at: correct.**
  - The ledger stamps `decided_at` with the database `clock_timestamp()` after the batch lock (S4-07,
    `postgres_evidence_ledger.py:14-21`).
  - That is the same database clock the worker lease's `knowledge_cutoff` is taken on. That design exists
    precisely so a lease whose cutoff predates a decision cannot claim it.
  - `knowledge_cutoff >= max(decided_at of the ACCEPTED dispositions)` is therefore the right proof that the run saw
    the upload.
  - Edge: messages rejected or in conflict at the central server never count as accepted, so the page stays at
    "Accepted n of m". This is not covered by D-UP.3. Residual risk; it does not occur with the fixture.
- **Analysed rule:**
  - It matches D-UP.3: dispatch, DEFAULT, `job_id IS NOT NULL`, the window covers `period_start`, no
    PENDING/LEASED job in any domain over the span, FAILED gives Not analysed.
  - Order: pending > failed > ran (see L2).
- **Dry run writes nothing:**
  - The service returns before `sender` and `insert`.
  - The field `check` builds the collector on `_NoGateway`, which raises on any IPC.
  - Proven no-DB, and on Postgres by the flow test (`count(*) = 0`).
- **Switch honoured on both sides:**
  - Off by default (no service means 403 `READING_UPLOAD_OFF`).
  - Startup refuses any code but KOBO-001.
  - The Site list is checked per request.
  - The page and the Health panel render only on a 200 entry read.
  - Upload access is the Site read access. That matches section 7.5 ("without sign-in", behind the switch).
- **Column-to-role mapping is never guessed:** the header must equal the profile columns exactly
  (HEADER_MISMATCH otherwise). Roles come from the profile rows.
- **Migration:** `ScriptDirectory.get_heads()` returns `['0061_reading_upload']`; 0061 → 0060 → 0059.
- **Mock flow:** Parts A-E are present, and the MOCK DEVIATIONs are labelled. The one exception is the
  "row · column" label, which is inaccurate (M1). Layout captures in each state are listed as a pending gate, not
  claimed as passed.
- **Stray files:** none. The guard and `test_estate_guard`/PR-3 test edits are justified (D-UP.8/10).

## The builder's question: move the Health panel copy and the step descriptions to server keys?

- **Move the Site-specific sentences.** These are:
  - the Health panel text ("solar output and the three feeder meters, every 15 minutes", `ReadingUpload.tsx:89`);
  - "{siteName}'s four meters" (`:288`).

  Both describe the CSV profile, not the page. They become wrong as soon as the profile or Site changes. Return them
  in the entry read beside `template_note`, as keys `reading_upload.entry_note` and `reading_upload.template_meters`.
- **Keep the generic tracker step descriptions in the page.** These are "The whole file passed." and "Handed to the
  site's data gateway.". They are page chrome, like the headings and buttons elsewhere in the app. The states'
  sentences are already the server's.
- Not a merge blocker. Do it in the same fix round if it is cheap.

## Checks I ran (VPS, head b5ccd7e40, PYTHONPATH = the worktree)

- No-DB pytest (4.7 s wall): **124 passed**. Files:
  - `backend/tests/test_up1_reading_upload.py`
  - `test_uq6a_message_seam.py`
  - `host/tests/test_up1_reading_upload_process.py`
  - `host/tests/test_up1_demo_upload_gateway.py`
  - `field/tests/test_field_csv_upload.py`
- Postgres on `assetops_up1_test` (the harness clones `assetops_up1_pt<run>_*_test`):
  - Files: `backend/tests/test_up1_reading_upload_postgres.py` and
    `host/tests/test_up1_reading_upload_flow_postgres.py`.
  - Result: **3 passed** in 11.2 s.
  - The flow printed ANALYSED, 196/196, board_day 2026-09-30, send-to-Analysed 2.8 s.
- vitest `src/sites/__tests__/readingUpload.test.tsx`: **10 passed**.
- Adjacent Health/route vitest set: **192 passed** (8 files: siteHealthBoundary, operatorSiteTabs, siteRangeTags,
  siteDetailRoute, coldHealthDepth, evHealthDepth, runsInventory, s2LedgerEvidence).
- `npx tsc --noEmit`: exit 0.
- `alembic` script heads: one (`0061_reading_upload`).
- Manual probes of the field `check` CLI:
  - a 200 KB field crashes the child (L1);
  - a formula-like cell gives an INVALID_TIMING refusal;
  - a NUL-filled file gives HEADER_MISMATCH.

## Not verified

- check-all and the configuration-persistence guard: left to the coordinator, per the lane rules.
- The full suites: not run, per policy.
- The client4/demo-build run (resume point 3): the `service:demo-upload` actor and the `kobo-edge-*` cohort risk.
- Page captures in each state.
- The production build.
