# Review: DD2b cold and EV decided books (DD2.3, DD2.4; `task/DD2b-cold-ev-books`, head 948515f0c)

## Round 1: discovery review (2026-11-22)

**Summary.**
- **Verdict: ACCEPT.** No High finding. No branch fix is required. The two Medium findings are faults in the spec and its rulings, not in this build. They go to the Architect (packet Q1, Q2), and each must be ruled before DD5 loads these files.
- M1: nothing in the code writes the cold or EV TARIFF_SCHEDULE that spec §3, §5.2 and §5.3 and D-DD.24 say "DS1b already writes". The packet's Q2 default leaves no owner.
- M2: Q1 is real. D-DD.24's split into an invoice file and a receipt file, plus the staged ADJUSTMENT, puts three systems on `customer_invoicing` at Thika, so `_refuse_switch` refuses at load.
- Low: four findings (L1-L4), none blocking.
- Reviewed in full: books.py, exports_cold.py, exports_ev.py, profile_csv.py, the 9 profiles and their samples, the 6 new test files, the CLI change. The ledger was checked against the manifest's incident batches.
- Checks run: simulator/tests/world 180 passed; architecture and workflow guards passed. The PostgreSQL run is the builder's (cited, not rerun).

Scope note: `main...HEAD` also contains DD2.2 (0db0c72de..012b08c37), which is already reviewed (`review-DD2.2.md`). This
review covers `7cf104918..HEAD`. `contracts/` is untouched in that range (D-DD.49 point 4 holds).

### Findings

**M1 (Medium; spec/ruling gap, not an acceptance gap of DD2b): no producer of cold and EV TARIFF_SCHEDULE.**
- Where: spec §3 rows "storage rate card" and "tariff schedules" ("records.py; staged"), §5.2 line "The rate card is
  DS1b's TARIFF_SCHEDULE (0.20 per crate-day from 2026-07-01), staged", §5.3 "Tariffs are DS1b's TARIFF_SCHEDULE per
  Site", and D-DD.24 ("written by `records.py` as today ... DS1b already writes them").
- What: `grep TARIFF_SCHEDULE simulator/assetops_simulator/world/*.py tools/world*.py` finds only `books.py:31`
  (`STAGED_KINDS`). DS1b writes no TARIFF_SCHEDULE for any tenant: cold DS1b kinds are EXPENSE, ADJUSTMENT and
  BUDGET_LINE, and EV's are EXPENSE and BUDGET_LINE. The staged set is therefore only `gen:COLD-THIKA:2026-10:actual:liability`.
  The D-DD.54 test (`test_dd2b_books.py:20`) passes for tariffs only because nothing produces one. The packet's Q2
  default says "DD2a's staging owns it", but DD2a stages DS1b's output and builds no new writer (spec §7 DD2.1), so
  nobody owns it.
- Why it matters: the cold invoices carry `tariff_code` `T-STORAGE` (`exports_cold.py:53`), and the EV utility-invoice
  sample carries `C-114`/`C-117`. At DD5 there is no rate card or tariff schedule to resolve them, and the EV bands of
  `M` `tenants.metro-bus.sites.*.tariff` never reach the store. The money figures still check (they are nodes), but
  the product's tariff lineage is empty.
- Fix (Architect): name the writer and the unit cost. One option is to extend DS1b `records.py` with cold and EV
  TARIFF_SCHEDULE records (check what that does to DS1b's goldens). The other is a small writer in DD2b or DD2a. Either
  way, `contract_ref` must equal `T-STORAGE` and the EV invoice tariff codes, with a parity test. Correct the spec's
  "already writes" wording.

**M2 (Medium; ruling-induced, packet Q1 confirmed): the three cold `customer_invoicing` systems at Thika collide at load.**
- Where: `backend/assetops_backend/commercial/uploads.py:260-266` (`_refuse_switch`, D-3A6.5: one source system per
  source type per Site); `commercial/profiles.py:217` (`PROFILE_SOURCE_SYSTEM_TAKEN`);
  `cold-storage-invoices-illustrative.profile.json:6-7` and `cold-storage-receipts-illustrative.profile.json:6-7`
  (both `customer_invoicing`, systems `cold-storage-invoices` / `cold-storage-receipts`); `records.py:62` (Thika
  liability ADJUSTMENT on `customer_invoicing` from the generator system).
- What: D-DD.24 itself split storage invoicing into two files, "because a profile writes one kind". Two profiles
  cannot share a system, so whichever cold invoicing upload comes second at a Site is refused `UPLOAD_SOURCE_SWITCHED`.
- Why it matters: DD5 cannot load the cold receipts (or the Thika adjustment) as built. Whatever DD5 decides may
  change this branch's receipts profile, sample and expected file.
- My view, and the default I would take: map receipts to `mobile_money_statement` (kinds RECEIPT, SETTLEMENT; this is
  mini-grid's precedent, since `collections-illustrative-1` is a separate source type from billing). The Thika
  ADJUSTMENT still needs its own answer. The cleaner general fix is a contract rule that treats profiles of one
  operator system as one system, but that is a product change. Have the Architect rule before DD5 starts, not inside
  DD5.

**L1 (Low): the hand-written samples for the DD4.4 profiles have no forcing test to become emulated slices.**
`books_support.py` `HAND_SAMPLES` (utility invoice, departures). Their values (e.g. Ruiru October PEAK 6076 kWh,
`C-117`) are typed in. When DD4.4 writes the real rows, nothing fails if these IDs stay hand-written and drift from the
emulator. Fix (DD4.4): add a test that `HAND_SAMPLES` is empty once `exports_measured` exists, or move the IDs to
`SAMPLES` in DD4.4's acceptance.

**L2 (Low): the ledger carries June opening-stock IN rows outside July to October, with no June invoice** (deviation 3,
`exports_cold.py:199-205`). The rows are honest (the crates were admitted in June). But any later check that reads the
ledger's months (C-DD2 to C-DD4 in DD2a and DD5) must treat June as opening stock, not as a missing month. Fix: name
this in the Architect's ruling on deviation 3, so DD2a's and DD5's checks can rely on it.

**L3 (Low): room capacity is met by the data, not by the construction.** `_fill` (`exports_cold.py:178-186`) places
batches on the least crowded day with no capacity term. Kirinyaga's peak is exactly 400 = `capacity_crates_per_room`.
`EMU_CAPACITY` fails loudly (`test_c8`), so nothing wrong can ship silently. But any change to the history leaves can
stop the emulator instead of moving a batch. Acceptable for pinned history; note it for DD4.1 (full room on peak days,
as the packet says).

**L4 (Low; preference): `test_dd2b_ev.py:86` passes the host's local tzinfo** (`datetime.now().astimezone().tzinfo`) to
`roster_rows`. It asserts only counts and dates, so it is harmless, but it depends on the host. `zone_currency(view)[0]`
would be deterministic.

### Packet questions and deviations (my view; the Architect is ruling separately)
- Q1: confirmed (M2). Rule before DD5. Default: receipts → `mobile_money_statement`, and the Thika ADJUSTMENT ruled
  separately.
- Q2: confirmed as a gap with no owner (M1). The "DD2a owns it" default does not hold.
- Q3: agree. Unify `NODES` at the DD2a merge. Merge-order risk: this branch also carries DD2.2's commits, which are on
  `task/DD2-books` and not on `main`. Merge DD2a first, or accept that DD2b brings in DD2.2.
- Dev 1 (row_digest for receipts and tickets): agree. `profiles_v1.py:258-259` refuses a constant version alongside a
  `status` writer. Correct the spec's "every profile constant '1'".
- Dev 2 (EV invoice `Line` / `Line type`): agree. `profiles_v1.py:205` requires one-to-one maps, so §5.6's many-to-one
  map cannot compile.
- Dev 3 (ledger rule): agree. §5.2's even spread cannot be exact (Thika 8432 is not divisible by 7). The builder's
  crate-day definition is consistent with the invoices (`crate_days_in`), and it is verified independently from the
  rows (`test_c2` counts from the ledger alone). Add L2 to the ruling.
- Dev 4 (named batch times): agree. These times are consistent with the manifest: B-1029 checked out 5 Oct 16:00;
  B-1031 present on 6 Oct with QA on 7 Oct; B-1034 present. The customer code is consistent with R5.
- Dev 5 (node lines wherever the plan holds the field): agree. D-DD.49 (b) is a general rule, and "(Ruiru)" describes
  the history months.
- Dev 6-8: agree.

### Checks I ran (worktree root, revision 948515f0c)
- `tools/heavy-slot.sh -- .venv/bin/python -m pytest simulator/tests/world/ -q` with `PYTHONPATH=simulator:contracts`
  (imports confirmed to resolve to the worktree): **180 passed in 13.89s**.
- `ASSETOPS_GUARD_PYTHON=... pwsh -NoProfile -File tools/check-architecture.ps1`: **Architecture check passed.**
- `pwsh -NoProfile -File tools/check-agent-workflow.ps1`: **Agent workflow check passed.**
- A probe (scratch, deleted) of DS1b's cold and EV records and unwritten rows: no duplicate unwritten keys. The c9 plant
  lists `crate_days` once (`NOT_IN_HISTORY`).

### Not verified by me
- The PostgreSQL run (`test_dd2b_profile_admission.py`, `test_dd2b_departures_postgres.py`, 13 passed). I cite the
  builder's run at 65f4fb270. The only commit after it, 948515f0c, changes only the packet, the state entry and the spec
  status. I read both test files; they assert what the packet claims.
- The plants P3-P9 (packet). The tests they target exist and assert the planted property.
- Layout evidence: not applicable (no screen).

### Residual risk the packet does not name
- If the c9-style plant happens in real data (a missing month of `crate_days`), the previous month's late batches still
  show crates in the room in a month with no invoice. This is honest (the crates were there), but a reader could take
  it as unbilled occupancy. It only matters if DD4 or history ever drops a cold month.
- The cold and EV full files have no byte golden, only sample slices (b3) and round trips. No test compares
  two runs' bytes: the CLI's second run in `test_3a3_exports.py` only checks the `DS1B_OUT not-empty` refusal.
  Determinism rests on the code using no clock or randomness (I found none; L4 is test-only). DD2a or DD5 could pin
  the cold and EV files' sha256 as 3A3 does for mini-grid.
