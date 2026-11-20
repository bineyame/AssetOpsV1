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

## Handshake answers (round 1)

None yet.
