# Architect request: W6-01e builder items KD1–KD5

You are the AssetOps Architect (Codex). W6-01e E1/E2 is built on `task/W6-01e-operational-records` (head `173cfc73`). Read `MSYS_NO_PATHCONV=1 git show task/W6-01e-operational-records:.agent/W6-01e-review-packet.md` (Known Deviations KD1–KD5), the E1/E2 cards and pre-flight rulings in `.agent/W6-01-build-spec.md`, the departure and mock rules in `.ai/ROLE_CONFIG.md`, `.agent/mock-departure-register.md`, and the v69 `oprecords` mock.

For each item, confirm it or give the literal replacement:
1. **KD1:** `select_operational` takes an extra keyword-only `cutoff` beyond the ruled signature.
2. **KD2:** the "Record a manual reading" panel is 298/486 px against a 180/230 cap. The mock's own form is 289/443. Reset the cap from the mock.
3. **KD3:** two strings the builder chose: `Until {date}`, and `Reading: {quantity} {unit}`. Check them against the mock.
4. **KD4:** state and case checks run before the kind filter, so a bad record fails filtered reads too.
5. **KD5:** update register rows R12, R29–R31 and R34 to their actual status after E2.

Append "W6-01e build rulings (KD1–KD5)" to `.agent/W6-01-build-spec.md` and update the register. Write nothing else. Do not commit. End your output with one line per item, saying whether code must change.
