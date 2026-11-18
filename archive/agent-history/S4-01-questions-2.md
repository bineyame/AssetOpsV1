# S4-01 phase 1 questions, batch 2 (fail-closed defaults shipped)

Raised by fix round 1 (`.agent/S4-01-phase-1-review.md` B1-B4, C3; `D-2026-10-12-s4-finding-phase-1-clarifications`).
None blocks phase 1. Each names the default the build ships and where it lives
(`backend/src/assetops_backend/analytics/finding_episode.py` unless stated).

10. **Indeterminate over a closed episode; reappearance after closure.** An Indeterminate cluster over a
    NO_LONGER_SUPPORTED episode appends `UNCONFIRMED`, so the closure's basis is superseded by a weaker claim and the
    "no longer supported" fact is visible only in History. A Candidate over a closed episode's span appends `REOPENED`
    (C3), not a new recurrence, because no observed break separates them.
    Default: keep both (UNCONFIRMED is the more cautious current state; REOPENED keeps one identity). Alternative:
    leave a closed episode closed under Indeterminate support. Architect to confirm both.

11. **Stop-span coverage inside a <= 20-minute gap.** `_stops` proves an observed OFF report at each end of the stop,
    in order (`last_on <= off_after <= next off_before <= next first_on`). An UNOBSERVED state between those two OFF
    reports is not visible in the interval result, so it cannot refuse the bridge.
    Default: accept (dispatch-3.1 treats report spacing up to 20 minutes as continuous coverage). Stricter
    alternative needs the off-period observation states exposed by the interval assessment.

12. **Canonical choice when an anchor lies outside every cluster (C6 residue).** Ownership reserves each episode for
    the cluster containing its anchor (B1). An earlier-anchor episode whose anchor is in no cluster can still be
    chosen canonical in a merge over an episode whose anchor is inside, because the merge rule "earliest anchor
    wins" applies after B1 retention.
    Default: earliest anchor wins (stable, reproducible identity). Alternative: prefer an episode whose anchor is
    still supported.

13. **Recurrence needs both ends observed.** `_recurrence` links only when the prior run's OFF-after and the new run's
    OFF-before are both observed and `site.covered(prior.end, new.start)`; either alone opens the new Finding
    unlinked (`recurs_after_finding_id` null). Effect in the producer: cross-day recurrence links between fixture
    case days disappear (the nights between them are unassessed).
    Default: fail closed (no link). Alternative: link on one observed OFF plus coverage.

14. **BASIS_REFRESHED per reassessment (phase 2/3 History risk).** Under Q4/Q5 (window revisions and input digests
    in the basis; provenance-only change -> `BASIS_REFRESHED`), every same-day window reassessment or backdated control
    appends one `BASIS_REFRESHED` revision to every Finding on the affected days (F05 collateral, F06 extra
    revisions). A Finding can accumulate many provenance-only revisions.
    Default: phase 1 records them all, append-only; phase 2/3 History must group consecutive `BASIS_REFRESHED`
    revisions as one "evidence basis updated" entry and never present them as a change of claim. Alternative:
    suppress when only window IDs change (rejected by Q4: the Finding would cite a non-selected revision).

15. **Gateway-path case day.** The Lab refuses a 0-minute generator minimum runtime (`LIFECYCLE_TIMING_NOT_ALIGNED`:
    mini-grid v3 needs a positive multiple of the 5-minute step), and the S4 setup control sets 0 minutes from 10-03.
    Default: `F01-gateway` runs on 2026-10-02 (roles-2, template runtime, before the setup controls) after every
    fixture case (`tools/s4_finding_cases.py GATEWAY_DAY`). Alternative: change the setup control to a positive
    multiple of 5 minutes so the gateway day shares the fixture controls (re-baselines the fixture's Candidate starts).
