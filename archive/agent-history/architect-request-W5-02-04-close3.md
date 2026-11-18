# Architect request: withdraw M5/E5 and fix the K4a ordering

You are the AssetOps Architect (Codex). Read "Recheck 2" in `.agent/W5-02-04-readiness-review.md`.

1. **M5/E5 can be avoided.** The Site timezone exists: `site.timezone` is NOT NULL in migration 0001, the Site API returns it, and `SiteDetailReadModel.timezone` (`frontend/src/sites/siteReadModel.ts:49`) is already on the Work frames' `site` object. Cold fixtures use Africa/Addis_Ababa and EV fixtures Etc/UTC. Withdraw M5/E5, and restore the mock cell `6 Oct · from 19:11` formatted in `site.timezone`. Give the literal formatter (reuse any existing Site-time helper; cite it), the tests, and the cold producer window in UTC that shows 19:00–20:00 EAT. Apply the same rule wherever else W5-02 and W5-04 show Site times.
2. **Ordering.** K4a now waits for W6 E2, the last W6-01 unit, which puts W5-03a behind all of W6-01. Re-sequence to shorten the critical path, for example by landing the rail override independently or earlier. Give a feasible merge-order rule with the file ownership.

Update the cards and closure rows in `.agent/W5-02-build-spec.md` and `.agent/W5-04-build-spec.md`, and `.agent/W6-01-build-spec.md` only if needed. Do not commit. End your output with two lines saying where each item is closed.
