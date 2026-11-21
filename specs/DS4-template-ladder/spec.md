# DS4: the template ladder, the world commands and the re-benchmark (implementer spec)

Status: rev 1, handshake pending. Architect (Claude), 2026-11-21, on the owner's delegation
(`owner/owner-away-architect-decides-2026-11-21.md`; pull order `specs/OWNER-AWAY/decisions-2026-11-21.md` row 4;
rows 33 to 36 for the calls made here). `delivery-plan.md` §2 row `DS4`: "Template ladder, the world commands and the
build manifest; the stage-by-stage re-benchmark of the build cost (delivery §5)" (2.5 units; depends on `DS3`; feeds
`WK`, `DS6`, `DS7`). Design source: data and build strategy §4, §8, §9 and Appendix A (branch
`task/data-build-strategy`, `Docs/engineering/data-and-build-strategy.md`; not on `main`). **2.75 units** (D-DS4.14),
three units, no split. Discovery review (W5): a new mechanism that decides what a "clean, good" database is, and one
edit in the bulk load's seam. Non-screen; no user-facing text (D-DS4.15). A **heavy database job**: one at a time
machine-wide (row 4), every database command through `tools/heavy-slot.sh --db`.

- **What it is.** One tool, `tools/world.py`, builds the demonstration world as a ladder of template databases
  (L0 schema, L1 inputs, L2 computed), each keyed by what it was built from and rebuilt only when that key changes;
  clones a run's database from L2 in seconds; checks a built world (inputs, census, snapshot rebuild, the
  independent model, DS3's parity); and measures every stage once on a quiet machine so the strategy's targets are
  replaced by numbers. Every write into a world goes through the product's own commands (`onboard_operator`,
  `load_world_inputs`, `build_structure_snapshot`, `observe_structure`); the tool itself writes no product table.
- **The telemetry question (D-DS4.1), answered first.** The world's telemetry comes from one source only: the world
  generator's telemetry writer (`DS2` and the Site configuration it needs, next fortnight), as Batch V2 files under
  `<world>/<tenant>/telemetry/`. This fortnight there is none, and the world says so in its definition and build
  manifest. §2 gives the survey and the reasons.
- **Builds on (merged on `main` at `7080d2d94`):** `tools/world_history.py exports` (3A3), `onboard_operator`
  (ON1, `backend/tests/fixtures/on1/lakeside-power.onboarding.json`), `load_world_inputs` and
  `evidence/bulk_load.py` (DS3: `BulkEvidenceLoad`, `permitted_database`, `BULK_LOAD_REFUSALS`),
  `PostgresEvidenceLedger.gateway_principal`, `build_structure_snapshot build|verify` (3B7a; `structure_snapshot/
  composition.py` `build_structure_snapshot`, `store.get`, `codec.payload_of`), `observe_structure run` (3B4),
  `commercial.pseudonym_key erase`, `scheduling.run enrol|tick` and `tools/demo_combined_drain.py` (`counts`,
  `n_for`, `step`), `tools/heavy_slot_check.py` (`require`), `backend/tests/pg_harness.py` (`clone_database`,
  `drop_database`), `backend/tests/test_ds3_bulk_load_postgres.py` (`seed_database`, `kobo_days`, `DAY6`, `census`),
  `backend/tests/test_ds3_parity_postgres.py`, `Docs/demo-sprint/product-direction-layer4/derived-values.json`.
- **Decisions:** `rulings.md` (D-DS4.1 to D-DS4.15). **Reviewer guide:** `reviewer-guide.md`. **Handshake:**
  `handshake.md`.

## 0. Before you start (gates; each is a hard stop)

- **Start:** the handshake has no open question; no other heavy database job holds the machine (row 4: DS3, DS4 and
  WK one at a time). No unmerged dependency (`DS3`, `ON1`, `3A3`, `3B7a`, `3B4` are merged).
- **Unit 3's real runs only:** the coordinator has created the key root `/opt/assetecon/keys/world` (mode 700,
  runbook step 3's rule: the coordinator creates key directories) and confirms the machine is quiet (RULES §7: one
  full job at a time, `tools/keep-awake-during-tests.ps1` started, cap twice the expected wall time). Units 1 and 2
  need neither: their tests use temporary key roots.
- **Branch** `task/DS4-template-ladder` off `main`; worktree `/opt/assetecon/AssetOpsV1-ds4`; symlink
  `frontend/node_modules` from the main checkout.
- **Databases (authorised set only).** Tests: `pg_harness` clones (`*_pt<run>_<tag>_test`) and, for the tool's own
  integration test, `assetops_ds4t<8 hex>_audit_*` databases it creates and drops itself (§5, T12 to T14). Unit 3:
  `assetops_worldbench_audit_*` (dropped by the bench) and `assetops_world_audit_*` (the ladder WK uses; kept). The
  tool connects to the server's `postgres` maintenance database for DDL on those names only (D-DS4.4). Never the
  walkthrough database `assetops_polish_walk1113_test`, any `assetops_op*` name, ports 5490 or 8990, or Docker.
- **Read:** `rulings.md`; `load_world_inputs.py` (whole); `evidence/bulk_load.py` (whole);
  `postgres_evidence_ledger.py:620-640`; `onboard_operator.py:99-150`; `build_structure_snapshot.py` (whole);
  `observe_structure.py:1-40`; `structure_snapshot/codec.py:74-90`, `:221-226`; `structure_snapshot/build.py:59-125`;
  `load_emulated_exports.py:1-60`, `:90-115`; `tools/world_history.py:1-80`; `tools/demo_combined.py:1-80` (the
  admin URL, `PG_TARGET_ENV`, `TICK`); `tools/demo_combined_drain.py` (whole); `tools/heavy_slot_check.py:152-175`;
  `pg_harness.py:243-275`, `:328-372`; `test_ds3_bulk_load_postgres.py:41-130`; `test_ds3_bench_postgres.py`
  (whole); `scheduling/run.py:1-100`; `scheduling/tick.py:288-330`; `Docs/engineering/operator-deep-dive-runbook.md`
  steps 2 to 7.
- **Files.** New: `tools/world.py`, `backend/conversions/world-layer4-v1.json`, `backend/tests/test_ds4_world.py` (no
  database), `backend/tests/test_ds4_world_postgres.py`, `backend/tests/test_ds4_batch_days_postgres.py`,
  `backend/tests/test_ds4_bench_pipeline_postgres.py`. Edited: `evidence/bulk_load.py` (one step, two pure functions,
  one refusal code), `evidence/adapters/postgres_evidence_ledger.py` (one read beside `gateway_principal`). **No
  migration**, no route, no screen, no guard edit, no simulator or contracts change, nothing under `tools/checks/`.

## 1. Outcome and why

The owner's rule is that the walkthrough runs only on a clean, good database, and the owner accepted the strategy's
meaning of it: "an L2 clone whose `world check` passed (parity, golden digests, oracle, snapshot rebuild)" (strategy
§10 question 4, "yes"). Today the walkthrough build takes about two hours from nothing and is checked by hand. DS4
makes the world a keyed, rebuilt-only-on-change template, a run's database a seconds-long clone, the check a command,
and the build cost a measurement instead of a target (delivery §5: "Its results replace the targets").

Gate questions (each can fail): Is a template used only when every input, code tree and migration it was built
from is unchanged, and is a stale one refused naming what changed? Does every write into a world go through the
product's own commands, into permitted names only, never the walkthrough or an operator's database? Does `world
check` fail on a changed input, a dirtied template, a snapshot that no longer rebuilds, a figure that differs from the
independent model, or a parity break? Is a world batch whose days have a gap refused before it is admitted
(D-DS3.21)? Does the re-benchmark state each stage's seconds with what they include, and say plainly which
operations it could not measure?

## 2. Where the world's telemetry comes from (D-DS4.1)

| Candidate surveyed | What it is on `main` | Why it is not the world's telemetry |
|---|---|---|
| The walkthrough build's telemetry (`tools/demo_combined.py`, its `_kobo`, `_cold`, `_ev`, `_kisiwa` children) | Registered Lab runs of the simulator packs, sealed by a real gateway process and submitted to central ingestion one envelope at a time (`demo_combined_kobo.py:1-20`, `:240-330`) | Its Sites (`COLD-LAB-001`, `EV-LAB-001`; Kobo in tenant `demo` from `fixtures/s1/kobo-001.yaml`) are not the world's; its totals are the walkthrough story's, not the manifest's (Kobo October 1,180 L, 330 L candidate, 120 L unexplained), so a litre split from it would contradict the fuel invoices and the independent model; its runs are registered publications, which the bulk path refuses (`BULK_PUBLISHED_BATCH`, D-DS3.4), so it would keep today's row-by-row cost |
| The test harness's Kobo days (`test_ds3_bulk_load_postgres.day_rows`, the S3 interval rows) | Hand-written flat feeder and generator rows at the converted test Kobo | A fixture: loading it into the world would show invented operation. It stays what it is, the parity slice (§3.6 C5) and the bench slice (§4) |
| Onboarding (`onboard_operator`, ON1) | The world's tenant, Sites (components only), people and roles | ON1's Sites have no gateway, sources or binding set, so no reading can be accepted at them at all (`gateway_principal` returns None: `BULK_UNKNOWN_GATEWAY`; central ingestion refuses likewise) |
| The pipeline drain (`demo_combined_drain.py`, `scheduling.run tick`) | The stages that turn accepted readings into assessments, snapshots and Findings | It consumes telemetry; it does not produce any. It is measured in §4 on the bench slice |
| A copy of the walkthrough database | Outputs of the 13 Nov build | Never: outputs are not inputs, and RULES §7 forbids touching it |

**Ruling.** World telemetry is written only by the world generator from the seed manifest (simulator windows and day
shapes reconciled to the manifest's day totals: `DS2`), sealed with the world Site's own binding set, SIMULATED, as
`<world>/<tenant>/telemetry/*.batch.json`, and loaded by `load_world_inputs` (bulk) under DS3's refusals plus the
gap-day rule (§3.7). Its precondition is that the world's Sites carry a gateway, sources and a published binding set,
declared through the product's own import and conversion path; no unit owns that today (queued, §9 Q2). Until both
land the world has no telemetry: the definition says `"telemetry": {"source": "none", "reason": "DS2_NOT_BUILT"}`,
the build manifest copies it, and every telemetry-fed leaf reads "Not available yet" naming its record, exactly as
`two-week-build-plan.md` §0.4 says a typical operator without an EMS export sees. The fortnight's money gate needs
none (DDR: Kobo −562.00 as +38.00 and −600.00). The 13 Nov walkthrough database keeps the telemetry stories until
then. Owner-level (row 33; owner to weigh in).

Consequences fixed here: cold-chain and EV parity slices (D-DS3.11) move to the unit that first writes cold-chain or
EV telemetry into a world, and `BULK_SITE_TYPE_UNPROVEN` stays (D-DS4.2, row 34); the real-path slice runs inside
`world check` at the harness Site and never enters the world (D-DS4.7); the L2 pipeline stages for telemetry (enrol,
tick, drain) join the ladder with the first world telemetry, and §4 measures their cost now (D-DS4.11, D-DS4.12).

## 3. Design

### 3.1 The world definition (`backend/conversions/world-layer4-v1.json`)

Exactly this content (D-DS4.6):

```json
{
  "format": "assetops.world-definition/1",
  "world": "layer4",
  "manifest": "Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml",
  "derived_values": "Docs/demo-sprint/product-direction-layer4/derived-values.json",
  "months": ["2026-10"],
  "built_by": "service:world-build",
  "tenants": [
    {"slug": "lakeside-power",
     "onboarding": "backend/tests/fixtures/on1/lakeside-power.onboarding.json",
     "submit_as": "wanjiru@lakeside-power.example",
     "accept_as": "joseph@lakeside-power.example",
     "sites": {"KISIWA-001": "Kisiwa", "KOBO-001": "Kobo", "MTO-001": "Mto"}}
  ],
  "not_built": [
    {"tenant": "harvest-cold", "reason": "NO_ONBOARDING_FILE"},
    {"tenant": "metro-bus", "reason": "NO_ONBOARDING_FILE"}
  ],
  "telemetry": {"source": "none", "reason": "DS2_NOT_BUILT"},
  "projection": {"sites": 9, "days": 61,
                 "basis": "manifest time_scales.sparse_operational_context span 2026-09-01..2026-10-31; nine Sites"}
}
```

`read_definition(path) -> Definition` is strict: exactly these keys at each level; `format` equal; `world`
`[a-z0-9]{1,16}`; every path relative, inside the repository, an existing file; `months` non-empty, each
`[0-9]{4}-(0[1-9]|1[0-2])`, sorted, distinct; `built_by` matches `structure_snapshot.model.BUILT_BY`; tenant `slug`
`[a-z0-9][a-z0-9-]{0,62}`, distinct; emails non-empty and different (submitter never accepter); `sites` non-empty;
`not_built` reasons in `{"NO_ONBOARDING_FILE"}`; `telemetry.source == "none"` only (DS2 widens it with its writer);
`projection.sites`, `projection.days` positive integers. Any breach: `WORLD_DEFINITION_INVALID <json path>`.

### 3.2 The ladder: rungs, keys and names (D-DS4.4, D-DS4.5)

| Rung | Database | Built from | Steps (product commands, §3.5) | Key parts (in this order) |
|---|---|---|---|---|
| L0 | `<prefix>_audit_l0_<key12>` | nothing | create; `alembic upgrade head`; freeze | `{"rung": "L0", "migrations": tree(backend/migrations)}` |
| L1 | `<prefix>_audit_l1_<key12>` | L0 | clone; per tenant: onboard digest, check, apply; per tenant: `load_world_inputs`; freeze | `{"rung": "L1", "l0": key0, "definition": sha256(definition bytes), "inputs": inputs digest, "code": {path: tree(path)}}` |
| L2 | `<prefix>_audit_l2_<key12>` | L1 | clone; per tenant, per month: snapshot build, observe; freeze | `{"rung": "L2", "l1": key1, "steps": sha256(canonical(L2_STEPS))}` |
| clone | `<prefix>_audit_c_<label>` | the current L2 | clone | none (its manifest names its parent) |

- `key = sha256(canonical(parts)).hexdigest()`, `canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"),
  ensure_ascii=True)`; `key12 = key[:12]`. `tree(p)` is `git rev-parse HEAD:<p>` (a tree or blob id). `code` covers,
  in this order, `backend/assetops_backend`, `contracts/assetops_contracts`, `simulator/assetops_simulator`,
  `tools/world.py`, `tools/world_history.py`. `L2_STEPS = (("snapshot", "assetops_backend.build_structure_snapshot",
  "build"), ("observe", "assetops_backend.observe_structure", "run"))`, a module constant.
- **Inputs digest.** `world_history.py exports --manifest <definition.manifest> --out <state>/tmp/exports-<pid>`; every
  file whose name starts `<slug>.` goes to `<inputs>/<slug>/commercial/`, and `unwritten.json` is copied into each
  tenant's `commercial/` (the loader skips it, `load_emulated_exports.py:102`); any other file:
  `WORLD_INPUT_UNPLACED <name>`. Lines `"<relative path>\t<sha256>\n"` for every file under `<inputs>`, plus
  `"onboarding/<slug>.json\t<sha256 of the onboarding file>\n"` per tenant, sorted, then sha256 of their UTF-8
  concatenation. The directory is moved to `<state>/inputs/<digest12>/` (kept if it already exists; its files are
  equal by construction).
- **Clean tree.** Before any key is computed: `git status --porcelain --untracked-files=all --` over the `code` paths,
  `backend/migrations`, the definition, every onboarding file, the manifest and the derived values. Any line:
  `WORLD_TREE_DIRTY <first path>`, before any database call (strategy: "built on a clean tree").
- **Prefix and labels.** `--prefix` matches `assetops_[a-z0-9]{1,24}` (default `assetops_world`); a label matches
  `[a-z0-9]{1,20}`; every database name the tool would create, clone into, check or drop must also pass
  `permitted_database(url)` (so `walk` and `serve` are refused, D-DS3.22) and be at most 63 bytes. Else
  `WORLD_NAME_NOT_PERMITTED <name>` or `WORLD_LABEL_INVALID`, before any database call.
- **Freezing.** After a rung's last step and its census: dispose every engine on it, then `ALTER DATABASE <name> WITH
  ALLOW_CONNECTIONS false`; only then the manifest is written. The tool never connects to a frozen template: `check`
  works on a clone (§3.6). Cloning: `CREATE DATABASE <new> TEMPLATE <source> STRATEGY FILE_COPY` (Appendix A: 0.35 s
  against `WAL_LOG`'s 0.77 s), after waiting up to 5 s for the source's `pg_stat_activity` count to be 0 (else
  `WORLD_DATABASE_IN_USE <source>`).
- **Reuse and staleness.** `build` computes L0, L1, L2 keys in order; a rung whose manifest exists and whose database
  exists is reused untouched. A database of that exact name without a manifest is a partial: dropped (no sessions
  required, never `FORCE`) and rebuilt. Templates with other keys are left alone (`list` shows them, `drop` removes
  them). `clone`, `reset` and `check` use only the L2 at the current key; when none exists and another L2 manifest
  does, `WORLD_TEMPLATE_STALE <part>` names the first differing part of the most recently built L2 against today's
  parts, in the order `migrations`, `definition`, `inputs`, `code.<path>` (in the order above), `steps`; when no L2
  manifest exists at all, `WORLD_NO_TEMPLATE`.

### 3.3 The build manifest (`<state>/manifests/<database>.json`)

`<state>` is `--state` (default `/opt/assetecon/worlds`); it must resolve outside the repository (else
`WORLD_STATE_INVALID`). One file per database, written atomically (`<name>.json.tmp`, then `os.replace`), canonical
JSON, after the rung is frozen:

```json
{"format": "assetops.world-build/1", "database": "assetops_world_audit_l1_0123456789ab", "rung": "L1",
 "key": "<64 hex>", "parts": {"rung": "L1", "l0": "...", "definition": "...", "inputs": "...", "code": {"...": "..."}},
 "parent": "assetops_world_audit_l0_...", "commit": "<git HEAD>", "built_at": "<UTC ISO 8601, seconds>",
 "world": "layer4", "telemetry": {"source": "none", "reason": "DS2_NOT_BUILT"},
 "inputs_dir": "/opt/assetecon/worlds/inputs/<digest12>", "inputs": {"<relative path>": "<sha256>"},
 "key_dir": "/opt/assetecon/keys/world/<L1 database>", "tenants": {"lakeside-power": "<tenant uuid>"},
 "steps": [{"step": "L1.onboard_apply:lakeside-power", "argv": ["-m", "assetops_backend.onboard_operator", "apply", "..."],
            "seconds": 1.234, "exit": 0, "out": {}}],
 "snapshots": {"lakeside-power:2026-10": {"portfolio_snapshot_id": "<uuid>", "sites": {"KOBO-001": "<uuid>"}}},
 "census": {"<table>": 0}, "size_bytes": 0, "check": null}
```

Fields by rung: `inputs_dir`, `inputs`, `key_dir`, `tenants` from L1 on (copied down); `snapshots` from L2 on;
`check` on L2 only (§3.6), `null` until checked; a clone's manifest has `rung` `"CLONE"`, `parent`, `key` of its
parent, `check_passed` (the parent's `check.passed`, or `null`) and `seconds`. `argv` never holds a URL or a
password; `out` is the step's last stdout line parsed as JSON, or `null`. `census` is the row count of every base table
of `current_schema()` except `alembic_version` (the DS3 rule, `test_ds3_bulk_load_postgres.census`), read just before
freezing; `size_bytes` is `pg_database_size`.

### 3.4 The commands (`python tools/world.py <command>`)

Common options: `--definition` (default `backend/conversions/world-layer4-v1.json`), `--state`, `--prefix`,
`--cap-seconds` (default 3600; `bench` 7200). `main(argv, *, deps=None) -> int`; `deps` (tests only) replaces the
admin connection, the subprocess runner, the git reader, the clock and `require`. Every command except `list` first
calls `heavy_slot_check.require("world", db=True)`.

| Command | Arguments | Does | Stdout (one JSON line each) |
|---|---|---|---|
| `build` | `--key-root DIR` | §3.2 L0, L1, L2 in order, reusing current rungs | one line per rung: `{"database", "rung", "key12", "reused", "seconds"}` |
| `clone` | `--label L` | clone the current L2 into `<prefix>_audit_c_<L>` (refused if it exists) | `{"database", "rung": "CLONE", "parent", "seconds", "key_dir", "check_passed"}` |
| `reset` | `--label L` | `drop` that clone, then `clone` it again | as `clone` |
| `check` | none | §3.6 on a check clone | one line per check, then `{"check": "ALL", "state"}` |
| `list` | none | read manifests and `pg_database` | one line per manifest: `{"database", "rung", "key12", "parent", "built_at", "exists", "check_passed"}` |
| `drop` | `--database NAME` | drop one database the tool built (below) | `{"database", "dropped": true}` |
| `bench` | `--key-root DIR --evidence DIR` | §4 | the report's path and its `ds7` block |

`--key-root` must exist, be a directory with mode `& 0o077 == 0`, and resolve outside the repository
(`WORLD_KEY_ROOT_INVALID`). L1 creates `<key-root>/<L1 database>/` (mode 0700) and passes it to every L1 and L2 step
as `ASSETOPS_PSEUDONYM_KEY_DIR`; clones share it (same tenant ids; the key is never copied, runbook step 3).

**`drop`.** The name must match `<prefix>_audit_(l0|l1|l2)_[0-9a-f]{12}` or `<prefix>_audit_c_[a-z0-9]{1,20}` and
have a manifest (`WORLD_UNKNOWN_DATABASE`); no manifest names it as `parent` while that child's database exists
(`WORLD_HAS_DESCENDANTS <child>`); its `pg_stat_activity` count is 0 (`WORLD_DATABASE_IN_USE`). Then, for an L1, per
tenant `python -m assetops_backend.commercial.pseudonym_key erase --dir <key_dir> --tenant-id <id>` (runbook step 7;
the directory and its tombstones stay for the coordinator); then `DROP DATABASE <name>` (never `WITH (FORCE)`); the
manifest is removed last.

**Exits.** 0 done; 2 refused before any database change (`<CODE> <detail>` on stderr, codes below); 3 a step failed
(`STEP_FAILED <database> <step> <exit>`; that rung gets no manifest and is a partial next time); 4 `check` found a
FAIL; 5 the cap was reached (`WORLD_CAP_EXCEEDED <step>`; the running child was killed by its own PID, no manifest).
Refusal codes: `WORLD_NOT_IN_SLOT` (from `require`, exit 69 as T1 defines; not remapped), `WORLD_DEFINITION_INVALID`,
`WORLD_TREE_DIRTY`, `WORLD_STATE_INVALID`, `WORLD_KEY_ROOT_INVALID`, `WORLD_NAME_NOT_PERMITTED`, `WORLD_LABEL_INVALID`,
`WORLD_INPUT_UNPLACED`, `WORLD_NO_TEMPLATE`, `WORLD_TEMPLATE_STALE`, `WORLD_CLONE_EXISTS`, `WORLD_UNKNOWN_DATABASE`,
`WORLD_HAS_DESCENDANTS`, `WORLD_DATABASE_IN_USE`, `WORLD_EVIDENCE_IN_REPO`. Diagnostics for the coordinator only;
nothing here is served.

### 3.5 Steps, connections and environment (D-DS4.3, D-DS4.4)

- **Admin connection.** `postgresql+psycopg://assetops:<ASSETOPS_PG_PASSWORD, default assetops-local-dev>@127.0.0.1:
  <ASSETOPS_PG_PORT, default 55432>/postgres`, `NullPool`, `AUTOCOMMIT`. It runs only: `CREATE DATABASE "<n>"`
  (optionally `TEMPLATE "<s>" STRATEGY FILE_COPY`), `ALTER DATABASE "<n>" WITH ALLOW_CONNECTIONS false`, `DROP
  DATABASE "<n>"`, and `SELECT`s on `pg_database` and `pg_stat_activity`, each on a name that passed §3.2's rule. A
  rung's own URL is the same with its database name; the tool connects to a rung only before freezing it (census,
  tenants: `SELECT id, slug FROM tenant`) and to a check clone (§3.6).
- **Product steps** run as `subprocess.run([sys.executable, *argv], cwd=<repo>, env=E, capture_output=True,
  text=True, timeout=<cap left>)`, except the migration (`cwd=<repo>/backend`, argv `-m alembic upgrade head`). `E` is
  built, never inherited: `PATH`, `HOME`, `LANG` copied when set; `PYTHONPATH=<repo>/backend:<repo>/contracts:
  <repo>/simulator`; `DATABASE_URL` the rung's URL; `ASSETOPS_TENANT_SLUG` the step's tenant; `ASSETOPS_PSEUDONYM_KEY_DIR`
  the L1 key directory (from L1 on); `ASSETOPS_PG_PORT`, `ASSETOPS_PG_PASSWORD` copied when set. Nothing else: no
  `PGDATABASE` or other `PG_TARGET_ENV` variable, and no `ASSETOPS_REAL_OPERATOR_DATA` (unset means off,
  `commercial/composition.py:56`). A step's exit is not 0: exit 3.
- **The steps, exactly:** L1 per tenant `-m assetops_backend.onboard_operator digest --file F` (stdout: the digest),
  `check --file F --key-dir K`, `apply --file F --key-dir K --confirmed-digest D`; then per tenant `-m
  assetops_backend.load_world_inputs --world <inputs_dir> --tenant S --submit-as A --accept-as B` (its stdout line's
  `commercial_exit` must be 0 and `batches` 0 while telemetry is none). L2 per tenant and month `-m
  assetops_backend.build_structure_snapshot build --tenant S --month M --by <built_by>` (its line gives
  `portfolio_snapshot_id` and `sites` for the manifest), then `-m assetops_backend.observe_structure run --tenant S
  --month M`.

### 3.6 `world check` (D-DS4.8)

Refused (exit 2) without a current L2 (§3.2). Creates `<prefix>_audit_c_check` from it (a leftover of that name is
dropped first under `drop`'s rules), runs every check below (all of them; no stop at the first FAIL), drops the check
clone in `finally`, writes the L2 manifest's `check` block `{"at", "commit", "derived_values_sha256", "passed",
"checks": [<the lines>]}`, prints one line per check `{"check": "C<n>", "state": "PASS"|"FAIL", "detail"}` and exits 0
or 4.

| Check | Passes when |
|---|---|
| C1 inputs | A fresh `exports` run, placed by §3.2's rule, gives exactly the L1 manifest's `inputs` map (a differing, missing or extra file is named) |
| C2 census | The check clone's census equals the L2 manifest's `census`, table by table (each differing table named with both counts) |
| C3 rebuild | For each tenant and month, `build_structure_snapshot verify --tenant S --snapshot <portfolio_snapshot_id>` on the check clone exits 0 with `"matches": true` (else its `differences` are named) |
| C4 oracle | The rule below: no mismatch, and at least one equal value |
| C5 parity | `pwsh -NoProfile -File tools/run-host-tests.ps1 -- backend/tests/test_ds3_parity_postgres.py` exits 0 (run with the tool's own environment, `DATABASE_URL` removed; it makes its own harness clones) |
| C6 batches | Every `*.batch.json` under the inputs satisfies §3.7's rule at its Site's timezone read on the check clone; with none, PASS with detail `0 batches (telemetry none)` |
| C7 steps | Every step recorded in the L0, L1 and L2 manifests has exit 0 |

**The oracle rule (C4).** Read in-process through `structure_snapshot.composition.build_structure_snapshot(url)`:
`store.get(tenant_id, <the manifest's Site snapshot ids>)`, `codec.payload_of(row)` per row. For each Site row, with
`name = definition.sites[payload["site_code"]]`, `expected = derived_values["sites"][f"{slug}/{name}"]`; compare
side `actual` (`payload["actual"][f]["value"]` with `expected["actual"]["nodes"][f]`) and side `plan`
(`payload["targets"]["values"][f]["value"]` with `expected["plan"]["nodes"][f]`), for every factor `f` in the
payload's side. Each is: `not_available` when the product value is `None` (never equal to anything, zero included:
unknown is not zero); `unchecked` when `f` is not in the expected nodes; `equal` when `Decimal(product) ==
Decimal(repr(expected))`; `mismatch` otherwise (no tolerance). Expected nodes the payload lacks are listed
`not_in_product`. Detail: the four counts per side, then every mismatch as `<slug>/<code> <side>.<f> product=<v>
expected=<v>`, then the `not_available` factors. The portfolio row is not compared (it is composed from the Sites;
the stated limit).

### 3.7 The gap-day rule in the bulk load (D-DS4.9; D-DS3.21)

In `evidence/bulk_load.py`:

```python
def local_days(envelope_texts: Sequence[str], timezone: str) -> list[date]   # sorted, distinct
def first_gap(days: Sequence[date]) -> date | None                         # first day missing between min and max
```

Per envelope: `doc = json.loads(text)`; `timing = doc["timing"] if "timing" in doc else doc` (v4 nests it, v3 does
not); `at = timing.get("interval_start") or timing["source_time"]`; the day is
`datetime.fromisoformat(at.replace("Z", "+00:00")).astimezone(ZoneInfo(timezone)).date()`. New step **3a** in
`BulkEvidenceLoad._one`, right after step 3 (the principal is known): `timezone = self.ledger.site_timezone(site_id)`
(cached per Site for the load; `None` refuses `BULK_UNKNOWN_GATEWAY`); a gap refuses `BULK_BATCH_GAP_DAYS <batch id>
"<first>..<last> lacks <gap>"`, nothing written or recorded, earlier batches staying (the load's rule). The code joins
`BULK_LOAD_REFUSALS`; `load_world_inputs` passes it through as every other `BulkLoadRefused` (exit 2).
`PostgresEvidenceLedger.site_timezone(site_id: UUID) -> str | None` sits beside `gateway_principal` ("DS3 bulk
admission" section): `SELECT timezone FROM site WHERE id = :s`, through `self._run`. One-day and contiguous batches
(the DS3 parity days, the v4 batch, every Kobo bench day) pass unchanged.

## 4. The re-benchmark (unit 3; D-DS4.11)

`world bench --key-root DIR --evidence DIR`: `--evidence` must resolve under `/opt/assetecon/evidence/` or outside
the repository (tests), never inside it (`WORLD_EVIDENCE_IN_REPO`). It records the start (`os.getloadavg()`, the first
line of `tools/heavy-slot.sh --status`, `git rev-parse HEAD`), then:

| # | Stage | Measured as |
|---|---|---|
| B1 | A cold ladder under prefix `assetops_worldbench` (any earlier bench databases dropped first, children before parents) | each step's `seconds` from the three manifests; each rung's total and `size_bytes` |
| B2 | Three clones of the bench L2 (labels `b1`, `b2`, `b3`), then dropped | wall seconds of each `CREATE DATABASE ... TEMPLATE`, and the clone's `pg_database_size` |
| B3 | One late commercial record on a clone `bl`: a one-row `lakeside-power.billing.csv` in a fresh directory (the generated file's header and its first `KOBO-001` row with `Revision` `2` and `Amount` plus `10.00`, two decimals), submitted and accepted by `load_emulated_exports` (Wanjiru, Joseph), then `build_structure_snapshot build` and `observe_structure run` for 2026-10 | seconds per step and in total; `revenue_delta` = the new Kobo snapshot's `actual.revenue` less the L2 one's (expected `10.00`; any other value or a refusal is recorded as found and goes to the Architect) |
| B4 | An option change; a contract-term edit | not built: rows `{"kind": "option_change", "state": "NOT_BUILT", "unit": "6a"}` and `{"kind": "contract_term_edit", "state": "NOT_BUILT", "unit": "9a0"}` |
| B5 | The telemetry pipeline on the bench slice: `ASSETOPS_DS4_BENCH=1 pwsh -NoProfile -File tools/run-host-tests.ps1 -- backend/tests/test_ds4_bench_pipeline_postgres.py -s`, its `DS4_PIPELINE {json}` line parsed | below |
| B6 | Projection and DS7 | `per_site_day_seconds = (load_seconds + tick_wall_seconds) / site_days` from B5; `projected_l2_seconds = <B1 L2 total> + per_site_day_seconds × projection.sites × projection.days`; `ds7 = {"threshold_seconds": 2700, "measured_l2_seconds", "projected_l2_seconds", "triggered": projected > 2700, "basis": projection.basis}` |

Finally every bench database is dropped (`finally`), and the report goes to `<evidence>/bench.json` (format
`assetops.world-bench/1`: `start`, `ladder`, `clones`, `changes`, `pipeline`, `projection`, `ds7`, and `targets`, one row
per strategy §4 operation: inputs "under 1 min" against B1's L1 total; L2 "under 45 min" against B1's L2 total and the
projection; a run's database "under 10 s" against B2; a one-option change "about 2 min" `NOT_BUILT`; advance one day
`NOT_BUILT` (`DS6`)).

**The pipeline bench (`test_ds4_bench_pipeline_postgres.py`; marked `slow`, skipped unless `ASSETOPS_DS4_BENCH=1`).**
`seed, kit, _ = seed_database("ds4pseed", relabel=True)` (DS3's seed, relabelled `minigrid-roles-4` so mini-domain
jobs exist); `pipe = clone_database("ds4ppipe", seed)`; `batches = kobo_days(kit, [DAY6 + timedelta(days=d) for d in
range(14)])`; time `BulkEvidenceLoad(build_evidence_ledger(pipe)).load(batches)`; enrol the Site (`-m
assetops_backend.scheduling.run enrol --tenant-id T --site-id S --by service:ds4-bench`, subprocess, `DATABASE_URL`
`pipe`); then ticks, each `tools/demo_combined.py`'s `TICK` arguments plus `--no-prebuild`, as a subprocess: after each,
`demo_combined_drain.counts(pipe)`, with `n = n_for(<counts before the first tick>)` and `step(history, ticks, n)`
deciding; stop on `done` or `fail`, or after 200 ticks (`fail`, "tick cap"). Per tick: wall seconds and the stderr
`assetops.perf {json}` line's per-stage `elapsed_ms` for the Site, summed per stage. Prints `DS4_PIPELINE ` + canonical
JSON `{"site_days": 14, "batches", "envelopes", "load_seconds", "ticks", "tick_wall_seconds", "stage_ms": {stage: ms},
"drain": {"verdict", "reason"}}`; drops both clones in `finally`. It asserts nothing about time; a `fail` verdict is
reported, not hidden.

**What the numbers mean** (the packet states each). Seconds are wall clock of one run on this VPS, subprocess start-up
and Python imports included, `synchronous_commit` at the server default; one sample each, not a distribution
(Appendix A's repeat agreed within 10 in 100, so read differences under that as noise). They describe this world:
one tenant, three Sites, one month, no telemetry; L1 and L2 here are not the strategy's full world. B5 is a flat
fixture Kobo with hand rows, not the world's physics; its stage split shows where time goes, its total gives the
per-Site-day figure. B6's projection is arithmetic on a measurement, never a measurement: it is labelled so in the
report and the packet. Nothing in §4 is a gate; no test asserts a time.

## 5. Tests (written first)

**No database** (`backend/tests/test_ds4_world.py`; imports `tools/world.py` by `sys.path` as
`test_demo_combined_finish_rows.py` does; fakes for admin, runner, git, clock, `require`):
- **T1 definition.** The repository file parses. Each breach of §3.1 (an unknown key, a slug with a capital, a missing
  onboarding file, months unsorted, `built_by` `system`, the same email twice, `telemetry.source` `"simulator"`)
  gives `WORLD_DEFINITION_INVALID` naming its path. **T1b (independent, W2):** read the manifest YAML with
  `yaml.safe_load` and `derived-values.json` with `json`, never through `tools/world.py`: the definition's tenants
  plus `not_built` equal the manifest's tenant list; each tenant's `sites` equals the manifest's `code: site` pairs;
  every `<slug>/<site>` is a key of `derived_values["sites"]`.
- **T2 keys.** On a temporary git repository holding stub files at every keyed path: changing `backend/migrations`
  changes key0 and therefore key1 and key2; changing the definition bytes, an input file, an onboarding file or each
  `code` path changes key1 and key2 only; changing `L2_STEPS` (monkeypatched) changes key2 only. One fixed parts dict
  hashed by hand in the test equals `key(parts)`. `stale_part` names the first differing part in §3.2's order.
- **T3 clean tree.** An untracked file under `backend/assetops_backend`, or a modified definition: `WORLD_TREE_DIRTY`
  naming that path, and the recording admin saw no statement.
- **T4 names.** Rung and clone names have §3.2's form and at most 63 bytes, and each passes `permitted_database`.
  Prefixes `assetops_walk1`, `Assetops_x`, `assetops_` + 25 letters, and the label `walk1` are refused
  (`WORLD_NAME_NOT_PERMITTED` or `WORLD_LABEL_INVALID`) before any admin statement. `drop` of `assetops_test`,
  `assetops_polish_walk1113_test` and of a well-formed name with no manifest: `WORLD_UNKNOWN_DATABASE`.
- **T5 build.** With fakes, a cold build issues exactly the admin statements and step argvs written in the test as
  literals, in order (L0 create, migrate, census, freeze; L1 clone, three onboarding steps, load, census, freeze; L2
  clone, snapshot, observe, census, freeze), and writes three manifests with §3.3's fields. Every product step's env
  is exactly §3.5's set, even with `PGDATABASE`, `PGHOST` and `ASSETOPS_REAL_OPERATOR_DATA=on` set in the parent. A second build
  runs no step and reports `"reused": true` three times. A database of the L1 name with no manifest is dropped and
  rebuilt. A step exiting 3: tool exit 3, `STEP_FAILED`, no manifest for that rung. A runner raising
  `TimeoutExpired`: exit 5, no manifest. No admin statement contains `FORCE`.
- **T6 clone, reset, drop.** `clone` with no L2: `WORLD_NO_TEMPLATE`; with only an L2 at another `code` tree:
  `WORLD_TEMPLATE_STALE code.backend/assetops_backend`; an existing label: `WORLD_CLONE_EXISTS`; the clone manifest
  has `parent` and `check_passed`. `drop` of L0 while L1 exists: `WORLD_HAS_DESCENDANTS`; with a session counted:
  `WORLD_DATABASE_IN_USE`, nothing dropped; dropping an L1 runs `pseudonym_key erase` once per tenant before `DROP
  DATABASE`, and the manifest goes last. `reset` drops then clones.
- **T7 slot.** Every command but `list` calls `require("world", db=True)` before anything else; `list` does not.
- **T8 the gap rule (pure).** `local_days` and `first_gap` at `Africa/Addis_Ababa`: `2026-10-06T10:00:00Z` and
  `2026-10-07T22:00:00Z` give days 6 and 8, gap 7 (contiguous in UTC: the plant P7 case); `06T10:00Z` and
  `07T10:00Z` give 6 and 7, no gap; one envelope: no gap; a v4 envelope's nested `timing`; an interval reading's
  `interval_start` used over its `source_time` (an interval `23:45Z` to `00:00Z`).
- **T9 check.** With fakes for the check clone: a changed input file fails C1 naming it; a census differing in one
  table fails C2 naming it with both counts; `verify` exiting 4 fails C3; the oracle on hand payloads: equal values
  pass, a plan-side mismatch fails (named), a `None` product value against expected `0.0` is `not_available`, never
  equal, and a payload with only `not_available` values fails (no equal value); parity exiting 1 fails C5; no batches
  passes C6; any FAIL gives exit 4 and `passed: false` in the L2 manifest; a later `clone` carries `check_passed:
  false`; the check clone is dropped even when a check raises.
- **T10 bench assembly (pure).** From literal stage records and a literal `DS4_PIPELINE` line, the report's
  `projection` and `ds7` equal hand-computed numbers (one case above 2700 s, one below); the two `NOT_BUILT` rows and
  the five `targets` rows are present; an evidence directory inside the repository is refused.
- **T11 seams (an `ast` and text scan).** `tools/world.py` holds no `INSERT`, `UPDATE`, `DELETE`, `COPY`, `TRUNCATE`
  or `FORCE` literal, and every SQL literal matches one of §3.5's shapes; it imports no `*_api` module and no
  adapter module; no `main.py` or `*_api.py` imports `bulk_load`; `bulk_load.py` still imports no simulator, host or
  commercial module.

**Postgres, the tool for real** (`backend/tests/test_ds4_world_postgres.py`; prefix `assetops_ds4t<secrets.token_hex(4)>`,
temporary key root (0700) and state; the git reader injected with this checkout's `HEAD` tree ids so a dirty build tree
does not refuse; the parity runner injected to return exit 0, since C5 is the DS3 file the regression set runs anyway;
a module `finally` drops, through the tool, every database with the prefix, children first, then sweeps any left
`<prefix>_audit_%`):
- **T12 build, clone, check.** A cold `build` makes three databases, each `datallowconn` false; L1's census holds
  `tenant` 1 and `site` 3, `commercial_record` above 0, `accepted_evidence` 0; L2's census holds `structure_snapshot`
  4 (three Sites and the portfolio row) and the observe step's exit 0. A second `build` creates nothing. `clone
  --label t1`: its census equals L2's. `check`: C1, C2, C3, C4, C6 and C7 PASS (C4's detail lists its counts; a
  mismatch here is a finding for the Architect, never a loosened rule).
- **T13 drop order.** Dropping L0 is refused while L1 exists; dropping the clone, L2, L1 (its tenant's key file is
  erased: `key_state` reports it so) and L0 leaves no database and no manifest with the prefix.
- **T14 in use.** With a session open on clone `t2`, `drop` exits 2 `WORLD_DATABASE_IN_USE` and the database still
  exists.

**Postgres, the gap rule** (`backend/tests/test_ds4_batch_days_postgres.py`; a module seed `seed_database("ds4g")`, a
fresh `clone_database(f"ds4g{n}", seed)` per case, dropped in `finally`; envelopes `kit.envelope("pv-inverter-controller",
seq, 0, "1.5", source_time=T)` with `seq` from 900001, sealed by `kit.seal(texts)`):
- **T15** times `2026-10-06T10:00:00Z`, `2026-10-07T22:00:00Z`: `BulkLoadRefused` `BULK_BATCH_GAP_DAYS`, detail
  naming `2026-10-07`; every ledger table's count unchanged (DS3 test 6's list).
- **T16** times `2026-10-06T10:00:00Z`, `2026-10-07T10:00:00Z`: `BulkLoaded(1, 0, 2)`.
- **T17** through `load_world_inputs.main` with a world `<tmp>/demo/telemetry/` holding `a.batch.json` (T16's) and
  `b.batch.json` (T15's): exit 2, stderr starting `BULK_BATCH_GAP_DAYS <b's batch id>`; `a` stored, `b` not.

**Regression:** `test_ds3_bulk_load.py`, `test_ds3_bulk_load_postgres.py`, `test_ds3_parity_postgres.py` (the v4
batch and the Kobo days pass the gap rule), `test_pg_harness.py`, the ON1, 3A3, 3B7a and 3B4 command tests;
`select-tests --base main` before review; fast check-all once at the end.

## 6. Units

| Unit | Content | Commits |
|---|---|---|
| 1 (1.25) | §3.1 to §3.5: the definition file, keys, names, the admin and runner, `build`, `clone`, `reset`, `drop`, `list`, manifests; T1 to T7, T11, T12 (without its `check` call), T13, T14 | 2 |
| 2 (0.75) | §3.6 `check`; §3.7 the gap rule and `site_timezone`; T8, T9, T12's `check`, T15 to T17; regression | 1 |
| 3 (0.75) | §4 `bench` and the pipeline bench; T10; the real runs (below); check-all; packet | 1 |

Total 2.75 (plan 2.5; D-DS4.14). **Unit 3's real runs**, each `tools/heavy-slot.sh --db --label ds4 -- <command>`, on
a quiet machine, in this order: (1) `python tools/world.py bench --key-root /opt/assetecon/keys/world --evidence
/opt/assetecon/evidence/DS4/<run>`; (2) `python tools/world.py build --key-root /opt/assetecon/keys/world` (the
`assetops_world` ladder WK starts from; kept); (3) `python tools/world.py check`. Packet `specs/DS4-template-ladder/
packet.md`: the bench report's figures with §4's meaning beside each, the `ds7` block, the three kept template names
with their keys and sizes, the check's lines, the clones made and dropped, the mid-build count, residual risk.

## 7. Done (questions; each can fail)

1. Does `build` reuse a rung only at an unchanged key, rebuild a partial, and do `clone`, `reset` and `check` refuse a
   stale or absent L2 naming the changed part (T2, T5, T6)?
2. Does every write into a world go through the product's commands with §3.5's environment, into names that pass
   `permitted_database`, with the admin connection running only §3.5's statements and never `FORCE` (T4, T5, T11)?
3. Is a template frozen before its manifest exists, never connected to afterwards, and dropped only without
   descendants or sessions, with its tenants' keys erased first (T5, T12 to T14)?
4. Does `check` fail on each of: a changed input, a dirtied census, a snapshot that does not rebuild, a figure unequal
   to the independent model (a missing value never counting as equal), a parity break; and pass on the real world
   (T9, T12)?
5. Is a world batch with a gap in its Site-local days refused before admission, with one-day batches unchanged (T8,
   T15 to T17, the DS3 regression)?
6. Does the bench report every §4 stage with its meaning, state the operations it could not measure as `NOT_BUILT`,
   and give the projection as a projection (T10, the packet)?
7. Does each plant of `reviewer-guide.md` fail its named test, and is the mid-build count 0?

## 8. Out of scope

World telemetry and its Site configuration (D-DS4.1; `DS2` and the queued configuration unit); the enrol, tick and
drain steps in L2 (added with the first world telemetry; measured here only); cold-chain and EV parity slices
(D-DS4.2); the world's history months and DS1b canonical files (D-DS4.6: the world loads the emulated exports, as the
runbook says a rehearsal tenant must); 3A7 statements and 3C2 Actions as L1 steps (each joins the L1 step list, and
so the key, in the unit or in `WK` when merged); the story clock, `advance` and after-branches (`DS6`); serving any
world database, and the walkthrough copy (held, D-DS4.13); `COPY` (D-DS3.1); pack edits (delivery §5's targets are
replaced by the coordinator's pack change from the packet's numbers).

## 9. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 (owner) | Where does the world's telemetry come from this fortnight? | Nowhere yet: only the world generator's telemetry writer (`DS2`), never the walkthrough build, a test fixture or a copy; telemetry-fed figures read "Not available yet" (D-DS4.1; row 33; owner to weigh in) |
| Q2 (owner) | Who declares the world Sites' gateways, sources and binding sets, without which no telemetry can be accepted at them? | A queued unit before `DS2`'s telemetry writer, about 1.5 units, through the product's import and conversion path (as `kobo-001-bindings.json` today) from the manifest's `physical` blocks (D-DS4.1; row 33) |
| Q3 (owner) | Cold-chain and EV parity slices: DS4 (as D-DS3.11 said) or with their telemetry? | With the unit that first writes their telemetry; `BULK_SITE_TYPE_UNPROVEN` stays (D-DS4.2; row 34) |
| Q4 (owner) | DS7's trigger ("L2 above 45 minutes"): on this telemetry-free L2, or on the projection for the world with telemetry? | On the projection, labelled as one, reported to the owner; re-measured by `world bench` at the first world telemetry (D-DS4.12; row 35; owner to weigh in) |
| Q5 (owner, held) | How the walkthrough serve reaches a world built into `assetops_world_audit_*` | **Held** (D-DS4.13; row 36; D-DS3.12). Options and the Architect's recommendation are in the ruling; nothing is built for it |
| Q6 | The real-path slice in every world build (strategy §4) | Inside `world check` (C5) at the harness Site, never in the world (D-DS4.7) |
| Q7 | Which tenants the world builds this fortnight | Those with an onboarding file: Lakeside only; Harvest Cold and Metro Bus listed `NO_ONBOARDING_FILE` (RC5: mini-grid first) (D-DS4.6) |
