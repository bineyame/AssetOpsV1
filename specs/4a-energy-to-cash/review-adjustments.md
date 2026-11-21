# Review: adjustments blank when never sent (D-4A.8 amended, D-DS4.25)

Branch `fix/4a-adjustments-blank`, head b603c5383, against main eb78c5684. Fresh reviewer, read only.

## Verdict: ACCEPT (no High or Medium; two Low notes)

Checks run (PYTHONPATH = worktree backend, contracts, simulator, tools, host):
- `test_4a_energy_to_cash.py`: 105 passed.
- `test_4a_energy_to_cash_postgres.py` via `heavy-slot.sh --db` on `assetops_test`: 4 passed.
- `test_3b3`, `test_4b`, `test_5b`, `test_5a`: 179 passed, 1 skipped.
- Plants, each reverted (git clean after): (1) gate returns 0 for never-sent: fails V28 and step adjustments_kwh-1;
  (2) gate on CHARGE again: fails V17, V28 and step adjustments_kwh-1. Both fail as the packet says.
- Own plant, evaluated structure on the 4a Postgres world (scratch test, deleted): KISIWA-001 (has CHARGE, never sent
  ADJUSTMENT) reads adjustments_kwh value None, NOT_CONNECTED, note `NEEDS:ADJUSTMENT`; its billed 7400 and revenue
  4070.00 are unchanged and not turned into 0. Kobo 45 and Mto 40 stay stated; Kobo billed 8645 and Mto billed 5400,
  unmapped 140, revenue 2160.00 unchanged. So the blank holds on the evaluated structure, not only the pure layer.

## Points you asked about
- Never-sent blank on the evaluated structure: confirmed (above). Ever-sent gives 0: V29, closed month with charges and
  no adjustment line.
- "Ever sent" judgement: `held` is the kinds of `latest_revisions(tenant, site_id=site, known_at)`: per Site (the
  SQL filters `latest.site_id = :site`, so tenant-level NULL-site rows and other Sites' records do not count), any
  month, at the cutoff. That is the money.py step-1 rule and honest: another Site's adjustments (including Mto's on
  meter M-0099) do not unblank Kisiwa.
- No node turns the blank into 0: `billed()`, `unmapped()` and `tariff()` read charges, reads and assignments, never
  the adjustments leaf; V28 asserts billed 5400 and unmapped 140 beside the blank.
- `NEEDS:ADJUSTMENT` is a code in `NOTES` and the leaf's note, not served text.

## Findings
- Low 1 (test gap, not blocking): no Postgres test pins the evaluated-level blank for a Site with CHARGE and no
  ADJUSTMENT (I only saw it in a scratch run). The pure-layer V28 and step test cover the rule; a PG assertion on
  KISIWA-001 would pin the seam. Preference.
- Low 2 (residual, as ruled): the gate is the ADJUSTMENT kind, so a Site that sent only money-only credit notes reads
  0 kWh stated, not blank. D-4A.8 says credit notes are not kWh, but D-DS4.25 gates on the kind; consistent with the
  ruling.
- Note: `C4_KNOWN_FINDINGS` entries for D-DS4.25 are left for the DS4 merge, as the packet says; I did not check DS4.
