# 3A2 review, round 1 (discovery, W5)

Reviewer: fresh Claude reviewer, 2026-11-20. Branch `task/3A2-commercial-file-intake`, head `186b31510` (code at
`31f09bb42`; `186b31510` is the docs-only packet commit). Worktree `/opt/assetecon/AssetOpsV1-3a2`, read only.
Judged against spec rev 2, rulings D-3A2.1-16 with the handshake answers, the reviewer guide rev 2 and RC4.

## Summary

- **Verdict: accept with findings fixed on the branch.** Two Medium test gaps (F1, F2), one Low (F3). No code defect
  found in privacy, RC4, rights, transactions or the migration; all three findings are cheap to fix.
- F1 (Medium): five of the nine §3.4 rows have no test; a plant that stops pseudonymising a METER-subject CHARGE passes.
- F2 (Medium): no test refuses another Site's (or the organisation's) upload on a Site path; a plant that drops the
  Site check in `_load` passes.
- F3 (Low): a NUL in `X-File-Name` or in a decline reason answers 500 `COMMERCIAL_STORE_FAULT`, not 422.
- Reruns: 3A2 service and API tests plus the 3A1 service tests, 80 passed. 3A2 Postgres file through `--db`, 39 passed,
  0 skipped. `check-architecture` passed. `check-agent-workflow` passed. Three plants of my own: one failed its test,
  two did not (F1, F2). Goldens recomputed by hand with `hmac`: all three match.
- Mid-build Q1: ratify the adapter placement. It follows the evidence-domain precedent and the guard registers the one
  writer. Q2: both defaults read correctly to me. Neither blocks.

## Findings

### F1 Medium (acceptance evidence gap, privacy): the §3.4 table is not pinned row by row

- **Where:** `backend/tests/test_3a2_commercial_upload_service.py:304-343` (tests 3 and 4) against
  `backend/assetops_backend/commercial/pseudonym.py:28-46`.
- **What:** the tests cover a CUSTOMER-subject CHARGE, a RECEIPT, a CUSTOMER_METER_READ and the EXPENSE categories.
  Nothing covers a METER-subject CHARGE or ADJUSTMENT, `ADJUSTMENT.body.authorised_by_ref`,
  `STORAGE_MOVEMENT.body.customer_ref`, `METER_ASSIGNMENT` (three paths) or `FLEET_ROSTER.body.tag_ref`. Plant R1 removed
  the `("subject.ref", "M", METER)` line from CHARGE, and the service and API files still passed 56/56.
- **Why it matters:** spec §8 Q2 asks whether every identifier in the table is pseudonymised. The packet answers yes
  from svc 3 and 4, but those tests cannot fail for five of the rows. The code is correct today (I compared it with
  the spec table line by line). A later edit, or 3A6 touching this table, would go unnoticed. This is the class sweep
  the reviewer guide asks for (W6).
- **Fix:** add a table-driven test, one case per (kind, path, condition) row. Each case should cover the positive
  condition and, where there is one, the negative (for example a SITE-subject CHARGE stays raw). Each expected value
  should be a hand-computed literal, or at least `pseudonym(KEY, cls, raw)` checked against the raw value at that
  path. The test should also assert that a field outside the table stays raw.

### F2 Medium (acceptance evidence gap, rights): "another Site's upload is 404" is untested

- **Where:** `backend/assetops_backend/commercial/uploads.py` `_load`
  (`if record is None or record.upload.site_id != scope.site_id`). The API tests at
  `backend/tests/test_3a2_commercial_upload_api.py:133-139` only use a random UUID and `not-a-uuid`.
- **What:** plant R3 replaced the condition with `if record is None`. Both files still passed 56/56. With that plant,
  Peter (Kobo Site manager) could read, through `/api/sites/KOBO-001/commercial-uploads/<id>`, a KISIWA upload or an
  organisation upload, with its file name, submitter and refusal rows. A finance lead could also decide an
  organisation upload from a Site path. The tenant half (`WHERE u.tenant_id = :t`) has no test with a real ID of
  another tenant either.
- **Why it matters:** spec §3.3 and §8 Q5 ("another tenant answered not found"), and the guide's rights focus. The
  code is correct today, but nothing would catch a regression.
- **Fix:** in the service or API tests, submit an upload on KISIWA and one on the organisation path. Then read and
  decide each through the Kobo path, expecting 404 `UPLOAD_NOT_FOUND` with byte-equal bodies. Read and decide the Kobo
  upload through the organisation path (404). Read an acme upload's real ID as Hugo on the organisation path (404).
  One Postgres case in test 5 should assert that `upload(other_tenant, id)` is `None`.

### F3 Low (robustness, not privacy): NUL and control characters in the two free-text inputs

- **Where:** `backend/assetops_backend/commercial_upload_api.py` `_file_name`, and `uploads.py` `decide`
  (the reason check).
- **What:** `X-File-Name: a%00.json` passes `_file_name`. A reason of `"x\u0000y"` passes the length check. Postgres
  `text` refuses NUL: psycopg raises `psycopg.DataError` when it dumps such a string (I confirmed this at the driver;
  the end-to-end request was not run), `_scrubbed` turns it into `StoreRefused`, and the person gets 500
  `COMMERCIAL_STORE_FAULT` ("The export could not be kept"). By D-3A2.2, a 500 means a bug. Other control characters
  (`%0A`, `%1B`) are stored and returned in the file name.
- **Why it matters:** this is a user input answered as a server fault, and the file list would show a name with
  control characters. Nothing leaks: the scrub holds.
- **Fix:** refuse any character below U+0020 or equal to U+007F with 422 `UPLOAD_BAD_REQUEST` field `file_name`.
  Refuse NUL in the reason with 422 `UPLOAD_DECISION_INVALID` field `reason`. Add one case to API test 9 and to
  service test 11. This is a one-line change each and needs no spec change.

## Probes (what I verified, beyond the packet's claims)

- **Privacy.**
  - No `logging`, `print` or logger in `commercial/**` or `commercial_upload_api.py`.
  - The file name is read only from the header; a `file_name` query parameter is refused.
  - The pseudonym key is used only by `hmac` and is never in a row, an exception or a response.
  - Refusal params carry only codes, cut paths, a provenance bounded by 2a's enum, and `limit_mb`.
  - In 2a (`records_v1.py:510-518`, `:533`, `:654`), only `_check_keys` (`CANONICAL_FORBIDDEN`) and the `json.` duplicate
    path can echo operator text, and `cut_path` covers both.
  - A lone surrogate in an envelope string is refused by 2a (`CANONICAL_REF batch.source_system`), so `data2` always
    encodes.
- **RC4.**
  - `commercial_upload_settings` is `create_app`'s first statement (`main.py:345`), and `app = create_app()` runs at
    import.
  - On: needs `assetops_op_[a-z0-9_]{1,40}`, case-sensitive. Off: refuses any lower-cased `assetops_op` prefix. Bad
    switch values raise.
  - `ADMITTED` is `{False: emulated or demo, True: observed-financial}`.
  - The only builder of `CommercialUploads` is `main.py:683`.
  - Plant R2 (case-sensitive off side) fails `test_8_settings_refused[off-ASSETOPS_OP_X-/keys]`.
- **Rights.**
  - `COMMAND_ROLES` matches §3.1.
  - The Site path calls `person_step(required=True, enabled=True)`. The organisation path returns 401 when there is no
    person or no account store, whatever `ASSETOPS_REQUIRE_PERSON` says.
  - Self-accept is allowed and both people are recorded (svc 2, parametrised).
- **Transactions.**
  - Check is a dry run: lock, decide, rollback.
  - On accept, `write_intake` takes the lock, checks the decision (`_DECIDED`), then calls `decide`, which checks the
    basis and builds the plan. It then writes the plan's rows and the decision row, and commits. `UploadStale` and
    `UploadAlreadyDecided` leave through the `finally` rollback.
  - The basis covers every named record's latest revision ID and the resolved Site map. Because the tables are
    append-only, any new version or provenance moves the latest revision ID.
- **Migration 0065.**
  - The SQL equals spec §2 exactly (diffed with comments stripped).
  - `down_revision = "0064_person_on_work"`, and `main`'s head is still 0064.
  - The downgrade locks both tables, refuses with rows present, and drops in reverse order without dropping
    `ledger_append_only()`.
  - The 3A1 test's `CASCADE` truncates `commercial_upload_decision` through its FK to `commercial_intake`; the packet's
    P2 log shows the failure without it.
- **Honesty.**
  - No unknown value is rendered as 0.
  - Counts come from the check and are re-derived for the result; the months list is empty when there is no
    recognition period.
  - The organisation scope's `site_code` is `null`.
- **Scope.**
  - The diff matches §8 Q9 plus the Q1 adapter file and the guard's domain-entry line (declared), and the usual state
    and index docs.

## Checks run (this review)

| Check | Result |
|---|---|
| Module paths, `PYTHONPATH` = worktree `backend`, `backend/tests`, `contracts`, `simulator` | `assetops_backend`, `assetops_contracts`, `commercial/uploads.py` all from `/opt/assetecon/AssetOpsV1-3a2/...` |
| `heavy-slot.sh -- pytest test_3a2_commercial_upload_service.py test_3a2_commercial_upload_api.py test_3a1_commercial_service.py` | 80 passed, 10.7 s |
| `heavy-slot.sh --db -- pytest tests/test_3a2_commercial_upload_postgres.py -rs` (base `assetops_test`, harness-routed run DBs) | 39 passed, 0 skipped |
| `check-architecture.ps1` (`ASSETOPS_GUARD_PYTHON` set; without it the chain guard cannot run in a worktree with no `.venv`) | Architecture check passed |
| `check-agent-workflow.ps1` | passed |
| Goldens `C-0412`, `MT-2201`, `P-JOSEPH` recomputed with `hmac` | all three equal the test literals |

**Plants:** each was applied alone, run and reverted in the scratch copy
`/tmp/claude-1001/-opt-assetecon-AssetOpsV1/36691a1d-3a44-455a-947e-9acaa1af47c0/scratchpad/rev3a2-plants-1795182787`,
which was made with `git archive 186b31510`. The clean run and the reverted run were each 56 passed.

| Plant | Result |
|---|---|
| R1: CHARGE METER subject not pseudonymised | 56 passed (**survives**: F1) |
| R2: RC4 off-side check case-sensitive | fails API test 8 `[off-ASSETOPS_OP_X]` |
| R3: `_load` ignores the upload's Site | 56 passed (**survives**: F2) |

**Builder's runs cited, not rerun:**
- 244 no-database tests at `31f09bb42`.
- Postgres 39, plus a regression set of 46, at `a8298dedf`. Python is unchanged after that commit; `31f09bb42` touches
  only the guard and docs.
- Fast check-all: 41 guards at `31f09bb42`.
- Plants V1-V18 and P2: their logs are in `/opt/assetecon/evidence/3A2/build-1/`. I read the summaries and did not
  replay them.

## Not verified

- The full backend suite (not run, by policy).
- The F3 NUL path end to end against Postgres; it is reasoned from the driver behaviour I confirmed.
- A real `create_app` with a key directory against a database.
- The routes through `LocaleMiddleware` in another locale.
- The regression set (3A1 Postgres, 3C0a, pg harness) and check-all: I cite the builder's runs.

## Residual risk the packet does not name

- **Mixed writers break linkage.** Records written through 3A1 `ingest` directly (3A3 emulators, seeds, story
  bootstrap) keep raw refs, while 3A2 stores pseudonyms. The same customer will not link across the two, and the same
  `source_record_id`/version sent both ways ends in `INTAKE_VERSION_CONFLICT`. 3A3 should either go through this
  service or pseudonymise with the same key.
- **A recreated key changes every pseudonym.** If a tenant's key is deleted for erasure and later recreated, a file
  that was already held comes back as `INTAKE_VERSION_CONFLICT` instead of UNCHANGED. The pilot runbook should say
  that erasure ends intake under the old identities.
- **No single list of waiting files.** The organisation path lists only organisation uploads, so the finance lead has
  no one list of everything waiting across Sites. This is for the screen unit (3A5 or later), not for this slice.
# 3A2 review, round 2 (verification, W5), head ee61d3ee3

Reviewer: fresh Claude, 2026-11-20. Worktree /opt/assetecon/AssetOpsV1-3a2, read only.

## Summary
- **Verdict: ACCEPT.** No findings.
- F1 fixed as a class: `test_3b_every_pseudonymisation_row` has 15 table-driven cases (every §3.4 row and condition, positive and
  negative; hand-written HMAC formula, a non-table field stays raw). My plant removing the CHARGE/METER row fails `[CHARGE meter]`.
- F2 fixed as a class: service `test_11b` (3 scopes x 3 IDs x get/decide, byte-equal to unknown; other tenant), API `test_1c`, and
  Postgres `test_5` (real second tenant). My plant dropping the `site_id` check fails 11b and 1c.
- F3: `has_control_character` used for file name (API) and decline reason (service); both tests extended (NUL, LF, ESC, DEL).
- D-3A2.17: adapter file and guard entry present; `check-architecture` passes (needs ASSETOPS_GUARD_PYTHON in a worktree without .venv).
- D-3A2.18: `Counts` carries words and text; person/role refusals use 3C1a keys; `commercial_upload.site_forbidden` added; old keys deleted.
- D-3A2.16: `_scrubbed` on `intake_revisions`, `site_zones` and `latest_revisions`; test_21 sweeps every public method. L1: 3A4 test +14 lines.
- Runs: 3A2 service+API+3A4 months, 101 passed. 3A2 Postgres via `heavy-slot.sh --db` on assetops_test routed DBs, 39 passed, 0 skipped
  (builder's 49 includes the 3A4 Postgres file, not rerun). `alembic heads`: one head, 0065_commercial_upload. check-agent-workflow passed.
- Not verified: 133 regression and check-all 41/41 (cited, not rerun); the os.open rule-8 plant (guard passes; not planted).
- Note: in my scratch copy `test_8_create_app_refuses_first` also failed; it is path-sensitive to the copy, not a plant effect. It passes in the worktree.
