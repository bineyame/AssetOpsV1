# 3A3 reviewer guide (rev 2)

For the fresh Reviewer: first at the handshake (read `spec.md`, `rulings.md` and this guide; put questions in
`handshake.md`), then at the review. Depth: discovery (W5): the seam over who writes commercial records, the RC4
boundary for loaders, and a new shared contract that `3A6` and every real adapter must pass.

## First checks

1. **Scope.** The diff holds only spec §7 question 9's list.
2. **No migration**; `alembic heads` unchanged.
3. **Module paths** in the packet resolve to the worktree for all three packages.
4. **RC4-F1 merged first.** `database_target` exists on the branch's base; the loader uses it, never `make_url`.
5. **3A2 unchanged in behaviour.** The 3A2 service, API and Postgres files pass with only the `read(data,
   context=...)` signature change; no expected value in them moved.

## Done means

Spec §7's nine questions answered yes with real output: the contracts file (through the T2 guard or directly), the
service, single-writer, emulator and loader files, the Postgres file through `tools/heavy-slot.sh --db`, the regression
set, check-all, and each plant below failing its named test.

## Planted violations (plant, run, revert; each must fail a named test)

| # | Plant | Must fail |
|---|---|---|
| V1 | Remove `refuse_operator_database` from the loader | L1 |
| V2 | Make the operator-name check case-sensitive (`startswith("assetops_op")` on the raw name) | L1 `[ASSETOPS_OP_X]` |
| V3 | Add `CommercialRecords(store, clock=...)` and an `.ingest(` call to `tools/world_history.py` | S1 |
| V4 | Restore `build_commercial_records` in the composition | S1 |
| V5 | On a map miss, write the raw cell instead of refusing | contracts 4 and C8 |
| V6 | Accept reordered headers (match by name) | contracts 2 and C8 |
| V7 | Drop rule C (write the `quantity.unit` constant on every expenses row) | contracts 5 and C1 (expenses) |
| V8 | Round the KOBO-001 kWh split (`round(billed / 40)` for every customer) | E2 |
| V9 | Write an O&M expense for KISIWA-001 from the plan | E5 |
| V10 | Register a fifth reader in `READERS` without a contract case | S2 |
| V11 | Ignore `ReadResult.refused` in `_check` | C8 |
| V12 | Drop `body.account_ref` from the billing `Account` column | contracts 1 and C1 (billing) |
| V13 | Let the loader mix `acme.budget.csv` with `acme.budget_workbook.json` | L3 |
| V1b | Decide the loader's refusal on `make_url(url).database` instead of `database_target` | L1 (`?dbname=`, `/`, `PGDATABASE`) |
| V14 | Skip the held-uploads path check (step 5b) | L5 |
| V15 | Accept a row holding NUL (drop the control-character rule) | contracts 2 |
| V16 | Fix `source-emulated` in `LayoutReader` whatever `real_data` says | C10 |
| V17 | Narrow S1 to `.ingest(` calls only | S1 (bound-method and `getattr` sources) |
| V18 | Let the same person submit and accept | L3 (`PERSON_SAME_FOR_BOTH`) |
| V19 | Carry DS1b's unwritten rows unfiltered | E9 |
| V20 | Remove the no-connect fixture from the loader file | its self-test |

## Probes

- **The seam.** S1's reach is ruled (D-3A3.12): alias imports, bound methods and `getattr` with the constant are
  caught; `importlib` and string-built names are not. Check the four inline sources fail and the residual is in the
  packet.
- **Independence (W2).** The goldens' expected JSON and E2 to E6's literals are written by hand; check none is
  produced by `read_layout`, `build_exports` or a helper they share.
- **Words.** Render a native refusal for row 3 as the person reads it ("Row 3, Category: this value is not one this
  layout knows.").
- **RC4.** The loader refuses before any connection: the spies in L1 see no call, the no-connect fixture would raise
  if one were tried, every such URL's host is `rc4.invalid`, and no Postgres test names an `assetops_op` database.
- **Provenance.** On an operator database a layout file is `observed-financial` and its `reader` says it was
  reshaped (D-3A3.10); a canonical JSON batch stamped `source-emulated` is still refused there.
- **Honesty.** No emulated figure without a manifest source; Kisiwa's O&M is absent, never 0.
