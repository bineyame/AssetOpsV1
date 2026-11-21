# 4a mid-build questions

Questions raised during the build about something the spec did not fix (spec rev 2). Count: 2. **Q1 answered: D-4A.27 (confirmed). Q2 answered: D-4A.28 (confirmed; PG1(e) wording amended).**

## Q1 (2026-11-21) D-4A.22's producer-world dates precede the Kobo Foundation

- **Found.** With `IMPORT_AT` 2026-08-31T06:00Z and `INSTALL_AT` 2026-09-01T06:00Z, `producer.configure_at` refuses
  (`FOUNDATION_INTERVAL_INVALID`: "No currently recorded Foundation period of KOBO-001 contains
  2026-09-01T06:10:00+00:00"). The imported Kobo Foundation starts at `kobo-001.yaml`'s `valid_from`
  2026-09-29T11:57:49Z, whatever the import clock.
- **Default applied.** `IMPORT_AT` 2026-09-29T12:00Z, `INSTALL_AT` 2026-09-30T06:00Z. The roles-4 set starts at
  install + 27 min (2026-09-30T06:27Z), before October's first local midnight (2026-09-30T21:00Z), so it is in force
  over the whole month as D-4A.22 intends; the band is effective at install + 28 min, recorded 2026-10-04T01:00Z.
  Nothing else changes. Also needed and not named in D-4A.22: the gateway and sources are enabled after
  `configure_at` (`test_s2_evidence_ledger_postgres.enable`, as `demo_combined_kobo.py:424-426` does).
- **Pre-flight (d) result** on this world: one `clinic-meter` batch of 24 hourly `INTERVAL_MEAN` envelopes, sealed
  against the roles-4 revision after the band's Foundation change: status 200, 24 ACCEPTED. PG1b was written after
  this. Log: `/opt/assetecon/evidence/4a-energy-to-cash/preflight-d.log`.
- **Reverse.** If the Architect wants other dates, only the two constants in `test_4a_energy_to_cash_postgres.py` move.

## Q2 (2026-11-21) PG1(e)'s `unexplained_loss_kwh` note contradicts §2.4

- **Found.** Spec §6.2 PG1(e) (and D-4A.17) expect `unexplained_loss_kwh` absent with `LOSS_BAND_NOT_DECLARED` on the
  producer Site after days 1-3. §2.4's binding table orders unexplained's steps as 1. delivered absent (its cause and
  note), 2. technical absent, 3. metered absent. After days 1-3 delivered is absent `FEEDER_READINGS_GAP`, so the
  rules give unexplained `FEEDER_READINGS_GAP` (the read returns exactly that; value None, NOT_AVAILABLE).
- **Default applied.** The rules stand (§2.4 binds). PG1(e) asserts technical `LOSS_BAND_NOT_DECLARED` and unexplained
  `FEEDER_READINGS_GAP`, both value None and NOT_AVAILABLE, so "never 0" is still asserted through the real read.
  Unexplained's own band case stays covered by test 1 (Kobo, §5.2) and V20/V21.
- **Reverse.** If the Architect wants unexplained to name the band here, either PG1(e) moves after a full month
  delivered before the band (a world-order change), or the §2.4 order changes (a rules change). Not done.
