# 3C0a rulings

Architect (Claude), 2026-11-20. Each ruling has its reason. Index lines: `.ai/decisions/index-rulings-7.md`. Handshake
answers go below under "Handshake answers (round 1)" and are folded into `spec.md`.

## D-3C0A.1 Accounts behind the API now; the screens and the refusal later

- **Ruling.** This unit adds accounts, sessions, role grants and their routes. It changes no existing route and
  refuses no existing command.
- **Why.** The owner started non-screen work and held screens (20 Nov). If commands were refused without a person
  before a sign-in page exists, today's screens would stop working. `3C1` records the person; the refusal switches on
  with `3C0b`'s sign-in page (D-BW1.3).

## D-3C0A.2 Every record is a row; current state is derived

- **Ruling.** Accounts, credentials, statuses, grants and attempts are append-only (the 0005 trigger). Only a session's
  `revoked_at` may be set, once. Current password, status and held grants are the latest rows.
- **Why.** OD-14 asks that every grant and removal be on record with its person and time; `decision-loop-specification.md`
  §8 makes `role_grant` append-only with "a removal is a new row". Applying the same rule to credentials and
  statuses gives one rule for the whole unit, and an auditor can see every change. A session is not a record of a
  decision; making it revoke-only keeps sign-out simple without allowing any other edit.

## D-3C0A.3 Email is unique across all tenants

- **Ruling.** `email_key` is globally unique; sign-in takes email and password, no tenant.
- **Why.** "One set of accounts per operator" (OD-13) is kept: each account belongs to one tenant. A global key
  removes a tenant field from sign-in, which the operator's people should not have to know. A person who works for
  two operators uses two emails; that is rare before SaaS scale and can be revisited with single sign-on.

## D-3C0A.4 Role codes are the manifest's; only the Site manager carries a Site

- **Ruling.** `OPERATOR_EXECUTIVE`, `FINANCE_AND_COMMERCIAL_LEAD`, `SITE_MANAGER`, `FIELD_TECHNICIAN`, `ANALYST`.
  `SITE_MANAGER` requires a Site; the others must not have one.
- **Why.** The manifest's `demo_workflow.tenants[].people` already uses these codes, and only Site managers carry a
  Site there. `decision-loop-specification.md` §8 says "Site where the role is Site-bound", and its permission table
  binds only the Site manager's choices to a Site. No other role exists: no Admin, no Viewer.

## D-3C0A.5 The tenant keeps one executive

- **Ruling.** A removal that would leave no ACTIVE account holding `OPERATOR_EXECUTIVE` is refused, under a per-tenant
  advisory lock with the check inside the transaction.
- **Why.** Only the executive grants roles (OD-14). With none left, nobody could grant again except by the onboarding
  command, so the rule prevents a locked-out operator. The lock makes two simultaneous removals safe.

## D-3C0A.6 One refusal for every failed sign-in, with a dummy hash and a lockout

- **Ruling.** Unknown email, wrong password, disabled account and missing credential give the same 401 body; the
  unknown-email path still runs scrypt; five failures in fifteen minutes lock the email key.
- **Why.** Telling them apart, by words or by timing, would tell an outsider which emails have accounts. The lockout
  bounds password guessing. The parameters are conventional and are revisited at the pilot (decision queue Q3).

## D-3C0A.7 The onboarding command creates people; only the first executive gets a role from it

- **Ruling.** `create --executive` grants `OPERATOR_EXECUTIVE` by `service:onboarding`, and only when the tenant has
  none. Every other grant comes from the executive through the API.
- **Why.** "The first executive of a tenant is created when the operator is onboarded" (`decision-loop-specification.md`
  §8); OD-14 says roles are granted and removed by the executive. Creating an account is not granting a role, so
  the command may create the others' accounts without breaking OD-14.

## D-3C0A.8 The demo people's accounts are not this unit's

- **Ruling.** Seeding Amina, Joseph, Peter and the others into the walkthrough database is done when that database is
  built (`WK`), after `3C0b`.
- **Why.** Their accounts need emails and passwords the manifest does not hold, and a walkthrough sign-in needs the
  sign-in page. Seeding them now would be data no screen can use.

## D-3C0A.9 The seam `3C1` uses is `accounts.principal.person_from_request`

- **Ruling.** One function turns a request into a `PersonPrincipal` or `None`, reading the `assetops_session` cookie.
- **Why.** Every command module today takes an injected principal (`mini_decision_principal`, `domain_work_principal`,
  `operational_entry_principal` in `create_app`). `3C1` replaces those injections with this one function; naming it
  now keeps `3C1` from reaching into the store.

## D-3C0A.10 Standard-library scrypt, no new dependency

- **Ruling.** `hashlib.scrypt` with n = 32768, r = 8, p = 1, a 16-byte salt and a 32-byte key, in a self-describing
  string.
- **Why.** No password library is in `backend/pyproject.toml`, and adding one needs the coordinator's dependency
  change in every worktree (`frontend/node_modules` precedent, lane rules). scrypt is memory-hard and in the standard
  library. Measured 0.13 s per hash on this machine (20 Nov), acceptable for sign-in. The parameters are in the
  stored string, so a later change verifies old hashes.
