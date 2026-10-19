# W4-01 / W3-01 closure check 2 (2026-10-20, main 70739d37)

Only items still open are listed. 11 of 13 are closed. The Action snapshot keys (`reserve_trial.py:276-289`, `postgres_action_store.py:273-274`) and the nine resolver keys plus reason extras (`source_provenance.py:157-226`) match the specs. `probe_fresh`, `ColdReadService`, `EvReadService`, both `_snapshot(c,...)` methods, the `contract-fixtures/w2` files, `var/sites/kobo-001.yaml` and `verification_outcome.recorded_at` also exist as cited.

## Open (2, both W4-01)

1. **Q7 / B7 (Medium): the positive-fixture setup has no literal command for the replay and Action steps.**
   - The spec says "execute the KOBO-001 accepted-evidence/assessment replay used by `tools/s4_finding_walkthrough.py`". That tool runs `assetops_backend.performance_migration run --tenant demo --site KOBO-001` (line 203) inside a docker, web and server walkthrough. It is not a reusable replay entry point.
   - Needed: the exact command or module that produces the CURRENT KOBO-001 Finding row in a private `_test` DB, as the cold and EV paths are named for W3. Alternatively, name the test helper to call.
   - Also needed: "creates/accepts it by the existing Action API" must name the endpoint or service call that supplies a selected Action event.
2. **Q28 (Low): the SERVICE attestation check names a "server service principal ID" that no source defines.**
   - The stored `action_event` actor shape is `actor_id ~ '^service:[a-z0-9-]+$'` (`0019_verification_core.py`). The attestation regex captures `service=<x>` with no `service:` prefix.
   - Needed: say whether the compare is `service:<x> == actor.id`, and where the server principal ID is read.

Blocked, not open: W3 EV Cost (W7) waits for the W2-07 money read. The spec states this explicitly.

Open count: 2 of 13 (0 High, 1 Medium, 1 Low).
