# ON1 rulings

Architect (Claude), 2026-11-20. Each ruling is applied by `spec.md` rev 1. D-ON1.7 settles the 3A2 review's residual
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

## D-ON1.3 Roles from the file at onboarding only; then the executive grants (refines D-3C0A.7)

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
