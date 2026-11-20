<!-- ON1 spec rev 2: verbatim source of Docs/engineering/operator-deep-dive-runbook.md (copied from the first heading). -->
# Operator deep-dive: from a signed agreement to the first accepted export, and to erasure

Who does what: the **coordinator** creates and deletes databases and keys (steps 2, 3 and 11); the **analyst** fills
the onboarding file, applies it and submits exports (steps 1, 4 to 7 and 9); the operator's **executive** confirms
the people and roles in writing (step 1) and approves them by signing in once (step 8); the operator's **finance
lead** accepts exports (step 9). No agent runs steps 2, 3 or 11, and no real operator data is touched before step 1
is done (RC4).

Shell variables used below (plain assignments such as `SLUG=lakeside-power`, never `export`): `OPNAME` (the
operator's database name part: lower-case letters, digits, `_`), `SLUG` (the operator code in the onboarding file),
`FILE`, `DIGEST`, `KEY_DIR`, `DB_PASSWORD`, `PORT`, `EMAIL`, `READER`, `EXPORT`, `UPLOAD_ID`, `EXPORTS_DIR`,
`TENANT_ID`, `REHEARSAL`, `DIR`. Run every command from the repository root with the project's Python on the path.

**Settings never go into your shell.** Every command that needs the operator's settings runs inside a `( ... )`
block that sets them for that block only. A setting exported into the shell would follow you: a later demo restart
from the same shell could serve this operator instead of the demo.

## 1. Before anything: the agreement and the file

- The data-processing agreement is signed. Record its date and the agreed retention term (how long the data is
  kept). Without both, stop.
- Fill the onboarding file with the operator (template: `backend/tests/fixtures/on1/lakeside-power.onboarding.json`):
  `"data": "real"`, the operator code and name, `"vertical": "MINI_GRID"`, each Site (code, name, time zone such as
  `Africa/Nairobi`, country, locality, `ACTIVE`, the date its records start, its installed components), and each
  person (email, name, the roles proposed for them). One person is the operator executive; at least one is the
  finance lead; at least one (often you) is the analyst. The analyst is never also the finance lead or the executive:
  whoever submits an export is never the person who accepts it. A Site manager names their Site.
- Print the file's roles digest:

```sh
python -m assetops_backend.onboard_operator digest --file "$FILE"
```

- Send the executive the people and roles in the file and this digest. The executive confirms them in writing,
  naming the digest. Keep that message; the digest is `DIGEST` below. Any later change to a person or a role changes
  the digest: send it again.
- Ask the operator to name export files by content and month (for example `billing-2026-10.csv`), never by a person.

## 2. The operator's database (coordinator only, after step 1)

```sh
OPNAME=pilot1
docker exec assetopsv1-postgres-1 createdb -U assetops "assetops_op_$OPNAME"
(
  export DATABASE_URL="postgresql+psycopg://assetops:$DB_PASSWORD@127.0.0.1:55432/assetops_op_$OPNAME"
  cd backend && ../.venv/bin/python -m alembic upgrade head
)
```

The name must be `assetops_op_` followed by lower-case letters, digits or `_` (at most 40). The server refuses any
other pairing of this database with the real-data switch, and any database address with extra settings that could
point elsewhere.

## 3. The key directory (coordinator only)

```sh
KEY_DIR=/opt/assetecon/keys/assetops_op_$OPNAME
install -d -m 700 "$KEY_DIR"
```

Keep it outside the repository and out of every backup, on this server or off it; never copy it. The key itself is
created in step 5.

## 4. The settings for this operator

Steps 5 to 7 each open their block with the same four settings:

```sh
(
  export DATABASE_URL="postgresql+psycopg://assetops:$DB_PASSWORD@127.0.0.1:55432/assetops_op_$OPNAME"
  export ASSETOPS_REAL_OPERATOR_DATA=on ASSETOPS_TENANT_SLUG="$SLUG" ASSETOPS_PSEUDONYM_KEY_DIR="$KEY_DIR"
)
```

With these four, the server takes only this operator's own records (`observed-financial`) and serves only its Sites.
Do not set `PGHOST`, `PGDATABASE`, `PGPORT`, `PGHOSTADDR`, `PGSERVICE` or `PGSERVICEFILE`: the server refuses to
start with any of them.

## 5. Check, then apply, the onboarding file

```sh
(
  export DATABASE_URL="postgresql+psycopg://assetops:$DB_PASSWORD@127.0.0.1:55432/assetops_op_$OPNAME"
  export ASSETOPS_REAL_OPERATOR_DATA=on ASSETOPS_TENANT_SLUG="$SLUG" ASSETOPS_PSEUDONYM_KEY_DIR="$KEY_DIR"
  python -m assetops_backend.onboard_operator check --file "$FILE" --key-dir "$KEY_DIR"
  python -m assetops_backend.onboard_operator apply --file "$FILE" --key-dir "$KEY_DIR" --confirmed-digest "$DIGEST"
)
```

`check` prints what would be created and changes nothing. Read it: the operator, each Site, each person (by
position in the file), each proposed role, the key and the roles digest. `apply` refuses a file whose digest is not
the one the executive confirmed; otherwise it creates them and prints the same plan as done, with the tenant's `id`
(keep it: it is `TENANT_ID` in step 11). The executive holds their role now; every other role is only proposed until
step 8. Running `apply` again creates nothing more. A refusal names its code and the place in the file; correct the
file (and have the executive confirm the new digest) and run `check` again. To change a Site, a name or a role after
onboarding, do not edit the file: the executive grants and removes roles, and Sites change through their Foundation.

## 6. Passwords

For each person, type their password (12 to 128 characters) when asked; send it to them through the operator's own
channel, never in the same message as the address of the server:

```sh
(
  export DATABASE_URL="postgresql+psycopg://assetops:$DB_PASSWORD@127.0.0.1:55432/assetops_op_$OPNAME"
  export ASSETOPS_REAL_OPERATOR_DATA=on ASSETOPS_TENANT_SLUG="$SLUG" ASSETOPS_PSEUDONYM_KEY_DIR="$KEY_DIR"
  python -m assetops_backend.accounts.onboard set-password --email "$EMAIL"
)
```

## 7. Start the server for this operator

```sh
(
  export DATABASE_URL="postgresql+psycopg://assetops:$DB_PASSWORD@127.0.0.1:55432/assetops_op_$OPNAME"
  export ASSETOPS_REAL_OPERATOR_DATA=on ASSETOPS_TENANT_SLUG="$SLUG" ASSETOPS_PSEUDONYM_KEY_DIR="$KEY_DIR"
  export ASSETOPS_SESSION_COOKIE_SECURE=off
  python -m uvicorn assetops_backend.main:app --host 127.0.0.1 --port "$PORT"
)
```

Use a port other than 5490 and 8990. The server listens on this machine only (127.0.0.1), which is why its sign-in
cookie may travel over plain http (`ASSETOPS_SESSION_COOKIE_SECURE=off`); never open this port to a network. It
refuses to start if the database, the switch and `ASSETOPS_TENANT_SLUG` do not agree; the message says which.

## 8. The executive approves the roles (once)

With the executive present, they sign in once with the digest they confirmed. Each person signs in by typing one
line, `{"email": "...", "password": "...", "approve_roles": "<digest>"}`, then Ctrl-D (the password never goes on
the command line):

```sh
curl -sS -c executive.cookies -H 'Content-Type: application/json' -d @- http://127.0.0.1:$PORT/api/auth/sign-in
```

The answer lists `roles_granted`: these roles are now granted by the executive. Until this step nobody else can
submit or accept. Signed in without `approve_roles`, the answer lists `roles_awaiting_approval` and grants nothing;
with another digest it refuses and grants nothing.

## 9. Receive an export

First route: the operator's own source profile (`3A6`), `READER` = the profile id registered for this operator.
Fallback, a workaround the owner kept (RC2): when no profile reads an export, reshape it by hand into one of the
template layouts (`billing-illustrative-1`, `collections-illustrative-1`, `expenses-illustrative-1`,
`budget-illustrative-1`, see `contracts/assetops_contracts/native/layouts_v1.py`) and use that layout id as
`READER`; record beside the agreement, per file, that it was reshaped and the minutes it took. Keep every export,
raw and reshaped, in `EXPORTS_DIR` and nowhere else.

The analyst signs in (typing `{"email": "...", "password": "..."}` then Ctrl-D), checks the file (nothing is kept),
then submits it:

```sh
curl -sS -c analyst.cookies -H 'Content-Type: application/json' -d @- http://127.0.0.1:$PORT/api/auth/sign-in
curl -sS -b analyst.cookies -H 'Content-Type: text/csv' -H "X-File-Name: $(basename "$EXPORT")" \
  --data-binary @"$EXPORT" \
  "http://127.0.0.1:$PORT/api/organisation/commercial-uploads?dry_run=true&reader=$READER"
```

Read the answer: how many rows are new, corrected, already held and refused, and each refused row in plain words.
Send the same request with `dry_run=false` to submit; its answer holds the upload's id (`UPLOAD_ID`). The finance
lead signs in the same way and accepts (or declines with a reason):

```sh
curl -sS -c finance.cookies -H 'Content-Type: application/json' -d @- http://127.0.0.1:$PORT/api/auth/sign-in
curl -sS -b finance.cookies -H 'Content-Type: application/json' -d '{"decision": "ACCEPT"}' \
  http://127.0.0.1:$PORT/api/organisation/commercial-uploads/$UPLOAD_ID/decision
```

Only an accepted export counts. If the answer is "Records in this export changed after it was checked", decline it
and send the file again.

## 10. Rehearsal on emulated data (never on an operator database)

The coordinator creates a rehearsal database `assetops_rehearsal_$REHEARSAL` (never the walkthrough database behind
5490, never a name starting `assetops_op`) and a key directory for it, then runs, with the real-data switch off:

```sh
REHEARSAL=ddr1
FILE=backend/tests/fixtures/on1/lakeside-power.onboarding.json
KEY_DIR=/opt/assetecon/keys/assetops_rehearsal_$REHEARSAL
(
  export DATABASE_URL="postgresql+psycopg://assetops:$DB_PASSWORD@127.0.0.1:55432/assetops_rehearsal_$REHEARSAL"
  export ASSETOPS_TENANT_SLUG=lakeside-power ASSETOPS_PSEUDONYM_KEY_DIR="$KEY_DIR"
  python -m assetops_backend.onboard_operator digest --file "$FILE"
  python -m assetops_backend.onboard_operator check --file "$FILE" --key-dir "$KEY_DIR"
  python -m assetops_backend.onboard_operator apply --file "$FILE" --key-dir "$KEY_DIR" --confirmed-digest "$DIGEST"
  python -m assetops_backend.accounts.onboard set-password --email amina@lakeside-power.example
  python -m uvicorn assetops_backend.main:app --host 127.0.0.1 --port "$PORT"
)
```

(`DIGEST` is the value the `digest` line printed; run `set-password` for Wanjiru and Joseph too.) Amina, the
emulated executive, approves the roles as in step 8. Stop the server, then write the emulated exports and load them,
Wanjiru (the analyst) submitting and Joseph (the finance lead) accepting:

```sh
(
  export DATABASE_URL="postgresql+psycopg://assetops:$DB_PASSWORD@127.0.0.1:55432/assetops_rehearsal_$REHEARSAL"
  export ASSETOPS_TENANT_SLUG=lakeside-power ASSETOPS_PSEUDONYM_KEY_DIR="$KEY_DIR"
  python tools/world_history.py exports --manifest Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml --out "$DIR"
  python -m assetops_backend.load_emulated_exports --dir "$DIR" --tenant lakeside-power --submit-as wanjiru@lakeside-power.example --accept-as joseph@lakeside-power.example
)
```

The loader refuses any operator database, and any database address it cannot read plainly, before it connects. A
rehearsal tenant takes the emulated files only: never load the generated world's canonical files into it.

## 11. Retention ends: erase (coordinator only)

At the agreed term, or on the operator's request. Stop the operator's server first. Then erase the key, the database
and every copy that holds names, emails or customer references:

```sh
python -m assetops_backend.commercial.pseudonym_key erase --dir "$KEY_DIR" --tenant-id "$TENANT_ID"
docker exec assetopsv1-postgres-1 dropdb -U assetops "assetops_op_$OPNAME"
rm -f -- "$FILE"
rm -rf -- "$EXPORTS_DIR"
rm -f -- executive.cookies analyst.cookies finance.cookies
```

Then check that no copy of the key directory or the database exists anywhere else on the server (step 3 kept them
out of backups; delete any you find) and remove the shell history lines that hold emails.

Erasing the key is final: customer, meter and staff identities can no longer be linked to anyone, the server answers
every new export for this operator "identities were erased", and no new key can be made for it. If the operator
returns, onboard it again as a new operator in a new database. Record the erasure date beside the agreement.
