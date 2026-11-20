# ON1 handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a pre-flight
of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and I1, I2 .... Each
question cites the spec section, says what is unclear and what answer the writer expects, and is marked **(done)**
when its answer changes what counts as done. The Architect answers every question once, in `rulings.md` under
"Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when neither section has an
open question; coding starts only then.

## Reviewer questions

Fresh Claude reviewer, 2026-11-20, on `main` d555e08c6. Severity is the reviewer's; High blocks code.

- **R1 (High, done) D-ON1.3, queue Q1: the default amends an owner decision.** OD-14 ("the executive grants and removes
  roles ... each change recorded") is an owner decision (D-2026-11-19-l4-pack-answers), and D-3C0A.7 kept onboarding to
  the first executive for that reason. Applying a default that lets `service:onboarding` grant every role needs the
  owner's yes before code, not after. And if yes: the person who runs `apply` is the analyst ("often you", runbook step
  1), who can write a FINANCE role for themselves into the file; the executive's confirmation lives only in an email.
  Expected: owner answer first; then the plan prints the file's SHA-256, the runbook records it beside the executive's
  written confirmation, and `apply` refuses a file whose people/roles differ from a confirmed digest passed on the
  command line (or the Architect states why not). Also say whether an AssetOps analyst holding an account inside the
  operator's tenant is intended.
- **R2 (High, done) D-ON1.5: the demo on 5490 can silently stop serving demo.** `host/lab_app.py` calls `create_app`,
  and `tools/demo_combined.py` `env()` copies `os.environ` whole (line 852) into the serve child. Runbook step 4 tells the
  coordinator to `export ASSETOPS_TENANT_SLUG=$SLUG`; a later demo restart from that shell serves the operator's (absent)
  Sites, with no error. Expected: `demo_combined` pins `ASSETOPS_TENANT_SLUG=demo` (and drops `ASSETOPS_REAL_OPERATOR_DATA`
  and `ASSETOPS_PSEUDONYM_KEY_DIR` unless it sets them itself), with a test; the runbook uses `env VAR=... command` or a
  subshell, never `export`; optionally `create_app` refuses a served slug that has no tenant row on first registry read.
  Add `tools/demo_combined.py` to §4.
- **R3 (High, done) Runbook step 8: the real-data path is refused.** The illustrative layouts are fixed
  `provenance="source-emulated"` (3A3 §2.3) and an operator database admits only `observed-financial`
  (`uploads.py:41`; 3A3 C10 asserts the refusal). So "reshape each export into one of the layouts" cannot land one real
  record. Expected: joint ruling with 3A3 R3, and the runbook changed to what works.
- **R4 (High, done) D-ON1.6, §6 service 7 and settings 2: an RC4 test must be unable to connect, not merely not
  expected to.** Settings 2 hands `create_app` a URL naming `assetops_op_pilot1`; under plants V3/V4 `create_app`
  carries on composing stores from that URL. If the URL names the real host (127.0.0.1:55432) and the coordinator has
  created that database, a reviewer's plant run touches real data. Expected: every URL naming `assetops_op*` in a test
  uses an unresolvable host (e.g. `@rc4.invalid:1/`), and an autouse fixture in those files makes
  `sqlalchemy.create_engine` and `psycopg.connect` raise. Also add 3A3 R1's `?dbname=assetops_op_x` and empty-name URLs
  to the matrix: `check` step 1 relies on `commercial_upload_settings`, which admits them today.
- **R5 (Medium, done) Runbook step 9 cannot succeed as written.** It has no `onboard_operator check/apply` lines; it
  never sets `ASSETOPS_TENANT_SLUG` (check step 2 refuses `ONBOARD_TENANT_NOT_SERVED`), `DATABASE_URL` or
  `ASSETOPS_PSEUDONYM_KEY_DIR` (the loader exits `COMMERCIAL_UPLOAD_OFF`); and `--submit-as $EMAIL --accept-as $EMAIL`
  is `PERSON_ROLE_REQUIRED` for an analyst-only person. It also does not say which database (not the walkthrough DB of
  5490?). Expected: full lines with `$ANALYST_EMAIL` and `$FINANCE_EMAIL` and the database named.
- **R6 (Medium, done) Settings 3, the runbook test, can pass vacuously.** If the fence or prefix match finds nothing, it
  passes. Expected: assert the checked lines, exactly (today 5: `check`, `apply`, `set-password`,
  `load_emulated_exports`, `erase`); also check `python tools/world_history.py ...` (give it a `build_parser`) and that
  `assetops_backend.main` has `app`. Without this, a step 9 class of error (missing settings) is never caught; say so in
  the guide as a residual.
- **R7 (Medium) Erasure is final only for the key.** Step 10 leaves the onboarding file (emails, names), the raw and
  reshaped export CSVs (raw customer refs), the curl cookie files, and any on-server backup of `KEY_DIR` or the database
  (step 3 excludes only backups "that leave the server"). Expected: step 10 lists each with its delete command, and
  step 3 keeps the key out of every backup.
- **R8 (Medium, done) §3.5 tombstone detection must fail closed and agree in all three places.** `FileKeyStore.key`
  opens the tombstone `O_RDONLY`: a tombstone the server user cannot read (written 0600 by the coordinator as another
  user) raises `PermissionError`, a 500, not 409. `key_state` and `create_key_file` say "exists": `Path.exists` follows
  symlinks, so a dangling-symlink tombstone is ERASED in `key` but absent there. Expected: one `_tombstoned(dir, id)`
  using `os.lstat` (anything but `FileNotFoundError` is erased), used by all three; keys tests 2 and 4 gain an
  unreadable and a dangling-symlink tombstone.
- **R9 (Medium, done) §3.5 `erase_key_file`, two edge cases.** (a) Tombstone present and key still present (the crash
  case): is the key unlinked? The sentence reads as if the unlink sits inside "if no tombstone". Expected: always unlink;
  return `ERASED`. (b) Neither file (key lost): `KeyMissing`, no tombstone, so a later `apply` on the same database
  creates a new key and every pseudonym changes. Expected: erase writes the tombstone anyway when the directory exists.
- **R10 (Medium) §3.1: avoidable failures after writes (exit 3).** A missing key directory fails at the last step,
  after tenant, Sites and people exist; an executive conflict on an existing tenant is found only by `onboard_create`.
  Expected: `check` verifies the key directory (exists, is a directory, mode 0700 or stricter) and the tenant's current
  executive.
- **R11 (Medium) Settings 2 second half names `assetops_test` directly**, outside the harness's routed databases, and
  builds the account, foundation, evidence and gateway stores plus the on-disk repositories. Expected: inject an
  in-memory `foundation_store` and the other fakes with a URL that cannot connect, and add a public accessor for the
  registry's served slug instead of reading private attributes.
- **R12 (Low) §2 `ONBOARD_SITE_INVALID` "plus the parser's message"**: the Site parser's messages quote values
  (codes, component ids), against "`where` ..., never a value". Expected: say Site fields carry no personal data, or
  print code and `where` only.
- **R13 (Low) Runbook step 8**: the password sits on the curl command line (shell history, `ps`); `finance.cookies` is
  never created; session cookies are `Secure` by default over plain http (`ASSETOPS_SESSION_COOKIE_SECURE`). Expected:
  `-d @-` from stdin, the finance lead's sign-in line, and the cookie setting stated.
- **R14 (Low) §3.1:** `OperatorOnboarding` takes `database_name` but `check` never reads it. Use it (a `real` file needs
  the exact `assetops_op_<name>` form) or drop it.
- **R15 (Low) §0 vs D-ON1.6 wording:** §0 says no test "names" an `assetops_op` database, yet service 7 and settings 2
  name one in `DATABASE_URL`. Use the ruling's "names in a connection".

## Implementer pre-flight

Same reviewer acting as Implementer, read-only, against `main` d555e08c6 (3A3 not yet built: `onboard_person`,
`load_emulated_exports` and `assetops_contracts.native` do not exist; Postgres 4 and the runbook test wait for it).

- **P1 (verified)** `FoundationStore.resolve_tenant` raises `TenantNotFound`; it never returns `None`, so check step 4
  catches it. `ensure_tenant` is `INSERT ... ON CONFLICT (slug) DO NOTHING`, so `import_site`'s own
  `ensure_tenant(slug, "Development tenant")` keeps the operator's name. `import_site(store, *, tenant_slug,
  configured_tenant_slug, source, legacy_documents, clock)`, `ImportSource(path, sha256, record, document_format)`,
  `find_site(...).import_record.source_path/source_sha256` exist as cited; `site_import.source_format` is plain text
  (0001), so `ASSETOPS_ONBOARDING_JSON` needs no migration.
- **P2 (verified)** `parse_site_document(document, *, source)`; `SITE_KEYS`, `LOCATION_KEYS`, `SOURCE_KEYS`,
  `FOUNDATION_KEYS` (version, valid_from, summary, components plus content keys) and `COMPONENT_KEYS` match §3.2;
  `VALID_FROM_PATTERN` needs the `Z` form the fixture uses. Not yet verified: that `PV_ARRAY`, `INVERTER`, `BATTERY`,
  `GENERATOR` with kW/kWh ratings parse for `MINIGRID`; commit 1's fixture test will prove it.
- **P3 (verified)** `accounts/onboard.py:36` `_parser` has no importer, so the rename is safe;
  `commercial/pseudonym_key.py` builds its parser inside `main` and must be split out. `role_grant`'s checks (0062)
  admit a `by_service` grant of any role, so no migration is needed. `_lock_tenant`/`_TENANT_LOCK` exist for
  `add_onboarding_grant`. `MemoryStore` (`test_3c0a_accounts_service.py:50`) has `add_tenant`, `add_site`,
  `tenant_by_slug`, `site_id` to subclass.
- **P4 (verified)** `commercial/adapters/file_key_store.py` is the registered writer (`configuration-persistence.ps1`
  line 225), so the tombstone and the unlink belong there; a planted `os.unlink(` in `pseudonym_key.py` matches the
  write-call rule and fails.
- **P5 (verified)** `DEVELOPMENT_TENANT_SLUG` decides what is served only in `main.create_app`. The walkthrough tools
  `w502`/`w504` build their own registry with it and are unaffected. No migration seeds a tenant row, so a fresh
  operator database is empty for check step 3.
- **P6** `main.py:853` runs `app = create_app()` at import, so the new `served_tenant_slug()` runs whenever any test
  imports `assetops_backend.main`; a bad ambient `ASSETOPS_TENANT_SLUG` breaks collection, not one test. Settings
  tests must set the variable with `monkeypatch` and call `create_app` themselves.
- **P7** `onboard_create` normalises email and checks the name (`BAD_NAME` 422, `EMAIL_TAKEN` 409) before writing.
  `apply` maps these to exit 3, but `check` has already caught both (`ONBOARD_EMAIL_TAKEN`, `ONBOARD_NAME`). I will
  keep them as backstops.
- **P8** §6 service 2 says "6 grants"; Postgres 1 says "7 grant rows". Both are right: 6 onboarding grants plus the
  executive's. The tests will name both counts so they do not read as a mismatch.
