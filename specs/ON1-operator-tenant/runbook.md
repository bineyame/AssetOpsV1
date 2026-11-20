<!-- ON1 spec: verbatim source of Docs/engineering/operator-deep-dive-runbook.md (copied from the first heading). -->
# Operator deep-dive: from a signed agreement to the first accepted export, and to erasure

Who does what: the **coordinator** creates and deletes databases and keys (steps 2, 3 and 10); the **analyst** fills
and applies the onboarding file and submits exports (steps 4 to 8); the operator's **finance lead** accepts exports
(step 8); the operator's **executive** confirms the people and roles (step 1). No agent runs steps 2, 3 or 10, and no
real operator data is touched before step 1 is done (RC4).

Shell variables used below: `OPNAME` (the operator's database name part: lower-case letters, digits, `_`), `SLUG`
(the operator code in the onboarding file), `KEY_DIR`, `FILE`, `TENANT_ID`, `EMAIL`, `DIR`, `PORT`, `DB_PASSWORD`.
Run every command from the repository root with the project's Python on the path.

## 1. Before anything: the agreement and the file

- The data-processing agreement is signed. Record its date and the agreed retention term (how long the data is
  kept). Without both, stop.
- Fill the onboarding file with the operator (template: `backend/tests/fixtures/on1/lakeside-power.onboarding.json`):
  `"data": "real"`, the operator code and name, `"vertical": "MINI_GRID"`, each Site (code, name, time zone such as
  `Africa/Nairobi`, country, locality, `ACTIVE`, the date its records start, its installed components), and each
  person (email, name, roles). One person is the operator executive; at least one is the finance lead; at least one
  (often you) is the analyst. A Site manager names their Site.
- The operator's executive reads the people and roles in the file and confirms them in writing. Keep that message.
- Ask the operator to name export files by content and month (for example `billing-2026-10.csv`), never by a person.

## 2. The operator's database (coordinator only, after step 1)

```sh
export OPNAME=pilot1
docker exec assetopsv1-postgres-1 createdb -U assetops "assetops_op_$OPNAME"
export DATABASE_URL="postgresql+psycopg://assetops:$DB_PASSWORD@127.0.0.1:55432/assetops_op_$OPNAME"
cd backend && ../.venv/bin/python -m alembic upgrade head && cd ..
```

The name must be `assetops_op_` followed by lower-case letters, digits or `_` (at most 40). The server refuses any
other pairing of this database with the real-data switch.

## 3. The key directory (coordinator only)

```sh
export KEY_DIR=/opt/assetecon/keys/assetops_op_$OPNAME
install -d -m 700 "$KEY_DIR"
```

Keep it outside the repository and out of every backup that leaves the server. The key itself is created in step 5.

## 4. The settings for this operator

```sh
export ASSETOPS_REAL_OPERATOR_DATA=on
export ASSETOPS_TENANT_SLUG=$SLUG
export ASSETOPS_PSEUDONYM_KEY_DIR=$KEY_DIR
```

With these three and the `DATABASE_URL` of step 2, the server takes only this operator's own records
(`observed-financial`) and serves only its Sites.

## 5. Check, then apply, the onboarding file

```sh
python -m assetops_backend.onboard_operator check --file $FILE --key-dir $KEY_DIR
python -m assetops_backend.onboard_operator apply --file $FILE --key-dir $KEY_DIR
```

`check` prints what would be created and changes nothing. Read it: the operator, each Site, each person (by
position in the file), each role, and the key. `apply` creates them and prints the same plan as done. Running `apply`
again creates nothing more. A refusal names its code and the place in the file; correct the file and run `check`
again. To change a Site, a name or a role after onboarding, do not edit the file: the executive grants and removes
roles, and Sites change through their Foundation.

## 6. Passwords

For each person, type their password (12 to 128 characters) when asked; send it to them through the operator's own
channel, never by the same message as the address of the server:

```sh
python -m assetops_backend.accounts.onboard set-password --email $EMAIL
```

## 7. Start the server for this operator

```sh
python -m uvicorn assetops_backend.main:app --port $PORT
```

Use a port other than 5490 and 8990. The server refuses to start if the database, the switch and
`ASSETOPS_TENANT_SLUG` do not agree; the message says which.

## 8. Receive an export

The analyst signs in, checks the file (nothing is kept), then submits it; the finance lead signs in and accepts it.
Until source profiles exist for this operator's exports (`3A6`), reshape each export into one of the layouts the
server reads (`billing-illustrative-1`, `collections-illustrative-1`, `expenses-illustrative-1`,
`budget-illustrative-1`, see `contracts/assetops_contracts/native/layouts_v1.py`) and send it with
`reader=<layout id>`; that reshaping is a workaround, and its time is recorded per file.

```sh
curl -sS -c analyst.cookies -H 'Content-Type: application/json' \
  -d '{"email": "'"$EMAIL"'", "password": "..."}' http://127.0.0.1:$PORT/api/auth/sign-in
curl -sS -b analyst.cookies -H 'Content-Type: text/csv' -H 'X-File-Name: billing-2026-10.csv' \
  --data-binary @billing-2026-10.csv \
  "http://127.0.0.1:$PORT/api/organisation/commercial-uploads?dry_run=true&reader=billing-illustrative-1"
```

Read the answer: how many rows are new, corrected, already held and refused, and each refused row in plain words.
Send the same request with `dry_run=false` to submit. The finance lead then accepts (or declines with a reason):

```sh
curl -sS -b finance.cookies -H 'Content-Type: application/json' -d '{"decision": "ACCEPT"}' \
  http://127.0.0.1:$PORT/api/organisation/commercial-uploads/<upload_id>/decision
```

Only an accepted export counts. If the answer is "Records in this export changed after it was checked", decline it
and send the file again.

## 9. Rehearsal on emulated data (never on an operator database)

On a rehearsal database (any name not starting `assetops_op`), with `ASSETOPS_REAL_OPERATOR_DATA` unset, onboard the
Lakeside file (`"data": "emulated"`), write the emulated exports and load them:

```sh
python tools/world_history.py exports --manifest Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml --out $DIR
python -m assetops_backend.load_emulated_exports --dir $DIR --tenant $SLUG --submit-as $EMAIL --accept-as $EMAIL
```

`--submit-as` names the analyst and `--accept-as` the finance lead (two different emails in practice). The loader
refuses any operator database before it connects.

## 10. Retention ends: erase (coordinator only)

At the agreed term, or on the operator's request (`TENANT_ID` is the `tenant.id` that step 5's `apply` printed):

```sh
python -m assetops_backend.commercial.pseudonym_key erase --dir $KEY_DIR --tenant-id $TENANT_ID
docker exec assetopsv1-postgres-1 dropdb -U assetops "assetops_op_$OPNAME"
```

Stop the server first. Erasing the key is final: customer, meter and staff identities can no longer be linked to
anyone, the server answers every new export for this operator "identities were erased", and no new key can be made
for it. If the operator returns, onboard it again as a new operator in a new database. Record the erasure date beside
the agreement.
