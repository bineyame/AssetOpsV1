# 3B7a handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a pre-flight
of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and I1, I2 .... Each
question cites the spec section, says what is unclear and what answer the writer expects, and is marked **(done)**
when its answer changes what counts as done. The Architect answers every question once, in `rulings.md` under
"Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when neither section has an
open question; coding starts only then.

## Reviewer questions

Reviewer (Claude, fresh; handshake round 1, 2026-11-20), against `main` at `11a5e2a06`. Severity: **High** blocks the
start of coding; Medium/Low are answered in the same round. Hand figures recomputed: Kobo 883.00 / 1445.00, Kisiwa
−65.00 (check −60.00), Mto 915.00, portfolio actual 883.00 (1 of 3), target 2295.00 (3 of 3), staff 1450.00, rebuilt
Kisiwa −250.00 (4070.00 − 3120.00 − 700.00 − 500.00); Nairobi October ends 2026-10-31T21:00Z, December 2026-12-31T21:00Z.
All agree with spec §5.

- **R1 (High, done).** §0 "Collisions", D-3B7A.7, 5b §0 and 5b reviewer guide: the seam has no owner who can actually
  act first. Units do not merge on their own (a slice merges whole after review), so "whichever of 3B7a unit 1 and 5b
  unit 2 merges first" never happens as written: both lanes run in parallel, both will have written §2.1 on their
  branches, and the second merge conflicts in `structure/read.py`. §2.1 is a signature sketch, not code, so the 5b
  guide's "byte-identical to 3B7a's text" cannot be checked (two implementers will not write identical docstrings,
  field order or `MappingProxyType({})` versus `{}`). Expected: name one writer and one event, for example "3B7a
  unit 1's seam commit (structure/read.py plus test 1) is merged to `main` alone, after a verification review, before
  5b unit 2 starts; 5b never writes it", and replace "byte-identical" with "5b's branch has no diff in
  `structure/read.py`".
- **R2 (High, done).** §4.2 "Guard": `$snapshotWriter` already exists in `tools/checks/configuration-persistence.ps1`
  (line 933: `chain/adapters/postgres_snapshot_store.py`, the day-snapshot writer, with its own shape checks at lines
  1211, 1489-1499 and 1871-1873, and in `$pgWriters` at line 1043). Followed literally, the spec redefines it and
  breaks the chain guard (or silently moves the day-snapshot rule onto the new adapter). Expected: a new name
  (`$structureSnapshotWriter`, `$structureSnapshotTables`, its own shape counter), appended to `$pgWriters` on its own
  line as lines 1045-1046 do, and the two plants plus a third (the chain day-snapshot rule still fails its own plant).
- **R3 (High, done).** D-3B7A.3, §3.3: the four reasons miss a change of *code rules* that alters values without
  touching the registry version or the payload format: 5a's `TARGET_RULE`/`MAIN_OF`, 4b's `SOURCE_STATE`/
  `STATED_STATE`/`READ_AS`, and `4a`/`4d` landing kWh and litre leaves (5b §8 says fuel cost then splits "with no
  change here"). After such a merge the October snapshot is served `current` with old values until the analyst
  happens to rebuild, which is exactly what decisions-register item 19 forbids. Expected: either a `rules_digest`
  column (sha256 of the canonical rule tables the build used) with a fifth reason `RULES` handled as
  `REBUILD_NEEDED`, or a ruling that bumps `REGISTRIES[...].version` (or `SNAPSHOT_FORMAT`) with every such rule change
  and a guard/test that enforces it. A plant: change one `TARGET_RULE` entry after a build; the read must not say
  current.
- **R4 (Medium).** §3.3 step 2 / D-3B7A.2: 3A4's stamp covers only the Site-month's placed money rows, but
  `CommercialLeafSource._month` also reads `held` = every record kind the Site has in *any* month (D-4B.5). A Site's
  first-ever EXPENSE or RECEIPT in November turns October's `om`, `staff`, `fuel_cost`, `outstanding` from
  `NOT_CONNECTED` to `NOT_RECEIVED` (and, for 5b, makes `om`/`staff` carriable), with no October stamp change: the
  served causes and words go stale silently. Expected: add the held-kinds set (sorted) to the Site row and compare it
  on serve (reason `RECORDS`), or list it under `untracked`, with a test.
- **R5 (Medium, done).** Reviewer-guide V9 cannot fail test 8: a same-instant rebuild over the same Sites collides on
  the *first Site row*, so even a store that writes row by row writes nothing. Expected: test 8 also builds at the
  same instant over a different Site set (e.g. first `[KOBO]`, then `[KISIWA]`): Kisiwa's Site row does not collide,
  the portfolio row does, and the row count must be unchanged.
- **R6 (Medium, done).** Test 10 says `structure_snapshot/read.py` imports nothing from `structure.read` but
  `SiteInputs`, yet §3.3 requires `StructureError("STRUCTURE_NOT_DECLARED", ...)` for a type with no structure,
  which needs `SITE_TYPE_TO_STRUCTURE` and `NOT_DECLARED` (both in `structure.read`). Expected: allow those two
  names (the test then still forbids `StructureRead`).
- **R7 (Low).** Test 6: how is the planted row stored? A copy at the same `as_of` raises `SnapshotExists`. Expected:
  a new id and a later `as_of`, put through the store, so it is the latest.
- **R8 (Low).** §2.3 `encode_site(s: SiteMonthSnapshot-without-ids)` names no type, and test 2's round trip needs a
  `SnapshotRow` to call `decode_site(row, site)`. Expected: `encode_site(tenant_id, site, month, as_of, inputs, actual,
  targets) -> str`, and test 2 wraps the payload in a hand-built row.
- **R9 (Low).** §3.2 `verify` rebuilds "with the same Sites (from the stored rows)", but an excluded Site (THIKA) has no
  row and the payload keeps only its code and reasons, so `portfolio:sites_excluded` cannot be recomputed. Expected:
  verify compares `sites`/`sites_excluded` as stored, or rebuilds them through `tenant_sites`.
- **R10 (Low).** §4.4 and D-3B7A.6 call for a runbook line, but no runbook file is in the §7 Q9 scope, and the deep-dive
  runbook (`Docs/engineering/operator-deep-dive-runbook.md`) is new on ON1's branch, not on `main`. Expected: name the
  file and its owner (add after ON1 merges), or move the line to the packet.
- **R11 (Low).** §4.2 `tenant_sites`: every Site of the tenant regardless of `lifecycle`, ordered by Postgres
  collation on `site_code` (the memory store sorts by Python). Expected: confirm all lifecycles, and order by
  `site_code_key` (or in Python) so both stores agree.


## Implementer pre-flight questions

Implementer pre-flight (same agent, implementer hat), every citation checked against `main` at `11a5e2a06`.

- **P1 (confirmed).** Every name in "Builds on" exists where the spec says: `structure/read.py` (`StructureRead`,
  `PortfolioStructure`, `site_count`, `NOT_DECLARED`, `SITE_TYPE_TO_STRUCTURE`); `structure/evaluate.py`
  (`evaluate`, `compose`, `SiteStructure`, `FactorValue`, `LeafValue`, `Missing`, `Coverage`, `ORIGIN_ORDER`);
  `structure/money.py` (`CommercialLeafSource`); `structure/composition.py` (`build_structure_read`);
  `structure/targets/read.py` (`TargetRead`, `SiteTargets`, `PortfolioTargets`, `TargetCheck`);
  `structure/targets/lines.py` (`BudgetLineReader.site/.portfolio(..., structure_key=, known_at=)`, `BudgetLines`
  with `.stamp`, `TargetLine`, `UnusedLine`); `commercial/months.py` (`site_month`, `portfolio_month`, `stale`,
  `MonthStamp`, `month_bounds`, `PORTFOLIO_ZONE = "UTC"`); `commercial/composition.py` (`build_commercial_reads(url)
  -> CommercialReads(months, store, dispose)`). No 3B7a module or table exists yet.
- **P2 (migration; collision check).** Head is `0065_commercial_upload` (`down_revision = "0064_person_on_work"`);
  no `0066` on `main`. ON1 (rev 3, `task/ON1-operator-tenant`) has **no migration**; its rulings move rev 2's
  `0066` (`role_proposal`) to `ON1b`, so `ON1b` renumbers after this lands. ON1 does not touch the guard,
  `structure/` or `migrations/`. `ledger_append_only()` is 0005's; `site_tenant_id_unique (tenant_id, id)` and
  `tenant.slug` are 0001's; the downgrade copies 0065's `REFUSE_IF_USED`. The 0065 migration test lives in
  `test_3a2_commercial_upload_postgres.py`.
- **P3 (guard shape).** The commercial shape regex accepts `VALUES (...)` only with no parentheses inside
  (`[^()]*`), so `site_snapshot_ids` is bound as a Python list of UUIDs, never `CAST(:x AS uuid[])`. With R2's
  rename, `$pgWriters +=` goes on its own line (estate self-test anchors, line 1045's comment).
- **P4 (one read per Site-month).** `CommercialLeafSource` caches its month read by `ReadContext` identity
  (`_last[0] is ctx`). `site_inputs` builds one `ReadContext` and uses it for every leaf and stated read, as `site`
  does now; otherwise D-4B.12's "one read" breaks. Test 1's equality would not catch it; I will add a read count.
- **P5 (double actual read).** `TargetRead.site` calls `self._actual.site(...)` itself (for `AT_ACTUAL`), so the
  build reads each Site's actual twice (inputs, then inside targets). Same `known_at`, so deterministic; noted
  for cost only, no change asked.
- **P6 (fixture).** `new_world()` is `test_3a4_commercial_months.py:78` (clock `READ_AT` 2026-11-20T08:00Z, equal
  to `AS_OF`); `NairobiSeeder` is in `test_3a4_commercial_months_postgres.py`; `test_5a_targets_postgres.py`
  exists. Kisiwa's missing `om` is `NOT_RECEIVED`, note None (`money.py` `_judge`, "nothing matched"), so §5's rows
  hold. `untracked` on the test reader: Mto `diesel_price` (fallback 1.30) only; Kobo and Kisiwa price from invoices.
- **P7 (open).** R6 decides the imports in `structure_snapshot/read.py`; R2 decides the guard variable names. I will
  not start unit 3 until both are answered.
