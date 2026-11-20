# 3C0a reviewer guide

For the fresh Reviewer, first at the handshake (read `spec.md`, `rulings.md` and this guide; put questions in
`handshake.md`) and then at the review of the built unit. Review depth: discovery (W5): a new schema, a security
mechanism and the seam `3C1` builds on.

## What to check first

1. **Scope.** `git diff --stat main...HEAD` shows only: `backend/migrations/versions/0062_operator_accounts.py`,
   `backend/assetops_backend/accounts/**`, `backend/assetops_backend/accounts_api.py`, the `create_app` keyword and
   router line in `main.py`, the `# 3C0a` block in `i18n/messages.py`, the five `backend/tests/test_3c0a_*.py` files,
   the guard block in `tools/checks/configuration-persistence.ps1`, and the packet. Any other file is a finding.
2. **No behaviour change.** No existing route, dependency, middleware or command module changes (D-3C0A.1). Diff
   `main.py` line by line.
3. **The migration** is the spec §2 SQL, character for character apart from formatting, plus the five triggers and the
   0061-style downgrade.

## Done means

- Spec §10's seven questions are each answered yes with real output in the packet: the focused files, the pooled
  Postgres files (through `tools/heavy-slot.sh`), check-all, `select-tests` output, and the two planted guard failures.
- The packet says the full suite was not run while building and why (spec §9).

## Probes

- **P1 Enumeration.** Compare the 401 bodies and headers for an unknown email and a wrong password: identical. Check
  the code path runs `verify_password` with `DUMMY_HASH` for the unknown email.
- **P2 Lockout.** Five failures, then a sixth: 429 with minutes; no attempt row written for the sixth; works after the
  window. The count is per email key, case-insensitive.
- **P3 Cookie.** `Set-Cookie` holds `HttpOnly`, `SameSite=Strict`, `Path=/api`, `Max-Age=43200`, and `Secure` unless
  `ASSETOPS_SESSION_COOKIE_SECURE=off`. The raw token is never stored (grep the adapter: only `token_sha256`).
- **P4 Tenant isolation.** An executive of tenant A granting to a person of tenant B, or naming B's Site or B's grant:
  404, and no row written.
- **P5 Last executive under concurrency.** Run the two-thread test five times; never zero executives.
- **P6 Database enforcement.** With the service bypassed (raw SQL in a test), UPDATE and DELETE on the five append-only
  tables fail; a session UPDATE that changes anything but `revoked_at` fails; a mismatched removal fails.
- **P7 Derived state.** Grant, remove, grant again the same role: two GRANTED rows, one REMOVED; `resolve` holds the
  role; the record lists three rows newest first.
- **P8 Guard.** The planted `UPDATE role_grant` and a second writer module both fail
  `configuration-persistence.ps1`; the packet shows the output.
- **P9 Words.** Every refusal code of spec §5 has its `accounts.*` key and the English text, character for character.

## Class sweeps (W6)

- A refusal missing its words: check all fifteen codes, not only the one found.
- A table missing its trigger: check all six tables' triggers in `pg_trigger`.
- A route accepting an unknown key: check all four POST routes.

## Risks to keep in view

- `3C1` will switch refusals on; check nothing here already refuses an existing command.
- The `Secure` cookie over the walkthrough's plain-http address is `3C0b`'s question (decision queue Q4); note it, do
  not block on it.
