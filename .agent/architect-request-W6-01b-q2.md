# Architect request: W6-01b build follow-ups

You are the AssetOps Architect (Codex). W6-01b B1–B3 is built on `task/W6-01b-maintenance` (head `43a9142c`). Read its handoff with `MSYS_NO_PATHCONV=1 git show task/W6-01b-maintenance:.agent/W6-01b-phase-handoff.md`, the Run entries, and the B1–B3 cards plus "W6-01b pre-flight rulings" in `.agent/W6-01-build-spec.md`. Apply the mock-fidelity rules in `.ai/ROLE_CONFIG.md`.

1. **Blocked: the `linked` fixture.** The ruled 21-day shift moves the setup to 09-12 and the F01 readings to 09-15, both before the KOBO-001 Foundation period, which starts 2026-09-29 (`backend/tests/fixtures/s1/kobo-001.yaml:17`). The builder's options are: shift only the `decided` instants, override the Foundation `valid_from`, or defer. Rule one with literals: the producer steps, clocks, the test (currently a strict xfail) and the `maintenance-linked` capture. Check the result against W4's linked test and the read-time rule.
2. **Builder choices to confirm or replace with literals:**
   - B1 fixtures: the seventh request is at KOBO-001, the stress plan has no due date, and the builder named the linked cases.
   - B3: the Preventive breadcrumb links back to Corrective, and dates read `1 Nov 2026`. Check both against the mock.
3. **Spec mismatch.** The ruled stress text stores 4000 and 500 characters, not the 3999 and 499 the spec states. Fix whichever is wrong.

Append "W6-01b build rulings (Q2)" to `.agent/W6-01-build-spec.md`. Write nothing else. Do not commit. End your output with one line per item, and say whether any code must change.
