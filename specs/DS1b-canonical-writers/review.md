# DS1b review, round 1 (discovery, W5)

Reviewer: fresh Claude reviewer (not the author), 2026-11-20. Branch `task/DS1b-canonical-writers`, head
`943f49dac`, base `main` `b28326e48`. Reviewed in a scratch worktree at `943f49dac`, removed afterwards; the author's
worktree was not touched. No database, server or Docker was used.

## Summary (round 1)

- **Verdict: ACCEPT with Lows.** No High or Medium finding. One Low (a test gap), fixable on the branch or carried.
- Honesty holds when checked independently. An independent script recomputed all 142 records from the raw manifest
  YAML and `history.json`, using its own reading of spec §2 and not the module's tables. It found the same 142 keys,
  no missing record, no extra record and no value difference.
- R1: no budget line comes from a fallback field, and none names a leaf that `missing-records.json` lists as a plan
  ASSUMPTION (or RESIDUAL) in any month.
- R2: Kisiwa `om`, Thika `maint` and Kasarani `maintenance` for October are not written and are listed
  `ESTIMATED_NOT_RECEIVED`. GAP-1 is intact: Kisiwa October O&M is neither an invoice nor a zero.
- R5: all 7 batches are `source-emulated`. No output says RECORDED or Recorded, or claims stronger provenance.
- R6: ZERO_NO_ROW applies to the actual side only. Thika's plan liability is a `0.00` BUDGET_LINE.
- R7: each (Site, month, side, name) has one record. The Thika October credit note is `-108.00`.
- `history.json` is byte-identical. The CLI on the real manifest gives the golden digests. Two runs under different
  hash seeds give identical bytes.
- The 11 planted violations each failed at least one test.

## Scope and base (reviewer guide §1-3)

- `git diff --stat b28326e48...943f49dac` lists `records.py` (new), the `leaves.py`, `world/__init__.py` and
  `conftest.py` docstrings or help text, `tools/world_history.py`, `test_records.py`, `golden/records_v1.json`, and
  the finish bookkeeping: the packet, `mid-build-questions.md`, the spec status line, the `specs/INDEX.md` row and
  `.ai/state/data.md` with its index line. This matches spec §4 and guide §2.
- `history.json`, `golden/history_v1.json`, `world/history.py` and the pack are unchanged (`git diff --quiet` was
  clean).
- `records.py` imports `assetops_contracts.canonical` and copies nothing from it. T8 asserts this.
- **Tests first.** Commit `f0e86e0c6` (T1-T9, `test_records.py` only) comes before `6691f3dee` (the module). Both
  commits carry the same timestamp (07:15:40), so commit order is the only evidence. It is sufficient under W2, but it
  is not proof that the tests were seen failing.

## Findings

### L1 (Low, test gap; not an acceptance gap): the writers' source types are pinned only by the golden

- **Where.** `simulator/assetops_simulator/world/records.py:57,62` (`billing_export` for MINI_GRID,
  `customer_invoicing` for COLD_CHAIN). T3 is `simulator/tests/world/test_records.py:234-252`.
- **What.** T3 checks each writer's kind and category against `leaf_sources`, and checks that the kind is allowed for
  its source type. It does not check *which* source type spec §2.1 names. I planted mutation M8, which moves the
  COLD_CHAIN credit note to `billing_export` (2a allows ADJUSTMENT there too). Only T1's golden digest failed.
- **Why it matters.** The source type decides which emulator (`3A3`) and which held-source declaration (`DS3`, R6)
  the Thika credit note belongs to. A later `--update-golden` run for an unrelated reason would absorb the change
  silently.
- **Fix.** Add a literal assertion in T3 or T4 of spec §2.1's (structure key, field) to source-type column. The
  manifest does not carry the source type, so the assertion stays literal.

No other finding. I did not manufacture any.

## Honesty, checked by hand (task item 2)

The script is in the session scratchpad and was not committed. It reads the manifest with `yaml`, plus
`history.json` and `missing-records.json`. It derives each leaf's own field from `factor_map`'s first whole
`record.<f>` alternative, and it uses spec §2.1's writers.

| Check | Result |
|---|---|
| Expected vs written records | 142 / 142. Missing: none. Extra: none. Value or category differences: none. |
| R1 fallbacks | `NOT_OWN_LINE` covers `billed_kwh` and `diesel_l` (mini-grid, every month), `offpeak_kwh` and `kwh` (EV). No `delivered_kwh`, `necessary_l` or `kwh_2200_2400` line exists. No line names a leaf on any `missing-records.json` plan entry carried as ASSUMPTION or RESIDUAL, in any month. |
| R2 estimates | October `ESTIMATED_NOT_RECEIVED`: KISIWA-001 `om`, COLD-THIKA `maint`, EV-KAS `maintenance`. All three match `missing-records.json` actual `leaf` entries (NOT_RECEIVED, "carried as ESTIMATED"). None was written. History-month coverage is RECORDED everywhere. GAP-1 ("line ESTIMATED; never zero") is intact. |
| R5 labels | All 7 envelopes carry `provenance: source-emulated` and `source_system: assetops-world-generator`. A byte scan of the batches found no `RECORDED`, `Recorded`, `recorded`, `observed`, `field-integrated`, `bench-tested` or `Simulated`. `ESTIMATED` appears only as the reason word in `unwritten.json`, which is not a record and is required by spec §2.3. |
| R6 zeros | Thika actual `liability` 0 in Jul-Sep gives `ZERO_NO_ROW` (3 rows, actual side). Thika plan `liability` 0 gives a BUDGET_LINE `0.00` with `currency USD`, in all four months. |
| R7 uniqueness | 142 IDs, 0 duplicates. |
| Credit note | `gen:COLD-THIKA:2026-10:actual:liability`: ADJUSTMENT `-108.00 USD`, `effective_from 2026-10-01`, `customer_invoicing`. Manifest actual `liability: 108.0`, coverage RECORDED. `derived-values.json` Thika actual `liability` is 108.0. |
| derived-values | Kobo `om`/`staff` (600/500), Thika `maint`/`staff`/`crate_days` (80/350/8680), Embakasi plan `peak_kwh`/`max_kw`/`maintenance` (26040/450/600) and Kasarani plan `maintenance` (300) all equal the written values. |

**Sampled in full** (envelope, clocks, body, money text):

- Mini-grid: `gen:KOBO-001:2026-10:actual:om` (EXPENSE OM `600.00`, `2026-10-31T17:00:00+03:00`, PAID, `om-contractor`) and `gen:MTO-001:2026-08:plan:staff` (BUDGET_LINE `450.00`, `currency USD`).
- Cold chain: `gen:COLD-THIKA:2026-09:actual:maint` (`80.00`, from 8000 cents, `2026-09-30T17:00`), `gen:COLD-MWEA:2026-10:plan:crate_days` (`7440`, no currency) and the credit note above.
- EV: `gen:EV-RUI:2026-10:actual:maintenance` (`500.00`), `gen:EV-EMB:2026-10:plan:peak_kwh` (`26040`), `gen:EV-EMB:2026-07:plan:max_kw` (`450`) and `gen:EV-KAS:2026-10:plan:maintenance` (`300.00`).

Every record has the 2a canonical shape. Money is text with two places, non-money is plain decimal text, and there
is no float.

**Unwritten list.** It has 341 rows: NOT_A_MONTH_RECORD 244, NOT_READ_BY_A_LEAF 43, NOT_OWN_LINE 36,
READ_IN_AN_EXPRESSION 12, ESTIMATED_NOT_RECEIVED 3, ZERO_NO_ROW 3. These equal the packet and the golden. The
independent recomputation shows that no skipped field should have been written, and no written record should have
been skipped. T5's disjoint-and-complete test covers the rest.

## Reruns (task items 4 and 5)

| Command (scratch worktree at `943f49dac`) | Result |
|---|---|
| Module paths, with `PYTHONPATH` set to the scratch worktree's backend, backend/tests, contracts, simulator, gateway, field, host and tools | `records.py`, `assetops_contracts/canonical/__init__.py` and `assetops_backend/__init__.py` all resolve under the scratch worktree |
| `tools/heavy-slot.sh -- pytest simulator/tests/world -q` | `122 passed in 4.92s` |
| `tools/heavy-slot.sh -- pytest backend/tests/test_2a_canonical_v1.py backend/tests/test_2a_canonical_manifest_parity.py -q` | `180 passed in 2.60s` |
| `tools/checks/neutral_tests.py` | exit 0: `487 passed`, simulator/tests 481, contracts/tests 6 |
| `check-architecture.ps1` (`ASSETOPS_GUARD_PYTHON` set to the shared venv) | `Architecture check passed.` |
| `check-agent-workflow.ps1` | `Agent workflow check passed.` |
| CLI `records` on the real manifest, run under `PYTHONHASHSEED` 1 and 7 into two fresh scratch directories | exit 0 both times; `diff -r` identical; all 7 batch sha256 values and `unwritten.json` equal `golden/records_v1.json` |
| CLI `generate` on the real manifest vs committed `history.json` | `cmp` identical |

I did not rerun the full suites or check-all. I cite the implementer's fast check-all at `3ed5f3dee`: 40 of 40
guards passed. The only later commits are bookkeeping and the packet.

**Planted violations.** Each was a one-line edit to `records.py`, run against `simulator/tests/world`, then reverted
with `git checkout`. The tree was clean afterwards.

| # | Violation | Caught by |
|---|---|---|
| M1 | Fallback budget lines (every alternative maps to its leaf) | T1, T2, T4, T5, T6, T7, ... (build refused) |
| M2 | ESTIMATED October cost written as an invoice | T1, T5 `unwritten_list` |
| M3 | A record labelled `Recorded` (`version_ref`) | T1 byte scan, T4 clocks |
| M4 | Duplicate (Site, month, field) record | T1, T2, T4, T5, T6, T7 (2a duplicate refusal) |
| M5 | Float `value` on a BUDGET_LINE | T1, T2, T4, T5, T6, T7 (format refusal) |
| M6 | ZERO_NO_ROW applied on the plan side | T1, T5 (both) |
| M7 | Credit-note sign flipped (+108.00) | T1, T4 sums |
| M8 | COLD_CHAIN credit note in `billing_export` | **T1 golden only** (L1) |
| M9 | Provenance `source-recorded` | T1, T2, T4, ... (2a refusal) |
| M10 | ESTIMATED skipped for Thika and Kasarani but not for Kisiwa `om` | T1, T5 |
| M11 | NOT_OWN_LINE fields dropped from the unwritten list | T1, T5 (both) |

## Deviations judged (task item 6)

- **Worktree path.** The build used `.claude/worktrees/ds1b`, where spec §0 names `/opt/assetecon/AssetOpsV1-ds1b`.
  The dispatch named only "a new worktree", and no output or path in the code depends on the location. Accept.
- **Extra public names.** The module also exports `Writer`, `READ_IN_EXPRESSION`, `money_text`, `SOURCE_ORDER`,
  `SOURCE_SYSTEM`, `PROVENANCE` and the reason constants. They are additive and not a contract change.
  `READ_IN_EXPRESSION` is derived independently by T3. Accept. The Architect may later add these names to spec §4's
  list.
- **October taken from `accounting_period`.** Spec §2 says "October is read from the view", and the view's period
  label is `accounting_period`. It equals `history.anchor_period` in the fixture and in the manifest. Accept. See the
  residual risk on overlap below.
- **The `expected_technical_loss_kwh` grep hit** (`records.py:74`). It is spec §2.2's literal record-field name in
  `PASS_THROUGH`, not a read of the `expectations` key, and the view's allowlist excludes that key anyway. Accept.

## Not verified

- Mid-build Q1 (the reason for an ESTIMATED zero liability) and Q2 (exponent text). They are being ruled separately.
  Neither case occurs in the fixture or the manifest, so no byte depends on them.
- The coordinator's output run into `/opt/assetecon/generated/ds1b-<rev>/`, and the downstream DS3 load, 3A3 native
  files and 3A5 labels.
- The full suites and check-all (the implementer's same-revision fast check-all is cited above).

## Residual risk not named in the packet

- **DS3 must carry the unwritten list's reasons.** In the store, Kisiwa, Thika and Kasarani October cost lines are
  simply absent. GAP-1 stays honest only if DS3 or 3B6 reads `ESTIMATED_NOT_RECEIVED` and coverage as "estimated from
  plan", not as MISSING without an estimate and not as 0. `derived-values.json` evaluates Kisiwa actual `om` at 700
  (the estimate), so a store-only re-evaluation will differ there by design.
- **No guard against overlapping months.** Nothing asserts that `accounting_period` is not among the history months.
  If it were, the written records would collide and fail safely as `DS1B_FORMAT` (2a's duplicate check), but the
  unwritten list would double-list rows without any error. This does not happen in today's inputs.
- **Reconciling finer records.** As the guide notes, 3A3 and DS2 records for the same (Site, month, field) must
  reconcile to these month lines or replace them (D-DS1B.8). This is not a DS1b defect.
- **Review location.** This file is at `.agent/review-DS1b-r1.md`, as the dispatch asked. The standing brief puts
  reviews in `specs/DS1b-canonical-writers/review.md`, so the coordinator should copy it there at merge, as was done
  for 2a and T2.
