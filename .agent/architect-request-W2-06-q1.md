# Architect request: W2-06 q1 (R1–R10) and closure of commits 2–5

You are the AssetOps Architect. Read:
- the `.ai/ROLE_CONFIG.md` sections "Mockup drives the design; implementers never decide" and the implementer dry-read;
- `.agent/W2-06-build-spec.md` (including the Pre-build closure);
- `.agent/W2-technical-design-ev.md`;
- the W2-05b build spec "Run 6 rulings (q6), manifest table", which is binding for the manifest values;
- the W2-03 cold assessment code, which is the analogue.

The code is on `task/W2-06-ev-assessment` at head `f9eb4db5`. Read these from that branch with `git show task/W2-06-ev-assessment:<path>`:
- `.agent/W2-06-pending-rulings.md`
- `.agent/W2-06-phase-handoff.md`
- `backend/migrations/versions/0025_*.py`

Commit 1 (migration 0025) is built. Commit 2 is blocked.

1. Resolve the R1 conflict. The contradictory W2-05b manifest asserts null `unknown_meter_seconds` and `supported_kwh`, but the W2-06 spec says integer ≥0 and stores the SUPPORT sum. Decide which one governs, and give the exact 0025 column nullability and CHECK change, if there is one. State the exact rule for when each value is null and when it is 0.
2. Answer R2–R9 exactly. Give literal reason codes and their order, literal basis values, numeric bounds, the overlap resolution rule, the per-interval error-bound formula, and the session-to-record link set.
3. Ratify R10 or correct it.
4. Next, do a line-level implementer dry-read of spec commits 3, 4 and 5 against the actual W2-03 cold analogue code. Commit 3 is the transactional writer and recompute, commit 4 the selected reads and refusals, and commit 5 the two UI routes and their captures. Pre-answer every question a mid-level implementer would ask:
   - writer transaction boundaries and the idempotency key;
   - recompute triggers and revision numbering;
   - Finding identity and dedupe;
   - response JSON shapes and every refusal code and status;
   - per-panel height budgets against the measured v69 EV mock heights, with column widths and wrapping;
   - chip tones (apply the cold Run 9 M5 pattern with EV values);
   - null and link copy;
   - the copy dry-read of every visible string and its source field.

   Aim: no further question rounds for W2-06.

Append everything to `.agent/W2-06-build-spec.md` as "Run 1 rulings (q1) and commits 2–5 closure". Write nothing else. Do not commit.
