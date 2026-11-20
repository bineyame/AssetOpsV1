# 3B1 handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

## Reviewer questions

Fresh Reviewer (Claude), 2026-11-20, on `main` at `2f5f2ce3c`. Read-only; no database, server or Docker touched.
Severity: High blocks coding, Medium needs an answer before coding, Low may take the default.

**Checked, no question.** A throwaway probe (yaml + `ast` + `assetops_contracts.canonical`, outside the repo) found:
- the 16 node IDs and expression texts of spec §2.2 equal `structures.MINI_GRID` (manifest :816-832) character for
  character, in the same order;
- the 31 leaves equal `factor_map.MINI_GRID` (:870-901), `leaf_sources.MINI_GRID` (:1640-1671) and
  `leaves_of("MINI_GRID")`, in the same order; no ID is both a leaf and a node;
- every name in the 16 expressions is a row;
- `home_categories.nodes.MINI_GRID` (:1373-1422) has 49 names: the 47 rows plus `cover_not_claimable` and
  `unclaimable_cover` (D-3B1.5); every row has a home;
- §2.2's homes equal the manifest's;
- every node composes under D-3B1.2 to §2.2's unit (catalogue units from `factors.py:49-79`);
- no money row sits under protect or assure, and no objective letter differs from its heading;
- `period_days` is the only CALENDAR / NEVER_EMPTY leaf.

So the 47 rows match the pack exactly. There is no High.

**R1 ABOVE and CALENDAR next to the four category codes (§2.3, §4) — Medium (done).**
- *Why.* `HOMES` (spec.md:100-103) puts two placements beside the catalogue's four categories
  (`outcomes/catalogue.py:9`). Two problems follow:
  - `STRUCTURE_MONEY_HOME` (spec.md:153) is a deny-list, so a money row homed `CALENDAR` passes. Nothing ties
    `CALENDAR` to a calendar leaf, and nothing ties `ABOVE` to a node.
  - A later reader (3B2 parity, 3B5's board) that groups by `HOMES.values()` shows six headings, not four.
- *Evidence.* Manifest :1403 `contribution: [above]`, :1422 `period_days: [calendar]`, and the rule at :1371;
  `decision-loop-specification.md` §3 `home_category` row ("Exactly one of the four … or ABOVE … or CALENDAR").
- *Proposed.*
  - Keep both codes as placements. Import `CATEGORIES` from `outcomes/catalogue.py` rather than retyping it, and add
    a test that the four category values of `HOMES` equal `CATEGORIES`.
  - Make `STRUCTURE_MONEY_HOME` an allow-list: money only under `GROW_REVENUE`, `OPTIMIZE_COST` or `ABOVE`.
  - `STRUCTURE_CATEGORY` also refuses:
    - `CALENDAR` on anything but a leaf of family `CALENDAR`, and the reverse;
    - `ABOVE` on a leaf.
  - Each rule gets one T3 case. A category read iterates `CATEGORIES`, never `HOMES`.

**R2 Integer literals as Decimal (§3) — Low (done).**
- *Why.* spec.md:122 says "numeric literals … as Decimal" but does not fix which source texts count. `ast` gives
  `True` as a bool Constant, `1e3` as a float, `0x10` and `1_000` as ints, and `1j` as a complex (probe).
  `Decimal("1_000")` is accepted silently. The pack's `num()` (`evaluate_structure.py:58-63`) refuses bool.
- *Proposed.*
  - Every numeric literal, int or not, is `Decimal(<source segment>)`, and the segment must fullmatch
    `[0-9]+(\.[0-9]+)?`.
  - Exponent, hex, underscore, bool, `None`, complex, str and bytes are refused with `STRUCTURE_EXPRESSION`.
  - `-1` is unary minus over the literal `1`.
  - T5 adds `True`, `1e3` and `1_0`.

**R3 Do `children` keep repeats? (§2.3) — Low.**
- *Why.* spec.md:112 says "the names in the expression, in first-seen order". It does not say whether a repeated
  name appears twice, or whether `min`/`max`/`ceil`/`floor` are names.
- *Evidence.* The probe found no mini-grid expression that repeats a name, so no figure depends on the answer
  today. 3B6's rows may.
- *Proposed.* `children` is a tuple of distinct factor IDs in first-seen order, with function names excluded.

**R4 Does `expression` supersede the design's `kind` and signed `children`? (§2.3) — Low.**
- *Why.* The design's record has a `kind` and "children: ordered (factor ID, sign) pairs"
  (`decision-loop-specification.md` §3, Records table). 3B3 combines "by its kind", and 3B2 checks "a parent total
  whose change its children explain". The spec drops both without a ruling.
- *Proposed.* A ruling (D-3B1.7) that the expression is the record: `kind` and sign are read from the parsed `Expr`
  by 3B2 and 3B3, and are not stored.

**R5 Does the start-up check also run in `host/lab_app.py`? — Low (no change).**
- *Evidence.* `host/lab_app.py:137` returns `create_app(resolved, execution=execution, **overrides)`, and :140 is
  `app = build_app()`. `main.py:832` `app = create_app()` runs at import. The other `FastAPI()` calls
  (`tools/demo_combined_kobo.py:344`, `tools/w504_ev_work_walkthrough.py:163`) are tool apps, not the product.
- *Proposed.* No second call. The check runs wherever `create_app` runs, and the packet says so.

**R6 Start-up cost (§5) — Low.**
- *Why.* `create_app` is called at 124 sites in 51 test files, plus once on import of `main`, so a slow check
  multiplies.
- *Evidence.* Parsing and walking the 16 expressions takes 0.23 ms per pass (probe, 1,000 passes).
- *Proposed.*
  - No caching: the check stays pure, and T4's monkeypatch works.
  - The packet reports `check_all()` as the first-call time plus the median of 1,000 calls (`timeit`).
    `create_app()` is not timed before and after; that number is noise.
  - The bound of 10 ms stands.

**R7 T1 maps homes through the code's `HOMES` (§6 T1) — Medium (done).**
- *Why.* spec.md:176 compares every home "mapped through `HOMES`", so the expectation uses a constant of the code
  under test. That breaks W2 and the guide's first check 2 (reviewer-guide.md:16-17). A swap of `ABOVE` and
  `CALENDAR` in `HOMES` would pass both T1 and the letter check.
- *Proposed.* T1 writes its own literal map (`grow` → `GROW_REVENUE` …), and asserts the four category values
  against `outcomes.catalogue.CATEGORIES`.

**R8 `parse(text)` cannot name `<key>/<factor>` (§3, §4) — Medium.**
- *Why.* spec.md:120 gives `parse(text)` with no key or factor. Yet spec.md:127 has it raise
  `StructureError("STRUCTURE_EXPRESSION <key>/<factor>")`, and spec.md:138 constructs
  `StructureError(code, structure_key, factor_id)`.
- *Evidence.* `ast.parse(" x", mode="eval")` raises `IndentationError` (probe), so syntax errors need mapping too.
- *Proposed.*
  - `parse` raises `ExpressionError(reason)`, which is not a `StructureError`.
  - `check` turns any `ExpressionError`, `SyntaxError` or `ValueError` from parsing into
    `StructureError("STRUCTURE_EXPRESSION", key, factor_id)`.
  - `StructureError` carries `code`, `structure_key` and `factor_id`, and `str()` is
    `"<CODE> <structure_key>/<factor_id>"`.

**R9 Check order and row order (§2, §4) — Medium (done).**
- *Why.* "In this order, over the rows in table order" (spec.md:139) can mean code-major or row-major.
  - `STRUCTURE_UNKNOWN_FACTOR`, `STRUCTURE_CYCLE` and `STRUCTURE_UNIT` need every row parsed first.
  - The guide's planted cycle (`diesel_l` reads `fuel_cost`) trips `CYCLE` on both `diesel_l` and `fuel_cost`,
    and `UNIT` on `diesel_l`. T3 must know which text to expect.
  - The node order inside `ROWS` is not stated; §2.1 fixes only the leaf order.
- *Proposed.*
  - Code-major: each code runs over all rows before the next code.
  - `ROWS` holds the 31 leaves in `leaves_of` order, then the 16 nodes in §2.2's order.
  - `CYCLE` names the first row in `ROWS` that lies on a cycle (`diesel_l` here).
  - `UNIT` composes a node from its children's declared units, so a node is blamed only for its own expression.

**R10 The catalogue check runs one way only (§4 `STRUCTURE_CATALOGUE`) — Medium (done).**
- *Why.* spec.md:147 refuses a leaf row that is not in the catalogue, but not a catalogue leaf with no row. Four
  leaves feed no node: `customer_hours_interrupted`, `field_visits`, `liability` and `unserved_critical_kwh`
  (probe). Deleting one of those rows still starts; only T1 notices, and only in tests.
- *Proposed.* `STRUCTURE_CATALOGUE` also fires:
  - for an ID in `leaves_of(key)` with no row, named by that ID;
  - for a node whose ID is a catalogue leaf ID;
  - for a `structure_key` outside `STRUCTURE_KEYS`, as `STRUCTURE_CATALOGUE <key>/-`, never a bare `KeyError`.

  Add a T3 case for the first.

**R11 Objective presence and form (§2.3, §4 `STRUCTURE_OBJECTIVE`) — Low (done).**
- *Why.* spec.md:152 checks only the letter. It does not say whether a Grow row may have `None`, or whether `G10`,
  `g1` or `G0` pass.
- *Proposed.*
  - The four categories require an objective matching `[GOPA][1-9]`, with the category's letter.
  - `ABOVE` and `CALENDAR` require `None`.
  - Any other case is `STRUCTURE_OBJECTIVE`.

**R12 Tolerance semantics differ from the design (§2.1, D-3B1.4) — Medium.**
- *Why.* The design's record says "tolerance: the OD-3 tolerance, in the factor's unit"
  (`decision-loop-specification.md` §3). The spec stores a percentage of another factor (spec.md:68). In the
  manifest, `tolerance_pct: 2.0` is a per-site value in each site's `fuel_balance` record (:116, :198), not a
  structure constant; cold rooms carry 5 (:434).
- *Proposed.*
  - Rule that "per cent of `of_factor`" supersedes "in the factor's unit" for this row.
  - The registry's value is the structure default, and a site's declared value (step 5, 3B4) overrides it.
  - `of_factor` must be a row (`STRUCTURE_UNKNOWN_FACTOR`) with the row's own unit (`STRUCTURE_UNIT`), and
    `pct > 0`.
  - T1 asserts that every mini-grid site's `fuel_balance.tolerance_pct` in the manifest equals 2.0.

**R13 `words` is not carried (§2.1, `FilledBy`) — Medium (done).**
- *Why.* P3B says a missing value reads "not available yet" with the record that would fill it.
  `structure-specification.md` §3.1 puts `record_words` "where declared" in every missing entry, and the pack copies
  it (`evaluate_structure.py:653-658`). The manifest gives words for `om` and `staff` (:1658-1659), and it names
  only `slice` and `trigger` as pack-only (:1629-1630). The spec's `FilledBy(family, kind)` drops the words, so 3B3
  has nowhere to read "Service contractor invoice" from except the system kind "EXPENSE (OM)".
- *Proposed.* `FilledBy(family, kind, words: str | None = None)`, copied verbatim, with T1 comparing it.

**R14 Where validation lives (§2.3, T3) — Medium.**
- *Why.* T3 plants invalid values with `dataclasses.replace`. If `FactorRow`, `Home` or `FilledBy` validate in
  `__post_init__`, as `Unit` does (`units.py:41-44`), planting raises `ValueError` before `check` runs, and the
  code is never proven.
- *Proposed.* The records do no validation; every refusal lives in `check`.

**R15 `Expr` is an undefined cross-slice contract (§3) — Medium (done).**
- *Why.* spec.md:120 returns `Expr`, and 3B3 evaluates it, so its shape is a seam the implementer would otherwise
  design (RULES §7: a choice the spec did not fix is a spec defect). Arity is not fixed either.
- *Proposed.*
  - Frozen dataclasses: `Num(value: Decimal)`, `Ref(name)`, `Bin(op in "+-*/", left, right)`, `Neg(operand)` and
    `Call(func in {min, max, ceil, floor}, args: tuple)`.
  - `ceil` and `floor` take exactly 1 argument, and `min` and `max` at least 2. Anything else is
    `STRUCTURE_EXPRESSION`.

**R16 Edges of the literal rule (§3, D-3B1.2) — Low.**
- *Why.* The spec does not cover a literal-only subtree inside a larger expression (`x - (1 + 1)`, or `-1`).
  Spec.md:134 makes an expression of literals only dimensionless, which would refuse `x - (1 + 1)` for a kWh `x`.
- *Proposed.*
  - A literal-only subtree is unit-free and adapts to its place, like a single literal. It becomes `ONE` only at the
    top of the expression or as an operand of `*` or `/`.
  - Unary minus keeps its operand's unit.
  - T2 adds `x - (1 + 1)` and `max(x, -1)`.

**R17 A node that carries leaf fields (§4) — Low.**
- *Why.* A node with `filled_by`, `absent` or `tolerance` set passes silently.
- *Proposed.*
  - A node with `filled_by` is refused as `STRUCTURE_LEAF_SOURCE`.
  - A node with `absent` is refused as `STRUCTURE_LEAF_ABSENT`.
  - A tolerance on a node stays allowed only if R12 says so.

**R18 `mid-build-questions.md` is another slice's file — Medium (process).**
- *Why.* `specs/3B1-structure-registry/mid-build-questions.md:7-26` is DS1b's text (`records.py _actual`,
  `DS1B_NUMBER`), and it reads "Count: **2**" before any 3B1 code exists. The packet's count would be wrong.
- *Sweep.* `grep -rln DS1B_NUMBER specs` finds the same copy in `specs/3A1-commercial-record-store/` and
  `specs/3C1-person-on-commands/`.
- *Proposed.* The Architect resets all three to the empty template with "Count: 0".
- *Also.* `rulings.md:3` says the index lines are in `index-rulings-7.md`; they are in `index-rulings-8.md:12-17`.

**R19 Leaf units must be written literally (§2.1, D-3B1.1) — Low.**
- *Why.* If `ROWS` writes `unit=LEAF_FACTORS[id].unit`, the unit half of `STRUCTURE_CATALOGUE` can never fire on
  real rows.
- *Proposed.* Leaf units in `ROWS` are literal unit constants (`KWH`, `MONEY / KWH` …), so the check compares two
  independent declarations. The same holds for `filled_by` and `absent` text: never read from YAML.

## Implementer pre-flight

Same agent, playing the Implementer's pre-flight against `main` at `2f5f2ce3c`. The numbers are P1 ... as dispatched;
they are not the reviewer guide's probes P1-P5.

**P1 Tests run against the worktree's own packages (§0) — Low (verified).**
- *Evidence.*
  - The shared venv's editable finders append to `sys.meta_path`
    (`.venv/.../__editable___assetops_backend_0_0_0_finder.py:74-76`), so the path finder over `PYTHONPATH` wins.
  - With `PYTHONPATH=/opt/assetecon/AssetOpsV1-2a/backend:…/contracts`, `find_spec` resolved both packages inside
    that tree.
  - The `fixtures` package is covered by `$PWD/host`.
- *Proposed.*
  - Keep spec §0's command, and run tests as
    `env -u DATABASE_URL -u ASSETOPS_TEST_DATABASE_URL $PY -m pytest …`. With `ASSETOPS_TEST_DATABASE_URL` set,
    pytest refuses to start outside a heavy slot (`backend/tests/conftest.py:141`). With `DATABASE_URL` set,
    `create_app` composes Postgres stores (`main.py:348`, `:356-357`).
  - T1 finds the manifest by `Path(__file__).resolve().parents[2]`, as `test_2a_canonical_manifest_parity.py:28-31`
    does, so it reads the worktree's manifest.

**P2 Where the call goes, and the merge with 3C1 (§5) — Medium.**
- *Evidence.*
  - "Before any router is built" falls between `main.py:341` (`install_handle_error_hook()`) and `:345`
    (`include_router(health_router)`).
  - 3C1 edits `main.py:267` (signature), `:347-351` (the accounts block) and `:578-694`, and adds its own
    `ConfigurationError` (3C1 spec.md:30, :90).
  - `create_app` has a local `registry = ImportedSiteRegistry(…)` (`main.py:358`).
  - The existing graph check raises `ChainGraphError`, a `ValueError` (`chain/graph.py:56`), not
    `ConfigurationError`.
- *Proposed.*
  - `structure/check.py` exposes `check_at_start()`, which runs `check_all()` and re-raises
    `ConfigurationError(str(e)) from e`.
  - `main.py` gets those two lines immediately after :341, as a function-local import plus the call. They sit 5
    unchanged lines from 3C1's hunk, with no top-of-file import edit.
  - Never import a name `registry` into `main`.

**P3 What T4 monkeypatches (§6 T4) — Low.**
- *Why.* If `check.py` does `from .registry import REGISTRIES`, patching `registry.REGISTRIES` has no effect.
- *Proposed.*
  - `check_all(registries=None)` reads `registry.REGISTRIES` at call time, and T4 patches that module attribute.
  - Importing `main` first runs the real check (`main.py:832`). That is fine and also proves the "starts" half.

**P4 Loading the yaml in T1 (§6) — Low.**
- *Evidence.* `yaml.safe_load` of the manifest takes 421 ms; `CSafeLoader` takes 53 ms (probe).
- *Proposed.* Load once per module, with a module-scoped fixture or `lru_cache`, using `yaml.CSafeLoader` when it is
  present.

**P5 A manifest-only change selects no parity test — Low (residual, not 3B1 scope).**
- *Evidence.* `tools/select-tests.py:53` lists `Docs/*` as no-backend, and :63 sends the manifest to the neutral
  tier only. A later edit to `structures` or `home_categories` therefore runs `test_3b1_…` and `test_2a_…` only at
  the merge's full tier.
- *Proposed.* A queued tooling item that maps the manifest to the two parity files. No 3B1 change.

**P6 Packaging and guards — Low (verified).**
- *Evidence.* `backend/pyproject.toml` `packages.find include = ["assetops_backend*"]` picks up `structure/` once it
  has an `__init__.py`. `tools/checks/module-roots.ps1` lists roots, not subpackages.
- *Proposed.* No guard registration needed.

**P7 Bounds already name non-rows — Low (residual, for 3B3).**
- *Evidence.* `evaluation.bounds.MINI_GRID` and `protect_nodes.MINI_GRID` (manifest :962-975) name
  `cover_not_claimable` and `unclaimable_cover`, which D-3B1.5 keeps out of version 1.
- *Proposed.* Note for 3B3: any bound or Protect list it reads must tolerate, or refuse by name, a node with no row
  until `9a0`. No 3B1 change.
