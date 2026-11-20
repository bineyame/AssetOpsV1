# 3C2: the agreed change recorded as an Action (implementer spec)

Status: rev 2, Architect (Claude), 2026-11-20, after handshake round 1 (`handshake.md`; answers in `rulings.md`
"Handshake answers (round 1)"). Lane C (`two-week-build-plan.md` §0.2, days 5 and 6). **1.5 units.** Discovery review
(W5): a new schema and a person rule. `USER_REVIEW_REQUIRED: false` (no screen; 5c shows the Action).
- **What it is.** RC9: the first change agreed at the end of the deep-dive is recorded by people as an Action with its
  owner and due date; the product does not value it this fortnight. 3C2 builds that record, the command that writes
  it in the agreeing person's name, the read 5c's "Actions in hand" shows, and the role rules.
- **Binding on it:** 5c spec §4.3 (rev 2), the contract: the `record_action` command line and a read of every agreed
  Action of the tenant, newest first, with names and state words (D-5C.8, D-5C.17). DDR G10 calls
  `build_agreed_actions(url).service.for_tenant(tenant)[0]`; those names are fixed.
- **Builds on (merged on `main`):** `3C0a` (`AccountService.onboard_person`, `OnboardPerson`; `ledger_append_only()`
  of 0005), `3A6` (`AccountService.tenant_by_slug`, D-3A6.17; **must be merged, gate A**), `3C1a`
  (`accounts/permissions.py` `COMMAND_ROLES`, `roles_of`), `3B1` (`structure.registry.REGISTRIES`),
  `structure/read.py` (`SITE_TYPE_TO_STRUCTURE`).
- **Not the S6-01a Actions.** The existing `actions/` store holds verification Actions opened from Findings by the
  SYSTEM demonstration actor (`actions/lifecycle.py`). They have no person who agreed them, no owner and no due date,
  and are never read here (D-3C2.1).
- **Decisions:** `rulings.md` (D-3C2.1 to D-3C2.13; D-3C2.2 amended by D-3C2.6). **Reviewer guide:**
  `reviewer-guide.md` (rev 2).

## 0. Before you start (gates; each is a hard stop, not a note)

- **Gate A (unit 1 build start).** (1) 3A6 merged: `git grep -n "def tenant_by_slug" main --
  backend/assetops_backend/accounts/service.py` shows one line. (2) The migration number: read `main`'s head
  (`git show main:backend/migrations/versions/`, the highest file and its `revision`); the new file is
  `00NN_agreed_action.py`, NN the next number, `revision = "00NN_agreed_action"`, `down_revision` that head (D-3C2.9,
  D-3A1.12). Write the head and NN in the packet. If 3B7a, 3A6 and 3A7 have all merged, this is `0069` on
  `0068_commercial_reconciliation`. 3C2 does not wait for 3A7 or 3B7a. Below, `00NN` means that number.
- **Gate B (merge preparation).** If `main`'s head moved since gate A, renumber on top of it (file name, `revision`,
  `down_revision`, test 6's hand pair) and run `alembic heads` (one head). Log it in the packet; it is not a mid-build
  question.
- **Gate C (unit 2 start).** Unit 1 merged, and `git ls-tree main backend/assetops_backend/deep_dive/actions.py` shows
  the file defining `NotConnectedActions` (5c unit 2 merged).
- Branch `task/3C2-agreed-action` off `main` at gate A; worktree `/opt/assetecon/AssetOpsV1-3c2`. Start when the
  handshake has no open question.
- **Read:** `rulings.md`; 3C0a `spec.md` §2 (the 0062 table style), §3 ("Who did it"), §4.1; 3A3 `spec.md` §2.6
  step 5 and §2.7 (the command's person step); `accounts/permissions.py`; 5c `spec.md` §3 (`AgreedAction`) and §4.3;
  `tools/checks/configuration-persistence.ps1:951-990` (the writer blocks); `0050_chain_response_expiry.py` (the
  TRUNCATE trigger).
- **Databases:** `*_test` only, through `tools/heavy-slot.sh --db -- <command>`. Never ports 5490 or 8990, the
  walkthrough database or Docker.
- **Collisions.** New: `backend/migrations/versions/00NN_agreed_action.py`, `backend/assetops_backend/actions/agreed.py`,
  `actions/adapters/postgres_agreed_action_store.py`, `actions/agreed_composition.py`,
  `backend/assetops_backend/record_action.py`, the two test files. Edited: `accounts/permissions.py` (one line),
  `tools/checks/configuration-persistence.ps1` (one writer block). Nothing else, `accounts/service.py` included.
  Unit 2: `deep_dive/actions.py` (one class), `deep_dive/composition.py` (one line),
  `backend/tests/test_5c_deep_dive_postgres.py` (case 9(d)), `backend/tests/test_3c2_agreed_actions.py` (case 9(e)).

## 1. Outcome and why

After the deep-dive the executive and their team agree one change ("Lower the generator stop setting at Kobo to 70%
battery charge"), who owns it and by when. The analyst records it with one command in the executive's name; it is kept
as written, never edited, and 5c's "Actions in hand" shows it with "Owner Peter · due 15 December 2026" and "Agreed by
Amina on 20 November 2026". Past its due date it reads "Overdue". Nothing values it (RC9).

Gate questions: can only the operator's executive agree a change, and only a person whose role covers the Site own
it (Peter owns Kobo's, not Mto's)? Does a re-run of the same command record nothing new, even after the due date? Does
the screen's read list only agreed Actions, newest first, with the people's names?

**What the command is not.** `record_action` is the analyst's trusted act, not a sign-in: it reads no password,
session or token; `--as` names the person the record is attributed to and `created_by_script` true says a script typed
it (D-3C2.12). The packet lists this as residual risk `R-AUTH`.

## 2. Unit 1: the record, the store, the command

### 2.1 Migration `00NN_agreed_action` (revises the head at gate A)

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
    created_at timestamptz NOT NULL
        CHECK (date_trunc('second', created_at AT TIME ZONE 'UTC') = created_at AT TIME ZONE 'UTC'),
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
CREATE TRIGGER agreed_action_no_truncate BEFORE TRUNCATE ON agreed_action
    FOR EACH STATEMENT EXECUTE FUNCTION ledger_append_only();
```
Downgrade: `LOCK TABLE agreed_action IN ACCESS EXCLUSIVE MODE`; refuse with `RAISE EXCEPTION 'Downgrade of
00NN_agreed_action refused: agreed Actions exist'` when a row exists; then drop both triggers, the indexes and the
table (never `ledger_append_only()`).

### 2.2 `actions/agreed.py` (pure apart from the injected store and accounts)

```python
ORIGIN = "DEEP_DIVE"
COMMAND = "action.agree"                       # accounts/permissions.py: "action.agree": (EXECUTIVE,)
TITLE_MAX = 200
STATE_OPEN, STATE_OVERDUE = "Open", "Overdue"
COVER_ALL, COVER_SITE = "ALL", "SITE"
#: D-3C2.6: the owner's cover by role; a role not listed owns nothing.
OWNER_COVER: Mapping[str, str] = MappingProxyType({
    "OPERATOR_EXECUTIVE": COVER_ALL, "FINANCE_AND_COMMERCIAL_LEAD": COVER_ALL, "SITE_MANAGER": COVER_SITE})
TITLE_REFUSED_CATEGORIES = frozenset({"Cc", "Cf", "Zl", "Zp"})

@dataclass(frozen=True)
class IdentityKey:          # the fields of agreed_action_once, tenant apart
    created_by_person_id: UUID; owner_person_id: UUID; title: str; due_on: date
    site_id: UUID | None; factor_id: str | None
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
    def site(self, tenant_id: UUID, site_code: str) -> tuple[UUID, str, str] | None: ...  # (id, site_type, site_code)
    def find(self, tenant_id: UUID, key: IdentityKey) -> AgreedActionRow | None: ...
    def add(self, row: AgreedActionRow) -> tuple[AgreedActionRow, bool]: ...   # (stored, already_recorded)
    def for_tenant(self, tenant_id: UUID) -> tuple[tuple[AgreedActionRow, str | None, str, str], ...]:
        ...   # (row, site_code, owner display name, creator display name), newest first by (created_at, id)

def state_words(due_on: date, today: date) -> str   # STATE_OVERDUE when due_on < today, else STATE_OPEN
def clean_title(title: str) -> str | None            # §2.3 step 1; None is BAD_TITLE
def owner_covers(roles: frozenset[tuple[str, UUID | None]], site_id: UUID | None) -> bool   # D-3C2.6

class AgreedActionService:
    def __init__(self, store: AgreedActionStore, accounts: AccountService, *, clock: Callable[[], datetime],
                 new_id: Callable[[], UUID] = uuid4) -> None
    def record(self, *, tenant_slug: str, as_email: str, title: str, owner_email: str, due_on: date,
               site_code: str | None, factor_id: str | None) -> Recorded
    def for_tenant(self, tenant_id: UUID) -> tuple[AgreedActionView, ...]   # newest first; one clock read
```
`owner_covers`: true when some held `(role, grant_site)` has `OWNER_COVER.get(role) == COVER_ALL`, or
`OWNER_COVER.get(role) == COVER_SITE` and `site_id is not None` and `grant_site == site_id`.
`MemoryAgreedActionStore` (in `agreed.py`, used by unit tests) holds Sites as `(tenant_id, code, site_type)` and
re-implements `find`, `add`'s identity rule and the newest-first order `(created_at, id)` descending.

**The clock (D-3C2.10).** `record` and `for_tenant` each call `clock()` exactly once:
`now = clock().astimezone(timezone.utc).replace(microsecond=0)` (a naive datetime raises `ValueError`, a programming
error). `now` serves step 8, `created_at` and the state words; `today = now.date()`. `main` never calls `clock` itself.

### 2.3 The rules of `record` (D-3C2.2 as amended; checked in this order, the first that fails refuses)

1. `clean_title(title)` (D-3C2.11): `t = title.strip(" ")` (U+0020 only, as `btrim`); `BAD_TITLE` when `t` is
   empty, `len(t) > 200`, any character has `unicodedata.category(c)` in `TITLE_REFUSED_CATEGORIES`, or `t[0]` or
   `t[-1]` is white space (`str.isspace()`). No Unicode normalisation; `t` is the stored title and the identity.
2. `tenant_id = accounts.tenant_by_slug(tenant_slug)`; None: `UNKNOWN_TENANT`.
3. The creator: `accounts.onboard_person(as_email)` None, `tenant_slug` differs from the argument, or not `active`:
   `PERSON_NOT_FOUND`. The first of `roles_of("action.agree")` the creator holds (any Site): none is
   `PERSON_ROLE_REQUIRED`; that role is `created_role`.
4. `site_code` given and `store.site(tenant_id, site_code)` None: `SITE_NOT_FOUND`.
5. The factor (D-3C2.8): given without `site_code`: `FACTOR_NEEDS_SITE`; in no registry of `REGISTRIES`:
   `FACTOR_UNKNOWN`; else `registry = REGISTRIES.get(SITE_TYPE_TO_STRUCTURE.get(site_type, ""))` is None or holds no
   row with that `factor_id`: `FACTOR_SITE_TYPE`.
6. The owner: `accounts.onboard_person(owner_email)` None, of another tenant or not `active`: `OWNER_NOT_FOUND`;
   `owner_covers(owner.roles, site_id)` false: `OWNER_SCOPE`. The owner may be the creator.
7. The re-run (D-3C2.7): `store.find(tenant_id, IdentityKey(creator, owner, t, due_on, site_id, factor_id))` found:
   return `Recorded(stored, view at today, True)`. Nothing is written and step 8 is not reached.
8. `due_on < today`: `DUE_IN_PAST`.
9. `store.add(AgreedActionRow(new_id(), tenant_id, t, site_id, factor_id, owner, creator, created_role, True, now,
   due_on, ORIGIN))`; its bool is `already_recorded`. A store error in steps 4, 7 or 9 is `ACTIONS_UNAVAILABLE`
   (exit 3).

Rights are checked on every run: a re-run after the owner lost the Site's grant is `OWNER_SCOPE`.

`add` (D-3C2.3, D-3C2.7): one transaction under `SELECT pg_advisory_xact_lock(hashtextextended('agreed_action:' ||
CAST(:tenant_id AS text), 0))`; a row with the same `(tenant_id, created_by_person_id, owner_person_id, title, due_on,
site_id, factor_id)` (compared with `IS NOT DISTINCT FROM` for the two nullable columns) is returned with `True` and
nothing is written; else one plain `INSERT INTO agreed_action (...) VALUES (...)` and the row with `False`. On
`sqlalchemy.exc.IntegrityError` whose `orig.diag.constraint_name == "agreed_action_once"`: roll back, read the row by
the key in a new transaction, return `(stored, True)`. Any other error propagates.

### 2.4 The adapter (`actions/adapters/postgres_agreed_action_store.py`)

SQLAlchemy `text()` statements, as the account store. `site`: `SELECT id, site_type, site_code FROM site WHERE
tenant_id = :t AND site_code_key = lower(:c)`. `find`: one `SELECT` of `agreed_action` by tenant and the key.
`for_tenant`: one `SELECT` of `agreed_action a` joined to `operator_account o` (owner) and `operator_account c`
(creator) on `(tenant_id, id)`, left-joined to `site s` on `(tenant_id, id)`, `WHERE a.tenant_id = :t ORDER BY
a.created_at DESC, a.id DESC`. It reads no other table (never `action`, `action_event` or any S6-01a table).
`dispose()` disposes its engine. `actions/agreed_composition.py`: `build_agreed_actions(database_url) ->
AgreedActionsService(service, dispose)`, where `service` is an `AgreedActionService` over this adapter and
`accounts.composition.build_account_service(url)`, clock UTC now; the only importer of the adapter.

### 2.5 The command (`python -m assetops_backend.record_action`)

`build_parser()` public, with the epilog "Overdue counts from the day after the due date, by the UTC calendar."
(R14); `main(argv, *, services=None, clock=None) -> int` (tests inject both; `clock` defaults to UTC now). Arguments:
`--tenant SLUG --as EMAIL --title TEXT --owner EMAIL --due YYYY-MM-DD [--site CODE] [--factor ID]`, all as the 5c
contract. Steps: `--due` not fullmatching `[0-9]{4}-[0-9]{2}-[0-9]{2}` or not a date: `BAD_DUE`; no `DATABASE_URL`
(and no injected services): `NO_DATABASE`; compose `build_agreed_actions(url)` (an error: `ACTIONS_UNAVAILABLE`,
exit 3); `service.record(...)`; dispose. A refusal writes exactly `<CODE> <sentence>\n` to stderr through
`sys.stderr.write`, nothing to stdout, and exits 2 (3 for `ACTIONS_UNAVAILABLE`). Success prints one JSON line on
stdout and exits 0, exactly these twelve keys in this order:

`{"action_id", "title", "site_code", "factor_id", "owner", "created_by", "created_role", "created_by_script",
"created_at", "due_on", "state", "already_recorded"}` with names (never emails), `created_at` the stored value as
`YYYY-MM-DDTHH:MM:SSZ`, `due_on` ISO date, `state` the state words at the call's one clock read. No value, money or
amount key (RC9).

**Sentences** (exact): `BAD_TITLE` "Write a title of 1 to 200 characters." · `UNKNOWN_TENANT` "No operator has that
name." · `PERSON_NOT_FOUND` "The person agreeing is not an active person of this operator." · `PERSON_ROLE_REQUIRED`
"Only the operator's executive records an agreed change." · `SITE_NOT_FOUND` "This operator has no Site with that
code." · `FACTOR_NEEDS_SITE` "Name the Site the factor belongs to (--site)." · `FACTOR_UNKNOWN` "No factor has that
name." · `FACTOR_SITE_TYPE` "This factor does not apply to that Site's type." · `OWNER_NOT_FOUND` "The owner is not
an active person of this operator." · `OWNER_SCOPE` "The owner's role does not cover where this change applies." ·
`DUE_IN_PAST` "The due date is before today." · `BAD_DUE` "Write the due date as YYYY-MM-DD, like 2026-12-15." ·
`NO_DATABASE` "Set DATABASE_URL to the operator's database." · `ACTIONS_UNAVAILABLE` "The Actions store cannot be
reached right now."

### 2.6 The guard

`tools/checks/configuration-persistence.ps1` gains a writer block as 3C0a's: `postgres_agreed_action_store.py` is the
sole runtime writer of `agreed_action`, with exactly one shape, a plain `INSERT INTO agreed_action (...) VALUES (...)`
(no `ON CONFLICT`, no `SELECT` source); no `UPDATE`, `DELETE` or `TRUNCATE` of it anywhere at runtime; the
advisory-lock and identity `SELECT`s are reads; the shape keeps one owner statement (anti-vacuity). Shown failing once
on a scratch copy with `UPDATE agreed_action SET title = :t` added to the adapter, and once with an `INSERT INTO
agreed_action` in another module; the packet records each run's exit code and message.

## 3. Unit 2: connecting 5c (gate C)

- `deep_dive/actions.py` gains `StoreAgreedActions(service)` (one constructor parameter): `for_tenant(tenant_id)`
  returns `AgreedActions(True, tuple(AgreedAction(str(v.action_id), v.title, v.site_code, v.factor_id, v.owner_name,
  v.created_by_name, v.created_at, v.due_on, v.state_words) for v in service.for_tenant(tenant_id)))` (order kept:
  newest first).
- `deep_dive/composition.py`: `NotConnectedActions()` becomes `StoreAgreedActions(build_agreed_actions(url).service)`
  (its `dispose` joins the composition's).
- 5c test 9(d) and 3C2 test 9(e) (§5).

## 4. Fixtures (hand-written; the tests write these literals, W2)

**People** (Postgres: ON1's `onboard_operator apply` with `backend/tests/fixtures/on1/lakeside-power.onboarding.json`;
unit tests: 3C0a's in-memory store and `AccountService` holding the same): tenant `lakeside-power`; Sites KISIWA-001,
KOBO-001, MTO-001 (MINIGRID); Amina OPERATOR_EXECUTIVE; Joseph FINANCE_AND_COMMERCIAL_LEAD; Wanjiru ANALYST; Peter
SITE_MANAGER KOBO-001; Halima SITE_MANAGER KISIWA-001; David SITE_MANAGER MTO-001; Musa FIELD_TECHNICIAN. **Unit tests
only:** Fatuma OPERATOR_EXECUTIVE of Lakeside, set DISABLED (`onboard_set_status(email, "DISABLED", None)`); Site
FRIDGE-001 (COLDCHAIN) of Lakeside in the memory store; a second tenant `other-op` with one executive, Zara. Emails are
`<name lower-case>@lakeside-power.example` (Zara: `zara@other-op.example`). Clock 2026-11-20T09:30:00Z unless a case
says otherwise; `new_id` gives `UUID(int=1)`, `UUID(int=2)`, … .

**R1** `--tenant lakeside-power --as amina@lakeside-power.example --title "Lower the generator stop setting at Kobo to
70% battery charge" --owner peter@lakeside-power.example --due 2026-12-15 --site KOBO-001 --factor candidate_l`: exit
0, stdout `{"action_id": "00000000-0000-0000-0000-000000000001", "title": "Lower the generator stop setting at Kobo to
70% battery charge", "site_code": "KOBO-001", "factor_id": "candidate_l", "owner": "Peter", "created_by": "Amina",
"created_role": "OPERATOR_EXECUTIVE", "created_by_script": true, "created_at": "2026-11-20T09:30:00Z", "due_on":
"2026-12-15", "state": "Open", "already_recorded": false}`.

**Re-runs** (each after R1; one row stays): R1 again at 09:30Z: the same line with `"already_recorded": true`. R1
again at 2026-11-20T10:00Z: the same, `created_at` still "2026-11-20T09:30:00Z". R1 again at 2026-12-16T08:00Z: exit
0, `already_recorded` true, `created_at` "2026-11-20T09:30:00Z", `state` "Overdue". R1 with the title written
`"  Lower the generator stop setting at Kobo to 70% battery charge  "`: `already_recorded` true.

**Refusals** (each R1 with the one change shown, on a store without R1; exit 2; stdout empty; stderr exactly
`CODE sentence\n`; no `@` in either):

| Change to R1 | Code |
|---|---|
| `--as joseph@…` | PERSON_ROLE_REQUIRED |
| `--as peter@…` | PERSON_ROLE_REQUIRED |
| `--as nobody@lakeside-power.example` | PERSON_NOT_FOUND |
| `--as zara@other-op.example` | PERSON_NOT_FOUND |
| `--as fatuma@…` (disabled) | PERSON_NOT_FOUND |
| `--owner halima@…` | OWNER_SCOPE |
| `--owner david@…` | OWNER_SCOPE |
| `--owner wanjiru@…` | OWNER_SCOPE |
| `--owner musa@…` | OWNER_SCOPE |
| `--site MTO-001` (owner Peter) | OWNER_SCOPE |
| no `--site`, no `--factor` (owner Peter) | OWNER_SCOPE |
| no `--site`, no `--factor`, `--owner wanjiru@…` | OWNER_SCOPE |
| `--owner zara@other-op.example` | OWNER_NOT_FOUND |
| `--owner fatuma@…` (disabled) | OWNER_NOT_FOUND |
| no `--site`, with `--factor` | FACTOR_NEEDS_SITE |
| `--factor nonsense` | FACTOR_UNKNOWN |
| `--site FRIDGE-001` | FACTOR_SITE_TYPE |
| `--site NOPE-001` | SITE_NOT_FOUND |
| `--site NOPE-001 --owner zara@other-op.example` (two faults) | SITE_NOT_FOUND |
| `--due 2026-11-19` | DUE_IN_PAST |
| clock 2026-12-16T08:00Z (no R1 stored) | DUE_IN_PAST |
| `--due 15/12/2026` | BAD_DUE |
| `--title "  "` | BAD_TITLE |
| a 201-character title | BAD_TITLE |
| `--title "Title\twith tab"` | BAD_TITLE |
| `--title "Title two"` | BAD_TITLE |
| `--title " Title"` | BAD_TITLE |
| `--tenant nope` | UNKNOWN_TENANT |
| no `DATABASE_URL`, no services | NO_DATABASE |

**Accepted** (each exit 0, `created_role` "OPERATOR_EXECUTIVE", `created_by` "Amina"): R1 with `--owner joseph@…`
(finance lead at Kobo); R1 without `--site` and `--factor`, owner Joseph (operator-wide; `site_code` null); R1 with
`--owner amina@…` (the creator); R1 with `--site MTO-001 --owner david@…`; R1 with `--due 2026-11-20` (today); a
title of exactly 200 characters; R1 with the clock 2026-11-20T09:30:00.654321Z: `created_at` "2026-11-20T09:30:00Z";
R1 with a clock that returns 2026-11-20T09:30Z on its first call and 2026-12-16T00:00Z on every later call: `state`
"Open", `created_at` "2026-11-20T09:30:00Z" (one read).

**Read** (memory; `new_id` yields 1, 2, 3, 5, 4): R1 (09:30Z, id 1), then "Change B" (10:00Z, id 2, owner Joseph, due
2026-11-30, no Site), "Change C" (10:30Z, id 3, owner Peter, due 2026-12-01, KOBO-001), "Change E" (11:00Z, id 5,
owner Joseph, due 2026-12-20, no Site), "Change D" (11:00Z, id 4, owner Joseph, due 2026-12-20, no Site):
`for_tenant` gives E, D, C, B, R1's (ids 5, 4, 3, 2, 1). With the clock at 2026-12-01T00:00Z their state words are
"Open", "Open", "Open", "Overdue", "Open" (C due that day is open; B due 30 November is overdue).

## 5. Tests (written first)

**No database** (`backend/tests/test_3c2_agreed_actions.py`):
1. R1 and every re-run of §4: the JSON lines exactly; the twelve keys exactly, in order; one stored row.
2. Every refusal and every accepted case of §4, each its own case: code, exit, exact stderr, empty stdout, no `@`.
3. The read: order, names and state words of §4; `state_words(2026-12-15, 2026-12-15)` "Open", `(…, 2026-12-16)`
   "Overdue".
4. `roles_of("action.agree") == ("OPERATOR_EXECUTIVE",)`; `OWNER_COVER` equals D-3C2.6's three entries exactly.
5. Grep: `actions/agreed.py` imports no adapter and nothing from `actions/service.py`, `lifecycle.py`,
   `verification*.py`, `ports.py` or `actions/composition.py`; only `agreed_composition.py` imports the adapter; the
   table names in the adapter's SQL strings, taken by `(?i)\b(?:FROM|JOIN|INTO|UPDATE)\s+([a-z_][a-z0-9_]*)`, are a
   subset of `{"agreed_action", "operator_account", "site"}`, and `\baction\b` and `\baction_event\b` match nowhere in
   the adapter; the migration file and the adapter's SQL match no
   `(?i)\b(commercial_\w+|value|amount|currency|price|cost|money)\b`.

**Postgres** (pooled `--db`; `backend/tests/test_3c2_agreed_actions_postgres.py`):
6. The chain: `revision`/`down_revision` equal gate A's hand pair (rev 2's expectation `("0069_agreed_action",
   "0068_commercial_reconciliation")`, renumbered with the file), and `down_revision` equals the previous module's
   `revision` read from the files. On a row: UPDATE raises, DELETE raises, TRUNCATE raises (each asserted); an owner
   of another tenant violates the foreign key; `due_on` before the created day violates the check; `factor_id`
   without `site_id` violates the check; a `created_at` with microseconds violates the check; downgrade with a row
   raises its sentence.
7. On ON1's Lakeside tenant: (a) R1 through `main` exits 0 with §4's line (clock injected; the test reads `id` with a
   `SELECT` and compares every key but `action_id`; the stored `created_at` equals 09:30:00Z); R1 again
   `already_recorded` true and one row; two threads running R1 through `main` at once leave one row, one `false` and
   one `true`. (b) The catch: the test's own connection inserts R1's row without the lock and holds the transaction;
   a thread calls `adapter.add` with an equal row; the test polls `pg_locks` until that backend waits (`granted =
   false`, 5 s limit), commits, and the thread returns `(row with the test's id, True)`. (c) The lock: the test's
   connection takes `pg_advisory_xact_lock(hashtextextended('agreed_action:' || tenant, 0))`; a thread calls
   `adapter.add`; within 5 s that backend waits on an `advisory` lock; the test commits; the thread returns `False`
   and one row exists. (d) `adapter.site(tenant, "kobo-001")` returns `(Kobo's id, "MINIGRID", "KOBO-001")`.
8. An `AgreedActionService` over the adapter (injected clock and `new_id` as §4's read) after the five records:
   `for_tenant` gives §4's order, names and state words; `build_agreed_actions(url).service.for_tenant` gives the
   same order and names.

**Unit 2:**
9. (d) In `backend/tests/test_5c_deep_dive_postgres.py`, after 5c's 9(c), the Lakeside people onboarded into that
   test's tenant, R1 recorded at 2026-11-20T09:30Z through `main`: the body's `actions` equals 5c §3.5 World C's
   (`connected` true, one row, text null, more 0). (e) In `test_3c2_agreed_actions.py` (no database): the only imports
   from `assetops_backend.actions` in `deep_dive/actions.py` and `deep_dive/composition.py` are `actions.agreed` and
   `actions.agreed_composition`, and `StoreAgreedActions.__init__` has exactly one parameter after `self`.

**Regression:** `test_3c0a_*`, `test_3c1_*`, the S6-01a action tests (`test_s6_action_*`), and once unit 2 lands the 5c
tests; the persistence guard; check-all once at the end; `select-tests` before review.

## 6. Done (questions; each can fail)

1. Does R1 record one agreed Action with Amina as creator, Peter as owner, due 15 December 2026, and print §4's line
   with exactly the twelve keys and no value?
2. Does every re-run of §4 record nothing new and say so, including one after the due date?
3. Is every refusal of §4 given with its code and exact sentence, nothing on stdout, and only the executive able to
   agree a change?
4. Can only an owner whose role covers the Action's Site (or, for executive and finance lead, the whole operator) own
   it, so that Peter owns Kobo's change and not Mto's, and the analyst and technician own none?
5. Is the record append-only (UPDATE, DELETE and TRUNCATE refused) and written only by its adapter (the guard, shown
   failing)?
6. Do the lock and the index each hold "once" on their own (tests 7(b) and 7(c))?
7. Does the read list only agreed Actions, newest first with the `id` tie-break, with names and "Open" or "Overdue"?
8. After unit 2, does 5c's screen show World C's row from the database, through the one service only?
9. Does each planted violation in the reviewer guide fail its named test, and is the mid-build count 0?

Packet: `specs/3C2-agreed-change-action/packet.md` (gate A's head and number, any gate-B renumber, residual risk
`R-AUTH`, the guard's two failing runs, the mid-build count).

## 7. Out of scope

Closing, completing, reassigning or re-dating an Action (3C3, with the screen controls); valuing the change (RC9;
`6a`); owners and due dates on the S6-01a finding Actions (queued `3C2b`, next fortnight; D-3C2.1); an HTTP route
(the analyst records by command; 3C3 adds the screen and a signed-in path); notifications; a Site's timezone for
"Overdue" (3C3).

## 8. Units

| Unit | Content | Needs | Commits |
|---|---|---|---|
| 1 (1.25) | §2: migration, model, memory store, adapter, service, command, permission line, guard block; tests 1 to 8; check-all; packet | gate A (3A6 merged; number read at the head); gate B at merge | 1 to 2 |
| 2 (0.25) | §3: `StoreAgreedActions`, the composition line; tests 9(d) and 9(e) | gate C (unit 1 and 5c unit 2 merged) | 1 |

## 9. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 (owner) | Who may record an agreed change | The operator's executive only (D-3C2.2); the finance lead and Site managers own changes but do not agree them for the operator |
| Q2 (owner) | May the analyst type the agreed change in the executive's name? | Yes, as 3A7 Q1: `created_by_script` true, the runbook says the executive agreed it in the meeting; not a sign-in (D-3C2.12, `R-AUTH`); a person records it on screen once 3C3 lands |
| Q3 (owner) | Owners and due dates on the existing finding Actions | Not this fortnight: queued `3C2b` (the delivery plan's 2.5-unit 3C2 is cut to the deep-dive's record, 1.5 units; D-3C2.1) |
| Q4 | "Overdue" by which day | The UTC date at the read (D-3C2.4, `--help` epilog); a Site's own timezone when 3C3 adds the screen |
| Q5 (owner) | Who may own an agreed change | Executive and finance lead anywhere; a Site manager at their Site only; analyst and field technician never (D-3C2.6). Letting the technician own Site changes would need a Site on the technician's grant |
| Q6 (owner) | A live S6-01a Action beside the agreed one in 5c test 9(d) | No: the import check 9(e) proves the screen has one source; a live S6-01a Action needs a Finding chain on 5c's tenant (+0.25 unit) |
