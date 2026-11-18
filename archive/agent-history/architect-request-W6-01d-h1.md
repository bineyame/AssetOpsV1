# Architect request: W6-01d review H1 — classify two departures

You are the AssetOps Architect (Codex). Read H1 in `MSYS_NO_PATHCONV=1 git show task/W6-01d-request-history:.agent/W6-01d-review.md`, the C4 rulings in `.agent/W6-01-build-spec.md`, the departure rule in `.ai/ROLE_CONFIG.md`, `.agent/mock-departure-register.md`, and the v69 `wr-history` mock.

Two C4 departures have no category code or register row:
- (a) the two visible gap rows, moved to the end of the table;
- (b) the completion wording that replaces the mock's "Marked completed · witness test outstanding".

For each one, first decide whether it is avoidable. If the mock's position or wording can be kept honestly, mark it D3 and give the literal correction. Otherwise assign D1 or D4 with the reason. Add rows R41 and R42 to the register, add `MOCK DEVIATION (Dn)` labels to the C4 rulings, and give the literal one-line header comment for `frontend/src/work/WorkRequestHistory.tsx`.

Write only the register and the spec. Do not commit. End your output with one line per item, saying whether code must change.
