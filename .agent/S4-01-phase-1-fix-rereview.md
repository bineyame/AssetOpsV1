# S4-01 phase 1 fix round - re-review

Reviewer: a fresh Claude reviewer (independent; did not author the slice or the fix round). 2026-10-12.
Target: branch `task/S4-01-finding-identity`, fix diff `9609dd8..d9c1b5f` (`7781821`, `6bfd145`, `43d3268`,
`db28578`, `71dd0b6`, `d9c1b5f`). Against: `.agent/S4-01-phase-1-review.md` (B1-B4, C3, C7) and
`.agent/architect-S4-01-answers-1.md` / `D-2026-10-12-s4-finding-phase-1-clarifications` (Q2 bridge coverage, Q4
window revisions in the basis, Q5 `BASIS_REFRESHED`, Q6 F01 through the ordinary gateway).

## Verdict

**Accept.** B1-B4, C3 and C7 are closed, and the four Architect corrections are implemented and tested. No blocking
finding. The carries below are documentation and fixture hygiene for phase 2/3, plus the Architect's answers on
Q10-Q15. None of the Q10-Q15 defaults is unsafe. The phase-1 gate can close; the S4-01 owner checkpoint still stands.

## Closure of earlier findings (verified, not taken from the packet)

| Item | Status | How verified |
|---|---|---|
| B1 split ownership | Closed | `finding_episode.py:479-491`: `home` reserves each episode for the cluster that holds its anchor, and other clusters skip it. A pure test covers the review's reproduction. A mutation dropping the `home` guard fails 2 tests (split, mixed split+merge). An extra 3-cluster probe kept the anchors correctly. |
| B2 interleaved passes | Closed | `postgres_finding_store.py:90-95`: the fence counts the Site's append-only `finding_revision` rows. `FindingMatcher.match` reads the fence before the windows and episodes (`finding_service.py:41-46`), so a pass planned before another pass commits sees a moved fence. `test_a_pass_planned_before_another_pass_committed_opens_no_duplicate` passed on my isolated DB. |
| B3 / Q3 recurrence | Closed | `_recurrence` (`:392-405`) links only when the gap is fully assessed, the prior run's OFF-after is observed and not after the new start, and the new run's OFF-before is observed. Four pure tests cover this. A mutation removing the coverage check fails the unassessed-day test. The run artifact now shows only same-day links (F03, F06). |
| B4 pure tests | Closed | `backend/tests/test_s4_finding_episode.py`: 16 tests, all DB-free, covering every scenario the review asked for. |
| Q2 bridge coverage | Closed | `_bridges` needs every instant of the gap covered by an observed segment or an observed, correctly ordered stop (`_fully_covered`, `_stops`). Mutating it to `return True` fails the empty-span and out-of-order-OFF tests. A probe gave: observed Necessary gap bridges (1 Finding); unobserved Necessary gap does not (2 Findings). |
| Q4 window basis | Closed | `_write` puts the selected window revision IDs and window input digests in `basis` and keeps `support` separate. A probe on a closed episode: only the window revision changes -> `BASIS_REFRESHED` with `NO_LONGER_SUPPORTED`; same window -> no write. The early return that used to skip NLS->NLS is gone, so a provenance change on a closed Finding is recorded. |
| Q5 `BASIS_REFRESHED` | Closed | Added to the 0009 CHECK and the `support_sha256` column. It is used on both the owner path and the unsupported path. The Postgres collateral check now asserts an equal `support_sha256` and a different `basis_sha256`. Mutation: test fails. |
| C3 reopen | Closed (Q10 residue to Architect) | Candidate over NLS -> `REOPENED`. Mutation: test fails. |
| C7 moved fence | Closed | The test applies a real planned `OPENED` write and asserts no Finding and no revision. |
| Q6 F01 gateway | Closed, with carry R1 | `gateway_case`: Lab run -> durable registered gateway -> TLS -> central acceptance. The producer asserts every accepted reading is under `s4-gateway-epoch-1` and the registered gateway ID, then that an `OPENED SUPPORTED` Finding exists on 10-02. |

Migration 0009 was edited in place. I read `alembic_version` (read-only) in every local database: none is at 0009
(`assetops`, `assetops_test`, `assetops_s2demo` are at 0006; `s3cases` and `s3walk` at 0008), so nothing applied
is invalidated.

## The 10-02 gateway-day deviation (dispatch question)

Acceptable for phase 1. It is not a defect in the product, but it is a weakness in the fixture design (R1).

- The Q6 ruling explicitly allows "F01 can run its own registered Lab/gateway case". The 10-02 case satisfies the
  ruling's substance: an ordinary gateway-sealed Batch V2 is centrally accepted and opens a SUPPORTED Finding through
  the same matcher.
- A 0-minute minimum runtime ("no minimum") is a coherent site property, and the central analytic accepts it. The
  refusal is the Lab's step-alignment constraint (`LIFECYCLE_TIMING_NOT_ALIGNED`), not evidence that the fixture
  control is wrong.
- The cost: the gateway day runs under the template runtime, before the 10-03 setup controls. So the gateway-sealed
  Finding and the fixture F01-F08 Findings do not share one control lineage, and the gateway case proves the path,
  not F01's specific Candidate. The packet says this honestly.

## Carry (not blocking)

- **R1 Fixture controls the Lab cannot run (Q15).** I recommend the Q15 alternative before the phase-3 owner
  walkthrough: a positive multiple of 5 minutes for the setup control. The gateway case and the fixture cases would
  then share one control lineage, and later fixture days could be reproduced through the gateway. If the default
  stays, phase 2/3 must label the 10-02 Finding as "registered gateway path, template runtime" and never present it
  as F01's own Candidate.
- **R2 Gateway case does not assert that the Finding's cited evidence is all gateway-sealed.**
  `tools/s4_finding_cases.py:418-428` checks the accepted readings of the delivered batches and that a Finding
  opened on 10-02. It does not check that the opened revision's cited evidence IDs are a subset of those batches'
  evidence. This holds today by construction (no fixture delivery on 10-01/10-02), so it is low severity. A
  one-query subset assertion would make the Q6 proof self-checking.
- **R3 Stale residual-risk lines in the packet.** `.agent/S4-01-phase-1-review-packet.md:86-88` still says
  recurrence links chain across case days ("Correct under Q3"). Line 91 still says "No pure unit tests for
  `finding_episode.plan`". The Fix round 1 section and `.ai/CODE_STATE.md` contradict both. Update or strike them
  so phase 2 does not inherit them.
- **C2, C5 still open as carried.** C2: idempotency keyed across all history, A->B->A reselection. C5: the fixture
  minimum-runtime control is published with `"source": "TEMPLATE"` (`tools/s4_finding_cases.py:86`). Unchanged by
  this round; it was never in scope.
- **C6 is now Q12.** Earliest anchor wins even when that anchor is outside every cluster. This matches the
  decision's literal rule; the Architect decides.

## Q10-Q15 defaults

None is unsafe as a fail-closed phase-1 default.

- **Q10:** reasonable. One condition for phase 3: the `UNCONFIRMED` title ("Generator support candidate
  unconfirmed...") must not read as an active new issue when it supersedes a `NO_LONGER_SUPPORTED` conclusion.
  History should show the earlier closure.
- **Q11:** acceptable within the 20-minute bound and dispatch-3.1 spacing.
- **Q12:** matches the decision text.
- **Q13:** matches the Q3 ruling exactly.
- **Q14:** right, and phase 2/3 must group the provenance-only revisions.
- **Q15:** see R1.

## Checks run by this reviewer

- Pure matcher tests: `.venv\Scripts\python.exe -m pytest backend/tests/test_s4_finding_episode.py -q` gave
  `16 passed in 0.14s`.
- Targeted mutations of `finding_episode.py`, in scratchpad copies only (the repo was not modified):
  - B1 `home` guard removed: 2 failed.
  - B3 coverage check removed: 1 failed.
  - Q2 `_fully_covered` replaced by `True`: 2 failed.
  - `REOPENED` removed: 1 failed.
  - `BASIS_REFRESHED` removed: 1 failed.
  - Unmutated copy: 16 passed.
  - I did not rerun the Implementer's pre-fix shim (8 failing); the per-fix mutations stand in for it.
- S4 Postgres tests: `backend/tests/test_s4_finding_store_postgres.py` on an isolated `assetops_s4rr_test` (created on
  the local Compose Postgres, then dropped) gave `6 passed, 3 warnings in 64.95s`, including the interleaving test
  and the real-write moved-fence test.
- `tools/check-architecture.ps1`: "Architecture check passed." `tools/check-agent-workflow.ps1`: "Agent workflow
  check passed."

Not verified by me:
- I did not rerun the producer (`tools/s4_finding_cases.py run`, which needs the Lab, the TLS server and the gateway
  pipe). Its run record (11 / 30, VERIFY PASSED) is the Implementer's.
- I did not rerun the full suites (backend Postgres 1858, host 667, gateway 164, simulator 265) or `check-all`.
- No frontend change, so `npm.cmd test`/`build`/`tsc` were not run and layout evidence does not apply.
- I did not reproduce the B2 mutation proof on the store adapter. The fence logic was checked by inspection and by
  the passing interleaving test.

## Residual risk not named by the packet

- The basis of a supported Finding takes its windows from those that own its interval revisions
  (`_support_write`). The unsupported path uses every window over the episode. A window that overlaps a
  cross-midnight episode but owns none of its intervals is therefore not in that Finding's basis. This looks
  harmless, because a changed interval would carry a new interval revision ID anyway. Phase 2's "currently selected
  window" read should use the same set the basis uses.
- `_recurrence` can link to a prior episode that is now `NO_LONGER_SUPPORTED` (only `MERGED` is excluded from
  `live`). This is consistent with the decision, which concerns an actual OFF break. Phase 3 wording should not
  imply the earlier issue was still active.
