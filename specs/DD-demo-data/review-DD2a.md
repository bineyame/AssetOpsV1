# Review: DD2a (DD2.2 Lows, DD2.1, DD2.5), `task/DD2-books` at 599f9f21e

## Round 1: discovery review (2026-11-22)

**Verdict: ACCEPT WITH FINDINGS FIXED ON THE BRANCH.** One Medium (M1), three Lows. The fix is small and local to
`tools/dd_check.py` and its test. A verification re-review of M1 is enough.
Judged against `packet-DD2a.md`, spec §5.1, §5.4, §7 DD2 and §8.1 (C-DD2 to C-DD4), rulings D-DD.48 and D-DD.53 to
D-DD.57, and `review-DD2.2.md`. DD2.2's L1 and L2 are closed: `bool` on a coded path or on `source_record_id` is refused at
`{pw}.type` and by `check_layout`, and the 3A6 spec row lists `bool`. DD2.1 meets D-DD.48: the node table, parity with
`M`, `ZERO_LEAVES`, the October `EMU_NODE` check on both sides, the plan side and cents against dollars. It meets
D-DD.53: Kobo October is 400 L on 26 Oct, then 400 L on 1 Oct and 380 L on 8 Oct, the last note says its remainder, and
notes are at 10:00. It meets D-DD.54: one staged file, every DS1b record in exactly one place. DD2.5's statements file is
right for Lakeside's history months. **But C-DD3, as it goes live, crashes on the real inputs**: the EV clause reads a
history field that does not exist. So C-DD3 can never PASS, and it never reports its mini-grid judgement (M1).
Counts: High 0, Medium 1, Low 3.

### Findings

**M1 (Medium, acceptance gap: C-DD3 cannot be judged on the full inputs).** `tools/dd_check.py:421`
(`expected = Decimal(str(record["energy_cost"]))`) is reached for every metro-bus history month. `history.json` holds no
`energy_cost` for any EV Site in July to September (Embakasi has `kwh`, the band kWh, `max_kw` and `maintenance`;
Kasarani has `kwh` and `maintenance`). The live path (`_judged(judge_identities)`, `tenants=None`) therefore raises
`KeyError: 'energy_cost'`. `run()` turns that into `C-DD3 FAIL could not be judged: KeyError`. I reproduced it: with the
real `read_inputs`, `judge_identities(inputs, [])` crashes, and with `tenants={"lakeside-power"}` it returns 12 detail
lines. This matters for three reasons:
- §7 DD2.5 says C-DD3 "goes live for the decided books", but no store can ever make it PASS.
- Once DD5 loads the books, a mini-grid identity failure would be hidden behind the crash.
- The clause does not test the identity §8.1 and the manifest `checks` state (`ev: energy_cost == peak_cost +
  offpeak_cost + demand_cost`). It compares the lines with a history leaf instead.

The tests did not catch it: `simulator/tests/world/test_dd2_checker_on_emulated_rows.py` judges C-DD3 and C-DD4 only
with `tenants=LAKESIDE`. `backend/tests/test_dd2_check.py:62` runs only `judge_kinds` over all tenants.
Fix:
1. A Site-month missing a figure the judge needs becomes a FAIL detail line, never an exception. The same applies to
   cold's `record["crate_days"]` at `:416`.
2. The EV clause judges the stated identity on stored rows: the invoice's energy-cost total equals the sum of its band
   and demand lines. Until DD4.4 it carries `pending: EV energy invoices are DD4.4's`, so the measured kind is not
   judged as if it were decided.
3. Add one test that runs `judge_identities` and `judge_leaves_and_nodes` on the real inputs with `tenants=None` and
   asserts no exception.

**L1 (Low, residual risk: SQL not exercised).** `tools/dd_check.py:326` (`BOOK_QUERY`) runs against no database in
any test. The heavy `--db` run covered the ds4 world, DDR and WK, not `dd_check`. I checked the columns by reading the
schema: `commercial_record_revision` in migration 0063 has `tenant_id`, `site_id`, `kind`, `recognition_period`,
`effective_from`, `occurred_at`, `provenance` (`source-emulated` is an allowed value), `amount`, `quantity`, `status`,
`canonical text` and `supersedes_revision_id`. `tenant.slug` and `site.site_code` are in 0001. All of them match, and
there is no RLS on these tables. A typo would surface only at DD5.
Fix (optional): one `--db` test that loads a small batch and asserts `stored_books` returns it, or a note that DD5's
first C-DD2 run is the SQL's first proof.

**L2 (Low, tidiness).** `tools/dd_check.py:337`: `BOOK_MONTHS` is defined and never used, because `_site_months`
iterates `history.meta.months` plus the accounting period. Delete it, or use it to assert the four months.

**L3 (Low, preference, not an acceptance gap).** C-DD3's mini-grid clause (`:403-414`) omits the manifest's
`diesel_cost == diesel_l x price` identity. §8.1 lists only the two revenue identities, so this is spec-conformant.
C-DD4's node clause covers `fuel_cost = diesel_l * diesel_price` on every history month and October's recorded figure.
Add it only if C-DD3 is meant to mirror `checks` one for one.

### Packet claims verified
- Deviations 1 to 6: each is accurate and acceptable as listed. For 2, only ADJUSTMENT exists today
  (`harvest-cold.customer_invoicing.json`, one record, one batch per tenant and source type, so names cannot collide).
  For 4, the cold and EV writer is a pure function tested on fixture rows, and it is wired in DD2b/DD4.4. That defers
  §7 DD2.5's "wired to `measured.json`", but no `measured.json` exists yet.
- Record IDs carry the month (`gen:<code>:<month>:<side>:<name>`), so four months of fuel-1 never collide as revisions.
- Statements (Lakeside, from my run): July revenue 9298.20 and fuel 4737.35, August 9271.35 and 4591.50, September
  9335.80 and 4491.65. `source_ref` is "Emulated management accounts, {Month YYYY}, final", and there is no October
  statement.
- C-DD4 with all tenants and an empty store runs without crashing (40 detail lines). Cold's `Formulas` evaluation
  resolves.
- The checker imports nothing from the simulator. Its evaluator is its own code and shares no table with `NODES`.

### Checks run (worktree, this head)
- `heavy-slot -- pytest contracts/tests/test_dd2_bool_type.py simulator/tests/world/test_dd2_nodes.py
  simulator/tests/world/test_dd2_checker_on_emulated_rows.py simulator/tests/world/test_3a3_exports.py
  backend/tests/test_dd2_check.py backend/tests/test_dd1_check.py -q` with `PYTHONPATH` set to the worktree packages:
  **74 passed**. The modules import from the worktree (checked `exports.__file__`).
- `ASSETOPS_GUARD_PYTHON=... pwsh tools/check-architecture.ps1`: **passed**. `pwsh tools/check-agent-workflow.ps1`:
  **passed**.
- Probes (scratch scripts, deleted): `judge_identities` on the real inputs (M1 crash); `build_exports` on the manifest
  (staged names, statements bytes, Kobo's notes in all four months, unwritten reasons).
- I cite the builder's same-head runs and did not rerun them: contracts 206, simulator world 170, backend 117, and the
  `--db` run with 118 passed. No full suite was rerun (§7). M1 needed no database.

### Not verified / residual risk
- `BOOK_QUERY` against a live store (L1).
- Deviation 3 (`EXPORT_PATHS_MIXED` when a staged JSON shares a source type with a CSV or profile file) is not met
  today. DD2b adds cold CSVs for `customer_invoicing`, so DD2b's review should check that staged ADJUSTMENT and the cold
  invoice CSV do not mix in one tenant's `commercial/`.
- `EMU_NODE` skips a recorded node that the record's leaves cannot reach (`node in nodes` guard). Today every October
  node is reachable (tested), so this has no effect now.

## Verification (fix round D-DD.58)

**Verdict: ACCEPT.** Head 1fa88f563; diff read `e55a79ff9..HEAD` (checker, packet, two test files; the main merge ignored).
- M1 closed: `judge_identities` no longer reads `energy_cost`; cold `crate_days` absent gives `<tenant>/<site> <month>: crate_days not recorded` and `continue`; the real-inputs test with `tenants=None` runs both judges without exception.
- EV clause matches D-DD.58: line = `round_half_even(quantity x band price, 0.01)`, price read from `M` `tenant.sites.<s>.tariff.prices` by `_EV_PRICE` (PEAK/OFFPEAK/NIGHT/FLAT/DEMAND); an absent price is a FAIL line; no tenant CHARGE row gives `pending: EV utility invoices are DD4.4's`. Tie rounding is tested both ways.
- L2 closed (`BOOK_MONTHS` deleted, test asserts it). L1 carried and stated in the packet (DD5's first C-DD2 run). L3 not adopted, per ruling.
- Parity: mini-grid code is untouched in the diff; the parity test checks line count and prefixes of the planted fixture, not full text. Acceptable (Info, no action).
- Checks I ran: the three dd_check files via `heavy-slot.sh --db -- run-host-tests.ps1`: 26 passed at this head; the same files at main `e55a79ff9` (throwaway worktree, removed): 19 passed. Delta 7, matching the packet. `tools/check-architecture.ps1` (ASSETOPS_GUARD_PYTHON set): passed.
- Not verified: `BOOK_QUERY` SQL (carried); the FLAT key `usd_per_kwh` is absent from `M`, a DD4.4 note already in the packet.
No remaining findings.
