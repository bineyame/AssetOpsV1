# 3C0a mid-build questions (RULES §4 item 7)

A question about something the spec did not fix stops only the affected part. Write it here (Q1, Q2 ...): the
section, what is stopped, what is built, and what you ask. The Architect rules in `rulings.md`. Record the count in
the packet; a count above zero is a spec-template defect to fix.

Count: **2** (Q1, Q2 in the build branch; answered in `rulings.md`, "Mid-build answers").

## Q1 (§3 Session, §4.1 port, R8): the port cannot see a session's age against the latest password (answered: MB1)

- **Section.** §3 "a session is valid while ... its `created_at` is not before the latest credential's `set_at`"
  (R8); §4.2 `resolve`; §4.1 port.
- **The gap.** The port gives `session(token_sha256) -> (id, tenant, person, expires, revoked)` (no `created_at`)
  and `current_credential(person_id) -> str | None` (the hash, no `set_at`). The service therefore cannot compare
  the two. Closing it needs either a changed port signature (for example `session` also returning `created_at`
  and a credential read returning `set_at`) or the rule moved into the store's `session` read. Both are port
  design, which the spec fixes.
- **Stopped (until MB1/MB2; now built).** Only the R8 condition in `AccountService.resolve`. Its service test
  (`test_resolve_none_after_a_later_password`) is written and marked `xfail(strict=True)` naming Q1.
- **Built.** Everything else in `resolve` (expiry, revocation, ACTIVE status, roles read at each call).
- **Asked.** Which port shape carries `created_at` and `set_at` (or is the condition the store's)?

## Q2 (§4.2, §5 sign-in and `/me` bodies): no port or service path gives the tenant's slug and name, or `/me`'s expiry (answered: MB2)

- **Section.** §5: sign-in and `GET /api/auth/me` answer `{"person", "tenant": {"slug", "name"},
  "session_expires_at"}`.
- **The gap.** (a) The port has `tenant_by_slug(slug)` but nothing from a tenant id to its slug and name, and
  neither `SignedIn` nor `PersonPrincipal` carries them. (b) For `/me`, `resolve` returns a `PersonPrincipal`
  (no expiry); the session's `expires` is read by the port but the service contract drops it.
- **Stopped (until MB1/MB2; now built).** The `tenant` object and `/me`'s `session_expires_at` in those two bodies.
- **Built.** Both routes: the cookie, every refusal, `person` (from `people`), sign-in's `session_expires_at`.
- **Asked.** Which port method gives a tenant's slug and name by id (for example `tenant(tenant_id) -> (slug, name)
  | None`), and how does `/me` learn the session's expiry (a principal field, or a service read by token)?
