# S4-01 phase 1 fix round 1 - handoff (PARTIAL: stopped at the context budget)

Branch `task/S4-01-finding-identity`. Fix commits on top of `9609dd8`: `S4-01 phase 1 fix round: anchor-first split...`
(matcher, store, 0009, pure tests) and `S4-01 fix round: Postgres interleaving...` (Postgres test, spec, producer check).
Sources: `.agent/S4-01-phase-1-review.md` (B1-B4, C3, C7), `.agent/architect-S4-01-answers-1.md` +
`D-2026-10-12-s4-finding-phase-1-clarifications` (four corrections). Do not commit `.agent/coordinator-handoff.md`.

## Landed (committed)

- `analytics/finding_episode.py`
  - **B1**: ownership reserves each episode for the cluster containing its anchor (`home`), then each cluster takes
    its earliest-anchor (then UUID) eligible episode; absorbed episodes merge into their home cluster's owner.
  - **B3 / Q3**: `_recurrence` links only if `site.covered(prior.end, c.start)`, the prior run's `off_after` is
    observed (<= c.start) and the new run's `off_before` is observed (>= prior end); otherwise unlinked.
  - **Q2**: `_bridges` now also needs `_fully_covered` - every instant of the gap in an observed segment or an observed
    stop (`_stops`: last_on <= off_after <= next off_before <= next first_on). `IntervalBasis.last_on` added.
  - **Q4**: basis = support digest + interval revision IDs + selected window revision IDs + window input digests + cited.
  - **Q5**: `support_sha256` (lifecycle, bounds, minutes, limitations, span times); provenance-only change ->
    `BASIS_REFRESHED` (owner path and `_unsupported_write`; the old "closed stays closed" early return is removed).
  - **C3**: Candidate over a NO_LONGER_SUPPORTED episode -> `REOPENED` (decision: "Model the close/reopen ... as durable
    recorded history"). Indeterminate over a closed episode still appends UNCONFIRMED - record as a question (below).
- `migrations/versions/0009_finding_store.py`: transitions + `BASIS_REFRESHED`, `REOPENED`; column `support_sha256 NOT NULL`.
- `adapters/postgres_finding_store.py`: **B2** `Fence.finding_revisions` = count of the Site's `finding_revision` rows
  (append-only, so it only grows); `episodes()` loads, `_insert_revision` writes `support_sha256`.
- `tests/test_s4_finding_episode.py` (new, pure, 16 tests): B1 split, 4 recurrence cases, 3-way merge, mixed
  split+merge, reopen, BASIS_REFRESHED vs SUPPORT_CHANGED, stale-margin skip, cross-midnight with/without OFF,
  out-of-order OFF, empty span in gap, modelling-only Indeterminate bridge.
- `tests/test_s4_finding_store_postgres.py`: **C7** moved-fence test applies a real planned OPENED write; new
  **B2** `test_a_pass_planned_before_another_pass_committed_opens_no_duplicate`; collateral now asserts BASIS_REFRESHED
  with equal `support_sha256`; `CaseRunner.stale_plan()`.
- `conversions/s4-finding-cases-v1.json`: F06 contradiction step adds 12:00/13:00 BASIS_REFRESHED (rev 2); bridge step
  12:00 MERGED is now rev 3, plus 08:00 (rev 3) and SPLIT_PART BASIS_REFRESHED; collateral note reworded.
- `tools/s4_finding_cases.py` `check`: collateral must be BASIS_REFRESHED with equal support digest.

## Evidence so far

- Pure tests: 16 passed. Against the pre-fix matcher (signature-only shim in scratchpad) 8 fail - B1 split, B3
  unassessed-day and no-OFF recurrence, mixed split+merge, reopen, BASIS_REFRESHED, out-of-order OFF, empty span -
  and 8 pass (regression coverage: 3-way merge, stale margin, bridges, linked recurrence, SUPPORT_CHANGED).
- S4 Postgres (isolated `assetops_s4fix_test`, dropped afterwards): 6 passed in 67.5 s.
- Mutation proofs (committed first, reverted with `git checkout --`): fence without `finding_revisions` ->
  interleaving test "DID NOT RAISE FindingFenceMoved"; fence check disabled -> moved-fence test "DID NOT RAISE".
- `tools/check-architecture.ps1`: "Architecture check passed."

## Next (resume here)

1. **Q6 F01 via the ordinary gateway** in `tools/s4_finding_cases.py` (copy the S3 pattern, `tools/s3_dispatch_cases.py`):
   after `prepare()` -> `start_lab()` (Lab on `--http-port` 8730), `snap = self.snapshot()`,
   `write_gateway_config(snap, self.credential)` overridden with `sequence_epoch = "s4-gateway-epoch-1"`,
   `start_gateway()` (pipe `\\.\pipe\assetops-s4-cases-gateway`, fix its "never started" comment). Port S3 `run_case`
   (:123-150; `window`/`basis` :66-67/:119, `SCENARIOS` :55-60 `prolonged`, MODEL/PUBLICATION :53-54) to run one
   prolonged roles-2 Lab run on a free day judged under the S4 controls (03, 04, 05, 07 or 10 - **not** 02, which
   predates the 10-03 setup controls; also an assessed 07 or 10 day changes recurrence coverage, so prefer 03-05),
   `deliver_all`, then `process-jobs` and `match-findings`; record batches from `sealed_inventory()` diff, the
   accepted evidence `sequence_epoch`/`gateway_id` (S3 `accepted()` :152-163) and the Finding(s) opened that day as
   "F01-gateway" in the artifact and `verify`. Keep F01-F06 fixture cases labelled "authenticated Batch V2 fault
   fixture, not gateway-sealed". Stop the Lab/gateway processes (`stop_all`). Update the spec/packet wording that
   F01's baseline Candidate is gateway-sealed.
2. Rerun producer: `tools/s4_finding_cases.py run --work <scratchpad>` + `verify` (own DB `assetops_s4cases`, TLS 8763,
   HTTP 8730); expect changed counts (fewer recurrence links: 10-08/10-11/10-15/10-21 cross-day links gone; F05
   collateral now BASIS_REFRESHED; F06 extra BASIS_REFRESHED). Record output in `.agent/S4-01-finding-cases-run.txt`.
   Drop the DB, confirm no listener on 8763/8730.
3. Full suites: backend with Postgres (isolated `_test` DB, drop afterwards), host, gateway, simulator (from
   `simulator/`), `tools/check-all.ps1` (`-ExecutionPolicy Bypass`), `tools/check-agent-workflow.ps1`.
4. Packet: add "Fix round 1" to `.agent/S4-01-phase-1-review-packet.md` (B1-B4, C7, C3, Q2/Q4/Q5/Q6 with the
   evidence above). Also fix C1 wording ("every later Finding" -> earlier days) in packet and `.ai/CODE_STATE.md`.
5. `.agent/S4-01-questions-2.md` (fail-closed defaults):
   - Q10 Indeterminate over a NO_LONGER_SUPPORTED episode appends UNCONFIRMED (closure basis lost); default keeps it.
     Same-span reappearance after closure is REOPENED, not a recurrence (no proven break) - Architect to confirm.
   - Q11 stop-span coverage proves OFF reports at both ends in order within the <=20-minute gap; an UNOBSERVED
     state between them is not visible in the interval result. Default: accept (dispatch-3.1 treats <=20 min report
     spacing as continuous); stricter alternative needs the off-period states exposed.
   - Q12 C6 residue: an earlier-anchor episode whose anchor is in no cluster may be canonical over an episode whose
     anchor is inside (merge rule "earlier anchor" wins over B1 retention when both apply).
   - Q13 recurrence requires both the prior run's observed OFF and the new run's observed OFF-before; either alone
     opens unlinked.
6. `.ai/CODE_STATE.md` S4-01 entry: add the fix-round deltas (<40 lines total).

## Open risks

- Every same-day window reassessment now appends BASIS_REFRESHED to each Finding on that day (Architect Q4 intent);
  phase 2/3 History must group these as provenance updates.
- The Q6 gateway case is not built yet: F01's gate is still open.
