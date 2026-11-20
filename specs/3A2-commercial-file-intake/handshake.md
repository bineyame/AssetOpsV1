# 3A2 handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

## Reviewer questions

Fresh Reviewer (Claude), 2026-11-20, after `spec.md`, `rulings.md`, `reviewer-guide.md`, P3A rules and RC4
(`owner/owner-recut-decisions-rc1-rc9-2026-11-20.md`). Severity: High blocks coding; Medium needs an answer; Low may
be answered "as written".

- **R1 (High, done). §3.2 step 8, §3.4, D-3A2.5, D-3A2.10: a refused record's personal values are kept raw.**
  `pseudonymise` leaves a record that `parse_record` refuses "exactly as sent", and step 8 encodes the whole object,
  so `commercial_upload.batch` stores every refused record verbatim: service test 5's RECEIPT keeps `" C-0412"`, and
  B_MIXED's row 4 (`"12,5"`) keeps its raw `subject.ref`/`account_ref`. The table is append-only, so this is never
  erasable (deleting the key does not help: the values were never keyed). This contradicts D-3A2.5 ("refused records
  ... are never stored beyond their code"). Service test 3 cannot catch it (B_BILL has no refused row). Expected:
  the stored batch replaces each refused record with a placeholder that keeps its index (or drops it and the row map
  carries the index), accept re-reads the refusal arrays already on the row; and test 3's grep runs on B_MIXED plus
  test 5's record, asserting no `C-0412` anywhere, with a planted violation (V11: keep refused records) that fails it.
- **R2 (High, done). Reviewer guide V10, §4 "Settings", §8 Q6: the RC4 start-up refusal has no test.** V10 names
  "the settings test", but §6 lists none, so the plant cannot fail a named gate. Expected: a numbered test (service
  or API file) for `commercial_upload_settings`: switch on + `assetops_test` refused; switch off + `assetops_op_x`
  refused; `on`/`off`/unset/other values; and `create_app` raising `ConfigurationError` before mounting anything.
  Also state the cases R3 asks about.
- **R3 (Medium, done). §4 "Settings": the edges of the "if and only if".** (a) `DATABASE_URL` unset (no database)
  with the switch on: refused or allowed? Expected refused (nothing real can be kept, and it hides a misconfiguration).
  (b) Is the check run when `ASSETOPS_PSEUDONYM_KEY_DIR` is unset (uploads off)? Expected yes, always, at
  `create_app`. (c) Name case: `make_url(...).database` of `ASSETOPS_OP_X` or a quoted name; expected case-sensitive
  fullmatch as written.
- **R4 (Medium, done). §1, §8 Q6, D-3A2.6: what the code can and cannot promise about RC4.** Provenance is declared
  by the file. A real export labelled `source-emulated` is admitted on the demo database; an emulated record reaches
  an `assetops_op_` database by any other writer (3A1 `ingest` called by `3A3` emulators or a seed script, reading
  uploads, story bootstrap). §1's "Nothing real is accepted on a server that is not the operator's own database" and
  Q6's "Is real data refused ..." are not testable as worded. Expected: Q6 reworded to "Is declared
  `observed-financial` refused off an `assetops_op_` database, and anything else refused on one?"; the mislabel and
  other-writer cases named as residuals in the packet (or, if the Architect wants it, `create_app` on an
  `assetops_op_` database also refuses the seeding and emulator switches).
- **R5 (Medium, done). §3.3, 3A1 R10: acceptance order silently decides "latest".** "Latest" is arrival order, and
  arrival is now acceptance. Upload U1 (record X v1) waits; U2 (X v2, the correction) is accepted first; accepting U1
  then makes v1 a REVISED revision 2 that supersedes v2, so the month shows the stale figure, and the accept answer
  only reports "revised". Expected one of: accept refuses (409 `UPLOAD_STALE`) when any record's outcome differs from
  the stored preview so the person re-checks; or accept re-runs the dry run and refuses a REVISED whose
  `source_version` is already superseded by a later-accepted upload. Plus a service test of this order.
- **R6 (Medium). §3.3, §3.5 "Acceptance": accept of an upload whose intake comes back REFUSED or with nothing new.**
  The `_refuse` path "passes the decision through", so a tenant slug changed between submit and accept gives an
  `ACCEPTED` decision tied to a `REFUSED` intake, and "Accepted by {name}" with nothing stored. Likewise an accept
  whose records all came back UNCHANGED. Expected: a REFUSED intake on accept is not an acceptance (write nothing,
  answer 409 or 500 by the Architect's call); all-UNCHANGED is accepted and the words say "nothing new was added".
- **R7 (Medium). §2, §5 `UploadSummary`: `file_name` is personal data that is kept, returned and logged.** Operators
  name exports after people ("arrears_John_Mwangi_0712....csv"). It is stored unpseudonymised in an append-only
  table, returned in every summary, and sent as a query parameter (`?file_name=`), which the server access log
  records. Expected: either a ruling that the name is kept as given (and a packet residual), or the name sent in a
  header or the body and not logged; and a line in the pilot runbook.
- **R8 (Medium). §5 refusal order, Site path: `scope` failures.** `registry.ledger_scope` raises
  `SiteStoreUnavailable` / `FoundationStoreError` (reading upload passes them as its `unavailable`), but §4 mounts
  with `unavailable=(*ACCOUNTS_UNAVAILABLE, *COMMERCIAL_UNAVAILABLE)` only, so a Site-store outage is a bare 500.
  Expected: add both to the tuple and answer 503 `COMMERCIAL_UPLOAD_UNAVAILABLE`, with an API test.
- **R9 (Medium). §3.5 "Errors", D-3A2.2: which adapter methods the `DBAPIError` scrub covers.** Writes only, or every
  method including the reads (`latest_revisions`, `intake`, `upload`, `uploads_in_scope`)? A read's error text can
  print a parameter too. `3A4` adds three reads to the same adapter in parallel and its spec does not mention the
  scrub. Expected: every public adapter method, stated in both specs, with one Postgres test on a read.
- **R10 (Low). §3.4 class sweep against 2a §6.4.** Checked every `_ref` body field of the 14 kinds. Not in the
  table and possibly a person: `EXPENSE.counterparty_ref` for `COLLECTION` (commission agents) and `HANDLING`;
  `CONTRACT_DOCUMENT.counterparty_ref` (an individual landlord); `source_record_id`, which billing exports often build
  from the account number and which `canonical-json-v1` cannot declare. Expected: queue Q3 extended to name them, or
  `COLLECTION` added to the STAFF rule.
- **R11 (Low). §5 `Refusal.field`: a refusal can echo a key the operator wrote.** 2a's `CANONICAL_FORBIDDEN` path
  carries the unknown key's text (up to 64 characters, ASCII-escaped), which is stored in `refusal_path` and
  `commercial_rejection.path` and returned as `field`. A spreadsheet export with a name in a header cell would put it
  there. Expected: accept as a residual, or label any `CANONICAL_FORBIDDEN` field as "an unknown field".
- **R12 (Low). §3.4 key store.** `FileKeyStore` checks length and `st_mode & 0o077`; should it also refuse a symlink
  (`O_NOFOLLOW` / `lstat`) and a key file not owned by the server's user? Does `create` refuse a missing `--dir`
  or create it with `0o700`? Expected: refuse a symlink; `--dir` must exist; nothing else.

## Implementer pre-flight

Pre-flight against `main` at `e39e617df` (3A1 merged; 3B3 on `task/3B3-structure-read` at `7f0ca4804`). Numbered
P… for this round (the preamble's I…). Checked and found as cited, no question: `CommercialRecords.ingest`,
`_Decision.__call__` (the `INTAKE_SITE_UNKNOWN` check sits where §3.5 puts the Site-scope check), `write_intake`'s
lock (`hashtextextended('commercial:' || tenant)`), `StoreRefused`, `ExistingRecord.provenances`; 2a's 17 codes and
3A1's 7 `INTAKE_*` codes (8 with the new one, as §6 test 15); `person_step`, `roles_of`, `PersonRefused`,
`has_role(role, None)` (false for SITE_MANAGER, as §3.1 says); `accounts/model.py` `ROLES` holds `ANALYST` and
`OPERATOR_EXECUTIVE`; `_body_within`; `create_app`'s last keyword is `accounts`; migration head `0064_person_on_work`
on `0063_commercial_records`, and no local branch holds a `0065`; `tenant`, `site`, `operator_account` and
`commercial_intake` all have `UNIQUE (tenant_id, id)` for the composite keys; `ledger_append_only()` exists; the
pg harness empties by FK closure from the tenant, so the two new tables need no harness change; the pseudonym
goldens of tests 3 and 4 recompute by hand with `hmac` (`C-448c...2029`, `M-c04f...3111`, `P-8612...cf42`).

- **P1 (High, done). §3.1, §6 "Regression", §8 Q9: adding the three rows to `SPEC_ROLES` fails 3C1a's own test.**
  `test_3c1a_person_work.py:476-478` asserts `COMMAND_ROLES == SPEC_ROLES` **and** `set(COMMANDS) == set(SPEC_ROLES)`,
  and `ALL = sorted(COMMANDS)` drives four parametrised work-route tests. The commercial keys have no `COMMANDS`
  entry (they are not work routes), so the second assert fails; §8 Q9 allows only "the `SPEC_ROLES` rows". Expected:
  permit editing line 478 to `set(COMMANDS) == {k for k in SPEC_ROLES if not k.startswith("commercial.")}` (or
  keep a separate `COMMERCIAL_SPEC_ROLES` in the 3A2 API test and assert `COMMAND_ROLES == {**SPEC_ROLES,
  **COMMERCIAL_SPEC_ROLES}` there), and widen Q9 to say so.
- **P2 (High, done). §2, §6 "Regression": 0065's foreign key to `commercial_intake` breaks 3A1's downgrade test.**
  `test_3a1_commercial_postgres.py:427` runs `TRUNCATE commercial_intake, commercial_record, ...` (0063's `TABLES`)
  without `CASCADE`. Once `commercial_upload_decision` references `commercial_intake`, Postgres refuses that
  TRUNCATE even with the new table empty ("cannot truncate a table referenced in a foreign key constraint"). The
  file is in the regression set and outside Q9. Expected: permit the one-line change to include every table that
  references the 0063 tables (or `CASCADE`), or a fixture that downgrades 0065 first; widen Q9.
- **P3 (Medium, done). §3.4 key command vs 3A1's guard test.** `test_no_log_call_in_the_commercial_package`
  (`test_3a1_commercial_service.py:445`) fails on any `print(` in `commercial/**`, and the key command must say "A
  key already exists ...". Expected: write with `sys.stderr.write(...)` (no test change), confirmed by the Architect.
- **P4 (Medium, done). §3.2 step 8: `ensure_ascii=False` can raise on a refused record.** `loads_canonical` refuses
  surrogates only in keys; a value such as `"\ud800"` in a record that 2a then refuses survives to step 8, and
  `.encode("utf-8")` raises `UnicodeEncodeError`, an unanswered 500. Moot if R1 drops refused records; otherwise
  expected `ensure_ascii=True` (still valid canonical JSON) and a test.
- **P5 (Medium). §3.4 `ALLOWED_EXTRA`: "a body field that 2a types as a ref" has no public source.** Field types live
  in `KindSpec._body` (`records_v1.py:125-128`, documented "the rest is private"). Expected: a literal set in
  `pseudonym.py` with a test that compares it to 2a's table, or a public accessor added to 2a (out of Q9's scope).
  Also: is the set per kind or the union over kinds, and is the `ValueError` raised when the reader is registered or
  on each call?
- **P6 (Low). §6 test helpers.** 3A1's `MemoryCommercialStore.add_tenant`/`add_site` mint their own UUIDs, so
  `UploadMemoryStore` registers People's tenant and Site IDs directly into `slugs`/`sites`, and supplies display names
  from `People` for `UploadRecord`. Not a question unless the Architect objects.
- **P7 (Low). §5: the `{upload_id}` path parameter.** Declared as `str` and parsed in the route, so a malformed ID is
  the same 404 body (a `UUID` annotation would give FastAPI's 422). Not a question unless the Architect objects.
- **P8 (Low). §0 "Collisions".** `3B3` also touches `chain/outcomes.py` and `financials/composition.py`, not only
  `structure/`; neither overlaps 3A2. `_body_within` is private to `reading_upload_api.py`: import it as is, or move
  it (outside Q9)? Expected: import as is.
