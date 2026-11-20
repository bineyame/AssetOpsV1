# 3A2 rulings

Architect (Claude), 2026-11-20. Each ruling has its reason. Index lines: `.ai/decisions/index-rulings-9.md`.
Handshake answers go below, under "Handshake answers (round 1)".

## D-3A2.1 `ExistingRecord.provenances` is ratified (3A1 choice a)

- **Ruling.** The port's `ExistingRecord` carries `provenances: Mapping[str, str]` beside `versions`, as built.
- **Why.** `INTAKE_PROVENANCE_CHANGED` (R12, D-3A1.9) cannot be decided without each stored version's provenance;
  3A1 spec §4.1 had no slot for it. It was a spec defect, correctly counted as a mid-build question (3A1 review L2).

## D-3A2.2 Store errors: one scrubbed fault, one 503 (3A1 choice b)

- **Ruling.** `StoreRefused(constraint)` is ratified and widened: every `DBAPIError` from the commercial adapter
  that is not `OperationalError` or `InterfaceError` leaves as `StoreRefused`, raised outside the handler (no
  cause, no context). Routes answer `StoreRefused` with 500 `COMMERCIAL_STORE_FAULT` and no detail, and
  `OperationalError` / `InterfaceError` with 503 `COMMERCIAL_UPLOAD_UNAVAILABLE`.
- **Why.** 2a's checks make these faults bugs, not user errors; a 500 says so. The driver's text and DETAIL print the
  failing row, which may hold personal data, so no form of it may leave (D-2A.11's class, D-3A1.10). A connection
  failure is not a bug and is retried, so it keeps the 503 every other store gives.

## D-3A2.3 An UNCHANGED outcome carries no revision number (3A1 choice c)

- **Ruling.** Ratified as built. The words say "already held" and give no revision number.
- **Why.** `revision_no` is "the revision this intake wrote"; UNCHANGED writes none. The person needs to know the row
  was already held, not which revision matched.

## D-3A2.4 Records enter the store only on acceptance, in one transaction with it

- **Ruling.** Check and submit run the store as a dry run; submit keeps the pseudonymised canonical batch on the
  upload row. Only "accept" ingests it, and the acceptance row is written inside the same `write_intake`
  transaction, under the tenant's commercial lock, after a "no decision yet" check.
- **Why.** OD-15 makes the finance lead's acceptance the gate on what counts. If records entered the store at
  submission, every reader (`3A4`, `4b`, `3B7a`) would have to filter by acceptance, and "latest revision" would be
  wrong whenever a later revision sat in an unaccepted file (D-3A1.8). Keeping the store "accepted only" keeps 3A1's
  semantics whole and R17 true (STORED is processed, acceptance is a separate recorded act). One transaction means
  there is never an accepted file without its records, or records without their acceptance.

## D-3A2.5 Pseudonymise at intake, with a per-tenant key outside the database

- **Ruling.** HMAC-SHA256 with a 32-byte key per tenant, in a file outside the database; three classes (customer,
  meter, person) so the same customer links across exports; applied only to records 2a accepts; the field table is a
  literal per kind, extendable by a reader from a closed list.
- **Why.** Integration design §6.9: "pseudonymise at intake with a per-tenant keyed hash". A key in the same
  database would let anyone with a copy of the database and a customer list re-identify people; outside it,
  deleting the key ends that (the erasure residual of D-3A1.10). Pseudonymising a refused record would hide 2a's
  refusal behind a valid-looking value, so refused records are left as sent and are never stored beyond their code.

## D-3A2.6 RC4 in code: the real-data switch and the operator database

- **Ruling.** `ASSETOPS_REAL_OPERATOR_DATA=on` admits only `observed-financial`; off admits only `source-emulated`
  and `demo-simulated`. `create_app` refuses to start unless the switch is on exactly when the database is named
  `assetops_op_<name>`. `bench-tested` and `field-integrated` never enter through this path.
- **Why.** RC4: real data only in its own database, only after a signed DPA. Code cannot see a DPA, but it can make
  the coordinator's act (creating `assetops_op_<name>` after the DPA) the only way real data is admitted, and keep
  emulated data out of that database ("simulated and observed values never share a number", integration design).
  This is also D-3A1.9's cap: a person's upload of an emulator file can never be `observed-financial`.

## D-3A2.7 Readers are a port; this unit ships the canonical one

- **Ruling.** `SourceReader` turns file bytes into a canonical batch object, a row map and extra personal paths.
  `READERS` holds `canonical-json-v1` only. The upload row records the reader's ID.
- **Why.** `3A6` adds source profiles as data ("only transport and profile change", integration design §7.2); it then
  registers readers without changing intake, refusals, pseudonymisation or acceptance. The row map lets a profile
  report the operator's own row numbers and column names.

## D-3A2.8 Two paths: one Site, or the organisation

- **Ruling.** The Site path refuses any record not of its Site (`INTAKE_SITE_NOT_THIS_SITE`, decided in the store's
  per-record loop so it is one more stored rejection). The organisation path takes any of the tenant's Sites and
  portfolio-level records.
- **Why.** The plan names a Site-bound path; a monthly budget workbook spans Sites and has portfolio lines, so it
  needs the organisation path. Deciding the Site rule in the store keeps "a refused row never sinks its file" and one
  account of refusals.

## D-3A2.9 A signed-in person, always, with these roles

- **Ruling.** Check and submit: analyst, finance lead. Accept and decline: finance lead, executive (OD-15). Read:
  those three and the Site manager for their Site. No unsigned path, whatever `ASSETOPS_REQUIRE_PERSON` says. The
  submitter may accept their own upload (queue Q1).
- **Why.** The routes are new, so there is no today's path to keep (D-3C1.1's switch protects existing screens only).
  P3A names who sees and acts.

## D-3A2.10 The raw file is never kept

- **Ruling.** Only its SHA-256, size and name are kept. The batch kept for acceptance is the pseudonymised canonical
  one.
- **Why.** A raw export holds names, phone numbers and addresses that design §6.9 says to drop before storage. The
  design's restricted raw-file store is not built (queue Q2).

## D-3A2.11 Migration numbering

- **Ruling.** `0065_commercial_upload` on `0064_person_on_work`, renumbered at merge preparation if another
  migration lands first (D-3A1.12).
- **Why.** As D-3A1.12.

## D-3A2.12 A submission must add or correct something

- **Ruling.** A submission with no NEW or REVISED record is refused (`UPLOAD_NOTHING_NEW`); the table's CHECK
  enforces it.
- **Why.** An upload that changes nothing would ask the finance lead to accept nothing; the check already told the
  person so.

## D-3A2.13 An acceptance applies exactly what was checked (handshake R5, R6)

- **Ruling.** The dry run records a `basis_sha256`: the SHA-256 of the store state it decided against (each named
  record's latest revision ID, and each Site code it resolved). Submit keeps it on the upload. Accept passes it in
  `Acceptance`; under the tenant's lock, after the "no decision yet" check, the decision recomputes the basis and, if
  it differs, raises `UploadStale` and writes nothing (409 `UPLOAD_STALE`). An envelope refusal on accept (the
  tenant's slug changed) is also `UploadStale`; it never writes a REFUSED intake.
- **Why.** "Latest" is arrival order (3A1 R10) and arrival is now acceptance, so the order in which the finance lead
  accepts waiting files would silently decide which figure a month shows. The intake decision is a pure function of
  the batch, the stored records and the Site map, so an equal basis means the accepted outcomes are exactly the
  previewed ones: the person accepts what they saw, or is told it changed. Comparing counts would miss a REVISED that
  now supersedes a later correction. The order-of-versions question itself stays 3A1 R10's (a residual).

## D-3A2.14 Only records 2a accepts are kept; a refusal keeps its code and a cut path (handshake R1, R11, P4)

- **Ruling.** The stored `batch` holds the envelope and only the records that `parse_batch(obj)` accepted,
  pseudonymised, in file order; `kept_index` maps each to its file index. Every refused record is dropped and kept only
  as `(file index, code, path)` on the upload row. For `CANONICAL_FORBIDDEN`, and for any `json.` path, the path is cut
  to its longest known parent (`record.body`, `record.subject`, ..., `batch`, `json`) before it is kept or returned
  (it can echo a key the operator wrote, dots included).
- **Why.** D-3A2.5 says a refused record is never stored beyond its code, and the upload table is append-only, so a
  raw ref kept there could never be erased (deleting the key does not help: it was never keyed). Dropping the record
  also makes the encoding question of P4 moot (2a refuses surrogates in values, so every kept string encodes).

## D-3A2.15 The file name travels in a header and is kept as given (handshake R7)

- **Ruling.** The name is sent as `X-File-Name` (percent-encoded UTF-8), never in the query string, which the access
  log records; a `file_name` query parameter is refused. It is kept as given on the upload row and returned in
  summaries, never logged. The pilot runbook says: name exports by content and month, never by a person.
- **Why.** The person must recognise the file in the list, and the name is the operator's own label. It is still
  personal data in an append-only row, so its exposure is cut to the product's own responses, and the residual is
  named (queue Q6, owner to weigh in).

## D-3A2.16 One scrub for every adapter method, proved by a class test (handshake R9; widens D-3A2.2)

- **Ruling.** Every public method of `PostgresCommercialStore`, reads included and `3A4`'s three reads included, is
  wrapped by one decorator `_scrubbed` that turns a non-connection `DBAPIError` into `StoreRefused(constraint)` raised
  outside the handler. A no-database test asserts every public method carries it.
- **Why.** A read's error text prints its parameters as a write's does. A rule applied method by method is the
  instance fix; the decorator plus the sweep test is the class fix, and catches the method the parallel unit adds.

## Handshake answers (round 1)

Answered once, 2026-11-20, and folded into `spec.md` rev 2 and `reviewer-guide.md` rev 2. "Adopted" means the
writer's expected answer is the ruling. Owner queue Q1 (submitter may accept, both recorded) and Q2 (no raw file,
only its SHA-256) are built on their defaults; "If the owner changes" below says what moves. **Estimate: 4 units**
(was 3.5): the basis check, the kept-records batch and the settings test add half a unit to commit 2 and 3.

**The Highs**
- **R1: adopted, by dropping** (D-3A2.14). The stored batch holds only accepted records; `kept_index` (new column)
  maps them to file rows; the refusal arrays on the row are the only account of a dropped record. Accept re-reads the
  refusal arrays. Service test 3 runs on `B_MIXED`, whose row 4 is a CHARGE with `subject.ref` and `account_ref`
  `C-0412` and amount `"12,5"`, and on test 5's receipt; it greps every stored string, row and exception for
  `C-0412`. Plant **V11** (keep refused records in the batch) fails it.
- **R2: adopted.** API test 8 is the settings test (cases in R3 below), and V10 names it. `create_app` runs the
  check as its first statement, so the refusal comes before any store or router is built. Plants **V10** (admit
  switch on with `assetops_test`) and **V13** (skip the check when `ASSETOPS_PSEUDONYM_KEY_DIR` is unset) each fail it.
- **P1: adopted (first form).** `SPEC_ROLES` gains §3.1's three rows and `test_3c1a_person_work.py:478` becomes
  `assert set(COMMANDS) == {k for k in SPEC_ROLES if not k.startswith("commercial.")}`. Q9 permits exactly that.
  The `COMMAND_ROLES == SPEC_ROLES` assert is untouched, so V4 still fails it.
- **P2: adopted, with `CASCADE`.** `test_3a1_commercial_postgres.py:427` becomes `"TRUNCATE " + ", ".join(TABLES) +
  " CASCADE"`: it then empties any table that references the 0063 tables, now and later (the class, not one table).
  The packet records the regression run failing without it ("cannot truncate a table referenced in a foreign key
  constraint") and passing with it. Q9 permits that one line.

**The Mediums**
- **R3: adopted, with one widening.** (a) Switch on with `DATABASE_URL` unset: refused. Switch off and unset:
  allowed. (b) The check always runs at `create_app`, whatever the key directory says. (c) The switch-on side is the
  case-sensitive fullmatch as written; the switch-off side refuses any database whose name, lower-cased, starts with
  `assetops_op` (so `ASSETOPS_OP_X` or a quoted variant is refused both ways). Detection is broad and admission is
  strict. Switch values: unset or `off` is off, `on` is on, anything else (empty, `ON`, `true`) is
  `ConfigurationError`.
- **R4: adopted.** Q6 becomes "Is declared `observed-financial` refused off an `assetops_op_` database, and anything
  else refused on one?". §1 says what the code holds: provenance is what the file declares. Two packet residuals: a
  real export mislabelled `source-emulated` is admitted on the demo database (the DPA and the coordinator's process
  cover it, not code); a writer other than this route (3A1 `ingest` from `3A3` emulators, seeds, story bootstrap)
  is not gated here. Carried to `3A3`: its emulator entry points refuse a database named `assetops_op*`. Not added
  to `create_app` now: those switches belong to their own units.
- **R5: adopted, by a basis digest** (D-3A2.13), stricter than either proposal: any change to the store state the
  check decided against refuses the accept with 409 `UPLOAD_STALE`; the upload stays WAITING and can be declined.
  Service test 19: (a) U1 holds X v1 (NEW at check), U2 holds X v2 and is accepted first; accepting U1 is
  `UPLOAD_STALE` and writes nothing; (b) X v0 stored, U1 holds X v1 (REVISED at check), U2 holds X v2 and is accepted;
  accepting U1 is `UPLOAD_STALE` although its counts are unchanged. Plants **V12** (skip the basis comparison) fails
  19a; **V14** (compare counts instead of the basis) fails 19b.
- **R6: adopted.** A changed tenant slug on accept is `UploadStale` before any write (no REFUSED intake, no decision);
  service test 20, plant **V15** (let `_refuse` write under an acceptance) fails it. All-UNCHANGED on accept cannot
  occur: an equal basis gives the previewed outcomes, and submit refused a file with nothing new. Service test 2
  asserts the accepted counts equal the preview's.
- **R7: header, kept as given** (D-3A2.15). API test 9: the name in `X-File-Name` round-trips with a non-ASCII
  character; a `file_name` query parameter is 422 `UPLOAD_BAD_REQUEST` field `file_name`; a header that does not
  decode is the same 422. Owner queue Q6 added.
- **R8: adopted.** `unavailable=(*ACCOUNTS_UNAVAILABLE, *COMMERCIAL_UNAVAILABLE, SiteStoreUnavailable,
  FoundationStoreError)`; both answer 503 `COMMERCIAL_UPLOAD_UNAVAILABLE`. API test 10 raises each from `scope`.
- **R9: adopted, as a class** (D-3A2.16). Postgres test 7: `uploads_in_scope(limit=-1)` (Postgres refuses a negative
  `LIMIT` with a `DataError`) leaves as `StoreRefused` with no cause and no context. Service test 21 asserts every
  public method of `PostgresCommercialStore` carries `_scrubbed` (it reads the decorator's marker attribute
  `__scrubbed__`); plant **V16** (remove it from `upload`) fails it. `3A4` spec rev 2 states the same rule; whichever
  unit merges second runs service test 21 after merging `main`.
- **P3: adopted.** The key command writes with `sys.stderr.write(...)`; 3A1's guard test is not edited.
- **P4: moot** (D-3A2.14). Only accepted records are encoded, and 2a refuses surrogates in every string value
  (`records_v1.py` `_string`, `_check_decimal`). `ensure_ascii=False` stays.

**The Lows**
- **R10: partly adopted.** `EXPENSE.counterparty_ref` is pseudonymised (P) when `category` is `STAFF` or
  `COLLECTION` (collection agents are often people). Queue Q3 now names `HANDLING` counterparties,
  `CONTRACT_DOCUMENT.counterparty_ref` and `source_record_id` (a reader of `3A6` declares the last when its profile
  builds IDs from account numbers). Service test 4 adds a COLLECTION expense.
- **R11: adopted** (D-3A2.14): the cut path. Service test 22: a record whose body holds a key `John_Mwangi` (and one with
  `John.Mwangi`) is `CANONICAL_FORBIDDEN` with field `body`; `John` appears in no stored string and no response.
- **R12: adopted.** `FileKeyStore` opens with `O_RDONLY | O_NOFOLLOW` and checks with `fstat` on that descriptor:
  a symlink is `PseudonymKeyUnusable`. The command refuses a missing `--dir` (exit 2, "The key directory does not
  exist."); it never creates one. No ownership check (deployment users are not fixed yet). Service tests 13 and 17
  add the two cases.
- **P5: a literal, checked against 2a.** `REF_BODY_FIELDS` in `pseudonym.py` is the union over kinds of the body
  fields 2a types `ref`; `ALLOWED_EXTRA = {"source_record_id", "subject.ref"} | {f"body.{n}" for n in
  REF_BODY_FIELDS}`. Service test 16 compares it with `{f.name for s in KIND_SPECS.values() for f in s._body if f.type
  == "ref"}` (a test may read 2a's private table; the code may not). `pseudonymise` raises `ValueError` on each call
  for a path outside the set or a class outside `C`, `M`, `P`.
- **P6, P7: as written.** `UploadMemoryStore` registers People's IDs directly; `{upload_id}` is a `str`, so a
  malformed ID is the same 404.
- **P8: import as is.** `_body_within` is imported from `reading_upload_api.py`; moving it is outside Q9.

**If the owner changes a default**
- **Q1 to "no":** the decision route refuses a decider equal to the submitter with 403 `UPLOAD_SELF_DECISION`
  (checked under the lock with the other checks); one word key, API test 2 gains the case, a one-finance-person
  operator then needs the executive to accept. Nothing else moves.
- **Q2 to "keep the raw file":** a new unit for a restricted raw-file store (its own database or bucket, its own key,
  24-month expiry job), and D-3A2.10 is superseded; this unit's schema keeps `file_sha256` as the link. 3A2's code
  does not change beyond writing the bytes to that port before step 8.
- **Q6 to "do not keep names":** the row keeps `file_sha256` and a label the person types at submit (or none); the
  header and API test 9 stay.
