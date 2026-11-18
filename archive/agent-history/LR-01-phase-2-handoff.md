# LR-01 phase 2 handoff — Finding and money surfaces (slice complete, in review)

Branch `task/LR-01-late-reading-series-and-money-limit`, phase-2 commits `3f71deac..2f326600` (+ closeout). Not merged.
Slice review packet: `.agent/LR-01-review-packet.md`. Owner steps: `.agent/LR-01-owner-walkthrough.md`.

## What landed

- **Matcher `finding-episode-3`** `backend/assetops_backend/analytics/finding_episode.py` (`_series`, `_end_reason`,
  `_support_write(former=...)`, `WindowBasis.series_limits`, `window_basis`): typed `end_reason`
  (`OFF_OBSERVED|CANDIDATE_ENDED|OPEN_BOUND|SERIES_LIMIT`); material generator-series refusals (asset's generator
  role cohort limits inside the former/current episode or cutting head/tail within 20 min) carried as
  `claim.series_limits` with kind, clock, evidence/attestation refs, window assessment revision and run, plus a
  `GENERATOR_SERIES_AMBIGUOUS` limitation; a cut tail drops the dependent `OPEN_BOUND ... after` (head likewise).
- **Shared gate** `backend/assetops_backend/financials/money_eligibility.py` (`money-eligibility-1`, `evaluate`,
  `MoneyEligibility.for_finding`): latest FindingRevision + every selected UTC day over episode ± 6 h; precedence
  PENDING (no selected window on an episode day [N3], non-CURRENT read, model change, live job, match pending,
  latest revision not citing the selected window, older matcher) > WITHHELD (revision series limit / SERIES_LIMIT /
  selected-window generator limit of the asset in the bracket) > ELIGIBLE. Fails closed (`unavailable`).
- **Consumers**: `consequence_read.ConsequenceReadService(eligibility=...)` gates `presented_as_current` and
  `current_amount_shown`, adds `money_eligibility` (+ head consequence ID) and `currentness.money_eligibility`;
  composition wires the real gate (`financials/composition.py`); `finding_api.bridge_consequence` returns state
  `WITHHELD_GENERATOR_SERIES|PENDING_REASSESSMENT`, no amount, `recorded_consequence_revision_id`;
  `scheduling/upstream.py` `findings[].money_eligibility` (downgraded to PENDING while this read has S3/S4/schedule
  blockers; upstream `eligibility` itself unchanged); `scheduling/health.release` disposes the gate's stores.
- **Migration 0015** `0015_finding_returning_basis`: drops `finding_revision_basis_unique` (index kept); replay guard
  in `postgres_finding_store._insert_revision` compares with the latest revision only. Needed so A -> B -> A
  (attestation recorded then revoked) appends a revision. Downgrade refuses while a returning basis exists.
- **Frontend**: `FindingConsequence.tsx` (`MoneyLimit`, gated pinned head, history "current" requires
  `current_amount_shown`), `financialsClient.ts` types, `SiteFinding.tsx` SERIES_LIMIT statement,
  `dispatchWords.ts` GENERATOR_SERIES_AMBIGUOUS wording.
- **Phase-1 review folded**: F1 `cohort._clock` reason depends only on touching attestations (`NO_ATTESTATION`
  otherwise; one touching but not covering = `OUTSIDE_VALIDITY`); L1 placement/measurement overlap over every
  attested reading of the channel; L2 requeued span covers the 07:00-07:05 mean (PG test).
- **Tools**: `tools/s402c_late_power_walkthrough.py` `run|attest|tick|serve|drop` for `assetops_lr01*` (work dir
  default `%LOCALAPPDATA%/AssetOps/<db>`; Performance comparison after every selection move; `serve` refuses other
  prefixes); `tools/s402d_tick_walkthrough.py` records the gate and asserts ELIGIBLE after tick 3;
  `tools/lr01-money-evidence.mjs` browser claims.

## Open risks / for the reviewer

- Migration 0015 relaxes a 0009 uniqueness constraint (see packet Known Deviations).
- The S5 seam's downgrade means S5 and the Finding API can differ while a schedule blocker stands (seam stricter).
- `bridgeCurrent`-based history wording still treats a non-gated STALE head as before (unchanged behaviour).
