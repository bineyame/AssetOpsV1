# 4d review, round 1 (discovery, W5)

Reviewer: fresh Claude reviewer, not the author. 2026-11-20. Branch `task/4d-litre-split`, head `1319f72a7`
(base `b8b812f23`; main has since moved by docs only (3C2), and the branch merges cleanly). Worktree
`/opt/assetecon/AssetOpsV1-4d`, read only. Judged against spec rev 2, rulings D-4D.1 to D-4D.15, reviewer guide
rev 2, packet and mid-build Q1.

## Summary (round 1)

- **Verdict: ACCEPT.** One Low finding (F1, about how strong a test is). Fixing it on the branch is recommended but
  should not hold the merge. I found no honesty breach.
- Honesty hunt, all clean:
  - every litre leaf is MODELLED with origin `unknown`;
  - a missing generator reading gives "Not available yet" naming the record, never 0.000, for both D-4D.10
    conditions (whole month: V18; one day: V19);
  - INDETERMINATE and unclassified running go to necessary, never to candidate;
  - STALE, FAILED and PENDING days are NOT_ASSESSED;
  - a gap month has no figure;
  - 5b's diff is empty.
- I recomputed Kobo by hand. 212 running hours at 5 L/h give 1060 L. Candidate is 66 h, so 330. Necessary is
  1060 − 330 = 730 (indeterminate 10). Burned is 500 + 1180 − 500 = 1180, so unexplained is 120. At −1.25 per
  litre, the gaps 30, 330 and 120 give −37.50, −412.50 and −150.00, which sum to −600.00.
- I reran the unit tests, both guards, 4 plants and the 4d Postgres file. All results match the packet.
- Q1: I agree with the default. 5c formats money; 5b and D-4D.6 stay as they are (reasons below).

## Findings

### F1 (Low; test strength, not an acceptance gap): test 3's sum invariant cannot detect a misclassified litre

- **File:** `backend/tests/test_4d_litre_split.py:405-416`; `specs/4d-litre-split/reviewer-guide.md`, P1 row.
- **What.** `necessary_l` is computed as `T − C` (`rules.py:300`), so `necessary_l + candidate_l == q(T)` holds
  whatever litres are put into C. The invariant only proves that T comes from slots. It cannot catch a litre counted
  in the wrong class. My own plant of P1 confirmed this. It failed 15 tests, test 1 and test 6 among them, but none
  of the `test_3_invariants` cases. The guide's table says P1 fails "test 1, test 3".
- **Why it matters.** The guide claims two independent catches for the plant that matters most for honesty
  (ambiguous running counted as avoidable). It has one kind: the literal tests. Those catch P1 today. The general
  invariant, however, would not catch a future fixture in which INDETERMINATE litres happen to equal the hand-written
  literal.
- **Fix.** In test 3, also assert `candidate_l == _q(the test's own count of running slots inside CANDIDATE spans
  × 5/12)`. Alternatively, amend the guide's P1 row to "test 1, test 6, V-cases". The first fix costs about 3 lines
  and makes the invariant non-tautological.

### Not findings

- **The `test_3b3_structure_evaluate.py:86` edit (`PROVIDED_CAUSE`).** This is correct and necessary. Spec §3.1
  makes the three leaves PROVIDED and NOT_CONNECTED when read alone, which is the same pin as the `STATE_TABLE` at
  :76 that §0 does list. Without the edit, 3B3's test fails. The cause is an omission in spec §0's line list, not
  scope creep. The packet names the edit. I record it here for the Architect, not as a finding against the
  Implementer.
- P11 fails Postgres test 2 through the `match="read-only transaction"` mismatch (`NotNullViolation`), not through
  the expected exception. The `match` is what tells the two apart, so the plant is still caught.

## Q1 (mid-build): effects carry five places

My view: **5c formats every money figure to its currency's places at display; leave 5b and D-4D.6 unchanged**,
which is the packet's default.

- Quantising each VOLUME or TERM effect in 5b would break the additive identity whenever gap × scale has sub-cent
  parts. For example, 730.417 L × −1.25 = −913.02125. Children rounded one by one need not sum to their parent.
  Today the children sum exactly: −37.50000 − 412.50000 − 150.00000 = −600.00000, which equals the record-based
  −600.00 as a `Decimal`.
- Cutting D-4D.6 below millilitres would move the litre figures themselves, which is the wrong layer for a display
  concern.
- Risk to state in 5c's spec:
  - a screen that prints the `Decimal` raw shows `-600.00000`;
  - children rounded for display may visibly differ from their parent by a cent, so 5c should say the rows are
    rounded rather than force them to add.

The Architect rules.

## Checks I ran (same head, `1319f72a7`)

- **Module paths.** PYTHONPATH was the worktree's `backend`, `contracts`, `simulator`, `host/tests`, `tools` and
  `backend/tests`. `rules.py` and `sources.py` resolve to `/opt/assetecon/AssetOpsV1-4d/backend/...`.
- **4d tests.** `heavy-slot.sh -- pytest backend/tests/test_4d_litre_split.py -q` gave 65 passed. With 3B3, 4b and
  5b added: 211 passed, 1 skipped.
- **Guards.** `check-architecture.ps1` passed (with `ASSETOPS_GUARD_PYTHON`). `check-agent-workflow.ps1` passed.
- **Postgres.** `/opt/assetecon/AssetOpsV1/tools/heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1 --
  backend/tests/test_4d_litre_split_postgres.py` gave 4 passed in 9.4 s, on the default `assetops_test` database.
- **Plants**, in the scratch copy `scratchpad/rev4d-r1-plants-2585101`, one at a time, each restored after its run:

| Plant | What it changes | Result |
|---|---|---|
| P1 | INDETERMINATE added to candidate | 15 failed, including test 1, test 6 and V24. Test 3 did not fail (F1). |
| P13 | rule 3 also requires every day to be NO_READINGS | V18 failed (the 0.000 case) |
| P18 | `day_state` ignores `status` | test 10's STALE_PROJECTION, FAILED and PENDING rows failed |
| Own plant | rule 5 ignores UNAVAILABLE days | V8[UNAVAILABLE] failed |

- **Process note.** The four plant pytest runs (about 6 s each) ran outside `heavy-slot.sh` by my error. The slot
  was taken only for a no-op. No database or server was touched.
- **Builder's runs cited, not rerun:**
  - 65 unit tests;
  - 369 passed in the `--db` regression. Its 3 failures were import errors from a missing PYTHONPATH. With the path
    fixed, the K3 files gave 28 passed;
  - check-all fast, 40 guards;
  - plants V1 to V26 and P1 to P20.

  The packet does not state the revision of the regression run. Its code commits end at `c17257a79`, and
  `1319f72a7` changes docs only, so the code is the same.

## Code read (discovery)

- **Rule order.** `rules.py` follows spec §2.3 in `NOTES` order. Rule 3 reads `held(lo, hi)` alone. Rule 4 uses
  `held` per UTC day. Rule 5 runs from `lo − 1 day`. Rules 12 to 14 come after 1 to 10. The closing dip's window is
  half-open. Rule 13 checks `valid` over the window first, then re-runs rules 4 to 10 over the window's parts
  outside the month.
- **Rounding.** All arithmetic is in `Fraction` and `q` is applied once per leaf.
- **Inputs.**
  - `inputs.py` uses K3's curve choice: `sfc_for` and `no_load_for` take the revision in force over the whole month,
    and `valid` is their intersection.
  - `held` counts readings in `(a, b]` with `bisect`.
  - `use` is A2's slot rule with ±30 min of readings. Slots are judged locally, so piece-wise sums are additive.
- **Adapter.** `dispatch_spans` reads spans only for a CURRENT selection and skips the WINDOW revision (`scope`
  comes from `_run_detail`'s `l.scope`). It sets READ ONLY inside the `_snapshot` REPEATABLE READ.
- **Composition.** A failure in the fourth builder disposes the first three.
- **W6 sweep.** No other live test pins the leaves HELD_NOT_CALCULATED. `test_5a_targets` and
  `test_3b3_structure_read_postgres:98` stay valid: the litre leaves stay missing there.

## Could not verify

- The full `select-tests` Docker run (384 files); the coordinator schedules it.
- The builder's other 16 plants and the 369-test regression, which I did not rerun.
- `read_at` on readings and curve histories in a single transaction: P3 accepts this as not one transaction, and no
  test covers it.

## Residual risk the packet does not name

- **Long interval readings.** `_Readings.use` keeps a reading only when its `interval_end` or `source_time` lies
  within ±30 min of the piece. A malformed interval reading longer than 30 min that crosses a piece edge can
  therefore be dropped from a piece-wise read. A single whole-range read would have flagged that slot unknown, so
  one slot could be valued where the whole-month rule would say incomplete. K3 bounds its reads the same way. This
  needs malformed EMS data and is low risk.
- **A delivery at the opening dip's instant.** It is counted (`t_o <= occurred_at`), whatever their real order on
  the day. This follows the spec, but it is ambiguous with operator data.
- **The memo.** It lives as long as the structure-read service, keyed by `known_at`. A corrected dip at an
  already-read `known_at` is served from the memo until the service restarts (in line with R13's "rebuild after
  such a change").
