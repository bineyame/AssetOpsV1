# W3-02 0c re-review of fix r1 (2c46c9fd)

Verdict: ACCEPT. Read only through `git show 2c46c9fd`. Nothing was run, as instructed.

- H1 cold: `cold_heads_on(known_at=K)` applies `created_at <= :k` before DISTINCT ON, with `id DESC` as the tie-break. The refusal is gone and no row is produced for a kind with no head by K. The unpinned W2 path is unchanged.
- H1 EV: `_select_as_of` derives the basis from tariff assignments recorded at K (`recorded_from <= K < recorded_to`, revision `recorded_at <= K`). `select_on` and history are bounded by `recorded_at <= K`, including under HISTORICAL. STALE_BASIS copy is exact and revision_id is null. `tariff_on` is pinned the same way.
- M1: the W2-04 `drain` runs before the comparison snapshot. The test asserts at least one PRODUCT_EXPOSURE head, ID/kind/basis/counted equality with W2, and withheld/hold equality.
- L1: `cold_pending_as_of_on` is correct as ruled. L3: `set(seqs) == {SESSION_ANALYTIC}` and a positive seq. L2: the pure tests assert a head at K+epsilon is absent at K and selected later.
- New tests are non-vacuous. Pure: same-Finding/kind old vs new head, work state before/after K, wrong analytic key. Postgres: K0/K/later replay for cold, and tariff correction for EV with a repeat read at K plus a STALE_BASIS control at K0. Each asserts identity of IDs.

Residual, not blocking:
- The EV STALE control at K0 relies on `derive` yielding a basis with no tariff (otherwise guard would be None). It is plausible, but I could not run it.
- `historical_label` is set only when the state is HISTORICAL, while the ruling says "explicit earlier cutoff". Lane B should confirm.

Classification of the open choice: mechanical consequence of the rulings, no Architect needed.
- The ruling requires identifying the stored as-of head under HISTORICAL with no current claim, and gives the "Historical as of {known_at}" copy.
- The guard `HISTORICAL_CURRENT_CLAIM` and the "Historical scenario" label are the existing W2 vocabulary.
- `historical_label` is only an additive carrier for the ruled copy. The head is shaped like a history row.
- Lane B should note the new field.
