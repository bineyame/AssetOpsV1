# W2-03 re-review (fix round, 2ea7f1fb)

Verdict: ACCEPT. No High or Medium findings.

Checks run (serial, private DB `assetops_w203rr_test`, created then dropped):
- w203 replay + rules: 22 passed, 0 skipped (205 s).
- Mutation: `attested = True or any(...)` in postgres_assessment_store.py makes both
  `test_unattested_probe_source_excluded_through_intake` variants fail; reverted (git checkout, tree clean).
- `coldRoutes.test.tsx`: 26 passed. `npx.cmd tsc --noEmit`: exit 0. (Full suite 2182 / check-all 10/10 not rerun; cited from packet.)

1. M1 fixed: `coldbackup-stocked` 1440 shows "Chamber temperature after the compressor record" for the probe row;
   "after recovery" is only emitted when a compressor running record exists, asserted both ways. The state is said once; no raw IDs seen.
2. M2 fixed: the intake-driven test drives real gateway rows through `in_force`/`attested` and asserts EXCLUDED/CLOCK_UNATTESTED,
   no SUPPORT, and known_points equal to the attested count. Unbound-role deviation is acceptable: S2 refuses with
   OUTSIDE_BINDING_PERIOD at acceptance, so the state cannot exist in accepted rows; the pure-rule test plus defence-in-depth remain.
3. q3 applied: guard `expectedTabs` extended by exactly Cooling and Recommendation, with two failing-fixture cases;
   UI renders them through `UnavailableTab`. The vocabulary exemption (`MANDATED`) is now the single ruled provenance sentence
   verbatim; the old four-word allowance is gone. Title, column and source wording match the ruling.
4. Lows L3-L7 present in the diff and asserted (L3 separator, L4 chip class, L5 late-reading assertions, L6 low-peak test, L7 docstring).
5. No weakened assertions found; changes only tighten.

Residual (Low, non-blocking): the layout height table was not re-measured after the extra tab-row entry; captures were viewed and look sound at 1440.
