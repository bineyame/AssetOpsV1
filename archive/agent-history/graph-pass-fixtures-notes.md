# Graph-pass scoring fixtures (checker lane)

Edited only `frontend/docs/architecture/test_delivery_next_work.cjs` (+6 tests, 32 pass). `delivery_next_work.cjs`, registry, panel contracts and packets untouched; no real defect exposed.

New fixtures load the real committed registry and `tasks/README.md`/packets (technical `requires` closure, `sequenced_after` ignored):
- Real README discovers S4-03 (renamed `S4-03-finding-evidence-history.md`), S4-04, S5-02, S6-03; files exist; packet status phase is not_started; no stale S4-03 link.
- Each of the four stops selection when active (`active_task`) and in_review (`review`), unknown refuses, not-started does not stop.
- `A-finding-index` reaches sitefindings:1 and mini:3 (both empty and positive variants, each portion); not finding-evidence:1/2, finding-history:1, mini:1/2/4. I-S4-04 reaches both; I-S5-02 reaches mini:3 only. I-S4-03 and I-S5-01 closures contain neither A-finding-index nor I-S4-04.
- `A-action-index` and `I-S6-03` reach only sitework:1; action/recommendation/changes/verification/plan panels (non-empty set asserted) do not need it; S6-01/S6-02 closures exclude it.
- `I-S6-01` requires `I-S4-01`; `I-S6-02` requires I-S6-01 and not I-S6-03; I-S6-03 requires I-S6-01, is sequenced_after I-S6-02 only.

Not run: non-vacuity mutation of the real registry (auto-mode classifier denied a temporary registry edit; no file was changed). Non-emptiness is asserted in-test instead. Reviewer may mutate the registry to prove failure.

## Runs
- `tools/check-all.ps1`: All 6 guards passed (incl. delivery fixtures).
- `check_v69_dependency_registry.cjs --next-work`: exit refused, exactly as expected:
  `[unmapped_approved_panel] 22 approved core panel(s) lack a reviewed claim-portion path: finding-evidence:1, finding-evidence:2, mini:1, mini:2, mini:3, mini:4, changes:1, changes:2, recommendation:1, recommendation:2, recommendation:3, verification:1, verification:2, verification:3, sitework:1, action-overview:1, sitefindings:1, finding-history:1, action-plan:1, action-execution:1, action-evidence:1, action-history:1`
  Fingerprints: registry=40314ec899f7f939 queue=81ab83be42b2270f packet_status=613b49b424fa249b panel_contracts=c6f0009bbbf68f61 manifest=468bd0cf06b26749 owner_input=f902d15082e24067.
- Hypothetical (in memory, scratchpad script, nothing written): marking those 22 reviewed gives status ranked; top I-sim-dispatch-cases 3.028 vs second A-finding-episode 2.691 (gap 11.1%, above 10%) -> select I-sim-dispatch-cases, no notice. Others: I-S3-01 3.228 (blocked on open prerequisites), V-01a 2.655, V-01b 2.463 eligible. Not selection authorization.
