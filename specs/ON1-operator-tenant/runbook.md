<!-- ON1 spec rev 3.1 (D-ON1.19): verbatim source of Docs/engineering/operator-deep-dive-runbook.md (copied from the first heading). -->
# Operator deep-dive: onboarding a tenant, receiving exports, and erasure

Who does what: the **coordinator** creates and deletes databases and keys (steps 2, 3 and 7); the **analyst** fills
the onboarding file, applies it and submits exports (steps 1, 4 and 6); the tenant's **finance lead** accepts exports
(step 6). No agent runs steps 2, 3 or 7.

**Real operators wait.** Today only emulated tenants are onboarded (the rehearsal). A real operator needs a signed
data-processing agreement, its own database (`assetops_op_<name>`), and its executive's approval of the roles at
sign-in; that last step is not built yet (unit `ON1b`). Until it is, the onboarding command refuses every file
marked `"data": "real"` before it writes anything, and no operator database is created. Never mark a real
operator's file `"emulated"`: real data belongs only in its own database, after the agreement is signed.

Shell variables used below (plain assignments such as `REHEARSAL=ddr1`, never `export`): `REHEARSAL` (the rehearsal
database's name part: lower-case letters, digits, `_`), `FILE`, `DIGEST`, `KEY_DIR`, `DB_PASSWORD`, `EMAIL`, `DIR`,
`TENANT_ID`. Run every command from the repository root with the project's Python on the path.

**Settings never go into your shell.** Every command that needs the tenant's settings runs inside a `( ... )` block
that sets them for that block only. A setting exported into the shell would follow you: a later demo restart from the
same shell could serve this tenant instead of the demo.

## 1. The onboarding file

Fill the onboarding file (template: `backend/tests/fixtures/on1/lakeside-power.onboarding.json`): `"data":
"emulated"`, the operator code and name, `"vertical": "MINI_GRID"`, each Site (code, name, time zone such as
`Africa/Nairobi`, country, locality, `ACTIVE`, the date its records start, its installed components), and each person
(email, name, roles). One person is the operator executive; at least one is the finance lead; at least one is the
analyst. The analyst is never also the finance lead or the executive: whoever submits an export is never the person
who accepts it. A Site manager names their Site. Every role in an emulated file is granted when the file is applied.

## 2. The rehearsal database (coordinator only)

```sh
REHEARSAL=ddr1
docker exec assetopsv1-postgres-1 createdb -U assetops "assetops_rehearsal_$REHEARSAL"
(
  export DATABASE_URL="postgresql+psycopg://assetops:$DB_PASSWORD@127.0.0.1:55432/assetops_rehearsal_$REHEARSAL"
  cd backend && ../.venv/bin/python -m alembic upgrade head
)
```

Never the walkthrough database behind 5490, never a name starting `assetops_op`; the real-data switch stays off.

## 3. The key directory (coordinator only)

```sh
KEY_DIR=/opt/assetecon/keys/assetops_rehearsal_$REHEARSAL
install -d -m 700 "$KEY_DIR"
```

Keep it outside the repository and out of every backup, on this server or off it; never copy it. The key itself is
created in step 4.

## 4. Digest, check and apply the onboarding file

Four blocks, run in order. First the digest (it reads the file only, no settings):

```sh
FILE=backend/tests/fixtures/on1/lakeside-power.onboarding.json
python -m assetops_backend.onboard_operator digest --file "$FILE"
```

Set `DIGEST` to the value it printed (64 characters), on its own line: `DIGEST=` followed by that value. `apply`
refuses any other file. Then check:

```sh
(
  export DATABASE_URL="postgresql+psycopg://assetops:$DB_PASSWORD@127.0.0.1:55432/assetops_rehearsal_$REHEARSAL"
  export ASSETOPS_TENANT_SLUG=lakeside-power ASSETOPS_PSEUDONYM_KEY_DIR="$KEY_DIR"
  python -m assetops_backend.onboard_operator check --file "$FILE" --key-dir "$KEY_DIR"
)
```

`check` prints what would be created and changes nothing; read it: the operator, each Site, each person (by position
in the file), each role, the key and the roles digest (it must equal `DIGEST`). A refusal names its code and the place
in the file; correct the file and start again from the digest. Then apply:

```sh
(
  export DATABASE_URL="postgresql+psycopg://assetops:$DB_PASSWORD@127.0.0.1:55432/assetops_rehearsal_$REHEARSAL"
  export ASSETOPS_TENANT_SLUG=lakeside-power ASSETOPS_PSEUDONYM_KEY_DIR="$KEY_DIR"
  python -m assetops_backend.onboard_operator apply --file "$FILE" --key-dir "$KEY_DIR" --confirmed-digest "$DIGEST"
)
```

`apply` creates them, grants every role, and prints the same plan as done, with the tenant's `id` (keep it: it is
`TENANT_ID` in step 7). Running `apply` again creates nothing more.

Last, a password for each person who will sign in (for Lakeside: Amina, Wanjiru and Joseph). Run this block once per
person, setting `EMAIL` to that person's email from the file each time; `set-password` asks for the password (12 to
128 characters) on standard input:

```sh
EMAIL=amina@lakeside-power.example
(
  export DATABASE_URL="postgresql+psycopg://assetops:$DB_PASSWORD@127.0.0.1:55432/assetops_rehearsal_$REHEARSAL"
  export ASSETOPS_TENANT_SLUG=lakeside-power ASSETOPS_PSEUDONYM_KEY_DIR="$KEY_DIR"
  python -m assetops_backend.accounts.onboard set-password --email "$EMAIL"
)
```

Then again with `EMAIL=wanjiru@lakeside-power.example` and with `EMAIL=joseph@lakeside-power.example`.

## 5. Do not change a tenant by editing the file

To change a Site, a name or a role after onboarding, do not edit the file: the executive grants and removes roles,
and Sites change through their Foundation. Once the executive has granted any role, the command grants no more.

## 6. Receive the emulated exports

Write the emulated exports and load them, Wanjiru (the analyst) submitting and Joseph (the finance lead) accepting:

```sh
(
  export DATABASE_URL="postgresql+psycopg://assetops:$DB_PASSWORD@127.0.0.1:55432/assetops_rehearsal_$REHEARSAL"
  export ASSETOPS_TENANT_SLUG=lakeside-power ASSETOPS_PSEUDONYM_KEY_DIR="$KEY_DIR"
  python tools/world_history.py exports --manifest Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml --out "$DIR"
  python -m assetops_backend.load_emulated_exports --dir "$DIR" --tenant lakeside-power --submit-as wanjiru@lakeside-power.example --accept-as joseph@lakeside-power.example
)
```

The loader refuses any operator database, and any database address it cannot read plainly, before it connects. A
rehearsal tenant takes the emulated files only: never load the generated world's canonical files into it. Only an
accepted export counts.

## 7. Erase (coordinator only)

When the rehearsal is done (and, once `ON1b` exists, at an operator's agreed term). Stop any server for this tenant
first. Then erase the key, the database and every copy that holds names, emails or customer references:

```sh
python -m assetops_backend.commercial.pseudonym_key erase --dir "$KEY_DIR" --tenant-id "$TENANT_ID"
docker exec assetopsv1-postgres-1 dropdb -U assetops "assetops_rehearsal_$REHEARSAL"
rm -rf -- "$DIR"
```

Delete the onboarding file too if it is not the repository's fixture. Then check that no copy of the key directory or
the database exists anywhere else on the server (step 3 kept them out of backups; delete any you find) and remove the
shell history lines that hold emails.

Erasing the key is final: customer, meter and staff identities can no longer be linked to anyone, the server answers
every new export for this tenant "identities were erased", and no new key can be made for it. If the tenant is
needed again, onboard it as a new tenant in a new database.
