# 3B3 review

## Round 1 (discovery, W5): branch `task/3B3-structure-read` at `7f0ca4804`

Reviewer: fresh Claude reviewer (did not author the work), 2026-11-20. Read only; nothing in the worktree changed.

### Summary (15 lines max)

- **Verdict: REVISE** (accept once M1 is fixed on the branch; one Medium, one Low; no High). A small Sonnet fix
  round and a verification re-review of M1 and its sweep suffice.
- Parity holds: 47 factors x Kobo/Kisiwa/Mto x actual/plan equal `derived-values.json` to the cent (rerun, plus my own
  script); all 38 `SUM` factors equal `portfolio.lakeside-power.actual.sums`; computed `blocks` equal the pack's.
- The six honesty hunts: unknown is never zero (`_merge` propagates None; the only short cut is the NEUTRAL 0 in `*`);
  no leaf is labelled stronger than its source; only `composes == "SUM"` rows are summed, and the 38/9 split equals
  spec §2.4; k of n is `len(included)` of every Site asked for; mixed currencies give no value at node and portfolio;
  the price builder holds and disposes one store.
- **M1 (Medium):** a node with no value because of a node-level cause (`CURRENCY_MISMATCH`, `ZERO_DENOMINATOR`)
  passes no reason to its ancestors or to the portfolio, and `site_count` then names a declared MINI_GRID Site
  `STRUCTURE_NOT_DECLARED`. Proven by probe. Not reachable on today's leaves; reachable when `3A4` adds a tariff.
- **L1 (Low):** `build_structure_read` leaks the snapshot store if the price builder raises.
- Reruns: focused 149 passed; outcome regressions 78 passed; 3 plants each caught; flaky files 19/15/15 passed
  alone; architecture (incl. configuration persistence) and workflow checks passed. PG not rerun (slot held).
- Coordinator-verified, not a finding: the 11 `TEMPLATE_STALE` tests (template rebuild).

### Findings

**M1 (Medium; acceptance gap, spec §1 and §7 Q4). A node-level cause is lost above its node, and `site_count`
names the wrong reason.**
- Where: `backend/assetops_backend/structure/evaluate.py:251-254` (`_part_of` drops the child's `missing`),
  `:311` (ancestor `missing_leaves` is the child's empty tuple), `:354` (`excluded[site]` = `()`), `:357` (the empty
  portfolio's `missing_leaves` omits that Site); `backend/assetops_backend/structure/read.py:58`
  (`value.excluded.get(code) or ... or NOT_DECLARED`).
- What: Kobo with `productive_tariff` in KES and every other money leaf in USD (probe on the pack's leaves):
  `revenue` is None with `CURRENCY_MISMATCH:KES,USD` (correct), but `collected` and `contribution` are None with
  `missing = None` and `missing_leaves = ()`: no value and no reason. Composed with Mto, `contribution` is Mto's
  810.000 with `excluded = {"Kobo": ()}`, and `site_count` gives
  `SiteCount(k=1, n=2, out=(("Kobo", ("STRUCTURE_NOT_DECLARED",)),))`. Kobo is a declared MINI_GRID Site, so the
  screen would say its structure is not declared. With Kobo alone, portfolio `contribution` is None with no
  `missing_leaves` and no `missing`. The same holds for `ZERO_DENOMINATOR` (only `shortfall_backed` divides today,
  and `max(lost_unit_kw, 1)` keeps it non-zero, so in MINI_GRID the reachable case is currency).
- Why it matters: spec §1 requires "a `missing` record whenever the value does not rest on its own record", and Q4
  requires every composed value to name its excluded Sites with their reasons. Here the value is honestly absent
  (no zero, k is right), but the reason is false (`site_count`) or empty (ancestors, portfolio). Today's product
  cannot reach it (`tariff` is NOT_CONNECTED and `diesel_l` is HELD_NOT_CALCULATED), but `3A4`'s tariff provider
  makes it reachable on a Site whose tariff and declared prices differ in currency, with no change here (spec §3's
  promise), and `3B5` will read `site_count` as is.
- Fix: carry the node-level cause upward. For example, a node whose value is None and whose `missing_leaves` is
  empty names the blocking node (e.g. `missing_leaves` gains `revenue`, or `missing` inherits the first child
  `problem` with its own `blocks`), so every None has a nameable reason; and in `site_count` test membership
  (`code in value.excluded`) rather than truthiness, so a MINI_GRID Site is never `NOT_DECLARED`. Tests: the probe
  above (ancestor and portfolio reasons non-empty; `site_count` never `STRUCTURE_NOT_DECLARED` for a MINIGRID
  Site). Sweep (W6): every place that reads `missing_leaves` as the reason (`_compose_factor`, `site_count`).

**L1 (Low; preference-adjacent, not an acceptance gap). `build_structure_read` leaks the snapshot store if the
price builder raises.**
- Where: `backend/assetops_backend/structure/composition.py:36-39`.
- What: `snapshots` is built before `build_window_price_selection`; if the second raises, `snapshots.dispose()` is
  never called. `PostgresAssumptionStore(...)` construction rarely raises, so the risk is small.
- Fix: build the prices in a `try` that disposes `snapshots` on failure, or build both before wiring.

No other finding. I looked for and did not find: a zero default in `evaluate.py`, `sources.py` or `read.py`
(`Decimal(0)` appears only in `month_sum`'s start, reached only when a day is counted, and the leaf drops any
unstated day, D-3B3.17); a node evidence stronger than its weakest non-NEUTRAL part; a summed `NONE` row; an
`included` that counts a Site with no value; a price state other than PRICED giving a value.

### Checks I ran (this revision, `7f0ca4804`, worktree module paths verified)

- Module paths: `<wt>/backend/assetops_backend/__init__.py`, `<wt>/contracts/assetops_contracts/__init__.py`.
- Focused, no DB (`heavy-slot.sh --`): `test_3b3_structure_evaluate.py`, `test_3b1_structure_registry.py`,
  `test_3b3_window_price_selection.py`: **149 passed** in 2.73 s.
- Outcome regressions over `_month_reading` (`test_ch6_evaluator.py`, `test_k10_declared_none_board.py`,
  `test_walk1_productive_sales.py`): **78 passed**.
- PG (`heavy-slot.sh --db`, `assetops_test`): `test_3b3_structure_read_postgres.py`: **not rerun**. The first attempt
  timed out waiting for the database slot (1200 s), and the second was stopped while the coordinator's template
  build held `db-job`, so as not to queue ahead of the 11 template tests. Cited: the builder's 5 passed (`--db`).
- Parity probe (my own script over `derived-values.json`): 0 mismatches at 3 Sites x 2 sides x 47 factors;
  contribution Kobo 883.000/1445.000, Kisiwa -250.000/-65.000, Mto 810.000/915.000 (actual/plan) = pack.
- Plants (my own, in scratch copy `scratchpad/rev3b3-r1-plants`, each reverted):
  1. unknown read as zero in `+` and `-` (`evaluate.py` Bin): **9 failed**;
  2. mixed currencies summed in `compose`: **1 failed**;
  3. `unserved_critical_kwh` labelled `RECORDED` (stronger than its source): **1 failed**.
- Flaky files alone (`--db`, `assetops_test`): `test_w205b_ev_replay_api.py` **19 passed**;
  `test_w503_ev_depth_postgres.py` **15 passed**; `test_w503_ev_scenarios_postgres.py` **15 passed**.
- `check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON` set; without it the guard refuses to run, which is the
  guard's own rule, not a branch fault): **Architecture check passed**, including the configuration-persistence
  seam (only `chain/composition.py` and `financials/composition.py` build adapters; `structure/composition.py` reaches
  them through `build_snapshot_store` and `build_window_price_selection`).
- `check-agent-workflow.ps1`: **Agent workflow check passed**.

### Builder evidence cited, not rerun

- Focused 149 passed (matches my rerun); PG 5 passed; fast `check-all` 40 guards; 22 + 5 plants.
- Full host run: 4137 passed, 32 failed, 11 errors, at the `ae641e63b` era, before round 1's code commit
  `e46b3f28c`. The evidence file `/opt/assetecon/evidence/3B3/failing-files-branch-vs-base.md` shows 29 identical
  at base `bf72c735d` and 3 flakes.

### Coordinator-verified (not a finding)

- The 11 `TEMPLATE_STALE` tests, after the coordinator's template rebuild; before merge (rulings, round 1).

### Not verified

- The full suite at this head: the builder's full run predates `e46b3f28c` (round 1 code: `month_sum`'s third value,
  `site_count`, `build_window_price_selection`). Select-tests over that commit were not rerun here.
- The Docker runner.

### Residual risk the packet does not name

- `3B7a` storage: `FactorValue.unit` is a `Unit`, and `Coverage.grades`, `excluded`, `sites_excluded` are
  `MappingProxyType`; storing them needs an explicit serializer (the reviewer guide's risk; nothing here is stored).
- `month_sum`'s "stated" test is per day, not per subject: `critical_served` is SITE-subject (one row per day), so
  it is exact today; a multi-subject measure summed the same way would read a missing subject's value as covered.
- A leaf with a value and evidence `NOT_AVAILABLE` is not refused by `_check_leaf` (it would label its ancestors
  NOT_AVAILABLE while they hold a value). Weaker, not stronger, so not an honesty breach; worth a check when a
  provider lands.
# Review 3B3 round 2 (verification of M1 and L1), head 44c01338d

## Summary
- Verdict: ACCEPT. M1 and L1 are fixed; no new finding.
- M1: evaluate.py:310-312 names the node itself in missing_leaves when a node has no value and no inherited leaves, so
  every None carries a reason (own `missing` or `missing_leaves`), through ancestors and the portfolio.
  read.py:58-62 tests `code in value.excluded`, so a declared Site is never labelled STRUCTURE_NOT_DECLARED.
- L1: composition.py disposes `snapshots` on any exception from the price builder, then re-raises; test counts one dispose.
- Question settled: naming the blocking node satisfies spec §2.3 ("excluded maps every other Site to its missing_leaves"),
  D-3B3.13 (names Sites per factor) and the owner's "k of n sites, missing ones named". None of them asks for the
  cause on the portfolio. The cause stays on the Site's own node (`values["revenue"].missing.record_kind`), so 3B5
  can say why by reading that node. Optional, not a finding: 3B5 may want a helper; no change needed in 3B3.
- Checks: focused evaluate + price-selection 73 passed (my rerun, worktree module path verified). Plant in a scratch
  copy (disabled the M1 fallback) failed 2 tests (the currency and zero-denominator M1 tests), 70 passed. Not rerun:
  regressions, Postgres, check-all (cite the builder's runs). Not verified: 152 focused count (I ran 2 of the files).
