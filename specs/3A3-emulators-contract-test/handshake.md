# 3A3 handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a pre-flight
of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and I1, I2 .... Each
question cites the spec section, says what is unclear and what answer the writer expects, and is marked **(done)**
when its answer changes what counts as done. The Architect answers every question once, in `rulings.md` under
"Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when neither section has an
open question; coding starts only then.

## Reviewer questions

Fresh Claude reviewer, 2026-11-20, on `main` d555e08c6 (no code change under `backend/`, `contracts/`, `simulator/`,
`tools/world_history.py` or `tools/checks/` since 6db81330a). Severity is the reviewer's; High blocks code.

- **R1 (High, done) §2.6 step 2, D-3A3.6: the operator-database refusal can be bypassed by the URL's query.**
  `database_name(url)` is `make_url(url).database`. For `postgresql+psycopg://u:p@h/assetops_test?dbname=assetops_op_x`
  it returns `assetops_test`, but the psycopg dialect's `create_connect_args` passes `dbname=assetops_op_x` and connects
  there (checked on the venv). `.../?dbname=assetops_op_x` gives `''`, not `None`, so the "`None` is refused" rule passes
  it too; `service=` and `PGDATABASE`/`PGSERVICE` choose the database the same way. 3A2's `commercial_upload_settings`
  has the same hole, so the switch-off check also admits it. Expected: one helper (used by both) that refuses a URL whose
  query names `dbname`, `service` or `options`, treats `''` as no name, and refuses when `PGDATABASE`/`PGSERVICE` is set
  with no name; L1 gains `?dbname=assetops_op_x`, `/?dbname=...` and `''` cases; a plant (drop the query check) fails L1.
- **R2 (High, done) §2.2 reading step 2, contracts test 2: "a NUL byte is `NATIVE_ROW row.<n>`" cannot pass as
  specified.** The project Python is 3.12.16; its `csv.reader(..., strict=True)` reads `1,\x002` as `['1', '\x002']`
  without `csv.Error` (run on the venv). Expected: an explicit rule (e.g. after decoding, a row whose raw text holds
  U+0000, or any C0 control other than tab/CR/LF, is `NATIVE_ROW row.<n>`; or the whole file `NATIVE_ENCODING`) and the
  test pinned to it.
- **R3 (Medium, done) §2.3, C10, and ON1 `runbook.md` step 8: is an illustrative layout ever admitted on real data?**
  Every layout fixes `provenance="source-emulated"`, and C10 asserts real data refuses it (`ADMITTED[True]` is
  `observed-financial` only, `uploads.py:41`). ON1's runbook step 8 tells the analyst to reshape a real export into these
  layouts before `3A6`: that path is refused every time. Expected: the Architect picks one (provenance from the context
  when `real_data`, a separate real layout id, or the runbook says real exports wait for `3A6`), and C10 says which.
- **R4 (Medium, done) §4 `CONTRACT_CASES`, C3: required headers are given for billing only** ("the same for the others
  with their headers"). Expenses row 2 is a FUEL row, so `Litres` is required there by 2a's `_When` rule but not on the
  OM row; budget `Site` is optional (`BUDGET_LINE` site presence "O"). Expected: the exact `required_headers` tuple for
  collections, expenses and budget.
- **R5 (Medium, done) §2.5 New records: number types.** The fixture holds money and prices as strings (`"3458.0"`,
  `"0.55"`), litres and kWh as ints, and `tenant.prices[...]` is keyed by Site *name* (`"Kobo"`), not code. With float
  arithmetic `0.55 * 100` is not whole and `EMU_PRICE` fires spuriously. Expected: "all arithmetic in `Decimal` from
  `str(v)`; cents by exact `* 100` with a whole check; prices looked up by `site["site"]`; `diesel_l`, `billed_kwh` must
  be whole (`EMU_PRICE` otherwise)".
- **R6 (Medium, done) §2.5 Reused from DS1b: the carried `unwritten` rows contradict the files.** For October DS1b lists
  `revenue`, `diesel_cost`, `collected`, `in_transit`, `outstanding` (actual, `NOT_A_MONTH_RECORD`), plan `revenue`,
  `diesel_cost`, `billed_kwh`, `diesel_l` (`NOT_READ_BY_A_LEAF`/`NOT_OWN_LINE`); the emulator then writes them. Carried
  "as they are", `unwritten.json` says a written figure was not written. Expected: drop DS1b rows for fields the
  emulator writes (or re-reason them), with an E-test.
- **R7 (Medium) §2.5: a DS1b record of a kept kind the layout cannot render** (a later plan leaf such as `in_transit` or
  an EXPENSE category outside the map) raises `NATIVE_RENDER` and stops the tool. Today only `om`/`staff` reach budget,
  but the rule should be stated: listed `NOT_IN_LAYOUT`, or an `EMU_` stop with its own code.
- **R8 (Medium, done; queue Q1) §2.6 `--accept-as`: a script records a decision in a named person's name.** 3A2's
  `decide` does not stop the submitter accepting their own upload, and ON1's runbook step 9 shows
  `--submit-as $EMAIL --accept-as $EMAIL`. Expected: the owner answers Q1 before code (OD-15 records acceptance "as the
  person's"); at least the loader refuses the same person for both, and the JSON line says the decision was scripted.
- **R9 (Medium) D-3A3.7 holds only inside one directory.** A tenant loaded once from DS1b JSON (`DS3`) and later from
  CSV (`DDR`) double-counts O&M and staff (different `source_system`). Expected: the loader refuses when the store
  already holds that tenant's source type under the other system (one read), or the ruling names it an accepted
  residual with the runbook line that prevents it.
- **R10 (Low) S1's reach.** State which forms it catches: `from ... import CommercialRecords as CR; CR(...)`,
  `getattr(x, "ingest")(...)`, `r = svc.ingest; r(...)`. The guide asks; the spec should answer.
- **R11 (Low) Plants that cannot fail.** Every `ContractCase.scope` is ORGANISATION, so C1 never exercises a Site
  scope (add one SITE case or drop the field); E8 has no `EMU_COLLECTIONS` or `EMU_PRICE` plant.
- **R12 (Low) §2.6 step 6: "a rerun is idempotent" only after acceptance.** Without `--accept-as`, a rerun submits the
  same file again as a second SUBMITTED upload. Expected: say so, or skip a file whose `file_sha256` is already waiting.
- **R13 (Low) §2.2 step 4:** a quoted cell spanning lines gives the row number of its *last* line (checked); say so.
- **R14 (Low) D-3A3.1 binds `DS3`:** DS1b's `records` directory holds every tenant's batches, and step 4 refuses
  another tenant's file (`EXPORT_FILE_UNKNOWN`), so `DS3` must split per tenant. Say it in the ruling.

## Implementer pre-flight

Same reviewer acting as Implementer, read-only, against `main` d555e08c6.

- **P1 (verified)** Every name §0 and the header cite exists: `parse_batch`, `parse_record`, `CanonicalRefused`,
  `SOURCE_TYPES`, `to_canonical_json`, `loads_canonical`; `ReadResult`, `SourceReader`, `CanonicalJsonReader`, `READERS`,
  `DEFAULT_READER`; `CommercialUploads._check/.submit/.decide`, `UploadScope`, `Actor`, `UploadRefused`; `PERSONAL_FIELDS`,
  `cut_path`; `commercial_upload_settings`, `build_commercial_uploads`, `build_commercial_records` (no caller outside
  `composition.py`; only 3A1's spec text names it); `database_name`; `roles_of`, `COMMAND_ROLES`
  (`commercial.upload` = ANALYST, FINANCE; `commercial.upload_decision` = FINANCE, EXECUTIVE); `build_records`,
  `money_text`, `batch_file_name`, `generate_history`, `period_end`, `load_view`, `_out_dir`.
- **P2 (verified)** 2a: `BUDGET_LINE` site presence is "O" (the `ORG-...` golden row is legal); `revenue`, `fuel_cost`,
  `billed_kwh`, `diesel_l` are structure nodes, not in `LEAF_FACTORS`, so the `budget_currency` rule skips them;
  `tariff` (MONEY/KWH) and `diesel_price` (MONEY/L) are leaves and need a currency, which §2.5 writes. The `+00:00`
  `produced_at` matches `_INSTANT`. `CHARGE` forbids `status`; `EXPENSE` FUEL requires `quantity` (unit L).
- **P3 (verified)** Fixture October figures reproduce E2 to E6 by hand: Kobo 8645 kWh / 40 = 216 r5, 217 x 0.40 = 86.80,
  revenue 3458.00; collected 3180.00 pays customers 1 to 36 and 67.60 of 37 (37 receipts); Mto 1890.00 = 35 x 54.00,
  in transit 150.00 = 54 + 54 + 42 (38 receipts); Kisiwa 7400 x 0.55 = 4070.00, 37 full + 1 part (38); fuel 1180 L =
  400/400/380 on days 1, 11, 21 (31 // 3 = 10); Kisiwa OM coverage ESTIMATED. No literal disagrees.
- **P4** `test_3a2_commercial_upload_service.py:585-592` `ExtraReader.read(self, data)` must take `context`; that file
  is outside §7 question 9's list. Add it (and say "signature only").
- **P5** New `AccountStore.tenant_slug`: the implementers are the Postgres adapter and `MemoryStore` in
  `backend/tests/test_3c0a_accounts_service.py:50` (outside the list too). Add it.
- **P6** §2.2 `maps: Mapping[...] = {}`: a dataclass refuses a `dict` default; I will use `MappingProxyType({})`
  (unless you prefer `field(default_factory=...)`). No behaviour change.
- **P7** §2.4: when `tenant_slug(tenant_id)` is `None`, `read_layout` gets `tenant_code=None` and 2a refuses the envelope
  (`CANONICAL_TYPE batch.tenant_code`, a file refusal) where the JSON reader gives `UPLOAD_TENANT_MISMATCH`. I will
  raise `UPLOAD_TENANT_MISMATCH` before reading unless ruled otherwise.
- **P8** §2.4: a `csv.Error` is a whole-file refusal with path `row.<n>`; `_file_refused` labels it "row n" and the
  code is `UPLOAD_FILE_REFUSED`. C8 checks only the header case; I will add one quoted-field case.
- **P9 (verified)** S1 on `main`: AST `.ingest(` calls in modules importing `assetops_backend.commercial` are only in
  `commercial/uploads.py` (the `service.py` hit is its docstring); the tests' `CommercialRecords(` calls are excluded.
  S1 passes once `build_commercial_records` is deleted.
- **P10 (verified)** T2's `tools/checks/neutral_tests.py` collects `contracts/tests` (min 1 passed): the contracts file
  runs there. No guard limits `assetops_contracts` sub-packages.
- **P11** E1 names `lakeside-power.*.csv`; L2 renders into `acme.<key>.csv`. The fixture is
  `simulator/tests/world/fixtures/view_v1.json`, not the YAML manifest; the runbook's `exports` line uses the YAML.
  The packet will record both SHA-256 sets if they differ.
