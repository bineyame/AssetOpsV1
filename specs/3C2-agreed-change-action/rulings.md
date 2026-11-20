# 3C2 rulings

Architect (Claude), 2026-11-20. Each ruling is indexed in `.ai/decisions/index-rulings-13.md`. Handshake answers go
below, under "Handshake answers (round 1)".

## D-3C2.1 An agreed change is its own append-only record, apart from the finding Actions

- **Ruling.** `agreed_action` (migration 0069) holds the change people agreed, its creator, owner and due date, written
  once and never edited (`ledger_append_only()`). The S6-01a Actions (verification plans opened from Findings by the
  SYSTEM demonstration actor) are not touched and never read by the deep-dive. Owners and due dates on those are
  queued as `3C2b`.
- **Why.** RC9 asks for one thing this fortnight: the agreed change with its owner and due date. The S6-01a Action is
  a different construct (no person agreed it; its lifecycle is APPLY and OBSERVE on a Site's Foundation); widening
  its table would put a person rule into a reviewed lifecycle under deadline. One name, two records, kept apart: the
  screen says "Agreed by" only where a person agreed. The delivery plan's 2.5-unit 3C2 is cut to 1.5 units on that
  basis (owner queue Q3).

## D-3C2.2 Only the executive agrees a change; the owner's role must cover where it applies

- **Ruling.** `action.agree` is `(OPERATOR_EXECUTIVE,)`. The owner is an active person of the tenant who holds the
  Site's SITE_MANAGER grant or any tenant-wide role; with no Site, a tenant-wide role. Amina agrees; Peter (Site
  manager of KOBO-001) owns a Kobo change, not a Mto one or an operator-wide one.
- **Why.** RC9's change is agreed at the end of the deep-dive with the executive, who answers for the operator.
  3C1's rule binds a Site manager to their Site (R5e) and lets other roles act at every Site; an owner who cannot
  act where the change applies could not carry it out.

## D-3C2.3 The command records in the agreeing person's name, once

- **Ruling.** `record_action --as` names the executive; the row stores `created_by_script` true. A re-run with the
  same creator, owner, title, due date, Site and factor returns the stored Action (`already_recorded` true) and writes
  nothing, under a per-tenant advisory lock; the unique index is the backstop.
- **Why.** 3A7's pattern (the finance lead's figures recorded by command in their name, D-3A7, Q1), so the record says
  who agreed, not who typed. A command retried after a lost connection must not create a second Action.

## D-3C2.4 State words are "Open" and "Overdue", by the UTC date at the read

- **Ruling.** `Overdue` when the due date is before the read's UTC date, else `Open`. No closing in this unit.
- **Why.** The delivery plan: "overdue computed as for maintenance schedules"; closing needs the screen controls
  (3C3). A state that is computed is never stored, so it cannot go stale.

## D-3C2.5 3C2 adopts 5c's contract; the domain read stays in `actions/`, the screen's mapping in `deep_dive/`

- **Ruling.** The command line and the read (every agreed Action of the tenant, newest first, names and state words)
  are 5c §4.3's. `actions/agreed.py` gives `AgreedActionView`s; `deep_dive/actions.py` maps them to 5c's
  `AgreedAction` (unit 2, after both merge). DDR's G10 reads the store through `build_agreed_actions`.
- **Why.** The dependency runs from the screen to the domain, never back; 3C2 unit 1 can merge before 5c exists, and
  the one-line connection lands when both do (D-5C.8).
