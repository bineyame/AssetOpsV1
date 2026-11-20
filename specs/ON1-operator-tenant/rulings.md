# ON1 rulings

Architect (Claude), 2026-11-20. D-ON1.1 to D-ON1.8 are applied by `spec.md` rev 1; rev 2 applies D-ON1.9 to
D-ON1.14 and the handshake answers below; rev 3 applies D-ON1.15 and D-ON1.16 (the re-scope). **D-ON1.3 is
superseded by D-ON1.9** (owner, 2026-11-20); **D-ON1.9 is deferred to the queued unit `ON1b`** for real data and
replaced on emulated data by D-ON1.15 (owner, 2026-11-20). D-ON1.7 settles the 3A2 review's residual
"a recreated key changes every pseudonym" (`specs/3A2-commercial-file-intake/review.md`, "Residual risk").

## D-ON1.1 One file, checked then applied, additive and re-runnable

- **Ruling.** The operator, its Sites and its people come from one JSON onboarding file. `check` prints the plan and
  writes nothing; `apply` runs the same check and then creates only what is missing. Anything that exists with other
  details is refused, never changed. A rerun after a partial failure completes the rest.
- **Why.** D-BW1.11 asks for one onboarding file the analyst fills. The writes span three stores (Sites, accounts, key
  file) with no shared transaction, so convergence (re-check, then add the missing) is what makes a half-done run
  safe. Refusing changes keeps onboarding from becoming a second way to edit Sites or roles beside the Foundation and
  the executive's grant API.

## D-ON1.2 Sites through the existing Site import, with a generated Site document

- **Ruling.** Each Site is created by `import_site` from a Site document built from the file entry
  (`site_type` MINIGRID, origin USER, source LIVE for real and SIMULATED for emulated data, foundation version 1 with
  the operator's components). Its import path is `onboarding:<slug>/<code>` and its digest covers that Site's entry
  only. At least one component is required (the Site parser's rule).
- **Why.** The server serves only imported Sites (`ImportedSiteRegistry`); the import is today's one creation path,
  with its idempotency and conflict rules. Reusing it avoids a second Site writer. The installed components are facts
  the operator gives anyway and later units (`4d`, `4a`) need.

## D-ON1.3 Roles from the file at onboarding only; then the executive grants (refines D-3C0A.7) — SUPERSEDED by D-ON1.9

- **Ruling.** Besides the first executive's grant, `apply` grants every role in the file by `service:onboarding`
  through `onboard_grant`. Once any role has been granted by a person, onboarding grants are refused
  (`ONBOARDING_CLOSED`) and the executive's API is the only way.
- **Why.** The deep-dive needs an analyst and a finance lead with roles before the first export, and there is no
  sign-in page this fortnight (RC7, `3C0b` moved out), so asking the executive to grant each role through the API
  would put curl in an executive's hands. The file the executive confirmed (runbook step 1) is their decision; the
  grant rows say it came from onboarding. OD-14 holds from the executive's first act. **Owner to weigh in** (queue Q1).

## D-ON1.4 No password in the file or the output

- **Ruling.** Accounts are created with a random password that is discarded; each person's password is set afterwards
  with 3C0a's `set-password`, typed on standard input. The plan prints no email, name or password.
- **Why.** A file of passwords would be a credential store in a working folder. 3C0a's command already handles the
  typing; this keeps one way to set a password.

## D-ON1.5 The server serves the tenant `ASSETOPS_TENANT_SLUG` names

- **Ruling.** `served_tenant_slug()` reads `ASSETOPS_TENANT_SLUG` (default `demo`); `create_app` builds the Site
  registry for it and refuses to start with the real-data switch on and the default. Command-line tools that refuse
  other tenants keep `DEVELOPMENT_TENANT_SLUG`.
- **Why.** The server has served one hard-coded tenant since S1-01, so an onboarded operator's Sites would answer "not
  found" on 3A2's Site path. One served tenant per process matches one operator per database (RC4).
- **Sweep (W6).** `grep -rn DEVELOPMENT_TENANT_SLUG` on `main`: 48 uses; `main.py`'s `FoundationService` is the only
  one that decides what the server serves. The rest are tools, backfills and walkthrough scripts for the demo tenant,
  none on the deep-dive path. `3B7a`'s rebuild command, not yet written, takes `served_tenant_slug()`.

## D-ON1.6 RC4 in onboarding

- **Ruling.** A `real` file is applied only with `ASSETOPS_REAL_OPERATOR_DATA=on` (which 3A2's settings already tie to
  an `assetops_op_<name>` database), the served tenant equal to the file's operator, and no other tenant in the
  database; an `emulated` file never with the switch on. Tests check every branch with names alone, on in-memory ports;
  no test creates, names in a connection or touches an `assetops_op` database.
- **Why.** RC4: real data in its own database, created by the coordinator only after a signed DPA. Code cannot see the
  DPA, but it can make the coordinator's database the only place a real file lands and keep emulated data out of it.

## D-ON1.7 Erasure is terminal: a tombstone, never a new key (3A2 residual)

- **Ruling.** Erasing a tenant's key writes `<tenant_id>.erased` before removing the key. With a tombstone the key
  store refuses (`PSEUDONYM_KEY_ERASED`, 409, in plain words), the key command refuses to create a key, and
  onboarding refuses the tenant. A returning operator is onboarded as a new tenant in a new database. Supersedes the
  erasure sentence of 3A2 §3.4 ("Erasure is deleting the file").
- **Why.** A recreated key changes every pseudonym, so a re-sent file would conflict with its own earlier records
  (`INTAKE_VERSION_CONFLICT`) and customers would stop linking: a silent corruption of the history. Recording the key's
  fingerprint in the database was rejected: it needs a migration for a case the runbook avoids (the key and the
  database are erased together), and a tombstone beside the key makes the refusal immediate with no schema change.

## D-ON1.8 Not collected at onboarding: currency, tariff, diesel price, loss band

- **Ruling.** The onboarding file holds none of them. Money carries its currency on every record (2a); the tariff, the
  budget's prices and fuel prices arrive as the operator's own records through intake (a tariff sheet, budget lines,
  fuel invoices); the expected technical loss band waits for `4a`, which connects `technical_loss_kwh`.
- **Why.** None has a reader today (`3B3` holds `tariff` and `technical_loss_kwh` NOT_CONNECTED; `tenant.default_currency`
  has no reader), and a field collected with no reader is a value silently ignored. Records through intake keep the
  evidence word of their source. Recorded so `4a` and `5a` pick them up (queue Q3).

## D-ON1.9 The file proposes roles; the executive approves them at sign-in (owner answer; supersedes D-ON1.3) — DEFERRED to `ON1b` by D-ON1.15 (still the rule for real data)

- **Ruling.** The onboarding file names people and **proposes** their roles. `apply` creates the accounts and the
  executive's own grant (D-3C0A.7, unchanged) and records every other role as a `role_proposal` row (migration 0066,
  append-only, with a `role_proposal_outcome` table). **Nothing is granted until the executive approves.** The
  executive approves by signing in with `approve_roles` set to the roles digest they confirmed (D-ON1.10): every open
  proposal of that digest becomes a grant **made by the executive** (`role_grant.by_person_id`), in one transaction
  under the tenant's role lock, and the answer lists them. Signing in without it grants nothing and lists what
  awaits approval; a different digest grants nothing (409). A proposal whose person is not active, or whose role is
  already held, is skipped with its reason. Once a person-made grant exists, `apply` proposes nothing more
  (`ONBOARDING_CLOSED`).
- **Owner.** `owner/owner-on1-roles-executive-approves-2026-11-20.md`, verbatim: "A, executive approves roles at first
  sign-in". OD-14 holds: every non-executive grant is the executive's own recorded act. Rev 1's default (the command
  grants the file's roles, D-ON1.3) is dropped.
- **Why the approval carries the digest.** The owner's word is "approves". A grant applied by any sign-in would
  happen whether or not the executive knew what the file held; naming the digest they confirmed in writing makes the
  sign-in an approval of exactly that file, and the analyst cannot change the roles after confirmation (the digest
  would differ) without the executive seeing a refusal. The approval stays inside sign-in (no new route), so the
  executive's one sign-in is the only act asked of them; it departs from RC7's "the executive does not sign in" for
  this act alone, which the owner's answer requires.
- **Cost.** One migration (two append-only tables), a step in sign-in, two fields in its answer. The rehearsal and the
  real runbook each include the executive's sign-in (the coordinator with the executive, on 127.0.0.1).

## D-ON1.10 The executive confirms a digest; submitting and accepting are different people

- **Ruling.** `roles_digest(f)` is the SHA-256 of the canonical JSON of the operator slug and, per person in email-key
  order, the email key, the name and the sorted (role, Site) pairs. `onboard_operator digest --file` prints it with no
  database; `apply` requires `--confirmed-digest` equal to it (`ONBOARD_DIGEST_DIFFERS`, before any write). The file
  is refused if any person holds `ANALYST` together with `FINANCE_AND_COMMERCIAL_LEAD` or `OPERATOR_EXECUTIVE`
  (`ONBOARD_ROLES_SEPARATE`).
- **Why.** R1: the executive's confirmation must bind the file that is applied, not a file edited afterwards; a
  digest the executive names in writing does that with no store. Separation stops the analyst, who submits, from
  also accepting their own export (OD-15's acceptance "as the person's" must be a second person's). Later grants
  through the executive's API are not limited here (a residual for the grant API, carried to `3C0b`).
- **Answer to R1's last question.** Yes: an AssetOps analyst (today the owner) holds an `ANALYST` account inside the
  operator's tenant, under the signed agreement, proposed in the file like any other person. It can submit, never
  accept.

## D-ON1.11 The demo serves the demo tenant whatever the shell holds

- **Ruling.** `tools/demo_combined.py` `Demo.env()` sets `ASSETOPS_TENANT_SLUG=demo` and removes
  `ASSETOPS_REAL_OPERATOR_DATA` and `ASSETOPS_PSEUDONYM_KEY_DIR` (it sets neither itself), beside RC4-F1's removal of
  the `PG*` target variables. The runbook never exports an operator setting into the shell: every operator command
  runs inside a `( ... )` subshell.
- **Why.** R2: the demo copies the shell's environment into the serve child, so one `export` from the runbook would
  make a later demo restart serve an operator's (absent) Sites with no error. Pinning in the one place every demo
  child's environment is built closes it for every child; the subshell rule stops the leak at its source.

## D-ON1.12 An RC4 test cannot connect, by construction

- **Ruling.** Every test URL naming `assetops_op*` (or any database, in the RC4 files) uses host `rc4.invalid` port 1;
  an autouse fixture in those files makes `psycopg.connect`, `psycopg.Connection.connect` and
  `sqlalchemy.engine.Engine.connect` raise, and one test proves the fixture raises. Settings 2's second half runs
  with no `DATABASE_URL` and an injected in-memory foundation store, read through a public accessor.
- **Why.** R4, R11: "the refusal precedes every connection" is true only while the code is right; under a planted
  violation the composition carries on to the URL's host. A name `.invalid` never resolves (RFC 6761) and the
  fixture fails any attempt, so a reviewer's plant run cannot touch a database even if the coordinator has created
  one with that name.

## D-ON1.13 The runbook is tested line by line, and erasure names every copy

- **Ruling.** The runbook test parses an exact, listed set of command lines (each `python -m assetops_backend.*`
  and `python tools/world_history.py` line, with `build_parser()`; the `uvicorn` line by checking `main.py` assigns
  `app`), fails on any extra or missing one, and fails on an `export` outside a subshell. Step 11 (erasure) deletes,
  by command, the key (tombstone), the database, the onboarding file, the export folder (raw and reshaped files),
  the cookie files, and any on-server copy of the key directory or database; step 3 keeps the key directory out of
  every backup, on the server or off it.
- **Why.** R6: a prefix match that finds nothing passes; an exact list cannot. R5 showed the class a parser cannot
  catch (missing settings); the subshell blocks put every setting next to its command, and the residual is stated in
  the guide. R7: "erasure is final" is true only if every copy holding identities goes with the key.

## D-ON1.14 Tombstone detection fails closed and is shared

- **Ruling.** One `_tombstoned(directory, tenant_id) -> bool` in `file_key_store.py`: `os.lstat` of the tombstone
  path; `FileNotFoundError` is False, any other outcome (a file, a symlink, a dangling symlink, a permission error)
  is True. `FileKeyStore.key`, `create_key_file`, `key_state` and `erase_key_file` use it. `erase_key_file` always
  writes the tombstone if absent, always unlinks a key if present, and answers `ERASED` (it erased something or
  wrote the tombstone) or `ALREADY_ERASED` (tombstone present, no key); a missing key with the directory present
  still writes the tombstone. `KeyMissing` is dropped.
- **Why.** R8: three detections that disagree leave a dangling symlink "erased" in one place and "absent" in
  another, and an unreadable tombstone gave a 500. R9: a crash between tombstone and unlink must still end with no
  key; and erasing a tenant whose key is already lost must still forbid a new one, or a later `apply` would mint a
  key and change every pseudonym.

## Handshake answers (round 1)

Architect (Claude), 2026-11-20, on `handshake.md` at `60710d425`. Folded into `spec.md` rev 2, `runbook.md` rev 2
and `reviewer-guide.md` rev 2. Builds after `RC4-F1` and `3A3`. Size 1.75 to **2.5 units**, **four commits**. The owner
answered D-ON1.9 during this round (A); no question is open.

- **R1 (High; owner answered).** The owner chose A ("A, executive approves roles at first sign-in"): D-ON1.9 is the
  ruling and D-ON1.3 is superseded. The file proposes roles; nothing is granted until the executive approves at
  sign-in with the confirmed digest; the grants are the executive's. D-ON1.10 binds the confirmation to the applied
  file (`--confirmed-digest`) and separates submitter from accepter. The analyst in the operator's tenant is intended
  (D-ON1.10). New plant V13: any proposed role granted before the executive approves fails service 3 and Postgres 1.
- **R2 (High).** D-ON1.11: `demo_combined` pins `ASSETOPS_TENANT_SLUG=demo` and drops the two operator settings; new
  test settings 4; the runbook uses subshells only; `tools/demo_combined.py` added to §4. The optional start-up check
  (refuse a served slug with no tenant row) is not adopted: it needs a database read before the first request, and
  the pin closes the case that matters.
- **R3 (High).** Joint with 3A3 R3, D-3A3.10: the owner kept hand reshaping as the fallback (RC2), so the layouts are
  admitted on an operator database with provenance `observed-financial`. Runbook step 9 puts `3A6`'s profile first
  and the template second, timed per file.
- **R4 (High).** D-ON1.12: host `rc4.invalid` port 1 in every such URL, the no-connect fixture with its self-test;
  RC4-F1's unclear URLs (`?dbname=assetops_op_x`, `/` with no name) join service 7's matrix through `check`'s
  settings step and settings 2.
- **R5 (Medium).** Runbook step 10 rewritten in full: a rehearsal database `assetops_rehearsal_<name>` (never 5490's
  walkthrough database, never `assetops_op*`), every setting in the subshell, `digest`, `check`, `apply`, the
  passwords, the executive's sign-in (A), the exports, and the loader with Wanjiru submitting and Joseph accepting.
- **R6 (Medium).** D-ON1.13: settings 3 asserts the exact list of checked lines (spec §6), parses
  `tools/world_history.py` with a new public `build_parser()`, checks `main.py` assigns `app` by AST (no import), and
  fails on a top-level `export`. The residual (a parser cannot see a missing setting) is in the guide.
- **R7 (Medium).** D-ON1.13: step 11 deletes every copy by command; step 3 excludes the key directory from every
  backup.
- **R8 (Medium).** D-ON1.14: `_tombstoned` by `lstat`, shared by all four; keys tests 2 and 4 add an unreadable
  (mode 000) and a dangling-symlink tombstone.
- **R9 (Medium).** D-ON1.14: (a) the key is always unlinked, answer `ERASED`; (b) no key and no tombstone writes the
  tombstone, answer `ERASED`; keys test 1 adds both.
- **R10 (Medium).** Accepted: `check` step 0 verifies the key directory (exists, a directory, `mode & 0o077 == 0`;
  `ONBOARD_KEY_DIR`), and step 6 compares the file's executive with the tenant's current one
  (`AccountService.executive_of(slug)`; a different or new person against an existing executive is
  `ONBOARD_EXECUTIVE_DIFFERS` at check, not exit 3 at apply).
- **R11 (Medium).** D-ON1.12: settings 2's second half has no `DATABASE_URL`, an injected `InMemoryFoundationStore`,
  and reads the new public `app.state.site_registry.served_tenant_slug` (`ImportedSiteRegistry` property from a new
  `FoundationService.tenant_slug` property).
- **R12 (Low).** Accepted: `ONBOARD_SITE_INVALID` prints code and `where` only; the parser's message is not printed
  or kept (`OnboardRefused(code, where)`, no detail).
- **R13 (Low).** Accepted: the password goes on standard input (`-d @-`); the finance lead's and the executive's
  sign-in lines exist; the server runs on 127.0.0.1 with `ASSETOPS_SESSION_COOKIE_SECURE=off`, stated as local http
  only.
- **R14 (Low).** Accepted: `database_name` is dropped from `OperatorOnboarding`; `commercial_upload_settings`
  (through RC4-F1) is the one decider.
- **R15 (Low).** Accepted: §0 says "creates, names in a connection, or touches".
- **P1 to P5 (verified).** Noted; no change.
- **P6.** Accepted: settings tests set `ASSETOPS_TENANT_SLUG` with `monkeypatch` and call `create_app` themselves; a
  bad ambient value failing at import is the intended loud failure, and the demo pin keeps it out of the demo.
- **P7.** Accepted: `onboard_create`'s refusals stay as backstops (exit 3).
- **P8.** Superseded by D-ON1.9: service 2 names "1 grant and 6 open proposals" after `apply`, service 3 "7 grants"
  after Amina's approval; Postgres 1 the same.

## D-ON1.15 Re-scope: emulated roles granted automatically; real files refused until `ON1b` (rev 3)

- **Ruling.** `apply` of an **emulated** file grants every role in it by `service:onboarding` (store
  `add_onboarding_grant`, under the tenant's role lock), after the executive's own onboarding grant. Once any grant
  by a person exists, onboarding grants stop (`ONBOARDING_CLOSED`). The submitter/accepter separation is checked
  twice: the file (`ONBOARD_ROLES_SEPARATE`, D-ON1.10) and the store (`ROLES_SEPARATE`, the class backstop for every
  onboarding grant). A **real** file passes `check`'s RC4 steps (data and switch agree, served tenant, one operator
  per database) and is then refused, `ONBOARD_REAL_AWAITS_APPROVAL`, before any write. No migration; sign-in, the
  grant API, the API answer and the persistence guard are not changed. The runbook keeps the rehearsal and erasure;
  the real-operator steps go to `ON1b`. The digest (`--confirmed-digest`) stays on every `apply`, so the rehearsal
  practises the real flow.
- **Owner.** `owner/owner-on1-approval-can-wait-2026-11-20.md`, verbatim: "the approval step can wait if autoamtic
  approval for the demo saves us time".
- **Does it save time? Yes, enough.** Rev 2 was 2.5 units in four commits; rev 3 is **2.0 units in three commits**.
  Rev 2's commit 3 (0.75: migration 0066 with two append-only tables and triggers, proposals, approval inside
  sign-in, two answer fields, the guard edit, five tests) is replaced by 0.25 (one service method, one store method
  reusing the registered grant insert, one check step, four tests). Beyond the units: no new alembic head while other
  lanes migrate, no change to 3C0a's sign-in (a protected seam with its own regression), a smaller discovery review,
  and the executive never signs in this fortnight, so RC7 ("the executive does not sign in") holds whole instead of
  with rev 2's exception. The cost moves, it does not vanish: `ON1b` is 0.75 unit (D-ON1.16), so building both
  costs 0.25 more than rev 2. That trade is right because ON1 sits on lane A's path to `DDR` (`two-week-build-plan.md`
  §0.1 rows 6 and 14) and no real export is planned this fortnight (§ "No real export yet"), so `ON1b` is off the
  critical path until a DPA is in sight. Had the saving been 0.25 or less, option A would have been kept as built.
- **OD-14, said plainly.** For **real** operators OD-14 is unchanged: no real file can be applied, so no role on a
  real operator's data is granted by anyone but, later, its executive (`ON1b`). For **emulated** tenants (the
  rehearsal's Lakeside, fictional people, never an operator database) this design **departs from OD-14**: the
  command grants the roles, as D-ON1.3 would have, recorded `by_service service:onboarding` so the record says so.
  OD-14 exists so an operator's executive controls who sees the operator's data; an emulated tenant has no operator
  and no real data, and the owner allowed automatic approval "for the demo". The owner's decision OD-14 itself is not
  changed.
- **Why nobody can self-grant on real data.** An emulated file cannot reach an operator database: `emulated` with the
  switch on is `ONBOARD_DATA_MISMATCH`, and 3A2's settings (through RC4-F1) refuse an `assetops_op_` database with
  the switch off. A real file is refused before any write. So the analyst who runs `apply` can grant themselves a
  role only on an emulated tenant in a non-operator database. **Residual (W5 probe):** a person who labels a real
  operator's file `emulated` and loads it into a non-operator database gets automatic grants; that act already
  breaks RC4 (real data outside its own database, before a DPA), which no code can see, and is named in the runbook.
  Under rev 2 the same mislabelled file still needed the executive's sign-in; the class is the RC4 breach, not the
  grant.
- **Rejected.** Real files grant only the executive and the executive grants the rest through 3C0a's grant API:
  no new code, but it puts curl in an executive's hands (the reason D-ON1.3 gave) and the grant API does not enforce
  the separation (queue Q5), so "no person holds both" would rest on a reader of the runbook. Refusing real files
  keeps both guarantees in code.

## D-ON1.16 Queued unit `ON1b`: the executive approves roles at sign-in (owner option A), for real operators

- **Ruling.** `ON1b` is queued, **0.75 unit, one commit**, one migration (the next free number at build time): rev 2's
  §3.3 proposal design as written in `spec.md` rev 2 (git `9630dbc1e`, §3.3, §4 rows for `accounts_api.py`, the
  guard and messages, §6 service 3 and 11, Postgres 1, 3 and 4), applied to **real files only**: `check` step 3a
  becomes "propose", the approval rides on sign-in with the confirmed digest, D-ON1.9's words. Emulated files stay
  automatic (D-ON1.15). It also restores the real-operator runbook steps (rev 2's steps 1 to 9; the settings test's
  list grows back to rev 2's 13 lines less the rehearsal's `uvicorn`, 12) and the executive's one sign-in, RC7's
  exception.
- **When.** Before the first real operator is onboarded: it is built as soon as a signed DPA is in sight, and the
  coordinator creates no `assetops_op_` database before it merges. It has its own handshake and a discovery review
  (OD-14 seam). Spec: written from rev 2's text when queued work is pulled; no new design is needed.
- **Why.** The owner's answer A stands as the rule for real data; only its timing moves. Keeping the design whole in
  rev 2's text makes the deferral cheap to undo.
