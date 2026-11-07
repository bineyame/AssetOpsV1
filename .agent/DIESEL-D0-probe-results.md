# DIESEL-D0: Kisiwa simulator trial, results

Ruling: `.agent/build-sheet-DIESEL-1.md` §2 (f755f085b). Owner decisions: `.agent/owner-diesel-site-2026-11-07.md`,
`.agent/owner-diesel-night-window-2026-11-07.md`.

## Expected outcome (recorded before the measured run, committed before the tool exists)

- Architect's pre-registered expectation (DIESEL-1 §2.9 S1, verbatim): "under cycle charging the saving comes only
  from diesel-charged energy still in the battery when the sun rises, so it depends on whether the overnight run
  reaches past dawn. A result below 20 % is plausible."
- Builder's hand estimate from the §2.2 values (no simulator run yet): with stop 90 % the generator runs about twice a
  night (about 20:00-22:00 at 38 kW, about 00:40-02:30 at 27 kW), about 115 kWh, about 41 L; the battery then drains to
  about 36-37 % by 08:00, so almost no diesel-charged energy is left when the sun takes over. With stop 60 % each run
  is shorter but the battery reaches the 35 % start setting more often (about four or five starts a night, one of
  them after 06:00), and the generator energy is about the same or higher. **Expected: NOT MET (S1), with a
  reduction near 0 % or negative.** Cold store: expected no power cut. Battery: expected never below 30 %.

The measured result is below; nothing in §2.2-§2.7 was changed after this was written.
