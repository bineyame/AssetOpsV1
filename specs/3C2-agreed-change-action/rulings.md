# 3C2 rulings

Architect (Claude), 2026-11-20 (rev 2 after handshake round 1). Each ruling is indexed in `.ai/decisions/index-rulings-13.md`. Handshake answers go
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

*Amended by D-3C2.6 (handshake R5, P4): the owner's cover is the `OWNER_COVER` table, not "any tenant-wide role".*

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

## D-3C2.14 The state words and refusal sentences are SC-1 statements, written after SC-1a merges (D-SC1.28)

Decided 2026-11-21 on the owner's behalf (`specs/OWNER-AWAY/decisions-2026-11-21.md`, row 2).

- **Ruling.** Gate A is unchanged and code starts on it. Commit 1 builds §2 with no served text: `STATE_OPEN,
  STATE_OVERDUE` become the codes `"OPEN"`, `"OVERDUE"` (`state_code(due_on, today)`, the same rule as
  `state_words`); every refusal is its code and exit code; tests 1 to 8 assert codes, exits and stored rows. Commit 2,
  after SC-1a merges and `main` is merged in: vocabulary `action_state` (`OPEN` → "Open", `OVERDUE` → "Overdue") and
  `i18n/statements/en/agreed_action.py` with one statement `agreed_action.refused.<code in lower case>` per §4
  refusal, carrying §4's exact sentence (reworded only where D-SC1.21 forbids a number word; any name, date or count
  through a slot); `state_words` and the stderr sentence render those statements; the success line's `state` is the
  rendered word; `actions/agreed.py` joins `ADOPTED`; the exact-string assertions of tests 2 and 3 land here. The 5c
  contract (`AgreedAction.state_words: str`) is unchanged. The epilog is static chrome (SC-1 §3.8 (g)).
- **Merge order.** 3A7 merges before 3C2; 3C2 renumbers on 3A7's migration at gate B, as §0 provides.
- **Why.** "Open" and "Overdue" reach the deep-dive screen; written as constants they are the hand-built words the
  owner ruled out. The non-text work is most of the unit, so it builds now.
- **Reverse.** Withdraw with D-SC1.28: commit 1's codes stay, and the words are written in `agreed.py` as §2.2 had them.

## Handshake answers (round 1)

Architect (Claude), 2026-11-20, on `handshake.md` round 1 (R1 to R15, P1 to P11). Spec moves to rev 2. New rulings
D-3C2.6 to D-3C2.13 follow the answers; D-3C2.2 is amended by D-3C2.6. Every gate named below has a plant in the
reviewer guide (rev 2) that fails it.

### Highs

- **P1 (migration order). Accepted as a hard gate, with D-3A1.12's numbering instead of a fixed parent (D-3C2.9).**
  The migration is `00NN_agreed_action`, NN the next number on `main`'s live head. Gate A (build start): the builder
  records `git show main:backend/migrations/versions/` and the head's `revision`; the file, `revision` and
  `down_revision` take that head. Gate B (merge preparation): if `main`'s head moved, renumber on top of it (file name,
  `revision`, `down_revision`, the hand pair of test 6) and run `alembic heads` (one head). Test 6 asserts both: the
  hand pair written at gate A and `down_revision` equal to the previous module's `revision` read from the files.
  3C2 does not wait for 3A7 or 3B7a: it needs neither one's code, and waiting buys only a fixed name. A renumber is
  logged in the packet; it is not a mid-build question. Rev 1's `0069 revises 0068` is the expected outcome only if
  3B7a, 3A6 and 3A7 all merge first.
- **P2 (`tenant_by_slug`). The dependency is stated; no edit to `accounts/service.py`.** D-3A6.17 rules
  `AccountService.tenant_by_slug(slug) -> UUID | None`; 3A6 builds it. Gate A also requires 3A6 merged: `git grep -n
  "def tenant_by_slug" main -- backend/assetops_backend/accounts/service.py` shows one line. 3C2 adding the same
  method would give two definitions at merge. Step 2 uses the returned UUID; the slug compared in step 3 is the
  argument.
- **R1 (retry after the due day). The identity read moves before the due check (D-3C2.7).** After the rights steps
  (1 to 6), `store.find(tenant_id, key)` reads the stored row; found, `record` returns it with `already_recorded` true
  and the state at the call's clock, and never reaches `DUE_IN_PAST`. Rights are still checked on every run: a re-run
  after the owner lost the Site is `OWNER_SCOPE`, not "already recorded". §4 gains: R1 at 2026-11-20T09:30Z, then R1
  with the clock at 2026-12-16T08:00Z: exit 0, `already_recorded` true, `created_at` "2026-11-20T09:30:00Z", `state`
  "Overdue"; and R1 alone at 2026-12-16T08:00Z: `DUE_IN_PAST`. Plant P23 (find after the due check) fails test 2.
- **R3 (index backstop). The adapter catches the unique violation on `agreed_action_once` (D-3C2.7).** On
  `sqlalchemy.exc.IntegrityError` whose `orig.diag.constraint_name == "agreed_action_once"`, the adapter rolls back,
  reads the row by the key in a new transaction and returns `(stored, True)`; any other error propagates (the service
  maps it to `ACTIONS_UNAVAILABLE`). Test 7 now tells the two apart: 7b (catch) opens its own connection, inserts R1's
  row without the lock and holds the transaction open; in a thread calls `adapter.add` (its lookup misses the
  uncommitted row; its INSERT waits on the index); polls `pg_locks` until that backend waits (`granted = false`, 5 s
  limit); commits; the thread returns `(row, True)` with the test's id. 7c (lock) takes `pg_advisory_xact_lock` on the
  tenant's key on its own connection, calls `adapter.add` in a thread, asserts within 5 s that the thread waits on an
  `advisory` lock, commits, and the thread returns `False` with one row. Plant P24 (catch removed) fails 7b; P25 (lock
  removed) fails 7c. The two-thread `main` case (7a) stays as the end-to-end check.

### Rights (R2, R4, R5, P4)

- **R2. Stated plainly (D-3C2.12).** `record_action` is not a sign-in. It reads no password, session or token; `--as`
  names the person the record is attributed to, and `created_by_script` true says a script typed it. Anyone with the
  database URL can attribute a change to the executive; that is the analyst's trusted act (Q2), and the packet lists it
  as residual risk `R-AUTH`, never as "authenticated". Inactive cases join §4: Fatuma, an OPERATOR_EXECUTIVE set
  DISABLED (`onboard_set_status(email, "DISABLED", None)`), as `--as` gives `PERSON_NOT_FOUND`, as `--owner`
  `OWNER_NOT_FOUND`. Plant P22 (`active` ignored) fails both.
- **R5 and P4 (owner scope). Ruled by role, not by "tenant-wide" (D-3C2.6, amending D-3C2.2).** Only SITE_MANAGER
  grants carry a Site in `role_grant`, so "any other role" let the analyst and the field technician own any Site's
  change. The owner rule is one literal table, `OWNER_COVER`: OPERATOR_EXECUTIVE and FINANCE_AND_COMMERCIAL_LEAD
  cover every Site and the whole operator; SITE_MANAGER covers only the Site of that grant, never the whole operator;
  ANALYST, FIELD_TECHNICIAN and any role not in the table cover nothing. An owner passes when one held grant covers.
  So Peter owns a Kobo change, not a Mto change and not an operator-wide one; David owns Mto's; Joseph and Amina own
  any; Wanjiru and Musa own none. §4 gains each of those cases. Plant P17 (rev 1's rule: any role but SITE_MANAGER
  covers all) fails the Wanjiru and Musa cases; P18 (the SITE_MANAGER grant matched by role name, not Site) fails
  `--site MTO-001 --owner peter`.
- **R4 (factor of the wrong Site type). The factor must belong to the Site type's registry (D-3C2.8).** The store's
  Site lookup returns `(site_id, site_type)`; the registry is `REGISTRIES.get(SITE_TYPE_TO_STRUCTURE.get(site_type))`
  (`structure/read.py`, reused). A factor in no registry is `FACTOR_UNKNOWN`; in some registry but not this Site's
  (including a Site type with no registry yet) is the new `FACTOR_SITE_TYPE` "This factor does not apply to that
  Site's type." The unit fixture adds FRIDGE-001 (COLDCHAIN) to Lakeside in the memory store only; R1 with `--site
  FRIDGE-001` refuses `FACTOR_SITE_TYPE`. Plant P26 (any-registry membership, rev 1) fails it.
- **P3 (verified).** Agreed; nothing to rule.

### R8 to R13

- **R8. Accepted.** Every refusal case asserts stdout `""`, stderr exactly `"CODE sentence\n"`, and no `@` in either.
- **R9. Accepted, with ids inserted out of order.** §4's read adds "Change D" and "Change E", both at 11:00Z, recorded
  E first with `UUID(int=5)`, then D with `UUID(int=4)` (`new_id` yields 1, 2, 3, 5, 4). Expected order: E, D, C, B,
  R1's. Insertion order would put D first, so a wrong tie rule fails. Plant P19 (`id ASC` or insertion order on a tie)
  fails tests 3 and 8.
- **R10 (RC9, nothing valued). Accepted.** Test 1 asserts the twelve keys of §2.5 exactly, in order. Test 5 greps the
  migration file and the adapter's SQL, case-insensitive, for `\b(commercial_\w+|value|amount|currency|price|cost|
  money)\b` and finds none (`VALUES` does not match `\bvalue\b`). Plant P11 (a `value` key in the line) fails test 1;
  P20 (a `value numeric` column) fails test 5.
- **R11. Accepted.** P7 fails test 6 on UPDATE and on DELETE, each asserted. P10: the packet records the guard's exit
  code and message for each failing run. Added: P12 (`created_role` taken from the owner) fails test 1 when the owner
  is Joseph (`created_role` must still read OPERATOR_EXECUTIVE; §4's accepted case asserts it); P13 (scope checked
  against the creator) fails `--owner halima` (Amina's grant would cover); P14 (steps 4 and 6 swapped) fails the new
  two-fault case `--site NOPE-001 --owner zara@other-op.example`: `SITE_NOT_FOUND`; P15 (`agreed.py` imports
  `actions.service`) fails test 5.
- **R12. Accepted.** Test 5 extracts table names from the adapter's SQL strings with
  `(?i)\b(?:FROM|JOIN|INTO|UPDATE)\s+([a-z_][a-z0-9_]*)` and asserts the set is a subset of `{"agreed_action",
  "operator_account", "site"}` (whole names, not substrings), plus no match of `\baction\b` or `\baction_event\b`
  anywhere in the adapter. Plant P8 (`... UNION SELECT ... FROM action`) fails it.
- **R13 (separation on the screen side). Met by a check that can fail, not by an S6-01a Action in 9(d).** Opening a
  real S6-01a Action needs a Finding, its revision, an assessment and a Foundation revision on 5c's test tenant
  (0016's five foreign keys); 5c's World A tenant has none, and building that chain in 9(d) is a test of S6-01a, not
  of the screen. The screen's only input is `service.for_tenant`, so the failure to guard against is a second source
  wired in. Test 9(e) (no database) greps `deep_dive/actions.py` and `deep_dive/composition.py`: the only imports
  from `assetops_backend.actions` are `actions.agreed` and `actions.agreed_composition`, and `StoreAgreedActions.
  __init__` takes exactly one parameter. Plant P16 (`StoreAgreedActions` also given `build_action_service`) fails
  9(e). If the owner wants the live S6-01a row in 9(d) as well, it is a 0.25-unit addition (queue Q6).

### Smaller

- **P5 (TRUNCATE). Closed, not left as residual risk (D-3C2.13).** 0050's precedent:
  `CREATE TRIGGER agreed_action_no_truncate BEFORE TRUNCATE ON agreed_action FOR EACH STATEMENT EXECUTE FUNCTION
  ledger_append_only();` Downgrade drops it. Test 6 asserts TRUNCATE raises; plant P21 (left out) fails it.
- **R7 and P9 (clock). One read per call, whole seconds (D-3C2.10).** `record` and `for_tenant` each call `clock()`
  once; `now = clock().astimezone(timezone.utc).replace(microsecond=0)`; a naive datetime raises `ValueError`
  (a programming error, not a refusal). `now` serves the due check, `created_at` and `state`. The stored and printed
  `created_at` are equal; printed `YYYY-MM-DDTHH:MM:SSZ`. §4 gains: clock 2026-11-20T09:30:00.654321Z prints and
  stores 09:30:00Z (test 7 reads the column); R1 again at 10:00Z prints `created_at` 09:30:00Z. Plant P27 (a second
  clock read for `state`) fails the case with a clock that returns 2026-11-20T09:30Z first and 2026-12-16T00:00Z after (state must read "Open").
- **R6 (title). No normalisation; controls refused; spaces stripped as `btrim` does (D-3C2.11).** Stored title =
  `title.strip(" ")` (U+0020 only, as `btrim`). `BAD_TITLE` when it is empty, over 200 code points, holds any
  character of Unicode category Cc, Cf, Zl or Zp (tab, U+0085, U+200B, U+2028 among them), or starts or ends with a
  character for which `str.isspace()` is true (NBSP, U+2003). No NFC: the identity is the stored code points. §4
  gains: `"Title\twith tab"`, `"Title two"`, `" Title"` BAD_TITLE; a 200-character title accepted; R1's
  title with two spaces on each side gives `already_recorded` true after R1.
- **R14 (UTC against Kobo's UTC+3). Accepted for this fortnight; the sentence lives in two places.** D-3C2.4 and the
  command's `--help` epilog: "Overdue counts from the day after the due date, by the UTC calendar." From 21:00Z on
  the due day a Kobo change already reads Overdue three hours late; 3C3 moves to the Site's timezone (queue Q4).
- **R15.** Answered by P1: §0 and §8 name gate A and gate B, not a fixed parent.
- **P6, P7 (verified).** Agreed.
- **P8 (unit 2 ground). Hard gate C:** unit 2 starts only when `git ls-tree main
  backend/assetops_backend/deep_dive/actions.py` shows the file and it defines `NotConnectedActions`, and unit 1 has
  merged. DDR G10's use (`build_agreed_actions(url).service.for_tenant(tenant)[0]`) fixes the names kept in rev 2.
- **P10.** (a) Yes: test 7 reads `id` with a `SELECT` on the row, not from the output. (b) MTO-001 and David are in
  ON1's fixture; the Mto cases are added (unit tests use the same people in memory, plus Fatuma, Zara and FRIDGE-001).
  (c) Test 7a runs two `main` calls, each composing its own engine; 7b and 7c use the test's own connection plus the
  adapter's engine. No pool-size rule is needed.
- **P11.** Rev 2 answers P1 and P2; the build starts at gate A with mid-build count 0.

## D-3C2.6 The owner rule is one table by role; a Site manager covers only their Site (amends D-3C2.2)

- **Ruling.** `OWNER_COVER = {OPERATOR_EXECUTIVE: "ALL", FINANCE_AND_COMMERCIAL_LEAD: "ALL", SITE_MANAGER: "SITE"}`
  in `actions/agreed.py`. "ALL" covers every Site and the operator-wide change; "SITE" covers a change at the grant's
  own Site only. ANALYST, FIELD_TECHNICIAN and any unlisted role own nothing. The owner passes when any held grant
  covers. Peter owns Kobo's change, not Mto's.
- **Why.** `role_grant` binds a Site only to SITE_MANAGER, so rev 1's "any other role" was not a scope at all: the
  analyst and the technician owned changes everywhere. The owner of an agreed change answers to the executive for
  carrying it out; the analyst prepares and verifies, the technician works under a Site manager's case. Executive and
  finance lead answer operator-wide. An explicit table makes a new role own nothing until a ruling adds it.

## D-3C2.7 A re-run is recognised before the due check; the unique index is caught, not fatal

- **Ruling.** After the rights steps, `store.find` returns an existing row as `already_recorded`; only then is the
  due date checked. The adapter catches the violation of `agreed_action_once`, reads the stored row and returns it.
- **Why.** A retry after a lost connection is the case idempotency exists for; refusing it because a day passed
  breaks D-3C2.3. The index is the backstop the lock cannot be: a writer that skips the lock must still meet "once".

## D-3C2.8 A factor must belong to the registry of its Site's type

- **Ruling.** `FACTOR_UNKNOWN` when no registry has the factor; `FACTOR_SITE_TYPE` when the Site's type has no
  registry or its registry lacks the factor. The mapping is `structure/read.py`'s `SITE_TYPE_TO_STRUCTURE`.
- **Why.** 5c shows "Site and factor" together; a mini-grid factor on a cold room would be a statement the product
  cannot stand behind. Reusing the one mapping keeps the rule right when 3B6 adds cold chain and EV.

## D-3C2.9 The migration takes the next number at the live head; 3A6 merged is the build gate

- **Ruling.** D-3A1.12 applies: `00NN_agreed_action` on `main`'s head at gate A, renumbered at gate B if the head
  moved; tests check the hand pair and the module chain. Gate A also needs 3A6 merged (`tenant_by_slug`). Unit 2's
  gate C is 5c unit 2 and 3C2 unit 1 merged. 3C2 does not wait for 3A7 or 3B7a.
- **Why.** A fixed parent across four unmerged lanes either blocks the lane or breaks `alembic heads`; the house rule
  already solves it. The only code 3C2 borrows from an unmerged lane is 3A6's method.

## D-3C2.10 One clock read per call, whole seconds

- **Ruling.** `record` and `for_tenant` read `clock()` once, in UTC, microseconds dropped; that value serves the due
  check, `created_at` and the state words. A re-run prints the stored `created_at`.
- **Why.** Three reads can straddle midnight and disagree; a stored value with microseconds would not equal the
  printed one, and the screen shows whole times.

## D-3C2.11 The title is kept as typed: spaces stripped, controls refused, no normalisation

- **Ruling.** Strip U+0020 only (as `btrim`); refuse Cc, Cf, Zl and Zp characters and a title starting or ending in
  other white space; no Unicode normalisation; the identity is the stored code points.
- **Why.** The service and the database check must agree on one rule, and an invisible character in a title would
  make two Actions look like one on screen.

## D-3C2.12 `record_action` is a trusted act, not a sign-in

- **Ruling.** The command reads no credential. `--as` attributes; `created_by_script` true marks the typing. The
  packet carries residual risk `R-AUTH`. A signed-in path arrives with 3C3's screen.
- **Why.** Q2's default: the analyst records what the executive agreed in the meeting. Calling it authenticated would
  be false; saying so keeps the record honest about how it was made.

## D-3C2.13 TRUNCATE on `agreed_action` is refused

- **Ruling.** A statement-level `BEFORE TRUNCATE` trigger calls `ledger_append_only()`, as 0050 does for
  `chain_input_change`.
- **Why.** Row triggers do not stop TRUNCATE; an append-only record with one open door is not append-only, and the
  fix is one line with a precedent.

## Mid-build answers

## D-3C2.15 The agreed-action composition lives in `actions/composition.py`; `agreed_composition.py` only re-exports (MB1)

- **Ruling.** Alternative B. `build_agreed_actions` and `AgreedActionsService` move into `actions/composition.py`
  (appended after S6-01a's code, calling none of it, no import-time effect); `actions/agreed_composition.py` becomes
  two re-export lines and imports no adapter. The persistence guard needs no change for this: `actions/composition.py`
  is already the package's one admitted adapter importer. Test 5 reads: only `actions/composition.py` imports the
  agreed adapter; `agreed_composition.py` imports no adapter and defines nothing else. DDR G10's
  `build_agreed_actions(url).service.for_tenant(tenant)[0]`, `record_action`'s import and test 9(e) are unchanged.
- **Why.** The guard's rule is one composition root per package; A would widen a held guard rule to fit one file,
  B keeps the rule and leaves the owner one question (the writer block). Costs weighed, none a design problem: the
  edit touches an S6-01a file by appending only (no open `task/*` branch edits it); importing the composition also
  loads S6-01a modules (imports only, no call, no cycle: `actions/` imports nothing from `deep_dive/`); agreed and
  S6-01a code share a file, kept apart by the block boundary and by `agreed.py` importing nothing from S6-01a (test 5).
- **Writer block.** `42de02e06` is independent of MB1 and still needed; it stays held for the owner (owner-away
  row 5). With B the guard is green on the adapter-import line without any change.
- **Code change that follows (builder, 3C2 branch).** Move the two definitions; make `agreed_composition.py`
  re-exports; retarget test 5's importer set to `{"actions/composition.py"}` plus the two assertions above.
