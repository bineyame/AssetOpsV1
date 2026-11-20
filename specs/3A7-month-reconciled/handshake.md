# 3A7 handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

## Reviewer questions

Fresh Claude reviewer, 2026-11-20, on `main` fb6d248d3 (spec rev 1, `rulings.md`, `reviewer-guide.md`, owner RC8 at
1 in 100, RC5). Severity: **High** blocks coding; Medium needs a ruling; Low is the Architect's call. **(done)** = the
answer changes what counts as done.

### High

- **R1 (done) §2.2 rule 2, §2.3 gate: a vacuous match opens the gate for the whole tenant.** `NONE_RECORDED_ZERO_STATED`
  is `MATCHED`, so a statement of `0.00` / `0.00` for a Site with no records at all (a newly onboarded Site), or of
  revenue plus `0.00` fuel for a Site with no generator, is a matched statement, and every Site-month of the tenant
  then reads reconciled. Neither the billing path nor the fuel path has been compared with anything; that is not
  §7.2's "one closed month reconciled ... on revenue and fuel or energy cost". Expected: only a statement whose
  headings each matched against used lines opens the gate (a zero-stated heading still matches for its own month);
  a test on a fresh world: S3 alone (MTO-001, revenue 250.00, fuel 0.00) leaves KOBO-001 `2026-10` at `NONE_MATCHED`.
- **R2 (done) D-3A7.1, D-3A7.6: the label may describe a different number from the one shown.** The standing compares
  the live figure (now); `5c` shows money beside 3B7a's snapshot, read at the snapshot's `known_at`. After a late
  record (T2's case) or a correction, the screen shows the snapshot figure while the label speaks of the live one, in
  either direction (a figure that does not match can read Recorded). R7 compares live with live only. Expected: a
  ruling that `standing` takes `known_at` (default now) and `5c` passes the displayed figure's, with a test where the
  two differ; or that `5c` shows live money whenever it shows the standing.
- **R3 (done) §6.2 T5, T6, R5: statement times are undefined, so T6 is nondeterministic.** S3 and S4 are both
  `(MTO-001, 2026-10)` and have no `recorded_at`; with the fixed read clock they tie, R5 breaks the tie by `id` text,
  and `uuid4` makes the current statement random: T6's `THIS_MONTH_NOT_COMPARABLE` holds only half the time. Expected:
  every statement's `recorded_at` written in §6.2 (S3, S4 at least, e.g. 2026-11-13 and 2026-11-14), and how the
  test clock moves (T1 records at 2026-11-05 and must be read before C, loaded at 2026-11-10).

### Medium

- **R4 (done) §2.1, §2.7: the share and display rounding cannot run in the exact context.** §2.1 puts all arithmetic
  under `Context(prec=200, traps=[Inexact, Rounded, InvalidOperation])`; `7.50 / 505.00` raises `Inexact` there, and
  so does `quantize` for display of a figure like `5.055`. Name the context for the share and the display quantise
  (e.g. `prec=34`, `ROUND_HALF_EVEN`) and keep the comparison exact.
- **R5 (done) V9, R3, §2.7: V9 cannot fail, and display rounding can contradict the verdict.** Every boundary figure
  has two decimals and `0.01 × 505.00` is exact to the cent, so quantising before comparing changes nothing. Add
  accounts `501.50`, recorded `506.52`: allowed `5.015`, difference `5.02`, `NOT_MATCHED`; quantising the allowed
  amount (`5.02`) would match. That case also shows the words problem: "5.02 more (1.00%), beyond the 5.02 allowed
  (1%)" reads as within. Expected: the allowed amount shown exactly (`5.015`) or rounded down, the share rounded up
  (or to more digits), so a sentence never contradicts its state; the literal in R3.
- **R6 (done) §2.3, D-3A7.7: the standing's text does not say what failed.** `THIS_MONTH_NOT_MATCHED` reads "Not yet
  reconciled: October 2026 (KOBO-001) does not match the management accounts within 1%."; the heading sentences live
  only in `this_month.headings[].text`. The owner asked that the product say exactly what did not match. Expected:
  `standing.text` appends the failing headings' sentences, or the spec states that `5c` must show them (and `5c`'s
  spec cites it).
- **R7 §2.4, D-3A7.4: the owner gate checks only that a file exists.** Any `owner/owner-*.md` passes (the RC file
  itself would), so the control does not show that the owner chose this tolerance for this tenant, and the row has no
  `set_by`. Expected: the cited file must contain the tenant slug and the tolerance as written, and the row records
  who ran the command; also say what happens where the deployment has no `owner/` folder.
- **R8 §2.1 scope: "the same figures as the screen" holds for mini-grid Sites only.** The organisation scope takes
  every Site in `site_zones`; 4b's `stated` refuses non-mini-grid Sites (`STATED_STATE`), so an organisation total
  can include money no deep-dive figure shows. Restrict the scope to mini-grid Sites (RC5) or state why every Site is
  right (the accounts cover them all).
- **R9 §2.6, R8: read counts.** An organisation and a Site statement both cover MTO-001 `2026-10`, so "`site_month`
  once per Site-month checked" needs memoisation within one standing read; and `statements()` checks every current
  statement live on each standing, i.e. statements × Sites month reads per figure on a `5c` page. Say whether the
  gate stops at the first match and whether the memo spans one standing or one request.

### Low

- **R10 §2.7:** `recon_amount` renders "Write the {heading}" with `fuel_cost`, a key; use "fuel cost" / "revenue".
- **R11 §6.1:** a statement carries `recorded_by` as a UUID only; "every statement names the finance lead" needs the
  person's name in the shape (or `5c` resolves it; say which).
- **R12 §2.7:** `{gap}` is "the same" only when the difference is exactly zero; `0.004` shows "0.00 more".
- **R13 §7:** say where `MonthsMemoryStore` is extended (a subclass in the 3A7 test file):
  `test_3a4_commercial_months.py` is not in done 9's list and 3B7a's tests import its `new_world`.
- **R14 §4:** in `tolerance ~ ... AND tolerance::numeric > 0`, Postgres may evaluate the cast when the pattern fails,
  raising a cast error instead of a check violation; Q1 tests `0.06` only.

## Implementer questions

See "Implementer pre-flight" (P1 to P5).

## Implementer pre-flight

Pre-flight of `spec.md` against `main` fb6d248d3 (3A6 not yet built, so its store, model and words are taken as
specified). Read-only; no database run.

- **P1 High (done) §0, §4: migration order.** `0068` revises `0067_source_profile` (3A6), which revises
  `0066_structure_snapshot` (3B7a, only on `task/3B7a-snapshot` 1f7e3b743, not merged). 3A7 can run no Postgres test
  until both are on its base; the ruling on 3A6's P1 must give 3A7's numbering too (`0067` revising 3A6's head if
  3B7a has not merged).
- **P2 Medium (done) §3, done 9:** `test_3c1a_person_work.py:479` asserts `COMMAND_ROLES == SPEC_ROLES`; adding
  `commercial.accounts_statement` fails it unless `SPEC_ROLES` gains the key, a file outside done 9's list.
- **P3 Medium (done) §5:** "the tenant from `--tenant` (`tenant_id` by slug through the accounts service)":
  `AccountService` has no slug lookup (only `AccountStore.tenant_by_slug`, `accounts/store.py:37`). Same question as
  3A6's P3; one answer for both, and `show` needs it (no `--as`).
- **P4 Low:** `reconciliation.py` imports `structure.money` (`COST_STATUSES`, a tuple at `money.py:36`) and
  `structure.evaluate` (`ORIGIN_ORDER`, line 40). No layering rule forbids it and there is no cycle
  (`structure.money` imports `commercial.months` only), but `build_commercial_reconciliation` puts the structure
  package in `commercial.composition`'s import closure, which 3B7a's code digest covers (stale snapshots after the
  merge, as 3A6's P9). 4b's `_cost` is private, so the reimplementation is right; R7 is the cross-check.
- **P5 Recomputed by hand (no question):** 3A4's fixture gives revenue 505.50 then 495.50 and fuel 762.50 then
  775.00; statement K: 5.50 more (1.10%) beyond 5.00, 17.50 less (2.24%) beyond 7.80, then 4.50 and 5.00 less within
  5.00 and 7.80. §6.2: organisation revenue 750.00, fuel 500.00 then 512.50; T1 within 7.55 and 5.05; T2 7.50 more,
  7.50 / 505.00 = 1.485% → 1.49%; T3 within 10.10; T4 2.50 within 5.10; T5 "the same" within 2.50; the boundary
  510.05 / 510.06 / 499.95 / 499.94 holds. Cited code exists: `CommercialMonths.site_month`, `MonthAmounts.closed`
  (`cutoff >= hi`, so October is closed at the read clock and November open: T9 holds), `MonthLine.dims`,
  `.source_systems`, `.provenance`, `site_zones`, `site_ids`, `build_commercial_reads` (`composition.py:128`),
  `has_control_character`, `COMMAND_ROLES`, `roles_of`; `site (tenant_id, id)` is unique (`0001`), so the statement's
  composite foreign key is valid. The months clock is private (`_clock`), as §2.6 anticipates.
