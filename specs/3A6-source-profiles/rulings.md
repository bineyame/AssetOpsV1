# 3A6 rulings

Architect (Claude), 2026-11-20. Each ruling: what, why, and (where a residual is closed) the class and the sweep (W6).
Applied by default; the open questions with defaults are in `spec.md` §10.

## D-3A6.1 A source profile is a JSON data file compiled to the one engine's `Layout` (amends D-3A3.2)

- **Ruling.** A profile (spec §2.1) compiles to a `Layout` through `native/profiles_v1.py`. The engine in
  `layouts_v1.py` gains optional file rules (CSV encoding and delimiter, header row, XLSX sheet), value rules (decimal
  and thousands marks, negatives, date, time and month forms, time zone), per-path types and scales, a joined record ID
  and a row digest version. Every new field defaults to today's behaviour, so the four illustrative layouts read and
  render byte for byte as before (done 1). `read_layout` splits into `split_file` and `read_rows`, both public.
- **Why.** §7.2: "only transport and profile change; the parser ... do[es] not". D-3A3.2 put the native shape in one
  engine so a new export is a new value, not a new parser; the transforms are what a real export needs (a decimal
  comma, a day-first date, a local time with no offset, a header under a title block, a workbook). Two engines would
  drift; one engine with defaults keeps 3A3's contract and its pins.

## D-3A6.2 Profiles live in the tenant's database, admitted by a command; the sample is never kept (RC4)

- **Ruling.** New append-only table `commercial_source_profile` (migration 0067) holds each admitted version: the
  profile text, its SHA-256, the SHA-256 of the sample and of the expected file, the row count, who admitted it and in
  which role. `python -m assetops_backend.source_profile {check,admit,list}`. Uploads name `profile.<id>.v<n>`; only the
  latest version of a profile reads (`UPLOAD_READER_SUPERSEDED` names it).
- **Why.** An operator's sample holds customer and staff references, so it may live only in that operator's database
  (RC4) and only as long as needed; its hash pins the profile to it without keeping it. Profiles in the repository would
  need a code review and a merge per operator, which is the "code change" the owner asked to remove (RC2), and would
  put a real operator's export shape beside other tenants'. §6.5's "each source system is registered per tenant with
  its profile" is this table. Only the latest version reads, so an analyst who fixed a profile cannot upload through
  the broken one by habit.

## D-3A6.3 Admission is the contract test as product code, pinned by hand-written records

- **Ruling.** `SourceProfiles.admit` runs, in order: the profile's validity, its status against the database's
  real-data switch, lineage, the sample read with no refusal, the reader's records equal to the analyst's hand-written
  expected records, and six probes (P1 header, P2 short row, P3 invisible characters, P4 every map, P5 every typed
  path, P6 every blanked column invents nothing). The pytest suite (C1 to C10) also runs over the committed
  illustrative profile through the intake.
- **Why.** 3A3 made `READERS` admission mechanical with a pytest case per reader (D-3A3.5), but a pytest case is code,
  and a real operator's sample cannot enter the repository. The probes are the store-free part of C3, C8 and the
  coded check, run on the operator's own sample; the store-dependent part (idempotency, pseudonymisation, acceptance)
  is 3A2's intake, unchanged, which every profile upload goes through. Independence (W2): the expected records are
  written by the analyst from the sample, not produced by the engine, so a profile cannot pass its own mistake.
  Status follows the database (as provenance does, D-3A3.10): `PINNED` on an operator database, `ILLUSTRATIVE`
  elsewhere, so a rehearsal profile cannot pose as a real one.

## D-3A6.4 Invisible characters beyond C0 are refused per row (3A3 residual; amends D-3A3.9)

- **Ruling.** A cell of a column that writes a path is refused (`NATIVE_CHARACTER`, its row alone) when it holds a
  character of Unicode category Cc (C1 controls U+0080 to U+009F included), Cf (U+200B to U+200F, U+FEFF, U+00AD, the
  bidirectional marks and the rest), Zl, Zp or Cs, besides 3A3's set; tab, LF and CR stay text. Dropped columns are not
  checked. The words now say "such as a NUL byte or an invisible mark".
- **Why.** D-3A3.9's reason applies unchanged: an invisible character inside a reference splits one customer into two
  pseudonyms. 2a already refuses C0 and C1 in refs (`_REF_BANNED`), but not zero-width or line-separator characters,
  which spreadsheet exports do carry (U+FEFF from a pasted cell, U+200B from web copies). Refusing in the engine,
  before 2a, gives the person one plain sentence for the whole class.
- **Class and sweep.** Class: an input check written as a code-point list where the risk is a Unicode category. Sweep:
  every character check on operator text: `layouts_v1._CONTROL` (now by category), 2a `_REF_BANNED` (C0 and C1; left:
  2a is a protected v1 seam, D-2A.2, and the engine now refuses the rest before 2a sees it), 3A2
  `has_control_character` (the two free-text inputs, file name and decline reason; C0 only; left: they are shown, not
  joined on, so an invisible mark there splits nothing), ON1's onboarding file (closed patterns, ASCII). No other
  site found.

## D-3A6.5 One source system per source type per Site, enforced at the intake (3A3 residual; amends D-3A3.7, D-3A3.14)

- **Ruling.** `CommercialUploads._check` refuses (409 `UPLOAD_SOURCE_SWITCHED`) a file whose kept records name a Site
  for which the tenant holds a waiting or accepted upload of the same source type from another source system. The
  emulated loader's own checks compare source types within a directory and source systems across runs (not reader IDs);
  the intake rule is the authority.
- **Why.** The double count D-3A3.7 guards against comes from the same money arriving under two record identities, and
  a record's identity is `(tenant, source_system, source_record_id)` (3A1). Reader IDs were the wrong key: two versions
  of one profile are two readers with one source system (their records revise each other, no double count), while the
  template and a profile for the same ledger are two systems (they would double count). D-3A3.14's reader-ID rule also
  lived only in the emulated loader, while real files arrive through the route. Narrowing by Site keeps a legitimate
  case: an operator whose Sites run on two vending platforms.
- **Class and sweep.** Class: a cross-upload invariant enforced in a caller instead of the one writer. Sweep: every
  caller of `CommercialUploads.check` and `.submit`: the route (now covered by the intake), the emulated loader (keeps
  an earlier, stricter, whole-directory check), ON1's command (submits nothing). `held_uploads` is the one read; it
  gains `source_system` and `site_codes`.

## D-3A6.6 Coded paths must be mapped, and the suite derives its probes from the canonical side (3A3 residual)

- **Ruling.** `CODED_PATHS` (the twelve closed-vocabulary paths: kind, status, subject kind, quantity unit and the body
  enums including `factor_id`) is fixed in the engine. A column writing one must carry a map; a map is allowed only on
  one. `check_layout` enforces this for every layout. The contract suite replaces `mapped: (header, value) | None` with
  `coded`, one probe per coded column, and asserts that the probed headers equal those whose column writes a coded path,
  computed from its own hand-written copy of the twelve paths.
- **Why.** The residual: a case with `mapped=None` was accepted when the layout declared no map, so a layout that wrongly
  omitted a map would hide, and an unmapped `factor_id` lets an operator heading such as `marketing` through as a factor
  nobody declared (2a checks only its pattern). Deriving from the canonical side makes the probe depend on what the
  column writes, not on what the layout claims. The sweep found a second gap of the same class: the illustrative
  expenses layout maps `Status`, but its case probed only `Category`; it now probes both.

## D-3A6.7 The single-writer test sees dynamic imports and names built from strings (3A3 residual; amends D-3A3.12)

- **Ruling.** S1 also fails on: a dynamic import call outside a reviewed allowlist (exactly the set found on `main`);
  any dynamic import naming the commercial package, allowlisted or not; outside the writers, a string constant
  `"ingest"` or `"CommercialRecords"`; in a module importing the commercial package, a non-constant `getattr`-family
  name or `operator.attrgetter`/`methodcaller`; `eval`, `exec` or `compile` in the commercial package or the native
  engine. Five planted sources prove each.
- **Why.** D-3A3.12 left these to review. A profile is data, and data must never become a way to reach code: the
  `eval` rule pins that; the others close the dynamic routes to `CommercialRecords.ingest`. No current file holds the
  `"ingest"` literal, so the rule costs nothing today. Still not seen, stated in the packet: a module importing nothing
  commercial that calls `.ingest` on a service handed to it (ten `.ingest` attributes of other services make a blanket
  rule noisy).

## D-3A6.8 Only the latest admitted version of a profile reads

- **Ruling.** Reader IDs are `profile.<profile_id>.v<version>`; an older version is refused with the latest's ID. The
  loader resolves `<SLUG>.profile.<profile_id>.<ext>` to the latest.
- **Why.** Versions of one profile share a source system, so their records revise each other; reading through an old
  version would re-introduce the fault the new version fixed. Naming the latest in the refusal tells the person what to
  do.

## D-3A6.9 Single-sheet XLSX through the standard library, with Excel's 15 digits

- **Ruling.** `native/xlsx.py` reads exactly one sheet with zipfile and ElementTree, refusing a DTD or entity, oversize
  members, the 1904 date system, error and ISO-date cells. Numbers are rounded to 15 significant digits and written in
  plain notation; a typed date, datetime or month column also reads an Excel serial.
- **Why.** The owner scoped "CSV and single-sheet XLSX" (§0.1 row 5); the contracts package is standard library only,
  and no XLSX library is installed. Excel stores money as binary floats and shows 15 significant digits, so
  `874.99999999999989` is the 875 the person typed; rounding to 15 digits recovers it exactly without inventing
  precision. Several sheets or merged cells go to the reshaping fallback (RC2), timed.

## D-3A6.10 The emulated loader takes admitted profiles; the command does not refuse operator databases

- **Ruling.** The loader admits `<SLUG>.profile.<profile_id>.csv|xlsx` once that profile is admitted for the tenant.
  `source_profile` composes through `commercial_upload_settings` and so runs on an operator database only with the
  real-data switch on, and elsewhere only with it off.
- **Why.** `DDR` must load an unseen shape "through a new profile with no code change" on the rehearsal tenant, and
  its runbook drives the loader. A pinned profile belongs where the operator's data lives (D-3A6.2), so the admission
  command must run there; the settings switch already refuses a mismatch both ways (RC4-F1).
