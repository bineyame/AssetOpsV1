# 3A3 review, round 1 (discovery, W5)

Fresh Claude reviewer, 2026-11-20. Branch `task/3A3-emulators`, head `05f8a41ae`, worktree `/opt/assetecon/AssetOpsV1-3a3`
(read only). Base `3b3916d4f`; `main` is now `d5af18b80` (one Docs-only commit), and `git merge-tree` merges it cleanly.
Judged against `spec.md` rev 2, `rulings.md` D-3A3.1 to D-3A3.12 with the handshake answers, `reviewer-guide.md` rev 2,
and owner RC4.

## Summary (round 1)

- **Verdict: ACCEPT WITH FINDINGS FIXED ON THE BRANCH.** There are three Medium findings (F1 to F3) and no High.
- The RC4 refusal holds. The loader refuses on `database_target` before any connection or service call. The
  no-connect fixture and the spies hold, and no Postgres test names an `assetops_op` database.
- One writer holds. S1 passes, `build_commercial_records` is gone, and nothing outside `commercial/uploads.py` calls
  ingest.
- Honesty holds today. An independent re-total of the emulated files equals the manifest for every Kobo, Kisiwa and
  Mto actual and plan figure. Kisiwa O&M is absent, not 0. Provenance follows the database: `source-emulated` off
  operator databases, so emulated data is never `observed-financial` there.
- **F1 (Medium, rights).** A person can submit in one run and then accept their own uploads in a second run through
  `ALREADY_WAITING`. Confirmed with a probe.
- **F2 (Medium, contract suite).** The suite admits a reader that silently drops short rows or rows holding a control
  character. Confirmed with a plant: 174 passed.
- **F3 (Medium, D2).** The budget `tariff` and `diesel_price` lines come from the price list that also prices the
  actuals. Nothing checks them against the plan. The spec gap was resolved without a mid-build question.
- Deviations: D1, D3, D4, D5 and D6 are sound. D2 is a workaround (F3).
- Checks I reran: 3A3 focused files 154 passed; Postgres P1 to P3 4 passed (0 skipped); architecture passed; agent
  workflow passed. My own plants: B and C fail their tests; A exposes F2.

## Findings

### F1 (Medium, acceptance gap: rights, D-3A3.11) The submitter can accept their own upload across two runs

`backend/assetops_backend/load_emulated_exports.py:157`, `:163` to `:172`, `:186`.

`PERSON_SAME_FOR_BOTH` compares only this run's `--submit-as` and `--accept-as`. A waiting upload found by SHA-256
(`ALREADY_WAITING`) is then decided by `--accept-as` without checking who submitted it. 3A2's `decide` does not stop
this either (handshake R8).

Probe, on a scratch worktree with 3A2's in-memory world:
1. Run 1: `--submit-as fiona` with no `--accept-as` gives 4 × WAITING.
2. Run 2: `--submit-as ana --accept-as fiona` gives exit 0 and 4 × ACCEPTED.
3. Every upload has `submitted_by == decided_by == Fiona`.

Fiona holds FINANCE, which may both upload and decide. This defeats the separation D-3A3.11 adds for OD-15
("acceptance as the person's"), and the JSON line hides it.

**Fix.** Add `submitted_by` to `HeldUpload` (one more column in `_HELD` and in the memory mirror). With `--accept-as`,
an `ALREADY_WAITING` upload whose submitter is the acceptor is `PERSON_SAME_FOR_BOTH`, exit 2, before any decision. Add
an L6 case for it.

Class: every scripted decide. Sweep: `decide(` callers outside routes (only the loader today).

### F2 (Medium, acceptance gap: the contract suite cannot refuse a row-losing reader) Spec §7 q2 and q3, D-3A3.5

`backend/tests/test_3a3_source_contract.py:136`, `:206`.

Plant A changed `LayoutReader.read` to drop every row the engine refused as `NATIVE_ROW` or `NATIVE_CHARACTER`, and to
renumber the rest. The contract suite, the loader file, the engine contracts and the 3A2 service file still passed:
**174 passed**.

C1 to C10 never send a short row or a control character through a reader. Only the engine tests (contracts 2 and 3)
do, and they test `read_layout`, not the reader under admission. This suite is the admission gate for `3A6` and
every real adapter (§7.3), so a profile reader that silently loses bad rows would be admitted, and the month would be
short with no refusal shown.

Related: the suite also admits vacuously. A case with fewer `required_headers`, or with `mapped=None`, passes C3 and
C8 on less.

**Fix (class).**
- C8 gains, for every case, row 3 with one cell fewer (`NATIVE_ROW`, field "row 3") and row 3 holding a NUL
  (`NATIVE_CHARACTER`, "row 3"). Each refuses row 3 alone, with counts `(3, 2, 0, 0, 1)`.
- C1 asserts that `counts.records` equals the golden's data rows.
- C3 gains the complement: every header not in `required_headers`, blanked, keeps row 2. The case then fully states
  which cells are required.

Re-plant A to confirm.

### F3 (Medium, D2: a workaround that can make a target echo the actual) Spec §2.5 budget lines, E6

`simulator/assetops_simulator/world/exports.py:43` to `:44`, `:233` to `:235`.

Spec §2.5 reads `tariff_usd_per_kwh` and `diesel_usd_per_l` from the plan, which holds no such fields. The builder
took them from `tenant.prices`, the same table `_charges` and `_fuel_records` use to price the **actuals**. The
budget unit-price lines therefore equal the actual unit prices by construction.

On today's manifest this is honest in value. I checked by hand: plan revenue ÷ plan kWh and plan diesel cost ÷ plan
litres equal the price list at all three Sites (0.40/1.25, 0.55/1.30, 0.40/1.25). But nothing enforces it. On a
manifest whose plan price differs from the price paid (a fuel-price rise is a natural demo story), the budget would
carry the actual price. That hides the price variance and contradicts the budget's own `fuel_cost = diesel_l ×
diesel_price`.

The line also changes how 5a labels the figure. Without a line, `tariff` and `diesel_price` are `AT_ACTUAL` ("taken at
this month's actual … (assumption)", `structure/targets/rules.py:37`). With D2's line they read as "Budget line for
the month", a stated target, while the value is the actual's price.

This was a spec gap (§2.5 names fields that do not exist). It should have gone to the Architect as a mid-build
question (RULES §4 item 7), but the packet records 0.

Smaller point: a missing price is listed as `PLAN_FIELD_ABSENT`, which names the wrong source.

**Fix.**
- Have the Architect rule on the source (D-3A3.13).
- Either derive the lines from the plan (`revenue / billed_kwh`, `diesel_cost / diesel_l`, with an exact-cents
  check), or keep the price list and stop with `EMU_PLAN_PRICE <tenant>/<site> <field>` unless price × plan quantity
  equals the plan money.
- Add an E8 plant for it (for example, Kobo plan `diesel_cost` 876.0).
- Give a missing price its own reason (`PRICE_ABSENT`).

### F4 (Low) S1 misses an aliased `build_commercial_uploads`

`backend/tests/test_3a3_single_writer.py:65`.

The caller rule matches the called name only, so `from ...composition import build_commercial_uploads as b; b(url, s)`
passes. The `CommercialRecords` rule catches aliases at import, but this one does not, and this allowlist is what
forces new callers to call `refuse_operator_database` first (§2.1).

**Fix:** flag any import of the name `build_commercial_uploads` outside `BUILD_CALLERS`, and add an alias source to
`PLANTED`.

### F5 (Low) RC4 on the un-injected path is held only by code order

`backend/tests/test_3a3_load_emulated.py` (L1).

Every L1 case injects `uploads` and `accounts`, so no test runs `main()` through the composition with an operator URL.
Today step 2 precedes step 3, and the composition opens no connection, so the guarantee holds by reading.

Spec §2.6 also makes the URL check independent of `ASSETOPS_REAL_OPERATOR_DATA`. With that switch `on`,
`commercial_upload_settings` admits an `assetops_op_<name>` database, so step 2 is the only stop.

**Fix:** one L1 case with `uploads=None, accounts=None`, `ASSETOPS_REAL_OPERATOR_DATA=on` and URL
`…rc4.invalid:1/assetops_op_x`. Expect exit 2 `EMULATED_ON_OPERATOR_DATABASE`, with the no-connect fixture in force.

### F6 (Low, residual for 3A6) `_path` treats every non-canonical reader as one path

`load_emulated_exports.py:119`.

`EXPORT_PATH_SWITCHED` only tells `canonical-json-v1` from "native". Once `3A6` registers profile readers (another
`source_system`), a tenant could hold an expense ledger from a profile and from the illustrative layout without being
refused. That double-counts O&M and staff, which is D-3A3.7's own reason.

**Fix (with 3A6 or now):** compare the reader's layout or `source_system`, not native against canonical. Otherwise
record it as a 3A6 residual.

## The probes the dispatch asked for

- **RC4 safety: holds.**
  - `refuse_operator_database` is `database_target` then `is_operator_name`, and is called first after
    `DATABASE_URL` (`load_emulated_exports.py`, `_run`). `make_url` is never used.
  - L1 covers three operator names (any case), `?dbname=`, `/?dbname=`, an empty name, `?service=` and `PGDATABASE`.
    The spies stay untouched.
  - The no-connect fixture is self-tested. Every URL uses `rc4.invalid:1`.
  - The Postgres file asserts that its routed name ends `_test` and does not start `assetops_op`. (F5 is the one gap.)
- **Intake path: holds.**
  - The loader calls only `CommercialUploads.submit`, `.get`, `.decide` and `.held`.
  - S1 is green and catches its seven planted sources.
  - In `world/exports.py` and `tools/world_history.py`, I grepped for `.ingest(`, `CommercialRecords(` and
    `build_commercial_records` and found none.
  - The emulator's records reach tests only through files (D4, via a child process).
- **Honesty: holds today (F3 is latent).**
  - My own re-total: every actual and plan field equals the manifest exactly, for billed kWh, revenue, collected, in
    transit, fuel cost, O&M and staff, and for plan revenue, fuel cost, kWh, litres, O&M and staff.
  - The only gap is Kisiwa O&M, which is ESTIMATED and therefore absent.
  - `outstanding` is re-reasoned `AS_UNPAID_CHARGES`.
  - Provenance follows `ReadContext.real_data`, and C10 asserts both sides.
  - `ORIGIN_ORDER` and `PROVENANCE_ORDER` carry `source-emulated` through the reads, so an emulated figure keeps its
    origin and is never stored as `observed-financial` off an operator database.
- **NATIVE_CHARACTER: correct.** The set is exactly D-3A3.9's. Tab, CR and LF are text. A header holding one fails
  the exact match. Contracts test 2 pins NUL, U+001F and U+007F as refusing that row alone. The service-level gap is
  F2. Residual: C1 controls (U+0080 to U+009F), U+FEFF in mid-cell and U+2028 are not refused, so an invisible one in
  a reference would still give one customer two pseudonyms. This is outside the ruling.
- **Rights.**
  - Same-run submit and accept is refused, and `decided_by_script` is written.
  - The roles come from `roles_of`, and only SITE_MANAGER is Site-scoped, so ignoring the grant's Site is safe.
  - The gap is F1.
- **Held-uploads read: correct.**
  - The SQL matches §2.8, and the memory mirror matches it.
  - P3 pins "declined absent, one waiting". My plant C (drop the decision filter) fails P3 with `6 == 5`.
  - The loader reads it once, before any submission. My plant B (count accepted uploads as waiting) fails L2.
  - The organisation-path `get` residual is stated in the packet.
- **Contract suite:** it refuses a reader that ignores mapping, reorders headers, hard-codes records, drops the
  pseudonymised class or fixes the provenance (the builder's V5, V6, V11, V12 and V16). It cannot refuse a reader
  that drops bad rows (F2).

## Deviations

| # | Judgement |
|---|---|
| D1 `days_in(month) // m` | Sound. It is the spec's intent, identical for October, and forced by DS1 R25a's guard. |
| D2 budget prices from `tenant.prices` | **Workaround.** It is honest only because today's price list equals the plan-implied price, and it bypassed a mid-build question (F3). |
| D3 `EMU_PRICE` for non-whole plan money | Sound. It stops rather than rounds. The code name is slightly broad. |
| D4 emulator files via a child process | Sound. It keeps the dependency direction (no simulator import under `backend/`). |
| D5 placeholder for `NATIVE_VALUE` too | Sound. It stops a refused row shadowing a later ID as a 2a duplicate. |
| D6 commit count | Process only, no effect. |

## Checks run (reviewer, head `05f8a41ae`)

`PYTHONPATH` was the worktree's `backend:backend/tests:contracts:simulator:gateway:field:host:tools`. The module paths
resolve to `/opt/assetecon/AssetOpsV1-3a3/{backend/assetops_backend,contracts/assetops_contracts,simulator/assetops_simulator}/__init__.py`.

| Check | Result |
|---|---|
| `heavy-slot.sh -- pytest` on `test_3a3_source_contract.py`, `test_3a3_single_writer.py`, `test_3a3_load_emulated.py`, `contracts/tests/test_3a3_native_layouts.py`, `simulator/tests/world/test_3a3_exports.py` | **154 passed**, 1 warning (13.8 s) |
| `heavy-slot.sh --db -- pwsh run-host-tests.ps1 -- backend/tests/test_3a3_load_emulated_postgres.py` (routed `*_test`) | **4 passed**, 0 skipped (9.6 s) |
| `check-architecture.ps1` | Passed. The first run without `ASSETOPS_GUARD_PYTHON` could not start the chain guard because the worktree has no `.venv`; that is the environment, not the branch. |
| `check-agent-workflow.ps1` | Passed |
| Plant A: reader drops `NATIVE_ROW`/`NATIVE_CHARACTER` rows | **Not caught**: 174 passed (F2) |
| Plant B: loader treats accepted uploads as waiting | Caught: `test_l2_load_accept_and_rerun` fails |
| Plant C: `_HELD` without the decision filter (Postgres) | Caught: `test_p3_held_uploads` fails (`6 == 5`) |
| Probe: Fiona submits, then accepts in a second run | **Exit 0, 4 × ACCEPTED** by the submitter (F1) |
| Independent re-total of `build_exports` against `view_v1.json` | All equal, except Kisiwa O&M (ESTIMATED, absent) |

How the plants were run:
- Plants A and B ran in a `git archive` copy in the scratchpad.
- Plant C and the probe ran in a detached scratch worktree, because the Postgres slot marker needs a git checkout.
  Both were removed afterwards, and `git worktree list` holds no `rev3a3` entry.
- The branch worktree is unchanged.
- No other database, server or Docker was touched.

The builder's same-revision runs are cited, not rerun. All are at `575a50e05`; `05f8a41ae` adds only the packet, the
state entries and the INDEX line.
- Regression set: 467 passed.
- Neutral: simulator 503, contracts 33.
- Postgres: 65 passed.
- Fast check-all: 40 guards passed.
- Plants V1 to V20 and V1b each fail.

## Could not verify

- The builder's `plants.log`, which sits in their scratchpad. I reran three plants of my own instead.
- The E7 SHA-256s against the runbook YAML. E7 pins the fixture's hashes, and I did not run the YAML command.
- The full 3A2, 3A1 and 3A4 regression and Postgres sets. They are cited and were not rerun.

## Residual risk the packet does not name

- F3's echo risk on any manifest where the plan price is not the paid price.
- F6, where 3A6 profile readers fall under the same "native" path.
- Non-C0 invisible characters in references (see NATIVE_CHARACTER above).
- A DS1b `EXPENSE` or `BUDGET_LINE` record with no `site_code`, or a Site outside the tenant's list, is kept but put in
  no file and not listed as unwritten (`exports.py`, `ds1b.get(("budget", s.code))`). None exists on today's
  manifest, so this is latent.
# 3A3 review r2 (verification, head 56da8deba, diff 05f8a41ae..56da8deba): ACCEPT, no findings

PYTHONPATH verified: assetops_backend, assetops_contracts, assetops_simulator all import from /opt/assetecon/AssetOpsV1-3a3.
Own runs: backend 3A3 files (source_contract, load_emulated, single_writer) 123 passed; simulator test_3a3_exports 17 passed; check-architecture run.
- F1 fixed as a class: HeldUpload.submitted_by, cross-run PERSON_SAME_FOR_BOTH by person ID before any write; plant (check disabled, scratch copy) fails only the new L6 test.
- F2 fixed: C8 row-3 short and NUL cases, C1 records == golden rows, C3 optional-blank complement. Plant A (reader drops short and control-char rows) fails C8 on all 4 cases.
- F3 fixed (D-3A3.13): plan money / plan qty, exact, EMU_PLAN_PRICE, PLAN_PRICE_UNDEFINED. Plants "price from actuals" and "price from tenant.prices" both fail E10 (and the first fails E8 plan-price).
- F4 (S1 import flag + alias plant), F5 (composition-path L1), F6 (path = reader ID, L5 case), SITE_NOT_IN_TENANT (E9) all present with tests.
- Deviation mapped=None: within intent. The assert is two-way: None iff the layout maps no column (LAYOUTS-derived), so a mapping layout with no case fails; only billing qualifies. Residual (Low): the "maps nothing" fact comes from the layout declaration, so a layout wrongly declaring no maps would hide; a new layout is reviewed in 3A6 anyway.
Not verified: no DB, E6/E7 SHA pins beyond the passing suite.
