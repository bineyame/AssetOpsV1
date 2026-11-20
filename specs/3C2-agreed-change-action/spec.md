# 3C2: the agreed change recorded as an Action (implementer spec)

Status: rev 1, Architect (Claude), 2026-11-20. Handshake not started (`handshake.md`). Lane C (`two-week-build-plan.md`
§0.2, days 5 and 6). **1.5 units.** Discovery review (W5): a new schema and a person rule. `USER_REVIEW_REQUIRED:
false` (no screen; 5c shows the Action).
- **What it is.** RC9: the first change agreed at the end of the deep-dive is recorded by people as an Action with its
  owner and due date; the product does not value it this fortnight. 3C2 builds that record, the command that writes
  it in the agreeing person's name, the read 5c's "Actions in hand" shows, and the role rules.
- **Binding on it:** 5c spec §4.3 (rev 2), the contract: the `record_action` command line and a read of every agreed
  Action of the tenant, newest first, with names and state words (D-5C.8, D-5C.17).
- **Builds on (merged on `main`):** `3C0a` (`AccountService.onboard_person`, `OnboardPerson`; `ledger_append_only()`
  of 0005), `3A6` (`AccountService.tenant_by_slug`, D-3A6.17), `3C1a` (`accounts/permissions.py` `COMMAND_ROLES`, `roles_of`),
  `3B1` (`structure.registry.REGISTRIES`), `3A7` (migration `0068_commercial_reconciliation`, which 0069 follows).
- **Not the S6-01a Actions.** The existing `actions/` store holds verification Actions opened from Findings by the
  SYSTEM demonstration actor (`actions/lifecycle.py`). They have no person who agreed them, no owner and no due date,
  and are never read here (D-3C2.1).
- **Decisions:** `rulings.md` (D-3C2.1 to D-3C2.5). **Reviewer guide:** `reviewer-guide.md`.

## 0. Before you start

- Branch `task/3C2-agreed-action` off `main` after 3A6 and 3A7 have merged (migration order, `tenant_by_slug`); worktree
  `/opt/assetecon/AssetOpsV1-3c2`. Start when the handshake has no open question. Unit 2 starts when unit 1 and 5c's
  unit 2 have both merged.
- **Read:** `rulings.md`; 3C0a `spec.md` §2 (the 0062 table style), §3 ("Who did it"), §4.1; 3A3 `spec.md` §2.6
  step 5 and §2.7 (the command's person step); `accounts/permissions.py`; 5c `spec.md` §3 (`AgreedAction`) and §4.3;
  `tools/checks/configuration-persistence.ps1:951-990` (the writer blocks).
- **Databases:** `*_test` only, through `tools/heavy-slot.sh --db -- <command>`. Never ports 5490 or 8990, the
  walkthrough database or Docker.
- **Collisions.** New: `backend/migrations/versions/0069_agreed_action.py`, `backend/assetops_backend/actions/agreed.py`,
  `actions/adapters/postgres_agreed_action_store.py`, `actions/agreed_composition.py`,
  `backend/assetops_backend/record_action.py`, the two test files. Edited: `accounts/permissions.py` (one line),
  `tools/checks/configuration-persistence.ps1` (one writer block). Unit 2: `deep_dive/actions.py` (one class),
  `deep_dive/composition.py` (one line), `backend/tests/test_5c_deep_dive_postgres.py` (case 9(d)).

## 1. Outcome and why

After the deep-dive the executive and their team agree one change ("Lower the generator stop setting at Kobo to 70%
battery charge"), who owns it and by when. The analyst records it with one command in the executive's name; it is kept
as written, never edited, and 5c's "Actions in hand" shows it with "Owner Peter · due 15 December 2026" and "Agreed by
Amina on 20 November 2026". Past its due date it reads "Overdue". Nothing values it (RC9).

Gate questions: can only the operator's executive agree a change, and only a person whose role covers the Site own
it? Does a re-run of the same command record nothing new? Does the screen's read list only agreed Actions, newest
first, with the people's names?

## 2. Unit 1: the record, the store, the command

### 2.1 Migration `0069_agreed_action` (revises `0068_commercial_reconciliation`)

The 0062 style: one raw `UPGRADE` string through `op.execute`; no column defaults (the adapter writes every value).

```sql
CREATE TABLE agreed_action (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant (id),
    title text NOT NULL CHECK (char_length(title) BETWEEN 1 AND 200 AND title = btrim(title)),
    site_id uuid NULL,
    factor_id text NULL CHECK (factor_id IS NULL OR factor_id ~ '^[a-z][a-z0-9_]{0,63}$'),
    owner_person_id uuid NOT NULL,
    created_by_person_id uuid NOT NULL,
    created_role text NOT NULL CHECK (created_role = 'OPERATOR_EXECUTIVE'),
    created_by_script boolean NOT NULL,
    created_at timestamptz NOT NULL,
    due_on date NOT NULL,
    origin text NOT NULL CHECK (origin = 'DEEP_DIVE'),
    FOREIGN KEY (tenant_id, owner_person_id) REFERENCES operator_account (tenant_id, id),
    FOREIGN KEY (tenant_id, created_by_person_id) REFERENCES operator_account (tenant_id, id),
    FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id),
    CHECK (factor_id IS NULL OR site_id IS NOT NULL),
    CHECK (due_on >= (created_at AT TIME ZONE 'UTC')::date)
);
CREATE UNIQUE INDEX agreed_action_once ON agreed_action
    (tenant_id, created_by_person_id, owner_person_id, title, due_on, site_id, factor_id) NULLS NOT DISTINCT;
CREATE INDEX agreed_action_tenant ON agreed_action (tenant_id, created_at DESC, id DESC);
CREATE TRIGGER agreed_action_immutable BEFORE UPDATE OR DELETE ON agreed_action
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
```
Downgrade: `LOCK TABLE agreed_action IN ACCESS EXCLUSIVE MODE`; refuse with `RAISE EXCEPTION 'Downgrade of
0069_agreed_action refused: agreed Actions exist'` when a row exists; then drop the trigger, the indexes and the table
(never `ledger_append_only()`).

### 2.2 `actions/agreed.py` (pure apart from the injected store and accounts)

```python
ORIGIN = "DEEP_DIVE"
COMMAND = "action.agree"                       # accounts/permissions.py: "action.agree": (EXECUTIVE,)
TITLE_MAX = 200
STATE_OPEN, STATE_OVERDUE = "Open", "Overdue"

@dataclass(frozen=True)
class AgreedActionRow:      # one agreed_action row, as written
    id: UUID; tenant_id: UUID; title: str; site_id: UUID | None; factor_id: str | None
    owner_person_id: UUID; created_by_person_id: UUID; created_role: str; created_by_script: bool
    created_at: datetime; due_on: date; origin: str
@dataclass(frozen=True)
class AgreedActionView:     # one row as a reader sees it (names joined)
    action_id: UUID; title: str; site_code: str | None; factor_id: str | None
    owner_name: str; created_by_name: str; created_at: datetime; due_on: date; state_words: str
@dataclass(frozen=True)
class Recorded:
    row: AgreedActionRow; view: AgreedActionView; already_recorded: bool
class AgreedActionRefused(Exception):  # .code, .exit (2 or 3)

class AgreedActionStore(Protocol):
    def site_id(self, tenant_id: UUID, site_code: str) -> UUID | None: ...
    def add(self, row: AgreedActionRow) -> tuple[AgreedActionRow, bool]: ...   # (stored, already_recorded)
    def for_tenant(self, tenant_id: UUID) -> tuple[tuple[AgreedActionRow, str | None, str, str], ...]:
        ...   # (row, site_code, owner display name, creator display name), newest first by (created_at, id)

def state_words(due_on: date, today: date) -> str   # STATE_OVERDUE when due_on < today, else STATE_OPEN

class AgreedActionService:
    def __init__(self, store: AgreedActionStore, accounts: AccountService, *, clock: Callable[[], datetime],
                 new_id: Callable[[], UUID] = uuid4) -> None
    def record(self, *, tenant_slug: str, as_email: str, title: str, owner_email: str, due_on: date,
               site_code: str | None, factor_id: str | None) -> Recorded
    def for_tenant(self, tenant_id: UUID) -> tuple[AgreedActionView, ...]   # newest first; state by clock's UTC date
```
`MemoryAgreedActionStore` (in `agreed.py`, used by unit tests) re-implements `add`'s identity rule and the newest-first
order.

### 2.3 The rules of `record` (D-3C2.2; checked in this order, the first that fails refuses)

1. `title.strip()` (the stored title) empty, over 200 characters, or holding a character below U+0020: `BAD_TITLE`.
2. `accounts.tenant_by_slug(tenant_slug)` None: `UNKNOWN_TENANT`.
3. The creator: `accounts.onboard_person(as_email)` None, of another tenant (`tenant_slug` differs) or not active:
   `PERSON_NOT_FOUND`. The first of `roles_of("action.agree")` the creator holds (any Site): none is
   `PERSON_ROLE_REQUIRED`; that role is `created_role`.
4. `site_code` given and `store.site_id(tenant_id, site_code)` None: `SITE_NOT_FOUND`.
5. `factor_id` given without `site_code`: `FACTOR_NEEDS_SITE`; given and not a factor id of any registry in
   `REGISTRIES` (`any(r.factor_id == f for reg in REGISTRIES.values() for r in reg.rows)`): `FACTOR_UNKNOWN`.
6. The owner: `accounts.onboard_person(owner_email)` None, of another tenant or not active: `OWNER_NOT_FOUND`. Scope:
   with a Site, the owner holds `("SITE_MANAGER", that site_id)` or any role other than SITE_MANAGER; without one, any
   role other than SITE_MANAGER. Otherwise `OWNER_SCOPE`. The owner may be the creator.
7. `due_on < clock()`'s UTC date: `DUE_IN_PAST`.
8. `store.add(AgreedActionRow(new_id(), tenant_id, title, site_id, factor_id, owner, creator, created_role, True,
   clock(), due_on, ORIGIN))`. A store error is `ACTIONS_UNAVAILABLE` (exit 3).

`add` (D-3C2.3): one transaction under `SELECT pg_advisory_xact_lock(hashtextextended('agreed_action:' ||
CAST(:tenant_id AS text), 0))`; a row with the same `(tenant_id, created_by_person_id, owner_person_id, title, due_on,
site_id, factor_id)` is returned with `True` and nothing is written; else one plain `INSERT INTO agreed_action (...)
VALUES (...)` and the row with `False`.

### 2.4 The adapter (`actions/adapters/postgres_agreed_action_store.py`)

SQLAlchemy `text()` statements, as the account store. `site_id`: `SELECT id FROM site WHERE tenant_id = :t AND
site_code_key = lower(:c)`. `for_tenant`: one `SELECT` of `agreed_action a` joined to `operator_account o` (owner) and
`operator_account c` (creator) on `(tenant_id, id)`, left-joined to `site s` on `(tenant_id, id)`, `WHERE a.tenant_id
= :t ORDER BY a.created_at DESC, a.id DESC`. It reads no other table (never `action`, `action_event` or any S6-01a
table). `dispose()` disposes its engine. `actions/agreed_composition.py`: `build_agreed_actions(database_url) ->
AgreedActionsService(service, dispose)`, where `service` is an `AgreedActionService` over this adapter and
`accounts.composition.build_account_service(url)`; the only importer of the adapter.

### 2.5 The command (`python -m assetops_backend.record_action`)

`build_parser()` public; `main(argv, *, services=None, clock=None) -> int` (tests inject both; `clock` defaults to
UTC now). Arguments: `--tenant SLUG --as EMAIL --title TEXT --owner EMAIL --due YYYY-MM-DD [--site CODE] [--factor
ID]`, all as the 5c contract. Steps: `--due` not fullmatching `[0-9]{4}-[0-9]{2}-[0-9]{2}` or not a date: `BAD_DUE`;
no `DATABASE_URL` (and no injected services): `NO_DATABASE`; compose `build_agreed_actions(url)` (an error:
`ACTIONS_UNAVAILABLE`, exit 3); `service.record(...)`; dispose. A refusal prints `<CODE> <sentence>` on stderr through
`sys.stderr.write` and exits 2 (3 for `ACTIONS_UNAVAILABLE`). Success prints one JSON line on stdout and exits 0,
keys in this order:

`{"action_id", "title", "site_code", "factor_id", "owner", "created_by", "created_role", "created_by_script",
"created_at", "due_on", "state", "already_recorded"}` with names (never emails), `created_at` ISO with `Z`, `due_on`
ISO date, `state` the state words at `clock()`.

**Sentences** (exact): `BAD_TITLE` "Write a title of 1 to 200 characters." · `UNKNOWN_TENANT` "No operator has that
name." · `PERSON_NOT_FOUND` "The person agreeing is not an active person of this operator." · `PERSON_ROLE_REQUIRED`
"Only the operator's executive records an agreed change." · `SITE_NOT_FOUND` "This operator has no Site with that
code." · `FACTOR_NEEDS_SITE` "Name the Site the factor belongs to (--site)." · `FACTOR_UNKNOWN` "No factor has that
name." · `OWNER_NOT_FOUND` "The owner is not an active person of this operator." · `OWNER_SCOPE` "The owner's role
does not cover where this change applies." · `DUE_IN_PAST` "The due date is before today." · `BAD_DUE` "Write the due
date as YYYY-MM-DD, like 2026-12-15." · `NO_DATABASE` "Set DATABASE_URL to the operator's database." ·
`ACTIONS_UNAVAILABLE` "The Actions store cannot be reached right now."

### 2.6 The guard

`tools/checks/configuration-persistence.ps1` gains a writer block as 3C0a's: `postgres_agreed_action_store.py` is the
sole runtime writer of `agreed_action`, with exactly one shape, a plain `INSERT INTO agreed_action (...) VALUES (...)`
(no `ON CONFLICT`, no `SELECT` source); the advisory-lock and identity `SELECT`s are reads; the shape keeps one owner
statement (anti-vacuity). Shown failing once on a scratch copy with `UPDATE agreed_action SET title = :t` added to the
adapter, and once with an `INSERT INTO agreed_action` in another module.

## 3. Unit 2: connecting 5c (after 5c unit 2 and unit 1 have merged)

- `deep_dive/actions.py` gains `StoreAgreedActions(service)`: `for_tenant(tenant_id)` returns `AgreedActions(True,
  tuple(AgreedAction(str(v.action_id), v.title, v.site_code, v.factor_id, v.owner_name, v.created_by_name,
  v.created_at, v.due_on, v.state_words) for v in service.for_tenant(tenant_id)))` (order kept: newest first).
- `deep_dive/composition.py`: `NotConnectedActions()` becomes `StoreAgreedActions(build_agreed_actions(url).service)`
  (its `dispose` joins the composition's).
- 5c test 9(d) (§5).

## 4. Fixtures (hand-written; the tests write these literals, W2)

**People** (unit tests: 3C0a's in-memory store and `AccountService`; Postgres: ON1's `onboard_operator apply` with
`backend/tests/fixtures/on1/lakeside-power.onboarding.json`): tenant `lakeside-power`; Amina OPERATOR_EXECUTIVE;
Joseph FINANCE_AND_COMMERCIAL_LEAD; Wanjiru ANALYST; Peter SITE_MANAGER KOBO-001; Halima SITE_MANAGER KISIWA-001.
A second tenant `other-op` with one executive, Zara (unit tests only). Clock 2026-11-20T09:30:00Z; `new_id` gives
`UUID(int=1)`, `UUID(int=2)`, … .

**R1** `--tenant lakeside-power --as amina@lakeside-power.example --title "Lower the generator stop setting at Kobo to
70% battery charge" --owner peter@lakeside-power.example --due 2026-12-15 --site KOBO-001 --factor candidate_l`: exit
0, stdout `{"action_id": "00000000-0000-0000-0000-000000000001", "title": "Lower the generator stop setting at Kobo to
70% battery charge", "site_code": "KOBO-001", "factor_id": "candidate_l", "owner": "Peter", "created_by": "Amina",
"created_role": "OPERATOR_EXECUTIVE", "created_by_script": true, "created_at": "2026-11-20T09:30:00Z", "due_on":
"2026-12-15", "state": "Open", "already_recorded": false}`. **R1 again:** the same line with `"already_recorded":
true`; one row.

**Refusals** (each R1 with one change; exit 2; stderr code first): `--as joseph@…` PERSON_ROLE_REQUIRED; `--as peter@…`
PERSON_ROLE_REQUIRED; `--as nobody@lakeside-power.example` PERSON_NOT_FOUND; `--as zara@other-op.example`
PERSON_NOT_FOUND; `--owner halima@…` OWNER_SCOPE; R1 without `--site` and `--factor`, owner Peter: OWNER_SCOPE; without
`--site`, with `--factor`: FACTOR_NEEDS_SITE; `--factor nonsense` FACTOR_UNKNOWN; `--site NOPE-001` SITE_NOT_FOUND;
`--owner zara@other-op.example` OWNER_NOT_FOUND; `--due 2026-11-19` DUE_IN_PAST; `--due 15/12/2026` BAD_DUE; `--title
"  "` and a 201-character title BAD_TITLE; `--tenant nope` UNKNOWN_TENANT; no `DATABASE_URL`, no services
NO_DATABASE. **Accepted:** R1 without `--site` and `--factor`, owner Joseph (tenant-wide): exit 0, `site_code` null;
R1 with owner Amina (the creator): exit 0; R1 with `--due 2026-11-20` (today): exit 0.

**Read** (memory): R1 (09:30Z), then "Change B" (10:00Z, owner Joseph, due 2026-11-30, no Site) and "Change C" (10:30Z,
owner Peter, due 2026-12-01, KOBO-001): `for_tenant` gives C, B, R1's; with the clock at 2026-12-01T00:00Z their state
words are "Open", "Overdue", "Open" (C due that day is open; B due 30 November is overdue).

## 5. Tests (written first)

**No database** (`backend/tests/test_3c2_agreed_actions.py`):
1. R1 and R1 again: the JSON lines exactly; one stored row.
2. Every refusal and every accepted case of §4, each its own case (code, exit and sentence).
3. The read: order, names and state words of §4; `state_words(2026-12-15, 2026-12-15)` "Open", `(…, 2026-12-16)`
   "Overdue".
4. `roles_of("action.agree") == ("OPERATOR_EXECUTIVE",)`.
5. Grep: `actions/agreed.py` imports no adapter and nothing from `actions/service.py`, `lifecycle.py` or
   `verification*.py`; only `agreed_composition.py` imports the adapter; the adapter's SQL names no table but
   `agreed_action`, `operator_account` and `site`.

**Postgres** (pooled `--db`; `backend/tests/test_3c2_agreed_actions_postgres.py`):
6. The chain link `("0069_agreed_action", "0068_commercial_reconciliation")`; an `UPDATE` and a `DELETE` on a row raise
   (the trigger); an owner of another tenant violates the foreign key; `due_on` before the created day violates the
   check; `factor_id` without `site_id` violates the check; downgrade with a row raises its sentence.
7. On ON1's Lakeside tenant: R1 through `main` exits 0 with §4's line (clock injected, ids from the database row: the
   test compares every key but `action_id`); R1 again `already_recorded` true and one row; two threads running R1 at
   once leave one row.
8. `build_agreed_actions(url).service.for_tenant` gives §4's read order and names after the three records.

**Unit 2** (in `backend/tests/test_5c_deep_dive_postgres.py`):
9. 5c test 9(d): after 5c's 9(c), the Lakeside people onboarded into that test's tenant, R1 recorded at
   2026-11-20T09:30Z through `main`; the body's `actions` equals 5c §3.5 World C's (`connected` true, one row, text
   null, more 0).

**Regression:** `test_3c0a_*`, `test_3c1_*`, the S6-01a action tests (`test_s6_action_*`), and once unit 2 lands the 5c
tests; the persistence guard; check-all once at the end; `select-tests` before review.

## 6. Done (questions; each can fail)

1. Does R1 record one agreed Action with Amina as creator, Peter as owner, due 15 December 2026, and print §4's line?
2. Does a re-run record nothing new and say so?
3. Is every refusal of §4 given with its code and sentence, and only the executive able to agree a change?
4. Can only a person whose role covers the Action's Site (or the whole operator) own it?
5. Is the record append-only (trigger) and written only by its adapter (the guard, shown failing)?
6. Does the read list only agreed Actions, newest first, with names and "Open" or "Overdue"?
7. After unit 2, does 5c's screen show World C's row from the database?
8. Does each planted violation in the reviewer guide fail its named test, and is the mid-build count 0?

Packet: `specs/3C2-agreed-change-action/packet.md` (the mid-build count).

## 7. Out of scope

Closing, completing, reassigning or re-dating an Action (3C3, with the screen controls); valuing the change (RC9;
`6a`); owners and due dates on the S6-01a finding Actions (queued `3C2b`, next fortnight; D-3C2.1); an HTTP route
(the analyst records by command; 3C3 adds the screen); notifications.

## 8. Units

| Unit | Content | Needs | Commits |
|---|---|---|---|
| 1 (1.25) | §2: migration, model, memory store, adapter, service, command, permission line, guard block; tests 1 to 8; check-all; packet | 3A6 and 3A7 merged | 1 to 2 |
| 2 (0.25) | §3: `StoreAgreedActions`, the composition line; test 9 | unit 1 and 5c unit 2 merged | 1 |

## 9. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 (owner) | Who may record an agreed change | The operator's executive only (D-3C2.2); the finance lead and Site managers own changes but do not agree them for the operator |
| Q2 (owner) | May the analyst type the agreed change in the executive's name? | Yes, as 3A7 Q1: `created_by_script` true, the runbook says the executive agreed it in the meeting; a person records it on screen once 3C3 lands |
| Q3 (owner) | Owners and due dates on the existing finding Actions | Not this fortnight: queued `3C2b` (the delivery plan's 2.5-unit 3C2 is cut to the deep-dive's record, 1.5 units; D-3C2.1) |
| Q4 | "Overdue" by which day | The UTC date at the read; a Site's own timezone when 3C3 adds the screen |
