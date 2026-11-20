# 3B7a: the frozen monthly snapshot (implementer spec)

Status: rev 2, handshake round 1 answered (`rulings.md` "Handshake answers (round 1)", D-3B7A.10 to D-3B7A.12).
Architect (Claude), 2026-11-20. Lane B, on the deep-dive path (`two-week-build-plan.md` §0.1 row 10; D-BW1.8;
OD-23). **2.75 units** (rev 1: 2.5; +0.25 for the code digest and the held kinds). Discovery review (W5): a new table, a new
read the screen will use, and money figures served from storage.
- **Structure:** design §2.8 "A calculated daily snapshot" (OD-23; decisions-register item 19); owner: "keep a
  calcualted daily snapshot that the UI would use, ofcourse with triggers to recalulate" and "once a day and on demand
  for now" (`owner/SUMMARY.md` §3). This slice is the store, the served read with its "as of", the out-of-date test
  and the rebuild on command. The triggers, the daily run and *Recalculate now* are `3B7b`.
- **Builds on (merged; `main` at `8fddb2bba`):** `3B3` (`evaluate`, `compose`, `SiteStructure`, `FactorValue`,
  `LeafValue`, `Missing`, `Coverage`, `StructureRead`, `PortfolioStructure`, `site_count`, `NOT_DECLARED`,
  `SITE_TYPE_TO_STRUCTURE`), `4b` (`CommercialLeafSource`, `build_structure_read`, `ORIGIN_ORDER`), `5a`
  (`TargetRead`, `SiteTargets`, `PortfolioTargets`, `BudgetLines`, `TargetLine`, `UnusedLine`, `TargetCheck`,
  `BudgetLineReader`), `3A4` (`CommercialMonths.site_month`, `.portfolio_month`, `.stale`, `MonthStamp`,
  `month_bounds`, `PORTFOLIO_ZONE`), `3A1` (`build_commercial_reads`).
- **Decisions:** `rulings.md` (D-3B7A.1 to D-3B7A.12). **Reviewer guide:** `reviewer-guide.md`.

## 0. Before you start

- **Branches.** Unit 0 (the seam) on `task/3B7a-seam` off `main`, alone; it is verification-reviewed and merged to
  `main` before anything else here starts (D-3B7A.10). Units 1 to 3 on `task/3B7a-structure-snapshot`, cut from
  `main` after the seam merged, worktree `/opt/assetecon/AssetOpsV1-3b7a`. Start when the handshake has no open
  question.
- **Read:** `rulings.md`; 3B3 `spec.md` §2 and §4; 4b `spec.md` §3 and §4.1; 5a `spec.md` §2 to §5; 3A4 `spec.md` §3;
  `structure/read.py`, `structure/composition.py`, `structure/targets/`, `commercial/months.py`,
  `migrations/versions/0065_commercial_upload.py`, `commercial/adapters/postgres_commercial_store.py` (the writer
  pattern), `tools/checks/configuration-persistence.ps1` (3A1's commercial block, lines ~218 and ~969).
- **Databases:** `*_test` only, through `tools/heavy-slot.sh --db -- <command>`. Never ports 5490 or 8990, the
  walkthrough database or Docker.
- **Collisions.** You own the new package `backend/assetops_backend/structure_snapshot/`, the CLI module, migration
  0066 and its guard block. The one edit to an existing module is §2.1 in `structure/read.py`, shared with `5b`:
  only unit 0 writes it (D-3B7A.10); `5b` unit 2 waits for it on `main` and its branch has no diff in that file. Migration number: renumber at merge preparation if another lands first (tests
  read the head from the modules, as 0065).

## 1. Outcome and why

For a tenant and a month, one command computes every Site's evaluated structure (actual and target sides) and the
portfolio's operator-level lines once, freezes them with the instant they were computed ("as of") and the stamps of
the records they rest on, and stores them. The read serves the frozen figures without recomputing from records,
with its "as of" and a freshness answer: current, or out of date and why. `5b` splits the gap from what this serves;
`5c` shows it with "as of". The owner's rule served: pages read a calculated snapshot; a screen never shows an older
figure as current (decisions-register item 19).

Gate questions: does the served October read for Lakeside equal a fresh read at its "as of", field by field? Does a
late invoice make the served read say it is out of date, naming the Site and month, until a rebuild?

## 2. Unit 0: the inputs seam (0.25 unit; its own branch and merge, D-3B7A.10); unit 1: the frozen form (1 unit)

### 2.1 `structure/read.py` (the shared seam; unit 0; D-3B7A.7, D-3B7A.10)

```python
@dataclass(frozen=True)
class SiteInputs:
    site_code: str; month: str; structure_key: str; structure_version: int
    leaves: Mapping[str, LeafValue]     # every leaf of the registry, in registry order
    stated: Mapping[str, LeafValue]     # every stated_by row in registry order; empty when no StatedSource is wired

def evaluate_inputs(inputs: SiteInputs) -> SiteStructure   # REGISTRIES[key]; version must equal, else
                                                            # StructureError("STRUCTURE_COMPOSE", key, site_code)
class StructureRead:
    def site_inputs(self, site: SiteRef, month: str, known_at: datetime | None = None) -> SiteInputs
    def site(self, site, month, known_at=None) -> SiteStructure   # now: evaluate_inputs(self.site_inputs(...))
```
`site_inputs` does exactly what `site` did before the evaluation (same refusals, same one read per leaf, same
`stated` map); both mappings are `MappingProxyType`. `site`'s results are unchanged (3B3, 4b and 5a tests stay green
without edits). Export `SiteInputs` and `evaluate_inputs` in `__all__`. Unit 0's diff is this file and
`backend/tests/test_3b7a_site_inputs_seam.py` (§6 test 1), nothing else.

### 2.2 `structure_snapshot/model.py`

```python
SNAPSHOT_FORMAT = 1
BUILT_BY = re.compile(r"(person:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
                      r"|service:[a-z][a-z0-9._-]{0,63})", re.ASCII)       # fullmatch
REASONS = ("RECORDS", "MONTH_CLOSED", "RULES", "STRUCTURE_VERSION", "FORMAT")   # this order, always (D-3B7A.11)
STATES = ("SERVED", "NO_SNAPSHOT", "REBUILD_NEEDED")

@dataclass(frozen=True)
class SnapshotRow:                       # what the store keeps; one per Site-month build, one per portfolio build
    id: UUID; tenant_id: UUID; site_id: UUID | None          # None: the portfolio row
    period: str; structure_key: str; structure_version: int; format: int
    as_of: datetime                       # UTC; the build instant and every read's known_at
    built_by: str; closed_at_build: bool
    rules_digest: str                     # §2.5, the running digest at build (D-3B7A.11)
    held_kinds: tuple[str, ...]           # Site row: sorted kinds held at as_of (§3.4, D-3B7A.12); portfolio row: ()
    stamps: tuple[MonthStamp, ...]        # Site row: (its site_month stamp,); portfolio row: (portfolio_month stamp,)
    payload: str; payload_sha256: str     # §2.3
    site_snapshot_ids: tuple[UUID, ...] | None   # portfolio row only: its Site rows, in payload "sites" order

@dataclass(frozen=True)
class SiteMonthSnapshot:
    snapshot_id: UUID; tenant_id: UUID; site: SiteRef; month: str; as_of: datetime; built_by: str
    closed_at_build: bool; stamps: tuple[MonthStamp, ...]
    inputs: SiteInputs; actual: SiteStructure; targets: SiteTargets

@dataclass(frozen=True)
class PortfolioMonthSnapshot:
    snapshot_id: UUID; tenant_id: UUID; month: str; as_of: datetime; built_by: str; closed_at_build: bool
    stamps: tuple[MonthStamp, ...]        # its own portfolio stamp only
    asked: tuple[str, ...]                # every Site code built for, in the order given
    sites_excluded: Mapping[str, tuple[str, ...]]   # a type with no structure: NOT_DECLARED
    sites: Mapping[str, SiteMonthSnapshot]          # the MINI_GRID Sites, in `asked` order
    portfolio_lines: BudgetLines
    def actual(self) -> PortfolioStructure     # compose(...) over sites' `actual`, sites_excluded set (D-3B7A.4);
                                               # the structure's composition, never a screen figure (D-5B.12)
    def targets(self) -> PortfolioTargets      # compose(...) over sites' `targets.structure`; `sites` = their targets

@dataclass(frozen=True)
class Freshness:
    current: bool                          # reasons == ()
    reasons: tuple[str, ...]               # a subsequence of REASONS
    stale_stamps: tuple[MonthStamp, ...]   # CommercialMonths.stale's answer, input order (§3.3)
    changed_kinds: tuple[str, ...]         # "<site_code>:<kind>", held now xor held at build; asked order, kind sorted
    untracked: tuple[str, ...]             # §2.4

@dataclass(frozen=True)
class Served:
    state: str                             # one of STATES
    snapshot: SiteMonthSnapshot | PortfolioMonthSnapshot | None   # None unless SERVED
    as_of: datetime | None                 # None only for NO_SNAPSHOT
    freshness: Freshness | None            # None only for NO_SNAPSHOT
```
`actual()` and `targets()` are exactly what `StructureRead.portfolio` and `TargetRead.portfolio` would return from
the same Site values (same `PortfolioStructure` fields; `targets().portfolio_lines` is the stored one).

### 2.3 `structure_snapshot/codec.py`: the payload (D-3B7A.8)

`encode_site(tenant_id: UUID, site: SiteRef, month: str, known_at: datetime, inputs: SiteInputs, actual:
SiteStructure, targets: SiteTargets) -> str`, `encode_portfolio(tenant_id: UUID, month: str, structure_key: str,
structure_version: int, known_at: datetime, asked: Sequence[str], sites_excluded: Mapping[str, tuple[str, ...]],
portfolio_lines: BudgetLines) -> str`, `decode_site(row, site: SiteRef) -> SiteMonthSnapshot`, `decode_portfolio(row, sites: Mapping[str, SiteMonthSnapshot]) ->
PortfolioMonthSnapshot`, `digest(payload: str) -> str` (`hashlib.sha256(payload.encode("utf-8")).hexdigest()`).

**Canonical JSON:** `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`. `Decimal` →
`str(d)` and back with `Decimal(s)` (exponent kept: `"1.3"`, `"1.30"`, `"1E+2"` survive as written); `datetime` →
`d.astimezone(timezone.utc).isoformat()`; `UUID` → `str`; tuples → lists; mappings → objects; `None` → `null`. No
`float` anywhere (`json.loads(..., parse_float=Decimal)` is not needed: no number is written as a JSON number except
`int`s).

**Site payload:**
```
{"format": 1, "kind": "SITE_MONTH", "tenant_id", "site_id", "site_code", "site_type", "timezone", "month",
 "structure_key", "structure_version", "known_at",
 "inputs": {"leaves": {f: LEAF}, "stated": {f: LEAF}},
 "actual": {f: FACTOR},
 "targets": {"values": {f: FACTOR}, "currency": str|null, "checks": [CHECK], "lines": LINES}}
LEAF   = {"value","evidence","sources":[],"coverage":COV|null,"missing":MISSING|null,"currency","origins":[]}
COV    = {"covered": int, "expected": int, "grades": {grade: int}}
MISSING= {"record_kind","source_family","cause","carried_as","blocks":[],"record_words","assumption","note"}
FACTOR = {"value","evidence","sources":[],"coverage","missing","missing_leaves":[],"assumed_leaves":[],"currency",
          "origins":[],"stated": bool,"computed","detail_missing":[]}      # factor_id is the key; unit is not stored
CHECK  = {"factor_id","stated","computed","currency","agrees": bool}
LINES  = {"site_id","period","version_ref","problem","lines":[TLINE],"blocked":{f: note},"unused":[ULINE],"stamp":STAMP}
TLINE  = every TargetLine field by name (value str, revision_id/intake_id/person_id str or null, declared_at iso)
ULINE  = {"factor_id","version_ref","line_ref","reason","source_systems":[]}
STAMP  = {"site_id": str|null, "period", "digest"}
```
**Portfolio payload:** `{"format": 1, "kind": "PORTFOLIO_MONTH", "tenant_id", "month", "structure_key",
"structure_version", "known_at", "sites": [codes asked, in order], "sites_excluded": {code: [reasons]},
"portfolio_lines": LINES}`. Snapshot IDs are never in a payload (a rebuild at the same instant gives the same bytes).

**Decoding** rebuilds the frozen dataclasses with tuples and `MappingProxyType` mappings, in the stored key order of
the registry (iterate `reg.rows`, not the JSON object order), and `FactorValue.unit = REGISTRIES[key].row(f).unit`.
It first checks `digest(row.payload) == row.payload_sha256`; a mismatch raises `RuntimeError("snapshot payload does
not match its digest")` (a bug or tampering, never served).

### 2.4 Untracked inputs (D-3B7A.5)

`untracked(inputs: SiteInputs) -> tuple[str, ...]`: the leaves of `inputs.leaves` (sorted) with a value, evidence not
`NEUTRAL`, row `filled_by.family != "CALENDAR"`, and any source not starting `"commercial:"`. These rest on inputs no
month stamp covers (readings, declared prices); `3B7b`'s triggers 1 and 4 will cover them. The portfolio's
`untracked` is `f"{code}:{leaf}"` over its Sites, in `asked` order then leaf order.

### 2.5 `structure_snapshot/rules_digest.py`: the code that built it (D-3B7A.11)

```python
RULE_ROOTS = ("assetops_backend.structure_snapshot.composition",)
def import_closure(package_dir: Path, roots: Sequence[str] = RULE_ROOTS) -> tuple[str, ...]
def rules_digest(package_dir: Path = <the assetops_backend directory>) -> str   # lru_cache on the default
```
`import_closure` parses each module with `ast` (never imports it) and follows every `Import` and `ImportFrom` node
anywhere in the file, **including inside function bodies** (the compositions import lazily), resolving relative
imports; it keeps names under `assetops_backend` whose file exists (`x.py` or `x/__init__.py`; for `from p import n`,
`p.n` when it is a module, else `p`), and includes each package `__init__` on the way. Sorted module names.
`rules_digest` is `sha256("\n".join(f"{name} {sha256(file bytes).hexdigest()}" for name in closure))`. The
composition computes it once and passes the string to the builder and the read; tests pass literals.

## 3. Unit 2: store, build and read, in memory (1 unit)

### 3.1 `structure_snapshot/store.py`

```python
class SnapshotExists(Exception): ...        # a row for the same scope and as_of already exists
class StructureSnapshotStore(Protocol):
    def tenant_sites(self, slug: str) -> tuple[UUID, tuple[SiteRef, ...]] | None   # every lifecycle; sorted in
                                                                                     # Python by site_code
    def put(self, rows: Sequence[SnapshotRow]) -> None     # one transaction: all rows or none; SnapshotExists
    def latest_site(self, tenant_id: UUID, site_id: UUID, period: str) -> SnapshotRow | None   # max as_of
    def latest_portfolio(self, tenant_id: UUID, period: str) -> SnapshotRow | None             # max as_of
    def get(self, tenant_id: UUID, ids: Sequence[UUID]) -> tuple[SnapshotRow, ...]   # in the order given;
                                                                                       # a missing id raises LookupError
class MemoryStructureSnapshotStore: ...     # the same port; a list of rows; `sites` set by the test
```
Rows are never updated or deleted (D-3B7A.1). Scope uniqueness: `(tenant_id, site_id, period, as_of)` for Site rows,
`(tenant_id, period, as_of)` for portfolio rows.

### 3.2 `structure_snapshot/build.py`

```python
@dataclass(frozen=True)
class BuildResult:
    as_of: datetime; portfolio_snapshot_id: UUID
    sites: Mapping[str, UUID]           # MINI_GRID Site code -> its new row id, in `sites` order
    excluded: tuple[str, ...]           # codes of the other types, in order
    rules_digest: str

@dataclass(frozen=True)
class Verification:
    snapshot_id: UUID; matches: bool; differences: tuple[str, ...]   # §3.2 paths, sorted
    rules_changed: bool                  # the row's rules_digest differs from the running one

class SnapshotBuilder:
    def __init__(self, actual: StructureRead, targets: TargetRead, lines: BudgetLineReader,
                 store: StructureSnapshotStore, kinds: HeldKinds, rules: str, clock: Callable[[], datetime],
                 ids: Callable[[], UUID] = uuid4) -> None   # `lines` is the reader inside `targets`
    def build(self, tenant_id: UUID, sites: Sequence[SiteRef], month: str, *, built_by: str) -> BuildResult
    def verify(self, tenant_id: UUID, snapshot_id: UUID) -> Verification   # a portfolio row's id
```
**`build`, in order** (D-3B7A.2):
1. `BUILT_BY.fullmatch(built_by)` else `ValueError("BAD_BUILT_BY")`; the month as `StructureRead` checks it; the
   same Site refusals as `TargetRead.portfolio` (another tenant, a repeated Site: `STRUCTURE_COMPOSE`).
2. `as_of = clock()`, converted to UTC. Every read below passes `known_at=as_of`.
3. For each MINI_GRID Site, in order: `inputs = actual.site_inputs(site, month, as_of)`; `t = targets.site(site,
   month, as_of)`; `actual_values = evaluate_inputs(inputs)`. The Site row's stamps are `(t.lines.stamp,)` (3A4's
   `site_month` stamp under `known_at`); `closed_at_build = as_of >= month_bounds(month, site.timezone)[1]`;
   `held_kinds = kinds.of(tenant_id, site.site_id, known_at=as_of)`. Every row's `rules_digest` is `rules`.
4. `pl = lines.portfolio(tenant_id, month, structure_key="MINI_GRID", known_at=as_of)` (the operator-level lines,
   as `TargetRead.portfolio` reads them; `lines` is the same `BudgetLineReader` the `TargetRead` holds). The portfolio
   row's stamps are `(pl.stamp,)`; `closed_at_build = as_of >= month_bounds(month, PORTFOLIO_ZONE)[1]`;
   `sites_excluded` = `{code: NOT_DECLARED}` for the other types.
5. One `store.put([*site_rows, portfolio_row])`. On `SnapshotExists` nothing is written and it propagates.

The builder never reads `targets.portfolio(...)` whole (that would read every Site twice); the portfolio target is
composed on serve (D-3B7A.4).

**`verify`** loads the portfolio row and its Site rows, rebuilds every Site payload at `known_at = row.as_of`
without writing (each `SiteRef` from its stored payload: `site_id`, `site_code`, `site_type`, `timezone`) and the
portfolio payload with `asked` and `sites_excluded` taken as stored (they are the build's inputs), and compares the
canonical bytes. `rules_changed` is `row.rules_digest != rules`. `differences` lists, sorted:
`"<site_code>:inputs.leaves.<f>"`, `"<site_code>:inputs.stated.<f>"`, `"<site_code>:actual.<f>"`,
`"<site_code>:targets.values.<f>"`, `"<site_code>:targets.lines"`, `"<site_code>:targets.checks"`,
`"<site_code>:targets.currency"`, `"portfolio:portfolio_lines"` for each part whose canonical JSON differs. `matches` is `differences == ()`.

### 3.3 `structure_snapshot/read.py`: the served read (D-3B7A.3)

```python
class SnapshotRead:
    def __init__(self, store: StructureSnapshotStore, months: CommercialMonths, kinds: HeldKinds, rules: str,
                 clock: Callable[[], datetime]) -> None
    def site(self, tenant_id: UUID, site: SiteRef, month: str) -> Served
    def portfolio(self, tenant_id: UUID, month: str) -> Served
```
It reads stored rows, `months.stale` and `kinds.of` only: it calls no `StructureRead`, `TargetRead`, `evaluate`,
`site_month` or `portfolio_month` (D-3B7A.3). For the portfolio it reads `latest_portfolio`, then `get(site_snapshot_ids)`.

Freshness of a row set (the Site row; or the portfolio row and its Site rows, portfolio first then `asked` order):
1. `FORMAT`: any row's `format != SNAPSHOT_FORMAT`. `STRUCTURE_VERSION`: any row's `structure_version !=
   REGISTRIES[row.structure_key].version`. Either: `Served("REBUILD_NEEDED", None, as_of, Freshness(False,
   reasons, (), (), ()))`, the payload not decoded (only these two reasons are reported; steps 2 to 4 are skipped).
2. `stale_stamps = months.stale(tenant_id, stamps)` over the rows' stamps in that order. For each Site row,
   `kinds.of(tenant_id, site_id)` (now, no `known_at`) against its `held_kinds`: the symmetric difference, as
   `"<site_code>:<kind>"`, is `changed_kinds`. `RECORDS` when either is non-empty (D-3B7A.12).
3. `MONTH_CLOSED`: some row has `closed_at_build` false and `clock() >= ` its month end (Site rows: the Site's
   timezone; the portfolio row: `PORTFOLIO_ZONE`).
4. `RULES`: some row's `rules_digest != rules` (D-3B7A.11).
5. Otherwise decode; `Served("SERVED", snapshot, row.as_of, Freshness(reasons == (), reasons, stale_stamps,
   changed_kinds, untracked))`. Out-of-date values are served with their freshness, never as current.
Reasons are reported in `REASONS` order.
No row: `Served("NO_SNAPSHOT", None, None, None)`. A `SiteRef` of a type with no structure: `StructureError(
"STRUCTURE_NOT_DECLARED", site_type, site_code)` as 3B3.

### 3.4 `structure_snapshot/kinds.py`: the record kinds a Site holds (D-3B7A.12)

```python
class HeldKinds(Protocol):
    def of(self, tenant_id: UUID, site_id: UUID, known_at: datetime | None = None) -> tuple[str, ...]
class StoreHeldKinds:                     # the one implementation, for both stores
    def __init__(self, store: CommercialStore) -> None
    # sorted({r.kind for r in store.latest_revisions(tenant_id, site_id=site_id, known_at=known_at)})
```
The same call 4b's `CommercialLeafSource._month` makes for `held`, so the frozen set equals what the build judged.

## 4. Unit 3: Postgres, guard, composition, command (0.5 unit)

### 4.1 Migration `0066_structure_snapshot.py` (revises `0065_commercial_upload`)

```sql
CREATE TABLE structure_snapshot (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant (id),
    site_id uuid NULL,                                        -- NULL: the portfolio row
    period text NOT NULL CHECK (period ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    rules_digest text NOT NULL CHECK (rules_digest ~ '^[0-9a-f]{64}$'),
    held_kinds text[] NOT NULL,                               -- '{}' on the portfolio row
    structure_key text NOT NULL CHECK (structure_key ~ '^[A-Z][A-Z_]{0,39}$'),
    structure_version int NOT NULL CHECK (structure_version >= 1),
    format int NOT NULL CHECK (format >= 1),
    as_of timestamptz NOT NULL,
    built_by text NOT NULL CHECK (built_by ~ '^(person:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|service:[a-z][a-z0-9._-]{0,63})$'),
    closed_at_build boolean NOT NULL,
    stamps text NOT NULL,                                     -- canonical JSON array of STAMP
    payload text NOT NULL,
    payload_sha256 text NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    site_snapshot_ids uuid[] NULL,
    FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id),
    CHECK ((site_id IS NULL) = (site_snapshot_ids IS NOT NULL)),
    UNIQUE (tenant_id, id)
);
CREATE UNIQUE INDEX structure_snapshot_site_at ON structure_snapshot (tenant_id, site_id, period, as_of)
    WHERE site_id IS NOT NULL;
CREATE UNIQUE INDEX structure_snapshot_portfolio_at ON structure_snapshot (tenant_id, period, as_of)
    WHERE site_id IS NULL;
CREATE TRIGGER structure_snapshot_immutable BEFORE UPDATE OR DELETE ON structure_snapshot
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
```
No column defaults. Downgrade refuses when any row exists (0065's `REFUSE_IF_USED` form), then drops trigger,
indexes, table. Not in the chain change log.

### 4.2 `structure_snapshot/adapters/postgres_structure_snapshot_store.py`

The port over SQLAlchemy `text()` statements, in 3A1's adapter style: one plain `INSERT INTO structure_snapshot
(...) VALUES (...)` per row inside one transaction; a unique violation (`23505`) rolls back and raises
`SnapshotExists`. `tenant_sites`: `SELECT id FROM tenant WHERE slug = :slug`, then `SELECT id, site_code, site_type,
timezone FROM site WHERE tenant_id = :t` (every lifecycle), sorted in Python by `site_code` as the memory store.
`held_kinds` is bound as a Python list (P3). `latest_*`: `ORDER BY as_of DESC LIMIT 1`. `stamps` is
canonical JSON. No UPDATE, DELETE or TRUNCATE.

**Guard** (`tools/checks/configuration-persistence.ps1`), in 3A1's form: a domain entry (`Name` `structure_snapshot`,
`Package` `$backendRoot/structure_snapshot`, `Composition` `$backendRoot/structure_snapshot/composition.py`, `Writer`
`$null`); `$structureSnapshotWriter` (`$backendRoot/structure_snapshot/adapters/postgres_structure_snapshot_store.py`),
`$structureSnapshotTables = @('structure_snapshot')` and its own counter `$structureSnapshotInsertsSeen`, as the sole
runtime writer with the one plain-INSERT shape and its anti-vacuity count; added by one line of its own after line
1046, `$pgWriters += $structureSnapshotWriter  # 3B7a: on its own line, as the account writer`; and, if the guard
lists Postgres readers, to them. **`$snapshotWriter` (line 933, the chain day-snapshot writer) and its checks are
not touched.** Show it failing on three plants (RULES §7): an `UPDATE structure_snapshot` in the adapter; an
`INSERT INTO structure_snapshot` from another module; an `UPDATE site_day_snapshot` in
`chain/adapters/postgres_snapshot_store.py` (the old rule still fails its own plant). This is an additive guard edit:
the owner approves it through the coordinator before unit 3 merges (handshake R2).

### 4.3 `structure_snapshot/composition.py`

`build_structure_snapshot(database_url) -> StructureSnapshotService(builder, read, store, dispose)`: `actual =
build_structure_read(url)`; `reads = build_commercial_reads(url)`; `lines = BudgetLineReader(reads.months,
reads.store)`; `targets = TargetRead(lines, actual.read)`; the adapter; `kinds = StoreHeldKinds(reads.store)`;
`rules = rules_digest()`; `SnapshotBuilder(actual.read, targets, lines, store, kinds, rules, _utc_now)`,
`SnapshotRead(store, reads.months, kinds, rules, _utc_now)`. A failure in any builder disposes those already built; `dispose`
disposes all three.

### 4.4 The command `assetops_backend/build_structure_snapshot.py`

```
python -m assetops_backend.build_structure_snapshot build  --tenant SLUG --month YYYY-MM --by BUILT_BY
python -m assetops_backend.build_structure_snapshot verify --tenant SLUG --snapshot UUID
```
`DATABASE_URL` from the environment, as 3A3's loader. One JSON line on stdout: build
`{"as_of", "portfolio_snapshot_id", "sites": {code: id}, "excluded": [codes]}`; verify `{"snapshot_id", "matches",
"differences": [...]}`. Exit 0 done (verify: matches); 2 refused before any work (`UNKNOWN_TENANT`, `BAD_MONTH`,
`BAD_BUILT_BY`, no `DATABASE_URL`: `NO_DATABASE`); 3 `SNAPSHOT_EXISTS`; 4 verify differs. Refusals print `<CODE>
<one sentence>` on stderr. Build's JSON line also carries `"rules_digest"`; verify's `"rules_changed"`. The runbook
line (the analyst, after each accepted import, and after a deploy): `build --tenant <slug> --month <YYYY-MM> --by
person:<their account id>` (D-3B7A.6). It goes in the packet; the coordinator adds it to
`Docs/engineering/operator-deep-dive-runbook.md` once ON1 has merged that file (handshake R10).

## 5. Fixture (no new file; hand-computed values are 4b's and 5a's)

The world is 3A4's `new_world()` with, in order: every step of `money_leaves_lakeside.json` (4b §4.1; `at`
`2026-11-06T09:00:00+00:00`, `service:test-4b`), then steps 1 and 2 of `targets_lakeside.json` (5a §5, their own
`at` and `entered_by`). Sites `KOBO-001`, `KISIWA-001`, `MTO-001` as `SiteRef(tid, id, code, "MINIGRID",
"Africa/Nairobi")`, in that order, plus `SiteRef(tid, UUID("3b7a0000-0000-4000-8000-000000000009"), "THIKA-001",
"COLDCHAIN", "Africa/Nairobi")`. Actual side: 4b's test reader (`CommercialLeafSource(months, store, fallback())`,
`StructureRead(src, stated=src)`); `lines = BudgetLineReader(months, store)`; targets: `TargetRead(lines, that
read)`. Builder clock
`AS_OF = 2026-11-20T08:00:00+00:00`, `built_by` `service:test-3b7a`, ids `UUID(int=n)` from a counter.

**Expected at `AS_OF`** (literals from 4b §4.1 and 5a §5):

| Read | Expected |
|---|---|
| Kobo actual | `contribution` 883.00 RECORDED; `revenue` 3458.00 stated; `diesel_price` 1.25 DERIVED |
| Kobo targets | `contribution` 1445.00 DECLARED; `checks == (TargetCheck("contribution", 1445.00, 1445.00, "USD", True),)` |
| Kisiwa | actual `contribution` None, `missing_leaves == ("om",)`; target `contribution` −65.00; check `(-60.00, -65.00, False)` |
| Mto | actual `contribution` None; target 915.00; `untracked == ("diesel_price",)` (the fallback's 1.30 assumption) |
| Portfolio | `actual()` contribution 883.00, `site_count` 1 of 3; `targets()` contribution 2295.00, 3 of 3, `staff` 1450.00; `portfolio_lines.lines` one line, `staff` 1200.00; `sites_excluded == {"THIKA-001": ("STRUCTURE_NOT_DECLARED",)}`; `asked` the four codes |
| Stamps | each Site row `(months.site_month(tid, id, "2026-10", known_at=AS_OF).stamp,)`; portfolio row `(months.portfolio_month(tid, "2026-10", known_at=AS_OF).stamp,)`; all rows `closed_at_build` True |

**The late invoice** (`LATE`): `expense_ledger`, `lakeside-accounts`, `source-emulated`, record
`KISIWA-EX-OM-1031` EXPENSE KISIWA-001, `occurred_at` `2026-10-31T10:00:00+03:00`, 700.00 USD, PAID, OM,
`counterparty_ref` `SUP-OM`, `document_ref` its ID, `recognition_period` `2026-10`; ingested at
`2026-11-21T09:00:00+00:00` by `service:test-3b7a`. After it, a rebuild at `2026-11-21T10:00:00+00:00` gives Kisiwa
actual `om` 700.00 RECORDED and `contribution` −250.00 RECORDED (4070.00 − 3120.00 − 700.00 − 500.00).

## 6. Tests (written first)

**Unit 0** (`backend/tests/test_3b7a_site_inputs_seam.py`, no database):
1. The seam: for Kobo, Kisiwa, Mto, `evaluate_inputs(read.site_inputs(s, OCT, AS_OF)) ==
   read.site(s, OCT, AS_OF)`; `site_inputs` keys are the 31 leaves and the two stated rows in registry order; a
   `StructureRead(src)` with no stated source gives `stated == {}`; through a counting `CommercialMonths` wrapper,
   one `site_inputs` call and one `site` call each make exactly one `site_month` call (P4, D-4B.12).

**No database** (`backend/tests/test_3b7a_structure_snapshot.py`):
2. *(unit 1)* Codec round trip: for each Site, `decode(encode(x)) == x` for inputs, actual, targets, and
   `encode(decode(encode(x))) == encode(x)` byte for byte; a hand-built `LeafValue` set with values
   `Decimal("1.3")`, `Decimal("1.30")`, `Decimal("1E+2")` and a `Coverage(28, 31, {"A": 20, "B": 8})` survives with
   `str()` equal; the payload contains no JSON number but the `int`s; a payload with one character changed and the
   old digest raises `RuntimeError`.
3. *(unit 2)* Build and serve at `AS_OF`: §5's table, every row; each served Site equals the fresh reads at
   `known_at=AS_OF` (`inputs`, `actual`, `targets`, object equality); `actual()` and `targets()` equal
   `StructureRead.portfolio` and `TargetRead.portfolio` over the same Sites at `AS_OF`; freshness current, reasons
   `()`, `stale_stamps ()`; Kobo and Kisiwa `untracked == ()`.
4. *(unit 2)* The late invoice: (a) after `LATE`, read clock `2026-11-21T09:30:00+00:00`: Kisiwa `SERVED`,
   `current` False, `reasons == ("RECORDS",)`, `stale_stamps == (kisiwa_stamp,)`, values still the `AS_OF` ones (om
   absent); Kobo and Mto current; portfolio `reasons == ("RECORDS",)`, `stale_stamps == (kisiwa_stamp,)`.
   (b) Rebuild at `2026-11-21T10:00:00+00:00`: §5's rebuilt Kisiwa values; every read current; the store holds two
   rows for each Site and two portfolio rows; the first rows are unchanged.
   (c) Built at one instant: ingest `LATE` at `2026-11-21T09:00:00+00:00` *before* a first build whose clock is
   `AS_OF` (earlier): the snapshot has Kisiwa `om` absent and is immediately `RECORDS`-stale.
   (d) A new kind (D-3B7A.12): first assert `kinds.of(tid, mto.id, known_at=AS_OF)` lacks `"CHARGE"`; build at
   `AS_OF`; ingest at `2026-11-21T09:00:00+00:00` by `service:test-3b7a` one `billing_export` batch
   (`source_system` `mto-billing`, `source-emulated`) with record `MTO-CH-1101` CHARGE MTO-001, shaped as 5b's
   `MTO-CH-1001` but `effective_from` `2026-11-01`, `effective_to` `2026-12-01`, `recognition_period` `2026-11`,
   100.00 USD, 250 kWh; read October at `2026-11-21T09:30:00+00:00`: Mto `reasons == ("RECORDS",)`, `stale_stamps
   == ()`, `changed_kinds == ("MTO-001:CHARGE",)`, values the `AS_OF` ones; Kobo and Kisiwa current; portfolio
   `reasons == ("RECORDS",)`, `changed_kinds == ("MTO-001:CHARGE",)`.
5. *(unit 2)* Month closed: (a) a build for `2026-12` (no records) at `2026-12-15T00:00:00+00:00`, read at
   `2026-12-20T00:00:00+00:00`: current; read at `2027-01-02T00:00:00+00:00`: `reasons == ("MONTH_CLOSED",)`,
   `stale_stamps == ()`. (b) An October build at `2026-10-31T12:00:00+00:00` (before Nairobi's month end,
   `2026-10-31T21:00:00+00:00`) read at `AS_OF`: `reasons == ("RECORDS", "MONTH_CLOSED")`.
6. *(unit 2)* Rebuild needed: a stored Site row copied with `structure_version` one less (payload re-encoded with that
   version and its digest), a new id `UUID(int=900)` and `as_of` one second after the build, put through
   `store.put` so it is the latest: `Served("REBUILD_NEEDED", None, as_of, Freshness(False, ("STRUCTURE_VERSION",),
   (), (), ()))`; the same with `format` 2 (id `UUID(int=901)`): reason `FORMAT`. No snapshot: `NO_SNAPSHOT`.
7. *(unit 2)* No recompute on read: `SnapshotRead(store, OnlyStale(months), kinds, rules, clock)`, where `OnlyStale`
   exposes only `stale` (any other attribute raises `AttributeError`), serves tests 3 and 4(a) unchanged.
8. *(unit 2)* Refusals: a same-instant second build raises `SnapshotExists` and writes nothing (row count
   unchanged); a build over `[KOBO]` at `T`, then over `[KISIWA]` at the same `T`: `SnapshotExists`, row count
   unchanged, no Kisiwa row (handshake R5); `built_by` `"test:x"` raises `ValueError("BAD_BUILT_BY")`; a Site of another tenant and a repeated
   Site raise `STRUCTURE_COMPOSE`.
9. *(unit 2)* Verify: right after test 3's build, `matches` True; after `LATE`, still True (rebuilt at `as_of`); with
   a builder whose fallback prices diesel at 1.40, `matches` False and `differences` contains
   `"MTO-001:inputs.leaves.diesel_price"` and `"MTO-001:actual.diesel_price"` and no path starting `"KOBO-001"` or
   `"KISIWA-001"`.
10. Grep: no `float(` under `structure_snapshot/`; `structure_snapshot/read.py` imports from `structure.read`
    exactly `SiteInputs`, `SITE_TYPE_TO_STRUCTURE` and `NOT_DECLARED` (never `StructureRead`), `StructureError` from
    `structure.check`,
    nothing from `structure.targets.read` but the result types, and not `evaluate`.
11. *(unit 1 for (b), (c); unit 2 for (a))* The code digest (D-3B7A.11): (a) built with `rules="a"*64`, read by a
    `SnapshotRead` with `rules="b"*64`: `SERVED`, `current` False, `reasons == ("RULES",)`, the `AS_OF` values; with
    `"a"*64`: current; `verify` reports `rules_changed` True under `"b"*64`. (b) `import_closure(<package dir>)`
    contains `assetops_backend.structure.targets.rules`, `.structure.sources`, `.structure.money`,
    `.structure.registry`, `.structure.rows_mini_grid`, `.structure.evaluate`, `.commercial.months` and
    `.commercial.composition` (imported inside a function body only). (c) `shutil.copytree` the package into
    `tmp_path`; `rules_digest(copy)` equals `rules_digest(original)`; replace one `TARGET_RULE` entry's text in the
    copy's `structure/targets/rules.py`: the digest differs.

**Postgres** (`backend/tests/test_3b7a_structure_snapshot_postgres.py`, pooled, `--db`; Sites by 3A4's
`NairobiSeeder`; the world through `PostgresCommercialStore` as `test_5a_targets_postgres.py`):
1. Tests 3, 4(a), 4(b), 4(d) and 9 against the Postgres snapshot store (`StoreHeldKinds` over
   `PostgresCommercialStore`).
2. The table refuses `UPDATE` and `DELETE` (the trigger); a second same-instant `put` raises `SnapshotExists` and the
   first row survives; `tenant_sites("lakeside-power")` lists the three Sites by code.
3. `build_structure_snapshot(url)` builds and serves Kobo's 883.00; `dispose()` runs. The command: `build` exits 0
   with one JSON line; a second `build` in the same second is not asserted (clock); `verify` exits 0; `--tenant nope`
   exits 2 `UNKNOWN_TENANT`.
4. Migration up, down (empty) and refusal (a row present), as 0065's test does.

**Regression:** `test_3b3_structure_evaluate.py`, `test_4b1_stated_nodes.py`, `test_4b_money_leaves.py`,
`test_5a_targets.py` (unchanged files, all green). Check-all once at the end (with the guard plants shown);
`select-tests` before review.

## 7. Done (questions; each can fail)

1. Does every served Lakeside October figure equal a fresh read at its "as of", field by field, Site and portfolio?
2. Does a late record make the served read say "out of date" with the Site's month named, while still serving the
   old figures with their "as of", and does a rebuild make it current?
3. Does a snapshot taken before the month closed say so once it has closed?
4. Is a snapshot of another structure version or format never served as values?
5. Is nothing recomputed on a served read (no evaluation, no month read but `stale`)?
6. Are snapshots never changed (append-only in memory and in Postgres), and is a same-instant rebuild refused whole?
7. Do figures resting on inputs no stamp covers say so (`untracked`), and does a change of the code that built them
   or of the record kinds a Site holds make the read say "out of date" (`RULES`, `changed_kinds`)?
8. Does verification rebuild at the "as of" and name what differs?
9. Was the seam merged alone, first (unit 0), and is every other edit inside the new package, migration, command,
   guard block, tests and packet?

Packet: `specs/3B7a-structure-snapshot/packet.md`, with the mid-build count and the guard plants' output.

## 8. Out of scope

Triggers, the dirty queue, the daily run, *Recalculate now* and the "recalculation pending" note (`3B7b`); a route
or a screen (`5c` reads this through the composition); the gap (`5b`); storing composed totals or the bridge
(D-3B7A.4); pruning old snapshots (queue Q3); cold-chain and EV structures (`3B6`).

## 9. Units

| Unit | Content | Needs | Commits |
|---|---|---|---|
| 0 | §2.1: the seam and its test, on `task/3B7a-seam`; verification review; merged to `main` alone (0.25) | `main` | 1 |
| 1 | §2.2 to §2.5: model, codec, untracked, code digest; tests 2, 11(b), 11(c) (1) | unit 0 on `main` | 1 |
| 2 | §3: memory store, held kinds, builder, verify, served read; tests 3 to 10, 11(a) (1) | unit 1 | 1 |
| 3 | §4: migration, adapter, guard (owner approval, R2), composition, command; Postgres tests; check-all; packet (0.5) | unit 2 | 1 |

## 10. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 (owner) | Store composed totals and the bridge in the snapshot, or derive them on serve from the frozen Site values | Derive on serve (D-3B7A.4): arithmetic only, no record read, and no stored total can disagree with its parts |
| Q2 (owner) | A changed price, tariff or setting, or new readings, before `3B7b` | Not detected this fortnight; the read lists the figures resting on them (`untracked`); `3B7b` triggers 1 and 4 |
| Q3 | Keep every snapshot or prune | Keep all (append-only); pruning with the owner's database strategy round |
| Q4 | Who rebuilds | The analyst by command after each accepted import (runbook); *Recalculate now* and the daily run are `3B7b` |
| Q5 | A code change since the build | Served out of date (`RULES`) until rebuilt; over-reports on a refactor, never under-reports (D-3B7A.11); `3B7b` rebuilds on deploy |
| Q6 (owner, via the coordinator) | Approve the additive guard block for `structure_snapshot` | Approve: a new writer block and one `$pgWriters +=` line, no existing rule changed; unit 3's merge waits for it |
